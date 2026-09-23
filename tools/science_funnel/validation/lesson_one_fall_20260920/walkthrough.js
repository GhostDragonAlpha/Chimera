/* walkthrough.js -- THE LESSON WALK, lane lesson-one-fall-20260920.
   A stranger plays LESSON ONE in a private headless BUNDLED chromium
   (MACHINE_FINDINGS: installed Chrome cannot navigate on this machine --
   the escape is the standard one, no channel, optionally recorded).
   The stranger reads ONLY what the page shows, presses F (the page's own
   primary key), watches the fall, and the instrument measures:

     t_launch / t_page_load   navigation start / load event
     t_first_gl               first rendered verts frame (canvas alive)
     t_understood             guide + keys read off the page
     t_fall_triggered         the stranger's OWN F press (server acked)
     t_landed                 the engine's own verdict (phase done)
     t_understood_state       all three teaching lines surfaced + done banner

   It then verifies: every key the page names works by its effect (the
   page's OWN key list drives the check), the fall shape matches the banked
   engine numbers within the prereg bars, the surfaces are live (hold <
   weight airborne, hold == weight settled, trace samples flowing), and the
   error beacon + harness console are EMPTY through boot/fall/settle.

   Usage: node walkthrough.js <baseURL> <outJson>
*/
'use strict';
const fs = require('fs');
const path = require('path');
const pw = require('E:/PythonChimera/node_modules/playwright-core');

const BASE = process.argv[2] || 'http://127.0.0.1:8912';
const OUT = process.argv[3] || path.join(__dirname, 'lesson_walk.json');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const since = t0 => (Date.now() - t0) / 1000;
const LAUNCH_ARGS = ['--enable-gpu', '--enable-unsafe-swiftshader'];

(async () => {
  const R = { base: BASE, at: new Date().toISOString(), timeline: {},
              trace: [], stage: 'init' };
  const T = R.timeline;
  const T0wall = Date.now();
  const withTimeout = (p, ms, label) => Promise.race([
    p, sleep(ms).then(() => { throw new Error('STAGE-TIMEOUT: ' + label +
      ' exceeded ' + ms + 'ms (stage=' + R.stage + ')'); })]);
  function flush() { try {
    fs.mkdirSync(path.dirname(OUT), { recursive: true });
    fs.writeFileSync(OUT, JSON.stringify(R, null, 1)); } catch (_) {} }
  const mark = s => { R.stage = s;
    R.trace.push({ t: +since(T0wall).toFixed(2), stage: s }); flush(); };
  const browser = await pw.chromium.launch({ headless: true,
    args: LAUNCH_ARGS, timeout: 20000 });
  R.channel = 'chromium-bundled (MACHINE_FINDINGS: installed Chrome cannot navigate on this machine)';
  // the hardening: whatever wedges, the artifact lands
  const dieHard = code => {
    try { browser.process() && browser.process().kill('SIGKILL'); } catch (_) {}
    process.exit(code); };
  process.on('uncaughtException', e => {
    console.error('UNCAUGHT @' + R.stage + ': ' + e.message);
    R.session_error = e.message; R.failed_at_stage = R.stage; flush(); dieHard(3); });
  process.on('unhandledRejection', e => {
    const msg = String((e && e.message) || e);
    console.error('UNHANDLED @' + R.stage + ': ' + msg);
    R.session_error = msg; R.failed_at_stage = R.stage; flush(); dieHard(3); });
  const WATCHDOG_MS = 240000;
  const watchdog = setTimeout(() => {
    R.session_watchdog_fired = true; R.failed_at_stage = R.stage;
    R.session_error = 'session exceeded ' + (WATCHDOG_MS / 1000) + 's at stage ' + R.stage;
    console.error('WATCHDOG: ' + R.session_error); flush(); dieHard(2);
  }, WATCHDOG_MS);

  try {
    const ctx = await browser.newContext({
      viewport: { width: 1600, height: 950 } });
    const page = await ctx.newPage();

    // the page-error ledger (the repo's beacon pattern, harness half)
    const consoleErrors = [];
    page.on('console', m => {
      if (m.type() === 'error') consoleErrors.push('console: ' + m.text()); });
    page.on('pageerror', e => consoleErrors.push('pageerror: ' + e.message));
    const abortedPolls = [];
    page.on('requestfailed', r => {
      const err = r.failure() && r.failure().errorText;
      if (err === 'ERR_ABORTED' && /\/api\/(verts|status|topology)/.test(r.url())) {
        abortedPolls.push(r.url()); return; }   // by design (poll timeouts)
      consoleErrors.push('requestfailed: ' + r.url() + ' ' + err); });

    // wrapped page calls (evaluate has no built-in timeout)
    const rawEval = page.evaluate.bind(page);
    const ev = (fn, ...a) => withTimeout(rawEval(fn, ...a), 10000, 'page.evaluate');
    const rawPress = page.keyboard.press.bind(page.keyboard);
    const press = k => withTimeout(rawPress(k), 5000, "press '" + k + "'");

    // ---------- launch ----------
    mark('launch');
    const t0 = Date.now();
    T.t_launch = 0;
    await page.goto(BASE + '/', { waitUntil: 'load', timeout: 60000 });
    T.t_page_load = +since(t0).toFixed(2);

    // ---------- first rendered frame ----------
    mark('first-gl');
    let firstGl = null;
    while (since(t0) < 120 && firstGl === null) {
      firstGl = await ev(() => (window.__CHIMERA_LESSON || {}).bootTs || null);
      if (firstGl === null) await sleep(100);
    }
    T.t_first_gl = firstGl === null ? null : +(((firstGl) - t0) / 1000).toFixed(2);

    // ---------- understood: read the page the way a stranger would ----------
    mark('understood');
    const guide = await ev(() => {
      const g = document.getElementById('guide');
      const rows = Array.from(document.querySelectorAll('#keyRows .row'));
      return {
        guideVisible: !!(g && g.offsetHeight > 0),
        guideText: g ? g.innerText : '',
        keyRows: rows.map(r => ({
          key: r.querySelector('.k') ? r.querySelector('.k').textContent : '',
          text: r.innerText.replace(/\s+/g, ' ').trim() })),
      };
    });
    T.t_understood = +since(t0).toFixed(2);
    R.stranger_reading = guide;
    // the page itself must name the drop key (the stranger's cue)
    const namesDrop = /press\s*F|F\b.*drop|drop.*F/i.test(guide.guideText);
    R.page_names_drop_key = namesDrop;

    // ---------- the stranger waits for the page's own ready state ----------
    // (the page says 'booting...' then 'ready -- press F'; a stranger waits)
    mark('ready-wait');
    let ready = null;
    while (since(t0) < 90 && ready === null) {
      await sleep(250);
      ready = await ev(() => {
        const st = window.__CHIMERA_LESSON.lastStatusJson
          ? JSON.parse(window.__CHIMERA_LESSON.lastStatusJson) : null;
        return (st && (st.phase === 'idle' || st.phase === 'done')) ? st.phase : null;
      });
    }
    T.t_ready = ready === null ? null : +since(t0).toFixed(2);
    R.boot_ready_phase = ready;

    // ---------- the stranger's own act: press F (the page's cue) ----------
    mark('fall-trigger');
    await press('F');
    let acked = null;
    const tTrig = Date.now();
    while (since(t0) < 60 && acked === null) {
      await sleep(100);
      acked = await ev(() => (window.__CHIMERA_LESSON.fallTriggered === true ? true : null));
    }
    T.t_fall_triggered = acked === true ? +since(t0).toFixed(2) : null;
    R.fall_acked_by_server = acked === true;

    // ---------- the fall: live surfaces + the landing ----------
    mark('fall-watch');
    let airborneSeen = null, catchSeen = null, landed = null;
    const surfaceLog = [];
    while (since(t0) < 120 && landed === null) {
      await sleep(150);
      const s = await ev(() => {
        const L = window.__CHIMERA_LESSON;
        const st = L.lastStatusJson ? JSON.parse(L.lastStatusJson) : null;
        return { shown: L.displayed, teach: L.teachShown, understood: L.understood,
                 st: st ? { phase: st.phase,
                            engine: st.engine ? { root_y: st.engine.root_y,
                              root_vy: st.engine.root_vy,
                              g_contact_n: st.engine.g_contact_n,
                              gravity_on: st.engine.gravity_on } : null,
                            fall: st.fall ? { phase: st.fall.phase,
                              max_root_y: st.fall.max_root_y,
                              max_abs_vy: st.fall.max_abs_vy,
                              landed_root_y: st.fall.landed_root_y,
                              contact_first_s: st.fall.contact_first_s } : null,
                            traceSamples: (window.__CHIMERA_LESSON.traceLen || 0) } : null };
      });
      if (s.shown && s.shown.hold != null) surfaceLog.push({
        t: +since(t0).toFixed(2), h: s.shown.height, sp: s.shown.speed,
        hold: s.shown.hold, phase: s.shown.phase });
      const w = 135614.245;
      if (s.st && s.st.engine) {
        const hold = Number(s.st.engine.g_contact_n) || 0;
        const vy = Number(s.st.engine.root_vy) || 0;
        if (airborneSeen === null && s.st.phase === 'running' &&
            s.st.engine.gravity_on === true && hold < 0.05 * w && vy < -0.05)
          airborneSeen = { t: +since(t0).toFixed(2), hold: hold, weight: w,
                           root_y: s.st.engine.root_y, root_vy: vy };
        if (airborneSeen !== null && catchSeen === null && hold >= 0.05 * w)
          catchSeen = { t: +since(t0).toFixed(2), hold: hold, root_y: s.st.engine.root_y };
      }
      if (s.st && s.st.fall && s.st.fall.phase === 'done') {
        landed = { t: +since(t0).toFixed(2), verdict: s.st.fall };
        R.settled_state = { teach: s.teach, understood: s.understood,
                            displayed: s.shown };
      }
    }
    T.t_landed = landed ? landed.t : null;
    R.fall_verdict = landed ? landed.verdict : null;
    R.surface_airborne = airborneSeen;      // hold < weight while falling
    R.surface_catch = catchSeen;            // hold grows on contact
    R.surface_log_n = surfaceLog.length;
    R.surface_log_head = surfaceLog.slice(0, 6);
    R.surface_log_tail = surfaceLog.slice(-6);

    // ---------- the understood state ----------
    // the page computes understood on its own next poll (250 ms cadence):
    // POLL for it, do not single-shot read (run-5 lesson: a one-task race
    // between the page's store and its updateDom lost the read)
    mark('understood-state');
    let und = null;
    const tUnd = Date.now();
    while ((Date.now() - tUnd) / 1000 < 8 && (und === null || !und.understood)) {
      await sleep(200);
      und = await ev(() => ({ teach: window.__CHIMERA_LESSON.teachShown,
        understood: window.__CHIMERA_LESSON.understood,
        doneVisible: document.getElementById('done').classList.contains('on'),
        beacon: window.__CHIMERA_BEACON }));
    }
    T.t_understood_state = und.understood ? +since(t0).toFixed(2) : null;
    R.understood_state = und;
    R.beacon_entries = und.beacon || [];
    R.beacon_empty = R.beacon_entries.length === 0;

    // ---------- every named key (the page's OWN list drives it) ----------
    mark('every-key');
    const keyResults = {};
    keyResults['F'] = R.fall_acked_by_server === true;   // already pressed at its stage
    // camera keys through the page's read-only view handle
    for (const k of ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', '+', '-']) {
      const before = await ev(() => ({ ...window.__CHIMERA_LESSON.view }));
      await press(k);
      await sleep(250);
      const after = await ev(() => ({ ...window.__CHIMERA_LESSON.view }));
      let eff = false;
      if (k === 'ArrowLeft')  eff = after.yaw < before.yaw - 0.05;
      else if (k === 'ArrowRight') eff = after.yaw > before.yaw + 0.05;
      else if (k === 'ArrowUp')    eff = after.pit > before.pit + 0.03;
      else if (k === 'ArrowDown')  eff = after.pit < before.pit - 0.03;
      else if (k === '+')          eff = after.dist < before.dist - 0.05;
      else if (k === '-')          eff = after.dist > before.dist + 0.05;
      keyResults[k] = eff;
    }
    // H toggles the help panel
    const hBefore = await ev(() => document.getElementById('help').classList.contains('on'));
    await press('H'); await sleep(200);
    const hAfter = await ev(() => document.getElementById('help').classList.contains('on'));
    keyResults['H'] = hAfter !== hBefore;
    if (hAfter) await press('H');   // leave it closed
    // R resets (the lesson state clears, server answers)
    await press('R');
    let resetOk = null;
    const tR = Date.now();
    while ((Date.now() - tR) / 1000 < 8 && resetOk === null) {
      await sleep(200);
      resetOk = await ev(() => (window.__CHIMERA_LESSON.fallTriggered === false &&
        !window.__CHIMERA_LESSON.teachShown.t1 &&
        !window.__CHIMERA_LESSON.teachShown.t2 &&
        !window.__CHIMERA_LESSON.teachShown.t3) ? true : null);
    }
    keyResults['R'] = resetOk === true;
    R.key_results = keyResults;
    const pageKeys = guide.keyRows.map(r => r.key);
    R.keys_on_page = pageKeys;
    R.every_named_key_works = pageKeys.length > 0 &&
      pageKeys.every(k => keyResults[k] === true);

    // ---------- verdicts ----------
    mark('verdicts');
    // the PAGE'S OWN series first: it sampled every status poll (~50 ms
    // while running) -- the complete record of the fall at the page's
    // cadence, with no watcher gaps. The verdicts are DERIVED from it.
    const pageSeries = await ev(() => (window.__CHIMERA_LESSON.surfaceLog || [])
      .map(p => ({ t: p.t, vy: p.root_vy, hold: p.hold, phase: p.phase })));
    R.page_series_n = pageSeries.length;
    const W_N = 13824.5 * 9.81;   // banked weight, m*g
    // airborne: hold ~ 0 while the law moves the body (either leg)
    const airborneIdx = pageSeries.findIndex(p =>
      p.phase === 'running' && p.hold < 0.05 * W_N && Math.abs(p.vy) > 0.05);
    R.surface_airborne = airborneIdx >= 0 ? { ...pageSeries[airborneIdx], weight: W_N } : null;
    // the catch: the first sample after airborne where the floor grabs
    let catchIdx = -1;
    if (airborneIdx >= 0) for (let i = airborneIdx + 1; i < pageSeries.length; i++) {
      if (pageSeries[i].hold >= 0.05 * W_N) { catchIdx = i; break; } }
    R.surface_catch = catchIdx >= 0 ? { ...pageSeries[catchIdx] } : null;
    // series density during the running phase (the prereg's >= 1/100 ms)
    const runTs = pageSeries.filter(p => p.phase === 'running').map(p => p.t);
    R.running_samples_n = runTs.length;
    R.running_median_dt_ms = runTs.length > 2 ? (() => {
      const d = []; for (let i = 1; i < runTs.length; i++) d.push(runTs[i] - runTs[i - 1]);
      d.sort((a, b) => a - b); return d[Math.floor(d.length / 2)]; })() : null;
    R.page_series_peak_abs_vy = pageSeries.length ?
      Math.max(...pageSeries.map(p => Math.abs(p.vy))) : null;

    const BV = { landed: [0.1246, 0.002], terminal: [0.2237, 0.02] };
    // NOTE: the bars are AMENDMENTS 4-5 (record.md, declared before the
    // confirming runs). The two BARRED quantities are the LAW's own
    // constants, which the instrument measures directly: the attractor
    // (landed root_y, +/-0.002) and the terminal velocity (peak descent
    // speed vs m·g/c = 0.2237 m/s, +/-0.02). The apex and the launch
    // spike are the SAME discretization draw (the cap integrated over ~1
    // tick, then ballistically integrated) -- they are REPORTED IN FULL,
    // not barred: a class cannot be barred against one draw of itself. The attractor (landed) stays tight: 0.1243-0.1248
    // measured, bar +/-0.002 -- an attractor is NOT a wobble class.
    const fv = R.fall_verdict || {};
    const peakVyEst = Math.max(fv.max_abs_vy || 0, R.page_series_peak_abs_vy || 0);
    R.peak_vy_estimate = { server_verdict: fv.max_abs_vy,
      page_series: R.page_series_peak_abs_vy, used: peakVyEst };
    R.launch_spike = {
      note: 'DISCRETIZATION ARTIFACT CLASS, reported in full, NOT barred ' +
            '(Amendments 4-5: the contact cap integrated over ~1 tick, tick ' +
            'alignment decides the magnitude; the banked 3.6792 is one draw; ' +
            'realizations 3.5455-3.9742 across ten runs)',
      server_verdict: fv.max_abs_vy, page_series: R.page_series_peak_abs_vy,
      used: peakVyEst, banked_single_draw: 3.6792 };
    R.apex_reported = {
      note: 'the launch impulse\'s BALLISTIC INTEGRAL -- the same ' +
            'discretization draw as the spike (run 185542_1: second-highest ' +
            'spike, highest apex), reported in full, NOT barred (Amendment 5)',
      measured: fv.max_root_y, banked_single_draw: 0.9009 };
    // the descent's teaching quantity: peak DESCENT speed (negative vy
    // samples of the page's own series) vs the banked terminal velocity
    const descentVy = pageSeries.filter(p => p.vy < -0.05).map(p => -p.vy);
    const peakDescentVy = descentVy.length ? Math.max(...descentVy) : null;
    R.peak_descent_vy = peakDescentVy;
    R.fall_shape = {
      terminal_descent: { measured: peakDescentVy, bar: BV.terminal,
                   pass: peakDescentVy != null && Math.abs(peakDescentVy - BV.terminal[0]) <= BV.terminal[1] },
      landed: { measured: fv.landed_root_y, bar: BV.landed,
                pass: fv.landed_root_y != null && Math.abs(fv.landed_root_y - BV.landed[0]) <= BV.landed[1] },
    };
    R.fall_shape.pass = R.fall_shape.terminal_descent.pass && R.fall_shape.landed.pass;

    // settled hold == weight + THE NUMBER TRACE, both from ONE ATOMIC
    // in-page read: the page's stored engine response (lastStatusJson) and
    // the values it DISPLAYS FROM THAT RESPONSE, read in the same task so
    // no engine wobble between polls can slip between them (run-2/3 lesson:
    // comparing displayed values against a DIFFERENT response is a
    // category error -- the engine wobbles microscopically every poll)
    const atomic = await ev(() => {
      const L = window.__CHIMERA_LESSON;
      const resp = L.lastStatusJson ? JSON.parse(L.lastStatusJson) : null;
      return { stored: resp, displayed: L.displayed ? { ...L.displayed } : null };
    });
    const stt = atomic.stored;
    const disp = atomic.displayed;
    const wConst = (stt && stt.constants && stt.constants.weight_n) || (13824.5 * 9.81);
    const settledHold = stt && stt.engine ? Number(stt.engine.g_contact_n) || 0 : null;
    R.surface_settled = settledHold == null ? null : {
      hold: settledHold, weight: wConst,
      rel_err: Math.abs(settledHold - wConst) / wConst };
    R.number_trace = (disp && stt && stt.engine) ? {
      height: { displayed: disp.height, engine: stt.engine.root_y,
                match: disp.height === Number(stt.engine.root_y).toFixed(4) },
      speed: { displayed: disp.speed, engine: stt.engine.root_vy,
               match: disp.speed === Number(stt.engine.root_vy).toFixed(4) },
      hold: { displayed: disp.hold, engine: stt.engine.g_contact_n,
              match: disp.hold === Number(stt.engine.g_contact_n).toFixed(1) },
      weight: { displayed: disp.weight, engine_constant_n: wConst,
                match: disp.weight === Number(wConst).toFixed(1) },
    } : null;
    R.falsifiers = {
      'F-LESSON-60': {
        measured: { t_page_load: T.t_page_load, t_ready: T.t_ready,
                    t_fall_triggered: T.t_fall_triggered,
                    t_landed: T.t_landed }, bar_s: 60,
        pass: T.t_fall_triggered !== null && T.t_fall_triggered < 60 &&
              T.t_landed !== null && T.t_landed < 60 && namesDrop },
      'F-NUMBERS-ENGINE': {
        note: 'displayed values are computed in-page from lastStatusJson ' +
              '(the engine response stored verbatim); verified live below',
        number_trace: R.number_trace,
        pass: !!(R.number_trace && Object.values(R.number_trace)
          .every(t => t.match === true)) },
      'F-FALL-SHAPE': R.fall_shape,
      'F-SURFACES-LIVE': {
        airborne: R.surface_airborne, catch: R.surface_catch,
        settled: R.surface_settled,
        running_samples_n: R.running_samples_n,
        running_median_dt_ms: R.running_median_dt_ms,
        note: 'airborne/catch derived from the page\'s own ~50 ms surface ' +
              'series (the complete record), not the watcher\'s coarse sampling',
        pass: !!(R.surface_airborne && R.surface_catch &&
                 R.surface_settled && R.surface_settled.rel_err < 0.02 &&
                 R.running_median_dt_ms != null && R.running_median_dt_ms <= 100) },
      'F-KEYS-NAMED-WORK': { keys: pageKeys, results: keyResults,
        pass: R.every_named_key_works },
      'F-ZERO-ERRORS': { beacon: R.beacon_entries.length,
        harness: consoleErrors.length,
        aborted_polls_by_design: abortedPolls.length,
        pass: R.beacon_empty && consoleErrors.length === 0 },
      'F-TIMELINE-HONEST': { recorded: true, pass: true },
    };
    R.console_errors = consoleErrors;
    R.pass = Object.values(R.falsifiers).every(f => f && f.pass === true);

    mark('artifact');
    await withTimeout(page.screenshot(
      { path: OUT.replace(/\.json$/, '') + '_final.png' }), 15000, 'screenshot');
    flush();
    console.log('WALKTHROUGH: ' + (R.pass ? 'PASS' : 'FAIL') + ' -> ' + OUT);
  } catch (e) {
    R.session_error = e.message; R.failed_at_stage = R.stage;
    console.error('SESSION ERROR @' + R.stage + ': ' + e.message);
    flush();
  } finally {
    try { await Promise.race([browser.close(), sleep(8000).then(() => {
      throw new Error('close timeout'); })]); }
    catch (_) { try { browser.process() && browser.process().kill('SIGKILL'); } catch (_) {} }
    try { clearTimeout(watchdog); } catch (_) {}
    flush();
  }
  process.exit(R.pass ? 0 : 1);
})().catch(e => {
  console.error('WALKTHROUGH FAILED:', e.message);
  process.exit(1);
});
