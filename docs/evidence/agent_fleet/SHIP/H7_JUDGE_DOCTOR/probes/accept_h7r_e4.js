/* accept_h7r_e4.js -- acceptance (e), calibrated + foot-area scan.
   Torso click already proven (accept_h7r_e3: engine hit y=4.479 -> body).
   The foot is small and the creature stands off-origin (hits cluster near
   x -0.4..-0.7, z -0.4..-0.7), so scan a small ladder of aims in the foot
   region until the engine resolves a hit; PASS when that hit lands in the
   foot band (y < 0.338) and the torso hit in the body band, both REAL
   parsed points (H9's defect: always undefined -> always 'body'). */
const path = require('path');
const fs = require('fs');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errs = [];
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  await page.goto('http://127.0.0.1:8206/?debug=1', { waitUntil: 'load' });
  await sleep(2000);
  await page.fill('#name-input', 'h7raccept');
  await page.click('#play-btn'); await sleep(1200);
  try { await page.click('#intro-begin', { timeout: 3000 }); } catch (e) {}
  await sleep(800);
  await page.evaluate(() => {
    const S = window.ChimeraSound;
    S.__pressArgs = [];
    const orig = S.press;
    S.press = function (force, region) {
      S.__pressArgs.push({ force, region });
      return orig.apply(S, arguments);
    };
  });
  const camArr = await page.evaluate(() =>
    fetch('/api/cam').then(r => r.json()).then(d => d.cam));
  const C = { r: camArr[0], theta: camArr[1], phi: camArr[2],
              target: [camArr[3], camArr[4], camArr[5]] };
  const aimAt = async (wx, wy, wz) => page.evaluate(([C, wx, wy, wz]) => {
    const vsub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
    const vdot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
    const vcross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
    const vnorm = a => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
    const ch = Math.cos(C.phi);
    const eye = [C.target[0] + C.r * ch * Math.sin(C.theta), C.target[1] + C.r * Math.sin(C.phi),
                 C.target[2] + C.r * ch * Math.cos(C.theta)];
    const cv = document.getElementById('gl'); const b = cv.getBoundingClientRect();
    const tanF = Math.tan(45 * Math.PI / 360);
    const fwd = vnorm(vsub(C.target, eye));
    const right = vnorm(vcross(fwd, [0, 1, 0])); const up = vcross(right, fwd);
    const d = vsub([wx, wy, wz], eye); const a = vdot(d, fwd);
    const ndcX = (vdot(d, right) / a) / (tanF * (cv.width / cv.height));
    const ndcY = (vdot(d, up) / a) / tanF;
    return { x: b.left + (ndcX + 1) / 2 * b.width, y: b.top + (1 - ndcY) / 2 * b.height };
  }, [C, wx, wy, wz]);
  const waitCalm = async () => {
    for (let k = 0; k < 25; k++) {
      const ps = await page.evaluate(() => fetch('/api/state').then(r => r.json()));
      if (ps.cells.every(c => Math.abs(Number(c.P) || 0) < 1000)) return true;
      await sleep(600);
    }
    return false;
  };
  const clickAt = async (wx, wy, wz) => {
    await waitCalm();
    const n0 = await page.evaluate(() => window.ChimeraSound.__pressArgs.length);
    const px = await aimAt(wx, wy, wz);
    await page.mouse.click(px.x, px.y);
    await sleep(1500);
    const args = await page.evaluate(n0 =>
      window.ChimeraSound.__pressArgs.slice(n0), n0);
    return args.length ? args[0].region : null;   // null = engine refused the click
  };
  const bandName = y => y < 0.338 ? 'foot' : y < 1.903 ? 'shin' :
    y < 3.415 ? 'thigh' : 'body';
  const OFF = 4.65;   // engineHitY = aimedY + OFF (measured, accept_h7r_e2/e3)
  const R = { scan: [] };
  // torso first (known good)
  R.torsoHint = await clickAt(0, 4.5 - OFF, 0.28);
  // foot scan: lowest rung first; stop at the first resolved hit
  outer:
  for (const x of [-0.5, -0.35, -0.2, -0.65, 0]) {
    for (const ey of [0.10, 0.22, 0.32]) {
      const hint = await clickAt(x, ey - OFF, -0.45);
      R.scan.push({ aim: [x, ey, -0.45], hint });
      if (Array.isArray(hint)) { R.footHint = hint; break outer; }
    }
  }
  const fh = Array.isArray(R.footHint) ? R.footHint : null;
  const th = Array.isArray(R.torsoHint) ? R.torsoHint : null;
  R.footHitY = fh ? fh[1] : null;  R.torsoHitY = th ? th[1] : null;
  R.footRegion = fh ? bandName(fh[1]) : null;
  R.torsoRegion = th ? bandName(th[1]) : null;
  R.hitsDiffer = JSON.stringify(R.footHint) !== JSON.stringify(R.torsoHint);
  R.CLEAN = !!fh && !!th && R.footRegion === 'foot' &&
    R.torsoRegion === 'body' && R.hitsDiffer;
  console.log('foot scan:', JSON.stringify(R.scan));
  console.log('foot click  -> engine hit', JSON.stringify(R.footHint), '-> band', R.footRegion);
  console.log('torso click -> engine hit', JSON.stringify(R.torsoHint), '-> band', R.torsoRegion);
  console.log('=>', R.CLEAN ? 'CLICK SOUNDS THE PART' : 'FAIL');
  R.pageErrors = errs;
  fs.writeFileSync(__dirname + '/accept_h7r_e4.json', JSON.stringify(R, null, 1));
  await browser.close();
})().catch(e => { console.error('PROBE FAILED:', e); process.exit(1); });
