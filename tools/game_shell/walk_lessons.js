/* walk_lessons.js -- THE R4 COMPLETION WALK, headless, ALL TEN LESSONS.
   A private Chrome drives the game page the way a player would:
   enters a name, walks all ten lessons (touch/pose/gravity by the page's
   own keyboard rail and buttons -- the page's SPACE handler posts
   /api/touch_hit {hit, force_n} at each lesson's (vertex-snapped) touch
   target, the pose button posts /api/pose, the gravity lesson's start
   hook posts /api/gravity), saves, and reports the progress file.
   Zero windows, zero interference with the operator's desktop.
   While walking it polls /api/state itself and logs each lesson's peak
   cell pressures next to the lesson's threshold, so a refusal to pass
   is a NUMBER, not a shrug. (W1 lane: progress under the fresh name
   "walker" -- Alan's file is never touched.)
   Run: node tools/game_shell/walk_lessons.js [url] */
const path = require('path');
const fs = require('fs');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));

const URL_ = process.argv[2] || 'http://127.0.0.1:8206';
const NAME = 'walker';
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });
  page.on('pageerror', e => console.log('PAGE ERROR:', e.message));
  const shots = 'C:/Users/allen/Desktop/CHIMERA_PROOF/R4_WALK_TEN';
  fs.mkdirSync(shots, { recursive: true });

  await page.goto(URL_, { waitUntil: 'load' });
  await sleep(2500);                                   // world attach (topology+verts)
  await page.screenshot({ path: shots + '/walk10_start.png' });

  // sign in and enter play
  await page.fill('#name-input', NAME);
  await page.click('#play-btn');
  await sleep(2000);
  // E4 intro overlay (a fresh name is greeted once): it owns the keyboard
  // while up, so begin before any lesson driving
  try {
    await page.click('#intro-begin', { timeout: 5000 });
    console.log('intro overlay: begun');
  } catch (e) { console.log('intro overlay: not shown'); }
  await sleep(1000);

  const state = () => page.evaluate(() => fetch('/api/state').then(r => r.json()));
  const judgeLine = async () => page.evaluate(() =>
    (document.getElementById('judge-debug') || {}).textContent || '');
  const lesson = async () => {
    const line = await judgeLine();                    // "judge: id phase=.. goalMet=.. passed=.. .."
    const m = String(line || '').match(/judge: (\S+) phase=(\S+) goalMet=(\S+) passed=(\S+)/);
    return { id: m ? m[1] : '?', phase: m ? m[2] : '?',
             goalMet: m ? m[3] === 'true' : false, passed: m ? m[4] === 'true' : false,
             line };
  };
  const rootLine = async () => page.evaluate(() =>
    fetch('/api/state').then(r => r.json()).then(s =>
      'gravity_on=' + s.gravity_on +
      ' root_y=' + Number(s.root_y).toFixed(4) +
      ' root_vy=' + Number(s.root_vy).toFixed(4)));

  // the lesson pack, for honest threshold-vs-measured reporting
  const pack = await page.evaluate(() => fetch('/lessons.json').then(r => r.json()));
  const goalOf = id => ((pack.lessons || []).find(l => l.id === id) || {}).goal || {};

  // background sampler: peak Pa per cell since the last resetPeaks()
  let peaks = [], sampling = true;
  (async function sampler() {
    while (sampling) {
      try {
        const s = await state();
        (s.cells || []).forEach((c, i) => {
          peaks[i] = Math.max(peaks[i] || -1e9, Number(c.P) || 0);
        });
      } catch (e) { /* a silent beat is not a verdict */ }
      await sleep(350);
    }
  })();
  const resetPeaks = () => { peaks = []; };
  const peaksLine = () =>
    peaks.map((p, i) => 'cell' + i + '=' + Math.round(p) + ' Pa').join(' ') || 'no cells seen';
  const report = async (tag, extraGoalCheck) => {
    const l = await lesson();
    const g = goalOf(l.id);
    console.log(tag + ' judge: ' + JSON.stringify(
      { id: l.id, phase: l.phase, goalMet: l.goalMet, passed: l.passed }));
    console.log(tag + ' line  : ' + l.line);
    console.log(tag + ' goal  : ' + JSON.stringify(g) +
      (extraGoalCheck || ''));
    console.log(tag + ' peaks : ' + peaksLine());
    return l;
  };

  // THE WAIT IS PHYSICS: after ESC the pressure decays with tau = 0.5 s from
  // whatever peak the press actually reached. The judge passes on the first
  // poll where every |P| < 1000 Pa. So: hold the scripted minimum wait, then
  // keep waiting until the ENGINE itself reports every cell calm, plus one
  // judge poll beat. Never a guess, never a lowered bar.
  const waitCalm = async (minMs, capMs) => {
    const t0 = Date.now();
    let calm = false, last = null;
    while (Date.now() - t0 < capMs) {
      if (Date.now() - t0 >= minMs) {
        try {
          const s = await state();
          const ps = (s.cells || []).map(c => Math.abs(Number(c.P) || 0));
          last = ps;
          if (ps.length && ps.every(p => p < 1000)) { calm = true; break; }
        } catch (e) { /* a silent beat is not a verdict */ }
      }
      await sleep(250);
    }
    console.log('   calm=' + calm + ' after ' + ((Date.now() - t0) / 1000).toFixed(1) +
      's  final |P| Pa: ' + (last || []).map(p => Math.round(p)).join(' '));
    await sleep(1600);                                  // the judge's next poll
  };

  const press = async (ms) => {                       // SPACE down, hold, up
    await page.keyboard.down(' ');
    await sleep(900);                                 // POST + one judge poll
    console.log('   mid-press: ' + await judgeLine()); // touchTarget set + holding == POST ok:true
    await sleep(Math.max(0, ms - 900));
    await page.keyboard.up(' ');
  };
  const key = async (k) => { await page.keyboard.press(k); await sleep(300); };
  const forceTo = async (keyK, n) => { for (let i = 0; i < n; i++) await key(keyK); };
  const poseClick = async (tag) => {                  // the page's ONLY pose path
    await page.click('#pose-btn');
    await sleep(3000);
    console.log('   ' + tag + ' pose: ' + await judgeLine());
  };

  // L1 WAKE THE CELL: max force, press the belly, release, heal
  resetPeaks();
  await forceTo('=', 15);
  await press(2500);
  await page.keyboard.press('Escape');
  await waitCalm(5000, 20000);
  await report('L1');

  // L2 THE GENTLE HAND: force under 8000, press the foot target
  resetPeaks();
  await key(']');
  await forceTo('-', 22);                              // 50000 -> 6000 N
  await press(2000);
  await page.keyboard.press('Escape');
  await waitCalm(4500, 20000);
  await report('L2');

  // L3 THE HEALING: force back up, wake any cell, release, wait
  resetPeaks();
  await key(']');
  await forceTo('=', 37);                              // -> capped 50000 N
  await press(2500);
  await page.keyboard.press('Escape');
  await waitCalm(6000, 20000);
  await report('L3');

  // L4 BEND THE KNEE: the pose button (the page posts /api/pose knee_L 40)
  resetPeaks();
  await key(']');
  await poseClick('L4');
  await report('L4');

  // L5 THE WHOLE BODY: two compartments (cycled targets), then release
  resetPeaks();
  await key(']');
  await press(2200);                 // belly target
  await press(2200);                 // cycles to the shin target
  await page.keyboard.press('Escape');
  await waitCalm(5500, 25000);
  await report('L5');

  // L6 THE BALANCE (pose_pair): the pose button posts BOTH wishes through
  // the page's one sender -- /api/pose ankle_L(17) +5, then ankle_R(18) -5.
  // The judge latches each accepted post separately, any order.
  resetPeaks();
  await key(']');
  await poseClick('L6');
  await report('L6');

  // L7 THE HEAVY HAND: force maxed, HOLD the belly -- 3 MPa wants ~43 kN
  resetPeaks();
  await key(']');
  await forceTo('=', 15);                              // ensure 50000 N
  await press(3000);
  await page.keyboard.press('Escape');
  await waitCalm(8000, 25000);
  await report('L7');

  // L8 THE CASCADE: the belly is the ONLY touch target -- the shins must
  // answer (cell 3 >= 5 kPa) from the belly press alone. Hold long enough
  // for the coupling to equilibrate and for one judge poll to see it.
  resetPeaks();
  await key(']');
  await press(6000);
  await page.keyboard.press('Escape');
  await waitCalm(8000, 25000);
  await report('L8');

  // L9 THE STAND (gravity_on): advancing to the lesson fires the page's own
  // start hook (/api/gravity {on:true}; the judge latches only when the
  // PAGE's enable resolved -- `armed`). If the hook missed we drive the
  // route ourselves as a DIAGNOSTIC, and say so: a directly-driven enable
  // cannot arm the page's judge, so that outcome is a finding, not a pass.
  resetPeaks();
  await key(']');
  let armed = false;
  for (let i = 0; i < 10; i++) {
    if (/armed=true/.test(await judgeLine())) { armed = true; break; }
    await sleep(500);
  }
  if (!armed) {
    console.log('L9 HOOK MISS: page never armed; driving /api/gravity directly (diagnostic)');
    await page.evaluate(() => fetch('/api/gravity', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ on: true }) }).then(r => r.json()).catch(() => null));
  }
  console.log('L9 armed=' + armed + '  world: ' + await rootLine());
  await sleep(2500);                                   // the fall: settle < 1 s
  console.log('L9 settling: ' + await rootLine());
  await sleep(3500);                                   // judge polls see the settle
  await report('L9', '  root: ' + await rootLine());

  // L10 THE GRADUATION (cells_woken): cycle the five targets -- belly, left
  // foot, right foot, left shin (cells 1, 0, 0, 3 = three DISTINCT cells),
  // then release and let the whole body heal.
  resetPeaks();
  await key(']');
  await forceTo('=', 15);                              // ensure 50000 N
  await press(2500);                 // target[0] belly   -> cell 1
  await press(2500);                 // cycles to [1] left foot  -> cell 0
  await press(2500);                 // cycles to [2] right foot -> cell 0
  await press(2500);                 // cycles to [3] left shin  -> cell 3
  await page.keyboard.press('Escape');
  await waitCalm(8000, 30000);
  await report('L10');

  sampling = false;
  await sleep(1500);                                   // E4's payoff watcher beat
  await page.screenshot({ path: shots + '/walk10_end.png' });

  // save + read back. All ten fresh passes in one session raise E4's payoff
  // overlay; its save button dismisses it AND clicks the real save flow.
  let saved = false;
  try {
    await page.click('#payoff-save', { timeout: 15000 });
    saved = true;
    console.log('payoff overlay: saved through it');
  } catch (e) {
    console.log('payoff overlay: not shown -- saving through the sidebar button');
  }
  if (!saved) { await page.click('#save-btn'); }
  await sleep(1500);
  const prog = await page.evaluate(n =>
    fetch('/api/progress?name=' + encodeURIComponent(n)).then(r => r.json()), NAME);
  console.log('SAVED PROGRESS:', JSON.stringify(prog.lessons ? Object.keys(prog.lessons) : prog));
  fs.writeFileSync(shots + '/progress_' + NAME + '.json', JSON.stringify(prog, null, 1));

  const passed = Object.keys(prog.lessons || {}).filter(k => prog.lessons[k].passed);
  console.log('PASSED LESSONS:', passed.length, 'of 10 ->', passed.join(', '));
  await browser.close();
  process.exit(passed.length === 10 ? 0 : 1);
})().catch(e => { console.error('WALK FAILED:', e.message); process.exit(1); });
