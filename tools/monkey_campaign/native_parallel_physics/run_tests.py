"""Compile and verify native physics in the canonical runner's disposable slot."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ENGINE = ROOT / 'ChimeraEngine/engine'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ticks', type=int, default=300)
    parser.add_argument('--compiler', choices=['gnu', 'msvc'], default='gnu')
    args = parser.parse_args()
    if not 1 <= args.ticks <= 3000:
        parser.error('ticks must be between 1 and 3000')
    out = Path(os.environ['CHIMERA_OUTPUT_DIR'])
    out.mkdir(parents=True, exist_ok=True)
    build = ROOT / 'native-physics-build'
    build.mkdir()
    compiler = shutil.which('g++')
    command_env = os.environ.copy()
    report = {'schema': 'chimera.native_parallel_physics_result.v1', 'passed': False,
              'ticks_per_configuration': args.ticks, 'configuration_count': 7,
              'scope': 'Pinned native CPU articulated-model software regression; no full animal/contact/GPU qualification.',
              'compiler_backend': args.compiler,
              'commands': [], 'runs': [], 'failures': []}
    def command(argv, target, timeout):
        print('RUN', ' '.join(str(x) for x in argv), flush=True)
        started = time.perf_counter()
        with target.open('wb') as stdout:
            result = subprocess.run([str(x) for x in argv], stdout=stdout, stderr=subprocess.PIPE,
                                    timeout=timeout, check=False, env=command_env)
        detail = {'argv': [str(x) for x in argv], 'exit_code': result.returncode,
                  'elapsed_s': time.perf_counter() - started, 'stdout_sha256': sha(target),
                  'stdout_bytes': target.stat().st_size,
                  'stderr': result.stderr.decode('utf-8', errors='replace')[-12000:]}
        report['commands'].append(detail)
        if target.suffix == '.log' or result.returncode:
            detail['stdout_tail'] = target.read_bytes()[-12000:].decode('utf-8', errors='replace')
        if result.returncode:
            raise RuntimeError(f'command exited {result.returncode}: {detail["stderr"]}\n{detail.get("stdout_tail", "")}')
        return detail
    try:
        if args.compiler == 'msvc':
            vcvars = Path('C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Auxiliary/Build/vcvars64.bat')
            if not vcvars.is_file():
                raise RuntimeError('MSVC environment setup unavailable')
            # Capture environment privately for child processes; never report it.
            setup = build / 'compiler_environment.cmd'
            setup.write_text('@echo off\ncall "'+str(vcvars)+'" >nul\nif errorlevel 1 exit /b 1\nset\n', encoding='utf-8')
            environment_text = subprocess.check_output(['cmd.exe', '/d', '/c', str(setup)], cwd=build, timeout=30).decode('mbcs')
            command_env = {key: value for line in environment_text.splitlines() if '=' in line and not line.startswith('=')
                           for key, value in [line.split('=', 1)]}
            compiler_path = next(value for key, value in command_env.items() if key.upper() == 'PATH')
            compiler = shutil.which('cl.exe', path=compiler_path)
            del environment_text
        if not compiler:
            raise RuntimeError('selected C++ compiler unavailable')
        if args.compiler == 'gnu':
            version = subprocess.check_output([compiler, '--version'], text=True).splitlines()[0]
        else:
            version = subprocess.run([compiler], cwd=build, env=command_env, capture_output=True, text=True, timeout=15)
            version = (version.stdout + version.stderr).strip().splitlines()[:3]
        report['compiler'] = {'path': compiler, 'sha256': sha(Path(compiler)),
                              'version': version}
        inputs = json.loads((HERE / 'INPUTS.json').read_text())
        assert sha(HERE / 'scene_fixture.json') == inputs['scene_fixture_sha256']
        assert sha(HERE / 'reference_cases.json') == inputs['reference_sha256']
        source_repo = os.environ.get('CHIMERA_SOURCE_REPO', 'E:/PythonChimera')
        git = ['git', '-c', 'safe.directory=' + source_repo, '-C', source_repo, 'show']
        graph_bytes = subprocess.check_output(git + [inputs['base'] + ':' + inputs['graph_blob_path']], timeout=30)
        assert hashlib.sha256(graph_bytes).hexdigest() == inputs['graph_blob_sha256']
        graph = json.loads(graph_bytes)
        for identity, expected in inputs['selected_graph_objects_sha256'].items():
            serialized = json.dumps(graph['objects'][identity], sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
            assert hashlib.sha256(serialized).hexdigest() == expected
        fixture = json.loads((HERE / 'scene_fixture.json').read_bytes())['coupled_dynamics']
        recipe = graph['objects']['model.dynamics.coupled_arm']['physical']['contract']
        assert fixture['recipe'] == recipe
        assert fixture['model'] == graph['objects'][recipe['source_model_id']]['physical']['model']
        reference_bytes = subprocess.check_output(git + [inputs['base'] + ':' + inputs['reference_path']], timeout=30)
        assert reference_bytes == (HERE / 'reference_cases.json').read_bytes()
        for header in ['coupled_articulation.hpp', 'coupled_dynamics.hpp']:
            original = subprocess.check_output(git + [inputs['base'] + ':ChimeraEngine/engine/' + header], timeout=30)
            assert original == (HERE / 'baseline' / header).read_bytes()
        report['git_input_provenance_verified'] = True
        del graph_bytes, graph, reference_bytes
        report['inputs_manifest_sha256'] = sha(HERE / 'INPUTS.json')
        report['source_sha256'] = {str(p.relative_to(ROOT)): sha(p) for p in [
            ENGINE / 'contribution_executor.hpp', ENGINE / 'coupled_articulation.hpp',
            ENGINE / 'coupled_dynamics.hpp', HERE / 'native_probe.cpp', HERE / 'executor_probe.cpp',
            HERE / 'baseline/coupled_articulation.hpp', HERE / 'baseline/coupled_dynamics.hpp',
            HERE / 'batch_probe.cpp', HERE / 'dynamics_controls.cpp']}
        flags = ['-std=c++17', '-O2', '-fno-fast-math', '-ffp-contract=off', '-pthread', '-Wall', '-Wextra']
        targets = [('baseline', HERE / 'native_probe.cpp', ['-I', str(HERE / 'baseline'), '-I', str(ENGINE)]),
                   ('candidate', HERE / 'native_probe.cpp', ['-DCHIMERA_PARALLEL_CANDIDATE', '-I', str(ENGINE)]),
                   ('executor', HERE / 'executor_probe.cpp', ['-I', str(ROOT)]),
                   ('batch', HERE / 'batch_probe.cpp', ['-I', str(ROOT)]),
                   ('controls_baseline', HERE / 'dynamics_controls.cpp', ['-I', str(HERE / 'baseline'), '-I', str(ENGINE)]),
                   ('controls_candidate', HERE / 'dynamics_controls.cpp', ['-DCHIMERA_PARALLEL_CANDIDATE', '-I', str(ENGINE)])]
        for name, source, includes in targets:
            binary = build / (name + '.exe')
            if args.compiler == 'gnu':
                argv = [compiler, *flags, *includes, source, '-o', binary]
            else:
                includes = ['/I' if value == '-I' else '/D' + value[2:] if value.startswith('-D') else value for value in includes]
                argv = [compiler, '/nologo', '/std:c++17', '/EHsc', '/O2', '/fp:precise', '/W4', '/MD',
                        *includes, source, '/Fe:'+str(binary), '/Fo:'+str(build / (name + '.obj'))]
            command(argv, build / (name + '_compile.log'), 120)
            report.setdefault('binaries', {})[name] = sha(binary)
        executor_json = build / 'executor.json'
        command([build / 'executor.exe'], executor_json, 30)
        report['executor'] = json.loads(executor_json.read_bytes())
        assert report['executor']['pass']
        (out / 'executor_checks.json').write_bytes(executor_json.read_bytes())
        batch_json = build / 'batch.json'
        command([build / 'batch.exe', HERE / 'scene_fixture.json', HERE / 'reference_cases.json'], batch_json, 90)
        report['batch'] = json.loads(batch_json.read_bytes())
        assert report['batch']['pass']
        (out / 'batch_checks.json').write_bytes(batch_json.read_bytes())
        control_baseline = None
        report['control_runs'] = []
        for name, workers in [('controls_baseline', 1), ('controls_candidate', 1), ('controls_candidate', 2), ('controls_candidate', 4)]:
            target = build / f'controls-{len(report["control_runs"])}.json'
            detail = command([build / (name + '.exe'), HERE / 'scene_fixture.json', workers], target, 180)
            raw = target.read_bytes()
            parsed = json.loads(raw)
            assert parsed['pass']
            if control_baseline is None:
                control_baseline = raw
                (out / 'control_checks.json').write_bytes(raw)
            report['control_runs'].append({'binary': name, 'workers': workers,
                                           'sha256': detail['stdout_sha256'], 'baseline_byte_identical': raw == control_baseline})
            if raw != control_baseline:
                raise AssertionError('native control/refinement baseline parity failed')
        baseline_bytes = None
        for name, workers in [('baseline', 1), ('candidate', 1), ('candidate', 2), ('candidate', 4), ('candidate', 4)]:
            target = build / f'probe-{len(report["runs"])}.json'
            detail = command([build / (name + '.exe'), HERE / 'scene_fixture.json',
                              HERE / 'reference_cases.json', workers, args.ticks], target, 180)
            data = target.read_bytes()
            parsed = json.loads(data)
            assert parsed['pass']
            if baseline_bytes is None:
                baseline_bytes = data
                metrics = {key: struct.unpack('>d', bytes.fromhex(value))[0]
                           for key, value in parsed['values'] if key.endswith('peak_balance_J')}
                report['baseline_metrics'] = {'reported_value_count': len(parsed['values']),
                                               'trajectory_double_count': len(parsed['trajectory_bits']),
                                               'peak_energy_residuals_J': metrics}
            same = data == baseline_bytes
            report['runs'].append({'binary': name, 'workers': workers, 'sha256': detail['stdout_sha256'],
                                   'bytes': len(data), 'baseline_byte_identical': same, 'elapsed_s': detail['elapsed_s']})
            if not same:
                # Retain a compact first difference, not megabytes of duplicate traces.
                first = next((i for i, (a, b) in enumerate(zip(baseline_bytes, data)) if a != b), min(len(data), len(baseline_bytes)))
                report['first_mismatch'] = {'byte': first, 'baseline_context': baseline_bytes[max(0, first-120):first+120].decode(errors='replace'), 'candidate_context': data[max(0, first-120):first+120].decode(errors='replace')}
                raise AssertionError('native baseline byte parity failed')
        report['passed'] = True
    except Exception as exc:
        report['failures'].append({'type': type(exc).__name__, 'detail': str(exc)})
    finally:
        (out / 'result.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8')
        print(json.dumps({'passed': report['passed'], 'runs_completed': len(report['runs']), 'failures': report['failures']}), flush=True)
    return 0 if report['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
