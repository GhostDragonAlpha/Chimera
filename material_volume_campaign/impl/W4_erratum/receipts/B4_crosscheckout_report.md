# B4 REPORT — cross-checkout reproducibility: RAW BYTES vs GIT BLOBS vs CANONICAL TEXT

Agent: B4 · Campaign: material-volume 24h · Workspace: E:/ChimeraWork/mvc-20260924
Date: 2026-09-24 · Status: **MATRIX COMPLETE — STOP** (stop rule from frozen prereg reached)

## 0. Preregistration (frozen BEFORE measurement)

`work/prereg.md` — sha256 `5e0226330ffcf07ea7fbde497232e9c7cddd281eb3f53fd39593dfd69566283e`
(frozen copy: `receipts/00_prereg_hash.txt`). Rule-0 theory, predictions P1-P5, falsifiers
F1-F4, expected-rule quotes, classification rubric, and stop rule were all written and
hash-pinned before the first hash was taken. No prereg criterion was altered after freezing.

Revision under test: pinned `81ff947504c2eb9809e5381c614d9aa28ba57ea1`. During the task HEAD
moved twice (fleet activity: f666e84f → 81ff9475 → 4f610ae1); every intervening commit touched
ZERO target paths (`git diff --stat f666e84f 81ff9475 -- tools Chimera/docs/matter` is empty),
so all layers measured one immutable content state. The matrix was re-run pinned to the explicit
sha (numbers identical to the first run; no verdict was changed by a re-run).

## 1. The three layers, measured (37 files: 11 `tools/material_volume*.py` + 16 `tools/material_volume*.json` + 10 `Chimera/docs/matter/*`)

| # | measurement | result |
|---|---|---|
| 1 | disk bytes == git blob bytes (HEAD) | **0 / 37** |
| 2 | git blob == LF-normalization of disk bytes | **37 / 37** (F1 clean) |
| 3 | git blob contains any CR byte | **0 / 37** (all blobs CR-free) |
| 4 | `git ls-files --eol` | **37 / 37** `i/lf  w/crlf  attr/text=auto` |
| 5 | JSON: parse(blob) == parse(disk) | **17 / 17** (F4 clean — no content drift) |
| 6 | JSON: blob bytes == `canonical_json(parse(blob))` | **1 / 17** — exactly the CLASS R report |
| 7 | `git archive` extract bytes == disk bytes | **37 / 37** |
| 8 | `git archive` extract bytes == blob bytes | **0 / 37** |

Illustrative trio (example report, the one file with three lawful forms):
- disk sha256 `d71f7621ba00701c…` (5473 B, 1 CRLF; CRLF-materialized single-line report)
- blob sha256 `5485c8c4fe73d679…` (5472 B, CR-free) = blob OID `2091bee63193f029`
- canonical sha256 `5485c8c4fe73d679…` — **identical to the blob**, and both byte-for-byte equal
  to the hashes quoted in `Chimera/docs/matter/material_volume_export_verification_receipt.md`
  (working-copy hash `d71f7621…`, canonical hash `5485c8c4…`). M-1a reproduced live at HEAD.

## 2. Run-behavior reproducibility (falsifier F3) — 4 CLIs x 3 materializations x 2 reps

Arms: **WT** (worktree files) and **ARC** (`git archive` extract at pinned rev) are the
preregistered pair; **BLB** (blob bytes materialized file-by-file via `git cat-file` — the LF
form) is a post-prereg ADDENDUM arm, included because ARC proved byte-identical to WT (row 7),
making WT-vs-ARC the same-bytes comparison. Receipts: `receipts/06_run_behavior.json`.

| CLI | raw stdout identical across all arms+reps | LF stdout identical | LF(stdout) == canonical_json(parsed) |
|---|---|---|---|
| `material_volume.py` (example input) | YES (1 form, 5446 B) | YES | no — `indent=2` pretty print (as coded, `tools/material_volume.py:971`) |
| `material_volume_admission.py` | YES (1 form, 5406 B) | YES | **yes** (canonical CLI bytes) |
| `material_volume_body_export.py` | YES (1 form, 5473 B) | YES | **yes** — LF stdout sha `5485c8c4fe73d679…` = the saved example report = the receipt's recorded canonical hash |
| `material_volume_body_export_reader.py` | YES (1 form, 2707 B) | YES | **yes** |

All returncodes 0, all stderr empty, zero parse errors. **F3 does not fire: cross-checkout
behavior is byte-identical, including the CRLF-vs-LF input-materialization delta.** Raw captured
stdout carries CRLF (1 CRLF for the one-line canonical CLIs; 271 for the pretty CLI) on both
sides — the win32 text-mode stdout rule quoted in the prereg, not a repo property.

## 3. Verdict matrix (file x layer) — `receipts/07_verdict_matrix.csv`

**182 classified comparisons over 37 files: 166 EXPECTED · 0 UNEXPECTED · 16 UNPROMISED.**
No falsifier fired (F1, F2, F3, F4 all clean). Classifications:

- **EXPECTED (166)** — disk≠blob on all 37 (rule: `.gitattributes` `* text=auto` + repo-local
  `core.autocrlf=true`: clean filter stores LF blobs, smudge materializes CRLF — the M-1a rule);
  blob==LF(disk) on all 37; archive-extract==disk and archive-extract≠blob on all 37 (rule:
  `git archive` applies the checkout EOL conversion, so an archive extract is the SMUDGED form —
  it is NOT a blob-bytes materialization); example report blob==canonical (rule: C-1, saved
  report regenerated as canonical CLI bytes); stdout CRLF (platform rule).
- **UNEXPECTED (0)** — none. No defect-class finding.
- **UNPROMISED (16)** — every non-report `.json` (15 tools examples/schemas +
  `matter_library.json`) holds a NON-canonical blob (e.g. `material_volume_example.json`:
  994 blob bytes vs 753 canonical bytes, same parse). No rule promises canonical bytes for
  input/schema/library JSON; C-1's scope was the saved REPORT. **Decision request MV-B4-1:**
  either canonize those 16 artifacts (one-time rewrite, content json-equal, verified) or declare
  pretty-form authoring as their contract, so future audits don't re-litigate each one.

## 4. Falsified predictions (honest report; none was a contract violation)

- **P3 did not survive at full strength**: I predicted all 17 JSON blobs byte-canonical (from
  C-1 read broadly). Measured: 1/17. The rubric pre-assigned this exact outcome UNPROMISED for
  CLASS I, so the verdict stands as a decision request, not a defect. Lesson: C-1's "saved-example
  serialization" meant the saved REPORT only.
- **P2 held 37/37** (all CRLF on disk, all disk≠blob), **P1 held 37/37** (all blobs CR-free),
  **P4/P5 held** (byte-identical run behavior; canonical CLIs emit canonical bytes modulo the
  platform newline; `material_volume.py` emits pretty JSON — its non-canonicity is a code-read
  property, not drift; note it is also UNPROMISED whether the operator wants that CLI canonical).

## 5. Operational law this task establishes (the confusion-killer)

1. **Disk bytes** are a checkout materialization — NOT portable identity (they changed 37/37 vs
   blobs; hash `d71f7621…` vs `5485c8c4…` for the same content).
2. **`git archive` extracts are disk-form (smudged), not blob-form.** To materialize a revision's
   true bytes use `git cat-file blob <rev>:<path>` / `git show`. (The B4 brief's suggested archive
   method silently yields layer (a), not layer (b) — measured 0/37 extract==blob.)
3. **Git blob bytes** at a pinned revision are the portable identity (M-1a rule, re-verified).
4. **Canonical text** (`sort_keys, separators=(",",":"), ensure_ascii, allow_nan, trailing \n`)
   is the content identity for JSON artifacts; today exactly one target file (the example report)
   is byte-canonical, and the exporter CLI regenerates it exactly.
5. Portability contract for future receipts: **blob OID at pinned rev + SHA-256 over LF-canonical
   bytes** — disk hashes and archive-extract hashes are neither.

## 6. Acceptance

1. Frozen prereg: `work/prereg.md`, sha256 `5e022633…6283e` (`receipts/00_prereg_hash.txt`). DONE
2. Three-layer hash matrix: `receipts/01_hash_matrix.json` (37 files, per-layer sha256/size/EOL
   census, blob OIDs), corroborated by `receipts/02_eol_lsfiles.txt`, `receipts/03_check_attr.txt`,
   `receipts/04_blob_oids.txt`, `receipts/05_matrix_digest.txt`. DONE
3. Run-behavior receipts: `receipts/06_run_behavior.json` (4 CLIs x 3 arms x 2 reps, raw+LF sha256,
   canonical equality, stderr, returncodes). DONE
4. Mismatch classification: `receipts/07_verdict_matrix.csv` (182 rows; 166/0/16). DONE
5. Integrity paste (run after all writes, verbatim):
   ```
   $ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- tools Chimera/docs/matter
   EXIT=0 (empty output above = clean)
   ```
   Target paths untouched. (One transient mis-path of a scratch script into
   `material_volume_campaign/agents/` was moved into `agents/B4_crosscheckout/work/` within the
   same minute; targets were never touched.)

## 7. Artifacts

- Brief: `material_volume_campaign/agents/B4_crosscheckout/brief.md` (verbatim copy)
- Prereg: `material_volume_campaign/agents/B4_crosscheckout/work/prereg.md`
- Scripts: `work/b4_matrix.py`, `work/b4_run_behavior.py`, `work/b4_verdict.py`
- Receipts: `receipts/00_prereg_hash.txt` … `receipts/07_verdict_matrix.csv`
- Scratch materializations (B4-owned): `work/archive_extract/` (smudged form),
  `work/blob_extract/` (405 tools blobs at pinned rev), `work/run_tmp/` (CLI stdout captures)

STOP — matrix complete per frozen stop rule. No commit made (writes confined to the B4 dir;
committing is the integrator's move).
