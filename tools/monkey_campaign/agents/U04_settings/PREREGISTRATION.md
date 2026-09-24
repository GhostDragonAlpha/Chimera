# U04 PREREGISTRATION — supported input settings: sensitivity, inversion, bindings

Frozen BEFORE implementation, 2026-09-24, against worktree base `b4de4de8`
(HEAD `b4de4de886a9c5bfba4572a2100b2104b178cb2d`). U04, verbatim (completion
map line 106): *"Sensitivity, inversion and bindings needed for the selected
controls work and persist."* Constraint, verbatim: *"Keyboard/mouse baseline;
controller support is an explicit product decision"* — NO controller support
is built here. Depends on U01 (integrated); U03 and X02 are in flight in the
same `product/` dir — disjoint filenames (`input_settings*.py` vs
`focus_policy*.py` / `session_flow*.py` / `input_mapper*.py` /
`follow_camera*.py`).

## RULE 0 — the theory, stated before the build

**STATEMENT** (disagreeable): the whole U04 settings surface — bindings
(per action, keyboard/mouse events), sensitivity (per axis), inversion (per
axis) — can live in ONE versioned JSON file whose loader is TOTAL: every
possible file content resolves to either (the declared settings, status
"loaded") or (the U01 default settings + a NAMED refusal list) — never a
partial accept, never a silent default — and whose values can never write the
seam's own numbers, because the schema has no keys for them and the apply
surface only ever hands DATA to the mapper's declared constructor parameters.

**PREDICTION** (not yet measured; measured by the tests below):
(a) Across 25+ named malformed/adversarial files (corrupt JSON, duplicate
keys, unknown schema/version, unknown/missing keys, wrong types, NaN/Infinity
literals, out-of-range sensitivity, unknown actions/axes) EVERY load returns
defaults with a non-empty, distinctly-coded refusal naming the offense — zero
silent accepts. (b) Across a 2000-payload fuzz of adversarial settings
vectors, load+apply leaves every seam constant
(`V_MAX_IN_BAND_M_S`, `OMEGA_MAX_RAD_S`, `INTERVAL_MS`, `HOLD_TICKS`,
`EXPIRY_TICKS`, `RELEASE_DECAY_MS`, `VALID_MS`, `PHYSICS_HZ`,
`SENS_RAD_PER_COUNT`'s module value, `DEFAULT_BINDINGS`) bit-identical and
every emitted record inside U01's bounds. (c) save -> load reproduces settings
exactly; a second save is byte-identical (canonical form). (d) Sensitivity
scales the mouse-delta->yaw conversion linearly up to the mapper's clamp; at
the top of the declared range (and at 100x baseline) `|yaw_rate|` never
exceeds `OMEGA_MAX_RAD_S = 1.6`. (e) `invert.yaw` flips the sign of the
mouse-driven yaw only. (f) With no settings file present, load returns
defaults (U01's exact baseline), status "first_run", and creates nothing.

**FALSIFIERS** (named now; any one firing kills the build as specified):
- F1 SILENT ACCEPT: any malformed/adversarial file that loads without a named
  refusal, or loads with refusal but settings != defaults (partial accept), or
  a refusal whose code/detail fails to name the offense. Corrupt, unknown
  schema/version, unknown/missing keys, wrong types, NaN/Infinity,
  out-of-range, unknown action/axis, duplicate JSON keys (top level or nested)
  must EACH refuse by name. (The campaign prereg's own law: duplicate JSON
  keys and non-finite numbers are refused.)
- F2 SEAM POISON: any settings file that, after load+apply, changes a seam
  constant (the numbers listed in (b) above) — including payloads that carry
  the seam constants' NAMES as keys with poisoned values. A settings file
  writes player preferences; it can never write the seam.
- F3 NON-SCALING OR BOUND-BREAKING SENSITIVITY: yaw not linear in the mouse
  counts at fixed settings (before the clamp); OR any emitted `|yaw_rate| >
  OMEGA_MAX_RAD_S` or non-finite value anywhere in the declared sensitivity
  range — including at 100x baseline and at the range ceiling. (A sensitivity
  of 100x scales INPUT deltas; the seam ceiling and steer bound are untouchable.)
- F4 ROUND-TRIP DRIFT: save -> load -> settings differ from the saved
  settings (bindings, sensitivity exactly, invert), or save -> load -> save
  is not byte-identical, or the save is not atomic (no temp+rename in the
  destination directory), or a load ever writes/creates a file.
- F5 COLLIDING BINDINGS: a duplicate physical-key inside the JSON `bindings`
  object accepted silently (JSON last-wins) instead of a NAMED conflict;
  an unknown action name accepted; a settings file that leaves one of the
  four selected controls (`forward`, `backward`, `turn_left`, `turn_right`)
  with NO binding accepted silently (U04's own words: bindings needed for
  the selected controls must WORK). Alias bindings (two physicals, one
  action — U01's `W`/`Up` shape) remain LEGAL. Sprint/jump bindings remain
  legal and refuse BY NAME at runtime (U01's registered refusals).
- F6 BROKEN FIRST RUN: absent file refuses instead of returning defaults;
  defaults differ from U01's baseline (`DEFAULT_BINDINGS`,
  `SENS_RAD_PER_COUNT`, no inversion); load creates a file; after one
  explicit save the same path loads back as "loaded" with identical settings.

**STOP RULE**: the test module green, all six falsifiers measured, receipt
saved. No tuning loop: if a falsifier fires, the MODULE is fixed against the
frozen contract below; the contract's numbers are never adjusted to pass.

## THE FROZEN SETTINGS MODEL

Three surfaces, exactly U01's declared data inputs (`input_mapper.py:174-182`:
`bindings=` and `sensitivity=` constructor parameters; nothing else):

1. **BINDINGS** — physical input name -> action, the mapper's own table shape
   (`DEFAULT_BINDINGS`, `input_mapper.py:99-106`). Legal actions:
   `ACTIONS = ("forward", "backward", "turn_left", "turn_right")` plus the
   registered-refusal actions `("sprint", "jump")` — a settings file may bind
   a key to a refusal action; at runtime it refuses BY NAME (U01's
   `REFUSALS`), never silently. Aliases legal. Coverage rule: each of the
   four selected controls keeps at least one binding (falsifier F5).
2. **SENSITIVITY** — per axis over `AXES = ("yaw",)`. The keyboard/mouse
   baseline has exactly ONE continuous input axis (mouse X deltas); movement
   is a binary demand at the frozen band ceiling (`V_MAX_IN_BAND_M_S`), so
   there is NO movement sensitivity to expose — a declared limit, not a
   missing feature. Units: rad/s of yaw demand per mouse count per 50 ms
   interval — U01's own conversion (`_yaw_demand`,
   `counts * sensitivity / INTERVAL_S`). Range: `(0.0, SENS_YAW_MAX]` with
   `SENS_YAW_MAX = OMEGA_MAX_RAD_S * INTERVAL_MS / 1000 = 1.6 * 0.05 =
   0.08` rad/count — DERIVED, not tuned: the value at which ONE count in ONE
   interval exactly saturates the declared steer bound; above it the scale is
   degenerate (every count saturates). Default = U01's frozen baseline
   `SENS_RAD_PER_COUNT = 0.002` (imported, never redeclared). Floor: zero is
   refused (a dead axis is a broken setting, refused by name); "how slow is
   unusable" is human feel — U07's actual-play field under P06, not invented
   here (declared limit). Sensitivity scales INPUT deltas only; the mapper's
   own clamp (`max(-OMEGA, min(OMEGA, ...))`) is the bound — reused, never
   bypassed.
3. **INVERSION** — per axis over the same `AXES`; booleans. `invert.yaw =
   true` negates the yaw DELTA scale (the applied mapper sensitivity becomes
   `-sensitivity`), per U01's integration note ("inversion = a negative
   sensitivity for the yaw axis"). It does NOT swap `turn_left`/`turn_right`
   key bindings — a key swap is a REMAP (an ordinary data edit of the
   bindings table, already measured values-only by U01's F5), not an
   inversion of the continuous axis. Declared limit, stated in the module
   docstring and handoff notes.

## THE FROZEN PERSISTENCE CONTRACT

- **Schema id**: `chimera.monkey_input.v1` — U01's integration-note
  suggestion, F01's `chimera.<thing>.v<N>` naming. One string field. Unknown
  or missing schema id (INCLUDING a hypothetical `chimera.monkey_input.v2`)
  = named refusal + defaults; there is no migration path today (R02 owns
  migration when an actual supported prior save requires it).
- **Document shape** (exact key set; extra or missing keys refuse by name):
  ```json
  {"schema": "chimera.monkey_input.v1",
   "bindings": {"W": "forward", "...": "..."},
   "sensitivity": {"yaw": 0.002},
   "invert": {"yaw": false}}
  ```
- **Load-with-refusal**: invalid UTF-8/JSON text, non-object root, duplicate
  JSON keys anywhere (object_pairs_hook detection — Python's json otherwise
  silently last-wins), `NaN`/`Infinity`/`-Infinity` literals (parse_constant
  refusal — non-finite never parses), unknown/missing keys, wrong types
  (booleans are NOT numbers — `isinstance(True, int)` is refused explicitly),
  unknown actions/axes, empty binding names, out-of-coverage bindings,
  non-finite or out-of-range sensitivity, non-bool invert values: EVERY case
  returns (defaults, refusal list) where every refusal carries a distinct
  machine code + a human detail naming the offense. NEVER a silent accept,
  NEVER a partial accept. Load NEVER writes (first run creates nothing).
- **Defaults on first run**: absent file -> (defaults, status "first_run").
  Defaults = U01's exact baseline (deep copy of `DEFAULT_BINDINGS`,
  `SENS_RAD_PER_COUNT`, `invert.yaw = false`).
- **Atomic save**: canonical UTF-8 JSON (sorted keys, fixed separators),
  written to a temp file in the DESTINATION directory, flushed + fsync'd,
  then `os.replace` (atomic rename) onto the target; temp cleaned up on
  failure. The settings file today is a SETTINGS file — not the save-game
  system (X02/R02 own session flow and save lifecycle; handoff notes filed).
- **Declared default path** (constant only — nothing is written by import or
  by tests; tests inject temp paths):
  `tools/monkey_campaign/data/settings/monkey_input_settings.json`, created
  on first explicit save by a live caller.

## THE SEAM PROTECTION RULE (U01's note, made structural)

Settings values can NEVER write the seam's own numbers. Three layers:
(1) the schema has a FIXED key set — no key named after any seam constant
(`v_max_in_band_m_s`, `omega_max_rad_s`, `interval_ms`, `hold_ticks`,
`expiry_ticks`, `valid_ms`, `release_decay_ms`, `physics_hz`, ...) can parse;
it arrives as an unknown key and refuses by name; (2) the apply surface is
only `mapper.bindings = dict(...)` and `mapper.sensitivity = ±sensitivity` —
the mapper's own declared data inputs; no module attribute of
`input_mapper` or `command_record` is ever assigned; (3) the sensitivity
range ceiling is derived FROM the seam's numbers, so the setting exists only
inside the space the seam already bounds. The fuzz proof (F2) measures all
three: no adversarial vector moves a seam constant, and every emitted record
stays inside U01's bounds.

## THE INTEGRATION SURFACE (mapper stays READ-ONLY)

`input_settings.apply_settings(settings, mapper)` sets the mapper's
`bindings` (a fresh dict) and `sensitivity` (signed by the inversion flag) —
the exact parameters U01's constructor already declares. FINDING recorded
(handoff notes): the mapper ALREADY exposes both hooks — bindings-as-data
(ctor param + public attr, read per event at `input_mapper.py:193,208`) and
the delta-scale (public attr `sensitivity`, consumed at the boundary in
`_yaw_demand`, `input_mapper.py:325`) — so NO addition is needed from the
coordinator; the "delta-scaling hook" named in the brief is
`InputMapper.sensitivity` itself. `configured_mapper(sink, settings, ...)`
builds a settings-configured mapper in one call.

## OWNERSHIP (declared before implementation; nothing existing modified)

- `tools/monkey_campaign/product/input_settings.py` — the module (stdlib +
  sibling `input_mapper` import only; disjoint from `focus_policy*.py`,
  `session_flow*.py`, `input_mapper*.py`, `follow_camera*.py`).
- `tools/monkey_campaign/product/input_settings_tests.py` — the falsifier
  tests (house style: sibling `*_tests.py`, runnable as a script, prints
  per-falsifier receipts, exit 1 on any failure).
- `tools/monkey_campaign/agents/U04_settings/` — brief, this prereg,
  handoff notes, receipts/.
- U01's `input_mapper.py` is READ-ONLY here (brief constraint): consumed,
  never edited.

## WHAT WOULD MAKE THIS THEORY LOSE (honest limits, stated now)

- One axis today. If a later lane adds a continuous movement axis (analog
  support is an explicit product decision, unmade), v2 of the schema adds the
  axis by a NEW prereg — the loader refuses unknown axes precisely so v2 is
  an event, not a silent reinterpretation.
- The sensitivity floor is not derived: "how slow is unusable" is human feel
  and belongs to U07's actual-play measurement under P06's frozen limits. The
  loader refuses zero and non-finite; finer floor calibration is not
  invented here.
- Inversion is the continuous yaw axis only; key-swap inversion is a remap
  the player can already express in bindings. If playtesting (X07) shows
  players expect an invert-keys flag, that is a v2 schema addition with its
  own prereg.
- The settings file does NOT survive X02's session restart flow yet and does
  NOT join R01's save/restore contract yet — R02 consumes this store
  (handoff notes filed); nothing here pre-builds the save-game system.
