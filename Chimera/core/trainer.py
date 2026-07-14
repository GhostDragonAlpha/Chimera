"""trainer — train ANY feature. The LLM writes the constraints; it never turns the crank.

THE DIVISION OF LABOUR (the human, 2026-07-14: "It'll be up to the LLM to generate
the constraints based on the scenario"):

    SCENARIO  (intent, in words)
        |
      [LLM]   writes the CONSTRAINTS  ->  docs/objectives/<feature>.json
        |
    OBJECTIVE (declarative, numeric, reviewable, diffable, FALSIFIABLE)
        |
    [TRAINER] 10^4-10^5 evaluations/sec. No LLM anywhere in this loop.
        |
    WINNER + PINNED CONSTRAINTS
        |
      [LLM]   reads the exploits, REPAIRS the objective
        `-------------------------------------------^

The LLM sits at the TOP and at the BOTTOM. Never in the middle.

THE THREE-PART SPLIT
--------------------
  DOMAIN      (code)  seed / mutate / measure  ->  a dict of NUMBERS about an artifact
  OBJECTIVE   (LLM)   numbers -> a score.  "what good means", stated once.
  TRAINER     (this)  generic. It does not know what a creature or an economy is.

A domain reports FACTS. An objective says which facts are GOOD. Keeping those apart
is what lets one trainer drive every feature in the game, and what lets the LLM
change the definition of "good" without touching a line of simulation code.

WHY THIS WORKS AT ALL — and where it stops
------------------------------------------
    morphology     1.5 ms/eval   ->  35,000 evals/sec (measured)
    balance        1-10 ms       ->   5,000-20,000/sec
    level layout   10-50 ms      ->   ~2,000/sec
    locomotion     100-500 ms    ->     ~100/sec
    C++ SYSTEMS    ~6 MINUTES    ->       0.002/sec   <-- SEVEN ORDERS OF MAGNITUDE

You can train DATA. You cannot train CODE. So push the game out of code and into
data — which this studio already did: the DSL *is* the genome.

THE EXPLOIT IS THE PRODUCT
--------------------------
A degenerate winner is not a failure. It is the optimiser AUDITING YOUR SPEC at
35 kHz and finding the hole you would have defended in code review. (2026-07-14:
the first creature run produced a boulder on a pole in three seconds.) So this
module reports PINNED constraints — the walls the winner is pressed against — because
that is exactly where the next exploit lives, and exactly what the LLM must repair.
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import multiprocessing as mp
import random
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBJ_DIR = ROOT / "docs" / "objectives"


# --- the objective: what the LLM writes --------------------------------------
#
#   {"measure": "credits_per_hour", "kind": "band", "min": 2e4, "max": 1.2e5,
#    "weight": 2.0, "why": "a grind below; the ship ladder collapses above"}
#
# kinds:  band {min,max} · at_most {max} · at_least {min} · target {value}
#         maximize {ref} · minimize {ref}
# hard:   true -> a GATE. Violating it scores ZERO, and the gate is named in the report.

_KINDS = {"band", "at_most", "at_least", "target", "maximize", "minimize"}


def _satisfy(c: dict, x: float) -> float:
    """How well measurement x meets constraint c. 0..1, and SMOOTH — a cliff gives
    the optimiser no signal to climb, so a violated constraint must still say which
    direction is less wrong."""
    k = c["kind"]

    def soft(dist: float, scale: float) -> float:
        scale = abs(scale) or 1.0
        return 1.0 / (1.0 + (dist / scale) ** 2)

    if k == "band":
        lo, hi = float(c["min"]), float(c["max"])
        if lo <= x <= hi:
            return 1.0
        span = (hi - lo) * 0.5 or 1.0
        return soft(lo - x if x < lo else x - hi, span)
    if k == "at_most":
        hi = float(c["max"])
        return 1.0 if x <= hi else soft(x - hi, abs(hi) * 0.5 or 1.0)
    if k == "at_least":
        lo = float(c["min"])
        return 1.0 if x >= lo else soft(lo - x, abs(lo) * 0.5 or 1.0)
    if k == "target":
        v = float(c["value"])
        return soft(abs(x - v), float(c.get("tol", abs(v) * 0.1 or 1.0)))
    if k == "maximize":
        # NEVER SATURATE. This used to be min(1.0, x/ref) — which CLAMPS, so the moment
        # x reached `ref` the gradient died and the optimiser stopped. That is the exact
        # SATISFICER trap I documented in TRAINING_PROTOCOL.md §3 and then rebuilt one
        # layer down: a `maximize` that saturates is a BAND WEARING A MAXIMIZE'S CLOTHES.
        # (Observed 2026-07-14: the brain hit 1.0000 at generation 100 and the remaining
        # 400 generations — 80,000 evaluations — changed nothing.)
        #
        # x/(x+ref) climbs forever: 0.5 at ref, 0.67 at 2*ref, 0.91 at 10*ref, and never
        # quite reaches 1. There is always somewhere left to go.
        ref = abs(float(c.get("ref", 1.0))) or 1.0
        x = max(0.0, x)
        return x / (x + ref)
    if k == "minimize":
        ref = abs(float(c.get("ref", 1.0))) or 1.0
        return ref / (ref + max(0.0, x))       # mirror image; also never saturates
    raise ValueError(f"unknown constraint kind: {k}")


class Objective:
    """A declarative spec. The LLM's whole output surface."""

    def __init__(self, spec: dict):
        self.name = spec.get("name", "unnamed")
        self.scenario = spec.get("scenario", "")
        self.constraints = spec["constraints"]
        for c in self.constraints:
            if c["kind"] not in _KINDS:
                raise ValueError(f"unknown kind {c['kind']!r}; expected one of {_KINDS}")

    @staticmethod
    def load(path) -> "Objective":
        return Objective(json.loads(Path(path).read_text(encoding="utf-8")))

    def score(self, m: dict) -> tuple:
        """(score, per-constraint detail). Weighted GEOMETRIC mean: one zero kills
        the whole body, which is the correct semantics for "all of these matter"."""
        if not m:
            return 0.0, []
        detail, lw, ls = [], 0.0, 0.0
        for c in self.constraints:
            x = m.get(c["measure"])
            if x is None:
                continue
            s = _satisfy(c, float(x))
            hard = bool(c.get("hard"))
            detail.append({"measure": c["measure"], "x": x, "sat": round(s, 3),
                           "hard": hard, "kind": c["kind"]})
            if hard and s < 1.0:
                return 0.0, detail          # a GATE. It failed. No partial credit.
            w = float(c.get("weight", 1.0))
            lw += w
            ls += w * math.log(max(s, 1e-6))
        if lw == 0.0:
            return 0.0, detail
        return math.exp(ls / lw), detail

    def pinned(self, m: dict, tol: float = 0.06) -> list:
        """Constraints the winner is PRESSED AGAINST. This is the exploit report:
        wherever the optimiser is riding a wall, it is extracting everything that
        wall allows — and that is where your spec is load-bearing, and where the
        next lollipop is hiding."""
        out = []
        for c in self.constraints:
            x = m.get(c["measure"])
            if x is None:
                continue
            x = float(x)
            for key, bound in (("max", c.get("max")), ("min", c.get("min"))):
                if bound is None:
                    continue
                b = float(bound)
                scale = abs(b) or 1.0
                if abs(x - b) / scale <= tol:
                    out.append(f"{c['measure']} = {x:,.4g} is riding its {key} "
                               f"({b:,.4g})")
        return out


# --- the domain: what code provides ------------------------------------------
#
# Any module exposing three functions is trainable. It does NOT know what "good" is.
#
#     seed()             -> genome (a plain JSON-able dict)
#     mutate(g, rng)     -> genome
#     measure(g)         -> {name: number}      FACTS. Never opinions.

_DOMAIN = None       # set per worker process


def _init(mod: str):
    global _DOMAIN
    _DOMAIN = importlib.import_module(mod)


def _eval(job: tuple) -> tuple:
    g, spec = job
    try:
        m = _DOMAIN.measure(g)
    except Exception:
        return 0.0, {}, []
    sc, detail = Objective(spec).score(m)
    return sc, m, detail


# --- the optimiser (a GA: no gradient exists through a grammar or a market) ----

def train(domain: str, obj: Objective, pop: int, gens: int, seed: int,
          workers: int, log=print) -> dict:
    """Two evaluation backends, chosen by what the domain offers.

    CPU:  `measure(g)` one genome at a time, fanned out over a process Pool. Right for
          anything whose sim is small, branchy and sequential — which is most physics.
    GPU:  `measure_batch(genomes)` — the WHOLE POPULATION in one call. A GPU is a
          throughput machine: the parallelism it wants is not INSIDE one creature (20
          links is nothing) but ACROSS thousands of them, batched into a single kernel.
          A domain that exposes measure_batch gets it, and the Pool is not used at all.
    """
    mod = importlib.import_module(domain)
    batched = hasattr(mod, "measure_batch")
    rng = random.Random(seed)
    spec = {"name": obj.name, "scenario": obj.scenario, "constraints": obj.constraints}

    g0 = mod.seed()
    population = [g0] + [mod.mutate(g0, rng) for _ in range(pop - 1)]
    n_elite = max(1, pop // 10)
    best, best_score, best_m, best_d, evals = g0, -1.0, {}, [], 0
    t0 = time.time()

    poolp = None if batched else mp.Pool(workers, initializer=_init,
                                         initargs=(domain,))
    if batched:
        log(f"  backend: GPU BATCH ({mod.__name__}.measure_batch) — "
            f"{pop} creatures per kernel\n")
    try:
        for gen in range(gens):
            if batched:
                ms = mod.measure_batch(population)          # the whole population, one kernel
                res = [(sc, m, det) for m, (sc, det)
                       in zip(ms, (obj.score(m) for m in ms))]
            else:
                res = poolp.map(_eval, [(g, spec) for g in population],
                                chunksize=max(1, pop // (workers * 4)))
            evals += len(population)

            ranked = sorted(range(pop), key=lambda i: res[i][0], reverse=True)
            top = ranked[0]
            if res[top][0] > best_score:
                best_score, best, best_m, best_d = (res[top][0], population[top],
                                                    res[top][1], res[top][2])
            if gen % max(1, gens // 10) == 0 or gen == gens - 1:
                fails = [d["measure"] for d in res[top][2]
                         if d["hard"] and d["sat"] < 1.0]
                log(f"  gen {gen:>4}  best {best_score:.4f}"
                    + (f"   GATE FAILED: {fails}" if fails else ""))

            nxt = [population[i] for i in ranked[:n_elite]]
            while len(nxt) < pop:
                a, b = rng.randrange(pop), rng.randrange(pop)
                win = population[a] if res[a][0] >= res[b][0] else population[b]
                nxt.append(mod.mutate(win, rng))
            population = nxt
    finally:
        if poolp is not None:
            poolp.close()
            poolp.join()

    dt = time.time() - t0
    return {"genome": best, "score": best_score, "measures": best_m,
            "detail": best_d, "pinned": obj.pinned(best_m),
            "evals": evals, "secs": dt, "rate": evals / max(dt, 1e-9)}


def _main() -> int:
    ap = argparse.ArgumentParser(
        prog="python -m core.trainer",
        description="Train any feature. The LLM writes the constraints; "
                    "the optimiser turns the crank.")
    ap.add_argument("--domain", required=True,
                    help="module with seed()/mutate()/measure(), "
                         "e.g. core.trainables.economy")
    ap.add_argument("--objective", required=True, help="the LLM-authored constraint spec")
    ap.add_argument("--pop", type=int, default=400)
    ap.add_argument("--gens", type=int, default=300)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--workers", type=int, default=max(1, mp.cpu_count() - 2))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    obj = Objective.load(a.objective)
    print(f"OBJECTIVE  {obj.name}")
    print(f"  scenario: {obj.scenario}")
    print(f"  {len(obj.constraints)} constraints, "
          f"{sum(1 for c in obj.constraints if c.get('hard'))} of them HARD gates")
    print(f"DOMAIN     {a.domain}")
    print(f"  {a.pop} x {a.gens} = {a.pop*a.gens:,} evaluations "
          f"on {a.workers} workers\n")

    r = train(a.domain, obj, a.pop, a.gens, a.seed, a.workers)

    print(f"\n{r['evals']:,} evaluations in {r['secs']:.1f}s "
          f"= {r['rate']:,.0f} evals/sec")
    print(f"best score {r['score']:.4f}\n")
    print("  MEASURED                              constraint      satisfied")
    for d in r["detail"]:
        gate = " HARD" if d["hard"] else "     "
        print(f"    {d['measure']:<32} {d['x']:>12,.4g}  {d['kind']:<9}{gate}"
              f"  {d['sat']:.2f}")

    if r["pinned"]:
        print(f"\n  PINNED — the winner is riding these walls. This is where the")
        print(f"  next exploit lives, and what the LLM must go and repair:")
        for p in r["pinned"]:
            print(f"    ! {p}")
    else:
        print("\n  nothing pinned — the winner is not riding any wall.")

    out = Path(a.out or (OBJ_DIR / f"{obj.name}.trained.json"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"objective": obj.name, "score": r["score"],
                               "measures": r["measures"], "genome": r["genome"]},
                              indent=2), encoding="utf-8")
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
