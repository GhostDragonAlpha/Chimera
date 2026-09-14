/* walk_lessons.js -- THE R4 COMPLETION WALK, headless.
   A private Chrome drives the game page the way a player would:
   enters a name, walks all five lessons (touch/pose by the page's own
   keyboard rail), saves, and reports the progress file.
   Zero windows, zero interference with the operator's desktop.
   While walking it polls /api/state itself and logs each lesson's peak
   cell pressures next to the lesson's threshold, so a refusal to pass
   is a NUMBER, not a shrug.
   Run: node tools/game_shell/walk_lessons.js [url] */
const path = require('path');
const fs = require('fs');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));

const URL_ = process.argv[2] || 'http://127.0.0.1:8206';
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });
  page.on('pageerror', e => console.log('PAGE ERROR:', e.message));
  const shots = 'C:/Users/allen/Desktop/CHIMERA_PROOF/R4_WALK';
  fs.mkdirSync(shots, { recursive: true });

  await page.goto(URL_, { waitUntil: 'load' });
  await sleep(2500);                                   // world attach (topology+verts)
  await page.screenshot({ path: shots + '/walk0_start.png' });

  // sign in and enter play
  await page.fill('#name-input', 'Alan');
  await page.click('#play-btn');
  await sleep(2000);

  const state = () => page.evaluate(() => fetch('/api/state').then(r => r.json()));
  const judgeLine = async () => page.evaluate(() =>
    (document.getElementById('judge-debug') || {}).textContent || '');
  const lesson = async () => {
    const line = await judgeLine();                    // "judge: id phase=.. goalMet=.. passed=.. .."
    const m = String(line || '').match(/judge: (\S+) phase=(\S+) goalMet=(\S+) passed=(\S+)/);
    return { id: m ? m[1] : '?', phase: m ? m[2] : '?',
             goalMet: m ? m[3] === 'true' : false, passed: m ? m[4] === 'true' : false,
             line };
  };

  // the lesson pack, for honest threshold-vs-measured reporting
  const pack = await page.evaluate(() => fetch('/lessons.json').then(r => r.json()));
  const goalOf = id => ((pack.lessons || []).find(l => l.id === id) || {}).goal || {};

  // background sampler: peak Pa per cell since the last resetPeaks()
  let peaks = [], sampling = true;
  (async function sampler() {
    while (sampling) {
      try {
        const s = await state();
        (s.cells || []).forEach((c, i) => {
          peaks[i] = Math.max(peaks[i] || -1e9, Number(c.P) || 0);
        });
      } catch (e) { /* a silent beat is not a verdict */ }
      await sleep(350);
    }
  })();
  const resetPeaks = () => { peaks = []; };
  const peaksLine = () =>
    peaks.map((p, i) => 'cell' + i + '=' + Math.round(p) + ' Pa').join(' ') || 'no cells seen';
  const report = async (tag, extraGoalCheck) => {
    const l = await lesson();
    const g = goalOf(l.id);
    console.log(tag + ' judge: ' + JSON.stringify(
      { id: l.id, phase: l.phase, goalMet: l.goalMet, passed: l.passed }));
    console.log(tag + ' line  : ' + l.line);
    console.log(tag + ' goal  : ' + JSON.stringify(g) +
      (extraGoalCheck || ''));
    console.log(tag + ' peaks : ' + peaksLine());
    return l;
  };

  // THE WAIT IS PHYSICS: after ESC the pressure decays with tau = 0.5 s from
  // whatever peak the press actually reached. The judge passes on the first
  // poll where every |P| < 1000 Pa. So: hold the scripted minimum wait, then
  // keep waiting until the ENGINE itself reports every cell calm, plus one
  // judge poll beat. Never a guess, never a lowered bar.
  const waitCalm = async (minMs, capMs) => {
    const t0 = Date.now();
    let calm = false, last = null;
    while (Date.now() - t0 < capMs) {
      if (Date.now() - t0 >= minMs) {
        try {
          const s = await state();
          const ps = (s.cells || []).map(c => Math.abs(Number(c.P) || 0));
          last = ps;
          if (ps.length && ps.every(p => p < 1000)) { calm = true; break; }
        } catch (e) { /* a silent beat is not a verdict */ }
      }
      await sleep(250);
    }
    console.log('   calm=' + calm + ' after ' + ((Date.now() - t0) / 1000).toFixed(1) +
      's  final |P| Pa: ' + (last || []).map(p => Math.round(p)).join(' '));
    await sleep(1600);                                  // the judge's next poll
  };

  const press = async (ms) => {                       // SPACE down, hold, up
    await page.keyboard.down(' ');
    await sleep(900);                                 // POST + one judge poll
    console.log('   mid-press: ' + await judgeLine()); // touchTarget set + holding == POST ok:true
    await sleep(Math.max(0, ms - 900));
    await page.keyboard.up(' ');
  };
  const key = async (k) => { await page.keyboard.press(k); await sleep(300); };

  // L1 WAKE THE CELL: max force, press the belly, release, heal
  resetPeaks();
  for (let i = 0; i < 15; i++) await key('=');
  await press(2500);
  await page.keyboard.press('Escape');
  await waitCalm(5000, 20000);
  await report('L1');

  // L2 THE GENTLE HAND: force under 8000, press the foot target
  resetPeaks();
  await key(']');
  for (let i = 0; i < 22; i++) await key('-');
  await press(2000);
  await page.keyboard.press('Escape');
  await waitCalm(4500, 20000);
  await report('L2');

  // L3 THE HEALING: force back up, wake any cell, release, wait
  resetPeaks();
  await key(']');
  for (let i = 0; i < 37; i++) await key('=');
  await press(2500);
  await page.keyboard.press('Escape');
  await waitCalm(6000, 20000);
  await report('L3');

  // L4 BEND THE KNEE: the pose button
  resetPeaks();
  await key(']');
  await page.click('#pose-btn');
  await sleep(3000);
  await report('L4');

  // L5 THE WHOLE BODY: two compartments (cycled targets), then release
  resetPeaks();
  await key(']');
  await press(2200);                 // belly target
  await press(2200);                 // cycles to the shin target
  await page.keyboard.press('Escape');
  await waitCalm(5500, 25000);
  await report('L5');

  sampling = false;
  await page.screenshot({ path: shots + '/walk5_end.png' });

  // save + read back
  await page.click('#save-btn');
  await sleep(1200);
  const prog = await page.evaluate(() =>
    fetch('/api/progress?name=Alan').then(r => r.json()));
  console.log('SAVED PROGRESS:', JSON.stringify(prog.lessons ? Object.keys(prog.lessons) : prog));
  fs.writeFileSync(shots + '/progress_Alan.json', JSON.stringify(prog, null, 1));

  const passed = Object.keys(prog.lessons || {}).filter(k => prog.lessons[k].passed);
  console.log('PASSED LESSONS:', passed.length, 'of 5 ->', passed.join(', '));
  await browser.close();
  process.exit(passed.length === 5 ? 0 : 1);
})().catch(e => { console.error('WALK FAILED:', e.message); process.exit(1); });
