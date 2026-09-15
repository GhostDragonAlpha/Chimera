# W2 DIMPLE-VISIBLE — the diagnosis and the fix

Agent: W2-dimple-visible · 2026-09-14 · slot-01 @ astra/tasks/matter-kernel-format-01
Files owned: `tools/game_shell/index.html` (the only file changed — zero engine edits)

## THE PRODUCT-CRITICAL DEFECT

Two blind judges and the H5 dry-run measured the same thing: pressing the creature in
the BROWSER shows no visible dent ("at no force, from no angle, did I ever SEE the skin
dent. The squish is entirely in the HUD numbers" — judge2; "skin smooth, pose identical
to rest" mid-hold at 4.893 MPa — H5 S5), while the engine reports dents up to 0.45 m.

## THE DIAGNOSIS (mechanism before fix — RULE 0)

Rig: scratch engine (port 8161, isolated cwd, snapshot copy of the live world, same
binary as live 8107 — verified: PID start 20 s after exe build) + scratch shell (8207)
+ headless Chromium driving the real page. Measured on 2026-09-14, live 8107 untouched
(GET only).

The prime-suspect chain, each measured:

**(a) "Does /verts carry the pressed positions at all?" — YES. REFUTED as the defect.**
- POST `/tick_touch {"hit":[0,4.444,0.700], "force_n":20000}` (the vertex-snapped belly
  point exactly as the page sends it) → GET `/verts`: the nearest hit vertex is
  displaced **0.3979 m — the law, exactly** (δ = F/(4πσ) = 20000/(4π·4000) = 0.3979 m).
  `dimple_m` state = 0.397887; P_upper 0 → 842 kPa. The dent is in the export.
- The engine does NOT apply the dent render-side in a shader; `MembraneTick::step()`
  writes the offsets into `verts9` (= `g_tick_verts`, the export source) each tick.

**(b) "Is the delta stream dropping it?" — NO. REFUTED.**
- The C3 kernel stream serves `0xD1` framing; keyframes carry the dent fully and runs
  carry the changed verts. A keyframe degradation (H14) cannot hide the dent — a
  keyframe IS the full mesh.

**(c) "Does the page's renderer upload it?" — YES. REFUTED.**
- Page checksum (`__h16pickProbe.sum1` over RG.verts) vs the same checksum of the
  shell's `/api/verts`: **diff 0.0000 at rest, during a held press, and after release**
  (one 0.0093 float-noise transient mid-decay). H16 parity holds UNDER PRESS.

**THE ACTUAL DEFECT — the kernel is sub-Nyquist on the display mesh.**
- The engine's kernel: δ = F/(4πσ) amplitude, **r0 = 3 cm** Gaussian falloff.
- The demo mesh near the belly: **vertex spacing ~3.7 cm** (measured nearest-neighbor).
- A 3 cm Gaussian on a 3.7 cm mesh = a 1-vertex spike. The dent — 0.398 m DEEP —
  renders as a **7 px wide × 27 px tall hairline slit** (103 canvas px changed,
  `crop_side.png`): technically present, unreadable as a dent. This is why "at no
  force, from no angle" — the answer is a knife-cut, not a dimple.
- **The engine's own /frame of the same press renders it as ONE pixel (max channel
  delta 3/255)** at its default camera (2560×1369, measured). The trailer's
  "0.045→0.4513 m growth" is `dimple_m` — a state number — not a default-camera pixel
  measurement. Both renderers had the same invisible answer.

## THE FIX (page-only; zero engine edits; no window #8 dependency)

The mandate's preferred shape — the press kernel client-side in the page's WebGL
vertex shader — applied as a **REPLACEMENT**, not an addition:

- **The law is the engine's own:** δ = F/(4πσ), σ = 4000 N/m (`sigma_n_`),
  Gaussian falloff, release decay exp(−t/τ), τ = 0.5 s (`tau_relax_`), 0.1 mm cutoff
  (deterministic rest). No new physics constants.
- **The regularization radius rides the amplitude (rad = δ):** a shape law, not a
  tuned size — cup depth equals cup radius (the shape of a dent; deeper-than-wide
  reads as a puncture, the pre-fix state). The response reads as a dimple at every
  force the slider can send and scales with the hand, which is the product.
- **REPLACE mode:** the shader displaces the **pre-press rest surface** (a rest
  snapshot mirrored from the stream while idle, frozen inside 3·rad during kernel
  life, its own VBO) by the law ONCE. Rationale measured the hard way: adding the
  page kernel on top of the streamed engine dent doubles the center displacement —
  at 50 kN, server 1 m + page 1 m = 2 m, and the cup floor pierced the body
  (`pay50k_side2.png` shows the healed render; the torn pre-fix version is in the
  transcript). Replace mode renders the law's amplitude exactly once — the same
  number the HUD reports.
- **The patch gate:** kernel weight gated by smoothstep(0, 0.5, dot(vertex normal,
  press-point normal)) — full weight within 60° of the press normal, zero past
  perpendicular. Measured without it: an ungated 0.4 m kernel pulled the far side of
  the hip and the thighs inward (a melted groin region).
- **Stream purity:** RG.verts stays a faithful mirror of /api/verts (the kernel lives
  only in the shader + the rest snapshot) — H16 bit-parity holds under press
  (measured), and `pickWorld` still raycasts the true streamed surface.

## THE FALSIFIER (stated before the run) — PASS

Bars derived from the camera geometry (px/m = 800/(2·tan(22.5°)·25.3 m) = 38.2 px/m at
the belly; 20 kN → δ = 0.398 m = 15.2 px projected depth): bbox width ≥ 15 px, ≥ 1000
changed px, blob shape (≥10 rows with ≥5 px), present by +0.7 s, monotone decay, gone
by +2.0 s. 20 kN belly press, held, default camera, headless:

| state | changed px | bbox | rows ≥5 px |
|---|---|---|---|
| pre-fix hold | 103 | 7×27 (a line) | — |
| **appear +0.5 s** | **1228** | **52×53** | **49** |
| **hold +1.5 s** | **1228** | **52×53** | **49** |
| decay +0.4 s | 289 | 18×27 | 26 |
| decay +1.0 s | 33 | 5×11 | 0 |
| **gone +2.0 s** | **0** | — | — |

Every bar passes. The page now exceeds the engine's own default-camera presentation
(1 px, delta 3) by three orders of magnitude. Screenshots: `f_rest/f_appear/f_hold/
f_decay1/f_decay2/f_gone.png`, `dent_zoom.png`, `triptych2.png`; the pre-fix slit:
`before/during2/crop_side.png`; the 50 kN payoff: `pay50k_side2.png`.
Numbers + probe sources: `falsifier_results.json`, `falsifier.py`, `focus_probe.py`,
`e2e_probe.py`, `slider_test.py`.

## THE SLIDER (judge 1's stall #3, measured by judge 1)

The page drew TWO slider-looking bars: the native track inside the input AND a separate
`#force-meter` div 9–20 px below the real hit box (measured at 1280×800: input rows
50–63 vs meter rows 77–82 in the card). Buyer drags aimed at the drawing that cannot
hit — 4/5 failed in the buyer session; the H7 D4 `pointer-events:none` patch only made
the impostor pass clicks through ("stray clicks fell through the panel").

**Fix:** the impostor div is GONE. The input's own track draws the fill, the gentle
threshold tick, and the thumb (`::-webkit-slider-runnable-track`, `::-moz-range-progress`)
— drawn position == hit box **by construction**. The note's tick is aligned to the
input's tick column in JS (re-aligned when the play screen becomes visible — the
boot-time measurement ran while hidden and landed the tick at 0 px; caught and fixed).

Verification (headless, `slider_test.py`): elementFromPoint at the drawn thumb →
`INPUT#force`; **buyer-grade drags 5/5 moved the value** (was 4/5 FAILING); click at
the tick column: 50000 → 8100 N (the gentle zone); arrow keys alive after the click;
tick pixel column 47 == the 15.15%-of-197 px target. `slider_fixed.png`.

## REGRESSION

Ten-lesson walk (`walk_lessons10.js`) against the scratch chain — see
`walk10_result.txt` in this directory. (Lessons 1–3 are the walk's first three.)

## NO ENGINE EDITS

None staged. The engine's law and export are correct; the defect was the kernel's
regularization radius being unrepresentable on the display mesh. If the fleet later
wants the ENGINE's own viewer to show the dent too, the right lever is
`press_r0_` (membrane_tick.hpp — a runtime member, default 0.03) sized from the
loaded mesh's vertex spacing at init — desk-checked here as a RECOMMENDATION ONLY,
staged nowhere, deliberately: it would shift every measured pressure gate downstream
and needs its own falsifier through the window.
