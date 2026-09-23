/* probe_matrix.js -- which (browser, server) pairs work right now?
   8 s timeout per cell, every browser is closed in finally.
   Usage: node probe_matrix.js */
'use strict';
const pw = require('E:/PythonChimera/node_modules/playwright-core');
const URLS = {
  local: 'http://127.0.0.1:9/?x=1',           // expect fast ERR_UNSAFE_PORT
  httpbin: 'https://httpbin.org/html',        // expect 200 (or a TLS verdict)
};
const BROWSERS = [
  ['chrome', () => pw.chromium.launch({ channel: 'chrome', headless: true, args: ['--no-proxy-server'], timeout: 15000 })],
  ['chromium-bundled', () => pw.chromium.launch({ headless: true, args: ['--no-proxy-server'], timeout: 15000 })],
];
(async () => {
  for (const [name, mk] of BROWSERS) {
    let browser;
    const t0 = Date.now();
    try {
      browser = await Promise.race([
        mk(),
        new Promise((_, rej) => setTimeout(() => rej(new Error('launch>15s')), 16000)),
      ]);
      console.log(name, 'launched in', Date.now() - t0, 'ms');
    } catch (e) {
      console.log(name, 'LAUNCH FAIL:', e.message.split('\n')[0]);
      continue;
    }
    for (const [label, url] of Object.entries(URLS)) {
      const t1 = Date.now();
      try {
        const page = await (await browser.newContext()).newPage();
        const resp = await Promise.race([
          page.goto(url, { timeout: 8000, waitUntil: 'commit' }),
          new Promise((_, rej) => setTimeout(() => rej(new Error('nav>8s')), 9000)),
        ]);
        console.log('  ', label, '->', resp ? 'status ' + resp.status() : 'no resp',
          '(' + (Date.now() - t1) + ' ms)');
      } catch (e) {
        console.log('  ', label, '->', e.message.split('\n')[0].slice(0, 80),
          '(' + (Date.now() - t1) + ' ms)');
      }
    }
    try { await Promise.race([browser.close(), new Promise(r => setTimeout(r, 6000))]); } catch (e) {}
    try { browser.process() && browser.process().kill('SIGKILL'); } catch (e) {}
  }
  process.exit(0);
})().catch(e => { console.error('MATRIX ERR:', e.message); process.exit(2); });
