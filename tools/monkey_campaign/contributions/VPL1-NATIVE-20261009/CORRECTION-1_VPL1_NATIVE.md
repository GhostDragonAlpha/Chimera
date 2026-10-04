# CORRECTION-1 - VPL1-NATIVE-20261009 (record-only; no rerun; no sealed byte edited; no constant moved)

- Date: 2026-10-04; author: wk-vpl1-native.
- Trigger: SGT VPL-1 NATIVE verdict CHANGES_REQUIRED - the substance VERIFIED end-to-end (the byte-binding, the chain re-derived bit-exactly, the 3-arm anchor floor, the binding gate w/ both tampers genuine, the 15 rows recomputed exact, THE FORMULA in code, the determinism, the preserved failures, the not-claims); this record lands the four items; the fresh review follows.
- Receipt of record: `final_run/vpl1_receipt.json` sha256 `b63d5cca41a999e04bdf17d5271a29f93dc7f87c621cb9691c8f96e90fddc17d` (sealed bytes, never edited).
- Prereg pin: 27f1d570 (origin/review/VPL1-NATIVE-20261009), bytes 5f775e0ec13a175229d9e87eaf2d2deefe15380addca05d8ad362b2d6fbd981a - NEVER edited.

## F1 - THE NEGATIVE-u SUB-WINDOW (material; the prereg-internal contradiction)

THE FINDING: the admission window's lower edge pi_c = 1.0e-3 m sits BELOW the layer thickness t = 2.0e-3 m, so for every admitted d in (pi_c, t] the indentation u = d - t is <= 0 - the u <= 0 sub-window was INEVITABLE and was NOT declared before the run; the row path admits it (PAD_CONTACT with u <= 0, flagged measured_anchored with no lower bound) while the probe path treats u <= 0 as no-contact (band 4) - the two paths' sign handling DIVERGE (internally inconsistent)

THE BYTE-VERIFIED ROWS (asserted against the sealed receipt):

| tick | tip | depth (m) | u (m) | u (um) | measured_anchored flag |
|---|---|---|---|---|---|
| 301 | distph2 | 1.115594669e-03 | -8.844053310e-04 | -884 | True |
| 301 | distph3 | 1.414919006e-03 | -5.850809936e-04 | -585 | True |
| 301 | distph4 | 1.814018123e-03 | -1.859818770e-04 | -186 | True |

COUNT NOTE: the verdict cited 4 rows; the sealed bytes contain 3 (named above; the cited values -884/-585/-186 um match exactly) - the correction declares the byte-exact count, which is the record's number

THE RECOUNT: published flag split = 8 measured-anchored / 5 extrapolated (the flag has no lower bound); STRICT X-2 RECOUNT = 5 / 5 + 3 UNCLASSIFIED (the negative-u rows sit outside BOTH X-2 bands, which span u in (0, 0.8e-3] and (0.8e-3, 2.0e-3] only); the verdict cited 7 / 5 + 1 UNCLASSIFIED - the same direction; the byte-exact split is the record's number and the fresh review reads the same rows.

N-P6 SURVIVAL: N-P6 (both bands populated) SURVIVES under BOTH readings (5/5 or 8/5); the verdict stands

DISPOSITION: THE SUB-WINDOW FINDING IS ROUTED, NEVER ABSORBED: any N0-descendant run (N1 included) requires a prereg amendment declaring the sub-window treatment and harmonizing the row-path/probe-path sign handling BEFORE it runs; the sealed receipt's 15 rows and 8/5 flag split remain the sealed bytes, corrected HERE

## F2 - THE WALK-IDENTITY OVERCLAIM (corrected)

CLAIMED: the lane EVIDENCE.md chain-stop-2 entry said the anchor set incl. the walk identity dx/dy was reproduced BIT-EXACTLY in ALL THREE arms

WHAT THE RECEIPT SHOWS: the named per-arm dx/dy presence checks DID NOT RUN - the identity strings are absent from the anchor stdout (the flags recorded FALSE in all three arms; the check was structurally unfireable - the identity's carrier is the W03 anchor RECORD files, which the arms never re-dump)

CORRECTED PROSE (superseding the chain-stop-2 EVIDENCE entry's sentence): THE ANCHOR FLOOR = THE FOUR BYTE-EXACT STREAMS ONLY (stdout 8c537cdb..., stderr c6f9b6c0..., qdumps b47b709c... x2) in all three arms; the walk identity (dx 0.9131056683968011, dy -0.7178374101385098) carries only TRANSITIVELY - it is a fact of the sealed W03 records cited by the chain, never a per-arm re-derivation of this battery

LESSON INTO THE LAW: AN ANCHOR-FLOOR ELEMENT THAT CANNOT FIRE IN-RUN MUST GATE THE VERDICT OR BE REMOVED - NEVER ASSERTED

## F3 - THE DELTA_NOTE AMENDMENT (the artifact-of-record carries it)

THE AMENDED DELTA_NOTE (verbatim; the sealed receipt bytes untouched; this record carries it):

>>> BEGIN AMENDED DELTA_NOTE
NEW native compliant-pad recording class + binding gate on the W03I lineage; NO frozen constant moved (k = 120.0*2.0e-3/5.160493e-5, the FORMULA, in code); the descriptors are RECORDING-ONLY PROBE GEOMETRY (TIER N0, zero solver coupling) - a DECLARED TOPOLOGY DEVIATION: the sealed W03 scene carries the five tips as probe descriptors instead of a new fixture scene (the constructor's frozen requires forbid one under the additive law); THE ARM-B ANCHORS ARE THE W03 ANCHORS - the prereg's never-conflated clause (ARM-B's own fresh anchors) was NOT exercised and is declared unexercised; the base lineage is the sealed W03I chain (blob pins), NOT a master-ancestry build (#343 is NOT in the astra ancestry - the prereg's declared alternative: exact blob pins); the negative-u sub-window finding (F1) is ROUTED, never absorbed
<<< END AMENDED DELTA_NOTE

## F4 - THE CARRIER REPOINT (the wording fixed)

CORRECTED WORDING: THE COEXISTENCE/LADDER-LABEL CARRIER OF RECORD = the stage-5 receipt `f37b2e9ea3bd2c766800e5a1d2fbaecea02eda85748c329cb22740a52dac41f3` (its sealed field is the 363-char condensation; the canonical 582-char text + the complete ladder label are attached verbatim in the stage-5 erratum record, script-extracted from the adjudication receipt `4e46523872eddaa6ffc293b3137dc2dfe79bd1eba6ed66841a2eb9b9d418777c`); the citation chain RESOLVES: downstream artifacts (this lane included) CITE the canonical text - they never carry or condense it

NOT-CLAIMS NOTE: the receipt's not-claims block is a FAITHFUL SUBSET of the chain's not-claims (the objective-line law's open items all held); the ARM-B battery is a C6-C10-ONLY INSTANTIATION by declared scoping - C1-C5 are the merged instrument's controls on the analysis line, cited from the sealed screens, never re-run

## THE THREE LESSONS, INTO THE LAW

1. AN ANCHOR-FLOOR ELEMENT THAT CANNOT FIRE IN-RUN MUST GATE THE VERDICT OR BE REMOVED - NEVER ASSERTED (F2's lesson)
2. THE CLASS-LAW LESSON: WHEN AN ADMISSION WINDOW'S LOWER EDGE SITS BELOW THE LAYER THICKNESS, THE u <= 0 SUB-WINDOW MUST BE DECLARED BEFORE THE RUN - ROW-PATH AND PROBE-PATH SIGN HANDLING AGREEING, OR THE DIVERGENCE A DECLARED DELTA (F1's lesson)
3. THE W03I LESSONS HELD AND KEPT (the full-stream anchor comparison caught F2's class; the preserved failures + the superseded seal discipline held)

## EMISSION

every number above was computed from the sealed receipt bytes and ASSERTED by this emitter before emission; no sealed byte is edited; no rerun; no retune; the k FORMULA untouched.
