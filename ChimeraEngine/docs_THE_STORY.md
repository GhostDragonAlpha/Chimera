# THE STORY — the seed, the true root (the outermost membrane)

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
>
> **[docs/THE_LAW.md](../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 25 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **SECURED 2026-07-24** — the operator ratified it ("Exactly perfect"). This is the **timeline**:
> the outermost membrane, the **seed** that comes *before* `theSolarSystem` (before what the workflow
> called "the root"). Every build begins here. It is a **DECIDE** artifact — the human's vision — and
> it lives at THE HUMAN terminal. Hub: [`THE_WORKFLOW.md`](THE_WORKFLOW.md) §2b.
>
> **TWO MEASURES (the operator's completing insight).** The written story is the **cheap, up-front
> proxy** — the human reads it and can say *"no, I want this instead"* before a line of the game is
> built. But the **TRUE measure** of a story is the human **seeing it unfold as the game is played
> and tested** — because *meaning is experienced, not described.* (The movie you didn't want to go to
> and loved anyway: the pitch cannot be trusted over the experience, and the experience can win you
> over.) So this text is **provisionally secured on the page**; it is **truly secured only when
> witnessed in play.** That final ratification is a visual **WITNESS**, not a read — the human's
> meaning-terminal discharged the same way physics discharges its own: by *seeing it run.*

---

## The story

### I. The Seed *(before you)*

In the beginning there is a seed. Not a world — a number. A handful of coordinates and a short list
of laws, and nothing else.

From the seed, sand falls and finds its angle — forty degrees, always, never told to. Gas cools until
it can no longer hold itself up and collapses inward until it catches fire, and that is a star. The
dust that was going nowhere in particular finds orbits, and the orbits find Kepler's law without ever
being handed it. Embryos thicken into planets. Planets cool. Oceans condense where the warmth allows
and freeze where it doesn't, and somewhere between the burning and the ice a band appears that no hand
placed — a habitable zone, arrived at rather than drawn.

All of this happens whether or not anyone is watching. It has happened the same way every time it has
ever been run, and it will happen the same way forever, because the seed is the same and the laws are
the same. This is the first thing the game tells you, though it never says it aloud:

**this universe is true. You cannot break it, and it cannot lie to you.**

### II. Arrival *(you, at the outer membrane)*

Then you arrive — a cold start in a small ship, the long dark between worlds pressing on the glass.

You reach for the only thing you have: **thrust.** And the universe answers you honestly, because it
answers everything honestly — the heavier the thing, the slower it yields; go fast enough, close
enough, and time itself begins to lean. You learn to fly not by reading numbers off a panel but by
feeling the mass of things, the way you'd learn to carry something heavy up a stair. The solar system
is the first room you stand in, and it is enormous, and it is the largest bubble you will ever be
inside.

### III. Descent *(through the scales)*

You choose a world and you fall toward it.

Orbit becomes atmosphere becomes weather becomes ground becomes the single grain of sand beneath your
boot — and here is the secret the universe has been keeping the whole time: **the law that shaped the
star is the law that shapes the sand.** Go small enough and the world speeds up. Go large enough and
it slows. Spin anything past the edge of light and it tears open a hole you cannot see into — for the
very same reason you cannot see into an atom. It is turtles all the way down, but every turtle is the
same turtle.

You stand on ground that is *actually there*. You **dig** into it. You **scan** it, and it tells you
the truth about what it's made of, because it has no other option.

### IV. The Garden *(Eden, and the Tree)*

And then, on one world, you find a garden.

It is lush the way a real forest is lush — not painted green, but green because water and warmth and
light fell on grown soil and life cascaded out of them, the way the star cascaded out of the gas. You
plant a seed and you **grow** it, and a forest that no one authored rises out of physics doing what
physics does. At the center of the garden stands a Tree.

The Tree is the turn of the whole story. Because up to this point the universe has given you *facts*,
and facts have been enough — enough to build a ship, cross a system, raise a forest. But facts cannot
tell you what any of it is *for*.

### V. The Gift *(meaning — your terminal)*

The Tree of Knowledge does not give you power. It gives you the one thing the universe keeps from
itself: the knowledge of good and evil — which is only another way of saying *the weight, and the
gift, of deciding what things mean.*

The universe can prove that Eden **exists**. It cannot decide that Eden is **paradise**. That word was
always yours to say. And it is not a word you say once — meaning sits on the timeline and changes with
every moment along it, so you will say it, and unsay it, and mean something new by it, for as long as
you're there.

### Coda

Same seed, same world, forever. You can close it and it keeps turning without you; come back and every
grain is where you left it. The game is not *won* — it is *understood*, and understanding is not a
place you arrive at but a thing you keep deciding.

You are a visitor in a true creation, and a creator within it. The only thing you carry out is the
meaning you made.

---

## The story is true (every beat is a built or measured system)

The story is not lore laid *over* the game — it is the game's own physics, told forward in time. That
is what makes it a timeline and not a fantasy.

| Beat | The real system |
|---|---|
| the seed → sand → star → planets → habitable zone | the compositional ladder: `bigbang`, `planet`; 40.03° repose, Kepler slope 1.50, the zone *emerged* |
| thrust, and time beginning to lean | the density clock (`thrust`, `core/membranes.py`) |
| descent through scales; the hole you can't see into | the membrane onion + `tears()` (black hole from the clock's light-ceiling) |
| ground that is actually there; dig; scan | matter-under-boots (contact-witnessed); the `dig`/`scan` verbs |
| the grown garden and the Tree | `eden` / `prove_eden` (Eden exists, reproducibly) |
| "proves it exists, cannot decide it's paradise" | the PHYSICS vs THE HUMAN split — the method sealed 2026-07-24 |

---

## How it fits the workflow

`theStory` is the **true root** — the seed, the outermost membrane. `theSolarSystem` is the first
thing *grown from it*, and everything else is grown from there, down the hierarchy, one `camelCase`
term at a time. We prove **down** from the seed; and the whole, once built, is **truly measured** the
only way meaning can be — by the human **watching it unfold.** Written here so the timeline is secured
before we prove `theSolarSystem` inside it.

---

## The decomposition — the terms this story declares

> This story, decomposed into the game: the terms to PROVE, in story order. It is the **single
> source** — `ChimeraEngine/gen_decl.py` parses this block into the engine's declaration
> (`terms_data.py` → `_DECL`), from which the hierarchy and `ChimeraEngine/THE_TERMS.md` both derive.
> Indentation is parent nesting; each line is `name [P|H] note` (`[P]` physics, measured · `[H]` the
> human, decided). **Change the story here, re-run `gen_decl.py`, and the whole game re-derives.**

```chimera-terms
theStory [H] the seed / the timeline
  theSeed [P] the number + the laws that unfold the world
    theDeterminism [P] same seed -> same world, bit-identical
    theLaws [P] the trained physics the seed runs under
    theTruth [P] every fact reaches physics; the world cannot lie
  theSolarSystem [P] the setting you fly
    theStar [P] the yellow hearth
    thePlanets [P] the worlds in orbit
      aPlanet [P] the world you fall toward
        theTerrain [P] the whole-sphere surface
        theAtmosphere [P] air, sky, weather
        theOcean [P] the water
        theBiomes [P] climate + life bands
        theGround [P] the surface underfoot (matter under boots)
        theInterior [P] layers, ore, caves
          theMining [P] planetary excavation -- the dig verb on a world (bore, ore, claim, beacon)
        theGarden [P] the lush living place (lushEden)
          theEcosystem [P] life cascading from physics
          theTree [P] the Tree of Knowledge
            theTreeForm [P] grown from one genome
            theFruit [H] knowledge of good and evil
          thePlanting [P] the tree grows into the surface (the seam)
          theFarming [P] cultivation -- grow food from energy + soil (the grow verb, tended)
            thePlanetaryFarm [P] farms on a world's surface
            theLunarFarm [P] farms on airless / low-g worlds (domes, regolith hydroponics)
            theOrbitalFarm [P] hydroponic farms in orbit / deep space
    theSpace [P] the medium you fly (the dark, gravity, scale)
    theDensityClock [P] time leans with mass and speed
  theShip [P] the player's vessel; the cold start
    theFlight [P] translation, pitch / yaw / roll, VTOL, wings, landing gear
    theShipPower [P] power buses + capacitor routing (attack / drive / barrier)
    theShipCombat [P] targeting grid, batteries, heavy ordnance, countermeasures
    theShields [P] the barrier grid + directional bias
    theWarpDrive [P] fold travel; VCM / WTM configuration
    theShipView [P] pilot / external-drone perspective, camera presets
    theSalvage [P] the industrial array -- space mining + graviton handling
  theDescent [P] traversing the scales (the membrane onion; LOD of meaning)
    theStanding [P] you stand on real ground, witnessed by contact
    theBlackHole [P] the density clock's ceiling; the hole you can't see into
  theVerbs [P] how you act -- verb over nouns
    theThrust [P] energy -> motion (the density clock)
    theDig [P] into the ground (grain physics)
    theBalance [P] center-of-mass vs center-of-thrust
    theGrow [P] life from energy (logistic)
    theScan [P] read composition (spectral)
    theNavigate [P] orbital mechanics, reach a target
    theShoot [P] aim + discharge weapons (infantry and ship)
    theMelee [P] close-quarters strike
    theEVA [P] suit traversal in vacuum / low-g (jetpack, mag-boots)
  theLoop [P] world + player + input -> verbs -> state -> tick
    thePlayer [P] the character; presence before action (the Dot)
    theInput [P] keystrokes -> verb dials
    theState [P] what ticks
    thePersistence [P] same seed, same world, forever (save / return)
  theMeaning [H] deciding what things mean; the gift, your terminal
    theParadise [H] does Eden read as paradise
    theChoice [H] good and evil; the human decides
    theWorthPlaying [H] is it a game worth playing
    theExperience [H] the felt whole; understood, not won
```

---

## The Verbs in Play — the control protocol

> The decomposition above names the terms; this is their **detail** — the game's controls, told the way
> the timeline is told: forward, in play. It is a control mission (the *Frostbound Protocol*) that names
> every binding as a soldier-pilot actually uses it, plus the two systems the game was built for —
> **planetary mining** (`theMining`) and **farming** (`theFarming`). Bindings are context-dependent: the
> same key is a helmet torch on foot, a high-beam in the rover, a target-paint in flight — so each Act
> is one context. This is the SOURCE that `theShip`, `theVerbs`, `theMining`, and `theFarming` decompose.

### Act I — Sub-Zero Extraction & Infantry Infiltration

The ambient temperature inside the abandoned research station at Sector 9 had plunged to negative forty degrees. Thick coats of crystalline frost clung to the exposed manganese conduits, shimmering under the pale neon flicker of dying emergency strips. Moisture from Commander Vance's breath fogged against his reinforced glass visor as he stepped onto the perforated iron catwalk.

Vance tapped his wrist-mounted terminal, initializing his **OmniSleeve HUD** [`F1`]. The blue holographic interface bloomed in the freezing air, projecting telemetry feeds and current contract updates. Swiping across the projection, he brought up the **Astro-Chart Navigator** [`F2`], mapping the orbital vectors of the moon's jagged ice canyons. He opened the **Sub-Space Comms Transceiver** [`F11`] to monitor local radio bands, opened his **Text Comm Feed** [`Enter`] to glance at encoded squad logs, and accessed the **Sub-System Terminal** [`~`] to scrub diagnostic packet logs. Finding the clutter distracting against the dimly lit corridor, he tapped the **Visor HUD Elements Toggle** [`F12`] to minimize the ambient tactical overlays.

Suddenly, an incoming sub-space ping chimed softly in his ear. Vance tapped `[` to **Accept Sub-Space Transmit** [`[`], listening to a brief burst of atmospheric static before closing the line. He mentally noted that had the signal been an automated orbital distress spam, he would have pressed `]` to **Reject Sub-Space Transmit** [`]`].

Vance leaned forward, initiating **Directional Locomotion** [`W` / `S` / `A` / `D`] as his mag-boots crunched across the frozen slush on the walkway. Spotting a wide fissure where the metal flooring had collapsed into an abyss of sub-glacial ice, he surged forward into a **Sprint Pace** [`Left Shift`] and executed a **Vertical Hop / Zero-G Leap** [`Spacebar`], soaring over the rift to land heavily on the far ledge.

Ahead, automated security sensors scanned the hallway with sweeping red lasers. Vance immediately dropped into a **Low Profile Stance** [`Left Ctrl`], crouching low beneath the beam paths. As the hallway narrowed near the primary vault, he dropped flat into a **Prone Stance** [`X`], crawling under the thermal motion grids. Reaching a heavy blast corner, he executed **Corner Peeking (Left / Right)** [`Q` / `E`] to slice the angle, visually inspecting the automated sentry turret guarding the vault door.

Before he trusted the override, Vance wanted to know what the door was *made of*. He tapped `6` to **Equip Scanner Array** [`6`], raising the handheld spectrometer, and held the `Left Mouse Button` to **Pulse Spectral Scan** [`Left Mouse Button`], washing the blast door in a lattice of blue light. Composition bloomed across his visor — a manganese-titanium weave, brittle at this temperature. He rolled the `Mouse Wheel` to **Adjust Scan Resolution** [`Mouse Wheel Up / Down`], tightening the beam onto the lock housing, then pressed `F` to **Log Composition Sample** [`F`]. The world could not lie about what it was made of; that was the whole promise of the place.

Reaching the vault console, Vance held `F` to summon the **Neural Direct-Interact Menu (Hold)** [Hold `F`], selecting the override sequence, and then tapped `F` to engage **Direct Action** [Tap `F`]. The hydraulic locks hissed, venting plumes of supercooled nitrogen. Before stepping through the threshold into the airlock, Vance unlatched his suit neck-ring using **Lock / Unseal Helmet** [`Left Alt + H`], clicked on his **Helmet Torch** [`T`] to pierce the pitch-black chamber, and pressed `Left Alt + X` to activate **Clear Visor Condensation** [`Left Alt + X`] as flash-frost swept across the glass.

Opening his suit interface via **Open Suit Storage** [`I`], he pulled his primary rifle from his magnetic back-harness. Vance cycled through his arsenal using **Arm Sidearm / Primary A / Primary B** [`1` / `2` / `3`], verified his tactical medical gear with **Equip Injector Applicator** [`4`], and confirmed his multi-tool payload with **Equip Utility Core** [`5`].

As he moved deeper, a frost-seized maintenance drone lunged from a wall recess, too close for the rifle. Vance drove his elbow up with `B` to **Melee Strike** [`B`], then held `B` for a **Weapon Bash** [Hold `B`] that caved its optical housing. The stairwell beyond was pitch black; he pressed `N` to **Cycle Visor Optics** [`N`] — standard, then **thermal** (the residual heat of fresh boot-prints glowing up the steps), then **low-light amplification**. Sprinting the gallery, he tapped `Left Ctrl` mid-stride to drop into a **Combat Slide** [`Left Ctrl` while sprinting], skidding under a half-collapsed bulkhead, and at the rubble beyond pressed `Spacebar` to **Mantle / Vault** [`Spacebar` at a ledge]. Spotting a second sentry down the hall, he clicked the `Middle Mouse Button` to drop a **Tactical Ping** [`Middle Mouse Button`] onto his squad feed, and held it for the **Command Wheel** [Hold `Middle Mouse Button`] to flag a hold-position order.

Bringing the rifle stock to his shoulder, Vance looked through the glass reticle in **Optic Sights View (ADS)** [`Right Mouse Button`]. For the three-hundred-meter shot he pressed `Y` to **Deploy Bipod / Brace** [`Y`] against the railing. Exhalations steadying, he held `Left Shift` for **Steady Aim** [`Left Shift`] while tapping `Page Up` / `Page Down` to **Adjust Optic Range** [`Page Up` / `Page Down`]. He clicked `V` to cycle his **Fire-Rate Selector** [`V`] from full-auto to a controlled three-round burst, then tapped `J` to bring up the **Tactical Rail Mod Menu** [`J`] to attach an infrared suppressor.

The automated sentry turned. Vance pressed his `Left Mouse Button` to **Discharge Weapon** [`Left Mouse Button`], sending high-velocity rounds directly into the sentry's optical core. Sparks exploded into the freezing air. As the slide locked back, he hit `R` to **Swap Magazine** [`R`], then held `G` to **Cook Throwable** [Hold `G`], counting the fuse down, and tapped `Left Alt + G` to **Cycle Throwable Type** [`Left Alt + G`] to an EMP canister before unhooking it with `G` to **Prime Throwables** [`G`] and tossing it into the server rack to neutralize the remaining security grid. A stray laser bolt grazed his shoulder blade; Vance pressed `C` to **Administer Bio-Patch** [`C`], injecting local coagulants. Losing his bearings in the identical corridors, he pulled up `M` for the **Field Map** [`M`], the full tactical overlay of the frozen levels, then held `R` to **Secure Armament** [Hold `R`] as the chamber went silent.

### Act II — The Surface Trench & Rover Extraction

Vance burst through the facility's lower bay doors into an underground garage carved from sheer granite and ice. Parked inside a frost-covered staging bay was an eight-wheeled terrestrial rover. Scrambling into the cockpit, Vance engaged **Drive Torque (Forward / Reverse)** [`W` / `S`] and adjusted his **Steering Direction** [`A` / `D`], slamming the vehicle through the wooden staging crates and out into the roaring blizzard outside.

Snow slammed into the reinforced cockpit windshield. Vance hit `Left Shift` to engage **Overcharge Speed** [`Left Shift`], sending all eight wheels spinning across the icy tundra. He clicked `T` to toggle **High-Beam Illumination** [`T`], carving dual shafts of white light through the blinding snowstorm.

The tundra was sheet ice. Vance flicked `X` to engage the **Traction Diff-Lock** [`X`], all eight wheels biting in unison. When the nose slid into a drift and bogged, he pressed `R` to **Deploy Recovery Winch** [`R`], firing the harpoon-anchor into a granite spur and working the `Mouse Wheel` to **Winch Reel (In / Out)** [`Mouse Wheel`] until the tires found purchase. He cut the whiteout with `N` for a **Vehicle Sensor Sweep** [`N`] and flicked `F4` to the **Chase / Cockpit Camera** [`F4`]. Any other night he would have held `F` to **Dismount Vehicle** [Hold `F`] — tonight he drove on.

Spotting the belly ramp of his starship anchored at the edge of a massive ice shelf, Vance slammed the **Emergency Wheel Brake** [`Spacebar`], bringing the rover into a dramatic four-wheel slide inside the ship's lower cargo deck.

### Act III — Pre-Flight Sequence & Atmospheric Ascent

With the rover secured, Vance sealed the ship's outer ramp, hitting **Hatch Seals (Lock / Unlock)** [`Left Alt + Keypad /`] to pressurize the hold. He climbed the ladder into the main cockpit, strapped into the pilot harness, and tapped `R` to initiate **Ignition Prime (Power & Thrusters On)** [`R`]. The twin fusion cores roared to life, casting an amber glow across the physical switchboard.

Systematically verifying power buses across the flight deck, Vance toggled **Thruster Array Power** [`I`], engaged **Barrier Array Power** [`O`], and primed **Ballistics / Directed-Energy Power** [`P`]. Prepping the ship for atmospheric release, Vance tapped `N` for **Strut Extension / Retraction** [`N`] to tuck the heavy landing gear into the belly bays. He toggled `K` for **Lift Thruster Configuration** [`K`] to orient the vertical engines, and pressed `Left Alt + K` to deploy his **Variable Geometry Wings (Expand / Fold)** [`Left Alt + K`]. Opening the comms array, he broadcast a departure clearance via **Station Docking Request** [`Left Alt + N`].

Vance lifted the ship vertically out of the icy trench using **Vertical Translation (Up / Down)** [`Spacebar` / `Left Ctrl`] and cleared the trench walls with **Lateral Translation (Left / Right)** [`A` / `D`]. Pushing **Primary Propulsion (Forward / Reverse)** [`W` / `S`], he pitched the nose toward the upper cloud deck, adjusting his ascent vector via **Elevation Pitch** [`Mouse Y-Axis`], **Azimuth Yaw** [`Mouse X-Axis`], and **Axial Roll** [`Q` / `E`].

With the trench walls closing, Vance toggled `Z` for **Flight Assist / Stability (SAS)** [`Z`], letting the stabilizers hold attitude, and tapped `Left Alt + X` to **Auto-Level Horizon** [`Left Alt + X`]. Crossing a gas ribbon on the climb, he extended `U` to **Fuel Scoop** [`U`], skimming reaction mass.

Breaking through the dense storm clouds, Vance activated **Burner Overdrive** [`Left Shift`], pushing the hull past the thermal barrier. Testing thruster response in high orbit, he tapped **Vector Arrestor** [`X`] to bring the ship to a dead stop relative to the orbital station, then pressed `C` to set **Automated Velocity Lock** [`C`]. Toggling **Inertial Drift Mode** [`Alt + C`], he decoupled his thruster dampeners, letting the ship coast forward while freely pitching the nose backward to observe the shrinking frozen moon below. To fine-tune his orbital cruise ceiling, he rotated his scroll wheel for **Velocity Governor Adjust** [`Mouse Wheel Up / Down`] and locked the ceiling by pressing **Velocity Governor Toggle** [`Left Alt + Mouse Wheel Click`].

In orbit he opened `M` for the **Star Map / Plot Course** [`M`], threading a route through the system, and pressed `Tab` for the **Discovery Scanner** [`Tab`] — a passive sweep that painted every body, station, and anomaly in range onto his nav-sphere. On the docking approach he opened `F3` for **Station Services** [`F3`] — refuel, rearm, hull repair — `F9` for the **Hangar Loadout** [`F9`] to swap a capacitor bank, and thumbed `F10` to the **Contract & Bounty Board** [`F10`], weighing new work against the ore in his hold. On the return leg he would tap `L` to run the **Auto-Landing Sequence** [`L`].

### Act IV — Deep Space Interdiction & Capacitor Warfare

As the ship crossed into open void, proximity sensors shrieked. Space ripped open as three pirate interceptors dropped out of warp. Vance held `B` to trigger the **Core Configuration Toggle (VCM / WTM)** [Hold `B`], switching his ship from warp travel configuration into high-threat Velocity Combat Mode.

Vance locked onto the leading interceptor by pressing `T` to **Paint Target Under Crosshair** [`T`]. As two more contacts appeared on the radar sphere, he cycled through the threat grid using **Cycle Nearest Hostile Track** [`5`], checked friendly transponders with **Cycle Allied Signals** [`6`], and scanned the wider grid with **Cycle All Contacts** [`7`]. Target acquired, Vance pressed `8` to **Target Sub-System Modules** [`8`], focusing his reticle specifically on the enemy's drive thrusters. He reset his module locking via `Left Alt + 8` for **Reset Module Targeting** [`Left Alt + 8`], pinned the main target with **Lock Priority Target / Release** [`P` / `Left Alt + P`], broke off temporary track with `Left Alt + T` for **Break Target Lock** [`Left Alt + T`], and pressed `G` to set his target tracking mode via **Mount Aim Mode (Assist / Manual / Rigid)** [`G`].

With plasma fire tearing past his cockpit canopy, Vance managed his ship's energy distribution in real time: **Max Capacitor to Attack Systems** [`F5` / `Numpad 8`] to flood the laser cannons; **Max Capacitor to Sub-Light Drives** [`F6` / `Numpad 4`] when extending from a tailing fighter; **Max Capacitor to Barrier Grid** [`F7` / `Numpad 6`] as heavy cannon fire hit his shields; and **Rebalance Energy Grid** [`F8` / `Numpad 5`] to normalize all systems. When the enemy squadron attempted a head-on strafing run, he re-routed shield geometry across the hull — **Barrier Bias Forward** [`Numpad 8`], **Barrier Bias Aft** [`Numpad 2`], **Barrier Bias Port / Starboard** [`Numpad 4` / `Numpad 6`], and **Rebalance Barrier Hull** [`Numpad 5`].

Vance squeezed the `Left Mouse Button` to **Fire Primary Battery** [`Left Mouse Button`], stripping the lead interceptor's shields, followed by the `Right Mouse Button` to **Fire Auxiliary Battery** [`Right Mouse Button`] to shred its armor. Clicking his `Middle Mouse Button`, he engaged the **Heavy Ordnance Interface (Toggle)** [`Middle Mouse Button`], locked his reticle to **Lock Smart Ordnance** [`Middle Mouse Button`], adjusted his missile cluster using **Adjust Salvo Volley Count** [`G` / `Left Alt + G`], and held the `Middle Mouse Button` to **Launch Ordnance** [Hold `Middle Mouse Button`]. The missile streak lit up the dark void before detonating the enemy ship's core.

A missile lock warning blared. Vance flipped `L` to bring his **Point-Defense Grid** [`L`] online, auto-intercepting the inbound seekers; punched `U` to **Deploy Decoy Drone** [`U`], spoofing the lock; hit `H` to **Launch Thermal Flares** [`H`], adjusting output with **Increase / Decrease Flare Burst Size** [`Right Alt + H` / `Left Alt + H`]; and pressed `J` to **Dispense Sensor Jamming Cloud** [`J`], blinding the tracking seeker. With the last interceptor crippled and coasting, he held `Y` to **Hail Target** [`Y`], offering surrender before the killing shot — thankful he had not needed to hold `Right Alt + Y` for **Emergency Pod Ejection** [Hold `Right Alt + Y`] or `Left Alt + Backspace` for the **Core Detonation Sequence** [Hold `Left Alt + Backspace`].

### Act V — Orbital Field Reclamation & Heavy Physics

With the threat eliminated, Vance held `B` to engage **Core Configuration Toggle (VCM / WTM)** [Hold `B`], switching back to Warp Travel Mode. He aligned the ship's nose with a distant star cluster and held `B` to initiate **Fold Drive Spooling & Calibration** [Hold `B` (while in WTM)], watching space bend around the canopy before snapping across the system in a flash of light.

Dropping out of fold-space near a dense asteroid field, Vance brought the ship to a full stop. He held `Y` to **Disengage Helm / Gunnery Station** [Hold `Y`], stood up from the pilot chair, and walked into the utility bridge bay. Before firing the emitter, Vance swept the field with `Tab` for a **Deposit Survey Scan** [`Tab`], grading each rock by yield.

Vance hit `M` to activate the **Industrial Array Toggle** [`M`]. Pressing the `Left Mouse Button` to **Fire Disintegration / Scraping Emitter** [`Left Mouse Button`], he stripped high-grade material from an ancient ship hull floating among the rocks. He tapped the `Right Mouse Button` to **Toggle Emitter Frequency** [`Right Mouse Button`], switching from scraping to fracturing, and fine-tuned beam intensity using **Adjust Emitter Output** [`Mouse Wheel Up / Down`]. Once the hull shattered, he activated his vacuum collection array via **Engage Extraction Sub-routine** [`Left Alt + 1 / 2 / 3`]. As raw ore filled the hold he pressed `Left Alt + M` to run the **Onboard Refinery** [`Left Alt + M`], processing slag into ingots, and checked `M` for the **Cargo Manifest** [`M`]. When volatile gas inside a mined cluster began to overheat, Vance hit `Left Alt + J` to **Eject Unstable Payload** [`Left Alt + J`], jettisoning the dangerous pod out into space before it could rupture the hold.

Stepping out into the depressurized cargo hold in zero-G, Vance aimed his handheld multi-tool at an isolated cargo crate floating in space. He pressed the `Left Mouse Button` to **Activate Graviton Beam** [`Left Mouse Button`], using his `Mouse Wheel Up / Down` to **Adjust Graviton Distance (Push / Pull)** [`Mouse Wheel Up / Down`]. Holding `R` while moving his hand, he engaged **Torque Graviton Payload** [Hold `R` + `Mouse Movement`], smoothly spinning the floating crate in mid-air before locking it onto the deck's magnetic cargo floor.

### Act VI — External Drone Optics & Persistent Departure

Returning to the pressurized cabin, Vance checked the external hull condition for heat scoring by pressing `F4` for **Perspective Toggle (Pilot / External Drone)** [`F4`]. Using his visual tracking visor via **Head-Tracking Look** [`Z`], he surveyed the exterior plating, pan-shifting the drone angle using **Drone Camera Offset** [Hold `F4` + `Arrow Keys`], and zooming in on the thruster bells using **Drone Lens Zoom** [Hold `F4` + `Mouse Wheel`]. Pleased with the external perspective, he saved the visual view using **Save Camera Angle Preset** [Hold `F4` + `Numpad 1–9`] and recalled it instantly with **Recall Camera Angle Preset** [`F4` + `Numpad 1–9`]. He tapped `Left Alt + Z` to check his **Rearview Optics** [`Left Alt + Z`], then paused to press `P` for **Cinematic / Photo Mode** [`P`], framing the frozen moon against the ribbon of the belt.

Vance walked back into the living quarters, opened `L` for the **Ship's Log** [`L`] to append the run's record, unclipped his armor flight vest, and lay down on the bunk. Opening his vehicle power interface, he selected the persistent exit command to save his ship's exact coordinates in the deep void, powering down the vessel's primary systems into quiet darkness.

### Act VII — Planetary Excavation & The Dig  *(theMining)*

Days later, a survey contract took Vance down to the surface of a rust-red world, its thin air scarcely holding a whisper of pressure. He rode the belly-ramp down and stepped onto real ground — regolith that crunched and gave under his mag-boots.

In the low gravity he held `Spacebar` to fire his **EVA Thrusters / Jetpack** [Hold `Spacebar`], drifting across a crater rim, and tapped `Left Alt + B` to toggle **Mag-Boot Adhesion** [`Left Alt + B`], clamping to a sheer rock face to walk it like a floor. Reaching a promising seam, he tapped `6` to raise the **Scanner Array** [`6`] and clicked `Right Mouse Button` to **Toggle Scan Depth (Surface / Subsurface)** [`Right Mouse Button`], reading the ore grade meters down.

Satisfied, Vance tapped `7` to **Equip Excavation Tool** [`7`], the heavy drill-emitter unfolding from his pack. He held the `Left Mouse Button` to **Bore / Excavate** [`Left Mouse Button`], carving into the crust as pulverized rock fountained up in the weak gravity, and clicked `Right Mouse Button` to **Cycle Dig Mode (Bore / Sweep / Pulverize)** [`Right Mouse Button`], widening the cut. He rolled the `Mouse Wheel` to **Adjust Bore Depth / Radius** [`Mouse Wheel Up / Down`], then held `F` to **Vacuum-Collect Ore** [Hold `F`], drawing the loosened ingot-grade material into his suit hopper. Before moving on, he pressed `B` to **Deploy Claim Beacon** [`B`], registering the deposit to his contract, and `Left Alt + J` to **Jettison Tailings** [`Left Alt + J`], dumping the worthless slag.

This was the game beneath the game — the same dig verb the ship used on a floating hull, brought down to boots on a world: the ground *actually there*, telling the truth about what it was made of.

### Act VIII — Cultivation: Planetary, Lunar & Orbital Farms  *(theFarming)*

The last leg was quieter. Vance's standing orders included a growing contract — three farm modules to tend across the system, and a full hold's difference in pay if they thrived.

On the red world's surface, inside a pressurized dome, he tapped `8` to **Equip Cultivation Kit** [`8`]. He held the `Left Mouse Button` to **Till / Prepare Soil** [Hold `Left Mouse Button`], then clicked `Left Mouse Button` to **Plant Seed / Sapling** [`Left Mouse Button`], selecting the crop with the `Mouse Wheel` to **Cycle Seed Stock** [`Mouse Wheel Up / Down`]. He scanned the bed with `6` for a **Soil Composition Read** [`6`], dispensed correction with `G` to **Dispense Nutrients / Fertilizer** [`G`], and held `Right Mouse Button` to **Irrigate / Water** [Hold `Right Mouse Button`]. Overhead he flicked `T` to toggle **Grow-Lamps (PAR Spectrum)** [`T`], flooding the beds with the light the thin sun could not, and opened `F1` for the **Greenhouse Climate Panel** [`F1`] to hold temperature, humidity, and CO₂ in band. When a row matured, he pressed `F` to **Harvest** [`F`] and held `F` to **Prune / Cull** [Hold `F`] the spent stalks.

He pressed `N` to **Cycle Farm Module (Planetary / Lunar / Orbital)** [`N`], and the setting changed: a **lunar** dome on an airless moon, its crops rooted in regolith-hydroponic trays under sealed glass, gravity a third of the world's; then an **orbital** farm — a slow-spinning hydroponic ring in open space, roots misted in aeroponic fog, the planet turning far below. Same verb, three settings: life coaxed out of energy and matter wherever a boundary could hold air and warmth. *Not painted green — green because water and warmth and light fell on grown substrate and life cascaded out of them.*

Vance logged the yields, powered down the lamps, and set the persistent save. Same seed, same world — and now, growing things, waiting for his return.

---

## Feature status & the Holding Bay (the archive protocol)

Every term in the decomposition is a FEATURE, and a feature has a STATUS:

- **In play** — it lives in the ` ```chimera-terms``` ` block above; it compiles into the game (`gen_decl.py`) and is a membrane to PROVE.
- **Holding / archived** — it has been set aside (not working, or deferred). It is **moved**, never deleted, into the ` ```chimera-archive``` ` block below. Concepts are recyclable: an archived feature keeps its bindings and can be referenced, lifted into a new context, or restored.

**The protocol.** To archive a feature, CUT its block (the term and its children) out of `chimera-terms` and PASTE it into `chimera-archive`, with a `# HELD <date>: <reason>` line. To restore, move it back. `gen_decl.py` parses *only* `chimera-terms`, so the Holding Bay is inert by construction — kept in the story, absent from the game, until we revive it. The decomposition is always the CURRENT truth of what is in play; the Holding Bay is the memory of what we set aside. (Same membrane law the rest of the studio runs on: a boundary is what makes "in play" attributable.)

```chimera-archive
# THE HOLDING BAY -- empty. Nothing is archived; every feature above is in play.
# When a feature is set aside, its block moves here with a `# HELD <date>: <reason>` line,
# bindings intact, ready to be revisited, recycled, or restored.
```
