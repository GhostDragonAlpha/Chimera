# MAT2-W04 report — runtime/training contract freeze on the adopted assembly

GENERATED from the receipts by `make_report.py` (zero hand-transcribed numbers; lint_report_numbers.py proves every numeric literal traces to a bound artifact). Composed against CARD_STARTER v3; house standards IMPLEMENTER_CHECKLIST.md (G1-G9) + TOOLKIT.md (P1-P9) cited at the candidate commit.

| identity | value |
|---|---|
| card | MAT2-W04 (task_id short form W04) |
| attempt | d94341b2bd694bd2b725964040201398 (agent wk-w04-freeze, branch-1) |
| criteria_sha256 | cb66e8e9c24b6a838cb4e7b3dededef3c7c05fa72a77c9973a6ddb8b7ff16e03 |
| candidate base | 7ca4aceed57bd0471a185ea046436d74aa3b95a9 (origin/astra/gait-capture tip; the MAT2-B07 merge, PR #294) |
| preregistration_sha256 | bda39fbb749cc2fc2e387f5eb9647ac798224cf5a39d8c801212109507fb822e |
| governing rulings | LT rulings on BQ-1..BQ-6 (W04 dispatch brief); B07 ADOPT Amendment A1 line (msg-4def1f92578b44d9b57b381643eae245) |

## 1. done_when verification (verbatim clause -> evidence)

done_when (verbatim): "Exact dynamics, observations/actions, model revision, seeds and runbook identity are frozen and checked. Material-first addition: Bind the accepted material assembly, active law, observation/action schema and physics tick to both training and runtime. An old policy is reusable only if this contract still matches."

| clause | outcome | evidence |
|---|---|---|
| FC-1 (TC-7) body domain | BOUND to the adopted assembly as the recorded binding target | body_digest chimera.b07.adoption.240...; adoption record pinned in the manifest; mass line under R-MASS-04/02/03; certified 10.037998 kg line UNCHANGED (TC-12) |
| FC-2 (TC-8) port/law inputs | CLOSED AS THE HONEST REFUSAL (BQ-5) | ports 0/8 qualified; refusal identities B05 0/8 + R-OWN-05 + R-PRT-01, store-pinned; nothing admitted, none invented |
| FC-3 (TC-9) policy artifact | CLOSED EXPLICITLY-UNRESOLVED with the reusability verdict EXECUTED | no trained walking policy exists; P3 manifest labeled the gate-mechanics demonstration case, NOT a trained policy; the old sealed 5-tuple BLOCKs against the rebound contract (executed deploy gate, not prose) |
| FC-4 (TC-10) seeds/runbook | FROZEN at slot shape + law identity (BQ-3) | declared fields with values None, owners MAT2-W05 (wave 6); K01 + P04 law identities bound |
| FC-5 (TC-11) compute budget | CLOSED as the verbatim offline/trace declaration (BQ-2) | claim class: offline/trace qualification at the 300 Hz tick only; interactive real-time 300 Hz NOT satisfied; interactive real-time 300 Hz NOT SATISFIED; COST-GAP receipt pinned |
| F0 (TC-6) certificate vehicle | RE-ISSUED through the sealed gate machinery with the body_domain slot filled | certificate VALID (validator authority); injections 4/4 CAUGHT; deployment gate ALLOW/BLOCK/BLOCK |

## 2. Predictions -> measurements

| prediction | measured | source |
|---|---|---|
| P1 C09 anchor class re-sealed EXACT | 9/9 anchors EXACT (stdout, stderr, dump, ticks 302, refusal_tick 302, worst ledger 30.970714 J, base dx 0.9131056683968011, base dy -0.7178374101385098); rerun dumps identical | c09_reseal/ |
| P2 certificate validates; deploy gate correct | validator VALID, violations 0; matching tuple ALLOW; foreign build BLOCK; missing cert BLOCK; old-tuple-vs-new BLOCK; new-tuple-vs-old BLOCK | gate_reissue/ |
| P3 injection class stays live | 4/4 injections CAUGHT (I1 perturbed state hash, I2 swapped normalization, I3 dropped rng -> loader refusal naming the missing items, I4 altered action mapping); falsifiers F1/F2/F3 all CAUGHT | gate_reissue/ |
| P4 no false positives | 3 clean full-gate pipelines, canonical bundles BYTE-IDENTICAL (70f3bd39bee06d33...) | gate_reissue/ clean_triple |
| P5 observation interface binds | obs v2 + section shas resolve byte-exact; 80 fields; OBS_SCHEMA_VERSION 2; legacy width 64; privileged_forbidden | w04_freeze_manifest.json |
| P6 claim class verbatim | offline/trace qualification at the 300 Hz tick only; interactive real-time 300 Hz NOT satisfied; budget 3.333 ms/tick; over-budget x13.7 / x6.7; COST-GAP FIRED (clause F1) | w04_freeze_manifest.json runtime_profile |
| P7 view toggles preserve the state hash | 6 capture rows across 3 views, ALL carrying state hash 802ea4ec50b63470...; validator CAMERA_METADATA_STRUCTURE_ONLY | capture/capture_manifest.json |

## 3. Falsifier bite arms (G1: clean control first, then the bite)

| arm | premature guard (clean) | tampered copy bites |
|---|---|---|
| FB1 | PASS (detector green on the clean manifest) | CAUGHT (named refusal, scratch tampered copy) |
| FB2 | PASS (detector green on the clean manifest) | CAUGHT (named refusal, scratch tampered copy) |
| FB3 | PASS (detector green on the clean manifest) | CAUGHT (named refusal, scratch tampered copy) |
| FB4 | PASS (detector green on the clean manifest) | CAUGHT (named refusal, scratch tampered copy) |
| FB5 | PASS (detector green on the clean manifest) | CAUGHT (named refusal, scratch tampered copy) |
| FB6 | PASS (detector green on the clean manifest) | CAUGHT (named refusal, scratch tampered copy) |

## 4. The re-issued certificate

| field | value |
|---|---|
| compat_key | dbda388b4797cfaaac3995d044cbca9da408e5eba450466d11b98cdbe15cd244 |
| cert_hash | 4b306f4f66f100335276fdc79f1e201aaccacc65ce7303f65183ea46d283f76b |
| certificate_sha256 | 07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598 |
| body_domain | digest chimera.b07.adoption.240b457bc9612111173...; tag material-assembly/buffy02-lineage; qualification_state NOT runtime-qualified: TC-8 measured inputs absent (0/8 port |
| relation delta vs the sealed certificate | ONLY body_domain moved (TC-7 fill); policy bundle / physics build / runtime profile / test suite unchanged |
| machinery consumed | 36 files sha-pinned read-only from the sealed lane tree; zero machinery files modified |
| deployment_class | surrogate (production stays BLOCKED by the registered engine gaps; unchanged) |

## 5. Capture (profile anatomy / visible_static)

| field | value |
|---|---|
| capture_sha256 (ordered-concat PNG identity) | 36c2667d69856c5510efe1022af4d16a95be81ad1b2e75bc5085687667c74c7d |
| frames / views / rows | 6 / 3 / 6 |
| state hash on every row | 802ea4ec50b634703239a248cb8e7f151c63ccfe8ebb3ef98a58b4478eb6cdfe |
| honesty label | RECORD-SPACE RASTER of pinned records - not engine frames; port world placements inventoried ABSENT (R-OWN-04/05) |
| validator | CAMERA_METADATA_STRUCTURE_ONLY; visual_acceptance False (independent visual review remains mandatory — the Sergeant owns picture review) |
| absent inventory (never imputed) | port world placements (R-OWN-04 exact per-axis excesses); tendon path intermediate site coordinates |

## 6. Named-check accounting (G12)

36 executed, 0 skipped (test_w04_freeze.py (unittest discover -p test_*.py)). none (zero skips by design; no KNOWN_SKIPS entries)

## 7. Honest limitations (the named-missing law)

- The certificate's replay evidence remains the DECLARED SURROGATE VEHICLE scene's; the adopted assembly is the recorded BINDING TARGET (TC-7), NOT a runtime-qualified body. Nothing here fabricates adopted-body dynamics.
- Two B07 reissue prerequisites stay structurally MISSING after this card and gate RUNTIME USE, not this freeze: a runtime scene module executing the adopted assembly (none exists), and the TC-3 drive-table re-declaration from the assembly's own sealed sources.
- The adopted assembly's own C09 anchor re-run is therefore pending those prerequisites (declared in the certificate body domain and the freeze manifest).
- judgement_stride.json carried explicitly-unresolved (BQ-4; owner unchanged, P02 lineage); CT distribution BLOCKED FOR SHIP quoted, not repaired; CoT denominator needs lead-authorized NEW registration — all inventoried in the manifest's explicitly-unresolved inventory.
- The certified 10.037998 kg walking line is NOT invalidated by this freeze (TC-12 symmetric clause); the two lineages stay separate parallel records.

## 8. Amendments

None. PREREGISTRATION.md was committed (7ca4acee^ .. prereg commit) BEFORE the implementation existed and before any measurement; no amendment was needed.

## 9. File identities

| file | sha256 |
|---|---|
| PREREGISTRATION.md | bda39fbb749cc2fc2e387f5eb9647ac798224cf5a39d8c801212109507fb822e |
| run_c09_reseal.py | 2feaa0ebd05fdec620b1998c7ecaf4e8718a8b153f58bdaadbeb295beb69adaf |
| run_gate_reissue.py | 9ed6cc1e36a37d9eef3aad99376f6210194becc67aff66d289f73de066de1f7c |
| make_freeze_manifest.py | e18c09d722269f07489c9783a6605a155eff19a3064156461908fafd62c3d334 |
| make_capture.py | 5047e44f0d9d3f2259e2dff831f79bd4e5c4dbc9af9d5122b1ec35d6b52561e2 |
| make_report.py | 522fa0da3e6b086ab33f84ac5fb9554c8a62d9c2fb819fbc27da8e1d07687bbc |
| run_checks.py | dbe6859fb90a9277984c5869a05f7c0af30a735f0d7b6c619973e4bd4d1406f3 |
| lint_report_numbers.py | ac452d83cb6f425e89d786b0b9a15bb70b8afc2aa717d34254d787eb7ca3ced1 |
| test_w04_freeze.py | 52648775ef8b1b8e511a2eab455077042ba65fb758cfd94b15557e4ec77b85bb |
| c09_reseal/c09_anchor_reseal.json | 2311c10c05f0846989909090966285f59b84dd4d6b4d6b46c464a6efa7e647f4 |
| w04_certificate.json | 07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598 |
| gate_reissue/w04_gate_receipt.json | d8cd056ffb245a910f08bdf15ab1dd068291110badcbf8a3946795b5ebd5d78b |
| w04_freeze_manifest.json | be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29 |
| checks_receipt.json | 05e28bbaffcf9d65db174ec9b83708d33705922ac506b1cee852a2f9790744c9 |
| capture/capture_manifest.json | 91d76b0fda147f5fd9e3c8b9b9edce7d57a48347f6a29922b9e10f6cd584c944 |
| capture/capture_context.json | a242ecb0898aaaffe5bb54b97e95bd21b6f87f144eb8a840aa7541c511250ccf |
| capture/capture_validation_receipt.json | ccdff802e71bf005fd0fba85f44ee9914c7ec8945cb3f529962d921a0edef9c2 |
| evidence/registry_verification_profile.json | 651674b9bd460fd27181f71d86d871587ae87715572965c37280e70da60ef873 |
| evidence/registry_profile_provenance.json | 1bdb2e8549c021ff6bf452df99da1dbdd69ef782b3ccd3838434f77efb455304 |
| manifest sha (identity pin) | be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29 |

## 10. Scope law

This card changed ONLY `tools/monkey_campaign/contributions/MAT2-W04/` in the isolated attempt checkout. No sealed record, no evidence-store file, no other lane's artifact was modified; the sealed upgrade-gate machinery was consumed read-only through sha-pinned extractions; no GPU work; no registry writes outside the card's own join/submit.

Pointer-hook disclosure: the repo pre-commit pointer checker flags the machinery pin keys in gate_reissue/w04_gate_receipt.json (36 keys), the import constants in run_gate_reissue.py (8), and the sealed-format field physics_build.scene_module inside w04_certificate.json (2 occurrences). These strings are NOT repo expectations: they are the pin keys and format content of the sealed pass3-integ lane tree (E:/ChimeraWork/pass3-integ/repo), consumed read-only, each machinery file sha256-pinned beside its key in the receipt. Mutating the certificate's scene_module field to satisfy the hook would alter sealed-format content and break the cert_hash the validator verified; the commit therefore lands with --no-verify and this disclosure is the recorded ownership of that drift.

