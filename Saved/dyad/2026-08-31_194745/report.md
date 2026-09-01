# dyad scan — 2026-08-31_194745

- started: 2026-08-31T19:47:46
- reads per shot: 1 (NOT a vote — all reported)
- crop: none (whole window)
- engine: 2560x1440

## shot 00 — theta 0.00
`fps 10.813266 · ft avg 84.058647 ms · stage: B7 ARTICULATE`

**read 0** (103.5s)

Overall read: it looks like a working tool, not a broken one — but as a composition it's top‑heavy and center‑empty, and the thing that should be the hero (the 3D viewport) is the weakest element on screen. The chrome (title bar, gate strip, side columns, bottom status) all read fine; the middle does not earn its space.

Concrete defects:

- **Text/button collision at top center.** The camera button row `[1 alpha] [2 beta] [3 closeup] + cam` sits in the same horizontal band as the left panel's first line `the JOIN of engine state + repo truth`. The end of that gray line runs right into / under the `[1 alpha]` box. Either drop the help text, move the buttons down a row, or give the left column a hard right edge so they can't overlap.
- **No separation between panels and viewport.** The STUDIO (left) and STATUS (right) blocks are just text on the same near‑black background as the 3D scene — no panel fill, border, or shadow. You cannot tell where UI ends and 3D begins; the grid/void seems to continue behind them. Give each column a distinct surface (even a 1px edge or a slightly different bg) so they read as panels, not floating text.
- **The viewport is empty and unbalanced.** It's a perspective floor grid plus two tiny axis lines and one caption (`no mesh loaded`). The upper ~half of the view is pure black with no horizon glow, skybox, or fog to sell depth, and there's a large dead band between that caption (mid‑height) and the REEL strip near the bottom. Content clusters at the top; the lower center is void. For an engine studio the viewport should be the focal point — right now the eye has nowhere to land except the faint grid. Even empty, add a horizon line/glow, a visible origin gizmo of normal size (the green/red axis marks are minuscule), and maybe a subtle vignette so it reads as "scene with nothing in it" rather than "render failed."
- **Low‑contrast text.** The gray lines — `GAIT/WATER/FROST - parked`, the help block, `(docs/THE_ENGINE_STUDIO.md)` — are dim on near‑black and will be hard to read at arm's length. Bump their luminance or use a distinct muted color with more separation from the bg.
- **Inconsistent button styling.** `+ cam` is plain text while `[1 alpha]` etc. are boxed; it looks like an orphan rather than a control. Box it or style it deliberately as a label.
- **Gate‑strip logic vs. message.** The strip shows three non‑green gates (B7 blue, B8 olive, B10 purple) but the line below only says `EARLIEST NON-GREEN GATE: B7`. That's technically correct ("earliest") but visually under‑explains why B8/B10 are colored differently; a reader will wonder if those are errors.
- **Bottom meter is cryptic.** The green segmented bar with red tick marks has no label or scale; the red ticks look like error flags out of context. Add a unit/label (frame budget? ms?) so it's legible at a glance.

Proportions of the side columns (~16–17% each) are sensible for 2560×1440; that part is fine. The real problem is framing: three horizontal chrome bands plus two text columns leave a rectangular hole in the middle that should be the star but is empty and dark. Fix the panel/viewport boundary, populate or dress the viewport (horizon + proper gizmo), and resolve the top‑center overlap, and it'll read as a confident working app instead of a sparse one.

One caveat: I'm inferring the `[1 alpha]` / `repo truth` overlap from pixel positions in the screenshot; if your actual layout has them on separate rows at runtime, ignore that bullet — but verify, because at this resolution they appear to share a line.
