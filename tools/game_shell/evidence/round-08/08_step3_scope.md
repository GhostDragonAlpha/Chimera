# Round-08 fix — Steps 0a/0b PASS; Step 3 ownership diff: STOP at scope gate

Date: 2026-10-10 · Worker: Tiel · Status: **STOPPED before regenerating the
real pack** — the ownership diff stays inside the two limbs being fixed but
extends beyond the strict foot/hand boxes (shin/forearm/upper-arm seam
correction). The assignment names this wall ("Any change elsewhere = STOP…
ownership diff spreads"). Qwen's scope ruling requested; everything else is
staged and green.

## Gate 0a — PASS (bit-exact)

`.tmp/skeleton/rom_referee_r2.json` restored (sha256 `1c0e31b3b2d259e3480cab389c7fa39abda3c72d4c41c4c403b1405f8df978f5`, identical to `_scratch_gen/rom_referee_r2.reconstructed.json`). HEAD (unmodified) generator, scratch output (`_scratch_gen/gen_r2_gate0a.py`, log `gate0a_r2.log`) → `74b3ab044b7adaed4a0f9349a81f5d3c87441084b2ec8981f4e0afaba50c1662` — bit-exact.

## Gate 0b — PASS (bit-exact both ways)

Working-tree generator (Option-B embedded fallback already applied, uncommitted):
- overlay moved aside (`WARNING: … applying the EMBEDDED referee ROMs`): `74b3ab04…c1662` (`gen_r2_gate0b.py`, `gate0b_nofile_r2.log`)
- overlay restored: `74b3ab04…c1662` (`gate0b_withfile_r2.log`)

Tracked state alone reproduces the pinned asset.

## Step 2 — patch applied to tools/rig_factory_fit.py (uncommitted)

1. **Terminal-tip law** (was lines 238-245): hand tip = 30-vert mean extremal
   along the elbow→wrist direction, within 2× forearm of the wrist, beyond the
   wrist plane → `(3.011, 2.518, -0.351)` (true fingertip; old law landed
   `(1.797, 5.131, -0.110)` at the ELBOW — the same sphere-cap bug as the foot).
   Foot tip = 30-vert mean extremal +z among verts below the ankle pivot on the
   +x side → `(1.102, 0.043, 1.399)` (true toe; old `(0.496, 1.213, 0.026)` up
   the shin). Sanity per 08_pack_probe: y≈0.04, z=1.40 > 0.4. The foot is a
   long splayed primate foot (heel z −0.2 → toe z 1.44).
2. **Terminal-band exemption** from LIMB_CAP: `ankle*`/`wrist*` segment claims
   are never rejected to the axial root; every other limb keeps the cap +
   axial fallback; mirror law untouched.
3. **Terminal blend partner**: verts owned by ankle_L/R → w=1, joint2=knee_L/R;
   wrist_L/R → w=1, joint2=elbow_L/R (the validated FIX PROOF law).

Scratch regeneration (`gen_r2_step2.py` → `step2_pack.bin`, log `step2.log`):
ROM overlay applied; ankle bands 121→1212 verts, wrist 263→1253, all w=1.00;
EMPTY BANDS: NONE; unassigned 0; share law max |w+w2−1| = 3.0e-08.

## Step 3 — ownership diff (`_diff_step2.py` → `step2_diff.txt`)

Joint tables **bit-identical to shipped: J ✓ AX ✓ ROM ✓ parents ✓** (the patch
does not touch ROM).

Owner transitions (per side; L counts shown, R mirrors exactly):
spine_lower→ankle_L 888, spine_lower→wrist_L 647, tail_base→wrist_L 377,
knee_L→ankle_L 311, elbow_L→wrist_L 215, wrist_L→elbow_L 203,
wrist_L→shoulder_L 46, ankle_L→knee_L 100. Total owner-changed 5590;
w/j2/w2-only 512. **No transition touches neck/jaw/spine_*/tail_mid/tail_tip/
hip/ear/lid/brow/mouth as from- or to-owner** — spine_lower/tail_base only
LOSE verts (the planted-foot defect itself).

Region split (changed verts): foot 2436, hand 2538, **OTHER 1128** — and all
1128 are on the two repaired limbs:
- wrist→elbow 187×2, wrist→shoulder 46×2: forearm/upper-arm skin the OLD wrist
  segment (which ran elbow→wrist) wrongly owned; returns to its limb joint.
- ankle→knee 100×2: shin skin the OLD ankle segment (which ran up the shin)
  wrongly owned.
- shoulder 123×2 / elbow 58×2 / knee 48×2 w/j2-only: seam blend partners
  updated by the pack's own adjacency law because the second-nearest segment
  moved (e.g. upper-arm seam j2 spine_upper→elbow_L, w→0.50).
- bbox of OTHER: y∈[0.38, 6.16], x∈[−2.47, 2.47] — shin + arm only; torso box
  displacement under knee_L=40 is 0.0000 in BOTH packs.

Pure-LBS sim (game's pose_binding law, both packs, rest bit-identical both):

| pose | sole L (old→new) | foot L | shin box | hand L |
|---|---|---|---|---|
| knee_L=40 | **0.164 → 1.447** | 0.237 → 1.403 | 0.339 → 0.275 | 0.000 → 0.000 |
| ankle_L=30 | 0.013 → 0.509 | 0.018 → 0.451 | 0.164 → 0.036 | 0.000 → 0.000 |
| wrist_L=40 | 0 → 0 | 0 → 0 | 0 → 0 | **0.017 → 0.659** |

Sole 1.447 matches the 08_rootcause FIX PROOF exactly. Shin box 0.339→0.275 is
NOT a shin change: restricted to the 53/125 shin verts whose binding is
unchanged, displacement is **0.225 → 0.225 identical**; the box mean moves only
because the ankle/knee crease relocated (the ruling's "~0.339 unchanged" came
from the minimal FIX PROOF, which did not relocate the crease).

## Why STOP (one ruling needed)

The gate says "ONLY foot-region and hand-region verts may change… Any change
elsewhere = STOP". Read strictly (foot = y<0.38, hand = below-wrist box), the
1128 limb-boundary verts are "elsewhere" → STOP. Read as limb regions, the diff
passes. The ruling's own Step-2 patch CANNOT avoid these changes: fixing the
tips necessarily relocates the terminal-band boundary on the shin/forearm.
Recommendation: **approve as in-scope** — every changed vert is on the leg/arm
of the repaired limb, ROM/J/AX/parents are bit-identical, rest pose is
bit-identical, torso is unmoved, and the numbers reproduce the validated fix.

## State preserved (nothing irreversible done)

- `Saved/meshes/monkey_joints.bin` UNTOUCHED, re-verified `74b3ab04…c1662`.
- `tools/creature_graph/data/creature_graph.json` pin NOT touched.
- Generator patch + overlay restore in working tree (uncommitted, as ruled).
- All Step-2/3 artifacts in `_scratch_gen/` (gen scripts, step2_pack.bin,
  logs, diff). Real-pack regeneration + re-pin + acceptance + engine/browser
  verification (Steps 3b-7) ready to run on approval — no re-analysis needed.
