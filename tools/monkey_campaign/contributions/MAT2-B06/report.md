# MAT2-B06 report — re-run real assembly readiness without substitutions

Date 2026-09-29. Arrival `arrival-b431f1fbeb554366b78bdf06dea80ba8`, attempt
`87c14d5c21ef4468962337301e0c3702`, workspace
`E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-B06\87c14d5c21ef4468962337301e0c3702`,
slot branch `branch-1`. The prepared base `c525b82c7c3ce0128565424764293a3c85811ab3`
was stale (ancestor check passed) and was fast-forwarded to the sealed tip
`051123cf1d549479c765e4f3e112ddddbedcf752` (carrying B03/B04/A06/A07/B05)
BEFORE any edit. Sparse checkout of
`tools/monkey_campaign/contributions/MAT2-B06/`. Remote
`git@github.com-fleetdeploy:GhostDragonAlpha/Chimera.git` — REPORTED ONLY; no
pushes, no PRs (publication is lead-serialized). A different instance reviews
this work.

Preregistration was committed BEFORE any implementation: `78856821` (frozen
file ALONE) and `80e1642f` (Amendment A1: the exact D-W04 pins replaced the
runtime-rehash rows, still before implementation). Final preregistration
sha256 `729dd133d65c0458182c50c8ed1721e456fa5c177cc9d2a6fb9fdb1a871e9809`
(hash-bound in the emitted document; the validator refuses
`preregistration_pin_mismatch`).

## done_when execution (criteria sha256
6c3bb5fb51aa87adb261e6a07f444c78cae28910b2327fe88f2b79c6da80802b, verbatim in
the receipt; registry card criteria identical, read read-only from
`E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3`)

"All mass/ownership/frame/port requirements evaluated, with remaining gaps
explicit" — `assembly_readiness.json` (chimera.assembly_readiness.v1,
canonical sha256 `88fa5e2d599017f5c9bf69ac92d920f23334c221f4afe87ccdda235f1fab2c71`)
emits 14 requirement_gate rows and 5 measured_screen rows. EVERY requirement is
evaluated against the ACTUAL sealed records (raw committed bytes at the frozen
tip, re-read via `git cat-file` and sha-pinned); there are 4
`evaluated_satisfied_at_scope` rows and 10 `evaluated_gap` rows, each gap
naming its missing evidence and the authorizing rank (A07 vocabulary). The
readiness gate rule is frozen: readiness is true ONLY with zero gate gaps and
every satisfied pin re-verifying. Verdict: **assembly_readiness FALSE** — the
honest carried outcome ("Buffy 02 binds 9 claims but 17.039978509953905 kg
stays transported/not counted; readiness false"), recorded verbatim in the
document.

Satisfied rows (pinned evidence re-read bitwise): R-MASS-01 counted bone
inventory 0.0447023937544344 kg (B03 C02; region-mass sum recomputed equal);
R-OWN-01 registry owner+role completeness (48 path records / 26 attachments /
22 waypoints / 6 grasp endpoints, all re-read); R-FRM-01 four B04 root frames
recomposed from their embedded pinned chains (identity quats asserted, hop
shas = the pinned chimanoid raw sha); R-PRT-02 declared pressure limits
(declared is NOT a qualification and never flips the ports row).

Gap rows (named evidence + rank): R-MASS-02 measured bone material density
absent (researched class, no conditions; MAT-03 admission); R-MASS-03 counted,
validated carried-load segment weights absent (B05 missing-evidence carried
verbatim); R-MASS-04 the 17.039978509953905 kg transported claims stay
unde composed (counted 0.0; lead decision); R-OWN-02 pending assembly mapping;
R-OWN-03 forearm correspondence; R-OWN-04 measured-outside placements
(fitting not authorized); R-OWN-05 C17 mechanics inputs; R-FRM-02 bound port
frame (ulna-edge correspondence + packet-to-forest binding); R-FRM-03
component/bond admission ledger (4 components, 9 unresolved bodies, counted
mass 0.0); R-PRT-01 mechanical qualification: 8 of 8 ports remain blocked,
0 qualified.

## Without substitutions

The evaluator's input set is ONLY the 8 sealed pins (B03 document + matter
library extract, B04 forest, A06 registry, A07 resolution, B05 ports, D-W04
mass matrix + receipt — exact blob sha256s in the prereg and the document)
plus the 7 pinned Cheng host files. A substituted stand-in input is refused
by name (`unbound_input_refused`, F1); a gap flipped to satisfied without
evidence is refused (`satisfied_requires_pinned_evidence`, F2); a satisfied
row whose recorded value disagrees with the sealed bytes is refused (F3);
tampered sealed bytes are refused (`sealed_pin_mismatch`, F6). Carried
verbatim texts are re-checked against the sealed sources
(`carried_text_mismatch`).

## Cheng tables (new fuel) — honest verdicts, statuses untouched

The license-internal transcribed Cheng (1999) tables are cited by file+sha256
and READ from their host location (no table bytes committed; license
UNVERIFIED, internal use). Per-row verdicts never flip a sealed status:

- R-MASS-02 `inadmissible_to_close`: no material-density column exists in any
  Cheng table (segment/tissue masses and inertials only).
- R-MASS-03 `partially_informs`: measured M. mulatta bands (M2-6) + body-weight
  regressions (M2-8) can SCREEN a future counted mass; they are not a counted
  mass of this assembly (n=6 other subjects, differing segment conventions, no
  specimen binding).
- R-MASS-04 `partially_informs`: S-MASS-06 shows the transported total is NOT
  the body mass of the arm claims (screen below); measurement cannot own or
  decompose the claims.
- R-OWN-02/03/04, R-FRM-02/03, R-PRT-02 `does_not_apply`: a measurement cannot
  authorize a mapping/binding/admission decision; the tables carry no absolute
  segment lengths, frame correspondence, or assembly topology.
- R-OWN-05, R-PRT-01 `does_not_close`: morphometry is muscle-belly level; no
  patch area, areal stiffness or couple resistance at any attachment interface.

Screens (never gate; all confirmed by the validator, which RECOMPUTES them
from the pins):

| id | screen | result |
|---|---|---|
| S-MASS-05 | excluded .osim claims vs measured M. mulatta bands (kg): humerus 0.203 vs 0.294±0.119; radius+ulna 0.154 vs 0.194±0.078; hand 0.049 vs 0.057±0.011 | all inside 1 SD (deltas 0.091 / 0.040 / 0.008); claims stay EXCLUDED |
| S-MASS-06 | implied body weight via M2-8 (m g/kg, b g) | 5.2326 / 6.0938 / 4.9097 kg, all in [4, 7]; %BW screen: 3.8% of the transported grams predicts 647.52 g upper arm vs the 0.203 kg claim — ratio 3.1897 (> 2): the transported total is not the arm claims' body mass |
| S-MASS-07 | eigen-free trace invariant: B03 bone trace 4.426e-04 kg m^2 vs Cheng Icg sum 6.343e-04 kg m^2 (1 g·cm² = 1e-7 kg·m²) | ratio 0.6978, in [0.3, 1.5]; bone-only vs whole-segment are different quantities — same order of magnitude is the only claim |
| S-MASS-08 | species law: rhesus (M. mulatta) context | M. fascicularis tables INADMISSIBLE (species law; cross-species reference only); M. mulatta tables admissible as screening references only |
| S-PORT-09 | port muscle coverage in M2-3 and M2-5 | 21 muscle rows each; Biceps long / Biceps short / Brachioradialis present; Pronator teres ABSENT in BOTH — even muscle-level data is incomplete for the port set; and muscle mass is not a port-gate input |

## Verification (exact candidate revision; commands and exit codes in the receipt)

1. `python -B assembly_readiness.py derive` -> emits the document +
   derivation receipt; exit 0; "valid=True gates=14 screens=5 gap=10
   readiness=False".
2. `python -B assembly_readiness.py verify` -> exit 0;
   "byte_identical=True valid=True falsifiers_all_bitten=True" (double derive
   byte-identical; receipts `work/runs/verification_receipt.json` and
   `work/runs/falsifier_log.json`).
3. `python -B -m unittest test_assembly_readiness` -> Ran 10 tests, OK
   (P1-P9 confirmations + F1-F6 all-bite assertion + artifact-untouched
   check).
4. `python -B lint_report_numbers.py --selftest` -> every numeric literal in
   this report traceable to the bound artifacts; planted fake literals
   flagged (planted probe: a fake implied body weight and a stand-in mass
   that "closes" the weights gap).

## Falsifier proof (each: tamper a COPY, watch the named refusal, discard)

All six preregistered falsifiers BITE (log in `work/runs/falsifier_log.json`):
F1 `unbound_input_refused` (stand-in input name); F2
`satisfied_requires_pinned_evidence` (R-OWN-02 flipped to satisfied with an
empty evidence block); F3 `satisfied_requires_pinned_evidence` (R-MASS-01
counted total altered to 0.05); F4 `cheng_source_pin_mismatch` (tampered M2-6
copy); F5 `unlawful_status_refused` (status "qualified" outside the frozen
vocabulary); F6 `sealed_pin_mismatch` (a B05 port flipped to qualified in the
raw bytes). The committed artifact re-verifies byte-identical after the run.

## Capture (visible_static; task_id "B06" SHORT form)

- Profile object READ READ-ONLY from `agent_slots.sqlite3`
  (`kanban.cards.MAT2-B06.spec.ontology_qualification.task.verification_profile`;
  id `anatomy`, kind `visible_static`); registry criteria sha equals the
  document criteria (asserted at capture time).
- `capture_readiness.py` renders one 1280x4320 lossless PNG sheet, 3 view
  pairs x diagnostic/clean (6 manifest views), TWO DECLARED FRAMES never
  merged (B04 no-fusion law honored visually): assembly_world rows (overview
  + side/oblique) draw the four root frames as axis triads, the pinned
  source-chain polylines (bones/joints layer) and the readiness banner with
  the per-domain gap counts; the close-up row draws the hand.vtp envelope
  point cloud, the A05 mutant skeleton and all 48 A07 resolution markers
  (green filled = supported, amber hollow = explicitly_unresolved, red ring =
  measured outside with the exact per-axis excess in the label) in the osim
  hand frame. Cameras carry the full field set (frame_id, coordinate_unit,
  position, orientation convention+unit quaternion, target, distance,
  orthographic span, near/far, aspect, resolution, bookmark sequence,
  samples, state interval); quaternion self-test asserted.
- Bindings: `subject_sha256` = sha256(assembly_readiness.json) =
  88fa5e2d599017f5c9bf69ac92d920f23334c221f4afe87ccdda235f1fab2c71 on every
  view (view toggles preserve the physical state hash); `capture_sha256`
  1d24ce882fc7f010a444d9f8f1de6aebb016989c00038ba185a3cec9e5f7ca8b. The
  capture was re-run after the final document bytes so the binding is exact.
- `visual_capture.validate_manifest` (UNMODIFIED source head) returned
  `structurally_valid: true` (6 views) BEFORE handoff; receipt
  `evidence/validation_receipt.json`.
- Implementer pixel inspection (not inferred from filenames): rows 0/1/2/4/5
  cropped and inspected at full resolution. Overview: readiness banner with
  gap counts, root/component labels readable with backdrops, axes labeled,
  counted-mass 0.0 and no-fusion notes present. Close-up: 8 red OUT markers
  with exact excesses (e.g. OUT path.abd_poll_longus.3 d[z+0.002450] m,
  matching the sealed A07 row), green supported labels, amber unresolved
  markers, legend, honest-gaps footer. Side + oblique independently agree on
  the z-separation of the two arm chains. Clean rows carry no subject labels.
  One supported record (path.ext_digitorum.2) is simultaneously
  osim-reference-supported and mutant-assembly measured-outside; the red
  ring + excess label is drawn (the safety-critical signal) and the manifest
  declares both facts; its green text label lost collision placement and is
  NOT bound (declared no-ambiguity mechanism).

## Honest limits

- Readiness FALSE is the sealed outcome; this card's deliverable is
  evaluation completeness with explicit gaps, not a readiness claim.
- Screens compare different quantities on labeled terms (bone-only vs
  whole-segment; claims vs measured bands; n=6 other subjects, 1999); a
  screen can flag plausibility or inconsistency but never ownership.
- The capture is a 2D orthographic structured-records sheet (PIL) of sealed
  records, declared as such; not a native-engine 3D render; no dynamics;
  implementer pixel inspection is NOT independent visual acceptance — the
  reviewer owns the visual gate.
- No sealed record was edited, no history rewritten, no fitting run; the
  Cheng tables stay license-internal at their host path (cited by file+sha).
- `agent_logs/local_buffy_qwen/assembly_handoff_02.md` is an untracked host
  artifact; its transported-mass record is used through the sealed in-tree
  D-W04 pins, never through the untracked bytes.

## Durable lessons (for the Lieutenant to record)

1. The VTP/envelope geometry needed by a close-up lives OUTSIDE the sparse
   contribution path; extracting exact committed bytes (or sha-pinned host
   files with explicit pin checks) into the capture script keeps the sparse
   checkout honest without widening it.
2. Records can legitimately carry TWO statuses at once (osim-reference
   supported AND mutant-assembly measured-outside); required-subject lists
   built by concatenation then break set-identity validation — build them as
   set unions.
3. Gap-row counts that reports will quote should be emitted as JSON numbers
   (`sealed_counts`) and validator-recomputed, not embedded only in carried
   prose strings; prose numbers inside JSON strings are invisible to a
   numeric lint.
4. Cheng Table 2-5 prints `n` where Table 2-3 prints the abbreviation
   column — presence checks must key on muscle NAMES, not column position.
5. Re-bind the capture AFTER the last document change; a state hash in image
   titles that predates the final document bytes is a stale binding that a
   reviewer can catch by comparing hashes.
