import argparse, hashlib, json, shutil, subprocess, tempfile, sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
with tempfile.TemporaryDirectory() as td:
    dst=Path(td)/"v1"; src=ROOT/"docs/evidence/elastic_foundation/fixtures/v1"
    shutil.copytree(src,dst)
    test=subprocess.run(["python","-m","unittest","tools.elastic_foundation.test_units_contract"],cwd=ROOT,capture_output=True,text=True)
    from tools.elastic_foundation import verify_fixtures
    out=[]
    import contextlib,io
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf): code=verify_fixtures.run(SimpleNamespace(version="v1",all=False),fix_root=Path(td))
    out.append(buf.getvalue())
    report={"commands":["python -m unittest tools.elastic_foundation.test_units_contract","verify_fixtures.run(version=v1, fix_root=temp_copy)"],"tests_exit":test.returncode,"tests_stdout":test.stdout,"tests_stderr":test.stderr,"fixture_exit":code,"fixture_stdout":out,"source_sha256":sha(ROOT/"tools/elastic_foundation/units_contract.py"),"test_sha256":sha(ROOT/"tools/elastic_foundation/test_units_contract.py")}
    Path(__file__).with_name("reproduce_final_output.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
