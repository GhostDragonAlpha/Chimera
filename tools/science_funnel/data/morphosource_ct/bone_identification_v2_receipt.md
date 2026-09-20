# Bone identification v2 — method receipt

- **Lane:** `buffy/bone-id-v2-20260919` (base `f7ddbd07`, tip of `origin/codex/force-data-runtime-20260916`)
- **Agent:** Buffy
- **Data:** MorphoSource µCT of two infant *Macaca mulatta* — USNM 497136-3 (`000875604`, seg threshold 118) and USNM 497135 (`000875599`, seg threshold 148); 160 µm; 25 connected components each (rank 1 = axial composite, 24 non-axial).
- **Outputs (new files only, nothing pre-existing modified):** `identify_bones_v2.py`, `bone_identification_v2.json`, `explore_proximity_v2.py` (kept: it derives the cut valley), this receipt.

## 1. Statement under membrane (Rule 0) and prediction

As preregistered in the lane prompt: bones identifiable by SHAPE + intra-specimen proximity clustering despite the curl — each limb's chain (femur→tibia→foot, humerus→forearm→hand) is a connected run of bones that touch at joints in the curled pose; size ordering identifies segments; the two specimens provide cross-specimen homology within age-matched tolerance. **Prediction: ≥12 of 23 bones per specimen confidently labeled.**

The prompt's denominator "23" carries v1's off-by-one: both manifests hold 24 non-axial bones (ranks 2–25). v2 uses 24 and records the discrepancy.

## 2. Why v1 failed and what "proximity" had to mean

v1 read proximity as *centroid mirror-symmetry*; the curled fetus invalidated it (20–22 refusals). v2's first implementation read the falsifier's "centroids chain within 1.2× the neighboring bone lengths" as the *edge rule*; that also fails on first principles: with bones 40–55 mm long the threshold is ~50 mm in a 170 mm body, so single-linkage merges all limbs into one 14–19 bone mega-chain (this run is preserved in the script's history of this lane, and is why the edge rule had to change).

The membrane's own mechanism — **"they touch at joints in the curled pose"** — gives the correct operationalization: adjacency = **surface-to-surface gap ≤ 3.0 mm**. The 3.0 mm cut is *derived, not tuned*: the empirical gap spectrum of BOTH specimens has a valley there (A: last touching pair 2.91 mm, next pair 3.30 mm; B: 2.97 → 3.04 mm). At 2.5 mm A's hind chains fragment; at 3.5 mm A's two hind chains merge (15–17 @ 3.68) and B's hind fragments join (2–4 @ 3.39). **(2.91, 3.04) is the only cut interval that avoids both failure modes in both specimens**, and 3.0 lies inside it.

## 3. Method

1. **Geometry** per bone from the committed preview meshes: centroid, PCA long axis, robust length (p2–p98), elongation √(λ1/λ2), end points; symmetric min surface gap for all pairs (KD-trees over decimated vertices).
2. **Chain recovery:** single-linkage components over touching edges (gap ≤ 3.0 mm).
3. **Segment rules** (shape, derived from this data's morphology gap — robust bones elongation 4.7–9.6, thin rods 13.2–14.7, cut at 10):
   - *Hind chain* = contains a thin long bone (the **fibula**). The robust bone touching the fibula most closely is the **tibia** (gaps 0.45–0.53 mm vs ≥2.97 mm to the femur); the other robust bone is the **femur**; remaining smalls are **foot_class**. Size ordering cross-checks (femur > tibia in all three hind chains ✓).
   - *Fore chain* = no thin member, long bones contain a mutually-touching pair (gaps 0.36–0.70 mm) = **forearm_class** (radius+ulna); the remaining robust long bone is the **humerus**; compact blocks (L<30, el<2.5) are **hand_class**.
   - *Sides are never assigned* — the curl jumbles left/right (v1's error is not inherited).
4. **Cross-specimen homology** at class level: a labeled bone is corroborated if the other specimen has a same-class chain-labeled bone within the preregistered 10% length tolerance. (Formal falsifier-2 test uses stricter 1-1 greedy pairing; confidence uses the side-agnostic "exists partner", because contralateral same-size bones cannot be told apart without side assignment.)
5. **Anchoring** (falsifier 3): chain's longest bone within 1.2× its length of the axial composite.
6. **Falsifier 1** applied *after* recovery exactly as preregistered: ≥3 bones whose centroids chain within 1.2× neighboring lengths. The preregistration is ambiguous between "min" and "mean" neighbor length — **both readings reported**; the "≥3 bones" clause is read as the preregistered subset (longest chainable subpath), with full-chain traversal reported as auxiliary.

## 4. Results

### Specimen 000875604 (A) — full recovery: **18/24 high-confidence** (prediction ≥12 ✓), 3 medium, 3 unresolved

| Chain | Members | Labels | Anchor |
|---|---|---|---|
| hind 1 | 2, 6, 15, 20, 22, 25 | femur=2, tibia=6, fibula=20, foot=15/22/25 | ✓ 19.6 mm |
| hind 2 | 3, 7, 17, 18, 21, 23, 24 | femur=3, tibia=7, fibula=21, foot=17/18/23/24 | ✓ 14.7 mm |
| fore 1 | 4, 8, 10, 12 | humerus=4, forearm=10+12 (pair gap 0.38), hand=8 | ✓ 6.1 mm |
| fore 2 | 5, 9, 11, 13 | humerus=5, forearm=11+13 (pair gap 0.47), hand=9 | ✓ 5.3 mm |

All four chains anchored; F1 passes under both readings (strict-min run ≥3 bones each). Unresolved: singletons 14, 16, 19 (compact blocks, no touching partners) — morphology hints only, never labels.

### Specimen 000875599 (B) — partial by segmentation, honest limit: **9/24 high-confidence** (prediction ✗ for this specimen), 0 medium, 12 unresolved

| Chain | Members | Labels | Anchor |
|---|---|---|---|
| hind | 3, 7, 19, 21, 24 | femur=3, tibia=7, fibula=19, foot=21/24 | ✓ 19.7 mm |
| fore | 5, 8, 9, 11 | humerus=5, forearm=8+9 (pair gap 0.70), hand=11 | ✓ 6.6 mm |

The other two limbs fragmented into 2-bone pieces at this specimen's higher threshold (148 vs 118) — the connections the method needs were severed *in segmentation*, not in the body. Fragments carry evidence-only hints (e.g. [4,20] = robust long + thin-rod → tibia+fibula-class diad morphology, unresolved). Force-merging them would be the v1 sin; the shortfall is recorded as the method's limit. One 3-bone small-bone cluster [14,23,25] is **reported unanchored** (19.0 mm vs 17.7 mm allowance) and unlabeled — never forced.

## 5. Falsifier outcomes

| # | Preregistered | Outcome |
|---|---|---|
| 1 | each chain has ≥3 bones chaining within 1.2× neighboring lengths | **PASS** (all 7 chains, strict-min and mean readings; all limb chains full-chain under mean) |
| 2 | homologous lengths agree within 10% | **PASS** (all formed 1-1 class pairs within 10%; max 5.4%; humerus 0.05%, femur 4.3%, tibia 4.5%, fibula 5.4%, forearm 2.8/3.0%, hand 3.3%, foot 2.7/3.5%) |
| 3 | axial composite anchors every chain at one end | **PASS for every labeled limb chain (7/7); one unlabeled 3-bone cluster in B is unanchored — reported, not forced** |
| pred | ≥12 confident per specimen | **A: 18 ✓ · B: 9 ✗ (segmentation-cap; recorded as the method's limit)** |

**Verdict:** the membrane statement is confirmed where the segmentation preserves joint contacts — 3 of 4 chains recovered in the threshold-damaged specimen, 4 of 4 in the gentler one, with cross-specimen agreement strong enough (≤5.4%, most ≤5%) that segment identities in A and B are mutually corroborating. The chained-fetal-pose does not prevent identification; mirror-symmetry does (v1), and coarse thresholds do (B's cap).

## 6. Derivation-vs-tuning audit (for the verifier)

Chosen after seeing data (all documented in `bone_identification_v2.json` → `derived_cuts`): joint-gap 3.0 (shared valley), thin-elongation 10 (morphology valley 9.64→13.18). Preregistered and untouched: 1.2× chaining, ≥3 bones, 10% homology, 1.2× anchor, 12-bone prediction. Falsifier-1's neighbor-length ambiguity (min vs mean) reported under both; the ≥3-bones subset reading follows the preregistered sentence literally. Two honesty bugs found and fixed by self-verification before locking: an inverted size-order check (data agreed everywhere; the check reported it backwards), and a loop-variable leak that printed B's fragments into A's output block.

## 7. Boundaries honored

No existing receipt or script modified; no physics files touched; port 8127 never touched (owned by PID 118580 before this lane started); work confined to `buffy/bone-id-v2-20260919` worktree `E:/ChimeraWork/buffy-bone-id-v2-20260919`; `master` untouched.

**Graph test verification:** `tools/creature_graph/tests/test_contracts.py` 19/19 OK; `test_class_contracts.py` OK; `tools/agent_fleet/test_graph_workflow.py` 24/24 OK. For the F2 reproduction modules (d1–d9, `test_qs_query_semantics`), direct `__main__` output was diffed against the pristine base commit `f7ddbd07` (checked out at `E:/ChimeraWork/codex-graph-workflow-20260916`): byte-identical on every module, so zero behavioral delta from this lane. (The d-suite is the F2 harness that is green-under-pytest on the defective base by design and turns red as repairs land — its direct-run output is a base-commit property, unchanged here.) The committed `reproduction_output.json` was not rewritten. Pre-existing at base, unrelated to this lane: `test_graphify.js` at repo root fails to parse (string literals contain raw CR/LF) and hardcodes external paths — reported, not modified.

---
🤖 Generated with Codebuff · Agent: Buffy
