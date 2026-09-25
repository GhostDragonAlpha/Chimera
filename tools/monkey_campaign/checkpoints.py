"""Read-only checkpoint evidence checks. No visual judgment or acceptance authority."""
import hashlib
import json
import math
from pathlib import Path, PureWindowsPath
import re
import stat

from integrity import unique_object, reject_constant

ORDER = ('implementation', 'numerical', 'runtime', 'visual', 'review', 'human')
KINDS = {'offline', 'visible_static', 'motion', 'final_playthrough'}
STATUSES = {'pending', 'pass', 'fail', 'inconclusive'}
REQUIRED_EVIDENCE = {
    'implementation': {'changes'}, 'numerical': {'results'},
    'runtime': {'commands', 'telemetry'}, 'visual': {'capture', 'inspection'},
    'review': {'review'}, 'human': {'acceptance'},
}
MAX_JSON = 1024 * 1024
MAX_EVIDENCE = 512 * 1024 * 1024  # Bounded per invocation; split larger captures.
NEXT = {
    'implementation': 'Implement the scoped change and record its exact candidate identity',
    'numerical': 'Run the preregistered checks; retain results and failures',
    'runtime': 'Reserve the runtime and replay the declared scenario with command/state traces',
    'visual': 'Capture and actually inspect the affected behavior; retain the inspection record',
    'review': 'Obtain independent review of this candidate and its evidence',
    'human': 'Present this candidate for explicit operator acceptance; do not infer consent',
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def finite_tree(value):
    if isinstance(value, float):
        require(math.isfinite(value), 'nonfinite_receipt_value')
    elif isinstance(value, dict):
        for child in value.values():
            finite_tree(child)
    elif isinstance(value, list):
        for child in value:
            finite_tree(child)


def document_bytes(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_JSON + 1)
    require(len(raw) <= MAX_JSON, 'json_size_limit')
    return raw


def decode_document(raw):
    value = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique_object,
                       parse_constant=reject_constant)
    finite_tree(value)
    require(isinstance(value, dict), 'document_must_be_object')
    return value


def load_document(path):
    return decode_document(document_bytes(path))


def validate_context(ctx, scope_sha256):
    require(ctx.get('schema') == 'chimera.checkpoint_context.v1', 'invalid_context_schema')
    require(ctx.get('scope_sha256') == scope_sha256, 'context_scope_mismatch')
    for key in ('task_id', 'controller_task', 'run_id', 'worker_id'):
        require(isinstance(ctx.get(key), str) and bool(ctx[key].strip()), 'missing_context_' + key)
    require(type(ctx.get('generation')) is int and ctx['generation'] >= 0, 'invalid_generation')
    for key in ('subject_sha256', 'criteria_sha256'):
        require(digest(ctx.get(key)), 'invalid_context_' + key)
    kind = ctx.get('kind')
    require(kind in KINDS, 'invalid_checkpoint_kind')
    gates = ctx.get('required_gates')
    require(isinstance(gates, list) and gates and all(isinstance(g, str) and g in ORDER for g in gates),
            'invalid_required_gates')
    require(gates == [g for g in ORDER if g in gates], 'duplicate_or_unordered_gates')
    minimum = {'implementation', 'review'}
    if kind != 'offline':
        minimum |= {'numerical', 'runtime', 'visual'}
    if kind == 'final_playthrough':
        minimum.add('human')
    require(minimum <= set(gates), 'required_checkpoint_waived')
    if kind == 'offline':
        require(isinstance(ctx.get('nonvisual_reason'), str) and ctx['nonvisual_reason'].strip(),
                'predeclared_nonvisual_reason_required')
    return gates


def evidence_hash(root, record, budget):
    require(isinstance(record, dict) and digest(record.get('sha256')), 'invalid_evidence_record')
    rel = record.get('path')
    require(isinstance(rel, str) and rel and '\\' not in rel and ':' not in rel,
            'evidence_path_must_be_relative_posix')
    require(not PureWindowsPath(rel).is_absolute() and not rel.startswith('/')
            and all(p not in ('', '.', '..') for p in rel.split('/')), 'evidence_path_escape')
    root = Path(root).absolute()
    for parent in (root, *root.parents):
        info = parent.lstat()
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400,
                'evidence_root_link_refused')
    path = root
    for piece in rel.split('/'):
        path = path / piece
        info = path.lstat()
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400,
                'evidence_link_refused')
    require(stat.S_ISREG(info.st_mode) and info.st_size > 0, 'evidence_not_nonempty_file')
    require(info.st_size <= budget[0], 'evidence_read_budget_exceeded')
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            budget[0] -= len(chunk)
            require(budget[0] >= 0, 'evidence_read_budget_exceeded')
            h.update(chunk)
    require(h.hexdigest() == record['sha256'], 'evidence_hash_mismatch:' + rel)
    return path


def check(receipt, ctx, context_sha256, scope_sha256, evidence_root):
    finite_tree(receipt)
    finite_tree(ctx)
    require(digest(context_sha256), 'invalid_context_pin')
    gates = validate_context(ctx, scope_sha256)
    require(receipt.get('schema') == 'chimera.checkpoint_receipt.v1', 'invalid_receipt_schema')
    require(receipt.get('context_sha256') == context_sha256, 'context_pin_mismatch')
    for key in ('scope_sha256', 'task_id', 'controller_task', 'generation', 'subject_sha256',
                'criteria_sha256', 'run_id'):
        require(type(receipt.get(key)) is type(ctx[key]) and receipt.get(key) == ctx[key],
                'receipt_context_mismatch:' + key)
    rows = receipt.get('gates')
    require(isinstance(rows, dict) and set(rows) <= set(gates), 'unknown_or_waived_gate')
    for name, row in rows.items():
        require(isinstance(row, dict) and row.get('status') in STATUSES, 'invalid_gate_status:' + name)
    out = {
        'mode': 'STRUCTURE_AND_HASH_CHECK_ONLY', 'goal_complete': False,
        'task_id': ctx['task_id'], 'run_id': ctx['run_id'],
        'ready_for_controller_review': False, 'verified_gate_records': [],
        'next_checkpoint': None, 'next_action': None,
        'limits': 'No pixels, physics, reviewer identity or human consent authenticated. '
                  'The controller must verify provenance and actual judgments before acceptance.',
    }
    budget = [MAX_EVIDENCE]
    for field, pin in (('subject_manifest', 'subject_sha256'), ('criteria_manifest', 'criteria_sha256')):
        record = receipt.get(field)
        require(isinstance(record, dict) and record.get('sha256') == ctx[pin], 'manifest_pin_mismatch:' + field)
        evidence_hash(evidence_root, record, budget)
    for name in gates:
        row = rows.get(name, {'status': 'pending'})
        state = row['status']
        if state != 'pass':
            out.update(next_checkpoint=name, checkpoint_status=state,
                       next_action=('Repair the evidenced failure, then repeat this checkpoint: ' if state == 'fail' else '')
                                   + NEXT[name])
            return out
        require(row.get('run_id') == ctx['run_id'] and row.get('subject_sha256') == ctx['subject_sha256'],
                'stale_gate_identity:' + name)
        require(isinstance(row.get('actor_id'), str) and row['actor_id'].strip(), 'gate_actor_missing:' + name)
        if name in {'visual', 'review'}:
            require(row['actor_id'] != ctx['worker_id'], 'independent_reviewer_required:' + name)
        evidence = row.get('evidence')
        require(isinstance(evidence, dict) and REQUIRED_EVIDENCE[name] <= set(evidence)
                and len(evidence) <= 16, 'gate_evidence_missing:' + name)
        for record in evidence.values():
            evidence_hash(evidence_root, record, budget)
        if name == 'visual':
            capture = evidence['capture']
            if ctx['kind'] in {'motion', 'final_playthrough'}:
                require(capture.get('kind') == 'video' and Path(capture['path']).suffix.lower() in {'.mp4', '.webm', '.mkv'},
                        'motion_requires_recording')
            else:
                require(capture.get('kind') in {'image', 'video'}, 'visual_capture_kind_missing')
            interval = row.get('tick_interval')
            runtime = rows.get('runtime', {})
            require(isinstance(interval, list) and len(interval) == 2
                    and all(type(v) is int and v >= 0 for v in interval) and interval[0] <= interval[1]
                    and interval == runtime.get('tick_interval'), 'capture_runtime_interval_mismatch')
            if ctx['kind'] in {'motion', 'final_playthrough'}:
                require(interval[0] < interval[1], 'motion_interval_empty')
        if name == 'human':
            require(row.get('source_kind') == 'operator_message' and row.get('source_reference'),
                    'human_source_reference_required')
            # A JSON claim is never a human signature. External verification remains mandatory.
        out['verified_gate_records'].append(name)
    out.update(ready_for_controller_review=True, next_checkpoint='controller_acceptance',
               next_action='Authenticate the evidence sources and actual judgments; submit through the existing '
                           'review/publication path, then refill the freed slot. For the final playthrough, '
                           'verify explicit operator acceptance of this exact candidate before closing the goal.')
    return out


def check_files(receipt_path, context_path, context_sha256, scope_sha256, evidence_root):
    require(digest(context_sha256), 'invalid_context_pin')
    raw = document_bytes(context_path)
    require(hashlib.sha256(raw).hexdigest() == context_sha256, 'context_file_changed')
    return check(load_document(receipt_path), decode_document(raw), context_sha256,
                 scope_sha256, evidence_root)
