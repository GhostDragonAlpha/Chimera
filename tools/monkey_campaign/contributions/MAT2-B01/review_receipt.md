# MAT2-B01 independent review receipt — frozen exporter revision 1af0bbde

- attempt: 67fafbdd5cdb4bc09faa3e4fd9b53eb1 · agent arrival-d6d1338a160d46b29807e1fbef765dc2
- date: 2026-09-27 · machine: CPU-only Windows, CPython 3.14, `python -B`,
  `PYTHONDONTWRITEBYTECODE=1`; no GPU, no network use during execution.
- review target (pinned, no substitution): `1af0bbdee68d6ddfdd02bf9bd948f7b22f914d56`
- criteria sha256: `11c4ca47f518e37283b6ea8fbe588f71d7c9234249c3c011899b82d6131fc3d3`
- preregistration frozen before any execution: `PREREGISTRATION.md` (this file
  was committed unmodified; predictions P1–P7 and falsifiers F-B01-1..8 frozen
  before the first probe ran).
- reviewer independence: the original proofs, their H/Q oracles, the archived
  campaign receipts and this attempt share no author, session, or tooling. No
  archived claim is promoted; archived receipts are cited as provenance only
  (MATERIAL_PLAN_ADOPTION.md rule).

## Verdict

**All three done_when clauses of MAT2-B01 are met with fresh, source-bound
numerical evidence. No falsifier fired.** Every PASS below is backed by a run
log in `work/runs/` or an extracted artifact with a three-class hash identity
in `work/runs/p6_hash_manifest.json`.

## Clause 1 — Actual independent review targets 1af0bbde

Executed the frozen receipt's five reviewer-brief items (receipt at
`3db8bc4e`, "Open reviewer brief"): all five executed; none skipped.

1. **Battery reproduction from 1af0bbde** (P1). Blob-form extraction
   (`git cat-file blob`) of all 27 `tools/material_volume*` files + docs;
   provenance = exact origin bytes (raw sha256 == blob bytes; see manifest).
   - `p1a_battery_blobform.txt`: full battery `Ran 7 tests`, **6 pass /
     1 failure**; SI 5/5 and FC 8/8 asserted inside passing tests; the single
     failure is `test_cli_determinism_and_saved_example_bytes`, assert
     `out1 != saved` differing **only in the trailing newline** (CLI stdout
     CRLF via Windows newline translation vs the LF-authored saved blob).
     This is exactly the receipt's M-1a / corrective-action C-1 /
     M01-F1 materialization class — **the frozen falsifier F-B01-1 does not
     fire** (failure confined to the saved-example byte-identity class;
     JSON content identical).
   - `p1b_battery_crlf_example.txt`: with the example report re-materialized
     as CRLF (what an autocrlf checkout materializes), **7/7 OK**.
   - Direct CLI probe: exporter stdout ends `}\r\n` (Windows `os.linesep`
     translation); the 1af0bbde blob ends `}\n` (0 CR bytes). The 7/7-vs-6/7
     flip is an environment newline behavior of one bytes-identity check,
     never a content defect.
2. **Unique-test inventory** (P2, brief item 1). `p2_inventory.json`:
   discovery-only enumeration = **66 unique identities** with the exact
   17/21/8/5/8/7 split of the frozen receipt's V2 table. F-B01-2 not fired.
3. **From-scratch re-derivation of SI/FC expectations** (P3, brief items 2+4).
   `derive_si_fc_independent_result.json`: two independent routes written
   fresh for this attempt — exact `Fraction` monomial integration over the
   reference simplex (78 checks) and a Duffy-collapsed 8-point Gauss–Legendre
   product rule (39 checks) — reproduce **every frozen literal** of both
   preregistrations (SI bodies 2/1 kg + combined row with the exact rational
   inertia [[47/120, 3/80, 1/80], …]; FC domain rows and combined
   127/120, 367/120, 427/120, ±329/240, ∓151/240, 89/240) within TOL 1e-12;
   **worst deviation 2.22e-15**. Route B shares no method code with the
   frozen Hammer–Stroud route; both routes are different authors from the
   original H/Q — the correlated-authorship residual risk named by the
   receipt is thereby covered. Fixture semantics (proposals→regions→materials
   mapping, vertex coordinates) were re-read independently by this attempt's
   own reader and the expectations re-derived from raw geometry.
   F-B01-3 not fired.
4. **C-1/C-2/C-3 adjudication against the preregistrations** (P5, brief
   item 3):
   - every fixture document, both schemas, and the prereg derivation script
     are **blob-OID-equal** between the freeze commit `d2c23741` and
     `1af0bbde` (17/17 checked); the SI/FC prereg docs are unchanged (absent
     from the `d2c23741..1af0bbde` changed-file list);
   - the verification prereg is **blob-OID-equal** between `f2bcac88` and
     `3db8bc4e`;
   - the `d2c23741..1af0bbde` delta in tools/ is exactly: the three
     proof/audit files added (964 insertions — the C-2 label alignment and
     C-3 allowlist corrections happened inside this authoring pass, before
     the commit), and the example report re-serialized (C-1): **JSON content
     equal**, bytes 8399 (pretty, `cd2b052dcf4a2334…`) → 5472 (canonical,
     `5485c8c4fe73d679…` — matches the frozen canonical manifest table).
   - No fixture, expectation, tolerance, or acceptance criterion changed
     between freeze and `1af0bbde`. F-B01-5 not fired.
5. **U1–U10 treated as untested unless separately evidenced** (brief
   item 5): see Clause 2 — U1 is now evidenced; **U2–U10 remain untested by
   the frozen revision** and stay open for B02. Nothing in this receipt
   claims them. (This attempt's evidence adds nothing for U2-U10 except P7's
   analytic scaling law, which is a math check on coupon geometry, not an
   exporter-path test.)

## Clause 2 — U1 has frozen analytic evidence

U1 = multi-cell aggregation (one body owning more than one cell, mixed
materials) — the first row of the frozen receipt's untested-assertion
inventory. Evidence, two layers:

- **Archived frozen coupon (provenance, commit `4f610ae1`)**: the campaign's
  `M02_multicell` coupon — 3 disjoint tetrahedra (right/regular/scalene),
  densities 12/6/9, `mc-body-1` owning `cell-R`+`cell-S` (mixed shapes and
  densities under one body — the U1 aggregation case), authored frames
  Ry(90°)Rz(30°)·(2,−1,3) and Ry(60°)Rz(90°)·(−1,4,−2). Its `PREREG.md`
  freeze-table (six artifact sha256s, prereg frozen before the exporter ever
  saw the fixture) was **verified byte-for-byte against the git-extracted
  artifacts: 6/6 match** (`m02_archived/`).
- **Fresh re-execution at the pinned bytes (this attempt)**: exporter module
  copies byte-identical across frozen extraction, archived coupon, and rerun
  tree (sha256-checked). `work/m02_rerun/`:
  1. derivation oracle gates green (`p4_derivation_gates.txt`: volumes 1/6,
     8/3, 17/6; AABBs disjoint; frames exactly orthonormal det +1; H vs Q/R2
     ≤ 2.84e-14; anchor vs published literals 2.78e-17; protected
     off-diagonal margin 2.3099 ≫ 0.002);
  2. **freeze-integrity control fired live**: regenerated
     `derived_expectations.json` sha256 == frozen `d8ed7a82b13c168b…`
     byte-identical;
  3. schema validation PASS (jsonschema 4.25.1, existing shipped schemas
     untouched);
  4. exporter run 1 and 2 both exit 0 and **byte-identical** (5955 bytes);
     JSON content equal to the archived receipt's report (my shell redirect
     recorded the platform CRLF trailing newline; content equality verified);
  5. archived comparator (freeze-check by sha256 built in): **142/142 PASS,
     0 FAIL** — worst deviation **5.684e-14** (whole-partition parallel-axis
     recombination) against frozen tolerances 1e-9·max(1,|exp|); the
     must-stay-zero off-diagonals of the isotropic regular tet are exactly
     0.0 (no invented cross terms); `off_diagonal_terms_preserved: true`,
     `principal_axis_transform_applied: false`, `dynamics_readiness_claimed:
     false`;
  6. shipped reader accepts the fresh report (exit 0).

F-B01-4 not fired. **U1 now carries frozen analytic evidence, re-verified
today at the review target's bytes.**

## Clause 3 — Hash claims remain distinct

`work/runs/p6_hash_manifest.json`: 99 evidence artifacts hashed into three
separately labeled classes — raw working-tree sha256, LF-canonical sha256,
and git blob OID of the pinned path. Verifications:

- the frozen receipt's 8 key-artifact canonical (LF) sha256 first-16 values
  all **match** this attempt's recomputation from origin blobs;
- the demonstration artifact
  (`tools/material_volume_export_proof_verify.py`) lawfully shows
  raw-blobform ≠ CRLF-materialized bytes with the **same stable blob OID**
  and a single canonical LF identity — the three classes are distinct and
  portable identity (blob OID + LF-canonical sha256) survives;
- every hash quoted anywhere in this receipt names its class.
F-B01-6 not fired. Honest residual: this attempt could not reproduce the
frozen 33-blob sorted digest `ee27dcd2…` from four candidate constructions
(the receipt never recorded the construction; archived B9 claims a
reproduction). Recorded as unresolved corroboration, not a criterion — the
per-artifact identities above do not depend on it.

## Attached calculation contracts (task-owned subset)

- **C02 mass inventory**: P4 coupon masses per body (27.5 kg = cell-R 2 kg
  ρ12 + cell-S 25 kg ρ9 aggregated under one body; 16.0 kg) against exact
  algebra; disjoint-AABB ownership gate; SI shared-interface control
  (internal interface contributes no material — battery F2); whole-partition
  recombination (Σ = 43.5 kg exact).
- **C03 COM + inertia**: full symmetric tensors incl. off-diagonals vs
  independent quadrature (P3 route B, P4 oracle Q); authored-frame rotation
  covariance (FC battery 8/8; coupon authored frames); parallel-axis
  recombination exact to 5.7e-14 relative to frozen tolerances.
- **C04 scaling/conditioning**: `p7_scaling_law.json` — this attempt's exact
  route on the coupon cells at unchanged density, s ∈ {0.5, 2, 10}:
  m ∝ s³ and I_com ∝ s⁵ in **30/30 checks ≤ 1e-12**. Boundary recorded: the
  exporter's `scale_to_m != 1.0` input path is NOT exercised or claimed
  (U2, B02 scope); no runtime claim anywhere (receipt's U10 boundary
  respected).

## Honest record for this attempt

- Pre-pass harness defects (this attempt's own tooling, fixed before any
  passing claim; preserved in session transcript): route-A double /6 factor;
  route-B Gauss–Legendre nodes left on [−1,1] for a [0,1] map; parallel-axis
  sign inversion; halved Legendre initial-guess angle. Two failing runs
  occurred and were diagnosed before the recorded passing run; the recorded
  passing run is reproducible from the committed scripts.
- P1's frozen prediction letter anticipated the 6/7-then-7/7 pattern; both
  materializations were then observed exactly as predicted (blob-form LF →
  6/7 with the single M-1a/C-1-class failure; CRLF example → 7/7 OK).
- DR-1 33-blob digest: not reproduced by this attempt's candidate
  constructions (see Clause 3).
- U2–U10 of the frozen receipt remain untested at 1af0bbde (B02 scope);
  U8/U9/U10 additionally require downstream consumer/runtime work that this
  offline records card does not own.

## Evidence identities (raw sha256, bytes on disk; full manifest in
work/runs/p6_hash_manifest.json)

Computed at submission time for every file under
`tools/monkey_campaign/contributions/MAT2-B01/`; see the submission
artifact list.
