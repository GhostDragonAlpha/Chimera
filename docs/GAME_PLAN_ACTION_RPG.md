# SEALED — an action RPG built from living structures

Working title: **SEALED** (alternates: *Tension*, *The Sump*, *Vivarium*).
Original concept: Qwen, 2026-10-11. Design, engineering and cross-genre revision:
Codex, 2026-10-11. Keep this plan in `GAME_PLAN_ACTION_RPG.md`.

**Confirmed direction:** grow ChimeraEngine itself. The user chose Option B on
2026-10-11; no Godot or Unreal host. **This document is a game-design proposal**
and an implementation sequence, not a claim that its proposed systems work today.
The selected project graph still governs scientific requirements and release gates.

The aim is to turn the membrane inventory into a game where understanding a body
or structure gives the player more ways to act. The player should come away saying,
“I made that work,” and “this is the creature I have cared for.”

**Reading route:** §§1–6 define the playable core; §§7–8 develop the companion
and world; §9 collects 60 genre lessons; §10 turns them into encounters, builds
and a chapter; §§11–14 connect those possibilities to implementation and tests.

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
7. **Borrow the decision that makes a genre work.** Preparation, inference,
   timing, expression and stewardship can share one world. Each proposed mode
   must identify the choice it adds and the existing parts it reuses.
8. **Teach, vary, combine, then transfer.** Introduce a relation in a readable
   situation, change one constraint, and later let the player recognize it
   elsewhere. Knowledge should keep working beyond its introductory encounter.
9. **Make room for several kinds of satisfaction.** Support curiosity, care,
   mastery, improvisation and quiet restoration. Rewards and pacing should
   acknowledge those motives without requiring every activity to become combat.

Content has authored parameters and progression rules. Keep measured physical
inputs, declared synthetic material profiles and game-design choices distinguishable.
The existing drive's parameters are explicitly synthetic; do not relabel them as
biologically measured to strengthen the fiction.

## 5. The playable vocabulary and control contract

The first prototype needs **inspect, touch, attach, pull, brace, cut, patch and
release**, plus locomotion and a finite energy refill. Later verbs include vent,
transfer, cure and grow, after their physical prerequisites pass.

The first repair may be a mechanically secured patch or an admitted brace.
Chemical curing and restored fluid containment are required only if the selected
repair depends on them; a structural repair must be described and tested as such.

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

## 9. What the rest of gaming can teach this game

The following library draws from **60 overlapping genre families and play styles**.
It is a design resource: each entry extracts a player experience, gives it a place
in SEALED, and identifies the work that would make it credible. Genre boundaries
are fluid; this is a broad collection of transferable ideas, not an exhaustive taxonomy.

The constant is the Warden, the companion and the physical world. A bridge can be
a platforming route, a stealth route, a delivery bottleneck, a defensive position
or a record of a previous accident. Those experiences become especially valuable
when a change made for one purpose affects the others.

**Stage labels refer to §13.** M2 ideas can inform the rescue's layout and feedback;
they do not enlarge its required feature list. M3 means a candidate for combinations,
M4 means a candidate for chapter polish, and M5 means optional expansion. Every
entry still requires its named prerequisites. **Beyond M5** means research only.

### Movement, contact and commitment

| Genre or play style | Lesson and SEALED application | Prerequisite and earliest candidate stage |
|---|---|---|
| G01 — Character action / beat 'em up | Expressive combinations should arise from situation: pull an arm, step outside its support, brace against a wall, then release. Reward varied useful control with presentation and optional mastery records. | Bounded effort, contact, interruption and recovery; M3. A combo rating must not multiply physical work. |
| G02 — Fighting games | Spacing, commitment, readable openings and counterplay make a small move set deep. A long reach loses leverage close in; a heavy brace resists a pull but turns slowly. | Reach and support envelopes, perceivable startup/recovery, clear collision; M3. Learnable timing can span a physical range. |
| G03 — Precision platformers | A demanding route feels fair when the player can read and repeat it. Make anchor spacing, line slack and safe recovery ledges legible before asking for a loaded crossing. | Qualified locomotion, grasp/release and camera; M2 layout lesson, M5 demanding traversal. Do not silently teleport a missed grasp. |
| G04 — Collectathons / open-world exploration | Curiosity needs visible destinations and a useful return. A glinting recovered bracket invites a detour; reaching it also reveals a shorter route home. | Landmarks, bounded navigation and meaningful salvage; M3. Avoid scattering identical collectibles solely to fill a map. |
| G05 — Metroidvanias | New capabilities reinterpret familiar places. A longer tendon opens a vertical route, while a compact carrying frame fits a passage that the reinforced frame cannot. | Capability-based route checks and persistent world changes; M3. Accept an unexpected physically valid early solution. |
| G06 — Soulslike action | Observation, consequential commitment and satisfying return paths make danger memorable. Let the player prepare a safe support, attempt a difficult crossing, then open a recovery shortcut. | Readable hazards, reliable controls and checkpoint recovery; M3. Difficulty comes from decisions, not hidden solver multipliers. |
| G07 — Giant-boss / climbing encounters | A large adversary can also be terrain. Support points, moving limbs and damaged attachments form routes that change as it moves. | Moving-surface contact, scale/inertia qualification, camera and safe detach; M5. Begin with a small moving structure before a giant creature. |

### Perception, threat and escape

| Genre or play style | Lesson and SEALED application | Prerequisite and earliest candidate stage |
|---|---|---|
| G08 — Tactical shooters | Angles, exposure and preparation can matter more than reaction speed. Fire a tether to create a hauling path while a shielded position protects the companion. | Projectile/contact law, finite launch energy, cover and line of sight; M5. New ranged tools must interact with existing materials. |
| G09 — Arena shooters / bullet hell | Clear trajectories turn danger into route planning. Read a sequence of falling debris or vent pulses, then cross through a gap or place a shield. | Visible telegraphs, qualified hazards and bounded event count; M5. Evading a hazard must remain distinct from camera visibility errors. |
| G10 — Artillery / trajectory games | A visible arc makes prediction and adjustment satisfying. Throw a line across a gap, estimate where it will land, then use the successful attachment to haul a load. | Finite launch work, projectile/contact rules and honest trajectory estimates; M5. Practice should improve judgment without randomizing an otherwise identical launch. |
| G11 — Stealth | Avoidance becomes interesting when sensing has causes. Move a load across a firm surface to reduce noise, or brace a creaking gate before opening it. | First use line of sight and declared contact-noise events; M3. Acoustic propagation, scent and fluid-carried traces need separate models. |
| G12 — Immersive simulations | A system should recognize a solution it was not scripted to expect. Enter a shelter by repairing its door, hauling its counterweight, making another opening or negotiating access. | Shared affordances and outcome-based objectives; M3. Content may constrain safety and resources without prescribing an exact action sequence. |
| G13 — Survival horror | Vulnerability and uncertain information give familiar actions new meaning. Inspect a dark chamber while the companion holds a failing support; the exit remains understandable. | Reliable low-light cues, bounded threat perception and escape options; M4. Suspense should not depend on unreadable controls. |
| G14 — Hunting / tracking | Evidence should guide hypotheses. Bent vegetation, displaced material and a distinctive contact pattern suggest a route and an injured side. | Scoped persistent traces linked to actual events, plus uncertainty; M5. A clue must not reveal more than its generating mechanism supports. |
| G15 — Extraction games | Choosing when to leave creates a compelling second half. Extra salvage increases load and may close the route used to enter. | Load-dependent traversal, an exit route and fair loss/recovery rules; M3. Valuable material should tempt, not force, another excursion. |
| G16 — Battle royale | Converging routes and scarce safe positions force changing priorities. A warned environmental event brings a few travelers toward the same shelter; cooperate, reroute or improve its capacity. | Qualified hazard and clear evacuation paths; M5. Borrow convergence before considering online elimination, large populations or a shrinking arena. |

### Puzzles, inference and timing

| Genre or play style | Lesson and SEALED application | Prerequisite and earliest candidate stage |
|---|---|---|
| G17 — Physics puzzles | Teach one relation, vary it, then let the player combine it. Brace a static load before meeting the same problem on a flexible crossing. | Inspectable load paths, multiple solutions and reset/recovery; M2. Test broad success regions, not a single exact placement. |
| G18 — Logic / programming puzzles | A readable chain of causes makes a mechanism understandable. Connect a sensor, finite drive and release so a hauling frame stops at a safe load. | Typed signals, explicit thresholds, bounded controller execution and manual override; M5. A command signal does not itself supply energy. |
| G19 — Detective / mystery games | Let the player infer what happened from the changed world. Compare a stretched attachment, an empty store and a broken support to reconstruct an accident. | Saved event-derived evidence, competing explanations and an evidence notebook; M3. An authored truth exists independently of the player's guess. |
| G20 — Adventure games / escape rooms | Environmental storytelling can teach a useful operation. An abandoned repair jig demonstrates how to support a door without a spoken tutorial. | Consistent affordances, inspectable demonstrations and escalating optional hints; M2. Avoid one arbitrary inventory-item pairing as the only answer. |
| G21 — Dungeon crawlers | Interconnected rooms make navigation, supplies and retreat one problem. Mark a chamber, secure a return line and decide whether a shortcut can carry the recovered load. | Small authored room graph, discoverable loops and explicit retreat resources; M3. Map knowledge is a reward even without a new enemy in every room. |
| G22 — Educational / scientific simulations | Prediction, intervention and observation make knowledge rewarding. Guess which support carries the load, test gently, then use the result in a rescue. | Optional instruments, visible uncertainty and reproducible local setups; M3. Reward a revised explanation as well as a correct first guess. |
| G23 — Rhythm games | Anticipation and synchrony can make cooperation tactile. Time a pull with a companion's effort or a swinging load's motion, using sound and visual cues. | Measured phase/load feedback and bounded actuation; M5. Timing changes the mechanical opportunity, not a magical damage bonus. |

### Planning, territory and logistics

| Genre or play style | Lesson and SEALED application | Prerequisite and earliest candidate stage |
|---|---|---|
| G24 — Turn-based tactics | Give the player time to compare consequences. Pause to mark a brace, a pull and a fallback, then execute those intentions in the physical world. | A declared single-player planning pause, queued intents and invalidation checks; M3. Preview uncertainty rather than promising an exact future trajectory. |
| G25 — Real-time strategy | Coordination creates choices about attention. Ask one capable helper to hold a support while the Warden routes material around it. | Per-agent task state, interruption, navigation and population budgets; M5. Start with one helper beyond the companion. |
| G26 — Tower defense | Defense can be construction under anticipated pressure. Reinforce a route, place a diversion and leave a controlled retreat path before a migration arrives. | Predictable arrivals, physically tested barriers and several viable routes; M5. Traps consume resources and may also endanger friendly bodies. |
| G27 — 4X / grand strategy | Local choices can change access and influence over a region. Repairing a crossing opens trade and shifts which settlement can maintain a water route. | A small explicit route/faction graph and slow strategic updates; M5. Represent distant consequences at an honest aggregate scale. |
| G28 — Wargames / logistics | Supply and evacuation can be the actual objective. Keep a convoy supplied, decide which span to reinforce, and rescue a disabled carrier. | Route capacities, travel costs, cargo ownership and bounded agents; M5. An off-screen route must account for transported stock. |
| G29 — MOBA / lane-control games | Objectives, pressure and distinct roles can focus a busy space. Two approaches to a shared pump create a choice between protecting access and repairing output. | Small objective graph and readable actor roles; M5. Borrow objective structure before considering teams, matchmaking or repeated waves. |
| G30 — Auto-battlers | Preparation and observation can reveal whether a configuration works. Compare two companion loadouts in a safe obstacle course, then inspect why one stalled. | Saved configurations, repeatable starts and understandable controllers; M3. Feedback must explain load and support rather than only rank a winner. |
| G31 — God games / ecosystem stewardship | Indirect intervention can be powerful. Restore water access or a nesting support, then observe how a few creatures change their choices. | Explicit needs, resource flows and bounded ecological policies; M5. The Warden acts through local construction rather than unexplained global influence. |

### Building, producing and caring

| Genre or play style | Lesson and SEALED application | Prerequisite and earliest candidate stage |
|---|---|---|
| G32 — Survival crafting | Preparation should express a forecast of trouble. Choose patches, tendon length and carrying space for a route whose risks can be observed. | Material accounting, repair usability and clear environmental needs; M3. Avoid mandatory upkeep that consumes attention without a decision. |
| G33 — Sandbox / voxel construction | The player values ownership of a working invention. Build a hoist from admitted parts, then discover it can also act as a rescue frame. | Typed attachments, stability validation, undo in planning and safe teardown; M3. Free-form topology is a later capability, not implied by modular parts. |
| G34 — Factory automation | Bottlenecks and useful feedback make a small system engaging. A lair winch, storage rack and stop sensor reduce repeated hauling. | Qualified transport/actuation, finite work, queue limits and diagnostics; M5. Automate an understood task before adding production chains. |
| G35 — City builders / colony sims | Arrangement should change function. Put a store close to a repair surface, but leave clearance for injured arrivals and the companion's turning envelope. | Occupancy, access, task allocation and bounded inhabitants; M5. One functional workshop is the first test. |
| G36 — Tycoon / economic games | Value comes from scarcity, quality and delivery cost. A sound brace may be worth more intact than recycled; a remote settlement pays for access restored. | Explicit stock, offers, condition and finite demand; M5. Economic prices remain social rules distinct from physical inventories. |
| G37 — Farming / life simulations | Familiar routines become meaningful when they reflect care and change. Tend a useful growing material and decide between today's harvest and a stronger support later. | Admitted growth/resource transport and an explicit schedule; M5. Start with one meaningful species/process, not many interchangeable crops. |
| G38 — Creature collection / breeding | Different capabilities encourage attachment and experimentation. Rescue creatures suited to grip, carry or sense, each with needs that change an expedition. | Qualified body templates and a strict active population limit; M5. Heredity and biological breeding require their own model; collection does not establish them. |

### Builds, repeated runs and escalation

| Genre or play style | Lesson and SEALED application | Prerequisite and earliest candidate stage |
|---|---|---|
| G39 — Traditional roguelikes | Limited information and consumable tools make small choices consequential. Offer a separate expedition challenge with a known loss contract and recoverable campaign state. | Verified encounter variants, checkpoint policy and explicit information limits; M5. Permanent loss is opt-in. |
| G40 — Roguelites | Repeated attempts can teach and vary a useful skill. Revisit a trial with altered anchors or material availability while retaining discovered construction knowledge. | Parameterized templates, valid seeds and a bounded reward schedule; M5. Repeat runs should not be required to grind basic control competence. |
| G41 — Deckbuilders / card games | A limited set of options makes synergies legible. Present expedition plans as a small hand of known techniques, then equip the physical parts they require. | A planning interface with costs and compatibility; M3. Cards are representations; drawing one never conjures a tool or forces combat into random inputs. |
| G42 — Loot-focused action RPGs | Discoveries should suggest a new build. A recovered tendon has a useful length and elastic range that changes hauling possibilities. | Inspectable properties, compatible mounts and storage limits; M3. Prefer a few distinct functional finds over endless percentage upgrades. |
| G43 — Horde / survivor games | Escalating pressure tests whether a simple setup remains useful. An optional defense trial increases arrivals while the player manages barriers and exits. | Measured crowd/contact budget and readable failure cascades; M5. Crowd spectacle cannot precede the actor-count performance gate. |
| G44 — Idle / incremental games | Delegation feels good when a mastered chore becomes dependable. A bounded workshop job can process a declared batch while the player explores. | Conservative aggregate jobs, capacity bounds and resumable accounting; M5. No unbounded offline rewards, timers or simulated population growth. |

### Story, relationships and shared play

| Genre or play style | Lesson and SEALED application | Prerequisite and earliest candidate stage |
|---|---|---|
| G45 — Computer RPGs | Different approaches should express a character. Negotiate access, repair a route, take a risk or trade valuable supplies, with consequences the world remembers. | Authored dialogue conditions, saved commitments and outcome-based quests; M3. Dialogue may establish permission, never silently override broken physics. |
| G46 — Party-based / Japanese RPGs | Complementary roles and contrasting personalities make a journey memorable. A cautious carrier and curious scout can disagree through concise, authored behavior. | Bounded party, authored reactions and distinct useful capabilities; M5. Keep the first chapter centered on the existing companion. |
| G47 — Visual novels / relationship games | Small remembered choices create emotional continuity. A companion reacts differently to a place where it was rescued or to a familiar repair ritual. | A compact event-to-reaction system, authored variations and skip/replay controls; M4. Emotion needs coherent context rather than unlimited dialogue. |
| G48 — Emergent story / life sims | Players remember connected events better than arbitrary lore. An old brace enables a later rescue, and the journal names the shared history. | Stable identities, bounded consequential-event memory and causal links; M4. Record salient changes rather than every simulation tick. |
| G49 — Cozy / care games | Safety and stewardship can be satisfying ends. Offer restoration expeditions, gentle trials and a lair where useful care is free from attack. | Adjustable threat/pacing, predictable care outcomes and a welcoming feedback language; M4. Gentle mode retains the same declared material behavior. |
| G50 — Walking simulators / contemplative exploration | Place, sound and small discoveries can carry an expedition without combat. Follow a repaired route, notice who now uses it and revisit a companion's resting place. | Strong environmental composition and a few persistent authored details; M4. Every peaceful interval need not hide a collectible or impending attack. |
| G51 — Cooperative puzzle games | Complementary information and responsibility create cooperation. One player or capable NPC monitors strain while another positions a support. | First prove the interaction with the companion; M3. Networked roles, disconnect recovery and state authority are beyond M5 until separately qualified. |
| G52 — Party games / local challenges | Short, readable constraints invite playful experimentation. Run a cargo relay or build a support from a small shared kit, then compare approaches. | Scenario reset, accessible controls and a local result record; M5. A same-machine pass-the-controller trial is sufficient to test appeal. |
| G53 — Social deduction | Uncertainty about intent makes evidence valuable. A damaged shared store may reflect an accident, an unreliable witness or deliberate interference. | Authored suspects, evidence and fair alternative explanations; M5. Start as a single-player investigation, not an unbounded deception AI. |
| G54 — MMOs / shared worlds | Shared places gain meaning through visible contributions. Let repaired routes bear a local record of who or which faction maintained them. | Persistent attribution is M4; an online shared world is beyond M5. Server ownership, grief recovery, moderation and live operations are separate projects. |

### Mastery, vehicles and player expression

| Genre or play style | Lesson and SEALED application | Prerequisite and earliest candidate stage |
|---|---|---|
| G55 — Racing / rally | Reading a route and managing momentum can make the same course replayable. Deliver a fragile load quickly while choosing safe lines and braking points. | Qualified movement and cargo dynamics, clear checkpoints and a safe reset; M5. Score delivery condition as well as elapsed time. |
| G56 — Sports / team sports | A compact arena and comprehensible rules make physical mastery social. Move a weighted object through a gate while opponents contest support and space. | Contact/control qualification, referee predicates and bounded actors; M5. A cooperative hauling trial comes before competitive balance. |
| G57 — Vehicle / flight simulators | Instruments and failure management can make operation engaging. Build a terrestrial cart and manage its load before attempting gliding or powered flight. | Wheel/contact and drive qualification for a cart; aerodynamics/propulsion for flight; M5 or later. Ground physics alone does not establish lift. |
| G58 — Sailing / diving games | An unfamiliar medium changes familiar decisions. Trim a small salvage raft or isolate a flooded compartment during an underwater recovery. | Buoyancy, drag, fluid transport and any modeled respiration; M5 or later. Begin with a contained test basin. |
| G59 — Score attack / speedrunning | Clear conditions and immediate retries let players define mastery. Complete the rescue with intact cargo, minimal material use or an elegant support arrangement. | Independent success/score predicates and stable scenario versions; M4. Public competitive verification needs additional determinism and integrity work. |
| G60 — Creative / asynchronous community play | A good invention deserves reuse. Save a load-tested assembly, annotate its limits and challenge another player to improve it. | Local versioned blueprints and validation; M4. Sharing, content moderation and executable-code isolation need a later distribution design. |

### The combinations with the most promise

**Investigation + repair + role-playing:** discover why a crossing failed, choose
whom to believe, and repair the actual cause. The result changes a route and a
relationship. This makes scientific understanding useful to the story.

**Traversal + extraction + creature care:** the path inward is easy with an empty
frame; rescuing someone makes the return a different problem. The companion's
condition and the player's earlier supports determine what is possible.

**Stealth + construction + tactics:** prepare a quiet way through a threatened
space. A brace suppresses a contact-noise source, a counterweight holds a door,
and a release creates a retreat. The same kit also has obvious rescue uses.

**Management + automation + adventure:** discover a difficult route, build a
reliable hauling solution, then leave one bounded job running. Returning shows
what that investment produced and what still needs personal attention.

**Rhythm + sports + physical mastery:** synchronize two bounded pulls to move a
load cleanly. An optional timed challenge measures coordination after ordinary
play has taught the mechanism. A timing aid can make the same challenge accessible.

**Horror + companionship + recovery:** danger narrows perception; care restores
confidence. A companion's trustworthy warning, a prepared line and a familiar
safe alcove carry emotional weight because the player has used them before.

The same activity may support several moods. Let the player enjoy a quiet rescue,
an efficient delivery or a risky improvisation without requiring every activity
to award combat experience or feed a universal score.

## 10. Turn the library into encounters and a campaign

### A reusable encounter grammar

Author each problem-solving encounter as **an intention, a physical constraint, two viable
approaches, a readable commitment, a consequence and a recovery route**. Add an
optional complication only after the base problem works. An approach is viable
only when its geometry, resources and control demands have been checked. Quiet
observations and relationship callbacks can simply offer a meaningful moment;
they do not each need an engineered obstacle.

Mission success is a predicate on world state and an explicit social agreement
when one applies. “The target is safely supported inside the shelter” is useful;
“the player clicked the intended anchor” usually is not. Check sustained stability
for a declared interval where a single lucky frame could falsely complete the task.

| Encounter | Player experience and combined genres | Several approaches / consequences | First dependency and scope |
|---|---|---|---|
| E01 — Bring Them Home | Care, physics puzzle, extraction | Reinforce the crossing, travel in stages, or rig a haul; the return includes the rescued load | Existing M2 slice; retain its small required scope |
| E02 — The Quiet Crossing | Stealth, engineering, traversal | Brace a noisy joint, take a longer route, or time passage around observation; prepared supports remain useful on escape | Bounded sight/noise events; optional M3 variant |
| E03 — Who Broke the Span? | Investigation, RPG choices, repair | Compare traces, gently load-test an attachment, and ask witnesses; repair changes with the inferred cause | Stored condition evidence and authored explanations; M3 |
| E04 — The Rival's Reach | Fighting, hunting, creature care | Contest footing, lure the rival to wider ground, retreat, or help its damaged side; each ends the encounter differently | One qualified opponent with limited perception; M3 |
| E05 — The Borrowed Tendon | Construction, management, adventure | Repurpose the lair gate's tendon for a rescue, build another haul, or trade for supplies; an unsecured gate creates an explicit cost | Existing modular parts and authored consequences; M3 |
| E06 — Before the Counterweight Falls | Tactics, puzzle, suspense | Catch and brace a visible descending load, redirect it, or evacuate the threatened area; use its measured motion to communicate urgency | Qualified moving load, safe retreat and planning controls; M3 |
| E07 — Market Across the Ribs | Delivery, racing, economy | Carry a small valuable item quickly, move bulk stock carefully, or improve the route first; damaged cargo changes its value | Route and stock accounting; optional M5 expansion |
| E08 — The Breathing Shelter | Escape room, horror, cooperative repair | Diagnose a failed valve, isolate one chamber or restore a flow route while preserving an exit | Qualified gas/flow model before breath-related stakes; M5 |
| E09 — Hold the Nursery Route | Defense, tactics, stewardship | Divert arrivals, reinforce a barrier or relocate the vulnerable occupants; destroyed habitat is a persistent cost | Small bounded population and measured defense geometry; M5 |
| E10 — The Warden's Trial | Sports, auto-battler preparation, score attack | Compare two loadouts on the same route; improve time, resource use or cargo condition without a single mandatory scoring optimum | Versioned local scenario and independent metrics; M4 |
| E11 — A Workshop That Waits | Automation, crafting, cozy care | Leave a finite hauling batch, return to diagnose a jam or enjoy a cleared work area; manual operation remains available | Bounded job queues, sensors and work accounting; M5 |
| E12 — A Place Worth Returning To | Life sim, exploration, emergent story | Revisit a repaired route with new capability; see a remembered repair enable a different rescue or peaceful encounter | Persistent identities, authored callbacks and capped world changes; M4 |

These are an encounter bank. Choose a small coherent subset for the first chapter.
E01 is the only required first slice; developing a table row is not authorization
to implement the entire bank.

### Six build directions, all assembled from useful parts

| Build direction | What it makes easier | What it gives up | A reason to reconfigure |
|---|---|---|---|
| Rigger | Reach, remote hauling and improvised bridges | Bulky lines, anchor dependence and recoil risk | A narrow interior rewards a shorter, simpler kit |
| Carrier | Protecting cargo and supporting injured bodies | Mass, turning space and speed under load | A fragile crossing rewards splitting one load into trips |
| Scout | Route reading, early warnings and low encumbrance | Storage, sustained pull and heavy protection | A discovery must be carried home or a support must be built |
| Restorer | Diagnosis, compatible patches and temporary support | Material stock occupies carrying space | Emergency escape may require sacrificing supplies |
| Defender | Stable footing, shielding and controlled access | Reduced reach or agility; support depends on terrain | A vertical route makes static strength less useful |
| Mechanist | Reusable hoists, triggers and workshop jobs | Setup time, complexity and additional failure points | An urgent rescue rewards direct handling |

These are equipment and practice profiles, not classes that prohibit actions.
Early versions of the Rigger, Carrier and Restorer are enough for M3. Scout sensors,
Defender hardware and Mechanist controllers enter only when their dependencies do.
A novice can use a recommended assembly; an expert can alter it and inspect the
tradeoff. Keep useful simple assemblies competitive through reliability and ease.

Evaluate a promising component by **the new situation it lets a player solve**.
An upgrade that merely repeats the same answer at a larger number needs a stronger
reason to exist. Different materials may trade mass, compliance, durability and
repairability; no material should become best at every relevant property by fiat.

### First-chapter pacing: learn, commit, return, reinterpret

After the M2 slice succeeds, use the following as a proposed **45–60-minute chapter
test**, not a content-duration promise. Timing starts after launch and character setup.

| Approximate beat | What the player experiences | What the designer learns |
|---|---|---|
| First 3 minutes | A useful touch/pull and an immediately readable goal | Can the player act before understanding the full theory? |
| Minutes 3–15 | Bring Them Home, including a recoverable mistake | Are two approaches discoverable and the load consequences legible? |
| Minutes 15–25 | Return, repair, select one modification and notice a lasting change | Does care produce a felt improvement rather than a maintenance chore? |
| Minutes 25–40 | One new encounter using the same kit, such as E03 or E05 | Does the player transfer knowledge instead of waiting for another tutorial? |
| Minutes 40–50 | A return route becomes newly useful or newly difficult | Do earlier physical choices have understandable consequences? |
| Remaining time | Optional trial, peaceful exploration or an experiment | Is there voluntary curiosity after the objective is complete? |

Keep tension in a readable wave: curiosity, preparation, commitment, recovery,
reflection. Avoid overlapping a difficult manipulation, new camera behavior,
new opponent and unexplained material in the same first encounter. Later encounters
can combine familiar demands. Rest spaces should provide time to inspect a companion
without an invisible timer continuing to punish the player.

### Story and quests recognize physical outcomes

Use a small cast with distinct needs: a keeper needs a safe route, a salvager needs
intact stock, and the companion needs manageable loading. Their requests can conflict
without making one side cartoonishly wrong. Restoring a bridge may help both while
using material the lair also needs. Write consequences around that concrete choice.

Record commitments separately from facts. A Warden can promise delivery and fail;
the world can contain a working repair whose owner has not yet learned about it.
Give NPCs bounded knowledge and a way to update it. Reputation follows known events
and authored interpretation, not omniscient judgment of every player action.

Use a compact quest state machine: offered, accepted, in progress, resolved, abandoned
or changed by events. A destroyed route may change the request into an evacuation.
An unanticipated valid rescue still resolves it. Record why an outcome counted so
the player and developer can inspect it. Authored dialogue and local state are enough
for the first chapter; cloud or resident language models are optional authoring aids.

### Variation that preserves solvability

Begin with authored layouts, then vary a few meaningful parameters: load, anchor
availability, visible damage, material kit and an optional observer. Each template
declares ranges that have been exercised, a deterministic generation seed, a known
feasible baseline solution and recovery capacity. Reject a generated instance if its
baseline no longer meets support, reach, inventory or route constraints.

That baseline is a validation witness, not a prescribed player path. Allow stronger
solutions. Validate geometry clearance and control tolerance as well as abstract
connectivity; a mathematically connected route may still be unplayable. Preserve
failed seeds and the exact parameter set instead of silently rerolling during play.

For M4 replayability, prefer two authored variations and an optional mastery goal
over a general world generator. M5 can combine qualified templates with a declared
active-area budget. A pacing controller may offer a later complication or choose
an unvisited encounter; it must not secretly retune loaded materials, create
unaccounted resources or move a visible threat to correct the player's success.

### Rewards for several kinds of player

Support curiosity with an explanation and a new route; mastery with a cleaner
solution and optional records; creativity with a reusable assembly; attachment with
a remembered companion response; stewardship with a place that works better.
Use mission rewards where they are useful, but allow the improved world itself to
be a reward. Keep essential equipment obtainable through more than destructive play.

Offer separate optional goals for speed, intact cargo, resource economy and elegant
construction. Show their tradeoffs without collapsing them into one required grade.
A relaxed player can complete a rescue; an expert can revisit the same scenario to
master it. Player-selected challenge settings should be saved with any scored result.

## 11. Engineering shape: one engine, explicit boundaries

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

### Shared gameplay services that make genre combinations affordable

Keep the number of reusable services small. These are proposed boundaries for
implementation; the current engine does not gain them merely because they are listed.

| Shared service | Contract | Genre opportunities it supports | A failure case to test |
|---|---|---|---|
| Affordance queries | Given an actor, a target and available tools, expose meaningful candidate actions with known preconditions and uncertainty; respect perception limits | Exploration, puzzles, crafting, combat, accessibility | A preview leaks a hidden defect, labels an uninspected anchor definitely safe, or accepts an attachment known to be invalid |
| Action execution | Track requested, validated, executing, completed, cancelled or blocked states; revalidate after relevant changes and return a useful reason | Tactics, companion commands, construction, automation | The target is cut away between preview and commitment; the actor must not keep acting on a stale object |
| Consequential events | Use stable actor/object IDs, simulation time, cause and resulting state changes; record visibility/observers where needed | Quests, detection, mystery, relationships, journals | A witness learns an unseen event, or a quest counts one rescue twice |
| Objective evaluation | Evaluate declared predicates on admitted world state, with a stability interval if needed; publish completion once | Rescue, defense, sports, optional challenges | A falling body briefly crosses a goal volume and falsely counts as safely delivered |
| Assembly descriptions | Save parts, port compatibility, geometry, material requirements and tested load envelope; instantiate only with available matter and work | Builds, loot, construction, local blueprint sharing | Reloading a design duplicates inventory or imports unsupported component versions |
| Local forecast | Run a bounded disposable prediction from the actor's observed state and explicit assumptions; show uncertainty without writing into the live world | Tactical previews, build tests, instruction | A forecast leaks hidden state, advances the live clock or promises precision outside its qualified range |
| Scenario and result records | Pin starting state, content/solver versions, seed, settings and independent outcome metrics | Replay challenges, sports, generation tests, QA | A faster result is compared with a different load, assistance setting or material profile |

**Commands and cancellation:** a short plan might say hold, attach, take load,
release. Each step has a completion condition and a failure response. If a hold
becomes unsafe, the agent reports the problem and uses its declared fallback;
it must not freeze a falling body to preserve the plan. Cancellation stops a command
or releases an attachment according to its contract; existing momentum remains.

**Physics facts and narrative state:** a broken support remains broken regardless
of quest status. Dialogue may grant access, settle a debt or establish a promise.
It cannot restore containment or conjure a missing part. Conversely, a physically
successful rescue can count even if the player skipped the expected dialogue beat.

Forecasts distinguish observations from assumptions. Unknown internal damage cannot
become visible merely because a preview evaluates the engine's complete hidden state.
Give a conditional estimate, an uncertainty range or a request for inspection when
information is missing. Full-state developer diagnostics remain separate from the
player's tools.

**Event memory:** keep salient facts such as a rescue, a changed route, a repair
and a witnessed betrayal. Coalesce repetitive observations and give transient traces
explicit lifetimes. Bound per-agent memory, journal entries and retained checkpoints.
A detective scene may pin the few evidence items it needs until its resolution;
that does not justify keeping every contact event forever.

**Time control:** single-player tactical pause freezes all simulated dynamics,
resource transfers and world deadlines together while the player edits intentions.
Slow time changes wall-clock presentation/scheduling consistently while preserving
the qualified physical integration step. UI animations may continue; they do not
recharge a battery or advance a cure. Time control is an explicit setting, never
an accidental difference between a menu and the visible world.

**Distant activity:** use a qualified aggregate job only for a process whose active
couplings can be represented honestly. Record initial inventories, bounded inputs,
work, capacity, elapsed simulation time and outputs. Stop at a limit or an unresolved
event and reconcile before reactivating the area. A structure carrying a live load
cannot become an unrelated off-screen production counter. First release can simply
pause inactive jobs; offline production is optional future work.

**Blueprints and content:** distinguish an assembly recipe from a runtime save.
One describes what could be built; the other records a particular body's current
damage, motion and inventory. Load user-authored recipes as validated data with
part-count, topology and parameter bounds. Import does not execute arbitrary code.
Recheck a recipe when solver or material versions change, and show its compatibility.

These services should be exercised by real encounters. Add one when two admitted
uses need it or when it removes a demonstrated blocker; avoid building a general
framework for every row in the genre library before the rescue can be played.

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

## 12. Graphics and readability

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

### Difficulty, comfort and accessibility belong in the design

Offer remappable controls, hold/toggle alternatives, adjustable camera movement,
subtitles, distinct visual equivalents for important sounds, and readable text/icon
scaling. A player who cannot distinguish colors or hear a strain cue must still
have a way to inspect the relevant state. Reduce camera shake and flashing effects
without removing the physical information they were intended to convey.

Assists can stabilize the camera, make valid attachments easier to select, buffer a
command or provide a longer explanation. They still select admissible geometry and
bounded actions. Where an optional challenge depends on timing, offer a slower or
less timing-sensitive route and save the chosen settings with the result. The
single-player pause and slow-time contract is defined in §11.

Tune difficulty through the number of simultaneous demands, opponent information
and decision policy, available repair supplies, clarity of hints, encounter layout
and the severity of loss. If a mode changes physical inputs, declare that profile.
A gentle adventure should retain causal consistency and interesting choices.

Provide optional escalating hints: point to an observable clue, explain the relation,
then demonstrate a possible approach. Preserve room for a different valid solution.
Test the HUD-light experience and the assisted experience with unfamiliar players;
neither should require a developer to explain what the companion is doing.

## 13. Roadmap and release gates

| Milestone | Deliverable | Exit evidence | Defer until later |
|---|---|---|---|
| M0 — preserve the baseline | Pinned playable demo; existing camera/lighting and tendon behavior recoverable | Known build, scoped historical receipts, explicit current limitations | Repeating already completed camera work |
| M1 — a body that carries a consequence | A complete bounded force path, admitted compartment ownership, local sensing, and locomotion/support qualification | Passive drop, stall, support loss, sever and renderer-rate controls; measured scale/inertias | Parkour, multiple species, whole-body biological fidelity |
| M2 — Bring Them Home | The compact rescue slice with two solutions, failure/recovery and a repair that persists | Physical controls plus observed fresh-player sessions from §6 | Predators if they delay the basic rescue; growth and large zones |
| M3 — combinations | One opponent, reusable rigging parts, a working lair and one selected additional encounter using the same parts; a second only after useful transfer is demonstrated | Parts work outside their introductory puzzle; distinct viable solutions; bounded memory across repeated sessions | Broad crafting catalog, detailed metabolism; the rest of the genre library |
| M4 — one finished chapter | Reliable onboarding, save/recovery, presentation, accessibility/settings and a coherent expedition arc; test the pacing proposal in §10 | Declared hardware/fidelity envelope; offline install/start; user-confirmed game loop and meaningful return | Mandatory co-op or a promised campaign duration |
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

### Promote a genre idea by evidence, not enthusiasm alone

Before assigning implementation, make a one-page encounter packet inside the normal
work record: player intention, reused verbs/parts, one new decision, prerequisites,
smallest scene, baseline and alternative solutions, failure/recovery, resource budget,
and a physical falsifier paired with a player-observation question. It remains a
proposal until admitted through the applicable project workflow.

Use the following shortlist to turn the library into deliberate experiments:

| Priority | Candidate | Why it is worth testing | Promotion / stop condition |
|---|---|---|---|
| First | E03: diagnose a collapsed span | Reuses inspection, attachment condition and gentle pulling; gives engineering understanding a narrative purpose | Continue if players distinguish evidence from guesses and alter a repair; simplify if they merely follow a highlighted answer |
| First | A short courier variation of E01 | Reuses a proven route with a different load; tests whether carrying remains enjoyable on repeat | Continue if the load changes route or assembly choices; fix controls if repetition mostly repeats frustration |
| First | E05: repurpose the lair tendon | Gives one component two jobs and creates a persistent tradeoff | Continue if players anticipate what loses support; improve feedback if the resulting failure feels arbitrary |
| Next | E02: cross quietly | Adds a different mood with one observer and a small sensing model | Continue only if detection has a readable cause and two avoidance strategies; defer if it demands a full sound simulation |
| Next | E10: compare loadouts | Makes functional progression visible with a bounded repeatable trial | Continue if two configurations win on different metrics; revise if one dominates every tested condition |
| Later | E08, E09 and E11 | Add flow, population pressure and automation after their laws/services qualify | Admit each independently; do not expand all three because they share a setting |

Every prototype should answer two separate questions: **did the mechanism behave
as declared, and did it create the intended decision?** Keep input identities,
performance measurements and observed confusion with the result. A successful
simulation with no useful choice needs design work; an exciting scene with an
unaccounted force needs engineering work.

For each selected encounter, test a normal route, an alternative route, deliberate
misuse, an unexpected valid construction, loss of a key attachment and reload during
recovery. Also test the relevant perception boundary, bounded memory after repetition,
and at least one accessible control/cue configuration. Choose only the checks relevant
to its mechanisms; this is not an invitation to rerun the whole project each time.

Keep one playable milestone as the team's main target. The first chapter can ship
with a small set of excellent combinations. Genre ideas that need flight, fluid
respiration, extensive crowds, online infrastructure or new biological processes
stay in the library until both an engineering gate and a player need justify them.

## 14. Risk controls that preserve the game

| Risk | Early signal | Response |
|---|---|---|
| Physics produces activity but few interesting decisions | Players repeat one strongest action in every encounter | Change geometry, available supports and consequences; test another solution with existing parts |
| Interaction feels slow or fussy | Players struggle to attach, aim or understand a failure | Improve intent controls, previews, camera and feedback before adding laws |
| Locomotion consumes the whole project | Candidate controllers never pass power/support controls | Scope a short supported interaction slice; retain the full-body gate and investigate the failing mechanism |
| Permanent damage punishes experimentation | Players reload after every injury or abandon a companion | Provide reversible supports, repair choices and fair recovery; preserve history without permanent uselessness |
| More detail exceeds the hardware budget | Long frames or memory growth during topology changes | Bound active scope, measure transition costs, and qualify reduced states rather than hiding failures |
| Fiction outruns implementation | A label says breathing, healing or growth but only a pose changes | Implement the missing transfer/state or use a narrower description until it is qualified |
| Genre breadth dilutes the identity | New menus and isolated minigames replace useful physical interactions | Require a new decision, shared verbs and a tested encounter before promoting a library entry |
| Rewards collapse into one dominant build | Every useful objective favors the same part or stat | Compare tradeoffs across load, clearance, reliability and repair; keep multiple outcome metrics |
| Variation produces unfair scenarios | A random layout has no feasible return or hides a mandatory warning | Validate a baseline solution, preserve recovery resources and retain failed seeds for diagnosis |
| Infrastructure replaces game development | Workflows and catalogs grow while the rescue remains unplayable | Judge the next task by the player action it enables or the demonstrated blocker it removes |
| Multiplayer swallows the first release | Work begins on lockstep before saves and single-player recovery work | Ship the single-player contract first; choose replication after determinism and bandwidth tests |

The concept is successful when a player applies something learned in one context to
another, sees the expected consequence, and cares about the particular body or place
that consequence changed. Scientific checks establish the mechanism. Player observation
establishes whether using it is understandable and worth doing again.

## 15. Change and publication discipline

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
