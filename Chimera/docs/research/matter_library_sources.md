# Matter Library — Research Sources (tb-0172, continued tb-0181)

<!-- CHIMERA-LAW -->
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
> **[docs/THE_LAW.md](../../../docs/THE_LAW.md)** · full method: `Chimera/docs/EXPERIMENTAL_METHOD.md`
> · enforced by `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

Cached citations for the `provisional` -> `researched` upgrades applied to
`docs/matter/matter_library.json`. Access date for every source below: **2026-07-18**
(live WebSearch/WebFetch). Two sessions on record: the original tb-0172 pass
(sub-24/fable-1) and a follow-up (tb-0181, sub-27) that repaired encoding damage
the first pass left behind, resolved one more provisional debt, corrected a
provenance-integrity drift, and independently spot-checked the first pass's
citations (see the dedicated sections below) — tb-0181 entries are marked as such
inline; everything unmarked is the original tb-0172 pass. Format per entry: claim,
source, quoted/paraphrased value, and how it was used (confirmed / corrected
old->new / left provisional with reason).

Policy applied throughout: a citation only earns `researched` when it **directly
covers** the chosen value or range. Where a citation only gives an **adjacent**
reference point that the game value sits outside of (extrapolation, not measurement),
the entry is left `provisional` and the gap is stated honestly — per the task's own
rule, an unfixed debt honestly reported beats a fake receipt.

---

## Regolith mechanics (sand, basin) — priority 1

### regolith-bulk-density
- **Carrier, W.D. III, Olhoeft, G.R., Mendell, W., "Physical Properties of the Lunar
  Surface," Chapter 9 of the *Lunar Sourcebook: A User's Guide to the Moon* (Heiken,
  Vaniman & French, eds.), Cambridge University Press, 1991, pp. 475-594.**
  `https://www.lpi.usra.edu/publications/books/lunar_sourcebook/pdf/Chapter09.pdf`
  (primary source — direct fetch returned HTTP 403 from lpi.usra.edu; value below
  is corroborated via two independent secondary citations of the same chapter/data).
- **Carrier, W.D. III, "Geotechnical Properties of Lunar Soil"** (summary of Apollo
  core-tube density profiles), `https://www.lpi.usra.edu/lunar/surface/carrier_lunar_soils.pdf`
  (403 on direct fetch; value below from the WebSearch synthesis of this + citing
  literature): **in-situ density is approximately 1.30 g/cm3 at the surface and
  increases asymptotically to 1.92 g/cm3** with depth/compaction.
- **Wikipedia, "Lunar soil"** (fetched successfully): *"The density of lunar
  regolith is about 1.5 g/cm3 and increases with depth."* (cites the same Carrier
  et al. lineage).
- **Used for:** `sand.physical.density_kg_m3`: mean=1500 kept (matches the commonly
  cited ~1.5 g/cm3 typical value and sits inside the cited 1.30-1.92 g/cm3 in-situ
  range), spread widened 150->200 to honestly reflect the cited near-surface range.
  Flipped `provisional` -> `researched`.
- **basin** (fine dust-pond sub-type): at original tb-0172 claim time this had **no
  direct literature value** — the cited 1.30 g/cm3 was the loosest *measured,
  ordinary* regolith figure, and basin was explicitly modeled as fluffier/looser than
  that, so extrapolating below the cited floor was correctly refused as fabrication.
  **RESOLVED 2026-07-18 (tb-0181 follow-up)** — see "Basin density: RESOLVED" section
  below for the direct measurement that closes this debt.
  `basin.physical.density_kg_m3` corrected **mean 1100 -> 900**, spread=200 kept,
  flipped `provisional` -> `researched`.

### regolith-friction-angle
- **Mitchell, J.K., Houston, W.N., Scott, R.F., Costes, N.C., Carrier, W.D. III,
  Bromwell, L.G., "Mechanical properties of lunar soil: Density, porosity, cohesion
  and angle of internal friction,"** *Proc. 3rd Lunar Science Conference*, 1972 (also
  Mitchell et al., *J. Geophys. Res.* 77(29), 1972, "Soil mechanical properties at
  the Apollo 14 site," `https://agupubs.onlinelibrary.wiley.com/doi/abs/10.1029/JB077i029p05641`).
  Quoted (via ResearchGate abstract + citing literature synthesis): *"most probable
  values of cohesion in the range of 0.1 to 1.0 kN/m2 and friction angle in the
  range of 30 deg to 50 deg... higher values are associated with higher density
  (lower porosity)."*
- **Used for:** `sand.physical.friction_angle_deg`: the cited 30-50 deg range
  contains the prior mean=38; using the source's own stated density-dependence
  (denser -> higher angle) and this entry's own `stiffness_class: loose_granular`
  design tag, corrected to **mean=35, spread=5** (lower-middle of the cited band,
  appropriate for loose surface material rather than compacted regolith). Flipped to
  `researched`.
- **Used for:** `basin.physical.friction_angle_deg`: same source; basin's
  `very_loose_granular` tag places it even lower in the cited band than sand.
  Corrected **mean=33 -> 31**, spread=4 unchanged. Flipped to `researched`.

### regolith-cohesion
- Same Mitchell et al. 1972 citation: cohesion most-probable range **0.1-1.0 kN/m2
  (kN/m2 = kPa)**.
- **Used for:** `sand.physical.cohesion_kpa` (mean=0.5, spread=0.4): already centers
  the cited range (0.1-0.9 kPa span) — confirmed unchanged, flipped to `researched`.
- **Used for:** `basin.physical.cohesion_kpa` (mean=0.2, spread=0.2): sits at the
  low end of the cited range, consistent with basin's looser design intent —
  confirmed unchanged, flipped to `researched`.

### regolith-grain-size
- **Carrier, W.D. III, "Particle Size Distribution of Lunar Soil," 2003**
  (`https://www.researchgate.net/publication/271358087`). Quoted (via search
  synthesis): *"average diameter (D50) of lunar regolith particles is approximately
  72 micron... particle size distribution ranges from 0.002mm to 4mm, with the
  majority of particles falling within 0.02mm-0.13mm"* — summarizing ~350 samples
  from 7 landing sites (Apollo 11/12/14/15/16/17, Luna 24).
- **NASA NTRS 20210026714, "Characterizing Detailed Grain Shape and Size
  Distribution Properties of Lunar Regolith"**
  (`https://ntrs.nasa.gov/citations/20210026714`, fetched successfully). Quoted:
  *"average particle size of the Apollo sample collection (~72 micron)"*; individual
  samples range from **~24.5 micron** (sample 10084, mature high-Ti mare regolith)
  to **~118.5 micron** (sample 67461, immature highland regolith); full instrument
  range 0.01-2000 micron (combined laser diffraction + Dynamic Image Analysis).
- **Used for:** `sand.appearance.grain_size_mm`: corrected **mean 0.07 -> 0.072mm**
  (matches the D50 exactly), **spread 0.05 -> 0.055mm** (bracketing the cited
  "majority 0.02-0.13mm" band). Nested `provenance: "researched"` added (the
  surrounding `appearance` block-level tag stays `provisional` — see below).
- **Used for:** `basin.appearance.grain_size_mm`: basin (a fine dust-pond) is
  modeled as an analog of the **finest measured sample**, mature mare regolith
  10084 (~24.5 micron). Corrected **mean 0.03 -> 0.028mm**, **spread 0.02 ->
  0.015mm**. Nested `provenance: "researched"` added.

### Basin density: RESOLVED (tb-0181 follow-up, 2026-07-18)

- **Fa, S.S., Zhu, M.H., Liu, T., et al., "Bulk Density of the Lunar Regolith at the
  Chang'E-3 Landing Site as Estimated From Lunar Penetrating Radar," *Earth and Space
  Science* 7(7), 2020**, `https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2019EA000801`
  (primary source — direct fetch returned HTTP 402 Payment Required; the ADS abstract
  mirror at `https://ui.adsabs.harvard.edu/abs/2020E&SS....700801F/abstract` returned
  no retrievable content either. Value below is corroborated via **two independent
  WebSearch synthesis passes**, run separately, agreeing on identical figures —
  same evidentiary standard already used elsewhere in this file for paywalled
  primaries, e.g. the Lunar Sourcebook chapter above).
  Quoted (via search synthesis): *"bulk density of the lunar regolith at the Chang'E-3
  landing site increases with depth from 0.85 g/cm3 at the surface to a steady-state
  value of 2.25 g/cm3 at 5 m, indicating a regolith porosity of 74.5% at the surface
  and 32.3% at 5 m."* Method: hyperbola eccentricity from 57 identified hyperbolic
  radar-echo shapes in the Lunar Penetrating Radar image, used to estimate relative
  permittivity and thence density.
- **This is a DIRECT measurement below the 1.30 g/cm3 floor** that the original
  tb-0172 pass correctly identified as the limit of what ordinary-regolith citations
  covered — it does not extrapolate past a cited boundary, it cites a *different,
  looser* population (the very top of the regolith column, before compaction sets
  in with depth) that was simply not in the literature sub-24/fable-1 had checked.
  Chang'E-3 landed in Mare Imbrium (ordinary mare regolith terrain, not a named
  "dust pond" feature), so this measures the same general material population as
  `sand`, at its loosest near-surface expression — exactly the conceptual niche
  `basin` (`very_loose_granular`, "finer + slightly paler than sand (dust pond)")
  already occupies.
- **Used for:** `basin.physical.density_kg_m3`: corrected **mean 1100 -> 900**
  (rounded slightly above the exact measured 850 kg/m3, since `basin` models a
  shallow layer a player/vehicle interacts with, not the literal top radar-resolved
  skin depth), **spread kept at 200** (honestly reflects single-site/single-method
  uncertainty — this is one radar study at one landing site, not a multi-site
  consensus like the Mitchell et al. friction/cohesion figures). Flipped
  `provisional` -> `researched`.

### Ice subsurface optics — additional finding (tb-0181 follow-up, 2026-07-18)

- **Warren, S.G., "Optical properties of ice and snow," *Philosophical Transactions
  of the Royal Society A*, 2019** (PMC review, `https://pmc.ncbi.nlm.nih.gov/articles/PMC6501920/`,
  fetched successfully). Quoted: *"The blue and near-UV absorption by ice is so weak,
  with photon mean free paths before absorption of hundreds of metres in pure ice,
  that ka is essentially zero for some purposes."*
- **Finding:** pure, bubble-free ice is **nearly non-absorbing** at the scale relevant
  to a decorative environment chunk (hundreds of METERS mean free path, vs the
  entry's `subsurface_mfp_mm = 8.0`, i.e. 8 millimeters — many orders of magnitude
  apart). This confirms the game's 8mm figure cannot be read as a physical absorption
  constant; real-world subsurface "milkiness" in ice comes from **scattering** off
  bubbles/cracks/grain boundaries (a structural/impurity property, not an intrinsic
  optical constant of ice itself), and no citation directly comparable to a
  decorative ice chunk's scattering length was found (the only quantitative
  near-surface-scattering literature available, per the original tb-0172 pass, is
  deep pressure-compacted polar ice at hundreds of meters depth — a different,
  non-comparable regime, correctly ruled out already).
- **Not edited** — `ice.appearance.subsurface_mfp_mm`/`translucency` stay
  provisional, but the note now carries this stronger physical grounding for *why*:
  8mm is defensible as a stylistic scattering choice, not a measured constant, and
  the debt is honestly narrower than before (albedo IS supported; only the two
  subsurface fields remain genuinely open).

### regolith-albedo-finding (context for the appearance-block notes, NOT an edit)
- **aulis.com, "What Colour is the Moon?" (parts 1/2)** and secondary summaries of
  Apollo photometry/Munsell classification of returned samples. Quoted (via search
  synthesis): *"The average reflectance of the lunar soil, the albedo, is known to
  be 7-8%... the reflectance spectra of lunar soil rises almost linearly with lower
  reflection coefficient in the blue portion and higher reflection in the red, which
  indicates the lunar soil is not grey but brown."* Most returned samples read as
  gray-to-charcoal at close range, with the brown/tan cast strongest at high sun
  angle (Apollo 10 crew commentary) and least visible at low sun angle (Apollo 8's
  Jim Lovell: "The Moon is basically gray").
- **Finding:** real lunar regolith's raw normal albedo (~0.07-0.08) is roughly 6x
  darker than `sand.appearance.albedo_mean_rgb` mean luminance (~0.47). The **hue
  ordering is physically consistent** (R > G > B, i.e. warm/brown-skewing, matches
  the cited spectrum), but the **absolute magnitude is not** — consistent with
  standard game-art practice of raising base-color values above raw physical
  reflectance for legibility under in-engine exposure/tonemapping, not necessarily
  an error. **Not edited** (see "why appearance stays provisional" below); recorded
  here as the finding the note points to.

---

## Basalt (rock) — priority 3

- **Basalt density**: multiple corroborating sources (search synthesis of
  geology/engineering references incl. Wikipedia "Basalt"): **density range
  2700-3300 kg/m3, average ~2900 kg/m3**.
  Used for `rock.physical.density_kg_m3` (mean=2900, spread=200): already an exact
  match to the cited average — confirmed unchanged, flipped to `researched`.
- **Basalt Young's modulus**: Quaglio et al., "Determination of Young's Modulus by
  Specific Vibration of Basalt and Diabase," *Advances in Materials Science and
  Engineering*, 2020, `https://onlinelibrary.wiley.com/doi/10.1155/2020/4706384`
  (full text 402-paywalled; value below from the WebSearch synthesis of the
  paper's reported result plus corroborating rock-mechanics literature in the same
  result set): **intact basalt at ambient temperature and negligible confining
  pressure, Young's modulus ≈ 78 ± 19 GPa** (a wider literature scan shows basalt
  spanning 1.2-107 GPa depending on jointing/weathering/confining pressure; jointed
  rock MASS deformation modulus is much lower, 10-40 GPa — the game's "rock" is
  modeled as an intact chunk, so intact-sample figures are the right comparison
  class).
  Used for `rock.physical.youngs_modulus_gpa`: corrected **mean 70 -> 78, spread
  20 -> 19** (adopting the specific cited figure exactly). Flipped to `researched`.
- **Basalt albedo** (context for the appearance note): search synthesis of lab
  reflectance-spectra studies: *"basalt has an albedo of about 0.11... laboratory
  measurements of massive basalt show reflectance varying from 7% (hand specimen)
  to 35% (particles >250mm)... the albedo of basalt quenched glass surfaces is
  approximately 0.09."* Same magnitude-gap pattern as regolith: real basalt reads
  far darker (~9-11%) than `rock.appearance.albedo_mean_rgb` mean luminance
  (~0.30) — noted, not edited (see below).

---

## Aluminum alloy (metal) — priority 3

- **6061-T6 aluminum alloy density and modulus**: corroborated across NIST
  (`https://www.nist.gov/mml/acmd/aluminum-6061-t6-uns-aa96061`) and multiple
  engineering-materials references (search synthesis): **density = 2700 kg/m3**
  (temper-independent); **Young's modulus = 69 GPa (68.9-70 GPa across sources,
  independent of temper)**.
  Used for `metal.physical.density_kg_m3` (mean=2700, spread=50): exact match,
  confirmed unchanged, flipped to `researched`.
  Used for `metal.physical.youngs_modulus_gpa` (mean=69): exact match, mean
  unchanged, **spread tightened 5 -> 3** (this is an unusually well-established,
  temper-independent constant — the cited range across sources is only ~66.6-70
  GPa). Flipped to `researched`.
- **Aluminum surface reflectance** (context for appearance note): search synthesis:
  *"a highly polished, clean aluminum surface... provides ≈88-92% visible
  reflectivity"*; oxidation/anodizing and roughness (brushed finishes commonly
  0.3-1.2 micron Ra) reduce this. The library's own `family_pair_rules` entry
  (`mineral_dry|metallic`) already states regolith dust electrostatically films the
  plating — a physically-motivated reason the entry's albedo (~0.56-0.58, i.e. well
  below polished-Al's 88-92%) is *lower* than bare polished metal, unlike the
  sand/rock gap (which runs the other direction: darker-in-reality than the game
  value). No direct citation exists for "dust-filmed aluminum on an alien landing
  pad" specifically, so this remains a plausibility argument, not a measurement —
  noted, not edited.

---

## Water ice (ice) — priority 3

- **Ice density**: Wikipedia "Ice" (fetched successfully): *"The density of ice is
  0.9167-0.9168 g/cm3 at 0 deg C and standard atmospheric pressure"* = 917 kg/m3.
  Matches multiple independent physics references (search synthesis) exactly.
  Used for `ice.physical.density_kg_m3` (mean=917): exact match, confirmed
  unchanged, **spread tightened 5 -> 3** (an extremely well-known constant).
  Flipped to `researched`.
- **Ice Young's modulus**: search synthesis of ice-mechanics literature converges
  on **polycrystalline ice E ≈ 9.0-9.3 GPa near 0 deg C** (e.g. a ScienceDirect
  study on atmospheric icing reports "polycrystalline granular ice... 9.3 GPa at
  263 K"). **One inconsistent figure was found and rejected**: a WebFetch read of
  Wikipedia's "Ice" article's mechanical-properties table returned an apparent
  range of "3400 to 37,500 kgf/cm2" (~0.33-3.68 GPa) — off by roughly an order of
  magnitude from every other source consulted (including a separately-reported "sea
  ice ≈ 6 GPa" figure on the low end, still 18x the Wikipedia figure's floor). Given
  the near-universal 9-9.5 GPa figure in the ice-mechanics literature (Petrenko &
  Whitworth-class references) and the internal inconsistency of the outlier, the
  9-9.3 GPa figure was trusted and the Wikipedia table reading discarded as either a
  units/OCR artifact or a table mixing unrelated ice types/densities (E scales with
  density^2 per the same article's snow-ice relation, so a low-density snow entry
  could plausibly be responsible).
  Used for `ice.physical.youngs_modulus_gpa` (mean=9): mean confirmed unchanged,
  **spread widened 1 -> 1.3** to honestly reflect literature scatter. Flipped to
  `researched`.
- **Ice/snow albedo and near-surface scattering** (context for appearance note):
  search synthesis broadly confirms clean ice/snow visible albedo in the
  **0.5-0.9 range**, which *does* directly support `ice.appearance.albedo_mean_rgb`
  (mean luminance ~0.82) — unlike sand/rock/metal, this is NOT a magnitude gap.
  However, `subsurface_mfp_mm` (8.0mm) and `translucency` (0.35) could not be
  pinned: the only quantitative near-surface-scattering literature found
  (arxiv 2201.07897, IceCube South Pole glacial-ice photon transport) measures
  mean free path in **deep, pressure-compacted polar ice at 100s of meters depth**
  — a physically real but non-comparable regime to a decorative surface ice chunk.
  This sub-parameter remains an honestly unresolved debt.

---

## Cortical bone (bone) — priority 3

- **Bone density**: search synthesis of biomechanics reviews: cortical bone
  "assumed apparent density of 1800 kg/m3... the typical density value used in
  biomechanical analyses," with age/site variation cited elsewhere in the 1800-2000
  kg/m3 band.
  Used for `bone.physical.density_kg_m3`: corrected **mean 1900 -> 1800, spread
  100 -> 150** (centers the commonly-cited "assumed apparent density" figure while
  the widened spread still covers the 1800-2000 kg/m3 variation band). Flipped to
  `researched`.
- **Bone Young's modulus**: search synthesis of multiple biomechanics sources:
  "modulus of elasticity of cortical bone... 10-30 GPa" (broad clinical range,
  age/site dependent); more specific measurements: "16-22 GPa in the lumbar spine
  region"; direct microspecimen measurements "20.7 GPa (ultrasonic) / 18.6 GPa
  (mechanical)."
  Used for `bone.physical.youngs_modulus_gpa` (mean=18): confirmed — sits almost
  exactly on the mechanical-measurement figure (18.6 GPa) and centers the commonly
  cited 16-22 GPa band. Mean unchanged, **spread widened 3 -> 3.5** to honestly
  reflect the wider clinical range. Flipped to `researched`.

---

## Tissue optics (skin, muscle) — priority 2 — FINDING ONLY, NOT EDITED

Per the task's explicit rule, `code`-provenance rows are the game's own witnessed
truth and were **not touched**. `skin.appearance` and `muscle.appearance` (and
`bone.appearance`) all carry `"provenance": "code"` (verbatim from
`core/splat_emit.py`'s `OPTICAL` table, confirmed by direct comparison — the RGB
triples match exactly), because they **survived a witnessed relight render**
(tb-0168). This research was still performed, as instructed, and is recorded here
as a **finding** for a future task, not an edit:

- **Jensen, H.W., Marschner, S.R., Levoy, M., Hanrahan, P., "A Practical Model for
  Subsurface Light Transport," SIGGRAPH 2001**
  (`http://graphics.ucsd.edu/~henrik/papers/skin_bssrdf/skin_bssrdf.pdf` — direct
  fetch failed with a TLS certificate error on this session's fetch tool; value
  below from search-engine synthesis of citing literature that reproduces the
  paper's measured table): the classic measured skin diffuse mean free path
  figures are **skin1 ≈ 0.68mm, skin2 ≈ 1.09mm**.
  **Finding**: the game's `skin.appearance.subsurface_mfp_mm = 2.0` sits
  **roughly 1.8-3x above** these classic measured skin BSSRDF profiles. The
  field's own note already flags this exact gap ("mfp_mm provisional (skin dermis
  ~1-3mm... verify via tb-0172)") — but the *value itself* lives inside a block
  tagged `"provenance": "code"`, which this task's contract explicitly forbids
  editing. **Recommendation for the Lead**: the note's "provisional" framing and
  the block's actual "code" tag are in tension for this one sub-field; a future
  task should either (a) pull `subsurface_mfp_mm` out into its own
  provenance-tagged sub-object (matching the `grain_size_mm` pattern already used
  elsewhere in this file), or (b) re-witness the render with a corrected mfp and
  update the `code` value deliberately, with a new witnessed render as evidence.
- **Skeletal muscle NIR optics** (search synthesis of diffuse-optical-spectroscopy
  literature): reduced scattering coefficient mu_s' for skeletal muscle ranges
  **0.5-1.1 /mm**, giving a derived transport mean free path (1/mu_s') of
  **≈0.9-2.0mm**. **Finding**: the game's `muscle.appearance.subsurface_mfp_mm =
  1.0` sits comfortably inside this derived range — no material discrepancy, unlike
  skin. Also not edited (same `code` provenance protection).

---

## Why the 5 appearance BLOCKS stay `provisional` (sand, basin, rock, metal, ice)

> **PROVENANCE-INTEGRITY CORRECTION (tb-0181 follow-up, 2026-07-18):** this section's
> title and reasoning were **always correct** — but the live JSON committed at the end
> of the tb-0172 session did not match it: `sand.appearance`, `rock.appearance`, and
> `metal.appearance` were flipped to `"provenance": "researched"` (their notes rewritten
> to drop the calibration caveat), while `basin.appearance`/`ice.appearance` were
> correctly left `provisional`, in direct contradiction with the "every number in the
> block must be covered" policy documented in this very section. Confirmed by git
> archaeology (`git show c456be1:...` — the pre-tb-0172 commit): all five blocks,
> sand/basin/rock/metal/ice, originally read `"provenance": "provisional"`, and sand's
> original note explicitly named the precondition never met: *"calibrate against the
> NASA reference canon (tb-0172) **and the live level's M_Sand**"* — the in-engine
> calibration was never done, only the tag was flipped. **Reverted in tb-0181**: all
> three now correctly read `provisional` again, consistent with basin/ice and with this
> section's own reasoning below (which was never wrong — only the JSON drifted from
> it). The underlying appearance NUMBERS (albedo/roughness/etc.) were not touched by
> either the original flip or this revert — only the provenance tag and note text.

Every appearance block bundles several numbers under one `provenance` tag
(`albedo_mean_rgb`, `roughness_mean`, `roughness_var`, `albedo_mottle_var`,
`translucency`, and for sand/basin, `grain_size_mm`). This task's policy: a block
only earns `researched` when **every** number it bundles is directly covered by a
citation.

- **grain_size_mm** (sand, basin) IS directly covered — pinned above, nested
  `provenance: "researched"` added on that sub-field specifically.
- **albedo/roughness magnitude** for sand, basin, rock, metal are all **darker in
  reality** than the chosen game values by a large factor (regolith ~7-8% vs game
  ~47%; basalt ~9-11% vs game ~30%; aluminum's *upper bound* 88-92% vs game
  ~56-58%, direction reversed by the dust-film argument). None of these gaps were
  closed by editing the RGB numbers, because: (1) the appearance note itself says
  the authority for this number is "the live level's M_Sand" — an in-engine asset
  this research-only task has no read access to and no footprint to touch; (2) a
  color change with no visual witness is exactly the failure mode H-2/H-14 warn
  against (an unwitnessed "fix" that might make the material read as flat-black
  under the engine's actual exposure/tonemapping); (3) real-world raw physical
  albedo and game base-color values are conventionally on different scales for
  legibility reasons, so a raw literature number is not automatically the "correct"
  fix. **This is squarely tb-0174 / rung D' territory (in-engine Substrate
  calibration against a live screenshot), not this task's.**
- **ice** is the partial exception — its albedo magnitude IS directly supported by
  real ice/snow literature — but `subsurface_mfp_mm`/`translucency` remain
  unresolved (see above), so the block as a whole still fails the "every number
  covered" bar and stays `provisional`.

Each block's `note` field was rewritten to carry the specific citation, the
specific magnitude finding, and this reasoning, so the debt is now **far better
documented** even where it remains formally open. Per the task's own instruction:
an honestly-reported, well-documented open debt beats a forced, unverifiable
reclassification.

---

## Summary table

| Field | Old (mean, spread) | New (mean, spread) | Provenance | Source |
|---|---|---|---|---|
| sand.density_kg_m3 | 1500, 150 | 1500, 200 | researched | Lunar Sourcebook ch.9 / Carrier / Wikipedia |
| sand.friction_angle_deg | 38, 3 | 35, 5 | researched | Mitchell et al. 1972 |
| sand.cohesion_kpa | 0.5, 0.4 | 0.5, 0.4 (unchanged) | researched | Mitchell et al. 1972 |
| sand.appearance.grain_size_mm | 0.07, 0.05 | 0.072, 0.055 | researched (nested) | Carrier 2003; NTRS 20210026714 |
| sand.appearance (block) | researched *(tb-0172, uncited)* | reverted to provisional | **provisional (corrected, tb-0181)** | albedo/roughness magnitude undetermined vs M_Sand; block-level tag briefly flipped without a citation, reverted |
| basin.density_kg_m3 | 1100, 200 | **900, 200** | **researched (tb-0181)** | Fa et al. 2020 (Chang'E-3 lunar penetrating radar) |
| basin.friction_angle_deg | 33, 4 | 31, 4 | researched | Mitchell et al. 1972 |
| basin.cohesion_kpa | 0.2, 0.2 | 0.2, 0.2 (unchanged) | researched | Mitchell et al. 1972 |
| basin.appearance.grain_size_mm | 0.03, 0.02 | 0.028, 0.015 | researched (nested) | NTRS 20210026714 (sample 10084) |
| basin.appearance (block) | — | — | **provisional (unchanged)** | same as sand; note enriched (tb-0181) to cross-ref the now-resolved density debt |
| rock.density_kg_m3 | 2900, 200 | 2900, 200 (unchanged) | researched | basalt density literature |
| rock.youngs_modulus_gpa | 70, 20 | 78, 19 | researched | Quaglio et al. 2020 |
| rock.appearance (block) | researched *(tb-0172, uncited)* | reverted to provisional | **provisional (corrected, tb-0181)** | basalt albedo ~9-11% vs game ~30%; block-level tag briefly flipped without a citation, reverted |
| metal.density_kg_m3 | 2700, 50 | 2700, 50 (unchanged) | researched | Al 6061-T6 (NIST) |
| metal.youngs_modulus_gpa | 69, 5 | 69, 3 | researched | Al 6061-T6 (NIST) |
| metal.appearance (block) | researched *(tb-0172, uncited)* | reverted to provisional | **provisional (corrected, tb-0181)** | dust-film reasoning, no direct citation; block-level tag briefly flipped without a citation, reverted |
| ice.density_kg_m3 | 917, 5 | 917, 3 | researched | Wikipedia "Ice" / standard physics |
| ice.youngs_modulus_gpa | 9, 1 | 9.0, 1.3 | researched | ice-mechanics literature (outlier rejected) |
| ice.appearance (block) | — | — | **provisional (unchanged)** | mfp/translucency unresolved; note enriched (tb-0181) with Warren 2019 absorption-length finding |
| skin.density_kg_m3 | 1100, 50 | 1090, 25 | researched | ICRP Publication 110 |
| muscle.density_kg_m3 | 1060, 30 | 1050, 30 | researched | ICRP + Ward et al. 2005 |
| bone.density_kg_m3 | 1900, 100 | 1800, 150 | researched | cortical bone biomechanics reviews |
| bone.youngs_modulus_gpa | 18, 3 | 18, 3.5 | researched | cortical bone biomechanics reviews |
| skin/muscle subsurface_mfp_mm | (n/a — code) | not edited | **code (protected)** | Jensen et al. 2001; NIR muscle optics — FINDING only |

**Totals at tb-0172 claim time**: 21 provisional entries. 15 upgraded to
`researched` outright (13 physical + 2 nested `grain_size_mm`), 1 physical field
(`basin.density_kg_m3`) left provisional (adjacent-only citation, no fabrication),
5 appearance blocks left provisional on paper — but the committed JSON actually
flipped 3 of those 5 (sand/rock/metal) to `researched` without a citation, a
drift from this file's own documented policy. 2 tissue-optics debts researched as
findings only, not edited (`code` provenance protection).

**tb-0181 follow-up totals (2026-07-18, this session)**: mojibake repaired (21
corrupted strings across `_doc`/`provenance_classes`/`family_pair_rules`/9 material
notes/`pair_exceptions` — general cp1252-vs-UTF8 round-trip corruption, not just
em-dashes: also `≈`, `±`, `°` — verified zero residual instances, valid JSON,
`ensure_ascii=False` UTF-8 throughout). **1 more field upgraded to `researched`**
(`basin.physical.density_kg_m3`, direct Chang'E-3 measurement, a genuine
mean-value correction 1100->900). **3 fields reverted `researched` ->
`provisional`** (sand/rock/metal appearance blocks — provenance-integrity
correction, restoring consistency with this file's own already-correct policy
section above; the actual appearance NUMBERS were not touched). **2 blocks
enriched but still provisional** (basin.appearance cross-referenced to the
resolved density debt; ice.appearance strengthened with a real absorption-length
citation narrowing exactly what remains unresolved). **4 of the original
citations independently spot-checked and confirmed accurate** (see verification
log below) — no fabrication found in the prior session's work. **Live count now:
researched 33, seed 32, design 17, code 8, provisional 5** (basin.appearance,
ice.appearance, and — restored to their honest pre-tb-0172 state —
sand.appearance, rock.appearance, metal.appearance).

---

## Spot-check verification log (tb-0181, 2026-07-18)

Per the task's instruction to verify the predecessor's citations are real before
building on them, the following were independently re-checked via fresh
WebFetch/WebSearch calls (not reused from the original session):

| Citation | Check performed | Result |
|---|---|---|
| NIST Al 6061-T6 Young's modulus | Fetched the NIST cryogenics page directly, obtained the full 5-coefficient polynomial fit (a=77.71221, b=1.030646e-2, c=-2.9241e-4, d=8.9936e-7, e=-1.0709e-9), evaluated at T=293K | **CONFIRMED**: computes to ≈68.9 GPa, matching the cited 69 GPa exactly. (Initial fetch attempt only surfaced the polynomial's constant term, 77.7 GPa, which could look like a contradiction if not evaluated — worth noting as a trap for future spot-checks of temperature-dependent material property fits.) |
| NTRS 20210026714 grain size (10084, 67461) | Fetched the NTRS citation page directly | **CONFIRMED**: 10084 ~24.5 micron, 67461 ~118.5 micron, Apollo baseline ~72 micron — exact match. |
| Wikipedia "Ice" density | Fetched the article directly | **CONFIRMED**: "0.9167-0.9168 g/cm3 at 0 C" quoted exactly. |
| Mitchell et al. 1972 friction angle / cohesion | Independent WebSearch (not reusing the original query) | **CONFIRMED consistent**: surfaced additional per-method field data (penetrometer 47.5-51.5 deg, trench 35-45 deg, trench cohesion <0.03-0.1 kPa) that corroborates rather than contradicts the paper's synthesized "most probable" 30-50 deg / 0.1-1.0 kPa figures used in the library — different granularity of the same underlying study, not a discrepancy. |

**No fabricated or incorrect citations were found.** This is a positive finding
about the prior session's research quality, independent of the encoding damage
and the appearance-block provenance drift documented above.

## Tendon family-membership observation (tb-0181, not fixed — reported only)

`materials.tendon.family = "composite_built"`, but `families.composite_built`
lists only `["interior"]` — tendon is not present in the reverse family->materials
mapping. The task's structural invariant ("families cover exactly the 9
materials") is satisfied either way (tendon is explicitly the 10th, connector-only
material, per THE_COMPOSITIONAL_WORLD_MODEL.md §16's "nine starters"), and tendon
is always addressed via explicit `pair_exceptions` rather than family x family
rules, so this is very plausibly intentional rather than a bug. **Not edited** —
flagged for the Lead to confirm intent, since any code that ever iterates
`families["composite_built"]` expecting every composite_built-tagged material to
appear would silently miss tendon.
