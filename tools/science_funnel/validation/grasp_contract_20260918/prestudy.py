"""Numerical pre-study for the 2026-09-18 bounded grasp contract.

This is deliberately an offline reference study. It does not modify or import
native engine behavior and writes only the requested JSON receipt.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from tools.creature_graph.store import CreatureGraph
from tools.science_funnel.coupled_arm import Assembly


def solve():
    root = Path(__file__).resolve().parents[4]
    graph = CreatureGraph.load(str(root / "tools/creature_graph/data/creature_graph.json"))
    recipe = graph.get("model.dynamics.coupled_arm")["physical"]["contract"]
    model = graph.get(recipe["source_model_id"])["physical"]["model"]

    # The requested settled pre-study pose: both dynamic target coordinates at 20 deg.
    q = {"shoulder_flexion": math.radians(20.0), "elbow_flexion": math.radians(20.0)}
    arm = Assembly(model, values=q, rates={"shoulder_flexion": 0.0, "elbow_flexion": 0.0},
                   gravity=model["gravity_m_s2"])
    hand, jac_full = arm.point("hand", recipe["hand_point_m"])
    dynamic = [arm.coordinates.index(name) for name in recipe["coordinates"]]
    jac = np.asarray(jac_full[:, dynamic].T, dtype=float)
    # World +Up normal and +East tangent.  The second plane's rows are their
    # anti-parallel negatives; the effective pair therefore has one normal row.
    normal = np.asarray(jac[:, 1], dtype=float)
    tangent = np.asarray(jac[:, 0], dtype=float)
    pair_rows = np.vstack((normal, -normal))
    contact_rows = np.vstack((normal, tangent))
    mass_full = np.asarray(arm.mass_matrix, dtype=float)
    mass = mass_full[np.ix_(dynamic, dynamic)]
    inv_mass = np.linalg.inv(mass)
    metric = contact_rows @ inv_mass @ contact_rows.T

    # Bounded store envelope.  The store capacity is inherited from the qualified
    # arm's 2 J battery; no new tuned capacity is introduced here.
    store_J = float(recipe["battery_initial_J"])
    radius = float(recipe["proxy_radius_m"])
    closure_samples = np.linspace(0.001, 0.010, 10)
    envelope = [{"closure_m": float(x), "force_bound_N": store_J / float(x)}
                for x in closure_samples]

    # Grid scan identifies the exact opposing-row rank collapse and the separate
    # two-row (normal/tangent) rank boundary.
    coords = model["coordinates"]
    s_range = coords["shoulder_flexion"]["range_rad"]
    e_range = coords["elbow_flexion"]["range_rad"]
    pair_dets = []
    contact_dets = []
    min_normal_norm = (float("inf"), None)
    for s in np.linspace(*s_range, 81):
        for e in np.linspace(*e_range, 81):
            probe = Assembly(model, values={"shoulder_flexion": float(s), "elbow_flexion": float(e)},
                             rates={}, gravity=model["gravity_m_s2"])
            _, pj_full = probe.point("hand", recipe["hand_point_m"])
            pj = np.asarray(pj_full[:, dynamic].T, dtype=float)
            n = np.asarray(pj[:, 1], dtype=float)
            t = np.asarray(pj[:, 0], dtype=float)
            pair_dets.append(float(np.linalg.det(np.vstack((n, -n)))))
            contact_dets.append(float(np.linalg.det(np.vstack((n, t)))))
            norm = float(np.linalg.norm(n))
            if norm < min_normal_norm[0]:
                min_normal_norm = (norm, (math.degrees(s), math.degrees(e)))

    # Worked KKT: prescribed acceleration floors [normal, tangent] in the
    # independent normal/tangent contact basis.
    accel_floor = np.array([1.0, 0.5])
    multipliers = np.linalg.solve(metric, accel_floor)
    kkt_mu = 0.50
    cone_total_normal = 2.0 * max(0.0, float(multipliers[0]))
    cone_limit = kkt_mu * cone_total_normal

    # Worked catch. Choose a joint velocity whose normal/tangent point speeds are
    # exactly (-0.08, +0.03) m/s, then solve the joint impulse in the same metric.
    point_velocity = np.array([-0.08, 0.03])
    qdot = np.linalg.solve(contact_rows, point_velocity)
    catch_mu = 0.25
    impulse_uncapped = np.linalg.solve(metric, -point_velocity)
    tangential_cap = catch_mu * (2.0 * max(0.0, float(impulse_uncapped[0])))
    impulse_capped = impulse_uncapped.copy()
    if abs(impulse_capped[1]) > tangential_cap:
        impulse_capped[1] = math.copysign(tangential_cap, impulse_capped[1])
        impulse_capped[0] = (-point_velocity[0] - metric[0, 1] * impulse_capped[1]) / metric[0, 0]
    delta_v = inv_mass @ contact_rows.T @ impulse_capped
    final_qdot = qdot + delta_v
    kinetic_before = 0.5 * float(qdot @ mass @ qdot)
    kinetic_after = 0.5 * float(final_qdot @ mass @ final_qdot)
    mean_point_velocity = point_velocity + 0.5 * (contact_rows @ delta_v)
    normal_dissipation = -float(impulse_capped[0] * mean_point_velocity[0])
    tangential_dissipation = -float(impulse_capped[1] * mean_point_velocity[1])
    total_dissipation = kinetic_before - kinetic_after

    result = {
        "schema": "chimera.grasp_contract_prestudy.v1",
        "pose": {"shoulder_flexion_deg": 20.0, "elbow_flexion_deg": 20.0,
                 "hand_world_m": hand.tolist(), "coordinate_order": recipe["coordinates"],
                 "hand_jacobian_m_per_rad": jac.tolist()},
        "qualified_store": {"capacity_J": store_J, "source": "model.dynamics.coupled_arm battery_initial_J"},
        "squeeze_force_envelope": envelope,
        "rank": {
            "opposing_rows": pair_rows.tolist(),
            "opposing_row_determinant_max_abs": max(abs(x) for x in pair_dets),
            "opposing_row_rank": 1 if np.linalg.norm(normal) > 1e-12 else 0,
            "normal_tangent_metric": metric.tolist(),
            "normal_tangent_determinant_grid_min": min(contact_dets),
            "normal_tangent_determinant_grid_max": max(contact_dets),
            "minimum_normal_row_norm_grid": min_normal_norm[0],
            "minimum_normal_row_norm_pose_deg": min_normal_norm[1],
        },
        "kkt_example": {
            "mu": kkt_mu, "metric": metric.tolist(), "acceleration_floor": accel_floor.tolist(),
            "multipliers_normal_tangent": multipliers.tolist(),
            "pair_total_normal": cone_total_normal, "pair_tangent_magnitude": abs(float(multipliers[1])),
            "coulomb_limit": cone_limit, "cone_pass": bool(abs(float(multipliers[1])) <= cone_limit + 1e-12),
            "decouples_iff_metric_off_diagonal_zero": bool(abs(metric[0, 1]) <= 1e-12),
        },
        "catch_example": {
            "mu": catch_mu, "point_velocity_before_m_per_s": point_velocity.tolist(),
            "joint_velocity_before_rad_per_s": qdot.tolist(),
            "uncapped_total_impulse_normal_tangent": impulse_uncapped.tolist(),
            "tangential_cap_N_s": tangential_cap,
            "capped_total_impulse_normal_tangent": impulse_capped.tolist(),
            "point_velocity_after_m_per_s": (contact_rows @ final_qdot).tolist(),
            "joint_velocity_after_rad_per_s": final_qdot.tolist(),
            "kinetic_before_J": kinetic_before, "kinetic_after_J": kinetic_after,
            "dissipation_normal_J": normal_dissipation,
            "dissipation_tangential_J": tangential_dissipation,
            "dissipation_total_J": total_dissipation,
            "dissipation_split_closes": bool(abs(total_dissipation - normal_dissipation - tangential_dissipation) < 1e-12),
            "symmetric_plane_impulse_split": "each plane receives one half of the total normal impulse; friction uses the anti-parallel row pair and the pair cone",
        },
        "scope": "Offline 2-DOF proxy-sphere grasp contract only; no runtime grasp implementation.",
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(solve(), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "schema": "chimera.grasp_contract_prestudy.v1"}))


if __name__ == "__main__":
    main()
