# The database hunt — 2026-09-17

The operator's three questions, answered from probe-verified evidence (three parallel
research workers; every candidate was probed live — pages fetched, URLs confirmed,
files downloaded where claimed; nothing cited from memory). Full worker dossiers:
`20260917_dbhunt_motion.md`, `20260917_dbhunt_world.md`, `20260917_dbhunt_phys.md`
in this directory. Scratch pins with sha256: `.tmp/source_intake/20260917_dbhunt/pins.json`.

## 1. What databases do we need (by the graph's own families, mapped to open problems)

| Family | Open problem it solves | Best verified source | Status |
|---|---|---|---|
| motion | muscle architecture beyond the arm's 39 (PCSA, fascicle, pennation, tendon) | Guimarães 2026 (CC BY 4.0, **includes Macaca mulatta**, 48 muscles × 9 species) | PINNED |
| motion | macaque bipedal activation/GRF/angle reference | Oku 2021 supplementary xlsx (CC BY, Europe PMC endpoint) | PINNED |
| observations | quadruped gait kinematics (387 strides, 14 primate species) | Janisch 2024 figshare (CC BY 4.0) | PINNED |
| observations | gait temporal/spatial tables, tetrapod-wide | Wimberly/Granatosky Dryad (CC0; analytic tables KB-scale, videos 2.1 GB separate decision) | VERIFIED |
| observations | Japanese macaque gait (terrestrial + pole) | Higurashi & Kumakura Dryad (CC0; browser download; scripted needs free token) | VERIFIED |
| world | geoid undulation N for the h=H+N terrain law | PROJ CDN `us_nga_egm08_25.tif` (public domain, 80.6 MB, **note: egm08 not egm2008 in the filename**) | PINNED |
| world | weather boundary conditions | NOAA GSOD per-station CSVs (public domain, direct URLs; ERA5 is registration-walled) | PINNED |
| world | ground stiffness by soil class | ISRIC SoilGrids (CC BY 4.0 API) + Vienna soil lab 20-yr CSV (CC BY 4.0) | PINNED (lab CSV) |
| world | rock strength for ground/terrain contact | THOR UCS table (CC BY 4.0, 3.7 KB) | PINNED |
| world | land cover class at the tile | ESA WorldCover 2021 (CC BY 4.0, S3 no-sign; tile ids via STAC) | VERIFIED |
| world | bathymetry | GEBCO (public domain; quadrant TIFs 933 MB, subsets via form) | VERIFIED |
| world | friction coefficients (μ grounding) | NO bulk database exists authless — open literature tables only (rubber-vs-concrete μ=0.34-0.71 verified). Weak close; flagged honestly | GAP STANDS |
| physiology | thermoregulation/BMR scaling | PanTHERIA 1.0 (CC0, 5,417 species, file read and verified) | PINNED |
| appearance | fur/skin optical reflectance | Goldenberg color+NIR replication CSV (CC BY 4.0, Zenodo) — the only machine-readable mammal fur optical dataset found | VERIFIED |
| appearance | ground/vegetation spectra | USGS Spectral Library v7 (CC0, ~5.1 GB, per-sensor subsets exist) | VERIFIED |
| chemistry | reactions beyond elements | Rhea (CC BY 4.0, anonymous FTP; per-format files after the 2026-09 restructure) | VERIFIED |
| identity | machine-resolvable names | GBIF backbone (CC BY 4.0 API; live Macaca mulatta match probed) + NCBI taxdmp (public domain, 79.5 MB) | VERIFIED |
| shape | macaque joint morphology (axes/centers) | NOTHING license-clear found — open problem stands | GAP STANDS |
| motion | quadruped-mammal EMG | Nothing open; best hope Nishizaki 2026 eLife "upon acceptance" | GAP STANDS |

Fabrication killed: the "Alton 2025 mammalian BMR database" that appears in search
results does not exist (Zenodo 404, Dryad empty, site 404, Crossref silent). PanTHERIA
is the real, older, verified equivalent.

## 2. Where we find them (the pattern)

- **Domain repositories with direct HTTP**: Dryad, Zenodo, figshare (ndownloader URLs),
  Europe PMC supplementaryFiles endpoint (beats NCBI bot-walls for CC BY supplements).
- **Government open data**: NOAA NCEI, USGS ScienceBase (CC0), NGA models via the PROJ CDN.
- **Institutional APIs**: ISRIC SoilGrids REST, GBIF species-match API, ESA S3 open bucket.
- **Dead ends to stop revisiting**: KUPRI/Digimorph macaque CT pages (dead links), bulk
  tribology DBs (none), fur BRDF (none), CanidGait (commercial, not a dataset).

## 3. How we download them (mechanics + what is already pinned)

Everything pinned today sits in `.tmp/source_intake/20260917_dbhunt/` with sha256 in
`pins.json` (9 files, ~85 MB total): the EGM2008 geoid grid (80.6 MB), PanTHERIA,
Guimarães muscle architecture zip, Oku 2021 macaque bipedal zip, Janisch kinematics
CSV, NOAA San Juan 2024 GSOD, THOR UCS, Vienna soil lab CSV. Download mechanics per
source are in the worker dossiers (exact URL patterns, API shapes, bot-wall notes:
NCBI walls curl but Europe PMC does not; Dryad scripted downloads need a free token;
WorldCover tile ids must come from STAC, not guessed).

Admission path (already built): each pinned source becomes a batch connector
(`tools/science_funnel/batch/connectors.py` + adapter + class contract), then
`batch_qualify --admit ... --apply` proves every record mechanically. Visual
verification of admitted data stays pending, per the operator's note.

## Priority intake queue (next slice)

1. Guimarães muscle architecture (closes the biggest motion gap; species-tagged Macaca mulatta).
2. EGM08 geoid + Copernicus tile → unblocks the terrain h=H+N reduction slice.
3. Janisch kinematics + Oku 2021 → the movement-law reference pair.
4. PanTHERIA → physiology scaling.
5. THOR + Vienna soil + San Juan GSOD → ground/weather boundary conditions.
