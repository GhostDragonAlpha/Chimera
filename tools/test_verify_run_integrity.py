"""CLI acceptance independent of parser internals; preregistered VERIFIER-REPAIR-02."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/'tools/verify_run.py'
GOOD=(ROOT/'LightEngine/output/print_leg_v2_log.txt').read_text(encoding='utf-8')
CASES=[
 ('unknown', GOOD+'\n  (z) FROBNICATE: KABOOM\n', 'UNKNOWN'),
 ('unknown_skipped', GOOD+'\n  (z) FROBNICATE: skipped\n', 'UNKNOWN'),
 ('duplicate', GOOD+'\n  (c) BALANCE: FAIL\n', 'DUPLICATE'),
 ('conflicting_duplicate', GOOD+'\n  (c) BALANCE: PASS\n', 'DUPLICATE'),
 ('truncated', GOOD+'\n[run] tick=99 | angle=\n', 'MALFORMED'),
 ('derived_truncated', GOOD+'\nDerived Foo=1e+\n', 'MALFORMED'),
 ('derived_suffix', GOOD+'\nDerived Foo=1garbage\n', 'MALFORMED'),
 ('derived_inf', GOOD+'\nDerived Foo=inf\n', 'NONFINITE'),
 ('derived_overflow', GOOD+'\nDerived Foo=1e999\n', 'NONFINITE'),
 ('sample_nonfinite', GOOD+'\n[run] tick=99 | angle=nandeg | contact=inf\n', 'NONFINITE'),
 ('empty', '', 'EMPTY LOG'),
 ('no_verdicts', '[run] tick=0 | angle=0deg\n', 'NO VERDICTS'),
 ('truncated_verdict', GOOD+'\n  (z) EXTRA:\n', 'MALFORMED'),
 ('rod_inf', GOOD+'\n[run] tick=99 | rod=tension(inf)\n', 'NONFINITE'),
 ('rope_nan', GOOD+'\n[run] tick=99 | rope links T/S/C=1/0/0 max_comp=nan\n', 'NONFINITE'),
 ('theta_nan', GOOD+'\n[run] tick=99 | theta=[nan, 1.0]deg\n', 'NONFINITE'),
 ('theta_trunc', GOOD+'\n[run] tick=99 | theta=[-120,]\n', 'MALFORMED'),
 ('rod_trunc', GOOD+'\n[run] tick=99 | rod=tension(1.0\n', 'MALFORMED'),
 ('rope_trunc', GOOD+'\n[run] tick=99 | rope links T/S/C=1/0/0 max_comp=1e+\n', 'MALFORMED'),
 ('gap_empty', GOOD+'\n[run] tick=99 | gap=\n', 'MALFORMED'),
 ('contact_trunc', GOOD+'\n[run] tick=99 | contact=1e+\n', 'MALFORMED'),
 ('invalid_boolean', GOOD+'\n[run] tick=99 | com_over_support=maybe\n', 'MALFORMED'),
]

def run(args,cwd):
    return subprocess.run([sys.executable,str(CLI),*map(str,args)],cwd=cwd,
                          capture_output=True,text=True,timeout=15)

@pytest.mark.parametrize('mode',['explicit','directory'])
@pytest.mark.parametrize('name,body,reason',CASES,ids=[c[0] for c in CASES])
def test_rejects_invalid_file(tmp_path,mode,name,body,reason):
    output=tmp_path/'LightEngine/output'
    output.mkdir(parents=True)
    p=output/'print_bad_log.txt'
    p.write_text(body,encoding='utf-8')
    cp=run(['--all'] if mode=='directory' else [p],tmp_path)
    assert cp.returncode==1,cp.stdout+cp.stderr
    assert reason in cp.stdout,cp.stdout+cp.stderr
    assert 'Traceback' not in cp.stderr

@pytest.mark.parametrize('mode',['explicit','directory'])
@pytest.mark.parametrize('position',[0,1,2])
def test_bad_file_preserves_remaining_reports(tmp_path,mode,position):
    output=tmp_path/'LightEngine/output'
    output.mkdir(parents=True)
    paths=[]
    for i in range(3):
        p=output/f'print_{i}_log.txt'
        p.write_text('Derived Foo=1e999' if i==position else GOOD,encoding='utf-8')
        paths.append(p)
    cp=run(['--all'] if mode=='directory' else paths,tmp_path)
    assert cp.returncode==1
    assert all(p.name in cp.stdout for p in paths),cp.stdout
    assert 'NONFINITE' in cp.stdout
    assert 'Traceback' not in cp.stderr

def test_missing_file_does_not_abort_later_file(tmp_path):
    good=tmp_path/'good.txt'
    good.write_text(GOOD,encoding='utf-8')
    cp=run([tmp_path/'absent.txt',good],tmp_path)
    assert cp.returncode==1 and 'ERROR' in cp.stdout and good.name in cp.stdout
    assert 'Traceback' not in cp.stderr

def test_empty_directory_fails(tmp_path):
    cp=run(['--all'],tmp_path)
    assert cp.returncode==1 and 'NO LOGS' in cp.stdout

@pytest.mark.parametrize('name',[
 'print_leg_v2_log.txt','print_lever_v6_log.txt','print_leg_v1_log.txt',
 'print_leg_v3_log.txt','print_leg_v3_control_log.txt'])
def test_valid_output_is_byte_identical(name):
    baseline=json.loads((ROOT/'docs/evidence/verifier-repair-02/baseline.json').read_text())
    cp=subprocess.run([sys.executable,str(CLI),'LightEngine/output/'+name],cwd=ROOT,capture_output=True)
    assert cp.returncode==0 and not cp.stderr
    if sys.platform=='win32':
        assert hashlib.sha256(cp.stdout).hexdigest()==baseline['fixtures'][name]['stdout_sha256']
    portable=json.loads((ROOT/'docs/evidence/verifier-repair-02/baseline_lf.json').read_text())
    assert hashlib.sha256(cp.stdout.replace(b'\r\n',b'\n')).hexdigest()==portable['fixtures'][name]


@pytest.mark.parametrize('mode',['explicit','directory'])
@pytest.mark.parametrize('file_position',[0,1,2])
@pytest.mark.parametrize('sample_position',[0,20,41])
def test_sparse_columns_are_named_and_other_files_survive(tmp_path,mode,file_position,sample_position):
    lines=GOOD.splitlines()
    samples=[i for i,line in enumerate(lines) if 'tick=' in line and '|' in line]
    at=samples[sample_position] if sample_position<len(samples) else samples[-1]+1
    lines.insert(at,'[leg_v2] tick=99 | angle=1.0deg')
    sparse='\n'.join(lines)+'\n'
    output=tmp_path/'LightEngine/output'
    output.mkdir(parents=True)
    paths=[]
    for i in range(3):
        p=output/f'print_{i}_log.txt'
        p.write_text(sparse if i==file_position else GOOD,encoding='utf-8')
        paths.append(p)
    cp=run(['--all'] if mode=='directory' else paths,tmp_path)
    assert cp.returncode==1
    assert 'MISSING_COLUMN' in cp.stdout and 'tip_to_drop' in cp.stdout,cp.stdout
    assert all(p.name in cp.stdout for p in paths)
    assert 'Traceback' not in cp.stderr


def test_uniform_minimal_schema_remains_legal(tmp_path):
    p=tmp_path/'minimal.txt'
    p.write_text('[run] tick=0 | clusters=1/1\n[run] tick=1 | clusters=1/1\n'
                 '  (d) INTEGRITY: PASS\n',encoding='utf-8')
    cp=run([p],tmp_path)
    assert cp.returncode==0,cp.stdout+cp.stderr
