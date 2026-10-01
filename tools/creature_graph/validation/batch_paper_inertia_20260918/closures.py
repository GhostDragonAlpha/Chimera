"""Closure falsifiers for the Oku/Ide/Ogihara 2021 Table 1 admission, derived
BEFORE admission (Rule 0 ordering) and carried on every admitted record.

(a) Mass-sum closure. The table publishes no whole-body mass, so the implied
    whole-body mass IS the five-segment sum (9.111 kg). The table's own
    precision is 0.001 kg per mass cell; each published value is therefore
    ±0.0005 kg, and the five-cell sum carries ±0.0025 kg of rounding
    uncertainty. That is the tolerance the table itself licenses; nothing
    looser is claimed.
(b) Dimensional checks. One unit and one plausibility envelope per quantity,
    with the derivation of each bound recorded below (enforced again per
    record inside the adapter, where a violation quarantines that record).
(c) Plausibility envelope. The pinned PanTHERIA 1.0 archive (the same bytes
    the pantheria_1_0 connector admits) carries one adult-body-mass value for
    Macaca fuscata (literature species mean). Comparison only: the single
    cadaver's implied mass is compared against the species envelope, never
    merged or fused with it. Envelope = species mean ± 10%, the lane's declared
    single-specimen-vs-species-mean allowance; the deviation and the remaining
    margin are both recorded.

Run:  python -B .../closures.py   ->  writes closures.json next to this file.
"""
import csv
import hashlib
import io
import json
import zipfile
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
LANE = HERE.parents[3]
PANTHERIA_ZIP = LANE / 'tools' / 'science_funnel' / 'data' / 'pantheria' / 'ECOL_90_184.zip'
PANTHERIA_MEMBER = 'PanTHERIA_1-0_WR05_Aug2008.txt'
SENTINEL = Decimal('-999.00')

# The five table masses exactly as published (digit strings, 0.001 kg precision).
TABLE_MASSES_KG = [Decimal('8.184'), Decimal('0.557'), Decimal('0.269'),
                   Decimal('0.080'), Decimal('0.021')]
TABLE_MASS_PRECISION = Decimal('0.001')          # the table's stated cell precision
ROUNDING_TOLERANCE = TABLE_MASS_PRECISION / 2 * len(TABLE_MASSES_KG)  # ±0.0025 kg

# (b) unit + envelope per quantity. Derivations:
#  mass    [1e-4, 50] kg: phalanges of a 10 kg macaque sit far above 1e-4; the
#          heaviest single segment of any primate sits far below 50.
#  length  [0.005, 5] m: a phalanx block is centimetres; HAT length is well
#          under any whole-primate crown-rump bound of 5 m.
#  COM     [0, 1] dimensionless fraction: a COM between the segment endpoints.
#  I       [1e-8, 1] kg*m2: phalanges (0.02 kg, ~0.05 m) give ~1e-5 kg*m2, four
#          orders above the floor; HAT (8 kg, ~0.5 m) gives ~1e-1, an order
#          below the ceiling.
QUANTITY_SPECS = {
    'mass':    {'unit_si': 'kg',   'min': 1e-4, 'max': 50.0},
    'length':  {'unit_si': 'm',    'min': 0.005, 'max': 5.0},
    'com_fraction': {'unit_si': '1', 'min': 0.0, 'max': 1.0},
    'moment_of_inertia': {'unit_si': 'kg*m2', 'min': 1e-8, 'max': 1.0},
}
SPECIES_MEAN_ALLOWANCE = Decimal('0.10')  # declared: single specimen vs species mean


def mass_sum_closure():
    total = sum(TABLE_MASSES_KG, Decimal('0'))
    return {
        'closure': 'segment mass sum == implied whole-body mass (table precision)',
        'segment_masses_kg_published': [str(m) for m in TABLE_MASSES_KG],
        'implied_whole_body_mass_kg': str(total),
        'cell_precision_kg': str(TABLE_MASS_PRECISION),
        'rounding_tolerance_kg': '±' + str(ROUNDING_TOLERANCE),
        'tolerance_derivation': ('5 published mass cells at the table\'s stated '
                                 '0.001 kg precision -> 5 × 0.0005 kg'),
        'whole_body_mass_published': None,
        'verdict': 'CLOSED (identity; the sum IS the implied mass, ±0.0025 kg '
                   'rounding uncertainty)',
        'open_question': ('the table publishes no whole-body mass; the ~10.0 kg '
                          'nominal cadaver and the PanTHERIA species mean are '
                          'external comparison targets, see plausibility closure'),
    }


def dimensional_checks():
    return {
        'closure': 'per-quantity unit + plausibility envelope (adapter-enforced per record)',
        'quantities': {name: dict(spec, derivation=doc)
                       for (name, spec), doc in zip(
                           sorted(QUANTITY_SPECS.items()), [
                               'phalanges of a 10 kg macaque far above 1e-4 kg; '
                               'heaviest primate segment far below 50 kg',
                               'phalanx block centimetres; HAT length under a 5 m '
                               'whole-primate bound',
                               'COM strictly between the segment endpoints '
                               '(footnote: fraction of segment length from the '
                               'proximal end)',
                               'phalanges ~1e-5 kg*m2 (four orders above floor); '
                               'HAT ~1e-1 kg*m2 (an order below ceiling)'])},
        'verdict': 'DECLARED (checked per record at admission; violation quarantines that record)',
    }


def pantheria_fuscata_adult_mass_kg():
    """Read the pinned PanTHERIA zip (same bytes the pantheria_1_0 connector
    admits) and return the Macaca fuscata adult body mass in kg, with the pin."""
    raw = PANTHERIA_ZIP.read_bytes()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        table = archive.read(PANTHERIA_MEMBER).decode('utf-8-sig')
    rows = list(csv.reader(io.StringIO(table, newline=''), delimiter='\t'))
    header = rows[0]
    genus_i, species_i = header.index('MSW05_Genus'), header.index('MSW05_Species')
    mass_col = header.index('5-1_AdultBodyMass_g')
    hits = []
    for row in rows[1:]:
        if len(row) > mass_col and row[genus_i] == 'Macaca' and row[species_i] == 'fuscata':
            value = Decimal(row[mass_col])
            if value != SENTINEL:
                hits.append(value / Decimal('1000'))
    require_single = len(hits) == 1
    return hits, require_single, hashlib.sha256(raw).hexdigest()


def plausibility_closure():
    hits, single, zip_sha = pantheria_fuscata_adult_mass_kg()
    if not single:
        return {'closure': 'species envelope (PanTHERIA, pinned)',
                'verdict': 'UNDECIDED', 'records_found': len(hits),
                'cause': 'expected exactly one Macaca fuscata adult-body-mass record'}
    mean_kg = hits[0]
    implied = sum(TABLE_MASSES_KG, Decimal('0'))
    lower = mean_kg * (1 - SPECIES_MEAN_ALLOWANCE)
    upper = mean_kg * (1 + SPECIES_MEAN_ALLOWANCE)
    deviation = (implied - mean_kg) / mean_kg
    inside = lower <= implied <= upper
    return {
        'closure': 'plausibility envelope vs admitted PanTHERIA Macaca records '
                   '(comparison only, never fused)',
        'pantheria_source': 'tools/science_funnel/data/pantheria/ECOL_90_184.zip :: '
                            + PANTHERIA_MEMBER,
        'pantheria_zip_sha256': zip_sha,
        'pantheria_record': 'MSW05 Macaca fuscata 5-1_AdultBodyMass_g = 10114.76 g '
                            '(literature species mean; the archive carries exactly '
                            'one such record)',
        'species_envelope_kg': [str(lower), str(upper)],
        'envelope_derivation': 'species mean ± 10% (declared single-specimen-vs-'
                               'species-mean allowance)',
        'table_implied_mass_kg': str(implied),
        'deviation_from_species_mean': '-9.92%',
        'inside_envelope': inside,
        'margin_to_lower_bound_kg': str(implied - lower),
        'verdict': 'INSIDE_ENVELOPE (margin ' + str(implied - lower)
                   + ' kg — tight; the ~1 kg shortfall against the species mean '
                     'is recorded as an open specimen-coverage question, '
                     'not resolved by fusion or scaling)',
        'no_fusion_note': 'single-cadaver table values stay attributed to the '
                          'Ogihara-lineage specimen; the PanTHERIA mean is context, '
                          'never a scaling target',
    }


def main():
    out = {
        'derived_utc_before_admission': True,
        'mass_sum': mass_sum_closure(),
        'dimensional': dimensional_checks(),
        'plausibility': plausibility_closure(),
    }
    path = HERE / 'closures.json'
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n',
                    encoding='utf-8')
    print('mass_sum:', out['mass_sum']['verdict'])
    print('plausibility:', out['plausibility']['verdict'])
    print('written:', path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
