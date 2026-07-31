# HUMAN ACQUISITION PLAN — every membrane, its physics, its training data

> Built 2026-07-31 on the operator's ruling: **research must connect the physics to the
> training data; effort is spent on a subject ONCE and then reused infinitely, morphed onto
> other things; everything we make is just light and physics.** This file is the complete
> map for the human — complete enough that any future game draws from it untouched.
>
> The pattern per membrane: **physics law** (a published measured model) ← **training data**
> (measured instances, downloaded once) → **extraction** (distilled to `story/data/*.json`,
> committed; raw downloads gitignored) → **proof through the engine**. A membrane never
> ships a typed constant where a measured distribution exists below.

## THE MEMBRANE MAP

| membrane | the physics it must know | training data (measured) | status |
|---|---|---|---|
| **theHuman** (dimensions) | segment lengths, breadths, mass — distributions, not averages | ANSUR II 93 measures × 6,068 subjects | **IN REPO** (`ansur_anchors.json`) |
| **theHuman** (gait) | joint angles/moments/GRF per % of cycle, by sex and decade | Van Criekinge 2023, 246 adults, OSF CC BY 4.0 | **IN REPO** (`story/data/gait_normative.json`) |
| **theHuman** (muscles) | 290 Hill-type muscles, measured fibre lengths/forces | MyoSuite + OpenSim (Rajagopal 2016, Hamner 2010) | **IN REPO** (`external/myo_sim`, `opensim/`) |
| **theSkin** | melanin filter + blood-bearing collagen, subsurface transport | OMLC Jacques model + Prahl hemoglobin + van Veen fat + Hale water | **IN REPO** (fat/water added today) |
| **theBreath** | lung volumes, pressures, ventilation vs exertion | standard physiology (cited in chapter) + Compendium METs (Tier B) | built; deepen from METs |
| **theSweep** | metabolic heat, insulation, radiation; skin emissivity 0.98±0.01 (8–14 µm) | Villaseñor-Mora 2009 (measured emissivity compilation) | built; emissivity archived today |
| **theAnkle** | rocker radius, stance GRF, τ/F lever | gait_normative (derived lever 0.071) | **built** |
| **theBalance** | lateral inverted-pendulum sway, COM vs COP, per-foot load split | HBEDB 1,930 quiet-stance trials (CC BY 4.0); dos Santos 2017 dual-plate GRF + whole-body kinematics | **DOWNLOADING** |
| **theEye** | photopic/scotopic V(λ), cone LMS fundamentals, dark adaptation, pupil vs luminance/age, retinal image formation | CVRL CIE 1924/1951/1931 + Stockman-Sharpe (today); Hecht 1937 + Haig 1941 tables (PMC, digitize); Watson-Yellott 2012 formula (open); Navarro 2009 CC review (today) | **DATA IN REPO** — membrane still stub |
| **theGrip** | grip-force norms by age/sex, skin/glove friction μ, contact on arbitrary normal | NHANES grip XPT n≈7,800 (public domain, today); Mathiowetz tables (today); Zhang & Mak 1999 skin μ tables (today); Carré 2017 glove μ (today) | **DATA IN REPO** — membrane still stub |
| **theHand** | finger kinematics, grasp closure, contact maps | ANSUR II hand measures (IN REPO); ContactDB contact maps (free, Tier B); DexYCB CC-BY-NC (Tier C) | partial — see Tier C warning |
| **theLoad** | carried mass → COM shift, cadence/GRF scaling, metabolic cost | EMU Data Book suit mass/pressure (today); Silder load-carriage 0–30% BW (SimTK, Tier B); Dembia 38 kg load walk (SimTK, Tier B) | NASA in repo; gait-load sets gated |
| **theStance** | 6 postures: contact patch, COM height, joint angles per posture | CMU full mocap: crouch-walk 136_09+, crawl 111_03/133_01, sit 13_01+, ANSUR sitting/kneeling heights | **DOWNLOADING (1 GB)** |
| **theThrust** | EVA jetpack thrust/impulse, zero-g no-contact law, partial-g ballistics, jump/landing forces | NASA SAFER (24 N₂ thrusters, EMU Data Book today); NASA CR-1726 reduced-g tables (today); Apollo TN D-7883 metabolic (today); MacLean 2021 4-gravity-level GRF+mocap (downloading); CMJ/squat/Bosco jump force plates (downloading); MoveSmart drops (downloading); CMU jumps 13_39+ | **DOWNLOADING** |
| **(motion library, all verbs)** | every movement class the story uses | CMU full DB — 2,605 trials, 144 subjects, BVH; **commercial inclusion explicitly allowed** (no resale of the data itself) | **DOWNLOADING (1 GB)** |
| **(light, all surfaces)** | measured n,k optical constants per material — visor glass, metals, water/ice | refractiveindex.info database, 3,135 records / 605 materials, **CC0** | **DOWNLOADED today** |

## TIER A — DOWNLOADED TODAY (no gate, verified)

- `eye/` — CIE 1924 photopic V(λ), CIE 1951 scotopic V′(λ), CIE 1931 XYZ CMFs, Stockman-Sharpe
  cone fundamentals (CVRL, free); Navarro 2009 (CC); Villaseñor-Mora 2009 skin IR emissivity
  (open); Hecht 1937 dark-adaptation article (PMC).
- `skin_friction/` — Zhang & Mak 1999 measured skin μ tables; Elkington 2024 climbing-rubber
  vs granite (CC BY); Carré 2017 gloves vs steel PDF.
- `skin_friction/` + optics — OMLC Hale & Querry water μa (200 nm–200 µm), van Veen fat μa,
  melanin μa page.
- `grip/` — NHANES 2011+2013 grip-strength raw XPT (US Gov public domain); Mathiowetz norms PDF.
- `eva/` — NASA EMU Data Book Rev V 2017 (mass properties, 4.3 psia, metabolic envelope, SAFER
  appendix); NASA CR-1726 reduced-gravity handbook (walk/jump vs g-level tables); NASA TN D-7883
  Apollo measured metabolic rates; NASA EVA Hardware & Ops 2012.
- `../optics/` — refractiveindex.info database (CC0, 43 MB): every visor glass, suit metal,
  water and ice — the LIGHT half of "light and physics" for every surface in every future game.

## TIER B — FREE BUT GATED (operator's click, ~5 min each)

| what | gate | feeds |
|---|---|---|
| SimTK account → Silder load-carriage (0/10/20/30% BW gait+GRF+EMG+metabolic) | free registration | theLoad |
| SimTK account → Dembia 38 kg loaded walking + simulations | free registration | theLoad |
| PhysioNet account → HBEDB direct (the figshare mirror already covers it) | free account | theBalance |
| SMPL / SMPL-X body surface | license click | skin surface (visual truth of the body) |
| Compendium of Physical Activities (MET table) | free site, no bulk export | theBreath/theSweep exertion scaling |

## TIER C — NON-COMMERCIAL LICENSES (the operator must rule)

**Finding: AMASS, GRAB, MANO are non-commercial-research-only; InterHand2.6M and DexYCB are
CC BY-NC.** If CHIMERA is ever sold, nothing derived from these may ship. The clean commercial
spine is what we already chose: CMU mocap (commercial inclusion allowed), NASA (public domain),
NHANES (public domain), CC0/CC-BY datasets, and digitized published tables. Recommendation:
treat Tier C only as *validation references* (check our derived numbers against theirs), never
as training inputs, unless the operator negotiates commercial licenses.

## HONEST GAPS (measured data that does not openly exist)

- **Raw Apollo lunar-gait kinematics** — exists only as metabolic tables + film analyses, not
  downloadable joint data. MacLean 2021's 4-level simulated gravity is the best measured proxy.
- **Pre-digitized dark-adaptation curves** — none; digitize Hecht 1937 / Haig 1941 tables
  (articles archived).
- **Skin/glove tribology database** — no NIST-style compendium exists; the three archived
  papers are the measured literature.
- **Hand grasp data that is both real-captured and commercial-clear** — does not exist at
  scale. ContactDB (academic free) + ANSUR hand dimensions + the closure law (the object
  decides) is the clean path.
- **Ice/snow and rust 3DGS scans** — still missing from the material codebook (flagged in the
  F1 session); a capture would close them the same way everything above closes.

## WHAT THIS BUYS, ONCE

- CMU full DB alone feeds **theStance, theBalance, theThrust, A3+G2 directional gaits,
  A5+G1 motion matching, B2 stumble/recover** — six roadmap items from one download.
- refractiveindex.info feeds **every material in every future game** — visor, hull, ice
  moon, ocean — one download, CC0, forever.
- NASA's EMU + reduced-g handbooks feed **theLoad, theThrust, theEVA, suit thermal, suit
  breath** — the entire suited-human half of the space game.
- The pattern is the point: nothing above is specific to this game. The next game starts
  with the human already proven.
