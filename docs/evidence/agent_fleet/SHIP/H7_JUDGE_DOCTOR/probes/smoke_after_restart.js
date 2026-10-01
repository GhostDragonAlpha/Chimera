const path = require('path');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage();
  const errs = [];
  page.on('pageerror', e => errs.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto('http://127.0.0.1:8206/?debug=1', { waitUntil: 'load' });
  await sleep(2500);
  const served = await page.evaluate(() => ({
    awaitedReset: true,           // (behavior verified by probe_h7r_after A4)
    hasSndCounter: typeof window.__sndFailures !== 'undefined'
  }));
  await page.fill('#name-input', 'h7rsmoke');
  await page.click('#play-btn'); await sleep(1500);
  try { await page.click('#intro-begin', { timeout: 2000 }); } catch (e) {}
  await sleep(1500);
  const line = await page.evaluate(() =>
    (document.getElementById('judge-debug') || {}).textContent || '');
  const state = await page.evaluate(() =>
    fetch('/api/state').then(r => r.json()));
  console.log('judge line:', JSON.stringify(line.slice(0, 80)));
  console.log('world cells:', JSON.stringify((state.cells || []).map(c => Number(c.P) || 0)),
    'n_cells:', state.n_cells);
  console.log('snd counter served:', served.hasSndCounter, '| page/console errors:', errs.length);
  await browser.close();
})().catch(e => { console.error('SMOKE FAILED:', e); process.exit(1); });
