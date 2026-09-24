# W1 PREREGISTRATION — source-bound regeneration verifier (frozen BEFORE implementation)

Frozen: 2026-09-24, before any verifier code was written and before any battery edit.
Author: W1. Worktree `E:/ChimeraWork/mvc-20260924`, HEAD `d1c99335`. Exporter revision
pin for this campaign: `1af0bbdee68d6ddfdd02bf9bd948f7b22f914d56` (never altered;
measured facts this design builds on: `git log 1af0bbde..HEAD -- tools/` is empty and
`git diff --stat 1af0bbde HEAD -- tools/` is empty — the pinned exporter and HEAD's
exporter are the same blob, `f6fd2af161705371cb9a59df941460ca2b8e2b84`).

## 0. The theory (Rule 0)

- **STATEMENT**: A delivered export report can be authenticated beyond diagnostic
  inspection by (a) possessing the exact source triple, (b) pinning the producer
  revision, (c) recomputing every input hash and the admission report with the pinned
  producer's own code, and (d) regenerating the complete report and comparing it to the
  delivered artifact under the exporter's own documented identity rule (its canonical
  JSON serialization). Any tampered value that survives this is a falsifier.
- **PREDICTION** (not yet measured): all 14 report-level value-class mutations of the
  B7 frozen matrix (M01–M14, the 9 the reader MISSES included) are caught as MISMATCH
  by this verifier; the genuine example report VERIFIES from this checkout's
  CRLF-materialized disk bytes (layer separation: trailing CRLF is not identity); the
  two B7 input-mutation controls (M07b, M09b) VERIFY against their own mutated inputs —
  producer agreement — which is exactly why the output must carry the decision's caveat.
- **FALSIFIERS** (named before the run, in §5). **Stop rule** in §6. No falsifier, no
  build; no falsifier may be tuned away after measurement.

## 1. Identity layers (B4 law, applied — this freezes which layer is used where)

1. **Disk/materialized bytes** (this checkout: CRLF smudge, e.g. example report
   5473 B, sha256 `d71f7621…`) — a checkout artifact. NEVER used as verification
   identity anywhere in the verifier or the battery's blob-form entry.
2. **Git blob bytes** at a pinned revision (LF, `git cat-file`/`git show`; example
   report 5472 B, sha256 `5485c8c4…`, OID `2091bee63193f029b4adf7a9e4bc88a2ce1f277b`)
   — the portable materialization identity. Used ONLY to obtain and byte-verify the
   pinned producer's code, and (battery M01-F1) as the blob-form reproduction target
   for `LF(CLI stdout)`.
3. **The exporter's own canonical identity** — `canonical_json(report)`:
   `json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
   allow_nan=False) + "\n"`, sha256 over the ASCII bytes. This is the exporter's
   documented report identity (its CLI emits exactly these bytes modulo the platform
   pipe newline; the verification receipt records this canonical hash). **ALL report,
   admission and input-hash comparisons in the verifier use THIS layer and no other.**

Cross-layer substitution (comparing raw disk bytes, or requiring the delivered FILE to
be byte-identical to anything) is forbidden — falsifier F-W1-3.

## 2. I/O contract (frozen)

```
python impl/W1_source_verify/material_volume_source_verify.py \
    --report <delivered report path> \
    --manifest <path> --partition <path> --groups <path> \
    --revision <git revision> \
    [--repo <repo root>] [--work-dir <dir>] [--output-json <path>] [--max-paths N]
```

- The verifier never imports the worktree's `tools/` modules for any hash, admission,
  or regeneration decision. It spawns `pinned_runner.py` (same dir) as a subprocess
  pinned to a byte-verified blob materialization of `--revision`.
- `pinned_runner.py` (inside the materialization's `sys.path` precedence) computes,
  with the PINNED modules only: strict parse of the three sources
  (`exporter.read_json_file`); `exporter._hashes(manifest, partition, groups)`;
  `admission.build_admission_report(manifest, partition)` + `exporter._canonical_hash`
  of it; `exporter.build_export_report(...)`; `exporter.canonical_json` of both the
  regenerated report and the strictly-parsed delivered report; sha256 of each.
- The driver compares returned hashes, itemizes JSON-path differences (stdlib
  `json.loads` for diffing only; hashing is never reimplemented), writes the verdict.

Output JSON (stdout; also `--output-json`) always carries: `verdict`, `caveat`
(the decision's sentence, verbatim, in every verdict including VERIFIED),
`identity` labels (which layer was used), `producer_revision`, `sources` (paths,
materialized-bytes sha256 labeled non-portable, canonical-parse sha256 labeled the
exporter's input identity), `checks` (named rows below), `mismatches` (itemized,
capped at `--max-paths`, default 20, with a truncation flag), `delivered_export_status`,
`delivered_admission_status`, `regenerated_export_status`, and
`independent_checks_note` (analytic checks are retained elsewhere; see §7).

Exit codes: `0` VERIFIED · `1` MISMATCH · `2` UNAVAILABLE-SOURCE · `3` PRODUCER-ERROR ·
`4` usage/internal error. A `--quiet` run still exits by these codes.

## 3. Verdict classes (frozen, mutually exclusive, priority order)

1. **UNAVAILABLE-SOURCE** — any of: a source path missing/unreadable; a source that
   fails the pinned `read_json_file` (invalid JSON, duplicate key, NaN literal, bad
   encoding); `--revision` unresolvable or its tree lacking any pinned producer module
   (`material_volume.py`, `material_volume_admission.py`,
   `material_volume_body_export.py`); repo root unresolvable; blob extraction or its
   byte-verification (`git hash-object` vs `git ls-tree` OID) failing.
   **Verification unavailable — never counted as acceptance, never a pass.**
2. **PRODUCER-ERROR** — sources and pin available, but the pinned producer itself
   fails to produce a parseable report (runner subprocess crash, non-JSON stdout,
   exception). Not a pass; not attributed to the delivered report.
3. **MISMATCH** — verification ran; at least one frozen check row failed:
   - `input_hash_manifest_sha256` / `input_hash_partition_sha256` /
     `input_hash_body_groups_sha256`: delivered `input_hashes.<name>` != recomputed
     `exporter._canonical_hash(source)`.
   - `input_hashes_declaration`: `algorithm`/`serialization` fields differ from the
     pinned `_hashes` declaration.
   - `admission_report_sha256_recomputed`: delivered
     `admission_report_sha256` != canonical hash of the pinned
     `build_admission_report(manifest, partition)`.
   - `report_canonical_identity`: sha256(`canonical_json(delivered)`) !=
     sha256(`canonical_json(regenerated)`).
   - `delivered_report_parse`: the delivered artifact cannot be strictly parsed
     (its canonical identity does not exist) — itemized as a mismatch of the
     delivered artifact, never a pass.
   All differing JSON paths itemized.
4. **VERIFIED** — all check rows pass: every input hash recomputed and equal;
   admission recomputed and equal; complete report regenerated by the pinned
   producer and equal under the exporter's canonical identity. The output still
   states the caveat (§7) and surfaces `delivered_export_status` /
   `delivered_admission_status` so VERIFIED can never be read as "the values are
   physically right".

## 4. Tolerances (frozen)

NONE. All comparisons are exact (canonical bytes / sha256 equality). No float
tolerance, no normalization beyond the exporter's own canonical serialization and
the `LF(CLI stdout)` rule for capturing subprocess output (B4: win32 pipes append
CR; the canonical layer is defined on content, and pinned canonical bytes are
LF-pure). The verifier applies no numeric tolerance anywhere.

## 5. Falsifiers (frozen before implementation)

- **F-W1-1 (tamper catch)**: every report-level mutation in the B7 frozen matrix
  (M01, M02, M03, M04, M05, M06, M07, M08, M09, M10, M10b, M11, M12, M13, M14 —
  corpus regenerated into `impl/W1_source_verify/tests/corpus/` from the frozen
  matrix definitions, never edited in the B7 dir) must verdict **MISMATCH** with a
  non-empty itemization. Any tampered report verdicted VERIFIED fires this falsifier
  and STOPS acceptance.
- **F-W1-2 (missing source is never a pass)**: deleting/renaming any source, an
  unresolvable revision, or an unparseable source must verdict **UNAVAILABLE-SOURCE**
  (exit 2) — never VERIFIED, never a silent skip-as-pass.
- **F-W1-3 (identity layer)**: the verifier's report identity is the exporter's
  canonical JSON layer. Demonstrated both ways: (i) a delivered report whose bytes
  differ from canonical ONLY by a trailing CRLF must still **VERIFY** (the live
  happy path on this checkout IS such a file — disk `d71f7621…` vs blob
  `5485c8c4…`); (ii) a recorded negative control shows the raw-bytes layer would
  have rejected that same file (raw sha != canonical sha), proving the verifier did
  not silently compare the wrong layer, and that a 1-content-byte change (B7 corpus)
  is rejected under the canonical layer.

## 6. Stop rule

Stop when: (a) this preregistration is frozen (hash recorded in
`receipts/00_prereg_sha256.txt` before implementation); (b) the verifier + test
suite are green, including all B7 value-class mutations caught (F-W1-1 quiet), the
battery failing-first sequence is receipted, and the append-style battery change is
applied with both identities labeled and the original checkout-dependent failure
preserved with its explanation. If any falsifier fires, it is reported, not tuned;
the stop rule is then NOT met.

## 7. The caveat (frozen wording, from the decision, verbatim)

> "Regeneration proves agreement with the producer, not correctness of the physical
> inputs or producer."

Every verifier output carries this sentence in `caveat`, plus
`independent_checks_note`: "Independent analytic checks are retained: the legacy
suites, proof batteries and admission/compiler refusals remain the correctness layer
for the physical inputs and the producer; this verifier adds source-bound producer
agreement only." The two B7 input-mutation controls (M07b/M09b regenerated in the
W1 dir) are the demonstration: they VERIFIED against their own tampered inputs is
the expected, correct outcome of an agreement check — and their reports themselves
say `blocked`/`not_admitted`, which the output surfaces.

## 8. Battery change (M01-F1), frozen shape — applied AFTER the failing-first receipts

- ADD to `tools/material_volume_export_proof_verify.py` (HEAD's battery only; the
  frozen revision 1af0bbde is never touched): one new test,
  `test_blob_form_reproduction_of_saved_example_report` — **BLOB-FORM IDENTITY
  (portable)**: `LF(CLI stdout) == git cat-file blob HEAD:tools/<example report>
  bytes == exporter.canonical_json(parsed)` bytes; explicitly labeled; labeled skip
  (never a pass) when git/blob is unavailable.
- RETAIN the original `test_cli_determinism_and_saved_example_bytes` as the separate
  **MATERIALIZED-FILE IDENTITY (checkout-dependent)** check with ALL original
  assertions intact, plus an appended explanation of the original checkout-dependent
  failure (M01-F1: LF materialization → 6/7 with a 1-byte trailing-newline
  difference, JSON equal; CRLF checkout → 7/7). The failure behavior is preserved,
  not normalized away.
- Failing-first sequence, receipted BEFORE the edit: (1) run the current battery
  from a raw-blob LF materialization — the original failure (6/7) captured;
  (2) run the blob-form test logic standalone — passes on genuine data pre-change
  (the property already holds; the battery lacks the entry).
