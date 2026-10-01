# H8 "world-doctor" — the zero-volume cell 4 (V≈0, P=1.62 GPa): diagnosed, reproduced, guarded

Fleet SHIP run, 2026-09-14. Workspace `E:\ChimeraWork\slot-01`, branch
`astra/tasks/matter-kernel-format-01`. LIVE engine 8107 touched via GET only.
Scratch engines: private ports 8138/8139, isolated cwds (G4's throwaway
recipe: `--hidden` only — `--no-restore` fail-fasts 0xC0000409 on this
lineage), killed after each run. The live world was re-verified untouched
after every scratch run.

## VERDICT

Cell 4 is a **degenerate daughter created by seal #6** — the second
consecutive `POST /tick_seal {"y":0.338,"cell":0}` in
`session_snapshot/tick_seal_history.log`. It is a closed double-layer
"pancake": 650 pieces, every slot lying IN the cut plane
(`ylo == yhi == 0.338`), rest volume **v0 = 4.65502e-09 m³ = 1.62e-8 of its
parent**. The seal admitted it because the only daughter acceptance check
refuses *non-positive* volume, and 4.655e-9 is positive — it is the float
noise of the flat double layer's divergence sum. The kappa water law then
turns every pose into GPa: `p = (v0−v)/(kappa·v0)` with v0 ~ 5e-9 amplifies
a 1.2e-9 m³ pose wobble to **1.62278 GPa** (the three live probe captures),
and my A/B measured **2.6096 GPa with V flipping negative** under a 40°
knee. At rest P reads 0 (the rest blend reproduces v0 bit-exactly), which
is why the world "looks fine" between lessons.

Scratch reproduction was **byte-identical**: replaying the live history
(entries 1-3 foundation cuts, then the repeats) on a clean engine created
cell 4 with v0 = 4.65502e-09, pieces=650, ylo==yhi==0.338 — the exact live
record.

## THE LIVE RECORD (GET /tick_state, 2026-09-14 — `tick_state_live_cell4.json`)

```
n_cells 5  sealed true  conserve_pct -0.000117
0 {v0 0.287914,  V 0.287914,  P 0, pieces 5550,  ylo -0.019507, yhi 0.338}   feet
1 {v0 12.5091,   V 12.5091,   P 0, pieces 26442, ylo 3.415,     yhi 9.97118}  upper body
2 {v0 0.693006,  V 0.693006,  P 0, pieces 5604,  ylo 1.903,     yhi 3.415}    torso
3 {v0 0.334578,  V 0.334578,  P 0, pieces 1668,  ylo 0.338,     yhi 1.903}    legs
4 {v0 4.65502e-09, V 4.65502e-09, P 0, pieces 650, ylo 0.338, yhi 0.338}      THE PANCAKE
```

Seal history (log copy: `tick_seal_history_live_copy.txt`; NOTE it grows —
see "secondary defect" below): entry 1 `{"y":3.415}` (whole → cells 0+1),
entry 2 `{"y":1.903,"cell":0}` (+cell 2), entry 3 `{"y":0.338,"cell":0}`
(+cell 3, the feet), then 48 repeats of the same four intents. The journal
only records `ok:true` responses; the bisect shows entry 6 — the FIRST
repeat of the 0.338 cut — is the one that succeeds and creates cell 4
(`bisect_timeline_NOGUARD.jsonl`).

## MECHANISM (membrane_tick.cpp, pre-guard line refs at HEAD 569083bb)

1. **seal() forces new cut slots exactly onto the plane**
   (`py.push_back(y)`, line 1150). Cell 0 after entry 3 therefore holds cap
   slots with py == 0.338f bit-exactly.
2. **Every LATER seal() re-evaluates those slots from the blend table over
   rest9** (`py[s] = Σ wᵢ·rest9[vᵢ]`, lines 1090-1096). Float rounding
   drifts them ~1 ulp; in this constellation ALL of cell 0's slots evaluate
   strictly below 0.338f, so the plane-crossing guard
   `if (y <= ymin || y >= ymax) return false;` (lines 1104-1109) does NOT
   fire on the repeat: ymax < y by an ulp.
3. **The re-cut through a slot layer** classifies the old in-plane cap
   triangles as "above" (`bl[j] = py < y`, line 1156) and produces flat /
   zero-area products; the weld law (lines 1196-1229) chains the new
   segments into 2 loops (the two ankle cross-sections) and fans new caps.
   The upper daughter receives ONLY in-plane pieces: 650 pieces, all slots
   at exactly y (hence the exported `ylo == yhi == 0.338`).
4. **The only daughter acceptance check is orientation**
   `if (!(vl > 0.f) || !(vu > 0.f)) return false;` (line 1263; split()'s
   component check is the same class, line 1030). The pancake's signed
   divergence sum is +4.655e-09 — noise, but positive — so it PUBLISHES as
   a sealed cell. There is no minimum-volume floor anywhere.
5. **The poison ships through the kappa law** in step()
   (`c.p = (c.v0 − v)/(kappa_·c.v0)`, line 624; kappa_ = 4.6e-10, water
   25 °C, membrane_tick.hpp:187). v→0 ⇒ p→1/kappa = 2.174 GPa = 145× the
   skin yield (yield_pa_ 15 MPa, hpp:141). With v0 = 4.655e-9, the live
   pose-wobble (v ≈ 0.25·v0) yields exactly the observed 1.62278 GPa; the
   sign flip under my A/B pose yields 2.6096 GPa.
6. **Who reads it**: gait's pressure witness `gait_p_max_ = max|P|`
   (lines 1701-1703) can never come back under GAIT_P_RELAX_PA (50 kPa,
   line 33); the lesson "every cell < 1000 Pa" calm predicate can never
   pass — matches H10's audit and the R4 walk logs
   (`cell4=1622780000` in every lesson peak).

## THE GUARD (coded; `ChimeraEngine/engine/membrane_tick.cpp` + `.hpp`)

One law at all three sites — **a sealed cell under 0.5% of its parent's
rest volume is not anatomy** — refused BY NAME:

- `SEAL_DEGENERATE_FRAC = 0.005f` (hpp:205) with the derivation comment.
  **Threshold derivation (measured separation, not taste)**: real daughters
  on this creature are 9.51%, 47.3%, 52.7%, 46.3%, 53.8% of their parents
  (bisect entries 1-3); the degenerate daughter is 1.62e-8 of its parent —
  nine orders below. The mission-named 0.5% sits 19× below the smallest
  real daughter and ~3e5 above the noise. In pressure terms the guarded
  singularity is p→1/kappa = 2.17 GPa vs the 15 MPa skin yield.
- **seal() admission** (cpp:1292-1303, after the orientation check): either
  daughter < 0.5% of the cut parent's v0 (first cut: parent = vl+vu) →
  `seal_refusal_ = "degenerate_split"`, return false. Nothing was
  published; the parent stays intact; the replay is idempotent.
- **split() admission** (cpp:1044-1049): any component < 0.5% of the split
  parent's v0 refuses the whole split by name, parent intact.
- **The live floor** (cpp:628-640, the per-tick volume block): a cell whose
  LIVE volume reads < 0.5% of its own v0 is flagged
  `c.degenerate = true` and its pressure is WITHHELD (`p = 0`) — the
  export carries `"degenerate":true` instead of an absurd P.
- **Named export**: `"seal_refusal"` in /tick_state (cpp:1999) and
  `"degenerate"` per cell (cpp:2046); `seal_refusal_` clears on a clean cut
  (cpp:1348) and on init (cpp:196).

## FALSIFIER (named before the run; both arms measured on scratch)

> WITHOUT the guard, replaying the live seal history on a clean engine
> creates the degenerate cell (byte-identical v0) and a 40° knee pose
> drives it past 1e9 Pa; WITH the guard the same history is refused by
> name, the cell count stays 4, volumes stay conserved < 0.1%, and no cell
> exceeds finite sub-GPa pressures under the same pose.

**HOLDS on both arms.**

| arm | history replay | 40° knee (pin 15) peak |P| |
|---|---|---|
| NO-GUARD (pristine HEAD build) | 5 cells; cell 4 v0 = 4.65502e-09, ylo==yhi==0.338 (byte-identical to live) | **2,609,590,000 Pa** on cell 4, V = −9.33e-10 (sign flipped) (`ab_pose_noguard.json`) |
| GUARDED | entry 6 refused, `seal_refusal = "degenerate_split"`, 4 cells | **89,701,800 Pa** on cell 0 (real water law on a real volume, V = 0.276) (`ab_pose_guarded.json`) |

Conservation (guarded): Σv0 = 13.824598 vs V_whole 13.8246 →
conserve_pct = −0.000117% (< 0.1% bar). Cell tables bit-identical to the
pre-poison state. The same pose window on the live 5-cell world is
documented at 1.62278 GPa (R4 walk, H5 dryrun resp.jsonl) — reproduced
first-party at 2.61 GPa here.

## RESTORE RECIPE (verified on scratch; for the lead's build window)

**Path A — no reset needed (VERIFIED, `restore_guarded_run.json`):**
1. Stop the engine (the operator's call), rebuild with the guarded
   `membrane_tick.cpp/.hpp`:
   `cmake -S ChimeraEngine/engine -B <dir> -A x64 -DVULKAN_SDK=C:/VulkanSDK/1.4.328.1`
   then `cmake --build <dir> --config Release --target all_shaders` and
   `--target chimera_engine`. (The post-build shader-copy step can fail
   intermittently — if `Release/shaders/*.spv` is missing, copy
   `<dir>/shaders` → `<dir>/Release/shaders` by hand; 25 .spv files.)
2. Start normally (`chimera_engine.exe 8107 --hidden`), same
   `session_snapshot/`. Boot restore replays: blobs ok; the 3 foundation
   seals ok; ALL 48 repeats refused (the degenerate one BY NAME).
3. Result: the clean 4-cell sealed creature — feet / legs / torso / upper
   body — volumes bit-identical to pre-poison, all `degenerate:false`,
   `seal_refusal:"degenerate_split"` visible in GET /tick_state.
4. Optional hygiene (engine stopped): trim
   `session_snapshot/tick_seal_history.log` to its first 3 lines (the
   foundation cuts) — see the secondary defect below.

**Path B — full clean-slate rebuild (for growing the 15-cell target fresh):**
1. On a RUNNING guarded engine: `POST /session {"op":"clear"}` (deletes the
   blobs + history; the engine is born empty on purpose), or delete
   `session_snapshot/` while stopped.
2. Re-import the creature: `python tools/classify_run.py http://127.0.0.1:8107`
   (posts /mesh_bin, /tick_joints, /tick_classify, /tick_vertbind — the
   same bytes the snapshot blobs hold; `--report` runs offline).
3. Re-seal the anatomy by named cuts — the verified live sequence:
   `POST /tick_seal {"y":3.415}` → `{"y":1.903,"cell":0}` →
   `{"y":0.338,"cell":0}` (tools/seal2_run.py, tools/mitosis_run.py drive
   the M1-M4 verification; tools/gravity_test.py re-verifies THE FALL on
   the sealed body). Every further cut is now guarded: a degenerate
   daughter is refused by name instead of becoming the next cell 4.

## SECONDARY DEFECTS NAMED (NOT touched — other owners)

- **main.cpp journal re-journaling** (main.cpp:3370-3377 + the boot-restore
  retry loop, main.cpp:3430-3452): restore replays go through the same
  dispatch, so every ok:true seal re-appends to tick_seal_history.log.
  Measured: the live log grew 39 → 51 during this session, and one guarded
  restore boot appended +3 (51 → 54). With the guard only clean cuts
  re-journal, but the file still inflates every boot. Fix owner: main.cpp
  (the replay path should not journal).
- **Pose auto-reset**: during the A/B a held /tick_pose decayed back to
  rest within ~2-3 s (the lesson layer's own reset). Documented so the
  A/B window (4 s sampling) is read correctly; owner: the lesson/judge
  layer.

## RUN ARTIFACTS

- `tick_state_live_cell4.json`, `state_live.json` — live captures (GET only)
- `tick_seal_history_live_copy.txt` — the poisoned history (51 lines at copy time)
- `bisect_timeline_NOGUARD.jsonl` / `bisect_final_state_NOGUARD.json` — entry-by-entry repro; entry 6 creates the pancake
- `bisect_timeline_GUARDED.jsonl` — same replay under the guard; refused by name from entry 6 on
- `ab_pose_noguard.json` / `ab_pose_guarded.json` — the falsifier A/B under an identical 40° knee pose
- `restore_guarded_run.json` — boot restore over the poisoned snapshot → clean 4-cell world
- `repro.py`, `ab_pose.py`, `pose_probe.py` — the drivers (G4 throwaway recipe)
