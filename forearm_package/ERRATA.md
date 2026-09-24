# ERRATA — additive corrections to the frozen session reports

**Law (architect, 2026-09-24):** record the three verified errata additively — original reports preserved unmodified in the frozen baseline (`baseline_snapshot/session_reports/`), each correction linked to its verifying receipt. This file is the corrections layer; where prose and artifact disagree, **the artifact is the record**.

---

## E-1 — role-count scoping in `anatomy_compiler_05.md` §3 (line 29)

- **Claimed:** "Measured law unchanged: **8 last-endpoints per side**, 0 first-endpoints (…), 24 waypoints."
- **Measured:** **4 last-endpoints per side** (right: `BIClong-P11`, `BICshort-P8`, `BRD-P3`, `PT-P5`; left: same `_l` names), 0 first-endpoints, 12 waypoints per side. The report's 8 / 0 / 24 are the **two-side totals**; only the "per side" scoping is wrong. The underlying packet fields are internally consistent.
- **Receipts:** `audits/A3_site_audit/report.md` §C + `receipts/audit_receipt.json` (fresh re-run by the coordinator); independently confirmed by A6 (`audits/A6_evidence/receipts/a6_verify_receipt.json`) and A10 (artifact re-derivation during spec drafting).
- **Architect confirmation:** 2026-09-24 ("the three verified errata").

## E-2 — zero-arm causality in `anatomy_compiler_05.md` §4-C

- **Claimed:** the candidate's zero moment-arm deltas are explained by "a straight tendon has zero moment arm about any joint, which the shift preserves."
- **Measured:** the fitted forearm paths **bend 20–65° at their elbow-entry indices**; the zero deltas hold because **no finite chain crosses a resolved joint boundary** — the bends sit on unresolved-owner coordinates (`elbow_flexion` owned by unresolved `ulna`; wrist triples by unresolved `hand_r`/`hand_l`), so those arms are NaN rather than zero. Numbers unaffected; the causal explanation is corrected.
- **Receipts:** `audits/A8_arms/report.md` (finding B; nonzero-arm census; `receipts/a8_arms_results.json`), scripts re-run by the coordinator.
- **Architect confirmation:** 2026-09-24.

## E-3 — Candidate-C breach magnitude in `anatomy_compiler_05.md` §4-C

- **Claimed:** "fitting sections violated by ~41 µm total."
- **Measured:** **no artifact supports 41 µm.** The recorded optimum encodes exactly **one violated section per side**: `ECRL-P3` @ t=0.35 (right) and `ECRL_l-P3` @ t=0.35 (left), each **67.147 µm** (67.147455… µm right, 67.146833… µm left); the objective recomputes to the recorded 4.34689e-07 m² to within 2–3e-13 m². **The failure stands unchanged** — 67 µm violates the `≤ −1 mm` law exactly as 41 µm would.
- **Receipts:** `audits/A5_containment/receipts/candidate41.json` + `report.md` (finding F4), decomposition re-inspected by the coordinator.
- **Architect confirmation:** 2026-09-24 — "Candidate C's recorded breach is 67.147 µm per side, not approximately 41 µm. Its failure remains unchanged."

---

## Appendix — stale-artifact labels (documentation, same additive law)

`runs/grounded_chimanoid.json`, `runs/mirror_read.json`, `runs/synthetic_twin.json` are **session-4 side artifacts** frozen into the snapshot; session 5 never regenerated them (they differ from regeneration by the session-4 admission-schema rename, +1136 bytes / 12 structural diffs each). Cite as session-4 history only; never as session-5 outputs. Receipt: `audits/A9_reproduce/report.md` (byte-identity table). Related: `mirror_read.json` is additionally the **synthetic-twin** read — never the actual-monkey handedness record (A4).
