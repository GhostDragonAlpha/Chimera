# MAT2-B01 preregistration — frozen BEFORE any verification execution

- task: MAT2-B01 (attempt 67fafbdd5cdb4bc09faa3e4fd9b53eb1)
- agent: arrival-d6d1338a160d46b29807e1fbef765dc2
- criteria_sha256: 11c4ca47f518e37283b6ea8fbe588f71d7c9234249c3c011899b82d6131fc3d3
- pinned review target: 1af0bbdee68d6ddfdd02bf9bd948f7b22f914d56
- profile: records / offline; numerical evidence required; falsifier: "Missing
  identities or a claimed pass unsupported by records fails; a screenshot is
  not a substitute."
- machine: CPU-only, `python -B`, `PYTHONDONTWRITEBYTECODE=1`, no GPU, no network.
- This file is written before running any proof, oracle, or coupon probe of
  this attempt. Only reconciliation reads (git history, docs, receipts) and
  this freeze preceded it.

## Statement being qualified

The frozen exporter-proof revision `1af0bbde` (SI 5/5, FC 8/8, verify 7/7) and
its single verification receipt at `3db8bc4e` left three items open; closing
card MAT2-B01 means actually closing them now, with fresh non-author evidence:

1. the receipt's "open reviewer brief" (independent proof audit) was never
   executed against `1af0bbde` — an actual independent review targeting
   `1af0bbde` must exist;
2. untested assertion **U1** ("bodies owning more than one cell (multi-cell
   aggregation, mixed-material provenance consistency under aggregation)") must
   carry **frozen analytic evidence** — the archived campaign coupon
   `M02_multicell` (commit `4f610ae1`, prereg-frozen 2026-09-24) is the
   reconciled evidence source; this attempt re-executes it at the pinned bytes
   instead of re-authoring a new coupon;
3. hash claims must remain distinct: raw working-copy SHA-256, LF-canonical
   SHA-256, and git blob OID are three different identity classes and every
   recorded identity in this attempt's evidence names its class (portable
   identity per B4 law = git blob OID + LF-canonical SHA-256).

Reconciled precondition (verified read-only before freeze): `tools/` module
bytes at `3db8bc4e` equal those at `1af0bbde` (`git diff --name-only
1af0bbde 3db8bc4e` touches only `Chimera/docs/matter/*`), so the archived
coupon's exporter modules are exactly the pinned review target's bytes.

## Independent role disclosure

The original proofs and their H/Q oracles are single-author artifacts (receipt
disclosure). This attempt's reviewer is a different session, tooling and day;
its from-scratch derivations below are written fresh in this attempt workspace
(pure stdlib, no `tools/` imports, no reuse of the frozen derivation script's
code), which supplies the correlated-authorship control the receipt said no
in-repo check could provide. Archived receipts (M01, M02, B4, B10) are cited
read-only as provenance, never promoted to this card's acceptance.

## Frozen predictions (all judged against frozen tolerances; no mid-run edits)

- **P1 (clause 1, battery).** From blob-form (`git cat-file blob`) extraction
  of `1af0bbde`: SI proof 5/5 OK; FC proof 8/8 OK; integrated verify battery
  reports exactly one failure and it is the documented saved-example
  byte-identity check (M-1a/C-1 materialization class, M01-F1: raw-LF
  materialization -> 6/7 at one byte); re-materializing the example report as
  CRLF working-copy bytes makes the battery 7/7. Any SI/FC failure, or any
  verify failure NOT of that saved-example byte-identity class, fires
  F-B01-1.
- **P2 (clause 1, inventory).** unittest discovery over the six frozen modules
  at `1af0bbde` enumerates exactly 66 unique (module, qualified name)
  identities: material_volume_checks 17, material_volume_admission_checks 21,
  material_volume_body_export_checks 8, material_volume_shared_interface_proof
  5, material_volume_frame_composition_proof 8,
  material_volume_export_proof_verify 7. Any other count fires F-B01-2.
- **P3 (clause 1, from-scratch re-derivation; brief items 2+4).** This
  attempt's own derivations (exact `fractions.Fraction` simplex moments on the
  frozen coupon geometry, plus an independently constructed quadrature
  cross-check) reproduce the frozen expectation tables in the two SI/FC
  preregistrations and the frozen results-doc rows (SI: masses 2/1/3 kg,
  combined COM (1/4,1/4,1/12), combined inertia
  [[47/120,3/80,1/80],[3/80,47/120,1/80],[1/80,1/80,9/40]] kg m^2; FC bodies
  2/1 kg) within TOL = 1e-12 (absolute where |exp| <= 1, else relative). A
  larger deviation fires F-B01-3.
- **P4 (clause 2, U1 coupon re-execution).** With the archived M02 fixtures,
  oracle, prereg tolerances (TOL(exp)=1e-9*max(1,|exp|), T_ZERO=1e-9) and
  comparator run unmodified at the pinned exporter bytes: derivation oracle
  gates green; schema validation 5/5; two exporter runs byte-identical; the
  comparator reports PASS on every row and the row count equals the archived
  receipt's 142; reader accepts the report; worst deviation <= 5.68e-14
  (archived bound; hard gate = frozen per-quantity tolerances). Any row FAIL,
  count mismatch, or run nondeterminism fires F-B01-4.
- **P5 (clause 1, C-1/C-2/C-3 adjudication; brief item 3).** The prereg
  documents and fixture documents present at freeze commits are byte-identical
  (blob-OID equality) between `d2c23741` (SI/FC preregs + 7 fixtures +
  derivation script) / `f2bcac88` (verification prereg) and `1af0bbde`. The
  `d2c23741..1af0bbde` delta touches only the disclosed corrective-action
  sites: proof/audit code (C-2 SI comparator labels, C-3 verify allowlist),
  the example report's serialization (C-1: JSON-content-equal, canonical
  bytes), and docs/forearm-package files. Any fixture/expectation/tolerance/
  acceptance-criterion change fires F-B01-5.
- **P6 (clause 3, hash distinctness).** The attempt's manifest labels raw /
  LF-canonical / blob-OID separately for every artifact; at least one artifact
  lawfully exhibits raw != canonical with blob OID stable across
  materializations; the 8 key frozen artifacts' LF-canonical SHA-256 (first
  16) match the frozen receipt's canonical manifest table. A conflated or
  mismatching identity fires F-B01-6.
- **P7 (contract C04, scaling law, independent transformed integrals).** This
  attempt's own derivation on the frozen U1 coupon cells at unchanged density:
  m(s) = s^3 m(1) and I_com(s) = s^5 I_com(1) for s in {0.5, 2, 10} within
  1e-12 relative. Boundary recorded, not claimed: the exporter's
  `scale_to_m != 1.0` input path remains U2 (B02 scope); no runtime claim.

## Attached calculation contracts (task-owned subset)

- **C02 mass inventory** — evidence: U1 coupon exact masses for disjoint
  mixed-density cells under one body (m = integral rho dV), disjoint-AABB
  ownership gate, SI shared-interface control (internal interface contributes
  no material), whole-partition recombination control.
- **C03 COM + inertia** — evidence: full symmetric inertia including
  off-diagonals vs this attempt's independent quadrature; authored-frame
  rotation covariance (FC proofs + coupon authored frames); parallel-axis
  recombination exact.
- **C04 scaling/conditioning** — evidence: P7 independent transformed
  integrals on non-unit fixtures; applicability boundary recorded (no
  exporter scale-path claim, no runtime claim).

## Frozen falsifiers

| id | fires when |
|---|---|
| F-B01-1 | SI/FC counts differ from 5/5 and 8/8, or a verify failure outside the saved-example byte-identity class occurs in either materialization |
| F-B01-2 | inventory != 66 with the exact 17/21/8/5/8/7 split |
| F-B01-3 | from-scratch derivation deviates > 1e-12 from any frozen expectation |
| F-B01-4 | any U1 coupon row fails frozen tolerance, row count != 142, or the two runs differ |
| F-B01-5 | any prereg/fixture criterion changed between freeze commits and 1af0bbde |
| F-B01-6 | hash classes conflated, or portable identity mismatches the frozen manifest |
| F-B01-7 | NEGATIVE CONTROL (must fire): perturbing one copied expectation by +1e-6 relative must be REJECTED by this attempt's comparator; if the perturbed value passes, the comparison harness is broken and every PASS verdict in this attempt is void |
| F-B01-8 | any probe cannot run as pinned (missing module/fixture identity) — record and stop, no substitution |

Stop rule: any falsifier firing stops the attempt's claim; the fired
falsifier, its output, and all completed probes are preserved verbatim. No
tolerance, fixture, or prediction is edited after this freeze; deviations are
reported as observed with a named classification.

## Frozen probes (exact commands; all CPU, all offline)

- extraction: `git cat-file blob <rev>:<path>` for every frozen artifact,
  provenance (commit, path, blob OID) recorded next to each extract;
- battery: `python -B tools/material_volume_export_proof_verify.py` over the
  extracted tree, in blob-form (LF) and CRLF-materialized variants;
- inventory: unittest discovery over the six extracted modules (no test
  executed twice for counting; discovery-only count, then suite runs);
- derivations: this attempt's scripts under `work/independent/` (stdlib only);
- coupon: archived M02 `derive_oracle.py` -> `validate_fixture.py` -> exporter
  x2 -> `compare.py`, run from extracted bytes with
  `PYTHONDONTWRITEBYTECODE=1`;
- adjudication: `git diff d2c23741 1af0bbde` / `git diff f2bcac88 1af0bbde`
  name+content inspection against P5's allowed-site list.

Freeze complete. Execution may now begin.
