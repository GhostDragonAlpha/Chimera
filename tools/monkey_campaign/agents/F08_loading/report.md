# M-F08 Report — repeatable forest loading (map item F08) — GREEN

Agent: M-F08. Date: 2026-09-24. Worktree `E:/ChimeraWork/monkey-play-20260924`,
branch `monkey-play-20260924` (HEAD at start `de5a3691`). CPU-only; headless;
no engine C++; no servers; no existing file modified.

Item F08, verbatim: "Scene seed/configuration reproduces assets, collision and
initial state with clear failures for missing assets. Resource cleanup uses
existing lifecycle machinery."

## Verdict: GREEN — 66/66 checks pass; all four preregistered falsifiers green

```
VERDICT: GREEN (66/66) -- falsifiers {'a_recompile_bytes': 'green',
 'b_missing_or_corrupt_silent': 'green', 'c_initial_state_variance': 'green',
 'd_teardown_leaves_live': 'green'}
```

Deliverables (all at declared paths, prereg-frozen before implementation):

- `tools/monkey_campaign/data/monkey_forest/forest_loader.py` — the one-shot
  forest loader (the ONE new data-layer module; sha256
  `53d7fdde7deb6223f6760f4d9d6d8f378f3c4bf3cc5513381bf83e68d8cfbb95`).
- `tools/monkey_campaign/agents/F08_loading/verify_loading.py` — the suite
  (sha256 `fc4d34ab754efc73d144b5b0b6682a65fe0d8e4111d237a2e9a2ec15d402b826`).
- `agents/F08_loading/`: brief.md, PREREGISTRATION.md (Amendments 1-2, both
  pre-implementation), HANDOFFS.md, receipts/{run.json, run.txt,
  determinism.txt}.

## What was built (theories → measurements)

**T1 reproducibility (recompile-not-copy), falsifier (a) — GREEN.**
`load_forest()` recompiles all four declarations from the recipe modules —
clearing from the frozen seed 4598321, terrain from the RECOMPILED clearing
bytes (temp file, never the committed copy), trunk from the recompiled
clearing dict, routes via `route_recipe.compile_declaration()` — validates each
with its own module's validator, then byte-compares against the committed
files. Measured: in-process ×2 byte-identical; 3 fresh-process `receipt` runs
byte-identical (stdout sha256 `facca270…1f5`); committed digests exactly the
prereg table (clearing 13,112 B `18dd2ff6…`, terrain 877,752 B `446ed3fb…`,
trunk 16,634 B `94ff906e…`, routes 8,495 B `28dff2b3…`).

**T2/T3 missing/corrupt assets, falsifier (b) — GREEN.** Phase A checks all
four presences before any recompile; each of 4 omissions in a sandbox copy
tree raises `f08_missing_artifact` naming (artifact, absolute sandbox path).
Corruption matrix 13/13 named: body-edit and pin-edit per artifact →
`f08_invalid_artifact` with `cause` = the recipe's own code
(`f01/f02/f03/f07_digest_mismatch`; truncated JSON → `f01_invalid_json`); the
coherent re-forge case (body edited AND re-pinned with the recipe's own
digest — a file that lies self-consistently) survives the self-pin and is
caught only by `f08_recompile_drift`. Zero silent loads; zero generic
exceptions; real files re-hashed unchanged after the suite.

**T4 initial state, falsifier (c) — GREEN.** The record (schema
`chimera.monkey_forest.v1`) is composed only from the four proven declarations
plus the ONE query surface, and self-pins:
`initial_state_sha256 = c3286e14a787f6bb65ccc93dc3e80b0412d777048d109d404ca49328fe1bf627`,
identical in-process ×2 and across the 3 fresh processes. Every frozen field
equals its declaring artifact: spawn `[0,0,0]` at height 0.0, envelope 0.25;
trunk `[11.976783, 0.0, 2.471766]` r 0.037 h 1.158; route R0 length 12.229185,
tangents R1L…R5R, grid 801×801 @ 0.05, blockers [B1, B2]; seed 4598321.

**T5 cleanup on existing machinery, falsifier (d) — GREEN.** Cited, not
rebuilt: `World.shutdown_engine()` (slice_server.py:174-181; main()'s finally
:604-605; top of every boot :96) and `SessionFlow`'s exit (teardown exactly
once; terminal rows absent; session_flow.py:107-117, 344-349;
`TeardownDouble` :141-151). **The gap was real**: nothing exists for the data
layer — recorded in the prereg, and the smallest adapter lives on
`ForestScene.teardown()`: zero-arg callable in SessionFlow's exact shape,
optional injected `engine_shutdown` released FIRST (reverse-load order),
release-by-name ×7, zero-live audit, idempotent second call (named no-op),
`f08_teardown_leak` on a failing release with a clean retry. Headless doubles
prove: 7/7 released exactly once, engine first; no survivor; no second
teardown.

**T6 the loaded surface is the real physics surface — GREEN.** Through the
loader: `height_at(0,0)==0.0`; gradients (0,0) at spawn AND trunk site;
`worst_triangle_slope() == 0.042522289331596436` at (17.0, 7.0) — bit-for-bit
F02's receipt; extent law strict `>` (20.0 inside, 20.05 outside);
`f02_outside_extent` on a past-edge query; W10's context-manager consumption
works and tears down clean.

## Honest findings during the run

1. **Prereg Amendment 1 (pre-implementation)**: my first-frozen T2 prediction
   ("all other 4×3 subsets still load green") was incoherent — omitting the
   clearing cannot load. Corrected and recorded BEFORE any loader code
   existed.
2. **Prereg Amendment 2 (pre-implementation)**: T6 misattributed F02's
   0.042522289 to `gradient_at(17,7)`; that point sits on a grid node and its
   containing triangle answers 0.029843375. The received number is
   `worst_triangle_slope()` — probed once, then frozen as the assertion.
3. Three implementation-run defects caught by the suite itself before any
   GREEN verdict (a module-dispatch AttributeError; a recipe
   `Refusal`-tuple catch; a double-not-callable TypeError) — the falsifiers
   were doing their job; each fix is in the committed loader/suite.

## Receipts

- `receipts/run.json` — 66 checks, verdict GREEN, sha256
  `4ebd3a6c5403663999102b2d6fd49aafcf1f157948a8cb91f95e8f9ca048c37c`
  (byte-identical across consecutive suite runs).
- `receipts/run.txt` — human log, sha256
  `235938d718939493ba78337ade5602f0f7c03cd906c98b859d07404dba6dcfa9`.
- `receipts/determinism.txt` — 3 fresh-process receipts, identical.

## Integrity paste (git status --porcelain -uall at completion, F08 lines)

```
?? tools/monkey_campaign/agents/F08_loading/HANDOFFS.md
?? tools/monkey_campaign/agents/F08_loading/PREREGISTRATION.md
?? tools/monkey_campaign/agents/F08_loading/brief.md
?? tools/monkey_campaign/agents/F08_loading/receipts/determinism.txt
?? tools/monkey_campaign/agents/F08_loading/receipts/run.json
?? tools/monkey_campaign/agents/F08_loading/receipts/run.txt
?? tools/monkey_campaign/agents/F08_loading/report.md
?? tools/monkey_campaign/agents/F08_loading/verify_loading.py
?? tools/monkey_campaign/data/monkey_forest/forest_loader.py
```

M-F08's footprint is EXACTLY `tools/monkey_campaign/agents/F08_loading/`
(9 files, this report included) plus the ONE declared data path
(`data/monkey_forest/forest_loader.py`, declared in the frozen prereg BEFORE
implementation). The other entries in the full status (`U02_camera/receipts/
latency_run.json` modified, `TIE2/receipts/independent_rerun_….out`) belong to
parallel sessions — untouched by M-F08. No existing file modified; no engine
C++; no GPU; no servers. Not committed (coordinator commits agent files, per
campaign pattern).
