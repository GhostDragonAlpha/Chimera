"""MAT2-G08 one-job runner (the W08/G06 pattern): main, rerun, compare,
falsify, regression, and the named-check suite, in ONE sealed job. Writes
checks_receipt.json with the executed/skipped accounting.

Run (sealed): python -B tools/monkey_campaign/contributions/MAT2-G08/run_all.py
"""
from __future__ import annotations

import g08_deps  # noqa: E402  (must run before upstream imports)

g08_deps.ensure()

import json  # noqa: E402
import pathlib  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import run_experiments as rexp  # noqa: E402


def main():
    rexp.mode_main()
    rexp.mode_rerun()
    rexp.mode_compare()
    rexp.mode_falsify()
    rexp.mode_regression()
    proc = subprocess.run(
        [sys.executable, '-B', '-m', 'unittest', 'test_g08_checks', '-v'],
        cwd=str(HERE), capture_output=True, text=True, timeout=1200)
    # unittest progress and results stream on stderr
    tail = [line for line in proc.stderr.splitlines() if line][-4:]
    receipt = {
        'schema': 'chimera.g08_checks.v1',
        'suite_exit': proc.returncode,
        'suite_tail': tail,
        'named_checks_green': proc.returncode == 0,
    }
    (HERE / 'checks_receipt.json').write_bytes(rexp.canonical(receipt))
    print(json.dumps(receipt, indent=1))
    if proc.returncode != 0:
        print(proc.stderr[-2000:])
        return 1
    for script in ('render_run.py', 'make_capture.py',
                   'check_capture_pixels.py', 'make_report.py',
                   'lint_report_numbers.py'):
        rc = subprocess.run([sys.executable, '-B', script],
                            cwd=str(HERE), capture_output=True,
                            text=True, timeout=1200)
        print('[[%s exit %s]]' % (script, rc.returncode))
        if rc.returncode != 0:
            print(rc.stdout[-800:])
            print(rc.stderr[-800:])
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
