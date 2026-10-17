# S0 — Mechanism and Scale Contract (mechanism factory)

Gate: GAME_PLAN_ACTION_RPG.md §13.1, row **S0 — mechanism and scale contract**
("Inventory of existing owners; select one law, boundary variables, units,
dimensionless coordinates and test domain"; stop condition "No duplicate
physics; sources and assumptions pinned; scale mapping derived; missing
variables reported").

Written 2026-10-16 by Maya (mechanism_factory increment). Repo pin at audit
time: `bd1af446` (working tree carries the known pre-existing dirt only).
CPU only; no engine boot; no GPU.

**Verdict (short):** the S0 work product now exists in this document. The
piece-record layer already carried most of the contract (law pin, units,
measured domain claims); what was genuinely missing — the DERIVED scale
mapping and dimensionless coordinates — is derived here from the pinned law
and verified on CPU. S0 is **closed-except**: the missing-variable list in
§7 must be carried into S1 and the record/packet owners; it is not a silent
closure.

---

## 1. Owner inventory (no duplicate physics)

One law, one solver, one compile path, one record layer, one fixture family,
one units table. Each physics-relevant concern has exactly one owner:

| Concern | Owner (path) | Pin (sha256, first 16) | What it owns, and nothing else |
|---|---|---|---|
| The law (energy + exact gradient + named refusals) | `tools/membrane_scale_lab/surface_energy_reference.py` | `ee9effcfbddad8d0` | `U = Σ γ_t A_t(current geometry)`, conservative corner/vertex forces, degeneracy and non-finite refusals. Explicitly distinct from `tools/ca_triangle.py` (signed area vs FROZEN import normal — a different projected-area law; the distinction is documented in the law's header and proven by negative controls in `surface_energy_checks.py`). |
| Law of record (prose source) | `docs/THE_SURFACE_ENERGY_TRANSLATION.md` (ASTRA, 2026-09-06) | `d20a7f88341f7d7a` | The preregistration the law implements; numerical allowances (FD h = e^(1/3), derivative/invariance limits). |
| The quasistatic equilibrium solver | `tools/mechanism_factory/patch_equilibrium.py::solve_equilibrium` | `a0f4b9f9b289ef1e` | Dead external loads at named vertices, five named terminal states, monotone backtracking projected descent, preconditioner P = 1/γ_max. Adds no constitutive law. |
| Fixtures (the geometry family) | `tools/membrane_scale_lab/fixture_generator.py::high_degree_fan` | `1ebd13b9a659fd85` | Apex-cone fans (n_rim triangles, apex = single free vertex), fixture validator. |
| Pieces A/B + the apex-weld seam law | `tools/mechanism_factory/composed_patch.py` | `12d4c08b9fcc1b7b` | The qualified piece pair, inversion/reflection placement, seam ownership, `_check_scale` (packet size axis). |
| Second assembly (k=2 fan-out star) | `tools/mechanism_factory/composed_chain.py` | `c3c0ae0a40b3ba04` | Reuses A and B byte-identically + piece C; topology law (star is the ONLY legal connected assembly under this law). |
| Piece records (law pin, units, measured-domain claims) | `tools/mechanism_factory/piece_record.py` + retained record `docs/evidence/mechanism_factory/pieces/assembly.star-k2.json` | `7f2d079eef3388c7` | `law_revision` = sha256 of the law file (verified equal to current bytes below); domain claims refused unless covered by in-gate measured cases in cited receipts; append-only evidence with archive. |
| Compile path / domain gate | `tools/mechanism_factory/native_binding.py` | `b2cfe406088beda0` | Scale and load enter ONLY via `compile_transaction(..., scale, load_N)`; refuses any (scale, load) outside the record's measured domain by name (`binding_scale_out_of_domain`, `binding_load_out_of_domain`); scale enters as a rigid dilation `V → s·V` (its own `_compile_piece` comment: "the qualified rigid physical-size law"). |
| Units, admitted domain, acceptance thresholds | `tools/mechanism_factory/example_packet.json` | `75e24523dc1cb002` | `chimera-mechanism-factory-work-packet-v1`: units, io_schema, admitted_domain, frozen thresholds (never widened by any consumer). |
| Material provenance | `tools/membrane_scale_lab/material_contract.py` | `6af75efe12da4ba8` | Registered material properties with source locators and named refusals; invents no modulus. |
| S1 grid study (scale vs resolution separation) | `tools/mechanism_factory/scale_resolution.py` + retained study `docs/evidence/mechanism_factory/scale_resolution_study_20261016T142810.182Z.json` (study_hash `eb78690ec8289c9c…`) | `636f460397d5ebd7` | The 5-scale × 4-resolution grid; matched/unmatched regime definition; star-drift block. |
| Load-domain study | `docs/evidence/mechanism_factory/load_domain_study_20261017.json` | (schema `chimera-mechanism-factory-load-domain-study-v1`, utc 2026-10-17T15:38:58Z) | The star's load → apex-z equilibrium table at scale 1.0; basis of the valid_loads_N amendment. |

Adjacent law families (`tools/elastic_foundation/`, `tools/finite_area_attachment/`,
`tools/ca_triangle.py`) are separate mechanisms with their own owners; none
re-implements the constant-gamma current-area law, and the one historical
near-collision (signed-area/frozen-normal) is fenced by the law module's own
header distinction and negative controls. **No duplicate physics found.**

Not owners (recorded honestly): the engine-side physical_to_render binding is
`unset` in every retained record; the overdamped descent path
(`overdamped_descent.py`, pin `a940ac9da88a8852`) is lab machinery, not part
of this mechanism's qualified chain.

## 2. The one selected law, with sources and assumptions pinned

**Law:** constant-tension quasistatic current-area surface energy —

    U(x) = Σ_t γ_t A_t(x) − Σ_i f_i · x_i      (energy [J])

with per-face γ constant (uniform γ = 1.0 J/wu² in every qualified case),
conservative vertex forces from the exact geometric derivative of the
UNSIGNED current area with the normal recomputed from current geometry:

    grad_a A = cross(b − c, n)/2 (cyclic),  n from CURRENT positions,
    face-corner force f = −γ · grad A,  vertex forces = incident corner sums.

Equilibrium = stationary point of U under full-rim pinning and dead loads at
the free apex. This is exactly the law §13.1 instructs to characterize ("if
the available law is constant-tension quasistatic relaxation, characterize
exactly that law; do not label it general elasticity, tissue or fracture").

**Pins (current bytes, sha256):**

- Law: `surface_energy_reference.py` = `ee9effcfbddad8d02e03f71d414b27da177f0656de535eaab0d76ae39796f0b7`
  — verified equal to the record's `physical_definition.law_revision` and the
  record's `function_card.freshness.source_pins` entry (recomputed 2026-10-16
  during this audit). The record cannot drift from the law silently:
  `piece_record.validate()` refuses a stale `law_revision` by name.
- Law-of-record prose: `docs/THE_SURFACE_ENERGY_TRANSLATION.md` =
  `d20a7f88341f7d7a…`
- Solver: `patch_equilibrium.py` = `a0f4b9f9b289ef1e…`; compile path:
  `native_binding.py` = `b2cfe406088beda0…`; packet: `example_packet.json` =
  `75e24523dc1cb002…` (full hashes reproducible from the pins in the record's
  freshness card and `HASHED_SOURCES` lists in `composed_patch.py` /
  `composed_chain.py`).
- CPU verification artifact: math-check evidence
  `D:/Chimera-Maintenance/Runtime/local-ai/math-tools/results/20261017-164746-44c94b59/result.json`
  (script `D:/Chimera-Maintenance/Runtime/local-ai/math-tools/checks_tmp/s0_scale_similarity_check.py`,
  sha256 `c0810171c697bb39…`, PASS 7/7, 2026-10-17).

**Assumptions** (each pinned where it lives): positions in meters with
`1 wu = 1 m` never redefined; γ in J/wu²; nondegenerate triangles (degeneracy
floor 64·e·max_edge², named refusals); quasistatic only (no inertia, no
dynamics terminal state); dead loads only (load potential linear in x);
loads on pinned vertices refused; vertical-only load component at the free
apex (tangential components excite the packet's excluded soft modes).

## 3. Boundary variables and units

From the packet's `io_schema` and the law's own validation (nothing else
enters the physics):

| Variable | Type / shape | Unit | Domain constraints (owner of the refusal) |
|---|---|---|---|
| `positions` x | (nV,3) float64 | wu (= m) | finite; nondegenerate triangles (law) |
| `faces` | (nF,3) int64, CCW | — | indices in range, no repeated vertex (law) |
| `gamma` | scalar or (nF,) | J/wu² (= J/m²) | nonnegative, finite; constant (uniform) in this mechanism's measured domain |
| `fixed_vertices` | list[int] | — | full rim only; a free rim has NO equilibrium (film contracts its free edge; packet exclusion, C3/C6 witnesses) |
| `loads` | list[(vertex,(fx,fy,fz))] | N | refused on pinned vertices; vertical-only on the free apex; dead loads (constant vectors) |
| `scale` s | float | dimensionless multiplier on wu | record's measured `valid_scales` gate at compile (native_binding), packet axis [0.5, 2.0] |
| **Outputs** | `status` (stationary/stagnated/step_limit/no_descent_step/invalid_surface); `energy` [J]; `free_residual` [N] (displacement-scale max |P·F_total| over free DOFs, NOT a Newton quantity); `reaction_forces` (nPins,3) [N]; apex position [wu] | | acceptance thresholds frozen in the packet: max_free_residual_N = 1e-6, force/moment balance 1e-6 |

Units table (packet §`units`, record §`physical_definition.units`, identical):
length `m` (1 wu = 1 m), force `N`, energy `J`; γ in J/wu² makes energies J
and reactions J/wu = N exact SI without rescaling.

## 4. Derived scale mapping and dimensionless coordinates (core content)

**What actually happens to scale in the code (owner: `native_binding.py`
`_compile_piece` / `composed_patch.build_assembly` / `composed_chain.build_star`):**
`scale` is a RIGID DILATION of the rest positions, `V → s·V`; faces, pins,
topology and γ are unchanged; the dead load is passed in NEWTONS unchanged.
So the mapping must be derived from how the law itself responds to a
dilation, not assumed.

**Derivation from the pinned law.** Under x → s·x with γ fixed:
A_t(s·x) = s²·A_t(x), so U_surface → s²·U_surface, and the exact gradient
gives vertex surface forces f(s·x) = s·f(x). The equilibrium condition is

    F_surface(x) + f_load = 0.

Substituting x = s·x₀: F_surface(s·x₀) = s·F_surface(x₀), so the dilated
problem is form-invariant iff f_load → s·f_load. Therefore:

- **Invariant under dilation:** γ, topology (faces, pins, seam), the mesh
  shape (all lengths in wu at unit scale), and the dimensionless response.
- **Scale as s:** lengths (s), areas (s²), energy (s²), internal/surface
  forces (s), compliance per wu (unchanged: P = 1/γ_max in wu/N).
- **The one load group:** Π = F / (γ·L) with L = s·r₀ the characteristic
  size (r₀ = recipe rim radius in wu; for the frozen fan recipe r₀ = 1.0 wu,
  so L = s and Π = F/(γ·s) numerically at γ = 1).
- **The dimensionless response coordinate:** η = z_apex / (s·r₀) = z_apex/L.
- **Exact similarity holds if and only if the load scales as s** (Π
  constant). The record's fixed-N family (load held in newtons across
  scales) is therefore a ONE-PARAMETER SWEEP OF Π ∝ 1/s — different
  dimensionless problems, and it must NOT be normalized as one. This is
  precisely the negative-control requirement §13.1 preregisters for S1.
- Why the equilibrium still depends on scale at fixed N: the internal force
  scale is γ·L ∝ s while the load is fixed, so the dimensionless load rises
  as 1/s; apex response in wu does not track s. This is measured, not
  assumed (below).

**CPU verification (math-check PASS 7/7, evidence path in §2):**

1. Algebraic identities, exact to machine precision (max_abs_error 0.0):
   `U(s·V, γ) = s²·U(V, γ)` and `f_vertex(s·V, γ) = s·f_vertex(V, γ)`.
2. Solver-level similarity on the F ∝ s ray with the qualified frozen recipe
   (n_rim 200, r = 1.0 wu, h = 0.3 wu, γ = 1, seed 1, full rim pinned, apex
   dead load): case A (s = 1.0, F = 0.8 N) vs case B (s = 0.5, F = 0.4 N) —
   apex_z(B) = 0.5·apex_z(A), U(B) = 0.25·U(A), max pin reaction(B) =
   0.5·(A), all within the preregistered tolerances (atol 2e-5 wu derived
   from the packet's 1e-6 N gate through the law's exact compliance
   P = 1/γ_max = 1 wu/N; measured deviations 0.0 at double precision).
3. Dimensionless collapse: η = −0.2633079630900263 at Π = 0.8 for BOTH
   cases — and digit-for-digit equal to the retained S1 study's (s = 1.0,
   n_rim = 200) cell (`scale_resolution_study_20261016T142810.182Z.json`),
   an independent cross-check of the mapping against already-retained
   evidence.
4. Negative control (must NOT be similar): case C (s = 0.5, F = 0.8 N,
   Π = 1.6) deviates from the similarity prediction by 0.164 wu — 4 orders
   of magnitude over tolerance. Fixed-N cross-scale solves are different
   dimensionless problems, as derived.

**How scale changes the equilibrium at fixed load (from the retained study,
fixed apex load 0.8 N, matched resolution n_rim = 300):**

| s [wu] | Π = F/(γ·s) | apex_z [wu] | η = −apex_z/s |
|---|---|---|---|
| 0.5 | 1.600 | −0.295890 | 0.59178 |
| 0.75 | 1.067 | −0.270721 | 0.36096 |
| 1.0 | 0.800 | −0.263320 | 0.26332 |
| 1.5 | 0.533 | −0.258389 | 0.17226 |
| 2.0 | 0.400 | −0.256728 | 0.12836 |

(The load-domain study `load_domain_study_20261017.json` is the same sweep
for the STAR at s = 1.0: apex_z runs 0.3870 → −0.0595 wu over F = 0 → 3.0 N,
i.e. the same η(Π) curve shape for the star's own geometry.)

**Consequence for the record's `valid_scales`:** the record lists discrete
measured scales [0.75, 1.0, 1.5, 2.0]. Under this contract those are
IN-DOMAIN points of the (s, Π) plane along the ray F = 0.8 N (Π = 0.8/s),
NOT a similarity claim: scale transfer between them is a measured
interpolation in a one-parameter family, not an invariance. Any S1
"same normalized response" claim must move along F ∝ s rays (Π constant);
any fixed-F cross-scale comparison is a Π sweep and must be labeled as such.
The star's drift at 1.5x/2.0x recorded under the pre-adoption v1 machinery
(retained study verdict "scale_physics") was superseded by the 11.19
solver-v2 adoption: the current qualification receipt
(`composed_chain_qualification_receipt_20261016T180652.327348Z.json`) measures
all five scales {0.5, 0.75, 1.0, 1.5, 2.0} within the packet's 1e-6 N law
(residuals 1.7e-7 … 4.2e-14 N), which is the measurement basis of the
record's domain amendment history.

## 5. Test domain (what is in-domain, from measurement only)

- **Scales:** record `valid_scales` = [0.75, 1.0, 1.5, 2.0] — covered by
  in-gate measured cases in the cited receipts (composed-chain receipts +
  qualification receipt above; single patch additionally in-gate at 0.5 in
  the retained S1 study). Packet admitted axis: [0.5, 2.0] m. The compile
  path refuses anything else by name (`binding_scale_out_of_domain`).
- **Loads:** record `valid_loads_N` = [0.0, 0.4, 0.8, 1.2, 1.6, 2.0, 2.5,
  3.0] — covered by the load-domain study rows (star, s = 1.0, all rows
  in-gate under the 1e-6 N law). Measured AT SCALE 1.0 ONLY (see §7).
- **Resolution:** the piece is qualified at n_rim = 200; the S1 ladder
  (100→300) does not reach the 1e-6 wu displacement tolerance (finest
  successive change ≈ 1.16e-5 wu, an honest retained limit); matched regime
  = n_rim 300, unmatched = 200, with the physics/remeshing decomposition
  ratio ≈ 2.9e3 recorded in the study.
- **Geometry family:** `fixture_generator.high_degree_fan` apex-cone fans,
  full-rim 3D pinning, single free apex, vertical loads; excluded: free seam
  rings and rim welds (witness (g)), partial-rim pins, tangential load
  components, non-uniform γ, degenerate/negative-orientation triangles.
- **Negative control (S1 preregistration input from this contract):** the
  fixed-load cross-scale case (§4 item 4) violates the similarity
  assumption and must NOT be accepted as the same normalized response.

## 6. Relationship to the piece-record layer

The record layer is a PIECE of the S0 contract and the gate's "no duplicate
physics" is largely satisfied by it: `law_revision` = the pinned law file's
hash (re-validated on every `validate()`/compile/restore), units and
excluded phenomena recorded, and domain claims refused unless covered by
in-gate measured cases in cited receipts (`piece_domain_unmeasured`,
`piece_load_unmeasured`). What the record deliberately does NOT carry — and
what this document adds — is the derivation: WHY [0.75, 1.0, 1.5, 2.0] are
the right points to measure (they are a Π-sweep at fixed N), which quantities
are invariant vs s^k, and the dimensionless coordinates that make a
scale-transfer claim in S1 meaningful. The record's own prose acknowledges
this split: it cites receipts, this contract derives the mapping the
receipts are samples of.

## 7. Missing variables (reported honestly — S0 is NOT silently closed)

1. **The (scale, load) cross-product is unmeasured.** valid_scales was
   measured at 0.8 N only; valid_loads_N was measured at s = 1.0 only
   (load-domain study title: "at scale 1.0"). The compile path's
   `_in_domain` treats the domain as the CARTESIAN PRODUCT of the two lists
   (any listed scale × any listed load), e.g. (2.0, 3.0 N) would compile
   although no cited receipt measures that cell. S1 must either fill the
   grid or narrow the compile gate to the measured cross.
2. **Packet/record load-axis conflict.** The packet's `admitted_domain.loads`
   says `max_force_N: 2.0` (and `composed_patch.py` still comments "≤2.0 N"),
   while the record's amended `valid_loads_N` includes 2.5 and 3.0 N (both
   measured in-gate). The packet was never amended; nothing reconciles the
   two owners. A named decision is owed: amend the packet, or revert the
   record's >2.0 N claims.
3. **No self-intersection / ground-crossing refusal.** At 3.0 N the star's
   seam apex sits at z = −0.0595 wu — below the rim plane; the film passes
   through its own ground ring and (for the star) through the hanger films'
   region. The law validates triangle nondegeneracy but has NO
   self-contact/self-intersection variable in its boundary set, and the
   record's excluded_phenomena do not name it. The in-domain claim at high
   load rests on the residual gate alone.
4. **Stale function-card prose in the retained record.**
   `assembly.star-k2`'s `function_card.operating_domain` still reads "rigid
   scales 0.75x and 1.0x ONLY (1.5x/2.0x measured over the unchanged gate)"
   and its `failures` list still names "scale drift at 1.5x/2.0x" — both
   superseded by the physical_definition amendments (1.5/2.0 in-domain under
   solver v2). The record layer's amendment laws cover physical_definition
   and representations but there is no amendment path for function_card
   prose. Record owner (not this increment — record JSONs are out of scope
   here) should either add a function-card amendment law or record the
   staleness on the freshness card.
5. **η(Π) is not yet a reusable artifact.** This contract pins the
   dimensionless coordinates and verifies two points of the patch's curve;
   tabulating η(Π) per mechanism (patch and star) as an explicit
   validity-queried table is S3's deliverable. The star's curve is NOT the
   patch's curve (different geometry, same law and coordinates).
6. **γ is a boundary variable with a degenerate measured domain.** The law
   supports arbitrary uniform (and per-face) γ, but every qualified case
   runs γ = 1.0. Under the derived mapping, varying γ at fixed F is again a
   Π sweep (Π = F/(γ·L)), so the missing measurement is a γ-axis ray, not a
   new group. Reported so S1/S3 do not treat γ as independently qualified.
7. **Dynamics.** The law is quasistatic by construction; the record's
   excluded_phenomena do not explicitly name transients/inertia (the
   overdamped path in the lab is separate machinery). Cheap to add at the
   next record touch; listed for completeness.
