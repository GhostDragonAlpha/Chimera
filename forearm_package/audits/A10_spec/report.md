# A10 REPORT — qualification specification v0 (DRAFT, NOT APPROVED)

**Agent:** A10 (audit) · **Date:** 2026-09-24 · **Deliverables:** `brief.md` (verbatim copy of the dispatch brief), `qualification_spec_v0.md`, this report.
**Input:** `baseline_snapshot/` at MANIFEST revision `git_head_at_snapshot c70b7a6c` — read-only, untouched (receipt below). A1–A9 had only their `brief.md` files present at audit time (no reports yet), so all cross-audit slots are explicit `[PENDING A<n>]` markers (counts in the spec: A1×5, A2×5, A3×3, A4×2, A5×4, A6×2, A7×3, A8×3, A9×6).

## ACCEPTANCE-CRITERION VERDICTS

**(1) All six sections complete — PASS.** `qualification_spec_v0.md` carries §1 Scope & definitions (mission, evidence ladder as law with verbatim anchors from report 05 §6 / `preregistration.interpretation_limit` / DERIVATION §12; terms: site, role, containment class, authority, comparable chain, mechanical_qualification — each defined from artifact text), §2 test categories T1–T8 (each with purpose, exact MANIFEST paths+sha256 inputs, pass-criterion TEMPLATE with `[ASTRA-APPROVES: …]` placeholders, falsifier style, current status), §3 current-state table (11 rows), §4 blockers (a)–(e), §5 non-goals, §6 proposals P1–P5 (smallest-change first, each with what it changes / what evidence gates it / what it does NOT change).

**(2) Every current-state row carries a citation — PASS.** All 11 rows of §3 cite file + JSON field or file + line (e.g., `admission_actual_monkey.json` lines 130/143–146; `experiment_transverse_candidate.json` `step_C_candidate.*.passed: false`; `attachment_candidates.json` per-site fields; report 05 lines 5, 29, 43, 47).

**(3) Blockers list exact and evidence-named — PASS.** (a) the 4 wrist sites (2/side) with the artifact facts (`n_loops: 4`, `n_identified_loops: 2`, `n_open_chains: 0`, verbatim `ambiguous_section` reason, axials 0.051510357/0.053482959 m) and four resolution-evidence requirements R1–R4; (b) the qualification gate; (c) candidates-packet self-hash absence (top-level keys enumerated; H-1 resolution cited from MANIFEST lines 5–11); (d) environment/reproducibility; (e) six further artifact-sourced items (role-count prose discrepancy, mass admission, hand/ulna unresolved-body scope, loop-vs-hull disagreement inventory, MANIFEST self-coverage, the tendon-less muscle).

**(4) Non-goals faithful to frozen boundaries — PASS.** §5 reproduces the `TASK_BOARD.md` lines 7–14 boundaries (Candidate C failure stands; no second candidate; no displacement; no relaxation; provenance preservation; no physics/semantics/muscle-limit/architecture changes; no retroactive rescue) plus the report 05 §6 scope anchor.

**(5) Zero invented numeric criteria — PASS.** Every pass-criterion value not already an artifact law is a placeholder (14 `[ASTRA-APPROVES: …]` slots). All quoted numbers were re-measured from the artifacts during this audit (e.g., 4/12/0 role memberships per body; 42/120 comparable chains; BRD_tendon −9.0164e-04 m; mirror max 6.31e-04 m / mean 5.5e-05 m / sanity 0.02 m; reconstruction 1.1525314521376605e-09 m; db 0.00624, dc ±0.00202, max displacement 0.006558811 m). One drafting error (P1 initially said "15 of 16" uniquely-identifying sites) was caught by self-check and corrected to the artifact value 14 of 16 before delivery.

**(6) Baseline integrity — PASS.** Receipt:
```
$ git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot
(no output)
EXIT:0
```

**Overall: PASS (6/6).**

## SUMMARY OF THE DRAFT'S KEY JUDGMENTS (10 lines)

1. The evidence ladder (geometric containment ≠ anatomical attachment evidence ≠ mechanical qualification) is written as law, anchored verbatim in report 05 §6 and the experiment's own `interpretation_limit` — no test result alone can flip the flag by wording.
2. Qualification is structured as a T1–T8 gate: the flag may become true only when the whole set passes under the architect's sign-off; today T1 is not satisfied (30/32 classified), T2/T6 are blocked, T7's census is open, T3–T5/T8 carry session-5 receipts awaiting independent confirmation.
3. Candidate C's failure is recorded as standing and load-bearing: even its measured loop-authority improvement (0 outside / 14 inside / 0 tight) left the 2 wrist sections unresolved — the ambiguity is section identification, not placement.
4. The 4 wrist sites' ambiguity is specified with exact artifact facts (2 ownership-identified loops of 4, no open chains) and four resolution-evidence requirements, with the choice among P1 (measure), P2 (authority ruling), P3 (documented uncertainty) left entirely to Astra.
5. A factual cross-check discrepancy was surfaced, not smoothed: report 05 §3's "8 last-endpoints per side / 24 waypoints" equals the both-sides totals; the artifact says 4/12 per body — flagged [PENDING A3], artifact is the record.
6. The candidates packet carries no self-hash (only `fitted_packet_sha256`, which names the fit packet per H-1); recorded as blocker (c) with a smallest-change proposal P4 for a future revision, baseline untouched.
7. Mass admission (0 physically admitted, density validation required) and the unresolved hand/ulna bodies are flagged as scope questions a grasp-qualification spec cannot silently skip — P5 asks Astra for the ruling.
8. The hull diagnostic is retained as non-authoritative exactly as the artifact records it; T1's template lets Astra define per-site authority waivers but the artifact default (loop authority) stands.
9. All thresholds that exist in artifacts (−1 mm clearance law, 1e-9 F5 criterion, 1e-6/0.02 m bounds, exact float equality for S13) are cited as existing laws, never re-invented; everything else is a placeholder.
10. Constraint audit: "APPROVED" appears only in the two "NOT APPROVED" statements (lines 3, 209); baseline snapshot clean in git; all writes confined to `audits/A10_spec/`.

## STOP RULE

No missing dependency blocks this draft: A1–A9 findings were not required for v0 (they fill `[PENDING …]` slots at pass-2 / I2). Draft complete; stopping here per the output contract.
