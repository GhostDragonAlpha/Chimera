"""Integrated training loop with automatic model audit.

Every training run:
1. Trains the domain (seed → mutate → measure → select)
2. Audits the model (detects stuck metrics)
3. Reports bugs (tells you what to fix, not just scores)
4. Decodes the best genome (produces game artifact)

Usage: python -m core.train_loop erisaid_mirror
"""

import importlib, inspect, json, random, sys, time
from pathlib import Path
from core.model_auditor import audit_run


class DomainRefusal(Exception):
    """The spine refuses to train a domain — with a named cause.

    work.data.trainer_spine_repair_20260917: a domain that violates the
    documented protocol used to surface as a bare TypeError from the call site
    (e.g. seed() called as seed(rng)). That is an internal crash, not a
    verdict. The spine refuses BEFORE training and says exactly what is wrong.
    """

    def __init__(self, code: str, detail: str = ""):
        self.code, self.detail = code, str(detail)
        super().__init__(f"{code}: {detail}" if detail else code)


def _require_protocol(domain, domain_name: str) -> None:
    """Refuse honestly unless the domain speaks the documented protocol
    (trainer.py's domain section): seed(rng) -> genome,
    mutate(genome, rng) -> genome, measure(genome) -> dict of numbers.
    Optional trailing parameters with defaults are fine. A MISSING function is
    also a protocol violation (e.g. a GPU-flavored domain that exposes only
    measure_batch cannot run through this CPU spine) — refused, never an
    AttributeError from the call site."""
    for attr, call, what in (("seed", (None,), "seed(rng)"),
                             ("mutate", ({}, None), "mutate(genome, rng)"),
                             ("measure", ({},), "measure(genome)")):
        func = getattr(domain, attr, None)
        if not callable(func):
            raise DomainRefusal(
                "domain_protocol_violation",
                f"{domain_name} does not define a callable {attr}(); the "
                f"documented protocol requires {what}. The spine refuses "
                f"instead of crashing on the call.")
        try:
            inspect.signature(func).bind(*call)
        except TypeError as exc:
            raise DomainRefusal(
                "domain_protocol_violation",
                f"{domain_name}.{what} does not accept the documented protocol "
                f"({exc}); the spine refuses instead of crashing on the call.") from exc


def train_and_audit(domain_name: str, pop: int = 40, gens: int = 20):
    """Train a domain and audit the model."""
    domain = importlib.import_module(f"core.trainables.{domain_name}")
    _require_protocol(domain, domain_name)

    t0 = time.time()
    rng = random.Random(42)
    population = [domain.seed(rng) for _ in range(pop)]
    best_genome = None
    best_score = -float("inf")
    history = []

    for gen in range(gens):
        scored = [(domain.measure(g), g) for g in population]
        # Score: sum all numeric metrics
        scored_sorted = []
        for m, g in scored:
            numeric = [v for v in m.values() if isinstance(v, (int, float))]
            score = sum(numeric)
            scored_sorted.append((score, g, m))
        scored_sorted.sort(key=lambda x: x[0], reverse=True)

        top_score, top_g, top_m = scored_sorted[0]
        if top_score > best_score:
            best_score = top_score
            best_genome = top_g

        history.append({k: v for k, v in top_m.items() if isinstance(v, (int, float))})

        elite = [g for _, g, _ in scored_sorted[:max(2, pop // 5)]]
        population = [domain.mutate(rng.choice(elite), rng) for _ in range(pop)]

    elapsed = time.time() - t0

    # Audit
    audit = audit_run(history, gens)
    final_m = domain.measure(best_genome)

    return {
        "domain": domain_name,
        "generations": gens,
        "population": pop,
        "time_s": round(elapsed, 1),
        "evals_per_sec": round((pop * gens) / max(0.001, elapsed)),
        "best_score": round(best_score, 3),
        "best_genome": best_genome,
        "final_measurements": {k: v for k, v in final_m.items() if isinstance(v, (int, float))},
        "genome_summary": final_m.get("genome_summary", {}),
        "audit": {
            "stuck_metrics": audit["stuck_metrics"],
            "stuck_rate": round(audit["stuck_rate"], 2),
            "recommendation": audit["recommendation"],
            "stuck": audit["stuck"][:5],
        },
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m core.train_loop <domain_name>")
        domains = [p.stem for p in Path("core/trainables").glob("*.py") if not p.stem.startswith("_")]
        print(f"Available domains: {', '.join(domains)}")
        sys.exit(1)

    domain = sys.argv[1]
    print(f"Training {domain}...")
    result = train_and_audit(domain)
    print(json.dumps(result, indent=2))
