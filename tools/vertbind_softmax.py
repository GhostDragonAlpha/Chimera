"""vertbind_softmax.py -- seam route 2 (H4): bounded-falloff softmax travel
weights. Regenerates the /tick_vertbind payload with Gaussian softmax weights
over the vertex's OWN-LIMB pin candidates (W8's same-limb restriction kept,
the IDW^2 law replaced), writes the exact 15-byte-row payload file, measures
the E2 posed-surface crease metric before/after offline, and (--ab) runs the
A/B on a PRIVATE scratch engine (never the live world).

RULE 0 membrane (stated before the build):
  STATEMENT   the residual E2 crease (180 knee45 crease edges after W8, G7
              verified) is carried by the IDW^2 weight LAW: near the 3rd/4th
              in-limb ordering boundary a whole pivot weight (E2 measured
              0.17-0.26 of rotation weight) crosses a single vertex ring. A
              Gaussian softmax w_j ~ exp(-(d_j/lam)^2) over ALL in-limb
              candidates pushes the mass a set-flip can move across one ring
              below 1%: the 4th candidate pin carries <1% by derivation, so
              at any ordering boundary both sides bind the flipped pin at
              <=~1% and the shear step is bounded by that.
  PREDICTION  knee-region >10 deg introduced crease edges at knee45 drop
              MORE THAN HALF vs the W8 binding (180 -> < 90), and
              hip20+knee45 likewise (212 -> < 106); no tearing appears:
              zero pose-introduced inverted-winding faces, weights sum to 1
              in float32, the deg-0 blend returns the authored rest, and the
              posed knee crops deform smoothly (no gaps, no shading tear).
  FALSIFIER   crease edges do NOT drop >50% vs the W8 binding on either
              pose, OR any tear signature appears (introduced inverted
              faces > 0, rest-return failure, visible gap in the crops) ->
              the bounded-falloff law is REFUTED for this seam; the numbers
              are recorded honestly and the payload is NOT offered to the
              lead for the live world.

RULE 1 -- lam is DERIVED, not swept. The arithmetic (every quantity measured
from monkey_full.bin + the W8 in-limb candidate sets; --report prints it):
  requirement: the 4th-nearest candidate pin of EVERY vertex carries <1%
    of the softmax mass.  w4 = exp(-(d4/lam)^2)/Z and Z >= exp(-(d1/lam)^2)
    (the nearest-pin term alone), so a SUFFICIENT bound is
        exp(-(d4/lam)^2) <= 0.01 * exp(-(d1/lam)^2)
    <=>  (d4^2 - d1^2) / lam^2 >= ln(100) = 4.60517
    <=>  lam <= sqrt((d4^2 - d1^2) / 4.60517)          [per vertex]
  worst vertex over the mesh sets the bound:
        min_v(d4^2 - d1^2) = 0.057035   (vertex 15530, spine_lower region,
                                         four pins within 12.7%: d4/d1 1.127)
        lam_max = sqrt(0.057035 / 4.60517) = 0.11129 m
  with s = mean over vertices of the nearest-pin distance d1 (measured
  0.62992 m) and lam = c*s:
        c = lam_max / s = 0.11129 / 0.62992 = 0.17668
  --report then VERIFIES the bound post-hoc with the exact normalized
  softmax (max_v w4 < 1%) and reports the shipped truncation mass.

Hard format (MembraneTick::load_vertbind, membrane_tick.cpp:745): body is
[u32 n] then per vertex one 15-byte row = 3 pin indices (u8) + 3 weights
(f32, little-endian), 4 + n*15 bytes total (276889 for n=18459). The engine
consumes the weights RAW, so the shipped 3 slots are renormalized to sum 1.
"""
from __future__ import annotations

import argparse
import json
import shutil
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / ".tmp"
EVID = ROOT / "docs" / "evidence" / "agent_fleet" / "SHIP" / "E2_SEAM_SOFTMAX"
ENGINE = TMP / "build_tick" / "Release" / "chimera_engine.exe"
RUN_DIR = TMP / "vertbind_softmax_run"      # ISOLATED cwd (gallery pattern)
PORT = 8137                                 # PRIVATE: never 8107

# the derived constants (RULE 1, header arithmetic; --report re-measures and
# asserts the measured values match these before using them)
LAMBDA = 0.111288318
C_S = 0.17668                              # lam / s, s = 0.6299166
LN100 = np.log(100.0)


# -- mesh + metric machinery (verbatim methods of classify_run.py / W8) ----
def parse_full(path: Path):
    raw = path.read_bytes()
    n, ic = struct.unpack_from("<II", raw, 0)
    verts = np.frombuffer(raw, dtype=np.float32, count=n * 9,
                          offset=24).reshape(n, 9)
    idx = np.frombuffer(raw, dtype=np.uint32, count=ic,
                        offset=24 + n * 36).reshape(-1, 3)
    return verts, idx


def vert_normal_acc(pos: np.ndarray, idx: np.ndarray) -> np.ndarray:
    f = np.cross(pos[idx][:, 1] - pos[idx][:, 0],
                 pos[idx][:, 2] - pos[idx][:, 0])
    acc = np.zeros((len(pos), 3))
    for k in range(3):
        for d in range(3):
            acc[:, d] += np.bincount(idx[:, k], weights=f[:, d],
                                     minlength=len(pos))
    return acc


def unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v, axis=1, keepdims=True)
    n[n < 1e-12] = 1.0
    return v / n


def ang(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.degrees(np.arccos(np.clip((a * b).sum(1), -1, 1)))


def posed(pos: np.ndarray, pins: np.ndarray, order: np.ndarray,
          w: np.ndarray, deg: np.ndarray) -> np.ndarray:
    """MembraneTick::apply_travel in numpy (same arithmetic path)."""
    pv = pins[order]
    b = pos[:, None, :] - pv
    th = deg[order]
    c, s = np.cos(th), np.sin(th)
    return np.stack([
        (w * (b[:, :, 0] + pv[:, :, 0])).sum(1),
        (w * (b[:, :, 1] * c - b[:, :, 2] * s + pv[:, :, 1])).sum(1),
        (w * (b[:, :, 1] * s + b[:, :, 2] * c + pv[:, :, 2])).sum(1)], 1)


def pin_key(order3: np.ndarray, npins: int) -> np.ndarray:
    s = np.sort(order3.astype(np.int64), axis=1)
    return (s[:, 0] * npins + s[:, 1]) * npins + s[:, 2]


def flip_band(key: np.ndarray, edges: np.ndarray, nv: int) -> np.ndarray:
    band = np.zeros(nv, dtype=bool)
    diff = key[edges[:, 0]] != key[edges[:, 1]]
    band[edges[diff].ravel()] = True
    return band


def limb_graph(pos, idx, pins, tri_joint, sane):
    """W8's limb derivation: vertex inherits its triangles' joint; the limb
    is that joint's cell group plus the groups that touch it (edge-adjacent
    sane faces only).  Returns (vjoint, limb_of, d2v, order_all)."""
    nv = len(pos)
    npins = len(pins)
    edge_faces = defaultdict(list)
    for t in range(len(idx)):
        a, b, c = idx[t]
        for e in ((a, b), (b, c), (c, a)):
            edge_faces[(min(e), max(e))].append(t)
    touches = defaultdict(set)
    for e, ts in edge_faces.items():
        if len(ts) == 2 and sane[ts[0]] and sane[ts[1]]:
            x, y = int(tri_joint[ts[0]]), int(tri_joint[ts[1]])
            if x != y:
                touches[x].add(y)
                touches[y].add(x)
    votes = np.zeros((nv, npins), np.int32)
    votes[idx.ravel(), np.repeat(tri_joint, 3)] = 1
    tied = votes == votes.max(axis=1, keepdims=True)
    d2v = ((pos[:, None, :] - pins[None, :, :]) ** 2).sum(axis=2)
    vjoint = np.where(tied, d2v, np.inf).argmin(axis=1)
    limb_of = [{j} | touches[j] for j in range(npins)]
    order_all = np.argsort(d2v, axis=1)
    return vjoint, limb_of, d2v, order_all, edge_faces


def w8_binding(nv, npins, vjoint, limb_of, d2v, order_all):
    """The SHIPPED W8 binding (same-limb idw2 top-3, 0.25 fill cap),
    verbatim arithmetic of tools/classify_run.py. Returns (order, w64)."""
    order_new = np.empty((nv, 3), dtype=np.int64)
    w_new = np.empty((nv, 3), dtype=np.float64)
    for v in range(nv):
        limb = limb_of[vjoint[v]]
        rank = order_all[v]
        chosen = [int(p) for p in rank if p in limb][:3]
        if len(chosen) < 3:
            for p in rank:
                if p not in limb:
                    chosen.append(int(p))
                    if len(chosen) == 3:
                        break
        d3 = d2v[v, chosen]
        raw = 1.0 / (d3 + 1e-6) ** 2
        is_in = np.fromiter((p in limb for p in chosen), dtype=bool, count=3)
        raw64 = raw.astype(np.float64)
        s_in = raw64[is_in].sum()
        s_out = raw64[~is_in].sum()
        if s_in > 0 and s_out / (s_in + s_out) > 0.25:
            w = np.where(is_in, raw64 * (0.75 / s_in), raw64 * (0.25 / s_out))
        else:
            w = raw64 / raw64.sum()
        order_new[v] = chosen
        w_new[v] = w
    return order_new, w_new


def softmax_binding(nv, npins, vjoint, limb_of, d2v, order_all, lam):
    """Route 2: Gaussian softmax over ALL own-limb candidates (out-of-limb
    fill only where the limb is too small, W8's combined 0.25 cap kept),
    truncated to the top-3 BY WEIGHT and renormalized to sum 1 (the 15-byte
    row has exactly 3 slots). Returns (order, w64, diag)."""
    order_new = np.zeros((nv, 3), dtype=np.int64)
    w_new = np.zeros((nv, 3), dtype=np.float64)
    diag = {"fill": 0, "capped": 0, "trunc_mass_max": 0.0, "w4_max": 0.0}
    for v in range(nv):
        limb = limb_of[vjoint[v]]
        rank = order_all[v]
        cand = [int(p) for p in rank if p in limb]
        is_in = [True] * len(cand)
        while len(cand) < 3:               # chain ends: fill out of limb
            for p in rank:
                if p not in cand:
                    cand.append(int(p))
                    is_in.append(False)
                    if len(cand) >= 3:
                        break
        if not all(is_in):
            diag["fill"] += 1
        d = np.sqrt(d2v[v, cand].astype(np.float64))
        e = np.exp(-((d / lam) ** 2))
        z = e.sum()
        if len(cand) >= 4:
            diag["w4_max"] = max(diag["w4_max"], float(e[3] / z))
        sm = e / z
        in_m = np.array(is_in)
        s_in = sm[in_m].sum()
        s_out = sm[~in_m].sum()
        if s_in > 0 and s_out / (s_in + s_out) > 0.25:
            diag["capped"] += 1
            sm = np.where(in_m, sm * (0.75 / s_in), sm * (0.25 / s_out))
        top = np.argsort(-sm, kind="stable")[:3]     # top-3 BY WEIGHT
        trunc = 1.0 - float(sm[top].sum())
        diag["trunc_mass_max"] = max(diag["trunc_mass_max"], trunc)
        order_new[v] = np.asarray(cand)[top]
        w_new[v] = sm[top] / sm[top].sum()
    return order_new, w_new, diag


def crease_metric(pos64, pins64, idx, region, nd0, order, w64, npins,
                  KNEE, HIP, ef):
    """E2/W8 posed-surface crease metric: interior sane edges in the knee
    region, introduced vertex-normal delta > 10 deg at knee45 / hip20+knee45."""
    out = {}
    for pose, degv in (("knee45", {KNEE: 45.0}),
                       ("hip20+knee45", {KNEE: 45.0, HIP: 20.0})):
        deg = np.zeros(npins)
        for j, d in degv.items():
            deg[j] = np.radians(d)
        pp = posed(pos64, pins64, order, w64, deg)
        acc = unit(vert_normal_acc(pp, idx))
        intro = np.maximum(0, ang(acc[ef[:, 0]], acc[ef[:, 1]]) - nd0)
        # tear proxy: sane faces whose winding flips vs the rest field
        f_rest = np.cross(pos64[idx][:, 1] - pos64[idx][:, 0],
                          pos64[idx][:, 2] - pos64[idx][:, 0])
        f_pos = np.cross(pp[idx][:, 1] - pp[idx][:, 0],
                         pp[idx][:, 2] - pp[idx][:, 0])
        sane = 0.5 * np.linalg.norm(f_rest, axis=1) > 1e-8
        flips = int(((f_rest * f_pos).sum(1)[sane] < 0).sum())
        out[pose] = {"crease": int((region & (intro > 10)).sum()),
                     "max_deg": float(intro[region].max()),
                     "winding_flips": flips}
    return out


# -- scratch engine (private port, isolated cwd; gallery pattern) -----------
def post(base: str, path: str, body: bytes | str, timeout: int = 300) -> dict:
    data = body.encode() if isinstance(body, str) else body
    req = urllib.request.Request(base + path, data=data, method="POST",
                                 headers={"Content-Type":
                                          "application/octet-stream"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def get_json(base: str, path: str, timeout: int = 60) -> dict:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return json.loads(r.read().decode())


def get_bytes(base: str, path: str, timeout: int = 120) -> bytes:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return r.read()


class ScratchEngine:
    """Throwaway engine on a PRIVATE port. Boot is the gallery's measured
    pattern: ISOLATED cwd holding its own shaders copy, so the tick is born
    EMPTY (the --no-restore semantics) without --no-restore itself, which
    fail-fasts at boot on this build when combined with --hidden
    (measured 2/2, tools/gallery/run_gallery.py). The LIVE world at 8107 is
    never touched."""

    def __init__(self, port: int):
        self.port = port
        self.base = f"http://127.0.0.1:{port}"
        self.proc = None
        self.log_path = RUN_DIR / f"engine_{port}.log"

    def start(self, wait_s: float = 90.0):
        assert ENGINE.is_file(), f"engine binary missing: {ENGINE}"
        RUN_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copytree(ENGINE.parent / "shaders", RUN_DIR / "shaders",
                        dirs_exist_ok=True)
        logf = open(self.log_path, "ab")
        self.proc = subprocess.Popen(
            [str(ENGINE), str(self.port), "--hidden"],
            cwd=str(RUN_DIR), stdout=logf, stderr=logf,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        deadline = time.time() + wait_s
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(f"engine exited at boot "
                                   f"(code {self.proc.returncode})")
            try:
                st = get_json(self.base, "/tick_state", timeout=2)
                assert st.get("sealed") is not True, "booted SEALED?!"
                time.sleep(1.0)
                return
            except (urllib.error.URLError, OSError):
                time.sleep(0.5)
        raise RuntimeError("engine did not answer")

    def kill(self):
        if self.proc is not None and self.proc.poll() is None:
            subprocess.run(["taskkill", "/F", "/T", "/PID",
                            str(self.proc.pid)], capture_output=True)
            self.proc.wait(timeout=15)


def save_bookmark(base: str, name: str, radius, theta, phi, tgt, pan=(0, 0)):
    v = [radius, theta, phi, tgt[0], tgt[1], tgt[2], pan[0], pan[1]]
    return post(base, "/cameras", json.dumps(
        {"op": "save", "name": name,
         "v": [float(x) for x in v]}))


# -- main -------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true",
                    help="offline: derivation + metric + payload write")
    ap.add_argument("--ab", action="store_true",
                    help="scratch-engine A/B with captures (port 8137)")
    ap.add_argument("--ship", metavar="BASE",
                    help="POST the payload to BASE /tick_vertbind only")
    args = ap.parse_args()
    if not (args.report or args.ab or args.ship):
        args.report = True

    joints = json.loads((TMP / "joints28.json").read_text())
    names = [j["name"] for j in joints]
    pins = np.asarray([j["J"] for j in joints], dtype=np.float32)
    npins = len(pins)
    KNEE, HIP = names.index("knee_L"), names.index("hip_L")

    verts, idx = parse_full(TMP / "monkey_full.bin")
    pos = verts[:, 0:3].astype(np.float32)
    idx = idx.astype(np.int64)
    nv = len(pos)
    pos64 = pos.astype(np.float64)
    pins64 = pins.astype(np.float64)

    # per-triangle CA types: nearest measured joint to the centroid
    # (float32 -- byte-identical to the shipped classification)
    centroids = pos[idx].mean(axis=1)
    d2t = ((centroids[:, None, :] - pins[None, :, :]) ** 2).sum(axis=2)
    tri_joint = d2t.argmin(axis=1).astype(np.uint8)
    sane = 0.5 * np.linalg.norm(np.cross(pos[idx][:, 1] - pos[idx][:, 0],
                                         pos[idx][:, 2] - pos[idx][:, 0]),
                                axis=1) > 1e-8

    vjoint, limb_of, d2v, order_all, edge_faces = \
        limb_graph(pos, idx, pins, tri_joint, sane)

    # ---- RULE 1: re-measure the derivation inputs, assert they match -----
    gaps = np.full(nv, np.inf)
    for v in range(nv):
        limb = limb_of[vjoint[v]]
        rank = order_all[v]
        cand = ([int(p) for p in rank if p in limb]
                + [int(p) for p in rank if p not in limb])
        if len(cand) >= 4:
            d = np.sqrt(d2v[v, cand[:4]].astype(np.float64))
            gaps[v] = d[3] ** 2 - d[0] ** 2
    s = np.sqrt(d2v[np.arange(nv), order_all[:, 0]].astype(np.float64)).mean()
    lam_max = np.sqrt(gaps.min() / LN100)
    c_meas = lam_max / s
    print("== lambda derivation (RULE 1, measured now) ==")
    wv = int(gaps.argmin())
    dv = np.sqrt(d2v[wv, order_all[wv, :4]].astype(np.float64))
    print(f"  min_v(d4^2-d1^2) = {gaps.min():.6f}   (worst vertex {wv}, "
          f"d4/d1 = {dv[3]/dv[0]:.3f})")
    print(f"  ln(100) = {LN100:.5f}")
    print(f"  lam_max = sqrt(min_gap/ln100) = {lam_max:.9f} m")
    print(f"  s = mean nearest-pin distance = {s:.7f} m")
    print(f"  c = lam_max/s = {c_meas:.5f}")
    assert abs(lam_max - LAMBDA) < 1e-6 and abs(c_meas - 0.17668) < 1e-4, \
        "measured derivation drifted from the header constants -- STOP"
    lam = LAMBDA
    print(f"  DERIVED lam = {lam:.9f} m  (c*s form: c={c_meas:.5f} x s)")

    # ---- the three bindings ----------------------------------------------
    order_old = order_all[:, :3]                       # pre-W8 (reference)
    d3o = np.take_along_axis(d2v, order_old, axis=1)
    w_old = 1.0 / (d3o + 1e-6) ** 2
    w_old /= w_old.sum(axis=1, keepdims=True)

    order_w8, w_w8 = w8_binding(nv, npins, vjoint, limb_of, d2v, order_all)
    order_sm, w_sm, diag = softmax_binding(nv, npins, vjoint, limb_of,
                                           d2v, order_all, lam)

    # ---- hard constraints on the NEW binding ------------------------------
    w32 = w_sm.astype(np.float32)
    sum_err = np.abs(w32.astype(np.float64).sum(1) - 1.0).max()
    deg0 = np.zeros(npins)
    rest_err = np.abs(posed(pos64, pins64, order_sm, w32.astype(np.float64),
                            deg0) - pos64).max()
    print("\n== hard constraints (NEW binding) ==")
    print(f"  float32 weight-sum max|sum-1|: {sum_err:.3e}")
    print(f"  deg-0 blend rest error (max m): {rest_err:.3e}")
    print(f"  softmax w4 max (exact, normalized): {diag['w4_max']:.6f} "
          f"(bound: < 0.01)")
    print(f"  shipped top-3 truncation mass max: {diag['trunc_mass_max']:.6f}")
    print(f"  fill verts: {diag['fill']}  (combined cap hit: {diag['capped']})")
    ok = (sum_err < 1e-6 and rest_err < 1e-6 and diag["w4_max"] < 0.01)
    print(f"  -> {'PASS' if ok else 'FAIL'}")

    # ---- E2 crease metric, W8's method ------------------------------------
    e = np.concatenate([idx[:, [0, 1]], idx[:, [1, 2]], idx[:, [2, 0]]])
    edges = np.unique(np.sort(e, axis=1), axis=0)
    interior = {e_: fs for e_, fs in edge_faces.items() if len(fs) == 2}
    ef = np.array(list(interior.keys()))
    ft = np.array([interior[(a, b)] for a, b in ef])
    edge_sane = sane[ft[:, 0]] & sane[ft[:, 1]]
    mid = (pos64[ef[:, 0]] + pos64[ef[:, 1]]) / 2
    region = (np.linalg.norm(mid - pins64[KNEE], axis=1) < 1.5) & edge_sane
    acc0 = unit(vert_normal_acc(pos64, idx))
    nd0 = ang(acc0[ef[:, 0]], acc0[ef[:, 1]])

    print("\n== E2 posed-surface crease metric (knee region, >10 deg) ==")
    res = {}
    for label, order, w in (("pre-W8 (reference)", order_old, w_old),
                            ("W8 (shipped OLD)", order_w8, w_w8),
                            ("SOFTMAX (NEW)", order_sm, w32.astype(np.float64))):
        res[label] = crease_metric(pos64, pins64, idx, region, nd0,
                                   order, w, npins, KNEE, HIP, ef)
        r = res[label]
        print(f"  {label:20s} knee45: {r['knee45']['crease']:4d} "
              f"(max {r['knee45']['max_deg']:.1f} deg, flips "
              f"{r['knee45']['winding_flips']}) | hip20+knee45: "
              f"{r['hip20+knee45']['crease']:4d} (max "
              f"{r['hip20+knee45']['max_deg']:.1f} deg, flips "
              f"{r['hip20+knee45']['winding_flips']})")
    old_n = res["W8 (shipped OLD)"]["knee45"]["crease"]
    new_n = res["SOFTMAX (NEW)"]["knee45"]["crease"]
    old_c = res["W8 (shipped OLD)"]["hip20+knee45"]["crease"]
    new_c = res["SOFTMAX (NEW)"]["hip20+knee45"]["crease"]
    drop1, drop2 = 1 - new_n / old_n, 1 - new_c / old_c
    print(f"  drop vs W8: knee45 {100*drop1:.1f}% | hip20+knee45 {100*drop2:.1f}%"
          f"  (falsifier bar: >50% both)")
    flips_new = (res["SOFTMAX (NEW)"]["knee45"]["winding_flips"]
                 - res["pre-W8 (reference)"]["knee45"]["winding_flips"],
                 res["SOFTMAX (NEW)"]["hip20+knee45"]["winding_flips"]
                 - res["pre-W8 (reference)"]["hip20+knee45"]["winding_flips"])
    print(f"  pose-introduced winding flips (softmax vs rest): "
          f"knee45 {flips_new[0]}, compound {flips_new[1]}")

    verdict = bool(drop1 > 0.5 and drop2 > 0.5 and ok
                   and max(flips_new) == 0)
    print(f"\n  OFFLINE FALSIFIER VERDICT: "
          f"{'LAW HELD' if verdict else 'LAW REFUTED'}")

    # ---- flip bands + duplicates (W8 report parity) ------------------------
    key_w8 = pin_key(order_w8, npins)
    key_sm = pin_key(order_sm, npins)
    band_w8 = flip_band(key_w8, edges, nv)
    band_sm = flip_band(key_sm, edges, nv)
    _, invu = np.unique(pos, axis=0, return_inverse=True)
    gsize = npins ** 3

    def split_groups(key):
        first = np.unique(invu.astype(np.int64) * gsize + key) // gsize
        _, cnt = np.unique(first, return_counts=True)
        return int((cnt > 1).sum())
    print(f"\n  flip-band verts: W8 {int(band_w8.sum())} -> "
          f"softmax {int(band_sm.sum())} / {nv}")
    print(f"  duplicate-position groups with split bindings: "
          f"W8 {split_groups(key_w8)}, softmax {split_groups(key_sm)}")

    # ---- payload file: the exact /tick_vertbind body -----------------------
    EVID.mkdir(parents=True, exist_ok=True)
    body = (struct.pack("<I", nv)
            + np.concatenate([order_sm.astype(np.uint8),
                              w32.view(np.uint8).reshape(nv, 12)],
                             axis=1).tobytes())
    assert len(body) == 4 + nv * 15
    payload_path = EVID / "vertbind_softmax_payload.bin"
    payload_path.write_bytes(body)
    (TMP / "vertbind_softmax_payload.bin").write_bytes(body)
    print(f"\n  payload written: {payload_path} ({len(body)} bytes)")
    metrics = {"lambda": lam, "c": c_meas, "s": float(s),
               "min_gap": float(gaps.min()),
               "w4_max": diag["w4_max"], "trunc_mass_max":
                   diag["trunc_mass_max"], "fill": diag["fill"],
               "capped": diag["capped"], "sum_err": float(sum_err),
               "rest_err": float(rest_err), "metric": res,
               "drop_knee45": float(drop1),
               "drop_compound": float(drop2),
               "flip_band_w8": int(band_w8.sum()),
               "flip_band_softmax": int(band_sm.sum()),
               "dup_splits_w8": split_groups(key_w8),
               "dup_splits_softmax": split_groups(key_sm),
               "offline_verdict": "HELD" if verdict else "REFUTED"}
    (EVID / "metrics.json").write_text(json.dumps(metrics, indent=2),
                                       encoding="utf-8")
    if args.ship:
        base = args.ship
        print("vertbind:", post(base, "/tick_vertbind", body, timeout=120))
        return 0

    if not args.ab:
        return 0

    # ---- scratch-engine A/B with captures ----------------------------------
    # Every frame is GATED by a verified pose: /verts must match the offline
    # predicted displacement (the engine is float32, allow 2 mm) before the
    # frame is grabbed -- a stale or lost pose post can then never ship.
    print(f"\n== scratch engine A/B on 127.0.0.1:{PORT} (live world 8107 "
          f"untouched) ==")
    knee_ids = np.where(np.linalg.norm(pos64 - pins64[KNEE], axis=1) < 0.35)[0]
    deg_ab = np.zeros(npins)
    deg_ab[KNEE] = np.radians(45)
    deg_ab[HIP] = np.radians(20)

    def predicted(order, w):
        pp = posed(pos64, pins64, order, w, deg_ab)
        return float(np.linalg.norm(pp[knee_ids] - pos64[knee_ids],
                                    axis=1).max())
    pred = {"old": predicted(order_w8, w_w8.astype(np.float32)
                             .astype(np.float64)),
            "new": predicted(order_sm, w32.astype(np.float64))}

    eng = ScratchEngine(PORT)
    eng.start()
    shots = {}
    ab_log = {}
    try:
        base = eng.base
        mesh = (TMP / "monkey_full.bin").read_bytes()
        print("mesh:", post(base, "/mesh_bin", mesh, timeout=300))
        pins_body = struct.pack("<I", npins) \
            + np.ascontiguousarray(pins).tobytes()
        print("joints:", post(base, "/tick_joints", pins_body))
        print("classify:", post(base, "/tick_classify",
                                struct.pack("<I", len(tri_joint))
                                + tri_joint.tobytes()))

        # camera derived from geometry: eye on the +x normal of the knee pin
        # (orbit: eye = target + r*(cos(phi)sin(theta), sin(phi), cos(phi)cos
        # (theta)); theta=pi/2 puts the eye on +x), slightly above.
        tgt = pins64[KNEE]
        print("camera:", save_bookmark(base, "h4knee", 0.6, np.pi / 2,
                                       0.15, tgt))

        def live_disp():
            b = get_bytes(base, "/verts")
            n = struct.unpack_from("<I", b, 0)[0]
            lv = np.frombuffer(b, np.float32, n * 9, 4).reshape(n, 9)[:, 0:3]
            return float(np.linalg.norm(lv[knee_ids] - pos64[knee_ids],
                                        axis=1).max())

        def pose_capture(tag, vb_body):
            print(f"vertbind({tag}):", post(base, "/tick_vertbind", vb_body,
                                            timeout=120))
            for jdeg in ((HIP, 0), (KNEE, 0)):
                post(base, "/tick_pose",
                     json.dumps({"joint_index": jdeg[0], "deg": jdeg[1]}))
            time.sleep(0.7)
            rest_d = live_disp()
            r1 = post(base, "/tick_pose", json.dumps({"joint_index": HIP,
                                                      "deg": 20}))
            r2 = post(base, "/tick_pose", json.dumps({"joint_index": KNEE,
                                                      "deg": 45}))
            assert r1.get("ok") and r2.get("ok"), f"pose refused {r1} {r2}"
            obs = rest_d
            for _ in range(20):                # verified pose: <= 10 s wait
                time.sleep(0.5)
                obs = live_disp()
                if abs(obs - pred[tag]) < 0.002:
                    break
            assert abs(obs - pred[tag]) < 0.002, \
                f"pose never verified: obs {obs:.4f} vs pred {pred[tag]:.4f}"
            post(base, "/cameras", json.dumps({"op": "recall",
                                               "name": "h4knee"}))
            time.sleep(0.5)
            png = get_bytes(base, "/frame?w=1280", timeout=120)
            assert png[:8] == b"\x89PNG\r\n\x1a\n", "no PNG from /frame"
            p = EVID / f"knee45_{tag}.png"
            p.write_bytes(png)
            ab_log[tag] = {"pred_disp": pred[tag], "observed_disp": obs,
                           "rest_disp": rest_d, "png_bytes": len(png)}
            print(f"  capture {tag}: disp pred {pred[tag]:.4f} obs {obs:.4f}"
                  f" (rest {rest_d:.6f}) -> {p.name}")
            return p

        # OLD arm: the W8 binding, exact 15-byte rows, posted FIRST
        old_body = (struct.pack("<I", nv)
                    + np.concatenate(
                        [order_w8.astype(np.uint8),
                         w_w8.astype(np.float32).view(np.uint8)
                         .reshape(nv, 12)], axis=1).tobytes())
        assert len(old_body) == 4 + nv * 15
        shots["old"] = pose_capture("old", old_body)
        shots["new"] = pose_capture("new", body)

        st = get_json(base, "/tick_state")
        (EVID / "tick_state_after.json").write_text(
            json.dumps(st, indent=2), encoding="utf-8")
    finally:
        eng.kill()
    metrics["ab"] = ab_log
    (EVID / "metrics.json").write_text(json.dumps(metrics, indent=2),
                                       encoding="utf-8")

    # crops: same box both frames, knee pin projected near center of frame
    try:
        from PIL import Image
        for tag in ("old", "new"):
            im = Image.open(shots[tag])
            w, h = im.size
            box = (int(w * 0.30), int(h * 0.25), int(w * 0.75), int(h * 0.80))
            im.crop(box).save(EVID / f"knee45_{tag}_crop.png")
        print("crops written")
    except ImportError:
        print("PIL unavailable -- full frames stand as the crops")

    print("\nAB captures in", EVID)
    return 0


if __name__ == "__main__":
    sys.exit(main())
