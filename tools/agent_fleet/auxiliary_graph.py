"""Operator-supplied verification graph, held outside public graph discovery."""
import copy
import hashlib
import json
from pathlib import Path
from control import require


class AuxiliaryGraph:
    def __init__(self, path=None):
        self.root = None
        self.digest = None
        self.graph = {'objects': {}, 'relations': []}
        if path is not None:
            path = Path(path).resolve()
            raw = path.read_bytes()
            self.digest = hashlib.sha256(raw).hexdigest()
            self.root = str(path.parent)
            self.graph = json.loads(raw)
            require(isinstance(self.graph.get('objects'), dict) and
                    isinstance(self.graph.get('relations'), list), 'auxiliary_graph_invalid')

    def context(self, work_id):
        selected = [self.graph['objects'][r['src']] for r in self.graph['relations']
                    if r.get('rel') == 'verifies' and r.get('dst') == work_id]
        if self.digest is not None:
            require(bool(selected), 'independent_verification_not_configured')
        checks, pins = [], {}
        for node in selected:
            require(isinstance(node.get('checks'), list) and node['checks'], 'auxiliary_checks_required')
            for check in node['checks']:
                require(isinstance(check.get('argv'), list) and check['argv'] and
                        all(isinstance(x, str) and x for x in check['argv']), 'auxiliary_argv_required')
                require(type(check.get('timeout_s')) is int and check['timeout_s'] > 0,
                        'auxiliary_timeout_required')
                checks.append(copy.deepcopy(check))
            require(isinstance(node.get('verifier_inputs'), dict) and node['verifier_inputs'],
                    'auxiliary_verifier_pins_required')
            for name, expected in node['verifier_inputs'].items():
                require(name not in pins or pins[name] == expected, 'auxiliary_pin_conflict')
                pins[name] = expected
        require(len({c['id'] for c in checks}) == len(checks), 'auxiliary_duplicate_check')
        return {'digest': self.digest, 'root': self.root, 'checks': checks, 'verifier_inputs': pins}

    def validate_summary(self, work_id, summary):
        context = self.context(work_id)
        if not context['checks']:
            require(summary is None, 'unexpected_independent_receipt')
            return
        require(isinstance(summary, dict) and summary.get('digest') == self.digest,
                'independent_receipt_required')
        logs = summary.get('logs')
        require(isinstance(logs, list) and len(logs) == len(context['checks']), 'independent_checks_missing')
        for log in logs:
            require(type(log.get('exit_code')) is int, 'independent_result_missing')
            require(hashlib.sha256(Path(log['path']).read_bytes()).hexdigest() == log['sha256'],
                    'independent_evidence_changed')


def run(context, candidate_root, output):
    """Trusted broker only. No case names/argv are returned to the worker."""
    import subprocess
    from graph_workflow import file_hash, local_file
    if not context['checks']:
        return None
    pins = context['verifier_inputs']
    require(pins == {name: file_hash(local_file(context['root'], name)) for name in pins},
            'independent_verifier_changed')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    logs = []
    for i, check in enumerate(context['checks']):
        argv = [s.replace('{candidate}', str(candidate_root)).replace('{verifier}', context['root'])
                for s in check['argv']]
        path = output / (str(i) + '.log')
        with path.open('wb') as stream:
            try:
                code = subprocess.run(argv, cwd=context['root'], stdout=stream,
                                      stderr=subprocess.STDOUT, timeout=check['timeout_s']).returncode
            except subprocess.TimeoutExpired:
                stream.write(b'CHECK_TIMEOUT\n'); code = 124
            except OSError:
                stream.write(b'CHECK_LAUNCH_FAILED\n'); code = 127
        logs.append({'path': str(path), 'sha256': file_hash(path), 'exit_code': code})
    return {'digest': context['digest'], 'logs': logs}
