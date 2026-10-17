"""Independent AP02 checks: Heron areas from 3-D edge lengths, conjugate-gradient
energy minimization, finite-difference cross stiffness. The Heron energy and the
CG minimizer never call the triangle force code or the production Newton solver;
stiffness_detailed and verify_quadratic2 deliberately call the production
detailed2 because that side is the measurement being checked. Formulations are
deliberately different from core2 so agreement is evidence, not tautology.
"""
from __future__ import annotations
import math
import numpy as np
from .core import Refusal, require
from .core2 import geometry2, detailed2, FACES, QUAD_DOMAIN, Response2

LIMITS2 = {"heron_energy": 2e-11, "heron_reaction": 1e-8, "cross_stiffness": 1e-6,
           "hessian_symmetry": 1e-6, "coupling_fraction": 0.05, "quadratic": 5e-3,
           "equilibrium_m": 2e-4, "residual_n": 1e-10}

def heron_energy(r, hp, hq, scale=1., gamma=1.):
    """Energy from Heron's formula on 3-D edge lengths — independent of the
    cross-product area gradient used by the reference law."""
    pos, _ = geometry2(r, hp, hq, scale)
    total = 0.
    for a, b, c in FACES:
        la = np.linalg.norm(pos[b]-pos[c]); lb = np.linalg.norm(pos[c]-pos[a]); lc = np.linalg.norm(pos[a]-pos[b])
        s = .5*(la+lb+lc)
        total += math.sqrt(max(s*(s-la)*(s-lb)*(s-lc), 0.))
    return gamma*total

def heron_reaction(r, hp, hq, scale=1., gamma=1., delta=1e-6):
    """Central-difference reaction pair from the Heron energy."""
    out = []
    for j in range(2):
        d = delta*scale
        hp2, hq2 = (hp+d, hq) if j == 0 else (hp, hq+d)
        hm2, hq3 = (hp-d, hq) if j == 0 else (hp, hq-d)
        out.append((heron_energy(r, hp2, hq2, scale, gamma) - heron_energy(r, hm2, hq3, scale, gamma))/(2*d))
    return out

def stiffness_detailed(r, hp, hq, scale=1., gamma=1., delta=1e-5):
    """2x2 Hessian by central FD of the detailed reactions."""
    H = np.zeros((2,2))
    for j in range(2):
        d = np.zeros(2); d[j] = delta*scale
        H[:,j] = (np.asarray(detailed2(r, float(hp+d[0]), float(hq+d[1]), scale, gamma)["reaction"]) -
                  np.asarray(detailed2(r, float(hp-d[0]), float(hq-d[1]), scale, gamma)["reaction"]))/(2*delta*scale)
    return H

def stiffness_heron(r, hp, hq, scale=1., gamma=1., delta=1e-4):
    """2x2 Hessian by second central differences of the Heron energy."""
    H = np.zeros((2,2)); d = delta*scale
    epp = heron_energy(r, hp+d, hq+d, scale, gamma); epm = heron_energy(r, hp+d, hq-d, scale, gamma)
    emp = heron_energy(r, hp-d, hq+d, scale, gamma); emm = heron_energy(r, hp-d, hq-d, scale, gamma)
    H[0,0] = (heron_energy(r, hp+d, hq, scale, gamma) - 2*heron_energy(r, hp, hq, scale, gamma) + heron_energy(r, hp-d, hq, scale, gamma))/d**2
    H[1,1] = (heron_energy(r, hp, hq+d, scale, gamma) - 2*heron_energy(r, hp, hq, scale, gamma) + heron_energy(r, hp, hq-d, scale, gamma))/d**2
    H[0,1] = H[1,0] = (epp - epm - emp + emm)/(4*d**2)
    return H

def verify_samples2(cases, values):
    require(len(cases) == len(values) and len(cases) > 0, "missing_cases")
    e_err = f_err = 0.
    for c, v in zip(cases, values):
        ref_e = heron_energy(c["recipe"], c["hp"], c["hq"], c["scale"], c["gamma"])
        ref_f = heron_reaction(c["recipe"], c["hp"], c["hq"], c["scale"], c["gamma"])
        e = abs(v["energy"]-ref_e)/max(c["gamma"]*c["scale"]**2, 1e-30)
        f = float(np.max(np.abs(np.asarray(v["reaction"])-np.asarray(ref_f))))/max(c["gamma"]*c["scale"], 1e-30)
        if c["gamma"] == 0:
            require(v["energy"] == 0 and all(x == 0 for x in v["reaction"]), "zero_gamma_failure"); e = f = 0.
        require(math.isfinite(e) and math.isfinite(f), "nonfinite_measurement")
        e_err = max(e_err, e); f_err = max(f_err, f)
    require(e_err <= LIMITS2["heron_energy"] and f_err <= LIMITS2["heron_reaction"], "heron_reference_mismatch")
    return {"cases": len(cases), "max_energy_error_normalized": e_err, "max_reaction_error_normalized": f_err,
            "limits": [LIMITS2["heron_energy"], LIMITS2["heron_reaction"]]}

def verify_quadratic2(r, quad, grid_half=QUAD_DOMAIN):
    """Measured error of the quadratic model against the detailed solve on a
    frozen grid inside its declared domain."""
    fn = Response2(quad)
    x = np.linspace(-grid_half, grid_half, 11)
    states = [(hp, hq) for hp in x for hq in x]
    detailed = [detailed2(r, float(hp), float(hq)) for hp, hq in states]
    e_scale = max(d["energy"] for d in detailed)
    f_scale = max(float(np.max(np.abs(d["reaction"]))) for d in detailed)
    require(e_scale > 0 and f_scale > 0, "degenerate_quadratic_grid")
    e_err = f_err = 0.
    for (hp, hq), d in zip(states, detailed):
        q = fn([hp, hq])
        e_err = max(e_err, abs(q["energy"]-d["energy"])/e_scale)
        f_err = max(f_err, float(np.max(np.abs(np.asarray(q["reaction"])-np.asarray(d["reaction"]))))/f_scale)
    return {"max_energy_error": e_err, "max_reaction_error": f_err, "limit": LIMITS2["quadratic"], "passes": e_err <= LIMITS2["quadratic"] and f_err <= LIMITS2["quadratic"]}

def minimum_energy2(pieces, loads, box):
    """Independent Hestenes-Stiefel conjugate-gradient minimization of the
    Heron potential; production uses Newton on triangle forces."""
    loads = np.asarray(loads, dtype=float)
    def potential(h):
        return sum(heron_energy(r, float(h[0]-a[0]), float(h[1]-a[1])) for r, a in pieces) - loads @ h
    def gradient(h):
        g = np.zeros(2); d = 1e-6
        for j in range(2):
            e = np.zeros(2); e[j] = d
            g[j] = (potential(h+e)-potential(h-e))/(2*d)
        return g
    h = np.zeros(2); g = gradient(h); dir_ = -g; cg0 = g @ g
    for _ in range(300):
        if np.linalg.norm(g) < 1e-9: break
        gd = g @ dir_
        if gd >= 0: dir_ = -g
        a = 1.0; f0 = potential(h)
        while True:  # backtracking line search; trial stays in the box/domain
            hn = np.clip(h + a*dir_, box[:,0], box[:,1])
            if potential(hn) <= f0 + 1e-4*a*gd or a < 1e-12: break
            a *= .5
        gn = gradient(hn)
        beta = max(0., (gn @ (gn - g))/max(cg0, 1e-300)); cg0 = gn @ gn
        h, g, dir_ = hn, gn, -gn + beta*dir_
    return h

def verify_equilibrium2(pieces, loads, box, measured):
    reference = minimum_energy2(pieces, loads, np.asarray(box, dtype=float))
    error = float(np.max(np.abs(np.asarray(measured["q"])-reference)))
    balance = np.zeros(2)
    for r, a in pieces:
        balance += np.asarray(heron_reaction(r, measured["q"][0]-a[0], measured["q"][1]-a[1]))
    balance -= np.asarray(loads, dtype=float)
    require(error <= LIMITS2["equilibrium_m"], "assembly_position_mismatch")
    require(float(np.max(np.abs(measured["residual_n"]))) <= LIMITS2["residual_n"], "assembly_not_converged")
    return {"independent_q_m": [float(v) for v in reference], "q_error_m": error,
            "reference_balance_residual_n": [float(v) for v in balance]}
