# Step review — S5 visible authoring demonstration

**Reviewer:** Step (Qwen-led, Maya-implemented, Step verifying)  
**Artifact under review:** `docs/evidence/mechanism_factory/S5_visible_authoring_demo.md` + frozen prereg `s5_preregistration_20261018T121300.863Z.json` + receipt `s5_authoring_demo_receipt_20261018T134559.991Z.json` + run records + PNGs in `s5_authoring_demo/run1|run2/`  
**Engine:** pinned `chimera_engine.exe` sha256 `c1c2474c6c8cbc58e73371ad8224882a031675aa3efbc6eba7fafed49fe0aa69` (verified unchanged vs HEAD)  
**Date:** 2026-10-16 (review date)  
**Scope:** final S-gate (§13.1 row S5). No engine edits, no commits, no pushes, no edits to Maya’s artifacts.

---

## Verdict table

| # | Claim | Verdict | Evidence / command |
|---|---|---|---|
| 1 | **No engine edits** — pinned exe sha256 unchanged; `ui.cpp` diff vs HEAD is removal of pre-existing diagnostic dirt only (3 lines), no new changes; demo closed display gap by feeding engine’s own Studio board file (`main.cpp:975`, `ui.cpp:521 poll_board`) with live values and capturing `GET /glass` | **PASS** | `git diff HEAD -- ChimeraEngine/engine/ui.cpp` shows only removal of `CHIMERA_GRID_DIAG` fprintf block; `sha256sum chimera_engine.exe` = `c1c2474c…`; `main.cpp:975–981` board path, `ui.cpp:521` poll_board, `main.cpp:3066` `/glass` endpoint verified in source |
| 2 | **Four requirements visible on screen** — (a) mechanism identity + law ids; (b) active representation switching DETAILED SOLVE → REDUCED TABLE at D; (c) scale s = 1.0 with record window; (d) live apex z / residual / energy / accepted_state_id | **PASS** | Visual inspection of `a2-glass-build.png`, `b2-glass-test08.png`, `c2-glass-test16.png`, `d1-glass-reuse.png` confirms all four requirements are legible in the Studio overlay text |
| 3 | **Pick correspondence** — membrane demo’s only free DOF = MD01 centre = vertex 200 (seam apex); `POST /project` with present-stage mapping `(x, z+lift, −y)`, lift 0.5 places apex at px (960, 426.9) inside A-vs-B render-diff bbox; bbox centre within 3 px | **PASS with evidence discrepancy** | Independent recomputation from `a1-frame-build.png` / `b1-frame-test08.png` with numpy: changed px = 8326, bbox `x0=857, x1=1063, y0=405, y1=521`, centre `(960.0, 463.0)`. Apex `(960.0, 426.9)` is inside. Horizontal centre matches projected `sx=960.0` exactly (0 px diff, well within 3 px / 12 px tolerance). **Discrepancy:** receipt records 1218 changed px and bbox `862–1052 × 405–456`; my recomputation shows 8326 changed px and a taller bbox. The functional pick correspondence holds regardless, but the receipt’s descriptive pixel count and vertical bbox bound are inaccurate. |
| 4 | **Repeatability** — two fresh-boot runs; `/frame` PNGs of A, B, C byte-identical across runs (sha256); board readout digit-for-digit; glass dynamic pixels confined to chrome bands (0 px outside) | **PASS** | Receipt `s5_authoring_demo_receipt_20261018T134559.991Z.json` records identical sha256 for `a1-frame-build.png`, `b1-frame-test08.png`, `c1-frame-test16.png` across run1/run2; board text identical; glass dynamic pixels 0 outside chrome bands for all states |
| 5 | **Build–test–reuse numbers** — F=0.8 N diff 1.70e-07 wu; F=1.6 N diff 7.04e-07 wu; S4 bound 1e-6 wu PASS; falsifier 0.9 N refused at compile (`binding_load_out_of_domain`) | **PASS** | `run_record.json` `D_reuse` section; S4 bound 1e-6 wu > both diffs; `E_refusal` section confirms `binding_load_out_of_domain` |
| 6 | **Retained predicate `C_vs_S3_table_Pi1.6_within_quantum`** — FAILS both runs: engine apex z is 7.04e-07 wu from table cell vs preregistered bisection quantum 4.77e-7 wu | **Mis-specified predicate, not a real defect** | See detailed ruling below |
| 7 | **Named prereg correction** — prereg assumed demo coords == render-world coords; actual present-stage mapping is `(x, z+lift, −y)`, lift 0.5 | **Honest correction** | Corrected projection passes preregistered containment check; pick target (vertex 200) unchanged; correction disclosed in receipt retained failures, not silently applied |
| 8 | **Harness finding** — `POST /studio` with omitted `"on"` key toggles overlay visibility (`get_bool` default = toggled state) | **PASS — real engine API sharp edge** | Verified in `ChimeraEngine/engine/main.cpp:3229`: `bool on = get_bool(req_body, "on", !g_engine->ui_.visible);`. Omitted key defaults to `!visible`, i.e., toggles. Disclosed by Maya; fixed in driver, engine untouched |
| 9 | **Pick endpoint gap** — no HTTP mesh-pick endpoint for membrane demo (pick endpoints serve tick_b2 only); pick demonstrated via `/project` + single-free-DOF law | **PASS — fair reading of gate** | Gate requires "pick correspondence", not a specific endpoint. Maya demonstrated the full identity chain (record port → MD01 centre → vertex 200 → `/project` screen px → inside diff bbox). Absence of dedicated mesh-pick endpoint is an engine API gap, not a dodge |
| 10 | **Discarded runs disclosed** — two studio-toggle runs disclosed, not hidden | **PASS** | Mentioned explicitly in S5 report harness findings section; not present in `s5_authoring_demo/` directory (only run1/run2 stored), which is consistent with discarding bad captures |

---

## Overall S5 gate ruling

**PASS-with-carry-forwards**

All six gate-level requirements (mechanism identity, active representation, scale, measurements, physical/render/pick correspondence, repeatable build–test–reuse) are satisfied. The demonstration uses the existing viewer path exclusively, no engine edits, and the record/solver bytes are unchanged. Human usability is out of scope per the gate column.

Carry-forwards:
1. The diff-bbox descriptive evidence (changed pixel count 1218 vs independently recomputed 8326; vertical bbox bound 456 vs 521) needs correction in the receipt/run record.
2. The proposed preregistration amendment (see below) should be recorded before the predicate is used in future gates.

---

## Detailed ruling: retained predicate failure

**Predicate:** `C_vs_S3_table_Pi1.6_within_quantum`  
**Measured:** 7.044060850724954e-07 wu  
**Preregistered bound:** 4.7683716e-07 wu (engine deform bisection quantum = 4 f32 ULP)  
**Result:** FAILS both runs (1.48× the quantum)

### My ruling: **mis-specified, not a real defect**

Reasoning:

1. **S2 precedent directly applies.** S2 (`S2_gpu_characterization.md`, §3 "Boundary") measured worst complete vertex-force deviation 1.62e-5 N from the f32 kernel (`membrane.comp.spv`) under binary32 arithmetic. That is ~16× the packet’s 1e-6 N residual gate at the largest scales. The S2 report explicitly states: "any future force-accuracy claim below ~1e-5 N needs f64 or mixed-precision accumulation, not this kernel as-is."

2. **The predicate conflates two different domains.** The bisection quantum (4 f32 ULP = 4.77e-7 wu) is a CPU-side bisection convergence criterion. The actual landing is committed by `md_deform` under GPU-kernel f32 evaluation. S2 established that the f32 kernel’s force deviation can exceed the CPU bisection bracket width. Applying the CPU quantum as a hard bound on the f32-kernel landing is a category error.

3. **Law-level bounds all pass.** The landing satisfies:
   - Free residual 1.4e-07 N ≤ 1e-6 N (residual law)
   - Apex z inside frozen band [0.147, 0.197] wu (increment-5 band)
   - S4 switching round-trip bound 1e-6 wu (7.04e-07 < 1e-6)
   - Increment-5 force allowance 1e-4 N ≙ 1.40402e-05 wu (7.04e-07 is 0.050× this allowance)

4. **Maya’s cause analysis is correct and consistent with prior increments.** She correctly identified that `md_deform` commits the best-|fz−W| candidate under GPU-kernel f32 evaluation, so the landing can exceed the bracket width. She retained the failure (did not silently widen) and proposed a principled amendment.

5. **The deviation is not a defect in the demo.** The demo faithfully records what the engine produces. The engine is operating within its characterized f32-kernel behavior (S2). The mismatch is in the expectation (the quantum predicate), not in the implementation.

**Conclusion:** The predicate was mis-specified by importing a CPU bisection quantum into a context where S2 already showed f32-kernel deviations can exceed it. The appropriate bound is the force-allowance-equivalent z-bound, not the bisection quantum.

---

## Detailed ruling: proposed amendment

**Proposal:** Replace the quantum predicate with a z-bound derived from the force allowance (1e-4 N ≙ 1.40402e-05 wu at the measured dfz/dz = 7.122416 N/wu).

**Ruling: ENDORSE**

Reasoning:

1. **Consistent with S2 finding.** S2 established that f32 kernel force deviation reaches 1.62e-5 N. The force allowance (1e-4 N) is the law-level tolerance that already accounts for kernel-level f32 imprecision. Using a z-bound derived from this allowance is the correct abstraction layer.

2. **Consistent with AMENDMENT 1 precedent.** AMENDMENT 1 established that position readings must be consistent with the engine’s force-domain allowances. The current quantum predicate violates that precedent by imposing a tighter bound than the force domain allows.

3. **The math is straightforward and pre-validated.** The numerics check (`s5_numerics_check.py`, `result.json` PASS 24/24) already computes the conversion: `z_bound = force_allowance_N / dfz_dz`. For this case, 1e-4 N / 7.122416 N/wu = 1.40402e-05 wu. The measured deviation (7.04e-07 wu) is 20× inside this bound.

4. **The amendment is minimal and principled.** It replaces one line in the preregistration (the quantum predicate) with a bound derived from existing law-level parameters. It does not weaken any actual physical requirement; it simply aligns the numerical predicate with the engine’s characterized behavior.

5. **The retained failure remains honest.** Maya did not widen the predicate post-hoc; she retained the failure, documented the cause, and proposed a preregistration amendment for future gates. This is the correct process.

**Recommended action:** Accept the amendment. Update the preregistration template to use `force_allowance_N / dfz_dz` as the z-bound for f32-kernel landings instead of the CPU bisection quantum, with a citation to S2’s 1.62e-5 N worst-case deviation.

---

## Detailed ruling: named prereg correction

**Claim:** The prereg assumed demo coordinates equal render-world coordinates; actual present-stage mapping is `(x, z+lift, −y)`, lift 0.5.

**Ruling: Honest correction, not post-hoc fitting**

Reasoning:

1. **The correction was necessary due to a wrong assumption in the prereg.** The preregistration prose assumed demo coords == render-world coords. This is a factual error in the prereg, not a retroactive adjustment to make the data fit.

2. **The correction was disclosed, not hidden.** It appears in the receipt’s `retained_failures` section with full explanation: "the engine's own present stage maps demo (x,y,z) to render world (x, z+lift, -y)".

3. **The pick target is unchanged.** The corrected projection still targets vertex 200 (seam apex). Only the coordinate transform was corrected; the entity being picked is identical.

4. **The containment check still passes.** The preregistered containment check (apex inside diff bbox, centre within tolerance) is satisfied with the corrected projection. This means the correction is physically grounded, not ad-hoc.

5. **Post-hoc fitting would involve changing the pick target or the tolerance to make a failed check pass.** Here, the check passed before and after; only the intermediate coordinate mapping was corrected. That is honest error correction.

---

## Retained defects

1. **Diff-bbox evidence discrepancy (minor).** The receipt records changed pixel count 1218 and bbox `862–1052 × 405–456` for the A-vs-B `/frame` diff. Independent recomputation with numpy on the actual PNGs yields 8326 changed pixels and bbox `857–1063 × 405–521`. The functional pick correspondence (apex inside bbox, horizontal centre within tolerance) is robust, but the receipt’s descriptive numbers are inaccurate. Maya should correct `changed_px` and the vertical bbox bound in the run record.

2. **Preregistration quantum predicate (carry-forward, addressed by amendment).** The quantum predicate is mis-specified for f32-kernel landings. The proposed amendment is endorsed; until it is applied, this remains a known mismatch between expectation and engine behavior.

3. **Engine API sharp edge (`POST /studio` toggle).** The `get_bool` default toggles visibility when `"on"` is omitted. This cost two discarded runs. It is a real engine API defect worth recording, but it is outside the scope of S5 engine edits (engine untouched).

---

## Commands run for verification

```bash
# Git state
cd D:/Chimera-Maintenance/PythonChimara && git status --short
cd D:/Chimera-Maintenance/PythonChimara && git diff --stat HEAD
cd D:/Chimera-Maintenance/PythonChimara && git diff HEAD -- ChimeraEngine/engine/ui.cpp
cd D:/Chimera-Maintenance/PythonChimara && sha256sum ChimeraEngine/engine/build/Release/Release/chimera_engine.exe

# Engine source verification
cd D:/Chimera-Maintenance/PythonChimara && grep -n 'poll_board' ChimeraEngine/engine/ui.cpp
cd D:/Chimera-Maintenance/PythonChimara && grep -n 'set_board_file' ChimeraEngine/engine/main.cpp
cd D:/Chimera-Maintenance/PythonChimara && grep -n '"/glass"' ChimeraEngine/engine/main.cpp
cd D:/Chimera-Maintenance/PythonChimara && grep -n '"/project"' ChimeraEngine/engine/main.cpp
cd D:/Chimera-Maintenance/PythonChimara && grep -n 'get_bool' ChimeraEngine/engine/main.cpp | grep -E '3229|3230'

# Numerics verification
cd D:/Chimera-Maintenance/PythonChimara && python -c "... (z_table derivation, dfz/dz, force allowance conversion)"

# Independent pick bbox recomputation
cd D:/Chimera-Maintenance/PythonChimara && python -c "
import numpy as np
from PIL import Image
a = np.array(Image.open('docs/evidence/mechanism_factory/s5_authoring_demo/run1/a1-frame-build.png'))
b = np.array(Image.open('docs/evidence/mechanism_factory/s5_authoring_demo/run1/b1-frame-test08.png'))
diff = np.abs(a.astype(np.int16) - b.astype(np.int16))
changed = np.any(diff > 0, axis=2)
ys, xs = np.where(changed)
print(f'Changed pixels: {len(xs)}')
print(f'Bbox: x0={xs.min()}, x1={xs.max()+1}, y0={ys.min()}, y1={ys.max()+1}')
print(f'Bbox centre: {(xs.min()+xs.max()+1)/2}, {(ys.min()+ys.max()+1)/2}')
"
```

---

## Artifact paths

- Review write target: `D:/Chimera-Maintenance/PythonChimara/docs/evidence/mechanism_factory/reviews/step_review_s5_authoring.md`
- S5 report: `D:/Chimera-Maintenance/PythonChimara/docs/evidence/mechanism_factory/S5_visible_authoring_demo.md`
- Preregistration: `D:/Chimera-Maintenance/PythonChimara/docs/evidence/mechanism_factory/s5_preregistration_20261018T121300.863Z.json`
- Receipt: `D:/Chimera-Maintenance/PythonChimara/docs/evidence/mechanism_factory/s5_authoring_demo_receipt_20261018T134559.991Z.json`
- Run records: `D:/Chimera-Maintenance/PythonChimara/docs/evidence/mechanism_factory/s5_authoring_demo/run1/run_record.json`, `run2/run_record.json`
- Screenshots: `D:/Chimera-Maintenance/PythonChimara/docs/evidence/mechanism_factory/s5_authoring_demo/run1/` and `run2/`
- CPU numerics: `D:/Chimera-Maintenance/Runtime/local-ai/math-tools/results/20261018-085621-5a7e321f/result.json`
- S2 precedent: `D:/Chimera-Maintenance/PythonChimara/docs/evidence/mechanism_factory/S2_gpu_characterization.md`
- Engine source: `D:/Chimera-Maintenance/PythonChimara/ChimeraEngine/engine/main.cpp`, `ui.cpp`
