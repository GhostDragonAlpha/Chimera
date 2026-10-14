"""Lane adapter module (auto-loaded): EGM08 geoid grid metadata properties.
Reads ONLY the TIFF header tags -- the 80 MB payload stays a pinned blob."""
from .common import draft
from .terrain import tiff_tags

_SHORT = {256: 'width', 257: 'height', 258: 'bits', 259: 'compression',
          322: 'tile_w', 323: 'tile_h', 339: 'sample_fmt'}


def egm08_grid_meta(raw, manifest, path):
    tags, endian, size = tiff_tags(str(path))
    dims = {}
    for tag, name in _SHORT.items():
        typ, cnt, val = tags[tag]
        dims[name] = val if typ == 3 else val
    require_fields = ('width', 'height', 'compression', 'tile_w', 'tile_h')
    for field in require_fields:
        if not dims.get(field):
            raise ValueError('egm08 tag missing: ' + field)
    from .common import Refusal
    if dims['compression'] != 8 or dims['bits'] != 32 or dims['sample_fmt'] != 3:
        raise Refusal('egm08_not_float32_deflate', str(dims))
    conditions = {'model': 'Earth Gravitational Model 2008', 'grid': '2.5 arcminute',
                  'datum_role': 'undulation N in h = H + N (EGM2008 orthometric to '
                                'WGS84 ellipsoidal)'}
    rows = [
        ('grid_columns', dims['width'], 'dimensionless'),
        ('grid_rows', dims['height'], 'dimensionless'),
        ('grid_spacing_deg', 360.0 / dims['width'], 'degree'),
        ('file_bytes', size, 'dimensionless'),
    ]
    out = []
    for field, value, unit in rows:
        payload = {'value_si': float(value), 'unit_si': unit,
                   'conditions': dict(conditions), 'subject': 'us_nga_egm08_25.tif',
                   'note': 'grid header metadata; payload stays a pinned blob'}
        row = draft('egm08:' + field, 'measurement', payload,
                    unknowns=['no uncertainty field in the grid',
                              'geoid slope between nodes is interpolated, not measured'])
        row['class_contract'] = {'class_id': 'batch.property.measurement', 'version': 1}
        out.append(row)
    return out


EXTRA_ADAPTERS = {'egm08_grid_meta': egm08_grid_meta}
