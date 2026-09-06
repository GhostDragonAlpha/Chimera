"""CPU reference for the live Chimera JNT2/JNT3 gait interface.

This is deliberately a *mirror*, not an animation exporter.  It reads the same
binary session assets used by the Vulkan engine, evaluates the composed FK/LBS
law in ``engine/shaders/joints.comp``, and gives the coordinator numerical
limits before a gait is put into engine.cpp.

Run from any directory:
    python tools/gait_mirror.py

Only numpy and the Python standard library are required.
"""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MESH = ROOT / "ChimeraEngine/engine/build/Release/session_snapshot/mesh_bin.blob"
DEFAULT_PACK = ROOT / "ChimeraEngine/engine/build/Release/session_snapshot/joints_bin.blob"
G = 9.80665
FPS = 60
FR_WALK = 0.183  # documented Earth walking Froude reference, not a fitted gain
CLEARANCE_FRACTION = 0.06


@dataclass
class Pack:
    tag: bytes
    names: list[str]
    assign: np.ndarray
    weight: np.ndarray
    pivot: np.ndarray
    axis: np.ndarray
    rom: np.ndarray
    parent: np.ndarray
    joint2: np.ndarray | None
    weight2: np.ndarray | None


def load_mesh(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Read `[u32 n][u32 index_count][n*pos,nrm,col][indices]` snapshot."""
    raw = path.read_bytes()
    n, ni = struct.unpack_from("<II", raw, 0)
    # Session snapshots preserve the request's 24-byte mesh_bin header
    # (`main.cpp`: N, index_count, camera r/theta/phi, slotmode), whereas the
    # first eight bytes alone are enough to identify the payload dimensions.
    header = 24
    expected = header + n * 9 * 4 + ni * 4
    if len(raw) != expected:
        raise ValueError(f"mesh length {len(raw)} != protocol length {expected}")
    verts = np.frombuffer(raw, "<f4", n * 9, header).reshape(n, 9).astype(np.float64)
    ind = np.frombuffer(raw, "<u4", ni, header + n * 9 * 4).copy()
    return verts[:, :3], ind


def load_pack(path: Path) -> Pack:
    raw = path.read_bytes()
    tag = raw[:4]
    if tag not in (b"JNT1", b"JNT2", b"JNT3"):
        raise ValueError(f"unsupported pack magic {tag!r}")
    nv, nj, name_bytes = struct.unpack_from("<III", raw, 4)
    off = 16
    names = [x.decode("utf8") for x in raw[off:off + name_bytes].split(b"\0") if x]
    if len(names) != nj:
        raise ValueError(f"pack names={len(names)}, header says {nj}")
    off += name_bytes
    assign = np.frombuffer(raw, "<i4", nv, off).copy(); off += nv * 4
    weight = np.frombuffer(raw, "<f4", nv, off).copy().astype(np.float64); off += nv * 4
    pivot = np.frombuffer(raw, "<f4", nj * 3, off).reshape(nj, 3).copy().astype(np.float64); off += nj * 12
    axis = np.frombuffer(raw, "<f4", nj * 3, off).reshape(nj, 3).copy().astype(np.float64); off += nj * 12
    rom = np.frombuffer(raw, "<f4", nj * 2, off).reshape(nj, 2).copy().astype(np.float64); off += nj * 8
    parent = np.full(nj, -1, dtype=np.int32)
    joint2 = weight2 = None
    if tag in (b"JNT2", b"JNT3"):
        parent = np.frombuffer(raw, "<i4", nj, off).copy(); off += nj * 4
    if tag == b"JNT3":
        joint2 = np.frombuffer(raw, "<i4", nv, off).copy(); off += nv * 4
        weight2 = np.frombuffer(raw, "<f4", nv, off).copy().astype(np.float64); off += nv * 4
    if off != len(raw):
        raise ValueError(f"unconsumed pack bytes: {len(raw) - off}")
    axis /= np.maximum(np.linalg.norm(axis, axis=1, keepdims=True), 1e-15)
    return Pack(tag, names, assign, weight, pivot, axis, rom, parent, joint2, weight2)


def rot(axis: np.ndarray, angle: float) -> np.ndarray:
    """Exact Rodrigues matrix: the live JNT2/JNT3 law, not small-angle Euler."""
    x, y, z = axis
    k = np.array(((0.0, -z, y), (z, 0.0, -x), (-y, x, 0.0)))
    c, s = math.cos(angle), math.sin(angle)
    return c * np.eye(3) + (1.0 - c) * np.outer(axis, axis) + s * k


def frames(pack: Pack, theta: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Root-to-own affine FK, exactly the order in joints.comp lines 220--248."""
    n = len(pack.names)
    mats = np.empty((n, 3, 3)); trans = np.empty((n, 3))
    done = np.zeros(n, bool)
    def one(j: int) -> None:
        if done[j]: return
        p = int(pack.parent[j])
        r = rot(pack.axis[j], float(theta[j]))
        t = pack.pivot[j] - r @ pack.pivot[j]
        if p >= 0:
            one(p); mats[j] = r @ mats[p]; trans[j] = r @ trans[p] + t
        else:
            mats[j] = r; trans[j] = t
        done[j] = True
    for j in range(n): one(j)
    return mats, trans


def pose_points(rest: np.ndarray, pack: Pack, theta: np.ndarray) -> np.ndarray:
    """Full per-vertex JNT2/JNT3 LBS position mirror."""
    m, t = frames(pack, theta)
    j = pack.assign
    valid = j >= 0
    out = rest.copy()
    a = j[valid]
    q1 = np.einsum("nij,nj->ni", m[a], rest[valid]) + t[a]
    if pack.tag == b"JNT1":
        return out  # live task's snapshot is JNT3; retained only to reject false equivalence.
    if pack.joint2 is None:
        b = pack.parent[a]
    else:
        b = pack.joint2[valid].copy()
        b[(b < 0) | (b >= len(pack.names))] = pack.parent[a[(b < 0) | (b >= len(pack.names))]]
    q2 = rest[valid].copy()
    has = b >= 0
    q2[has] = np.einsum("nij,nj->ni", m[b[has]], rest[valid][has]) + t[b[has]]
    # The JNT3 payload retains w2 for the factory/gate, but the live shader
    # derives the second term as (1-w[i]) (joints.comp 176, 253--255).
    w = pack.weight[valid]
    out[valid] = w[:, None] * q1 + (1.0 - w)[:, None] * q2
    return out


def lipm_constants(h: float, leg: float) -> dict[str, float]:
    """One explicitly labelled *diagnostic* LIPM transit, not a derived gait.

    LIPM itself supplies omega but no clock.  We use its time constant solely to
    make the reachability falsifier dimensionally reproducible; this period
    must never be copied into engine.cpp as a preferred cadence.
    """
    omega = math.sqrt(G / h)
    step_time = 1.0 / omega
    cadence = 1.0 / step_time
    speed = math.sqrt(FR_WALK * G * leg)
    step_length = speed * step_time
    return dict(omega=omega, step_time=step_time, cadence=cadence,
                speed=speed, step_length=step_length, half_step=step_length / 2.0)


def lipm_x(t: float, c: dict[str, float]) -> float:
    """Relative COM coordinate over a stance interval, x(0)=-a, x(T)=+a."""
    w, T, a = c["omega"], c["step_time"], c["half_step"]
    v0 = w * a / math.tanh(w * T / 2.0)
    return -a * math.cosh(w * t) + v0 / w * math.sinh(w * t)


def lipm_boundary_velocity(c: dict[str, float]) -> tuple[float, float]:
    """Velocity needed to cross -a to +a, and the unmatched terminal velocity."""
    w, T, a = c["omega"], c["step_time"], c["half_step"]
    v0 = w * a / math.tanh(w * T / 2.0)
    vt = -a * w * math.sinh(w * T) + v0 * math.cosh(w * T)
    return v0, vt


def damped_ls(fun, target, q0, lo, hi, iterations=80):
    """Finite-difference Gauss--Newton: deterministic least squares, no scipy."""
    q = np.clip(q0.copy(), lo, hi)
    lam = 1e-4
    for _ in range(iterations):
        r = fun(q) - target
        jac = np.empty((len(r), len(q)))
        for k in range(len(q)):
            d = 1e-5
            qq = q.copy(); qq[k] += d
            jac[:, k] = (fun(np.clip(qq, lo, hi)) - fun(q)) / d
        step = np.linalg.solve(jac.T @ jac + lam * np.eye(len(q)), -jac.T @ r)
        cand = np.clip(q + step, lo, hi)
        if np.linalg.norm(fun(cand) - target) < np.linalg.norm(r):
            q = cand; lam *= 0.3
        else: lam *= 10.0
        if np.linalg.norm(step) < 1e-7: break
    return q


def main() -> None:
    rest, _ = load_mesh(DEFAULT_MESH)
    pack = load_pack(DEFAULT_PACK)
    ix = {n: i for i, n in enumerate(pack.names)}
    required = [f"{j}_{side}" for side in "LR" for j in ("hip", "knee", "ankle")]
    if missing := [n for n in required if n not in ix]:
        raise RuntimeError(f"live pack has no required leg chain: {missing}; names={pack.names}")
    ground = float(rest[:, 1].min())
    com = rest.mean(axis=0)
    h = float(com[1] - ground)
    # Mechanical hip->ankle length from the actual fitted rig, averaged L/R.
    leg = float(np.mean([np.linalg.norm(pack.pivot[ix[f"ankle_{s}"]] - pack.pivot[ix[f"hip_{s}"]]) for s in "LR"]))
    c = lipm_constants(h, leg)
    # Verify the symmetric boundary condition before using it.
    x0, xT = lipm_x(0.0, c), lipm_x(c["step_time"], c)
    v0, vT = lipm_boundary_velocity(c)
    print(f"pack={pack.tag.decode()} vertices={len(rest)} joints={len(pack.names)}")
    print(f"COM={com.tolist()} ground_y={ground:.6f} H_com={h:.6f} leg={leg:.6f}")
    print("diagnostic_step_length={step_length:.6f} diagnostic_cadence_hz={cadence:.6f} "
          "diagnostic_cadence_spm={spm:.3f} speed={speed:.6f} diagnostic_step_time={step_time:.6f}"
          .format(**c, spm=60*c["cadence"]))
    print(f"lipm_boundary_residual: dx={xT-c['half_step']:.3e} velocity_reset_required={vT-v0:.6f}")
    print("cadence_result: UNDEFINED by LIPM alone; x=0,v=0 remains equilibrium and a nonzero periodic gait "
          "requires explicitly modelled push-off/impact or a separately-derived swing clock.")

    peaks: dict[str, float] = {}
    all_err = []; theta_log = []
    frames_n = max(2, int(round(2.0 * c["step_time"] * FPS)))
    last_q = {s: np.zeros(3) for s in "LR"}
    # A pivot is never a foot marker: own-axis rotation fixes it exactly.  The
    # sole proxy is the lowest tenth of vertices owned by each ankle band. This
    # is a reproducible mesh measurement and it moves under the whole JNT3 LBS
    # law, including the ankle's own frame.
    sole = {}
    for side in "LR":
        band = np.flatnonzero(pack.assign == ix[f"ankle_{side}"])
        if len(band) == 0:
            raise RuntimeError(f"empty ankle band: {side}")
        cut = np.quantile(rest[band, 1], 0.10)
        sole[side] = band[rest[band, 1] <= cut]
    def marker(theta_all: np.ndarray, side: str) -> np.ndarray:
        return pose_points(rest, pack, theta_all)[sole[side]].mean(axis=0)
    marker_rest = {side: marker(np.zeros(len(pack.names)), side) for side in "LR"}
    for fi in range(frames_n):
        phase = fi / frames_n
        theta = np.zeros(len(pack.names))
        for si, side in enumerate("LR"):
            # One support interval per leg; L and R are exactly half a stride apart.
            local = (phase + 0.5 * si) % 1.0
            hip, knee, ankle = (ix[f"{j}_{side}"] for j in ("hip", "knee", "ankle"))
            chain = np.array([hip, knee, ankle])
            # Forward = horizontal projection of the measured hip->sole vector.
            d = marker_rest[side] - pack.pivot[hip]; d[1] = 0.0
            fwd = d / max(np.linalg.norm(d), 1e-12)
            up = np.array([0.0, 1.0, 0.0])
            # stance: planted foot moves backward relative to hip according to LIPM.
            # swing: minimum-jerk horizontal transfer plus sin^2 clearance (C1 at ends).
            if local < 0.5:
                tau = local * 2.0
                rel = -lipm_x(tau * c["step_time"], c)
                target = marker_rest[side] + fwd * rel
            else:
                u = (local - 0.5) * 2.0
                s = 10*u**3 - 15*u**4 + 6*u**5
                target = marker_rest[side] + fwd * ((-c["half_step"]) * (1-s) + c["half_step"]*s) \
                         + up * (CLEARANCE_FRACTION * leg * math.sin(math.pi*u)**2)
            def endpoint(q):
                tt = np.zeros(len(pack.names)); tt[chain] = q
                return marker(tt, side)
            lo = np.radians(pack.rom[chain, 0]); hi = np.radians(pack.rom[chain, 1])
            q = damped_ls(endpoint, target, last_q[side], lo, hi)
            last_q[side] = q; theta[chain] = q
            achieved = endpoint(q)
            all_err.append(float(np.linalg.norm(achieved - target)))
            for j, val in zip(chain, q): peaks[pack.names[j]] = max(peaks.get(pack.names[j], 0.0), abs(float(val)))
        theta_log.append(theta)
    rms = math.sqrt(float(np.mean(np.square(all_err))))
    print("joint_peaks_rad=" + ", ".join(f"{k}:{v:.6f}" for k,v in sorted(peaks.items())))
    print(f"foot_error_max={max(all_err):.6f} foot_error_rms={rms:.6f} world_units")
    dtheta = np.diff(np.vstack([theta_log, theta_log[0]]), axis=0)
    # Euler truncation |sin d-d|<=|d|^3/6 and |cos d-(1-d²/2)|<=d^4/24;
    # the conservative positional leading term is rho*d²/2 per hinge.
    rho = max(float(np.linalg.norm(marker_rest[s] - pack.pivot[ix[f"hip_{s}"]])) for s in "LR")
    e_frame = rho * np.max(np.sum(dtheta[:, [ix[f'{j}_{s}'] for s in 'LR' for j in ('hip','knee','ankle')]] ** 2, axis=1)) / 2.0
    n_need = max(1, math.ceil(math.sqrt(e_frame / (0.005 * h))))
    print(f"small_angle_per_frame_bound={e_frame:.8f} ({100*e_frame/h:.5f}% H) substeps_for_0.5pctH={n_need}; "
          "live engine exact-Rodrigues composition drift=0 for static theta evaluation")
    if max(all_err) > 0.005 * h:
        print("FALSIFIER FIRED: actual fixed-axis/ROM chain cannot meet 0.5% H target; do not integrate as a walk.")
    else:
        print("foot placement condition passes 0.5% H numerical threshold (visual/contact validation remains open).")


if __name__ == "__main__":
    main()