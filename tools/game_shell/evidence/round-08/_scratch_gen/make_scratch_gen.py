"""Build a scratch copy of tools/rig_factory_fit.py with ONLY the output paths
redirected (repro gate / regeneration harness). Source logic untouched.

Usage: python make_scratch_gen.py OUT_PY
"""
import sys, io

SRC = r"E:/PythonChimera/tools/rig_factory_fit.py"
SCRATCH = r"E:/PythonChimera/tools/game_shell/evidence/round-08/_scratch_gen"

src = open(SRC, encoding='utf-8').read()
subs = [
    ("ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))",
     'ROOT = r"E:\\PythonChimera"'),
    ("PACK_OUT = os.path.join(ROOT, 'Saved/meshes/monkey_joints.bin')",
     f"PACK_OUT = r'{SCRATCH}\\monkey_joints_repro.bin'"),
    ("NPZ_OUT = os.path.join(ROOT, '.tmp/skeleton/joints_pack.npz')",
     f"NPZ_OUT = r'{SCRATCH}\\joints_pack.npz'"),
    ("MJCF_OUT = os.path.join(ROOT, '.tmp/skeleton/chimera_primate.xml')",
     f"MJCF_OUT = r'{SCRATCH}\\chimera_primate.xml'"),
    ("ROM_OUT = os.path.join(ROOT, '.tmp/skeleton/factory_rom_r2.json')",
     f"ROM_OUT = r'{SCRATCH}\\factory_rom_r2.json'"),
    ("REPORT = os.path.join(ROOT, '.tmp/skeleton/rig_fit_report.txt')",
     f"REPORT = r'{SCRATCH}\\rig_fit_report.txt'"),
]
if len(sys.argv) > 2:  # optional: redirect the referee verdict input to a scratch file
    subs.append((
        "_ref_path = os.path.join(ROOT, '.tmp/skeleton/rom_referee_r2.json')",
        f"_ref_path = r'{sys.argv[2]}'"))
for old, new in subs:
    assert src.count(old) == 1, f'patch anchor not unique/missing: {old!r}'
    src = src.replace(old, new)
open(sys.argv[1], 'w', encoding='utf-8').write(src)
print('scratch generator written:', sys.argv[1])
