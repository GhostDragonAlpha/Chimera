"""INTAKE-PAPER-TABLE lane adapters (2026-09-18). One CC BY 4.0 source admitted
through the batch connector machinery:

  oku_paper_table     Oku, Ide & Ogihara 2021 (Commun Biol 4:1831, DOI
                      10.1038/s42003-021-01831-w), Table 1 "Dimensions and
                      inertial parameters of the limb segments" for a single
                      adult male Japanese macaque cadaver (Ogihara 2009
                      lineage) -- one measurement record per
                      (segment, quantity) plus one table-summary record.

The pinned artifact is the article's full text (PMC version of record,
EuropePMC fullTextXML); nature.com does not serve the tables page authlessly
(bot wall, recorded in the data dir receipt). The table lives as
<table-wrap id="T1"> markup inside that XML; parsing is stdlib-only
(xml.etree).

Identity law: every cell is re-checked digit-for-digit against the banked
transcription (BANKED below) after one recorded normalization (exponent
separator case, U+2212 minus, exponent zero-padding; mantissa digits never
touched). A cell that does not match refuses as digit_mismatch and the row is
quarantined whole -- a corrupted table value can never be admitted quietly.

Closure law: the lane's derived closures (mass-sum identity with the table's
own ±0.0025 kg rounding tolerance, per-quantity unit envelopes, PanTHERIA
species-envelope comparison) are carried on EVERY record as conditions;
they are derived before admission and are never silently resolved here.

Known structural gap (carried, never patched): this table folds the
forelimbs into HAT and publishes no whole-body mass; the implied whole-body
mass is the five-segment sum."""
import xml.etree.ElementTree as ET

from .adapters import ADAPTERS, rejection
from .common import Refusal, number, require
from .units import convert

# Banked transcription (lane dispatch, verified against the live page by
# tools/creature_graph/validation/batch_paper_inertia_20260918/
# verify_live_table.py; per-cell results in verification.json). order:
# mass_kg, length_m, com_percent, inertia_kgm2_written.
BANKED = {
    'HAT':       ('8.184', '0.482', '52', '2.07e-2'),
    'thigh':     ('0.557', '0.163', '41', '1.61e-3'),
    'shank':     ('0.269', '0.182', '40', '7.01e-4'),
    'foot':      ('0.080', '0.074', '62', '5.49e-5'),
    'phalanges': ('0.021', '0.045', '50', '6.26e-6'),
}
SEGMENT_SYNONYMS = {'hat': 'HAT', 'thigh': 'thigh', 'shank': 'shank',
                    'foot': 'foot', 'phalanges': 'phalanges',
                    'phalangeal': 'phalanges'}

LICENSE_QUOTE = ('Open Access This article is licensed under a Creative Commons '
                 'Attribution 4.0 International License, which permits use, '
                 'sharing, adaptation, distribution and reproduction in any '
                 'medium or format, as long as you give appropriate credit to '
                 'the original author(s) and the source, provide a link to the '
                 'Creative Commons license, and indicate if changes were made.')

SPECIMEN_QUALIFIER = ('single adult male Japanese macaque (Macaca fuscata) '
                      'cadaver, Ogihara 2009 lineage; values recalculated for '
                      'the foot and phalangeal segments from CT-scanned '
                      'surface data per the table footnote')

CLOSURE_CONDITIONS = {
    'closure_mass_sum': 'segment masses sum to 9.111 kg = the implied whole-body '
                        'mass; rounding tolerance ±0.0025 kg (5 cells × 0.0005 kg '
                        'at the table\'s stated 0.001 kg precision); the table '
                        'publishes no whole-body mass',
    'closure_dimensional': 'per-quantity unit + envelope checks (mass kg, length m, '
                           'COM dimensionless fraction, I kg*m2) enforced per record',
    'closure_plausibility': 'implied mass 9.111 kg lies INSIDE the declared ±10% '
                            'envelope around the PanTHERIA 1.0 Macaca fuscata '
                            'species mean (10.11476 kg, pinned ECOL_90_184.zip) at '
                            '-9.92% deviation, margin 0.0077160 kg -- tight; the '
                            'shortfall is an open specimen-coverage question, '
                            'comparison only, never fused or scaled',
}

KNOWN_GAPS = [
    'forelimbs are folded into HAT in this table (structural; never patched)',
    'whole-body mass not published; implied mass is the five-segment sum',
    'single cadaver specimen; no population variance, no uncertainty columns',
    'inertia axis basis: about the segment COM per the table footnote; '
    'axial vs transverse axis distinction not published',
    'foot and phalangeal values were recalculated by the authors from '
    'CT-scanned surface data, unlike the other rows (recorded per footnote)',
]


def _normalize_cell(raw):
    """Recorded normalization to the banked transcription convention:
    exponent separator case, U+2212 minus, exponent zero-padding. Mantissa
    digits are never touched."""
    cell = raw.strip().replace('\u2212', '-').replace('E', 'e')
    if 'e' in cell:
        mantissa, exponent = cell.split('e', 1)
        sign = '-' if exponent.startswith('-') else ''
        digits = exponent.lstrip('+-').lstrip('0') or '0'
        cell = mantissa + 'e' + sign + digits
    return cell


def _text(el):
    if el is None:
        return ''
    return ''.join(el.itertext())


def _table_rows(raw):
    """The pinned full text must carry exactly one <table-wrap> whose id is
    the inertial-parameters table (Tab1/T1 in this article's markup) and
    whose caption names it; return its segment rows."""
    root = ET.fromstring(raw)
    import re
    wraps = [t for t in root.iter('table-wrap')
             if re.fullmatch(r'(tab)?\s*1', (t.get('id') or ''), re.IGNORECASE)]
    require(len(wraps) == 1, 'table_wrap_unexpected', str(len(wraps)))
    require('inertial parameters' in _text(wraps[0]).lower(),
            'table_caption_changed', 'Tab1')
    header, body = None, []
    for tr in wraps[0].iter('tr'):
        cells = [_text(td).strip() for td in tr.findall('td')]
        cells += [_text(th).strip() for th in tr.findall('th')]
        if not any(cells):
            continue
        joined = ' '.join(cells).lower()
        if header is None and not cells[0].strip() and 'mass' in joined:
            require('length' in joined and 'com' in joined, 'table_header_changed',
                    joined)
            header = cells
            continue
        if header is not None:
            body.append(cells)
    require(header is not None, 'table_header_missing', 'T1')
    require(len(body) == 5, 'segment_row_count_unexpected', str(len(body)))
    return body


# quantity -> (unit as published, quantity key for the SI table, envelope)
QUANTITY_SPECS = {
    'mass':    ('kg', 'mass', 1e-4, 50.0),
    'length':  ('m', 'length', 0.005, 5.0),
    'com':     ('percent', 'dimensionless', 0.0, 1.0),
    'inertia': ('kg*m2', 'moment_of_inertia', 1e-8, 1.0),
}
QUANTITY_LABEL = {'mass': 'mass', 'length': 'length',
                  'com': 'COM position (fraction of segment length from the '
                         'proximal end, per table footnote)',
                  'inertia': 'moment of inertia about the COM (per table footnote)'}


def oku_paper_table(raw, manifest, path):
    """The pinned article full text -> 20 measurement records (one per
    segment x quantity) + 1 table-summary record. A corrupted segment row
    quarantines exactly that row (and, dependently, the summary); every
    other row still admits, visibly."""
    del manifest  # connector constants are unused; the receipt carries the pins
    rows = _table_rows(raw)
    out = []
    seen, verified_masses = {}, []
    for cells in rows:
        segment = SEGMENT_SYNONYMS.get(cells[0].strip().lower())
        location = 'table1:' + (cells[0].strip() or '?')
        try:
            require(segment is not None, 'segment_row_unexpected', cells[0])
            require(segment not in seen, 'duplicate_segment_row', segment)
            seen[segment] = True
            banked = BANKED[segment]
            published = dict(zip(('mass', 'length', 'com', 'inertia'), banked))
            values = {}
            for slot, raw_cell in zip(('mass', 'length', 'com', 'inertia'),
                                      cells[1:5]):
                normalized = _normalize_cell(raw_cell)
                require(normalized == banked[len(values)], 'digit_mismatch',
                        f'{segment} slot {slot}: banked {banked[len(values)]!r} vs '
                        f'page {normalized!r} (raw {raw_cell!r})')
                values[slot] = number(normalized)
            verified_masses.append(values['mass'])
            for slot, (unit, quantity, lo, hi) in QUANTITY_SPECS.items():
                payload = convert(values[slot], unit, quantity)
                require(lo <= payload['value_si'] <= hi, 'envelope_violation',
                        f'{segment}:{slot}')
                payload.update(
                    subject='Macaca fuscata/' + segment,
                    conditions={
                        'species': 'Macaca fuscata (Japanese macaque)',
                        'specimen': SPECIMEN_QUALIFIER,
                        'paper': 'Oku, Ide & Ogihara 2021, Communications Biology '
                                 '4:1831, DOI 10.1038/s42003-021-01831-w, Table 1',
                        'license_quote': LICENSE_QUOTE,
                        'table_cell': {'segment': segment,
                                       'published': published[slot],
                                       'precision_note': 'values as published; the '
                                                         'table rounds mass to 0.001 kg'},
                        'basis': QUANTITY_LABEL[slot],
                        **CLOSURE_CONDITIONS,
                    },
                    source_field=slot,
                    parameter=('segment_' + slot if slot in ('mass', 'length')
                               else ('segment_com_fraction' if slot == 'com'
                                     else 'segment_moment_of_inertia')),
                )
                out.append(draft_paper_row(f'oku2021.table1:{segment}:{slot}',
                                           payload,
                                           f'Oku 2021 Table 1 {segment} {slot}'))
        except Refusal as exc:
            out.append(rejection(location, exc))

    # Table-summary record: the implied whole-body mass with the closure
    # block. It admits only when all five published masses verified
    # digit-for-digit; otherwise it is quarantined as dependent.
    if len(verified_masses) == 5:
        implied = sum(verified_masses)
        payload = convert(implied, 'kg', 'mass')
        payload.update(
            subject='Macaca fuscata/whole_body_implied',
            conditions={
                'species': 'Macaca fuscata (Japanese macaque)',
                'specimen': SPECIMEN_QUALIFIER,
                'paper': 'Oku, Ide & Ogihara 2021, Communications Biology 4:1831, '
                         'DOI 10.1038/s42003-021-01831-w, Table 1',
                'license_quote': LICENSE_QUOTE,
                'summary_kind': 'table_summary (implied whole-body mass)',
                'derivation': 'sum of the five published segment masses '
                              '(8.184 + 0.557 + 0.269 + 0.080 + 0.021 kg)',
                'rounding_tolerance_kg': 0.0025,
                'tolerance_derivation': '5 cells x 0.0005 kg at the table\'s stated '
                                        '0.001 kg precision',
                'pantheria_species_mean_kg': 10.11476,
                'pantheria_deviation': '-9.92% (inside the declared ±10% envelope, '
                                       'margin 0.0077160 kg)',
                'known_gaps': list(KNOWN_GAPS),
                **CLOSURE_CONDITIONS,
            },
            source_field='table_summary',
            parameter='whole_body_mass_implied',
        )
        out.append(draft_paper_row('oku2021.table1:summary:implied_mass', payload,
                                   'Oku 2021 Table 1 implied whole-body mass'))
    else:
        out.append(rejection('table1:summary', Refusal(
            'dependent_row_quarantined',
            'summary implied mass withheld; a segment mass row failed '
            'digit-for-digit verification')))
    return out


def draft_paper_row(external_id, payload, label):
    from .common import draft
    row = draft(external_id, 'measurement', payload,
                unknowns=['single_cadaver_no_population_variance',
                          'forelimbs_folded_into_hat_structural_gap',
                          'whole_body_mass_implied_not_published',
                          'inertia_axis_about_com_per_footnote'],
                label=label)
    row['class_contract'] = {'class_id': 'batch.property.paper_table_inertial',
                             'version': 1}
    return row


ADAPTERS['oku_paper_table'] = oku_paper_table
