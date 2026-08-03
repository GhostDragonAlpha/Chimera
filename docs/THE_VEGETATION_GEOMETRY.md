# THE VEGETATION GEOMETRY — a grass blade is a line, not three dots

> Membrane stated 2026-08-04, before the build. Opened by the rung-3 blind read
> (`docs/THE_SLICE.md`): "the tuft was never in frame" — and by the 2026-08-04 probe
> (`ChimeraEngine/output/tuft_before.jpg`, `tools/stone_legibility.py before tuft`,
> the blind read's own rig: 3.2 m third-person camera, −0.55 down-look), which
> measured the tuft as a faint smudge *after* its albedo had already been moved to
> the palette's green end. The physics membrane for the tuft is already proven
> (`ChimeraEngine/touchables.py`: the damped aggregate spring, E from Kosmalla 2025,
> recovery < 2 s). What is unproven is whether anyone can SEE it.

---

## RULE 0 — THE THEORY

**STATEMENT.** The tuft's illegibility is a GEOMETRY failure, not a colour or
lighting failure. A grass blade is a 0.35 m line; the render row draws it as three
isolated splats at f = 0.15 / 0.55 / 1.0 along that line — spacing 0.14–0.16 m
against a splat display width of 0.02 m. At any camera distance that resolves the
splat at all, seven-eighths of every blade is simply not drawn, and 60 sparse
dotted arcs merge into the ground's own noise. Drawn instead as `ceil(L/w)+1`
contiguous splats — spacing ≤ the splat's own width — each blade reads as a stalk
and the tuft reads as vegetation.

**PREDICTION.** With the grain count derived (below) and nothing else moved —
same albedo, same splat width, same lighting, same camera rig —
`python tools/stone_legibility.py after tuft` produces a frame in which the tuft
is a distinct vertical green structure at 3.2 m, judgeable by eye. The terminal
for "reads as grass" is THE HUMAN; the instrument's before/after pair is the
evidence laid in front of them.

**FALSIFIER.** Named before the run: if, at the same rig, with grain spacing ≤
splat width along every blade, the after frame still shows no vertical structure —
a faint patch, a smudge, or nothing — then geometry is not the gap and this
theory loses. The hunt then moves to where the falsifier points: the lighting
model (all blade normals are `(0,0,1)` — a vertical blade lit as flat ground),
the exposure dial, or the LOD path, in that order.

A description survives any result; this one loses if the line is drawn and still
cannot be seen.

---

## THE DERIVATION (nothing chosen; rule 1)

```
w = 0.02 m          splat display width of a blade -- the EXISTING render-row dial
                    (touchables.py, THE HUMAN: 12.5x the measured 1.6 mm blade,
                    Kosmalla 2025 -- legibility, unchanged by this membrane)
L = 0.35 m          blade height -- the EXISTING design placeholder (THE HUMAN)
spacing <= w        the contiguity condition: a line reads as a line when its
                    grains touch
n = ceil(L / w) + 1 = ceil(17.5) + 1 = 19 grains per blade
spacing achieved    = L / (n-1) = 0.0194 m <= 0.02 m
total splats        = 60 blades x 19 = 1140  (was 180)
```

Every number on the right-hand side was already in the file with its provenance;
the count falls out of the contiguity condition. There is no sweep: 18 fails the
condition, 20 oversamples it, 19 is the closure.

The bent-blade mapping is unchanged — `f * L` along the bend direction, the same
chord the physics' aggregate theta implies — only `f` now walks `k/(n-1)` over 19
grains instead of the three hand-placed fractions. RENDER ROW ONLY: the spring
(k, c, theta_max), the blade count, the disk, and the albedo are untouched — F2's
rule, the same one the stone's 40→160 densification followed.

---

## THE VERDICT (2026-08-04): **FIRED. The theory loses.**

Instrument: `tools/stone_legibility.py`, before/after pair at the blind read's own
rig (`ChimeraEngine/output/tuft_before.jpg` / `tuft_after.jpg`, the after frame
inspected at native resolution, crop x 960–1440 / y 300–620).

Measured: the tuft went from a **faint smudge** (before) to a **solid, brighter
green patch ~70×60 px** (after) — and the prediction was "a distinct VERTICAL
green structure." The after frame shows **no vertical structure**: the 1140
contiguous grains merge into one rounded blob. The falsifier was written for
exactly this outcome — *"the after frame still shows no vertical structure — a
faint patch, a smudge, or nothing — then geometry is not the gap and this theory
loses"* — and it fired. Grain contiguity at the 0.02 m scale is real (the patch
is measurably more solid) and irrelevant to legibility (the patch still does not
read as an object).

The comparison that names the successor theory: **the stone, at the same rig and
the same 0.35 m extent, reads as a solid shaded BALL** (`stone_after.jpg`) —
because its splats carry sphere normals and shade across the surface. The tuft's
blades all carry normal `(0,0,1)`: a vertical blade lit exactly like the ground
it stands in, so it has no shading gradient to separate it from the ground plane
— and it reads, precisely, as a brighter patch OF ground. That is the falsifier's
own named hunt, first item, now promoted by measurement:

**SUCCESSOR MEMBRANE (stated 2026-08-04, before its build):** a blade is a thin
cylinder; its splats must carry a HORIZONTAL normal (the cylinder's silhouette
faces sideways, not up). Prediction: with per-blade horizontal normals — and
nothing else moved — the after frame's patch separates from the ground as a
shaded object. Falsifier: if the blades carry horizontal normals and the patch
still reads as ground, the hunt moves to exposure, then to the LOD/splat-size
path (does the renderer clamp screen-space splat size? 1140 splats merging into
70 px says the mapping `b[:,20]` -> screen pixels is itself unverified).

The line-drawing code stays — not because it passed (it did not) but because it
is the more honest geometry: a blade IS 0.35 m long, and drawing three dots was
never a physical claim at all. The cost is 1140 splats against a terrain of
millions. The membrane's ledger entry closes here, FIRED, with its evidence
published — which is what a falsifier is FOR.

---

## VERDICT 2 (2026-08-04, the successor membrane): **FIRED. Normals are not the gap either.**

Built as stated above: per-blade horizontal cylinder normals, golden-angle
azimuth, Rodrigues-tilted with the bend. Measured at the same rig
(`ChimeraEngine/output/tuft_normals.jpg`, native-res crop): the patch went
**DARKER than the ground and nearly vanished** — physically predictable in
hindsight (at sun_alt 52.5 deg the beam's horizontal component is 0.61 and an
azimuth-averaged horizontal normal harvests far less of it than an up normal's
0.79), and measured regardless. The renderer HONOURS the normals (brightness
moved, a lot) — so the lighting pipeline sees the tuft, and legibility still
does not follow. The prediction ("separates as a shaded object") is not met;
the falsifier fired. The code reverted to up-lit normals — the MEASURED more
legible of the two — with the provenance row saying so.

Two surface membranes eliminated by measurement in one day. What remains of the
falsifier's hunt, in its written order:

1. ~~geometry (grain contiguity)~~ FIRED — the patch got solid, not legible.
2. ~~lighting (normal claim)~~ FIRED — brightness moved, legibility did not.
3. exposure — a GLOBAL dial shared with the ground (THE HUMAN); not movable for
   one object without moving the world's photograph. Not the object-level fix.
4. **the splat -> screen-pixel mapping — unverified, and now the prime suspect.**
   The stone at the same rig and the same 0.35 m extent reads as a shaded ball
   with surface detail; the tuft's 1140 splats merge into a 70 px blob with no
   internal structure at ANY brightness. If `b[:,20]` (splat size) is clamped,
   rescaled, or LOD-merged in the renderer, then every object-level membrane is
   arguing over a dial that is not wired to the screen. **Next: read the
   renderer's projection path (`matter.py` / the splat kernel) and MEASURE the
   mapping — one blade of known width at a known distance, predicted pixel
   width vs rendered.** Instrument first, membrane after; that is rule 0.
