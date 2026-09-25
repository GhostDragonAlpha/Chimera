# R5 forest-front review — CORRECTED VERDICT (native-readiness separation)

| field | value |
|---|---|
| Task | `R5-forest-review` (Kanban slot 10) |
| Attempt | `92f723834c64405aae3e8debabc65418`, branch `codex/monkey-r5-forest-review-92f723834c` |
| Criteria hash | `6198e40ba1cfe37059275bc908e55e1e4fa804d58d418bcc21ea8520e4753ae6` |
| Responds to | lead finding `msg-183cad37dbef420ea1122e84d6720cf6` (astra-codex, OPEN) |
| Reviewer | non-author correction attempt; original R5 findings preserved, none retracted |
| Reviewed tree | play worktree `E:/ChimeraWork/monkey-play-20260924`, branch `monkey-play-20260924`, HEAD `dc7ea81111d98f32a4d88252c59f2fb8cf3c7399`, clean status under `tools/monkey_campaign/` |
| Method | read-only over the play worktree; CPU-only; no engine process, no GPU, no source edits; all identities re-measured fresh by `tools/measure_evidence.py` (13/13 green, `evidence/identities.json`) |

## 1. The corrected verdict

Two published claims are corrected by this review:

1. Commit `9afbddcd90164b5544a16fd0bc72278d985eb6e3` — subject ends
   *"FOREST FRONT F01-F08 COMPLETE; W10 scene-ready."*
2. The integrated R5 report (`report.md`, blob `f18eea1baeb4`, integrated at
   `dc7ea811…` whose subject says *"W10 SCENE-READY"*) — §5 states
   *"The scene is genuinely ready to serve W10… The forest front owes nothing further."*

Both conflate **verified static results** with **native playable readiness**. Corrected:

> **F01, F02, F03, F04, F07, F08 are verified at the static/declarative level only.
> F05 and F06 are NOT complete — they were never started. The forest front is NOT
> "F01–F08 complete". W10 is NOT ready: native heightfield contact, native trunk
> (rigid-prop) contact, trained walking (W05–W09), and in-scene walking/camera
> acceptance are all missing. The F02/F03/F04 receipts are Python-side static
> verifications; their own recorded statements say the native engine cannot
> exercise them today.**

### Per-item corrected table

| Item | Corrected status | Basis (identity in §6) |
|---|---|---|
| F01 clearing | **VERIFIED (static/declarative)** — preserved | deterministic recipe, extent/spawn conventions; R5 identity receipt 15/15 includes it |
| F02 terrain | **VERIFIED STATIC ONLY — native collision NOT established** | render==query agreement (1e-17 family) is a Python-binding property; F02's own report §follow-up item 3: *"Native heightfield contact does not exist (`earth_environment.hpp` is a plane; `gait_controller.hpp` walks `contact_plane_height_m`) … Until then the clearing's physical surface is this Python binding"* |
| F03 trunk | **VERIFIED STATIC ONLY — native trunk contact NOT established** | geometry/derivations/mesh reproduce; but F04's L2 statement: *"trunk contact does not exist (no rigid-prop machinery at all)"*; friction is an declared UNEVIDENCED PLACEHOLDER owed to G04 |
| F04 contact | **VERIFIED STATIC ONLY — zero cases exercised in the native engine** | 13/13 + firing controls are headless geometric checks; F04's own L2 statement: *"Consequently NONE of F04's cases can be exercised in-vivo today"* |
| F05 terrain range for walking | **NOT STARTED — not complete, not blocked-resolved** | no artifacts exist (§4); prerequisites F02 ✓ but W06 ✗ (walking evaluation not done) |
| F06 terrain-aware walking | **NOT STARTED — not complete** | no artifacts exist (§4); prerequisites F05 ✗ and W07 ✗ |
| F07 routes | **VERIFIED (static/declarative)** — preserved | 641,494/641,494 reachability, corridor, blocking-causes are static scene-graph facts; route *execution* by a walker is W10 territory and unexercised |
| F08 loading | **VERIFIED (static/declarative)** — preserved | 66/66 loader determinism/refusals/teardown are Python-loader facts; loading a scene the native contact model cannot stand on does not make it playable |
| **Front level** | **CORRECTED: front = 6 of 8 items verified static; F05/F06 open; native readiness absent** | replaces "F01-F08 COMPLETE; W10 scene-ready" |
| **W10** | **NOT READY** (was: "scene-ready") | §5 prerequisite audit |

The card's falsifier — *"Static Python receipts credited as native W10 playable readiness,
or omitted F05/F06 gates counted complete"* — is answered: this review credits them as
static only and counts F05/F06 open.

## 2. What remains verified — the original R5 findings stand, as STATIC verification

Nothing in the original R5 review is retracted. Its 70/70 checks (re-counted from the
committed receipts: 15/15 identity, 36/36 integrated, 19/19 citations) are valid and
preserve author/source identities (blobs in §6). Specifically still true:

- Four forest declarations recompile byte-identical in fresh processes; mutual pins
  (clearing/terrain/trunk/routes/loader) all hold.
- One coherent world: single trunk site `(11.976783, 0.0, 2.471766)`, single spawn,
  one blocker set; trunk base coplanar with the queried surface (worst |h| = 0.0 over
  the footprint disk).
- Route layer: all free cells reachable; corridor ≥ 1.0 m; blocking causes fully
  explained (B1 extent + B2 trunk only).
- Loader: deterministic `initial_state` digest, named refusal matrices, teardown 7/7.
- Notes N2 (refusal-class split) and N3 (posts straddle the edge, render-only) remain
  correct and now become **native-integration warnings** rather than footnotes, because
  W10 will be the first consumer that actually stands a walker in this world.

The boundary is the evidence class, not the arithmetic: every one of those checks ran
headless in Python. **No native engine process was launched by F01–F08 or by R5** —
F02's report states this explicitly ("no engine process was launched (CPU-only prereg)").

## 3. The separation: what each claimed capability is actually evidenced by

| Claimed capability | Evidence actually on file | Class | Missing for native/W10 |
|---|---|---|---|
| Terrain height/normal queries | `terrain_query.TerrainSurface` (Python) render==query to ~1e-17 | **static** | native walker contact: engine ground is ONE plane at `contact_plane_height_m` (`gait_controller.hpp:94`, `:2005-2010` verified in-tree) |
| Trunk collision | F03 analytic solid + F04 SDF tangency 7e-16 (Python) | **static** | no rigid-prop machinery in engine; meshes render-only, no collision query route in HTTP contract (F04 L2 citations, verified `earth_environment.hpp:67,118`) |
| Ground+trunk multi-surface support | none — declared out of scope by F04 | **gap** | no solver rows for non-(0,1,0) normals; separately-gated engine task owed to G04/W10 |
| Continuous collision / tunnelling safety | F04 firing controls (headless geometry) | **static** | engine has kTouch tick band vs one plane only (F04 L2) |
| Repeatable scene loading | F08 66/66 incl. fresh-process recompiles | **static, but directly consumable** | nothing — loader determinism is real; what it loads cannot yet be stood upon natively |
| Traversable routes | F07 static sweep/BFS | **static** | a walking policy to traverse them (W05–W09) |
| Follow camera | U02 module receipts (24/24 on the full-state POST /camera contract, per board) | **module-level** | in-scene acceptance with a walking subject (W10's visual receipts) |
| Player walks/turns/stops in scene | none | **gap** | W05 training run ("no reported completed run", map W05 row), W06 evaluation, W07 native policy load, W08 command verification, W09 out-of-envelope behavior |

## 4. F05/F06 — explicit accounting (they are not complete)

Definitions (MONKEY_COMPLETION_MAP.md, blob `95a3e36ac995`, measured verbatim):

- **F05** — "Specify the terrain range for walking"; prerequisites **F02, W06**; done when
  "Slope, obstacle size and surface-friction envelope is declared from evidence".
- **F06** — "Implement and qualify terrain-aware walking"; prerequisites **F05, W07**; done
  when "Player walks the declared uneven-ground cases with certified runtime/training agreement".

Measured state (all checks in `evidence/identities.json` → `f05_f06_absence`):

- No `agents/F05*` or `agents/F06*` directory exists (full agent-dir list recorded).
- No tracked file under `tools/monkey_campaign` matches F05/F06.
- The PLAY_BOARD "Forest" row (blob `26e6d47a8bae`) names F01, F03, F02, F04, F07, F08
  states — it contains **no F05 or F06 state at all**; the row's "F01→F08" front label and
  the "FOREST FRONT F01-F08 COMPLETE" conclusion covered six items.
- The only F05/F06 references in the tree are forward-looking: F02's report names them as
  the intended consumers of `terrain_query.TerrainSurface` once walking exists.

Prerequisite reality: W06 (evaluate trained walking) is not done — the map's own W05 row
records *"no reported completed run"*, and the board's walking chain shows W03 remainders
open (GPU legs queued behind broker, C3 clean-window, anchor A/B, C++-leg tie gap).
**F05 is therefore blocked on the walking chain, not merely unlisted; F06 is blocked on F05
and W07. Counting them under a "F01–F08 COMPLETE" heading was the error this review corrects.**

## 5. W10 readiness — corrected verdict

W10's row: "Accept walking in the actual game scene"; prerequisites **W08, W09, F04, U02**;
done when "Player can walk, turn and stop in the scene on a supported surface; numerical
and visual receipts match".

Prerequisite audit at HEAD `dc7ea811…`:

| Prerequisite | State | Evidence identity |
|---|---|---|
| W08 commanded start/stop/speed/heading | **OPEN** — needs W07 | board walking chain (W03 remainder open) |
| W09 out-of-envelope behavior | **OPEN** — needs W07 | same |
| F04 contact geometry | **row met at its declared L1 scope only** — the same receipt's L2 statement records that no case can run in the native engine | F04 report blob `af679533dfb7` |
| U02 camera | **module-level receipts only** — no in-scene walking acceptance | board Controls row (U02 DONE, 24/24) |
| (feeding all) native heightfield/trunk contact service | **DOES NOT EXIST** — separately-gated engine task, unassigned at HEAD | F02 report item 3; F04 L2; verified engine sources §6 |

**Corrected verdict: W10 is NOT ready.** The original R5 sentence "the map's W10 row … can
consume this front today via `ForestScene` + `terrain_query.TerrainSurface` + the
`engine_shutdown` injection point" is corrected to: those Python entry points can *supply
scene data* to a future W10 harness, but the native walker cannot stand on
`TerrainSurface` — the engine's physical ground is a single plane, and the native walker's
contact model has no heightfield and no trunk. "Scene-ready" as published overstated the
front by exactly the distance between a verified static scene description and a playable
native scene: the engine contact-service task, the walking chain W05–W09, and in-scene
camera/walking acceptance.

What would make W10 genuinely consumable (unchanged from the authors' own records, now
stated as prerequisites rather than footnotes): (1) the separately-gated engine
contact-service task (per-point surface service implementing F03's analytic contract +
F02's terrain query; multi-normal rows into the existing friction solve; a collision query
route; measured bark friction); (2) W05 training executed and W06 evaluated; (3) W07
native policy load; (4) W08/W09 verification; (5) the W10 acceptance run itself with
numerical + visual receipts, camera in scene.

## 6. Source and receipt identities (all re-measured at play HEAD `dc7ea811…`)

| Object | sha256 (first 20) | git blob | role |
|---|---|---|---|
| claim commit | — | `9afbddcd90164b…` | subject: "…FOREST FRONT F01-F08 COMPLETE; W10 scene-ready" |
| R5 integration commit (= HEAD) | — | `dc7ea81111d9…` | subject: "…W10 SCENE-READY (70/70 …)" |
| `agents/R5_forest_review/report.md` | `665ed6c84936be9c1add` | `f18eea1baeb4` | original review (PRESERVED, untouched) |
| `agents/R5_forest_review/brief.md` | `c6d00207113764d1987c` | `68430c5db851` | original brief |
| `…/receipts/identity_receipt.json` | `5e22eac9dcc1dccd5423` | `1f6fd85293fb` | 15/15 (re-counted) |
| `…/receipts/integrated_receipt.json` | `9535e292ca803296c3d1` | `d5672e1c2417` | 36/36 (re-counted) |
| `…/receipts/citations_receipt.json` | `b4492907f9091d28e426` | `ce9b7e5147b8` | 19/19 (re-counted) |
| `tools/monkey_campaign/PLAY_BOARD.md` | `78f1d5bb6baacf929e32` | `26e6d47a8bae` | carries the front-complete board claim (Forest row) |
| `tools/monkey_campaign/MONKEY_COMPLETION_MAP.md` | `ff1eecb594b38e19297b` | `95a3e36ac995` | F05/F06/W05/W10 row definitions |
| `agents/F02_terrain/report.md` | `1dd5299ec2e63addaccf` | `f6b094988b56` | native-heightfield gap statement (follow-up item 3) |
| `agents/F04_contact/report.md` | `14ab9ded69635facc916` | `af679533dfb7` | L2 engine-service gap statement |
| `ChimeraEngine/engine/gait_controller.hpp` | `7b2ee097f19d777e0972` | `5863348f2dee` | `:94` single `plane_model_y_`; `:2005-2010` friction/1..8 contact points (verified in-tree) |
| `ChimeraEngine/engine/earth_environment.hpp` | `af98f59a3f1ea7727207` | `38edb9807b61` | `:67` sphere-vs-plane impulse; `:118` strict out-of-patch (verified in-tree) |

Full hashes, byte sizes, verbatim map rows, agent-dir listing and every check detail are
in `evidence/identities.json` (schema `r5.correction.evidence.v1`, 13/13 green).

## 7. Method and integrity

This correction: read-only over the play worktree; wrote only inside this attempt
workspace (`E:/ChimeraWork/monkey-coordination/kanban-attempts/R5-forest-review/92f723834c64405aae3e8debabc65418`);
CPU-only, stdlib-only; no engine launch, no GPU, no training, no physical threshold
altered, no duplicate verification runs beyond fresh hashing/counting of committed files
(the original 70/70 measurements were NOT re-run — they are preserved as authored and
re-counted from their committed receipts). The play worktree's tracked files are
unmodified; the original R5 report and all author artifacts remain exactly as integrated
at `dc7ea811…`.
