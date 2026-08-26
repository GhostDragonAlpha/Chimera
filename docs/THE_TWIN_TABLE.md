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
