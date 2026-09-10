"""Run once before implementation; refuse overwriting the compatibility oracle."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
out=Path(__file__).with_name('baseline.json')
assert not out.exists()
names=['print_leg_v2_log.txt','print_lever_v6_log.txt','print_leg_v1_log.txt',
       'print_leg_v3_log.txt','print_leg_v3_control_log.txt']
rows={}
for name in names:
    p='LightEngine/output/'+name
    cp=subprocess.run([sys.executable,'tools/verify_run.py',p],cwd=ROOT,capture_output=True)
    assert cp.returncode==0 and not cp.stderr
    rows[name]={'stdout_sha256':hashlib.sha256(cp.stdout).hexdigest(),
                'fixture_sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()}
out.write_text(json.dumps({'base':'cf27528166b7df1e20ddf474396624c8bf7f63a3',
 'python':sys.version,'fixtures':rows},indent=2),encoding='utf-8')
print('Captured five valid fixture stdout hashes before implementation.')
