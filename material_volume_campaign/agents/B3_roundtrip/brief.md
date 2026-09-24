# ROLE: B3 — reader/exporter round-trip (off-diagonals, provenance, explicit frames)

> PROVENANCE NOTE: this brief is a RECONSTRUCTION. The original B3 dispatch died in
> the campaign's 4th transient [1302] (RECOVERY.md T5, "died at 5 min"); the
> coordinator's retry dispatch restated every brief law verbatim, and this file was
> written from that restatement BEFORE any B3 execution. No B3 measurement had run
> when this file was created. Any deviation of this reconstruction from the original
> wording is the coordinator's restatement to blame, not a quiet relaxation.

CONTEXT: 24h material-volume campaign. Workspace = worktree E:/ChimeraWork/mvc-20260924
(branch material-volume-campaign-20260924, base 3db8bc4e). Targets: the exporter/reader
stack under tools/ — `material_volume_body_export.py` (authoritative report producer,
canonical JSON on stdout) and `material_volume_body_export_reader.py`
(`read_json_file` + `summarize_export_report` + `canonical_json`) — and the contract
`Chimera/docs/matter/rigid_body_mass_export_consumption_contract_v1_proposal.md`
(proposal v0.9, §1 field-authority table, CON-1..CON-14).

KNOWN CONTEXT from B4 (integrated, binding here): disk bytes on this Windows worktree
are the CRLF-smudged layer vs LF git blobs. For BYTE-LAYER comparisons use the
exporter's own `canonical_json` serialization — never raw file bytes.

LAWS: everything outside agents/B3_roundtrip/ is READ-ONLY. tools/ and docs/ are never
written by B3 — run against tools/ via sys.path insertion (or module copies) with
PYTHONDONTWRITEBYTECODE=1 and sys.dont_write_bytecode, so tools/ gains no __pycache__.
PREREGISTRATION BEFORE EXECUTION; preserve failures; corrections = logged explanation +
new receipt. CPU-only. Write ONLY inside agents/B3_roundtrip/.

OBJECTIVE: measure whether a genuine exporter report — written, parsed back by the
reader, and passed through the reader's summary — preserves the contract's §1
authoritative content: off-diagonal tensor entries, center of mass, frame fields,
per-cell provenance, admission binding, and the readiness non-claim.

TASK:
1. PREREGISTER before any run:
   - Fixtures: >= 2, including one authored fixture whose report has NONZERO
     off-diagonal inertia entries produced VIA A ROTATED AUTHORED FRAME (proper
     orthonormal rotation, not axis-aligned); second fixture may reuse the shipped
     tools/ example triple. All fixture files live inside agents/B3_roundtrip/.
   - Invariant list (checked per fixture, per layer): (I1) all 9 inertia tensor
     entries; (I2) COM value+unit+frame; (I3) frame fields (body_frame and the
     tensor/COM frame identifiers); (I4) per-cell provenance rows; (I5)
     admission_status + admission_report_sha256; (I6) dynamics_readiness_claimed
     stays false in every produced document.
   - Tolerance: EXACT EQUALITY on parsed values (float equality after JSON parse;
     no approx comparisons; any mismatch recorded with float.hex).
   - Falsifier: ANY invariant field dropped or differing at any layer, for any
     fixture. A fired falsifier is a preserved verdict, never tuned away.
   - Stop rule: the full invariant x fixture x layer matrix is complete, plus the
     byte-layer canonical round-trip checks, plus the integrity paste; then verdict
     and STOP.
2. Execute: exporter CLI on each fixture triple -> report file; reader parse
   (read_json_file) -> canonical comparison against exporter output; reader summary
   (summarize_export_report) -> invariant checks against the parsed report; reader
   output itself re-parsed (its own round-trip stability).
3. Byte-layer findings: classify every non-identity EXPECTED (rule quoted) /
   UNEXPECTED (defect-class, preserve) / UNPROMISED (decision request); relate the
   summary-projection findings to M09's banked U7 finding (summary drops CON-4/6/7
   display fields on blocked/refused reports) WITHOUT duplicating it — B3's lane is
   the complete/export path and the §1 authoritative fields.
ACCEPTANCE: (1) frozen prereg with file-timeline proof; (2) fixtures + canonical
hashes; (3) invariant x fixture verdict matrix; (4) byte-layer findings + relation to
U7; (5) integrity: `git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- tools
Chimera/docs/matter` -> empty (pasted), and tools/ free of __pycache__.
OUTPUT: report.md (+ work/, receipts/, fixtures/). STOP when verdicted.
