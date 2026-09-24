# W5 preregistration — DIAGNOSTIC CLI promotion preparation (frozen before any home/ edit)

Frozen: 2026-09-24, worktree `E:/ChimeraWork/mvc-20260924`, branch
`material-volume-campaign-20260924`, **pinned revision
`feb01661bedb81063d88937d4c284ee9b4fa3ebd`** (verified present via
`git cat-file -e` before freeze; `git diff feb01661 -- tools/` EMPTY at freeze,
so the working tree's tools/ IS the pinned revision's tools/).
Brief: `brief.md` (verbatim copy, written first). Product home: THIS directory
only (`impl/W5_diag_promo/`). Nothing outside it may be created or modified.

## Context recorded at freeze (the W3 situation)

The brief said W3's reader repair (M13) was in flight and W5 must pin the
reader at a revision W5 records, then note the final re-pin. **Measured
timeline:** at W5 session start, HEAD was `df5ac8c6` and
`git status` showed ` M tools/material_volume_body_export_reader.py` (W3's
uncommitted repair). While W5 was reading sources, the coordinator integrated
W3 (`af735b7f`) and W1 (`fe031402`); at freeze HEAD is `feb01661` and tools/ is
clean. **Therefore the revision pinned here (feb01661) already CONTAINS W3's
landed reader repair** (blob `1ee791e0580ca0e30bf0b73321cfd981cd79b486`), and
the "final re-pin" obligation reduces to: re-pin at integration time if HEAD
has moved again (the manifest keeps the rule). W5 did NOT block on W3 and did
NOT touch the reader — both satisfied trivially at freeze; verified again at
verdict time.

## THEORY (Rule 0)

- **STATEMENT**: Promotion preparation is a byte-faithful relocation. The
  diagnostic CLI's behavior is a function of (a) its own bytes and (b) the
  public interface of its pinned dependencies (reader
  `summarize_export_report`/`canonical_json`, exporter
  `read_json_file`/`ExportInputError`). A copy that differs from the pinned
  source ONLY by prepended comment lines, executed in the same dependency
  scope, is behaviorally identical and suite-equivalent; dependency pinning +
  docs + a clean home copy need no behavior change at all.
- **PREDICTION** (untested until the runs below):
  - P1: the full 17-test M09+B8 suite passes UNCHANGED (same test IDs, same
    results) at BOTH the original location (pre-freeze baseline, already
    measured: 17/17 OK in `receipts/original_baseline_tests.log`) and the home
    copy, against the post-W3 reader — W3's integration receipt claims valid
    output and existing refusals byte-identical, and the diagnostic consumes
    only the reader's public API, so no test can tell the repair happened.
  - P2: on a shared fixture battery (5 genuine statuses + 3 hostile + 2
    malformed + usage errors), original CLI and home CLI produce byte-identical
    stdout/stderr and identical exit codes, because comment-only diffs cannot
    reach the bytecode's behavior.
  - P3: the home copy's default dependency discovery
    (`find_tools_dir(None)`, nearest-ancestor walk) resolves to the SAME
    `E:/ChimeraWork/mvc-20260924/tools` directory the original resolves to,
    because both live under the same worktree root.
- **FALSIFIERS** (named before the build; any hit = W5 defect, fixed HERE or
  the promotion is declared NOT READY — never tuned away):
  - F-W5.1 **behavior edit**: the home copy's diff vs the pinned source blob
    (`f9763b4318e6954b9141b8bc954c10a856c39cf2`) contains ANY line that is not
    a prepended full-line comment; OR any (stdout, stderr, exit-code) triple
    differs between original and home CLI on the shared battery.
  - F-W5.2 **home suite not green**: any of the 17 tests fails or errors when
    run from `home/tests/`.
  - F-W5.3 **equivalence break**: the home run's per-test verdict set differs
    from the frozen baseline (`receipts/original_baseline_test_ids.txt`, all
    ok) in test IDs or outcomes, or the test COUNT is not 17.
  - F-W5.4 **write outside the product home**: after all runs, `git status
    --porcelain` shows any change outside `material_volume_campaign/impl/
    W5_diag_promo/` that W5 caused. (Other agents' pre-existing dirs — e.g.
    W6's untracked dir — and coordinator commits during the task are recorded,
    not claimed. The ORIGINAL M09 dir must be porcelain-clean after the
    baseline run — measured: it is.)
  - F-W5.5 **manifest defect**: any OID in the manifest does not resolve at the
    pinned revision (`git cat-file -e <rev>:<path>`), or a role statement
    ("direct import" / "transitive import" / "test fixture") contradicts the
    actual import graph (`grep '^import material_volume'` over the four
    modules).
  - F-W5.6 **docs drift**: any quote or number in `docs/` or `report.md` that
    does not match its cited source file verbatim (checked by scripted grep at
    verdict time), or a promise of invariance beyond M05's proved domain.

## FROZEN PROMOTION CHECKLIST (acceptance = all six verdict GREEN)

1. [ ] **CHECK-1 frozen prereg** — this file exists before any home/ edit
      (file mtime order provable; brief.md is the first file written).
2. [ ] **CHECK-2 home copy + header** — `home/material_volume_diagnostic.py`
      exists; diff vs pinned source blob is comment-only (F-W5.1); header
      carries ALL SIX required fields: tool identity, version, source receipt
      trail (M09 `7701d8db` -> B2a review -> B8 `8c4f8ba2`), frozen exit
      contract (0/2/4/64 — its OWN contract; M06-H04's 0/2/1 mapping is the
      VALIDATION CLI's, NOT this tool's), static/read-only claims, dependency
      statement (reader by role + blob OID, re-pin rule).
3. [ ] **CHECK-3 dependency manifest** — `docs/dependency_manifest.md` (+
      machine-readable `receipts/dependency_oids.json`) lists every dependency
      (4 local modules: reader, body_export, admission, material_volume;
      numpy; 4 example-JSON fixtures) with role, blob OID at feb01661, and the
      W3 re-pin note. Every OID resolvable (F-W5.5).
4. [ ] **CHECK-4 docs** — `docs/material_volume_diagnostic.md`: usage +
      frozen exit codes; MV-O2/O3 section separating input permutation /
      physical-value equality / output-array order / byte equality, each
      labeled PROVED (M05 receipt numbers) / PROMISED (doc quote) / NOT
      promised, with the Astra decision quoted verbatim; MV-B4-1 section with
      the three identity layers (git blob identity / LF-only contract text
      identity / raw disk equality) as DISTINCT claims, decision quoted
      verbatim. No invariance claimed outside M05's proved domain (F-W5.6).
5. [ ] **CHECK-5 suite green on the home copy** — 17/17 from `home/tests/`
      (F-W5.2), per-test equivalence vs baseline (F-W5.3), receipts:
      home tests log, CLI battery equivalence receipt, home run_suite receipt.
6. [ ] **CHECK-6 publication note + integrity** — `report.md` contains the
      exact publisher file list, target-home path proposal, and the non-author
      review hook; final `git status --porcelain` paste showing W5-caused
      changes ONLY under `impl/W5_diag_promo/` (F-W5.4).

## FROZEN METHOD (executed in this order)

M1. Baseline (BEFORE freeze, no W5 writes outside receipts/): run the original
    suite via `python -m unittest discover` (NOT `run_suite.py`, which writes
    receipts into the original dir — W5 must not touch it). Paste original-dir
    porcelain before/after; fixtures regenerate byte-identically (mtime-only
    churn, git-invisible). DONE: 17/17 OK, 5.664 s, porcelain clean.
M2. Freeze this file. THEN build: `home/material_volume_diagnostic.py`
    (pinned source + prepended comment header, `cat`-composed, no in-file
    edits), `home/tests/` (verbatim copies of the two test files — the test
    module resolves ALL its paths from `__file__`, so no path edit exists to
    make), `home/run_suite.py` (ONLY the path constants adapted:
    `WORKTREE = MY_DIR.parents[3]`, `RECEIPTS -> ../../receipts` i.e. the W5
    receipts dir; adaptations published as a diff receipt).
M3. Dependency manifest from `git ls-tree feb01661` + import-graph grep.
M4. Docs from M05 report/receipts + B4 report + the three verbatim decisions.
M5. Home suite run + CLI battery equivalence script (both CLIs, 10 fixtures +
    2 usage probes, byte-compare triplets).
M6. Publication note + verdict tally + integrity paste in `report.md`.

Verdicts are filled into CHECKLIST section ABOVE only as "GREEN (evidence
path)" / "RED (evidence path)" — no rewording of criteria after runs.

## STOP condition

All six checks GREEN with receipts = promotion-ready (NOT promoted — the
coordinator publishes through the existing publisher path after the non-author
review). Any RED = promotion NOT READY, defect named with evidence. W5 stops
at the verdict.
