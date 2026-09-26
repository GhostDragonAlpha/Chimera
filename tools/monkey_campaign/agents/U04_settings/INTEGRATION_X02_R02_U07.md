# U04 integration notes — for X02, R02, U07 (and the coordinator)

Module: `tools/monkey_campaign/product/input_settings.py`
(+ `input_settings_tests.py`).
Prereg: `agents/U04_settings/PREREGISTRATION.md` (frozen before
implementation, base `b4de4de8`). Receipt:
`agents/U04_settings/receipts/input_settings_tests_20260924.txt`
(VERDICT: GREEN, 33/33 checks, exit 0). U01's `input_mapper.py` was NOT
modified (his suite re-run after my build: still GREEN).

## The contract in one paragraph

`input_settings.py` owns the whole U04 settings surface: a versioned JSON
file, schema id **`chimera.monkey_input.v1`** (F01's `chimera.<thing>.v<N>`
naming), carrying exactly four keys — `schema`, `bindings` (physical name ->
action, U01's table shape), `sensitivity` (per-axis; today the single axis
`"yaw"`), `invert` (per-axis booleans). `load_settings(path)` is TOTAL: it
returns `(settings, status, refusals)` where status is `"loaded"`,
`"first_run"` (absent file: U01's exact defaults, nothing created), or
`"refused"` (defaults + a list of `Refusal(code, detail)` naming EVERY
offense) — never a partial accept, never a silent default, never a write.
`save_settings(settings, path)` writes canonical bytes atomically (same-dir
temp -> flush + fsync -> `os.replace`, temp cleaned on failure).
`apply_settings(settings, mapper)` / `configured_mapper(sink, settings)`
feed a live `InputMapper` through its own declared data inputs only.

## FINDING for the coordinator: no mapper addition is needed

The brief asked for "a declared delta-scaling hook — if the mapper lacks the
hook, record the finding + the smallest needed addition". The mapper does NOT
lack the hook: U01 already exposes both integration points as constructor
parameters and public attributes —

- `InputMapper(sink, bindings={...})` — bindings-as-data, read per event
  (`input_mapper.py:193,208`);
- `InputMapper(sink, sensitivity=...)` — the delta scale, consumed at every
  boundary in `_yaw_demand` (`counts * sensitivity / INTERVAL_S`,
  `input_mapper.py:325`).

`apply_settings` sets exactly those two attributes and nothing else. U01's
F5 already proved such data edits change emitted VALUES only. **Zero
amendments to `input_mapper.py` are requested.** Inversion is implemented as
U01's own suggestion: the applied sensitivity is signed
(`-sensitivity` when `invert.yaw`), so the mapper's clamp
(`max(-OMEGA, min(OMEGA, ...))`) stays the single bound.

## The seam-protection rule, as built (three structural layers)

1. The schema's key set is FIXED: a file carrying
   `"v_max_in_band_m_s"`, `"omega_max_rad_s"`, `"interval_ms"`,
   `"hold_ticks"`, ... arrives as `key_unknown` and refuses by name
   (F2a fuzzed all 19 seam-constant names x 9 poisoned values: 171/171
   refused or inert, 18 seam constants bit-identical).
2. `apply_settings` can only write `mapper.bindings` and
   `mapper.sensitivity` — it assigns NO module attribute of
   `input_mapper` or `command_record`; bindings are handed over as a COPY
   (F2d: mutating the mapper's dict never writes `DEFAULT_BINDINGS`).
3. The sensitivity ceiling is DERIVED from the seam's numbers:
   `SENS_YAW_MAX_RAD_PER_COUNT = OMEGA_MAX_RAD_S * INTERVAL_MS / 1000 =
   0.08` — one mouse count in one 50 ms interval exactly saturating the
   declared steer bound. 100x baseline (0.2) is UNREACHABLE through a file
   (`value_out_of_range`, F4d) and even the direct-vector probe cannot push
   an emitted record past the seam's bounds (F2e).

## Notes for R02 — player settings and save lifecycle (your row builds on this)

- The file IS your settings persistence floor. `chimera.monkey_input.v1` is
  deliberately rigid: unknown schema (INCLUDING `v2`), unknown keys, and
  missing keys all refuse — so when you add fields, that is a NEW schema
  version (`chimera.monkey_input.v2`) with its own prereg, and the v1
  refusal is your migration trigger, not a silent reinterpretation. The map's
  R02 note ("schema migration only when an actual supported prior save
  requires it") is honored by construction.
- Atomic write is done (temp+fsync+`os.replace`, no residue — F3d); the
  interrupted-write cases measured here: a stale temp from a dead process is
  ignored by load (F3e) and a corrupted real file refuses + defaults (F3f,
  flipped at head/middle/tail). NOT done here (yours): user-facing
  save-selection UI, backup/rotate, multi-slot settings, and wiring the
  settings load into session start.
- `DEFAULT_SETTINGS_PATH = tools/monkey_campaign/data/settings/
  monkey_input_settings.json` is declared but nothing creates it except an
  explicit `save_settings` call (F6e: import and the whole test run leave it
  absent). The tests never touch the declared path — they inject temp dirs.
- `Refusal.code` values are a stable machine vocabulary (19 codes exercised
  in F1d) — reuse them for user-facing messaging (S04's "recoverable
  errors are understandable") instead of parsing `detail` strings.

## Notes for X02 — session flow

- Settings load is side-effect-free and fast (one file read + pure
  validation): call it whenever your flow needs current settings; on refusal,
  defaults are already in hand and the refusal list is displayable. Do NOT
  retry-with-deletion on refusal — a refused file is evidence (the campaign
  never deletes; the operator may want to read it).
- Restart/pause do not need to persist anything: settings live in the FILE,
  mapper state does not. On restart, re-run
  `load_settings` + `apply_settings` (or rebuild via
  `configured_mapper`) — U01's `release_all` hook remains the
  focus-loss floor (U03's), unaffected by settings.
- Save on change, not on exit, if you want interruption safety: each save is
  atomic, so a crash mid-session never corrupts the file.

## Notes for U07 — measuring controls during play

- Sensitivity is the per-axis delta scale in rad/s of yaw demand per mouse
  count per 50 ms interval. When reporting feel-vs-measured-latency
  separately (C12), pin the sensitivity vector that produced the trace —
  it is part of the input configuration, and the ceiling (0.08) plus default
  (0.002) bound the space you need to sweep. The FLOOR is deliberately not
  derived: "how slow is unusable" is your actual-play measurement under
  P06's frozen limits — the prereg assigns it to you, it was not guessed here.

## Declared limits (honest scope of "supported")

- ONE axis (`yaw`, mouse X). Movement sensitivity does not exist: the walk
  demand is binary at the seam's frozen band ceiling. An analog movement
  axis is controller territory — an explicit product decision, unmade —
  and would be a v2 schema event.
- `invert.yaw` negates the continuous mouse axis only; swapping A/D keys is
  a REMAP the player expresses in `bindings` (values-only, F5d) — not an
  inversion flag. If X07 playtesting shows players expect invert-keys, that
  is v2 with its own prereg.
- Controller/gamepad: NOT built (the map's explicit product decision).
  U01's integration note already sketches the `analog(fwd, yaw, now_ms)`
  entry point a future decision would need; nothing here pre-builds it.

## Disjointness (the coordinator's file-ownership law)

U04 wrote ONLY: `product/input_settings.py`, `product/input_settings_tests.py`,
and `agents/U04_settings/*` (brief, prereg, notes, receipts). U01's
`input_mapper*.py`, U03's `focus_policy*.py`, X02's `session_flow*.py`, and
U02's `follow_camera*.py` were read (mapper) or not touched; `git status`
paste is in the receipt report. No existing tracked file was modified.
