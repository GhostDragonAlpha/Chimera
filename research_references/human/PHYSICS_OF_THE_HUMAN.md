# THE PHYSICS OF THE HUMAN — the complete inventory, and how a human gets proven

<!-- CHIMERA-LAW -->
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
> **[docs/THE_LAW.md](../../docs/THE_LAW.md)** · full method: `Chimera/docs/EXPERIMENTAL_METHOD.md`
> · enforced by `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> Built 2026-07-31 on the operator's question and ruling.
>
> **The question: "how do you prove a human with physics — what are all the physics that are
> required?"** This file is the full answer: every physics a human needs, each with its
> official source and its proof status.
>
> **The ruling (verbatim): "physics have to be proven by either deriving them yourself, or
> you have to get them from a reputable physics paper or book — official physics sources,
> official scientific sources. We're going to pound in the college papers. The college papers
> are where the gold is. That's what humanity believes, so it counts as a direct source —
> probably the best one we have."**
>
> So every row below carries exactly one of two legal proof bases:
> **(D)** *self-derived* — derived in a membrane's `physics.py` from first principles plus
> measured constants, validated against measured data; or **(S)** *official source* — a
> peer-reviewed paper, an international standard, or a canonical textbook (named per row).
> Measured training data comes from the acquisition sweep (`ACQUISITION_PLAN.md`). A row is
> DONE only when it has crossed the engine's boundary (`prove`: physics number + human dyad
> ≥ 0.6). Sources are cited so the membrane can derive FROM them — per the doctrine, the
> physics is the code.

---

## 1. THE FRAME — body as segments (structure)

| # | physics | proof | official source | measured data (repo) | membrane | status |
|---|---|---|---|---|---|---|
| 1.1 | Segment masses, lengths, COM positions | S+D | Dempster 1955 (WADC); **de Leva 1996**, *J. Biomech.* 29(9) — the standard Zatsiorsky corrections; Hanavan 1964 | ANSUR II 6,068 subjects (`ansur_anchors.json`) | theHuman | **PROVEN** |
| 1.2 | Segment moments of inertia | S+D | de Leva 1996 (radius of gyration per segment) | derived from 1.1 + density | theHuman | derived, in tree |
| 1.3 | Joint degrees of freedom, axes, ranges of motion | S | AAOS *Joint Motion: Method of Measuring and Recording*; Kapandji, *Physiology of the Joints* | OpenSim model definitions (in repo) | myobody / theAnkle | in myobody |
| 1.4 | Newton-Euler rigid-body dynamics | D | Featherstone, *Rigid Body Dynamics Algorithms* (2008) — we derive, the book validates | — | all moving membranes | running (MuJoCo substrate) |
| 1.5 | Ground contact: Signorini + Coulomb | S+D | Signorini 1933; Coulomb 1785; Stewart & Trinkle 1996 | measured μ: Zhang & Mak 1999, Elkington 2024 (in repo) | theAnkle, theGround, B1 | partial |

## 2. THE ENGINES — muscles (actuation)

| # | physics | proof | official source | measured data | membrane | status |
|---|---|---|---|---|---|---|
| 2.1 | Hill muscle: F = F₀·(a·f_L·f_V + f_PE)·cos α | S | **Zajac 1989**, *CRC Crit. Rev. Biomed. Eng.*; Hill 1938 | OpenSim/Thelen 2003 parameters (in repo) | myobody | running |
| 2.2 | Force-length / force-velocity curves | S | Millard et al. 2013, *J. Biomech. Eng.* | in the muscle models | myobody | running |
| 2.3 | Tendon series elasticity (toe + linear) | S | Millard 2013; Thelen 2003 | in the muscle models | myobody | running |
| 2.4 | Activation dynamics ȧ = (u−a)/τ | S | Zajac 1989; Thelen 2003 | τ_act ≈ 10 ms, τ_deact ≈ 40 ms | myobody | running |
| 2.5 | Muscle architecture (F₀, l₀, pennation) | S | **Ward et al. 2009**, *Clin. Orthop.* — measured cadaveric | Rajagopal 2016 / Saul 2015 (in repo) | myobody | running |
| 2.6 | Moment arms τ = Σ rᵢ(q)·Fᵢ | S+D | Rajagopal 2016, *IEEE TBME* | model definitions | myobody | running |

## 3. THE LOCOMOTION — gait (movement)

| # | physics | proof | official source | measured data | membrane | status |
|---|---|---|---|---|---|---|
| 3.1 | The gait cycle: stance/swing/double support, joint kinematics per % cycle | S | **Van Criekinge et al. 2023** (246 adults, CC BY 4.0); Perry & Burnfield, *Gait Analysis* (textbook); Inman, Ralston & Todd 1981, *Human Walking* | `story/data/gait_normative.json` (in repo) | theHuman gait | **PROVEN** |
| 3.2 | Ground reaction forces (the 1.1–1.2 BW peaks, the lever τ/F) | S | Van Criekinge 2023 | gait_normative (in repo) | theAnkle | **PROVEN** |
| 3.3 | Inverted-pendulum walking mechanics; why speed selects step length | S+D | Kuo 2002, *J. Biomech. Eng.*; Kuo 2007, *Hum. Mov. Sci.* ("six determinants") | validated against 3.1 | theHuman gait | derived in tree |
| 3.4 | Lateral sway & dynamic balance: COP inside base of support | S | Winter 1995, *Gait & Posture* — human balance and posture control | **HBEDB 1,930 trials + dos Santos dual-plate (in repo)** | theBalance | stub — data ready |
| 3.5 | Directional gaits: turns, side-steps, backwards | S | CMU mocap trials (measured: 16_17+ turns, 136_09+ crouch, 111_03 crawl) | **CMU full DB (in repo)** | theStance, A3+G2 | stub — data ready |
| 3.6 | Jump takeoff/landing forces | S | Bosco protocol; measured force plates | **CMJ/squat/Bosco + MoveSmart drops (in repo)** | theThrust (ground) | stub — data ready |
| 3.7 | Gravity dependence of gait & ballistics | S+D | NASA CR-1726 (in repo); h = v²/2g derived | **MacLean 2021 four-gravity GRF+mocap (in repo)** | theThrust, theEVA | stub — data ready |
| 3.8 | Cost of transport: metabolic cost of walking vs speed/load | S | Margaria 1938; **Pandolf et al. 1977**, *J. Appl. Physiol.* (load-carriage equation) | Compendium METs; Apollo TN D-7883 (in repo); Silder load data (Tier B) | theSweep, theLoad | partial |

## 4. THE FURNACE — metabolism, circulation, breath (energy)

| # | physics | proof | official source | measured data | membrane | status |
|---|---|---|---|---|---|---|
| 4.1 | Basal metabolic rate | S | **Mifflin-St Jeor 1990**, *Am. J. Clin. Nutr.*; Harris-Benedict 1919 | ANSUR body dims | theSweep | **PROVEN** (built) |
| 4.2 | Metabolic rate vs activity (METs) | S | Ainsworth et al. 2011 Compendium; ISO 8996 | Apollo measured rates (in repo) | theSweep | built, deepen |
| 4.3 | Muscle-level metabolic cost | S | Umberger et al. 2003; Bhargava et al. 2004 | from the muscle models | theSweep | open |
| 4.4 | Lung volumes, ventilation vs oxygen uptake | S | Wasserman et al., *Principles of Exercise Testing* (textbook); ATS/ERS standards | standard physiology (cited in chapter) | theBreath | **PROVEN** (built) |
| 4.5 | Cardiac output: Fick principle Q̇ = V̇O₂/(Ca−Cv) | S | Fick 1870; standard cardiology texts | measured norms | theBreath/C1 | open |
| 4.6 | Oxyhemoglobin dissociation | S | Hill 1910 (the Hill equation); **Severinghaus 1979**, *J. Appl. Physiol.* | hemoglobin spectra (in repo) | theBreath | open |
| 4.7 | Barometric coupling: breath vs ambient pressure | S+D | barometric formula; theAtmosphere (proven law) | — | theBreath | **PROVEN** (built) |

## 5. THE THERMAL LOOP — heat (temperature)

| # | physics | proof | official source | measured data | membrane | status |
|---|---|---|---|---|---|---|
| 5.1 | Pennes bioheat: conduction + blood perfusion + metabolism | S | **Pennes 1948**, *J. Appl. Physiol.* — the founding tissue-heat equation | — | theSweep | built, deepen |
| 5.2 | Whole-body thermoregulation (sweat, shiver, vasomotor) | S | **Fiala et al. 1999**, *Int. J. Biometeorol.*; ISO 11079 (cold stress) | measured model parameters in the papers | theSweep/C3 | open |
| 5.3 | Radiative exchange: skin emissivity | S | Villaseñor-Mora 2009 (measured 0.98 ± 0.01, in repo); Stefan-Boltzmann (derived) | in repo | theSweep | built |
| 5.4 | Clothing/suit insulation (clo units, suit thermal) | S | ISO 9920; **NASA EMU Data Book** (in repo) | EMU metabolic envelope 1000–2000 Btu/hr | aHuman suit, theSweep | partial |

## 6. THE SENSES — the eye (vision)

| # | physics | proof | official source | measured data | membrane | status |
|---|---|---|---|---|---|---|
| 6.1 | Photopic/scotopic luminous efficiency V(λ), V′(λ) | S | **CIE 1924 / CIE 1951 standards** — measured, not modeled | **CSVs in repo** (`eye/`) | theEye | data ready — stub |
| 6.2 | Color matching: spectral → XYZ → LMS | S | **CIE 1931 standard**; Stockman & Sharpe 2000 cone fundamentals | **CSVs in repo** | theEye | data ready — stub |
| 6.3 | The schematic eye (retinal image, accommodation) | S | **Navarro et al. 1985**, *JOSA A*; Navarro 2009 review (CC, in repo) | in repo | theEye | data ready — stub |
| 6.4 | Pupil size vs luminance/field/age | S | **Watson & Yellott 2012**, *J. Vision* — unified formula | constants in the paper | theEye | data ready — stub |
| 6.5 | Dark adaptation time-course (rod-cone break) | S | **Hecht, Haig & Chase 1937**, *J. Gen. Physiol.*; Haig 1941 | archived (PMC, in repo) — digitize | theEye | data ready — stub |
| 6.6 | Visual acuity & field extent | S | standard optometry measures (Sloan; ISO 8596) | published norms | theEye | open |

## 7. THE SURFACE — skin (what light meets)

| # | physics | proof | official source | measured data | membrane | status |
|---|---|---|---|---|---|---|
| 7.1 | Epidermal melanin filter: μa ∝ λ⁻³·³ | S | **Jacques (OMLC)**, measured model; melanin fractions 1.3–43% by class | in repo | theSkin | **PROVEN** |
| 7.2 | Blood-bearing dermis: hemoglobin extinction | S | Prahl/OMLC compilation (Gratzer + Kollias) | **in repo** (376 rows, 250–1000 nm) | theSkin | **PROVEN** |
| 7.3 | Tissue water & fat absorption | S | **Hale & Querry 1973**, *Appl. Opt.*; **van Veen et al. 2004** | in repo | theSkin | data ready |
| 7.4 | Subsurface transport: diffusion dipole BSSRDF | S | **Jensen et al. 2001**, *SIGGRAPH* — the measured skin BRDF/BSSRDF | parameters in the paper | theSkin (full version) | open |
| 7.5 | Skin friction (contact law input) | S | **Zhang & Mak 1999**, *Prosthet. Orthot. Int.* (measured tables, in repo) | in repo | theGrip | data ready |
| 7.6 | Body surface area | S+D | **DuBois & DuBois 1916** — on ANSUR median = 2.01 m² | ANSUR (in repo) | theSkin | **PROVEN** |

## 8. THE MANIPULATION — hand, grip, load (interaction)

| # | physics | proof | official source | measured data | membrane | status |
|---|---|---|---|---|---|---|
| 8.1 | Grip/pinch strength distributions by age & sex | S | **Mathiowetz et al. 1985**, *Arch. Phys. Med. Rehabil.*; NHANES protocol | **NHANES raw trials in repo** (8,291 rows) | theGrip | data ready — stub |
| 8.2 | Gloved/bare contact friction vs material, wet/dry | S | **Carré et al. 2017**, *Wear* (in repo); Zhang & Mak 1999 | in repo | theGrip | data ready — stub |
| 8.3 | Grasp closure: command the process, contact decides pose | D | house law (THE_STORY.md), validated against ContactDB contact maps (Tier B) | ANSUR hand dims (in repo) | theHand | stub |
| 8.4 | Carried mass → COM shift, gait & metabolic cost change | S+D | Pandolf 1977; Silder et al. (SimTK, Tier B); Dembia 2017 (Tier B) | EMU suit mass (in repo); CMU loaded-motion trials | theLoad | stub |
| 8.5 | Posture set: stand/crouch/prone/crawl geometry | S+D | CMU measured trials (136_09+, 111_03, 133_01) | ANSUR sitting/kneeling heights (in repo) | theStance | stub — data ready |

## 9. THE CONTEXT — a human on a planet (coupling)

| # | physics | proof | official source | measured data | membrane | status |
|---|---|---|---|---|---|---|
| 9.1 | Gravity field & its variation | — | already proven upstream: theSolarSystem, aPlanet (codebook) | — | parent chain | **PROVEN** |
| 9.2 | Atmospheric pressure/temperature at the body | — | already proven: theAtmosphere (law + aNitrogenAtmosphere) | — | parent chain | **PROVEN** |
| 9.3 | The suited human: suit mass, pressure, mobility, jetpack | S | **NASA EMU Data Book Rev V**; SAFER appendix (in repo) | in repo | aHuman, theEVA, theLoad | data ready |
| 9.4 | Variation across humans: age, sex, growth | S | WHO/CDC growth standards; ANSUR II male+female (in repo); gait by decade (in repo) | in repo | aHuman class | open — for future games |
| 9.5 | Terrain coupling: foot on measured ground | — | already proven: theGround, aTerrain, theBiomes | 3DGS genome codebook (in repo) | B1 foot IK | next on menu |

---

## HOW A HUMAN GETS PROVEN — the answer to the question

1. **The human is a conjunction, not a concept.** It is proven exactly when every row above
   is proven — there is no single "human proof", only the tree closing row by row. That is
   why the story hierarchy descends setting-first: the parents (planet, atmosphere, ground)
   were proven before the body, because every body row needs them as inputs.
2. **Each row proves through the engine, once.** orient → frame (the row as one atomic
   claim) → question×N until measured saturation → classify (each variable to PHYSICS or
   THE HUMAN) → render → dyad (the physics number vs the human reading, ≥ 0.6) → prove.
   The row then lives in the codebook forever and every future membrane — and every future
   game — inherits it. Effort per subject: once.
3. **The two legal proof bases per the operator's ruling:** derive it yourself (D) against
   measured data, or take the law from an official scientific source (S) — the named paper,
   standard, or textbook in the table. The college papers are the gold: what humanity has
   measured and agreed on counts as a direct source. A row with neither is a stub, and a
   stub is honest — it says so in its chapter.
4. **Current tally:** 9 rows **PROVEN** through the boundary (the whole context chain plus
   gait, GRF, breath, thermal base, skin optics, anthropometry), ~20 rows **data-ready**
   (the acquisition sweep put their measured inputs in the repo — these are the next
   proofs: theBalance, theEye ×6, theGrip, theStance, theThrust, theLoad), remainder open
   with their sources named. No row lacks a named source or an honest gap declaration.

**The menu order stands** (docs/HUMAN_FEATURE_MENU.md): B1 foot IK next — rows 1.5, 3.2,
9.5 and catalog row 10 (FABRIK/DLS) — then A3+G2 (row 3.5), A5+G1 (motion matching over the
CMU library), C1+C3 (rows 4.5, 5.2), B2 stumble/recover (rows 3.4, 3.6, 3.2).
