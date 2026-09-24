# FOREARM PACKAGE — RECOVERY RECORD (checkpoint log, append-only)

## CHECKPOINT 2026-09-24 (T0) — campaign reopen, baseline reconciled

**Verified:**
- Session-5 artifacts located and reconciled: campaign lived entirely in gitignored `.tmp/anatomy_compiler/` + `agent_logs/bigpickle/`; nothing was committed anywhere. Baseline = Session 5 (report 05, 2026-09-23 23:35).
- Durable snapshot created: `baseline_snapshot/` (44 files: code, runs, source_xml, session_reports 01–05, mesh inputs) — byte-identical, originals untouched.
- `MANIFEST.json` crosschecks 4/4 GREEN: chimanoid.xml == source_sha256 (675e00d0…); monkey_birth.bin == target_mesh_sha256 (550a5b3e…); monkey_joints.bin == target_pack_sha256 (74b3ab04…); **H-1 resolved** — declared `fitted_packet_sha256` a4475550… == sha256 of `actual_monkey_fit.json` (field semantics: the fit packet; NOT byte drift).
- TASK_BOARD.md written; frozen boundaries on record.

**Active (dispatched at T0, background):**
A1 left wrist ambiguity · A2 right wrist ambiguity · A3 32-site source audit · A4 transforms+bilateral · A5 containment authority+uncertainty · A6 evidence taxonomy · A7 tendon paths · A8 moment arms · A9 Session-5 reproduction · A10 qualification spec v0.

**Blocked:** none yet. (Watch: A9 environment drift; A1/A2 may hit "loop detail not recorded in packet" → they recompute from `inputs/` mesh copies.)

**Next:** collect audit completions as they land → verify receipts → integrate (I1/I2) → checkpoint → refill slots with follow-on bounded tasks (e.g. wrist-ambiguity resolution-evidence probes, spec pass-2) → I3 blocker report for Astra.

**Git:** branch `forearm-package-20260924` from detached HEAD c70b7a6c; only `forearm_package/` is staged/committed by this campaign. Unrelated dirty files in the worktree are other lanes' — untouched.

**Exact resume point if this session dies:** read TASK_BOARD.md statuses → for each DISPATCHED-but-missing audit, re-dispatch the same brief (briefs live in the dispatch log / audit dir `brief.md` if written) → continue the loop. Never re-run a completed audit without cause.

## CHECKPOINT 2026-09-24 (T1) — first audit integrated

**Verified:**
- A3 (32-site source audit) COMPLETE and coordinator-receipt-verified (fresh re-run 32/32; canonical + raw hashes independently reproduced; baseline integrity clean).
- A3 verdict: PASS on identity/units/roles/provenance/canonical-hash. One falsifier fired on DOCUMENTATION: ERRATUM E-1 — report-05 line 29 "8 last-endpoints per side" is wrong; measured 4/side (8/0/24 are two-side totals). Recorded on the board; baseline NOT edited.
- Side observation: 937 site elements = 468 named + 469 tendon-path refs.

**Active:** A1, A2, A4, A5, A6, A7, A8, A9, A10 still running (background).

**Blocked:** none.

**Next:** integrate remaining audits as they land; I1 (wrist consolidation) after A1+A2; I2 (spec pass-2) after the pack; commit each integration.

## CHECKPOINT 2026-09-24 (T2) — A10 spec v0 integrated

**Verified:**
- A10 qualification_spec_v0.md delivered (209 lines, 6 sections): coordinator spot-check green — "APPROVED" appears only in NOT-APPROVED banners; 14 [ASTRA-APPROVES] placeholders; 33 [PENDING A<n>] slots; baseline integrity clean.
- A10 independently re-derived the role-count law (0 first / 4 last / 12 waypoint per body) from artifacts — independent confirmation of A3's ERRATUM E-1 before reading A3.
- New baseline facts surfaced by A10 (from fit-packet records, to be owned by I1 after A1/A2 confirm): wrist sections record n_loops=4, n_identified_loops=2, n_open_chains=0 at axials 0.05151 m / 0.05348 m; hull unresolved there too (dist_to_hull null). Candidate C numbers verified from record (db=6.24mm, dc=±2.02mm, max disp 6.559mm, passed=false both sides; only BRD/BRD_l path-length deltas nonzero ≈ −0.90mm; arm deltas 0.0).

**Active:** A1, A2, A4, A5, A6, A7, A8, A9 still running.

**Blocked:** none. (A10's 3 [PENDING A3] slots are fillable now at I2 — A3 done.)

**Next:** integrate A1–A9 as they land → I1 (wrist) → I2 (spec pass-2, incl. filling A3 slots) → I3.

## CHECKPOINT 2026-09-24 (T3) — A10 committed (pointer fixed), A4 integrated

**Verified:**
- A10 spec v0 committed; doc-lint caught a broken relative pointer to the manifest tool from the spec's dir — fixed to the correct relative path (mechanical coordinator fix, no content change); hook satisfied without bypass.
- A4 (transforms + bilateral) COMPLETE, receipt re-verified by coordinator fresh re-run: PASS 5/5, falsifier not triggered. Reconstruction max 1.15e-9 m (export precision; 5.6e-17 m full precision — "0.0 at export precision" claim of report 05 §3 confirmed). Bilateral: mirror max 0.6306 mm (BICshort-P6), mean 0.0547 mm; asymmetry concentrated in exactly 2 pairs (BICshort-P6 0.63 mm, FCU-P2 0.24 mm; other 14 ≤ 2 nm). Handedness mode `preserve` recorded at actual_monkey_fit.json:119-120, chirality_det +1. R is scale×rotation by construction (s≈0.2217, det(R)=s³, Q=R/s proper) — semantics, not defect.
- A4 negative-finding preserved: mirror_read.json is the synthetic-twin read, NOT the actual-monkey policy record.

**Active:** A1, A2, A5, A6, A7, A8, A9 still running.

**Blocked:** none.

**Next:** integrate A1–A9 as they land → I1 (wrist consolidation) → I2 (spec pass-2; A3+A4 slots fillable) → I3.

## CHECKPOINT 2026-09-24 (T4) — A6 + A7 integrated

**Verified:**
- A6 (evidence taxonomy) PASS 6/6, receipt re-verified: 32-row evidence table; prediction held (zero rows carry measured-anatomy attachment evidence); probitive-claim scan zero hits. FINDING S-1: the bilateral asymmetry is SOURCE-AUTHORED — in raw XML, 14/16 pairs exact z-mirrors; BICshort-P6 (Δ2.732mm) and FCU-P2 (Δ1.030mm) are not — exactly the two pairs A4 measured as the fit's only asymmetries. Fit inherits, does not create.
- A7 (tendon paths) PASS 5/5, all five scripts re-verified: 42/42 L0 bit-identical; 42/120 comparability reproduced; candidate deltas recomputed 42/42 exact WITHOUT re-running the dead candidate; only BRD/BRD_l nonzero (−0.90164mm/−0.901337mm).
- STRUCTURAL FACT for I3: of 18 tendons touching the 32 sites, only BRD/BRD_l have derived lengths/arms; the 16 grasp-critical ones are null on unresolved hand/ulna bodies. Grasp qualification is blocked deeper than the 2 ambiguous wrist sections — hand/ulna body resolution is the load-bearing missing piece.

**Active:** A1, A2, A5, A8, A9 still running.

**Blocked:** none mechanically; substantive blockers accumulating for I3 (hand/ulna resolution; wrist ambiguity; Astra decisions).

**Next:** integrate A1/A2/A5/A8/A9 → I1 → I2 (fill A3/A4/A6/A7 slots) → I3.

## CHECKPOINT 2026-09-24 (T5) — A9 integrated (reproduction secured)

**Verified:**
- A9 (Session-5 reproduction) PASS 6/6: 49/49 falsifiers green (8.2 s); 9/9 session-5 artifacts byte-identical; determinism 2x regen 12/12; H-1 CONFIRMED at producer level; candidate record byte-identical (failure stands; dc mirror-signs recorded: +2.02 right / -2.02 left).
- A9 quarantine used a temporary .tmp swap + junction (hardcoded paths); coordinator INDEPENDENTLY verified the restore: live .tmp/anatomy_compiler is a real dir (no junction), 36/36 code+runs files hash-match the snapshot MANIFEST.
- Findings banked: S6 runs/-mkdir environment gap; 3 STALE session-4 side artifacts labeled (grounded_chimanoid / mirror_read / synthetic_twin — never cite as session-5 outputs); absolute-path hardcoding as reproducibility gap (Astra proposals).

**Active:** A1, A2, A5, A8 still running.

**Blocked:** none mechanically.

**Next:** integrate A1/A2/A5/A8 → I1 → I2 (fill all landed slots) → I3.

## CHECKPOINT 2026-09-24 (T6) — A8 integrated

**Verified:**
- A8 (moment arms + transmission) PASS 6/6, scripts re-verified by coordinator fresh re-run: zero-arm law holds at 2.776e-17 m; FD crosscheck max 5.551e-11 < 1e-9 (analytic values bit-exact vs packet); BRD/BRD_l L0 inside lengthrange' with ~+1 mm headroom; all 14 arm-chain q-ranges verbatim vs XML.
- ERRATUM E-2 banked: report-05's straight-tendon zero-arm explanation is imprecise — zero deltas hold because bends sit on UNRESOLVED owners (elbow=ulna, wrists=hand_r/l), not straightness.
- TRANSMISSION FACT sharpens the I3 blocker: grasp transmission set EMPTY; 562/702 arm pairs NaN = coverage gap at exactly the grasp-relevant joints (undefined, not dead). Hand/ulna body resolution is THE unlock for any wrist/elbow transmission claim.
- Doc-code drift note: compiler.py FD eps=1e-5 vs DERIVATION 8.3's 5e-7 (passes either way).
- Board edit slip during integration (A7 bullet briefly overwritten) — caught and restored within the same pass; verified present.

**Active:** A1, A2, A5 still running.

**Blocked:** none mechanically.

**Next:** integrate A1/A2/A5 -> I1 (wrist) -> I2 (spec pass-2; A3/A4/A6/A7/A8/A9/A10 slots ready) -> I3.

## CHECKPOINT 2026-09-24 (T7) — A1 integrated (left wrist ambiguity resolved into evidence)

**Verified:**
- A1 (left wrist) PASS 4/4, receipt re-verified (fresh re-run of recompute_loops.py; integrity clean). Prediction CONFIRMED; falsifier not fired.
- CORE EVIDENCE: ECRB_l-P3 / ECRL_l-P3 ambiguity = genuine needle-sliver pocket (coincident vertices @0.000mm; window [51.122,57.723)mm). BOTH identified loops agree: OUTSIDE, >=4.83mm vs 1mm margin (ECRB_l-P3 +4.83/+4.87mm; ECRL_l-P3 +5.51/+5.51mm). The unresolved class is mechanically honest; the underlying geometry is unambiguous (outside).
- Resolution options now evidence-backed for Astra: degenerate-loop exclusion rule / loop-agreement rule / permanent-uncertainty acceptance. NOT ours to choose.
- Benign quirk recorded: _chain_closed_loops seed-triangle double-count in reported tri lists (harmless here).
- Board-edit slip #2 during append (transmission bullet briefly overwritten) — caught+restored same pass, verified by grep (3/3 bullets present). Lesson applied: future board appends anchor on the file's tail anchor line, not on a sibling bullet.

**Active:** A2, A5 still running.

**Blocked:** none mechanically.

**Next:** A2 lands -> I1 (bilateral consolidation of the wrist finding) -> A5 -> I2 (spec pass-2) -> I3.

## CHECKPOINT 2026-09-24 (T8) — A2 integrated; I1 wrist finding CONSOLIDATED

**Verified:**
- A2 (right wrist) PASS 4/4, receipts re-run by coordinator (falsifier not fired reproduces; integrity clean).
- I1 DELIVERED: findings/I1_wrist_ambiguity.md — bilateral consolidation. All four ambiguous sites OUTSIDE >=4.83mm under BOTH loops; verdict-invariant (Δ<=0.077mm); mechanism = unwelded seam (1,255 duplicated-coordinate vertices mesh-wide) x no-bridging law; A1/A2 numbers mirror-consistent to sub-µm. Projection labeled NOT-a-reclassification: resolution -> 6/1/9/0 per side; Candidate-C projection stays dead.
- Resolution paths P1/P2/P3/P5 evidence-complete; P4 (hull SECTION_T extension) blocked on Astra — the one baseline change that would add independent confirmation.

**Active:** A5 (containment authority + uncertainty) — the last wave-1 audit.

**Blocked:** none mechanically; Astra queue now holds: wrist resolution rule (I1), hand/ulna body resolution (A7/A8 structural), P4 authorization, S6 self-containment + path relativization (A9), candidates-packet self-hash (H-1 residual).

**Next:** A5 -> I2 (qualification-spec pass-2, fill all landed slots) -> I3 (consolidated Astra blocker report).

## CHECKPOINT 2026-09-24 (T9, FINAL for wave 1) — A5 integrated; I2 + I3 DELIVERED. Campaign goal state reached.

**Verified:**
- A5 (containment authority) PASS 6/6, all scripts re-run by coordinator (49/49 synthetic matrix; full recompute reproduces every verdict; candidate41 decomposition exact). ERRATUM E-3: "~41um" unsupported; exact = 67.147um single violation/side (ECRL-P3 @ t=0.35).
- I2: QUALIFICATION_SPEC.md v1 (pass-2) — all PENDING slots resolved; T3/T4/T5 SATISFIED; T1 decision-ready; T2 evidence-complete; T6/T7 structurally blocked on hand/ulna; T8 nearly.
- I3: BLOCKER_REPORT.md — decision queue D1..D6, head blocker = hand/ulna body resolution (D2); explicitly-not-requested list faithful to frozen boundaries.
- WAVE 1 COMPLETE: 10/10 audits PASS, every receipt independently re-verified by the coordinator, every integration committed (commit chain 0ad24b02 -> d43b6b00 -> 8ecc099b -> 833df5d4 -> 810ae171 -> f69d7035 -> 9da311d3 -> 0d2c73be -> this commit).
- Baseline integrity clean throughout; live .tmp tree verified intact (36/36 hashes) after A9's quarantine.

**Active:** none — all subagents complete; no spin.

**Blocked (by design, pending Astra):** D1 wrist rule; D2 hand/ulna session; D3 T-set approval; D4 self-hash rules; D5 package self-containment; D6 errata sheet.

**Next (on Astra answers):** execute the chosen wrist rule (pure classification-record change or authorized SECTION_T extension); prepare the hand/ulna evidence-session brief (landmarks + falsifiers) for Astra sign-off; P7 mechanical package work on authorization; ERRATA.md on authorization. If the session dies here: resume from this file + TASK_BOARD.md; every audit is re-runnable from its brief.md.

## CHECKPOINT 2026-09-24 (T10) — WAVE 2 OPENED: D2 authorized (hand/ulna body resolution)

**Architect decisions received:**
- D2 AUTHORIZED as the next campaign goal (body-resolution evidence package for ulna/ulna_l/hand_r/hand_l).
- E-3 CONFIRMED (67.147 um/side; failure unchanged). ERRATA authorized additively -> ERRATA.md written (E-1/E-2/E-3 + stale-artifact appendix, receipts linked, originals preserved).
- Wrist finding stands; NO hull extension; D1 pending; D3-D5 undecided pending exact contracts.
- New standing laws: preregistration-before-candidate-evaluation; fail conditions (source-contradiction / unexplained-transform / multiple-equally-supported-owners); moment-arm utility ban; read-only scope; stop = decision-ready package.

**Verified:** ERRATA.md + board wave-2 section + B1-B4 assignment rows committed.

**Active (dispatched at T10, background):** B1 source anatomy · B2 ownership chain · B3 mechanical requirements · B4 challenge protocol.

**Blocked:** none (four independent evidence tasks all ready).

**Next:** collect B1-B4 -> verify receipts -> I5: assemble BODY_RESOLUTION_MAP.md (one proposed map, preregistered per the architect's law, evidence+uncertainty per entry, smallest implementation change, explicit blockers) -> return for architectural approval. Ten-slot ceiling available if findings expose more independent work.

## CHECKPOINT 2026-09-24 (T11) — B3 integrated

**Verified:**
- B3 (mechanical requirements) PASS 5/5, coordinator spot-verified against the fit packet's own reason strings ("body ulna: no fitted scale (endpoints not declared)" etc. — the unresolved cause is UNDECLARED LANDMARKS, not missing geometry/contracts).
- Key structure: source tree humerus -> ulna -> radius -> hand; ulna owns elbow_flexion(_l); hands own the wrist triples; radius owns ZERO coordinates. Target FK terminates at wrist (no digits); fitted elbow/wrist origins already equal the target joints exactly; 30 sites unplaced (10 ulna + 5 hand per side).
- Classification: all GEOMETRY gaps = NEEDS-NEW-EVIDENCE within existing contracts. ONE structural tension: ulna resolution re-anchors radius.P (first-child closure JOINT_EPS=1e-9) -> supersedes the A4-verified radius record (flag F-2/F-4 for Astra).
- Architectural flags: F-1 digits out of scope; F-2 ulna/radius anchor partition ruling; F-3 hand-region landmark evidence pending B1; F-4 baseline supersession discipline.

**Active:** B1, B2, B4 still running.

**Blocked:** none.

**Next:** integrate B1/B2/B4 -> I5 BODY_RESOLUTION_MAP.md (preregistered per architect law) -> return for approval.

## CHECKPOINT 2026-09-24 (T12) — B2 integrated

**Verified:**
- B2 (ownership chains) PASS 6/6; coordinator fresh re-run reproduces the unlock arithmetic: D2-only -> 12/16 comparable; D2+thorax -> 16/16; thorax-only -> 4/16 (blast radius 40 records). Integrity clean.
- Earliest breakers: ECRB/ECRL/FCU at TERMINAL hand sites; FCR idx2; ECU idx1 (ULNA) + second blocker terminal hand; PT idx1 (ulna, only blocker); BIClong/BICshort idx0 THORAX (no D2 sites in their chains at all).
- Census 42/120 triple-confirmed (A7 + frozen experiment record + B2).
- Packet-wide: 122 nonzero finite arms are ALL leg tendons — zero informative forearm arms (E-2 again).
- Structural negative: no pronation/supination coordinate in the model (radius owns zero joints); post-D2 arms exist only about elbow_flexion(_l) and the wrist triples; D2 also repairs BRD's null elbow arms.

**Active:** B1, B4 still running.

**Blocked:** none.

**Next:** B1+B4 -> I5 BODY_RESOLUTION_MAP.md.

## CHECKPOINT 2026-09-24 (T13) — B1 integrated (source anatomy; classification settled)

**Verified:**
- B1 PASS 5/5; coordinator fresh re-run of all 5 scripts reproduces every headline number; integrity clean.
- CLASSIFICATION SETTLED: (I) missing identifiers — the four bodies are authored ANCHOR-ONLY in the correspondence (prox==dist, axial_unresolved=True, refusals=0; live rebuild == shipped digest 52c92fe0...) and fail because the PACK declares no distal joint for them. Not (G) missing geometry. Prediction's falsifier prong fired honestly (authoring exists; pack data is the break); spirit held ((I) dominates; digits absent_in_source).
- Source facts: chain humerus->ulna->radius->hand; ulna segment is a 2.31 cm elbow-head piece (radius carries the 29.2 cm forearm to the hand origin at 0.2920 m); ulna 0.729 kg / hand 0.4575 kg inertials present; 30 tendon sites (10/ulna incl. ECU-P2/3/4 interior; 5/hand, ECRB/ECRL/FCR/FCU-P4 terminal, ECU-P6 terminal); hands have 27 welded hand-skeleton meshes, ZERO digit joints.
- Target facts: hand skin EXISTS as a 111.4 mm connected paddle distal to each wrist (47.1x18.1 mm far end) but pack-owned by elbow (0-41 mm) and tail_base/spine_lower (41-111 mm) — ownership mis-attribution to be treated as diagnostic, not authority. Wrist band itself = forearm skin (7 distal verts <= 1.8 mm). Rig hand_tip law measures upper-arm skin — unusable.
- I-map implication: resolution needs AUTHORIZED distal landmarks authored from the mesh evidence (the paddle) + the B3 F-2 anchor-partition ruling — measurement alone cannot close it.

**Active:** B4 (challenge protocol) — last wave-2 agent.

**Blocked:** none.

**Next:** B4 -> I5 BODY_RESOLUTION_MAP.md.
