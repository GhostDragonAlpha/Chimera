# Workshop challenge 2 — the saved recipe transfers; the world changes; one edit recovers

**Date:** 2026-10-18
**Driver:** `tools/construction_packet/workshop_challenge2.py` (imports the
published challenge-1 driver; run:
`python tools/construction_packet/workshop_challenge2.py run --out DIR --port N`;
`... compare RUN1 RUN2 --out comparison.json`)
**Runtime:** B-suite construction engine
`.tmp/body-engine/Release/chimera_engine.exe`,
sha256 `47bbf42a7437089264a9f830f832f7432dfc2deb48680330ce4478134b278406`
(both engines in each run; recorded per phase in the receipts).
**Runs:** `run1/` (ports 8820/8821), `run2/` (ports 8822/8823),
`comparison.json`.
**Gate:** §5.1 workshop "inventions can be reused"; §13.1 "exercise the
resulting action in the native scene".

## Player benefit

Challenge 1 showed the player can build and save a solution. This increment
shows the save is worth something: **the player's saved invention loads into
a brand-new world and still works**, and when the world changes under it,
the game **names what broke and how to fix it**, and one small edit recovers
the structure. That is the workshop promise — invent once, reuse, adapt.

## The arc (both runs, identical verdicts)

1. **Build** (engine #1): contact tower — granite pillar on the marked hazard
   slab, crate centred. Predicate PASS: clearance **79.882 mm**, total
   reaction **115.03 N**; the chain-law prediction hit to the micron
   (predicted 79.882 mm). `/tick_b2_save` → `save_B.json`.
2. **TRANSFER**: engine #1 shut down cleanly by handle; engine #2 boots a
   **fresh world with no build step and a never-admitted scene**;
   `/tick_b2_restore` of the save document. Restored hash **equals** engine
   #1's saved hash (bit-exact cross-session). Settle → predicate PASS,
   clearance 79.882 mm, reaction 115.03 N. Board verdict (green WS4 chip,
   `4-transfer-glass.png`): "TRANSFER VERDICT: the saved recipe works in a
   fresh world UNCHANGED — crate 79.9 mm above the hazard. The invention is
   REUSABLE."
3. **CONSTRAINT VARIATION**: `/tick_b2_patch crate mass_kg` 1.9625 → 3.9250
   (the player doubles the load). Quasi-static prediction said 72.046 mm;
   the actual settled margin was **−8.92 mm — FAIL**: the doubled step load
   punches the crate through the pillar onto the hazard (the documented
   over-compression/tunnel class; deterministic — −8.92 mm in both runs).
   Board verdict (red WS4 chip, `5-variation-glass.png`): "LOST SUPPORT: the
   doubled load punched the crate down through its support onto the hazard
   (clearance -9 mm). ACTION: add the second pillar beside the first and
   reload the crate across both."
4. **RECOVERY EDIT** (the ACTION line, one player-scale edit): remove the
   wrecked tower, let the pad spring back, place the **second pillar beside
   the first** (unrotated, x 0.555/0.685), re-place the crate straddling
   both tops at the post-patch pair equilibrium, apply the doubled mass
   while paused (no step load). Predicate PASS: clearance **79.051 mm**
   (predicted 76.544). Board verdict (green, `6-recovered-glass.png`):
   "RECOVERED: the doubled load now rides TWO pillars — crate 79 mm above
   the hazard (was -9 mm, through the tower). The recipe was reused, the
   world changed, one edit recovered it."
5. **Persistence probes**: terminal save → restore **bit-exact**; refused
   edit (`patch` unknown part) leaves the hash unchanged.

`gate_challenge2` (both runs): build/transfer/recovery passed,
restored-hash match, variation measured (expected FAIL — the gate measures
the named margin loss, it does not require a pass there), restore bit-exact,
refusals preserved. `gate_pass: true`.

## Determinism (two independent runs, honestly scoped)

- Analytic anchors: **byte-identical modulo the step counter**; all states
  within band; settled save docs within band (0 violations).
- Frame shots: 3/5 byte-identical; the 2 differing shots
  (`6-recovered-terminal`, `7-terminal-restored`) are settled-physics frames
  inside the documented jitter band.
- Glass shots: **not** byte-identical between runs (unlike challenge 1).
  Measured: 417–901 differing px per shot (0.02–0.04 % of 1920×1080). The
  Studio board region — including every verdict line — is byte-identical;
  the diffs sit in the 3D viewport (settled-jitter specular edges) and the
  live STATUS HUD (FPS/t clock readouts). The falsifier text is rendered
  "named before the run" on the board itself.

## Measured cost

- Frame time (32 samples): mean of per-run averages 1.191 / 1.173 ms;
  single-frame max 47.6 / 37.1 ms (first frame).
- Clock: sim/wall 1.0, 0 catch-up clamps, max gap 3.95 ms.
- Memory: RSS peak **138.0 MB** (two sequential engines, one at a time).
- 14 routes, all inside the frozen B2 surface.

## Engine/API findings (new, beyond the arc)

1. `/tick_b2_patch` accepts `mass_kg` and rescales mass, inertia **and**
   ground-rung k/c by the same ratio (rest sink preserved by engine law) —
   load patches are legal world edits, which is what made the variation a
   real edit rather than a rebuild.
2. Cross-session restore works on a fresh **never-admitted** engine
   (`B2Scene::restore` sets `active_ = true`) — no admit step needed.
3. **Rotated-surface contact finding (candidate engine bug)**: a ROTATED
   part acting as the *contact surface* drops vertex-resting loads — the
   crate free-fell (exact ½gt², zero pair force) through a 90°-yawed support
   at 2.4 mm and 6.7 mm penetration, while the geometrically identical
   unrotated support held at both depths (yawed square-pillar control
   included). Probes preserved in `probes/` (run from the repo root; they
   import the challenge drivers). Suspected rotated-face-owner bug in
   `pp_pair_`. **Challenge 1 evidence is unaffected**: its support surfaces
   (pier tops, deck) were unrotated. Workshop rule adopted now: *supports
   are placed unrotated*; whether this becomes an engine ticket is a lead
   decision for the engine track (the B-suite exe is a build artifact; the
   membrane-pinned exe is frozen).

## Preregistration disclosure (deviation, same as challenge 1)

Design (law, falsifier, predicate thresholds, expected variation FAIL) was
frozen in the committed driver before the capture runs, and the falsifier is
rendered on the board as "named before the run" — but there is no separate
UTC-stamped preregistration JSON. Disclosed deviation from the membrane-loop
pattern.

## Process record

Maya authored the 710-line driver and one smoke run in a single dispatch
(~2.4 h) under the revised brief (author + smoke only, no capture, no
commit); the lead ran the two capture runs and the comparison directly. The
process change after challenge 1's two timeouts worked as intended.

## Verdict

§5.1's reuse promise is now demonstrated end-to-end in the native scene:
saved invention → fresh world → works unchanged → world varies → named
failure with ACTION → one edit recovers → save/restore still bit-exact.
**Not shown:** human playability (scripted walkthrough), and the
rotated-surface defect is documented, not fixed.
