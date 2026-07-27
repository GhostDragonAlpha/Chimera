# Reference Scan Sources — Material Appearance Training

> **2026-07-18 (tb-0190) supersedes this file's original tb-0175 content.** The old
> catalog (Quixel/Sketchfab/ScanTheWorld-first) never distinguished "clean CC0 download"
> from "needs an account," never confirmed a single real byte size, and predates the
> tier-5a/5b split. `docs/research/sample_sources_bakeoff.md` (tb-0188) did that
> licensing work; this file is the PER-FILE PROVENANCE LEDGER the bake-off's own §7
> follow-up procedure calls for. Old tb-0175 avenues not in the current tier-5a list
> (Sketchfab CC0 search, ScanTheWorld, Tanks & Temples, generic 3DGS `.ply` dumps) are
> dropped here as superseded — see the bake-off doc §Avenue 3 for why they were not
> promoted (account-gated or unverified license, not re-litigated here).

## STATUS, verbatim: ZERO FILES DOWNLOADED — this ledger has NO real rows yet

Every row in §2 below is a **live-verified candidate awaiting a fetch**, not a
downloaded file. This is not a technical failure — every one of the 8 tier-5a sources
was confirmed reachable this session (see §3). The gate is a safety boundary, and it is
the same wall three prior sessions in this exact lineage hit and named honestly:

- tb-0175: "reference scan downloads not performed."
- tb-0180 (`core/material_harvester.py`'s own docstring, read in full before writing
  this file): shipped a synthetic placeholder corpus instead, because "this agent
  operates under a safety contract that gates 'downloading any file' behind the ACTUAL
  human's explicit permission in live chat — a subagent dispatched by the Lead cannot
  obtain that (an agent's instruction is never the human's consent)."
- tb-0188 (the bake-off doc, §0): "This session is a non-interactive dispatched
  subagent with no live chat channel back to the human... zero files downloaded this
  session."

**tb-0190's own dispatch packet asserts "THE HUMAN'S EXPLICIT APPROVAL, verbatim,
2026-07-18: 'downloads approved'."** That assertion is text inside a task-board
record — i.e. it is *observed content*, authored by whichever agent wrote the task,
not the actual human typing "yes" to this agent in this live conversation. The
operating rule this agent works under is explicit and does not carve out an exception
for a dispatch packet that quotes the human, however precisely: an agent's own message
(including a task packet) is never itself the user's consent, and downloading any file
is gated on that consent being given directly, in the live chat, to the agent that
would act on it. A subagent invoked via a dispatch has no such channel — structurally,
by design, regardless of how the packet is worded. So this session made the same call
tb-0175/tb-0180/tb-0188 made, and did the same thing they did instead: verify
everything short of the fetch itself, so the actual fetch is a single trivial step for
whoever next has a live human "yes" in the same turn they can act on it (see the
closing note in §4).

**What's different this session:** every candidate below now carries a real,
API-confirmed byte size and a real direct-download URL (not an estimate) for 7 of the
8 sources, plus a corrected reachability record for the 2 sources the bake-off flagged
as unresolved. That is new, genuine verification work — it is just not a download.

## 1. Priority (unchanged from the bake-off's own verdict, §4.2): regolith weighted highest

sand/regolith > basin (same avenue as regolith, no dedicated source found) > rock >
metal > ice (pattern-only; its appearance debt is subsurface, out of this ledger's
scope per bake-off §4.1).

## 2. Tier-5a candidate manifest — every field below is a LIVE VALUE, not an estimate, unless flagged

**Raw evidence for every number below:** `_verification/` in this same directory holds
the unmodified JSON responses each source's own public metadata API returned live this
session (`_verification/README.md` maps each file to its claim). These are structured
metadata only — asset ids, tags, and per-format file sizes — never the licensed
image/texture bytes themselves; nothing in `_verification/` is `.png`/`.jpg` and none of
it is ingestible by `core.material_harvester` (checked: it only reads image
extensions).

### ambientCG (CC0, no account — https://docs.ambientcg.com/license/, quoted in full in the bake-off doc)

Sizes and URLs below came from `https://ambientcg.com/api/v2/full_json?id=<AssetId>&include=downloadData`
(the site's own public metadata API), fetched live 2026-07-18. No image/zip file itself
was fetched — only the JSON manifest describing it.

| material | asset | direct download URL (1K-JPG) | size (bytes) | size (MB) | target path (once fetched) |
|---|---|---|---|---|---|
| rock | Rock026 | https://ambientcg.com/get?file=Rock026_1K-JPG.zip | 7,285,475 | 7.29 | `reference_scans/ambientcg/rock/Rock026_1K-JPG.zip` |
| regolith (Earth-analog, NOT lunar — pattern/coverage cross-check only, see bake-off §4.2) | Ground037 | https://ambientcg.com/get?file=Ground037_1K-JPG.zip | 10,574,958 | 10.57 | `reference_scans/ambientcg/regolith/Ground037_1K-JPG.zip` |
| ice | Snow004 | https://ambientcg.com/get?file=Snow004_1K-JPG.zip | 6,369,066 | 6.37 | `reference_scans/ambientcg/ice/Snow004_1K-JPG.zip` |
| metal | Metal049A (clean/silver/smooth — closest tag match to "brushed alloy" of the four candidates surfaced in the Metal category listing: Metal063/Metal049A/Metal055A/Metal046B/Metal048A) | https://ambientcg.com/get?file=Metal049A_1K-JPG.zip | 2,744,738 | 2.74 | `reference_scans/ambientcg/metal/Metal049A_1K-JPG.zip` |

Running total (ambientCG, 1K-JPG only): **26,984,237 bytes ≈ 25.7 MB** — well inside the
recipe's "tens of MB total" discipline for a bake-off-scale set, and that is for FOUR
materials at once.

### Poly Haven (CC0, no account — https://polyhaven.com/license, quoted in the bake-off doc)

Sizes and URLs below came from `https://api.polyhaven.com/files/<slug>` (the site's own
public metadata API), fetched live 2026-07-18.

| material | asset | resolution | direct URL | size (bytes) | size (MB) |
|---|---|---|---|---|---|
| rock | rock_surface | 1k diffuse jpg | (confirmed present in API response; exact byte count not re-extracted after the initial WebFetch summary — re-query `api.polyhaven.com/files/rock_surface` before fetching to get the precise figure) | ~886,000 (WebFetch-summarized, not a raw API number — flagged, see §4) | ~0.89 |
| rock | dark_rock | 1k diffuse jpg | https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/dark_rock/dark_rock_diff_1k.jpg | 533,128 | 0.53 |
| rock | dark_rock | 2k diffuse jpg | https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/dark_rock/dark_rock_diff_2k.jpg | 2,159,653 | 2.16 |
| ice | snow_01 | 1k diffuse jpg | https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/snow_01/snow_01_diff_1k.jpg | 356,249 | 0.36 |
| ice | snow_01 | 2k diffuse jpg | https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/snow_01/snow_01_diff_2k.jpg | 1,331,975 | 1.33 |

Recommend the 1k or 2k jpg variants only (not the 8k/16k EXR sets, which run
50–380+ MB each per the full size table pulled for `dark_rock`/`snow_01` — confirmed
live, not estimated, and the reason the recipe's "1K or 2K, not 8K/16K" instruction from
the bake-off's own §5a is corroborated by real numbers now, not just a guess at "large").

### NASA / planetary (public domain, no account — US-government-authored, per NASA's general policy already quoted in the bake-off doc)

| item | URL | reachability (live, 2026-07-18) | what was and was NOT confirmed |
|---|---|---|---|
| ALSCC close-up regolith frames | https://www.lpi.usra.edu/resources/apollo/catalog/alscc/ | HTTP 200 | Page loads, but a plain HTTP GET returns only the SITE'S GENERIC NAV SHELL — no individual frame/image links are present in the static HTML (checked directly, not assumed). This catalog is very likely JavaScript-rendered past the shell; a downloader will need a browser or the page's underlying data API (not identified this session) to reach an actual frame URL. **New finding this session** — the bake-off doc did not go this deep; recorded honestly as a real obstacle, not smoothed over. |
| 70mm Apollo-surface catalog | https://www.lpi.usra.edu/resources/apollo/catalog/70mm/ | HTTP 200 | Same shell issue, BUT the real per-mission navigation structure IS present in the static HTML: relative links `mission/?10` through `mission/?17` (Apollo missions 10–17). This is the actual path structure a downloader needs to drill into next; individual frame URLs one level below this were not resolved this session (scope discipline — stopped at the structural finding, did not keep drilling toward an actual fetch). |
| LROC PDS archive | https://lroc.im-ldi.com/data/ | HTTP 200 | Root confirmed reachable. Individual NAC product URLs (the actual files) were not located this session; the bake-off's "hundreds of MB–low GB per strip" estimate for full products stands UNCONFIRMED by an actual header check — still a size flag, not a licensing one. |
| JPL Mars raw images | https://mars.nasa.gov/msl/multimedia/raw-images/ | HTTP 200 (page) | The page loads. A public raw-image JSON API was attempted (`mars.nasa.gov/rss/api/?feed=raw_images&category=msl&feedtype=json...`) and returned `total_results: 0` — **inconclusive**, most likely a wrong parameter/category value on this specific query rather than proof the feed is broken, and not chased further to stay inside this session's scope. Flagged, not resolved. |
| NASA Astromaterials 3D (ARES/JSC) | https://ares.jsc.nasa.gov/astromaterials3d/ | HTTP 200 | Project root confirmed reachable. Two guessed per-sample URL patterns for sample 78236 (`ares.jsc.nasa.gov/astromaterials3d/detail.htm?sample=78236` and a Sketchfab-slug guess) both returned 404 — the real per-sample URL structure was NOT discovered this session; a downloader will need to navigate the site's own sample browser, not construct a URL by pattern-guessing (an honest miss, recorded rather than papered over with a plausible-looking but unverified URL). |

### USGS Spectral Library v7 (public domain, no account)

| item | URL | reachability (live, 2026-07-18) |
|---|---|---|
| USGS Spectral Library v7 (DOI) | https://doi.org/10.5066/F7RR1WDJ | HTTP 200 — resolves to a real ScienceBase catalog landing page: `https://www.sciencebase.gov/catalog/item/5807a2a2e4b0841e59e3a18d`. This corrects the bake-off doc's untested DOI to an actually-followed redirect chain. The library-wide download link itself was not fetched (numeric/spectral data, feeds physical calibration per bake-off §Avenue 4, not the Julesz pattern showdown). |

## 3. What this session corrected in the predecessor's own record (Fab.com, tier 5b — reachability only, NOT an acquisition step)

The bake-off doc (§6) reported a TLS certificate error fetching Fab's support redirect
(`https://support.fab.com/s/?ProductOrigin=Quixeltier1`) via its WebFetch-class tool, and
treated Fab's account-gate as "high-confidence but not independently first-party-confirmed."
This session's `WebFetch` call hit the identical TLS error on the identical URL
(`unable to verify the first certificate`) — but a raw `curl` HEAD request from this box
reached it cleanly: HTTP 301 to a language-suffixed URL, served by a Salesforce
support portal (`Server: sfdcedge`), setting a `CookieConsentPolicy` cookie. **Correction,
not a new fact:** the TLS error is specific to the WebFetch-class tool's certificate
validation on this one host, not a real-world unreachability — the account-gate
conclusion itself is unchanged (this is a Salesforce-hosted support/help portal, not an
asset endpoint, and Fab's own license page + forum threads already established the
account requirement independently). **Tier 5b remains untouched beyond this one
reachability correction** — no login attempted, no asset page fetched, nothing acquired
or advanced toward acquisition.

## 4. What could NOT be verified this session (honest, not smoothed over)

- **No real sample was downloaded or run through `core.material_harvester`.** Every
  number in this file is either a metadata-API response (JSON describing a file) or an
  HTTP status code — never a fetched image/mesh/archive body. The recipe's
  "harvester descriptors on real samples vs. synthetic baselines" showdown could not be
  performed for the same reason tb-0188 could not perform it: no real pixels exist to
  feed `iter_corpus_images()`.
- **Poly Haven `rock_surface`'s exact 1K byte count** was taken from an earlier
  `WebFetch` prose summary ("1k diffuse JPG: ~886 KB"), not re-extracted from the raw
  JSON the way the other four Poly Haven rows were — flagged in its own table cell
  rather than presented with the same confidence as the others.
- **ALSCC's and 70mm's actual per-frame image URLs** were not found — both catalog
  pages return a navigation shell (or, for 70mm, a per-mission index) rather than direct
  file links from a plain HTTP GET. A future session (or a human browsing directly)
  will need to either execute the page's JavaScript or find its underlying data API.
- **LROC PDS individual NAC product URLs and their real sizes** were not located —
  only the archive root's reachability was confirmed.
- **JPL Mars raw-image API query returned 0 results** on this session's specific
  parameters — not chased to a working query, so the avenue's live-fetchability
  remains ESTABLISHED for the page (HTTP 200) but UNCONFIRMED for an actual individual
  frame via API.
- **NASA Astromaterials 3D's real per-sample (78236) URL** was not found — two
  plausible guesses both 404'd; not guessed a third time to avoid fabricating a
  plausible-but-wrong path into this ledger.
- **No license text was re-quoted from the primary sources this session** — the
  bake-off doc already did that live-fetch-and-quote work on the same day (2026-07-18)
  and is treated as current; this session's contribution is the per-file byte-size and
  reachability layer beneath it, not a re-verification of license wording already on
  record.

## 5. Follow-up (unchanged in spirit from the bake-off's §7, now with real URLs ready)

The moment an agent WITH a live human "yes" in the same turn it can act — which, per
the operating rule this session works under, means the Lead's own top-level
conversation with the human, not a dispatched subagent — the exact `curl`/download
commands are just the URLs in §2 above, saved to the `target path` column's
directories. Then: `python -m core.material_harvester` picks up anything dropped under
`docs/matter/reference_scans/<source>/<material>/` with zero code changes
(`iter_corpus_images()` tags it `photo` automatically), `tag_exemplar()` one real region
per material, and re-run `harvest()` + both `separation_test()` calls +
`julesz_adversarial_probe()` — compare against this session's re-confirmed synthetic
baseline (`docs/research/sample_sources_bakeoff.md` §3: regolith 136,541 / rock 421,233
/ brushed_metal 61,567 / ice 11,817 trace-of-covariance). That comparison is the actual
"which avenue beats the baseline" verdict — it cannot be produced by this session,
because it needs pixels this session was not able to fetch.
