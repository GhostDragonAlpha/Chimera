# work.environment.terrain — source research and contract draft (worker notes)

Date: 2026-09-17. Base commit a6e6acf26dacb37be9f42c2589f4417ae38247d5.
Full deliverable is the worker's final message; this file is the working copy.

## Repo facts read (read-only)
- tools/science_funnel/earth_scene.py — source_parameters(): WGS84 (a=6378137.0 m, 1/f=298.257223563) parsed
  from pinned NGA page; NASA Glenn troposphere fit; receipt pattern download_receipt.json {path,bytes,sha256,url};
  local_frame() geodetic->ECEF treats altitude_m as WGS84 ELLIPSOIDAL height; frame local_EUS (east,up,south).
- model.environment.earth_patch contract: schema chimera.earth_patch.v1, tick 300 Hz, lat 0.0, lon 100.0 (open
  ocean W of Sumatra — must be re-authored for any land tile), patch_half_width_m 1.2, defaults slope_deg 0,
  friction 0.4, assumptions "Planar rigid ground; ... Coulomb friction".
- ChimeraEngine/engine/graph_earth.hpp — ground(x,z)={x, tan(slope)*x, z}; 12x12 render tiling; "visually tiled
  without inventing terrain scans". Contact plane: contact_plane_height_m, normal [0,1,0] (frictionless qualified).
- Coupled contact evidence: worst_gap_m 4.15e-7, worst_absolute_error 1.27e-11; earth regression checks
  unilateral_contact, support_load_mg pass.

## Candidates
1. Copernicus DEM GLO-30 Public (AWS Open Data mirror) — RECOMMENDED.
   - registry.opendata.aws/copernicus-dem: bucket copernicus-dem-30m (eu-central-1), "No AWS account required",
     COGs, "available on a free basis ... under the terms and conditions of the Licence".
   - dataspace.copernicus.eu COP-DEM page: "The GLO-30 and GLO-90 datasets are available worldwide with a free
     license."; CRS horizontal "WGS84-G1150 (EPSG 4326)", vertical "EGM2008 (EPSG 3855)", vertical unit meters,
     DGED grid alignment RasterPixelIsPoint; GLO-30 1.0" (~30 m), 1x1 deg tiles, GeoTIFF float32; ABS vertical
     accuracy < 4 m LE90; DSM not bare earth; attribution notices required (DLR/Airbus/COPERNICUS lines).
   - Per-tile XML (fetched, N18W066): horizontalDatumCode WGS84-G1150, verticalDatumCode WGS84-G1150 (EOXML
     quirk — ESA page governs: EGM2008 heights), 1.0" spacing, verticalSpacing 0.1 m, spec TD-GS-PS-0021 v3.0.
   - Tile naming: Copernicus_DSM_COG_10_{N|S}dd_00_{E|W}ddd_00_DEM/..._DEM.tif (lon zero-padded to 3 digits —
     W066 not W66; first query failed for this reason).
   - VERIFIED TODAY 2026-09-17: HEAD Copernicus_DSM_COG_10_N18_00_W066_00_DEM/Copernicus_DSM_COG_10_N18_00_W066_00_DEM.tif
     -> HTTP 200, Content-Length 7,406,696 B, Content-Type image/tiff, Last-Modified 2022-05-09 (2021 release).
2. NASADEM_HGT v001 (MEaSUREs, LP DAAC): 1" (30 m), 60N-56S, HGT tiles (s16i2 m), EGM96 vertical + WGS84
   horizontal (per independent study d-nb.info/1277240469/34 citing LP DAAC docs); "openly shared, without
   restriction, in accordance with the EOSDIS Data Use and Citation Guidance"; Earthdata Login (free auth).
3. SRTMGL1 v003 (LP DAAC): 1" (30 m), 60N-56S, HGT int16 m, DOI 10.5067/MEASURES/SRTM/SRTMGL1.003; same EOSDIS
   sentence; vertical datum EGM96 per SRTM User Guide V3 (page itself silent — flag); Earthdata auth.
4. USGS 3DEP / The National Map: public domain ("USGS-authored or produced data and information are considered
   to be in the U.S. Public Domain." — usgs.gov copyrights page); 1/9" (~3 m), 1/3" (~10 m), 1" (~30 m), 1 m lidar;
   NAD83 horizontal, NAVD88 vertical (bare-earth); apps.nationalmap.gov/downloader (no login); US/territories
   only — covers Puerto Rico, hence cross-check for Cayo Santiago.
5. ASTER GDEM v003 (ASTGTM): 1" (~30 m), 83N-83S, GeoTIFF, EGM96 vertical (CMR C1711961296-LPCLOUD);
   "available at no charge for any user pursuant to an agreement between METI and NASA" (asterweb.jpl.nasa.gov/
   gdem.asp); v3 used ASTWBD to flatten water anomalies (Abrams 2020, mdpi.com/2072-4292/12/7/1156);
   accuracy class ~20 m @95% (Athmania & Achour 2014) — last-resort fallback only.

## Recommendation
- PRIMARY: Copernicus DEM GLO-30 Public via AWS bucket (no auth, COG, per-tile EOXML, stable 2021 release).
- TILE: Copernicus_DSM_COG_10_N18_00_W066_00_DEM (covers 18-19N, 66-65W).
- PATCH CENTER candidate: Cayo Santiago rhesus colony, PR — 18.1565N, 65.7350W (island at 18°09'23"N
  65°44'03"W; final centre nudged within the island flat by the measured-tilt admission check).
- Datum recording: keep tile height H in its NATIVE orthometric datum (EGM2008) + pinned undulation N +
  conversion law h = H + N; scene frame stays WGS84 ellipsoidal (altitude_m is ellipsoidal per local_frame).
  Geoid grids: PROJ us_nga_egm2008_25.tif / us_nga_egm96_15.tif (NGA models, matching the NGA-pinned datum).
- Units: EPSG:4326 degrees horizontal, metres vertical; DEM vertical quantization 0.1 m.
- Grid metric at 18.156N: 1" = 30.75 m (N-S, meridional M) x 29.42 m (E-W, N·cosφ). Patch 2.4 m = 0.08 cell —
  patch sits inside ONE cell; heightfield over patch is a bilinear patch of 4 surrounding samples.

## Reduction law (draft)
0 PIN: GET tile + EOXML + WBM water mask; record URL/date/length/sha256/ETag; refuse on drift (receipt pattern).
1 GEOREFERENCE: read geotransform from the file (RasterPixelIsPoint per ESA DGED); do not assume corner vs center.
2 WINDOW: 5x5 samples (~+/-65 m) around centre — minimal window containing the patch plus a full ring of
  second differences for the holdout test. Refuse if any sample is nodata (-32767) or water-masked.
3 VERTICAL: h = H + N(EGM2008) at centre; N pinned (record model + sha256); two implementations must agree.
4 REDUCE: bilinear interpolation in local east/north metres (degrees->metres via WGS84 M and N radii).
5 HOLDOUT: every 2x2 cell: centre sample vs mean of 4 corners; pointwise bound |e| <= (|dxx|+|dyy|)/8 from the
  cell's second differences (standard bilinear remainder, no free parameter); RMS reported.
6 PLANE: least-squares plane over the 2.4 m patch -> tilt theta + residual recorded as OBSERVATION. Contact
  plane height := interpolated height at centre; normal STAYS [0,1,0]; theta is NOT consumed by the solver in
  this slice. A tilted/curved contact surface is a NEW qualification with its own falsifier (support deficit
  1-cos(theta) vs measured cell normals).
7 PROVENANCE: tile sha256, geoid grid, centre, window, method id, heightfield -> graph source node + receipt;
  any bit change flips scene_sha256 (existing digest pattern).

## Scoped falsifiers (draft, 6)
1. Tile pin integrity: re-GET byte-identical (sha256 + 7,406,696 B observed 2026-09-17).
2. Interpolation: all holdout centres within derived bound; RMS reported; violation -> tile rejected.
3. Vertical datum: two independent EGM2008 implementations agree within 0.1 m (= DEM's own vertical quantization).
4. Cross-source: NASADEM(EGM96) vs GLO-30(EGM2008) window medians within combined stated envelopes
   (4 m + 16 m LE90 class); failure exposes DSM/bare-earth or geoid surprises.
5. Planarity/contact scope: measured patch tilt 1-cos(theta) <= 1e-3 (theta <= 2.56 deg) for admission; contact
   regressions (unilateral_contact, support_load_mg, worst_gap 4.15e-7 m) pass UNCHANGED with plane at terrain height.
6. Provenance closure: every sampled height traceable by sha256 chain; flipping any input flips scene_sha256.

## Ambiguities (state plainly)
- EOXML verticalDatumCode reads WGS84-G1150 while ESA page says EGM2008 heights — EOXML field carries the
  horizontal datum code; falsifier 3 resolves it empirically at pinning.
- AWS bucket = GLO-30 Public 2021 release; CDSE hosts newer editions (2024_1) behind free registration — the
  pin names the AWS object; do not chase editions silently.
- GLO-30 and NASADEM/SRTM are RADAR SURFACE models (DSM), 3DEP is bare earth — at 30 m postings the difference
  is inside the cross-source envelopes; recorded as assumption, tested by falsifier 4.
- SRTMGL1 earthdata page does not state its vertical datum; the SRTM User Guide V3 does (EGM96) — cite the guide.
- 3DEP 1 m over PR post-Maria: existence to verify at implementation (TNM downloader); 1/3" PR coverage is certain.
