# PREREGISTRATION — D-W03-ANCHORS-20260924-FOLLOWUP

Card: `D-W03-ANCHORS-20260924-FOLLOWUP` (planning ID W03, verification profile:
anchor-certificate verification).
Attempt `32070971d03443cebb213bf285835871`, agent `c95e1722350849bca846b237c1f60997`,
criteria sha256 `6c301b40e033f40ff1c97148f11bdf8e44000134ab3214c8f3582991ea62730f`.
Written BEFORE any implementation edit (Rule 0).

## SUBJECT (predecessor facts, all cited — none fabricated)

Parent card D-W03-ANCHORS-20260924 (winning PR
https://github.com/GhostDragonAlpha/Chimera/pull/119, head
`37fd8679aee97674eca34cd83031ba020ff99c04`, criteria `841796bb…`) delivered
`anchor_manifest_v2.proposal.json` (schema `chimera.anchor_manifest.v2.proposal`,
22 entries) under the astra-0008 W03 ruling (Option B: versioned re-baselining),
verified locally at
`E:/ChimeraWork/monkey-coordination/kanban-attempts/D-W03-ANCHORS-20260924/f7fd439796784e7e980a33cd90978c0d/anchor_manifest_v2.proposal.json`.
Key predecessor facts this card BUILDS ON (each re-measurable by the verifier):

- 18 git-text anchors verify at orphan commit `a62b286e` (5 CRLF + 2 raw fixture,
  2 v1-band, 3 pre-v2, 6 v2-recorded), with per-entry declared extraction
  convention (raw = blob bytes; lf-to-crlf = blob with LF→CRLF, equal to the
  registry's on-disk working-tree hash).
- `a62b286e` is an ORPHAN: object exists in `E:/ChimeraWork/monkey-play-20260924`,
  no ref contains it (G1 blocker, lead-owned).
- 4 v2 binaries are NOT_IN_GIT by design (gitignored; re-anchor to
  source+build-script+rebuild hash; G2 open).
- TIE2 battery: 5 files on disk under `tools/monkey_campaign/agents/TIE2` at
  branch commit `ebc00096`, verifying RAW (host legs only; GPU legs never executed).
- Gates G1–G6 all OPEN; the sole host-vs-device parity on record is HISTORICAL;
  fresh device proof (G3) and C3 bars (G4) unmeasured.

## STATEMENT (a theory that can lose)

A deterministic certificate verifier can bind the W03 walking-anchor chain —
source identities (commits, paths, extraction conventions), binary identities
(source+build-script anchoring), input anchors and output receipts — and decide,
from pinned evidence ALONE, whether the versioned certificate is complete; in
particular it can make "CPU/host evidence presented as device qualification"
structurally impossible (an output's leg+nature must both satisfy the comparison's
requirement, and a missing receipt stays missing) such that the REAL tree today
yields INCOMPLETE with exactly the open gates named — no verifier-side pass is
reachable while G1–G6 stand.

## PREDICTION (not yet measured)

1. Converting the parent manifest to a `chimera.walking_anchor_certificate.v1`
   and verifying against `E:/ChimeraWork/monkey-play-20260924` reproduces the
   parent's anchor facts through independent code: 18/18 git anchors verify under
   their declared conventions; 4 binaries report source-anchored/absent; the 5
   TIE2 on-disk outputs verify RAW; `a62b286e` is reported unreachable-from-refs
   (finding, not refusal).
2. The real-tree verdict is INCOMPLETE (exit 1) with named findings including:
   provenance-commit-unreachable (G1), fresh device proof MISSING for the
   host-vs-device parity comparison and the C3 bars comparison (CPU evidence on
   record classifies as historical/host-only and is explicitly rejected as device
   proof), binaries not rebuilt (G2). QUALIFIED is unreachable on this tree.
3. Mutating one anchor's expected hash in the certificate → exactly that anchor
   reported `anchor_hash_mismatch` (named), verdict not qualified.
4. Pointing an anchor at a real commit that lacks its path → `anchor_path_missing`
   finding; naming a nonexistent commit → named refusal exit 3 (PIN_UNRESOLVABLE),
   no verdict written.
5. A synthetic COMPLETE certificate (fixture git repo, all anchors verifying,
   on-disk receipts present, a leg=device nature=fresh receipt, all gates CLOSED
   with verified evidence) → QUALIFIED exit 0; deleting that device receipt, or
   swapping it for a host/historical one, flips the verdict to INCOMPLETE with
   `output_missing` / `cpu_evidence_not_device_proof` named — CPU evidence can
   never close a device-required comparison.

## FALSIFIER (named before the run)

Any of the following fails this card:

- F1: the verifier reports QUALIFIED (or omits a missing-comparison finding) on
  the real tree while any gate G1–G6 is open or any device-required comparison
  lacks a fresh device receipt;
- F2: a host/historical (CPU) output satisfies a device-required comparison;
- F3: an anchor whose bytes were mutated (or whose path/commit does not resolve)
  verifies, or fails without a named finding/refusal;
- F4: a predecessor fact is fabricated (any manifest/parent claim cited above
  that the verifier cannot reproduce from the named sources when measured), a
  fixture is labeled native acceptance (fixtures stay labeled "fixture"; the
  real-tree run is the only non-fixture verdict), or the patch touches
  physics/thresholds/production sources (it adds only this contribution
  directory's files).

## BOUNDS

CPU-only, stdlib-only, read-only against the source repo (git cat-file/ls-tree/
rev-parse/branch --contains only); temporary directories for fixtures; each
verifier/child invocation bounded ≤110 s; no GPU, no training, no live-checkout
edits, ≤16 MiB new output.
