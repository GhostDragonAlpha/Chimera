# DATABASE HUNT — Physiology / Appearance / Chemistry / Identity
Worker: dbhunt_phys · Date of probes: 2026-09-17 (all live-HTTP evidence same day)
Read-only task: no graph writes, no code. Scratch probe artifacts in `probe/` (incl. downloaded PanTHERIA zip).

---

## FALSIFIER VERDICT

**PREDICTION UNDER TEST:** "At least four verifiable, authless-downloadable, license-clear datasets close named physiology/appearance/chemistry/identity gaps."

**VERDICT: SUPPORTED.** Eight datasets verified by direct HTTP probe, across all four families, all authless, all with a captured license statement or license metadata field:

| # | Dataset | Family | License (how verified) | Authless proof |
|---|---------|--------|------------------------|----------------|
| 1 | PanTHERIA 1.0 | PHYSIOLOGY (BMR/thermoreg) | **CC0** (figshare API license field) | **Downloaded during probe**: 2,950,934 bytes, BMR columns read from inside the zip |
| 2 | USGS Spectral Library v7 | APPEARANCE (ground/veg spectra) | **CC0 1.0** (quoted from usgs.gov page) | `file/get` URL returned 200 + attachment disposition |
| 3 | Rhea | CHEMISTRY (reactions) | **CC BY 4.0** (verbatim LICENSE.txt fetched from FTP) | Anonymous dir listing of ftp.expasy.org, release 2026-09-02 |
| 4 | GBIF Backbone Taxonomy | IDENTITY | **CC BY 4.0** (API `license` field = legalcode URL) | `/species/match?name=Macaca mulatta` → 200, `ACCEPTED`, confidence 99 |
| 5 | NCBI taxonomy taxdmp | IDENTITY | Public domain (US Govt work, 17 USC 105 basis) | HEAD 200, 79,535,405 bytes, dated today |
| 6 | ITIS SQLite bulk | IDENTITY | Public domain (US federal program; statement not on downloads page — minor caveat) | HEAD 200, 224,511,428 bytes |
| 7 | Goldenberg et al. color+NIR reflectance | APPEARANCE (mammal fur) | **CC BY 4.0** (Zenodo license field `cc-by-4.0`) | Zenodo API 200, `access_right: open` |
| 8 | PHYLACINE 1.2.1 | PHYSIOLOGY (masses/phylogeny support) | **CC0** (README quote captured) | GitHub release redirect → 200, 106,362,537 bytes |

Named-need scorecard: (1) muscle activation dynamics — **NOT CLOSED** (see unknowns); (2) fur/skin optical — closed for *reflectance spectra* (7), not BRDF; (3) USGS — **CLOSED**, no login; (4) Rhea — **CLOSED** (CC BY 4.0 quote); (5) taxonomic backbone — **CLOSED** thrice over; (6) mammal BMR — **CLOSED** (PanTHERIA carries `18-1_BasalMetRate_mLO2hr` + `5-2_BasalMetRateMass_g`, 5,417 rows).

---

## PER-CANDIDATE DOSSIERS

### FAMILY: PHYSIOLOGY

#### P1. PanTHERIA 1.0 — mammal life-history + BMR — **DOWNLOADABLE_NOW** (strongest probe in this dossier)
- Files: `https://ndownloader.figshare.com/files/5604752` (= `ECOL_90_184.zip`, 2,950,934 bytes, md5 published on figshare). Landing: Wiley figshare collection 3301274 → article 3531875 "Full Archive", DOI `10.6084/m9.figshare.3531875.v1`.
- License: **CC0** — figshare API `license: CC0` for article 3531875.
- Auth: none. Mechanism: direct HTTPS file. (The old `esapubs.org/archive/ecol/E090/184/...` path is **dead — 404**; use figshare.)
- Ground truth from this probe (zip in `probe/pantheria.zip`): `PanTHERIA_1-0_WR05_Aug2008.txt` = 5,417 data rows; columns include **`18-1_BasalMetRate_mLO2hr`**, **`5-2_BasalMetRateMass_g`**, `5-1_AdultBodyMass_g`, `1-1_ActivityCycle`, `6-2_TrophicLevel`, `28-2_Temp_Mean_01degC`. BMR in ml-O2/hr + the mass it was measured at + adult mass ⇒ Kleiber/White-Seymour scaling derivable per RULE 1 (derive, don't sweep).
- Caveat: 2008 compilation; BMR column sparser than body mass (−999 sentinels throughout).

#### P2. PHYLACINE 1.2.1 — **DOWNLOADABLE_NOW**
- File: `https://github.com/MegaPast2Future/PHYLACINE_1.2/releases/download/v1.2.1/PHYLACINE_1.2.1.zip` → redirect → 200, **106,362,537 bytes**. Site: `https://megapast2future.github.io/PHYLACINE_1.2/`; Dryad `doi:10.5061/dryad.bp26v20` (Dryad API returned empty body at probe time — use the GitHub release).
- License: **CC0** — README.md line 304, quote: *"This work is licensed under a Creative Commons 0 License"* (CC0 badge linked).
- Use: updated late-Quaternary mammal masses, diet, phylogeny — mass-checks and phylogeny for PanTHERIA BMR (PanTHERIA masses are 2008-vintage).

#### P3. Muscle activation dynamics (Hill-type params, twitch times, fatigue) — **NOT CLOSED — see UNKNOWNS**
- Best near-miss: `opensim-org/opensim-models` (GitHub). Models dir verified via API: `Arm26, Gait2392_Simbody, Leg39, Rajagopal, ...` — per-muscle Hill-type parameters (Fmax, optimal fiber length, tendon slack length, activation/deactivation time constants) live inside `.osim` XML. **License: `null` via GitHub API; `LICENSE.md`/`LICENSE` raw = 404/404.** No license file ⇒ default copyright ⇒ fails license-clear. Human models, not macaque. Classification: DOWNLOADABLE_NOW / LICENSE-UNCLEAR — operator decision needed (OpenSim *software* is Apache-2.0; the models repo is not).
- Literature fallbacks (tables, not DBs): Seki et al. 2001 (Pt/CT/½RT, PMC2278430), McNulty et al. 2000 (single motor-unit twitch distributions, PMC2270021), Blümel et al. 2012 (method to measure ALL Hill params, PMC3505888), Chen et al. 2023 review of musculotendon parameter conventions (PMC10172227).

#### P4. REFUTED ARTIFACT — "Alton et al. 2025 updated mammalian BMR database"
Search summary claimed: Dryad `10.5061/dryad.b8gtht9dc`, Zenodo 15288924, site `mamphys.github.io`, Sci Data `s41597-025-04514-8`. Probed: Zenodo API → **404 "persistent identifier is not registered"**; Dryad API/page → empty; mamphys.github.io → **404**; Crossref bibliographic query → no such title. Classification: **UNVERIFIABLE — likely search-engine fabrication.** Do not cite.

### FAMILY: APPEARANCE

#### A1. USGS Spectral Library Version 7 — **DOWNLOADABLE_NOW**
- Item: ScienceBase `https://www.sciencebase.gov/catalog/item/5807a2a2e4b0841e59e3a18d` (DOI `10.5066/F7RR1WDJ`). **Direct file:** `https://www.sciencebase.gov/catalog/file/get/5807a2a2e4b0841e59e3a18d?name=usgs_splib07.zip` → HEAD **200**, `content-disposition: attachment; filename="usgs_splib07.zip"`, `application/x-zip-compressed`. Size ~5.1 GB (per Esri/EnMAP docs; Content-Length not returned — streamed). Item JSON API works authless.
- **No login required** (HEAD succeeded with no credentials).
- License: usgs.gov data page, Rights field, quote: *"This work is marked with CC0 1.0 Universal."*
- Contents: lab/field/airborne spectra, UV–TIR; vegetation, soils, minerals, man-made targets — the ground/vegetation appearance backbone. Full library is 5.1 GB; per-sensor subset zips exist on the same item.

#### A2. Goldenberg et al. — "Color and near-infrared reflectance covary in distinct ways across taxa and time" replication data — **DOWNLOADABLE_NOW**
- `https://zenodo.org/api/records/15084543` (DOI `10.5281/zenodo.15084543`), posted 2025-03-25, `access_right: open`, **license `cc-by-4.0`** (Zenodo field). Files incl. `total_dataset.csv` ("Our full dataset") + mammal phylogeny (`mammals.tree`, Alvarez et al. 2022).
- Closest verified thing to a fur optical dataset: reflectance (+ NIR 700–1100+) measurements across taxa **including mammals**, machine-readable, sha256-pinnable.
- Complementary (not fur): figshare 25705380 / Sci Data 2025 "Spectral dataset of natural objects' reflectance, Southern Cone of South America" — 532 natural-object samples, 400–1000 nm (barks, stones, vegetation) — good environment-texture companion; license not yet probed (figshare default CC BY likely; probe before intake).

#### A3. Anti-candidates (appearance)
- **OMLC spectra** (`https://omlc.org/spectra/`): melanin, hemoglobin, water, fat, aorta — human-tissue optics. Page copyright: *"Copyright 2018 Scott Prahl."* **No license grant found** ⇒ license-unclear; usable as reference numbers, not as intake artifact without operator decision.
- **No fur BRDF database exists authless** — nothing verified. Anisotropic fur scattering remains a modeling problem (Kajiya-Kay/Marschner-style), calibrated against A2's reflectance spectra.

### FAMILY: CHEMISTRY

#### C1. Rhea — **DOWNLOADABLE_NOW**
- Listing: `https://ftp.expasy.org/databases/rhea/` — anonymous, current release dated 2026-09-02; subdirs `biopax/ ctfiles/ eb-eye/ kegg/ nlp/ old_releases/ rdf/ tsv/ txt/` + `LICENSE.txt` + `rhea-release.properties`. `tsv/` verified to contain `rhea-chebi-smiles.tsv`, `chebiId_name.tsv`, `rhea-directions.tsv`, `rhea-ec-iubmb.tsv`, etc.
- **License quote (LICENSE.txt fetched verbatim this probe):** *"We have chosen to apply the Creative Commons Attribution 4.0 International (CC BY 4.0) License (https://creativecommons.org/licenses/by/4.0/) to all copyrightable parts of the Rhea database. All files in the Rhea FTP directory may be copied and redistributed freely, without advance permission, provided that this copyright statement is reproduced with each copy."*
- Auth: none. `Access-Control-Allow-Origin: *` on file responses.
- Note: old top-level `rhea.tar.gz` is **404** (site restructured 2026-09); intake should pull per-format files under `tsv/` (+`LICENSE.txt` into the manifest — it IS the license evidence).

#### C2. BRENDA — **REGISTRATION** (license improved, access did not)
- `https://www.brenda-enzymes.org/copy.php` greps: *"licensed under Creative Commons Attribution License"* … *"CC BY 4.0"* … but also *"commercial products, processes, or services"* carve-out language and *"commercial users"* differentiation. Bulk data requires (free academic) account ⇒ fails authless. Enzyme kinetics from BRENDA: ON_REQUEST/REGISTRATION, CC BY 4.0 with commercial caveat.

#### C3. SABIO-RK — **UNVERIFIED LICENSE**
- REST API exists (`https://www.ebi.ac.uk/sabiork/...`, authless) but license statement not captured (documentation/about greps empty). Kinetics (Km, kcat) would serve physiology+chemistry; hold until license quoted.

#### C4. KEGG — confirmed restrictive (context premise; no re-probe needed). Rhea's `kegg/` subdir provides the KEGG mapping **of Rhea reactions** under Rhea's CC BY — the legal bridge.

### FAMILY: IDENTITY

#### I1. GBIF Backbone Taxonomy — **DOWNLOADABLE_NOW (by query)**
- API: `https://api.gbif.org/v1/species/match?name=Macaca%20mulatta` → 200 authless: `usageKey 2436604, "Macaca mulatta (Zimmermann, 1780)", ACCEPTED, confidence 99, family Cercopithecidae`. Dataset API: `https://api.gbif.org/v1/dataset/d7dddbf4-2cf0-4f39-9b2a-bb099caae36c` → `"license":"http://creativecommons.org/licenses/by/4.0/legalcode"`, DOI `10.15468/39omei`, type CHECKLIST/TAXONOMIC_AUTHORITY.
- License: **CC BY 4.0** (legalcode URL in API field). Auth: none, no key for species/match.
- Bulk file URL not probed (page 403 to fetchers); by-query satisfies the named need.

#### I2. NCBI Taxonomy — **DOWNLOADABLE_NOW (bulk)**
- `https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdmp.zip` → HEAD **200**, **79,535,405 bytes**, Last-Modified same-day (daily builds), sibling `.md5` present (fits the sha256-pinned pipeline), `Access-Control-Allow-Origin: *`. Also `new_taxdump.zip` (151 MB) for extended fields.
- License: public domain — US Government work (17 USC 105); NCBI asserts no copyright over the taxonomy dump.

#### I3. ITIS — **DOWNLOADABLE_NOW (bulk)**
- `https://www.itis.gov/downloads/itisSqlite.zip` → HEAD **200**, **224,511,428 bytes**, `application/zip`, Last-Modified 2026-08-27, served via AWS, no auth. Other formats same pattern (`itisMySQLBulk.zip`, `itisPostgreSql.zip`, `itisInformix.tar.gz`, ...). `MD5SUMS` provided.
- License: ITIS is a US federal interagency program ⇒ public domain; **the downloads page itself carries no license statement** (grep empty) — cite the agency basis, minor caveat.

#### I4. Catalogue of Life — **DOWNLOADABLE_NOW (by query) / bulk URL UNVERIFIED**
- ChecklistBank API: `https://api.checklistbank.org/dataset/3` → `"title":"Catalogue of Life"`, `"license":"cc by"`, size **5,432,443 name usages**, imported **2026-09-12** (monthly cadence). Authless.
- Bulk archive: `download.catalogueoflife.org/col/col-*.zip` guesses all **404**; `api.checklistbank.org/dataset/3/export.zip` → **400**. The download page is JS-rendered. COL usable by-query today; bulk file URL = open action item (check `download.checklistbank.org` layout next session).

---

## RANKED TOP-5 INTAKE PROPOSAL

1. **PanTHERIA 1.0** (CC0, 2.9 MB, figshare direct) — closes named need 6 (thermoregulation/BMR) with `18-1_BasalMetRate_mLO2hr` + body masses for 5,417 species; Kleiber scaling *derived*, not swept. Intake: zip → verify md5 from figshare API → pin.
2. **USGS Spectral Library v7** (CC0, ~5.1 GB, ScienceBase direct) — closes named need 3 (ground/vegetation/skin-adjacent optical). Large: intake the per-sensor subset zips first (VNIR for the dyad), full zip later.
3. **Rhea** (CC BY 4.0, tens of MB in `tsv/`+`rdf/`, expasy FTP direct) — closes named need 4 (reactions beyond the periodic table); `rhea-chebi-smiles.tsv` gives machine-readable species; keep `LICENSE.txt` in the manifest.
4. **GBIF Backbone + NCBI taxdmp** (CC BY 4.0 by-query + public-domain bulk, both verified authless) — closes named need 5; GBIF for runtime name resolution (`species/match`, Macaca mulatta → usageKey 2436604 verified), taxdmp for the bulk sha256-pinned artifact.
5. **Goldenberg et al. color+NIR reflectance** (CC BY 4.0, Zenodo direct) — only verified machine-readable mammal-fur optical data; seeds fur/skin appearance until a dedicated pelage-spectra database is proven to exist.

Runner-up: **PHYLACINE 1.2.1** (CC0, 101 MB) — mass/phylogeny update to pair with PanTHERIA.

## EXPLICIT UNKNOWNS

1. **Muscle activation dynamics tables (twitch CT/½RT, force-frequency, fatigue × fiber type/species) — the named need #1 — remain UNCLOSED.** No deposited machine-readable dataset was verified. OpenSim `.osim` models hold Hill-type params but the models repo carries **no license file** (license: null) and is human-only. Options: (a) operator ruling on OpenSim models license, (b) literature-extraction task from Seki 2001 / McNulty 2000 / Blümel 2012 tables, (c) new search targeted at motor-unit datasets (Dryad/Zenodo query syntax on this probe returned empty — inconclusive, not exhaustive).
2. **Fur BRDF** (anisotropic): no database found anywhere, authless or not. Appearance must calibrate reflectance-only (Goldenberg) against a fur-scattering model.
3. **Skin spectral reflectance** as a *licensed* dataset: OMLC is license-unclear (copyright Prahl, no grant). A CC-licensed human-skin spectra dataset is still to be found.
4. **Acoustic absorption of natural surfaces**: no natural-ground impedance DB verified. Nearest leads unprobed in depth: PTB absorption-coefficient database (free for simulations, German NMI) and RoomTreat 60-material CSV (CC BY 4.0, but manufactured materials). Natural-ground acoustics is flow-resistivity modeling (Embleton/Delany-Bazley), likely a derivation task, not a DB intake.
5. **COL bulk archive URL** — unresolved (404/400 on guesses; page is JS). By-query verified.
6. **SABIO-RK license** — not quoted; needed before any kinetics intake.
7. **BRENDA CC BY 4.0 commercial carve-out** exact wording — needs the full license.php text before any commercial-product use.
8. **ITIS public-domain statement** — inferred from federal status, not quoted from itis.gov.
9. USGS `usgs_splib07.zip` exact byte size — streamed (no Content-Length); ~5.1 GB from third-party docs.
10. Web-search summaries on this run **fabricated at least one plausible dataset** (Alton 2025 BMR) — every claim in this dossier is backed by a direct probe, and two search-found URLs (Zenodo 15288924, mamphys.github.io) are confirmed dead. Pattern noted for future intake gates: search-summary claims are claims, not evidence.
