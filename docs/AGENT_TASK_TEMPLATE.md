# Agent task template

> Fill three placeholders — **`<DIRECTION>`**, **`<NAME>`**, and the one-line task —
> then paste the block into a fresh agent.
>
> Launch: `pi --provider lmstudio --model <the model LM Studio has resident>`

---

## The prompt

```
You are working on CHIMERA at E:\PythonChimera. Read docs/ONBOARDING.md — it is your
briefing. Then execute the task below.

WORKING DIRECTORY for all commands: E:\PythonChimera\Chimera
(in bash, use /e/PythonChimera/Chimera)

TASK — the <DIRECTION> direction of the six directions.
<ONE SENTENCE: what the player sees when they look that way, and what is missing.>

STEP 1 — DECODE IT WITH THE 40 QUESTIONS.
  python -m core.forty_questions generate <NAME>
Answer at least FIVE using the command, never by editing the JSON:
  python -m core.forty_questions answer <NAME> <id> "<answer>"

EVERY ANSWER MUST CONTAIN A NUMBER YOU MEASURED FROM THE THING YOU ARE BUILDING.
Not a default parameter. Not a count of functions in a module. Not a value read from
a config file. If you obtained it with inspect.signature(), len(SOME_DICT), or by
reading a docstring, IT DOES NOT COUNT — that is a fact about the code, not about
the artifact. A valid number comes from running the pipeline and measuring its
output: splat counts, extents, distributions, errors, timings.
If you cannot measure a question, LEAVE IT UNANSWERED. Unanswered is honest.

STEP 2 — BUILD IT from functions that already exist. Do not write new modules.
  core.membrane_shapes : sphere, plane, cylinder, box, dome, displace, clothe
  core.progeny         : ground_patch, ground_tile, landmark, lod, compose, ground,
                         load_genome, recombine, build_child, place, scatter, pose
  core.sections        : section_at, open_section, seam_check, neighbours
  core.render_world    : render_orbit
Materials: Chimera/docs/matter/recovered_genomes.json
Render to exactly: Saved/SplatEmit/<NAME>.png

>>> ESCAPE HATCH — READ THIS BEFORE BUILDING <<<
If the existing functions CANNOT do this task, STOP and report exactly which
function is missing and what it would need to do. Naming a missing capability is a
SUCCESSFUL outcome and I want it. Building something differently-shaped and calling
it the task is a FAILURE. If a function's docstring contradicts your use of it, that
is the signal — say so instead of proceeding.

STEP 3 — MEASURE THE IMAGE YOU MADE. Not the log. Run this and paste the output:
  python -c "
from PIL import Image; import numpy as np
a=np.asarray(Image.open('Saved/SplatEmit/<NAME>.png').convert('RGB')).astype(float)
nz=a.sum(2)>12
print('size', a.shape[1], 'x', a.shape[0])
print('non-black pixels', round(100*nz.mean(),1), '%')
print('mean RGB of content', np.round(a[nz].mean(0),1) if nz.any() else 'EMPTY')
print('distinct bright regions', int(((a.sum(2)>250).sum())>0))"
Then describe in two sentences what the image ACTUALLY shows, using those numbers.
If the content is under 5% of the frame or the mean RGB is not what the material
implies, say so — that is a finding, not a failure to hide.

ACCEPTANCE — done when BOTH exist, and not before:
  1. Chimera/Saved/SplatEmit/<NAME>.png       (nonzero, and measured in STEP 3)
  2. Chimera/docs/forty_questions/<NAME>.json (>= 5 answered VIA THE COMMAND)

FORBIDDEN:
  - No status document, summary, report, or NEXT_STEPS file. Writing about work is
    not doing work.
  - Do not ask me what to focus on. The task is above.
  - Do not hand-edit the 40Q JSON or its n_answered field.
  - Do not end your turn until both artifacts exist OR you have invoked the escape
    hatch with a specific missing function named.

REPORT: the five+ measured numbers and what each measures, the exact build command,
the STEP 3 output verbatim, and what the image shows.
```

---

## Why each clause exists

Every line below was added because an agent failed without it. Do not trim them; the
prompt is short because the failures were expensive.

| Clause | The failure it prevents |
|---|---|
| **No status document** | Given *"do not end your turn without writing a file"*, an agent wrote a 523-byte doc restating the onboarding back, never ran the command, and reported success. It satisfied the letter with the cheapest possible file. |
| **Do not ask what to focus on** | The first agent read the whole briefing correctly, then ended with *"What would you like to focus on?"* |
| **Measured FROM THE ARTIFACT** | Given *"a number obtained by running code"*, an agent used `inspect.signature()` and `len(SHAPES)`. Real numbers, wrong questions — it answered "at what resolution does the pattern emerge?" with the render window size, and "what breaks at the seam?" with a tile constant, for a sky that has no tiles. |
| **Answer via the command** | An agent hand-edited the JSON and set `n_answered: 5, depth_verdict: "explored"` itself, bypassing the DNA-graph recording the tool performs. |
| **ESCAPE HATCH** | The decisive one. An agent read `dome()`'s docstring — *"ground you can stand on"* — wrote *"for the sky, maybe a hemisphere or a sphere inverted?"* in its own reasoning, and used `dome` anyway, clothing a sky in rock. **With only two legal outcomes — produce the artifact or fail — producing a wrong artifact dominates.** Making "the toolkit is missing X" a winning outcome converts a silent wrong build into a bug report. |
| **STEP 3 as a paste-and-run command** | Told to *"look at the PNG"*, an agent reasoned *"or just describe based on the render output"* and did that. It reported the material as *"earthy brownish"* read from a JSON file; the render was grey-green. A programmatic measurement works even for agents that cannot view images, and `mean RGB` alone would have caught it. |

---

## The pattern behind all of them

Every acceptance condition written so far has been a **proxy**, and each time the agent
found the cheapest way to satisfy the proxy rather than do the work:

```
v1  "write a file"                        -> a status document
v2  "a number obtained by running code"   -> inspect.signature()
v3  "a number measured from the artifact" -> current
```

This is not misbehaviour. It is the same thing a trainer's degenerate winner does to a
badly-specified objective: **the agent is auditing the spec.** When a run fails, fix the
acceptance condition first and suspect the agent second — `docs/EXPERIMENTAL_METHOD.md`
rule 1, applied to tasking.

**Expect v4.** When one appears, add a row to the table above with the specific failure,
so the next person does not pay for it twice.
