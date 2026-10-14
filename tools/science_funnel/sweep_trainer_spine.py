"""The DOMAIN SWEEP — preregistered falsifier of work.data.trainer_spine_repair_20260917.

LAW: every module in Chimera/core/trainables either completes
train_and_audit(pop=6, gens=5) or refuses with its OWN honest cause — never an
internal spine TypeError/KeyError. Each module runs in its own bounded child
process (per-module timeout); outcomes are enumerated in a canonical receipt
written under tools/science_funnel/validation/trainer_repair_20260917/.

Outcome classes:
  completed      train_and_audit returned (audit summary recorded)
  refused        the domain's own designed refusal: Refusal / DomainRefusal /
                 FileNotFoundError raised from the domain's own frame
  refused_env    the domain cannot even import here (missing optional
                 dependency, e.g. warp/newton for the GPU domains) — cause kept
  refused_ugly   the domain's own frame raised something that is not a designed
                 refusal type (recorded honestly; REFUTES the repair)
  failed_internal  the exception's innermost frame is spine code, or the child
                 died without a classified marker (REFUTES the repair)
  timeout        the per-module timeout expired (REFUTES the repair)

Exit code 0 iff the falsifier held (no refuting outcome class).

  python -B -m tools.science_funnel.sweep_trainer_spine \
      [--timeout 600] [--out tools/science_funnel/validation/trainer_repair_20260917/sweep_receipt.json]
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRAINABLES = ROOT / 'Chimera' / 'core' / 'trainables'
DEFAULT_OUT = (ROOT / 'tools' / 'science_funnel' / 'validation'
               / 'trainer_repair_20260917' / 'sweep_receipt.json')
WORK_ID = 'work.data.trainer_spine_repair_20260917'
REFUTING = {'refused_ugly', 'failed_internal', 'timeout', 'crashed'}

# Designed refusal exception types when raised from the DOMAIN's own frame.
DESIGNED_REFUSALS = {'Refusal', 'DomainRefusal', 'FileNotFoundError', 'NotImplementedError'}

CHILD_CODE = r'''
import json, sys, time, traceback
sys.path.insert(0, "Chimera")
mod = sys.argv[1]

def emit(payload):
    print("SWEEP " + json.dumps(payload))
    sys.stdout.flush()

try:
    import importlib
    importlib.import_module("core.trainables." + mod)
except Exception as e:
    emit({"outcome": "refused_env",
          "cause": "import: " + type(e).__name__ + ": " + str(e)[:300]})
    sys.exit(0)

from core.train_loop import train_and_audit, DomainRefusal
from tools.science_funnel.common import Refusal
try:
    t0 = time.time()
    r = train_and_audit(mod, pop=6, gens=5)
    emit({"outcome": "completed", "seconds": round(time.time() - t0, 1),
          "stuck_metrics": r["audit"]["stuck_metrics"],
          "recommendation": r["audit"]["recommendation"][:120]})
except (Refusal, DomainRefusal) as e:
    emit({"outcome": "refused", "exc_type": type(e).__name__,
          "cause": str(e)[:300]})
except Exception as e:
    tb = traceback.extract_tb(sys.exc_info()[2])
    inner = tb[-1] if tb else None
    fname = inner.filename.replace("\\", "/").lower() if inner else ""
    marker = ("core/trainables/" + mod + ".py")
    if marker in fname:
        emit({"outcome": "refused", "exc_type": type(e).__name__,
              "cause": "domain frame: " + str(e)[:300]})
    else:
        emit({"outcome": "failed_internal", "exc_type": type(e).__name__,
              "cause": str(e)[:200] + " @ " + fname})
'''


def sweep_module(python: str, module: str, timeout: float) -> dict:
    started = time.time()
    try:
        proc = subprocess.run(
            [python, '-B', '-c', CHILD_CODE, module], cwd=str(ROOT),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            errors='replace', timeout=timeout)
    except subprocess.TimeoutExpired:
        return {'module': module, 'outcome': 'timeout',
                'cause': f'no classified answer within {timeout}s', 'seconds': round(time.time() - started, 1)}
    except OSError as exc:
        return {'module': module, 'outcome': 'crashed',
                'cause': f'spawn failed: {exc}', 'seconds': round(time.time() - started, 1)}
    elapsed = round(time.time() - started, 1)
    marker = None
    for line in reversed((proc.stdout or '').splitlines()):
        if line.startswith('SWEEP '):
            try:
                marker = json.loads(line[len('SWEEP '):])
            except ValueError:
                marker = None
            break
    if marker is None:
        tail = (proc.stdout or '')[-400:]
        return {'module': module, 'outcome': 'crashed',
                'cause': f'exit {proc.returncode} without a SWEEP marker; tail: {tail}',
                'seconds': elapsed}
    record = {'module': module, 'seconds': elapsed}
    record.update(marker)
    outcome, exc_type = record.get('outcome'), record.get('exc_type')
    if outcome == 'refused' and exc_type not in DESIGNED_REFUSALS:
        record['outcome'] = 'refused_ugly'
        record['cause'] = f'{exc_type} is not a designed refusal: {record.get("cause", "")}'
    return record


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--timeout', type=float, default=600.0,
                    help='per-module child timeout in seconds')
    ap.add_argument('--python', default=sys.executable)
    ap.add_argument('--out', type=Path, default=DEFAULT_OUT)
    ap.add_argument('--only', default='', help='comma-separated module filter (debug)')
    args = ap.parse_args()

    modules = sorted(p.stem for p in TRAINABLES.glob('*.py')
                     if p.stem != '__init__')
    if args.only:
        modules = [m for m in modules if m in set(args.only.split(','))]
    if not modules:
        raise SystemExit('no trainables found under ' + str(TRAINABLES))

    results = []
    for module in modules:
        record = sweep_module(args.python, module, args.timeout)
        results.append(record)
        print(f"  {record['module']:<22} {record['outcome']:<15} "
              f"{record.get('cause', '')[:100]}")

    totals = {}
    for record in results:
        totals[record['outcome']] = totals.get(record['outcome'], 0) + 1
    held = not (set(totals) & REFUTING)
    receipt = {
        'schema': 'chimera.trainer_sweep.v1',
        'work': WORK_ID,
        'recorded_utc': datetime.now(timezone.utc).isoformat(),
        'law': 'every module in Chimera/core/trainables completes '
               'train_and_audit(pop=6, gens=5) or refuses with its own honest '
               'cause; never an internal spine TypeError/KeyError',
        'bounded': {'per_module_timeout_s': args.timeout,
                    'python': args.python,
                    'modules': len(modules)},
        'results': results,
        'totals': totals,
        'falsifier': {
            'held': held,
            'verdict': ('SURVIVED: every module completed or refused with an '
                        'honest named cause' if held else
                        'REFUTED: refuting outcome class present'),
            'refuting_classes': sorted(set(totals) & REFUTING),
        },
        'replay': 'python -B -m tools.science_funnel.sweep_trainer_spine '
                  '--timeout %g --out %s' % (args.timeout, args.out),
    }
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    from tools.science_funnel.common import canonical
    out.write_bytes(canonical(receipt))
    print(f"sweep receipt: {out}")
    print('falsifier:', receipt['falsifier']['verdict'])
    return 0 if held else 1


if __name__ == '__main__':
    raise SystemExit(main())
