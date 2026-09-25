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
