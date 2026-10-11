# SEALED — an action RPG built on provable matter

Working title: **SEALED** (alternates: *Tension*, *The Sump*, *Vivarium*).
Author: Qwen (planner). Date: 2026-10-11.
Status: ACTIVE — §10 DECIDED 2026-10-11 by the user: Option B, grow
the current engine. No external engine host (Godot and Unreal rejected).
This plan is the bridge from the verified demo (commit e70a7fe5, live at
http://127.0.0.1:8210) to a shippable game. Every mechanic below is either
already implemented and verified in this repo, or is a stated extension of
a law we already own. Nothing here invents a system we have no physics for.

---

## 1. The pitch in three sentences

You are a Warden bonded to a living creature on a sealed, pressure-born
moon — and everything in that world, you, your creature, every predator,
every wall, obeys one substrate: stored energy, tension, and topology.
There are no hit points, no stats, no cooldowns — only energy ledgers that
never lie, tendons you can feel and cut, and cells that heal or burst.
Where Star Citizen is wide, SEALED is deep: one honest physics book under
every object, so the stories it generates are *true*, not scripted.

The player-facing promise for the Star Citizen audience: *your thing is
real and it remembers.* A torn knee tendon is a torn knee tendon — your
creature limps until you feed it, rest it, and let it scar. That single
property, applied to combat, traversal, crafting, building and story, is
the whole game.

## 2. Design pillars (each one is already a law we own)

1. **Energy is the only currency.** Battery, food, money, health, XP are
   the same number in different books. (A1 ledger — implemented, verified
   to 3e-12 J in tendon_drive.hpp.)
2. **Damage is topology, not subtraction.** Nothing loses HP. Cells
   rupture, tendons sever, seals re-form. Disabled, not depleted.
   (Rupture + sever — both implemented and playable in the demo.)
3. **The body is a build.** You don't level up; you accumulate energy
   until a phase change becomes possible, and then your body or structure
   literally grows. (Build order #2 from THE_MEMBRANE_INVENTORY.md.)
4. **The ledger is the art.** Energy flow is visible inside every body —
   light under skin, glow through walls. Readability is not a UI layer;
   it is the rendering style. (Our readouts become subsurface glow.)
5. **No fake objects.** If the UI says it, the simulation did it. The
   graph store keeps every claim provable and replayable.

## 3. What we already have (verified, committed)

| Asset | State | Becomes in the game |
|---|---|---|
| MembraneTick sealed-cell pressure sim | live, verified | every body and structure's "health" |
| Tendon drive: muscle A7, tendon A8, capsule A5, battery, ledger | live, 5/5 falsifiers | locomotion, combat verbs, exhaustion |
| Sever (tendon cut → limb limp) | live, playable | the core combat finisher |
| Rupture (cell burst → topology change) | live | damage, death, terrain destruction |
| Touch/pressure at vertices, gravity | live | interaction, world weight |
| LBS binding + rig factory (18 459 verts, 28 joints, referee ROM) | live, pinned | any creature species we rig |
| Graph store (provable state, sha-pinned assets) | live | the save system / world memory |
| 12-lesson arc with verdicts, hints, progress | live | the prologue tutorial (reskinned) |
| Evidence-driven build discipline (falsifier per feature) | culture | keeps the sim honest forever |

The 12 lessons are not thrown away: they become the Warden's training
prologue, copy rewritten in-world. "FEEL THE MUSCLE" is already the best
tutorial the game has — it just needs fur.

## 4. The world and the fiction

**The Sump** — a shattered, tidally-locked moon where life never invented
bones. Every organism is sealed pressure: cells → organs → limbs, exactly
the membrane model the engine runs. The Warden (player) is bonded to a
creature — first species: the monkey we already rig — through a shared
energy network: feeding it charges it; it carries you; its ledger is
partly yours.

Three zones, hand-authored, deep rather than wide (anti-SC stance):
- **The Fringe** — grazing flats, tutorial, light predators.
- **The Ribs** — vertical canyon country; traversal is body-gated (you
  grow the tendons that let you climb, then the world re-reads you).
- **The Deep Sump** — late game: huge slow fauna, ruin-structures of a
  dead precursor seal-civilization, the story's energy mystery.

## 5. The core loop

Minute-to-minute:
**Move** on real muscles (sprint drains the shared battery; overexertion
heats; strain accumulates) → **Feed/hunt** to capture energy → **Fight or
flee** using disable-combat → **Cache energy** before dark.

Session loop:
Return to the lair → **deposit energy** → the lair *grows a room* (phase
change, not a menu) → tend wounds, feed the creature specific muscle
groups → tomorrow's body is yesterday's diet.

Long loop:
Accumulate → grow → new capability (climb, swim, carry, sever harder) →
deeper zone → bigger prey → bigger structures → the Sump's story unlocks
as *ecology*, not cutscenes: you learn the world because its energy flows
are real and learnable.

## 6. Combat: disable, don't deplete

Combat is wrestling with the ledger. Every attack is a real impulse on a
real body; every injury is one of the two verbs we already ship:

- **Strike** — impulse → pressure spike → cells rupture where it lands.
  A ruptured leg-cell leaks pressure; the limb sags.
- **Sever** — a called shot (grapple, hold, pull past ROM) cuts a tendon.
  The limb goes limp *forever until healed*. This is the demo's falsifier
  as a finisher, and it works on you too — which is why combat is tense.
- **Grapple/choke** — potential difference → flux: pin an enemy's cell
  pressure and it suffocates on its own gradient.
- **Armor/structures** — walls are big slow cells; sieges are pressure
  engineering.

Enemies obey the identical laws (same kernel, no NPC stat sheet). Fun
check for Phase 1: one predator, one ravine — does a 90-second chase where
you can *choose* to maim it or flee it make you whoop? If not, fix combat
before building anything else.

## 7. Building: energy accumulates, structures appear

The user's founding requirement, made literal: you carry metabolic energy;
depositing it past a threshold triggers a phase change — a new sealed room
grows out of the lair wall, pressurized, alive. Structures are bodies:
- **Stores** — dormant cells that hold energy (your bank; raidable).
- **Nurseries** — heal cells faster (re-seal rate up).
- **Forges** — grow tendon-tools: reach extenders, cutting spurs (sever at
  range), spring shanks (jump).
- **The Bond Well** — deep-late: expand the shared ledger; your creature's
  battery becomes a grid you can spend remotely.

No blueprints, no tech tree UI. Growth order is gated by accumulated
energy and by what your body can carry — the inventory's build order is
literally the progression system.

## 8. Progression, death, and persistence

- **No XP.** Capability = stored energy + grown structures + scars.
- **Scars persist.** A healed torn tendon regrows weaker or stiffer
  (parameters change, permanently, in the save graph). Two players'
  creatures diverge by lived history.
- **Death is a setback, not a reset.** Creature death = catastrophic
  re-seal: you wake at the lair, the body is rebuilt from stored energy
  (costly), and the scars of the death remain. Permadeath off by default,
  on as a mode for the SC-hardcore crowd.
- **Save = ledger snapshot.** The graph store already pins state by
  sha256; a save is a provable world state, replayable — which gives us
  free anti-cheat, free spectate/replay, and free speedrun verification.

## 9. Graphics direction ("way more detailed" done honestly)

Art direction: **the ledger is visible.** Subsurface glow shows charge;
skin transmits pressure color (taut blue → flaccid grey); severed tendons
go dark; structures breathe on a pressure clock. This is a *rendering of
simulation state*, so detail and truth never diverge — the tech demo of
that look is the real pitch video.

Hard truth, stated plainly: the current engine's renderer is a dev window,
not a game renderer, and "advanced graphics" is the single largest cost
item in this plan. The physics kernel is the crown jewel and must stay
headless, deterministic, and ledger-checked; the renderer should be
replaceable. The decision on the host is recorded in §10.

## 10. THE DECISION — RECORDED 2026-10-11: Option B (grow the current engine)

- **Option A — Godot 4 host (recommended).** Keep ChimeraEngine as a C++
  middleware kernel (GDExtension); Godot gives PBR, shadows, animation,
  UI, input, shipping, and moddability now. Fastest path to "looks like a
  game"; kernel stays provable. Cost: a bridge layer + porting input/camera
  out of the engine loop.
- **Option B — grow the current engine.** Full control, no bridge tax, but
  we hand-write what Godot gives free (shadows, post, assets pipeline,
  packaging). Realistically the slowest path to good-looking.
- **Option C — Unreal 5.** Best out-of-box visuals; worst fit: licensing
  friction against an open deterministic kernel, and the kernel becomes a
  plugin guest in someone else's house.

**DECIDED: Option B.** The user rejected external engine hosts on
2026-10-11. ChimeraEngine stays the whole stack — kernel, game layer and
renderer in one process, no bridge seam. Consequences: the graphics track
becomes in-engine renderer work (lighting, shadows, materials, then the
ledger-glow look), sequenced by visual payoff; every renderer system reads
simulation state directly, which makes the §9 art direction easier, not
harder. Options A and C above are kept as the rejected-alternatives record.

## 11. Architecture (target shape)

```
[ ChimeraEngine — one process, one build ]
   kernel (headless core): membrane cells · tendon drives · rupture/sever
   · ledger invariants · fixed 300 Hz internal step · graph-logged state
   game layer: camera · input · AI (decides u-commands, never forces) · UI
   renderer: in-engine upgrades — lighting → shadows → materials → glow
   content: rig factory (species) · authored zone graphs · lesson copy
        |
   graph store (save/memory/pins)
```

The AI rule is load-bearing: NPCs issue *effort commands* (u in 0..1) to
the same drives the player uses — no NPC can be stronger than its body,
and difficulty is literally feeding or starving the opponents.

## 12. Roadmap — each phase ends playable and fun-checked

- **Phase 0 — DONE.** Demo: body, lessons, tendon drive, sever, restart.
  (e70a7fe5; visible-browser verified; published to origin
   WK-SEAL-ENERGY-20261011 2026-10-11.)
- **Phase 1 — "The Bond" (first build target).** Third-person camera on
  the monkey in the existing engine; in-engine renderer pass 1 (lighting +
  materials on the pinned mesh); tendon-drive *locomotion controller*
  (a policy that turns u-commands into real run/jump — the one genuine R&D
  risk, budgeted first); one ravine; one predator; disable-combat v1
  (strike→rupture, grapple→sever); feed/charge loop. Fun gate: the chase
  whoop test (§6).
- **Phase 2 — "The Lair".** Energy deposit → grown structures; night
  pressure; wound care; two species (rig factory earns its keep). Fun
  gate: the lair grew because *I* played well — and it is on screen.
- **Phase 3 — "The Ribs".** Body-gated traversal; scars/persistence;
  sever-mastery combat; death-as-setback. Fun gate: a 2-hour session with
  zero UI prompts and one story a player retells.
- **Phase 4 — "The Chorus."** NPC wardens with the same laws; territory
  and energy-economy conflicts; co-op on the shared ledger (one kernel,
  lockstep + graph log — provable multiplayer). Ship.

Graphics track runs parallel from Phase 1, in-engine: lighting pass →
shadow maps → PBR-ish materials → the glow-through-skin ledger look as the
first real art milestone.

## 13. Risks, honestly

1. **Scope.** Star Citizen spent ~$700M on breadth. We compete on depth
   per square meter: one moon valley, one bond, one physics book. This
   plan is a 10–20 hour handcrafted game, not a metaverse.
2. **Locomotion R&D.** Kinematic pose + tendon drives do not run by
   themselves; a controller (CPG-style or optimization-based, deterministic)
   is Phase 1's real work. Mitigation: start with walk/lope, not parkour.
3. **Sim cost.** Deterministic CPU physics bounds creature count: hero
   creature + a handful of live bodies; herds LOD down to scripted until
   you touch them. The ledger stays honest at the LOD seam.
4. **Content pipeline.** Rig factory already generalizes rigs (referee
   ROM, terminal-segment law) — species count scales with art time, not
   code time. Art is the new bottleneck; plan for an artist hire/asset buy
   at Phase 2.
5. **In-engine renderer cost.** Shadow maps, material pipeline and asset
   tooling are hand-written work a commercial editor gives free.
   Mitigation: renderer upgrades are phased by visual payoff, each one
   reads simulation state directly, and the kernel's ledger invariants
   never depend on renderer changes.

## 14. What "fun" means here (the acceptance test for every feature)

A feature ships when a stranger, unprompted, does something the sim didn't
script and the world *answers truthfully*: they kick a wall and it stays
dented; they maim a predator and it hunts slower forever; their creature
refuses a cliff because yesterday's diet didn't grow the tendon. Lessons
taught the physics; the game must make the physics *personal*.

## 15. Version control discipline (push consistently)

Work is not protected until it is committed AND pushed. This repo has
already lost uncommitted work once (the 273-line incident).

1. **One scoped commit per verified milestone.** A milestone is real when
   its evidence is reviewed (falsifier passes, gameplay verified). Stage
   explicit paths only — the tree is shared with other agents; never
   `git add -A`, never commit files outside the milestone's scope.
2. **Push every reviewed commit to the configured remote (origin) on the
   working branch, immediately after review.** Local-only commits do not
   count as protected work.
3. **Phase gates are push points.** A phase is not done until its commits
   are on the remote.
4. **No force-push, no history rewrites, no pushing other branches or
   tags.** If a push fails (auth, non-fast-forward), STOP and report —
   rebasing our own scoped commits onto the remote branch is allowed;
   rebasing or touching others' commits is not.
5. **Evidence travels with code.** Each milestone commit includes its
   evidence files (reports, probe JSONs, screenshots under 5 MB) so the
   remote is the audit trail.
6. **Diverged remote branch: publish, then integrate.** If the working
   branch has diverged on the remote, push our scoped commits to a new
   branch (WK-<milestone>-<date>) and open a PR. Never rebase, merge or
   stash in the shared working tree — it holds other agents' uncommitted
   work (the 273-line incident). Integration happens in a separate
   `git worktree`, never in the live checkout.

---
Phase 1 assignment 1 (per the §10 decision): third-person camera on the
creature in the existing engine, keyboard-driven tendon already live,
ledger invariant asserted every frame — then renderer pass 1 (lighting +
materials on the pinned mesh).
