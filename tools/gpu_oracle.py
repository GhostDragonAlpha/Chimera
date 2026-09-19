"""gpu_oracle.py - GPU-batched multibody force ingredients on the RTX 4090.

Computes, for MANY joint poses simultaneously (torch, float64, CUDA), the same
quantities the CPU analytic reference (tools/science_funnel/coupled_arm.py)
computes for ONE pose at a time:

    M(q)             per-pose mass matrix            [N, n, n]
    gravity force    per-pose jv^T (m g)              [N, n]
    bias force       per-pose velocity-dependent term [N, n]
    potential energy per-pose -sum m g.p             [N]
    point Jacobians  linear + angular, per body      [N, n, 3]

The construction mirrors coupled_arm.Assembly exactly: same composition order,
same per-axis derivative semantics (assignment for rotation d, accumulation
for translation jt), same Leibniz product rule for frame tuples - only
batched over the pose dimension with einsum. Parity is checked numerically
against the CPU Assembly for a sample of poses before any speed claim.

SCOPE (inherited from the reference): fixed-root SI force ingredients for the
admitted macaque arm model. No time integration, no contact, no muscle
actuation, no free root, no claim that the native engine or the GPU path is
"qualified simulation". This is a fast oracle for the seven-coordinate lift
(native parity against many fixture poses), free-root mass-matrix inspection
and future higher-DOF work.

Usage:
    python tools/gpu_oracle.py [--poses 4096] [--check 16] [--device cuda]
                               [--seed 0] [--zero-rates] [--out receipt.json]
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

REPO = Path(__file__).resolve().parents[1]
MODEL_ID = "model.anatomy.macaque_arm"


def _skew_const(axis):
    a = torch.asarray(axis, dtype=torch.float64)
    return torch.stack([
        torch.stack([torch.zeros_like(a[0]), -a[2], a[1]]),
        torch.stack([a[2], torch.zeros_like(a[0]), -a[0]]),
        torch.stack([-a[1], a[0], torch.zeros_like(a[0])]),
    ])


def _axial(A):
    # A: [..., 3, 3] -> [..., 3]  (mirror of coupled_arm.axial)
    return torch.stack([
        A[..., 2, 1] - A[..., 1, 2],
        A[..., 0, 2] - A[..., 2, 0],
        A[..., 1, 0] - A[..., 0, 1],
    ], dim=-1) / 2


def _cross(a, b):
    return torch.stack([
        a[..., 1] * b[..., 2] - a[..., 2] * b[..., 1],
        a[..., 2] * b[..., 0] - a[..., 0] * b[..., 2],
        a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0],
    ], dim=-1)


class BatchedAssembly:
    """Vectorized mirror of coupled_arm.Assembly over a pose batch.

    Frame tuple per body: (T [N,4,4], d [N,n,4,4], td [N,4,4], tdd [N,4,4]).
    """

    def __init__(self, model, device=None, dtype=torch.float64):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)
        self.dtype = dtype
        self.model = model
        self.gravity = torch.asarray(model["gravity_m_s2"], dtype=dtype,
                                     device=self.device)
        self.coordinates = sorted(k for k, v in model["coordinates"].items()
                                  if not v["locked"])
        self.slots = {k: i for i, k in enumerate(self.coordinates)}
        self.n = len(self.slots)
        if self.n == 0:
            raise ValueError("no_dynamic_coordinates")

        # Topological body order (mirror of Assembly's ready-loop walk).
        bodies = {b["name"]: b for b in model["bodies"]}
        pending = set(bodies) - {"ground"}
        self.order = []
        placed = {"ground"}
        while pending:
            ready = [k for k in sorted(pending)
                     if bodies[k]["joint"]["parent"] in placed]
            if not ready:
                raise ValueError("cyclic_body_hierarchy")
            for k in ready:
                placed.add(k)
                pending.remove(k)
                self.order.append(k)

        # Static per-body data.
        self.body_names = [b["name"] for b in model["bodies"]]
        self.static = {}
        for b in model["bodies"]:
            entry = {"name": b["name"], "mass": float(b["mass_kg"]),
                     "mc": torch.asarray(b["mass_center_m"], dtype=dtype,
                                         device=self.device)}
            xx, yy, zz, xy, xz, yz = b["inertia_kg_m2"]
            entry["ic"] = torch.asarray(
                [[xx, xy, xz], [xy, yy, yz], [xz, yz, zz]],
                dtype=dtype, device=self.device)
            if b["joint"] is not None:
                j = b["joint"]
                entry["parent"] = j["parent"]
                entry["parent_frame"] = self._euler_frame(
                    j["parent_location_m"], j["parent_orientation_rad"])
                entry["child_inv"] = torch.linalg.inv(self._euler_frame(
                    j["child_location_m"], j["child_orientation_rad"]))
                entry["axes"] = []
                for ax in j["axes"]:
                    f = ax["function"]
                    coef = f["coefficients"]
                    if f["type"] == "Constant":
                        slope, offset = 0.0, float(coef[0])
                    else:
                        slope, offset = float(coef[0]), float(coef[1])
                    entry["axes"].append({
                        "rot": ax["name"].startswith("rotation"),
                        "axis": torch.asarray(ax["axis"], dtype=dtype,
                                              device=self.device),
                        "slot": self.slots.get(ax["coordinate"]),
                        "slope": slope,
                        "offset": offset,
                        "name": ax["name"],
                    })
            else:
                entry["parent"] = None
            self.static[b["name"]] = entry

        self._frames = None  # cached by forward()

    def _eye4(self):
        return torch.eye(4, dtype=self.dtype, device=self.device)

    def _euler_frame(self, location, orientation):
        # mirror of macaque_anatomy.frame: R = Rx(a) @ Ry(b) @ Rz(c)
        t = self._eye4()
        for axis, angle in zip(torch.eye(3, dtype=self.dtype,
                                         device=self.device), orientation):
            r = self._rodrigues(axis, torch.full((), float(angle),
                                                 dtype=self.dtype,
                                                 device=self.device))
            t[:3, :3] = t[:3, :3] @ r
        t[:3, 3] = torch.asarray(location, dtype=self.dtype,
                                 device=self.device)
        return t

    def _rodrigues(self, axis_unit, theta):
        # theta: [N] or scalar; returns [N,3,3] or [3,3]
        K = _skew_const(axis_unit)
        K2 = K @ K
        I = torch.eye(3, dtype=self.dtype, device=self.device)
        if theta.dim() == 0:
            return I + torch.sin(theta) * K + (1 - torch.cos(theta)) * K2
        s = torch.sin(theta).view(-1, 1, 1)
        c = torch.cos(theta).view(-1, 1, 1)
        return I + s * K + (1 - c) * K2

    def _identity_tuple(self, n_poses):
        z = lambda *s: torch.zeros(*s, dtype=self.dtype, device=self.device)
        # clone(): expand() shares memory; the caller overwrites :3,3 blocks.
        return (self._eye4().expand(n_poses, 4, 4).clone(),
                z(n_poses, self.n, 4, 4),
                z(n_poses, 4, 4),
                z(n_poses, 4, 4))

    def _prod(self, a, b):
        # Leibniz product of frame tuples (mirror of coupled_arm.product).
        T = a[0] @ b[0]
        d = a[1] @ b[0].unsqueeze(1) + a[0].unsqueeze(1) @ b[1]
        td = a[2] @ b[0] + a[0] @ b[2]
        tdd = a[3] @ b[0] + 2.0 * (a[2] @ b[2]) + a[0] @ b[3]
        return (T, d, td, tdd)

    def forward(self, q, rates):
        """q, rates: [N, n] (slot order = sorted unlocked coordinates)."""
        N = q.shape[0]
        frames = {"ground": self._identity_tuple(N)}

        for name in self.order:
            st = self.static[name]
            if st["parent"] is None:
                continue
            # motion tuple: rotate-compose per axis, translation overwritten.
            motion = self._identity_tuple(N)
            translation = torch.zeros(N, 3, dtype=self.dtype,
                                      device=self.device)
            vt = torch.zeros(N, 3, dtype=self.dtype, device=self.device)
            jt = torch.zeros(N, self.n, 3, dtype=self.dtype,
                             device=self.device)
            for ax in st["axes"]:
                if ax["slot"] is None:
                    value = torch.full((N,), ax["offset"], dtype=self.dtype,
                                       device=self.device)
                    rate = torch.zeros(N, dtype=self.dtype,
                                       device=self.device)
                else:
                    value = ax["slope"] * q[:, ax["slot"]] + ax["offset"]
                    rate = ax["slope"] * rates[:, ax["slot"]]
                if ax["rot"]:
                    R = self._rodrigues(ax["axis"], value)
                    dR = _skew_const(ax["axis"]) @ R
                    t = self._eye4().expand(N, 4, 4).clone()
                    t[:, :3, :3] = R
                    d = torch.zeros(N, self.n, 4, 4, dtype=self.dtype,
                                    device=self.device)
                    if ax["slot"] is not None:
                        d[:, ax["slot"], :3, :3] = ax["slope"] * dR
                    td = torch.zeros(N, 4, 4, dtype=self.dtype,
                                     device=self.device)
                    td[:, :3, :3] = rate.view(N, 1, 1) * dR
                    tdd = torch.zeros(N, 4, 4, dtype=self.dtype,
                                      device=self.device)
                    tdd[:, :3, :3] = (rate * rate).view(N, 1, 1) * (
                        _skew_const(ax["axis"]) @ dR)
                    motion = self._prod(motion, (t, d, td, tdd))
                else:
                    translation = translation + ax["axis"] * value.unsqueeze(1)
                    vt = vt + ax["axis"] * rate.unsqueeze(1)
                    if ax["slot"] is not None:
                        jt[:, ax["slot"], :] += ax["axis"] * ax["slope"]
            # Translation axes live in the parent joint frame: overwrite the
            # motion tuple's translation blocks (mirror of Assembly).
            motion[0][:, :3, 3] = translation
            motion[1][:, :, :3, 3] = jt
            motion[2][:, :3, 3] = vt

            parent = frames[st["parent"]]
            here = (st["parent_frame"].expand(N, 4, 4),
                    torch.zeros(N, self.n, 4, 4, dtype=self.dtype,
                                device=self.device),
                    torch.zeros(N, 4, 4, dtype=self.dtype, device=self.device),
                    torch.zeros(N, 4, 4, dtype=self.dtype, device=self.device))
            child_inv = (st["child_inv"].expand(N, 4, 4),
                         torch.zeros(N, self.n, 4, 4, dtype=self.dtype,
                                     device=self.device),
                         torch.zeros(N, 4, 4, dtype=self.dtype,
                                     device=self.device),
                         torch.zeros(N, 4, 4, dtype=self.dtype,
                                     device=self.device))
            frames[name] = self._prod(self._prod(self._prod(parent, here),
                                                 motion), child_inv)

        self._frames = frames

        # Per-body dynamics accumulation (mirror of Assembly's body loop).
        M = torch.zeros(N, self.n, self.n, dtype=self.dtype,
                        device=self.device)
        grav = torch.zeros(N, self.n, dtype=self.dtype, device=self.device)
        bias = torch.zeros(N, self.n, dtype=self.dtype, device=self.device)
        potential = torch.zeros(N, dtype=self.dtype, device=self.device)
        self.jacobians = {}
        for b in self.model["bodies"]:
            st = self.static[b["name"]]
            m = st["mass"]
            T, d, td, tdd = frames[b["name"]]
            r = T[:, :3, :3]
            rT = r.transpose(-1, -2)
            iw = r @ st["ic"] @ rT
            # [4,1] column; torch broadcasts it over every batch dimension,
            # so T@p4c -> [N,4,1], d@p4c -> [N,n,4,1], tdd@p4c -> [N,4,1].
            p4c = torch.cat([st["mc"],
                             torch.ones(1, dtype=self.dtype,
                                        device=self.device)]).view(4, 1)
            position = (T @ p4c)[:, :3, 0]
            jv = (d @ p4c)[:, :, :3, 0]                     # [N, n, 3]
            jw = _axial(d[:, :, :3, :3] @ rT.unsqueeze(1))  # [N, n, 3]
            omega = _axial(td[:, :3, :3] @ rT)              # [N, 3]
            alpha = _axial(tdd[:, :3, :3] @ rT
                           + td[:, :3, :3] @ td[:, :3, :3].transpose(-1, -2))
            acceleration = (tdd @ p4c)[:, :3, 0]
            # jv/jw are [N, n, 3] (rows = coordinates). Quadratic forms are
            # J @ J^T -> [n, n]; angular: (jw @ iw) @ jwT, matching the
            # reference's jv.T @ jv and jw.T @ iw @ jw in its [3, n] layout.
            M = M + m * (jv @ jv.transpose(-1, -2)) \
                  + (jw @ iw) @ jw.transpose(-1, -2)
            grav = grav + torch.einsum("nsi,i->ns", jv, m * self.gravity)
            iw_alpha = iw @ alpha.unsqueeze(-1)
            iw_omega = iw @ omega.unsqueeze(-1)
            gyro = iw_alpha.squeeze(-1) + _cross(omega, iw_omega.squeeze(-1))
            bias = bias + torch.einsum("nsi,ni->ns", jv, m * acceleration) \
                        + (jw @ gyro.unsqueeze(-1)).squeeze(-1)
            potential = potential - m * (position * self.gravity).sum(-1)
            self.jacobians[b["name"]] = {
                "position": position, "jv": jv, "jw": jw, "iw": iw,
                "mass": m,
            }

        if not (torch.isfinite(M).all() and torch.isfinite(bias).all()
                and torch.isfinite(grav).all()
                and torch.isfinite(potential).all()):
            raise ValueError("nonfinite_assembly")
        return {"mass_matrix": M, "gravity_force": grav, "bias_force": bias,
                "potential": potential}

    def point_force(self, body, local_m, force_N):
        """Generalized force [N, n] for a force applied at a body point."""
        st = self.static[body]
        T, d, _, _ = self._frames[body]
        p4 = torch.cat([torch.asarray(local_m, dtype=self.dtype,
                                      device=self.device),
                        torch.ones((), dtype=self.dtype,
                                   device=self.device)]).view(1, 4, 1)
        jv = (d @ p4)[:, :, :3, 0]
        f = torch.asarray(force_N, dtype=self.dtype, device=self.device)
        return jv @ f


def load_model():
    """Same model source as coupled_arm.main (admitted graph, not live source)."""
    import sys
    sys.path.insert(0, str(REPO))
    from tools.science_funnel.macaque_anatomy import ROOT, MODEL
    from tools.creature_graph.store import CreatureGraph
    graph = CreatureGraph.load(str(ROOT / "tools/creature_graph/data/creature_graph.json"))
    model = graph.get(MODEL)["physical"]["model"]
    return model, graph.graph_hash()


def _sample_poses(model, n, seed, random_rates):
    rng = np.random.default_rng(seed)
    coords = sorted(k for k, v in model["coordinates"].items()
                    if not v["locked"])
    q = np.empty((n, len(coords)))
    rates = np.zeros((n, len(coords)))
    for i, name in enumerate(coords):
        c = model["coordinates"][name]
        lo, hi = c["range_rad"]
        eps = 1e-6
        q[:, i] = rng.uniform(lo + eps, hi - eps, size=n)
        if random_rates:
            rates[:, i] = rng.uniform(-1.0, 1.0, size=n)
    return coords, q, rates


def run(poses=4096, check=16, device=None, seed=0, out_path=None,
        random_rates=True):
    model, graph_hash = load_model()
    batcher = BatchedAssembly(model, device=device)
    coords, q, rates = _sample_poses(model, poses, seed, random_rates)
    q_t = torch.asarray(q, dtype=torch.float64, device=batcher.device)
    v_t = torch.asarray(rates, dtype=torch.float64, device=batcher.device)

    # Warmup (JIT/cuBLAS handles), then timed forward.
    batcher.forward(q_t[:4], v_t[:4])
    if batcher.device.type == "cuda":
        torch.cuda.synchronize()
    t0 = time.perf_counter()
    out = batcher.forward(q_t, v_t)
    if batcher.device.type == "cuda":
        torch.cuda.synchronize()
    gpu_sec = time.perf_counter() - t0

    # Parity: same poses through the CPU analytic reference.
    from tools.science_funnel.coupled_arm import Assembly
    k = min(check, poses)
    diffs = {"mass_matrix": 0.0, "gravity_force": 0.0, "bias_force": 0.0,
             "potential": 0.0}
    scales = {"mass_matrix": 1.0, "gravity_force": 1.0, "bias_force": 1.0,
              "potential": 1.0}
    for i in range(k):
        values = {c: float(q[i, j]) for j, c in enumerate(coords)}
        rate_d = {c: float(rates[i, j]) for j, c in enumerate(coords)}
        ref = Assembly(model, values=values, rates=rate_d,
                       gravity=tuple(model["gravity_m_s2"]))
        got_m = out["mass_matrix"][i].cpu().numpy()
        got_g = out["gravity_force"][i].cpu().numpy()
        got_b = out["bias_force"][i].cpu().numpy()
        got_p = float(out["potential"][i].cpu())
        diffs["mass_matrix"] = max(diffs["mass_matrix"],
                                   float(np.abs(got_m - ref.mass_matrix).max()))
        scales["mass_matrix"] = max(scales["mass_matrix"],
                                    float(np.abs(ref.mass_matrix).max()))
        diffs["gravity_force"] = max(
            diffs["gravity_force"],
            float(np.abs(got_g - ref.gravity_force).max()))
        scales["gravity_force"] = max(
            scales["gravity_force"], float(np.abs(ref.gravity_force).max()))
        diffs["bias_force"] = max(diffs["bias_force"],
                                  float(np.abs(got_b - ref.bias_force).max()))
        scales["bias_force"] = max(scales["bias_force"],
                                   float(np.abs(ref.bias_force).max()))
        diffs["potential"] = max(diffs["potential"],
                                 abs(got_p - ref.potential_J))
        scales["potential"] = max(scales["potential"],
                                  abs(ref.potential_J))

    rel = {k2: diffs[k2] / scales[k2] for k2 in diffs}
    parity_pass = all(v < 1e-9 for v in rel.values())

    # CPU throughput reference on the same box (bounded; honest per-pose rate).
    cpu_poses = min(poses, 128)
    t0 = time.perf_counter()
    for i in range(cpu_poses):
        values = {c: float(q[i, j]) for j, c in enumerate(coords)}
        rate_d = {c: float(rates[i, j]) for j, c in enumerate(coords)}
        Assembly(model, values=values, rates=rate_d,
                 gravity=tuple(model["gravity_m_s2"]))
    cpu_sec = time.perf_counter() - t0

    result = {
        "phase": "gpu-oracle",
        "device": str(batcher.device),
        "dtype": "float64",
        "poses": poses,
        "coordinates": batcher.n,
        "coordinate_order": batcher.coordinates,
        "gpu_batch_seconds": round(gpu_sec, 4),
        "gpu_poses_per_second": round(poses / gpu_sec, 1),
        "cpu_reference_poses_timed": cpu_poses,
        "cpu_ms_per_pose": round(1000 * cpu_sec / cpu_poses, 3),
        "cpu_estimate_note": ("cpu_ms_per_pose is a bounded same-box per-pose "
                              "rate; no extrapolated total is claimed"),
        "parity_poses": k,
        "max_abs_diff": {k2: float(f"{v:.3e}") for k2, v in diffs.items()},
        "max_rel_diff": {k2: float(f"{v:.3e}") for k2, v in rel.items()},
        "parity_tolerance_rel": 1e-9,
        "parity_pass": bool(parity_pass),
        "graph_hash": graph_hash,
        "model": MODEL_ID,
        "recorded_utc": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
        "scope": ("Fixed-root SI force ingredients (M, gravity, bias, "
                  "Jacobians) batched over poses for the admitted macaque arm "
                  "model; no time integration, contact, actuation, free root "
                  "or simulation-quality claim."),
    }
    if out_path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        result["out"] = str(out_path)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--poses", type=int, default=4096)
    ap.add_argument("--check", type=int, default=16)
    ap.add_argument("--device", default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--zero-rates", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    result = run(poses=args.poses, check=args.check, device=args.device,
                 seed=args.seed, out_path=Path(args.out) if args.out else None,
                 random_rates=not args.zero_rates)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["parity_pass"] else 1)


if __name__ == "__main__":
    main()
