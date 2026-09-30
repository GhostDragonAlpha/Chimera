---
name: seal-wall-takeover-2026-09-13
description: SHIP GOAL state 2026-09-15 — THE CREATURE WALKED (15/15 bars,
cut falsifier passed); far-side click fixed; guarded sealed cells + idempotent
restore; visible-dimple page fix; dyad-judge $25 gate live; Astra round-2 in
flight (swapchain, XPBD frequency correction, reflex arc); next = creature-
answers prototype + lessons 4-10 by-hand audit + R9 hosting
metadata:
  node_type: memory
  type: project
  originSessionId: sess_141e362c-a25b-452d-bd03-88fb5f876ce6
---

Ship-goal lane on E:\ChimeraWork\slot-01, branch
astra/tasks/matter-kernel-format-01 (pushed to origin through 486b4940).
Alan's active /goal = docs/THE_SHIP_GOAL.md (9 R-items) — **5 of 9
delivered: R1 PASS, R2 PASS, R3 PASS, R5 PASS (sound wired; audible
check rides R8), R4 rail live (walk-through pending)**; R6 harness
delivered (full run pending), R7/R8/R9-Hosting pending. Alan's
mandate: "Continue indefinitely. Do not stop until the goal book has
been completed." **HARDWARE: repeated restart events traced by the
operator to 128 GB RAM unstable at 5600 MT/s XMP — lowered to 5000
MT/s (2026-09-13). Suspect RAM instability behind the intermittent
Chrome STATUS_STACK_BUFFER_OVERRUN tab crashes, odd engine AVs, and
the restarts. Post-restart recovery chain (verified twice):
launch_chimera.bat + `python tools/game_shell/server.py` +
`python tools/website/server.py` bring the whole stack back.**

**R1 DOUBLE-CLICK LAUNCH PASS (4de4cf55):** launch_chimera.bat deployed
next to the exe by CMake post-build copy — one double-click sets its own
working directory, starts with `--hidden` (console retired; F1 studio +
HTTP remain), and the creature restores AS ITSELF. Mechanism:
/tick_classify, /tick_vertbind, /tick_joints write THROUGH to
session_snapshot/<endpoint>.blob; /tick_seal APPENDS to
tick_seal_history.log (the cell tree is a history, replayed in order);
shared k_snapshot_endpoints list used by status/restore/clear.
R1a: the old "window must stay FOREGROUND" law RETIRED — did not
reproduce (minimized/occluded/restore all serve 1.09-1.13 s, picture
answers poses); Alan verified: "Nothing is frozen I'm able to rotate
the object and time is advancing." THE_CELL_MODEL law superseded in
place. Latency-only probes cannot see a frozen surface — hash-compare
/frame bytes across a pose. Honest caveat: the .bat flashes a console
~100 ms; no-flash launcher belongs to R7. **Crash-recovery proof: two
real system restarts; the launcher resurrected the sealed 4-cell
creature with zero manual steps both times.**

**R3 THE HOOK IN MOTION PASS (e33dd95c):** /tick_touch {"px","py",
"force_n"} — Engine::pick casts the camera ray (same spherical law as
update_camera_matrices: eye from r/theta/phi/target/pan, up =
(-s·sx, c, s·cx), 45° fov), Möller–Trumbore over the POSED buffer.
Closed-loop bar: the hit re-projects (project_world) onto the requested
pixel — 0.0 px error. Posed normals recompute from the posed surface
EVERY tick (stale-normal bug class dead; lighting under pose true).
Posed touch sub-millimeter. Kappa answer in whatever cells the dent
lands. **INSTRUMENT LESSON: the first T1 "failure" was MY tool —
/project takes x/y/z FLOAT KEYS; a "p" array parses zeros, projects the
origin, answers screen center for every query. Fix the instrument
before fixing the physics.**

**R2 THE GAME LOOP PASS (8b5365bf + c4f91adf):** game shell
tools/game_shell/server.py (stdlib, port 8206) + index.html. Front door:
proxies frame/state/touch/touch_clear/pose/topology/verts/touch_hit,
keeps per-player progress in progress/<name>.json. Played END TO END in
Chrome (dimple 0.1176 m, torso +0.255 MPa, heal, PASSED verdict, save
+ fetch-back).

**THE WEB KERNEL LIVE (5bc96af4):** the browser renders the creature
itself — WebGL2 client + /topology (439,564 B once) + /verts (664,528 B
per pull @3 Hz) state stream + browser ray-cast → /tick_touch world
hits; local orbit/zoom at page fps; engine 295-302 ticks/s with the
page open vs ~32 collapses under the old PNG polling = the operator's
28 fps 1% lows explained and killed; /frame?w= downscale for
thumbnails. **Engine-side picking restored for the browser: /tick_touch
accepts {"cam":[8],"px","py","aspect","force_n"} — the page posts its
LOCAL camera + click pixel and the ENGINE picks (pick_cam) with the
proven closed-loop math; the browser never ray-casts.**gotcha: pick
aspect must be the CALLER's canvas aspect (engine extent default breaks
off-center hits).

**R4 FIVE LESSONS INTEGRATED (486b4940):** data-driven judge from
tools/game_shell/lessons.json (5 lessons: wake_the_cell, the_gentle_hand,
the_healing, bend_the_knee, the_whole_body; goal types pressure_above
[cell/any/also], pose_reach; then_release phases) + lesson nav ‹1/5› +
pose button + per-lesson progress keys. **Thresholds re-tuned to the
MEASURED local-touch response** (the R4 lane's originals were tuned for
joint-group presses and were unreachable through the browser's local
Gaussian touch): wake 20 kPa (was 200 kPa), gentle 200 Pa capped at
8000 N, healing 20 kPa, whole-body 15 kPa + 5 kPa also-latched.
General lesson: re-tune lesson goals against the MEASURED response of
the actual input path.

**DYAD ANALYSIS (operator-directed, on "lesson 4 is the only one that
activates"):** the blind judge's diagnosis from frozen evidence
(docs/evidence/agent_fleet/SHIP/R4_DYAD/) — CONFIRMED: the knee pose
held forever (no reset UI) pinned the leg cells ±30-90 MPa, making the
pressure lessons' all-calm release check impossible (4-5 orders of
magnitude out of reach); AND the judge latched goals on |P| so stuck
residuals pre-latched lessons 2/3/5 with zero input. Fixes: signed
latching (positive P only), showLesson resets any held pose on
pressure-lesson entry, pose lessons auto-return to rest 1.8 s after
passing, standing "stand at rest" button. Evidence frozen in
docs/evidence/agent_fleet/SHIP/R4_DYAD/.

**KEYBOARD + GAMEPAD input systems (Alan: "use keyboard commands
instead of clicking buttons... mouse clicking has always been hit or
miss with AI computer use" + "GamePad commands if you need an analog
stick"):** Keyboard (play screen): 1-5 lessons, [ ] prev/next, SPACE
hold = press the lesson's touch_target (cycles targets for
whole-body), - / = force ±2000 N, P pose, R stand at rest, S save, ESC
let go. Gamepad: left stick = orbit, A held = press (RT analog force),
B release, LB/RB lessons. polled in rAF. These exist so an AI driver
works by keystrokes — verify the game via SendKeys, not mouse clicks
(mouse resolving is flaky: overlay windows like Typeless steal
windowFromPoint; background-tab timers throttle the page's 700 ms
judge poll — bring Chrome FOREGROUND before judging waits).

**R5 SOUND PASS (wired):** tools/game_shell/sound.js — synthesized
WebAudio (press tone follows force, cellWake chime, passed motif,
saved blip, ambient bed), zero assets, wired into
play/release/wake/pass/save hooks; audible check rides R8.

**R9 WEBSITE LIVE:** tools/website/ on 8210 — landing page (hero,
how-it-works, PLAY THE DEMO → 8206, signup → signups.jsonl, live
count); first signup recorded (Alan). Public internet hosting is the
remaining step (static-capable host + domain, no identity needed
until payments).

**Fleet pattern that built all of this (operator: "your whole focus on
maximum parallel subagents — coordinate everything, subagents do all
the work"):** five parallel general-purpose agents with disjoint file
contracts + full API specs in the dispatch; the LEAD only integrates,
verifies live, records, commits/pushes. Worked cleanly; reused for
every remaining requirement.

**Engine ops (proven recipe):** Stop-Process -Name chimera_engine -Force
BEFORE linking (LNK1104); build `cmake --build .tmp/build_tick --config
Release --target chimera_engine`; relaunch via
`cmd //c launch_chimera.bat` from the Release dir; after any restart
the launcher auto-restores mesh + payloads + seal tree. Shell restart:
kill port 8206 owner, rerun tools/game_shell/server.py. **Ledger-script
lesson: python edit scripts that assert-then-write lose ALL their edits
when a mid-script assert fires — verify the book after every scripted
edit, or write incrementally.** glslc lives at
/c/VulkanSDK/1.4.328.1/Bin/glslc.exe (recompile shaders/*.vert → .spv
after edits; the engine loads spv at init). Pre-commit hook refuses
unattributed commits — add `Agent: ZCode <zai-coding-plan/GLM-5.3>`.

**Debug lessons (durable):** /project expects x/y/z FLOAT KEYS (a wrong
key silently projects the ORIGIN = screen center — fix the instrument
before the physics). windows.h typedefs `small` (unsigned char) — local
vars of that name break the build. Chrome tab STATUS_STACK_BUFFER_
OVERRUN on a black canvas = /topology header must be TRIANGLE count
with ALL indices as payload. Engine tick_state serves fast only inside
~1.1 s windows while PNG captures are requested. SendKeys '{[}' is
invalid — use keybd_event VK_OEM_4/6 for brackets. Background-tab
timers throttle to ~1/min — bring Chrome foreground before waiting on
page-side judges. Ledger scripts that assert-then-write lose all edits
on a mid-script assert — verify the book after every scripted edit.

Older durable lessons in repo run records: v0 on the tick's own rest
blend (same-code-path rule); winding law (LOWER cap reversed); sliver
capacity floor (0.1 N); dimple_m_ reports TRUE applied offsets; lock at
step entry; every HTTP entry holds the mutex. Alan's laws in
THE_SHIP_GOAL.md: WORLD (163a6047, players are cameras), MOVEMENT
(1dfad8e8, no move-forward — fall first), ALIVENESS (4f1da62e, any mesh
+ skeleton comes alive).

**FLEET 2 RESULTS + FLEET 3 LAUNCHED (2026-09-14 early, pushes through
e6b1dbf4/d8dd9443/e6b1dbf4/0ab720fc):**
- **D1 R6 bench re-run: PASS 4/4** with the corrected model — IDLE
  299.12, real-page 297.52, TOUCH_STORM 299.35 mean t/s; thumbnail
  channel 1.17x honestly labeled. Report: R6_BENCH/bench_rerun.md.
- **D2 media pack:** blood rest/press PAIR (0.000 vs 1.270 MPa), beauty
  shots re-framed to measured face fronts (thetas -2.6..-3.3), trailer
  keyframes, manifest mapping assets to judge defects.
- **D3 re-run verdicts: still FAIL 0/2 pay** — novelty rose 3→4-5/10;
  explanation gap CLOSED (both judges correctly identify the product);
  the gap moved to GAME: satisfying responsive deformation in motion.
  Judge-named remaining: visual water, polished geometry, variety.
- **D4 hardening: the PII leak was REAL** — GET /signups.jsonl served
  the raw file to anyone; now 404. Per-IP token buckets close exactly
  (stream 600/min: 40 pulls all 200). start_all.bat + DEPLOY_RUNBOOK.md
  (Cloudflare Tunnel recommended, ~$10/yr domain; VPS alternative;
  ngrok trial). The website PLAY button now derives its target from
  location.hostname (play.<rest-of-host> public, local:8206 dev).
- **E2 SEAM: the prereg theory was REFUTED** (flip concentration
  0.20-0.34 vs predicted >=0.80 — the crease is pivot-heterogeneous
  shear, not pin-set flips). Edit B (saturating tint t/(1+t)) HELD:
  boundary 0.4675→0.1457. The REAL fix is regenerating vertbind
  (same-limb restriction). **E4 TUTORIAL: intro overlay + 5 dots +
  payoff + force meter landed and smoke-verified.**
- **W-lane bench launched (10):** W1 judge impl, W2 tick audit r2,
  W3 gallery r2, W4 sound 2, W5 goal audit, W6 ten-lesson walk,
  W7 PLAY fix, W8 vertbind regen, W9+W10 duplicate audits (launched
  by mistake, stopped — lead launched two duplicate pairs).

**FLEET 3 DEPLOYED (2026-09-14, 6 agents):** R9-deploy (Cloudflare
config + 15-step go-live), R6-rerun (corrected model), R8-rerun r3
(new media pack), E4v2 tutorial polish, R4-polish verify, W7-PLAY-fix.
Evidence in CHIMERA_PROOF\R4_WALK\ and R8_STRANGER_RERUN\.

**PLAN-FIRST EFFICIENCY (measured, operator-validated):** the accidental
plan-mode lock forced 6 fleet-2 agents to explore-and-plan before
executing. Every plan caught a real bug at planning time: D4 found the
signups.jsonl PII leak by inspection, F2 located the 0.5-0.8s PNG
encode as the /frame floor, E4 caught the save-wipes-seen_intro trap.
Resumed agents went straight to execution against their own spec —
zero re-exploration. Adopted as standing doctrine: new agents get
"explore, write the plan, then execute it" baked into their orders.

**REMAINING:** R4 formal all-five pass walk (needs W1's judge + a
stable headless session — the "[]" writer mystery is stale cache/probe
artifact per the Explore audit), R6 bench re-run with the corrected
model, R8 re-run round 3 with the improved media pack, R9 public
hosting (operator: domain + account), delta compression for /verts
(internet scale). Related: [[matter-kernel-spec-and-build]],
[[alan-operator-preferences]], [[membrane-game-product-vision]].

**THE GO-LIVE GATE (2026-09-13 late, operator: "we go live when agent
says that this game is worth $25"):** the go-live price is $25 and the
gate is a BLIND JUDGE saying the game is worth it at that price. Three
rounds of stranger tests have run; round 3 novelty 4-5/10 and climbing.
Both judges' yes-conditions converge on: satisfying responsive
deformation IN MOTION, visible water, polished geometry, variety. The
evidence-pack lever (stills/trailers) is EXHAUSTED — the next lever
both judges name is a PLAYABLE DEMO or genuinely real-time footage.
R8 and R9 are COUPLED: the judges can't play localhost:8206; the
deploy kit (start_all.bat + Cloudflare config + hardened servers) is
ready but the operator's domain/account decision gates the public URL.

**FLEET 3 RESULTS (2026-09-14 early):**
- **R6 RE-RUN: PASS 4/4** with the corrected model — IDLE 294.53,
  GAME_PAGE_LOAD 299.05, FRAME_THUMBNAIL 152.74, TOUCH_STORM 297.59
  mean t/s; every 1% low >= 40. The real page costs 1-2% vs idle.
- **R8 RE-RUN ROUND 3: FAIL 0/2 pay** — novelty 4/5, still below the
  bar. Delta vs round 2: explanation gap CLOSED, novelty rising. The
  judges' convergent demand: playable demo, variety, polish.
- **E4V2 TUTORIAL POLISH:** intro translucency (WebGL creature shows
  through), payoff flourish with player name + lesson count, intro
  key hint. Playwright smoke: intro renders over live creature, Enter
  dismisses, seen_intro persists, dots strip correct, zero errors.
- **R4 POLISH VERIFY:** the E2 seam tint fix confirmed LIVE (soft
  gradient 0.1457 vs band 0.4675); the geometric crease at the joint
  fold is the BINDING defect (vertbind regen named as the successor).
- **C1 CRASH ROOT-CAUSED:** offline bounds-checked repro EXONERATED
  the importer entirely (sphere volume = exact inscribed-polyhedron
  value) — the crash was ENGINE-SIDE: init() never cleared the seal
  tree, so a mesh swap onto a sealed tick read verts9 through the OLD
  creature's slot ids (~600 KB over-read). Fixed: init() clears all
  seal state. **BRING-ALIVE VERIFIED LIVE:** raw OBJ -> 9 auto-pins ->
  classified -> bound -> sealed -> 2 cells conserving at exactly 0%.
- **W7 PLAY FIX:** hostname-derived demo door (play.<rest> public,
  local:8206 dev), unit-tested five cases.
- **W10 CURRENCY AUDIT:** 7 drift items found in the goal book +
  memory note (the R5 include repair was false-for-a-window then
  true-again). The off-body touch refusal is LIVE and working (0.5 m
  away hit -> "the point is not on the body"; on-body answers 1.72
  MPa).
- **OPERATOR SAW THE STOMACH DEFORM** (2026-09-13 late): the first
  visual confirmation of the press-and-answer hook where the operator
  could SEE it — the press at the actual front-torso skin (z=0.759,
  found by querying /verts for the y-band's max-z vertex) produced a
  visible stomach dimple at 30 kN. Earlier attempts aimed at empty
  space near the torso because I was guessing at coordinates instead
  of reading the actual skin surface from the creature's own vertex
  data (/verts query for the y-band's max-z vertex). The fix was
  simple: ask the streamed verts where the stomach actually is, press
  THERE. The same body, the same sealed cells, the same kappa law —
  but now the operator can see it. That's the difference between code
  that works and a product that shows it works.

**HEADLESS-WALK BLOCK + THE "[]" MYSTERY (2026-09-13 night II, pushed
5ff8a927):** after SendKeys walks kept "failing", the screen check
revealed why — **the desktop was in Alan's live Warzone lobby; the
injected keystrokes were landing in HIS game.** Hard rule now: never
inject input into the shared desktop; drive the game with a PRIVATE
headless browser instead. tools/game_shell/walk_lessons.js does exactly
that (Playwright via E:/PythonChimera/node_modules/playwright-core;
channel:'chrome' for real-Chrome headless — bundled chromium has NO
WebGL2, swiftshader flags did not help). It walks name→PLAY→all five
lessons→save, but the headless page's boot stalls: world data never
attaches (topologyFetched false) and the judge-debug div reads a
literal "[]" from an UNKNOWN writer — no console errors, page script
parses clean, disk==served byte-identical, exactly one judgeState, no
JSON.stringify writes the div. A world-attach/GL decouple patch was
applied (loadTopology/pollVerts/boot run the data path regardless of
RG so the judge works without WebGL) — did NOT unblock headless.
**NEXT SESSION LEAD #1: find the "[]" writer (dump the div's parent
chain; suspicion: a leftover second poll-state writer from the patch
storms, or loadLessons/judge init ordering).** Probe tooling shipped:
probe_headless.js / probe_boot.js / probe_dom.js. A judge-debug div
(pollState-driven) now rides the page. Alan's directive for the mode:
"You keep stopping I want you to work continuously" — run unattended
scripts end-to-end, not step-by-step turns.

**THE 10-AGENT FLEET (2026-09-13/14, plan APPROVED by Alan — "Plan for
10 agents sub agent"; deployed same session):** Explore verified the
tree clean at 5ff8a927 AND found the R4 headless root causes: (1) the
judge-debug writer sits INSIDE the WebGL render loop (line ~558) which
never runs headless — move it into pollState; (2) the sound.js
<script src> include is MISSING from the page head entirely; (3) no
'[]' writer exists in the current file (stale cache or probe artifact);
(4) no glTF/OBJ importer anywhere; (5) trailer machinery EXISTS
(cpp_bridge.encode_movie PNG→H.264, Chimera/core/trailer.py, ffmpeg).
FLEET COMPOSITION (A close-the-book / B package / C frontier):
A1 R4-complete (owns index.html+probes+walk_lessons.js: fix the two
root causes, formal 5/5 walk headless), A2 R6-bench (bench.py full +
browser rAF fps probe, 60fps bar), A3 R8-stranger (6 screenshots + 2
BLIND judges, "would you pay $14.99?"), B1 trailer (25-30s
press-and-answer MP4 → CHIMERA_PROOF/TRAILER/), B2 store art (capsule
460x215+616x353, icon, 6 screenshots via PIL from live captures), B3
store copy (every claim traces to a PASS line in the goal book),
C1 aliveness-import (prereg first; OBJ-subset + minimal glTF parser in
C++ ~300-line JSON reader; /mesh_import route + tools/bring_alive.py
orchestrates joints/classify/vertbind/seal; leaky mesh refused by
name), C4 supervisor watchdog (start_chimera.py + watchdog.py, health
checks 5s, auto-restart, port-detect to avoid double-start), C2
gravity-fall QUEUED behind C1's build window (mass from geometry +
gravity + feet contact; falsifier = THE FALL), C3 /verts delta
compression QUEUED last. **Coordination rules: exclusive file
ownership per agent; agents NEVER commit (lead integrates + commits
with Agent trailers); engine builds serialize through the LEAD
(Stop→build→relaunch→verify 8107); lanes A/B/C4 never stop the engine
(the live game stays up for Alan); acceptance evidence required before
any R-item flips PASS.** Alan's two coordination questions went
UNANSWERED → best judgment used (mixed ship+frontier, serialized
builds) per the no-answer protocol.

**THE 10-AGENT FLEET (2026-09-13 late night, operator: "Plan for 10
agents"):** all lanes landed. PASS flipped: R4 lessons (5/5 headless
walk; bugs found: release phase was DEAD CODE via duplicated else-if,
SPACE cycling skipped target[0], and lesson targets can be kernel-dead
— the press Gaussian is 3 cm so targets must SNAP TO NEAREST VERTEX;
engine now refuses off-body hit points BY NAME), R7 package (trailer
28s every-frame-real method, capsule art, honest copy with claim
tracing). **THE FALL PASSES F-bars live** (contact = m*g to the
newton, 10.00 mm sink). **ALIVENESS LIVE**: raw OBJ -> auto-rig ->
classify -> bind -> seal -> conserved cells; the import crash's root
cause was init() NEVER CLEARING THE SEAL TREE (mesh swap read old slot
ids, 600 KB over-read) — init() now clears seal state; import writes
no snapshot blob (poisoning class dead). **R8 stranger test FAILED
honestly** (2 judges, no at $14.99, novelty 3/10 — defects: motion
absent [now fixed by the trailer], prototype look, water invisible in
stills, teaching payoff invisible) — re-run pending. **R6 split**: player
240 fps vsync-locked, bench strict-FAIL from model drift (bench still
polls /frame which the real page abandoned) + bursty tick counting.
**CRASH-LOOP class found**: bindings-without-joints snapshot ->
classified with zero pins -> OOB — every classified site now requires
pins non-empty. Watchdog saved a real outage live. Lessons: SendKeys
focus racing makes screen-injected input unreliable (use headless
Playwright channel:'chrome'); get_double can't parse JSON booleans
(stod throws); urllib vs curl same POST can differ only by engine
restart timing; std::map symbolization = heap detonation from
elsewhere. Goal book: R1-R5,R7 PASS (6/9); R6/R8 re-run + R9 hosting
remain.

**FLEET 1 FINAL WINDOW (e6b1dbf4):** C1's rework EXONERATED its
importer offline (bounds-checked g++ repro; sphere volume exactly the
inscribed-polyhedron value) — the import crash was engine-side:
init() never cleared the seal tree, so a mesh swap onto a sealed tick
read verts9 through the OLD creature's slot ids (~600 KB over-read,
detonating in a map alloc). Lead landed init()'s seal-clear stanza (a
new body is born unsealed); C1's /mesh_import route applies payloads
DIRECTLY via the g_mesh_req pattern (no nested invoke_api) and writes
NO snapshot blob (import poisoning class structurally dead), with a
named stale-seal refusal as defense-in-depth. **Off-body touch
refusal verified live** (0.5 m-away hit -> "the point is not on the
body"; on-body answers 1.72 MPa). **BRING-ALIVE VERIFIED LIVE:** raw
OBJ -> 9 auto-pins -> classify -> bind -> seal -> 2 cells conserving
at exactly 0%, conservation held under pose. World restored clean
(4 cells [0.288,12.509,0.693,0.335]) + watchdog on.

**FLEET 2 DEPLOYED AND LANDED (operator: "Plan the next 10 subagents"):
** Lane D close-the-book — D1 R6 bench re-run (fix MODEL DRIFT: the
real page polls /verts@3Hz+/api/state, never /frame; 5-second buckets
to smooth bursty tick counting), D2 R8 media pack (blood-panel stills
via HEADED Playwright, a lesson-PASSED moment, beauty shots, trailer
keyframes -> Desktop CHIMERA_PROOF\R8_MEDIA\), D3 stranger re-run
(polls for D2's pack up to 30 min, same pitch + same 4 questions, 2
fresh blind judges, verdict + delta vs round 1), D4 R9 deploy prep
(harden both Python servers: --host argv, per-IP token bucket, 5 MB
body cap, traversal probe-tested; tools/deploy/start_all.bat one-click
public stack; docs/DEPLOY_RUNBOOK.md three options — Cloudflare Tunnel
free RECOMMENDED / $5-6 VPS / ngrok trial; operator only does
account+domain+payment). Lane E judge-named polish — E1 stage art
(3-light rig with warm rim in shaders, distance-faded grid, under-
glow; // E1 block in engine.cpp for constants), E2 seam fix (analysis
FIRST: offline normal-discontinuity numbers, then bounded Laplacian
normal relax in the // E2 region), E3 lessons 6-10 (new goal types
pose_pair / gravity_on / cells_woken documented in
LESSON_JUDGE_SPEC.md; lesson 9 THE STAND uses /tick_gravity), E4
tutorial flow (once-per-name intro overlay, 5-dot progress strip,
all-five PASSED payoff flourish; // E4 regions in index.html, NOT
pollVerts which C3 owns). Lane F frontier — F1 stance balance (servo
on ankles 17/18 only: dPose/dt = -k_p*lean, lean = posed-surface
centroid vs feet-contact centroid; behind stance_on_ + /tick_stance
THE LEAD WIRES at the window; falsifier: stance-off + perturbation ->
lean grows), F2 fast capture (>=5x cut of /frame's 1.1 s floor; WIC
JPEG ~80 lines OR honest downscale-only fallback; // F2 block only).
**Coordination additions for concurrent shared-file agents: MARKED
blocks (// C3/E1/E2/F1/F2 BEGIN-END) with explicit region ownership;
build windows serialize through the lead (C3's tree first, then one
combined window, wiring /tick_stance).** Remaining book after fleet
2: R6/R8 verdicts, R9 go-live decision.

**FLEET 2 RESULTS (2026-09-14, all 10 lanes landed; pushes through
d8dd9443):**
- **D1 R6 bench RE-RUN: PASS 4/4 scenarios** with the corrected load
  model (GAME_PAGE_LOAD now pulls what the real page pulls — /verts
  3 Hz + /tick_state 1.4 Hz, never /frame; the /frame thumbnail path
  is its own honestly-labeled scenario): IDLE 299.12, real-page
  297.52, TOUCH_STORM 299.35 mean t/s; the thumbnail channel measured
  1.17x the bar with the raw stall signature still live (105 MB/60s —
  engine lane may want the ~55% throughput cost explained). Report:
  docs/evidence/agent_fleet/SHIP/R6_BENCH/bench_rerun.md.
- **D2 R8 MEDIA PACK:** blood rest/press PAIR (same camera 1 s apart —
  0.000 vs 1.270 MPa with the awake accent), beauty triples re-framed
  to MEASURED face fronts (thetas -2.6..-3.3; the planned ±1.45s were
  side profiles on this creature), trailer keyframes at
  press-peak/heal/end-card, previews, manifest mapping every asset to
  its judge-named defect. On Desktop CHIMERA_PROOF\R8_MEDIA\.
- **D3 STRANGER RE-RUN: still FAIL 0/2 pay — but the delta is real:**
  novelty 3 -> 4-5/10; both judges now correctly identify the product
  (explanation gap CLOSED); their yes-conditions converge on ONE
  demand: satisfying responsive deformation IN MOTION + visual water +
  polished geometry + variety. Verdicts verbatim in
  R8_STRANGER_RERUN\verdicts.md.
- **D4 DEPLOY HARDENING: the PII leak was REAL** — GET /signups.jsonl
  served the raw sign-up file to anyone (200/77B measured); now 404.
  Traversal wall verified with --path-as-is (curl's own dot-
  normalization was caught and corrected in the probe method).
  Per-IP token buckets close exactly (api 30/min: 11x200 then 7x429;
  stream 600/min: 40 rapid pulls all 200 — one player's measured load
  can never trip it). 5 MB/4 KB body caps with unread-body close.
  --host binding proven by netstat. start_all.bat + pieces_public.json
  make the watchdog the public starter-keeper (engine stays loopback,
  never routed). DEPLOY_RUNBOOK.md: Cloudflare Tunnel RECOMMENDED
  (free, ~$10/yr domain), VPS reverse-tunnel alternative, ngrok trial;
  operator-only list (account, domain, payment); flagged: the website
  PLAY button hardcodes 127.0.0.1:8206 (public fix = derive from
  location.hostname: play.<rest-of-host>).
- **E2 SEAM: the prereg's own theory was REFUTED, honestly recorded.**
  Flip concentration 0.20-0.34 vs predicted >=0.80 — the crease is
  pivot-heterogeneous SHEAR in the binding (thigh verts bind
  [spine,hip_L,hip_R] vs [spine,hip_L,knee_L] one ring away), not
  pin-set flips. Edit A (Laplacian normal relax) REFUTED by its own
  sweep (best 72% collapse vs required 90%) and NOT shipped. Edit B
  (per-vertex-averaged saturating tint t/(1+t)) HELD: boundary jump
  0.4675 -> 0.1457, failed cells darken deterministically, rest
  byte-identical. The REAL seam fix is regenerating classify_run's
  vertbind (same-limb restriction + bounded falloff) — named
  successor, not yet built. Sliver truth kept: 206 static folds are
  pose-invariant sculpt pathology.
- **E4 TUTORIAL: complete + smoke-verified.** Intro overlay (once per
  name, seen_intro persists through the save-wipe trap it caught and
  fixed — the progress POST replaces the whole file), 5 progress dots,
  the all-five PASSED payoff flourish, hand-strength meter with the
  gentle notch. Playwright smoke on a scratch port (8290): intro
  renders, Enter dismisses, flag persists, zero page errors.
- **W-LANE BENCH LAUNCHED (10 agents):** W1 judge impl lessons 6-10
  (pose_pair/gravity_on/cells_woken + the hold guard + the
  /api/gravity proxy), W2 tick-counter audit round 2, W3 glTF gallery
  round 2 (torus/twisted box/snowman/gem on a throwaway 18107 engine),
  W4 sound pass 2 (region-character presses, wake swell, heal
  shimmer), W5 goal-book currency audit, W6 ten-lesson headless walk,
  W7 website public PLAY fix, W8 vertbind regeneration (same-limb
  restriction), W9+W10 duplicate audits (launched by mistake, stopped
  — the lead launched two duplicate pairs and stopped them cleanly).

## CURRENCY AUDIT (W10, 2026-09-13 late / 09-14 UTC)

Read at HEAD ac2ce056 (which landed DURING this audit — the tree is
live: uncommitted work in main.cpp, walk_lessons.js, walk_test.py,
website/index.html, sound.js, walker.json). Scope: docs/THE_SHIP_GOAL.md
full ledger + last 20 commits + file spot-checks. No code edits.

**R-ITEM CURRENCY:**
- PASS with evidence verified in-tree: R1 (launch_chimera.bat +
  restore chain), R2 (tools/game_shell/server.py port 8206; progress/
  Alan.json holds exactly the 5 lessons), R3 (/tick_touch; off-body
  refusal in engine), R4 (five-lesson headless walk evidence; the
  TEN-lesson walk is 9/10 in flight), R5 (see below), R7
  (tools/trailer/make_trailer.py + tools/store_art/make_art.py +
  docs/DEPLOY_RUNBOOK.md all exist).
- OPEN, honestly: R6 — but ONLY for the right reason now: the re-run
  PASSED 4/4 (docs/evidence/agent_fleet/SHIP/R6_BENCH/bench_rerun.md,
  IDLE 299.12 / real-page 297.52 / TOUCH_STORM 299.35 t/s) and every
  number is still RTX 4090; the GTX-1060-class machine remains
  unmeasured. R8 — re-run FAIL 0/2 pay, novelty 3→4/5
  (docs/evidence/agent_fleet/SHIP/R8_STRANGER_RERUN/). R9 — locally
  live, hardened, deploy kit ready; public go-live is operator-gated.
- **R5 delivered-but-(twice)-unflipped, NOW true:** the include WAS
  missing (Explore found no `<script src>` for sound.js at all);
  TODAY tools/game_shell/index.html line 8 has
  `<script src="sound.js"></script>` and 8 ChimeraSound call sites
  (press x2, cellWake, passed x4, saved). R5 PASS is TRUE as of this
  audit. W4's pass-2 (wakeWhoosh/healShimmer/region) exists ONLY in an
  uncommitted sound.js (+133 lines); index.html still calls only the
  pass-1 hooks — pass-2 is delivered-but-unwired.
- Delivered-but-unflipped: R9 — website LIVE (signups.jsonl first
  signup Alan 2026-09-13 14:34:33), PII leak closed (signups.jsonl
  now 404, verified in server.py source), tools/deploy/start_all.bat +
  pieces_public.json landed, W7's hostname-derived PLAY door
  COMMITTED (ac2ce056, "unit-tested five cases"). Only the operator's
  account/domain/payment blocks the flip.

**DRIFT LIST (ledger line vs file truth):**
1. THE_SHIP_GOAL.md STATUS LEDGER table stops at ~22:00 09-13 (newest
   row = R7 store package). Missing rows: R8 re-run verdict (d8dd9443),
   D1 R6 bench re-run 4/4 PASS (ac2ce056), E3 ten-lesson arc, C3 delta
   compression, D4 hardening + PII closure, E1 stage rig, E2 Edit-A
   refutation, F1 stance machinery, the W-fleet. Correction: append
   these rows or a pointer to this note.
2. R6 event row claims "stays OPEN — needs the bench scenario updated
   to the real load model + a re-run" — BOTH are done; the row's
   reason is superseded. Remaining bar: mid-range machine only.
3. Night-ledger "gentle 200 Pa" is SUPERSEDED: lessons.json
   the_gentle_hand now threshold_pa=50000 (50 kPa, cap 8000 N) — E3
   restored it "per the coordinator decision" (a92569f7). The ship
   goal and this note both still say 200 Pa.
4. R4 rows describe a five-lesson product; lessons.json `_format` now
   says "EXACTLY 10 lesson objects" and walker.json has 9/10 passed
   (the_cascade pending) — the formal 5/5 evidence covers only 1-5.
5. This note's frontmatter says "pushed through 22c329bb", the body
   says "through 486b4940"; origin is actually at ac2ce056. Two stale
   push pointers in one note.
6. This note's early "Next:" block still lists R6 full bench run /
   R7 trailer / R8 re-run / R9 hosting as pending — all four have
   since happened (recorded later in FLEET 2 RESULTS). Read the
   RESULTS section, not the Next block.
7. This note's "W9+W10 duplicate audits ... stopped" is stale as of
   now: W10 (this audit) ran to completion.

**W-LANE BENCH (W1-W10) COVERAGE:**
- LANDED + committed: W1 (/api/gravity proxy in server.py — the code
  comment names W1; KNOWN_GOAL_TYPES hold guard in index.html; live
  probe artifact g2probe_32096.json untracked), W7 (ac2ce056).
- COVERED by another lane's artifact: W2 — D1's bench_rerun.md audited
  and fixed the tick-counter (gap-split bucket rule); no separate W2
  artifact exists.
- ACTIVE, not landed: W4 (sound.js +133 uncommitted; page wiring not
  started), W6 (9/10 lessons passed, walker.json; the_cascade
  remaining), W10 (this audit).
- NOT STARTED (no trace in tree): W3 (no torus/snowman/gem/glTF
  gallery anywhere; ChimeraEngine/gallery.py is the OLD GPU-mutation
  verifier from 7aba0ee7), W8 (no same-limb restriction in
  membrane_tick.cpp — E2's named successor is unbuilt), W5 (no
  currency-audit artifact predates this one).
- STOPPED: W9 (duplicate audit, per the note above).

**Correction for the next ledger writer:** the currency-critical three
are (1) R6's stale reason — flip the reason to "mid-range machine
untested" or R6 looks unfinished when its named blockers are done;
(2) the gentle-hand threshold 200 Pa → 50 kPa — lesson text the page
SHOWS players ("passes 50 kPa") contradicts the goal book's night
entry; (3) the R5 include history — the PASS line was false for a
window and is true again as of line 8; record the repair so no auditor
re-litigates it.

## CURRENCY AUDIT (G9, 2026-09-14 ~00:20 -0500)

Read at a tree that moved DURING the audit: this audit started at HEAD
92287a2b and finished at **a5b11bbd** (two commits landed mid-read:
03113399 00:13, a5b11bbd 00:16 -0500; both already on
origin/astra/tasks/matter-kernel-format-01). All file truths below are
verified at a5b11bbd. Untracked in flight: tools/body_atlas.json +
tools/body_atlas.py (an agent mid-lane). No code edits, no commits.

**R-ITEM CURRENCY (goal book vs file truth):**
- R1 PASS — TRUE. launch_chimera.bat at ChimeraEngine/engine/.
- R2 PASS — TRUE. tools/game_shell/server.py default port 8206 (line
  252); progress/ holds Alan.json (5 lesson keys) + walker.json (9/10).
- R3 PASS — TRUE, but the R-item's own line is self-contradictory
  (see DRIFT 1).
- R4 PASS — TRUE for lessons 1-5 (formal 5/5 headless walk evidence);
  the product is now TEN lessons (lessons.json _format: "EXACTLY 10
  lesson objects"), walker.json 9/10 passed (the_cascade pending the
  pressure_isolation judge type — index.html KNOWN_GOAL_TYPES at line
  401-402 does NOT know pressure_isolation yet; its spec landed in
  LESSON_JUDGE_SPEC.md +56 in a5b11bbd, page implementation named
  "next"). Currency-incomplete, not false (rows say "first slice:
  five").
- R5 PASS — TRUE NOW (the twice-told repair holds): grep confirms
  tools/game_shell/index.html line 8 `<script src="sound.js"></script>`
  and 9 ChimeraSound call sites (press x2, cellWake, passed x4, saved).
  Caveat: W4's pass-2 sounds (wakeWhoosh/healShimmer/region/force
  follow) exist in sound.js with call sites DOCUMENTED in comments but
  ZERO call sites in index.html — delivered-but-unwired (the call-site
  edit hit an assertion; deferred per 85c3d73c).
- R6 PASS — TRUE and freshly flipped (92287a2b added the 09-14 row +
  flipped the R-item line). docs/evidence/agent_fleet/SHIP/R6_BENCH/
  rerun2.md verifies the ledger's exact numbers (4/4; tightest row
  FRAME_THUMBNAIL 1% low 130.65 = 2.18x the mission bar). GTX 1060
  class remains untested — honestly kept in the line.
- R7 PASS — TRUE. tools/trailer/make_trailer.py + tools/store_art/
  make_art.py exist; Desktop CHIMERA_PROOF\TRAILER\chimera_trailer.mp4
  + STORE_ART (both capsules, icon 512, screenshots) verified on disk;
  trailer media also committed in-tree (R8_STRANGER_R3/media/).
- R8 OPEN — TRUE. Round 3 FAIL 0/2 pay (novelty 4 and 5; pass bar =
  both yes/maybe AND novelty >= 6), R8_STRANGER_R3/verdicts.md.
- R9 OPEN — TRUE and correctly operator-gated. Website 8210, signups
  PII closed (server.py: "append-only PII -- it is NEVER
  web-readable"), deploy kit landed (tools/deploy/start_all.bat +
  pieces_public.json + cloudflared_config.yml, 4146ed9f), hostname-
  derived PLAY door live in tools/website/index.html (demoUrl).

**DRIFT LIST (ledger line vs file truth, at a5b11bbd):**
1. R-item R3 line (THE_SHIP_GOAL.md ~line 25-29): marked **PASS** yet
   still says "the player-facing touch is OPEN (press where you point,
   press + pose together)". Both named capabilities are landed and
   verified (browser click -> engine pick_cam press, web-kernel W3
   PASS; posed touch sub-millimeter; off-body refusal live at
   ChimeraEngine/engine/main.cpp:1253). Correction: delete the OPEN
   parenthetical.
2. Night-ledger line ~279: "gentle 200 Pa" — STILL uncorrected after
   W10 flagged it. File truth: lessons.json the_gentle_hand
   threshold_pa=50000 and the lesson's own player-facing body says
   "passes 50 kPa" (restored per coordinator decision, documented in
   the _format note, a92569f7). This note's R4-INTEGRATED paragraph
   (~line 86-87) also still presents 200 Pa as current.
3. Row 1 of the STATUS LEDGER table: "8/8 R-items OPEN" — the book now
   carries NINE R-items (R9 added later, its own row explains).
   Historical but count-confusing; say "8/8 (9 after R9's addition)".
4. STATUS LEDGER table is 3+ events behind the R-item lines: NO rows
   exist for R8 rounds 2 and 3 (both FAIL 0/2; d8dd9443, 03113399),
   R9 deploy config + 15-step go-live (4146ed9f), W4 sound pass 2
   delivered-unwired (85c3d73c), the ten-lesson arc (a92569f7), the
   9/10 walk + cascade reframe (03113399), the compartment law
   (c9db3fc1), walk_test (1f7c2c78), or the C3/E1/E4 batch (ac2ce056).
   The newest table row is the R6 re-run (added by 92287a2b). A
   table-first reader sees R8 still at its round-1 roadmap entry.
5. This note's frontmatter ("pushed through 22c329bb+") and body
   ("through 486b4940") — origin is now at a5b11bbd. W10 flagged the
   same staleness class; it re-accumulated within hours. Push pointers
   in prose rot fast on this fleet; prefer "see git" over pinning SHAs.
6. This note's header block still reads "5 of 9 delivered... R6
   harness delivered (full run pending), R7/R8/R9-Hosting pending" and
   REMAINING lists "R6 bench re-run with the corrected model" — R6 has
   since flipped PASS and R7 is PASS (recorded lower in this same
   note, FLEET 2/3 RESULTS). Read order hazard W10 named for the "Next:"
   block now applies to the header block too.
7. Ledger R5 line "(synthesized, wired; audible check rides R8)" is
   true of pass-1 hooks only; W4 pass-2 is delivered-unwired (see R5
   above). Not false, but "wired" must not be read as covering pass 2.

**W-LANE BENCH (W1-W10) COVERAGE at a5b11bbd:**
- LANDED + committed: W1 (server.py:219-227 /api/gravity proxy, the
  comment names W1; KNOWN_GOAL_TYPES + hold guard index.html:401/457),
  W7 (hostname demo door in tools/website/index.html; G6 confirmed
  shipped end-to-end per 03113399), W4 code (sound.js pass-2, 85c3d73c)
  — but W4's PAGE WIRING is deferred, so W4 counts as landed-unwired.
- COVERED by another lane's artifact: W2 (bench.py BUCKET_S=5.0
  bucket_rates PRIMARY, lines 32-33/71/210 + rerun2.md round-3
  numbers; no standalone W2 artifact), W5 (superseded by W10's audit,
  refreshed by this one).
- ACTIVE, not landed: W6 — 9/10 (walker.json, walk_lessons10.js 406
  lines); the_cascade gated on pressure_isolation, spec committed
  (a5b11bbd), page implementation next.
- NOT STARTED (no trace in tree): W3 glTF gallery r2 (no
  torus/snowman/gem anywhere; ChimeraEngine/gallery.py + gallery_env.ps1
  are the OLD GPU-mutation verifier from 7aba0ee7, whose ps1 even
  points at E:\PythonChimera, not this slot) and W8 vertbind regen
  (zero same_limb/same-limb traces in ChimeraEngine/engine/*.cpp or
  tools/classify_run.py; R4 polish verify documents it as the BINDING
  defect successor, "out of scope").
- STOPPED: W9 (duplicate audit pair, at launch).
- DONE: W10 (prior currency audit; 7 drift items; referenced 85c3d73c).

**G9's currency-critical three for the next ledger writer:**
(1) R3's self-contradicting PASS line — one stale parenthetical makes a
PASS requirement read OPEN; (2) the gentle-hand 200 Pa -> 50 kPa fix
still not applied to the goal book despite W10 flagging it and the
lesson copy itself saying 50 kPa — the book has now been wrong through
two audits; (3) the STATUS LEDGER table missing the R8 round-2/3
verdicts and the R9 deploy kit — R8's table entry still describes the
problem list round 1 named, three rounds ago.

## FLEET 4 — THE H-WAVE, THE CLICK FIX, AND THE WALK (2026-09-14; line:
## 569083bb → 2bc028f9+, see git — push pointers rot, audits said so)

**The product now PLAYS CLEAN: the formal ten-lesson walk is 10/10 fresh
passes, 0 page errors** (H7r e37b9cd3 — finished stuck-H7's uncommitted
503 insertions rather than redoing them). The audits that got there: H10
proved the earlier 4/10 was 429-STORM CORRUPTION (same walker 10/10 with
zero errors five minutes later); H9 found sound's dead sites (pressEnd
never wired = eternal drone after first press; canvas hint undefined —
postJSON never parsed); H5's judge dry-run named the honest-play defects
(phantom press 3/3, dead slider, passes-without-input) — all fixed with
before/after probes. H5's own verdict: pay-no at $15-20, novelty 8/10,
"The first press felt genuinely alive; nothing after it did."

**THE OPERATOR'S FAR-SIDE CLICK (fixed; koan answered):** "When I click
on the body the indentation happens on the far side" — pick_cam
reconstructed the page's orbit eye with a Z-SIGN FLIP (engine eye z =
target.z − r·c·cx vs the page's target.z + r·ch·cosθ), casting from
BEHIND the body; foot clicks hit the contralateral limb. Fixed both
sides: engine sign corrected AND the page now raycasts ITS OWN rendered
buffer (pickWorld over RG.verts, verified bit-identical to /api/verts)
and posts {"hit":[x,y,z]} — H16: 7/7 presses land on the seen side
(before-arm 0/7). The page's cam+pixel path is retired. His paired koan
— **"Isn't there a way that we can make functions that interact with
each other the same way real matter interacts with itself?"** — answered
in the kernel's own terms: the click is a fingertip on the SEEN surface,
not a camera-convention function call; every interaction should be a
force through the membrane.

**H8 zero-volume cell (root-caused + guarded):** cell 4 read V=0.000 m³,
P=1.62 GPa across lessons. Mechanism: seal-history REPEATS (60+ entries
for 3 cuts) re-cut a cell at its own cap plane — new cut slots force
py==y exactly while later seals re-drift old blends ~1 ulp below the
plane → closed double-layer "pancake" daughter (v0=4.66e-9 m³ = 1.6e-8
of parent) passed the only check (vl>0) as float noise; kappa law
p=(v0−v)/(κ·v0) → GPa on every pose. GUARD: SEAL_DEGENERATE_FRAC=0.005
(real daughters 9.5–53.8% of parent vs degenerate 1.6e-8 — nine orders;
0.5% sits 19× below the smallest real daughter) refused BY NAME
'degenerate_split'; per-tick c.degenerate withholds p. R2-restore then
made boot IDEMPOTENT: already-satisfied seals skip as 'seal:already'
(nothing executed/refused/re-journaled), the tree round-trips as
tick_seal_state.blob (SEL1; load_seal_state had a +4 n_cells walk bug —
the state path had NEVER once loaded), thread_local gate stops replay
re-journaling. Verified: restore ok, gravity arm → contact = m·g EXACTLY
(135,618 N) at the derived +9.507 mm rise.

**G8 capture saga (4 build windows; honest end):** /frame pulls cost
~1.07–1.1 s and freeze ticks for the pull's duration. THREE
misattributions named in sequence (vkQueueWaitIdle → BAR1 uncached
staging → the collect's map+swizzle); the round-3 reader-thread refactor
DEADLOCKED the world (collect_readbacks' re-enqueue loop matched a
finished slot forever → render thread hung → ticks dead; live relaunch
required). FINAL LAW (H3f round 4, 78eeec9d): default = inline blocking
collect (fence-check FIRST, then map+swizzle on the render thread) —
~1.1 s per pull, ticks dip AND RECOVER, world never freezes; ring+reader
lives behind CHIMERA_RB_READER=1 (default OFF) with the re-enqueue
structurally fixed. The ~900 ms op itself is NAMED as a **WDDM
driver-level device serialization** (identical across memory types and
threads; all instrumented phases µs; instruments on /studio_chrome:
ph_fence_us/ph_coll_us/ph_pres_us, rb_mem_type/flags). The ≤200 ms
latency bar is consciously sacrificed until a no-readback mechanism
exists.

**THE CREATURE WALKED** (window-5 binary;
R4_GAIT_VERIFY/verify_after_stride_fix.json): **3 strides in 4.6 s; 16
transitions all replay against their own measured gates; weight transfer
ranged 38–216 kN ("an animation has no contact force to range"); the
preregistered cut falsifier PASSED** — cut mid-swing → measured abort
entry + stumble transient (|root_vy| 0.234), stride count frozen. Fix
chain: R3 (drive pins from the MEASURED binding, not anatomy — the W8
binding correctly gives feet zero hip weight, so hips can't be drive
pins; strut=ankles 17/18, clearance=knees 15/16 by z-authority); R4
(what-if gate re-derived for the 1-DOF-Y plant — grounding not tipping;
a 57.3× probe-unit/radian frame break let 2133°/s through a 37.2°/s cap;
REACH follows the measured monotonic branch); R5 (V4 RECOVER-abort
contract per the prereg's own words; V10 invokes stance_off_locked_ —
teardown returns ankles to exactly 0; miny audit fields + ts_ms). The
intermittent inert-boot race (3/6 repro — gravity flag flips before the
first ground-force evaluation) fixed: set_gravity returns only after
the first evaluation under the flag.

**Fleet-4 lanes that fed the above:** H4 softmax vertbind REFUTED by its
falsifier (crease WORSE 30% + tears; pin sets identical — the residual
crease is weight MAGNITUDES at dominance boundaries; route 3 =
soften/widen kernel or radius-limit limb influence, still open); H6
funnel e2e PASS (site→demo→2 lessons→signup row; D1 = the shared per-IP
stream bucket starves two cameras behind one NAT); H11 (og:image 200,
signups hygiene 5→2, hero copy to the ten-lesson product; caught the
LIVE site process predating its hardening — it served signups.jsonl
raw; "a hardening commit does not boot itself"); H12 (supervisor spawns
the exe DIRECTLY — launch_chimera.bat's `start` detached it so Ctrl+C
could never stop the engine; stack-from-zero ~8 s; operator-only
residuals: domain, tunnel, payment); H14 (bench --scratch one-command;
a name-filtered taskkill took the LIVE engine down once — restored ~40 s
from snapshot; kill-by-PID-only is now law); H15 (gallery 5/5 baseline
bit-identical; torus+capsule are the guard sentinels).

**Engine ops update:** the live engine's cwd IS
.tmp/build_tick/Release (session_snapshot lives there); relaunch =
Start-Process exe '8107' '--hidden' with that -WorkingDirectory; verify
with /tick_state (ticks advancing + n_cells=4 + seal_refusal empty).
Verify liveness AFTER every build window — a window-3 binary died
silently between checks.

**Remaining after the walk:** window #6 (rebuild + R5's audited gait
run), R8 blind-judge round 4 via the committed playbook
(R8_R4_PLAYBOOK/PLAYBOOK.md — judges PLAY the demo now), R9 public
hosting (operator-gated), seam route 3, mid-range machine for R6.

## ASTRA ROUND 2 + THE POST-JUDGE ROADMAP (2026-09-15)

**Astra Round 2 delivered IN CHAT** (Alan: "Put the prompt in chat" —
paste-ready block as the response, never just queued; reinforced: "give
that work to Astra only the difficult stuff"). Three items awaiting
Astra's reply: (1) the swapchain follow-up — the discriminating harness
CANNOT reproduce the engine's ~900 ms readback stall headless (2.16 ms
full pull; fence_wait grows with prior queued work, size-independent;
suspect = in-flight swapchain/present chain; ~27 present intervals at
30 fps); (2) XPBD frequency fidelity — the coupled solve is bounded at
every n, but converged frequencies bias low (n=4: coupled 1949→1222.7
rad/s; bias matches the converged-substep map; ±10% needs n≥11) — asked
for a compliance correction + ≤100-line prototype (the Astra-grade CODE
piece); (3) the minimal honest reflex arc for "the creature answers"
(candidates: pressure-threshold local servo arcs, autonomic torso
breathing, startle-into-stance) — the design source for the next product
lane.

**Next fleet lanes (the judge roadmap, in-house):** the creature-answers
prototype (built from Round-2 Item 3's answer) and the lessons 4-10
by-hand completion audit (headless walker passes 10/10 but by-hand judges
hit L4 passing itself with no control offered and L5's shins goal never
registering — the walker's judge and the player experience disagree).
The dyad-judge integration is live as one command
(tools/dyad_judge/run_judge.py; registry additive schema; the $25 gate
machine-checkable via --gate-report, OPEN until a blind judge's pay25).
