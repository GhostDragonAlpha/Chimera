"""Life-science lane connectors (2026-09-17, intake-life). Auto-merged into
batch/connectors.CONNECTORS by the connectors_* convention. Artifact pins
resolve ONLY from each data directory's download_receipt.json -- written by
tools/science_funnel/life_fetch.py (idempotent, byte-pinned); nothing is
hardcoded here."""
from . import connectors as C

_pan_receipt, _pan_pins = C._pins('pantheria')
_tax_receipt, _tax_pins = C._pins('ncbi_taxdmp')
_rhea_receipt, _rhea_pins = C._pins('rhea')

CONNECTORS = {
    'pantheria_1_0': {
        'connector_id': 'pantheria_1_0',
        'mode': 'admit',
        'data_dir': 'pantheria',
        'adapter': 'pantheria_traits',
        'source': {
            'id': 'pantheria.1.0.wr05',
            'release': 'PanTHERIA 1.0 WR05 Aug2008, figshare 3531875 '
                       '(ECOL_90_184.zip), pinned 2026-09-17',
            'url': 'https://ndownloader.figshare.com/files/5604752',
            'license': 'CC0 (figshare API license field, probe-verified 2026-09-17)',
            'known_gaps': ['BMR measured 573/5,416 rows; adult mass 3,542',
                           'sentinels (-999) are nodata, never measurements',
                           'BMR->W assumes 20.1 J/mL O2 (declared on every record)',
                           'name resolution covers the Macaca subtree only'],
        },
        'artifacts': [
            *C._artifacts('pantheria', [('ECOL_90_184.zip', 'data')], _pan_pins),
            *C._artifacts('ncbi_taxdmp', [('macaca_names.tsv', 'attachment')], _tax_pins),
        ],
        'constants': {'o2_calorific_J_per_mL': 20.1,
                      'macaca_names_sha256': _tax_pins['macaca_names.tsv']['sha256']},
        'classes': {'entity': 'batch.entity.pantheria_species',
                    'measurement': 'batch.property.pantheria_trait'},
    },
    'ncbi_taxdmp_macaca': {
        'connector_id': 'ncbi_taxdmp_macaca',
        'mode': 'admit',
        'data_dir': 'ncbi_taxdmp',
        'adapter': 'ncbi_taxdmp_macaca',
        'source': {
            'id': 'ncbi.taxdmp.macaca',
            'release': 'taxdmp.zip 2026-09-17, 79,535,405 bytes, md5-verified; '
                       'Macaca subtree (43 taxa under genus tax_id 9539) derived '
                       'deterministically by life_fetch',
            'url': 'https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdmp.zip',
            'license': 'public domain (US Government work, 17 USC 105)',
            'known_gaps': ['Macaca subtree only, never all taxa',
                           'zip exceeds the 64MB bundle limit; bundles pin the '
                           'derived TSVs, the receipt pins the zip'],
        },
        'artifacts': [
            *C._artifacts('ncbi_taxdmp', [('macaca_nodes.tsv', 'data'),
                                          ('macaca_names.tsv', 'attachment')],
                          _tax_pins),
        ],
        'constants': {'macaca_names_sha256': _tax_pins['macaca_names.tsv']['sha256']},
        'classes': {'entity': 'batch.entity.ncbi_taxon'},
    },
    'rhea_reactions': {
        'connector_id': 'rhea_reactions',
        'mode': 'admit',
        'data_dir': 'rhea',
        'adapter': 'rhea_chebi_smiles',
        'source': {
            'id': 'rhea.chebi_smiles.tsv',
            'release': 'Rhea release 142 (2026-09-02), per pinned '
                       'rhea-release.properties',
            'url': 'https://ftp.expasy.org/databases/rhea/tsv/rhea-chebi-smiles.tsv',
            'license': 'CC BY 4.0; LICENSE.txt pinned in-bundle; attribution: '
                       'Rhea database, Swiss Institute of Bioinformatics',
            'known_gaps': ['participant species map, not the reaction list',
                           'competing-SMILES ids quarantine, never merge',
                           'SMILES are pinned bytes, not validated structures'],
        },
        'artifacts': [
            *C._artifacts('rhea', [('rhea-chebi-smiles.tsv', 'data'),
                                   ('LICENSE.txt', 'attachment'),
                                   ('rhea-release.properties', 'attachment')],
                          _rhea_pins),
        ],
        'classes': {'entity': 'batch.entity.rhea_chebi_species'},
    },
}

# Data dirs the reprove blob index must see so these admissions stay
# re-provable by recorded-producer replay in later runs.
SEARCH_DIRS = ['pantheria', 'ncbi_taxdmp', 'rhea']
