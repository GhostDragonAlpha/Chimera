# MAT2-B02 preregistration — frozen BEFORE any implementation or verification execution

- task: MAT2-B02 (attempt 5cf7f1cc0d1b40cb9f4a08fc12c4c535)
- agent: arrival-cccbccce34f94eb294f9e71640348b64
- criteria_sha256: 151a4aa7693f30c49a32167c78301240b68d701ce1ea766134c71a4080454d7e
- pinned target (no substitution): 1af0bbdee68d6ddfdd02bf9bd948f7b22f914d56
- profile: records / offline; numerical evidence required; falsifier: "Missing
  identities or a claimed pass unsupported by records fails; a screenshot is
  not a substitute."
- machine: CPU-only Windows, CPython 3.14.3, numpy 2.2.6, `python -B`,
  `PYTHONDONTWRITEBYTECODE=1`; no GPU, no network use during execution.
- Authorization chain: card done_when + frozen receipt `3db8bc4e` inventory
  U2–U10 + B01 frozen receipt handoff ("U2–U10 … stay open for B02"; "the
  exporter's `scale_to_m != 1.0` input path is NOT exercised or claimed
  (U2, B02 scope)").
- This file is written before authoring any fixture, oracle, test, or
  diagnostic, and before running any probe of this attempt. Only
  reconciliation reads (git history, pinned bytes, receipts, board) and the
  clause map preceded it. No tolerance, fixture geometry, prediction, or
  falsifier may be edited after this freeze; deviations are reported as
  observed with a named classification.

## Statement being qualified

At the pinned revision `1af0bbde` the exporter battery (66 unique tests) left
the frozen receipt's assertions U2–U7 without any test and named U8–U10 as
out of scope for an offline records card. This attempt supplies the missing
scale/transform/status/numerical tests and static diagnostics as fresh,
source-bound numerical evidence at the pinned bytes, each with a distinct
evidence class, and inventories U8–U10 explicitly as unresolved for their
downstream owners. Card observation honored: none of these coupons becomes a
release or runtime gate; every exporter output stays `validation_only`,
`production_wired: false`, `dynamics_readiness_claimed: false`.

## Independent role disclosure

The exporter/reader/admission/compiler bytes are the original author's
(pinned, never modified by this attempt). This attempt authors its own
coupons and an exact-arithmetic oracle (stdlib `fractions` only, no import of
any frozen module, no reuse of frozen oracle code) written fresh in this
attempt workspace. That supplies an independent expectation source for every
comparison below, covering the export path at the pinned bytes. Independent
review of this attempt remains downstream reviewer work and is not claimed
here.

## Frozen fixtures (authored after this freeze, exactly as specified here)

All coordinates are exactly representable binary fractions. Vertex IDs use a
bijection; every cell is listed with positively oriented vertex order.

- **Coupon N** (2 bodies, 3 cells; scale_to_m 1.0):
  - cell-na1: [(0,0,0), (1,0,0), (0,1,0), (0,0,1)], region-A, material tissue-A (ρ=12 kg/m³)
  - cell-na2: [(1,0,0), (0,1,0), (0,0,1), (2,1,1)], region-A, material tissue-B (ρ=7)
  - cell-nb1: [(5,-3,2), (6,-3,2), (5,-2,2), (5,-3,3)], region-B, material tissue-C (ρ=1000)
  - body coupon-body-A owns {cell-na1, cell-na2}; authored frame: rotation
    Rz(90°)=[[0,-1,0],[1,0,0],[0,0,1]], origin (0,0,0), frame id frame-A.
  - body coupon-body-B owns {cell-nb1}; authored frame: identity rotation,
    origin (5,-3,2), frame id frame-B.
- **Coupon U** (U2 unit conversion): identical to Coupon N except every
  coordinate value is multiplied by 100 (cm-authored) and both frames'
  `scale_to_m` = 0.01. Physically the same two bodies as Coupon N.
- **Coupon S(s)** for s ∈ {0.5, 2.0, 10.0}: identical to Coupon N except the
  two frames' `scale_to_m` = s (same numeric coordinates).
- **Coupon R** (U6): identical physics to Coupon N under: vertex-ID bijection
  (a0→w03, a1→w11, a2→w07, a3→w05, b0→w02, b1→w10, b2→w06, b3→w00, c0→w01,
  c1→w09, c2→w08, c3→w04 where a*=cell-na1, b*=cell-na2, c*=cell-nb1
  vertices in listed order), vertex rows in reverse order, cell rows in
  reverse order, cell IDs renamed cell-na1→cell-rz9, cell-na2→cell-ra0,
  cell-nb1→cell-rc5 (this flips the within-body-A sorted integration order
  [na1,na2]→[ra0,rz9] i.e. na2 before na1), and each cell's vertex_ids
  permuted by the even permutation [v0,v1,v2,v3]→[v1,v0,v3,v2]. Regions,
  materials, ownership, frames (same numeric transforms), mass_authority
  unchanged.
- **Coupon B** (U7 blocked): Coupon N with tissue-B's density_kg_m3,
  density_source, conditions set to null (the pinned missing-density
  mechanism).
- **Coupon G** (U7 refused, unknown group cell): Coupon N with a third body
  group coupon-body-ghost referencing cell id "cell-ghost" absent from the
  partition.
- **Coupon F** (U7 refused, bad frame): Coupon N with coupon-body-A's frame
  rotation replaced by [[0,-1,0],[1,1,0],[0,0,1]] (non-orthonormal).
- **Coupon C** (U3 cube): unit cube [0,1]³, Kuhn 6-tet split, vertices
  000,001,010,011,100,101,110,111 (coordinates (x,y,z)·1.0):
  - t1 (cube-t1): [000,100,110,111]; t2: [000,100,101,111]; t3: [000,010,110,111];
    t4: [000,010,011,111]; t5: [000,001,101,111]; t6: [000,001,011,111];
    each ρ: region-A t1,t3 → tissue-CA ρ=3; region-B t2,t4 → tissue-CB ρ=4;
    region-C t5,t6 → tissue-CC ρ=5.
  - bodies: cube-body-A {t1,t3}, cube-body-B {t2,t4}, cube-body-C {t5,t6},
    all identity frames, origin (0,0,0).
- **Coupon L** (U4 large coordinates): single tet [(1000000,-2000000,3000000),
  (1000001,-2000000,3000000), (1000000,-1999999,3000000),
  (1000000,-2000000,3000001)], ρ=1.25 (exact 5/4), identity frame.
- **Coupon D** (U4 near-degenerate sliver): single tet [(0,0,0), (1,0,0),
  (0,1,0), (0.25, 0.5, 2**-20)], ρ=6, identity frame. Normalized determinant
  ≈ 9.5e-7 ≫ 64·eps ≈ 1.42e-14 (admissible), aspect ratio ≈ 4.7e6.
- **Coupon X** (U4 extreme density ratio): one body, two cells:
  cell-xa = Coupon N cell-na1 geometry with ρ = 1e-6 (exact 1/1000000);
  cell-xb = Coupon N cell-na2 geometry with ρ = 1e9 (exact 10**9);
  same region/material per cell under one region and one body, identity frame.

## Frozen oracle (authored after this freeze, exactly as specified here)

`work/oracle/b02_oracle.py`: pure stdlib (`fractions`, `math`, `json`).
Exact rational tetrahedral integrals via the reference-simplex map: for
vertices p0..p3 and density ρ, V = det/6; m = ρV; centroid = (Σpᵢ)/4; exact
∫xᵢxⱼ dV by monomial expansion under the affine map from the reference
simplex (reference-simplex monomial integral a!b!c!/(a+b+c+3)!); inertia
about COM = trace(S)·Id − S with S the exact central second moment. The
oracle imports nothing from the frozen tree and shares no code with it.
Densities entered as exact Fractions (12, 7, 1000, 5/4, 6, 1/1000000, 10**9,
3, 4, 5); coordinates as exact Fractions of the values above (2**-20 exact;
0.25, 0.5 exact).

## Frozen hand-derived literals (checked against the oracle, then the exporter)

- Coupon N: V(na1)=1/6, m(na1)=2 kg, centroid (1/4,1/4,1/4); V(na2)=1/2,
  m(na2)=7/2 kg, centroid (3/4,1/2,1/2); m(body-A)=11/2 kg, COM_domain(A)=
  (25/44, 9/22, 9/22); V(nb1)=1/6, m(body-B)=500/3 kg, COM_domain(B)=
  (21/4, −11/4, 9/4). COM_body(A) = Rz(90°)ᵀ·COM_domain(A);
  COM_body(B) = (1/4, 1/4, 1/4).
- Coupon C: per-region volume 1/3; masses 1, 4/3, 5/3 kg; whole-partition
  mass 4 kg; 12 boundary faces each area 1/2 (total 6); interior faces 6,
  each area √2/2; emitted cross-region interface rows exactly 4: two A-B
  (sum √2), two B-C (sum √2); no A-C row; all four interface faces contain
  vertex 000 and their region endpoints span {A,B,C} (3 regions meet).
- Coupon D: V = 2**-20/6, m = 2**-20 kg exactly.
- Coupon X: m_xa = 1/600000 kg, m_xb = 5e8 kg, both finite; COM ≈ cell-xb's
  centroid (dominant mass).
- Coupon L: V = 1/6, m = 5/24 kg; COM = base + (1/4,1/4,1/4).

## Frozen predictions (all judged against frozen tolerances; no mid-run edits)

Tolerances: REL(a,e) = |a−e|/max(1e-300,|e|) unless |e| < 1 then |a−e| absolute;
ABS tol as stated. Comparison tolerance class **T1 = 1e-12** (relative where
|expected| ≥ 1, else absolute 1e-12) for unit-scale quantities; **T2 = 1e-9**
relative (inertia) / 1e-9 absolute (COM components) for the large-coordinate
coupon L, justified by |values| up to ~3e13 and float64 accumulation over the
exporter's einsum/sum reductions (eps≈2.2e-16; budget ≈ 4·10³ × eps·κ).
Fixtures are labeled fixtures everywhere; fixture PASS is not runtime
acceptance.

- **P-U2 (scale path, unit conversion).** Exporter runs on Coupon U exit 0
  with export_status "complete" and both bodies exported. Against Coupon N at
  s=1: per-body mass equal within T1; domain-frame COM and body-frame COM
  equal within T1; every inertia-tensor entry equal within T1; volume equal
  within T1. (This exercises `scale_to_m != 1.0` on the exporter input path,
  closing the boundary B01 recorded.) Any deviation beyond T1 or any
  non-complete status fires F-B02-1.
- **P-U5 (scale covariance sweep).** For s ∈ {0.5, 2.0, 10.0}: m(body,s) =
  s³·m(body,1) within T1; volume(body,s) = s³·volume(body,1) within T1;
  every entry of inertia_about_com (body frame) satisfies I(s) = s⁵·I(1)
  within T1; COM_body(A)(s) = s·COM_body(A)(1) within T1 (origin 0);
  COM_body(B)(s) = s·(1/4,1/4,1/4) − (0,0,0) evaluated via the frame
  equation = s·COM_domain − origin, compared within T1 to the reported
  value; units and frame-invariant flags unchanged; export_status complete.
  Any violation fires F-B02-2.
- **P-U2S (invalid scale statuses).** scale_to_m = 0.0 and = −1.0 yield
  admission reason "bad_scale"; a coordinate_frame missing scale_to_m yields
  admission reason "bad_schema"; in all three cases the export report has
  export_status "blocked", admission_status "refused", every body's
  mass_properties None, and CLI exit code 1. Any other status/reason fires
  F-B02-3.
- **P-U6 (reorder/renumber invariance).** Coupon R vs Coupon N: identical
  export_status, reason_codes, unassigned_cell_ids; identical owned_cell_ids
  sets; every mass_properties number equal within T1; the admission
  `supplied_geometry_signature` values are exactly equal (string equality);
  input_hashes.manifest_sha256/partition_sha256/body_groups_sha256 DIFFER
  between the two (arrays reordered — canonical JSON preserves array order)
  and admission_report_sha256 MAY differ; the two raw report bytes are not
  byte-identical. If any mass-property deviates beyond T1, signatures
  differ, or the identity fields are equal, fires F-B02-4.
- **P-U7 (reader status behavior).** (a) Coupon B export: status "blocked",
  admission_status "not_admitted", body-A and body-B mass_properties None;
  body-A's blocking rows name cell-na2 with status "missing_density"
  (body-A owns cell-na2), body-B (cell-nb1 resolved) carries no blocking
  rows; the pinned reader summarizes the report with exit 0, one body entry
  per group, mass_properties None for both. (b) Coupon G export: export_status "refused", reason
  "unknown_group_cell_id", exit code 1; reader summarizes with exit 0 and
  status "refused". (c) Coupon F export: export_status "refused", reason
  "invalid_authored_frame", admission_status "not_evaluated"; reader exit 0.
  (d) Tamper control: injecting mass_properties into a "blocked" body group
  of Coupon B's report makes the reader exit 2 with reason
  "blocked_group_has_mass". (e) A report whose export_status is "exploded"
  makes the reader exit 2 with reason "bad_export_status". Any deviation
  fires F-B02-5.
- **P-U3 (multi-face interfaces).** On Coupon C: admission interface rows =
  exactly 4, each with area within T1 of √2/2; the two rows with region pair
  {A,B} sum to within T1 of √2; the two rows with region pair {B,C} sum to
  within T1 of √2; no row involves region pair {A,C}; the set of regions
  referenced by rows whose face_vertex_ids contain vertex 000 is exactly
  {A,B,C}; boundary rows = 12 each within T1 of 1/2; exporter masses per
  body within T1 of {1, 4/3, 5/3} and their sum within T1 of 4 (no interface
  mass contributed). Any deviation fires F-B02-6.
- **P-U4 (numerical stress).** Coupon L: exporter completes; every
  mass-property field within T2 of the exact oracle (REL for inertia;
  ABS 1e-9 for COM components; mass/volume T1). Coupon D: completes; mass
  within T1 of 2**-20; volume within T1 of 2**-20/6; inertia entries within
  T1 of the oracle's exact values. Coupon X: completes; m_xa within T1 of
  1/600000; m_xb within T1 of 5e8; total within T1 of 500000000.0000001666…;
  all reported values finite; no NaN/overflow anywhere in any report. Any
  deviation, refusal, or non-finite output fires F-B02-7.
- **P-OR (oracle self-consistency).** The exact oracle reproduces every
  hand-derived literal in this preregistration exactly (Fraction equality
  before float conversion). Any mismatch fires F-B02-8 (the preregistration
  itself would be wrong and must be reported, not silently fixed).
- **P-NC (negative control, must fire).** Perturbing one oracle expectation
  by +1e-6 relative (mass of body-A in Coupon N) must be REJECTED by the
  suite's comparator; if the perturbed value passes, every PASS verdict in
  this attempt is void and F-B02-9 fires.
- **P-DET (determinism).** The diagnostics generator run twice produces
  byte-identical output; two exporter runs on the same coupon are
  byte-identical. Any difference fires F-B02-10.
- **P-HASH (distinct evidence classes).** The diagnostics manifest labels
  raw working-tree sha256, LF-canonical sha256, and git blob OID separately
  for every evidence artifact; at least one artifact lawfully exhibits
  raw ≠ LF-canonical with a stable blob OID (the committed LF file vs a
  CRLF-materialized copy); every hash quoted in the final receipt names its
  class. A conflated or missing identity fires F-B02-11.
- **P-COUNT (coverage counts).** The unittest suite runs exactly 11 tests
  (unit-conversion; scale sweep; invalid-scale statuses; reorder invariance;
  blocked reader; refused reader unknown-cell; refused reader bad-frame;
  tamper control; bad-status control; negative control; determinism) —
  "Ran 11 tests … OK". Field-level comparisons across suite + diagnostics
  are individually asserted and total ≥ 500; the exact count is recorded in
  the diagnostics JSON and must match between determinism runs. Any other
  count fires F-B02-12.
- **P-BOUND (applicability boundary, recorded not claimed).** The exporter
  accepts only a uniform scalar scale_to_m (schema field, single number);
  anisotropic scaling enters only as authored geometry integrated per cell
  (contract C04 wording); U8/U9/U10 have no consumer/runtime in this card
  and are recorded UNRESOLVED; no runtime, anatomical, or dynamics claim is
  made anywhere; every report keeps validation_only true, production_wired
  false, dynamics_readiness_claimed false. A claim outside this boundary
  fires F-B02-13.

## Frozen falsifiers

| id | fires when |
|---|---|
| F-B02-1 | Coupon U vs N deviation > T1, or Coupon U export not complete |
| F-B02-2 | any sweep relation (m s³ / I s⁵ / volume s³ / COM frame law) violates T1 |
| F-B02-3 | invalid-scale trio does not produce blocked+refused with the named admission reasons and exit 1 |
| F-B02-4 | any Coupon R mass-property deviates > T1, geometry signatures differ, or identity fields fail to differ |
| F-B02-5 | any U7 status/reader outcome differs from (a)–(e), including reader exit codes and named reasons |
| F-B02-6 | any Coupon C interface/boundary/mass literal deviates > T1 |
| F-B02-7 | Coupon L/D/X deviate beyond T2/T1, refuse, or emit any non-finite value |
| F-B02-8 | oracle disagrees with any hand-derived literal (prereg error — report, do not edit) |
| F-B02-9 | NEGATIVE CONTROL fails to fire (perturbed expectation accepted) |
| F-B02-10 | determinism breaks (non-identical reruns) |
| F-B02-11 | evidence-class identities conflated, missing, or mislabeled |
| F-B02-12 | suite count ≠ 11, or field-comparison total < 500, or counts differ between determinism runs |
| F-B02-13 | any claim or output outside the P-BOUND applicability boundary |
| F-B02-14 | any probe cannot run as pinned (missing module/fixture identity) — record and stop, no substitution |

Stop rule: any falsifier firing stops the attempt's claim; the fired
falsifier, its output, and all completed probes are preserved verbatim. No
tolerance, fixture, or prediction is edited after this freeze.

## Frozen probes (exact commands; all CPU, all offline)

- extraction: `git cat-file blob 1af0bbde:<path>` for the pinned exporter,
  reader, admission, compiler, checks, schemas, example fixtures, and matter
  docs into `work/frozen/1af0bbde/`, with a provenance manifest recording
  commit, path, blob OID, and raw sha256 per extract;
- authoring (after this freeze, exactly as specified above): oracle,
  fixtures, `work/b02_checks.py`, `work/diagnostics/b02_diagnostics.py`;
- suite: `python -B work/b02_checks.py` from the extraction root on sys.path
  (no installation, no package changes to the pinned tree);
- diagnostics: `python -B work/diagnostics/b02_diagnostics.py` twice,
  byte-compare;
- schema validation of each "complete" export report against the pinned
  shipped body-export schema (jsonschema, fixture-labeled);
- identity: raw/LF-canonical/blob-OID manifest over this contribution's
  artifacts.

Freeze complete. Implementation and execution may now begin.
