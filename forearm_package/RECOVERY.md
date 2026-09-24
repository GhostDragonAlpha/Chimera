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
