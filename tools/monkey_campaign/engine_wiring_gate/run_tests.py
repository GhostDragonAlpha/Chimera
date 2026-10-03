"""The whole-game gate for the combine-core wiring (PREREGISTERED).

Compile the REAL per-tick combine-core consumer (MembraneTick::step, the
ordered-pass tail whose fall pass routes through combine_core.hpp over the
PR #319 ContributionExecutor seam) under ONE compiler backend (GNU or MSVC),
capture 180 ticks of the deterministic synthetic membrane at worker counts
1/2/4, and prove:

  PRIMARY  candidate@1 / candidate@2 / candidate@4 full captures are
           byte-identical (the workers provenance line is normalized --
           it is the only line allowed to differ),
  SERIAL   baseline (the unwired base blobs) V-stream == candidate V-stream
           at every worker count, byte-for-byte (every physics float),
  CROSS    the parsed hexfloat VALUES of the capture are exported
           (values_<compiler>.txt, declared output) so the GNU and MSVC
           value streams can be compared byte-for-byte at evidence level.

Compile inputs are pinned: the baseline headers come from the shared
repository's Git object database at the recorded base (byte-asserted against
INPUTS.json); the preregistration hash is pinned BEFORE the runs. A refusal
or a mismatch is FAILED evidence: the live dynamics default stays one worker
(the serial law) and nothing is qualified.

No rendered frame is involved (numeric capture only). No physics claim: the
claim is determinism of the wired consumer, not new physics.
"""
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
PROBE = HERE / 'membrane_gate.cpp'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def v_lines(raw: bytes):
    return [line for line in raw.split(b'\n') if line.startswith(b'V')]


def values_bytes(raw: bytes):
    """Cross-compiler-comparable value stream: every capture token with %a
    hexfloats parsed and re-emitted as canonical 16-hex-digit float bits."""
    out = []
    for line in raw.split(b'\n'):
        if not line.startswith(b'V'):
            continue
        for tok in line.split()[1:]:
            value = float.fromhex(tok.decode('ascii'))
            out.append(struct.pack('>d', value).hex())
    return ('\n'.join(out) + '\n').encode()


def normalize(raw: bytes):
    """The only allowed per-worker difference is the workers provenance
    line; everything else must match byte-for-byte."""
    return b'\n'.join(line for line in raw.split(b'\n')
                      if not line.startswith(b'GATE workers='))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ticks', type=int, default=180)
    parser.add_argument('--compiler', choices=['gnu', 'msvc'], default='gnu')
    args = parser.parse_args()
    if not 1 <= args.ticks <= 3000:
        parser.error('ticks must be between 1 and 3000')
    out = Path(os.environ['CHIMERA_OUTPUT_DIR'])
    out.mkdir(parents=True, exist_ok=True)
    build = ROOT / 'engine_wiring_gate_build'
    build.mkdir()
    (build / 'obj').mkdir()
    command_env = os.environ.copy()
    report = {'schema': 'chimera.engine_wiring_gate_result.v1',
              'passed': False, 'ticks_per_configuration': args.ticks,
              'worker_counts': [1, 2, 4],
              'scope': 'Determinism qualification of the wired membrane-tick '
                       'combine consumer over a pinned synthetic scene; no '
                       'physics claim, no rendered frame, no default change.',
              'compiler_backend': args.compiler,
              'commands': [], 'runs': [], 'failures': []}

    def command(argv, target, timeout):
        print('RUN', ' '.join(str(x) for x in argv), flush=True)
        started = time.perf_counter()
        with target.open('wb') as stdout:
            result = subprocess.run([str(x) for x in argv], stdout=stdout,
                                    stderr=subprocess.PIPE, timeout=timeout,
                                    check=False, env=command_env)
        detail = {'argv': [str(x) for x in argv],
                  'exit_code': result.returncode,
                  'elapsed_s': time.perf_counter() - started,
                  'stdout_sha256': sha(target),
                  'stdout_bytes': target.stat().st_size,
                  'stderr': result.stderr.decode('utf-8',
                                                 errors='replace')[-12000:]}
        report['commands'].append(detail)
        if target.suffix == '.log' or result.returncode:
            detail['stdout_tail'] = target.read_bytes()[-12000:].decode(
                'utf-8', errors='replace')
        if result.returncode:
            raise RuntimeError(f'command exited {result.returncode}: '
                               f'{detail["stderr"]}\n'
                               f'{detail.get("stdout_tail", "")}')
        return detail

    try:
        # ---- compiler selection (the #319 pattern) -----------------------
        if args.compiler == 'msvc':
            vcvars = Path('C:/Program Files (x86)/Microsoft Visual Studio/'
                          '2022/BuildTools/VC/Auxiliary/Build/vcvars64.bat')
            if not vcvars.is_file():
                raise RuntimeError('MSVC environment setup unavailable')
            setup = build / 'compiler_environment.cmd'
            setup.write_text('@echo off\r\ncall "' + str(vcvars) +
                             '" >nul\r\nif errorlevel 1 exit /b 1\r\nset\r\n',
                             encoding='utf-8')
            environment_text = subprocess.check_output(
                ['cmd.exe', '/d', '/c', str(setup)], cwd=build,
                timeout=120).decode('mbcs')
            command_env = {key: value
                           for line in environment_text.splitlines()
                           if '=' in line and not line.startswith('=')
                           for key, value in [line.split('=', 1)]}
            compiler_path = next(value for key, value in command_env.items()
                                 if key.upper() == 'PATH')
            compiler = shutil.which('cl.exe', path=compiler_path)
            del environment_text
        else:
            compiler = shutil.which('g++')
        if not compiler:
            raise RuntimeError('selected C++ compiler unavailable')
        if args.compiler == 'gnu':
            version = subprocess.check_output([compiler, '--version'],
                                              text=True).splitlines()[0]
        else:
            probe = subprocess.run([compiler], cwd=build, env=command_env,
                                   capture_output=True, text=True,
                                   timeout=30)
            version = (probe.stdout + probe.stderr).strip().splitlines()[:3]
        report['compiler'] = {'path': compiler, 'sha256': sha(Path(compiler)),
                              'version': version}

        # ---- pinned inputs ------------------------------------------------
        inputs = json.loads((HERE / 'INPUTS.json').read_text())
        assert inputs['gate']['ticks'] == args.ticks, \
            'tick count is preregistered; amend the prereg first'
        assert sha(HERE / 'PREREGISTRATION.md') == \
            inputs['pins']['preregistration_sha256'], 'prereg drift'
        assert sha(HERE / 'engine_material_payload.json') == \
            inputs['pins']['payload_sha256'], 'payload drift'
        assert sha(PROBE) == inputs['pins']['probe_sha256'], 'probe drift'
        source_repo = os.environ.get('CHIMERA_SOURCE_REPO', 'E:/PythonChimera')
        git = ['git', '-c', 'safe.directory=' + source_repo, '-C',
               source_repo, 'show']
        baseline = build / 'baseline'
        baseline.mkdir()
        for name in ('membrane_tick.hpp', 'membrane_tick.cpp',
                     'joint_binding.hpp'):
            pin = inputs['pins'][f'base_{name}']
            original = subprocess.check_output(
                git + [inputs['base'] + ':ChimeraEngine/engine/' + name],
                timeout=60)
            assert hashlib.sha256(original).hexdigest() == pin['sha256'], \
                f'base blob drift: {name}'
            assert original == (HERE / 'baseline' / name).read_bytes(), \
                f'baseline copy drift: {name}'
            (baseline / name).write_bytes(original)
        report['git_input_provenance_verified'] = True
        report['inputs_manifest_sha256'] = sha(HERE / 'INPUTS.json')
        report['base'] = inputs['base']
        report['source_sha256'] = {
            str(p.relative_to(ROOT)): sha(p) for p in [
                ENGINE / 'combine_core.hpp', ENGINE / 'coupled_dynamics.hpp',
                ENGINE / 'membrane_tick.hpp', ENGINE / 'membrane_tick.cpp',
                PROBE, HERE / 'run_tests.py']}

        # ---- compile: baseline (unwired base blobs) and candidate ---------
        payload = HERE / 'engine_material_payload.json'
        binaries = {}
        if args.compiler == 'gnu':
            flags = ['-std=c++17', '-O2', '-fno-fast-math', '-ffp-contract=off',
                     '-pthread', '-Wall', '-Wextra']

            def cc(target, defines, first_inc, tick_src):
                argv = [compiler, *flags, *defines, '-I', str(first_inc),
                        '-I', str(ENGINE), str(PROBE), str(tick_src),
                        '-o', target]
                command(argv, build / (target.stem + '_compile.log'), 300)
        else:
            def cc(target, defines, first_inc, tick_src):
                argv = [compiler, '/nologo', '/std:c++17', '/EHsc', '/O2',
                        '/fp:precise', '/W4', '/MD', *defines, '/I',
                        str(first_inc), '/I', str(ENGINE), str(PROBE),
                        str(tick_src), '/Fe:' + str(target),
                        '/Fo:' + str(build / 'obj') + '/']
                command(argv, build / (target.stem + '_compile.log'), 300)
        cc(baseline / 'gate_baseline.exe', ['-DMEMBRANE_GATE_BASELINE'],
           baseline, baseline / 'membrane_tick.cpp')
        cc(build / 'gate_candidate.exe', [], ENGINE,
           ENGINE / 'membrane_tick.cpp')
        binaries['baseline'] = sha(baseline / 'gate_baseline.exe')
        binaries['candidate'] = sha(build / 'gate_candidate.exe')
        report['binaries'] = binaries

        # ---- run: baseline@1, candidate@1/2/4 ------------------------------
        captures = {}
        for name, exe, workers in [('baseline', baseline / 'gate_baseline.exe', 1),
                                   ('candidate', build / 'gate_candidate.exe', 1),
                                   ('candidate', build / 'gate_candidate.exe', 2),
                                   ('candidate', build / 'gate_candidate.exe', 4)]:
            target = build / f'capture_{name}_{workers}.txt'
            detail = command([exe, str(workers), str(args.ticks), str(payload)],
                             target, 300)
            raw = target.read_bytes()
            if b'FAIL' in raw or b'refuse=' in raw:
                raise RuntimeError(f'{name}@{workers}: refusal/FAIL in capture')
            captures[(name, workers)] = raw
            report['runs'].append({'binary': name, 'workers': workers,
                                   'sha256': detail['stdout_sha256'],
                                   'bytes': len(raw)})

        # ---- PRIMARY: candidate full-stream identity across workers -------
        candidate_first = normalize(captures[('candidate', 1)])
        (out / 'gate_capture_candidate_w1.txt').write_bytes(
            captures[('candidate', 1)])
        (out / 'gate_capture_baseline_w1.txt').write_bytes(
            captures[('baseline', 1)])
        for workers in (2, 4):
            same = normalize(captures[('candidate', workers)]) == candidate_first
            report['runs'].append({'check': 'candidate_worker_identity',
                                   'workers': workers,
                                   'baseline_byte_identical': same})
            if not same:
                other = normalize(captures[('candidate', workers)])
                first = next((i for i, (a, b) in
                              enumerate(zip(candidate_first, other))
                              if a != b),
                             min(len(candidate_first), len(other)))
                report['first_mismatch'] = {
                    'byte': first,
                    'w1_context': candidate_first[max(0, first-120):first+120].decode(errors='replace'),
                    'wn_context': other[max(0, first-120):first+120].decode(errors='replace')}
                raise AssertionError(
                    f'candidate worker byte parity failed at workers={workers}')

        # ---- SERIAL: baseline V-stream == candidate V-stream --------------
        baseline_v = v_lines(captures[('baseline', 1)])
        for workers in (1, 2, 4):
            same = baseline_v == v_lines(captures[('candidate', workers)])
            report['runs'].append({'check': 'baseline_v_stream_identity',
                                   'workers': workers,
                                   'baseline_byte_identical': same})
            if not same:
                raise AssertionError(
                    f'baseline V-stream parity failed at workers={workers}')

        # ---- CROSS: exported normalized value stream -----------------------
        values = values_bytes(captures[('candidate', 1)])
        (out / f'values_{args.compiler}.txt').write_bytes(values)
        report['values_sha256'] = sha(out / f'values_{args.compiler}.txt')
        report['passed'] = True
    except Exception as exc:
        report['failures'].append({'type': type(exc).__name__,
                                   'detail': str(exc)})
    finally:
        (out / 'result.json').write_text(
            json.dumps(report, indent=2, allow_nan=False) + '\n',
            encoding='utf-8')
        print(json.dumps({'passed': report['passed'],
                          'runs_completed': len(report['runs']),
                          'failures': report['failures']}), flush=True)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
