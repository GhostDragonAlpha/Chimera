# H15 GUARD-THRESHOLD ANALYSIS — will the coming degenerate-split guard eat the gallery?

Agent H15, 2026-09-14. The guard (mission brief + H10's walker audit,
commit 62f60378): a sealed-cell guard in `ChimeraEngine/engine/membrane_tick.cpp`
that REFUSES splits producing a daughter cell with V below ~0.5 % of the
parent. H10's audit names its actual target: the LIVE bear's lesson-6 pose
state inflates a degenerate cell4 (V0 ~ 3e-9 m³ — a junk split product) to a
permanent 1.6228 GPa. **That junk cell does not exist anywhere in the gallery
flow.** The gallery's job is the converse: prove the guard does not refuse or
distort LEGITIMATE seals.

## Where the guard lands vs where the gallery walks

- `MembraneTick::split()` (membrane_tick.cpp:944, endpoint `/tick_seal_split`)
  — flood-fill component split; today it refuses `comps < 2` and any
  component with `!(v > 0)`. The volume guard lands HERE. The gallery flow
  NEVER calls `/tick_seal_split`.
- `MembraneTick::seal()` (membrane_tick.cpp:1048, endpoint `/tick_seal`) —
  the mitosis cut-and-weld the gallery calls ONCE per shape at mid-height.
  Today it refuses daughters signing negative (`!(vl > 0) || !(vu > 0)`,
  line 1263). If the guard's threshold check is implemented in a helper
  shared with split() — or is also bolted onto the daughter-volume check —
  the seal path inherits it, which is exactly why the gallery must re-pass
  on the new binary.

## The recorded cell volumes vs the 0.5 % threshold (official baseline)

| creature | V_whole | daughter volumes | % of parent (each) | margin to 0.5 % floor | smallest ABSOLUTE daughter |
|----------|--------:|-----------------|-------------------:|----------------------:|---------------------------:|
| blob     | 8.33391 | 4.16691 / 4.16688 | 49.9995 / 49.9991 | **100x** | 4.167 m³ |
| torus    | 7.34284 | 3.67145 / 3.67145 | 50.0004 / 50.0004 | **100x** | 3.671 m³ |
| capsule  | 1.69175 | 0.84587 / 0.84587 | 49.9996 / 49.9999 | **100x** | **0.846 m³ (smallest in the gallery)** |
| peanut   | 0.90617 | 0.45309 / 0.45308 | 50.0001 / 49.9999 | **100x** | 0.453 m³ |
| rbox     | 8.47347 | 4.23674 / 4.23676 | 50.0001 / 50.0003 | **100x** | 4.237 m³ |

**The mid-height seal cuts every gallery shape in HALF.** The nearest gallery
daughter sits 100x above a 0.5 %-of-parent floor. Reference-basis hazard
checked: even a guard that wrongly measures against the WHOLE creature's
first-seal volume (`vol_whole0_`) instead of the cell being split still sees
50 % — safe under either basis. An ABSOLUTE floor of 0.5 % of the smallest
gallery parent (0.5 % x 0.90617 = 0.0045 m³) is still 190x below the smallest
capsule daughter (0.846 m³). **No gallery shape produces cells anywhere near
the threshold in the standard flow. No shape is predicted to trip the guard.**

## The risk list — what the after-run watches, by name

1. **TORUS (watch closest — the multi-loop seal).** Only shape with
   `seal_loops=2` (annulus cut, 128 cuts, 124 caps). If the guard's
   bookkeeping counts loop cap-welds or per-loop partial volumes as
   "components", the torus is where it misfires FIRST. A wrong refusal here
   reads as: `/tick_seal` → `ok:false` (possibly naming degeneracy), or
   `n_cells != 2`, or `seal_loops != 2`, or a daughter set that is not
   3.67145 + 3.67145.
2. **CAPSULE (smallest absolute volumes).** Smallest parent (1.69 m³) and
   smallest daughters (0.846 m³) — nearest to any ABSOLUTE floor, and its C1
   cylinder/hemisphere seams (96 cuts, 94 caps) are the second edge case. If
   the guard carries any absolute-epsilon term, the capsule is the gallery's
   sentinel for it.
3. **PEANUT (waist cut).** The mid-height plane passes exactly through the
   Gaussian waist (radius 0.225 m at y=0) — the smallest SEAL CROSS-SECTION
   in the gallery (cap area ~0.159 m²). Not near the volume floor, but it is
   the thinnest cut; if the guard gains any per-cut-area term, watch the
   peanut's caps (126) and daughters (0.45309/0.45308).
4. **ALL SHAPES — the triage rule.** The gallery NEVER offers a junk split:
   every daughter it creates is 50 % of parent. Therefore, in this protocol,
   **ANY degenerate/refusal string on ANY gallery shape is a REGRESSION, not a
   correct refusal.** The driver's guard-watch (strings `degenerate`, `refus`,
   `guard` scanned in every import/joints/classify/vertbind/seal response) is
   the tripwire; baseline run recorded ZERO hits.

### Triage table for the after-run

| Observation on the new binary | Meaning |
|-------------------------------|---------|
| 5/5 ALIVE, expected table matched, zero guard strings | guard landed clean; aliveness re-proven |
| `/tick_seal_split` refuses WITH a degenerate message | guard working as designed (gallery never calls it — informational only) |
| `/tick_seal` ok:false or n_cells/loops/caps off, with `degenerate` string, on ANY shape | **GUARD BROKE A LEGITIMATE SEAL** — the daughters are 50 % of parent; escalate to the engine owner with that shape's row + `engine_logs/` |
| seal record matches but dimple != 0.198944 +/- 0.005 or displacement routing changed | the build window changed the touch/travel path, not just the guard — record per BASELINE.md bars and flag OFF-EXPECTED |
