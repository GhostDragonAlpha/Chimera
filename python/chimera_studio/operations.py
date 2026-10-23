# SPDX-License-Identifier: AGPL-3.0-or-later
"""Revision-checked Blender commands shared by human buttons and local AI callers.
No network listener, arbitrary Python executor, simulation law or evidence catalog.
"""
import contextlib
import copy
import hashlib
import json
import math
import threading
import time
import uuid

import numpy as np
import bpy
import bmesh
from bpy.app.handlers import persistent
from . import blocks, blocks_ui, gpu_workspace as workspace, layer_editing

TEXT = 'Chimera Operations.json'
SCHEMA = 'chimera.studio.operations.v1'
MAX_RECORDS = 64
MAX_BYTES = 512 * 1024
_records = {}
# action: (existing Blender operator, target-count range, native asynchronous)
PAINT_ACTIONS={'set_cloth_stiffness_region','clear_cloth_stiffness_region','apply_published_material','set_layer_region_weights','set_layer_pin_region','edit_layer_material','apply_layer_preset','set_layer_attachment','rebind_layer_attachment','detach_layer_cache','activate_layer_cache','bake_layers','cancel_layer_bake','capture_layers','compare_layers','show_layer_trials','clear_layer_preview'}
WORKFLOW_ACTIONS={'begin_workflow_trial','finish_workflow_trial','compare_workflow_trials','cancel_workflow_trial'}
RESPONSE_ASSET_ACTIONS={'export_response_asset','import_response_asset'}
PORT_ACTIONS = {'learn_port_response','measure_port_response','show_port_response','cancel_port_response','compose_port_responses','show_port_assembly','learn_condensed_response','measure_condensed_response','show_condensed_response','qualify_scaled_response','measure_scaled_response','show_scaled_response','use_scaled_response_card'}
EXPLANATION_ACTIONS={'explain_layer_trials','prepare_layer_alternative'}
PAINT_ACTIONS |= EXPLANATION_ACTIONS
AUTHOR_ACTIONS=PAINT_ACTIONS|{'set_layer_drive','create_physical_copy','remember_layer_cache','relocate_layer_cache'}
LAYER_SEARCH_ACTIONS={'search_layer_material','cancel_layer_search','use_layer_search_result'}
ACTIONS = {
    **{a:('chimera.workflow_outcome',(0,0),False) for a in WORKFLOW_ACTIONS},
    **{a:('chimera.response_asset',(0,0),False) for a in RESPONSE_ASSET_ACTIONS},
    **{a:('chimera.layer_search',(1,2) if a=='search_layer_material' else (0,0),a!='cancel_layer_search') for a in LAYER_SEARCH_ACTIONS},
    **{a:('chimera.explain_layer_trials',(0,0),False) for a in EXPLANATION_ACTIONS},
    'create_physical_copy':('chimera.create_physical_copy',(0,0),False),
    **{a:('chimera.port_response',(0,0),a in ('learn_port_response','measure_port_response','compose_port_responses','learn_condensed_response','measure_condensed_response','qualify_scaled_response','measure_scaled_response')) for a in PORT_ACTIONS},
    **{a:('chimera.layer_operation',n,a in layer_editing.ASYNC_ACTIONS) for a,n in layer_editing.ACTIONS.items()},
    'learn_procedure': ('chimera.learn_procedure', (0, 0), False),
    'run_procedure': ('chimera.run_procedure', (0, 0), True),
    'cancel_procedure': ('chimera.cancel_procedure', (0, 0), False),
    'forget_procedure': ('chimera.forget_procedure', (0, 0), False),
    'search_adaptive': ('chimera.search_adaptive', (0, 0), True),
    'cancel_adaptive_search': ('chimera.cancel_adaptive_search', (0, 0), False),
    'select_adaptive_result': ('chimera.select_adaptive_result', (0, 0), False),
    'create_adaptive_result': ('chimera.create_adaptive_result', (0, 0), False),
    'search_designs': ('chimera.search_designs', (0, 0), True),
    'cancel_design_search': ('chimera.cancel_design_search', (0, 0), False),
    'select_design': ('chimera.select_design', (0, 0), False),
    'create_design': ('chimera.create_design', (0, 0), False),
    "create_mounted_panel": ("chimera.add_mounted_panel", (0, 0), False),
    'render_native': ('chimera.native_render_frame', (0, 0), True),
    'cancel_comparison': ('chimera.cancel_comparison', (0, 0), False),
    'search_material': ('chimera.search_material', (0, 0), True),
    'cancel_material_search': ('chimera.cancel_material_search', (0, 0), False),
    'select_material_result': ('chimera.select_material_result', (0, 0), False),
    'learn_assembly': ('chimera.learn_assembly', (0, 0), False),
    'instantiate_assembly': ('chimera.instantiate_assembly', (0, 0), False),
    'clear_layer_preview': ('chimera.clear_layer_preview', (0, 0), False),
    'capture_layers': ('chimera.capture_layer_trial', (0, 0), False),
    'compare_layers': ('chimera.compare_layer_trials', (0, 0), False),
    'show_layer_trials': ('chimera.compare_layer_trials', (0, 0), False),
    'link_evidence': ('chimera.link_recipe_evidence', (0, 0), False),
    'capture_trial': ('chimera.capture_trial', (0, 0), False),
    'compare_trials': ('chimera.compare_trials', (0, 0), True),
    'create_films': ('chimera.add_membrane_assembly', (0, 0), False),
    'assign_surface': ('chimera.assign_membrane_material', (1, 6), False),
    'mark_apex': ('chimera.mark_membrane_apex', (1, 1), False),
    'connect_apices': ('chimera.connect_membrane_apices', (2, 2), False),
    'disconnect_apices': ('chimera.disconnect_membrane_apices', (2, 2), False),
    'build_films': ('chimera.build_membrane_assembly', (2, 6), True),
    'apply_load': ('chimera.gpu_load', (0, 0), True),
    'resume': ('chimera.gpu_resume', (0, 0), True),
    'replay': ('chimera.gpu_seek', (0, 0), True),
    'release': ('chimera.gpu_release', (0, 0), False),
    'authoring': ('chimera.gpu_authoring', (0, 0), False),
    'learn_native_warm_start': ('chimera.learn_native_warm_start',(0,0),False),
    'set_native_warm_start': ('chimera.set_native_warm_start',(0,0),True),
    'duplicate_layers': ('uipc.duplicate_construction', (1, 128), False),
}


def main_thread():
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError('Call Studio operations on Blender main thread')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def target_id(obj):
    if obj.get('chimera_block_id') and not obj.get('chimera_gpu_preview'):
        return 'membrane:' + obj['chimera_block_id']
    if hasattr(obj, 'uipc_body') and obj.uipc_body.role != 'NONE' and obj.get('uipc_object_id'):
        return 'uipc:' + obj['uipc_object_id']
    return None


def resolve(context, targets):
    result = []
    for key in targets:
        hits = [o for o in context.scene.objects if target_id(o) == key]
        if len(hits) != 1:
            raise ValueError('Missing or duplicate part identity: ' + key)
        obj = hits[0]
        if obj.type != 'MESH' or obj.library or obj.data.library:
            raise ValueError(obj.name + ': use a local editable mesh')
        if context.view_layer.objects.get(obj.name) != obj:
            raise ValueError(obj.name + ': include it in the active view layer')
        if obj.hide_get() or obj.hide_viewport or obj.hide_select:
            raise ValueError(obj.name + ': return to authoring and make this source selectable')
        result.append(obj)
    return result


def _source(context):
    context.view_layer.update()
    if hasattr(context.scene,'uipc_settings'):layer_editing.module(context.scene)
    parts = []
    for obj in sorted(context.scene.objects, key=lambda o: o.name):
        key = target_id(obj)
        if key is None:
            continue
        if obj.mode == 'EDIT':
            obj.update_from_editmode()
        if obj.type != 'MESH':
            raise ValueError(obj.name + ': physical source is not a mesh')
        item = {'id': key, 'name': obj.name,
                'matrix': [list(r) for r in obj.matrix_world],
                'vertices': [list(v.co) for v in obj.data.vertices],
                'edges': [list(e.vertices) for e in obj.data.edges],
                'faces': [list(f.vertices) for f in obj.data.polygons],
                'modifiers': [(m.name, m.type, m.show_viewport, m.show_render) for m in obj.modifiers]}
        if key.startswith('membrane:'):
            item.update(apex=obj.get('chimera_free_center'), gamma=obj.get('chimera_film_gamma'))
        else:
            # Reuse libuipc's actual material exporter; do not guess its RNA fields.
            import importlib
            package = type(obj.uipc_body).__module__
            bridge = importlib.import_module(package + '.bridge')
            item['material'] = bridge.object_material(obj)
            if 'chimera_published_material' in obj:item['published_material_reference']=obj['chimera_published_material']
            if 'chimera_cloth_reference_frame' in obj:item['cloth_reference_frame']=obj['chimera_cloth_reference_frame']
            if 'chimera_cloth_stiffness_region' in obj:item['cloth_stiffness_region']=obj['chimera_cloth_stiffness_region']
            item['tetrahedra'] = list(obj.data.get('uipc_tetrahedra',[]))
            item['groups'] = [(g.name, g.index) for g in obj.vertex_groups]
            item['weights'] = [[(g.group, g.weight) for g in v.groups] for v in obj.data.vertices]
            if obj.get('chimera_affine_component'):
                from . import reduced_components
                item['component_reduction'] = obj['chimera_affine_component']
                mesh = obj.chimera_detailed_mesh
                item['detailed_component'] = None if mesh is None else {'vertices':[list(v.co) for v in mesh.vertices], 'faces':[list(f.vertices) for f in mesh.polygons], 'tets':list(mesh.get('uipc_tetrahedra',[])), 'groups':reduced_components.groups(obj,mesh)}
        parts.append(item)
    source = {'parts': parts, 'connections': json.loads(context.scene.chimera_blocks.connections),
              'unit_scale': context.scene.unit_settings.scale_length}
    if hasattr(context.scene, 'uipc_settings'):
        from . import layer_joints
        source['native_hinges']=layer_joints.rows(context.scene)
        source['layer_seams'] = [dict(name=e.name, a=target_id(e.object_a) if e.object_a else None,
            b=target_id(e.object_b) if e.object_b else None, enabled=e.enabled, binding=e.binding,
            group_a=e.group_a, group_b=e.group_b, stiffness=e.stiffness, pairing=e.pairing,
            reverse_b=e.reverse_b) for e in context.scene.uipc_settings.attachments]
    return source


def _source_match(context, doc):
    """Compare authoring with the accepted assembly; do not rebuild or rewind it."""
    if doc is None or 'assembly' not in doc['spec']:
        return None, 'No compiled assembly correspondence to check'
    try:
        if abs(context.scene.unit_settings.scale_length-1)>1e-9:
            raise ValueError('Unit Scale changed; compiled assembly uses meters')
        ids={p['id'] for p in doc['spec']['assembly']['parts']}
        parts=[]
        for key in sorted(ids):
            hits=[o for o in context.scene.objects if o.get('chimera_block_id')==key and not o.get('chimera_gpu_preview')]
            if len(hits)!=1:raise ValueError('Missing or duplicate compiled source: '+key)
            parts.append(blocks_ui.part(hits[0]))
        connections=[e for e in json.loads(context.scene.chimera_blocks.connections) if any(i in ids for i in e)]
        compiled=blocks.compile_parts(parts,connections)
        def physical(spec):
            value=copy.deepcopy(spec)
            # Labels may change without changing the physical construction.
            for collection in ('parts','regions'):
                for part in value['assembly'][collection]:part.pop('name',None)
            return value
        matches=physical(compiled)==physical(doc['spec'])
        return matches, ('Sources match the accepted native assembly' if matches else
                         'Source geometry, material or connections changed; rebuild explicitly')
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        return False, 'Accepted checkpoint retained; source needs repair/rebuild: '+str(error)


def _connections_report(source, doc):
    """Name each apex weld's authored/accepted state so a human or AI can repair
    exactly one broken connection instead of guessing behind needs_rebuild.
    Report only: this never compiles, rebuilds or changes build filtering."""
    spec = doc['spec']['assembly'] if doc and 'assembly' in doc['spec'] else None
    names = {p['id']: p['name'] for p in source['parts']}
    if spec:
        for p in spec['parts']:
            names.setdefault(p['id'], p['name'])
    edges = {}
    for label, items in (('authored', source['connections']),
                         ('accepted', spec['connections'] if spec else [])):
        for e in items:
            key = tuple(sorted(e))
            entry = edges.setdefault(key, {'edge': [key[0], key[1]],
                'names': [names.get(key[0], key[0]), names.get(key[1], key[1])]})
            entry[label] = True
    for entry in edges.values():
        entry['stale'] = bool(entry.get('authored')) and not entry.get('accepted')
        entry['missing'] = bool(entry.get('accepted')) and not entry.get('authored')
    return sorted(edges.values(), key=lambda item: item['edge'])


def _regions_report(doc):
    """Per-film area and energy from the accepted membrane assembly.

    Decomposes the declared law U = gamma * sum(face_area) exactly: each
    region's face list partitions spec['triangles'], so Heron areas of the
    accepted float32 positions times the uniform gamma sum to native energy_J
    (independently re-checked in tests). This is Blender-side arithmetic on
    accepted native geometry, NOT an independent native measurement; the sum
    is checked against state['energy_J'] and the report fails closed (no
    numbers) if they disagree or no accepted membrane doc exists.
    """
    if not (doc and 'assembly' in doc['spec']):
        return {'available': False,
                'reason': 'Region energy needs a built membrane assembly; build or resume one first'}
    try:
        spec, state = doc['spec'], doc['state']
        faces = np.asarray(spec['triangles'])
        claimed = sorted(int(f) for r in spec['assembly']['regions'] for f in r['faces'])
        if claimed != list(range(len(faces))):
            raise ValueError('region face lists are not the exact triangle partition')
        positions = np.asarray(state['positions_f32'], dtype='<f4').astype(float).reshape(-1, 3)
        if len(positions) != len(spec['positions']):
            raise ValueError('accepted state vertex count does not match the compiled spec')
        gamma = float(spec['gamma'])
        regions = []
        for region in spec['assembly']['regions']:
            v = positions[faces[np.asarray(region['faces'])]]
            ab = np.linalg.norm(v[:, 1] - v[:, 0], axis=1)
            bc = np.linalg.norm(v[:, 2] - v[:, 1], axis=1)
            ca = np.linalg.norm(v[:, 0] - v[:, 2], axis=1)
            s = (ab + bc + ca) * .5
            area = float(np.sqrt(np.maximum(0., s * (s - ab) * (s - bc) * (s - ca))).sum())
            regions.append({'id': region['id'], 'name': region['name'], 'faces': len(region['faces']),
                            'area_m2': area, 'energy_J': area * gamma})
        total = math.fsum(r['energy_J'] for r in regions)
        residual = abs(total - float(state['energy_J']))
        if not (math.isfinite(total) and math.isfinite(residual) and residual <= 3e-4):
            return {'available': False,
                    'reason': f'Per-film energy sum deviates from native energy_J by {residual:.3g} J; numbers refused'}
        return {'available': True, 'gamma_J_m2': gamma, 'regions': regions,
                'energy_sum_J': total, 'energy_residual_J': residual,
                'basis': 'decomposition of the declared law U = gamma*sum(face area) on accepted native '
                         'geometry; Blender-side arithmetic checked against native energy_J, not an '
                         'independent native measurement'}
    except (KeyError, IndexError, TypeError, ValueError) as error:
        return {'available': False, 'reason': 'Accepted membrane state not decomposable: ' + str(error)}


def _construction_snapshot(context):
    # Always read current Blender/native state. No cross-call cache: a person
    # can edit geometry, materials or connections between any two timer calls.
    source = _source(context)
    doc = workspace.document()
    native = None if doc is None else {'spec': digest(doc['spec']), 'state': digest(doc['state']),
            'accepted_state_id': doc['state'].get('accepted_state_id')}
    if doc and doc.get('runtime_variant') is not None:native['runtime_variant']=doc['runtime_variant']
    revision = {'scene': context.scene.name,
                'scene_id': context.scene.get('chimera_operation_scene_id'),
                'source_revision': digest(source), 'native_revision': digest(native)}
    return source, doc, native, revision


def construction_revision(context=None):
    """Fresh procedure guard with the same physical identities as full inspect.

    Procedures do not consume unrelated search-result hashes or UI diagnostics.
    Their child proposals still use full inspection and ordinary preflight.
    """
    main_thread()
    return _construction_snapshot(context or bpy.context)[3]


def inspect(context=None):
    main_thread()
    context = context or bpy.context
    source, doc, native, revision = _construction_snapshot(context)
    from . import native_warm_start,layer_checkpoint,port_response,layer_search
    from . import trial_compare,recipe_evidence,layer_trials,reusable_assembly,material_search,design_search,active_search,procedures
    matches, reason = _source_match(context, doc)
    active_job=trial_compare._future[3] if trial_compare._future else None
    port_job=(port_response._state.get('job') or {}).get('id')
    comparison_job=(trial_compare._pair.get('job') or {}).get('id')
    adaptive_job=(active_search._state.get('job') or {}).get('id')
    design_job=(design_search._state.get('job') or {}).get('id')
    search_job=(material_search._state.get('job') or {}).get('id')
    return {'schema': SCHEMA, **revision, 'mode': context.mode,
            'native': native, 'native_busy': workspace.busy(),
            'native_history': ({'count': len(workspace._session.history), 'cursor': workspace._session.cursor}
                               if workspace._session and not workspace.busy() else None),
            'pair_revision':trial_compare.revision(),'comparison_busy':trial_compare.busy(),
            'port_response_job':port_job if port_job==active_job else None,'port_response_revision':port_response.revision(),
            'comparison_job':comparison_job if comparison_job==active_job else None,
            'warm_start_revision':native_warm_start.revision(),
            'layer_settings_revision':layer_editing.revision(context.scene),
            'layer_cache_revision':layer_editing.cache_revision(context.scene),
            'layer_checkpoint_revision':layer_checkpoint.revision(context.scene),
            'layer_bake_job':(layer_editing.job_view() or {}).get('id'),
            'layer_search_revision':layer_search.revision(),'layer_search_job':layer_search._run['id'] if layer_search.live() else None,
            'procedure_revision':procedures.revision(),'procedure_history_revision':procedures.history_revision(),
            'procedure_job':procedures._run['id'] if procedures._run and procedures._run['status'] in ('queued','running') else None,
            'adaptive_job':adaptive_job if adaptive_job==active_job else None,'adaptive_revision':active_search.revision(),
            'design_job':design_job if design_job==active_job else None,'design_revision':design_search.revision(),
            'search_job':search_job if search_job==active_job else None,
            'search_revision':material_search.revision(),'assembly_revision':reusable_assembly.revision(), 'evidence_revision':recipe_evidence.revision(),'layer_trial_revision':layer_trials.revision(),
            'source_matches_native': matches, 'needs_rebuild': matches is False, 'source_note': reason,
            'parts': [{'id': p['id'], 'name': p['name'], 'vertices': len(p['vertices'])} for p in source['parts']],
            'connections': _connections_report(source, doc),
            'regions': _regions_report(doc),
            'native_hinges':source.get('native_hinges',[]),
            'native_warm_start':native_warm_start.report(),
            'actions': [a for a in ACTIONS if (a not in layer_editing.ACTIONS or hasattr(context.scene,'uipc_settings')) and (a not in ('create_mounted_panel','duplicate_layers','capture_layers','compare_layers','show_layer_trials','clear_layer_preview') or hasattr(context.scene,'uipc_settings'))],
            'limits': 'Existing pinned membrane law and optional libuipc authoring; water deferred'}


def _number(value, lo, hi, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not lo <= value <= hi:
        raise ValueError(f'{name} must be finite in [{lo}, {hi}]')
    return value


def preflight(context, action, targets, params):
    if action not in ACTIONS or not isinstance(params, dict):
        raise ValueError('Choose an advertised Studio action and parameter object')
    if not isinstance(targets, list) or any(not isinstance(t, str) for t in targets) or len(targets) != len(set(targets)):
        raise ValueError('Targets must be unique stable part identities')
    lo, hi = ACTIONS[action][1]
    if not lo <= len(targets) <= hi:
        raise ValueError(f'{action} needs {lo}-{hi} target parts')
    allowed=(context.mode in ('OBJECT','EDIT_MESH') or
             context.mode=='PAINT_WEIGHT' and action in PAINT_ACTIONS or
             context.mode in ('SCULPT','POSE') and action in AUTHOR_ACTIONS)
    if not allowed:
        raise ValueError('Use Object/Edit Mode; Sculpt/Pose support evaluated physical copies and ordinary layer material, seam, bake and comparison actions; Weight Paint supports layer controls')
    if context.mode=='SCULPT' and context.object and context.object.use_dynamic_topology_sculpting:
        raise ValueError('Finish dynamic-topology sculpting and disable Dyntopo before a physical operation; no automatic topology conversion is performed')
    if action=='duplicate_layers' and not hasattr(context.scene,'uipc_settings'):
        raise ValueError('Open the GPU Materials profile to enable libuipc construction tools')
    from . import trial_compare
    if action not in ('cancel_workflow_trial','cancel_port_response','cancel_procedure','cancel_adaptive_search','cancel_design_search','cancel_material_search','cancel_comparison') and (workspace.busy() or trial_compare.busy()):
        raise RuntimeError('Wait for the current native command or comparison to finish')
    if action in LAYER_SEARCH_ACTIONS:
        from . import layer_search
        objects=resolve(context,targets)
        return objects,layer_search.preflight(context,action,targets,params)
    if action in EXPLANATION_ACTIONS:
        from . import layer_explanations
        return [],layer_explanations.preflight(context,action,params)
    if action=='create_physical_copy':
        from . import evaluated_geometry
        return [],evaluated_geometry.preflight(context,params)
    if action in WORKFLOW_ACTIONS:
        from . import workflow_outcomes
        return [],workflow_outcomes.preflight(context,action,params)
    if action in RESPONSE_ASSET_ACTIONS:
        from . import response_assets
        return [],response_assets.preflight(context,action,params)
    if action in PORT_ACTIONS:
        from . import port_response
        return [],port_response.preflight(action,params,context)
    if action in layer_editing.ACTIONS:
        objects=resolve(context,targets)
        if any(not t.startswith('uipc:') for t in targets):raise ValueError('Choose libuipc physical parts')
        preview={'operator':ACTIONS[action][0],'targets':[o.name for o in objects]}
        preview.update(layer_editing.preflight(context,action,objects,params))
        return objects,preview
    if action in ('learn_native_warm_start','set_native_warm_start'):
        from . import native_warm_start
        return [],native_warm_start.preflight(action,params)
    keys = {'learn_procedure': {'candidate','name'}, 'run_procedure': {'procedure','bindings','values'}, 'forget_procedure': {'procedure'}, 'search_adaptive': {'gammas','load','target','tolerance','budget','schedule'}, 'select_adaptive_result': {'index'}, 'create_adaptive_result': {'index'}, 'search_designs': {'gammas','scales','load','band_width','bands','budget','seed'}, 'select_design': {'index'}, 'create_design': {'index'}, 'create_mounted_panel': {'origin'}, 'render_native': {'view'}, 'search_material': {'gammas','load','target','tolerance'}, 'select_material_result': {'index'}, 'learn_assembly': {'name'}, 'instantiate_assembly': {'gamma'}, 'assign_surface': {'gamma'}, 'mark_apex': {'vertex'}, 'apply_load': {'load'},
            'replay': {'checkpoint'}, 'duplicate_layers': {'offset'}, 'capture_layers': {'slot','label'}, 'compare_layers': {'seconds','focus'}, 'show_layer_trials': {'seconds','focus'}, 'capture_trial': {'slot','label'}, 'link_evidence': {'target','recipe'}}.get(action, set())
    if action=='run_procedure' and 'strategy' in params:keys=keys|{'strategy'}
    if set(params) != keys:
        raise ValueError('Expected parameters: ' + ', '.join(sorted(keys)))
    objects = resolve(context, targets)
    expected_prefix = 'uipc:' if action == 'duplicate_layers' else 'membrane:'
    if any(not t.startswith(expected_prefix) for t in targets):
        raise ValueError('Action does not match the selected native owner')
    preview = {'operator': ACTIONS[action][0], 'targets': [o.name for o in objects]}
    if action in ('learn_procedure','run_procedure','forget_procedure'):
        from . import procedures
        if action=='run_procedure':
            if procedures._run and procedures._run['status'] in ('queued','running'):raise ValueError('A procedure is already active')
            _,steps=procedures.prepare(params,context);preview['steps']=steps
        elif action=='learn_procedure':
            if not isinstance(params['name'],str) or not 1<=len(params['name'].strip())<=80:raise ValueError('Give the procedure a name')
            procedures.source_candidate(params['candidate'])
        elif params['procedure'] not in procedures.learned():raise ValueError('Unknown retained procedure')
    elif action in ('search_adaptive','select_adaptive_result','create_adaptive_result'):
        from . import active_search
        if action=='search_adaptive':active_search.request(params,'Validate adaptive search')
        else:active_search.chosen(params['index'])
    elif action in ('search_designs','select_design','create_design'):
        from . import design_search
        if action=='search_designs':design_search.request(params,'Validate design search')
        else:design_search.chosen(params['index'])
    elif action=='create_mounted_panel':
        from . import mounted_panel
        mounted_panel.preflight(context,params['origin'])
        preview.update(parts=3,stitches=16,requires_bake=True)
    elif action=='render_native':
        if params['view'] not in ('VIEWPORT','FIXED'):raise ValueError('Choose VIEWPORT or FIXED')
        preview['view_request']=blocks_ui.render_request(context,params['view'])
    elif action in ('search_material','select_material_result'):
        from . import material_search
        if action=='search_material':material_search.request(params,'Validate proposed material search')
        else:
            result=material_search.validate_result(material_search._state['result']);i=params['index']
            if type(i)!=int or not 0<=i<len(result['trials']) or result['trials'][i]['status']!='measured':raise ValueError('Choose a measured candidate')
    elif action in ('learn_assembly','instantiate_assembly'):
        from . import reusable_assembly
        if action=='learn_assembly': reusable_assembly.infer(params['name'], 'Validate proposed reusable construction')
        else:
            spec=reusable_assembly.prepare(params['gamma'])
            if abs(context.scene.unit_settings.scale_length-1)>1e-9:raise ValueError('Use meters and Unit Scale 1')
            preview.update(parts=len(spec['assembly']['parts']),connections=len(spec['assembly']['connections']),compiled_spec=digest(spec))
    elif action in ('capture_layers','compare_layers','show_layer_trials','clear_layer_preview'):
        from . import layer_trials
        layer_trials.backend(context.scene)
        if action=='capture_layers':
            if params['slot'] not in ('A','B') or not isinstance(params['label'],str) or not 1<=len(params['label'].strip())<=80:
                raise ValueError('Choose A/B and a trial label of 1-80 characters')
            layer_trials.current(context.scene)
        elif action!='clear_layer_preview' and (not isinstance(params['seconds'],(int,float)) or isinstance(params['seconds'],bool) or not math.isfinite(params['seconds']) or params['seconds']<0 or not isinstance(params['focus'],str)):
            raise ValueError('Choose a finite sample time and shared physical part ID')
    elif action == 'link_evidence':
        from . import recipe_evidence
        recipe_evidence.preflight(params['target'],params['recipe'])
    elif action == 'capture_trial':
        if params['slot'] not in ('A','B') or not isinstance(params['label'],str) or not 1<=len(params['label'].strip())<=80:
            raise ValueError('Choose A/B and a trial label of 1-80 characters')
        trial_compare.checkpoint(workspace.document())
    elif action == 'compare_trials':
        trial_compare.validate_pair(trial_compare._pair)
        if set(trial_compare._pair['slots'])!={'A','B'}:raise ValueError('Store both A and B before comparing')
    elif action == 'assign_surface':
        _number(params['gamma'], .000001, 1000, 'Surface tension J/m2')
    elif action == 'mark_apex':
        v = params['vertex']
        if type(v) != int or not 0 <= v < len(objects[0].data.vertices):
            raise ValueError('Apex vertex is outside the source mesh')
        if objects[0].data.users > 1:
            raise ValueError('Make the apex-selection mesh single-user first')
    elif action in ('build_films', 'connect_apices'):
        parts = [blocks_ui.part(o) for o in objects]
        ids = {p['id'] for p in parts}
        edges = [sorted(ids)] if action == 'connect_apices' else [e for e in json.loads(context.scene.chimera_blocks.connections) if all(i in ids for i in e)]
        spec = blocks.compile_parts(parts, edges)
        preview.update(vertices=len(spec['positions']), triangles=len(spec['triangles']), gamma=spec['gamma'], compiled_spec=digest(spec))
    elif action in ('resume', 'apply_load', 'replay'):
        doc = workspace.document()
        if not doc or doc['spec']['mode'] != 'membrane':
            raise ValueError('Use a confirmed membrane checkpoint; water remains deferred')
        if action == 'apply_load':
            workspace.current()
            _number(params['load'], 0, 10, 'Center load N')
        elif action == 'replay':
            current = workspace.current();index = params['checkpoint']
            if type(index) != int or not 0 <= index < len(current.history):
                raise ValueError('Checkpoint outside the confirmed history')
    elif action == 'duplicate_layers':
        if any(o.get('chimera_affine_component') for o in objects):raise ValueError('Restore detailed FEM before duplicating a reduced component')
        offset = params['offset']
        if not isinstance(offset, list) or len(offset) != 3:
            raise ValueError('Offset requires three coordinates')
        for value in offset:
            _number(value, -1000, 1000, 'Offset')
        # Native libuipc validates the closed selection again at execution.
        preview['requires_bake'] = True
    return objects, preview


def _payload(record):
    return {k: record[k] for k in ('action', 'targets', 'params', 'purpose', 'expected')}


def propose(action, targets=None, params=None, purpose='', context=None):
    main_thread();context = context or bpy.context
    targets = [] if targets is None else targets;params = {} if params is None else copy.deepcopy(params)
    if action in ('set_layer_attachment','rebind_layer_attachment') and isinstance(params,dict) and 'attachment' in params:
        params['attachment']=layer_editing.attachment_selector(layer_editing.entry(context.scene,params['attachment']))
    if not isinstance(purpose, str) or not purpose.strip() or len(purpose) > 500:
        raise ValueError('State why this operation helps the construction (1-500 characters)')
    _, preview = preflight(context, action, targets, params)
    if not context.scene.get('chimera_operation_scene_id'):
        context.scene['chimera_operation_scene_id'] = uuid.uuid4().hex
    current = inspect(context)
    if action=='run_procedure':from . import procedures
    from . import native_warm_start
    expected = {k: current[k] for k in ('scene', 'scene_id', 'source_revision', 'native_revision')}
    if action=='create_physical_copy':
        expected['evaluated_revision']=preview['evaluated_revision']
        expected['layer_settings_revision']=current['layer_settings_revision']
        expected['layer_cache_revision']=current['layer_cache_revision']
    if action in WORKFLOW_ACTIONS:
        expected['layer_settings_revision']=current['layer_settings_revision'];expected['layer_cache_revision']=current['layer_cache_revision']
    if action in PORT_ACTIONS:expected['port_response_revision']=current['port_response_revision']
    if action=='use_scaled_response_card':expected['scaled_card_revision']=preview['scaled_card_revision']
    if action=='export_response_asset':expected['response_asset_revision']=preview['response_asset_revision']
    if action in ('compose_port_responses','learn_condensed_response'):expected['composition_revision']=preview['composition_revision']
    if action=='set_layer_drive':expected['controller_signature']=preview['controller_signature']
    if action=='cancel_port_response':
        if current['port_response_job'] is None:raise ValueError('No active port response job')
        expected['port_response_job']=current['port_response_job']
    if action in ('learn_native_warm_start','set_native_warm_start','apply_load'):expected['warm_start_revision']=native_warm_start.revision()
    if action in ('run_procedure','forget_procedure') or action=='learn_procedure' and params['candidate'].startswith('saved:'):expected['procedure_revision']=current['procedure_revision']
    if action in layer_editing.ACTIONS or (action=='run_procedure' and procedures.definition(params['procedure'])['pattern'].get('owner')=='libuipc'):
        expected['layer_settings_revision']=current['layer_settings_revision']
        expected['layer_cache_revision']=current['layer_cache_revision']
        if action=='cancel_layer_bake':expected['layer_bake_job']=current['layer_bake_job']
        if action in ('continue_layers','refine_saved_component'):expected['layer_checkpoint_revision']=current['layer_checkpoint_revision']
    if action in LAYER_SEARCH_ACTIONS:
        expected['layer_settings_revision']=current['layer_settings_revision'];expected['layer_cache_revision']=current['layer_cache_revision']
        if action=='cancel_layer_search':expected['layer_search_job']=current['layer_search_job']
        if action=='use_layer_search_result':expected['layer_search_revision']=current['layer_search_revision'];expected['layer_trial_revision']=current['layer_trial_revision']
    if action=='cancel_procedure':
        if current['procedure_job'] is None:raise ValueError('No active procedure')
        expected['procedure_job']=current['procedure_job']
    if action=='render_native':expected['render_view_revision']=digest(preview['view_request'])
    if action in ('capture_trial','compare_trials','link_evidence','learn_assembly'):expected['pair_revision']=current['pair_revision']
    if action=='cancel_adaptive_search':
        if current['adaptive_job'] is None:raise ValueError('No active adaptive search')
        expected['adaptive_job']=current['adaptive_job']
    if action=='search_adaptive':expected['assembly_revision']=current['assembly_revision']
    if action in ('select_adaptive_result','create_adaptive_result'):expected['adaptive_revision']=current['adaptive_revision']
    if action=='cancel_design_search':
        if current['design_job'] is None:raise ValueError('No active design search')
        expected['design_job']=current['design_job']
    if action in ('select_design','create_design'):expected['design_revision']=current['design_revision']
    if action=='search_designs':expected['assembly_revision']=current['assembly_revision']
    if action in ('cancel_comparison','cancel_material_search'):
        field='comparison_job' if action=='cancel_comparison' else 'search_job'
        if current[field] is None:raise ValueError('No active job for '+action)
        expected[field]=current[field]
    if action=='select_material_result':expected['search_revision']=current['search_revision']
    if action in ('learn_assembly','instantiate_assembly','search_material'):expected['assembly_revision']=current['assembly_revision']
    if action=='link_evidence':expected['evidence_revision']=current['evidence_revision']
    if action in EXPLANATION_ACTIONS:expected['layer_trial_revision']=current['layer_trial_revision']
    if action in ('capture_layers','compare_layers','show_layer_trials','clear_layer_preview','remember_layer_cache','relocate_layer_cache','compare_component_trials','review_component_choice','apply_component_choice'):expected['layer_trial_revision']=current['layer_trial_revision']
    record = {'id': uuid.uuid4().hex, 'action': action, 'targets': copy.deepcopy(targets),
              'params': copy.deepcopy(params), 'purpose': purpose.strip(), 'expected': expected,
              'preview': preview, 'status': 'proposed', 'created': time.time(), 'error': None}
    record['payload_hash'] = digest(_payload(record))
    protected=set()
    from . import workflow_outcomes
    active=workflow_outcomes._active
    if active:
        protected={k for k in _records if k not in active['before_ids']}|{active['begin_operation']}
        if action not in ('finish_workflow_trial','cancel_workflow_trial') and len(protected)>=MAX_RECORDS-2:
            raise ValueError('Finish or stop the measured trial before its complete command history fills')
    if action=='compare_workflow_trials':protected.update(params['trials'])
    if action=='learn_procedure':
        from . import procedures
        candidate=procedures.source_candidate(params['candidate'])
        protected.update(r['id'] for episode in candidate['examples'] for r in episode)
    if len(_records) >= MAX_RECORDS:
        # Completed child details are already retained by their search parent.
        for key, old in sorted(_records.items(),key=lambda item:not bool(item[1].get('layer_search_parent'))):
            if key not in protected and old['status'] not in ('queued', 'running', 'proposed') and not (old.get('learned_procedure') and not old.get('procedure_forgotten')):
                del _records[key];break
        else:
            raise ValueError('Finish or discard pending proposals before creating more')
    _records[record['id']] = record
    if hasattr(context.scene,'chimera_operations'):
        settings=context.scene.chimera_operations
        settings.action=action;settings.parameters=canonical(params);settings.purpose=purpose.strip()
        settings.latest=record['id'];settings.message='Proposal ready: '+action
    return copy.deepcopy(record)


def _bm_flags(bm):
    return ([v.select for v in bm.verts], [e.select for e in bm.edges], [f.select for f in bm.faces])


def _set_bm_flags(bm, flags):
    for elements, values in zip((bm.verts, bm.edges, bm.faces), flags):
        if len(elements) != len(values):raise ValueError('Selection topology changed during command')
    for elements in (bm.faces,bm.edges,bm.verts):
        for element in elements:element.select_set(False)
    for elements, values in zip((bm.verts,bm.edges,bm.faces),flags):
        for element, value in zip(elements,values):
            if value:element.select_set(True)
    bm.select_flush_mode()


@contextlib.contextmanager
def selected_targets(context, objects, apex=None):
    old_active = context.view_layer.objects.active
    selected = list(context.selected_objects)
    old_mode = context.mode
    # Edit selection belongs to BMesh; an Object-mode mesh is not its authority.
    edit_flags = {}
    paint_group=old_active.vertex_groups.active_index if old_mode=='PAINT_WEIGHT' and old_active else None
    mode_names={'PAINT_WEIGHT':'WEIGHT_PAINT','SCULPT':'SCULPT','POSE':'POSE'}
    if old_mode=='SCULPT' and old_active and old_active.use_dynamic_topology_sculpting:
        raise ValueError('Finish dynamic-topology sculpting and disable Dyntopo before a physical operation')
    pose_selection=[]
    if old_mode=='POSE':
        for rig in context.objects_in_mode:
            if rig.type=='ARMATURE':
                pose_selection.append((rig,rig.data.bones.active.name if rig.data.bones.active else None,
                                       {b.name:b.select for b in rig.pose.bones}))
    if old_mode in mode_names:bpy.ops.object.mode_set(mode='OBJECT')
    if old_mode == 'EDIT_MESH':
        edit_flags = {o.data: _bm_flags(bmesh.from_edit_mesh(o.data))
                      for o in context.objects_in_mode_unique_data if o.type == 'MESH'}
        bpy.ops.object.mode_set(mode='OBJECT')
    apex_mesh = objects[0].data if apex is not None else None
    apex_flags = None
    if apex_mesh is not None and apex_mesh not in edit_flags:
        bm=bmesh.new()
        try:bm.from_mesh(apex_mesh);apex_flags=_bm_flags(bm)
        finally:bm.free()
    try:
        if objects:
            for o in context.selected_objects:o.select_set(False)
            for o in objects:o.select_set(True)
            context.view_layer.objects.active = objects[0]
        if apex is not None:
            for v in objects[0].data.vertices:v.select = v.index == apex
        yield
    finally:
        if context.mode in ('EDIT_MESH',*mode_names):bpy.ops.object.mode_set(mode='OBJECT')
        if apex_flags is not None:
            bm=bmesh.new()
            try:bm.from_mesh(apex_mesh);_set_bm_flags(bm,apex_flags);bm.to_mesh(apex_mesh)
            finally:bm.free()
        for o in context.selected_objects:o.select_set(False)
        def still_live(obj):
            try:return obj is not None and context.view_layer.objects.get(obj.name)==obj
            except ReferenceError:return False
        for o in selected:
            if still_live(o):o.select_set(True)
        if still_live(old_active):
            context.view_layer.objects.active = old_active
        if old_mode == 'EDIT_MESH' and still_live(old_active):
            bpy.ops.object.mode_set(mode='EDIT')
            for mesh, flags in edit_flags.items():
                bm=bmesh.from_edit_mesh(mesh);_set_bm_flags(bm,flags)
                bmesh.update_edit_mesh(mesh,loop_triangles=False,destructive=False)
        elif old_mode in mode_names and still_live(old_active):
            if paint_group is not None and 0<=paint_group<len(old_active.vertex_groups):old_active.vertex_groups.active_index=paint_group
            for rig,active,flags in pose_selection:
                if not still_live(rig):continue
                for name,values in flags.items():
                    bone=rig.pose.bones.get(name)
                    if bone:bone.select=values
                rig.data.bones.active=rig.data.bones.get(active) if active else None
            bpy.ops.object.mode_set(mode=mode_names[old_mode])


def apply(operation_id, context=None):
    main_thread();context = context or bpy.context
    record = _records[operation_id]
    if record['status'] != 'proposed':
        return status(operation_id)  # Retrying a delivered command never repeats it.
    try:
        if digest(_payload(record)) != record['payload_hash']:
            raise ValueError('Proposal payload changed; create a fresh proposal')
        current = inspect(context)
        if record['action']=='create_physical_copy':
            from . import evaluated_geometry
            current['evaluated_revision']=evaluated_geometry.preflight(context,record['params'])['evaluated_revision']
        if record['action']=='set_layer_drive':
            from . import controller_motion
            current['controller_signature']=controller_motion.checked(context,resolve(context,record['targets'])[0],record['params'])[2]['controller_signature']
        if record['action']=='use_scaled_response_card':
            from . import scale_response
            current['scaled_card_revision']=scale_response.preflight(record['action'],record['params'],context)['scaled_card_revision']
        if record['action']=='export_response_asset':
            from . import response_assets
            current['response_asset_revision']=response_assets.preflight(context,record['action'],record['params'])['response_asset_revision']
        if record['action']=='learn_condensed_response':
            from . import port_condensation
            current['composition_revision']=digest(port_condensation.inputs(context,record['params']))
        if record['action']=='compose_port_responses':
            from . import port_assembly
            current['composition_revision']=port_assembly.revision(context,record['params'])
        if record['action']=='render_native':current['render_view_revision']=digest(blocks_ui.render_request(context,record['params']['view']))
        if any(current[k] != v for k, v in record['expected'].items()):
            raise ValueError('Proposal is stale: source, scene or native state changed; inspect and propose again')
        objects, _ = preflight(context, record['action'], record['targets'], record['params'])
        action, params = record['action'], record['params']
        operator_name, _, native_async = ACTIONS[action]
        module, name = operator_name.split('.')
        operator = getattr(getattr(bpy.ops, module), name)
        # Reuse the existing UI implementation, with its physical admission checks.
        with selected_targets(context, objects, params.get('vertex')):
            if action == 'assign_surface':context.scene.chimera_blocks.gamma = params['gamma']
            elif action == 'apply_load':context.scene.chimera_gpu.load = params['load']
            elif action == 'replay':context.scene.chimera_gpu.replay = params['checkpoint']
            kwargs = {'offset': params['offset']} if action == 'duplicate_layers' else {}
            if action in LAYER_SEARCH_ACTIONS:kwargs={'action':action,'payload':canonical({'targets':record['targets'],'params':params}),'purpose':record['purpose']}
            if action in EXPLANATION_ACTIONS:kwargs={'action':action,'parameters':canonical(params),'purpose':record['purpose']}
            if action=='create_physical_copy':kwargs={'parameters':canonical(params),'purpose':record['purpose']}
            if action in WORKFLOW_ACTIONS:kwargs={'action':action,'parameters':canonical(params),'purpose':record['purpose']}
            if action in RESPONSE_ASSET_ACTIONS:kwargs={'action':action,'parameters':canonical(params),'purpose':record['purpose']}
            if action in PORT_ACTIONS:kwargs={'action':action,'parameters':canonical(params),'purpose':record['purpose']}
            if action=='learn_native_warm_start':kwargs={'purpose':record['purpose']}
            if action=='set_native_warm_start':kwargs={'enabled':params['enabled']}
            if action in layer_editing.ACTIONS:kwargs={'action':action,'payload':canonical({'targets':record['targets'],'params':params}),'purpose':record['purpose']}
            if action=='learn_procedure':kwargs={**params,'purpose':record['purpose']}
            if action=='run_procedure':kwargs={'values_json':canonical(params),'purpose':record['purpose']}
            if action=='forget_procedure':kwargs=params
            if action in ('apply_load','assign_surface'):kwargs={'value_json':canonical(params['load'] if action=='apply_load' else params['gamma'])}
            if action=='search_adaptive':kwargs={'settings':canonical(params),'purpose':record['purpose']}
            if action=='select_adaptive_result':kwargs=params
            if action=='create_adaptive_result':kwargs={**params,'purpose':record['purpose']}
            if action=='search_designs':kwargs={'settings':canonical(params),'purpose':record['purpose']}
            if action=='select_design':kwargs=params
            if action=='create_design':kwargs={**params,'purpose':record['purpose']}
            if action=='create_mounted_panel':kwargs=params
            if action=='render_native':kwargs={'view_mode':params['view']}
            if action=='search_material':kwargs={'values':canonical(params),'purpose':record['purpose']}
            if action=='select_material_result':kwargs=params
            if action=='learn_assembly':kwargs={**params,'purpose':record['purpose']}
            if action=='instantiate_assembly':kwargs={'gamma_json':canonical(params['gamma']),'purpose':record['purpose']}
            if action in ('capture_trial','link_evidence','capture_layers'):kwargs={**params,'purpose':record['purpose']}
            if action in ('compare_layers','show_layer_trials'):kwargs={**params,'preview':action=='show_layer_trials'}
            if not operator.poll():raise ValueError('Blender operator is unavailable in this context')
            result = operator('EXEC_DEFAULT', **kwargs)
            if result != {'FINISHED'}:raise RuntimeError('Blender command refused: ' + str(result))
            if action=='prepare_layer_alternative':
                from . import layer_explanations
                record['prepared_operation']=copy.deepcopy(layer_explanations._last_prepared)
            if action in WORKFLOW_ACTIONS:
                from . import workflow_outcomes as outcomes
                if action=='begin_workflow_trial':
                    outcomes._active['begin_operation']=record['id'];record['workflow_trial_start']=copy.deepcopy(outcomes._last_begin)
                elif action=='finish_workflow_trial':record['workflow_trial']=copy.deepcopy(outcomes._last_trial)
                elif action=='compare_workflow_trials':record['workflow_comparison']=copy.deepcopy(outcomes._last_comparison)
                else:record['workflow_trial_cancelled']=copy.deepcopy(outcomes._last_begin)
            if action in RESPONSE_ASSET_ACTIONS:
                from . import response_assets
                record['response_asset']=copy.deepcopy(response_assets._last_result)
            if action in ('export_layer_asset','import_layer_asset'):
                from . import layer_assets
                record['construction_asset']=copy.deepcopy(layer_assets._last_result)
            if action=='place_layer_construction':
                from . import layer_assets
                record['construction_placement']=copy.deepcopy(layer_assets._last_result)
            if action=='create_hinge_torque_controller':
                from . import hinge_torque_curve
                record['torque_controller']=copy.deepcopy(hinge_torque_curve._last_result)
            if action=='learn_procedure':
                from . import procedures
                record['learned_procedure']=copy.deepcopy(procedures._last_learned)
            record['operator_finished'] = True
            if native_async:
                job = _job(record)
                record.update(status=job['status'], native_job=job['id'])
        record['applied'] = time.time()
        if native_async:
            job = _job(record)
            _accept_job(record, job, context)
        else:
            record.update(status='succeeded', finished=time.time(), result=inspect(context))
    except Exception as error:
        if record.get('native_job'):
            record['context_error'] = str(error)
        else:
            record.update(status='failed', error=str(error), finished=time.time())
    return copy.deepcopy(record)


def _job(record):
    if record['action'] in ('search_layer_material','use_layer_search_result'):
        from . import layer_search
        return layer_search.status(record.get('native_job'))
    if record['action'] in ('learn_port_response','measure_port_response','compose_port_responses','learn_condensed_response','measure_condensed_response','qualify_scaled_response','measure_scaled_response'):
        from . import port_response
        return port_response.status(record.get('native_job'))
    if record['action'] in layer_editing.ASYNC_ACTIONS:return layer_editing.job_status(record.get('native_job'))
    if record['action']=='run_procedure':
        from . import procedures
        return procedures.status(record.get('native_job'))
    if record['action']=='search_adaptive':
        from . import active_search
        return active_search.status(record.get('native_job'))
    if record['action']=='search_designs':
        from . import design_search
        return design_search.status(record.get('native_job'))
    if record['action']=='search_material':
        from . import material_search
        return material_search.status(record.get('native_job'))
    if record['action']=='compare_trials':
        from . import trial_compare
        return trial_compare.status(record.get('native_job'))
    return workspace.job_status(record.get('native_job'))


def _accept_job(record, job, context=None):
    # A fast worker can terminate before apply returns. Use the same terminal
    # bookkeeping here and during later polling so failure text is never lost.
    record.update(status=job['status'], native_job=job['id'], native_result=job, error=job.get('error'))
    if job['status'] == 'succeeded':
        try:
            now = inspect(context)
            record['result'] = now
            # libuipc validates physical inputs before attaching its cache;
            # newly attached playback modifiers are a presentation change.
            record['source_changed_while_running'] = (False if record['action'] in layer_editing.ASYNC_ACTIONS else now['source_revision'] != record['expected']['source_revision'])
        except Exception as error:
            record.update(status='failed',error='Native job completed but result inspection failed: '+str(error)+'; inspect the retained checkpoint before retry')
    if record['status'] in ('succeeded', 'failed', 'interrupted'):
        record['finished'] = time.time()
        if record.get('context_error'):
            record.update(status='failed',error='Native job ended; Blender context recovery failed: '+record['context_error'])


def status(operation_id):
    main_thread();record = _records[operation_id]
    if record['status'] in ('queued', 'running'):
        workspace.poll()
        try:job = _job(record)
        except ValueError:
            record.update(status='interrupted', error='Native job handle is absent; saved checkpoint retained; inspect before retry')
        else:_accept_job(record, job)
    return copy.deepcopy(record)


def peek(operation_id):
    """Read cached status in a Panel.draw context; never accept native results."""
    main_thread()
    return copy.deepcopy(_records[operation_id])


def poll():
    # Timer callbacks may update Blender IDs; panel drawing cannot. Keep status
    # fresh independently of whether a human or AI asks for it this frame.
    for key in list(_records):
        if _records.get(key,{}).get('status') in ('queued','running'):status(key)
    return .1


def discard(operation_id):
    main_thread()
    if _records[operation_id]['status'] != 'proposed':
        raise ValueError('Only an unapplied proposal can be discarded')
    _records[operation_id].update(status='discarded', finished=time.time())


def saved_history():
    # Completed procedures/searches retain their program, outcome and native evidence.
    # Their duplicate child receipts can leave the bounded save without losing a
    # learned definition, active job, measured trial or the main construction state.
    from . import workflow_outcomes
    active=workflow_outcomes._active
    protected=({k for k in _records if k not in active['before_ids']}|{active['begin_operation']}) if active else set()
    terminal={'succeeded','failed','interrupted','discarded'}
    parents={r['native_result']['id'] for r in _records.values()
             if r.get('action')=='run_procedure' and r.get('status') in terminal
             and isinstance(r.get('native_result'),dict) and r['native_result'].get('id')}
    searches={r['native_result']['id']:set(r['native_result'].get('completed',[]))
              for r in _records.values() if r.get('action') in LAYER_SEARCH_ACTIONS
              and r.get('status')=='succeeded' and isinstance(r.get('native_result'),dict)
              and r['native_result'].get('id')}
    records=list(_records.values());omitted=[]
    def encoded():return canonical({'schema':SCHEMA,'records':records,'compacted_completed_children':omitted})
    payload=encoded()
    for record in list(records):
        if len(payload.encode('utf-8'))<=MAX_BYTES:break
        # Successful search rows retain complete measured inputs/cache references.
        # Only successful, explicitly completed generated child receipts are
        # redundant; preserve failed children, unfinished parents and live trials.
        search_child=(record.get('status')=='succeeded' and record['id'] in searches.get(record.get('layer_search_parent'),set()))
        if record['id'] not in protected and record.get('status') in terminal and (record.get('procedure_parent') in parents or search_child) and not record.get('learned_procedure') and not record.get('workflow_trial'):
            records.remove(record);omitted.append(record['id']);payload=encoded()
    if len(payload.encode('utf-8'))>MAX_BYTES:raise ValueError('Operation history exceeds its save budget; retained procedures and measured trials were preserved')
    return payload


@persistent
def save_pre(_):
    for key in list(_records):status(key)
    payload = saved_history()
    text = bpy.data.texts.get(TEXT) or bpy.data.texts.new(TEXT)
    text.clear();text.write(payload)


@persistent
def load_pre(_):
    _records.clear()


@persistent
def load_post(_):
    text = bpy.data.texts.get(TEXT)
    if not text:return
    try:
        raw = text.as_string()
        if len(raw.encode('utf-8')) > MAX_BYTES:raise ValueError('Oversized saved operation history')
        value = json.loads(raw)
        if value.get('schema') != SCHEMA or not isinstance(value.get('records'), list) or len(value['records']) > MAX_RECORDS:
            raise ValueError('Unsupported saved operation history')
        newly_interrupted=[]
        for record in value['records']:
            if not isinstance(record, dict) or not isinstance(record.get('id'), str) or record.get('action') not in ACTIONS:
                raise ValueError('Malformed saved operation')
            if record.get('status') not in ('proposed','queued','running','succeeded','failed','interrupted','discarded') or record['id'] in _records:
                raise ValueError('Invalid saved operation status or duplicate ID')
            if digest(_payload(record)) != record.get('payload_hash'):
                raise ValueError('Saved operation payload checksum mismatch')
            if record.get('status') in ('queued', 'running'):
                record.update(status='interrupted', error='File reopened without a live job; inspect the saved checkpoint before retry')
                newly_interrupted.append(record)
                if record.get('action') in ({'run_procedure','search_layer_material','use_layer_search_result'}|layer_editing.ASYNC_ACTIONS) and isinstance(record.get('native_result'),dict):
                    record['native_result'].update(status='interrupted',error=record['error'])
            _records[record['id']] = record
        from . import layer_checkpoint
        for record in newly_interrupted:layer_checkpoint.recover_interrupted(record)
    except (ValueError, KeyError, TypeError) as error:
        _records.clear();workspace.message('Operation history refused: ' + str(error))


def register():
    if not bpy.app.background:bpy.app.timers.register(poll,first_interval=.1,persistent=True)
    for handlers, fn in ((bpy.app.handlers.save_pre, save_pre), (bpy.app.handlers.load_pre, load_pre), (bpy.app.handlers.load_post, load_post)):
        if fn not in handlers:
            if fn is save_pre:handlers.insert(0, fn)  # Accept completed jobs before native checkpoint serialization.
            else:handlers.append(fn)


def unregister():
    if bpy.app.timers.is_registered(poll):bpy.app.timers.unregister(poll)
    for handlers, fn in ((bpy.app.handlers.save_pre, save_pre), (bpy.app.handlers.load_pre, load_pre), (bpy.app.handlers.load_post, load_post)):
        if fn in handlers:handlers.remove(fn)
    _records.clear()
