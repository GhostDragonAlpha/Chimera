# B9 — Material–geometry–solver qualification envelope (implementation evidence)

Date: 2026-10-12. Scope: `B9_envelope_scope.md` (accepted direction from the
plan owner). Battery: `tools/construction_packet/test_b9_envelope.py`
(port 8797, own engine). Result: **7/7 green, six consecutive stable runs**;
full B0–B9 regression **84 passed** (77 prior + 7 B9), 135 s.

## What the engine gained (b2_scene.cpp / .hpp)

1. **Declared bands** (constants block, each calibrated on a measured B8
   failure): rest sink ≥ `B9_SINK_MIN_M = 10 mm` (2.5 mm exploded at 81 m/s);
   sliding parts ≥ `B9_SLIDE_MIN_H_M = 50 mm` tall (20 mm exploded at
   91 m/s); tipping band — a declared sustained lateral load F at COM height
   H must satisfy `F·H/(m·g) ≤ B − sink − 2 mm`, where B is the **smaller**
   base half-extent (tipping rolls over the edge the load points at) and the
   10 mm foundation sink is subtracted from the usable base.
2. **Named refusals before mutation.** Admission, place and restore all run
   the same `parse_part_` validation; a refused part names the violated band
   with its numbers ("lateral load 2 N at COM height 55 mm needs 11.8 mm of
   normal shift across a 10 mm base half-width on a 10 mm-sinking foundation
   (B9 tipping band: base half-width must exceed 23.8 mm)"). The live world
   is untouched: the refused `place` leaves the state hash byte-identical
   (asserted with the clock paused — the save document includes the step
   counter, which is itself the format-vs-physics lesson).
3. **The optional `envelope` block** (`max_lateral_load_n`,
   `max_approach_speed_m_s`, `role: stand|slide|impinge`) travels with the
   part: it is echoed in the save document and revalidated on restore, so
   the envelope law is live after reload, not a saved comment.
4. **Visible runtime response after admission** (criterion 5 — transaction
   checks alone cannot cover a load or velocity that evolves past the band):
   the substep watchdog records named events — `max_approach_speed_m_s`
   (COM speed past the declared band), `backstop_stop_m` (declared stop
   crossed), `stand_tilt_rad` (stand-role part tilted past 10°) — exposed as
   `out_of_envelope_events` (cumulative counter),
   `out_of_envelope_last` (part, limit, measured, declared) and
   `out_of_envelope_limits` (per-limit counts). The watchdog **never mutates
   physics**; events are telemetry, outside the save document, hash-neutral.

## Acceptance criteria → tests (scope doc §3)

| Criterion | Test |
|---|---|
| 1 named refusals before mutation | `test_sink_band_named_refusal`, `test_tipping_band_boundary`, `test_slide_band_boundary` |
| 2 unchanged state after rejection | hash assertions in each refusal test (paused clock) |
| 3 boundary cases | `test_tipping_band_boundary`: 35 mm base refuses / 40 mm admits, with the band rule re-derived independently in Python from the authored geometry |
| 4 known-failure reproductions | the three refusal tests admit the exact B8 failure tuples (2 N on the 20 mm wall; 4× stiff ground; 20 mm slider); dynamic exits covered by the runtime trio |
| 5 visible runtime response | `test_runtime_speed_event`, `test_runtime_stop_event`, `test_runtime_tilt_event` (per-limit count deltas) |
| envelope survives save/restore | `test_envelope_roundtrip` (echo in save, hash-equal restore, refusal law still live) |

## What the battery caught in the engine (honest findings)

- **Sink site-count bug:** the first implementation computed the rest sink
  as `m·g/k_site`, but `k_site` is per-SITE (the rung law divides the total
  by the number of ground sites) — the engine reported a 40 mm sink for a
  10 mm part. Fixed to `m·g/(n_base·k_site)`; the battery's boundary pair
  only agrees with the engine after the fix.
- **COM convention bug:** the tipping check added `R·com_local` to `p.c`,
  double-counting the COM offset (`world_vert_` already subtracts
  `com_local`). Fixed to use `p.c` directly (the world-COM convention).
- **Test-side races (two rounds):** the event baseline must be read BEFORE
  the admit (the speed exit happens within milliseconds of the admission
  response), and hash-equality checks need the clock paused (the save
  document includes the step counter). Both were test bugs, found by
  instrumented failure messages, not engine bugs.

## Calibration anchors (all measured, B8 gallery evidence)

- 2 N at COM on the 20 mm-base, 110 mm wall: required shift 11.8 mm vs
  usable −2 mm → refused (the measured topple).
- 40 mm base, same wall family: shift 5.9 mm vs usable 8 mm → admitted;
  the runtime tilt event then fires when a 15 N load (shift 44 mm) tips it.
- 4× stiff ground (2.5 mm sink): refused at admission — the scene that
  exploded at 81 m/s can no longer be authored.
- 20 mm slider: refused; the 50 mm squat family admits (the B7/B8 qualified
  family).

## Boundary of what B9 declares

The bands are qualified-region declarations: geometries between the largest
measured failure and the smallest measured pass are **unqualified**, not
silently allowed (the 2 mm margin is the declared boundary tolerance). The
full tuple vision from the scope doc (mass-ratio and stiffness-ratio bands,
per-material published bands in `/tick_b2_state`, UI pre-warnings) remains
future work; B9 declares and enforces the three bands the B8 measurements
calibrated, plus the runtime event channel any further band will use.
