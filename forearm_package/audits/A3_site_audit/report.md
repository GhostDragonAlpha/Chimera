# A3 SITE AUDIT — 32 forearm sites vs source XML (units, identities, endpoint roles)

**Auditor:** A3 (audit agent, evidence only) · **Date:** 2026-09-24
**Baseline (read-only):** `E:/PythonChimera/forearm_package/baseline_snapshot/`
**Method:** independent reimplementation — stdlib `ElementTree` parse of `source_xml/chimanoid.xml` + direct float comparison against `runs/attachment_candidates.json`. The pipeline's own test suite was NOT executed. For the record, the existing unit-identity test S13 lives at `code/run_tests.py:1144-1147` (registered at `:1232-1233`); it was located but never run by this audit.
**Script:** `scripts/audit_sites.py` · **Machine-readable receipt:** `receipts/audit_receipt.json`

**PREREGISTRATION (frozen):** PREDICTION: 32/32 exact float identity, roles consistent, one uniform provenance block, canonical hash reproduces. FALSIFIER: any single mismatch (float, unit, role, count, hash) fails the audit — itemize both values exactly; do not repair.

---

## VERDICT SUMMARY

| # | Criterion | Verdict |
|---|---|---|
| 1 | 32-row table complete, per-row PASS/FAIL with values | **PASS** — 32/32 PASS |
| 2 | Measured role counts vs report-05 law | **FAIL** — report-05 line 29 claims "8 last-endpoints **per side**"; measured **4 per side** (8 is the two-side **total**). Full itemization in §C. |
| 3 | Provenance uniformity across the 32 sites | **PASS** — one packet-level block, all three pinned hashes recomputed and matched |
| 4 | Canonical-hash recipe reproduced | **PASS** — reproduced exactly on first attempt |
| 5 | Baseline integrity | **PASS** — `git status --porcelain` output empty |

Overall: the 32-site packet is byte-exact against the XML on floats, units, tendon identity, and per-site roles. **One falsifier fired**, on the *documentation* side: the role-count law as worded in `session_reports/anatomy_compiler_05.md` line 29. Nothing was repaired; the finding stands as recorded.

---

## A. Per-site evidence (criterion 1) — 32 rows, 32 PASS

Columns: XML body · XML raw `pos` string (verbatim attribute text) · packet `source_pos_local` · exact float equality (Python `==` on parsed floats, no tolerance) · detectability delta = max|packet − XML×0.065| (the gap the unit check would have caught) · tendon index/length · derived role.

| Site | XML body | XML raw pos | packet source_pos_local | exact== | Δ vs ×0.065 | idx/len | role | Verdict |
|---|---|---|---|---|---|---|---|---|
| BIClong-P11 | radius | -0.002 -0.0375 -0.002 | [-0.002, -0.0375, -0.002] | True | 3.506e-02 | 9/10 | last_endpoint | PASS |
| BIClong-P9 | radius | 0.01467 -0.0102 -0.01062 | [0.01467, -0.0102, -0.01062] | True | 1.372e-02 | 8/10 | waypoint | PASS |
| BICshort-P6 | radius | 0.0119375 -0.0102 -0.0114103 | [0.0119375, -0.0102, -0.0114103] | True | 1.116e-02 | 5/7 | waypoint | PASS |
| BICshort-P8 | radius | -0.002 -0.0375 -0.002 | [-0.002, -0.0375, -0.002] | True | 3.506e-02 | 6/7 | last_endpoint | PASS |
| BRD-P2 | radius | 0.03577 -0.12742 0.02315 | [0.03577, -0.12742, 0.02315] | True | 1.191e-01 | 1/3 | waypoint | PASS |
| BRD-P3 | radius | 0.0419 -0.221 0.0224 | [0.0419, -0.221, 0.0224] | True | 2.066e-01 | 2/3 | last_endpoint | PASS |
| ECRB-P2 | radius | 0.02905 -0.13086 0.02385 | [0.02905, -0.13086, 0.02385] | True | 1.224e-01 | 1/4 | waypoint | PASS |
| ECRB-P3 | radius | 0.03549 -0.22805 0.03937 | [0.03549, -0.22805, 0.03937] | True | 2.132e-01 | 2/4 | waypoint | PASS |
| ECRL-P2 | radius | 0.03195 -0.13463 0.02779 | [0.03195, -0.13463, 0.02779] | True | 1.259e-01 | 1/4 | waypoint | PASS |
| ECRL-P3 | radius | 0.04243 -0.23684 0.0362 | [0.04243, -0.23684, 0.0362] | True | 2.214e-01 | 2/4 | waypoint | PASS |
| ECU-P5 | radius | -0.01421 -0.22696 0.03481 | [-0.01421, -0.22696, 0.03481] | True | 2.122e-01 | 4/6 | waypoint | PASS |
| FCR-P2 | radius | 0.0211 -0.21943 0.00127 | [0.0211, -0.21943, 0.00127] | True | 2.052e-01 | 1/3 | waypoint | PASS |
| FCU-P2 | radius | 0.0105197 -0.183974 0.00012377 | [0.0105197, -0.183974, 0.00012377] | True | 1.720e-01 | 1/4 | waypoint | PASS |
| FCU-P3 | radius | 0.01082 -0.22327 0.00969 | [0.01082, -0.22327, 0.00969] | True | 2.088e-01 | 2/4 | waypoint | PASS |
| PT-P3 | radius | 0.01179 -0.053657 -0.022189 | [0.01179, -0.053657, -0.022189] | True | 5.017e-02 | 2/4 | waypoint | PASS |
| PT-P5 | radius | 0.0254 -0.1088 0.0198 | [0.0254, -0.1088, 0.0198] | True | 1.017e-01 | 3/4 | last_endpoint | PASS |
| BIClong_l-P11 | radius_l | -0.002 -0.0375 0.002 | [-0.002, -0.0375, 0.002] | True | 3.506e-02 | 9/10 | last_endpoint | PASS |
| BIClong_l-P9 | radius_l | 0.01467 -0.0102 0.01062 | [0.01467, -0.0102, 0.01062] | True | 1.372e-02 | 8/10 | waypoint | PASS |
| BICshort_l-P6 | radius_l | 0.0146695 -0.0102 0.0106184 | [0.0146695, -0.0102, 0.0106184] | True | 1.372e-02 | 5/7 | waypoint | PASS |
| BICshort_l-P8 | radius_l | -0.002 -0.0375 0.002 | [-0.002, -0.0375, 0.002] | True | 3.506e-02 | 6/7 | last_endpoint | PASS |
| BRD_l-P2 | radius_l | 0.03577 -0.12742 -0.02315 | [0.03577, -0.12742, -0.02315] | True | 1.191e-01 | 1/3 | waypoint | PASS |
| BRD_l-P3 | radius_l | 0.0419 -0.221 -0.0224 | [0.0419, -0.221, -0.0224] | True | 2.066e-01 | 2/3 | last_endpoint | PASS |
| ECRB_l-P2 | radius_l | 0.02905 -0.13086 -0.02385 | [0.02905, -0.13086, -0.02385] | True | 1.224e-01 | 1/4 | waypoint | PASS |
| ECRB_l-P3 | radius_l | 0.03549 -0.22805 -0.03937 | [0.03549, -0.22805, -0.03937] | True | 2.132e-01 | 2/4 | waypoint | PASS |
| ECRL_l-P2 | radius_l | 0.03195 -0.13463 -0.02779 | [0.03195, -0.13463, -0.02779] | True | 1.259e-01 | 1/4 | waypoint | PASS |
| ECRL_l-P3 | radius_l | 0.04243 -0.23684 -0.0362 | [0.04243, -0.23684, -0.0362] | True | 2.214e-01 | 2/4 | waypoint | PASS |
| ECU_l-P5 | radius_l | -0.01421 -0.22696 -0.03481 | [-0.01421, -0.22696, -0.03481] | True | 2.122e-01 | 4/6 | waypoint | PASS |
| FCR_l-P2 | radius_l | 0.0211 -0.21943 -0.00127 | [0.0211, -0.21943, -0.00127] | True | 2.052e-01 | 1/3 | waypoint | PASS |
| FCU_l-P2 | radius_l | 0.00949 -0.1841 -0.0005 | [0.00949, -0.1841, -0.0005] | True | 1.721e-01 | 1/4 | waypoint | PASS |
| FCU_l-P3 | radius_l | 0.01082 -0.22327 -0.00969 | [0.01082, -0.22327, -0.00969] | True | 2.088e-01 | 2/4 | waypoint | PASS |
| PT_l-P3 | radius_l | 0.01179 -0.053657 0.022189 | [0.01179, -0.053657, 0.022189] | True | 5.017e-02 | 2/4 | waypoint | PASS |
| PT_l-P5 | radius_l | 0.0254 -0.1088 -0.0198 | [0.0254, -0.1088, -0.0198] | True | 1.017e-01 | 3/4 | last_endpoint | PASS |

Unit check detail (criterion 1b): for all 32 sites, packet == XML float triple (exact) AND packet != XML×0.065. Detectability is proven real: min over 32 sites of max|packet − XML×0.065| = **0.0111615625** (per-site deltas in the table; no site is all-zero, so the 0.065 hypothesis is distinguishable from the verbatim hypothesis at every site — had the factor been applied, exact== would be False for all 32). Packet field label `source_pos_local_units` reads "source SI (metres), verbatim from the XML — NOT scaled by the target mesh factor" on every site, matching report-05 §1 (line 11).

Identity detail (criterion 1c): every site's XML owning body equals its packet `source_body` (radius right / radius_l left). Every site is referenced by exactly one spatial tendon (membership count 1/1 for all 32; multi-membership scan silent), with `index_in_path` and `path_length` matching the XML `<spatial>` child order exactly (e.g. BIClong-P11: index 9 of path length 10 in `BIClong_tendon`). Packet per-membership `role` and aggregated `endpoint_roles` match the index-derived role in all 32.

---

## B. Completeness (criterion 1/3 adjunct)

- All 32 packet sites exist in the XML under the expected body: right `radius` set == packet set (16==16), left `radius_l` set == packet set (16==16). `packet_not_in_xml` = [] (no invented sites), `xml_not_in_packet` = [] (no missing sites), no duplicate site names.
- Global scan: the XML holds **937 site elements = 468 named anatomical sites + 469 unnamed tendon-path refs** (`<site site="..."/>`). All 468 named sites are globally unique. Each of the 32 audited sites belongs to ≥1 spatial tendon (in fact exactly 1); 120 spatial tendons enumerated.
- Observation (out of audit scope, no effect on the 32): the campaign brief's "937 sites, 468 tendon-referenced" inverts the two counts — 937 is the element total and 468 is the named-site count; tendon path references number 469. Recorded as an observation, not repaired.

---

## C. Role counts vs report-05 law (criterion 2) — FINDING (falsifier fired)

Derived independently: role per (site, tendon) membership from path index — 0 ⇒ `first_endpoint`, last ⇒ `last_endpoint`, interior ⇒ `waypoint` (same rule as `code/attachment_candidates.py:71-82`, reimplemented, not called).

Measured (site-level == membership-level; every site has exactly one membership):

| Scope | first_endpoint | last_endpoint | waypoint |
|---|---|---|---|
| right (radius) | 0 | **4** | 12 |
| left (radius_l) | 0 | **4** | 12 |
| **total** | **0** | **8** | **24** |

The 8 last-endpoint sites: BIClong-P11/l, BICshort-P8/l, BRD-P3/l, PT-P5/l. Confirmed: 0 first-endpoints anywhere — every tendon path enters the radius at an interior index, exactly as report-05 line 29 asserts.

**FINDING (itemized, not repaired):** `session_reports/anatomy_compiler_05.md` line 29 states "Measured law unchanged: **8 last-endpoints per side**, 0 first-endpoints (every tendon path enters the radius at an interior index), 24 waypoints."
- Report claim: 8 last-endpoints **per side**.
- Measured: **4 last-endpoints per side** (right 4, left 4).
- Reconciliation: the report's numbers 8 / 0 / 24 are exactly the **two-side totals** (4+4 last, 0+0 first, 12+12 waypoints). The "per side" qualifier on "8 last-endpoints" is contradicted by measurement; the raw numbers themselves are correct as totals. Under the frozen falsifier ("any count mismatch fails the audit"), this is a genuine mismatch between report text and measurement, so criterion 2 is recorded **FAIL as worded** while the packet's underlying per-site role data is fully self-consistent.

---

## D. Provenance uniformity (criterion 3) — PASS

Structure: the packet carries **one** `provenance_hashes` block at the top level (`runs/attachment_candidates.json`); **no per-site provenance keys exist** on any of the 32 candidates (scan found none). Uniformity therefore holds by construction — there is exactly one block, and all 32 sites share it.

All pinned values recomputed from bytes, independently:

| Field | Pinned | Recomputed | Match |
|---|---|---|---|
| source_xml_raw_sha256 | 675e00d0898cf7a175f3e4fe8f240eb24301c2f5e201ffa9215aea45b01b83d1 | identical | YES |
| source_xml_canonical_sha256 | 7caa32c6e31e319876ea21625b662c5c00e736038f542b38ce6b0cb81aadc8a5 | identical | YES |
| fitted_packet_sha256 | a447555069748d7fe421ff2a4ddeaa108729924ae088478741c86c38c3880937 | identical to sha256 of `runs/actual_monkey_fit.json` (identified by hashing all 12 files in `runs/`; unique match) | YES |

Cross-check: `MANIFEST.json` lines 10-11 pin the same a4475550… (actual_monkey_fit.json) and 854f7097… for attachment_candidates.json — my recompute of the packet file also gives 854f7097…. No per-site deviation to flag. Provenance assignment code: `code/actual_target_fit.py:649-654` (packet sha computed from written bytes at `:592` `write_json`, then raw/canonical hashes copied from intake metadata at `intake.py:60-65`).

---

## E. Canonical-hash recipe (criterion 4) — PASS (reproduced, first attempt)

Recipe found at `code/intake.py:57-65`:
```python
with open(path, "rb") as fh: data = fh.read()
sha = hashlib.sha256(data).hexdigest()
canonical = data.replace(b"\r\n", b"\n").rstrip(b"\n") + b"\n"
sha_canonical = hashlib.sha256(canonical).hexdigest()
```
My independent reimplementation (in `scripts/audit_sites.py`, written from the recipe, not imported): `sha256(xml_bytes.replace(b"\r\n", b"\n").rstrip(b"\n") + b"\n")` → `7caa32c6e31e319876ea21625b662c5c00e736038f542b38ce6b0cb81aadc8a5` — **matches** the packet and the expected 7caa32c6… exactly. Raw hash also reproduced: sha256(on-disk bytes) → 675e00d0… match. (The recipe itself notes the on-disk file differs from pinned upstream bytes only by a trailing CRLF — intake.py:61-63, 72-73.)

---

## F. Baseline integrity (criterion 5) — PASS

```
$ git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot
(empty output; exit 0)
```
No baseline file was modified, created, or deleted by this audit. All audit writes are confined to `forearm_package/audits/A3_site_audit/`.

---

## RECEIPTS (exact commands)

```
mkdir -p forearm_package/audits/A3_site_audit/{scripts,receipts}
PYTHONDONTWRITEBYTECODE=1 python forearm_package/audits/A3_site_audit/scripts/audit_sites.py
  → "n_rows": 32, "n_pass": 32, "n_fail": 0 ; spatial_tendon_count 120 ; xml_total_sites 937
  → role_counts_site_level: right {first 0, last 4, waypoint 12} ; left {first 0, last 4, waypoint 12}
  → raw_sha_recomputed == expected 675e00d0… ; canon_sha_recomputed == expected 7caa32c6…
  → fitted_packet_sha256_search.matches: ["actual_monkey_fit.json"]
git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot   # empty
```
Full per-site evidence (XML raw strings, both float triples, scaled values, all membership comparisons): `receipts/audit_receipt.json`.

## UNCERTAINTIES / NEGATIVE FINDINGS PRESERVED

1. **Role-count law wording (the one FAIL):** §C above. The packet data is consistent; the report-05 sentence's "per side" scoping is the mismatch (8/0/24 are totals). Judgment call documented: I did not accept "totals" as satisfying a claim that says "per side".
2. None on hashes: all three pinned hashes reproduced byte-exactly on the first attempt; no residual uncertainty.
3. Observation recorded (§B): brief's "468 tendon-referenced" vs measured 469 tendon path refs / 468 named sites — wording inversion upstream of this audit; no effect on the 32 sites.

**STOP RULE:** all five criteria have verdicts; no blocker remains. Audit complete.
