"""Model auditor — detects when the trainer is telling us the model is wrong.

When a metric is stuck at floor/ceiling across N generations despite strong
selection pressure, it's not undertraining — it's a MODEL BUG. The physics
cannot produce that outcome. The fix is to change seed() or measure(), not
to train harder.

Applied universally: every domain inherits this audit automatically.
"""

from __future__ import annotations
import math


def audit_run(history: list[dict], generations: int, stuck_threshold: float = 0.01) -> dict:
    """Analyze a training run for stuck metrics.

    Args:
        history: List of {metric_name: value} dicts per generation (best genome)
        generations: Total generations run
        stuck_threshold: Maximum change considered "stuck"

    Returns:
        Dict with stuck metrics, variance, and recommended fixes
    """
    if len(history) < 5:
        return {"stuck": [], "message": "Not enough history for audit"}

    metrics = list(history[0].keys())
    stuck = []

    for metric in metrics:
        values = [h.get(metric, 0) for h in history]
        first_half = sum(values[:len(values)//2]) / max(1, len(values)//2)
        second_half = sum(values[len(values)//2:]) / max(1, len(values) - len(values)//2)
        delta = abs(second_half - first_half)
        floor_ceiling = min(values) == max(values)
        at_zero = all(v == 0.0 for v in values)
        at_max = all(v == max(values) for v in values)

        if delta <= stuck_threshold or floor_ceiling:
            stuck.append({
                "metric": metric,
                "first_half_mean": round(first_half, 4),
                "second_half_mean": round(second_half, 4),
                "delta": round(delta, 6),
                "at_floor": at_zero,
                "at_ceiling": at_max,
                "diagnosis": _diagnose(metric, at_zero, at_max, first_half, second_half),
            })

    return {
        "generations": generations,
        "total_metrics": len(metrics),
        "stuck_metrics": len(stuck),
        "stuck_rate": len(stuck) / max(1, len(metrics)),
        "recommendation": (
            "MODEL BUGS DETECTED — do not train harder. Fix the domain's seed() or measure()."
            if stuck else "All metrics moving. Model appears valid."
        ),
        "stuck": stuck,
    }


def _diagnose(metric: str, at_zero: bool, at_max: bool, first: float, last: float) -> str:
    """Human-readable diagnosis for a stuck metric."""
    if at_zero:
        return (
            f"METRIC '{metric}' is STUCK AT ZERO across all generations. "
            f"The domain's physics model cannot produce this value. "
            f"Fix: add a baseline parameter to seed() or change the measure() formula. "
            f"Example: if brightness(w) = 1-exp(-w/k) produces 0 at w=0, "
            f"add baseline: baseline + (1-baseline)*(1-exp(-w/k))."
        )
    if at_max and last >= 1.0:
        return (
            f"METRIC '{metric}' is PEGGED AT CEILING. "
            f"The domain's physics maxes out immediately — no discrimination between genomes. "
            f"Fix: add a scaling factor or cost that prevents trivial maxing. "
            f"Example: if response_diversity = 1.0 for all genomes, "
            f"add a complexity cost or noise term to spread the distribution."
        )
    return (
        f"METRIC '{metric}' moved only {abs(last-first):.6f} across generations. "
        f"Selection pressure is present but the metric is unresponsive. "
        f"Fix: check that mutate() actually perturbs the parameters driving this metric."
    )


def audit_domain(domain_name: str, pop_size: int = 30, gens: int = 15):
    """Quick audit of a domain — run a short training pass and diagnose stuck metrics."""
    import importlib
    import random

    try:
        domain = importlib.import_module(f"core.trainables.{domain_name}")
    except ImportError:
        return {"error": f"Domain {domain_name} not found"}

    rng = random.Random(0)
    pop = [domain.seed(rng) for _ in range(pop_size)]

    history = []
    for gen in range(gens):
        scored = [(domain.measure(g), g) for g in pop]
        scored.sort(key=lambda x: sum(v for k, v in x[0].items() if isinstance(v, (int, float)) and k != "genome_summary"), reverse=True)
        history.append({k: v for k, v in scored[0][0].items() if isinstance(v, (int, float))})

        elite = [g for _, g in scored[:max(2, pop_size // 5)]]
        pop = [domain.mutate(rng.choice(elite), rng) for _ in range(pop_size)]

    result = audit_run(history, gens)
    result["domain"] = domain_name
    return result


if __name__ == "__main__":
    import sys, json

    if len(sys.argv) > 1:
        domain = sys.argv[1]
        result = audit_domain(domain)
    else:
        # Audit all trainable domains
        from pathlib import Path
        domains = [p.stem for p in Path("core/trainables").glob("*.py") if not p.stem.startswith("_")]
        results = {}
        for d in domains:
            try:
                results[d] = audit_domain(d)
                print(f"  {d}: {results[d].get('stuck_metrics', '?')} stuck, {results[d].get('recommendation', '?')[:60]}")
            except Exception as e:
                results[d] = {"error": str(e)}
                print(f"  {d}: ERROR - {e}")
        result = results

    print(json.dumps(result, indent=2))
