"""economy — the DeepSpaceTrader market, as a trainable domain.

The genome is lifted straight out of tests/dsl_grammar/deep_space_trader.chimera.
THE DSL IS THE GENOME — this studio built a genotype->phenotype pipeline before it
knew that is what it was doing. These numbers currently change only when a human or
an LLM edits them by hand. They are data, so they can be TRAINED.

WHAT THE HAND-AUTHORED NUMBERS ACTUALLY DO
------------------------------------------
    Titanium:  buy at Titan_Surface  45  ->  sell at Orbital_Hub_7  72   = +27/kg
    Cargo capacity 50,000 kg                    -> 1,350,000 credits per run
    Prices are STATIC. Nothing pushes back.

That is a riskless, unbounded money printer, and it is why H-13 records that economy
features "repeatedly grade C/F". You cannot see it by reading the DSL; you see it the
moment a greedy agent runs the numbers 400,000 times.

THIS MODULE REPORTS FACTS, NOT OPINIONS. It measures. It never says which number is
good — that is docs/objectives/economy.json, written by the LLM from a scenario.

The simulated player is a GREEDY ARBITRAGEUR: at every station it takes the trade
with the best credits-per-hour, forever. It is not a nice player. It is the player
who reads a wiki, and it is exactly the player your economy must survive.
"""

from __future__ import annotations

import random

# --- sim settings (NOT genome: these are the test conditions, not the game) ----
SIM_HOURS = 60.0
MAX_STEPS = 400            # totality: a `for` bound, never a `while True`
START_CREDITS = 10_000.0

STATIONS = ["Orbital_Hub_7", "Titan_Surface_Outpost", "Ares_Market_Central"]


def _pair(a: str, b: str) -> str:
    return "|".join(sorted((a, b)))


def seed() -> dict:
    """The live DSL numbers. Verbatim where the spec gives them; the gaps filled at
    the same order of magnitude, because a 3-station market needs a full price grid
    and the spec only prices some pairs."""
    return {
        # commodity -> mass kg/unit, and per-station [buy_from_station, sell_to_station]
        "commodities": {
            "Titanium":       {"mass": 1.0,  "p": {"Orbital_Hub_7": [80.0, 72.0],
                                                   "Titan_Surface_Outpost": [45.0, 40.0],
                                                   "Ares_Market_Central": [62.0, 56.0]}},
            "Iron_Ore":       {"mass": 1.0,  "p": {"Orbital_Hub_7": [38.0, 33.0],
                                                   "Titan_Surface_Outpost": [22.0, 18.0],
                                                   "Ares_Market_Central": [30.0, 25.0]}},
            "Synthetic_Food": {"mass": 0.5,  "p": {"Orbital_Hub_7": [19.0, 16.0],
                                                   "Titan_Surface_Outpost": [24.0, 20.0],
                                                   "Ares_Market_Central": [15.0, 12.0]}},
            "Quantum_Cores":  {"mass": 8.0,  "p": {"Orbital_Hub_7": [5000.0, 4200.0],
                                                   "Titan_Surface_Outpost": [5600.0, 4800.0],
                                                   "Ares_Market_Central": [5300.0, 4500.0]}},
        },
        # fuel litres per jump (DSL: 2000 / 3000 / 4000). Keys built with _pair so
        # they cannot drift out of sorted order.
        "jump_fuel": {
            _pair("Orbital_Hub_7", "Titan_Surface_Outpost"): 2000.0,
            _pair("Orbital_Hub_7", "Ares_Market_Central"): 3000.0,
            _pair("Titan_Surface_Outpost", "Ares_Market_Central"): 4000.0},
        "jump_hours": {
            _pair("Orbital_Hub_7", "Titan_Surface_Outpost"): 1.5,
            _pair("Orbital_Hub_7", "Ares_Market_Central"): 2.0,
            _pair("Titan_Surface_Outpost", "Ares_Market_Central"): 2.5},
        "fuel_price": 0.6,          # credits/litre — the DSL never sets one
        "cargo_kg": 50_000.0,       # Trader_Vessel_Alpha
        "next_ship_cost": 2_000_000.0,

        # ELASTICITY: how hard the market pushes back when you trade into it.
        # The DSL has NO such concept — prices are static — so this starts at ZERO,
        # which is precisely why the money printer exists. It is a genome locus so
        # the optimiser can DISCOVER whether it needs one. If it evolves away from
        # zero, that is not a tuned number: it is a structural finding about the DSL.
        "elasticity": 0.0,
    }


def mutate(g: dict, rng: random.Random) -> dict:
    import copy
    d = copy.deepcopy(g)

    def jit(v, frac, lo, hi):
        return max(lo, min(hi, v * (1.0 + rng.uniform(-frac, frac))))

    for c in d["commodities"].values():
        for st, pr in c["p"].items():
            if rng.random() < 0.5:
                pr[0] = jit(pr[0], 0.20, 1.0, 20_000.0)          # buy price
            if rng.random() < 0.5:
                pr[1] = jit(pr[1], 0.20, 0.5, 20_000.0)          # sell price
            pr[1] = min(pr[1], pr[0])                            # a station never
            #                     pays more than it charges: that is a free bug, not
            #                     a design choice, so it is not in the search space.
    for k in d["jump_fuel"]:
        if rng.random() < 0.3:
            d["jump_fuel"][k] = jit(d["jump_fuel"][k], 0.25, 100.0, 20_000.0)
    for k in d["jump_hours"]:
        if rng.random() < 0.3:
            d["jump_hours"][k] = jit(d["jump_hours"][k], 0.25, 0.25, 12.0)
    d["fuel_price"] = jit(d["fuel_price"], 0.25, 0.02, 20.0)
    d["cargo_kg"] = jit(d["cargo_kg"], 0.20, 500.0, 400_000.0)

    if rng.random() < 0.30:                    # let it reach the elasticity locus
        d["elasticity"] = max(0.0, min(0.9, d["elasticity"]
                                       + rng.uniform(-0.06, 0.10)))
    return d


def measure(g: dict) -> dict:
    """Run a greedy arbitrageur through the market and report what happened.

    TOTAL: a `for` over MAX_STEPS. No `while True`, so no genome can hang the trainer.
    """
    import copy
    px = {c: copy.deepcopy(v["p"]) for c, v in g["commodities"].items()}
    mass = {c: v["mass"] for c, v in g["commodities"].items()}

    credits = START_CREDITS
    station = STATIONS[0]
    t = 0.0
    hours_to_ship = None
    route_profit, visits, used_comm = {}, {s: 0 for s in STATIONS}, set()
    early_profit = late_profit = 0.0
    early_h = late_h = 0.0

    def best_from(here: str, purse: float):
        """The most profitable laden run out of `here`, or None."""
        b = None
        for c in px:
            buy = px[c][here][0]
            if buy <= 0:
                continue
            for dest in STATIONS:
                if dest == here:
                    continue
                sell = px[c][dest][1]
                key = _pair(here, dest)
                fuel_cost = g["jump_fuel"][key] * g["fuel_price"]
                hrs = max(g["jump_hours"][key], 0.05)
                units = min(g["cargo_kg"] / max(mass[c], 1e-6), purse / buy)
                if units <= 0:
                    continue
                net = units * (sell - buy) - fuel_cost
                rate = net / hrs
                if b is None or rate > b[0]:
                    b = (rate, net, c, dest, units, hrs, key)
        return b

    for _ in range(MAX_STEPS):
        if t >= SIM_HOURS:
            break

        best = best_from(station, credits)

        if best is None or best[1] <= 0.0:
            # NOTHING pays from here. A competent player does not give up — they
            # DEADHEAD: jump empty to wherever the good route starts. Modelling a
            # player who simply starves was a bug in this simulator, and it hid the
            # money printer entirely (the printer runs Titan_Surface -> Orbital_Hub_7,
            # and the player spawns at Orbital_Hub_7).
            move = None
            for dest in STATIONS:
                if dest == station:
                    continue
                key = _pair(station, dest)
                fuel_cost = g["jump_fuel"][key] * g["fuel_price"]
                hrs = max(g["jump_hours"][key], 0.05)
                if fuel_cost >= credits:
                    continue
                nxt_best = best_from(dest, credits - fuel_cost)
                if nxt_best is None or nxt_best[1] <= 0.0:
                    continue
                gain = nxt_best[1] / (hrs + nxt_best[5])     # rate INCLUDING the deadhead
                if move is None or gain > move[0]:
                    move = (gain, dest, fuel_cost, hrs)
            if move is None:
                break                            # genuinely stranded: no route anywhere
            _, dest, fuel_cost, hrs = move
            credits -= fuel_cost
            t += hrs
            station = dest
            visits[dest] += 1
            continue

        rate, net, c, dest, units, hrs, key = best
        credits += net
        t += hrs
        used_comm.add(c)
        visits[dest] += 1
        rk = f"{c}:{station}->{dest}"
        route_profit[rk] = route_profit.get(rk, 0.0) + net

        if t <= SIM_HOURS * 0.25:
            early_profit += net
            early_h += hrs
        elif t >= SIM_HOURS * 0.75:
            late_profit += net
            late_h += hrs

        # THE MARKET PUSHES BACK — but only if the genome gave it the ability to.
        # elasticity == 0 (the DSL today) means it never does, so the same route
        # pays the same forever. That is the money printer, in one line.
        e = g["elasticity"]
        if e > 0.0:
            sat = min(1.0, units * mass[c] / max(g["cargo_kg"], 1e-6))
            px[c][station][0] *= (1.0 + e * sat)       # you bid the source UP
            px[c][dest][1] *= (1.0 - e * sat)          # you glut the destination
            px[c][dest][1] = max(px[c][dest][1], 0.5)

        if hours_to_ship is None and credits >= g["next_ship_cost"]:
            hours_to_ship = t

    total = sum(route_profit.values())
    top = max(route_profit.values()) if route_profit else 0.0

    early_rate = early_profit / max(early_h, 1e-6)
    late_rate = late_profit / max(late_h, 1e-6)
    # Does the best route EXHAUST ITSELF? With static prices it never can — the
    # decay is exactly 0 and the printer runs forever.
    decay = 0.0 if early_rate <= 0 else max(0.0, min(1.0, 1.0 - late_rate / early_rate))

    return {
        "credits_per_hour": total / max(t, 1e-6),
        "hours_to_next_ship": hours_to_ship if hours_to_ship is not None else 999.0,
        "top_route_share": (top / total) if total > 0 else 1.0,
        "routes_used": float(len(route_profit)),
        "commodities_used": float(len(used_comm)),
        "stations_visited": float(sum(1 for v in visits.values() if v > 0)),
        "rate_decay": decay,
        "elasticity": g["elasticity"],
        "final_credits": credits,
    }
