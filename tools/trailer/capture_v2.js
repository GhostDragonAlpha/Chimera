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

  // wait for the creature to be calm BEFORE the take (leftover decay would
  // make "rest" a lie). All |P| < 1000 Pa, or note it and proceed honestly.
  const calm = await waitCalm(page, 20000);
  log('calm before take:', calm);
  if (!calm) notes.push('engine not fully calm at take start (see report)');

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
  const ph = {};
  ph.sampler_start = await page.evaluate(() => {
    window.__g10cap.start(); return performance.now();
  });

  // 01 REST + slow real orbit (proves smooth local rendering at rAF rate)
  await sleep(800);
  ph.orbit1_start = await page.evaluate(() => performance.now());
  await drag(page, box, { dx: 140, dy: 0, steps: 70, ms: 3200 });
  ph.orbit1_end = await page.evaluate(() => performance.now());
  await sleep(600);

  // 02 PRESS — the page's own SPACE rail POSTs /api/touch_hit {hit, force_n}
  ph.press_key = await page.evaluate(() => performance.now());
  await page.keyboard.press('Space');
  const pressed = await waitDimpleAbove(page, 0.02, 4000);
  ph.dimple_visible = await page.evaluate(() => performance.now());
  log('press registered (dimple_m > 0.02 m):', pressed,
      'at +', ((ph.dimple_visible - ph.press_key) / 1000).toFixed(2), 's');
  if (!pressed) notes.push('dimple did not cross 0.02 m within 4 s of SPACE');

  // 03 HOLD — force stays on; the dent breathes with the idle animation
  await sleep(4000);
  const holdDimple = await readDimple(page);
  ph.release_key = await page.evaluate(() => performance.now());

  // 04 RELEASE — ESCAPE -> the page POSTs /api/touch_clear; tau = 0.5 s healing
  await page.keyboard.press('Escape');
  const healed = await waitDimpleBelow(page, 0.01, 8000);
  ph.healed = await page.evaluate(() => performance.now());
  log('healed (dimple_m < 0.01 m):', healed,
      'at +', ((ph.healed - ph.release_key) / 1000).toFixed(2), 's after ESCAPE');
  if (!healed) notes.push('dimple did not fall below 0.01 m within 8 s of ESCAPE');

  // 05 TAIL — a slow orbit back: smooth local motion over the settled body
  await sleep(400);
  ph.orbit2_start = await page.evaluate(() => performance.now());
  await drag(page, box, { dx: -110, dy: 0, steps: 55, ms: 2200 });
  ph.orbit2_end = await page.evaluate(() => performance.now());
  await sleep(800);

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
    player_name: NAME, pressed, healed,
    hold_dimple_m: holdDimple, calm_before_take: calm,
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
  const t0 = Date.now();
  while (Date.now() - t0 < capMs) {
    try {
      const s = await state(page);
      const ps = (s.cells || []).map(c => Math.abs(Number(c.P) || 0));
      if (ps.length && ps.every(p => p < 1000)) return true;
    } catch { /* a silent beat is not a verdict */ }
    await sleep(300);
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
   past 6 px the page orbits and never touches), pointerup. */
async function drag(page, box, { dx, dy, steps, ms }) {
  const x0 = box.x + box.w * 0.5, y0 = box.y + box.h * 0.55;
  await page.mouse.move(x0, y0);
  await page.mouse.down();
  const per = ms / steps;
  for (let i = 1; i <= steps; i++) {
    await page.mouse.move(x0 + dx * i / steps, y0 + dy * i / steps);
    await sleep(per);
  }
  await page.mouse.up();
}
