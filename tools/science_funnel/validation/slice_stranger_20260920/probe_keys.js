/* probe_keys.js -- do key events reach the page's handler at all?
   Probe 1: in-page synthetic KeyboardEvent (window.dispatchEvent)
   Probe 2: CDP keyboard.press
   Both captured with a capture-phase listener; focus state printed.
   Usage: node probe_keys.js <baseURL> */
'use strict';
const pw = require('E:/PythonChimera/node_modules/playwright-core');
const BASE = process.argv[2] || 'http://127.0.0.1:8901';
(async () => {
  const browser = await pw.chromium.launch({ headless: true, args: ['--no-proxy-server'] });
  try {
    const page = await (await browser.newContext()).newPage();
    page.on('pageerror', e => console.log('[pageerror]', e.message.slice(0, 120)));
    await page.goto(BASE + '/', { waitUntil: 'load', timeout: 30000 });
    for (let i = 0; i < 60; i++) {
      const ok = await page.evaluate(() =>
        !!(window.__CHIMERA_KEYS && window.__CHIMERA_KEYS.length &&
           /root_y/.test((document.getElementById('status') || {}).textContent || '')));
      if (ok) break;
      await new Promise(r => setTimeout(r, 500));
    }
    await page.evaluate(() => {
      window.__keydowns = [];
      window.addEventListener('keydown',
        e => window.__keydowns.push({ key: e.key, code: e.code, trusted: e.isTrusted }), true);
    });
    await page.evaluate(() => {
      window.dispatchEvent(new KeyboardEvent('keydown',
        { key: '2', code: 'Digit2', bubbles: true }));
    });
    await new Promise(r => setTimeout(r, 800));
    console.log('in-page synthetic:', JSON.stringify(await page.evaluate(() => ({
      seen: window.__keydowns,
      msg: (document.getElementById('msg') || {}).textContent || '' }))));
    await page.keyboard.press('1');
    await new Promise(r => setTimeout(r, 800));
    console.log('CDP press:', JSON.stringify(await page.evaluate(() => ({
      seen: window.__keydowns,
      msg: (document.getElementById('msg') || {}).textContent || '' }))));
    console.log('activeElement:', await page.evaluate(() => {
      const a = document.activeElement;
      return a ? a.tagName + '#' + a.id : 'none';
    }), '| document.hasFocus():', await page.evaluate(() => document.hasFocus()));
  } finally {
    await browser.close().catch(() => {});
  }
  process.exit(0);
})().catch(e => { console.error('ERR', e.message.split('\n')[0]); process.exit(2); });
