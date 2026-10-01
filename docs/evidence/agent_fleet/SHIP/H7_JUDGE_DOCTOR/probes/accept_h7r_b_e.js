/* accept_h7r_b_e.js -- H7r acceptance (b) and (e).
   (b) lessons 1-3 pass on REAL page input (SPACE rail + the '-' force key),
       each with its OWN pass sentence (H5 S3's identical-sentence defect).
   (e) a canvas click on a named body part sounds THAT part: the press
       sound's region hint is the engine's resolved hit (H9 blocker 2 --
       it used to be undefined, every click sounded 'body').
   Run: node accept_h7r_b_e.js */
const path = require('path');
const fs = require('fs');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const R = {};
  const verdict = () => page.evaluate(() =>
    (document.getElementById('verdict') || {}).textContent);
  const judge = async () => {
    const m = (await page.evaluate(() =>
      (document.getElementById('judge-debug') || {}).textContent || ''))
      .match(/judge: (\S+) phase=(\S+) goalMet=(\S+) passed=(\S+)/);
    return m ? { id: m[1], phase: m[2], goalMet: m[3] === 'true', passed: m[4] === 'true' } : {};
  };
  const aimAt = async (wx, wy, wz) => page.evaluate(([wx, wy, wz]) => {
    const c = { r: 26, theta: -0.55, phi: 0.42, target: [0, 4.5, 0] };
    const vsub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
    const vdot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
    const vcross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
    const vnorm = a => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
    const ch = Math.cos(c.phi);
    const eye = [c.target[0] + c.r * ch * Math.sin(c.theta), c.target[1] + c.r * Math.sin(c.phi),
                 c.target[2] + c.r * ch * Math.cos(c.theta)];
    const cv = document.getElementById('gl'); const b = cv.getBoundingClientRect();
    const tanF = Math.tan(45 * Math.PI / 360);
    const fwd = vnorm(vsub(c.target, eye));
    const right = vnorm(vcross(fwd, [0, 1, 0])); const up = vcross(right, fwd);
    const d = vsub([wx, wy, wz], eye); const a = vdot(d, fwd);
    const ndcX = (vdot(d, right) / a) / (tanF * (cv.width / cv.height));
    const ndcY = (vdot(d, up) / a) / tanF;
    return { x: b.left + (ndcX + 1) / 2 * b.width, y: b.top + (1 - ndcY) / 2 * b.height };
  }, [wx, wy, wz]);

  await page.goto('http://127.0.0.1:8206/?debug=1', { waitUntil: 'load' });
  await sleep(2000);
  await page.fill('#name-input', 'h7raccept');
  await page.click('#play-btn'); await sleep(1200);
  try { await page.click('#intro-begin', { timeout: 3000 }); } catch (e) {}
  await sleep(800);

  // ---------- (b): L1, L2, L3 on real input; distinct sentences ----------
  const passVerdict = async (capMs) => {
    for (let k = 0; k < capMs / 400; k++) {
      const v = await verdict();
      if (/^PASSED/.test(v)) return v;
      await sleep(400);
    }
    return null;
  };
  const playPressureLesson = async () => {
    await page.keyboard.down(' '); await sleep(900);
    await page.keyboard.up(' ');
  };
  R.b = {};
  // L1 wake_the_cell (default 20000 N)
  await playPressureLesson();
  R.b.L1 = { verdict: await passVerdict(25000), judge: await judge() };
  await page.keyboard.press(']'); await sleep(1500);   // L2 the_gentle_hand
  // force down to 6000 via the page's own '-' rail (20000 -> 6000, 7 steps)
  for (let i = 0; i < 7; i++) { await page.keyboard.press('-'); await sleep(60); }
  R.b.L2force = await page.evaluate(() =>
    document.getElementById('force-label').textContent);
  await playPressureLesson();
  R.b.L2 = { verdict: await passVerdict(25000), judge: await judge() };
  await page.keyboard.press(']'); await sleep(1500);   // L3 the_healing
  await playPressureLesson();
  R.b.L3 = { verdict: await passVerdict(25000), judge: await judge() };
  const vs = [R.b.L1.verdict, R.b.L2.verdict, R.b.L3.verdict];
  R.b.allPassed = vs.every(v => v && v.startsWith('PASSED'));
  R.b.distinct = new Set(vs).size === 3;
  R.b.CLEAN = R.b.allPassed && R.b.distinct;
  console.log('L1:', JSON.stringify(R.b.L1.verdict));
  console.log('L2:', JSON.stringify(R.b.L2.verdict), 'force label:', R.b.L2force);
  console.log('L3:', JSON.stringify(R.b.L3.verdict));
  console.log('(b) =>', R.b.CLEAN ? '3/3 REAL PASSES, DISTINCT SENTENCES' : 'FAIL');

  // ---------- (e): canvas click sounds the part clicked -------------------
  await page.evaluate(() => {
    const S = window.ChimeraSound;
    S.__pressArgs = [];
    const orig = S.press;
    S.press = function (force, region) {
      S.__pressArgs.push({ force, region });
      return orig.apply(S, arguments);
    };
  });
  const waitCalm = async () => {
    for (let k = 0; k < 25; k++) {
      const ps = await page.evaluate(() => fetch('/api/state').then(r => r.json()));
      if (ps.cells.every(c => Math.abs(Number(c.P) || 0) < 1000)) return true;
      await sleep(600);
    }
    return false;
  };
  await waitCalm();
  // the foot (world y ~0.18) and the torso (world y ~4.5)
  const footPx = await aimAt(0.46, 0.18, 0.3);
  await page.mouse.click(footPx.x, footPx.y);
  await sleep(1400);                       // tap press lands + pulse runs
  const footArgs = await page.evaluate(() => window.ChimeraSound.__pressArgs.slice());
  await waitCalm();
  const torsoPx = await aimAt(0, 4.5, 0.3);
  await page.mouse.click(torsoPx.x, torsoPx.y);
  await sleep(1400);
  const torsoArgs = await page.evaluate(() => window.ChimeraSound.__pressArgs.slice());
  const bandName = y => y < 0.338 ? 'foot' : y < 1.903 ? 'shin' :
    y < 3.415 ? 'thigh' : 'body';
  const fHit = footArgs.length && footArgs[0].region;
  const tHit = torsoArgs.length && torsoArgs[0].region;
  R.e = {
    footClickArgs: footArgs, torsoClickArgs: torsoArgs,
    footHintIsPoint: Array.isArray(fHit), torsoHintIsPoint: Array.isArray(tHit),
    footHitY: Array.isArray(fHit) ? fHit[1] : null,
    torsoHitY: Array.isArray(tHit) ? tHit[1] : null,
    footRegion: Array.isArray(fHit) ? bandName(fHit[1]) : String(fHit),
    torsoRegion: Array.isArray(tHit) ? bandName(tHit[1]) : String(tHit),
    consoleErrors: errs.length
  };
  R.e.CLEAN = R.e.footHintIsPoint && R.e.torsoHintIsPoint &&
    R.e.footRegion === 'foot' && R.e.torsoRegion === 'body';
  console.log('foot click hint:', JSON.stringify(fHit), '-> region', R.e.footRegion);
  console.log('torso click hint:', JSON.stringify(tHit), '-> region', R.e.torsoRegion);
  console.log('(e) =>', R.e.CLEAN ? 'CLICK SOUNDS THE PART (was: always body)' : 'FAIL');
  console.log('console errors:', errs.length);
  R.consoleErrors = errs.slice(0, 8);
  fs.writeFileSync(__dirname + '/accept_h7r_b_e.json', JSON.stringify(R, null, 1));
  await browser.close();
})().catch(e => { console.error('PROBE FAILED:', e); process.exit(1); });
