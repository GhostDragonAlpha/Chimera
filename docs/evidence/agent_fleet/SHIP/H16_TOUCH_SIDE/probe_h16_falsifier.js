/* probe_h16_falsifier.js -- H16 "touch-side" falsifier (named before the run).
   THE OPERATOR'S DEFECT: "When I click on the body the indentation happens
   on the far side." THE OLD PAGE PATH: on press the page posts its orbit
   camera + click pixel to /tick_touch (index.html tryTouch); the engine's
   pick_cam (engine.cpp ~6734) rebuilds the eye with a Z-sign flip vs the
   page's camEye (index.html ~899), so the engine's ray casts from BEHIND
   the body and the press lands where the player CANNOT see.
   THE NEW PATH (the fix under test): the page picks the click with its
   OWN ray-cast (pickWorld over the same RG.verts buffer the renderer
   draws) and posts the ready world point {"hit":[x,y,z],force_n} -- the
   engine presses exactly where the player SEES the cursor.

   DESIGN CONSTRAINT: the page is an IIFE -- no internals are reachable
   from the probe. The mesh math runs NODE-SIDE on the PUBLIC streams
   (GET /api/verts, GET /api/topology through the page server) with the
   page's camera math replicated here. The page camera stays at its
   authored default (r=26, theta=-0.55, phi=0.42, target=[0,4.5,0]) and is
   only moved by a REAL pointer drag on the canvas (the page's own orbit
   handler; exact because one move event gives theta -= dx*0.005).
   Presses are REAL mouse presses. Touch traffic (request + response) is
   captured by patching window.fetch IN THE PAGE.

   THE MARK AUTHORITY: the PAGE's own resolved press point. The probe's
   replicated ray-cast is only good enough to AIM the cursor (measured: a
   replicated pick through the body-center pixel landed 0.84 m off-mesh
   near a protruding feature while the page's own pick sat exactly on the
   streamed mesh -- nearest-vertex distance 0.0000 for every page pick).
   So: pressPoint := request.hit (after) or response.hit (before), and it
   is checked against the engine mesh directly.

   SIDING INVARIANT (the falsifier, both phases):
     pressVisible -- cast a ray from the page eye to pressPoint over the
       streamed mesh: 'seen'  = unobstructed (the player SEES the press
                                point; it faces the camera),
                    'blind' = occluded by the body (the far side),
                    'air'   = off the body entirely.
     localDent   -- max shift-corrected displacement of mesh vertices
                    within 0.15 m of pressPoint (the dent happened AT the
                    clicked spot, not global swing; a 20 kN press kicks the
                    whole body, so displacement is measured relative to the
                    body's own centroid shift).
     VERDICT NEAR iff pressVisible=='seen' AND localDent > 0.002 m AND
                |pressPoint - seed| < regionR (the aimed region)
              (the indentation happens AT the clicked, SEEN spot; the
               control's noise floor is 0.000-0.0006 m. The aim clause
               catches the old path's wrong-limb presses: measured live,
               a click on the +x foot landed on the -x foot, 1.47 m away
               -- visible by luck, still not where the player aimed).
   BEFORE-phase expectation: the operator's repro (all DEFAULT-orbit rows)
   is FAR -- the cam+pixel press lands blind or in the air (the opposite-
   orbit row is reported but not required: the z-flip is view-dependent,
   and for center-pixel clicks from a mirrored eye it can accidentally
   land near the seen point -- exactly why convention coupling is fragile).
   AFTER-phase expectation: EVERY press row NEAR -- 7/7, request is the
   {"hit":...} form, and every pressPoint sits exactly ON the streamed
   mesh (nearest-vertex distance ~0), proving the page picked from the
   LIVE buffer.
   CYCLES: control (no press, noise floor), 5x torso from the default view
   (the operator's repro, 20000 N at the body's screen-center pixel), 1x
   torso from the OPPOSITE orbit (theta + pi via a real drag), 1x foot
   (2000 N -- the gentle-hand's organ; never 20 kN on a limb).
   Evidence: GET /frame from the ENGINE's default camera during one held
   press per phase (read-only, named by the falsifier brief) + page
   screenshots. All mutating traffic rides the page server (8206).
   Run: node probe_h16_falsifier.js before|after [baseURL] */
const path = require('path');
const fs = require('fs');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));

const PHASE = (process.argv[2] || 'before').toLowerCase();
const BASE = process.argv[3] || 'http://127.0.0.1:8206';
const URL_ = BASE + '/?debug=1';
const OUT = path.join(__dirname, 'falsifier_' + PHASE + '.json');
const NAME = 'h16fals_' + PHASE;
const sleep = ms => new Promise(r => setTimeout(r, ms));

/* ---- vector math (mirrors index.html's pick helpers) ---- */
const UP = [0, 1, 0];
const sub3 = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const add3 = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const mul3 = (a, s) => [a[0] * s, a[1] * s, a[2] * s];
const dot3 = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross3 = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm3 = a => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
const len3 = a => Math.hypot(a[0], a[1], a[2]);
/* the page's camEye, exactly (index.html ~899) */
function eyeOf(cam) {
  const ch = Math.cos(cam.phi);
  return [cam.target[0] + cam.r * ch * Math.sin(cam.theta),
          cam.target[1] + cam.r * Math.sin(cam.phi),
          cam.target[2] + cam.r * ch * Math.cos(cam.theta)];
}
/* Moeller-Trumbore, exactly the page's rayTri (~1587); P = flat verts, 9-stride */
function rayTri(ox, oy, oz, dx, dy, dz, P, b0, b1, b2) {
  const ax = P[b0], ay = P[b0 + 1], az = P[b0 + 2];
  const e1x = P[b1] - ax, e1y = P[b1 + 1] - ay, e1z = P[b1 + 2] - az;
  const e2x = P[b2] - ax, e2y = P[b2 + 1] - ay, e2z = P[b2 + 2] - az;
  const px = dy * e2z - dz * e2y, py = dz * e2x - dx * e2z, pz = dx * e2y - dy * e2x;
  const det = e1x * px + e1y * py + e1z * pz;
  if (det > -1e-8 && det < 1e-8) return -1;
  const inv = 1 / det;
  const sx = ox - ax, sy = oy - ay, sz = oz - az;
  const u = (sx * px + sy * py + sz * pz) * inv;
  if (u < 0 || u > 1) return -1;
  const qx = sy * e1z - sz * e1y, qy = sz * e1x - sx * e1z, qz = sx * e1y - sy * e1x;
  const v = (dx * qx + dy * qy + dz * qz) * inv;
  if (v < 0 || u + v > 1) return -1;
  const t = (e2x * qx + e2y * qy + e2z * qz) * inv;
  return t > 1e-6 ? t : -1;
}
/* first hit along a ray against the full streamed mesh (the page's
   pickWorld inner loop, node-side) */
function pickFirst(P, idx, o, d) {
  let best = -1;
  for (let i = 0; i < idx.length; i += 3) {
    const t = rayTri(o[0], o[1], o[2], d[0], d[1], d[2],
      P, idx[i] * 9, idx[i + 1] * 9, idx[i + 2] * 9);
    if (t > 0 && (best < 0 || t < best)) best = t;
  }
  return best < 0 ? null : { t: best, p: add3(o, mul3(d, best)) };
}
/* project a world point through the page's orbit camera to a CSS pixel
   (the exact inverse basis of pickWorld) -- used only to AIM the cursor */
function project(P, cam, eye, rect) {
  const fwd = norm3(sub3(cam.target, eye));
  const right = norm3(cross3(fwd, UP));
  const upv = cross3(right, fwd);
  const tanF = Math.tan(cam.fov / 2), aspect = rect.width / rect.height;
  const d = sub3(P, eye);
  const dz = dot3(d, fwd);
  const kx = dot3(d, right) / dz, ky = dot3(d, upv) / dz;
  const ndcX = kx / (tanF * aspect), ndcY = ky / tanF;
  return { x: rect.left + (ndcX + 1) / 2 * rect.width,
           y: rect.top + (1 - ndcY) / 2 * rect.height, behind: dz <= 0 };
}
/* the probe's twin of the page's pickWorld for one pixel -- diagnostic
   only (measured: it can disagree with the page near silhouettes; the
   page's own pick is the authority) */
function pickPixel(px, py, cam, eye, rect, P, idx) {
  const fwd = norm3(sub3(cam.target, eye));
  const right = norm3(cross3(fwd, UP));
  const upv = cross3(right, fwd);
  const tanF = Math.tan(cam.fov / 2), aspect = rect.width / rect.height;
  const ndcX = ((px - rect.left) / rect.width) * 2 - 1;
  const ndcY = 1 - ((py - rect.top) / rect.height) * 2;
  const kx = ndcX * tanF * aspect, ky = ndcY * tanF;
  const dir = norm3([fwd[0] + right[0] * kx + upv[0] * ky,
                     fwd[1] + right[1] * kx + upv[1] * ky,
                     fwd[2] + right[2] * kx + upv[2] * ky]);
  const hit = pickFirst(P, idx, eye, dir);
  return hit ? hit.p : null;
}

const CAM_DEFAULT = { r: 26, theta: -0.55, phi: 0.42, target: [0, 4.5, 0],
                      fov: 45 * Math.PI / 180 };
const camState = JSON.parse(JSON.stringify(CAM_DEFAULT));

async function fetchJson(u) { return (await fetch(u)).json(); }
async function waitCalm(capMs) {
  const t0 = Date.now();
  while (Date.now() - t0 < capMs) {
    try {
      const s = await fetchJson(BASE + '/api/state');
      if ((s.P_lower || 0) < 1000 && (s.P_upper || 0) < 1000) return true;
    } catch (e) { /* a silent beat is not a verdict */ }
    await sleep(500);
  }
  return false;
}
/* the streamed mesh in BOTH layouts: il = the interleaved Float64 9-stride
   array (exactly the page's RG.verts -- pickFirst indexes it with the *9
   triangle offsets; a packed stride-3 copy here once garbage-indexed every
   cast and mis-sided the verdicts), pos = packed positions for centroid /
   dent math */
async function fetchVerts() {
  const res = await fetch(BASE + '/api/verts');
  const vb = Buffer.from(await res.arrayBuffer());
  const n = vb.readUInt32LE(0);
  const il = new Float64Array(n * 9);
  const pos = new Float64Array(n * 3);
  for (let i = 0; i < n; i++) {
    for (let k = 0; k < 9; k++) il[i * 9 + k] = vb.readFloatLE(4 + i * 36 + k * 4);
    pos[i * 3] = il[i * 9]; pos[i * 3 + 1] = il[i * 9 + 1]; pos[i * 3 + 2] = il[i * 9 + 2];
  }
  return { il, pos };
}
async function fetchTopology() {
  const res = await fetch(BASE + '/api/topology');
  const tb = Buffer.from(await res.arrayBuffer());
  const n = tb.readUInt32LE(0);
  const idx = new Uint32Array(n * 3);
  for (let i = 0; i < n * 3; i++) idx[i] = tb.readUInt32LE(4 + i * 4);
  return idx;
}
function centroidOf(P) {
  let x = 0, y = 0, z = 0; const n = P.length / 3;
  for (let i = 0; i < P.length; i += 3) { x += P[i]; y += P[i + 1]; z += P[i + 2]; }
  return [x / n, y / n, z / n];
}
/* identical summation to the page's __h16pickProbe checksum over the
   INTERLEAVED floats, so an exact match proves the page's RG.verts == the
   engine's /api/verts (the raycast reads the same buffer the renderer
   draws). Measured live: exact equality to the last bit. */
function meshChecksum(il) {
  let s1 = 0, s2 = 0, n = 0;
  for (let i = 0; i < il.length; i += 3) {
    s1 += il[i] + il[i + 1] + il[i + 2];
    s2 += il[i] * il[i] + il[i + 1] * il[i + 1] + il[i + 2] * il[i + 2];
    n++;
  }
  return { sum1: s1, sum2: s2, vertCount: n };
}
/* nearest streamed-mesh vertex to a point (on-body check for pressPoint) */
function nearestVertexDist(P, p) {
  let bd = Infinity;
  for (let i = 0; i < P.length; i += 3) {
    const dx = P[i] - p[0], dy = P[i + 1] - p[1], dz = P[i + 2] - p[2];
    const d2 = dx * dx + dy * dy + dz * dz;
    if (d2 < bd) bd = d2;
  }
  return Math.sqrt(bd);
}
/* is pressPoint on the SEEN surface? 'seen' = the eye's ray to it is
   unobstructed; 'blind' = the body occludes it; 'air' = it is off-body.
   il = the INTERLEAVED 9-stride mesh (pickFirst's layout), pos = packed
   positions (nearest-vertex layout). */
function pressVisibility(il, pos, idx, eye, pressPoint) {
  const off = nearestVertexDist(pos, pressPoint);
  const to = sub3(pressPoint, eye), dist = len3(to);
  const hit = pickFirst(il, idx, eye, mul3(to, 1 / dist));
  const seen = !!hit && hit.t > dist - 5e-3;
  return { verdict: seen ? 'seen' : (off < 0.15 ? 'blind' : 'air'),
           offMesh: +off.toFixed(4),
           castT: hit ? +hit.t.toFixed(3) : null, distToEye: +dist.toFixed(3) };
}

let IDX = null;

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });
  const pageErrors = [];
  page.on('pageerror', e => pageErrors.push(String(e.message).slice(0, 200)));
  page.on('console', m => {
    if (m.type() === 'error') pageErrors.push('console.error: ' + m.text().slice(0, 200));
  });
  await page.goto(URL_, { waitUntil: 'load' });
  await page.fill('#name-input', NAME);
  await page.click('#play-btn');
  try { await page.click('#intro-begin', { timeout: 5000 }); } catch (e) { /* no first-run intro */ }

  // the world's mesh must be streamed before anything is aimed
  for (let i = 0; i < 60; i++) {
    try { IDX = await fetchTopology(); if (IDX.length) break; } catch (e) {}
    await sleep(1000);
  }
  if (!IDX || !IDX.length) throw new Error('no topology through the page');
  await sleep(3000);   // the page's own delta stream settles onto the live buffer

  // in-page rig: touch-traffic capture ONLY (window.fetch patch; the page
  // itself is never reached into -- it is an IIFE).
  await page.evaluate(() => {
    window.__touchLog = [];
    const of = window.fetch.bind(window);
    window.fetch = function (url, opts) {
      const u = (typeof url === 'string') ? url : (url && url.url) || '';
      const isTouch = u.indexOf('/api/touch_hit') >= 0 || u.indexOf('/api/touch_clear') >= 0;
      if (!isTouch) return of.apply(null, arguments);
      let req = null;
      try { req = opts && opts.body ? JSON.parse(opts.body) : null; } catch (e) {}
      const t0 = Date.now();
      return of.apply(null, arguments).then(async res => {
        let body = null;
        try { body = await res.clone().json(); } catch (e) {}
        window.__touchLog.push({ url: u, status: res.status, req, res: body,
          ms: Date.now() - t0, t: t0 });
        return res;
      });
    };
  });
  const rect = await page.evaluate(() => {
    const r = document.getElementById('gl').getBoundingClientRect();
    return { left: r.left, top: r.top, width: r.width, height: r.height };
  });
  const setForce = n => page.evaluate(v => {
    const f = document.getElementById('force');
    f.value = String(v);
    f.dispatchEvent(new Event('input'));
  }, n);
  /* a REAL orbit drag through the page's own pointer handlers: one move
     event, so theta -= dx*0.005 is EXACT. Down-to-move inside the 130 ms
     stillness window, so a drag never arms a press. */
  async function dragThetaTo(thetaNew) {
    const dTheta = thetaNew - camState.theta;
    if (Math.abs(dTheta) < 1e-9) return;
    const dx = -dTheta / 0.005;
    const cx = rect.left + rect.width / 2, cy = rect.top + rect.height / 2;
    const owner = await page.evaluate(p => {
      const el = document.elementFromPoint(p.x, p.y);
      return el ? (el.id || el.tagName) : 'none';
    }, { x: cx, y: cy });
    if (owner !== 'gl') throw new Error('orbit drag blocked by ' + owner);
    await page.mouse.move(cx, cy); await sleep(50);
    await page.mouse.down(); await sleep(30);
    await page.mouse.move(cx + dx, cy, { steps: 1 }); await sleep(60);
    await page.mouse.up(); await sleep(250);
    camState.theta = thetaNew;   // exact per the handler's math
  }

  const rows = [];
  const shots = __dirname;

  /* dent measurement, shift-corrected (a 20 kN press KICKS the whole
     body; the deformation, not the rigid motion, is what counts), plus
     the press-point siding analysis */
  function analyze(basePos, heldPos, baseIL, eye, pressPoint) {
    const C = centroidOf(basePos);
    const shift = sub3(centroidOf(heldPos), C);
    let localDent = 0, topD = -1, topV = null;
    for (let i = 0; i < heldPos.length; i += 3) {
      const dx = (heldPos[i] - shift[0]) - basePos[i],
            dy = (heldPos[i + 1] - shift[1]) - basePos[i + 1],
            dz = (heldPos[i + 2] - shift[2]) - basePos[i + 2];
      const d2 = dx * dx + dy * dy + dz * dz;
      if (d2 > topD) { topD = d2; topV = [heldPos[i], heldPos[i + 1], heldPos[i + 2]]; }
      const ddx = basePos[i] - pressPoint[0], ddy = basePos[i + 1] - pressPoint[1],
            ddz = basePos[i + 2] - pressPoint[2];
      if (ddx * ddx + ddy * ddy + ddz * ddz < 0.15 * 0.15 && d2 > localDent) localDent = d2;
    }
    return {
      localDent: +Math.sqrt(localDent).toFixed(4),
      globalDent: { v: topV, disp: +Math.sqrt(topD).toFixed(4) },
      shiftM: shift.map(v => +v.toFixed(3)),
      pressVis: pressVisibility(baseIL, basePos, IDX, eye, pressPoint)
    };
  }

  async function control() {
    await waitCalm(20000);
    await setForce(20000);
    await sleep(500);
    const eye = eyeOf(camState);
    const base = await fetchVerts();
    await sleep(750);
    const held = await fetchVerts();
    const a = analyze(base.pos, held.pos, base.il, eye, [999, 999, 999]);   // far-away point: noise floor
    rows.push({ tag: 'control-no-press', expect: 'noise floor',
                localDentAtFarPoint: a.localDent,
                globalDent: a.globalDent, shiftM: a.shiftM });
    console.log('CONTROL no press: localDentAtFarPoint=' + a.localDent +
      ' m  global=' + a.globalDent.disp + ' m  (the noise floor)');
  }

  async function cycle(tag, camKind, seed, regionR, force, withShots, useCentroid) {
    await waitCalm(25000);
    const thetaTarget = camKind === 'opposite' ? CAM_DEFAULT.theta + Math.PI : CAM_DEFAULT.theta;
    await dragThetaTo(thetaTarget);
    await setForce(force);
    await sleep(700);
    const eye = eyeOf(camState);
    const cam = JSON.parse(JSON.stringify(camState)); cam.fov = CAM_DEFAULT.fov;
    const base = await fetchVerts();
    const basePos = base.pos;
    const C0 = centroidOf(basePos);
    /* AIM ONLY: the click pixel. Torso = the body's screen-center pixel
       (the operator's repro: both the true ray and the engine's mirrored
       ray cross the body there). Foot = the most-facing streamed vertex
       near the seed, so the cursor sits on the limb. */
    let pj = null;
    if (useCentroid) {
      const p = project(C0, cam, eye, rect);
      if (!p.behind) pj = p;
    } else {
      let bs = -Infinity, bv = null;
      for (let i = 0; i < basePos.length; i += 3) {
        const dx = basePos[i] - seed[0], dy = basePos[i + 1] - seed[1], dz = basePos[i + 2] - seed[2];
        if (dx * dx + dy * dy + dz * dz > regionR * regionR) continue;
        const s = dot3(sub3([basePos[i], basePos[i + 1], basePos[i + 2]], C0), norm3(sub3(eye, C0)));
        if (s > bs) {
          const p = project([basePos[i], basePos[i + 1], basePos[i + 2]], cam, eye, rect);
          if (p.behind || p.x < rect.left || p.x > rect.left + rect.width ||
              p.y < rect.top || p.y > rect.top + rect.height) continue;
          bs = s; bv = p;
        }
      }
      pj = bv;
    }
    if (!pj) { rows.push({ tag, error: 'no on-canvas aim pixel' }); return; }
    /* THE PICK PROBE (?debug=1 hook): the page's OWN camEye + pickWorld at
       this exact pixel, plus the RG.verts checksum -- settles whose eye,
       whose math, and which buffer in one call */
    let probe = null, myRawPick = null, mySum = null;
    try {
      probe = await page.evaluate(([x, y]) => window.__h16pickProbe(x, y), [pj.x, pj.y]);
      myRawPick = pickPixel(pj.x, pj.y, cam, eye, rect, base.il, IDX);
      mySum = meshChecksum(base.il);
    } catch (e) { probe = { error: String(e.message).slice(0, 120) }; }
    const owner = await page.evaluate(pt => {
      const el = document.elementFromPoint(pt.x, pt.y);
      return el ? (el.id || el.tagName) : 'none';
    }, { x: pj.x, y: pj.y });
    if (owner !== 'gl') {
      rows.push({ tag, error: 'aim pixel covered by ' + owner });
      console.log(tag + ': BLOCKED -- ' + owner);
      return;
    }
    const t0 = Date.now();
    if (withShots) await page.screenshot({ path: shots + '/page_before_' + PHASE + '_' + tag + '.png' });
    await page.mouse.move(pj.x, pj.y); await sleep(150);
    await page.mouse.down();
    await sleep(800);                       // 130 ms arm + POST + the dent sets
    const held = await fetchVerts();
    let frameKB = null;
    if (withShots) {
      await page.screenshot({ path: shots + '/page_held_' + PHASE + '_' + tag + '.png' });
      try {   // the ENGINE's default camera, named by the falsifier brief (read-only)
        const fr = await fetch(BASE.replace(':8206', ':8107') + '/frame?w=800&fmt=jpg');
        const ab = await fr.arrayBuffer();
        fs.writeFileSync(shots + '/engine_frame_' + PHASE + '_' + tag + '.jpg', Buffer.from(ab));
        frameKB = +(ab.byteLength / 1024).toFixed(0);
      } catch (e) { frameKB = -1; }
    }
    const stateNow = await fetchJson(BASE + '/api/state').catch(() => null);
    const traffic = await page.evaluate(t0 =>
      window.__touchLog.filter(e => e.t >= t0 && e.url.indexOf('touch_hit') >= 0), t0);
    await page.mouse.up();
    await sleep(300);
    await page.keyboard.press('Escape');    // belt to the pointerup's braces
    const entry = (traffic && traffic.length) ? traffic[traffic.length - 1] : null;
    const reqForm = entry && entry.req
      ? (entry.req.cam !== undefined ? 'cam+pixel' : (entry.req.hit ? 'hit' : 'other'))
      : 'no-post';
    /* THE MARK AUTHORITY: where the press actually landed.
       after: the page's own picked point (request.hit)
       before: the engine's resolved point (response.hit) -- the old path */
    const pressPoint = entry && entry.req && entry.req.hit ? entry.req.hit
      : (entry && entry.res && entry.res.hit ? entry.res.hit : null);
    const a = pressPoint ? analyze(basePos, held.pos, base.il, eye, pressPoint) : null;
    const onAimDist = pressPoint ? +len3(sub3(pressPoint, seed)).toFixed(3) : null;
    const near = !!(a && a.pressVis.verdict === 'seen' && a.localDent > 0.002 &&
                    onAimDist !== null && onAimDist < regionR);
    rows.push({
      tag, camKind, force,
      camProbe: { r: cam.r, theta: +cam.theta.toFixed(4), phi: cam.phi,
                  target: cam.target },
      eye: eye.map(v => +v.toFixed(2)), pixel: { x: +pj.x.toFixed(1), y: +pj.y.toFixed(1) },
      reqForm, request: entry ? entry.req : null,
      response: entry ? { status: entry.status, body: entry.res, ms: entry.ms } : null,
      pressPoint: pressPoint && pressPoint.map(v => +v.toFixed(3)),
      onAimDist,
      pressVisibility: a ? a.pressVis : null,
      pickProbe: probe ? {
        pageEye: probe.eye && probe.eye.map(v => +v.toFixed(2)),
        pageRawPick: probe.raw && probe.raw.map(v => +v.toFixed(3)),
        myRawPick: myRawPick && myRawPick.map(v => +v.toFixed(3)),
        bufferMatch: !!(probe.sum1 === (mySum && mySum.sum1) &&
                        probe.sum2 === (mySum && mySum.sum2) &&
                        probe.vertCount === (mySum && mySum.vertCount))
      } : { unavailable: true },
      localDentAtPress: a ? a.localDent : null,
      globalDent: a ? a.globalDent : null, shiftM: a ? a.shiftM : null,
      dimpleMwhileHeld: stateNow ? stateNow.dimple_m : null,
      frameKB,
      VERDICT: near ? 'NEAR (seen side)' : 'FAR (blind side)'
    });
    console.log(tag + ': click(' + pj.x.toFixed(0) + ',' + pj.y.toFixed(0) + ') f=' + force +
      ' req=' + reqForm +
      ' press=' + (pressPoint ? pressPoint.map(v => v.toFixed(2)).join(',') : 'none') +
      ' vis=' + (a ? a.pressVis.verdict : '?') +
      ' localDent=' + (a ? a.localDent : '?') +
      (frameKB ? ' frame=' + frameKB + 'KB' : '') +
      ' -> ' + (near ? 'NEAR (seen side)' : 'FAR (blind side)'));
  }

  const TORSO_SEED = [0.0, 4.5, 0.35], TORSO_R = 2.0;
  const FOOT_SEED = [0.46, 0.18, 0.3], FOOT_R = 0.6;

  await control();
  for (let i = 1; i <= 5; i++)
    await cycle('torso-default-' + i, 'default', TORSO_SEED, TORSO_R, 20000, i === 1, true);
  await cycle('torso-opposite-orbit', 'opposite', TORSO_SEED, TORSO_R, 20000, false, true);
  await cycle('foot-default', 'default', FOOT_SEED, FOOT_R, 2000, true, false);

  const scored = rows.filter(r => r.VERDICT);
  const nearN = scored.filter(r => r.VERDICT.indexOf('NEAR') === 0).length;
  const defRows = scored.filter(r => r.camKind === 'default');
  const nearDef = defRows.filter(r => r.VERDICT.indexOf('NEAR') === 0).length;
  const summary = {
    phase: PHASE, base: BASE, playerName: NAME,
    falsifier: 'the press lands where the player LOOKS: pressPoint visible from the page eye (seen surface) AND the dent (shift-corrected, >2 mm) is at the pressPoint',
    expectation: PHASE === 'before'
      ? 'DEFECT LIVE: all ' + scored.length + ' press rows FAR (the cam+pixel press lands on the blind side, in the air, or on the wrong limb)'
      : 'DEFECT GONE: all ' + scored.length + ' press rows NEAR; request is the {"hit":...} form; pressPoint exactly on the streamed mesh',
    rows: rows.length, scored: scored.length, near: nearN, far: scored.length - nearN,
    defaultRows: defRows.length, nearDefault: nearDef,
    expectationMet: PHASE === 'before' ? nearN === 0
      : (nearN === scored.length && scored.length >= 7),
    pageErrors
  };
  fs.writeFileSync(OUT, JSON.stringify({ summary, rows }, null, 1));
  console.log('\nSUMMARY[' + PHASE + ']: near=' + nearN + '/' + scored.length +
    ' (default-orbit: ' + nearDef + '/' + defRows.length + ')' +
    '  expectationMet=' + summary.expectationMet +
    '  pageErrors=' + pageErrors.length);
  console.log('written: ' + OUT);
  await browser.close();
  process.exit(summary.expectationMet ? 0 : 2);
})().catch(e => { console.error('PROBE FAILED:', e); process.exit(1); });
