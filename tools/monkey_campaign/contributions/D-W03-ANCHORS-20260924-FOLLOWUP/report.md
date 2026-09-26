# D-W03-ANCHORS-20260924-FOLLOWUP — versioned walking-anchor certificate verifier

**Verdict: implemented and verified; the REAL tree correctly measures INCOMPLETE —
QUALIFIED is unreachable while gates G1–G6 stand, and CPU evidence is structurally
rejected as device proof. Every preregistered prediction held; no falsifier fired.**

- card: `D-W03-ANCHORS-20260924-FOLLOWUP` (planning id W03; depends on
  D-W03-ANCHORS-20260924 = merged PR #119 head `37fd8679aee97674eca34cd83031ba020ff99c04`)
- attempt: `32070971d03443cebb213bf285835871`, agent `c95e1722350849bca846b237c1f60997`
- branch-2 checkout base `c525b82c7c3ce0128565424764293a3c85811ab3`; criteria
  `6c301b40e033f40ff1c97148f11bdf8e44000134ab3214c8f3582991ea62730f`
- preregistration: `PREREGISTRATION.md` (written before any implementation edit)
- prior attempt `d04bc55e81a0485388755822900674a7` left only a checkout skeleton —
  no candidate work existed to recover; this attempt implemented from scratch.

## What was implemented

`implementation.py` — a deterministic, read-only, CPU-only, stdlib-only verifier for
`chimera.walking_anchor_certificate.v1` certificates that bind the W03 anchor chain:

- **source identities**: per anchor — commit + repo path + extraction convention
  (`raw` blob bytes, or `lf-to-crlf` = the on-disk working-tree bytes the shutdown
  registry hashed) + expected sha256, resolved via `git rev-parse`/`cat-file`.
- **binary identities**: v2 binaries anchored to `source_build` (source commit +
  build script hash-verified); an on-disk rebuilt binary hash is the ONLY G2-closing
  evidence; historical hashes stay historical.
- **output receipts**: git-blob or on-disk locations with a LEG (host/device/cpp)
  and NATURE (historical/fresh), each hash-verified.
- **the device-proof law**: a comparison requiring `device_leg_fresh` is satisfied
  ONLY by verified evidence with leg=device AND nature=fresh. CPU/host evidence
  offered in its place produces the named rejection
  `cpu_evidence_not_device_proof`; a missing receipt stays `output_missing`;
  supporting host evidence next to a valid fresh device receipt is allowed.
- **reachability law**: a provenance commit that resolves as an object but sits on
  NO branch (the `a62b286e` orphan) is a named finding
  `provenance_commit_unreachable` (G1), never a silent pass.
- **gate law**: a CLOSED gate needs verified evidence; unverified references
  downgrade it to effective OPEN (`gate_evidence_missing`).
- verdicts: `QUALIFIED` (exit 0) / `INCOMPLETE` (exit 1, named findings) /
  refusals (exit 3: unknown schema, missing repo, unresolvable pin — no verdict
  written).
- `from-manifest` subcommand converts the parent's
  `anchor_manifest_v2.proposal.json` (22 entries) into the v1 certificate,
  preserving per-entry conventions and expected hashes.

## Exact reproduction commands (from this attempt workspace)

```
python -B -m unittest test_implementation -v
python -B implementation.py from-manifest --manifest E:/ChimeraWork/monkey-coordination/kanban-attempts/D-W03-ANCHORS-20260924/f7fd439796784e7e980a33cd90978c0d/anchor_manifest_v2.proposal.json --tie2-disk-root E:/ChimeraWork/monkey-play-20260924/tools/monkey_campaign/agents/TIE2 --out evidence/certificate.json
python -B implementation.py verify --certificate evidence/certificate.json --repo E:/ChimeraWork/monkey-play-20260924 --out evidence/verify_out
```

Measured: suite **15/15 OK in 3.643 s**; real-tree verify **exit 1 — INCOMPLETE**
(evidence preserved in `evidence/certificate.json`, `evidence/verify_out/verdict.json`).
Environment: Windows 10.0.26200 x64, CPython 3.14.3. All runs CPU-only, read-only
against the repo (rev-parse / cat-file / branch --contains only).

## Real-tree result (prediction 1-2 exact)

- checked: **18/18 git anchors verify** under their declared conventions
  (zero `anchor_hash_mismatch`, zero `anchor_path_missing`); 5/5 TIE2 on-disk
  outputs verify RAW; 4 binaries report `binary_not_rebuilt` (source-anchored).
- findings, by name: `provenance_commit_unreachable` (a62b286e orphan — G1);
  18 x `anchor_commit_unreachable` (orphan evidence per anchor); 4 x
  `binary_not_rebuilt` (G2); `cpu_evidence_not_device_proof` for
  `host_device_parity_t1_t43` (5 verified host/historical outputs, all CPU);
  `output_missing` for `c3_bars_remeasure` (no evidence at all — G4).
- comparisons: parity t1–43 UNSATISFIED (fresh device receipt absent — G3),
  c3 bars UNSATISFIED; gates G1–G6 all effective OPEN → verdict INCOMPLETE.
- This replicates the parent card's anchor table and gap isolation through
  independently written code — the certificate machinery cannot manufacture a
  pass on the real tree.

## Test coverage (15 tests, all green)

- fixture QUALIFIED control (complete synthetic certificate, labeled fixture);
- old-anchor mutation → exactly that anchor reported `anchor_hash_mismatch`;
- missing device receipt file → `output_missing`, comparison unsatisfied;
- CPU-only or historical-natured evidence → `cpu_evidence_not_device_proof`,
  never QUALIFIED;
- gate evidence downgrade CLOSED→effective OPEN;
- unresolvable commit → refusal `PIN_UNRESOLVABLE` exit 3, no verdict file;
- wrong schema → refusal `CERT_SCHEMA_UNKNOWN` exit 3;
- real-tree conversion structure (18 anchors raw+crlf conventions, 4 binaries),
  18/18 verification, orphan G1, 4x G2, device proofs missing, mutated real
  anchor fails named.

## Falsifier scorecard (from PREREGISTRATION.md)

- **F1** (QUALIFIED/missing-finding omission while gates open): NOT FIRED —
  real tree INCOMPLETE with every open gate named.
- **F2** (CPU output satisfying a device comparison): NOT FIRED — named
  rejection tested both real (TIE2 host legs) and synthetic.
- **F3** (mutated/unresolvable anchor passing, or failing unnamed): NOT FIRED.
- **F4** (fabricated predecessor fact / fixture labeled native acceptance /
  out-of-scope edits): NOT FIRED — every parent fact cited was re-measured
  through the verifier itself; fixtures labeled "fixture"; the patch adds only
  this contribution directory; no physics/threshold/production change.

## Remaining gates (preserved as missing — not closed by this card)

G1 reachable-ref for `a62b286e` (lead), G2 binary rebuild, G3 fresh device
tie-v2 replay, G4 C3 bars re-measure, G5 tick-41 sign-knife registration, G6
non-author review + certificate publication. When G1–G5 close, rerunning
`verify` on an updated certificate (with the fresh device receipts and rebuilt
binary hashes) is the adoption check G6 review can rely on.

---

# RECONCILIATION — attempt 588079e4fea6488393055523be11dd6d (2026-09-25, later)

Responds to the lead's hash/provenance reconciliation directive (and
E:/Chimera/attempt-identity-audit/AUDIT.md). Chronology, honestly:

1. **Original request** `publication-da5f190d…` (attempt `32070971`) recorded:
   implementation `1ba7ba87`, tests `be5c2c48`, patch `ecf66f5a`, report
   `0f8d5b14`, prereg `e4e1cd0c`. It remains PENDING — preserved, not blessed.
2. **Post-submission changes in the 32070971 workspace by another party**:
   `PREREGISTRATION.md` was replaced (now `71dd118f` — its content describes
   the GENERIC source→binary→device verifier that became PR #129, attempt
   `fedb0b8b`, and PR #129 shipped that exact file); `proposed.patch` was
   overwritten (now `5f0567cf`); `candidate.diff` was added. The three files
   implementation/tests/report were NEVER modified (hashes still match the
   original request). The tampered files are left in place as evidence; this
   attempt did not touch them. (Context: this reviewer's CHANGES_REQUIRED
   review of PR #129, recorded separately, documents the scope disconnect.)
3. **This handoff recovers the original candidate byte-exactly**:
   - `PREREGISTRATION.md` reconstructed from the author's frozen source text
     and **verified against the recorded hash `e4e1cd0c`** (exact match);
   - `proposed.patch` regenerated from the four verified files and **verified
     against the recorded hash `ecf66f5a`** (exact match);
   - `implementation.py`/`test_implementation.py`/`report.md` copied
     byte-identical (hashes `1ba7ba87`/`be5c2c48`/`0f8d5b14` all match).
4. **One justified test change** (documented, not silent): the real-tree TIE2
   test now guards against the MUTABLE live worktree. Since the original run,
   the play worktree advanced (HEAD `391f0ede`) and the five TIE2 battery
   files were REMOVED from disk; the verifier honestly reports them as named
   `output_missing` findings (outputs checked 0) while the device-proof law
   is unchanged — no comparison is satisfied, verdict still INCOMPLETE. With
   the files present (the parent card's recorded state), the same test
   asserts 5/5 verified + the CPU-substitution rejection. No other test logic
   changed.
5. **Re-verification in this attempt's workspace**: `python -B -m unittest
   test_implementation` → **15/15 OK**; real-tree run → exit 1 **INCOMPLETE**
   (18/18 git anchors verify; 30 named findings: orphan provenance G1, 4×
   binaries-not-rebuilt G2, parity + C3 device proofs missing).
6. Fresh hashes for this handoff are on the request; the patch in THIS
   request is regenerated from the recovered set plus the guarded test, so
   its hash differs from `ecf66f5a` by exactly that documented change.
