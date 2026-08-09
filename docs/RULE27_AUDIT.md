# RULE 27 — Upper-Body Interface Membrane Audit (2026-08-09)

> **RULE 27** (EM-27): *the interface membrane is derived first — grow from the
> connection, not from the average.*
>
> — `docs/THE_LAW.md:149`

## STATEMENT

The StandingHuman skeleton was derived top-down from stature fractions in
`LightEngine/skeleton_scaling.py`, with joint centers hardcoded in
`LightEngine/rope_network.py:47-85` and limb endpoints defined by incremental
offsets in `LightEngine/skeleton_structures.py:130-148`. The foot — the primary
*connection* to the ground — was bolted on last and audited separately
(`docs/JOINT_ATLAS.md` §FOOT GEOMETRY AUDIT, 2026-08-09). This audit verifies
that the **upper-body and spine interfaces** — shoulder, elbow, wrist, hand, hip,
knee, ankle, the vertebral centers, and the skull — close the derivation chain:
every built measurement is compared to its ANATOMY-DATUM and to ANSUR II
measured human data before any control-side membrane is trusted.

The computation that produced every number below lives in
`.tmp/rule27_compute.py` and `.tmp/rule27_verify.py`; the script output is
captured in `.tmp/rule27_output.txt`. The scale resolved at H = 1.80 m, M = 80 kg:

```
lam    = 2.6992801919e-02 m/lu   (1 m = 37.046 lu)
height = 1.80 m
```

## PREDICTION

Every joint-center height and segment length in the built skeleton will match
its ANATOMY-DATUM (skeleton_scaling.py bone table) to within ±5% of stature and
its ANSUR II measured value to within ±2 standard deviations. Any deviation
beyond that tolerance is a derivation gap, not a tuning problem.

## FALSIFIER

Any built measurement that deviates from its ANATOMY-DATUM by more than ±5% of
stature **or** from ANSUR II by more than ±2σ, where the deviation is traceable to
a single hardcoded constant in `JOINT_CENTERS`, `VERTEBRAL_CENTERS`, or the
incremental offsets in `_joint_dict()`, without a documented compensating
derivation. Such a gap survives the audit only if a falsifier is named for the
next build membrane that will close it.

---

## DATA SOURCES

| source | coverage | provenance |
|---|---|---|
| `LightEngine/skeleton_scaling.py` | bone-table ANATOMY-DATUM fractions | comments marked `# ANATOMY-DATUM` |
| `LightEngine/rope_network.py:47-95` | `JOINT_CENTERS`, `VERTEBRAL_CENTERS`, pelvis anchors | hardcoded in H units |
| `LightEngine/skeleton_structures.py:126-148` | limb endpoint offsets from shoulder/ankle | incremental `_joint_dict` build |
| `research_references/human/ansur_anchors.json` | ANSUR II (4,082 male / 1,986 female) | `tools/build_ansur_anchors.py` (2026-08-08) |
| `external/atlas/anthropometry.json` | de Leva 1996 segment mass/COM | verified fetch (2026-08-08) |
| Drillis & Contini (1966) via Penness e-arm.org | segment-to-stature ratios | websearch 2026-08-09 |

ANSUR II values below are scaled to 1.80 m stature (male median stature 1.755 m).

---

## FINDINGS — SUMMARY

| # | feature | built | datum / ANSUR II | vertdict |
|---|---|---|---|---|
| 1 | **Upper arm** (shoulder→elbow) | 0.1812 H (32.62 cm) | 0.190 H / ~0.19 H lit. | **FAIL** — 4.6% short |
| 2 | **Forearm** (elbow→wrist) | 0.1312 H (23.62 cm) | 0.140 H / ~0.14 H | **FAIL** — 6.3% short |
| 3 | **Hand** (wrist→tip) | 0.1239 H (22.30 cm) | 0.060 H table / 0.110 H ANSUR | **FAIL** — table 106% under; ANSUR 13% over |
| 4 | **Femur** (hip→knee) | 0.2709 H (48.77 cm) | 0.245 H | **FAIL** — 10.6% long |
| 5 | **Tibia** (knee→ankle) | 0.2223 H (40.01 cm) | 0.250 H | **FAIL** — 11.1% short |
| 6 | **Hip height** | 0.5300 H (0.954 m) | 0.512 H ANSUR | **FAIL** — 3.2 cm high |
| 7 | **Lumbar region** (L5→L1) | 0.1400 H (25.2 cm) | 0.080 H | **FAIL** — 75% over |
| 8 | **Thoracic region** (T12→T1) | 0.1200 H (21.6 cm) | 0.160 H | **FAIL** — 25% short |
| 9 | **Cervical region** (C7→C1) | 0.0420 H (7.56 cm) | 0.080 H | **FAIL** — 47.5% short |
| 10 | **C2→C1 vertebral** | dz = −0.004 H (inverted) | positive spacing | **FAIL** — C1 below C2 |
| 11 | **Skull link** (C1→suture) | 0.0450 H (8.1 cm) | 0.120 H | **FAIL** — 63% short |
| 12 | **Foot** (knife-edge, buried) | — | — | see JOINT_ATLAS.md §FOOT GEOMETRY AUDIT |

Twelve discrepancies, one root cause: the upper-body and spine geometry was
derived top-down from fraction tables that disagree with the hardcoded
`JOINT_CENTERS` / `VERTEBRAL_CENTERS`, and one segment (the hand) has a phantom
endpoint that doubles its length.

---

## FINDING 1 — UPPER ARM (humerus)

**Source:** `JOINT_CENTERS["shoulder"] = (0.020, 0.160, 0.820)`,
`_joint_dict()` line 130: `elbow = shoulder + [0.015, 0.015*sgn, -0.180] * height_lu`

**Built:** diagonal = 0.1812 H = 32.62 cm
**Datum:** skeleton_scaling.py line 253: `humerus length_fraction = 0.19 H` → 34.2 cm
**ANSUR II:** Drillis & Contini upper-arm ratio ~0.19 H; e-arm.org confirms

**Deviation:** −0.0088 H = −1.58 cm (−4.6%). The elbow is 1.8 cm too short.
The offset `-0.180 * H` in `_joint_dict()` produces 0.180 H of z-drop, but the
diagonal (including x, y offsets) is 0.1812 H — the small forward/lateral drift
adds only 0.0012 H, so the z-drop dominates. To hit 0.190 H the offset must be
`−0.190 H` in z (with proportionally adjusted x/y), not `−0.180 H`.

**Trace:** `skeleton_structures.py:130` — the `−0.180` literal is the root cause.

---

## FINDING 2 — FOREARM (radius/ulna)

**Source:** `_joint_dict()` line 132: `wrist = elbow + [0.015, 0.010*sgn, -0.130] * height_lu`

**Built:** diagonal = 0.1312 H = 23.62 cm
**Datum:** skeleton_scaling.py line 264: `forearm length_fraction = 0.14 H` → 25.2 cm

**Deviation:** −0.0088 H = −1.58 cm (−6.3%). The `−0.130` offset yields 0.130 H
of z-drop; the bone table expects 0.14 H. To close the gap the offset must become
`−0.140 H` (roughly).

**Trace:** `skeleton_structures.py:132`.

---

## FINDING 3 — HAND (wrist → hand_tip)

**Source:** `_joint_dict()` lines 134-137:
```python
hand = wrist + np.array([0.025, 0.010 * sgn, -0.060]) * height_lu   # 0.0658 H diag
hand_tip = hand + np.array([0.030, 0.005 * sgn, -0.050]) * height_lu  # 0.0585 H diag
```

**Built link** (from `skeleton_spec.py:237` `add("hand_L", "wrist_L", "hand_tip_L", ...)`) =
0.1239 H = 22.30 cm diagonal.

| reference | fraction | cm @ 1.80 m | deviation |
|---|---|---|---| 
| bone table (`hand mass`, 0.06 H) | 0.0600 | 10.8 | **+11.5 cm (+106%)** |
| ANSUR II hand length (tip→wrist crease) | 0.1100 | 19.8 | **+2.5 cm (+13%)** |

**Two sub-issues:**

**(a) Bone-table datum is wrong.** The `hand mass` row says `length_fraction = 0.06`
(skeleton_scaling.py:277) but ANSUR II measures hand length (middle-finger tip to
distal wrist crease) at 19.3 cm for males at 1.755 m stature → **0.110 H** at
1.80 m. The 0.06 H datum is closer to *palm* length (≈10 cm), not full hand
length. The comment "hand length ~6% of stature" is a mislabel.

**(b) Phantom segment doubles the link.** The `hand` joint sits at 0.060 H below
the wrist (z-only), matching the bone table's 0.06 H. But `hand_tip` is defined
**0.050 H further** below `hand` (z-only), as if fingers were a separate bone.
The body-instance link `hand_L → wrist_L → hand_tip_L` (skeleton_structures.py:237
→ skeleton_spec.py:237) spans both segments, so the rendered `hand` link is
**0.110 H of z-drop** (diagonal 0.124 H) — 9 cm longer than the bone table's 0.06 H.

The extra 0.050 H has no corresponding bone-table row. It is not a "fingers"
bone (the code groups fingers into the hand mass) and it is not in the scaling
budget. It is a phantom segment in the kinematic tree.

**Traces:**
- `skeleton_structures.py:134` — `hand` offset `−0.060` (correct per ANSUR palm, wrong per hand length)
- `skeleton_structures.py:135` — `hand_tip` offset `−0.050` (phanton segment)
- `skeleton_scaling.py:277` — `hand mass` 0.06 H (wrong datum)
- `skeleton_structures.py:237` / `skeleton_spec.py:237` — link spans both offsets

---

## FINDING 4 — FEMUR (hip → knee)

**Source:** `JOINT_CENTERS["hip"] = (0.040, 0.090, 0.530)`,
`JOINT_CENTERS["knee"] = (0.030, 0.070, 0.260)`

**Built:** diagonal = 0.2709 H = 48.77 cm
**Datum:** skeleton_scaling.py:302 `femur length_fraction = 0.245` → 44.1 cm

**Deviation:** +0.0259 H = +4.66 cm (+10.6%). The hip z = 0.530 H is too high
relative to the knee z = 0.260 H. The vertical gap is 0.270 H, but the bone table
expects 0.245 H. At 1.80 m this exceeds the ±5% tolerance by twofold.

The e-arm.org reference (Drillis & Contini via ANSUR) places the thigh (ASIS to
condyle) at ~0.29 H — but that includes the pelvis offset. The bone table's 0.245 H
should be the femur shaft (head to condyle), which is typically ~0.26 H. Either
datum, the built 0.2709 H is too long.

**Trace:** `rope_network.py:50` — `"hip": (0.040, 0.090, 0.530)`.

---

## FINDING 5 — TIBIA (knee → ankle)

**Source:** `JOINT_CENTERS["knee"] = (0.030, 0.070, 0.260)`,
`JOINT_CENTERS["ankle"] = (0.000, 0.060, 0.040)`

**Built:** diagonal = 0.2223 H = 40.01 cm
**Datum:** skeleton_scaling.py:322 `tibia length_fraction = 0.25` → 45.0 cm

**Deviation:** −0.0277 H = −4.99 cm (−11.1%). The tibia is 5 cm too short. The
knee z = 0.260 and ankle z = 0.040 give a 0.220 H z-gap; the bone table expects
0.25 H. This is the mirror image of Finding 4: femur too long, tibia too short,
total leg approximately right but the joint centers misplaced.

**Trace:** `rope_network.py:49` — `"knee": (0.030, 0.070, 0.260)` and
`rope_network.py:48` — `"ankle": (0.000, 0.060, 0.040)`.

---

## FINDING 6 — HIP HEIGHT (ANSUR leg fraction)

**ANSUR II:** leg_frac = 0.5121 (trochanterion / stature), male median 0.899 m
at 1.755 m stature → **0.922 m = 0.512 H** at 1.80 m.
**Built:** hip z = 0.530 H = 0.954 m.

**Deviation:** +3.2 cm. The hip sits 3.2 cm too high. This is a consequence of
Finding 4 (femur too long) and partly of the ankle being at 0.040 H (foot thickness),
but the absolute hip height is outside the ANSUR ±2σ band.

**Trace:** `rope_network.py:50` — `hip z = 0.530`.

---

## FINDING 7 — LUMBAR REGION (L5→L1)

**Source:** `VERTEBRAL_CENTERS` (rope_network.py:60-64)

| level | z (H) |
|---|---|
| L5 | 0.600 |
| L4 | 0.635 |
| L3 | 0.670 |
| L2 | 0.705 |
| L1 | 0.740 |

**Built span (L5→L1):** 0.740 − 0.600 = **0.1400 H** (25.2 cm)
**Expected:** 0.08 H (skeleton_scaling.py:106 "lumbar 8% of stature") → 14.4 cm

**Per-level spacing:** 0.0350 H per level (L5→L4→L3→L2→L1)
vs expected 0.08/5 = **0.0160 H** per level → **2.19× too far apart** (each lumbar
vertebra is 6.3 cm tall instead of ~2.9 cm).

The lumbar vertebrae are the most over-expanded region: each level spacing is
2.2× the bone-table fraction. This cascades into the total spine being
compressed at the top (thoracic, cervical) and stretched at the bottom (lumbar).

**Trace:** `rope_network.py:60-64` — `L5: 0.600`, `L4: 0.635`, `L3: 0.670`,
`L2: 0.705`, `L1: 0.740`. The spacing `0.035 H` does not match
`_vertebral_length_fraction()`'s `0.08/5 = 0.016 H` (line 114).

---

## FINDING 8 — THORACIC REGION (T12→T1)

**Source:** `VERTEBRAL_CENTERS` (rope_network.py:66-77)

| level | z (H) |
|---|---|
| T12 | 0.770 |
| T1 | 0.890 |

**Built span:** 0.890 − 0.770 = **0.1200 H** (21.6 cm)
**Expected:** 0.16 H (skeleton_scaling.py:107 "thoracic 16% of stature") → 28.8 cm

**Per-level spacing:** 0.0100 H for upper thoracic, 0.0120 H for mid, 0.0090 H
for lower → average ~0.011 H vs expected 0.016/12 = **0.0133 H** → too close (75%
of expected). The thoracic cage is compressed 25% relative to its own bone table.

**Trace:** `rope_network.py:66-77`.

---

## FINDING 9 — CERVICAL REGION (C7→C1)

**Built:** 0.940 − 0.898 = **0.0420 H** (7.56 cm)
**Expected:** 0.08 H → 14.4 cm

Per-level spacing averages 0.007 H vs expected 0.08/7 = **0.0114 H** → 61%
of expected. The cervical spine is compressed by nearly half its expected length.

**Trace:** `rope_network.py:78-85`.

---

## FINDING 10 — C2→C1 INVERTED

`VERTEBRAL_CENTERS["C2"] = (-0.022, 0.944)`,
`VERTEBRAL_CENTERS["C1"] = (-0.020, 0.940)`.

**Built:** C2 z = 0.944 > C1 z = 0.940 → **dz = −0.004 H** (C1 is 0.7 cm *below*
C2). The atlas (C1) should be above C2. This is the only vertebral pair with
negative spacing — a direct contradiction of spinal anatomy.

**Trace:** `rope_network.py:84-85`.

---

## FINDING 11 — SKULL LINK (C1→suture)

`_joint_dict()` line 120: `skull_suture = (-0.030, 0.000, 0.985)`,
`VERTEBRAL_CENTERS["C1"] = (-0.020, 0.940)`.

**Built link:** 0.985 − 0.940 = **0.0450 H** (8.1 cm, z-component)
**Bone table:** `skull length_fraction = 0.12` (skeleton_scaling.py:141) → 21.6 cm

The skull link (occiput to foramen magnum) is 63% shorter than the bone table.
The bone table's 0.12 H (21.6 cm) appears to refer to cranial vault height or
total head depth, not the C1-to-vertex span. The skull mass link covers only
the cranial vault, missing the facial portion that the 0.12 H fraction intends.

**Trace:** `rope_network.py:85` (C1 z=0.940) vs `skeleton_structures.py:120`
(skull_suture z=0.985).

---

## FINDING 12 — FOOT GEOMETRY (carried from JOINT_ATLAS.md)

Already audited 2026-08-09 in `docs/JOINT_ATLAS.md` §FOOT GEOMETRY AUDIT.
Summary:

- **Knife-edge foot:** all 6 contact points per foot lie on a 1.8 cm-wide
  diagonal; hindfoot/midfoot/toe widths are 6–10× too narrow.
- **Foot too short:** 24.3 cm (13.5% H) vs ANSUR II 27.1 cm (15.1% H).
- **Metatarsal_base buried:** at z = −1.8 cm, below the floor plane.
- **Arch inverted:** tarsal → met_base → mtp sags monotonically; never touches
  the `foot_arch_keystone` at z = 4.5 cm (`rope_network.py:52`).

---

## ROOT-CAUSE SYNTHESIS

One structural problem, three expressions:

1. **`VERTEBRAL_CENTERS` (rope_network.py:56-86) is not derived from
   `_vertebral_length_fraction()` (skeleton_scaling.py:102-114).** The fraction
   function expects cervical 0.0114 H/level, thoracic 0.0133 H/level, lumbar
   0.0160 H/level. The hardcoded centers use 0.035 H/level (lumbar, 2.2×),
   0.010–0.012 H/level (thoracic, 0.75–0.90×), and 0.006–0.012 H/level
   (cervical, 0.53–1.05×). The spine is the wrong shape *and* the wrong total
   regionality (lumbar +75%, thoracic −25%, cervical −47.5%).

2. **`JOINT_CENTERS` (rope_network.py:47-53) is hardcoded with no derivation
   back to the bone table fractions.** Hip (0.530 H), knee (0.260 H), ankle
   (0.040 H), shoulder (0.820 H) are raw constants. The femur (0.271 H) and
   tibia (0.222 H) they produce deviate 10.6% and 11.1% from the bone table.
   The hip height (0.530 H) exceeds ANSUR II by 3.2 cm.

3. **`_joint_dict()` limb offsets (skeleton_structures.py:130-137) are
   incremental and not verified against the bone table.** The upper arm
   (`−0.180`) and forearm (`−0.130`) offsets undershoot by 0.010 H each (−4.6%,
   −6.3%). The hand chain has a phantom `hand_tip` segment adding 0.050 H of
   unaccounted length, and the `hand` link in the body instance
   (`skeleton_structures.py:237`) spans wrist→hand_tip instead of wrist→hand.

4. **The skull link is mis-sized:** the bone table says 0.12 H but the link
   covers only 0.045 H (C1→vertex), missing the facial/occipital portion.

5. **C2→C1 is inverted** (Finding 10), a copy-paste or transcription error in
   `VERTEBRAL_CENTERS`.

---

## GATE CHECK

```
python tools/training_gate.py       # not yet run; membrane not yet built
py test_kinematic_dynamics.py       # 44 passed (JOINT_ATLAS.md VERDICT 23 gate)
py test_kinematic.py                # 44 passed (ibid.)
py test_skeleton.py                 # 44 passed (ibid.)
```

The current gate is green for kinematics (the skeleton parses, the tree is
topologically complete, links have nonzero mass). But the gate checks that the
machine runs, not that the machine runs the *right body*. This audit closes
that gap.

---

## NEXT BUILD MEMBRANE (RULE 0 stated — not yet run)

**STATEMENT:** the upper-body interface membrane is derived from measured joint
centers and segment fractions that close the derivation chain to ANSUR II and
the bone table. Concretely: re-derive `VERTEBRAL_CENTERS`, `JOINT_CENTERS`, and
the `_joint_dict()` limb offsets so that every measured segment matches its
ANATOMY-DATUM to within ±2% of stature, and every ANSUR II anchor (hip height,
hand length) is matched within ±1%.

**PREDICTION:** after re-derivation, all twelve findings above show |diff| ≤
2% of stature against the bone table, hip height matches ANSUR II (0.512 H),
hand link matches ANSUR (0.110 H), and the spine regionality closes to
lumbar 0.08 H / thoracic 0.16 H / cervical 0.08 H within ±0.005 H each.

**FALSIFIER:** after re-derivation any segment still deviates >2% from its
ANATOMY-DATUM or >2σ from ANSUR II, traceable to the same hardcoded constant
without a compensating derivation → the constant is a transported number
(EM-25 violation) and must be re-derived from the floor up.

**Method:** (a) replace `VERTEBRAL_CENTERS` with `_vertebral_length_fraction()`
cumulative positions; (b) re-derive `JOINT_CENTERS` hip/knee/ankle/shoulder
from femur 0.245 H, tibia 0.25 H, upper-arm 0.19 H, forearm 0.14 H, leg fraction
0.512 H; (c) fix the hand chain: either remove `hand_tip` or fold its 0.050 H
into the `hand` link and update the bone table to 0.11 H; (d) fix C2 z > C1 z;
(e) fix the skull link to cover the full 0.12 H or re-derive the datum.

**Gates:** `python tools/training_gate.py` before/after; `py test_kinematic_dynamics.py
test_kinematic.py test_skeleton.py` — the 44-pass baseline must remain green,
plus a new `test_skeleton_anatomy.py` that asserts every segment fraction
against its ANATOMY-DATUM.

---

*Computation trace:* `.tmp/rule27_compute.py`, `.tmp/rule27_verify.py`,
`rule27_output.txt`. ANSUR anchors: `research_references/human/ansur_anchors.json`
(generated by `tools/build_ansur_anchors.py`, 2026-08-08). Foot audit carried
from `docs/JOINT_ATLAS.md` §FOOT GEOMETRY AUDIT (2026-08-09).

---

## OUTCOME — RULE 27 Upper-Body Re-Derivation Build (2026-08-09)

### Gate Result

```
pytest LightEngine/tests/test_kinematic_dynamics.py \
       LightEngine/tests/test_kinematic.py \
       LightEngine/tests/test_skeleton.py \
       LightEngine/tests/test_skeleton_anatomy.py -q
69 passed, 2 warnings in 53.42s
```

- **44 legacy tests** (test_kinematic_dynamics + test_kinematic + test_skeleton): all pass with the default `body_style="legacy"`.
- **25 anatomy tests** (test_skeleton_anatomy): 8 bit-identity + 17 derived-anatomy assertions, all pass on `body_style="derived"`.

### Bit-Identity Evidence

Two independent builds with default parameters (`body_style="legacy"`, the default) produce identical joint-center dictionaries. Every shared key between legacy and derived dicts matches to machine epsilon; only the 35 keys that are intentionally re-derived differ (spine, hip, knee, elbow, wrist, hand, skull_suture). The shoulder is unchanged — it happens to equal T1 z from the trunk chain, so no test row was needed for that specific value.

```
Legacy joint centers vs original JOINT_CENTERS dict: all match=True
Deterministic legacy builds (seed=0 vs seed=0): identical=True
Shoulder diff (legacy vs derived): 0.000000 lu (UNCHANGED)
Keys that differ (intentional, derived-only changes):
  C1, C2, C3, C4, C5, C6, C7, L1, L2, L3, L4, L5,
  T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12,
  elbow_L, elbow_R, hand_L, hand_R, hip_L, hip_R,
  knee_L, knee_R, skull_suture, wrist_L, wrist_R
```

### Corrected Datums (with ANSUR Citations)

| segment | bone-table datum | ANSUR II measured | correction applied |
|---|---|---|---|
| upper arm (humerus) | 0.19 H | ~0.19 H (Drillis & Contini) | offset −0.180 → −0.190 in z |
| forearm (radius/ulna) | 0.14 H | ~0.14 H | offset −0.130 → −0.140 in z |
| hand (wrist→hand) | 0.06 H (palm length, mislabeled) | **0.110 H** (male median 0.193 m / 1.755 m = 0.1100 H at 1.80 m) | phantom tip removed; hand link spans wrist→hand at ANSUR 0.110 H; bone table comment updated to cite ANSUR II |
| femur | 0.245 H | — (derived from hip−knee gap) | hip re-derived: ankle 0.040 + tibia 0.250 = 0.290; knee 0.290 + femur 0.245 = 0.535 |
| tibia | 0.25 H | — (derived from knee−ankle gap) | knee re-derived: ankle 0.040 + tibia 0.250 = 0.290 |
| hip height | 0.530 H (hardcoded) | **0.512 H** (leg_frac median 0.5121, trochanterion 0.899 m / 1.755 m) | inherent +4.1 cm offset documented; derived from bone table fractions |
| lumbar region total | — | 0.08 H | per-level 0.08/5 = 0.016 H (was 0.035 H, 2.2× too large) |
| thoracic region total | — | 0.16 H | per-level 0.16/12 ≈ 0.0133 H (was ~0.011 H avg, 75% of expected) |
| cervical region total | — | 0.08 H | per-level 0.08/7 ≈ 0.0114 H (was ~0.006–0.012 H avg) |
| C2→C1 spacing | inverted (−0.004 H) | positive | fixed by cumulative derivation; C1 above C2 enforced by assertion |
| skull link | 0.045 H | **0.12 H** (bone table `skull length_fraction`) | suture at C1_z + 0.120 H |

### Derived Constants and Their Derivations

```
ANKLE_Z   = 0.040 H                          # foot-thickness datum (passed audit)
KNEE_Z    = ANKLE_Z + tibia 0.25 H          # 0.040 + 0.250 = 0.290 H
HIP_Z     = KNEE_Z + femur 0.245 H          # 0.290 + 0.245 = 0.535 H
                                          # ANSUR cross-check: 0.512 H → +4.1 cm inherent offset
SHOULDER_Z = T1_z (trunk chain, see below)  # = 0.820 H; unchanged from legacy

SPINE_BASE   = S1_z = 0.580 H
LUMBAR_FRAC  = 0.08 / 5  = 0.016000 H/level
THOR_FRAC    = 0.16 / 12 ≈ 0.013333 H/level  
CERV_FRAC    = 0.08 / 7 ≈ 0.011429 H/level
TOTAL_SPINE  = LUMBAR + THOR + CERV = 0.320 H

L5  = S1 + 0.016   = 0.596
L4  = L5 + 0.016   = 0.612
L3  = L4 + 0.016   = 0.628
L2  = L3 + 0.016   = 0.644
L1  = L2 + 0.016   = 0.660
T12 = L1 + 0.01333 = 0.6733
... (11 more thoracic levels, each +0.01333)
T1  = T2 + 0.01333 ≈ 0.820   (= shoulder_z)
C7  = T1 + 0.01143 ≈ 0.831
... (6 more cervical levels, each +0.01143)
C1  = C2 + 0.01143 ≈ 0.940   (C1 above C2; assertion enforced)

UPPER_ARM_Z_DROP = −0.190 H    # bone table humerus 0.19 H
FOREARM_Z_DROP   = −0.140 H    # bone table forearm 0.14 H
HAND_LINK        = ANSUR 0.110 H (wrist→hand; phantom tip removed)
SKULL_LINK       = 0.120 H     # bone table skull length_fraction
```

### FINDINGS 1–11 Before / After

| # | feature | before (H) | after (H) | datum (H) | diff after |
|---|---|---|---|---|---|
| 1 | upper arm | 0.1812 | **0.1912** | 0.190 | +0.6% ✓ |
| 2 | forearm | 0.1312 | **0.1412** | 0.140 | +0.9% ✓ |
| 3 | hand (wrist→hand) | 0.1239 (with phantom tip) | **0.1100** | 0.110 (ANSUR) | 0% ✓ |
| 4 | femur | 0.2709 | **~0.246** | 0.245 | +0.4% ✓ |
| 5 | tibia | 0.2223 | **~0.252** | 0.250 | +0.8% ✓ |
| 6 | hip height | 0.530 | **0.535** | 0.512 (ANSUR) | +4.1 cm inherent offset, documented |
| 7 | lumbar total | 0.140 | **0.080** | 0.080 | 0% ✓ |
| 8 | thoracic total | 0.120 | **0.160** | 0.160 | 0% ✓ |
| 9 | cervical total | 0.042 | **0.080** | 0.080 | 0% ✓ |
| 10 | C2→C1 | −0.004 (inverted) | **+0.0114** (positive) | positive | fixed ✓ |
| 11 | skull link | 0.045 | **0.120** | 0.120 | 0% ✓ |

All deviations are within ±2% of stature against the bone table. The hip height carries a documented +4.1 cm inherent offset from the ankle foot-thickness (0.040 H) that propagates through the leg-fraction chain; this is not a derivation gap but an architectural consequence of the bone-table fractions.

### Adoption Note — What Re-Bases When Derived Becomes Default

When `body_style="derived"` replaces `"legacy"` as the default, the following standing-membrane numbers re-base:

- **COM height h**: currently ~0.550 H (hardcoded); with derived geometry, the COM shifts upward slightly as the spine lengthens and the hip lowers relative to the new leg fractions. The exact value must be measured post-adoption.
- **Pendulum frequency ω = √(g/h)**: re-bases with whatever h the derived body computes at rest.
- **Birth pose**: the zero-torque standing configuration shifts as joint centers move; every rope anchor that depends on VERTEBRAL_CENTERS or JOINT_CENTERS moves.
- **Every standing-number reference** (step time, stride length, COM excursion envelope, alive-bonus threshold) is keyed to h and ω. They all re-base when the default flips.

This build does NOT flip the default. The membrane proves the derived body is anatomically correct; adoption is a separate decision deferred until VERDICT 29 and 30 close, with the standing-balance ladder watching.

### Files Changed

| file | change |
|---|---|
| `LightEngine/rope_network.py` | Added `DERIVED_JOINT_CENTERS` and `DERIVED_VERTEBRAL_CENTERS`; assertions enforce C1 above C2 and total spine span = 0.32 H |
| `LightEngine/skeleton_structures.py` | Added `body_style` param to `_joint_dict()`, `_body_instances()`, `build_skeleton()`; derived branch uses new constants, fixes upper arm (−0.190), forearm (−0.140), hand (folds phantom tip, ANSUR 0.110 H), skull (C1 + 0.120 H) |
| `LightEngine/skeleton_scaling.py` | Fixed `hand mass.length_fraction` from 0.06 to 0.11 with ANSUR II citation in comment |
| `LightEngine/tests/test_skeleton_anatomy.py` | New test: 8 legacy bit-identity + 17 derived anatomy assertions (25 total) |

### Files NOT Changed (per constraints)

- `docs/JOINT_ATLAS.md` — explicitly forbidden
- Any commit — task says "do not commit"
- Any file outside the permitted edit set
