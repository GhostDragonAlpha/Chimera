# R5-forest-review — evidence-verification correction report (attempt 9d1066c3)

Attempt `9d1066c32ba143beac5cde244e003244`, card `R5-forest-review`, criteria
`6198e40ba1cfe37059275bc908e55e1e4fa804d58d418bcc21ea8520e4753ae6`, branch `branch-10`,
base HEAD `d6ad8f098b9d892ba5d9c3a69290a13580897c86` (PR #115 head — also the exact
source of the four ORIGINAL deliverable files' bytes).
Commit sha of this correction: a committed file cannot contain its own commit's sha;
see the attempt-workspace copies of this report and `receipt.json` in the attempt
inbox, and the coordinator's ledger.

This correction fixes evidence verification ONLY. The static/native verdict of
`corrected_review.md` is UNCHANGED and not re-adjudicated: F02/F03/F04 verified static
only; F05/F06 never started (blocked on the walking chain); W10 NOT ready.

## What was hardened (finding msg-b935f0d9554d4924aa68f6f4f3872abd)

`tools/measure_evidence_v2.py` (the original `tools/measure_evidence.py` is preserved
byte-for-byte, unmodified) re-measures the same identities plus:

1. Every git invocation is checked; any nonzero exit refuses the whole run (exit 3,
   `GIT_COMMAND_FAILED` naming the exact command and exit code). v1 discarded
   returncodes and silently measured empty strings.
2. `ls-files` can never count as an empty inventory on failure: empty output is
   accepted only when git exited 0 AND the sanity query `git rev-parse --verify HEAD`
   also exited 0 (both recorded in the output).
3. Blob ids are validated: `git rev-parse <pin>:<path>` failure refuses; every id must
   be 40 hex; `git hash-object` (filtered AND `--no-filters`) of every working file is
   recorded against the resolved blob.
4. The reviewed revision is PINNED (required CLI argument; missing argument is a named
   refusal `PINNED_REVISION_REQUIRED`); its full sha + subject are recorded and
   `git status --porcelain` is run over the cited paths, so committed bytes are
   distinguished from dirty worktree bytes (the play worktree has 7 dirty/untracked
   lines elsewhere; NONE on the 11 cited paths).
5. Explicit line-ending policy: per document, sha256 of working bytes and of
   `git cat-file blob` bytes under raw / lf-normalized / crlf-normalized conventions.
   4 of 11 cited documents are raw-identical to their blobs; the other 7 are CRLF on
   disk vs LF blobs and are proven identical only under the normalization conventions.
   A document matching under NO convention is the named FAILURE
   `modified_cited_source`, never a pass.

The 13 original checks keep their names and semantics; the intact-tree v2 run reports
30/30 green (13 original + 11 per-document source identities + 6 hardening gates).

## Controls (tools/run_controls.py → evidence/control_results.json)

- (a) GIT-FAILURE (v2 against a temp dir that is not a repository, isolated from this
  machine's drive-root repo via `GIT_CEILING_DIRECTORIES`): v2 refused with exit 3,
  one stderr line:
  `REFUSAL GIT_COMMAND_FAILED command='git -C C:\Users\allen\AppData\Local\Temp\r5ctrl_a_notarepo_q46xfmbf rev-parse --verify dc7ea81111d98f32a4d88252c59f2fb8cf3c7399^{commit}' exit=128 stderr='fatal: not a git repository (or any of the parent directories): .git'`
  and wrote NO output file. The ORIGINAL tool under the same control: exit 1, empty
  stdout, an unhandled `FileNotFoundError` traceback, no output file — it died after
  silently treating every failed git command as empty data; the v1 `git()` helper
  (lines 59–63) has no returncode check, so a failed `ls-files` would have passed
  `f05_f06_no_tracked_files` on an empty inventory. Original left unmodified.
- (b) MODIFIED-CITED-SOURCE (tampered temp copy of PLAY_BOARD.md fed via v2's
  documented `--override-file` injection point; real worktree untouched): v2 exit 1,
  exactly one check red —
  `FAIL source_identity_tools/monkey_campaign/PLAY_BOARD.md - MODIFIED_CITED_SOURCE: work bytes match committed blob 26e6d47a8bae under NO declared line-ending convention`
  (summary 29/30).
- (c) LINE-ENDING-RESCUE positive control (CRLF→LF-flipped temp copy of
  identity_receipt.json): exit 0, 30/30, identity still proven — the policy
  distinguishes pure line-ending differences from content modification, so the
  modified-source control in (b) is a real discriminator.

## Probe note

`E:/PythonChimera/pr-review-20260925/` (probe.py and REVIEW.md named in the finding)
does NOT exist on disk as of 2026-09-25 (`ls`: "No such file or directory", exit 2).
The finding text itself was used as the requirement source.

## Falsifier self-check

Before `git add`, `git -C <checkout> status --porcelain` showed ONLY new untracked
files under `tools/monkey_campaign/contributions/R5-forest-review/`; the four
originals (tracked at base HEAD d6ad8f09..., blobs b718a68c/03dc4a76/16b93586/80a775f7)
show NO modification. Original evidence is preserved byte-for-byte.

## Remaining gates

Lead review of this attempt and merge of the eventual branch-10 PR; F05/F06/W10
verdicts are UNCHANGED (F05/F06 still require the native walking chain; W10 still not
scene-accepted as a product milestone). Finding msg-da228e217fe645d792ae98dba350eaf1
is addressed: all outputs live in this attempt workspace, full source revisions and
blob/file hashes are recorded in `evidence/correction_receipt.json`, and committed vs
worktree bytes are distinguished by the v2 run itself.
