# theEye

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
>
> **RULE 0 IS ENFORCED AT S-1 VALIDATE** — every port tested alone, and `port_test()` REFUSES to
> register a test that names no falsifier. The model it feeds: `docs/THE_COMPILER.md` — ports →
> primitives → programs → parser → runtime → calibration.
>
> **[docs/THE_LAW.md](../../../../../../../../../../../../../../../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **chapter 30** of the story  ·  **t = 5.75715e+15 s** since theZero  ·  lasts **3.52941 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** Everything above this chapter derived a world. This one derives the hole the
world has to fit through. An eye is a two-millimetre aperture, and a two-millimetre aperture cannot
be argued with — diffraction puts a hard floor under how fine a detail can survive the trip to the
retina, and no amount of retina underneath recovers what the pupil already threw away. So how much
detail is worth drawing is not a taste question. It is an optics question, and it has an answer.

*The smallest membrane in the body so far.* Twenty-four millimetres, and its film is one interval
between blinks: ten fixations, ten saccades, and the lid coming down at the end.

## The chain, and the number at the end of it

The parent hands down how much sunlight arrives (`S_earth = 1.005`), how high the sun is
(**40.1°** — THE ONE SUN, matter.py's law at the film's opening, not a second star), and how thick
the air is (**0.52 bar**). Nothing else is needed.

| step | | |
|---|---|---:|
| the star's light at the top of the air | `S · 1361 W/m² · 93 lm/W` | **127,193 lx** |
| through 1.55 air masses at τ = 0.146 | Beer–Lambert, τ scaled by the parent's own pressure | ×0.798 |
| onto the ground, sun 40.1° up | direct 65,376 + skylight 8,287 | **73,663 lx** |
| off a 20%-reflectance scene | `L = Eρ/π` | **4,690 cd/m²** |
| the pupil that forces | Moon & Spencer 1944 | **2.202 mm** |
| **what diffraction then allows** | **`θ = 1.22 λ / D`** | **1.057 arcmin** |

**The 20/20 line on an eye chart is 1.00 arcmin.** Nothing in that chain was fitted to it — it is an
insolation, an air pressure, a sun altitude and the CIE's 1924 luminous-efficiency curve read off
disk, multiplied together. **20/21.1.**

### The wavelength was not typed either

`λ` is where `cie1924_photopic_vlambda.csv` is highest, found by parabola through the top three
samples: **555.14 nm**. The dark-adapted curve in the file next to it peaks at **506.5 nm**. Nobody
in this chapter chose a colour to design against; the CIE measured it in 1924 and the file says so.

## The second road to the same place

The first road went through sunlight and air. The second goes through a cadaver's retina and never
mentions this world at all.

| | |
|---|---|
| peak foveal cone density (Curcio 1990) | 199,000 /mm² |
| → hexagonal spacing `√(2A/√3)` | **2.409 µm** |
| ÷ the eye's nodal distance, 16.67 mm | **0.4968 arcmin per cone** |
| → Nyquist sampling limit | **60.4 cycles/degree** |
| **the pupil whose diffraction cutoff equals that** | **1.921 mm** |
| the pupil this world's daylight actually forces | **2.180 mm** |

**1.135.** The eye is built at its own diffraction limit to within 14%, and the two numbers share no
input: one is sunlight and air, the other is a cone mosaic. Below that pupil the retina is finer
than the image it is given; above it the image is finer than the retina can sample. A body that
spends nothing on waste should sit near the crossing, and this one does.

A third check falls out of the same constant. Angle-to-retina is `16.67 mm/rad` = **290.9 µm per
degree**; Drasdo & Fowler measured **291**. And dividing a 1.5 mm foveal pit by it gives **5.16°**
where the clinic says ~5.2°, and a 0.35 mm rod-free floor gives **1.203°** where the clinic says
~1.2°. Three clinical numbers reproduced from one optical constant that was not fitted to any of
them.

## And the free number is shown not to matter

The scene's reflectance is the one thing here that is neither derived nor inherited — this membrane
does not know what the person is looking at. So instead of defending the choice, the chapter
measures how much it is worth:

| scene reflectance | pupil | acuity |
|---:|---:|---:|
| 0.05 (fresh asphalt) | 2.341 mm | 0.995 arcmin |
| 0.20 (declared) | 2.180 mm | **1.068 arcmin** |
| 0.80 (snow) | 2.076 mm | 1.121 arcmin |

**Sixteenfold in reflectance is 12.7% in acuity**, because the pupil law is logarithmic. The free
number is doing almost none of the work, and that is a fact rather than a reassurance.

## How little of the world is sharp

| | | |
|---|---:|---|
| the whole visual field | **5.271 sr** | 42% of the entire sphere, standing still |
| horizontal, both eyes | **200°** | union of one eye's 100° temporal and 60° nasal, twice |
| horizontal, in depth | **120°** | where the two fields overlap |
| vertical | **130°** | 60 up, 70 down — a brow beats a cheek |
| the fovea | 5.156° | **0.121%** of the field |
| **the foveola — the actually-sharp part** | **1.203°** | **0.0066% of the field** |

**One part in fifteen thousand.** Everything a person believes they can see at once, they cannot.

And there is a hole in it. The optic disc — where the nerve and the vessels leave — has no receptors
at all: 5.5° × 7.5°, 15.5° out from fixation, **0.00987 sr**.

> **The blind spot is 28.5 times the area of the sharpest part of vision, and nobody notices it.**

## What the renderer is being told

| | |
|---|---:|
| pixels per degree, to match the eye | **56.2** |
| the whole field at foveal acuity | **54.6 megasamples** |
| the whole field at the acuity the eye actually has | **0.295 megasamples** |
| **foveated rendering is worth** | **185×** |
| finest feature worth generating at 1 m | 0.311 mm |
| … at 10 m | 3.11 mm |
| … at 100 m | 3.11 cm |
| … at 1 km | 31.1 cm |
| a 1.755 m person stops being resolvable at | **5.65 km** |
| stereo depth runs out at `IPD / 20 arcsec` | **660 m** |

The foveated figure comes from integrating Levi & Klein's measured falloff — `MAR(E) = MAR₀·(1 +
E/2.5°)` — over the measured field. **It was not fitted to anything, and it lands on the retina's own
wiring:** 0.295 million resolvable elements against **1.2 million ganglion cells** per eye is
**4.07 axons per element**, which is what an ON/OFF midget pair plus parasol cells actually is.

Beyond 660 m two eyes stop paying for themselves, so a second view is 660 m of value and then heat.

## The eye is not a fraction of the body

Every other chapter about this human scales with its stature. This one does not, and it is worth
saying why: an eyeball is 24 mm in a tall adult and 24 mm in a short one — adult-sized by about
thirteen, and varying by about a millimetre across the whole adult range.

The stub this replaced multiplied stature by 0.024 and published a **42 mm** eyeball. Seventy-five
per cent too big, and the tell was that it *moved when the body's height moved.*

The same fact measured a second way, from 4,082 ANSUR II adults: interpupillary breadth
**64.0 mm**, with a Pearson correlation against stature of **0.18**. Stature explains 3% of the
variance. A person's eyes are the species' eyes, not their own.

## Ten orders of magnitude, and the iris barely helps

| | |
|---|---:|
| the range the eye works over | **14 log units** (10⁻⁶ to 10⁸ cd/m²) |
| what one adaptation state covers | **~3 log units** |
| pupil, wide open to fully shut | 7.85 mm → 1.91 mm |
| **what the pupil is worth, by area** | **1.23 log units** |
| **the iris's share of the whole range** | **8.8%** |

**The other 91% is chemistry, and chemistry is slow.** Hecht, Haig & Chase measured it in 1937: cones
finish in about five minutes, the rod–cone break is at seven, and rods keep improving for another
half hour.

> Walking out of a lit room into a polar night on this world, full dark adaptation takes
> **2,100 s — 603 strides, and 713 metres of walking** before the dark becomes a place.

The pupil, meanwhile, has a 220 ms latency and is done in a second. It is the fastest part of vision
and the least important.

## Its clock

`duration_s` is **3.529 s** — one interval between blinks, at the measured resting rate of 17/min.
That is the eye's longest closed loop: the period at which the tear film has to be renewed or the
cornea stops being an optic. Inside it sit **10.2 fixation–saccade cycles**, which is the mechanism
this whole chapter is about — *a 1.2° sharp spot is made into a seen world by moving it three times
a second.*

| | |
|---|---:|
| fixation (Rayner, natural scenes) | 300 ms |
| saccade, 12° amplitude (`2.2A + 21 ms`, Bahill's main sequence) | 47.4 ms |
| **peak velocity that a raised-cosine profile then predicts** | **398 °/s** |
| the main sequence measures, at 12° | 300–500 °/s |
| blink | 150 ms, 4.25% of the interval |

The waveform was an approximation; its consequence was not.

### And a fixation is not a stop

Written without this, two thirds of the movie's frames came out byte-identical — which was a
statement about my model, not about eyes. **The eye is never still.** Ocular drift wanders a few
arcminutes at a few arcminutes per second, with a tremor of about a third of an arcminute at
30–100 Hz riding on top.

| | |
|---|---:|
| drift excursion | 2.5 arcmin |
| tremor | 0.3 arcmin at 60 Hz |
| **the drift, in foveal resolvable elements** | **2.34** |

Nothing against a 200° field, which is the honest thing for it to be — and about two elements at the
fovea, which is the scale that matters. **It must not be still.** Ditchburn & Ginsborg in 1952 and
Riggs and colleagues in 1953 optically stabilised the retinal image so that it *could not* move, and
it faded to nothing within a couple of seconds. A perfectly steady eye is a blind eye: the receptors
are difference detectors, and a constant signal is no signal at all.

## What you are looking at

The eye's own sampling lattice — one grain per resolvable element — over one interval between
blinks. **The size of each grain is the angle it resolves.** A splat of angular size *s* at radius 1
subtends *s* radians, so the grains are not symbols for the resolution; at true scale they *are* it.
Fovea to periphery is a **41×** range in one picture.

The construction is the acuity law and nothing else: rings spaced by the local minimum resolvable
angle, and the same spacing again around each ring. **What falls out is the log-polar layout the
visual cortex is actually wired in.** Nobody put it there — tiling a field with elements that grow as
`(1 + E/2.5°)` has no other shape available to it.

- **The oval is the head's field and does not move.** The lattice inside it does. That is the whole
  trick of vision, in one frame.
- **The gap that travels with the fovea is the optic disc.** It is eye-fixed, so it rides along.
- **There are two different kinds of nothing here, and telling them apart is the point.** In the
  blind spot there are *no receptors*, so no matter is emitted — a real hole. Outside the oval there
  *are* receptors and the brow and the cheek and the nose are in the way, so the grains are emitted
  and lit by zero: they go black through the same call that lights everything else. The faint ghost
  beyond the field is how much retina a face costs.
- **The colour is the macular pigment and nothing else** — lutein and zeaxanthin absorbing blue in
  front of the foveal cones, amber at the centre and gone by 8°, computed through the CIE 1931
  colour-matching functions. The *macula lutea*: they called it the yellow spot before anybody could
  measure a spectrum.
- **The field dims while the eye is in flight**, by the 0.5 log unit of saccadic suppression Burr,
  Morrone & Ross measured. The world does not smear, because it is turned down while the eye moves.
- **At the end the lid comes down**, and what is under it is not black but dim red — hemoglobin
  passes long wavelengths, which is the same measurement `theSkin` derives its own colour from.

The lattice drawn is the true one decimated by a stated factor of 10; the real one holds 295,000
elements and a splat buffer will not take that. The *relative* sizes, which are the entire content
of the picture, are exact.

## What this chapter honestly cannot do

**The star's colour does not reach this membrane, and that is a broken carry-chain, not an
oversight.** `aBlueWorld` derives `T_star_surface` and `L_star`. `aTerrain` does not carry them.
`theGround` does not carry them. So by the time the chain reaches `theHuman`, the star's *spectrum*
is gone and only its total flux survives as `S_earth`.

Three things follow, and none of them is worked around:

- The luminous efficacy above is **93 lm/W, the Sun's**, flagged `efficacy_is_a_solar_fallback`. The
  machinery to compute it from a temperature is here and is checked: at 5772 K it returns
  **92.03 lm/W** against a measured ~93, and it maxes at 95.4 near 6600 K where the literature puts
  the blackbody maximum at ~95. It is wired to read `T_star_surface` from the parent the moment
  anyone carries it, so **the number will move by itself** — tested: with the chain repaired the
  efficacy goes to 92.58, the Wien peak appears at 496 nm, and the illuminance shifts.
- This world's daylight has **no derived colour**, so the render is neutral outside the macula. That
  grey is a missing number made visible, not a choice.
- The chapter cannot put the star's Wien peak beside the eye's own. At the Sun's 5772 K the peak is
  **502 nm** — within 1% of the *scotopic* 506.5 and 10% to the blue of the *photopic* 555.1 — and
  whether that also holds for this star is exactly what cannot be said here.

**The horizon is not derivable either.** `horizon = √(2Rh)` needs a planet radius, and theHuman
publishes none. It could be reconstructed from an assumed density — and it is not, because that
would be taste wearing a derivation's clothes. `horizon_reachable` is `false`, and the key is
**absent rather than NaN**: a NaN carries the right name and the right unit and poisons everything
that binds to it. The eye height (1.624 m) is published and the law is written; supply an `R` and
the horizon and its grain size both appear.

## What is honestly still missing

- **Only two of the six eye rows in `PHYSICS_OF_THE_HUMAN.md` can dock.** `folding.py` has declared
  signatures for H6.03 (the schematic eye) and H6.06 (acuity and field extent), and both now bind
  here. H6.01 (V(λ)), H6.02 (colour matching), H6.04 (pupil vs luminance) and H6.05 (dark
  adaptation) are all *used* in this file and none of them has a signature yet, so nothing can check
  that they were used correctly.
- **The pupil law is Moon & Spencer 1944, not Watson & Yellott 2012.** The modern unified formula
  adds field size, age, and monocular-vs-binocular viewing; this chapter has none of those and does
  not pretend to. Age in particular is real and large — a 60-year-old's dark-adapted pupil is
  roughly two thirds of a 20-year-old's.
- **The drift and tremor are the right size but the wrong shape.** Their amplitudes are measured;
  their waveforms are two incommensurate sinusoids and a 60 Hz oscillation standing in for what is
  really a random walk with a correction. Microsaccades — 0.1–1.0° at about 1.5 per second — are not
  modelled at all, and they are the part of fixational motion that a viewer could actually see.
- **Rods are in the numbers but not in the picture.** At 5,886 cd/m² rods are saturated and
  contribute nothing, so drawing a rod/cone gradient in daylight would have been a decoration. The
  measured rod topography — zero in the foveola, peaking at ~18° — is exactly what makes a faint star
  visible when you look slightly away from it, and this chapter derives none of it. It is also the
  reason the dark-adaptation numbers above are a *time* and not a *picture*.
- **The macular band shape is a single Gaussian fitted by eye** to the measured lutein absorbance
  envelope. The peak density and the 1.5° e-folding are sourced; the band's shape is not.
- **The sequence of places the eye looks is arbitrary** and says so. The step *length* is measured
  (12° mean in free viewing) and the step *duration* is measured (the main sequence); only the
  direction is invented, because nothing in this membrane knows what is worth looking at. That is a
  property of a scene, and there is no scene here.
- **No visor, no torch, no thermal band.** The five story verbs this chapter was declared for
  (`Cycle Visor Optics`, `Helmet Torch`, `Clear Visor Condensation`, `ADS`, `HUD Toggle`) are all
  still unbuilt. What has changed is that they now have something to be built *against*: a
  transmission multiplies an illuminance that is derived, and a torch is a second light source in a
  chain that now knows what a lumen is worth here.
- **One eye, not two.** Everything except `stereo_range_m` and the 200°/120° split is monocular. Eye
  dominance, vergence, and the fact that the two blind spots do not overlap are all absent.
- **A caution found while writing this, and left as a warning in `units.json`:** `folding.py`
  matches unit suffixes case-insensitively on a second pass, so **any key ending `_nm` is read as a
  newton-metre.** `photopic_peak_nm` would have bound a wavelength into a torque socket, silently,
  and it looks completely correct. This chapter publishes `photopic_peak_wavelength` instead; the
  collision is still live for the next person who types a wavelength the obvious way.

*Contained in `theHuman`. What it hands on: how much detail is worth making, and the news that
99.99% of the field does not need it.*
