/* probe_before.js -- H7 judge-doctor BEFORE-fix repros, one script per defect
   family, headless channel:'chrome' against the 8206 door only.
   Every section prints MECHANISM / OBSERVED / VERDICT lines.
   Run: node probe_before.js  */
const path = require('path');
const fs = require('fs');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));

const URL_ = process.argv[2] || 'http://127.0.0.1:8206';
const OUT = __dirname + '/../before_repro.json';
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const consoleErrors = [];
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  const R = {};

  const judgeLine = () => page.evaluate(() =>
    (document.getElementById('judge-debug') || {}).textContent || '');
  const judge = async () => {
    const m = (await judgeLine()).match(/judge: (\S+) phase=(\S+) goalMet=(\S+) passed=(\S+)/);
    return m ? { id: m[1], phase: m[2], goalMet: m[3] === 'true', passed: m[4] === 'true' } : {};
  };
  const cells = () => page.evaluate(() => fetch('/api/state', { cache: 'no-store' })
    .then(r => r.json()).then(s => (s.cells || []).map(c => Number(c.P) || 0)));
  const hand = () => page.evaluate(() => (document.getElementById('hand-state') || {}).textContent);

  await page.goto(URL_, { waitUntil: 'load' });
  await sleep(2000);

  // ---- shared setup: fresh name, gravity off (restore authored rest) ------
  await page.evaluate(() => fetch('/api/gravity', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ on: false }) }).then(r => r.json()));
  await page.fill('#name-input', 'h7probe');
  await page.click('#play-btn');
  await sleep(1200);
  try { await page.click('#intro-begin', { timeout: 3000 }); } catch (e) {}
  await sleep(800);

  // ======================================================== D3 phantom press
  // MECHANISM: a still click starts the press only at pointerup (endPress ->
  // tryTouch), and holding flips true asynchronously AFTER the up; so the up
  // that STARTS a press can never END it -- every click leaves the hand
  // pressing forever (mouseup ends nothing).
  {
    const box = await page.locator('#gl').boundingBox();
    await page.mouse.move(box.x + box.width * 0.5, box.y + box.height * 0.55);
    await page.mouse.down(); await sleep(2000); await page.mouse.up();
    await sleep(700);
    const afterUp = { hand: await hand(), judge: await judge() };
    // is a cell still pressurised after the release?
    const cellAfterUp = (await cells())[1];
    // does the "let go" chip clear it?
    await page.click('#letgo-btn'); await sleep(600);
    const afterLetgo = { hand: await hand(), judge: await judge(), cell: (await cells())[1] };
    await page.screenshot({ path: __dirname + '/../shots/before_D3_phantom.png' });
    R.D3 = { afterUp, cellAfterUp, afterLetgo };
    console.log('D3 after mouse-up   :', JSON.stringify(afterUp), 'torso Pa=', cellAfterUp);
    console.log('D3 after let-go chip:', JSON.stringify(afterLetgo));
  }

  // ================================================ D4 slider (three modes)
  // MEASURED GEOMETRY: where is the range input, what does H5's (1190,453)
  // actually hit, and do drag / track-click / arrow-keys move the value?
  {
    const geo = await page.evaluate(() => {
      const f = document.getElementById('force');
      const b = f.getBoundingClientRect();
      const at = (x, y) => { const el = document.elementFromPoint(x, y);
        return el ? (el.id || el.tagName + '.' + (el.className || '')) : 'null'; };
      return { rect: { x: b.x, y: b.y, w: b.width, h: b.height },
               h5probe: { at1190_453: at(1190, 453), at1190_431: at(1190, 431) },
               value: f.value, disabled: f.disabled, readonly: f.readOnly };
    });
    // mode A: drag from thumb
    const thumbX = geo.rect.x + geo.rect.w * (20000 - 500) / (50000 - 500);
    const thumbY = geo.rect.y + geo.rect.h / 2;
    await page.mouse.move(thumbX, thumbY); await page.mouse.down();
    await page.mouse.move(thumbX - 120, thumbY, { steps: 8 }); await page.mouse.up();
    await sleep(200);
    const afterDrag = await page.evaluate(() => document.getElementById('force').value);
    // mode B: track click at 25% (should be ~12875)
    const tx = geo.rect.x + geo.rect.w * 0.25, ty = geo.rect.y + geo.rect.h / 2;
    await page.mouse.click(tx, ty); await sleep(200);
    const afterTrack = await page.evaluate(() => document.getElementById('force').value);
    // mode C: arrow keys (element focus after click)
    await page.keyboard.press('ArrowLeft'); await page.keyboard.press('ArrowLeft');
    await page.keyboard.press('ArrowLeft'); await sleep(200);
    const afterArrows = await page.evaluate(() => document.getElementById('force').value);
    // mode D: H5's aim -- click (1190,453) then arrows
    await page.evaluate(() => document.getElementById('force').blur());
    await page.mouse.click(1190, 453); await sleep(200);
    const focusAfterH5 = await page.evaluate(() =>
      document.activeElement ? (document.activeElement.id || document.activeElement.tagName) : 'none');
    await page.keyboard.press('ArrowLeft'); await sleep(200);
    const afterH5 = await page.evaluate(() => document.getElementById('force').value);
    R.D4 = { geo, afterDrag, afterTrack, afterArrows, focusAfterH5, afterH5 };
    console.log('D4 geometry:', JSON.stringify(geo));
    console.log('D4 drag->', afterDrag, ' track->', afterTrack, ' arrows->', afterArrows,
      ' | H5 aim focus:', focusAfterH5, 'value->', afterH5);
    await page.screenshot({ path: __dirname + '/../shots/before_D4_slider.png' });
  }

  // ====================================================== D2 presses die
  // MECHANISM CANDIDATES: (a) mouse path alternates press/release because the
  // press starts at up; (b) SPACE path: keyup releases nothing, and the next
  // keydown while holding only cycles -- if the engine refuses a second
  // /tick_touch while a press is held, every second scripted press is dead.
  // Test: engine-level double touch through the page door, then 5 scripted
  // SPACE press-release cycles, counting answers.
  {
    await page.keyboard.press('Escape'); await sleep(400);
    // engine gate: two touch_hits with NO clear between
    const dbl = await page.evaluate(async () => {
      const post = (hit) => fetch('/api/touch_hit', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(hit) }).then(r => r.json());
      const target = [0.0, 4.5, 0.35];
      const r1 = await post({ hit: target, force_n: 20000 });
      await new Promise(res => setTimeout(res, 800));
      const mid = await fetch('/api/state').then(r => r.json());
      const p1 = (mid.cells || [])[1] ? Number(mid.cells[1].P) || 0 : -1;
      const r2 = await post({ hit: target, force_n: 30000 });   // second press, no clear
      await new Promise(res => setTimeout(res, 800));
      const mid2 = await fetch('/api/state').then(r => r.json());
      const p2 = (mid2.cells || [])[1] ? Number(mid2.cells[1].P) || 0 : -1;
      await fetch('/api/touch_clear', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
      return { r1, p1, r2, p2 };
    });
    await sleep(3000);
    // scripted SPACE x5: down 900ms -> up (nothing) -> Escape -> wait
    const spaceAnswers = [];
    for (let i = 0; i < 5; i++) {
      const before = (await cells())[1];
      await page.keyboard.down(' '); await sleep(900); await page.keyboard.up(' ');
      await sleep(400);
      const during = (await cells())[1];
      await page.keyboard.press('Escape'); await sleep(600);
      spaceAnswers.push({ before, during, answered: during > before + 5000 });
      await sleep(1200);
    }
    // mouse x5: down 900ms -> up (the current page presses ON up)
    const mouseAnswers = [];
    for (let i = 0; i < 5; i++) {
      const before = (await cells())[1];
      await page.mouse.move(720, 500); await page.mouse.down(); await sleep(900);
      await page.mouse.up(); await sleep(500);
      const during = (await cells())[1];
      await page.keyboard.press('Escape'); await sleep(600);
      mouseAnswers.push({ before, during, answered: during > before + 5000 });
      await sleep(1200);
    }
    R.D2 = { engineDoubleTouch: dbl, spaceAnswers, mouseAnswers };
    console.log('D2 engine double-touch:', JSON.stringify(dbl));
    console.log('D2 SPACE answers:', spaceAnswers.map(a => a.answered ? 'Y' : 'n').join(''));
    console.log('D2 mouse answers:', mouseAnswers.map(a => a.answered ? 'Y' : 'n').join(''));
  }

  // ==================================== D1 latch across lessons + world leak
  // MECHANISM: lessonState is per-id and NEVER reset at lesson start, and
  // showLesson neither clears a held engine touch nor resets lastTouchForce
  // -- a press held in lesson N leaks its pressures into lesson N+1's judge.
  {
    await page.keyboard.press('Escape'); await sleep(400);
    // hold a press, then switch lessons WITHOUT releasing
    await page.keyboard.down(' '); await sleep(900);
    const holdingDuring = await judge();
    await page.keyboard.up(' ');           // no keyup handler: still holding?
    await page.keyboard.press(']');        // straight to lesson 2, hand still on
    await sleep(1400);
    const l2Start = { judge: await judge(), cells: await cells(), hand: await hand() };
    // leave the world dirty; go back to 1: is L1 still goalMet from before?
    await page.keyboard.press('Escape'); await sleep(400);
    await page.keyboard.press('['); await sleep(800);
    const l1Revisit = await judge();
    R.D1 = { holdingDuring, l2Start, l1Revisit };
    console.log('D1 during L1 press:', JSON.stringify(holdingDuring));
    console.log('D1 L2 start (hand never released):', JSON.stringify(l2Start));
    console.log('D1 L1 revisit:', JSON.stringify(l1Revisit));
  }

  // ============================================== D5 pass without the input
  // MECHANISM: forceOk = !cap || !lastTouchForce || <= cap -- a lesson whose
  // qualifying press NEVER happened (lastTouchForce stays 0 on the mouse
  // path) passes as soon as the cell reads high for ANY reason. Inject a
  // state frame with cell0 above the gentle threshold and no press made.
  {
    await page.keyboard.press('Escape'); await sleep(300);
    await page.keyboard.press(']'); await sleep(600);   // L2 the_gentle_hand
    await page.route('**/api/state', route => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ cells: [
        { V: 0.287, P: 60000 }, { V: 12.5, P: 0 }, { V: 0.69, P: 0 },
        { V: 0.33, P: 0 }, { V: 0.0, P: 1622780000 }],
        root_y: 0, root_vy: 0, conserve_pct: 0 }) }));
    await sleep(2500);   // several judge polls against the injected frame
    const verdictText = await page.evaluate(() =>
      (document.getElementById('verdict') || {}).textContent);
    const j = await judge();
    await page.unroute('**/api/state');
    R.D5 = { injectedNoPress: { verdict: verdictText, judge: j } };
    console.log('D5 L2 with injected cell0=60kPa, NO press ever:',
      JSON.stringify({ verdict: verdictText, judge: j }));
    // distinct sentences: collect the pass line for L1..L3 from the source
    const src = await page.evaluate(() => fetch('/').then(r => r.text()));
    const passLines = (src.match(/PASSED[^']*/g) || []).slice(0, 8);
    R.D5.passLinesInSource = passLines;
    console.log('D5 pass sentences in page source:', JSON.stringify(passLines));
  }

  // ==================================================== D6 the 429 storm
  // MECHANISM: pollVerts retries ?delta=key IMMEDIATELY on failure and the
  // 333 ms timer never backs off -- under starvation the page hammers ~6
  // req/s forever. Count /api/verts + /api/state + /api/... requests for 8 s
  // with every API answer poisoned (500) -- the no-server-behavior probe.
  {
    let n = 0;
    await page.route('**/api/**', route => { n++; route.fulfill({ status: 500, body: '{}' }); });
    const t0 = Date.now();
    await sleep(8000);
    await page.unroute('**/api/**');
    const ratePerMin = n / 8 * 60;
    R.D6 = { requestsIn8s: n, ratePerMin: Math.round(ratePerMin) };
    console.log('D6 starved page made', n, 'API requests in 8s =',
      Math.round(ratePerMin), '/min (budget 600/min)');
  }

  R.consoleErrors = consoleErrors.slice(0, 10);
  fs.writeFileSync(OUT, JSON.stringify(R, null, 1));
  console.log('WROTE', OUT);
  await browser.close();
})().catch(e => { console.error('PROBE FAILED:', e); process.exit(1); });
