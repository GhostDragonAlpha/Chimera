# I-S02-PACKAGE-PREFLIGHT-FOLLOWUP — report

Card `I-S02-PACKAGE-PREFLIGHT-FOLLOWUP` (development slot 3), attempt
`c469c25457294a6daf5cbc8aba8a40bd`, agent `arrival-cfc4a71bdf25473585dd24f1fd8aacae`,
criteria `b19c2b9e09610d10f9dd7e770e8735216aaa65c8c8e6001242cff396a03e8afc`.
Bounded implementation; CPU-only (`python -B` throughout); no GPU; no engine start;
no training; **no game package was built, published or distributed**; no mesh/model
copied; no commercial or distribution right claimed; zero writes outside this
contribution directory (in the isolated attempt checkout
`E:/ChimeraWork/monkey-coordination/kanban-attempts/I-S02-PACKAGE-PREFLIGHT-FOLLOWUP/c469c25457294a6daf5cbc8aba8a40bd/checkout`,
branch-3). All source reads were read-only `git show`/`git ls-tree`/`git grep`.

## 1. What was connected

The winning card `I-S02-PACKAGE-PREFLIGHT` (PR #153, head `e0a0abc8`, merge
`e449405f3cfdad7ab69536c474c9bf6f4fbfc68c`) delivered a structural preflight that
consumes a `chimera.package.manifest.v1` manifest **which nothing on this lineage
produced** — its own report names "the builder emits chimera.package.manifest.v1
next to the package" as future integration work. This card delivers that missing
producer, as an adapter over the packager's actual declared inputs, and pins the
winning checker byte-for-byte.

## 2. Frozen lineage and identities (steps 1-2, before any edit)

`PREREGISTRATION.md` (sha256
`a39ef0088e8cb8cc74076bb833ad938911fdcb9daddbb0fee44da55ec12ee517`, measured again in
section 7) was frozen BEFORE `implementation.py`/`test_implementation.py`
were written (mtime order preserved: prereg 16:05:37, reference copy 16:05:52,
implementation 16:08:03, tests 16:15:08). This card consumes **no physical
quantity**; every number below is a byte identity or a test count — nothing derives
from or alters physics, thresholds or training artifacts.

Pinned dependency (byte-pin discipline, `reference/` pattern):

- upstream: `tools/monkey_campaign/contributions/I-S02-PACKAGE-PREFLIGHT/package_preflight.py`
  @ `e0a0abc8` — **11458 bytes, sha256
  `1f81f62e3ad1b7030fd2d1de7d6d932bbdf323b8533c89c36e462bf29e246ba2`**
- vendored here: `reference/package_preflight__e0a0abc8.py`, byte-identical;
  `load_pinned_preflight()` re-verifies the digest on every load and refuses
  `PIN-MISMATCH` on any drift. The checker's code is never copied or modified.

## 3. The current packager entry point (identified, read-only)

Searched the PR base `astra/gait-capture` @ `5e54c0b7` (the base of both the winning
PR #153 and this followup; all six files byte-identical at this attempt's head
`c525b82c`). The current packaging lane is the **R1 double-click launch pair**:

| lane file @ 5e54c0b7 | bytes | sha256 | role |
|---|---|---|---|
| `DEMO.bat` | 250 | `92cbcceca31a80a52e189659a3c613c03dece695ed2fd8bf7654a6b41f4df690` | "Double-click this" -> `powershell … "%~dp0tools\run_demo.ps1" %*` |
| `tools/run_demo.ps1` | 3605 | `6b12c3f7dbc6ec5d9f42b927f42f002eb5eb58169f661db3ee4333fc000eb089` | finds installed python, frees port 8765, starts `ChimeraEngine\gallery.py`, waits for `/live` |
| `ChimeraEngine/gallery.py` | 7353 | `8a326949b81175274109492e2200edd6bdab2f6cffba1dc45a723fe7103fd12a` | serves `gallery.html`; imports `splat_appearance`; imports `live_viewer` opportunistically (try/except) |
| `ChimeraEngine/gallery.html` | 3187 | `5640c54f4539a548c56a1befaa31e0be504353e2c6eb75b2c406c480d730c6e2` | gallery page |
| `ChimeraEngine/splat_appearance.py` | 33275 | `3fa559e46d6d93584892c694400683286a22f43c7a1343a8016bd996ed67869e` | imported by gallery.py |
| `ChimeraEngine/live_viewer.py` | 122566 | `4a223b7d4dd3bf1c154ccdee2f0ce9bbda33e0953eab7ef25b8e6a0494f61adb` | live engine viewer |

Explicitly ruled OUT, with their actual identities at `5e54c0b7`:

- `Chimera/core/uat_packager.py` (9283 B, `8ba24dfea4a8453ac38fe5190ed1b028135a2586beb5b01d6fbaf1be55642ed2`)
  — RETIRED Unreal-era packager (detects Unreal Engine, not this game).
- `ChimeraEngine/demo.py` + `ChimeraEngine/demo_output/demo_manifest.json`
  (14217 B / 253 B) — scripted camera-flight VIDEO tour; render-output metadata,
  not a distribution manifest.
- `ChimeraEngine/bake_splats.py` + `ChimeraEngine/baked/bake_manifest.json`
  (6395 B / 7554 B) — engine-internal splat-bake CACHE manifest (truncated hashes,
  cache status), not a package manifest.
- `tools/playable_slice/` (`PlayableSlice.bat` R1 lane) — exists on the
  `monkey-play-20260924` branch lineage only; absent from this PR's base.

Honest boundary: there is STILL no self-contained-package builder on this lineage.
`live_viewer`'s import closure reaches the whole engine (`ParticleEngine`, `matter`,
`theHuman`, `walker`, `one`, `lod`, `perf_guard`, `controller`, `touchables`,
`human_messenger`, plus `numpy`/`PIL`). The complete closure is future S02 builder
work; the adapter is closure-agnostic and records this boundary in
`KNOWN_OPEN_CLOSURE_MODULES`.

## 4. What was built (adapter design)

`implementation.py` — the manifest producer/adapter, all checking routed through the
pinned module:

1. **`DEMO_LANE_INPUTS`** — the launcher lane's actual declared inputs with frozen
   byte identities (packager FACTS a caller may admit; the producer decides nothing).
2. **`produce_manifest(package_root, admission, *, package_name,
   max_file_bytes=1048576, declared_dependencies=None, extra_dev_root_patterns=())`**
   — turns an EXTERNAL admission record (every row: `path`, `role`,
   `decision_ref`; optional `text_config`) into a canonical manifest:
   - package-relative forward-slash paths (absolute/drive/UNC/`..`/backslash rows
     refuse `PRODUCER-PATH`), actual byte sizes, sha256 of bounded reads
     (oversize refuses `PRODUCER-OVERSIZE`, mirroring the checker's bounded-read law);
   - each entry embeds `role` + `admission_ref` — license/admission decisions stay
     EXPLICIT and EXTERNAL (missing `decision_ref`/`source` refuses
     `ADMISSION-INCOMPLETE`/`ADMISSION-MALFORMED`); declaration is admission-driven
     and the producer never enumerates to declare, so **an unapproved asset
     structurally cannot enter the manifest**;
   - `schema` is used verbatim from the pinned checker; `declared_dependencies`
     (modules/system) and `dev_root_patterns` are caller-supplied and recorded;
   - canonical bytes: `json.dumps(sort_keys=True, indent=2, ensure_ascii=True)` +
     `\n` — no absolute path, no root reference, no timestamp;
   - ALL-OR-NOTHING: any refusal -> `MANIFEST-REFUSED`, `manifest is None`.
     Verdict vocabulary is exactly `MANIFEST-PRODUCED`/`MANIFEST-REFUSED` + named
     refusal codes; the only PASS/FAIL words in the system remain the pinned
     checker's structural verdicts.
3. **`audit_staging(package_root, manifest)`** — the one enumerating step,
   builder-side before publication: `STAGE-UNDECLARED` (staged file no entry
   declares — undeclared development path or unapproved asset),
   `STAGE-MISSING` (declared entry absent), `STAGE-NOT-FILE` (declared path that is
   not a regular file); deterministic sort by (check, path).
4. **`run_preflight(package_root, manifest)`** — calls the PINNED
   `preflight(manifest, package_root, dev_root_patterns=manifest["dev_root_patterns"])`
   and returns its result unchanged. The adapter issues no verdict of its own.

## 5. Verification (frozen prereg vs measured)

Command: `python -B -m unittest test_implementation` from this directory.
**First final run: `Ran 24 tests` -> `OK` (0.186 s); second run `OK` (0.191 s);
deterministic.** 15 prereg-named falsifier tests + 9 contract tests, all on
synthetic minimal packages under `TemporaryDirectory`; no repository source file is
opened by any test (only this contribution's own vendored bytes and its own module
text); no network; no junction creation (the checker's junction coverage is
inherited, not re-tested). Fixtures are labeled fixtures — nothing here is
native-acceptance evidence, and no S02 runtime/visual gate is claimed exercised.

| Frozen prediction (PREREGISTRATION.md section 4) | Measured |
|---|---|
| F1 relocation: identical content at two roots -> byte-identical manifest; pinned checker PASS with identical `findings_json()` at both roots; corruption fails identically at both roots | `test_f1_manifest_bytes_identical_across_roots` / `test_f1_preflight_pass_identical_at_both_roots` / `test_f1_corruption_fails_identically_at_both_roots` — all PASS; canonical bytes equal across roots; corrupted staged file fires P-HASH+P-SIZE identically at both roots |
| F2 missing assets: admitted-but-absent file -> `MANIFEST-REFUSED` + `SOURCE-MISSING`, `manifest is None`; file deleted after production -> pinned `P-MISSING` naming the path | `test_f2_missing_admitted_file_refuses_production` / `test_f2_deleted_after_production_fires_p_missing` — PASS (`ChimeraEngine/gallery.py` named) |
| F3 undeclared development paths: (a) dev-root string declared faithfully but pinned checker fires `P-DEVROOT` naming the pattern -> `PREFLIGHT-FAIL`; (b) staged undeclared file named `STAGE-UNDECLARED` and absent from entries | `test_f3_devroot_string_fires_p_devroot` (`e:/pythonchimera` named, hash still exact) / `test_f3_undeclared_staged_file_named_and_excluded` (`gallery_out.log`) — PASS |
| F4 admission externality: missing `decision_ref` -> `ADMISSION-INCOMPLETE`; missing `source` -> `ADMISSION-MALFORMED`; entries carry `role`+`admission_ref`; vocabulary frozen, no permission verdict | `test_f4_*` (4 tests) — PASS; producer literals scan equals the frozen vocabulary; `PREFLIGHT-*`/`APPROVED`/`LICENSED`/`PERMISSION` absent |
| F5 byte-pin: vendored bytes == 11458 B / `1f81f62e…`; tampered scratch copy refused `PIN-MISMATCH`; SCHEMA/verdicts verbatim from pinned module | `test_f5_*` (3 tests) — PASS |
| F6 exact admission: manifest declares exactly the admitted set; extra staged asset appears only as `STAGE-UNDECLARED` | `test_f6_manifest_declares_exactly_admitted_set` — PASS (`assets/unapproved_model.bin` excluded, audit-named) |
| Contract: path/dup/oversize/text/deps refusals; entries carry relative paths + sizes + hashes; stats; canonical form; dev-root patterns passed through to the checker | `AdapterContractTests` (9 tests) — PASS; produced clean manifest verifies `PREFLIGHT-PASS` through the pinned module |

## 6. Honest deviations / notes

- **Three TEST-harness defects fired during the first run and were fixed the same
  session (21/24 -> 24/24). The implementation matched the frozen prereg in all
  three cases; only the tests were wrong:** (1) `test_f6` expected an unsorted path
  list (`sorted()` orders `ChimeraEngine/…` before `DEMO.bat`); (2) the
  `STAGE-NOT-FILE` fixture staged an undeclared directory, but that check by
  preregistration fires for a *declared* path that exists and is not a regular file —
  the fixture now declares the directory; (3) the deps-passthrough test asserted the
  default `declared_dependencies` against a production that deliberately passed
  `system=["powershell"]`. Reported loudly per prereg discipline; no defect was
  hidden and no implementation behavior was tuned to a test.
- `STAGE-NOT-FILE` covers declared paths only; an undeclared EMPTY directory is
  invisible to the audit (it contains no file to ship). Recorded as a known audit
  boundary, consistent with the prereg's wording.
- The admission record's `decision_ref`/`source` values are pointer STRINGS; the
  producer cannot validate the external decision's existence or content — that is
  the point (decisions stay external). S01's BLOCKED-FOR-SHIP MorphoSource rows and
  the Vulkan/MSVC license questions are untouched and cannot be blessed by any of
  this.
- Integration runbook for the eventual S02 builder (matching the winning report's
  proposal): stage -> `produce_manifest` (admission-gated) -> write
  `canonical_json()` beside the package -> `audit_staging` (must be empty) ->
  `run_preflight`; `PREFLIGHT-FAIL` blocks packaging.

## 7. Artifact identities

sha256 of the exact bytes in this directory (proposed.patch excludes itself and is
hash-bound in the publication request):

- `reference/package_preflight__e0a0abc8.py` — 11458 B,
  `1f81f62e3ad1b7030fd2d1de7d6d932bbdf323b8533c89c36e462bf29e246ba2` (the #153 pin)
- `implementation.py` — 19495 B,
  `7cc592f942554c465c20fbdebfd6cb43a4fe148571b9c313c4c34013b6bd493e`
- `test_implementation.py` — 21906 B,
  `a3f97220b4fe387344cd9746ea9fa247befa8a05fa9256d947b184f8f825f575`
- `PREREGISTRATION.md` — 12711 B,
  `a39ef0088e8cb8cc74076bb833ad938911fdcb9daddbb0fee44da55ec12ee517`
- `report.md` — this file (hash bound in the publication request)
- `proposed.patch` — new-file patch (git format) adding PREREGISTRATION.md,
  implementation.py, test_implementation.py, report.md and reference/ against base
  `astra/gait-capture` @ `5e54c0b7`; excludes itself (self-reference); verified with
  `git apply --stat` / `git apply --check` on a pristine base tree.

Remaining gates (NOT claimed here): real admission decision over the demo-lane
inputs (S01/R07 lineage), the actual staged package, clean-machine launch evidence
(S03), runtime/visual verification. No package published; no rights claimed.

---

# CORRECTION REPORT (CHANGES_REQUIRED on PR #167 head `a5124959` resolved)

Correction attempt `a9ab83c83d7e4eb595d08440c54237c2`, agent
`arrival-4519bbf2c5944487965ca96ac718c5ff`; criteria hash unchanged
(`b19c2b9e…`). The correction prereg addendum (bottom of PREREGISTRATION.md,
frozen 2026-09-26T23:13:25Z) was written BEFORE any correction edit and BEFORE
the post-fix reproducer run. The lead's evidence
(`E:/Chimera/queue-check-20260926/pr167/REVIEW.md` + `reproduce.py` +
`results.json`, reproduced sha256 `3403354e…`) named two falsifiers; both are
fixed in the producer/adapter layer only. The upstream pinned reference is
UNTOUCHED (11458 B, `1f81f62e…` re-verified post-fix).

## C1. What changed (implementation.py, `7cc592f9…` -> `062f4ed9…`)

- Bounded COMPLETE-content hashing / source-drift refusal: the read is no longer
  sliced. A stat size above `max_file_bytes` still refuses `PRODUCER-OVERSIZE`
  before any read; a read longer than the limit now refuses `PRODUCER-OVERSIZE`
  ("read 16 B exceeds max_file_bytes 8 B (stat said 4 B); no truncated-content
  hash is produced"); a read whose length contradicts the stat now refuses the
  NEW named code `SOURCE-DRIFT`. An entry's `bytes` is the exact byte count
  hashed — `bytes` and `sha256` always describe the same complete bytes.
  Documented boundary (prereg addendum C2.1): the stat gate bounds routine reads
  to <= max_file_bytes; detecting a drift requires observing the changed bytes
  once (they are refused, not hashed); same-size concurrent rewrites remain
  outside producer detection and are re-verified by the pinned checker's own
  re-read at preflight.
- Canonical duplicate handling: a declared path must now equal its own posix
  normalization (`PurePosixPath(rel).as_posix() == rel`); `./` prefixes, `.`
  segments, redundant or trailing separators refuse `PRODUCER-PATH`
  ("non-canonical posix path …"), replacing the previous dead `.`-segment branch.
  Duplicate detection compares canonical identities case-insensitively (explicit
  Windows case handling on this win32 lineage): `a.txt` + `./a.txt` refuses
  (non-canonical), `A.txt` + `a.txt` and exact duplicates refuse `PRODUCER-DUP`
  naming both spellings, and a genuine conflict (same canonical path, different
  role/decision_ref) is refused, never silently deduped. ALL-OR-NOTHING
  (`manifest is None` on any refusal) is unchanged.

## C2. Reproducer, before and after (her probe logic unchanged; single documented
`src=` line re-pointed from the returned attempt to this attempt's checkout)

BEFORE (against returned head `a5124959`, implementation `7cc592f9…`): the
defect fires byte-identically to the lead's `results.json` —

- `growth.verdict = "MANIFEST-PRODUCED"`, `bytes_actually_read = [16]`,
  `entries[0] = {"path": "a.txt", "bytes": 4, "sha256": "924592b9…"}` (hash of
  the FIRST 8 of 16 actually-read bytes at limit 8);
- `alias.verdict = "MANIFEST-PRODUCED"` with BOTH `"a.txt"` and `"./a.txt"`
  entries (sha256 `88d4266f…` twice).

AFTER (corrected implementation `062f4ed9…`), her reproduce.py output verbatim:

```json
{
  "growth": {
    "verdict": "MANIFEST-REFUSED",
    "bytes_actually_read": [16],
    "manifest": null
  },
  "alias": {
    "verdict": "MANIFEST-REFUSED",
    "manifest": null
  }
}
```

Refusal details (supplementary probe printing `refusals_json()`):

- growth: `[{"code": "PRODUCER-OVERSIZE", "detail": "read 16 B exceeds
  max_file_bytes 8 B (stat said 4 B); no truncated-content hash is produced",
  "path": "a.txt"}]`
- alias: `[{"code": "PRODUCER-PATH", "detail": "non-canonical posix path (a
  declared path must equal its own posix normalization: no './' prefix, no '.'
  segments, no redundant or trailing separators)", "path": "./a.txt"}]`

Both match the prereg addendum's frozen predictions (section C3) exactly.

## C3. Regressions and suite state

8 new tests (`CorrectionRegressionTests`): growth-over-limit PRODUCER-OVERSIZE
(observed read 16), growth-within-limit SOURCE-DRIFT, shrink SOURCE-DRIFT,
complete-content boundary (8/8 still produces, hash == complete bytes),
non-canonical dot alias, non-canonical separator forms, case alias PRODUCER-DUP,
conflicting duplicate rows PRODUCER-DUP. The ONLY prior-test edit is the F4
frozen-vocabulary set gaining `SOURCE-DRIFT`.

`python -B -m unittest test_implementation` -> **Ran 32 tests (24 prior + 8 new),
OK**, three consecutive runs (0.203 s / 0.183 s / 0.194 s), deterministic,
CPU-only, synthetic TemporaryDirectory packages; no repo source opened by tests;
no GPU; no engine; no package built or published.

## C4. Correction artifact identities (supersede section 7 for the changed files)

- `reference/package_preflight__e0a0abc8.py` — UNCHANGED, 11458 B,
  `1f81f62e3ad1b7030fd2d1de7d6d932bbdf323b8533c89c36e462bf29e246ba2`
- `implementation.py` — 21648 B,
  `062f4ed92616a92aaa32976c3e7bf7b349838f77dbada5236446954e5f80f1da`
- `test_implementation.py` — 31253 B,
  `1eaea0bd6055b9c7566eb65639715f673f6d277d0fa5b6c64b9142609e6c8874`
- `PREREGISTRATION.md` — 19771 B (frozen sections 0-6 preserved verbatim;
  correction addendum appended),
  `1d550690030957a189d3c1abd8163b3fc92d513f4ac5dc043544d4850afea6a9`
- `report.md` — this file (hash bound in the publication request)
- `proposed.patch` — regenerated new-file patch (git format) adding the five
  content files against base `astra/gait-capture` @ `8567f629`; excludes itself.

Remaining gates unchanged and NOT claimed: real admission decision over the
demo-lane inputs (S01/R07 lineage), the actual staged package, clean-machine
launch evidence (S03), runtime/visual verification. No package published; no
rights claimed.
