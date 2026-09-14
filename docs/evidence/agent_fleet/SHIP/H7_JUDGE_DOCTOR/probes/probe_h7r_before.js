/* probe_h7r_before.js -- H7r BEFORE-fix repro for the six defects H7's tree
   does NOT yet cover (three audit lists). Each section B1..B6 names its
   defect, injects the failure at the PAGE level (route interception or
   synth wrapping only -- the engine sees ordinary traffic), and measures
   the defect live. Run: node probe_h7r_before.js
   B1 H10-1  gravity false-arm: a failed /api/gravity enable still arms the judge
   B2 H10-2  touch_clear is fire-and-forget: a 429'd release is dropped, no retry
   B3 H9-1   pressEnd never called: the press voice never ends on release
   B4 H10-3  showLesson does not await resetPose: the next lesson's window
             opens while the previous lesson's pose is still held
   B5 H9-3   lesson-switch re-whoosh: an already-awake cell whooshes again
   B6 H9-4   snd() failure invisibility: a throwing synth is undiagnosable,
             no counter, no console anything
*/
const path = require('path');
const fs = require('fs');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));
const URL_ = 'http://127.0.0.1:8206/?debug=1';
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const consoleErrors = [];
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  page.on('pageerror', e => consoleErrors.push('pageerror: ' + e.message));
  const R = {};
  const judgeLine = () => page.evaluate(() =>
    (document.getElementById('judge-debug') || {}).textContent || '');
  const verdict = () => page.evaluate(() =>
    (document.getElementById('verdict') || {}).textContent);
  const worldState = () => page.evaluate(() =>
    fetch('/api/state').then(r => r.json()));
  const cells = async () => (await worldState()).cells.map(c => Number(c.P) || 0);
  const wrapSound = method => page.evaluate(m => {
    const S = window.ChimeraSound; if (!S) return false;
    S['__n_' + m] = 0;
    const orig = S[m];
    S[m] = function () { S['__n_' + m]++; return orig.apply(S, arguments); };
    return true;
  }, method);
  const soundCount = method => page.evaluate(m =>
    (window.ChimeraSound || {})['__n_' + m] || 0, method);

  await page.goto(URL_, { waitUntil: 'load' });
  await sleep(2000);
  // world at rest, gravity off (the walker's own convention), fresh name
  await page.evaluate(() => fetch('/api/gravity', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ on: false }) }).then(r => r.json()));
  await page.fill('#name-input', 'h7rprobe');
  await page.click('#play-btn'); await sleep(1200);
  try { await page.click('#intro-begin', { timeout: 3000 }); } catch (e) {}
  await sleep(800);

  // ===== B2 (H10-2): 429'd touch_clear is dropped, engine keeps pressing ==
  {
    let clearCalls = 0;
    await wrapSound('press'); await wrapSound('pressEnd');
    await page.route('**/api/touch_clear', async route => {
      clearCalls++;
      try {
        if (clearCalls === 1) {           // the FIRST release post dies: 429
          return await route.fulfill({ status: 429, contentType: 'application/json',
            body: JSON.stringify({ ok: false, error: 'too many requests' }),
            headers: { 'Retry-After': '1' } });
        }
        const resp = await route.fetch();
        return await route.fulfill({ response: resp });
      } catch (e) { try { await route.abort(); } catch (e2) {} }
    });
    const during = {};
    await page.keyboard.down(' '); await sleep(900);
    during.press = (await worldState());
    await page.keyboard.up(' ');          // -> clearTouch -> first POST 429s
    await sleep(3000);                    // window for any retry that might exist
    const after = (await worldState());
    await page.unroute('**/api/touch_clear');
    // honest clear so the section leaves the world clean
    await page.evaluate(() => fetch('/api/touch_clear', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: '{}' }).then(r => r.json()));
    await sleep(500);
    const healed = (await worldState());
    const f = s => ({ fl: s.force_l, fr: s.force_r });
    R.B2 = { clearCalls, forceDuring: f(during.press),
             forceAfterFailedClear: f(after), forceAfterHonestClear: f(healed) };
    // BEFORE verdict: exactly 1 clear attempt (dropped), engine force channel
    // still engaged after it; AFTER (fix) would retry (>=2) and the world's
    // force returns to 0 without the honest manual clear.
    R.B2.DEFECT_LIVE = clearCalls === 1;
    console.log('B2 touch_clear calls during release:', clearCalls,
      '| engine force during:', JSON.stringify(R.B2.forceDuring),
      'after failed clear:', JSON.stringify(R.B2.forceAfterFailedClear),
      'after honest clear:', JSON.stringify(R.B2.forceAfterHonestClear),
      '=>', R.B2.DEFECT_LIVE ? 'DEFECT LIVE (no retry, drop confirmed)' : 'retried?');
  }

  // ===== B3 (H9-1): pressEnd never fires on a page-driven release =========
  {
    const counts = {};
    for (const m of ['press', 'pressEnd']) await wrapSound(m);
    await page.keyboard.down(' '); await sleep(800);
    await page.keyboard.up(' '); await sleep(1200);
    counts.press = await soundCount('press');
    counts.pressEnd = await soundCount('pressEnd');
    // and via the mouse release funnel too (down/up on the torso)
    counts.press0 = counts.press;
    await page.keyboard.down(' '); await sleep(600);
    await page.keyboard.press('Escape'); await sleep(800);   // ESC = clearTouch
    await page.keyboard.up(' '); await sleep(400);           // physical release too
    counts.press2 = await soundCount('press');
    counts.pressEndAfterEsc = await soundCount('pressEnd');
    R.B3 = counts;
    R.B3.DEFECT_LIVE = counts.pressEnd === 0 && counts.pressEndAfterEsc === 0 &&
      counts.press >= 2;
    console.log('B3 press calls:', counts.press, '/', counts.press2,
      ' pressEnd calls:', counts.pressEnd, '/', counts.pressEndAfterEsc,
      '=>', R.B3.DEFECT_LIVE ? 'DEFECT LIVE (release never ends the voice)' : 'wired?');
  }

  // ===== B1 (H10-1): a failed gravity enable still arms the judge =========
  {
    let g429 = 0;
    await page.route('**/api/gravity', route => {
      g429++;
      return route.fulfill({ status: 429, contentType: 'application/json',
        body: JSON.stringify({ ok: false, error: 'too many requests' }),
        headers: { 'Retry-After': '1' } });
    });
    // walk ']' to lesson 9 (the_stand, index 8); its showLesson enables gravity
    for (let i = 0; i < 8; i++) { await page.keyboard.press(']'); await sleep(900); }
    await sleep(1500);   // the .then() would have fired by now if it lies
    const line = await judgeLine();
    const w = (await worldState());
    await page.unroute('**/api/gravity');
    const armed = /armed=true/.test(line);
    // engine never got the enable (route ate it): root must still be at rest
    const engineNeverEnabled = Math.abs(Number(w.root_y) || 0) < 1e-4 &&
                               Math.abs(Number(w.root_vy) || 0) < 1e-3;
    R.B1 = { gravity429s: g429, judgeArmed: armed, root_y: w.root_y,
             root_vy: w.root_vy, engineNeverEnabled,
             DEFECT_LIVE: armed && engineNeverEnabled };
    console.log('B1 gravity enable 429s:', g429, '| judge says armed=true:',
      armed, '| engine root_y:', w.root_y, 'root_vy:', w.root_vy,
      '=>', R.B1.DEFECT_LIVE ? 'DEFECT LIVE (false arm)' : 'arm honest?');
  }

  // ===== B4 (H10-3): next lesson opens while the held pose lives on ======
  {
    // back to the_balance (index 5): '[ 'x3 from the_stand (index 8)
    for (let i = 0; i < 3; i++) { await page.keyboard.press('['); await sleep(700); }
    await sleep(500);
    const line0 = await judgeLine();
    R.B4 = { arrivedAt: (line0.match(/judge: (\S+)/) || [])[1] };
    // take ONLY the first wish (ankle pose) -- a partial pair never auto-resets
    await page.click('#pose-btn'); await sleep(800);
    const heldCells = await cells();
    // delay every /api/pose RESPONSE by 700 ms (requests still reach the
    // engine instantly -- only the page's knowledge is slowed)
    let poseDelayOn = true;
    await page.route('**/api/pose', async route => {
      try {
        const resp = await route.fetch();
        if (poseDelayOn) await sleep(700);
        try { await route.fulfill({ response: resp }); } catch (e) { /* unrouted mid-flight */ }
      } catch (e) { try { await route.abort(); } catch (e2) {} }
    });
    const t0 = Date.now();
    await page.keyboard.press(']');            // -> the_heavy_hand (non-pose)
    let flipMs = -1;
    for (let k = 0; k < 150; k++) {            // poll the verdict for 6 s
      const v = await verdict();
      if (/the creature waits/.test(v)) { flipMs = Date.now() - t0; break; }
      await sleep(40);
    }
    await sleep(150);
    const cellsAtFlip = await cells();
    poseDelayOn = false; await sleep(900);   // let in-flight handlers drain
    await page.unroute('**/api/pose');
    const maxAtFlip = Math.max(...cellsAtFlip.map(Math.abs));
    const calmAtFlip = cellsAtFlip.every(p => Math.abs(p) < 500);
    R.B4.heldCellsBeforeNav = heldCells;
    R.B4.flipMs = flipMs;
    R.B4.cellsAtFlip = cellsAtFlip;
    R.B4.maxAbsPaAtFlip = maxAtFlip;
    R.B4.calmAtFlip = calmAtFlip;
    R.B4.DEFECT_LIVE = flipMs >= 0 && flipMs < 1500 && !calmAtFlip;
    console.log('B4 verdict flip after ]:', flipMs, 'ms | cells at flip:',
      JSON.stringify(cellsAtFlip), '=>',
      R.B4.DEFECT_LIVE ? 'DEFECT LIVE (window opened on a held pose)' : 'awaited?');
  }

  // ===== B5 (H9-3): lesson switch re-whooshes an already-awake cell ======
  {
    for (const m of ['wakeWhoosh']) await wrapSound(m);
    await page.keyboard.press('1'); await sleep(700);   // L1 wake_the_cell
    // inject an awake torso on EVERY state poll (page-level lie, engine untouched)
    const inj = { cells: [
      { V: 0.288, P: 0 }, { V: 12.5, P: 60000 }, { V: 0.69, P: 0 },
      { V: 0.33, P: 0 }], root_y: 0, root_vy: 0, conserve_pct: 0 };
    await page.route('**/api/state', route => route.fulfill({
      status: 200, contentType: 'application/json', body: JSON.stringify(inj) }));
    await sleep(2000);                       // L1 polls: crossing -> whoosh #1
    const w1 = await soundCount('wakeWhoosh');
    await page.keyboard.press('3');          // switch to L3 the_healing
    await sleep(2000);                       // first L3 polls
    const w2 = await soundCount('wakeWhoosh');
    await page.unroute('**/api/state');
    await sleep(400);
    R.B5 = { whooshOnL1: w1, whooshAfterSwitch: w2 - w1,
             DEFECT_LIVE: w1 >= 1 && (w2 - w1) >= 1 };
    console.log('B5 whoosh on L1:', w1, ' additional after lesson switch:',
      w2 - w1, '=>', R.B5.DEFECT_LIVE ? 'DEFECT LIVE (spurious re-whoosh)' : 'memo holds?');
  }

  // ===== B6 (H9-4): a throwing synth leaves no trace anywhere ============
  {
    await page.evaluate(() => {
      const S = window.ChimeraSound;
      const orig = S.press;
      S.press = function () { S.__pressThrew = (S.__pressThrew || 0) + 1;
        throw new Error('boom (injected)'); void orig; };
    });
    const errsBefore = consoleErrors.length;
    await page.keyboard.up(' '); await sleep(300);   // defensive: no stale key
    await page.keyboard.down(' '); await sleep(500);
    await page.keyboard.up(' '); await sleep(800);
    const threw = await page.evaluate(() => window.ChimeraSound.__pressThrew || 0);
    const counterExists = await page.evaluate(() =>
      typeof window.__sndFailures !== 'undefined');
    const line = await judgeLine();
    const sndFailShown = /snd-fail/.test(line);
    const newConsoleErrors = consoleErrors.length - errsBefore;
    R.B6 = { synthThrew: threw >= 1, failureCounterExists: counterExists,
             sndFailShown, newConsoleErrors,
             DEFECT_LIVE: threw >= 1 && !counterExists && !sndFailShown &&
               newConsoleErrors === 0 };
    console.log('B6 synth threw:', threw, 'x | failure counter exists:',
      counterExists, '| shown in debug line:', sndFailShown,
      '| new console errors:', newConsoleErrors,
      '=>', R.B6.DEFECT_LIVE ? 'DEFECT LIVE (silence undiagnosable)' : 'visible?');
  }

  R.consoleErrors = consoleErrors.slice(0, 10);
  R.consoleErrorCount = consoleErrors.length;
  fs.writeFileSync(__dirname + '/probe_h7r_before.json', JSON.stringify(R, null, 1));
  console.log('console errors during probe:', consoleErrors.length);
  console.log('WROTE probe_h7r_before.json');
  await browser.close();
})().catch(e => { console.error('PROBE FAILED:', e); process.exit(1); });
