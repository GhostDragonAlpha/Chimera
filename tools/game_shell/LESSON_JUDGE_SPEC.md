# LESSON_JUDGE_SPEC — how the game page decides pass/fail (R4)

The judge lives in the page (`tools/game_shell/index.html`). It consumes two
channels only:

1. **`GET /api/state`** — polled every **~700 ms** (proxied by `server.py` to the
   engine's `GET /tick_state`).
2. **`POST /api/pose`** — the page's own pose sender, observed by the judge
   (proxied to the engine's `POST /tick_pose`).

The lesson pack is `lessons.json` next to this file (schema documented in its
`_format` field). Ten lessons, played in array order — lessons 6–10 added
2026-09-13, introducing three goal types (`pose_pair`, `gravity_on`,
`cells_woken`). This spec is the exact pseudocode for the judge loop;
`wake_the_cell` is already implemented in the page and matches it. The first
five lessons are live; lessons 6–10 are the page team's implementation
contract (§6 extended, §10, §11).

---

## 1. The state shape (verified against `membrane_tick.cpp::state_json`)

```json
{
  "ticks": 12345, "enabled": true,
  "cells": 4,                        // trap: an INT count, emitted first ...
  "n_cells": 4,
  "V_lower": ..., "V_upper": ..., "P_lower": ..., "P_upper": ...,
  "root_y": 0.0, "root_vy": 0.0,     // the fall — the_stand (gravity_on) judges these
  "cells": [                         // ... then the ARRAY. Last key wins in
    {                                // JSON.parse / json.loads, so after
      "v0": 0.288,                   // parsing, state.cells IS THIS ARRAY.
      "V": 0.288,                    // volume now, m3
      "P": 0.0,                      // gauge pressure, Pa (0 = healed)
      "pieces": ..., "caps": ..., "ylo": ..., "yhi": ...
    }
    // 4 entries: 0 feet, 1 torso, 2 thighs, 3 shins
  ],
  "has_scene": true
}
```

The judge reads `state.cells[i].P` (`state.n_cells` guards the length). The
`gravity_on` goal additionally reads `state.root_y` / `state.root_vy`, verified
emitted by `membrane_tick.cpp::state_json`.
Pressures are **gauge Pa**: ~0 at rest, ~+2.1 MPa on the torso at a 30 kN press
(P is linear in force; ~3.5 MPa at the 50 kN slider max — re-measured
2026-09-13; the +0.5 MPa figure that stood here predated the vertex-snap fix).

## 2. Constants

```js
const POLL_MS       = 700;    // judge tick; <= 1000 ms so heals are never missed
const CALM_PA       = 1000;   // then_release passes when every |P| < 1000 Pa
const POSE_TOL_DEG  = 2;      // pose intent tolerance around goal.deg
const HINT_AFTER_MS = 25000;  // show lesson.hint once if GOAL stalls this long
const TAU_S         = 0.5;    // measured release decay (do not hardcode elsewhere)

const JOINT_INDEX = { hip_L: 13, hip_R: 14, knee_L: 15,
                      knee_R: 16, ankle_L: 17, ankle_R: 18 };

// lessons 6-10 (2026-09-13):
const ROOT_VY_SETTLE = 0.05;  // m/s — "settled means settled" (tools/gravity_test.py VY_SETTLE)
const ROOT_SETTLE_M  = 0.002; // m — |root_y| must exceed this: the root left its authored rest
const WOKEN_PA       = 20000; // Pa — cells_woken: a cell counts as woken at P >= this
```

## 3. Judge state — reset per lesson, latches sticky

```js
let lesson = null;          // the current lesson object from lessons.json
let judge = null;

function startLesson(L) {
  lesson = L;
  judge = {
    phase:   "GOAL",        // GOAL -> (if then_release) RELEASE -> PASSED
    main_ok: false,         // latch: goal's own condition crossed at some poll
    also_ok: !L.goal.also,  // latch: 'also' condition (true when absent)
    pose_ok: false,         // latch: accepted pose intent observed (pose_reach)
    pair_ok: {},            // pose_pair: joint name -> sticky per-joint latch
    gravityArmed: false,    // gravity_on: true once the enable POST resolved
    woken: new Set(),       // cells_woken: distinct cell indices latched so far
    passed:  false,         // pass detection EXACTLY ONCE
    startedAt: Date.now(),
    hintShown: false,
  };
}
```

A **latch** goes `false -> true` and never back. A calm or noisy poll can never
un-latch it; only `startLesson` resets latches. "At any moments" in lesson
bodies means exactly this: each latch is keyed to its own crossing poll.

## 4. The judge loop

```js
setInterval(judgeTick, POLL_MS);

async function judgeTick() {
  if (!lesson || judge.passed) return;

  // -- read the world -----------------------------------------------------
  let s = null;
  try { s = await fetch("/api/state").then(r => r.json()); } catch (e) {}
  if (!s || !Array.isArray(s.cells)) return;          // world unreachable:
                                                      // HOLD state, never
                                                      // pass and never fail
                                                      // the player for it
  const cells = s.cells;
  if (cells.length < (s.n_cells || cells.length)) return;  // partial read: skip

  // -- latches (order-independent; sticky) --------------------------------
  const g = lesson.goal;
  if (g.type === "pressure_above" || g.type === "pressure_below") {
    if (!judge.main_ok && cellCondition(cells, g))    judge.main_ok = true;
    if (!judge.also_ok && cellCondition(cells, g.also)) judge.also_ok = true;
  } else if (g.type === "gravity_on") {
    // the_stand: settled = enabled AND the root has left its authored rest
    // AND is no longer moving. root_y is exactly 0 at the authored rest, so
    // neither condition can fire before the fall; measured settle ~9.5 mm.
    if (!judge.main_ok && judge.gravityArmed &&
        Math.abs(s.root_vy) <= ROOT_VY_SETTLE &&
        Math.abs(s.root_y)  >  ROOT_SETTLE_M)      judge.main_ok = true;
  } else if (g.type === "cells_woken") {
    // the_graduation: squeeze only (negative P never wakes), sticky set
    cells.forEach((c, i) => { if (c.P >= WOKEN_PA) judge.woken.add(i); });
    if (!judge.main_ok) judge.main_ok = judge.woken.size >= g.count;
  }
  // pose latches (pose_reach AND pose_pair) live in observePose (section 6).

  // -- phase machine -------------------------------------------------------
  if (judge.phase === "GOAL") {
    if (!judge.hintShown && Date.now() - judge.startedAt > HINT_AFTER_MS) {
      judge.hintShown = true;
      showHint(lesson.hint);                          // once, softly
    }
    if (goalComplete()) {
      if (lesson.then_release) {
        judge.phase = "RELEASE";
        verdict("it answered — now let go, and let it heal");
      } else {
        pass();
      }
    }
  } else if (judge.phase === "RELEASE") {
    if (allCalm(cells)) pass();
    // Holding keeps P up, so allCalm stays false: the physics itself enforces
    // "the player let go". No hold-tracking is needed.
  }
}
```

## 5. Evaluating the goal types

```js
// pressure_above / pressure_below / the 'also' extension, one shape:
function cellCondition(cells, cond) {
  if (!cond) return false;                                                    // guard
  const ps = (cond.cell === "any")            // 'any' (the_healing): the goal
    ? cells.map(c => c.P)                     // latches if ANY ONE cell crosses
    : [cells[cond.cell].P];                   // 0 feet, 1 torso, 2 thighs, 3 shins
  return cond.type === "pressure_above"
    ? ps.some(P => P >=  cond.threshold_pa)
    : ps.some(P => P <=  cond.threshold_pa);  // pressure_below: reserved shape,
}                                             // unused by the whole pack

function goalComplete() {
  const g = lesson.goal;
  if (g.type === "pose_reach")  return judge.pose_ok;
  if (g.type === "pose_pair")   return g.joints.every(j => judge.pair_ok[j.joint]);
  if (g.type === "gravity_on")  return judge.main_ok;     // the settle latch
  if (g.type === "cells_woken") return judge.woken.size >= g.count;
  return judge.main_ok && judge.also_ok;      // also_ok === true when no 'also'
}

function allCalm(cells) {
  return cells.every(c => Math.abs(c.P) < CALM_PA);   // every cell |P| < 1000 Pa
}
```

Per lesson, concretely:

| lesson | GOAL latches when | RELEASE |
|---|---|---|
| wake_the_cell | `cells[1].P >= 20000` | all `\|P\| < 1000` |
| the_gentle_hand | `cells[0].P >= 50000`, force <= 8000 N (capped — see below) | all `\|P\| < 1000` |
| the_healing | any one `cells[i].P >= 20000` | all `\|P\| < 1000` |
| bend_the_knee | accepted `POST /api/pose` `joint_index===15 && \|deg-40\| <= 2` | none (`then_release: false`) |
| the_whole_body | `cells[1].P >= 15000` AND, at any moment, `cells[3].P >= 5000` | all `\|P\| < 1000` |
| the_balance | accepted posts: `ankle_L`(17) at `5 ± 2` AND `ankle_R`(18) at `-5 ± 2`, any order | none (`then_release: false`) |
| the_heavy_hand | `cells[1].P >= 3000000` | all `\|P\| < 1000` |
| the_cascade | `cells[3].P >= 5000` — the belly is the lesson's ONLY touch target | all `\|P\| < 1000` |
| the_stand | gravity enabled AND `\|root_vy\| <= 0.05` AND `\|root_y\| > 0.002` (§10) | none (`then_release: false`) |
| the_graduation | 3 distinct cells each reached `P >= 20000` at some poll (§11) | all `\|P\| < 1000` |

Rows 1–5 transcribed 2026-09-13 from the re-tuned `lessons.json` (the
200 kPa-era numbers that used to stand here predated the re-tune; the pack is
the single source of truth, and the_gentle_hand's 50000 Pa restores the value
its own body copy states — reachable gently since the vertex-snap fix).
`max_force_n`: the live page gates the latch on the touch force — while
`lastTouchForce > max_force_n` the judge tick returns early
(`index.html::judgeState`), so an over-force press can never latch a capped
lesson; the pseudocode above omits that gate for brevity.

## 6. The pose goals — judged on the POSTED INTENT (pose_reach, pose_pair)

The judged condition is the intent the player posts, not the pressures that
follow. The page routes every pose through one sender; the judge observes it
and latches only when the **engine accepted** (`ok: true` — the engine refuses
unknown joints and `|deg| > 90` with `ok: false`; a refused post never latches).

```js
async function postPose(joint_index, deg) {         // the page's ONLY pose path
  const res = await api("/api/pose", { joint_index: joint_index, deg: deg });
  observePose(joint_index, deg, res && res.ok === true);
  return res;
}

function observePose(joint_index, deg, accepted) {
  const g = lesson && lesson.goal;
  if (!g || (g.type !== "pose_reach" && g.type !== "pose_pair") || judge.passed)
    return;                                         // only pose goals latch here
  if (!accepted) return;                            // refused: do not latch
  if (g.type === "pose_reach") {
    const want = JOINT_INDEX[g.joint];              // knee_L -> 15
    if (joint_index === want && Math.abs(deg - g.deg) <= POSE_TOL_DEG) {
      judge.pose_ok = true;                         // sticky; pass fires on the
    }                                               // next judgeTick (or inline
  } else {                                          // call goalComplete if idle)
    for (const j of g.joints) {                     // pose_pair (the_balance):
      const want = JOINT_INDEX[j.joint];            // each entry latches on its
      if (joint_index === want &&                   // own accepted post; any
          Math.abs(deg - j.deg) <= POSE_TOL_DEG) {  // order, any moments
        judge.pair_ok[j.joint] = true;              // sticky, per joint
      }
    }
  }
}
```

The `+/-2 deg` tolerance exists for slider quantization; sliders post integers,
so a player setting 40 or 41 passes, 43 does not. If a future `/tick_state`
exposes pose intents, the poll may *cross-check* the latch, but the POST
observation alone is the defined judge.

`pose_pair` (`the_balance`) needs no machinery beyond this list: the lesson's
UI must produce two accepted posts (one per ankle; sliders post integers, so
5 and -5 are exact), and `goalComplete` (§5) waits until every entry in
`g.joints` has its sticky latch. Two opposing wishes, one body — the judge
does not care in which order they arrive.

## 7. Pass — exactly once, then save and advance

```js
function pass() {
  if (judge.passed) return;                 // the exactly-once guard
  judge.passed = true;
  verdict("PASSED — " + lesson.title);      // the green badge
  saveProgress(lesson.id);                  // fire-and-forget
  setTimeout(() => startLesson(nextUnpassedLesson()), 2500);  // advance
}

async function saveProgress(id) {
  const prog = await fetch("/api/progress?name=" + encodeURIComponent(name))
                     .then(r => r.json());
  prog.lessons = prog.lessons || {};
  prog.lessons[id] = { passed: true, at: new Date().toISOString() };
  await api("/api/progress", prog);         // server writes progress/<name>.json
}
```

- Progress keys are the lesson `id`s; **`wake_the_cell` is already live** in
  `index.html` and in existing `progress/<name>.json` files — do not rename it.
- On play start, load progress and `startLesson` the first lesson whose
  `lessons[id].passed` is not true; a passed lesson can always be replayed (a
  fresh `startLesson` resets the judge).
- The save is idempotent: re-passing rewrites the same shape with a new `at`.

## 8. Timing the release phase (measured: `tau = 0.5 s`)

On release, `P(t) = P0 * exp(-t / 0.5)`, reaching zero exactly. The RELEASE
phase therefore lasts `t_calm(P0) = 0.5 * ln(P0 / 1000)` seconds, then the next
poll passes it. With a 700 ms poll:

| peak P0 | time to calm | polls to pass |
|---|---|---|
| 20 kPa (wake_the_cell, the_healing, the_whole_body torso) | 1.5 s | ~2–3 |
| 50 kPa (the_gentle_hand) | 2.0 s | ~3 |
| 3 MPa (the_heavy_hand) | 4.0 s | ~6–7 |

The binding cell is the one with the highest PEAK, not the lowest threshold
(`allCalm` is every cell): the_cascade's belly press spikes the torso far past
the shins' 5 kPa goal, so budget its release by the torso's peak (up to ~4 s
at the forces that trip the cascade).

Two consequences, both worth telling the player in the lesson copy:

- **Nothing heals while holding** — a held touch keeps P up, `allCalm` stays
  false, and the phase waits. The "let go" button (`POST /api/touch_clear`) is
  the actual verb.
- **Do not poll slower than ~1 s.** A latch keyes off a single crossing poll;
  sustained holds make that safe for the GOAL phase, but the calm moment at the
  end of RELEASE is brief enough that a 2 s poll can sit between two polls
  straddling several seconds of real progress. 700 ms sees every lesson's
  release finish within one poll of its theoretical time.

## 9. Edge cases, in one place

- **World unreachable / malformed state** (`!s || !Array.isArray(s.cells)`):
  skip the tick silently. Never pass, never fail, never clear latches.
- **Duplicate `cells` key** in `/tick_state`: the int count is emitted first,
  the array second; every real parser keeps the last, so `s.cells` is the
  array. The judge additionally prefers `s.n_cells` for the length guard.
- **`cell` out of range** (bad lesson file): `cells[cond.cell]` would throw —
  the `cellCondition` guard returns `false` instead; a lesson that cannot be
  evaluated can never pass by accident.
- **`then_release: false`** (bend_the_knee): pass fires in the GOAL branch; the
  RELEASE branch is never entered.
- **Replay**: `startLesson` fully resets phase and latches; old progress never
  short-circuits a replay's judge, only the lesson *order* chooser.
- **English only** in every player-facing string (lesson bodies, hints,
  verdicts), per the lane rules.
- **Unknown goal types HOLD.** A lesson whose `goal.type` the page has not
  implemented must neither crash nor pass: guard `judgeTick`/`observePose`
  with a `KNOWN_GOAL_TYPES` check (`pressure_above`, `pressure_below`,
  `pose_reach`, `pose_pair`, `gravity_on`, `cells_woken`) and skip. Until the
  page ships §6/§10/§11, lessons 6–10 simply wait; the first five play
  exactly as before (the pack still loads — one JSON array, ten entries).
- **Gravity persists and is deterministic.** `set_gravity(true)` is
  idempotent and does not reset the root; `set_gravity(false)` returns the
  body to its authored rest exactly (`root_y = root_vy = 0`,
  `membrane_tick.cpp::set_gravity`). So a replayed `the_stand` with the body
  already settled latches on its first poll — correct, a re-passed lesson —
  and a gravity-off reset is clean if the page ever wants one.

---

## 10. The gravity goal — `gravity_on` (`the_stand`)

The page, not the player, turns the world on. The engine route is live —
`POST /tick_gravity {"on":true}`, wired to `MembraneTick::set_gravity`
(`main.cpp`) — and the page reaches it through a **new server proxy route**,
mirroring the pose one:

```
POST /api/gravity  ->  POST /tick_gravity        (server.py: page team adds it)
```

At `startLesson`, when the goal is `gravity_on`, the page enables once and
arms the judge when the POST resolves:

```js
if (L.goal.type === "gravity_on") {
  api("/api/gravity", { on: true }).then(() => { judge.gravityArmed = true; });
}
```

The settle latch lives in `judgeTick` (section 4). The goal completes on the
first poll where the body is SETTLED:

```js
judge.gravityArmed &&
Math.abs(s.root_vy) <= ROOT_VY_SETTLE &&   // 0.05 m/s — "settled means settled"
Math.abs(s.root_y)  >  ROOT_SETTLE_M       // 0.002 m  — the root left its rest
```

Measured backing (`tools/gravity_test.py`, THE FALL):

- The authored rest holds `root_y = 0` exactly and the enable does not move
  it, so neither condition can fire before the fall — no instant pass.
- The measured settle from that rest is **~9.5 mm** — over the 2 mm bar with
  margin; `VY_SETTLE = 0.05 m/s` is that script's own settled constant.
- **Cell pressures stay exactly 0 at rest under gravity** (F2). Gravity, once
  on, stays on for the rest of the arc, and the later RELEASE phases
  (`allCalm`, §8) are unaffected — resting cells read zero.

`the_stand` uses `then_release: false`: the lesson ends in stillness, not in
healing. Replays are idempotent (§9, gravity persistence).

## 11. The free-play goal — `cells_woken` (`the_graduation`)

No thresholds in the lesson object; the judge carries one wake bar and counts
distinct cells. SIGNED convention, same as `pressure_above` (the page's dyad
fix): only a squeeze latches — `P >= WOKEN_PA` (20000 Pa, the pack's wake bar
since `wake_the_cell`); expansion (negative P) never counts. The set is
sticky and cumulative; order and moments are free (§4 shows the latch).

```js
// goalComplete (section 5):
if (g.type === "cells_woken") return judge.woken.size >= g.count;   // 3
```

Calibration: P is linear in force, and the measured response puts any
compartment past 20 kPa at a small fraction of the slider minimum (a 500 N
touch already yields tens of kPa), so the graduation asks for breadth, not
strength — any three of the four rooms, touched however gently. The lesson
offers five touch targets (belly, both feet, both shins); the page cycles
them on each SPACE press, exactly as `the_whole_body` cycles two.
`then_release: true` — after the third cell latches, the player must let the
whole body heal (`allCalm`, §8); with gravity on this still passes, because
resting cells read exactly 0 (§10).
