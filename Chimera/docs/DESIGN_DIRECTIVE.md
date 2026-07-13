# CHIMERA — DESIGN DIRECTIVE: The Ship Must Fly First

> Owner's directive (verbatim intent): *"We've built a ship that flies good FIRST. How are we going to go into combat if the ship doesn't even fly?"*

**Design authority ruling (one line):** The "ship" is the astronaut's **body on the regolith**. Prove the body *flies* — walk, sense, survive — as a **continuous, felt, witnessed** experience; then wire the **one social verb** (gesture → offer → sacrifice → star) that makes the flying mean something. **Combat, economy, missions, ships, docking, quantum travel, and the whole deep-space-trader layer are DEFERRED** until that core is witnessed-good.

- Date: 2026-07-13 · Status: **ACTIVE** · Authority: Design (Architect mode)
- Supersedes ad-hoc engineering prioritization. This is the call engineering executes.
- Source of truth: `E:\PythonChimera\CHIMERA_VISION.py` (the seed / Design Laws) + `python -m core.helm targets` (~40% realized, heading GRADUATE) + a two-front C++ audit of `Source/Chimera/ProceduralGenerated/` (2026-07-13).

---

## 0. Reading of the seed (why this call)

The vision's own master `tick()` and its `_live_one_life()` proof define the core loop, in order: **move/look** → footsteps/dust/gait → **survive** O2/battery/dust/cold → **act** via verbs (chiefly the `GestureWheel`) → **meet needy strangers**, offer or refuse (the sacrifice engine) → **death → star → heir**. 

Three Design Laws bind the prioritization:
- **Law 1 — the world answers the body.** Every verb has physical, audible, visible consequence. No abstract clicks. (A verb with no world-state change is not a verb — see H-21.)
- **Law 2 — the bad ending is a costless life.** Meaning = what you gave up. Taught only through consequence, never words.
- **Law 3 — wordless.** The gesture wheel *is* the social interface.

**Combat is not ranked by the seed at all.** The vision's single deepest narrative beat is `WEAPON_NEVER_FIRED` counted as a *sacrifice* — the seed valorizes **not** fighting. Combat is one verb among twelve, and the least load-bearing one. This is decisive for what we defer.

---

## 1. THE CORE THAT MUST FLY FIRST

The core has two layers. The **BODY** is the literal "ship" — it must fly first because you cannot judge feel without it and everything else stands on it. The **GESTURE** is the reason to fly — without it we have proven the *engine*, not the *game*.

### The first five minutes (the experience we are building toward)
1. You wake as an astronaut on a regolith plain. Earth and Moon hang in the sky; Earth is your north. You hear your own breath and the suit servo. (**presence**)
2. You **walk**. Sand crunches, dust kicks up under each boot, footprints trail behind you. Metal pad, rock, and sand basin each sound and feel different. You **sprint** — breath quickens, the view widens, O2 burns faster. You **bend** to glance at the O2 gauge on your wrist. (**move + sense**)
3. Your air and battery are draining. You feel the clock. You must reach the habitat to refill before you suffocate; dust clogging your suit is slowing you; night is cold and the battery matters. (**survive — a real decision, not a cosmetic bar**)
4. A **dot on the horizon** resolves into a stranger. Their suit is hissing — they need oxygen. You **hold TAB**; the gesture wheel blooms; you **offer** your oxygen can — or you **refuse**. They could not pay. You gave anyway. Nothing rewards you. That was the point. (**act + meaning, in one gesture**)

### Bill of materials for the core (with honest current status)
| System | Pillar | Needed for the 5 min | Status today |
|---|---|---|---|
| Pawn locomotion: walk/jog/sprint/bend/jump, low-g | Move | Yes | WIRED (BP + native CharacterMovement) |
| Footsteps + sand sound, dust puffs, footprints | Sense | Yes | WIRED but sand telemetry returns hardcoded defaults (live bug) |
| Wind / weather / ambient suit sound | Presence | Yes | Partially wired |
| Diegetic O2/battery/dust readout (wrist gauge) | Sense | Yes | Only console debug text; `WID_O2HUD` exists but is never created |
| Suit survival loop: O2/battery/dust/cold + refill | Survive | Yes | Component WIRED + ticking; threat/refill curve unproven in play |
| **One world verb wired to input with a world consequence** | Act | Yes | **The gesture wheel is ABSENT; 6 verbs have zero input binding** |
| **Stranger with a need + offer/refuse → runtime sacrifice log** | Act + Meaning | Yes | **ABSENT at runtime (log fed only from unit tests)** |
| Death → star → will → heir wakes at habitat | Meaning | For the loop to close | GenerationSubsystem ABSENT; star/log/ending are an unwired shelf |

**What the core is NOT:** combat, weapons, shields, economy, commodity pricing, missions, factions, ship subsystems, docking, quantum travel, the Titan Run, the space-body universe, Attunement, the full Mass crowd, or multiplayer. None of those are in the first five minutes.

---

## 2. HONEST ASSESSMENT

**Is the core realized and coherent? Partly for the body; not at all for the game.**

- **The SURVIVAL/MOVEMENT pillar genuinely exists in-engine and is wired.** `ADeepSpaceTraderGameMode` → `ADemoPlayerController::OnPossess` spawns/possesses the astronaut Blueprint and runtime-attaches camera, footprints, `UChimeraMovementComponent` (telemetry only — it does **not** drive locomotion; native CharacterMovement does), and `USuitLifeSupportComponent` (ticking, draining O2/battery/dust). A 2026-07-13 sim run proved W-hold moved the pawn ~626 uu/s and Space raised Z — real move + jump end-to-end.

- **"Zero PIE playtests" is not literally true — but the spirit is.** Scaffolded sleepwalker sim sessions have run through the real input bridge, with screenshots. But they **teleport the pawn between beats** (not continuous free play), several **fail** (`walk_rock_to_sand_basin` failed on missing SandDrift_FX; `crouch_beat_verify` = 5 failed / 4 reached), mouse-look is flagged **"unproven,"** one run honestly records **telemetry returning hardcoded defaults**, and some evidence stamps look **templated** (identical `fps:119.999`, identical `passed:8/8`). **Conclusion: there is no trustworthy witnessed continuous free-play of the body, and zero witnessed play of the acting or narrative pillars.** The existing evidence should be distrusted until re-proven.

- **The ACTING pillar barely exists.** The only wired verbs are movement + pickup/drop (E/Q). Input is **legacy `BindAxis/BindAction`**, not the Enhanced Input the seed specifies (the `IMC_Default`/`IA_*` assets are orphaned template leftovers). **Six advertised verbs — Dig, Scan, DrawWeapon, Fire, GestureWheel (hold-TAB), AttuneDial — have no input binding at all.** The `ATool_Shovel/Scanner/Weapon` actors carry real logic but are **never spawned and never bound**. The gesture wheel — the seed's "entire social interface" — **does not exist in any form** (TAB currently maps to a leftover vehicle "SwitchCamera").

- **The NARRATIVE spine is a shelf of unwired parts.** `SacrificeLogComponent`, `StarMemorialComponent`, and `CostlessLifeEndingDiagnostic` compile with real math and pass unit tests, but are fed **only from tests** — no gameplay event records a sacrifice, no death writes a star. There is **no `GenerationSubsystem`, no heir/rebirth** (only a placeholder `FInheritanceState` struct). Design Law 2 lives in headers and tests, not in play.

- **Combat's "verified bugs" (shields bypassed, hull not clamped) are real but irrelevant to the core.** They sit inside a system the first five minutes never touch and the seed never ranks.

**Bottom line:** the body is ~80% of the way to flying (needs a witnessed continuous session + two sensory fixes + a real gauge + a real threat curve). The *game* — the single gesture that carries the meaning — is at zero. A beautifully-walking astronaut with nothing to do and no cost to bear is a tech demo, not Chimera.

---

## 3. PRIORITY ORDER (ranked by "does it make the ship fly")

**P0 — PROVE THE BODY FLIES (the gate; days, not weeks).** One *continuous* witnessed PIE session: spawn → walk metal→rock→sand → sprint → bend to read the gauge → let O2 fall → refill at the habitat → survive into night. As part of this: (a) fix `SandSoundComponent` hardcoded-default telemetry; (b) prove mouse-look; (c) replace the console debug O2 with the real diegetic gauge — wire `CreateWidget` for `WID_O2HUD` and author its UMG asset. *Why first:* you cannot make design judgments about feel blind, and the current witnessed evidence is scaffolded and partly templated. Nearly free; unblocks all judgment.

**P1 — MAKE SURVIVAL A REAL DECISION.** Tune the O2/battery/dust drain, the refill source, and the night-cold threat so a 5-minute session contains a genuine "will I make it back?" beat. Witness one death and one successful refill. *Why:* this is the "flies GOOD" of the survival pillar — the tension that makes walking matter. Depends on P0.

**P2 — WIRE THE ONE VERB THAT MAKES IT A GAME.** Build `UGestureWheel` (hold-TAB radial, real UMG + input binding) + a **single scripted stranger** (`AActor` with a need enum — no Mass/ADotCharacter needed yet) + wire `OnGesture` → `SacrificeLogComponent::RecordProtectionAtCost` at runtime. Offering to one who cannot pay must silently log a sacrifice with a visible world consequence (Law 1). *Why:* the biggest hole and the highest meaning-per-unit-effort; it converts a walking-sim into Chimera. Depends on P0.

**P3 — CLOSE THE GENERATION LOOP.** On death: write the star from the sacrifice log (`StarMemorialComponent::AddLife`), invoke `CostlessLifeEndingDiagnostic` (dim star + empty mirror for a costless life), show a wordless will screen, respawn the heir at the habitat with halved credits. A minimal `GenerationSubsystem` (currently absent). *Why:* makes Laws 2 and 4 legible and finishes the loop; small once P2 feeds the log. Depends on P2.

**P4 — DEEPEN PRESENCE.** Footprint persistence and the weekly storm that erases it (Law 4), Earth/Moon sky landmarks + compass rim, night light from ancestor stars. *Why:* sells "alone on a planet." Opportunistic; do it as the sensory world gets witnessed.

### DEFER — explicitly, and by name
- **COMBAT** — ship weapons/shields/hull-clamp bugs, the `DrawWeapon`/`Fire` verbs. The seed does not rank combat and its moral spine is `WEAPON_NEVER_FIRED`. **Do not spend one hour on shield-bypass while the gesture wheel does not exist.**
- **The deep-space-trader layer** — economy, commodity pricing, missions, factions, ship subsystems, docking, quantum travel. Secondary by the seed's own words.
- **Attunement minigame + the Erisaid mirror** (`MIRROR_KEEPER` ending). A beautiful second-order verb — after the core flies.
- **Full Mass crowd + `ADotCharacter` LOD actorization.** A single scripted stranger proves the loop; Mass scaling is a later optimization.
- **Titan Run, the space-body universe, networking/replication, multiplayer.**
- **Enhanced Input migration.** Legacy input works. Align to the seed opportunistically when you build the gesture verb — not as its own project.

> Engineering note: the gesture wheel and stranger are **new loop-built files** (safe to author by hand). Do **not** hand-edit generator-owned files (GameMode, Economy, Combat, Missions, Save templates…); fix the generator template instead. Migrate substantial loop-built systems under generator ownership per project convention.

---

## 4. THE BAR — what "flies GOOD" means (so it is judgeable, not vibes)

Judge all of the following in **one continuous witnessed PIE session**, telemetry captured **foregrounded**.

**FEEL (locomotion).**
- Low-gravity weight is legible: jump hang-time clearly longer than Earth, a soft landing settle. Walk / jog / sprint / bend are visually distinct via camera (sprint FOV ~92→101 + bob; bend drops the head ~0.55 m).
- Every footstep produces **synchronized** sound + dust puff + a persistent footprint; sound scales with speed and differs by surface (metal / rock / sand); audio↔visual sync **< 100 ms**; telemetry comes from real components (no `count=0` / `latency=999` defaults).
- Mouse-look is smooth and **proven** (today it is flagged "unproven").

**FEEDBACK (survival).**
- O2 / battery / dust are readable **diegetically** — a wrist gauge you glance down to, not console text; the needle animates; a low-O2 warning fires.
- A **real decision** inside five minutes: O2 forces a return to habitat or cache; refill works; running out kills; night + dead battery kills by cold. The threat is real, not cosmetic.

**PRESENCE (the sensory world).**
- Standing still, the world is alive: wind-driven dust, a weather shift, Earth + Moon as sky landmarks, ambient suit sound. It reads as **alone on a planet**, not a greybox.

**MEANING (the game, not the tech demo).**
- Hold TAB → a radial gesture wheel blooms → you select and commit a gesture → it produces a **world consequence** (Law 1 — no abstract clicks).
- You meet **at least one** stranger with a visible need and **offer or refuse**. Giving to one who cannot pay **silently** logs a sacrifice; at death it becomes a brighter star; a costless life yields a dim star and an empty mirror. Never explained in words (Law 3); taught by consequence (Law 2).

**THE SINGLE PROXY (would a human enjoy it).** A first-time player, given no text, within five minutes: (a) understands they are a **fragile astronaut who must manage air**; (b) **feels the world answer their body**; (c) faces **one costed choice** to help a stranger — and remembers it. If a witnessed session cannot produce (a) + (b) + (c), **the ship is not yet flying**, and no downstream system may be funded.

---

## 5. Handoff

Execute **P0 first** in Code / UE5 mode. P0 is a proof + three small fixes, not a build-out — it is the gate that tells us whether the body actually flies. Do not open combat, economy, or missions work until Section 4's bar is met for the body (P0–P1) and the single gesture (P2). Re-read this directive at each priority boundary.
