# THE MEMBRANE INVENTORY

> **Provenance (banner added by G1-creature-graph, 2026-09-15; everything below it is verbatim).**
> The text below is a verbatim transcription of Astra's 42-item membrane inventory audit,
> received 2026-09-15 as paste attachment
> `pasted-text-20260915-081226-aee2c7fa.txt`. Transcribed unchanged for verbatim fidelity
> and credited to Astra. It is the canonical seed of the creature graph
> (`tools/creature_graph/`): every numbered item becomes a membrane **TYPE** (reusable
> definition, law, falsifier, priority); the creature's current state is held as
> **INSTANCES** of those types. The graph's `inventory_anchor` fields point back at the
> section numbers below. Nothing below this line was edited.
>
> **Continuation (G2-creature-graph, 2026-09-15).** This run loaded the inventory as
> the graph's seed: all 42 items now exist as TYPE objects (`type.A1`…`type.E42`,
> falsifiers verbatim, priorities + top-five build ranks) in
> `tools/creature_graph/data/authored/types.json`, built into the canonical store
> `tools/creature_graph/data/creature_graph.json`. Verified by
> `tools/creature_graph/acceptance.py` (28/28 green); see
> `docs/evidence/agent_fleet/SHIP/CREATURE_GRAPH/`.

---

# Membrane inventory audit

**The missing work extends beyond anatomy. You have containment, articulation, and behavior, but only partial models of attachment, transport, sensing, failure, and repair.** Those are the mechanisms that make different membranes mean different things to the player.

Below is a **42-item inventory of physical membrane families, their anatomical/world instances, and the product interfaces needed to teach them honestly**. It covers the stated vision; it is not a claim that all of biology or cosmology reduces to membranes.

I treat your supplied inventory as the implementation record. I did not locate the quoted “every bone” requirement in the local Markdown, so that requirement comes from your statement rather than independent repository verification.

### Priority key

- **P0 — Gate:** needed for the near creature’s intended claims and interactions; a reduced model is acceptable.
- **P1 — Expansion:** valuable subsequent gameplay or richer physiology.
- **P2 — Frontier:** molecular, developmental, ecological, or cosmic scope.

**A price gate cannot determine the anatomy.** The near product needs a convincing, falsifiable chain from **press → local deformation → sensing → physical response → changed consequence after damage**. It does not automatically need a simulated gut.

---

## First: the common membrane definition you are missing

Every physical membrane should identify:

1. **Its two sides:** region A and region B; either may be the environment.
2. **Its geometry:** area, thickness, orientation, rest shape, attachment topology.
3. **What it carries:** tension, bending, compression, shear, electrical charge.
4. **What crosses it:** water, gas, solutes, heat, light, electrical current.
5. **Its state:** strain, activation, permeability, damage, cure, temperature.
6. **Its failure transitions:** intact → yielding/debonding → open → repaired.
7. **Its accounting:** mass, momentum, energy, and material transferred.

A shared septum has two region owners but **one physical wall**. Opposite orientations used to calculate the two volumes must not double its mass or stiffness.

The governing pattern is:

\[
\text{stored energy}\rightarrow\text{force},\qquad
\text{potential difference}\rightarrow\text{flux},\qquad
\text{failure criterion}\rightarrow\text{topology change}.
\]

Three existing assumptions need qualification:

- **Triangles are not physical weights.** GPU residency is an implementation property. Physical mass comes from density integrated over volume and membrane area; remeshing must preserve it.
- **\(\delta=F/(4\pi\sigma)\) is not a universal indentation law.** For example, a small-slope tensioned annular membrane gives \(\delta=F\ln(R/a)/(2\pi T)\), where support radius \(R\) and contact radius \(a\) matter. Your coefficient needs its assumed geometry.
- **Exponential recovery describes viscoelastic relaxation, not healing.** Returning shape does not restore broken material, lost water, or consumed energy.

---

# A. Anatomy

### 1. Bone-associated sealed compartments — **P0**

**Definition/law.** Each intended skeletal segment owns a closed hydraulic region. With \(C_i=V_i-V_{0i}\),

\[
U_i=\frac{C_i^2}{2\kappa V_{0i}},
\qquad P_i=-\frac{\partial U_i}{\partial V_i}.
\]

This derives the existing water law independently for each region.

**Player moment.** Press a calf: its pressure changes locally; neighboring compartments respond through actual walls and attachments. Puncture it: the torso does not automatically drain.

**Reuse → new.** Reuse sealing, volume calculation, XPBD, cuts, and the skeleton. Add volumetric partitioning, internal walls, segment ownership, and independent fluid inventories.

**Falsifier:** *A compartment that cannot remain sealed when its neighbor is punctured is not a compartment.*

**Important:** these are your creature’s engineered compartments. Biological bones are not generally hermetic water bags. Also, **28 pins does not imply 28 bones**: derive segments from skeleton connectivity, including any explicitly defined terminal segments.

#### How to partition angled bones

**Triangle classification is a seed, not a seal.** Labels on the exterior do not define internal closing surfaces.

A workable construction is:

1. Define bone segments between connected pins in the **reference configuration**.
2. Fill the creature’s interior with a tetrahedral or volumetric representation.
3. Assign interior regions using distance to **bone segments**, constrained by anatomical connectivity. Unconstrained Euclidean proximity can incorrectly join an arm to the torso.
4. Create matching internal faces wherever neighboring volume elements have different labels.
5. Extract each region’s exterior patches plus internal faces into an oriented closed boundary.
6. Check positive volume, closure, connectedness, no overlaps/gaps, and conservation of the parent’s material inventory.

This is a standard **labeled-volume/interface** problem; CGAL’s domain representation explicitly labels interfaces by their two incident subdomains. [CGAL labeled domains](https://doc.cgal.org/latest/Mesh_3/classCGAL_1_1Labeled__mesh__domain__3.html)

For an initial controlled creature, oblique planes near joints can work: a plane can have any normal. The hard part is **branch junctions and conforming caps**, not bone angle. Do not repeatedly reclassify during motion—that would silently move material between compartments.

### 2. Load-bearing outer skin — **P0**

**Definition/law.** A thin elastic shell stores stretching and bending energy:

\[
U_s=\int_S W_{\rm stretch}\,dA+\int_S W_{\rm bend}\,dA.
\]

For isotropic material, stretching stiffness scales with \(Et\); bending stiffness is \(Et^3/[12(1-\nu^2)]\). Forces follow from differentiating energy. A viscoelastic internal state supplies relaxation and dissipation.

**Player moment.** Pressing, pinching, folding, and stretching produce consistent material responses.

**Reuse → new.** Reuse the surface mesh, pressure coupling, and recovery measurements. Add an explicit shell constitutive model, rest geometry, and consistent coupling to internal walls.

**Falsifier:** *A skin that cannot resist stretching cannot contain pressure.*

### 3. Septa, fascia, and sliding attachment layers — **P0**

**Definition/law.** Internal sheets divide regions or couple neighboring tissues. Bonded attachments transmit traction; sliding interfaces allow tangential motion while resisting interpenetration. A compliant attachment can use \(U=\tfrac12 k\|\Delta x\|^2\).

**Player moment.** Skin slides over a bending joint without becoming a pin-weight crease; pulling one patch loads a surrounding area.

**Reuse → new.** Reuse binding, shell mechanics, and the tensile web. Add finite attachment patches, slip/contact laws, and attachment failure. The same machinery can later suspend organs.

**Falsifier:** *An attachment that cannot slip or detach cannot demonstrate attachment strength.*

### 4. Structural bone walls — **P1; P0 if bone breakage is promised**

**Definition/law.** A load-bearing mineralized shell or beam. A reduced beam stores axial and bending energy,

\[
U=\tfrac12\int(EA\epsilon^2+EI\chi^2)\,ds.
\]

The law follows from integrating elastic stress through its cross-section.

**Player moment.** A limb resists bending; an overloaded structural member fractures.

**Reuse → new.** Reuse rigid skeleton geometry and breakable bonds. Add section geometry, elastic response, strength, and fracture. Keep this material distinct from the bone-associated water region.

**Falsifier:** *A bone that cannot bend or break cannot teach bone strength.*

### 5. Joint capsules — **P0**

**Definition/law.** A joint membrane is physically a **capsule enclosing the articulation**, with attachment rims and a fluid-containing cavity. It stores shell/fiber energy and transmits forces between its attachments. Joint torque follows from geometry:

\[
\tau=-\frac{\partial U_{\rm capsule}}{\partial\theta}.
\]

**Player moment.** Bending stretches the capsule; excessive loading can destabilize the articulation.

**Reuse → new.** Reuse pins, relative rotations, sealed cells, and shell attachments. Add capsule geometry, passive restraint, finite strength, and a fluid space if modeled.

**Falsifier:** *A joint whose restraints cannot fail cannot demonstrate dislocation.*

An indestructible hidden hinge must not continue supplying the restraint that the player supposedly severed.

### 6. Cartilage and lubricated bearing surfaces — **P1**

**Definition/law.** Cartilage supports compression through a solid matrix and pressurized interstitial fluid. Darcy flow,

\[
q=-\frac{k_{\rm perm}}{\mu}\nabla p,
\]

describes slow pressure-driven drainage; contact and lubrication determine tangential resistance.

**Player moment.** A loaded joint cushions, creeps, and moves differently when lubrication is impaired.

**Reuse → new.** Reuse contact and hydraulic accounting. Add porous tissue, permeability, and lubrication. Cartilage fluid pressurization and its contribution to lubrication are experimentally supported. [Cartilage load support](https://pmc.ncbi.nlm.nih.gov/articles/PMC2758165/)

**Falsifier:** *A bearing whose motion never changes with load or lubrication cannot teach lubrication.*

### 7. Active contractile tissue — **P0 for the “muscle” claim**

**Definition/law.** A muscle is active fiber-bearing tissue inside connective envelopes—not a membrane that contracts merely because it is sealed. A reduced model is

\[
F=aF_{\max}f_\ell(\ell)f_v(\dot\ell)+F_{\rm passive},
\qquad
\dot a=(u-a)/\tau_a.
\]

Fiber geometry converts force to joint torque. Mechanical work must come from an explicit energy source. Force–length–velocity functions are empirical constitutive relationships, not deductions from water compressibility. [OpenSim muscle formulation](https://pmc.ncbi.nlm.nih.gov/articles/PMC4397580/)

**Player moment.** An obstructed muscle develops tension; faster shortening reduces available force; opposing muscles can stiffen a joint.

**Reuse → new.** Keep intent commands and force caps. Add attachment-to-attachment paths, activation, contractile state, passive elasticity, and work accounting.

**Falsifier:** *A muscle that cannot stall under load cannot demonstrate contraction.*

### 8. Tendons, ligaments, and their insertions — **P0**

**Definition/law.** Tension-dominant connective structures with slack length. A first model is

\[
F=\frac{EA}{L_0}\max(0,L-L_0),
\]

derived from axial strain and cross-sectional stress. Nonlinear recruitment and failure can follow.

**Player moment.** Pulling a tendon moves its attached segment; cutting it removes that particular force path.

**Reuse → new.** Reuse the tensile web and skeleton. Add anatomical endpoints, slack, wrapping paths, and insertion strength.

**Falsifier:** *A tendon that can be cut without interrupting force transmission is not a tendon.*

### 9. Vessels, pump chambers, and valves — **P1**

**Definition/law.** Compliant fluid conduits and chambers. A lumped model uses \(C_v=dV/dp\), conservation \(\dot V=Q_{\rm in}-Q_{\rm out}\), and resistance \(Q=\Delta p/R\). A heart is an actively contracting chamber with directional valves.

**Player moment.** Squeeze a vessel, obstruct flow, feel a pulse, or observe downstream supply loss.

**Reuse → new.** Reuse cells, contraction, and transport interfaces. Add a connected flow network and valve states.

**Falsifier:** *A circulation that cannot be interrupted cannot demonstrate circulation.*

**Near-product decision:** no anatomical heart is necessary unless flow, pulse, or resource delivery is part of the promise.

### 10. Respiratory sacs, diaphragm, and airways — **P0 correction; P1 full respiration**

**Definition/law.** Gas volume obeys an appropriate gas law, such as \(pV=nRT\), coupled to airflow resistance and an actively moved wall. Water remains governed by its separate constitutive law.

**Player moment.** A torso expands; restraint reduces excursion; airway obstruction changes the cycle.

**Reuse → new.** Reuse rhythm generation, servos, and chamber boundaries. Add gas inventory, an airway, and actuator work—or replace “breathing” with volume-preserving active torso motion.

**Falsifier:** *A breath that cannot be obstructed cannot demonstrate breathing.*

The current 13.4 s allometric period is a model choice requiring a biological reference. It does not validate a water-volume oscillator.

### 11. Gut, mouth, and absorptive lining — **P1**

**Definition/law.** An active tube encloses transported contents; its wall contracts and selectively transfers substances. Species balance is

\[
\frac{dM_s}{dt}=\text{inflow}-\text{outflow}+\text{reaction}.
\]

Digestion requires reaction kinetics; absorption requires permeability.

**Player moment.** Feed the creature, watch material move, and connect intake to usable resources.

**Reuse → new.** Reuse chambers, active tissue, transport, and contact. Add contents, chemistry, and resource conversion.

**Falsifier:** *A gut that produces nourishment without consuming anything cannot demonstrate digestion.*

**Near-product decision:** optional. A declared finite actuator-energy reservoir is sufficient before simulated digestion exists.

### 12. Filtration and excretory barriers — **P2**

**Definition/law.** Selective filters separate fluid and solutes according to permeability, pressure, and chemical potential differences.

**Player moment.** Accumulated waste or salt changes function; a selective filter restores balance.

**Reuse → new.** Reuse vessel networks and selective transport. Add species inventories and regulated removal.

**Falsifier:** *A filter that cannot retain one substance while passing another cannot demonstrate filtration.*

---

# B. Materials and membrane lifecycle

### 13. Material-bearing surface and interior — **P0**

**Definition/law.**

\[
m=\int_\Omega\rho\,dV+\int_S\rho_s\,dA,
\qquad
F=-\frac{\partial U}{\partial q}.
\]

Mass comes from matter; surface/bulk energy determines response. Density, elasticity, hardness, strength, and toughness are different properties.

**Player moment.** Equal-sized objects made from different materials weigh and deform differently.

**Reuse → new.** Reuse GPU geometry and material tables. Add resolution-independent material accounting and explicit parameter units.

**Falsifier:** *A material that changes weight when retessellated cannot teach mass.*

### 14. Adhesive films, welds, and cured bonds — **P0**

**Definition/law.** An interface transmits traction according to separation and cure state: \(t=t(\delta,c)\). Cure evolves through a stated kinetic law \(\dot c=f(c,T,\ldots)\); separation work is the area under the traction–separation curve.

**Player moment.** Glue two objects, wait, then load the joint; an uncured joint fails sooner.

**Reuse → new.** Reuse the approved third-material glue model. Add contact area, cure history, thickness where relevant, and mixed-mode debonding.

**Falsifier:** *A glue joint that cannot fail at its interface cannot demonstrate adhesion.*

### 15. Distributed tensile web and reinforcement — **P0**

**Definition/law.** Fibers share load through force balance at nodes; each stores strain energy. Failure changes the graph, after which loads redistribute. “Weakest link” means the most critically loaded link relative to its strength, not simply the smallest strength number.

**Player moment.** Pulling a net tightens several paths; one break can trigger another.

**Reuse → new.** Complete the approved tensile-web machinery; share it with tendons, fascia, cloth, and reinforcement.

**Falsifier:** *A web that cannot redistribute load after a break cannot demonstrate a web.*

### 16. Yielding, scratches, and wear — **P0**

**Definition/law.** In a simplified fully plastic spherical indentation, \(F\approx H A\) and \(A\approx2\pi Rd\), giving

\[
d\approx\frac{F}{2\pi RH}.
\]

This assumes small penetration and a suitable hardness measure in pressure units. Sliding wear additionally needs distance, frictional work, and displaced/removed material.

**Player moment.** A hard tool leaves a persistent groove in softer material.

**Reuse → new.** Reuse the scratch battery and material pairs. Add permanent geometry/material state and debris accounting where removal is claimed.

**Falsifier:** *A scratch that disappears on unloading cannot demonstrate plastic damage.*

Mohs ranking is not interchangeable with indentation hardness in pascals.

### 17. Cracks, rupture, puncture, and delamination — **P0**

**Definition/law.** A fracture surface consumes energy. In a cohesive model,

\[
G_c=\int_0^{\delta_f}t(\delta)\,d\delta.
\]

Strength controls initiation; fracture energy controls separation work. Damage must be spatially located and change force/transport paths. [Cohesive fracture formulation](https://bleyerj.github.io/comet-fenicsx/tours/interfaces/intrinsic_czm/intrinsic_czm.html)

**Player moment.** A puncture leaks; a tear spreads; a peeled layer loses attachment.

**Reuse → new.** Reuse cuts and split guards. Add local damage, opening surfaces, crack connectivity, and coupled loss of sealing/strength.

**Falsifier:** *A rupture that leaves every physical connection intact is only a damage counter.*

### 18. Pores, holes, selective permeability, and leakage — **P0 holes; P1 selectivity**

**Definition/law.** For a simple inertial orifice,

\[
Q=C_dA_h\,\operatorname{sgn}(\Delta p)
\sqrt{\frac{2|\Delta p|}{\rho}}.
\]

A narrow viscous passage needs a different resistance law. Semipermeable transport can use \(J_v=L_p(\Delta p-s\Delta\pi)\), with osmotic pressure \(\pi\approx cRT\) in the dilute ideal limit.

**Player moment.** Hole size and pressure affect leakage; later, water passes a barrier that retains solute.

**Reuse → new.** Reuse cuts and chamber volumes. Add mass transfer between named regions, receiving fluid, and pressure-dependent flow.

**Falsifier:** *A hole through which nothing can pass cannot demonstrate permeability.*

After leakage, retain **mass conservation across the whole system**, not the original volume of the wounded cell. Transport follows potential differences and mass balance. [MIT membrane transport](https://www.ocw.mit.edu/courses/10-445-separation-processes-for-biochemical-products-summer-2005/resources/lecture_7_cooney/)

### 19. Patches, repair, scars, and regeneration — **P0 patch; P1 biological healing**

**Definition/law.** A patch adds material and interfaces; cure restores specified strength and reduces permeability. Biological repair additionally consumes resources and changes rest structure.

**Player moment.** Seal a leak and reload the repair; a weak patch can peel off.

**Reuse → new.** Reuse glue, cuts, transport, and the tensile web. Add repair geometry and separate measures of sealing, strength, and appearance.

**Falsifier:** *A repair that cannot leak or fail under renewed load cannot demonstrate repair quality.*

Do not implement healing by decrementing `damage_sum` while leaving topology unchanged.

### 20. Thermal boundaries, dissipation, and phase change — **P0 energy ledger; P1 thermal gameplay**

**Definition/law.** Heat transfer follows temperature differences, e.g. \(q=-k_T\nabla T\). Energy accounting includes mechanical work, stored elastic energy, heat, chemical energy, and losses. Phase change consumes latent heat.

**Player moment.** Repeated work warms tissue; heated glue cures differently; ice melts.

**Reuse → new.** Reuse force/velocity telemetry and materials. Add dissipation accounting first; temperature fields and phase inventory later.

**Falsifier:** *An actuator that delivers unlimited work without an energy source cannot teach energy.*

### 21. Growth, fission, and actual mitosis — **P1 growth/fission; P2 mitosis**

**Definition/law.** Growth changes rest geometry by adding material:

\[
\dot M=\text{intake}-\text{loss},\qquad
\dot A_0=\text{membrane production rate}.
\]

Division requires neck formation, membrane supply or stretching, separation work, and allocation of contents and state. Two equal spherical daughters of the same total volume require \(2^{1/3}\approx1.26\) times the parent sphere’s area.

**Player moment.** Feed material to a compartment; it grows, deforms, and eventually divides.

**Reuse → new.** Reuse splitting and sealing. Add rest-area growth, resources, neck mechanics, and conservative state transfer. Lipid-vesicle experiments demonstrate coupled growth and division, but not a universal division rule. [Protocell growth experiment](https://pmc.ncbi.nlm.nih.gov/articles/PMC2669828/)

**Falsifier:** *A split that creates membrane and contents for free cannot demonstrate growth.*

A plane cut is fragmentation. Without genome replication and segregation, call autonomous division **fission**, not mitosis.

### 22. Molecular membranes and chemical machinery — **P2**

**Definition/law.** Lipid membranes have bending energy, permeability, charge, and molecular composition. A common reduced bending model is

\[
U=\int_S\left[\frac{k_b}{2}(2H-C_0)^2+\bar kK_G\right]dA.
\]

Chemical reactions and transport follow species and energy balances; membrane proteins provide selective channels and active pumps.

**Player moment.** Osmotic swelling, ion gradients, selective transport, or photosynthetic energy conversion.

**Reuse → new.** Reuse shell, transport, and energy interfaces. Add species chemistry, electrochemical potentials, and molecularly justified parameters.

**Falsifier:** *A selective membrane with no selectivity cannot demonstrate a cell membrane.*

This family also supports future plant tissue and organelles; each does not require a separate universal physics engine.

---

# C. World

### 23. Ground contact and supporting substrate — **P0**

**Definition/law.** Ground is usually the boundary of a solid, not a stretched sheet. Normal nonpenetration supplies support; tangential friction satisfies a law such as \(\|F_t\|\le\mu F_n\). The substrate’s deformation determines contact compliance.

**Player moment.** Standing, slipping, pushing off, falling, and leaving an indentation.

**Reuse → new.** Reuse gravity and the calibrated spring. Qualify that spring’s material/geometry interpretation; verify friction, support moments, and equal reaction forces.

**Falsifier:** *A ground that cannot let a foot slip cannot teach traction.*

Matching \(mg\) at equilibrium does not validate transient contact behavior.

### 24. Water surfaces and liquid bodies — **P1; P0 if leaks need a pool**

**Definition/law.** A free surface is a fluid interface, not a sealed elastic skin. Surface energy \(U=\gamma A\) gives the Young–Laplace pressure jump \(\Delta p=\gamma(1/R_1+1/R_2)\). Hydrostatic pressure integration gives buoyancy \(F_b=\rho gV_{\rm displaced}\).

**Player moment.** Water spills, pools, sloshes, displaces around a limb, and supports floating objects.

**Reuse → new.** Reuse volume and boundary geometry. Add transport, changing free surfaces, buoyancy, and an appropriate reduced fluid solver.

**Falsifier:** *A liquid surface that cannot rearrange when displaced cannot demonstrate liquid.*

Do not reuse the skin’s \(4000\ \mathrm{N/m}\) tension as water’s surface tension.

### 25. Soil, sand, and porous ground — **P1**

**Definition/law.** Granular contacts and friction support load; a continuum approximation needs yield and compaction, such as \(\tau_{\rm yield}=c+\sigma_n\tan\phi\). Pore fluid adds pressure and drainage.

**Player moment.** Heavy feet sink; wet and dry ground behave differently.

**Reuse → new.** Reuse contact, friction, plasticity, and transport. Add granular or soil state.

**Falsifier:** *A soil that always springs back perfectly cannot demonstrate compaction.*

### 26. Atmosphere, wind, and acoustic pressure — **P1**

**Definition/law.** Gas is a bulk medium with an equation of state. Momentum transport produces wind loading; compressibility produces sound waves. A reduced drag law uses \(F_D=\tfrac12\rho C_DAv^2\), within its applicable regime.

**Player moment.** A gust pushes the creature; a pressure wave reaches it after a delay.

**Reuse → new.** Reuse force application, gas compartments, and pressure sensors. Add an ambient medium and propagation.

**Falsifier:** *A wind that moves the creature without exchanging momentum cannot teach wind.*

Atmospheric “layers” are not automatically material membranes.

### 27. Containers, cloth, ropes, tools, and constructed objects — **P1; one tool/patch in P0**

**Definition/law.** These instantiate existing shell, bulk, tensile, contact, and bond laws. A container’s boundary determines containment; a rope transmits tension; a tool’s geometry determines contact loading.

**Player moment.** Catch leaked water, tie a support, press with different tips, or patch a wound.

**Reuse → new.** Reuse the matter kernel and importer. Add useful object assemblies and interaction affordances, rather than new one-off physics.

**Falsifier:** *A container that cannot spill cannot demonstrate containment.*

### 28. Planetary and cosmic interfaces — **P2**

**Definition/law.** Planetary crusts can be elastic/plastic shells; oceans and atmospheres are fluid domains. Gravity remains a field, e.g. \(\nabla^2\Phi=4\pi G\rho\) in Newtonian gravity. An event horizon is a causal boundary, not an ordinary material membrane. [NASA horizon explanation](https://imagine.gsfc.nasa.gov/science/objects/black_holes1.html)

**Player moment.** Eventually connect shell mechanics to planetary structure and gravity to larger scales.

**Reuse → new.** Reuse material families where valid. Add scale-appropriate field equations and model transitions.

**Falsifier:** *A change of scale that changes the conservation laws without disclosure cannot teach scale.*

“Everything is a membrane” should remain an organizing vision, not an incorrect universal constitutive law.

---

# D. Senses and response

### 29. Local tactile receptor surfaces — **P0**

**Definition/law.** A finite receptor patch measures local traction or deformation:

\[
s=\frac1A\int_A t_n\,dA,
\]

followed by specified filtering, saturation, and thresholding.

**Player moment.** The creature responds differently to a calf press, a torso press, and a broad squeeze.

**Reuse → new.** Reuse contacts, pressure telemetry, and flinch plumbing. Add spatial sensor patches and their signal model.

**Falsifier:** *A touch response that survives disconnecting its touch sensor cannot demonstrate sensing.*

One uniform cell pressure cannot identify where on that cell the touch occurred.

### 30. Proprioception, load sensing, and balance sensing — **P0**

**Definition/law.** Sensors measure joint configuration, tissue extension, tendon force, angular motion, and specific force. These are separate observables; acceleration is not an omniscient measurement of body tilt.

**Player moment.** A loaded limb braces, an unsupported foot searches, and a leaning body attempts recovery.

**Reuse → new.** Reuse measured joints, contacts, lean gates, and stance logic. Add explicit sensor ownership, latency, and failure.

**Falsifier:** *A balance controller that knows an unmeasured state perfectly cannot demonstrate embodied feedback.*

### 31. Axonal membranes and propagation — **P0 delayed graph; P2 detailed electrophysiology**

**Definition/law.** Charge conservation gives a compartment cable model:

\[
C_j\dot V_j=
\sum_k\frac{V_k-V_j}{R_{jk}}-I_{\rm ion,j}+I_{\rm input,j}.
\]

Active ionic conductances support action potentials. A cheap declared abstraction uses event travel time \(L/v\), refractory state, and connection failures. Passive cable diffusion alone is not a full spike model. [NEURON derivation](https://www.neuron.yale.edu/neuron/static/papers/nc97/nc3p1.htm)

**Player moment.** A distal stimulus produces a delayed response; interrupting the path removes it.

**Reuse → new.** Reuse reflex events and skeleton paths. Add a connected signaling graph and scheduled propagation.

**Falsifier:** *A nerve that transmits across a cut cannot demonstrate a nerve.*

Do not introduce artificial long delays merely to make them visible; display the signal timeline separately.

### 32. Synapses, reflex integration, and adaptation — **P0**

**Definition/law.** A junction converts arriving signals into downstream activation. A minimal state can integrate input, decay, threshold, and recover; for example \(\tau\dot s=-s+\sum w_i\,\text{input}_i\). These are chosen reduced circuit dynamics, not membrane mechanics.

**Player moment.** A rapid tap startles, sustained load braces, repeated harmless taps habituate.

**Reuse → new.** Reuse intent machinery and the three candidate reflexes. Add explicit pathways, delay, hysteresis, adaptation, and causal logs.

**Falsifier:** *A reflex whose response is unchanged by severing its sensory path cannot demonstrate a reflex.*

A spinal reflex is still nervous-system computation; “no central planner” is the useful distinction.

### 33. Eyes: optical boundary, sensor, eyelid, and gaze actuator — **P0**

**Definition/law.** An eye admits light through an aperture onto a photosensitive surface. The minimum honest abstraction is a low-resolution eye camera or geometric visibility sensor with field of view and occlusion. Gaze changes through bounded actuation; an eyelid is an opaque shutter.

**Player moment.** The creature notices the approaching in-world hand/tool, looks toward it, and loses new visual evidence when it is hidden.

**Reuse → new.** Reuse rendering, ray tests, pins, and servos. Add an eye-local sensing viewpoint, delayed tracking, and gaze limits.

**Falsifier:** *An eye that acquires new information through an opaque cover cannot demonstrate sight.*

A decorative eyeball aimed at globally known cursor coordinates is not visual sensing. Corneal deformation and detailed refraction can wait.

### 34. Eardrums and vibration sensors — **P1**

**Definition/law.** A pressure difference drives a damped membrane mode:

\[
m_e\ddot x+c_e\dot x+k_ex=A_e\Delta p.
\]

This follows directly from force balance.

**Player moment.** A sound or ground vibration causes a response with direction- and distance-dependent timing.

**Reuse → new.** Reuse pressure signals and reflex integration. Add acoustic propagation or a declared reduced sound sensor.

**Falsifier:** *An ear that hears equally well when acoustically isolated cannot demonstrate hearing.*

### 35. Chemical and thermal receptor interfaces — **P2**

**Definition/law.** Chemical reception can use binding kinetics,

\[
\dot b=k_{\rm on}c(1-b)-k_{\rm off}b.
\]

Thermal sensing follows heat exchange with the receptor, not instant access to every object’s temperature.

**Player moment.** The creature detects a nearby chemical source or reacts after touching something warm.

**Reuse → new.** Reuse transport, thermal state, and sensory circuits. Add receptor parameters and environmental fields.

**Falsifier:** *A receptor that responds without its stimulus reaching it cannot demonstrate reception.*

---

# E. Product interfaces

These are **software and interaction boundaries, not physical membranes**. Their “laws” are architectural invariants. They are nevertheless necessary to keep the physics honest.

### 36. Player-to-world mechanical interface — **P0**

**Definition/law.** Pressing applies a finite force over a finite contact footprint. A virtual compliant manipulator may use \(F=k_h(x_{\rm target}-x)+c_h(v_{\rm target}-v)\), with declared caps. External work is \(\int F\cdot dx\).

**Player moment.** Press, hold, release, pull, and compare tools.

**Reuse → new.** Reuse press input and contact. Add consistent units, contact geometry, and force/work records.

**Falsifier:** *A press that deforms geometry without applying the corresponding load cannot teach force.*

### 37. Simulation-to-browser state boundary — **P0**

**Definition/invariant.** Rendered deformation, displayed pressure, and visible response must refer to consistent authoritative states. Streaming carries timestamps and topology versions; interpolation must not invent causal events.

**Player moment.** The dimple, pressure rise, and flinch visibly agree.

**Reuse → new.** Reuse streaming and readback instrumentation. Add causal alignment, stale-state handling, and measured end-to-end latency.

**Falsifier:** *A displayed response that precedes its authoritative cause cannot teach causality.*

### 38. Measurement and explanation interface — **P0**

**Definition/invariant.** Every shown quantity has units, provenance, model assumptions, and appropriate precision. Display numerical damping and sampling limitations when they affect the lesson.

**Player moment.** Open a cross-section, select one compartment, and explain why its pressure or tendon load changed.

**Reuse → new.** Reuse the HUD and lesson measurements. Add region/boundary inspection and synchronized plots.

**Falsifier:** *A measurement that cannot be checked against an independent calculation cannot teach measurement.*

Your earlier frequency results make amplitude loss and aliasing part of this requirement.

### 39. Import, sealing, and resolution boundary — **P0**

**Definition/invariant.** Imported geometry must acquire valid physical regions, materials, attachments, and sensor locations. Refinement/coarsening preserves mass and converges toward the same physical response.

**Player moment.** A new creature works for understandable geometric reasons, not because its topology accidentally resembles the test mesh.

**Reuse → new.** Reuse classify→bind→seal and the five-shape gallery. Add internal partition tests, self-intersection checks, material ownership, and deformation-time validity.

**Falsifier:** *An importer that passes only before the first joint bends has not imported a physical creature.*

Preserve intended torus holes; “watertight” does not mean “fill every cavity.”

### 40. Persistence, replay, and topology history — **P0**

**Definition/invariant.** Saving preserves the complete physical state: fluid inventories, rest geometry, wounds, cure, activation, delayed signals, and stable region identities.

**Player moment.** Return to the same wounded or repaired creature and continue the experiment.

**Reuse → new.** Reuse state streaming and test records. Add versioned physical saves and topology-event history.

**Falsifier:** *A wound that disappears on reload is not persistent damage.*

### 41. Lesson and counterfactual boundary — **P0**

**Definition/invariant.** Success depends on the taught mechanism. A test changes the relevant cause while holding confounders controlled; transfer tests use unfamiliar geometry or parameters.

**Player moment.** Predict which chamber leaks, which tendon moves the limb, or whether a patch will hold.

**Reuse → new.** Reuse ten lessons, falsifier machinery, and blind judges. Add mechanism ablations and transfer cases.

**Falsifier:** *A lesson passed equally well after disabling its claimed law does not teach that law.*

### 42. Creature-care loop and value gate — **P0**

**Definition/invariant.** The product joins discovery, consequence, recovery, and renewed interaction. The loop must remain understandable without reading the engineering HUD. Accessibility and usable input are part of that boundary.

**Player moment.** Notice → press → receive an answer → investigate → change something → see a lasting consequence.

**Reuse → new.** Reuse the creature, lessons, and evaluation system. Add a coherent short experience and external human evaluation of comprehension, attachment, and value.

**Falsifier:** *A creature whose “aliveness” survives replacing feedback with disconnected replay has not yet proved responsive aliveness.*

A machine-checkable $25 gate can validate conditions; willingness to pay still requires evidence from people.

---

# Top five build order

## 1. Bone-associated compartment graph, shared septa, and inspection

Replace height bands with valid skeletal-segment regions. Show their boundaries and independent pressures. Begin with one articulated limb, then cover the skeleton.

**Falsifier:** *A compartment that cannot survive its neighbor being punctured is not a compartment.*

## 2. One complete physical force path across a joint

Build **contractile tissue → tendon → bone segment → capsule/ligament restraint**, with skin sliding over the joint. Commands enter through the existing intent machinery.

**Falsifier:** *A tendon that can be severed without changing the commanded movement is not carrying that movement.*

## 3. Local touch, delayed reflexes, and honest gaze

Give the creature enough sensing to answer the actual stimulus, with support-aware reactions and explicit signal paths. Repair or relabel the water-volume “breathing” immediately.

**Falsifier:** *A response that survives disconnecting its sensor has not demonstrated sensing.*

## 4. Spatial rupture → leak → patch → reload

Make one wound change both containment and mechanics; make a patch restore measurable properties; preserve the result across saves.

**Falsifier:** *A repair that cannot fail under renewed load cannot demonstrate repair.*

## 5. A HUD-independent press–answer–investigate–repair experience

Align browser state and measurements, add cross-section inspection, then test unfamiliar presses and disconnected-replay controls with people.

**Falsifier:** *An experience understood only through the engineering HUD has not yet taught through the creature.*

**That is the near-product target: a connected, inspectable, interruptible body. Heart, gut, molecular chemistry, and cosmic membranes belong in the inventory, but they do not outrank proving that chain.**
