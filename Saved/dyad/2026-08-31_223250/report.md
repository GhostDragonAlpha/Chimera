# dyad scan — 2026-08-31_223250

- started: 2026-08-31T22:32:56
- reads per shot: 1 (NOT a vote — all reported)
- crop: none (whole window)
- engine: 2560x1440

## shot 00 — theta 0.00
`fps 94.5177 · ft avg 7.60637 ms · stage: B7 ARTICULATE`

**read 0** (496.1s)

**Overall read:** It looks like a working tool, not a broken one — the 3D viewport is live (humanoid + perspective grid), status/timeline/reel are all populated. But as a *composition* it's top‑heavy and the hero subject is framed badly, so the first thing that loses me is the model itself.

**The framing defect (biggest issue).** The body is cropped at the waist: no head, most of the torso gone, just hips→feet plus two dangling forearms. Meanwhile there's a large dead black zone *below* the feet down to the REEL strip. So the subject sits top‑weighted in the viewport with empty space where its head should be and void where its shadow/ground should be. The camera is zoomed/positioned wrong — it doesn't fit the model, and there's no ground plane contact (the grid starts mid‑shin). To an artist this reads as a clipped capture or a render that hasn't auto‑framed, not an intentional shot. Fix: frame to bounding box, put feet on the grid horizon, fill vertical space.

**Balance / proportion.**
- Both side panels are top‑anchored text blocks with tall empty bottoms; they don't read as bounded panels — the background shade difference from the viewport is too subtle, so they look like floating text rather than windows. Give them a visible edge or fill the height (scroll region, pinned footer).
- The REEL and TIMELINE strips sit low‑center but stop short of the right edge, leaving an asymmetric right margin that doesn't match the left — the bottom third feels lopsided.
- Net effect: top 40% is busy, bottom 30% is mostly black with two narrow strips adrift in it.

**Legibility / text defects.**
- No hard collisions or clipped words; the real problem is *low‑contrast dim gray* on near‑black (the explanatory lines under the workspace list, the timeline ruler ticks, the "r12.0 0.00/0.30" sub‑labels). At 2560×1440 it's readable but tiring; bump secondary text contrast ~2 stops.
- Left panel wraps awkwardly ("the JOIN of engine state + repo truth" → 3 lines; "workspaces (A3 - click to switch):" → 2). Either widen the column or shorten strings so they don't break mid‑phrase.
- The REEL's four thumbnails are **identical** with identical labels (`t9.39 spine_upp +117.6d 22:33 r12.0 0.00/0.30` ×4). That looks like a placeholder/bug, not data — it undercuts the "live" claim and is the second thing that reads as broken.
- The center bottom `36 fps 25.13 ms` followed by a row of dashes looks like an unfinished progress bar; either complete it or remove the dashes.

**Confusing / unclear.**
- Acronym soup with no legend: C1, C4, D3, D5, E1, F4, A3 appear inline without explanation; "EARLIEST NON‑GREEN GATE" and "+ cam" are opaque to anyone but you. The relationship between the gate tabs (top), the workspace list (left), and REEL/TIMELINE (bottom) isn't visually grouped — three separate systems competing for attention with no hierarchy cue.
- The rainbow of gate colors (green/blue/olive/purple) is functional but noisy at the very top where your eye lands first; consider muting inactive gates so B7's blue pops more cleanly.

**Quick fix list, in priority order:** 1) auto‑frame the model and ground it on the grid; 2) make side panels visually bounded (border or filled height); 3) raise contrast of secondary text and timeline ticks; 4) de‑duplicate or label the REEL frames so they don't look like a bug; 5) span the bottom strips full‑width to kill the right margin asymmetry.

It's not ugly — it's coherent and clearly functional — but the cropped hero shot plus top‑heavy, half‑empty panels make it read as "tool in development" rather than "polished application." The framing of the 3D subject is the single change that would most improve how it looks.
