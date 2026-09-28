# MAT2-U03 — Focus loss and input release under a declared policy

Task: MAT2-U03 / planning id U03. Attempt `53bf60ba7dee454bac95cec63ba717cf`,
arrival `arrival-6da597476070494bbf757db3cb05d4f8`, criteria sha256
`03b278cbe376141d5e3659b6d9b211530e0f7fc9990376e33087da4a9c3e724c`, scope
`cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`,
base revision `c525b82c7c3ce0128565424764293a3c85811ab3`, isolated branch-2
checkout (sparse: this contribution path only).

## Reconciliation and reuse (step 1 — done before implementation)

- Dependency MAT2-U01 is DONE (PR #197, merged as `ebdfda61` into
  astra/gait-capture). Its PREREGISTRATION declares exact subject hashes; all
  three were re-derived from the committed `pinned_seam` bytes at that merge
  and MATCH: `input_mapper.py` `7a36a45e…` (the qualified subject),
  `command_record.py` `67711759…` (the CommandRecord v1 seam),
  `input_mapper_tests.py` `95f44e90…` (the frozen F1–F6 falsifier module);
  `follow_camera.py` `d61347f0…` is referenced only.
- The canonical top-level `tools/monkey_campaign/product/` paths do not exist
  at this base (the U01 merge lives on the astra lineage), so the exact bytes
  are vendored at `pinned_seam/` — U01's own pinned-seam precedent — and the
  tests re-verify the ACTUAL loaded module files against the pins (a wrong
  resolution fails loudly).
- The U01 interface is the floor, by its own declaration:
  `InputMapper.release_all` ("U03's focus-loss/disconnect hook") and the
  static `InputMapper.is_expired` aging floor (VALID_MS=100 ms,
  EXPIRY_TICKS=30 @ 300 Hz). This card redeclares NEITHER constant; it imports
  and wraps.
- Prior attempt `f633058890344cb4ada3561352506015` (parked PAUSED by the lead,
  owner arrival-545c7328…): verified read-only to contain only a bare sparse
  `.git` at the same base — no commits, no working tree, no artifacts. There
  was no prior U03 work to continue; the lead's inbox message confirms "No
  candidate or PR existed".

## Declared policy (frozen in PREREGISTRATION.md before implementation)

`u03_focus_release_policy.v1` (focus_policy.py), wrapping the U01 seam:

- KEY RELEASE → upstream floor unchanged: the demand ages through the U01
  decay tail and lands on exactly 0.0, then emission stops (inert resumes).
- FOCUS LOSS (alt-tab) / DISCONNECT → `clear_held_age_to_zero`: upstream
  `release_all` clears held keys; any live demand ages to exactly 0.0 through
  the same tail (the tail is never gated); then new demands are HELD while
  unfocused/disconnected — presses and mouse counts are refused BY NAME
  (`press_refused_while_gated:<name>`, `mouse_refused_while_gated`), never
  silently.
- RESUME (refocus/reconnect) → `fresh_grid_no_replay`: the gate lifts; the
  next press starts a fresh 50 ms grid; nothing from the gated window is
  replayed (there is nothing held to replay).
- NO STUCK MOVEMENT (consumer side) → `effective_demand()`: the only lawful
  consumer read on this floor — a held record older than the upstream aging
  floor (strict `>`, 30 ticks) is INERT, so movement cannot outlive 100 ms
  without a fresh record even if the producer never ticks again.

## Verification (step 4 — actual runs, from the attempt checkout root)

```
python -B tools/monkey_campaign/contributions/MAT2-U03/test_focus_policy.py
python -B tools/monkey_campaign/contributions/MAT2-U03/pinned_seam/tools/monkey_campaign/product/input_mapper_tests.py
python -B tools/monkey_campaign/contributions/MAT2-U03/emit_focus_trace.py
```

Observed results (all reproducible; rerun after the final commit):

- `test_focus_policy.py`: `Ran 11 tests in ~0.16s` → **OK**; embedded named
  checks: **PROBE SUMMARY: 52 named checks, 0 failed**.
  - P0: the vendored U01 falsifier module runs GREEN unchanged (subprocess,
    `VERDICT: GREEN`, exit 0) — the F1–F6 frozen numbers held on the exact
    bytes this card builds on.
  - P1: policy id and the five declared action names; wrappers missing any
    U01 member refused by name (`upstream_interface_missing:press/release_all/
    is_expired`); the ACTUAL loaded mapper file hashes to the pinned subject
    `7a36a45e…`, the loaded seam to `67711759…`, the vendored U01 tests to
    `95f44e90…`.
  - P2 (alt-tab mid-walk): 6 walk records at the band ceiling; focus loss at
    1257 ms clears the held set; the next boundaries emit exactly the two
    tail records (v0*(1−43/100), then EXACTLY 0.0) and emission stops; a
    forced gated press is refused by name and emits nothing; refocus at 1700
    resumes with exactly one record on the fresh grid and no replay.
  - P3 (disconnect on the live-zero path): the S held zero-advance demand is
    cleared; no tail from a zero demand; no records afterwards; the event is
    named in the trace.
  - P4 (key release): monotone decay, sample v0*(1−30/100) then EXACTLY 0.0,
    landing by release+100 ms on the probe's grid; wrapper-transparent (4
    sink records total).
  - P5 (consumer floor with NO producer ticks): effective demand commanded at
    age exactly 30 ticks, INERT from age 31 (the upstream strict `>`), named
    `demand_inert/expired_record`; no-record reads are inert too.
  - P6: resume/disconnect/reconnect with nothing held are named no-ops.
  - F1 (stuck command, bitten live): a forced press while gated is refused
    (`press_refused_while_gated:W`); no nonzero demand exists past
    trigger+100 ms; held stays empty.
  - H1 (hazard baseline, recorded honestly): the RAW mapper without the
    policy keeps issuing nonzero records at every boundary for as long as a
    key is held — exactly the hazard the policy removes, demonstrated on the
    same vendored bytes.
  - F2 (unbound timing): decay at elapsed == 100 ms is EXACTLY 0.0; the aging
    boundary is strict at 30 vs 31 ticks; every policy event binds its
    injected now_ms.
  - F3 (nothing silent): focus loss, press refusal, mouse refusal and resume
    each leave a named trace entry; no untraced transitions.
- `input_mapper_tests.py` (standalone rerun of the U01 regression):
  `VERDICT: GREEN -- all falsifier checks passed; the frozen numbers held.`
- `emit_focus_trace.py` → `policy_traces.json` (byte-identical on
  regeneration, sha256 `4bf40725…`): the frozen qualification scenario as a
  per-tick table (30 rows, 17 sink records) — the profile's
  "input/state/tick display" diagnostic layer as numerical evidence — with
  policy gate state, held set, and consumer effective demand, plus three
  episode-scoped no-stuck-movement invariants evaluated on the trace itself:
  focus loss 1257 → nonzero demand last at 1300 (cease by 1357); disconnect
  1815 → last nonzero 1900 (cease by 1915); key release 2080 → last nonzero
  2150 (cease by 2180). Gated press refused by name; no replay after resume.

## Observed behavior note (recorded, not smoothed)

The upstream grid is boundary-anchored (next due = last boundary + 50 ms), so
with offset ticks the EXACT-ZERO landing record can land later than
release+100 ms wall-clock (observed: release 1815 → zero record at 1950,
i.e. the second boundary). The upstream deadline clause is boundary-based
(its own F4 runs dense ticks). What remains true under drift — and what this
card asserts — is the stuck-movement bound: the last NONZERO record after a
release is the first boundary sample (never past release+100 ms, since a gap
≥ 100 ms yields exactly 0.0 immediately), and the consumer aging floor makes
the demand inert within 100 ms even with no producer ticks at all. Both bounds
are asserted exactly (P5, F1, F2, trace invariants).

## Failures encountered (preserved, not erased)

1. `test_focus_policy.py` first draft called module-level `M.is_expired`
   (AttributeError): `is_expired` is a staticmethod of the upstream
   `InputMapper` CLASS. Fixed in the test (instance access); the policy code
   was already correct.
2. `emit_focus_trace.py` first draft dispatched script events only inside
   tick rows, so events between boundaries (the forced gated press at 1460
   and the DISCONNECT at 1815) never fired — the trace invariants failed
   (`no_stuck_movement=False`, `gated_press_refused_by_name=False`). Fixed
   with a merged timeline: events fire at their exact injected ms; the 20 Hz
   boundary runs only at declared tick times.
3. The no-stuck-movement invariant needed two corrections, both preserved:
   the first draft scanned ALL later rows (a later trigger's lawful decay
   falsely failed earlier triggers); the second scanned past the deadline but
   charged LATER EPISODES' lawful post-resume demands (fresh presses at 1710
   are new commands, not stuck movement) to earlier triggers. Final form:
   per demand episode — no nonzero effective demand after trigger+100 ms
   until the next lawful press.

## Honest boundary (runtime & visual)

The `controls` verification profile is kind=motion with camera-required
fields, views and clean-view requirements. **No runtime or visual claim is
made**: this attempt checkout is sparse (the contribution path only), the
base carries no integrated game loop that consumes the seam, and real alt-tab
would manipulate operator desktop focus, which the card's observation
("Keep operator desktop focus and processes untouched") forbids. Alt-tab,
disconnect and key release are INJECTED policy events on an injected
integer-ms clock. The visual/camera clause and a real-runtime exercise of the
policy are recorded PENDING_RUNTIME for the runtime lane (the venue that
produced U01's real capture), inventoried explicitly here rather than
claimed — `policy_traces.json.display_honesty` records the same boundary.
No GPU, training, network, engine process or desktop automation was started;
writes were confined to this attempt checkout.

## Artifacts (sha256 recorded in qualification_receipt.json and the
--request-pr handoff)

- PREREGISTRATION.md (frozen before implementation)
- focus_policy.py
- test_focus_policy.py
- emit_focus_trace.py
- policy_traces.json (generated, byte-reproducible)
- pinned_seam/tools/monkey_campaign/product/input_mapper.py (vendored, pinned)
- pinned_seam/tools/science_funnel/typeb_export/command_record.py (vendored, pinned)
- pinned_seam/tools/monkey_campaign/product/input_mapper_tests.py (vendored, pinned)
- report.md (this file)
