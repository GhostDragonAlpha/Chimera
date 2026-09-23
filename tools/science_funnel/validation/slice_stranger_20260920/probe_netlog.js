/* probe_netlog.js -- capture Chrome's own network log for one navigation.
   Usage: node probe_netlog.js <url> <netlogPath> */
'use strict';
const { chromium } = require('E:/PythonChimera/node_modules/playwright-core');
const url = process.argv[2] || 'http://127.0.0.1:8917/';
const netlog = process.argv[3] || 'netlog.json';
(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true,
    args: ['--no-proxy-server', '--log-net-log=' + netlog] });
  try {
    const page = await (await browser.newContext()).newPage();
    await page.goto(url, { timeout: 15000, waitUntil: 'commit' })
      .then(() => console.log('committed'))
      .catch(e => console.log('goto err:', e.message.split('\n')[0]));
  } finally {
    await browser.close().catch(() => {});
  }
  process.exit(0);
})().catch(e => { console.error('PROBE ERR:', e.message.split('\n')[0]); process.exit(2); });
