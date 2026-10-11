# SEALED — an action RPG built from living structures

Working title: **SEALED** (alternates: *Tension*, *The Sump*, *Vivarium*).
Original concept: Qwen, 2026-10-11. Design and engineering revision: Codex, 2026-10-11.

**Confirmed direction:** grow ChimeraEngine itself. The user chose Option B on
2026-10-11; no Godot or Unreal host. **This document is a game-design proposal**
and an implementation sequence, not a claim that its proposed systems work today.
The selected project graph still governs scientific requirements and release gates.

The aim is to turn the membrane inventory into a game where understanding a body
or structure gives the player more ways to act. The player should come away saying,
“I made that work,” and “this is the creature I have cared for.”

## 1. The game we are making

You are a Warden bonded to a creature in the Sump, a world of living shelters,
strained bridges and animals whose bodies bear the history of their lives.
You explore, fight, rescue and build by redirecting force and resources through
those bodies. Your companion is also your climbing partner, load bearer and
collaborator in improvised machines.

The distinguishing feature is **transferable understanding**. Learning how to brace
an injured limb teaches you how to support a broken bridge. Learning how to isolate
a leaking chamber teaches you how to protect the lair. A tendon spool can become a
splint, a climbing aid, a winch or a trap because its attachments and loading change.

This is a third-person action RPG with an emphasis on experimentation. Combat must
be responsive, exploration must reward curiosity, and care must change what happens
on the next expedition. Physical consistency gives choices consequences; presentation,
encounters and pacing make those choices enjoyable.

**The first promise is small:** one companion, one damaged crossing, one rescue,
and several physically distinct ways to bring everyone home.

## 2. What the new concepts unlock

The opportunity is in combinations, not in making 42 unrelated features from
[THE_MEMBRANE_INVENTORY.md](THE_MEMBRANE_INVENTORY.md). Each row below is a proposed
gameplay application. Its prerequisites remain work unless evidence in §3 says otherwise.

| Physical idea | What the player can do with it | A memorable situation | Engineering prerequisite |
|---|---|---|---|
| Independent compartments and shared walls | Isolate a damaged region; divide a store; build redundancy | Sacrifice one bridge chamber to keep the route behind you intact | Closed region graph, one physical owner per shared wall, separate inventories |
| Tendons, insertion strength and slack | Brace, pull, suspend, tension, release; reroute a load | Turn your climbing line into a temporary leg brace, then recover it | Finite attachment patches, tensile failure, reactions on both endpoints |
| Capsules, contact and friction | Wedge, lever, pin, trip and stabilize | Beat a stronger predator by denying its footing rather than exhausting a bar | Coupled body dynamics, finite restraints, contact and traction |
| Punctures, valves and transport | Vent, transfer pressure, isolate leaks, control a passage | Open a pressure door by equalizing it instead of breaking it | Gas/liquid inventories, flow law and transported energy; rupture alone is insufficient |
| Adhesives, patches and cure | Make temporary repairs, reinforce seams, construct reusable joints | Hold a patch in compression while a companion braces the wall | Material supply, adhesion/cure state, strength and failure under renewed loading |
| Material differences and geometry | Trade stiffness against weight, flexibility against protection | A stiff splint restores carrying but makes a narrow squeeze harder | Versioned material profiles, section geometry, mass and inertia updates |
| Touch, proprioception, delays and reflexes | Read strain through the companion; exploit an enemy's limited information | A loaded foothold warns through posture and sound before it fails | Signals caused by contact/load, bounded propagation, interruption controls |
| Yielding, damage and repaired topology | Track history through function, not just a cosmetic scar | The repaired side of a bridge changes which route is safe next time | Persistent rest state, connectivity, residual strength and serialization |
| Thermal transfer and phase change | Store heat, soften a seal, release a frozen mechanism, cool a load | Spend scarce charge to thaw a valve, or take the long mechanical route | Temperature, heat capacity, transfer, latent heat and a tested material range |
| Growth and resource transport | Grow a load path, relocate a room, specialize a companion | Build a light shelter now or retain the material for tomorrow's climbing organ | Matter input, construction work, feasible geometry and stable topology insertion |
| Environmental and ecological feedback | Change access, food routes and shelter conditions | A repaired water route brings grazing animals back, attracting predators later | Explicit resource sources/sinks and scoped agents; a whole ecosystem is not required |

Prioritize the first six rows for a reusable construction vocabulary. Sensing makes
their consequences readable. Thermal systems, growth and ecology expand that vocabulary
after the basic interactions can be played, saved and recovered.

### Three scenes to build toward

**The broken crossing.** Your companion cannot carry the rescued animal across a
sagging bridge. You can unload supplies, tension a second support, lead both animals
through separately, or lower the load and haul it up the other side. Each solution
changes loads and geometry. There is no mission flag requiring one specific solution.

**The injured rival.** A predator returns with a damaged forelimb and favors a different
stance. You can drive it away, repair it to gain safe passage, or lure it onto ground
where that stance is a disadvantage. This needs persistent functional damage and an
AI that observes its own capabilities; it does not need a general social simulation.

**The living workshop.** A lair tendon normally closes a gate. You disconnect it,
attach it to a hauling frame and use stored tension to raise a chamber for repairs.
Doing so leaves the gate unsecured. Construction becomes rearranging a useful system,
with visible consequences, rather than selecting a larger structure from a menu.

These are encounter proposals and acceptance scenarios, not current engine features.

## 3. Starting point: evidence and limits

Reviewed checkout: `E:/PythonChimera`, branch `WK-ENGINE-PATHS-20260929-PR`,
HEAD `16097866b22d160d69ef2cf6f67802067164d507` at the start of this revision.
The working tree contains unrelated changes and untracked experiments. This review
reads their existence without adopting them as finished features. No controller
session was provisioned for this edit; it is repository-only planning.

| Capability | What the inspected source/evidence supports | What it does not establish |
|---|---|---|
| Energy-based tendon drive | `tendon_drive.hpp` and the round-11 report describe one default-off knee drive; unit checks cover ledger, sever, stall, rest and monotonic behavior | Whole-body locomotion, measured biological parameters, healing or a complete combat system |
| Tendon accounting | Round 11 reports 759 armed frames, maximum residual about `1.055e-12 J`, and zero violations against its `1e-6 J` guard | A universal world-energy tolerance or a proof of every other solver |
| Creature appearance and binding | The existing rigged mesh and sealed-cell demo provide a visible body and interaction surface | Correct inertias, independent physical degrees of freedom or stable movement of every limb |
| Local sever/rupture demonstrations | Existing demo paths provide a starting point for interrupting a force path and changing containment | Spatial weapon contact, arbitrary cracks, conserved leak flow, choking or repair |
| Follow camera and first lighting pass | Commits `6107d763` and `813c8c76`, with round-11 evidence, add optional follow view, lit materials and ledger feedback | A completed camera for fast combat, shadows, game art or horizontal locomotion; that report explicitly describes single-Y root motion |
| Lessons and shell | The existing lesson progression, restart and interaction loop are reusable onboarding material | A complete rescue encounter, RPG progression or a finished commercial release |
| Graph and source/evidence pins | Provenance and versioned descriptions of scientific/content inputs | A runtime save format, rollback, cross-hardware deterministic replay or anti-cheat |
| Gait and other experiments | Candidate files and earlier receipts exist | Current integration qualification; inspect the relevant graph contract and exact build before relying on them |

Evidence entry points:

- [Round-11 camera, lighting and ledger report](../tools/game_shell/evidence/round-11/11_camera_light_report.md).
- [Round-10 playable report](../tools/game_shell/evidence/round-10/10_playable_report.md).
- [Tendon implementation](../ChimeraEngine/engine/tendon_drive.hpp) and
  [MembraneTick interface](../ChimeraEngine/engine/membrane_tick.hpp).
- [Membrane inventory](THE_MEMBRANE_INVENTORY.md), especially its final five-step build order.
- Graph contracts `req.current_product_focus`, `req.teddy_gpu_matter_kernel`,
  `req.creature_assembly`, `req.body_environment_interface`, `req.embodied_senses`,
  `req.engine_game_release` and `req.documentation_admission`.

These are source and historical-evidence references. No fresh physics run or
playtest was performed merely to revise this document. The first camera/lighting
slice is already reported complete and should not be reassigned as new work.

## 4. Design rules that let the systems combine

1. **Function follows the physical path.** An attachment, wall, valve or actuator
   must do the work attributed to it. Severing the path removes its contribution;
   a hidden hinge or animation must not silently replace it.
2. **Energy constrains action; it is not the only resource.** Track usable energy,
   matter, contained fluid/gas, heat and load-bearing structure separately. Food
   can provide material and chemical energy through a declared reduced process.
   Money is a social representation; it is not literally joules. A charged but
   punctured body and an intact exhausted body should create different problems.
3. **Change a capability, not an invisible score.** Damage affects a load path,
   seal, sensor or actuator. A health summary may communicate those conditions,
   but it must not secretly determine physical outcomes.
4. **Give the player a usable interface.** Attachment previews, strain indicators,
   material recipes, maps and short tutorials are allowed. “No menus” and “no UI”
   are not product requirements. Construction must be understandable without
   knowing the engine's terminology.
5. **Make experimentation recoverable.** Show a warning before irreversible
   failure when the character could perceive one. Offer a quick release, a
   temporary brace and a route home. Permanent injury must not trap a player in
   a campaign they can no longer play.
6. **Keep a small vocabulary useful everywhere.** Adding a material or part should
   create new combinations of existing verbs before it adds another bespoke rule.

Content has authored parameters and progression rules. Keep measured physical
inputs, declared synthetic material profiles and game-design choices distinguishable.
The existing drive's parameters are explicitly synthetic; do not relabel them as
biologically measured to strengthen the fiction.

## 5. The playable vocabulary and control contract

The first prototype needs **inspect, touch, attach, pull, brace, cut, patch and
release**, plus locomotion and a finite energy refill. Later verbs include vent,
transfer, cure and grow, after their physical prerequisites pass.

| Player intention | Engine action | Player feedback | Meaningful limit |
|---|---|---|---|
| Move toward a point | A controller requests bounded joint effort and support changes | Foot contact, lean, pace and exertion | Load, balance, traction, available work |
| Pull or carry | Establish an attachment and a force-limited drive | Visible line tension, posture, slip | Both bodies receive reactions; anchor strength matters |
| Brace | Add an admitted support or tension path | Deflection changes and load redistributes | Brace weight, fit, buckling/slack and attachment strength |
| Cut | A tool contact satisfies the admitted failure rule | The specific load path opens; motion changes | Reach, alignment, material and work; a click alone is not cutting |
| Patch | Consume a compatible patch and attach it across a defect | Containment/stiffness recovery with a visible seam | Fit, remaining damage, cure and renewed loading |
| Inspect | Reveal information available to the Warden or companion | Shape, pulse, strain, leak direction; optional instrument overlay | Sensor range and access; no unexplained knowledge through walls |

Use intent-level controls: walk here, hold this, brace there, release now. The
player should not manually operate every muscle. A grasp preview snaps to valid
attachment regions while the resulting attachment still has finite strength.
Input buffering, camera assistance and readable silhouettes improve control without
injecting unaccounted forces or teleporting bodies.

Keep a **quick release** available during pulls and grapples. It releases the
constraint; stored energy and momentum continue to evolve. It is not a freeze key.

## 6. The first vertical slice: “Bring Them Home”

**Target session:** 10–15 minutes, a design target to validate with players.
One compact ravine, one companion, one stranded creature or salvage load, one
damaged crossing, and one repair alcove. Use the selected monkey appearance.
Start with the graph's terrestrial reference conditions; the moon setting is
fiction until a different environment profile is deliberately admitted.

### The sequence

1. **Bond.** Touch a supported limb and command a short pull. The companion's
   posture and response establish that it senses loading and can stall.
2. **Discover.** Find the crossing and the stranded target. See a strained
   attachment and a leaking or structurally open chamber, according to the
   currently qualified damage model. The objective is clear before inspection.
3. **Choose.** Cross light, brace the bridge, or rig a haul. Provide enough
   material for two viable approaches, but not effortless completion of all three.
4. **Commit.** Move the target. Its weight changes the problem. A poor attachment
   slips or fails with enough warning to permit release and recovery.
5. **Care.** Repair a damaged component and retest it under a small load.
   The repair changes a measured capability and remains after save/reload.
6. **Return.** Reach the alcove with the target and companion. The new resource
   buys a useful choice: restore a brace, reinforce storage, or retain expedition stock.

**Success:** target and companion reach the safe area with a stable support path.
**Recoverable failure:** lose a support, spill a bounded resource, or drop the load
onto a recoverable ledge. **Terminal failure:** all viable recovery paths are lost;
offer a checkpoint restart with the reason visible. The first slice does not require
permadeath, biological regrowth, autonomous predators or an entire settlement.

### The gate

- An unfamiliar player starts without an agent or developer operating the engine.
- At least two solutions produce different measured load/attachment histories.
- A damaged path changes behavior; a patch/brace restores only its stated function.
- The player can explain the failure and recover using an offered physical action.
- Saved damage, inventory, attachments and mission state survive reload.
- Turning off the engineering HUD leaves enough visual/audio feedback to play.
- Record control confusion, time to first useful action, recoveries and whether
  the player tries a second solution. A “whoop” is useful feedback, not the sole gate.

Initial playtest proposal: five fresh players, at least four complete the objective
without a developer rescue, and each can identify one physical cause of failure or
success. These counts are a product hypothesis, not scientific validation or evidence
that the game is commercially ready. Preserve failures and revise the encounter.

## 7. Combat, companionship and progression

### Combat is a contest over support and access

Begin with a single opponent built from the same bounded components. Its decisions
can differ from the player's; its physical limits cannot be replaced by a difficulty
multiplier hidden inside the solver.

An encounter has readable stages: observe posture, provoke a commitment, contest
support, exploit an opening, then choose escape, capture or a disabling injury.
Reward correct timing and positioning before permanent cutting. Temporary loss of
balance, trapped reach, a loaded tendon or a blocked route can all win an encounter.

Do not advertise choking from pressure alone. Respiration requires gas transport
and resource accounting. Likewise, a generic impulse does not imply a spatially
correct fracture; the contact and failure model must establish where damage occurs.

Enemies should retreat, protect a compromised side, seek support and avoid obviously
unsafe loads. Their perception is bounded: contact, line of sight and admitted
sensors feed a compact local state machine or utility policy. Online language-model
calls are not part of combat timing, navigation, save validity or the physics loop.

### The companion becomes personal through useful history

Care changes behavior that the player can recognize: a trusted brace placement,
a remembered route, a preferred resting posture or a repaired region requiring
different loading. Begin with explicit, saved preferences and capability estimates.
Do not promise an unsolved general learning system.

Never make a permanent scar a mandatory downward spiral. Offer rehabilitation,
replaceable supports and alternative body configurations. A visible scar can remain
while lost function is restored through a different load path. Care must involve
diagnosis and choice, not repeated waiting timers.

### Progression creates tradeoffs and new combinations

| Progression choice | New opportunity | Cost or disadvantage |
|---|---|---|
| Reinforced carrying frame | Haul larger finds; protect a damaged limb | More mass, wider turning clearance |
| Longer elastic tendon | Reach distant anchors; store a launch impulse | Slack management and a more dangerous recoil |
| Additional compartment/valve | Survive one leak; redistribute a resource | Extra walls, connections and maintenance |
| Softer contact surface | Grip and cushion on a particular substrate | Wear, compliance or reduced cutting resistance |
| Better sensing attachment | Earlier load warning; more precise manipulation | Material/energy cost and exposure to damage |
| Grown structural branch, later | A new route or support geometry | Matter supply, construction work, time and changed inertia |

These are build directions, not rigid character classes. Unlock knowledge through
successful inspection, recovered patterns and experiments; unlock construction through
materials, suitable geometry and available work. Energy accumulation alone must not
create matter, anatomical information or an instant new room.

The campaign is a chain of places whose constraints invite different assemblies.
The Fringe teaches support and care; the Ribs rewards rigging and access; the Deep
Sump adds connected infrastructure and larger consequences. Build one chapter before
committing to three zones or a 10–20-hour content promise.

## 8. The lair, economy and world memory

The lair is the system the player gradually learns to maintain. Start with a store,
a repair surface and attachment points. Later add a nursery, a hauling frame,
pressure storage and a growing shelter. A new room requires an admissible structure,
material input and energy expenditure; thresholds authorize a construction process
rather than materializing an unsupported mesh.

The economy has several shortages: useful matter, usable energy, access, time and
safe transport. This supports rescue, salvage, construction and negotiation alongside
hunting. Predators should not be the only fuel source, and the only viable route
through the game should not be increasing destructive power.

Use a small number of authored ecological relationships first. Repairing one water
route or opening one passage changes where a few creatures can feed or shelter.
Show the causal chain before building a free-running ecology. Identify external
energy input and resource regeneration so a closed valley is not secretly creating
food or doomed to unavoidable depletion.

**Persistence is explicit engineering work.** Save the runtime state required for
continuation: stable object/component IDs, transforms and velocities, material and
fluid inventories, stored energy and temperature, damaged topology/rest state,
attachments, actuator state, AI memory, mission state, clock/RNG state, content and
solver versions. Include every constitutive internal state actually used by the
selected model, not just fields displayed in the UI.

Use a versioned checkpoint plus an ordered command/topology-event journal, written
atomically with one previous known-good checkpoint. Define journal compaction and
bounded disk use. Graph provenance identifies inputs; it does not substitute for
runtime serialization. Test an interrupted save, corrupted latest checkpoint, a save
during a loaded attachment, and reload after a cut and patch.

Replay needs a declared determinism scope and compatibility policy. Multiplayer,
anti-cheat and speedrun verification each need additional protocols and validation;
checksums alone establish none of them. Single-player is the initial release target.

## 9. Engineering shape: one engine, explicit boundaries

ChimeraEngine remains the whole runtime stack, with a headless physical core and
its own renderer. One process does not require every subsystem to mutate the same
state. Keep boundaries that make the game testable and saveable:

```text
Player input / bounded NPC observations
                  |
          intent and command queue
                  |
 fixed simulation clock -> physical state + component/attachment graph
                  |             |
           admitted events   inventory / work accounting
                  |
          immutable frame snapshot
             /             \
  in-engine rendering     gameplay feedback / UI
                  |
        checkpoint + ordered event journal
```

The renderer reads a completed snapshot and interpolates appearance where allowed.
It does not write forces, repair topology or advance the world clock. Graph/HTTP
inspection must be rate-limited consumers; do not serialize or synchronously log the
entire world on every physical substep.

### A component contract that makes combinations safe

Every admitted component declares its geometry, material profile, state, typed
connection points, carried/transported quantities, capacity and failure conditions.
An attachment has endpoints, an orientation/frame, compatible connection types and
a finite load path. A wire, tendon and fluid conduit are different port types;
their visual similarity must not permit invalid transfers.

An interaction carries an equal-and-opposite force or an explicitly paired transfer
where the selected law requires one. Discrete topology changes record what was removed,
created, transferred and dissipated. Separate systems may exchange work through a
defined interface; they may not each count the same physical wall or stored energy.

Keep the component catalog small: chamber, wall, tensile element, bounded actuator,
contact surface, attachment and patch first. Introduce a valve or heater only with
its transport/thermal contract. Game content combines these admitted components.

### Physical and computational scope

- Target the graph's fixed **300 Hz** simulation clock independently of rendering.
  Treat that as a qualification requirement, not proof that every existing demo
  already runs that way. Catch-up work must be bounded and slow frames reported.
- Close scale, mass, inertia and coordinate frames before tuning a gait. Do not
  silently resize an existing many-tonne profile to make it look like a small monkey.
- Qualify passive dynamics, bounded actuation, balance, then walk/turn/stop.
  Power removal preserves momentum and passive forces; ground removal permits falling.
- Respect the resident GPU matter-kernel contract. CPU orchestration and selected
  reference calculations do not justify moving the production physical world to CPU
  or using cosmetic skin over an unrelated character solver.
- Account for usable energy, elastic/kinetic/gravitational storage and modeled heat
  with explicit external work/flux. Track mass and transported species independently.
  Give each solver a justified tolerance; a tiny single-joint residual is not a
  whole-world accuracy promise.
- Admit damage, repair and growth at explicit simulation boundaries. Reject invalid
  geometry before publishing it to physics, collision, rendering or the save system.
- Keep LOD transitions conservative for their declared quantities. Never swap a
  loaded attached bridge or engaged creature to a visual-only approximation.

### Performance targets to measure

The initial reference machine is the user's RTX 4090 and i9-13900K with 128 GB RAM.
Test with the local LLM released through the existing GPU handoff mechanism.
Running the game beside a resident model is a separate operating profile.

Start with the companion, one interacting target/opponent, and the local structure.
Set a provisional 60 FPS presentation target at a declared resolution. Record median
and p95 frame time, p99 tick/catch-up behavior, control latency, GPU/host memory and
bytes read back. The 16.7 ms frame interval is a target, not a current measurement.
Set content and simulation budgets from those results before increasing creature count.

Bound caches, event journals, transient contact data and inactive objects. Repeatedly
load, damage, repair, save, unload and revisit the same scene; memory should reach a
stable plateau. “It fits once” does not establish a usable expedition loop.

## 10. Graphics and readability

Keep the confirmed **Option B: grow the current engine**. Godot and Unreal were
rejected as hosts. Preserve the ability to test the core headlessly and, after
qualification, let a separate game repository consume a pinned engine interface.
The repository split in `req.engine_game_release` does not require an external engine.

Give each important condition at least two readable cues: shape/posture plus sound,
motion plus a material change, or an icon plus a visible seam. Color alone is inadequate.
Energy glow is a designed visualization of selected state, not a claim that all
materials physically emit visible light. Distinguish charge, strain and temperature.

Visual work should improve decisions in this order:

1. Refine the existing follow camera: collision, occlusion, recovery after a fall,
   framing of companion + manipulated object, and optional horizon comfort.
2. Improve contact readability: stable depth, useful shadows/contact cues, materials
   that distinguish soft walls, stiff supports and active attachments.
3. Make load and failure readable: tendon tightening, support deflection, seam opening,
   leakage when modeled, and an unmistakable successful patch.
4. Add localized glow, cross-section inspection and selective translucency without
   turning every normal scene into an engineering display.
5. Add environmental dressing after geometry and silhouettes remain legible in motion.

Use one coherent small art set. An anatomically elaborate asset that the player cannot
read under load is less useful than a well-lit, consistent creature and workshop.
The existing 12 lessons become optional Warden training and contextual exercises;
do not require a long classroom prologue before the first meaningful expedition.

## 11. Roadmap and release gates

| Milestone | Deliverable | Exit evidence | Defer until later |
|---|---|---|---|
| M0 — preserve the baseline | Pinned playable demo; existing camera/lighting and tendon behavior recoverable | Known build, scoped historical receipts, explicit current limitations | Repeating already completed camera work |
| M1 — a body that carries a consequence | A complete bounded force path, admitted compartment ownership, local sensing, and locomotion/support qualification | Passive drop, stall, support loss, sever and renderer-rate controls; measured scale/inertias | Parkour, multiple species, whole-body biological fidelity |
| M2 — Bring Them Home | The compact rescue slice with two solutions, failure/recovery and a repair that persists | Physical controls plus observed fresh-player sessions from §6 | Predators if they delay the basic rescue; growth and large zones |
| M3 — combinations | One opponent, reusable rigging parts, a working lair and a third encounter solved with the same parts | Parts work outside their introductory puzzle; bounded memory across repeated sessions | Broad crafting catalog, detailed metabolism |
| M4 — one finished chapter | Reliable onboarding, save/recovery, presentation, settings and a coherent expedition arc | Declared hardware/fidelity envelope; offline install/start; user-confirmed game loop | Mandatory co-op or a promised campaign duration |
| M5 — expand only what worked | Further regions, selected thermal/growth/ecology interactions | Each new mechanism has a physical falsifier and a new player decision | Cosmic simulation and full molecular chemistry unless a later game specifically needs them |

Engine qualification and a named release precede the separate game repository, as
the graph requires. That release freezes interfaces, evidence scope and compatibility;
it does not declare all future science finished. Do not turn this design document
into an automatic controller queue or begin implementing all rows at once.

**Immediate next engineering assignment:** audit the complete force/support path and
choose one qualified route to a controlled carry/brace interaction. Reconcile existing
gait experiments before commissioning another controller. If walking remains unqualified,
use a supported manipulation test to prove attachment, load, cut and repair while the
locomotion work proceeds; do not present that stationary test as the finished RPG.

## 12. Risk controls that preserve the game

| Risk | Early signal | Response |
|---|---|---|
| Physics produces activity but few interesting decisions | Players repeat one strongest action in every encounter | Change geometry, available supports and consequences; test another solution with existing parts |
| Interaction feels slow or fussy | Players struggle to attach, aim or understand a failure | Improve intent controls, previews, camera and feedback before adding laws |
| Locomotion consumes the whole project | Candidate controllers never pass power/support controls | Scope a short supported interaction slice; retain the full-body gate and investigate the failing mechanism |
| Permanent damage punishes experimentation | Players reload after every injury or abandon a companion | Provide reversible supports, repair choices and fair recovery; preserve history without permanent uselessness |
| More detail exceeds the hardware budget | Long frames or memory growth during topology changes | Bound active scope, measure transition costs, and qualify reduced states rather than hiding failures |
| Fiction outruns implementation | A label says breathing, healing or growth but only a pose changes | Implement the missing transfer/state or use a narrower description until it is qualified |
| Infrastructure replaces game development | Workflows and catalogs grow while the rescue remains unplayable | Judge the next task by the player action it enables or the demonstrated blocker it removes |
| Multiplayer swallows the first release | Work begins on lockstep before saves and single-player recovery work | Ship the single-player contract first; choose replication after determinism and bandwidth tests |

The concept is successful when a player applies something learned in one context to
another, sees the expected consequence, and cares about the particular body or place
that consequence changed. Scientific checks establish the mechanism. Player observation
establishes whether using it is understandable and worth doing again.

## 13. Change and publication discipline

Preserve the original plan in Git history. New mechanics in this revision remain
proposals until the relevant graph admission and implementation work occur. Existing
measured evidence retains its original scope and date.

For each implementation milestone, record its prediction and falsifier, scoped source
changes, exact build/input identities, physical results and observed gameplay failures.
Commit explicit paths only and preserve other agents' work. Use the applicable
`Agent: NAME` trailer and the standing publication workflow: publish completed scoped
commits to the intended branch and verify the remote ref. Never force-push, reset,
stash or rebase the live shared checkout to obtain a clean-looking result.

Keep review/publication separate from master integration, graph admission and runtime
deployment. A document revision does not authorize changing those independently.
