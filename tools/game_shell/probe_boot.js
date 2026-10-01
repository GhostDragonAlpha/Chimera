/* probe_boot.js -- which stage of the page's script actually ran? */
const path = require('path');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message.slice(0, 200)));
  page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text().slice(0, 200)); });
  await page.goto('http://127.0.0.1:8206', { waitUntil: 'load' });
  await page.waitForTimeout(4000);
  const info = await page.evaluate(() => ({
    forceLabel: document.getElementById('force-label').textContent,
    lessonNav: !!document.getElementById('lesson-next'),
    judgeDebug: (document.getElementById('judge-debug') || {}).textContent || '(missing)',
    glErrorHidden: document.getElementById('gl-error').classList.contains('hidden'),
    soundLoaded: typeof window.ChimeraSound,
    canvasW: (document.getElementById('c') || document.querySelector('canvas') || {}).width || 0
  }));
  console.log(JSON.stringify(info, null, 1));
  console.log('ERRORS:', errors.length ? errors : 'none');
  await browser.close();
})().catch(e => { console.error('PROBE FAILED:', e.message); process.exit(1); });
