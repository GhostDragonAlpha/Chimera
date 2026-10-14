/* framing_probe.js -- THE FRAMING PROBE (lane render-truth-20260920).
   The camera is the page's OWN client view (the player's orbit/zoom); this
   probe renders CANDIDATE framings through the page's own draw path and
   saves the page canvas's own bytes so the framing is chosen from pixels,
   not taste. Candidates derive from the body's measured extent:
   length 0.605 m (long axis z, probe pos_min/max: z +-0.3026), height
   0.269 m; horizontal frame extent 1.717*dist at the slice's own 0.9 rad
   fov and the 640x360 capture viewport. Readable-phase dist 0.64 puts the
   body at ~55% of frame width. Wide fall framing (dist 1.1, ty 0.52) keeps
   the measured fall peak (root_y 0.9009 + ymax 0.1346 -> top ~1.04 m) in
   frame. yaws: the page default 0.7, the derived side profile pi/2 ~1.571,
   and the opposite three-quarter 2.44.

   Usage: node framing_probe.js <baseURL> <outDir>
*/
'use strict';
const fs = require('fs');
const path = require('path');
const pw = require('E:/PythonChimera/node_modules/playwright-core');

const BASE = process.argv[2];
const OUT = process.argv[3];
fs.mkdirSync(OUT, { recursive: true });

const LAUNCH_ARGS = ['--window-size=680,400', '--force-device-scale-factor=1',
  '--enable-gpu', '--enable-unsafe-swiftshader', '--no-proxy-server',
  '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
  '--disable-backgrounding-occluded-windows'];

function httpJson(base, p, timeoutMs) {
  return new Promise((res, rej) => {
    const req = require('http').get(base + p, { timeout: timeoutMs || 5000 }, r => {
      let b = '';
      r.on('data', c => (b += c));
      r.on('end', () => { try { res(JSON.parse(b)); } catch (e) { rej(e); } });
    });
    req.on('timeout', () => { req.destroy(); rej(new Error('timeout ' + p)); });
    req.on('error', rej);
  });
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await pw.chromium.launch({ headless: true, args: LAUNCH_ARGS });
  const ctx = await browser.newContext({ viewport: { width: 640, height: 360 } });
  const page = await ctx.newPage();
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('requestfailed', r => errors.push('requestfailed: ' + r.url()));

  await page.goto(BASE + '/', { waitUntil: 'load', timeout: 60000 });
  // page readiness: GLB index buffer parsed, ghost parsed, live verts flowing
  const t0 = Date.now();
  while (Date.now() - t0 < 60000) {
    const ok = await page.evaluate(
      "idxCount>0 && ghost!==null && liveVerts && liveVerts.length>100000 ? 1 : 0");
    if (ok) break;
    await sleep(200);
  }
  const meshSource = await page.evaluate('window.__CHIMERA_MESH_SOURCE');
  const diag = await page.evaluate(async () => {
    const r = await fetch('/standing_body.glb');
    return { status: r.status, bytes: (await r.arrayBuffer()).byteLength,
             beacon: window.__CHIMERA_BEACON };
  });
  console.log('GLB_FETCH ' + JSON.stringify(diag));
  // let the standing start settle (real physics, ~15.5 s measured) so the
  // probe frames show the standing pose the judge will see
  let settled = false;
  while (Date.now() - t0 < 90000 && !settled) {
    await sleep(1000);
    try {
      const st = await httpJson(BASE, '/api/status');
      settled = !!(st.scene && st.scene.settled);
    } catch (e) { /* the world is still arriving */ }
  }
  // hide the HUD (capture-side view choice) and the ghost overlay (the
  // movie lane's recorded view state) so the probe shows the judged subject
  await page.addStyleTag({ content:
    '#honesty,#verdict,#controls,#banner,#keys,#guide,#guidepill,#beacon,#bootstatus,#settle{display:none !important}'});
  await page.evaluate('ghost=null;ghostBase=null;1');

  const candidates = [
    { name: 'yaw0.70_d0.64', yaw: 0.70, dist: 0.64, pit: 0.35, ty: 0.14 },
    { name: 'yaw1.57_d0.64', yaw: 1.571, dist: 0.64, pit: 0.35, ty: 0.14 },
    { name: 'yaw2.44_d0.64', yaw: 2.44, dist: 0.64, pit: 0.35, ty: 0.14 },
    { name: 'yaw1.57_d0.80', yaw: 1.571, dist: 0.80, pit: 0.35, ty: 0.14 },
    { name: 'fall_yaw1.57_d1.10', yaw: 1.571, dist: 1.10, pit: 0.35, ty: 0.52 },
  ];
  for (const c of candidates) {
    // set + draw + read in ONE JS task: without preserveDrawingBuffer the
    // drawing buffer does not survive between tasks (the movie lane's
    // AMENDMENT 2 measurement) -- a split evaluate reads a cleared buffer.
    // Values inlined in an IIFE: node Playwright evaluates a function
    // STRING as an expression (its value is the function -> undefined).
    const data = await page.evaluate(
      "(() => { cam.yaw=" + c.yaw + "; cam.dist=" + c.dist +
      "; cam.pit=" + c.pit + "; cam.tx=0; cam.tz=0; cam.ty=" + c.ty +
      "; draw(); return document.getElementById('gl')" +
      ".toDataURL('image/png'); })()");
    fs.writeFileSync(path.join(OUT, c.name + '.png'),
      Buffer.from(data.split(',', 2)[1], 'base64'));
    console.log('probe frame:', c.name);
  }
  console.log('MESH_SOURCE=' + meshSource);
  console.log('ERRORS=' + errors.length + (errors.length ? ' :: ' + errors.slice(0, 5).join(' | ') : ''));
  await browser.close();
  process.exit(errors.length === 0 ? 0 : 1);
})().catch(e => { console.error('FRAMING PROBE FAILED:', e.message); process.exit(1); });
