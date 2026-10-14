/* probe_navigate.js -- WHY DOES THE DOCUMENT FETCH HANG? (diagnostic)
   Usage: node probe_navigate.js <url> */
'use strict';
const { chromium } = require('E:/PythonChimera/node_modules/playwright-core');
const url = process.argv[2] || 'http://127.0.0.1:8901/';
(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true,
    args: ['--no-proxy-server'] });
  try {
    const page = await (await browser.newContext()).newPage();
    page.on('console', m => console.log('[console]', m.type(), m.text().slice(0, 120)));
    page.on('requestfailed', r => console.log('[reqfail]', r.url(),
      r.failure() && r.failure().errorText));
    page.on('request', r => console.log('[req]', r.url()));
    page.on('response', r => console.log('[resp]', r.status(), r.url()));
    console.log('navigating', url, '...');
    const t0 = Date.now();
    const resp = await page.goto(url, { timeout: 25000, waitUntil: 'commit' });
    console.log('COMMITTED in', ((Date.now() - t0) / 1000).toFixed(1), 's status', resp && resp.status());
    const t1 = Date.now();
    await page.waitForLoadState('load', { timeout: 20000 })
      .then(() => console.log('LOAD done in', ((Date.now() - t1) / 1000).toFixed(1), 's'))
      .catch(e => console.log('LOAD still pending after 20 s:', e.message.split('\n')[0]));
    console.log('title:', await page.title());
  } finally {
    await browser.close().catch(() => {});
  }
  process.exit(0);
})().catch(e => { console.error('PROBE ERR:', e.message.split('\n')[0]); process.exit(2); });
