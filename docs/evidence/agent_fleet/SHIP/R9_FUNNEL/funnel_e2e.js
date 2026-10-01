/* funnel_e2e.js -- H6 "funnel-e2e": THE STRANGER WALK, headless.
   Plays the customer exactly: land on the website cold, find the demo
   door by reading the page, click through to the game shell, pass TWO
   lessons through the page's own rail (SPACE / force keys / ESC), come
   back and sign up as funnel-test@example.com. Every stage screenshotted;
   console errors, HTTP >= 400, failed requests, and 429s counted.
   Evidence -> docs/evidence/agent_fleet/SHIP/R9_FUNNEL/

   Run: node docs/evidence/agent_fleet/SHIP/R9_FUNNEL/funnel_e2e.js */
const fs = require('fs');
const { chromium } = require('E:/PythonChimera/node_modules/playwright-core');

const SITE = 'http://127.0.0.1:8210';
const SHOTS = 'E:/ChimeraWork/slot-01/docs/evidence/agent_fleet/SHIP/R9_FUNNEL';
const CAMERA_NAME = 'FunnelVisitor';
const SIGNUP = { name: 'H6 Funnel Test', email: 'funnel-test@example.com' };

const T0 = Date.now();
const T = {
  at: new Date().toISOString(), runner: 'H6-funnel-e2e',
  consoleErrors: [], pageErrors: [], badResponses: [], failedRequests: [],
  reqCount: { site: 0, game: 0 }, urlCounts: { site: {}, game: {} },
  notes: [],
};
const sleep = ms => new Promise(r => setTimeout(r, ms));

function wire(page, tag) {
  page.on('console', m => {
    if (m.type() === 'error') {
      T.consoleErrors.push({ tag, text: m.text(), tSec: (Date.now() - T0) / 1000 });
      console.log('CONSOLE ERROR [' + tag + ']:', m.text());
    }
  });
  page.on('pageerror', e => {
    T.pageErrors.push({ tag, message: e.message });
    console.log('PAGE ERROR [' + tag + ']:', e.message);
  });
  page.on('request', r => {
    T.reqCount[tag] = (T.reqCount[tag] || 0) + 1;
    try {
      const u = new URL(r.url());
      const k = u.pathname + (u.pathname.indexOf('/api/') === 0 ? '?' +
        (u.searchParams.get('delta') || '') : '');
      T.urlCounts[tag][k] = (T.urlCounts[tag][k] || 0) + 1;
    } catch (e) {}
  });
  page.on('response', r => {
    if (r.status() >= 400) {
      T.badResponses.push({ tag, url: r.url(), status: r.status(),
                            tSec: Math.round((Date.now() - T0) / 100) / 10 });
      console.log('HTTP ' + r.status() + ' [' + tag + '] t+' +
        Math.round((Date.now() - T0) / 100) / 10 + 's: ' + r.url());
    }
  });
  page.on('requestfailed', r => {
    T.failedRequests.push({ tag, url: r.url(), error: r.failure() && r.failure().errorText });
    console.log('REQ FAILED [' + tag + ']: ' + r.url() + ' (' +
      (r.failure() && r.failure().errorText) + ')');
  });
}

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const context = await browser.newContext({ viewport: { width: 1600, height: 900 } });
  const out = { verdict: 'FAIL', stages: {} };

  // ============ STAGE 1: cold landing ============
  console.log('=== STAGE 1: land on ' + SITE + ' cold ===');
  const site = await context.newPage();
  wire(site, 'site');
  const t0 = Date.now();
  const resp = await site.goto(SITE, { waitUntil: 'load', timeout: 30000 });
  const siteLoadMs = Date.now() - t0;
  await sleep(1200);                                  // count fetch settles
  await site.screenshot({ path: SHOTS + '/01_site_landing_cold.png' });
  const nav = await site.evaluate(() => {
    const n = performance.getEntriesByType('navigation')[0];
    return n ? { ttfbMs: Math.round(n.responseStart),
                 domContentLoadedMs: Math.round(n.domContentLoadedEventEnd),
                 loadMs: Math.round(n.loadEventEnd) } : {};
  });
  const firstScreen = await site.evaluate(() => ({
    kicker: (document.querySelector('header .kicker') || {}).textContent || '',
    h1: (document.querySelector('h1') || {}).textContent || '',
    tagline: (document.querySelector('.tagline') || {}).textContent || '',
    ctaText: (document.getElementById('play') || {}).textContent || '',
    ctaVisible: !!(document.getElementById('play') &&
                   document.getElementById('play').offsetParent !== null),
    footerCount: (document.getElementById('n') || {}).textContent || '',
    links: Array.from(document.querySelectorAll('a[href]')).map(a => a.href),
  }));
  const countBefore = await site.evaluate(() =>
    fetch('/api/signups/count').then(r => r.json()).then(d => d.count).catch(() => null));
  out.stages.landing = {
    url: SITE, httpStatus: resp.status(), wallClockLoadMs: siteLoadMs, nav,
    firstScreen, signupCountBefore: countBefore,
    fiveSecondRead: firstScreen.kicker + ' / ' + firstScreen.h1 + ' / ' +
                    firstScreen.tagline + ' / CTA: "' + firstScreen.ctaText + '"',
  };
  console.log('landing: HTTP ' + resp.status() + ', load ' + siteLoadMs + ' ms, nav ' +
    JSON.stringify(nav));
  console.log('first screen: ' + out.stages.landing.fiveSecondRead);
  console.log('links on page: ' + JSON.stringify(firstScreen.links) +
    '  signup count before: ' + countBefore);

  // ============ STAGE 2: the demo door ============
  console.log('=== STAGE 2: click the play CTA ===');
  const doorP = context.waitForEvent('page', { timeout: 10000 }).then(p => {
    wire(p, 'game');
    return p;
  });
  await site.click('#play');
  let game = null, doorMode = 'NO DOOR OPENED WITHIN 10 s';
  try {
    game = await doorP;
    doorMode = 'new tab (window.open _blank)';
    await game.waitForLoadState('load', { timeout: 20000 });
  } catch (e) {
    doorMode = 'no popup: ' + e.message.split('\n')[0];
  }
  const siteUrlAfter = site.url();
  let door = { mode: doorMode, openerStillOnSite: siteUrlAfter === SITE + '/' };
  if (game) {
    const gt0 = Date.now();
    await game.waitForLoadState('load', { timeout: 20000 }).catch(() => {});
    const gameLoadMs = Date.now() - gt0;
    const gnav = await game.evaluate(() => {
      const n = performance.getEntriesByType('navigation')[0];
      return n ? { ttfbMs: Math.round(n.responseStart),
                   domContentLoadedMs: Math.round(n.domContentLoadedEventEnd) } : {};
    }).catch(() => ({}));
    door.url = game.url();
    door.gameNav = gnav;
    door.gameArrivalWallMs = gameLoadMs;
    door.title = await game.title().catch(() => '?');
    await sleep(2500);                                // world attach (topology+verts)
    await game.screenshot({ path: SHOTS + '/02_game_start_screen.png' });
  }
  out.stages.door = door;
  console.log('door: ' + JSON.stringify(door));

  // ============ STAGE 3: PLAY -- two lessons ============
  console.log('=== STAGE 3: play (name ' + CAMERA_NAME + ') ===');
  const gameOpenAtS = (Date.now() - T0) / 1000;
  const play = { cameraName: CAMERA_NAME, gameOpenAtS };
  if (!game) {
    play.fatal = doorMode;
    out.stages.play = play;
  } else {
    await game.fill('#name-input', CAMERA_NAME);
    await game.click('#play-btn');
    await game.waitForSelector('#screen-play.on', { timeout: 15000 });
    await sleep(2500);                                // world attach beat
    const introShown = await game.isVisible('#intro-overlay');
    play.introOverlayShown = introShown;
    await game.screenshot({ path: SHOTS + '/03_game_intro_overlay.png' });
    if (introShown) { await game.click('#intro-begin'); }
    await sleep(1000);

    const judgeLine = () => game.evaluate(() =>
      (document.getElementById('judge-debug') || {}).textContent || '');
    const judge = async () => {
      const m = (await judgeLine()).match(/judge: (\S+) phase=(\S+) goalMet=(\S+) passed=(\S+)/);
      return m ? { id: m[1], phase: m[2], goalMet: m[3] === 'true', passed: m[4] === 'true' }
               : { id: '?', phase: '?', goalMet: false, passed: false };
    };
    const verdictText = () => game.evaluate(() =>
      (document.getElementById('verdict') || {}).textContent || '');
    const lessonTitle = () => game.evaluate(() =>
      (document.getElementById('lesson-title') || {}).textContent || '');
    const key = async k => { await game.keyboard.press(k); await sleep(160); };
    const waitPassed = async capMs => {
      const s0 = Date.now();
      while (Date.now() - s0 < capMs) {
        const j = await judge();
        const v = await verdictText();
        if (j.passed || /PASSED/.test(v)) return { passed: true, ms: Date.now() - s0, judge: j };
        await sleep(500);
      }
      return { passed: false, ms: Date.now() - s0, judge: await judge(),
               verdict: await verdictText() };
    };

    // -- LESSON 1: WAKE THE CELL --------------------------------------
    const l1 = { title: await lessonTitle() };
    console.log('L1 title: ' + l1.title);
    // the stranger's first instinct: CLICK the creature on the canvas
    const box = await game.locator('#gl').boundingBox();
    const cx = box.x + box.width / 2, cy = box.y + box.height * 0.55;
    await game.mouse.move(cx, cy); await sleep(200);
    await game.mouse.down(); await sleep(150); await game.mouse.up();
    await sleep(1200);
    l1.clickProbe = {
      atPx: [Math.round(cx), Math.round(cy)],
      bloodAfter: await game.evaluate(() =>
        (document.getElementById('blood') || {}).textContent || ''),
      verdictAfter: await verdictText(),
    };
    console.log('L1 blind click -> blood: ' + l1.clickProbe.bloodAfter.slice(0, 140));
    await game.keyboard.press('Escape'); await sleep(600);   // clean hand
    // the taught rail: '=' raises the hand to 50000 N, SPACE presses the target
    for (let i = 0; i < 15; i++) await key('=');
    l1.forceN = await game.evaluate(() => Number(document.getElementById('force').value));
    await game.keyboard.down(' ');
    await sleep(2500);
    l1.bloodMidPress = await game.evaluate(() =>
      (document.getElementById('blood') || {}).textContent || '');
    l1.judgeMidPress = await judgeLine();
    await game.screenshot({ path: SHOTS + '/04_lesson1_pressing.png' });
    await game.keyboard.up(' ');
    await game.keyboard.press('Escape');
    const r1 = await waitPassed(90000);
    l1.pass = r1;
    l1.verdictAfter = await verdictText();
    await game.screenshot({ path: SHOTS + '/05_lesson1_passed.png' });
    play.lesson1 = l1;
    console.log('L1 pass: ' + JSON.stringify({ passed: r1.passed, in: r1.ms + 'ms',
      judge: r1.judge, verdict: l1.verdictAfter }));

    // -- LESSON 2: THE GENTLE HAND ------------------------------------
    await key(']');
    const l2 = { title: await lessonTitle() };
    console.log('L2 title: ' + l2.title);
    for (let i = 0; i < 22; i++) await key('-');      // 50000 -> 6000 N (< 8000 cap)
    l2.forceN = await game.evaluate(() => Number(document.getElementById('force').value));
    await game.keyboard.down(' ');
    await sleep(2000);
    l2.bloodMidPress = await game.evaluate(() =>
      (document.getElementById('blood') || {}).textContent || '');
    l2.judgeMidPress = await judgeLine();
    await game.screenshot({ path: SHOTS + '/06_lesson2_pressing.png' });
    await game.keyboard.up(' ');
    await game.keyboard.press('Escape');
    const r2 = await waitPassed(90000);
    l2.pass = r2;
    l2.verdictAfter = await verdictText();
    await game.screenshot({ path: SHOTS + '/07_lesson2_passed.png' });
    play.lesson2 = l2;
    console.log('L2 pass: ' + JSON.stringify({ passed: r2.passed, in: r2.ms + 'ms',
      judge: r2.judge, verdict: l2.verdictAfter }));

    // -- save progress (the page's own save flow) ----------------------
    await game.click('#save-btn');
    await sleep(1500);
    play.saved = await game.evaluate(n =>
      fetch('/api/progress?name=' + encodeURIComponent(n))
        .then(r => r.json()).then(d => ({ lessons: Object.keys(d.lessons || {}) }))
        .catch(e => ({ error: String(e) })), CAMERA_NAME);
    console.log('progress saved: ' + JSON.stringify(play.saved));
    out.stages.play = play;
  }

  // ============ STAGE 4: back to the site, SIGN UP ============
  console.log('=== STAGE 4: signup ' + SIGNUP.email + ' ===');
  await site.bringToFront();
  await site.locator('#name').scrollIntoViewIfNeeded();
  await site.fill('#name', SIGNUP.name);
  await site.fill('#email', SIGNUP.email);
  await site.screenshot({ path: SHOTS + '/08_signup_filled.png' });
  await site.click('#join');
  let noteText = '', noteGood = false;
  try {
    await site.waitForFunction(
      () => { const n = document.getElementById('note');
              return n && n.className === 'good' && n.textContent.length > 0; },
      null, { timeout: 10000 });
    noteText = await site.evaluate(() => document.getElementById('note').textContent);
    noteGood = true;
  } catch (e) {
    noteText = await site.evaluate(() =>
      (document.getElementById('note') || {}).textContent || '(no note)');
  }
  await sleep(1200);                                  // count refresh beat
  const countAfter = await site.evaluate(() =>
    (document.getElementById('n') || {}).textContent || '?');
  await site.screenshot({ path: SHOTS + '/09_signup_done.png' });
  out.stages.signup = { ...SIGNUP, noteGood, noteText, countAfter };
  console.log('signup: noteGood=' + noteGood + ' note="' + noteText +
    '" footer count now ' + countAfter);

  // ============ health ledger ============
  out.sessionWallS = Math.round((Date.now() - T0) / 10) / 100;
  out.urlCounts = T.urlCounts;
  out.health = {
    consoleErrors: T.consoleErrors, pageErrors: T.pageErrors,
    badResponses: T.badResponses, failedRequests: T.failedRequests,
    httpRequestsTotal: T.reqCount, rateLimit429s: T.badResponses.filter(r => r.status === 429).length,
    notes: T.notes,
  };
  const lessonsOk = play.lesson1 && play.lesson2 &&
                    play.lesson1.pass.passed && play.lesson2.pass.passed;
  out.verdict = (door.mode.indexOf('new tab') === 0 && lessonsOk && noteGood &&
                 T.pageErrors.length === 0) ? 'PASS' : 'FAIL';
  fs.writeFileSync(SHOTS + '/transcript.json', JSON.stringify(out, null, 1));
  console.log('=== FUNNEL VERDICT: ' + out.verdict + ' ===');
  console.log('health: consoleErrors=' + T.consoleErrors.length +
    ' pageErrors=' + T.pageErrors.length + ' http>=400=' + T.badResponses.length +
    ' failedReqs=' + T.failedRequests.length + ' requests=' + JSON.stringify(T.reqCount));
  await browser.close();
  process.exit(out.verdict === 'PASS' ? 0 : 1);
})().catch(e => {
  console.error('FUNNEL WALK FAILED:', e.message);
  fs.writeFileSync(SHOTS + '/transcript.json', JSON.stringify(
    { verdict: 'FAIL', fatal: e.message, health: T }, null, 1));
  process.exit(1);
});
