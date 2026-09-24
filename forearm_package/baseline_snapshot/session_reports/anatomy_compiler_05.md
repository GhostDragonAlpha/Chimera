# ANATOMY COMPILER 05 — CORRECTED ATTACHMENT PACKET + ONE PREREGISTERED PLACEMENT EXPERIMENT (CANDIDATE FAILS THE DECLARED CRITERIA; BASELINE PRESERVED)

**Agent:** bigpickle | **Date:** 2026-09-23 | **Scope:** `.tmp/anatomy_compiler/` (build only; no production edits, no commit, no MuJoCo, no training/attachment-force/material work)
**Baseline:** the session-5 packet (`actual_monkey_fit.json`, sha256 `a447555069748d7f…`) preserves the session-4 fit AND its fired containment findings verbatim (hull sampling retained as diagnostic; `envelope_containment.*` residuals untouched). Nothing was shrunk, tuned, or repaired to turn anything green.
**Verdict: G0 + F1–F7 + S1–S14 all green, exit 0. The placement candidate was fit, evaluated, and it FAILED the preregistered success criteria — reported as a failure, per the stop rule.**

---

## 1. Correction 1 — source-coordinate units (`attachment_candidates.py`, test S13)

Session-4's candidates packet multiplied SOURCE site coordinates by the TARGET mesh factor `MESH_UNIT_TO_M = 0.065`. That was wrong: `intake.py` reads XML site `pos` directly (source SI) and `compiler.py` copies them verbatim into `source_pos_local`. Fixed: `source_pos_local` now exports the exact intake floats — no rounding, no scaling — labelled `"source SI (metres), verbatim from the XML — NOT scaled by the target mesh factor"`. Target-mesh conversion stays isolated to `mesh_target.py` (TARGET vertices only). S13 parses the RAW XML (`ET.parse(REAL_XML)`, not through intake) and asserts exported == XML value for all 32 forearm sites, plus intake equality and a mesh-factor-distance pin. The old `*_m` field names are gone; "m" no longer labels source coordinates.

## 2. Correction 2 — signed-distance classification (`target_envelope.py`, test S11 extended)

The old law `"none clears the margin ⇒ outside"` conflated two different facts. Four distinct classes now, at every band-width variant:

| class | law |
|---|---|
| `outside` | d > 0 at every variant — geometrically outside |
| `inside_insufficient_clearance` | d ≤ 0 at every variant, clearance never reaches the 1 mm margin |
| `inside` | d ≤ −1 mm at every variant |
| `unresolved` | class flips under band-width variation, or no sampled band near the axial position |

Re-classification left the real findings standing: the five OUTSIDE sites (BRD-P2/P3, ECRB-P2, ECRL-P2, PT-P5 per side, +3.3…+4.6 mm) are d > 0 at every variant — still OUTSIDE. The three well-clearing sites stay INSIDE. No site on real data fell in the new tight class via the hull path; S11 manufactures one synthetically (0.5 mm inside a hull vertex) and asserts it is `inside_insufficient_clearance`, `n_outside == 0`.

## 3. Correction 3 — candidate handoff (`attachment_candidates.json` v5, tests S12)

- **`mechanical_qualification: false` on every site**, with the reason spelled out: resolved coordinates + tendon endpoint membership do not qualify a membrane port.
- Roles renamed `proximal_candidate`/`distal_candidate` → **`first_endpoint`/`last_endpoint`** (the packet does not establish anatomical proximal/distal orientation). Measured law unchanged: 8 last-endpoints per side, 0 first-endpoints (every tendon path enters the radius at an interior index), 24 waypoints.
- **Numeric local-to-world transforms** per body: `R = Bp @ diag(scale) @ Bᵀ` (B rebuilt from the fit's own landmark resolution), `t = fitted_origin`, with `fitted_pos_global = t + R @ source_pos_local`. Reconstruction error recorded per body (0.0 at export precision; verified < 1 µm in step A).
- **Hash separation**: `source_xml_raw_sha256` (`675e00d0…`) + canonical (`7caa32c6…`) identify the upstream XML; `fitted_packet_sha256` (`a4475550…`) is the sha256 of the WRITTEN packet bytes, computed after `write_json`. Different objects, different fields, never aliased.
- **Per-site containment status rides along**: `skin_containment.{loop (authority), hull_sampling_diagnostic}` with verdict, signed distance, and reason.
- **Figure** (`figure_forearm_candidates.png`): colour = placement status (green inside / amber tight / red outside / grey unresolved), marker shape = role (filled = endpoint, hollow = waypoint).

## 4. Preregistered placement experiment (`experiment_transverse_fit.py`)

Preregistration is the module's top-of-file law and is copied verbatim into the output BEFORE results. Steps ran once, in order:

**A — verification (passed).** Every exported world point reconstructed from its local coordinates and the exported transform: max error 1.15e-9 m (export rounds at 1e-9; bound 1e-6). Unit separation asserted (source == XML; target factor applied to target mesh only). Mirror: reflecting the right side across the target sagittal plane (x = 0) reproduces the left side's 16 points with **max error 0.63 mm, mean 0.055 mm** — the fit respects bilateral symmetry far inside the 20 mm sanity bound.

**B — baseline under the FINAL loop authority (fired, preserved).** Triangle–plane section loops at each site's exact axial position, the infinite plane cut chained into closed loops, the limb's skin loop IDENTIFIED mechanically by majority pack-vertex ownership (≥ 50 % of cut-segment triangles owned by the side's proximal/distal joints — the pack's own `assign` data, no proximity choice, no bridging; exactly one loop must identify). Baseline verdict per side: **6 inside / 1 tight / 7 outside / 2 ambiguous**. The loop authority SHARPENS session-4 (5 hull-outside → 7 loop-outside: BIClong-P9 and BICshort-P6 are measured outside at axials the bands never sampled) and reclassifies PT-P3 as inside-but-tight. ECRB-P3/ECRL-P3 stay ambiguous (wrist-level sections yield multiple ownership-identified loops). Hull sampling is retained verbatim beside it.

**C — the ONE candidate (FAILED; stopped).** Joint-anchored transverse translation (db, dc) shared by all sites of a side; axial length, joints, masses untouched; other side independent. Bounds ±8 mm declared; objective = Σ max(0, 1 mm − clearance)² over sites × the three session-4 fitting bands + 1e-2·(db²+dc²); deterministic 3-stage grid search. Optimum: **db = +6.24 mm, dc = ±2.02 mm** (mirror-symmetric solution emerged from the two independent fits), max site displacement 6.56 mm, strictly inside bounds. Evaluation: fitting sections violated by ~41 µm total (strict `≤ −1 mm` fails — a hair, but the criterion is the criterion); loop authority improved to **0 outside / 14 inside / 0 tight / 2 ambiguous** — the two ambiguous sections remain ambiguous (section identification, not placement). **passed = False on both sides.** Effects: 42/120 tendons have fully-resolved comparable chains; max |Δ path length| = **0.90 mm** (BRD); max |Δ moment arm| ≈ 0 (1e-12 rounding floor) — the cluster translation is a rigid shift of distal path points and the fitted forearm paths are straight (a straight tendon has zero moment arm about any joint, which the shift preserves). Bound violations: none. Outputs: `runs/experiment_transverse_candidate.json` + `runs/figure_transverse_candidate.png`. Baseline untouched as its own revision. Per the stop rule: no second candidate, no relaxation, no re-fit.

## 5. Tests and artifacts

`python run_tests.py` → **ALL FALSIFIERS GREEN, exit 0** (G0; F1–F7; S1–S14). S11 extended (tight class + distinct outside), S12 rewritten (endpoint roles, mech-qual=false, transform reconstruction, hash separation), S13 (raw-XML unit identity) and S14 (loop law: open chains never close; identified-loop requirement; axis probe inside, 50 mm-lateral probe outside) added; DERIVATION.md §13 appended.

Regenerated: `actual_monkey_fit.json` (loop-authority measurements + residuals `envelope_containment_loop.*`; hull findings retained), `actual_monkey_tables.txt`, `admission_actual_monkey.json` (adds `envelope_containment_loop_ok` + per-side loop/tight/ambiguous lists), `attachment_candidates.json` (v5), both forearm figures, experiment json + figure. Temp probes removed.

## 6. What is NOT claimed

- The candidate's pass/fail is against the DECLARED criteria; a ~41 µm shortfall is still a fail, and the two ambiguous wrist sections were not resolved by choosing a loop.
- Even a passing candidate would have remained authored transverse geometry under declared bounds — not recovered anatomy, not measured attachment, not mechanical qualification. It did not pass.
- `mechanical_qualification` is false for every site in the packet; endpoint roles are path positions only.
- No material inference, no training changes, no production wiring; the packet's fitted geometry is bit-identical to session 4 except the ADDED measurement records.
