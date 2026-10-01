# H10 walker-auditor — why the ten-lesson walk scored 4/10 with contradictory records

READ-ONLY audit. No code was changed; nothing was run against the live stack (pure static
analysis of the served page code plus the evidence already on disk). Every "code-verified"
claim below names the file and line.

**The single most important fact: the evidence dir holds TWO runs of the SAME script
(`tools/game_shell/walk_lessons10.js`), five minutes apart.**

| run | artifact | verdict | page errors |
|---|---|---|---|
| attempt 2, ~07:35-07:41 | `R4_TEN_WALK/walk10_attempt2_summary.txt` | **4/10**, two goalMet=true-FAILs | **1419, all 429** |
| attempt 3, ~07:41-07:46 | `R4_TEN_WALK/walk10_log.txt` + `verdicts_walker.json` | **10/10** | **0 (zero)** |

Attempt 3 is not a different measurement method — it is the identical walker on a quiet
loopback. The pipeline is not lying in two directions; one run was storm-corrupted and one
was clean. The save timestamps bracket it: attempt 2's save (`saved_at 07:40:10`, preserved
as `R4_TEN_WALK/walker_progress_before.json`) holds exactly the 4 fresh passes; attempt 3's
save (`saved_at 07:46:19`, `R4_TEN_WALK/progress_walker.json`) holds 10/10.

---

## 1. THE PASS-RULE MAP (static, code-verified)

**Walker side (`tools/game_shell/walk_lessons10.js`):**

- The walker plays each lesson once, in pack order, advancing with `]`. At each lesson's
  report moment it reads `#judge-debug` and regexes
  `judge: (\S+) phase=(\S+) goalMet=(\S+) passed=(\S+)` (walk_lessons10.js:162-170).
- **PASS rule** (walk_lessons10.js:502): `ok = v.passed && v.id === packIds[i]` — i.e. the
  page's own `passed` flag must be TRUE **in this session, on this lesson, at the report
  moment**. It is a fresh-pass rule by construction.
- **It does NOT diff the progress file.** The `PROGRESS FILE:` line is informational only —
  the save happens once at the end via `#save-btn` / `#payoff-save`
  (walk_lessons10.js:480-493). A lesson can therefore be judged FAIL in the table while a
  previous session's save still holds it; that is not the contradiction here (attempt 2's
  save held exactly its 4 fresh passes).
- **Between lessons the walker resets nothing but its own peak sampler** (`resetPeaks()`,
  walk_lessons10.js:198). It does not re-arm or clear any page state.
- **Stale-latch hazard, neutralized:** the page CAN pre-latch a lesson from a restored save —
  progress load sets `lessonState[id] = {goalMet:true, passed:true, phase:'done'}`
  (index.html:1591-1593). The walker kills this path by clearing the save before signing in:
  `POST /api/progress {lessons:{}}` (walk_lessons10.js:131). Attempt 3's log proves the clear
  landed (`RESET: walker progress cleared -- lessons now: []`, walk10_log.txt:3). Attempt 2's
  clear is proven after the fact: all ten attempt-2 judge rows show `phase=goal|release`,
  never `phase=done` — no row was pre-latched (anomaly lines 1-10).

**Page side (`tools/game_shell/index.html`), the judge the walker reads:**

- `lessonState[id]` latches persist for the page's lifetime, keyed by lesson id
  (index.html:427-429). Navigating between lessons does NOT clear them; `showLesson` only
  reads them ("PASSED — this one is yours already", index.html:478). The walker visits each
  lesson once, so no revisit artifact occurred.
- `passed=true` has exactly three origins: a pose latch on an ACCEPTED post
  (pose_reach index.html:507, pose_pair index.html:527 — `observePose` refuses to latch when
  the engine answers not-ok or the POST fails, index.html:495-504); a non-release goal latch
  (`then_release:false`, index.html:1222); a release-phase calm poll
  (index.html:1227-1238).
- Release lessons (`then_release:true`): goal latch flips `phase` goal→release
  (index.html:1216-1220); pass then requires a poll where **every cell the engine reports**
  has `|P| < 1000 Pa` (index.html:1232: `cells.every(...)`). This "every cell" predicate is
  the sink into which the degenerate 5th cell drains (see §3, L7/L10).
- The judge only evaluates on a SUCCESSFUL `/api/state` poll — `pollState` catches any HTTP
  error and skips `judgeState` + `renderJudgeDebug` (index.html:1085-1098). During 429
  windows the judge line FREEZES at its last value; the walker reads a stale line and cannot
  tell.
- `pollState` runs at 700 ms (index.html:1805); `pollVerts` at 333 ms (index.html:1804) —
  the page alone consumes ~266 req/min of the shell's per-IP stream bucket.

**Server side (`tools/game_shell/server.py`):** one token bucket per IP per class; EVERY
actuation and read the walk needs — `/api/touch_hit`, `/api/touch_clear`, `/api/pose`,
`/api/gravity`, `/api/state`, `/api/verts` — shares the single `stream` bucket (600/min,
burst 240; server.py:50-56). Every fleet agent on 127.0.0.1 shares ONE bucket. This is the
storm's anatomy.

---

## 2. THE ANOMALY, LINE BY LINE (attempt 2, `walk10_attempt2_summary.txt`)

Legend for "clean twin": the same lesson in attempt 3 (`walk10_log.txt`), same script, quiet
loopback. All line references code-verified in the working-tree `index.html` (unmodified in
git status, hence the served page).

| # | lesson | anomaly says | mechanism (most probable, code-consistent) | class |
|---|---|---|---|---|
| 1 | wake_the_cell | PASS release goalMet=true | Clean window. Torso press landed (peak 2,135,680 Pa >= 20 kPa), goal latched, ESC, calm poll (cell4 still 0) -> passed. Identical in clean twin (log:8-14). | genuine pass |
| 2 | the_gentle_hand | FAIL goal, goalMet=false, **all cells 0** | The 6 kN foot press never produced pressure at the engine within any observed poll: `POST /api/touch_hit` 429'd (index.html:1337 — on !res.ok `holding` stays false, the press silently dies) and/or every state read in the window starved, so the judge (which only runs on a good poll, index.html:1090) never saw anything. Clean twin: identical maneuver -> feet 6,772,550 Pa, PASS (log:15-21). Deterministic physics says the press itself died, not the threshold. | (c) press-pipeline death by 429 |
| 3 | the_healing | PASS release goalMet=true | Clean window, same shape as L1 ("any" cell >= 20 kPa; torso 2,135,680 Pa). Clean twin identical (log:22-28). | genuine pass |
| 4 | bend_the_knee | FAIL goal, goalMet=false, all cells 0 | The `#pose-btn` click posts `/api/pose knee_L 40`; `observePose` latches ONLY on `body.ok===true` (index.html:495-507). The post was refused/429'd -> no latch. Proof the engine never moved: attempt-2 peaks are ALL zero, while the clean twin's same pose blows cell4 to 2,609,590,000 Pa (log:29-33) — the deformation never happened. Matches the known "pose-refused-without-reason" defect (commit 569083bb). | (c) actuation death (pose post) |
| 5 | the_whole_body | PASS release goalMet=true | Clean window: torso 2,135,680 Pa (>= 15 k) and shins 87,496,300 Pa (>= 5 k) both latched, then calm. Clean twin identical (log:34-42). | genuine pass |
| 6 | the_balance | PASS goal goalMet=true — "suspicious pass at rest" | NOT an artifact. pose_pair judges the POSTED INTENT only — `judgeState` returns early for pose lessons (index.html:1134); cells are irrelevant to its latch. The ankle posts were accepted: the attempt-2 peaks (6009940 / 8788 / 715501 / **1622780000**) are byte-identical to the clean twin's L6 pose signature (log:43-47) — the engine really took ankle_L +5 / ankle_R -5. `phase=goal` (not `done`) proves no save-restore pre-latch. BUT this lesson is where the world defect detonates: holding ankle poses deforms the degenerate cell4 (V0 ~ 3e-9 m3, i.e. V=0 in the pack's 4-cell model) to P = 1,622,780,000 Pa, and pose lessons skip `showLesson`'s `resetPose` (index.html:448-452), so the garbage rides into every later lesson. | genuine pass; side effect = the L7/L10 poison |
| 7 | the_heavy_hand | **FAIL release goalMet=true** | The click spiral landed: torso peak 11,928,400 Pa >= 3 MPa -> goalMet, then_release -> phase=release. Pass needs ONE calm poll with EVERY cell < 1000 Pa (index.html:1232). cell4 was still at 1.6228 GPa — held there because `showLesson`'s `resetPose()` (which restores the joints and lets cell4 decay, tau=0.5 s — the clean twin shows cell4 back to 0 by L7, log:62) is fire-and-forget and its six `/api/pose` posts 429'd. Attempt-2 L7 peaks carry L6's EXACT pose signature (6009940/8788/715501/1622780000) — the ankle pose was still live. A permanently-pressurized garbage cell inside an "every cell" predicate = can never pass. goalMet=true + FAIL is exactly this shape. Contributing risk: `clearTouch` is fire-and-forget too (index.html:1471-1478) — a 429'd touch_clear leaves the engine pressing (the "sticky phantom press" of commit 569083bb). The save confirms it never recovered: attempt 2's final save holds no the_heavy_hand. | (b) calm predicate x world cell4, enabled by 429 |
| 8 | the_cascade | FAIL goal, goalMet=false, cell1 peak = 0 | NOT the old judge-hold: the gate passed ("served page carries pose_pair AND pressure_isolation", walk10_log.txt:1) and the judge now evaluates pressure_isolation (index.html:416, 1162-1169); the clean twin PASSES this lesson (torso 2,135,680 Pa, quiet cells 0, log:63-76). In attempt 2 the traced 3.5 s belly press produced NOTHING (cell1 peak 0 Pa) — same death as L2: touch_hit 429'd / state reads starved. Judge never saw torso >= 15 kPa -> no latch. | (c) press-pipeline death by 429 |
| 9 | the_stand | FAIL goal, goalMet=false | gravity_on goal needs `gravityArmed && |root_vy|<=0.05 && |root_y|>0.002` (index.html:1205-1207). **Code-verified page bug:** the arm is `postJSON('/api/gravity',{on:true}).then(()=> gravityArmed=true)` (index.html:464-470) with NO `res.ok` check — fetch resolves on HTTP 429, so a REJECTED enable still arms the judge while the engine never turns gravity on; root_y stays exactly 0 and the goal can never latch. The walker's safety net then misfires: its fallback posts gravity directly only if it never sees `armed=true` (walk_lessons10.js:444-452) — the false arm suppresses it. Alternative sub-mechanism, same storm: gravity enabled but every judge poll in the ~11 s window starved (frozen line). Attempt 3: armed=true, root settles 9.5 mm, PASS (log:77-82). | (b) false-arm page bug + storm |
| 10 | the_graduation | **FAIL release goalMet=true** | Same artifact as L7. Three real cells woken (peaks: feet 65.3 MPa, torso 2.13 MPa, shins 86.3 MPa, each >= 20 kPa) -> wokenSet >= 3 -> goalMet (index.html:1208-1214; note cell4's 1.62 GPa garbage ALSO counts as "woken" there — a spurious extra latch, index.html:1211-1212) -> phase=release -> calm check sees cell4 at 1.6228 GPa -> can never pass. Clean twin passes once resetPose works and cell4 reads 0 (log:83-95). | (b) calm predicate x world cell4, enabled by 429 |

**Why 4/10 and why those 4:** the four passes are exactly the lessons whose decisive events
(a) got a clean window and (b) needed no calm poll after cell4 detonated — L1/L3/L5 happened
before the balance's poses, and L6 is a pose lesson that passes without any calm check. The
two goalMet=true-FAILs are exactly the two release lessons judged after L6 poisoned cell4.

---

## 3. CLASSIFICATION — what the fixing agent must vs must not touch

**(a) Walker-logic artifacts: NONE.** The PASS rule is sound (fresh in-session `passed` on
the right lesson; progress diff correctly NOT part of the rule). Two walker weaknesses for
the record, neither verdict-changing: its L9 fallback trusts the page's `armed=true` (which
can be a false arm); its sampler treats starved polls as silent zeros instead of counting
them.

**(b) Page judge-state / robustness defects (`tools/game_shell/index.html` — page owner):**
1. gravity false-arm: `.then()` sets `gravityArmed` without checking `res.ok`
   (index.html:467-469). One-line fix. Directly produced L9's unpassable state and defeated
   the walker's diagnostic fallback.
2. `clearTouch` fire-and-forget (index.html:1478): a 429'd touch_clear = engine keeps
   pressing (phantom press). Needs res.ok + retry.
3. `showLesson`'s `resetPose()` fire-and-forget (index.html:452): six sequential pose posts,
   none checked; under storm the previous lesson's pose-held deformation (and cell4's
   garbage) carries into the next lesson's judge window. Needs await/retry.
4. Missing garbage-cell guard: the release calm predicate (`cells.every`, index.html:1232)
   and cells_woken (index.html:1211-1212) trust every cell the engine reports; a degenerate
   cell with GPa-scale P permanently fails the former and spuriously latches the latter.
   A cheap page-side guard (skip cells with absurd |P| or V0 below epsilon) would have made
   L7/L10 pass in attempt 2.

**(c) Press/actuation-pipeline deaths (storm, not code):** L2 and L8 (touch_hit), L4 (pose
post). All three passed in attempt 3 with identical scripted input — proven transient. Root
is the shared per-IP stream bucket (server.py:50-56) shared by every loopback co-tenant; the
1419-error run is what co-tenants look like to each other.

**(d) Genuinely-held world-state lessons: NONE in this run.** the_cascade — the only
historical hold in the 9/10 era — held because the served judge could not evaluate
pressure_isolation at all (commit 09e71b55); it is implemented now and passes cleanly
(clean log:63-76). the_stand's stance/gravity machinery works (clean log:77-82). Nothing
failed in attempt 2 because the world truly could not satisfy it.

**World defect (owned by the matter-kernel/engine agent, already known):** cell4 reports
V0 ~ 3e-9 m3 (the pack's model has FOUR cells, 0-3). P is a sane 0 only at exact rest
(`world_state_after.json`: V=4.66e-9, P=0); any pose-induced deformation produces deterministic
garbage — 0.75 GPa (`world_state_before.json`), 1.62 GPa (ankle pair), 2.61 GPa (knee 40) —
which decays only when the pose resets. Until cell4 gets a real rest volume, is excluded from
`/api/state`, or is flagged, every multi-cell predicate on the page is poisoned.

---

## 4. ROOT EXPLANATION (the one paragraph)

The ten-lesson measurement pipeline does not lie in two directions; attempt 2 was starved and
attempt 3 was not. The shell rate-limits per IP with one 600 req/min stream bucket shared by
every actuation and read the walk depends on (server.py:50-56) — and every fleet agent on
127.0.0.1 shares that single bucket — so under co-tenant load the walker's presses, poses,
and gravity enable, and the judge's own state polls, died intermittently (1419 console 429s);
passes survived only where a decisive actuation happened to land in a clean window, the two
goalMet=true-FAILs are the two release lessons whose "every cell < 1000 Pa" calm predicate
could never be satisfied after lesson 6's accepted ankle poses inflated the engine's
degenerate fifth cell (V0 ~ 0 -> P = 1.62 GPa) while the same storm also silenced the page's
own fire-and-forget resetPose that would have healed it, and the historical 9/10 predates the
pressure_isolation judge (commit 09e71b55) so the_cascade's old hold was judge-blindness, not
physics. The same script, on a quiet loopback five minutes later, scored 10/10 with zero page
errors — that is the verified state of the lessons; the 4/10 is a measured record of the
storm, and both records are honest.

## 5. FIX LIST

**To the page owner (`tools/game_shell/index.html`) — do these:**
1. L467-469: `if (res.ok) stg.gravityArmed = true;` — kill the false arm (L9).
2. clearTouch: check `res.ok`, retry on 429 (phantom press).
3. showLesson: await resetPose() (or retry its posts) before the lesson window starts.
4. Guard the judge's per-cell predicates against degenerate cells (calm `every` and
   cells_woken): skip cells with non-finite or absurd |P| / negligible V0.

**To the engine/world owner (matter-kernel cell4):**
5. The 5th cell's rest volume is ~0 (3e-9 m3) so P=(V0-V)/(kappa*V0) explodes under any pose
   deformation (0.75/1.62/2.61 GPa measured). Give it a real V0, exclude it from
   `/api/state`, or flag it — until then the page's calm predicate is unpassable whenever a
   pose is held and its reset fails.

**To the fleet/infra owner (not fixed here):**
6. The per-IP stream bucket is shared by all loopback agents; stagger fleet runs against one
   shell or partition the bucket per agent, or every co-tenant walk re-rolls attempt 2.

**Walker owner (optional, for the record):**
7. L9 fallback should verify the world (`gravity_on`, `root_y` from /api/state) instead of
   trusting `armed=true`; the sampler should count starved polls into the verdict table
   instead of printing them as 0 Pa.

*Method note: pure static analysis + existing evidence; nothing was executed against the
live stack (engine 8107 / shell 8206 untouched). Sources: tools/game_shell/walk_lessons10.js;
tools/game_shell/index.html (lines cited inline); tools/game_shell/lessons.json;
tools/game_shell/server.py; docs/evidence/agent_fleet/SHIP/R4_TEN_WALK/{walk10_attempt2_summary.txt,
walk10_log.txt, verdicts_walker.json, progress_walker.json, walker_progress_before.json,
world_state_before.json, world_state_after.json}.*
