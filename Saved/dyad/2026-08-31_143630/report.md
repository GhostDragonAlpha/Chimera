# dyad scan — 2026-08-31_143630

- started: 2026-08-31T14:36:30
- reads per shot: 1 (NOT a vote — all reported)
- crop: none (whole window)
- engine: 2560x1440

## shot 00 — theta 0.00
`fps 10.705202 · ft avg 84.435471 ms · stage: B7 ARTICULATE`

**read 0** (308.0s)

Overall read: the window is dominated by a black hole. The center viewport takes up roughly two‑thirds of the width and most of the height, and it contains *nothing* — no grid, no origin/axis gizmo, no skybox, no model, no "empty scene" placeholder. Your own status panel says `mesh: see viewport | splats: 0`, so you know it's empty, but the surface gives zero visual cue that it's a live render target versus a dead window. To an artist this is the first thing that breaks the image: the eye has nowhere to land in the middle, and the composition reads as "render failed" rather than "working app with no asset loaded." That single defect outweighs everything else on the screen.

Specific defects:

- **Viewport emptiness / no feedback.** A 3D viewport that's pure black at full res looks broken. Even an empty scene should show a ground grid, a tri‑axis gizmo in a corner, or a centered "no mesh loaded" hint. Right now it's indistinguishable from a crashed GL context. This is the biggest fix you can make.

- **Dead vertical space in both side panels.** The left STUDIO list ends around 1/3 down and the right STATUS block ends even higher; below that, both columns are empty dark fill all the way to the bottom of their region. The panels are far taller than their content needs, so you have two tall voids flanking one giant central void. Either shrink the panels to fit content, or move content (e.g., put the REEL/TIMELINE blocks into a side column) so the lower half isn't empty.

- **Text is too small for 2560×1440.** You're rendering terminal‑density monospace at full monitor resolution. The top instruction line, the workspace list, and especially the right‑hand status lines are sub‑legible at arm's length on a 1440p display. Nothing is cut off or overlapping that I can see, but the *size* is the problem: most body text is one step too small to be comfortable, and the bracketed camera buttons `[1 alpha] [2 beta] [3 closeup] + cam` are nearly invisible against the black.

- **Camera presets look adrift.** Those four bracketed labels float at the top‑left of the viewport with no toolbar background, no label, and no visual grouping. They read as stray text rather than controls. Give them a container or a small "CAM" caption so they register as buttons.

- **Bottom bands are cramped and inconsistent.** REEL (D3) and TIMELINE (D1) are squeezed into thin horizontal strips at the very bottom of the center column. The REEL section is mostly empty black with one orange line — too tall for its content. The timeline crams `PAUSE -1f +1f 1x`, `t = 37.002 s / 0.0 s`, `? theta = +0.00 deg | PLAYING` into a single tight row of small elements; it's the densest, least‑breathing part of the UI and the buttons are tiny.

- **Low‑contrast panel separation.** The left/center/right division relies on faint background‑shade differences with no clear borders or gutters. At a glance the structure is soft; you have to look for the edges. Consistent 1px separators or uniform gutters would make the three columns read as distinct regions immediately.

- **Stage‑button color legend isn't obvious.** B0–B6 are all identical green, so the "earliest non‑green gate" idea is carried by color alone with no on‑screen key. Only B7/B8/B10 stand out. A viewer can't tell what green vs. blue vs. olive means without reading the prose line above them.

- **Contradictory "live" signals.** The bottom bar shows `7 fps 138.74 ms` and the timeline says `PLAYING` with a timecode, yet nothing is visible in the viewport. That combination makes it look like something *should* be rendering but isn't — which reinforces the "broken" impression rather than the "working" one.

On framing/balance: content clusters in the top ~35% and bottom ~15%, leaving a dead band across the middle third of the height. The vertical rhythm is broken. If I were reframing it, I'd (a) fill or clearly label the viewport so it stops reading as empty, (b) tighten the side panels to their content height or redistribute the REEL/TIMELINE into them, and (c) bump the base font size up one notch for 1440p. The terminal aesthetic is coherent and intentional — that's fine — but right now it costs you legibility and makes an empty scene look like a failure state.

Does it read as a working application? Marginally. The live FPS counter, `PLAYING` flag, and status panel say "it's running," but the empty viewport and 7 fps undercut that hard. Fix the viewport feedback first; everything else is secondary to that.
