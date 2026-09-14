/* soak_h7r_10min.js -- acceptance (f): a 10-minute session with ZERO console
   errors. A fresh page plays like a quiet player: one SPACE press/hold/release
   every ~30 s, one lesson advance every ~60 s (all ten, then wraps), the
   force nudged by the '-' / '=' rails. Counts console errors, page errors,
   and any 429/5xx response the whole time. Run: node soak_h7r_10min.js */
const path = require('path');
const fs = require('fs');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const consoleErrors = [], pageErrors = [], badStatus = [];
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  page.on('pageerror', e => pageErrors.push(e.message));
  page.on('response', r => {
    if (r.status() === 429 || r.status() >= 500)
      badStatus.push(r.status() + ' ' + r.url());
  });
  await page.goto('http://127.0.0.1:8206/?debug=1', { waitUntil: 'load' });
  await sleep(2000);
  await page.fill('#name-input', 'h7rsoak');
  await page.click('#play-btn'); await sleep(1200);
  try { await page.click('#intro-begin', { timeout: 3000 }); } catch (e) {}
  const T0 = Date.now(), TEN_MIN = 10 * 60 * 1000;
  let beat = 0;
  while (Date.now() - T0 < TEN_MIN) {
    // gentle press/hold/release on the lesson's target
    await page.keyboard.down(' '); await sleep(900); await page.keyboard.up(' ');
    await sleep(2500);
    // nudge the force rail occasionally
    if (beat % 2 === 0) { await page.keyboard.press('='); }
    else { await page.keyboard.press('-'); }
    await sleep(1200);
    // advance the lesson every ~60 s
    if (beat % 2 === 1) { await page.keyboard.press(']'); }
    await sleep(2500);
    beat++;
  }
  const R = {
    minutes: (Date.now() - T0) / 60000,
    beats: beat,
    consoleErrors, pageErrors,
    badStatusResponses: badStatus.slice(0, 10),
    badStatusCount: badStatus.length,
    CLEAN: consoleErrors.length === 0 && pageErrors.length === 0 &&
      badStatus.length === 0
  };
  console.log('soak minutes:', R.minutes.toFixed(2), '| beats:', beat);
  console.log('console errors:', consoleErrors.length,
    '| page errors:', pageErrors.length,
    '| 429/5xx responses:', badStatus.length,
    '=>', R.CLEAN ? 'ZERO-ERROR SESSION' : 'ERRORS SEEN');
  if (consoleErrors.length) console.log(consoleErrors.slice(0, 5));
  if (badStatus.length) console.log(badStatus.slice(0, 5));
  fs.writeFileSync(__dirname + '/soak_h7r_10min.json', JSON.stringify(R, null, 1));
  await browser.close();
})().catch(e => { console.error('SOAK FAILED:', e); process.exit(1); });
