# MAT2-M01 PREREGISTRATION — frozen before implementation

Frozen: 2026-09-27Z, before authoring material_state.py or any test run.
Task: MAT2-M01 / planning id M01 — "Define reusable material state and distinct
relation types" (criteria sha256 6ad0547d180d402881dbbf09e6f62581c5b0ebafa308cbddc0b6d5f69abfd859,
scope sha256 cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097,
base revision c525b82c7c3ce0128565424764293a3c85811ab3, isolated branch-1 checkout).

## Frozen statement

One versioned schema (`chimera.material_state.v1`) distinguishes, as distinct named
sub-objects: regions/shells, rest/current geometry, mass (single-owner), material
direction/history, pressure/deformation law, contact and bond. Containment and
mechanical connection are DISTINCT relation types: a bond is never implied by
containment, and every mechanical load path is an explicit bond with named endpoints.
Matter has exactly one owner; references do not re-own it; total mass is counted
once. A known object (the existing teddy prototype) displays its actual regions and
graph relations with stable IDs.

## Frozen predictions

P1 (schema): a well-formed material_state document validates and round-trips
byte-identically through the canonical encoder; every region/mass/law/bond carries a
stable ID matching `[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}`.
P2 (single ownership): for the teddy fixture, summing mass over owners equals the
document total exactly (float-exact accounting recorded); referencing a second time
with role "reference" does not change the total; a second owner claim is refused.
P3 (distinct relations): every containment edge (parent) and every bond (mechanical)
is typed; a bond's endpoints must name existing ports; containment must not create a
bond record and vice versa; the display output lists both relation kinds separately.
P4 (carried data): every region in the schema fixture corresponds to a membrane id in
the pinned `ChimeraEngine/native/teddy_membranes.json` at base revision c525b82c
(reuse, not reinvention); counts recorded.

## Frozen falsifiers (each must fail loudly with a named code)

F1 (mass double-count): two owner claims for one matter id → REFUSED
(`duplicate_matter_owner`). Owner+reference for the same id → accepted, total mass
unchanged.
F2 (containment-as-bond): a document whose regions are nested but that acquires any
mechanical bond record purely from nesting → REFUSED (`bond_requires_explicit_endpoints`);
removing an explicit bond removes the load path (bond count drops; nothing else changes).
F3 (unstable identity): mutating a region id between revisions of the same object
without a declared rename → REFUSED (`region_identity_drift`); stable ids survive
re-serialization with identical digests.

## Frozen probes

`test_material_state.py` (CPU-only, python -B, stdlib only, no engine, no network):
P1-P4 positive checks and F1-F3 injected refusals, all in one test file.
`render_material_display.py`: CPU-only structured display (JSON, not pixels) of the
teddy object's regions and graph relations with stable IDs — the task-owned "known
object displays" evidence. Honest boundary: this base revision contains no runnable
material solver; motion/camera visual evidence is NOT claimable here and is explicitly
deferred to runtime-facing cards (M03/M04, MAT-PRESSURE). The `material` motion
profile's visual clause is recorded as pending-runtime, not passed.

## Honest boundary

Offline schema/records qualification at chosen fidelity: no runtime physics, no GPU,
no training, no visual capture claim. Density is one property among many; no
activation law is invented; no anatomy constants are fabricated (teddy regions and
material catalog are reused source data, not authored physics).
