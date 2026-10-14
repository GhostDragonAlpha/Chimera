# Rule 0 record — THE FRONT PAGE TELLS THE TRUTH, lane frontpage-status-20260920

Lane: `lane/frontpage-status-20260920` @ `5b2b7f89` (the INTEGRATION PASS 5
receipt commit, the pass-5 push of record; verified by rev-parse at worktree
creation). Master untouched; only this lane branch is pushed. Git trailer on
this lane's commits: `Agent: frontpage`.

## THE THEORY

**STATEMENT** (someone could disagree): the repo's front page (`README.md`) and
the ship-goal status doc (`docs/THE_SHIP_GOAL.md`) can be brought current with
the 2026-09-20 landings such that EVERY rendered claim cites its receipt (a
path under `tools/science_funnel/validation/` on this tree, or a commit sha),
the page's existing structure survives (updates, not redesign), and the open
reds appear as reds — and this can be verified mechanically by re-opening each
cited receipt and finding each claimed number/verdict in it.

**PREDICTIONS** (unmeasured at freeze time):

- P1 (claim-receipt closure): every entry in `receipt.json` `claims[]`
  (claim text -> receipt path + locator) resolves inside its cited receipt:
  the number or verdict the doc renders is present in the receipt's own bytes.
- P2 (voice): the `README.md` diff consists of in-place truth updates plus at
  most ONE appended status subsection; every pre-existing heading survives
  byte-identical; no heading is removed or renamed.
- P3 (honest reds): the rendered docs name, as reds, at minimum: the slice
  boot bar (135.73 s vs the 10 s bar), rear-up static strength NOT COVERED
  (both the k-fill and the measured-arm books), ankle plantar walk coverage
  0.7434x UNDER, the tick-cost cost-gap FIRED (6.7-13.7x the 300 Hz budget
  after every byte-neutral removal), the vanhoof calibration STOP gate FIRED
  (zero records admitted), and the not-yet-merged successor lanes
  (mesh-parse, fk-reduction — both evaluated and NOT merged by pass 5).
- P4 (determinism): no doc build exists for these files (plain markdown
  consumed directly); the claims self-check re-runs with identical verdicts.
- P5 (scope): `git status` on this lane names only `README.md`,
  `docs/THE_SHIP_GOAL.md`, and `tools/science_funnel/validation/frontpage_status_20260920/`.

**FALSIFIERS** (named before any edit; any one firing is recorded, not tuned):

| id | pass condition |
|----|----------------|
| F1_UNVERIFIED_CLAIM | any statement rendered in README.md or THE_SHIP_GOAL.md whose cited receipt does not contain it -> FIRED; the claim is removed or corrected, and every claim appears in `receipt.json` `claims[]` with its receipt path and locator |
| F2_VOICE_BREAK | any pre-existing README heading removed/renamed, or a diff that restructures the page rather than updating it -> FIRED |
| F3_HONEST_REDS | any red named in P3 absent from the rendered docs -> FIRED |
| F4_DETERMINISM | a doc build exists (none is expected), or the self-check does not reproduce its verdicts on re-run -> FIRED |
| F5_SCOPE | any touched file outside README.md, docs/THE_SHIP_GOAL.md, and this lane dir -> FIRED |

## THE BRIEFING CORRECTIONS (measured against this tree BEFORE any edit)

The mission briefing contained three statements this tree does not support.
They are corrected here, before the work, and none of them is rendered:

1. "mesh_parse_20260920/ — 135.7 s -> 2.10 s": NO directory
   `tools/science_funnel/validation/mesh_parse_20260920/` exists on master at
   `5b2b7f89`. The pass-5 receipt
   (`integration_pass5_20260920/receipt.json`, `evaluated_and_NOT_merged`)
   records `lane/mesh-parse-20260920` @ `7d7868d3` as still in flight and
   explicitly NOT merged. The boot bar on master stands RED at 135.73 s vs the
   slice's own 10 s bar (`slice_real_body_20260920/receipt.json`,
   F-SLICE-LAUNCH; record.md Amendment 3; engine parse 237.67 s isolated,
   130-240+ s across boots). The 2.10 s figure appears NOWHERE on this tree.
2. "fk_reduction_20260920/": NO such directory exists on master. The pass-5
   receipt records `lane/fk-reduction-20260920` @ `720364e4` as local-only,
   no origin tip, not landed. The CPU/GPU split can only be cited as far as
   the LANDED tick-cost receipt does (the CPU attribution + the named,
   unimplemented successors).
3. "walking covered every joint": the landed receipts say walking demand is
   COVERED at knee (1.5975x) and MTP (1.6495x) and UNDER at the ankle
   (plantar 0.7434x, dorsal 0.5123x — k-fill F1, fired as pre-registered),
   with the shortfall adjudicated as demand-side mass context
   (`ankle_adjudication_20260920`, verdict B), never tuned.

## RUN PLAN

Prereg (this file + receipt.json, committed BEFORE any doc edit) -> edit
README.md and docs/THE_SHIP_GOAL.md in the existing voice -> mechanical
self-check: re-open every cited receipt, locate every claimed number/verdict
(script lives OUTSIDE the repo, in the lane scratch) -> append the claims
table + per-claim verdicts to receipt.json -> commit milestones -> push ONLY
`lane/frontpage-status-20260920`.

Receipt: `tools/science_funnel/validation/frontpage_status_20260920/receipt.json`.

Agent: frontpage
