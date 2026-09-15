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

   D1 EXTENSION (2026-09-14, playbook rule 8 — extra driver commands, blind
   rules untouched): {"do":"keydown","key":"Space"} / {"do":"keyup","key":"Space"}.
   The page binds a press to SPACE keydown and ends it on keyup (H7 fix), so a
   proper S4 press-HOLD-release needs down and up as separate commands; the
   playbook's {"do":"key"} fires an instant down+up and cannot hold.
   Everything below between the EXTENSION BEGIN/END markers is R8_R4_PLAYBOOK
   PLAYBOOK.md Appendix A, verbatim.
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
      /* ── D1 EXTENSION BEGIN (playbook rule 8): hold-able keyboard press ── */
      case 'keydown': await page.keyboard.down(c.key); say({ ok: true, did: 'keydown', key: c.key }); break;
      case 'keyup': await page.keyboard.up(c.key); say({ ok: true, did: 'keyup', key: c.key }); break;
      /* ── D1 EXTENSION END ── */
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
