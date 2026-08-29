# SOUND MODES 01 — H10 STAGE 1: CPU MODAL REFERENCE ON THE SALLY BODY DUAL GRAPH
**Author:** kimi (main agent) | **Date:** 2026-08-29 | **Law:** `agent_logs/hy3/sound_packet_02.md` (revised) + `agent_logs/hy3/sound_packet_01.md` (S1–S5 where 02 doesn't replace) | **Script:** `.tmp/sound_modes.py` | **Data:** `.tmp/sound_modes/results.json` (+ `results_v2_breathing_variant.json`) | **CPU-only; no GPU, no engine contact**

## MEMBRANE (Rule-0, stated before the build — restated from the script header)

- **STATEMENT:** the dual-graph spring lattice assembled from the LANDED T2
  carrier law (`k = 0.75·K_BOND/A0`, `docs/THE_MASTER_LIST.md` Landed Foundations;
  K_BOND = 1.0, `LightEngine/constants.py:51`) plus packet-02's corrected plate
  bending `D = K_BOND·t³·C_geometry` (sound_packet_02 S1) produces a shell
  spectrum whose lowest-mode frequency RATIOS match a named thin-shell reference
  branch within the packet's ≤2× band, and whose lowest eigenfrequencies
  converge under 2× refinement at the expected linear-element FEM rate.
- **PREDICTION (unmeasured before the run):** F1 — the icosphere multiplet
  ladder f_l/f_2 within [0.5, 2]× of a named reference branch; F3 — sphere
  l=2 convergence rate p ≈ 2 and SALLY's lowest 20 shifts monotone and O(h²);
  F2 — Weyl count below the carrier-Debye cutoff ≤ N_dof.
- **FALSIFIERS (named before the run):** F1 FAIL = a measured ratio outside
  [0.5, 2]× of EVERY named branch (membrane sphere √(l(l+1)), Kraus
  inextensional (l(l+1)−2), pure bending l(l+1)); F3 FAIL = p outside
  [1.5, 2.5] or divergent/non-monotone SALLY shifts; F2 FAIL = Weyl > N_dof.

## ASSEMBLY (choices with refs)

Dual graph from the water reference's own loader (`.tmp/tri_water.py::
build_substrate` on `tw.load_part(tw.GLB_PATH, "SALLY_body_0")` — the birth
GLB, 34,538 tris; 206 zero-area faces dropped: A = 0 carries no mass and no
area rigidity, it has no dynamics). One scalar out-of-plane DOF per dual node.

- **Membrane (T2):** graph Laplacian L_m on dual edges with CONSTANT weight
  `k_e = 0.75·K_BOND/A0_eq_mesh`. **This is the measured-correct reading —
  see the lineage below.** A0_eq = (√3/4)·R_BOND² = 9.743e-3
  (`tools/ca_triangle.py:627`, "equilateral@R_BOND area (RUN A derivation ref)";
  R7b: "CA rest area = equilateral@R_BOND, no free number", `:647`), mapped to
  the mesh frame by the part's carrier scale S = R_BOND/e_med = 2.1413 (the
  CA's own named ratio, `docs/THE_TRIANGLE_CARRIER.md:135`; per-part constant,
  never recomputed for refined copies) ⇒ A0_eq_mesh = 2.1249e-3,
  **k_e = 352.95**.
- **Bending (packet-02 S1):** `D = K_BOND·t³`; discrete Kirchhoff form
  K_bend = D·L_gᵀ·diag(1/A)·L_g with L_g the geometric Laplacian (weights
  l_e/l_ij = C_geometry, from matching a dihedral spring ½Kb(Δθ)² to a
  curvature² energy ½D·κ²·l_e·l_ij with κ ≈ Δθ/l_ij). ω_flex ∝ t holds in the
  assembly (D ∝ t³, M ∝ t ⇒ ω ∝ √(t³/t) = t) — the packet-02 correction is
  present and correctly scaled.
- **Mass:** M_i = A_i·t·ρ. **t = 5e-3, ρ = 300 — CHOSEN-UNVERIFIED** (the
  packet's open experiment: measure plush skin thickness and density). Every
  ratio/rate verdict below is independent of t, ρ, and the unit convention;
  absolute "Hz" inherit mesh-length-unit × landed K_BOND = 1.0 and are flagged.
- **Null modes:** the scalar dual field cannot represent in-plane stretch of a
  uniform radial displacement ⇒ one constant-field null mode PER DUAL-GRAPH
  COMPONENT. This is packet-01 S1's "honest approximation (surface vs
  volumetric)" made concrete. Handled by shift-invert at σ = −1e-6·λ_scale and
  excluded from every table (identified by eigenvalue threshold, cross-checked
  against `csgraph.connected_components`).
- **Solve:** `scipy.sparse.linalg.eigsh` shift-invert (SuperLU), per-mode
  residual check ‖Kφ − λMφ‖/(λ‖Mφ‖) — 0 failures on all physical modes
  (residuals ~1e-11).

## THE LINEAGE — WHAT THE MATH CONTRADICTED (three assemblies measured)

1. **v1 (packet-literal per-triangle A0):** k_e = 0.75·K_BOND/A0_e with A0_e =
   the edge's own adjacent triangle areas. **F3 FALSIFIED: sphere f_l2 =
   0.919 → 1.826 → 3.649 Hz across subdiv 3/4/5 (p = −1.008)** — frequencies
   DOUBLE under refinement. This is the audit's element-level ω∝1/A pathology
   (Big Pickle's S5, quoted at the top of packet 02) MEASURED in the global
   eigenproblem: the stiffness eigenvalue is refinement-invariant while the
   nodal mass shrinks ∝ h². SALLY's lowest-20 shifts were −22…−38%.
2. **v2 (constant k_e + a "breathing" diagonal of my own):** the constant
   `k_e = 0.75·K_BOND/A0_eq` (packet-02 S5's "re-scaled k, m to preserve patch
   physics" made precise — k must NOT be re-derived from the sub-triangle's
   area) fixed the sphere ladder completely. But my added breathing term
   0.75·K_BOND·(A_i/A0_eq)·(2H_i)² (scalar reduction of the area law through
   rest curvature) **was REJECTED by measurement**: it dominated the low
   spectrum of the near-flat body (energy share ≈ 1.000 on the lowest modes)
   and its H-sampling collapses under midpoint refinement (new vertices lie on
   flat parent faces ⇒ H ≈ 0 there) ⇒ SALLY shifts −54…−76%
   (`results_v2_breathing_variant.json` preserved as evidence). It is not in
   either packet; it is dead.
3. **v3 (final):** packet-literal K = L_m(constant k_e) + K_bend(D ∝ t³), null
   block reported openly. **All stage-1 falsifiers below are v3.**

**Contradiction recorded for the packets:** packet-01 S1 writes "each shared
edge carries an area-rigidity spring k_area = 0.75·K_BOND/A0" with A0 read as
the local triangle area; read that way the assembly is refinement-inconsistent
at the GLOBAL level (v1, p = −1.008). The law survives only in its
constant-rest-area form (A0 := equilateral@R_BOND through the part's S) —
which is also what the landed CA actually computes (its meshes are scaled so
e_med = R_BOND and are near-uniform, `ca_run.json`: k_area_derived_median =
94.41 ≈ 0.75/A0_eq = 76.98, same order). The T2 master-list line should be
read with A0 = the carrier's rest-area constant, not the per-triangle area.

## MEASURED NUMBERS

### Substrate + carrier-Debye Nyquist (printed derivation)
- SALLY_body_0 birth mesh: 17,409 verts, 34,332 kept tris; dual nodes 34,332,
  dual edges 51,291; A_med = 1.4285e-3, l_ij_med = 3.7524e-2, A_surf = 87.43.
- **Dual-graph components: 25** (sizes 8044, 4958, 1686×2, 1590×2, 1418×2,
  1184×2, …) — the open-socket birth repair leaves the body as separate shell
  pieces (matches THE_TRIANGLE_CARRIER.md:134: shared-edge adjacency within a
  shell; cross-shell coupling is the fold walk's job — a stage-2 question).
- k_eff = 0.75·K_BOND/A0_eq_mesh = 352.95 (constant); m_node = A_med·t·ρ =
  2.1427e-3; **ω_D = 2√(k_eff/m_node) = 811.7 rad/s ⇒ f_max = 129.19 Hz**
  (the lattice-Debye cutoff of packet 02, replacing the air-343 14 kHz
  arithmetic); c_lat = ω_D·l_med/2 = 15.23 length-units/s.

### SALLY lowest physical modes (25-mode null block excluded; mem share ≈ 1.0000, bend share ~1e-6 on every one)
| mode | f (Hz) | f/f1 | | mode | f (Hz) | f/f1 |
|---|---|---|---|---|---|---|
| 1 | 1.6691 | 1.0000 | | 7 | 2.1657 | 1.2975 |
| 2 | 1.7858 | 1.0699 | | 8 | 2.1955 | 1.3153 |
| 3 | 2.0532 | 1.2301 | | 9–10 | 3.0651 | 1.8364 |
| 4–5 | 2.1185 | 1.2692 | | 11 | 3.0772 | 1.8436 |
| 6 | 2.1462 | 1.2858 | | 12 | 3.1348 | 1.8781 |

All 64 solved modes (incl. nulls) lie below the 129.19 Hz Debye cutoff.
Absolute Hz flagged: mesh-unit × K_BOND = 1.0 × CHOSEN t·ρ; ratios are exact.

### F1 — icosphere ladder (ca_run.json validation shape, R = 1.521 from V0 = 14.737; k_e = 76.98 carrier-frame constant)
Multiplets clean: count 3 @ 0.806 Hz (l=1), **5 @ 1.3945 (l=2), 7 @ 1.9716
(l=3, spread 3.7%), 9 @ 2.5430 (l=4, spread 2.9%)**; l≥5 merges in the
discretization (reported, not used). One null mode (9.9e-8 Hz).

| ratio | measured | membrane √(l(l+1)/6) | Kraus inext. (μ−2)/4 | pure bending μ/6 |
|---|---|---|---|---|
| f₃/f₂ | **1.4139** | 1.414 (1.00×, **IN**) | 2.500 (0.57×, IN) | 2.000 (0.71×, IN) |
| f₄/f₂ | **1.8236** | 1.826 (1.00×, **IN**) | 4.500 (0.41×, OUT) | 3.333 (0.55×, IN) |

**F1: PASS** — the ladder is the membrane-sphere branch essentially exactly
(1.00× both), inside 2× of the bending branch, and inside 2× of Kraus at l=3.
The Kraus inextensional branch is missed at l=4 (0.41×): reported honestly —
at the landed constants the scalar carrier IS a membrane-branch lattice
(bending energy share ~1e-6 at these wavelengths; see honest negatives).

### F3 — refinement convergence (the important one)
- **F3a sphere rate (1,280 / 5,120 / 20,480 tris):** f_l2 = 1.395840 →
  1.394465 → 1.394143 Hz, monotone approach from above, **measured p = 2.094**
  — the expected O(h²) for linear elements. **PASS** (band [1.5, 2.5]).
- **F3b SALLY 2× midpoint refinement (34,332 → 137,328 tris, surface
  bit-preserved, SAME carrier constants):** all 20 lowest physical modes shift
  **monotone up, +2.38…+4.31% (max 4.314%)**, no drift, no sign flips, zero
  residual failures. **PASS** (the pre-registered criterion: monotone and
  small; the base mesh's estimated discretization offset is ~4× the shift,
  ~11–17% — plausible at 34k tris with slivers, and stage 2 inherits it
  openly). Compare v1's −22…−38% and v2's −54…−76%: the constant-stiffness
  assembly is what makes the eigenproblem refinement-consistent.

### F2 — Weyl sanity
**N_Weyl(f_max) = A_surf·π·f_max²/c_lat² = 19,765 modes vs N_dof = 34,332 —
PASS** (the reduction cannot leak mass/resolution; 19.8k global modes below
the Debye cutoff is also the stage-2 bank's ceiling: 512 global modes is
2.6% of it, 1.2 GB float32 ≪ 24 GB VRAM per packet-01 S3).

## FALSIFIER TABLE

| # | falsifier (named before the run) | result | verdict |
|---|---|---|---|
| F1 | lowest-mode ratios vs thin-shell reference band (≤2×) | ladder = membrane branch at 1.00×/1.00×; inside 2× of bending; Kraus OUT only at l=4 | **PASS** |
| F2 | mode count below cutoff ≤ Weyl bound ≤ DOF | 19,765 ≤ 34,332 | **PASS** |
| F3 | convergence under refinement at expected FEM rate | sphere p = 2.094; SALLY 20/20 monotone +2.4…+4.3% | **PASS** |
| F3 (v1 reading) | per-triangle A0 assembly | p = −1.008 | **FALSIFIED** (recorded; the packet text needs the constant-A0 reading) |

## HONEST NEGATIVES / OPEN ITEMS

- **The ω ∝ t flexural law is assembled but unobservable in the low band.**
  Bending energy share of the lowest modes ~1e-6 (body) — at t = 5e-3 and
  K_BOND = 1.0 the membrane branch dominates at every resolved wavelength
  (crossover λ* ≈ mesh spacing). This is physically correct thin-shell
  behavior at t/R ~ 1e-3, but it means packet 02's headline "After: ω_flex ∝ t"
  is NOT what a stage-1 measurement can see: the low modes are
  membrane-branch and scale ω ∝ t^(−1/2). The D ∝ t³ term matters for the
  short-wavelength/patch band (stage 2's local modes), not the global low end.
- **t = 5e-3, ρ = 300 CHOSEN-UNVERIFIED** (experiment: measure plush skin
  thickness + density — sets absolute pitch). Rayleigh α, β CHOSEN-UNVERIFIED
  (experiment: record a plush impact, fit ζ_m) — not touched this stage.
- **The body is 25 dual-graph components** — the pieces ring independently in
  this stage. Cross-socket coupling (fold walk) is unbuilt; stage-2 impact
  response across sockets needs it named.
- Absolute Hz inherit mesh-unit × K_BOND = 1.0 (dimensionless-lu convention);
  a real pitch needs the t·ρ measurement AND the unit anchor — both flagged,
  neither hidden.
- Through-thickness/Lamb modes absent by construction (packet-01 S1 honesty).
- 206 zero-area birth faces dropped (no mass, no dynamics — stated rule).
- Sphere l≥5 multiplets merge under icosphere discretization; only l ≤ 4 used.

## READY FOR STAGE 2 (GPU/runtime bank + impact excitation)

- The mode table (ω_m, φ_m) is computable at runtime scale: sparse
  shift-invert solves the lowest N_global ≪ 19,765 Weyl-bounded modes;
  storage per packet-01 S3 (512 × 600k float32 = 1.2 GB < 24 GB).
- **Dependencies named:** impact excitation = the gait's contact impulse N_i
  (packet-01 S2, "one sensor, two senses") — **gait G3 load feedback is still
  in flight as H7** (G4 transition was FALSIFIED at CPU tier precisely because
  the stance-depth surrogate carried no body state; real substrate λ is
  mandatory). Stage-2 sound takes its impulse from the same λ when it lands.
- Damping α, β and the t·ρ measurement are the two open CHOSEN-UNVERIFIED
  experiments before absolute pitch (not ratios) can be pass-failed.
- Do not re-derive k_e per mesh resolution — the constant-stiffness reading
  (per-part S, A0_eq) is the measured-consistent law; v1's failure is recorded
  so the next agent doesn't re-pay for it.
