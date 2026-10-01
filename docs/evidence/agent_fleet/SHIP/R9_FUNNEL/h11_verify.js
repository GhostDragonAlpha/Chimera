/* h11_verify.js -- H11 "store-package": package verification, headless.
   After the D3 og:image fix, the copy refresh, and the D4 door fix:
     1. landing loads with ZERO console/page errors and no HTTP >= 400;
     2. every og/meta tag resolves -- og:image (616x353 + 460x215) HTTP 200;
     3. the hero says what the product IS (ten lessons, press-answer, heal);
     4. PLAY THE DEMO still opens the game shell on 8206 (fresh tab, 200);
     5. the signup flow still records (one H11 FUNNEL-TEST probe row);
     6. the PII guard still refuses signups.jsonl (404).
   Run: node docs/evidence/agent_fleet/SHIP/R9_FUNNEL/h11_verify.js */
const fs = require('fs');
const { chromium } = require('E:/PythonChimera/node_modules/playwright-core');

const SITE = 'http://127.0.0.1:8210';
const OUT = 'E:/ChimeraWork/slot-01/docs/evidence/agent_fleet/SHIP/R9_FUNNEL';
const T = {
  at: new Date().toISOString(), runner: 'H11-store-package',
  consoleErrors: [], consoleWarns: [], pageErrors: [], badResponses: [],
  failedRequests: [], checks: {}, notes: [],
};
const sleep = ms => new Promise(r => setTimeout(r, ms));
function check(name, ok, detail) {
  T.checks[name] = { ok, detail: detail === undefined ? null : detail };
  console.log((ok ? 'PASS ' : 'FAIL ') + name + (detail !== undefined ? '  -> ' + JSON.stringify(detail) : ''));
}

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1600, height: 900 } });
  const page = await ctx.newPage();
  page.on('console', m => {
    if (m.type() === 'error') T.consoleErrors.push(m.text());
    if (m.type() === 'warn') T.consoleWarns.push(m.text());
  });
  page.on('pageerror', e => T.pageErrors.push(e.message));
  page.on('response', r => { if (r.status() >= 400) T.badResponses.push(r.status() + ' ' + r.url()); });
  page.on('requestfailed', r => T.failedRequests.push(r.url()));

  // -- 1. cold landing ----------------------------------------------------
  const t0 = Date.now();
  const resp = await page.goto(SITE, { waitUntil: 'load' });
  const loadMs = Date.now() - t0;
  check('site_200', resp.status() === 200, { status: resp.status(), loadMs });

  // -- 2. og / meta tags resolve ------------------------------------------
  const meta = await page.evaluate(() => ({
    title: document.title,
    description: document.querySelector('meta[name="description"]')?.content || null,
    ogTitle: document.querySelector('meta[property="og:title"]')?.content || null,
    ogDesc: document.querySelector('meta[property="og:description"]')?.content || null,
    ogType: document.querySelector('meta[property="og:type"]')?.content || null,
    ogImages: [...document.querySelectorAll('meta[property="og:image"]')].map(m => m.content),
    ogDims: {
      w: document.querySelector('meta[property="og:image:width"]')?.content || null,
      h: document.querySelector('meta[property="og:image:height"]')?.content || null,
    },
    ogAlt: document.querySelector('meta[property="og:image:alt"]')?.content || null,
  }));
  check('og_title', !!meta.ogTitle, meta.ogTitle);
  check('og_description', !!meta.ogDesc, meta.ogDesc);
  check('og_type_website', meta.ogType === 'website', meta.ogType);
  check('meta_description', !!meta.description, meta.description);
  check('og_image_count', meta.ogImages.length === 2, meta.ogImages);

  for (const img of meta.ogImages) {
    const r = await page.request.get(SITE + '/' + img);
    const buf = await r.body();
    check('og_image_200:' + img, r.status() === 200 && buf.length > 1000,
          { status: r.status(), bytes: buf.length, type: r.headers()['content-type'] });
  }

  // -- 3. hero copy says what the product IS -------------------------------
  const hero = await page.evaluate(() => document.querySelector('header').innerText);
  check('hero_press_answer', /press it anywhere and the pressure answers/i.test(hero));
  check('hero_watch_it_heal', /watch it heal/i.test(hero));
  check('hero_ten_lessons', /ten short lessons/i.test(hero));
  const cards = await page.evaluate(() => [...document.querySelectorAll('.card h3')].map(h => h.textContent));
  check('ten_lessons_card', cards.some(c => /ten lessons/i.test(c)), cards);

  await page.screenshot({ path: OUT + '/h11_landing_after.png' });

  // -- 4. PLAY THE DEMO door ------------------------------------------------
  const [popup] = await Promise.all([
    ctx.waitForEvent('page', { timeout: 10000 }),
    page.click('#play'),
  ]);
  await popup.waitForLoadState('load', { timeout: 15000 });
  const door = popup.url();
  const doorStatus = await popup.evaluate(() => document.title);
  check('demo_door', /^http:\/\/127\.0\.0\.1:8206\/?$/.test(door), { door, title: doorStatus });
  await popup.close(); // stop its poll loop; the door check is complete

  // -- 5. signup probe (H11 FUNNEL-TEST) ------------------------------------
  await page.fill('#name', 'H11 Funnel Test');
  await page.fill('#email', 'funnel-test@example.com');
  const countBefore = await (await page.request.get(SITE + '/api/signups/count')).json();
  await page.click('#join');
  await page.waitForFunction(() => document.getElementById('note').textContent.length > 0, null, { timeout: 8000 });
  const note = await page.evaluate(() => document.getElementById('note').textContent);
  const noteClass = await page.evaluate(() => document.getElementById('note').className);
  await sleep(700); // let the refresh of the footer counter land
  const countAfter = await (await page.request.get(SITE + '/api/signups/count')).json();
  check('signup_recorded', noteClass === 'good' && countAfter.count === countBefore.count + 1,
        { note, before: countBefore.count, after: countAfter.count });
  await page.screenshot({ path: OUT + '/h11_signup_probe.png' });

  // -- 6. PII guard still refuses the store ---------------------------------
  const pii = await page.request.get(SITE + '/signups.jsonl');
  check('signups_jsonl_refused', pii.status() === 404, pii.status());

  // -- health ---------------------------------------------------------------
  check('console_errors_zero', T.consoleErrors.length === 0, T.consoleErrors);
  check('no_failed_selftest', !T.consoleWarns.some(w => /self-test FAILED/.test(w)), T.consoleWarns);
  check('page_errors_zero', T.pageErrors.length === 0, T.pageErrors);
  check('no_http_400plus', T.badResponses.length === 0, T.badResponses);
  check('no_failed_requests', T.failedRequests.length === 0, T.failedRequests);

  T.landingMeta = meta;
  fs.writeFileSync(OUT + '/h11_transcript.json', JSON.stringify(T, null, 2));
  const failed = Object.entries(T.checks).filter(([, v]) => !v.ok);
  console.log('\nH11 VERIFY: ' + (failed.length === 0 ? 'PASS (' + Object.keys(T.checks).length + ' checks)' :
    'FAIL (' + failed.length + '/' + Object.keys(T.checks).length + ' failed: ' + failed.map(([k]) => k).join(', ') + ')'));
  await browser.close();
  process.exit(failed.length === 0 ? 0 : 1);
})().catch(e => { console.error('RUNNER ERROR:', e); process.exit(2); });
