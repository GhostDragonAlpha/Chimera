# M03 ERRATA — logged corrections to the frozen preregistration (PREREG.md, sha256 59adffa6...)

**Logged per campaign law: corrections = logged explanation + new receipt. PREREG.md itself is NOT
edited.** The frozen prereg's scaling LAWS were correct; two hand-derived anchor BLOCKS contained
arithmetic slips. Both were discovered because the frozen prereg was executed as written and the
deviations were preserved (receipts/analysis.json, layer "prereg_as_frozen").

## E1. Body-B inertia anchor: sign error on I[xy] and I[yz] (4 tensor entries)

- **Frozen (wrong):** `I_B(1) = [[3/40, −1/80, 1/80], [−1/80, 3/40, −1/80], [1/80, −1/80, 3/40]]`
- **Corrected:** `I_B(1) = [[3/40, +1/80, +1/80], [+1/80, 3/40, +1/80], [+1/80, +1/80, 3/40]]`
- **Root cause:** in the quick body-frame transform I mapped b2 to body coordinates as (0,−1,0).
  Correctly, b2's domain offset from the origin is (−1, 0, 0), and `R^T·(−1,0,0)` with
  `R^T = [[0,1,0],[−1,0,0],[0,0,1]]` is **(0, 1, 0)**. The authored body-frame tetrahedron is
  therefore (0,0,0), (1,0,0), (0,1,0), (0,0,1) — identical in form to cell-A's local tet, so its
  tensor must have cell-A's form scaled by m=1 (all off-diagonals +m/80), not the mixed signs.
- **Independent cross-check:** rotating the separately derived DOMAIN tensor,
  `R^T I_domain R` with `I_domain(1) = [[0.075, −0.0125, −0.0125], [−0.0125, 0.075, 0.0125],
  [−0.0125, 0.0125, 0.075]]`, reproduces the all-positive corrected tensor exactly.
- **Observed falsifier deviations caused (preserved):** `B.I[xy]`, `B.I[yx]`, `B.I[yz]`, `B.I[zy]`
  each deviate from the frozen anchor by relative 2.0 (the sign flip: |−x − x|/|−x| = 2) at every
  scale; worst reported at s=0.065.

## E2. Combined domain-inertia anchor: wrong diagonals xx, yy, zz

- **Frozen (wrong):** xx 347/144, yy 491/144, zz 683/144 (and the inherited per-scale decimals
  347/2880, 491/2880, 683/2880 at s=0.5).
- **Corrected:** **xx 427/120, yy 607/120, zz 847/120** (off-diagonals 803/240, −397/240, 329/240
  unchanged; same fractions × s⁵ per scale).
- **Root cause:** denominator-conversion slips when summing the two body contributions over a common
  denominator (e.g. 827/360 was carried as 827/720 instead of 1654/720; 227/180 → 908/720 was done
  correctly). Correct sums: xx 908/720 + 1654/720 = 2562/720 = 427/120; yy 1268/720 + 2374/720 =
  3642/720 = 607/120; zz 1748/720 + 3334/720 = 5082/720 = 847/120.
- **Independent verification:** trace(I_comb(1)) from corrected diagonals = 1881/120 = 15.675, which
  equals the independently computed 0.45 (body-A local trace) + 0.225 (body-B local trace) +
  2·(2·5/4) + 2·(1·5) = 15.675. The frozen diagonals give 10.5625 ≠ 15.675.
- **Observed falsifier deviations caused (preserved):** `comb.I[xx]` 0.477, `comb.I[yy]` 0.484,
  `comb.I[zz]` 0.488 relative (worst at s=0.065).

## Verdict consequence

- The frozen prereg's falsifier FIRED on 7 quantities (E1: 4, E2: 3). **Root cause: agent-side anchor
  derivation errors, NOT exporter defects.** The receipts that exposed them are preserved verbatim.
- After correction: 42/42 absolute comparisons PASS (worst 7.402e-16 relative); all 39 anchor-free
  law/ratio tests PASS (worst 7.896e-16). The exporter-side scaling conclusion is unchanged by this
  erratum because the law/ratio layer never used the faulty anchors.
- Correction receipts: receipts/analysis.json (both layers), receipts/ratio_table.md, receipts/run_log.txt.
