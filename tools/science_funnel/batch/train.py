"""Batch-gated trainer hook. The gate is the batch's own law: training may only
run on a proven library state (graph valid + zero contract failures + count
identity closed). The exercise runs ONE existing trainer domain in a child
process; no ML quality is claimed -- this proves the wiring, not a policy."""
import subprocess
import sys
from pathlib import Path

from ..common import canonical, require, sha

ROOT = Path(__file__).resolve().parents[3]
# The documented canonical domain (train_loop docstring example). arrangement
# refuses without a scan (by design), pref_selftest predates the seed(rng)
# protocol, beat_generator hits a latent auditor KeyError -- recorded here so
# the next slice can repair the auditor, not silently skip it.
EXERCISE_DOMAIN = 'erisaid_mirror'


def batch_gate(graph, batch_summary):
    """Derive-before-train at batch scale: the gate refuses unless the whole
    batch proven (graph checks clean, zero contract failures, identity closed)."""
    require(not graph.check(), 'train_gate_graph_invalid')
    require(batch_summary['totals']['contract_failures'] == 0,
            'train_gate_contract_failures')
    require(batch_summary['count_identity']['closed'], 'train_gate_count_identity_open')
    return {'gate': 'closed-proven-library-state', 'passed': True}


def exercise(domain=EXERCISE_DOMAIN, pop=6, gens=5, timeout=300):
    """Run one trainer domain in a child process; capture and hash its output.

    gens >= 5 is REQUIRED: model_auditor.audit_run returns a short-history dict
    without 'stuck_metrics' below five generations and train_loop reads that key
    unconditionally -- a latent defect recorded in the batch receipt, not
    silently patched here. train_loop's CLI takes only a domain name, so the
    exercise calls train_and_audit directly."""
    code = ("from core.train_loop import train_and_audit; import json;"
            " print(json.dumps(train_and_audit(%r, pop=%d, gens=%d)))" % (domain, pop, gens))
    command = [sys.executable, '-B', '-c', code]
    try:
        result = subprocess.run(command, cwd=str(ROOT / 'Chimera'),
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                timeout=timeout, text=True, errors='replace')
        return {'domain': domain, 'command': command, 'exit_code': result.returncode,
                'output_sha256': sha(result.stdout.encode(errors='replace')),
                'output_tail': result.stdout[-2000:],
                'completed': result.returncode == 0}
    except subprocess.TimeoutExpired:
        return {'domain': domain, 'command': command, 'exit_code': None,
                'completed': False, 'failure': 'timeout'}
