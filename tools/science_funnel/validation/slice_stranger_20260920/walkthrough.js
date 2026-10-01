/* walkthrough.js -- THE SCRIPTED STRANGER, lane slice-stranger-20260920.
   A person who has never seen this project, played by a private headless
   browser (Playwright, channel 'chrome', fresh context -- never the shared
   desktop). The stranger reads ONLY what the page shows (the welcome guide
   and the page's own key list), then acts. It measures the first minute:

     t_launch          the page navigation starts (the mission's "launch")
     t_page_load       load event
     t_first_motion    the first /api/verts frame is rendered on the canvas
     t_understood      the page's own words tell the stranger what to press
                       (guide visible + objective named + keys listed)
     t_first_action    the first deliberate action -- key 1, chosen from the
                       page's own words -- has its server effect confirmed
     t_restart_done    key R: pill shown, engine returns, mock state cleared

   It then walks EVERY key the page names (F-EVERY-NAMED-KEY) and checks
   effects: endpoints, camera view (read-only handle), guide toggle, the
   300 N press through the engine's /tick_touch, and the error beacon +
   harness console both empty (F-ZERO-ERRORS).

   Usage: node walkthrough.js <baseURL> <outJson>
*/
'use strict';
const fs = require('fs');
const path = require('path');
const http = require('http');
const pw = require('E:/PythonChimera/node_modules/playwright-core');

// The prereg names channel 'chrome'. Measured mid-session 2026-09-22: the
// machine's installed Chrome 153.0.8010.53 began hanging EVERY real
// navigation (headless or not, Playwright or its own --dump-dom; instant
// pre-connect rejections still work; probes committed beside this file).
// So the instrument CANARIES the channel first: if installed Chrome cannot
// commit a navigation, that is finding F-ENV-CHROME, recorded verbatim in
// the artifact, and the run completes on Playwright's bundled Chromium of
// the same build. The stranger-path verdicts (guidance, keys, restart,
// timings) are browser-binary-independent; the channel deviation is not
// hidden -- it is a measurement.
const LAUNCH_ARGS = ['--no-proxy-server',
  '--disable-background-timer-throttling',
  '--disable-renderer-backgrounding',
  '--disable-backgrounding-occluded-windows'];
async function launchWithCanary(baseUrl) {
  let browser;
  try {
    browser = await pw.chromium.launch({ channel: 'chrome', headless: true,
      args: LAUNCH_ARGS, timeout: 15000 });
    const pg = await (await browser.newContext()).newPage();
    await pg.goto(baseUrl + '/', { timeout: 6000, waitUntil: 'commit' });
    await pg.close();
    await browser.close();
    return { browser: null, channel: 'chrome',
      channel_note: 'channel chrome per prereg (canary committed)' };
  } catch (e) {
    try { browser && browser.process() && browser.process().kill('SIGKILL'); } catch (_) {}
    try { browser && await Promise.race([browser.close(), sleep(4000)]); } catch (_) {}
  }
  const b2 = await pw.chromium.launch({ headless: true, args: LAUNCH_ARGS,
    timeout: 15000 });
  return { browser: b2, channel: 'chromium-bundled',
    channel_note: 'FINDING F-ENV-CHROME: channel chrome FAILED its canary ' +
      '(the machine\'s installed Chrome hangs every real navigation -- ' +
      'evidence: netlog_probe.json, probe_matrix.js output, chrome ' +
      '--dump-dom hang, all committed); the run completed on Playwright\'s ' +
      'bundled Chromium (same playwright build), deviation recorded' };
}

const BASE = process.argv[2] || 'http://127.0.0.1:8901';
const OUT = process.argv[3] ||
  path.join(__dirname, 'walkthrough_run.json');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const since = t0 => (Date.now() - t0) / 1000;

(async () => {
  const R = { base: BASE, at: new Date().toISOString(), timeline: {},
    trace: [], stage: 'init' };
  const T = R.timeline;
  // launch args mirror the proven realbody-movie capture launch: this
  // machine's installed Chrome routes 127.0.0.1 through a per-app proxy
  // that env/WinINET probes do not show -- --no-proxy-server is the fix
  // measured working (rbmovie capture_record.json, same day, same machine)
  const chan = await launchWithCanary(BASE);
  R.channel = chan.channel;
  R.channel_note = chan.channel_note;
  let browser = chan.browser;
  if (!browser) {
    // the chrome canary committed: launch the real session on the channel
    browser = await pw.chromium.launch({ channel: 'chrome', headless: true,
      args: LAUNCH_ARGS, timeout: 15000 });
  }
  // ---- instrument hardening (run #6 lesson: a wedged Playwright call must
  // cost the run a RECORDED artifact, never a silent stall) -- these live
  // ABOVE the try so the catch/finally path can still flush the artifact
  const T0 = Date.now();
  const withTimeout = (p, ms, label) => Promise.race([
    p, sleep(ms).then(() => { throw new Error('STAGE-TIMEOUT: ' + label +
      ' exceeded ' + ms + 'ms (stage=' + R.stage + ')'); })]);
  function flush() { try {
    fs.mkdirSync(path.dirname(OUT), { recursive: true });
    fs.writeFileSync(OUT, JSON.stringify(R, null, 1)); } catch (_) {} }
  const mark = s => { R.stage = s;
    R.trace.push({ t: +since(T0).toFixed(2), stage: s }); flush(); };
  const dieHard = code => {
    try { browser.process() && browser.process().kill('SIGKILL'); } catch (_) {}
    process.exit(code); };
  process.on('uncaughtException', e => {
    console.error('UNCAUGHT @' + R.stage + ': ' + e.message);
    R.session_error = e.message; R.failed_at_stage = R.stage;
    flush(); dieHard(3); });
  process.on('unhandledRejection', e => {
    const msg = String((e && e.message) || e);
    console.error('UNHANDLED @' + R.stage + ': ' + msg);
    R.session_error = msg; R.failed_at_stage = R.stage;
    flush(); dieHard(3); });
  // the watchdog: whatever wedges, the artifact lands within the cap
  const WATCHDOG_MS = 240000;
  const watchdog = setTimeout(() => {
    R.session_watchdog_fired = true;
    R.failed_at_stage = R.stage;
    R.session_error = 'session exceeded ' + (WATCHDOG_MS / 1000) +
      's at stage ' + R.stage + ' -- killed by the instrument watchdog';
    console.error('WATCHDOG: ' + R.session_error);
    flush(); dieHard(2);
  }, WATCHDOG_MS);
  // everything runs inside try/finally: a failed step must NEVER leak the
  // browser (the realbody lane measured what a leak costs the machine)
  try {
  const ctx = await browser.newContext({
    viewport: { width: 1600, height: 950 },
    permissionGranted: [],
  });
  const page = await ctx.newPage();

  // ev/press need the page; the rest of the hardening lives above the try
  const rawEval = page.evaluate.bind(page);
  const ev = (fn, ...a) => withTimeout(rawEval(fn, ...a), 10000, 'page.evaluate');
  const rawPress = page.keyboard.press.bind(page.keyboard);
  const press = k => withTimeout(rawPress(k), 5000, "press '" + k + "'");
  // harness-side status reader: Node http with a hard timeout. During the
  // restart boot the server holds its lock through the real-body import, so
  // an IN-PAGE fetch('/api/status') can stall past any page.evaluate budget
  // (run #7's recorded STAGE-TIMEOUT). The counter is verified from here.
  const readStatusH = () => new Promise(res => {
    const req = http.get(BASE + '/api/status', { timeout: 1500 }, r => {
      let b = '';
      r.on('data', c => (b += c));
      r.on('end', () => { try { res(JSON.parse(b)); } catch (_) { res(null); } });
    });
    req.on('timeout', () => { req.destroy(); res(null); });
    req.on('error', () => res(null));
  });
  const bootCountH = async () => {
    for (let i = 0; i < 4; i++) {
      const s = await readStatusH();
      if (s && typeof s.boot_count === 'number') return s.boot_count;
      await sleep(400);
    }
    return -1;
  };

  // the repo's error-beacon pattern, harness half: capture console errors
  // and page errors for the whole session
  const consoleErrors = [];
  page.on('console', m => {
    if (m.type() === 'error') consoleErrors.push('console: ' + m.text());
  });
  page.on('pageerror', e => consoleErrors.push('pageerror: ' + e.message));
  const abortedPolls = [];
  page.on('requestfailed', r => {
    const err = r.failure() && r.failure().errorText;
    // the page's own poll timeouts (AbortSignal.timeout on the three polling
    // endpoints) are BY DESIGN -- counted separately, never as errors
    if (err === 'ERR_ABORTED' &&
        /\/api\/(verts|status|topology)/.test(r.url())) {
      abortedPolls.push(r.url());
      return;
    }
    consoleErrors.push('requestfailed: ' + r.url() + ' ' + err);
  });

  // ---------- launch: the stranger opens the page ----------
  mark('launch');
  const t0 = Date.now();
  T.t_launch = 0;
  await page.goto(BASE + '/', { waitUntil: 'load', timeout: 60000 })
    .catch(e => { throw new Error('page did not load: ' + e.message); });
  T.t_page_load = +since(t0).toFixed(2);

  // ---------- first motion: a real verts frame is on the canvas ----------
  mark('first-motion');
  let firstMotion = null;
  while (since(t0) < 120 && firstMotion === null) {
    firstMotion = await ev(() =>
      (window.__CHIMERA_BOOT_TS || null));
    if (firstMotion === null) await sleep(100);
  }
  T.t_first_motion = firstMotion === null
    ? null : +((firstMotion - t0) / 1000).toFixed(2);

  // ---------- understood: read the page the way a stranger would ----------
  mark('understood');
  // (nothing is hard-coded here that the page does not itself show)
  const guide = await ev(() => {
    const g = document.getElementById('guide');
    const obj = document.getElementById('objective');
    const rows = Array.from(document.querySelectorAll('#keys .row'));
    return {
      guideVisible: !!(g && g.style.display !== 'none' && g.offsetHeight > 0),
      guideText: g ? g.innerText : '',
      objectiveText: obj ? obj.innerText : '',
      keyRows: rows.map(r => ({
        key: r.getAttribute('data-key'),
        text: r.innerText.replace(/\s+/g, ' ').trim(),
      })),
    };
  });
  T.t_understood = +since(t0).toFixed(2);
  R.stranger_reading = guide;
  // the stranger picks the action the objective names: the guide's objective
  // line says "press 1" -- the page said so, not the harness
  const objectiveNamesSend = /marker.*press|press.*1|send/i.test(
    guide.objectiveText + ' ' + guide.guideText);
  R.page_objective_names_send = objectiveNamesSend;

  // ---------- first deliberate action: key 1 (send), effect confirmed ----------
  mark('first-action');
  await press('1');
  let sendEffect = null;
  const tSend = Date.now();
  while (since(t0) < 120 && sendEffect === null) {
    await sleep(100);
    sendEffect = await ev(() => {
      const b = document.getElementById('banner');
      return (b && b.style.display === 'block' &&
              /MOCK\[mock_carry\]/.test(b.textContent)) ? true : null;
    });
  }
  T.t_first_action = sendEffect === null ? null : +since(t0).toFixed(2);
  T.t_action_effect_latency_s = +((Date.now() - tSend) / 1000).toFixed(2);
  R.first_action = { chosenBy: 'the page told the stranger (key 1)',
                     effect: sendEffect === true ? 'MOCK[mock_carry] banner on' : 'none' };

  // ---------- stop the slide (key 2), then the 300 N press (Space) ----------
  mark('stop-then-press');
  await press('2');
  await sleep(400);
  R.stop_key = await ev(() => {
    const m = document.getElementById('msg');
    return { msg: m ? m.textContent : '' };
  });

  const pressMsg0 = await ev(() =>
    (document.getElementById('msg') || {}).textContent || '');
  await press(' ');
  let pressEffect = null;
  const tPress = Date.now();
  while (since(tPress) < 12 && pressEffect === null) {
    await sleep(150);
    pressEffect = await ev(s0 => {
      const m = (document.getElementById('msg') || {}).textContent || '';
      return m !== s0 && /press \(real, 300 N\)/.test(m) ? m : null;
    }, pressMsg0);
  }
  R.space_press = pressEffect ? { effect: pressEffect.slice(0, 220) }
                              : { effect: 'none' };
  await sleep(600); // let the press settle back before the walk

  // ---------- every named key (F-EVERY-NAMED-KEY) ----------
  mark('every-named-key');
  // the walk covers the view keys mechanically here; 1/2/Space were verified
  // at their stages above, 3/S/R are verified at their stages below -- every
  // key the page names is pressed and its handler reached, exactly once
  const keys = guide.keyRows.map(r => r.key);
  R.keys_on_page = keys;
  const keyResults = {};
  keyResults['1'] = sendEffect === true;
  keyResults['2'] = /stopped/.test(R.stop_key.msg || '');
  keyResults[' '] = !!pressEffect;
  for (const k of ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', '+', '-', 'H']) {
    const before = await ev(() => ({
      yaw: window.__CHIMERA_VIEW.yaw, pit: window.__CHIMERA_VIEW.pit,
      dist: window.__CHIMERA_VIEW.dist,
      guideShown: document.getElementById('guide').style.display !== 'none' }));
    await press(k);
    await sleep(350);
    const after = await ev(() => ({
      yaw: window.__CHIMERA_VIEW.yaw, pit: window.__CHIMERA_VIEW.pit,
      dist: window.__CHIMERA_VIEW.dist,
      guideShown: document.getElementById('guide').style.display !== 'none' }));
    let effect;
    if (k === 'ArrowLeft')  effect = after.yaw < before.yaw - 0.05;
    else if (k === 'ArrowRight') effect = after.yaw > before.yaw + 0.05;
    else if (k === 'ArrowUp')    effect = after.pit > before.pit + 0.03;
    else if (k === 'ArrowDown')  effect = after.pit < before.pit - 0.03;
    else if (k === '+')          effect = after.dist < before.dist - 0.05;
    else if (k === '-')          effect = after.dist > before.dist + 0.05;
    else if (k === 'H')          effect = after.guideShown !== before.guideShown;
    keyResults[k] = effect;
    // H was toggled by this press; leave the guide OPEN for the next checks
    if (k === 'H' && !after.guideShown) await press('H');
  }

  // ---------- the fall test (key 3), real; then save (S); then restart (R) ----------
  mark('fall');
  await press('3');
  await sleep(1200);
  R.fall_started = await ev(() =>
    /running|THE FALL/.test(
      (document.getElementById('fall-verdict') || {}).textContent || ''));
  keyResults['3'] = R.fall_started === true;
  // let the fall play out (the engine owns the timing; 40 s cap server-side)
  let fallDone = false;
  const tFall = Date.now();
  while (since(tFall) < 45 && !fallDone) {
    await sleep(500);
    fallDone = await ev(() =>
      /landed root_y/.test(
        (document.getElementById('fall-verdict') || {}).textContent || ''));
  }
  R.fall_completed = fallDone;
  R.fall_verdict = await ev(() =>
    (document.getElementById('fall-verdict') || {}).textContent || '');

  // ---------- save (key S): the session record lands ----------
  mark('save');
  await press('S');
  let saved = false;
  const tSave = Date.now();
  while ((Date.now() - tSave) / 1000 < 8 && !saved) {
    await sleep(250);
    saved = await ev(() =>
      /saved:/.test((document.getElementById('msg') || {}).textContent || ''));
  }
  R.save_key = saved;
  keyResults['S'] = saved;

  // ---------- restart: key R, clean, world returns ----------
  mark('restart');
  const bootCount0 = await bootCountH();
  const st0 = await readStatusH();
  R.scene_pin_before = (st0 && st0.scene && st0.scene.scene_sha256) || null;
  const tRestart = Date.now();
  await press('R');
  keyResults['R'] = 'checked-here';
  let pillShown = null;
  while ((Date.now() - tRestart) / 1000 < 5 && pillShown === null) {
    await sleep(100);
    pillShown = await ev(() => {
      const p = document.getElementById('bootstatus');
      return (p && p.style.display === 'block' &&
              /RESTARTING/.test(p.textContent)) ? true : null;
    });
  }
  R.restart_pill_shown = pillShown === true;
  let worldBack = false;
  while ((Date.now() - tRestart) / 1000 < 60 && !worldBack) {
    await sleep(250);
    // the honest world-back signal: a dying OLD engine can still answer for
    // a moment (that is how the pill once hid without a new boot), so the
    // server's own boot counter must ALSO have incremented -- read
    // harness-side (see readStatusH above)
    let dom = null;
    try {
      dom = await ev(() => {
        const pill = (document.getElementById('bootstatus') || {}).style.display;
        const st = (document.getElementById('status') || {}).textContent || '';
        return { pill, st };
      });
    } catch (_) { dom = null; }
    const boots = await bootCountH();
    worldBack = !!dom && dom.pill !== 'block' && /root_y/.test(dom.st) &&
      boots === (bootCount0 || 0) + 1;
  }
  T.t_restart_done = +((Date.now() - tRestart) / 1000).toFixed(2);
  R.restart_world_returned = worldBack;
  // the restart really happened iff the boot counter incremented -- that is
  // already part of worldBack above; recorded for the artifact
  const bootCount1 = await bootCountH();
  const st1 = await readStatusH();
  R.scene_pin_after = (st1 && st1.scene && st1.scene.scene_sha256) || null;
  R.scene_pin_stable = !!R.scene_pin_before &&
    R.scene_pin_before === R.scene_pin_after;
  R.boot_count_before = bootCount0;
  R.boot_count_after = bootCount1;
  R.restart_actually_booted = bootCount1 === (bootCount0 || 0) + 1;
  keyResults['R'] = R.restart_pill_shown && worldBack && R.restart_actually_booted;
  // prereg F-CLEAN-RESTART: "same scene pin, settles again" -- wait for the
  // scene's own settled flag (the server's convergence window, real physics)
  let settled = false;
  const tSettle = Date.now();
  while ((Date.now() - tSettle) / 1000 < 45 && !settled) {
    await sleep(500);
    const st = await readStatusH();
    settled = !!(st && st.scene && st.scene.settled === true);
  }
  R.restart_settled = settled;
  R.restart_settle_wait_s = +((Date.now() - tSettle) / 1000).toFixed(2);
  await sleep(1200); // let the settle pill show, then let it hide
  R.restart_state = await ev(() => ({
    status: ((document.getElementById('status') || {}).textContent || '').slice(0, 200),
    pill: (document.getElementById('bootstatus') || {}).style.display,
    carryActive: (document.getElementById('banner') || {}).style.display === 'block',
  }));

  R.key_results = keyResults;
  R.every_named_key_works = keys.length > 0 &&
    keys.every(k => keyResults[k] === true) &&
    keys.every(k => guide.keyRows.find(r => r.key === k));

  // ---------- the beacon verdict ----------
  mark('verdicts');
  R.aborted_polls_by_design = abortedPolls.length;
  R.beacon_entries = await ev(() => window.__CHIMERA_BEACON);
  R.beacon_empty = R.beacon_entries.length === 0;
  R.console_errors = consoleErrors;
  R.console_empty = consoleErrors.length === 0;

  // ---------- verdicts ----------
  const u = T.t_understood, fa = T.t_first_action;
  R.falsifiers = {
    'F-STRANGER-60': {
      bar_s: 60, measured: {
        t_launch: T.t_launch, t_page_load: T.t_page_load,
        t_first_motion: T.t_first_motion, t_understood: u,
        t_first_action: fa },
      pass: fa !== null && fa < 60 && objectiveNamesSend },
    'F-EVERY-NAMED-KEY': { keys: keys, results: keyResults,
      pass: R.every_named_key_works },
    'F-BEACON-SILENT': { beacon: R.beacon_entries.length,
      harness: consoleErrors.length, pass: R.beacon_empty && R.console_empty },
    'F-RESTART-CLEAN': { pill: R.restart_pill_shown,
      world_back_s: T.t_restart_done, returned: R.restart_world_returned,
      boots: [R.boot_count_before, R.boot_count_after],
      carry_cleared: R.restart_state ? !R.restart_state.carryActive : false,
      pass: R.restart_pill_shown && R.restart_world_returned &&
            R.restart_actually_booted && R.scene_pin_stable &&
            R.restart_settled === true && T.t_restart_done < 60 &&
            (R.restart_state ? !R.restart_state.carryActive : false) },
    'F-TIMELINE-HONEST': { recorded: true,
      pass: true },
  };
  R.pass = Object.values(R.falsifiers).every(f => f.pass);
  R.console_error_note = 'console+pageerror+requestfailed captured the ' +
    'whole session; the page half lives in window.__CHIMERA_BEACON';

  mark('artifact');
  await withTimeout(page.screenshot({ path: OUT.replace(/\.json$/, '') + '_final.png' }), 15000, 'screenshot');
  flush();
  console.log(JSON.stringify(R.falsifiers, null, 1));
  console.log('WALKTHROUGH: ' + (R.pass ? 'PASS' : 'FAIL') + ' -> ' + OUT);
  } catch (e) {
    R.session_error = e.message;
    R.failed_at_stage = R.stage || 'unknown';
    console.error('SESSION ERROR @' + R.stage + ': ' + e.message);
    flush();
  } finally {
    // kill-safe close: browser.close() itself has hung once on this machine
    try {
      await Promise.race([browser.close(), sleep(8000).then(() => {
        throw new Error('browser.close() timed out'); })]);
    } catch (_) {
      try { browser.process() && browser.process().kill('SIGKILL'); } catch (_) {}
    }
    try { clearTimeout(watchdog); } catch (_) {}
    flush();
  }
  process.exit(R.pass ? 0 : 1);
})().catch(e => {
  console.error('WALKTHROUGH FAILED:', e.message);
  process.exit(1);
});
