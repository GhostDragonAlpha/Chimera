/* probe_before2.js -- H7 sharper before-repros:
   1. mouse press aimed AT the body: capture the touch_hit BODY ok flag and
      the page's reaction (the res.ok HTTP-vs-body bug).
   2. decay-under-hold: is an engine touch an impulse (decays while held)?
   3. 429-eats-a-press: exhaust the stream bucket, then one SPACE press --
      does the press silently vanish (no retry, no report)?
   4. D5 redo: slider parked at 6000 N (under the gentle cap) + injected
      cell0=60 kPa with NO press -> does L2 pass without its input?
   Run: node probe_before2.js */
const path = require('path');
const fs = require('fs');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));
const URL_ = process.argv[2] || 'http://127.0.0.1:8206';
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const R = {};
  const judgeLine = () => page.evaluate(() =>
    (document.getElementById('judge-debug') || {}).textContent || '');
  const hand = () => page.evaluate(() => (document.getElementById('hand-state') || {}).textContent);
  const cells = () => page.evaluate(() => fetch('/api/state').then(r => r.json())
    .then(s => (s.cells || []).map(c => Number(c.P) || 0)));

  await page.goto(URL_, { waitUntil: 'load' });
  await sleep(2000);
  await page.evaluate(() => fetch('/api/gravity', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ on: false }) }).then(r => r.json()));
  await page.fill('#name-input', 'h7probe2');
  await page.click('#play-btn'); await sleep(1200);
  try { await page.click('#intro-begin', { timeout: 3000 }); } catch (e) {}
  await sleep(800);

  // ---- 1. AIMED mouse press: project the torso point (0,4.5,0.3) to a pixel
  const cam0 = { r: 26, theta: -0.55, phi: 0.42, target: [0, 4.5, 0] };
  const px = await page.evaluate((c) => {
    const vsub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
    const vdot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
    const vcross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
    const vnorm = a => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
    const ch = Math.cos(c.phi);
    const eye = [c.target[0] + c.r * ch * Math.sin(c.theta), c.target[1] + c.r * Math.sin(c.phi),
                 c.target[2] + c.r * ch * Math.cos(c.theta)];
    const cv = document.getElementById('gl'); const b = cv.getBoundingClientRect();
    const tanF = Math.tan(45 * Math.PI / 360);
    const fwd = vnorm(vsub(c.target, eye));
    const right = vnorm(vcross(fwd, [0, 1, 0])); const up = vcross(right, fwd);
    const d = vsub([0, 4.5, 0.3], eye); const a = vdot(d, fwd);
    const ndcX = (vdot(d, right) / a) / (tanF * (cv.width / cv.height));
    const ndcY = (vdot(d, up) / a) / tanF;
    return { x: b.left + (ndcX + 1) / 2 * b.width, y: b.top + (1 - ndcY) / 2 * b.height };
  }, cam0);
  // capture the touch_hit response BODY the page receives
  let touchBody = null;
  await page.route('**/api/touch_hit', async route => {
    const resp = await route.fetch(); const b = await resp.text(); touchBody = b;
    await route.fulfill({ response: resp, body: b });
  });
  await page.mouse.move(px.x, px.y); await page.mouse.down(); await sleep(700);
  const duringHold1 = await cells();
  await page.mouse.up(); await sleep(400);
  const afterUp = { hand: await hand(), torso: (await cells())[1] };
  await page.screenshot({ path: __dirname + '/../shots/before2_mouse_aimed.png' });
  R.mouseAimed = { pixel: px, touchBody, duringHold1, afterUp };
  console.log('1. aimed mouse press: pixel', JSON.stringify(px));
  console.log('   touch_hit BODY:', touchBody);
  console.log('   torso during hold:', duringHold1[1], ' after up:', JSON.stringify(afterUp));
  await page.unroute('**/api/touch_hit');
  await page.keyboard.press('Escape'); await sleep(500);

  // ---- 2. decay-under-hold: SPACE press held 6 s, sample torso every second
  await page.evaluate(() => { const f = document.getElementById('force'); f.value = 50000;
    f.dispatchEvent(new Event('input')); });
  await page.keyboard.down(' ');
  const decay = [];
  for (let i = 0; i < 6; i++) { await sleep(1000); decay.push((await cells())[1]); }
  await page.keyboard.up(' '); await sleep(400);
  R.decayUnderHold = { torsoPa: decay, note: 'SPACE still "held" (no keyup release in this build)' };
  console.log('2. torso while held (1s samples):', decay.join(' '),
    ' hand:', await hand());
  await page.keyboard.press('Escape'); await sleep(500);

  // ---- 3. 429-eats-a-press: exhaust the stream bucket, then one SPACE press
  const burst = await page.evaluate(async () => {
    let got429 = 0;
    for (let i = 0; i < 300; i++) {
      const r = await fetch('/api/state').catch(() => null);
      if (r && r.status === 429) got429++;
    }
    return got429;
  });
  await sleep(300);
  const before = (await cells())[1];
  await page.keyboard.down(' '); await sleep(900);
  const midLine = await judgeLine(); const midHand = await hand();
  await page.keyboard.up(' ');
  await sleep(1500);
  const after = (await cells())[1];
  R.starvedPress = { burst429s: burst, torsoBefore: before, midLine, midHand, torsoAfter: after,
    answered: after > before + 5000 };
  console.log('3. burst 429s:', burst, ' then SPACE press: before', before,
    ' after', after, ' answered:', after > before + 5000);
  console.log('   mid line:', midLine, ' hand:', midHand);
  await sleep(8000); // let the bucket refill

  // ---- 4. D5 redo: slider at 6000 N, injected cell0=60 kPa, NO press
  await page.keyboard.press('Escape'); await sleep(300);
  await page.keyboard.press(']'); await sleep(700);            // L2 the_gentle_hand
  await page.evaluate(() => { const f = document.getElementById('force'); f.value = 6000;
    f.dispatchEvent(new Event('input')); });
  let bloodText = null;
  await page.route('**/api/state', route => route.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ cells: [
      { V: 0.287, P: 60000 }, { V: 12.5, P: 0 }, { V: 0.69, P: 0 },
      { V: 0.33, P: 0 }, { V: 0.0, P: 1622780000 }],
      root_y: 0, root_vy: 0, conserve_pct: 0 }) }));
  await sleep(3000);
  const v5 = await page.evaluate(() => (document.getElementById('verdict') || {}).textContent);
  bloodText = await page.evaluate(() => (document.getElementById('blood') || {}).textContent);
  const j5 = await judgeLine();
  await page.unroute('**/api/state');
  R.injectedNoPress = { verdict: v5, judge: j5, blood: bloodText.trim().split('\n') };
  console.log('4. L2 injected cell0=60kPa (force 6000, NO press):');
  console.log('   verdict:', v5); console.log('   judge  :', j5);
  console.log('   blood  :', JSON.stringify(bloodText.trim().split('\n')));
  await page.screenshot({ path: __dirname + '/../shots/before2_D5_injected.png' });

  fs.writeFileSync(__dirname + '/../before_repro2.json', JSON.stringify(R, null, 1));
  console.log('WROTE before_repro2.json');
  await browser.close();
})().catch(e => { console.error('PROBE FAILED:', e); process.exit(1); });
