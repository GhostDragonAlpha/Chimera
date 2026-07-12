# THE GAUNTLET — agent qualification crucible

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
