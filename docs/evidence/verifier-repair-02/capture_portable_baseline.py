"""Derive LF oracle from immutable baseline source, never current implementation."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[3]
original=json.loads(Path(__file__).with_name('baseline.json').read_text())
out=Path(__file__).with_name('baseline_lf.json')
assert not out.exists()
source=subprocess.run(['git','-C',str(ROOT),'show',original['base']+':tools/verify_run.py'],
                      capture_output=True,check=True).stdout
rows={}
with tempfile.TemporaryDirectory() as tmp:
    cli=Path(tmp)/'baseline.py'
    cli.write_bytes(source)
    for name,expected in original['fixtures'].items():
        cp=subprocess.run([sys.executable,str(cli),'LightEngine/output/'+name],cwd=ROOT,capture_output=True)
        assert cp.returncode==0 and not cp.stderr
        assert hashlib.sha256(cp.stdout).hexdigest()==expected['stdout_sha256']
        rows[name]=hashlib.sha256(cp.stdout.replace(b'\r\n',b'\n')).hexdigest()
out.write_text(json.dumps({'base':original['base'],'normalization':'CRLF to LF only','fixtures':rows},indent=2),encoding='utf-8')
print('LF-only oracle derived from immutable base; raw Windows hashes also matched.')
