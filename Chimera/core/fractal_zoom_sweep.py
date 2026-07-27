"""fractal_zoom_sweep — stress-test stress_gradient_to_emission_prob across gradient
distributions that would reveal failure of a hardcoded midpoint.

Tests three families:
  1. NARROW — gradients tightly clustered [0.21, 0.28] (the old midpoint's own
     neighbourhood). Should produce probabilities spanning [0.05, 0.95] after
     per-batch normalisation; a fixed midpoint would saturate.
  2. WIDE — gradients spread across [0.1, 0.5].
  3. SKEWED — log-normal and beta distributions biased toward one tail, so the
     median shifts away from the arithmetic mean, testing MAD robustness.

Each test generates N=4 independent batches (different random seeds), calls
stress_gradient_to_emission_prob, and records:
  - probability range (min, max)
  - probability span (max - min)
  - proportion of probabilities in [0.05, 0.95] (unsaturation)
  - proportion in [0.01, 0.99] (the hard clamp boundaries)

KILL CRITERION: any batch where the probability span < 0.50 AND the unsaturation
fraction < 0.80 — meaning the per-batch normalisation failed to spread the
distribution adequately, AND probabilities are bunching at the clamp edges.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

from core.splat_emit import stress_gradient_to_emission_prob

ROOT = Path(__file__).resolve().parents[1]

_KILL_SPAN = 0.50        # min acceptable probability span
_KILL_UNSAT = 0.80       # min acceptable unsaturation fraction
_N_BATCHES = 4           # batches per distribution family
_N_POINTS = 2000         # points per batch


# --- distribution generators ------------------------------------------------

def narrow_batch(seed: int) -> np.ndarray:
    """Tight cluster around [0.21, 0.28] — the old midpoint's own home range.
    A hardcoded midpoint at 0.245 would saturate to near 0 and 1 immediately;
    per-batch normalisation should spread it."""
    rng = np.random.RandomState(seed)
    return rng.uniform(0.21, 0.28, size=_N_POINTS)


def wide_batch(seed: int) -> np.ndarray:
    """Wide spread across [0.1, 0.5]."""
    rng = np.random.RandomState(seed)
    return rng.uniform(0.1, 0.5, size=_N_POINTS)


def skewed_batch(seed: int) -> np.ndarray:
    """Right-skewed log-normal distribution shifted to [0.05, 0.6] range.
    Median < mean — tests that MAD-based normalisation (which uses median)
    handles asymmetry correctly."""
    rng = np.random.RandomState(seed)
    raw = rng.lognormal(mean=-1.2, sigma=0.5, size=_N_POINTS)
    raw = np.clip(raw, 0.05, 0.60)
    return raw


def beta_skewed_batch(seed: int) -> np.ndarray:
    """Beta(0.5, 2.0) — concentrated near 0 (left-heavy)."""
    rng = np.random.RandomState(seed)
    raw = rng.beta(0.5, 2.0, size=_N_POINTS)
    return np.clip(raw, 0.02, 0.60)


# --- analysis ----------------------------------------------------------------

_DISTRIBUTIONS = {
    "narrow": narrow_batch,
    "wide": wide_batch,
    "skewed_lognormal": skewed_batch,
    "skewed_beta": beta_skewed_batch,
}


def analyze_batch(gradients: np.ndarray, label: str) -> dict:
    """Run stress_gradient_to_emission_prob on one batch and return metrics."""
    prob = stress_gradient_to_emission_prob(gradients)

    p_min = float(prob.min())
    p_max = float(prob.max())
    span = p_max - p_min
    frac_unsat = float(np.mean((prob >= 0.05) & (prob <= 0.95)))
    frac_clamped = float(np.mean((prob <= 0.01) | (prob >= 0.99)))
    frac_near_clamp = float(np.mean((prob <= 0.03) | (prob >= 0.97)))

    grad_min = float(gradients.min())
    grad_max = float(gradients.max())
    grad_median = float(np.median(gradients))
    grad_mean = float(gradients.mean())

    return {
        "label": label,
        "gradient_min": grad_min,
        "gradient_max": grad_max,
        "gradient_median": grad_median,
        "gradient_mean": grad_mean,
        "prob_min": p_min,
        "prob_max": p_max,
        "prob_span": span,
        "unsaturation_fraction_0_05_0_95": frac_unsat,
        "clamped_fraction_0_01_0_99": frac_clamped,
        "near_clamp_fraction_0_03_0_97": frac_near_clamp,
        "kill": bool(span < _KILL_SPAN and frac_unsat < _KILL_UNSAT),
    }


# --- CLI ---------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", default=None,
                    help="output directory (default: Saved/FractalZoomSweep)")
    ap.add_argument("--seed", type=int, default=42, help="master seed")
    a = ap.parse_args()

    out_dir = Path(a.out_dir) if a.out_dir else (ROOT / "Saved" / "FractalZoomSweep")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n=== FRACTAL ZOOM SWEEP — stress test per-batch normalisation ===\n")

    all_results = {}
    any_kill = False

    for dist_name, gen_fn in _DISTRIBUTIONS.items():
        print(f"--- {dist_name} ---")
        batch_results = []
        for i in range(_N_BATCHES):
            seed = a.seed + i * 10007
            gradients = gen_fn(seed)
            info = analyze_batch(gradients, f"{dist_name}_{i}")
            batch_results.append(info)

            status = "KILL" if info["kill"] else "ok"
            print(f"  batch {i}: span={info['prob_span']:.3f}  "
                  f"unsat={info['unsaturation_fraction_0_05_0_95']:.3f}  "
                  f"clamped={info['clamped_fraction_0_01_0_99']:.3f}  "
                  f"prob=[{info['prob_min']:.3f}, {info['prob_max']:.3f}]  "
                  f"grad median={info['gradient_median']:.4f}  "
                  f"grad range=[{info['gradient_min']:.4f},{info['gradient_max']:.4f}]  "
                  f"[{status}]")

            if info["kill"]:
                any_kill = True

        all_results[dist_name] = batch_results

    # also run a stress test with meta dicts to exercise the adaptive-gain path
    print("\n--- adaptive gain (meta dict) ---")
    meta_results = []
    for scale_factor in [0.5, 1.0, 2.0]:
        rng = np.random.RandomState(a.seed + int(scale_factor * 100))
        grad = rng.uniform(0.1, 0.5, size=_N_POINTS) * scale_factor
        meta = [{"type": "candidate", "volume": rng.randint(20, 2000)}
                for _ in range(_N_POINTS)]
        prob = stress_gradient_to_emission_prob(grad, meta)
        span = float(prob.max() - prob.min())
        unsat = float(np.mean((prob >= 0.05) & (prob <= 0.95)))
        kill = bool(span < _KILL_SPAN and unsat < _KILL_UNSAT)
        meta_results.append({
            "label": f"meta_scale_{scale_factor:.1f}",
            "prob_span": span,
            "unsaturation_fraction": unsat,
            "kill": kill,
        })
        status = "KILL" if kill else "ok"
        print(f"  scale={scale_factor:.1f}: span={span:.3f}  "
              f"unsat={unsat:.3f}  [{status}]")
    all_results["adaptive_gain_meta"] = meta_results

    verdict = "KILL" if any_kill else "SURVIVES"
    print(f"\n=== VERDICT: {verdict} ===")
    all_results["verdict"] = verdict

    (out_dir / "results.json").write_text(
        json.dumps(all_results, indent=2), encoding="utf-8")
    print(f"  -> {out_dir / 'results.json'}")

    return 1 if any_kill else 0


if __name__ == "__main__":
    sys.exit(main())
