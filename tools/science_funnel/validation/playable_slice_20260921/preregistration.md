# PREREGISTRATION — THE PLAYABLE SLICE (agent/playable-slice-20260921)

Banked at master 1391014f, BEFORE any slice code was written. Astra round-3
directive: start a small playable slice against the frozen engine interface now;
mock behavior clearly identified and outside physics evidence.

## RULE 0 — THE MEMBRANE

**STATEMENT.** A human can double-click one launcher and reach a live vertical
slice — the committed standing-pose macaque in the shared world through the
engine's TRIANGLE render path, one objective (carry the creature to the marker
and release it), honest physics outcomes from the engine's own movement law,
failure feedback, and a byte-clean restart — with every mocked behavior NAMED
in the UI and in the code (a mock registry, grep-audited), and every real
behavior (rendering, gravity, floor contact, the release transient) performed
by the real engine with no splat route reachable.

**PREDICTION (not yet measured).**
- P1 LAUNCH: from a clean machine state (no slice or engine processes of this
  lane alive), double-click launch reaches a rendered first frame in the
  browser in under 10 s, with zero console errors.
- P2 FALL/RELEASE: arming the engine's movement law on the freshly imported
  standing macaque produces the engine's own derived root transient — NOT an
  animation. DERIVED BRANCH (before the run, from banked engine constants):
  the importer centers Y, so the authored rest's lowest vertex sits at
  -h/2 (penetrating); the root law (membrane_tick.cpp: root_vy += (F/m - g)*dt,
  F = min(50mg, k*depth + c*max(0,-vy)), k = 1.3562e7 N/m, c = 6.062e5 N s/m,
  m = 13824.5 kg, g = 9.81 m/s^2, floor y=0) therefore starts with F > 0 and
  produces the RISE branch; with zeta = 0.7 the settle overshoot is
  exp(-pi*zeta/sqrt(1-zeta^2)) ~= 4.6% of the h/2 - 1 cm amplitude, which does
  NOT lift the lowest vertex above the floor — so NO F=0 free-fall window
  exists for a centered import on this lineage. The measurable law is the ODE
  itself: the checker integrates the banked constants and the measured
  root_y(t) curve must match it (an eased tween would not).
- P3 MOCK TRUTH: the set of MOCK[...] marker tokens in the slice's code equals
  the mock registry's id set exactly (grep-auditable, both directions), and the
  UI shows a registry-named banner for each active mock.
- P4 RESTART: a restart re-boots the scene from the same sha-pinned import
  bytes; the standing start is byte-identical across two independent restarts
  (same scene sha, same start-state sha over the engine's /verts + /tick_state).
- P5 NO SPLAT: the slice's render path touches /mesh_import + /verts +
  /topology + /camera only; no splat route (layer_splat_buffer, /membrane_bin,
  splat.wgsl) is reachable from any slice file (grep-audited).

**FALSIFIERS (named before the run).**
- F-SLICE-LAUNCH: first frame >= 10 s, or any console error, or a launcher
  step that fails silently = FAIL, recorded with the measured time and the
  console transcript.
- F-SLICE-FALL: the measured root transient deviates from the banked-constant
  ODE beyond the named tolerance (RMSE > 3 mm on root_y, or the identified
  equilibrium sink outside 1.000 cm +/- 10%), or the derived branch
  prediction (rise, no F=0 window) is wrong and the curve matches nothing =
  FAIL, recorded. THE STRUCTURAL FINDING IS PRE-REGISTERED: a true
  drop-from-height free fall needs an authored-above-floor rest, which the
  centered importer cannot author; if a free-fall window nonetheless appears,
  the derivation was wrong — record it and fit g directly.
- F-SLICE-MOCK-TRUTH: any mock site without a registry entry, any registry
  entry without a code site, or an active mock without its UI banner = FAIL.
- F-SLICE-RESTART: scene sha or start-state sha differs across restarts = FAIL.
- F-SLICE-NO-SPLAT: any splat route reachable from slice code = FAIL.

## HONESTY LAW (load-bearing)

Two categories only: REALITY (engine rendering, engine gravity, engine floor
contact, engine release transient, engine camera) and FANTASY (the carry mock
that slides the creature toward the marker — pending real locomotion, physics
target 426 = the wave-38 walk's refusal at 302; receipt
gait_zero_20260919/receipt_wave38.json). Every FANTASY behavior is named by
its registry id in the UI while active and at its code site. The mock registry
is the contract; the audit script is its enforcer.

## WHAT THE SLICE IS NOT

It is not a physics claim: the locomotion is not real and is not shown as real.
It is not the gait harness: the walk machine (wave-38, refusal 302, target 426)
is a separate lineage; the slice names it as the pending real component.
