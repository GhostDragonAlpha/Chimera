# THE CONTROLLER MAP — the whole game collapsed onto ~12 buttons

> The controller is the **compression**. "Everything a human does" is infinite; a gamepad has ~12
> gameplay inputs. So every action in the game MUST resolve onto a button, and every button resolves
> to ONE parameterized state-machine *formula* whose numbers are filled in by the membranes you're
> standing inside. This is the state-machine + membrane architecture (`docs/THE_STATE_MACHINE_PHYSICS.md`)
> pointed at the controller.
>
> **Status:** DRAFT for the operator. This is player-controls-first — it is *the* design artifact.

## The formula (one line)

> **action = StateMachine( button ) driven by ( object · ground · gravity · surface · body )**

The **button** picks which formula. The **membranes** hand it the parameters (the object membrane
gives size/mass, the ground membrane gives slope, the world membrane gives gravity). One formula,
every scenario — because a scenario is just a parameter set. Context also *selects the variant*: the
same button fires a different formula-instance depending on what's in front of you (near a ledge, at
cover, holding a ball) — exactly how a modern "action" button already works.

## The ATOMS — the shared sub-states (~13, the "Frankenstein" parts)

Every formula is stitched from these. They are what gets reused, so they are what we train once and
share everywhere. The commonality goes all the way down: ~13 atoms → ~50 formulas → ~12 buttons.

| atom | what it does |
|---|---|
| **STEP** | plant a foot, shift weight, swing the other — the locomotion unit |
| **PLANT** | establish a stable contact (foot or hand) for support |
| **SHIFT** | move center-of-mass over a support |
| **BALANCE** | hold COM over the base of support (the stand we're training now) |
| **RECOVER** | return toward balance after a shove or slip |
| **REACH** | extend a limb toward a target point |
| **GRIP** | close a hand on a contacted object *(params: grip type, force)* |
| **RELEASE** | open the hand |
| **BRACE** | co-contract to stiffen against a load or impact |
| **PUSH** | extend a braced limb against a surface/object |
| **PULL** | flex a gripped limb to draw the body or object |
| **SWING** | ballistic limb motion (throw, strike, stride) |
| **LAUNCH / ABSORB** | explosive leg extension (jump) / flexion to absorb (land) |

## The MAP — button → formula → atoms → context → variant

| input | formula (verb) | atoms it stitches | driven by | contextual variant |
|---|---|---|---|---|
| **Left Stick** | MOVE (walk↔run by magnitude) | STEP · PLANT · SHIFT · BALANCE · RECOVER | terrain slope/stairs, gravity, friction | in water → swim-stroke; at edge → edge-shuffle |
| **L3 click** | SPRINT | STEP(fast) · SWING | gravity (Moon = longer float) | — |
| **Right Stick** | LOOK / AIM-orient | ORIENT (head→torso→body) | — | with LT → fine-aim |
| **A / ✕** | JUMP → TRAVERSE | LAUNCH · ABSORB / REACH+PULL / SWING-leg | ledge height, gap width, gravity | ledge → **mantle**; obstacle → **vault**; else jump |
| **B / ○** | CROUCH → LOW | SHIFT-down · PLANT / SWING | speed, overhead clearance | running → **slide**; hold → **prone/crawl**; at cover → **take-cover** |
| **X / □** | GRAB / INTERACT | REACH · GRIP · BRACE · (LIFT) | **object: size, mass, shape, grips** | pin → pinch; ball → two-hand; door → PUSH/PULL; lever → PULL |
| **Y / △** | USE / STOW held item | item-specific | held item's genome | — |
| **LB** | LEFT HAND / lean-left | REACH(L) · GRIP(L) / SHIFT(L) | object; cover geometry | at cover → lean-left peek |
| **RB** | RIGHT HAND / lean-right | REACH(R) · GRIP(R) / SHIFT(R) | object; cover | at cover → lean-right peek |
| **LT** | AIM / BRACE (raise & steady) | ORIENT · BRACE | held mass (heavier → more brace) | two-hand item → both arms |
| **RT** | ACTION: THROW / STRIKE | SWING (wind → release) / PUSH | **held mass/shape sets the arc** | empty hand → punch; held → throw |
| **D-pad** | STANCE / GESTURE select | pose set | — | up → stand-tall; down → prone; ←/→ → emote |

*(ORIENT is the 14th atom — head/torso/whole-body aim; used by Right Stick and every aimed action.)*

## Where the parameters come from — the membranes

The hierarchy's strength is that **each membrane you're inside supplies part of the parameter set**,
automatically, as a local constant:

- **World membrane** → gravity → scales every force (Moon strides, high-g crouch).
- **Ground membrane** → slope, stairs, surface friction/softness → shapes STEP and PLANT.
- **Object membrane** → size, mass, shape, grip-points → shapes GRIP, LIFT, THROW. *The object hands the grab its own numbers.*
- **Body membrane** → reach, strength, fatigue, damage → limits what's possible.

The policy is *conditioned* on all of these. That is "taking advantage of the hierarchy": you never
pass parameters by hand — you stand inside the membranes and they parameterize the formula for you.

## Worked example — X = GRAB, one formula, two objects

| atom | pin (params from its genome) | bowling ball (params from its genome) |
|---|---|---|
| REACH | to a point | to a wide surface |
| GRIP | pinch, 2 fingers, ~1 N | power grip, both hands, ~40 N |
| BRACE | none | brace core for 7 kg |
| LIFT | wrist | whole arm |

Same state machine. The *only* difference is the right two columns — and those come straight from
the object's typed-brick genome (`size`, `mass`, `shape`). Write GRAB once; every object parameterizes it.

## How this trains

Each **formula is a trainable state machine** — a goal-conditioned, context-conditioned policy: the
button is the goal, the membrane parameters are the observed/told context. The **atoms are the shared
network representation** — learning STEP for walking also serves it for sprinting and vaulting. So
**this map IS the training curriculum**, organized by controller: train the atoms, compose the
formulas, condition on the membranes.

## Build order (the story picks the buttons)

You don't build all 12 at once. The **story** — the first world the player lands on — decides which
buttons matter first, and that fixes the first atoms:

1. **Left Stick (MOVE)** → atoms BALANCE, STEP, PLANT, RECOVER. *← we are training BALANCE right now.*
2. **A (JUMP/TRAVERSE)** → LAUNCH, ABSORB — over terrain and gravity.
3. **X (GRAB)** → REACH, GRIP, BRACE — the arms wake up; objects hand over their parameters.
4. **B (CROUCH/LOW), RT (THROW/STRIKE)** → SWING, PUSH.
5. Acrobatics (mantle, climb, cover) → fold in via AMP + motion data.

The 290-muscle body learning to **balance** — training as you read this — is literally rung 1, atom 1,
button 1.
