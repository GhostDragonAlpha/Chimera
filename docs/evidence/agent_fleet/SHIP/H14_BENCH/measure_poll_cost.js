#!/usr/bin/env node
/* measure_poll_cost.js -- H14: the PAGE POLL COST, measured (not claimed).
 *
 * Question (mission C3 feed): what does ONE open game page cost the engine,
 * in engine ticks and in bytes on the wire, and what is the current baseline
 * bytes/min per player that C3's delta-compression (>10x byte drop) must
 * beat?
 *
 * What it measures, in phases, all against a SCRATCH stack it boots itself:
 *   phase A "no_page"   -- engine alone: /tick_state sampled at 100 ms.
 *   phase B "page_idle" -- one headless Chrome player on the shell, PLAY
 *                          clicked, hands off: page polls /api/verts?delta=1
 *                          at 3 Hz + /api/state at ~1.4 Hz; engine sampled.
 *   phase C "page_active"-- same page, plus a scripted knee pose oscillation
 *                          (the shell's /api/pose, what a player's sliders
 *                          do) so the delta stream has changes to carry.
 *
 * Per-poll bytes come from the PAGE's own PerformanceResourceTiming
 * (transferSize) -- the page is the one delta client and its resource
 * entries are the honest wire view; parallel pulls from outside would steal
 * the delta chain (seq gaps -> resync keyframes -> fake bytes).
 *
 * Fleet safety: this script NEVER dials the live stack. The engine and the
 * shell it uses are its own children on private ports (8141/8241), in an
 * isolated cwd, killed (BY PID) on exit. The pose posts go to the scratch
 * shell only.
 *
 * Usage:
 *   node measure_poll_cost.js --engine-exe <chimera_engine.exe> [--out json]
 * Defaults assume the repo layout: ../../../../../../tools/game_shell for the
 * shell, .tmp/build_tick/Release for the exe (pass --engine-exe explicitly).
 * Exit 0 = all three phases measured, 1 = something failed.
 */

'use strict';

const { spawn, execSync } = require('child_process');
const fs = require('fs');
const http = require('http');
const path = require('path');

const ARGV = process.argv.slice(2);
const flag = (name, dflt) => {
  const i = ARGV.indexOf('--' + name);
  return i >= 0 && ARGV[i + 1] ? ARGV[i + 1] : dflt;
};

const REPO = path.resolve(__dirname, '..', '..', '..', '..', '..');
const SHELL_DIR = path.join(REPO, 'tools', 'game_shell');
const ENGINE_EXE = flag('engine-exe',
  path.join(REPO, '.tmp', 'build_tick', 'Release', 'chimera_engine.exe'));
const ENGINE_PORT = parseInt(flag('engine-port', '8141'), 10);
const SHELL_PORT = parseInt(flag('shell-port', '8241'), 10);
const PHASE_S = parseInt(flag('seconds', '45'), 10);
const SETTLE_S = parseInt(flag('settle-s', '30'), 10);
const ENGINE = 'http://127.0.0.1:' + ENGINE_PORT;
const GAME = 'http://127.0.0.1:' + SHELL_PORT;
const OUT = flag('out', path.join(__dirname, 'poll_cost_raw.json'));
const KNEE_L = 15;

let chromium;
try { ({ chromium } = require('playwright-core')); }
catch (_) { ({ chromium } = require('E:/PythonChimera/node_modules/playwright-core')); }

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

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
                                    body: Buffer.concat(chunks) }));
    });
    req.on('timeout', () => req.destroy(new Error('timeout')));
    req.on('error', reject);
    if (data) req.write(data);
    req.end();
  });
}

async function getTicks() {
  const r = await httpReq('GET', ENGINE + '/tick_state');
  if (r.status !== 200) throw new Error('tick_state HTTP ' + r.status);
  return JSON.parse(r.body.toString('utf8')).ticks;
}

/* G8 method: sample (t, ticks) on a fixed cadence; the TRUE rate is
 * (last.ticks - first.ticks) / wall -- immune to poll timing noise. */
async function sampleTicks(seconds, gapMs = 100) {
  const samples = [];
  const end = Date.now() + seconds * 1000;
  while (Date.now() < end) {
    try {
      samples.push({ t: Date.now(), ticks: await getTicks() });
    } catch (_) { /* keep the window honest; count nothing */ }
    await sleep(gapMs);
  }
  if (samples.length < 2) return null;
  const wallMin = (samples[samples.length - 1].t - samples[0].t) / 60000;
  const gained = samples[samples.length - 1].ticks - samples[0].ticks;
  return { ticks_per_min: gained / wallMin, wall_s: wallMin * 60,
           gained, polls: samples.length };
}

function stat(vals) { // (kept for ad-hoc console use)
  if (!vals.length) return { n: 0 };
  const s = [...vals].sort((a, b) => a - b);
  return { n: s.length, mean: s.reduce((a, b) => a + b, 0) / s.length,
           min: s[0], p50: s[Math.floor(s.length / 2)], max: s[s.length - 1] };
}
void stat;

/* ---------------- scratch stack: engine + shell, isolated, by PID -------- */

function freePort(port) {
  try {
    const out = execSync('netstat -ano', { encoding: 'utf8' });
    return !out.split('\n').some((l) => l.includes(':' + port + ' ') &&
                                       l.includes('LISTENING'));
  } catch (_) { return true; }
}

async function bootEngine() {
  if (!fs.existsSync(ENGINE_EXE)) throw new Error('engine exe missing: ' + ENGINE_EXE);
  if (!freePort(ENGINE_PORT)) throw new Error('engine port ' + ENGINE_PORT +
                                              ' busy -- refusing (is live on it?)');
  const runDir = path.join(REPO, '.tmp', 'h14_poll_cost_run');
  fs.mkdirSync(runDir, { recursive: true });
  const exeDir = path.dirname(ENGINE_EXE);
  for (const name of ['shaders', 'session_snapshot']) {
    const src = path.join(exeDir, name), dst = path.join(runDir, name);
    if (fs.existsSync(src) && !fs.existsSync(dst)) {
      execSync('xcopy /E /I /Q /Y "' + src + '" "' + dst + '"');
    }
  }
  const log = fs.openSync(path.join(runDir, 'engine.log'), 'a');
  const proc = spawn(ENGINE_EXE, [String(ENGINE_PORT), '--hidden'],
                     { cwd: runDir, stdio: ['ignore', log, log],
                       detached: false });
  for (let i = 0; i < 120; i++) {
    if (proc.exitCode !== null) break;   // died at boot
    try { await getTicks(); return { proc, runDir }; }
    catch (_) { await sleep(500); }
  }
  try { execSync('taskkill /F /T /PID ' + proc.pid); } catch (_) {}
  throw new Error('scratch engine never answered on ' + ENGINE_PORT);
}

function bootShell() {
  const code = "import sys; sys.path.insert(0, r'" + SHELL_DIR + "'); " +
    "import server; server.Handler.engine_url = '" + ENGINE + "'; server.main()";
  const proc = spawn('python', ['-c', code, String(SHELL_PORT)],
                     { cwd: SHELL_DIR, stdio: 'ignore' });
  return { proc };
}

async function killTree(proc, label) {
  if (!proc || proc.exitCode !== null) return;
  try { execSync('taskkill /F /T /PID ' + proc.pid); }
  catch (e) { console.error('[poll_cost] kill ' + label + ': ' + e.message); }
}

/* ---------------- the player page ---------------- */

/* Harvest the page's own resource timings for the poll streams (append-only;
 * harvesting after each phase lets the numbers be split idle vs active by
 * simple subtraction). */
const harvestEntries = (page) => page.evaluate((gameBase) =>
  performance.getEntriesByType('resource')
    .filter((e) => e.name.includes('/api/verts') ||
                   e.name.includes('/api/state'))
    .map((e) => ({ url: e.name.split('?')[0].replace(gameBase, ''),
                   delta: e.name.includes('delta=1'),
                   transfer: e.transferSize,
                   decoded: e.decodedBodySize,
                   start: e.startTime, dur: e.duration })), GAME);

function tally(entries) {
  const verts = entries.filter((e) => e.url.includes('/api/verts'));
  const states = entries.filter((e) => e.url.includes('/api/state'));
  const steady = verts.filter((v) => v.transfer <= 100000); // post-keyframe
  return {
    verts: { count: verts.length,
             bytes: verts.reduce((a, v) => a + v.transfer, 0),
             keyframes: verts.filter((v) => v.transfer > 100000).length,
             steady: { n: steady.length,
                       mean: steady.length ? +(steady.reduce((a, v) => a + v.transfer, 0) / steady.length).toFixed(1) : 0,
                       p50: steady.length ? steady.map((v) => v.transfer).sort((a, b) => a - b)[Math.floor(steady.length / 2)] : 0,
                       max: steady.length ? Math.max(...steady.map((v) => v.transfer)) : 0 } },
    state: { count: states.length,
             bytes: states.reduce((a, s) => a + s.transfer, 0) },
  };
}

async function run() {
  const result = { what: 'H14 page poll cost (measured)',
    date_utc: new Date().toISOString(),
    engine: ENGINE, game: GAME, phase_s: PHASE_S,
    engine_exe: ENGINE_EXE, phases: {}, poll_bytes: {}, notes: [] };
  let engine = null, shell = null, browser = null;
  try {
    console.error('[poll_cost] booting scratch engine on ' + ENGINE_PORT + ' ...');
    engine = await bootEngine();
    console.error('[poll_cost] booting scratch shell on ' + SHELL_PORT +
                  ' (proxies to ' + ENGINE + ') ...');
    shell = bootShell();
    await sleep(1500);

    console.error('[poll_cost] settle ' + SETTLE_S + 's (boot transient: the ' +
                  'first run measured a cold engine at 271 t/s and a warmed ' +
                  'one at 299 -- the settle kills that confound) ...');
    await sleep(SETTLE_S * 1000);

    console.error('[poll_cost] phase A: engine alone, ' + PHASE_S + 's ...');
    result.phases.no_page = await sampleTicks(PHASE_S);

    browser = await chromium.launch({ channel: 'chrome', headless: true });
    const context = await browser.newContext(
      { viewport: { width: 1600, height: 900 } });
    await context.addInitScript(() => {
      performance.setResourceTimingBufferSize(20000);
    });
    const page = await context.newPage();
    page.on('pageerror', (e) => console.error('[poll_cost] pageerror:',
                                              String(e.message).slice(0, 150)));
    await page.goto(GAME, { waitUntil: 'load', timeout: 30000 });
    await sleep(1500);   // the boot intervals (pollVerts/pollState) attach on load
    await page.click('#play-btn');
    try {
      const introOpen = await page.evaluate(() =>
        !document.getElementById('intro-overlay').classList.contains('hidden'));
      if (introOpen) await page.keyboard.press('Enter');
    } catch (_) {}
    await sleep(2000);   // topology + first keyframe land; steady polling

    console.error('[poll_cost] phase B: page open, idle, ' + PHASE_S + 's ...');
    result.phases.page_idle = await sampleTicks(PHASE_S);
    const afterIdle = tally(await harvestEntries(page));

    console.error('[poll_cost] phase C: page open, knee pose oscillating, ' +
                  PHASE_S + 's ...');
    const t0c = Date.now();
    const poseLoop = (async () => {
      for (let deg = 25, i = 0; ; i++, deg = deg === 25 ? 0 : 25) {
        try {
          const r = await httpReq('POST', GAME + '/api/pose',
                                  { joint_index: KNEE_L, deg });
          if (r.status !== 200) throw new Error('pose HTTP ' + r.status);
        } catch (e) { result.notes.push('pose error: ' + e.message); }
        await sleep(2000);
        if (Date.now() - t0c > (PHASE_S - 1) * 1000) break;
      }
    })();
    result.phases.page_active = await sampleTicks(PHASE_S);
    await poseLoop.catch(() => {});
    const afterActive = tally(await harvestEntries(page));

    // Per-phase byte rates: append-only entries, so active = total - idle.
    const idleVerts = afterIdle.verts, actVerts = afterActive.verts;
    const idleState = afterIdle.state, actState = afterActive.state;
    result.poll_bytes = {
      idle_player_bytes_per_min: {
        verts: +(idleVerts.bytes / (PHASE_S / 60)).toFixed(1),
        state: +(idleState.bytes / (PHASE_S / 60)).toFixed(1),
        total: +((idleVerts.bytes + idleState.bytes) / (PHASE_S / 60)).toFixed(1),
        verts_pulls: idleVerts.count,
        steady_state_p50_bytes: idleVerts.steady.p50,
        window_s: PHASE_S,
      },
      active_player_bytes_per_min: {
        verts: +((actVerts.bytes - idleVerts.bytes) / (PHASE_S / 60)).toFixed(1),
        state: +((actState.bytes - idleState.bytes) / (PHASE_S / 60)).toFixed(1),
        total: +(((actVerts.bytes - idleVerts.bytes) +
                  (actState.bytes - idleState.bytes)) / (PHASE_S / 60)).toFixed(1),
        verts_pulls: actVerts.count - idleVerts.count,
        keyframe_pulls: actVerts.keyframes - idleVerts.keyframes,
        steady_state_mean_bytes: actVerts.steady.mean,
        steady_state_max_bytes: actVerts.steady.max,
        window_s: PHASE_S,
        pose: 'knee_L oscillated 25<->0 deg every 2 s (the shell /api/pose)',
      },
      verts_steady_state_overall: actVerts.steady,
      state_bytes: { min: 0, note: 'see per-phase rates; state polls are ' +
                    '1.4 Hz and near-constant size' },
    };

    // The page is closed before the phases below, so the delta chain is
    // never contended while bytes are being measured.
    await browser.close();
    browser = null;

    console.error('[poll_cost] phase D: page closed again, ' + PHASE_S + 's ...');
    result.phases.no_page_again = await sampleTicks(PHASE_S);

    // The C3 comparison bar needs the full-frame size on the same engine.
    const full = await httpReq('GET', ENGINE + '/verts');
    result.poll_bytes.full_frame_bytes = full.body.length;
    const oneDelta = await httpReq('GET', ENGINE + '/verts?delta=1');
    result.poll_bytes.direct_delta_pull_1 = {
      bytes: oneDelta.body.length,
      kernel_flags: oneDelta.body.length >= 2 ? oneDelta.body[1] : null,
      note: 'flags 0 = keyframe (full), flags 1 = runs (delta)',
    };
    await sleep(3000);   // let the world go fully idle, then ask again
    const twoDelta = await httpReq('GET', ENGINE + '/verts?delta=1');
    result.poll_bytes.direct_delta_pull_2_after_3s_idle = {
      bytes: twoDelta.body.length,
      kernel_flags: twoDelta.body.length >= 2 ? twoDelta.body[1] : null,
    };
    result.poll_bytes.full_vs_steady_delta_ratio =
      +(full.body.length / Math.max(1, result.poll_bytes.idle_player_bytes_per_min.steady_state_p50_bytes)).toFixed(1);
    result.notes.push('direct pulls happen AFTER the page closed; the first ' +
                      'may still carry settle/pose residue, the second is ' +
                      'the honest idle-world delta answer');

    const okA = result.phases.no_page && result.phases.page_idle &&
                result.phases.page_active && result.phases.no_page_again;
    console.log(JSON.stringify(result, null, 1));
    fs.mkdirSync(path.dirname(OUT), { recursive: true });
    fs.writeFileSync(OUT, JSON.stringify(result, null, 1));
    console.error('[poll_cost] json written to ' + OUT);
    return okA ? 0 : 1;
  } catch (e) {
    result.fatal = e.message;
    console.error('[poll_cost] FATAL: ' + e.message);
    try { fs.writeFileSync(OUT, JSON.stringify(result, null, 1)); } catch (_) {}
    return 1;
  } finally {
    if (browser) { try { await browser.close(); } catch (_) {} }
    await killTree(shell && shell.proc, 'shell');
    await killTree(engine && engine.proc, 'engine');
  }
}

run().then((rc) => process.exit(rc)).catch((e) => {
  console.error(e && e.stack || e);
  process.exit(1);
});
