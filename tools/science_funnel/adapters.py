"""Database funnels. All imported content is data; nothing here executes a model."""
import csv
import io
import math
from .common import Refusal, draft, loads, number, require, text
from .units import convert


def rejection(location, exc):
    return {'location': location, 'refusal': {'code': exc.code, 'detail': exc.detail}}


def tabular(raw):
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig'), newline=''))
    fields = reader.fieldnames
    require(fields and len(set(fields)) == len(fields), 'csv_bad_header')
    result = list(reader)
    require(result, 'empty_capture')
    require(all(None not in row and all(v is not None for v in row.values())
                for row in result), 'csv_ragged_row')
    return result


def context(manifest, row=None):
    ctx = dict(manifest.get('conditions', {}))
    for key, column in manifest.get('condition_columns', {}).items():
        require(row is not None and column in row, 'missing_column', column)
        ctx[key] = row[column] or 'unknown'
    return ctx


def cell(row, manifest, field, optional=False):
    columns = manifest.get('columns', {})
    column = columns.get(field, field)
    if field in manifest.get('constants', {}):
        return manifest['constants'][field]
    if optional and (column not in row or row[column] == ''):
        return None
    require(column in row and row[column] != '', 'missing_column_value', column)
    return row[column]


def measurements(raw, manifest, path):
    out = []
    for index, row in enumerate(tabular(raw), 2):
        try:
            q = cell(row, manifest, 'quantity')
            q = manifest.get('quantity_map', {}).get(q, q)
            unit = cell(row, manifest, 'unit')
            unit = manifest.get('unit_map', {}).get(unit, unit)
            value = convert(cell(row, manifest, 'value'), unit, q,
                            cell(row, manifest, 'uncertainty', optional=True))
            value.update(subject=text(cell(row, manifest, 'subject'), 'subject'),
                         conditions=context(manifest, row), raw_row=row)
            out.append(draft(cell(row, manifest, 'id'), 'measurement', value,
                             unknowns=['uncertainty'] if value['uncertainty_si'] is None else []))
        except Refusal as exc:
            out.append(rejection(f'csv_record:{index}', exc))
    return out


def series(raw, manifest, path):
    groups = {}
    for row in tabular(raw):
        groups.setdefault(cell(row, manifest, 'id'), []).append(row)
    out = []
    for key, rows in sorted(groups.items()):
        try:
            samples, metadata = [], None
            for row in rows:
                x = convert(cell(row, manifest, 'x'), cell(row, manifest, 'x_unit'),
                            cell(row, manifest, 'x_quantity'))
                y = convert(cell(row, manifest, 'value'), cell(row, manifest, 'unit'),
                            cell(row, manifest, 'quantity'),
                            cell(row, manifest, 'uncertainty', optional=True))
                current = {'subject': cell(row, manifest, 'subject'),
                           'conditions': context(manifest, row),
                           'x_quantity': x['quantity'], 'x_unit_si': x['unit_si'],
                           'quantity': y['quantity'], 'unit_si': y['unit_si']}
                require(metadata is None or current == metadata, 'series_context_changed', key)
                metadata = current
                require(not samples or x['value_si'] > samples[-1]['x'], 'axis_not_increasing', key)
                samples.append({'x': x['value_si'], 'value': y['value_si'],
                                'uncertainty': y['uncertainty_si']})
            require(len(samples) >= 2, 'insufficient_samples', key)
            out.append(draft(key, 'series', {**metadata, 'samples': samples,
                                           'interpolation': 'unspecified', 'raw_rows': rows},
                             unknowns=['interpolation', 'sampling_protocol_if_not_in_conditions']))
        except Refusal as exc:
            out.append(rejection('series:' + key, exc))
    return out


def two_point_frame(anchors, unit):
    require(isinstance(anchors, list) and len(anchors) == 2 and
            all(isinstance(p, list) and len(p) == 3 for p in anchors), 'two_3d_anchors_required')
    a, b = [[convert(c, unit, 'length')['value_si'] for c in p] for p in anchors]
    delta = [number(y - x) for x, y in zip(a, b)]
    length = number(math.hypot(*delta))
    require(length > 0, 'coincident_anchors')
    z = [v / length for v in delta]
    # Explicit deterministic roll convention. Two points cannot recover anatomical roll.
    helper = [0., 0., 0.]
    helper[min(range(3), key=lambda i: abs(z[i]))] = 1.
    def cross(u, v):
        return [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
    x = cross(helper, z)
    norm = math.hypot(*x)
    x = [v / norm for v in x]
    y = cross(z, x)
    return {'anchors_m': [a, b], 'origin_m': a, 'basis_columns': [x, y, z],
            'length_m': length, 'roll': 'least_aligned_source_axis_convention',
            'placement': 'unbound_source_frame'}


def geometry(raw, manifest, path):
    records = loads(raw)
    require(isinstance(records, list) and records, 'geometry_list_required')
    out = []
    for index, record in enumerate(records):
        try:
            require(isinstance(record, dict), 'geometry_record_required')
            frame = record.get('frame', {})
            require(isinstance(frame, dict), 'coordinate_frame_required')
            text(frame.get('id'), 'frame.id')
            require(frame.get('handedness') == 'right', 'right_handed_frame_required')
            text(frame.get('axis_convention'), 'frame.axis_convention')
            basis = two_point_frame(record.get('anchors'), record.get('length_unit'))
            out.append(draft(record.get('id'), 'geometry', {**basis, 'frame': frame,
                            'shape_specification': record.get('shape', {}), 'raw_record': record},
                             unknowns=['engine_frame_transform', 'shape_meshing', 'anatomical_roll']))
        except Refusal as exc:
            out.append(rejection(f'geometry:{index}', exc))
    return out


def model(raw, manifest, path):
    records = loads(raw)
    require(isinstance(records, list) and records, 'model_list_required')
    out = []
    for index, record in enumerate(records):
        try:
            require(isinstance(record, dict), 'model_record_required')
            for field in ('id', 'equations', 'validity_domain', 'assumptions'):
                require(record.get(field), 'model_field_required', field)
            require(isinstance(record.get('ports'), list) and record['ports'], 'model_ports_required')
            for port in record['ports']:
                require(isinstance(port, dict), 'model_port_required')
                text(port.get('name'), 'port.name')
                convert(0, port.get('unit'), port.get('quantity'))
            out.append(draft(record['id'], 'model', {'definition': record, 'executable': False},
                             unknowns=['compiler_implementation', 'numerical_qualification']))
        except Refusal as exc:
            out.append(rejection(f'model:{index}', exc))
    return out


def ontology(raw, manifest, path):
    from tools.reference_data.parsers import parse_obo
    parsed = parse_obo(str(path))
    return [draft(t['id'], 'relation' if t.get('is_typedef') else 'entity', t, label=t.get('name'),
                  unknowns=['unprojected_ontology_axioms']) for t in parsed['terms']
            if t.get('id')]


def relations(raw, manifest, path):
    from tools.reference_data.parsers import parse_ro_owl
    require(b'<!DOCTYPE' not in raw.upper() and b'<!ENTITY' not in raw.upper(), 'xml_doctype_refused')
    parsed = parse_ro_owl(str(path))
    return [draft(r['iri'], 'relation', r, label=r.get('label'),
                  unknowns=['domain_range_and_property_chains']) for r in parsed]


def units(raw, manifest, path):
    from tools.reference_data.parsers import parse_qudt_ttl
    rec = parse_qudt_ttl(str(path))
    return [draft(rec['subject'], 'unit_definition', rec, label=rec.get('label'),
                  unknowns=['full_RDF_semantics', 'conversion_offset_not_projected'])]


OSIM_FIELDS = {
    'max_isometric_force_N': ('max_isometric_force', 'N'),
    'optimal_fiber_length_m': ('length', 'm'), 'tendon_slack_length_m': ('length', 'm'),
    'pennation_angle_at_optimal_rad': ('angle', 'rad'),
    'max_contraction_velocity': ('frequency', '1/s'),
    'activation_time_constant_s': ('activation_time', 's'),
    'deactivation_time_constant_s': ('activation_time', 's'),
}


def opensim(raw, manifest, path):
    from tools.reference_data.parsers import parse_osim
    require(b'<!DOCTYPE' not in raw.upper() and b'<!ENTITY' not in raw.upper(), 'xml_doctype_refused')
    parsed = parse_osim(str(path))
    name = text(parsed.get('model_name'), 'OpenSim model name')
    out = [draft(name, 'model', {'definition': parsed, 'executable': False},
                 unknowns=['partial_XML_projection', 'frame_transforms', 'body_mass_inertia_projection',
                           'source_model_to_creature_adaptation'])]
    for muscle in parsed['muscles']:
        for field, (quantity, unit) in OSIM_FIELDS.items():
            if muscle[field] is None:
                continue
            value = convert(muscle[field], unit, quantity)
            value.update(subject=name + '/muscle/' + muscle['name'], source_parameter=field,
                         conditions={**context(manifest), 'model': name,
                                     'parameter_semantics': field})
            if field == 'max_contraction_velocity':
                value['conditions']['normalization'] = 'optimal fiber lengths per second; not m/s'
            out.append(draft(name + '/' + muscle['name'] + '/' + field, 'measurement', value,
                             unknowns=['uncertainty', 'creature_applicability']))
    return out


ADAPTERS = {'uberon_obo': ontology, 'ro_owl': relations, 'qudt_ttl': units,
            'opensim_xml': opensim, 'measurements_csv': measurements, 'series_csv': series,
            'geometry_json': geometry, 'model_json': model}

def coolprop_surface(raw, manifest, path):
    """Strict selected CoolProp correlation; no arbitrary equation execution."""
    fluid = loads(raw)
    surface = fluid['ANCILLARIES']['surface_tension']
    name = text(fluid['INFO']['NAME'], 'fluid name')
    temperature = number(manifest.get('temperature_K'))
    # This adapter qualifies one common comparison temperature only. EOS bounds
    # alone do not establish a surface-correlation applicability interval.
    require(temperature == 298.15, 'surface_temperature_not_qualified')
    require(surface['description'] == 'sigma = sum(a_i*(1-T/Tc)^n_i)', 'surface_model_unsupported')
    tc = number(surface['Tc'])
    a = [number(x) for x in surface['a']]
    n = [number(x) for x in surface['n']]
    require(len(a) == len(n) and a and tc > temperature, 'surface_coefficients_invalid')
    value = sum(x * (1-temperature/tc)**power for x,power in zip(a,n))
    require(value > 0, 'surface_tension_nonpositive')
    payload = convert(value, 'N/m', 'surface_tension')
    payload.update(subject=name, conditions={'temperature_K':temperature,
      'interface':'pure_liquid_vapor','measurement_kind':'published_correlation_evaluation'},
      correlation={'a_N_m':a,'n':n,'Tc_K':tc,'reference':surface['BibTeX']})
    return [draft(name+'/surface_tension/298.15K', 'measurement', payload,
              unknowns=['source_fit_uncertainty','bulk_flow','optical_appearance'])]

ADAPTERS['coolprop_surface'] = coolprop_surface

from .force_adapters import FORCE_ADAPTERS
ADAPTERS.update(FORCE_ADAPTERS)
