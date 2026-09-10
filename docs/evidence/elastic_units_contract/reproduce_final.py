"""Reproducible evidence runner; writes once to a caller-selected path."""
import argparse, contextlib, hashlib, io, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def execute(output, run=subprocess.run, verifier=None):
    output = Path(output)
    if output.exists(): raise FileExistsError("output_exists_refusing_overwrite")
    if verifier is None:
        from tools.elastic_foundation import verify_fixtures
        verifier = verify_fixtures.run
    with tempfile.TemporaryDirectory() as td:
        shutil.copytree(ROOT / "docs/evidence/elastic_foundation/fixtures/v1", Path(td)/"v1")
        env=dict(os.environ); env.pop("CHIMERA_UNITS_CANDIDATE", None)
        test=run([sys.executable,"-m","unittest","tools.elastic_foundation.test_units_contract"],cwd=ROOT,capture_output=True,text=True,env=env)
        buf=io.StringIO()
        with contextlib.redirect_stdout(buf): verify_code=verifier(SimpleNamespace(version="v1",all=False),fix_root=Path(td))
        report={"commands":[f"{sys.executable} -m unittest tools.elastic_foundation.test_units_contract","verify_fixtures.run(version=v1, fix_root=temp_copy)"],"tests_exit":test.returncode,"tests_stdout":test.stdout,"tests_stderr":test.stderr,"fixture_exit":verify_code,"fixture_stdout":buf.getvalue(),"source_sha256":sha(ROOT/"tools/elastic_foundation/units_contract.py"),"test_sha256":sha(ROOT/"tools/elastic_foundation/test_units_contract.py")}
    with output.open("x",encoding="utf-8") as f: json.dump(report,f,indent=2)
    return 0 if test.returncode == 0 and verify_code == 0 else 1

def self_test():
    with tempfile.TemporaryDirectory() as td:
        existing=Path(td)/"existing.json"; existing.write_text("keep",encoding="utf-8")
        try: execute(existing,run=lambda *a,**k: (_ for _ in ()).throw(AssertionError("child_ran")))
        except FileExistsError: pass
        else: return 1
        out=Path(td)/"fail.json"
        def bad_run(*a,**k): return SimpleNamespace(returncode=1,stdout="",stderr="forced")
        if execute(out,run=bad_run,verifier=lambda *a,**k: 0) != 1: return 1
        out2=Path(td)/"verify-fail.json"
        if execute(out2,run=lambda *a,**k: SimpleNamespace(returncode=0,stdout="",stderr=""),verifier=lambda *a,**k: 1) != 1: return 1
    return 0

def main():
    p=argparse.ArgumentParser(); p.add_argument("--output",required=True); p.add_argument("--self-test",action="store_true"); a=p.parse_args()
    if a.self_test: return self_test()
    return execute(a.output)
if __name__ == "__main__": raise SystemExit(main())
