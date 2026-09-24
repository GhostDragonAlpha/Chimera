# I3 — CONSOLIDATED BLOCKER REPORT FOR ASTRA

**Campaign:** forearm anatomy package for monkey grasp qualification (climbing).
**Date:** 2026-09-24. **Coordinator:** ZCode execution lead (GLM). **Architect (decision owner):** Astra.
**State at issue:** 10/10 audit assignments executed, receipts independently re-verified, integrated. Baseline frozen and untouched (integrity receipt: `git status --porcelain -- forearm_package/baseline_snapshot` empty throughout; live `.tmp` tree hash-verified 36/36 after the one quarantine operation). All campaign work committed on branch `forearm-package-20260924` (see RECOVERY.md for the commit chain).

**Nothing below is decided.** Each item names the exact missing evidence or decision, and the smallest proposed change. Per the frozen boundaries: no second candidate, no site displacement, no margin relaxation, `mechanical_qualification` remains `false`, Candidate C's failure stands (exact breach: **67.147 µm**/side at ECRL-P3 @ t=0.35 — the "~41 µm" in report 05 is erratum E-3).

---

## WHAT IS SETTLED (no decision needed — verified facts)

1. **Source fidelity:** all 32 sites byte-exact vs `chimanoid.xml` (coordinates, units, tendon identity, path indices, roles; canonical-hash recipe reproduced). [A3]
2. **Transforms + bilateral:** reconstruction exact (1.15e-9 m export precision); fit respects bilateral symmetry; the only two asymmetries (BICshort-P6, FCU-P2) are authored in the source XML. [A4, A6]
3. **Containment machinery:** four-class law verified law-for-law + 49/49 synthetic boundary matrix + full recompute reproduces every per-site verdict on both authorities; uncertainty budget measured (loop-edge sagitta 29–45 µm median; hull chord 187–256 µm). [A5]
4. **Wrist ambiguity:** mechanically honest `unresolved`, geometrically one-sided — all four sites OUTSIDE ≥ 4.83 mm under both identified loops, verdict-invariant (Δ ≤ 0.077 mm); cause = unwelded seam (1,255 duplicated-coordinate vertices mesh-wide) × the no-bridging law. [A1 ⊕ A2 → `findings/I1_wrist_ambiguity.md`; independently corroborated by A5]
5. **Evidence taxonomy:** zero of 32 sites carry measured-anatomy attachment evidence; no artifact language overclaims. [A6]
6. **Reproduction:** Session 5 regenerates byte-identically, 49/49 falsifiers green, deterministic across regenerations; all hash invariants confirmed at producer level. [A9]
7. **Paths/arms where defined:** BRD/BRD_l lengths bit-identical, ~+1 mm excursion headroom; analytic arms FD-verified to 5.6e-11; candidate zero-arm law holds. [A7, A8]
8. **Errata:** E-1 role counts (4/side, not 8/side), E-2 zero-arm causality (unresolved owners, not straightness), E-3 shortfall number (67.147 µm, not ~41 µm). Documentation-level; artifacts remain the record.

## DECISIONS REQUESTED (ranked; smallest change first)

**D1 — Wrist resolution rule** (unblocks T1; evidence complete at `findings/I1_wrist_ambiguity.md`)
Options: (a) loop-agreement verdict; (b) degenerate-loop exclusion threshold; (c) authorize the hull `SECTION_T` band extension (the one baseline change: pure measurement past 50.084 mm; adds the diagnostic's independent voice); (d) permanent documented uncertainty (T1.2 amended). (a)/(b) yield OUTSIDE for all four sites on current evidence → per side would read 6 inside / 1 tight / 9 outside / 0 unresolved (projection, not a reclassification).

**D2 — Hand/ulna body resolution** (HEAD BLOCKER; unblocks T6/T7 for 16 of 18 grasp tendons)
Fact: ECRB, ECRL, ECU, FCR, FCU (per side) terminate on unresolved `hand_*`; PT crosses unresolved `ulna*`; 562/702 moment-arm pairs are NaN — wrist/elbow transmission is undefined, not zero. Without resolving those bodies, no mechanical grasp qualification of the wrist/digit paths can exist. Proposal: authorize a new evidence session (correspondence landmarks for the four bodies, same authored-landmark discipline; new fit session under the same falsifier regime; new revision chain — the frozen session-5 baseline is untouched).

**D3 — Qualification test-set approval** (the gate itself)
`QUALIFICATION_SPEC.md` v1 (pass-2) holds the T1–T8 structure with statuses: T3/T4/T5 satisfied; T1 decision-ready (D1); T2 evidence-complete (A6 taxonomy — adoption requested); T6/T7 blocked (D2); T8 nearly satisfied (D4). Astra approves pass values, the sign-off record, and the evidence-class taxonomy.

**D4 — Package integrity rules** (small, mechanical)
Candidates-packet self-hash rule (future revisions hash their own written bytes); MANIFEST self-coverage rule.

**D5 — Package self-containment authorization** (mechanical; touches frozen code)
S6 `runs/` auto-creation (first pristine run currently fails with FileNotFoundError); path relativization (`run_tests.py:16`, `actual_target_fit.py:58`, `synthetic_fixtures.py:28`, `mesh_target.py:31-32`); a one-command reproduce script. No measured values change.

**D6 — Errata sheet** (documentation only): E-1/E-2/E-3 + stale-artifact labels (grounded_chimanoid / mirror_read / synthetic_twin are session-4 history), as `ERRATA.md` in the package — frozen reports stay unedited.

## EXPLICITLY NOT REQUESTED

Any second fitting candidate; any site displacement; any margin relaxation; any physics/attachment-semantics/muscle-limit change; any retroactive rescue of Candidate C.

## EVIDENCE INDEX

| finding | artifact |
|---|---|
| wrist ambiguity (consolidated) | `findings/I1_wrist_ambiguity.md` ← `audits/A1_left_wrist/`, `audits/A2_right_wrist/` |
| source fidelity + E-1 | `audits/A3_site_audit/report.md` |
| transforms/bilateral + S-1 | `audits/A4_transforms/report.md` |
| containment law + budget + E-3 | `audits/A5_containment/report.md` (incl. `receipts/candidate41.json`) |
| evidence taxonomy | `audits/A6_evidence/report.md` + `table.md` |
| paths/comparability | `audits/A7_paths/report.md` |
| arms/transmission + E-2 | `audits/A8_arms/report.md` |
| reproduction + H-1 | `audits/A9_reproduce/report.md` |
| spec v0 | `audits/A10_spec/qualification_spec_v0.md` |
| spec v1 (pass-2) | `QUALIFICATION_SPEC.md` |
| task board / known state | `TASK_BOARD.md` |
| checkpoint log | `RECOVERY.md` |
| frozen baseline | `baseline_snapshot/` + `MANIFEST.json` |
