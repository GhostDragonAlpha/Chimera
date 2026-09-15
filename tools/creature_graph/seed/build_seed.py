"""Build the AUTHORED seed files for the creature graph.

Outputs (all under tools/creature_graph/data/authored/):
  types.json         the 42 membrane TYPES from docs/THE_MEMBRANE_INVENTORY.md
                     (Astra, 2026-09-15): reusable definitions -- law, falsifier
                     (verbatim), priority, inventory anchor, build rank.
  instances.json     the creature's CURRENT state: the 4 verified height-band
                     compartments (measured), the selected limb's bone segments
                     (measured pins), per-bone compartments as SPECIFIED
                     placeholders (THE ANATOMICAL COMPARTMENT LAW), septa, skin.
  mechanisms.json    actuators / sensors / pathways / materials / models /
                     parameters + validation evidence (independent of the
                     implementation ladder).
  requirements_tasks.json  AUTHORED requirements + experiences + work items
                     (tasks follow authored requirements, never imported facts).

Everything here is AUTHORED content. Engine-extracted data lands in SEPARATE
files (data/extracted/) and is joined by stable IDs only -- a re-extract can
never erase planned anatomy.

Deterministic: re-running rewrites identical bytes (no timestamps in payload).
"""

import json
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "authored")

WATER_LAW = "P = -(V - V0)/(kappa * V0), kappa = 4.6e-10 Pa^-1 (alpha = kappa*V0 in the coupled XPBD form C = V - V0)"

# provenance constants (measured facts, cited on the objects that carry them)
BODY_ATLAS_PROV = {
    "source": "tools/body_atlas.json (camera-awareness atlas, built by tools/body_atlas.py)",
    "fetched_utc": "2026-09-14T05:28:03+00:00",
    "engine_ticks_at_fetch": 208588,
}
LIVE_PROV = {
    "source": "GET http://127.0.0.1:8107/tick_state (light poll, no /frame)",
    "fetched_utc": "2026-09-15T13:47:00Z",
    "engine_ticks": 731615,
    "note": "live state belongs to the ENGINE; the graph stores this snapshot read-only",
}
SHIP_GOAL_PROV = {
    "source": "docs/THE_SHIP_GOAL.md, THE ANATOMICAL COMPARTMENT LAW (operator correction, 2026-09-13)",
}
BRIEF_PROV = {
    "source": "operator mission brief of record, 2026-09-15 (pasted-text-20260915-084209-ee5dd0b0.txt)",
}

# ----------------------------------------------------------------------------
# The 42 membrane TYPES. Falsifiers are VERBATIM from docs/THE_MEMBRANE_INVENTORY.md
# (Astra, 2026-09-15). build_rank: 1..5 = the inventory's "Top five build order";
# None = not named in the top five.
# ----------------------------------------------------------------------------
TYPES = [
    # --- A. Anatomy ---
    ("A1", "Bone-associated sealed compartments", "P0", 1,
     "U_i = C_i^2/(2*kappa*V_0i); P_i = -dU_i/dV_i -- the existing water law derived independently per region",
     "A compartment that cannot remain sealed when its neighbor is punctured is not a compartment.",
     "Press a calf: local pressure changes; neighbors respond through actual walls. Puncture it: the torso does not automatically drain."),
    ("A2", "Load-bearing outer skin", "P0", 2,
     "U_s = int_S W_stretch dA + int_S W_bend dA; stretching stiffness ~ Et, bending ~ Et^3/[12(1-nu^2)]",
     "A skin that cannot resist stretching cannot contain pressure.",
     "Pressing, pinching, folding, and stretching produce consistent material responses."),
    ("A3", "Septa, fascia, and sliding attachment layers", "P0", 2,
     "Bonded attachments transmit traction; sliding interfaces resist interpenetration; compliant attachment U = 1/2 k ||dx||^2",
     "An attachment that cannot slip or detach cannot demonstrate attachment strength.",
     "Skin slides over a bending joint; pulling one patch loads a surrounding area."),
    ("A4", "Structural bone walls", "P1", None,
     "Reduced beam: U = 1/2 int (EA eps^2 + EI chi^2) ds; distinct from the bone-associated water region",
     "A bone that cannot bend or break cannot teach bone strength.",
     "A limb resists bending; an overloaded structural member fractures."),
    ("A5", "Joint capsules", "P0", 2,
     "Capsule enclosing the articulation, attachment rims, fluid cavity; tau = -dU_capsule/dtheta",
     "A joint whose restraints cannot fail cannot demonstrate dislocation.",
     "Bending stretches the capsule; excessive loading can destabilize the articulation."),
    ("A6", "Cartilage and lubricated bearing surfaces", "P1", None,
     "Darcy flow q = -(k_perm/mu) grad p; contact and lubrication set tangential resistance",
     "A bearing whose motion never changes with load or lubrication cannot teach lubrication.",
     "A loaded joint cushions, creeps, and moves differently when lubrication is impaired."),
    ("A7", "Active contractile tissue", "P0", 2,
     "F = a Fmax f_l(l) f_v(ldot) + F_passive; adot = (u-a)/tau_a; work from an explicit energy source",
     "A muscle that cannot stall under load cannot demonstrate contraction.",
     "An obstructed muscle develops tension; faster shortening reduces force; opposing muscles stiffen a joint."),
    ("A8", "Tendons, ligaments, and their insertions", "P0", 2,
     "F = (EA/L_0) max(0, L - L_0) -- tension-dominant with slack length",
     "A tendon that can be cut without interrupting force transmission is not a tendon.",
     "Pulling a tendon moves its attached segment; cutting it removes that particular force path."),
    ("A9", "Vessels, pump chambers, and valves", "P1", None,
     "Lumped: C_v = dV/dp; dV/dt = Q_in - Q_out; Q = dp/R; directional valves",
     "A circulation that cannot be interrupted cannot demonstrate circulation.",
     "Squeeze a vessel, obstruct flow, feel a pulse, or observe downstream supply loss."),
    ("A10", "Respiratory sacs, diaphragm, and airways", "P0", 3,
     "Gas volume obeys pV = nRT coupled to airflow resistance and an actively moved wall; water stays on its own law",
     "A breath that cannot be obstructed cannot demonstrate breathing.",
     "A torso expands; restraint reduces excursion; airway obstruction changes the cycle."),
    ("A11", "Gut, mouth, and absorptive lining", "P1", None,
     "dM_s/dt = inflow - outflow + reaction; digestion needs kinetics, absorption needs permeability",
     "A gut that produces nourishment without consuming anything cannot demonstrate digestion.",
     "Feed the creature, watch material move, connect intake to usable resources."),
    ("A12", "Filtration and excretory barriers", "P2", None,
     "Selective filters separate fluid and solutes by permeability, pressure, chemical potential",
     "A filter that cannot retain one substance while passing another cannot demonstrate filtration.",
     "Accumulated waste or salt changes function; a selective filter restores balance."),
    # --- B. Materials and membrane lifecycle ---
    ("B13", "Material-bearing surface and interior", "P0", None,
     "m = int_Omega rho dV + int_S rho_s dA; F = -dU/dq; density, elasticity, hardness, strength, toughness are different properties",
     "A material that changes weight when retessellated cannot teach mass.",
     "Equal-sized objects from different materials weigh and deform differently."),
    ("B14", "Adhesive films, welds, and cured bonds", "P0", None,
     "Interface traction t = t(delta, c); cure kinetic cdot = f(c, T, ...); separation work = area under traction-separation",
     "A glue joint that cannot fail at its interface cannot demonstrate adhesion.",
     "Glue two objects, wait, then load the joint; an uncured joint fails sooner."),
    ("B15", "Distributed tensile web and reinforcement", "P0", None,
     "Fibers share load through node force balance; failure changes the graph and loads redistribute",
     "A web that cannot redistribute load after a break cannot demonstrate a web.",
     "Pulling a net tightens several paths; one break can trigger another."),
    ("B16", "Yielding, scratches, and wear", "P0", None,
     "Fully plastic indentation: F ~ H A, A ~ 2 pi R d, so d ~ F/(2 pi R H); wear needs distance + frictional work",
     "A scratch that disappears on unloading cannot demonstrate plastic damage.",
     "A hard tool leaves a persistent groove in softer material."),
    ("B17", "Cracks, rupture, puncture, and delamination", "P0", 4,
     "Cohesive zone: G_c = int_0^deltaf t(delta) d(delta); strength initiates, fracture energy separates",
     "A rupture that leaves every physical connection intact is only a damage counter.",
     "A puncture leaks; a tear spreads; a peeled layer loses attachment."),
    ("B18", "Pores, holes, selective permeability, and leakage", "P0", 4,
     "Inertial orifice Q = C_d A_h sgn(dp) sqrt(2|dp|/rho); semipermeable J_v = L_p (dp - s dpi)",
     "A hole through which nothing can pass cannot demonstrate permeability.",
     "Hole size and pressure affect leakage; later, water passes a barrier that retains solute."),
    ("B19", "Patches, repair, scars, and regeneration", "P0", 4,
     "A patch adds material and interfaces; cure restores strength and reduces permeability",
     "A repair that cannot leak or fail under renewed load cannot demonstrate repair quality.",
     "Seal a leak and reload the repair; a weak patch can peel off."),
    ("B20", "Thermal boundaries, dissipation, and phase change", "P0", None,
     "q = -k_T grad T; energy ledger: mechanical work, stored elastic energy, heat, chemical, losses; phase change consumes latent heat",
     "An actuator that delivers unlimited work without an energy source cannot teach energy.",
     "Repeated work warms tissue; heated glue cures differently; ice melts."),
    ("B21", "Growth, fission, and actual mitosis", "P1", None,
     "Mdot = intake - loss; A_0dot = membrane production rate; division needs neck, supply, separation work",
     "A split that creates membrane and contents for free cannot demonstrate growth.",
     "Feed material to a compartment; it grows, deforms, and eventually divides."),
    ("B22", "Molecular membranes and chemical machinery", "P2", None,
     "Bending energy U = int_S [k_b/2 (2H - C_0)^2 + kbar K_G] dA; selective channels and active pumps",
     "A selective membrane with no selectivity cannot demonstrate a cell membrane.",
     "Osmotic swelling, ion gradients, selective transport, photosynthetic conversion."),
    # --- C. World ---
    ("C23", "Ground contact and supporting substrate", "P0", None,
     "Normal nonpenetration + friction ||F_t|| <= mu F_n; substrate deformation sets contact compliance",
     "A ground that cannot let a foot slip cannot teach traction.",
     "Standing, slipping, pushing off, falling, leaving an indentation."),
    ("C24", "Water surfaces and liquid bodies", "P1", None,
     "Free surface: U = gamma A, Young-Laplace dp = gamma(1/R1 + 1/R2); buoyancy F_b = rho g V_displaced",
     "A liquid surface that cannot rearrange when displaced cannot demonstrate liquid.",
     "Water spills, pools, sloshes, displaces around a limb, supports floating objects."),
    ("C25", "Soil, sand, and porous ground", "P1", None,
     "Granular yield tau = c + sigma_n tan(phi); pore fluid pressure and drainage",
     "A soil that always springs back perfectly cannot demonstrate compaction.",
     "Heavy feet sink; wet and dry ground behave differently."),
    ("C26", "Atmosphere, wind, and acoustic pressure", "P1", None,
     "Bulk gas equation of state; drag F_D = 1/2 rho C_D A v^2 within its regime; compressibility makes sound",
     "A wind that moves the creature without exchanging momentum cannot teach wind.",
     "A gust pushes the creature; a pressure wave reaches it after a delay."),
    ("C27", "Containers, cloth, ropes, tools, and constructed objects", "P1", None,
     "Instantiations of existing shell/bulk/tensile/contact/bond laws; a tool's geometry sets contact loading",
     "A container that cannot spill cannot demonstrate containment.",
     "Catch leaked water, tie a support, press with different tips, patch a wound."),
    ("C28", "Planetary and cosmic interfaces", "P2", None,
     "Crusts as elastic/plastic shells; Newtonian gravity laplacian(Phi) = 4 pi G rho; an event horizon is a causal boundary",
     "A change of scale that changes the conservation laws without disclosure cannot teach scale.",
     "Eventually connect shell mechanics to planetary structure and gravity to larger scales."),
    # --- D. Senses and response ---
    ("D29", "Local tactile receptor surfaces", "P0", 3,
     "s = (1/A) int_A t_n dA followed by specified filtering, saturation, thresholding",
     "A touch response that survives disconnecting its touch sensor cannot demonstrate sensing.",
     "The creature answers a calf press differently from a torso press or a broad squeeze."),
    ("D30", "Proprioception, load sensing, and balance sensing", "P0", 3,
     "Sensors measure joint configuration, tissue extension, tendon force, angular motion, specific force -- separate observables",
     "A balance controller that knows an unmeasured state perfectly cannot demonstrate embodied feedback.",
     "A loaded limb braces, an unsupported foot searches, a leaning body attempts recovery."),
    ("D31", "Axonal membranes and propagation", "P0", 3,
     "Cable model C_j Vdot_j = sum_k (V_k - V_j)/R_jk - I_ion + I_input; cheap abstraction: event travel time L/v + refractory state",
     "A nerve that transmits across a cut cannot demonstrate a nerve.",
     "A distal stimulus produces a delayed response; interrupting the path removes it."),
    ("D32", "Synapses, reflex integration, and adaptation", "P0", 3,
     "tau sdot = -s + sum w_i input_i -- chosen reduced circuit dynamics with threshold, decay, adaptation",
     "A reflex whose response is unchanged by severing its sensory path cannot demonstrate a reflex.",
     "A rapid tap startles, sustained load braces, repeated harmless taps habituate."),
    ("D33", "Eyes: optical boundary, sensor, eyelid, and gaze actuator", "P0", 3,
     "Aperture + photosensitive surface; honest minimum: eye-local visibility sensor with FOV, occlusion, delay, bounded gaze",
     "An eye that acquires new information through an opaque cover cannot demonstrate sight.",
     "The creature notices the in-world hand, looks toward it, loses new evidence when hidden."),
    ("D34", "Eardrums and vibration sensors", "P1", None,
     "m_e xddot + c_e xdot + k_e x = A_e dp -- force balance",
     "An ear that hears equally well when acoustically isolated cannot demonstrate hearing.",
     "A sound or ground vibration causes a response with direction- and distance-dependent timing."),
    ("D35", "Chemical and thermal receptor interfaces", "P2", None,
     "Binding kinetics bdot = k_on c (1-b) - k_off b; thermal sensing follows heat exchange, not instant access",
     "A receptor that responds without its stimulus reaching it cannot demonstrate reception.",
     "The creature detects a nearby chemical source or reacts after touching something warm."),
    # --- E. Product interfaces (architectural invariants, not physical membranes) ---
    ("E36", "Player-to-world mechanical interface", "P0", None,
     "Finite force over finite footprint; F = k_h(x_t - x) + c_h(v_t - v) with declared caps; W = int F.dx",
     "A press that deforms geometry without applying the corresponding load cannot teach force.",
     "Press, hold, release, pull, and compare tools."),
    ("E37", "Simulation-to-browser state boundary", "P0", None,
     "Displayed deformation/pressure/response refer to consistent authoritative states; timestamps + topology versions; interpolation invents nothing",
     "A displayed response that precedes its authoritative cause cannot teach causality.",
     "The dimple, pressure rise, and flinch visibly agree."),
    ("E38", "Measurement and explanation interface", "P0", None,
     "Every shown quantity has units, provenance, model assumptions, appropriate precision; damping/aliasing disclosed",
     "A measurement that cannot be checked against an independent calculation cannot teach measurement.",
     "Open a cross-section, select one compartment, explain why its pressure changed."),
    ("E39", "Import, sealing, and resolution boundary", "P0", None,
     "Imported geometry acquires valid regions, materials, attachments, sensor locations; refinement preserves mass",
     "An importer that passes only before the first joint bends has not imported a physical creature.",
     "A new creature works for understandable geometric reasons."),
    ("E40", "Persistence, replay, and topology history", "P0", None,
     "Saving preserves fluid inventories, rest geometry, wounds, cure, activation, delayed signals, stable region identities",
     "A wound that disappears on reload is not persistent damage.",
     "Return to the same wounded creature and continue the experiment."),
    ("E41", "Lesson and counterfactual boundary", "P0", None,
     "Success depends on the taught mechanism; ablations and transfer tests; confounders controlled",
     "A lesson passed equally well after disabling its claimed law does not teach that law.",
     "Predict which chamber leaks, which tendon moves the limb, whether a patch holds."),
    ("E42", "Creature-care loop and value gate", "P0", None,
     "Discovery, consequence, recovery, renewed interaction; understandable without the engineering HUD",
     "A creature whose \"aliveness\" survives replacing feedback with disconnected replay has not yet proved responsive aliveness.",
     "Notice, press, receive an answer, investigate, change something, see a lasting consequence."),
]


def make_types():
    out = []
    for anchor, name, pri, rank, law, falsifier, moment in TYPES:
        out.append({
            "id": f"type.{anchor}",
            "kind": "type",
            "name": name,
            "classification": None,
            "status": "specified",       # a TYPE is a definition; instances carry build state
            "priority": pri,
            "build_rank": rank,
            "inventory_anchor": anchor,
            "spatial": None,
            "geometry": None,
            "physical": {"law": law, "player_moment": moment},
            "attachments": [],
            "dependencies": [],
            "evidence": [],
            "falsifier": {"statement": falsifier, "acceptance_test": None,
                          "status": "untested"},
            "unknowns": [],
            "notes": "membrane TYPE from docs/THE_MEMBRANE_INVENTORY.md item "
                     f"{anchor} (Astra, 2026-09-15); reusable concept, not a creature part",
            "provenance": {"source": "docs/THE_MEMBRANE_INVENTORY.md",
                           "credited_to": "Astra", "date": "2026-09-15"},
        })
    return out


# ----------------------------------------------------------------------------
# INSTANCES -- the creature's current state. All engine coordinates are
# REFERENCE-POSE/REST values read from the live engine's tick_state and the
# body atlas; live simulation state is NEVER stored here (the engine owns it).
# ----------------------------------------------------------------------------
def make_instances():
    objs = []

    # -- named regions -------------------------------------------------------
    objs.append({
        "id": "region.environment", "kind": "region", "name": "The environment",
        "classification": None, "status": "specified", "priority": "P0",
        "build_rank": None, "inventory_anchor": None, "spatial": None,
        "geometry": None, "physical": None, "attachments": [], "dependencies": [],
        "evidence": [], "falsifier": {}, "unknowns": [],
        "notes": "everything outside the body interior; may be one side of any membrane",
        "provenance": {"source": "brief 2026-09-15: the environment can be one side"},
    })
    objs.append({
        "id": "region.body_interior", "kind": "region", "name": "Body interior",
        "classification": None, "status": "geometry_built", "priority": "P0",
        "build_rank": None, "inventory_anchor": "B13",
        "spatial": {"note": "interior of the sealed skin; no own coordinates "
                            "(union of compartment regions)"},
        "geometry": {"shape": "union-of-compartments", "is_placeholder": False,
                     "known_dimensions": "from the sealed 4-cell partition"},
        "physical": None, "attachments": [], "dependencies": [], "evidence": [],
        "falsifier": {}, "unknowns": ["full per-bone subdivision pending"],
        "notes": "material mass lives here; nested regions (fluid inside structural) "
                 "must never double-count mass",
        "provenance": {"source": "brief 2026-09-15 (material occupying nested regions)"},
    })
    for band, lo, hi, v0 in [
            ("feet", -0.019507, 0.338, 0.287914),
            ("shins", 0.338, 1.903, 0.334578),
            ("thighs", 1.903, 3.415, 0.693006),
            ("torso", 3.415, 9.97118, 12.5091)]:
        objs.append({
            "id": f"region.band.{band}", "kind": "region", "name": f"{band} band region",
            "classification": None, "status": "geometry_built", "priority": "P0",
            "build_rank": None, "inventory_anchor": None,
            "spatial": {"band_y": [lo, hi], "frame": "engine world frame, y-up",
                        "note": "height-band cut planes at MEASURED joint heights "
                                "(0.338 ankle, 1.903 knee, 3.415 hip)"},
            "geometry": {"shape": "slab of the sealed body between y-planes",
                         "is_placeholder": False},
            "physical": None, "attachments": [], "dependencies": [], "evidence": [],
            "falsifier": {}, "unknowns": [],
            "notes": "the 4-band partition is the MINIMUM seal proof, not the product "
                     "(THE ANATOMICAL COMPARTMENT LAW)",
            "provenance": dict(LIVE_PROV, **SHIP_GOAL_PROV),
        })
    objs.append({
        "id": "region.leg_l", "kind": "region", "name": "Left leg (selected limb)",
        "classification": None, "status": "specified", "priority": "P0",
        "build_rank": 1, "inventory_anchor": "A1",
        "spatial": {"anchored_to": "chain frame.hip_l -> frame.knee_l -> frame.ankle_l",
                    "frame": "engine world frame, y-up",
                    "note": "the limb is DEFINED by skeleton connectivity in the "
                            "reference configuration, not by a horizontal band"},
        "geometry": {"shape": "limb volume (unpartitioned)", "is_placeholder": True},
        "physical": None, "attachments": [], "dependencies": [], "evidence": [],
        "falsifier": {},
        "unknowns": ["volumetric extent pending the labeled-volume partition"],
        "notes": "THE SELECTED LIMB for the one-honest-limb demonstration; "
                 "connected bone path hip_L->knee_L->ankle_L->terminal foot",
        "provenance": dict(BODY_ATLAS_PROV, **SHIP_GOAL_PROV),
    })

    # -- measured joint frames (selected limb) --------------------------------
    for pin, aim, note in [
            ("hip_l", [0.1689, 3.44397, 0.12355], "co-located with spine_lower pin"),
            ("knee_l", [0.4745, 1.8988, -0.0057], "the demo joint"),
            ("ankle_l", [0.4562, 0.3313, 0.0711], "")]:
        objs.append({
            "id": f"frame.{pin}", "kind": "frame", "name": f"measured pin {pin.upper()}",
            "classification": None, "status": "geometry_built", "priority": "P0",
            "build_rank": None, "inventory_anchor": None,
            "spatial": {"origin": aim, "frame": "engine world frame, y-up",
                        "axis_convention": "engine convention (y = height); "
                                           "handedness recorded in the engine docs",
                        "length_units": "m"},
            "geometry": {"shape": "point (measured joint anchor)",
                         "is_placeholder": False},
            "physical": None, "attachments": [], "dependencies": [], "evidence": [],
            "falsifier": {}, "unknowns": [],
            "notes": note or "measured joint pin from the body atlas (28 pins total; "
                             "28 pins != 28 bones -- segments derive from connectivity)",
            "provenance": dict(BODY_ATLAS_PROV),
        })

    # -- bone segments (connected bone paths in the reference configuration) ---
    segs = [
        ("seg.thigh_l", "Left thigh segment (femur-analogue)", "frame.hip_l", "frame.knee_l",
         "proximal end co-located with spine_lower/hip_L"),
        ("seg.shin_l", "Left shin segment (tibia-fibula analogue)", "frame.knee_l", "frame.ankle_l",
         "the sculpt carries one shin pin; fibula not separately pinned -- UNKNOWN"),
        ("seg.foot_l", "Left foot segment (terminal)", "frame.ankle_l",
         [0.93209, 0.15954, 0.71522],
         "terminal segment, EXPLICITLY DEFINED (A1 note): distal endpoint is the "
         "measured feet-cell left center, provisional until a toe pin is measured"),
    ]
    for sid, name, a, b, note in segs:
        objs.append({
            "id": sid, "kind": "curve", "name": name,
            "classification": "creature.bone_segment", "status": "geometry_built",
            "priority": "P0", "build_rank": 1, "inventory_anchor": "A1",
            "spatial": {"endpoints": [a, b], "frame": "engine world frame, y-up",
                        "length_units": "m"},
            "geometry": {"shape": "bone centerline (placement authority: the "
                                   "MEASURED skeleton)",
                         "is_placeholder": False},
            "physical": None, "attachments": [], "dependencies": [], "evidence": [],
            "falsifier": {}, "unknowns": ["cross-section dimensions UNKNOWN"],
            "notes": note + ". Segment ownership derives from skeleton CONNECTIVITY, "
                            "not from horizontal bands or nearest-pin labels alone.",
            "provenance": dict(BODY_ATLAS_PROV, **SHIP_GOAL_PROV),
        })

    # -- membranes: skin + the three shared band septa ------------------------
    objs.append({
        "id": "memb.skin", "kind": "surface", "name": "Load-bearing outer skin (whole body)",
        "classification": "type.A2", "status": "geometry_built", "priority": "P0",
        "build_rank": 2, "inventory_anchor": "A2",
        "spatial": {"anchored_to": "the creature surface mesh (rest configuration)",
                    "frame": "engine world frame", "length_units": "m"},
        "geometry": {"shape": "closed triangle surface (the seal's exterior)",
                     "is_placeholder": False,
                     "known_dimensions": "skin area 64.69 m^2 (measured, C1r derivation)"},
        "physical": {"law": "existing: pressure coupling + press approximation "
                            "delta = F/(4 pi sigma), sigma = 4000 N/m (QUALIFIED "
                            "REDUCED model; assumed geometry undocumented)",
                     "carries": ["tension", "pressure"],
                     "region_a": "region.body_interior",
                     "region_b": "region.environment"},
        "attachments": [], "dependencies": [], "evidence": ["ev.band_seal_conservation"],
        "falsifier": {"statement": "A skin that cannot resist stretching cannot contain pressure.",
                      "acceptance_test": None, "status": "untested"},
        "unknowns": ["shell constitutive model (stretch/bend) not yet explicit",
                     "fold artifacts in the 3-nearest-pin IDW skinning",
                     "weight-based skinning does not prove physical attachment"],
        "notes": "the seal's exterior wall; one physical surface, no double wall",
        "provenance": dict(BRIEF_PROV),
    })
    for sept_id, ra, rb, lo_hi, note in [
            ("memb.septum.feet_shins", "region.band.feet", "region.band.shins",
             [0.338, 0.338], "cut plane at the measured ankle height"),
            ("memb.septum.shins_thighs", "region.band.shins", "region.band.thighs",
             [1.903, 1.903], "cut plane at the measured knee height"),
            ("memb.septum.thighs_torso", "region.band.thighs", "region.band.torso",
             [3.415, 3.415], "cut plane at the measured hip height")]:
        objs.append({
            "id": sept_id, "kind": "surface",
            "name": f"Shared septum {ra.split('.')[-1]} | {rb.split('.')[-1]}",
            "classification": "type.A3", "status": "geometry_built", "priority": "P0",
            "build_rank": None, "inventory_anchor": "A3",
            "spatial": {"band_y": lo_hi, "frame": "engine world frame, y-up",
                        "note": "ONE physical wall shared by both region owners "
                                "(opposite orientation in each region's volume calc; "
                                "no double stiffness, no double mass, no gap)"},
            "geometry": {"shape": "sealed cut interface (welded cap pair)",
                         "is_placeholder": False},
            "physical": {"law": "shared sealed interface; transmits mechanical "
                                "coupling (neighbor pressure may change through it)",
                         "carries": ["pressure", "traction"],
                         "region_a": ra, "region_b": rb},
            "attachments": [], "dependencies": [], "evidence": ["ev.band_seal_conservation"],
            "falsifier": {"statement": "A compartment that cannot remain sealed when its neighbor is punctured is not a compartment.",
                          "acceptance_test": "puncture one band; the OTHER band's "
                                             "inventory must not drain (acceptance 3)",
                          "status": "untested"},
            "unknowns": ["permeability/failure not implemented: an opening "
                         "surface does not yet exist (type.B17/B18 gap)"],
            "notes": note + ". A geometric closing face IS the load-bearing wall "
                            "here because both sides seal against the same welded "
                            "cut; this must be RE-PROVEN for per-bone oblique septa.",
            "provenance": dict(LIVE_PROV, **SHIP_GOAL_PROV),
        })

    # -- the four VERIFIED band compartments ----------------------------------
    for band, v0, region in [
            ("feet", 0.287914, "region.band.feet"),
            ("shins", 0.334578, "region.band.shins"),
            ("thighs", 0.693006, "region.band.thighs"),
            ("torso", 12.5091, "region.band.torso")]:
        objs.append({
            "id": f"inst.band.{band}", "kind": "volume",
            "name": f"{band.capitalize()} compartment (verified band instance)",
            "classification": "type.A1", "status": "verified", "priority": "P0",
            "build_rank": 1, "inventory_anchor": "A1",
            "spatial": {"band_y": {"feet": [-0.019507, 0.338],
                                   "shins": [0.338, 1.903],
                                   "thighs": [1.903, 3.415],
                                   "torso": [3.415, 9.97118]}[band],
                        "frame": "engine world frame, y-up", "length_units": "m",
                        "v0_m3": v0},
            "geometry": {"shape": "sealed hydraulic cell (cut-and-weld partition)",
                         "is_placeholder": False,
                         "known_dimensions": "v0 from the live engine's per-cell state"},
            "physical": {"law": WATER_LAW, "carries": ["pressure"],
                         "region_a": region, "region_b": None,
                         "state_note": "live pressure/volume live in the ENGINE; "
                                       "this object carries rest (V0) values only"},
            "attachments": [], "dependencies": [],
            "evidence": ["ev.band_seal_conservation"],
            "falsifier": {"statement": "A compartment that cannot remain sealed when its neighbor is punctured is not a compartment.",
                          "acceptance_test": "puncture a neighbor band; this cell "
                                             "keeps its inventory (acceptance 3)",
                          "status": "untested"},
            "unknowns": [],
            "notes": "VERIFIED instance of type.A1 at the 4-band granularity. NOT "
                     "the product: the ANATOMICAL COMPARTMENT LAW requires one "
                     "sealed compartment per intended bone segment.",
            "provenance": dict(LIVE_PROV, **SHIP_GOAL_PROV),
        })

    # -- PER-BONE compartments: SPECIFIED placeholders (the ANATOMICAL --------
    #    COMPARTMENT LAW), linked to the parallel physics lane (AN2) by ID ----
    for comp, seg, region_a, note in [
            ("inst.comp.thigh_l", "seg.thigh_l", "region.seg.thigh_l",
             "femur-analogue compartment"),
            ("inst.comp.shin_l", "seg.shin_l", "region.seg.shin_l",
             "tibia-fibula-analogue compartment"),
            ("inst.comp.foot_l", "seg.foot_l", "region.seg.foot_l",
             "terminal foot compartment")]:
        objs.append({
            "id": comp, "kind": "volume",
            "name": f"{comp.split('.')[-1]} compartment (specified placeholder)",
            "classification": "type.A1", "status": "specified", "priority": "P0",
            "build_rank": 1, "inventory_anchor": "A1",
            "spatial": {"anchored_to": seg,
                        "frame": "engine world frame, y-up",
                        "note": "provisional placement along the measured bone "
                                "segment; NOT known geometry"},
            "geometry": {"shape": "volumetric region around the bone segment "
                                  "(labeled-volume partition, pending)",
                         "is_placeholder": True},
            "physical": {"law": WATER_LAW + " (per-region form; V0i UNKNOWN until "
                                            "the partition exists)",
                         "carries": ["pressure"],
                         "region_a": region_a, "region_b": None},
            "attachments": [], "dependencies": ["work.partition_leg_l", "work.septa_leg_l"],
            "evidence": [],
            "falsifier": {"statement": "A compartment that cannot remain sealed when its neighbor is punctured is not a compartment.",
                          "acceptance_test": "THE ANATOMICAL COMPARTMENT LAW "
                                             "verification: compartment count == bone "
                                             "count, every cell conserves, a press on "
                                             "the bone answers in THAT bone's cell",
                          "status": "untested"},
            "unknowns": ["V0i unknown until partition",
                         "boundary geometry unknown (oblique planes/branch junctions)",
                         "mass share of the 13,824.5 kg inventory unknown"],
            "notes": note + ". SPECIFIED placeholder per docs/THE_SHIP_GOAL.md "
                            "ANATOMICAL COMPARTMENT LAW (2026-09-13). Parallel "
                            "physics lane AN2 ('one honest limb') owns the "
                            "volumetric partition implementation; watch git log for "
                            "'(Agent: AN2-one-honest-limb)' -- linked by stable IDs "
                            "(this object id), not by name.",
            "provenance": dict(SHIP_GOAL_PROV),
        })
    # the per-bone regions the volumes name
    for rid, seg in [("region.seg.thigh_l", "seg.thigh_l"),
                     ("region.seg.shin_l", "seg.shin_l"),
                     ("region.seg.foot_l", "seg.foot_l")]:
        objs.append({
            "id": rid, "kind": "region", "name": f"{rid.split('.')[-1]} region",
            "classification": None, "status": "specified", "priority": "P0",
            "build_rank": 1, "inventory_anchor": "A1",
            "spatial": {"anchored_to": seg,
                        "note": "provisional placement; no owned coordinates yet"},
            "geometry": {"shape": "pending labeled-volume region",
                         "is_placeholder": True},
            "physical": None, "attachments": [], "dependencies": [], "evidence": [],
            "falsifier": {}, "unknowns": ["extent, volume, mass share"],
            "notes": "named region for the per-bone compartment; created so the "
                     "septa can name both sides before the partition exists",
            "provenance": dict(SHIP_GOAL_PROV),
        })
    # per-bone septa as SPECIFIED placeholder walls (one wall, two owners)
    for sept_id, ra, rb in [
            ("memb.septum.thigh_l_shin_l", "region.seg.thigh_l", "region.seg.shin_l"),
            ("memb.septum.shin_l_foot_l", "region.seg.shin_l", "region.seg.foot_l")]:
        objs.append({
            "id": sept_id, "kind": "surface",
            "name": f"Septum {ra.split('.')[-1]} | {rb.split('.')[-1]} (specified)",
            "classification": "type.A3", "status": "specified", "priority": "P0",
            "build_rank": 1, "inventory_anchor": "A3",
            "spatial": {"anchored_to": "joint plane between the two segments "
                                       "(oblique plane, normal UNKNOWN)",
                        "frame": "engine world frame, y-up"},
            "geometry": {"shape": "conforming internal interface (pending)",
                         "is_placeholder": True},
            "physical": {"law": "shared sealed interface (planned); a visual cap "
                                "alone CANNOT establish independent compartments",
                         "carries": ["pressure", "traction"],
                         "region_a": ra, "region_b": rb},
            "attachments": [],
            "dependencies": ["work.septa_leg_l"],
            "evidence": [],
            "falsifier": {"statement": "A compartment that cannot remain sealed when its neighbor is punctured is not a compartment.",
                          "acceptance_test": "puncture thigh_l; shin_l keeps its "
                                             "inventory; total mass conserved",
                          "status": "untested"},
            "unknowns": ["orientation/normal", "area", "conforming geometry at "
                                                        "the branch junction"],
            "notes": "DISTINGUISH: geometric closing face vs implemented "
                     "load-bearing septum -- this object is SPECIFIED, i.e. "
                     "neither yet.",
            "provenance": dict(SHIP_GOAL_PROV),
        })
    return objs


# ----------------------------------------------------------------------------
# MECHANISMS: actuators, sensors, pathways, materials, models, parameters,
# and the validation evidence (implementation state and validation state are
# INDEPENDENT -- a failing current test stays visible).
# ----------------------------------------------------------------------------
def make_mechanisms():
    objs = []
    # -- materials ------------------------------------------------------------
    objs.append({
        "id": "material.water", "kind": "material", "name": "Sealed water (creature fluid)",
        "classification": None, "status": "geometry_built", "priority": "P0",
        "build_rank": None, "inventory_anchor": "B13", "spatial": None,
        "geometry": None,
        "physical": {"law": WATER_LAW, "carries": ["pressure", "mass"]},
        "attachments": [], "dependencies": [], "evidence": ["ev.band_seal_conservation"],
        "falsifier": {}, "unknowns": ["temperature/viscosity conditions unspecified"],
        "notes": "V_whole = 13.8246 m^3 live => 13,824.6 kg at 1000 kg/m^3, matching "
                 "the reported 13,824.5 kg material inventory (preserved on repartition)",
        "provenance": dict(BRIEF_PROV, **LIVE_PROV),
    })
    objs.append({
        "id": "material.skin_membrane", "kind": "material", "name": "Skin membrane material",
        "classification": None, "status": "geometry_built", "priority": "P0",
        "build_rank": 2, "inventory_anchor": "A2", "spatial": None, "geometry": None,
        "physical": {"law": "qualified reduced: tension sigma = 4000 N/m; "
                            "NOT a universal indentation law",
                     "carries": ["tension"]},
        "attachments": [], "dependencies": [], "evidence": [],
        "falsifier": {}, "unknowns": ["E, thickness, nu UNKNOWN (no shell model yet)"],
        "notes": "the 4000 N/m tension is NOT water's surface tension (C24 warning)",
        "provenance": dict(BRIEF_PROV),
    })
    objs.append({
        "id": "material.glue", "kind": "material", "name": "Glue (third material)",
        "classification": None, "status": "specified", "priority": "P0",
        "build_rank": None, "inventory_anchor": "B14", "spatial": None, "geometry": None,
        "physical": {"law": "cure strength + traction-separation (approved model, "
                            "scratch prototype exists)"},
        "attachments": [], "dependencies": [], "evidence": [],
        "falsifier": {}, "unknowns": ["cure kinetics parameters", "separation work"],
        "notes": "approved third-material glue model; cure strength recorded as work-in-progress",
        "provenance": dict(BRIEF_PROV),
    })

    # -- models (constitutive/physical models actually in use) ----------------
    models = [
        ("model.water_compressibility", "Water compressibility law", "geometry_built",
         WATER_LAW,
         "couples volume constraint C = V - V0 with alpha = kappa*V0 into the XPBD stack",
         ["ev.band_seal_conservation"],
         []),
        ("model.xpbd_coupled", "Coupled XPBD stack (volume+joint+servo+contact)",
         "geometry_built",
         "outer tick 300 Hz, 2 Gauss-Seidel iterations per substep, n=4 substeps for cost; "
         "reportedly bounded across tested substep counts",
         "the verified current solver is the BASELINE; integrator replacement is a separate experiment",
         ["ev.xpbd_fidelity_gap"],
         ["frequency, amplitude, damping, and output sampling need separate evidence"]),
        ("model.press_indentation", "Press indentation (qualified reduced)", "geometry_built",
         "delta = F/(4 pi sigma), sigma = 4000 N/m",
         "existing press approximation; the coefficient DEPENDS ON ASSUMPTIONS that "
         "are undocumented (e.g. annular membrane gives delta = F ln(R/a)/(2 pi T))",
         [], ["assumed support/contact geometry UNKNOWN"]),
        ("model.exponential_recovery", "Exponential recovery (NOT healing)", "geometry_built",
         "shape recovery exp decay, tau = 0.5 s",
         "recovery is viscoelastic relaxation; it is NOT material healing -- returning "
         "shape does not restore broken material, lost water, or consumed energy",
         [], []),
        ("model.contact_spring", "Ground contact spring", "geometry_built",
         "contact spring k = 1.3562e7 N/m",
         "stated contact spring; material/geometry interpretation needs qualification "
         "(matching mg at equilibrium does not validate transient contact behavior)",
         [], ["transient contact behavior unvalidated"]),
        ("model.breath_allometry", "Autonomic breath (volume-target oscillation)",
         "geometry_built",
         "torso cell volume TARGET oscillates: rate from Stahl respiratory allometry "
         "f = 53.5 * M^-0.26 => 4.485/min (period 13.38 s); tidal volume 6.2 mL/kg * "
         "M^1.01 => 0.0940 m^3 => 1.45 mm mean swell",
         "applied as the LAST surface pass; the pressure law/conservation/gait "
         "measurements are structurally blind to it (the honest derivation shows a "
         "water-stiff sealed cell CANNOT breathe: the tidal swell, if the kappa law "
         "saw it, answers 14.9 MPa = 99% of skin yield)",
         [],
         ["a model choice requiring a biological reference; does NOT validate a "
          "water-volume oscillator; a real gas compartment remains an explicit "
          "future requirement (type.A10)"]),
    ]
    for mid, name, status, law, note, evid, unknowns in models:
        objs.append({
            "id": mid, "kind": "model", "name": name,
            "classification": None, "status": status, "priority": "P0",
            "build_rank": None, "inventory_anchor": None, "spatial": None,
            "geometry": None,
            "physical": {"law": law}, "attachments": [], "dependencies": [],
            "evidence": list(evid),
            "falsifier": {},
            "unknowns": list(unknowns),
            "notes": note,
            "provenance": dict(BRIEF_PROV),
        })

    # -- SELECTED parameters (selection is an explicit adaptation decision) ----
    params = [
        ("param.kappa", "kappa (water compressibility)", 4.6e-10, "Pa^-1",
         "sealed liquid water cells of this creature", "in_use",
         "operator brief 2026-09-15 / engine water law; specimen: the creature's "
         "water inventory; temperature/strain-rate conditions UNKNOWN"),
        ("param.sigma_skin", "sigma (skin tension coefficient)", 4000.0, "N/m",
         "the press approximation delta = F/(4 pi sigma) on this creature's skin",
         "in_use", "engine constant (brief 2026-09-15); assumed contact/support "
                   "geometry UNKNOWN -- qualified reduced model"),
        ("param.tau_recovery", "tau (skin recovery)", 0.5, "s",
         "exponential shape recovery after unload", "in_use",
         "engine constant; NOT a healing timescale"),
        ("param.contact_spring_k", "ground contact spring", 1.3562e7, "N/m",
         "ground contact under the creature's feet", "in_use",
         "engine constant; interpretation of material/geometry needs qualification"),
        ("param.mass_inventory", "creature mass from material inventory", 13824.5, "kg",
         "whole creature; MUST be preserved when repartitioning", "in_use",
         "derived from the material inventory (brief); live V_whole 13.8246 m^3 "
         "x 1000 kg/m^3 agrees to 13,824.6 kg"),
        ("param.breath_period", "autonomic breath period", 13.38, "s",
         "torso volume-target oscillation (reflex breathing)", "in_use",
         "Stahl respiratory allometry at the engine's own mass (C1r derivation); "
         "MODEL CHOICE requiring a biological reference -- it does NOT validate a "
         "water-volume oscillator (the 1% volume strain at kappa implies ~21.7 MPa)"),
    ]
    for pid, name, value, units, applicability, sel_status, source in params:
        objs.append({
            "id": pid, "kind": "parameter", "name": name,
            "classification": None, "status": "geometry_built", "priority": "P0",
            "build_rank": None, "inventory_anchor": None, "spatial": None,
            "geometry": None,
            "physical": {"value": value, "selection_status": sel_status},
            "attachments": [], "dependencies": [], "evidence": [],
            "falsifier": {},
            "units": units,
            "value": value,
            "source": source,
            "applicability": applicability,
            "validation": "unchecked against independent reference" if sel_status == "in_use" else "n/a",
            "unknowns": [],
            "notes": "SELECTED parameter (not a reference assertion): selecting it "
                     "for the creature was an explicit adaptation decision; the "
                     "reference side (Uberon/RO/QUDT/OpenSim) never auto-becomes "
                     "a creature parameter",
            "provenance": {"source": source},
        })

    # -- actuators / sensors / pathways (honestly labeled) ---------------------
    objs.append({
        "id": "actuator.joint_servos", "kind": "actuator",
        "name": "Joint actuators (force/torque-limited servos)",
        "classification": None, "status": "geometry_built", "priority": "P0",
        "build_rank": 2, "inventory_anchor": "A7",
        "spatial": {"anchored_to": "the 28 measured joint pins",
                    "frame": "engine world frame"},
        "geometry": {"shape": "servo constraints at pins", "is_placeholder": False},
        "physical": {"law": "force/torque-limited servo intents through /tick_pose; "
                            "NOT implemented contractile tissue (labeled accurately "
                            "per the brief)"},
        "attachments": [], "dependencies": [], "evidence": [],
        "falsifier": {"statement": "A muscle that cannot stall under load cannot demonstrate contraction.",
                      "acceptance_test": "obstruct motion; respect the force/torque "
                                         "cap; measure the reaction load (acceptance 5)",
                      "status": "untested"},
        "unknowns": ["no activation/contractile state", "no explicit energy reservoir yet"],
        "notes": "REUSE for the first causal demonstration (brief: reuse them for "
                 "the first causal demonstration).",
        "provenance": dict(BRIEF_PROV),
    })
    objs.append({
        "id": "sensor.scalar_cell_pressure", "kind": "sensor",
        "name": "Per-cell scalar pressure telemetry",
        "classification": None, "status": "geometry_built", "priority": "P0",
        "build_rank": None, "inventory_anchor": "D29",
        "spatial": {"anchored_to": "one sensor per sealed cell (no sub-cell location)",
                    "frame": "engine world frame"},
        "geometry": {"shape": "scalar per cell", "is_placeholder": False},
        "physical": {"law": "reports cell pressure P each tick (300 Hz outer tick; "
                            "tick period 3.33 ms); /tick_state exposes it"},
        "attachments": [], "dependencies": [], "evidence": [],
        "falsifier": {"statement": "A touch response that survives disconnecting its touch sensor cannot demonstrate sensing.",
                      "acceptance_test": "disconnect pathway.pressure_to_intent; the "
                                         "active response must vanish while passive "
                                         "mechanical response remains (acceptance 4)",
                      "status": "untested"},
        "unknowns": [],
        "notes": "LIMITATION: one uniform cell pressure cannot identify WHERE on "
                 "the cell the touch occurred (brief). Local receptor patches are "
                 "the type.D29 fix and remain SPECIFIED.",
        "provenance": dict(BRIEF_PROV),
    })
    objs.append({
        "id": "pathway.pressure_to_intent", "kind": "pathway",
        "name": "Pressure-to-intent pathway (the reflex 'nerve')",
        "classification": None, "status": "geometry_built", "priority": "P0",
        "build_rank": 3, "inventory_anchor": "D31",
        "spatial": {"anchored_to": "cell -> controller -> same-limb drive pins",
                    "frame": "engine world frame"},
        "geometry": {"shape": "disconnectable connection", "is_placeholder": False},
        "physical": {"law": "per-cell pressure crossing -> binding-derived strut "
                            "pin intent; FINITE delay: one outer tick (3.33 ms); "
                            "DISCONNECTABLE via the pressure_coupling route flag "
                            "(the battery's built-in negative control)"},
        "attachments": [], "dependencies": [], "evidence": ["ev.reflex_controls_fail"],
        "falsifier": {"statement": "A nerve that transmits across a cut cannot demonstrate a nerve.",
                      "acceptance_test": "cut the pathway; signal contribution gone, "
                                         "passive mechanics remain (C1r: prev_p tracks "
                                         "truth through a cut so reconnect never "
                                         "synthesizes a spike)",
                      "status": "untested"},
        "unknowns": [],
        "notes": "exists (C1r plumbing) but the REFLEX CONTROLS fail (see "
                 "ev.reflex_controls_fail): their existence is not verification.",
        "provenance": dict(BRIEF_PROV),
    })

    # -- validation evidence (independent of implementation state) -------------
    objs.append({
        "id": "ev.band_seal_conservation", "kind": "evidence",
        "name": "4-band seal conservation (live session)",
        "classification": None, "status": "geometry_built", "priority": None,
        "build_rank": None, "inventory_anchor": None, "spatial": None,
        "geometry": None,
        "physical": None, "attachments": [], "dependencies": [], "evidence": [],
        "falsifier": {},
        "validation": "passing",
        "last_result": None,
        "deps": ["inst.band.feet", "inst.band.shins", "inst.band.thighs",
                 "inst.band.torso", "memb.skin", "memb.septum.feet_shins",
                 "memb.septum.shins_thighs", "memb.septum.thighs_torso",
                 "material.water"],
        "captured": {},   # filled at build time from content_version()
        "captured_utc": "2026-09-15T13:47:00Z",
        "engine": {"ticks": 731615, "sealed": True, "n_cells": 4,
                   "conserve_pct": -0.000117273, "V_whole_m3": 13.8246,
                   "url": "GET 127.0.0.1:8107/tick_state"},
        "acceptance": "sealed=true, no seal refusal, |conserve_pct| < 0.01, "
                      "sum of per-cell v0 == V_whole, all cells non-degenerate",
        "unknowns": [],
        "notes": "VALIDATION state (passing) is independent of implementation "
                 "state; a physics-relevant change to any dep stales this "
                 "conservatively (the result stays visible in last_result).",
        "provenance": dict(LIVE_PROV),
    })
    objs.append({
        "id": "ev.reflex_controls_fail", "kind": "evidence",
        "name": "Reflex plumbing fails its controls (current)",
        "classification": None, "status": "geometry_built", "priority": None,
        "build_rank": None, "inventory_anchor": None, "spatial": None,
        "geometry": None,
        "physical": None, "attachments": [], "dependencies": [], "evidence": [],
        "falsifier": {},
        "validation": "failing",
        "last_result": None,
        "deps": ["pathway.pressure_to_intent", "sensor.scalar_cell_pressure",
                 "actuator.joint_servos"],
        "captured": {},
        "captured_utc": "2026-09-15T13:47:00Z",
        "engine": {"note": "brief: 'Reflex plumbing exists but fails its controls: "
                           "volume-target breathing, pressure-triggered flinch, and "
                           "pressure-rate startle. Their existence is not "
                           "verification.'"},
        "acceptance": "each reflex must pass its own negative control (severed "
                      "path => no active response, passive mechanics remain)",
        "unknowns": [],
        "notes": "A FAILED CURRENT TEST STAYS VISIBLE. This is exactly the record "
                 "that must not silently vanish when the pathway is edited.",
        "provenance": dict(BRIEF_PROV),
    })
    objs.append({
        "id": "ev.xpbd_fidelity_gap", "kind": "evidence",
        "name": "XPBD convergence does not establish modal fidelity",
        "classification": None, "status": "geometry_built", "priority": None,
        "build_rank": None, "inventory_anchor": None, "spatial": None,
        "geometry": None,
        "physical": None, "attachments": [], "dependencies": [], "evidence": [],
        "falsifier": {},
        "validation": "failing",
        "last_result": None,
        "deps": ["model.xpbd_coupled"],
        "captured": {},
        "captured_utc": "2026-09-15T13:47:00Z",
        "engine": {"measured": "converged n=4 XPBD: 1222.7 rad/s; true ring mode: "
                               "1949 rad/s (synthetic prototype, not the creature's "
                               "identified model)"},
        "acceptance": "frequency, amplitude, damping, and output sampling each "
                      "carry separate evidence",
        "unknowns": [],
        "notes": "Reported context from the brief; a synthetic comparison lives at "
                 "Tools/modal_fidelity_ring.py when present. Failing stays visible.",
        "provenance": dict(BRIEF_PROV),
    })
    return objs


# ----------------------------------------------------------------------------
# REQUIREMENTS + EXPERIENCES + WORK (tasks follow AUTHORED requirements,
# never imported anatomical facts).
# ----------------------------------------------------------------------------
def make_requirements_tasks():
    objs = []
    reqs = [
        ("req.every_bone_sealed", "THE ANATOMICAL COMPARTMENT LAW",
         "Every intended skeletal bone/segment owns one sealed hydraulic compartment "
         "(operator correction 2026-09-13: \"you can't just have four sections\"). "
         "Treat this as Chimera's ENGINEERED anatomy, not a claim that biological "
         "bones are hermetic water bags.",
         "verification: compartment count matches the bone count, every cell "
         "conserves, and a press on any bone answers in THAT bone's cell -- not a "
         "neighbor's",
         ["inst.comp.thigh_l", "inst.comp.shin_l", "inst.comp.foot_l"]),
        ("req.mass_preserved", "Material inventory preservation",
         "Preserve the 13,824.5 kg material inventory when repartitioning; any "
         "exchange is accounted between named regions.",
         "verification: sum of region masses unchanged by a partition; exchanges "
         "carry named-region accounting",
         ["material.water", "inst.band.feet", "inst.band.shins",
          "inst.band.thighs", "inst.band.torso"]),
        ("req.sealed_design_is_chimera", "The sealed-compartment design is a Chimera requirement",
         "Imported reference data (Uberon/RO/QUDT/OpenSim/BodyParts3D) is REFERENCE; "
         "selecting a creature parameter is an explicit adaptation decision with "
         "applicability and validation. The custom sealed-compartment design remains "
         "a Chimera requirement regardless of what biology says.",
         "verification: no imported fact auto-becomes a creature parameter or task; "
         "join records are explicit mappings",
         []),
        ("req.press_answer_chain", "The press-answer chain",
         "The near product needs a convincing, falsifiable chain: press -> local "
         "deformation -> sensing -> physical response -> changed consequence after damage.",
         "verification: the player/developer can select a bone-associated "
         "compartment, inspect its intended and implemented boundaries, press it, "
         "observe its local response, interrupt a relevant physical or sensory path, "
         "and see the resulting evidence attached to the same stable graph identities",
         ["experience.press_and_response", "experience.local_withdrawal"]),
        ("req.honest_measurement", "Honest measurement (E38)",
         "Every shown quantity has units, provenance, model assumptions, and "
         "appropriate precision; virtual simulator measurements are distinguished "
         "from real-world ones (the former do not independently validate the "
         "simulator's material model).",
         "verification: cross-section inspection shows units + provenance; virtual "
         "vs real labels present",
         []),
        ("req.value_gate_distinct", "The $25 gate is machine-checkable, distinct from willingness-to-pay",
         "Preserve the $25 gate's actual definition and distinguish it from human "
         "willingness-to-pay evidence (E42: a machine-checkable gate validates "
         "conditions; WTP still requires evidence from people).",
         "verification: the gate's definition is preserved verbatim; human WTP "
         "records are a different evidence kind",
         []),
    ]
    for rid, name, statement, verification, deps in reqs:
        objs.append({
            "id": rid, "kind": "requirement", "name": name,
            "classification": None, "status": "specified", "priority": "P0",
            "build_rank": None, "inventory_anchor": None, "spatial": None,
            "geometry": None, "physical": {"statement": statement,
                                           "verification": verification},
            "attachments": [], "dependencies": list(deps), "evidence": [],
            "falsifier": {}, "unknowns": [],
            "notes": "AUTHORED requirement -- tasks may follow only these, never "
                     "imported anatomical facts",
            "provenance": dict(SHIP_GOAL_PROV, **BRIEF_PROV),
        })

    # experiences (product-side targets)
    exps = [
        ("experience.press_and_response", "Press and receive an honest answer",
         "The approved first-proof question: which unfinished structures enable "
         "press-and-response, have prerequisites available, and lack passing falsifiers?",
         "A press deforms locally, the cell answers in its pressure, and the answer "
         "survives independent calculation."),
        ("experience.local_withdrawal", "Local withdrawal (select -> inspect -> intervene -> observe)",
         "The central falsifier demo: if the graph says a structure exists and works, "
         "we must be able to SELECT it, INSPECT its physical connections, INTERVENE "
         "on it (obstruct an actuator, disconnect a sensor path, disable a finite "
         "attachment), and OBSERVE the predicted change.",
         "An intervention on one compartment/limb changes exactly the predicted "
         "local things and nothing hidden."),
    ]
    for eid, name, statement, falsifier in exps:
        objs.append({
            "id": eid, "kind": "experience", "name": name,
            "classification": None, "status": "specified", "priority": "P0",
            "build_rank": None, "inventory_anchor": None, "spatial": None,
            "geometry": None, "physical": {"statement": statement},
            "attachments": [], "dependencies": [], "evidence": [],
            "falsifier": {"statement": falsifier, "acceptance_test": None,
                          "status": "untested"},
            "unknowns": [], "notes": "player experience (product-side target)",
            "provenance": dict(BRIEF_PROV),
        })

    # work items with EXPLICIT authored priorities
    works = [
        ("work.partition_leg_l", "Partition the left leg into per-bone volumetric regions",
         1, ["cap.classify_bind_seal", "cap.cut_split"],
         ["experience.local_withdrawal", "experience.press_and_response"],
         "Derive segments from skeleton connectivity in the reference configuration; "
         "labeled-volume/interface partition (oblique planes allowed; branch "
         "junctions and conforming caps are the hard part); validate closure, "
         "orientation, positive volumes, disjoint interiors, parent coverage, mass "
         "conservation; recheck under joint motion; never reclassify per frame.",
         "Acceptance = req.every_bone_sealed verification on the leg: count matches, "
         "cells conserve, press answers in the right bone's cell."),
        ("work.septa_leg_l", "Build the leg's shared septa as load-bearing walls",
         2, ["cap.cut_split"],
         ["experience.local_withdrawal"],
         "Matching internal interfaces wherever neighboring volume elements differ; "
         "a shared septum is ONE physical wall (opposite orientation per region); no "
         "double stiffness/mass, no gaps; distinguish geometric closing face from "
         "implemented load-bearing septum.",
         "Puncture thigh_l: shin_l keeps its inventory; total system mass conserved."),
        ("work.causal_demo_leg_l", "One honest causal intervention on the existing machinery",
         3, ["cap.reflex_plumbing"],
         ["experience.local_withdrawal"],
         "Smallest supported intervention: obstruct an actuator, disconnect a "
         "sensor path, or disable a finite attachment -- connected to EXISTING "
         "measured inputs and the EXISTING bounded actuator/intent system. No "
         "anatomical tendon-cut claim while a hidden actuator supplies the same force.",
         "Disconnecting the sensory path removes its active contribution while "
         "passive mechanical response remains (acceptance 4); obstructing motion "
         "respects the force cap and yields reaction loads (acceptance 5)."),
        ("work.reference_adaptation_osim", "Adapt the OpenSim leg reference explicitly",
         4, [],
         ["experience.press_and_response"],
         "Join the imported OpenSim leg model (leg6dof9musc) to creature segments "
         "ONLY through explicit mapping records; name similarity yields CANDIDATES, "
         "never equivalences; any parameter selection becomes an adaptation decision "
         "with applicability + validation (req.sealed_design_is_chimera).",
         "Each selected parameter carries source, units, applicability, and a "
         "validation plan; virtual vs real measurement distinguished."),
        ("work.inspect_consistent_ids", "Inspection with consistent IDs and timestamps",
         5, [],
         ["experience.press_and_response"],
         "The selected structure, pressure trace, sensor event, and actuator "
         "response carry consistent IDs and timestamps; report latency and sampling "
         "limits (300 Hz outer tick = 3.33 ms; REST GET snapshot, no in-tick "
         "roundtrip). Graph-layout coordinates can never modify engine coordinates.",
         "Acceptance 9 graph side: one inspection record joins structure + pressure "
         "+ intervention by stable ids + engine ticks/UTC."),
    ]
    for wid, name, pri, deps, enables, plan, acceptance in works:
        objs.append({
            "id": wid, "kind": "work", "name": name,
            "classification": None, "status": "specified", "priority": "P0",
            "build_rank": None, "inventory_anchor": None,
            "spatial": None,
            "geometry": {"shape": None, "is_placeholder": True,
                         "note": "a roadmap task has NO physical extent; it "
                                 "associates with physical objects without "
                                 "acquiring fabricated geometry"},
            "physical": {"plan": plan},
            "attachments": [], "dependencies": list(deps), "evidence": [],
            "falsifier": {"statement": plan.split(";")[0],
                          "acceptance_test": acceptance, "status": "untested"},
            "authored_priority": pri,
            "enables": list(enables),
            "unknowns": [],
            "notes": "AUTHORED task following req.every_bone_sealed / "
                     "req.press_answer_chain; never derived from imported facts",
            "provenance": dict(SHIP_GOAL_PROV, **BRIEF_PROV),
        })

    # capabilities (engine machinery an implementation may reuse)
    caps = [
        ("cap.classify_bind_seal", "classify -> bind -> seal pipeline", "geometry_built",
         "mesh import, 9/28 auto-pins, classification, IDW binding, cut-and-weld seal "
         "with degenerate-split guard (0.5% parent volume)",
         "an importer that passes only before the first joint bends has not imported "
         "a physical creature"),
        ("cap.cut_split", "Cut/split machinery with degenerate-split guard", "geometry_built",
         "0.5% parent-volume guard; a geometrical split that caps both daughters is "
         "NOT equivalent to an open wound",
         "a rupture that leaves every physical connection intact is only a damage counter"),
        ("cap.reflex_plumbing", "Reflex plumbing (breath/flinch/startle)", "geometry_built",
         "volume-target breathing, pressure-triggered flinch, pressure-rate startle; "
         "pressure_coupling route flag severs pressure->intent (negative control)",
         "a reflex whose response is unchanged by severing its sensory path cannot "
         "demonstrate a reflex"),
        ("cap.gait", "Gait machine (stance/lift/reach/load)", "geometry_built",
         "contact/pressure/lean transitions measured; controller interruption "
         "produced abort/stumble; 28 measured joint pins; stance servos",
         "cutting the controller mid-stride must stumble, never glide"),
        ("cap.xpbd_solver", "The verified XPBD solver", "geometry_built",
         "volume/joint/servo/contact constraints, 300 Hz, bounded across tested "
         "substep counts; the BASELINE -- integrator replacement is a separate "
         "experiment",
         "stability is not fidelity"),
    ]
    for cid, name, status, what, fz in caps:
        objs.append({
            "id": cid, "kind": "capability", "name": name,
            "classification": None, "status": status, "priority": "P0",
            "build_rank": None, "inventory_anchor": None, "spatial": None,
            "geometry": None, "physical": {"law": what}, "attachments": [],
            "dependencies": [], "evidence": [],
            "falsifier": {"statement": fz, "acceptance_test": None,
                          "status": "untested"},
            "unknowns": [], "notes": "existing engine machinery (reuse, don't replace)",
            "provenance": dict(BRIEF_PROV),
        })
    return objs


# ----------------------------------------------------------------------------
# RELATIONS (authored, typed, directed; multiplicity preserved)
# ----------------------------------------------------------------------------
def make_relations():
    rels = []
    a = rels.append
    # containment / bounding
    a(("region.body_interior", "contains", "region.band.feet", "4-band partition"))
    a(("region.body_interior", "contains", "region.band.shins", "4-band partition"))
    a(("region.body_interior", "contains", "region.band.thighs", "4-band partition"))
    a(("region.body_interior", "contains", "region.band.torso", "4-band partition"))
    a(("memb.skin", "bounds_region", "region.band.feet", "exterior wall"))
    a(("memb.skin", "bounds_region", "region.band.shins", "exterior wall"))
    a(("memb.skin", "bounds_region", "region.band.thighs", "exterior wall"))
    a(("memb.skin", "bounds_region", "region.band.torso", "exterior wall"))
    a(("memb.skin", "bounds_region", "region.body_interior", "the seal itself"))
    # shared septa: ONE wall, TWO owners (two distinct edges, orientations differ)
    a(("memb.septum.feet_shins", "bounds_region", "region.band.feet", "side A"))
    a(("memb.septum.feet_shins", "bounds_region", "region.band.shins", "side B (same wall)"))
    a(("memb.septum.shins_thighs", "bounds_region", "region.band.shins", "side A"))
    a(("memb.septum.shins_thighs", "bounds_region", "region.band.thighs", "side B (same wall)"))
    a(("memb.septum.thighs_torso", "bounds_region", "region.band.thighs", "side A"))
    a(("memb.septum.thighs_torso", "bounds_region", "region.band.torso", "side B (same wall)"))
    # per-bone (specified) septa name their two sides before geometry exists
    a(("memb.septum.thigh_l_shin_l", "bounds_region", "region.seg.thigh_l", "side A (planned)"))
    a(("memb.septum.thigh_l_shin_l", "bounds_region", "region.seg.shin_l", "side B (same wall, planned)"))
    a(("memb.septum.shin_l_foot_l", "bounds_region", "region.seg.shin_l", "side A (planned)"))
    a(("memb.septum.shin_l_foot_l", "bounds_region", "region.seg.foot_l", "side B (same wall, planned)"))
    # segments compose the limb
    a(("region.leg_l", "contains", "region.seg.thigh_l", "skeleton connectivity"))
    a(("region.leg_l", "contains", "region.seg.shin_l", "skeleton connectivity"))
    a(("region.leg_l", "contains", "region.seg.foot_l", "terminal segment (explicit)"))
    # attachments (bonded rims)
    a(("seg.thigh_l", "attached_to", "seg.shin_l", "knee articulation (measured pin frame.knee_l)"))
    a(("seg.shin_l", "attached_to", "seg.foot_l", "ankle articulation (measured pin frame.ankle_l)"))
    a(("seg.thigh_l", "inside", "region.leg_l", "membership: bone path of the limb"))
    a(("seg.shin_l", "inside", "region.leg_l", "membership"))
    a(("seg.foot_l", "inside", "region.leg_l", "membership"))
    # force transmission (physical; CYCLES ALLOWED -- action/reaction pairs are real)
    a(("seg.thigh_l", "transmits_force_to", "seg.shin_l", "knee contact"))
    a(("seg.shin_l", "transmits_force_to", "seg.thigh_l", "reaction (Newton's 3rd) -- cycle is physical"))
    a(("seg.shin_l", "transmits_force_to", "seg.foot_l", "ankle contact"))
    a(("seg.foot_l", "transmits_force_to", "seg.shin_l", "reaction -- cycle is physical"))
    a(("actuator.joint_servos", "transmits_force_to", "seg.shin_l",
       "knee servo intent (force/torque-capped; NOT contractile tissue)"))
    # signal path (finite delay, disconnectable)
    a(("sensor.scalar_cell_pressure", "carries_signal_to", "pathway.pressure_to_intent",
       "per-cell pressure events; delay = one outer tick (3.33 ms)"))
    a(("pathway.pressure_to_intent", "carries_signal_to", "actuator.joint_servos",
       "flex intent to the binding-derived strut pin"))
    # material / model use
    for band in ("feet", "shins", "thighs", "torso"):
        a((f"inst.band.{band}", "uses_material", "material.water", "fluid inventory"))
        a((f"inst.band.{band}", "uses_model", "model.water_compressibility", "pressure law"))
        a((f"inst.band.{band}", "inside", "region.body_interior", "4-band partition"))
    a(("memb.skin", "uses_material", "material.skin_membrane", "surface material"))
    a(("memb.skin", "uses_model", "model.press_indentation", "press answer (qualified reduced)"))
    a(("memb.skin", "uses_model", "model.exponential_recovery", "recovery (NOT healing)"))
    for comp in ("inst.comp.thigh_l", "inst.comp.shin_l", "inst.comp.foot_l"):
        a((comp, "uses_material", "material.water", "planned fluid inventory"))
        a((comp, "uses_model", "model.water_compressibility", "per-region pressure law"))
    # provenance: instances derived_from measured frames
    a(("seg.thigh_l", "derived_from", "frame.hip_l", "measured pin"))
    a(("seg.thigh_l", "derived_from", "frame.knee_l", "measured pin"))
    a(("seg.shin_l", "derived_from", "frame.knee_l", "measured pin"))
    a(("seg.shin_l", "derived_from", "frame.ankle_l", "measured pin"))
    a(("seg.foot_l", "derived_from", "frame.ankle_l", "proximal end"))
    a(("inst.band.feet", "derived_from", "frame.ankle_l", "band cut at measured ankle height"))
    a(("inst.band.shins", "derived_from", "frame.ankle_l", "band cut at measured ankle height"))
    a(("inst.band.shins", "derived_from", "frame.knee_l", "band cut at measured knee height"))
    a(("inst.band.thighs", "derived_from", "frame.knee_l", "band cut at measured knee height"))
    a(("inst.band.thighs", "derived_from", "frame.hip_l", "band cut at measured hip height"))
    a(("inst.band.torso", "derived_from", "frame.hip_l", "band cut at measured hip height"))
    a(("param.kappa", "derived_from", "material.water", "the fluid's compressibility"))
    return rels


def main():
    os.makedirs(OUT, exist_ok=True)
    files = {
        "types.json": make_types(),
        "instances.json": make_instances(),
        "mechanisms.json": make_mechanisms(),
        "requirements_tasks.json": make_requirements_tasks(),
    }
    for fname, objs in files.items():
        ids = [o["id"] for o in objs]
        assert len(ids) == len(set(ids)), f"duplicate ids in {fname}"
        path = os.path.join(OUT, fname)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(objs, f, indent=1, ensure_ascii=False)
        print(f"wrote {path}: {len(objs)} objects")
    rels = make_relations()
    with open(os.path.join(OUT, "relations.json"), "w", encoding="utf-8",
              newline="\n") as f:
        json.dump([{"src": s, "rel": r, "dst": d, "note": n} for s, r, d, n in rels],
                  f, indent=1, ensure_ascii=False)
    print(f"wrote relations.json: {len(rels)} authored relations")


if __name__ == "__main__":
    main()
