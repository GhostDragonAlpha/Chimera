"""Digit-for-digit verification of the banked Oku/Ide/Ogihara 2021 Table 1
values against the live page.

The live page is the article's PMC version of record, served authlessly by
EuropePMC (nature.com serves a JavaScript client-challenge page to non-browser
fetchers; that refusal is recorded in the fetch log, not worked around).
Every banked value must match the page digit-for-digit; any mismatch lists the
cell with a cause and the lane refuses admission until resolved.

Run:  python -B tools/creature_graph/validation/batch_paper_inertia_20260918/verify_live_table.py
Writes verification.json next to this script. Exit 2 on any mismatch.
"""
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
LANE = HERE.parents[3]
XML = LANE / 'tools' / 'science_funnel' / 'data' / 'oku_paper_table' / 'PMC7940622_fulltext.xml'
DOSSIER = LANE / 'tools' / 'science_funnel' / 'data' / 'oku_paper_table' / '20260917_dbhunt_motion.md'

# Banked in the lane dispatch (thread 4, PAPER-TABLE-INERTIA-INTAKE) from the
# Oku/Ide/Ogihara 2021 probe; the live page is the admission authority.
# order: segment -> (mass_kg, length_m, com_percent, inertia_kgm2_written)
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
LICENSE_SNIPPET = ('This article is licensed under a Creative Commons '
                   'Attribution 4.0 International License')


def _text(el):
    if el is None:
        return ''
    return ''.join(el.itertext())


def extract_table(xml_path):
    """Return the inertial-parameters <table-wrap> (id Tab1/T1 in this
    article's markup) parsed as caption, footnotes and rows of cell strings
    (digit strings exactly as published)."""
    import re
    root = ET.parse(xml_path).getroot()
    wrap = next((t for t in root.iter('table-wrap')
                 if re.fullmatch(r'(tab)?\s*1', (t.get('id') or ''),
                                 re.IGNORECASE)), None)
    if wrap is None:
        raise SystemExit('inertial-parameters table-wrap (Tab1/T1) not found '
                         'in the pinned XML')
    caption_el = wrap.find('caption')
    label = _text(caption_el.find('label'))
    title = _text(caption_el.find('title'))
    notes = [_text(n) for n in wrap.iter('table-wrap-foot')]
    rows = []
    for tr in wrap.iter('tr'):
        cells = [_text(td).strip() for td in tr.findall('td')]
        cells += [_text(th).strip() for th in tr.findall('th')]
        if any(cells):
            rows.append(cells)
    return {'label': label.strip(), 'title': title.strip(), 'footnotes': notes,
            'rows': rows}


def normalize_cell(raw):
    """Recorded, identity-preserving normalization of a page cell to the
    banked transcription convention: exponent separator case, U+2212 minus
    sign, and exponent zero-padding. The mantissa digits are never touched."""
    cell = raw.strip().replace('\u2212', '-').replace('E', 'e')
    if 'e' in cell:
        mantissa, exponent = cell.split('e', 1)
        sign = '-' if exponent.startswith('-') else ''
        digits = exponent.lstrip('+-').lstrip('0') or '0'
        cell = mantissa + 'e' + sign + digits
    return cell


def match_banked(table):
    """Locate each segment row and compare its four cells digit-for-digit
    (after the recorded normalization; the raw page cell is kept too)."""
    header, body = None, []
    for cells in table['rows']:
        joined = ' '.join(cells).lower()
        if header is None and (not cells[0].strip()) and 'mass' in joined:
            header = cells
            continue
        if header is not None:
            body.append(cells)
    results, mismatched = [], False
    for segment, banked in BANKED.items():
        row = next((cells for cells in body
                    if SEGMENT_SYNONYMS.get(cells[0].strip().lower()) == segment), None)
        if row is None:
            results.append({'segment': segment, 'status': 'MISSING_ROW',
                            'cause': 'segment row not found under the table header'})
            mismatched = True
            continue
        cells = row[1:5]
        if len(cells) < 4:
            results.append({'segment': segment, 'status': 'SHORT_ROW',
                            'cells': row, 'cause': 'fewer than four value cells'})
            mismatched = True
            continue
        cells = cells[:4]
        normalized = [normalize_cell(c) for c in cells]
        mism = [{'banked': b, 'page_raw': p, 'page_normalized': n}
                for b, p, n in zip(banked, cells, normalized) if b != n]
        results.append({'segment': segment, 'banked': list(banked),
                        'page_raw': cells, 'page_normalized': normalized,
                        'status': 'MATCH' if not mism else 'MISMATCH',
                        'mismatches': mism})
        mismatched = mismatched or bool(mism)
    return results, mismatched, header


def main():
    xml_raw = XML.read_bytes()
    dossier_raw = DOSSIER.read_bytes()
    text = xml_raw.decode('utf-8')
    table = extract_table(XML)
    cells, mismatched, header = match_banked(table)
    license_ok = LICENSE_SNIPPET in text
    license_ref = ('https://creativecommons.org/licenses/by/4.0/' in text)

    out = {
        'artifact': 'tools/science_funnel/data/oku_paper_table/PMC7940622_fulltext.xml',
        'artifact_sha256': hashlib.sha256(xml_raw).hexdigest(),
        'banked_dossier': 'docs/research/20260917_dbhunt_motion.md (pinned copy)',
        'banked_dossier_sha256': hashlib.sha256(dossier_raw).hexdigest(),
        'table_label': table['label'],
        'table_title': table['title'],
        'table_header': header,
        'table_footnotes': table['footnotes'],
        'cells': cells,
        'normalization': ('exponent separator case (E->e), U+2212 -> ASCII minus, '
                          'exponent zero-padding stripped; mantissa digits untouched'),
        'caption_title_in_xml': ('Dimensions and inertial parameters of the limb '
                                 'segments' in text),
        'license_sentence_verified': license_ok,
        'license_ref_verified': license_ref,
        'license_quote': ('Open Access ' + LICENSE_SNIPPET + ', which permits use, '
                          'sharing, adaptation, distribution and reproduction in any '
                          'medium or format, as long as you give appropriate credit '
                          'to the original author(s) and the source, provide a link '
                          'to the Creative Commons license, and indicate if changes '
                          'were made.'),
        'mismatched': mismatched,
        'verdict': 'CLOSED' if (not mismatched and license_ok and license_ref)
                   else 'QUARANTINED',
    }
    path = HERE / 'verification.json'
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n',
                    encoding='utf-8')
    for row in cells:
        print(row.get('segment'), row.get('status'),
              row.get('mismatches') or '')
    print('license:', out['license_sentence_verified'], out['license_ref_verified'])
    print('verdict:', out['verdict'])
    print('written:', path)
    return 2 if out['verdict'] != 'CLOSED' else 0


if __name__ == '__main__':
    sys.exit(main())
