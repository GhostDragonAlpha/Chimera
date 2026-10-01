"""MAT2-G08 capture-tail runner: the deterministic capture + report tail on
top of the certified receipts carried in the sealed package (the physics
gates ran in job f3fb5dc2, receipts byte-identical in the seal). Writes the
capture evidence set and the final REPORT.md.

Run (sealed): python -B tools/monkey_campaign/contributions/MAT2-G08/run_capture_tail.py
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


def main():
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
