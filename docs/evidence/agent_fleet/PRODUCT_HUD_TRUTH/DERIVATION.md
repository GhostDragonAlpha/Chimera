# product-hud-truth-01 — DERIVATION (before any code)

Task: product-hud-truth-01 · base cb874a3a · worker subagent-worker-02
Defect source: PR #97 blind dyad judge findings 4(b)/4(d), verbatim in the task packet.

## 1. The data path, traced at base cb874a3a

### The joint readout (judge finding 4(b))

```
POST /joint {"joint":name,"theta":deg}          main.cpp:1105-1145
  -> request_joint_edit(idx, deg)               engine.cpp:5519-5528
       joints_owner_ = 1                        (edit claims the pose)
       edit_joint_ = idx, edit_theta_deg_ = deg, edit_pending_ = true
  -> render thread, pose dispatch               engine.cpp:7709-7751
       edit_mode = (joints_owner_ == 1)         engine.cpp:7709
       st[idx*8+7] = clamp(deg, ROM) * pi/180   engine.cpp:7749   <- THE state buffer
       (the JNT kernel FK-poses the mesh from this same buffer, binding 7)
  -> the UI's per-frame view of that buffer     engine.cpp:7435-7445
       joints_view[k].theta = st[k*8+7]*180/pi  engine.cpp:7442   <- LIVE values
       ui_.set_joints_view(view, owner, selected)
  -> the glass joint row                        ui.cpp:2535-2553 (build_chrome)
       if (owner_ui == 1 && sel_ui >= 0)  -> "EDIT <sel> theta ..."   (2026-09-04 fix)
       else                               -> "SHOW <clk_name_> theta <clk_theta_>..."
```

THE GAP: `POST /joint` with `theta` claims ownership (owner=1) but never sets
`selected_joint_` (only the separate `"select"` key does, main.cpp:1120-1125).
The product demo path — a script driving joints — therefore always falls to the
`SHOW` branch, which prints the SHOW sweep's cycling state:

- `clk_name_ = show_joint_name((t/per) % nj)`       engine.cpp:7383-7388
- `clk_theta_ = st[cur*8+7]` for that SAME sweep cur engine.cpp:5495-5501

With the sweep not posing (joints_on_ defaults 0, engine.hpp:407) every non-driven
lane of st holds 0.0, so the row reads a cycling name over a 0.00 theta — exactly
the judge's "(b) the banner always reads theta 0.00 deg and names a joint different
from the one moving". Retained before-frame g020 (PR #97): row says
"SHOW knee_L theta 0.00 deg" while the rig overlay on the SAME image says
"shoulder_R +36" and "elbow_R +75" — the live values were on screen the whole time;
the row just never followed them.

### The clock plane (judge finding 4(d))

```
Engine::frame()                                  engine.cpp:7376-7398
  ui_.set_show_clock(t, nj*per, ...)             engine.cpp:7386  (28 x 4 s = 112 s)
Engine::frame_idle_ui()                          engine.cpp:8501-8519
  ui_.set_show_clock(t, nj*per, ...)             engine.cpp:8508  (same expression)
  -> timeline readout                            ui.cpp:1939-1952
       "t = %.3f s / %.1f s (lap %ld) | <sweep joint> theta = %+.2f deg | PLAYING"
```

The push is unconditional in the pose owner: while a script holds the pose, the
readout still presents the sweep's 112 s lap. Measured on the retained before-run
(reel wall-clock captions in before-frame g020): the PR #97 capture pipeline cost
~2.7-3.0 s of real time per captured frame (two full-resolution PNG encodes per
iteration dominate; the engine renders at ~33 fps), so the honest sweep clock
advanced ~36 s per 12-frame keyframe gap while the movie spec declared a 4.5 s
10 fps clip — the judge's "(d) timing is inconsistent ... not a real-time capture".

## 2. The fix law (generalizing the 2026-09-04 EDIT-row precedent)

The 2026-09-04 fix made the row follow the operator's EDIT selection. The
generalization: **when the pose is edit-held, the readouts follow the joints the
edit path actually drove.**

Which joints did the edit path drive? This is DERIVABLE from state the UI already
receives every frame, with no new engine authority:

- While `owner == 1` the sweep never writes thetas (engine.cpp:7722-7751: the edit
  branch is exclusive of the show branch), so ANY theta change in the pushed view
  comes from the edit/script/stride paths — all of them programmatic pose drivers.
- Therefore: a joint whose pushed theta differs from its previous-frame theta while
  `owner == 1` IS a driven joint. A per-joint bit set (uint32_t, nj = 28 < 32),
  accumulated in `set_joints_view` (ui.hpp — the same function that already receives
  the live view), cleared on owner 0->1 transitions (new claim episode) and on
  owner 0 (show reclaimed, engine.cpp:692 / main.cpp:1724 are the only owner-0
  writers).
- False positives: impossible (the sweep cannot run while owner==1). False
  negatives: only a re-drive to the identical theta, which was already set as a bit
  at the first change. The set is exact.

The clock plane: the deliverable allows "reflects the active interaction timeline
or is explicitly labeled as the sweep clock". The derived choice is the first arm,
through machinery the product ALREADY has: the show clock is the engine's one time
parameter and `POST /show {"time":T}` (main.cpp:1730-1734, "the timeline's HTTP
twin") scrubs it WITHOUT touching pose ownership (only `"playing":true` hands the
pose back, main.cpp:1724). A scripted demo that declares a frame interval drives
that declared timeline through the product's own endpoint; the readout then shows
the interaction's clock, origin at the pose claim (`clk_t_ - t0`, t0 recorded at
the owner 0->1 transition — time stays engine-owned; the UI only differences the
pushed clock). The sweep lap never appears beside edit-held motion, and the
timeline footer labels the sweep paused.

Why the readout edit branch lives in the UI, not at engine.cpp:7386/8508: the UI
already holds owner, the live thetas, and the derived driven set at the one
formatting site (ui.cpp:1925-1952, 2535-2553 — "Every string drawn here is ALSO
the string the HTTP twin serves", main.cpp:1987-2011 serves hud_rows_ verbatim).
Pushing a parallel "edit clock" from the engine would need new Engine members
(engine.hpp is outside this task's write scope) and would duplicate the selection
law at two push sites. The engine's set_show_clock keeps pushing the sweep clock
(it remains a live parameter for when the show resumes); the DISPLAY law chooses
the plane by pose owner.

The reel caption carries the same defect class (the judge sees it in the glass):
`reel_note_grab` names the sweep's cycling joint + its theta (engine.cpp:7140-7151,
"t59.13 hip_R +0.0d" in before-frame g020). It reads the UI's derived driven set
through a const getter (same render thread — no race) and names the first driven
joint (+count) with its live st+7 theta while the pose is edit-held.

## 3. The equations close

- Row truth: displayed theta = `joints_[k].theta` = `st[k*8+7] * 180/pi` — the exact
  buffer the kernel consumed this frame. Commanded deg -> f32 rad -> f32 deg
  round-trip error ~1e-5 relative (75 deg -> <0.001 deg); display quantization
  %.2f = 0.005 deg. Bound: |displayed - commanded| <= 0.05 deg (>=10x margin).
- Clock truth: probe pins the clock with `POST /show {"playing":false}` once
  (owner untouched), then `POST /show {"time": i*0.1}` per frame; with the clock
  paused the scrub is the ONLY writer, so displayed age at keyframe i is
  (i - i_claim) * 0.1 s exactly, ± one render-frame sampling (measured 33 fps
  -> 0.03 s; bound 0.10 s). Keyframe gaps in the driven regime (8, 5, 10, 9
  frames) -> 0.8 / 0.5 / 1.0 / 0.9 s ± 0.10 s.
- Peaks: 0.6 x flex(shoulder_R=60) = 36.0 deg, 0.6 x flex(elbow_R=125) = 75.0 deg
  (recorded in PR #97's render_records: commanded 36.0 / 75.0 at hold) — the
  packet's "36/75 deg" is the exact scripted value, inside ROM, clamp inactive.

## 4. Scope accounting

In scope: ChimeraEngine/engine/ui.cpp, ui.hpp, engine.cpp, and this evidence dir.
- ui.hpp: driven-set members + set_joints_view derivation + const getter.
- ui.cpp: the three formatting sites (HUD row 2542, timeline readout 1944, footer 2114).
- engine.cpp: reel_note_grab caption law (7140-7151). set_show_clock sites unchanged.
- main.cpp / engine.hpp: NOT touched (out of scope; the design needs nothing there).
