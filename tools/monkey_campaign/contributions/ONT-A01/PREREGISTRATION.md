# PREREGISTRATION — ONT-A01 (attempt fb552e4136ef4bfdaaa93686fb063e78)

Frozen 2026-09-26, BEFORE any probe of this attempt ran. Arrival
`arrival-1b915fe5e1a44a1383a63baf10ce743f`. Criteria sha256
`2bcf59fa0b786b009b30711334e38fe374d9a2a2bdefdba9566a4018c4a9c775`.

## done_when (exact card clause)

> Independent anatomical evidence determines roll sign or records ambiguity

Kind `measurement`, verification profile `anatomy` (`visible_static`),
`numerical_evidence_required: true`. Authorized diagnostic measurement; NOT a
production mapping. Subject of the claim is evidence/records about anatomy, not a
runtime behavior claim about the playable application.

## Statement

The U-STR ulna roll sign is determined (not ambiguous) by independent anatomical
evidence: in the source rest frame the ulna volar side is +x; in the target world
frame volar/anterior is +z; the correct construction maps source volar +x onto
target section azimuth +90 deg (world +z), and the 180 deg flip (source volar onto
target dorsal −z/posterior) is refuted; witness law `az_target = az_source + 90 deg`,
unanimous over the declared roll candidates (ECU-P2, ANC-P2, TRIlat-P5).

This statement is ALREADY MADE by prior verified work — reconciliation finding, not
a new claim by this card: audit `O1_ulna_orientation` integrated at play-lane commit
`c3255f74` (branch `forearm-package-20260924`, later lanes carry it: `f1023853`
"roll derived from O1's law"). This attempt's task-owned work is to RE-VERIFY the
pinned evidence from the pinned inputs, bind it into this campaign lane as a
source-bound qualification receipt, inventory what cannot independently re-decide
it, and produce the anatomy-profile visual capture. No new anatomy, no new
constants, no production mapping.

## Reconciliation (read-only, completed before freezing)

- ONT-P02 lineage map (`8c7ed8c2`, tools/monkey_campaign/contributions/ONT-P02):
  forearm/paddle assets KEPT_SEPARATE; U-STR = architect's sole PROVISIONAL ulna
  candidate; CT monkey = render-lineage SOURCE_ASSET; training body 10.038 kg is
  separate. A01 inherits P02's identities; this card must not fuse lineages.
- O1 audit @ `c3255f74`: receipts `o1_ulna_mesh_probe.json`,
  `o1_source_split.json`, `o1_target_sections_directed.json`,
  `o1_target_olecranon.json`, `o1_combine_sign.json`; preregistered in its own
  `brief.md`; verdicts quoted in its `report.md`.
- CT bone identification v3 (`tools/science_funnel/data/morphosource_ct/
  bone_identification_v3.json` @ `33e7a444`): forearm bones labeled only
  `forearm_class`; transfer_rules `side_rule`: "sides never assigned (the curl
  jumbles them)". The CT dataset therefore CANNOT yet independently re-decide
  ulna-vs-radius, let alone volar side. Recorded as an explicit unresolved
  inventory item; NOT resolved by this card (that would be invented anatomy).
- Membrane ontology (`tools/membrane_ontology/ontology.json` rev 2): `bones`
  (parent `skeleton`) — "Individual bone membership must be imported from a pinned
  source and anatomically resolved" — this evidence feeds that gap for one bone,
  evidence-only; membranes stay `unresolved`/`not_qualified`.
- Input identities verified on disk BEFORE freezing: `monkey_birth.bin`
  sha256 550a5b3e…ABFA3C, `monkey_joints.bin` sha256 74b3ab04…50C1662 (both equal
  O1's frozen EXPECT_SHA), vendor `ulna.stl` 19,884 bytes (binary STL, 396 tris).

## Frozen predictions (probe P = re-measurement from pinned inputs)

P1 (source bone identity + volar label). Vendor `ulna.stl`, authored scale
(1, 1.2, 1), mm = mesh*1000 with authored unit m: the maximal −x feature of the
whole bone (the olecranon) has x = −28.32 mm ± 0.5; distal extreme y = −297.1 mm
± 0.5. Receipt-of-record: `o1_ulna_mesh_probe.json`.

P2 (target volar label, olecranon test). Exact triangle–plane sections of the
target mesh on the C3 forearm axis, directed radial profile, posterior sector
azimuth −90 ± 30 deg (world −z), anterior +90 ± 30 deg (world +z):
D(t) = max rho_post − max rho_ant at t = +6 mm = +3.29 mm ± 0.75; D > +2 mm for
every station t in [−2, +12] mm by steps of 2. Receipt-of-record:
`o1_target_sections_directed.json`.

P3 (sign law). From pinned `o1_source_split.json` volar azimuths and the pinned
C3-S2 witness azimuth −111.87 deg: every declared candidate satisfies
error_no_flip < error_flip; TRIlat-P5 error_no_flip = 0.15 deg ± 1.0; verdict
unanimous NO-FLIP; law `az_target = az_source + 90 deg (mod 360)`.
Receipt-of-record: `o1_combine_sign.json`.

Tolerances above are frozen now; bootstrap std of P2 (0.2–0.7 mm per station) is
the acknowledged noise floor. No tuning; a missed tolerance is reported as it
falls.

## Falsifier (decidable either way — this is the card's "or records ambiguity" arm)

F1: olecranon NOT the extreme −x feature (or |x_olecranon − (−28.32 mm)| > 0.5)
    → source volar = +x unsupported.
F2: D(+6) ≤ 0, or any t in [−2, +12] has D ≤ +2 → target volar = +z unsupported
    (an inverted or absent protrusion refutes the facing/volar identification).
F3: any candidate with error_flip < error_no_flip → the flip survives; sign NOT
    determined.
F4: any P1–P3 value outside its frozen tolerance → disagreement with the record;
    the attempt does NOT overrule the record — it RECORDS AMBIGUITY with both
    readings stated.
Outcome rule: if F1–F3 all avoid and P1–P3 hold → done_when satisfied as
"evidence determines roll sign". If any falsifier fires → done_when satisfied as
"records ambiguity", with the fired condition, both readings, and the exact
measured numbers written into the numerical receipt. Silent trimming, re-trying
with loosened tolerances, or dropping a dissenter is forbidden.

## Probes frozen before execution (profile anatomy / visible_static)

Numerical (CPU-only, deterministic, no GPU, no network): N1 = P1 mesh probe;
N2 = P2 directed sections (exact segment intersection, 5-deg bins); N3 = P3 sign
law re-combination; N4 = cross-check that my re-measured values and the pinned
receipt values are both written into the numerical receipt side by side.

Visual: ONE capture (single hashed PNG contact sheet, `capture_sha256`) with the
three declared profile views, each with diagnostic + clean pair (identical camera
and state binding per pair):
- V1 `whole-creature overview` — full target mesh (pack `monkey_birth.bin`), frame
  axes triad, forearm region boxed; layers: outer envelope, selected bones/joints,
  frame axes, stable 3D labels.
- V2 `local attachment close-up` — source ulna mesh (authored scale), six labeled
  sites (TRIlat-P5, ANC-P2, BRA-P4, BRA-P3, PT-P2, ECU-P2), volar/dorsal direction
  arrows; layers: selected bones/joints, muscle/tendon paths, attachment sites,
  frame axes, stable 3D labels.
- V3 `orthogonal side and oblique views` — source ulna, sampled trajectory of four
  bookmarks (anterior, posterior, left-lateral oblique, superior); layers:
  selected bones/joints, frame axes, stable 3D labels.
Cameras: orthographic, all profile camera_required_fields present, orientations as
unit quaternions (w,x,y,z, camera-to-frame) computed from the actual camera bases,
distances exact. Diagnostic rows declare occlusion_mode `xray` (overlay markers
are NOT occluded — honest); clean rows `depth_tested` (true per-pixel z-buffer,
below). Required_subject_ids per view ⊆ observed. All labels bound 1:1.

Renderer honesty label (frozen): rasterization is a numpy z-buffer software
rasterizer, CPU-only, deterministic, fixed seed/no randomness — NOT native engine
frames; the manifest carries
`render: {backend: "numpy-zbuffer-software-raster-cpu", native_engine_frames:
false}` and every receipt repeats it. The subject is a records/component claim
(anatomy evidence), so component evidence is the honest bar here; nothing in this
card claims a native application run.

## Integrity constraints honored

Zero writes in E:/PythonChimera or the play worktree; all writes inside the
attempt workspace; inputs read read-only from pinned paths/git objects; every
extracted reference file recorded with path + sha256; PYTHONDONTWRITEBYTECODE=1;
tests CPU-only.
