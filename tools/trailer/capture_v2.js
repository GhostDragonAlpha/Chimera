/* capture_v2.js — G10 trailer v2: REAL-TIME capture of the LIVE game page.
   The round-1 trailer was ~1 fps engine grabs, time-remapped; the judges said
   that "leaves responsiveness unproven." This file answers with the real thing:

     - opens http://127.0.0.1:8206 in HEADED Chrome (channel:'chrome');
     - enters the play screen and selects lesson 5 ("THE WHOLE BODY"), whose
       first touch target is the proven belly point [0.0, 4.5, 0.35];
     - drives a GENUINE press through the page's own input rail:
         SPACE  -> the page itself POSTs /api/touch_hit {hit, force_n}
         ESCAPE -> the page itself POSTs /api/touch_clear
       (real key events, the same code path a player's keyboard takes);
     - two real mouse-drag orbits (pointerdown -> pointermove -> pointerup)
       prove the browser renders smooth LOCAL motion at its rAF rate;
     - samples the WebGL canvas (#gl) at ~24 fps from INSIDE the page:
       a rAF callback chained after the page's own frame() calls
       canvas.toDataURL in the same rendering opportunity (so the drawing
       buffer is intact) — every saved frame is a real browser-rendered
       frame, timestamped with performance.now(). The timeline is real wall
       clock: no time-remap, no holds, no crossfades, no interpolation.
   The engine at :8107 is never built, stopped, or configured; the only
   engine traffic is the touch press itself (sanctioned) and its clear.

   Output: <outdir>/frames/frame_00000.jpg ... + <outdir>/timeline.json
   Run: node tools/trailer/capture_v2.js <outdir> [url]
*/
'use strict';
const fs = require('fs');
const path = require('path');
const { chromium } = require('E:/PythonChimera/node_modules/playwright-core');

const OUT = process.argv[2];
const URL_ = process.argv[3] || 'http://127.0.0.1:8206';
if (!OUT) { console.error('usage: node capture_v2.js <outdir> [url]'); process.exit(2); }
fs.mkdirSync(path.join(OUT, 'frames'), { recursive: true });

const NAME = 'g10_v2';                 // fresh visitor; never saved
const GATE_MS = 41;                    // ~24 fps sample gate
const MAX_FRAMES = 1600;
const savedMeta = [];

const sleep = ms => new Promise(r => setTimeout(r, ms));
const log = (...a) => console.log('[capture]', ...a);

(async () => {
  const notes = [];
  const browser = await chromium.launch({
    channel: 'chrome',
    headless: false,                                  // HEADED — a real window
    args: [
      '--window-size=2320,1200',
      '--window-position=20,20',
      '--disable-backgrounding-occluded-windows',
      '--disable-renderer-backgrounding',
      '--disable-background-timer-throttling',
      '--autoplay-policy=no-user-gesture-required',
    ],
  });
  const page = await browser.newPage({
    viewport: { width: 2280, height: 1080 },          // stage = 2280-360 sidebar = 1920x1080
    deviceScaleFactor: 1,
  });
  page.on('pageerror', e => log('PAGE ERROR:', e.message));

  log('opening', URL_);
  await page.goto(URL_, { waitUntil: 'load' });
  await sleep(3000);                                  // world attach (topology + first verts)

  // enter the play screen as a player would
  await page.fill('#name-input', NAME);
  await page.click('#play-btn');
  await sleep(1500);
  try { await page.click('#intro-begin', { timeout: 5000 }); log('intro overlay: begun'); }
  catch { log('intro overlay: not shown'); notes.push('intro overlay not shown'); }
  await sleep(800);

  // sanity: the WebGL canvas must be live at exactly 1920x1080 backing pixels
  const cinfo = await page.evaluate(() => {
    const c = document.getElementById('gl');
    return { w: c.width, h: c.height, cw: c.clientWidth, ch: c.clientHeight };
  });
  log('canvas:', JSON.stringify(cinfo));
  if (cinfo.w !== 1920 || cinfo.h !== 1080)
    notes.push(`canvas is ${cinfo.w}x${cinfo.h}, expected 1920x1080 (encode rescales)`);

  // lesson 5 = index 4 "THE WHOLE BODY": touch_targets[0] is the belly
  await page.keyboard.press('5');
  await sleep(700);
  const lessonTitle = await page.evaluate(
    () => (document.getElementById('lesson-title') || {}).textContent || '?');
  log('lesson:', lessonTitle);

  // force 20000 -> 30000 N via the page's own '=' rail (+2000 per press)
  for (let i = 0; i < 5; i++) { await page.keyboard.press('='); await sleep(120); }
  const forceLabel = await page.evaluate(
    () => (document.getElementById('force-label') || {}).textContent || '?');
  log('force:', forceLabel);

  // wait for a QUIET window before the take. This is a SHARED slot: other
  // fleet agents press the same creature, and gravity may be on (a settled
  // stand holds real pressure, so |P| < 1000 Pa is not the rest signal here).
  // Quiet = no active dent AND no >100 kPa jumps between polls, sustained 4 s.
  const quiet = await waitQuiet(page, 120000);
  log('quiet window before take:', quiet);
  if (!quiet) { notes.push('no quiet window before take (shared slot busy) — ABORT');
    await browser.close(); process.exit(5); }

  // ---- the in-page sampler -----------------------------------------------
  // chained rAF: runs right after the page's frame() within the same
  // rendering opportunity, so canvas.toDataURL sees the freshly drawn buffer.
  await page.evaluate(([gate, maxF]) => {
    window.__g10cap = { on: false, frames: [], last: 0 };
    const canvas = document.getElementById('gl');
    const tick = () => {
      if (!window.__g10cap.on) return;
      const now = performance.now();
      if (now - window.__g10cap.last >= gate) {
        window.__g10cap.last = now;
        let url = null, err = null;
        try { url = canvas.toDataURL('image/jpeg', 0.82); }
        catch (e) { err = String(e && e.message || e); }
        window.__g10cap.frames.push({ t: now, url, err });
        if (window.__g10cap.frames.length >= maxF) { window.__g10cap.on = false; return; }
      }
      requestAnimationFrame(tick);
    };
    window.__g10cap.start = () => {
      window.__g10cap.frames = []; window.__g10cap.last = -1e9;
      window.__g10cap.on = true;
      requestAnimationFrame(tick);
    };
    window.__g10cap.stop = () => { window.__g10cap.on = false; };
  }, [GATE_MS, MAX_FRAMES]);

  // probe: does the dataURL path deliver a real JPEG? (the scene is mostly
  // flat dark background — 1920x1080 legitimately compresses to ~15-20 KB,
  // so the size gate is low; the real blank-check happens in Python via PIL)
  const probe = await page.evaluate(() => {
    const c = document.getElementById('gl');
    try {
      const u = c.toDataURL('image/jpeg', 0.82);
      return { ok: u.length > 8000 && u.startsWith('data:image/jpeg;base64,/9j/'),
               len: u.length, err: null };
    } catch (e) { return { ok: false, len: 0, err: String(e) }; }
  });
  log('dataURL probe:', JSON.stringify(probe));
  if (!probe.ok) {
    await browser.close();
    console.error('[capture] FATAL: canvas.toDataURL did not yield pixels:', probe.err);
    process.exit(4);
  }

  const box = await page.evaluate(() => {
    const r = document.getElementById('gl').getBoundingClientRect();
    return { x: r.left, y: r.top, w: r.width, h: r.height };
  });

  // ---- THE TAKE (every timestamp is the page's own performance.now) -------
  // Camera work is REAL user input on the page's local camera: drags orbit
  // (theta/phi), wheel zooms (cam.r, clamped 3..60) — all pure local math at
  // the page's rAF rate, so captured motion is the browser's own render rate.
  // Drags step at ~55 Hz (> capture rate) so no two consecutive captures see
  // the same camera unless the scene is genuinely still.
  const ph = {};
  ph.sampler_start = await page.evaluate(() => {
    window.__g10cap.start(); return performance.now();
  });

  // 01 REST at the wide shot, then a slow real orbit (establishing sweep that
  // also swings theta to -0.55 -> ~0.0 so the belly faces the camera)
  await sleep(800);
  ph.orbit1_start = await page.evaluate(() => performance.now());
  await drag(page, box, { dx: -110, dy: -40, steps: 130, sleepMs: 14 });
  ph.orbit1_end = await page.evaluate(() => performance.now());
  await sleep(300);

  // 02 ZOOM IN to the belly with real wheel ticks (r 26 -> ~7.5)
  ph.zoom_start = await page.evaluate(() => performance.now());
  await page.mouse.move(box.x + box.w * 0.5, box.y + box.h * 0.55);
  for (let i = 0; i < 20; i++) { await page.mouse.wheel(0, -62); await sleep(100); }
  ph.zoom_end = await page.evaluate(() => performance.now());
  await sleep(500);
  // remember the shared world we are filming (for the honest report)
  const world = await state(page);
  const worldGravity = !!world.gravity_on;
  const baselineP = (world.cells || []).map(c => Math.abs(Number(c.P) || 0));

  // 03 PRESS — the page's own SPACE rail POSTs /api/touch_hit {hit, force_n}
  //    at the lesson's belly target [0.0, 4.5, 0.35]. Verify the page LATCHED
  //    holding (letgo button goes hot); one retry if it did not.
  ph.press_key = await page.evaluate(() => performance.now());
  await page.keyboard.press('Space');
  await sleep(400);
  let latched = await page.evaluate(
    () => document.getElementById('letgo-btn').classList.contains('hot'));
  if (!latched) {
    log('page did not latch holding — one Space retry');
    await page.keyboard.press('Space');
    await sleep(400);
    latched = await page.evaluate(
      () => document.getElementById('letgo-btn').classList.contains('hot'));
  }
  const pressed = latched && (await waitDimpleAbove(page, 0.02, 4000));
  ph.dimple_visible = await page.evaluate(() => performance.now());
  log('press registered (latched + dimple_m > 0.02 m):', pressed,
      'at +', ((ph.dimple_visible - ph.press_key) / 1000).toFixed(2), 's');
  if (!pressed) notes.push('press not verified (latch or dimple missing)');

  // 04 HOLD-AS-A-LIVE-DRAG: one continuous gesture — pointerdown 0.4 s after
  //    the press, slow orbit around the dent for ~4 s, pointerup. The page
  //    releases the press exactly on that pointerup (endPress -> clearTouch),
  //    so the hold shows MOTION (real-time camera work around the held dent)
  //    and the release is a genuine player gesture, not a synthetic key.
  await sleep(400);
  const holdDimple = await readDimple(page);          // the dent, on camera, held
  ph.hold_drag_start = await page.evaluate(() => performance.now());
  await drag(page, box, { dx: 70, dy: 10, steps: 200, sleepMs: 14 });
  ph.release_key = await page.evaluate(() => performance.now());   // pointerup = release

  // 05 HEAL — tau = 0.5 s decay, streamed at the page's 3 Hz mesh rate.
  //    The pointerup above releases the press when the page was holding; if
  //    holding had somehow been lost, that same pointerup fires tryTouch —
  //    a stray press. One ESCAPE covers both branches: clearTouch releases
  //    the real press (or no-ops) / clears the stray one (it sets holding).
  await sleep(300);
  await page.keyboard.press('Escape');
  const healed = await waitDimpleBelow(page, 0.02, 10000);
  ph.healed = await page.evaluate(() => performance.now());
  log('healed (dimple_m < 0.02 m):', healed,
      'at +', ((ph.healed - ph.release_key) / 1000).toFixed(2), 's after release');
  if (!healed) notes.push('dimple did not return under 0.02 m within 10 s of release');
  await sleep(Math.max(0, 2600 - (ph.healed - ph.release_key)));

  // 06 TAIL — a slow orbit back at the close shot, then stop
  ph.orbit2_start = await page.evaluate(() => performance.now());
  await drag(page, box, { dx: -70, dy: 0, steps: 80, sleepMs: 14 });
  ph.orbit2_end = await page.evaluate(() => performance.now());
  await sleep(400);

  ph.sampler_stop = await page.evaluate(() => {
    window.__g10cap.stop(); return performance.now();
  });

  // ---- pull the frames out of the page ------------------------------------
  const framesDir = path.join(OUT, 'frames');
  let n = 0, errs = 0;
  for (let guard = 0; guard < 400; guard++) {
    const chunk = await page.evaluate(() => window.__g10cap.frames.splice(0, 40));
    if (!chunk.length) break;
    for (const f of chunk) {
      if (f.err || !f.url || f.url.length < 5000) { errs++; continue; }
      const b64 = f.url.slice(f.url.indexOf(',') + 1);
      fs.writeFileSync(path.join(framesDir, `frame_${String(n).padStart(5, '0')}.jpg`),
                       Buffer.from(b64, 'base64'));
      f.i = n; delete f.url;
      savedMeta.push(f);
      n++;
    }
  }

  const t0 = savedMeta.length ? savedMeta[0].t : 0;
  const lastT = savedMeta.length ? savedMeta[savedMeta.length - 1].t : 0;
  const timeline = {
    method: 'real-time browser capture: page-rAF-chained canvas.toDataURL, '
          + '~24 fps gate, wall-clock timestamps; no time-remap, no interpolation',
    url: URL_, headed: true, channel: 'chrome',
    viewport: '2280x1080', deviceScaleFactor: 1,
    canvas: cinfo, lesson: lessonTitle, force: forceLabel,
    player_name: NAME, pressed, healed, latched,
    hold_dimple_m: holdDimple, quiet_before_take: quiet,
    world_gravity_on: worldGravity, world_baseline_pa: baselineP,
    gate_ms: GATE_MS, dataurl_probe: probe, todataurl_errors: errs,
    t0_page_ms: t0,
    phases_wall_ms: ph,
    phases_s: Object.fromEntries(Object.entries(ph).map(([k, v]) => [k, +(((v - t0) / 1000).toFixed(4))])),
    captured_at: new Date().toISOString(),
    frames: savedMeta.map(f => ({ i: f.i, t_s: +(((f.t - t0) / 1000).toFixed(4)) })),
    notes,
  };
  fs.writeFileSync(path.join(OUT, 'timeline.json'), JSON.stringify(timeline, null, 1));
  log(`saved ${n} frames (${errs} sampler errors) -> ${framesDir}`);
  log('timeline.json written; wall footage ' + ((lastT - t0) / 1000).toFixed(2) + ' s');

  await browser.close();
  process.exit(n >= 240 ? 0 : 3);
})().catch(e => { console.error('[capture] FAILED:', e); process.exit(1); });

// ------------------------------------------------------------------ helpers
async function state(page) {
  return page.evaluate(() => fetch('/api/state').then(r => r.json()));
}
async function readDimple(page) {
  try { return Number((await state(page)).dimple_m || 0); } catch { return null; }
}
async function waitCalm(page, capMs) {
  // kept for compatibility; the take gate is waitQuiet (below)
  return waitQuiet(page, capMs);
}
/* Quiet window: dimple under 0.02 m AND no >100 kPa jump in any cell between
   consecutive polls, sustained for 4 s. Under gravity (shared slot) a settled
   stand holds real pressure, so an absolute |P| threshold never fires. */
async function waitQuiet(page, capMs) {
  const t0 = Date.now();
  let lastP = null, quietSince = null;
  while (Date.now() - t0 < capMs) {
    try {
      const s = await state(page);
      const d = Number(s.dimple_m || 0);
      const ps = (s.cells || []).map(c => Math.abs(Number(c.P) || 0));
      let spikes = false;
      if (lastP && lastP.length === ps.length)
        for (let i = 0; i < ps.length; i++)
          if (Math.abs(ps[i] - lastP[i]) > 100000) spikes = true;   // someone pressing
      lastP = ps;
      if (d < 0.02 && !spikes) {
        if (!quietSince) quietSince = Date.now();
        else if (Date.now() - quietSince >= 4000) return true;
      } else quietSince = null;
    } catch { /* a silent beat is not a verdict */ }
    await sleep(400);
  }
  return false;
}
async function waitDimpleAbove(page, min, capMs) {
  const t0 = Date.now();
  while (Date.now() - t0 < capMs) {
    if ((await readDimple(page)) > min) return true;
    await sleep(150);
  }
  return false;
}
async function waitDimpleBelow(page, max, capMs) {
  const t0 = Date.now();
  while (Date.now() - t0 < capMs) {
    const d = await readDimple(page);
    if (d !== null && d < max) return true;
    await sleep(150);
  }
  return false;
}

/* A real drag: pointerdown, many small pointermoves (an orbit gesture —
   past 6 px the page orbits and never touches), pointerup. Steps sleep
   `sleepMs` between moves; with CDP overhead this lands ~50-60 Hz, above
   the capture rate, so consecutive captures never see a repeated camera. */
async function drag(page, box, { dx, dy, steps, sleepMs }) {
  const x0 = box.x + box.w * 0.5 - dx / 2, y0 = box.y + box.h * 0.55 - dy / 2;
  await page.mouse.move(x0, y0);
  await page.mouse.down();
  for (let i = 1; i <= steps; i++) {
    await page.mouse.move(x0 + dx * i / steps, y0 + dy * i / steps);
    await sleep(sleepMs);
  }
  await page.mouse.up();
}
