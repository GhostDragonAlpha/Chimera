# E2 SEAM SOFTMAX — agent H4 "seam-softmax", fleet (2026-09-13)

Route 2 of the E2 seam fix: bounded-falloff softmax travel weights
(`tools/vertbind_softmax.py`, new script; `tools/classify_run.py` untouched).
**VERDICT: the law is REFUTED by its prereg'd falsifier. The lead should NOT
post this payload to the LIVE world.** The numbers below are real measurements
(offline metric = W8's method, engine A/B on a private scratch engine), and
the failure localizes the residual crease more tightly than before — that is
the payload of this run.

## RULE 0 ledger

- Prereg (this run): the residual crease (180 knee45 edges after W8) is
  carried by the IDW^2 weight LAW near the 3rd/4th in-limb ordering boundary;
  a Gaussian softmax whose 4th candidate pin carries <1% bounds the mass a
  set-flip can move across one ring, so knee-region >10 deg introduced crease
  edges drop >50% vs W8 on both poses, with no tear signature.
  **LOST** — crease edges ROSE 30.6% (knee45) / 20.3% (compound); the
  stiffness the derivation forces concentrates the shear into harder,
  narrower bands and introduces 6-7 inverted-winding faces per pose.

## The lambda derivation (RULE 1 — derived, not swept)

Requirement (mission): the 4th-nearest candidate pin of every vertex carries
<1% of the softmax mass. With w4 = exp(-(d4/λ)²)/Z and Z >= exp(-(d1/λ)²),
the sufficient bound is (d4² - d1²)/λ² >= ln(100) = 4.60517, i.e.
λ <= sqrt((d4² - d1²)/4.60517) per vertex. Measured over monkey_full.bin
(18459 verts, W8 in-limb candidate sets):

- worst vertex 15530 (belly, spine_lower region; four candidate pins within
  12.7% of each other, d4/d1 = 1.127): min(d4² - d1²) = 0.057035
- λ_max = sqrt(0.057035/4.60517) = **0.11129 m**
- s = mean nearest-pin distance = 0.62992 m → **c = λ/s = 0.17667**

Post-hoc verification with the exact normalized softmax: max w4 = 0.766%
(< 1%), shipped top-3 truncation mass <= 0.766%, fill 5880 verts (cap hit 0),
float32 weight-sum error 4.3e-8, deg-0 rest return 3.1e-7 (W8-class bounds,
all PASS).

Note honestly recorded: requiring the bound at the WORST vertex forces a very
stiff law (c = 0.177; a pin 2λ away carries e^-4 = 1.8% before normalization).
A knee-region-only worst vertex would allow λ = 0.2155; the mission's
requirement is per-vertex universal, so the mesh-wide bound was shipped. No
sweep was run — the refutation below is for THE derived λ, exactly as RULE 1
demands.

## Numbers (E2 knee-region metric, >10 deg introduced vertex-normal delta)

| binding            | knee45 creases (max deg) | hip20+knee45 creases (max deg) | pose-introduced inverted-winding faces |
|--------------------|--------------------------|--------------------------------|----------------------------------------|
| pre-W8 (reference) | 193 (161.9)              | 237 (161.4)                    | 8 / 14                                 |
| W8 (shipped OLD)   | 180 (165.7)              | 212 (164.6)                    | 2 / 2                                  |
| SOFTMAX (NEW)      | **235 (168.6)**          | **255 (168.3)**                | **14 / 21**                            |

Drop vs W8: **-30.6% (knee45), -20.3% (compound)** — negative, i.e. WORSE.
Falsifier bar was >50% drop with zero tear signature. Both prongs failed.

Pin SETS are identical between W8 and softmax (flip-band 4117 → 4117 verts;
duplicate-position split bindings 0 → 0) — only the weight profile changed.
That isolates the mechanism cleanly: the residual crease is NOT carried by
truncation-edge flip mass (bounding the 4th pin to <1% changed nothing about
which sets flip), it is carried by the weight MAGNITUDE profile near
pivot-dominance boundaries. λ = 0.111 makes the binding harder than the
shipped 1/(d²)² law: a thigh vertex that under W8 moved ~75/25 between hip
and knee now moves ~100/0, so each dominance boundary becomes a narrow,
full-contrast shear line — more edges past 10 deg, higher max delta, and 6-7
faces whose winding actually inverts under pose (a real tear signature).

## Engine A/B (scratch engine 127.0.0.1:8137, isolated cwd, live world 8107 untouched)

Both payloads load (`/tick_vertbind` ok) and pose identically well: verified
against the offline prediction before each frame — knee-region displacement
old pred 0.2606 / obs 0.2606; new pred 0.2614 / obs 0.2614; rest return ~0.
Captures (identical camera derived from the knee pin, hip_L 20 + knee_L 45):

- `knee45_old.png` / `knee45_old_crop.png` — W8 binding: smooth S-bend, the
  known crease band above the knee.
- `knee45_new.png` / `knee45_new_crop.png` — softmax: the same bend with a
  visibly HARDER angular kink mid-leg and a shading discontinuity on the
  shin fold — the metric's extra creases and inverted faces, visible.

Capture protocol note: the first AB attempt caught a stale frame (pose posted,
frame grabbed before the render thread caught up) and one later probe lost a
pose POST silently; the committed script now GATES every frame on /verts
matching the offline predicted displacement (2 mm tolerance) before capture,
so a stale or lost pose can never ship as evidence.

## Files

- `tools/vertbind_softmax.py` — the generator + metric + gated A/B (repo)
- `vertbind_softmax_payload.bin` — the exact /tick_vertbind body
  (4 + 18459*15 = 276889 bytes); loads ok, but DO NOT POST TO THE LIVE WORLD
- `metrics.json` — every number above, machine-readable
- `knee45_{old,new}.png` + `_crop.png` — the pose-test captures
- `tick_state_after.json`, `engine_8137_log.txt` — scratch engine state/log

## For the LEAD (routing)

**Do not apply.** The bounded-falloff softmax with the mission's own λ
derivation makes the seam worse, and the failure is informative: with pin
sets held identical, W8's weight profile beats the stiff Gaussian profile —
the residual 180 knee45 creases live in the weight MAGNITUDES near
pivot-dominance boundaries, not in set-flip mass. Any route 3 should either
SOFTEN the falloff relative to the shipped 1/(d²)² law (more mixing across
boundaries, e.g. a true IDW² on DISTANCE not squared distance, or a wider
kernel whose λ derivation targets blend-band WIDTH ~ multiple vertex rings
rather than 4th-pin mass) or attack the band by geometry (E2's original
observation that the 0.5-1.0 m shear band is where knee weight leaks into
idle regions suggests restricting knee_L's influence radius by the limb
skeleton, not by rank). The payload file here is evidence, not a shipment.
