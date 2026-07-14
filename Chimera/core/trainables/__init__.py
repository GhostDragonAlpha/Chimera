"""trainables — domains that core.trainer can optimise.

Each module exposes exactly three functions and NO opinion about what is good:

    seed()          -> genome (a plain JSON-able dict)
    mutate(g, rng)  -> genome
    measure(g)      -> {name: number}     FACTS ONLY.

"What good means" lives in docs/objectives/<feature>.json, written by the LLM.
Keeping the two apart is what lets one trainer drive every feature, and lets the
definition of good change without touching a line of simulation code.
"""
