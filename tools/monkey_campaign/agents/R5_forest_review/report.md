# R5 Report — INDEPENDENT NON-AUTHOR REVIEW of the forest front (F01–F08) as an integrated whole

Reviewer: R5. Date: 2026-09-24. Worktree `E:/ChimeraWork/monkey-play-20260924`,
branch `monkey-play-20260924`, reviewed state = committed HEAD `9afbddcd`
("FOREST FRONT F01–F08 COMPLETE; W10 scene-ready") with a clean tree under
`tools/monkey_campaign/`. R5 authored none of the reviewed items. CPU-only,
headless, stdlib-only. Checklist frozen BEFORE any run:
`work/checklist.md`. All numbers below were re-measured by R5 from scratch
unless explicitly marked as read from a committed receipt.

## VERDICT

| Item | Verdict | Basis |
|---|---|---|
| F01 clearing | **APPROVE** | All claims reproduced; deterministic recompile byte-exact in a fresh subprocess |
| F02 terrain | **APPROVE** | Render/query identity holds at 1e-17 family; honesty row (ulp) independently re-observed |
| F03 trunk | **APPROVE** | Site pinned to F01; derivations, mesh, representation error all reproduce |
| F04 contact | **APPROVE** | 13/13 with firing controls; decisive numbers independently recomputed; L2 gap honestly recorded |
| F07 routes | **APPROVE-WITH-NOTES** | Scene numbers all reproduce; ONE note: R0 endpoint semantics in the committed declaration (Note N1) |
| F08 loading | **APPROVE** | Recompile-not-copy proven; CLI receipt byte-exact vs its own claim; refusal matrix real |
| **FRONT-LEVEL** | **APPROVE-WITH-NOTES** | One coherent world; notes N1–N3 below; nothing blocks the front |

**W10-readiness: the forest front is genuinely scene-ready** — the map's W10 row
("Player can walk, turn and stop in the scene on a supported surface; numerical
and visual receipts match") can consume this front today via `ForestScene` +
`terrain_query.TerrainSurface` + the `engine_shutdown` injection point. W10
itself remains blocked by things OUTSIDE this front, all already recorded by the
authors, none hidden: (1) the frozen engine has no heightfield/prop contact
service (F04's L2 statement — a separately-gated engine task owed to G04/W10);
(2) walking training/execution W05–W09; (3) U02's camera (separate lane). No
further gap is owed by F01–F08.

## 1. Cross-artifact identity receipts (15/15 green — `receipts/identity_receipt.json`)

Recompiled ALL FOUR declarations from the recipe modules in a FRESH SUBPROCESS
(recompile-not-copy, R5's own harness, not F08's):

| Artifact | Recompiled bytes | file sha256 (recomputed = committed = claimed) | self-pin (recomputed = committed = claimed) |
|---|---|---|---|
| clearing | 13,112 | `18dd2ff65410cd1c…` | `aa2607df97e0d6ec…` |
| terrain | 877,752 | `446ed3fbd0f50205…` | `8c7d60c88a75234a…` |
| trunk | 16,634 | `94ff906ec5e8b838…` | `b7089e7826a221a5…` |
| routes | 8,495 | `28dff2b33e74fcc4…` | `7c3ad6e86039b633…` |

Mutual pins, independently confirmed:
- Trunk→F01: `trunk.site.provenance.declaration_sha256` = clearing body pin `aa2607df…` — holds.
- Terrain→F01: bundle `source` carries F01's body pin `aa2607df…`, file sha `18dd2ff6…`, schema, seed 4598321 — holds.
- Routes→{F01,F02,F03}: `inputs` pins all three body pins AND file shas — all six hold.
- Loader→all four: receipt re-states all four file shas + self-pins; `initial_state_sha256` `c3286e14a787f6bb…` reproduced from scratch (in-process and via the CLI).

One-number invariants:
- **Trunk site** `(11.976783, 0.0, 2.471766)` identical in F01 `trunk_sites[0]`, F03 `site.base_centre_m` and `solid.axis_base_m`, F07 `routes.trunk_axis_m` and blocker B2 `site_m` (the route layer stores planar `[x,z]` — consistent), and F08's `initial_state`.
- **Spawn** `(0,0,0)` identical in F01, F03, F07, F08.
- **B2 r_block** = 0.037 + 0.250 = 0.287 exactly; **extent** half-width 20.0 identical in F01/B1/F07; **seed** 4598321 everywhere; site annulus prereg bounds hold (dist 12.229185 ∈ [8,14]; inset 8.023217 ≥ 3).
- Route graph vs F04's blocking causes: F07's B2 predicate is exactly F03's analytic solid + F01's body envelope; N1 (slope) and N2 (posts) match F04's VIS-03 NO-CLAIM; zero unexplained causes confirmed by R5's own 641,601-cell sweep (below).

## 2. Integrated scenario (R5's own, headless — 36/36 green — `receipts/integrated_receipt.json`)

Loaded via F08's `load_forest()`, then queried F02 → F04-style SDF → F07 corridor in one process:

- **Loader**: four artifacts recompile-identical; CLI `receipt` run twice from scratch, raw stdout sha256 `facca270dcd4fd9e…` — **byte-exact equal to the sha F08's determinism receipt claims** (first R5 mismatch was R5's own CRLF normalization of the pipe, not the artifact).
- **F02 surface at trunk site**: `height_at = 0.0`, `gradient_at = (0,0)`, `normal = (0,1,0)` exactly; same at spawn; `worst_triangle_slope() = 0.042522289331596436` at `(17.0, 7.0)` — bit-for-bit F02's receipt; strict-`>` extent verified (20.0 inside, 20.05 refused `f02_outside_extent`).
- **F04-style trunk SDF (R5's own capped-cylinder implementation)**: on-axis sdf = −0.037 exactly (F04 GHO-03); worst |sdf − r_sole| over 320 lateral tangency points = **8.4e-16** (F04 recorded 7.0e-16 — same machine-epsilon scale); trunk chord error recomputed from the stored vertex table = **1.783070e-4 m** (declared 1.78307e-4 ≤ TOL 2e-4).
- **Trunk flushness (the brief's named falsifier)**: over the full 0.5 m footprint disk (81×81 clipped), worst |terrain height| = **0.0** and worst |gradient| = **0.0** — the analytic y=0, the F02 query surface, and the F03 base cap (65 vertices at y=0.0) are EXACTLY coplanar. The site's declared slope 0.0 is true: the site clears every mound by ≥ 5.06 m (margins [29.98, 20.19, 5.06, 24.92, 26.85] m), analytic h(site) = 0.0. **The trunk base sits flush — no gap, no burial.**
- **F07 corridor (R5's own sweep + BFS over 801×801 @ 0.05 m)**: blocked cells = **107**, all inside the B2 disk (claimed 107, all B2); free cells = 641,494, **all reachable** from spawn (claimed 641,494/641,494); worst grid gradient 0.042522 (slope never blocks); a ≥ 1.0 m-wide (clearance ≥ 0.5 m) corridor connects spawn to the trunk approach zone; gate clearance at (11.3, 2.0) = **0.537984** (F07's claimed 0.538 → width 1.076); R0 min clearance outside the approach zone = **0.502185** (claimed 0.502).
- **Edges/negatives**: all four closed corners answer finite height/gradient/normal; `−0.0` safe; 6/6 past-edge queries (including negative side and +1e-9 overshoots) refuse `f02_outside_extent`; the A/B triangle formulas agree on cell diagonals to 2.8e-17 m (see honesty row).
- **Loader initial_state vs F07 declaration**: spawn/axis/straight/tangents/grid/blockers copied verbatim (no restatement drift). Teardown: 7/7 resources released, zero live.

## 3. Citation spot-checks (19 named checks / 24+ citations — `receipts/citations_receipt.json`)

Per item, 3+ each, all reproduced against the tree:

- **F01**: worst central-difference grid slope **0.034606** at (17,6) — exact under F01's own max-norm convention (`clearing_recipe.py:426 max(…, gx, gz)`; R5's isotropic-hypot variant gives 0.034616, also ≤ 0.05); spawn clearance **11.729184690233646** m exact to the last digit; 80 posts, worst off-edge **0.0**, spacing 2.0. Plus bytes/digests in §1.
- **F02**: mesh **13,920 v / 13,920 i / 4,640 tri** (3,200 ground + 1,440 post) exact; mesh↔analytic deviation at (19.5,5.5) = **6.460 mm** (claimed worst); worst triangle slope bit-exact (§2). Plus bundle digest in §1.
- **F03**: H = (0.419+0.482)+(0.125+0.132) = **1.158**, R = 0.074/2 = **0.037**; energies m·g·H = **113.992539 J**, m·g·(H−0.901) = **25.298862 J**; sagitta R(1−cos(π/32)) = **1.781651e-4** vs measured chord 1.783070e-4. Plus declaration digest/site pin in §1.
- **F04** (committed `run.json`, hash-verified `efded804…`, 10,442 B): **13/13 PASS** verdicts recorded; INT-01 worst tangency **7.043e-16**; INT-03 worst |terrain h| = **0.0** (both independently re-measured by R5 in §2); VIS-03 envelope overlap **0.23268 m PASS-AS-DECLARED NO-CLAIM**.
- **F07**: free/blocked **641,494 / 107 all B2** (recomputed); corridor **0.538** @ (11.3,2.0) and R0 **0.502** (recomputed); analytic slope bound **0.037956** = A₂·π/(2R₂) exact; 10 tangents all construct with endpoints inside the closed extent. Plus digest in §1.
- **F08**: `run.json` **verdict GREEN, 66/66 `pass: true`** (hash-verified `4ebd3a6c…`); CLI receipt stdout **byte-exact** vs its own `facca270…` claim; `worst_triangle_slope` bit-exact through the LOADED surface; `forest_loader.py` sha `53d7fdde…` and `verify_loading.py` sha `fc4d34ab…` both verified.

**R5 honesty row**: three initial REDs in R5's own harness were R5's errors, not the artifacts': (1) R5 compared the planar `[x,z]` route layer against `[x,y]`; (2) R5 precomputed the gate clearance sloppily (0.538247; true 0.537984 — the artifact is right); (3) R5 predicted diagonal identity "exactly 0.0" and measured 2.8e-17 — R5 thereby INDEPENDENTLY reproduced the same ~1-ulp effect F02 already recorded in its honesty row, inside the frozen 1e-9 family. F01's "worst grid slope" first looked off by 1e-5 until R5 found the max-norm convention; under the declared convention it is exact. No author number required tuning.

## 4. Falsifier-mining notes (what no suite tried; measured, none blocking)

- **N1 (F07) — R0 endpoint semantics, the front's one real documentation hazard.** The committed `route_declaration.json` R0 carries `to_m` = the trunk AXIS and `length_m` = 12.229185 (the full axis distance), while its `note` says it "ends at the contact ring: dist_to_axis = r_block". Both cannot be read literally at once: at t = length_m the walker's centre is ON the axis (dist_to_axis = 0.0000, envelope ~0.287 m inside the blocker; ~29 samples at 0.01 m step lie inside B2). The recipe and the verify suite both handle it correctly (`t_contact = length − end_short` → contact at t = 11.942185; `contact_dist_from_axis_m = 0.287`), and `length_m` rounds the true axis distance 12.22918469… exactly, so nothing green depends on the naive reading — but a W10 consumer who walks `length_m` as a walked length drives the monkey through the trunk. **Smallest fix, when next touched: a prereg amendment adding `walked_length_m: 11.942185` (or rewording the note). Not a defect in any measured number.**
- **N2 — refusal-class split.** `terrain_query` raises `terrain_bundle.Refusal`; `forest_loader` defines its own distinct `Refusal`. A W10 harness that catches the loader's class around surface queries will leak recipe refusals. No committed path is broken (each layer catches its own); carry as a W10 integration note.
- **N3 — posts straddle the physical edge by design.** Ground mesh max x = 20.000000 exactly; all-vertex max = 20.05 (post girth). Posts are render-only NO-CLAIM (F04 VIS-03): a walker stopped by the extent rule visually overlaps post prisms, and camera occlusion cases (C23/U02) must not treat posts as blockers. Already declared by F02's amendment; restated here as a W10 visual fact.
- **Mound 2 is clipped by the world edge** (analytic reach x = 23.595 m; h_analytic(21,6) = 0.068 m exists outside the query domain and the query refuses; the ground mesh ends at 20.0). Consistent with every declaration; the world visibly ends at the post line on that flank.
- **Trunk radius 0.037 m is a derivation, not evidence** — the Oku foot is the span proxy while A05 (hand digits) is open, honestly labelled in F03; G01 consumes it as declared. R5 flags for G01: an opposed grip span of 7.4 cm on a 10 kg macaque is the consequence of that proxy, and any G01 verdict inherits its provenance.
- **F-row "done when" floated against reality**: F01/F03/F07/F08 rows are met outright on the measured evidence. F02 and F04 are met within their declared two-layer separation: "rendered ground and physical query surfaces agree" holds because the render arrays ARE the query surface (agreement 1e-17 family, re-verified), and F04's "no unacceptable tunnelling/ghost/interpenetration/disagreement" holds for the declared geometric model with firing controls — while the map's "Reuse engine geometry/collision paths" clause remains only partially satisfiable until the recorded engine-side contact service exists (native engine has plane-only contact; no mesh-collision route). This is recorded by the authors, not discovered by R5; it is the honest boundary of the front.

## 5. W10-readiness verdict

**The scene is genuinely ready to serve W10.** One coherent world, verified end-to-end through the production loader: deterministic four-artifact identity, one spawn, one trunk site, one blocker set, routes and contact agreeing with the terrain they stand on. W10's remaining prerequisites are outside this front and already on the map's books: the engine contact-service task (gated, preregistered — F04's L2), walking W05–W09, and U02's camera. The forest front owes nothing further.

## 6. Integrity

R5 wrote ONLY `tools/monkey_campaign/agents/R5_forest_review/` (brief.md, report.md, work/ ×4 scripts + checklist, receipts/ ×3 JSON). `git status --porcelain -uall` shows no tracked modification anywhere; the only untracked paths outside R5's dir are two pre-existing parallel-session leftovers (U02's modified receipt, TIE2's out file) noted by earlier reports, untouched by R5. The only bytes R5 caused outside its dir are Python interpreter `__pycache__` entries regenerated for the imported (unchanged) recipe modules during re-running — sources unmodified, git-invisible, consistent with the existing campaign pattern. Nothing outside the review dir was modified by hand; no engine C++; no GPU; no servers; CPU-only headless throughout.

## Receipts (this dir)

- `brief.md` — verbatim task brief.
- `work/checklist.md` — preregistered checklist, frozen before any run.
- `work/r5_identity.py` → `receipts/identity_receipt.json` — 15/15.
- `work/r5_integrated.py` → `receipts/integrated_receipt.json` — 36/36.
- `work/r5_citations.py` → `receipts/citations_receipt.json` — 19/19.
- Total: 70/70 checks green; 3 harness REDs resolved against R5 (documented above), 0 against the artifacts.
