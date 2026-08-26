# THE TWIN TABLE — A3 Phase 1 adjudication (2026-08-26)

**The defect.** `ChimeraEngine/engine_state.py` inserts `E:\PythonChimera\Chimera` at
`sys.path[0]` before importing `core.saturation`, so every **wired** process (anything that
imports `engine_state`: `mcp_server`, `orient`, the gates) freezes package `core`'s `__path__`
to **`Chimera/core/`**. Processes that never import `engine_state` and put `ChimeraEngine/` on
`sys.path` themselves (script-dir auto-prepend or explicit insert) bind **`ChimeraEngine/core/`**
instead. Same `import core.X`, two different files.

**Method.** Every module name present in both trees (30 at `core/` level + 1 under
`core/trainables/`; the task's "45" estimate was high — actuals below) was compared by raw
SHA-256, then by `git diff --no-index` (CRLF-normalizing), then by AST parse of top-level
def/class names + line spans. Importer scan (`rg` for `import core.X` / `from core.X`) across
the repo excluding `attic/`, `__pycache__`, the two core trees themselves, and prose; each hit
adjudicated by reading its module's `sys.path` handling.

**STATEMENT:** the ChimeraEngine copies deleted below are inert — no live process executes
them, and their content is identical to the Chimera copy a wired process would load anyway.
**PREDICTION (untested before this run):** deleting them changes no observable behavior:
ports stay 18/21 with unchanged drift, `engine_state` still binds `Chimera/core`, and the
non-wired witnesses (`physics.py`, `fields_witness.py`) still import their engine-bound twins.
**FALSIFIER:** ports move off 18/21, or any smoke entry point raises ImportError, or the new
guard in `engine_state.py` fires in a clean wired process. Result: NOT FALSIFIED (smoke log in
commit message; drift numbers identical to the accepted set recorded in 1bbae9f1).

## The table

| name | classification | wired tree executes | action | divergent-defs summary |
|---|---|---|---|---|
| biomes | CONTENT-EQUAL (LF vs CRLF only; git diff empty) | Chimera | DELETED engine copy | — |
| capcom | BYTE-EQUAL (sha256) | Chimera | DELETED engine copy | — |
| circadian | BYTE-EQUAL | Chimera | DELETED engine copy | — |
| dna_sqlite_backend | BYTE-EQUAL | Chimera | DELETED engine copy | — |
| eden | CONTENT-EQUAL (EOL-only) | Chimera | DELETED engine copy | — |
| graphify_interface | BYTE-EQUAL | Chimera | DELETED engine copy | importers: dead `archive/one_off_scripts` + `Chimera/dna_dashboard.py` (Chimera-side binding) |
| helm | BYTE-EQUAL | Chimera | DELETED engine copy | zero importers anywhere |
| history_book | BYTE-EQUAL | Chimera | DELETED engine copy | zero importers |
| lm_gateway | BYTE-EQUAL | Chimera | DELETED engine copy | zero importers |
| matter_items | BYTE-EQUAL | Chimera | DELETED engine copy | sole importer is dead `archive/old_stacks/splat_gpu.py` |
| membrane_shapes | CONTENT-EQUAL (EOL-only) | Chimera | DELETED engine copy | zero importers |
| metronome | BYTE-EQUAL | Chimera | DELETED engine copy | zero importers |
| perception | CONTENT-EQUAL (EOL-only) | Chimera | DELETED engine copy | zero importers |
| planet_membrane | CONTENT-EQUAL (EOL-only) | Chimera | DELETED engine copy | zero importers |
| progeny | BYTE-EQUAL | Chimera | DELETED engine copy | zero importers |
| render_world | BYTE-EQUAL | Chimera | DELETED engine copy | zero importers |
| research_gate | CONTENT-EQUAL (EOL-only) | Chimera | DELETED engine copy | zero importers (the LIVE gate is `Chimera/core/research_gate.py`, cited by THE_FORMULA) |
| saturation | CONTENT-EQUAL (EOL-only) | Chimera | DELETED engine copy | only importer is `engine_state.py` itself, which binds Chimera FIRST by construction |
| scene_model | BYTE-EQUAL | Chimera | DELETED engine copy | zero importers |
| sections | BYTE-EQUAL | Chimera | DELETED engine copy | zero importers |
| splat_types | BYTE-EQUAL | Chimera | DELETED engine copy | zero importers |
| telemetry_probe | BYTE-EQUAL | Chimera | DELETED engine copy | `ParticleEngine/bridge/__init__.py:107` imports it inside try/except with explicit `"none"` fallback; no behavioral delta either way |
| training_gate | BYTE-EQUAL | Chimera | DELETED engine copy | live gate invoked as `python tools/training_gate.py` / `Chimera/core` binding |
| visionkeeper | BYTE-EQUAL | Chimera | DELETED engine copy | zero external importers |
| trainables/arrangement | BYTE-EQUAL | Chimera | DELETED engine copy | zero importers |
| __init__ (core/) | BYTE-EQUAL (empty file both sides) | n/a | KEPT BOTH | package machinery, not a twin module; deleting would flip `ChimeraEngine/core` to a PEP-420 namespace portion and silently change resolution semantics for every non-wired process |
| __init__ (core/trainables/) | BYTE-EQUAL (12 lines) | n/a | KEPT BOTH | same reasoning |
| **matter** | **DIVERGED** | Chimera | **PRESERVED** | Chimera-only def `assemble_3d_swaps` (+101 lines, Kawasaki-swap dynamics); shared `metrics_3d` differs in SIGNATURE (Chimera adds `types=None` param + tendon-mode branch). Engine copy is STALE. Wired processes get the newer Chimera copy |
| **photo_studio** | **DIVERGED** | Chimera | **PRESERVED** | Engine-only def `DEST = "/Game/Grown/"`; engine imports live `core.splat_mesh`, Chimera copy imports `core.splat_to_ue5` — a module DELETED in b7528218, so the Chimera copy's `main()` would ImportError if its GLB path ran. Here the ENGINE copy is the newer one; wired processes are pinned to the stale one. Needs adjudication, not deletion |
| **splat_emit** | SAME-SKELETON, comment-diverged | Chimera | PRESERVED | identical defs+spans; exactly 2 comment/docstring lines differ (engine says `core.splat_mesh.quad_cloud` — correct post-b7528218; Chimera copy references deleted `core.splat_to_ue5`). Not byte-equal → evidence-gated rule says hands off; flag for adoption of engine wording |
| **splat_level** | **DIVERGED in `main()`** | Chimera | **PRESERVED** | GLB-export branch: engine copy uses fixed `core.splat_mesh.write_splat_glb(world, …)` signature (b7528218 fix); Chimera copy still calls dead-by-signature `core.splat_to_ue5` code against a deleted module. Engine copy newer; wired processes pinned to stale copy |
| **membranes** | BYTE-EQUAL but ENGINE-BOUND | Chimera | **PRESERVED — live exclusive engine binding** | `physics.py:35-39` (self-documented: "This directory must come FIRST or a stale Chimera/core would shadow it"), `physics_articulated.py:32-42`, `fields_witness.py:35-44`, `gravity_witness.py:25,173`, `sdf_body.py:15,244` all bind `ChimeraEngine/core/membranes.py`. Deleting it would ModuleNotFoundError every live witness despite byte-equality |
| **terrarium** | BYTE-EQUAL but ENGINE-BOUND | Chimera | **PRESERVED — live exclusive engine binding** | `demo_sdf_show.py:11`, `master_loop_sdf.py:126`, `sdf_body.py:343` rely on script-dir auto-prepend (`python ChimeraEngine/<file>.py`) which freezes `core.__path__` to the ENGINE tree |

## Non-wired binding inventory (who executes the ENGINE tree today)

- `ChimeraEngine/core/membranes.py` ← physics.py, physics_articulated.py (+its witness),
  fields_witness.py, gravity_witness.py, sdf_body.py
- `ChimeraEngine/core/terrarium.py` ← demo_sdf_show.py, master_loop_sdf.py, sdf_body.py
- Everything else twin-named resolves to `Chimera/core` (engine_state freeze, or explicit
  `_HERE.parent / "Chimera"` inserts in appearance.py / human_messenger.py /
  sound_messenger.py, or Chimera-side script dirs).

## Phase-1 verdict

25 engine copies deleted (18 sha256-equal + 7 EOL-only content-equal). 6 pairs preserved
pending adjudication (4 genuinely diverged/stale-in-Chimera: `matter`, `photo_studio`,
`splat_level`, `splat_emit`; 2 byte-equal-but-engine-bound: `membranes`, `terrarium`). Both
`__init__.py` twins kept as package machinery.

Guard added at `ChimeraEngine/engine_state.py:21-24`: asserts the freshly-inserted Chimera
path actually wins the `core` binding, failing loudly ("core package shadowed to …") if any
prior import froze `core` to the engine tree. Negative test: pre-binding
`ChimeraEngine/core.membranes` then importing `engine_state` fires the assert as designed.

## Collateral discovery: the hook itself was shadow-bound

`.githooks/pre-commit`'s completeness gate ran `( cd ChimeraEngine && python -m core.saturation
--staged )` — i.e. the project's own S2b anti-rot gate was silently executing the STALE
ENGINE twin via cwd binding, exactly the defect this phase convicts. Deleting the twin made
the hook fail with `No module named core.saturation`, blocking every commit. Fix (same
commit): re-pointed to `( cd Chimera && python -m core.saturation --staged )` — the wired,
canonical copy, content-identical (EOL-equal) to what the hook had been measuring all along.
Verified: gate PASSes from the Chimera tree (`complete 1.00/dry 4; declared refused at
0.50/dry 0`).

---

# A3 PHASE 2 — the six survivors adjudicated (2026-08-26)

**Method correction first (it changes the evidence base).** `Chimera/.ignore` contains the
line `/core` — so every ripgrep-based tree scan silently skips **all of `Chimera/core/`**
(git still tracks every file there; explicit-path searches still work). Phase 1's rg importer
scan could not see ANY Chimera/core-internal importer. Phase 2 re-derived every importer
verdict with `git grep -E "(from|import) core\.X" -- "*.py"` over TRACKED files
(ignore-immune). The corrected scan is what all verdicts below rest on.

## 1+4. splat trio (`photo_studio`, `splat_level`, `splat_emit`) — engine copies DELETED; one surgical fix ported into `Chimera/core/splat_level.py`

**Phase 1's DANGER premise was FALSE for the wired tree.** b7528218 deleted only the ENGINE
copy of `core.splat_to_ue5`; `Chimera/core/splat_to_ue5.py` survives untouched (restored in
6412e7f8, last touched before b7528218) and carries everything its callers need:
`DEST`, `TARGET_CM`, `quad_cloud(splats, scale, tangent_scale=…)`, `write_splat_glb(splats,
scale, path, soft_edge=…, **kw)`, `_inject_material`. Every Chimera-side caller checks out
against it: photo_studio.main (`DEST/TARGET_CM/quad_cloud`), rebuild_world:138/157 and
test_pipeline:99 (`write_splat_glb(world, scale=, path=)` — correct shape), materialize:259
(`_inject_material`). Wired processes were NOT importing a deleted module.

**The one genuinely dead spot on the wired side**: `Chimera/core/splat_level.py`'s
`--save-glb` branch still had the tb-0183 dead-by-signature call
(`verts, colors = quad_cloud(...)` — quad_cloud returns a Scene, not a tuple — then
`write_splat_glb(str(path), verts, colors)`), soft-swallowed by try/except. FIXED here by
porting b7528218's exact call shape — `write_splat_glb(world, 1.0, str(glb_path),
tangent_scale=1.0, soft_edge=False)` — which is valid against THIS tree because
`write_splat_glb(**kw)` forwards `tangent_scale` into `quad_cloud`.

**Wholesale port of the engine copies was REJECTED, and phase 1's "port the fix" framing
was a trap**: the engine copies import `core.splat_mesh`, which does NOT exist in
Chimera/core (b7528218 created it engine-side only). Copying them over the Chimera copies
would have broken photo_studio.main and splat_level's import at run time. Doing it
"properly" means re-homing the geometry API in the canonical tree (keep-or-delete
`splat_to_ue5` vs adopt `splat_mesh`) — precisely the operator Q1 that b7528218's commit
message deferred. Not an unambiguous fix; not done.

**Deletion evidence for the three ENGINE copies** (per the task's own criterion — no live
binding can reach them):

- Corrected importer scan: zero importers of `core.photo_studio` / `core.splat_level` /
  `core.splat_emit` anywhere outside the trio itself and dead `archive/old_stacks/
  splat_gpu.py`.
- All seven known engine-binding scripts (`physics.py`, `physics_articulated.py`,
  `fields_witness.py`, `gravity_witness.py`, `sdf_body.py`, `demo_sdf_show.py`,
  `master_loop_sdf.py`) reference none of the three names (rg on those files).
- No dynamic-import path reaches them: repo-wide `importlib`/`__import__`/`runpy` uses are
  unrelated (`dream_loop`, `model_auditor`, `train_loop`, `engine_state`'s reload,
  `splat_appearance`'s file-location loads); the only `python -m core.<trio>` strings are
  docstrings inside the copies themselves; the pre-commit hook runs `cd Chimera && python
  -m core.saturation --staged`.
- Untracked-but-live files checked too: `tools/mesh_view.py`, `tools/gsplat`,
  `Chimera/Python/` — clean.
- Chain health after deletion: engine `splat_emit`'s only importer was engine
  `photo_studio` (deleted in the same action); `matter_items` now exists ONLY in
  `Chimera/core`, imports its sibling `splat_emit` there, so any process that resolves
  `matter_items` at all binds the Chimera pair. `cd Chimera && python -c "import
  core.matter_items, core.splat_emit"` verified below.
- `ChimeraEngine/core/splat_mesh.py` KEPT: not a twin (never existed in Chimera/core);
  its only code importers were the trio just deleted, but docs cite it and it is
  b7528218's deliberate artifact. Now zero code importers — noted for the next sweep.
- `splat_emit`'s divergence WAS comment-only (2 lines), and each side's wording was true
  FOR ITS OWN TREE ("core.splat_mesh" engine-side, "core.splat_to_ue5" Chimera-side — the
  module is alive there). With the engine copy deleted the question dissolves.

## 2. `matter` — divergence documented, NOT merged, NO code changes

AST comparison of top-level defs:

| def | verdict |
|---|---|
| `_row`, `main`, `render_3d`, `_prove_cross2d`, `_prove_limb3d` | byte-IDENTICAL text both sides (spans shifted +98/+100 by the insertion below) |
| `assemble_3d_swaps` | CHIMERA-ONLY (matter.py:455, +~98 lines incl. docstring). **Zero callers in tracked files on either side** — not invoked by `main` (byte-identical both sides proves it), no dynamic-import construction of the name |
| `metrics_3d` | signature differs: engine `(grid, shape)` :455 vs chimera `(grid, shape, types=None)` :542. Chimera adds a tendon-mode branch: `types=None` → historical `(BONE,MUSCLE,SKIN)` radii + tendon block; explicit `types` → radii for exactly those ids, NO tendon block, early return. Backward-compatible: every 2-arg call behaves identically under both signatures |

Callers of the differing defs, with binding trees (corrected scan):

- `metrics_3d(..., types=…)` — REQUIRED by `Chimera/core/matter_derive.py:593`
  (`types=mats`) and `Chimera/core/matter_gpu.py:582-585` (`types=types`). Both modules
  exist ONLY in Chimera/core (no engine twin — never was one), so they bind the Chimera
  copy in any process that resolves them at all. The engine copy could not serve them.
- `metrics_3d(grid, shape)` 2-arg — `Chimera/core/matter.py` internal (:692),
  `matter_derive.py:266/299/656`, and `tools/phase8_repeat.py:79` (which inserts
  `ROOT/"Chimera"` at sys.path[0], line 41 → binds the CHIMERA copy explicitly).
  Compatible with both signatures anyway.
- `assemble_3d_swaps` — no callers either side.

Verdict: engine copy is STALE but INERT — nothing outside Chimera/core + tools binds
`core.matter` from the engine tree (zero importers per corrected scan). Deletion candidate
for a future evidence-gated pass, exactly like phase 1's byte-equal set; deliberately NOT
executed here (pair instruction: document, don't merge).

## 3. `membranes`, `terrarium` — cross-referenced, both copies kept

Re-verified BYTE-EQUAL (sha256). Added one identical path-agnostic comment line at the top
of each of the four files —

`# TWIN: kept byte-equal with the same-named module in the sibling core/ tree; edit both or consolidate deliberately -- see docs/THE_TWIN_TABLE.md.`

— chosen path-agnostic so each pair REMAINS byte-equal after the edit (a comment naming
the other path would have broken the very invariant it documents). Post-edit sha256:
still equal within each pair.

## Phase-2 verification battery

Run after all changes (outputs recorded in the commit message): `python tools/orient.py`;
`cd ChimeraEngine && python -c "import engine_state"` (must bind Chimera/core);
`python tools/port_tests.py` tail must stay 18/21 with the accepted drift set;
`curl http://127.0.0.1:8091/health` must stay engine_up; plus
`cd Chimera && python -c "import core.matter_items, core.splat_emit"`,
`cd Chimera && python -m py_compile core/splat_level.py`, and a fresh negative check that
nothing imports the three deleted engine names.
