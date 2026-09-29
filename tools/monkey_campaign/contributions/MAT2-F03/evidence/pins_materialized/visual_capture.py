"""Pure structural checks for camera-pinned capture manifests.

This does not inspect pixels, authenticate telemetry, or award visual acceptance.
The caller hashes the actual capture and supplies its identity and runtime interval
in context. Each required named view has a diagnostic row and, when requested, a
clean row of the same state/trace and camera. All coordinates within a camera use
its declared frame and length unit. Orientation is a unit quaternion mapping
camera coordinates to that frame, in w,x,y,z order.
"""
import math
import re


SCHEMA = 'chimera.visual_capture_manifest.v1'
MAX_VIEWS = 64
MAX_SAMPLES = 10000


def require(ok, code):
    if not ok:
        raise ValueError(code)


def obj(value, code):
    require(isinstance(value, dict), code)
    return value


def text(value):
    return isinstance(value, str) and bool(value.strip())


def digest(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def number(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def vector(value, size, code):
    require(isinstance(value, list) and len(value) == size and all(number(x) for x in value), code)
    return value


def names(value, code, nonempty=False):
    require(isinstance(value, list) and all(text(x) for x in value), code)
    require(len(set(value)) == len(value) and (bool(value) or not nonempty), code)
    return value


def interval(value, code):
    require(isinstance(value, list) and len(value) == 2
            and all(type(x) is int and x >= 0 for x in value) and value[0] <= value[1], code)
    return value


def camera(value, ticks, motion):
    c = obj(value, 'camera_missing_or_invalid')
    require(text(c.get('frame_id')), 'camera_frame_missing')
    require(c.get('coordinate_unit') in ('m', 'cm', 'mm'), 'camera_coordinate_unit_invalid')
    require(c.get('handedness') in ('right', 'left'), 'camera_handedness_missing')
    require(c.get('orientation_convention') == 'quaternion_wxyz_camera_to_frame',
            'camera_orientation_convention_invalid')
    axes = ('+X', '-X', '+Y', '-Y', '+Z', '-Z')
    forward, up = c.get('forward_axis'), c.get('up_axis')
    require(forward in axes and up in axes and forward[-1] != up[-1],
            'camera_local_axes_invalid')
    near, far = vector(c.get('near_far_planes'), 2, 'camera_clip_planes_invalid')
    require(0 < near < far, 'camera_clip_planes_invalid')
    resolution = c.get('viewport_resolution')
    require(isinstance(resolution, list) and len(resolution) == 2
            and all(type(x) is int and 1 <= x <= 65536 for x in resolution),
            'camera_resolution_invalid')
    aspect = c.get('aspect_ratio')
    require(number(aspect) and aspect > 0
            and math.isclose(aspect, resolution[0] / resolution[1], rel_tol=1e-6, abs_tol=1e-9),
            'camera_aspect_resolution_mismatch')
    projection = c.get('projection')
    require(projection in ('perspective', 'orthographic'), 'camera_projection_invalid')
    if projection == 'perspective':
        fov = c.get('vertical_fov_degrees')
        require(number(fov) and 0 < fov < 180, 'camera_fov_invalid')
        require('orthographic_span' not in c, 'camera_projection_parameters_conflict')
    else:
        span = c.get('orthographic_span')
        require(number(span) and span > 0, 'camera_orthographic_span_invalid')
        require('vertical_fov_degrees' not in c, 'camera_projection_parameters_conflict')
    require(c.get('sample_mode') in ('fixed_bookmark', 'sampled_trajectory'),
            'camera_sample_mode_invalid')
    samples = c.get('samples')
    require(isinstance(samples, list) and 1 <= len(samples) <= MAX_SAMPLES,
            'camera_samples_missing_or_invalid')
    require(not motion or len(samples) >= 2, 'motion_camera_samples_required')
    last = None
    for s in samples:
        obj(s, 'camera_sample_invalid')
        tick = s.get('tick')
        require(type(tick) is int and ticks[0] <= tick <= ticks[1]
                and (last is None or tick > last), 'camera_sample_tick_invalid')
        last = tick
        position = vector(s.get('position'), 3, 'camera_position_invalid')
        target = vector(s.get('target'), 3, 'camera_target_invalid')
        distance = s.get('distance_to_target')
        actual_distance = math.dist(position, target)
        require(number(distance) and distance > 0 and math.isfinite(actual_distance)
                and math.isclose(distance, actual_distance, rel_tol=1e-6, abs_tol=1e-9),
                'camera_target_distance_mismatch')
        q = vector(s.get('orientation'), 4, 'camera_orientation_invalid')
        require(math.isclose(math.hypot(*q), 1.0, rel_tol=1e-6, abs_tol=1e-9),
                'camera_quaternion_not_unit')
    require(samples[0]['tick'] == ticks[0] and samples[-1]['tick'] == ticks[1],
            'camera_samples_do_not_cover_interval')
    if c['sample_mode'] == 'fixed_bookmark':
        first = {k: samples[0][k] for k in ('position', 'target', 'distance_to_target', 'orientation')}
        require(all(all(s[k] == v for k, v in first.items()) for s in samples),
                'fixed_camera_bookmark_changes')
    else:
        require(c.get('interpolation') in ('recorded_each_tick', 'linear_position_target_slerp_orientation'),
                'camera_interpolation_missing')
        if c['interpolation'] == 'recorded_each_tick':
            require(len(samples) == ticks[1] - ticks[0] + 1, 'camera_recorded_ticks_missing')
    return c


def visibility(value, mode):
    v = obj(value, 'visibility_missing_or_invalid')
    layers = names(v.get('layers'), 'visibility_layers_invalid')
    labels = names(v.get('label_ids'), 'visibility_label_ids_invalid')
    names(v.get('selected_ids'), 'visibility_selected_ids_invalid')
    required = names(v.get('required_subject_ids'), 'visibility_required_subject_ids_invalid', True)
    observed = names(v.get('observed_subject_ids'), 'visibility_observed_subject_ids_invalid')
    missing = names(v.get('missing_subject_ids'), 'visibility_missing_subject_ids_invalid')
    require(set(required) <= set(observed) and not missing, 'required_subject_visibility_not_declared')
    require(v.get('occlusion_mode') in ('depth_tested', 'xray', 'mixed'), 'visibility_occlusion_mode_invalid')
    bindings = v.get('tag_bindings')
    require(isinstance(bindings, list) and len(bindings) <= 10000, 'tag_bindings_invalid')
    bound = []
    for binding in bindings:
        obj(binding, 'tag_binding_invalid')
        require(text(binding.get('label_id')) and text(binding.get('subject_id')), 'tag_binding_invalid')
        bound.append(binding['label_id'])
    require(len(bound) == len(set(bound)) and set(bound) == set(labels), 'tag_binding_identity_mismatch')
    if mode == 'clean':
        require(not labels and not layers and not bindings and v['occlusion_mode'] == 'depth_tested',
                'clean_view_contains_diagnostics')
    else:
        require(bool(layers), 'diagnostic_layers_missing')
    return v


def artifact_locator(value, motion):
    """Locate this view inside the root hashed capture, without decoding media.

    Video seconds are [start, end]; image rectangles are [left, top, width,
    height] in pixels with an upper-left origin. Media duration and dimensions
    are not decoded here and must be checked during independent inspection.
    """
    loc = obj(value, 'capture_artifact_locator_missing')
    kind = loc.get('kind')
    require(kind in ('video', 'image'), 'capture_artifact_locator_kind_invalid')
    require(not motion or kind == 'video', 'motion_artifact_locator_requires_video')
    if kind == 'video':
        seconds = vector(loc.get('seconds'), 2, 'capture_video_seconds_invalid')
        require(0 <= seconds[0] <= seconds[1] and (not motion or seconds[0] < seconds[1]),
                'capture_video_seconds_invalid')
    else:
        region = loc.get('region')
        require(region in ('whole_frame', 'pixel_rectangle'), 'capture_image_region_invalid')
        if region == 'pixel_rectangle':
            rect = loc.get('pixel_rectangle')
            require(isinstance(rect, list) and len(rect) == 4
                    and all(type(x) is int for x in rect)
                    and rect[0] >= 0 and rect[1] >= 0 and rect[2] > 0 and rect[3] > 0,
                    'capture_image_rectangle_invalid')
        else:
            require('pixel_rectangle' not in loc, 'capture_image_region_conflict')
    return kind


def validate_manifest(manifest, context, profile):
    """Validate JSON-compatible camera metadata without mutation or filesystem I/O.

    Context requires task_id, subject_sha256, run_id, capture_sha256, tick_interval.
    Profile requires id, kind, views, clean_view_required and diagnostic_layers.
    Return a structural receipt; independent image/physics review remains mandatory.
    """
    m = obj(manifest, 'capture_manifest_invalid')
    ctx = obj(context, 'capture_context_invalid')
    p = obj(profile, 'capture_profile_invalid')
    require(m.get('schema') == SCHEMA, 'capture_manifest_schema_invalid')
    for key in ('task_id', 'run_id'):
        require(text(ctx.get(key)) and m.get(key) == ctx[key], 'capture_identity_mismatch:' + key)
    for key in ('subject_sha256', 'capture_sha256'):
        require(digest(ctx.get(key)) and m.get(key) == ctx[key], 'capture_identity_mismatch:' + key)
    require(text(p.get('id')) and m.get('profile_id') == p['id'], 'capture_profile_mismatch')
    kind = p.get('kind')
    require(kind in ('visible_static', 'motion', 'final_playthrough'), 'capture_profile_not_visual')
    ticks = interval(m.get('tick_interval'), 'capture_interval_invalid')
    require(ticks == interval(ctx.get('tick_interval'), 'capture_context_interval_invalid'),
            'capture_interval_mismatch')
    motion = kind in ('motion', 'final_playthrough')
    require(not motion or ticks[0] < ticks[1], 'motion_capture_interval_empty')
    wanted = names(p.get('views'), 'profile_views_invalid', True)
    required_layers = names(p.get('diagnostic_layers'), 'profile_diagnostic_layers_invalid')
    require(type(p.get('clean_view_required')) is bool, 'profile_clean_view_requirement_invalid')
    rows = m.get('views')
    require(isinstance(rows, list) and 1 <= len(rows) <= MAX_VIEWS, 'capture_views_invalid')
    seen, pairs, layers_seen, artifact_kinds = set(), {}, set(), set()
    for row in rows:
        r = obj(row, 'capture_view_invalid')
        require(r.get('view_id') in wanted, 'capture_view_not_declared')
        mode = r.get('mode')
        require(mode in ('diagnostic', 'clean'), 'capture_view_mode_invalid')
        key = (r['view_id'], mode)
        require(key not in seen, 'capture_view_duplicate')
        seen.add(key)
        pair_id = r.get('pair_id')
        require(text(pair_id), 'capture_pair_id_missing')
        binding = obj(r.get('state_binding'), 'capture_state_binding_invalid')
        require(binding.get('kind') in ('state', 'trace') and digest(binding.get('sha256')),
                'capture_state_binding_invalid')
        require(not motion or binding['kind'] == 'trace', 'motion_state_trace_required')
        artifact_kinds.add(artifact_locator(r.get('artifact_locator'), motion))
        camera(r.get('camera'), ticks, motion)
        visible = visibility(r.get('visibility'), mode)
        if mode == 'diagnostic':
            layers_seen.update(visible['layers'])
        pair = pairs.setdefault(pair_id, {})
        require(mode not in pair, 'capture_pair_duplicate_mode')
        pair[mode] = r
    for view_id in wanted:
        require((view_id, 'diagnostic') in seen, 'required_diagnostic_view_missing:' + view_id)
        if p['clean_view_required']:
            require((view_id, 'clean') in seen, 'required_clean_view_missing:' + view_id)
    require(set(required_layers) <= layers_seen, 'required_diagnostic_layers_missing')
    require(len(artifact_kinds) == 1, 'capture_artifact_locator_kind_mismatch')
    for pair in pairs.values():
        require('diagnostic' in pair, 'clean_view_without_diagnostic_pair')
        if p['clean_view_required']:
            require('clean' in pair, 'diagnostic_view_without_clean_pair')
        if 'clean' in pair:
            a, b = pair['diagnostic'], pair['clean']
            require(a['view_id'] == b['view_id'], 'capture_pair_view_mismatch')
            require(a['state_binding'] == b['state_binding'], 'capture_pair_state_mismatch')
            require(a['camera'] == b['camera'], 'capture_pair_camera_mismatch')
    return {'mode': 'CAMERA_METADATA_STRUCTURE_ONLY', 'structurally_valid': True,
            'visual_acceptance': False, 'profile_id': p['id'], 'view_count': len(rows),
            'capture_kind': next(iter(artifact_kinds)),
            'limits': 'No pixels, visibility, camera motion, label placement, physical state or reviewer '
                      'identity authenticated. Independent capture and numerical review remain required.'}
