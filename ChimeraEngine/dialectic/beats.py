"""
Beat script executor for the Chimera particle engine.

Beats are JSON scripts that define actions (set control variables,
run simulation frames) and expectations (assert particle state).
Replaces the Unreal sleepwalker — instead of driving PIE, it drives
the GPU particle simulation directly.

Format:
{
  "demo": "test_name",
  "loop": 0,
  "settle_s": 3,
  "beats": [
    {
      "name": "dust_falls",
      "features": ["Dust_Accumulation"],
      "actions": [
        {"set_var": {"gravity": [0, 0, -981]}},
        {"set_var": {"wind_strength": 0}},
        {"wait": 2.0}
      ],
      "expects": [
        {"prop_gt": {"type": "dust", "prop": 0, "value": 0.05}}
      ]
    }
  ]
}

Expect types:
  particle_count:  {"type": "dust", "min": N, "max": M}
  prop_gt:         {"type": "dust", "prop": 0, "value": V}
  prop_lt:         {"type": "sand", "prop": 1, "value": V}
  prop_range:      {"type": "dust", "prop": 0, "min": A, "max": B}
  position_mean_z: {"type": "dust", "max": Z}
  speed_mean:      {"type": "sand", "max_mag": S}
"""

import json
import time
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class BeatOutcome:
    name: str
    features: list[str]
    reached: bool
    expectations: list[dict]  # [{name, passed, detail}, ...]
    sim_time: float
    wall_time: float


@dataclass
class BeatRun:
    demo: str
    loop: int
    beats_total: int
    beats_reached: int
    outcomes: list[BeatOutcome]
    chronicle: dict
    simtime_s: float
    walltime_s: float
    temperature: str  # [SIM] verdict string


class BeatRunner:
    """
    Executes beat scripts against the GPU particle engine.

    Usage:
        runner = BeatRunner()
        result = runner.run("docs/beats/dust_test.beats.json")
        print(f"{result.beats_reached}/{result.beats_total} beats passed")
    """

    def __init__(self, fps: int = 60):
        self.fps = fps
        self.dt = 1.0 / fps

    def run(self, beats_path: str) -> BeatRun:
        spec = json.loads(Path(beats_path).read_text(encoding="utf-8"))
        demo = spec.get("demo", "unknown")
        loop = spec.get("loop", 0)
        settle = spec.get("settle_s", 3)
        beats = spec.get("beats", [])

        from ParticleEngine.core import ParticleSimulator, COL, PARTICLE_TYPES, C_POS, C_VEL, C_PROPS
        from ParticleEngine.kernels.standard import (
            gravity_kernel, wind_kernel, box_boundary_kernel, accumulation_kernel,
            temperature_kernel, color_lifetime_kernel,
        )
        from ParticleEngine.control_vars import default_physics_registry
        from ParticleEngine.gpu_pipeline import FullGPUPipeline

        # Init simulation
        sim = ParticleSimulator(max_particles=100000)
        reg = default_physics_registry()
        for k in [gravity_kernel, wind_kernel, box_boundary_kernel,
                   accumulation_kernel, temperature_kernel, color_lifetime_kernel]:
            sim.add_kernel(k, k.__name__)

        # Default spawn
        sim.spawn(10000, "dust", (0, 0, 500), 300,
                  mass=0.005, life=-1, color=(0.75, 0.68, 0.55, 0.8), size=0.5)
        sim.spawn(5000, "sand", (200, 100, 600), 200,
                  mass=0.02, life=-1, color=(0.9, 0.72, 0.35, 0.9), size=0.4)
        sim.spawn(3000, "atmosphere", (0, 0, 2000), 800,
                  mass=0.001, life=-1, color=(0.5, 0.6, 0.85, 0.08), size=12.0)

        # Upload to GPU
        for _ in range(int(settle * self.fps)):
            sim.step(self.dt, reg.snapshot())

        pipe = FullGPUPipeline()
        pipe.upload(sim._data[:sim.count])

        cvars = reg.snapshot()
        outcomes = []
        simtime = 0.0
        t0 = time.time()

        for beat in beats:
            name = beat.get("name", "?")
            features = beat.get("features", [])

            # Execute actions
            for action in beat.get("actions", []):
                self._do_action(action, cvars, pipe, sim)

            # Check expectations
            expectations = []
            all_passed = True
            # Download particle state from GPU
            gpu_data = pipe.download_particles()

            for expect in beat.get("expects", []):
                result = self._check_expect(expect, gpu_data, pipe._n)
                expectations.append(result)
                if not result["passed"]:
                    all_passed = False

            outcome = BeatOutcome(
                name=name,
                features=features,
                reached=all_passed,
                expectations=expectations,
                sim_time=simtime,
                wall_time=time.time() - t0,
            )
            outcomes.append(outcome)

        elapsed = time.time() - t0
        reached = sum(1 for o in outcomes if o.reached)

        return BeatRun(
            demo=demo,
            loop=loop,
            beats_total=len(beats),
            beats_reached=reached,
            outcomes=outcomes,
            chronicle={"session": demo, "fps": self.fps},
            simtime_s=simtime,
            walltime_s=elapsed,
            temperature=f"[SIM] {reached}/{len(beats)} beats reached in '{demo}'."
        )

    def _do_action(self, action, cvars, pipe, sim):
        if "set_var" in action:
            for k, v in action["set_var"].items():
                cvars[k] = tuple(v) if isinstance(v, list) else v
        elif "wait" in action:
            frames = int(action["wait"] * self.fps)
            for _ in range(frames):
                pipe.step_particles(self.dt, cvars)
        elif "spawn" in action:
            s = action["spawn"]
            # Spawn on CPU, re-upload
            count = sim.spawn(
                s.get("count", 100),
                s.get("type", "dust"),
                tuple(s.get("position", [0, 0, 500])),
                s.get("spread", 100),
                mass=s.get("mass", 0.005),
                life=s.get("life", -1),
                color=tuple(s.get("color", [1, 1, 1, 1])),
                size=s.get("size", 0.5),
            )
            pipe.upload(sim._data[:sim.count])

    def _check_expect(self, expect, data, n):
        """Evaluate one expectation against particle data."""
        NCOLS = 28; PX, PY, PZ = 0, 1, 2; VX, VY, VZ = 3, 4, 5; TYPE = 11
        PROPS = slice(12, 16)

        for key, spec in expect.items():
            try:
                type_name = spec.get("type", None)
                type_code = None
                from ParticleEngine.core import PARTICLE_TYPES
                if type_name:
                    type_code = PARTICLE_TYPES.get(type_name)
                    mask = data[:n, TYPE] == type_code
                else:
                    mask = np.ones(n, dtype=bool)

                masked = data[:n][mask]

                if key == "particle_count":
                    cnt = len(masked)
                    min_v = spec.get("min", 0)
                    max_v = spec.get("max", 1e9)
                    ok = min_v <= cnt <= max_v
                    return {"name": key, "passed": ok,
                            "detail": f"count={cnt} (range [{min_v},{max_v}])"}

                elif key == "prop_gt":
                    prop_idx = spec["prop"]
                    val = float(masked[:, PROPS][:, prop_idx].mean()) if len(masked) else 0
                    ok = val > spec["value"]
                    return {"name": key, "passed": ok,
                            "detail": f"prop{prop_idx}={val:.4f} > {spec['value']}"}

                elif key == "prop_lt":
                    prop_idx = spec["prop"]
                    val = float(masked[:, PROPS][:, prop_idx].mean()) if len(masked) else 0
                    ok = val < spec["value"]
                    return {"name": key, "passed": ok,
                            "detail": f"prop{prop_idx}={val:.4f} < {spec['value']}"}

                elif key == "prop_range":
                    prop_idx = spec["prop"]
                    val = float(masked[:, PROPS][:, prop_idx].mean()) if len(masked) else 0
                    ok = spec["min"] <= val <= spec["max"]
                    return {"name": key, "passed": ok,
                            "detail": f"prop{prop_idx}={val:.4f} in [{spec['min']},{spec['max']}]"}

                elif key == "position_mean_z":
                    val = float(masked[:, PZ].mean()) if len(masked) else 0
                    ok = val < spec["max"]
                    return {"name": key, "passed": ok,
                            "detail": f"z_mean={val:.1f} < {spec['max']}"}

                elif key == "speed_mean":
                    vel = masked[:, [VX, VY, VZ]]
                    mag = float(np.linalg.norm(vel, axis=1).mean()) if len(masked) else 0
                    ok = mag < spec["max_mag"]
                    return {"name": key, "passed": ok,
                            "detail": f"speed_mean={mag:.1f} < {spec['max_mag']}"}

                else:
                    return {"name": key, "passed": False,
                            "detail": f"unknown expect type: {key}"}

            except Exception as e:
                return {"name": key, "passed": False,
                        "detail": f"error: {e}"}

        return {"name": "?", "passed": False, "detail": "empty expect"}
