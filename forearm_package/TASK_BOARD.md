# FOREARM PACKAGE — DURABLE TASK BOARD

**Campaign:** complete the forearm anatomy package needed to qualify the monkey's physical grasp for climbing.
**Coordinator:** ZCode execution lead (GLM). **Architect:** Astra (external — owns all architectural decisions; this campaign reports evidence, it does not decide).
**Opened:** 2026-09-24. **Baseline:** Session 5 (frozen). **Input revision:** `baseline_snapshot/MANIFEST.json` (44 files, all crosschecks green).

## FROZEN BOUNDARIES — no agent may cross

- Session-5 baseline unchanged. Candidate C FAILED its declared criteria (~41 µm over the ≤ −1 mm clearance law) — the failure stands.
- No second fitting candidate. No anatomical-site displacement. No margin relaxation.
- Preserve verbatim source coordinates, the four containment classes, v5 provenance, endpoint roles, separate XML/fitted-packet hashes.
- `mechanical_qualification: false` on every site until Astra-approved tests pass.
- No physics, attachment-semantics, muscle-limit, or architecture changes — those go to Astra with evidence + smallest proposed change.
- New qualification criteria cannot retroactively rescue Candidate C.

## KNOWN STATE (Session-5 receipts, admission_actual_monkey.json + report 05)

- **Loop authority (baseline), per side:** 6 inside / 1 tight (`PT-P3`, `PT_l-P3`) / 7 outside / 2 ambiguous.
- **Ambiguous wrist sections:** right `ECRB-P3` + `ECRL-P3`; left `ECRB_l-P3` + `ECRL_l-P3` — wrist-level sections yield multiple ownership-identified loops (section identification, not placement).
- **Loop outside, right:** BIClong-P9, BICshort-P6, BRD-P2, BRD-P3, ECRB-P2, ECRL-P2, PT-P5 (7). Hull diagnostic (per side): 5 outside / 0 tight / 8 unresolved — loop sharpens hull (BIClong-P9, BICshort-P6 outside at unsampled axials; PT-P3 tight).
- **Candidate C (evaluated, NOT applied):** db=+6.24 mm, dc=±2.02 mm, mirror-symmetric; loop authority would read 0 outside / 14 inside / 0 tight / 2 ambiguous; FAILED by ~41 µm. Effects recorded: max |Δ path length| 0.90 mm (BRD); max |Δ moment arm| ≈ 0 (straight-tendon zero-arm law); 42/120 tendons with fully-resolved comparable chains.
- **H-1 RESOLVED at snapshot:** `fitted_packet_sha256` (a4475550…) = sha256 of `actual_monkey_fit.json` (field names the fit packet, not the candidates packet). No byte drift. A9 confirms independently. Residual observation for Astra: the candidates packet carries no self-hash.
- Site naming: right side unsuffixed (`BRD-P2`), left side `_l` (`BRD_l-P2`). Right body is `radius`, left is `radius_l`. 16 sites/side, 32 total. Roles: first_endpoint/last_endpoint/waypoint (path positions only — packet establishes no anatomical proximal/distal orientation).
- **ERRATUM E-1 (A3, verified 2026-09-24):** report-05 line 29 says "8 last-endpoints **per side**" — measured law is **4 last-endpoints per side** (right 4: BIClong-P11, BICshort-P8, BRD-P3, PT-P5; left mirrored), 0 first-endpoints, 12 waypoints per side. The report's 8/0/24 numbers are correct as TWO-SIDE TOTALS; only the "per side" scoping is wrong. Baseline packet data itself is fully self-consistent (A3: 32/32 exact float identity vs XML, units verbatim, one uniform provenance block, canonical-hash recipe reproduced).
- Observation (A3, no effect on the 32): XML holds 937 `<site>` elements = 468 named sites + 469 unnamed tendon-path refs; wording that calls 468 "tendon-referenced sites" is loose but not contradictory (469 refs cover the 468 named sites).
- **Bilateral asymmetry is concentrated (A4, verified):** of 16 pairs, only TWO carry real asymmetry — BICshort-P6 0.6306 mm and FCU-P2 0.2447 mm; the other 14 pairs differ ≤ 2 nm. Plane x=0 confirmed from the pack's own spine joints (all exactly x=0.0). Caveat on record: `runs/mirror_read.json` is the SYNTHETIC-twin read — never cite it as the actual-monkey handedness record.
- **Transform semantics (A4):** exported `R` is scale×rotation by construction (uniform s≈0.2217; RᵀR = s²·I, zero shear; Q=R/s proper det +1; det(R)=s³) — consistent with `R = Bp @ diag(scale) @ Bᵀ`, not a bug.

## ASSIGNMENTS

| id | assignment | agent dir | status | verdict | receipt |
|----|------------|-----------|--------|---------|---------|
| I0 | durable snapshot + manifest + board (coordinator) | `baseline_snapshot/` | DONE | PASS (4/4 crosschecks) | `MANIFEST.json` |
| A1 | left ambiguous wrist section — independent investigation | `audits/A1_left_wrist` | DISPATCHED | — | `report.md` |
| A2 | right ambiguous wrist section — independent investigation | `audits/A2_right_wrist` | DISPATCHED | — | `report.md` |
| A3 | 32-site audit vs source XML (units, identities, endpoint roles) | `audits/A3_site_audit` | DONE | **PASS** (32/32 identity/units/roles/provenance; canonical hash reproduced) + **ERRATUM E-1** on report-05 role-count scoping | `report.md` (receipt re-verified by coordinator) |
| A4 | local-to-world transforms + bilateral correspondence | `audits/A4_transforms` | DONE | **PASS 5/5** (falsifier not triggered) — reconstruction max 1.15e-9 m export / 5.6e-17 m full precision; mirror max 0.6306 mm (BICshort-P6), mean 0.0547 mm; mode `preserve` recorded (`actual_monkey_fit.json:119-120`, chirality_det +1) | `report.md` (receipt re-verified by coordinator) |
| A5 | containment authority, signed distances, uncertainty budget, four classes | `audits/A5_containment` | DISPATCHED | — | `report.md` |
| A6 | anatomical attachment evidence vs geometric containment vs fitted assumption | `audits/A6_evidence` | DISPATCHED | — | `report.md` |
| A7 | tendon-path and length consequences (existing model, baseline) | `audits/A7_paths` | DISPATCHED | — | `report.md` |
| A8 | moment arms + force transmission over declared pose range | `audits/A8_arms` | DISPATCHED | — | `report.md` |
| A9 | independent reproduction of Session 5 + regression receipts + H-1 confirmation | `audits/A9_reproduce` | DISPATCHED | — | `report.md` |
| A10 | qualification specification v0 (DRAFT — not approved) | `audits/A10_spec` | DONE (v0; pass-2 = I2) | **PASS 6/6** — 14 ASTRA-APPROVES placeholders, zero invented criteria; independently re-derived ERRATUM E-1's role-count law from artifacts (0 first / 4 last / 12 waypoint per body) | `qualification_spec_v0.md` + `report.md` |

## INTEGRATION QUEUE (coordinator-only)

- **I1:** fold A1+A2 into one wrist-section ambiguity finding (shared integration; the two investigations stay independent until compared).
- **I2:** qualification-spec pass-2 — fold verified audit findings into the A10 draft.
- **I3:** consolidated blocker report for Astra: every unresolved item with the specific missing evidence + smallest proposed change. Campaign-terminal deliverable.

## RULES OF THE BOARD

- Audits read ONLY `baseline_snapshot/` (read-only) and write ONLY their own `audits/<id>/` dir.
- Every report carries: verdict per acceptance criterion, evidence (file+line+numbers), explicit uncertainty, preserved failures, receipts (commands + output).
- A finding is integrated only after its receipt verifies (numbers reproduce, paths exist).
- File-ownership conflicts are impossible by construction; anything shared goes through the coordinator.
