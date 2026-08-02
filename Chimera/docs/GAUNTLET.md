# THE GAUNTLET — agent qualification crucible

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
> **[docs/THE_LAW.md](../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 25 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> Commissioned by the human 2026-07-12: *"have the agent go through... a gauntlet...
> we want them to do all the rules of the studio. One complete pass may take the agent
> several turns... the agent sees that it must achieve a certain outcome before the next
> role can be attained, and the only way out of the tunnel is through an elaborate gate
> that allows for choices to be made based off of research decisions. The path... will be
> laid out — the agent will just have to make the connection themselves. Feed in as many
> agents of different types as you can... it may shine more in some areas than others...
> it writes down notes... artifact checkpoints."*

Implementation: `core/gauntlet.py`. Tests: `python core/test_gauntlet.py`.

## Why it exists

`--capable` was self-declared — any agent could wave the flag and claim the studio's
hardest lanes. The gauntlet makes capability **earned**: `task_board` refuses
`capable_only` claims from agents without the `journeyman` role. Heterogeneous agents
(different models, different strengths) each run the same stations; the per-station
score profile is the capability map used to route them where they shine.

## The rules of the crucible

1. **Outcomes, not effort.** Every station is verified MECHANICALLY against live state
   (DNA graph, task board, tunnel, filesystem). No LM judges anything. A bounce names
   the failed checks — never how to pass them.
2. **Connections laid out, never drawn.** Briefs name where the path runs
   (`core.preflight`, the graph, the board) but never the exact commands. Passing
   requires the agent to make the connections itself — that is the point.
3. **Several turns is fine.** Runs persist in `docs/gauntlet/runs/<agent>.json`;
   `enter` resumes, never restarts. Every attempt (including every beating) is recorded.
4. **Artifact checkpoints.** Stations demand written notes in `docs/gauntlet/<agent>/` —
   committed evidence of passage, cross-examined at submit time.
5. **The human outranks the machine.** `gauntlet grant --agent X --role journeyman
   --note "..."` — one sentence of fiat, recorded in the credential history.

## The seven stations

| # | Station | Artifact | Proves | Specialty tag (>=85) |
|---|---|---|---|---|
| 1 | ORIENTATION | orientation.md | can read live studio state (GPA, loop, board, pains) | — |
| 2 | THE SCRIBE | (graph node) | typed recording via helpers, token `gauntlet:<agent>` | — |
| 3 | THE SCHOLAR'S DESK | research.md | research writes the exam: real sources + numeric criteria | researcher |
| 4 | THE CARTOGRAPHER | graph.md | graph literacy: latest build to the minute, paired statuses | cartographer |
| 5 | THE GATEKEEPER'S DRILL | gates.md | failure autopsy: real failed build + gate + H-rule | — |
| 6 | THE TUNNEL RUN | tunnel_note.md | the single entry, end to end, on a seeded sandbox task | tunnel-runner |
| 7 | THE EXIT GATE | verdict.md | a defended choice among rehearsal's LIVE candidates | — |

Roles: passing stations 1–3 earns `initiate` mid-run; completing all seven earns
`journeyman` (+ specialty tags). Completion is recorded to the DNA graph as a
PhaseComplete node.

## Operating it

```powershell
python -m core.gauntlet enter  --agent <id>    # start or resume; prints the station brief
python -m core.gauntlet submit --agent <id>    # verify current station; advance or bounce
python -m core.gauntlet status --agent <id>    # where am I / scores / attempts
python -m core.gauntlet roster                 # every agent's roles + score profile
```

Feed agents in; read the roster; route accordingly. Extending the gauntlet = adding a
station dict (brief + mechanical verifier) to `STATIONS` — keep verifiers zero-LM and
cross-examined against live state, per the result-grader ethos.

---

# THE CURRICULUM — features go to school (K -> PhD)

> Second commission, same day: *"this gauntlet is gonna be like the entire education
> system from elementary school all the way up through PhD, but hyper-focused to game
> development... you should have hundreds of checkpoints... we have to think about how
> you conceptualize a feature from every angle of humanity... it'll also be like
> training an AI — if an AI was one feature, think of it like that."*

The gauntlet above qualifies PORTERS (agents). The Curriculum schools CARGO (features).
Implementation: `core/curriculum.py` (engine) + `docs/curriculum/curriculum.json`
(the authored curriculum — grow the JSON, never the engine). Tests:
`python core/test_curriculum.py`.

**The AI-training reading is literal:** a feature enrolls like a model entering
training; grade bands are curriculum-learning stages; every passed checkpoint is a
saved, evaluated state in its transcript (`docs/gauntlet/features/<slug>/`); the PhD
dissertation — with a falsifiable claim — is the final eval before deployment to
automated observation.

**Founding curriculum (69 checkpoints, 7 bands):**   <!-- counted from curriculum.json 2026-07-16; the doc said 54, 28% low -->

| Band | Question | Porter role | Sample checkpoints |
|---|---|---|---|
| kindergarten | Is it fun? | — | the toy test, the player's face, the second use |
| elementary | What is it? | — | noun+verb (H-21), player-visible truth (H-14), 3 prior games |
| middle | How does it feel? | — | first-10-seconds latency, readability vs regolith-grey, the diegetic no |
| high | How does it work? | — | governing curve with real numbers, 3 tuning knobs, cost/pay exchange |
| bachelor | How is it built? | initiate | generator-vs-manual decomposition, read-backs (H-22), foregrounded budgets, **online research w/ cached evidence** |
| master | How does it fit? | journeyman | vision bible, wordless narrative, **4-lens accessibility, culture/ethics, emotion, the body**, benchmark canon, coherence exam across its own transcript |
| phd | Prove it deserves to exist | journeyman | research exam (URL + cache), sleepwalker testimony (H-19), telemetry vs budget, dissertation with PROCEED/REFINE/PARK verdict + falsifiable claim, the Will |

- Checkpoints within a band pass in ANY order, by DIFFERENT agents — the transcript
  records who carried what (the shines-where profile across agent types).
- ONLINE RESEARCH IS A CHECKPOINT (ba.research.online, phd.evidence.research): a live
  URL must be cited AND its cached copy must exist on disk — retrieval leaves evidence.
- Toward "hundreds": board task `Curriculum Faculty` holds the authoring backlog
  (uncovered disciplines listed in its recipe); dream-loop-distilled H-rules should be
  promoted into checkpoints — the curriculum grows from the studio's own scars.

```powershell
python -m core.curriculum enroll --feature X          # matriculate
python -m core.curriculum status --feature X          # grade + remaining checkpoints
python -m core.curriculum brief  --feature X [--checkpoint id]
python -m core.curriculum submit --feature X --checkpoint id --agent <you>
python -m core.curriculum roster                      # the whole school
```
