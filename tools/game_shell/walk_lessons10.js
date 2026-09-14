/* walk_lessons10.js -- THE G5 TEN-LESSON WALK, headless (base: the W6 walk).
   A private Chrome drives the game page the way a player would:
   enters the name "walker", walks ALL TEN lessons by the page's own
   keyboard rail (SPACE = the page's lesson touch targets, '=' / '-' force
   in 2000 N steps, 'p'/pose button, ESC let go, ']' next lesson), then
   reads the progress file. Evidence -> C:/Users/allen/Desktop/CHIMERA_PROOF/R4_WALK_TEN.

   G5 additions (this revision):
   1. GATE v2: the walk does not start until the SERVED page carries the
      lessons 6-10 judge. TWO markers, polled every 60 s, up to 40 min:
      'pose_pair' (the_balance -- W1/G3) and 'pressure_isolation'
      (the_cascade -- the re-tuned pack's goal type, which the served
      KNOWN_GOAL_TYPES does not evaluate yet; without it lesson 8 HOLDs
      forever and a ten-lesson walk would be a false verdict). If
      pressure_isolation never appears inside the cap the walk RUNS ANYWAY
      as a DIAGNOSTIC: the nine implementable lessons play, lesson 8's hold
      is documented with measured numbers, and the exit is honest failure.
      If pose_pair itself never appears, no walk is attempted at all.
   2. FRESH-WALK RESETS, through the game's own doors only:
      a. the prior walker holds 9/10 passes on disk, so entering play would
         start at lesson 8 -- POST /api/progress {lessons:{}} clears the
         save (the previous save is backed up into the evidence dir first);
      b. the world's gravity was left ON by the previous walk (root settled
         at ~9.5 mm), so POST /api/gravity {on:false} returns the body to
         its authored rest -- lessons 1-8 play from gauge zeros and
         the_stand (L9) performs its real fall when the page enables.
      Both are logged, and the pre-reset world state is snapshotted.
   3. PAGE-ERROR LEDGER: every pageerror / console error is counted; the
      exit code demands ten FRESH in-session passes AND zero page errors.
      Poll rates (sampler 700 ms, calm-wait 500 ms) sit inside the server's
      documented 600 req/min stream budget.

   Run: node tools/game_shell/walk_lessons10.js [url] */
const path = require('path');
const fs = require('fs');
const http = require('http');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));

const URL_ = process.argv[2] || 'http://127.0.0.1:8206';
const NAME = 'walker';
const REPO_PROGRESS = 'E:/ChimeraWork/slot-01/tools/game_shell/progress';
const SHOTS = 'C:/Users/allen/Desktop/CHIMERA_PROOF/R4_WALK_TEN';
const sleep = ms => new Promise(r => setTimeout(r, ms));

// -- the gate: the served page must carry the lessons 6-10 judge -----------
function servedPage() {
  return new Promise((resolve, reject) => {
    http.get(URL_ + '/?t=' + Date.now(), res => {
      let b = '';
      res.on('data', c => { b += c; });
      res.on('end', () => resolve(b));
    }).on('error', reject);
  });
}
const GATE_CAP_MS = 40 * 60 * 1000;
async function gate() {
  const t0 = Date.now();
  let n = 0;
  while (Date.now() - t0 < GATE_CAP_MS) {
    n++;
    try {
      const html = await servedPage();
      const pp = html.includes('pose_pair');
      const pi = html.includes('pressure_isolation');
      if (pp && pi) {
        console.log('GATE: served page carries pose_pair AND pressure_isolation' +
          ' (poll ' + n + ', waited ' + ((Date.now() - t0) / 1000).toFixed(0) + ' s) -- walking all ten.');
        return { mode: 'full', waitedS: (Date.now() - t0) / 1000, polls: n };
      }
      console.log('GATE poll ' + n + ': pose_pair=' + pp + ' pressure_isolation=' + pi +
        ' -- waiting 60 s');
    } catch (e) {
      console.log('GATE poll ' + n + ': fetch failed (' + e.message + ') -- waiting 60 s');
    }
    await sleep(60000);
  }
  // the cap: pose_pair governs whether any walk is legal at all
  let pp = false;
  try { pp = (await servedPage()).includes('pose_pair'); } catch (e) {}
  if (!pp) return { mode: 'abort', waitedS: (Date.now() - t0) / 1000, polls: n };
  console.log('GATE TIMEOUT after ' + ((Date.now() - t0) / 60000).toFixed(0) +
    ' min: the served page never gained pressure_isolation.' +
    ' Running the DIAGNOSTIC walk: nine lessons play, lesson 8\'s hold is' +
    ' documented with measured numbers, the exit is honest failure.');
  return { mode: 'diagnostic', waitedS: (Date.now() - t0) / 1000, polls: n };
}

(async () => {
  const g = await gate();
  if (g.mode === 'abort') {
    console.log('GATE TIMEOUT after 40 min: the served page never gained pose_pair.' +
      ' No walk was attempted -- reporting the wait honestly.');
    fs.mkdirSync(SHOTS, { recursive: true });
    fs.writeFileSync(SHOTS + '/gate_aborted.json', JSON.stringify(
      { at: new Date().toISOString(), waited_s: Math.round(g.waitedS), polls: g.polls }, null, 1));
    process.exit(2);
  }

  const diagnostic = g.mode === 'diagnostic';
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });
  const pageErrors = [];
  page.on('pageerror', e => {
    pageErrors.push('pageerror: ' + e.message);
    console.log('PAGE ERROR:', e.message);
  });
  page.on('console', m => {
    if (m.type() === 'error') {
      pageErrors.push('console: ' + m.text());
      console.log('CONSOLE ERROR:', m.text());
    }
  });
  fs.mkdirSync(SHOTS, { recursive: true });

  await page.goto(URL_, { waitUntil: 'load' });
  await sleep(2500);                                   // world attach (topology+verts)
  await page.screenshot({ path: SHOTS + '/walk10_start.png' });

  // -- FRESH-WALK RESET a: back up the prior save, then clear it ----------
  try {
    const prior = fs.readFileSync(REPO_PROGRESS + '/' + NAME + '.json', 'utf8');
    fs.writeFileSync(SHOTS + '/walker_progress_before.json', prior);
    console.log('RESET: prior walker save backed up (' +
      (JSON.parse(prior).lessons ? Object.keys(JSON.parse(prior).lessons).length : 0) + ' passes on disk)');
  } catch (e) { console.log('RESET: no prior walker save on disk (' + e.message + ')'); }
  const post = (p, body) => page.evaluate(pa =>         // one arg: Playwright's
    fetch(pa.p, { method: 'POST',                       // evaluate takes exactly one
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify(pa.body) }).then(r => r.json()).catch(() => null),
    { p, body });
  await post('/api/progress', { name: NAME, lessons: {}, seen_intro: true });
  const progCheck = await page.evaluate(n =>
    fetch('/api/progress?name=' + encodeURIComponent(n)).then(r => r.json()), NAME);
  console.log('RESET: walker progress cleared -- lessons now: ' +
    JSON.stringify(Object.keys(progCheck.lessons || {})));

  // -- FRESH-WALK RESET b: gravity off, the body back to its authored rest --
  const rootLine = async () => page.evaluate(() =>
    fetch('/api/state').then(r => r.json()).then(s =>
      'gravity_on=' + s.gravity_on +
      ' root_y=' + Number(s.root_y).toFixed(4) +
      ' root_vy=' + Number(s.root_vy).toFixed(4)));
  console.log('WORLD BEFORE: ' + await rootLine());
  fs.writeFileSync(SHOTS + '/world_state_before.json', JSON.stringify(
    await page.evaluate(() => fetch('/api/state').then(r => r.json())), null, 1));
  console.log('GRAVITY RESET: ' + JSON.stringify(
    await post('/api/gravity', { on: false })));
  await sleep(1500);
  console.log('WORLD AT REST: ' + await rootLine());

  // sign in and enter play
  await page.fill('#name-input', NAME);
  await page.click('#play-btn');
  await sleep(2000);
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
  const cellLine = async () => {
    try {
      const s = await state();
      const c = (s.cells || []).map(x => Math.round(Number(x.P) || 0));
      return 'feet=' + (c[0] || 0) + ' torso=' + (c[1] || 0) + ' thighs=' + (c[2] || 0) +
        ' shins=' + (c[3] || 0) + ' Pa';
    } catch (e) { return 'cells unreadable'; }
  };

  // the lesson pack, for honest threshold-vs-measured reporting
  const pack = await page.evaluate(() => fetch('/lessons.json').then(r => r.json()));
  const goalOf = id => ((pack.lessons || []).find(l => l.id === id) || {}).goal || {};
  fs.writeFileSync(SHOTS + '/lesson_pack_served.json', JSON.stringify(pack, null, 1));

  // background sampler: peak |P| per cell since the last resetPeaks()
  let peaks = [], sampling = true;
  (async function sampler() {
    while (sampling) {
      try {
        const s = await state();
        (s.cells || []).forEach((c, i) => {
          peaks[i] = Math.max(peaks[i] || 0, Math.abs(Number(c.P) || 0));
        });
      } catch (e) { /* a silent beat is not a verdict */ }
      await sleep(700);
    }
  })();
  const resetPeaks = () => { peaks = []; };
  const peaksLine = () =>
    peaks.map((p, i) => 'cell' + i + '=' + Math.round(p) + ' Pa').join(' ') || 'no cells seen';
  const dismissPayoffIfUp = async (tag) => {
    // E4's payoff fires the moment the set completes (all ten) and an
    // overlay owns the keyboard. Dismiss through the real save flow.
    try {
      await page.click('#payoff-save', { timeout: 2500 });
      console.log(tag + ' payoff overlay: dismissed through #payoff-save (real save flow)');
      await sleep(1500);
      return true;
    } catch (e) { return false; }
  };
  const verdicts = [];
  const report = async (tag, extra) => {
    const l = await lesson();
    const goal = goalOf(l.id);
    console.log(tag + ' judge: ' + JSON.stringify(
      { id: l.id, phase: l.phase, goalMet: l.goalMet, passed: l.passed }));
    console.log(tag + ' line  : ' + l.line);
    console.log(tag + ' goal  : ' + JSON.stringify(goal) + (extra || ''));
    console.log(tag + ' peaks : ' + peaksLine());
    verdicts.push({ tag, id: l.id, phase: l.phase, goalMet: l.goalMet,
                    passed: l.passed, peaks: peaksLine(), goal });
    await dismissPayoffIfUp(tag);
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
      await sleep(500);
    }
    console.log('   calm=' + calm + ' after ' + ((Date.now() - t0) / 1000).toFixed(1) +
      's  final |P| Pa: ' + (last || []).map(p => Math.round(p)).join(' '));
    await sleep(1600);                                  // the judge's next poll
  };

  const press = async (ms) => {                       // SPACE down, hold, up
    await page.keyboard.down(' ');
    await sleep(900);                                 // POST + one judge poll
    console.log('   mid-press: ' + await judgeLine());
    console.log('   mid-press cells: ' + await cellLine());
    await sleep(Math.max(0, ms - 900));
    await page.keyboard.up(' ');
  };
  // L8's press, traced: one measured line per 500 ms of hold -- the numbers
  // a hold diagnosis is written from.
  const pressTrace = async (ms) => {
    await page.keyboard.down(' ');
    const t0 = Date.now();
    let first = true;
    while (Date.now() - t0 < ms) {
      await sleep(500);
      console.log('   trace ' + ((Date.now() - t0) / 1000).toFixed(1) + 's: ' +
        await cellLine() + (first ? '  |  ' + await judgeLine() : ''));
      first = false;
    }
    await page.keyboard.up(' ');
  };
  const key = async (k) => { await page.keyboard.press(k); await sleep(300); };
  const forceTo = async (keyK, n) => { for (let i = 0; i < n; i++) await key(keyK); };
  const poseClick = async (tag) => {                  // the page's ONLY pose path
    await page.click('#pose-btn');
    await sleep(3000);
    console.log('   ' + tag + ' pose: ' + await judgeLine());
  };

  // -- the page's OTHER real touch verb: a still CLICK. tryTouch posts the
  // local camera + click pixel; the ENGINE resolves the hit and presses
  // there. Used by L7: MEASURED, the pack's SPACE target's nearest vertex
  // tops at ~1.93 MPa at the 50 kN slider max, but a per-vertex sweep
  // (171 torso vertices, 50 kN) peaks at 29.8 MPa near (0.87, 8.54, 0.28)
  // -- well past the 3 MPa bar.
  const cam0 = { r: 26, theta: -0.55, phi: 0.42, target: [0, 4.5, 0] };
  const vsub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  const vdot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const vcross = (a, b) => [a[1] * b[2] - a[2] * b[1],
                            a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const vnorm = a => { const l = Math.hypot(a[0], a[1], a[2]) || 1;
                       return [a[0] / l, a[1] / l, a[2] / l]; };
  const clickWorld = async (wx, wy, wz, tag) => {
    const ch = Math.cos(cam0.phi);
    const eye = [cam0.target[0] + cam0.r * ch * Math.sin(cam0.theta),
                 cam0.target[1] + cam0.r * Math.sin(cam0.phi),
                 cam0.target[2] + cam0.r * ch * Math.cos(cam0.theta)];
    const rect = await page.evaluate(() => {
      const c = document.getElementById('gl');
      const b = c.getBoundingClientRect();
      return { left: b.left, top: b.top, width: b.width, height: b.height,
               aspect: c.width / c.height };
    });
    const tanF = Math.tan(45 * Math.PI / 360);
    const fwd = vnorm(vsub(cam0.target, eye));
    const right = vnorm(vcross(fwd, [0, 1, 0]));
    const up = vcross(right, fwd);
    const d = vsub([wx, wy, wz], eye);
    const a = vdot(d, fwd);
    const ndcX = (vdot(d, right) / a) / (tanF * rect.aspect);
    const ndcY = (vdot(d, up) / a) / tanF;
    const bx = rect.left + (ndcX + 1) / 2 * rect.width;
    const by = rect.top + (1 - ndcY) / 2 * rect.height;
    console.log('   ' + tag + ' click aim px: (' + bx.toFixed(1) + ',' + by.toFixed(1) + ')');
    const readP1 = async () => {
      try {
        const s = await state();
        return (s.cells || [])[1] ? Number(s.cells[1].P) || 0 : 0;
      } catch (e) { return 0; }
    };
    const spiral = [[0, 0], [4, 0], [-4, 0], [0, 4], [0, -4],
                    [8, 0], [-8, 0], [0, 8], [0, -8],
                    [6, 6], [-6, 6], [6, -6], [-6, -6]];
    for (const [dx, dy] of spiral) {
      await page.keyboard.press('Escape');               // the hand opens first
      await sleep(700);
      await page.mouse.move(bx + dx, by + dy); await sleep(150);
      await page.mouse.down(); await sleep(150); await page.mouse.up();
      await sleep(900);                                  // POST + the dent set
      const p1 = await readP1();
      console.log('   ' + tag + ' click (' + (bx + dx).toFixed(0) + ',' +
        (by + dy).toFixed(0) + ') -> torso ' + Math.round(p1) + ' Pa');
      if (p1 >= 3000000) {
        // a second tap of the same strong spot: the spike window (~0.7 s at
        // tau=0.5) now straddles two judge polls instead of gambling on one
        await page.mouse.down(); await sleep(400); await page.mouse.up();
        await sleep(1600);
        return true;
      }
    }
    return false;
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
  await press(2200);                 // SPACE while holding cycles + reposts the shin target
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

  // L7 THE HEAVY HAND: 3 MPa on the torso, force maxed. MEASURED: the
  // pack's SPACE target's nearest vertex tops at ~1.93 MPa at 50 kN, so
  // the walker plays the lesson the way a player would -- CLICK a strong
  // spot (the page's real click verb; the engine resolves the hit). The
  // measured per-vertex response peaks at 29.8 MPa near (0.87, 8.54, 0.28).
  resetPeaks();
  await key(']');
  await forceTo('=', 15);                              // ensure 50000 N
  await clickWorld(0.872, 8.542, 0.276, 'L7');
  await page.keyboard.press('Escape');
  await waitCalm(8000, 30000);
  await report('L7');

  // L8 THE CASCADE (pressure_isolation): press the belly hard -- the torso
  // must wake past 15000 Pa while the feet and shins stay under 100 Pa.
  // The press is TRACED: one measured line per 500 ms of hold. If the
  // served judge does not evaluate pressure_isolation yet, the lesson
  // HOLDs by design ("the teachers have not built this lesson yet") and
  // the trace is the diagnosis -- the walk never forces a latch.
  resetPeaks();
  await key(']');
  console.log('L8 pre-press: ' + await judgeLine());
  console.log('L8 pre-press cells: ' + await cellLine());
  await pressTrace(3500);
  await page.keyboard.press('Escape');
  await waitCalm(8000, 25000);
  {
    const l8 = await lesson();
    const g8 = goalOf(l8.id);
    let diag = '';
    if (!l8.passed && g8.type === 'pressure_isolation') {
      const pt = peaks[1] || 0;
      const pq = Math.max(peaks[0] || 0, peaks[3] || 0);
      const worldSat = pt >= (g8.threshold_pa || 0) && pq < (g8.quiet_max_pa || 0);
      diag = '  DIAGNOSTIC: pack wants torso >= ' + g8.threshold_pa +
        ' Pa with cells 0+3 < ' + g8.quiet_max_pa + ' Pa; measured on this press: torso peak ' +
        Math.round(pt) + ' Pa, quiet peak ' + Math.round(pq) + ' Pa -> world ' +
        (worldSat ? 'SATISFIED the condition; the served judge does not evaluate ' + g8.type
                  : 'did NOT satisfy the condition');
      console.log('L8' + diag);
    }
    const rep = await report('L8');
    if (diag) verdicts[verdicts.length - 1].note = diag;
  }

  // L9 THE STAND (gravity_on): advancing to the lesson fires the page's own
  // start hook (/api/gravity {on:true}; the judge latches only when the
  // PAGE's enable resolved -- `armed`). Gravity was reset OFF before the
  // walk, so this is the real fall: root 0 -> ~9.5 mm settle in < 1 s.
  resetPeaks();
  await key(']');
  let armed = false;
  for (let i = 0; i < 10; i++) {
    if (/armed=true/.test(await judgeLine())) { armed = true; break; }
    await sleep(500);
  }
  if (!armed) {
    console.log('L9 HOOK MISS: page never armed; driving /api/gravity directly (diagnostic)');
    await post('/api/gravity', { on: true });
  }
  console.log('L9 armed=' + armed + '  world: ' + await rootLine());
  await sleep(2500);                                   // the fall: settle < 1 s
  console.log('L9 settling: ' + await rootLine());
  await sleep(3500);                                   // judge polls see the settle
  await report('L9', '  root: ' + await rootLine());

  // L10 THE GRADUATION (cells_woken): cycle the five targets -- belly, left
  // foot, right foot, left shin (cells 1, 0, 0, 3 = three DISTINCT cells),
  // then release and let the whole body heal. Under gravity the resting
  // cells read exactly 0, so the heal still passes (SPEC section 10).
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
  await page.screenshot({ path: SHOTS + '/walk10_end.png' });

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
  fs.writeFileSync(SHOTS + '/progress_' + NAME + '.json', JSON.stringify(prog, null, 1));
  fs.writeFileSync(SHOTS + '/world_state_after.json', JSON.stringify(
    await page.evaluate(() => fetch('/api/state').then(r => r.json())), null, 1));
  console.log('WORLD AFTER: ' + await rootLine());

  // THE VERDICT TABLE -- ten FRESH in-session passes, in pack order
  const packIds = (pack.lessons || []).map(l => l.id);
  console.log('\n===== TEN-LESSON VERDICT TABLE (this session) =====');
  verdicts.forEach((v, i) => {
    const ok = v.passed && v.id === packIds[i];
    console.log(' ' + (i + 1) + '. ' + v.id.padEnd(16) + (ok ? 'PASS' : 'FAIL') +
      '  phase=' + v.phase + ' goalMet=' + v.goalMet + '  ' + v.peaks +
      (v.note ? '\n     ' + v.note : ''));
  });
  const fresh = verdicts.filter((v, i) => v.passed && v.id === packIds[i]).length;
  const passedKeys = Object.keys(prog.lessons || {}).filter(k => prog.lessons[k].passed);
  console.log('FRESH PASSES THIS SESSION: ' + fresh + ' of 10');
  console.log('PROGRESS FILE: ' + passedKeys.length + ' of 10 -> ' + passedKeys.join(', '));
  console.log('PAGE ERRORS: ' + pageErrors.length,
              pageErrors.length ? JSON.stringify(pageErrors) : '(zero)');
  fs.writeFileSync(SHOTS + '/verdicts_' + NAME + '.json',
                   JSON.stringify({ url: URL_, name: NAME, mode: g.mode,
                                    gateWaitedS: Math.round(g.waitedS),
                                    freshPasses: fresh,
                                    progressPasses: passedKeys.length,
                                    pageErrors: pageErrors,
                                    lessons: verdicts }, null, 1));

  await browser.close();
  const ok = fresh === 10 && passedKeys.length === 10 && pageErrors.length === 0;
  if (!ok && diagnostic) {
    console.log('DIAGNOSTIC WALK END: the served judge never gained' +
      ' pressure_isolation; lesson 8 held by design. Reported honestly, exit 1.');
  }
  process.exit(ok ? 0 : 1);
})().catch(e => { console.error('WALK FAILED:', e.message); process.exit(1); });
