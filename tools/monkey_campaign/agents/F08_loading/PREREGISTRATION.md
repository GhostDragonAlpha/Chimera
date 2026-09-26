# F08 Preregistration — frozen BEFORE implementation

Recorded 2026-09-24, before `forest_loader.py`, `verify_loading.py`, or any run.
Item F08, verbatim (MONKEY_COMPLETION_MAP.md:124): "Scene seed/configuration
reproduces assets, collision and initial state with clear failures for missing
assets. Resource cleanup uses existing lifecycle machinery."

Inputs, read and re-proved at load (all four validated live on 2026-09-24 before
this prereg was frozen; file sha256 measured on the committed bytes):

| Input | Path (repo-relative) | Self-pin (body) | File sha256 (committed bytes) |
|---|---|---|---|
| F01 clearing | `tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json` | `aa2607df97e0d6ec6a132b1e1ed0686da2ae920de7d659a8bb5ced013a358474` (`declaration_sha256`) | `18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1` (13,112 B) |
| F02 terrain bundle | `tools/monkey_campaign/data/monkey_clearing/terrain_bundle.json` | `8c7d60c88a75234a4ea94bc5ec83b666d620502b47cac8667e83b8713cb04fe0` (`bundle_sha256`) | `446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52` (877,752 B) |
| F03 trunk | `tools/monkey_campaign/data/monkey_trunk/trunk_declaration.json` | `b7089e7826a221a570b261b8c69666a4017a6ab62d20a2223d061654d0f63fe3` (`declaration_sha256`) | `94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1` (16,634 B) |
| F07 routes | `tools/monkey_campaign/data/monkey_routes/route_declaration.json` | `7c3ad6e86039b63324e4695abe5e5525e2693a98f9a0ef91355b804da8b8e211` (`route_declaration_sha256`) | `28dff2b33e74fcc4103ac3699899b0937f6975323758d1fa142092704bf4496c` (8,495 B) |

The F07 route declaration's `inputs` block carries the three upstream pins, so
one file carries the whole chain — but this loader does NOT trust stored pins
alone: it RE-COMPILES (F07's handoff law: re-compile, never copy).

## The theories (Rule 0 — statement / prediction / falsifier, before the build)

### T1 — The reproducibility contract (recompile, not copy)

**STATEMENT:** The integrated forest is fully determined by the recipe modules +
the scene seed: `clearing_recipe.compile_declaration(seed=4598321)`,
`terrain_bundle.compile_bundle(<recompiled clearing bytes>)`,
`trunk_recipe.compile_declaration(f01_declaration=<recompiled clearing>)`, and
`route_recipe.compile_declaration()` each re-produce their committed artifact
byte-for-byte. The committed files are derived data; the recipes are the law.

**PREDICTION (not yet measured by THIS agent):** all four recompiles are
byte-identical to the committed files — clearing 13,112 B sha
`18dd2ff6…`, terrain 877,752 B sha `446ed3fb…`, trunk 16,634 B sha `94ff906e…`,
routes 8,495 B sha `28dff2b3…` — across 2 in-process loads AND ≥3 fresh-process
loads (F07's own determinism protocol; the float pipeline is grid-snapped to
1e-6 precisely so libm ulp cannot move a byte).

**FALSIFIER (a):** any recompile producing even one different byte. A single
mismatch anywhere in the 4 × 3+1 matrix kills T1 and is reported RED, not tuned.

### T2 — The missing-asset contract (named refusal, exact artifact)

**STATEMENT:** Loading refuses BY NAME, with the exact absent artifact, when any
one of the four declarations is missing from the configured root — before any
recompile runs — and never touches real files to prove it (sandbox copy tree,
one file omitted per case).

**PREDICTION:** each of the 4 omissions raises `Refusal` code
`f08_missing_artifact` whose detail names (artifact key, absolute sandbox path);
all other 4×3 subsets still load green; zero real files are modified (verified
by re-hashing the four committed files after the whole suite).

**FALSIFIER (b):** a missing/corrupted artifact loading silently — any case
where the suite completes a load with an artifact absent or corrupt, or where
the refusal is a generic exception (FileNotFoundError, KeyError) instead of a
named code.

### T3 — The corruption contract (integrity failure is loud)

**STATEMENT:** Every tampered committed file is caught by a NAMED refusal that
identifies the artifact: (i) body-edit or pin-edit breaks the file's own
self-pin → `f08_invalid_artifact` carrying the recipe's own code
(`f01_digest_mismatch` / `f02_*` / `f03_digest_mismatch` / `f07_digest_mismatch`
family); (ii) a self-consistent RE-FORGE (body + pin both recomputed, so the
file lies coherently) survives the self-pin but cannot survive recompilation →
`f08_recompile_drift`; (iii) unparseable bytes → `f08_invalid_artifact` with the
recipe's `f0X_invalid_json` code.

**PREDICTION:** the corruption matrix (4 artifacts × {body-edit, pin-edit,
re-forge} + 1 garbage-bytes case = 13 cases) yields 13/13 named refusals, zero
silent loads, zero generic exceptions.

**FALSIFIER (b) again:** any matrix cell that loads or raises unnamed.

### T4 — The initial-state contract

**STATEMENT:** The initial scene state a player boots into — spawn pose, trunk
site, route graph parameters, collision surface identity — is DERIVED, not
restated: the loader composes it only from the four proven declarations, snaps
to the house 1e-6 grid, and self-pins it (`initial_state_sha256` over the
canonical body, house digest law).

**PREDICTION:** the record carries spawn `position_m = [0.0, 0.0, 0.0]` at
terrain height `0.0` with `body_radius_envelope_m = 0.25`; trunk site
`base_centre_m = [11.976783, 0.0, 2.471766]`, radius `0.037`, height `1.158`;
route graph spawn `[0,0]`, axis `[11.976783, 2.471766]`, straight `R0` length
`12.229185`, tangents `R1L…R5R` (10), grid 801×801 @ 0.05 m, blockers exactly
`[B1, B2]`; and its digest is IDENTICAL across 2 in-process loads and ≥3 fresh
processes.

**FALSIFIER (c):** initial state varying across loads — any digest difference
between processes, or any field above not equalling its declaring artifact.

### T5 — The cleanup hook (existing machinery, smallest adapter)

**STATEMENT:** The engine-process lifecycle already exists and is cited, not
rebuilt: `World.shutdown_engine()` (tools/playable_slice/slice_server.py:174-181
— `terminate()` → `wait(timeout=10)` → `kill()` → clear handle; invoked in
`main()`'s `finally` at :604-605 and at the top of every boot at :96) and
`SessionFlow`'s exit transition (tools/monkey_campaign/product/session_flow.py
— teardown callable fired exactly once, terminal `(exited, *)` rows deliberately
absent so "teardown never runs twice"; `TeardownDouble` at :141-151 is the
declared recording double). **The gap:** nothing exists for the DATA layer —
the four parsed declarations, the `terrain_query.TerrainSurface`, and the
initial-state record have no registry, no close, no drop anywhere on the
lineage. The smallest adapter: `ForestScene.teardown()` — a zero-arg callable
in EXACTLY SessionFlow's teardown shape, that (1) optionally runs an injected
`engine_shutdown` first (declared referent `World.shutdown_engine`, engine dies
before data drops, matching boot's own ordering), (2) releases every registered
resource BY NAME in reverse-load order, (3) audits zero live resources after,
(4) is idempotent per SessionFlow's law (second call is a named no-op receipt,
never a second teardown), (5) raises `f08_teardown_leak` if any release fails.

**PREDICTION:** on a full load, teardown releases 7/7 registered resources
(clearing, terrain, trunk, routes, terrain_surface, initial_state, engine
slot), the post-teardown audit names zero live resources, a second teardown
performs zero releases, and a leak-injection double (release raises) triggers
`f08_teardown_leak`.

**FALSIFIER (d):** teardown leaving declared resources live — the headless
test-double proof: a `ResourceDouble` registry proves every declared resource
received its release exactly once and none survives the audit; any survivor, or
a second-teardown that releases again, kills T5.

### T6 — The loaded surface is the real physics surface

**STATEMENT:** The loader hands W10 the ONE query implementation
(`terrain_query.TerrainSurface` over the proven bundle — never a second
heightfield), so post-load queries answer with the engine's own laws.

**PREDICTION:** through the loader's surface: `height_at(0,0) == 0.0` (spawn on
flat base ground by F01's construction); `gradient_at(17.0, 7.0)` magnitude
`0.042522` (F02/F07's recorded worst triangle); `classify(20.05, 0.0) ==
"outside"` while `classify(20.0, 0.0) == "inside"` (strict `>` extent law);
spawn-slope `0.0` consistent with the trunk record's
`terrain_slope_at_site_m_per_m = 0.0`.

**FALSIFIER:** any query answer diverging from those received numbers — the
loader would have bound a different surface than the declared one.

## Frozen values (no tuning after this point)

- Scene seed: `4598321` (F01's `seed`; ASCII "F01" — consumed, never re-chosen).
- Recompile chain (dependency order, each from RECOMPILED upstream, never from
  the committed copy): clearing from seed → terrain from recompiled-clearing
  temp file (`compile_bundle` reads a path) → trunk from recompiled clearing
  dict → routes via `route_recipe.compile_declaration()` (its own
  `load_live_inputs` reads the REAL pinned tree — that module's pins are frozen
  law; the loader's recompile-drift check is what proves the configured root's
  copy faithful).
- Refusal codes (new, `f08_` namespace, house `Refusal` class with `.code`,
  `.detail` plus `.artifact`/`.path`/`.cause`): `f08_missing_artifact`,
  `f08_invalid_artifact` (cause = the recipe's own code),
  `f08_recompile_drift`, `f08_recompile_refused` (cause = the recipe's own
  code, live-tree drift), `f08_teardown_leak`, `f08_teardown_state`
  (misuse: teardown contract violated by the adapter itself), `f08_cli_verb`.
- Per-artifact check order (fixed): presence → recompile → validate recompiled
  → parse committed (strict) → committed self-pin → committed validator →
  byte-compare committed vs recompiled. Phase A (presence, all four) precedes
  Phase B; Phase B runs in dependency order clearing → terrain → trunk →
  routes.
- Teardown ordering: engine_shutdown (if injected) → resources in reverse-load
  order → audit → terminal. Second call: named no-op.
- Initial-state record schema: `chimera.monkey_forest.v1`; fields frozen to the
  T4 list; digest over the canonical body without the pin (house law).

## Declared write paths (integrity envelope)

- `tools/monkey_campaign/agents/F08_loading/` — brief.md,
  PREREGISTRATION.md, verify_loading.py, HANDOFFS.md, report.md, receipts/.
- `tools/monkey_campaign/data/monkey_forest/forest_loader.py` — the ONE new
  data-layer module (name declared here BEFORE implementation; disjoint from
  every existing module; follows the recipe/data directory pattern).
- Nothing else. No existing file modified; no engine C++; CPU-only; headless;
  no servers; sandbox tests copy files into a temp dir and never delete or
  rewrite real files.

## Post-run amendments

None permitted without a new falsifier set. F05's future envelope re-freeze
(amendment path in F07's HANDOFFS) will change the route declaration's bytes —
at that point this loader's job is to REFUSE (`f08_recompile_drift`) until the
committed artifacts are recompiled through the recipes, which is the contract
working, not failing.

## Amendment 1 (2026-09-24, BEFORE any implementation or run)

T2's prediction as first frozen contained an error: "all other 4×3 subsets
still load green" is incoherent — a root from which the clearing is omitted
cannot load, and must not. The corrected prediction, frozen before one line of
loader code exists: each of the 4 omissions raises `f08_missing_artifact`
naming exactly that artifact and its absolute sandbox path; the four presence
checks are INDEPENDENT (Phase A checks all four before Phase B runs, so the
named artifact never depends on compile order); the happy-path control (all
four present in the sandbox) loads green. No other prediction changes.

## Amendment 2 (2026-09-24, BEFORE the verify suite is written)

T6 misattributed a received number: F02/F07's `0.042522289` is the SURFACE-WIDE
worst-triangle slope (`TerrainSurface.worst_triangle_slope()`, the measure F02's
receipt and F07's handoff actually record, located at triangle first-vertex
(17.0, 7.0)), not the containing-triangle point query `gradient_at(17.0, 7.0)`
— the point (17, 7) sits on a grid node shared by six triangles and its
containing triangle answers `0.029843375278275748`. The corrected T6
predictions, frozen before verify_loading.py exists: `worst_triangle_slope()`
returns exactly `0.042522289331596436` at `(17.0, 7.0)` (bit-for-bit F02's
receipt); `height_at(0,0) == 0.0`; `gradient_at` at the spawn AND at the trunk
site `(11.976783, 2.471766)` equals `(0.0, 0.0)` (both on flat base ground);
`classify(20.05, 0) == "outside"`, `classify(20.0, 0) == "inside"`; and a
height query at `(20.05, 0)` refuses with `f02_outside_extent`. All measured
once in a probe BEFORE this amendment was appended; the suite freezes them as
assertions. No other prediction changes.


## AMENDMENT 3 (2026-09-24, coordinator, per R5 review N1)
The routes recipe's R0 note was corrected (STOP t=11.942185 vs length_m=12.229185 = spawn-to-AXIS distance, not walkable length). The declaration regenerated (8495->8630 bytes; new sha256 dab19459863ad3c0e58f048c81bb56fd8ecf39d9722681252d1f82c1c3c15849); the frozen byte table and committed-sha table updated accordingly. No falsifier changed; re-run below.
