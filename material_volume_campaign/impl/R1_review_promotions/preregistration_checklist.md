# R1 PREREGISTERED CHECKLIST — frozen 2026-09-24, BEFORE any check execution

Reviewer: R1 (non-author of W5 and W6). Everything under `impl/` is READ-ONLY to me;
all my writes go to `impl/R1_review_promotions/` only. All runs use `python -B`
(no bytecode writes) and copies extracted from committed git bytes wherever a run
would otherwise write into a reviewed/original location.

## Theory (Rule 0)

- **STATEMENT:** The claims in the W5 and W6 packages (pin purity, suite counts,
  battery equivalence, manifest completeness, docs verbatim-ness, publication file
  lists) are accurate and reproducible by a non-author from the committed bytes alone.
- **PREDICTION (unmeasured by me at freeze):** (a) W5 home copy = blob `f9763b43…`
  + comment-only header, 0 non-comment line changes; (b) M10 original suite = 71/71
  on original bytes; W6 suite = 101/101; W5 home suite 17/17; 22-case CLI battery
  0 mismatches — all reproduce on my machine today; (c) every recorded OID resolves
  at its recorded revision and both import closures are exactly as manifested.
- **FALSIFIERS (named before the run; any hit = finding):**
  - F-R1.1: any non-comment line differs between W5 `home/material_volume_diagnostic.py`
    and blob `f9763b4318e6954b9141b8bc954c10a856c39cf2` → pin claim false.
  - F-R1.2: original-bytes M10 suite ≠ 71 passes, or W6 suite ≠ 101 passes → count
    claims false.
  - F-R1.3: W5 home suite ≠ 17/17 or my independently-implemented battery finds
    ≥1 mismatch → claim false.
  - F-R1.4: any recorded OID fails `git cat-file -e`, mismatches `git ls-tree` at the
    recorded revision, or a real import of either shipped tool is missing from its
    manifest → manifest defect.
  - F-R1.5: any spot-checked quote absent from its cited source (modulo
    whitespace/blockquote normalization), or the exit-contract note (diagnostic
    0/2/4/64 vs validation 0/2/1) inconsistent across the two packages → docs defect.
  - F-R1.6: my hostile input makes either tool traceback, hang, exit unexpectedly,
    or write outside its own run area → tool defect (graded against the named
    refusal contract: named refusal + clean exit is a pass).
  - F-R1.7: a publisher file list is wrong or incomplete (missing tests/runner,
    imports unresolved at the proposed landing, files the publisher must invent)
    → publication-readiness finding.

## Checks

1. **PIN VERIFICATION**
   - 1a. `git cat-file blob f9763b43…` → `work/pin_blob.py`; diff vs
     `impl/W5_diag_promo/home/material_volume_diagnostic.py`; classify every
     differing line. Only full-line `#` comments / blank lines prepended allowed.
     Record exact non-comment change count.
   - 1b. Extract M10 (validator + tests + fixtures) from committed bytes to
     `work/m10_original_bytes/`; verify `impl/W6_validator/receipts/baseline_reproduction/`
     copy is faithful to the same bytes; run the ORIGINAL tests on ORIGINAL bytes →
     expect 71 pass. Run W6's full `tests/` from a scratch copy → expect 101 pass.
     Before/after: hash + porcelain of `agents/M10_validator` to prove untouched.
2. **CLAIM RE-RUNS**
   - 2a. Extract W5 `home/` from committed bytes to `work/w5_home/`; run
     `run_suite.py` → expect PASS/17; `unittest discover` → expect 17 ok.
   - 2b. My OWN battery script (not theirs): run original M09 tool and W5 home tool
     over the 10 battery fixtures + 2 usage probes; compare (exit, stdout sha256,
     stderr sha256) → expect 22/22 identical.
   - 2c. W6 exit-class live behavior from a scratch copy: accept fixture → exit 0 +
     ACCEPT; genuine partial → exit 2 + REJECT; missing file → exit 2; argparse
     misuse → exit 2.
3. **DEPENDENCY MANIFESTS** — pull every OID from W5 `docs/dependency_manifest.md` +
   `receipts/dependency_oids.json` and W6 `docs/DEPENDENCY_MANIFEST.md`;
   `git cat-file -e` each; cross-check `git ls-tree` at the recorded revision(s) and
   current working tree. AST-walk the import closure of both shipped tools myself;
   compare to the manifests' module lists.
4. **DOCS TRUTH** — W5: 3 quotes (body_export permutation-promise line, M05 5/5
   float.hex receipt numbers, B4 portability contract) checked against cited sources.
   W6: 3 reconciliation quotes (D1/CON-14, D2/CON-3, D3/CON-16) checked against the
   main-checkout contract file; confirm it records v1.0 D1–D5 decided. Cross-package
   exit-contract note consistency (0/2/4/64 vs 0/2/1).
5. **ADVERSARIAL** — one hostile input per tool, of my own devising, distinct from
   all suite fixtures:
   - 5a diagnostic: JSON with `NaN` literal density + duplicate body id (Python json
     accepts NaN; both traps in one document). Expect: named refusal or clean
     diagnostic exit (0/2/4/64), never a traceback, no writes.
   - 5b validator: report with a cell owned twice by the SAME body (self-overlap) and
     an admission hash in uppercase with surrounding whitespace. Expect: named REJECT,
     exit 2, no crash.
6. **PUBLICATION READINESS** — check each named publisher file exists; simulate the
   proposed `tools/` landing in `work/` (tool + 4 dep modules) and run the real CLI
   there to prove imports resolve; check W6 USAGE.md flags against real `--help`;
   name anything the publisher must invent.

## Exit condition

Verdict per package (APPROVE / APPROVE-WITH-NOTES / REJECT with blocking defects)
+ publication order recommendation, written to `report.md` with receipts under
`receipts/`.
