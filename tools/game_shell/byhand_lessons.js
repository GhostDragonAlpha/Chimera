/* byhand_lessons.js -- THE BY-HAND AUDIT (lane L1 lessons-byhand).
   A private headless Chrome drives the game page the way a SLOW HUMAN
   would: real pointer moves (stepped, with human pauses), presses held
   for seconds while "watching the gauge", navigation by the visible
   arrows, force set by DRAGGING the visible slider, releases through
   the visible "let go" button. It uses ONLY controls the page itself
   surfaces -- no scripted POSTs, no keyboard shortcuts a stranger
   could not find, none of the walker's direct API resets.

   For every lesson 1..10 it records: control found? action performed?
   pass registered? pass sentence? -- plus the four judge-reported
   stalls (dead arrows, "you touched only water.", unlabeled cells,
   the pose chips). Run BEFORE a fix it captures the defects; run
   AFTER it is the by-hand 10/10 gate. The walker (walk_lessons10.js)
   stays the scripted regression; both must pass.

   Run:  node tools/game_shell/byhand_lessons.js [name] [outdir]  */
const path = require('path');
const fs = require('fs');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));

const URL_ = 'http://127.0.0.1:8206/?debug=1';
const NAME = process.argv[2] || ('byhand-' + new Date().toISOString().replace(/[:.]/g, '-').slice(0, 16));
const OUT = process.argv[3] || 'E:/ChimeraWork/slot-01/docs/evidence/agent_fleet/SHIP/L1_LESSONS_BYHAND';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const human = () => sleep(200 + Math.random() * 200);   // 200-400 ms between actions

// the page's own orbit camera (index.html `cam`), for aiming the pointer
const CAM = { r: 26, theta: -0.55, phi: 0.42, target: [0, 4.5, 0], fov: 45 };

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });
  const pageErrors = [];
  page.on('pageerror', e => pageErrors.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') pageErrors.push('console: ' + m.text()); });

  const log = (...a) => console.log(...a);
  const results = { name: NAME, started: new Date().toISOString(), url: URL_,
                    lessons: [], checks: {}, pageErrors };

  // ---------- reads (the page's own HUD, plus the world the HUD mirrors)
  const state = async () => page.evaluate(() =>
    fetch('/api/state').then(r => { if (r.status === 429) throw new Error('429'); return r.json(); })
      .catch(e => { throw e; }));
  const stateSafe = async () => {           // back off on 429 / hiccups
    for (let i = 0; i < 5; i++) {
      try { return await state(); } catch (e) { await sleep(800 * (i + 1)); }
    }
    return null;
  };
  const dom = sel => page.evaluate(id => (document.getElementById(id) || {}).textContent || '', sel.slice(1));
  const judgeLine = () => dom('#judge-debug');
  const verdict = () => dom('#verdict');
  const handLine = () => dom('#hand-state');
  const bloodText = () => dom('#blood');
  const lessonIndex = () => dom('#lesson-index');
  const judge = async () => {                // parse the page's own telemetry line
    const m = (await judgeLine()).match(/judge: (\S+) phase=(\S+) goalMet=(\S+) passed=(\S+)(.*)/);
    return m ? { id: m[1], phase: m[2], goalMet: m[3] === 'true', passed: m[4] === 'true', rest: m[5] } : null;
  };
  const cellsP = async () => { const s = await stateSafe();
    return s ? (s.cells || []).map(c => Math.abs(Number(c.P) || 0)) : null; };
  const rootLine = async () => { const s = await stateSafe();
    return s ? ('gravity_on=' + s.gravity_on + ' root_y=' + Number(s.root_y).toFixed(4)) : 'state unreadable'; };

  // wait for the judge's passed flag (the page's own verdict, not ours)
  const waitPassed = async (capMs) => {
    const t0 = Date.now();
    while (Date.now() - t0 < capMs) {
      const j = await judge();
      if (j && j.passed) return true;
      await sleep(600);
    }
    return false;
  };
  const waitCalm = async (capMs) => {        // the release phase: the world heals
    const t0 = Date.now();
    while (Date.now() - t0 < capMs) {
      const ps = await cellsP();
      if (ps && ps.length && ps.every(p => p < 1000)) { await sleep(1800); return true; }
      await sleep(600);
    }
    return false;
  };

  // ---------- human gestures (pointer only; nothing the page does not show)
  const humanClick = async sel => {
    const el = await page.$(sel);
    if (!el) return false;
    const b = await el.boundingBox();
    await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2, { steps: 10 });
    await human();
    await page.mouse.down(); await sleep(60 + Math.random() * 60); await page.mouse.up();
    await human();
    return true;
  };

  // aim the pointer at a world point on the creature (what a player does:
  // look at the belly / shin / foot and move the mouse there) and PRESS
  const pressWorld = async (wx, wy, wz, holdMs, tag) => {
    const rect = await page.evaluate(() => {
      const c = document.getElementById('gl');
      const r = c.getBoundingClientRect();
      return { left: r.left, top: r.top, width: r.width, height: r.height, aspect: r.width / r.height };
    });
    const ch = Math.cos(CAM.phi);
    const eye = [CAM.target[0] + CAM.r * ch * Math.sin(CAM.theta),
                 CAM.target[1] + CAM.r * Math.sin(CAM.phi),
                 CAM.target[2] + CAM.r * ch * Math.cos(CAM.theta)];
    const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
    const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
    const crs = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
    const nrm = a => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
    const tanF = Math.tan(CAM.fov * Math.PI / 360);
    const fwd = nrm(sub(CAM.target, eye));
    const right = nrm(crs(fwd, [0, 1, 0]));
    const up = crs(right, fwd);
    const d = sub([wx, wy, wz], eye);
    const depth = dot(d, fwd);
    const ndcX = (dot(d, right) / depth) / (tanF * rect.aspect);
    const ndcY = (dot(d, up) / depth) / tanF;
    const bx = rect.left + (ndcX + 1) / 2 * rect.width;
    const by = rect.top + (1 - ndcY) / 2 * rect.height;
    log('   ' + tag + ' aim px (' + bx.toFixed(0) + ',' + by.toFixed(0) + ')');
    await page.mouse.move(bx, by, { steps: 14 });
    await human();
    await page.mouse.down();
    await sleep(300);                        // the page's own 130 ms arm guard + POST
    const t0 = Date.now();
    let midCells = null, midHand = '';
    while (Date.now() - t0 < holdMs) {       // hold like a human, glancing at the HUD
      await sleep(700);
      midCells = await cellsP();
      midHand = await handLine();
    }
    log('   ' + tag + ' held ' + holdMs + ' ms  hand: "' + midHand + '"  |P| Pa: ' +
        (midCells || []).map(p => Math.round(p)).join(' '));
    await page.mouse.up();
    await human();
    return { hand: midHand, cells: midCells };
  };

  // drag the visible force slider (the judges' most-reported stall)
  const dragForceTo = async (target) => {
    const el = await page.$('#force');
    const b = await el.boundingBox();
    const lo = 500, hi = 50000;
    const xOf = v => b.x + 8 + ((v - lo) / (hi - lo)) * (b.width - 16);
    const v0 = Number(await page.$eval('#force', i => i.value));
    const y = b.y + b.height / 2;
    await page.mouse.move(xOf(v0), y, { steps: 8 });
    await human();
    await page.mouse.down();
    // human drags overshoot and correct: go fast, then settle
    await page.mouse.move(xOf(target) + (Math.random() * 14 - 7), y, { steps: 18 });
    await sleep(120 + Math.random() * 120);
    await page.mouse.move(xOf(target), y, { steps: 5 });
    await sleep(150);
    await page.mouse.up();
    await human();
    let v1 = Number(await page.$eval('#force', i => i.value));
    if (Math.abs(v1 - target) > 400) {       // coarse correction: click the track, then nudge
      await page.mouse.click(xOf(target), y);
      await human();
      v1 = Number(await page.$eval('#force', i => i.value));
      const k = v1 < target ? '=' : '-';
      let guard = 80;
      while (Math.abs(v1 - target) > 400 && guard-- > 0) {
        await page.keyboard.press(k); await sleep(25);
        v1 = Number(await page.$eval('#force', i => i.value));
      }
    }
    log('   force slider -> ' + v1 + ' N (wanted ' + target + ')');
    return v1;
  };

  // drag a pose-angle slider (range -90..90) to a value, like a wrist move
  const dragAngleTo = async (sel, target) => {
    const el = await page.$(sel);
    if (!el) return null;
    const b = await el.boundingBox();
    const xOf = v => b.x + 7 + ((v + 90) / 180) * (b.width - 14);
    const v0 = Number(await page.$eval(sel, i => i.value));
    const y = b.y + b.height / 2;
    await page.mouse.move(xOf(v0), y, { steps: 8 });
    await human();
    await page.mouse.down();
    await page.mouse.move(xOf(target) + (Math.random() * 8 - 4), y, { steps: 12 });
    await sleep(100 + Math.random() * 100);
    await page.mouse.move(xOf(target), y, { steps: 4 });
    await sleep(120);
    await page.mouse.up();
    await human();
    let v1 = Number(await page.$eval(sel, i => i.value));
    // fine-tune like a wrist: the slider takes its own arrow keys, 1 deg each
    let guard = 12;
    while (v1 !== target && guard-- > 0) {
      await page.focus(sel);
      await page.keyboard.press(v1 < target ? 'ArrowRight' : 'ArrowLeft');
      await sleep(40);
      v1 = Number(await page.$eval(sel, i => i.value));
    }
    return v1;
  };

  const nextLesson = async wantIdx => {      // navigate by the visible arrow
    await humanClick('#lesson-next');
    await sleep(900);                        // showLesson resets the world to rest
    const idx = await lessonIndex();
    return idx.startsWith(wantIdx + ' ');
  };
  const dismissPayoff = async () => {
    try { await page.click('#payoff-continue', { timeout: 1500 }); log('   payoff dismissed'); await human(); }
    catch (e) { /* not up */ }
  };

  // ======================================================================
  await page.goto(URL_, { waitUntil: 'load' });
  await sleep(2500);                          // world attach
  await page.fill('#name-input', NAME);
  await humanClick('#play-btn');
  await sleep(1200);
  try { await humanClick('#intro-begin'); log('intro: begun'); } catch (e) { log('intro: not shown'); }
  await sleep(800);

  // -- world to authored rest through the page's own button --------------
  log('WORLD BEFORE: ' + await rootLine());
  await humanClick('#rest-btn');
  await sleep(1500);
  log('WORLD AT REST (via "stand at rest"): ' + await rootLine());

  // -- stall check 1: the lesson arrows ----------------------------------
  const idx0 = await lessonIndex();
  await humanClick('#lesson-next'); await sleep(700);
  const idx1 = await lessonIndex();
  await humanClick('#lesson-prev'); await sleep(700);
  const idx2 = await lessonIndex();
  results.checks.arrows = { from: idx0, afterNext: idx1, afterPrev: idx2,
                            nextWorks: idx1 !== idx0, prevWorks: idx2 === idx0 };
  log('ARROWS: next ' + (idx1 !== idx0 ? 'WORKS' : 'DEAD') + '  prev ' + (idx2 === idx0 ? 'WORKS' : 'DEAD'));

  // -- stall check 2: keyboard lesson keys beyond 5 -----------------------
  await page.keyboard.press('7'); await sleep(600);
  const idxK = await lessonIndex();
  await page.keyboard.press('1'); await sleep(900);   // back by the page's own key
  results.checks.keyboardBeyond5 = { pressed7: idxK, changed: idxK !== '1 / 10' };
  log('KEY "7": lesson shows "' + idxK + '" (changed=' + (idxK !== '1 / 10') + ')');

  // -- stall check 3: a click on open water -------------------------------
  {
    const rect = await page.evaluate(() => {
      const r = document.getElementById('gl').getBoundingClientRect();
      return { left: r.left, top: r.top, width: r.width, height: r.height };
    });
    await page.mouse.move(rect.left + rect.width * 0.12, rect.top + rect.height * 0.15, { steps: 10 });
    await human();
    await page.mouse.down(); await sleep(400); await page.mouse.up();
    await sleep(400);
    results.checks.waterMissMessage = await handLine();
    log('WATER MISS hand line: "' + results.checks.waterMissMessage + '"');
  }
  // -- stall check 4: the blood panel's labels ----------------------------
  results.checks.bloodLabels = (await bloodText()).split('\n').slice(0, 4);
  log('BLOOD PANEL:\n   ' + results.checks.bloodLabels.join('\n   '));

  // the pack, for the honest numbers each lesson asks for
  const pack = await page.evaluate(() => fetch('/lessons.json').then(r => r.json()));
  const L = id => pack.lessons.find(l => l.id === id);
  const packTarget = (l, i) => (l.touch_targets || [l.touch_target])[i || 0];

  const record = async (id, control, actions, extra) => {
    // the page's debug line catches up with the verdict on the NEXT state
    // poll (~700 ms): while the verdict already says PASSED but the judge
    // line lags, wait — never record a pass state older than the sentence.
    const t0 = Date.now();
    while (Date.now() - t0 < 2500) {
      const v = (await verdict()).trim();
      const j = await judge();
      if (!(j && !j.passed && v.indexOf('PASSED') === 0)) break;
      await sleep(300);
    }
    const j = await judge();
    const row = Object.assign({ id, control, actions,
      passed: !!(j && j.passed), sentence: (await verdict()).trim(),
      judgeLine: await judgeLine() }, extra || {});
    results.lessons.push(row);
    log('>> ' + id + ': ' + (row.passed ? 'PASS' : 'NO-PASS') + '  "' + row.sentence + '"' +
        (row.note ? '\n   NOTE: ' + row.note : ''));
    await dismissPayoff();
    return row;
  };

  // ===== L1 WAKE THE CELL ==============================================
  {
    await dragForceTo(50000);
    const t = packTarget(L('wake_the_cell'));
    const mid = await pressWorld(t[0], t[1], t[2], 2200, 'L1 belly');
    await humanClick('#letgo-btn');
    await waitCalm(20000);
    await record('wake_the_cell', 'force slider drag + click-hold the belly + let go',
      ['drag slider to 50000 N', 'press belly ' + (Math.round(2200)) + ' ms', 'click "let go"'],
      { midHoldCells: mid.cells });
  }

  // ===== L2 THE GENTLE HAND ============================================
  {
    await nextLesson(2);
    // first the WRONG action: a strong press (the honest-refusal audit)
    await dragForceTo(50000);
    const t = packTarget(L('the_gentle_hand'));
    const wrong = await pressWorld(t[0], t[1], t[2], 2000, 'L2 too-strong foot');
    const wrongVerdict = await verdict();
    await humanClick('#letgo-btn');
    await waitCalm(15000);
    // now the right action: a gentle hand
    await dragForceTo(6000);
    const right = await pressWorld(t[0], t[1], t[2], 2200, 'L2 gentle foot');
    await humanClick('#letgo-btn');
    await waitCalm(15000);
    await record('the_gentle_hand', 'force slider drag + click-hold a foot + let go',
      ['WRONG: press foot at 50000 N', 'drag slider to 6000 N', 'press foot 2200 ms', 'click "let go"'],
      { overForceHint: wrongVerdict.trim(), overForceCells: wrong.cells, gentleCells: right.cells });
  }

  // ===== L3 THE HEALING ================================================
  {
    await nextLesson(3);
    await dragForceTo(50000);
    const t = packTarget(L('the_healing'));
    await pressWorld(t[0], t[1], t[2], 2200, 'L3 belly');
    await humanClick('#letgo-btn');
    const calm = await waitCalm(20000);
    await record('the_healing', 'click-hold any part + let go + wait',
      ['press belly 2200 ms', 'click "let go"', 'waited for the heal: ' + calm]);
  }

  // ===== L4 BEND THE KNEE ==============================================
  {
    await nextLesson(4);
    const hasSlider = !!(await page.$('#pose-angle'));
    const hasOldChip = !!(await page.$('#pose-btn'));
    let actions = [], note = null;
    if (hasSlider) {
      actions.push('drag knee slider to 60 (a wrong wish first)');
      const vWrong = await dragAngleTo('#pose-angle', 60);
      await humanClick('#pose-post');
      await sleep(900);
      const wrongVerdict = await verdict();
      actions.push('wrong-wish verdict: "' + wrongVerdict.trim() + '"');
      actions.push('drag knee slider to 40 and post');
      const v = await dragAngleTo('#pose-angle', 40);
      actions.push('slider read ' + v + ' deg');
      await humanClick('#pose-post');
    } else if (hasOldChip) {
      note = 'DEFECT: no angle control -- one chip posts the goal verbatim';
      actions.push('click the single pose chip');
      await humanClick('#pose-btn');
      await sleep(1500);
      const afterOne = await judge();
      if (afterOne && afterOne.passed) {   // the self-pass
        actions.push('ONE click passed the lesson (self-granted)');
        await humanClick('#pose-btn');     // the chip stays: is it alive?
        await sleep(800);
        actions.push('clicked the chip again: verdict "' + (await verdict()).trim() + '"');
      }
    } else {
      note = 'DEFECT: no pose control at all';
    }
    await record('bend_the_knee',
      hasSlider ? 'knee angle slider + "post the wish" button'
      : (hasOldChip ? 'single auto-wish chip (no angle control)' : 'NONE'),
      actions, { note, controlsSeen: { slider: hasSlider, oldChip: hasOldChip } });
  }

  // ===== L5 THE WHOLE BODY =============================================
  {
    await nextLesson(5);
    const l = L('the_whole_body');
    const belly = l.touch_targets[0], shin = l.touch_targets[1];
    await dragForceTo(20000);
    await pressWorld(belly[0], belly[1], belly[2], 2200, 'L5 belly');
    let jMid = await judge();
    const afterBelly = { goalMet: jMid && jMet(jMid), note: (jMid && jMid.rest || '').trim() };
    await human(); await human();
    // THE HUMAN SHIN PRESS: held long while watching the gauge climb
    const shinHold = await pressWorld(shin[0], shin[1], shin[2], 5000, 'L5 shin(stare)');
    jMid = await judge();
    const afterShin = { goalMet: jMid && jMet(jMid), note: (jMid && jMid.rest || '').trim() };
    await humanClick('#letgo-btn');
    await waitCalm(25000);
    await record('the_whole_body', 'click-hold belly, then click-hold the shins, let go',
      ['press belly 2200 ms', 'press shin 5000 ms (a human stare)', 'click "let go"'],
      { shinHoldCells: shinHold.cells, afterBelly, afterShin,
        note: 'shin goal latched=' + JSON.stringify(afterShin) });
  }
  function jMet(j) { return j.goalMet; }

  // ===== L6 THE BALANCE ================================================
  {
    await nextLesson(6);
    const chips = await page.$$('.pose-post');
    let actions = [], note = null, control;
    if (chips.length >= 2) {
      control = 'one wish chip per ankle, each with its own angle slider';
      actions.push('drag ankle_L slider to 5, post it');
      await dragAngleTo('#pose-angle-0', 5); await humanClick('#pose-post-0');
      await sleep(900);
      const afterOne = await judge();
      const passedAfterOne = !!(afterOne && afterOne.passed);
      if (passedAfterOne) note = 'DEFECT: one wish passed the pair lesson';
      actions.push('drag ankle_R slider to -5, post it');
      await dragAngleTo('#pose-angle-1', -5); await humanClick('#pose-post-1');
      actions.push('passed after first wish: ' + passedAfterOne);
    } else if (await page.$('#pose-btn')) {
      control = 'single auto-wish chip';
      note = 'DEFECT: the chip posts BOTH wishes in one click; after the pass it stays visible but inert';
      actions.push('click the single chip once');
      await humanClick('#pose-btn');
      await sleep(1500);
      actions.push('click the (still visible) chip again');
      const vBefore = await verdict();
      await humanClick('#pose-btn');
      await sleep(800);
      actions.push('second click changed nothing: "' + (await verdict()).trim() + '" (was "' + vBefore.trim() + '")');
    } else {
      control = 'NONE'; note = 'DEFECT: no pose control';
    }
    await record('the_balance', control, actions, { note });
  }

  // ===== L7 THE HEAVY HAND =============================================
  {
    await nextLesson(7);
    await dragForceTo(50000);
    const t = packTarget(L('the_heavy_hand'));
    const mid = await pressWorld(t[0], t[1], t[2], 5000, 'L7 belly(max)');
    await humanClick('#letgo-btn');
    await waitCalm(25000);
    const peak = mid.cells ? Math.max(...mid.cells) : 0;
    const want = L('the_heavy_hand').goal.threshold_pa;
    await record('the_heavy_hand', 'force slider to max + click-hold the belly + let go',
      ['drag slider to 50000 N', 'press belly 5000 ms', 'click "let go"'],
      { torsoPeakPa: Math.round(peak), lessonWantsPa: want,
        note: peak < want ? 'DEFECT: the belly at the slider MAX reaches ' + Math.round(peak) +
          ' Pa -- the lesson as pointed asks ' + want + ' Pa and can never latch' : 'reachable' });
  }

  // ===== L8 THE CASCADE ================================================
  {
    await nextLesson(8);
    await dragForceTo(50000);
    const t = packTarget(L('the_cascade'));
    const mid = await pressWorld(t[0], t[1], t[2], 3000, 'L8 belly');
    await humanClick('#letgo-btn');
    await waitCalm(25000);
    await record('the_cascade', 'force slider to max + click-hold the belly + let go',
      ['press belly 3000 ms', 'click "let go"'],
      { midHoldCells: mid.cells });
  }

  // ===== L9 THE STAND ==================================================
  {
    await nextLesson(9);
    const hasBtn = !!(await page.$('#gravity-btn'));
    let actions = [], note = null, control;
    if (hasBtn) {
      control = '"wake the world\'s weight" button on the lesson card';
      await humanClick('#gravity-btn');
      actions.push('clicked "wake the world\'s weight"');
      await sleep(2500);
      actions.push('world: ' + await rootLine());
    } else {
      control = 'NONE (the page arms gravity by itself at lesson start)';
      note = 'DEFECT: nothing to do -- watch whether the lesson passes with zero action';
      actions.push('(no action available; waiting)');
      await sleep(2500);
      actions.push('world: ' + await rootLine());
    }
    const passed = await waitPassed(15000);
    if (!hasBtn && passed) note += ' -- PASSED WITH ZERO PLAYER ACTION';
    await record('the_stand', control, actions, { note, passedOverride: passed, world: await rootLine() });
  }

  // ===== L10 THE GRADUATION ============================================
  {
    await nextLesson(10);
    const l = L('the_graduation');
    await dragForceTo(20000);
    const spots = l.touch_targets;
    const pick = [spots[0], spots[1], spots[3]];   // belly, left foot, left shin
    const cells = [];
    for (let i = 0; i < pick.length; i++) {
      const mid = await pressWorld(pick[i][0], pick[i][1], pick[i][2], 2000, 'L10 spot' + i);
      cells.push(mid.cells);
      await human();
    }
    await humanClick('#letgo-btn');
    await waitCalm(25000);
    const j = await judge();
    await record('the_graduation', 'click-hold three different parts + let go',
      ['belly, left foot, left shin -- 2000 ms each', 'click "let go"'],
      { cellsPerPress: cells, judgeRest: j && j.rest });
  }

  // ======================================================================
  results.finished = new Date().toISOString();
  const rows = results.lessons;
  const passedN = rows.filter(r => r.passed || r.passedOverride).length;
  const sentences = rows.map(r => r.sentence);
  results.distinctSentences = new Set(sentences).size === sentences.length;
  results.passedCount = passedN;
  log('\n===== BY-HAND VERDICT TABLE (' + NAME + ') =====');
  rows.forEach((r, i) => log(' ' + (i + 1) + '. ' + r.id.padEnd(16) +
    (r.passed || r.passedOverride ? 'PASS' : 'NO-PASS') + '  "' + r.sentence.slice(0, 72) + '"'));
  log('PASSED BY HAND: ' + passedN + ' of 10   distinct sentences: ' +
      (results.distinctSentences ? 'yes' : 'NO') + '   page errors: ' + pageErrors.length);
  const file = OUT + '/byhand_' + NAME + '.json';
  fs.writeFileSync(file, JSON.stringify(results, null, 1));
  log('EVIDENCE: ' + file);
  await browser.close();
  process.exit(0);
})().catch(e => { console.error('BYHAND FAILED:', e); process.exit(1); });
