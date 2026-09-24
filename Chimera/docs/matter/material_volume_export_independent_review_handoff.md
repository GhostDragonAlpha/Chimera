# Independent review + multi-cell coupon — dispatch handoff

**Status: subagent deployment unavailable in the authoring session.** The
authoring session has no delegation tool; per coordination rules no sequential
work is relabeled as agents and **no independent review is claimed here**.
Dispatch is owned by the delegation-enabled GLM coordinator. This document is
the complete dispatch package: bounded assignments, isolation rules, and the
completion-receipt skeleton to fill at handoff.

**Audit target revision (frozen):** `1af0bbde` =
`1af0bbdee68d6ddfdd02bf9bd948f7b22f914d56` (material-volume-export lane).
The later reconciliation (verification receipt, commits `3db8bc4e`, merged
`eae0870a`) is **evidence only**: it MUST NOT substitute its revision for the
audit target.

**Ground rules (all assignments).**

- One isolated worktree per assignment, on a dedicated branch — never the
  shared working copy. The shared branch moves concurrently (other lane's
  commits land there).
- Freeze-before-execution: fixtures, expectations, tolerances, and falsifiers
  are frozen and committed **before** any exporter execution. Nothing frozen is
  altered afterward; corrections get ledger entries (C-n), never silent edits.
- Hash rule (consumption contract §6): label raw-file SHA-256, Git blob
  identity, and canonical-content SHA-256 **separately**; specify
  canonicalization exactly; newline normalization only for declared text
  artifacts; a canonical-content match can never satisfy a raw-byte equality
  claim.
- Scope: do **not** expand into the remaining coverage gaps (U2–U10) without a
  finding that makes a specific gap necessary.
- Non-claims preserved in every output: no runtime wiring, no constitutive
  laws, no inferred anatomy, no mechanical-readiness or dynamics-readiness
  claim.

## Assignment 1 — independent reviewer (audit of `1af0bbde`)

Provenance requirement: a reviewer with independent provenance (different
author/tooling from the material compiler/export lane). The known residual
risk is **correlated authorial error** — the exporter and its oracles share an
author — and adjudicating it is the point of this assignment.

1. Reproduce the exact revision `1af0bbde` in the isolated worktree and run
   the full battery; reconcile against the frozen inventory: **59 leaf +
   7 verification = 66 unique test identities** (17/21/8/5/8/7 by module).
   The verification receipt is admissible as evidence only.
2. Audit the two frozen preregistrations
   (`material_volume_export_proof_prereg_shared_interface.md`,
   `material_volume_export_proof_prereg_frame_composition.md`) against their
   fixtures, rational expectations, frozen tolerances (TOL = 1e-12,
   T_PROTECTED = 0.002), and falsifiers F1–F7: confirm no fixture,
   expectation, tolerance, or acceptance criterion changed after freeze, and
   adjudicate corrections C-1/C-2/C-3 against the frozen criteria. C-0, C-5,
   C-6 and fired falsifier **V3-F** are verify-not-erase ledger items; V3-F
   remains fired — remediation does not erase it.
3. Adjudicate **mathematical independence beyond import separation** of H
   (hand rationals), Q (Hammer–Stroud 4-point degree-3 tet quadrature), and
   R2 (congruence): re-derive the SI/FC analytic expectations from scratch
   and compare with the frozen tables; check fixture semantics (especially the
   proposals→regions→materials mapping) independently.
4. Treat every U1–U10 row of the receipt's untested-assertion inventory as
   untested unless separately evidenced.
5. Return findings plus a reproducible receipt: commands run, reviewed
   revisions, and per-artifact identities labeled per the hash rule.

## Assignment 2 — multi-cell coupon author (targets U1)

Goal: a preregistered export proof for a body owning **multiple cells**,
executed with the same freeze discipline as the SI/FC coupons.

1. Preregister (commit before execution) a body containing **≥2
   non-overlapping cells** with known densities and distinct materials (so
   mixed-material provenance under aggregation is exercised), placed at
   **nontrivial offsets** — choose vertices/offsets so the body COM is off the
   frame origin and the full inertia tensor about COM carries protected,
   non-negligible off-diagonal terms.
2. Independently derive mass, COM, and the **full** inertia tensor about COM:
   a hand/rational derivation plus at least one algebraically independent
   numeric check. Do not reuse the exporter's moment path or the existing
   proof oracles' code.
3. Verify **body aggregation** (per-cell contributions combine into the body
   record) and **total recombination** (body totals recombine from per-cell
   contributions) with **off-diagonal terms preserved** (CON-9). Any
   cross-body aggregate check must obey CON-16 / D3: read-only, explicit
   frames, disjoint cell ownership — no body collapse, no joint inference, no
   runtime regrouping.
4. Freeze fixture, expectations, tolerances, and falsifiers in the
   preregistration before exporter execution. Record corrections in a ledger;
   never edit frozen values.
5. Deliverables: preregistration doc, fixture files, proof test module
   (planned naming prefix `tools/material_volume_multi_cell_*` — not present
   at the pinned revisions), and a results table with falsifier
   dispositions. U1 leaves the untested inventory only on passing evidence.

## Assignment 3 — reviewer check of the coupon (after Assignment 2 lands)

The Assignment 1 reviewer, in its own isolated worktree, checks the coupon
addition **separately** from the main audit: the preregistration commit
precedes the proof code and any exporter execution; frozen values are
unchanged; expectations are independently re-derived; off-diagonal terms are
preserved; and per-cell `cell_provenance` (mixed-material provenance) travels
intact through aggregation.

## Completion receipt (skeleton — fill at handoff)

| field | value |
|---|---|
| actual agent identities | **pending dispatch** — must name the real agents and their provenance; never the authoring session |
| reviewed revisions | pending — must include the exact audit target `1af0bbde` and the coupon's landing revision |
| independent findings | pending — independent verification remains OPEN until returned |
| multi-cell results | pending — U1 disposition: evidenced-closed or finding raised |
| approved static contract | D1–D5 as recorded in `rigid_body_mass_export_consumption_contract_v1_proposal.md` §5 (static inspection and validation only) |
| remaining untested assertions | U1–U10 minus those closed with evidence |

No runtime wiring is performed or proposed, and no mechanical-readiness or
dynamics-readiness claim is made or implied by this handoff.
