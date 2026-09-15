# C1 CREATURE ANSWERS — DESK-CHECK NOTE

**No engine build was performed** (the lead owns window #8). The new code has
NOT been compiled; this note is the verification until then. Every named trap
was addressed explicitly, and the trap-prone logic that could be exercised
standalone WAS executed (not just read).

## The named traps

1. **Windows.h `small`** — main.cpp includes `<windows.h>` (rpcndr.h
   `#define small char`). Checked: no identifier named `small` (or `min`/
   `max` as unqualified calls) anywhere in the new code; the only `small`
   in main.cpp is inside a pre-existing comment. membrane_tick.cpp includes
   only std headers (`<cmath>` already present for `std::pow/sin/cos/exp`,
   `<cstdint>` in the hpp for `uint64_t`). Name-collision grep for every new
   identifier (`REFLEX_*`, `DEG2RAD_F`, `get_bool`, `ReflexState`,
   `reflex_*`) returns nothing outside the new code.
2. **stod-on-booleans** — `std::stod("true")` throws and the catch silently
   returns the default: a `{"pressure_coupling":false}` cut would have
   flipped itself back to `true`. The route parses the master `"on"` with
   the house literal-substring law (the /tick_gait precedent) and channels
   with a new `get_bool` (find_colon_after + first-character `t`/`f`),
   never stod. **Executed check**: the exact helper code compiled standalone
   (g++ -Wall -Wextra, zero warnings) and run against 16 bodies — compact
   arm, spaced disarm (the documented hazard), the nerve-cut body, missing
   keys, malformed values, value-shadowed keys, prefix-colliding keys:
   **16/16 pass** (`parse_check.cpp`, transcript in the commit message and
   DESKCHECK_PARSE.txt).
3. **Compact-JSON parse hazard** — `/tick_reflex` follows /tick_gait and
   /tick_stance exactly: `{"on": true}` (with a space) parses as DISARM.
   Documented in the route comment and in BATTERY.md's curl examples
   (compact bodies only).

## Structural checks

- Brace/paren balance via a comment/string-aware state machine: **0/0** on
  all three edited files, identical to the pre-edit baseline
  (`deskcheck_balance.py`).
- The three `step()` hooks are `if (reflex_.armed) ...` — one bool check on
  the default path; with reflexes OFF the executable path of step() is
  byte-identical to before (the gait_verify control leg, run on the CURRENT
  binary, is the behavior reference: 15/15 PASS,
  `gait_verify_control_scratch8164.json`).
- Bounds: every `joint_deg_[pin]` write is preceded by a size check; every
  slot read is guarded `sl < nv`; the detector reseeds (prev_p := current
  pressures) whenever the sealed-cell count changes — a new cut can never
  read as a pressure spike; `reflex_ = ReflexState{}` in init() (the C1
  stale-index crash class).
- Locks: every new method takes `seal_mtx_` (or is called under it from
  step()); `reflex_summary_json()` is const and locks, like
  `state_json()`.

## Manual review checklist (read twice, line by line)

- Pass order in step(): travel → press → volumes/pressures → **detect**
  (flinch/startle; pin writes same-latency as stance/gait) → stance →
  **startle compose** → gait → **breath** (last surface pass, before the
  root offset) → gravity. The breath is invisible to the pressure law, the
  conservation export, foot sets, lean, and depth BY CONSTRUCTION;
  PREREG R1's prediction makes window #8 MEASURE it.
- Ownership handoffs: the flinch writes only unowned pins and holds a
  per-side `pin_held` flag so its final zero lands exactly once and never
  stomps a rung that armed mid-flinch; the startle composes OVER
  `stance_th_` and clamps the TOTAL inside the 5 deg ankle cap.
- The nerve cut gates only the TRIGGERS; `prev_p` keeps tracking the true
  pressure while cut, so reconnecting the nerve cannot synthesize a stale
  rising edge (the negative control must not leak into the positive case).
- Deterministic off: envelopes, phase, and any reflex-held pin return to
  authored bearing exactly (the flex-0 precedent); a mesh swap clears all
  reflex state and the route is the only re-arming path.

## Known compile-risk residue (for window #8's build log)

Honest list of what a desk-check cannot prove: MSVC-specific conversions
were kept trivial (explicit casts on all double←float Narrowings in the
allometry code); `static const char* kReflexChannels[]` is a function-local
static inside the route lambda (legal C++); no C++17-and-beyond features
beyond what the file already uses. If the build fails, the first suspects
in order: (1) the route lambda's static array, (2) the
`std::string + const char*` chains in `set_reflex`'s block accumulation,
(3) an implicit wide-char/`L` mismatch — none expected.
