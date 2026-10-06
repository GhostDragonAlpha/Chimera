# PREREGISTRATION — ONT-U04 (input settings: sensitivity, inversion, bindings, persistence)

Card `ONT-U04` (planning id **U04**), attempt `caffa214d5c1429f87a145634f3dd373`,
arrival `arrival-784f5dbaf83343cd8bb1b925a2583364`, branch `branch-2` (isolated
sparse attempt checkout), criteria_sha256
`91ae72baefd10d8e670a4c715fa0fec8ef8bddd014fe5cb7b1a4bcfbbffd931b`.
Source pin: revision `9afbddcd90164b5544a16fd0bc72278d985eb6e3` of
`E:/ChimeraWork/monkey-play-20260924`, read via `git show <rev>:<path>` only —
zero checkouts, zero working-tree changes in any source repository. This file
is frozen BEFORE running the falsifier battery (Rule 0).

## Reconciliation (step 1 of the brief, done first)

- **The U04 implementation already exists at the pin.** Commit
  `4699b37d` ("monkey-play: U04 integrated — input settings …", on the
  monkey-play line that contains the pin `9afbddcd`) adds
  `tools/monkey_campaign/product/input_settings.py` (504 lines) +
  `input_settings_tests.py` (830 lines) with the integration receipt in
  `agents/U04_settings/`. The campaign base `astra/gait-capture` and this
  attempt's HEAD (`c525b82c`, 2026-09-24) predate that line, so the campaign
  branch contains **no** input-settings code at all (`tools/monkey_campaign/`
  at HEAD has no `product/` directory).
- **Prior ONT-U04 attempts left no artifacts.** Nine earlier attempt
  directories under `kanban-attempts/ONT-U04/` hold only checkout skeletons at
  HEAD `c525b82c` with zero commits; one (`bd24b16f…`) holds an untracked
  reference extraction whose four Python modules are byte-identical to this
  attempt's (same pin hashes); its two package `__init__` files are empty
  placeholders where this candidate carries the pin's exact bytes. None
  reached a submission. No completed implementation is being repeated; the
  missing step is **delivering the already-integrated pin implementation as a
  reviewable candidate on the campaign branch**.
- **Precedent followed:** merged PR #138 (`review/I-U07-TRACE`, merge
  `eaa2fa46`) delivered a pin-derived module the same way:
  `contributions/<TASK>/{PREREGISTRATION.md, <module>.py, test_<module>.py,
  proposed.patch, report.md, receipt.json, reference/ + EXTRACTION_LEDGER.json}`.
- **done_when clause mapping (pin):** sensitivity → per-axis yaw delta scale
  with a derived ceiling; inversion → sign of the yaw delta scale (never a key
  swap); bindings → physical-name → action table over U01's mapper grammar;
  persist → versioned `chimera.monkey_input.v1` JSON, atomic save, total
  refusing load. Every clause is owned by the pinned module.

## STATEMENT (a theory someone could disagree with)

Input settings for the keyboard/mouse baseline can be exposed entirely as DATA
over U01's frozen seam: a settings vector (bindings table + per-axis yaw
sensitivity + per-axis inversion) that (a) round-trips through a versioned
JSON file byte-deterministically and atomically, (b) is applied to the mapper
through the mapper's own declared data inputs only (`bindings=`,
`sensitivity=`) and never writes any seam constant, and (c) loads TOTALLY:
every possible file resolves to either the declared settings or U01's exact
defaults plus a named refusal — never a partial accept, never a silent
default, never a write from load. The sensitivity range is DERIVED, not tuned:
`(0, OMEGA_MAX_RAD_S * INTERVAL_MS/1000]`, the value at which one mouse count
in one 50 ms interval exactly saturates the declared steer bound, so no
settings value can exist outside the space the seam already bounds.

## PREDICTION

The pinned falsifier battery
(`input_settings_tests.py`, seed 20260924, F1–F6, 24 named checks) passes
unchanged against the extracted reference tree: every adversarial file refuses
BY NAME with the EXACT defaults as fallback (F1); no settings vector —
including a 100x baseline and a 2000-payload fuzz — moves any emitted
CommandRecord past the seam's own bounds (F2); save→load is exact and
byte-identical on resave, the write is atomic, load never writes (F3);
emitted yaw equals `clamp(counts*s/interval, ±OMEGA)` exactly across the sweep
(F4); binding collisions/unknowns/unbound controls are named, aliases stay
legal, remaps are values-only (F5); an absent file is `first_run` with U01's
exact defaults and creates nothing (F6).

## FALSIFIERS (frozen; the battery is the pinned file, byte-exact)

- **F1 SILENT ACCEPT** — every adversarial settings file (36-case corpus:
  corrupt JSON, duplicate keys anywhere, NaN/Infinity literals, unknown
  schema, missing/unknown keys, wrong types incl. booleans-as-numbers,
  unknown axes, out-of-range values, unknown actions, unbound selected
  controls) refuses BY NAME and falls back to the EXACT defaults; one
  multi-offense file reports EVERY offense; the corpus exercises every
  declared refusal code.
- **F2 SEAM POISON** — 171 named poison payloads (seam-constant key names ×
  poisoned values) plus a 2000-payload random fuzz leave all 18 seam
  constants bit-identical and every emitted record inside U01's bounds;
  `apply_settings` copies the bindings table; even a direct extreme vector
  cannot push an emitted record past the seam.
- **F3 ROUND-TRIP** — first run creates nothing; save→load reproduces
  settings exactly; save→load→save is byte-identical (canonical form); the
  write is same-directory temp + `os.replace` with no residue; a stale
  interrupted-write temp is ignored; bit-flipped real files refuse BY NAME.
- **F4 SENSITIVITY** — `yaw == clamp(counts*s/interval, ±OMEGA)` EXACTLY for
  every (sensitivity, inversion, counts) triple in the frozen sweep; doubling
  s doubles the unclamped yaw; 100x baseline + 100k-count flick lands exactly
  AT the seam bound, never beyond; 100x is UNREACHABLE through a settings
  file; `invert.yaw` negates mouse-driven yaw only and does not swap keys.
- **F5 BINDINGS** — duplicate binding keys refuse by name; aliases stay legal
  and both drive; sprint/jump stay bindable and refuse by name at runtime; a
  remap changes emitted VALUES only (same record type/version/adapter
  projection); remap-created collisions resolve by U01's precedence and are
  named in the trace; unbound selected controls and unknown actions refuse at
  the file boundary.
- **F6 FIRST RUN** — absent file → `first_run` defaults identical to U01's
  baseline; defaults drive a plain U01 mapper record-for-record; after one
  explicit save the same path loads as `loaded`; the declared default path is
  never created by import or tests.

Falsification = any FAIL line in the battery, any hash drift between the
candidate and `reference/` copies of the pinned modules, or any test run
longer than 120 s / larger than 16 MiB of new output.

## VISUAL/NONVISUAL SCOPE (declared, not skipped)

The verification profile `controls` is kind=motion. This candidate is the
settings DATA LAYER ONLY: it binds and scales inputs into U01's existing
mapper and persists them; it starts no window, no engine, no GPU process and
renders nothing. Motion/runtime/visual qualification of the CONTROLS (stuck
commands, camera obstruction, focus loss) remains owned by the parent runtime
tasks and the live campaign's runtime phase; those gates are NOT claimed here
and this candidate cannot close them. Headless, CPU-only: no clock, no
window, no engine import, no desktop input, no network.

## SCOPE / LIMITS (from the assigned brief)

Code and artifacts ONLY inside `tools/monkey_campaign/contributions/ONT-U04/`
in this attempt checkout. No production checkout changes, no package
installation, no GUI, no native build, no GPU, no training, no process
control, no unbounded fuzzing (the battery is bounded: 2000-payload fuzz,
seed frozen). Reference extractions are byte-exact and read-only after
extraction; every extracted identity is in `EXTRACTION_LEDGER.json`. The
proposed integration patch is a PROPOSAL for the lead/publisher only; it does
not claim integration.
