# INTAKE-GEO — Rule 0 admission of four geoscience sources
Lane: `lane/intake-geo-20260917` (base 14c56162) · Worker: GLM 5.3 · Preregistered 2026-09-17

This document states the Rule 0 membrane BEFORE the qualifying run and BEFORE any
connector code. The four sources were probe-verified (license + authless URL + direct
download) by `docs/research/20260917_dbhunt_world.md` the same day; this lane converts
them into pinned, mechanically proven batch admissions.

---

## RULE 0 ADMISSION (stated before the run)

**STATEMENT.** Four license-clear, authless geoscience tables — THOR rock strength
(Zenodo 12687445, CC BY 4.0, 47 lithologic-group σ_UCS summaries), the Vienna/Lower
Austria/Burgenland geotechnical lab dataset (Zenodo 14251191, CC BY 4.0, 1,066 soil
specimens), the NOAA GSOD station-year CSV for station 78535011630 / Roosevelt Roads,
PR (US Gov; WMO Res-40 note carried, never resolved silently), and the ESA WorldCover
2021 v200 tile over the Cayo Santiago patch (CC BY 4.0 per the tile's own embedded
license field) — can be admitted as sha256-pinned intake bundles whose adapters carry
mechanical falsifiers per record class, with zero silent drops.

**PREDICTION (not yet measured; the WorldCover centre datum is read for the first time
under this membrane, after this statement was written).** All row counts below were
re-measured from the pinned bytes before the qualifying run; 1,478 records are
expected in total (48 + 1,066 + 359 + 5).
1. THOR: all 48 data rows admit as `batch.property.measurement` records whose
   `value_si` is the mean σ_UCS in pascals (source value × 1e6, exact). The megapascal
   attribution is a **declared assumption on every record** — the pinned CSV bytes carry
   no unit column; MPa is the unit of the companion paper (Haag & Schoenbohm 2025,
   EPSL 660, 119364) and the only unit consistent with the rock-mechanics envelope
   (0.1–1000 MPa). The derived ratio columns 75/25 and 90/10 are omitted with a
   recorded unknown (recomputable from the admitted percentiles). (The brief-stage
   count "47" was a miscount — Class I 3 + Class II 10 + Class III 35 = 48; corrected
   at first adapter run, before the qualifying run.)
2. Soranzo: all 1,066 specimen rows admit as `batch.observation.soil_specimen` records;
   an empty cell is an absent quantity, never a zero; every measured cell sits inside a
   declared per-family envelope. Per-column units are source-conventional (%, mm, g/cm³,
   m/s, kPa, degree) and are **declared as assumed on every record** — the pinned bytes
   carry no unit column; the companion paper's test families (PSD, Atterberg, Proctor,
   permeability, direct shear) fix the families, not the printed units.
3. GSOD: all 359 data rows (unique dates 2024-01-01..2024-12-24; 7 days absent from the
   source file itself) admit as `batch.observation.gsod_day` records. Exactly **519
   sentinel cells** (SNDP 359, GUST 106, STP 31, VISIB 9, WDSP 5, MXSPD 5, PRCP 3,
   SLP 1) become explicit nodata entries — never values — with the sentinel code table
   parsed from the pinned README, not hardcoded. STP is admitted as asserted (≈15–16 mb
   rendered) with a recorded truncation unknown: the README documents STP missing =
   9999.9, but the file ships STP missing = 999.9 and its real values render 4-digit
   station pressures (≈1015.9 mb) as 3 digits — asserted bytes are carried, never
   "repaired".
4. WorldCover: the bucket's own tile index (`esa_worldcover_grid.geojson`, 2,651
   features) resolves 18.1565 N 65.7350 W to **exactly one** tile, `N18W066` (measured
   during provenance fetch, before the class datum was read). The pinned tile
   self-declares `product_tile = N18W066` in its embedded GDAL metadata — the two
   independent identity claims must agree. The tile is 36,000×36,000, one band,
   BitsPerSample 8, SampleFormat 1 (uint8), Deflate, Predictor 1, 1024×1024 tiles,
   GTRasterTypeGeoKey = 1 (RasterPixelIsArea), EPSG:4326, tiepoint (0,0)→(−66.0, 21.0),
   pixel scale 1/12000 degree. The integer TIFF reader added to `terrain.py` reads the
   patch-centre pixel (row, col = floor of the area-convention inverse geotransform,
   with a recorded boundary note if the point falls within 1e-9 of a pixel edge); the
   class value must be one of the eleven legend codes {10, 20, 30, 40, 50, 60, 70, 80,
   90, 95, 100} declared in the tile's own embedded legend, and one class record plus
   four tile-metadata `batch.property.measurement` records admit (5 = 5 + 0).

**FALSIFIER (named before the run).**
- A corrupted row quarantines **exactly itself**: one injected bad THOR row (mean UCS
  9.99e4 MPa → value 9.99e10 Pa outside the physical envelope), one injected bad soil
  row (a gradation fraction of 150 %), one injected bad GSOD row (TEMP 99.99 — a
  canonical all-9s missing rendering that belongs to NO accepted code set for that
  column, so it must quarantine, not pass as nodata and not admit as a value), and one
  injected out-of-vocabulary WorldCover class code (55) — each quarantines only its own
  record and the count identity still closes. Verified by direct injection in
  `test_batch_geo.py` before the qualifying run.
- The count identity closes per connector: fetched == admitted + quarantined, zero
  silent drops, enforced mechanically by the pipeline and asserted per run.
- Idempotency: re-running `geo_fetch` re-verifies every pin and leaves receipts
  byte-identical; re-running the full `batch_qualify --apply` command re-proposes every
  bundle as a no-op against the rebuilt graph (same hash); upstream byte drift refuses
  loudly (`pin_drift`, never re-pinned silently).
- The integer reader refuses float assumptions: a float32 band (SampleFormat 3) or a
  non-integer dtype must refuse (`terrain_int_reader_*` refusal), and the existing
  float reader's behavior is untouched (the full pre-existing terrain suite must stay
  green bit-for-bit).
- The two decode paths (stdlib targeted zlib tile decode; tifffile full-page decode)
  must agree bit-exactly on the synthetic tiles and on the real centre value (one-time
  full decode recorded below; re-runnable via `CHIMERA_GEO_HEAVY=1`).

## DERIVATIONS (RULE 1 — no sweeps, no chosen numbers)

- **MPa → Pa.** `value_si = source_MPa × 1e6`, exact. Source-declared unit carried as
  `payload.source_unit = 'MPa'` next to the SI pair.
- **Tile anchoring.** The WorldCover tiling grid is lower-left-corner anchored 3°×3°.
  The tile id is NOT guessed from neighbours: the point is tested against every feature
  of the pinned `esa_worldcover_grid.geojson` (point-in-polygon, ray casting); exactly
  one feature may contain it. Measured hit: `ll_tile = N18W066`, ring (−66,18)→(−66,21)
  →(−63,21)→(−63,18). The S3 bucket's index at
  `https://esa-worldcover.s3.eu-central-1.amazonaws.com` IS the tile index used (the
  bucket carries no STAC JSON items; the grid GeoJSON is its machine-readable index).
- **Centre pixel.** RasterPixelIsArea (GeoKey 1025 = 1, read from the pinned file):
  pixel (row, col) covers lat [lat0 −(row+1)·s, lat0 − row·s], lon [lon0 + col·s,
  lon0 + (col+1)·s] with s = ModelPixelScale. The containing pixel is
  row = floor((lat0 − lat)/s), col = floor((lon − lon0)/s), guarded so a point within
  1e-9 of an edge snaps deterministically and records `on_pixel_edge = true`.
- **Sentinel law.** Parsed, not hardcoded: the pinned README's data section declares
  `Missing = <code>` per column, and the adapter derives each column's accepted code
  set mechanically. **Pre-run refinement (recorded before any run, from the pinned
  bytes alone):** the naive "all 9s = missing" reading is REFUTED by the file itself —
  VISIB/WDSP/MXSPD carry real 9.9 values (9.9 miles visibility, 9.9 knots wind), so a
  blanket all-9s rule would quarantine real rows. The operative law: accepted codes =
  the column's documented code plus, for 6-char codes (9999.9), the leading-digit-
  clipped 5-char rendering (999.9) — the README's own general all-9s line licenses the
  clipping (and is anchored verbatim), while the file shows it cannot be the whole law.
  Two README defects are absorbed by the derivation, not patched over: STP documents
  9999.9 but ships missing as 999.9 (same clipping), and MXSPD's code is wrap-garbled
  to `999.` in the pinned bytes (resolved as the unique canonical code starting with
  that fragment). A cell equal to a canonical all-9s code that NO accepted set claims
  quarantines (`gsod_unrecognized_sentinel_code`).
- **Envelope bounds** are physical, not tuned: UCS 0.1–1000 MPa (all 47 group means
  span 3.66–130.08); soil fractions 0–100 %, grain sizes 0–150 mm, CU/CC 0–5000,
  densities 0.5–3.5 g/cm³, Atterberg 0–150 %, k10 1e-13–1e-1 m/s (measured span
  4.47e-12–1.1e-4), shear 0–200 kPa / 0–90°; GSOD temps −80–150 °F, pressures
  0–1100 mb (STP asserted values ride inside; the truncation is recorded, not fixed),
  winds 0–250 kn, visibility 0–100 mi, precipitation 0–30 in, obs counts 0–31.

## SOURCES (pins recorded in each `download_receipt.json`)

| Source | License | Pin |
|---|---|---|
| THOR `2 -  UCS.csv` (Zenodo 12687445; filename carries literal spaces) | CC BY 4.0 (Zenodo API metadata, pinned as artifact) | sha256 `466e47ef419b1d777b513441631a9e72b65b840f9ded07fed73f444e77599eff`, 3,736 bytes |
| Soranzo `Zenodo_DATA_Soranzo.csv` (Zenodo 14251191) | CC BY 4.0 (Zenodo API metadata, pinned as artifact) | sha256 `5932484eac2ba102af9ec71cb414570b338a37975569e88b879e6f83f447a71f`, 94,297 bytes |
| NOAA GSOD `78535011630.csv` (2024) + `readme.txt` | US Government work; README carries the WMO Resolution 40 note for non-US locations — carried on every record, never resolved silently | csv sha256 `338bb5b9e1fd5fdcfb2bba9a052c7a5db75cd740f59b8494b0a544e7769efc6d`, 83,597 bytes; readme sha256 `25a784a4cba0eab5f070137c57c4b4bd113982e054c77812b2d22e96c5818bc1`, 11,288 bytes |
| ESA WorldCover `ESA_WorldCover_10m_2021_v200_N18W066_Map.tif` + tile-grid index + PUM V2.0 | CC-BY 4.0 (declared in the tile's own embedded GDAL metadata); copyright "ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium" | tif sha256 `0d8b5835abb8aa33a80f4c66f5cf244a0368b551fa9fb470219d82e267241b78`, 4,604,997 bytes; grid `eeb5074bf182c411b3872b2494f6514401ecd9ba8ba0c353fe282f1e2b822f5b`, 543,674 bytes; PUM `4301a3d95260d88bd4315f43ccf2a12ef74ad391109b9f36e22b6e51d8490107`, 4,102,952 bytes |

## CLASS CONTRACTS

Reused where it fits: `batch.property.measurement` (THOR UCS summaries; WorldCover tile
metadata). Authored where the shape needs it (multi-quantity observation rows and a
categorical class):

- `batch.observation.soil_specimen` — one lab specimen, many co-measured quantities,
  per-family numeric envelopes; empty = absent, never zero.
- `batch.observation.gsod_day` — one station-day; documented sentinel codes become
  nodata entries, never values; per-unit-family envelopes.
- `batch.property.worldcover_class` — a categorical land-cover class at a point: the
  class code and its label must both be inside the eleven-class legend the tile itself
  declares; uint8/int16 band format, never float.

## RUN COMMAND (preregistered)

```
python -B -m tools.creature_graph.batch_qualify --reprove all \
  --admit thor_rock_ucs,vienna_soil_lab,noaa_gsod_station_year,esa_worldcover_n18w066 \
  --apply --out tools/science_funnel/validation/batch_geo_20260917/receipt.json
```

`--reprove all` is included deliberately: the five existing admissions must re-prove
byte-identically after this lane's code changes (recorded-producer replay) — evidence
unchanged is part of this admission's claim.

## VERDICT (runs completed 2026-09-17)

**SUPPORTED** — every prediction, with three honest corrections the runs measured, all
recorded at first measurement and none papered over.

**Applied receipt** `tools/science_funnel/validation/batch_geo_20260917/receipt.json`
(batch_id `375762c306cb373b…`): all five pre-existing admissions re-proved
byte-identically (3,821 records); 1,189 new records admitted and applied — THOR 48/0,
Soranzo 777 (+289 quarantined), GSOD 359/0, WorldCover 5/0; 5,010 records verified,
**0 contract failures**, count identity closed; graph rebuilt to 32,942 objects /
37,548 relations (hash `164e40ccbc9bc5d4…`); graphify consumer roundtrip HONEST 7/7;
mutation probe flagged exactly one corrupted record.

**Idempotency receipt** `receipt_rerun.json` (batch_id `7ba9c6ad41db30fa…`): the
identical second `--apply` run added **0 objects**, rewrote no shard bytes
(records_003.json = 4,505,538 bytes in both runs) and reproduced the graph hash.

1. **THOR — SUPPORTED, with a count correction.** 48 rows admit (the brief-stage
   "47" was a miscount of Class III; corrected at first adapter run, before the
   qualifying run). Every record carries `value_si` = mean_MPa × 1e6 in Pa with the
   megapascal attribution declared; class `batch.property.measurement` 48/48.
2. **Soranzo — SUPPORTED, with a shape correction.** 777 specimens admit; **289
   fully-empty source rows quarantine by design** (`no_measured_values`); the count
   identity closes 1,066 = 777 + 289 with zero silent drops. The exact-header check
   caught the water-content column `w` missing from the family map before any run;
   class `batch.observation.soil_specimen` 777/777.
3. **GSOD — SUPPORTED exactly.** 359 records, 0 quarantined; nodata totals SNDP 359 /
   GUST 106 / STP 31 / VISIB 9 / WDSP 5 / MXSPD 5 / PRCP 3 / SLP 1 = **519 exactly as
   preregistered**; STP truncation carried as asserted with unknowns; the sentinel law
   is parsed from the pinned README at run time (the wrap-garbled MXSPD fragment
   resolves to 999.9 mechanically); class `batch.observation.gsod_day` 359/359.
4. **WorldCover — SUPPORTED.** The bucket tile index resolves the patch centre to
   exactly one feature, `N18W066`, and the tile's own embedded `product_tile` agrees.
   The integer reader decoded the centre pixel **(row 34122, col 3180) = class 80,
   "Permanent water bodies"** — both axes sit exactly on pixel edges (snap recorded,
   `on_pixel_edge = true`); the 3×3 window is uniformly 80. The stdlib reader and a
   full tifffile decode agree bit-exactly on the 90,000-pixel verification window
   (one-time run before the qualifying run; re-runnable via `CHIMERA_GEO_HEAVY=1`),
   and the tile histogram holds only legend codes plus nodata 0. Class
   `batch.property.worldcover_class` 1/1; the four tile-metadata records passed
   `batch.property.measurement` 4/4.

**Falsifiers proven before the runs** (`tools/science_funnel/tests/test_batch_geo.py`,
32 tests + 1 gated heavy test, all green; funnel suite 224 OK): a corrupted row
quarantines exactly itself (THOR mean 99900 MPa; soil fraction 150 %; the wrong-code
sentinel TEMP=99.99 under `gsod_unrecognized_sentinel_code`; a real ocean nodata
pixel against the legend; an injected N18W067 tile-identity mismatch); the count
identity closes per connector; the integer reader refuses float bands and agrees
bit-exactly with tifffile on synthetic uint8/uint16 predictor-1/2 tiles while the
float reader's behavior is frozen; `geo_fetch` re-runs offline-idempotent and the
tile resolution is a single hit.

**FORCED DEVIATION (shared-code repair, recorded 2026-09-17).** The first full
idempotency re-run REFUSED at `build_graph` ("duplicate object id"):
`apply_patches` — as sharded at this lane's base 14c56162 — tracked known ids from
the program file only, so a second `--apply` re-appended shard-resident bulk
objects and the rebuild refused. The defect is latent in the shard split itself
(no lane had re-applied after 14c56162). Repaired in this lane minimally: shard
objects/relations now load into the known-identity sets; the stores were restored
to base and the qualifying run executed twice under the repaired writer —
first run added 1,193 objects, second added 0 and reproduced the hash. Evidence
unchanged was re-proven after the repair (the five reprove sources replayed
byte-identically in both runs).

**Honest findings for downstream laws.** The Cayo Santiago patch centre reads
Permanent water bodies (80) at 10 m in WorldCover v200 2021 — the source
classification puts the exact coordinate in the water at the islet's margin; the
`work.environment.terrain` ground-class dispatch must treat this pixel's law as
water until a measured shore offset says otherwise. Records stay `extracted`:
proven intake, never verification.
