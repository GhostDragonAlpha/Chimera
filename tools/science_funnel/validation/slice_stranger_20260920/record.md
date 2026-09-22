# Rule 0 preregistration — THE STRANGER PASS, lane slice-stranger-20260920

Lane: `lane/slice-stranger-20260920`, branched from `lane/mesh-parse-20260920`
@ `7d7868d3` (the landed mesh-parse tip — the real-body slice WITH the 2-second
cached boot). Worktree: `E:/ChimeraWork/buffy-stranger-20260920`. Git trailer
on this lane's commits: `Agent: stranger`.

Pushed into the bear-pit as-written: **only this lane branch**. Master, the
shared desktop, other worktrees under `E:/ChimeraWork` (running lanes
finish-agent, rbmovie-agent, thincli-agent, fkred-agent, vanhoof2-agent,
integ5-agent), the engine's physics, and `gait_controller.hpp` are all frozen.

## WHAT THIS LANE INHERITS (read before anything else)

The slice (`tools/playable_slice/` at this base) is the PROOF of the real
body: a page that serves the real CT-derived macaque skeleton — 25 bones,
499,976 triangles, imported through the engine's own kind-'G' front door from
the pinned `standing_body.glb` cache — and runs the engine's OWN movement law
(gravity + floor contact at the derived attractor —(m·g/k)−ymin) in the "O"
history and the byte-clean 2-second boot in the mesh-parse lane (full-boot
t_first_verts **2.08–2.10 s** vs the slice's own 10 s bar; receipts in
`slice_real_body_20260920/` and `mesh_parse_20260920/`).

The slice page today has **no first-run guidance, no keyboard controls, no
timed motion-to-action staging, no on-page error beacon, and no stranger's
walkthrough instrument**. The registered controls are mouse-only
(orbit-drag, wheel-zoom, click-press) plus the five buttons (SEND / STOP /
THE FALL TEST / RESTART / SAVE). A person who has never seen the project
lands on the page and has to discover: what the creature IS, what the game
DOES, and what to PRESS — on a page whose only hint is the honesty panel.

This lane's whole claim is that the SLICE can carry a stranger's first minute.

## THE THEORY

**STATEMENT** (someone could disagree): the playable slice's page, on this
base (real body, cached 2 s boot), can be made self-explanatory and
keyboard-first — first-run on-page guidance in plain words, every control
named on the page, every control backed by a working key path, a visible
motion-to-action progression, and a restart that returns the world clean —
WITHOUT touching the engine, its physics, or `gait_controller.hpp`; the only
edits are page-level (`tools/playable_slice/index.html`), additive to the
slice server, and the lane's measurement instrument. And the instrument that
plays the stranger (private headless Playwright, channel `chrome`) can
measure that first minute: boot → motion → understood control → deliberate
action → restart.

**PREDICTIONS** (not measured yet; the walkthrough below exists to measure
them):

- P-1 (boot): from the moment the slice server is up and the page is open,
  the world is VISIBLE and the page can report itself booted
  ("booting the world…" is gone) within the slice's own launch class —
  server timeline `t_first_verts` under the 10 s bar (inherited; measured
  2.08–2.10 s on this base) and the page's own first frame follows within
  2 s of the page load.
- P-2 (motion): the visitor SEES motion without pressing anything — the
  body settles under the engine's own gravity/contact law from the import
  pose to the derived attractor (the standing start's visible oscillation)
  within a named budget, and the page shows that motion (`root_y` moving in
  the HUD / the renderer streaming). The engine's law runs from boot; the
  body is not posed static.
- P-3 (understood control): the FIRST-RUN guidance on the page itself — in
  plain words: what am I looking at / what does it do / what do I press —
  lets a stranger nominate the first control (the SEND/the press) by reading
  the page alone, no manual, in seconds.
- P-4 (keyboard-first): every control NAMED on the page has a key path that
  WORKS — the engine-visible press is reachable by keyboard (the
  mouse-through-automation unreliability is the law, so the key path is the
  path that counts), and every named key produces its named effect without
  error.
- P-5 (act): the scripted stranger reaches a DELIBERATE first action — a
  control it chose by reading the page, not the harness — in under
  **60 seconds from launch** (the mission's own suggested bar).
- P-6 (restart): the page's restart path (key R) reboots the world and
  returns to a settled standing start with zero console errors and the same
  scene pin — a clean-second-time, not a dead-end.
- P-7 (zero-console-errors): the whole run — boot, motion, actions, restart
  — produces a page with ZERO console errors and ZERO page errors, by the
  on-page error beacon's count AND by the harness's own captured console.

**FALSIFIERS** (named before the run; any one failing = the theory loses,
the RED is recorded and reported, never hidden behind a redesign):

| id | class | pass condition |
|----|-------|----------------|
| F-STRANGER-60 | THE stranger bar (the mission's own) | the scripted stranger, acting through a private headless-browser walkthrough (Playwright, channel `chrome`, fresh context, no shared desktop), reaches a DELIBERATE action (a control it names by reading the page, then presses) in **under 60 s from launch** — launch = the first page navigation, and the action must be a real one the page does (send/press/fall), not merely "page loaded" |
| F-EVERY-NAMED-KEY | keyboard-first (the law) | EVERY control named on the page works through its key path, verified by the walkthrough pressing it; including the press at a real body vertex, with the effect visible in the page's own state (no dead keys, no thrown errors) |
| F-BOOT-BAR | boot budget | server timeline t_first_verts under 10 s (the slice's own bar, inherited measured 2.08–2.10 s) AND page first-frame within 2 s of load; printed and reported, not tuned |
| F-MOTION-BAR | the visitor sees motion | visible motion (root_y moving toward the attractor through the engine's law) is confirmed on the page within 20 s of the world being reported up — the body is not static-parked. If the settle is genuinely done by the time the page connects, the page's own motion trace (root_y history in HUD) is the evidence, and the bar is that the LAW moves it, measured |
| F-GUIDE-PLAIN | the guidance is on-page and plain | the page itself (first-run state) names: what the creature is, what the slice does, and what to PRESS — with the key names; a stranger (here: the walkthrough) can read those off the page and name the first control back to the harness |
| F-CLEAN-RESTART | restart path | key R restarts: the world reboots, returns to the standing start, settles again, same scene pin, ZERO console/page errors across boot→restart→settled; restart does not brick the page |
| F-ZERO-ERRORS | the error beacon | the on-page error beacon (window.onerror + unhandledrejection + captured console.error) counts ZERO at the end of the walkthrough, AND the harness's own captured page console/pag error transcript is empty; the beacon pattern is the repo's own PAGE-ERROR ledger (walk_lessons10.js), reused |
| F-SCOPE | containment | zero edits under ChimeraEngine/, zero edits to engine physics or `gait_controller.hpp` (git diff those trees EMPTY vs the base); the only shipped-tree edits are `tools/playable_slice/` page/server-additive and this lane dir `tools/science_funnel/validation/slice_stranger_20260920/`; no GPU work (the engine boots below are the slice's own modest render loads, same as the landed lanes ran); push ONLY `lane/slice-stranger-20260920`; no master |

3-run determinism for the walkthrough instrument (the repo's own bank
norm): the walkthrough is run 3x on the same engine build; the reported
numbers (timestamps) are the three runs' measurements, and the verdicts
(F-GUIDE-PLAIN, F-EVERY-NAMED-KEY, F-ZERO-ERRORS, F-CLEAN-RESTART) must be
IDENTICAL across the three (error-free, guide readable, all keys alive,
restart clean).

## DERIVED, NOT TUNED (Rule 1)

- The **60 s** F-STRANGER-60 bar is the MISSION's named bar, not this
  lane's taste; it is written here verbatim and enforced by the instrument.
  Inside it this lane stages nothing artificially — the page's own
  first-run guidance is the help; the walkthrough is instructed to read the
  page and act only on what the page says.
- The **10 s** F-BOOT-BAR is the slice's OWN launch clause (F-SLICE-LAUNCH,
  inherited; measured 2.08–2.10 s at this base) — not new.
- The **20 s** F-MOTION-BAR is derived from the launch bar's class plus the
  settle recorder's own window (slice_server's `_finish_settle` polls the
  attractor; the standing start's visible settle oscillation is real engine
  physics observable by any connected page within that window). A number
  needed to be NAMED for the falsifier to be falsifiable; 20 s is the
  engine-settle class, not a gameplay tuning knob.
- The **motion evidence** is the engine's OWN numbers: `root_y` approaching
  −(m·g/k)−ymin = 0.124641 m (banked constants, imported ymin), the derived
  attractor from slice_real_body_20260920's F-SLICE-FALL — not a fake idle
  animation.
- Everything the guidance says is TRUE of the slice as it exists: REAL
  (render/gravity/floor/press/fall) vs MOCK (the carry) vs DECLARED (the
  ghost overlay) come from `mock_registry.json`, the same file the honesty
  lane audits. New page copy adds no new claim about the world; it only
  makes the existing claims findable in plain words.
- The press's key path must press a REAL body vertex through the engine's
  own `/tick_touch` (the page's existing raycast, reached by keyboard
  instead of a mouse-up) — the key path replaces the pointer, not the
  physics.

## RUN PLAN

Prereg (this file, committed) → confirm the engine build in THIS worktree
(cached boot, the slice's own binary) → implement: page guidance + key
paths + motion trace + error beacon + restart polish (all in
`tools/playable_slice/index.html`, additive server bits only if the page
cannot do it alone) → write the walkthrough instrument (private headless
Playwright, channel `chrome`, fresh context) in this lane dir → RUN it 3x,
capturing timestamps (boot / first motion / first understood control / first
action / restart) → verdicts → `receipt.json` in THIS directory → commit
("Agent: stranger") → push ONLY `lane/slice-stranger-20260920`.

Receipt: `tools/science_funnel/validation/slice_stranger_20260920/receipt.json`.
Prereg: this file.

## AMENDMENT — RUN RESULTS (2026-09-22, after the run; nothing above altered)

ALL EIGHT FALSIFIERS PASS, 3/3 runs with identical verdicts (the prereg's
determinism requirement). Headline numbers, three green runs
(walkthrough_run_172717 / 172810 / 172856.json):

- t_page_load 0.07–0.08 s; first motion on canvas 0.50–0.57 s;
  t_understood 0.56–0.63 s; **t_first_action 0.85–0.91 s** (bar: 60 s;
  the action is chosen from the page's own words, effect confirmed);
  restart world-back 1.62–1.66 s, scene pin stable, re-settled ~15.5 s,
  boot counter 1→2; on-page beacon 0 and harness console 0 throughout,
  including through the restart. All 13 named keys verified by key path.

The instrument's channel story is recorded, not hidden: the prereg named
channel `chrome`; the machine's installed Chrome 153 now fails a navigation
canary on EVERY real navigation (finding F-ENV-CHROME, evidence committed:
netlog_probe.json + probe_*.js + FINDING_chrome_loopback.md), so the runs
complete on Playwright's bundled Chromium of the same build after the canary
fails, and every artifact carries the deviation verbatim.

What the honest REDs bought (all artifacts kept, receipt.json lists them):
1. run 160844: unbounded polling collapsed under load → serialized polls +
   fetch timeouts (a stranger's slow laptop would have hit this too).
2. run 164558: the dead-keys RED — the handler read `k.key` (undefined)
   instead of `k.name`; NO named key had ever worked. F-EVERY-NAMED-KEY did
   its job. Fixed; every key now verified with a stage effect.
3. run 171524: boots [1,1] — boot_count was derived from a list that resets
   per boot and could never increment. Server now carries a cumulative
   counter, verified harness-side.
4. run 172112: an in-page /api/status read stalls behind the boot lock →
   STAGE-TIMEOUT recorded; the counter read moved to the harness (Node http,
   hard timeout). This is also why the instrument now has per-stage traces,
   per-call budgets, a watchdog, and progressive artifact flush.

Duplicate-dispatch note: two agents were assigned this lane; glm53-lead-02's
prereg (4ff5576e) governs and is the one falsified-or-confirmed here; the
reconciliation lives in DUPLICATE_ASSIGNMENT.md (commit 8d97ba26).