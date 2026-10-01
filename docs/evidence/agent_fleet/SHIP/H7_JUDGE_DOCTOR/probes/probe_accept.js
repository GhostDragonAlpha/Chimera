/* probe_accept.js -- H7 acceptance (a) + (e):
   (a) self-play lessons 1-3 pass on their own real input, with three
       DISTINCT pass sentences, saved progress on request;
   (e) then a 10-minute quiet soak: zero console errors, zero 429s.
   Run: node probe_accept.js */
const path = require('path');
const fs = require('fs');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));
const URL_ = 'http://127.0.0.1:8206/?debug=1';
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const consoleErrors = [];
  let http429 = 0;
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  page.on('response', r => { if (r.status() === 429) http429++; });
  const R = {};

  await page.goto(URL_, { waitUntil: 'load' });
  await sleep(2000);
  await page.evaluate(() => fetch('/api/gravity', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ on: false }) }).then(r => r.json()));
  await page.fill('#name-input', 'h7accept');
  await page.click('#play-btn'); await sleep(1200);
  try { await page.click('#intro-begin', { timeout: 3000 }); } catch (e) {}
  await sleep(600);

  const judgeLine = () => page.evaluate(() =>
    (document.getElementById('judge-debug') || {}).textContent || '');
  const verdict = () => page.evaluate(() =>
    (document.getElementById('verdict') || {}).textContent);
  const setForce = v => page.evaluate(v => {
    const f = document.getElementById('force'); f.value = v;
    f.dispatchEvent(new Event('input'));
  }, v);
  const waitPassed = async (capMs) => {
    const t0 = Date.now();
    while (Date.now() - t0 < capMs) {
      if (/passed=true/.test(await judgeLine())) return true;
      await sleep(400);
    }
    return false;
  };
  const waitCalm = async (capMs) => {
    const t0 = Date.now();
    while (Date.now() - t0 < capMs) {
      const calm = await page.evaluate(() => fetch('/api/state').then(r => r.json())
        .then(s => (s.cells || []).every(c => {
          const v = Number(c.V);
          if (Number.isFinite(v) && v <= 1e-6) return true;   // sealed solid
          return Math.abs(Number(c.P) || 0) < 1000; })));
      if (calm) return true;
      await sleep(500);
    }
    return false;
  };

  // ---- L1 WAKE THE CELL: press the belly hard, let go, heal --------------
  await setForce(50000);
  await page.keyboard.down(' '); await sleep(2500); await page.keyboard.up(' ');
  const l1 = { passed: await waitPassed(15000), verdict: await verdict() };
  await waitCalm(20000);
  console.log('L1:', JSON.stringify(l1));

  // ---- L2 THE GENTLE HAND: sub-8000 N foot press -------------------------
  await page.keyboard.press(']'); await sleep(800);
  await setForce(6000);
  await page.keyboard.down(' '); await sleep(1500); await page.keyboard.up(' ');
  const l2 = { passed: await waitPassed(15000), verdict: await verdict() };
  await waitCalm(20000);
  console.log('L2:', JSON.stringify(l2));

  // ---- L3 THE HEALING: wake any cell, let go, wait ----------------------
  await page.keyboard.press(']'); await sleep(800);
  await setForce(50000);
  await page.keyboard.down(' '); await sleep(2500); await page.keyboard.up(' ');
  const l3 = { passed: await waitPassed(15000), verdict: await verdict() };
  await waitCalm(20000);
  console.log('L3:', JSON.stringify(l3));

  // save through the page's own button
  await page.click('#save-btn'); await sleep(1200);
  const prog = await page.evaluate(() =>
    fetch('/api/progress?name=h7accept').then(r => r.json()));
  const passedOnDisk = Object.keys((prog && prog.lessons) || {})
    .filter(k => prog.lessons[k].passed);
  const distinct = new Set([l1.verdict, l2.verdict, l3.verdict]).size === 3;
  R.selfPlay = {
    l1, l2, l3,
    allPassed: l1.passed && l2.passed && l3.passed,
    distinctSentences: distinct,
    passedOnDisk,
    CLEAN: l1.passed && l2.passed && l3.passed && distinct && passedOnDisk.length >= 3,
  };
  console.log('(a) self-play:', JSON.stringify(R.selfPlay, null, 1));

  // ---- (e) 10-minute quiet soak on the same page -------------------------
  console.log('(e) soaking 10 minutes...');
  const t0 = Date.now();
  const errsAtStart = consoleErrors.length;
  while (Date.now() - t0 < 10 * 60 * 1000) {
    await sleep(10000);
    // a gentle heartbeat interaction once a minute: orbit a little
    if ((Date.now() - t0) % 60000 < 10000) {
      const box = await page.locator('#gl').boundingBox();
      await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
      await page.mouse.down();
      await page.mouse.move(box.x + box.width / 2 + 40, box.y + box.height / 2, { steps: 5 });
      await page.mouse.up();
    }
  }
  const soakErrors = consoleErrors.slice(errsAtStart);
  R.soak = { minutes: 10, consoleErrors: soakErrors, count: soakErrors.length,
             http429s: http429,
             CLEAN: soakErrors.length === 0 && http429 === 0 };
  console.log('(e) soak:', soakErrors.length, 'console errors,', http429, 'x 429 =>',
    R.soak.CLEAN ? 'CLEAN' : 'NOT CLEAN');
  if (soakErrors.length) console.log(soakErrors.slice(0, 5));

  fs.writeFileSync(__dirname + '/../accept_a_e.json', JSON.stringify(R, null, 1));
  console.log('WROTE accept_a_e.json');
  await browser.close();
})().catch(e => { console.error('PROBE FAILED:', e); process.exit(1); });
