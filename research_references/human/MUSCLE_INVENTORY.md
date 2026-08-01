# THE MUSCLE INVENTORY — every muscle that moves the human, what it does, why it exists

> Built 2026-07-31 on the operator's directive: **"for the human body we need to know, for
> all the muscles that move the human body, which ones do what and why do they exist."**
>
> Ground truth: the engine's own models in `external/myo_sim/` (Apache 2.0, verified
> 2026-07-30). The myobody carries **290 muscle-tendon actuators**; the separate myoarm adds
> the 25 shoulder/elbow muscles and myohand the 39 wrist/hand muscles. Every name below is
> the name in our XML; the measured parameters (F₀, optimal fibre length, pennation, tendon
> slack) live beside them in `leg/assets/myolegs_muscle.xml`, `torso/assets/`,
> `arm/assets/`, `hand/assets/`.
>
> Sources (the college-paper rule): **Neumann, *Kinesiology of the Musculoskeletal
> System*** (the standard textbook, per-muscle actions); **Ward et al. 2009** (measured
> cadaver architecture); **Rajagopal et al. 2016** (the leg model ours is built from);
> **Saul et al. 2015** (the arm); **Christophy et al. 2012** (the lumbar spine musculature);
> **Caggiano et al. 2022** (MyoSuite). Per-muscle "why" = its mechanical job in gait,
> posture, or manipulation — the reason the body pays for it, per the kinesiology
> literature. Model names map to anatomy one-to-one unless noted (compartment splits are
> modeling choices, marked as such).

---

## 1. THE LOWER LIMB — the gait engine (80 actuators, 42 names, both legs)

Walking is the proven membrane; every leg muscle below has a measured role in the gait
cycle (Van Criekinge 2023, in repo). Gait-phase roles: LOADING (heel strike → flat foot),
MIDSTANCE, PUSH-OFF (terminal stance), SWING.

### Hip — the pelvis engine

| muscle (engine name ×L/R) | what it does | why it exists |
|---|---|---|
| **Gluteus maximus** (glmax1, glmax2, glmax3 — 3 compartments) | hip extension, external rotation; the biggest muscle in the body (F₀ largest in the leg model) | the anti-gravity extensor: fires at LOADING to accept body weight onto the leg and stop the trunk pitching forward. Humans' enormous glmax (vs apes) exists *because* we walk upright — it is the bipedalism muscle |
| **Gluteus medius** (glmed1-3) | hip abduction; anterior compartment internally rotates, posterior externally | **theBalance's prime mover**: in single-leg stance it alone stops the pelvis dropping toward the swing side (its failure = Trendelenburg gait). Lateral stability the gait membrane needs sideways |
| **Gluteus minimus** (glmin1-3) | abduction + internal rotation, under medius | fine-tunes the same frontal-plane balance; its deep position gives it a stabilizing moment arm at all hip angles |
| **Tensor fasciae latae** (tfl) | hip flexion + abduction + internal rotation via the IT band | tensioner of the lateral fascia: stiffens the whole lateral thigh as a column during stance — a muscle that exists to preload a ligament |
| **Piriformis** (piri) | external rotation (extended hip), abduction (flexed hip) | one of the deep-six rotators: holds the femoral head centered in the socket while big movers torque — a guidance muscle, not a power muscle |
| **Iliacus + psoas** (iliacus, psoas — the iliopsoas) | the primary hip flexor; psoas also side-flexes the lumbar spine | swings the leg forward in SWING and pulls the trunk upright when lying/sitting. The only muscle connecting spine→pelvis→femur: the postural bridge between trunk and leg |
| **Pectineus/adductor brevis** (addbrev) | hip adduction + flexion assist | pulls the swing leg back to the midline — walking is a narrow-track activity and the adductors keep the feet on it |
| **Adductor longus** (addlong) | adduction, flexion assist | same track-keeping, longer lever |
| **Adductor magnus** (addmagProx, addmagMid, addmagIsch, addmagDist — 4 compartments) | the workhorse adductor; ischial compartment is a powerful hip EXTENSOR | two muscles in one skin: front = adductor/flexor, back = a fourth hamstring. Exists because the medial thigh must both narrow the gait track AND extend the hip under load |
| **Gracilis** (grac) | hip adduction + knee flexion/internal rotation | the long guy-wire of the medial thigh; knee-level internal-rotation control during stance |

### Knee — the hinge that must also lock

| muscle | what it does | why it exists |
|---|---|---|
| **Rectus femoris** (recfem) | knee extension + hip flexion (two-joint) | the only quad crossing the hip: couples trunk-forward motion into knee extension. Fires in SWING (hip flex + knee control) and LOADING |
| **Vastus lateralis/medialis/intermedius** (vaslat, vasmed, vasint) | pure knee extension; the largest force producers after glmax | the weight-acceptors: they catch the body at LOADING (knee flexes ~20° under load and the vasti eccentrically brake it). Vasmed's oblique fibres keep the kneecap tracking straight |
| **Biceps femoris long head** (bflh) | knee flexion + hip extension (two-joint hamstring) | brakes the swing leg before heel strike (eccentric — the classic hamstring-injury moment) and drives hip extension in propulsion |
| **Biceps femoris short head** (bfsh) | knee flexion only | pure knee flexor without hip coupling: lets the knee flex while the hip extends (standing on one leg and lifting the other) |
| **Semimembranosus/semitendinosus** (semimem, semiten) | knee flexion + hip extension + internal rotation | the medial hamstrings: balance bflh's lateral pull so flexion happens without twisting the knee |
| **Sartorius** (sart) | hip flexion + abduction + external rotation, knee flexion — the tailor's muscle | longest muscle in the body; a two-joint strap that coordinates the cross-legged posture — fine positioning of the leg, not power |

### Ankle & foot — the rocker (theAnkle's muscles, BUILT membrane)

| muscle | what it does | why it exists |
|---|---|---|
| **Soleus** (soleus) | ankle plantarflexion, one joint, huge F₀, slow-twitch | **the postural muscle par excellence**: always on when standing — you stand on your soleus. In gait it eccentrically controls the shank's forward roll over the foot (MIDSTANCE), the rocker theAnkle derived |
| **Gastrocnemius lateral/medial** (gaslat, gasmed) | plantarflexion + knee flexion (two-joint), fast-twitch | the push-off engine: fires at PUSH-OFF with the Achilles tendon returning stored elastic energy (H§2.3 — why walking is cheap). Crosses the knee so it borrows knee angle for power |
| **Tibialis posterior** (tibpost) | plantarflexion + inversion; holds the medial arch | the arch's dynamic ligament: without it the foot collapses flat (its failure = adult flatfoot). Midfoot stiffness for push-off |
| **Fibularis longus/brevis** (perlong, perbrev) | eversion + plantarflexion assist | lateral stabilizers of the ankle: resist the inversion roll that sprains ankles; perlongus also braces the arch transversely |
| **Tibialis anterior** (tibant) | dorsiflexion + inversion | lifts the toes in SWING so the foot clears the ground (its failure = foot drop), and eccentrically lowers the foot after heel strike — the silent foot-slap preventer |
| **Extensor digitorum/hallucis longus** (edl, ehl) | toe extension + dorsiflexion assist | toe clearance with tibant; ehl extends the big toe for the final toe-off roll |
| **Flexor digitorum/hallucis longus** (fdl, fhl) | toe flexion + plantarflexion assist | grip the ground at PUSH-OFF; fhl under the big toe carries the last of body weight off the ground |

## 2. THE TRUNK — the stability tower (~170 actuators)

The spine is a stack of blocks standing on a pelvis; it cannot be stable passively, so it is
guy-wired. The torso musculature (from Christophy 2012's lumbar model) exists almost
entirely for **stiffness and pressure**, not movement — this is theBalance's deep layer.

| muscle (engine names) | what it does | why it exists |
|---|---|---|
| **Rectus abdominis** (rect_abd) | trunk flexion; the six-pack | flexes the trunk forward and, more importantly, pressurizes the abdomen against the spinal extensors — the front wall of the pressure cylinder |
| **External oblique** (EO1-EO6 — 6 fascicles) | trunk flexion + contralateral rotation + lateral flexion | the diagonal guy-wire: rotation control while walking (arms and legs counter-rotate the trunk every step — EO/IO manage that twist) |
| **Internal oblique** (IO1-IO6) | trunk flexion + ipsilateral rotation | EO's mirror: together they make rotation symmetric and cinch the abdominal wall like a corset |
| **Iliocostalis** (IL_L1-4, IL_R5-12 — 12 fascicles, lumbar + thoracic) | spinal extension + lateral flexion, outermost extensor | longest lever of the extensors: coarse extension power (lifting, standing up straight) |
| **Longissimus** (LTpL_L1-5, LTpT_R4-12, LTpT_T1-12 — 17 fascicles) | spinal extension + lateral flexion, middle layer | the main erecting cable: holds the trunk against gravity all day (theSweep measures its metabolic cost) |
| **Multifidus** (MF_m1-5 × laminar/superficial/transverse — 15 fascicles) | segmental spinal extension + rotation, deepest layer, spans 2-4 vertebrae each | **the fine stabilizer**: controls each vertebra individually — posture at joint resolution. Its atrophy is the strongest imaging correlate of back pain (the measured reason it exists) |
| **Psoas spinal portions** (Ps_L1-L5 × TP/VB/IVD — 11 fascicles) | lumbar lateral flexion + vertical compression | pre-compresses the lumbar column so it buckles less under load — a spine pre-tensioner |
| **Quadratus lumborum** (QL_ant/mid/post — 16 fascicles) | lateral flexion + "hip hiking" | lateral balance of the pelvis from above: in gait it lifts the swing-side pelvis so the foot clears (works opposite gluteus medius, which holds from below) |

## 3. THE SHOULDER & ARM — the positioning system (myoarm, 25 muscles ×L/R)

The shoulder trades stability for the largest range of any joint — so it needs a dedicated
muscle class (the cuff) whose only job is holding the ball in the socket.

| muscle (engine name) | what it does | why it exists |
|---|---|---|
| **Deltoid, 3 heads** (DELT1 ant, DELT2 mid, DELT3 post) | arm elevation: flexion/abduction/extension | the prime mover that lifts the arm; three heads because the shoulder moves in every direction and one line of pull cannot cover a sphere |
| **Supraspinatus** (SUPSP) | initiates abduction, compresses the humeral head into the socket | rotator cuff #1: starts the lift the deltoid can't start cleanly, and centres the ball while it moves |
| **Infraspinatus + teres minor** (INFSP, TMIN) | external rotation | cuff #2/#3: externally rotate and depress the head — without them the humeral head rides up and impinges (the measured impingement mechanism) |
| **Subscapularis** (SUBSC) | internal rotation | cuff #4: the front wall; balances INFSP so the head stays centred |
| **Pectoralis major** (PECM1-3 — clavicular/sternal/costal) | arm flexion + adduction + internal rotation | the climbing/throwing power muscle: pulls the arm across the body — the push of a push-up |
| **Latissimus dorsi** (LAT1-3) | arm extension + adduction + internal rotation | the pull of a pull-up; connects arm→spine→pelvis, the body's longest power path — climbing and crutch-walking both load it |
| **Teres major** (TMAJ) | extension + adduction assist | "lat's little helper": same job, shorter lever |
| **Coracobrachialis** (CORB) | flexion + adduction assist | fine positioning of the raised arm |
| **Biceps long/short head** (BIClong, BICshort) | elbow flexion + forearm supination + weak shoulder flexion | the supinator-flexor: turns a doorknob and brings hand to mouth. Long head's tendon crosses the shoulder — a second stabilizer for the joint |
| **Brachialis** (BRA) | pure elbow flexion | the workhorse flexor: works at every forearm rotation (biceps weakens when pronated — brachialis exists so flexion never depends on wrist angle) |
| **Brachioradialis** (BRD) | elbow flexion in mid-rotation | the hammer muscle: strongest flexor with a neutral grip — carrying things |
| **Triceps long/lateral/medial** (TRIlong, TRIlat, TRImed) | elbow extension; long head also extends the shoulder | pushing and punching; long head crosses the shoulder to couple arm drive into elbow drive (throwing, poling) |
| **Anconeus** (ANC) | extension assist | stabilizes the elbow joint capsule during extension — a lock-keeper |
| **Supinator** (SUP) | forearm supination | rotates palm-up without elbow flexion (biceps supinates only while flexing) |

## 4. THE WRIST & HAND — the manipulation system (myohand, 39 muscle-tendon units)

theHand's law is *command the process, not the position* — the hand's muscles exist to
offer every closure direction so the OBJECT can choose which ones it stops.

### Wrist movers

| muscle | what it does | why it exists |
|---|---|---|
| **ECRL + ECRB** (extensor carpi radialis longus/brevis) | wrist extension + radial deviation | extend the wrist for power grips: grip force triples with the wrist slightly extended — these set that angle (measured: grip strength vs wrist angle, NHANES protocol position) |
| **ECU** (extensor carpi ulnaris) | extension + ulnar deviation | balances ECRL/B so extension doesn't drag the hand sideways |
| **FCR + FCU** (flexor carpi radialis/ulnaris) | wrist flexion + deviation | assist finger flexion and brace the wrist during grip |
| **PL** (palmaris longus) | weak wrist flexion, tightens palmar fascia | tensions the palm's skin-anchor — grip without slipping (absent in ~14% of humans, with zero functional loss: the measured redundancy) |
| **PT** (pronator teres) | forearm pronation | palm-down rotation for placing the hand on surfaces |
| **PQ** (pronator quadratus) | pronation, deep | pronation at any elbow angle + compresses the distal radius-ulna joint |

### Finger movers

| muscle | what it does | why it exists |
|---|---|---|
| **FDS 2-5** (flexor digitorum superficialis ×4) | flexes the middle joints of the fingers | the first stage of closure: curls fingers around an object |
| **FDP 2-5** (flexor digitorum profundus ×4) | flexes the fingertip joints — the only muscle that can | completes closure; the grip-force producer whose force the NHANES dynamometer actually measures |
| **EDC 2-5** (extensor digitorum communis ×4) | extends the fingers | opens the hand — every grasp starts with release |
| **EDM + EIP** (extensor digiti minimi, extensor indicis proprius) | independent extension of little/index finger | lets those two fingers point while others stay closed — signalling and tool-aiming |
| **Lumbricals** (LU_RB2-5) | flex the knuckles while extending the fingers | the paradox muscle: sets finger posture for precision handling — writing, threading, not power |
| **Interossei, radial + ulnar sets** (RI2-5, UI_UB2-5) | spread/close the fingers, assist lumbrical posture | finger spacing control: fanning the hand wide (grip large objects) or tight (precision) |

### The thumb — the human specialization

| muscle | what it does | why it exists |
|---|---|---|
| **APL** (abductor pollicis longus) | lifts the thumb away from the palm | opens the C-grip: positions the thumb before opposition |
| **EPB + EPL** (extensor pollicis brevis/longus) | extends the thumb at two joints | thumb release and the "thumbs-up" posture; EPL is the only thumb extensor of the distal joint |
| **FPL** (flexor pollicis longus) | flexes the thumb tip | the power thumb in grip — the pad-to-pad pinch |
| **OP** (opponens pollicis) | rotates the thumb metacarpal to face the fingers | **opposition itself**: the movement that makes a tool-using hand. No other primate's opponens acts with this leverage — this muscle is why the human hand is a manipulator and not a hook |

## 5. WHAT THE MODEL HONESTLY OMITS

- **Neck & head**: myobody's head is rigid (neck_flexion/rotation joints, no neck muscles).
  Sternocleidomastoid, scalenes, splenius, the suboccipitals — exist to balance the ~5 kg
  head over the spine and aim the eyes. Needed when theEye aims: flagged, not modeled.
- **Face, jaw, tongue, eye muscles**: mastication (masseter/temporalis), expression,
  extraocular muscles — out of the locomotion scope; listed so the gap is named.
- **Foot intrinsics**: the 20 small foot muscles (arch fine-tuners) are not in myolegs;
  tibpost/perlong/fdl/fhl carry their gross function. Fine if B1 needs them: gap named.
- **Compartment splits** (glmax1-3, addmag×4, EO×6, MF×15...) are modeling choices that
  capture one muscle's fan of fibre directions — anatomically one muscle, mechanically a
  fan of moment arms. The split IS the "why": coverage of torque directions.

## THE PATTERN — why muscles exist at all

Every row above is one of four mechanical jobs, and there is no fifth:

1. **Prime movers** — torque for propulsion (glmax, vasti, gastroc, deltoid, lat, FDP).
2. **Stabilizers** — hold a joint centred or a column stiff while movers work (rotator
   cuff, soleus in standing, multifidus, piriformis, anconeus).
3. **Balancers** — oppose each other so net motion is straight (hamstrings medial/lateral,
   EO/IO, ECRL/ECU, gluteus medius vs QL across the pelvis).
4. **Couplers** — two-joint muscles that transfer energy between joints (recfem,
   hamstrings, gastroc, biceps, triceps long head): they let one joint's motion power
   another's, which is most of why walking costs so little (H§3.3).

The 290 actuators are these four jobs × every joint direction × redundancy for failure.
That is the complete answer to "why do they exist": each is a measured solution to a
torque-direction, stiffness, or energy-transfer requirement of a body that walks upright,
balances a head, and manipulates objects — and every number for them is already in the repo.
