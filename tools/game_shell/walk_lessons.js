/* walk_lessons.js -- THE R4 COMPLETION WALK, headless.
   A private Chrome drives the game page the way a player would:
   enters a name, walks all five lessons (touch/pose by the page's own
   keyboard rail), saves, and reports the progress file.
   Zero windows, zero interference with the operator's desktop.
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
  const judgeLine = () => page.evaluate(() =>
    (document.getElementById('judge-debug') || {}).textContent || '');
  const lesson = () => {
    const line = judgeLine();                          // "judge: id phase=.. goalMet=.. passed=.."
    const m = String(line || '').match(/judge: (\S+) phase=(\S+) goalMet=(\S+) passed=(\S+)/);
    return { id: m ? m[1] : '?', phase: m ? m[2] : '?',
             goalMet: m ? m[3] === 'true' : false, passed: m ? m[4] === 'true' : false,
             line };
  };
  const press = async (ms) => {                       // SPACE down, hold, up
    await page.keyboard.down(' ');
    await sleep(ms);
    await page.keyboard.up(' ');
  };
  const key = async (k) => { await page.keyboard.press(k); await sleep(300); };

  // L1 WAKE THE CELL: max force, press the belly, release, heal
  for (let i = 0; i < 15; i++) await key('=');
  await press(2500);
  await page.keyboard.press('Escape');
  await sleep(5000);
  console.log('L1:', JSON.stringify(lesson()));

  // L2 THE GENTLE HAND: force under 8000, press the foot target
  await key(']');
  for (let i = 0; i < 22; i++) await key('-');
  await press(2000);
  await page.keyboard.press('Escape');
  await sleep(4500);
  console.log('L2:', JSON.stringify(lesson()));

  // L3 THE HEALING: force back up, wake any cell, release, wait
  await key(']');
  for (let i = 0; i < 37; i++) await key('=');
  await press(2500);
  await page.keyboard.press('Escape');
  await sleep(6000);
  console.log('L3:', JSON.stringify(lesson()));

  // L4 BEND THE KNEE: the pose button
  await key(']');
  await page.click('#pose-btn');
  await sleep(3000);
  console.log('L4:', JSON.stringify(lesson()));

  // L5 THE WHOLE BODY: two compartments (cycled targets), then release
  await key(']');
  await press(2200);                 // belly target
  await press(2200);                 // cycles to the shin target
  await page.keyboard.press('Escape');
  await sleep(5500);
  console.log('L5:', JSON.stringify(lesson()));

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
