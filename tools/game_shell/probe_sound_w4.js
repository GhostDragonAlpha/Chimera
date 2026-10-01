/* probe_sound_w4.js -- W4 SOUND SMOKE TEST, headless.
   Verifies the sound wiring cannot break gameplay, three ways:
   1. MAIN LOAD (sound.js served): the page boots, ZERO console errors,
      NO AudioContext exists at load (lazy), the PLAY click (a user
      gesture) constructs exactly the first one, every ChimeraSound
      method is callable without throwing (region hints included), and
      a scripted SPACE press still holds the touch (judge line
      holding=true, torso pressure rises) -- sound did not break play.
   2. BLOCKED LOAD (sound.js request fails): the page still boots and
      the SPACE press still works, silently -- window.ChimeraSound is
      undefined and snd() no-ops (zero uncaught page errors).
   Evidence JSON -> the path in OUT below (override: argv[3]).

   Run: node tools/game_shell/probe_sound_w4.js [url] [outJson] */
const path = require('path');
const fs = require('fs');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));

const URL_ = process.argv[2] || 'http://127.0.0.1:8206';
const OUT = process.argv[3] ||
  'E:/ChimeraWork/slot-01/docs/evidence/agent_fleet/SHIP/R4_TEN_WALK/sound_smoke.json';
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const result = { url: URL_, at: new Date().toISOString(), main: {}, blocked: {} };

  // ---------- run 1: the real page ----------
  {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    await ctx.addInitScript(() => {
      window.__acCreated = 0;
      const Orig = window.AudioContext;
      if (Orig) {
        window.AudioContext = class extends Orig {
          constructor(...a) { super(...a); window.__acCreated++; }
        };
      }
    });
    const page = await ctx.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push('pageerror: ' + e.message));
    page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });

    await page.goto(URL_, { waitUntil: 'load' });
    await sleep(2500);
    result.main.booted = await page.isVisible('#screen-start');
    result.main.audioContextsAtLoad = await page.evaluate(() => window.__acCreated);
    await page.screenshot({ path: OUT.replace(/\.json$/, '') + '_boot.png' });

    // the gesture: PLAY, then the intro's begin
    await page.fill('#name-input', 'smoke');
    await page.click('#play-btn');
    await sleep(1500);
    try { await page.click('#intro-begin', { timeout: 4000 }); } catch (e) {}
    await sleep(800);
    result.main.audioContextsAfterGesture = await page.evaluate(() => window.__acCreated);
    result.main.playScreenOn = await page.isVisible('#screen-play');

    // every sound method must be callable WITHOUT throwing (an evaluate
    // rejection IS a throw) -- region hints: world point, name, index
    result.main.allMethodsCallClean =
      await page.evaluate(() => {
        const S = window.ChimeraSound;
        if (!S) return 'ChimeraSound MISSING';
        S.init();
        S.ambient(true);
        S.press(20000, [0.0, 4.5, 0.35]);   // world point -> band match
        S.press(40000, 'shin');             // named region retarget
        S.press(40000, 3);                  // cell-index retarget
        S.press(6000);                      // no hint = keep region
        S.wakeWhoosh();
        S.healShimmer();
        S.cellWake();
        S.passed();
        S.saved();
        S.pressEnd();
        S.ambient(false);
        return true;
      });

    // the scripted SPACE press must still WORK (sound must not break play)
    await sleep(500);
    await page.keyboard.down(' ');
    await sleep(1200);
    const judge = await page.evaluate(() =>
      (document.getElementById('judge-debug') || {}).textContent || '');
    result.main.judgeLineMidPress = judge.trim();
    result.main.pressHolds = /holding=true/.test(judge);
    const st = await page.evaluate(() =>
      fetch('/api/state').then(r => r.json()));
    result.main.torsoPaDuringPress = Math.round(Number((st.cells || [])[1] && st.cells[1].P) || 0);
    result.main.pressMovedPhysics = result.main.torsoPaDuringPress > 0;
    await page.keyboard.up(' ');
    await page.keyboard.press('Escape');

    result.main.consoleErrors = errors;
    result.main.zeroConsoleErrors = errors.length === 0;
    await ctx.close();
  }

  // ---------- run 2: sound.js fails to load -> silent but alive ----------
  {
    const ctx2 = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    await ctx2.route('**/sound.js', r => r.abort());
    const page2 = await ctx2.newPage();
    const errors2 = [];
    page2.on('pageerror', e => errors2.push('pageerror: ' + e.message));
    await page2.goto(URL_, { waitUntil: 'load' });
    await sleep(2000);
    result.blocked.booted = await page2.isVisible('#screen-start');
    await page2.fill('#name-input', 'smoke');
    await page2.click('#play-btn');
    await sleep(1500);
    try { await page2.click('#intro-begin', { timeout: 4000 }); } catch (e) {}
    await sleep(800);
    result.blocked.chimeraSoundAbsent =
      await page2.evaluate(() => window.ChimeraSound === undefined);
    await page2.keyboard.down(' ');
    await sleep(1200);
    const judge2 = await page2.evaluate(() =>
      (document.getElementById('judge-debug') || {}).textContent || '');
    result.blocked.pressHolds = /holding=true/.test(judge2);
    await page2.keyboard.up(' ');
    await page2.keyboard.press('Escape');
    result.blocked.uncaughtPageErrors = errors2;
    result.blocked.zeroUncaughtErrors = errors2.length === 0;
    await ctx2.close();
  }

  await browser.close();
  result.pass =
    result.main.booted && result.main.audioContextsAtLoad === 0 &&
    result.main.audioContextsAfterGesture >= 1 && result.main.playScreenOn &&
    result.main.allMethodsCallClean === true && result.main.pressHolds &&
    result.main.pressMovedPhysics && result.main.zeroConsoleErrors &&
    result.blocked.booted && result.blocked.chimeraSoundAbsent &&
    result.blocked.pressHolds && result.blocked.zeroUncaughtErrors;
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(result, null, 1));
  console.log(JSON.stringify(result, null, 1));
  console.log('SOUND SMOKE: ' + (result.pass ? 'PASS' : 'FAIL') + ' -> ' + OUT);
  process.exit(result.pass ? 0 : 1);
})().catch(e => { console.error('SMOKE FAILED:', e.message); process.exit(1); });
