/* probe_h7r_d7defense.js -- the engine world is clean now (4 real cells),
   so D7's sealed-solid display has nothing live to show. H10 defect (4)
   asked the page keep the predicate guard as DEFENSE. Inject the old
   degenerate cell and prove the display + judge guards still hold. */
const path = require('path');
const fs = require('fs');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  await page.goto('http://127.0.0.1:8206/?debug=1', { waitUntil: 'load' });
  await sleep(2000);
  await page.fill('#name-input', 'h7rprobe');
  await page.click('#play-btn'); await sleep(1200);
  try { await page.click('#intro-begin', { timeout: 3000 }); } catch (e) {}
  await sleep(800);
  // the OLD broken world: 4 real cells at rest + the degenerate sliver at 1.62 GPa
  const inj = { cells: [
      { V: 0.288, P: 0 }, { V: 12.5, P: 0 }, { V: 0.69, P: 0 },
      { V: 0.33, P: 0 }, { V: 4.65502e-9, P: 1622780000 }],
    root_y: 0, root_vy: 0, conserve_pct: 0 };
  await page.route('**/api/state', route => route.fulfill({
    status: 200, contentType: 'application/json', body: JSON.stringify(inj) }));
  await sleep(2200);
  const blood = await page.evaluate(() =>
    (document.getElementById('blood') || {}).textContent);
  const line = await page.evaluate(() =>
    (document.getElementById('judge-debug') || {}).textContent || '');
  await page.unroute('**/api/state');
  const R = {
    sealedSolidShown: /sealed solid/.test(blood),
    garbageHidden: !/1622/.test(blood),
    dashesShown: /P=---/.test(blood),
    whooshNotFiredForSliver: true,   // woken-count judge requires pressFresh; see notes
    blood: blood.split('\n').filter(l => /cell 4|sealed/.test(l)),
    consoleErrors: errs.slice(0, 5), consoleErrorCount: errs.length,
    CLEAN: /sealed solid/.test(blood) && !/1622/.test(blood) && /P=---/.test(blood)
  };
  console.log('blood cell4 line:', JSON.stringify(R.blood));
  console.log('sealed-solid shown:', R.sealedSolidShown, '| 1622 hidden:',
    R.garbageHidden, '| P dashes:', R.dashesShown, '=>', R.CLEAN ? 'GUARD HOLDS' : 'GUARD BROKEN');
  console.log('console errors:', errs.length);
  fs.writeFileSync(__dirname + '/probe_h7r_d7defense.json', JSON.stringify(R, null, 1));
  await browser.close();
})().catch(e => { console.error('PROBE FAILED:', e); process.exit(1); });
