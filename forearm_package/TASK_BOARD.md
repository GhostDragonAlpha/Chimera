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
- **REPRODUCIBILITY (A9, verified):** Session 5 fully reproduces — 49/49 falsifiers green in 8.2 s (Python 3.14.3, numpy 2.2.6, matplotlib 3.10.8); all 9 session-5 artifacts regenerate byte-identical; two full regenerations agree 12/12. H-1 confirmed at producer level (`actual_target_fit.py:648-649` hashes written bytes after `write_json`). Candidate record byte-identical: db=+6.24 mm both sides, dc=+2.02 (right) / −2.02 (left), objective 4.34689e-07 m², max displacement 6.5588 mm, passed=false both sides.
- **STALE-ARTIFACT LABEL (A9 finding):** `runs/grounded_chimanoid.json`, `runs/mirror_read.json`, `runs/synthetic_twin.json` are SESSION-4 side artifacts frozen into the snapshot — they differ from regeneration (+1136 bytes each, 12 structural diffs = the session-4 admission-schema rename) because session 5 never regenerated them. Expected staleness, not determinism drift; cite only as session-4 history (A4's mirror_read.json caveat is the same fact from the other side).
- **PACKAGE GAPS for Astra (A9; proposals, not changes):** (1) S6 assumes `runs/` exists — first pristine run fails with FileNotFoundError until the dir is created (suite not self-contained); (2) scripts hardcode absolute paths (`run_tests.py:16`, `actual_target_fit.py:58`, `synthetic_fixtures.py:28`, `mesh_target.py:31-32`) — reproduction required a path junction; a path-relativized package would reproduce with zero ceremony.
- Site naming: right side unsuffixed (`BRD-P2`), left side `_l` (`BRD_l-P2`). Right body is `radius`, left is `radius_l`. 16 sites/side, 32 total. Roles: first_endpoint/last_endpoint/waypoint (path positions only — packet establishes no anatomical proximal/distal orientation).
- **ERRATUM E-1 (A3, verified 2026-09-24):** report-05 line 29 says "8 last-endpoints **per side**" — measured law is **4 last-endpoints per side** (right 4: BIClong-P11, BICshort-P8, BRD-P3, PT-P5; left mirrored), 0 first-endpoints, 12 waypoints per side. The report's 8/0/24 numbers are correct as TWO-SIDE TOTALS; only the "per side" scoping is wrong. Baseline packet data itself is fully self-consistent (A3: 32/32 exact float identity vs XML, units verbatim, one uniform provenance block, canonical-hash recipe reproduced).
- Observation (A3, no effect on the 32): XML holds 937 `<site>` elements = 468 named sites + 469 unnamed tendon-path refs; wording that calls 468 "tendon-referenced sites" is loose but not contradictory (469 refs cover the 468 named sites).
- **Bilateral asymmetry is concentrated (A4, verified):** of 16 pairs, only TWO carry real asymmetry — BICshort-P6 0.6306 mm and FCU-P2 0.2447 mm; the other 14 pairs differ ≤ 2 nm. Plane x=0 confirmed from the pack's own spine joints (all exactly x=0.0). Caveat on record: `runs/mirror_read.json` is the SYNTHETIC-twin read — never cite it as the actual-monkey handedness record.
- **Transform semantics (A4):** exported `R` is scale×rotation by construction (uniform s≈0.2217; RᵀR = s²·I, zero shear; Q=R/s proper det +1; det(R)=s³) — consistent with `R = Bp @ diag(scale) @ Bᵀ`, not a bug.
- **FINDING S-1 (A6, cross-confirmed by A4): the bilateral asymmetry is SOURCE-AUTHORED.** In the raw XML, 14/16 left/right pairs are exact z-mirrors; BICshort-P6 (Δ 2.732 mm) and FCU-P2 (Δ 1.030 mm) are not — the same two pairs (and only those) that A4 measured as the fit's only real asymmetries (0.63 mm / 0.24 mm). The fit inherits the source's authored asymmetry; it does not create it.
- **Evidence taxonomy (A6):** zero of 32 sites carry measured-anatomy attachment evidence — every row = source(coordinates+membership+role) + fit(transform+scale+landmarks) + containment(geometric only). Chain resolution: only BRD chains fully resolved; ECRB/ECRL/FCR/FCU terminate on the unresolved hand bodies; ECU has 4 unresolved sites on ulna+hand; BIC origins authored on thorax. Third independent confirmation of E-1 (4 last-endpoints/side).
- **STRUCTURAL FACT (A7, head blocker input): only BRD/BRD_l are functional forearm chains in the packet.** 18 tendons touch the 32 sites; 16 of them (ECRB, ECRL, ECU, FCR, FCU per side; PT ends on unresolved ulna) have NULL rest length, NULL muscle length, NULL moment arms — `path_incomplete: unresolved_bodies`. The packet claims no functional wrist moment arm except through BRD (0.088831 m / 0.088836 m, bit-identical recompute). Grasp qualification is therefore blocked on hand/ulna body resolution, deeper than the 2 ambiguous wrist sections. Comparability census: 42/120 comparable; 78 not (thorax-only 40, ulna-only 10, hand-only 8, hand+ulna 2, thorax+ulna 2, talus-only 10, talus+toes 6).
- **ERRATUM E-2 (A8, verified):** report-05 §4-C's "a straight tendon has zero moment arm about any joint" is IMPRECISE as the explanation of the candidate's zero arm-deltas — the paths bend 20–65° at elbow entries; the zero deltas hold because no finite chain crosses a *resolved* joint boundary (bends sit on unresolved owners), not because of straightness. Numbers unaffected; documentation causality corrected.
- **TRANSMISSION FACT (A8, sharpens A7's structural fact):** grasp-relevant transmission set is EMPTY. 140/702 arm pairs finite (all exactly 0.0 or ≤1.4e-17 noise); 562/702 NaN — a COVERAGE GAP at exactly the grasp-relevant joints (elbow_flexion owned by unresolved ulna; wrist triples by unresolved hand_r/l). Elbow + wrist transmission is UNDEFINED, not dead. BRD L₀ sits inside lengthrange′ with ~+1 mm headroom. Doc-code note: compiler.py L46/L528 FD ε=1e-5 vs DERIVATION §8.3's 5e-7 (passes either way; recorded as drift).

## ASSIGNMENTS

| id | assignment | agent dir | status | verdict | receipt |
|----|------------|-----------|--------|---------|---------|
| I0 | durable snapshot + manifest + board (coordinator) | `baseline_snapshot/` | DONE | PASS (4/4 crosschecks) | `MANIFEST.json` |
| A1 | left ambiguous wrist section — independent investigation | `audits/A1_left_wrist` | DISPATCHED | — | `report.md` |
| A2 | right ambiguous wrist section — independent investigation | `audits/A2_right_wrist` | DISPATCHED | — | `report.md` |
| A3 | 32-site audit vs source XML (units, identities, endpoint roles) | `audits/A3_site_audit` | DONE | **PASS** (32/32 identity/units/roles/provenance; canonical hash reproduced) + **ERRATUM E-1** on report-05 role-count scoping | `report.md` (receipt re-verified by coordinator) |
| A4 | local-to-world transforms + bilateral correspondence | `audits/A4_transforms` | DONE | **PASS 5/5** (falsifier not triggered) — reconstruction max 1.15e-9 m export / 5.6e-17 m full precision; mirror max 0.6306 mm (BICshort-P6), mean 0.0547 mm; mode `preserve` recorded (`actual_monkey_fit.json:119-120`, chirality_det +1) | `report.md` (receipt re-verified by coordinator) |
| A5 | containment authority, signed distances, uncertainty budget, four classes | `audits/A5_containment` | DISPATCHED | — | `report.md` |
| A6 | anatomical attachment evidence vs geometric containment vs fitted assumption | `audits/A6_evidence` | DONE | **PASS 6/6, zero falsifier hits** — 32-row evidence table; prediction held (no row carries measured-anatomy attachment evidence); probative-claim scan clean (all "qualification" negated) | `report.md` + `table.md/csv` (receipt re-verified by coordinator) |
| A7 | tendon-path and length consequences (existing model, baseline) | `audits/A7_paths` | DONE | **PASS 5/5** (falsifier not fired) — 42/42 L₀ bit-identical; 42/120 comparability reproduced + 78 enumerated in 13 categories; candidate Δ recomputed 42/42 exact vs record without re-running | `report.md` (all 5 scripts re-verified by coordinator) |
| A8 | moment arms + force transmission over declared pose range | `audits/A8_arms` | DONE | **PASS 6/6** — zero-arm law 2.776e-17 m; FD crosscheck 5.551e-11 < 1e-9 (analytic matches packet bit-exactly); BRD margins +0.986/+0.975 mm; **transmission set EMPTY — wrist/elbow arms are NaN (undefined) on unresolved owners, not zero** | `report.md` (scripts re-verified by coordinator) |
| A9 | independent reproduction of Session 5 + regression receipts + H-1 confirmation | `audits/A9_reproduce` | DONE | **PASS 6/6** — 49/49 falsifiers green (8.2 s); 9/9 session-5 artifacts byte-identical; determinism proven (2 regenerations, 12/12 identical); H-1 CONFIRMED (producer lines quoted); candidate record byte-identical, failure stands; live `.tmp` restore independently verified by coordinator (no junction, 36/36 hashes match) | `report.md` + `receipts/` |
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
