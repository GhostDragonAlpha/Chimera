# dyad scan — 2026-08-31_221104

- started: 2026-08-31T22:11:13
- reads per shot: 1 (NOT a vote — all reported)
- crop: none (whole window)
- engine: 2560x1440

## shot 00 — theta 0.00
`fps 10.38452 · ft avg 87.373436 ms · stage: B7 ARTICULATE`

**read 0** (483.1s)

Overall read: it's a monospace/terminal‑styled engine HUD over an empty perspective grid. It *works* as a debug surface, but as a composed window it reads top‑heavy and adrift — three clusters of text pinned to the top corners and center, a big dead black band across the upper viewport, and two thin control strips floating in the lower third with nothing anchoring them. The 3D view is visible (grid floor + green/red axis cross at horizon) but empty, so the window reads as an idle/empty state rather than a ready‑to‑work app.

Specific defects:

- **Text collision / truncation (the one hard bug).** In the left STUDIO panel, line 2 "the JOIN of engine state + repo truth" runs straight into the camera‑preset buttons `[1 alpha] [2 beta] [3 closeup]`. The word "truth" is clipped/overlapped by the left edge of `[1 alpha]`. That's a real layout collision, not just tight spacing.
- **Dead void in the upper viewport.** The horizon sits ~35–40% down, leaving a large pure‑black band between the top toolbar and the grid that does nothing. The composition is bottom‑weighted (grid) while all the UI weight is at the very top — off‑balance.
- **Floating, ungrouped panels.** Left STUDIO text, right STATUS text, and the center help lines have no background fill or borders; they're just glyphs over the render. The perspective grid lines pass *behind* the left help block (below the horizon), which makes that area busy and reads as debug text dumped on top of a frame rather than docked panels.
- **REEL and TIMELINE are adrift.** Two thin horizontal bars in the lower third with a large empty gap between them, not visually connected to each other or to the grid. They look pasted on, not docked. The REEL bar's "[0/12]" strip is mostly empty space.
- **Empty‑state framing weakens the "working app" read.** "no mesh loaded", "no grabs yet", "no joints pack" are honest, but with no object and a void above, the center feels abandoned rather than ready. The axis cross floating at an empty horizon doesn't help.
- **Minor legibility/consistency nits:** orange used for all three "empty/error" body lines is low‑contrast on near‑black; inconsistent caps ("JOIN", "volp‑ARAP"); the top gate tabs use green/blue/gold/purple with no legend, which is a bit noisy.

Framing fixes that would help most:
1. Fix the left‑panel overlap — give the preset buttons their own row or push the STUDIO text into a narrower column / add a panel background so nothing collides.
2. Give left/right/center info real panels (subtle fill + 1px border) and consistent gutters, so they read as UI, not overlay text.
3. Kill the top void: raise the horizon, or add a faint sky gradient/vignette/fog to the upper viewport so it's intentional space, not black.
4. Dock REEL + TIMELINE into one bottom timeline bar (or at least remove the gap) so they anchor to the window edge instead of floating mid‑viewport.

Legibility at 2560×1440 is otherwise fine — nothing else is cut off or unreadable; the collision above and the empty/adrift framing are the things that actually lose me.
