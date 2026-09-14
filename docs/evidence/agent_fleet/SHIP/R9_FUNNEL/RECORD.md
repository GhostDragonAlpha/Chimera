# R9 FUNNEL E2E — the stranger walk (fleet agent H6 "funnel-e2e")

2026-09-14 · workspace `E:\ChimeraWork\slot-01` · branch `astra/tasks/matter-kernel-format-01` · HEAD `09e71b55`
Method: headless Playwright, `channel: 'chrome'`, viewport 1600x900, real clicks / keys / form fills only.
Runner: `funnel_e2e.js` in this directory. Transcript of the final run: `transcript.json`.

## VERDICT: PASS

The falsifier: *a stranger with zero developer knowledge can go site → demo → 2 lessons →
signup, and the signup row exists in the store.* The final run (camera name `FunnelVisitor`)
did exactly that with **zero console errors, zero page errors, zero HTTP >= 400, zero failed
requests** — and the row is on disk. One major deployment risk was found and named (D1); it
does not block a solo customer, but must be read before the domain goes live.

---

## 1. Cold landing — http://127.0.0.1:8210

- HTTP 200, `load` in **31 ms** wall clock (nav timing: TTFB 2 ms, DCL 8 ms, load 28 ms). No slow loads anywhere (nothing above 110 ms in any run).
- **The 5-second read passes.** Above the fold, in order: kicker "A SERIOUS INDIE PHYSICS GAME" · H1 "CHIMERA" · tagline "a creature of sealed water cells. touch it anywhere, and it answers." · a gold-bordered **PLAY THE DEMO** button. A stranger knows what this is and where to play inside 5 seconds. (Screenshot `01_site_landing_cold.png`.)
- CTA is a real `<button>` (not a link) that opens the demo door — obvious, one candidate, no competing CTAs.
- Footer counter "join N explorers" read live from `/api/signups/count` (3 on landing, before this run's signup).
- **Dead links: none** — the page carries zero `<a href>` anchors; the only door is the CTA button. `robots.txt` serves 200.

## 2. The demo door (site → game)

- Clicking PLAY THE DEMO opens a **new tab** at **`http://127.0.0.1:8206/`** (`window.open(..., "_blank", "noopener")`); the site tab stays put — a stranger can come back to sign up. Screenshot `02_game_start_screen.png`.
- The door is **derived from the serving hostname** (`demoUrl()` in `tools/website/index.html`), not a constant. Verified working URLs:
  - `http://127.0.0.1:8210` → door `http://127.0.0.1:8206` ✓ (this walk)
  - `http://localhost:8206` ✓ responds 200 (curl; browser IPv4 fallback)
  - `http://[::1]:8206` ✗ **connection refused** — the shell binds 127.0.0.1 only. Browsers fall back to IPv4, so `localhost` visitors work in practice; noted for the runbook (D4).
- Transition health: game page title "CHIMERA — touch the living physics", TTFB 8 ms, DCL 51 ms. **No CORS errors, no mixed content** (site and door are both plain HTTP on the same host; all game API calls are same-origin).

## 3. PLAY — two lessons, the stranger's path

Start screen: name field ("your name (your camera's name)") → PLAY → first-run intro overlay
(drag/click/SPACE, 1–5 lessons) → "begin". Then the lesson rail on the right drives everything.
No stall a stranger would hit: the intro names the controls, each lesson's card states its goal
and hint, and the SPACE rail presses the lesson's own target.

- **Lesson 1 — WAKE THE CELL**: taught rail (`=` to raise the hand to 50,000 N, SPACE to press the belly, ESC to let go) → judge `goalMet=true` mid-press, **PASSED 4.1 s** after release: "PASSED — you felt the water. it was always there." (Screenshots `04_lesson1_pressing.png`, `05_lesson1_passed.png`.)
- **Lesson 2 — THE GENTLE HAND**: `]` advances the rail, 22 × `-` slides the hand to 6,000 N (under the 8,000 N cap; the meter draws the "gentle ≤" zone), SPACE presses the foot target — mid-press cell 0 read 5.38 MPa vs the 0.05 MPa bar — ESC, **PASSED 4.1 s** after release. (Screenshots `06_lesson2_pressing.png`, `07_lesson2_passed.png`.)
- "save progress" wrote `progress/FunnelVisitor.json` with both lessons. **The world remembers a returning visitor by name** (run 3 re-entered as `FunnelGuest` and lesson 2 said "yours already" — correct product behavior, caused by run 2's save under that name).
- Stranger stalls found (minor): **D2** below — a blind first click on the creature gives no visible response.

## 4. SIGNUP — funnel-test@example.com

- Back on the still-open site tab: scrolled to "join the list", filled name `H6 Funnel Test`, email `funnel-test@example.com` (screenshot `08_signup_filled.png`), clicked Join.
- The note turned gold: **"you're on the list. the creature will be waiting."** and the footer count went **4 → 5**. (Screenshot `09_signup_done.png`.)
- **The store:** `tools/website/server.py` appends one JSON line per submission to
  **`E:\ChimeraWork\slot-01\tools\website\signups.jsonl`** (name + email + timestamp; the file
  is never web-readable — path guard in the server refuses it). Rows on disk after the walk:

```
{"name": "Alan", "email": "alan@chimera.game", "at": "2026-09-13 14:34:33"}
{"name": "H6 Funnel Test", "email": "funnel-test@example.com", "at": "2026-09-14 07:24:31"}   <- run 1
{"name": "H6 Funnel Test", "email": "funnel-test@example.com", "at": "2026-09-14 07:31:15"}   <- run 2
{"name": "H6 Funnel Test", "email": "funnel-test@example.com", "at": "2026-09-14 07:34:27"}   <- run 3
{"name": "H6 Funnel Test", "email": "funnel-test@example.com", "at": "2026-09-14 07:35:27"}   <- run 4 (the clean PASS)
```

  `GET /api/signups/count` returns 5 ✓. Each run appended one row — the server deliberately
  keeps duplicate lines for a returning email ("a returning email earns a second line,
  honestly"). Four clearly-marked test rows remain in the live store; the operator may want to
  prune three before going public (left in place as evidence).

## 5. Health ledger (final run)

- Console errors: **0** · page errors: **0** · HTTP >= 400: **0** · failed requests: **0**.
- Requests: site page 5 total; game page 254 over its ~60 s session ≈ **254 req/min** — matches the documented solo poll (verts 3 Hz + state 1.4 Hz = 264/min) and sits far under the shell's 600/min stream bucket. **No rate-limit trip in a normal solo session** (runs 3 and 4: zero 429s).

---

## Run history (the walk ran four times)

| run | camera | L1 | L2 | signup | note |
|---|---|---|---|---|---|
| 1 | FunnelTester | PASS 4.1 s | HELD — 429 storm | ✓ row 07:24:31 | 46 × 429 |
| 2 | FunnelGuest | HELD — 429 storm (90 s cap) | PASS 7.1 s (caught a quiet window) | ✓ row 07:31:15 | 494 × 429 |
| 3 | FunnelGuest | PASS 4.1 s | "yours already" (restored from run 2's save) | ✓ row 07:34:27 | clean, but not a fresh double-pass |
| 4 | **FunnelVisitor** | **PASS 4.1 s** | **PASS 4.1 s (fresh)** | ✓ row 07:35:27 | **the clean PASS** |

Runs 1-2 hit an HTTP 429 storm caused by a co-tenant loopback client (another fleet agent's
`judge_drive.js` + its headless Chrome, polling 8206 from 127.0.0.1). The evidence — first 429
at t+1.6 s, *before* my game page opened at t+4.2 s — proves the drain was external. Full
numbers: `rate_limit_storm_evidence.json`.

## DEFECTS

**D1 — MAJOR (read before the domain goes live): the game shell's per-IP stream bucket freezes the lesson judge under any second concurrent session on the same IP.**
The shell rate-limits per client IP (`tools/game_shell/server.py`: stream class 600/min, burst 240). On localhost every session shares the single `127.0.0.1` bucket; through the public tunnel buckets key on `CF-Connecting-IP`, so **all players behind one home/office NAT share one bucket**. Two actively-playing cameras demand ~500-1000+ req/min against a 600/min refill — the server docstring's "even two behind one home router 429-free" is not safe at measured rates. The stranger-facing failure is ugly: starved `/api/state` polls mean the lesson judge can never see the body heal, so the verdict freezes on *"the goal is met — now LET GO, and let the body heal."* forever while the player has done everything right (both storm runs latched `goalMet=true` in the physics and still could not pass). Only the small link line may show "the world is silent — retrying…"; the verdict line itself never names the starvation. Suggested fixes (none applied — read-only walk): raise the stream budget or key buckets per session; add backoff on 429 in `pollVerts` (each failed `?delta=1` currently costs an immediate `?delta=key` retry — measured 6.7 Hz vs 3 Hz intended during a storm); surface starvation in the verdict line.

**D2 — MINOR: a stranger's first blind click on the creature reads as nothing.** A 150 ms click at the body's center produced no visible blood response when read 1.2 s later (press decay τ≈0.5 s beats the ~0.7 s readout refresh). The click verb works when held, and the intro teaches SPACE, but the first "poke it and watch" moment can look dead. A brief press flash or a one-line hint ("hold the click to press") would close it.

**D3 — INFO: `og:image` 404s until the deploy copies the capsule** (`store_art/capsule_616x353.png` → 404; the HTML comment documents this as expected until the deploy step runs). Scrapers find no image today.

**D4 — INFO: the shell binds IPv4 only** (`[::1]:8206` refused; `localhost` visitors work via browser IPv4 fallback). Consider binding both or documenting it in the runbook. No dead links anywhere on the landing page.

## Evidence index

- `funnel_e2e.js` — the headless stranger walk (this directory)
- `transcript.json` — final run's full transcript (verdict PASS)
- `rate_limit_storm_evidence.json` — runs 1-2 storm measurements + co-tenant diagnosis
- `01_site_landing_cold.png` … `09_signup_done.png` — one screenshot per stage
- Signup store: `tools/website/signups.jsonl` (rows above) · count endpoint `/api/signups/count`
- Gameplay artifacts created by playing (expected product behavior): `tools/game_shell/progress/FunnelTester.json`, `FunnelGuest.json`, `FunnelVisitor.json`

---

# H11 "store-package" — package tightening (2026-09-14)

Workspace `E:\ChimeraWork\slot-01` · branch `astra/tasks/matter-kernel-format-01` ·
base HEAD `569083bb`. The funnel was already PASS (H6, above); this pass closed the
named loose ends (D3, D4, the test-row hygiene) and refreshed the copy to the
ten-lesson product. Everything below verified headless (channel 'chrome'),
final run **PASS 20/20 checks** — `h11_verify.js` / `h11_transcript.json` in this
directory.

## VERDICT: PASS — funnel green, package tightened, one NEW defect found and fixed

**D5 (found this pass, FIXED): the live website process predated its own hardening —
GET /signups.jsonl served the raw signup list (200, rows on the wire).** The guard
commit `879cf69d` (R9 hardening, fleet D4) landed in the file, but the running
process had been started 2026-09-13 21:56:41 — before it — and Python never reloads.
First H11 verify run caught it (19/20, `signups_jsonl_refused -> 200`). The site was
restarted at the end of the pass (blip ~1 s, netstat-confirmed same bind 127.0.0.1:8210)
and the same probe now returns **404**. Exposure window was loopback-only (the bind
never left 127.0.0.1), but any public deployment from the stale process would have
shipped the leak the guard already fixed. LESSON: a hardening commit does not boot
itself — restart-after-guard is part of the fix. (The game shell process also predates
its `879cf69d` 404 fix — left untouched this pass, out of H11 ownership; flagged to the operator.)

## 1. D3 og:image — FIXED (404 -> 200)

The real store capsule (R7, fleet B2 art, generated by `tools/store_art/make_art.py`
from live engine capture `capture_01_hero.png` per `CHIMERA_PROOF\STORE_ART\manifest.json`)
now lives in the served tree:

- `tools/website/store_art/capsule_616x353.png` (60,218 B, PIL-verified 616x353 RGB)
- `tools/website/store_art/capsule_460x215.png` (37,395 B, PIL-verified 460x215 RGB)

The placeholder HTML comment is gone; the page now carries `og:title`, `og:description`,
`og:type=website`, two `og:image`s with `width`/`height`/`alt` on the primary. Both
resolve **HTTP 200, image/png** through the live server. Screenshot `h11_landing_after.png`.

## 2. Signup list hygiene — DONE, byte-exact

`tools/website/signups.jsonl` before: **5 rows** (1 real + 4 H6 test rows) → after: **2 rows**
(count endpoint reads 2, so the footer's "join 2 explorers" stays honest). Kept rows are
byte-identical to their pre-edit bytes (CRLF forms preserved; proven by md5: the
reconstructed pre-edit file hashes to the measured `9b709e89dd5410190ffa74c490d1c785`,
and the final file equals the two kept rows in their original form). Exactly three lines
removed, then the two H11 probe rows from the verify runs:

```
- {"name": "H6 Funnel Test", "email": "funnel-test@example.com", "at": "2026-09-14 07:24:31"}   (H6 run 1)
- {"name": "H6 Funnel Test", "email": "funnel-test@example.com", "at": "2026-09-14 07:31:15"}   (H6 run 2)
- {"name": "H6 Funnel Test", "email": "funnel-test@example.com", "at": "2026-09-14 07:34:27"}   (H6 run 3)
- {"name": "H11 Funnel Test", "email": "funnel-test@example.com", "at": "2026-09-14 08:17:52"}  (H11 verify)
- {"name": "H11 Funnel Test", "email": "funnel-test@example.com", "at": "2026-09-14 08:19:30"}  (H11 verify, post-restart)
- H11 verify, final run (row timestamped 2026-09-14 08:22 local, server clock; counted 2->3 then removed by the dedupe)
```

Final store: Alan's real row + exactly ONE clearly-marked funnel-test row
(`H6 Funnel Test / funnel-test@example.com at 2026-09-14 07:35:27` — H6's clean-PASS run).

## 3. Copy refresh — the page says what the product IS

- Hero tagline: *"a creature of sealed water cells. press it anywhere and the pressure
  answers — let go, and watch it heal."*; under the button: *"free in your browser,
  nothing to install — ten short lessons, every answer given by touch. sound on."*
- New card **"Ten lessons"** in the how-it-works grid.
- Every claim traces: ten lessons = the served pack (`tools/game_shell/lessons.json`, all
  ten titles; ten-lesson arc commit `a92569f7`); press-answer = R3 PASS; tau heal = R3
  "tau recovery exact"; browser play = the web kernel + H6's walk; sound = W4
  (`ee249856`). No stale "five lessons" anywhere on the page.
- `docs/STORE_COPY.md`: five→ten in short description, description, and bullet 4 (trace
  updated to the ten-lesson arc + the 9/10 headless walk); the gentle-hand threshold
  corrected 200 Pa → **50 kPa** (the correction the goal book already made twice —
  `e6fd55f9`, `a92569f7`; the old figure survived in this copy until now); a synthesized-
  sound sentence added; a TRAILER section documents the real-time capture (19.92 s, 467
  frames at ~24 fps, zero time-remap — commit `7994c208`); the honesty ledger's R6 note
  updated (re-run PASS 4/4 on this host, the GTX 1060-class bar still untested, so the
  mid-range claim stays unmade).

## 4. D4 IPv6 — FIXED in the door code

`demoUrl()` used to build `http://[::1]:8206` for a v6-served page — H6 measured that
door REFUSED (the shell binds IPv4 only). It now sends every loopback host (`::1`,
`[::1]` included) to the shell's real IPv4 door `127.0.0.1:8206`, with a comment naming
D4; the on-page unit harness gained the two v6 cases (quiet pass on every load).
`tools/website/server.py` docstring annotates the same fact.

## 5. One more fix the measurements forced: the hero had NO padding

Computed-style probe during verification: `header` computed `padding: 0px 24px` —
`.wrap`'s shorthand (specificity 0,1,0) silently beats a bare `header` rule (0,0,1),
so the intended 110/90 px hero padding NEVER applied (pre-existing since the page was
born; both H6 screenshots show the cramped top). Fixed as `header.wrap { ... }` —
measured after: sub-line bottom 590 → section top 680, exactly the 90 px gap.

## 6. Final health ledger (restarted server, final page)

20/20 checks PASS: site 200 in 37 ms · og images 200 (60,218 B + 37,395 B, image/png) ·
hero asserts (press-answer / watch-it-heal / ten-lessons) · demo door opens
`http://127.0.0.1:8206/` (title "CHIMERA — touch the living physics") · signup probe
recorded (count N → N+1, gold note) · `/signups.jsonl` 404 · zero console errors, zero
page errors, zero HTTP ≥ 400, zero failed requests, no failed `demoUrl` self-test.

## What only the operator can do (remaining gap list)

1. **The domain** — buy it and run the cloudflared tunnel (DEPLOY_RUNBOOK's go-live
   list); the page's door and og URLs are relative and deploy-ready.
2. **The payment account** (Stripe/PayPal, his identity) — the page is demo+signup
   only until then; selling needs his account.
3. **Mid-range performance** (R6's honest remainder): the GTX 1060-class bar is still
   untested on this host.
4. **D1 (H6, MAJOR, unfixed — out of H11 ownership):** the game shell's per-IP stream
   bucket (600/min) starves the lesson judge when two cameras share one NAT IP; needs
   the shell's budget raised or per-session keying before a public push.
5. Signups backup: the runbook's `copy tools\website\signups.jsonl E:\backups\` step is
   the operator's routine; the file is now production-clean (2 rows).
