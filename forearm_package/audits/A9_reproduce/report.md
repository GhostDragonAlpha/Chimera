# A9 REPRODUCTION AUDIT — Session 5 (independent reproduction + H-1)

**Agent:** A9 audit | **Date:** 2026-09-24 | **Quarantine:** `audits/A9_reproduce/work/`
**Brief:** `brief.md` (verbatim copy of the assigned brief). Baseline: `baseline_snapshot/` (read-only).
**Preregistration (frozen):** all tests green; every regenerated artifact byte-identical; H-1 confirmed; candidate record reproduces passed=false with the same optimum. **Falsifier:** any red test, any non-identical byte, or hash mismatch.

## HEADLINE

Session 5 **reproduces** from a clean copy on this machine today: the suite is green (after the one-shot clean re-run permitted by the stop rule; first-run red preserved verbatim below), **all 9 session-5 artifacts are bit-identical to the baseline** (including all 3 PNGs and the fit packet at `a4475550…`), determinism is proven independently (two full regenerations, 12/12 files identical), **H-1 is CONFIRMED** (the declared `fitted_packet_sha256` names the WRITTEN fit-packet bytes, `a4475550…`, not the candidates packet `854f7097…`; regeneration preserves the invariant), and the **candidate record reproduces exactly** (passed=false both sides, db=+6.24 mm, dc=±2.02 mm, byte-identical). Two findings are recorded and preserved (neither is a determinism break of the session-5 outputs): an environment-dependency in `run_tests.py` (S6 assumes `runs/` exists) and 3 stale pre-session-4-schema auxiliary artifacts in `runs/` that the frozen code cannot and does not claim to reproduce.

---

## 1. run_tests verdict + timing — PASS (with one preserved first-run red, diagnosed)

Receipts: `receipts/run_tests.out` (first run), `receipts/run_tests_rerun.out` (clean re-run), `.err` files empty.

- **First run** (pristine quarantine: snapshot `code/` + inputs, `runs/` NOT created): **48 PASS / 1 FAIL, exit 1.** Failure preserved verbatim:
  ```
  FAIL  s6_strict_json_export  -> FileNotFoundError: [Errno 2] No such file or directory: 'E:\\PythonChimera\\.tmp\\anatomy_compiler\\runs\\actual_monkey_fit.json.s6.json'
  ```
  Diagnosis (from the error itself, nothing fixed in code): S6 (`run_tests.py:660-695`) writes a temp probe to `str(actual_target_fit.OUT_PACKET) + ".s6.json"`; `OUT_PACKET` lives in `runs/` (`actual_target_fit.py:58-61`), and nothing in `run_tests.py` creates that directory. In the session-5 workspace `runs/` already existed (created by sessions 1–4; the snapshot's `runs/` still holds their outputs). A pristine copy of `code/` alone therefore cannot satisfy the suite. This is an **environment-dependency finding**, not a computation drift: the fit inside S6 completed; only the temp-file write hit a missing directory.
- **Clean re-run** (stop rule: ONE re-run; environment replicated to session-5 state by creating `runs/` EMPTY — no baseline outputs pre-seeded, so no byte-identity claim can be contaminated): **49 PASS / 0 FAIL, `ALL FALSIFIERS GREEN`, exit 0, wall 8.2 s.** G0 (2), F1–F7, S1–S14 all present and green.
- Wall time of the first run was not captured (missing `bc` in Git Bash); the re-run is the recorded timing. Suite cost is ~8 s; negligible.

## 2. Per-artifact byte-identity table — PASS for all 9 session-5 artifacts; FINDING for 3 stale auxiliary artifacts

Method: two complete regenerations (gen1, gen2) of every entry point, all exit 0. Full machine receipt: `receipts/byte_compare.{out,json}`.

| artifact (runs/) | baseline sha256 | gen1==gen2 | gen2==baseline |
|---|---|---|---|
| actual_monkey_fit.json | a447555069748d7fe421ff2a4ddeaa108729924ae088478741c86c38c3880937 | YES | **YES** |
| actual_monkey_tables.txt | c3f90f2342895eccb9a6ce2ef8dafca32e075bab0ca020c76eb6e4184f55397d | YES | **YES** |
| admission_actual_monkey.json | 833ca65b282eab83180bdbe65bbd8f934924fdd1416c8058d510e5481d86b4ad | YES | **YES** |
| attachment_candidates.json | 854f70976deb10264f052a8dafc3247c9bf6bf03761748e343329ce30e1032ae | YES | **YES** |
| experiment_transverse_candidate.json | 3c13fca70c2a726ec59379f2c5b1e597db3af5d82bedc39d0a4c08186f58ab3a | YES | **YES** |
| figure_actual_fit.png | b8e153c3a681e7b7f70d781f6e064d578c88ca942e412ca92e4165505b92fbd0 | YES | **YES** |
| figure_forearm_candidates.png | bb5095474c0b1603b71c9652c6098d24c12070c0015e0bc40d89197ee92aeed9 | YES | **YES** |
| figure_transverse_candidate.png | 1f514e9fe2850db418e2c888ab7020ef8ea61c7590eba3bd324300b449006eeb | YES | **YES** |
| _envelope_probe.json | ef4cd6b125086b2907c3a2b700c3c3741bb2be05ba7b8a17eac3bc1e49b9d2b7 | YES | **YES** |
| grounded_chimanoid.json | 457496993f7dbd1ea900e2c32f984fbc7c90402ef34d107fd2b3b38fa0ce47c4 | YES | **NO** (first diff offset 2308; gen +1136 bytes) |
| mirror_read.json | aa625a929fd18e9a60aa78bf6a6baebbd22dbdc724f3912e36feb234bedb230f | YES | **NO** (first diff offset 1741; gen +1136 bytes) |
| synthetic_twin.json | 92d6fecf824366c817904723401489defe4a9bc06fdef7d92b31fd37ca68e22f | YES | **NO** (first diff offset 1664; gen +1136 bytes) |

- **Determinism (S4): proven.** gen1==gen2 bit-identical for 12/12 files across two full regenerations (~30 s each, 6 entry points each, all exit 0). No RNG, no drift.
- **FINDING (non-identical bytes, preserved, not fixed):** the three `example_whole_body.py` artifacts (`grounded_chimanoid.json`, `mirror_read.json`, `synthetic_twin.json`) differ from the baseline copies. Structural diff (exactly 12 differences per file, identical pattern): the admission-ledger schema only — `admitted_physical` (17 bodies, mass totals 521.99/602.70 kg) replaced by the session-4 split `kinematically_admitted` + `physically_admitted=[]` + `transported_under_assumption`, plus added `mass_admission` and `audit.assumptions.geometry_resolution_does_not_discharge_density_validation=true`. This is the admission-split schema revision that session 4 introduced and S10 (`run_tests.py:934-958`) now pins. The baseline copies of these three files were last written by pre-revision code in an earlier session; session 5 did NOT regenerate them (report 05 §5's regenerated list does not include them), and the snapshot froze them stale. Excerpt at the first diff of each file (identical in all three): baseline `"root_ref_frame_not_scale_evidence": true` vs gen `"root_ref_frame_not_scale_evidence": true,` + `"geometry_resolution_does_not_discharge_density_validation": true`. All geometry/physiology/tendon fields are equal. **Classification: expected staleness of earlier-session side artifacts, NOT a determinism break of session-5 outputs.** The falsifier as pre-registered ("any non-identical byte") is reported as FIRED on these 3 files with the cause measured; verdict on the campaign claim ("Session 5 reproduces") is unaffected because none of the three is a session-5 output.

## 3. H-1 — CONFIRMED (independently recomputed)

Receipts: `receipts/h1_and_candidate.out`.

- sha256(baseline `runs/actual_monkey_fit.json`) = `a447555069748d7fe421ff2a4ddeaa108729924ae088478741c86c38c3880937` (matches MANIFEST and the coordinator's measurement).
- sha256(regenerated fit packet) = same value (bit-identical regeneration).
- sha256(baseline `runs/attachment_candidates.json`) = `854f70976deb10264f052a8dafc3247c9bf6bf03761748e343329ce30e1032ae`; regenerated = same.
- Declared field, read from BOTH packets: `provenance_hashes.fitted_packet_sha256 = a4475550…` — equals the **fit-packet bytes** on both sides; does NOT equal the candidates packet's own hash. Invariant preserved under regeneration.
- Defining code (baseline `code/attachment_candidates.py`, quoted):
  - Lines 57–63 (docstring of the parameter): `fitted_packet_sha256: sha256 of the WRITTEN fitted packet file bytes — a different object from the source XML hashes and labelled as such.`
  - Lines 204–213: `"provenance_hashes": { "source_xml_raw_sha256": None, "source_xml_canonical_sha256": None, "fitted_packet_sha256": fitted_packet_sha256, "note": ("source XML hashes identify the UPSTREAM anatomy file; " "fitted_packet_sha256 identifies the WRITTEN fitted packet bytes. " "They are different objects and never interchangeable.") }`
  - Module docstring lines 22–24: "hashes are SEPARATE: the source XML (raw + canonical) vs the actual fitted packet file (sha256 of the written bytes). The XML hash is never labelled as the fitted-packet hash."
  - The producer (`code/actual_target_fit.py:648-649`): `packet_sha = _hashlib.sha256(OUT_PACKET.read_bytes()).hexdigest()` — computed **after** `write_json(f, str(OUT_PACKET))` (line 592) — then `build_attachment_candidates(f, real, mt, corr, sw, fitted_packet_sha256=packet_sha)`. This is exactly the "sha256 of the WRITTEN packet bytes, computed after write_json" semantics stated by report 05 §3.
- **Verdict: the declared field names the FIT packet (the written `actual_monkey_fit.json` bytes), not the candidates packet and not an XML hash; regeneration reproduces the packet bit-identically and the invariant holds. H-1 = CONFIRMED.**

## 4. Candidate-record reproduction — PASS

`runs/experiment_transverse_candidate.json`: baseline and regenerated files are byte-identical (`3c13fca7…` both; parsed objects equal). Values (from the baseline file; identical in the regeneration):

- `step_C_candidate.radius`: `db_m=0.00624` (+6.24 mm), `dc_m=0.00202` (+2.02 mm), `passed=false`, `bounds_ok=true`, `fitting_sections_ok=false`, `additional_sections_ok=true`, objective 4.34689e-07 m², `max_displacement_m=0.006558811` (6.56 mm), loop authority at candidate: 0 outside / 14 inside / 0 tight / 2 ambiguous (ECRB-P3, ECRL-P3).
- `step_C_candidate.radius_l`: `db_m=0.00624`, `dc_m=-0.00202` (mirror-symmetric dc emerged from the two independent fits), `passed=false`, same counts (ambiguous: ECRB_l-P3, ECRL_l-P3).
- Matches report 05 §4 exactly: **passed=False on both sides**, db=+6.24 mm, dc=±2.02 mm, max site displacement 6.56 mm, strictly inside ±8 mm bounds. The failure stands as reported; nothing repaired, no second candidate run.

## 5. Environment record

- Python 3.14.3 (`C:\Python314\python.exe`, tags/v3.14.3:323c59a, MSC v.1944 64 bit), numpy 2.2.6, matplotlib 3.10.8 (PRESENT — all three figures regenerated and bit-identical), OS Microsoft Windows 10.0.26200.9457, shell Git Bash, `PYTHONDONTWRITEBYTECODE=1` throughout, no GPU/no network used.
- Wall times: suite 8.2 s (green re-run); full regeneration of all 12 artifacts ~30.0 s (6 entry points: `actual_target_fit.py` → `experiment_transverse_fit.py` → `figure_fit.py` → `figure_forearm_candidates.py` → `example_whole_body.py` → `target_envelope.py`); comparison/audit scripts < 1 s.

## 6. Baseline integrity receipts

- `git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot` — **EMPTY before** (first command of the session) and **EMPTY after** (post-restore). Receipts in this file's transcript; re-runnable.
- MANIFEST self-check: 44/44 files size+sha256 match (`receipts/integrity_check.out`, script `receipts/integrity_check.py`).
- The pipeline reads absolute paths OUTSIDE the snapshot (`code/synthetic_fixtures.py:28` REAL_XML=`E:\PythonChimera\.tmp\chimanoid.xml`; `code/mesh_target.py:31-32` MESH_BIRTH/PACK_JNT3=`E:\PythonChimera\Saved\meshes\monkey_{birth,joints}.bin`; outputs to absolute `E:\PythonChimera\.tmp\anatomy_compiler\runs` per `code/actual_target_fit.py:58`, `attachment_candidates.py:38`, `experiment_transverse_fit.py:98`; `run_tests.py:16` inserts `.tmp/anatomy_compiler` at sys.path[0]). All three live inputs verified hash-identical to the snapshot copies: chimanoid.xml `675e00d0…`, monkey_birth.bin `550a5b3e…`, monkey_joints.bin `74b3ab04…`. The snapshot's `code/*.py` (24 files) hash-match the live workspace's top-level `.py` files byte-for-byte, and the live `runs/` was 12/12 identical to the snapshot before the audit.
- Quarantine method (forced by the absolute paths — a cwd-only quarantine is impossible without editing the frozen code, which was forbidden): live `.tmp/anatomy_compiler` renamed aside to `.tmp/anatomy_compiler_A9_hold` after a full backup (`backup_tmp_anatomy_compiler/`, 47 files) and hash manifest (`receipts/restore_manifest_live.json`); a junction `.tmp/anatomy_compiler → audits/A9_reproduce/work` placed the quarantine copy at the hardcoded path so every read and write stayed inside this audit dir. After the audit the junction was removed and the original tree restored: **47/47 files byte-identical to the pre-audit state** (verified against the manifest), hold directory removed.

## UNCERTAINTY (explicit)

1. The exact historical session that last wrote the 3 stale auxiliary artifacts cannot be named from the snapshot (report 05 §5 does not list them; their schema predates the S10 admission split, i.e. session 3/4-era or earlier). The classification "stale, superseded schema" is measured (12 schema-only structural differences each; zero geometry/physiology differences); no pre-revision code exists in the snapshot to attempt their byte-reproduction.
2. First suite run's wall time was not captured (missing `bc`); 8.2 s is from the clean re-run. Immaterial to any verdict.
3. PNG byte-identity holds for this machine's matplotlib 3.10.8/Windows; a different renderer stack could legitimately produce different PNG bytes. On THIS environment, the reproduction target is met exactly.
4. The S6 first-run red's "session-5 environment had runs/ pre-existing" premise is supported by the presence of session-1..4 artifacts inside the snapshot `runs/` (evidence, not a transcript).

## Receipts index (all under `audits/A9_reproduce/`)

- `brief.md` — verbatim brief
- `receipts/run_tests.out`, `receipts/run_tests_rerun.out` (+ `.err`, both empty)
- `receipts/integrity_check.{py,out}` — MANIFEST 44/44, live inputs 3/3 MATCH
- `receipts/byte_compare.{py,out,json}` — full sha256 table, determinism + baseline axes, first-diff offsets
- `receipts/h1_and_candidate.out`, `receipts/candidate_numbers.out` — H-1 + candidate values
- `receipts/swap_tmp.py`, `receipts/restore_manifest_live.json` — swap/restore + 47-file restoration proof
- `backup_tmp_anatomy_compiler/` — pre-audit image of the live workspace
- `regen1/`, `work/runs/` — the two full regenerations (gen1, gen2)
- `work/` — the quarantine copy that was executed (snapshot code + inputs)
