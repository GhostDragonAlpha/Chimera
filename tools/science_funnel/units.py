"""Explicit SI conversions; dimension equality never implies semantic equality.

Exponent order: mass, length, time, current, temperature, amount, luminous intensity.
SI prefixes/degree definitions are exact. This bounded table is independently
reviewable; importing QUDT text does NOT automatically change executable conversions.
"""
import math
from .common import number, require

DIMENSIONS = {
    'dimensionless': (0, 0, 0, 0, 0, 0, 0),
    'length': (0, 1, 0, 0, 0, 0, 0), 'area': (0, 2, 0, 0, 0, 0, 0),
    'volume': (0, 3, 0, 0, 0, 0, 0), 'mass': (1, 0, 0, 0, 0, 0, 0),
    'time': (0, 0, 1, 0, 0, 0, 0), 'frequency': (0, 0, -1, 0, 0, 0, 0),
    'force': (1, 1, -2, 0, 0, 0, 0), 'pressure': (1, -1, -2, 0, 0, 0, 0),
    'compressibility': (-1, 1, 2, 0, 0, 0, 0),
    'stiffness': (1, 0, -2, 0, 0, 0, 0), 'torque': (1, 2, -2, 0, 0, 0, 0),
    'temperature': (0, 0, 0, 0, 1, 0, 0), 'speed': (0, 1, -1, 0, 0, 0, 0),
    'density': (1, -3, 0, 0, 0, 0, 0), 'viscosity': (1, -1, -1, 0, 0, 0, 0),
    'volume_flow': (0, 3, -1, 0, 0, 0, 0),
    'hydraulic_compliance': (-1, 4, 2, 0, 0, 0, 0),
}
# Quantity semantics retained even for identical dimensions (angle vs strain,
# pressure vs modulus, force vs maximum isometric force, torque vs energy).
QUANTITIES = {k: k for k in DIMENSIONS}
QUANTITIES.update({'young_modulus': 'pressure', 'bulk_modulus': 'pressure',
                   'stress': 'pressure', 'surface_tension': 'stiffness', 'strain': 'dimensionless',
                   'angle': 'dimensionless', 'energy': 'torque',
                   'max_isometric_force': 'force', 'activation_time': 'time'})

# symbol -> (dimension key, multiplier, offset, canonical symbol)
UNITS = {}


def _add(dimension, si, entries):
    for symbol, scale, offset in entries:
        UNITS[symbol] = (dimension, scale, offset, si)


_add('length', 'm', [('m', 1, 0), ('cm', .01, 0), ('mm', .001, 0)])
_add('area', 'm2', [('m2', 1, 0), ('mm2', 1e-6, 0), ('cm2', 1e-4, 0)])
_add('volume', 'm3', [('m3', 1, 0), ('cm3', 1e-6, 0), ('mm3', 1e-9, 0)])
_add('mass', 'kg', [('kg', 1, 0), ('g', .001, 0)])
_add('time', 's', [('s', 1, 0), ('ms', .001, 0)])
_add('pressure', 'Pa', [('Pa', 1, 0), ('kPa', 1e3, 0), ('MPa', 1e6, 0), ('GPa', 1e9, 0)])
_add('temperature', 'K', [('K', 1, 0), ('degC', 1, 273.15)])
_add('dimensionless', '1', [('1', 1, 0)])
_add('dimensionless', 'rad', [('rad', 1, 0), ('deg', math.pi / 180, 0)])
for _dim, _unit in [('force', 'N'), ('stiffness', 'N/m'), ('compressibility', '1/Pa'),
                    ('torque', 'N*m'), ('torque', 'J'), ('frequency', 'Hz'),
                    ('frequency', '1/s'), ('speed', 'm/s'), ('density', 'kg/m3'),
                    ('viscosity', 'Pa*s'), ('volume_flow', 'm3/s'),
                    ('hydraulic_compliance', 'm3/Pa')]:
    _add(_dim, _unit, [(_unit, 1, 0)])


def convert(value, unit, quantity, uncertainty=None):
    require(quantity in QUANTITIES, 'unknown_quantity', quantity)
    require(unit in UNITS, 'unknown_unit', unit)
    dim, a, b, canonical_unit = UNITS[unit]
    require(DIMENSIONS[dim] == DIMENSIONS[QUANTITIES[quantity]], 'unit_dimension_mismatch',
            f'{quantity} / {unit}')
    require((quantity == 'angle') == (unit in ('rad', 'deg')), 'unit_semantics_mismatch',
            f'{quantity} / {unit}')
    require(not (quantity == 'torque' and unit == 'J') and
            not (quantity == 'energy' and unit == 'N*m'), 'unit_semantics_mismatch', unit)
    v = number(value)
    result = number(a * v + b)
    u = None
    if uncertainty is not None:
        u = number(uncertainty)
        require(u >= 0, 'negative_uncertainty')
        u = number(abs(a) * u)
    return {'quantity': quantity, 'value_si': result, 'unit_si': canonical_unit,
            'dimensions': list(DIMENSIONS[dim]), 'uncertainty_si': u,
            'original': {'value': v, 'unit': unit, 'uncertainty': uncertainty},
            'conversion': {'scale': a, 'offset': b}}
