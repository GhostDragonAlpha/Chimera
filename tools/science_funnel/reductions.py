"""Bounded scientific reductions: derivation plus assumptions, never magic equivalence."""
from .common import digest, number, require, text
from .units import convert

LAWS = {
    'axial_stiffness': {
        'inputs': {'E': 'young_modulus', 'A': 'area', 'L': 'length'},
        'output': ('stiffness', 'N/m'), 'equation': 'k = E*A/L',
        'derivation': 'stress=E*strain; F/A=E*(delta_L/L); hence F=(E*A/L)*delta_L.',
        'assumptions': ['small_axial_strain', 'homogeneous_material', 'uniform_cross_section',
                        'straight_taut_member', 'quasistatic_loading'],
    },
    'hydraulic_compliance': {
        'inputs': {'kappa': 'compressibility', 'V0': 'volume'},
        'output': ('hydraulic_compliance', 'm3/Pa'), 'equation': 'C = kappa*V0',
        'derivation': 'kappa=-(1/V)*dV/dP; linearize about V0: delta_V=-kappa*V0*delta_P.',
        'assumptions': ['small_volume_strain', 'constant_compressibility', 'single_liquid_phase'],
    },
    'propagation_delay': {
        'inputs': {'L': 'length', 'v': 'speed'}, 'output': ('time', 's'),
        'equation': 'delay = L/v',
        'derivation': 'dt=ds/v(s); constant v gives integral(ds/v)=L/v.',
        'assumptions': ['uniform_propagation_speed', 'path_length_is_traveled_route'],
    },
}


def reduce(request, records):
    """Calculate a candidate; incomplete applicability is retained as a blocking gap."""
    law_id = request.get('law')
    require(law_id in LAWS, 'reduction_unsupported', law_id)
    law = LAWS[law_id]
    text(request.get('target_id'), 'target_id')
    inputs = request.get('inputs', {})
    require(isinstance(inputs, dict) and set(inputs) == set(law['inputs']), 'reduction_inputs_mismatch')
    ctx = request.get('context', {})
    require(isinstance(ctx, dict), 'reduction_context_required')
    checks = request.get('assumptions', {})
    require(isinstance(checks, dict), 'reduction_assumptions_required')
    blockers = ['runtime_validation_pending', 'uncertainty_propagation_pending']
    for assumption in law['assumptions']:
        if not isinstance(checks.get(assumption), str) or not checks[assumption].strip():
            blockers.append('assumption_unjustified:' + assumption)
    values, provenance, identities = {}, [], []
    for symbol, quantity in law['inputs'].items():
        spec = inputs[symbol]
        require(isinstance(spec, dict) and spec.get('record') in records, 'reduction_record_missing', symbol)
        record = records[spec['record']]
        identities.append(record['id'])
        payload = record['payload']
        if spec.get('field') == 'length_m':
            require(record['record_type'] == 'geometry' and quantity == 'length', 'reduction_field_mismatch')
            measurement = convert(payload['length_m'], 'm', 'length')
            conditions = {'frame': payload['frame']['id']}
            blockers.append('geometry_instance_binding_pending:' + symbol)
        else:
            require(spec.get('field') in (None, 'value_si') and
                    record['record_type'] == 'measurement', 'reduction_scalar_required', symbol)
            measurement = payload
            conditions = payload.get('conditions', {})
        require(measurement['quantity'] == quantity, 'reduction_quantity_mismatch', symbol)
        value = number(measurement['value_si'])
        require(value > 0, 'reduction_positive_input_required', symbol)
        # Source values are condition-dependent. Absence never means universality.
        if not conditions:
            blockers.append('source_conditions_missing:' + symbol)
        for key in sorted(set(conditions) | set(ctx)):
            a, b = conditions.get(key), ctx.get(key)
            if a in (None, '', 'unknown') or b in (None, '', 'unknown'):
                blockers.append('applicability_unresolved:' + symbol + ':' + key)
            else:
                require(a == b, 'applicability_mismatch', symbol + ':' + key)
        if record['source'].get('license', '').lower() in ('unknown', 'not stated'):
            blockers.append('license_unresolved:' + symbol)
        values[symbol] = value
        provenance.append({'symbol': symbol, 'record_id': record['id'],
                           'source_version': record['source_version'],
                           'artifact': record['artifact'], 'value_si': value})
    if law_id == 'axial_stiffness':
        output = values['E'] * values['A'] / values['L']
    elif law_id == 'hydraulic_compliance':
        output = values['kappa'] * values['V0']
    else:
        output = values['L'] / values['v']
    prediction = request.get('validation', {})
    require(isinstance(prediction, dict), 'validation_record_required')
    for key in ('observable', 'falsifier', 'acceptance_rule'):
        if not isinstance(prediction.get(key), str) or not prediction[key].strip():
            blockers.append('validation_missing:' + key)
    result = {'record_type': 'reduction', 'law': law_id, **law,
              'target_id': request['target_id'], 'result': convert(number(output), law['output'][1], law['output'][0]),
              'selected_inputs': provenance, 'input_ids': sorted(set(identities)),
              'request': request, 'runtime_ready': False, 'authority': 'derived_candidate',
              'blockers': sorted(set(blockers))}
    result['id'] = 'data.reduction.' + digest(result)
    return result
