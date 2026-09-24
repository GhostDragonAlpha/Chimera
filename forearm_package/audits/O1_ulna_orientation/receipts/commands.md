# O1 — EXACT COMMANDS (receipts index)

Environment: Windows, Git Bash; `PYTHONDONTWRITEBYTECODE=1` on every run; python 3.14 +
NumPy + matplotlib (Agg backend set in-script BEFORE pyplot import — CPU-only software
rendering; NO OpenGL/Vulkan/WebGL/GPU context anywhere in this audit). All inputs
read-only; all writes confined to `audits/O1_ulna_orientation/`.

```bash
# 0. brief copied verbatim as the first action (Write tool): brief.md

# 1. module copy for baseline inputs (byte-identical to baseline mesh_target.py except
#    the two input path constants, repointed to the read-only snapshot; same file C3 used)
mkdir -p work
cp ../../C3_independent_challenge/work/mesh_target_c3.py work/mesh_target_o1.py

# 2. bone-mesh identity probe + bone-surface volar/dorsal anatomy  -> receipts/o1_ulna_mesh_probe.json
PYTHONDONTWRITEBYTECODE=1 python scripts/o1_probe_ulna_mesh.py      | tee receipts/o1_ulna_mesh_probe_run.log
#    (run twice: first run's frozen all-10 rule FIRED; refined anchor-class rule recorded in the same receipt; log appended)

# 3. target pack joints (facing facts)                              -> printed + inside o1_target_olecranon.json
PYTHONDONTWRITEBYTECODE=1 python - <<'PY'
import sys; sys.path.insert(0, 'work')
from mesh_target_o1 import MonkeyTarget
BASE = r'E:/PythonChimera/forearm_package/baseline_snapshot'
mt = MonkeyTarget(birth_path=BASE+'/inputs/monkey_birth.bin', pack_path=BASE+'/inputs/monkey_joints.bin')
print('birth sha', mt.birth_sha)
for n in mt.names: p = mt.joint_pos(n); print(f'{n:14s} x={p[0]:+.4f} y={p[1]:+.4f} z={p[2]:+.4f}')
PY

# 4. source dorsovolar split + U-STR frame geometry                  -> receipts/o1_source_split.json
PYTHONDONTWRITEBYTECODE=1 python scripts/o1_source_split.py         | tee receipts/o1_source_split_run.log

# 5. target olecranon vertex-band test + facing                     -> receipts/o1_target_olecranon.json
PYTHONDONTWRITEBYTECODE=1 python scripts/o1_target_olecranon.py     | tee receipts/o1_target_olecranon_run.log
#    (superseded for the elbow claim by 6: the rig's elbow_R band extends to t=105.6 mm = 41 mm past the wrist)

# 6. DECISIVE target test: exact-section directed protrusion        -> receipts/o1_target_sections_directed.json
PYTHONDONTWRITEBYTECODE=1 python scripts/o1_target_sections_directed.py | tee receipts/o1_target_sections_directed_run.log

# 7. figures (Agg)                                                   -> figures/*.png + receipts/o1_figures_note.txt
PYTHONDONTWRITEBYTECODE=1 python scripts/o1_figures.py              | tee receipts/o1_figures_run.log

# 8. combine: the U-STR roll SIGN                                    -> receipts/o1_combine_sign.json
PYTHONDONTWRITEBYTECODE=1 python scripts/o1_combine_sign.py         | tee receipts/o1_combine_sign_run.log

# 9. band-vertex axial location (cross-wave correction; inline)
PYTHONDONTWRITEBYTECODE=1 python - <<'PY'
import sys; sys.path.insert(0, 'work')
import numpy as np
from mesh_target_o1 import MonkeyTarget
BASE = r'E:/PythonChimera/forearm_package/baseline_snapshot'
mt = MonkeyTarget(birth_path=BASE+'/inputs/monkey_birth.bin', pack_path=BASE+'/inputs/monkey_joints.bin')
e = mt.joint_pos('elbow_R'); w = mt.joint_pos('wrist_R')
a = (w-e)/np.linalg.norm(w-e)
verts = mt.band_verts('elbow_R'); rel = verts - e
perp = rel - np.outer(rel@a, a); d = np.linalg.norm(perp, axis=1)
for i in np.argsort(-d)[:10]:
    print(f't={rel[i]@a*1000:7.1f} mm  perp={d[i]*1000:6.2f} mm')
PY
#    -> top-10 band vertices all at t = 89.5..97.8 mm (25-33 mm PAST the wrist: paw skin)

# 10. baseline integrity (end of work)
git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot   # (empty)
git -C E:/PythonChimera rev-parse --short HEAD                                    # 43b599a7
```

Citations: `receipts/external_citations.md` (+ attempts log `receipts/o1_citation_search_attempts.log`).
Existing-image inventory (negative result): `receipts/o1_existing_images_inventory.md`.
