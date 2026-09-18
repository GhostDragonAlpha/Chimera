"""INTAKE-APPEARANCE lane connectors (auto-loaded by batch.connectors).

Three connectors, one lane (2026-09-18):
  goldenberg_reflectance -- Goldenberg et al. color+NIR reflectance
    replication data (Zenodo 15084543, CC BY 4.0): the only verified
    machine-readable mammal fur optical dataset; plumage + egg summary
    reflectance across 441 taxa of 7 classes (94 Mammalia).
  phylacine_1_2_1 -- PHYLACINE 1.2.1 (CC0, GitHub release): late-Quaternary
    mammal trait table admitted as reference entities from a DERIVED
    deterministic extraction; the 106 MB release zip exceeds the 100 MB git
    per-file ceiling and is pinned by receipt only, never committed.
  usgs_splib07_subset -- USGS Spectral Library v7 (CC0, ScienceBase): the
    ASCII channel only (splib07a + splib07b zips); ADMISSION selects
    Chapter-V Vegetation + Chapter-S Soils and Mixtures of splib07a by the
    recorded subset rule, and the 5.1 GB full bundle is admitted as a named
    DEFERRED identity with cause -- never downloaded.

Pins resolve at load time from each data dir's download_receipt.json (written
by tools/science_funnel/appearance_fetch.py, idempotent, byte-pinned). The
class contracts these connectors map to live in the authored class-contract
store (batch.observation.goldenberg_taxon, batch.property.goldenberg_reflectance,
batch.entity.phylacine_species, batch.series.splib07_spectrum,
batch.deferred.usgs_splib07_full -- all authored for this lane with
envelopes derived from the pinned bytes).
"""
from .. import adapters_appearance  # noqa: F401  (registers lane adapter names)
from . import connectors as C
from .connectors import _artifacts, _pins

_gold_receipt, _gold_pins = _pins('goldenberg_reflectance')
_phy_receipt, _phy_pins = _pins('phylacine')
_usgs_receipt, _usgs_pins = _pins('usgs_splib07_subset')

CONNECTORS = {
    'goldenberg_reflectance': {
        'connector_id': 'goldenberg_reflectance',
        'mode': 'admit',
        'data_dir': 'goldenberg_reflectance',
        'adapter': 'goldenberg_rows',
        'source': {
            'id': 'zenodo.goldenberg.15084543',
            'release': 'Replication data for "Color and near-infrared '
                       'reflectance covary in distinct ways across taxa and '
                       'time" (Zenodo 15084543, DOI 10.5281/zenodo.15084543, '
                       'posted 2025-03-25); total_dataset.csv sha256-verified '
                       'against the API-recorded upstream md5 2026-09-18',
            'url': 'https://zenodo.org/records/15084543',
            'license': 'CC BY 4.0 (Zenodo record metadata license field '
                       '"cc-by-4.0", access_right "open"; record JSON pinned '
                       'as artifact); attribution: Goldenberg et al.',
            'known_gaps': ['summary reflectance per taxon row (B2 totals over '
                           'UV/VIS/NIR segments), not raw spectra',
                           'reflectance percent can exceed [0, 100] '
                           '(measured noise retained, never clamped)',
                           '660 of 3,528 cells are NA and emit statuses, '
                           'never zeros',
                           'phylogenies pinned as attachments, not parsed '
                           '(comparative-methods work is a later membrane)'],
        },
        'artifacts': _artifacts('goldenberg_reflectance', [
            ('total_dataset.csv', 'data'),
            ('zenodo_record_15084543.json', 'attachment'),
            ('mammals.tree', 'attachment'),
        ], _gold_pins),
        'constants': {
            'expected_rows': 441,
            'zenodo_record_sha256':
                _gold_pins['zenodo_record_15084543.json']['sha256'],
        },
        'classes': {'entity': 'batch.observation.goldenberg_taxon',
                    'measurement': 'batch.property.goldenberg_reflectance'},
    },
    'phylacine_1_2_1': {
        'connector_id': 'phylacine_1_2_1',
        'mode': 'admit',
        'data_dir': 'phylacine',
        'adapter': 'phylacine_species',
        'source': {
            'id': 'phylacine.1.2.1',
            'release': 'PHYLACINE 1.2.1 (MegaPast2Future/PHYLACINE_1.2 GitHub '
                       'release v1.2.1, 106,362,537 bytes HEAD-verified '
                       '2026-09-18; Dryad doi:10.5061/dryad.bp26v20); trait '
                       'table extracted deterministically from the pinned zip',
            'url': 'https://github.com/MegaPast2Future/PHYLACINE_1.2/releases/'
                   'download/v1.2.1/PHYLACINE_1.2.1.zip',
            'license': 'CC0 (README quote captured by the probe dossier; '
                       'release-notes PDF pinned as the in-archive license '
                       'evidence)',
            'known_gaps': ['the release zip (106,362,537 bytes) EXCEEDS the '
                           '100 MB git per-file ceiling: pinned by receipt '
                           'only, never committed; bundles pin the derived '
                           'trait table (ncbi_taxdmp precedent)',
                           'the 132 MB complete and 96 MB small phylogeny '
                           'members stay inside the pinned zip, never '
                           'extracted (same ceiling)',
                           'range maps (11,668 GeoTIFFs) and taxonomy '
                           'synonymy tables not admitted by this lane',
                           'IUCN EP status is the source spelling; never '
                           'normalized silently'],
        },
        'artifacts': _artifacts('phylacine', [
            ('phylacine_trait_table.csv', 'data'),
            ('phylacine_release_notes.pdf', 'attachment'),
        ], _phy_pins),
        'constants': {'expected_rows': 5831},
        'classes': {'entity': 'batch.entity.phylacine_species'},
    },
    'usgs_splib07_subset': {
        'connector_id': 'usgs_splib07_subset',
        'mode': 'admit',
        'data_dir': 'usgs_splib07_subset',
        'adapter': 'splib07_chapter_spectra',
        'source': {
            'id': 'usgs.splib07.ascii_subset',
            'release': 'USGS Spectral Library Version 7 (ScienceBase item '
                       '5807a2a2e4b0841e59e3a18d, DOI 10.5066/F7RR1WDJ); '
                       'ASCII channel zips fetched 2026-09-18 with sizes '
                       'HEAD+item-JSON verified; admission selects '
                       'Chapter-V Vegetation + Chapter-S Soils and Mixtures '
                       'of the native-resolution splib07a grid',
            'url': 'https://www.sciencebase.gov/catalog/item/'
                   '5807a2a2e4b0841e59e3a18d',
            'license': 'CC0 1.0 (usgs.gov data-release rights field, quoted '
                       'by the probe dossier; FGDC metadata XML pinned as '
                       'identity evidence)',
            'known_gaps': ['SUBSET RULE: no mammal chapter exists in SPLib '
                           '(fur optics comes from the Goldenberg source); '
                           'the appearance-relevant chapters are Vegetation '
                           'and Soils-and-Mixtures; minerals/artificial/'
                           'coatings/liquids/organic chapters and errorbar '
                           'files stay pinned but are not admitted; splib07b '
                           '(the same spectra resampled to common grids) is '
                           'pinned whole and not admitted -- splib07a is the '
                           'native-resolution canonical grid',
                           'the full 5,479,324,354-byte bundle is a DEFERRED '
                           'identity record with cause, never downloaded',
                           '39 AVIRIS spectra sit on the AVIRIS-1996 grid '
                           'whose 3 detector-overlap points decrease: in 38 '
                           'the overlap channels are nodata, so the admitted '
                           'sample axes are monotonic and carry the recorded '
                           'overlap unknown; 1 spectrum (Bacterial_mat_YNP-B1) '
                           'decreases across MEASURED channels and '
                           'quarantines -- resolving the overlap is a later '
                           'membrane, never a silent dedupe',
                           'sample metadata HTML (with photos) not pinned; '
                           'spectra carry the zip-carried header identity'],
        },
        'artifacts': _artifacts('usgs_splib07_subset', [
            ('ASCIIdata_splib07a.zip', 'data'),
            ('ASCIIdata_splib07b.zip', 'attachment'),
            ('ASCIIdata.xml', 'attachment'),
            ('USGS_Spectral_Library_Version_7_Data.xml', 'attachment'),
            ('sciencebase_item.json', 'attachment'),
            ('sciencebase_ascii_item.json', 'attachment'),
        ], _usgs_pins),
        'constants': {
            'chapters': ['ChapterV_Vegetation', 'ChapterS_SoilsAndMixtures'],
            'expected_spectrum_files': 495,
            'deferred': {
                'path': 'usgs_splib07.zip',
                'bytes': 5479324354,
                'url': 'https://www.sciencebase.gov/catalog/file/get/'
                       '5807a2a2e4b0841e59e3a18d?name=usgs_splib07.zip',
                'cause': 'The full v7 bundle is 5,479,324,354 bytes (item '
                         'JSON, verified 2026-09-18) -- far above the 256 MB '
                         'intake-bundle and 100 MB per-file ceilings; its '
                         'SPECPR binaries, GIF plots and photo-laden HTML '
                         'add nothing to the admitted ASCII channel. The '
                         'ASCII child item carries NO per-chapter zips (its '
                         'full 30-file list is pinned), so the two whole-'
                         'ASCII zips are the smallest per-spectrum artifacts '
                         'and the chapter selection happens at admission by '
                         'this recorded rule.',
            },
        },
        'classes': {'series': 'batch.series.splib07_spectrum',
                    'entity': 'batch.deferred.usgs_splib07_full'},
    },
}

# Data dirs the reprove blob index must see so these admissions stay
# re-provable by recorded-producer replay in later runs.
SEARCH_DIRS = ['goldenberg_reflectance', 'phylacine', 'usgs_splib07_subset']
