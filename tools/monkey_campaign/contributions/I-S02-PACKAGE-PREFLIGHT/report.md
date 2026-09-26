# I-S02-PACKAGE-PREFLIGHT — report

Card `I-S02-PACKAGE-PREFLIGHT` (slot 8), attempt `4139256674844346ae7c21857442d3f2`,
branch `codex/monkey-i-s02-package-preflight-4139256674`. Bounded implementation;
CPU-only; no GPU; no engine; no training; no game package built or published; no
mesh/model copied. Source repository `E:/ChimeraWork/monkey-play-20260924` treated as
READ-ONLY (pinned base `9afbddcd90164b5544a16fd0bc72278d985eb6e3`; every read via
`git show`, zero checkouts, zero extractions — all tests use synthetic packages).

## What exists at the pinned revision (step 3, recorded)

Tracked-file search at `9afbddcd` finds **no self-contained-package builder**. The
packaging-adjacent paths are repo-relative launchers (`DEMO.bat` sha `92cbcceca31a80a5`,
`tools/playable_slice/PlayableSlice.bat` sha `1b299af629b1ad78`, `run_slice.ps1` sha
`3c59439b40f7dad9` — all `%~dp0`-anchored, finding installed Python) and the RETIRED
Unreal-era `Chimera/core/uat_packager.py` (sha `8ba24dfea4a8453a`, UE detection —
not the game). S02's builder is future work; this card delivers the preflight checker
that validates its manifests. Read-first `product/session_flow.py` (sha
`30e06c04dc33da27`) supplied the product-module idiom (injected deps, headless,
prereg-frozen shape).

## What was built

`package_preflight.py` (sha256 `d51e8718a1c3b4802d8411a8e6a6ac8f2f6cf8f52360fcefe48b01d45b97f15e`)
— a caller-supplied-manifest structural preflight (schema `chimera.package.manifest.v1`).
Named checks: P-MISSING, P-PATH (absolute/drive/UNC/`..`), P-JUNCTION (reparse point
escaping the root, resolved-path containment), P-SIZE (declared-vs-actual and cap),
P-HASH (sha256), P-DEP (undeclared module imports in `text_config` .py entries),
P-EXT-TOOL (undeclared system executables in text configs), P-DEVROOT (development-root
references), P-DUP, P-TEXT (UTF-8), P-MANIFEST (schema/cap). Verdict vocabulary is
exactly {`PREFLIGHT-PASS`, `PREFLIGHT-FAIL`} — structurally incapable of a
distribution-permission claim (S01's MorphoSource BLOCKED-FOR-SHIP rows cannot be
blessed by this tool; enforced by test).

Scope laws held: package root arrives only as a call argument; manifests carry no
absolute paths; only `text_config` entries are content-scanned; hashing is capped by
`max_file_bytes` (oversize → P-SIZE, digest never verified from an unbounded read);
no directory enumeration — `stats["paths_opened"]` records every touched path and the
suite asserts none escapes the root.

`test_package_preflight.py` (sha256 `fe279eb04a563c7748b5d000df4cee535db5408ca9a5678981b5780f4be272b8`)
— 17 tests, all synthetic packages under `TemporaryDirectory`.

## Verification (frozen prereg vs measured)

PREREGISTRATION.md (sha256 `6f8aeb6d7617864dd5caf6c44d7adcac91900edd8a9053f9587840591bdea568`)
was frozen BEFORE the module was written (mtime order preserved in the receipt).

| Prediction | Measured |
|---|---|
| clean package PASS, byte-identical findings at two roots | PASS + empty findings; `findings_json` equal at `a/deep/nest` and `b` (F1) |
| broken package fails IDENTICALLY at both roots (no root leakage in details) | equal verdict + equal `findings_json` (F1) |
| each named defect fires exactly its finding | P-MISSING / P-HASH / P-SIZE ×2 / P-PATH (traversal, drive, UNC, posix-abs) / P-JUNCTION (LIVE NTFS junction via `mklink /J`) / P-DEP (`numpy` underdeclared) / P-EXT-TOOL (`powershell` underdeclared) / P-DEVROOT (`E:/PythonChimera` at line 2) / P-TEXT / P-DUP — each fires its own check name |
| bounded hashing reads at most the cap | 1 MiB+5 B file against a 64 KiB cap → `bytes_read == 65536`, P-SIZE fired |
| no permission state expressible | `VERDICTS` exact; "permission"/"distribution" appear only inside the OUT-OF-SCOPE docstring; no API attribute carries permission/license naming (F3) |
| stdlib needs no declaration | `import json/os` clean with empty modules list |

Run: `python -B -m unittest test_package_preflight` → **17/17 OK** (twice; deterministic;
the junction test is live on this host — zero skips in the final runs; the earlier
symlink-based variant's skip was replaced by the junction, whose creation needs no
elevation).

## Honest deviations / notes

- Two test-code defects were found and fixed DURING the first run (launcher not marked
  `text_config`, so its `powershell` reference went unscanned; vocabulary test's
  docstring filter too strict). Both were failures of the TEST harness, not of the
  checker; final suite green with fixes recorded here.
- The `P-EXT-TOOL` watchlist (`powershell`, `python`, …) is module DATA by design; a
  package naming a different external executable in free prose is out of the checker's
  epistemic reach — declared-text-config structural scanning only, per the frozen scope.
- S02 remains OPEN: this is preparatory support only. S01 distribution terms (Vulkan
  component licenses, MSVC redist, MorphoSource restrictions) and R07 compatibility are
  unchanged and unreconciled by this card.

## Integration proposal (for the eventual S02 builder, not executed here)

1. The builder emits `chimera.package.manifest.v1` next to the package; preflight runs
   against the staged tree before any installer step; `PREFLIGHT-FAIL` blocks packaging.
2. `dev_root_patterns` should then include the actual build checkout path so leakage
   findings name the true origin.
3. `bytes_read`/`paths_opened` stats are the audit surface for the S03 clean-machine
   smoke (prove the package's launcher touches nothing outside its root at preflight
   time; runtime tracing is S03/U07 territory).

---

# CORRECTION — attempt 1b2d224dbae042aead907aded54a67d2 (2026-09-25)

Responds to the lead's CHANGES REQUIRED on PR #124 head `155a0f5c`. Base
module adopted byte-identical (sha256 `7ccb6649…`), prior 17-test suite
intact and passing in this workspace before the fix.

## Both defects reproduced failing-first (evidence: failing_first_base.txt)

- **R1 (the lead's reproducer)**: `config.py` = `import os, missing_dependency`
  with valid size/hash, no declared modules → BASE returned **PREFLIGHT-PASS**
  (defect confirmed: the regex read only the first name).
- R2: the base regex ALREADY flagged single-name `import numpy as np` and
  from-import modules `from foo import bar` — an earlier draft of this report
  claimed BASE missed those forms, which is empirically FALSE for base
  `7ccb6649…` (its per-line `re.MULTILINE` regex captures `numpy` / `foo`).
  The genuine base gap in R2's territory was the TAIL of a multi-name
  statement (`import os, json` → `json` unflagged), which R1 covers.
- R3: BASE was SILENT on unparseable .py files (it never parsed; no named
  parse refusal existed).
- R4: BASE opened and hashed files despite an invalid `max_file_bytes`
  (unbounded I/O).
- 3 of the 7 new correction tests FAILED against the base (the defect proof:
  R1, R3, R4 — `failures=3, errors=0`), recorded before any fix; the other 4
  passed on base already (see "Correction of evidence" below).

## The fixes (package_preflight.py, corrected sha256 `1f81f62e…`)

1. `_iter_imports` is now STRUCTURAL: `ast.parse`; multi-name statements yield
   EVERY alias; aliases resolve (`numpy as np` → numpy); from-imports yield
   the module (both `from foo import bar[ as baz]` → foo); relative imports
   (level>0) are package-internal and skipped; a file that does not parse is
   a NAMED `P-TEXT` refusal — never a silent skip.
2. Cap validation happens BEFORE any file I/O: invalid `max_file_bytes` →
   `P-MANIFEST` finding + immediate FAIL with `paths_opened=[]`,
   `bytes_read={}`. With a valid cap every file gets ONE bounded read of at
   most cap+1 bytes (the +1 sentinel only detects oversize; `bytes_read`
   reports content bytes within the cap, preserving the module's documented
   contract); hashing AND the text_config decode consume exactly those
   bounded bytes — the old uncapped second read is gone; oversize files get
   `P-SIZE` with no digest verified.

## Verification

`python -B -m unittest test_package_preflight test_correction` → **24/24 OK
(17 prior + 7 correction), run twice, deterministic**. Correction tests:
R1 reproducer now FAILS preflight with `P-DEP` naming `missing_dependency`;
aliases/from-imports flagged, relative sibling never; unparseable .py → named
`P-TEXT`; invalid cap → zero I/O; read-time cap enforcement (declared size
honest, actual > cap → `P-SIZE`, `bytes_read` ≤ cap, garbage hash NOT
verified for oversize files).

## Falsifier scorecard

The prior prereg falsifier "any new test passing against BASE — report
loudly" FIRED and is reported loudly: 4 of the 7 correction tests already
passed on the base (R2's alias/from-import shapes, R2's stdlib/declared pass,
R5's oversize and bounded-read checks); the 3 that failed (R1, R3, R4) prove
both lead defects real. No prior test broken (17/17 still green); no silent
skip survives; no read exceeds the cap; synthetic packages only — no
restricted assets touched or distributed; no production/source-repo edits.

## Correction of evidence — attempt 52645eef46df4af6aa0ca12a10542f9d (2026-09-26)

Responds to the operational lead's pre-publication verification
(arrival-876e63bf; evidence
`E:/ChimeraWork/monkey-coordination/lead-verify-20260926/I-S02-PACKAGE-PREFLIGHT.json`).
Two evidence defects in THIS correction record were confirmed and fixed; the
code fixes were independently verified sound (24/24 green twice, lead
reproducer fixed) and are NOT changed — `package_preflight.py`,
`test_package_preflight.py` and `test_correction.py` remain byte-identical to
the previously submitted candidate (sha256 `1f81f62e…`, `45343953…`,
`6a24a683…`).

1. **failing_first_base.txt regenerated by actually running the published
   tests against the adopted base bytes.** The prior record claimed
   `FAILED (failures=3, errors=2)` (= 5/7) and came from an earlier test
   draft; it was irreproducible. The PUBLISHED `test_correction.py`
   (`6a24a683…`) against the byte-verified base `package_preflight.py`
   (`7ccb6649…`, CRLF form of blob `d51e8718…` at PR #124 head `155a0f5c`)
   yields **`Ran 7 tests` → `FAILED (failures=3)`** — 3/7 failing (R1
   `test_multi_name_import_is_flagged`, R3 `test_unparseable_py_is_named_refusal`,
   R4 `test_invalid_cap_fails_before_any_io`), 4/7 passing on base (R2
   `test_aliases_multiple_and_from_imports`, R2
   `test_stdlib_and_declared_still_pass`, R5
   `test_oversize_enforced_at_read_time`, R5
   `test_bounded_read_never_exceeds_cap_plus_one`). Run TWICE, deterministic
   (0.040 s / 0.025 s), prereg frozen before the run; verbatim output of both
   runs replaces the artifact.
2. **report.md's R2/R3 statement corrected to observed behavior.** The claim
   "BASE missed `import numpy as np` / `from foo import bar`" was empirically
   false: the base regex matched single-name and from-import forms. Corrected
   above: the genuine base gap was multi-name import tails (R1) plus the
   silent skip of unparseable .py (R3). The 5-of-7 and "no new test passed
   against the base" claims were corrected to the measured 3/7 and 4/7.

Provenance of the regenerated evidence (hashes verified before and after the
runs): module `7ccb66494ea9ee1b95a6247a1ad25981108c769fc3efb2143422822406561738`,
test file `6a24a683ac930b4ba7bbe251daaae59ccdeeb0f223523418e2a844ad49408f61`;
corrected module (post-fix, unchanged from prior submission)
`1f81f62e3ad1b7030fd2d1de7d6d932bbdf323b8533c89c36e462bf29e246ba2`.
