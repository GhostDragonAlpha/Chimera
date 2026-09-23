# THE STRANGER PASS — report (lane slice-stranger-20260920)

Date: 2026-09-22 · Base: 7d7868d3 (lane/mesh-parse-20260920, the real-body slice with the cached 2 s boot) · Agent: stranger

## What was asked

Make the playable slice playable by a person who has never seen the project,
unaided, within a minute — with every control keyboard-first and named
on-page, boot→motion→action each timed, a clean restart, zero console errors,
and a scripted headless-browser stranger as the acceptance instrument.

## Result: ALL FALSIFIERS PASS, 3/3 identical runs

**The first minute, measured** (three green runs, worst-case values):

| moment | measured | budget |
|---|---|---|
| page load | 0.08 s | — |
| first motion on canvas | 0.57 s | 20 s |
| page understood (guide readable, keys listed) | 0.63 s | — |
| **first deliberate action, effect confirmed** | **0.91 s** | **60 s** |
| restart R: world back | 1.66 s | 60 s |
| restart: re-settled at the standing start | 15.5 s | — |

Zero on-page beacon errors and zero harness-captured console/page errors in
all three runs, including across the restart. All 13 keys the page names
(1, 2, 3, Space, arrows, +/−, H, S, R) verified working through their key
paths, each with a stage-checked effect; the Space press goes through the
engine's real `/tick_touch` at a body vertex. Scene pin stable across
restart; carry state cleared. Engine trees: zero edits (diff vs base empty).

## What shipped on the page (tools/playable_slice/)

- First-run guide in plain words (what the creature is, what the slice does,
  what to press), the keys card, and a live status line — everything a
  stranger needs is on the page itself.
- Keyboard-first controls with per-key effects; H re-shows the guide.
- The repo's error-beacon pattern (window.onerror + unhandledrejection +
  console.error capture) wired to an on-page beacon, asserted zero by the
  instrument.
- Server (additive): restart-gap answered as a first-class `{"restarting":
  true}` state instead of errors, a cumulative boot counter, serialized
  polling with fetch timeouts (the page no longer stacks thousands of 9 MB
  requests under load).

## What the honest REDs bought

The instrument failed before it passed, and the REDs are kept as artifacts:

1. **Unbounded polling collapses under load** (4233 errors, run 1) →
   serialized polls + timeouts.
2. **The dead-keys RED** — the handler matched `k.key` (undefined) instead
   of `k.name`: *no* named key had ever worked. This is precisely the defect
   F-EVERY-NAMED-KEY exists to catch.
3. **A boot counter that could not count** — derived from a list that resets
   per boot; restarts measured [1,1]. Now cumulative, verified harness-side.
4. **An in-page status read stalling behind the boot lock** → recorded
   STAGE-TIMEOUT, read moved to the harness; the instrument gained per-stage
   traces, per-call budgets, a 240 s watchdog, and progressive artifact
   flush so a wedged run can never again die silently.

## Findings (first-class, in receipt.json)

- **F-ENV-CHROME**: the machine's installed Chrome 153 hangs *every* real
  navigation (loopback and external, headless or not, even `chrome
  --dump-dom` alone); evidence committed (netlog + probe matrix). The
  instrument attempts channel `chrome` every run via a canary and completes
  on Playwright's bundled Chromium (same build) when it fails — the
  deviation is recorded verbatim in every artifact.
- **F-DEAD-KEYS-FOUND, F-BOOT-COUNT-METRIC, F-POLL-FRAGILITY**: product and
  measurement defects above, fixed and documented.

## Provenance

Governing prereg: 4ff5576e (glm53-lead-02; duplicate dispatch reconciled in
DUPLICATE_ASSIGNMENT.md / commit 8d97ba26). Receipt:
`receipt.json` in this directory; instrument `walkthrough.js` +
`run_walkthrough.ps1`; artifacts `walkthrough_run_*.json` + screenshots.
Branch `lane/slice-stranger-20260920` only; master untouched.
