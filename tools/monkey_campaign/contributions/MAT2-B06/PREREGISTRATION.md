# PREREGISTRATION — MAT2-B06 "Re-run real assembly readiness without substitutions"

Frozen BEFORE any implementation or measurement. This file is committed ALONE
(separate-first); the evaluator refuses any document whose
`preregistration_sha256` does not match these live bytes, so the freeze is
git-provable and hash-bound.

- Card MAT2-B06 (planning id B06), slot 1, branch-1, attempt
  `87c14d5c21ef4468962337301e0c3702`, arrival
  `arrival-b431f1fbeb554366b78bdf06dea80ba8`.
- Criteria sha256 `6c3bb5fb51aa87adb261e6a07f444c78cae28910b2327fe88f2b79c6da80802b`
  (startup assignment == registry `kanban.cards[MAT2-B06].criteria_sha256`,
  read read-only from `E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3`).
- done_when (verbatim): "All mass/ownership/frame/port requirements evaluated,
  with remaining gaps explicit".
- Profile: `anatomy` (`visible_static`), numerical_evidence_required; capture
  with task_id SHORT FORM "B06".
- Sealed base: slot branch fast-forwarded `c525b82c7c3ce0128565424764293a3c85811ab3`
  -> `051123cf1d549479c765e4f3e112ddddbedcf752` (ancestor check passed; sealed
  tip carries B03/B04/A06/A07/B05). Remote
  `git@github.com-fleetdeploy:GhostDragonAlpha/Chimera.git` reported only —
  no pushes, no PRs (publication is lead-serialized).

## 1. Statement

This card RE-EVALUATES assembly readiness against the ACTUAL sealed records of
the dependency cards. It is a read-only evaluation: no sealed record is edited,
no stand-in is substituted, nothing is fitted, no gap is silently promoted.
Every requirement in the four domains (mass / ownership / frame / port) is
either (a) `evaluated_satisfied_at_scope` with its pinned evidence re-read and
re-verified bitwise from the sealed bytes, or (b) `evaluated_gap` naming the
missing evidence and the authorizing rank (A07 vocabulary: a recorded lead or
captain decision), or (c) a `measured_screen` — new evaluation enabled by the
transcribed Cheng tables, which can never promote a status by itself.

NEW FUEL (license-internal, cited by file+sha256, read-only, never committed to
this repository): the REALITY-grade transcribed Cheng (1999) tables at
`E:/ChimeraWork/research-data/20260929/cheng_tables/` (21-muscle morphometry +
segment inertials for M. mulatta / M. fascicularis; transcription receipts
pin the source PDF sha256 `9f79e16b4397eef08d5e7f3a2f2eac4d8a827cb0817f9644e26e560f0f0f0eae`).
For each gap the evaluator records honestly whether the measured data CLOSES
the gap, PARTIALLY INFORMS it, is INADMISSIBLE (species/stage law), or DOES
NOT APPLY / DOES NOT CLOSE. Verdicts never alter sealed statuses.

## 2. Sealed input pins (raw committed bytes at the sealed tip; the evaluator
re-reads them via `git cat-file` at the frozen commit and refuses any mismatch)

| role | path at sealed tip | blob sha256 |
|---|---|---|
| b03_material | tools/monkey_campaign/contributions/MAT2-B03/material_volume_input.json | `6e8033f26c823f410eb5beb8fdaaefd4c0c37db61327a86221e087bc832b9ddc` |
| b03_matter_library | tools/monkey_campaign/contributions/MAT2-B03/data/matter_library_1af0bbde.json | `de10200fb87bf48c3cc80d5e223805f02e27df115b91186f42f28064a64054ed` |
| b04_frames | tools/monkey_campaign/contributions/MAT2-B04/frame_forest.json | `156ef55722e1ecda3238f3733131eb707f209cb93531d0e133227b00ebba8203` |
| a06_ownership | tools/monkey_campaign/contributions/MAT2-A06/attachment_ownership.json | `f1f0430772258e8449fc354841becf2f1869783399e63f3f145565b8d0b1041c` |
| a07_resolution | tools/monkey_campaign/contributions/MAT2-A07/placement_resolution.json | `cd596d7c21fa81a4c2632e13b63ba26e62da51d44eca2355147fd5dff1587490` |
| b05_ports | tools/monkey_campaign/contributions/MAT2-B05/mechanical_port_requirements.json | `ef69ee740262cc5783e763517e4d27e0306f31d059b8273bb125486ad7647f3d` |
| dw04_mass_matrix | tools/monkey_campaign/contributions/D-W04-MASS-20260924/mass_matrix.json | pinned at runtime by re-hash of the sealed blob; recorded in the emitted document |
| dw04_receipt | tools/monkey_campaign/contributions/D-W04-MASS-20260924/receipt.json | same rule |

## Amendment A1 (recorded before any implementation commit)

The two "pinned at runtime" rows above are replaced by exact pins (blob sha256
at the sealed tip, computed the same way as every other row):

| role | blob sha256 |
|---|---|
| dw04_mass_matrix | `6a32229438f59158a0995b6b90043639e8b103eedf2d09243502faaa9a68ff39` |
| dw04_receipt | `f37fb0cc7bf8ccdf1572fc31ba909ef9b0ae8eff043613a13b9e4c4648cbf445` |

Everything else in this preregistration is unchanged.

## 3. Cheng source pins (live host files; sha256 verified at every run; the
evaluator refuses `cheng_source_unavailable` / `cheng_source_pin_mismatch`)

| role | file | sha256 |
|---|---|---|
| cheng_m2_3_mulatta_morphometry | E:/ChimeraWork/research-data/20260929/cheng_tables/M2-3_mulatta_morphometry.csv | `16ca8bcd9be48b3766125801eb05a8f4f10b446b4caed76d9fddeb2e45df71fa` |
| cheng_m2_5_fascicularis_morphometry | E:/ChimeraWork/research-data/20260929/cheng_tables/M2-5_fascicularis_morphometry.csv | `9469449f8735df84a163d364a67402d127ca8ac54a402595ce4cebb6d16cf148` |
| cheng_m2_6_mulatta_inertials | E:/ChimeraWork/research-data/20260929/cheng_tables/M2-6_mulatta_inertials.csv | `1948a2d8399b5253461c6ed70eed87ea38c5df4083b75437e1e3dbd1a4ce93f3` |
| cheng_m2_7_fascicularis_inertials | E:/ChimeraWork/research-data/20260929/cheng_tables/M2-7_fascicularis_inertials.csv | `d1d601feaf61b033bdbccf8509be946d0e1884fec62388c8630287703fc63133` |
| cheng_m2_8_regressions | E:/ChimeraWork/research-data/20260929/cheng_tables/M2-8_regressions.csv | `b185ee8e98b6e663defed0abd4d004fec053eb6417e027c54801070cd894ec22` |
| cheng_readme | E:/ChimeraWork/research-data/20260929/cheng_tables/README_cheng_tables.md | `7ec44aa1031df22f0263a023aade9cc0c6c572ce268d14934a6ef49a61900ca3` |
| cheng_receipt | E:/ChimeraWork/research-data/20260929/cheng_tables/TRANSCRIPTION_RECEIPT.md | `a3031b236dc368fb8f59f571e39666fc0ed504f383fff9b34d26c36817f2e568` |

License: UNVERIFIED per the transcription README (internal use only; no
redistribution). The tables are therefore READ from their host location and
cited by file+sha256; only evaluation RESULTS (cited values with cell
coordinates) enter the emitted document.

## 4. Frozen requirement rows (the complete gate; nothing else may gate)

Lawful gate statuses: `evaluated_satisfied_at_scope`, `evaluated_gap`.
Screen status: `measured_screen` (never gates). Any other value is refused
(`unlawful_status_refused`).

MASS
- R-MASS-01 gate: counted bone mass inventory for the five closed arm-bone
  regions (C02). Expect SATISFIED at counted-bone scope: sealed B03
  `provenance.counted_set.counted_total_kg == 0.0447023937544344` and equals
  the sum of the five counted region masses (recomputed).
- R-MASS-02 gate: measured bone material density support for the counted
  inventory (B03 density provenance class is "researched"; conditions absent).
  Expect GAP; missing evidence: a lead-admitted measured bone material density
  with stated temperature/moisture/strain-rate conditions (MAT-03 admission).
  Cheng verdict: `inadmissible_to_close` (the Cheng tables carry segment/tissue
  masses and inertials; no material density column exists in any of the five).
- R-MASS-03 gate: counted, validated carried-load segment weights for the
  ports (B05 `weights` blocked side). Expect GAP; B05 missing_evidence carried
  verbatim. Cheng verdict: `partially_informs` (measured M. mulatta segment
  mass bands + body-weight regressions can SCREEN any future counted mass;
  they are not a counted mass of this assembly: different subjects, n=6,
  segment conventions differ, no specimen binding).
- R-MASS-04 gate: transported-assembly accounting (Buffy 02: 17.039978509953905
  kg all_transported, counted 0.0, readiness false). Expect GAP; missing
  evidence: a recorded ownership decision decomposing the transported claims
  into counted, validated masses (rank: lead). Cheng verdict:
  `partially_informs` (scale screens below; no measured table can own or
  decompose the claims).

OWNERSHIP
- R-OWN-01 gate: explicit owner+role for every grasp-relevant endpoint,
  attachment, waypoint record in the ownership registry. Expect SATISFIED at
  registry scope (sealed A06 counts 48 paths / 26 attachments / 22 waypoints /
  6 grasp endpoints; every record re-read to carry owner+role).
- R-OWN-02 gate: assembly mapping for the 14 pending hand-body path records.
  Expect GAP (A07 `recorded_assembly_mapping_decision`; rank: recorded lead or
  captain decision). Cheng verdict: `does_not_apply` (a measurement cannot
  authorize a mapping decision).
- R-OWN-03 gate: forearm assembly correspondence (31 forearm records
  `explicitly_unresolved`). Expect GAP (same rank law). Cheng:
  `does_not_apply`.
- R-OWN-04 gate: 8 measured-outside placements (4 insertions + 4 waypoints,
  exact per-axis excesses). Expect GAP (`fitting_not_authorized`; new fitting
  requires separate authorization; none authorized). Cheng: `does_not_apply`.
- R-OWN-05 gate: C17 finite attachment mechanics inputs for the 26
  attachments. Expect GAP (`inputs_unavailable_in_pinned_sources`). Cheng:
  `does_not_close` (morphometry is muscle-belly level; no patch area / areal
  stiffness / couple resistance at any attachment interface).

FRAME
- R-FRM-01 gate: authored assembly frame forest composed from pinned source
  chains. Expect SATISFIED at authored-placement scope (sealed B04: four
  roots; transforms recomposed from the embedded chains inside the evaluator).
- R-FRM-02 gate: accepted ulna-edge correspondence + authorized
  packet-to-forest binding (B05 `anchor_frame_id` blocked). Expect GAP
  (B05 missing_evidence carried verbatim; rank: recorded lead/architect
  decision). Cheng: `does_not_apply` (the tables carry percentages only — no
  absolute segment lengths, no frame correspondence).
- R-FRM-03 gate: component/bond admission ledger (4 disconnected components,
  9 unresolved bodies, counted mass 0.0, no cross-component bond). Expect GAP
  carried explicitly (thorax/ulna/ulna_l admission-unresolved). Cheng:
  `does_not_apply`.

PORT
- R-PRT-01 gate: mechanical qualification of the eight real tendon ports.
  Expect GAP: 0 of 8 qualified, 8 remaining blocked (B05 counts + per-port
  input statuses re-read byte-exact; qualification_rule re-read and enforced).
  Cheng verdict: `does_not_close` for all eight (the missing evidence is
  attachment-site patch/stiffness/couple/frame, not muscle morphometry);
  honesty addendum: PT (pronator teres) has NO row in the Cheng morphometry
  tables, so even muscle-level data is incomplete for this port set.
- R-PRT-02 gate: declared pressure limits carried from the pinned M03 source.
  Expect SATISFIED at declared scope (status `declared`; declared is NOT
  qualified and never flips R-PRT-01).

SCREENS (new evaluations; never gate)
- S-MASS-05: excluded osim segment claims vs measured M. mulatta bands
  (M2-6): humerus claim 0.203 kg vs 0.294±0.119; radius+ulna 0.154 vs
  0.194±0.078; hand 0.049 vs 0.057±0.011 (kg). Predict INSIDE 1 SD for all
  three; the claims stay EXCLUDED regardless.
- S-MASS-06: implied body weight of the arm claims via M2-8 regressions
  (m g/kg, b g): upper arm (203-23.0)/34.4; forearm (154-17.5)/22.4; hand
  (49-35.4)/2.77. Predict all three in [4.0, 7.0] kg. And the %BW screen at
  the transported total: 3.8% x 17039.978509953905 g = ~647.5 g expected
  upper arm vs the 203 g claim — predict ratio > 2 (the transported total is
  not the body mass of the arm claims; determinate internal inconsistency
  screen, not an ownership verdict).
- S-MASS-07: inertia screen, eigen-free: trace of the sealed B03 aggregate
  bone inertia (sum of the 3x3 diagonal, exact invariant) vs the sum of
  Cheng M2-6 Icg mean values (upper arm + forearm + hand) converted
  1 g·cm^2 = 1e-7 kg·m^2. Predict the bone-only trace inside
  [0.3, 1.5] x the measured whole-segment Icg sum (bone-only vs
  whole-segment are different quantities; same order of magnitude is the
  claim, equality is NOT claimed and cannot close B03's own cross-method
  verification, which stands at its own scope).
- S-MASS-08: species law: the campaign animal context is rhesus (M. mulatta;
  Turnquist & Kessler adult-female band book context per the sealed D-W04
  record). M. fascicularis tables (M2-5, M2-7) are INADMISSIBLE to close any
  requirement on this assembly (species mismatch), retained only as
  cross-species reference; M. mulatta tables are admissible as screening
  references only (species match; subject/stage mismatch remains).
- S-PORT-09: port muscle coverage in the Cheng morphometry tables: predict
  Biceps long / Biceps short / Brachioradialis rows EXIST and Pronator teres
  is ABSENT in BOTH M2-3 and M2-5; both tables carry exactly 21 muscle rows.

## 5. Frozen counts of the emitted document

- requirement_gate rows: 14 (satisfied 4: R-MASS-01, R-OWN-01, R-FRM-01,
  R-PRT-02; gap 10: R-MASS-02, R-MASS-03, R-MASS-04, R-OWN-02, R-OWN-03,
  R-OWN-04, R-OWN-05, R-FRM-02, R-FRM-03, R-PRT-01).
- measured_screen rows: 5 (S-MASS-05..S-MASS-08, S-PORT-09).
- assembly_readiness: FALSE (any gap row forces false; the carried card
  observation is honored verbatim).
- gaps_by_domain: mass 3, ownership 4, frame 2, port 1.

## 6. Readiness gate rule (frozen)

`assembly_readiness` is true ONLY IF every requirement_gate row is
`evaluated_satisfied_at_scope` AND every satisfied row's evidence pin
re-verifies bitwise against the sealed bytes. Screens never gate; declared
status never qualifies; authored requirements never qualify a port; no
substituted stand-in, no silent promotion, no fitting.

## 7. Frozen falsifiers (each: tamper a COPY, watch the named refusal, discard;
the committed artifact must be untouched and re-verified afterwards)

- F1 `unbound_input_refused` — a stand-in "measured segment mass" document
  (unbound JSON claiming a counted carried-load mass) is placed in the
  evaluator's input set. The evaluator must refuse: inputs are only the
  sealed pins + the pinned Cheng files; nothing else may close a gap.
- F2 `satisfied_requires_pinned_evidence` — a copy of the emitted document
  with R-OWN-02 flipped to `evaluated_satisfied_at_scope` (evidence block
  absent). The validator must refuse.
- F3 `satisfied_requires_pinned_evidence` (pin-broken arm) — a satisfied row
  whose recorded artifact sha256 disagrees with the sealed pin.
- F4 `cheng_source_pin_mismatch` — a tampered copy of a pinned Cheng CSV.
- F5 `unlawful_status_refused` — a row status outside the frozen vocabulary.
- F6 `sealed_pin_mismatch` — a tampered copy of a sealed dependency document
  (e.g., one B05 port flipped to qualified) in the evaluator's input set.

## 8. Verification plan (exact-head; all commands recorded with exit codes)

1. `python -B assembly_readiness.py derive` -> emits `assembly_readiness.json`
   (canonical bytes, `newline="\n"`) + derivation receipt; all frozen
   predictions re-checked.
2. `python -B assembly_readiness.py verify` -> re-derives from the pins and
   compares byte-identical; re-runs the falsifier arms on copies under
   `work/`; writes `work/runs/verification_receipt.json`.
3. `python -B test_assembly_readiness.py` -> unittest probes P1-P9 + F1-F6.
4. `python -B lint_report_numbers.py --selftest` -> every numeric literal in
   report.md traceable to a bound artifact (B05 pattern adapted).
5. Capture: `python -B capture_readiness.py` -> visible_static sheet, task_id
   "B06", profile read read-only from the registry; manifest validated with
   the UNMODIFIED source-head `visual_capture.validate_manifest`; every
   view's state_binding = sha256(assembly_readiness.json).

## 9. Honest limitations (frozen)

- The Cheng values enter as CITED measurement results with file+sha256+cell
  provenance; the license is UNVERIFIED (internal use only) — no table bytes
  are committed to this repository.
- Screens compare different quantities on purpose-labeled terms (bone-only vs
  whole-segment; claims vs measured bands; n=6 subjects, no specimen binding);
  a screen can flag inconsistency or plausibility, never ownership.
- No runtime solver, no native-engine run, no new fitting: the visual capture
  is a 2D orthographic structured-records sheet of the readiness state
  (declared as such), not a 3D render.
- This card evaluates readiness; it does NOT rewrite sealed history, does NOT
  alter any sealed record, and its FALSE readiness verdict is the expected
  honest outcome, not a failure of the card.
