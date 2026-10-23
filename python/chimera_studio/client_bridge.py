# SPDX-License-Identifier: AGPL-3.0-or-later
"""Opt-in local filesystem transport into the existing main-thread operations.
The session capability is access to its directory under the current OS account;
this is not a boundary against hostile processes running as that account.
"""
import contextlib
import os
import time
import uuid
import bpy
from bpy.app.handlers import persistent
from . import operations as commands, client_protocol as wire

_state = None
_last_message = 'Local client is disabled'


def manifest():
    s = _state
    return {'schema': wire.SCHEMA, 'session': s['id'], 'pid': os.getpid(),
            'file': bpy.data.filepath, 'scene': s['scene'].name,
            'active': True, 'updated': time.time(), 'created': s['created'],
            'transport': 'local JSON files; typed Studio operations only'}


def start(context=None):
    global _state, _last_message
    commands.main_thread()
    if _state: return _state['id']
    context = context or bpy.context
    if not context.window: raise ValueError('Enable the client from the intended Blender window')
    session = uuid.uuid4().hex
    path = wire.SESSIONS / session
    (path / 'requests').mkdir(parents=True)
    (path / 'responses').mkdir()
    _state = {'id': session, 'path': path, 'scene': context.scene,
              'window': context.window, 'created': time.time(), 'published': 0, 'cleaned': 0}
    try:
        wire.atomic(path / 'session.json', manifest())
        bpy.app.timers.register(poll, first_interval=.1)
    except Exception:
        stop('Client could not start')
        raise
    _last_message = 'Enabled for this window and scene'
    return session


def stop(reason='Disabled by operator'):
    global _state, _last_message
    commands.main_thread()
    s = _state
    if s:
        # Native jobs belong to the existing workspace, not this connection.
        try:
            value = wire.read(s['path'] / 'session.json')
            value.update(active=False, updated=time.time(), reason=reason)
            wire.atomic(s['path'] / 'session.json', value)
        finally:
            _state = None
            if bpy.app.timers.is_registered(poll): bpy.app.timers.unregister(poll)
    _last_message = reason


@contextlib.contextmanager
def context():
    s = _state
    window = s['window']
    if window not in list(bpy.context.window_manager.windows) or window.scene != s['scene']:
        raise ValueError('Client window or scene changed; enable a new session')
    areas = [a for a in window.screen.areas if a.type == 'VIEW_3D']
    # Do not guess a camera when several editors are present. Choose explicitly
    # by arranging one 3D View before requesting VIEWPORT rendering.
    if len(areas) == 1:
        area = areas[0]
        region = next(r for r in area.regions if r.type == 'WINDOW')
        with bpy.context.temp_override(window=window, area=area, region=region): yield
    else:
        with bpy.context.temp_override(window=window): yield


def dispatch(method, args):
    if method == 'inspect' and not args: return commands.inspect()
    if method == 'propose' and set(args) == {'action', 'targets', 'params', 'purpose'}:
        if args['action'] == 'render_native' and args['params'].get('view') == 'VIEWPORT':
            if len([a for a in _state['window'].screen.areas if a.type == 'VIEW_3D']) != 1:
                raise ValueError('VIEWPORT rendering needs exactly one 3D View in the connected window')
        return commands.propose(**args)
    if method in ('apply', 'status', 'discard') and set(args) == {'operation'}:
        key = wire.identity(args['operation'])
        if method == 'apply': return commands.apply(key)
        if method == 'status': return commands.status(key)
        commands.discard(key)
        return commands.peek(key)
    if method in ('scan_layer_assets','scan_response_assets') and set(args) == {'path'}:
        from . import layer_assets
        return layer_assets.scan(args['path'])
    if method == 'check_cloth_stitch' and set(args)=={'scale','stiffness_N_m','gap_m','displacement_m','purpose'}:
        from . import cloth_stitch
        return cloth_stitch.start(bpy.context.scene,**args)
    if method == 'show_cloth_stitch' and not args:
        from . import cloth_stitch
        return cloth_stitch.show(bpy.context.scene)
    if method == 'cancel_cloth_stitch' and not args:
        from . import cloth_stitch
        cloth_stitch.cancel();return cloth_stitch.report()
    if method == 'check_cloth_assembly' and set(args)=={'names','load_N','purpose'}:
        from . import cloth_assembly
        return cloth_assembly.start(bpy.context.scene,**args)
    if method == 'show_cloth_assembly' and not args:
        from . import cloth_assembly
        return cloth_assembly.show(bpy.context.scene)
    if method == 'cancel_cloth_assembly' and not args:
        from . import cloth_assembly
        cloth_assembly.cancel();return cloth_assembly.report()
    if method == 'check_cloth_load' and set(args)=={'scale','load_N','purpose'}:
        from . import cloth_load
        return cloth_load.start(bpy.context.scene,**args)
    if method == 'show_cloth_load' and not args:
        from . import cloth_load
        return cloth_load.show(bpy.context.scene)
    if method == 'cancel_cloth_load' and not args:
        from . import cloth_load
        cloth_load.cancel();return cloth_load.report()
    if method == 'learn_cloth_rail' and set(args)=={'port','purpose'}:
        from . import cloth_port
        return cloth_port.start(bpy.context.scene,**args)
    if method == 'query_cloth_rail' and set(args)=={'scale','height'}:
        from . import cloth_port
        value=cloth_port.query(**args)
        return {k:v for k,v in value.items() if k!='positions_m'}
    if method == 'preview_cloth_rail' and set(args)=={'scale','height'}:
        from . import cloth_port
        return cloth_port.preview(bpy.context.scene,**args)
    if method == 'cancel_cloth_rail' and not args:
        from . import cloth_port
        cloth_port.cancel();return cloth_port.report()
    if method == 'learn_cloth_vector' and set(args)=={'port','purpose'}:
        from . import cloth_vector
        return cloth_vector.start(bpy.context.scene,**args)
    if method == 'query_cloth_vector' and set(args)=={'scale','tangent_m','bitangent_m','normal_m'}:
        from . import cloth_vector
        return cloth_vector.query(**args)
    if method == 'preview_cloth_vector' and set(args)=={'scale','tangent_m','bitangent_m','normal_m'}:
        from . import cloth_vector
        return cloth_vector.preview(bpy.context.scene,**args)
    if method == 'predict_cloth_stitch' and set(args)=={'scale','stiffness_N_m','rest_length_m','carrier_displacement_m','anchor_rest_m','port_rest_m'}:
        from . import cloth_vector
        return cloth_vector.predict(**args)
    if method == 'cancel_cloth_vector' and not args:
        from . import cloth_vector
        cloth_vector.cancel();return cloth_vector.report()
    if method == 'build_cloth_training_labels' and set(args)=={'focus','seconds','samples','scale_thickness','purpose'}:
        from . import cloth_labels
        return cloth_labels.start(bpy.context.scene,**args)
    if method == 'cancel_cloth_training_labels' and not args:
        from . import cloth_labels
        cloth_labels.cancel();return cloth_labels.report()
    if method == 'inspect_cloth_triangles' and set(args) == {'focus','seconds','limit'}:
        from . import triangle_inspection
        return triangle_inspection.inspect(bpy.context.scene, **args)
    if method == 'show_cloth_triangle' and set(args) == {'params','report_id','triangle'}:
        from . import triangle_inspection_ui
        return triangle_inspection_ui.show(bpy.context.scene, **args)
    if method == 'inspect_attachment_loads' and set(args) == {'seconds', 'review_N'}:
        from . import attachment_loads
        return attachment_loads.inspect(bpy.context.scene, **args)
    if method == 'find_layer_designs' and set(args) == {'query', 'limit'}:
        from . import construction_queries
        return construction_queries.find(**args)
    if method == 'inspect_layer_design' and set(args) == {'query', 'operation', 'index', 'revision_id', 'scope_id'}:
        from . import construction_queries
        return construction_queries.inspect(**args)
    if method == 'search_memory' and set(args) == {'query', 'limit'}:
        from . import construction_memory
        return construction_memory.search(**args)
    if method == 'inspect_memory' and set(args) == {'ref', 'revision'}:
        from . import construction_memory
        return construction_memory.inspect(**args)
    if method == 'report' and set(args) == {'kind'}:
        if args['kind']=='cloth_stitch':
            from . import cloth_stitch
            return cloth_stitch.report()
        if args['kind']=='cloth_assembly':
            from . import cloth_assembly
            return cloth_assembly.report()
        if args['kind']=='cloth_load':
            from . import cloth_load
            return cloth_load.report()
        if args['kind']=='cloth_port':
            from . import cloth_port
            return cloth_port.report()
        if args['kind']=='cloth_vector':
            from . import cloth_vector
            return cloth_vector.report()
        if args['kind']=='cloth_labels':
            from . import cloth_labels
            return cloth_labels.report()
        if args['kind']=='triangle_inspection':
            saved=bpy.context.scene.chimera_triangle_inspection
            result={'purpose':saved.purpose,'scope':'Saved inspection intent; inspect again to verify native evidence.'}
            try:result['params']=saved.params()
            except ValueError as error:result.update(params=None,error=str(error))
            return result
        if args['kind']=='construction_requirements':
            saved=bpy.context.scene.chimera_memory
            result={'purpose':saved.query,'mode':saved.mode,'scope':'Saved authoring intent only. Find measured alternatives again to check current evidence and compatibility.'}
            try:result['query']=saved.requirement()
            except (ValueError,AttributeError) as error:result.update(query=None,error=str(error))
            return result
        if args['kind']=='hinge_torque_curves':
            from . import hinge_torque_curve
            return hinge_torque_curve.report()
        if args['kind']=='workflow_outcomes':
            from . import workflow_outcomes
            return workflow_outcomes.report()
        if args['kind']=='component_choice':
            from . import component_choice
            return component_choice.report()
        if args['kind']=='published_materials':
            from . import published_materials
            return published_materials.report()
        if args['kind']=='layer_search':
            from . import layer_search
            return layer_search.report()
        if args['kind']=='explanation':
            from . import layer_explanations
            return layer_explanations.report()
        if args['kind']=='geometry':
            from . import evaluated_geometry
            return evaluated_geometry.report()
        if args['kind']=='regions':
            from . import painted_regions
            return painted_regions.report()
        if args['kind']=='ports':
            from . import port_response
            return port_response.report()
        if args['kind']=='layers':
            from . import layer_editing
            return layer_editing.report()
        if args['kind'] in ('procedures','procedure_candidates'):
            from . import procedures
            return procedures.report() if args['kind']=='procedures' else procedures.candidate_report()
        if args['kind'] == 'adaptive':
            from . import active_search
            return active_search.report()
        if args['kind'] == 'designs':
            from . import design_search
            return design_search.report()
        if args['kind'] == 'materials':
            from . import material_search
            return material_search.report()
        if args['kind'] == 'history':
            return [{'id': r['id'], 'action': r['action'], 'purpose': r['purpose'],
                     'status': r['status'], 'error': r.get('error')}
                    for r in commands._records.values()]
    raise ValueError('Unsupported method or argument keys; use inspect/propose/apply/status/discard/report')


def _one(path):
    s = _state
    try: key = wire.identity(path.stem)
    except ValueError:
        # Do not delete arbitrary files supplied in the folder.
        return
    destination = s['path'] / 'responses' / (key + '.json')
    # Check before parsing: even malformed re-delivery must not overwrite the
    # first reply. Clients compare fingerprints when they submit a request.
    if destination.exists():
        path.unlink(missing_ok=True)
        return
    fingerprint = None
    try:
        value = wire.read(path, wire.MAX_REQUEST)
        fingerprint = wire.digest(value)
        wire.request(value, s['id'], key)
        with context(): result = dispatch(value['method'], value['args'])
        reply = {'ok': True, 'result': result}
    except Exception as error:
        reply = {'ok': False, 'error': type(error).__name__ + ': ' + str(error)}
    finally:
        path.unlink(missing_ok=True)
    reply.update(schema=wire.SCHEMA, session=s['id'], id=key,
                 request_sha256=fingerprint, completed=time.time())
    try:
        wire.atomic(destination, reply)
    except ValueError as error:
        # An oversize reply must never stop the session (poll() would stop on an
        # escaping exception) nor hide that the operation may have executed.
        wire.atomic(destination, wire.oversize_reply(str(error), s['id'], key, fingerprint))


def poll():
    global _last_message
    if not _state: return None
    try:
        s = _state
        # Close rather than redirect commands into a different human scene.
        if s['window'] not in list(bpy.context.window_manager.windows) or s['window'].scene != s['scene']:
            stop('Window or scene changed; enable a new client session')
            return None
        processed = 0
        for path in sorted((s['path'] / 'requests').glob('*.json'), key=lambda p:p.name):
            try: wire.identity(path.stem)
            except ValueError: continue  # Unrelated filenames cannot starve valid requests.
            _one(path);processed += 1
            if processed == 2: break
        now = time.time()
        if now - s['published'] >= 1:
            wire.atomic(s['path'] / 'session.json', manifest());s['published'] = now
        if now - s['cleaned'] >= 10:
            # Requests expire after 30 s; retain replies longer than that so a
            # duplicate cannot re-execute after its cached reply is removed.
            for path in (s['path'] / 'responses').glob('*.json'):
                if now - path.stat().st_mtime > wire.RETENTION_SECONDS:
                    path.unlink()
            s['cleaned'] = now
    except Exception as error:
        _last_message = 'Client transport failed: ' + str(error)
        stop(_last_message)
        return None
    return .1


@persistent
def load_pre(_):
    stop('File replaced; inspect and enable a new client session')


class Enable(bpy.types.Operator):
    bl_idname = 'chimera.enable_client';bl_label = 'Enable Local Z Code Client'
    def execute(self, context):
        try: start(context)
        except Exception as error:
            self.report({'ERROR'}, str(error));return {'CANCELLED'}
        return {'FINISHED'}


class Disable(bpy.types.Operator):
    bl_idname = 'chimera.disable_client';bl_label = 'Disable Local Client'
    def execute(self, context):
        stop();return {'FINISHED'}


class Panel(bpy.types.Panel):
    bl_label = 'Local Z Code Connection';bl_idname = 'CHIMERA_PT_client'
    bl_space_type = 'VIEW_3D';bl_region_type = 'UI';bl_category = 'Chimera'
    def draw(self, context):
        from .operations_ui import wrapped
        layout = self.layout
        if _state:
            wrapped(layout, context, 'Session: ' + _state['id'])
            layout.operator('chimera.disable_client')
            wrapped(layout, context, 'Uses the shared operations, purposes and native job status.')
        else: layout.operator('chimera.enable_client')
        wrapped(layout, context, _last_message)
        wrapped(layout, context, 'Run tools/studio_client.py sessions from Z Code. File changes close this connection.')


CLASSES = (Enable, Disable, Panel)


def register():
    for cls in CLASSES: bpy.utils.register_class(cls)
    bpy.app.handlers.load_pre.append(load_pre)


def unregister():
    stop('Integration disabled')
    if load_pre in bpy.app.handlers.load_pre: bpy.app.handlers.load_pre.remove(load_pre)
    for cls in reversed(CLASSES): bpy.utils.unregister_class(cls)
