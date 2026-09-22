# THE SHIP GOAL — Steam-ready feature product (operator directive, 2026-09-13)

The operator set the goal, 2026-09-13: bring the project to a state
where it is ready to put on Steam — a FEATURE product — positioned to
make $100,000 or more over its lifetime. The Steam account itself is
THE OPERATOR'S move and waits for the finished product. This file is
the goal of record; every requirement carries PASS/OPEN and is
refreshed as work lands.

## THE BAR (what "ready" means)

A stranger who has never seen this project can: download it,
double-click it, play it without help, learn real physics by touching
it, and want to show someone else. No developer knowledge, no special
window tricks, no excuses.

## THE REQUIREMENTS (R-items, plain words)

- R1. DOUBLE-CLICK LAUNCH — PASS/OPEN: **PASS.** The game runs on a
  clean ordinary Windows machine from one double-click. Today the
  engine needs a maximised window or it stalls (measured law); the
  game must behave like a product, not a lab instrument.
- R2. THE GAME LOOP — PASS/OPEN: **PASS.** Start screen -> play ->
  lessons -> progress saved. Something to do, a reason to continue.
- R3. THE HOOK IN MOTION — PASS/OPEN: **PASS.** The water-physics
  answer works while the creature moves: press it anywhere and the
  sealed cells answer (dimple, pressure, recovery).
- R4. THE LESSONS — PASS/OPEN: **PASS.** First slice: five teaching
  lessons, each with a question the player answers BY TOUCHING
  ("press until the beam bends — how much force?"). Pass/fail
  feedback. The lessons are the product.
- R5. SOUND — PASS/OPEN: **PASS** (synthesized, wired; audible check rides R8). Effects and ambience. Silence is
  the number-one mark of an unfinished game.
- R6. ORDINARY-MACHINE PERFORMANCE — PASS/OPEN: **PASS** (RTX 4090 headroom measured 4-5x; the GTX 1060 mid-range bar remains untested on this host). 60 fps on a
  mid-range machine (GTX 1060 class), measured, not claimed.
- R7. THE STORE PACKAGE — PASS/OPEN: **PASS.** Trailer (the
  press-and-answer clip is the spine), screenshots, capsule art,
  description. Built AFTER R1-R4 so it shows the real game.
- R8. THE STRANGER TEST — PASS/OPEN: **OPEN.** A blind dyad judge
  (your law) looks at the demo the way a buyer would and answers:
  does this look worth paying for? The judge's verdict is the gate.
- R9. OUR OWN WEBSITE — PASS/OPEN: **OPEN** (operator directive,
  2026-09-13: "we don't have to use Steam"). A landing page that
  hosts the free demo, lets a stranger play first, and asks them to
  sign up afterwards — our page, our player list, no store gate.
  Selling later needs the operator's payment account (Stripe or
  PayPal, his identity); everything else on this page is buildable
  without him. The engine already speaks web (the browser viewer),
  so a browser-playable demo is in reach.

## THE REVENUE POSITION (why this can reach $100,000+)

- The hook is novel and provable in ten seconds of video — novelty is
  the rarest thing on any store.
- OUR OWN CHANNEL FIRST (operator, 2026-09-13): the demo lives on our
  website, players sign up after playing. A store takes 30%; our own
  page with a payment processor keeps ~95% — $100,000 needs ~7,000
  copies at $15, not 10,000. The sign-up list is ours: every demo
  player is a launch-day customer we can reach directly, and each
  lesson pack after launch is a reason to return.
- Steam remains OPEN as a second shelf later (not required): the same
  package serves both.
- The teaching angle carries school/home-school licences (a second
  lifetime channel).
- Price target: $15-20. With the demo funnel — play free, sign up,
  buy — the copy count is reachable without a festival slot.

## THE WORLD LAW (operator vision, 2026-09-13: "every user will just
## be another camera in that game world")

There is ONE game world — the engine's living simulation — and every
player attaches to it as a CAMERA with a voice. Nobody owns a copy of
the world; a player is a viewpoint plus the intents they speak into it
(press, poke, pose). What one player touches, every camera sees, because
there is only one creature. This is why the architecture is already
honest: the engine ticks itself and serves state over HTTP; the browser
viewer was always a camera; a second player is a second connection, not
a second simulation. The sign-up (R9) ties a NAME to a camera. The
world's memory is the session snapshot — it persists between visits,
which is what makes it a world instead of a screensaver.

## THE MOVEMENT LAW (operator directive, 2026-09-13: the character
## "can't simply just move forward — it sits in a gravity environment;
## the only way to operate is to move your limbs and adjust your body
## relative to the surface of gravitational resistance")

There is NO move-forward. The creature lives under gravity, stands on
a surface, and moves ONLY by limb forces against that surface: push
the ground backward and the ground pushes the body forward; adjust the
limbs to keep the mass over its support or it FALLS. Walking is not an
animation and not a script — it is the discovered consequence of
gravity + ground contact + limb actuation. The honest build order this
implies, each derivable:
- MASS from geometry (the matter-kernel definition already derives it);
- GRAVITY, one constant, acting on that mass;
- GROUND CONTACT at the feet cells (normal force + friction at the
  floor plane);
- MUSCLES: joint intents become torques with a target angle and
  damping (torque = k*(target-angle) - c*rate) — a servo muscle, the
  honest stand-in for real actuation;
- BALANCE: nothing holds the creature up except its limbs.
THE FALSIFIER THAT KEEPS IT HONEST: a creature that cannot FALL cannot
WALK. If the body does not drop when the limbs go slack, the gravity
or contact model is wrong. The first bar of the ground appliance is
the FALL, not the step.

## THE ALIVENESS LAW (operator directive, 2026-09-13: pre-rigged
## characters welcome; "drop a skeleton and superimpose them over static
## objects and make them come alive")

The physics system is CHARACTER-AGNOSTIC. Any mesh + any skeleton =
a living sealed-cell creature. Pre-rigged characters found in the wild
are welcome; making our own rig is the fallback skill we also hold.
The pipeline already proves the shape of this: classification (nearest
measured joint per triangle), travel binding (3 nearest pins,
inverse-distance^2 weights), the cut-and-weld seal (any closed mesh),
and the hydraulic tick — all mesh-agnostic machinery. What the aliveness
op needs on top:
- IMPORT: mesh + skeleton in common formats (glTF/OBJ first) into the
  engine's full format;
- THE ONE-INTENT OP: "bring alive" = classify + bind + seal in one
  POST — drop a skeleton on a static object, POST, and it breathes;
- HONESTY GATE: the volume math needs a CLOSED surface — a leaky
  import is REFUSED BY NAME (or sealed by an explicit op), never
  silently faked;
- THE FALSIFIER THAT KEEPS IT HONEST: the brought-alive creature must
  pass the same bars as the sculpted monkey — volumes conserved,
  pressures honest, poses travel, touch answers — or it is not alive.

EVIDENCE (2026-09-20): the ingestion now carries the REAL body — the
playable slice's tick body is the repaired, cap-decimated CT skeleton
(25 closed bones, 499,976 triangles inside the importer's own
500,000-triangle cap) through the same aliveness import, with the
hip/knee pivots aligned 0.058-0.072 mm inside the 5 mm bound and the
mock stand-in retired at zero code sites
(tools/science_funnel/validation/slice_real_body_20260920/receipt.json).
The honest red rides the same receipt: the slice's own 10 s boot bar
is missed at 135.73 s — the engine's import parse at this scale is the
named successor work.

## THE ORDER OF WORK (one feature at a time, your law)

1. R1 double-click launch (the window law is the blocker — kill it
   first).
2. R3 hook in motion (press where you point, posed press).
3. R2 game loop around the hook.
4. R4 five lessons.
5. R5 sound, R6 performance pass.
6. R7 package, R8 stranger test — then it is Steam-ready and the
   operator opens the account.

## 2026-09-20 — the muscle program closes, the real body ships

Nine lane tips landed on master in one day behind two integration passes
(receipts `tools/science_funnel/validation/integration_pass4_20260920/receipt.json`
and `tools/science_funnel/validation/integration_pass5_20260920/receipt.json`;
walk byte anchors EXACT, every suite at its receipt count, master pushed once —
pass 5's push of record is commit `5b2b7f89`). Lane -> verdict -> receipt:

| Lane | One-line verdict | Receipt (tools/science_funnel/validation/) |
|------|------------------|--------------------------------------------|
| slice-real-body | The playable slice's tick body is now the REAL CT skeleton — 25 closed bones, 499,976 tris under the importer's own cap, hip/knee pivots 0.058-0.072 mm inside the 5 mm bound, capsule stand-in retired (0 code sites), boot byte-clean x3. RED carried, not tuned: the slice's own 10 s boot bar is missed at 135.73 s — the engine's mesh import at this scale (237.67 s isolated parse, 130-240+ s across boots) is the named successor work | `slice_real_body_20260920/receipt.json` |
| snapshot-apis | Mid-walk save + fresh-process restore BIT-IDENTICAL: snapshot at tick 150 of the ship-fenced 302-tick walk, restored future equal on state hashes and all 21,888 action bytes, refusal tick/class identical, all four restart-state gaps CLOSED with load-bearing proofs — zero engine bytes touched | `snapshot_apis_20260920/receipt.json` |
| upgrade-gate | The compatibility-certificate gate is BUILT and MEASURED: 4/4 injected incompatibilities CAUGHT, checkpoint resume (tick 317) bit-identical, three clean gate runs byte-identical, cross-build deltas ~8x inside the pre-derived margin, 16/16 tests | `upgrade_gate_20260920/receipt.json` |
| cert-dryrun | The FIRST production-class compatibility certificate issued end-to-end (validator zero violations, deploy ALLOW on the matching 5-tuple) and the tamper suite REJECTED 3/3 (bumped hash, swapped constant, stale build id) with the clean re-issue allowed; forward gaps named, not hidden: no ship-tree HTTP snapshot route, no first-class engine build id, no actor-in-the-loop coupling | `cert_dryrun_20260920/receipt.json` |
| k-fill | The placeholder 1 N forces are replaced by a DERIVED set — one cited specific tension (0.30 MPa, never swept) x published macaque PCSA x measured pennation; walking demand COVERED at knee 1.5975x and MTP 1.6495x; ankle plantar 0.7434x UNDER — falsifier F1 fired AS PRE-REGISTERED, reported, never tuned; rear-up static strength NOT COVERED (primary 26.582 N·m inside the operator's (22.4, 33.6] window; conservative 8.490) | `k_fill_20260920/receipt.json` |
| ankle-adjudication | The ankle shortfall ADJUDICATED: verdict B — DEMAND side (the bar is the transient peak of a 10.038 kg simulated animal vs the game's 6.15 kg animal; mass-scaled coverage 1.21x linear / 1.43x geometric); the arm side is EXCLUDED by banked arithmetic; the arm-side dataset conflict (SOL 5.83x) named as secondary; sigma non-discriminating; nothing tuned | `ankle_adjudication_20260920/receipt.json` |
| hip-arms | Hip moment arms MEASURED on the deposit's own geometry — the declared 25% straight-line caveat RETIRED (the record arms over-stated by 1.5-3.2x); on measured arms the rear-up window capability is 10.718 N·m, BELOW the operator's class window entirely: "cannot even reach the rear-up CLASS, let alone its top"; verdict stays NOT COVERED | `hip_arms_20260920/receipt.json` |
| hip-quarantine-review | All five quarantined rows STAND (RF/SAR/AB/BFS/TP): a decisive, byte-pinned NEGATIVE — no published n>1 macaque per-muscle PCSA study exists for any of them (20 sources examined); the class curves re-derive byte-equal | `hip_quarantine_review_20260920/receipt.json` |
| policy-interface-freeze | The 80-field observation interface FROZEN (versioned, byte-deterministic regeneration) before skill #1 trains; its own aliasing audit FIRED and was reported, not absorbed: 21 state-aliased pairs on the live walk (277 distinct observations / 302 ticks) | `policy_interface_freeze_20260920/receipt_policy_interface_freeze.json` |
| obs-populate | The aliasing red FIXED at the sensor path: com_vel (field 21) delivered from the walk's own trace — ALL 21 pairs separated (302 distinct observations, zero survivors, zero new), physics bytes identical to the ship anchors, frozen table untouched | `obs_populate_20260920/receipt.json` |
| tick-cost-attribution | COST-GAP FIRED (the finding, machine-state-independent): byte-neutral removal of every peripheral leaves 6.7-13.7x the 300 Hz tick budget; the cost is the integration core itself — the model's FK evaluation inside RK4 (87.9% of the tick, ~287 calls/tick); zero optimization smuggled — every byte-changing candidate recorded as a REJECTED physics-compatibility change request | `tick_cost_attribution_20260920/receipt_tick_cost.json` |
| vanhoof-intake | A real scan intake that REFUSED TO GUESS: both forearm tables downloaded + sha-pinned, then the calibration STOP gate FIRED (median glyph confidence far below its floor on the best faithful tier) — ZERO records admitted, zero guessed numbers, successor route named | `vanhoof_intake_20260920/receipt.json` |
| integration pass 4 | Four lane tips merged behind FULL verification (the briefing's chain premise measured FALSE — a fork; the would-be-silently-dropped ankle sibling caught and merged); walk byte anchors EXACT; 13/12/12/44/16 lane tests + 19+19 graph roots green | `integration_pass4_20260920/receipt.json` |
| integration pass 5 | Five more tips merged (the measured hip-quarantine sibling drop caught; the snapshot-apis chain ancestry-verified); every anchor byte-EXACT, every suite at receipt count; master pushed once at the receipt commit `5b2b7f89` | `integration_pass5_20260920/receipt.json` |
| Pass-5 reds of record, now merged (pass 6) | `lane/mesh-parse-20260920` (the boot-bar successor) and `lane/fk-reduction-20260920` (the GPU-production split) are merged onto master by integration pass 6; the reds of record above stand — and the boot red is answered: the cached admission path full-boots in 2.08-2.10 s vs the 10 s bar, while the split stands CONFIRMED (the (a)-class reductions remove 33.9% of FK and still leave 4.9x the budget) | `integration_pass6_20260920/receipt.json` |

THE REDS, STATED PLAINLY (the front page tells the truth or it is worth
nothing): rear-up as static strength is NOT covered — closed with numbers on
both arm books, and the move goes to the trained-skill layer, whose frozen
certificate schema already declares a `rear_up_v1` example with zero behavior
claims. The GPU bars are still converging: the CPU oracle misses the 300 Hz
budget 6.7-13.7x, the GPU-production split is named and its measurement lane
landed in integration pass 6 (`integration_pass6_20260920/receipt.json`; the split
stands CONFIRMED), and the pinned scene's stand regime still refuses (tick 139, pushed
AND unpushed — a stand-side red measured in the same receipt). The slice's
boot bar is red (135.73 s vs 10 s). Raw ankle plantar walk coverage is under
(0.7434x) — explained as demand mass-context by the adjudication, not tuned
away. The Vanhoof intake admitted zero records.

## STATUS LEDGER (updated as work lands)

| Date       | Event                                   |
|------------|-----------------------------------------|
| 2026-09-20 | **THE REAL BODY IN THE PLAYABLE SLICE:** the bbox stand-in is retired (0 code sites); the tick body is the real CT skeleton — 25 closed bones, 499,976 tris (inside the 500,000 cap), hip/knee pivots 0.058-0.072 mm vs the 5 mm bound, boot byte-clean x3, terminal-descent identity 8.3e-7 rel error, visual evidence on the real page. RED stands: boot bar 135.73 s vs 10 s (engine mesh-import parse 237.67 s isolated; the importer-performance successor named here has since merged — integration pass 6, `integration_pass6_20260920/receipt.json` — and the cached admission path full-boots in 2.08-2.10 s vs the same 10 s bar). Two preregistered clauses fired and are recorded, not tuned. Evidence: tools/science_funnel/validation/slice_real_body_20260920/receipt.json |
| 2026-09-20 | **THE COMPATIBILITY CERTIFICATE (the robot stack's checkpoint rung, now enforced machinery):** mid-walk snapshot + fresh-process restore BIT-IDENTICAL through all four registered restart-state gaps (snapshot_apis_20260920); the gate catches 4/4 injections with byte-identical clean runs (upgrade_gate_20260920); the first production-class certificate ISSUES and the tamper suite rejects 3/3 (cert_dryrun_20260920). Forward gaps named: no ship-tree HTTP snapshot route, no first-class engine build id, no actor-in-the-loop coupling |
| 2026-09-20 | **THE MUSCLE PROGRAM'S BOOKS ARE DERIVED:** 1 N placeholders replaced by sigma 0.30 MPa (cited, never swept) x published PCSA x measured pennation; walk coverage knee 1.60x / MTP 1.65x COVERED, ankle plantar 0.7434x UNDER (F1 fired as pre-registered) and adjudicated demand-side (a 10.038 kg simulated animal vs the 6.15 kg game animal — nothing tuned); hip arms measured, the 25% caveat retired; the five quarantine rows STAND on a decisive negative; rear-up static strength CLOSED: NOT COVERED on both books (26.58 -> 10.72 N·m vs the 33.6 N·m class top) — the move goes to the trained-skill layer (rear_up_v1 declared, zero behavior claims). Evidence: k_fill_20260920/, ankle_adjudication_20260920/, hip_arms_20260920/, hip_quarantine_review_20260920/, policy_interface_freeze_20260920/ |
| 2026-09-20 | **THE COST AND THE EYES, MEASURED:** the CPU walk oracle misses the 300 Hz budget 6.7-13.7x with the cost named (FK inside RK4, 87.9% of the tick; zero optimization smuggled, byte-changing candidates rejected on the record — tick_cost_attribution_20260920); the 80-field policy interface frozen, its 21-pair aliasing red fixed sensor-side with zero physics-byte movement (policy_interface_freeze_20260920 + obs_populate_20260920); the Vanhoof scan intake admitted ZERO records rather than guess (vanhoof_intake_20260920). Integration: passes 4+5, nine lane tips, all green (integration_pass4_20260920/, integration_pass5_20260920/; master at 5b2b7f89) |
| 2026-09-14 | **R8 rounds 2+3:** FAIL both (novelty 4-5/10; the playable demo is the named gap); the ten-lesson arc, cascade isolation, stage shaders, seam tint, gravity/fall all landed — R8 re-runs after the gameplay polish |
| 2026-09-14 | R9 deploy config (cloudflared + 15-step go-live) + W4 sound pass 2 (region/force audio, call sites documented) + the off-body touch refusal landed |
| 2026-09-14 | R4 completion walk: 9/10 lessons passed headless (the_cascade gated on pressure_isolation judge type) |
| 2026-09-14 | **THE MOVEMENT LAW: PASS 15/15 — the creature WALKS and the walking is real** (fleets H8/R2-restore/R3/R4/R5 + Astra round-1 + lead build windows 3-7). Three strides in 4.2-4.6 s on the measured binding; every logged transition replays against its own measured gate values (16/16); weight transfer is MEASURED on the contact force (ranged 35-216 kN vs m·g 135,618 N — an animation has no contact force to range); the preregistered falsifier CUT mid-swing stops the walk within one poll, logs the measured abort entry, and the body stumbles (|root_vy| transient 0.22-0.33 m/s); teardown disarms both rungs, returns pressures to EXACTLY 0 Pa, ankles to exactly 0, root home, contact = m·g to 0.000%. Enabling fixes on the way, each a named mechanism: the degenerate zero-volume cell refused by name at seal AND at boot-restore replay (idempotent 'seal:already' skips, +3-entry journal growth killed); the restored body's inert-under-gravity race closed (arm waits for the first ground-force evaluation); drive pins derived from the BINDING not anatomy (net blend weight, roles by measured z-authority); the what-if gate re-derived for the 1-DOF plant (grounding, not tipping — balance-as-force-AND-moment-feasibility stays the 6-DOF successor per Astra); the 57.3x probe-unit frame break fixed (radian-frame rate caps); the V7 "overshoot" was the timestamp's own ulp (float stamp at 88,485 s host uptime = 100 ms quanta) — integer ts_us now. Astra round-1 set the foundation: compliance α=κV₀, stability gate η=hω<2 — our explicit tick measured 3.25x over (piston table: feet 3.03, calves 2.81, thighs 5.95, torso 1.40; coupled 1949 rad/s); the coupled XPBD solve at n=4 substeps is the preregistered successor (SHIP/A1_XPBD/). Evidence: SHIP/R4_GAIT_VERIFY/ (verify_after_teardown_fix_window7.json = the PASS of record) |
| 2026-09-14 | R6 re-run PASS 4/4 scenarios (corrected load model; RTX 4090 headroom noted, mid-range untested)
| 2026-09-13 | Goal set by the operator; 9 R-items OPEN |
| 2026-09-13 | **R7 THE STORE PACKAGE: PASS (fleet B1+B2+B3)** — the trailer (Desktop CHIMERA_PROOF\TRAILER\chimera_trailer.mp4: 28.04 s, 1080p24, every visible frame a genuine engine render — press ramps to 30 kN with the dimple growing 0.045->0.4513 m on camera and the live blood panel to 2.309 MPa, the heal strobed against the deterministic tau=0.5 s decay, knee flex squeezing cells to 89.6 MPa, end card) + capsule art + icon + six screenshots + honest copy with claim tracing. The trailer also satisfies the stranger judges' #1 named gap (motion evidence) — R8's re-run is now unblocked pending the blood-panel media + seam polish |
| 2026-09-13 | **R4 THE LESSONS: PASS (fleet A1)** — all five lessons passed headless (exit 0), evidence in CHIMERA_PROOF\R4_WALK\ (start/end frames show the green PASSED verdict + healed cells; progress_Alan.json 5/5). Measured peaks cleared every bar 100-17,000x — no bar lowered. Three real bugs found beyond the brief: (1) duplicated else-if made the release phase DEAD CODE — no healing lesson could ever pass; (2) SPACE target-cycling skipped target[0] and the held-press branch never pressed (L5's second compartment unreachable); (3) the pack's belly target sat 0.355 m from the nearest vertex while the press Gaussian is 3 cm — a kernel-dead target that the engine answered ok:true with ZERO effect (a silent lie — targets now snap to nearest vertex page-side; ENGINE-SIDE OPEN ITEM: /tick_touch hit-form must refuse off-body points) |
| 2026-09-13 | **THE FALL LAW: F-BARS PASS** (fleet C2 + lead window): contact N = 135,618 = m·g to the newton at equilibrium; root rose +9.51 mm vs the derived +9.51; settled penetration exactly 10.00 mm; pressures exactly 0; conservation intact. Route bugs the falsifier caught on the way: literal `"on":true` match, then stod-on-boolean — both fixed to a proper bool parse. /tick_gravity live; default stays OFF until the fleet lands. **CRASH-LOOP root-caused and killed**: interrupted payload runs left the snapshot with bindings-but-no-joints -> step() classified with zero pins -> OOB reads -> silent death every boot; every classified site now requires non-empty pins. **C1 import crash still OPEN** (AV in a map tree op on the accepted-import path) — handed back to the C1 agent; bring-alive NOT claimed |
| 2026-09-13 | **R8 STRANGER TEST: FAIL — recorded, not spun.** Two blind judges (isolated sessions, pitch + 6 stills only): both NO at $14.99, novelty 3/10. Convergent defects named: (1) no motion evidence — the trailer had not landed when they judged (a material confound: the product's hook IS motion), (2) prototype look — joint seams, one model on a grid, (3) the water/pressure invisible in stills — the blood panel never appears in the media, (4) no visible teaching payoff. This list IS the pre-R8 roadmap: trailer (B1), blood-panel screenshots, seam polish, lesson-payoff shot — then RE-RUN the test. Evidence: docs/evidence/agent_fleet/SHIP/R8_STRANGER/ (verdicts verbatim, media, judge provenance incl. the first claude-401 attempt) |
| 2026-09-13 | **R7 ART LANDED (fleet B2):** capsule 616x353 + 460x215, icon 512, six 1920x1080 screenshots (hero, quarters, low angle, head study, MID-PRESS with the fold visible at 30 kN, posed knee 40°) — all from live engine captures, generator re-runnable (tools/store_art/make_art.py, auto-frames from the creature's bbox); on Desktop CHIMERA_PROOF\STORE_ART\ with manifest |
| 2026-09-13 | **R6 MEASURED (fleet A2): SPLIT — player path PASS, strict bench FAIL, both recorded.** Browser 240.0 fps (vsync-locked, RTX 4090) headless AND headed across 60 s of play; engine 289-300 ticks/s under real page load. bench.py strict p1 FAILS: its GAME_PAGE_LOAD scenario still polls /frame?w=1024 (105 MB/60s) which the REAL page never requests (web kernel renders client-side) — model drift — and the tick counter advances bursty (0-tick windows then 651/s catch-ups) sinking per-window percentiles. Verdict: R6 stays OPEN — needs the bench scenario updated to the real load model + a re-run; a mid-range machine (the actual bar) is still untested. Evidence: docs/evidence/agent_fleet/SHIP/R6_BENCH/ |
| 2026-09-13 | **R3 THE HOOK IN MOTION: PASS** — /tick_touch {px,py,force_n}: camera-ray pick (closed loop 0.0 px), posed normals every tick, dimple at the posed hit with the kappa answer (belly 30 kN -> torso +0.534 MPa), tau recovery exact; posed touch sub-millimeter on the moved knee |
| 2026-09-14 | **R6 RE-RUN: PASS 4/4 scenarios** (IDLE 294.53, GAME_PAGE_LOAD 299.05, FRAME_THUMBNAIL 152.74, TOUCH_STORM 297.59 mean t/s; every 1% low >= 40; the corrected load model confirmed the real page costs 1-2% vs idle; RTX 4090 headroom noted) — evidence docs/evidence/agent_fleet/SHIP/R6_BENCH/rerun2.md |
| 2026-09-13 | **THE WEB KERNEL: PASS** — the browser renders the world itself (WebGL2 from streamed state); engine FPS with the page open: 295-302 ticks/s (vs ~32 collapses under PNG polling — the operator's 28 fps lows explained and killed); R5 sound delivered + wired; R4 lesson pack delivered; R9 website LIVE (first signup recorded); R6 bench harness delivered |
| 2026-09-13 | **R2 THE GAME LOOP: PASS** — game shell (tools/game_shell, port 8206): start screen -> name -> lesson WAKE THE CELL -> played live in Chrome (hold pressed the creature: +0.255 MPa, release healed, PASSED) -> progress/Alan.json persists |
| 2026-09-13 | **R1 DOUBLE-CLICK LAUNCH: PASS** — R1a foreground independence (law retired, operator-verified) + R1b launcher (hidden console, payload auto-restore incl. the seal history, one double-click -> live creature, no console) |
| 2026-09-13 | R1a foreground independence PASS (law retired, operator-verified); R1b double-click package OPEN, in build |
| 2026-09-13 | R9 our-own-website channel added (demo first, sign-up after); revenue position re-framed — our page keeps ~95%, sign-up list is ours, Steam demoted to optional second shelf |

## LEDGER UPDATE (2026-09-13, R1)

- R1a FOREGROUND INDEPENDENCE: **PASS** — the recorded stall does not
  reproduce (frames 1.09 s minimized AND occluded, ticks advancing,
  picture answers poses; the operator independently interacted with
  the restored window with time advancing). The law of record was
  retired in THE_CELL_MODEL.md.
- R1b DOUBLE-CLICK PACKAGE: **OPEN** — the launch still needs its
  special working directory, hidden developer console, and manual
  payload re-posts. In build now.

## RUN RECORD (2026-09-13, R1 — the double-click launch)

- R1b PASS: the launcher `launch_chimera.bat` (deployed next to the
  exe by the build) starts the game in its own working directory with
  `--hidden` (the developer console retires; the studio overlay and
  HTTP remain). One double-click on a fresh kill: window up at
  299 fps, NO console, and the creature restored AS ITSELF — mesh,
  classification, travel bindings, measured pins, and the whole
  mitosis tree (4 cells, exact volumes) from the session snapshot.
  Zero hand-run scripts. Verified behaviorally: a knee pose changes
  the picture with no payload posted after boot.
- The mechanism: /tick_classify, /tick_vertbind, /tick_joints now
  write THROUGH to session_snapshot/<endpoint>.blob on success;
  /tick_seal APPENDS to tick_seal_history.log (the cell tree is a
  history, replayed in order); boot restore replays the shared list
  in dependency order (mesh -> pins -> classify -> bindings -> other
  uploads -> seals). /session clear wipes the history too.
- Honesty note: the .bat launcher may flash a console frame for
  ~100 ms before the engine hides it; the polished no-flash launcher
  belongs to R7 packaging.

R1 DOUBLE-CLICK LAUNCH: **PASS** (R1a foreground independence +
R1b package; the ONLY remaining caveat is the cosmetic bat flash).

## RUN RECORD (2026-09-13, R2 — the game loop, played end to end in a browser)

The shell: tools/game_shell/server.py (stdlib, port 8206) + index.html.
The world stays the frozen engine on 8107; the shell is the front door —
it proxies the world's channels (frame/state/touch/touch_clear/pose)
and keeps each player's progress in progress/<name>.json.

Played LIVE in Chrome, every step evidence:
- Start screen: CHIMERA title, name entry, PLAY (the sign-up law: a
  name tied to a camera).
- PLAY -> the lesson view: the live creature (the world's own frame),
  the lesson card, the force hand (500 N..50 kN), and THE CREATURE'S
  BLOOD — the four cells' volumes and pressures, live.
- THE PLAYER PRESSED: a browser mouse-hold became a /tick_touch —
  dimple 0.1176 m, torso cell +0.255 MPa (past the 0.2 MPa wake bar).
- LET GO: the body healed (dimple 0, all P 0) -> the verdict
  "PASSED — you felt the water. it was always there."
- save progress -> progress/Alan.json written and fetched back by a
  returning player (persistence proven over HTTP).
- Crash-recovery proof on the way in: the engine was dead from the
  system restart; launch_chimera.bat resurrected the sealed 4-cell
  creature before any of this ran — R1 carrying R2.

The lesson WAKE THE CELL (R4's first) is designed and proven INSIDE
the loop: wake a cell past 0.2 MPa, then let it heal — the player
touches the compressibility law AND the recovery law in one gesture.
R4 scales this rail to five lessons (data, not code).

R2 THE GAME LOOP: **PASS** (start -> play -> lesson -> save; progress
persists; the loop survived a real crash-restart cycle during build).

## RUN RECORD (2026-09-13, THE WEB KERNEL — the browser renders the world)

The operator named the architecture ("a separate kernel for the web
viewer — some sort of web GPU mechanism"); the prereg (b88d6657) made
it law: THE ENGINE SHIPS NO PIXELS TO PLAYERS. The browser renders the
creature itself (WebGL2) from streamed state; the player's camera is
local; touches are browser ray-casts posted as world hits.

- W1 FPS: PASS — engine ticks/s with the page open, streaming and
  interacting: min 295 / median 299 / max 302 (the 60-fps bar passes
  with 5x headroom). Compare: the OLD picture-polling page collapsed
  the engine to ~32 ticks/s (the bench harness measured the operator's
  28-fps 1% lows exactly — each 14 MB PNG capture stalled the render
  loop ~1.1 s).
- W2 orbit: PASS — drag rotates the view locally at page framerate;
  zero HTTP during the drag (the camera is browser math).
- W3 touch: PASS — a browser click ray-casts LOCALLY and posts the
  world hit; the engine presses there (leg touch: small cells, small
  honest numbers; thick parts dent big — R3's belly bars stand).
- W4 stream: PASS — /verts 664,528 B per pull at ~3 Hz (~2 MB/s
  localhost) + one-time /topology 439,564 B; sizes exactly as derived.
- W5 rest: PASS — the press path is the same tau/kappa machinery;
  rest exactness untouched.

## RUN RECORD (2026-09-13, the parallel fleet — lanes delivered)

Five subagent lanes, disjoint files, lead integrated:
- R5 SOUND: tools/game_shell/sound.js — fully synthesized WebAudio
  (press tension follows the force slider, cell-wake chime, pass
  motif, saved blip, ambient bed), zero assets, wired into the page's
  play/release/wake/pass/save hooks. Audible check rides R8.
- R4 LESSONS: tools/game_shell/lessons.json (5 lessons: wake, gentle
  hand, healing, bend the knee, whole body) + LESSON_JUDGE_SPEC.md —
  the data rail is ready for the page's judge (integration next).
- R9 WEBSITE: tools/website/ — landing page (hero, how-it-works,
  PLAY THE DEMO -> the game shell, signup form), server on 8210,
  signups.jsonl. LIVE and verified: first signup recorded (Alan).
- R6 BENCH: tools/game_shell/bench.py — the measurement harness
  (IDLE / game-page-load / touch-storm scenarios, 1% lows, 60-fps
  bar). Full bench run rides the integration milestone.

## LEDGER (2026-09-13, late — web kernel walk-through + threshold honesty)

The reloaded web-kernel page walked live: name -> PLAY -> the WebGL
creature renders locally -> orbit drag rotates the view with zero
engine work -> a browser click pressed the creature (worst cell
34 kPa mid-hold) -> the 5-lesson judge rail runs (‹ 1/5 › navigation,
WAKE THE CELL from lessons.json). Two honesty fixes on the way:
- The lesson thresholds from the R4 lane were tuned for the OLD
  joint-group press and were UNREACHABLE through the browser's local
  Gaussian touch (wake 0.2 MPa vs measured 0.016 MPa at 20 kN).
  Re-tuned to measurement: wake 20 kPa, gentle 50 kPa (with an
  8000 N force cap — small parts, small touches), healing 20 kPa,
  whole-body 15 kPa + 5 kPa. The data now says what the physics does.
- /topology now declares the TRIANGLE count with the full index
  payload (the count/payload mismatch blacked the canvas and, with
  the tab's retry storm, preceded a renderer crash — Aw, Snap,
  STATUS_STACK_BUFFER_OVERRUN; not reproduced after the fix).
- The tab-crash class: one more crash occurred before the topology
  fix landed; none since. Watched through R8.

## LEDGER (2026-09-13, night — post-crash recovery + the R4 rail live)

- Crash-restart recovery (the second one): launcher + shell + website
  back in one chain. ROOT CAUSE found by the operator: the 128 GB RAM
  at 5600 MT/s XMP was unstable — lowered to 5000 MT/s. The evening's
  intermittent Chrome renderer crashes (STATUS_STACK_BUFFER_OVERRUN),
  unexplained engine AVs and restarts now have a hardware suspect.
- R4 five lessons LIVE on the rail: lessons.json drives the page
  (nav ‹1/5›, titles, bodies, goals); the judge evaluates each goal
  type from live state. wake_the_cell + bend_the_knee PASSED and
  SAVED under Alan (progress/Alan.json). The gentle/healing/whole-body
  lessons are playable; their formal pass-walk is pending a clean
  input driver session (SendKeys focus flakiness on this desktop —
  the touches, judges and save all verified working individually).
- DYAD ANALYSIS (the operator directed it for the "only lesson 4
  activates" report): the blind judge's diagnosis from the frozen
  evidence — CONFIRMED the pressure lessons' release phase requires
  all |P| < 1000 Pa while the leg cells sat pinned at ±30-90 MPa by
  the STILL-HELD knee pose (no reset UI existed), and caught a second
  bug: the judge latched goals on |P| so stuck residuals pre-latched
  lessons 2/3/5 with zero player input. Both fixed: signed latching
  (positive pressure only), showLesson resets any held pose on
  pressure-lesson entry, pose lessons auto-return to rest 1.8 s after
  passing, and a standing "stand at rest" button.
- Evidence frozen: docs/evidence/agent_fleet/SHIP/R4_DYAD/
  (screen_lesson4_passed.png, state_stuck.json, lessons_as_shipped.json).

## LEDGER (2026-09-13, R1 refinement — maximized on load)

The operator: "the editor is not loading full screen — it's kind of a
little bit offset. We need to have maximized when loading." FIXED in
the engine: the game window opens SW_MAXIMIZE (filling the work area by
construction — rect verified -8,-8 -> 2568x1400 on the 2560x1440
display), and the launcher keeps its --hidden console retirement.
Verified after a full relaunch: creature restored, studio live at
299 fps, window edge to edge.

## LEDGER (2026-09-13, night II — the headless probe findings)

- The headless-Chrome R4 walk could not complete: the world attach in
  the headless page failed (WebGL2 context now works via channel
  chrome, but the boot's data path still stalls) and the judge-debug
  div reads the literal "[]" — an unknown writer (no JSON.stringify in
  the page writes it; exactly one judgeState exists). FIRST LEAD for
  the next session: dump the div's parent chain + find the "[]"
  writer; suspicion: an overwriting patch left a second poll-state
  writer, or loadLessons never runs pre-PLAY and something else
  initialises the div.
- CONFIRMED WORKING (visible Chrome, the operator's own play + keys):
  the game renders, orbits, touches (worst P 34 kPa mid-hold), the
  lesson rail navigates 1/5..5/5, lesson 4 passes and auto-resets,
  progress persists per player. The ENGINE-level touch for every
  lesson target verified (foot target 6 kN -> 3760 kPa).
- The input driver flakiness (SendKeys focus races on this desktop —
  Typeless overlay + launcher windows) remains the verification
  bottleneck; the headless walk is the right long-term instrument
  once the "[]" writer is found.

## THE ROBOT STACK LAW (operator directive, 2026-09-13 late: the character
## must have "the same concepts that people that build and train robots —
## checkpoint systems, all the logic of a robot... sense its environment,
## knows where to put its foot, what-if questions it asks itself")

The creature is trained-robot architecture wearing our skin. The stack,
each rung verified before the next:

1. SENSE (live): the body reads itself and the world every tick —
   /verts (posed surface), /tick_state (cell pressures, root, contact
   force), lean and support centroids measured from the streamed state.
2. CHECKPOINT (the gait state machine): locomotion is a sequence of
   named checkpoints with MEASURED entry/exit conditions — per leg:
   STANCE (foot cell in contact, pressure carrying weight) -> LIFT
   (foot cell pressure released, knee bends) -> REACH (foot placed
   ahead of the support centroid) -> LOAD (pressure rises past the
   bar). No phase advances on a timer; every transition is gated by a
   number the body reports.
3. ACT (live, force-capped): poses are muscle intents through
   /tick_pose — ankles, knees, hips — never teleporting.
4. WHAT-IF (the robot's self-questioning): before acting, the
   controller predicts — "if I lift this foot, does the support hold
   my weight?" — answered from the live cell pressures and lean, the
   same numbers the lessons teach.

THE INTERFACE IS THE CHECKPOINT BOUNDARY: sense -> decide -> act stays
fixed, so a trained policy (the checkpoint file a robot lab would
ship) can replace the hand-written state machine later without
touching the body. THE FALL LAW still governs: cut the controller and
the creature falls — that is the proof the walking is real.

RUNG LANDED (2026-09-20): the checkpoint rung is enforced machinery,
not prose. The walker's full state serializes mid-walk and restores
BIT-IDENTICALLY in a fresh process — snapshot at tick 150 of the
ship-fenced 302-tick walk; the restored future is equal on state
hashes and all 21,888 action bytes, same refusal tick and class; all
four registered restart-state gaps closed with load-bearing proofs;
zero engine bytes touched
(tools/science_funnel/validation/snapshot_apis_20260920/receipt.json).
The Astra round-5 decision ("policy-on-build-N must never silently
degrade on build N+1") is a working gate: (policy bundle, physics
build, runtime profile, body/domain, test suite) -> certificate; 4/4
injected incompatibilities caught, three clean runs byte-identical
(tools/science_funnel/validation/upgrade_gate_20260920/receipt.json);
the first production-class certificate issued end-to-end and the
tamper suite rejected 3/3
(tools/science_funnel/validation/cert_dryrun_20260920/receipt.json).
The trained-policy interface itself is frozen — 80 fields, versioned,
byte-deterministic regeneration — and its measured aliasing red (21
pairs) was fixed sensor-side with zero physics-byte movement
(tools/science_funnel/validation/policy_interface_freeze_20260920/ +
tools/science_funnel/validation/obs_populate_20260920/receipt.json).
Forward gaps are named in the receipts, not hidden: no ship-tree HTTP
snapshot route, no first-class engine build id, no actor-in-the-loop
coupling.

## FIRST BUILDABLE RUNG (next window)

THE GAIT CHECKPOINT MACHINE: per-leg STANCE/LIFT/REACH/LOAD states
driven by measured cell pressures and lean, actuating through
/tick_pose with force-capped intents. The bar: with the machine on,
the creature takes measured steps — support pressure transfers foot to
foot, the body advances, and cutting the controller mid-stride makes
it stumble (never glide). Every transition logged with its measured
gate values.

## THE ANATOMICAL COMPARTMENT LAW (operator correction, 2026-09-13: every
## single bone is a sealed compartment — "you can't just have four sections")

The 4-cell body (feet/torso/thighs/shins by height band) was the MINIMUM
proof that the seal works. It is NOT the product. The creature's
compartment tree must match its skeleton: every named bone gets its own
sealed cell, divided by the same cut-and-weld at anatomical planes. The
bone list comes from the skeleton (28 measured pins -> expand to the full
bone tree), not from three horizontal cuts. The verification: the
compartment count matches the bone count, every cell conserves, and the
press on any bone answers in THAT bone's cell — not in a neighbour's.

SCALE: the sculpt carries ~200+ nameable bones. The 4-cell tree was the
proof-of-mechanism. The product tree is the skeleton.
