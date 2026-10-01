/* accept_h7r_e2.js -- acceptance (e), corrected aim: the page's live camera
   (GET /api/cam -> target [0,0,0]) is used to project the world points, so
   the clicked pixels land on the intended part. Pass = a foot click's press
   hint resolves to the foot band, a torso click's to the body band, and the
   two hits are DIFFERENT engine-resolved vertices (the H9 defect returned
   undefined for every click -> the synth always said 'body'). */
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
  // the LIVE camera, not an assumed one
  const camArr = await page.evaluate(() =>
    fetch('/api/cam').then(r => r.json()).then(d => d.cam));
  const C = { r: camArr[0], theta: camArr[1], phi: camArr[2],
              target: [camArr[3], camArr[4], camArr[5]], panX: camArr[6], panY: camArr[7] };
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
  const clickPart = async (wx, wy, wz) => {
    await waitCalm();
    const n0 = await page.evaluate(() => window.ChimeraSound.__pressArgs.length);
    const px = await aimAt(wx, wy, wz);
    await page.mouse.click(px.x, px.y);
    await sleep(1500);   // tap press + pulse
    const args = await page.evaluate(n0 =>
      window.ChimeraSound.__pressArgs.slice(n0), n0);
    return args;
  };
  const bandName = y => y < 0.338 ? 'foot' : y < 1.903 ? 'shin' :
    y < 3.415 ? 'thigh' : 'body';
  const R = { cam: C };
  R.foot = await clickPart(0.0, 0.15, 0.25);      // the foot
  R.torso = await clickPart(0.0, 4.5, 0.30);      // the torso
  const fh = R.foot.length && R.foot[0].region, th = R.torso.length && R.torso[0].region;
  R.footRegion = Array.isArray(fh) ? bandName(fh[1]) : String(fh);
  R.torsoRegion = Array.isArray(th) ? bandName(th[1]) : String(th);
  R.hitsDiffer = JSON.stringify(fh) !== JSON.stringify(th);
  R.CLEAN = Array.isArray(fh) && Array.isArray(th) &&
    R.footRegion === 'foot' && R.torsoRegion === 'body' && R.hitsDiffer;
  console.log('foot click -> hit', JSON.stringify(fh), '-> band', R.footRegion);
  console.log('torso click -> hit', JSON.stringify(th), '-> band', R.torsoRegion);
  console.log('hits differ:', R.hitsDiffer, '=>', R.CLEAN ? 'CLICK SOUNDS THE PART' : 'FAIL');
  console.log('pageerrors:', errs.length);
  R.pageErrors = errs;
  fs.writeFileSync(__dirname + '/accept_h7r_e2.json', JSON.stringify(R, null, 1));
  await browser.close();
})().catch(e => { console.error('PROBE FAILED:', e); process.exit(1); });
