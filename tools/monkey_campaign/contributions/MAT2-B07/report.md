# MAT2-B07 report — assembly adoption under the recorded authorization package

GENERATED from the receipts by `make_report.py` (zero hand-transcribed numbers). Composed against CARD_STARTER v3; house standards IMPLEMENTER_CHECKLIST.md (G1-G9) + TOOLKIT.md (P1-P9) cited at the candidate commit.

| identity | value |
|---|---|
| card | MAT2-B07 (task_id short form B07) |
| attempt | 08d3db08d4d64179b2f95a516a2155bd (agent wk-b07-adopt, branch-3) |
| criteria_sha256 | 5393a5d7707c370ce5c8ea072512a2b053d0abfb1d36dc952d509714150c77d2 |
| preregistration_sha256 | b08ba98f32dd1710f602bb7a5e2849a282fdb443d326de0ccd5c9ea49ffccf6a |
| governing decision | Captain #4 ADOPT-WITH-AUTHORIZATIONS (msg-4def1f92578b44d9b57b381643eae245) |

## 1. done_when verification

done_when (verbatim): "Architect names why this assembly replaces the current body, then requalifies affected dynamics/policies before use. Material-first addition: Adopt the material assembly only after actual limb load transmission and a compatible runtime/training contract are evidenced; static export is not runtime qualification."

- Architect named reason: RECORDED (adoption_record.json `adoption_decision.architect_named_reason`; kind ADOPT_WITH_AUTHORIZATIONS).
- Limb load transmission: evidenced at limb scope by the sealed M11 record (cited; not re-proven here).
- Compatible runtime/training contract: the bound SHAPE (RUNTIME_CONTRACT.md TC-1..TC-6, TC-12) + the TC-7 body-domain bind recorded by this attempt; the full freeze remains W04's card outcome.
- Static export is not runtime qualification: the record claims NO runtime qualification for the adopted assembly (TC-8 inputs absent; `assembly_readiness_claimed` = false; admitted mass 0.0 kg).

## 2. Adoption decision (summary)

the adopted assembly becomes the recorded BINDING TARGET (TC-7) for the runtime contract; no runtime body swap, no certificate forgery, no readiness=true claim, no port qualification

## 3. Authorization package discharge (8 items)

| item | ruling | discharge |
|---|---|---|
| 1 | R-MASS-04 | closed_by_recorded_ruling |
| 2 | R-MASS-02 | closed_by_recorded_ruling |
| 3 | R-MASS-03 | refusal_stands |
| 4 | R-OWN-02/03 | closed_by_work_with_receipt |
| 5 | R-OWN-04 | authorized_lane_open |
| 6 | R-OWN-05 | authorized_lane_open |
| 7 | R-FRM-02 | closed_by_work_with_receipt |
| 8 | R-FRM-03 | closed_by_recorded_ruling_with_work_receipt |

## 4. Per-row readiness closure table (the sealed B06 receipt rows)

Closure EVIDENCE per row; sealed statuses are never flipped here. assembly_readiness claimed by this record: false (honest count: 4 satisfied rows untouched; of the 10 gaps: 3 closed_by_work_with_receipt (R-OWN-02, R-OWN-03, R-FRM-02), 3 closed_by_recorded_ruling (R-MASS-02, R-MASS-04) or ruling with work receipt (R-FRM-03), 2 refusal_stands (R-MASS-03, R-PRT-01), 2 authorized_lane_open (R-OWN-04, R-OWN-05)).

| requirement | domain | sealed status | closure class |
|---|---|---|---|
| R-MASS-01 | mass | evaluated_satisfied_at_scope | satisfied_row_untouched |
| R-MASS-02 | mass | evaluated_gap | closed_by_recorded_ruling |
| R-MASS-03 | mass | evaluated_gap | refusal_stands |
| R-MASS-04 | mass | evaluated_gap | closed_by_recorded_ruling_with_work_receipt |
| R-OWN-01 | ownership | evaluated_satisfied_at_scope | satisfied_row_untouched |
| R-OWN-02 | ownership | evaluated_gap | closed_by_work_with_receipt |
| R-OWN-03 | ownership | evaluated_gap | closed_by_work_with_receipt |
| R-OWN-04 | ownership | evaluated_gap | authorized_lane_open |
| R-OWN-05 | ownership | evaluated_gap | authorized_lane_open |
| R-FRM-01 | frame | evaluated_satisfied_at_scope | satisfied_row_untouched |
| R-FRM-02 | frame | evaluated_gap | closed_by_work_with_receipt |
| R-FRM-03 | frame | evaluated_gap | closed_by_recorded_ruling_with_work_receipt |
| R-PRT-01 | port | evaluated_gap | refusal_stands |
| R-PRT-02 | port | evaluated_satisfied_at_scope | satisfied_row_untouched |

## 5. Ownership mappings (R-OWN-02 / R-OWN-03)

- Law validation (F1): 3/3 Captain-mapped A05 rows reproduced BIT-EXACT before emission.
- Hand-body mapping decisions recorded: 14 (R-OWN-02); distances 0.001238..0.014362 m.
- Forearm correspondence records: 31 (R-OWN-03; ulna 5 / radius 18 / humerus 8); distances 0.0047..0.1770 m.
- Every record carries the authorization citation (msg-4def1f92578b44d9b57b381643eae245) and its distance; distances inform, never authorize.
- Forearm distance law: zero-coordinate pose, declared joint translations/orientations; Euler-convention alternative bound 5.75867609998357e-06 m max (recorded per record).

## 6. Frame bindings (R-FRM-02 / R-FRM-03)

- Ulna-edge correspondence: ACCEPTED by this attempt (U-STR; radius supersession consequence ACCEPTED, execution stays with the staged ONT-A03 record).
- Packet-to-forest binding: 4 stable-name rows verified from the pinned B04 bytes; no transform authored (no_fusion_statement carried).
- Component/bond admission: 4 components, 39 bonds (kinematically_preserved), 9 unresolved bodies carried, counted mass 0.0 kg (agreement re-verified: equal=true).

## 7. TC-7 body-domain bind + TC-12 rebind record

- TC-7: body domain chimera.b07.adoption.a971dce72c1d494b481ba06acf8e0dd4; domain_tag material-assembly/buffy02-lineage; qualification_state: NOT runtime-qualified (TC-8 inputs absent)
- TC-12 executed here: the TC-7 bind record + the C09 anchor-class re-run against the CERTIFIED backend; the sealed certificate re-issue through the gate is NOT fabricated — 4 named prerequisites recorded (adopted-assembly scene; TC-3 drive-table re-declaration; TC-8 measured inputs; then the TC-6 certificate + C09 anchors on THAT body).
- Certified line: NOT silently invalidated (symmetric clause); admitted mass 0.0 kg; the certified walking body stays 10.037998 kg.

## 8. C09 anchor-class re-run (the certified CPU walk backend)

| anchor | frozen | reproduced | verdict |
|---|---|---|---|
| base_dx | 0.9131056683968011 | 0.9131056683968011 | EXACT |
| base_dy | -0.7178374101385098 | -0.7178374101385098 | EXACT |
| dump_sha256 | b47b709c43a021d24bfee13bb2fe4592167cf205ee0abf9971de462319389c93 | b47b709c43a021d24bfee13bb2fe4592167cf205ee0abf9971de462319389c93 | EXACT |
| n_ticks | 302 | 302 | EXACT |
| refused_tick | 302 | 302 | EXACT |
| stderr_sha256 | c6f9b6c00a1d549a4bc709724d2f62f8f28b37823696de4689e1950651c37481 | c6f9b6c00a1d549a4bc709724d2f62f8f28b37823696de4689e1950651c37481 | EXACT |
| stdout_sha256 | 8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc | 8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc | EXACT |
| tick_first_last | [0, 301] | [0, 301] | EXACT |
| worst_ledger_J_rounded | 30.970714 | 30.970714 | EXACT |

9/9 anchors EXACT from pinned extractions rebuilt in this workspace (source revision 17ba94b948ca217c1bbf8f7dee5b51b995b387bb).

## 9. Profile-class capture (climbing / motion)

- 6 view rows (3 views x diagnostic/clean), 24 frames, FFV1 -level 3 -g 1 -fflags +bitexact; structural validation: true (view_count 6).
- capture_sha256 416f2e28f3f9373b777186fbe4d82d51ecf450af13148f6b58feca66ffd1639a; decode-identity checks at [0, 12, 23] (identity only).
- Honesty label: RECORD-SPACE RASTER - not engine frames; not a climbing replay; motion-class delivery is the camera bookmark timeline over the static record set.
- Screens never gate: the receipts above are the numerical evidence the profile demands; independent image review remains mandatory.

## 10. Named checks (G12 accounting)

- Suite result: 27 executed, 0 skipped (exit 0, ok=true). No skip paths exist in the suite; KNOWN_SKIPS not needed.
- Falsifier arms live in the suite with clean-control-first + premature guards (G1): fb1 hand tamper, fb2 scope tamper, fb3 binding-name tamper, fb4 agreement tamper.

## 11. Refused steps (verbatim law, none forced)

- Ports: 0/8 qualified; the honest refusal record (PORT_QUALIFICATION.md) stands; this attempt qualifies no port (auth item 3).
- R-OWN-04: fitting lane authorized (auth item 5) and SEPARATELY dispatched — not executed here.
- R-OWN-05: c17-stiffness lane owns measured attachment-interface sources; lead admission only on measured sources — none admitted here.
- Certificate re-issue for the adopted body: refused until the 4 TC-12 prerequisites exist (no fabrication).

## 12. Evidence index (sha256)

| artifact | sha256 |
|---|---|
| ownership_mappings.json | c63adf4a15b97bab53ed29e2702ada87fbab75fc06501d40eac0506110de707d |
| frame_bindings.json | 345176992b53a05dc6276929f49c621da15a2d59e7abef1274ee03a2a0c0aa5b |
| adoption_record.json | f6952e8afc778f79a0ede05b61d73dd7c3fabd68789703552cd6136e25ef0199 |
| c09_anchor_rerun/c09_anchor_rerun.json | a68baa487e5b90e8e1427538bf831a7a0a01da4a65adb24fbc050b9f90944c0d |
| capture/capture_receipt.json | 1fc251bd033462f807e5d7209803939ac8c04f7890ac4b73fc1065b06bf451c9 |
| checks_receipt.json | 81da14d829d7ada4435cb9d2a510a104a1518f907fe65d1faf84171ec7b2ad57 |
| PREREGISTRATION.md | b08ba98f32dd1710f602bb7a5e2849a282fdb443d326de0ccd5c9ea49ffccf6a |
| ownership_mappings.py | d3842fd859d506d3efa8a2c45ed110ac7bb207ffdfc222fc6a8ac4ffef24fef5 |
| adoption_record.py | e204d5fbabcf2b9ec1bad2bba9d648749a78635c8c9105f2a5469b335e5d7246 |
| test_b07_adoption.py | 77bf08991ebdcb3cb85b00e6aed320cd66ca4d90edfa897f7d8719f13e64a21b |
| c09_anchor_rerun.py | 3100e1af6b8943e0e3de6f1e49a7d62d051bcc2cb1fa8538b1548f342b735e74 |
| make_capture.py | 9f6991a2aa850ccffe0c75e8813b9dda1be6676c5657c841fc060fc8c2124519 |
| make_report.py | 01fa2aac9d45558e30f093946739b03aef75d3f211e6bf21861c63a4e258f1ca |
| lint_report_numbers.py | e9930216ed4d78e43dc0d349173c53b42162caacafc5e891bbdd706e6369eb23 |

