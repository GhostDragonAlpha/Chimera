"""MAT2-G06 sealed-run driver: the full evidence chain in ONE runner job.

Runs every preregistered mode in order in this process's scratch copy and
refuses on the first nonzero step (the runner records the failure; no
artifact of a failed chain is kept by the caller beyond the runner log).
Order: main -> rerun -> compare -> falsify -> regression -> render ->
capture -> pixel recheck -> report -> lint. Deterministic; no wall clock
enters any receipt.

Run: python -B run_all.py
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
CARD = str(HERE / 'run_experiments.py')

STEPS = (
    [sys.executable, '-B', CARD, 'main'],
    [sys.executable, '-B', CARD, 'rerun'],
    [sys.executable, '-B', str(HERE / 'run_experiments.py'), 'compare'],
    [sys.executable, '-B', str(HERE / 'run_experiments.py'), 'falsify'],
    [sys.executable, '-B', str(HERE / 'run_experiments.py'), 'regression'],
    [sys.executable, '-B', str(HERE / 'render_run.py')],
    [sys.executable, '-B', str(HERE / 'make_capture.py')],
    [sys.executable, '-B', str(HERE / 'check_capture_pixels.py')],
    [sys.executable, '-B', str(HERE / 'make_report.py')],
    [sys.executable, '-B', str(HERE / 'lint_report_numbers.py')],
)


def main():
    for i, cmd in enumerate(STEPS, start=1):
        print('=== step %d/%d: %s' % (i, len(STEPS),
                                      pathlib.Path(cmd[2]).name + ' '
                                      + (cmd[3] if len(cmd) > 3 else '')),
              flush=True)
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=2400)
        tail = (proc.stdout or '')[-1200:]
        print(tail, flush=True)
        if proc.returncode != 0:
            print('STEP_FAILED: %s (exit %s)\nstderr tail:\n%s'
                  % (cmd, proc.returncode, (proc.stderr or '')[-1500:]),
                  flush=True)
            return 1
    print('RUN_ALL_OK: %s steps green' % len(STEPS), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
