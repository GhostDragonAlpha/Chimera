"""LOCAL-REFERENCES-INTAKE lane connectors (2026-09-18). Auto-loaded by
connectors.py's lane-module convention (connectors_*.py exporting
CONNECTORS_LANE). The three adapters live in
tools/science_funnel/adapters_local_refs.py and register themselves via
LOCAL_REFS_ADAPTERS; adapters.py itself is owned by another lane and is not
edited here.

All artifacts are REPO-RESIDENT research_references/human/ files: the data dirs
carry a copy-in with the committed (LF) bytes and the download receipt records
source 'repo-resident research_references/human/...' -- no URL is invented,
none is needed. Derivations are by tools/science_funnel/derive_local_refs_*.py
(idempotent, Rule-1-recorded rules; the anchors gate the ANSUR derivation).
"""
from .. import adapters_local_refs  # noqa: F401  (registers the three adapters)
from .connectors import _artifacts, _pins

_ansur_receipt, _ansur_pins = _pins('ansur2_derived_20260918')
_mocap_receipt, _mocap_pins = _pins('mocap_walk_series_20260918')
_doc_receipt, _doc_pins = _pins('muscle_inventory_doc_20260918')

ANSUR_SOURCE_TEXT = (
    'US Army Anthropometric Survey 2012 (ANSUR II), public release 2017 via the '
    'Penn State OPEN Design Lab; repo-resident mirror '
    'research_references/human/ANSUR_II_{MALE,FEMALE}_Public.csv (4,082 male + '
    '1,986 female subjects, 93 measures; cp1252). SOURCES.md, verbatim: '
    '"DOWNLOADED (mirror of the Penn State OPEN Design Lab release; US Gov work, '
    'public since 2017)". Sources.md grants no person-level redistribution, so '
    'admission is AGGREGATE ONLY; the raw rows stay repo-resident and enter the '
    'membrane only as pinned bytes of the derived tables (a recorded '
    'redistribution grant would falsify that decision).')

MOCAP_SOURCE_TEXT = (
    'CMU MoCap subject 35 walk trial 35_01 via the una-dinosauria BVH mirror; '
    'repo-resident derived reference research_references/human/'
    'mocap_walk_reference.json (120 fps, 359 frames, mean gait-cycle curves over '
    '4 cycles; the raw-unit scale was measured by that file against the ANSUR II '
    'male median trochanterion height). License per SOURCES.md: free for '
    'research AND commercial inclusion; may not resell the data itself; credit '
    'mocap.cs.cmu.edu + NSF EIA-0196217.')

DOC_SOURCE_TEXT = (
    'Repository-authored MUSCLE_INVENTORY.md (2026-07-31, myo_sim ground truth; '
    'cites Neumann, Ward 2009, Rajagopal 2016, Saul 2015, Christophy 2012, '
    'Caggiano 2022). Admitted as ONE documentation-reference entity pinned by '
    'sha256 -- a citation, never measurements.')

CONNECTORS_LANE = {
    'ansur2_derived_20260918': {
        'connector_id': 'ansur2_derived_20260918',
        'mode': 'admit',
        'data_dir': 'ansur2_derived_20260918',
        'adapter': 'ansur2_aggregates',
        'source': {
            'id': 'ansur2.derived_aggregates_20260918',
            'release': 'deterministic per-sex derived tables (columns and unit '
                       'laws = the existing anchors\' own derivation), built '
                       '2026-09-18 by tools/science_funnel/'
                       'derive_local_refs_ansur.py; anchors verified to 1e-9',
            'url': 'repo-resident research_references/human/ANSUR_II_MALE_Public.csv '
                   '+ ANSUR_II_FEMALE_Public.csv (no download; copy-in of committed '
                   'bytes)',
            'license': 'US Government work (17 USC 105), public release 2017 via '
                       'Penn State OPEN Design Lab; no person-level redistribution '
                       'grant recorded -- aggregate-only admission (see SOURCES.md '
                       'and the work record)',
            'known_gaps': [
                'person-level rows never admitted; aggregate-only is a recorded '
                'falsifiable decision',
                '2012 military population; not a civilian sample',
                'margins in the derived tables are derived, not directly measured',
                'the anchors\' percentile law is an order-statistic, not an '
                'interpolated percentile',
            ],
        },
        # ONE data artifact (the adapter is run once per data artifact); the
        # female table, the mocap siblings and the raw CSVs ride as pinned
        # attachments (the bp3d companion pattern).
        'artifacts': _artifacts('ansur2_derived_20260918', [
            ('ansur2_male_derived.csv', 'data'),
            ('ansur2_female_derived.csv', 'attachment'),
            ('ANSUR_II_MALE_Public.csv', 'attachment'),
            ('ANSUR_II_FEMALE_Public.csv', 'attachment'),
        ], _ansur_pins),
        'constants': {'female_derived_sha256':
                      _ansur_pins['ansur2_female_derived.csv']['sha256']},
        'classes': {'measurement': 'batch.property.measurement'},
    },
    'mocap_walk_series_20260918': {
        'connector_id': 'mocap_walk_series_20260918',
        'mode': 'admit',
        'data_dir': 'mocap_walk_series_20260918',
        'adapter': 'mocap_walk_series',
        'source': {
            'id': 'cmu.mocap.subject35.walk',
            'release': 'mean gait-cycle curves derived 2026-09-18 by '
                       'tools/science_funnel/derive_local_refs_mocap_doc.py from '
                       'the repo-resident reference file (101 samples, n_cycles=4 '
                       'per curve)',
            'url': 'repo-resident research_references/human/mocap_walk_reference.json '
                   '(no download; copy-in of committed bytes)',
            'license': 'CMU MoCap: free for research AND commercial inclusion; may '
                       'not resell the data itself; credit mocap.cs.cmu.edu + NSF '
                       'EIA-0196217',
            'known_gaps': [
                'mean over 4 cycles, not per-cycle data',
                'source degrees rounded to 2 decimal places',
                'BVH raw-unit scale was measured, not documented, by the source file',
                'one subject, one speed (1.285 m/s); not a population norm',
            ],
        },
        'artifacts': _artifacts('mocap_walk_series_20260918', [
            ('mocap_cmus35_walk_hip_mean_cycle.csv', 'data'),
            ('mocap_cmus35_walk_knee_mean_cycle.csv', 'attachment'),
            ('mocap_cmus35_walk_ankle_mean_cycle.csv', 'attachment'),
            ('mocap_walk_reference.json', 'attachment'),
        ], _mocap_pins),
        'constants': {
            'knee_curve_sha256': _mocap_pins['mocap_cmus35_walk_knee_mean_cycle.csv']['sha256'],
            'ankle_curve_sha256': _mocap_pins['mocap_cmus35_walk_ankle_mean_cycle.csv']['sha256'],
            'spatiotemporal_scalars': _mocap_receipt['series']['scalars_carried_on_records'],
            'conventions_verbatim': _mocap_receipt['series']['conventions_verbatim'],
        },
        'classes': {'series': 'batch.property.series'},
    },
    'muscle_inventory_doc_20260918': {
        'connector_id': 'muscle_inventory_doc_20260918',
        'mode': 'admit',
        'data_dir': 'muscle_inventory_doc_20260918',
        'adapter': 'muscle_inventory_doc',
        'source': {
            'id': 'chimera.muscle_inventory_doc',
            'release': 'repository-authored document, committed LF bytes pinned '
                       '2026-09-18 (sha256 in the connector constants and the work '
                       'record)',
            'url': 'repo-resident research_references/human/MUSCLE_INVENTORY.md '
                   '(no download; copy-in of committed bytes)',
            'license': 'repository-authored; cites published kinesiology sources '
                       '(Neumann; Ward et al. 2009; Rajagopal et al. 2016; Saul '
                       'et al. 2015; Christophy et al. 2012; Caggiano et al. 2022)',
            'known_gaps': [
                'prose document admitted as a citation entity, never reified into '
                'measurement records',
                'muscle role text is not machine-parsed',
            ],
        },
        'artifacts': _artifacts('muscle_inventory_doc_20260918', [
            ('MUSCLE_INVENTORY.md', 'data'),
        ], _doc_pins),
        'constants': {'muscle_inventory_sha256':
                      _doc_pins['MUSCLE_INVENTORY.md']['sha256']},
        'classes': {'entity': 'batch.entity.external'},
    },
}
