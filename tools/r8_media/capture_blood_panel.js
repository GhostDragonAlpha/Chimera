/* capture_blood_panel.js -- D2 R8 MEDIA: the blood-panel proof shots.
   A private, HEADED Chrome drives the game page at :8206 the way a player
   would and captures three honest screenshots of the creature's blood:

     blood_rest.png          -- every cell at 0.000 MPa, "the creature waits."
     blood_press.png         -- 30 kN on the torso: live MPa, awake accent,
                                the judge's release prompt, mid-press
     blood_lesson_passed.png -- lesson 2 (the_gentle_hand) PASSED, verdict 'good'

   THE TOUCH KERNEL TRUTH (measured, see index.html): a press is a 3 cm
   Gaussian around the world point -- an unsnapped point presses NOTHING
   while /tick_touch answers ok:true (a silent lie). So every target here is
   snapped to its nearest skin vertex via /api/verts (u32 count + n*9 f32,
   interleaved pos3/normal3/color3) before it is pressed.

   Run: node tools/r8_media/capture_blood_panel.js
   Output: C:/Users/allen/Desktop/CHIMERA_PROOF/R8_MEDIA/ */
const path = require('path');
const fs = require('fs');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));

const URL_ = 'http://127.0.0.1:8206';
const OUT = 'C:/Users/allen/Desktop/CHIMERA_PROOF/R8_MEDIA';
const PROG = 'E:/ChimeraWork/slot-01/tools/game_shell/progress/media.json';
const NAME = 'media';
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  // A stale progress file for this name would pre-latch lessonState.passed and
  // the judge would never re-arm -- the release prompt would be dead. Fresh name.
  if (fs.existsSync(PROG)) { fs.unlinkSync(PROG); console.log('reset stale progress for "' + NAME + '"'); }

  const browser = await chromium.launch({ channel: 'chrome', headless: false });
  const page = await browser.newPage({
    viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1,
  });
  page.on('pageerror', e => console.log('PAGE ERROR:', e.message));

  await page.goto(URL_, { waitUntil: 'load' });
  await sleep(1500);
  await page.fill('#name-input', NAME);
  await page.click('#play-btn');
  try {   // E4: the first-run greeting owns the screen until begun
    await page.waitForSelector('#intro-overlay:not(.hidden)', { timeout: 8000 });
    await page.click('#intro-begin');
    console.log('intro dismissed');
  } catch (e) { /* a returning name skips it */ }
  await sleep(1200);

  // ---- world helpers -------------------------------------------------------
  // RG lives inside the page's IIFE (not on window), so topology readiness is
  // read the way the page itself reads it: /api/topology's u32 tri count.
  const triCount = async () => page.evaluate(() =>
    fetch('/api/topology').then(r => r.arrayBuffer())
      .then(b => new DataView(b).getUint32(0, true)).catch(() => 0));
  let tris = 0;
  for (let i = 0; i < 60 && !tris; i++) { tris = await triCount(); if (!tris) await sleep(500); }
  if (!tris) throw new Error('no topology streamed from the world');
  console.log('topology triangles:', tris);
  await sleep(2500);                                    // verts stream + render settle

  const state = async () => page.evaluate(() =>
    fetch('/api/state').then(r => r.json()));
  const pressN = async () => {                          // waitCalm: every |P| < 1000 Pa
    const t0 = Date.now();
    let ps = [];
    while (Date.now() - t0 < 25000) {
      try {
        const s = await state();
        ps = (s.cells || []).map(c => Math.abs(Number(c.P) || 0));
        if (ps.length && ps.every(p => p < 1000)) {
          console.log('   calm after ' + ((Date.now() - t0) / 1000).toFixed(1) + 's  |P| Pa: ' +
            ps.map(p => Math.round(p)).join(' '));
          return true;
        }
      } catch (e) { /* a silent beat is not a verdict */ }
      await sleep(250);
    }
    console.log('   NEVER CALM  |P| Pa: ' + ps.map(p => Math.round(p)).join(' '));
    return false;
  };
  const snap = async (pt) => page.evaluate(async (target) => {
    const res = await fetch('/api/verts');
    const buf = await res.arrayBuffer();
    const n = new DataView(buf).getUint32(0, true);
    const f = new Float32Array(buf, 4, n * 9);
    let best = -1, bd = Infinity;
    for (let i = 0; i < n; i++) {
      const dx = f[i * 9] - target[0], dy = f[i * 9 + 1] - target[1], dz = f[i * 9 + 2] - target[2];
      const d2 = dx * dx + dy * dy + dz * dz;
      if (d2 < bd) { bd = d2; best = i; }
    }
    return { hit: [f[best * 9], f[best * 9 + 1], f[best * 9 + 2]], dist: Math.sqrt(bd) };
  }, pt);
  const touch = async (hit, forceN) => {                // engine retry: 10 s backoff
    for (let k = 0; ; k++) {
      const r = await page.evaluate(async (body) => {
        try {
          const res = await fetch('/api/touch_hit', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
          });
          return await res.json();
        } catch (e) { return { ok: false, error: String(e) }; }
      }, { hit, force_n: forceN }).catch(e => ({ ok: false, error: String(e) }));
      if (r && r.ok) return r;
      if (k >= 5) throw new Error('touch_hit failed: ' + JSON.stringify(r));
      console.log('   touch retry ' + (k + 1) + ' -- ' + JSON.stringify(r));
      await sleep(10000);
    }
  };
  const clearTouch = async () => page.evaluate(() =>
    fetch('/api/touch_clear', { method: 'POST' }).then(r => r.json()).catch(() => ({ ok: false })));
  const judgeLine = async () => page.evaluate(() =>
    (document.getElementById('judge-debug') || {}).textContent || '');
  const verdict = async () => page.evaluate(() => {
    const v = document.getElementById('verdict');
    return v ? { text: v.textContent, cls: v.className } : { text: '', cls: '' };
  });
  const blood = async () => page.evaluate(() => {
    const b = document.getElementById('blood');
    return { text: b ? b.textContent : '', awake: !!(b && b.querySelector('.awake')) };
  });
  const setForce = async (n) => page.evaluate((v) => {
    const el = document.getElementById('force');
    el.value = String(v);
    el.dispatchEvent(new Event('input'));
  }, n);

  // ---- shot (a): blood_rest -- everything at rest ---------------------------
  console.log('shot (a) blood_rest: waiting for a calm body ...');
  await pressN();
  const st0 = await state();
  const blood0 = await blood();
  const v0 = await verdict();
  console.log('   cells: ' + JSON.stringify((st0.cells || []).map(c => (Number(c.P) / 1e6).toFixed(3))) + ' MPa');
  console.log('   verdict: "' + v0.text + '" [' + v0.cls + ']');
  if (!v0.text.includes('the creature waits'))
    throw new Error('rest verdict is not "the creature waits.": ' + JSON.stringify(v0));
  const notZero = (st0.cells || []).filter(c => Math.abs(Number(c.P) || 0) >= 500);
  if (notZero.length) throw new Error('rest shot would not read 0.000 MPa: ' + JSON.stringify(notZero));
  await page.screenshot({ path: OUT + '/blood_rest.png' });
  console.log('   saved blood_rest.png');

  // ---- shot (b): blood_press -- 30 kN on the torso, mid-press ----------------
  console.log('shot (b) blood_press: 30000 N on the snapped torso point ...');
  await setForce(30000);
  const torso = await snap([0, 4.5, 0.32]);
  console.log('   snapped [0,4.5,0.32] -> ' + torso.hit.map(x => x.toFixed(4)).join(', ') +
    '  (dist ' + torso.dist.toFixed(4) + ' m)');
  await touch(torso.hit, 30000);
  console.log('   touch posted: ' + await judgeLine());

  // poll until the torso reads live MPa, the awake accent shows, and the
  // judge's release prompt is up. Fallback: the page's own SPACE press on
  // lesson 1's pre-snapped target.
  let viaFallback = false;
  const torsoP = async () => {
    const s = await state();
    return Math.abs(Number((s.cells || [])[1] && (s.cells || [])[1].P) || 0);
  };
  const t0 = Date.now();
  let maxP = 0;
  while (Date.now() - t0 < 8000) {
    maxP = Math.max(maxP, await torsoP());
    if (maxP >= 20000) break;
    await sleep(250);
  }
  if (maxP < 20000) {                    // the direct press woke nothing -> SPACE
    console.log('   direct press silent (peak ' + Math.round(maxP) + ' Pa) -- falling back to the page SPACE press');
    await clearTouch();
    await sleep(500);
    viaFallback = true;
    await page.keyboard.down(' ');
    await sleep(1200);
    const t1 = Date.now();
    while (Date.now() - t1 < 10000) {
      maxP = Math.max(maxP, await torsoP());
      if (maxP >= 20000) break;
      await sleep(250);
    }
  }
  // the judge latches goalMet -> phase=release -> the release prompt
  const t2 = Date.now();
  while (Date.now() - t2 < 10000) {
    const v = await verdict();
    if (v.text.includes('LET GO')) break;
    await sleep(250);
  }
  // the awake accent (|P| >= 0.2 MPa) -- give it its own beat
  const t3 = Date.now();
  while (Date.now() - t3 < 8000) {
    if ((await blood()).awake) break;
    await sleep(250);
  }
  const stB = await state(), blB = await blood(), vB = await verdict();
  const mpa = (stB.cells || []).map(c => (Number(c.P) / 1e6).toFixed(3)).join(' ');
  console.log('   mid-press cells MPa: ' + mpa + (viaFallback ? '  [via SPACE fallback]' : ''));
  console.log('   awake accent: ' + blB.awake + '  verdict: "' + vB.text + '" [' + vB.cls + ']');
  await page.screenshot({ path: OUT + '/blood_press.png' });
  console.log('   saved blood_press.png');
  // release: let go and wait for the heal (tau = 0.5 s) before lesson 2
  if (viaFallback) await page.keyboard.up(' ');
  else await clearTouch();
  await pressN();

  // ---- shot (c): blood_lesson_passed -- lesson 2 PASSED ----------------------
  console.log('shot (c) blood_lesson_passed: lesson 2 (the_gentle_hand) ...');
  await page.click('#lesson-next');
  await sleep(800);
  console.log('   ' + await judgeLine());
  await setForce(6000);                                  // under the 8000 N cap
  const foot = await snap([0.46, 0.18, 0.30]);
  console.log('   snapped [0.46,0.18,0.30] -> ' + foot.hit.map(x => x.toFixed(4)).join(', ') +
    '  (dist ' + foot.dist.toFixed(4) + ' m)');
  await touch(foot.hit, 6000);
  const t4 = Date.now();                                 // judge goalMet (cell 0 >= 200 Pa)
  while (Date.now() - t4 < 15000) {
    if (/goalMet=true/.test(await judgeLine())) break;
    await sleep(250);
  }
  console.log('   goal latched: ' + await judgeLine());
  // RELEASE. The page's #letgo-btn is a no-op here: its clearTouch() early-returns
  // when `holding` is false, and a direct /api/touch_hit POST never sets it. So the
  // release goes through the same channel the press used -- POST /api/touch_clear --
  // and is VERIFIED by the pressure actually decaying.
  await clearTouch();
  await sleep(400);
  if (await torsoP() > 5000) {           // a dropped clear is retried, never assumed
    console.log('   clear did not land -- retrying');
    await clearTouch();
  }
  await pressN();
  const t5 = Date.now();                                 // the judge's calm poll -> PASSED
  let passed = false;
  while (Date.now() - t5 < 15000) {
    const v = await verdict();
    if (v.cls.includes('good') && v.text.includes('PASSED')) { passed = true; break; }
    await sleep(250);
  }
  const vC = await verdict();
  console.log('   verdict: "' + vC.text + '" [' + vC.cls + ']  passed=' + passed);
  if (!passed) throw new Error('lesson 2 never showed a PASSED verdict');
  await page.screenshot({ path: OUT + '/blood_lesson_passed.png' });
  console.log('   saved blood_lesson_passed.png');

  // ---- restore: no touch held, body calm ------------------------------------
  await clearTouch();
  const calm = await pressN();
  console.log('RESTORE: touch cleared, calm=' + calm);
  await browser.close();
  process.exit(0);
})().catch(e => { console.error('BLOOD CAPTURE FAILED:', e.message); process.exit(1); });
