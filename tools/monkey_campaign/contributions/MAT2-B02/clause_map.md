# MAT2-B02 clause-to-evidence map (reconcile phase deliverable — read-only findings)

Card: MAT2-B02 — "Complete supported static exporter coverage — Authorized
scale/transform/status/numerical tests and static diagnostics ship with
distinct evidence classes"
Attempt: 5cf7f1cc0d1b40cb9f4a08fc12c4c535 · agent arrival-cccbccce34f94eb294f9e71640348b64
Criteria sha256: 151a4aa7693f30c49a32167c78301240b68d701ce1ea766134c71a4080454d7e
Verification profile: `records` / offline; numerical evidence required;
falsifier: "Missing identities or a claimed pass unsupported by records fails;
a screenshot is not a substitute."

## Reconciliation findings (all reads completed before any execution)

- Card state at arrival: OPEN, development slot 1, attempt_count 1, no prior
  PRs, no winner, task inbox EMPTY (`kanban_cli.py inbox --task MAT2-B02`).
  This attempt is the only live claim; no sibling PENDING publication exists
  for this card at the current criteria.
- Dependency MAT2-B01 merged 2026-09-27: merge commit `202fd858` ("Merge pull
  request #207 from GhostDragonAlpha/review/MAT2-B01"), now the head of
  `astra/gait-capture` (this card's PR base). B01's frozen receipt
  (`contributions/MAT2-B01/review_receipt.md` at that merge) closed U1,
  executed the `3db8bc4e` open reviewer brief, and established the
  three-class hash discipline. Its explicit handoff, quoted: "U2–U10 remain
  untested by the frozen revision and stay open for B02"; C04 boundary: "the
  exporter's `scale_to_m != 1.0` input path is NOT exercised or claimed (U2,
  B02 scope)"; runtime boundary: "U8/U9/U10 additionally require downstream
  consumer/runtime work that this offline records card does not own."
- The frozen single receipt at `3db8bc4e`
  (`Chimera/docs/matter/material_volume_export_verification_receipt.md`)
  defines the untested-assertion inventory U1–U10 at pinned revision
  `1af0bbde` = `1af0bbdee68d6ddfdd02bf9bd948f7b22f914d56`. B02's scope is
  exactly U2–U7 for this offline records card:
  | id | assertion (frozen receipt wording) | done_when word |
  |---|---|---|
  | U2 | `scale_to_m != 1.0` input-scaling path in the exporter | scale |
  | U5 | uniform-scale covariance of the export report (mass ∝ λ³, inertia ∝ λ⁵ at exporter level) | scale + numerical |
  | U6 | cell-reorder / vertex-renumber invariance of the export report | transform |
  | U7 | reader behavior on `blocked` / `refused` reports in the integrated verification | status |
  | U3 | multi-face interfaces (area sums over several shared faces; >2 regions meeting) | numerical + static diagnostics |
  | U4 | numerical stress: large coordinates, near-degenerate tets, extreme density ratios | numerical |
  U8 (cross-report consumer composition), U9 (consumption-contract clauses,
  no consumer exists), U10 (anything beyond the two synthetic coupons: no
  anatomical/mechanical/dynamics claim) are downstream consumer/runtime work —
  inventoried explicitly as UNRESOLVED by this attempt, never claimed
  (profile: "Inventory absent or unresolved components explicitly").
- Pinned bytes: `tools/` module bytes at `3db8bc4e` == at `1af0bbde` (B01
  finding, re-confirmed by `git diff --name-only 1af0bbde 3db8bc4e` touching
  only `Chimera/docs/matter/*`). All probes therefore target `1af0bbde`
  blob-form extraction, no substitution.
- Code-structure facts read from the pinned bytes before freeze (these shape
  frozen predictions):
  - exporter consumes `partition["coordinate_frame"]["scale_to_m"]` only
    AFTER admission is `validation_only_admissible`; admission `_frame`
    rejects missing/non-finite/non-positive scale first (reasons `bad_schema`
    / `bad_scale`) — so invalid scales surface as `blocked` exports with
    `admission_status: "refused"`, not as exporter `refused` status.
  - compiler `_interface_tables` skips same-region shared faces
    (`region_a_id == region_b_id → continue`); interface rows are
    cross-region only, oriented, with `area_m2` per face; pair sums are not
    pre-aggregated (multi-face interfaces sum across rows).
  - `_canonical_geometry_signature` is explicitly order/renumber-invariant
    (sorted coordinate-token keys) — a frozen invariant for U6.
  - compiler degeneracy line: `|det|/max_edge^3 <= 64*float64_epsilon`
    (≈1.42e-14) refuses; a unit-leg tet with height 2**-20 has normalized
    det ≈ 9.5e-7 — admissible but near-degenerate (aspect ≈ 4.7e6).
  - missing density: `density_kg_m3: null` → admission `not_admitted` →
    export `blocked` with per-body `blocking_cell_ids` (mechanism of the
    pinned test `test_missing_density_blocks_export_and_keeps_affected_cell`).
  - reader `summarize_export_report` accepts statuses {complete, partial,
    blocked, unsupported, refused}, exits 2 with named reasons on contract
    violations; pinned legacy coverage exercises `unsupported` only —
    `blocked`/`refused` (U7) untested at the pinned revision.
- Existing owner / prior work: the two prior B01 attempt dirs were paused
  NOT-STARTED checkpoints (B01 finding); no prior B02 attempt artifacts exist
  in this workspace; nothing to recover — no completed implementation is
  being repeated (B01 did not touch U2–U10 beyond P7's coupon-level scaling
  math, which is provenance, not an exporter-path claim).
- Authorization chain for the new tests: this card's done_when + the frozen
  receipt's reporting inventory + B01's explicit "B02 scope" handoff. The
  card's observation "Do not make every possible coupon a release gate" is
  honored: all probes are offline records evidence; nothing here promotes a
  fixture to a runtime or release gate; exporter outputs stay
  `validation_only`, `production_wired: false`, `dynamics_readiness_claimed:
  false` everywhere.

## First unmet clause at arrival

All components of the done_when are unmet at the pinned revision: no
scale-path test (U2), no exporter-level scale-covariance test (U5), no
export-report reorder/renumber invariance test (U6), no reader test for
`blocked`/`refused` (U7), no multi-face interface diagnostic (U3), no
numerical-stress diagnostic (U4), and no static diagnostics artifact with
distinct evidence classes exists for this card. This attempt supplies all of
them; U8/U9/U10 stay explicitly open for their downstream owners.

## Clause-to-evidence plan (evidence produced after the preregistration freeze)

| clause | evidence (this attempt, under tools/monkey_campaign/contributions/MAT2-B02/) |
|---|---|
| scale (U2, U5) | work/coupons/coupon_n_* unit-coordinate coupon vs work/coupons/coupon_u_* cm-authored equivalent (scale_to_m=0.01); s-sweep {0.5, 2, 10} covariance m∝s³, I∝s⁵; invalid-scale status trio; work/b02_checks.py + work/runs/ |
| transform (U6) | work/coupons/coupon_r_* (vertex-ID bijection + reversed rows + within-body cell-id sort flip + even per-cell vertex permutation); numeric invariance + exact geometry-signature equality; identity fields recorded, not compared |
| status (U7) | blocked (missing density) and refused (unknown group cell; non-orthonormal frame) reports through the pinned reader; reader tamper control (blocked_group_has_mass); bad-status rejection |
| numerical (U4, contracts) | work/diagnostics: large-coordinate, near-degenerate sliver, extreme-density-ratio coupons vs this attempt's exact Fraction oracle; worst deviations recorded |
| static diagnostics (U3 + evidence classes) | work/diagnostics/b02_diagnostics.py → work/runs/static_diagnostics.json: cube 6-tet 3-region coupon (multi-face pair sums, >2 regions at a vertex, whole-partition recombination), three-class hash manifest (raw / LF-canonical / blob OID), unresolved inventory U8/U9/U10, applicability boundaries; run twice, byte-identical |
| contracts C02/C03/C04 | C02: per-coupon exact masses + recombination controls; C03: full symmetric tensors vs oracle incl. off-diagonals, authored-frame rotation covariance; C04: U5 sweep + non-unit fixtures + adverse-scale diagnostics; boundary recorded: uniform scale_to_m only (anisotropic scaling enters as authored geometry), no runtime claim |

Written before preregistration freeze; no probe, fixture, or oracle has been
executed at the time of this file's writing.
