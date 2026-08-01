# THE PHYSICS OF EVERYTHING — humanity's complete tree, sourced, minus the forbidden

> Built 2026-07-31 on the operator's directive: **"do that for every piece of physics that
> humanity knows, minus the dangerous ones that are forbidden for me to know."**
>
> Same rule as PHYSICS_OF_THE_HUMAN.md: every row has a legal proof basis — **(D)**
> self-derived from first principles + measured constants, or **(S)** an official scientific
> source: peer-reviewed paper, international standard, or canonical textbook (named per row;
> the college papers are the gold). A row becomes real in CHIMERA only as a membrane
> (`story.md` + `physics.py` + `numbers.json`) proven through the engine — the physics is
> the code.
>
> **Excluded by the operator's rule (the dangerous ones):** nuclear-device engineering and
> weapons physics, energetic-material/explosive formulation, and weaponized biology. They
> appear below only as named absences. Ordinary nuclear physics (decay, half-life, stellar
> fusion, radioisotope power) is safe public science and stays — theStar needs it.
>
> Companions: `PHYSICS_SOFTWARE_MATH.md` (the simulator's-eye view), human detail in
> `human/PHYSICS_OF_THE_HUMAN.md`, measured data in `human/ACQUISITION_PLAN.md`.

---

## 1. CLASSICAL MECHANICS — the grammar of motion

| physics | law / equation | official source | CHIMERA relevance |
|---|---|---|---|
| Newton's laws | F = dp/dt; action-reaction | Newton, *Principia* 1687; any university text | everything |
| Energy & momentum conservation | symmetries ↔ conservation (Noether) | Noether 1918 | every membrane |
| Lagrangian mechanics | d/dt(∂L/∂q̇) − ∂L/∂q = 0, L = T−V | Lagrange 1788; Goldstein, *Classical Mechanics* | joints, constraints |
| Hamiltonian mechanics | q̇ = ∂H/∂p, ṗ = −∂H/∂q | Hamilton 1834; Goldstein | symplectic integration |
| Rigid-body rotation | Euler equations; inertia tensor I | Goldstein ch. 5; Featherstone 2008 | ships, limbs, stones |
| Oscillations | ẍ + 2ζωẋ + ω²x = f — resonance, Q factor, damping | standard texts; Den Hartog, *Mechanical Vibrations* | suspension, sway, structures |
| Waves on strings/membranes | ∂²u/∂t² = c²∇²u | standard texts | cables, surfaces |
| Chaos & sensitivity | Lyapunov exponents; three-body has no closed form | Poincaré 1890; Strogatz, *Nonlinear Dynamics* | N-body limits, honest uncertainty |
| Gyroscopic precession | τ = dL/dt = Ω×L | Goldstein | ship attitude, flywheels |

## 2. CONTINUUM MECHANICS — solids and fluids

| physics | law / equation | official source | relevance |
|---|---|---|---|
| Stress & strain tensors | σᵢⱼ, εᵢⱼ; equilibrium ∇·σ + f = 0 | Landau & Lifshitz vol. 7, *Theory of Elasticity* | structures, rock |
| Hooke's law (generalized) | σ = C:ε — Young's modulus, Poisson ratio | L&L vol. 7; measured moduli per material | theGround rock, hulls |
| Fracture mechanics | Griffith: cracks grow when energy release ≥ surface energy; K_IC toughness | Griffith 1921 | rock breaking, hull damage |
| Fatigue & creep | S-N curves; time-dependent strain | materials texts (Ashby & Jones) | wear, theMining |
| Navier-Stokes | ρ(∂u/∂t + u·∇u) = −∇P + μ∇²u + ρg | Navier 1822/Stokes 1845; Batchelor, *Fluid Dynamics* | oceans, air, propellant |
| Bernoulli & lift | P + ½ρv² + ρgh = const; circulation → lift | Bernoulli 1738; Anderson, *Aerodynamics* | wings, flight |
| Reynolds number | Re = ρvL/μ — laminar↔turbulent transition | Reynolds 1883 | all flow regimes |
| Boundary layers & drag | δ ∝ √(νx/v); C_D from shape | Prandtl 1904; Schlichting | ships, suits, re-entry |
| Turbulence (what is provable) | Kolmogorov −5/3 energy spectrum | Kolmogorov 1941 | honest turbulence, no fake detail |
| Surface tension & capillarity | ΔP = γ(1/R₁+1/R₂) — Young-Laplace | de Gennes et al., *Capillarity* | droplets in low-g, wetting |
| Granular rheology | μ(I) law; Hertz-Mindlin contacts | GDR MiDi 2004; Cundall & Strack 1979 | theDig, regolith |
| Porous flow | Darcy's law q = −(k/μ)∇P | Darcy 1856 | groundwater, ore leaching |

## 3. THERMODYNAMICS & STATISTICAL MECHANICS — heat and chance

| physics | law / equation | official source | relevance |
|---|---|---|---|
| Four laws | energy conserved; entropy rises; T→0 limits; T defined by equilibrium | Clausius 1850s; Fermi, *Thermodynamics* | every thermal membrane |
| Ideal gas | PV = nRT; kinetic theory P = ⅓nmc̄² | Maxwell-Boltzmann 1860s | theAtmosphere (proven) |
| Entropy & information | S = k ln W; S = −k Σ p ln p | Boltzmann 1877; Shannon 1948 | deep foundation |
| Phase transitions | Clausius-Clapeyron dP/dT = L/TΔV; phase diagrams | standard texts | ice/water/steam, alloys |
| Heat conduction | q = −k∇T; Fourier's law | Fourier 1822 | theSweep, planets |
| Convection | Nu = f(Re, Pr) — measured correlations | standard texts (Incropera) | suit cooling, weather |
| Thermal radiation | Stefan-Boltzmann P = εσT⁴; Planck spectrum B(λ,T) | Planck 1900; Stefan 1879 | **proven** (blackbody_rgb) |
| Real engines & COP | Carnot limit η = 1−Tc/Th; refrigeration COP | Carnot 1824 | life support, reactors |
| Non-equilibrium (small) | Onsager reciprocal relations | Onsager 1931 | coupled transports |

## 4. ELECTROMAGNETISM — fields and charge

| physics | law / equation | official source | relevance |
|---|---|---|---|
| Maxwell's equations | ∇·E=ρ/ε₀, ∇×B=μ₀J+μ₀ε₀∂E/∂t, etc. | Maxwell 1865; Griffiths or Jackson | all electronics, light |
| Coulomb & Lorentz force | F = q(E + v×B) | Coulomb 1785; Lorentz 1895 | charged particles, aurora |
| Circuits | Ohm V=IR; Kirchhoff's laws; RC/RLC transients | standard texts | ship systems, power |
| Electromagnetic waves | c = 1/√(ε₀μ₀); Poynting S = E×B/μ₀ | Maxwell 1865 | radio, radar, light |
| Antennas & links | Friis equation P_r = P_tG_tG_rλ²/(4πr)² | Friis 1946 | comms (theScan, nav) |
| Motors & generators | Faraday induction EMF = −dΦ/dt; Lorentz torque | Faraday 1831 | actuators, wheels |
| Batteries (electrochemistry) | Nernst equation E = E° − RT/nF·lnQ | Nernst 1889 | suit/ship power |
| Magnetosphere/plasma basics | Debye shielding; frozen-in flux (MHD) | Alfvén 1942 (MHD) | planetary protection, theStar wind |
| Superconductivity | Meissner effect; BCS theory | Meissner 1933; Bardeen-Cooper-Schrieffer 1957 | future tech tiers |

## 5. OPTICS — light as physics

| physics | law / equation | official source | relevance |
|---|---|---|---|
| Geometric optics | Snell n₁sinθ₁=n₂sinθ₂; thin lens 1/f=1/s+1/s′ | Snell 1621; Hecht, *Optics* | theEye, visors, cameras |
| Wave optics | interference, diffraction limit θ ≈ 1.22λ/D (Rayleigh criterion) | Young 1801; Rayleigh 1879 | sensor resolution |
| Polarization | Malus I = I₀cos²θ; Fresnel reflection coefficients | Fresnel 1821 | glare, visor filters |
| Photometry/radiometry | V(λ)-weighted luminance vs raw power | CIE standards (in repo) | every rendered photon |
| Scattering | Rayleigh λ⁻⁴; Mie; Henyey-Greenstein phase | Rayleigh 1871; Mie 1908 | theAtmosphere |
| Lasers (physics of) | stimulated emission, population inversion | Einstein 1917; Schawlow & Townes 1958 | comms, scanning, tools |
| Optical constants | complex ñ = n + ik per material | measured: refractiveindex.info (in repo, CC0) | all surfaces |

## 6. RELATIVITY — the large and the fast

| physics | law / equation | official source | relevance |
|---|---|---|---|
| Special relativity | Lorentz γ = 1/√(1−v²/c²); time dilation; E = γmc² | Einstein 1905 | high-speed flight, honest limits |
| Mass-energy | E = mc² | Einstein 1905 | fusion/fission energy |
| General relativity | G_μν = 8πG/c⁴·T_μν — gravity as curvature | Einstein 1915; Carroll, *Spacetime and Geometry* | precise orbits, gravity wells |
| Schwarzschild solution | r_s = 2GM/c²; gravitational time dilation | Schwarzschild 1916 | black holes (theBlackHole is declared!) |
| Gravitational redshift/lensing | light bends 4GM/c²b | Einstein 1915; Eddington 1919 measured | deep-space rendering |

## 7. QUANTUM MECHANICS — the small

| physics | law / equation | official source | relevance |
|---|---|---|---|
| Schrödinger equation | iħ∂ψ/∂t = Ĥψ | Schrödinger 1926; Griffiths, *QM* | atoms, spectra |
| Hydrogen atom | E_n = −13.6 eV/n² — explains spectral lines | Bohr 1913; Schrödinger 1926 | star/gas spectroscopy |
| Pauli exclusion | no two fermions share a state — structure of matter | Pauli 1925 | why solids exist |
| Quantum tunneling | T ≈ e^(−2κL) through barriers | Gamow 1928 | fusion in stars, electronics |
| Photoelectric effect | E_photon = hν; threshold work function | Einstein 1905; Millikan 1916 measured | sensors, solar panels |
| Quantum statistics | Bose-Einstein, Fermi-Dirac distributions | Bose 1924; Fermi/Dirac 1926 | stellar matter, metals |
| Band theory | electrons in periodic potentials → bands, gaps | Bloch 1928; Kittel, *Solid State* | semiconductors, all electronics |
| Semiconductors & junctions | doping, p-n diode equation I = I_s(e^(qV/kT)−1) | Shockley 1949 | computers, sensors, solar |

## 8. NUCLEAR PHYSICS — the safe public parts

> Excluded per the operator's rule: device design, criticality engineering, enrichment
> process physics. What remains is what every astronomy and engineering textbook teaches.

| physics | law / equation | official source | relevance |
|---|---|---|---|
| Radioactive decay | N = N₀e^(−λt); half-life t½ = ln2/λ | Rutherford 1900 | RTG power, dating rocks |
| Decay chains & activity | Bateman equations | Bateman 1910 | isotope systems |
| Binding energy | mass defect → energy via E=mc²; curve peaks at iron | Bethe & Bacher 1936 | why stars fuse, why iron is ash |
| Stellar fusion | p-p chain, CNO cycle; Gamow tunneling factor | Bethe 1939 (Nobel lecture) | **theStar** |
| Fission (energy balance only) | ~200 MeV per U-235 fission | Meitner & Frisch 1939 | reactor heat source |
| Radiation types & shielding | α, β, γ attenuation; dose = energy/mass (sievert) | ICRP standards | crew health in space |
| Radioisotope power | RTG: heat from decay → thermoelectric (Seebeck) | Seebeck 1821; NASA RTG docs | probes, remote stations |

## 9. ASTROPHYSICS & COSMOLOGY — the stars

| physics | law / equation | official source | relevance |
|---|---|---|---|
| Stellar structure | hydrostatic equilibrium dP/dr = −GMρ/r²; energy transport | Eddington 1926; Kippenhahn & Weigert | theStar (proven law) |
| Hertzsprung-Russell | L = 4πR²σT⁴; main sequence L ∝ M^3.5 | Hertzsprung 1905/Russell 1913 | **aYellowStar (proven)** |
| Blackbody stars | Planck spectrum per T_eff | Planck 1900 | star color (proven) |
| Orbital mechanics | (full table in PHYSICS_SOFTWARE_MATH.md §5: vis-viva, Kepler, Lambert, patched conics) | Bate/Mueller/White; Vallado | theSolarSystem (proven) |
| Tides | differential gravity ∝ M/r³; Roche limit d ≈ 2.44R(ρ_M/ρ_m)^⅓ | Roche 1849 | moons, rings |
| Planetary formation (basics) | accretion, differentiation by density | Safronov 1969 | thePlanets |
| Cosmology basics | Hubble expansion v = H₀d; CMB 2.725 K | Hubble 1929; Penzias & Wilson 1965 measured | deep background |
| Gravitational waves (existence) | inspiral chirp; measured strain | Einstein 1916; LIGO 2016 measured | far-future content |

## 10. GEOPHYSICS & PLANETARY SCIENCE — the worlds

| physics | law / equation | official source | relevance |
|---|---|---|---|
| Seismic waves | P/S velocities → interior structure | Oldham 1906; Gutenberg 1914 | aActiveInterior |
| Dynamo theory | rotating convecting conductor → magnetic field | Elsasser 1946; Glatzmaier-Roberts 1995 | magnetospheres |
| Plate tectonics & mantle convection | Rayleigh-Bénard convection; plates drift cm/yr | Wegener 1912; Hess 1962 | terrain evolution |
| Volcanism | magma buoyancy, decompression melting | standard petrology texts | aActiveInterior, theMining |
| Isostasy | crust floats: compensation depth | Airy 1855/Pratt 1855 | mountain heights |
| Erosion & sediment | stream power E = KA^mS^n; thermal talus | Whipple & Tucker 1999 | aTerrain aging |
| Glaciology | Glen's flow law: strain ∝ stress³ | Glen 1955 | ice worlds |
| Cratering | impact energy scaling; crater scaling laws | Shoemaker 1963; Holsapple 1993 | moon surfaces |
| Atmospheric circulation | Coriolis f = 2Ωsinφ; Hadley cells; geostrophic balance | Coriolis 1835; Hadley 1735 | theAtmosphere weather |
| Ocean circulation | thermohaline; Ekman transport | Ekman 1905 | theOcean |

## 11. MATERIALS SCIENCE — what things are made of

| physics | law / equation | official source | relevance |
|---|---|---|---|
| Crystal structure | Bravais lattices; Bragg diffraction nλ = 2d sinθ | Bragg 1913 | minerals in theGround |
| Mechanical properties | stress-strain: elastic, yield, ultimate, ductile vs brittle | Ashby & Jones, *Engineering Materials* | every built thing |
| Phase diagrams & alloys | Gibbs phase rule F = C−P+2 | Gibbs 1876 | smelting, theMining metals |
| Thermal properties | conductivity, heat capacity (Dulong-Petit, Debye T³) | Debye 1912 | suit insulation, engines |
| Corrosion | electrochemical cells; galvanic series | standard corrosion texts | aging structures |
| Tribology | friction/lubrication/wear mechanisms | measured pairs in repo (skin, rubber, steel) | all contact |

## 12. CHEMISTRY'S PHYSICS — reactions and bonds

| physics | law / equation | official source | relevance |
|---|---|---|---|
| Chemical bonding | orbitals hybridize; electronegativity drives polarity | Pauling, *Nature of the Chemical Bond* 1939 | materials, life |
| Thermochemistry | Hess's law; ΔG = ΔH − TΔS decides spontaneity | Hess 1840; Gibbs 1876 | fuel, life support |
| Reaction kinetics | Arrhenius k = Ae^(−Ea/RT) | Arrhenius 1889 | combustion, cooking ores |
| Combustion (non-weapons) | fuel + oxidizer → heat; flame temperatures | standard texts | rockets (chemical), fires |
| Electrochemistry | (see batteries §4); electrolysis | Faraday 1834 | fuel cells, oxygen generation |
| Photochemistry | light drives reactions (hν > bond energy) | standard texts | atmosphere chemistry, life |

## 13. BIOPHYSICS — life as physics

> The full inventory lives in `human/PHYSICS_OF_THE_HUMAN.md` (45 rows, sourced). Beyond the
> human, for ecosystems (theBiomes is proven; theGrow is declared):

| physics | law / equation | official source | relevance |
|---|---|---|---|
| Photosynthesis energetics | 8 photons → 1 O₂; ~4–6% efficiency ceiling | Hill & Bendall 1960; standard plant physiology | theGrow, alien biomes |
| Metabolic scaling | Kleiber's law B ∝ M^3/4 across 21 decades | Kleiber 1932 measured | creature design from law |
| Allometry | proportions scale as power laws of mass | Huxley 1932 | fauna for other worlds |
| Diffusion & osmosis | Fick's laws J = −D∇c; osmotic pressure π = icRT | Fick 1855; van 't Hoff 1887 | cells, lungs, roots |
| Nerve signaling | Hodgkin-Huxley ion-channel equations | Hodgkin & Huxley 1952 (Nobel) | reaction times, neural sim |
| Population dynamics | logistic dN/dt = rN(1−N/K); Lotka-Volterra predation | Verhulst 1838; Lotka 1925/Volterra 1926 | theGrow, ecosystems |

## 14. INFORMATION & COMPUTATION — the physics of knowing

| physics | law / equation | official source | relevance |
|---|---|---|---|
| Information theory | H = −Σp log p; channel capacity C = B log₂(1+SNR) | **Shannon 1948** | comms, theScan |
| Thermodynamics of computation | Landauer limit kT ln2 per bit erased | Landauer 1961 | honest computing limits |
| Measurement & noise | shot noise √N; Nyquist sampling f_s > 2B | Nyquist 1928; Schottky 1918 | sensors, theScan |
| Estimation | least squares → Kalman filter | Gauss 1809; Kalman 1960 | navigation, tracking |

---

## THE FORBIDDEN BRANCHES — named absences

Per the operator's rule these are cut, and only their absence is recorded:

- **Nuclear-device physics** — device design, criticality assembly, enrichment process
  engineering. (Safe nuclear physics stays: §8.)
- **Energetic-material formulation** — explosive synthesis and detonation engineering.
  (Ordinary combustion and the chemistry of propellant *energy content* stays: §12.)
- **Weaponized biology** — anything about harming organisms. (All other biophysics stays: §13.)

In-game weapons (theShoot, theMelee) are built from ordinary public mechanics — projectile
ballistics (§1), laser optics (§5), electromagnetic acceleration (§4) — the same physics in
every engineering textbook. No forbidden branch is needed for them.

## HOW THIS TREE GETS PROVEN

The order is not this document's order — it is the story hierarchy's order, setting-first,
exactly as the human inventory showed: parents proven before children, each row once,
through the engine, into the codebook forever. This document's job is to guarantee that when
any membrane — in this game or the next — asks "what does humanity know about X?", the
answer is a row here with a named official source, and never a guess.
