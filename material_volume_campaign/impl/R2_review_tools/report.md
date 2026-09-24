# R2 REPORT — INDEPENDENT NON-AUTHOR REVIEW of W1 (verifier + battery append) and W3 (reader repair)

Reviewer: R2 (non-author). Date: 2026-09-24. Worktree `E:/ChimeraWork/mvc-20260924`,
HEAD `a00146f3`. Reviewed commits: `af735b7f` (W3), `fe031402` (W1), `feb01661` (fixture
unstage). `git log --follow` confirms neither tools/ file was touched by any commit
after the reviewed ones (battery: 1af0bbde→fe031402 only; reader: d2c23741→af735b7f
only), so this review at HEAD measures exactly the reviewed deltas.
Prereg frozen before any check: `work/prereg_R2.md`, sha256
`1199d8875236842198b03483fe15e010708864c8a06d0e2eacefb2046c02049e`
(`receipts/00_prereg_hash.txt`). Python 3.14.3, numpy 2.2.6, CPU-only.
All R2 writes confined to `impl/R2_review_tools/` (verified by `git status` at the end).

## VERDICTS

| Change | Verdict |
|---|---|
| W1 source-bound regeneration verifier + battery append (`fe031402`) | **APPROVE-WITH-NOTES** |
| W3 reader M13 repair (`af735b7f`) | **APPROVE-WITH-NOTES** |

No blocking defects found. Notes are residual-scope observations, all measured, none a
regression introduced by the reviewed changes; each is a candidate decision request,
not a defect in the claimed scope.

## Check 1 — W1 adversarial re-run (P1–P4): ALL HOLD

Corpus built by `work/build_r2_corpus.py` from the shipped example — mutations authored
independently of W1's B7 corpus (receipts `w1_*.json`):

| Case | Exit | Verdict | Itemization |
|---|---|---|---|
| genuine example report | 0 | VERIFIED | — (caveat + note present) |
| R2-M1: 1-ULP inertia edit (`0.07500000000000001 → 0.07500000000000002`) | 1 | MISMATCH | `$body_groups[1]...inertia_tensor_about_com.value[0][0]` |
| R2-M2: swapped provenance (`input_hashes.manifest_sha256 ↔ partition_sha256`) | 1 | MISMATCH | `input_hashes.manifest_sha256`, `input_hashes.partition_sha256`, `$report` |
| R2-M3: subtle mass change (1 ULP, `1.0 → 1.0000000000000002`) | 1 | MISMATCH | `$body_groups[1]...mass.value` |
| missing groups file | 2 | UNAVAILABLE-SOURCE | detail names the missing material |
| tampered pair (1-ULP density in partition + report REGENERATED from it by W1's own pinned_runner) | 0 | VERIFIED | — but caveat + independent_checks_note present, delivered/regenerated statuses surfaced |
| tampered partition + GENUINE report (negative control) | 1 | MISMATCH | `input_hashes.partition_sha256`, `admission_report_sha256`, `$admission_report_sha256` |

**Attempt to make it lie (tampered pair):** the verifier DOES verify colluding
report+source — and that is exactly the documented producer-agreement caveat, not a
hidden failure: every VERIFIED output carries the frozen caveat sentence, the
independent-checks note, and both export/admission statuses. Honest.

**Note N-W1-1 (pin choice is the caller's, not authenticated):** running the verifier
with `--revision HEAD` (a00146f3, exporter blob identical to the pin) also returns
VERIFIED (`receipts/w1_headpin.json`). The tool byte-verifies the materialization
against the GIVEN pin but has no notion of "the" frozen revision. Consistent with the
caveat wording ("not correctness of ... producer"); pin governance lives outside the
tool. Non-blocking.

## Check 2 — Pin integrity (P5): HOLD

- `git ls-tree -r 1af0bbdee68d…` OIDs: material_volume.py `3d46b030…`,
  material_volume_admission.py `41615ec7…`, material_volume_body_export.py
  `f6fd2af1…`. `git hash-object` of BOTH my re-materialization
  (`work/w1_mat/tools/`) AND W1's committed materialization
  (`impl/W1_source_verify/work/pinned/1af0bbdee68d/tools/`) reproduce all three OIDs
  exactly. Worktree `tools/material_volume_body_export.py` is the same blob
  `f6fd2af1…` (pinned == HEAD exporter).
- Negative: pin `c25ba960` (predates the modules) → UNAVAILABLE-SOURCE, exit 2, detail
  names all three missing modules (`receipts/w1_badpin.json`).
- W1 suite PIN constant `1af0bbdee68d6ddfdd02bf9bd948f7b22f914d56` resolves
  (`git cat-file -t` → commit; message = the exporter-proof commit). The battery file
  itself contains no revision reference (nothing to drift); the append's 61+/0− shape
  already proves the frozen rev untouched by W1.

## Check 3 — Battery append audit (P6): HOLD

- `git diff af735b7f fe031402` on the battery: **61 insertions, 0 deletions**
  (`receipts/30_battery_diffstat.txt`); 0 deleted content lines.
- All 28 executable/statement lines of the original
  `test_cli_determinism_and_saved_example_bytes` survive unchanged (script-checked
  subset test; the insertions inside it are comments only) → the original
  checkout-dependent failure behavior is preserved with its explanation.
- Both identities labeled: "MATERIALIZED-FILE IDENTITY (checkout-dependent)" and
  "BLOB-FORM IDENTITY (portable)" present in the current file.
- New `test_blob_form_reproduction_of_saved_example_report` RAN and passed at HEAD
  (`-v` receipt; the `skipTest` path is a labeled unittest skip — never silently a
  pass — and was not taken here).

## Check 4 — W3 re-run (P7–P10): ALL HOLD, one measured residual

- **14/14 crash shapes** (W3 T01–T13 + B7 `corrupt_M13.json` verbatim) on a scratch
  copy of the CURRENT reader: every one exits 2, zero tracebacks, refusal lines match
  W3's frozen table exactly (inertia → "not a rectangular numeric array"; center →
  "not a numeric array of length 3"; mass → "not a finite JSON number"; all located at
  `body_groups[1] …`) — `receipts/42_crash_shapes_14.txt`. The PRE-W3 reader exits 1
  with a traceback on all 14 (the original defect independently reproduced).
- **Valid-output byte identity**: reader stdout on the shipped example report
  (sha256 `d37a34a5…`, 2707 B) and the B3 rotcoupon report (`8674569a…`, 2902 B) is
  byte-identical pre/post AND matches W3's own `after` receipts
  (`receipts/43_byte_identity_ab.txt`).
- **Existing refusals byte identity**: K1–K5 (W3 fixtures) + my synthesized
  blocked-group-with-mass shape → identical stderr bytes + exit 2 pre/post; K5's
  short-circuit precedence (shape refusal before mass coercion) preserved
  (`receipts/43`, `44`).
- **Unexpected-exception guard** (`receipts/45_guard_injection.txt`): injected
  `RuntimeError` in `np.asarray` → propagates; `__float__` raising `RuntimeError` →
  propagates; `__float__` raising `ValueError` → converted to the named refusal.
  No blanket catch.
- **R2 hostile variants** (mine, disjoint from W3's fixtures):
  - 4-column center value → named refusal, identical pre/post.
  - mass `"1e400"` (string → inf) → named refusal via the isfinite guard, pre/post.
  - numeric-string mass `"2.0"` and boolean `true` → exit 0 silent acceptance —
    exactly W3's recorded out-of-scope observation O1, unchanged by the repair.
- **Note N-W3-1 (generality probe, falsifier F-R2-3 — hit, recorded, non-blocking):**
  out-of-range integer literals still crash UNCAUGHT at the SAME three wrapped sites:
  mass = 10^400 (400-digit JSON int) → `OverflowError: int too large to convert to
  float` at `_as_number` (reader line 43); one 10^400 tensor entry → same at
  `_as_float_array`. Exit 1 + traceback, on BOTH the current and the pre-W3 reader —
  a pre-existing class, NOT a regression (A/B receipts `40_*/41_*`). The JSON number
  grammar admits unbounded integers, and `OverflowError` is neither TypeError nor
  ValueError, so it is outside W3's frozen conversion contract. Candidate decision
  request for a follow-up (e.g., include OverflowError in the conversion tuple).

## Check 5 — Joint run (P11): HOLD

`receipts/50_joint_run.txt` (HEAD a00146f3, one shell, sequential):
full battery **8 tests OK** (includes both identity tests + the reader tests) ·
W1 suite **9 tests OK** · W3 suite **11 tests OK**. The W1 battery change and the W3
reader repair coexist with zero interference (the battery itself runs the repaired
reader against example + coupon reports).

## Falsifier ledger

| Falsifier | Status |
|---|---|
| F-R2-1 (any P1–P4/P7/P9/P10/P11 fails) | not fired |
| F-R2-2 (pin integrity) | not fired |
| F-R2-3 (coercion class outside the 14 shapes still crashes) | **FIRED — recorded**: OverflowError on out-of-range JSON integers; measured pre-existing on both readers, non-regression, non-blocking |
| F-R2-4 (append not purely additive / silent skip) | not fired |

## Receipts index

`00_prereg_hash.txt` · `10_corpus_build.txt` · `w1_genuine/m1/m2/m3/missing_source/
tampered_pair/tp_negative/badpin/headpin(.json+.stdout.json)` · `w1_tp_regeneration_runner.json`
· `30_battery_diffstat.txt` · `40_*/41_*` (6 hostile fixtures × current/pre) ·
`42_crash_shapes_14.txt` · `43_byte_identity_ab.txt` · `44_k1_k5_ab.txt` ·
`45_guard_injection.txt` · `50_joint_run.txt`. Scratch: `work/w1/`, `work/w1_mat/`,
`work/w1_mat_badpin/`, `work/w1_mat_headpin/`, `work/w3/{current,pre,fixtures}/`.
