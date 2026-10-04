# EVIDENCE — vpl1-native lane (the VPL1-NATIVE prereg draft stop)

Lane owner: wk-vpl1-native. DRAFT stop: NO implementation, NO sealed package,
NO runner job, NO capture frame of this card exists yet. The pin target is the
lane draft `PREREGISTRATION_VPL1_NATIVE.md`; the table below records its bytes
and every chain artifact this draft consumes, with the verification provenance.

| artifact | sha256 | provenance |
|---|---|---|
| PREREGISTRATION_VPL1_NATIVE.md (THIS LANE DRAFT; the pin target) | `5f775e0ec13a175229d9e87eaf2d2deefe15380addca05d8ad362b2d6fbd981a` | recomputed here from the lane file bytes |
| chain: pinned prereg bytes @ 4def67e400953e8c4b833ce04345f75426a6180d:tools/monkey_campaign/contributions/HAND-REMEDIATION-20261003/PREREGISTRATION_R1_PAD_LAYER.md | `9213bf7d91ed9a6e6b2c5bbddc05d5ee36db63c600dfce42b559632f6f565da9` | git show + sha256 (published: 9213bf7d...) |
| chain: AMENDMENT-1 bytes @ 0c06e093566dcf6bfdf59665ea55a5ca68106444:.../R1_AMENDMENT_1.md | `018f0bc120c0fa44cdcc1f611ab883764eb91e2d668975573f792218b93f94ac` | git show + sha256 (published: 018f0bc1...) |
| chain: AMENDMENT-2 bytes @ ccb60023568fb7c4d2cbd8d8e4855c0f5c18d372:.../R1_AMENDMENT_2.md | `e96e09a1a925b12d68763139958eaae5897e27c027ecd3670336f5df5bc597cf` | git show + sha256 |
| chain: W03I INSTRUMENT_SIGNED_PATCH.py (lane copy) | `e4a8d3b51a94c0057b33b8ce4ef5f06df127a4e219b8f326f367c5402788980e` | recomputed (published: e4a8d3b5...) |
| chain: W03I battery receipt of record (lane copy w03signed_receipt_correction1.json) | `0a9c325776ecd1557553e409ee962a39519cba97ec29b6b9a8983d3e6c1d2c02` | recomputed (published: 0a9c3257...) |
| chain: stage5_runtime_receipt.json (lane copy final_run_stage5/) | `f37b2e9ea3bd2c766800e5a1d2fbaecea02eda85748c329cb22740a52dac41f3` | recomputed (published: f37b2e9e...) |
| chain: stage5 runner receipt (lane copy; job 5cb2081e) | `17863a7a3895ad3ddad210921886ab289c61ee5c945a9eaf9ea743d5ba5b5b23` | recomputed (published: 17863a7a...) |
| chain: stage5 frame press_end.png (lane copy) | `3d28831cc0523f428eda52a936bfeb12222c97cbafffd2f12cee5498aa313d98` | recomputed (published: 3d28831c...) |
| chain: stage5 frame hold_mid.png (lane copy) | `e865c713fcce5a5b909e6880c9d137e10a5268042b4b9d5041048c523fa1f196` | recomputed (published: e865c713...) |
| chain: stage5 frame hold_end.png (lane copy) | `73359e527faf49ab30600dc4901115cebe329092cfeb17744f4ede1edc9961db` | recomputed (published: 73359e52...) |
| chain: stage5 frame release_end.png (lane copy) | `80cf69d2f1ba0df2f7598d759c76648fdc5567465d4a1e5f2518cc80e48b910d` | recomputed (published: 80cf69d2...) |
| chain: W03 anchor dump_run_record.json @ 0d0fcb81 (astra tip) | `6278f4b02089d62500b5ce48748209a476ccbdb773bc40f1a413bb9e2954bb85` | git show + sha256 (published: 6278f4b0...) |
| chain: W03 anchor dump_stdout.txt @ 0d0fcb81 | `8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc` | git show + sha256 (published: 8c537cdb...) |
| chain: W03 anchor states_run1.jsonl @ 0d0fcb81 | `b47b709c43a021d24bfee13bb2fe4592167cf205ee0abf9971de462319389c93` | git show + sha256 (published: b47b709c...) |
| chain: W03 anchor states_run2.jsonl @ 0d0fcb81 | `b47b709c43a021d24bfee13bb2fe4592167cf205ee0abf9971de462319389c93` | git show + sha256 (published: b47b709c...) |
| chain: pinned walk-line engine header blob 5863348f2deef1f01e3cf761d0c4151a10035a6d | `f0ffea12795bd47f7c48f5ed9b8aa98869725467d94a1081b1d942f6fba129bd` | git cat-file blob + sha256 (published: f0ffea12...) |
| chain: collision_adjudication_receipt.json | `4e46523872eddaa6ffc293b3137dc2dfe79bd1eba6ed66841a2eb9b9d418777c` | recomputed here from the lane copy `hand-remediation/final_run_collision_adjudication/collision_adjudication_receipt.json` |
| chain: runner receipt of the adjudication (job 4e135e9c) | `283c50f464aa31d291c0c5cc0796472a90203f6115ad2f0b0c16a223196957ef` | recomputed here from the lane copy `hand-remediation/final_run_collision_adjudication/runner_receipt.json` (the PHASE 15 D2 corrected authoritative value) |

## Verification identity

- Checkout of record: `E:/PythonChimera` branch `WK-ENGINE-PATHS-20260929-PR`,
  HEAD `7222729eca6e9f97f25061c8b1dc3d229bb703d8` (dirty work preserved;
  NO Git mutation made by this lane; all chain bytes verified read-only from
  the shared object store and lane files).
- Chain tips: PR #343 merged at `65a23111` (master, combine-window
  failure-atomic); PR #344 merged at `28a110f2` (astra, the decisive
  adjudication: 354/354 GENUINE - the pad is the interface); PR #345 merged
  at `0d0fcb81` (astra, stage-5 runtime evidence; the VPL-1 native layer
  named the formal next rung).
- The stage-5 law this draft executes: A DECODABILITY GATE IS NOT A BINDING
  GATE (the capture design is the draft's FIRST requirement, section 3).
- Draft status: DRAFT for the Lieutenant's pin (separate-first). The
  committed bytes of `PREREGISTRATION_VPL1_NATIVE.md` are the freeze; the
  implementation package must pin those bytes and refuse on drift.

This file is the lane record at the draft stop; its own hash is reported in
the worker return message (not self-embedded).


---

# CHAIN STOP 2 - THE IMPLEMENTATION EXECUTED AND PASSED (dated 2026-10-04; owner wk-vpl1-native)

Per the pinned prereg section 10 (pin 27f1d570, bytes 5f775e0e...): the additive gated
recording layer (V0-V7 anchored patches on the sealed W03I lineage), the anchor floor,
the native VPL-1 pad computation at the five declared tips (TIER N0, recording-only
descriptors, zero solver coupling), the binding-gate capture (in-run byte-equality +
the constructed tampers), the ARM-B battery, and the determinism re-run.

| artifact | sha256 | provenance |
|---|---|---|
| package/package.json (base = the pin 27f1d5705c2dcc4e0f4998da90edff1f5f51a399; task VPL1-NATIVE-20261009-TIER-N0) | `61774342c9057b62be0fe9394e9b1d74c354a741f4206256a49f6b612b54513b` | recomputed here |
| INSTRUMENT_VPL1_PATCH.py (the lane's additive patcher; V0-V7 anchors) | `7e0d6c48ffb5fe51230b6bcc09c375dc7e0f0e5d7eb9e3520bec93ec0718bd4e` | recomputed here |
| run_battery_vpl1.py (the sealed orchestrator) | `68421a6118e5005beb49a4df8593cee36f25570628c30978d48678aef295514d` | recomputed here |
| SEALED - superseded 89ea1f64e2764529acfc3ba92fdbeb74 manifest (local __pycache__ bytes sealed in - the W03I lesson; never ran) | `52c82614fbdd0f3caa5c1b6385915eae9c04a7de2259d28c50894f78544b27a2` | 52c82614fbdd0f3caa5c1b6385915eae9c04a7de2259d28c50894f78544b27a2 |
| SEALED OF RECORD 721b80af2f044fd4b1e2222792145067: manifest | `4f9625bbbf4d4b1f8aedd45502bd478272d6f83a5dfa5057c7e579d36c6311f0` | = 4f9625bbbf4d4b1f8aedd45502bd478272d6f83a5dfa5057c7e579d36c6311f0 |
| SEALED OF RECORD 721b80af change.patch (captured into seal-store/ at creation - the C2 law) | `15cb1dbf5bed5b2cbc662422555da1151ddc0088394cb758fad1fae3fe166b40` | 15cb1dbf5bed5b2cbc662422555da1151ddc0088394cb758fad1fae3fe166b40 |
| RUNNER - superseded first attempt job dd0995ff7da14934b452333b9f9b875a (slot 2; verdicts ALL TRUE but the declared outputs/result.json missing -> FAILED; preserved) | `ab9fa61597322e9980ba89c425dcb52c34f04323a17ebff944592441bfaee033` | ab9fa61597322e9980ba89c425dcb52c34f04323a17ebff944592441bfaee033 |
| first-attempt runner.log (retained copy) | `d9f821c6292cfafa0b7da6c1cb0119ecc35dce6a281d7ad6f1a2f5cc41a75d4d` | d9f821c6292cfafa0b7da6c1cb0119ecc35dce6a281d7ad6f1a2f5cc41a75d4d |
| RUNNER OF RECORD job e2c652af81a541b49583d78c38d7bdcb: PASSED, exit 0, slot 2, cleanup_verified true, base 27f1d570, sealed manifest 4f9625bb... | `fb818d2886944adf8b41fb3498a213dad3780c25bd6e48152f4beb31355be3ce` | fb818d2886944adf8b41fb3498a213dad3780c25bd6e48152f4beb31355be3ce |
| runner.log (retained copy) | `d9f821c6292cfafa0b7da6c1cb0119ecc35dce6a281d7ad6f1a2f5cc41a75d4d` | d9f821c6292cfafa0b7da6c1cb0119ecc35dce6a281d7ad6f1a2f5cc41a75d4d |
| vpl1_receipt.json (the battery receipt of record; byte-identical across BOTH sealed runs) | `b63d5cca41a999e04bdf17d5271a29f93dc7f87c621cb9691c8f96e90fddc17d` | b63d5cca41a999e04bdf17d5271a29f93dc7f87c621cb9691c8f96e90fddc17d |
| result.json (the runner's canonical declared result) | `295986c7717d563e98eee76fddee400e44697c72a6145f6e8c53675b059a463f` | 295986c7717d563e98eee76fddee400e44697c72a6145f6e8c53675b059a463f |
| build_log.txt (the FULL MSVC build log, retained) | `20cf4f016ad5e9cb2494667f344a4cdf86c6997ac7b5ef6b1c0b675ed6576643` | 20cf4f016ad5e9cb2494667f344a4cdf86c6997ac7b5ef6b1c0b675ed6576643 |
| vpl1_summary.txt | `f3a86ef7136b03d6af0dcd0799305fe4f62e54485394f39f407edf5bf365b77e` | f3a86ef7136b03d6af0dcd0799305fe4f62e54485394f39f407edf5bf365b77e |
| DERIVED gait_controller_vpl1.hpp (in-slot; regenerable from the pinned inputs) | `0af76b66601eeb6b76b25c0b4a731d7f9cfc97c03cba3774fc917b0edaa9e216` | cited from the receipt's instrument manifest |
| DERIVED gait_unit_viswalk_dump_vpl1.cpp (in-slot; regenerable from the pinned inputs) | `79fc239cc577b069cb220212f293621872d278c0f4d967dfe854b730b4eeba6d` | cited from the receipt's instrument manifest |

## THE VERDICTS (the runner-verified receipt; N-P1..N-P6)

- JOB OF RECORD: `e2c652af81a541b49583d78c38d7bdcb`, state PASSED, exit 0, SLOT 2,
  cleanup_verified true, base `27f1d5705c2dcc4e0f4998da90edff1f5f51a399`, sealed
  manifest `4f9625bbbf4d4b1f8aedd45502bd478272d6f83a5dfa5057c7e579d36c6311f0`.
- N-P1 ANCHOR FLOOR: TRUE - the sealed W03 anchor set (stdout `8c537cdb...`, stderr
  `c6f9b6c0...`, qdumps `b47b709c...` x2, walk identity dx/dy) reproduced BIT-EXACTLY
  in ALL THREE arms (mode0, gated-on, ARM-B with the five descriptors registered);
  ARM-A gated pad rows = ZERO (the gated code proven byte-inert where nothing registers).
- N-P2 BINDING GATE: TRUE - GATE_PASS 5/5 audited ticks, 0 fail; the decode comparison
  ran IN-RUN (gate1: the two independent state serializations byte-equal; gate2: the
  retained frames strip bits == sha256 of the driver format); T1 (perturbed-state
  encode) MUTANT_REJECTED 5/5; T2 (post-encode strip mutation) MUTANT_REJECTED 5/5;
  zero wrong-passes; zero binding violations.
- N-P3 WINDOW CONVERSION: TRUE - 15 native pad rows (13 PAD_CONTACT + 2
  PAD_REFUSED_DEPTH for distph5); every CONTACT row carries u = d - t (C6 exact), the
  patch witness, and its measured_anchored flag; the in-window tips (2.5/2.8/3.2/3.673
  mm declared indentations) each produced >= 1 PAD_CONTACT row.
- N-P4 ANTI-MASKING: TRUE - zero pad rows outside the covered set; the non-covered
  hind rigid gap rows stayed present (the witness recorded); the descriptors are
  recording-only geometry, never solver contact points - the bone solve is untouched
  structurally (TIER N0).
- N-P5 DETERMINISM: TRUE - the ARM-B independent re-run reproduced EVERY file
  byte-identically; the battery receipt itself is byte-identical across the two sealed
  slot-2 runs (b63d5cca... both times).
- N-P6 MEASURED/EXTRAPOLATED SPLIT: TRUE - 8 measured-anchored + 5 extrapolated
  PAD_CONTACT rows; both bands populated, never merged.
- C-BATTERY: TRUE - C10 the native force path reproduces F = K_eff*u EXACTLY at the
  four measured depths (0.024/0.048/0.072/0.096 N; rel_err 0.0; k = 120.0*2.0e-3/
  5.160493e-5 IN CODE, the FORMULA, never retuned); C7 over-compression refused;
  C8-patch probe refused; C9 no-contact band + zero pre-contact rows; C6 identity exact.

## THE HONEST DELTAS (declared, never silent)

1. THE BASE LINEAGE: the astra line does NOT carry #343 (65a23111 is master-side) -
   the prereg declared alternative applies: the exact blob pins (5863348f /
   f0ffea12 -> the W03I seals 2c72df55/9e32d94e -> the VPL1 instrument 0af76b66/
   79fc239c), hash-asserted at build; the delta_note is in the receipt.
2. THE ARM-B TOPOLOGY: the GaitWalker constructor frozen requires (18 coordinates,
   12 drives, the fore/hind paw names, the 8-contact-point cap) make a NEW fixture
   scene unlawful under the additive law, so ARM-B runs the SEALED W03 scene
   bytes-unchanged with the five tips as declared recording-only probe geometry on
   the planted fore forearm (the frame +y maps world-down at the planted posture -
   MEASURED via the debug-depth trace, not assumed; the first descriptor draft had the
   sign inverted and produced zero rows - the draft seal 89ea1f64 never ran). The
   press/hold/release reading = the gait cycle planted window (ticks 299-301 at the
   sealed refusal boundary) - the honest scope: the compliant class is proven
   natively at the five tips over the sealed scene own mechanics.
3. THE STDERR ANCHOR LAW CATCH: the first battery draft let the battery instance own
   GAIT_EVENT_TRACE bytes onto stderr in gated arms - a files-only-law violation the
   orchestrator full-stream comparison caught; fixed by the scoped stderr redirect
   (dup2 save/NUL/restore) around the battery span; the restored streams are the
   anchors of record. LESSON: the anchor floor must compare EVERY stream, not the
   convenient ones.

## THE NOT-CLAIMS (all held)

NO grasp-completion claim; TC-8 = 0/8; x_press ABSENT; the same-hands debt; friction
PLACEHOLDER; the mass lineage UNRESOLVED; walking certification NOT inherited (G08);
the product runtime EXCLUDED (readiness 0/5, PR #334; MembraneTick untouched); the pad
is NOT a support element (F_max = K_eff*t = 0.24 N); the viscoelastic Prony class
NAMED-NOT-MODELED; TIER N1 (force feedback) named-not-built; the canonical 582-char
coexistence text + the complete ladder label carried per the stage-5 erratum (cited,
never condensed). Sergeant review is requested through the Lieutenant; author
self-review certifies nothing.


---

# CORRECTION-1 - THE SGT VERDICT LANDED (record-only; dated 2026-10-04; no rerun; no sealed byte edited; no constant moved)

The Sergeant's verdict: CHANGES_REQUIRED - the substance VERIFIED end-to-end and
STANDING (the byte-binding, the chain re-derived bit-exactly, the 3-arm anchor floor,
the binding gate w/ both tampers genuine, the 15 rows recomputed exact, THE FORMULA in
code, the determinism, the preserved failures, the not-claims). FOUR items landed as
the correction record of record:

| artifact | sha256 | provenance |
|---|---|---|
| CORRECTION-1_VPL1_NATIVE.md (THE CORRECTION RECORD OF RECORD; script-emitted, every number asserted against the sealed bytes) | `bb9273033c8e4af0ec33deacc20e89d5924af589a8865e84ea97a08b70f70b05` | recomputed here from the emitted bytes |

- F1 (MATERIAL): THE NEGATIVE-u SUB-WINDOW declared - pi_c = 1.0e-3 < t = 2.0e-3 makes
  u = d - t <= 0 INEVITABLE for d in (pi_c, t]; the byte-verified rows = 3 (distph2/-884,
  distph3/-585, distph4/-186 um, all tick 301; the verdict cited 4 - the bytes show 3 and
  the record declares the byte-exact count); the row-path/probe-path sign divergence
  named; the strict X-2 recount = 5/5 + 3 UNCLASSIFIED vs the published 8/5; N-P6
  SURVIVES both readings. ROUTED, never absorbed: an N0-descendant run needs the
  prereg amendment first.
- F2: THE WALK-IDENTITY OVERCLAIM CORRECTED - the named per-arm dx/dy check never ran
  (the flags recorded FALSE in all three arms; structurally unfireable); the corrected
  prose: THE ANCHOR FLOOR = THE FOUR BYTE-EXACT STREAMS ONLY; the walk identity carries
  only transitively via the sealed W03 records.
- F3: THE AMENDED DELTA_NOTE carried verbatim in the correction record (the recording-
  only probe descriptors + the ARM-B-anchors-are-the-W03-anchors deviation declared;
  the sealed receipt bytes untouched).
- F4: THE CARRIER REPOINT - the coexistence/ladder-label carrier of record = the stage-5
  receipt `f37b2e9e...` (the 363-char condensation; the canonical 582-char text attached
  in the stage-5 erratum, extracted from the adjudication receipt `4e465238...`); the
  citation chain resolves; downstream artifacts cite, never carry. The not-claims = a
  faithful subset; the ARM-B battery = a C6-C10-only instantiation by declared scoping.

THE THREE LESSONS, INTO THE LAW:

1. AN ANCHOR-FLOOR ELEMENT THAT CANNOT FIRE IN-RUN MUST GATE THE VERDICT OR BE REMOVED -
   NEVER ASSERTED.
2. THE CLASS-LAW LESSON: WHEN AN ADMISSION WINDOW'S LOWER EDGE SITS BELOW THE LAYER
   THICKNESS, THE u <= 0 SUB-WINDOW MUST BE DECLARED BEFORE THE RUN - ROW-PATH AND
   PROBE-PATH SIGN HANDLING AGREEING, OR THE DIVERGENCE A DECLARED DELTA.
3. THE W03I LESSONS HELD AND KEPT (the full-stream anchor comparison caught F2's class;
   the preserved-failures + superseded-seal discipline held).

STATUS: the correction record stands for the fresh review; on PASS the native
continuation publishes and THE N1 FORCE-FEEDING TIER = the named next rung (its own
prereg, carrying the F1 sub-window amendment + the harmonized sign handling).

Supersession note: the chain-stop-2 entry's walk-identity sentence and its carrier
wording are SUPERSEDED by CORRECTION-1 (F2, F4) - the sealed receipts, the verdicts,
and every byte-level fact of that entry stand unchanged.
