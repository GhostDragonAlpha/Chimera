/* h9_click_probe.js -- focused probe for W4 call site 3: the silent
   canvas-click touch (tryTouch -> engine-resolved res.hit -> snd('press',
   force, res.hit)). Route-intercepted instrumented sound.js copy, same
   harness as h9_audit.js. One click-press, then release. */
const path = require('path');
const fs = require('fs');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));
const { inject } = { inject: body => body.replace(
  /window\.ChimeraSound = \{[\s\S]*?\};/,
  fs.readFileSync('E:/ChimeraWork/slot-01/docs/evidence/agent_fleet/SHIP/H9_AUDIO/harness_snippet.js', 'utf8')) };
const OUT = 'E:/ChimeraWork/slot-01/docs/evidence/agent_fleet/SHIP/H9_AUDIO/h9_click_probe.json';
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  await ctx.addInitScript(() => {
    window.__acCreated = 0;
    const O = window.AudioContext;
    if (O) window.AudioContext = class extends O {
      constructor(...a) { super(...a); window.__acCreated++; }
    };
  });
  await ctx.route('**/sound.js', async route => {
    const resp = await route.fetch();
    await route.fulfill({ status: 200, contentType: 'application/javascript', body: inject(await resp.text()) });
  });
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
  await page.goto('http://127.0.0.1:8206', { waitUntil: 'load' });
  await sleep(2500);
  await page.fill('#name-input', 'h9-click');
  await page.click('#play-btn');
  await sleep(1500);
  try { await page.click('#intro-begin', { timeout: 4000 }); } catch (e) {}
  await sleep(4500);
  const box = await page.locator('#gl').boundingBox();
  // a still click (down+up, no drag): pointerup path calls tryTouch
  await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
  await sleep(1800);
  const judge = await page.evaluate(() =>
    ((document.getElementById('judge-debug') || {}).textContent || '').trim());
  const log = await page.evaluate(() => window.__SNDLOG);
  const pressEntries = log.filter(x => x.m === 'press');
  await page.screenshot({ path: 'E:/ChimeraWork/slot-01/docs/evidence/agent_fleet/SHIP/H9_AUDIO/05_canvas_click.png' });
  await page.keyboard.press('Escape');
  await sleep(400);
  fs.writeFileSync(OUT, JSON.stringify({
    at: new Date().toISOString(),
    clickPressFired: pressEntries.length > 0,
    pressEntries, judge, acCreated: await page.evaluate(() => window.__acCreated),
    consoleErrors: errs
  }, null, 1));
  console.log(JSON.stringify({ clickPressFired: pressEntries.length > 0, pressEntries, judge, acCreated: await page.evaluate(() => window.__acCreated), consoleErrors: errs }, null, 1));
  await browser.close();
})().catch(e => { console.error('CLICK PROBE FAILED:', e); process.exit(1); });
