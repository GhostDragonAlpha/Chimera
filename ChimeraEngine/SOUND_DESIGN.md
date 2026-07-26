# THE SOUND — matter's second projection (design)

> **Status: DESIGN (2026-07-25).** The appearance system is built and proven; this is its TWIN, specified
> to sit into the exact same machinery. Nothing here is built yet — it is the plan we build against. The
> operator asked for sound "with the same setup, timelines and everything, so they sit right in," and to
> DESIGN it before improvising. This is that design.
>
> **UPDATE 2026-07-25 — the AI ear EXISTS (revises §2 to HYBRID).** Tested empirically: `qwen2.5-omni-7b`
> DOES hear — via **llama-server direct**, NOT LM Studio (LM Studio loads the mmproj for vision only and
> never wires the audio tower; llama-server's `init_audio` does). Quality is "experimental": right on
> broad features (heard `theStar`'s real sonification as *"a deep, rumbling bass"* — matches the physics),
> imperfect on fine detail. So the sound dyad is **not human-ONLY, it is HYBRID**: the Omni model is an
> *advisory* ear, the operator stays authoritative. Bonus — ONE Omni model served all three senses the
> dyad needs: **eye** (nailed the marble), **ear** (the star rumble), **movie** (understood an ordered
> frame sequence as video → the appearance dyad can judge the MOVIE, not just the end still). Serving: a
> dedicated `llama-server` (omni GGUF + `mmproj-F32`; model on GPU, 5.3 GB projector on CPU) on
> `127.0.0.1:1235`. `sonify.py` is built (`theStar` passes the ear; `aPlanet` wind/water needs tuning).

## The principle — light and pressure are the same matter, projected twice

The render is the matter model projected into **light**: a term's `SCENE` becomes splats become pixels
(`splat_appearance.py`). Sound is the same matter projected into **pressure waves**: a term's `SOUNDSCAPE`
becomes a synthesized waveform. **Sound DERIVES from the physics — no aesthetic pass** — exactly as the
render derives from the matter at every scale. A term is one **timeline slice**; it has TWO projections,
and they unfold on the SAME timeline: you *see* the splat movie and *hear* the sonification, together.

The killer proof that this is physics and not taste: **theSolarSystem's sound is the music of the spheres,
literally.** The proven orbital periods (Kepler, already in the catalog) ARE frequencies — scale each up by
octaves into the audible range and the planets' orbital ratios become a chord whose intervals are the real
orbital resonances. Kepler went looking for exactly this (*Harmonices Mundi*, 1619); we have the data he
lacked. Nothing is composed; the orbits are made audible.

## The twin — every appearance part has a sound part

| appearance (built) | sound (to build) | role |
|---|---|---|
| `splat_appearance.py` — `SCENES`, `project_movie`, `compose_buffer` | `sonify.py` — `SOUNDSCAPES`, `sonify`, `compose_sound` | the GENERATOR: matter → the projection |
| `human_messenger.py` — vision LLM → a TERM; `PHYSICS_READING` | `sound_messenger.py` — the OPERATOR → a TERM; `PHYSICS_HEARING` | the HUMAN side of the dyad |
| `APPEARANCE MESSENGER` gate | `AUDITORY MESSENGER` gate | the prove-workflow gate |
| gallery `/live` — the MJPEG visual stream | gallery `/live` — an audio channel, same timeline | the shared view/ear |

## 1. The generator — `sonify(term)` (matter → pressure)

- Each term with a physical sound has a `SOUNDSCAPE` spec (the audio twin of `SCENES`). Terms that are
  silent by nature (`theDeterminism`, `theMeaning`) simply have none.
- `sonify(term)` synthesizes a **waveform from the term's PHYSICS numbers** through programmed synthesis
  laws (additive + subtractive, plain `numpy` → a WAV; **no GPU needed** — cheap CPU synthesis frees the
  4090 for the vision model). Deterministic (seeded from the term name, like the scenes).
- **Same timeline as the movie:** the waveform's duration is the movie's duration and it EVOLVES with the
  visual begin→end (aPlanet's accretion: chaotic dust-hiss settling into a steady world-hum). In the live
  viewer it loops. Audio and video are two readings of the one slice.

**Grounded examples (the laws, not taste):**
- `theStar` — granulation **noise** (convective turbulence) over a low **hum** whose pitch tracks the star's
  density (helioseismology: a star's p-mode frequency scales with √density). A warm, continuous furnace-roar.
- `aPlanet` — **wind** (filtered noise, intensity from atmosphere density) + **ocean** swell (low broadband,
  from ocean fraction) + a faint rotational sub-bass. The habitable world you can hear breathing.
- `thePlanets` — the six worlds as a **timbre gradient**: hot worlds bright/harsh, cold worlds dark/pure — the
  same hot→cold axis the render shows, in sound.
- `theSolarSystem` — the **music of the spheres**: children's orbital periods → audible frequencies (a drone
  chord in true orbital ratios) under the star's rumble. Composed from the physics (see §5).

## 2. The human-ONLY dyad — `sound_messenger.py`

The proof is still a **dyadAnalysis**: PHYSICS (a NUMBER) and the HUMAN (a TERM) agreeing. But sound changes
one thing, and it is load-bearing:

- **PHYSICS → a NUMBER** — measured features of the waveform the law predicts (dominant frequency, spectral
  centroid, roughness), e.g. "theStar rumbles below ~150 Hz, broadband, no shrill partials."
- **HUMAN → a TERM — and it can ONLY be the operator.** There is **no audio-recognition model**, so unlike
  vision (where the LM Studio vision model stands in as the eye), the sound dyad has **no AI proxy**. The
  operator listens and rules. This is the **permanent form of `human_messenger`'s `human_override`**: the
  ear is *always* the human.
- **Consequence, by design:** the sound dyad **cannot auto-run** — it always waits for the operator. So every
  sound proof **guarantees the operator's presence** — the strongest form of "guarantee the human at the
  critical decision" (the operator's own rule). No model loaded is not a failure mode here; it is the normal
  mode.
- `PHYSICS_HEARING` dict — per term, the expected auditory reading (the twin of `PHYSICS_READING`), so the
  operator's words can be cross-referenced to what the physics predicts → an alignment 0–1.

## 3. Delivery — the audio channel in the live viewer

- `gallery.py` gains a `/sound?term=…` route serving the term's sonified WAV; the `/live` page plays it
  (looped `<audio>`, later Web Audio for tight sync) **alongside** the visual stream — the audio-visual
  shared view, on one timeline.
- A small operator control on the page: **listen, then submit what you hear** (a word + a hold/redo). That
  submission IS the human side of the sound dyad — posted to the engine, recorded, cross-referenced.

## 4. The gate — `AUDITORY MESSENGER`

- A gate parallel to `APPEARANCE MESSENGER`, applied to terms that HAVE a `SOUNDSCAPE`.
- **HUMAN-terminal:** it holds only when the operator has heard the sound and ruled it matches. (Open
  question for the operator: is sound a *required* second projection for a term to prove, or an *additive*
  one — a term proves on its appearance, and sound deepens it? Recommend **additive** at first, hardening to
  required for sound-essential terms later.)

## 5. Composition — `compose_sound(term)`

The twin of `compose_buffer`: a parent's sound is **mixed from its proven children's sounds**, placed by the
same layout that places their bodies. For `theSolarSystem`, each child planet's tone sits at its orbital
frequency and the star's rumble underneath — the music of the spheres, emerging from the proven children,
exactly as the composed *render* is the real star + real marble on orbits. Add a planet to the story, prove
it, and it joins the chord.

## The PROGRAM / TRAIN / HUMAN line, for audio

- **PROGRAM** the synthesis laws (matter property → sound parameter — density→pitch, turbulence→noise,
  orbital period→frequency).
- **TRAIN** the free numbers (which frequencies, how much noise) against reality where it exists
  (helioseismology spectra, real wind/ocean recordings) or against the operator's taste.
- **HUMAN** is the ear (the sole verifier) and the taste terminal.

## Honest limits

- **No AI ear.** Every sound proof needs the operator — by design, not as a gap. I cannot verify sound at
  all; only the operator can. So building this means: I write the generator + delivery, the operator listens
  and judges.
- **The laws are unbuilt.** Each term's synthesis law must be authored (like each visual scene was), grounded
  in the physics, then heard and tuned by the operator.
- **Sync is loose at first** (both loop); tight audio-visual sync (Web Audio) is a later refinement.

## First build (proof of concept)

1. `sonify.py`: `SOUNDSCAPES["theStar"]` + `sonify("theStar")` → a warm rumble from its physics (a WAV).
2. `gallery.py`: `/sound?term=theStar`; the `/live` page loops it under the visual.
3. The operator opens `/live`, **hears** theStar, and rules — the first human-only sound dyad.

Then `aPlanet` (wind + ocean), then `theSolarSystem` (the music of the spheres via `compose_sound`).
