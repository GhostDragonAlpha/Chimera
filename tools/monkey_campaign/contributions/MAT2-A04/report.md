# MAT2-A04 — hand assembly identity and palm orientation: reconciliation report

Attempt `31c8beb654664b6d8e28280e38f7c0d6`, agent `arrival-73c48ff5c55146f1ad7ff5231213ec6c`,
card criteria `b6a4bb30f1bfe207c76969f2eebfd736d33360546d1d0522bae8e29860a1bf3d`,
scope `cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`,
candidate base `8ec90f13` (astra/gait-capture tip), preregistration frozen at
commit `d18b12bc` **before** any re-verification run of this attempt. CPU-only
throughout; python `-B`; no GPU context.

## DONE_WHEN (the only clause qualified)

"Source and target assembly correspondence is evidenced, including palm sign and
geometry coverage" — calculation contracts C01, C16 (identity leg); verification
profile `anatomy` (kind `visible_static`, numerical evidence required).
Dependency `P02`: DONE (MAT2-P02 merged as PR #196, in this base).

## Reconcile verdict: clause already carried by the merged ONT-A04 winner

The merged **ONT-A04** work — PR #177 head `020c0a5c216a4182d0bed9c4ade59cb0beb585ad`,
merged as `56d0116a` into `astra/gait-capture`, lead-ACCEPTED at independent review
`6e27829fa06c44cc92907bb5fa0273c8` with `done_when_verified: true` and
`profile_verified: true` — qualifies the *identical* clause under the *identical*
definition (`57ded6eb…`), calculation contracts (`C01`, `C16`) and profile
(`anatomy`/`visible_static`). Only era bookkeeping changed (scope
`01ea5cdd…` → `cb5475f8…`, card criteria `bf8583ae…` → `b6a4bb30…`). Per the
dispatch and the card plan ("reconcile existing assignment and gate before
dispatch"; "reuse verified work; do not repeat completed implementation"), this
attempt **reuses** that evidence at hash-verified identity and adds only:

1. the scoped re-verification demanded by the new card era
   (`validation_state: NOT_REVERIFIED_IN_THIS_REVIEW` → re-verified here);
2. the campaign-schema deliverables for this card: `card_task.json`
   (planning CONTRACT envelope, `task_id: "A04"`, current scope, C01/C16),
   `qualification_receipt.json` (`chimera.qualification_receipt.v1`, kind
   `reconcile`), and this report + `reconciliation.json` clause map;
3. the recorded **operator decision request** for the one genuinely missing
   decision (target palm face A/B) — recorded, never answered.

## Clause-to-evidence map (all pins re-asserted at this base)

| clause part | verdict | evidence (merged, byte-pinned) |
|---|---|---|
| source↔target correspondence evidenced | satisfied | C01/C2 frame chain (hand_r origin pin, identity quats, <1e-12 m round-trip, det +1, extents/rays reproduced); C6 inventory (27 bone IDs + 5 port IDs + band + 2 anchors, owner map); capture renders source assembly and target band separately per view (`878eb3de…` / `4447058a…`) |
| including palm sign | source CLOSED; target UNRESOLVED with named operator gate | source: independent pisiform-signed palm-plate re-derivation, `n_palm = (+0.128427, −0.168691, −0.977266)` exact to 1e-9, 5/5 split, exact z-mirror; target: ±T_R A/B instrument in-tree (`reference/LABELING_CARD.md`), human verdict not recorded anywhere → decision request below |
| geometry coverage | satisfied with explicit gaps | 13 carpals/metacarpals region-covered (homology only, scale UNDECIDED); **14 phalanges NOT covered** (no digit structure; grooves refuted by C2); H-LEN/H-ASP UNRESOLVED, H-BODY REJECTED circular; **no scale promoted** |

## Verification executed at this base (exact commands, CPU-only)

Scratch copy `rerun/ONT-A04/` inside the attempt workspace; the in-tree merged
ONT-A04 tree was **not modified**.

```
# P1  7/7 accepted-head pin assertions                    -> 7/7 PASS
python -B a04_correspondence_probe.py                     # P2 exit 0; all_green=True
                                                          #     deviations=2 (both merged-recorded)
python -B -m unittest test_ont_a04                        # P3 Ran 19 tests ... OK
python -B capture_build.py                                # P4 878eb3de... 700x3628, 6 views,
                                                          #     structurally_valid=True fired=0
python -B verification/revalidate_manifest.py ...         # P5 structurally_valid=True vs
                                                          #     current-era envelope task_id 'A04'
```

Results (receipts under `verification/`):

- **P1**: in-tree ONT-A04 files byte-match the accepted head: probe
  `8e36aa2f…`, PNG `878eb3de…`, manifest `4447058a…`, capture receipt
  `74731438…`, numerical leg `e3864b16…`, state snapshot `33d3219c…`,
  qualification receipt `726efaf8…`. **7/7 PASS.**
- **P2**: `all_green=True`, exit 0, exactly the two merged-record FIRED
  deviations (C4 s2 site-metric convention within the 3.5 mm anchor class; C5
  far-end 18.0393 vs printed 18.1 mm). Regenerated `numerical_receipt.json` /
  `state_snapshot.json` are **byte-identical** on disk to `e3864b16…`/`33d3219c…`
  (the probe console prints LF-canonical hashes `1208bfbe…`/`acf4f53d…` of the
  same bytes — Windows CRLF write translation, deterministic, per the merged
  review record; on-disk hashes are the governing pins).
- **P3**: `Ran 19 tests in 0.167s — OK` (includes the failing-first
  `TestCaptureTruth` regressions for review `8837d083`'s three findings).
- **P4**: capture regenerates **byte-identical** (`878eb3de…` PNG, `4447058a…`
  manifest), sheet 700×3628, 6 views, `structurally_valid=True`, `fired=0`.
- **P5**: `visual_capture.validate_manifest` returns `structurally_valid=True`
  binding the merged manifest to context subject `33d3219c…`, capture
  `878eb3de…`, `tick_interval [0,0]`, run `ont-a04-anatomy-20260926-d9e5561a`,
  under THIS card's profile from `card_task.json` (`task_id "A04"`, scope
  `cb5475f8…`). Validator materialized read-only from this base commit.
- **P6**: no human A/B verdict exists anywhere — the only occurrences of the
  answer strings are the UNFILLED instrument template (`DECISION_CARD.md` answer
  block: no pick, no reader, no date) and the in-tree `LABELING_CARD.md`; the
  gate artifact's own `VERIFICATION.txt` records **34/34 PASS** for instrument
  *provenance* (panel rects re-derived from evidence bytes), not an answer.

No prediction missed; falsifiers G-A…G-F did not fire.

## DECISION REQUEST (recorded, not decided)

**To:** operator (human terminal only) via the Execution Sergeant.
**Question (verbatim from the instrument):** "Which lettered face is the PALM
(ventral) — A or B?" (A = +T_R-side broad face, B = −T_R-side;
T_R = (0.890060, −0.455843, 0.000951)).
**Instrument:** merged `tools/monkey_campaign/contributions/ONT-A04/reference/LABELING_CARD.md`;
prepared, hash-verified operator artifact
`E:/ChimeraWork/monkey-coordination/review-workspaces/labeling_gate_ER/gate_artifact/DECISION_PANEL.png`
(`DECISION_PANEL.png` `33b88a30…`, `DECISION_CARD.md` `c4a36f28…`, 34/34
provenance checks PASS).
**Lawful answers:** "A is the palm" / "B is the palm" / "CANNOT DECIDE (F-R1a)"
(the last refutes the visibility assumption and is recorded, not retried).
**This attempt records the request and NO answer** — a worker or model answer is
another claim, not the verdict. Non-blocking for this reconciliation; the verdict
remains a named open gate for downstream consumers of the target palm sign.

## Honest boundaries / remaining gates (named, not claimed)

- Target palm sign verdict — open (decision request above).
- Same-assembly scale UNDECIDED (H-LEN/H-ASP unresolved, H-BODY circular);
  no scale number promoted; "orientation alone does not set scale" enforced.
- 14 phalanges + thumb distal ray have no target geometry coverage — owner A05.
- C16 reach/ROM leg — downstream grasp-skill scope, not claimed here.
- No runtime/native claim — visible_static offline profile; runtime render and
  training bodies remain P02-kept-separate lineages.
- Independent review of this reconciliation candidate — pending; `head_sha` in
  the in-tree receipt is null until set at ACCEPTED.
- Left STL identity untestable on disk (vendor carries no `_l` files) —
  preserved limitation of the source receipt.

## Inputs (read-only; all writes inside this attempt workspace)

- Merged ONT-A04 tree at base `8ec90f13` (blob-verified against accepted head pins).
- Vendor STLs `E:/PythonChimera/vendor/myo_sim/meshes/<bone>.stl` and
  `E:/PythonChimera/Saved/meshes/monkey_birth.bin` / `monkey_joints.bin` — consumed
  read-only by the merged probe/capture (hash-pinned inside the merged evidence).
- Campaign authority `E:/PythonChimera/tools/monkey_campaign/APPROVED_SCOPE.json`
  `fe74180d…` (scope `cb5475f8…`, 2026-09-27, 95 tasks).
- CPU-only: stdlib + numpy + matplotlib Agg before pyplot import; no
  GPU/OpenGL/Vulkan/CUDA at any step.
