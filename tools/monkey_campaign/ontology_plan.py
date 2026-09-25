"""Validate and project the one task catalog into its membrane ontology.

Logical layers describe prerequisites, never elapsed time or earned acceptance.
Integration checkpoint contributors do not depend on their own checkpoint.
"""
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path

from campaign import validate_catalog, selected_tasks
from integrity import content_digest, unique_object, reject_constant
import json

HERE = Path(__file__).resolve().parent
CAMERA_FIELDS = {
    'frame_id', 'coordinate_unit', 'position', 'orientation_convention_and_values',
    'target', 'distance_to_target', 'projection', 'vertical_fov_or_orthographic_span',
    'near_far_planes', 'aspect_ratio', 'viewport_resolution',
    'camera_motion_or_bookmark_sequence', 'visibility_layers', 'label_ids',
    'occlusion_or_xray_mode', 'state_or_tick_interval',
}


def require(ok, code):
    if not ok:
        raise ValueError(code)


def dependency_layers(by, field='depends_on'):
    remaining, assigned, layers = set(by), set(), []
    while remaining:
        ready = sorted(k for k in remaining if set(by[k][field]) <= assigned)
        require(ready, 'ontology_dependency_cycle_or_unknown')
        layers.append(ready)
        assigned.update(ready)
        remaining.difference_update(ready)
    return layers


def named(rows, label):
    require(isinstance(rows, list) and rows, 'missing_' + label)
    out = {}
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get('id'), str)
                and row['id'] and row['id'] not in out, 'invalid_or_duplicate_' + label)
        out[row['id']] = row
    return out


def references(value, allowed, label, nonempty=False):
    require(isinstance(value, list) and all(isinstance(v, str) for v in value)
            and len(set(value)) == len(value) and set(value) <= set(allowed)
            and (bool(value) or not nonempty), 'invalid_' + label)


def project(catalog, nodes=None, definition_raw_sha256=None):
    by = validate_catalog(catalog)
    contract = catalog.get('ontology_contract')
    require(isinstance(contract, dict) and contract.get('schema') == 'chimera.ontology_work_plan.v1',
            'missing_ontology_contract')
    require(contract.get('definition_path') == 'tools/membrane_ontology/ontology.json',
            'unexpected_ontology_definition_path')
    if nodes is None:
        path = HERE.parent / 'membrane_ontology'
        spec = importlib.util.spec_from_file_location('chimera_ontology_definition', path / 'model.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        raw = (path / 'ontology.json').read_bytes()
        nodes = module.validate(module.decode(raw))
        definition_raw_sha256 = hashlib.sha256(raw).hexdigest()
    require(contract.get('definition_raw_sha256') == definition_raw_sha256,
            'ontology_definition_pin_mismatch')
    profiles = named(contract.get('visual_profiles'), 'verification_profile')
    checkpoints = named(contract.get('checkpoints'), 'checkpoint')
    connections = {k for k, n in nodes.items() if n['kind'] == 'connection'}
    for profile in profiles.values():
        require(profile.get('kind') in {'offline', 'visible_static', 'motion', 'final_playthrough'},
                'invalid_profile_kind')
        for key in ('subject', 'scenario', 'falsifier'):
            require(isinstance(profile.get(key), str) and profile[key].strip(), 'missing_profile_' + key)
        require(profile.get('numerical_evidence_required') is True, 'numerical_evidence_waived')
        if profile['kind'] == 'offline':
            require(bool(profile.get('nonvisual_reason')), 'nonvisual_reason_required')
        else:
            for key in ('views', 'diagnostic_layers'):
                require(isinstance(profile.get(key), list) and profile[key]
                        and all(isinstance(v, str) and v for v in profile[key]), 'missing_profile_' + key)
            require(type(profile.get('clean_view_required')) is bool, 'clean_view_requirement_missing')
            require(isinstance(profile.get('camera_required_fields'), list)
                    and CAMERA_FIELDS <= set(profile['camera_required_fields']), 'camera_requirements_missing')
    for tid, task in by.items():
        mapping = task.get('ontology')
        require(isinstance(mapping, dict), 'task_ontology_missing:' + tid)
        require(mapping.get('primary_membrane') in nodes, 'primary_membrane_missing:' + tid)
        references(mapping.get('related_membranes'), nodes, 'related_membranes:' + tid)
        references(mapping.get('connection_ids'), connections, 'connection_ids:' + tid)
        references(mapping.get('checkpoint_ids'), checkpoints, 'checkpoint_ids:' + tid)
        require(mapping.get('verification_profile') in profiles, 'unknown_profile:' + tid)
        require(mapping.get('scenario_scope') == task['done_when'], 'scenario_scope_mismatch:' + tid)
        reasons = task.get('dependency_reasons', {})
        require(isinstance(reasons, dict) and set(reasons) <= set(task['depends_on'])
                and all(isinstance(v, str) and v for v in reasons.values()), 'invalid_dependency_reasons:' + tid)
    for cid, checkpoint in checkpoints.items():
        references(checkpoint.get('task_ids'), by, 'checkpoint_tasks:' + cid, True)
        references(checkpoint.get('membrane_ids'), nodes, 'checkpoint_membranes:' + cid, True)
        references(checkpoint.get('requires'), checkpoints, 'checkpoint_requires:' + cid)
        require(checkpoint.get('profile_id') in profiles, 'checkpoint_profile_missing:' + cid)
        require(isinstance(checkpoint.get('acceptance'), str) and checkpoint['acceptance'],
                'checkpoint_acceptance_missing:' + cid)
        for tid in checkpoint['task_ids']:
            require(cid in by[tid]['ontology']['checkpoint_ids'], 'checkpoint_task_mapping_mismatch:' + cid)
    for tid, task in by.items():
        for cid in task['ontology']['checkpoint_ids']:
            require(tid in checkpoints[cid]['task_ids'], 'task_checkpoint_mapping_mismatch:' + tid)
    dependency_layers(checkpoints, 'requires')
    layers = dependency_layers(by)
    layer_by = {tid: i for i, layer in enumerate(layers) for tid in layer}
    selected = selected_tasks(by)
    tasks = []
    for tid in sorted(by):
        task = deepcopy(by[tid])
        task.update(selected=tid in selected, dependency_layer=layer_by[tid],
                    verification_profile=deepcopy(profiles[task['ontology']['verification_profile']]))
        task['verification_profile']['scenario'] = (
            'Qualify only this task: ' + task['ontology']['scenario_scope'] +
            ' Profile procedure: ' + task['verification_profile']['scenario'] +
            ' Use the task-owned subset of layers/behaviors. Inventory absent or unresolved components explicitly; '
            'do not require downstream skills to accept an upstream interface. Freeze exact applicable probes and views before execution.')
        tasks.append(task)
    gates = [dict(deepcopy(c), verification_profile=deepcopy(profiles[c['profile_id']]))
             for c in checkpoints.values()]
    return dict(scope_sha256=content_digest(catalog), task_count=len(by), selected_count=len(selected),
                task_status_policy='Planned requirements; reconcile current receipts. No earned acceptance inferred.',
                checkpoint_policy='Integration milestones after contributor evidence; never prerequisites for their own contributor tasks. Independent implementation may proceed earlier.',
                dependency_layers=layers, checkpoints=gates, tasks=tasks,
                definition_raw_sha256=definition_raw_sha256)


def load_catalog(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(2 * 1024 * 1024 + 1)
    require(len(raw) <= 2 * 1024 * 1024, 'catalog_size_limit')
    return json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)
