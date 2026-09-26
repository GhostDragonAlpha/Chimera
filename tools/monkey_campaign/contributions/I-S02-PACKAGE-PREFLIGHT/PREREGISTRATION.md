# PREREGISTRATION — I-S02-PACKAGE-PREFLIGHT (frozen before implementation)

Card: `I-S02-PACKAGE-PREFLIGHT` (Kanban slot 8), attempt `4139256674844346ae7c21857442d3f2`,
criteria hash `6198e40b…` is NOT this card's — this card's own criteria hash is carried by
the board (see receipt.json). Base revision `9afbddcd90164b5544a16fd0bc72278d985eb6e3`,
source repository `E:/ChimeraWork/monkey-play-20260924` (READ-ONLY for this card).
Planned S02 row (map): "Clean machine/user can launch without repo paths, development
Python or operator-installed tools beyond declared dependencies." S01 is BLOCKED-FOR-SHIP
on MorphoSource assets — preflight must be incapable of blessing around that.

## STATEMENT (someone could disagree with)

A manifest-driven, caller-rooted structural preflight can decide, from a caller-supplied
manifest plus the package tree alone, whether a self-contained package is INTERNALLY
coherent — every file present, relative, traversal/junction-contained, size-bounded,
hash-matching, with no undeclared external dependencies or development-root references in
its declared text configs — and that decision is INVARIANT under relocation of the package
to any directory, without scanning anything outside the package root and without ever
making a distribution-rights claim.

## PREDICTION (not yet measured)

1. A clean synthetic package preflights PASS at root A and at relocated root B with
   byte-identical findings (empty).
2. Each named defect fires exactly its own finding and flips the verdict to FAIL:
   missing file (P-MISSING), absolute/`..`/UNC path (P-PATH), junction/symlink escaping
   the root (P-JUNCTION), wrong sha256 (P-HASH), size mismatch / over-cap file (P-SIZE),
   undeclared module import in a declared text config (P-DEP), absolute reference to a
   development root in a declared text config (P-DEVROOT), reference to an executable
   outside the declared dependency list (P-EXT-TOOL).
3. Bounded hashing reads at most `max_file_bytes` bytes of any file (a 1 MiB file with a
   64 KiB cap reads exactly 64 KiB, measured).
4. The module's output vocabulary contains no permission state: the only verdicts are
   `PREFLIGHT-PASS` and `PREFLIGHT-FAIL`; no API or output can assert distribution
   permission (S01's BLOCKED-FOR-SHIP assets must remain un-blessable by construction).

## FALSIFIER (named before the run)

The card's own falsifier, decomposed into testable failures:

- **F1 (relocation)**: any finding (or its absence) differs between the same package
  preflighted at two different roots → the theory is dead; the checker has a location
  dependence.
- **F2 (undeclared dependency passes)**: a declared text config importing a module absent
  from the manifest's declared dependencies yields PASS → dead.
- **F3 (permission claim)**: any output field, verdict, or docstring-promised behavior
  that asserts or implies distribution permission (rather than structural coherence) →
  dead. Checked mechanically: the verdict enum is exactly {PREFLIGHT-PASS, PREFLIGHT-FAIL}
  and the word "permission" appears only in the out-of-scope disclaimer.

## SCOPE LAWS (frozen)

- The package root comes ONLY from the caller at call time; the manifest carries no
  absolute paths (relocation is a structural property, not a convention).
- Text configs scanned are EXACTLY the entries the caller marks `text_config: true`;
  nothing else is opened for content (binaries are hashed, never parsed).
- Hashing is size-capped by the manifest's `max_file_bytes`; oversize is a finding, never
  a full read.
- Development-root detection matches a caller-supplied pattern list (defaults cover
  `E:/PythonChimera`, `E:/ChimeraWork`, `C:/VulkanSDK`, `C:\Python3*`, and the package's
  own build checkout path supplied by the caller) — patterns are DATA, not code.
- No directory tree walks outside the package root; no subdirectory enumeration at all
  (manifest-driven only) — "never scan arbitrary user directories".
- No asset-rights inference: file roles (code/data/asset) are recorded as manifest facts,
  never graded.

## BASELINE RECORDED (read-only, at the pinned revision — sha256 of git-show bytes)

| identity | bytes | object |
|---|---|---|
| `92cbcceca31a80a5…` | 250 | `DEMO.bat` — repo-relative launcher (`%~dp0`) |
| `1b299af629b1ad78…` | 260 | `tools/playable_slice/PlayableSlice.bat` — same pattern |
| `3c59439b40f7dad9…` | 3,889 | `tools/playable_slice/run_slice.ps1` — finds installed Python; repo paths |
| `30e06c04dc33da27…` | 16,981 | `tools/monkey_campaign/product/session_flow.py` (read_first; product-module idiom) |
| `8ba24dfea4a8453a…` | 9,283 | `Chimera/core/uat_packager.py` — RETIRED Unreal-era packager, not the game |
| `7dde4dcb170c02fe…` | 15,533 | `agents/S01_provenance/report.md` — the shipped-surface matrix this checker must not contradict |

**Packaging entry point at the pinned revision: NONE EXISTS.** Tracked-file search at
`9afbddcd` finds repo-relative launchers only (above); `uat_packager.py` is the retired UE
pipeline. S02's builder is future work; this card supplies the checker its manifests will
be validated against. **No source files extracted** (the card permits extraction for CPU
tests; all tests use synthetic packages, so the read-only posture is total).

---

# CORRECTION ADDENDUM — attempt 1b2d224dbae042aead907aded54a67d2 (2026-09-25)

Responds to the lead's CHANGES REQUIRED on PR #124 head `155a0f5c` (base
module copied byte-identical, sha256 `7ccb6649…`; prior 17-test suite intact
in this workspace). Written BEFORE the fix; failing-first tests were run
against the BASE module first and their failures recorded.

## The two corrections

1. **AST import parsing** (the lead's reproducer): `_iter_imports` regex read
   only the first name — `import os, missing_dependency` returned
   PREFLIGHT-PASS undeclared. Fixed structurally: `ast.parse`; multi-name
   Import statements yield EVERY alias's top-level module; aliases
   (`import numpy as np` → numpy); ImportFrom yields the module (`from foo
   import bar [as baz]` → foo); relative imports (level>0) are
   package-internal and skipped; a file that does not parse is a NAMED
   `P-TEXT` refusal — never a silent skip.
2. **Read-time caps**: invalid `max_file_bytes` → P-MANIFEST finding and an
   EARLY FAIL with ZERO files opened (validate before I/O); with a valid cap,
   every file is read ONCE, bounded to cap+1 bytes — oversize produces
   `P-SIZE` with no digest verified, and the text_config decode consumes the
   SAME bounded bytes (the old code's uncapped second read is gone);
   `bytes_read` never exceeds cap+1 per entry.

## Failing-first predictions (measured against BASE before the fix)

- R1 lead reproducer: BASE PASS (defect) → FIXED FAIL with P-DEP naming
  `missing_dependency`.
- R2 aliases/multi/from: BASE misses numpy+foo (defect) → FIXED flags both,
  never the relative `sibling`.
- R3 unparseable .py: BASE silent (defect) → FIXED named P-TEXT refusal.
- R4 invalid cap: BASE opens+hashes files (defect) → FIXED zero I/O.
- R5 cap is read-time: oversize file (declared size honest) → P-SIZE,
  bytes_read ≤ cap+1, no hash verified; all 17 prior tests still pass after
  the fix.

## Falsifier

Any new test passing against BASE (defect not real — report loudly); any
prior test broken; a silent skip surviving; any read exceeding cap+1 when a
cap is set; restricted-asset distribution (none — synthetic packages only).

---

# CORRECTION-OF-EVIDENCE ADDENDUM — attempt 52645eef46df4af6aa0ca12a10542f9d (2026-09-26)

Responds to the operational lead's pre-publication verification finding
(arrival-876e63bf, evidence `E:/ChimeraWork/monkey-coordination/lead-verify-20260926/I-S02-PACKAGE-PREFLIGHT.json`):
the prior correction's failing-first EVIDENCE was irreproducible (recorded 5/7;
the published `test_correction.py` against the adopted base yields 3/7) and
report.md's R2/R3 claim was empirically false. Written and frozen BEFORE this
attempt's base run. The prior addendum's own falsifier — "any new test passing
against BASE (defect not real — report loudly)" — FIRED: two of the seven
published correction tests pass on the base. That firing is now reported loudly.

## STATEMENT (someone could disagree with)

The published failing-first record for attempt `1b2d224dbae042aead907aded54a67d2`
overstated the base's blindness. The honest record is whatever the PUBLISHED
`test_correction.py` (sha256 `6a24a683…`) actually produces against the
byte-verified adopted base `package_preflight.py` (sha256 `7ccb6649…`, CRLF form
of blob `d51e8718…` at PR #124 head `155a0f5c`), run verbatim, and this attempt
records that output unaltered whatever it turns out to be.

## PREDICTION (frozen before the run; derived only from reading the base source)

Base `_iter_imports` is a per-line regex (`re.MULTILINE`) that captures the FIRST
name of an `import` statement and the module of a `from X import` statement;
base cap handling validates `max_file_bytes` only into `cap=None` + P-MANIFEST
and proceeds to hash with bounded reads, enforcing the cap via pre-stat size.
Therefore, of the 7 published correction tests:

1. FAIL on base: `test_multi_name_import_is_flagged` (R1 — `import os,
   missing_dependency` yields only `os`; undeclared tail passes);
2. FAIL on base: `test_unparseable_py_is_named_refusal` (R3 — base never parses;
   no P-TEXT parse refusal exists);
3. FAIL on base: `test_invalid_cap_fails_before_any_io` (R4 — base records
   P-MANIFEST, then opens and hashes files anyway; `paths_opened` non-empty);
4. PASS on base: `test_aliases_multiple_and_from_imports` (R2 — the base regex
   ALREADY yields single-name `import numpy as np` → `numpy` and from-import
   modules `from foo import bar` → `foo`, and never matches `from . import`);
5. PASS on base: `test_stdlib_and_declared_still_pass` (R2);
6. PASS on base: `test_oversize_enforced_at_read_time` (R5 — base's pre-stat
   cap check already fires P-SIZE, reads at most cap bytes for oversize files
   and verifies no digest for them);
7. PASS on base: `test_bounded_read_never_exceeds_cap_plus_one` (R5).

Predicted bottom line: `Ran 7 tests` → `FAILED (failures=3)` — 3/7 failing,
4/7 passing on base. The code fixes are NOT in question (24/24 green verified
twice by the lead); this attempt rewrites NO working code.

## FALSIFIER (named before the run)

If the actual run's failure set differs from prediction 1-7 in any direction,
the ACTUAL result supersedes this prediction everywhere and is reported loudly;
no count is ever asserted that a recorded run does not show. If the run cannot
be reproduced at all, the evidence stays marked irreproducible and nothing is
published. Scope frozen: regenerate `failing_first_base.txt` from the verbatim
run; correct report.md's R2/R3, 5-of-7 and "no new test passed" statements to
the observed behavior; rehash every affected artifact; module and both test
files remain byte-identical to the published candidate (`1f81f62e…`,
`45343953…`, `6a24a683…`).
