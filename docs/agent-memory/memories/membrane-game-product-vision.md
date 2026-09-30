---
name: membrane-game-product-vision
description: Alan's 2026-09-12 product vision — the Membrane Game (Star Citizen
scope, Minecraft accessibility, cosmic-to-molecular via membranes) plus the
serialized one-at-a-time feature law (visually provable → pass human+dyad →
freeze), the division of labor (dyad verifies parts, Alan tests controls),
the 8-tier feature inventory delivered against it, and the architectural
pivot ENGAGED and deepened — the GPU-resident triangles law (weights
metaphor), bonds-as-materials (glue with cure strength, tensile web), THE
SCRATCH LAW (pairwise hardness — who gives first — with constants
sourced from real material science), and "THE OLOGIES" (Alan's own name
for the game's content: every -ology is a set of material laws the kernel
runs; the 240-card catalogue IS the packed ologies); membrane + bond
definition format + test battery as the next build; THE SHIP GOAL
(2026-09-13, docs/THE_SHIP_GOAL.md) — Steam-READY feature product for
$100k+ lifetime, 9 R-items, OUR OWN WEBSITE first (demo + sign-up,
~95% kept), Steam optional second shelf; percentiles (P($100k) 10-15%
with the push), only-Alan blockers (payment account, price, taste)
metadata:
  node_type: memory
  type: project
  originSessionId: sess_8207b32c-37a6-441b-91a8-b9f8901a74d5
---

**THE COMPETITIVE-MOAT ANSWER (2026-09-21, delivered for Alan's phone call — "what makes this project special when everyone can make a video game with AI"):** the core line: AI made GENERATING games free, so the scarce things are TRUTH and CONSEQUENCE — and that's what this project manufactures. Three phone-friendly moats: (1) THE PHYSICS IS THE GAMEPLAY AND CAN'T BE FAKED — the movement law (no move-forward; locomotion only by limb forces) means a creature that can FALL is a creature whose victories mean something; competitors get animation, almost none get consequence; the punchline is our infant monkey PROVABLY CANNOT STAND (mathematical proof in-repo) — they can generate a standing pose in seconds, none of them can prove anything about their world; (2) THE BRING-ALIVE FLYWHEEL RIDES THE AI WAVE — when everyone generates 3D models, the game that makes ANY mesh physically live (real mass/joints/falling) turns the world's infinite generated assets into creatures; their content is our gameplay; the moat GROWS with the competition; (3) THE VERIFICATION-ECONOMY DEV PROCESS — in the everyone-has-AI world, generation is free and knowing-if-it's-any-good is the bottleneck; the falsifier-first/byte-exact discipline plus the constraint ledger built the verification economy by necessity and it's now the accidentally strategic asset, and the verified experiment corpus compounds while prompts don't. One-sentence version: everyone else's AI makes games that LOOK alive; ours makes worlds that measurably ARE — and in a flooded market, the thing that's actually true is the thing people keep.

Alan's definitive product statement (2026-09-12), correcting fleet process:

**Process law (supersedes parallel feature waves):** "We have invested too
much stock in figuring out complex mathematical proof of a mechanism we may
not decide to use based off visual input and simulation performance results
we find along the way." Features = **visually provable concepts, ONE AT A
TIME**. A feature that passes the human AND the dyad is DONE — frozen,
left unworked until a later polish pass. The lead's serialized queue
replaces parallel polish lanes (the walk-realism lane was the counter-
example: arm-swing polish on a creature that couldn't travel).

**The membrane primitive (his words):** "Each membrane encompasses a
concept — one membrane encompasses the thigh bone, one the shin bone, and
a third encompasses the joint which connects them. This is how we
construct our world with our system AND get the visual proof required for
progress." Membranes are both the physics unit and the world-building
unit; joints are membranes too.

**The vision:** a game with **Star Citizen feature scope**, the material
detail of Space Engineers / advanced material sims, and the
**Minecraft lesson** — hardware-limited simplicity that runs smoothly,
leaves room for imagination, and is playable online with friends (his
named killer feature). Scale ambition: **cosmic level down to the
molecular structure of matter** — "we're simulating physical properties of
the outer membrane of material, represented by the triangles of our
advanced rendering physics combo system — putting reality into a game
like Star Citizen or Minecraft."

**Division of labor (his caveat, same day):** "the Dyad will have to take
care of most of the little tiny broken down elements like how a knee works
and stuff like that — the human will mainly be testing the input system
and controls once we get those working, but first we have to build all the
parts." **The dyad owns the PARTS** (every knee, joint, membrane,
material — micro verification, mechanically + visually, without Alan);
**Alan owns the HANDS** (input, controls, and FEEL — the play layer;
nobody else can grade feel); **sequence is parts-first, controls-after**.

**The inventory delivered (THE MEMBRANE GAME, 8 tiers / 33 features):**
T0 body (5 frozen: rig, truthful HUD, choreography, camera fit, viewer) →
T1 locomotion (walk-travels = the current single feature; foot planting;
composed arm-swing) → T2 fluids (water body, downhill flow, buoyancy =
first teaching moment) → T3 materials, the membrane heart (squash, cloth,
fracture=the Minecraft verb, freeze, melt, burn) → T4 hands (grab, carry,
throw, place/build=the Space Engineers verb) → T5 world (terrain chunks,
variable gravity=cosmic end, wind, day/night) → T6 molecular (heat
spread, vibration, ice→water→steam state changes) → T7 friends
(multiplayer) → **T8 CONTROLS (Alan's test bench)**: keyboard→motion
(W=walk — the contract already takes commands; binding a key is small
once travel lands), mouse→camera orbit/zoom, click→grab/pour/poke,
gamepad — all Python-side through the viewer, which is already the
control surface by construction. Cadence math he was given: 5 frozen, 1
in flight, 23 queued; one-at-a-time bus mode ≈ 1 visible capability/day,
full inventory ~4-5 weeks at 88% first-pass. **Multiplayer quiet weapon:
the engine is already a server — the HTTP contract every feature speaks
IS the multiplayer architecture** (P(cost low) 70%).

**Why:** this is the destination every lane should trace to; it resolved
the doctrine collision (no-C++ vs visually-verifiable) via the one
sanctioned engine exception (root-translation) and retired the
proofs-before-visuals pattern.

**LOCKED INTO THE REPO (2026-09-12, Alan's "first goal" directive):**
`docs/THE_GAME.md` — the product constitution, written on the slot-1
integration lane (fleet-product-charter-01, PR #111, gated like any PR
with a fidelity-bar reviewer; a copy lives on Alan's desktop
CHIMERA_PROOF/THE_GAME.md). It carries: the vision verbatim, the membrane
primitive, the 8 operating laws (one-at-a-time / visually provable /
pass=freeze / proofs-wait-for-visuals / kitchen-rule with named appliance
exceptions / invisibles-seen-then-unseen / dyad-owns-parts-human-owns-hands
/ observations-beat-databases), the Chimera language protocol, the tiered
inventory, and the cadence math. **Alan's commitment recorded in it,
verbatim: "I am not going to stop until I'm dead or it's created. My
autistic mind will not let this one go ever."** Future changes are
append-only amendments by operator direction only — this file is the
touchstone every lane answers to.

**How to apply:** admit ONE feature at a time from the tier order; every
feature's acceptance = human + blind dyad (with the division of labor
above: the dyad judges the part, Alan judges only controls/feel — so
part-verification runs WITHOUT waiting on him); on pass, freeze and move
down the inventory; proofs/reference models wait until a visual asks for
them. From the first controllable part onward, every frozen part arrives
with a control attached so his testing keeps pace with the build (walk
passing the dyad triggers key-binding: the first thing he can PLAY).
**Parts-bin rule (2026-09-12): abandoned work stays on branches as
storage — cherry-pick useful pieces forward one at a time when a need
names them; no reconciliation archaeology.**
See [[alan-fleet-operating-style]], [[chimera-holodeck-catalogue]].

**FRONT PAGE + MASTER (2026-09-12, his shouted order — the vision must
not be "hiding inside the God damn repo") — COMPLETED**: charter PR #111
went through FOUR review generations (two legitimate REJECTs answered:
gen-2 forked above its own Tier-0 proofs; gen-3 smuggled three scratch
files via a dirty-worktree `git add -A`; final head f3856921) and merged
at 22209e4e; **master promoted to 8e939e77 and set as `default_branch` —
the repo front page now opens on "CHIMERA — the membrane game / A world
built from membranes — cosmic down to molecular — where the physics
cannot lie"** (verified via the GitHub readme endpoint). The README front
page carries the vision, what-runs-today, a verified quickstart
(engine/CMakeLists path + port 8105 aligned with the viewer default),
short-form laws, repo map, and status.

**THE TEDDY IS THE PRODUCT'S FACE — it must be visibly ON master
(2026-09-12, his explicit preservation order):** "Just make sure that we
see that monkey teddy bear with all of the rigging numbers and stuff —
we've got labels on joints and everything... along with the way the
viewer looks... how the engine runs right now needs to be preserved for
the master." The creature + rig + joint labels/numbers + viewer look are
first-class product identity, not incidental assets. Verified on
origin/master at 6864e105 via tree receipts: `Saved/meshes/
monkey_birth.bin` (661 KB) + `monkey_joints.bin` (296 KB, 28 joints), the
label/HUD engine code (`ui.cpp` 196 KB, `engine.cpp` 489 KB),
`tools/product_viewer/` complete, and the committed proof media (labeled
keyframes + walk/motion-sweep/water movies under docs/evidence/).
**Branch topology he was given (and accepted): astra/gait-capture is the
WORK line (where features merge under review); master receives promoted
merges of it — "nothing of the creature, the labels, or the viewer is
stranded."** Anyone cloning master gets the teddy, its rig, its truthful
numbers, the viewer, and every proof movie.

**Tier-1 status at "proceed as planned" (2026-09-12 late):** the single
active feature is **engine-root-translation-01** (w02; the one sanctioned
C++ appliance — one public root-translate route + readback, parity
falsifier: same thetas, same pixels except translation); walk-travels
(feature #6, the REAL walking acceptance) queues behind it.
**Walk-realism (PR #110) FAILED its visual rubric honestly — its real
discovery is the COMMANDED-VS-RENDERED GAP**: engine readbacks showed
counter-swing to ≤0.0004° and head level to 0.001°, but the blind judge
saw "arms hang straight down... stiff like dead pendulums" — the
composed stride pack's arm rotations do not visibly reach the render
path (open defect; blocks any realism claim). Its durable physics
finding: the gait plane and pose plane CANNOT compose at the route layer
(a /joint write into a playing stride is overwritten every frame) but DO
compose at the data layer (composed stride pack via /stride_bin, gates
G1–G7 pass). Realism stays OPEN per pass=freeze and retries after travel
lands. Also parked per serialization: water-v2 (host stopped mid-lane,
worktree preserved), invisibles (host stale ~60 min, ambiguous — check
worktree writes before counting it).

**THE VISION EVOLVED — the Kilo-era state (2026-09-12, Alan's handoff
prompt on return to the native harness; supersede older framings where
they conflict):**
- **docs/THE_ALIGNMENT.md is the sealed operating system** (lead-authored
  from Alan's live directives): truth hierarchy — the ONLY machine truth
  is a dyad report describing an image actually rendered by the engine;
  all status reporting is lies. Triangle ontology: the triangle is "the
  electron" — an irreducible; the project is **PROGRAMMABLE MATTER** (the
  outside membrane programmed with the mathematical characteristics of
  the simulated material); all math on triangles; knee≠hip are triangular
  representations to unfold; begin/end states and everything between is
  **TRAINED**. **The fleet is RETIRED (THE_ALIGNMENT.md §8, operator
  order)** — controller/daemons/lanes/agent-liveness reporting are dead
  and may never return; task states (any harness) lie; trust directories
  and renders only.
- **The web viewer IS the game client** ("unless we can transmit to a web
  viewer our product is useless; you will play the game by applying
  controls to the web browser; I will do the same; so will the player").
  Multiplayer-minded: every client serves the world, none owns it.
  tools/product_viewer/server.py on 127.0.0.1:8206 carries the
  one-to-one engine-window mirror, clean /frame product pane, drag-orbit,
  WASD/QE/R/P keys, pose-clock toggle, THE WALK GAME CONTROL
  (/api/walk {on} — every browser sees the same body), take-mode
  observer-yield, red ENGINE DOWN banner, /graph ledger constellation.
- **THE TRAINED WALK is the front — robot tech mandated** (MuJoCo 3.10.0;
  sim body slot-05\external\myo_sim; frozen policies stand_theta.npy/
  walk_theta.npy/step_theta.npy restored). Measured baseline: f4_walk
  FAIL all four bars (falls forward at 1.02s, speed 44% of derived
  0.9924 m/s). Pre-registered next build: train the stand term WITH the
  moving base JOINTLY, then --forward 0.5; bars: hold ≥60s, periodicity
  ≥0.35, travel positive, duty in band.
- **THE FORCE VETO — carry forever**: nothing so far was trained; the
  stride pack is a recording and a posted root velocity was authored;
  Alan nearly abandoned the project over it. "The object itself has to
  generate force and you have to train the object to walk" — every
  movement must be earned by training in the simulator and judged by the
  dyad, or it is not shown as progress. Never post an authored linear
  /root velocity.
- The one loop: build (Python over the frozen engine) → render → dyad →
  apply → repeat; the human sees everything and overrides all; pass =
  dyad approves AND the operator agrees, then frozen. The monkey is the
  seed of the universe — the world materializes around it as controls
  arrive.

**KILO HANDOFF OPERATIONAL ADDENDUM (2026-09-12, from Alan's pasted
resume prompt — the operational state he authored):** engines in
`slot-05\.tmp\engine_build\` — **roottranslation-BASE STABLE** (served
8107 with the teddy loaded) vs **roottranslation transformed BROKEN**
(crashes on hinge_bin+stride_bin+stride-on, reproduced twice; parity
battery: P1 thetas-untouched-by-root PASS, P4 pixel-exact round-trip
PASS, P2 centroid-vs-/project FAIL, P3 root×hinge freezes the body —
completion is SERIAL after the trained walk). **f4_walk measured
baseline (10 seeds, honest): FAIL all four bars** — falls forward at
1.02 s, pelvis min 48% of target, speed 0.44 m/s = 44% of the derived
0.9924, periodicity 0.15, and the ablation travels too (the oscillator
is decorative: the travel is a fall). **EM-25 boundary law: the stride
pack stores RADIANS, /joint takes DEGREES — convert at the boundary
(the statue regression).** **Unit scale PAUSED: teddy leg 3.12 engine
units vs the 0.9201 m reference — derive the scale first, never
transport it.** Graphify graph built over slot-05 (35,723 nodes /
51,272 edges / 2,649 communities; query/explain/affected/path/
merge-graphs/watch/cluster-only) — KNOWN GAP: engine.cpp member
functions did NOT extract (single-giant-class file), so frozen-core
impact analysis stays manual. Viewer selftest: node
`C:\Users\allen\node-portable\node-v22.23.1-win-x64\node.exe`
`E:\ChimeraWork\concept_proof\selftest.js` (env
PLAYWRIGHT_BROWSERS_PATH=C:\Users\allen\AppData\Local\ms-playwright;
playwright-core resolves at E:\PythonChimera\node_modules). Kilo
runbook copy: `C:\Users\allen\.config\kilo\chimera-fleet-lead-runbook.md`.
The handoff's first moves: (1) viewer visible in the native harness or
say so plainly; (2) candidate-1 training (moving-base stand term WITH
the base, JOINTLY — hypothesis nine's lesson) in background; (3)
f4_walk --forward 0.5 against the pre-registered bars (hold ≥60 s,
periodicity ≥0.35, travel positive, duty in 0.6027 band); (4) learned
gait → engine render → blind dyad → desktop; (5) root appliance
completion, serial.

**MOVEMENT ARCHITECTURE — Python-the-puppeteer applies FORCES, never poses
(2026-09-12, operator synthesis; supersedes all pose-posting patterns):**
"Python controls the CPU — the puppeteer strings that pull on reality
itself." Leg power is mathematical: strength as a FUNCTION of joint angle
(a leg is strong at some knee angles, weak at others) computed Python-side
and applied as pulls; the ENGINE integrates at full frame rate between
Python ticks (30–60 Hz Python, 190+ fps engine). Poses were the shortcut
that broke it; forces are the living-muscle model. **Build-then-train law:**
build the creature the way a robot/human is built — skeleton, hinges, ALL
the physical limitations of the chosen creature (human, robot, teddy-bear
monkey: joint ROM, torque ceilings, mass) — THEN train inside those limits.
The creature is the hard, non-uniform case done first to prove possibility;
uniform structures come easier. **Rig-completion phase law:** the rendered
look is the product of the CURRENT phase (rigging the bones + creating the
object) — skin-not-following-bones is in-phase work: audit the coupling,
fix it Python-side as data (recomputed joint bindings/hinge bands from the
mesh's own weights), engine untouched. **Misinterpretation guard:** basic
movement can be misread as successful walking (the stride "travel" was a
fall; readbacks passed while the judge saw stiff arms) — the simulator's
mechanical truth (contact timing/forces, center-of-mass, ROM-stop
violations, the four bars) is PRIMARY; the rendered look validates the rig;
the dyad judges the result. Lanes from this synthesis:
engine-torque-route-01 (the strings — torque/force route, serial appliance
behind root-translation) + walk-policy-train-01 (MuJoCo candidate-1
training with the rig-audit caveat; dispatched to worker-03).

**THE BODY CHECKLIST (2026-09-12 session close — the checklist FORM was
ALAN's own proposal: "you can't have a body that walks unless you have a
certain number of things there's probably a checklist you need"; the
5-item list was delivered against it and he proceeded):** the gate list
before ANY walk training —
1. **FEET** — the ankle is currently the terminal joint; a walker needs a
   real foot (heel, ball, possibly toes) with contact surfaces. "Without
   them, walking is falling with style."
2. **SKIN BOUND TO BONE** — every triangle follows its membrane (the
   audit-driven rebind).
3. **MASS** — per-membrane weight derived from geometry, so limbs swing
   true.
4. **LIMITS COMPLETE** — ROM (have) + strength/torque ceilings (to derive).
5. **THE STAND TEST** — the finished body holds itself upright, still, for
   one minute in the simulator = THE gate into training ("if it can't
   stand, it can't walk").
Offered trigger he holds: "build the checklist" starts the feet — design
first, his approval, THEN build. See the matching ask-first rule in
[[alan-operator-preferences]] (training authorization) and the happy-medium
spend doctrine (execution mode: lead-works-alone for this phase).

**THE ARCHITECTURAL-PIVOT QUESTION (2026-09-12, session final exchange —
PROPOSED, awaiting his word):** Alan stepped back to first principles:
"First we have to ask ourselves can we accurately simulate matter with our
methods I think we have to throw this whole monkey in the garbage and think
about this systematically from architectural perspective." The analysis
returned (pending his trigger — "say the word" starts it; NOT yet approved):

- **Accuracy map of the membrane method (honest):** YES for the materials a
  teaching game lives on — thin shells/skin/cloth (thin-shell mechanics on
  triangle meshes is established physics), surfaces (contact, friction,
  reflection, heat entry, surface flow — the surface is where matter
  interacts), skeletons/machines (hinged membranes with angle-dependent
  strength = classic rigid-body + MuJoCo gym). NO for **thick volume matter**
  (a solid beam's internal stress lives in its volume; triangles only see
  the outside — approximate with the right behavior for teaching, but exact
  volume physics is not this method's native land). Percentiles given:
  P(membrane method passes teaching-grade on its home classes) ~85%;
  P(volume matter as teachable approximation) ~75%.
- **THE MONKEY VERDICT: not garbage — DEMOTED from substrate to skin.** The
  mistake was construction ORDER, not the asset: the monkey was built as
  ART (mesh) with physics bolted on; his architecture says author the body
  as MEMBRANES FIRST (each with triangles, material, mass, strength curve)
  and the mesh is clothing draped over it. The monkey mesh becomes the skin
  of a membrane-authored body; feet get authored as membranes directly;
  nothing built is wasted — the substrate changes.
- **Four-layer systematic architecture proposed:** (1) matter kernel —
  triangle + membrane + CA types, every membrane carries material math
  (partially exists: hinge law, strain overlay, water graph); (2) body
  authoring — bodies written as membrane hierarchies in a definition file;
  THE DEFINITION IS THE BODY, meshes draped as appearance; (3) solvers per
  material class — rigid-hinge, thin-shell, surface-flow — all
  membrane-compatible, one engine; (4) verification — dyad + measured gates
  (built).
- **The proof before the game: a MEMBRANE TEST BATTERY with a falsifier**
  (Rule 0): a shell bends with the measured curve, a cloth drapes, water
  spreads, a block compresses within a stated error of reference — if the
  battery fails, the method fails BEFORE the game is built on sand. First
  build if triggered: the membrane definition format + the test battery —
  no monkey needed, no training, just matter proving itself.

**THE PIVOT ENGAGED + DEEPENED — the GPU-WEIGHTS LAW and BONDS-AS-
MATERIALS (2026-09-12 session close, Alan's direct continuation; the
four-layer proposal was ACCEPTED: "what you have said is good and that's
what I want because each membrane has to be able to like have a
relationship to the others... We need to go deeper"):**

- **THE GPU-RESIDENT TRIANGLES LAW ("triangles are weights") — his own
  idea, restated as the FPS diagnosis:** "everything gets translated
  through the engine. That's why right now the engine is running at a low
  FPS — because we didn't follow my idea of loading all of the triangles
  into the GPU, sort of like a model that's loaded for doing AI." An AI
  model doesn't ship its weights to the CPU per inference; likewise ALL
  triangles load onto the GPU ONCE and stay there as resident state — the
  matter computes itself in place every frame, and PYTHON NEVER TOUCHES
  FRAMES: it issues intents (pull here, glue this) and exits. The 22fps
  stutter was the per-frame Python round-trip violating this law (the CA-
  field GPU law in THE_TRIANGLE_GUIDE is the same law; this named its
  violation as the cause).
- **BONDS ARE MATERIALS — glue as first-class matter:** gluing two
  membranes creates a THIRD material between them: the glue, with its own
  cure strength, stiffness, yield. "If you have two metal material
  membranes and mathematical glue on them, the bond strength depends on
  the cure strength of the glue." Two steel membranes with weak glue = a
  joint that fails at the glue line, not the steel — the physics decides
  where it breaks. This is not a special case; the connection is just more
  matter. **"There'll be lots of tensile material type physics
  calculations going on here."**
- **THE TENSILE WEB (teaching payload):** every pull distributes load
  through the bond network; the network finds its weakest link; failures
  are honest (the sim answers "why did the wing snap THERE?" by breaking,
  not by script).
- **THE KERNEL STATEMENT (complete):** matter is membranes; connection is
  matter; the GPU holds it all and computes it; Python pulls and glues —
  never poses, never frames.
- **Deepened next build:** the **membrane + BOND definition format**
  (materials + bonds with cure parameters) and the test battery — battery
  item one writes itself from this exchange: *a glue joint, pulled, breaks
  at its measured cure strength, on the GPU, without Python in the loop.*
  Spec goes to Alan for review BEFORE building (ask-first rule; two
  unauthorized-training burns already).

**THE KERNEL SPEC IS WRITTEN — KERNEL_SPEC.md (2026-09-12 session close,
delivered to his desktop CHIMERA_PROOF/ + `E:\ChimeraWork\matter_graph\
KERNEL_SPEC.md`; his "ready to get to work" triggered it):** the full spec
he must approve before anything builds —
- **§1 The four laws** (triangles-are-weights / bonds-are-materials /
  tensile web / scratch law, each with its incident or source).
- **§2 The definition format:** bodies authored as JSON data — the
  definition IS the body; materials carry sourced constants
  (density/young_modulus/yield/hardness_vickers); membranes reference
  triangle binaries + thickness; bonds carry members + contact +
  cure_strength; **mass derives from geometry × density, never guessed;
  every constant cites its source table (OPEN until sourced); the monkey
  is demoted to draped clothing.**
- **§3 The test battery (Rule 0, each with prediction + falsifier):**
  B1 scratch (steel on wood: wood yields at the contact line, steel
  unmarked), B2 glue (two steels + weak glue pulled: breaks AT the glue
  line at ~cure strength, not in the steel, not holding past 2×), B3
  tensile chain (weakest bond fails first at its yield), B4 shell (cloth
  drapes, folds measured vs shell math), B5 residency (zero Python
  per-frame traffic, GPU frame time in budget). P(teaching-grade B1–B4)
  ~85%; battery runs BEFORE the body work resumes.
- **§5 Build order:** (1) format parser+validator → (2) sourced constants
  table → (3) battery B1 first, then B2–B5 serially → (4) only after the
  battery passes: bodies authored as membranes (FEET first), training
  stays forbidden until the body is complete.
- **§6 APPROVAL GATE:** nothing builds until the operator approves or
  strikes lines — trigger word "approved".

**THE OLOGIES** — Alan's own coinage for the game's CONTENT (2026-09-12,
session final naming: "Yes exactly We bring out the ologies as what I call
it"):** every science -ology is a set of material laws the kernel runs —
ge-ology gave the scratch law, rhe-ology gives flow, therm-ology gives
heat. The kernel is the MACHINE; the ologies are the CONTENT it runs.
**The 240-card physics curriculum (40 domains) IS the already-packed
ology catalog** — it was waiting for this kernel the whole time (see
[[chimera-holodeck-catalogue]]). **Catalogue provenance (2026-09-12,
Alan's words): the 240-card ology catalog was designed by ASTRA — "the
American model."** The lineage: Alan set the laws, Astra packed the
ologies, the lead builds the machine that runs them. The whole game in his one sentence: **the
kernel runs the ologies on GPU-resident triangles, and the player sees
them.** Use "the ologies" as his term when discussing content domains.

**THE STEAM MARKET QUESTION (2026-09-13, Alan: "can I set a goal to
make $100,000 on Steam selling our game project")** — answered honestly;
the goal is HIS to set, revenue is nobody's to promise. Percentiles
given: **P($100k) ≈ 10–15% WITH demo + Steam festival + streamer
outreach; 2–5% without.** Math he was shown: $100k = ~$143k gross
(Steam 30%) ≈ 10,000 copies at $20 / 20,000 at $10; median indie sells
~1,500 copies. The hook is real and trailer-shaped: *press the creature
and it answers like real tissue* — demonstrable in ten seconds of video.
**Build-side gaps (P(lead delivers) ≈ 85%):** game loop (start screen,
reason to keep playing), the teaching content (the ologies ARE the
product), audio, player-facing UI, store page (capsule/trailer/
screenshots), and a packaged double-click build — **the maximized-
window foreground stall is a named LAUNCH BLOCKER** (fixable). **Only-
Alan blockers:** the Steam partner account (his tax identity + banking
+ $100 Steam Direct per app — never create it for him), price/ad money
decisions, trailer/hook taste calls.

**GOAL RESHAPED BY ALAN same day — THE SHIP GOAL (supersedes the
demo-first sequencing):** the goal is Steam-READY — a FEATURE product —
positioned for $100,000+ lifetime; **the Steam account explicitly waits
until the finished product exists** ("We don't have to get a Steam
account until we have a finished product"). Recorded as
`docs/THE_SHIP_GOAL.md` (eb86f778, on
astra/tasks/matter-kernel-format-01): the bar is "a stranger downloads,
double-clicks, plays unaided, learns physics by touch, wants to show a
friend"; 8 R-items all OPEN (R1 double-click launch, R2 game loop, R3
hook in motion, R4 five lessons, R5 sound, R6 60 fps ordinary machine,
R7 store package, R8 blind stranger test), with a status ledger. Work
order: R1 first (kill the maximised-window blocker), then hook, loop,
lessons, sound, performance, package — the 8-goal engineering ladder in
[[seal-wall-takeover-2026-09-13]] maps onto it. Price target $15-20;
the "start the demo" trigger is superseded by the R-item order (R1
begins on his continue).

**CHANNEL AMENDED — OUR OWN WEBSITE FIRST (2026-09-13, Alan: "we don't
have to use Steam also we can also open our own website and attract
customers to just sign up after playing the demo"; R9 added to
THE_SHIP_GOAL.md, de3b8f3a):** the funnel is OUR PAGE — free demo
hosted by us, play first, sign-up capture underneath — keeping ~95% of
revenue vs a store's 70% (~7,000 copies at $15 instead of ~10,000);
the sign-up list is OURS (direct launch-day reach, lesson packs as
return reasons); Steam demoted to OPTIONAL second shelf (same package
serves both); a browser-playable demo is in reach because the engine
already serves web (the viewer). The demo -> festival -> streamers
funnel is superseded; only-Alan dependency becomes the payment account
(Stripe/PayPal, his identity) when selling starts.

**THE WORLD LAW (2026-09-13, Alan: "we'll create a game world and every
user will just be another camera in that game world"; recorded in
THE_SHIP_GOAL.md, 163a6047)** — the multiplayer architecture is now
operator law, formalizing the quiet-weapon note above: ONE game world
(the engine's living simulation), every player attaches as a CAMERA
with a voice. Nobody owns a copy; a player = a viewpoint plus the
intents they speak (press, poke, pose). What one touches, every camera
sees — there is only one creature. The sign-up (R9) ties a NAME to a
camera; the session snapshot is the world's memory (persistence between
visits is what makes it a world, not a screensaver). Consequences: a
second player is a second connection, never a second simulation;
scaling = more worlds (servers), not per-player copies. Steers R2
  (game loop = "join the world"), R9 (the website = the front door to
  the camera), and the sign-up. The press is what makes it a place —
  a world people can only watch is a video.

**THE MOVEMENT LAW (2026-09-13, Alan: the character "can't simply just
move forward — it sits in a gravity environment; the only way to
operate is to move your limbs and to adjust your body relative to the
surface of gravitational resistance"; recorded in THE_SHIP_GOAL.md,
1dfad8e8, beside the world law)** — NO move-forward exists: the
creature is a body with weight in gravity on a surface, and walking is
NOT an animation or a script — it is the discovered consequence of
gravity + ground contact + limb actuation. Build order each piece
derivable: (1) MASS from geometry (the matter-kernel definition
already derives it), (2) GRAVITY one constant, (3) GROUND CONTACT at
the feet cells (normal force + friction at the floor plane),
(4) MUSCLES — joint intents become servo torques
(k*(target-angle) − c*rate), never teleport angles, (5) BALANCE —
nothing holds the creature up except its limbs. **THE FALSIFIER THAT
KEEPS IT HONEST: a creature that cannot FALL cannot walk — the first
bar of the ground appliance is the FALL, not the step.** This law
extends THE FORCE VETO (never an authored linear velocity) into the
membrane-engine era and gates the walk goal (#6 in the 8-goal plan):
the ground appliance must precede any lesson asking "how do you
walk?". Consistent with the BODY CHECKLIST below (mass/limits/stand
test) — same physics, now operator law for the sealed-cell creature.

**THE ALIVENESS LAW (2026-09-13, Alan: "we don't have to make our own
characters we can find pre rigged characters but we should also know
how to make our own... drop a skeleton and superimpose them over
static objects and then make them come alive... it's gonna transform
any character — in fact system will be necessary"; recorded in
THE_SHIP_GOAL.md, 4f1da62e)** — the physics is CHARACTER-AGNOSTIC:
any mesh + any skeleton = a living sealed-cell creature. Pre-rigged
characters are content found in the wild; authoring our own rig is the
fallback skill. The product op is ONE INTENT — "bring alive" =
classify + bind + seal in a single POST on any static mesh. Needs:
glTF/OBJ import into the engine's full format; the honesty gate —
leaky imports REFUSED BY NAME (the volume math needs a closed
surface); the falsifier — a brought-alive creature must pass the same
bars as the sculpted monkey (volumes conserved, pressures honest,
poses travel, touch answers) or it is not alive. The pipeline already
proves the shape: classify_run.py is mesh-agnostic machinery. This
resolves the content-pipeline question: import, not sculpting.

**COMPETITIVE POSITIONING vs AI-GENERATED GAMES (2026-09-21, Alan's phone discussion with a friend — discussion only, no development effect):** the question was how to compete when everyone can make a video game with AI. The delivered framing (reusable for website/pitch copy): **AI made GENERATING games free, so the scarce goods are TRUTH and CONSEQUENCE — exactly what this project manufactures.** Three moats: (1) **Physics-as-gameplay with consequence** — the movement law means a creature that can FALL is a creature whose victories mean something; competitors have animation, we have reproducible physics (the walk reproduces bit-exact from any clone; we can explain WHY the monkey walks down to a 7e-7 m touch reading; we hold a mathematical PROOF the infant corpse cannot stand — competitors can generate a standing pose but cannot prove anything about their worlds); (2) **The bring-alive flywheel RIDES the AI wave** — when everyone generates 3D models with AI, the game that makes ANY mesh physically live (classify+bind+seal, THE ALIVENESS LAW) turns the world's infinite generated assets into gameplay; their content is our creatures — a moat that grows with the competition; (3) **The verification-economy dev process is a compound asset** — falsifier-first discipline, byte-exact reproduction, the constraint-ledger substrate; in a world where generation is free, VERIFICATION is the bottleneck and we've been building that economy for months, plus the verified experiment corpus compounds. One-liner delivered: *"everyone else's AI makes games that look alive; ours makes worlds that measurably are — and in a flooded market, the thing that's actually true is the thing people keep."*
