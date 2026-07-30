# HUMAN DATA — the measured source base

> Built 2026-07-30 on the operator's steer: "for a human body it's so complicated we're going to
> need actual sources for all the concepts — I don't like all this guessing." Every body concept
> derives from one of these, or says why it can't. Scope note (the operator): realistic human
> with realistic biology and physics, genitalia omitted — the standard rating convention.

## Tier 0 — IN THE REPO NOW

| source | what it measures | status |
|---|---|---|
| `external/myo_sim` (**MyoSuite MyoSim**, Caggiano et al. 2022, arXiv:2205.13600, Apache 2.0) | the full musculoskeletal model: 26 bodies, 113 geoms, **290 muscles** with measured Hill parameters; legs from Rajagopal et al. 2016 (OpenSim), arms from Saul et al. 2015 | PRESENT. **Verified against our splat pipeline 2026-07-30** (`tools/verify_myo_splat.py`, A/B vs MuJoCo renderer: same body, blind-eye agrees) |
| `research_references/human/ANSUR_II_MALE_Public.csv` (4,082 subjects) + `ANSUR_II_FEMALE_Public.csv` (1,986) | **93 direct anthropometric measurements per subject** (mm): stature, segment lengths, breadths, circumferences, sitting heights — the dimensional truth of human bodies | DOWNLOADED (mirror of the Penn State OPEN Design Lab release; US Gov work, public since 2017) |

## Tier 1 — PUBLIC, FETCHABLE (no license wall)

| source | what it is | access |
|---|---|---|
| **ANSUR II** full report + data dictionary (Paquette et al., Natick) | measurement definitions + procedures for the CSVs above | https://www.openlab.psu.edu/ansur2/ |
| **Visible Human Project** (NLM) | CT + MRI + **cryosection** of a male (1 mm) and female (0.33 mm) — real anatomy in cross-section: organs, muscle paths, bone | since 2019 **no registration** — NLM FTP terms (https://www.nlm.nih.gov/research/visible/getting_data.html) |
| **CMU MoCap database** | ~2,600 motion-capture trials of real people walking/running/sitting — the movement truth for gait work | http://mocap.cs.cmu.edu/ (free, with citation) |
| **OpenSim models** (Stanford; Rajagopal 2016 gait model, Hamner 2010 running) | the measured musculoskeletal parameters myo_sim is built on: muscle origins/insertions, optimal fibre lengths, pennation, max isometric forces | https://github.com/opensim-org/opensim-models (BSD) |

## Tier 2 — LICENSE-GATED (needs the operator's click)

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
- **Motion** (how a real walk looks): CMU MoCap / AMASS for the trainer's references — the gait
  dyad judges against real human footage, not our own render's self-image.
- **Insides** (breath, blood, the loop): Visible Human cross-sections + the standard physiology
  numbers (already cited inside `theBreath`/`theSweep`).
