# ANATOMY COMPILER 04 — CONTRACT CORRECTIONS: SERIALIZATION GATE, ADMISSION SPLIT, SPATIAL CONTAINMENT (FALSIFIER FIRED), ATTACHMENT CANDIDATES

**Agent:** bigpickle | **Date:** 2026-09-23 | **Scope:** `.tmp/anatomy_compiler/` (build only; no production edits, no commit, no MuJoCo, no training/attachment-force work)
**Membrane:** DERIVATION.md (F1–F7, S1–S8) **amended by** the session-4 contract: (1) a resolved field exports a NUMBER — NaN/Infinity is unwritable, `null` is reserved for records the machinery explicitly marks unresolved; (2) geometric admission is NOT mass admission — a transported mass is `source_effective × |det D|` under a RECORDED constant-density assumption, and `physically_admitted` stays EMPTY until a validated material/mass source exists; (3) the median-width comparison is a coarse **WIDTH SCREEN** with no spatial claim; true **CONTAINMENT** judges each fitted site against the measured section hull, and returns **unresolved** wherever the sampled geometry cannot establish it; (4) attachment candidates derive deterministically from ordered tendon paths: **port ⇔ path END, waypoint ⇔ interior**.
**Verdict: G0 + F1–F7 + S1–S12 all green, exit 0. And the new containment falsifier FIRED on the real data — honestly.**

---

## 1. Contract 1 — serialization gate (`schema.py`, test S9)

`PacketValidationError` (code `nonfinite_resolved_field`) now guards `write_json`: `validate_finite` walks every dataclass/array/list/dict and refuses a non-finite value in any field whose owning record is NOT explicitly unresolved. Non-finite stays legal only in `_NONFINITE_ALLOWED` fields of records that carry `unresolved+reason`, status `path_incomplete*`/`unresolved_body`, or `matched=False` (sites' fitted positions, joints' axis, tendon points/rest_length, moment-arm values). `_jsonable` now emits `None` as explicit `null` (Optional fields are lossless). No import cycle: the error mirrors `correspondence.Refusal`'s shape without importing it.

S9 proves both directions on the real fit: clean packet → `problems == []`, zero NaN/Infinity tokens, unresolved site exports `fitted_pos_global: null` + reason; injected NaN in a RESOLVED site → refused, message names `fitted_pos_local`; same injection in a genuinely-unresolved site → still legal.

## 2. Contract 2 — the admission split (`compiler.py`, test S10)

The ledger now separates what geometry proved from what mass assumes:

```
counts: geometrically_resolved 9 | flagged 0 | unresolved 9 | admitted_kinematic 9
        transported_under_assumption 8 | physically_admitted 0
totals: transported 5.263 kg | physically_admitted 0.0 | flagged 0.0 | root-ref 11.777 | all 17.040
mass_admission: assumption=uniform_constant_density_scale, kind=source_effective_x_det_scale,
                requires_density_validation=True, density_validated=False
```

`FittedPhysiology.admitted` is re-documented as *transport-eligibility*, never physical admission. The audit gains `geometry_resolution_does_not_discharge_density_validation: True`. Pelvis stays `root_ref_frame_unscaled` and out of every subtotal. Report/caption/admission-summary wording updated everywhere (`ADMITTED` → `TRANSPORTED-under-assumption (physically admitted 0.000)`); S4 re-locks the new keys.

## 3. Contract 3 — width screen vs spatial containment (`target_envelope.py`, test S11) — **THE FALSIFIER FIRED**

- `feasibility` → `width_screen` (alias kept): a **1-D median screen**, docstring and payload say `width_screen_coarse` and name its blind spot: a narrow cluster displaced transversally passes it by construction.
- `containment()`: each fitted site is projected into the envelope frame (axial along elbow→wrist; b,c = the measured transverse axes; both metres — `mesh_target` already scales `V`/`J` by 0.065). Per section the sampler now records the **2-D convex hull** of the band vertices (`_convex_hull_2d`, monotone chain — no scipy) at nominal band AND at `band_half × (1 ± 0.25)`. Verdict law: **inside only if all three hulls clear by the 1 mm margin; outside only if none does; a flip between inside and across band-width signs, or a miss of the axial window (t ± 8 mm), or unusable band geometry ⇒ UNRESOLVED — never assumed inside.**
- `main` wiring: only a HARD `outside` sets `envelope_containment.outside.<body>` + `envelope_containment_ok=False`; unresolved sets `envelope_containment.unestablished.<body>`. **Segments are NOT re-flagged post-fit** — the admission ledger is locked inside `fit()`; mutating `segment.status` afterwards would desync the packet. The envelope is a skin constraint, not a length measurement; the falsifier loses loudly in residuals/measurements/admission instead.

**Result on the real fit (both forearms, 16 sites each): 3 inside / 5 outside / 8 unresolved.** Width screen: PASS (spread 5.7 mm vs 20.2/22.9 mm envelope, clearance 14.5/17.0 mm) — exactly the displaced-narrow-cluster shape the contract predicted the screen cannot catch. The OUTSIDE sites are ~3.3–4.6 mm beyond the hull: BRD-P2 (+4.63 mm), BRD-P3 (+3.71), ECRB-P2 (+3.35), ECRL-P2 (+4.26), PT-P5 (+3.29; +2.90 under the wide band). INSIDE: FCR-P2 (−2.18), FCU-P2 (−3.80), FCU-P3 (−3.68). UNRESOLVED (8): the remaining sites sit outside the sampled t = 0.35/0.5/0.65 ± 8 mm windows (elbow/wrist thirds of the forearm are unsampled geometry).

**Honest reading (what this finding is and is not):** the radius axial scale `[0.2217]³` is pack-joint evidence and is untouched; what fails is the **authored transverse placement** (`uniform transverse = axial scale`): the source muscle sites, transported at that authored ratio, land measurably OUTSIDE the measured monkey skin hull at mid-forearm sections for 5 of 16 sites per side. The packet now says so with per-site signed distances under all three band variants. `envelope_containment_ok=False` is recorded in residuals, measurements, and the admission summary (`containment_outside` / `containment_unresolved` lists). Nothing is tuned to pass; the falsifier is left red in the record while the suite stays green because S11 tests the *law*, not the verdict.

## 4. Contract 4 — attachment candidates (`attachment_candidates.py`, test S12)

`runs/attachment_candidates.json` (44,159 bytes, strict JSON, `allow_nan=False`): for radius and radius_l, all 16 sites each with source ids, `source_pos_local_m` (metres, ×0.065 recorded), fitted local/global metres, per-record resolved flag + reason, frame/units declarations, packet provenance hashes, and **tendon membership with `index_in_path` / `path_length` / `role`**. Role law: FIRST in a tendon's ordered `site_names` = `proximal_candidate`, LAST = `distal_candidate`, interior = `waypoint` (never a candidate for that tendon; a site may be a candidate for one tendon and a waypoint for another). Measured: **8 distal candidates per forearm, 0 proximal, 24 waypoint memberships** — every tendon path ENTERS the radius at an interior index and its forearm-end site is the LAST entry (paths begin on humerus; ECRL/FCR/FCU-class paths end on the unresolved hand, so their radius sites are correctly waypoints, NOT ports). S12: role⇔index law, one role per (site, tendon), 16/16 sites, bit-identical rebuild.

Reader example: `example_read_candidates.py` (by-site and by-tendon views; run verified). Enlarged figure: `figure_forearm_candidates.py` → `runs/figure_forearm_candidates.png` (per forearm: axial-vs-b path view + true b-vs-c cross-section with hulls, ports, waypoints, containment-verdict coloring).

## 5. Tests & artifacts

Suite: `python run_tests.py` → **ALL FALSIFIERS GREEN, exit 0** (G0; F1–F7; S1–S12). S4 re-locked to the split ledger; S5 rides the `width_screen` alias; S6 passes with None→null emission; DERIVATION.md §13 gained the appended S1–S12 rows (S1–S8 shipped in session 3 but were never entered — recorded now, append-only).

Regenerated: `runs/actual_monkey_fit.json` (**1,315,062 bytes**, was 1,230,610 — hulls ×3 variants ×3 sections ×2 forearms + containment records + nulls), `actual_monkey_tables.txt`, `admission_actual_monkey.json`, `attachment_candidates.json`, `figure_actual_fit.png`, `figure_forearm_candidates.png`. Temp probes (`_probe_contain.py`, `runs/_c1_smoke.json`) removed.

## 6. What is NOT claimed

- No mass is physically admitted; no density is invented; `requires_density_validation` stands.
- No threshold was tuned: margin 1 mm, band 8 mm, sweep ±25 %, sections 0.35/0.5/0.65 are the documented constants from session 3, unchanged.
- Containment says nothing about the axial scale; the outside verdict indicts only the authored transverse placement assumption. Fixing that (a transverse evidence source, or a narrower authorship) is a NEW derivation decision and was not made here.
- The 8 unresolved sites per forearm are exactly that: the sampled geometry does not reach them (t < 0.34 or t > 0.66), and the packet refuses to call them inside.
