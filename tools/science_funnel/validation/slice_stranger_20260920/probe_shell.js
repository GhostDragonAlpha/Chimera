/* probe_shell.js -- is the broken component the chrome-headless-shell?
   Launch the installed chrome.exe binary directly (playwright executablePath)
   with headless mode and try a real navigation.
   Usage: node probe_shell.js */
'use strict';
const fs = require('fs');
const pw = require('E:/PythonChimera/node_modules/playwright-core');
const CANDIDATES = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
];
const exe = CANDIDATES.find(p => fs.existsSync(p));
if (!exe) { console.log('no installed chrome.exe found'); process.exit(3); }
console.log('installed chrome:', exe);
(async () => {
  const browser = await pw.chromium.launch({
    executablePath: exe, headless: true, args: ['--no-proxy-server'], timeout: 15000 });
  try {
    const page = await (await browser.newContext()).newPage();
    const t0 = Date.now();
    const resp = await Promise.race([
      page.goto('https://httpbin.org/html', { timeout: 8000, waitUntil: 'commit' }),
      new Promise((_, rej) => setTimeout(() => rej(new Error('nav>8s')), 9000)),
    ]);
    console.log('chrome.exe headless httpbin ->', resp ? 'status ' + resp.status() : '?',
      '(' + (Date.now() - t0) + ' ms)');
  } catch (e) {
    console.log('chrome.exe headless httpbin ->', e.message.split('\n')[0].slice(0, 90));
  } finally {
    try { await Promise.race([browser.close(), new Promise(r => setTimeout(r, 6000))]); } catch (e) {}
    try { browser.process() && browser.process().kill('SIGKILL'); } catch (e) {}
  }
  process.exit(0);
})().catch(e => { console.error('PROBE ERR:', e.message.split('\n')[0]); process.exit(2); });
