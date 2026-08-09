# THE EXPERIMENTAL METHOD

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
> **[docs/THE_LAW.md](../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 27 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> How this studio finds out what is true about a running system.
>
> **Rules 1-10** come from the 2026-07-23 GLM-5.2 session, where *every single conclusion reached by
> reasoning was wrong, and every conclusion that held came from a measurement.* They are about not
> fooling yourself while DEBUGGING.
>
> **Rules 18-21** come from the same 2026-08-01 session, later in the day, and are about DIRECTION:
> where to look when everything you can see is already correct. Rule 21 is the operator's, and it
> reframes the other three.
>
> **Rules 12-17** come from the 2026-08-01 material-genome and terrain session, where six separate
> results were written down as true and then **reversed by a control**. They are about not fooling
> yourself while REPORTING — a harder problem, because a wrong debugging conclusion announces itself
> the next time you run the thing, and a wrong measurement does not announce itself at all.
>
> *(The GLM-5.2 model itself was removed the same day as a liability — see
> `pi-servers/README.md`. It is kept here only as a debugging example; the lesson is
> about method, not about that model, and nothing here implies GLM is still available.)*

This is the sibling of `docs/RESULT_GRADING_RUBRIC.md` (which grades *features*) and
`core/why.py` (which asks whether a claim reaches a terminal). This document is about
**diagnosing live systems** — performance, faults, "it seems slow."

---

## RULE 1 — A PARAMETER SWEEP IS AN ADMISSION THE DERIVATION WAS NOT DONE

CLAUDE.md has carried the operator's words since 2026-07-28: *"You have to know it works because
it's proven mathematically first before you start training."* On 2026-08-02 that correction was
needed a second time, and the shape of the relapse is worth keeping because it looked like rigour.

A walker would not walk. The response was a **four-variant parameter sweep** — alive bonus,
stagnation floor, penalty weight, effort cost — run in parallel, on the reasoning that measuring
four guesses beats making one. It even sounded like the project's own method: one variable per
variant, controls, a fair comparison.

**Every variant was asking the body for a speed it physically cannot walk at.**

    this world     g = 7.076 m/s^2 (0.722 Earth),  leg 0.9201 m
    the body derives its own comfortable speed:    0.9924 m/s
    the trainer was targeting:                     1.285  m/s   <- MEASURED ON EARTH

Froude settles it: `Fr = v^2/(gL)`, and equal Fr means dynamically similar gait. Earth walking at
1.285 m/s is Fr = 0.183; demanding 1.285 m/s at 7.076 m/s^2 is Fr = 0.254 — 39% higher, heading
toward the walk→run transition. So the velocity term demanded a running-ward gait while the
tracking term demanded Earth *walking* envelopes. The two pulled against each other, and the body's
best answer was to satisfy neither and collect the alive bonus.

> THE CROUCH WAS THE ONLY STABLE POINT IN A CONTRADICTORY REWARD.

The stride clock was wrong too, though NOT by the number first published here. A pendulum goes
as sqrt(L/g) -- but the honest comparison is against what `theHuman` DERIVES for itself, not
against a transported Earth stride. The body publishes `step_time_s`, so its stride is **1.1730 s**
and the trainer's 1.127 s was **3.9% fast** -- not the 18% this rule claimed for a day. The 1.3267 s
figure was Earth's 1.127 s divided by sqrt(g/g_E), i.e. the very move this rule forbids, committed
by the gate written to enforce it. See RULE 25.

**A sweep could never have found this.** Four variants all asking for an impossible speed rank four
flavours of the same failure, and the winner would have been whichever failed most gracefully.

    THE TELL: if you are about to run variants, ask what QUESTION each one answers. If the
    answer is "which number is best", stop — that is a search where a derivation belongs.
    Sweeping is legitimate only for numbers that are genuinely FREE, and a target speed
    derived by Froude from measured gravity is not free.

**ENFORCED, not merely written down:** `python tools/training_gate.py --target-speed X --stride-s Y`
refuses a run whose targets are not Froude-consistent with the world the body stands in. It checks
three things — speeds scaled by sqrt(g/g_E), strides by sqrt(g_E/g), and agreement with what the
body itself publishes — and it refuses the trainer as it stood on 2026-08-02.

---

## RULE 2 — MEASURE THE THING, NOT A PROXY FOR THE THING

I spent hours optimising **prefill** (14 → 1.38 s/layer, ~10×) because it was easy to
sample. The metric the operator actually waits on is **decode tokens/sec**, which moved
**0.26 → 0.289**. Ten-fold improvement in the wrong number.

**Ask first: what does the human actually wait for?** Optimise that. A proxy you can
measure in 90 seconds is seductive precisely because it is cheap.

---

## RULE 3 — BENCHMARK IN THE STATE THE SYSTEM WILL ACTUALLY BE IN

Measured C: at **1,849 MB/s** random-4MB while it had 480 GB free, concluded it was 5.3×
faster than E:, and moved a 357 GB model onto it. In place, it measured **11.25 s/layer
vs E:'s 7.50** — 50% *slower*.

Two reasons the benchmark lied, neither visible in the benchmark:
- **The drive was 87% full by the time the model lived there.** SSDs lose substantial
  performance past ~80% as spare area and SLC cache shrink.
- **`pagefile.sys` lives on C:.** A memory-mapped model on a RAM-constrained box pages
  constantly, so the model ended up competing with itself for the same spindle.

**A synthetic benchmark measures the drive. Your workload measures the system.**

---

## RULE 4 — DISTRUST ANY PROBE THAT CAN READ A CACHE

colibrì's startup probe measured the freshly-written D: mirror at **5.53 GB/s** and routed
80% of expert reads to it. **D: is a SATA SSD whose interface caps at ~550 MB/s.** The
probe had read the OS page cache, not the disk. Cost: **7.50 s/layer** instead of 4.50 —
a 40% penalty from one bad number, and the tool warned about it in a line nobody read:

```
[MIRROR] no O_DIRECT on the mirror: the probe may read the page cache
```

**Sanity-check every measurement against a physical limit.** SATA III cannot exceed
~600 MB/s. If your number beats the interface, you measured something else.

---

## RULE 5 — WATCH WHAT THE MACHINE IS DOING, NOT WHAT IT REPORTS

The single most useful instrument all night was **the operator looking at Task Manager**.

| Operator observation | What it actually found |
|---|---|
| "it's pulsing" | CPU and GPU strictly alternating — an un-overlapped pipeline (`COLI_CUDA_PIPE=1` → `2`, 5.63 → 4.77 s/layer) |
| "temperature is only in the high 50s" | a 4090 at 39 °C / 46 W is **starved, not working** — TDP is 450 W |
| "only the E drive is seeing activity" | the mirror wasn't configured at all yet |
| "the demand is on D and E is idle" | the split was inverted; fixing it went 7.50 → 4.50 s/layer |

**Temperature and power draw are truth signals.** A cool GPU under load is an idle GPU.
`nvidia-smi --query-gpu=utilization.gpu,temperature.gpu,power.draw` — utilization alone
lies (it counts any kernel activity in the window, so a stalling GPU reads high).

**Sample CPU and GPU *together*.** Each looked busy-ish alone; sampled in the same loop
they were visibly taking turns, which is what pointed at the pipeline flag.

---

## RULE 6 — CAPTURE STDERR BEFORE YOU DIAGNOSE

The server returned, for hours:

```json
{"message": "The colibri engine failed to process the request.", "code": "engine_error"}
```

That message is generated by `except Exception` at `openai_server.py:1036`, which relabels
**every** failure identically. It is not information.

Relaunching with `-RedirectStandardError` and reading the log gave the answer in one line:
prefill was at layer 21/78 when the request was killed. **The engine had never failed —
it was executed mid-work by a 300-second timeout shorter than its own minimum runtime.**

**If a component's error text is generic, it is a category, not a diagnosis. Go find the
log.** Launch detached processes with stdout/stderr redirected to files from the start.

---

## RULE 7 — ONE VARIABLE AT A TIME, AND KEEP THE CONTROL

Every config change was measured in isolation against the previous best:

| Change | s/layer |
|---|---:|
| baseline (CPU) | 14.00 |
| GPU mode | 7.50 |
| expert tier 8 → 13 GB | 5.63 |
| `COLI_CUDA_PIPE=2` | 4.77 |
| mirror, correct weights | 4.50 |
| mirror, **wrong** weights | 7.50 |

The last row is why this matters: the *same hardware change* produced 4.50 or 7.50
depending on one parameter. Had it been bundled with the pipeline change, the pipeline
would have been blamed.

**Bake the proven config in before testing the next thing** — so a failed experiment
never costs you a working state.

---

## RULE 8 — RECORD THE NEGATIVE RESULTS

Things that did **not** work, and are written down so nobody repeats them:

- **Model on C:** — 50% slower than E:. 357 GB copied, measured, reverted, deleted.
- **`--vram 18` and `--repin`** — byte-identical placement to 13 GB (621 experts both
  times). The cap was a policy ceiling, not memory.
- **`--ctx 262144`** — evicts a third of the experts, decode drops **42%**.
- **Spatial voting** (splat DNA, same principle) — 82.5% → 82.8%, flat.

An un-recorded negative result gets re-run by the next agent at full cost. `docs/HISTORY_BOOK.md`
and `graphify_record elimination` exist for exactly this.

---

## RULE 9 — ARITHMETIC BEFORE ACTION, BUT VERIFY THE MODEL BEHIND IT

Estimated the KV cache at ctx 1,000,000 as **1,785 GB** using
`layers × kv_heads × head_dim × ctx × 2 × 2`, and advised against it.

Actual at 262,144: **47.7 GB** — my formula was **~10× too pessimistic**, because GLM-5.2
uses compressed latent attention rather than storing full K/V per head. The operator
pushed back, we tried it, and 256K loaded fine.

**Do the arithmetic — it prevents most disasters. Then check whether its assumptions hold
for this system.** State the estimate as an estimate, and let the machine overrule you.

---

## RULE 10 — READ THE TOOL'S OWN SOURCE AND CHANGELOG

Three of the biggest levers were undocumented in any workflow file and found by grepping
the tool itself:

```
COLI_MODEL_MIRROR    # dual-drive read bandwidth      (CHANGELOG #421)
COLI_CUDA_PIPE=2     # resident pipeline, CPU/GPU overlap  (README)
--queue-timeout      # the flag that fixed the actual bug  (coli:989)
```

`getenv("...")` / `add_argument("...")` sweeps over a tool's source enumerate its real
control surface in seconds. `--help` showed `--queue-timeout`; only the **source comment**
explained that `PIPE=1` merely reorders I/O while `PIPE=2` keeps the residual stream
on-device.

---

## RULE 11 — THE OPERATOR'S OBSERVATIONS OUTRANK YOUR MODEL

Every major correction tonight came from the human watching the machine:

- *"it seems to be pulsing"* → the pipeline flag
- *"the CPU isn't being used very much"* → CPU/GPU alternation
- *"only the E drive is seeing activity"* → mirror not wired
- *"the demand is on D"* → inverted split, 40% swing
- *"1 million context"* → my formula was 10× wrong
- *"just run it on CPU so I have the GPU for the fast model"* → the correct engineering
  call, which no amount of tuning would have reached

**When the operator says something looks wrong, measure that thing before defending your
model of the system.** They are watching the machine; you are watching your assumptions.

---

## RULE 12 — RUN THE INSTRUMENT ON SOMETHING WHOSE ANSWER YOU ALREADY KNOW

Rule 7 says keep a control. This is the sharper form, and it is the most productive single rule in
this document: **push a KNOWN subject through the WHOLE instrument, end to end, and see what it
says.** Not a held-out sample, not a second condition — a thing whose answer you know because you
made it.

The 2026-08-01 material work had one to hand and nearly did not use it. To read a material genome
out of a generated video, the take was fitted with Gaussian splats on the GPU, and its `log_size`,
`aniso` and `opacity` distributions came back squarely inside the range real 3DGS scans occupy.
That is a publishable-looking result. Then the same fit was run on **the clay we had sent the
generator** — one flat grey, rendered by our own engine from geometry we derived:

| feature | generated take | the clay control | |
|---|---|---|---|
| `log_size` | −0.024 | −0.039 | identical |
| `aniso` | 0.447 | 0.419 | 6.9% |
| `opacity` | 0.802 | 0.806 | 0.5% |
| `R`/`G`/`B` | .667/.635/.629 | .888/.887/.870 | **−0.22 to −0.25** |

Three of the four were the FITTER'S signature, not the material's — a fixed-N fit pins mean splat
area at `area/N` by conservation, so they were decided before the first optimiser step. Only colour
carried information. Without the control, three invented numbers enter the codebook and every
genome built on them is wrong in a way nothing downstream can detect.

**It kept working all day.** The same control later showed that an apparent detail improvement was
render grain (Rule 12), and a third run showed that a visible cross-hatch came from the canvas
rather than from the new code blamed for it (Rule 14).

    A measurement without a control is not a weak measurement. It is not a measurement.

**The best control is a thing you built**, because then you know the answer by construction rather
than by another measurement that could be wrong in the same way.

---

## RULE 13 — MEASURE AT THE SCALE THE THING LIVES AT

A measurement taken at the wrong scale reports the ABSENCE of whatever it cannot resolve, and it
reports it as confidently as a real null.

`aTerrain` gained five octaves of relief reaching down to ~3 m. Measured on a 480p render of the
whole 12 km patch, the surface came back *less* complex than before. The arithmetic says why: the
finest drawn octave is 23.4 m, the patch spans ~300 px at that framing, so that octave projects to
**0.6 px**. The instrument was structurally blind to exactly the thing that had been added — and it
did not return "cannot see", it returned a number, in the wrong direction.

Framed so the octaves were several pixels across, the same test reversed: 1.36× raw and **1.31×
after a denoise**, against 0.90× at the wide framing.

    Before believing a null, compute how many PIXELS (or samples, or bins) the effect occupies
    in your instrument. If the answer is under one, you measured your framing.

This is LOD applied to measurement rather than to rendering, and it is the same doctrine: a membrane
is examined at its own scale, by an instrument that resolves it.

---

## RULE 14 — A THRESHOLD DEFINED IN TERMS OF THE POPULATION IT MEASURES CANNOT REPORT ANYTHING ABOUT THAT POPULATION

Adaptive densification was added to the splat fitter so that the final splat count would become a
MEASUREMENT of surface complexity rather than an echo of a command-line flag. Two growth rules were
written before one worked, and both failed the same way:

| rule | result |
|---|---|
| grow the top 12% by positional gradient (a quantile) | take and clay both reached **5,619 splats — identical to the digit** |
| grow above 2× the MEDIAN gradient (meant to read the tail) | both finished at **0.253 splats/px — ratio 0.999** |
| grow where the RESIDUAL exceeds an absolute 2% | **1.398×** — content-driven at last |

A quantile is 12% of a population whether that population is straining or idle. A multiple of the
median looks different but is not: gradient-magnitude distributions have nearly the same *shape*
whatever the image contains — they differ in scale, not in skew — so the fraction clearing 2× its
own median is a property of the distribution FAMILY, not of the picture.

The residual works because it is an outside reference: *"these pixels are still wrong by more than
2%"* is true or false regardless of how any other splat is doing, and it terminates on its own.

    Self-normalisation is the enemy of measurement. Every normalisation buys robustness by
    DISCARDING a degree of freedom — check that it is not the one you came to measure.

The same trap in a different coat: `log_size` in a material genome is defined relative to its own
capture's median, so a take treated as ONE element reports ~0 **by construction**, and will read
"inside the reference range" no matter what it contains.

---

## RULE 15 — SUSPECT THE INSTRUMENT'S CONSTRUCTION, NOT ONLY ITS READING

Rule 5 says watch what the machine does rather than what it reports. This is one level deeper: the
DATA can carry an artifact of how it was built, and then a correct instrument reads a correct number
off a subject that is lying.

After the octaves went in, `aTerrain` rendered with a diagonal cross-hatch. The new code was the
obvious suspect and was rebuilt in Fourier space to remove any periodicity. The cross-hatch stayed.
Measured, as the ratio of most- to least-favoured direction in each field's power spectrum
(1.0 = isotropic):

| field | directional ratio |
|---|---|
| `_red_surface` canvas — 3 plane waves × 7 octaves | **27.8×** |
| the same after 500 steps of erosion | **8.2×** |
| the new detail field (Fourier noise) | **1.1×** |

The new code was innocent. Twenty-one plane waves is an interference pattern, not a spectrum — and
erosion, which the docstring asserted would destroy it, only halves it twice, because incision
follows the ground it is handed. **A comment claiming one process cleans up after another is a
hypothesis, not a fact.**

The sting is in what it had been doing to a measurement nobody doubted: directional spikes drag a
RADIAL average off the true slope, so the membrane's spectral exponent had been reading **2.54**
when the underlying law gives **2.95 ± 0.08**. The fit was correct; the field was an artifact. And
nothing downstream could have caught it, because a plausible number under a correct formula is
invisible to reading — the same species as the `* 0.0` dead terms in `docs/THE_FOLDING.md`.

---

## RULE 16 — MATCHING NAMES IS NOT MATCHING DEFINITIONS

`story/folding.py` checks that published numbers carry compatible units. It cannot see a FORMULA in
code that computes a differently-defined quantity under the same name, and that is where four
defects hid in one afternoon. Joining an existing codebook meant matching
`Construction/material_elements.py`, and every one of these was written from the name alone:

| feature | the codebook's definition | what had been written |
|---|---|---|
| `aniso` | `1 − min/max` → **[0,1)** | `max/min` → [1,∞) |
| `log_size` | log of the median axis, relative to the capture's own median | log of the geometric mean, over the image diagonal |
| `greenness` | `G − max(R,B)` | `G − ½(R+B)` — reads magenta as green |
| opacity cut | **> 0.5** — *"haze is not a material"* | > 0.05 |

The `aniso` error is the instructive one: it read **2.25** against a reference range of 0.296–0.996
and looked like a spectacular finding — a generated take falling far outside anything real. It was
a unit-free quantity on the wrong interval, and no dimensional check can ever see that.

    When you join someone else's codebook, THEIR FILE IS THE AUTHORITY. Open it, read the
    formula, and match it line by line. A shared name is a coincidence until you have checked.

---

## RULE 17 — DERIVE THE SHAPE, LET PHYSICS SET THE LEVEL — AND WHEN THEY DISAGREE, THAT IS THE FINDING

Continuing `aTerrain`'s spectrum below its grid needed two things: how fast amplitude falls per
octave, and how tall the whole ladder stands. They come from different places, and trying to take
both from one place is what manufactures a fudge factor.

- **The SHAPE is derived.** For a 2D field with PSD ~ k^−β the octave variance goes as k^(2−β), so
  amplitude goes as k^(1−β/2) — and β is MEASURED off the membrane's own eroded surface. Notably not
  the canvas's own falloff: erosion steepens the spectrum it was handed, so inheriting the canvas's
  number would under-produce at every octave.
- **The LEVEL comes from a physical constraint the membrane already enforces.** β < 3 means slope
  grows without bound as wavelength falls, so the spectrum *cannot* set the level. The friction angle
  can, and `slopes_below_repose` was already published and already checked. Bisection finds the
  largest level at which that existing test still passes.

**The two disagreed by a factor of twenty, and the disagreement is the result**: the level lands at
0.051, meaning the spectrum wants ~20× more sub-grid relief than the ground can physically stand.
That is not a clamp chosen to look right — it is the threshold-hillslope regime every talus cone and
scree slope sits in, and it was arrived at because two independent derivations were allowed to
contradict each other in public.

A related trap caught the same day: the first version capped each octave at its own repose limit
independently. Five octaves each at the limit sum to well past it, because **slopes add**. A
constraint on the whole surface must be applied to the whole surface.

---

## RULE 18 — BACKTRACE: DEBUG UP THE CHAIN, NOT FORWARD FROM THE SYMPTOM

The operator's method, and it is better than the one it replaced. **Forward debugging finds the
place an error became VISIBLE. Backtracing finds the place it ENTERED.** In a hierarchy where every
child consumes its parent's numbers, those are rarely the same membrane, and the first is where you
will waste the day.

MEASURED, on 2026-08-01. A foot passed through the floor. Six hypotheses were tested against the
foot and every one was eliminated:

| interrogated | verdict |
|---|---|
| segment lengths | sourced from ANSUR II — clearance unmoved |
| pelvis height | at geometric maximum, 0.5124 against a 0.5123 ceiling |
| ankle sign | flipping it does not reorder the profile |
| half-cycle offset | all three curves sampled at one `f` |
| knee amplitude | 63.8° at 71%, dead centre of the literature band |
| knee phase | correct; the sweep found a lever with no defect behind it |

Every input verified clean and the output was still wrong, because **the foot was faithfully
executing an instruction handed to it from four membranes up.** One backtrace step found what six
forward investigations walked past: `aBlueWorld` mass → `g = 7.076` → Froude → comfortable speed
falls 15% → the model selects the *slow* condition **from a dataset recorded on Earth**. The −49°
toe-off it could not accommodate is an Earth push-off, worn by a body in 0.72 g.

    WHEN EVERY INPUT VERIFIES AND THE OUTPUT IS STILL WRONG, STOP INTERROGATING THE MEMBRANE.
    Walk UP. Ask what it was handed, and whether that was true where it now stands.

The project already had the shape of this and had not applied it to numbers: `core/why.py` describes
the reverse question (*"this simtest was bogus, WHAT DID IT CONVICT?"*) and `story.py path` prints a
serial forward. Missing is the same walk backward over VALUES — given a suspect number, enumerate
the ancestors it depends on and check each one's regime.

---

## RULE 19 — ONE QUANTITY, ONE LANDMARK

Two measurements of "the same" body part, taken to different landmarks, are different numbers. They
are also dimensionally identical, so no fold, bond or regime check can tell them apart, and they
will sit in one model disagreeing until something downstream cannot close.

Found the same day, in one leg:

    0.5123   thigh + shank + ankle_drop     ANSUR II, TROCHANTERION
    0.5300   LEG_FRAC                       Dempster, hip JOINT
    0.5243   leg_over_stature()             the 246 adults the gait curves come from

**3.11 cm apart, in a leg that has one length.** The trochanterion is a bump you can feel on the
femur; the hip joint centre sits medial and superior to it. Ingesting ANSUR's segments raw put a
third length into a model that already had two, so every foot number computed after it stood on a
skeleton 3 cm shorter than the leg it hung from.

**The fix is not to pick one source — it is to give each source what it actually measured.** ANSUR
measured 6,068 people and is authoritative for the PROPORTIONS. `leg_over_stature()` measured the
same 246 the walk curves came from and is authoritative for the TOTAL. Scaling the splits onto that
total keeps both and invents neither. The vault moved 2.36% → 2.43% against a literature ~2.5%
unprompted: the pelvis path had been computed on a pendulum that disagreed with its own bones.

---

## RULE 20 — THE INSTRUMENT MUST MOVE WITH THE MEMBRANE, AND IT MUST NOT KEEP ITS OWN COPY

A witness that TYPES any part of the body's geometry is a second, private copy of that geometry,
and it drifts the moment the real one is measured. Then it grades the new body against the old one
and reports a defect that is entirely its own.

This happened **four times in a single day**, which is what promotes it from an incident to a rule:

| the witness held | what happened |
|---|---|
| `forefoot_lever_frac` default `0.152` | three membranes took the stale toe-tip value and were convicted of a 5.39% penetration and a travelling contact plane that were the instrument's — *predicted verbatim by the comment sitting directly above the bug* |
| `thigh, shank = 0.245, 0.246` | the moment the body's segments were measured, it graded the new skeleton against Dempster and reported 1.78% penetration |
| the flat two-point foot | after the roll-over went in, it reported 0.55% penetration and a sled |
| the rocker, ungated | applied in swing where it was never measured, hiding a real toe penetration behind a shallower fictitious one |

**THE RULE: a witness reads PUBLISHED numbers and refuses when they are absent.** Not a default — a
refusal. A fallback is an assumption wearing a hat, and the path is the membrane chain, so the
lookup walks UP it. A body that publishes a gait cycle must publish the skeleton it was drawn with,
or the cycle cannot be judged.

And its converse, which is the harder half: **a witness may not import the membrane it judges.**
That is one system measuring itself — a monad. Restate the law from the membrane's published
account and drive it entirely from published values.

---

## RULE 21 — IN A GROWN WORLD, AN AUTHORED PHENOTYPE IS THE DEFECT

The last thing 2026-08-01 established, and it reframes the other three. This engine grows things: a
seed, laws, and numbers trained against measurable targets. **The walker was the one thing still
being AUTHORED** — its gait read out of a table of 246 Earth-dwelling adults — while everything
around it was derived.

That is why no amount of geometry could seat it. A −49° toe-off is not a bug; it is an **Earth
phenotype in a 0.72 g world**, and correcting the foot to accommodate it only moves the mismatch
somewhere new. The body has to be grown where it lives.

**WHICH TURNS THE MEASURED DATASET FROM THE ANSWER INTO THE CONTROL, and that is the good part.**
Evolve a body at 9.80665 and it must reproduce the dataset's cadence, duty factor, double support
and MTC — none of which it was fitted to. That is the proof the engine works. Only then set g to
the world's own value and let it run again. The precedent is already in this repo: the Froude law
predicted the Moon's walk→run transition at 0.83 m/s, *which is why Apollo astronauts bunny-hopped*
— a fact nobody put in.

    THE WITNESS IS NOT A TEST. IT IS THE FITNESS FUNCTION.

`gait_witness` already refuses a buried foot, a travelling contact plane, a duty factor outside the
walk band, a wrong vault. Those were never acceptance criteria for an authored gait — they are
selection pressure for a grown one. Which is also why the geometry work still matters: **you cannot
select for a gait you cannot measure honestly**, and that morning the witness was passing a foot
buried in the floor.

---

## RULE 22 — THE SERIAL IS THE PLACE IN TIME, NOT THE PLACE IN THE TREE

The operator's, and it fixes something that costs order every time it is missing. A membrane's
address is its PATH, and a path encodes **containment** — what is inside what. The story is told in
**time**. Those agree all the way down a spine and stop agreeing the instant the tree branches:
`theStar` and `thePlanets` are siblings in the tree and are not simultaneous, and until 2026-08-01
nothing written anywhere said which came first.

    A HIERARCHY SAYS WHAT CONTAINS WHAT. A TIMELINE SAYS WHAT FOLLOWS WHAT.
    The fourth dimension is the second one, and it is not free with the first.

**DERIVE THE EPOCH, DO NOT DECLARE IT.** Every membrane already publishes `duration_s` — its own
span — and those are real: `theCooling`'s 1.199e13 s *is* the 380,000 years to recombination.
Summing down the path from the seed gives the seed's own seconds at which each process completes:

    t_end(m) = t_end(parent) + duration_s(m)

Monotonic down every branch by construction, because a child cannot finish before the parent it
lives inside. Nothing chosen, nothing invented. `python story/timeline.py --write`.

**AND THE STORY CARRIES THE SAME NUMBER.** Both `numbers.json` and `story.md` are stamped, because
otherwise there are two orderings and they disagree — and the human-readable one loses silently.
A story that does not know its own place in the story is decoration.

**IT FINDS WHAT IS OUT OF ORDER, WHICH IS THE POINT.** On its first run: `theHumanClock` landed at
3 seconds after the seed, sorting before recombination — the first membrane whose containment and
chronology genuinely disagree, sitting under `theClock` because it *is* a clock while what it
describes happens thirteen billion years later. And nine hand-written chapter numbers disagreed
with the derived order, **two pairs of them colliding** (`theSolarSystem`/`theStar` both claiming
chapter 6). Those were paragraph counts that drifted every time a membrane was inserted between two
others, with nothing to notice, **because a number in prose has no consumer**.

State the limit where the tool can see it: this sums process spans, not the waiting between them,
so the epoch is exact as an ORDERING and approximate as an absolute time.

---

## RULE 23 — CHECK THE GENERATOR BEFORE YOU BELIEVE THE WITNESS

A witness that reads published numbers **cannot see a generator that failed to publish**. It walks
the last good file on disk and reports everything green.

This cost twice in one afternoon. `story/grow.py` was dying on a retired key while `chain_witness`
reported *"42 working, 0 stubs, 0 broken"* — because the witness was reading `numbers.json` files
written before the change. The second time, `grow` was piped to `/dev/null` and the failure was
invisible entirely.

    THE ORDER IS: generator exits clean -> witness passes -> THEN the result is believed.
    Never discard the generator's output. A green witness over stale data is worse than a
    red one, because it is quiet.

---

## RULE 24 — AN INSTRUMENT NEEDS AN INSTRUMENT

`tools/methodology_gate.py` was written to catch the failures of forty-two membranes and made
**four of its own inside a day**, every one of which would have sent someone after an innocent
membrane:

| the gate's bug | what it did |
|---|---|
| required a `FREE` dict of a **seed** | accused 20 innocent membranes; a seed chooses nothing, so there is nothing to declare |
| grepped for `measured\|literature\|predict` | failed a story citing **Carter 1968, g = 2** out of the Kerr–Newman metric |
| keyed duplicates on `round(v, 12)` | sent `2.29e-35` **and** `5.39e-44` both to `0.0`, so at the top of the tree, where everything is Planck-scale, it **invented** pairs |
| filtered identities by jumping a dial to a `FREE` bound | dropped a true identity, then in another form invented pairs on membranes whose `derive` degenerates off-default |

The pattern: **a check applied outside the shape it was written for** — the same species as every
membrane defect in this document. There is no exemption for tools.

    Any column a gate reports must be checkable BY HAND on one known case before it is trusted
    across forty. Run the slider on one membrane yourself; if the tool disagrees with you, the
    tool is wrong until proven otherwise.

---

## RULE 25 — A TRANSPORTED NUMBER IS NOT A DERIVED NUMBER, AND THE GATE THAT DEMANDED ONE COULD ONLY PASS ON EARTH

Found 2026-08-02, in the self-critique of the trainer rewrite that rule 1 forced. It is rule 1's
own failure mode one level in, committed by the tool written to enforce rule 1.

**There are THREE grades of number, not two,** and only the first two were named:

    1.2850 m/s   an EARTH measurement, used raw           <- what rule 1 caught
    1.0915 m/s   the same measurement, Froude-TRANSPORTED <- what the gate demanded
    0.9924 m/s   what theHuman DERIVES for itself          <- what the membrane published all along

Transport is a real improvement and it is still second-best. `theHuman` derives its comfortable
speed from a Froude law and its cadence from the leg as a compound pendulum with a measured swing
drive; both were sitting in `numbers.json`. **A transported number carries the reference world's
anatomy inside it. A derived one does not.**

**AND THE CHECK WAS A TAUTOLOGY.** `training_gate.py` computed

    want_T = stride_s / scale        then asked whether  |stride_s - want_T| / want_T > TOL

— the input against a transform of **itself**. That can only pass when `scale == 1`, which is to
say **on Earth**. The gate written to refuse Earth numbers was unpassable on every world except
Earth, and it refused `theHuman`'s correct 1.1730 s while demanding a 1.3809 s no membrane
publishes. It is rule 20 exactly — *the instrument kept its own private copy of the body* — and
rule 24 exactly — *an instrument needs an instrument*.

**IT PUBLISHED A WRONG NUMBER FOR A DAY, INTO SIX DOCUMENTS.** Rule 1 claimed the gait was clocked
*"18% too fast"*. Against the body's own derived stride the error is **3.9%**. The 18% was the
tautology's output, and the real defect in that sweep was **entirely in the speed** (1.29x), not in
the clock. A number with no consumer drifts; a wrong number *with* six consumers propagates.

    THE TEST: ask what your check compares against. If the answer is "a transform of the thing
    being checked", it is a tautology, and it will pass or fail as a property of the transform
    rather than of the subject. The reference must come from OUTSIDE -- which is rule 14 again,
    in the time domain instead of the pixel domain.

**Enforced:** the stride check now reads `2 x theHuman.step_time_s` and **refuses when it is
absent** rather than falling back — because a gate inventing the cadence it polices is the whole
disease. `python tools/training_gate.py --target-speed 0.9924 --stride-s 1.1730` passes; the raw
Earth pair and the transported pair are both refused.

---

## RULE 26 — A CLAIM WITHOUT A FALSIFIER IS A DESCRIPTION, AND A DESCRIPTION CANNOT BE WRONG

Named 2026-08-02, after a day in which FOUR confident diagnoses were stated and then reversed:
*the plant is too slow* (the muscles were 3.2x faster than the fall) · *the CoM starts outside the
base* (it was 4.8 mm inside; the plot's origin was the heel midpoint) · *the stance selection is
the defect* (the CoM was inside all three) · *the body ends at the pelvis* (47 kg of spine, torso,
neck and head, invisible to a traversal that walked downward from the pelvis).

**Every one of them was stated without naming what would refute it.** That is the common cause, and
it is not carelessness -- each was a reasonable reading of a real measurement. The failure is
structural:

    IF YOU CANNOT SAY IN ADVANCE WHAT WOULD PROVE YOU WRONG, YOU WILL NOT NOTICE WHEN IT HAPPENS.
    You will find a reason the result still fits, and every reason will be individually reasonable.

So a claim is not admissible until it carries three parts: a STATEMENT someone could disagree with,
a PREDICTION not yet measured, and a FALSIFIER named BEFORE the run. Rule 0, and it sits above
rule 1 because you cannot derive your way to something you have not claimed.

**AND THE CONVERSE IS THE HALF THAT GETS FORGOTTEN: a confirmed prediction that COULD NOT have
failed is worth nothing.** Before believing a pass, check the falsifier was reachable. `GROUND ->
FOOT` closing at +0.7% was real evidence because the contact solver and the integrator could have
disagreed. `mean(hold)` improving while every episode ended in 0.42 s was not, because a shorter
window cannot exceed a max-based bar.

---

## RULE 27 — THE INTERFACE MEMBRANE IS DERIVED FIRST

Operator ruling, 2026-08-09, after the foot-geometry audit (evidence node: `docs/JOINT_ATLAS.md`,
FOOT GEOMETRY AUDIT 2026-08-09). Twelve VERDICTs (12-23) measured controller diseases that were
geometry diseases: the body had been derived top-down from stature fractions -- hip height, knee
height, ankle height -- and the foot, the one membrane that touches the terrain, was bolted on
last as a line of offsets. The measured cost: a support polygon 1.8 cm wide against the project's
own research datums of 5-7 cm, a metatarsal base born 1.8 cm BELOW the floor plane, an inverted
arch that never touches the keystone joint the data already carried, and a statue that twelve
control-side membranes could not melt.

**Whatever touches the parent membrane is where derivation starts, because the parent's physics
sets the constraints.** The floor's spring law, the friction cone, the load path -- these are
properties of the terrain, and the foot must be derived to meet them. The foot is not a body part
with contacts attached; it is a contact patch with a body attached. The same holds everywhere:
the hand is built palm-first when grasping arrives, not arm-first.

Operational form:

    1. derive the contact patch from the PARENT membrane's physics (its force law, its
       friction, its geometry),
    2. grow the structure upward from the patch -- bone lengths, joint centers, arches --
       so that every point has a load path to the parent,
    3. nothing may be born buried: a point below its parent's surface at birth is a
       derivation error, not a contact-solver problem.

Rule 18 says debug UP the chain; this rule says BUILD up from the connection. They are the same
law read in the two directions of time: the interface is where the physics enters, in debugging
and in growth alike.

---

## THE REMAKE PROCEDURE — how to go back over everything without reading it all

Written down because "go back over everything" is where a session evaporates, and because the
context that starts it will not be the context that finishes it.

1. **PROGRAM THE GATE FIRST.** Forty-two careful reads, each hoping to notice what twenty-three
   rules say to look for, is the forward-debugging trap at tree scale. `tools/methodology_gate.py`
   scores every membrane on form / derives / emits / free / units / one-name / typed / predicts.
   The reading then goes only where it points.
2. **WORK IN TIMELINE ORDER** (`python story/timeline.py`), not in the order things look broken.
   Rule 18: a defect at the root poisons everything below it, and the symptom surfaces far from
   where it entered.
3. **ONE MEMBRANE AT A TIME, AND EACH RENAME TRAVELS WITH ITS CONSUMERS IN ONE COMMIT.** Grep for
   `parent["<key>"]` before retiring anything. A rename that lands without its readers breaks the
   tree eight membranes downstream, and the witness will not tell you.
4. **AFTER EVERY CHANGE:** `story/grow.py` exits clean → `chain_witness` → `folding.py audit` →
   the gate. In that order, every time (rule 23).
5. **WHEN A MEMBRANE FAILS A COLUMN, SUSPECT THE COLUMN ONCE** before suspecting the membrane
   (rule 24). Two of `theZero`'s four failures were the gate's.
6. **A SYSTEMATIC PATTERN IS ONE DECISION, NOT N EDITS.** 45 flagged pairs across the tree were a
   single choice — every membrane publishing its size under both the contract name and its own
   physics name. Count the pattern before fixing instances.

---

## THE CHECKLIST

1. **Derive the target before you train** — if a variant answers "which number is best", stop.
2. What does the human **wait for**? Measure that, not a proxy.
3. Benchmark in the **final state** (full drive, real workload, real contention).
4. Sanity-check every number against a **physical limit**.
5. Watch **temperature, power, and per-device activity** — sample CPU and GPU together.
6. **Redirect stderr to a file** before diagnosing anything.
7. **One variable at a time**; bake in each win before the next test.
8. **Write down what failed**, with the number.
9. Do the arithmetic, then **verify its assumptions**.
10. **Grep the tool's source** for env vars and flags.
11. When the operator says it looks wrong — **go measure it.**
12. Push a **known subject** through the whole instrument. No control, no measurement.
13. Count how many **pixels/samples** the effect occupies before believing a null.
14. Never threshold on a **quantile of the thing you are measuring** — use an outside reference.
15. Ask whether the **data carries an artifact of how it was built**, not only whether the probe is sound.
16. When joining a codebook, **read their formula** — a shared name is a coincidence until checked.
17. **Derive the shape, let physics set the level** — and publish it when the two disagree.
18. **Backtrace.** When every input verifies and the output is still wrong, stop interrogating the
    membrane and walk UP the chain — forward debugging finds where an error became visible, not
    where it entered.
19. **One quantity, one landmark.** Two measurements of the same part to different landmarks are
    different numbers, dimensionally identical, and invisible to every check.
20. **The instrument must move with the membrane** — read published numbers, refuse when they are
    absent, and never import the thing you judge.
21. **In a grown world, an authored phenotype is the defect.** The witness is the fitness function,
    and the measured dataset is the CONTROL, not the answer.
22. **The serial is the place in TIME, not in the tree.** Containment and chronology part company
    the moment the tree branches; derive the epoch from published durations and stamp the STORY
    with it too, or the two orderings disagree and the readable one loses silently.
23. **Check the generator before you believe the witness.** A witness reading published numbers
    cannot see a generator that failed to publish; it reads the last good file and reports green.
24. **An instrument needs an instrument.** The gate written to catch 42 membranes made four of its
    own bugs in a day. Check any column by hand on one known case before trusting it across forty.
25. **A transported number is not a derived number.** Three grades, not two: an Earth measurement
    raw, the same one Froude-transported, and the one the membrane DERIVED. Transport still carries
    the reference world's anatomy. And ask what your check compares against — `training_gate`
    compared a stride to a transform of itself, a tautology that could only pass on Earth, and it
    published "18% too fast" into six documents when the real error was 3.9%.
26. **A claim without a falsifier is a description, and a description cannot be wrong.** State the
    theory, the prediction and what would kill it BEFORE the run -- four confident diagnoses were
    reversed in one day and not one had named its own refutation. And check the falsifier was
    REACHABLE before believing a pass.
