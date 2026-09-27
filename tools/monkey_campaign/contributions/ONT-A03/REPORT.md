# ONT-A03 REPORT — Approve and implement supported ulna correspondence (attempt 9435c49896af49d18c70a08ce20138d2)

Card **ONT-A03** (planning id A03), attempt `9435c49896af49d18c70a08ce20138d2`,
arrival `arrival-bb1ef1a6a3994ca9bb660ad90af78d6d`.
Criteria sha256 `d15183d955c5d3764ed605e4c265145400806e5fb7e67738cebb3cf569056e7d`.
Scope sha256 `01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6`.
Base revision (attempt checkout `branch-2`, fast-forwarded to the base head)
`2e258b45c9c4e24fa6843a65d9d5324156d10b8d` (branch `astra/gait-capture`).
Verification profile `anatomy` (`visible_static`), `numerical_evidence_required: true`,
`clean_view_required: true`. Preregistration frozen BEFORE any probe run at attempt
commit `582015a5` (blob `1b1ca64a…`); all receipts carry its hash.

**done_when**

> Architect approves mapping/supersession, historical radius preserved, new
> transforms and regressions qualified

**Outcome: all three clauses IMPLEMENTED as one staged candidate and qualified —
probe 75/75 checks PASS (`outcome = STAGED_AND_QUALIFIED`), regression suite
138/138 PASS, canonical camera manifest `structurally_valid: true` (6 rows), and
the closed-form values reproduce the review-accepted I7 receipt 08 to its own
tolerances.** The staged record carries
`status = STAGED_FOR_ARCHITECT_APPROVAL`: per the card completion clause
("Lead-approved exact-head PR merged with full ontology qualification evidence"),
the approval act for this mapping/supersession is the connected lead's merge of
this exact head; this candidate does NOT self-approve.

---

## 1. MAPPING/SUPERSESSION APPROVED-AS-STAGED (clause 1)

`transforms/radius_supersession_record.json` (sha256 `e98c3c77…`) stages the
U-STR candidate — P = `body_origin:ulna` ↔ `elbow_R` (anchor gap 0.0), P_d =
`body_origin:radius` ↔ the derived point 5.1158 mm along the elbow→wrist axis —
WITH the O1-resolved roll (source `site:TRIlat-P5` ↔ the shipped `_band_roll`
extreme vertex; measured residual 0.1535°; the residual SELECTS the pair and is
NOT validation), exactly as frozen in I7 receipt 00 and passed by the authorized
B4 diagnostic (T1–T5 both sides + T6 process, receipt 07).

**Decision basis (recorded, never relabeled):** SOURCE-KINEMATIC CONVENTION
FIDELITY — the measured, B4-passed consistency of the candidate with the source
author's joint-frame convention and the forced first-child closure of the shared
elbow-region joint. R1's verdict sentence is carried VERBATIM into the record
(extracted at run time from `reference/receipts/R1_report.md` §6.1, key phrases
asserted): "**REFUTED as an anatomical claim** … ≈ 0 % (±~1 %) of forearm length
distal to the humeroulnar hinge, far outside the frozen 4–12 % plausibility band."
The source convention is NOT presented as anatomical evidence. The selection rule
is residual-derived; NO moment-arm, utility or performance evidence entered the
selection (T6 ban carried, receipt 07, 0 banned occurrences).

**Approval semantics (frozen in PREREGISTRATION §Approval semantics):** the
staged record states that the lead's merge of this exact head IS the architect
approval act and that a lead CHANGES_REQUIRED supersedes it. Bound carried from
the merged A02 receipt: this implementation does NOT authorize mechanically
qualified grasp (G-chain work remains) and touches no training body.

## 2. HISTORICAL RADIUS PRESERVED (clause 2)

- The BEFORE record is preserved packet-verbatim in the staged record (per side:
  scale `0.22170679566544982`, t/P = `elbow_R`, rotation G, frame basis Bp,
  P_d = `wrist_R`, span `0.06474489854186721` m) and re-asserted live:
  the BEFORE map reproduces every packet fitted global to ≤ 1e-9 m (S13:
  source locals untouched), and the radius distal landmark is unchanged.
- The superseded set is enumerated AS HISTORY in the staged record: radius/radius_l
  `local_to_world` (R, t); the max-world-reconstruction-error record; the
  experiment step-A mirror table; the A4/B4 receipt set. The preservation block
  hash-pins the frozen baseline packet, receipts 00/07/08/10, the USTR receipt,
  and the failed alternatives (U-ANA, H-BODY) by name.
- The extraction provenance chains: `astra/gait-capture @ 2e258b45` → merged
  ONT-A02 (review-accepted PR #181) → forearm-package-20260924 records. All 20
  content files match A02's recorded extraction hashes byte-exact
  (`M0.provenance_chain`, 20/20) and every `reference/` file matches this
  attempt's `EXTRACTION.json` (21/21).
- Nothing was executed against any store: no production source, model store, fit
  or training-body write; all writes are inside this contribution directory.

## 3. NEW TRANSFORMS AND REGRESSIONS QUALIFIED (clause 3)

**Transforms (executed, both sides, closed form re-derived from the pinned
inputs and checked against I7 receipt 08):**

| record | BEFORE (frozen, preserved) | AFTER (staged) |
|---|---|---|
| radius P | `elbow_R` = (−0.11548098385334016, 0.3191090774536133, −0.0060765563324093825) | `ulna.P_d` = (−0.11781299127866669, 0.3145557153217149, −0.006067056594766505) |
| radius P_d | `wrist_R` | unchanged |
| span | 64.74489854186721 mm | **59.62909405176015 mm** |
| uniform scale s | 0.22170679566544982 | **0.20418868001006546** (−7.901478889180636 %) |
| det(full map) = s³ | 0.010897754382730345 | **0.008513242115903161** |
| rigid part G / roll basis Bp | packet values | **unchanged** (max abs diff 2.22e-16 right / 6.66e-16 left) |
| translation t | packet | recomputed (−0.5743881501002028, −0.36085729483653595, −0.23549874330359868) for `radius` |
| 16+16 site globals | A4-verified | recomputed; max displacement **4.950983466166482 mm** (`BICshort-P6`) / **4.948423135921825 mm** (`BIClong_l-P9`); all deltas ≤ 1e-9 of receipt 08 |

**Mechanism EXECUTED as code** (`M3.*`): `JOINT_EPS` parsed from the pinned
`compiler.py` line 47 equals `1e-9`; the `shared_joint_separation` refusal sits
inside the closure block (lines 399–423); executing the first-child closure on
the FROZEN record RAISES the named refusal (gap 5.115804490107064 mm ≫ 1e-9)
and on the STAGED record the shared joint is one point (separation exactly 0.0).

**Property laws re-qualified:** staged P lies ON the elbow→wrist line
(perpendicular ≤ 1e-12 m) at 5.1158 mm; orthonormal ONBs; det(L) = s³; left/right
staged scales equal; fraction law 7.545856…% × 1.0471281884537094 =
7.901478841651782 % (exact-float equality ≤ 1e-9); staged record file equals a
fresh in-memory recompute (drift-free).

**Tendon-coverage effects (receipt 10, ulna-only scenario):** PT/PT_l newly
defined; BRD/BRD_l elbow arms repaired (complete, no unresolved owners); 10
tendons still blocked at the terminal hand (ECRB/ECRL/ECU/FCR/FCU ×2 — of which
the 8 non-ECU are the addendum's "8 (terminal hand)"; ECU ×2 double-blocked,
terminal hand site open); BIClong/BICshort ×2 thorax-blocked (campaign-level
scope). Scenario counts 2 / 4 / 14 (plus-hand = context only, NOT this run).

**Regressions:** `test_ota03_ulna_correspondence.py` — 138/138 PASS covering
identity/extraction/provenance, the definition clause, the staged supersession
clause vs receipt 08, the executed mechanism, coverage effects, historical
preservation, decision-record semantics, receipt self-consistency, canonical
manifest structure, the all-bookmark bounds regression (the profile's own
"clipped/occluded subject fails" falsifier), render determinism, pure-recompute
equality, and clean-pair camera/state sharing.

## 4. VISUAL EVIDENCE (anatomy profile)

`evidence/capture_sheet.png` (1920×1080, sha256 `7ee98625…`), three declared
views, each with a diagnostic + clean pair sharing camera and state binding:

- **V1 whole-creature overview** (target frame, m): target pack mesh
  (18 459 verts / 36 630 tris), frame triad, boxed right forearm region,
  `elbow_R`/`wrist_R`, dotted elbow→wrist axis, and both radius proximal anchors —
  HISTORICAL (`elbow_R`, preserved) and STAGED (`ulna.P_d`, +5.1158 mm).
- **V2 local attachment close-up** (source rest frame, mm): vendor `ulna.stl` at
  the ulna body origin and `radius.stl` at the authored offset (XML scale
  1, 1.2, 1), the 23.0746 mm kinematic offset with axial/lateral/posterior
  component arrows (14.324 / 18.088 / 0.301 mm; 51.63°), frame triad, recorded
  tendon-path waypoints (ECU-P2..P4 on the ulna, BIClong-P9/P11 on the radius)
  and the PT-P2/BRA-P3/BRA-P4 attachment sites.
- **V3 orthogonal side and oblique views** (target frame, m): forearm region
  sub-mesh across four bookmarks (anterior, posterior, lateral oblique, superior)
  with the axis, historical/staged anchors and the span annotation
  "64.7449 mm (historical) → 59.6291 mm (staged)".

Framing is deterministic: cameras come from the PROJECTED BOUNDS of each view's
declared subject point set with the single uniform 8 % margin;
`assert_in_bounds` runs at generation time and the all-bookmark bounds regression
re-checks every declared subject point of every view/bookmark in the committed
manifest. Diagnostic rows declare `occlusion_mode: "mixed"` (mesh depth-tested,
overlays unoccluded = xray semantics); clean rows `depth_tested` with no
layers/labels. **Honesty label (in the manifest render block):** deterministic
CPU numpy z-buffer software raster + matplotlib Agg compose — **NOT native engine
frames**; no GPU, no engine start. The claim subject is anatomy evidence records.

## 5. Reconcile-first: what existed and was reused

| record | where | reuse |
|---|---|---|
| I7 consolidated receipt + B4 ADDENDUM 1 | `reference/USTR_DIAGNOSTIC_RECEIPT.md` | parent outcome record (DR-B decision material) |
| I7 receipts 00/07/08/09/10 | `reference/receipts/` | frozen candidate, gate, before/after map, C1 replacement, coverage |
| R1 / C1 / O1 / B4 receipts | `reference/receipts/` | refutation (verbatim), landmark set, roll sign, known-good records |
| Session-5 baseline snapshot + compiler.py | `reference/baseline_snapshot/` | pinned inputs and the executed closure mechanism |
| ONT-A02 (dependency, merged PR #181) | `tools/monkey_campaign/contributions/ONT-A02` | extraction source of every reference byte (provenance chain asserted) |
| ONT-A01 renderer/camera method (merged PR #176) | via A02's reviewed adaptation | same deterministic CPU z-buffer method, re-frozen for A03's subjects |

The A02 contribution's own extraction record is carried at
`reference/provenance/ONT_A02_EXTRACTION.json` (hash `60241502…`, matching A02's
REPORT evidence index). No source repository was modified; no git write, push or
network call occurred in any probe.

## 6. Commands and observed results

```
cd <attempt checkout>/tools/monkey_campaign/contributions/ONT-A03

PYTHONDONTWRITEBYTECODE=1 python -B _make_extraction.py
  -> wrote 21 entries to reference/EXTRACTION.json               [exit 0]

PYTHONDONTWRITEBYTECODE=1 python -B ota03_ulna_correspondence.py
  -> checks 75/75 PASS  outcome=STAGED_AND_QUALIFIED             [exit 0]
     staged record transforms/radius_supersession_record.json
     sha256 e98c3c772e808831…

PYTHONDONTWRITEBYTECODE=1 python -B ota03_render_views.py
  -> structurally_valid: True views: 6                           [exit 0]

PYTHONDONTWRITEBYTECODE=1 python -B make_qualification_receipt.py
  -> checks {'fail': 0, 'pass': 75, 'total': 75}
     visual_gate.verify: structurally_valid true, view_count 6   [exit 0]

PYTHONDONTWRITEBYTECODE=1 python -B test_ota03_ulna_correspondence.py
  -> 138/138 tests PASS                                          [exit 0]
```

Falsifier bookkeeping (PREREGISTRATION §Falsifier): **F1** (identity) no mismatch —
reference integrity 21/21, provenance chain 20/20, MANIFEST identities reproduced;
**F2** (value) 0 of 75 checks outside tolerance; **F3** (visual) manifest
structurally valid, all-bookmark bounds regression passes, pairs share
camera+state, clean rows carry no diagnostics; **F4** (execution/authority)
staged execution confined to this contribution directory, no production/source/
fit/training write, R1's refutation retained verbatim (not relabeled), no
utility selection, no mechanically-qualified-grasp claim.

## 7. What remains for the reviewer (and what this card does not claim)

1. **Independent review of the exact published head** — reproduce the staged
   recompute, inspect `evidence/capture_sheet.png` pixels against the declared
   subjects, and **fill `evidence.qualification_review`**: the `independent_review`
   entry in `qualification_receipt.json` is explicitly `pending` with a zero
   placeholder (the accepted A01/A02 receipt shape); the reviewer supplies the
   real receipt path + raw sha256 and pins `head_sha` to the reviewed head.
2. The decision presented is bounded: merging this head approves the staged
   mapping/supersession on the kinematic-convention basis with R1's refutation
   retained; it does NOT authorize mechanically qualified grasp, does not touch
   the training body, and does not produce any runtime or human acceptance.
3. Downstream scope stays open: terminal hand tendon sites wait on A04/A05
   (hand evidence); the BIC thorax half is campaign-level scope; grasp
   qualification is G-chain work.

## 8. Evidence index (sha256)

| artifact | sha256 |
|---|---|
| `PREREGISTRATION.md` | `1b1ca64a…` |
| `reference/EXTRACTION.json` | `4fe87ba7…` |
| `transforms/radius_supersession_record.json` | `e98c3c77…` |
| `evidence/state_snapshot.json` | `f9cae65f…` |
| `evidence/numerical_receipt.json` | `6862817b…` |
| `evidence/capture_sheet.png` | `7ee98625…` |
| `evidence/capture_manifest.json` | `d11ac140…` |
| `evidence/capture_context.json` | `c0797687…` |
| `evidence/visual_provenance.json` | `1266921a…` |
| `evidence/qualification_receipt.json` | `27331aad…` |

Key source identities: `chimanoid.xml` `7caa32c6…`, `actual_monkey_fit.json`
`7b5d6345…`, `compiler.py` `8a4ba07c…`, `monkey_birth.bin` `550a5b3e…`,
`monkey_joints.bin` `74b3ab04…`, `ulna.stl` `71026415…`, `radius.stl` `1cfc0056…`,
A02 provenance record `60241502…`.
