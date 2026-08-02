# MEMBRANE × PHYSICS — which laws apply to each membrane, and why

<!-- CHIMERA-LAW -->
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
> **[docs/THE_LAW.md](../docs/THE_LAW.md)** · full method: `Chimera/docs/EXPERIMENTAL_METHOD.md`
> · enforced by `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> Built 2026-07-31 on the operator's directive: **"all of the natural world is a combination
> of all of the known — so we need to figure out for each membrane which ones apply and
> why."**
>
> A membrane is never one physics. It is the intersection of every law whose variables the
> membrane touches. This document is that intersection, enumerated: for every chapter in
> `story/`, the physics rows that govern it, with the reason each applies. References:
> **E§n** = row of `PHYSICS_OF_EVERYTHING.md`, **H§n** = row of
> `human/PHYSICS_OF_THE_HUMAN.md`, **S§n** = row of `PHYSICS_SOFTWARE_MATH.md`. Status:
> PROVEN (crossed the engine boundary), BUILT (derives numbers, not yet through `prove`),
> STUB (declared, honest-empty), DECLARED (in THE_STORY.md, no chapter yet).

---

## THE COSMOLOGICAL CHAIN — where setting comes from

**theZero** — the initial condition. `STUB`-grade honesty: the origin is not provable, it is the seed.
- E§9 cosmology basics (Hubble expansion, CMB 2.725 K) — the only measured facts about the beginning
- E§3 thermodynamics (entropy arrow) — why there is a "before" and "after" at all

**theHorizon** — the causal boundary of what can be seen.
- E§6 relativity (light-travel time, causal structure) — the horizon IS a light-speed fact
- E§9 cosmology (particle horizon vs event horizon) — how far the visible universe extends

**theClock** — time as a physical process. Every `duration_s` in the tree derives here.
- E§1 oscillations (periodic processes define seconds; SI: caesium hyperfine, E§7) — a clock is counted physics, not abstraction
- E§3 entropy (the arrow of time) — why duration has a direction
- E§6 relativity (time dilation) — a clock in a gravity well or at speed disagrees; the game must know

**theDensityClock** — the story's own clock: time read off density.
- E§1 mechanics + E§3 statistical mechanics (ρ = M/V evolving under expansion/collapse) — density is measurable state
- the story declares it the clock of thrust — energy→motion priced by density

**theHumanClock** — the body's own timebase.
- H§4.4/4.5 (cardiac and respiratory periods — measured rhythms) — heartbeat and breath are the body's seconds
- E§13 Hodgkin-Huxley (neural time constants) — reaction time sets the human frame rate

**theEmptying** — the rarefaction of everything.
- E§9 Hubble expansion v = H₀d — measured recession
- E§3 adiabatic expansion cooling — expansion and cooling are one fact seen twice

**theCooling** — temperature falling until structure can exist.
- E§3 Planck spectrum per epoch (blackbody of the universe) — temperature is the era's label
- E§9 recombination/CMB — matter becomes neutral, light goes free: the precondition for atoms, hence for everything below

**theCloud** — the gas cloud that will be a star.
- E§9 gravitational collapse (Jeans criterion: a cloud collapses when gravity beats pressure) — why a star forms at all
- E§3 ideal gas (pressure support) + E§2 fluid dynamics (turbulent cascade in the cloud) — what resists collapse

**theGalaxy** — the gravitationally-bound swarm the system swims in.
- E§1/E§9 N-body gravity (rotation, orbits of stars about the core) — galactic structure is orbital mechanics at scale
- E§9 stellar populations — the mix of star ages that sets the neighborhood

## THE SYSTEM — star and planets (the PROVEN chain)

**theSolarSystem** `PROVEN`
- E§9 orbital mechanics (Kepler, N-body symplectic, S§5) — the planets' motions are conic sections plus perturbations
- E§1 angular momentum conservation — why the system is a disk
- E§9 accretion (Safronov 1969) — where the bodies came from

**theStar** `PROVEN` (law) — **aYellowStar** `PROVEN` (instance)
- E§9 stellar structure (hydrostatic equilibrium dP/dr = −GMρ/r²) — a star is gravity balanced by pressure
- E§8 stellar fusion (Bethe 1939: p-p chain, tunneling) — the light's source
- E§3 Planck blackbody (T_eff → spectrum) — the light's color
- E§4 MHD/plasma (stellar wind, flares) — the weather it throws at the planets
- E§9 H-R relation (L = 4πR²σT⁴, L ∝ M^3.5) — the instance's numbers

**thePlanets** `PROVEN` — **theRockyPlanet / aRockyPlanet / aBlueWorld** `PROVEN`
- E§9 accretion + differentiation by density — iron sinks, silicates float: why rocky planets have cores
- E§11 silicate mineralogy — what rock IS
- E§8 radiogenic heat (decay in the body) + E§3 conductive loss — the planet's heat budget
- E§9 tides (differential gravity) — moon-locking, internal flexing heat

## THE WORLD — atmosphere, ocean, interior, terrain (PROVEN)

**theAtmosphere** `PROVEN` — **aNitrogenAtmosphere** `PROVEN`
- E§3 ideal gas + hydrostatic balance (P(h) = P₀e^(−Mgh/RT)) — pressure falls exponentially; theBreath and flight inherit this
- E§3 adiabatic lapse rate — temperature structure with altitude
- E§5 Rayleigh/Mie scattering (λ⁻⁴, HG phase) — sky color, sunsets, haze: the LOOK of the world
- E§10 Coriolis + Hadley cells (f = 2Ω sin φ) — wind belts, weather systems
- E§12 photochemistry — how starlight rewrites the gas

**theOcean** `PROVEN` — **aSaltOcean** `PROVEN`
- E§2 hydrostatic pressure (P = ρgh) — pressure per depth; diving, hulls
- E§2 surface tension + gravity waves (Young-Laplace, dispersion) — the surface you see
- E§5 Beer-Lambert with MEASURED water absorption (Hale & Querry 1973, in repo) — light dies with depth, red first
- E§12 salinity chemistry + E§13 osmosis (van 't Hoff) — what salt does to life and freezing
- E§9 tides (lunar/solar differential pull) + E§10 Ekman/thermohaline transport — the currents
- E§2 Navier-Stokes / shallow water (Saint-Venant) — waves on aTerrain's coasts

**theInterior** `PROVEN` — **aActiveInterior** `PROVEN`
- E§10 mantle convection (Rayleigh-Bénard: buoyancy vs viscosity) — the engine under the terrain
- E§3 heat transport (conduction + convection from core to crust) — geothermal gradient
- E§10 seismology (P/S wave speeds → structure) — how the inside is known without digging
- E§4 dynamo theory (rotating convecting conductor → field) — the magnetosphere that shields the atmosphere
- E§11 high-pressure phases (minerals transform with depth) — why the mantle is layered

**theTerrain** `PROVEN` — **aTerrain** `PROVEN`
- E§10 stream-power erosion (E = KA^mS^n) + thermal weathering/talus — mountains age by law
- E§10 isostasy (crust floats) — how high mountains can stand
- E§10 plate tectonics (convection-driven drift) — where ranges come from
- E§2 granular mechanics (soil, scree) — the walkable surface's give
- E§5 + 3DGS genome codebook (measured, in repo) — the terrain's measured look (veg #26, rock #24)

**theGround** `PROVEN`
- E§2 granular contact (Hertz-Mindlin) + E§1 Coulomb friction (μ MEASURED, in repo) — what a foot or wheel meets
- E§2 elasticity + Griffith fracture of rock — stones break by law, not by art
- E§11 mineral properties (crystal structure, hardness) — quartz/feldspar/oxide roles (genomes #24/#9/#28)
- E§3 thermal conduction — ground temperature underfoot
- E§5 measured mineral optics (refractiveindex.info, in repo) — how stone takes light

## THE MINING — industry on the interior (PROVEN)

**theMining** `PROVEN` — **aTerraceMine** `PROVEN`
- E§2 fracture mechanics (Griffith: cracks grow when release ≥ surface energy) — digging is controlled fracture
- E§2 μ(I) granular rheology + angle of repose — spoil piles and terrace slopes hold by measured friction
- E§11 phase diagrams + ore mineralogy — ore grades are crystal chemistry (aTerraceMine: Fe 0.3024, Cu 0.006)
- E§12 thermochemistry of smelting (ΔG = ΔH − TΔS) — what refining costs in energy
- E§1 mechanics of machinery — excavators are Newton's laws with diesel
- H§8.4 theLoad (carried mass coupling) — the human who digs pays metabolically

## THE HUMAN — the body (map already complete in detail)

**theHuman** `PROVEN` — **aHuman** `PROVEN`: the full 45-row inventory is
`human/PHYSICS_OF_THE_HUMAN.md`. Summary of the intersections:
- H§1 frame (de Leva segments, ANSUR measured) + E§1 Newton-Euler — the body's mechanics
- H§2 muscles (Zajac/Millard Hill model, Ward measured architecture) — the actuators
- H§3 gait (Van Criekinge measured, Kuo inverted pendulum) — the movement
- H§4 metabolism (Mifflin-St Jeor, Fick, Hill-Severinghaus) — the furnace
- H§5 thermal (Pennes bioheat, Fiala, measured emissivity) — the loop
- H§9 planet coupling (NASA EMU suit, gravity variants) — the context

**theBreath** `BUILT`
- E§3 gas partial pressures + H§4.7 barometric coupling — breathing is pressure exchange with theAtmosphere (proven parent)
- E§13 Fick diffusion across the alveolar membrane — O₂/CO₂ cross by concentration gradient
- H§4.4 ventilation vs V̇O₂ (Wasserman) — exertion links breath to metabolism

**theSweep** `BUILT`
- H§5.1 Pennes bioheat (conduction + perfusion + metabolism) — tissue temperature by equation
- H§4.1/4.2 metabolic heat (resting + MET scaling) — the furnace's output
- H§5.3 radiative loss (Stefan-Boltzmann, ε = 0.98 measured) + H§5.4 suit insulation (NASA EMU) — exchange with the world

**theAnkle** `BUILT`
- E§1 contact mechanics + H§3.2 measured GRF — the stance film
- H§2.3 tendon elasticity (energy return) — why walking is cheap
- H§1 joint geometry (rocker radius 0.279 m, derived) — the foot rolls, not slides

**theSkin** `BUILT` (optics + area)
- H§7.1–7.3 melanin/hemoglobin/water/fat optics (ALL measured, in repo) — light through the surface
- H§7.4 Jensen dipole BSSRDF — the full subsurface model (open depth)
- H§7.6 DuBois area (2.01 m² on ANSUR median) — the exchange surface for theSweep

**theBalance** `STUB` — physics identified, data in repo
- H§3.4 inverted-pendulum sway + Winter's COP-inside-base-of-support — standing is continuous falling, caught
- E§13 vestibular/neural feedback — the sensor that drives corrections
- measured: HBEDB 1,930 trials, dos Santos dual-plate

**theEye** `STUB` — physics identified, data in repo
- E§5 photometry + H§6.1 CIE V(λ)/V′(λ) — brightness is wavelength-weighted, differently day and night
- H§6.3 Navarro schematic eye (ray-traced retinal image) + H§6.4 Watson-Yellott pupil — the camera the visor serves
- H§6.5 Hecht dark adaptation — walking from light into dark is a 30-minute physics process
- H§6.6 acuity/field — the resolution budget

**theGrip** `STUB` — physics identified, data in repo
- E§1 Coulomb friction with MEASURED μ (Zhang & Mak; Carré gloves) — grip is friction management
- H§8.1 strength distributions (NHANES raw, Mathiowetz) — how hard a hand can close
- E§1 contact on arbitrary surface normals — the story's rock-face walking: a DIFFERENT contact law, not a movement mode

**theHand** `STUB`
- H§1 hand kinematics (ANSUR hand dimensions, in repo) — the linkage
- H§8.3 closure law (command the process; the object decides the pose) — the house rule, validated against ContactDB (Tier B)
- E§1 contact mechanics per fingertip — where force lands

**theLoad** `STUB`
- E§1 added-mass mechanics (COM shifts, inertia grows) — a hopper of ore is physics, not inventory
- H§3.8 Pandolf load-carriage equation + measured (Silder/Dembia, Tier B) — the metabolic price per kilogram
- H§9.3 EMU suit mass (NASA, in repo) — the suit itself is the first load

**theStance** `STUB`
- H§8.5 posture geometry (CMU measured: crouch 136_09+, crawl 111_03) — six postures, six contact patches
- E§1 statics (COM over base of support per posture) — each stance re-solves standing
- H§1 ANSUR sitting/kneeling heights (in repo) — the measured dimensions per posture

**theThrust** (human's child) `STUB`
- E§1 impulse/momentum + S§5 Tsiolkovsky (jetpack: thrust from expelled mass) — EVA flight is Newton with no floor
- H§3.6 jump takeoff/landing forces (measured plates, in repo) — the ground-bound version
- H§3.7 gravity-dependent ballistics (NASA CR-1726 + MacLean 4-g data, in repo) — hops in low-g
- the contact ABSENCE law: every locomotion row assumes a foot on something; this membrane owns the exception

## THE DECLARED VERBS — no chapters yet, physics already mapped

**theDig** `DECLARED` — E§2 fracture + granular μ(I) (breaking and moving ground); E§11 tribology (tool wear); E§3 energetics (work per volume).
**theGrow** `DECLARED` — E§13 photosynthesis energetics + logistic growth (Verhulst) + E§3 energy budgets: life from energy, capped by carrying capacity.
**theScan** `DECLARED` — E§14 Shannon (information per measurement) + E§4 EM waves (Friis link budget) + E§7 spectroscopy (composition from light) + E§14 Nyquist/noise: a scan is a physics measurement, with a bandwidth and a noise floor.
**theNavigate** `DECLARED` — E§9 orbital mechanics (Kepler, Lambert, patched conics) + E§14 Kalman estimation (position from noisy fixes) + E§6 relativistic corrections where they matter.
**theShoot** `DECLARED` — ordinary public physics only: E§1 projectile ballistics + E§2 drag (Reynolds, C_D) + E§5 laser optics (for beams) + E§12 propellant energy content. The forbidden branches (named absences in PHYSICS_OF_EVERYTHING.md) are not needed for any of it.
**theMelee** `DECLARED` — E§1 impulse/momentum transfer + E§2 fracture/penetration mechanics + H§2 muscle force-velocity: a strike is a collision powered by Hill curves.
**theEVA** `DECLARED` — E§9 orbital mechanics + S§5 rocket equation + H§9.3 suit (NASA EMU: pressure, thermal, mass) + H§4 vacuum physiology (theBreath against 0 bar): the whole suited-human stack, in vacuum.
**theBlackHole** `DECLARED` — E§6 general relativity (Schwarzschild r_s = 2GM/c², time dilation) + E§6 gravitational lensing + E§4/E§3 accretion-disk MHD and radiation: the density clock's ceiling, rendered honestly.

---

## THE RULE THIS DOCUMENT ENFORCES

When a membrane is built or extended, its chapter must answer: **which rows here apply, and
did the derive use them?** A membrane that touches a variable governed by a row it ignores
is incomplete by construction — the natural world does not run a subset of physics. And the
converse discipline: a row listed here that the membrane's own questions never exercise is
declared as not-applicable, with the reason — honesty in both directions, never a physics
bibliography for show.
