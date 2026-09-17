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

from .adapters_life import LIFE_ADAPTERS
ADAPTERS.update(LIFE_ADAPTERS)


def smithsonian_voyager(raw, manifest, path):
    """Smithsonian 3D Voyager document.json -> geometry candidates (one per model).

    Derivative policy: the Web3D High GLB is the pinned mesh asset; the document
    itself (with units and bounding box) and the GLB bytes are both pinned in the
    bundle. Mesh geometry is NOT parsed here -- admission is metadata + pinned
    bytes, geometry reduction is a later membrane.
    """
    doc = loads(raw)
    require(doc.get('asset', {}).get('type') == 'application/si-dpo-3d.document+json',
            'smithsonian_document_type')
    scene = doc['scenes'][doc.get('scene', 0)]
    units = text(scene.get('units'), 'scene units')
    collection = doc['metas'][0]['collection']
    title = text(collection.get('title'), 'collection title')
    record_id = text(collection.get('edanRecordId'), 'edan record id')
    # model names live on the SCENE NODES referencing the model index
    node_names = {}
    for node in doc.get('nodes', []):
        if isinstance(node, dict) and 'model' in node and node.get('name'):
            node_names[node['model']] = node['name']
    out = []
    for index, model in enumerate(doc['models']):
        name = node_names.get(index) or 'model' + str(index)
        require(model.get('units') == units, 'model_units_conflict', name)
        derivative = None
        for candidate in model.get('derivatives', []):
            if candidate.get('usage') == 'Web3D' and candidate.get('quality') == 'High':
                derivative = candidate
                break
        require(derivative is not None, 'derivative_high_missing', name)
        asset = derivative['assets'][0]
        box = model['boundingBox']
        extents = [box['max'][axis] - box['min'][axis] for axis in range(3)]
        payload = {'units': units, 'bbox_min_mm': list(box['min']),
                   'bbox_max_mm': list(box['max']), 'bbox_extent_mm': max(extents),
                   'glb_uri': asset['uri'], 'glb_byte_size': asset['byteSize'],
                   'glb_faces': asset['numFaces'], 'title': title,
                   'copyright_field': doc['asset'].get('copyright', '')}
        row = draft('si3d:' + record_id + ':' + name, 'geometry', payload,
                    unknowns=['mesh_geometry_not_parsed', 'license_metadata_conflict'
                              if payload['copyright_field'] else 'mesh_reduction_pending'],
                    label=title + ' / ' + name)
        row['class_contract'] = {'class_id': 'batch.geometry.smithsonian_voyager', 'version': 1}
        out.append(row)
    return out


ADAPTERS['smithsonian_voyager'] = smithsonian_voyager


def copernicus_meta(raw, manifest, path):
    """Copernicus DSM tile EOXML -> tile property assertions.

    Reads only what the tile's own metadata declares: posting scale, vertical
    quantization, extent polygon, datum codes, vertical envelope. The EOXML
    verticalDatumCode carries the horizontal datum code (known ESA quirk); the
    EGM2008 height datum is named by the vertical extent's geoid element and the
    ambiguity is carried on every row as an unknown, never silently resolved.
    """
    import xml.etree.ElementTree as ET
    root = ET.fromstring(raw.decode('utf-8-sig'))

    def text_of(tag):
        for element in root.iter():
            if element.tag.split('}')[-1] == tag:
                for child in element.iter():
                    value = (child.text or '').strip()
                    if value:
                        return value
        raise Refusal('missing_text', tag)

    def decimals(tag, limit):
        values = []
        for element in root.iter():
            if element.tag.split('}')[-1] != tag:
                continue
            for child in element.iter():
                value = (child.text or '').strip()
                if value:
                    values.append(float(value))
                    break
        require(len(values) >= limit, 'missing_text', tag)
        return values

    tile = text_of('fileIdentifier').replace('.xml', '')
    posting = None
    for element in root.iter():
        if element.tag.split('}')[-1] != 'resolution':
            continue
        for child in element.iter():
            if child.tag.split('}')[-1] == 'Scale':
                value = (child.text or '').strip()
                if value:
                    posting = float(value)
                    break
    require(posting and posting > 0, 'missing_text', 'resolution/Scale')
    vertical_spacing = float(text_of('verticalSpacing'))
    h_datum = text_of('horizontalDatumCode')
    v_datum_field = text_of('verticalDatumCode')
    lons = sorted({v for v in decimals('westBoundLongitude', 1) + decimals('eastBoundLongitude', 1)})
    lats = sorted({v for v in decimals('southBoundLatitude', 1) + decimals('northBoundLatitude', 1)})
    require(len(lons) == 2 and len(lats) == 2, 'extent_incomplete', tile)
    heights = decimals('minimumValue', 1) + decimals('maximumValue', 1)
    require(len(heights) >= 2, 'vertical_extent_incomplete', tile)
    geoid = 'EGM2008 geoid'
    rows = [
        ('posting', posting, 'arcsec', 'horizontal posting scale declared by the tile EOXML'),
        ('vertical_quantization', vertical_spacing, 'm', 'vertical quantization step'),
        ('extent_west', lons[0], 'degree', 'tile extent polygon'),
        ('extent_east', lons[1], 'degree', 'tile extent polygon'),
        ('extent_south', lats[0], 'degree', 'tile extent polygon'),
        ('extent_north', lats[1], 'degree', 'tile extent polygon'),
        ('height_min', min(heights), 'm', 'vertical envelope over the tile'),
        ('height_max', max(heights), 'm', 'vertical envelope over the tile'),
    ]
    conditions = {'tile': tile, 'horizontal_datum_code': h_datum,
                  'dataset': 'Copernicus DEM GLO-30 Public (DSM, not bare earth)',
                  'datum_law': 'h = H + N: keep H native EGM2008 orthometric, scene frame WGS84 ellipsoidal',
                  'geoid_named_by_tile': geoid}
    out = []
    for field, value, unit, note in rows:
        payload = {'value_si': value, 'unit_si': unit, 'conditions': dict(conditions),
                   'subject': tile, 'note': note}
        row = draft('copernicus:' + tile + ':' + field, 'measurement', payload,
                    unknowns=['eoxml_vertical_datum_code_carries_horizontal_code:'
                              + v_datum_field, 'dsm_not_bare_earth', 'abs_accuracy_4m_LE90'])
        row['class_contract'] = {'class_id': 'batch.property.copernicus_tile', 'version': 1}
        out.append(row)
    return out


ADAPTERS['copernicus_meta'] = copernicus_meta


def bp3d_lists(raw, manifest, path):
    """BodyParts3D concept lists -> anatomy entity records (one per FMA concept).

    The primary artifact is partof_parts_list_e.txt; the companion isa list is
    named by sha256 in manifest constants and read from the bundle directory.
    Concepts appearing in both lists are emitted once with both lists recorded;
    a concept whose label or representation id disagrees across lists is
    quarantined (no silent merge). Mesh element files and inclusion pairs stay
    pinned attachments -- geometry import is a later membrane.
    """
    companion_pin = manifest.get('constants', {}).get('isa_parts_sha256')
    require(companion_pin, 'missing_text', 'constants.isa_parts_sha256')

    def concepts(blob, origin):
        rows = []
        for index, line in enumerate(blob.decode('utf-8-sig').splitlines()[1:], 2):
            if not line.strip():
                continue
            parts = line.split('\t')
            require(len(parts) >= 3, 'missing_text', origin + ':row' + str(index))
            rows.append((parts[0].strip(), parts[1].strip(), parts[2].strip()))
        return rows

    merged = {}
    conflicts = []
    for origin, blob in (('partof', raw),
                         ('isa', path.parent.joinpath(companion_pin).read_bytes())):
        for fma, bp, label in concepts(blob, origin):
            if fma in merged and merged[fma][1] != (bp, label):
                conflicts.append({'location': origin + ':' + fma, 'refusal': {
                    'code': 'duplicate_source_identity',
                    'detail': 'label/representation differs across lists: '
                              + repr(merged[fma][1]) + ' vs ' + repr((bp, label))}})
                continue
            entry = merged.setdefault(fma, [[], (bp, label)])
            if origin not in entry[0]:
                entry[0].append(origin)
    out = []
    for fma in sorted(merged):
        lists, (bp, label) = merged[fma]
        payload = {'fma_id': fma, 'representation_id': bp, 'label': label,
                   'lists': lists, 'license': 'CC Attribution 4.0 International',
                   'attribution': 'BodyParts3D, (c) The Database Center for Life Science'}
        row = draft('bp3d:' + fma, 'entity', payload,
                    unknowns=['mesh_geometry_not_imported', 'fma_version_not_pinned'],
                    label=label)
        row['class_contract'] = {'class_id': 'batch.entity.external', 'version': 1}
        out.append(row)
    return out + conflicts


ADAPTERS['bp3d_lists'] = bp3d_lists
