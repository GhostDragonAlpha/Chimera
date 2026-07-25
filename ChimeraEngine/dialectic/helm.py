"""
Helm — gap analysis between design intent and simulation reality.

The Helm reads the current particle engine state and compares it
against the design seed (what we're building toward). It produces
ranked gaps: problems to solve next.

Heuristic: gaps are ranked by (design_weight × reality_gap).
"""

from dataclasses import dataclass, field
import numpy as np


@dataclass
class Gap:
    name: str
    design_target: str       # what we want
    reality: str             # what we have
    severity: float          # 0-1, higher = bigger problem
    evidence: dict | None = None


class Helm:
    """
    Steers development by ranking gaps between design and reality.

    Usage:
        helm = Helm()
        helm.add_target("atmospheric_density", "Dense visible haze", weight=0.8)
        gaps = helm.analyze(particle_data)
        for g in gaps:
            print(f"{g.name}: {g.reality} (severity {g.severity:.2f})")
    """

    def __init__(self):
        self._targets: dict[str, dict] = {}

    def add_target(self, name: str, description: str, weight: float = 0.5):
        self._targets[name] = {"description": description, "weight": weight}

    def analyze(self, particle_data, pipe) -> list[Gap]:
        """Analyze particle state against design targets. Returns ranked gaps."""
        gaps = []
        for name, target in self._targets.items():
            gap = self._check_target(name, target, particle_data, pipe)
            if gap:
                gaps.append(gap)
        gaps.sort(key=lambda g: -g.severity)
        return gaps

    def _check_target(self, name, target, data, pipe) -> Gap | None:
        NCOLS = 28; TYPE = 11; ALPHA = 19; PZ = 2; VX, VY, VZ = 3, 4, 5
        n = min(len(data), pipe._n) if hasattr(pipe, '_n') else len(data)

        if name == "atmospheric_density":
            # Check atmosphere particle count and opacity
            atm = data[:n][data[:n, TYPE] == 5]  # atmosphere type
            if len(atm) < 100:
                return Gap(name, target["description"],
                          f"Only {len(atm)} atmosphere particles",
                          target["weight"])
            avg_alpha = float(atm[:, ALPHA].mean()) if len(atm) > 0 else 0
            if avg_alpha < 0.03:
                return Gap(name, target["description"],
                          f"Atmosphere too transparent (alpha={avg_alpha:.3f})",
                          target["weight"] * 0.7)
            return None

        elif name == "dust_settling":
            dust = data[:n][data[:n, TYPE] == 0]  # dust type
            if len(dust) < 500:
                return Gap(name, target["description"],
                          f"Only {len(dust)} dust particles",
                          target["weight"])
            avg_z = float(dust[:, PZ].mean())
            # Dust should be settling (z decreasing over time)
            avg_speed = float(np.linalg.norm(dust[:, [VX, VY, VZ]], axis=1).mean())
            if avg_speed > 50:
                return Gap(name, target["description"],
                          f"Dust too fast (speed={avg_speed:.0f}), not settling",
                          target["weight"] * 0.8)
            return None

        elif name == "particle_diversity":
            types = set(int(t) for t in data[:n, TYPE])
            if len(types) < 3:
                return Gap(name, target["description"],
                          f"Only {len(types)} particle types active",
                          target["weight"])
            return None

        return None


def default_helm() -> Helm:
    """Create a Helm with standard Chimera design targets."""
    h = Helm()
    h.add_target("atmospheric_density", "Visible volumetric haze from atmosphere particles", 0.6)
    h.add_target("dust_settling", "Dust particles accumulate on surfaces over time", 0.8)
    h.add_target("particle_diversity", "Multiple particle types active simultaneously", 0.5)
    return h
