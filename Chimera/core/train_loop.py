"""Integrated training loop with automatic model audit.

Every training run:
1. Trains the domain (seed → mutate → measure → select)
2. Audits the model (detects stuck metrics)
3. Reports bugs (tells you what to fix, not just scores)
4. Decodes the best genome (produces game artifact)

Usage: python -m core.train_loop erisaid_mirror
"""

import importlib, json, random, sys, time
from pathlib import Path
from core.model_auditor import audit_run


def train_and_audit(domain_name: str, pop: int = 40, gens: int = 20):
    """Train a domain and audit the model."""
    domain = importlib.import_module(f"core.trainables.{domain_name}")

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
