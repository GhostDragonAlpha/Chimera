# ANATOMY COMPILER 03 — ADMISSIBLE PACKET: STRICT-JSON NULLS, PROVENANCE, ACTUATOR HYGIENE, FOREARM OUTER-ENVELOPE FIT

**Agent:** bigpickle | **Date:** 2026-09-23 | **Scope:** `.tmp/anatomy_compiler/` (build only; no production edits, no commit, no MuJoCo, no training/attachment-force/display-mesh work)
**Membrane:** `.tmp/anatomy_compiler/DERIVATION.md` (F1–F7) **amended by** v3 contract: unresolved quantities export as `null` with explicit status+reason (never zeros); JSON is strict (`allow_nan=False`, round-trip verified); actuators are parsed from `<actuator>` only (the `<default>` block is resolved, never emitted); provenance records hashes + scale + coordinate conventions + aspect policy and separates upstream byte identity from documented local transforms; ph/"ysisology carries an admission ledger (resolved/flagged/unresolved/admitted); pelvis is `root_ref_frame_unscaled` — fixing the root frame is NOT scale evidence; the forearm b/c are OUTER-ENVELOPE-BOUNDED AUTHORED assumptions (skin width is not internal anatomy evidence).
**Inputs (read-only):** `Saved/meshes/monkey_birth.bin` (sha256 `550A5B3EC927…AABFA3C`) + `monkey_joints.bin` (sha256 `74B3AB044B7A…50C1662`); source `.tmp/chimanoid.xml` (**raw** sha256 `675e00d0…` / **canonical LF** sha256 `7caa32c6…` — differs by exactly ONE trailing CRLF, 154835 → 154834 bytes, verified).
**Deliverables (lead's list):** corrected packet + schema, regression tests, updated fit + figure, machine-readable admission summary. **All shipped; suite exit 0.**

**Verdict: F1–F7 + G0 + S1–S8 all green (`python run_tests.py` → exit 0). The forearm is now fit cleanly — radius/radius_l `[0.2217]³`, resolved (not flagged) under `policed_flag` — because the transverse axes are explicit envelope-bounded authorships instead of contaminated evidence. The contaminated wrist-band finding is preserved VERBATIM as the S3/S5 regression: fit the legacy `build_correspondence` and radius MUST still flag.**

---

## 1. The contract, as received and as delivered

**Lead falsifiers (all now enforced):** strict-JSON failure (a packet with `NaN`/`Infinity` tokens must not be writable); unnamed/default actuator leakage (121 XML muscles = 120 `<actuator>` records + 1 `<default>` — the default must never become an actuator); missing provenance; flagged records promoted to admitted; root-frame identity used as physical scale evidence; outer-envelope measurements mislabeled as internal anatomy.

**Delivered corrections:**
- `schema.py::_jsonable` now maps non-finite scalars to `null`, and an **all-NaN vector collapses to a single `null`** (an unresolved limb exports `null`, not `[null,null,null]`). `write_json` uses `allow_nan=False` **and** re-parses + rejects any non-standard token. New fields: `axis_measure_kind` (what *was* measured vs authored), `reason` on every unresolved site/joint, `admitted`/`admission_note` on physiology, `rest_length: Optional[float]`, `measurements` + `admission` on the anatomy, `attr_source` per muscle attribute, constants `ROOT_REF_FRAME_UNSCALED` + measure kinds.
- `intake.py` parses actuators via `.//actuator/muscle` **only**; the `<default>` block is resolved verbatim for inherited attrs (`ctrllimited true / ctrlrange "0 1" / scale 200`) and recorded in `meta`, never materialized as a phantom muscle. Named refusals: `unnamed_actuator`, `duplicate_actuator`, `invalid_tendon_ref`. Post-conditions: 120 actuator records, all named & unique, all tendon-refs valid, tendonless 0.
- `compiler.py` v3: admission ledger (counts: geometrically_resolved / flagged / unresolved / admitted_kinematic / admitted_physical; bodies lists incl. `excluded_from_physical` with reasons; `totals_mass_kg` split admitted / flagged-only / root-reference-only / all-transported); `meta.source_identity` carries raw + canonical hashes with the transformation note; `fit(..., provenance=...)` threads through; audit gains `flagged_geometry_excluded_from_admitted_physical` and `root_ref_frame_not_scale_evidence`.

**Verified on the export:** 168 unresolved sites → `fitted_pos_global: null` + reason; 17 unresolved joints → `axis: null` + reason; 0 non-standard JSON tokens in a 1.2 MB packet; strict round-trip stable.

## 2. Actuator population measured (121 = 120 + 1, and where they live)

Parsed the source directly: `root.findall(".//muscle")` returns **121**. The breakdown that the contract is about:
- **120** live under `<actuator><muscle>` — every one declares `force/timeconst/lengthrange/ctrllimited/ctrlrange`, `ctrllimited="true"`, `ctrlrange="0 1"`.
- **1** unnamed `<default><default class="muscle"><muscle ctrllimited="true" ctrlrange="0 1" scale="200"/></default></default>` — a *mechanism* default, not an actuator. Intake resolves it for inherited attrs and never counts it. S8 (`s8_actuator_hygiene`) blocks regressions both ways.

## 3. Provenance: upstream identity ≠ local transform

The source has exactly **one CRLF** and it is trailing (`…</mujoco>\r\n`). Canonicalization (CRLF→LF, strip trailing) is a **documented, non-semantic text transform**, and the packet records:

| file | sha256 |
|---|---|
| monkey_birth.bin | `550A5B3EC927EA13614AD250963B23E2948E76A238AC110DA9889F339AABFA3C` |
| monkey_joints.bin | `74B3AB044B7ADAED4A0F9349A81F5D3C87441084B2EC8981F4E0AFABA50C1662` |
| chimanoid.xml | raw `675e00d0898cf7a175f3e4fe8f240eb24301c2f5e201ffa9215aea45b01b83d1` → canonical `7caa32c6e31e319876ea21625b662c5c00e736038f542b38ce6b0cb81aadc8a5` |
| correspondence | canonical serialization digest `52c92fe0d2…` |

plus `mesh_units_to_m: 0.065`, `coordinate_conventions` (up +y / right +x / anterior +z, global_scale_factor 1.0), and `aspect_policy` (policed_flag, max_magnitude 5 / min 0.2 / max_aspect 6, on_violation = flag never silent repair). `meta.source_identity` distinguishes raw (pinned upstream bytes) from canonical (documented local normalization) — S7 locks this.

## 4. The forearm: contaminated band, preserved; envelope-bounded authorship, adopted

The wrist-band regression did its job in session 2: under band transverse evidence, radius `[0.2217 2.6372 0.4434]` → aspect 11.9 > 6 → FLAGGED (S3 still asserts this on the legacy path, byte-identical). The question the packet now answers honestly: **is the forearm cross-section unmeasurable, or just unmeasurable by THAT band?**

**Measured:** a bounded outer(skin)-envelope estimator (`target_envelope.py`) samples interior sections at t = 0.35/0.5/0.65 of the elbow→wrist axis, each a band ±8 mm wide with a **radial cap 50 mm** — without the cap, torso/upper-arm vertices contaminating the axial projection produced the 0.17 m garbage; with it, the geometry is real forearm skin:

| limb | sections (verts) | b median | b uncert | c median | c uncert |
|---|---|---|---|---|---|
| radius | 0.35→75 / 0.5→66 / 0.65→56 | 20.2 mm | 0.55 mm | 22.9 mm | 0.08 mm |
| radius_l | 75 / 66 / 56 | 20.2 mm | 0.55 mm | 22.9 mm | 0.08 mm |

Sensitivity is recorded (section placement ±5%, band half-width ±25%) and small on this geometry. **Nature: `outer_envelope` — a SKIN bound, explicitly NOT internal anatomy.** The packet therefore does NOT use skin width as bone/tissue scale evidence: radius b/c are **AUTHORED at the measured axial scale** (`n_axis_evidence 21 / n_axis_assumptions 6`, blanket True — the assumption notes say so line-by-line), and the envelope is used only for one **feasibility check**: fitted INTERNAL muscle-site spread (source offsets × fit scale) must clear the skin envelope. Result **ok=True** on both forearms (spread ~mm vs 20 mm envelope). If that overlap ever failed, the segment flags (`envelope_exceeded.<body>`, SEG_FLAGGED) — an envelope violation is impossible, never a confirmation.

**The two quantities never meet each other's lane:** skin-width vs source-site-spread is a calibration question; the packet keeps them separate and labels both.

## 5. Admission ledger and physiology

| quantity | result |
|---|---|
| geometrically resolved / flagged / unresolved | 9 / **0** / 9 |
| admitted_kinematic / admitted_physical | 9 / **8** (femur_r/l, tibia_r/l, humerus, humerus_l, radius, radius_l) |
| flagged excluded from physical | yes (none exist now; flag path covered by compiler audit flag) |
| pelvis | **root_ref_frame_unscaled**, `admitted: False`, note *"identity scale carries the original mass as a reference-frame quantity — it does not measure or validate pelvis size"* |
| totals | admitted_physical **5.263 kg** · flagged_only 0.0 · root_reference_only **11.777 kg** · all_transported **17.040 kg** |

This is the honest resolution of the session-2 tension: fixing the root frame does **not** establish pelvis size (11.777 kg stays a reference-frame quantity). Radius contributes 0.008 kg/limb now (was flagged 0.189) because its b/c dropped from the 2.6-band to the 0.2217-authored transverse.

## 6. Falsifiers, session 3 surface (all green with F1–F7, S1–S3 kept)

| ID | Promise | Result |
|---|---|---|
| S4 | envelope-packet invariants: rig F1s, 9/9 ledger, axial ratios re-derived to 1e-6, **21 ev / 6 ass / blanket True**, radius resolved `[0.2217]³` authored-b/c under POLICED_FLAG, admission ledger 8 admitted + pelvis excluded with the reference-frame note, totals 5.263/11.777/17.040, 120 tendons (42/78), deterministic re-fit byte-identical | PASS |
| S5 | envelope estimator: interior sections only, radial-capped, ~2 cm (not the 0.17 m band garbage), sensitivity+uncertainty recorded, `nature=outer_envelope`; feasibility ok-pass/fail both exercised; **legacy band still flags radius** | PASS |
| S6 | strict JSON: `write_json` rejects any NaN/Infinity token and round-trips; unresolved sites/joints export `null` + reason; rest_length null where unmeasured | PASS |
| S7 | provenance: 4 required inputs hashed, source raw-vs-canonical recorded (single trailing CRLF), mesh_units 0.065, coordinate conventions, aspect policy; threaded into packet meta | PASS |
| S8 | actuator hygiene: 120 named/unique/tendon-refs-valid records, ctrlrange `0 1` parsed, `<default>` resolved only | PASS |
| (regression) | F1–F7, S1–S3, whole-body example unchanged | PASS |

## 7. Artifacts (`runs/` unless stated)

- `actual_monkey_fit.json` — **admissible** packet (strict JSON, null contract, provenance, admission ledger, envelope measurements).
- `actual_monkey_tables.txt` — human table (includes envelope + feasibility + provenance sections).
- **`admission_actual_monkey.json`** — machine-readable admission summary (NEW, lead deliverable).
- `figure_actual_fit.png` — regenerated: green SKIN-envelope rings at the wrists, admission counts and "pelvis = root-reference frame, not scaled" in the caption. **I cannot visually confirm the png (no image input) — it needs an eyeball.**
- `target_envelope.py` (new estimator), `actual_target_fit.py` (envelope correspondence + provenance + admission), `run_tests.py` S4–S8.

## 8. What ISN'T claimed (honest boundaries)

- The forearm cross-section is **still not measured** — it is authored at the axial scale under an outer skin bound. The envelope is a constraint, not a scale law.
- 11.777 kg pelvis remains a reference-frame quantity; its true size/scale is unknown from the rig.
- Trunk, hands, feet, elbow-head scales remain unresolved (no declared endpoints) — never invented.
- Only the `policed_flag` run is the shipped packet; the `unbounded`/`policed` behavior is regression-tested, not shipped.
- No production file was modified; nothing committed.