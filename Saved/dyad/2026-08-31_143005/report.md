# dyad scan — 2026-08-31_143005

- started: 2026-08-31T14:30:05
- reads per shot: 2 (NOT a vote — all reported)
- crop: [2230, 92, 330, 900]
- engine: 2560x1440

## shot 00 — theta 0.00
`fps 9.841835 · ft avg 92.529999 ms · stage: EARLIEST NON-GREEN GATE: B7 articulate -- the next stage  [next]`

**read 0** (57.3s)

No genuine glyph collision. At the pixel level every character sits in its own monospace cell with uniform tracking; on the three lines you flagged ("water clock: off | macro steps 0", "volp-ARAP: no pack | mode volp", "frost decode: off | frames 0") I see no characters overlapping, touching, or merging — the density is just a small bitmap/terminal font rendered tightly, not a layout defect. The vertical bars `|` and the digits all have clear gaps on both sides.

Clipping: none of the flagged lines is cut at the panel edge; they end well inside the right margin with their final `0` fully formed. The only line that runs to the boundary is the green "FPS 7 | ft avg 135.25 ms | max 1270" — its last digit sits very close to the right edge and would be the first thing to clip if the panel narrowed, but in this crop it appears intact, not truncated.

So: small and tightly spaced, yes; real overlap or cut-off glyphs, no.

**read 1** (61.3s)

No genuine glyph collision. On every line the characters use a uniform monospace advance width with consistent inter‑glyph gaps; nothing overlaps, touches, or crowds at the line ends. The lines you flagged ("water clock: off | macro steps 0", "volp-ARAP: no pack | mode volp", "frost decode: off | frames 0") all end with a normal space before the final character and clear margin to the right border — they are simply small, not colliding.

The one real defect is clipping, not collision: the green line `FPS 7 | ft avg 135.25 ms | max 1270` runs into the panel's right edge with no trailing space and its value is truncated at the border (the last digit sits flush against / past the edge). Every other line ends well short of the right margin, so only that green FPS line is cut off.

So: small and tightly set, yes; overlapping glyphs, no; clipped line, yes — just the green FPS line.
