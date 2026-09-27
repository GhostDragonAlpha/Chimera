# MAT2-B01 clause-to-evidence map (reconcile phase deliverable)

Card: MAT2-B01 — "Close independent exporter review and multi-cell coupon —
Actual independent review targets 1af0bbde; U1 has frozen analytic evidence;
hash claims remain distinct"
Attempt: 67fafbdd5cdb4bc09faa3e4fd9b53eb1 · agent arrival-d6d1338a160d46b29807e1fbef765dc2
Criteria sha256: 11c4ca47f518e37283b6ea8fbe588f71d7c9234249c3c011899b82d6131fc3d3

## Reconciliation findings (read-only, before any execution)

- `1af0bbde` = `1af0bbdee68d6ddfdd02bf9bd948f7b22f914d56` ("material-volume-export:
  body-grouping and frame-composition export proofs pass (SI 5/5, FC 8/8,
  verify 7/7)"), present in this checkout's object store.
- The frozen single receipt at `3db8bc4e`
  (`Chimera/docs/matter/material_volume_export_verification_receipt.md`)
  declares: zero subagents deployed, "no independent review is claimed",
  an OPEN reviewer brief (5 items), and an untested-assertion inventory
  U1–U10. **U1** = "bodies owning more than one cell (multi-cell aggregation,
  mixed-material provenance consistency under aggregation)". These are the
  three open clauses this card asks to close.
- The card's "multi-cell coupon" = the U1 coupon. The archived material-volume
  campaign built and integrated exactly it: `M02_multicell` (commit
  `4f610ae1`, "multi-cell coupon PASS 142/142 … prereg timeline proven").
  Per MATERIAL_PLAN_ADOPTION.md, old DONE is not silently promoted: this
  attempt RE-EXECUTES the archived coupon at the pinned bytes and cites the
  archived receipt as provenance only.
- `tools/` module bytes at `3db8bc4e` == at `1af0bbde` (diff touches only
  `Chimera/docs/matter/*`), so the archived coupon's exporter modules are
  exactly the review target's bytes.
- MAT2-P03 merged crosswalk (lead-verify receipt, raw sha256
  `2ea458a294009c16ce8258e3b364af0df31a57d52468a2b9cf5d7f7e1b205b4f`): no
  archived-board counterpart promoted to B01; B01's acceptance must be
  evidenced fresh — this attempt does that.
- Task inbox for MAT2-B01: empty. The two prior attempt dirs on this card are
  paused NOT-STARTED checkpoints; untouched.

## Clause-to-evidence map

| clause | evidence (this attempt, all under tools/monkey_campaign/contributions/MAT2-B01/) |
|---|---|
| Actual independent review targets 1af0bbde | work/frozen/1af0bbde/** (blob-form extracts); work/runs/p1a_battery_blobform.txt (6/7, single M-1a/C-1-class failure); p1b_battery_crlf_example.txt (7/7 OK); p2_inventory.json (66 = 17/21/8/5/8/7); derive_si_fc_independent_result.json (78 exact + 39 quadrature checks reproduce every frozen literal, worst 2.22e-15); review_receipt.md §P5 (C-1/C-2/C-3 adjudication: fixtures/prereg docs OID-equal freeze→1af0bbde; C-1 json-content-equal, canonical sha 5485c8c4fe73d679 matches frozen table) |
| U1 has frozen analytic evidence | work/m02_archived/** (archived coupon receipt, commit 4f610ae1; its PREREG freeze-table hashes verified against extracted bytes — all 6 match); work/m02_rerun/** (fresh re-execution at pinned bytes: derivation gates green; expectations regenerate byte-identical sha d8ed7a82…; schema PASS; exporter ×2 byte-identical; comparator 142/142 PASS, worst 5.684e-14; reader exit 0, readiness false) |
| hash claims remain distinct | work/runs/p6_hash_manifest.json (99 artifacts × {raw, LF-canonical, blob-OID}; 8/8 frozen key canonical-16 match; raw ≠ CRLF-materialized demonstrated with stable blob OID) |
| contracts C02/C03/C04 | C02/C03: P4 coupon (disjoint mixed-density cells under one body; full tensor incl. off-diagonals vs independent quadrature; parallel-axis recombination) + SI shared-interface control (battery F2) + P3 routes A/B; C04: p7_scaling_law.json (30/30, m∝s³, I∝s⁵ at unchanged density, s∈{0.5,2,10}; exporter scale-path explicitly NOT claimed — U2/B02 scope) |

## First unmet clause at arrival

All three done_when clauses were unmet in this review cycle (independent
review existed only as archived-campaign receipts, never as current-cycle
evidence; U1 evidence was archived-only; no current hash-distinctness
manifest). This attempt supplies all three.
