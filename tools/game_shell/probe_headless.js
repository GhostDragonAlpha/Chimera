/* probe_headless.js -- introspect the served page in headless Chrome. */
const path = require('path');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });
  const logs = [];
  page.on('console', m => logs.push(m.type() + ': ' + m.text().slice(0, 120)));
  page.on('pageerror', e => logs.push('PAGEERROR: ' + e.message));
  await page.goto('http://127.0.0.1:8206', { waitUntil: 'load' });
  await page.waitForTimeout(6000);
  const info = await page.evaluate(() => {
    const dbg = document.getElementById('judge-debug');
    const glc = document.createElement('canvas');
    const gl2 = glc.getContext('webgl2');
    return {
      debugDivExists: !!dbg,
      debugText: dbg ? dbg.textContent : null,
      webgl2: !!gl2,
      lessonCardTitle: (document.querySelector('.lesson-title') || {}).textContent || null,
      screenPlayOn: !!document.getElementById('screen-play').classList.contains('on'),
      topologyFetched: typeof RG !== 'undefined' && !!RG && RG.triCount > 0,
      glTruthy: typeof gl !== 'undefined' ? !!gl : 'n/a'
    };
  });
  console.log(JSON.stringify(info, null, 1));
  console.log('console messages:', logs.length ? logs.slice(0, 10) : 'none');
  await browser.close();
})().catch(e => { console.error('PROBE FAILED:', e.message); process.exit(1); });
