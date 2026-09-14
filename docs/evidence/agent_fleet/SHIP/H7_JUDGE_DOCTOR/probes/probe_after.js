/* probe_after.js -- H7 AFTER-fix verification: every before-repro rerun;
   each section asserts the repro is GONE.
   Run: node probe_after.js */
const path = require('path');
const fs = require('fs');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));
const URL_ = process.argv[2] || 'http://127.0.0.1:8206/?debug=1';
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
  const hand = () => page.evaluate(() => (document.getElementById('hand-state') || {}).textContent);
  const state = () => page.evaluate(() => fetch('/api/state').then(r => r.json()));
  const cells = async () => (await state()).cells.map(c => Number(c.P) || 0);
  const verdict = () => page.evaluate(() => (document.getElementById('verdict') || {}).textContent);
  // project a world point to a pixel with the default camera
  const aimAt = async (wx, wy, wz) => page.evaluate(([wx, wy, wz]) => {
    const c = { r: 26, theta: -0.55, phi: 0.42, target: [0, 4.5, 0] };
    const vsub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
    const vdot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
    const vcross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
    const vnorm = a => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
    const ch = Math.cos(c.phi);
    const eye = [c.target[0] + c.r * ch * Math.sin(c.theta), c.target[1] + c.r * Math.sin(c.phi),
                 c.target[2] + c.r * ch * Math.cos(c.theta)];
    const cv = document.getElementById('gl'); const b = cv.getBoundingClientRect();
    const tanF = Math.tan(45 * Math.PI / 360);
    const fwd = vnorm(vsub(c.target, eye));
    const right = vnorm(vcross(fwd, [0, 1, 0])); const up = vcross(right, fwd);
    const d = vsub([wx, wy, wz], eye); const a = vdot(d, fwd);
    const ndcX = (vdot(d, right) / a) / (tanF * (cv.width / cv.height));
    const ndcY = (vdot(d, up) / a) / tanF;
    return { x: b.left + (ndcX + 1) / 2 * b.width, y: b.top + (1 - ndcY) / 2 * b.height };
  }, [wx, wy, wz]);

  await page.goto(URL_, { waitUntil: 'load' });
  await sleep(2000);
  await page.evaluate(() => fetch('/api/gravity', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ on: false }) }).then(r => r.json()));
  await page.fill('#name-input', 'h7after');
  await page.click('#play-btn'); await sleep(1200);
  try { await page.click('#intro-begin', { timeout: 3000 }); } catch (e) {}
  await sleep(800);

  // ============ D3: mouse hold-release leaves NOTHING pressed (5 cycles) ==
  {
    const px = await aimAt(0, 4.5, 0.3);
    const cycles = [];
    for (let i = 0; i < 5; i++) {
      await page.mouse.move(px.x, px.y);
      await page.mouse.down(); await sleep(900); await page.mouse.up();
      await sleep(1300);   // release settles + one judge-poll beat for the line
      const line = await judgeLine();
      cycles.push({ hand: await hand(), holding: /holding=true/.test(line),
                    pressed: /pressing/.test(await hand()) });
    }
    // release-outside-canvas: press, drag out past 6px (orbit hand-off),
    // release OUTSIDE the canvas -- the press must end exactly once
    await page.mouse.move(px.x, px.y); await page.mouse.down(); await sleep(600);
    await page.mouse.move(50, 60, { steps: 4 });
    await page.mouse.up();
    await sleep(1300);   // the judge line refreshes on the next poll beat
    const outside = { hand: await hand(), holding: /holding=true/.test(await judgeLine()) };
    // alt-tab mid-hold (blur): press, blur the page, check
    await page.mouse.move(px.x, px.y); await page.mouse.down(); await sleep(600);
    await page.evaluate(() => window.dispatchEvent(new Event('blur')));
    await sleep(1300);   // the judge line refreshes on the next poll beat
    const blurClear = { hand: await hand(), holding: /holding=true/.test(await judgeLine()) };
    await page.mouse.up(); await sleep(300);
    R.D3 = { cycles, outside, blurClear };
    const allClean = cycles.every(c => !c.holding && !c.pressed) &&
      !outside.holding && !blurClear.holding;
    R.D3.CLEAN = allClean;
    console.log('D3 5-cycle hold-release:', cycles.map(c => c.pressed ? 'STUCK' : 'clean').join(' '),
      '| drag-out:', JSON.stringify(outside), '| blur:', JSON.stringify(blurClear),
      '=>', allClean ? 'REPRO GONE' : 'STILL BROKEN');
  }

  // ============ D2: every press answers, both paths, taps too ============
  {
    await page.evaluate(() => { const f = document.getElementById('force'); f.value = 50000;
      f.dispatchEvent(new Event('input')); });
    await sleep(300);
    // mouse holds x5 (aimed at the torso)
    const px = await aimAt(0, 4.5, 0.3);
    const mouseAns = [];
    for (let i = 0; i < 5; i++) {
      await page.mouse.move(px.x, px.y); await page.mouse.down(); await sleep(700);
      const during = (await cells())[1];
      await page.mouse.up(); await sleep(900);
      mouseAns.push(during > 20000);
    }
    // SPACE holds x5
    const spaceAns = [];
    for (let i = 0; i < 5; i++) {
      await page.keyboard.down(' '); await sleep(700);
      const during = (await cells())[1];
      await page.keyboard.up(' '); await sleep(900);
      spaceAns.push(during > 20000);
    }
    // taps x3 (down+up ~120ms; the pulse must still land the dent) --
    // measure the PEAK over the pulse window from a CALM base each time
    const waitTorsoCalm = async () => {
      for (let k = 0; k < 20; k++) {
        if ((await cells())[1] < 5000) return true;
        await sleep(700);
      }
      return false;
    };
    const tapAns = [];
    for (let i = 0; i < 3; i++) {
      await waitTorsoCalm();
      const before = (await cells())[1];
      await page.mouse.move(px.x, px.y); await page.mouse.down(); await sleep(120);
      await page.mouse.up();
      let peak = before;
      for (let k = 0; k < 8; k++) { await sleep(150);
        const p = (await cells())[1]; if (p > peak) peak = p; }
      tapAns.push(peak > Math.max(before, 5000) * 1.5);
      await sleep(1000);
    }
    R.D2 = { mouseAns, spaceAns, tapAns };
    const ok = mouseAns.every(Boolean) && spaceAns.every(Boolean) && tapAns.every(Boolean);
    R.D2.CLEAN = ok;
    console.log('D2 mouse:', mouseAns.map(b => b ? 'Y' : 'n').join(''),
      ' space:', spaceAns.map(b => b ? 'Y' : 'n').join(''),
      ' taps:', tapAns.map(b => b ? 'Y' : 'n').join(''),
      '=>', ok ? 'EVERY PRESS ANSWERS' : 'STILL BROKEN');
  }

  // ============ D4: slider three modes + sent-force agreement ============
  {
    await page.keyboard.press('Escape'); await sleep(300);
    const setSlider = async (v) => page.evaluate((v) => {
      const f = document.getElementById('force'); f.value = v;
      f.dispatchEvent(new Event('input'));
    }, v);
    await setSlider(50000); await sleep(150);
    const geo = await page.evaluate(() => {
      const b = document.getElementById('force').getBoundingClientRect();
      return { x: b.x, y: b.y, w: b.width, h: b.height };
    });
    // mode A: drag from thumb to ~6000 N (thumb aim clamped inside the track)
    const frac = v => Math.min(1, Math.max(0, (v - 500) / (50000 - 500)));
    const txOf = v => geo.x + 6 + (geo.w - 12) * frac(v);
    await page.mouse.move(txOf(50000), geo.y + geo.h / 2); await page.mouse.down();
    await page.mouse.move(txOf(6000), geo.y + geo.h / 2, { steps: 10 }); await page.mouse.up();
    await sleep(200);
    const dragVal = Number(await page.evaluate(() => document.getElementById('force').value));
    // mode B: track click at the 6000 N position (from 500 N start)
    await setSlider(500); await sleep(150);
    await page.mouse.click(txOf(6000), geo.y + geo.h / 2); await sleep(200);
    const trackVal = Number(await page.evaluate(() => document.getElementById('force').value));
    // mode C: arrows from 20000 down to ~6000 (140 x ArrowLeft at step 100)
    await setSlider(20000); await sleep(150);
    await page.locator('#force').focus();
    for (let i = 0; i < 140; i++) await page.keyboard.press('ArrowLeft');
    const arrowVal = Number(await page.evaluate(() => document.getElementById('force').value));
    // sent-force agreement: set 6000 via the slider, press, capture the POST
    await setSlider(6000); await sleep(150);
    const label = await page.evaluate(() => document.getElementById('force-label').textContent);
    const meter = await page.evaluate(() =>
      document.getElementById('force-meter-fill').style.width);
    let sentForce = null;
    await page.route('**/api/touch_hit', async route => {
      const req = route.request(); const post = req.postDataJSON();
      sentForce = post.force_n;
      const resp = await route.fetch(); await route.fulfill({ response: resp });
    });
    const px = await aimAt(0.46, 0.18, 0.3);   // the foot
    await page.mouse.move(px.x, px.y); await page.mouse.down(); await sleep(600);
    await page.mouse.up(); await sleep(600);
    await page.unroute('**/api/touch_hit');
    // tolerance: native track/arrows land on the input's own step grid
    const near = (a, b, tol) => Math.abs(a - b) <= tol;
    const okDrag = near(dragVal, 6000, 1500);
    const okTrack = near(trackVal, 6000, 2500);
    const okArrow = near(arrowVal, 6000, 200);
    const okAgree = sentForce === 6000 && label === '6000 N';
    R.D4 = { dragVal, trackVal, arrowVal, label, meter, sentForce,
             CLEAN: okDrag && okTrack && okArrow && okAgree };
    console.log('D4 drag->', dragVal, ' track->', trackVal, ' arrows->', arrowVal,
      '| label', label, ' meter', meter, ' sent', sentForce,
      '=>', R.D4.CLEAN ? 'SLIDER ALIVE + AGREES' : 'STILL BROKEN');
    await page.screenshot({ path: __dirname + '/../shots/after_D4_slider.png' });
  }

  // ============ D1: fresh judge state per lesson; no world leak ==========
  {
    await page.keyboard.press('Escape'); await sleep(400);
    await page.evaluate(() => { const f = document.getElementById('force'); f.value = 50000;
      f.dispatchEvent(new Event('input')); });
    // earn goalMet on L1 (press -> torso wakes), then switch away MID-release
    await page.keyboard.down(' '); await sleep(800); await page.keyboard.up(' ');
    await sleep(200);
    const l1mid = await judge();
    await page.keyboard.press(']'); await sleep(1200);   // straight to L2, mid-release
    const l2 = await judge();
    const l2hand = await hand();
    const l2cells = await cells();
    // back to L1: goalMet must be RESET (passed may survive, goalMet no)
    await page.keyboard.press('Escape'); await sleep(300);
    await page.keyboard.press('['); await sleep(1000);
    const l1back = await judge();
    const ok = l2.id === 'the_gentle_hand' && l2.phase === 'goal' && !l2.goalMet &&
      /hand open|you touched/.test(l2hand) && l1back.phase === 'goal';
    R.D1 = { l1mid, l2, l2hand, l2cells, l1back, CLEAN: ok };
    console.log('D1 L1 mid:', JSON.stringify(l1mid));
    console.log('D1 L2 start:', JSON.stringify(l2), 'hand:', l2hand, 'cells:', JSON.stringify(l2cells));
    console.log('D1 L1 revisit:', JSON.stringify(l1back), '=>', ok ? 'FRESH STATE' : 'STILL LATCHED');
  }

  // ============ D5: no pass without the qualifying input =================
  {
    await page.keyboard.press('Escape'); await sleep(300);
    // park on L2 with force 6000 (would satisfy the cap IF a press happened)
    await page.evaluate(() => { const f = document.getElementById('force'); f.value = 6000;
      f.dispatchEvent(new Event('input')); });
    await page.keyboard.press(']'); await sleep(700);
    await page.route('**/api/state', route => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ cells: [
        { V: 0.287, P: 60000 }, { V: 12.5, P: 0 }, { V: 0.69, P: 0 },
        { V: 0.33, P: 0 }, { V: 0.0, P: 1622780000 }],
        root_y: 0, root_vy: 0, conserve_pct: 0 }) }));
    await sleep(2500);
    const noPress = { verdict: await verdict(), judge: await judge() };
    await page.unroute('**/api/state');
    await sleep(500);
    // now the real input: a genuine sub-8000 N press through the page's
    // SPACE rail -- its foot target is snapped to the nearest mesh vertex,
    // so it cannot miss (a mouse-aimed foot press is a ~10 px shot that a
    // real player can also miss; the ENGINE resolves those honestly).
    // H7 test note: the camera is re-baselined by a fresh page load --
    // earlier sections orbit the camera, and aimAt uses the DEFAULT one.
    await page.goto('http://127.0.0.1:8206/?debug=1', { waitUntil: 'load' });
    await sleep(1800);
    await page.fill('#name-input', 'h7after'); await page.click('#play-btn');
    await sleep(1200);
    try { await page.click('#intro-begin', { timeout: 2000 }); } catch (e) {}
    await sleep(800);
    await page.keyboard.press(']'); await sleep(700);   // L2 the_gentle_hand
    await page.evaluate(() => { const f = document.getElementById('force'); f.value = 6000;
      f.dispatchEvent(new Event('input')); });
    let recordedPress = null;
    await page.route('**/api/touch_hit', async route => {
      const post = route.request().postDataJSON();
      if (post && post.force_n) recordedPress = post.force_n;
      const resp = await route.fetch(); await route.fulfill({ response: resp });
    });
    await page.keyboard.down(' '); await sleep(800);
    const midLine = await judgeLine();
    await page.keyboard.up(' ');
    await sleep(4500);   // goal latch + release + calm
    await page.unroute('**/api/touch_hit');
    const realInput = { verdict: await verdict(), judge: await judge(),
                        recordedPress, midLine };
    const ok = !noPress.judge.goalMet && !noPress.judge.passed;
    R.D5 = { noPress, realInput, CLEAN: ok };
    console.log('D5 injected 60kPa, NO press:', JSON.stringify(noPress),
      '=>', ok ? 'DOES NOT PASS' : 'STILL PASSES UNDONE');
    console.log('D5 real gentle press after:', JSON.stringify(realInput));
    await page.screenshot({ path: __dirname + '/../shots/after_D5_gentle.png' });
  }

  // ============ D6: starved page backs off ================================
  {
    let n = 0;
    await page.route('**/api/**', route => { n++; route.fulfill({ status: 500, body: '{}' }); });
    await sleep(10000);
    await page.unroute('**/api/**');
    const perMin = Math.round(n / 10 * 60);
    R.D6 = { requestsIn10s: n, perMin, CLEAN: perMin < 120 };
    console.log('D6 starved page:', n, 'requests in 10s =', perMin,
      '/min (was 443/min)', '=>', R.D6.CLEAN ? 'BACKING OFF' : 'STILL HAMMERING');
    // the honest unreachable line
    const v = await verdict();
    R.D6.unreachableLine = v;
    console.log('D6 verdict while unreachable:', JSON.stringify(v));
    await sleep(4000); // recovery
  }

  // ============ D7: sealed-solid display + debug gate =====================
  {
    const blood = await page.evaluate(() =>
      (document.getElementById('blood') || {}).textContent);
    const hasSealed = /sealed solid/.test(blood);
    const noGarbage = !/1622/.test(blood);
    // debug gate: reload without ?debug=1 -> judge line stays empty
    await page.goto('http://127.0.0.1:8206/', { waitUntil: 'load' });
    await sleep(2000);
    await page.fill('#name-input', 'h7after'); await page.click('#play-btn');
    await sleep(1500);
    try { await page.click('#intro-begin', { timeout: 2000 }); } catch (e) {}
    await sleep(1500);
    const lineNoDebug = await judgeLine();
    await page.goto('http://127.0.0.1:8206/?debug=1', { waitUntil: 'load' });
    await sleep(2000);
    await page.fill('#name-input', 'h7after'); await page.click('#play-btn');
    await sleep(1500);
    try { await page.click('#intro-begin', { timeout: 2000 }); } catch (e) {}
    await sleep(1500);
    const lineDebug = await judgeLine();
    const ok = hasSealed && noGarbage && lineNoDebug === '' && /^judge: /.test(lineDebug);
    R.D7 = { hasSealed, noGarbage, lineNoDebug: lineNoDebug.slice(0, 40),
             lineDebug: lineDebug.slice(0, 60), CLEAN: ok };
    console.log('D7 blood has "sealed solid":', hasSealed, ' no 1622 garbage:', noGarbage,
      '| debug line empty w/o flag:', lineNoDebug === '',
      ' present with flag:', /^judge: /.test(lineDebug),
      '=>', ok ? 'GUARDS UP' : 'STILL BROKEN');
  }

  R.consoleErrors = consoleErrors.slice(0, 10);
  R.consoleErrorCount = consoleErrors.length;
  fs.writeFileSync(__dirname + '/../after_verify.json', JSON.stringify(R, null, 1));
  console.log('console errors during probe:', consoleErrors.length);
  console.log('WROTE after_verify.json');
  await browser.close();
})().catch(e => { console.error('PROBE FAILED:', e); process.exit(1); });
