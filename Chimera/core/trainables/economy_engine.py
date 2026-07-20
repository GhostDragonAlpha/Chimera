"""economy_engine — market dynamics as a trainable domain.

CWM rung: Systems (Loop 8). FStationMarket at 50% realized.

ELEMENTS:
  - COMMODITIES: 8 tradable goods
  - STATIONS: 4 trade hubs
  - ROUTES: connections between stations

PRINCIPLES:
  - Supply/demand equilibrium
  - Arbitrage across stations
  - Price discovery through trade volume
  - Faction reputation affects prices

MEASURABLE PHYSICS:
  - price_stability: do prices converge or oscillate?
  - arbitrage_opportunity: price gaps between stations
  - trade_volume: total goods moved
  - faction_impact: does reputation change prices?
"""

from __future__ import annotations
import copy, math, random

EVAL_SEED = 271
N_TICKS = 200
N_COMMODITIES = 8
N_STATIONS = 4

COMMODITIES = ["water", "oxygen", "metal", "fuel", "food", "medicine", "data", "luxury"]
BASE_PRICES = {"water": 10, "oxygen": 25, "metal": 50, "fuel": 40, "food": 15, "medicine": 60, "data": 80, "luxury": 100}


def seed(rng=None):
    rng = rng or random.Random()
    return {
        "supply_elasticity": rng.uniform(0.01, 0.3),
        "demand_elasticity": rng.uniform(0.01, 0.3),
        "arbitrage_threshold": rng.uniform(0.05, 0.4),
        "faction_price_modifier": rng.uniform(0.0, 0.3),
        "volatility": rng.uniform(0.01, 0.15),
        "station_supply": {s: {c: rng.uniform(50, 200) for c in COMMODITIES} for s in range(N_STATIONS)},
        "station_demand": {s: {c: rng.uniform(30, 150) for c in COMMODITIES} for s in range(N_STATIONS)},
    }

def mutate(g, rng=None):
    rng = rng or random.Random()
    g = copy.deepcopy(g)
    for k in ["supply_elasticity", "demand_elasticity", "arbitrage_threshold", "faction_price_modifier", "volatility"]:
        if rng.random() < 0.5:
            g[k] = max(0.001, g[k] * math.exp(rng.uniform(-0.15, 0.15)))
    return g

def measure(g):
    rng = random.Random(EVAL_SEED)
    prices = {s: {c: BASE_PRICES[c] for c in COMMODITIES} for s in range(N_STATIONS)}
    trades, arbitrages, volatilities = [], [], []

    for t in range(N_TICKS):
        for s in range(N_STATIONS):
            for c in COMMODITIES:
                supply, demand = g["station_supply"][s][c], g["station_demand"][s][c]
                ratio = demand / max(1, supply)
                delta = (ratio - 1) * g["supply_elasticity"] * prices[s][c]
                noise = rng.uniform(-g["volatility"], g["volatility"]) * prices[s][c]
                prices[s][c] = max(1, min(10000, prices[s][c] + delta + noise))

        for c in COMMODITIES:
            all_p = [prices[s][c] for s in range(N_STATIONS)]
            spread = (max(all_p) - min(all_p)) / max(1, sum(all_p) / len(all_p))
            if spread > g["arbitrage_threshold"]:
                arbitrages.append(spread)
        trades.append(sum(sum(p[c] for c in COMMODITIES) for p in prices.values()))

    return {
        "price_stability": 1.0 / (1.0 + (sum(arbitrages) / max(1, len(arbitrages)))),
        "arbitrage_opportunity_rate": len(arbitrages) / N_TICKS,
        "trade_volume_mean": sum(trades) / len(trades),
        "price_convergence": 1.0 - (sum(arbitrages[-20:]) / max(0.001, sum(arbitrages[:20]))) if arbitrages else 0.5,
        "genome_summary": {"elasticity": g["supply_elasticity"], "volatility": g["volatility"]},
    }
