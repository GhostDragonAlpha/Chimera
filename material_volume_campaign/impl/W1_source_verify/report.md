# W1 REPORT — SOURCE-BOUND REGENERATION VERIFICATION (Astra decision MV-VALUE) + battery M01-F1

Agent W1 · 2026-09-24 · worktree `E:/ChimeraWork/mvc-20260924` (session start HEAD
`d1c99335`) · exporter revision pin `1af0bbdee68d6ddfdd02bf9bd948f7b22f914d56`
(never altered — verified unchanged in the object store below) · CPU-only · no
runtime wiring. All W1 writes confined to `impl/W1_source_verify/` plus the
append-style edit to `tools/material_volume_export_proof_verify.py` (the file
this task owns for M01-F1).

**HEADLINE: the verifier is built, frozen prereg first, and the decided closure
holds — all 14 B7 report-level value-class mutations (including the 9 the reader
misses) are caught as itemized MISMATCH; the genuine example VERIFIES; missing
or unusable source is UNAVAILABLE-SOURCE (never a pass); a broken pinned
producer is PRODUCER-ERROR (never a pass); the exporter's canonical layer is
the only identity (trailing-CRLF-materialized reports still VERIFY, one-ULP
content changes do not). The battery now carries two labeled byte identities,
and the original checkout-dependent failure is preserved, explained, and
reproduced on demand. Falsifiers F-W1-1/2/3: none fired.**

## 1. Preregistration (frozen BEFORE implementation)

`prereg.md`, sha256
`0d8c8f35f9c90fbd3578e49fc2421f011079773dc888334462ba99a3d9411155`
(`receipts/00_prereg_sha256.txt`, frozen before any verifier code existed).
Frozen: I/O contract, four verdict classes with priority, zero tolerances
(exact canonical-byte comparisons only), the three falsifiers, the stop rule,
the caveat wording, the battery-change shape. No criterion was altered after
freezing. One implementation-stage defect was found and fixed in MY OWN
uncommitted verifier (not a prereg change): caller-supplied relative paths
broke inside the pinned-runner subprocess (different cwd) and surfaced as a
spurious PRODUCER-ERROR — fixed by resolving all caller paths to absolute
before spawning; suite re-run green after the fix (receipt 06).

## 2. What was built

- `material_volume_source_verify.py` — the verifier driver (the eventual
  promotion candidate). Never hashes anything itself: it spawns
  `pinned_runner.py` inside a byte-verified blob materialization of the pinned
  revision and compares the runner's returned identities.
- `pinned_runner.py` — ALL identity computation, in the PINNED producer's own
  code, replicating the exporter CLI's exact pipeline
  (`read_json_file -> build_export_report -> canonical_json`) plus the
  exporter's OWN `._hashes(manifest, partition, groups)` and
  `build_admission_report` + `._canonical_hash`. Nothing is reimplemented.
  Materialization = `git cat-file blob <pin>:tools/…` for the three producer
  modules, each byte-verified with `git hash-object` against `git ls-tree` OIDs
  (B4 layer 2; disk/`git archive` forms are never used).
- Verdicts (exit codes 0/1/2/3; usage 4): `VERIFIED` (every input hash
  recomputed and matching, admission recomputed and matching, complete report
  equal under the exporter's canonical JSON identity) / `UNAVAILABLE-SOURCE`
  (missing/unusable source, unresolvable pin, missing pinned producer modules,
  extraction byte-check failure — verification UNAVAILABLE, never accepted) /
  `MISMATCH` (any difference, itemized to JSON paths) / `PRODUCER-ERROR`
  (pinned producer fails to regenerate a parseable report — never a pass).
- Every output carries `caveat` = "Regeneration proves agreement with the
  producer, not correctness of the physical inputs or producer.", plus
  `independent_checks_note`, identity-layer labels, and the delivered report's
  own `export_status`/`admission_status` so VERIFIED can never be read as
  "the values are physically right".

## 3. Measured results (all in `receipts/`)

**Verifier suite (`tests/test_source_verify.py`): 9 tests, OK, exit 0**
(receipt `06_verifier_suite_run.txt`, re-run after the relative-path fix).

1. **Happy path**: tools example triple + the saved example report + the pin →
   `VERIFIED`, all 8 check rows pass. Cross-confirmations: canonical report
   sha256 `5485c8c4fe73d679…` == the B4/receipt canonical hash == blob
   `2091bee63193f029`; recomputed admission hash `a4ea955917b41eae…` ==
   M07's independently recorded C1 admission hash; input hashes match the
   delivered `input_hashes` exactly (`cab86eb6…`, `dd5aa016…`, `dcb55f1d…`).
2. **F-W1-1 (tamper catch) — quiet**: all 14 B7 report-level mutations
   M01–M14 → `MISMATCH` (exit 1) with non-empty itemization. The corpus was
   REGENERATED into `tests/corpus/` from the B7 frozen matrix definitions and
   verified content-IDENTICAL to B7's frozen fixtures (14/14 + valid report).
   This is the closure the decision bought: M02 (symmetry-preserving inertia
   diagonal), M04 (positive wrong mass), M06 (COM shift), M07 (density
   provenance), M08 (dropped provenance), M09 (impostor owner), M10 (status
   flip), M11 (readiness flag), M12 (tampered admission digest) — all the
   reader's misses — are caught, e.g. M04 itemizes
   `$body_groups[0].mass_properties.mass.value`. M14 (NaN literal) is caught
   via `delivered_report_parse` (the pinned strict reader refuses the file).
3. **The decision's caveat demonstrated, not just stated**: the B7 input-level
   controls M07b/M09b — reports regenerated by W1 from the mutated inputs —
   `VERIFY` against their own tampered inputs (producer agreement, as
   designed) while the output surfaces `export_status=blocked`,
   `admission_status=not_admitted/refused` (`missing_density`,
   `duplicate_mass_owner_id`), matching B7's receipts exactly. Agreement with
   the producer is not correctness of the inputs; the retained analytic layer
   (admission/compiler refusals) remains the input-correctness check.
4. **F-W1-2 (missing source never a pass) — quiet**: missing
   manifest/partition/groups/report, unresolvable revision, duplicate-JSON-key
   source, NaN-literal source → all `UNAVAILABLE-SOURCE`, exit 2 (6 cases).
5. **PRODUCER-ERROR is reachable and never a pass**: a scratch git repo
   (built under `work/scratch_broken_repo`, main repo untouched) whose pinned
   "producer" cannot emit JSON → `PRODUCER-ERROR`, exit 3.
6. **F-W1-3 (identity layer) — quiet**: (i) live happy path: the delivered
   file IS the CRLF disk materialization (5473 B, `d71f7621…`) and VERIFIES;
   (ii) explicit negative control asserts raw sha != canonical sha (the
   raw-bytes layer would have rejected it — proof the verifier did not
   silently compare the wrong layer); (iii) CRLF-ending, LF-only, and
   CRLF-everywhere materializations of the valid report all VERIFY; (iv) a
   one-ULP content change (`2.0 -> 2.0000000001`) is MISMATCH.
7. **Producer honesty**: `work/pinned_pincheck` materialization bytes ==
   `git cat-file blob <pin>:tools/material_volume_body_export.py` and !=
   the worktree's CRLF disk copy — the verifier demonstrably runs the pinned
   bytes. Per-verdict evidence JSONs: `receipts/verdicts/`.

## 4. Battery change (M01-F1) — append-style, failing-first

`tools/material_volume_export_proof_verify.py`: **61 insertions, 0 deletions**
(`git diff --numstat`). The frozen revision's battery blob is untouched
(`git cat-file blob 1af0bbde:…verify.py` sha256 `282bc52bfa997c6c…`, pre- and
post-change).

- ADD `test_blob_form_reproduction_of_saved_example_report` — **BLOB-FORM
  IDENTITY (portable)**: `LF(CLI stdout) == git cat-file blob
  HEAD:tools/material_volume_body_export_example_report.json ==
  exporter.canonical_json(parsed)`; labeled skip (never a pass) if git/blob is
  unavailable. Written FIRST as
  `tests/standalone_blob_form_prereg.py` and run against the PRE-change
  battery (receipt 03: passes on genuine data — the property already held;
  what the battery lacked was the entry).
- RETAIN `test_cli_determinism_and_saved_example_bytes` as the separate
  **MATERIALIZED-FILE IDENTITY (checkout-dependent)** check — every original
  assertion intact (0 deletions) — with the explanation of the original
  checkout-dependent failure appended (M01-F1: from a raw-LF blob
  materialization it fails at exactly one trailing byte, CLI 5473 vs saved
  5472, `\r` vs `\n` at offset 5471, JSON byte-identical; on this repo's
  `core.autocrlf=true` checkout it passes).
- Failing-first receipts: `01` PRE-change battery from a raw-blob LF
  materialization → `Ran 7 tests, FAILED (failures=1)`, the failure is exactly
  the materialized-file assertion (the original checkout-dependent failure,
  preserved on file); `02` PRE-change worktree → 7/7 OK; `03` blob-form test
  pre-change → OK; `04` POST-change worktree → **8/8 OK**; `05` POST-change
  battery from the LF materialization → `Ran 8 tests, FAILED (failures=1)`,
  the ONLY failure the labeled materialized-file check — the original failure
  behavior is preserved under the new labels, and the portable blob-form entry
  passes under BOTH materializations; `06b` standalone control post-change →
  OK; `08` battery re-run alongside the concurrent W3 reader change → 8/8 OK
  (nested 17/21/8/5/8 all green).

## 5. Caveat (decision-required, in the verifier's output)

Every verdict — including VERIFIED — states: *"Regeneration proves agreement
with the producer, not correctness of the physical inputs or producer."* plus
`independent_checks_note` (the legacy suites, proof batteries, and
admission/compiler refusals remain the correctness layer for the physical
inputs and the producer; this verifier adds source-bound producer agreement
only). The suite asserts its presence (happy path and M07b/M09b tests).

## 6. Shared-worktree concurrency note (honesty)

During this task, sibling implementers modified files W1 never touched:
`tools/material_volume_body_export_reader.py` (B7-M13 ragged-tensor refusal —
authored by `impl/W3_reader_m13/`, mtime 16:45, after my 16:37 battery edit)
and `material_volume_campaign/CAMPAIGN_REPORT.md` (since committed by them).
Those entries in the integrity paste below are THEIRS; W1's only tracked-file
change is the battery file. W1 reverted nothing of theirs and re-verified
coexistence (receipt 08: battery 8/8 including the reader-dependent test).
W1 also removed its own `tools/__pycache__` (gitignored; created when
`tests/build_corpus.py` imported the tools modules).

## 7. Acceptance verdicts

1. **Frozen prereg** — MET (`prereg.md`, sha256 above, frozen before
   implementation; no post-freeze criterion change).
2. **Verifier on the exporter's own functions** — MET (runner computes every
   identity with the pinned revision's `read_json_file`, `_hashes`,
   `_canonical_hash`, `build_admission_report`, `build_export_report`,
   `canonical_json`; the driver reimplements no hashing).
3. **Test suite green incl. all B7 value-class mutations caught** — MET
   (9/9 OK; 14/14 mutations → itemized MISMATCH; corpus content-identical to
   B7's frozen fixtures; M07b/M09b caveat behavior as designed).
4. **Battery change failing-first, both identities labeled, original failure
   preserved** — MET (receipts 01→05 sequence; 61+/0−; blob-form vs
   materialized-file labels; original failure and its explanation preserved
   in the file and reproduced in receipts 01 and 05).
5. **Caveat documented in output** — MET (every verdict JSON; asserted by
   tests; demonstrated by the M07b/M09b controls).
6. **Integrity** — MET, paste below, with the concurrency attribution.

## 8. Integrity paste (run after all writes, verbatim)

```
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain
 M tools/material_volume_body_export_reader.py        <- W3_reader_m13's, NOT W1's
 M tools/material_volume_export_proof_verify.py       <- W1's only tracked-file change (61+/0-)
?? material_volume_campaign/impl/W1_source_verify/    <- W1's dir
?? material_volume_campaign/impl/W3_reader_m13/       <- sibling's
?? material_volume_campaign/impl/W6_validator/        <- sibling's

$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- tools/material_volume_export_proof_verify.py material_volume_campaign/impl/W1_source_verify
 M tools/material_volume_export_proof_verify.py
?? material_volume_campaign/impl/W1_source_verify/

$ git -C E:/ChimeraWork/mvc-20260924 cat-file blob 1af0bbde:tools/material_volume_export_proof_verify.py | sha256sum
282bc52bfa997c6caa4296a306d8e577bf85cd7f9a8fcc09b664201445e3d941  (frozen rev unchanged)
```

No commit made (writes confined to the W1 dir + the owned battery file;
committing is the integrator's move).

## 9. Artifacts

- `brief.md` (verbatim) · `prereg.md` (frozen) · `receipts/00_prereg_sha256.txt`
- `material_volume_source_verify.py` · `pinned_runner.py`
- `tests/`: `test_source_verify.py` (9 tests), `build_corpus.py`,
  `standalone_blob_form_prereg.py`, `corpus/` (regenerated B7 adversarial set)
- `receipts/`: 01–08 battery failing-first sequence, 06 suite runs,
  `verdicts/` (one evidence JSON per verdict class)
- `work/`: `blob_tools_LF/` (LF materialization), `pinned/<rev>/`,
  `scratch_broken_repo/` (PRODUCER-ERROR harness), `pinned_pincheck/`

STOP — all six acceptance criteria verdicted.
