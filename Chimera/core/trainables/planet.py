"""planet — the planet-averages rung: oceans, atmospheres, interior heat, as ONE number each.

Commissioned 2026-07-18, the human's bar for the whole big-bang ladder: "We know it
works when oceans form, an atmosphere forms, and there's a temperature gradient in
the planet interior... once we get the planet then we have the averages. It's gonna
be great." And the scale doctrine: "think of the planet as ONE when we get to that
scale" / "intelligence is compression and compression is intelligence."

THE CHAIN COMPOSES: this domain consumes docs/objectives/bigbang.systems.json — the
solar rung's grown planets, coalesced to (m_rel, a, e) triples (each planet is ONE).
It never re-runs the N-body; the rung below's output IS this rung's input data.

THE EFFECTIVE LAWS (each an accepted planetary-science relation, each cheap):
    T_eq        equilibrium temperature: 278.6 K / sqrt(a_AU) * (1-albedo)^0.25
                (L = 1 L_sun; Earth: T_eq ~ 255 K at albedo 0.3 — the anchor).
    greenhouse  dT = g_coeff * P_bar^g_exp. Earth: +33 K at 1 bar; Venus: ~+500 K
                at 92 bar (those two researched points bracket g_exp ~ 0.6).
    atmosphere  Jeans-parameter retention: a planet holds a gas when
                v_esc/v_th(mu, T) exceeds a threshold (~6 in the literature).
                Earth keeps N2 (lambda ~ 27) and loses H2 (~7) — the knife edge
                the jeans_threshold locus trains. P scales as f*M^2/R^4,
                normalized to Earth's atmosphere mass fraction 8.7e-7.
    oceans      the delivered water inventory (Earth: 2.3e-4 of mass) condenses
                iff 273 K < T_surf < 647 K AND P above the triple point
                (0.006 bar — the reason MARS is dry today, not temperature).
                Coverage ~ 0.7 * inventory/Earth-inventory, capped at 1.
    interior    specific accretion energy retained: T_center = T_surf +
                retention * 11,400 K * (M/R relative to Earth) — anchored so
                retention 0.5 reproduces Earth's ~5,700 K core. Gradient =
                interior heat over depth; the operator bar asks that it EXIST.
    ice-albedo  the one FEEDBACK: albedo depends on the surface (ocean 0.06,
                ice 0.6, rock 0.2, cloud lift from atmosphere) while T depends
                on albedo — iterated to a damped fixed point (Budyko-Sellers
                lineage; snowball/temperate bistability is genuinely inside).
    radius      rocky mass-radius R ~ M^0.27 (R_earth units), capped at 4 R_e
                (Neptune-class); a body that retains H2 above 10 M_e is a GIANT.

THE GENOME (SEED = what the nebula delivered; SHORTCUTS = compressed processes):
    SEED:      mass_scale_log (M_earth per sim mass unit — the rung anchors its
               own units, per the compression doctrine: the solar rung's masses
               are architecture-level), water_frac_log, outgas_frac_log
    SHORTCUTS: greenhouse g_coeff/g_exp, jeans_threshold, heat_retention

NOTHING GRADES ON TASTE: the objective (docs/objectives/planet.json) binds the
emergent CLIMATE ARCHITECTURE to researched anchors — at least one ocean world per
system, interior gradients on every rocky world, 3+ distinct climate classes
(airless / frozen / temperate-ocean / hot / runaway / giant — the solar system
spans them), ocean-world surface temperature in the liquid window, Earth-like
greenhouse on the ocean world. Facts only; worst-cased across the catalog systems.

DETERMINISTIC: no RNG anywhere — the catalog systems are the restarts, the
fixed-point iteration is a bounded damped for-loop (totality by construction).

DOMAIN CONTRACT: seed(rng) -> genome ; mutate(genome, rng) -> genome ;
measure(genome) -> {fact: float}.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

CATALOG = Path(r"E:\PythonChimera\Chimera\docs\objectives\bigbang.systems.json")

# --- physical constants of the effective laws (researched, NOT genome) ----------
T_SUN_AU = 278.6            # K at 1 AU, zero albedo, 1 L_sun
EARTH_ATM_FRAC = 8.7e-7     # Earth's atmosphere as a fraction of its mass
EARTH_WATER_FRAC = 2.3e-4   # Earth's ocean inventory as a fraction of its mass
TRIPLE_P_BAR = 0.006        # water triple point — Mars sits just below
T_FREEZE, T_CRIT = 273.0, 647.0
ALB_OCEAN, ALB_ICE, ALB_ROCK = 0.06, 0.60, 0.20
CLOUD_ALB_LIFT = 0.15       # thick-atmosphere cloud albedo contribution (cap)
K_CORE = 11400.0            # K: retention 0.5 -> Earth's ~5,700 K core (M/R = 1)
V_ESC_EARTH = 11.2          # km/s
V_TH_N2_288 = 0.41          # km/s thermal speed scale of N2 at 288 K
MU_N2, MU_H2, MU_H2O = 28.0, 2.0, 18.0
GIANT_MIN_ME = 10.0         # retains H2 above this mass -> gas giant class
FP_ITERS = 30               # ice-albedo fixed point: bounded, damped
FP_DAMP = 0.5

GENOME_SCHEMA = {
    # --- SEED: what the nebula delivered ---
    "mass_scale_log":  {"min": 2.0, "max": 4.3, "init": 3.0},   # 10^x M_e/unit
    "water_frac_log":  {"min": -5.0, "max": -2.5, "init": -3.6},
    "outgas_frac_log": {"min": -7.5, "max": -4.5, "init": -6.0},
    # --- SHORTCUTS: compressed processes ---
    "g_coeff":         {"min": 5.0, "max": 80.0, "init": 33.0},
    "g_exp":           {"min": 0.25, "max": 0.95, "init": 0.60},
    "jeans_threshold": {"min": 3.5, "max": 10.0, "init": 6.0},
    "heat_retention":  {"min": 0.05, "max": 1.00, "init": 0.50},
    # The MOIST-GREENHOUSE LIMIT (round-2 lesson: without it, 376 K steam
    # pressure-cookers scored as 'ocean' and diversity died at 2 classes).
    # Researched: Kasting's habitable-zone inner edge — above ~340-350 K,
    # stratospheric water photolyzes and the hydrogen escapes; hot worlds
    # DRY OUT (Venus is the graduate). Oceans only condense BELOW this.
    "moist_limit":     {"min": 330.0, "max": 420.0, "init": 360.0},
}


def seed(rng=None) -> dict:
    r = _rand01(rng)
    return {k: s["min"] + r() * (s["max"] - s["min"])
            for k, s in GENOME_SCHEMA.items()}


def mutate(genome: dict, rng=None) -> dict:
    g = _gauss(rng)
    out = dict(genome)
    for k, s in GENOME_SCHEMA.items():
        out[k] = float(min(s["max"], max(s["min"],
                                         genome[k] + g((s["max"] - s["min"])
                                                       * 0.12))))
    return out


def _rand01(rng):
    if rng is None:
        rng = np.random.default_rng()
    return rng.random if hasattr(rng, "random") else rng.rand


def _gauss(rng):
    if rng is None:
        rng = np.random.default_rng()
    if hasattr(rng, "normal"):
        return lambda s: float(rng.normal(0.0, s))
    return lambda s: rng.gauss(0.0, s)


# --- one planet, resolved to its averages ---------------------------------------

def _planet_state(m_earth: float, a_au: float, genome: dict) -> dict:
    """All the averages of ONE planet, from its mass and orbit. Deterministic."""
    radius = min(m_earth ** 0.27, 4.0) if m_earth > 0 else 0.1
    v_esc = V_ESC_EARTH * math.sqrt(max(m_earth, 1e-6) / radius)
    water_inv = 10.0 ** genome["water_frac_log"]
    outgas_inv = 10.0 ** genome["outgas_frac_log"]
    thr = genome["jeans_threshold"]

    # Ice-albedo fixed point: T depends on albedo depends on surface state.
    albedo, t_surf, p_bar, ocean_cov, retains_h2 = 0.25, 250.0, 0.0, 0.0, False
    for _ in range(FP_ITERS):
        t_eq = T_SUN_AU / math.sqrt(a_au) * (1.0 - albedo) ** 0.25
        v_th = V_TH_N2_288 * math.sqrt(max(t_eq, 30.0) / 288.0)
        lam_n2 = v_esc / v_th
        lam_h2 = v_esc / (v_th * math.sqrt(MU_N2 / MU_H2))
        ret_n2 = 1.0 / (1.0 + math.exp(-(lam_n2 - thr)))
        retains_h2 = lam_h2 > thr
        p_new = (outgas_inv / EARTH_ATM_FRAC) * ret_n2 \
            * (m_earth ** 2) / (radius ** 4)
        t_new = t_eq + genome["g_coeff"] * max(p_new, 0.0) ** genome["g_exp"]

        wet = (T_FREEZE < t_new < genome["moist_limit"]) \
            and (p_new > TRIPLE_P_BAR)
        ret_h2o = 1.0 / (1.0 + math.exp(-(v_esc / (v_th * math.sqrt(
            MU_N2 / MU_H2O)) - thr)))
        cov_new = min(1.0, 0.7 * (water_inv * ret_h2o) / EARTH_WATER_FRAC) \
            if wet else 0.0
        frozen = t_new <= T_FREEZE
        alb_surface = (ALB_OCEAN * cov_new + ALB_ROCK * (1.0 - cov_new)
                       if not frozen else ALB_ICE)
        alb_new = min(0.75, alb_surface
                      + CLOUD_ALB_LIFT * min(p_new, 2.0) / 2.0)

        albedo += FP_DAMP * (alb_new - albedo)
        t_surf += FP_DAMP * (t_new - t_surf)
        p_bar += FP_DAMP * (p_new - p_bar)
        ocean_cov += FP_DAMP * (cov_new - ocean_cov)

    t_center = t_surf + genome["heat_retention"] * K_CORE \
        * (max(m_earth, 1e-6) / radius)
    giant = retains_h2 and m_earth > GIANT_MIN_ME
    if giant:
        klass = "giant"
    elif p_bar < TRIPLE_P_BAR:
        klass = "airless"
    elif ocean_cov > 0.02:
        klass = "ocean"
    elif t_surf <= T_FREEZE:
        klass = "frozen"
    elif p_bar > 5.0 and t_surf > genome["moist_limit"]:
        klass = "runaway"
    else:
        klass = "hot_rock"
    return {"m_earth": m_earth, "a_au": a_au, "radius": radius,
            "t_surf": t_surf, "t_center": t_center, "p_bar": p_bar,
            "ocean_cov": ocean_cov, "albedo": albedo, "class": klass,
            "gradient_k": t_center - t_surf}


def resolve_system(planets: list[dict], genome: dict) -> list[dict]:
    """Resolve every planet of one catalog system to its averages."""
    scale = 10.0 ** genome["mass_scale_log"]
    return [_planet_state(p["m_rel"] * scale, max(p["a"], 0.05), genome)
            for p in planets]


def _load_catalog() -> list[list[dict]]:
    data = json.loads(CATALOG.read_text())
    return [s for s in data["systems"] if s]


def measure(genome: dict) -> dict:
    """FACTS ONLY, worst-cased across the catalog's grown systems."""
    systems = [resolve_system(s, genome) for s in _load_catalog()]
    per = []
    for sys_p in systems:
        rocky = [p for p in sys_p if p["class"] != "giant"]
        oceans = [p for p in sys_p if p["class"] == "ocean"]
        classes = {p["class"] for p in sys_p}
        per.append({
            "n_planets": len(sys_p),
            "n_ocean": len(oceans),
            "n_classes": len(classes),
            "grad_frac": (np.mean([1.0 if p["gradient_k"] > 500.0 else 0.0
                                   for p in rocky]) if rocky else 0.0),
            "atmo_frac": np.mean([1.0 if p["p_bar"] > TRIPLE_P_BAR else 0.0
                                  for p in sys_p]),
            "runaway_frac": np.mean([1.0 if p["class"] == "runaway" else 0.0
                                     for p in sys_p]),
            "ocean_t": (np.mean([p["t_surf"] for p in oceans])
                        if oceans else 0.0),
            "ocean_gh": (np.mean(
                [p["t_surf"] - T_SUN_AU / math.sqrt(p["a_au"])
                 * (1.0 - p["albedo"]) ** 0.25 for p in oceans])
                if oceans else 0.0),
            "ocean_t_center": (np.mean([p["t_center"] for p in oceans])
                               if oceans else 0.0),
            "habitable_frac": len(oceans) / max(len(sys_p), 1),
        })
    a = {k: np.array([r[k] for r in per]) for k in per[0]}
    return {
        "has_ocean_worst": float(a["n_ocean"].min() > 0),
        "n_ocean_mean": float(a["n_ocean"].mean()),
        "climate_classes_worst": float(a["n_classes"].min()),
        "gradient_frac_worst": float(a["grad_frac"].min()),
        "atmo_frac_mean": float(a["atmo_frac"].mean()),
        "runaway_frac_mean": float(a["runaway_frac"].mean()),
        "ocean_temp_mean": float(a["ocean_t"][a["n_ocean"] > 0].mean()
                                 if (a["n_ocean"] > 0).any() else 0.0),
        "ocean_greenhouse_mean": float(a["ocean_gh"][a["n_ocean"] > 0].mean()
                                       if (a["n_ocean"] > 0).any() else 0.0),
        "ocean_t_center_mean": float(
            a["ocean_t_center"][a["n_ocean"] > 0].mean()
            if (a["n_ocean"] > 0).any() else 0.0),
        "habitable_frac_worst": float(a["habitable_frac"].min()),
    }


if __name__ == "__main__":
    import time
    g = {k: s["init"] for k, s in GENOME_SCHEMA.items()}
    t0 = time.perf_counter()
    facts = measure(g)
    dt = time.perf_counter() - t0
    print(json.dumps(facts, indent=1))
    print(f"one eval: {dt*1000:.1f}ms -> {1.0/dt:.0f} evals/sec/worker")
    for i, s in enumerate(_load_catalog()):
        states = resolve_system(s, g)
        row = ", ".join(f"{p['class']}@{p['a_au']:.2f}au"
                        f"({p['m_earth']:.1f}Me,{p['t_surf']:.0f}K)"
                        for p in states)
        print(f"  system {i}: {row}")
