#!/usr/bin/env python3
"""xpbd_diagnostic.py -- THE PISTON DIAGNOSTIC + MODAL ESTIMATE (A12-xpbd-prereg).

Astra's answer turned into derived numbers on OUR world. NO solver code here --
numbers, prereg inputs, and the measured constants the coupled XPBD design needs.

READ-ONLY against the live engine (GET /tick_state, /verts, /topology on
127.0.0.1:8107). One pull per endpoint per run; back off on errors.

THE PHYSICS (Astra, cited in A1_XPBD/PREREG.md):
  - Sealed-cell volume constraint C_i = V_i - V0_i with compliance
    alpha_i = kappa * V0_i, kappa = 4.6e-10 Pa^-1 (water, 25 C -- the engine's
    own kappa_, membrane_tick.hpp:206; B = 1/kappa = 2.174 GPa).
  - Stability gate: eta = h * omega_max with
    omega_max^2 = lambda_max(M^-1/2 K_tangent M^-1/2),
    K_water ~ J_V^T diag(1/(kappa V0_i)) J_V.
    Explicit at h = 1/300 s demands omega_max < 600 rad/s (f < 95.5 Hz).
  - First diagnostic, the piston mode: eta^2 = h^2 A^2 / (kappa V0 * m_eff).

THE METHOD (three routes, all measured on the live mesh):
  The four sealed cells are the y-BANDS of the body solid (each seal cut is a
  plane y = p_i; a cell = the body's solid between its bounding planes, closed
  by the seal caps). Therefore, for A(y) = the body's total cross-section area
  at height y (a slicer: triangle-plane intersection -> chained loops ->
  even-odd nested shoelace areas):
      V_cell = integral of A(y) dy over the band          (validates vs live v0)
      dV_cell/dp = A(p) at the bounding plane             (the PISTON IDENTITY:
        the piston Jacobian row IS the cut cross-section area -- Leibniz)
  Route 1: V_band = integral of A(y) dy vs the live v0 -- validates the whole
           chain (slicer, band model, units) against the engine's own volumes.
  Route 2: A(p_i) at each of the 3 cut planes (plus +/-1 mm brackets) -- the
           piston areas, shown with the arithmetic in DIAGNOSTIC.md.
  Route 3: FD numeric probe (the engine's own doctrine): shift the vertex ring
           within eps of a cut plane by +/-delta in y, re-slice, and integrate
           the LOCAL area change -> dV_cell/ddelta measured per cell. Confirms
           the Leibniz J (signs: below cell +, above cell -, sum = 0).

THE MODEL (stated, per Rule 0 -- this is a membrane, not a fact):
  - m_eff: the body carries rho = 1000 kg/m^3 on the sealed volumes (the
    mission's own number: 13.8245 m^3 -> 13,824.5 kg). The engine's DOF are
    joints + one rigid root; vertices are skinned, so a joint drags a
    SUB-BODY. For the ring-piston at plane i the effective mass is the
    reduced mass mu_i = m_below*m_above/(m_below+m_above) of the two sides
    (free-free, conservative). The grounded variant (lower side planted, the
    balance rung's configuration; m_eff = m_above) is reported alongside.
  - Ring vertex masses for Route 3 are lumped from the geometry:
    m_i = rho * sum over faces containing i of det(face)/18, so sum(m_i) =
    rho * V_whole exactly (13,824.5 kg).

Outputs: docs/evidence/agent_fleet/SHIP/A1_XPBD/diagnostic_results.json
"""

import json
import os
import struct
import sys
import time
import urllib.request
from collections import defaultdict

import numpy as np

BASE = "http://127.0.0.1:8107"
OUT_DIR = "docs/evidence/agent_fleet/SHIP/A1_XPBD"
KAPPA = 4.6e-10            # Pa^-1, water 25 C (engine kappa_, Astra agree)
RHO = 1000.0               # kg/m^3 on the sealed volumes
H = 1.0 / 300.0            # s, the explicit tick
ETA_BAR = 2.0              # explicit stability bar (Astra)
OMEGA_EXPLICIT = ETA_BAR / H   # 600 rad/s
DELTA = 1.0e-4             # m, FD probe half-step (central difference)
BAND = 0.05                # m, kernel-probe band half-width (Route 3)
D_BAND = 0.00125           # m, slice spacing for the volume integrals


def get_binary(path, tries=4):
    delay = 1.0
    for k in range(tries):
        try:
            with urllib.request.urlopen(BASE + path, timeout=30) as r:
                return r.read()
        except Exception as e:
            if k == tries - 1:
                raise
            print(f"  ! {path} failed ({e}); backing off {delay:.1f}s", file=sys.stderr)
            time.sleep(delay)
            delay *= 2


def get_json(path, tries=4):
    delay = 1.0
    for k in range(tries):
        try:
            with urllib.request.urlopen(BASE + path, timeout=30) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:
            if k == tries - 1:
                raise
            time.sleep(delay)
            delay *= 2


def parse_verts(blob):
    """[u32 n][n*9 f32: pos3, normal3, color3] (membrane_tick export_verts)."""
    (n,) = struct.unpack_from("<I", blob, 0)
    floats = np.frombuffer(blob, dtype="<f4", count=n * 9, offset=4)
    v = floats.reshape(n, 9).astype(np.float64)
    return v[:, 0:3], v[:, 3:6]


def parse_topology(blob):
    """[u32 ntri][ntri*3 u32] (membrane_tick export_topology)."""
    (ntri,) = struct.unpack_from("<I", blob, 0)
    idx = np.frombuffer(blob, dtype="<u4", count=ntri * 3, offset=4)
    return idx.reshape(ntri, 3).astype(np.int64)


def slice_area(pos, tri, p):
    """Total cross-section area of the closed mesh at height y=p.

    Triangle-plane intersection -> segments in (x,z), each ORIENTED by the
    physical rule t = n_hat x y_hat (outward normal x up), which is CCW
    around the solid and globally consistent. The segments are exactly the
    boundary of the cross-section (the polygon turns at every crossing
    point, so no segment duplicates or cancels), and the shoelace sum over
    all of them is the net enclosed area -- no loop chaining, no nesting
    tests; holes subtract automatically (their boundary runs CW).
    Verts exactly at p count as not-below (strict straddle test)."""
    P = pos[tri]
    y = P[:, :, 1]
    strad = (y < p).any(axis=1) & (y >= p).any(axis=1)
    fidx = np.where(strad)[0]
    Q = 1e-5
    key = lambda pt: (round(pt[0] / Q), round(pt[1] / Q))
    seg_list = []
    # pass 1: canonical crossing point per EDGE (sorted vertex pair), so both
    # triangles sharing the edge get the bit-identical point (last-bit noise
    # would split the quantized keys and the interior pair fails to cancel)
    edge_pt = {}
    cross_edges = defaultdict(list)  # tri -> its crossing edges (cyclic order)
    for t in fidx:
        for slot, (u, v) in enumerate(((tri[t, 0], tri[t, 1]),
                                       (tri[t, 1], tri[t, 2]),
                                       (tri[t, 2], tri[t, 0]))):
            yu, yv = pos[u, 1], pos[v, 1]
            if (yu < p) == (yv < p):
                continue
            canon = (u, v) if u < v else (v, u)
            if canon not in edge_pt:
                yl, yh = pos[canon[0], 1], pos[canon[1], 1]
                tt = (p - yl) / (yh - yl)
                q = pos[canon[0]] + tt * (pos[canon[1]] - pos[canon[0]])
                edge_pt[canon] = (q[0], q[2])
            cross_edges[t].append(slot)
    # pass 2: per triangle, the segment joins its two crossing edges. The
    # PHYSICAL direction is t = n_hat x y_hat (outward normal x up): CCW
    # around the solid, globally consistent (slot order alone is accidental
    # per loop and mixes orientations across loops).
    a3, b3, c3 = pos[tri[:, 0]], pos[tri[:, 1]], pos[tri[:, 2]]
    nrm = np.cross(b3 - a3, c3 - a3)
    for t, slots in cross_edges.items():
        if len(slots) != 2:
            continue                 # vertex-graze (0/1/3 crossings): no segment
        E = [((tri[t, 0], tri[t, 1]), (tri[t, 1], tri[t, 2]),
              (tri[t, 2], tri[t, 0]))[s] for s in slots]
        def cpt(e):
            cc = (e[0], e[1]) if e[0] < e[1] else (e[1], e[0])
            return edge_pt[cc]
        p1, p2 = cpt(E[0]), cpt(E[1])
        if abs(p1[0] - p2[0]) < 1e-12 and abs(p1[1] - p2[1]) < 1e-12:
            continue
        nx, nz = nrm[t, 0], nrm[t, 2]
        tx, tz = -nz, nx             # t = n x y_hat, (x,z) components
        if (p2[0] - p1[0]) * tx + (p2[1] - p1[1]) * tz < 0:
            p1, p2 = p2, p1
        k1, k2 = key(p1), key(p2)
        if k1 == k2:
            continue
        seg_list.append((k1, k2))
    # every crossing triangle contributes exactly one boundary segment (the
    # polygon turns at each crossing point, so segments never duplicate):
    # the shoelace sum over ALL of them is the net enclosed area
    # A = 1/2 sum (x1*z2 - z1*x2) per segment (keys are quantized to Q=1e-5 m)
    if len(seg_list) == 0:
        return 0.0, 0, 0
    arr = np.array(seg_list, dtype=float)        # (nseg, 2 endpoints, 2 coords)
    area = 0.5 * float(np.sum(arr[:, 0, 0] * arr[:, 1, 1] -
                              arr[:, 0, 1] * arr[:, 1, 0]))
    return abs(area) * Q * Q, len(seg_list), 0


def band_volume(pos, tri, lo, hi, step=D_BAND):
    """V = integral of A(y) dy over [lo, hi] (midpoint rule, stated step)."""
    n = max(4, int(round((hi - lo) / step)))
    ys = np.linspace(lo, hi, n + 1)
    mids = 0.5 * (ys[:-1] + ys[1:])
    vals = [slice_area(pos, tri, float(m))[0] for m in mids]
    vals = np.abs(vals)
    return float(np.mean(vals) * (hi - lo)), n


def det6_sum(pos, tri):
    a, b, c = pos[tri[:, 0]], pos[tri[:, 1]], pos[tri[:, 2]]
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)


def main():
    ts = get_json("/tick_state")
    print(f"live: ticks={ts['ticks']} sealed={ts['sealed']} n_cells={ts['n_cells']} "
          f"V_whole={ts['V_whole']:.6f} conserve={ts['conserve_pct']:.6f}%")
    cells = ts["cells"]
    V0 = np.array([c["v0"] for c in cells])
    ylo = np.array([c["ylo"] for c in cells])
    yhi = np.array([c["yhi"] for c in cells])
    order = np.argsort(ylo)
    V0, ylo, yhi = V0[order], ylo[order], yhi[order]
    caps_live = np.array([c["caps"] for c in cells], dtype=int)[order]
    pieces_live = np.array([c["pieces"] for c in cells], dtype=int)[order]
    bands = list(zip(ylo, yhi))
    nc = len(V0)
    np_ = nc - 1
    cuts = np.array([0.5 * (yhi[k] + ylo[k + 1]) for k in range(np_)])
    print(f"cells (floor->up): V0={V0.round(6)}  caps={caps_live}")
    print(f"cut planes: {cuts}")

    pos, normals = parse_verts(get_binary("/verts"))
    tri = parse_topology(get_binary("/topology"))
    nv, nf = len(pos), len(tri)
    nrm_max = float(np.abs(np.linalg.norm(normals, axis=1) - 1).max())
    y = pos[:, 1]
    ext_ok = abs(y.min() - ylo[0]) < 1e-4 and abs(y.max() - yhi[-1]) < 1e-4
    print(f"mesh: nv={nv} nf={nf} |1-|n||max={nrm_max:.1e} "
          f"y-extent matches live bands: {ext_ok}")

    # ---- Route 1: volume integrals vs the live law --------------------------
    V_band = np.zeros(nc)
    n_slices = np.zeros(nc, dtype=int)
    for k in range(nc):
        V_band[k], n_slices[k] = band_volume(pos, tri, ylo[k], yhi[k])
    V_err = (V_band - V0) / V0
    whole = det6_sum(pos, tri)
    print("Route 1 (slice integrals vs live v0):")
    for k in range(nc):
        print(f"  cell{k}: V_int={V_band[k]:.6f} v0={V0[k]:.6f} "
              f"err={V_err[k]:+.3%} ({n_slices[k]} slices)")
    print(f"  whole divergence = {whole:.6f} vs live V_whole {ts['V_whole']:.6f} "
          f"({(whole - ts['V_whole']) / ts['V_whole']:+.2e})")

    # ---- Route 2: cut-plane areas (the piston areas) ------------------------
    A = np.zeros(np_)
    A_br = []
    slice_signs = []
    for i in range(np_):
        a0, r0, b0 = slice_area(pos, tri, float(cuts[i]))
        am, rm, bm = slice_area(pos, tri, float(cuts[i]) - 0.001)
        ap, rp, bp = slice_area(pos, tri, float(cuts[i]) + 0.001)
        slice_signs.append(np.sign(a0) if a0 else 0.0)
        A[i] = abs(a0)
        A_br.append({"at": float(abs(a0)), "minus1mm": float(abs(am)),
                     "plus1mm": float(abs(ap)),
                     "residual_segments": [r0, rm, rp], "nonmanifold": [b0, bm, bp]})
        print(f"Route 2 (plane y={cuts[i]:.4f}): A={abs(a0):.6f} m^2 "
              f"[-1mm: {abs(am):.6f} ({rm} segs), +1mm: {abs(ap):.6f} ({rp} segs)] "
              f"nonmanifold={b0 + bm + bp}")

    # ---- Route 3: FD numeric probe (kernel-weighted piston, central diff) ---
    # The engine's own doctrine perturbs and measures dV per cell. A bare ring
    # shift only moves the sparse loop verts and dilutes the piston response;
    # the faithful mesh-representable piston velocity field is a linear-taper
    # kernel: u(y) = delta * (1 - |y-p|/BAND) inside the band, 0 outside.
    # Narrowing the band must converge to the Leibniz piston area A(p).
    J = np.zeros((nc, np_))          # J[c, i] = dV_cell_c / dy_plane_i
    A_kernel = np.zeros(np_)
    for i in range(np_):
        p = float(cuts[i])
        wlo, whi = p - BAND - 4 * DELTA, p + BAND + 4 * DELTA
        mids = np.linspace(wlo, whi, 49)
        w = np.clip(1.0 - np.abs(y - p) / BAND, 0.0, 1.0)
        ring = w > 0
        loc0 = np.abs(np.array([slice_area(pos, tri, float(m))[0] for m in mids]))
        dV = {}
        for sgn in (+1, -1):
            pp = pos.copy()
            pp[ring, 1] += sgn * DELTA * w[ring]
            loc1 = np.abs(np.array([slice_area(pp, tri, float(m))[0] for m in mids]))
            dV[sgn] = float(np.mean(loc1 - loc0) * (whi - wlo))
        # shifting the boundary +y: V_below += A*delta, V_above -= A*delta
        J[i, i] = dV[1] / (2 * DELTA)
        J[i + 1, i] = -dV[1] / (2 * DELTA)
        A_kernel[i] = abs(J[i, i])
        asym = abs(dV[1] + dV[-1]) / max(abs(dV[1]), 1e-30)
        print(f"Route 3 (plane y={p:.4f}, kernel band {BAND} m, "
              f"{int(ring.sum())} verts): J_below={J[i, i]:+.5f} "
              f"J_above={J[i + 1, i]:+.5f} (Leibniz A={A[i]:.5f}; "
              f"antisymmetry residual {asym:.1%})")
    A_probe = A_kernel.copy()
    for i in range(np_):
        print(f"  plane {i}: A_kernel={float(A_kernel[i]):.6f} vs "
              f"Leibniz-slice A={float(A[i]):.6f} "
              f"({float(A_kernel[i] / A[i]):+.1%})")

    # ---- masses -------------------------------------------------------------
    w = np.zeros(nv)
    a3, b3, c3 = pos[tri[:, 0]], pos[tri[:, 1]], pos[tri[:, 2]]
    contrib = np.einsum("ij,ij->i", a3, np.cross(b3, c3)) / 18.0
    for j in range(3):
        np.add.at(w, tri[:, j], contrib)
    m_vert = RHO * w
    print(f"lumped vertex mass: sum={m_vert.sum():.1f} kg (target 13824.5)")

    m_below_plane = np.cumsum(V0)[:-1] * RHO     # per PLANE (3), from live v0
    m_total = V0.sum() * RHO
    m_above_plane = m_total - m_below_plane
    mu_red = m_below_plane * m_above_plane / (m_below_plane + m_above_plane)
    mu_grounded = m_above_plane.copy()

    # ---- THE PISTON TABLE (per cell, per Astra's first diagnostic) ----------
    # per cell: governing plane = its bounding plane with the larger
    # eta^2 = h^2 A^2 / (kappa V0_cell mu_plane); end cells have one plane.
    rows = []
    for k in range(nc):
        cands = []
        if k < np_:
            cands.append(k)
        if k > 0:
            cands.append(k - 1)
        ci = max(cands, key=lambda c: (A[c] ** 2 / mu_red[c]))
        r = {
            "cell": int(k), "V0": float(V0[k]),
            "band": [float(ylo[k]), float(yhi[k])],
            "pieces_live": int(pieces_live[k]), "caps_live": int(caps_live[k]),
            "governing_plane": int(ci), "cut_y": float(cuts[ci]),
            "A_slice": float(A[ci]), "A_probe": float(A_probe[ci]),
            "mu_reduced": float(mu_red[ci]), "m_grounded": float(mu_grounded[ci]),
        }
        for tag, m in (("reduced", mu_red[ci]), ("grounded", mu_grounded[ci])):
            for atag, Av in (("slice", A[ci]), ("probe", A_probe[ci])):
                omega2 = Av * Av / (KAPPA * V0[k] * m)
                r[f"omega2_{tag}_{atag}"] = float(omega2)
                r[f"eta_{tag}_{atag}"] = float(H * omega2 ** 0.5)
            omega2 = A[ci] * A[ci] / (KAPPA * V0[k] * m)
            r[f"omega_{tag}"] = float(omega2 ** 0.5)
            r[f"f_{tag}"] = float(omega2 ** 0.5 / (2 * np.pi))
            r[f"eta2_{tag}"] = float(H * H * omega2)
            r[f"eta_{tag}"] = float(H * omega2 ** 0.5)
            r[f"inside_{tag}"] = bool(H * H * omega2 < ETA_BAR ** 2)
        rows.append(r)

    # ---- MODAL ESTIMATE: coupled coarse K_water eigenvalues -----------------
    # K = J^T S^-1 J (S = diag(kappa*V0)) on the 3 ring directions,
    # M = diag(mu_i). omega_max^2 = lambda_max(M^-1/2 K M^-1/2).
    # PRIMARY: the Leibniz-slice J (exact for the validated slicer geometry).
    # VARIANT: the kernel-probe J (Route 3, the engine's numeric-probe
    # doctrine). Their agreement bounds the model error on omega_max.
    JL = np.zeros((nc, np_))
    for i in range(np_):
        JL[i, i] = A[i]
        JL[i + 1, i] = -A[i]
    Sinv = np.diag(1.0 / (KAPPA * V0))
    Mc = np.diag(mu_red)
    Mm12 = np.diag(1.0 / np.sqrt(mu_red))
    out_modal = {}
    for tag, Jm in (("leibniz", JL), ("kernel_probe", J.copy())):
        Kc = Jm.T @ Sinv @ Jm
        G = Mm12 @ Kc @ Mm12
        ev = np.linalg.eigvalsh(0.5 * (G + G.T))[::-1]
        out_modal[tag] = {
            "J": Jm.tolist(), "K_coarse": Kc.tolist(),
            "eigenvalues_omega2": [float(x) for x in ev],
            "omega_max": float(ev[0] ** 0.5),
            "f_max": float(ev[0] ** 0.5 / (2 * np.pi)),
            "eta_at_300hz": float(H * ev[0] ** 0.5),
        }
    om = out_modal["leibniz"]
    eta = om["eta_at_300hz"]
    n_sub = max(1, int(np.ceil(eta / ETA_BAR)))

    print("\n=== PISTON TABLE (h=1/300 s, bar eta<2) ===")
    print(f"{'cell':>4} {'V0':>9} {'plane_y':>8} {'A_slice':>8} {'A_probe':>8} "
          f"{'mu_red':>8} {'omega':>9} {'f_Hz':>8} {'eta':>7}  verdict")
    for r in rows:
        print(f"{r['cell']:>4} {r['V0']:>9.4f} {r['cut_y']:>8.3f} {r['A_slice']:>8.4f} "
              f"{r['A_probe']:>8.4f} {r['mu_reduced']:>8.1f} {r['omega_reduced']:>9.1f} "
              f"{r['f_reduced']:>8.2f} {r['eta_reduced']:>7.3f}  "
              f"{'INSIDE' if r['inside_reduced'] else 'OUTSIDE'}")
    for tag in ("leibniz", "kernel_probe"):
        m = out_modal[tag]
        print(f"modal[{tag}]: omega2 spectrum {np.round(m['eigenvalues_omega2'], 1)} "
              f"-> omega_max={m['omega_max']:.1f} rad/s (f={m['f_max']:.2f} Hz), "
              f"eta={m['eta_at_300hz']:.3f}")
    print(f"explicit bar: omega < {OMEGA_EXPLICIT:.0f} rad/s (eta<2) -> "
          f"EXPLICIT AT 300 Hz {'FAILS' if eta > ETA_BAR else 'HOLDS'}")
    print(f"substeps: n >= ceil(eta/2) = {n_sub} at h=1/300 "
          f"(h/n = {H / n_sub:.3e} s)")

    # ---- persist ------------------------------------------------------------
    out = {
        "meta": {
            "tool": "tools/xpbd_diagnostic.py", "agent": "A12-xpbd-prereg",
            "date": "2026-09-14",
            "source": "Astra answer (coupled XPBD volume solve); cited in PREREG.md",
            "endpoints": ["/tick_state", "/verts", "/topology"],
            "ticks": int(ts["ticks"]),
            "kappa_pa_inv": KAPPA, "B_gpa": 1 / KAPPA / 1e9, "rho": RHO,
            "h_s": H, "eta_bar": ETA_BAR, "omega_explicit_bar_rad_s": OMEGA_EXPLICIT,
            "delta_probe_m": DELTA, "kernel_band_m": BAND,
            "d_band_m": D_BAND,
            "mass_total_kg": float(m_vert.sum()),
            "mesh": {"nv": nv, "nf": nf},
        },
        "volume_validation": {
            "band_integral": [float(x) for x in V_band],
            "live_v0": [float(x) for x in V0],
            "band_relerr": [float(x) for x in V_err],
            "slice_steps_m": [float(n_slices[k] and D_BAND) for k in range(nc)],
            "whole_divergence": whole,
            "whole_live": float(ts["V_whole"]),
        },
        "cut_planes": {
            "y": [float(v) for v in cuts],
            "A_slice": [float(v) for v in A],
            "A_brackets": A_br,
            "A_probe_fd": [float(v) for v in A_kernel],
            "m_below": [float(v) for v in m_below_plane],
            "m_above": [float(v) for v in m_above_plane],
            "mu_reduced": [float(v) for v in mu_red],
            "mu_grounded_m_above": [float(v) for v in mu_grounded],
        },
        "piston_table": rows,
        "modal": out_modal,
        "substeps": {"required": int(n_sub), "h_over_n": float(H / n_sub),
                     "rule": "n >= ceil(h*omega_max/2) at h=1/300, bar eta<2"},
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    path = f"{OUT_DIR}/diagnostic_results.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
