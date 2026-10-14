/* probe_parallel.js -- while Chrome's document request hangs, does another
   client reach the same server? Prints both verdicts.
   Usage: node probe_parallel.js <pageUrl> <healthUrl> */
'use strict';
const { chromium } = require('E:/PythonChimera/node_modules/playwright-core');
const pageUrl = process.argv[2] || 'http://127.0.0.1:8917/';
const healthUrl = process.argv[3] || 'http://127.0.0.1:8917/api/health';
(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true,
    args: ['--no-proxy-server'] });
  try {
    const page = await (await browser.newContext()).newPage();
    const t0 = Date.now();
    const nav = page.goto(pageUrl, { timeout: 15000, waitUntil: 'commit' })
      .then(() => 'committed')
      .catch(e => 'hang: ' + e.message.split('\n')[0]);
    await new Promise(r => setTimeout(r, 6000)); // let the document hang
    const t1 = Date.now();
    const health = await fetch(healthUrl)
      .then(r => 'node fetch OK in ' + (Date.now() - t1) + 'ms')
      .catch(e => 'node fetch ERR ' + (e.cause ? e.cause.code : e.message));
    console.log('chrome navigation:', await nav);
    console.log('while hanging, other client:', health);
  } finally {
    await browser.close().catch(() => {});
  }
  process.exit(0);
})().catch(e => { console.error('PROBE ERR:', e.message.split('\n')[0]); process.exit(2); });
