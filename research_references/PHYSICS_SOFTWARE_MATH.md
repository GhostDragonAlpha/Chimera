# THE PHYSICS OF SOFTWARE — every math concept the simulators encompass

> Built 2026-07-31 on the operator's ruling: **"drive all the physics concepts that pieces of
> software encompass — we're just interested in the math, because math isn't copyrightable."**
>
> Legal shape of this document: **equations and algorithms are facts; facts are not
> copyrightable.** What IS copyrightable is the source code that implements them. So every
> entry below names the software that proves the concept matters, then states the MATH from
> its canonical published source (paper, textbook, standard) — never from the code. We
> reimplement from the paper and cite it. This is the same clean-room route the acquisition
> plan uses for data (ACQUISITION_PLAN.md): measure or derive, never copy.
>
> Master tree: **`PHYSICS_OF_EVERYTHING.md`** (same directory) — humanity's complete
> physics, sourced the same way, minus the forbidden branches. This file is the
> simulator's-eye view; that one is the whole forest.
>
> Purpose: this is the complete periodic table of game physics. When a membrane asks "what
> physics do I need?", the answer is a row here, with the source to derive from. The verbs in
> `Chimera/docs/THE_STORY.md` (theThrust, theDig, theBalance, theGrow, theScan, theNavigate,
> theShoot, theMelee, theEVA) and the human menu (A/B/C/F/G items) map onto these rows.
>
> **The operator's sharpening (2026-07-31): "we don't need the code, we just need the physics
> — because the physics IS the code in my development methodology."** Consequence: no row in
> this catalog terminates in a library call or a ported implementation. Each row's terminal
> form is a membrane — `story.md` + `physics.py` + `numbers.json` — whose physics.py derives
> the row's equation from first principles and the measured inputs, then proves it through
> the engine (orient → frame → question → classify → render → dyad → prove). MuJoCo and the
> other engines named here are computing substrates and witnesses, not sources: we hand them
> our measured parameters, we never adopt their internals as our law. A law that lives in
> someone else's code is a law we do not hold.

---

## 1. RIGID-BODY DYNAMICS & CONTACT — MuJoCo (ours), Bullet, PhysX, ODE, DART

The core of every physics engine. One equation system, five decades of refinement.

| concept | the math | canonical source | CHIMERA consumer |
|---|---|---|---|
| Newton-Euler equations of motion | **M(q)q̈ + c(q,q̇) = τ + J(q)ᵀ f** — mass matrix M, Coriolis/centrifugal bias c, applied torque τ, contact force f mapped by Jacobian J | Featherstone, *Rigid Body Dynamics Algorithms* (2008) | every membrane that moves |
| Composite rigid body / recursive Newton-Euler | O(n) computation of M and c per joint tree | Featherstone 2008, ch. 6–7 | MuJoCo already solves it for us |
| Semi-implicit (symplectic) Euler | vₜ₊₁ = vₜ + a·Δt; xₜ₊₁ = xₜ + vₜ₊₁·Δt — position uses the NEW velocity; unconditionally better energy behavior than explicit Euler | Hairer et al., *Geometric Numerical Integration* | integrator choice everywhere |
| Signorini contact condition | fₙ ≥ 0, d ≥ 0, fₙ·d = 0 — no pulling, no penetration, force only when touching | Signorini (1933); Stewart & Trinkle 1996 | theGround, theAnkle, B1 foot IK |
| Coulomb friction cone | |fₜ| ≤ μ fₙ — tangential force bounded by normal force × friction coefficient; **μ measured** (Zhang & Mak, Elkington — in repo) | Coulomb (1785); measured μ in `research_references/human/skin_friction/` | theGrip, theStance, walking |
| Contact as convex optimization (MuJoCo's core trick) | min_f ½ fᵀA f + bᵀ f subject to cone constraints — soft contact modeled as spring-damper, solved as one convex problem, not impulse iteration | Todorov 2011, "Convex and analytically-invertible dynamics with contacts and constraints" | why we run MuJoCo and not Bullet |
| Sequential impulses (Bullet/PhysX alternative) | iterate velocity-level impulse updates per contact until convergence; Baumgarte bias adds λ/Δt·d position correction | Catto (GDC 2005–2014), "Iterative dynamics with temporal coherence" | comparison baseline; grasp why MuJoCo's answer differs |
| Restitution & compliance | e = v_out/v_in normal velocity ratio; MuJoCo solref = (timeconst, dampratio) → critical damping k = 1/(d²·timeconst²) | MuJoCo docs, Computation chapter | foot-ground feel (B1) |
| GJK distance algorithm | iterative simplex closest-point between convex shapes; support function s(d) = argmax_x x·d per shape | Gilbert, Johnson, Keerthi 1988 | collision queries |
| EPA penetration depth | expanding polytope over the Minkowski difference after GJK reports overlap | van den Bergen 2001 | contact depth for soft contact |
| SAT (separating axis) | boxes/OBBs overlap iff no axis separates them; 15 axes for OBB-OBB | Gottschalk et al. 1996 | OBB colliders |
| Friction pyramid / torsional & rolling friction | cone linearized to 2·n_dir pyramid for the solver; MuJoCo adds torsional (τ ≤ μₜ·r·fₙ) and rolling terms | MuJoCo docs; Todorov 2010 | foot yaw slip, stone tumbling |

## 2. MUSCLE & BIOLOGICAL ACTUATORS — OpenSim, MyoSuite, MuJoCo muscle

The 290-muscle body already runs on this math; this is the table it came from.

| concept | the math | canonical source | consumer |
|---|---|---|---|
| Hill-type muscle model | F = F₀·(a·f_L(l)·f_V(v) + f_PE(l))·cos α — max isometric force F₀ scaled by active force-length, force-velocity, passive force-length curves and pennation angle α | Zajac 1989, "Muscle and tendon: properties, models, scaling" | myobody, theThrust, gait |
| Force-length curve | f_L = exp(−((l/l₀ − 1)/W)²) — Gaussian-ish active curve, width W ≈ 0.5–0.6 | Millard et al. 2013 | training reward terms |
| Force-velocity curve | f_V hyperbola: (v_max + v)/(v_max − v/v_scale) contraction side; enhanced eccentric plateau ~1.5–1.8·F₀ | Hill 1938; Millard 2013 | jump landing, stumble |
| Tendon series elasticity | nonlinear toe region then linear: f_T ≈ 0 toe, k_t·(l_T − l_slack) above ~2–3% strain | Millard et al. 2013; Thelen 2003 | elastic energy return in gait |
| Activation dynamics | ȧ = (u − a)/τ(u,a), τ_act ≈ 10 ms, τ_deact ≈ 40 ms — first-order excitation→activation lag | Zajac 1989; Thelen 2003 | policy response time (gait training) |
| Moment arms | τ_joint = Σᵢ rᵢ(q)·Fᵢ — muscle force × joint-dependent moment arm | Rajagopal 2016 model (in repo) | torque from muscle force |
| Metabolic cost of muscle | udot ≈ activation heat + work: models of Umberger/Bhargava — Ḗ per muscle from a, v, F | Umberger 2003; Bhargava 2004 | theSweep, endurance, load carriage |

## 3. POSITION-BASED DYNAMICS — PBD/XPBD (Müller/Macklin), cloth, soft body, hair

Not force-based: project constraints directly on positions. Rock-solid at any timestep.

| concept | the math | canonical source | consumer |
|---|---|---|---|
| Constraint projection | solve C(x) = 0 per constraint by moving positions along ∇C weighted by inverse masses | Müller et al. 2007, "Position Based Dynamics" | cloth suit, cables, soft tissue |
| XPBD compliance | α̃ = α/Δt² — physical stiffness made timestep-independent; Δλ = (−C − α̃λ)/(Σ wᵢ|∇Cᵢ|² + α̃) | Macklin et al. 2016, "XPBD" | anything elastic |
| Distance/stretch constraint | C = |x₁ − x₂| − rest | Müller 2007 | suit fabric, tendons (alt. model) |
| Volume/tetrahedral soft body | C = (1/6)(x₂−x₁)·((x₃−x₁)×(x₄−x₁)) − V₀ | Müller 2007 | soft tissue, pressure suit volume |
| Shape matching | extract rigid transform from deformed cluster, pull points toward matched shape | Müller et al. 2005 | deformable props |
| Long-range attachments (LRA) | clamp distance to anchor, zero iterations — inextensible rope | Kim et al. 2012 | tethers, winch line (theDig/recovery) |

## 4. GRANULAR MEDIA — DEM (LIGGGHTS, Yade, MercuryDPM)

The ground is grains; the mine eats them. theDig and theMining live here.

| concept | the math | canonical source | consumer |
|---|---|---|---|
| Hertz contact (normal) | Fₙ = (4/3)·E*·√R*·δ^1.5 — elastic spheres, δ overlap, E*/R* effective modulus/radius | Hertz 1882; Cundall & Strack 1979 (DEM) | theDig, stones in theGround |
| Mindlin tangential friction | incremental tangential stiffness with Coulomb cap |Fₜ| ≤ μFₙ | Mindlin & Deresiewicz 1953 | grain shear, angle of repose |
| Angle of repose | tan θ_repose ≈ μ_eff — pile slope set by inter-grain friction (measured: soil 30–40°) | soil mechanics texts; measured per soil type | terrace mine slopes (aTerraceMine) |
| μ(I) rheology (dense granular flow) | μ(I) = μ_s + (μ₂−μ_s)/(I₀/I + 1), I = inertial number γ̇d/√(P/ρ) — granular flow behaves as a fluid with shear-rate-dependent friction | GDR MiDi 2004; Jop et al. 2006 | ore flow, landslides, digging feel |
| Janssen effect | silo wall pressure saturates with depth: P(z) = P_∞(1 − e^(−z/λ)) | Janssen 1895 | hoppers, ore bins |

## 5. ORBITAL MECHANICS — GMAT, SPICE, KSP, Orekit

Where simulation has its strength: the space game is this math.

| concept | the math | canonical source | consumer |
|---|---|---|---|
| Vis-viva | v² = GM·(2/r − 1/a) — speed anywhere on a conic from energy alone | Bate, Mueller & White, *Fundamentals of Astrodynamics* | theNavigate, ship flight |
| Kepler's equation | M = E − e·sin E — solve for eccentric anomaly by Newton iteration (3–5 steps) | Bate/Mueller/White | orbit propagation |
| Classical orbital elements | (a, e, i, Ω, ω, ν) — six numbers fully specify an orbit; h = r×v gives i, Ω; e-vector gives e, ω | Vallado, *Fundamentals of Astrodynamics* | theSolarSystem (already deriving) |
| Sphere of influence (patched conics) | r_SOI = a·(m/M)^(2/5) — switch two-body frames at this radius | Bate/Mueller/White | planet ↔ moon ↔ sun transfers |
| Hohmann transfer | Δv₁ = √(GM/r₁)·(√(2r₂/(r₁+r₂)) − 1); Δv₂ = √(GM/r₂)·(1 − √(2r₁/(r₁+r₂))) | Hohmann 1925 | theNavigate burns |
| Lambert's problem | given r₁, r₂, Δt → the transfer conic; universal-variable or Izzo's solver | Izzo 2015, "Revisiting Lambert's problem" | rendezvous, course plotting |
| Symplectic N-body (leapfrog/Verlet) | KDK: kick-drift-kick — energy bounded over aeons, unlike RK | Wisdom & Holman 1991 | solar system integration |
| Tsiolkovsky rocket equation | Δv = v_e·ln(m₀/m_f) — the tyranny every ship answers to | Tsiolkovsky 1903 | theThrust (ship), fuel |
| J2 oblateness perturbation | secular nodal regression Ω̇ = −(3/2)J₂(μ/R²)(R/p)²cos i | Vallado | station orbits |

## 6. FLUIDS — SPH (DualSPHysics, GPUSPH), shallow water

Oceans, atmospheres in motion, propellant slosh. Lower priority; listed for completeness.

| concept | the math | canonical source | consumer |
|---|---|---|---|
| SPH kernel summation | ρᵢ = Σⱼ mⱼ W(rᵢⱼ,h); forces from ∇W — poly6/spiky kernels | Monaghan 1992; Müller et al. 2003 | theOcean surface, splashes |
| Tait equation of state | P = B((ρ/ρ₀)^γ − 1), γ = 7 — weakly compressible water | Monaghan 1994 | pressure in SPH |
| Shallow water equations | ∂h/∂t + ∇·(hu) = 0; ∂u/∂t + u·∇u = −g∇(h+b) — 2D heightfield ocean | Saint-Venant 1871 | ocean waves on aTerrain |
| Hydrostatic atmosphere | P(h) = P₀·exp(−Mgh/RT) — the exponential atmosphere | theAtmosphere already derives this | flight ceilings, breath |

## 7. LIGHT TRANSPORT — PBRT, Mitsuba, 3DGS (our renderer's lineage)

The other half of "light and physics". Measured inputs now in repo (CVRL, refractiveindex.info, OMLC).

| concept | the math | canonical source | consumer |
|---|---|---|---|
| The rendering equation | Lₒ(x,ω) = Lₑ + ∫ f_r(x,ωᵢ,ωₒ)·Lᵢ(x,ωᵢ)·(n·ωᵢ) dωᵢ | Kajiya 1986 | every pixel |
| GGX/Cook-Torrance microfacet BRDF | f_r = F(ω·h)·G(l,v,h)·D(h) / (4(n·l)(n·v)); D_GGX = α²/(π((n·h)²(α²−1)+1)²) | Cook & Torrance 1982; Walter et al. 2007 | suit metal, rock, visor |
| Schlick Fresnel | F(θ) = F₀ + (1−F₀)(1−cosθ)⁵, F₀ = ((n−1)/(n+1))² — F₀ from **measured n,k** (refractiveindex.info, in repo) | Schlick 1994 | all specular |
| Oren-Nayar diffuse (rough surfaces) | retro-reflective rough diffuse; regolith/moon-dust behavior | Oren & Nayar 1994 | lunar/regolith surfaces |
| Beer-Lambert extinction | T(d) = e^(−σ_t·d) — absorption+scattering through media | Beer 1852; **measured σ from OMLC** (in repo) | skin, ocean, atmosphere |
| Diffusion dipole BSSRDF | multi-scale subsurface scattering: Rd from σ′_s, σ_a, η — the skin light model | Jensen et al. 2001 | theSkin (already has Jacques; this is the full version) |
| Rayleigh scattering | β(λ) ∝ 1/λ⁴·(n²−1)² — why the sky is blue, sunsets red | Rayleigh 1871; Preetham 1999 sky model | theAtmosphere renders |
| Mie scattering | aerosol haze, size ~λ; Henyey-Greenstein phase p(θ) = (1−g²)/(4π(1+g²−2g cosθ)^1.5) | Mie 1908; HG 1941 | dust, fog, visor bloom |
| Spectral→XYZ→RGB | X = ∫ L(λ)x̄(λ)dλ etc. — **measured CMFs in repo** (`eye/ciexyz1931_cmf.csv`) | CIE 1931 (measured) | every color the engine outputs |
| 3D Gaussian splatting | anisotropic Gaussians Σ = RSSᵀRᵀ projected to 2D, α-composited front-to-back | Kerbl et al. 2023 | our renderer's core |
| ACES / Reinhard tone mapping | filmic curve mapping HDR→display; Reinhard: L/(1+L) | Reinhard 2002; ACES (Academy) | theEye's adaptation, final image |

## 8. THE EYE AS A CAMERA — vision science software (ISETBIO, psychophysics toolboxes)

theEye is a stub; its math is measured, and its functions are now in the repo.

| concept | the math | canonical source | consumer |
|---|---|---|---|
| Luminous efficiency | photopic V(λ) peak 555 nm; scotopic V′(λ) peak 507 nm — **measured CSVs in repo** | CIE 1924/1951 | day/night visibility |
| Dark adaptation | threshold falls ~3–4 log units over ~30 min, rod-cone break at ~8 min (Hecht, measured tables archived) | Hecht et al. 1937 | walking out of a lit base into night |
| Unified pupil formula | d = f(luminance, field diameter, age, monocular) — mm | Watson & Yellott 2012 | exposure, depth of field |
| Schematic eye ray tracing | 4 aspheric surfaces + GRIN lens; corneal power ~43 D, total ~60 D | Navarro 1985/2009 (in repo) | what the visor must correct |
| Skin emissivity | ε = 0.98 ± 0.01 (8–14 µm), pigmentation-independent (measured) | Villaseñor-Mora 2009 (in repo) | thermal visor mode, theSweep radiation |

## 9. VEHICLE DYNAMICS — CarSim, rFactor-class tire models

The rover in Act I.

| concept | the math | canonical source | consumer |
|---|---|---|---|
| Pacejka magic formula | F = D·sin(C·atan(Bα − E(Bα − atan Bα))) — tire force from slip angle α; B,C,D,E fitted per tire | Pacejka, *Tire and Vehicle Dynamics* | rover handling on regolith |
| Slip ratio / combined slip | σ = (v_wheel − v_contact)/v; friction ellipse combines lateral+longitudinal | Pacejka | traction diff-lock verb |
| Suspension: spring-damper + anti-roll | F = k·x + c·ẋ per corner | vehicle dynamics texts | ride over terrain |

## 10. CHARACTER ANIMATION — motion matching (Ubisoft/EA), IK solvers

The human menu items A5+G1 (motion matching) and B1 (foot IK) are these rows.

| concept | the math | canonical source | consumer |
|---|---|---|---|
| Motion matching | feature vector (joint positions/velocities + future trajectory points) → k-NN over the mocap library per frame window; **library = CMU full DB, in repo** | Clavet 2016, "Motion Matching and the Road to Next-Gen Animation" | A5+G1 |
| Inertialization blending | critically-damped spring on pose offsets — no foot sliding on transitions | Bollo, "Inertialization: high-performance animation transitions" | gait transitions |
| CCD inverse kinematics | iterate joints end-to-root, rotate each toward target | well-known heuristic | quick IK |
| FABRIK | forward/backward reach passes along the chain, joint-length preserving | Aristidou & Lasenby 2011 | **B1 foot IK** |
| Damped least squares (Jacobian) | Δq = Jᵀ(JJᵀ + λ²I)⁻¹ e — singularity-robust IK | Buss & Kim 2005 | precise foot placement |
| Foot phase from GRF | stance/swing segmentation from measured GRF curves | gait_normative.json (in repo) | IK target timing |

## 11. PHYSIOLOGY — Fiala thermal, Pennes bioheat, respiratory models

| concept | the math | canonical source | consumer |
|---|---|---|---|
| Pennes bioheat equation | ρc ∂T/∂t = ∇(k∇T) + q_met + ω_bρ_bc_b(T_blood − T) — tissue heat with blood perfusion | Pennes 1948 | theSweep's full version |
| Metabolic rate vs activity | MET multiples of resting ~1.2 W/kg — measured compendium + Apollo data (in repo) | Compendium of Physical Activities; TN D-7883 | theBreath, theSweep, exertion |
| Ventilation vs exertion | V̇E rises ~linearly with V̇O₂ to anaerobic threshold | standard exercise physiology | breath audio/visor fog |

## 12. TERRAIN EVOLUTION — erosion sims, geomorphology

| concept | the math | canonical source | consumer |
|---|---|---|---|
| Thermal weathering (talus) | transport material downslope wherever local slope > talus angle | Musgrave et al. 1989 | mountain aging |
| Stream power incision | E = K·A^m·S^n — erosion rate from drainage area and slope | Whipple & Tucker 1999 | river valleys over geological time |

---

## HOW TO USE THIS TABLE

1. A membrane names its question → find the row → derive from the CANONICAL SOURCE column
   (paper/book/standard), never from the software's code.
2. The measured inputs for most rows are already in the repo after the 2026-07-31 acquisition
   sweep (ACQUISITION_PLAN.md): friction μ, muscle parameters, CMFs, n,k constants, mocap,
   force plates, NASA suit/g numbers.
3. Rows with no measured input yet say so here — that is the shopping list, and only the
   operator may strike a row or declare "typed is fine" for one.
4. Software named in each header is proof the concept is worth having — a market of
   engineering effort voted for it. The math is the law; the software is only a witness.
