/* probe_dom.js -- discriminate: div missing vs empty; script execution truth. */
const path = require('path');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });
  const errors = [];
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message.slice(0, 300)));
  page.on('console', m => errors.push('console-' + m.type() + ': ' + m.text().slice(0, 200)));
  await page.goto('http://127.0.0.1:8206', { waitUntil: 'load' });
  await page.waitForTimeout(5000);
  const info = await page.evaluate(() => {
    const dbg = document.getElementById('judge-debug');
    return {
      readyState: document.readyState,
      scriptsInDom: document.querySelectorAll('script').length,
      judgeDebugExists: !!dbg,
      judgeDebugText: dbg === null ? 'NULL' : ('[' + dbg.textContent + ']'),
      judgeDebugInBody: dbg ? document.body.contains(dbg) : false,
      forceLabel: document.getElementById('force-label').textContent,
      bloodText: (document.getElementById('blood') || {}).textContent || '',
      lessonsLoaded: typeof LESSONS !== 'undefined' ? LESSONS.length : 'n/a',
      RGstate: typeof RG !== 'undefined' ? (RG === null ? 'null' : 'set') : 'n/a'
    };
  });
  console.log(JSON.stringify(info, null, 1));
  console.log('ERRORS:', errors.length ? errors.slice(0, 6) : 'none');
  await browser.close();
})().catch(e => { console.error('PROBE FAILED:', e.message); process.exit(1); });
