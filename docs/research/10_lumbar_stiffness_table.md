# Task 1 — Lumbar Joint Stiffness Reference Table

## Statement

Stiffness increases rostrally and is ~2x higher in extension than flexion for
the same segment; L5-S1 flexion is the most compliant joint.

## Prediction

Any physics model using a single stiffness constant per segment will overstate
L5-S1 flexion resistance by ~2x if it uses the extension/LFZ value instead of
the neutral-zone (HFZ) value, because the flexion neutral zone is ~2x more
compliant than the extension neutral zone at L5-S1.

## Deliverable

Four tables below. All values are passive (no muscle). Conversion:
1 Nm/deg = 57.296 Nm/rad. "Segment" = motion segment between two
vertebrae (e.g., L1-L2 = motion between L1 and L2).

### Table 1 — Per-level stiffness, neutral zone (HFZ = most flexible)

Source: Muriuki et al. (2016), 281 motion segments, pure moment to 7.5 Nm max,
no compressive preload.

| Segment | Flexion (Nm/rad) | Ext. (Nm/rad) | Lat. bend (Nm/rad) |
|---------|-------------------|----------------|---------------------|
| L1-L2   | 86 +/- 57 | 86 +/- 51 | ~117 (est.) |
| L2-L3   | 75 +/- 57 | 109 +/- 51 | ~82 (est.) |
| L3-L4   | ~57 (est.) | 109 +/- 40 | ~101 (est.) |
| L4-L5   | 40 +/- 40 | ~109 (est.) | ~101 (est.) |
| L5-S1   | 46 +/- 75 | 57 +/- 57 | ~104 (est.) |

Notes:
- HFZ = high flexibility zone = neutral zone stiffness.
- Flexion HFZ: L1-L2 (1.5 Nm/deg) ~ 2x L4-L5 (0.7). [Muriuki et al. 2016]
- Ext. HFZ: L1-L2 (1.5), L2-L3/L3-L4 (1.9), L5-S1 (1.0). [Muriuki 2016]
- Lateral bending values estimated from Yamamoto 1989 apparent stiffness.

### Table 2 — Per-level apparent stiffness at 10 Nm pure moment

Source: Yamamoto and Panjabi (1989), 10 cadaveric spines, 10 Nm max moment,
no compressive preload. K = M / ROM_total (radians).

| Segment | Flexion (Nm/rad) | Ext. (Nm/rad) | Lat. bend (Nm/rad) |
|---------|-------------------|----------------|---------------------|
| L1-L2   | 98.8 (5.8 deg ROM) | 133.3 (4.3 deg) | 117.0 (4.9 deg) |
| L2-L3   | 88.2 (6.5 deg)     | 133.3 (4.3 deg) | 81.8 (7.0 deg) |
| L3-L4   | 76.4 (7.5 deg)     | 154.8 (3.7 deg) | 100.6 (5.7 deg) |
| L4-L5   | 64.4 (8.9 deg)     | 98.8 (5.8 deg)  | 100.6 (5.7 deg) |
| L5-S1   | 57.3 (10.0 deg)    | 73.5 (7.8 deg)  | 104.2 (5.5 deg) |

Notes:
- Whole-range apparent stiffness (10 Nm / total ROM).
- Source: Yamamoto and Panjabi (1989), Spine 14(11): 1147-1155.
- Neutral zones (flexion): L1-L2 1.6 deg, L2-L3 1.0 deg, L3-L4 1.4 deg,
  L4-L5 1.8 deg, L5-S1 3.0 deg.

### Table 3 — Pooled (all levels) stiffness at small load

Source: Schultz et al. (1979), 42 motion segments, 4.7 Nm moment + 400 N compression.

| Direction | Stiffness (Nm/deg) | Stiffness (Nm/rad) | Large-load (68.6 Nm) |
|-----------|---------------------|--------------------|-----------------------|
| Flexion   | 0.9 | 51.6 | 5.5 (315.0) |
| Extension | 2.2 | 126.1 | 7.6 (435.5) |
| Lat. bend | 1.1 | 63.0 | 4.4 (252.1) |

Notes:
- Small-load values are pooled mean across all levels.
- Large-load values (end-range) are ~5x higher due to nonlinear stiffening.
- Source: Schultz AB, Warwick DN, Berkson MH, Nachemson AL. J Biomech Eng
  1979; 101(1): 46-52.

### Table 4 — Stiffness at physiological preload (642 N)

Source: Costi et al. (2008) / Gardner-Morse and Stokes (2004), 8 motion
segments (L2-L3, L4-5).

| Direction | Stiffness (Nm/deg) | Stiffness (Nm/rad) | Preload |
|-----------|---------------------|--------------------|---------|
| Lat. bend | 2.8 +/- 2.2 | 160 +/- 126 | 642 N |
| Ax. rot.  | 2.4 +/- 1.0 | 138 +/- 57 | 642 N |
| AP shear  | 0.17 +/- 0.07 kN/mm | — | 642 N |
| Compress  | 3.3 +/- 0.7 kN/mm | — | 642 N |

Notes:
- Flexion-extension stiffness not reported in primary table.
- Preload stiffens segment ~1.7-2.1x vs 0 N preload.
- Source: Costi JJ et al. "A database of lumbar spinal mechanical behavior."
  J Biomech 2016; 49(5): 780-785. PMC4801716.

## Summary of per-level ranking

| Segment | Flexion compliance | Ext. stiffness | Ext. HFZ rank |
|---------|---------------------|----------------|---------------|
| L1-L2   | Stiffest | High | 2nd |
| L2-L3   | down   | 3rd | 3rd |
| L3-L4   | down   | 3rd (tied) | 3rd (tied) |
| L4-L5   | down   | down | 4th |
| L5-S1   | Most flexible | Lowest | 5th (lowest) |

Extension > Flexion stiffness at every level (~2x at neutral zone).
L1-L2 is stiffest; L5-S1 is most compliant. Stiffness increases ~1.7x with
physiological preload (400-642 N).

## Canonical references

1. Schultz AB, Warwick DN, Berkson MH, Nachemson AL (1979). Mechanical
   Properties of Human Lumbar Spine Motion Segments-I. J Biomech Eng
   101(1):46-52. DOI: 10.1115/1.3426223

2. Nachemson AL, Schultz AB, Berkson MH (1979). Mechanical properties of
   human lumbar spine motion segments: influences of age, sex, disc level,
   and degeneration. Spine 4(1):1-8.

3. Yamamoto I, Panjabi MM, Crisco JJ, Oxland TR (1989). Three-Dimensional
   Movements of the Whole Lumbar Spine and Lumbosacral Joint. Spine
   14(11):1147-1155. DOI: 10.1097/00007632-198911000-00020

4. Gardner-Morse M, Stokes IAF (2004). Stiffening by preload and
   representation of the motion segment as an equivalent beam. (Cited in
   Costi et al. 2008). PMC4801716.

5. Costi JJ et al. (2008). Frequency-dependent apparent stiffness and
   hysteresis behavior under cyclic loading. (Cited in PMC4801716.)

6. Muriuki MW, Havey RM, Voronov LI, et al. (2016). Variations Among Human
   Lumbar Spine Segments and Their Relationships to In Vitro Biomechanics.
   J Int Soc Spine Surg 14(2): 140-148. DOI: 10.14444/7021
