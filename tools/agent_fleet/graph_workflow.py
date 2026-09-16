"""Graph-backed admission and proof gates on the existing fleet controller.

Trusted runner receipts are not worker checkboxes. This is a control-plane
boundary, not an OS sandbox: deployment must keep broker credentials private.
"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from control import require, sha, text
from review_handoff import ReviewHandoffControl
from auxiliary_graph import AuxiliaryGraph

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from creature_graph.store import CreatureGraph
from creature_graph.queries import blockers_of
from creature_graph.project_documents import verify as document_bytes


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def local_file(root, name):
    require(isinstance(name, str) and name, 'workflow_path_required')
    path = (Path(root) / name).resolve()
    require(path.is_relative_to(Path(root).resolve()), 'workflow_path_escape')
    require(path.is_file(), 'workflow_file_missing:' + name)
    return path


def candidate(repo):
    """Require committed inputs; .tmp and ignored artifacts are NOT source inputs.

    External assets/toolchains must be pinned explicitly in the graph contract.
    """
    root = Path(repo).resolve()
    def git(*args):
        p = subprocess.run(['git', '-c', 'safe.directory=' + root.as_posix(),
                            '-C', str(root), *args], capture_output=True, text=True)
        require(p.returncode == 0, 'workflow_git_failed')
        return p.stdout.strip()
    require(not git('status', '--porcelain', '--untracked-files=normal'),
            'workflow_candidate_not_clean')
    return {'head': git('rev-parse', 'HEAD'), 'tree': git('rev-parse', 'HEAD^{tree}')}


def unpack(payload):
    g = CreatureGraph()
    g.objects = copy.deepcopy(payload['objects'])
    g.relations = copy.deepcopy(payload['relations'])
    g.layout = copy.deepcopy(payload.get('layout', {}))
    g.meta = copy.deepcopy(payload.get('meta', {}))
    return g


def pack(g):
    return {'objects': g.objects, 'relations': g.relations, 'layout': g.layout, 'meta': g.meta}


def binding(g, work_id):
    require(not g.check(), 'workflow_graph_invalid')
    require(work_id in g.objects, 'workflow_unknown_graph_work')
    work = g.get(work_id)
    require(work['kind'] == 'work', 'workflow_not_work')
    require(not blockers_of(g, work_id), 'workflow_graph_dependencies_unavailable')
    contract = work.get('execution_workflow')
    require(isinstance(contract, dict), 'workflow_graph_checklist_missing')
    for field in ('statement', 'prediction'):
        text(contract.get(field), 'workflow_' + field)
    require(isinstance(contract.get('read_first'), list) and contract['read_first'],
            'workflow_read_first_required')
    verifier = contract.get('verifier_inputs')
    require(isinstance(verifier, dict) and verifier and all(
        isinstance(k, str) and isinstance(v, str) and len(v) == 64
        and all(c in '0123456789abcdef' for c in v) for k, v in verifier.items()),
        'workflow_verifier_pins_required')
    checks = contract.get('checks')
    require(isinstance(checks, list) and checks, 'workflow_checks_required')
    ids = []
    for check in checks:
        ids.append(text(check.get('id'), 'workflow_check_id'))
        text(check.get('falsifier'), 'workflow_falsifier')
        argv = check.get('argv')
        require(isinstance(argv, list) and argv and
                all(isinstance(x, str) and x for x in argv), 'workflow_argv_required')
        require(type(check.get('timeout_s')) is int and check['timeout_s'] > 0,
                'workflow_timeout_required')
    require(len(set(ids)) == len(ids), 'workflow_duplicate_check')
    # Pin the complete prerequisite closure, including acceptance and workflow
    # fields that intentionally are not physical-content-version fields.
    read_hashes = {}
    for oid in contract['read_first']:
        require(oid in g.objects and 'document' in g.get(oid), 'workflow_read_requires_graph_document')
        read_hashes[oid] = hashlib.sha256(document_bytes(g.get(oid))).hexdigest()
    scope, todo = set(), [work_id] + contract['read_first']
    while todo:
        oid = todo.pop()
        if oid not in scope:
            scope.add(oid)
            todo.extend(g.requires(oid))
    inputs = {'objects': {oid: g.get(oid) for oid in sorted(scope)},
              'relations': sorted([r for r in g.relations
                                   if r['src'] in scope or r['dst'] in scope],
                                  key=lambda r: r['rid'])}
    return {'work_id': work_id, 'input_hash': digest(inputs),
            'contract': copy.deepcopy(contract), 'read_hashes': read_hashes}


class GraphWorkflowControl(ReviewHandoffControl):
    """Mandatory graph gates for this service; legacy service remains explicit.

    Contract changes require a new task, not editing an in-flight checklist.
    Existing unbound tasks cannot claim/submit/integrate via this service.
    """
    graph_read_operations = ('graph_snapshot', 'workflow_context', 'workflow_view', 'workflow_verifier_context')

    def __init__(self, *args, graph_path, auxiliary_path=None, **kwargs):
        self.graph_workflow_enforced = True
        self.auxiliary = AuxiliaryGraph(auxiliary_path)
        self.graph_path = Path(graph_path).resolve()
        require(self.graph_path.is_file(), 'workflow_graph_missing')
        super().__init__(*args, **kwargs)
        con = self.connect()
        try:
            con.execute('BEGIN IMMEDIATE')
            con.execute('CREATE TABLE IF NOT EXISTS workflow_config (id INTEGER PRIMARY KEY, graph_path TEXT)')
            con.execute('INSERT OR IGNORE INTO workflow_config (id, graph_path) VALUES (1, ?)', (str(self.graph_path),))
            columns = {row[1] for row in con.execute('PRAGMA table_info(workflow_config)')}
            if 'verifier_hash' not in columns:
                con.execute('ALTER TABLE workflow_config ADD COLUMN verifier_hash TEXT')
                con.execute('UPDATE workflow_config SET verifier_hash=? WHERE id=1', (self.auxiliary.digest,))
            require(con.execute('SELECT verifier_hash FROM workflow_config WHERE id=1').fetchone()[0] == self.auxiliary.digest,
                    'independent_verifier_configuration_changed')
            stored = con.execute('SELECT graph_path FROM workflow_config WHERE id=1').fetchone()[0]
            require(stored == str(self.graph_path), 'workflow_graph_configuration_changed')
            state = json.loads(con.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
            if 'project_graph' not in state:
                graph = CreatureGraph.load(str(self.graph_path))
                require(not graph.check(), 'workflow_graph_invalid')
                state['project_graph'] = pack(graph)
                con.execute('UPDATE state SET body=? WHERE id=1', (json.dumps(state),))
            con.commit()
        finally:
            con.close()

    def current(self, state, task):
        stored = task.get('graph_workflow')
        require(stored is not None, 'workflow_unbound_task')
        now = binding(unpack(state['project_graph']), stored['work_id'])
        require(now == stored, 'workflow_graph_inputs_changed')
        return now

    def proof(self, state, task, head):
        self.current(state, task)
        receipt = task.get('workflow_receipt')
        require(receipt is not None, 'workflow_proof_required')
        require(receipt['generation'] == task['generation'], 'workflow_stale_generation')
        require(receipt['candidate']['head'] == head, 'workflow_candidate_mismatch')
        require(receipt['input_hash'] == task['graph_workflow']['input_hash'], 'workflow_stale_proof')
        self.auxiliary.validate_summary(task['graph_workflow']['work_id'], receipt.get('independent'))
        require(all(c['exit_code'] == 0 for c in (receipt.get('independent') or {}).get('logs', [])),
                'independent_checks_failed')
        expected = task['graph_workflow']['contract']['checks']
        require([c['id'] for c in receipt['checks']] == [c['id'] for c in expected],
                'workflow_missing_checks')
        require(all(type(c.get('exit_code')) is int and c['exit_code'] == 0
                    for c in receipt['checks']), 'workflow_checks_failed')
        for record in receipt['checks']:
            require(file_hash(record['log']) == record['log_sha256'], 'workflow_evidence_changed')

    def _dispatch(self, s, actor, op, p):
        if op == 'workflow_verifier_context':
            require(actor == 'SUPERVISOR', 'trusted_verifier_only')
            task = s['tasks'].get(p.get('task'))
            require(task is not None, 'unknown_task')
            self.current(s, task)
            return self.auxiliary.context(task['graph_workflow']['work_id'])
        if op == 'graph_snapshot':
            g = unpack(s['project_graph'])
            return {'graph_hash': g.graph_hash(), 'controller_revision': s['revision'],
                    'graph': pack(g)}
        if op == 'graph_apply':
            if actor != 'SUPERVISOR':
                self._lead(s, actor, p.get('epoch'))
            g = unpack(s['project_graph'])
            require(p.get('expected_hash') == g.graph_hash(), 'workflow_graph_revision_conflict')
            objects = p.get('objects')
            require(isinstance(objects, list) and objects, 'workflow_patch_required')
            ids = [o.get('id') for o in objects]
            require(len(set(ids)) == len(ids), 'workflow_duplicate_patch_id')
            for obj in objects:
                oid = obj['id']
                old = g.objects.get(oid)
                governed = ('execution_workflow', 'falsifier', 'physical')
                require(actor == 'SUPERVISOR' or all(
                    obj.get(k) == (old or {}).get(k) for k in governed),
                    'workflow_independent_contract_approval_required')
                require(obj.get('kind') != 'evidence', 'workflow_evidence_requires_measurement_api')
                require(not old or old.get('kind') != 'evidence', 'workflow_history_immutable')
                require(not old or 'document' not in old or old == obj, 'workflow_document_version_immutable')
                require(obj.get('status') != 'verified' or old == obj,
                        'workflow_promotion_requires_qualified_integration')
                g.objects[oid] = copy.deepcopy(obj)
            # Existing edges never disappear through an object update. A changed
            # dependency field needs a separate reviewed graph migration.
            g.sync_dependencies()
            require(not g.check(), 'workflow_graph_invalid')
            g.refresh_validation(stamp=False)
            s['project_graph'] = pack(g)
            return {'graph_hash': g.graph_hash(), 'updated': ids}
        if op == 'create_task':
            self._lead(s, actor, p.get('epoch'))
            bound = binding(unpack(s['project_graph']), text(p.get('graph_work'), 'graph_work'))
            require(not any(t.get('graph_workflow', {}).get('work_id') == bound['work_id']
                            and t['state'] not in ('ABANDONED', 'INTEGRATED')
                            for t in s['tasks'].values()), 'workflow_work_already_active')
            result = super()._dispatch(s, actor, op, p)
            result['graph_workflow'] = bound
            return result
        if op == 'workflow_view':
            return {'graph_path': str(self.graph_path), 'tasks': [
                {'task': t['id'], 'state': t['state'], 'owner': t['owner'],
                 'generation': t['generation'], 'graph_work': t.get('graph_workflow'),
                 'prepared': t.get('workflow_prepared'), 'receipt': t.get('workflow_receipt')}
                for t in s['tasks'].values()]}
        if op == 'workflow_context':
            t = s['tasks'].get(p.get('task'))
            require(t is not None, 'unknown_task')
            bound = self.current(s, t)
            return {'task': t['id'], 'generation': t['generation'],
                    'worktree': s['slots'][t['slot']]['path'] if t['slot'] else None,
                    **bound}
        if op == 'workflow_prepare':
            t = self._task(s, actor, p.get('task'), p.get('generation'),
                           instance=p.get('_resolved_instance'))
            require(t['state'] == 'RUNNING', 'workflow_task_not_running')
            bound = self.current(s, t)
            require(p.get('input_hash') == bound['input_hash'], 'workflow_wrong_contract')
            actual = bound['read_hashes']
            require(p.get('read_hashes') == actual, 'workflow_read_inputs_mismatch')
            # This proves acknowledgement of exact bytes, not comprehension.
            t['workflow_prepared'] = {'generation': t['generation'], 'read_hashes': actual,
                                      'input_hash': bound['input_hash']}
            return t['workflow_prepared']
        if op == 'workflow_attest':
            require(actor == 'SUPERVISOR', 'workflow_trusted_runner_only')
            t = s['tasks'].get(p.get('task'))
            require(t is not None and t['state'] == 'RUNNING', 'workflow_task_not_running')
            self.current(s, t)
            require(t.get('workflow_prepared', {}).get('generation') == t['generation'],
                    'workflow_prepare_required')
            receipt = copy.deepcopy(p.get('receipt'))
            require(isinstance(receipt, dict), 'workflow_receipt_required')
            require(receipt.get('generation') == t['generation'], 'workflow_stale_generation')
            root = s['slots'][t['slot']]['path']
            require(t['workflow_prepared']['read_hashes'] == t['graph_workflow']['read_hashes'],
                    'workflow_read_inputs_changed')
            pins = t['graph_workflow']['contract']['verifier_inputs']
            require(receipt.get('verifier_inputs') == pins and pins == {
                name: file_hash(local_file(root, name)) for name in pins},
                'workflow_verifier_changed')
            require(receipt.get('candidate') == candidate(root), 'workflow_candidate_mismatch')
            require(receipt.get('input_hash') == t['graph_workflow']['input_hash'], 'workflow_stale_proof')
            expected = t['graph_workflow']['contract']['checks']
            checks = receipt.get('checks')
            require(isinstance(checks, list) and len(checks) == len(expected), 'workflow_missing_checks')
            for result, spec in zip(checks, expected):
                require(result.get('id') == spec['id'] and result.get('argv') == spec['argv'],
                        'workflow_check_mismatch')
                require(type(result.get('exit_code')) is int, 'workflow_exit_code_required')
                require(file_hash(result['log']) == result['log_sha256'], 'workflow_evidence_changed')
            self.auxiliary.validate_summary(t['graph_workflow']['work_id'], receipt.get('independent'))
            # Keep failures as results; only proof() can admit the candidate.
            t.setdefault('workflow_history', []).append(receipt)
            t['workflow_receipt'] = receipt
            return {'recorded': True, 'all_passed': all(c['exit_code'] == 0 for c in checks + (receipt.get('independent') or {}).get('logs', []))}
        if op == 'claim':
            t = s['tasks'].get(p.get('task'))
            require(t is not None, 'unknown_task')
            self.current(s, t)
            result = super()._dispatch(s, actor, op, p)
            t.pop('workflow_prepared', None)
            t.pop('workflow_receipt', None)
            return result
        if op in ('resource_acquire', 'resource_request', 'submit_review'):
            t = self._task(s, actor, p.get('task'), p.get('generation'),
                           instance=p.get('_resolved_instance'))
            self.current(s, t)
            require(t.get('workflow_prepared', {}).get('generation') == t['generation'],
                    'workflow_prepare_required')
            if op == 'submit_review':
                self.proof(s, t, p.get('head'))
                root = s['slots'][t['slot']]['path']
                require(candidate(root) == t['workflow_receipt']['candidate'], 'workflow_candidate_mismatch')
        if op == 'integration_request':
            self._lead(s, actor, p.get('epoch'))
            t = s['tasks'].get(p.get('task'))
            require(t is not None, 'unknown_task')
            self.proof(s, t, p.get('head'))
        if op == 'ack_integration':
            require(actor == 'SUPERVISOR', 'trusted_publisher_only')
            request = s['requests'].get(p.get('request'))
            require(request is not None, 'unknown_integration_request')
            self.proof(s, s['tasks'][request['task']], request['head'])
        return super()._dispatch(s, actor, op, p)
