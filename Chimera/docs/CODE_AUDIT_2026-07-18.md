# Code Audit Findings — 2026-07-18 (tb-0214 truth-sync)

**Status:** FINDINGS ONLY. No code changes applied per operator order. Documentation corrected to match reality where drift was confirmed.

---

## Core Pipeline + Gates
- **CRITICAL:** `core/council.py::_check_build` queries a node type no writer creates → auto-refutes every build check, poisons DNA graph with false refutations.
- Postflight push handling needs stabilization against stale filter states.
- Accepted gate bypass path inconsistent with judge enforcement expectations.

## Trainables + Trainer Coherence
- Stack structure verified: domain/objective/trainer separation holds.
- GPU trainer auto-selection and MJCF bone-tree mapping correct per measured results.

## Matter Subsystems, UE5 Bridge, Scene/Photo
- **HIGH:** `core/matter_gpu.py` volume constraint reads live atomics during updates → race/non-deterministic against docstring promise of pass-start counts.
- **HIGH:** `core/limb.py::grow_limb(gpu=True)` default silently diverges downstream witness artifacts between CPU and CUDA boxes.
- Generator pipeline skips materialization/flight templates: `generate_materialization_subsystem_files` defined but never called → subsystem orphaned, cannot regenerate via standard pipeline run.
- Generated C++ retains test-scaffold landmine class patterns (hardcoded inputs/motion/spawning in `Tick`/`BeginPlay`, e.g., FlightComponent `ThrustInput=1.0f`).

## Witness + Observation Slice
- Doc-vs-code drift verified mechanically and manually where critical.
- `THE_COMPOSITIONAL_WORLD_MODEL.md` corrected: editor-staged tb-0197 claim marked refuted; runtime MaterializationSubsystem recorded as standing realization.
- CLAUDE.md Key Paths, ladder principles, generator ownership, and bridge traps synced to measured reality.

---

## Actionable Backlog (for next build/fix lane)
1. Fix `council._check_build` node-type query or redirect build checks to the actual created schema.
2. Make volume constraint counts snapshot at pass-start in `matter_gpu.py`.
3. Decouple `grow_limb(gpu)` default from downstream reproducible artifacts; require explicit GPU intent in witness pipelines.
4. Wire `generate_materialization_subsystem_files` into the main generator pipeline and regenerate Flight/Materialization templates.
5. Strip test-scaffold hardcoded inputs from generated Tick/BeginPlay stubs.
