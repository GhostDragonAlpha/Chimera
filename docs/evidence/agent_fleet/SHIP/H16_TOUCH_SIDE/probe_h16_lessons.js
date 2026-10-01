/* probe_h16_lessons.js -- H16 lessons regression, self-play through the
   page like a player, with the MOUSE (the path H16 changed). Plays
   lessons 1-3 (wake_the_cell / the_gentle_hand / the_healing) on a fresh
   name: snaps each lesson's touch target to the streamed mesh, projects
   it through the page's own camera, and CLICKS it with a real pointer
   press (the fixed pickWorld -> {"hit",force_n} path). the_gentle_hand
   presses at 6000 N -- under its max_force_n 8000 judge cap -- set
   through the page's own '-' slider rail. Touch traffic (the posted hit
   and force) is captured by patching window.fetch. PASS = the lesson's
   progress dot latches 'passed' in the page's own E4 strip.
   Exit 0 iff all three lessons pass AND every gentle-hand press posted
   force_n <= 8000.
   Run: node probe_h16_lessons.js [baseURL] */
const path = require('path');
const fs = require('fs');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));

const BASE = process.argv[2] || 'http://127.0.0.1:8206';
const URL_ = BASE + '/?debug=1';
const OUT = path.join(__dirname, 'lessons_selfplay.json');
const NAME = 'h16selfplay';
const sleep = ms => new Promise(r => setTimeout(r, ms));

const LESSONS = require('E:/ChimeraWork/slot-01/tools/game_shell/lessons.json');
const pack = Array.isArray(LESSONS) ? LESSONS : (LESSONS.lessons || []);
const THREE = ['wake_the_cell', 'the_gentle_hand', 'the_healing']
  .map(id => pack.find(l => l.id === id));

const UP = [0, 1, 0];
const sub3 = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot3 = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross3 = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm3 = a => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
function eyeOf(cam) {
  const ch = Math.cos(cam.phi);
  return [cam.target[0] + cam.r * ch * Math.sin(cam.theta),
          cam.target[1] + cam.r * Math.sin(cam.phi),
          cam.target[2] + cam.r * ch * Math.cos(cam.theta)];
}
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
async function fetchVerts() {
  const res = await fetch(BASE + '/api/verts');
  const vb = Buffer.from(await res.arrayBuffer());
  const n = vb.readUInt32LE(0);
  const pos = new Float64Array(n * 3);
  for (let i = 0; i < n; i++) {
    pos[i * 3] = vb.readFloatLE(4 + i * 36);
    pos[i * 3 + 1] = vb.readFloatLE(4 + i * 36 + 4);
    pos[i * 3 + 2] = vb.readFloatLE(4 + i * 36 + 8);
  }
  return pos;
}
function snap(pos, pt) {
  let bd = Infinity, bv = pt;
  for (let i = 0; i < pos.length; i += 3) {
    const dx = pos[i] - pt[0], dy = pos[i + 1] - pt[1], dz = pos[i + 2] - pt[2];
    const d2 = dx * dx + dy * dy + dz * dz;
    if (d2 < bd) { bd = d2; bv = [pos[i], pos[i + 1], pos[i + 2]]; }
  }
  return bv;
}

const CAM = { r: 26, theta: -0.55, phi: 0.42, target: [0, 4.5, 0], fov: 45 * Math.PI / 180 };

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
  try { await page.click('#intro-begin', { timeout: 5000 }); } catch (e) {}
  for (let i = 0; i < 60; i++) {
    try { if ((await fetch(BASE + '/api/topology')).ok) break; } catch (e) {}
    await sleep(1000);
  }
  const pos = await fetchVerts();
  await sleep(3000);
  await page.evaluate(() => {
    window.__touchLog = [];
    const of = window.fetch.bind(window);
    window.fetch = function (url, opts) {
      const u = (typeof url === 'string') ? url : (url && url.url) || '';
      if (u.indexOf('/api/touch_hit') < 0) return of.apply(null, arguments);
      let req = null;
      try { req = opts && opts.body ? JSON.parse(opts.body) : null; } catch (e) {}
      const t0 = Date.now();
      return of.apply(null, arguments).then(async res => {
        let body = null;
        try { body = await res.clone().json(); } catch (e) {}
        window.__touchLog.push({ status: res.status, req, res: body, t: t0 });
        return res;
      });
    };
  });
  const rect = await page.evaluate(() => {
    const r = document.getElementById('gl').getBoundingClientRect();
    return { left: r.left, top: r.top, width: r.width, height: r.height };
  });
  const eye = eyeOf(CAM);

  const rows = [];
  for (let li = 0; li < THREE.length; li++) {
    const l = THREE[li];
    const targetSrc = (l.touch_targets && l.touch_targets[0]) || l.touch_target;
    const snapped = snap(pos, targetSrc);
    const pj = project(snapped, CAM, eye, rect);
    const owner = await page.evaluate(pt => {
      const el = document.elementFromPoint(pt.x, pt.y);
      return el ? (el.id || el.tagName) : 'none';
    }, { x: pj.x, y: pj.y });
    // the force: lesson 2 (index 1) rides at 6000 N -- under the 8000 cap.
    // The slider starts at 20000; '-' steps down 2000 per press.
    const wantForce = li === 1 ? 6000 : 20000;
    let forceNow = await page.evaluate(() => +document.getElementById('force').value);
    while (forceNow > wantForce) { await page.keyboard.press('-'); forceNow -= 2000; await sleep(60); }
    while (forceNow < wantForce) { await page.keyboard.press('='); forceNow += 2000; await sleep(60); }
    const t0 = Date.now();
    let passed = false, goalMet = false;
    // up to 3 press cycles: hold until the goal is met (the verdict says
    // so), LET GO -- the pass latches on the release -- then poll the dot
    for (let cyc = 0; cyc < 3 && !passed; cyc++) {
      await page.mouse.move(pj.x, pj.y); await sleep(150);
      await page.mouse.down();
      const tHold0 = Date.now();
      while (Date.now() - tHold0 < 8000) {
        const v = await page.evaluate(() => {
          const el = document.getElementById('verdict');
          return el ? el.textContent : '';
        });
        if (/goal is met/i.test(v)) { goalMet = true; break; }
        await sleep(250);
      }
      await page.mouse.up();
      const tRel0 = Date.now();
      while (Date.now() - tRel0 < 10000) {
        passed = await page.evaluate(id => {
          const d = document.getElementById('dot-' + id);
          return !!d && d.classList.contains('passed');
        }, l.id);
        if (passed) break;
        await sleep(300);
      }
    }
    await sleep(400);
    const verdict = await page.evaluate(() => {
      const v = document.getElementById('verdict');
      return v ? v.textContent : '';
    });
    const traffic = await page.evaluate(t0 =>
      window.__touchLog.filter(e => e.t >= t0), t0);
    const maxForcePosted = traffic.reduce((m, e) =>
      Math.max(m, e.req && Number.isFinite(e.req.force_n) ? e.req.force_n : 0), 0);
    rows.push({
      lesson: l.id, index: li + 1,
      aimPixel: { x: +pj.x.toFixed(1), y: +pj.y.toFixed(1) }, occluder: owner,
      targetSnapped: snapped.map(v => +v.toFixed(3)),
      forceSlider: wantForce, maxForcePosted,
      presses: traffic.length, pressOk: traffic.every(e => e.res && e.res.ok === true),
      goalMet, passed, verdict: (verdict || '').slice(0, 120)
    });
    console.log((li + 1) + '. ' + l.id + ': clicks=' + traffic.length +
      ' force<=' + maxForcePosted + ' N  passed=' + passed +
      '  verdict="' + (verdict || '').slice(0, 60) + '"');
    if (li < THREE.length - 1) { await page.keyboard.press(']'); await sleep(1200); }
  }

  const gentle = rows.find(r => r.lesson === 'the_gentle_hand');
  const summary = {
    base: BASE, playerName: NAME,
    lessonsPassed: rows.filter(r => r.passed).length + '/3',
    gentleUnder8000: !!gentle && gentle.maxForcePosted > 0 && gentle.maxForcePosted <= 8000,
    expectationMet: rows.every(r => r.passed) &&
      gentle && gentle.maxForcePosted > 0 && gentle.maxForcePosted <= 8000,
    pageErrors
  };
  fs.writeFileSync(OUT, JSON.stringify({ summary, rows }, null, 1));
  console.log('\nSUMMARY: lessons ' + summary.lessonsPassed +
    ', gentle-hand posted <=' + (gentle ? gentle.maxForcePosted : '?') +
    ' N (cap 8000), expectationMet=' + summary.expectationMet +
    ', pageErrors=' + pageErrors.length);
  console.log('written: ' + OUT);
  await browser.close();
  process.exit(summary.expectationMet ? 0 : 2);
})().catch(e => { console.error('PROBE FAILED:', e); process.exit(1); });
