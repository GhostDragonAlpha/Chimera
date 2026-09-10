# AUDIT.md — source and physics audit (BP-ELASTIC-FOUNDATION §A)

Inspected in a **fresh isolated checkout** of `GhostDragonAlpha/Chimera` (origin of the workspace:
`https://github.com/GhostDragonAlpha/Chimera.git`). Recorded commits:

- workspace/`master` HEAD inspected: **`51cd7212fd6ef2cfda95c330abcc2ff154cc6141`**
- `astra/gait-capture` fetched and inspected: **`cf2a0ae2c7bd68f1c64db630c4db5de32785580a`**
  (merge-base with the workspace HEAD `7cafb332…`). The remote ref no longer exists upstream
  (fetch fails), but the local fetched ref was inspected; the record is the commit id.
- GLM's current GPU/runtime work and the surface-energy reference live as **untracked** files in
  the workspace (`Chimera/tools/surface_energy_reference.py`, mutation evidence under
  `review-mutations-01/`). They were READ for this audit, never modified.

The task's ownership boundary is honored: this milestone writes **only**
`tools/elastic_foundation/` and `docs/evidence/elastic_foundation/`. No production file, contract,
shader, engine file or GLM file is edited. No commit, no push.

---

## 1. What exists and what each piece is

| Piece | Location (as inspected) | What it is |
|---|---|---|
| Surface-energy law of record | `docs/THE_SURFACE_ENERGY_TRANSLATION.md` (ASTRA 2026-09-06; present in `.tmp/**` copies and the review-mutations isolated checkout) | `U = Σ γ_t A_t`, constant nonneg `γ`, exact `∇A` from current normals. It is **interfacial**; the doc's own counterexample `diag(2, ½)` is the proof that area ≠ in-plane metric |
| Surface reference implementation | `Chimera/tools/surface_energy_reference.py` (G01/GLM, untracked) | `evaluate_surface`, `triangle_metric` (the per-face rest→current `C = JᵀJ` in a declared rest tangent basis), CSR vertex→corner gather, named refusals, degeneracy floor `64ε·max_edge²`, FD budget `256ε^(2/3)`, algebra budget `512ε` |
| GPU membrane probe | `tools/membrane_gpu_probe/{probe.cpp, membrane.comp}` + fixtures (review-mutations isolated checkout) | Two-stage GPU: stage A per-face corner forces + energy + validity; stage B fixed-order CSR gather. std430 layout: positions vec4, indices uvec4, gamma float, CSR offsets/corners uint, FaceRecord (normal_area + 3 corner forces), vertex forces, total energy, validity |
| Material library | `Chimera/docs/matter/matter_library.json`; read-only wrapper `tools/matter_data.py` | Researched per-material data: density, friction, cohesion, stiffness class, and for some materials `youngs_modulus_gpa`. **No Poisson ratio, no shear modulus, no material-direction data anywhere** |
| Composition table | `tools/materials.py` | Teddy-part densities only (mass/inertia inputs). Not a constitutive table |
| CA triangle mechanics | `tools/ca_triangle.py` | Bond + area-mode CA on the particle graph. **Different law**: signed area against a FROZEN import normal (a rest-area/strain experiment), plus bond springs. Not a constitutive sheet law; deliberately not redefined by either GLM's surface module or this work |
| "Elastic FEA" stub | `WorldModel/physics/elastic_deformation_fea.py` | Scalar Hooke `ε = σ/E` toy: **no triangle, no deformation gradient, no vertex forces, no mesh**. Nothing reusable except the lesson that a constituted law was never built |
| Master list | `docs/THE_MASTER_LIST.md` | The construction ledger for the CA/cells/gait stack; relevant entries (L6 hinge ARAP skin, L7 water) confirm the existing substrate is triangle-based with derived constants, but no elastic-sheet law is listed anywhere |
| Session contract | `ChimeraEngine/AGENT_PROTOCOL.md`, `docs/THE_OPERATING_MANUAL.md`, `docs/THE_TRIANGLE_GUIDE.md` | Boundary table (agent may not edit production, contracts, engine, or others' checkouts; may use `.tmp/`); runtime law (Python = derivation bench + one-shot setup only, never per-frame); "blocked is earned"; evidence under owned dirs; appending evidence over rewriting history |

## 2. Reuse and gap verdicts

**Reusable as inputs (read-only):**
- The triangle substrate + the pullback-metric object `C = JᵀJ` and its rest-frame convention
  (`t1 = normalize(b−a)`, `n = cross/|…|`, `t2 = cross(n,t1)`) from `triangle_metric` — my `F`,
  `C` are the same objects in the same frame, so a future combined GPU run reads one metric
  (see `GPU_HANDOFF.md`).
- The CSR vertex→corner gather order (vertex asc, face asc, slot asc) — shared GPU stage B.
- The refusal categories (index/empty/shape/dtype/negative-parameter/collapsed/degenerate/
  nonfinite-result) and the degeneracy floor convention `64ε·max_edge²`.
- `E` measured per material where the library has it (rock, metal, others), for the future real
  material port.

**Unimplemented (this milestone's job):**
- A rest-shape-remembering, stretch+shear-resisting constitutive law with analytic vertex forces.
  Nothing in the tree provides it: the FEA stub has no triangle; `ca_triangle.py` is a different
  experiment; the surface metric explicitly refuses to invent a modulus and the normal law has none.
- Per-reference-area energy + plane-stress thickness reduction (absent everywhere).
- An orthotropic parameter set and a material-direction transport rule (absent, hence the named
  refusal in `DERIVATION.md` §7).

## 3. Measured data vs synthetic parameters vs unsupported capabilities

- **Measured material data**: `E` (some materials, cited), density, friction, cohesion — the
  library. No `ν` anywhere ⇒ real-material ports refuse by name (F7b/c), never degrade to invented
  numbers.
- **Synthetic test parameters**: every fixture's `(E, ν, h)` is declared synthetic (`E = 1 Pa,
  ν = 0.3, h = 1 m` default; `γ = 1` in the surface law is the analogous convention there).
- **Unsupported capabilities** (documented, not deleted): bending/buckling stiffness, bulk-solid
  response, orthotropy, rate dependence, plasticity, fracture, contact, liquid coupling — 
  `WHAT_COMES_NEXT.md`.

## 4. Unit conventions (audit result)

- Surface reference: "positions in meters (any consistent unit works); γ in energy/area".
- CA seed: the dimensionless `LightEngine/constants.py` run (`R_BOND = 0.15`, `K_BOND = 1.0`) is a
  **different** substrate; not the sheet's units.
- This law: positions in any consistent unit (nominal m), `E` in Pa, `ν` dimensionless, `h` in m,
  energy per reference area, total energy per triangle `U_t = A₀·W̄` (J), corner forces (N),
  gathered vertex forces (N). Unit consistency is a falsified class (F8).

## 5. Failure modes inherited (named, not copied)

- Non-polyconvex STVK under strong compression (Pascon 2019) — declared a domain bound (§6 of
  `DERIVATION.md`), not fixed by a hidden repair.
- Overflow: the reference earned `NONFINITE_RESULT` for finite-but-1e100 inputs; the same gate is
  implemented here (F9e).
- Gather bugs on connected meshes are invisible to single-triangle tests — the battery includes
  connected patches and the M6 gather mutation on purpose (the reference's own F8 lesson).
- A "one law, two frames" trap: the surface reference distinguishes frozen-normal from current
  normal; this law distinguishes Lagrangian (material) from Eulerian (spatial) frame usage — M5 is
  the instrument for that class.

## 6. What the audit deliberately did NOT re-derive

- The surface law's own budgets and physics (GLM/G01 owns them).
- The CA graph, legs, hinges, water — unrelated substrates listed for boundary clarity only.
- The material library's measured values (it is the contract; this work only reads it).

## 7. Amendment (2026-09-08) — sheet-level pullback frame

Section 2 above records the audit's reuse claim that my `F`/`C` share the surface reference's
PER-FACE rest tangent convention (`t1 = normalize(x1−x0)`). During falsification that per-face
frame fired F11 (interior patch-test residual non-zero and non-convergent under refinement);
the frame was re-derived to a single sheet-level, rest-derived, co-rotating basis
(`DERIVATION.md` §11, `PREREGISTRATION.md` A1). The audit statement that the metrics are "the
same objects in the same frame" now reads: the surface reference remains per-face; THIS law uses
a sheet frame, so a future combined GPU stage must agree ONE convention per stage (the handoff
records the choice). The shared items elsewhere in this audit — CSR gather order, refusal
categories, degeneracy floor, budget model — are unaffected.