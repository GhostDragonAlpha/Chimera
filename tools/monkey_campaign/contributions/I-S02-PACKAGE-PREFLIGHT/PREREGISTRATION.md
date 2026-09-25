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
