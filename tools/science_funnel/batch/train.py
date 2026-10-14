"""Batch-gated trainer hook. The gate is the batch's own law: training may only
run on a proven library state (graph valid + zero contract failures + count
identity closed). The exercise runs trainer domains in child processes; no ML
quality is claimed -- this proves the wiring, not a policy."""
import subprocess
import sys
from pathlib import Path

from ..common import canonical, require, sha

ROOT = Path(__file__).resolve().parents[3]
# The documented canonical domain (train_loop docstring example) PLUS the domain
# the trainer-spine repair unblocked: pref_selftest used to predate the
# seed(rng) protocol and died with a TypeError under train_and_audit; the spine
# now probes the protocol and pref_selftest accepts the rng
# (work.data.trainer_spine_repair_20260917). arrangement still refuses without
# a scan (by design) and is therefore NOT an exercise domain.
EXERCISE_DOMAINS = ('erisaid_mirror', 'pref_selftest')
# Retained name for the recorded canonical domain (receipts and replay logs
# older than the repair name it singly).
EXERCISE_DOMAIN = EXERCISE_DOMAINS[0]


def batch_gate(graph, batch_summary):
    """Derive-before-train at batch scale: the gate refuses unless the whole
    batch proven (graph checks clean, zero contract failures, identity closed)."""
    require(not graph.check(), 'train_gate_graph_invalid')
    require(batch_summary['totals']['contract_failures'] == 0,
            'train_gate_contract_failures')
    require(batch_summary['count_identity']['closed'], 'train_gate_count_identity_open')
    return {'gate': 'closed-proven-library-state', 'passed': True}


def _run_one(domain, pop, gens, timeout):
    """Run one trainer domain in a child process; capture and hash its output.

    train_loop's CLI takes only a domain name, so the exercise calls
    train_and_audit directly. Since work.data.trainer_spine_repair_20260917 the
    audit dict has ONE shape at every history length (the old short-history
    dict without 'stuck_metrics' below five generations is gone), so no
    generation floor is required here; gens=5 stays the recorded default."""
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


def exercise(domains=EXERCISE_DOMAINS, pop=6, gens=5, timeout=300):
    """Run every exercise domain in a child process; record each run in the
    returned receipt dict under 'runs', keyed by domain."""
    runs = {domain: _run_one(domain, pop, gens, timeout) for domain in domains}
    return {'domains': list(domains), 'pop': pop, 'gens': gens,
            'runs': runs,
            'completed': all(run['completed'] for run in runs.values())}
