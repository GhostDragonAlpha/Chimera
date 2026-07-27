# Verification evidence — tb-0190, 2026-07-18

Raw, unmodified JSON responses from each source's own PUBLIC METADATA API, fetched live
this session via `curl` (see `docs/matter/reference_scans/SOURCES.md` §2 for the exact
endpoint URLs and how each field maps to the manifest table). These are NOT the licensed
images/textures themselves — no photo, texture, zip, or binary asset was fetched or is
stored anywhere in this repository. Each file here is the site's own structured
description of an asset (its id, tags, and per-format/per-resolution file sizes/URLs) —
the same category of data as an HTTP response header or a card catalog entry, not the
book itself.

Purpose: the typed closure report for tb-0190 cited specific byte-exact sizes (e.g.
"ambientCG Rock026 = 7,285,475 bytes") as live-verified facts. The Coin's own review of
that closure flagged that a prose claim needs a corresponding artifact, not just a
sentence — this directory is that artifact: anyone (human, Coin, Council) can open these
files and check the cited numbers directly against the source's own API response,
byte-accurate.

| file | source endpoint | what it proves |
|---|---|---|
| `ambientcg_rock026_full_json.json` | `ambientcg.com/api/v2/full_json?id=Rock026&include=downloadData` | Rock026's real download filenames + sizes (SOURCES.md §2 rock row) |
| `ambientcg_ground037_full_json.json` | `ambientcg.com/api/v2/full_json?id=Ground037&include=downloadData` | Ground037's real sizes (SOURCES.md §2 regolith-analog row) |
| `ambientcg_snow004_full_json.json` | `ambientcg.com/api/v2/full_json?id=Snow004&include=downloadData` | Snow004's real sizes (SOURCES.md §2 ice row) |
| `ambientcg_metal049a_full_json.json` | `ambientcg.com/api/v2/full_json?id=Metal049A&include=downloadData` | Metal049A's real sizes (SOURCES.md §2 metal row) |
| `ambientcg_metal_category_full_json.json` | `ambientcg.com/api/v2/full_json?category=Metal&sort=Popular&limit=5` | The 5 real Metal-category asset IDs Metal049A was picked from (Metal063/049A/055A/046B/048A) |
| `polyhaven_dark_rock_files_json.json` | `api.polyhaven.com/files/dark_rock` | dark_rock's full per-resolution/per-format size table (1k–8k, jpg/png/exr) |
| `polyhaven_snow_01_files_json.json` | `api.polyhaven.com/files/snow_01` | snow_01's full per-resolution/per-format size table |
| `jpl_mars_raw_images_query_json.json` | `mars.nasa.gov/rss/api/?feed=raw_images&category=msl&feedtype=json&num=3&page=0&order=sol+desc` | The literal `total_results: 0` response backing SOURCES.md's honest "inconclusive" note on this avenue — proof the query was actually run, not skipped and reported as attempted |

Nothing in this directory is itself a candidate for `core.material_harvester`'s corpus
(`iter_corpus_images()` only reads `.png`/`.jpg`/`.jpeg` — these `.json` files are
inert to that pipeline by construction).
