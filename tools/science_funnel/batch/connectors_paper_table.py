"""INTAKE-PAPER-TABLE lane connectors (2026-09-18). Auto-loaded by
connectors.py's lane-module convention (connectors_*.py exporting
CONNECTORS_LANE). The adapter lives in tools/science_funnel/adapters_paper_table.py
and registers itself into the shared ADAPTERS registry at import; adapters.py
itself is owned by another lane and is not edited here."""
from .. import adapters_paper_table  # noqa: F401  (registers the adapter)
from .connectors import _artifacts, _pins

_table_receipt, _table_pins = _pins('oku_paper_table')

CONNECTORS_LANE = {
    'oku_paper_table': {
        'connector_id': 'oku_paper_table',
        'mode': 'admit',
        'data_dir': 'oku_paper_table',
        'adapter': 'oku_paper_table',
        'source': {
            'id': 'oku2021.paper_table_inertial',
            'release': 'Oku, Ide & Ogihara 2021 (Commun Biol 4:1831, DOI '
                       '10.1038/s42003-021-01831-w), Table 1 "Dimensions and '
                       'inertial parameters of the limb segments", pinned '
                       '2026-09-18 as the article full text (PMC version of '
                       'record) via the EuropePMC fullTextXML endpoint; '
                       'nature.com/tables/1 does not serve authlessly (bot '
                       'wall, recorded)',
            'url': 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7940622/fullTextXML',
            'license': 'CC BY 4.0 ((c) The Author(s) 2021, Communications '
                       'Biology; license sentence quoted verbatim from the '
                       'pinned page and carried on every record)',
            'known_gaps': [
                'forelimbs are folded into HAT in this table (structural; '
                'never patched)',
                'whole-body mass not published; implied mass is the '
                'five-segment sum (9.111 kg ±0.0025 kg rounding)',
                'single adult male cadaver (Ogihara 2009 lineage); no '
                'population variance, no uncertainty columns',
                'inertia about the segment COM per the table footnote; axial '
                'vs transverse axis distinction not published',
                'foot and phalangeal rows recalculated by the authors from '
                'CT-scanned surface data (per the table footnote)',
            ],
        },
        'artifacts': _artifacts('oku_paper_table', [
            ('PMC7940622_fulltext.xml', 'data'),
            ('20260917_dbhunt_motion.md', 'attachment'),
        ], _table_pins),
        'classes': {'measurement': 'batch.property.paper_table_inertial'},
    },
}
