# B9 — doccheck report: matter docs vs actual CLI behavior at the campaign base

**Agent:** B9 (documentation-example verification)
**Date:** 2026-09-24
**Workspace:** worktree `E:/ChimeraWork/mvc-20260924`, branch `material-volume-campaign-20260924`, HEAD `8d574a12`, base `3db8bc4e` (= merge-base with HEAD, verified).
**Scope frozen before any run:** `inventory.md` (this directory) — extraction rule R1–R5, comparison rules C-exit/C-num/C-bytes/C-hash/C-json, and 54 numbered examples. No material CLI was executed before the inventory file was written. Pre-freeze reads were limited to git state reads, `ls`, and the nine docs.
**Laws kept:** docs and tools untouched (integrity paste below); all executions from `work/repo/` copies with `PYTHONDONTWRITEBYTECODE=1`; every failure and false alarm preserved; CPU-only; writes confined to `agents/B9_doccheck/`.

## FALSIFIER STATUS

**Falsifier: any documented command that fails or any promised behavior absent. NOT FIRED at the level of executable claims.** Every documented command ran as written (54/54 decided: 48 MATCHES, 2 DRIFTED, 4 UNVERIFIABLE, 0 BROKEN). Both drift findings are documentation-wording defects, not failing commands or absent behaviors. One false alarm (determinism) was raised, diagnosed as B9's own capture pipeline (newline normalization), and re-run cleanly — both runs of that diagnosis are preserved in receipts.

## 1. Execution summary

- 11/11 `tools/material_volume*.py` accept `--help`, exit 0 (receipts `x01_*.txt`). argparse mains with exactly the documented flags: `material_volume.py` (positional input), `material_volume_admission.py` (`--manifest --partition`), `material_volume_body_export.py` (`--manifest --partition --groups`), `material_volume_body_export_reader.py` (positional report path), and the three proof/verify entry points. The unittest suites print unittest usage to stderr (rc 0); `material_volume_export_proof_prereg_derivation.py` has no argparse and ignores argv — `--help` runs the full derivation (18,553 bytes, exit 0), which is itself the documented behavior (L11-13).
- Suite counts at HEAD, all green and exactly as documented: compiler `Ran 17 tests OK`, admission `Ran 21 tests OK`, export checks `Ran 8 tests OK`, SI proof `Ran 5 tests OK`, FC proof `Ran 8 tests OK`, verify `Ran 7 tests OK`; derivation script exit 0 with `PREREGISTRATION CROSS-CHECK OK (H == Q == R2 within 1e-12; hand totals exact)`.
- Determinism: two direct exporter runs byte-identical (5473 bytes, `cmp` clean); stdout is exactly key-sorted compact canonical ASCII JSON, single line.
- V2 reproduced by unittest discovery at HEAD: 17/21/8/5/8/7 unique identities, 66 total = 59 leaf + 7 verification; the verification runner reports only `Ran 7 tests` — exactly the documented asymmetry.
- All four cited commits exist with matching subjects: `d2c23741` ("land compiler/export lane + freeze export-proof preregistration before execution"), `1af0bbdee68d6ddfdd02bf9bd948f7b22f914d56` ("body-grouping and frame-composition export proofs pass (SI 5/5, FC 8/8, verify 7/7)"; ancestor of HEAD), `02da40be` (forearm-package B2 — the "shared branch moved mid-session" revision), `f2bcac88` ("preregister verification checks V1–V3 before execution").
- Hash receipts reproduce: all 8 canonical LF SHA-256 first-16 values match; all 6 per-module listing digests match the construction `sha256("\n".join(sorted(Class.test_name ids)) + "\n")`; the 33-blob digest `ee27dcd2…` matches `sha256` over `ls-tree`-format lines (`100644 blob <oid>\t<path>\n`, path-sorted) of the 33-file set `tools/material_volume*` + 6 `Chimera/docs/matter/*.md` (i.e., excluding `matter_library.json`).

## 2. Verdict table (54 examples; details and line refs in `inventory.md`)

| id | doc | claim (short) | verdict |
|---|---|---|---|
| E-C-01 | compiler L36-63 | bipyramid fixture compiles; exit 0/1/2 semantics; checks battery | MATCHES |
| E-C-02 | compiler L128-132 | battery stdlib-only; final count 17/17 | MATCHES (`Ran 17 tests / OK`) |
| E-C-03 | compiler L63 | exit 1 unresolved; exit 2 named refusal | MATCHES (exit 1; `bad_schema` + detail; `unused_vertex` refusal also exit 2) |
| E-C-04 | compiler L133 | `py_compile` both files | MATCHES (run on work copies only) |
| E-C-05 | compiler L133 | example file: exit 0; V=1/3, m=1, COM (0.25,0.25,-1/12), 1 interface area 0.5 normal (0,0,-1) | MATCHES (all five exact) |
| E-C-06 | compiler L134 | env note: pytest unavailable | UNVERIFIABLE (historical env claim; today pytest 9.0.2 IS installed — recorded, no CLI promise affected) |
| E-C-07 | compiler L134 | "existing `Chimera/tools/surface_energy_checks.py`" | **DRIFTED** (finding F-B9-1) |
| E-C-08 | compiler L104 | `validate_mass_source_claims()` exists and rejects mixed ledgers | MATCHES (symbol at tools/material_volume.py:239; suite green) |
| E-C-09 | compiler L120-122 | output record fields | MATCHES (every named key present incl. `resolved_only_subtotal_not_body_total`, `boundary_faces`, `unresolved_adjacencies`, `connected_components`) |
| E-A-01 | admission L9-12 | five paths exist | MATCHES (5/5) |
| E-A-02 | admission L15-21 | documented invocation: exit 0, one canonical JSON report | MATCHES (stdout byte-equals canonical dumps; `validation_only_admissible`; `anatomical_completeness_certified: false`; no timestamps/paths) |
| E-A-03 | admission L19/L100 | checks suite green | MATCHES (`Ran 21 tests / OK`) |
| E-A-04 | admission L21 | exit 1 valid-not-admitted; exit 2 malformed/refusal | MATCHES (shrunk-partition variant: `not_admitted`, missing v4/cell-lower, exit 1; malformed JSON and unused-vertex variants: named refusal, exit 2) |
| E-A-05 | admission L38 | `volume_surface_ownership_collision` marked | MATCHES (dual-claim variant: `ownership.volume_surface_ownership_collisions = ["dual-matter"]`, `not_admitted`, exit 1) |
| E-B-01 | body_export L8-14 | documented command emits `chimera.rigid_body_mass_export.v1` to stdout | MATCHES (exit 0) |
| E-B-02 | body_export L17-18 | reader inspects written report | MATCHES (accepts exporter stdout verbatim; `complete`, `dynamics_readiness_claimed: false`) |
| E-B-03 | body_export L20 | schema/checks/fixture paths; groups version | MATCHES (`chimera.rigid_body_cell_groups.v1`) |
| E-B-04 | body_export L22 | coupon numbers; combined mass 3, V 1/3, COM (13/12, -5/12, 7/12) | MATCHES (recombination diff 0.0) |
| E-B-05 | body_export L42 | tensor metadata flags | MATCHES (true/true/false; `basis: authored_body_frame`; units as documented) |
| E-B-06 | body_export L48-56 | export_status enum; four safety flags false | MATCHES (all five statuses exercised; flags exact) |
| E-B-07 | body_export L62-64 | export checks green | MATCHES (`Ran 8 tests / OK`) |
| E-B-08 | body_export L44-46 | deterministic canonical output; input hashes | MATCHES (byte-identical reruns; canonical bytes verified; `input_hashes` + `admission_report_sha256` present) |
| E-FC-01 | fc-prereg L11-13 | derivation cross-check 1e-12 or fail | MATCHES (exit 0, cross-check OK) |
| E-FC-02 | fc-prereg L16-77 | four fixtures match frozen tables incl. composed matrices | MATCHES (21/21 content checks, incl. composition law R_DA=R_DP·R_PA) |
| E-FC-03 | fc-prereg L186-188 | FC proof runs; count 8 | MATCHES (`Ran 8 tests / OK`) |
| E-FC-04 | fc-prereg L102-121 | frozen run expectations at TOL 1e-12 | MATCHES (direct exporter comparison, all four bodies PASS) |
| E-SI-01 | si-prereg L10 | derivation path | MATCHES |
| E-SI-02 | si-prereg L15-43 | three fixtures match frozen tables | MATCHES |
| E-SI-03 | si-prereg L126-129 | SI proof runs; count 5 | MATCHES (`Ran 5 tests / OK`) |
| E-SI-04 | si-prereg L65-79 | frozen decimals; 1 internal face area 0.5 | MATCHES (bodies + recombination PASS at TOL; interface via suite F2, green; export report carries no interface field by design) |
| E-R-01 | results L14 | landing commit `d2c23741` exists | MATCHES |
| E-R-02/03 | results L15-16 | proofs 5/5, 8/8 | MATCHES (reproduced at HEAD) |
| E-R-04 | results L17, L100 | verify `Ran 7 tests OK` | MATCHES |
| E-R-05 | results L18 | leaf suites 17/21/8 all OK | MATCHES |
| E-R-06 | results L39-52 | deviations ≤ 9.44e-16 vs frozen expectations | MATCHES (conclusion reproduced; per-entry deltas are suite-internal — direct checks PASS at TOL 1e-12) |
| E-R-07 | results L18-19 | R1 clean-room + handoff-recorded battery | UNVERIFIABLE (historical execution record; live rerun done instead) |
| E-V-01 | v-prereg L4-5 | revision `1af0bbde` exists | MATCHES (full hash, ancestor of HEAD) |
| E-V-02 | v-prereg L27 | six suites green, counts 17/21/8/5/8/7 | MATCHES (V1 reproduced) |
| E-V-03 | v-prereg L28 | discovery: 66 = 59 leaf + 7 verification; runner prints `Ran 7` | MATCHES (V2 reproduced exactly) |
| E-V-04 | v-prereg L29 | V3 hashes | MATCHES (via E-VR-07) |
| E-VR-01..03 | receipt L3-8 | commits `1af0bbde…`, `02da40be`, `f2bcac88` exist | MATCHES (3/3, subjects consistent) |
| E-VR-04 | receipt L29-35 | per-module listing sha256[:16] (6 values) | MATCHES (all six reproduce; construction recovered, see §1) |
| E-VR-05 | receipt L49-63 | past-execution ledger (totals 328) | UNVERIFIABLE (historical run-count ledger; not decidable from today's tree) |
| E-VR-06 | receipt L84-89 | 33-blob listing digest `ee27dcd2…` | MATCHES (set and serialization recovered; exact match) |
| E-VR-07 | receipt L104-118 | canonical LF sha256[:16] of 8 artifacts at 1af0bbde | MATCHES (8/8 exact) |
| E-VR-08 | receipt L96-101 | V3 recheck 14/14, 14/14, 1/14 | UNVERIFIABLE (the 14 working-copy hash values are not printed in any doc; comparison inputs unavailable) |
| E-P-01 | contract L15-17 | exporter is the named producer | MATCHES |
| E-P-02 | contract L19-34 | full field/flag structure of the report | MATCHES (every named field, unit, frame, basis, and false flag verified in actual stdout; `input_hashes.serialization` = "UTF-8 canonical JSON (sorted object keys; array order preserved)") |
| E-P-03 | contract L39-54 | status semantics | MATCHES (unsupported/blocked/partial/refused exercised with B9-authored variants: `not_exported` ⇒ `mass_properties: null` + `reason_codes`; blocked carries `blocking_cell_ids`/`blocking_assignment_statuses`; partial carries `unassigned_cell_ids: ["cell-B"]`) |
| E-P-04 | contract L104-105 | CON-15: composition proven "≤ 9.4e-16" | **DRIFTED** (finding F-B9-2) |
| E-X-01 | brief mandate | `--help` on all 11 CLIs | MATCHES (11/11 exit 0; argv-handling classes recorded) |

Totals: **48 MATCHES · 2 DRIFTED · 4 UNVERIFIABLE · 0 BROKEN.**

## 3. Drift findings (itemized, with doc line references)

### F-B9-1 — DRIFTED path claim: `Chimera/tools/surface_energy_checks.py` (minor; outside the lane)

- Doc: `Chimera/docs/matter/material_volume_compiler.md` L134: "An unrelated **existing `Chimera/tools/surface_energy_checks.py`** invocation from the `Chimera/` working directory also stopped at its `evidence_output` import path (ModuleNotFoundError)".
- Observed: `E:/ChimeraWork/mvc-20260924/Chimera/tools/surface_energy_checks.py` does not exist. `git ls-tree -r 3db8bc4e` and `git log --all -- "*surface_energy*"` show the file only ever tracked as `tools/surface_energy_checks.py` (plus `docs/evidence/g01/` snapshots) — the `Chimera/tools/…` path was never in any tracked tree. An untracked copy does exist in the main checkout at `E:/PythonChimera/Chimera/tools/surface_energy_checks.py`.
- Impact: none on the material lane — the doc itself states that suite was NOT used as evidence. Reported because a path named as "existing" fails the existence check at this revision. Not fixed (docs read-only).

### F-B9-2 — DRIFTED numeric bound: CON-15 "≤ 9.4e-16" vs recorded 9.44e-16 (minor)

- Docs: `rigid_body_mass_export_consumption_contract_v1_proposal.md` L105 (CON-15): "proven equivalent to two-step composition on the FC coupon, **≤ 9.4e-16**". `material_volume_export_proof_results.md` L49/L67: "All deviations **≤ 9.44e-16**" / "within **9.44e-16**".
- Conflict: 9.44e-16 > 9.4e-16 — the contract's stated bound is contradicted by the results doc's own recorded maximum (0.4% above the bound; presumably a rounding slip from 9.44 to 9.4).
- Impact: none substantive — both are ~3 orders of magnitude inside the frozen TOL = 1e-12, and B9's direct re-measurement of all four FC frozen expectations PASSED at 1e-12. The bound as worded is still wrong and should read ≤ 9.44e-16 (or ≲ 1e-15). Not fixed (docs read-only).

### Environment note (not drift): pytest availability

- `material_volume_compiler.md` L134 records `pytest: command not found` in its authoring session. Today `python -m pytest --version` → `pytest 9.0.2` (exit 0). The claim is about that session's environment, not CLI behavior; the doc's instruction ("run the documented `python` command instead") remains correct and verified.

### UNVERIFIABLE items (no CLI promise affected)

- E-R-07: the R1 clean-room receipt and the "recorded at handoff" full battery are records of past executions; the live equivalents were re-run green (E-R-02..05).
- E-VR-05: the past-execution ledger (per-suite standalone/nested counts, totals 328) counts executions that happened in past sessions; not decidable from today's tree.
- E-VR-08: the V3 recheck ("recorded == … for 14/14; 1/14") compares against 14 previously reported working-copy hashes that the docs never print in full; the comparison inputs are not in the record. (The portable canonical manifest, E-VR-07, verifies 8/8.)
- E-C-06: historical environment claim, see above.

## 4. Receipts index (`receipts/`)

- Compiler: `c01a.txt` `c01b.txt` `c03_unresolved.txt` `c03_malformed.txt` `c04.txt` `c05.txt` `c06_pytest.txt` `c07_surface.txt` `c08_symbol.txt`
- Admission: `a01_exists.txt` `a02.txt` `a03.txt` `a04_exit1.txt` `a04_exit1_full.json` `a04_exit1_shrunk.json/.txt` `a04_exit2.txt` `a05_dual.out/.err`
- Export: `b01.txt` `b01_stdout.json` `b02.txt` `b07.txt` `b08_determinism.txt` `b08_run2.json` `p03_{unsupported,blocked,partial,refused}.{out,err,exit}`
- Proofs/verify: `fc01.txt` `si03.txt` `fc03.txt` `r04.txt`
- Git/hash/V2: `git_claims.txt` `v2_test_identities.json`
- `--help`: `x01_01…x01_11_*.help.txt`
- Derived outputs: `derived_outputs/{det1,det2,si_out,fcshared_out,fccomposed_out}.json`
- Variants authored by B9 (all inside `work/`, repo untouched): `work/repo/variant_*.json`, `work/repo/bipyramid.json`, `work/repo/body_mass_export.json`

## 5. Integrity (acceptance item 5)

```
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- tools Chimera/docs/matter
(empty — 0 lines; docs and tools untouched by B9)
```

Nothing was committed; B9 writes only under `E:/ChimeraWork/mvc-20260924/material_volume_campaign/agents/B9_doccheck/` (`brief.md`, `inventory.md` [frozen pre-run], `report.md`, `receipts/`, `work/`).
