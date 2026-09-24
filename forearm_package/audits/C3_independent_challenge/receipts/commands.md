# C3 receipts — exact commands

Environment: Windows, Git Bash, python 3.14 + NumPy, PYTHONDONTWRITEBYTECODE=1.
Baseline READ-ONLY: all reads via `E:/PythonChimera/forearm_package/baseline_snapshot/`.
The target-mesh loader ran through a byte-identical module copy
(`work/mesh_target_c3.py` = baseline `code/mesh_target.py`, only the two path
constants repointed to the snapshot inputs; hashes asserted in-run:
birth `550a5b3e…aabfa3c`, pack `74b3ab04…50c1662` == MANIFEST.json:153/158).

## Commands (run from audits/C3_independent_challenge/)

1. First action:
   ```
   mkdir -p …/audits/C3_independent_challenge/{scripts,receipts,work}
   # brief.md copied VERBATIM (Write tool) — frozen preregistration predates all runs
   ```

2. Source-side geometry (ulna sites, roll witnesses, hand planes, chain vectors):
   ```
   PYTHONDONTWRITEBYTECODE=1 python scripts/c3_source_geometry.py
   ```
   console log: `receipts/c3_source_geometry_run.log`
   full data:    `receipts/c3_source_geometry.json`  (cited as C3-S1)

3. Target-side sections (forearm tube, elbow band, paddle):
   ```
   PYTHONDONTWRITEBYTECODE=1 python scripts/c3_target_sections.py
   ```
   console log: `receipts/c3_target_sections_run.log`
   full data:    `receipts/c3_target_sections.json`  (cited as C3-S2)

4. Baseline integrity (start and end):
   ```
   git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot
   # empty both times; HEAD 276db875
   ```

## Method notes bound into the receipts

- Sections: exact triangle-plane intersection segment endpoints (no slab bias, no
  bridging), radius-capped about the axis line (45 mm forearm / 40 mm paddle).
- Principal azimuths mod 180°; bootstrap = 200 point resamples per station (seed 0);
  circular std via double-angle (mod 180) / direct (signed) statistics.
- Both ulna-axis DIRECTIONS (+a/−a): all reported magnitudes and mod-180 lines are
  invariant under the sign flip by construction (stated in the JSON `method_note`);
  the source-axis direction question itself is C1's and was not assumed.
- T6 utility-ban: no moment arm, path length, or transmission quantity computed or
  cited anywhere in scripts/ or receipts/.
