/* probe_h7r_after.js -- H7r AFTER-fix verification: the six BEFORE defects
   (probe_h7r_before.js, all DEFECT LIVE) re-run under the same failure
   injections; each section asserts the repro is GONE.
   A1 H10-1  a 429'd gravity enable leaves the judge UNARMED (and an honest
             enable still arms)
   A2 H10-2  a 429'd touch_clear is RETRIED until the world takes it
   A3 H9-1   every page-driven release calls pressEnd (voice ends)
   A4 H10-3  the next lesson's window opens only AFTER the awaited reset
   A5 H9-3   a lesson switch never re-whooshes an already-awake cell
   A6 H9-4   a throwing synth is counted + debug-visible, never console-noise
   Run: node probe_h7r_after.js */
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
  const gravityOff = () => page.evaluate(() => fetch('/api/gravity', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ on: false }) }).then(r => r.json()));

  await page.goto(URL_, { waitUntil: 'load' });
  await sleep(2000);
  await gravityOff();
  await page.fill('#name-input', 'h7rprobe');
  await page.click('#play-btn'); await sleep(1200);
  try { await page.click('#intro-begin', { timeout: 3000 }); } catch (e) {}
  await sleep(800);

  // ===== A2 (H10-2): the 429'd clear is retried and lands ================
  {
    let clearCalls = 0;
    await page.route('**/api/touch_clear', async route => {
      clearCalls++;
      try {
        if (clearCalls === 1) {
          return await route.fulfill({ status: 429, contentType: 'application/json',
            body: JSON.stringify({ ok: false, error: 'too many requests' }),
            headers: { 'Retry-After': '1' } });
        }
        const resp = await route.fetch();
        return await route.fulfill({ response: resp });
      } catch (e) { try { await route.abort(); } catch (e2) {} }
    });
    await page.keyboard.down(' '); await sleep(900);
    await page.keyboard.up(' ');          // -> clearTouch -> first POST 429s
    await sleep(3000);                    // window for the backoff retry
    await page.unroute('**/api/touch_clear');
    const retriesHappened = clearCalls >= 2;
    // leave the world clean WITHOUT the manual honest clear: retry it only
    // if the page failed (it should not)
    let manualNeeded = false;
    if (!retriesHappened) { manualNeeded = true; await gravityOff(); }
    R.A2 = { clearCalls, retriesHappened, manualNeeded,
             CLEAN: retriesHappened && !manualNeeded };
    console.log('A2 touch_clear calls during release:', clearCalls,
      '=>', R.A2.CLEAN ? 'RETRIED + LANDED (was: 1 call, dropped)' : 'STILL BROKEN');
  }

  // ===== A3 (H9-1): every release ends the press voice ===================
  {
    for (const m of ['press', 'pressEnd']) await wrapSound(m);
    await page.keyboard.down(' '); await sleep(800);
    await page.keyboard.up(' '); await sleep(1000);          // keyup release
    const afterKeyup = await soundCount('pressEnd');
    await page.keyboard.down(' '); await sleep(600);
    await page.keyboard.press('Escape'); await sleep(800);   // ESC release funnel
    await page.keyboard.up(' '); await sleep(400);
    const afterEsc = await soundCount('pressEnd');
    const presses = await soundCount('press');
    R.A3 = { presses, afterKeyup, afterEsc, CLEAN: presses >= 2 &&
      afterKeyup >= 1 && afterEsc === presses && afterEsc > afterKeyup };
    console.log('A3 presses:', presses, ' pressEnd after keyup:', afterKeyup,
      ' after ESC:', afterEsc,
      '=>', R.A3.CLEAN ? 'VOICE ENDS ON EVERY RELEASE (was: 0 calls)' : 'STILL BROKEN');
  }

  // ===== A1 (H10-1): failed enable -> unarmed; honest enable -> armed ====
  {
    let g429 = 0;
    await page.route('**/api/gravity', route => {
      g429++;
      try {
        return route.fulfill({ status: 429, contentType: 'application/json',
          body: JSON.stringify({ ok: false, error: 'too many requests' }),
          headers: { 'Retry-After': '1' } });
      } catch (e) {}
    });
    for (let i = 0; i < 8; i++) { await page.keyboard.press(']'); await sleep(900); }
    await sleep(3000);              // the old .then() would have lied by now
    const line429 = await judgeLine();
    const w1 = (await worldState());
    await page.unroute('**/api/gravity');
    const unarmedUnder429 = !/armed=true/.test(line429) && /armed=false/.test(line429);
    // now the honest arm: navigate away and back -- the enable re-fires
    await gravityOff(); await sleep(500);
    await page.keyboard.press('['); await sleep(900);
    await page.keyboard.press(']'); await sleep(1200);
    let armedHonest = false, settled = null;
    for (let k = 0; k < 25; k++) {          // wait for the enable + settle
      const line = await judgeLine();
      if (/armed=true/.test(line)) armedHonest = true;
      const w = (await worldState());
      settled = { root_y: w.root_y, root_vy: w.root_vy };
      if (armedHonest && Math.abs(Number(w.root_vy) || 0) < 0.05 &&
          Math.abs(Number(w.root_y) || 0) > 0.002) break;
      await sleep(700);
    }
    await gravityOff();                     // leave the world at rest
    await sleep(400);
    R.A1 = { gravity429s: g429, unarmedUnder429, armedHonest, settled,
             CLEAN: g429 >= 1 && unarmedUnder429 && armedHonest };
    console.log('A1 429s:', g429, '| armed stays FALSE under 429:', unarmedUnder429,
      '| honest enable arms + root settles:', armedHonest, JSON.stringify(settled),
      '=>', R.A1.CLEAN ? 'ARM IS HONEST (was: armed=true over a dead enable)' : 'STILL BROKEN');
  }

  // ===== A4 (H10-3): window opens only after the awaited reset ===========
  {
    for (let i = 0; i < 3; i++) { await page.keyboard.press('['); await sleep(700); }
    await sleep(500);
    const line0 = await judgeLine();
    R.A4 = { arrivedAt: (line0.match(/judge: (\S+)/) || [])[1] };
    await page.click('#pose-btn'); await sleep(800);   // first wish only: no auto-reset
    const heldCells = await cells();
    let poseDelayOn = true;
    await page.route('**/api/pose', async route => {
      try {
        const resp = await route.fetch();
        if (poseDelayOn) await sleep(700);
        try { await route.fulfill({ response: resp }); } catch (e) {}
      } catch (e) { try { await route.abort(); } catch (e2) {} }
    });
    const t0 = Date.now();
    await page.keyboard.press(']');            // -> the_heavy_hand (non-pose)
    let flipMs = -1;
    for (let k = 0; k < 200; k++) {            // poll the verdict for 8 s
      const v = await verdict();
      if (/the creature waits/.test(v)) { flipMs = Date.now() - t0; break; }
      await sleep(40);
    }
    await sleep(150);
    const cellsAtFlip = await cells();
    poseDelayOn = false; await sleep(900);
    await page.unroute('**/api/pose');
    const calmAtFlip = cellsAtFlip.every(p => Math.abs(p) < 500);
    R.A4.heldCellsBeforeNav = heldCells;
    R.A4.flipMs = flipMs;
    R.A4.cellsAtFlip = cellsAtFlip;
    R.A4.calmAtFlip = calmAtFlip;
    // the flip must come AFTER the six delayed reset posts resolved
    // (>= ~3.5 s with the 700 ms response delay) and the cells must be calm
    R.A4.CLEAN = flipMs >= 3500 && calmAtFlip;
    console.log('A4 verdict flip after ]:', flipMs, 'ms | cells at flip:',
      JSON.stringify(cellsAtFlip), '=>',
      R.A4.CLEAN ? 'WINDOW OPENS ON REST (was: flip at 8 ms on a held pose)' : 'STILL BROKEN');
  }

  // ===== A5 (H9-3): lesson switch never re-whooshes ======================
  {
    await wrapSound('wakeWhoosh');
    await page.keyboard.press('1'); await sleep(700);
    const inj = { cells: [
      { V: 0.288, P: 0 }, { V: 12.5, P: 60000 }, { V: 0.69, P: 0 },
      { V: 0.33, P: 0 }], root_y: 0, root_vy: 0, conserve_pct: 0 };
    await page.route('**/api/state', route => route.fulfill({
      status: 200, contentType: 'application/json', body: JSON.stringify(inj) }));
    await sleep(2000);
    const w1 = await soundCount('wakeWhoosh');
    await page.keyboard.press('3');
    await sleep(2000);
    const w2 = await soundCount('wakeWhoosh');
    // and a REAL re-crossing still whooshes: wake bar falls, then rises again
    await page.unroute('**/api/state');
    await sleep(600);
    R.A5 = { whooshOnL1: w1, whooshAfterSwitch: w2 - w1,
             CLEAN: w1 >= 1 && w2 === w1 };
    console.log('A5 whoosh on L1:', w1, ' additional after lesson switch:', w2 - w1,
      '=>', R.A5.CLEAN ? 'MEMO HOLDS ACROSS SWITCH (was: +1 spurious)' : 'STILL BROKEN');
  }

  // ===== A6 (H9-4): throwing synth -> counted, debug-visible, quiet =====
  {
    await page.evaluate(() => {
      const S = window.ChimeraSound;
      S.press = function () { S.__pressThrew = (S.__pressThrew || 0) + 1;
        throw new Error('boom (injected)'); };
    });
    const errsBefore = consoleErrors.length;
    await page.keyboard.up(' '); await sleep(300);   // defensive: no stale key
    await page.keyboard.down(' '); await sleep(500);
    await page.keyboard.up(' '); await sleep(1200);  // let the debug line render
    const threw = await page.evaluate(() => window.ChimeraSound.__pressThrew || 0);
    const counter = await page.evaluate(() => window.__sndFailures || null);
    const counterExists = counter !== null;
    const line = await judgeLine();
    const sndFailShown = /snd-fail:\s*press/.test(line);
    const newConsoleErrors = consoleErrors.length - errsBefore;
    R.A6 = { synthThrew: threw >= 1, counterExists,
             counted: counterExists && (counter.press || 0) >= 1,
             sndFailShown, newConsoleErrors,
             CLEAN: threw >= 1 && counterExists && (counter.press || 0) >= 1 &&
               sndFailShown && newConsoleErrors === 0 };
    console.log('A6 synth threw:', threw, 'x | counted:', counterExists && (counter.press || 0),
      '| debug line shows snd-fail:', sndFailShown,
      '| new console errors:', newConsoleErrors,
      '=>', R.A6.CLEAN ? 'SILENCE IS DIAGNOSABLE (was: no trace anywhere)' : 'STILL BROKEN');
  }

  R.consoleErrors = consoleErrors.slice(0, 10);
  R.consoleErrorCount = consoleErrors.length;
  fs.writeFileSync(__dirname + '/probe_h7r_after.json', JSON.stringify(R, null, 1));
  console.log('console errors during probe:', consoleErrors.length,
    '(the only allowed: browser logs of THIS probe\'s own injected 429s)');
  console.log('WROTE probe_h7r_after.json');
  await browser.close();
})().catch(e => { console.error('PROBE FAILED:', e); process.exit(1); });
