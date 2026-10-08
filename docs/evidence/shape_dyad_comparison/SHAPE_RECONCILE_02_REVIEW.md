# SHAPE-RECONCILE-02 — independent evidence review

Author: independent trial session (read-only-plus-evidence lane). Date: 2026-09-10.
Scope: compare the two theShape dyad experiment streams from artifacts only; no source,
shared-reading, or term-store edits; no engine launched. Reviewer base revision:
HEAD `302da837` (astra/gait-capture) + dirty diff (see below).

---

## 0. Identity and preservation of both reports

| artifact | author-lane | sha256 (16) | status |
|---|---|---|---|
| `docs/THE_SHAPE_DYAD_CORRECTION.md` | presentation lane (this reviewer) | `cab6062217b8e17f` | intact; preregistration + addendum present (8 keyword hits) |
| `docs/evidence/shape_dyad_correction/run_20260910/dyad_result.json` | new-physics lane | `926336db941eeca0` | intact; own file inside the presentation lane's evidence dir (addition, not overwrite) |
| `Saved/dyad/**/report.{md,json}` | shared report path | — | **no overwrite**: no `report.*` under `Saved/dyad` has mtime > 2026-09-09 22:00 |

The two lanes did **not** overwrite each other. The only collision is additive: the
new-physics lane archived its `dyad_result.json` inside the presentation lane's
evidence directory. Both files are preserved above under distinct identities.

---

## 1. Source revision + dirty diff (shared by the two recent lanes)

Uncommitted working-tree diff at review time (authorship: new-physics lane, mtimes
2026-09-09 23:05–23:58 local):

- `story/theShape/physics.py` — cell-size law changed: min paw **semi-axis** → min
  paw **width**; `MIN_CELLS_ACROSS = 3` unchanged.
- `story/theShape/numbers.json` — `cell_size` 0.01 → **0.02 m**; grid
  47×97×94 → **24×49×48**; `cell_count` 24801 → **6595**; `com_gap_cells`
  worst 0.653 < slack 1.0 (claim holds under the rewritten law).
- `story/theShape/lattice_cells.npz` — `cddafbd747ebf5af` (@HEAD) → `34306e5d36623407` (worktree).
- `ChimeraEngine/cpp_bridge.py` — `render_term_movie`: per-frame camera + explicit
  14-float buffer with **σ = cell_size × size_scale (0.35)**, α forced 1.0, settle-capture.
- `ChimeraEngine/human_messenger.py` — expected reading for `theShape` rewritten:
  "BLOCKY, voxel-built … visible cubes like a 3D cross-stitch" → "many small
  overlapping brown grains or soft blobs … visible grain texture".
- The term store's `theShape` claim/numbers are **unchanged** (pointers still to
  `numbers.json` keys; visual/movie pointers still to the Sep-1 / Aug-27 artifacts).

Timing fact that matters for attribution: `physics.py` changed 23:05, the presentation
lane's k_min renders ran 23:36–23:55 — **the presentation-lane stills measured the NEW
48-cell lattice** (its archived scripts divide by 96, so their recorded
`k_eye_px_per_cell` values are ~2× understated; true k is ~2× the recorded number).

---

## 2. Comparison table

Three runs exist with preserved evidence. "Store" = committed-revision lane
(approx. Aug 27 render, Sep 1 store update; raw log not in `dyad_log.jsonl`).

| dimension | Run A — committed lane (store FAIL_RESTART 0.450) | Run B — new-physics lane (movie, FAIL_RESTART 0.200) | Run C — presentation lane (stills, texture experiment) |
|---|---|---|---|
| source revision | tracked @cf275281-era (pre-dirty-diff) | worktree @302da837 + dirty diff | worktree @302da837 + dirty diff (unknowingly) |
| physics diff | none (semi-axis law) | semi-axis→paw-width, s=0.02 | same as B (its emit() was used verbatim) |
| geometry (lattice) | 96 cells tall, 24801 cells, s=0.01 m, npz `cddafbd7…` | 48 cells tall (24×49×48), 6595 cells, s=0.02 m, npz `34306e5d…` | same as B (48 cells; scripts assumed 96 — recorded k understated ~2×) |
| CoM claim | gap 0.31–0.54 cells (old numbers) | worst 0.653 < 1.0 slack (new numbers) | not re-derived (cited) |
| presentation σ | engine default (σ ≈ cell pitch ⇒ merged surface) | σ = 0.35 × s = 0.007 m, α=1 | σ ∈ {0.6, 0.35} × s (the axis under test), α=1 |
| camera | fixed (0, −2.7e, 0.72e), extent @ t=1.0 (recovered from git diff hunk) | per-frame extent (0, −2.7e, 0.72e) | same standard camera, full frame + 3 crop margins (0.06/0.14/0.25) |
| framing (measured) | 384-px frame: subject 160×123 px, h-ratio 0.57, fill 0.11, **k ≈ 123/96 ≈ 1.3 px/cell** | full 2560×1440: subject h-ratio **1.00 (clipped)**, fill 0.65; eye frame: fill 0.65, **k ≈ 4.5+ px/cell (lower bound, clipped)** | full 1280×720: subject h-ratio 0.62, unclipped; eye crops **true k ≈ 4.5–6.0 px/cell** |
| image/movie hashes | `cpp_theShape_movie_00_384.png` (Aug 27 04:04); begin/end pair byte-identical 14,748,233 B (stale capture, Sep 1) | 12 frame hashes in `dyad_result.json` (frame00 `5e94d03f4c906657…` = worktree file, verified) | 4 archived PNGs + `engine_t0_full.png` (files under `shape_dyad_correction/`) |
| instrument / prompt | omni movie (12 frames, one call) per store; logged re-runs **wall-breached** (`error: 'one-image wall breach'`, rc0) → verdict from earlier unlogged run | omni movie, open description prompt ("main colors, the shapes, what it depicts, how it changes"), 12 images, 1 call, 1986-char report | **targeted surface-texture question on single stills** ("smooth, or repeating fine structure? name its shape") + one open still observation |
| expected reading | "BLOCKY, voxel-built teddy … visible cubes like a 3D cross-stitch" (original) | revised (grains) — short form | original AND revised both scored (0.35 / 0.40) |
| served model | qwen3.8-27b-nvfp4-mtp (watch) | qwen3.8-27b-nvfp4-mtp | qwen3.8-27b-nvfp4-mtp (all calls) |
| raw key response | not preserved in `dyad_log.jsonl` for the 0.450 run — **UNKNOWN** | "flat circular/fan-shaped disc … small cross-hatched grid cluster at center … NOT bear-like, no head/ears/torso/limbs; ground plane? No" | σ0.6: "smooth"; σ0.35: "small, regularly spaced dots forming a grid-like (dotted lattice) pattern"; observe-style: "rough and grainy … stippled" |
| verdict | FAIL_RESTART, alignment 0.450 < 0.6 (store) | FAIL_RESTART, alignment 0.200 < 0.6 (own record; falsifier (ii) fired per its note) | no acceptance verdict claimed; texture-legibility measurement only |
| judge | LLM `align()` (senses) — **judge identity UNKNOWN** | same — **UNKNOWN** | same — **UNKNOWN** |

---

## 3. Which comparisons actually isolate one variable?

- **B vs A (0.200 vs 0.450): isolates nothing.** Physics (96→48 cells), σ
  (merged→0.35), reading (cubes→grains) and framing (small→clipped-at-frame-edge)
  all change simultaneously.
- **C: σ 0.6 vs 0.35 at matched crop — the only clean single-variable isolation in
  the record** (texture legibility: merged → grid-legible, blind eye, one image/call).
- **C: margin 0.06/0.14/0.25 at fixed σ** — within-lane control; legibility stable.
- **C-observe vs B-stills (23:44 series): two variables (framing + question), shared
  negative outcome** — silhouette unnamed under both framings → framing is not the
  current silhouette blocker; bounds but does not isolate.
- **A's logged 23:09/23:21 re-runs are INCONCLUSIVE** (one-image wall breach, zero
  report) — the store's 0.450 predates the log and cannot be re-audited from it.

### The "square grid" observation — instrument check (as asked)

**Confirmed:** the grid reading came from the presentation lane's **targeted
surface-texture question on single stills** (`kmin_experiment2`, prompt: "Describe
the surface … smooth, or does it show a repeating fine structure? If it shows
repeating structure, name its shape."), at true k ≈ 4.5–6 px/cell — **not** from the
movie acceptance instrument, whose prompt is an open description ("main colors, the
shapes, what it depicts, how it changes"). It is real, blind, one-image-per-call
evidence that **grain texture becomes legible at σ=0.35·s and does not at σ=0.6·s**
— and nothing more. It does **not** close silhouette recognition; the movie
instrument has never produced an anatomy naming ("head/ears/limbs") under any
configuration in the log, for either physics version.

Also confirmed from the raw movie readings: under the new physics the eye reports
subject clipped at the frame edge (black bands top/bottom) — Run B's framing is a
confound its own note does not record.

---

## 4. Smallest evidence-backed experiment matrix

Goal: separate **geometry → projection/framing → presentation → reviewer
interpretation**, one variable per run, using existing verified machinery and the
standard movie instrument (12-frame omni watch) as the acceptance reviewer
throughout; expected reading and 0.6 threshold held fixed; no new physics law.

| run | buffer rendered | varied vs base | isolates | decision it feeds |
|---|---|---|---|---|
| E1 | none — re-score the **same** observed text vs the same expected reading, ≥3 fresh blind judge calls | judge calls only | reviewer-interpretation variance | if alignment spreads ≥0.1 across identical inputs, the 0.2–0.45 numbers carry that uncertainty |
| E2 | lattice emit(), σ=0.35, 12-frame movie, camera pulled back so subject ≈ 0.6 of frame height (**unclipped**) | framing only (vs Run B) | projection/framing | PASS → B's failure was framing; rerun the dyad properly. FAIL → framing exonerated |
| E3 | (conditional) same as E2 with σ=0.6 | presentation only | splat σ at movie scale | distinguishes "grain texture helps silhouette" from "σ irrelevant at k≈4.5"; skip if E2 PASS |
| E4 | the **smooth source cloud** (the lattice's own parent), matched camera/σ-mapping, same instrument | geometry only (cloud vs lattice) | geometry conversion vs reading/instrument | cloud reads as bear + lattice doesn't → geometry/reading mismatch real (escalate geometry preregistration, operator decides). Cloud also reads disc → the reading/instrument pair cannot see this scene class; operator-level instrument question, not a tolerance question |

All five raw readings and hashes archived per run; stills one-image-per-call;
k recorded with the **correct** lattice denominator (48) and clipping noted.
NOT_TESTED until run: E1–E4; judge identity; the 0.450 run's raw observation text.

**Base for all runs:** the current worktree state, unmodified — the review makes no
claim about whether the paw-width cell law or the grains reading is *correct*; it
only establishes what the next single-variable runs must hold fixed.

---

## 5. Provenance notes

- Reviewer's engine from the earlier session was drained (PID-verified kill);
  no engine was launched for this review.
- Run B's engine (PID 11448, `ChimeraEngine/engine/build/Release/chimera_engine.exe`,
  sha16 `79bfbe967401a869`, mtime Sep 6) was **not** touched.
- Store's `theShape` visual/movie pointers still reference the Aug-27/Sep-1
  artifacts; the store has not absorbed Run B's result at review time.
- `engine_state.json` / verdict-store tracked-status under git: not verified — UNKNOWN.
