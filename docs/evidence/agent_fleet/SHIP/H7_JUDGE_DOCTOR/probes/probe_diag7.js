const path = require('path');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('http://127.0.0.1:8206/?debug=1', { waitUntil: 'load' });
  await sleep(2000);
  const raw = await page.evaluate(() => fetch('/api/state').then(r => r.json()));
  console.log('live cells raw:', JSON.stringify(raw.cells));
  await page.fill('#name-input', 'h7diag');
  await page.click('#play-btn'); await sleep(1500);
  try { await page.click('#intro-begin', { timeout: 2000 }); } catch (e) {}
  await sleep(2500);
  const blood = await page.evaluate(() => (document.getElementById('blood') || {}).textContent);
  const jline = await page.evaluate(() => (document.getElementById('judge-debug') || {}).textContent);
  console.log('blood:', JSON.stringify(blood));
  console.log('judge line:', JSON.stringify(jline));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
