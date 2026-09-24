# B4 PREREGISTRATION — cross-checkout three-layer reproducibility (FROZEN before measurement)

Campaign: material-volume 24h · Agent: B4 · Workspace: E:/ChimeraWork/mvc-20260924
Revision under test: HEAD = f666e84f (branch material-volume-campaign-20260924)
Frozen: 2026-09-24, before any hash/run in this task. This file is hash-pinned in receipts/00_prereg_hash.txt immediately after write and never edited after that.

## RULE 0 THEORY

**STATEMENT** (disagreeable): The material-volume stack's reproducibility is fully determined by three
independent byte layers — (a) disk working-copy bytes, (b) git blob bytes (post clean-filter), (c) canonical
text per the exporter's `canonical_json` — and every relationship among them is fixed by exactly three
declared factors: the `.gitattributes` contract (`* text=auto`; `*.bat/*.ps1 text eol=crlf`; binary rules;
`forearm_package/** -text`), the checkout config (`core.autocrlf=true`, repo-local), and the C-1
canonicalization of saved examples ("saved-example serialization regenerated as canonical CLI bytes,
content unchanged"). No fourth factor exists.

**PREDICTIONS** (none measured yet at freeze time; orientation = config reads and code reads only):

- **P1 (blobs are LF-normalized):** every one of the 37 target files
  (11 `tools/material_volume*.py` + 16 `tools/material_volume*.json` + 10 `Chimera/docs/matter/*`)
  has a git blob at HEAD containing zero CR bytes; none of the set is exempt (`forearm_package/**`
  does not intersect the set; no .bat/.ps1/binary in the set). Corroborated by `git ls-files --eol` i/lf.
- **P2 (disk materializes CRLF):** every one of the 37 files on the worktree disk contains CRLF line
  endings (checkout materialization under `core.autocrlf=true` + `text=auto`), therefore disk bytes ≠ blob
  bytes for ALL 37, and disk sha256 ≠ blob sha256 for ALL 37. Any disk==blob equality in this worktree
  would SURPRISE this prediction.
- **P3 (canonical text layer):** for every `.json` in the set (17 files: 16 tools + matter_library.json),
  the LF form of the git blob is EXACTLY `canonical_json(parsed)` — sorted keys, `separators=(",", ":")`,
  `ensure_ascii=True`, `allow_nan=False`, trailing `\n` — because the exporter's saved artifacts were
  regenerated canonically (C-1) and the receipt records "recorded == canonical form for 14/14".
  File-class split:
  - CLASS R (report; canonical REQUIRED by contract): `tools/material_volume_body_export_example_report.json`
    (it is a saved CLI stdout). blob != canonical here would be a defect (falsifier F2).
  - CLASS I (inputs/schemas/library; canonical equality NOT contractually promised, only predicted):
    the other 16 `.json`. blob != canonical here is UNPROMISED (decision request), not a defect.
  - CLASS T (`.py`, `.md`, 20 files): canonical_json NOT APPLICABLE (not JSON documents); only layers
    (a) and (b) are defined.
- **P4 (run-behavior identity):** running each exporter CLI on the same example inputs from (i) the
  worktree files and (ii) a `git archive HEAD` extract of the same commit, with the same interpreter and
  platform, yields byte-identical stdout captures (sha256 equal) for all four CLIs:
  1. `python tools/material_volume.py tools/material_volume_example.json`
  2. `python tools/material_volume_admission.py --manifest <adm manifest example> --partition <adm partition example>`
  3. `python tools/material_volume_body_export.py --manifest <be manifest> --partition <be partition> --groups <be groups>`
  4. `python tools/material_volume_body_export_reader.py <be example report>`
- **P5 (platform stdout form):** stdout captures on this platform (win32, CPython text-mode stdout,
  newline=None → `os.linesep` translation) will contain CRLF on BOTH sides (worktree and archive), so
  P4 equality holds; additionally, LF-normalized stdout of CLIs 2-4 equals `canonical_json(parsed stdout)`
  (the "canonical CLI bytes" claim); CLI 1 prints `indent=2` pretty JSON (NOT canonical) — that is a
  documented code-read property of `tools/material_volume.py:971`, predicted to reproduce identically,
  and its non-canonicity is NOT a defect (no contract promises canonical bytes for that CLI).

**FALSIFIERS** (named before the run; any one firing stops classification-as-expected and is preserved verbatim):

- **F1:** a file whose git blob at HEAD differs from the LF-normalization of its disk bytes without a
  declared rule (i.e., blob != LF(disk) for a `text=auto` file, or any byte difference for a
  `-text`/binary-attributed file). This would mean the clean-filter contract is broken.
- **F2:** a CLASS R file (`material_volume_body_export_example_report.json`) whose blob (or LF(disk))
  is NOT equal to `canonical_json` re-serialization of its parsed content. This would defeat C-1 and the
  receipt's canonical-CLI-bytes claim.
- **F3:** any CLI whose stdout bytes differ between the worktree run and the git-archive-extract run of
  the same commit (f666e84f). This would mean cross-checkout behavior is not reproducible.
- **F4:** a `.json` file whose disk parse differs from its blob parse (content drift between layers beyond
  whitespace). JSON parse is EOL-insensitive, so any parse difference is substantive.

**EXPECTED-RULE QUOTES** (the rules mismatches will be classified against):
- `.gitattributes` line 1: `* text=auto` → clean filter LF-normalizes text files into blobs; smudge
  materializes per `core.autocrlf=true` → CRLF working copies. Quote for disk≠blob: EXPECTED.
- M-1a (verification receipt): working-copy hashes are checkout-materialization dependent; portable
  identity = git blob OID at revision + SHA-256 over LF-canonical bytes. Quote for "disk hash differs
  across checkouts but blob/canonical hashes agree": EXPECTED.
- C-1 (verification receipt ledger): saved-example serialization regenerated as canonical CLI bytes,
  content unchanged (verified json-equal). Quote for CLASS R blob==canonical: EXPECTED.
- CPython io: `sys.stdout` with `newline=None` translates `\n` to `os.linesep` on win32 when captured.
  Quote for CRLF in captured CLI stdout: EXPECTED (platform rule, not a repo rule).

**CLASSIFICATION RUBRIC** (every mismatch in the matrix gets exactly one):
- EXPECTED — mismatch follows from a quoted rule above (rule text quoted in the verdict cell).
- UNEXPECTED — falsifier fires; defect-class finding; preserved verbatim, not tuned away.
- UNPROMISED — the layers disagree but no rule covers the file class (CLASS I non-canonical forms);
  logged as a decision request for the operator.

**STOP RULE:** the matrix is complete when all 37 files have layers (a)+(b) hashed and all 17 `.json`
have layer (c), `git ls-files --eol` + `git check-attr` receipts exist for the full set, and all four
CLI pairs of P4 have comparison receipts — then verdicts are assigned ONCE from the frozen numbers and
this agent stops. No re-runs to improve verdicts; failures are preserved as measured.

**INTEGRITY LAW:** writes confined to
`E:/ChimeraWork/mvc-20260924/material_volume_campaign/agents/B4_crosscheckout/**`.
Everything outside is read-only. No new worktrees; other-revision bytes only via
`git archive`/`git cat-file`/`git show`. `PYTHONDONTWRITEBYTECODE=1` on every python invocation.
