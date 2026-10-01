# R8 / R4 JUDGE PLAYBOOK — blind buyer test of a live web demo

You are a **stranger with a wallet**. You know nothing about this product except
what this document says and what the page itself shows you. Your job: PLAY it
like a buyer who found the link, then deliver a pay/no-pay verdict.

This document is your ENTIRE briefing. It is self-contained. You need zero
codebase context, and you must not acquire any (see THE BLIND RULES).

- The product: **http://127.0.0.1:8206**
- Your tools: a shell with `node` + the `playwright` npm package, driving
  **headless Chrome** (`channel: 'chrome'`, `headless: true`).
- Your output: one verdict block (template at the end) + session artifacts.

---

## 1. THE BLIND RULES (violating any of these voids the verdict)

1. **The rendered page is your only window into the product.** You may look at
   it, click it, drag it, type into it, and read the text and labels it
   displays. That is all.
2. **FORBIDDEN:** reading any file of any repository, `view-source:`,
   devtools, fetching the page's HTML/JS/CSS (curl/wget/HTTP clients),
   inspecting network traffic bodies, reading JS variables or game state via
   `evaluate`, or web-searching for the product. If you would not see it on
   the screen as a buyer, you may not know it.
3. The `eval` command in the driver below is allowed **only** to read visible
   text (`document.body.innerText`) and element geometry (bounding boxes of
   things you can already see). Never to inspect internals.
4. **No questions to any human or other agent** about the product. Anything
   the page does not tell you is a *stall* — record it and move on.
5. **No hints exist.** Whatever controls the page wants you to use, the page
   must teach you. If you had to guess, that is a stall — write down the guess.
6. If the page errors or freezes: screenshot it, wait **60 seconds**, reload
   once, continue. If it is still broken, finish the session anyway and say so
   in the verdict.
7. Playwright screenshots do **not** capture the mouse cursor — your shots
   will show touches with no visible pointer. Judge legibility by what the
   PAGE shows in response (labels, text, scene), not by the pointer.
8. You may extend the driver (Appendix A) with extra commands if the session
   needs them; the blind rules above still apply to whatever you add.

## 2. SETUP (one time, ~5 minutes)

Work in a scratch directory of your choice (e.g. `%TEMP%\judge_r4\`). You will
create: `shots/` (screenshots), `cmd/` (command box), `done/`, `resp.jsonl`,
`session.log`.

2.1. Check tooling **from inside the scratch dir** (module resolution is
per-directory; a check from another directory can pass while the driver
still fails here):

```bash
cd <scratch dir>
node -e "require('playwright'); console.log('ok')"
```

If that fails: `npm i playwright` in the scratch dir (the `playwright`
package alone is enough — you launch the installed Chrome via
`channel: 'chrome'`, no browser download needed), then re-run the check.

2.2. Save the driver script below as `judge_drive.js` (verbatim from
Appendix A — it is complete, nothing else to install).

2.3. Start it in the background from the scratch dir:

```bash
node judge_drive.js http://127.0.0.1:8206 .
```

It launches headless Chrome, opens the URL, and then waits for **command
files**: drop a file containing one JSON command per line into `cmd/` (any
filename, e.g. `c001.json`); the driver executes them in order, moves the file
to `done/`, and appends one JSON response line per command to `resp.jsonl`.
Console errors, page crashes, and failed requests are logged with timestamps
in `session.log`. Stop the session with `{"do":"quit"}`.

## 3. SESSION FLOW (minimum 10 minutes hands-on before the verdict)

Do these in order. Screenshot name format: `NN_name.png` (01, 02, ...).

- **S1 · Cold landing.** Screenshot `01_landing` immediately, wait 5 s,
  screenshot `02_landing_settled`. Then, BEFORE touching anything, write your
  first impressions: What do you think this is? What would you click first and
  why? (If you can't tell what to click first — that's a stall.)
- **S2 · Self-taught controls.** Explore using only what the page shows. Log
  every wrong guess and every hesitation over ~10 s as a stall (with a
  screenshot at the moment of confusion).
- **S3 · Lessons — the core test.** The page offers some form of lesson / task
  / exercise (call them whatever the page calls them). **Complete at least 3
  of them to a clear pass or fail**, in whatever order the page allows. For
  each: what the page asked, what you did, what the page said when you
  finished (exact wording).
- **S4 · The press test (required).** Find a way to press / squish / poke the
  creature — the page itself must show you how; if you cannot find it in 3
  minutes, that is a stall, try again later, but you may not skip S4. Press
  it, **hold the press for several seconds while watching**, then release and
  **keep watching until the creature settles**. Record exactly what happened
  during the press and after the release.
- **S5 · Free play.** Anything else the page offers — try it. More lessons
  welcome.
- **S6 · Quit** (`{"do":"quit"}`) and write the verdict block.

**Stall = anything that cost you >10 seconds, any wrong guess, any button that
did nothing, any text you had to reread, any load over ~3 s, anything you'd
blame the product for as a buyer.** When in doubt, it's a stall. A stall
needs: step number, what you were trying to do, what you tried, screenshot,
how you got unstuck (or didn't).

## 4. VERDICT (fill the template verbatim, your own words, no polishing)

Answer as a buyer, not as an engineer. Exact template:

```markdown
## VERDICT — judge: <your name>, date: <date>

### Buyer answers
1. **What is this?** — <your words>
2. **Would you pay $15-20 for it?** — yes/no + <why, one or two sentences>
3. **What's missing?** — <list>
4. **What would you need to make it worth $25?** — <list, be specific>

### Structured verdict
- PAY ($15-20): yes / no
- WOULD PAY $25: yes / no
- NOVELTY: <n>/10 — <one line: what it's like, what you've never seen before>

### QUOTES (verbatim from your answers above, pick the 3 sharpest)
- "<quote>"
- "<quote>"
- "<quote>"

### Mechanics witnessed
- Lessons completed: <n> — <pass/fail + the page's exact result text, per lesson>
- Press test: <performed? what happened during the hold, what happened after release>
- Stalls encountered: <count> — <one line each>
- Page errors: <any>

### Honesty note
- <Did you know this project before today? Say yes/no and one line. A judge
  who peeked at anything forbidden must say so here.>
```

## 5. ARTIFACTS

Keep in your scratch dir, hand all of it to the operator (or, if you have
write access to `docs/evidence/agent_fleet/SHIP/R8_R4_PLAYBOOK/judges/<your
name>/` in the demo's repo, copy it there — writing is allowed, reading is
not):

- `verdict.md` — the verdict block
- `session.log`, `resp.jsonl` — the driver's logs
- `shots/` — all screenshots (minimum: every stall + `01_landing` +
  one shot per lesson result + press-hold and after-release shots)
- `notes.md` (optional) — your S1 first impressions and running notes

---

## Appendix A — `judge_drive.js` (verbatim, complete)

```js
#!/usr/bin/env node
/* Blind-judge browser harness. Playwright + headless Chrome (channel 'chrome').
   Usage:  node judge_drive.js <startUrl> <workDir>
   Drop files with one JSON command per line into <workDir>/cmd/ — they run in
   order, files move to done/, responses append to resp.jsonl.
   Commands:
     {"do":"shot","name":"01_landing"}            screenshot -> shots/
     {"do":"click","x":720,"y":450}               left click at viewport pixel
     {"do":"move","x":720,"y":450,"steps":10}     mouse move (for drags: move, down, move..., up)
     {"do":"down"} {"do":"up"}                    mouse button press/release
     {"do":"wheel","dx":0,"dy":-240}              scroll / wheel-zoom
     {"do":"key","key":"ArrowLeft"}               keyboard press
     {"do":"type","text":"hello"}                 type text
     {"do":"clickText","text":"Play"}             click first visible text match
     {"do":"text","max":3000}                     read visible page text (allowed: it is what a buyer sees)
     {"do":"eval","js":"document.body.innerText"} allowed ONLY for visible text / bounding boxes
     {"do":"wait","ms":1500}                      wait
     {"do":"quit"}                                close browser and exit
*/
'use strict';
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const [, , startUrl, workDir = '.'] = process.argv;
if (!startUrl) { console.error('usage: node judge_drive.js <url> [workDir]'); process.exit(1); }
const cmdDir = path.join(workDir, 'cmd'), doneDir = path.join(workDir, 'done'), shotDir = path.join(workDir, 'shots');
for (const d of [cmdDir, doneDir, shotDir]) fs.mkdirSync(d, { recursive: true });
const resp = fs.createWriteStream(path.join(workDir, 'resp.jsonl'), { flags: 'a' });
const slog = fs.createWriteStream(path.join(workDir, 'session.log'), { flags: 'a' });
const stamp = () => new Date().toISOString();
const say = (o) => { const line = JSON.stringify(o); process.stdout.write(line + '\n'); resp.write(line + '\n'); slog.write(stamp() + ' ' + line + '\n'); };

(async () => {
  const t0 = Date.now();
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newContext({ viewport: { width: 1440, height: 900 } }).then(c => c.newPage());
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') slog.write(stamp() + ' console.' + m.type() + ': ' + m.text().slice(0, 300) + '\n'); });
  page.on('pageerror', e => slog.write(stamp() + ' PAGEERROR: ' + String(e).slice(0, 400) + '\n'));
  page.on('requestfailed', r => slog.write(stamp() + ' REQFAIL: ' + r.url().slice(0, 200) + ' ' + (r.failure() && r.failure().errorText) + '\n'));

  await page.goto(startUrl, { waitUntil: 'load', timeout: 30000 })
    .then(() => say({ ok: true, did: 'goto', url: startUrl, ms: Date.now() - t0 }))
    .catch(e => say({ ok: false, did: 'goto', error: String(e).split('\n')[0] }));

  const run = async (c) => {
    switch (c.do) {
      case 'shot': { const f = path.join(shotDir, String(c.name || 'shot').replace(/[^\w.-]/g, '_') + '.png'); await page.screenshot({ path: f, fullPage: !!c.fullPage }); say({ ok: true, did: 'shot', file: f }); break; }
      case 'click': await page.mouse.click(c.x, c.y, { button: c.button || 'left', clickCount: c.count || 1 }); say({ ok: true, did: 'click', x: c.x, y: c.y }); break;
      case 'move': await page.mouse.move(c.x, c.y, { steps: c.steps || 8 }); say({ ok: true, did: 'move', x: c.x, y: c.y }); break;
      case 'down': await page.mouse.down({ button: c.button || 'left' }); say({ ok: true, did: 'down' }); break;
      case 'up': await page.mouse.up({ button: c.button || 'left' }); say({ ok: true, did: 'up' }); break;
      case 'wheel': await page.mouse.wheel(c.dx || 0, c.dy || 0); say({ ok: true, did: 'wheel' }); break;
      case 'key': await page.keyboard.press(c.key); say({ ok: true, did: 'key', key: c.key }); break;
      case 'type': await page.keyboard.type(c.text || '', { delay: c.delay || 0 }); say({ ok: true, did: 'type' }); break;
      case 'clickText': { const el = page.getByText(c.text, { exact: !!c.exact }).first(); await el.click({ timeout: c.timeout || 5000 }); const b = await el.boundingBox().catch(() => null); say({ ok: true, did: 'clickText', text: c.text, box: b }); break; }
      case 'text': { const t = await page.evaluate(() => document.body.innerText); say({ ok: true, did: 'text', text: String(t).slice(0, c.max || 3000) }); break; }
      case 'eval': say({ ok: true, did: 'eval', result: JSON.stringify(await page.evaluate(c.js)).slice(0, c.max || 2000) }); break;
      case 'wait': await page.waitForTimeout(c.ms || 1000); say({ ok: true, did: 'wait', ms: c.ms || 1000 }); break;
      case 'quit': say({ ok: true, did: 'quit' }); await browser.close(); process.exit(0);
      default: say({ ok: false, error: 'unknown command', cmd: c.do });
    }
  };

  say({ ok: true, did: 'ready', cmdDir });
  let quitting = false;
  while (!quitting) {
    const files = fs.readdirSync(cmdDir).filter(f => f.endsWith('.json')).sort();
    for (const f of files) {
      const full = path.join(cmdDir, f);
      let lines = [];
      try { lines = fs.readFileSync(full, 'utf8').split(/\r?\n/).filter(s => s.trim()); } catch (e) { say({ ok: false, error: 'unreadable cmd file', file: f }); }
      for (const line of lines) {
        let c; try { c = JSON.parse(line); } catch { say({ ok: false, error: 'bad JSON', line: line.slice(0, 120) }); continue; }
        try { await run(c); } catch (e) { say({ ok: false, cmd: c.do, error: String(e).split('\n')[0].slice(0, 250) }); }
        if (c.do === 'quit') { quitting = true; break; }
      }
      try { fs.renameSync(full, path.join(doneDir, f)); } catch (e) { try { fs.unlinkSync(full); } catch (_) {} }
    }
    if (!quitting) await new Promise(r => setTimeout(r, 400));
  }
})().catch(e => { say({ ok: false, fatal: String(e).split('\n')[0] }); process.exit(1); });
```

## Appendix B — pre-flight checklist (copy into your notes)

- [ ] tooling check passed (`node -e "require('playwright')"`)
- [ ] driver started, `resp.jsonl` shows `did:"goto"` then `did:"ready"`
- [ ] S1 cold-landing shots + first impressions written
- [ ] S2 controls self-taught, stalls logged
- [ ] S3 at least 3 lessons to pass/fail, page's exact result text captured
- [ ] S4 press-hold-release-recover witnessed and described
- [ ] S5 free play done
- [ ] verdict block filled, honesty note included
- [ ] artifacts collected
