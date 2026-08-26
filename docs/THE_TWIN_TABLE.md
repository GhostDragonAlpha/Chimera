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

---

# A3 PHASE 3 — matter merge proposal (2026-08-26)

READY-TO-APPLY plan for the last genuinely diverged pair. Re-verified from scratch — phase 2's
"engine copy STALE but INERT" verdict survives contact with a deeper scan, but the scan also
found rot neither phase had named. Doc-only: no code changed in this phase.

## Method

Both files parsed with `ast`; every top-level node (def/class/import/assign/if-guard) hashed
per-span twice — raw text sha256 and CRLF-normalized sha256 — then diffed. Importer census re-run
with `git grep` over TRACKED files only (the `.ignore` trap from phase 2 does not apply to
git grep), extended beyond phase 2's `(from|import) core.X` pattern to **bare-name**
`from matter import …` / `import matter` bindings, dynamic-construction patterns
(`getattr`, `import_module`, `__import__`), string references, untracked-but-live dirs
(`Chimera/Python/`, `tools/mesh_view.py`, `Saved/mesh_view/`), and `attic/**`
(tracked: `attic/retired_island/…`; zero untracked files under `attic/`).

## 1. Per-symbol equality matrix

File level: chimera sha256 `38a0be7bc111` (748 lines) vs engine sha256 `4be5227b9d7a`
(650 lines). Every span below BYTE-EQUAL means raw-sha256 equal (EOLs included).

| symbol | chimera | engine | delta |
|---|---|---|---|
| imports (`__future__`, argparse, json, math, pathlib, numpy) | :40–47 | :40–47 | BYTE-EQUAL |
| tissue constants + `NAMES`, `TISSUES` | :53–55 | :53–55 | BYTE-EQUAL |
| `_build_J_from_library` | :66–115 | :66–115 | BYTE-EQUAL |
| `J_PROVEN_DIFFERENTIAL/_UNIFORM(+[M,M])/J_DIFFERENTIAL/J_UNIFORM` assigns | :119–131 | :119–131 | BYTE-EQUAL |
| `TENDON`, `NAMES[TENDON]` | :148–149 | :148–149 | BYTE-EQUAL |
| `_build_J_3d_from_library` | :151–192 | :151–192 | BYTE-EQUAL |
| `J_PROVEN_DIFFERENTIAL_3D/_UNIFORM_3D(+[M,M])/J_DIFFERENTIAL_3D/J_UNIFORM_3D` | :195–208 | :195–208 | BYTE-EQUAL |
| `_OFFS` | :216 | :216 | BYTE-EQUAL |
| `init_blob` | :219–236 | :219–236 | BYTE-EQUAL |
| `assemble` | :239–286 | :239–286 | BYTE-EQUAL |
| `metrics` | :289–308 | :289–308 | BYTE-EQUAL |
| `is_sorted` | :311–317 | :311–317 | BYTE-EQUAL |
| `_COLORS` | :320–322 | :320–322 | BYTE-EQUAL |
| `render` | :325–350 | :325–350 | BYTE-EQUAL |
| `_nd_offsets` | :359–374 | :359–374 | BYTE-EQUAL |
| `init_limb_3d` | :377–399 | :377–399 | BYTE-EQUAL |
| `assemble_3d` | :402–452 | :402–452 | BYTE-EQUAL |
| `assemble_3d_swaps` | :455–539 | — | **CHIMERA-ONLY** |
| `metrics_3d` | :542–599 | :455–501 | **DIFFERS** (below) |
| `render_3d` | :602–633 | :504–535 | BYTE-EQUAL |
| `_row` | :636–639 | :538–541 | BYTE-EQUAL |
| `_prove_cross2d` | :642–684 | :544–586 | BYTE-EQUAL |
| `_prove_limb3d` | :687–733 | :589–635 | BYTE-EQUAL |
| `main` | :736–744 | :638–646 | BYTE-EQUAL |
| `if __name__ == "__main__"` guard | :747–748 | :649–650 | BYTE-EQUAL |

`metrics_3d` full body diff (normalized): chimera adds the `types=None` parameter; default
path sets `types=(BONE, MUSCLE, SKIN)` and `tendon_mode=True` — i.e. the engine body verbatim;
explicit `types` loops over those ids and early-returns before the tendon block. The engine
loop literal `(BONE, MUSCLE, SKIN)` and tendon block are otherwise character-identical. So:
every 2-arg call behaves identically under both signatures; every `types=` call TypeErrors on
the engine copy. **The engine file contains zero symbols absent from the chimera file — the
chimera copy is a strict superset. There is nothing to PORT, which collapses option (b) to a
null set before the binding question even starts.**

## 2. `assemble_3d_swaps` caller census — CONFIRMED ZERO (not refuted)

- `git grep -n "assemble_3d_swaps"` over ALL tracked files: the def line
  (`Chimera/core/matter.py:455`) and PROSE only — `docs/THE_LIVING_MATTER.md:1308,1358`,
  this table's own phase-1/2 rows. Nothing in `attic/retired_island/**` (tracked, therefore
  inside the grep; zero untracked files exist under `attic/`). No hit anywhere executes it.
- Broader net, `assemble_3d*` (to catch partial/dynamic construction) plus
  `getattr(…assemble…)` / `import_module(…matter…)` / `__import__(…matter…)`: every hit
  resolves to `assemble_3d` (limb.py:109, rig.py:82, rebuild_world.py:152,
  splat_gpu_emit.py:177, grown_arrangement.py:258, matter.py internal :690/691,
  `assemble_3d_gpu` in matter_gpu.py + its callers) — never `_swaps`. The only `_swaps`
  string outside the def is its own docstring cross-reference (:458).
- Untracked-but-live (`Chimera/Python/`, `tools/*.py` incl. `mesh_view.py`,
  `Saved/mesh_view/`): zero hits.
- String references `matter.assemble_3d_swaps`: prose only (THE_LIVING_MATTER.md, above).

## 3. The binding reality — including what phase 2 missed

Package-name importers of `core.matter` (complete list): bake.py:38, limb.py:34–35,
rebuild_world.py:35,145, rig.py:25–26, splat_emit.py:76, splat_gpu_emit.py:173,
test_pipeline.py:31, trainables/generated/ground_terrain.py:161,184,
trainables/grown_arrangement.py:44, matter_derive.py (internal), matter_gpu.py:570,
tools/phase8_repeat.py:53 (inserts `ROOT/"Chimera"` explicitly). **All resolve to
`Chimera/core/matter.py`** — wired freeze or explicit insert. Zero package-name importers
exist under `ChimeraEngine/` (grep exit 1), and the seven known engine-binding scripts
(physics, physics_articulated, fields_witness, gravity_witness, sdf_body, demo_sdf_show,
master_loop_sdf) contain only prose mentions of "matter" — their engine bindings are
`core.membranes`/`core.terrarium`, which import stdlib+numpy only: no transitive chain into
matter exists.

Per differing symbol:

- `metrics_3d(grid, shape, types=…)`: matter_derive.py:593 and matter_gpu.py:582–585 ONLY.
  Both modules exist solely in Chimera/core, so any process running them at all has frozen
  `core.__path__` there; the engine copy could not serve them (TypeError). The 2-arg callers
  (matter.py internal :692, matter_derive :266/:299/:656, phase8_repeat:79) are signature-
  compatible with both copies and all bind Chimera anyway.
- `assemble_3d_swaps`: no callers through ANY binding (§2).
- Old-metrics_3d-behavior dependency: NONE. No file binds the engine tree and calls
  `metrics_3d`; no engine-tree file calls it at all.

**What phase 2 missed — the ~30 bare-name `matter` importers are NOT engine-twin binders.**
walker.py, live_viewer.py, touchables.py, the hertz/optics/overlap/viscoelastic chain (+12
`test_*.py`), and ten `tools/*` scripts do `from matter import lit, blank, SOLID, …`. Their
sys.path setups point at repo root, `story/`, or `ChimeraEngine/` — **never
`ChimeraEngine/core/`** — and they were written against the STORY TREE's own `matter.py`
(path written split here: the file is gone), a THIRD file that merely shares the name:
provenance check shows that deleted file (2fb2f75f^) shares ZERO defs with the engine twin
(story = the light/appearance API: `lit`, `paint`, `youngs_modulus`, `BULK_MODULUS_PA`,
sun geometry; engine twin defines none of these — grep count 0). So the bare-name census
never reached either copy of the adhesion module, past or present. The engine copy's total
lifetime binder count: **zero**.

**Rot finding (pre-existing, NOT created by this proposal):** both twins are unimportable
TODAY. Module-level `_build_J_from_library()` opens the library JSON under each parent's
`docs/matter/` directory (file name `matter_library.json`; path split here because the file
is deliberately gone); it was deleted from Chimera in 2fb2f75f ("THE LIGHT SEED: the matter
era ends") and never existed under ChimeraEngine. Verified live: `cd Chimera && python -c
"import core.matter"` and `cd ChimeraEngine && python -c "import core.matter"` BOTH raise
FileNotFoundError. The port battery still reads 18/21 because `tools/matter_data.py` REFUSES
by design when the library is missing. Every `core.matter` importer therefore dies at import
in any process — the divergence is real but neither copy executes anywhere.

## 4. THE PROPOSAL — DECIDED: option (a), with option (b) ruled out as empty

**Adopt `Chimera/core/matter.py` as canonical everywhere; delete
`ChimeraEngine/core/matter.py`.**

Rule-0 triad:

> **STATEMENT:** the engine twin has zero binders of any kind — package-name (all fourteen
> resolve to Chimera), bare-name (built against the story-tree matter module, dead since
> 2fb2f75f), and direct-execution (no `python …/engine…/matter.py` invocation strings) — so
> deleting it changes no process's behavior.
>
> **PREDICTION:** after deletion, `python tools/orient.py` output is unchanged;
> `python tools/port_tests.py` stays 18/21 with the same three drifts
> (joint_limit −2.83%, force_velocity +0.15%, plantar_pressure +100.83%);
> `cd Chimera && python -c "import core.matter"` still fails with FileNotFoundError on the
> same missing library JSON (unchanged failure mode);
> `cd ChimeraEngine && python -c "import core.matter"` fails with ModuleNotFoundError (it
> already failed — FileNotFoundError — before);
> `git ls-files "**/core/matter.py"` returns exactly one file.
>
> **FALSIFIER:** any of those six checks deviating — ports off 18/21 or a fourth drift;
> orient raising; a Chimera-bound importer's exception class changing (only possible if some
> caller catches FileNotFoundError narrowly around the import: none exists in the census);
> or any NEW ImportError appearing in a process that previously got past that line. Any one
> fires ⇒ revert (below) and re-adjudicate.

Exact end-state content strategy:

1. `git rm ChimeraEngine/core/matter.py` — the ONLY change. `Chimera/core/matter.py` stays
   byte-for-byte `38a0be7bc111`; no edit to any survivor (option (b)'s port step has nothing
   to port: strict-superset proof in §1).
2. Do NOT touch `ChimeraEngine/core/__init__.py` (phase-1 rule: package machinery survives);
   the engine `core` package simply loses one stale member.
3. Do NOT "fix" the import rot here. Restoring/generating the missing library JSON under
   Chimera `docs/matter/` (see §3 for the exact name)
   or formally retiring the matter-era callers is an operator decision (2fb2f75f retired the
   era deliberately); unification neither worsens nor repairs it, and bundling it would make
   this change unverifiable.

Verification battery (run in order, record outputs):

```bash
python tools/orient.py                                   # unchanged tree/ledger/git read
python tools/port_tests.py                               # tail MUST stay 18/21, same 3 drifts
cd Chimera && python -c "import core.matter"             # expect FileNotFoundError (unchanged)
cd ChimeraEngine && python -c "import core.matter"       # expect ModuleNotFoundError (was FNFE)
git ls-files "*core/matter.py"                           # exactly: Chimera/core/matter.py
git grep -n "assemble_3d_swaps" -- "*.py"                # def line only
```

Rollback: single-file revert, no dependencies —

```bash
git revert <this-commit>        # restores ChimeraEngine/core/matter.py verbatim (4be5227b9d7a)
```

No other file references the deleted path (grep-proven §3), so revert is complete by itself.

## Phase-3 status

PROPOSED, not applied — this commit is documentation-only (this section). The apply commit,
when an operator green-lights it, should carry this battery's outputs in its message.
