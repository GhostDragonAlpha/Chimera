"""INTAKE-MUSCLE lane connectors (2026-09-17). Auto-loaded by connectors.py's
lane-module convention (connectors_*.py exporting CONNECTORS_LANE). The two
adapters live in tools/science_funnel/adapters_muscle.py and register
themselves into the shared ADAPTERS registry at import; adapters.py itself is
owned by another lane and is not edited here."""
from .. import adapters_muscle  # noqa: F401  (registers the two adapters)
from .connectors import _artifacts, _pins

_guim_receipt, _guim_pins = _pins('guimaraes_arch')
_oku_receipt, _oku_pins = _pins('oku_bipedal')

CONNECTORS_LANE = {
    'guimaraes_arch': {
        'connector_id': 'guimaraes_arch',
        'mode': 'admit',
        'data_dir': 'guimaraes_arch',
        'adapter': 'guimaraes_arch',
        'source': {
            'id': 'guimaraes2026.hindlimb_architecture',
            'release': 'S1 dissection dataset snapshot-pinned 2026-09-17 via the '
                       'EuropePMC supplementaryFiles endpoint (PMC13425262); the zip '
                       'container is repackaged per request, so pins are member sha256',
            'url': 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13425262/supplementaryFiles',
            'license': 'CC BY 4.0 ((c) 2026 The Author(s), Wiley Periodicals LLC; '
                       'license line pinned in the full-text XML attachment)',
            'known_gaps': [
                'one specimen per species (Macaca mulatta = 127, KU Leuven, right limb)',
                'six species in S1, not the nine of the paper text (human rows come '
                'from Charles 2019 DTI and are not in this file)',
                'pennation present only for the 19 homologous muscles of the 217-'
                'observation subset',
                'sheet headers declare m/kg on columns whose values are mm/g; '
                'recorded on every affected record, resolved only by the row-level '
                'PCSA closure law',
                'rows failing the dataset\'s own closure identities (PCSA = m/(rho*FL), '
                'muscle = belly + tendon) quarantine whole, visibly',
            ],
        },
        'artifacts': _artifacts('guimaraes_arch', [
            ('AJPA-190-e70329-s001.xlsx', 'data'),
            ('AJPA-190-e70329-s002.docx', 'attachment'),
            ('PMC13425262_fulltext.xml', 'attachment'),
        ], _guim_pins),
        'classes': {'measurement': 'batch.property.measurement'},
    },
    'oku_bipedal': {
        'connector_id': 'oku_bipedal',
        'mode': 'admit',
        'data_dir': 'oku_bipedal',
        'adapter': 'oku_bipedal_series',
        'source': {
            'id': 'oku2021.bipedal_series',
            'release': 'Supplementary Data 1 (MOESM2 xlsx) snapshot-pinned 2026-09-17 '
                       'via the EuropePMC supplementaryFiles endpoint (PMC7940622); '
                       'member sha256 pinned (the task brief named PMC8134959, an '
                       'unrelated paper; corrected per the dbhunt dossier C7)',
            'url': 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7940622/supplementaryFiles',
            'license': 'CC BY 4.0 ((c) The Author(s) 2021, Communications Biology; '
                       'license line pinned in the full-text XML attachment)',
            'known_gaps': [
                'simulation output trajectories of a planar nine-link model, not '
                'biological measurement',
                'the two column blocks are unlabelled in the sheet; before/after '
                'alteration roles follow the Fig. 4 caption line order and carry '
                'that basis on every record',
                'sheets are named Fig3ABC/Fig3D while their panels match the Fig. 4 '
                'caption (angles, GRFs, moments, forces)',
                'x axis is integer percent of gait cycle; sub-percent timing absent',
                'no per-sample uncertainty published',
            ],
        },
        'artifacts': _artifacts('oku_bipedal', [
            ('42003_2021_1831_MOESM2_ESM.xlsx', 'data'),
            ('42003_2021_1831_MOESM1_ESM.pdf', 'attachment'),
            ('PMC7940622_fulltext.xml', 'attachment'),
        ], _oku_pins),
        'classes': {'series': 'batch.property.series'},
    },
}
