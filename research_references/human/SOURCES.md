# HUMAN DATA — the measured source base

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
> **[docs/THE_LAW.md](../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 25 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> Built 2026-07-30 on the operator's steer: "for a human body it's so complicated we're going to
> need actual sources for all the concepts — I don't like all this guessing." Every body concept
> derives from one of these, or says why it can't. Scope note (the operator): realistic human
> with realistic biology and physics, genitalia omitted — the standard rating convention.

## Tier 0 — IN THE REPO NOW

| source | what it measures | status |
|---|---|---|
| `external/myo_sim` (**MyoSuite MyoSim**, Caggiano et al. 2022, arXiv:2205.13600, Apache 2.0) | the full musculoskeletal model: 26 bodies, 113 geoms, **290 muscles** with measured Hill parameters; legs from Rajagopal et al. 2016 (OpenSim), arms from Saul et al. 2015 | PRESENT. **Verified against our splat pipeline 2026-07-30** (`tools/verify_myo_splat.py`, A/B vs MuJoCo renderer: same body, blind-eye agrees) |
| `research_references/human/ANSUR_II_MALE_Public.csv` (4,082 subjects) + `ANSUR_II_FEMALE_Public.csv` (1,986) | **93 direct anthropometric measurements per subject** (mm): stature, segment lengths, breadths, circumferences, sitting heights — the dimensional truth of human bodies | DOWNLOADED (mirror of the Penn State OPEN Design Lab release; US Gov work, public since 2017) |
| `research_references/human/opensim/` — Rajagopal2016, Hamner2010, gait2392 (Thelen 2003 muscle), arm26 (.osim) | the measured musculoskeletal parameters myo_sim is built on: muscle origins/insertions, optimal fibre lengths, pennation, max isometric forces (162 muscle defs in Rajagopal alone) | DOWNLOADED (opensim-org/opensim-models, BSD) |
| `research_references/human/mocap/` — 35_01_walk.bvh, 35_08_jog.bvh (CMU MoCap, subject 35) | **real human movement**: full-skeleton walk + jog trials at 120 Hz — the trainer's reference footage, not our own render's self-image | DOWNLOADED (CMU MoCap via the una-dinosauria BVH mirror; original: mocap.cs.cmu.edu, free with citation) |
| `research_references/human/gait_osf/` → **`story/data/gait_normative.json`** (Van Criekinge et al. 2023, OSF doi [10.17605/OSF.IO/T72CW](https://doi.org/10.17605/OSF.IO/T72CW), CC BY 4.0) | **THE NORMATIVE GAIT: 246 healthy adults aged 18–91**, three self-selected speeds, joint angles / moments / powers / GRF at every percent of the cycle, plus spatiotemporal parameters — **grouped by sex and age decade**, and per-subject mass, stature and **leg length** | **INGESTED 2026-07-30** (`tools/ingest_gait_osf.py`; `--check` re-derives and diffs). Raw workbooks gitignored, the extracted table is committed |
| `research_references/human/skin_optics_omlc_jacques.html` | **measured skin light model** (Jacques, OMLC): melanin absorption `μa.mel = 6.6×10¹¹·λ⁻³·³³ cm⁻¹`, melanin fractions by pigmentation class (1.3–43%), baseline + reduced-scattering power law — the body's measured reflection, per the operator's light rule | ARCHIVED |
| `research_references/human/hemoglobin_extinction_prahl.json` (OMLC, Prahl compilation of Gratzer + Kollias data) | **molar extinction of oxy/deoxy hemoglobin, 250–1000 nm in 2 nm steps** (376 rows) — the missing `μa.blood` half of the Jacques model (his Figure 2 was an unarchived GIF); converts with `μa = 2.303·e·x/64500`, whole blood x=150 g/L | DOWNLOADED 2026-07-31 (https://omlc.org/spectra/hemoglobin/summary.html) |
| **ACQUISITION SWEEP 2026-07-31** — the full membrane→physics→data map is **`ACQUISITION_PLAN.md`**; bulk downloads below are gitignored raw stores, extracted tables get committed as `story/data/*.json` | | |
| `mocap/cmu_full/` — **CMU MoCap complete** (2,548 BVH trials, 113 subjects, via the una-dinosauria mirror) | every movement class the story uses: crouch-walk (136_09+), crawl (111_03, 133_01), jumps (13_39+, 16_22+), climb (01_02+), sit (13_01+), walk/run 90° turns (16_17+, 16_41+) — feeds theStance, theBalance, theThrust, A3+G2, A5+G1, B2 | DOWNLOADED 2026-07-31. License: free for research AND commercial inclusion; may not resell the data itself; credit mocap.cs.cmu.edu + NSF EIA-0196217 |
| `eye/` — CIE 1924 photopic V(λ), CIE 1951 scotopic V′(λ), CIE 1931 XYZ CMFs, Stockman-Sharpe cone fundamentals (CVRL); Navarro 2009 eye review (CC); Villaseñor-Mora 2009 skin IR emissivity 0.98±0.01; Hecht 1937 dark adaptation (PMC) | the measured functions of vision: brightness weighting day/night, spectral→LMS, retinal image formation, dark-adaptation time-course | DOWNLOADED 2026-07-31 (theEye's data, membrane still stub) |
| `eva/` — NASA EMU Data Book Rev V 2017; NASA CR-1726 reduced-gravity handbook 1971; NASA TN D-7883 Apollo metabolic 1975; NASA EVA Hardware & Ops 2012 | the suited human measured: EMU mass properties, 4.3 psia, metabolic envelope 1000–2000 Btu/hr, SAFER 24 N₂ thrusters; walk/jump performance vs g-level tables; measured Apollo EVA metabolic rates | DOWNLOADED 2026-07-31 (US Gov public) |
| `grip/` — NHANES 2011+2013 grip-strength raw trials (n≈7,800/cycle, XPT); Mathiowetz adult norms PDF | population grip/pinch strength distributions by age/sex — derive our own norms from raw trials | DOWNLOADED 2026-07-31 (US Gov public domain; XPT readability verified: 8,291 rows, 2013 cycle) |
| `skin_friction/` — Zhang & Mak 1999 measured skin μ tables; Elkington 2024 rubber-vs-granite (CC BY); Carré 2017 gloves-vs-steel PDF; OMLC Hale & Querry water μa + van Veen fat μa | measured friction for theGrip's contact law; tissue spectra extending theSkin's light model | DOWNLOADED 2026-07-31 |
| `partial_g/` — MacLean & Ferris 2021 (figshare): 12 subjects × 4 gravity levels (1/0.76/0.55/0.31 g) × 4 speeds, GRF + mocap + EMG (.mat) | the only raw multi-gravity human gait dataset — theThrust's partial-g locomotion truth | DOWNLOADED 2026-07-31 |
| `balance/` — HBEDB 1,930 quiet-stance trials (figshare CC BY 4.0 mirror, 376 MB); dos Santos 2017 dual-plate + whole-body kinematics (7.4 GB raw) | measured postural sway: COP spectra, Romberg ratio, per-foot load split | DOWNLOADED 2026-07-31 (zips verified) |
| `jump/` — loaded CMJ / squat jump / 30 s Bosco force plates (figshare CC BY 4.0); MoveSmart Zenodo (CC0, 166 MB): 1000 Hz force plate walk/jog/run + 20 cm drops | jump force-time curves, landing impact 2.5–4× BW — theThrust's takeoff/landing truth | DOWNLOADED 2026-07-31 (zips verified) |
| `research_references/optics/refractiveindex.info-database/` — 3,135 measured n,k records over 605 materials (Scientific Data 2024) | **measured optical constants for every surface in every future game** — visor glasses (full Schott/Ohara catalogs), metals, water/ice | DOWNLOADED 2026-07-31, **CC0** |

## Tier 1 — PUBLIC, FETCHABLE (no license wall)

| source | what it is | access |
|---|---|---|
| **ANSUR II** full report + data dictionary (Paquette et al., Natick) | measurement definitions + procedures for the CSVs above | https://www.openlab.psu.edu/ansur2/ |
| **Visible Human Project** (NLM) | CT + MRI + **cryosection** of a male (1 mm) and female (0.33 mm) — real anatomy in cross-section: organs, muscle paths, bone | since 2019 **no registration** — NLM FTP terms (https://www.nlm.nih.gov/research/visible/getting_data.html) |
| **CMU MoCap database** | ~2,600 motion-capture trials of real people walking/running/sitting — the movement truth for gait work | http://mocap.cs.cmu.edu/ (free, with citation) |
| **OpenSim models** (Stanford; Rajagopal 2016 gait model, Hamner 2010 running) | the measured musculoskeletal parameters myo_sim is built on: muscle origins/insertions, optimal fibre lengths, pennation, max isometric forces | https://github.com/opensim-org/opensim-models (BSD) |

## Tier 2 — LICENSE-GATED (needs the operator's click)

> **Commercial warning added 2026-07-31** (ACQUISITION_PLAN.md Tier C): AMASS, SMPL/SMPL-X,
> GRAB, MANO are **non-commercial-research-only**; InterHand2.6M and DexYCB are CC BY-NC.
> Nothing derived from them may ship in a sold game. The clean commercial spine is CMU mocap
> (commercial inclusion allowed), NASA + NHANES (public domain), CC0/CC-BY datasets, and
> digitized published tables. Treat the MPI/Meta sets as validation references at most.

| source | what it is | gate |
|---|---|---|
| **SMPL / SMPL-X** (Loper 2015; Pavlakos 2019, MPI) | the standard learned body: 6,890-vertex skinned mesh, shape + pose blend shapes **learned from thousands of real 3D scans (CAESAR)** — realistic skin surface, realistic variation | free for research, license acceptance at https://smpl.is.tue.mpg.de/ |
| **CAESAR** (SAE International) | 4,300 civilians 3D-scanned + 99 measures — civilian (not military) body truth | purchase from SAE |
| **AMASS** (Mahmood 2019, MPI) | every big mocap set unified under SMPL — ~40 h of real motion | research license at https://amass.is.tue.mpg.de/ |

## What feeds what (the wiring)

- **Dimensions** (how long, how wide, how heavy a person is): ANSUR II — distributions, not one
  "average". The body's membranes derive from measured percentiles, never guessed lengths.
- **Muscles + skeleton** (what pulls what): myo_sim (present, verified) backed by OpenSim numbers.
- **Skin surface** (what the eye meets): SMPL when licensed; until then the verified myo_sim
  geometry is the visual truth, and the membranes say so.
- **Motion** (how a real walk looks): **the OSF normative set is now the walk itself**, not a
  reference to compare against — `theHuman` reads its hip, knee, ankle and ground-reaction curves
  directly, and derived walking speed selects the shape between the three measured conditions.
  CMU MoCap / AMASS remain for movements it does not cover (jog, sit, reach).
  **Retired by it:** `swing = 0.42 rad`, `DUTY = 0.60`, the three hand-placed rocker fractions, the
  1.2-body-weight ground reaction, and the 0.10-of-stature forefoot lever. The lever is now derived
  as `τ/F` from two of the study's own curves and comes out at **0.071**.
- **Insides** (breath, blood, the loop): Visible Human cross-sections + the standard physiology
  numbers (already cited inside `theBreath`/`theSweep`).
