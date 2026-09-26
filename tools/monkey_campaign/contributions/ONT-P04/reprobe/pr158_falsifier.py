"""ONT-P04 PR #158 lead falsifier runner (correction attempt 06792d79).

Reproduces the #158 half of the operational lead's
E:/Chimera/queue-check-20260926/current/reprobe.py VERBATIM (same reviewer
Rig, same actor, same arguments). The lead's original script also carries a
#160 half that crashes before printing (`p.stat().st_size()` is an int, not a
callable - a harness bug in the quick script, unrelated to the #158 finding),
so this runner captures the #158 results the lead's script would have printed.

Usage: python -B pr158_falsifier.py <gpu_handoff_source_dir> <expected_sha256> <out.json>

CPU-only, temporary registries only, no live process is touched.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

SOURCE_DIR = Path(sys.argv[1])
EXPECTED = sys.argv[2]
OUT = Path(sys.argv[3])

STAGE = Path('E:/ChimeraWork/monkey-coordination/kanban-reviews/ONT-P04/'
             '659b2663a8d04cefb01ac4e12379734d/review-evidence')
WS = Path(__file__).resolve().parent.parent
# The gpu_handoff UNDER TEST is loaded from SOURCE_DIR first: the reviewer's
# adversarial_probes module inserts its own staged contribution copy into
# sys.path at import time, so loading the under-test module first (and letting
# the Rig reuse it from sys.modules) is what pins the probe to SOURCE_DIR.
sys.path.insert(0, str(WS / 'pinned' / 'tools' / 'agent_fleet'))
sys.path.insert(0, str(SOURCE_DIR))
import gpu_handoff  # noqa: E402
import control  # noqa: E402
from control import Refusal  # noqa: E402

assert hashlib.sha256(Path(gpu_handoff.__file__).read_bytes()).hexdigest() == EXPECTED
assert hashlib.sha256(Path(control.__file__).read_bytes()).hexdigest() == (
    '39ff01dc8a4192e04606ee9d87386780739e89c8a1774da48501a9545792f6b3')

sys.path.insert(0, str(STAGE))
from adversarial_probes import Rig  # noqa: E402

r = Rig()
r.setup()
results = {}


def call_recorded(op, actor, **p):
    """The lead's falsifier call, with the resulting outcome recorded:
    the returned result on success, the frozen refusal name on refusal."""
    try:
        return {'accepted': r.call(op, actor, **p)}
    except Refusal as e:
        return {'refused': str(e)}


try:
    r.task_pair()
    rid = r.request()['request']
    r.register_fixtures()
    r.admit(rid)
    # --- lead's falsifier lines, verbatim arguments ---
    results['foreign_checkpoint'] = call_recorded(
        'handoff_checkpoint_preserved', 'gamer', task='training',
        evidence='foreign assertion', workers=['bionic'])
    results['foreign_unload_wrong_config'] = call_recorded(
        'handoff_model_unload', 'gamer', task='training',
        instance='qwen-local',
        restoration_config={'artifact': 'DIFFERENT', 'context': 1})
    # --- additive evidence: what actually landed in the request record ---
    snap = r.snap()
    req = snap['handoff']['requests'][rid]
    results['task_drain_record_after'] = req['drain']
    results['gamer_is_request_owner'] = (req['owner'] == 'gamer')
finally:
    r.teardown()
OUT.write_text(json.dumps(results, indent=2), encoding='utf-8')
print(json.dumps(results, indent=2))
