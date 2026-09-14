#!/usr/bin/env node
/* fps_probe.js -- MEASURED (not claimed) browser-side fps for the Chimera game
 * page. Lane R6 companion to bench.py: bench.py measures the ENGINE (ticks/s on
 * GET /tick_state); this measures what a PLAYER'S BROWSER actually renders.
 *
 * How it measures:
 *   1. Playwright launches Chrome (channel 'chrome'), and BEFORE the page loads
 *      addInitScript wraps window.requestAnimationFrame with a counting shim.
 *      Every frame the page schedules through rAF (the game's own render loop,
 *      index.html `frame()`) increments window.__rafFrames exactly once. No
 *      extra rAF loop is injected -- the count is the page's own cadence.
 *   2. The probe clicks #play-btn (enter play), then for each 10 s window:
 *        - reads (frames, ms) across the window via page.evaluate, using the
 *          page's own performance.now() clock;
 *        - animates a pose through the shell API like a player would:
 *          POST /api/pose {joint_index: 15 (knee_L), deg: 25} then deg: 0;
 *        - samples GET /tick_state on the ENGINE from Node (250 ms) so the
 *          report can show ticks/s UNDER BROWSER LOAD, not just idle.
 *   3. Runs the whole thing twice: headless AND headed (a real window -- rAF in
 *      a headed window is what a player gets; occlusion throttling is possible
 *      and is reported, not hidden).
 *
 * Output: JSON on stdout and a copy at .tmp/fps_probe.json. It does NOT touch
 * .tmp/bench_report.md (bench.py owns that file; the R6 VERDICT section that
 * cites both measurements is appended by the agent, after both have run).
 *
 * Usage:
 *      node tools/game_shell/fps_probe.js                 # headless + headed
 *      node tools/game_shell/fps_probe.js --mode headless
 *      node tools/game_shell/fps_probe.js --windows 2
 *      node tools/game_shell/fps_probe.js --game http://127.0.0.1:8241 \
 *                                          --engine http://127.0.0.1:8141
 *                                                        # scratch stack
 *
 * Fleet note (H14, 2026-09-14): this probe is MUTATING -- it animates a
 * pose mid-window, which the fleet rules forbid against the shared live
 * stack. Point --game/--engine at a scratch pair (see
 * docs/evidence/agent_fleet/SHIP/H14_BENCH/PROTOCOL.md) for anything that
 * is not operator-authorized live measurement.
 *
 * Exit code: 0 = at least one mode measured, 1 = nothing measured.
 */

'use strict';

const fs = require('fs');
const http = require('http');
const path = require('path');

/* argv FIRST: --game/--engine must be known before anything dials out. */
const ARGV = process.argv.slice(2);
const flag = (name, dflt) => {
  const i = ARGV.indexOf('--' + name);
  return i >= 0 && ARGV[i + 1] ? ARGV[i + 1] : dflt;
};

const GAME = flag('game', 'http://127.0.0.1:8206');
const ENGINE = flag('engine', 'http://127.0.0.1:8107');

/* Playwright lives where the ship's node_modules are; try the local clone
 * first, then the canonical ship root, so the probe runs from any checkout. */
let chromium;
try {
  ({ chromium } = require('playwright-core'));
} catch (_) {
  ({ chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core')));
}

const WINDOW_MS = 10000;
const KNEE_L = 15;                       // index.html JOINT_INDEX.knee_L
const VIEWPORT = { width: 1600, height: 900 };
const ROOT = path.resolve(__dirname, '..', '..');
const OUT_JSON = path.join(ROOT, '.tmp', 'fps_probe.json');

/* ---------------- tiny stdlib HTTP (no deps) ---------------- */

function httpReq(method, url, body) {
  return new Promise((resolve, reject) => {
    const data = body === undefined ? null : Buffer.from(JSON.stringify(body));
    const req = http.request(url, {
      method,
      headers: data ? { 'Content-Type': 'application/json',
                        'Content-Length': data.length } : {},
      timeout: 15000,
    }, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => resolve({ status: res.statusCode,
                                    body: Buffer.concat(chunks).toString('utf8') }));
    });
    req.on('timeout', () => req.destroy(new Error('timeout after 15s')));
    req.on('error', reject);
    if (data) req.write(data);
    req.end();
  });
}

async function postPose(deg) {
  const r = await httpReq('POST', GAME + '/api/pose',
                          { joint_index: KNEE_L, deg });
  if (r.status !== 200) throw new Error('POST /api/pose deg=' + deg +
                                        ' -> HTTP ' + r.status);
  return r.body;
}

async function getTicks() {
  const r = await httpReq('GET', ENGINE + '/tick_state');
  if (r.status !== 200) throw new Error('GET /tick_state -> HTTP ' + r.status);
  return JSON.parse(r.body).ticks;
}

const sleep = (ms) => new Promise((res) => setTimeout(res, ms));

/* Sample the engine tick counter for durationMs. Returns per-interval ticks/s
 * plus a count of failed polls; an engine restart (counter backwards) is
 * reported as a reset, mirroring bench.py. */
async function sampleTicks(durationMs, gapMs = 250) {
  const rates = [];
  let resets = 0, failed = 0;
  let prev = await getTicks();
  let prevT = Date.now();
  const end = Date.now() + durationMs;
  while (Date.now() < end) {
    await sleep(gapMs);
    try {
      const ticks = await getTicks();
      const now = Date.now();
      const dt = (now - prevT) / 1000;
      const delta = ticks - prev;
      if (dt > 0) {
        if (delta >= 0) rates.push(delta / dt);
        else resets += 1;
      }
      prev = ticks; prevT = now;
    } catch (e) {
      failed += 1;               // keep sampling; the window is still valid
    }
  }
  return { rates, resets, failed };
}

function stats(vals) {
  if (!vals.length) return { mean: NaN, min: NaN, max: NaN, n: 0 };
  const s = [...vals].sort((a, b) => a - b);
  return { mean: s.reduce((a, b) => a + b, 0) / s.length,
           min: s[0], max: s[s.length - 1], n: s.length };
}

/* ---------------- the rAF shim, injected before page scripts ---------------- */

const INIT_SHIM = () => {
  window.__rafFrames = 0;
  if (typeof window.requestAnimationFrame === 'function') {
    const orig = window.requestAnimationFrame.bind(window);
    window.requestAnimationFrame = function (cb) {
      return orig(function (t) {
        window.__rafFrames += 1;
        return cb(t);
      });
    };
  }
};

/* Promise that resolves after `ms` with the frames the page scheduled across
 * the window, measured on the page's own clock. Caller must NOT await it
 * immediately -- the pose animation and tick sampling run in parallel. */
function rafWindow(page, ms) {
  return page.evaluate((dur) => new Promise((res) => {
    const f0 = window.__rafFrames;
    const t0 = performance.now();
    setTimeout(() => {
      res({ frames: window.__rafFrames - f0,
            ms: performance.now() - t0,
            total: window.__rafFrames });
    }, dur);
  }), ms);
}

/* ---------------- one full measurement pass (a launch mode) ---------------- */

async function measureMode(mode, windows) {
  const out = { mode, ok: false, error: null, rafLoopStarted: false,
                enteredPlay: false, windows: [], fps: stats([]),
                ticksUnderLoad: stats([]) };
  let browser;
  try {
    browser = await chromium.launch({ channel: 'chrome', headless: mode === 'headless' });
    const context = await browser.newContext({ viewport: VIEWPORT });
    await context.addInitScript(INIT_SHIM);
    const page = await context.newPage();
    page.on('pageerror', (e) => console.error('[fps_probe] pageerror:',
                                              String(e.message).slice(0, 200)));

    await page.goto(GAME, { waitUntil: 'load', timeout: 30000 });

    // The page only starts its rAF loop when WebGL2 is up (index.html boot).
    try {
      await page.waitForFunction(() => window.__rafFrames > 0,
                                 null, { timeout: 15000 });
      out.rafLoopStarted = true;
    } catch (e) {
      out.error = 'page rAF loop never started (WebGL2 missing or page failed ' +
                  'to boot); __rafFrames never advanced';
      return out;
    }

    await page.click('#play-btn');           // enter play
    out.enteredPlay = true;
    // The E4 first-run intro overlay shows once per name; a player presses
    // Enter through it. Dismiss it if present so the page sits in the same
    // state a mid-session player's does (overlay-open blocks nothing the
    // probe measures -- polls and rAF run regardless -- this is fidelity).
    try {
      const introOpen = await page.evaluate(() =>
        !document.getElementById('intro-overlay').classList.contains('hidden'));
      if (introOpen) await page.keyboard.press('Enter');
    } catch (_) { /* no overlay element: older page, nothing to dismiss */ }
    await sleep(2000);                       // let lessons/verts settle

    for (let w = 0; w < windows; w++) {
      const pending = rafWindow(page, WINDOW_MS);   // NOT awaited yet

      // animate the pose like the mission spec: knee 25, then back to 0
      await sleep(500);
      const poseA = await postPose(25).then(() => 'ok',
                                            (e) => 'ERR: ' + e.message);
      await sleep(4000);
      const poseB = await postPose(0).then(() => 'ok',
                                           (e) => 'ERR: ' + e.message);

      const tickRes = await sampleTicks(WINDOW_MS);
      const win = await pending;
      const fps = win.frames / (win.ms / 1000);
      const ts = stats(tickRes.rates);
      out.windows.push({
        window: w + 1,
        fps: +fps.toFixed(2),
        frames: win.frames,
        ms: +win.ms.toFixed(0),
        knee25: poseA, knee0: poseB,
        ticks_mean: +ts.mean.toFixed(2),
        ticks_min: +ts.min.toFixed(2),
        ticks_n: ts.n,
        tick_resets: tickRes.resets,
        tick_failed_polls: tickRes.failed,
      });
      await sleep(1000);                       // breathe between windows
    }

    out.fps = stats(out.windows.map((w) => w.fps));
    out.ticksUnderLoad = stats(out.windows.map((w) => w.ticks_mean));
    out.ok = out.windows.every((w) => w.frames > 0);
    if (!out.ok) out.error = 'a window counted 0 rAF frames';
    return out;
  } catch (e) {
    out.error = e.message;
    return out;
  } finally {
    if (browser) { try { await browser.close(); } catch (_) {} }
  }
}

/* ---------------- main ---------------- */

async function main() {
  const argv = ARGV;
  const windows = Math.max(1, parseInt(flag('windows', '3'), 10) || 3);
  const modeArg = flag('mode', 'both');
  const modes = modeArg === 'both' ? ['headless', 'headed'] : [modeArg];

  const result = {
    what: 'Chimera game-page browser fps probe (R6, measured)',
    game: GAME,
    engine: ENGINE,
    window_ms: WINDOW_MS,
    windows_per_mode: windows,
    date_utc: new Date().toISOString(),
    pose: 'POST /api/pose {joint_index: 15 (knee_L), deg: 25 then 0} mid-window',
    modes: {},
  };

  let anyOk = false;
  for (const mode of modes) {
    console.error('[fps_probe] measuring mode=' + mode + ' ...');
    const r = await measureMode(mode, windows);
    result.modes[mode] = r;
    anyOk = anyOk || r.ok;
    if (r.ok) {
      console.error('[fps_probe] mode=' + mode +
                    ': fps mean ' + r.fps.mean.toFixed(2) +
                    ', min ' + r.fps.min.toFixed(2) +
                    ' over ' + r.fps.n + ' window(s); engine ticks/s under' +
                    ' browser load: mean ' + r.ticksUnderLoad.mean.toFixed(1));
    } else {
      console.error('[fps_probe] mode=' + mode + ' FAILED: ' + r.error);
    }
  }

  try {
    fs.mkdirSync(path.dirname(OUT_JSON), { recursive: true });
    fs.writeFileSync(OUT_JSON, JSON.stringify(result, null, 1));
    console.error('[fps_probe] json written to ' + OUT_JSON);
  } catch (e) {
    console.error('[fps_probe] could not write json: ' + e.message);
  }
  console.log(JSON.stringify(result, null, 1));
  process.exit(anyOk ? 0 : 1);
}

main().catch((e) => {
  console.error('[fps_probe] FATAL: ' + (e && e.stack || e));
  process.exit(1);
});
