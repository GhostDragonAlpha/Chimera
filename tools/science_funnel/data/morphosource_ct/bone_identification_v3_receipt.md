# Bone identification v3 — cross-specimen homolog transfer receipt

- **Lane:** `buffy/bone-id-transfer-20260919` (base `01a92b23`, tip of `buffy/bone-id-v2-20260919`)
- **Agent:** Buffy
- **Data:** the v2 membrane (`bone_identification_v2.json`) + the committed preview meshes of both infant *Macaca mulatta* — A = `000875604` (seg threshold 118), B = `000875599` (seg threshold 148).
- **Outputs (new files only, nothing pre-existing modified):** `transfer_labels_v3.py`, `bone_identification_v3.json`, this receipt.

## 1. Statement under membrane (Rule 0) and prediction

As preregistered in the lane prompt: **A's labels transfer to B by homology** — for every B bone without a confident label, a candidate A homolog exists (same chain kind at the same chain position, max-extent within 10%) and the transfer is unique. **Prediction: B reaches ≥14/24 confident** (its 2 intact chains + the fragmented bones resolved by homolog matching).

## 2. Method

1. **Transfer unit** = one B bone. Fragmented bones transfer individually. B's 9 v2-confident bones (2 intact chains) are **retained, not transfer targets**; the v2-unlabeled 3-bone cluster [14, 23, 25] is **excluded from individual transfer** and routed through falsifier 2 (below).
2. **Metric:** max extent = span of vertex projections on the PCA long axis between the 1st and 99th percentiles, **uncapped**. Audited before use: p1–p99 inflates v2's p2–p98 robust lengths by ≤ 3.4% on every bone of both specimens — there is no tail pathology, and an earlier draft's 4 mm "hair" cap (which truncated real long-bone extents to 4.0 mm and produced nonsense) was found, diagnosed as a bug, and removed. The tolerance lives on max extent as the mission specifies; v2's p2–p98 lengths remain the recorded chain/homology metric, unchanged.
3. **A class envelopes:** [min, max] max-extent over A's 21 confident donors, per class (femur [46.41, 46.44], tibia [44.62, 44.69], fibula [38.24, 38.37], humerus [41.74, 43.14], forearm_class [40.87, 44.28], hand_class [25.62, 26.00], foot_class [9.17, 14.51] mm).
4. **Chain kind / position gate (B-side evidence only, never the extent match — that would be circular), kind-relative because chain positions are per-kind:** thin rod (el > 10, v2's valley-derived cut) ⇒ hind position 2 (fibula); robust long (L ≥ 30, el ≤ 10) ⇒ positions 0–1 of hind if its own component contains a thin member, else hind+fore; compact block (L < 30, el < 2.5) ⇒ the distal element (hind position 3 foot **or** fore position 2 hand); irregular ⇒ all slots eligible.
5. **Candidate classes** = A classes whose (kind, position) is eligible **and** whose envelope lies within 10% of the bone's max extent (miss measured against the nearer envelope edge). **Exactly one ⇒ transfer; two or more ⇒ ambiguous, never assigned; zero ⇒ unassigned, recorded.** All transfers evaluated at B's threshold 148.
6. **Post-assignment consistency:** transferred labels in one component must occupy distinct (kind, position) slots — no conflicts occurred.
7. **3-bone cluster (falsifier 2):** anchor = longest member by max extent; anchored iff its axial-composite distance ≤ 1.5× that extent; a class-hint may then be issued only if one A envelope covers **every** member within 10% — a hint is never a label and never counted confident.
8. **Sides are never assigned** (falsifier 3; the curl jumbles them — v1's error is not inherited).

## 3. Results — B (000875599): **14/24 confident** (9 retained + 5 transferred), prediction ≥14 ✓

| B rank | max extent | verdict | class | envelope miss | position evidence |
|---|---|---|---|---|---|
| 10 | 24.54 | **transferred** | hand_class | 4.2% | compact block ⇒ distal |
| 12 | 37.31 | **transferred** | forearm_class | 8.7% | robust long ⇒ pos 0–1 |
| 16 | 14.87 | **transferred** | foot_class | 2.5% | compact block ⇒ hind distal (via thin partner 2) |
| 17 | 14.94 | **transferred** | foot_class | 3.0% | compact block singleton ⇒ hind distal |
| 20 | 40.38 | **transferred** | fibula | 5.2% | thin rod ⇒ hind position 2 |
| 2 | 45.21 | **ambiguous — refused** | femur/forearm/humerus/tibia (1.2–4.8%) | — | robust long, kind undetermined |
| 6 | 40.98 | **ambiguous — refused** | forearm(0.0%)/humerus/tibia | — | robust long, kind undetermined |
| 4 | 55.69 | unassigned | — | 19.9% | (likely threshold-fused with a pelvic/shoulder element; not repaired) |
| 13 | 17.88 | unassigned | — | 23.2% | compact singleton, no envelope ≤10% |
| 15 | 30.55 | unassigned | — | 17.5% | irregular |
| 18 | 20.44 | unassigned | — | 20.2% | compact (oversized), no envelope ≤10% |
| 22 | 21.79 | unassigned | — | 14.9% | irregular |

The two refusals are exactly the ambiguous cases: **2** sits between femur/tibia (hind proximal) and humerus/forearm (fore) — without an intact chain, kind is structurally undecidable; **6** is a 40.98 mm robust bone that matches forearm_class to 0.0% but equally matches humerus at 1.8%. Per falsifier 1, reported ambiguous, never assigned.

**The fibula transfer (rank 20) shows the position gate doing real work:** on length alone B-20 is within 10% of forearm_class (1.2%), femur, humerus, and tibia; its thin-rod morphology (el 14.58, v2's valley) makes it hind position 2, where the only eligible class is fibula (miss 5.2%, nearest donor A-21). Without the gate, this would have been a 5-way ambiguity.

**The 3-bone cluster [14, 23, 25] stays unlabeled — refused at the hint stage, honestly:** under the mission's 1.5× rule it now **anchors** (anchor 14, extent 16.27 mm, allowance 24.40 mm, axial distance 19.02 mm; it also passes an auxiliary 1.2×-of-max-extent reading, 19.02 ≤ 19.52 — v2's unanchored verdict used a *different* allowance, 1.2× the chain's longest *p2–p98 length*, 17.7 mm). But anchoring only opens the hint door, and **no class-hint may be issued**: no A envelope covers all three members within 10% — the worst member misses are foot_class 12.1% (member 14, 16.27 mm, above the 14.51 mm ceiling) and hand_class 56.8%. Anchored but unlabelable ⇒ stays unlabeled, uncounted, exactly as the falsifier prescribes.

**A (000875604) is carried forward byte-identical** — asserted in the script on a canonical re-dump against the v2 JSON, and re-verified from the written file: 18 high + 3 medium = 21/24, four chains, unchanged.

## 4. Falsifier outcomes

| # | Preregistered | Outcome |
|---|---|---|
| 1 | every transferred label ≤10% AND kind/position matches the A homolog; two classes within tolerance ⇒ ambiguous, never assigned | **PASS** — 5/5 transfers within 10% (4.2–8.7%) at matching (kind, position); 2 ambiguous bones refused, 5 with no candidate recorded unassigned; no cluster position conflicts |
| 2 | cluster hint only if anchored within 1.5× the anchor bone's extent | **EXERCISED, REFUSED** — anchored (19.02 ≤ 24.40 mm) but no envelope covers all members ⇒ stays unlabeled; a hint is not an assignment |
| 3 | sides never assigned | **PASS** — 0 side assignments anywhere in the output |
| pred | B ≥14/24 | **✓ 14/24 exactly** (9 retained + 5 transferred); A carried at 21/24 |

**Verdict:** the statement holds where the evidence is structurally decidable. Every B bone that received a label has a unique, kind/position-consistent A homolog within 10% on max extent; every case where the mission forbids assignment (ambiguity, tolerance miss, hint-without-coverage) is reported as a refusal with numbers, not smoothed over. B's segmentation damage (threshold 148) is now *bounded*: its 10 unresolved bones are individually explained (2 kind-ambiguous, 5 outside tolerance, 3 hint-refused), not merely missing.

## 5. Honesty notes (for the verifier)

- The 4 mm max-extent cap in the first draft was **my bug** (an invented "segmentation hair" concern, applied to all bones): it truncated a 46.4 mm femur to 4.0 mm and collapsed the whole decision into cap-equivalence. Diagnosed by inspecting raw spans (p1–p99 ≤ 1.034 × p2–p98 everywhere), fixed, and the audit recorded in the script docstring and JSON.
- The 3-bone cluster is excluded from individual transfer **by design** (falsifier 2 gives it an exclusive route), not by outcome — written before running.
- Position evidence comes only from v2's morphology rules; the extent match never feeds back into eligibility (circularity guard, asserted in `transfer_rules`).
- foot_class transfers (16, 17) are class assignments, not 1-1 pairings — B's tarsals fragmented into more pieces than A's, so B legitimately carries more foot_class bones (4) than either A hindlimb position count; recorded in `limits`.
- Ambiguity is evaluated within the kind/position-eligible set. Rank 6 matches forearm_class at 0.0% — a pure length coincidence across kinds that the structural gate exists to refuse.

## 6. Verification and boundaries

- **Graph tests green:** `tools/creature_graph/tests/test_contracts.py` + `test_class_contracts.py` — 23 passed (27 subtests); `tools/agent_fleet/test_graph_workflow.py` — 24 passed. Run in this worktree.
- `bone_identification_v3.json` round-trips (`json.loads`); specimen A asserted byte-identical to v2 (canonical dumps); every transferred label re-read from the written file and cross-checked against its provenance block.
- All work confined to `tools/science_funnel/data/morphosource_ct/` (3 new files) in worktree `E:\buffy-transfer`, branch `buffy/bone-id-transfer-20260919`; nothing pre-existing modified; no ports touched; push limited to this lane.

---
🤖 Generated with Codebuff · Agent: Buffy
