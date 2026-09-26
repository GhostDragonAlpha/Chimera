# I-S02-PACKAGE-PREFLIGHT-FOLLOWUP — PREREGISTRATION (frozen before implementation)

Card `I-S02-PACKAGE-PREFLIGHT-FOLLOWUP` (development slot 3), attempt
`c469c25457294a6daf5cbc8aba8a40bd`, agent `arrival-cfc4a71bdf25473585dd24f1fd8aacae`,
criteria `b19c2b9e09610d10f9dd7e770e8735216aaa65c8c8e6001242cff396a03e8afc`.
Bounded implementation; CPU-only; no GPU; no engine start; no training; **no game
package is built, published or distributed by this card**; no mesh/model copied;
no production checkout edited. Every statement below was frozen BEFORE
`implementation.py` / `test_implementation.py` were written. All reads of the source
repository were read-only `git show` from the attempt checkout (branch-3, head
`c525b82c7c3ce0128565424764293a3c85811ab3`); zero working-tree files outside this
contribution directory are touched.

## 0. Physical quantities

This card consumes **no physical quantity**. Every number it freezes or measures is a
byte identity (file size in bytes, SHA-256 of exact bytes) or a test count. Nothing
here derives from, or alters, a physics constant, threshold, seed or training artifact.
S02's "clean machine launches" clause is not claimed by this card; the card only
connects two existing artifacts (packager lane inputs -> preflight manifest).

## 1. Pinned dependency lineage (byte-pin discipline)

Dependency: card `I-S02-PACKAGE-PREFLIGHT`, winning PR #153
(head `e0a0abc83c714dac7ae399da872ec9bdb376186f`, merge `e449405f3cfdad7ab69536c474c9bf6f4fbfc68c`,
merged 2026-09-26T19:39:36Z, per the frozen board record).

The winning checker is vendored BYTE-PINNED into this contribution:

- upstream path: `tools/monkey_campaign/contributions/I-S02-PACKAGE-PREFLIGHT/package_preflight.py`
  at head `e0a0abc8`
- vendored path: `reference/package_preflight__e0a0abc8.py`
- frozen identity: **11458 bytes, sha256
  `1f81f62e3ad1b7030fd2d1de7d6d932bbdf323b8533c89c36e462bf29e246ba2`**
- the adapter loads it BY PATH and re-verifies that sha256 before first use; any byte
  drift is a named `PIN-MISMATCH` refusal (falsifier F5). The checker's code is never
  copied, edited or re-implemented here.

## 2. The packager's actual entry point (identified, read-only, before any edit)

Searched the PR base `astra/gait-capture` @ `5e54c0b7` (the base of BOTH the winning
PR #153 and this followup) via `git ls-tree`/`git grep`/`git show`. The current
packaging lane is the **R1 double-click launch pair**:

| lane file @ 5e54c0b7 | bytes | sha256 | role (read from its own bytes) |
|---|---|---|---|
| `DEMO.bat` | 250 | `92cbcceca31a80a52e189659a3c613c03dece695ed2fd8bf7654a6b41f4df690` | "Double-click this" -> `powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\run_demo.ps1" %*` |
| `tools/run_demo.ps1` | 3605 | `6b12c3f7dbc6ec5d9f42b927f42f002eb5eb58169f661db3ee4333fc000eb089` | finds installed python, frees port 8765, starts `ChimeraEngine\gallery.py`, waits for `/live` |
| `ChimeraEngine/gallery.py` | 7353 | `8a326949b81175274109492e2200edd6bdab2f6cffba1dc45a723fe7103fd12a` | serves `gallery.html`; imports `splat_appearance` and (try/except) `live_viewer` |
| `ChimeraEngine/gallery.html` | 3187 | `5640c54f4539a548c56a1befaa31e0be504353e2c6eb75b2c406c480d730c6e2` | gallery page served by gallery.py |
| `ChimeraEngine/splat_appearance.py` | 33275 | `3fa559e46d6d93584892c694400683286a22f43c7a1343a8016bd996ed67869e` | imported by gallery.py |
| `ChimeraEngine/live_viewer.py` | 122566 | `4a223b7d4dd3bf1c154ccdee2f0ce9bbda33e0953eab7ef25b8e6a0494f61adb` | the live engine viewer (optional at gallery import time) |

All six are byte-identical at this attempt's head `c525b82c` and at the PR base.

Explicitly ruled OUT as the current packager entry point (recorded with their actual
identities at `5e54c0b7`):

- `Chimera/core/uat_packager.py` (9283 B, `8ba24dfea4a8453ac38fe5190ed1b028135a2586beb5b01d6fbaf1be55642ed2`)
  — RETIRED Unreal-era packager; detects Unreal Engine, not this game.
- `ChimeraEngine/demo.py` + `ChimeraEngine/demo_output/demo_manifest.json`
  (14217 B / `4aad0ca1…`, 253 B / `52112118…`) — a scripted camera-flight VIDEO tour;
  its "manifest" is render-output metadata, not a distribution manifest.
- `ChimeraEngine/bake_splats.py` + `ChimeraEngine/baked/bake_manifest.json`
  (6395 B / `7eb8bcea…`, 7554 B / `a5ce8b0c…`) — engine-internal splat-bake CACHE
  manifest (per-membrane `.npz`, truncated hashes), not a package manifest.
- `tools/playable_slice/` (the other double-click lane, `PlayableSlice.bat`) — exists
  only on the `monkey-play-20260924` branch lineage, NOT on this PR's base
  `astra/gait-capture`; out of this PR's lineage.

Honest boundary: there is STILL no self-contained-package BUILDER on this lineage (the
winning report's finding stands at the current base). `gallery.py`'s optional
`live_viewer` import closure reaches the whole engine (`ParticleEngine`, `matter`,
`theHuman`, `walker`, `one`, `lod`, `perf_guard`, `controller`, `touchables`,
`human_messenger` + third-party `numpy`/`PIL`) — the complete closure is future S02
builder work. This card therefore delivers the missing **manifest producer/adapter**
that (a) names the lane's actual declared inputs, (b) turns an EXTERNAL admission
decision over those inputs into a byte-pinned `chimera.package.manifest.v1` the
winning checker consumes, and (c) audits a staged tree for undeclared leftovers.

## 3. Expected behavior (the adapter's contract, frozen)

`implementation.py` (in this directory) provides, importing the pinned checker from
`reference/package_preflight__e0a0abc8.py` (path-loaded, sha-verified):

1. `load_pinned_preflight()` -> the pinned module; refuses `PIN-MISMATCH` unless the
   vendored bytes hash to the frozen `1f81f62e…` digest.
2. `produce_manifest(package_root, admission, *, package_name, max_file_bytes=1048576,
   declared_dependencies=None, extra_dev_root_patterns=())` ->
   `ManifestProduction` with verdict exactly `MANIFEST-PRODUCED` or `MANIFEST-REFUSED`:
   - the manifest declares ONLY files the admission record lists (the producer never
     enumerates directories for declaration — the admission list is the source of
     truth); an unapproved asset structurally cannot enter the manifest;
   - per admitted path it records: `path` (package-relative, forward slashes),
     `bytes` (actual size), `sha256` (hex digest of a bounded read of at most
     `max_file_bytes`), `text_config` (verbatim from the admission row),
     `role` and `admission_ref` (verbatim from the admission row — license/admission
     decisions stay EXPLICIT and EXTERNAL; the producer expresses no permission
     semantics of its own);
   - the manifest carries `schema = "chimera.package.manifest.v1"` (the pinned
     checker's constant, used verbatim), a positive integer `max_file_bytes`,
     `declared_dependencies` (caller-supplied `{"modules": [...], "system": [...]}`),
     and records `dev_root_patterns` (caller extension) for the runbook to pass back
     to `preflight(..., dev_root_patterns=...)`;
   - canonical output: `canonical_json()` is `json.dumps(..., sort_keys=True,
     indent=2, ensure_ascii=True)` + one trailing `\n`, with NO absolute path, NO
     source-root reference and NO timestamp — byte-identical for identical content
     regardless of the package's location on disk;
   - ALL-OR-NOTHING: any refusal yields `MANIFEST-REFUSED` with a list of named
     refusals and `manifest is None` (fail closed, no partial manifest):
     `ADMISSION-MALFORMED` (missing `source`/`entries`), `ADMISSION-INCOMPLETE`
     (row missing `path`/`role`/`decision_ref`), `PRODUCER-DUP` (same path admitted
     twice), `PRODUCER-PATH` (absolute / drive-anchored / UNC / `..` segment),
     `SOURCE-MISSING` (admitted file absent at `package_root`), `SOURCE-NOT-FILE`
     (admitted path is a directory), `PRODUCER-OVERSIZE` (file larger than the cap —
     mirroring the checker's bounded-read law), `PRODUCER-TEXT` (`text_config` row
     that does not decode as UTF-8), `PRODUCER-DEPS` (declared_dependencies not a
     dict of lists of str).
3. `audit_staging(package_root, manifest)` -> `StagingAudit` with named findings:
   `STAGE-UNDECLARED` (a regular file present in the staged tree that no manifest
   entry declares), `STAGE-MISSING` (a declared entry absent on disk), `STAGE-NOT-FILE`
   (a declared path that is not a regular file). Findings are sorted by
   (check, path); stats record `files_seen`. This is the one enumerating step, and it
   runs in the BUILDER's workspace before publication — the pinned checker itself is
   never asked to enumerate.
4. `run_preflight(package_root, manifest)` -> convenience connective tissue: calls the
   PINNED module's `preflight(manifest, package_root,
   dev_root_patterns=manifest.get("dev_root_patterns", ()))` and returns its result
   unchanged. The adapter adds no verdict of its own.

## 4. Falsifiers (frozen before implementation; each maps to named tests)

- **F1 relocation**: identical synthetic content staged at two different roots must
  give byte-identical `canonical_json()`, and the PINNED checker must return
  `PREFLIGHT-PASS` with identical `findings_json()` at both roots; a corrupted staged
  file must fail IDENTICALLY at both roots (same verdict, same findings bytes).
  Test names: `test_f1_manifest_bytes_identical_across_roots`,
  `test_f1_preflight_pass_identical_at_both_roots`,
  `test_f1_corruption_fails_identically_at_both_roots`.
- **F2 missing asset**: an admitted file absent at `package_root` must yield
  `MANIFEST-REFUSED` with `SOURCE-MISSING` and `manifest is None`; a file deleted
  AFTER a manifest was produced must be caught by the pinned checker as `P-MISSING`.
  Tests: `test_f2_missing_admitted_file_refuses_production`,
  `test_f2_deleted_after_production_fires_p_missing`.
- **F3 undeclared development paths**:
  (a) a `text_config` whose content embeds a development root string
  (`E:/PythonChimera`) must be declared faithfully (hash correct) but the pinned
  checker must fire `P-DEVROOT` naming the pattern and return `PREFLIGHT-FAIL`;
  (b) a staged file absent from the admission record must be named `STAGE-UNDECLARED`
  by `audit_staging` and must NOT appear in manifest entries.
  Tests: `test_f3_devroot_string_fires_p_devroot`,
  `test_f3_undeclared_staged_file_named_and_excluded`.
- **F4 admission externality**: an admission row without `decision_ref` must refuse
  `ADMISSION-INCOMPLETE`; an admission record without an external `source` line must
  refuse `ADMISSION-MALFORMED`; every produced entry carries `role` +
  `admission_ref`; and the producer's verdict vocabulary
  (`MANIFEST-PRODUCED`/`MANIFEST-REFUSED` + refusal codes) contains no
  distribution-permission claim (the only PASS/FAIL words in the system belong to the
  pinned checker's structural verdicts). Tests:
  `test_f4_missing_decision_ref_refuses`, `test_f4_missing_source_refuses`,
  `test_f4_entries_carry_external_admission_refs`,
  `test_f4_no_permission_verdict_in_producer_vocabulary`.
- **F5 byte-pin**: the vendored reference module must hash to
  `1f81f62e3ad1b7030fd2d1de7d6d932bbdf323b8533c89c36e462bf29e246ba2` and the adapter
  must route ALL checking through it (its `SCHEMA`/`VERDICTS` objects are used
  verbatim); a tampered copy in a scratch directory must be refused `PIN-MISMATCH`.
  Tests: `test_f5_vendored_bytes_match_pin`, `test_f5_tampered_copy_refused`,
  `test_f5_schema_verdicts_come_from_pinned_module`.
- **F6 unapproved asset exclusion (structural)**: staging MORE files than admitted
  must still produce a manifest declaring exactly the admitted set — the extra files
  appear only as `STAGE-UNDECLARED` audit findings, never as entries. Tests:
  `test_f6_manifest_declares_exactly_admitted_set`.

## 5. Test constraints

`python -B -m unittest test_implementation` from this directory; CPU-only; every test
builds its synthetic minimal package under `TemporaryDirectory`; no repository source
file is opened by any test (the only repo-owned bytes read are this contribution's own
vendored `reference/` copy, for the F5 pin check); no network; no junction/symlink
creation required by any test (the pinned checker's junction coverage is inherited, not
re-tested); fixtures are labeled fixtures — nothing here is native-acceptance evidence,
and no runtime/visual gate of S02 is claimed exercised.

## 6. Out of scope, by construction

No installer step; no publishing; no game package artifact committed; no claim of
commercial or distribution rights (S01's BLOCKED-FOR-SHIP MorphoSource rows stand
untouched and cannot be blessed by anything here); no change to any physics/threshold
source; no edit outside this contribution directory.

---

# CORRECTION ADDENDUM (CHANGES_REQUIRED on PR #167 head `a5124959`)

Frozen **before any correction edit to `implementation.py`/`test_implementation.py`
and before the post-fix run of the reviewing lead's reproducer**: 2026-09-26T23:13:25Z.
Correction attempt `a9ab83c83d7e4eb595d08440c54237c2`, agent
`arrival-4519bbf2c5944487965ca96ac718c5ff`; the card's criteria hash is UNCHANGED
(`b19c2b9e09610d10f9dd7e770e8735216aaa65c8c8e6001242cff396a03e8afc`). Sections 0-6
above stay frozen and in force; this addendum only narrows the producer's contract.

## C1. The two reproduced falsifiers (lead evidence at
`E:/Chimera/queue-check-20260926/pr167`, reproduced independently pre-fix)

- **F-GROWTH** (stat/read growth -> truncated success): the producer recorded the
  stat size, read the whole file, then hashed a slice. With an injected deterministic
  growth (4 -> 16 bytes) between stat and read at `max_file_bytes=8` it returned
  `MANIFEST-PRODUCED` with `bytes=4` and a sha256 of the FIRST 8 bytes
  (`924592b9…`) while actually reading 16 bytes — a truncated-content hash presented
  as the file's complete-content identity, and `bytes` inconsistent with the hash.
- **F-ALIAS** (lexical aliases admitted twice): `a.txt` and `./a.txt` were both
  admitted as two manifest entries for one file (same digest `88d4266f…` twice),
  because duplicate detection compared raw declared spellings and dot-segment rows
  were not canonicalized.

Pre-fix reproduction method (recorded): the lead's `reproduce.py` (sha256
`3403354eb6a8d0a4ba8bca65505405e977ee13f0a6b282f87fa168f99498bcea`), copied
read-only into a TEMP directory with only its one `src=` line re-pointed at this
attempt's checkout (which holds the returned head's byte-identical
`implementation.py`, `7cc592f9…`), run with `python -B` on synthetic TEMP inputs.
Observed output matched the lead's `results.json` byte-for-byte in substance:
`growth.verdict = MANIFEST-PRODUCED`, `bytes_actually_read = [16]`,
`entries[0].bytes = 4`, `entries[0].sha256 = 924592b9…`; `alias.verdict =
MANIFEST-PRODUCED` with both `a.txt` and `./a.txt` entries.

## C2. Correction contract (frozen before implementation)

1. **Bounded complete-content hashing / source-drift refusal** — the producer never
   presents read bytes as a file identity unless they are the COMPLETE content it
   hashed, and refuses by name whenever the read contradicts the declared limit or
   the observed source identity:
   - stat size > `max_file_bytes` -> `PRODUCER-OVERSIZE` BEFORE any read (existing
     law, unchanged);
   - read length > `max_file_bytes` -> `PRODUCER-OVERSIZE` (NEW): bytes actually
     read beyond the limit are refused, never sliced and hashed;
   - read length != stat size -> `SOURCE-DRIFT` (NEW named refusal): the source
     changed between stat and read; those bytes are never hashed into any entry;
   - an entry's `bytes` records the exact number of bytes hashed — the complete
     content actually read; `bytes` and `sha256` always describe the same bytes;
   - ALL-OR-NOTHING is unchanged: any refusal -> `MANIFEST-REFUSED`,
     `manifest is None`, no partial manifest.
   Documented boundary: the stat gate bounds routine reads to <= `max_file_bytes`;
   detecting a drift event requires observing the changed bytes once (they are then
   refused, not hashed); same-size concurrent rewrites are outside producer
   detection and are re-verified by the pinned checker's own re-read at preflight.
2. **Canonical duplicate handling** — declared package-relative paths are
   canonicalized before duplicate detection:
   - a declared path must BE its own canonical posix form:
     `PurePosixPath(rel).as_posix() == rel`; a `./` prefix, embedded `.` segments,
     redundant separators or a trailing slash refuse `PRODUCER-PATH` ("non-canonical
     path …"); this replaces the previous dead `.`-segment branch with a round-trip
     law (absolute/drive/UNC/`..`/backslash refusals are unchanged);
   - duplicate detection compares canonical identities CASE-INSENSITIVELY (explicit
     Windows case handling on this win32 lineage): a second declared row whose
     canonical identity equals an admitted one refuses `PRODUCER-DUP`, naming both
     declared spellings; this covers exact duplicates and case aliases (`A.txt` vs
     `a.txt`);
   - a genuine conflict (same canonical path, different declared entries, e.g.
     different `role`/`decision_ref`) is REFUSED, never silently deduped — dropping
     an admission row would misrepresent the external decision record;
   - no admission-vocabulary change: rows still carry `path`/`role`/`decision_ref`
     verbatim; declared canonical paths appear in entries verbatim.

## C3. Frozen predictions for the post-fix reproducer run (her probe, logic unchanged)

- growth probe: `verdict = MANIFEST-REFUSED`; `manifest = null`; exactly a
  `PRODUCER-OVERSIZE` refusal naming `a.txt` with the 16 B read against the 8 B
  limit in its detail; `bytes_actually_read == [16]`.
- alias probe: `verdict = MANIFEST-REFUSED`; `manifest = null`; `./a.txt` refused
  with code `PRODUCER-PATH` (non-canonical posix form).
If either probe still produces a manifest, this correction FAILS its own falsifier.

## C4. Regressions (frozen names, added to `test_implementation.py`)

- `test_correction_growth_read_over_limit_refuses_oversize` (mirrors the lead's
  growth probe: 4 -> 16 at limit 8; asserts `MANIFEST-REFUSED`, `manifest is None`,
  code `PRODUCER-OVERSIZE` naming `a.txt`, observed read length 16)
- `test_correction_growth_within_limit_refuses_source_drift` (4 -> 8 at limit 8:
  read fits the limit but contradicts the stat -> `SOURCE-DRIFT`, no manifest)
- `test_correction_shrink_refuses_source_drift` (stat 8 -> read 4 -> `SOURCE-DRIFT`)
- `test_correction_complete_content_hash_at_exact_limit_boundary` (8-byte file at
  limit 8 still PRODUCES; `bytes` == 8; `sha256` == sha256 of the complete bytes —
  guards against over-refusal and against any truncation)
- `test_correction_noncanonical_dot_alias_refused` (`['a.txt', './a.txt']` and a
  lone `'./a.txt'` -> `MANIFEST-REFUSED`, `PRODUCER-PATH` non-canonical)
- `test_correction_noncanonical_separator_forms_refused` (`'sub//x.txt'`,
  `'dir/'`, `'a/./b.txt'` -> `PRODUCER-PATH` non-canonical)
- `test_correction_case_alias_refused_as_canonical_duplicate` (`['a.txt', 'A.txt']`
  -> `PRODUCER-DUP` naming both spellings, no manifest)
- `test_correction_conflicting_duplicate_rows_refused` (same canonical path twice
  with different `role`/`decision_ref` -> `PRODUCER-DUP`, no manifest)

Existing tests: all 24 prior tests remain. The ONLY prior-test edit is the F4
frozen-vocabulary set gaining `SOURCE-DRIFT` (the vocabulary guard must know the new
named refusal; the guard's equality law itself is unchanged). The upstream pinned
reference `reference/package_preflight__e0a0abc8.py` stays BYTE-IDENTICAL
(11458 B, `1f81f62e…`) and is not edited; corrections live only in the
producer/adapter layer (`implementation.py`), its tests, and this documentation.
