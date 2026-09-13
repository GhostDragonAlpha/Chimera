# LESSON_JUDGE_SPEC — how the game page decides pass/fail (R4)

The judge lives in the page (`tools/game_shell/index.html`). It consumes two
channels only:

1. **`GET /api/state`** — polled every **~700 ms** (proxied by `server.py` to the
   engine's `GET /tick_state`).
2. **`POST /api/pose`** — the page's own pose sender, observed by the judge
   (proxied to the engine's `POST /tick_pose`).

The lesson pack is `lessons.json` next to this file (schema documented in its
`_format` field). Five lessons, played in array order. This spec is the exact
pseudocode for the judge loop; `wake_the_cell` is already implemented in the
page and matches it.

---

## 1. The state shape (verified against `membrane_tick.cpp::state_json`)

```json
{
  "ticks": 12345, "enabled": true,
  "cells": 4,                        // trap: an INT count, emitted first ...
  "n_cells": 4,
  "V_lower": ..., "V_upper": ..., "P_lower": ..., "P_upper": ...,
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

The judge reads **only** `state.cells[i].P` (and `state.n_cells` for the guard).
Pressures are **gauge Pa**: ~0 at rest, +0.5 MPa on the torso at a 30 kN press.

## 2. Constants

```js
const POLL_MS       = 700;    // judge tick; <= 1000 ms so heals are never missed
const CALM_PA       = 1000;   // then_release passes when every |P| < 1000 Pa
const POSE_TOL_DEG  = 2;      // pose intent tolerance around goal.deg
const HINT_AFTER_MS = 25000;  // show lesson.hint once if GOAL stalls this long
const TAU_S         = 0.5;    // measured release decay (do not hardcode elsewhere)

const JOINT_INDEX = { hip_L: 13, hip_R: 14, knee_L: 15,
                      knee_R: 16, ankle_L: 17, ankle_R: 18 };
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
    pose_ok: false,         // latch: accepted pose intent observed
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
  }
  // pose_ok is latched in observePose (section 6), not here.

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
}                                             // unused by these five lessons

function goalComplete() {
  const g = lesson.goal;
  if (g.type === "pose_reach") return judge.pose_ok;
  return judge.main_ok && judge.also_ok;      // also_ok === true when no 'also'
}

function allCalm(cells) {
  return cells.every(c => Math.abs(c.P) < CALM_PA);   // every cell |P| < 1000 Pa
}
```

Per lesson, concretely:

| lesson | GOAL latches when | RELEASE |
|---|---|---|
| wake_the_cell | `cells[1].P >= 200000` | all `\|P\| < 1000` |
| the_gentle_hand | `cells[0].P >= 50000` | all `\|P\| < 1000` |
| the_healing | any one `cells[i].P >= 400000` | all `\|P\| < 1000` |
| bend_the_knee | accepted `POST /api/pose` `joint_index===15 && \|deg-40\| <= 2` | none (`then_release: false`) |
| the_whole_body | `cells[1].P >= 200000` AND, at any moment, `cells[3].P >= 100000` | all `\|P\| < 1000` |

## 6. The pose goal — judged on the POSTED INTENT

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
  if (!lesson || lesson.goal.type !== "pose_reach" || judge.passed) return;
  if (!accepted) return;                            // refused: do not latch
  const want = JOINT_INDEX[lesson.goal.joint];      // knee_L -> 15
  if (joint_index === want && Math.abs(deg - lesson.goal.deg) <= POSE_TOL_DEG) {
    judge.pose_ok = true;                           // sticky; pass fires on the
  }                                                 // next judgeTick (or inline
}                                                   // call goalComplete if idle)
```

The `+/-2 deg` tolerance exists for slider quantization; sliders post integers,
so a player setting 40 or 41 passes, 43 does not. If a future `/tick_state`
exposes pose intents, the poll may *cross-check* the latch, but the POST
observation alone is the defined judge.

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
| 50 kPa (the_gentle_hand) | 2.0 s | ~3–4 |
| 200 kPa (wake_the_cell, the_whole_body torso) | 2.6 s | ~4–5 |
| 400 kPa (the_healing) | 3.0 s | ~5 |

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
