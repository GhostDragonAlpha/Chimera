# R1 REPORT — INDEPENDENT NON-AUTHOR REVIEW of the W5 + W6 promotion packages

Reviewer: R1 · 2026-09-24 · worktree `E:/ChimeraWork/mvc-20260924` (branch
`material-volume-campaign-20260924`, HEAD `a00146f3`). I authored neither
package. Brief verbatim: `brief.md`; checklist frozen BEFORE execution:
`preregistration_checklist.md`. All runs CPU-only, `python -B` /
`PYTHONDONTWRITEBYTECODE=1`; every re-run executed from git-extracted scratch
copies in `work/` or in place with before/after integrity proofs. Receipts:
`receipts/check1a_pin_diff.txt`, `check1b_baseline_and_w6_suite.txt`,
`check3_manifests.txt`, `check4_docs_truth.txt`, `check5_adversarial.txt`,
`check6_publication_readiness.txt`, `m10_before_hashes.txt`.

## VERDICTS

| package | verdict |
|---|---|
| **W5_diag_promo** (diagnostic CLI promotion) | **APPROVE** |
| **W6_validator** (validator promotion) | **APPROVE-WITH-NOTES** (2 notes, named below; both are docs/readiness defects in `TOOL_HOME_PROPOSAL.md`, not behavior defects) |

**Publication order recommendation: W5 first, W6 second.** W5 is fully
publisher-ready as it stands. W6 should go only after the coordinator appends
an erratum to `impl/W6_validator/docs/TOOL_HOME_PROPOSAL.md` correcting N1/N2
(append-only; the promoted code and tests need NO change), so the publisher
never executes the two wrong instructions.

## 1. PIN VERIFICATION (brief item 1)

- **W5 comment-only header: CONFIRMED.** I extracted blob
  `f9763b4318e6954b9141b8bc954c10a856c39cf2` myself (`git cat-file`) and diffed:
  `home/material_volume_diagnostic.py` ends with the blob's exact bytes; the
  only diff opcode is one prepended block of 73 lines (4717 bytes), every line
  a `#` comment or blank. **Non-comment line changes: 0.** The header carries
  all six claimed fields, including the exit-contract scope note (0/2/4/64 vs
  the validation CLI's 0/2/1) and the RE-PIN RULE.
- **W6 baseline-71: REPRODUCED.** I ran the ORIGINAL M10 tests on the ORIGINAL
  bytes, in place: **71 passed in 0.67 s**, pre/post file-hash comparison: 0
  files changed; git porcelain (M10 dir + tools/) empty after. My first
  attempt from a deeper scratch copy produced 1 failed / 70 passed — diagnosed
  as MY harness artifact: M10's `_tools_dir()` is a fixed `parents[3]/"tools"`
  index, and the copy degraded gracefully to
  `reader_cross_check {ran: False, note: ModuleNotFoundError}` (correct
  named-degradation behavior, no crash). W6's own `receipts/baseline_71.txt`
  documents this exact trap and the designed `CHIMERA_TOOLS_DIR` override; I
  reproduced their route too (their `baseline_reproduction` copy is
  byte-identical to the M10 original over 56 files): **71 passed in 0.71 s.**

## 2. CLAIM RE-RUNS (brief item 2) — all reproduced from scratch

- **W5 home suite: 17/17.** From a depth-faithful replica
  (`work/w5rep/.../home/`, because `run_suite.py` computes `WORKTREE =
  MY_DIR.parents[3]`): `Ran 17 tests ... OK`, read-only proof
  `before_after_identical=True (files_snapshotted=415, added=0, removed=0,
  changed=0)` — same 415-file count as W5's receipt. (My first flat-layout
  attempt: 17/17 OK but the post-flight proof crashed on the wrong worktree —
  again the fixed-index artifact, mine, not the tool's.) Real-worktree
  porcelain after all runs: clean.
- **W5 CLI battery: 22/22 identical — my OWN script, not theirs**
  (`work/r1_battery.py` logic): 10 fixtures x {plain, `--json`} + 2 usage
  probes, comparing (exit, stdout sha256, stderr sha256) of the ORIGINAL M09
  tool vs the W5 home copy: **0 mismatches**; my independently measured exit
  histogram **{0: 16, 2: 4, 64: 2}** matches W5's claim exactly.
- **W6 suite: 101/101 twice.** From my scratch extraction of committed HEAD
  bytes (override set): **101 passed in 2.16 s**; at the committed package
  location WITHOUT override: **101 passed in 2.13 s**, porcelain clean after.
- **W6 exit classes, live:** accept fixture → **0** (ACCEPT);
  `genuine_partial_report.json` → **2** (REJECT, `partial_rejected` named,
  `preserved_diagnostics` keys exactly
  `['all_supplied_cells_assigned','bodies','unassigned_cell_ids','unassigned_cells']`);
  `genuine_blocked_report.json` → **2** with body hash
  `298c544846f7f6e521db7205472ccf542501d95db7c1b4a11f6ad744cf8dd60f` — exactly
  the claimed value; missing file → **2** with
  `could_not_evaluate: input_read_error: ... FileNotFoundError` on stderr;
  argparse bad-flag and no-args → **2**. (`--version` string matches the
  report verbatim.) Exit 1 is the monkeypatched path, covered in-suite.

## 3. DEPENDENCY MANIFESTS (brief item 3) — complete and accurate

- **All 13 recorded OIDs resolve** (`git cat-file -e`): W5's 4 tools + 4
  fixture JSONs + 3 source blobs; W6's `@d1c99335` reader provenance OID and
  the worktree v0.9 contract blob `376adfa5`.
- **`git ls-tree` cross-check:** the four tool OIDs match at BOTH `feb01661`
  (the recorded authoritative pin) and current HEAD `a00146f3` — the RE-PIN
  RULE is already satisfied; all 8 `working_tree_sha256` values in
  `dependency_oids.json` still match the live files. Main checkout
  `E:/PythonChimera`: contract blob `ee254224` present at current main HEAD
  `768f3de0`; raw sha256 `c6977868` and canonical sha256 `fa845491` match W6's
  record exactly.
- **Import closures (my own AST walk + live observation):**
  - W6 validator → `material_volume_body_export_reader` → {`body_export` →
    `admission` → `material_volume`} + numpy + stdlib — **exactly** the
    manifested 4-module closure; nothing missed.
  - W5 diagnostic loads the reader/exporter via `importlib` at runtime
    (static AST sees no local imports by design); code inspection + live runs
    confirm consumption of `summarize_export_report`, `canonical_json`,
    `read_json_file`, `ExportInputError`; runtime closure is the same four
    modules + numpy. Manifest complete; nothing missed.

## 4. DOCS TRUTH (brief item 4)

- **W5 spot-checks (3):** body_export doc "identifies the exact serialized
  inputs, including row ordering" and "key-sorted canonical JSON with no
  timestamps..." — VERIFIED verbatim (`Chimera/docs/matter/material_volume_body_export.md`);
  "emits deterministic ... JSON to stdout" — VERIFIED (L14 paragraph); M05
  numbers (P0a==P0b sha `8a69419e`, 8927 B, PASS-EXACT `float.hex` equality,
  7 runs) — VERIFIED in `agents/M05_order/receipts/`; B4 portability contract
  quote and "0/37" — VERIFIED verbatim (`agents/B4_crosscheckout/report.md`
  L94–L100). The four-claims separation (PROMISED / PROVED-EXACT-but-NOT-
  PROMISED / UNPROMISED / byte-equality scoped) is faithfully documented with
  the proved domain and the untested vertex-renumber half stated.
- **W6 spot-checks (3):** D1, D2, D3 rows in the reconciliation table are
  VERBATIM in the main checkout's decided contract (§5 table, "v1.0 (D1–D5
  decided)", recorded 2026-09-24). M07 receipt reproduction claim VERIFIED
  (`298c5448…` reduced and `4d4c43e1e0d1…` root present in
  `agents/M07_ownership/report.md` + `receipts/case-c4-export.json`).
  MV-O1 behavior live-verified: blocked bodies labeled `reduced_block_record`,
  `full_report_identity.raw_file_sha256`/`canonical_content_sha256` match the
  delivered bytes I hashed myself; claim kinds named, never conflated.
- **Exit-contract note consistency:** W5 (doc §3 + home header) states
  diagnostic 0/2/4/64 with an explicit scope note that M06-H04's 0/2/1 is the
  validation CLI's mapping; W6 (module docstring, `--help` epilog, `--version`,
  USAGE.md exit table) states 0=accepted / 2=named refusal / 1=unexpected
  internal failure per M06-H04, with the compatibility note that original M10
  keeps 0/1/2. **Consistent and mutually distinguishing.** M06-H04's source
  verified (`agents/M06_malformed/report.md` L153/L212).

## 5. ADVERSARIAL (brief item 5) — both tools held

- **Diagnostic** (input of my own devising, not in any suite): shipped example
  report mutated three ways at once — `"value":NaN` literal mass (Python-json
  nonstandard constant), first `body_groups` record duplicated verbatim (same
  body_id twice), duplicate top-level `export_status` key appended. Result:
  exit **2**, named `input_read_error ... ValueError` from the strict loader,
  final `readiness: false` sentinel intact, no traceback, input bytes
  untouched, in both human and `--json` modes. Contract held.
- **Validator**: accept fixture with body-A `owned_cell_ids =
  ["cell-A","cell-A"]` (SELF-overlap — the suite only covers cross-body
  overlap) plus `admission_report_sha256` uppercased AND whitespace-padded
  (suite has uppercase only). Result: exit **2**, REJECT, both hostilities
  named — `R11 owned_cell_ids_duplicated` + `R4 hash_binding_malformed` — no
  traceback. Contract held.

## 6. PUBLICATION READINESS (brief item 6)

- **W5:** the §4 publisher table is exactly right against the package: tool
  file, doc, manifest all present; `home/run_suite.py` + `home/tests/` +
  fixtures present for the reviewer re-run; every receipt file named in the
  report exists (no dangling references). **Landing simulation**
  (`work/landing_sim/repo_root/tools/`): diagnostic co-located with its four
  dependencies runs with no flags and emits correct output. Nothing missing.
  Publisher decisions explicitly left open (and legitimately so): doc target
  (`tools/docs/` vs lineage convention), RE-PIN RULE execution at integration
  (already verified satisfied at current HEAD), the commit itself.
- **W6:** `tests/` included (adapted suite + 5 delta files + 56 fixtures);
  USAGE.md matches the live CLI flag-for-flag (`--verify-aggregate` exercised:
  emits the `con16_verification_aggregate` artifact with
  `not_a_v1_body_record` / `joints_inferred:false` /
  `runtime_grouping_changed:false`, refuses on non-ACCEPT reports, and the
  verdict itself carries no aggregate keys). **Landing simulation: the
  installed CLI works** (ACCEPT + `reader_cross_check ran=True`) — but see N1:
  for a different reason than the proposal states.
- **Findings the publisher would otherwise trip on:**
  - **W6-N1 (must fix by erratum before publication):**
    `docs/TOOL_HOME_PROPOSAL.md` claims the tool's `_tools_dir()` is
    `Path(__file__).resolve().parents[1] / "tools"` once installed. The code
    (validator line 114) is unchanged from M10: `parents[3] / "tools"`. At a
    repo-root `tools/` landing that index resolves OUTSIDE the repo. The landed
    CLI still works because the reader import succeeds via the script-dir
    `sys.path` entry (dependencies sit beside the tool) — empirically
    verified — but installation **step 4 as written** ("run the frozen suite
    against the installed location", AGENT_DIR repointed) will FAIL
    `test_reader_cross_check_passes_on_accept` (and the pycache guard's
    `HERE.parents[3]` path) unless the `CHIMERA_TOOLS_DIR` override is set —
    the override exists in the code and in DEPENDENCY_MANIFEST's
    re-verification steps, but step 4 never mentions it. The publisher would
    have to invent this. Code change NOT required; a one-paragraph erratum is.
  - **W6-N2 (fix in the same erratum):** the proposal cites
    `receipts/final_hashes.txt`, which does not exist. The sha256 actually
    lives in `receipts/integrity_and_hashes.txt` and is CORRECT (I recomputed
    `5ecce0b5…` from the live file).
  - No corresponding defects found in W5's docs.

## 7. Falsifier ledger (my prereg)

| falsifier | outcome |
|---|---|
| F-R1.1 non-comment pin drift | NOT HIT (0 lines) |
| F-R1.2 suite counts | NOT HIT (71/71, 101/101, 17/17 all reproduced) |
| F-R1.3 battery mismatch | NOT HIT (22/22 identical, independent script) |
| F-R1.4 OID / import-closure defect | NOT HIT (13/13 resolve; closures exact) |
| F-R1.5 quote / exit-note inconsistency | NOT HIT for the tool docs; hit in ONE place outside them — W6's TOOL_HOME_PROPOSAL (N1 misstates code, N2 names a nonexistent receipt) |
| F-R1.6 hostile-input break | NOT HIT (both tools: named refusals, clean exits) |
| F-R1.7 publisher file-list defect | PARTIALLY HIT — W6's proposal (N1/N2 above); W5's is exactly right |

Two harness lessons recorded for future reviewers (both caused by MY copy
depth, both already documented by the packages themselves): fixed
`parents[3]` indices make arbitrary-depth scratch reproductions invalid; use
`CHIMERA_TOOLS_DIR` / depth-faithful replicas or run in place with `-B` +
`-p no:cacheprovider` and hash-based before/after proofs.

## 8. STOP

All six preregistered checks executed; falsifiers graded; verdicts issued.
**W5: APPROVE. W6: APPROVE-WITH-NOTES (N1, N2 — erratum before publication).
Order: W5, then W6.** R1 stops here.
