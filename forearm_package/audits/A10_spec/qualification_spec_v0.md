# QUALIFICATION SPECIFICATION v0 — MECHANICAL GRASP QUALIFICATION (FOREARM PACKAGE)

**Status: DRAFT — NOT APPROVED.** Owner: Astra (external architect). Drafted by: A10 (audit agent), 2026-09-24.
**Input revision:** `baseline_snapshot/MANIFEST.json` (44 files, crosschecks 4/4 green, `git_head_at_snapshot` `c70b7a6c` — MANIFEST.json lines 4–28, 251). Baseline snapshot untouched by this audit (`git status --porcelain -- forearm_package/baseline_snapshot` → empty; see `report.md`).
**Authority boundary:** this draft structures requirements and records current status with citations. It invents **no** numeric criteria values: every threshold that is not already an artifact law is a `[ASTRA-APPROVES: …]` placeholder. Sections 3–4 record status; section 6 proposes options; nothing here decides.

---

## 1. SCOPE & DEFINITIONS

### 1.1 Mission

The package exists to "qualify the monkey's physical grasp for climbing" (`TASK_BOARD.md` line 3). A **mechanically qualified grasp** must be a state in which a defined test set — executed against the frozen baseline artifacts, each test carrying its own falsifier — has PASSED under the architect's sign-off, thereby licensing the per-site flag `mechanical_qualification: true`. Today that flag is `false` on all 32 sites with the reason recorded in the artifact itself (`runs/attachment_candidates.json`, every site: `mechanical_qualification: false`, `mechanical_qualification_note`: "resolved coordinates and tendon endpoint membership do NOT qualify a membrane attachment port; qualification requires independent anatomical evidence not present in this packet."). Candidate C — the one preregistered placement fix attempt — FAILED its declared criteria (`runs/experiment_transverse_candidate.json`, `step_C_candidate.radius.passed = false`, `step_C_candidate.radius_l.passed = false`; shortfall ~41 µm against the clearance law, report 05 §4 line 43; `TASK_BOARD.md` line 9) and the failure STANDS.

### 1.2 The evidence ladder (stated as law)

**Geometric containment ≠ anatomical attachment evidence ≠ mechanical qualification.** No link in this chain may be crossed by wording. Anchors, verbatim:

- report 05 §6 ("What is NOT claimed", `session_reports/anatomy_compiler_05.md` lines 51–56):
  > - The candidate's pass/fail is against the DECLARED criteria; a ~41 µm shortfall is still a fail, and the two ambiguous wrist sections were not resolved by choosing a loop.
  > - Even a passing candidate would have remained authored transverse geometry under declared bounds — not recovered anatomy, not measured attachment, not mechanical qualification. It did not pass.
  > - `mechanical_qualification` is false for every site in the packet; endpoint roles are path positions only.
  > - No material inference, no training changes, no production wiring; the packet's fitted geometry is bit-identical to session 4 except the ADDED measurement records.
- Same law embedded in the experiment's own preregistration: `interpretation_limit`: "a passing candidate is AUTHORED transverse geometry under declared bounds — not recovered anatomy, not measured attachment, not mechanical qualification" (`experiment_transverse_candidate.json` → `preregistration.interpretation_limit`).
- The status ledger makes the same split per output value: `derived`, `kinematically_preserved`, `ingested_unchanged`, `requires_density_validation` / `requires_physiological_rerun`, `rigid_reference_zero`, `absent_in_source` (`code/DERIVATION.md` §12, lines 299–309). Mass-family outputs are explicitly NOT discharged by geometry: "Geometry resolution alone does NOT discharge requires_density_validation; no body is physically admitted because no validated material/mass source was supplied and none is invented" (`runs/admission_actual_monkey.json` → `admission.mass_admission.note`; `physically_admitted: 0`, line 16; `requires_density_validation: true`, line 81).

Consequence for this specification: passing T1 (containment) can never by itself produce qualification; qualification requires the whole T-set (§2) to pass as signed off by the architect.

### 1.3 Definitions (all from artifacts)

- **Site** — one of the 32 forearm muscle-attachment candidate points: 16 per side, owned by `radius` (right, unsuffixed names, e.g. `BRD-P2`) and `radius_l` (left, `_l` names, e.g. `BRD_l-P2`) (`attachment_candidates.json` → `bodies.radius.candidates` (16), `bodies.radius_l.candidates` (16); naming law `TASK_BOARD.md` line 23). Scope string: "foreign-forearm muscle attachment sites (radius, radius_l)" (`attachment_candidates.json` → `source.scope`).
- **Role** — path position of a site inside a tendon's ordered site list. Verbatim rule: "a site is a FIRST/LAST ENDPOINT of tendon X only when it is the first/last entry of X's ordered site_names; intermediate entries are waypoints and never endpoints for that tendon. Endpoint roles are NOT mechanical qualifications: every site ships mechanical_qualification=false." (`attachment_candidates.json` → `port_vs_waypoint_rule`). Measured: per body, 0 `first_endpoint`, 4 `last_endpoint` (right: `BIClong-P11`, `BICshort-P8`, `BRD-P3`, `PT-P5`; left: same `_l` names), 12 `waypoint` memberships (counted from `tendon_membership[].role`, this audit).
- **Containment class** — exactly four, per the classification law (report 05 §2, lines 17–22):

  | class | law (verbatim, report 05 §2) |
  |---|---|
  | `outside` | d > 0 at every variant — geometrically outside |
  | `inside_insufficient_clearance` | d ≤ 0 at every variant, clearance never reaches the 1 mm margin |
  | `inside` | d ≤ −1 mm at every variant |
  | `unresolved` | class flips under band-width variation, or no sampled band near the axial position |

  Field name in artifacts is `unresolved`; campaign prose (report 05 §4, TASK_BOARD) says "ambiguous" for the same class — this specification uses `unresolved` (the field) and notes "ambiguous" as its prose synonym.
- **Authority** — the measurement path whose verdict rules. Two are recorded per site (`attachment_candidates.json` → `skin_containment`): the **loop authority** (`authority: "local_triangle_plane_loop"` — triangle-plane section loops chained into closed loops, the limb's skin loop identified mechanically by majority pack-vertex ownership, no bridging, no proximity choice; exactly one loop must identify — report 05 §4 step B, line 41; DERIVATION §13 S14, line 344) and the **hull sampling diagnostic** (`hull_sampling_diagnostic`, retained verbatim, non-authoritative — report 05 line 4, §4 step B). Where the loop law cannot identify exactly one skin loop, the site is `unresolved` — this is section identification failing, not placement (report 05 §4 line 41, line 53).
- **Comparable chain** — a tendon whose candidate-site path has both chain endpoints resolved, so its length can be compared across revisions: "sum over consecutive path pairs with both endpoints resolved (same rule both revisions)" (`experiment_transverse_candidate.json` → `preregistration.evaluation.tendon_lengths`); flag `tendon_deltas[<tendon>].comparable`. Measured: 42 of 120 comparable.
- **mechanical_qualification** — per-site boolean. `false` everywhere today (all 32 sites, `attachment_candidates.json`). Under this specification it may become `true` for a site only when the full T-set of §2 has passed as signed off by the architect and no blocker of §4 remains open for that site's evidence chain. This specification does not define the numeric pass values; it defines the structure that has them.

---

## 2. REQUIRED TEST CATEGORIES T1–T8

Each category states: purpose; input artifacts (exact paths + MANIFEST sha256); pass-criterion TEMPLATE (placeholders, no invented numbers); falsifier style (each test must be able to FAIL); current status vs baseline. Artifact paths are relative to `baseline_snapshot/`.

### T1 — Containment resolution

- **Purpose:** every one of the 32 sites carries a loop-authority containment verdict from the four-class law, with zero `unresolved` sites, so "inside the skin" is measured, not assumed. (Campaign-mandated shape: "32/32 sites classified with zero ambiguous — currently 2 ambiguous", A10 brief.)
- **Input artifacts:** `runs/actual_monkey_fit.json` (sha256 `a4475550…0937`); `runs/admission_actual_monkey.json` (`833ca65b…b4ad`); `runs/attachment_candidates.json` (`854f7097…32ae`); `code/target_envelope.py` (`1752c0fd…f1307`); `code/run_tests.py` (`f46f1c4a…857b`, tests S11/S14); `inputs/monkey_birth.bin` (`550a5b3e…fa3c`), `inputs/monkey_joints.bin` (`74b3ab04…c1662`).
- **Pass-criterion TEMPLATE:**
  - T1.1: 32/32 sites carry a `skin_containment.loop.verdict` in the four-class set; no missing verdicts.
  - T1.2: zero sites with verdict `unresolved` (field `unresolved` / prose "ambiguous").
  - T1.3: `inside` sites satisfy the artifact clearance law `d ≤ −1 mm` at every variant, `inside_insufficient_clearance` sites are reported as tight, not counted as inside (report 05 §2 table; `experiment_transverse_candidate.json` → `preregistration.clearance_requirement`: "every site inside every fitting-section hull with d <= -0.001 m"). Any change to this margin is an architect decision under the frozen boundary "No margin relaxation" (`TASK_BOARD.md` line 10) — `[ASTRA-APPROVES: any clearance-margin definition differing from the artifact law]`.
  - T1.4: `[ASTRA-APPROVES: the accepted classification authority per site — loop authority is the artifact default; any per-site waiver must name the alternative evidence]`.
- **Falsifier style:** FAIL if any site is `unresolved` or unclassified; FAIL if a class flips under band-width variation without being marked `unresolved` (S11 law, DERIVATION §13 line 341); FAIL if open section chains were bridged or a loop was chosen by proximity rather than pack-ownership identification (S14 law, DERIVATION §13 line 344; report 05 §4 reason strings).
- **Current status vs baseline:** NOT SATISFIED. Loop authority per side: 6 inside / 1 tight (`PT-P3`, `PT_l-P3`) / 7 outside / 2 `unresolved` (`admission_actual_monkey.json` → `envelope.radius.loop_outside` (7 names, lines 131–139), `loop_tight` (`PT-P3`), `loop_ambiguous` (`ECRB-P3`, `ECRL-P3`); same for `radius_l` lines 181–197; `loop_authority_ok: false` lines 130, 181; corroborated by `experiment_transverse_candidate.json` → `step_B_baseline_loop_authority.{radius,radius_l}` and `TASK_BOARD.md` line 18). Flags `envelope_containment_ok: false`, `envelope_containment_loop_ok: false` (admission lines 90–92). Hull diagnostic (per side): 5 outside / 0 tight / 8 `unresolved` (`TASK_BOARD.md` line 20; admission `containment_unresolved` 8 names). 30/32 sites are classified; the 2 per-side wrist sites are the open blocker — §4(a), [PENDING A1] [PENDING A2] [PENDING A5].

### T2 — Attachment evidence classes

- **Purpose:** every site carries a stated evidence class that separates (i) geometric containment, (ii) anatomical attachment evidence, and (iii) fitted assumption — so the evidence ladder (§1.2) is checkable per site, per A6's taxonomy.
- **Input artifacts:** `runs/attachment_candidates.json` (`854f7097…32ae`, per-site `mechanical_qualification` + note); `code/DERIVATION.md` (`cba8b8a1…5d25`, §12 status ledger); `session_reports/anatomy_compiler_05.md` (`ed6e333c…36ce`, §6); source anatomy `source_xml/chimanoid.xml` (`675e00d0…83d1`).
- **Pass-criterion TEMPLATE:** every site carries an evidence-class label from the taxonomy `[ASTRA-APPROVES: the evidence-class taxonomy per A6 findings]`; every label maps to named evidence (field or external artifact) or is capped at the geometric tier; no site's label exceeds what its cited evidence supports.
- **Falsifier style:** FAIL if any site claims a tier above geometric containment while its only evidence fields are resolved coordinates + tendon endpoint membership (the exact condition the packet's own note forbids); FAIL if a label exists with no citable evidence record.
- **Current status vs baseline:** BLOCKED — the taxonomy does not yet exist in the artifacts; the packet currently carries only the negative fact (`mechanical_qualification: false` + note on all 32 sites). [PENDING A6] for the taxonomy findings; adoption is `[ASTRA-APPROVES: taxonomy adoption]`.

### T3 — Source fidelity

- **Purpose:** the 32 sites' source coordinates, units, and roles in the packet are verbatim the source XML's — no scaling, rounding, or relabeling crept in (report 05 §1 correction 1).
- **Input artifacts:** `source_xml/chimanoid.xml` (`675e00d0…83d1` raw; canonical `7caa32c6…`); `runs/attachment_candidates.json` (`854f7097…32ae`, per-site `source_pos_local`, `source_pos_local_units`, `endpoint_roles`); `code/intake.py` (`a607af51…f8897`); `code/run_tests.py` (`f46f1c4a…857b`, test S13).
- **Pass-criterion TEMPLATE:** for all 32 sites: `source_pos_local` equals the raw-XML `pos` floats exactly (S13 asserts exported == XML value — the artifact's law is exact equality, report 05 §1); the units label is present and correct ("source SI (metres), verbatim from the XML — NOT scaled by the target mesh factor", `attachment_candidates.json` per-site `source_pos_local_units`; body units `source_positions`: "source SI (metres), verbatim XML values", `target_positions`: "target metres (mesh units x authored 0.065 applied to TARGET mesh only)"); roles re-derive exactly per `port_vs_waypoint_rule`. `[ASTRA-APPROVES: any tolerance looser than exact float equality, if ever proposed]`.
- **Falsifier style:** FAIL on any exported-vs-XML mismatch; FAIL on any `_m`-style relabeling of source coordinates or mesh-factor (0.065) contamination of source values (S13's mesh-factor-distance pin; report 05 §1).
- **Current status vs baseline:** receipts exist (S13 green — report 05 line 5 "G0 + F1–F7 + S1–S14 all green, exit 0" and §5 line 47). One cross-check discrepancy is open and must be resolved by the site audit: report 05 §3 (line 29) states "8 last-endpoints per side, 0 first-endpoints … 24 waypoints", but the artifact counts per body are 4 `last_endpoint` / 12 `waypoint` / 0 `first_endpoint` memberships — the report's figures equal the both-sides totals (8, 24), so the "per side" phrasing appears mislabeled. The artifact, not the prose, is the record; [PENDING A3] to verify the 32 sites against the XML and settle the prose.

### T4 — Transform + bilateral integrity

- **Purpose:** every exported world point is reproducible from its local coordinates and the exported transform, and the fit respects bilateral symmetry — per A4.
- **Input artifacts:** `runs/attachment_candidates.json` (`854f7097…32ae`, per-body `local_to_world`: `R_source_local_to_target`, `t_fitted_origin_m`, `composition`: "R = Bp @ diag(scale) @ B.T …", `max_world_reconstruction_error_m`); `runs/experiment_transverse_candidate.json` (`3c13fca7…ab3a`, `step_A_verification`); `code/compiler.py` (`8a4ba07c…df852`); `code/correspondence.py` (`21770e6c…4a7df8`).
- **Pass-criterion TEMPLATE:** reconstruction error of `fitted_pos_global = fitted_origin + R @ source_pos_local` within `[ASTRA-APPROVES: reconstruction tolerance]` — existing artifact receipts: `max_world_reconstruction_error_m: 0.0` (candidates packet, both bodies) and `1.1525314521376605e-09` m against bound 1e-6 (experiment step A, report 05 §4 line 39). Bilateral: reflecting the right side across the sagittal plane x = 0 reproduces the left side's 16 points within `[ASTRA-APPROVES: bilateral bound]` — existing artifact receipt: `max_pair_error_m: 0.000631`, `mean_pair_error_m: 5.5e-05`, `sanity_bound_m: 0.02` (experiment `step_A_verification.mirror`; report 05 §4: max 0.63 mm, mean 0.055 mm, bound 20 mm). `R` must be a proper rotation composed as recorded.
- **Falsifier style:** FAIL on reconstruction above bound; FAIL on improper `R` (det ≠ +1); FAIL on bilateral error above the sanity bound; FAIL on any unit crossing between source (SI) and target (metres) spaces.
- **Current status vs baseline:** receipts exist in the artifacts (step A "verification (passed)", report 05 §4 line 39). Independent verification of transforms and bilateral correspondence [PENDING A4].

### T5 — Reproducibility / determinism

- **Purpose:** the whole pipeline is regenerable byte-identically and the full falsifier suite is green — per A9.
- **Input artifacts:** `code/run_tests.py` (`f46f1c4a…857b`); `code/synthetic_fixtures.py` (`cbefde27…76034`); all `runs/*` hashes in `MANIFEST.json` (lines 160–219); `code/DERIVATION.md` §13 (S4 "deterministic", S12 "bit-identical rebuild", lines 334, 342).
- **Pass-criterion TEMPLATE:** `python run_tests.py` exits 0 with G0 + F1–F7 + S1–S14 green; regeneration of the run artifacts is byte-identical to the MANIFEST hashes (S12 law); the counts gate (19 bodies / 39 coords / 468 sites / 120 tendons / 121 muscles) reproduces on the real XML intake and the synthetic fixture (DERIVATION §0 counts gate, lines 56–58). `[ASTRA-APPROVES: which of these constitute release-blocking tests vs informational]`.
- **Falsifier style:** FAIL on any red test; FAIL on any byte drift between regenerated and MANIFEST-hashed artifacts; FAIL on nondeterminism across two consecutive regenerations.
- **Current status vs baseline:** session-5 receipt exists (report 05 line 5: "G0 + F1–F7 + S1–S14 all green, exit 0"; §5 line 47). Independent reproduction on the current environment, byte-identity, and the H-1 hash confirmation [PENDING A9] — environment status is blocker §4(d).

### T6 — Path / excursion consistency

- **Purpose:** exported tendon rest lengths are the closed-form path sums, and rebaselined `lengthrange` values are exactly `λ·range` with `λ = L′_rest/L_rest` — per A7 (`DERIVATION.md` §7 line 209 "Rest length L₀ = Σ_{j<K} |s_{j+1} − s_j|"; §10 lines 271–274, flag `assumption: homogeneous_path_scaling`).
- **Input artifacts:** `runs/actual_monkey_fit.json` (`a4475550…0937`, paths + rest lengths + `lengthrange′`); `runs/experiment_transverse_candidate.json` (`3c13fca7…ab3a`, `tendon_deltas`, 120 entries); `code/compiler.py` (`8a4ba07c…df852`); `code/DERIVATION.md` (`cba8b8a1…5d25`).
- **Pass-criterion TEMPLATE:** for every tendon: exported rest length equals the recomputed path sum; `range′ = λ·range` holds with the recorded λ; the comparable-chain rule ("both endpoints resolved, same rule both revisions", `preregistration.evaluation.tendon_lengths`) is applied symmetrically across revisions; `[ASTRA-APPROVES: the pose/excursion sweep that defines consistency, and its tolerance]` (DERIVATION §14 declares homogeneous path scaling as an ASSUMPTION — validating or bounding it is an architect-gated decision, not a default).
- **Falsifier style:** FAIL on any tendon whose exported rest length ≠ recomputed sum; FAIL on any `lengthrange′` ≠ λ·range; FAIL on a comparable-chain rule applied asymmetrically (a chain comparable in one revision and not the other without a stated reason).
- **Current status vs baseline:** instrument receipts exist — the candidate experiment produced a full 120-entry `tendon_deltas` census: 42 comparable, of which exactly 2 have nonzero length delta (`BRD_tendon` −9.0164e-04 m, `BRD_l_tendon` −9.01337e-04 m; report 05 §4 "max |Δ path length| = 0.90 mm (BRD)"). Baseline-wide L₀-vs-`lengthrange′` consistency validation [PENDING A7].

### T7 — Transmission non-degeneracy

- **Purpose:** the fitted forearm actually transmits force: a census of signed moment arms over tendon × coordinate pairs exists, the zero-arm law holds where it must, and no forearm tendon is degenerate (all-zero transmission) across the declared pose range — per A8.
- **Input artifacts:** `runs/actual_monkey_fit.json` (`a4475550…0937`, per-pair analytic + finite-difference arms); `code/compiler.py` (`8a4ba07c…df852`, `_analytic_arm`); `code/DERIVATION.md` (`cba8b8a1…5d25`, §8 lines 215–246: motion model, analytic gradient, F5 cross-check; §8.1 zero-arm law: root free-fly coordinates carry "arm: 0, reason: rigid_reference"); `runs/experiment_transverse_candidate.json` (`3c13fca7…ab3a`, `preregistration.evaluation.moment_arms`: "compiler._analytic_arm recomputed identically for baseline and candidate positions").
- **Pass-criterion TEMPLATE:** every tendon × coordinate pair reports a signed arm; analytic vs central-FD agreement within the existing artifact law `|arm_analytic − arm_fd| / (1 + |arm_fd|) < 1e-9` (DERIVATION §8.3 line 244, F5); root free-fly coordinates are exactly the zero-arm set with `reason: rigid_reference`; the nonzero-arm census is non-empty for forearm function; any all-zero forearm tendon across the declared pose range is either a declared FAIL or `[ASTRA-APPROVES: named degeneracy exception]`. `[ASTRA-APPROVES: the pose range over which non-degeneracy is demanded]`.
- **Falsifier style:** FAIL on any analytic/FD disagreement; FAIL on any nonzero arm attributed to a rigid-reference coordinate; FAIL on an unexplained all-zero transmission chain.
- **Current status vs baseline:** F5 green receipt exists (report 05 line 5); the candidate experiment measured `moment_arm_max_abs_delta_m = 0.0` across all 120 tendons (report 05 §4: "max |Δ moment arm| ≈ 0 (1e-12 rounding floor)" — straight-tendon zero-arm preservation). Full nonzero-arm census over the declared pose range [PENDING A8].

### T8 — Package integrity

- **Purpose:** every consumed artifact is hash-identified; the three hash families (source XML raw/canonical, fitted packet, candidates packet) are separate and never aliased; the manifest's crosschecks are green.
- **Input artifacts:** `MANIFEST.json` (44 files, lines 29–250); `runs/attachment_candidates.json` (`854f7097…32ae`, `provenance_hashes`: `source_xml_raw_sha256` `675e00d0…`, `source_xml_canonical_sha256` `7caa32c6…`, `fitted_packet_sha256` `a4475550…`, `target_mesh_sha256` `550a5b3e…`, `target_pack_sha256` `74b3ab04…`, and the note: "source XML hashes identify the UPSTREAM anatomy file; fitted_packet_sha256 identifies the WRITTEN fitted packet bytes. They are different objects and never interchangeable."); manifest regeneration tool at `../../tools/make_manifest.py` (outside baseline, in the package tree).
- **Pass-criterion TEMPLATE:** manifest crosschecks 4/4 green (they are today — MANIFEST lines 4–28: XML == `source_sha256`, `monkey_birth.bin` == `target_mesh_sha256`, `monkey_joints.bin` == `target_pack_sha256`, H-1 `fitted_packet_sha256` == sha256 of `actual_monkey_fit.json`); every file listed with bytes/mtime/sha256 and all hashes verified; raw vs canonical XML hashes recorded separately; fitted-packet hash never aliased to the candidates packet; `[ASTRA-APPROVES: the rule resolving the candidates-packet self-hash gap — blocker §4(c)]` and `[ASTRA-APPROVES: whether MANIFEST.json itself must carry a self-hash or external anchoring]` (MANIFEST.json does not appear in its own `files` map).
- **Falsifier style:** FAIL on any hash mismatch at verification time; FAIL on any aliasing of the hash families; FAIL on any future packet revision shipped without a self-hash (once the rule above is set).
- **Current status vs baseline:** PARTIAL — crosschecks green and hash separation established (report 05 §3 "Hash separation" line 31; MANIFEST crosschecks); the candidates packet carries no self-hash of its own bytes (its top-level keys are `kind, source, revision, revision_safety, port_vs_waypoint_rule, bodies, provenance_hashes` — none is a self-hash; the observation is pre-recorded at `TASK_BOARD.md` line 22). [PENDING A9] to confirm independently.

---

## 3. CURRENT-STATE TABLE

| Category | Status | Receipt / citation |
|---|---|---|
| T1 containment resolution | **NOT SATISFIED** (2 `unresolved` sites/side) | `admission_actual_monkey.json` `envelope.radius.loop_authority_ok: false`, `loop_ambiguous: ["ECRB-P3","ECRL-P3"]` (lines 130, 143–146); `radius_l` (lines 181, 194–197); `experiment_transverse_candidate.json` `step_B_baseline_loop_authority` counts 6/1/7/2 per side; `TASK_BOARD.md` line 18. [PENDING A1] [PENDING A2] [PENDING A5] |
| T2 attachment evidence classes | **BLOCKED** — taxonomy missing | All 32 sites carry only `mechanical_qualification: false` + note (`attachment_candidates.json` per-site fields); [PENDING A6] |
| T3 source fidelity | Receipt exists; one prose cross-check open | S13 green (report 05 lines 5, 47; §1); units strings in `attachment_candidates.json`; role-count phrasing discrepancy (report 05 §3 line 29 vs artifact counts) — [PENDING A3] |
| T4 transform + bilateral | Receipt exists; independent check open | `experiment_transverse_candidate.json` `step_A_verification` (reconstruction 1.1525e-09 m; mirror max 6.31e-04 m, mean 5.5e-05 m); `attachment_candidates.json` `local_to_world.max_world_reconstruction_error_m: 0.0`; report 05 §4 step A. [PENDING A4] |
| T5 reproducibility/determinism | Receipt exists; reproduction open | report 05 line 5 ("G0 + F1–F7 + S1–S14 all green, exit 0"), §5; DERIVATION §13 S4/S12. [PENDING A9] |
| T6 path/excursion consistency | **BLOCKED** — assumption not yet validated | DERIVATION §10 (`homogeneous_path_scaling`), §14 (declared assumption); 120-entry `tendon_deltas` census exists (42 comparable). [PENDING A7] |
| T7 transmission non-degeneracy | Census open; F5 receipt exists | DERIVATION §8, F5 (report 05 line 5); arm deltas 0.0 in `tendon_deltas`. [PENDING A8] |
| T8 package integrity | **PARTIAL** — crosschecks green; self-hash gap | `MANIFEST.json` lines 4–28 (4/4 green); `provenance_hashes` separation (report 05 §3); no candidates-packet self-hash (`TASK_BOARD.md` line 22). [PENDING A9] |
| Candidate C (preregistered placement fix) | **FAILED — failure stands** | `experiment_transverse_candidate.json` `step_C_candidate.radius.passed: false`, `.radius_l.passed: false`; `fitting_sections_ok: false` (right); optimum `db_m: 0.00624`, `dc_m: ±0.00202`, `max_displacement_m: 0.006558811`; ~41 µm shortfall (report 05 §4 line 43); `TASK_BOARD.md` lines 9, 21 |
| `mechanical_qualification` (the flag itself) | **FALSE — all 32 sites** | `attachment_candidates.json` per-site `mechanical_qualification: false` + note; report 05 §6; `TASK_BOARD.md` line 12 |
| Physical (mass) admission | **0 of 9 resolved bodies**; density validation required | `admission_actual_monkey.json` `admission.counts.physically_admitted: 0` (line 16), `mass_admission.requires_density_validation: true` (line 81), note lines 83 |

---

## 4. EXACT UNRESOLVED BLOCKERS

**(a) The 2 ambiguous wrist sections (per side).** Right: `ECRB-P3`, `ECRL-P3`; left: `ECRB_l-P3`, `ECRL_l-P3` (`admission_actual_monkey.json` lines 143–146, 194–197). Artifact facts: at those axials the section yields 4 closed loops of which **2** are identified as the limb's skin by pack ownership, 0 open chains; verdict `unresolved` with the reason "ambiguous_section: 4 closed loop(s) (2 identified as this limb's skin by pack ownership) + 0 open chain(s) at this axial position; no bridging, no repair, no proximity choice" (`experiment_transverse_candidate.json` → `step_B_baseline_loop_authority.radius.per_site["ECRB-P3"|"ECRL-P3"]`; axial 0.051510357 m and 0.053482959 m respectively). The hull diagnostic also returns `unresolved` there (`admission_actual_monkey.json` `containment_unresolved` includes `ECRB-P3`, `ECRL-P3`, lines 125–126; `hull_sampling_diagnostic.verdict: "unresolved"`, `dist_to_hull_m: null` in `attachment_candidates.json` per-site records). Candidate C did not resolve them: `loop_authority_candidate` still lists `unresolved: ["ECRB-P3","ECRL-P3"]` (report 05 §4 line 43: "section identification, not placement"). Resolution-evidence requirements (what any fix MUST produce; the choice among them is Astra's):
  - R1: a mechanically identified single skin loop at each of the 4 sites — by the S14 law (closed-loop chaining, majority pack-ownership identification, no bridging, no proximity choice; DERIVATION §13 line 344), not by picking one of the 2 identified loops;
  - R2: evidence that distinguishes the two ownership-identified loops (e.g., section/continuity evidence from axials where identification is unique, or denser section sampling from the existing `inputs/` mesh — no fit change), recorded in the packet with hashes;
  - R3: the four-class law and the margin law remain exactly as in §1.3/T1 (no relaxation);
  - R4: whatever resolves it must leave Candidate C's failed verdict untouched (frozen boundary, `TASK_BOARD.md` lines 9, 14).
  [PENDING A1] (left) and [PENDING A2] (right) for the independent investigations; integration at I1 (`TASK_BOARD.md` line 43).

**(b) The qualification gate itself.** `mechanical_qualification: false` on every site until the T-set of §2 is signed off by Astra AND passes; the flag can only flip through that gate — never by wording (evidence ladder, §1.2; per-site note; `TASK_BOARD.md` line 12). Missing evidence: the complete T-set (T1, T2, T6, T7 currently not satisfied/blocked; T3–T5, T8 awaiting independent audit confirmation) plus `[ASTRA-APPROVES: the pass values and the sign-off record]`.

**(c) The candidates packet carries no self-hash.** Observed directly: top-level keys of `attachment_candidates.json` are `kind, source, revision, revision_safety, port_vs_waypoint_rule, bodies, provenance_hashes` — no field hashes the packet's own bytes. The existing `fitted_packet_sha256` (`a4475550…`) names the FIT packet, confirmed: MANIFEST crosscheck H-1 shows it equals sha256 of `runs/actual_monkey_fit.json` and NOT sha256 of `runs/attachment_candidates.json` (`854f7097…`) (MANIFEST lines 5–11; `TASK_BOARD.md` line 22; report 05 §3 line 31). Needed: `[ASTRA-APPROVES: the self-hash rule for packet revisions]`; independent confirmation [PENDING A9].

**(d) Environment / reproducibility status.** Session-5's green receipt was produced in its own environment; whether it reproduces here (tests exit 0, byte-identical regeneration, hash invariants hold) is exactly what A9 must establish before T5 can be marked satisfied. [PENDING A9].

**(e) Further items the artifacts show:**
- **e1 — role-count prose discrepancy:** report 05 §3 line 29 says "8 last-endpoints per side … 24 waypoints"; the artifact says 4 `last_endpoint` / 12 `waypoint` memberships per body (both-sides totals 8 / 24). The artifact is the record; prose should be corrected or explained. [PENDING A3].
- **e2 — mass admission is open:** `physically_admitted: 0`, `requires_density_validation: true`, `density_validated: false` (`admission_actual_monkey.json` lines 16, 81–83). Any qualification claim that leans on mass/force quantities (T7's transmission claims at climbing loads) must state whether it depends on this open item.
- **e3 — scope of "grasp" vs unresolved bodies:** the admission marks 9 bodies unresolved, including `hand_l`, `hand_r`, `ulna`, `ulna_l` (`admission_actual_monkey.json` lines 31–41), while all 32 candidate sites live on `radius`/`radius_l`. Whether forearm-only containment can qualify a *grasp* whose hand bodies are unresolved is a scope ruling for Astra; this spec flags it, not decides it.
- **e4 — loop-vs-hull disagreement inventory:** loop sharpens hull (hull 5 outside/0 tight/8 unresolved per side vs loop 7 outside/1 tight/2 unresolved; `TASK_BOARD.md` line 20). The residual disagreements (e.g., `BIClong-P9`, `BICshort-P6` outside at axials hull bands never sampled; `PT-P3` tight) are recorded but not independently re-measured. [PENDING A5].
- **e5 — MANIFEST self-coverage:** `MANIFEST.json` does not appear in its own `files` map (44 entries, none is the manifest); its integrity is anchored only externally (git). Minor, but belongs in the T8 integrity rule.
- **e6 — the tendon-less muscle:** 121 muscles, 1 with no tendon (`DERIVATION.md` §2 line 92, §10 lines 277–278, carried `no_path`); the census laws of T6/T7 must state its treatment explicitly so the 120-vs-121 counts never silently drift.

---

## 5. NON-GOALS (frozen boundaries, faithful to `TASK_BOARD.md` lines 7–14)

- The session-5 baseline is unchanged; Candidate C FAILED its declared criteria (~41 µm over the ≤ −1 mm clearance law) — **the failure stands** (`TASK_BOARD.md` line 9; report 05 §4; `step_C_candidate.*.passed: false`).
- **No second fitting candidate.**
- **No anatomical-site displacement.**
- **No margin relaxation.**
- Preserve verbatim source coordinates, the four containment classes, v5 provenance, endpoint roles, separate XML/fitted-packet hashes (`TASK_BOARD.md` line 11).
- `mechanical_qualification` stays `false` on every site until the architect has signed off a passing test set (`TASK_BOARD.md` line 12, paraphrased; the gate is §4(b)).
- No physics, attachment-semantics, muscle-limit, or architecture changes — those go to Astra with evidence + smallest proposed change (`TASK_BOARD.md` line 13).
- New qualification criteria cannot retroactively rescue Candidate C (`TASK_BOARD.md` line 14).
- And from the scope anchor (report 05 §6, quoted verbatim in §1.2): even a passing candidate "would have remained authored transverse geometry under declared bounds — not recovered anatomy, not measured attachment, not mechanical qualification. It did not pass."

---

## 6. PROPOSALS-FOR-ASTRA (options only — smallest change first; none is a decision)

**P1 — Resolve the wrist ambiguity by pure measurement (no fit change).**
- *What it would change:* adds measurement records only — e.g., additional section planes and/or continuity tracking from axials where loop identification is unique (14 of 16 sites/side identify exactly 1 loop today; the 2 wrist sites identify 2 — `step_B_baseline_loop_authority.*.per_site` fields `n_identified_loops`) into the wrist band — recorded as an append-only revision of the measurement records.
- *Evidence that gates it:* the new sections must identify exactly one skin loop at (or continuously traceable to) each of the 4 sites under the S14 law (no bridging, no proximity choice — requirement R1/R2 of §4(a)); the resulting class must be stable under the band-width variation of S11. [PENDING A1] [PENDING A2] supply the independent investigation this builds on.
- *What it does NOT change:* site placement, the four-class law, the clearance margin, Candidate C's failed verdict, any existing hash (append-only; new revision gets its own hashes per T8).

**P2 — An Astra ruling on classification authority at the wrist sites.**
- *What it would change:* which measurement path's verdict rules at the 4 wrist sites (loop authority vs hull diagnostic), possibly site-class-scoped.
- *Evidence that gates it:* an authority that actually returns a non-`unresolved` verdict there. Current artifacts show **neither** does: loop gives `n_identified_loops: 2` (ambiguous section) and hull gives `unresolved` with `dist_to_hull_m: null` at `ECRB-P3`/`ECRL-P3`. A ruling alone, over today's data, produces no class — it must be combined with P1's new measurement or P3's acceptance.
- *What it does NOT change:* the data, the class definitions, placement, or Candidate C's verdict; and it cannot turn `unresolved` into `inside`/`outside` by fiat — only a measurement or a documented-uncertainty ruling can.

**P3 — Accept `unresolved` as a permanent documented uncertainty class at the wrist sites.**
- *What it would change:* T1.2's "zero `unresolved`" target would be replaced by `[ASTRA-APPROVES: the maximum count and identity of permanently unresolved sites under which qualification may still be granted]`, plus a documented uncertainty statement per such site (the evidence ladder then caps those sites' claims at "not measured" for clearance).
- *Evidence that gates it:* an Astra risk ruling, informed by [PENDING A1]/[PENDING A2] and [PENDING A5]'s uncertainty budget; the ruling must state explicitly what a climbing-qualification claim may and may not assert at sites whose clearance is not measured.
- *What it does NOT change:* placement, classes for the other 28 sites, margins, Candidate C's verdict, the requirement that the remaining T-set pass.

**P4 — Packet self-hash rule (blocker §4(c)).**
- *What it would change:* a future revision (v6+) of `attachment_candidates.json` adds a field carrying the sha256 of its own written bytes (computed after write, mirroring `fitted_packet_sha256`'s pattern); same rule extended to future MANIFEST revisions if desired.
- *Evidence that gates it:* none beyond the regeneration itself — but the regeneration must reproduce all existing measured values byte-for-byte except the added field, under the S12 revision-safety discipline (`revision_safety` field; DERIVATION §13 S12).
- *What it does NOT change:* no measured value, no class, no baseline file (the baseline snapshot stays frozen; this is a proposal for the next revision only).

**P5 — Scope ruling on mass admission and hand coverage (blockers §4(e2), §4(e3)).**
- *What it would change:* an explicit statement of whether the qualification's T-set must include mass-admission-dependent tests (given `requires_density_validation: true`, `physically_admitted: 0`) and whether forearm-only coverage suffices while `hand_*`/`ulna_*` bodies are unresolved.
- *Evidence that gates it:* [PENDING A7]/[PENDING A8] (what the transmission claims actually depend on) + the admission artifact's own note that no validated material/mass source was supplied and none is invented.
- *What it does NOT change:* geometry, containment classes, placement, Candidate C.

---

*DRAFT v0 ends here. This document is NOT APPROVED; pass-2 (integration queue I2, `TASK_BOARD.md` line 44) folds the verified A1–A9 findings into the `[PENDING …]` slots.*
