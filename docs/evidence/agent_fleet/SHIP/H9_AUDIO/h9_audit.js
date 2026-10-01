/* h9_audit.js -- H9 AUDIO-AUDIT live run (READ-ONLY lane).
   Loads the LIVE page on 127.0.0.1:8206 headless (channel: chrome), but
   serves an INSTRUMENTED LOCAL COPY of sound.js via Playwright route
   interception. The served file is never edited. The copy wraps every
   public ChimeraSound method: each call is logged (method, ctx state,
   args) plus post-call internal state (is a held press voice alive,
   which region it carries) -- reachable because the wrapper sits inside
   the same IIFE scope as the module's privates.

   Run: node h9_audit.js
   Out: h9_live_audit.json, h9_broken_synth.json, sound_instrumented.js,
        01_boot.png, 02_play.png, 03_after_release.png, 04_lesson_switch.png */
const path = require('path');
const fs = require('fs');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));

const URL_ = 'http://127.0.0.1:8206';
const OUT_DIR = 'E:/ChimeraWork/slot-01/docs/evidence/agent_fleet/SHIP/H9_AUDIO';
const sleep = ms => new Promise(r => setTimeout(r, ms));

// The harness REPLACES the module's export object IN PLACE (inside the
// IIFE, where ctx / pressV / the synth functions are in scope). Logging
// only -- behavior identical. Injected at the exact `window.ChimeraSound
// = {...};` export block of the served file.
const HARNESS = `
  window.__SNDLOG = [];
  window.__SNDSTATE = { pressVActive: false, region: null };
  function __safe(v) {
    if (v === undefined) return 'undefined';
    if (v === null) return null;
    if (typeof v === 'number') return Math.round(v * 1000) / 1000;
    if (typeof v === 'string') return v;
    if (v && typeof v.length === 'number')
      return Array.prototype.slice.call(v, 0, 3)
        .map(function (x) { return Math.round(Number(x) * 1000) / 1000; });
    return String(v);
  }
  function __wrap(name, fn) {
    return function () {
      var args = Array.prototype.slice.call(arguments), out;
      try { out = fn.apply(null, args); }
      finally {
        var rec = { m: name, t: Date.now(),
                    ctx: ctx ? ctx.state : 'no-ctx',
                    args: args.map(__safe) };
        if (name === 'press') {
          rec.voiceActiveAfter = !!pressV;
          rec.heldRegion = pressV && pressV.region ? pressV.region.name : null;
          window.__SNDSTATE.pressVActive = !!pressV;
          window.__SNDSTATE.region = rec.heldRegion;
        }
        if (name === 'pressEnd') {
          rec.voiceActiveAfter = !!pressV;
          window.__SNDSTATE.pressVActive = !!pressV;
        }
        window.__SNDLOG.push(rec);
      }
      return out;
    };
  }
  window.ChimeraSound = {
    init: __wrap('init', init),
    ambient: __wrap('ambient', ambient),
    press: __wrap('press', press),
    pressEnd: __wrap('pressEnd', pressEnd),
    wakeWhoosh: __wrap('wakeWhoosh', wakeWhoosh),
    healShimmer: __wrap('healShimmer', healShimmer),
    cellWake: __wrap('cellWake', cellWake),
    passed: __wrap('passed', passed),
    saved: __wrap('saved', saved)
  };
`;
function inject(body) {
  const re = /window\.ChimeraSound = \{[\s\S]*?\};/;
  if (!re.test(body)) throw new Error('H9: export block not found in served sound.js');
  return body.replace(re, HARNESS.trim());
}

const AC_COUNTER = `
  window.__acCreated = 0;
  window.__acStates = [];
  const __Orig = window.AudioContext;
  if (__Orig) {
    window.AudioContext = class extends __Orig {
      constructor(...a) { super(...a); window.__acCreated++; window.__acStates.push('created'); }
      get state() { const s = super.state; return s; }
    };
  }
`;

async function sampleJudge(page) {
  return page.evaluate(() =>
    ((document.getElementById('judge-debug') || {}).textContent || '').trim());
}

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const result = { at: new Date().toISOString(), url: URL_, main: {}, broken: {} };

  // ---------------- context A: the instrumented main run ----------------
  {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    await ctx.addInitScript(AC_COUNTER);
    const consoleErrs = [];
    const consoleAll = [];
    let servedBody = null;
    await ctx.route('**/sound.js', async route => {
      const resp = await route.fetch();
      servedBody = await resp.text();
      await route.fulfill({ status: 200, contentType: 'application/javascript', body: inject(servedBody) });
    });
    const page = await ctx.newPage();
    page.on('pageerror', e => consoleErrs.push('pageerror: ' + e.message));
    page.on('console', m => { consoleAll.push(m.type() + ': ' + m.text()); if (m.type() === 'error') consoleErrs.push('console: ' + m.text()); });

    // 1) boot
    await page.goto(URL_, { waitUntil: 'load' });
    await sleep(2500);
    result.main.acAtLoad = await page.evaluate(() => window.__acCreated);
    result.main.booted = await page.isVisible('#screen-start');
    await page.screenshot({ path: OUT_DIR + '/01_boot.png' });

    // 2) the PLAY gesture
    await page.fill('#name-input', 'h9-audit');
    await page.click('#play-btn');
    await sleep(1500);
    try { await page.click('#intro-begin', { timeout: 4000 }); } catch (e) {}
    await sleep(4500);   // let meshPos (vertex snap source) + lessons land
    result.main.acAfterGesture = await page.evaluate(() => window.__acCreated);
    result.main.playScreenOn = await page.isVisible('#screen-play');
    result.main.gestureLog = await page.evaluate(() => window.__SNDLOG);
    result.main.worldCellsAtStart = await page.evaluate(() =>
      fetch('/api/state').then(r => r.json()).then(s => (s.cells || []).map(c => Math.round(Number(c.P) || 0))));
    result.main.judgeAtStart = await sampleJudge(page);
    await page.screenshot({ path: OUT_DIR + '/02_play.png' });

    // 3) press cycle 1: SPACE down, hold through ~3 polls, force change mid-hold
    const timeline = [];
    const t0 = Date.now();
    const mark = async lbl => timeline.push({ t: Date.now() - t0, lbl, judge: await sampleJudge(page) });
    await mark('before-space');
    await page.keyboard.down(' ');
    await sleep(700);
    await mark('space+700ms');
    // mid-hold force follow: 20000 -> 34000 via the slider's own event
    await page.evaluate(() => {
      const f = document.getElementById('force');
      f.value = 34000;
      f.dispatchEvent(new Event('input'));
    });
    await sleep(1100);
    await mark('hold+1.8s');
    result.main.stateDuringHold = await page.evaluate(() =>
      fetch('/api/state').then(r => r.json()).then(s => (s.cells || []).map(c => Math.round(Number(c.P) || 0))));
    result.main.whooshDuringHold = await page.evaluate(() =>
      window.__SNDLOG.filter(x => x.m === 'wakeWhoosh').length);
    result.main.cellWakeDuringHold = await page.evaluate(() =>
      window.__SNDLOG.filter(x => x.m === 'cellWake').length);

    // 4) STILL HOLDING: switch to lesson 3 (the_healing, same torso target).
    //    Lesson 1 latched by now (then_release -> phase=release), so the cell
    //    is still awake. The fresh per-lesson memo must re-whoosh on the next
    //    poll if the memo is lesson-scoped rather than world-scoped.
    const whooshBefore = await page.evaluate(() =>
      window.__SNDLOG.filter(x => x.m === 'wakeWhoosh').length);
    await page.keyboard.press('3');
    await sleep(2600);   // ~3 polls
    const whooshAfter = await page.evaluate(() =>
      window.__SNDLOG.filter(x => x.m === 'wakeWhoosh').length);
    result.main.lessonSwitch = { whooshBefore, whooshAfter, spuriousRefire: whooshAfter > whooshBefore };
    result.main.judgeAfterSwitch = await sampleJudge(page);
    await page.screenshot({ path: OUT_DIR + '/04_lesson_switch.png' });

    // 5) release through the page's own rail. NOTE: the page has NO keyup
    //    handler for space; ESC is the keyboard release (clearTouch).
    await page.keyboard.up(' ');
    await sleep(300);
    await page.keyboard.press('Escape');
    await sleep(800);
    await mark('after-escape');
    result.main.stateAfterRelease1 = await page.evaluate(() => window.__SNDSTATE);
    result.main.pressEndEverCalled = await page.evaluate(() =>
      window.__SNDLOG.some(x => x.m === 'pressEnd'));
    await page.screenshot({ path: OUT_DIR + '/03_after_release.png' });

    // 6) rest, then watch the release-phase calm -- does healShimmer mark it?
    //    (lesson 3, the_healing, is then_release too)
    await page.keyboard.press('r');   // rest (clearTouch + resetPose)
    const shimmerDeadline = Date.now() + 10000;
    while (Date.now() < shimmerDeadline) {
      const passed = await page.evaluate(() =>
        (window.__SNDLOG.some(x => x.m === 'healShimmer')));
      if (passed) break;
      await sleep(700);
    }
    result.main.shimmerFired = await page.evaluate(() =>
      window.__SNDLOG.some(x => x.m === 'healShimmer'));
    result.main.judgeAtEnd = await sampleJudge(page);
    result.main.cellsAtEnd = await page.evaluate(() =>
      fetch('/api/state').then(r => r.json()).then(s => (s.cells || []).map(c => Math.round(Number(c.P) || 0))));

    // 7) press cycle 2 on the settled world: does a SECOND press still fire
    //    the page's press audio, and does the world answer it?
    const pressCountBefore = await page.evaluate(() =>
      window.__SNDLOG.filter(x => x.m === 'press').length);
    await page.keyboard.down(' ');
    await sleep(900);
    result.main.judgeDuringCycle2 = await sampleJudge(page);
    await page.keyboard.up(' ');
    await page.keyboard.press('Escape');
    await sleep(600);
    result.main.pressCycle2 = {
      audioFired: (await page.evaluate(() =>
        window.__SNDLOG.filter(x => x.m === 'press').length)) > pressCountBefore,
      judge: await sampleJudge(page)
    };

    result.main.log = await page.evaluate(() => window.__SNDLOG);
    result.main.acFinal = await page.evaluate(() => window.__acCreated);
    result.main.timeline = timeline;
    result.main.consoleErrors = consoleErrs;
    result.main.consoleTail = consoleAll.slice(-25);
    result.main.servedMatchesWorktree = servedBody === fs.readFileSync('E:/ChimeraWork/slot-01/tools/game_shell/sound.js', 'utf8');
    fs.writeFileSync(OUT_DIR + '/sound_instrumented.js', inject(servedBody));
    result.main.harnessAttached = await page.evaluate(() =>
      !!(window.__SNDLOG && window.__SNDLOG.length));
    await ctx.close();
  }

  // ---------------- context B: a synth that THROWS -- is it visible? --------
  {
    const ctx2 = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    await ctx2.addInitScript(AC_COUNTER);
    await ctx2.route('**/sound.js', async route => {
      const resp = await route.fetch();
      await route.fulfill({ status: 200, contentType: 'application/javascript', body: await resp.text() });
    });
    const page2 = await ctx2.newPage();
    const errs2 = [];
    page2.on('pageerror', e => errs2.push('pageerror: ' + e.message));
    page2.on('console', m => { if (m.type() === 'error') errs2.push('console: ' + m.text()); });
    await page2.goto(URL_, { waitUntil: 'load' });
    await sleep(2000);
    await page2.fill('#name-input', 'h9-broken');
    await page2.click('#play-btn');
    await sleep(1500);
    try { await page2.click('#intro-begin', { timeout: 4000 }); } catch (e) {}
    await sleep(1000);
    // break the synth AFTER load: press() now always throws
    await page2.evaluate(() => {
      window.__SNDLOG = window.__SNDLOG || [];
      const orig = window.ChimeraSound.press;
      window.ChimeraSound.press = function () {
        window.__SNDLOG.push({ m: 'press-THREW', t: Date.now() });
        throw new Error('H9: synth exploded');
      };
    });
    await page2.keyboard.down(' ');
    await sleep(900);
    result.broken.judgeLine = await page2.evaluate(() =>
      ((document.getElementById('judge-debug') || {}).textContent || '').trim());
    result.broken.pressCalledAndThrew = await page2.evaluate(() =>
      (window.__SNDLOG || []).some(x => x.m === 'press-THREW'));
    result.broken.pressHoldsAnyway = /holding=true/.test(result.broken.judgeLine);
    await page2.keyboard.up(' ');
    await page2.keyboard.press('Escape');
    result.broken.consoleOrPageErrors = errs2;
    result.broken.failureInvisible = errs2.length === 0 && result.broken.pressHoldsAnyway;
    await ctx2.close();
  }

  await browser.close();

  // ---------------- assertions --------------------------------------------
  const m = result.main;
  const pressCalls = m.log ? m.log.filter(x => x.m === 'press') : [];
  result.verdict = {
    acZeroAtLoad: m.acAtLoad === 0,
    acExactlyOneAfterGesture: m.acAfterGesture === 1,
    acStillOneAtEnd: m.acFinal === 1,
    pressFiredOnSpace: pressCalls.length >= 2,
    pressCarriedWorldPoint: pressCalls.some(x => Array.isArray(x.args[1]) && x.args[1].length === 3),
    forceFollowFired: pressCalls.filter(x => x.args.length === 1).length >= 1,
    heldRegionResolved: pressCalls.some(x => x.heldRegion),
    whooshOncePerCrossing: m.whooshDuringHold <= 1,
    pressEndNeverWired: m.pressEndEverCalled === false,
    pressVoiceStillActiveAfterRelease: m.stateAfterRelease1 ? m.stateAfterRelease1.pressVActive === true : null,
    zeroConsoleErrors: (m.consoleErrors || []).length === 0,
    servedMatchesWorktree: m.servedMatchesWorktree
  };
  fs.writeFileSync(OUT_DIR + '/h9_live_audit.json', JSON.stringify(result, null, 1));
  console.log(JSON.stringify({ verdict: result.verdict, main: {
    acAtLoad: m.acAtLoad, acAfterGesture: m.acAfterGesture, acFinal: m.acFinal,
    pressCalls: pressCalls.length,
    whooshDuringHold: m.whooshDuringHold, cellWakeDuringHold: m.cellWakeDuringHold,
    lessonSwitch: m.lessonSwitch, shimmerFired: m.shimmerFired,
    pressEndEverCalled: m.pressEndEverCalled,
    stateAfterRelease1: m.stateAfterRelease1,
    cellsAtEnd: m.cellsAtEnd,
    consoleErrors: m.consoleErrors,
    servedMatchesWorktree: m.servedMatchesWorktree,
    judgeAtStart: m.judgeAtStart, judgeAtEnd: m.judgeAtEnd,
    broken: result.broken } }, null, 1));
})().catch(e => { console.error('H9 AUDIT FAILED:', e); process.exit(1); });
