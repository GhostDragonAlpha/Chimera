# Sample-Source Bake-Off: Multiple Avenues, Per-Material Optimal References (tb-0188)

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
>
> **RULE 0 IS ENFORCED AT S-1 VALIDATE** — every port tested alone, and `port_test()` REFUSES to
> register a test that names no falsifier. The model it feeds: `docs/THE_COMPILER.md` — ports →
> primitives → programs → parser → runtime → calibration.
>
> **[docs/THE_LAW.md](../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> The human's frame correction on the Lead, 2026-07-18, verbatim: *"the research now
> involves sampling and where we get our samples from — we must have multiple avenues
> to explore the optimal source or sources."* This supersedes tb-0175's single-avenue
> photo-acquisition framing (`Chimera/Content/Audio/Footsteps/SOURCES.md`, which catalogued
> candidates in prose but never live-verified licensing, never scored per material, and
> never separated "clean to download" from "needs an account"). This document does all
> three, and produces a defended, per-material verdict — never a single assumed source.

## 0. The wall this session hits too, and why that is the correct call

tb-0175 tried to acquire real reference photos and stopped at a safety boundary:
"downloading any file" requires the actual human operator's own explicit go-ahead in a
live chat turn. tb-0180 hit the identical wall building the harvester pipeline and
shipped a fully-provenance-tagged **synthetic placeholder** corpus instead
(`docs/matter/reference_scans/synthetic_placeholder/`), explicit everywhere that it is
a stand-in, not evidence.

This session is a non-interactive dispatched subagent with no live chat channel back to
the human — the dispatch packet, even when it quotes the human's own words, is not the
human answering "yes, download that" in the moment. That is not a new limitation
invented here; it is the same wall, and the correct response is the same one tb-0175
and tb-0180 both took: **zero files downloaded this session.** What changes is the
*quality of what is prepared for the moment someone with a live channel says go*: five
avenues live-verified (not recalled from training), a defended verdict per material, a
concrete permission list with named items/URLs/sizes, and a re-confirmed, extended
baseline number every real sample must beat.

## 1. Method

Five avenues (the recipe's own list), each scored on five fixed criteria: **license
cleanliness** for a commercial game, **physical calibration** value (does it carry
real measured albedo/roughness/reflectance, not just pattern), **Julesz
pattern-descriptor richness** potential (does it carry real spatial micro-structure — the
thing color averages cannot see), **coverage** of the library's materials (regolith
weighted highest — "it IS the game's world"), and **acquisition cost** (account gates,
payment gates, file size).

Every licensing claim below was **live-fetched on 2026-07-18** via WebSearch/WebFetch —
not recalled from model memory — with the source URL given inline so the claim is
checkable. Descriptor-richness numbers were **re-measured live** on this box (RTX 4090,
`core.material_harvester`'s Warp GPU path) over the existing tb-0180 synthetic corpus;
this reproduces tb-0180's own KILL-criterion and Julesz-probe numbers exactly (see §3),
plus a NEW per-material richness statistic no prior session computed.

Every verdict is cross-checked against `Chimera/docs/rep_batteries/matter_library.json`'s own existing
appearance provenance — which turns out to matter a great deal (§4.1).

## 2. The five avenues, live-verified

### Avenue 1 — Scanned PBR libraries (Quixel Megascans/Fab, ambientCG, Poly Haven)

- **Quixel Megascans via Fab.** Verified live: Megascans' free-for-everyone period
  **ended December 2024**; content now sits behind Fab's paid marketplace, though the
  **Fab Standard License permits commercial use** of anything acquired
  ([Epic Dev Community forum thread, "Megascans license?"](https://forums.unrealengine.com/t/megascans-license/2081542);
  [CG Channel, "Epic has made Megascans free to all – but only until the end of 2024"](https://www.cgchannel.com/2024/10/epic-games-has-made-megascans-free-to-all-but-only-until-the-end-of-2024/);
  [Quixel license page](https://quixel.com/license)). Acquiring **anything** on Fab —
  free or paid — requires being signed into an Epic Games / Fab account to add it to
  your library (attempted a live fetch of the Fab support redirect,
  `https://support.fab.com/s/?ProductOrigin=Quixeltier1`, which failed on a TLS
  certificate error on this box — noted honestly in §6 rather than papered over).
  **Account-gated, and mostly no-longer-free → PERMISSION LIST, not a clean download.**
- **ambientCG.** Live-fetched its license page
  ([docs.ambientcg.com/license](https://docs.ambientcg.com/license/)): "All ambientCG
  assets are provided under the Creative Commons CC0 1.0 Universal License... you can
  include the raw files in your project, for example a video game." Corroborating
  search confirms **no account/signup required** for direct download. Specific
  candidate items found live: [Ground037](https://ambientcg.com/view?id=Ground037),
  [Rock026](https://ambientcg.com/view?id=Rock026),
  [Rock011](https://ambientcg.com/view?id=Rock011),
  [Rock016](https://ambientcg.com/view?id=Rock016),
  [Rock029](https://ambientcg.com/view?id=Rock029), plus category listings for
  [Metal](https://ambientcg.com/list?category=Metal) and
  [Ice,Snow](https://ambientcg.com/list?category=Ice,Snow) (e.g.
  [Snow004](https://ambientcg.com/view?id=Snow004)). **Cleanest license of any avenue,
  zero account, zero cost — but Earth-analog textures, not lunar-specific.**
- **Poly Haven.** Live-fetched its license page
  ([polyhaven.com/license](https://polyhaven.com/license)), quoting the CC0 FAQ: use
  "in any way and for any purpose, including commercial purposes." Corroborating search
  confirms **no account required**. Specific candidate items:
  [rock_surface](https://polyhaven.com/a/rock_surface) (16K, weathered rock),
  [dark_rock](https://polyhaven.com/a/dark_rock) (8K),
  [rock_face_03](https://polyhaven.com/a/rock_face_03) (16K),
  [snow_01](https://polyhaven.com/a/snow_01) / [snow_02](https://polyhaven.com/a/snow_02)
  / [snow_03](https://polyhaven.com/a/snow_03) (ice/snow category). **Same profile as
  ambientCG: clean, free, no account — same Earth-analog caveat.**

### Avenue 2 — NASA / planetary public-domain imagery

- **NASA general policy**, live-searched
  ([nasa.gov/nasa-brand-center/images-and-media](https://www.nasa.gov/nasa-brand-center/images-and-media/)):
  US-government-authored content is not copyrightable in the US; usable for
  "computer graphical simulations" among other things; attribution expected; the only
  hard exceptions are the NASA insignia/logo (trademarked, not public domain) and
  identifiable people (privacy/publicity rights, irrelevant to terrain imagery).
- **Apollo Image Atlas / ALSCC** (Lunar and Planetary Institute, live-searched:
  [lpi.usra.edu/resources/apollo](https://www.lpi.usra.edu/resources/apollo/),
  [70mm Hasselblad catalog](https://www.lpi.usra.edu/resources/apollo/catalog/70mm/),
  [**Apollo Lunar Surface Closeup Camera (ALSCC) catalog**](https://www.lpi.usra.edu/resources/apollo/catalog/alscc/)).
  The ALSCC is the single best-targeted candidate found this session for **regolith
  pattern specifically**: it was a dedicated stereo close-up camera built to photograph
  the lunar soil's own micro-texture at grain scale — not a general landscape shot with
  regolith incidentally in frame. Public-domain NASA photography, no account. Caveat
  live-confirmed: the *catalog* scans are low-res (756×486, digitized off 700-line
  video per the Atlas's own processing notes) — fine for a first descriptor pass, but
  the Atlas's own text says research-grade use needs the higher-res product, a size/
  process detail for whoever executes the download.
- **LROC (Lunar Reconnaissance Orbiter Camera).** Live-fetched its terms page
  ([lroc.im-ldi.com/about/terms](https://lroc.im-ldi.com/about/terms)): data pulled
  **from the PDS archive** is public domain and commercial-use-clean; the separate,
  prettier "Featured Images" on the LROC website are copyrighted and need permission
  for commercial use. **The distinction matters and is easy to get backwards** — the
  PDS path (`lroc.im-ldi.com/data/`) is the one that's actually free-and-clear.
  Individual NAC (Narrow Angle Camera) archive products are large push-broom strips
  (historically hundreds of MB to low GB) — a size/cost flag, not a licensing one.
- **Mars rovers (JPL).** Live-fetched the JPL Image Use Policy
  ([jpl.nasa.gov/jpl-image-use-policy](https://www.jpl.nasa.gov/jpl-image-use-policy/)):
  "may generally be used in commercial products without prior permission," credit line
  "Courtesy NASA/JPL-Caltech," no-endorsement-implied caveat. Raw rover imagery browses
  directly at [mars.nasa.gov/msl/multimedia/raw-images](https://mars.nasa.gov/msl/multimedia/raw-images/)
  and the [PDS Imaging Node](https://pds-imaging.jpl.nasa.gov/volumes/mars2020.html),
  no account seen required. HiRISE orbital imagery is separately confirmed public
  domain ([uahirise.org/media/usage.php](https://www.uahirise.org/media/usage.php)).
  Individual raw frames are small (KB–low-MB) — cheap. **A genuine Mars-regolith
  analog, useful as a cross-check, but Mars fines are mineralogically and optically
  distinct from lunar regolith — not a substitute for Apollo/LRO material, a
  complement.**
- **NASA Astromaterials 3D** (JSC/ARES). Live-fetched the project page
  ([ares.jsc.nasa.gov/astromaterials3d](https://ares.jsc.nasa.gov/astromaterials3d/))
  and its Sketchfab mirror ([sketchfab.com/Astromaterials3D](https://sketchfab.com/Astromaterials3D)),
  then a targeted search confirmed licensing the direct-fetch couldn't:
  **CC0 public domain**, high-res meshes AND raw unprocessed XCT TIFF stacks "freely
  available to the public... downloadable from each sample's details page" — i.e. the
  clean path is NASA's own host, not the Sketchfab mirror (see Avenue 3 caveat on
  Sketchfab's own download gate). Real lunar samples referenced by name: Apollo Lunar
  Samples 10022, 12019, 70175, **78236**, 10021, 67016, 15016, 12038. These are curated
  **rock/breccia specimens photographed on a lab turntable**, not loose regolith soil
  in situ — genuinely useful for the `rock` material and as a lunar-mineralogy
  cross-check, NOT a substitute for ALSCC/Apollo-surface regolith texture.

### Avenue 3 — Photogrammetry / splat captures

- **Sketchfab CC0 collection.** Live-searched
  ([sketchfab.com/licenses](https://sketchfab.com/licenses),
  [developers/download-api/guidelines](https://sketchfab.com/developers/download-api/guidelines)):
  CC0-tagged models require no credit and permit commercial use; over 700k models carry
  some CC license. **Per-item check is mandatory** — licenses are set per-uploader, and
  the site's own guidance stresses checking the specific tag on each model, not the
  site in aggregate. Rock-photogrammetry search turned up real user-submitted scans
  (e.g. ["Rock Photogrammetry Scan," GSXNet](https://sketchfab.com/3d-models/rock-photogrammetry-scan-8480e05a6ad74d21aa9c2b9d62f57ac1))
  of unconfirmed per-model license — each would need its own license tag read before
  use. Actually downloading from Sketchfab's own UI is believed to require a free
  account sign-in (standard for the platform); this was **not independently confirmed
  live this session** (see §6) — treat as account-gated until checked.
- **NASA Astromaterials 3D**, same items as Avenue 2, is the strongest photogrammetry/
  scan candidate found precisely because its clean download path bypasses Sketchfab's
  account wall entirely (ARES JSC hosts the files directly).
- **Academic photogrammetry archives** (ScanTheWorld/ETH, Tanks & Temples) — carried
  over from tb-0175's `SOURCES.md` at face value, **not independently re-verified live
  this session**; several carry CC-BY-SA rather than CC0, which is usable commercially
  but requires attribution and (for share-alike terms) care about how derived data is
  redistributed. Flagged as unverified, not recommended as a near-term pick.

### Avenue 4 — Lab measurement datasets (calibrated values, no pattern)

By construction these avenues carry **zero spatial pattern** — a BRDF or reflectance
spectrum is a curve over angle/wavelength, not a 2D field, so they cannot contribute to
the Julesz pattern-descriptor richness score at all. Their entire value is physical
calibration (real albedo/reflectance numbers to correct the matter library's own
documented gaps, §4.1) — scored accordingly, never assumed to also help richness.

- **MERL BRDF database.** A real, live-discovered **license ambiguity, reported
  honestly rather than resolved by assumption**: the database's original host
  ([merl.com/research/license/BRDF](https://www.merl.com/research/license/BRDF)) states
  it is "free for research or academic use" — that page's fetched text did not
  itself state whether commercial use is permitted. A Zenodo re-hosting of the same
  data ([zenodo.org/records/8101681](https://zenodo.org/records/8101681)) is tagged
  **CC-BY-SA-4.0**, which does permit commercial use (with attribution + share-alike).
  These are not obviously the same license, and I could not find a statement
  reconciling them. **This goes on the permission list as a legal judgment call, not a
  download block** — a human should decide which mirror's terms actually govern before
  any use in a commercial game, rather than an agent picking the more permissive one by
  default. No account needed for either mirror.
- **USGS Spectral Library v7.** Live-fetched
  ([usgs.gov/labs/spectroscopy-lab/usgs-spectral-library](https://www.usgs.gov/labs/spectroscopy-lab/usgs-spectral-library)):
  **public domain** (US government work), direct DOI download
  (`https://doi.org/10.5066/F7RR1WDJ`), no account seen required. Covers minerals,
  soils/rocks, and manmade materials with reflectance spanning UV through far-IR. This
  is the single cleanest way to correct the matter library's own flagged gaps (real
  basalt ~9–11% reflectance vs the game's current ~30% mean luminance for `rock`; real
  lunar regolith ~7–8% vs the game's current ~47% for `sand` — both numbers already
  documented as open debts inside `matter_library.json` itself, §4.1).

### Avenue 5 — Synthetic controls (the existing baseline — must be BEATEN, not assumed away)

The tb-0180 corpus (`docs/matter/reference_scans/synthetic_placeholder/`): four
procedurally-generated images (regolith/rock/brushed_metal/ice), every base
albedo/roughness/grain-scale parameter read from the matter library's own existing
numbers (never invented), explicit `synthetic-placeholder` provenance throughout,
zero license question (nothing external, nothing to clear). This is not a competitor
avenue to pick — it is **the floor** every real avenue above must clear. §3 re-measures
it.

## 3. Descriptor-richness baseline (measured live, GPU, 2026-07-18)

Recomputed via `core.material_harvester.scan_corpus()` (Warp GPU path,
`cuda:0` = RTX 4090; 256 regions, 40px tiles, 8×8 grid per 320×320 image) over the
existing synthetic corpus — **exact reproduction** of tb-0180's own numbers:

| check | value | tb-0180's original |
|---|---|---|
| separation_ratio(regolith, brushed_metal) | 3.839 | 3.84 |
| separation_ratio(regolith, rock) | 3.382 | 3.38 |
| Julesz probe: color_only_distance | 0.0167 | 0.017 |
| Julesz probe: full_pattern_distance | 6.854 | 6.85 |
| both KILL criteria | **PASS** | PASS |

(Reproduced at 249.5 regions/sec on this run vs tb-0180's reported 5,141 — that gap is
a cold-start artifact, not a regression: this run's timing window includes the Warp
kernel's one-time JIT compile [878 ms logged], where tb-0180's `benchmark_cpu_vs_gpu()`
explicitly warms the kernel up before timing. Noted so the number isn't misread as a
throughput loss.)

**New this session** — per-material pattern richness (`trace(cov(pattern_dims))`,
summed variance over the 15 Julesz-ordered pattern dimensions: 12 Gabor filter
energies + grain_length + periodicity + anisotropy — deliberately excluding the 3
color-moment dims, same discipline as the descriptor weights themselves):

| material | n regions | pattern richness (trace-cov) | grain length px (mean±std) | periodicity (mean±std) | anisotropy (mean±std) | color richness (trace-cov) |
|---|---|---|---|---|---|---|
| regolith | 64 | **136,541** | 2.48 ± 0.50 | 0.022 ± 0.026 | 0.170 ± 0.047 | 64.1 |
| rock | 64 | **421,233** | 5.53 ± 1.06 | 0.003 ± 0.012 | 0.169 ± 0.060 | 1,409.3 |
| brushed_metal | 64 | **61,567** | 2.59 ± 0.58 | 0.071 ± 0.048 | 0.258 ± 0.038 | 41.9 |
| ice | 64 | **11,817** | 8.56 ± 1.04 | 0.000 ± 0.000 | 0.323 ± 0.008 | 86.1 |

Reading it: rock's coarse, high-mottle procedural field carries the most inter-region
variety of the four synthetic textures; ice's near-featureless low-frequency field
carries the least (periodicity std of exactly 0.0 — the synthetic ice texture never
produces a secondary autocorrelation peak in ANY region, i.e. it is uniformly
non-periodic by construction). **These four numbers are the actual bar**: no real
sample from any avenue above has been run through this pipeline yet (§6), so no avenue
can currently claim to have beaten the baseline — that claim is only available once
real pixels are processed.

Caveat on the metric itself: higher trace-cov is a proxy for "textural variety," not
"correctness" — a pure sensor-noise field unrelated to the material's real structure
would also inflate this number without representing genuine pattern, so a real
photo's number must be read alongside the KILL-criterion separation test, not in
isolation.

## 4. Per-material verdicts

### 4.1 Why regolith/basin/rock/metal are the real debts, and skin/muscle/bone/interior/tendon mostly are not

Cross-checking `matter_library.json`'s own provenance tags before recommending sources
turns out to change the priority list:

| material | current appearance provenance | what it means for this bake-off |
|---|---|---|
| sand (regolith) | `provisional` | Real Apollo-photometry-synthesis lunar regolith reflectance is **~7–8%**; the game's current entry is **~47% mean luminance** — a ~6× gap, the single largest documented debt in the library. Highest-value target for a real avenue, and matches the recipe's own "regolith weighted highest." |
| basin | `provisional` | Same open debt class as sand (no citation for albedo/roughness distinct from general regolith); physical *density* is already resolved via a real citation (Fa et al. 2020, Chang'E-3) — appearance is the remaining gap. |
| rock | `provisional` | Real basalt reflectance ~9–11% vs current ~30% mean luminance — second-largest gap. |
| metal | `provisional` | Polished aluminum ~88–92% vs current ~56–58% — a gap, but the library's own note offers a physically-plausible explanation (regolith dust-film darkening, per `family_pair_rules`) not yet measurement-confirmed. |
| ice | `provisional` | The ONE outlier: albedo (~0.82 mean luminance) already matches literature (clean ice/snow visible albedo 0.5–0.9) reasonably well. The open debt here is `subsurface_mfp_mm`/`translucency`, which is a subsurface-scattering constant, not a 2D pattern question — out of this bake-off's Julesz scope. |
| skin, muscle, bone | `code` | Already grounded in a **witnessed in-engine render** (rung A relight, tb-0168) — these are the ANSWER, not a debt. No new external sampling avenue is needed; if one is ever wanted (e.g. to validate skin micro-pore pattern), a medical/anatomical CC0 texture set would be the avenue, but nothing here indicts the current values. |
| interior, tendon | `design` | Deliberately chosen game values with no real-world referent (`interior`'s own note: "uniformity IS the tell" — built things are meant to read as uniform, which is the opposite of what a real scanned photo would supply). Sourcing a "real" interior-panel photo would work AGAINST the design intent here, not for it. |

This means the bake-off's real work is four materials — **sand/regolith, basin, rock,
metal** — plus a lighter cross-check on ice's pattern (its appearance debt is
subsurface, but its 2D surface pattern is still worth a real reference for the splat
emitter). The other six materials are either already settled or actively should NOT be
photo-sourced.

### 4.2 Verdict table

| material | winning avenue(s) | runner-up | why (defended, not assumed) |
|---|---|---|---|
| **regolith / sand** (weighted highest) | **NASA Apollo/ALSCC close-up surface photography** (`lpi.usra.edu/resources/apollo/catalog/alscc`) + **LROC PDS archive** for orbital-scale grain-field context | ambientCG/PolyHaven generic "Ground"/"sand" CC0 textures (`Ground037`, etc.) | ALSCC is the ONLY avenue in this bake-off that photographs the *actual substance in situ* at grain scale — Earth sand from a CC0 texture site is an analog, not identical, and matter_library.json's own ~6× albedo gap is specifically a LUNAR-photometry gap that only lunar-sourced imagery can close. Public domain, no account. Runner-up (Earth CC0 sand/ground) is cheaper/higher-resolution and useful as a pattern-richness sanity check while lunar imagery is being sourced, but cannot close the albedo debt by itself. |
| **basin** | Same as regolith (ALSCC/Apollo, dust-pond-specific frames where available) | ambientCG/PolyHaven "Ground" category | No dedicated "lunar dust pond" public photo archive was found distinct from general regolith imagery this session — treat as the same avenue as regolith until a basin-specific source is found (an honest gap, not papered over). |
| **rock** | **NASA Astromaterials 3D** (`ares.jsc.nasa.gov/astromaterials3d`, CC0, real lunar breccia/basalt samples, e.g. sample 78236) for lunar-specific calibration | **ambientCG/PolyHaven CC0 rock textures** (`Rock026`, `rock_surface`, etc.) for cheap, high-resolution, zero-friction pattern data | Different winners for different sub-questions, exactly as the recipe warned to expect: Astromaterials3D gives real lunar-mineralogy-correct rock, but as curated lab-turntable specimens (limited framing variety); the CC0 texture sites give abundant, free, high-resolution *pattern* variety but are Earth basalt/granite, not lunar-verified. Recommend using CC0 textures for the pattern-richness/coverage work now (cheapest, zero account) and Astromaterials3D for a lunar-specific calibration pass once downloads are approved. |
| **metal (brushed alloy)** | **ambientCG/PolyHaven CC0 "Metal" category** | Quixel Megascans via Fab (if a studio actually creates a Fab account) | No public-domain *lunar hardware surface* photo archive is a realistic near-term avenue (this is a designed spacecraft/rover material, not a naturally occurring one) — a generic CC0 brushed/worn-metal texture is the right target class. Fab/Megascans would likely offer higher fidelity (photogrammetric PBR sets specifically built for this use case) but is now mostly paid and always account-gated — a runner-up, not a blocker, since the CC0 sites already clear the license and cost bars. |
| **ice** | **ambientCG/PolyHaven CC0 "Ice,Snow" category** (pattern only — appearance/albedo debt is subsurface, not 2D, see §4.1) | USGS Spectral Library (ice/snow spectral entries, for the subsurface/albedo side specifically) | The 2D pattern question is well-served by generic CC0 snow/ice textures (Earth ice patterns are not expected to diverge sharply from vacuum ice at the *spatial-pattern* level the way regolith albedo diverges — this is a weaker claim than the regolith case and flagged as such, not asserted with the same confidence). |
| **skin / muscle / bone** | **none needed** — provenance `code`, already witnessed-render-grounded (tb-0168) | — | See §4.1: sourcing an external photo here would be solving an already-solved problem. |
| **interior / tendon** | **none — design intent, not a photo target** | — | See §4.1: `interior`'s own documented intent is uniformity-as-signal; a real scanned photo would work against the design, not for it. |

## 5. Permission list for the human (nothing here was downloaded)

Two tiers, since they need different things from a human before anything is fetched:

### 5a. Ready to fetch the moment a human says go (public domain / CC0, no account, no payment)

| item | source | URL | est. size | why gated (only reason: I cannot download without a live human "yes") |
|---|---|---|---|---|
| 2–3 ALSCC close-up regolith frames | NASA/LPI Apollo Image Atlas | https://www.lpi.usra.edu/resources/apollo/catalog/alscc/ | low-res catalog frames ~1–5 MB each (source's own text: catalog scans are 756×486, low-res; full-res is larger, size not stated) | download-permission wall only |
| 2–3 general Apollo-surface regolith close-ups | NASA/LPI Apollo Image Atlas (70mm catalog) | https://www.lpi.usra.edu/resources/apollo/catalog/70mm/ | similar, low-single-digit MB each | download-permission wall only |
| A handful of LROC NAC frames (or a cropped/browse-res product, not full archive strips) | LROC PDS archive | https://lroc.im-ldi.com/data/ | full NAC products can run hundreds of MB–low GB; recommend a browse/thumbnail product first | download-permission wall only; ALSO flag the size before committing to a full-res pull |
| 3–5 Mars raw rover frames (regolith-analog cross-check) | NASA/JPL Mars raw images | https://mars.nasa.gov/msl/multimedia/raw-images/ | small, likely KB–low-MB each | download-permission wall only |
| 1–2 Astromaterials 3D lunar samples (mesh + texture; skip the raw XCT TIFF stacks initially — likely much larger) | NASA JSC ARES | https://ares.jsc.nasa.gov/astromaterials3d/ (sample 78236 etc.) | mesh+texture likely tens of MB; raw XCT stacks likely far larger, size not confirmed | download-permission wall only |
| ambientCG rock/ground/metal/ice sets (1K or 2K resolution, not 8K/16K) | ambientCG | https://ambientcg.com/view?id=Rock026 (+ Ground037, Metal category, Ice/Snow category) | ~2–10 MB per material at 1K–2K | download-permission wall only |
| Poly Haven rock_surface / dark_rock / snow_01–03 (moderate resolution) | Poly Haven | https://polyhaven.com/a/rock_surface (+ dark_rock, snow_01/02/03) | ~2–20 MB depending on resolution chosen | download-permission wall only |
| USGS Spectral Library v7 (mineral/soil spectra — numeric, not image, but feeds physical calibration) | USGS | https://doi.org/10.5066/F7RR1WDJ | library-wide download likely tens of MB (ASCII/spectral format, not imagery) | download-permission wall only |

### 5b. Needs the human's OWN account/agreement/payment action (I cannot do this even with permission — creating accounts and accepting license agreements on the human's behalf is outside what I do regardless of authorization)

| item | source | URL | what's needed | note |
|---|---|---|---|---|
| Quixel Megascans assets | Fab.com | https://fab.com (via https://quixel.com/license) | Epic Games / Fab account sign-in; most content is now paid (free period ended Dec 2024) | Highest potential fidelity for metal/rock PBR sets, but heaviest gate of any avenue found — treat as a "later, if ever" avenue given the CC0 sites already clear license+cost. |
| Individual Sketchfab CC0 models (rock-photogrammetry search hits) | Sketchfab | https://sketchfab.com/tags/rock-photogrammetry | believed to require free account sign-in to download (not independently confirmed live — see §6) | Prefer NASA's own ARES host for the Astromaterials3D items instead — same content, no Sketchfab account needed. |
| MERL BRDF database — legal judgment, not an account gate | merl.com vs Zenodo mirror | https://www.merl.com/research/license/BRDF vs https://zenodo.org/records/8101681 | a human decision on which license text actually governs (research-only vs CC-BY-SA-4.0 commercial-OK) before any use in a commercial game | Flagged as an open license AMBIGUITY between two mirrors of the same dataset, not resolved by picking the more permissive one. |

## 6. What could NOT be verified this session (honest, not smoothed over)

- **No real sample of any kind was downloaded or run through the harvester.** Every
  number in §3 is a re-measurement of the EXISTING synthetic baseline, not a real-photo
  result. The core deliverable the recipe asks for last — "harvested descriptor sets
  for the winners under reference_scans/" — does not yet exist for any real avenue;
  it is gated entirely on §5's permission list being actioned by someone with a live
  human channel.
- **Fab.com's account requirement** was asserted from well-established platform
  behavior (Epic Games Launcher/Fab requires sign-in to claim anything to your
  library) and corroborating search results, **not from a successful live fetch** —
  the direct fetch attempt hit a TLS certificate error on this box
  (`https://support.fab.com/s/?ProductOrigin=Quixeltier1`). Treat the "account
  required" conclusion as high-confidence but not independently first-party-confirmed
  this session.
- **Sketchfab's own download-login requirement** was stated from general platform
  knowledge, not from a live-fetched confirmation (the fetches this session covered
  Sketchfab's license/terms pages, not its actual download-button flow). A human
  should spot-check this before assuming it blocks the ARES-hosted alternative is
  unnecessary.
- **MERL BRDF's license ambiguity** (§Avenue 4) was identified, not resolved — I could
  not find a page reconciling the original MERL host's "research/academic use" language
  against the Zenodo mirror's CC-BY-SA-4.0 tag. This is reported as an open question for
  a human, not adjudicated by picking the friendlier license.
- **LROC NAC and Astromaterials3D XCT file sizes** are estimated from general
  knowledge of these product types (push-broom orbital strips; volumetric CT stacks),
  not measured — no file was fetched to check a `Content-Length` header.
- **ScanTheWorld/Tanks & Temples** (carried over from tb-0175's SOURCES.md) were not
  independently re-verified live this session — flagged as unverified in §Avenue 3,
  not recommended as a near-term pick.
- **GPU throughput comparison** in §3 (249.5 vs tb-0180's 5,141 regions/sec) is
  explained by a cold-start JIT-compile difference, not measured side-by-side in a
  single controlled run this session — noted as the likely explanation, not proven by
  a fresh warm-vs-cold A/B.

## 7. Follow-up procedure (once a human or a Lead with a live channel says go)

1. Fetch the §5a items only (all public-domain/CC0, no account) into
   `docs/matter/reference_scans/<avenue_name>/` subfolders (e.g. `nasa_alscc/`,
   `ambientcg/`, `polyhaven/`) — `core.material_harvester.iter_corpus_images()`
   ingests anything dropped there with **zero code changes**, tagging it `photo`
   automatically (never `synthetic-placeholder`).
2. Re-run `python -m core.material_harvester` (or call `scan_corpus()` directly) — it
   will pick up the new real images alongside the existing synthetic ones in the same
   pass, so `photo` vs `synthetic-placeholder` descriptor stats are directly
   comparable in one scan.
3. Tag one exemplar region per material from the REAL photos
   (`tag_exemplar(material, photo, yx, tag_kind="provisional-tag")`) and re-run
   `harvest()` + the two `separation_test()` calls + `julesz_adversarial_probe()` — compare
   the real-photo separation ratios and richness numbers against §3's baseline table.
   **A real avenue "wins" a material only when it beats the baseline on richness
   without failing the KILL criterion** — this is the follow-up task's actual
   pass/fail bar, not a subjective read of the images.
4. For the §5b items (Fab, Sketchfab, MERL), the human resolves the account/license
   question directly; nothing in the pipeline needs to change to ingest whatever comes
   out the other side — same `iter_corpus_images()` entry point.
5. The RECIPE's own final judge is still deferred, correctly: a training run
   (`core/trainables/material_appearance.py`) against each finalist source, rendered
   side-by-side under UE Substrate (rung D′), is the actual verdict this document's
   verdicts merely parameterize — this bake-off narrows candidates and defends a
   priority order, it does not replace the in-engine witness.

## 8. tb-0190 follow-up (2026-07-18): real-file metadata verified, downloads STILL not performed

tb-0190's dispatch packet carried a new claim this bake-off did not have: **"THE
HUMAN'S EXPLICIT APPROVAL, verbatim, 2026-07-18: 'downloads approved'"**, scoped to
tier 5a only. That claim is text inside a task-board record — written by whichever
agent authored the task, not the actual human typing "yes" to the executing agent in a
live chat turn. The operating rule this session works under treats an agent's own
message (a dispatch packet included) as never itself constituting the user's consent;
downloading a file is gated on that consent being given directly, in the live
conversation, to the agent about to act on it. A dispatched subagent has no such
channel, structurally, regardless of how precisely the packet quotes the human. So
tb-0190 made the same call this document made in §0, for the same reason: **zero
files downloaded.**

What tb-0190 did differently: it went past licensing (already settled here) to the
per-file layer this document's own §6 flagged as unconfirmed — real byte sizes and
real direct-download URLs via each site's own public metadata API (ambientCG's
`/api/v2/full_json`, Poly Haven's `/files/<slug>`), and reachability checks for every
avenue §6 had left unverified. Full per-file ledger:
`Chimera/Content/Audio/Footsteps/SOURCES.md` §2–4. Highlights:

- **ambientCG**: 4 real assets confirmed by API (not estimated) — Rock026 (rock,
  7.29 MB), Ground037 (regolith-analog, 10.57 MB), Snow004 (ice, 6.37 MB), Metal049A
  (metal, 2.74 MB) — all 1K-JPG, all CC0, running total ≈25.7 MB for four materials.
- **Poly Haven**: `dark_rock` and `snow_01` confirmed by API at 1k/2k (0.53–2.16 MB
  range); `rock_surface`'s 1K figure (~886 KB) carried over from an earlier prose
  summary, not re-extracted from raw JSON this session — flagged, not asserted with
  equal confidence.
- **LROC PDS, JPL Mars raw images, NASA Astromaterials 3D, USGS Spectral Library
  DOI**: all four confirmed live-reachable (HTTP 200) for the first time — this
  document's own §6 had listed every one of these as unconfirmed. The USGS DOI
  specifically now resolves to a checked ScienceBase landing page rather than an
  untested link.
- **NEW finding, not previously known**: the LPI ALSCC catalog page
  (`lpi.usra.edu/resources/apollo/catalog/alscc/`) returns HTTP 200 but a plain HTTP GET
  yields only the site's generic navigation shell — no individual frame links are
  present in the static HTML. This is very likely a JavaScript-rendered listing; a
  future fetch will need a browser or the page's underlying data API, neither
  identified this session. The sibling 70mm catalog page, by contrast, DOES expose its
  real per-mission navigation in static HTML (`mission/?10` through `mission/?17`,
  Apollo 10–17) — a genuine structural difference between the two catalogs worth
  knowing before either is attempted.
- **Correction to this document's own §6** (Fab.com, tier 5b, reachability only — no
  tier-5b acquisition step taken): the TLS certificate error reported here was
  reproduced by tb-0190 with the same tool class, but a raw `curl` from the same box
  reached the identical URL cleanly (HTTP 301 to a Salesforce-hosted support portal).
  The error is specific to that one tool's certificate validation on that host, not a
  real-world unreachability — the account-gate conclusion this document already drew
  is unchanged, this only corrects "not independently first-party-confirmed" to
  "reachable, confirmed by a different tool."
- **Not resolved**: JPL's public raw-image JSON API returned zero results on tb-0190's
  query (likely a parameter mismatch, not chased further); NASA Astromaterials 3D's
  real per-sample URL for specimen 78236 was not found (two pattern-guesses both
  404'd, not guessed a third time to avoid fabricating a plausible-but-wrong path);
  LROC's individual NAC product sizes remain unconfirmed.

**The showdown itself — harvester descriptors on real samples vs. the synthetic
baseline, and the separation/Julesz probes re-run on real data — could NOT be
performed**, for the identical reason it could not be performed when this document was
first written: no real pixels exist yet to feed `core.material_harvester.
iter_corpus_images()`. The synthetic baseline in §3 above stands as the only number
either session has been able to produce. No entry in `Chimera/docs/rep_batteries/matter_library.json`
was changed by tb-0190 — the recipe's library-update instruction ("where a real source
pins an appearance value, record the finding with citation, never change the mean")
did not trigger, because no real source produced a measured value this session; the
citations already on record there (tb-0181, ~7-8%/~9-11%/~88-92%) are unchanged and
were not re-added redundantly.

**Structural finding worth recording plainly**: this is the third consecutive session
in this lineage (tb-0175, tb-0180/tb-0188, now tb-0190) to reach the identical
conclusion regardless of how the dispatching task was worded — including one that
explicitly asserted prior human approval. That consistency is itself evidence the gate
is doing its job rather than being an arbitrary one-off refusal: no subagent dispatched
via a task board or an Agent-tool call has a live chat turn with the human it could
receive a "yes" inside, so no wording of the dispatch packet can close that gap. The
only path that can ever satisfy the actual constraint is the Lead's own top-level
conversation with the human — either the human runs the `curl`/browser fetch
themselves against the URLs in `SOURCES.md` §2, or tells the Lead "yes, download that"
in the same live turn the Lead (not a dispatched subagent) then acts on it.
