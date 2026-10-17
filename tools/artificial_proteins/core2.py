"""AP02: one piece, two independent rail ports on one shared surface.

Extends the AP01 law (constant-gamma current area, authoritative in
tools/membrane_scale_lab) from one scalar rail port to two. The response is a
map (h_p, h_q) -> (R_p, R_q); the ports are cross-coupled through the shared
triangulation, so dR_p/dh_q is a measured physical quantity, not an assumption.
The quadratic reduced model is admitted only inside its declared domain and
only against measured error; the detailed solve stays authoritative.
"""
from __future__ import annotations
import json
import math
import numpy as np
from tools.membrane_scale_lab.surface_energy_reference import evaluate_surface
from .core import (Refusal, require, finite, digest, UNITS, LAW, DOMAIN, source_hashes)

RECIPE_SCHEMA = "chimera.artificial_protein.recipe.v2"
QUAD_SCHEMA = "chimera.artificial_protein.quadratic.v1"
PORTS = {"support": "fixed_rim", "p": "rail_z", "q": "rail_z"}
QUAD_DOMAIN = 0.02          # normalized |h| admitted for the quadratic model;
                            # largest radius on the frozen 11x11 grid meeting the
                            # 5e-3 budget for all shipped recipes (PREREGISTRATION2);
                            # 0.15 and 0.03 were measured and rejected
FACES = np.array([[6,0,1],[6,1,2],[6,2,3],[7,3,4],[7,4,5],[7,5,0],[6,3,7],[6,7,0]], dtype=np.int64)

def _signed_area(a, b, c):
    return 0.5 * ((b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0]))

def recipe2(seed=0):
    require(type(seed) is int and 0 <= seed <= 1000, "invalid_seed")
    rng = np.random.default_rng(seed)
    angles = np.arange(6) * (2 * np.pi / 6)
    radii = 1 + rng.uniform(-0.035, 0.035, 6)          # same rim stream as AP01
    rim = np.column_stack([1.1 * radii * np.cos(angles), .8 * radii * np.sin(angles)])
    theta = rng.uniform(0.45, math.pi - 0.45)
    rp, rq = rng.uniform(0.30, 0.50), rng.uniform(0.30, 0.50)
    p = np.array([1.1 * rp * math.cos(theta), .8 * rp * math.sin(theta)])
    q = -np.array([1.1 * rq * math.cos(theta), .8 * rq * math.sin(theta)])
    r = {"schema": RECIPE_SCHEMA, "id": f"ap02_{seed}", "law": LAW, "units": UNITS.copy(),
         "rim_xy": rim.tolist(), "port_xy": [p.tolist(), q.tolist()], "domain": list(DOMAIN),
         "ports": PORTS.copy(), "seed": seed}
    validate_recipe2(r)
    return r

def validate_recipe2(r):
    require(isinstance(r, dict) and set(r) == {"schema","id","law","units","rim_xy","port_xy","domain","ports","seed"}, "recipe_fields")
    require(r["schema"] == RECIPE_SCHEMA and r["law"] == LAW, "unsupported_law")
    require(isinstance(r["id"], str) and r["id"].isascii() and r["id"].replace("_","").isalnum(), "invalid_id")
    require(type(r['seed']) is int and 0 <= r['seed'] <= 1000, 'invalid_seed')
    require(r["units"] == UNITS and r["domain"] == list(DOMAIN), "unit_or_domain_mismatch")
    require(r["ports"] == PORTS, "unsupported_ports")
    try:
        rim = np.asarray(r["rim_xy"], dtype=float); ports = np.asarray(r["port_xy"], dtype=float)
    except (ValueError, TypeError) as e:
        raise Refusal("invalid_rim") from e
    require(rim.shape == (6,2) and ports.shape == (2,2) and np.isfinite(rim).all() and np.isfinite(ports).all(), "invalid_geometry")
    require(np.max(np.abs(rim)) <= 1.2 and np.min(np.linalg.norm(rim, axis=1)) >= .7, "rim_out_of_domain")
    edge = np.roll(rim,-1,axis=0)-rim
    cross = lambda a,b: a[:,0]*b[:,1]-a[:,1]*b[:,0]
    require(np.all(cross(edge, np.roll(edge,-1,axis=0)) > .1), "nonconvex_rim")
    require(np.all(cross(rim, np.roll(rim,-1,axis=0)) > .1), "centre_outside_rim")
    p, q = ports
    require(np.linalg.norm(p) >= .15 and np.linalg.norm(q) >= .15, "port_too_central")
    require(np.linalg.norm(p) <= .6 and np.linalg.norm(q) <= .6, "port_outside_safe_interior")
    require(p[1]*q[1] < 0 and abs(p[1]) >= .05 and abs(q[1]) >= .05, "ports_not_opposite_sides")
    pts = np.vstack([rim, p, q])
    areas = np.array([_signed_area(pts[a], pts[b], pts[c]) for a,b,c in FACES])
    require(np.all(areas > .02), "invalid_port_triangulation")
    return r

def geometry2(r, hp, hq, scale=1.0):
    validate_recipe2(r)
    require(finite(scale) and .5 <= scale <= 2, "scale_out_of_domain")
    require(finite(hp) and DOMAIN[0] <= hp/scale <= DOMAIN[1], "port_p_out_of_domain")
    require(finite(hq) and DOMAIN[0] <= hq/scale <= DOMAIN[1], "port_q_out_of_domain")
    pos = np.vstack([np.column_stack([r["rim_xy"], np.zeros(6)]),
                     np.column_stack([r["port_xy"], np.zeros(2)])]) * scale
    pos[6, 2] = hp; pos[7, 2] = hq          # physical rail heights, AP01 convention
    return pos, FACES.copy()

def detailed2(r, hp, hq, scale=1.0, gamma=1.0):
    require(finite(gamma) and 0 <= gamma <= 2, "gamma_out_of_domain")
    pos, faces = geometry2(r, hp, hq, scale)
    ev = evaluate_surface(pos, faces, gamma)
    return {"energy": float(ev.energy),
            "reaction": [float(-ev.vertex_forces[6,2]), float(-ev.vertex_forces[7,2])],
            "positions": pos.tolist(), "forces": ev.vertex_forces.tolist(), "faces": faces.tolist()}

def measure_quadratic(r, delta=1e-5):
    """Measured linear response about the origin at gamma=scale=1 (FD of the
    detailed reactions; symmetrized). Not a fit: no data beyond the origin."""
    e0 = detailed2(r, 0., 0.)["energy"]
    K = np.zeros((2,2))
    for j in range(2):
        d = np.zeros(2); d[j] = delta
        K[:,j] = (np.asarray(detailed2(r, float(d[0]), float(d[1]))["reaction"]) -
                  np.asarray(detailed2(r, float(-d[0]), float(-d[1]))["reaction"]))/(2*delta)
    K = .5*(K+K.T)
    require(np.all(np.linalg.eigvalsh(K) > 0), "quadratic_not_positive_definite")
    return K, e0

def quadratic_from_measurements(r, K, energy_at_origin, *, measured_errors):
    K = np.asarray(K, dtype=float)
    require(K.shape == (2,2) and np.all(np.isfinite(K)) and np.allclose(K, K.T, atol=0, rtol=1e-12), "invalid_K")
    require(np.all(np.linalg.eigvalsh(K) > 0), "quadratic_not_positive_definite")
    require(finite(energy_at_origin), "invalid_energy")
    require(isinstance(measured_errors, dict) and set(measured_errors) == {"reaction","energy"}
            and all(finite(v) and v >= 0 for v in measured_errors.values()), "invalid_measured_errors")
    a = {"schema": QUAD_SCHEMA, "recipe_hash": digest(r), "units": UNITS.copy(),
         "K": K.tolist(), "energy_at_origin": float(energy_at_origin), "domain_half": QUAD_DOMAIN,
         "measured_errors": {k: float(v) for k,v in measured_errors.items()},
         "source_hashes": source_hashes(), "lineage": [],
         "scope": "quadratic two-port response about the origin, inside declared domain only"}
    a["sha256"] = digest(a)
    return a

def validate_quadratic(a, check_sources=True):
    require(isinstance(a, dict) and a.get("schema") == QUAD_SCHEMA, "quadratic_schema")
    require(a.get("units") == UNITS, "unit_mismatch")
    require(a.get("domain_half") == QUAD_DOMAIN, "domain_mismatch")
    require(a.get("sha256") == digest({k:v for k,v in a.items() if k != "sha256"}), "artifact_hash_mismatch")
    if check_sources:
        require(a.get("source_hashes") == source_hashes(), "stale_sources")
    K = np.asarray(a["K"])
    require(K.shape == (2,2) and np.all(np.isfinite(K)) and np.allclose(K, K.T, atol=0, rtol=1e-12), "invalid_K")
    require(np.all(np.linalg.eigvalsh(K) > 0), "quadratic_not_positive_definite")
    return a

class Response2:
    """Immutable-by-copy checked quadratic artifact; validate once, evaluate many."""
    def __init__(self, artifact):
        a = json.loads(json.dumps(artifact)); validate_quadratic(a)
        self.artifact = a; self.K = np.array(a["K"]); self.e0 = float(a["energy_at_origin"])
    def __call__(self, h, scale=1.0, gamma=1.0):
        h = np.asarray(h, dtype=float)
        require(h.shape == (2,) and np.all(np.isfinite(h)), "invalid_port_state")
        require(finite(scale) and .5 <= scale <= 2 and finite(gamma) and 0 <= gamma <= 2, "parameter_out_of_domain")
        require(np.all(np.abs(h/scale) <= self.artifact["domain_half"]), "port_out_of_domain")
        require(not self.artifact["lineage"] or (scale == 1.0 and gamma == 1.0), "composite_scaling_unqualified")
        u = h/scale; r = self.K @ u
        return {"reaction": [float(v) for v in gamma*scale*r],
                "energy": float(gamma*scale**2*(self.e0 + .5*u @ r))}

def equilibrium2(pieces, loads, box, *, tolerance=1e-10):
    """Two shared rail DOFs; damped Newton on the measured residual with an FD
    Hessian. Convexity of the current-area law (sum of norms of affine maps)
    makes the box-bounded Newton reliable; the independent reference is the
    conjugate-gradient minimizer in verify2."""
    require(finite(tolerance) and tolerance == 1e-10, "invalid_solve_contract")
    loads = np.asarray(loads, dtype=float); box = np.asarray(box, dtype=float)
    require(loads.shape == (2,) and np.all(np.isfinite(loads)), "invalid_loads")
    require(box.shape == (2,2) and np.all(box[:,0] < box[:,1]) and np.all(np.isfinite(box)), "invalid_box")
    require(len(pieces) > 0, "empty_assembly")
    def residual(h):
        return sum(np.asarray(fn((h - np.asarray(anchor, dtype=float)))["reaction"]) for fn, anchor in pieces) - loads
    h = np.zeros(2)
    for iteration in range(60):
        r0 = residual(h)
        if np.max(np.abs(r0)) <= tolerance:
            return {"q": [float(v) for v in h], "residual_n": [float(v) for v in r0], "iterations": iteration+1,
                    "reactions": [list(map(float, fn((h - np.asarray(anchor, dtype=float)))["reaction"])) for fn, anchor in pieces],
                    "energy": float(sum(fn((h - np.asarray(anchor, dtype=float)))["energy"] for fn, anchor in pieces))}
        d = 1e-6*max(1.0, float(np.max(np.abs(h))))
        H = np.zeros((2,2))
        for j in range(2):
            e = np.zeros(2); e[j] = d
            H[:,j] = (residual(h+e) - residual(h-e))/(2*d)
        H = .5*(H+H.T)
        try: step = -np.linalg.solve(H, r0)
        except np.linalg.LinAlgError: raise Refusal("hessian_singular")
        lam = 1.0
        for _ in range(40):
            trial = h + lam*step
            if np.all(trial >= box[:,0]) and np.all(trial <= box[:,1]):
                rt = residual(trial)
                if np.linalg.norm(rt) < np.linalg.norm(r0)*(1 - 1e-4*lam) or np.linalg.norm(rt) < np.linalg.norm(r0):
                    h = trial; break
            lam *= .5
        else:
            raise Refusal("equilibrium_not_converged")
    raise Refusal("equilibrium_not_converged")
