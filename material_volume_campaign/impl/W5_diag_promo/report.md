# W5 report — DIAGNOSTIC CLI promotion preparation: READY (pending non-author review)

Agent W5 · 2026-09-24 · worktree `E:/ChimeraWork/mvc-20260924`, branch
`material-volume-campaign-20260924`, **pin `feb01661bedb81063d88937d4c284ee9b4fa3ebd`**.
Brief verbatim: `brief.md`. Frozen checklist: `preregistration.md` (frozen
16:56:42, BEFORE any home/ artifact — earliest home file 16:58:19; brief itself
16:50:23, the first file written in this dir). All W5 writes stayed inside
`material_volume_campaign/impl/W5_diag_promo/` (one incident, honest, §Falsifiers).

**VERDICT: PROMOTION-READY.** Zero behavior edits; 17/17 at both locations;
byte-identical CLI behavior on a 22-case battery; dependencies pinned by blob
OID at the recorded revision (which already contains W3's landed reader
repair); the three Astra decisions documented verbatim-anchored. This agent
does NOT integrate — the coordinator publishes via the existing publisher path
after the review hook (§4).

The Astra decision executed, verbatim: "Authorize isolated promotion
preparation for the diagnostic and validator into their permanent tool home,
including exact dependency pinning, current-contract reconciliation and review.
Integration follows the existing publisher path after tests; no runtime wiring
or wholesale campaign-tree copy." (The validator half is W6's task.)

## 0. Results at a glance

| measurement | value |
|---|---|
| original suite baseline (pre-freeze, committed location) | 17/17 OK (5.664 s) — `receipts/original_baseline_tests.log` |
| home suite (run_suite.py, adapted paths only) | PASS — 17 run, 0 failures, 0 errors — `receipts/run_suite_home.log` |
| read-only proof (home run) | before_after_identical=True, 415 files, added=0 removed=0 changed=0 |
| git integrity inside home run (tools + Chimera/docs/matter) | (empty) |
| per-test equivalence vs baseline | identical ID sets (17), all ok — `receipts/home_test_ids.txt` vs `receipts/original_baseline_test_ids.txt`, sorted diff EMPTY |
| CLI battery (original vs home; 10 fixtures × human/json + 2 usage probes) | 22 cases, 0 mismatches; exit histogram {0: 16, 2: 4, 64: 2} — `receipts/cli_battery_equivalence.json` |
| default dependency resolution from both CLI locations | SAME dir `E:\ChimeraWork\mvc-20260924\tools` |
| home-copy diff vs pinned source blob `f9763b43…` | prepended comment header ONLY: 0 non-comment lines added, 0 lines removed — `receipts/home_header_diff.txt` |
| run_suite adaptation vs pinned blob `848b4ee1…` | exactly 2 path-constant lines — `receipts/home_run_suite_path_adaptations.diff` |
| tests copy vs committed original | VERBATIM-IDENTICAL (diff empty) |
| docs drift check | 12/12 source needles OK; all 8 dependency OIDs match `git ls-tree` ground truth; 0 failures |
| environment | CPython 3.14.3, numpy 2.2.6, Windows, CPU-only |

## 1. FROZEN CHECKLIST — verdicts (criteria never reworded; see `preregistration.md`)

- **CHECK-1 frozen prereg: GREEN.** `preregistration.md` frozen before edits
  (mtime order above; brief.md first). Theory/P1–P3/F-W5.1–6 named before the
  build, exactly as executed.
- **CHECK-2 home copy + header: GREEN.** `home/material_volume_diagnostic.py`
  = pinned blob `f9763b4318e6954b9141b8bc954c10a856c39cf2` + prepended comment
  header carrying all six required fields: tool identity; version (1.0.0,
  promotion candidate, blob-pinned); receipt trail M09 `7701d8db` → B2a
  ACCEPT-WITH-NOTES (D1/D2/D3) → B8 `8c4f8ba2` → W5; frozen exit contract
  0/2/4/64 with the explicit note that M06-H04's 0/2/1 is the VALIDATION CLI's
  mapping, not this tool's; static/read-only claims (writes nothing incl. no
  `__pycache__` in tools/, validates nothing, promotes nothing, no runtime
  wiring); dependency statement with roles, OIDs, and the re-pin rule.
  F-W5.1 proof: `receipts/home_header_diff.txt`.
- **CHECK-3 dependency manifest: GREEN.** `docs/dependency_manifest.md` +
  `receipts/dependency_oids.json`: 4 local modules with verified import roles
  (reader DIRECT; body_export DIRECT+transitive; admission, material_volume
  transitive — graph `reader -> body_export -> admission -> material_volume`
  grep-verified), 2 external (numpy 2.2.6, CPython 3.14.3), 4 example-JSON test
  fixtures. Every OID verified with `git cat-file -e` at the pin; working-tree
  bytes matched the pin at freeze (`git diff feb01661 -- tools/` EMPTY).
  **W3 note:** the repair was in flight at dispatch (uncommitted, HEAD
  `df5ac8c6`) and LANDED (`af735b7f`) before this pin — the pinned reader blob
  `1ee791e0580ca0e30bf0b73321cfd981cd79b486` already contains it, and both
  suite runs measured against it. The manifest's RE-PIN RULE binds the
  publisher: re-pin OIDs against the then-current landed revision and re-run
  the home suite before publishing if HEAD moved.
- **CHECK-4 docs: GREEN.** `docs/material_volume_diagnostic.md`: §2 usage,
  §3 frozen exit codes (0/2/4/64, scope note separating the validation CLI's
  0/2/1), §4 **MV-O2/O3** (decision verbatim; four separated claims — input
  permutation PROMISED (body_export doc L46 quote), physical-value equality
  PROVED-EXACT 5/5 `float.hex`-identical but NOT yet prose-promised (MV-O2
  open), output-array order ID-sorted by code but UNPROMISED (MV-O3 open),
  byte equality promised for same-input determinism only — each with its M05
  receipt numbers; proved domain stated; vertex-renumber marked untested; "no
  sorting was changed"), §5 **MV-B4-1** (decision verbatim; three identity
  layers — git blob identity, LF-only text identity, raw disk equality — as
  distinct claims, with B4's portability contract quoted). Verbatim +
  drift evidence: `receipts/docs_verbatim_check.txt` (ALL VERBATIM,
  whitespace/blockquote-normalized) and the 12-needle drift scan (0 failures).
  The third decision ("Promotions") is anchored verbatim in §4 below.
- **CHECK-5 suite green on the home copy: GREEN.** `receipts/run_suite_home.log`
  (verdict PASS; read-only proof 415 files identical; git integrity empty) +
  `receipts/home_tests_verbose.log` (17 ok) + equivalence receipts + battery.
- **CHECK-6 publication note + integrity: GREEN.** §4 and §5 of this report.

## 2. Predictions (Rule 0) — all CONFIRMED

- P1 confirmed: same tests, same results (17/17) at both locations against the
  post-W3 reader — the repair is invisible to the diagnostic, exactly as W3's
  "valid output + existing refusals byte-identical" receipt predicted.
- P2 confirmed: comment-only header change → 22/22 identical
  (stdout sha256, stderr sha256, exit code) triples.
- P3 confirmed: both locations resolve the same `tools/` by ancestor walk.

## 3. Falsifier ledger (from the frozen prereg)

- **F-W5.1 behavior edit — NOT HIT.** 0 non-comment diff lines; battery 0
  mismatches.
- **F-W5.2 home suite not green — NOT HIT.** 17/17 OK.
- **F-W5.3 equivalence break — NOT HIT.** Same ID sets, same count, all ok.
- **F-W5.4 write outside the product home — HIT ONCE, REPAIRED, honestly
  recorded.** The first home `run_suite.py` run wrote its canonical receipts
  (`read_only_proof.json`, `output_samples.txt`, `u7_reader_probe.txt`,
  `git_integrity.txt`) to `material_volume_campaign/impl/receipts/` — an
  off-by-one in MY adapted path constant (`MY_DIR.parents[1]` from `home/`
  resolves to `impl/`, not `W5_diag_promo/`); the frozen prereg's own M2
  arithmetic ("../../receipts") was the error's source — its stated intent
  ("the W5 receipts dir") was unambiguous. Caught by the final-porcelain
  review, NOT by luck of the gate. Repair: corrected the constant to
  `MY_DIR.parent / "receipts"` (still a pure path adaptation — diff receipt
  regenerated), deleted the stray `impl/receipts/` (my artifact, created
  16:59), re-ran: PASS again, receipts landed correctly. The preregistration
  file is left untouched (frozen); this report is the erratum. The tests copy
  needed NO edit (all its paths resolve from `__file__`; verbatim-identical).
- **F-W5.5 manifest defect — NOT HIT.** All OIDs resolve at the pin; roles
  grep-verified.
- **F-W5.6 docs drift — NOT HIT.** 0 drift failures; both documentation
  decisions verbatim; no invariance promised beyond M05's proved domain
  (§4 of the doc marks the domain and the untested vertex-renumber half).

## 4. Publication readiness (for the coordinator/publisher)

Astra "Promotions", verbatim: "Authorize isolated promotion preparation for
the diagnostic and validator into their permanent tool home, including exact
dependency pinning, current-contract reconciliation and review. Integration
follows the existing publisher path after tests; no runtime wiring or
wholesale campaign-tree copy."

**Exact files for the publisher (all inside this dir):**

| source here | proposed target in the game lineage |
|---|---|
| `home/material_volume_diagnostic.py` | `tools/material_volume_diagnostic.py` |
| `docs/material_volume_diagnostic.md` | `tools/docs/material_volume_diagnostic.md` (or the lineage's doc convention — publisher's call) |
| `docs/dependency_manifest.md` | review artifact; publish at the publisher's discretion — its RE-PIN RULE must be executed at integration time either way |

- **Target home proposal:** `tools/` of the game lineage (the publisher path
  lands things in `E:/ChimeraWork/monkey-play-20260924`). Placing the CLI
  INSIDE `tools/`, co-located with the reader and its transitive modules,
  satisfies the ancestor-walk discovery with no flags; `--tools-dir`/`M09_TOOLS_DIR`
  remain for non-standard layouts.
- **NOT published (deliberately — no wholesale campaign-tree copy):** `home/tests/`,
  `home/run_suite.py`, `receipts/`, `preregistration.md`, `brief.md` — these
  are the campaign's review trail and stay in the campaign tree (this dir).
- **Pre-publication gate:** execute the manifest's RE-PIN RULE (re-run
  `git ls-tree <landed-rev> -- tools/`; update OIDs if HEAD moved; re-run the
  home suite — acceptance 17/17 + battery 0 mismatches).
- **Review hook (binding):** a NON-AUTHOR must review before integration — the
  coordinator dispatches it (the board's R1–R3 row). Reviewer minimum: verify
  CHECK-1..6 evidence paths in §1 (each receipt named), re-run the two suite
  commands (`python home/run_suite.py`; unittest discover on `home/tests`),
  and spot-check `receipts/home_header_diff.txt` is comment-only. Integration
  follows the existing publisher path only after that review.

## 5. Integrity

Final porcelain (full worktree; `receipts/final_git_porcelain.txt`):

```
?? material_volume_campaign/impl/W5_diag_promo/
```

W5-caused changes are EXCLUSIVELY under `impl/W5_diag_promo/`. The original
M09 dir is porcelain-clean after the baseline run (before/after pastes:
`receipts/original_dir_porcelain_{before,after}.txt`, both empty — the suite
regenerated its `work/` fixtures byte-identically, git-invisible). tools/ and
`Chimera/docs/matter` untouched (home run's internal git gate: empty). W3/W1
integration commits and W6's parallel dir activity during this task are the
coordinator's/other agents' — recorded in the prereg context, not claimed by
W5. Nothing committed by W5 — integration/commit is the coordinator's call.

## 6. STOP statement

All six checklist checks GREEN with receipts; falsifier ledger closed (one
hit, repaired, recorded); predictions all confirmed. **W5 verdict:
PROMOTION-READY, pending the non-author review. W5 stops here.**
