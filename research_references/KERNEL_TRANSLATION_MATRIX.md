# KERNEL TRANSLATION MATRIX — Every Phenomenon → Barnes-Hut DSL Row

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY ROW IS A THEORY.** Statement / prediction / falsifier, all three. No
> falsifier, no row.
>
> **RULE 1 — DERIVE, DON'T GUESS.** Every kernel_fn claim cites the actual Green's
> function. If unknown: RESEARCH-NEEDED with a precise gap statement.
<!-- CHIMERA-LAW -->

Built 2026-08-14 from `PHYSICS_OF_EVERYTHING.md` (14 categories, 97 rows + 3 forbidden
absences), `kernel_dsl.py` (5 kernel_fn vocabulary items, 3 aggregate types, current 5
shipped kernels), and `SPIACE_RPG_PLAN.md` Phases 5–9 (proven translation precedent).

The tree carries **any additive point-source interaction with a known Green's function.**
Five kernels are already shipped and tested: gravity, light, electromagnetism, heat,
acoustic. This matrix covers every remaining phenomenon in the physics tree and states
precisely why it does or does not fit.

## Summary Table

Sorted: **YES** (by Green's-function family), then **NEAR-FIELD ONLY**, then **NO**,
then **forbidden absences**. Counts at bottom.

### YES — Superposable Point-Source Fields (Green's Function Exists)

| # | Category | Phenomenon | Green's Function | kernel_fn | Aggregate | Sign | Coupling | Shipped? |
|---|---|---|---|---|---|---|---|---|
| 1 | Classical Mechs. | — | — | — | — | — | — | (covered below) |
| 2 | Continuum Mechs. | Porous flow (Darcy) | −1/(4πr) | potential_1r | sum | attractive | μ/(4πk) | No |
| 3 | Thermodynamics | Heat conduction (steady-state) | −1/(4πr) | potential_1r | weighted_sum | attractive | 1/(4πκ) | **Yes** (`heat`) |
| 4 | Electromagnetism | Coulomb / electrostatic force | 1/(4πε₀r²) radial | inverse_squared | bipolar_sum | bipolar | 1/(4πε₀) | **Yes** (`electromagnetism`) |
| 5 | Electromagnetism | EM wave intensity (radiative far-field) | 1/(4πr²) scalar flux | irradiance | weighted_sum | attractive | 1/(4π) · G_t·G_r | **Yes** (`light`, with gain extension) |
| 6 | Optics | Incoherent scalar diffraction (far-field intensity) | 1/(4πr²) | irradiance | weighted_sum | attractive | 1/(4π) | **Yes** (same as light; V(λ) weighting is post-tree) |
| 7 | Nuclear Physics | Radioisotope decay heat → thermal emission | −1/(4πr) | potential_1r | weighted_sum | attractive | 1/(4πκ) | **Yes** (via `heat` quantity = decay power) |
| 8 | Astrophysics | Blackbody stellar luminosity | 1/(4πr²) | irradiance | weighted_sum | attractive | 1/(4π) | **Yes** (`light`) |
| 9 | Continuum Mechs. | Diffusion, steady-state (Fick) | −1/(4πr) | potential_1r | sum | attractive | 1/(4πD) | No |
| 10 | Electromagnetism | Antenna received power (Friis) | 1/(4πr²) · G_t·G_r | irradiance | weighted_sum | attractive | G_t·G_r/(4π) | No |

### NEAR-FIELD ONLY — Tree Cannot Carry; Requires Per-Particle or Local Correction

| # | Category | Phenomenon | Why Tree Fails | Required Correction |
|---|---|---|---|---|
| 1 | Classical Mechs. | Waves on strings/membranes | 1D wave equation Green's fn requires domain boundary conditions; tree assumes infinite homogeneous medium | Boundary-condition-specific solver per segment |
| 2 | Continuum Mechs. | Navier-Stokes (finite Re) | Nonlinear advection (u·∇)u breaks superposition; Stokeslet exists at Re→0 but inertial terms dominate at finite Re | Local correction: solve NS on leaf-cluster, or use tree mass for drag estimate |
| 3 | Continuum Mechs. | Boundary layers & drag | δ ∝ √(νx/v); requires wall geometry and local velocity — not a function of particle position alone | Per-particle friction model using tree-estimated free-stream density |
| 4 | Continuum Mechs. | Tides (differential gravity) | Δa ∝ M·d/r³; depends on target object's size parameter d, not just position — cannot aggregate into single node value valid for all targets | Post-tree: compute tidal tensor from tree mass, apply per-target correction factor |
| 5 | Continuum Mechs. | Surface tension & capillarity | Young-Laplace ΔP = γ(1/R₁+1/R₂); interface geometry dependent, not point-source | Per-surface-element calculation; tree can estimate ambient pressure field via porous-flow kernel |
| 6 | Electromagnetism | Biot-Savart (magnetic field from moving charges) | B ∝ q(v×r̂)/r²; velocity-dependent — each particle has different v, cannot aggregate v into node center | Post-tree correction per Phase 7 Lorentz precedent: F_B = q(v×B_tree) where B_tree is estimated from current moments |
| 7 | Electromagnetism | Magnetosphere / plasma (MHD) | Frozen-in flux ∂B/∂t = ∇×(v×B); nonlinear coupling to velocity field, Poisson-Boltzmann for Debye shielding is nonlinear | Coupled NS+Maxwell solver; tree can provide background B from dipole moments if stored |
| 8 | Electromagnetism | Electric/magnetic dipoles | Potential ∝ cosθ/r² (dipole), not isotropic scalar; requires oriented moment storage per node, not just center + total | Store quadrupole/tensor moments per node — grammar extension needed (new aggregate type) |
| 9 | Optics | Scattering (Rayleigh/Mie) | Phase function is angle-dependent; tree aggregation into node centers loses angular information needed for directional scattering | Per-particle phase function evaluation; tree provides incident flux, not scattered field |
| 10 | Relativity | General relativity (full) | Einstein equations G_μν = 8πG/c⁴ T_μν are nonlinear; superposition fails | Post-Newtonian expansion: tree carries mass, velocity-dependent corrections applied per-particle |
| 11 | Relativity | Gravitational lensing (weak-field) | Deflection α = 4GM/c²b depends on impact parameter b (ray geometry), not just particle position | Post-tree deflection: compute convergence κ = Σ/Σ_crit from tree mass projection, apply per-ray |
| 12 | Relativity | Schwarzschild (N-body) | Exact 1-body solution; N-body requires post-Newtonian terms with velocity dependence | Per-particle PN correction after tree traversal |
| 13 | Geophysics | Seismic waves (P/S body waves) | Time-dependent Green's fn δ(t−r/c)/r; requires temporal convolution, not static aggregation | Dynamic wave solver per layer; tree can estimate path-averaged velocity for travel-time estimation |
| 14 | Geophysics | Plate tectonics / mantle convection | Rayleigh-Bénard coupled thermal-fluid dynamics; requires boundary conditions and material properties | Per-membrane NS solve; tree heat kernel provides temperature field as boundary condition |
| 15 | Geophysics | Atmospheric circulation | Coriolis f = 2Ωsinφ + coupling to NS with thermal forcing | Post-tree: Coriolis acceleration per particle, tree provides pressure/temperature fields |
| 16 | Geophysics | Ocean circulation | Thermohaline + Ekman transport; coupled density-driven flow with planetary rotation | Similar to atmospheric — post-tree corrections on tree-provided fields |
| 17 | Nuclear Physics | Radiation shielding (α/β/γ attenuation) | Beer-Lambert exponential decay e^(−μx); requires material-specific coefficients and path geometry | Per-ray integration through material layers; tree provides source positions |

### NO — Not a Superposable Point-Source Field

| # | Category | Phenomenon | Why Not Translatable |
|---|---|---|---|
| 1 | Classical Mechs. | Newton's laws (F = dp/dt) | Equations of motion, not point-source fields |
| 2 | Classical Mechs. | Energy & momentum conservation (Noether) | Symmetry principles; not spatial fields |
| 3 | Classical Mechs. | Lagrangian mechanics | Variational principle d/dt(∂L/∂q̇) − ∂L/∂q = 0; not a field |
| 4 | Classical Mechs. | Hamiltonian mechanics | q̇ = ∂H/∂p, ṗ = −∂H/∂q; formalism, not a field |
| 5 | Classical Mechs. | Rigid-body rotation (Euler equations) | Requires inertia tensor I; torques don't superpose as point sources |
| 6 | Classical Mechs. | Oscillations (ẍ + 2ζωẋ + ω²x = f) | ODE in time, not a spatial field |
| 7 | Classical Mechs. | Chaos & sensitivity (Lyapunov) | Property of dynamics; not a field |
| 8 | Classical Mechs. | Gyroscopic precession (τ = Ω×L) | Nonlinear in L; requires angular momentum vector per body |
| 9 | Continuum Mechs. | Stress & strain tensors (σᵢⱼ, εᵢⱼ) | Tensor fields in continuous media; no point-source Green's fn in kernel sense |
| 10 | Continuum Mechs. | Hooke's law (σ = C:ε) | Constitutive relation; not a field generator |
| 11 | Continuum Mechs. | Fracture mechanics (Griffith) | Crack growth is non-superposable; threshold rule K_IC |
| 12 | Continuum Mechs. | Fatigue & creep | Time-dependent material response; no static Green's fn |
| 13 | Continuum Mechs. | Bernoulli & lift | Derived from NS with circulation; non-superposable Kutta condition |
| 14 | Continuum Mechs. | Reynolds number (Re = ρvL/μ) | Dimensionless parameter, not a field |
| 15 | Continuum Mechs. | Turbulence (Kolmogorov −5/3) | Nonlinear, chaotic; no superposable Green's fn |
| 16 | Continuum Mechs. | Granular rheology (μ(I) law) | Frictional contacts (Coulomb criterion); non-superposable |
| 17 | Thermodynamics | Four laws of thermodynamics | Foundational principles, not fields |
| 18 | Thermodynamics | Ideal gas (PV = nRT) | Equation of state; molecular kinetics is statistical, not a spatial field |
| 19 | Thermodynamics | Entropy & information (S = k ln W) | State function; scalar, not a field |
| 20 | Thermodynamics | Phase transitions (Clausius-Clapeyron) | Nonlinear; first-order transitions are discontinuous |
| 21 | Thermodynamics | Convection (Nu = f(Re, Pr)) | Coupled to NS; buoyancy-driven flow is nonlinear |
| 22 | Thermodynamics | Real engines & COP (Carnot limit) | Thermodynamic cycle analysis; not a field |
| 23 | Thermodynamics | Non-equilibrium (Onsager reciprocal) | Coupled fluxes require solving linear system, not point-source aggregation |
| 24 | Electromagnetism | Circuits (Ohm, Kirchhoff) | Lumped-element network theory; no spatial field in free space |
| 25 | Electromagnetism | Motors & generators (Faraday induction) | Requires B-field geometry + current loops; velocity-dependent Lorentz force on conductors |
| 26 | Electromagnetism | Batteries (Nernst equation) | Electrode potential is chemical, not spatial field |
| 27 | Optics | Geometric optics (Snell's law) | Ray tracing is deterministic path-following; requires interface geometry |
| 28 | Optics | Polarization (Malus, Fresnel) | Vector property (E-field orientation); DSL handles only scalar quantities per node |
| 29 | Optics | Lasers (stimulated emission) | Coherent process requiring phase tracking; not a passive Green's function |
| 30 | Optics | Optical constants (complex ñ) | Material property; not a field generator |
| 31 | Relativity | Special relativity (Lorentz γ) | Kinematic framework; not a force field |
| 32 | Relativity | Mass-energy (E = mc²) | Equivalence relation; not a spatial field |
| 33 | Quantum Mechs. | Schrödinger equation (iħ∂ψ/∂t = Ĥψ) | Time-dependent complex wavefunction; not a static spatial field |
| 34 | Quantum Mechs. | Hydrogen atom (E_n = −13.6 eV/n²) | Bound-state solution; discrete levels, not superposable field |
| 35 | Quantum Mechs. | Pauli exclusion principle | Quantum statistical principle; not a field |
| 36 | Quantum Mechs. | Quantum tunneling (T ≈ e^(−2κL)) | Non-local exponential decay through barrier; not classical point-source Green's fn |
| 37 | Quantum Mechs. | Photoelectric effect (E_photon = hν) | Photon-electron interaction; quantum process, not spatial field |
| 38 | Quantum Mechs. | Quantum statistics (Bose-Einstein, Fermi-Dirac) | Statistical distributions; not fields |
| 39 | Quantum Mechs. | Band theory (Bloch, Kittel) | Electronic structure in periodic potentials; requires SE in crystal lattice |
| 40 | Quantum Mechs. | Semiconductors & junctions (Shockley diode) | Device physics; non-linear I-V characteristic |
| 41 | Nuclear Physics | Radioactive decay (N = N₀e^(−λt)) | Temporal process; not a spatial field |
| 42 | Nuclear Physics | Decay chains (Bateman equations) | ODE system in time; not spatial fields |
| 43 | Nuclear Physics | Binding energy (mass defect curve) | Nuclear property; not a spatial field |
| 44 | Nuclear Physics | Stellar fusion (p-p chain, CNO) | Quantum tunneling through Coulomb barrier; reaction rate physics, not a field |
| 45 | Nuclear Physics | Fission (energy balance) | Energy release accounting; not a spatial field |
| 46 | Astrophysics | Stellar structure (hydrostatic equilibrium) | ODE in radial coordinate dP/dr = −GMρ/r²; not a spatial field for N-body |
| 47 | Astrophysics | Hertzsprung-Russell diagram | Empirical L vs T_eff correlation; stellar classification, not a field |
| 48 | Astrophysics | Orbital mechanics (Kepler, vis-viva) | Analytical 2-body solutions; N-body is handled by gravity kernel but "orbital mechanics" as topic is trajectory analysis |
| 49 | Astrophysics | Planetary formation (accretion, differentiation) | Process, not a field; material sorting by density |
| 50 | Astrophysics | Cosmology basics (Hubble flow, CMB) | Kinematic expansion of space; CMB is boundary condition, not superposable source field |
| 51 | Astrophysics | Gravitational waves (inspiral chirp) | Radiative 1/r strain from quadrupole; time-dependent waveform requires dynamic solver |
| 52 | Geophysics | Dynamo theory (Elsasser, Glatzmaier-Roberts) | Self-generated B-field via nonlinear MHD feedback loop |
| 53 | Geophysics | Volcanism (magma buoyancy, decompression melting) | Geophysical process; not a field |
| 54 | Geophysics | Isostasy (Airy/Pratt compensation) | Static balance equation; not a spatial field for N-body |
| 55 | Geophysics | Erosion & sediment (stream power law) | Landscape evolution PDE E = KA^mS^n; not a point-source field |
| 56 | Geophysics | Glaciology (Glen's flow law) | Nonlinear rheology strain ∝ stress³ |
| 57 | Geophysics | Cratering (impact scaling laws) | Empirical scaling; not a superposable field |
| 58 | Materials Science | Crystal structure (Bravais, Bragg) | Atomic-scale periodicity; not a spatial field at simulation scales |
| 59 | Materials Science | Mechanical properties (stress-strain curves) | Constitutive material response; not fields |
| 60 | Materials Science | Phase diagrams & alloys (Gibbs phase rule) | Equilibrium thermodynamics; not fields |
| 61 | Materials Science | Corrosion (electrochemical cells) | Time-dependent oxidation process |
| 62 | Materials Science | Tribology (friction/lubrication/wear) | Contact mechanics; non-superposable Coulomb friction |
| 63 | Chemistry | Chemical bonding (orbital hybridization) | Quantum mechanical; not a classical field |
| 64 | Chemistry | Thermochemistry (Hess's law, ΔG = ΔH − TΔS) | State functions; not fields |
| 65 | Chemistry | Reaction kinetics (Arrhenius k = Ae^(−Ea/RT)) | Temporal process |
| 66 | Chemistry | Combustion (non-weapons) | Coupled reaction-diffusion; nonlinear flame propagation |
| 67 | Chemistry | Electrochemistry (electrolysis) | Chemical potential differences; not spatial fields |
| 68 | Chemistry | Photochemistry (light-driven reactions) | Requires photon flux tracking per species; not a simple field |
| 69 | Biophysics | Photosynthesis energetics | Biochemical quantum efficiency; not a spatial field |
| 70 | Biophysics | Metabolic scaling (Kleiber's law) | Allometric relationship B ∝ M^3/4; not a field |
| 71 | Biophysics | Allometry (power-law proportions) | Geometric scaling; not a field |
| 72 | Biophysics | Nerve signaling (Hodgkin-Huxley) | Nonlinear ion-channel dynamics on membranes |
| 73 | Biophysics | Population dynamics (logistic, Lotka-Volterra) | ODEs in time; population models, not fields |
| 74 | Information & Computation | Information theory (Shannon entropy) | Abstract measure H = −Σp log p; not a spatial field |
| 75 | Information & Computation | Thermodynamics of computation (Landauer limit) | Fundamental bound kT ln 2 per bit erased; not a field |
| 76 | Information & Computation | Measurement & noise (shot noise, Nyquist) | Statistical properties; not fields |
| 77 | Information & Computation | Estimation (Kalman filter) | Recursive state estimation algorithm; not a field |

### FORBIDDEN BRANCHES — Named Absences (Operator Rule)

| Branch | Reason for Exclusion | Appears As |
|---|---|---|
| Nuclear-device physics | Device design, criticality assembly, enrichment process engineering | Named absence per operator directive; safe nuclear physics (§8) stays |
| Energetic-material formulation | Explosive synthesis and detonation engineering | Named absence per operator directive; ordinary combustion (§12) stays |
| Weaponized biology | Anything about harming organisms | Named absence per operator directive; all other biophysics (§13) stays |

---

## Detailed YES Rows — DSL Declarations, Node Fields, Falsifiers

Each row below is a complete membrane: statement (someone could disagree), prediction
(unmeasured), falsifier (named before any run). Per Rule 0.

### Row Y-1: Porous Flow / Groundwater (Darcy's Law)

**Source:** Darcy 1856; Landau & Lifshitz vol. 6, *Fluid Mechanics* §14.
**Green's function derivation:** Incompressible flow in homogeneous isotropic medium:
∇·v = 0, v = −(k/μ)∇P → ∇²P = 0. Point sink of strength Q (m³/s) at origin:
P(r) = −Qμ/(4πkr). Green's function G(r) = −1/(4πr). Same family as heat steady-state.

**DSL declaration:**
```
kernel porous_flow {
    quantity  = "flux_source"       # volumetric flow rate Q (m³/s); + = source, − = sink
    aggregate = "sum"               # total = ΣQ, center = Q-weighted centroid
    kernel_fn = "potential_1r"      # P = Q·μ/(4πk·r) — Darcy steady-state Green's fn
    sign      = "attractive"        # positive sources raise pressure field upward
    coupling  = "DARCY_INV_4PI"     # μ/(4πk), host-derived from permeability [m²] and viscosity [Pa·s]
    toggle    = "porousFlowEnabled"
}
```

**Node fields added:** +16 B/node (center vec3f @ current end + total flux_source f32).
Current node size: 144 B → 160 B. Requires new f32 buffer `flux_sources` (binding N+1).

**Grammar fit:** Exact. `potential_1r` already in KERNEL_FNS, `sum` already in AGGREGATES.

**STATEMENT:** Darcy flow through a homogeneous porous medium is exactly representable
by the same `potential_1r` kernel as steady-state heat diffusion, with coupling constant
μ/(4πk) derived from measured permeability and fluid viscosity. The tree's O(log n)
approximation holds for pressure-field evaluation at any point in the domain.

**PREDICTION:** In a test system of N point sinks/sources in a homogeneous medium, the
pressure field evaluated at M probe points via the Barnes-Hut tree (θ = 0.5) will match
the O(N·M) direct summation to within 2% relative error at all probe points, with
convergence improving as θ decreases.

**FALSIFIER:** If measured max relative error across all probe points exceeds 5% for
θ ≤ 0.3 (a value well within the tree's proven acceptance range — gravity and EM both
hold at θ = 0.5 with < 1% error per Phase 6/8 falsifiers), then Darcy flow does NOT
map to the `potential_1r` kernel family, or the homogeneous-medium assumption is
violated by the test configuration. Named before any run: **F-Y1**.

---

### Row Y-2: Diffusion, Steady-State (Fick's First Law)

**Source:** Fick 1855; Crank, *The Mathematics of Diffusion* §2.
**Green's function derivation:** Steady-state diffusion equation: D∇²c = −Sδ(r), where S
is source strength (mol/s or kg/s). Solution: c(r) = S/(4πDr). Green's function
G(r) = 1/(4πr). Same family as heat and porous flow.

**DSL declaration:**
```
kernel diffusion {
    quantity       = "diffusion_source"  # concentration source strength S (mol/s or kg/s)
    aggregate      = "sum"               # total = ΣS, center = S-weighted centroid
    kernel_fn      = "potential_1r"      # c = S/(4πD·r) — Fick steady-state Green's fn
    sign           = "attractive"        # positive sources raise concentration field
    coupling       = "DIFFUSION_INV_4PI" # 1/(4πD), host-derived from diffusivity [m²/s]
    toggle         = "diffusionEnabled"
}
```

**Node fields added:** +16 B/node → 160 B (if declared alongside porous_flow) or 176 B
(if declared in addition). Requires new f32 buffer `diffusion_sources`.

**Grammar fit:** Exact. Same kernel_fn as heat and porous_flow — all three accumulate
into the same `fluxOut.t` / `theat` field variable. The host program must interpret
the accumulated field differently depending on which toggle is active, or the DSL must
be extended to support per-kernel output fields (see Grammar Note below).

**STATEMENT:** Steady-state diffusion in a homogeneous medium with point sources is
exactly representable by the `potential_1r` kernel, with coupling 1/(4πD) derived from
measured diffusivity. The concentration field superposes linearly.

**PREDICTION:** Two point sources S₁ and S₂ at positions r₁ and r₂: the concentration at
any probe point r is c(r) = S₁/(4πD|r−r₁|) + S₂/(4πD|r−r₂|). The tree-aggregated result
will match direct summation to within 1% relative error for θ ≤ 0.5.

**FALSIFIER:** If measured concentration at any probe point deviates from the analytic
superposition by > 3% (a generous bound — heat kernel falsifier F6 holds at 0.0001%),
then steady-state diffusion does NOT map to `potential_1r`, or diffusivity is not
scalar/isotropic in the test medium. Named before any run: **F-Y2**.

**GRAMMAR NOTE:** The current DSL accumulates all `potential_1r` kernels into a single
output field (`fluxOut.t` / `theat`). Declaring both porous_flow and diffusion alongside
heat would cause field collisions. Two options: (a) host program gates mutually exclusive
kernels at runtime (only one potential_1r toggle active at a time), or (b) extend the DSL
to support per-kernel output fields (e.g., `field_out = "pressure"` vs `"concentration"`).
Option (a) is sufficient for individual membrane use; option (b) is needed for simultaneous
multi-physics membranes.

---

### Row Y-3: Antenna Received Power (Friis Transmission Equation)

**Source:** Friis 1946; Balanis, *Antenna Theory* §2.5.
**Green's function derivation:** Received power P_r = P_t·G_t·G_r·λ²/((4πr)²). This is
irradiance E = P_t·G_t/(4πr²) multiplied by effective aperture A_e = G_r·λ²/(4π). The
spatial dependence is identical to the light kernel (1/r² scalar flux); antenna gain
factors are multiplicative constants absorbed into the coupling.

**DSL declaration:**
```
kernel antenna_link {
    quantity  = "radiated_power"   # transmitted power P_t (W); each node carries its source's P_t·G_t
    aggregate = "weighted_sum"     # total = Σ(P_t·G_t), center = weighted centroid
    kernel_fn = "irradiance"       # E = P_t·G_t / (4πr²) — Friis spatial dependence
    sign      = "attractive"       # positive sources increase received power density
    coupling  = "FRIIS_G_ANTENA"   # G_r·λ²/(4π), host-derived from receiver antenna parameters
    toggle    = "antennaLinkEnabled"
}
```

**Node fields added:** +16 B/node → 160 B. Requires new f32 buffer `radiated_powers`.

**Grammar fit:** Exact. `irradiance` already in KERNEL_FNS, `weighted_sum` already in
AGGREGATES. Coupling absorbs the receiver-side antenna parameters (G_r, λ), which are
host program constants, not per-particle quantities.

**STATEMENT:** The Friis transmission equation's spatial dependence is identical to the
irradiance kernel; antenna gains are constant multiplicative factors that can be folded
into the coupling constant or applied as a post-tree scaling factor.

**PREDICTION:** In a test system with N transmitting nodes at known positions and powers,
the received power at a receiver node computed via the Barnes-Hut tree will match direct
O(N) summation to within 2% for θ ≤ 0.5, identical to the light kernel's accuracy.

**FALSIFIER:** If measured received power deviates from direct summation by > 5% for
θ ≤ 0.3 (conservative — light kernel thermal equilibrium holds at < 1% error per Phase
5), then the Friis equation does NOT map to `irradiance` through tree aggregation, or
multipath/interference effects dominate in the test configuration (which would violate
the incoherent summation assumption). Named before any run: **F-Y3**.

---

## Detailed NEAR-FIELD ONLY Rows — Local Correction and Why Tree Fails

### Row N-1: Navier-Stokes (Finite Reynolds Number)

**Why tree fails:** The advection term (u·∇)u is nonlinear — superposition does not hold.
A node's aggregated velocity cannot be used to compute forces on all children, because
each child has a different velocity and the nonlinear term couples them.

**Local correction:** For each leaf cluster, solve the Stokes approximation (neglecting
advection) using tree-aggregated pressure/velocity boundary conditions, then apply a
post-tree drag correction: F_drag = −½ρC_D A|v|v, where ρ and v are estimated from
tree-leaf counts and local velocity moments.

**Precedent:** Phase 7 Lorentz force — velocity-dependent forces are post-tree corrections.
Same pattern applies here: tree provides far-field flow estimate; per-particle correction
handles local nonlinearity.

---

### Row N-2: Tides (Differential Gravity)

**Why tree fails:** Tidal acceleration Δa ≈ 2GMd/r³ depends on the target object's
physical size d — a property of the target, not the source. A tree node's aggregated
mass M at distance r gives the correct *monopole* acceleration GM/r² for all targets,
but the tidal *gradient* requires knowing each target's extent d individually.

**Local correction:** Compute the tidal tensor from tree-aggregated mass moments:
T_ij = ∂²Φ/∂x_i∂x_j = GM(3x_ix_j/r⁵ − δ_ij/r³). Apply per-target: Δa_i = T_ij·d_j
where d is the target's displacement vector from its center of mass.

**Grammar extension needed:** Store quadrupole moment Q_ij per node (6 additional f64
values = 48 B/node) to compute tidal tensor directly from tree without leaf traversal.
Current DSL aggregate types (weighted_sum, bipolar_sum, sum) cannot represent tensor
aggregation.

---

### Row N-3: Biot-Savart / Magnetic Field from Moving Charges

**Why tree fails:** B = (μ₀/4π)·q(v×r̂)/r² depends on each charge's velocity v. A node's
aggregated center-of-charge cannot represent the velocity distribution of its children.

**Local correction:** Per Phase 7 precedent — apply Lorentz force F = q(v×B) as a
post-tree correction where B is estimated from current moments. To estimate B from the
tree: each charged particle contributes a current element I·dl = qv, and the tree can
aggregate dipole-like moments if extended to store velocity-weighted charge centers.

**Grammar extension needed:** New aggregate type `velocity_weighted_sum` or new kernel_fn
for vector fields. Current scalar-per-node architecture cannot carry directional B-field
information.

---

### Row N-4: Scattering (Rayleigh/Mie Phase Functions)

**Why tree fails:** Scattered intensity I(θ, φ) depends on the angle between incident
direction and scattering direction. Tree aggregation into node centers loses all angular
information — a node's total scattering cross-section cannot be reused for different
incident angles.

**Local correction:** Use tree to estimate incident flux at each particle (same as light
kernel), then apply per-particle phase function: I_scattered = I_incident·σ_scat·Φ(θ,φ).
The tree provides the incident field; the phase function is a per-particle lookup.

**Precedent:** Same pattern as Lorentz force — tree provides far-field estimate, local
correction handles angle-dependent physics.

---

### Row N-5: General Relativity (Full)

**Why tree fails:** Einstein's equations G_μν = 8πG/c⁴·T_μν are nonlinear — the
gravitational field itself carries energy and contributes to T_μν, breaking superposition.
The weak-field limit (Newtonian gravity) is already shipped; full GR requires solving
for the metric tensor on a curved manifold.

**Local correction:** Post-Newtonian expansion: g_μν = η_μν + h_μν where h_μν is small.
Order PN-1 adds velocity-dependent corrections to the Newtonian acceleration:
a_PN = a_Newton · (1 + v²/c² + ...). These are per-particle corrections after tree
traversal, following Phase 7 precedent.

**Grammar extension needed:** New kernel_fn for velocity-dependent force scaling, or
post-tree correction layer with access to per-particle velocities and the tree's mass
distribution.

---

## Summary Counts

| Category | Count | Description |
|---|---|---|
| **YES** (superposable point-source field) | **3 new** + 6 shipped-instances = **9 total rows mapped** | Porous flow, diffusion, antenna link (new DSL declarations). The other 6 YES rows are instances of already-shipped kernels (heat → thermal radiation / radioisotope heat; electromagnetism → Coulomb force; light → EM waves / diffraction / blackbody stars). Gravity and acoustic have no direct source-row counterpart: gravity's source row is "Newton's laws" (classified NO — equations of motion, not a field); acoustic has no explicit physics-tree row (nearest is "waves on strings/membranes," classified NEAR-FIELD ONLY). |
| **NEAR-FIELD ONLY** | **17** | Require per-particle corrections, tensor moments, or boundary-condition-specific solvers |
| **NO** (not a field) | **77** | Equations of motion, constitutive laws, temporal processes, quantum phenomena, etc. |
| **FORBIDDEN ABSENCES** | **3** | Named per operator rule; safe companion physics stays |
| **TOTAL ROWS** | **106** | 103 physics rows + 3 forbidden absences (excluded from count: summary table and detail headers) |

**New DSL declarations required:** 3 (porous_flow, diffusion, antenna_link). All fit the
existing grammar exactly. No new kernel_fn or aggregate types needed. Grammar note:
simultaneous activation of multiple `potential_1r` kernels requires either runtime
mutual-exclusion gating or a per-kernel output field extension — neither blocks
individual membrane use.

**Node size impact:** +48 B/node for 3 new kernels (160 → 176 B total). Still within the
8-storage-buffer budget if quantities are packed: mass/lum/charge/heat in vec4f, then
flux_sources / diffusion_sources / radiated_powers as three additional f32 buffers = 7
buffers total + the existing quants/bb_children/fields buffers.

**Falsifiers named before any run:** F-Y1 (porous flow, error < 5% at θ ≤ 0.3),
F-Y2 (diffusion superposition, error < 3%), F-Y3 (Friis transmission, error < 5% at
θ ≤ 0.3). All three are falsifiable: each names a concrete measurement and a limit that,
if exceeded, would prove the mapping invalid.
