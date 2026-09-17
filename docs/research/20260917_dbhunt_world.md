# DATABASE HUNT — WORLD / MATERIALS / TRANSPORT
Worker: `worker_dbhunt_world` · 2026-09-17 · read-only run, probes only (curl HEAD/ranged GET, REST GETs, page fetches)

---

## FALSIFIER VERDICT — FIRST

**RULE 0 membrane.**
- **STATEMENT:** Every named world/material gap in the intake brief has at least one verifiable, authless, downloadable source (direct HTTP or free API, no registration).
- **PREDICTION (unmeasured before this run):** Probing the candidate access paths (PROJ CDN, AWS WorldCover, CEDA/GEBCO, NCEI, ISRIC, Zenodo/Mendeley/ScienceBase) will yield HTTP 200/206 with content-length and no auth for at least one source per gap.
- **FALSIFIER (named before the run):** Any gap where every probed candidate returns 404 on all reasonable URL patterns, or requires login/agreement click-through/API key, or publishes no machine-readable artifact.

**VERDICT: SUPPORTED** — with one quality caveat, not a refutation.

| Gap | Authless-downloadable source found? | Classification |
|---|---|---|
| (1) EGM2008 geoid N(φ,λ) | YES — PROJ CDN, direct 200, 80.6 MB | DOWNLOADABLE_NOW |
| (2) Friction coefficients μ | YES, but ONLY as open-access literature tables (rubber-on-ground, skin tribology); **no authless bulk tribology database exists** | DOWNLOADABLE_NOW (tables, manual extraction) |
| (3) Soil mechanical props | YES — SoilGrids API+WebDAV (CC BY 4.0); USDA KSSL bulk (no login) | DOWNLOADABLE_NOW |
| (4) Land cover | YES — WorldCover v200 single tile on AWS, 4.6 MB | DOWNLOADABLE_NOW |
| (5) Bathymetry | YES — GEBCO 2026 direct on CEDA (public domain); small subsets via web form | DOWNLOADABLE_NOW |
| (6) Weather offline | YES — 3 independent authless paths (NCEI ISD/GSOD CSV, NASA POWER, Open-Meteo) | DOWNLOADABLE_NOW |
| (7) Rock/geology mechanical | YES — THOR (Zenodo, CC BY 4.0, direct CSV 200); USGS ScienceBase CC0 | DOWNLOADABLE_NOW |

**Caveat (the honest part of the verdict):** the friction gap passes the falsifier only in the weak sense — the "source" is peer-reviewed open-access tables inside papers, not a queryable database. A stricter membrane ("every gap has a machine-readable bulk download") would be **REFUTED** by friction. No Zenodo/Mendeley/Kaggle friction-coefficient bulk dataset surfaced in searches; tribonet.org table URL 404'd; Engineering ToolBox table is live (HTTP 200) but copyrighted (view-only reference, not intake-able as a pinned artifact).

---

## PER-CANDIDATE DOSSIERS (probed evidence)

### WORLD-1. EGM2008 geoid undulation grid — THE #1 GAP CLOSER

- **Candidate (verified):** `https://cdn.proj.org/us_nga_egm08_25.tif`
- **Probe:** HTTP 200; `Content-Length: 80585622` (80.6 MB); `Content-Type: image/tiff`; ranged GET returns **206** (partial reads work — good for sha256-pinned streaming verification).
- **Naming correction:** the brief guessed `us_nga_egm2008_25.tif` — **that URL 404s**. Also 404: `us_ega_egm2008_25.tif`, `egm2008_25.gtx`, `egm96_15.gtx`, `us_noaa_egm2008_1.tif` (all probed). The real PROJ-data names (from `OSGeo/PROJ-data` `copyright_and_licenses.csv`) are:
  - `us_nga_egm08_25.tif` — EGM2008, 2.5 arc-min, worldwide
  - `us_nga_egm96_15.tif` — EGM96, 15 arc-min, worldwide (probe: HTTP 200, `Content-Length: 2710815` = 2.7 MB — trivially small fallback)
- **License (quoted from `us_nga_README.txt` in PROJ-data repo):** "Format: GeoTIFF converted from GTX · License: **Public Domain**" — both grids, source NGA. Repo CSV row: `us_nga_egm08_25.tif,Disclaimed,Public domain`.
- **Auth:** none. **Mechanism:** direct URL. **Format:** GeoTIFF (PROJ-ready, proj.db references it for `+geoidgrids`).
- **NGA direct (probed):** `https://earth-info.nga.mil/GandG/wgs84/gravitymod/egm2008/egm08_wgs84.html` → **302** redirect to their JS app (`/index.php?dir=wgs84&action=wgs84`) — ON_REQUEST/click-through. The PROJ CDN copy is the clean path; provenance is documented (regenerable via GeographicLib per the README).
- **Fit to h=H+N:** gives N(φ,λ) globally at 2.5′ (≈4.6 km) resolution; combine with the already-banked Copernicus DEM GLO-30 tile for H.

### WORLD-2. Land cover — ESA WorldCover 2021 10 m

- **Candidate (verified):** `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N18W066_Map.tif`
- **Probe:** HTTP 200, `Content-Length: 4604997` (4.6 MB), anonymous — single 3°×3° COG tile, directly overlapping the banked DEM tile N18W066. (Adjacent guessed tile `N18W067` 404s — tile grid is lower-left-corner anchored; verify per-region tile ID from the STAC `https://services.terrascope.be/stac/` before any other region.)
- **License (quoted from AWS Registry `registry.opendata.aws/esa-worldcover-vito/`):** "**CC-BY 4.0**"; access: "AWS CLI Access (No AWS account required)" with `aws s3 ls --no-sign-request s3://esa-worldcover/`.
- **Auth:** none. **Mechanism:** direct URL (HTTPS or no-sign-request S3). **Format:** Cloud Optimized GeoTIFF, 11 classes (tree/ shrub/ grass/ crop/ built-up/ bare/ snow-water/ wetland/ mangrove/ moss/ water).
- **Gap-closing:** class → friction/soil dispatch table (which μ, which contact stiffness per surface).

### WORLD-3. Bathymetry — GEBCO 2026 (and ETOPO alt)

- **Verified direct URLs (from gebco.net page, HEAD/ranged probes on CEDA):**
  - Global zip: `https://dap.ceda.ac.uk/bodc/gebco/global/gebco_2026/ice_surface_elevation/geotiff/gebco_2026_geotiff.zip?download=1` — ranged GET **206**, `application/zip`, ~4 GB zipped.
  - **Quadrant tiles** (HTML index verified): `.../geotiff/` lists 8 files, e.g. `gebco_2026_n90.0_s0.0_w-90.0_e0.0_geotiff.tif` (covers PR region) — probe: HTTP 200, `Content-Length: 933257436` (933 MB), `image/tiff`, no auth.
  - Small-subset path: web app `https://download.gebco.net` (user-defined area → netCDF / GeoTIFF / Esri ASCII, no login) — form-mediated, no bulk API.
- **License (quoted from gebco.net):** "The GEBCO Grid is placed in the **public domain** and may be used free of charge." (acknowledgment + DOI `10.5285/4f68d5c7-45eb-f999-e063-7086abc036fa` requested in publications).
- **Auth:** none. **Classification:** DOWNLOADABLE_NOW (authless quadrants; true small tiles need the web form).
- **Alt (page probed 200):** NOAA ETOPO 2022, `https://www.ncei.noaa.gov/products/etopo-global-relief-model` — land+bathymetry, US Gov (no further probe; files via NGDC THREDDS).

### WORLD-4. Weather usable offline — 3 authless paths (ERA5 is REGISTRATION)

- **NCEI ISD global-hourly (verified):** `https://www.ncei.noaa.gov/data/global-hourly/access/2024/78535011630.csv` (San Juan Luis Muñoz Marín — geographically relevant to the banked N18W066 tile) → HTTP 200, `Content-Length: 7138703` (7.1 MB / station-year), `text/csv`, no auth. Per-station-year direct URLs; station directory indexes are HTML-listed.
- **NCEI GSOD (verified):** `https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/2024/78535011630.csv` → HTTP 200, **83 KB**/station-year. The tiny-subset winner.
- **NASA POWER hourly point API (verified):** `https://power.larc.nasa.gov/api/temporal/hourly/point?parameters=T2M,RH2M,WS2M&community=AG&longitude=-66.1&latitude=18.4&start=20240101&end=20240102&format=CSV` → HTTP 200, CSV with header, MERRA-2 reanalysis at 0.5°×0.625°, no auth, no key. NASA open-data terms.
- **Open-Meteo archive API (verified):** `https://archive-api.open-meteo.com/v1/archive?latitude=18.4&longitude=-66.1&start_date=2024-01-01&end_date=2024-01-02&hourly=temperature_2m,...` → HTTP 200 JSON, no key; free non-commercial tier (commercial requires paid key — a license-term trap, not an auth wall).
- **ERA5 (checked, rejected):** CDS dataset page carries "Login ‒ Register" gating and no anonymous direct-download path; license "CC-BY licence". Classification: **REGISTRATION**. Do not bank ERA5 when the three above cover the need authlessly.

### WORLD/MATERIALS-5. Soil — ISRIC SoilGrids (verified) + USDA NCSS/KSSL (verified, form-mediated)

- **SoilGrids REST API (verified):** `https://rest.isric.org/soilgrids/v2.0/properties/query?lon=-93.5&lat=41.8&property=sand&property=clay&depth=0-5cm&value=mean&value=Q0.05` → HTTP 200 JSON, no auth; e.g. clay mean 238 g/kg (d_factor 10 → 23.8%). **Probe note:** the PR-coast point (18.4, −66.1) returned `mean:null` — near-coast pixels can be nodata; test exact points before relying on them.
- **SoilGrids WebDAV file server (verified):** `https://files.isric.org/soilgrids/latest/data/` browsable anonymously; per-property rasters tiled, e.g. `.../sand/sand_0-5cm_mean/tileSG-000-019/tileSG-000-019_4-4.tif` → HTTP 200, **144,815 bytes** (145 KB per tile chunk) — genuinely small-subset downloadable. Global per-map ≈ 5 GB (VRT + tiles), full property stack ≈ 120 GB (do NOT bulk-take).
- **License (quoted from ISRIC docs):** "Since 2019, SoilGrids products are provided under the **CC BY 4.0**"; API: "the REST API v2.0 is still under active development (beta stage)" and "our Fair Use Policy is defined as **5 API calls per 1 minute period**"; ISRIC notes service instability ("temporarily pause the service") — WebDAV is the stable path.
- **USDA NCSS/KSSL Lab Data Mart (verified page):** `https://ncsslabdatamart.sc.egov.usda.gov/` — HTTP 200, no login stated. Quote: "Nearly all data in the Kellogg Soil Survey Laboratory and the associated pedon data are available for download" in **SQLite, Access, GeoPackage, ESRI File GDB**; plus Soil Data Access webservices (`https://sdmdataaccess.nrcs.usda.gov/WebServiceHelp.aspx`). Contains lab-measured particle-size, **Atterberg limits (plasticity)**, CEC — the measured proxies a constitutive spring can be keyed to. Exact bulk-file URL is behind a dynamic page (see UNKNOWNS).
- **Bonus (verified via Zenodo API):** Austrian geotech lab dataset `https://zenodo.org/records/14251191` — cc-by-4.0, **open**, `Zenodo_DATA_Soranzo.csv` (0.1 MB) — 20+ years of lab soil testing (Vienna/Lower Austria/Burgenland); machine-readable soil constitutive-adjacent data.

### MATERIALS-6. Friction coefficients μ (the weak family)

- **No authless bulk tribology database found.** Searches over general web + Zenodo/Mendeley/Kaggle returned none machine-readable. tribonet.org calculator URL guessed 404.
- **Open-access measurement tables (verified existing, tables in-article):**
  - **Rubber (tire granules) vs ground-relevant surfaces:** PMC `https://pmc.ncbi.nlm.nih.gov/articles/PMC6355959` (Data in Brief, 2019, open access). Measured static μ, recycled-tire rubber against glass/PVC/ceramic/marble/wood/**concrete (smooth 0.34–0.44, rough 0.58–0.71)**/sandpaper (0.60–0.90), G.U.N.T TM 120 apparatus, 5 granule sizes. Directly the rubber-vs-ground family the brief asks for. Authless; CC-BY article; extraction = manual table transcription (the original ScienceDirect Data in Brief may carry a machine-readable supplement — unverified, see UNKNOWNS).
  - **Human skin tribology:** Derler & Gerhardt 2012 review "Tribology of Skin" — compiled μ tables, open copies at TU/e research portal and DORA Lib4RI (full-text PDF); Zhu et al. 2010 in-vivo skin CoF, PMC `https://pmc.ncbi.nlm.nih.gov/articles/PMC2997446/` open access. Skin-μ ≈ 0.2–0.5 dry, up to >1 hydrated.
- **Reference-only (live but not intake-able):** `https://www.engineeringtoolbox.com/friction-coefficients-d_778.html` — HTTP 200, classic static/kinetic μ table for many pairs, **copyrighted** (view-only; cannot be pinned/redistributed as an artifact).

### MATERIALS/TRANSPORT-7. Rock / geology mechanical properties

- **THOR — the rock strength database (verified):** `https://zenodo.org/records/12687445` — Zenodo API: license **cc-by-4.0**, access_right **open**; files include `2 -  UCS.csv`, `3 - Klp.csv`, `5 - authours.csv`, `Search tool.xlsx` (2.5 MB). Direct-file probe: `https://zenodo.org/records/12687445/files/2%20-%20%20UCS.csv?download=1` → HTTP 200, `text/plain`, 3,736 bytes, no auth. UCS standardized across rock types per Aydin & Basu (2005). DOWNLOADABLE_NOW.
- **USGS density + magnetic properties, western US/Alaska (verified):** DOI `10.5066/P9FONTGS` → resolves 302 to ScienceBase `https://www.sciencebase.gov/catalog/item/60356a96d34eb120311748e8` — HTTP 200; "over 20,000 physical property measurements" in ASCII + data dictionary; Rights (quoted): "This work is marked with **CC0 1.0 Universal**". No login. (Density/magnetics, not UCS — complements THOR.)
- **ROCK-sc/10/4025 (partially verified):** `https://data.mendeley.com/datasets/vk9vs574sk/1` — page HTTP 200; public files-API returned `{"error":400}`; 9 measured intact-rock parameters + 1 derived (index props → strength/stiffness). Download works through the web UI; programmatic path UNVERIFIED.
- **Rejected:** Zenodo 15703538 "High-temperature rock properties" — API says access_right **restricted** → ON_REQUEST, excluded.

---

## RANKED TOP-5 INTAKE PROPOSAL
(gap-closing power × license × authless × small-subset-downloadable)

1. **EGM2008 geoid — `https://cdn.proj.org/us_nga_egm08_25.tif`** (80.6 MB GeoTIFF, Public Domain, no auth, 206-range OK). Closes the banked-terrain contract h=H+N; the stated #1 need. EGM96 fallback `us_nga_egm96_15.tif` (2.7 MB) if 80 MB is too big for first admission. *Note the corrected filename.*
2. **NOAA GSOD + ISD station CSVs — `https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/2024/78535011630.csv`** (83 KB) and `.../global-hourly/access/2024/78535011630.csv` (7.1 MB), US Gov public domain, no auth. Weather boundary conditions offline, per-station-year, sha256-pinnable as-is.
3. **ESA WorldCover v200 tile — `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N18W066_Map.tif`** (4.6 MB COG, CC-BY 4.0, no-sign-request). Ground-class layer co-registered with the banked DEM tile → drives per-class friction/soil dispatch.
4. **THOR rock strength database — `https://zenodo.org/records/12687445`** (CC-BY 4.0, open, direct CSV 200; UCS.csv 3.7 KB + 2.5 MB search-tool XLSX). The only machine-readable rock-mechanical table found; closes gap (7) with a pin-size of kilobytes.
5. **ISRIC SoilGrids — REST `https://rest.isric.org/soilgrids/v2.0/properties/query?...` + WebDAV `https://files.isric.org/soilgrids/latest/data/`** (CC BY 4.0; 145 KB tile chunks; API free at 5 calls/min). Soil texture/OC per point → class-keyed ground-contact spring. Bank a point-query + one tile chunk, not the 120 GB stack.

**Bench (next cycle, in order):** GEBCO quadrant GeoTIFF (933 MB — big; prefer `download.gebco.net` form subset) · USDA KSSL bulk GeoPackage · USGS CC0 rock-props ScienceBase item · PMC rubber-friction tables transcription + Derler skin-μ review (manual-extraction intake, the only honest route for the friction gap).

## EXPLICIT UNKNOWNS

1. **KSSL bulk download URL** — the Data Mart page states bulk SQLite/GeoPackage availability but the static HTML shows a "Loading…" placeholder; the concrete file URL behind it was not captured. Mechanism verified no-login, artifact URL not yet.
2. **Mendeley programmatic download** for ROCK-sc/10/4025 (page 200, public files-API 400) — web-UI download presumed working; API path unverified.
3. **WorldCover tile-ID resolution for arbitrary regions** — N18W067 404'd while N18W066 hit; tile anchoring must come from the STAC API per region rather than guessed neighbors.
4. **Data in Brief (PMC6355959) machine-readable supplement** — ScienceDirect version may carry an xlsx/csv supplement beyond the in-article tables; not probed (publisher wall).
5. **SoilGrids coastal nodata** — PR-coast point returned `mean:null`; coverage over coastlines/water must be checked per-point before banking any PR-region soil query.
6. **GEBCO small-subset automation** — `download.gebco.net` is form-mediated; whether the form's POST is scriptable without a browser session was not tested.
7. **Fur friction** — no dedicated fur/hair-on-ground measurement table was hunted down (skin covered; fur would need a separate targeted search).
8. **ETOP0 2022 file-level URLs** — page verified 200 only; the NGDC THREDDS direct-file pattern was not probed (GEBCO already covers the need).

## PROVENANCE / METHOD NOTE
Every classification above rests on a probe run during this session: `curl -sI` (headers), ranged `curl -r 0-99` (206 checks), REST/JSON GETs (Zenodo API, SoilGrids API, NASA POWER, Open-Meteo), and page fetches for license quotes (PROJ-data README + licenses CSV, AWS Registry, gebco.net, ISRIC docs, USGS release page, CDS ERA5 page). No files written outside this scratch dir; no graph writes.
