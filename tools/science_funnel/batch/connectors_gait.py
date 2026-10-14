"""INTAKE-GAIT lane connectors (auto-loaded by batch.connectors).

Three connectors, one lane (2026-09-17):
  janisch_wildprimate_kin -- Janisch et al. 2024 wild primate limb joint
    kinematics (figshare, CC BY 4.0): 387 stride rows x 14 species, admitted
    as per-stride observation records; the cercopithecoid rows are the
    macaque-analog quadrupedal reference.
  granatosky_gait -- Wimberly/Slater/Granatosky tetrapod gait database
    (Dryad, CC0): analytic-table identities pinned from the API v2 file list;
    the 2.1 GB Gait_Videos.zip is excluded by intake policy; file bytes
    DEFERRED (bearer-token 401 + Anubis bot wall, evidence pinned).
  higurashi_gait -- Higurashi & Kumakura Japanese macaque gait (Dryad, CC0):
    same deferral shape; Dataset_macaque-gait.xlsx digest pinned for the
    future token-enabled download.

Pins resolve at load time from each data dir's download_receipt.json; the
class contracts these connectors map to live in the authored class-contract
store (batch.observation.janisch_stride, batch.deferred.dryad_file).
"""
from .. import adapters_gait  # noqa: F401  (registers lane adapter names)
from .connectors import _artifacts, _pins

_jan_receipt, _jan_pins = _pins('janisch_kinematics')
_gran_receipt, _gran_pins = _pins('dryad_granatosky')
_hig_receipt, _hig_pins = _pins('dryad_higurashi')

_DEFERRAL = {
    'cause': 'Dryad scripted download requires a free bearer token (API answers 401 '
             '"Unauthorized, must have current bearer token"); website file_stream URLs '
             'sit behind an Anubis bot challenge; no Dryad account can be registered '
             'from this agent and browser download is unavailable to it',
    'evidence': 'first-hand 401 and Anubis-challenge bodies pinned as artifacts in '
                'this connector data dir (probe_evidence records every attempt)',
    'probed_utc': '2026-09-17T00:00:00+00:00',
}

CONNECTORS = {
    'janisch_wildprimate_kin': {
        'connector_id': 'janisch_wildprimate_kin',
        'mode': 'admit',
        'data_dir': 'janisch_kinematics',
        'adapter': 'janisch_strides',
        'source': {
            'id': 'janisch.wildprimate_kinematics',
            'release': 'figshare article 23231366 v1 (published 2023-05-26); CSV bytes '
                       'downloaded via direct ndownloader and sha256-verified 2026-09-17',
            'url': 'https://figshare.com/articles/dataset/_/23231366',
            'license': 'CC BY 4.0 (figshare API license field)',
            'known_gaps': ['one all-NA row (file line 28) quarantines by design, never admits',
                           'joint-angle conventions are defined by the source R code, '
                           'which is not machine-pinned by this connector',
                           'phylogenetic eigenvectors PE_1..13 omitted (derivable from '
                           'the pinned consensus tree nexus attachment)',
                           'no macaque species in the sample; the quadrupedal '
                           'cercopithecoids (Papio, Chlorocebus, Cercopithecus, '
                           'Lophocebus) are the macaque analog'],
        },
        'artifacts': _artifacts('janisch_kinematics', [
            ('wildprimate_kin.csv', 'data'),
            ('figshare_23231366_api.json', 'attachment'),
            ('consensusTree_10kTrees_Primates_Version3.nex', 'attachment'),
        ], _jan_pins),
        'constants': {
            'species_vocabulary': [
                'Alouatta_palliata', 'Cebus_capucinus', 'Cercopithecus_lhoesti',
                'Chlorocebus_aethiops', 'Eulemur_rubriventer', 'Eulemur_rufifrons',
                'Hapalemur_aureus', 'Lagothrix_lagotricha', 'Lemur_catta',
                'Lophocebus_albigena', 'Papio_anubis', 'Piliocolobus_badius',
                'Plecturocebus_discolor', 'Saimiri_sciureus',
            ],
            'expected_stride_rows': 387,
        },
        'classes': {'entity': 'batch.observation.janisch_stride'},
    },
    'granatosky_gait': {
        'connector_id': 'granatosky_gait',
        'mode': 'admit',
        'data_dir': 'dryad_granatosky',
        'adapter': 'dryad_files_meta',
        'source': {
            'id': 'dryad.z08kprrd5',
            'release': 'Dryad version 3 (files_changed, published 2021-08-06); API v2 '
                       'dataset + version file list pinned 2026-09-17; file bytes deferred',
            'url': 'https://datadryad.org/dataset/doi:10.5061/dryad.z08kprrd5',
            'license': 'CC0 1.0 (Dryad API v2 dataset record license field)',
            'known_gaps': ['file bytes not downloaded (deferral cause on every record); '
                           'Dryad-declared sha-256 digests are API claims, unverified '
                           'by download',
                           'Gait_Videos.zip (2.1 GB) excluded by intake policy; only its '
                           'identity is admitted',
                           'row-level primate coverage of mammal_gait.txt unverified '
                           '(requires the deferred bytes)'],
        },
        'artifacts': _artifacts('dryad_granatosky', [
            ('granatosky_files.json', 'data'),
            ('granatosky_dataset.json', 'attachment'),
            ('dryad_api_401_evidence.json', 'attachment'),
            ('dryad_anubis_challenge.html', 'attachment'),
            ('probe_evidence.json', 'attachment'),
        ], _gran_pins),
        'constants': {
            'dataset_sha256': _gran_pins['granatosky_dataset.json']['sha256'],
            'exclude_paths': ['Gait_Videos.zip'],
            'deferral': dict(_DEFERRAL),
        },
        'classes': {'entity': 'batch.deferred.dryad_file'},
    },
    'higurashi_gait': {
        'connector_id': 'higurashi_gait',
        'mode': 'admit',
        'data_dir': 'dryad_higurashi',
        'adapter': 'dryad_files_meta',
        'source': {
            'id': 'dryad.fj6q573tc',
            'release': 'Dryad version 4 (metadata_changed, published 2021-07-30); API v2 '
                       'dataset + version file list pinned 2026-09-17; file bytes deferred',
            'url': 'https://datadryad.org/dataset/doi:10.5061/dryad.fj6q573tc',
            'license': 'CC0 1.0 (Dryad API v2 dataset record license field)',
            'known_gaps': ['file bytes not downloaded (deferral cause on every record); '
                           'Dryad-declared sha-256 digests are API claims, unverified '
                           'by download',
                           'gait.xlsx contents (2 Japanese macaques, terrestrial + pole) '
                           'await the token-enabled download'],
        },
        'artifacts': _artifacts('dryad_higurashi', [
            ('higurashi_files.json', 'data'),
            ('higurashi_dataset.json', 'attachment'),
            ('dryad_api_401_evidence.json', 'attachment'),
            ('dryad_api_dataset401_evidence.json', 'attachment'),
            ('dryad_anubis_challenge.html', 'attachment'),
            ('probe_evidence.json', 'attachment'),
        ], _hig_pins),
        'constants': {
            'dataset_sha256': _hig_pins['higurashi_dataset.json']['sha256'],
            'exclude_paths': [],
            'deferral': dict(_DEFERRAL),
        },
        'classes': {'entity': 'batch.deferred.dryad_file'},
    },
}
