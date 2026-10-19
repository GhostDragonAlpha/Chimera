# WC-INTERACT-2 — the ghost follows your eyes, F welds, and the panel says what mode you're in

**Date:** 2026-10-19
**Change:** engine interactive mode extended, 150+/5- across four clean files
(`engine.cpp`, `main.cpp`, `membrane_tick.{cpp,hpp}`); `ui.cpp` untouched
(pre-existing dirt, mtime 2026-10-12).
**Runtime:** rebuilt B-suite engine, sha256
`757f280a4ed3a522…` (final, with status line); Maya's weld+hover build
`80d265f5b4c3f8f6…`; baseline before edits `9cb45190…` (the WC-INTERACT-1
exe).
**Evidence:** `wc_interact2_smoke.py` + `results.json` (26 asserts) +
hover/weld PNGs; `cap_status.py` + status PNGs (this directory).
**Gate:** §5.1 "Close the gaps…" row 1 (attachment + preview), phase 2 of
WC-INTERACT.

## Player benefit

Three upgrades to playing the workshop with the mouse:

1. **The ghost follows the cursor.** Moving the mouse re-picks through the
   same camera ray + `B2Scene::pick` the click uses; the cyan place preview
   now draws where you LOOK, not where you last clicked. A pick miss keeps
   the last anchor (no flicker); a hover never steals the white selection
   highlight — the click still owns selection.
2. **F welds.** Click a part (white), hover a second part, press F: a real
   finite-area connector (3 anchor pairs, k = 10000 N/m — the documented
   interactive default between the challenge drivers' 2000/20000) is created
   through the UNCHANGED `B2Scene::set_weld` transaction. This is the
   connected-structure verb: the welded-span solution of workshop challenge
   1 is now buildable without typing anything. Refusals name the missing
   input ("select a part first", "hover the second part", "a part cannot
   weld to itself"); the pool cap and re-set-replaces semantics are
   inherited from the transaction.
3. **The STATUS panel says what mode you're in.** A new live line —
   `build: place_2 | sel pier_0 | hov block_b` (or `build: off`) — appears
   in the Studio STATUS panel. **No ui.cpp edit was needed:** main.cpp's
   existing 1 Hz composer feeds the panel through the public inline setter
   `StudioUI::set_status_lines` (ui.hpp:129); the engine only appends a
   line. The lead decision on the readout is resolved: clean-file path
   exists and is shipped.

## Evidence

- **Baseline before edits** (source == 0d105e42): rebuild + full regression
  88 passed (exe `9cb45190`). Two intermediate runs each had one different
  wall-clock-sensitive test fail under parallel load (frame-time envelope;
  B6 valve flux tolerance — unreachable from b2i code, which those tests
  never enable); quiet re-runs green. No test weakened.
- **After Maya's edits** (exe `80d265f5`): full regression 88 passed —
  lead re-ran independently (189.12 s).
- **After the lead's status-line addition** (final exe `757f280a`): full
  regression 88 passed (187.25 s).
- **Smoke, real Win32 input** (26/26 asserts): hover A with NO click posted
  → `hovered == block_a`, anchor == exact-pixel pick hit; hover B → anchor
  MOVED onto B's surface (hover-follow proven); parts/welds untouched by
  hover; F with nothing selected → named refusal, no weld; Tab + hover B →
  ghost follows (`5-hover-ghost-over-b.png` — cyan pier preview over
  block_b); click A + hover B + F → `/tick_b2_state` welds shows
  `{a: block_a, b: block_b, n_anchors: 3, k: 10000}`, log "welded block_a
  to block_b", selection kept (`6-welded.png`); F self-weld → named
  refusal, existing weld byte-unchanged; X drops the welded part and its
  connector with it; disable resets hover state too.
- **Status line** (`cap_status.py`): disarmed grab shows `build: off`;
  after arming + a real WM_MOUSEMOVE over block_b (no click), the panel
  reads `build: place off | sel - | hov block_b` (lead viewed the pixels;
  state route asserts `hovered == block_b`).

## Lead review (author-independent, focused)

Full diff read: hover hook gated on `!g_mouse_captured && b2i_enabled()`
(captured moves stay orbit/pan); panels skipped via the public
`ui_.wants_mouse` (ui.hpp:137 — the same test the wheel route uses, Blender
law); F behind the existing console gate; `b2i_hover`/`b2i_weld` take
`b2_mtx_` then `b2i_mtx_` never nested in reverse (no deadlock path);
`b2i_status_line` composes under `b2i_mtx_` directly because that mutex is
not recursive (commented); weld document verified against `set_weld`'s
actual validation (b2_scene.cpp:671-733 — no proximity check, same-point
pairs legal); state route appends `hovered` with existing fields
byte-compatible.

## Known limits (stated)

- The weld connector has no render mesh — the welded state is proven by the
  state route + engine log, not pixels (rendering connectors is engine-
  track work).
- Hover can update under the open console (no console-position check —
  consistent with the untouched click path).
- k = 10000 N/m is a fixed default; no player-facing stiffness choice yet.
- Human playability unobserved (as ever, until someone plays).

## Process

Maya implemented + smoked in one dispatch (~1.6 h) under the revised brief
(baseline-first, no capture/commit); the lead re-ran the regression twice
(Maya's exe and the final exe), added the status-line readout (the verdict
task she was given — she found the clean-file path, the lead shipped it),
captured the status evidence, and reviewed the full diff before publishing.
