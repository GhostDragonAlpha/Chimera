"""Recipe, port response and assembly adapters; existing triangle law is authoritative."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from tools.membrane_scale_lab.surface_energy_reference import evaluate_surface

ROOT = Path(__file__).resolve().parents[2]
LAW = "constant_gamma_current_area_v1"
DOMAIN = (-0.4, 0.4)
UNITS = {"length": "m", "energy": "J", "force": "N", "gamma": "J/m^2"}

class Refusal(ValueError):
    pass

def require(condition, reason):
    if not condition:
        raise Refusal(reason)

def finite(x):
    return type(x) in (int, float) and math.isfinite(x)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()

def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def source_hashes():
    paths = list((ROOT / "tools/artificial_proteins").glob("*.py"))
    paths += [ROOT / "tools/artificial_proteins/PREREGISTRATION.md",
              ROOT / "tools/artificial_proteins/PREREGISTRATION2.md",
              ROOT / "tools/artificial_proteins/native/batch.cpp",
              ROOT / "tools/artificial_proteins/native/CMakeLists.txt",
              ROOT / "tools/membrane_scale_lab/surface_energy_reference.py",
              ROOT / "tools/python_control/client.py", ROOT / "tools/membrane_demo_client.py",
              ROOT / "tools/membrane_scale_lab/membrane_gpu_probe/probe_core.hpp",
              ROOT / "tools/membrane_scale_lab/membrane_gpu_probe/membrane.comp"]
    return {str(p.relative_to(ROOT)).replace("\\", "/"): file_hash(p) for p in sorted(paths) if p.exists()}

def recipe(seed=0):
    require(type(seed) is int and 0 <= seed <= 1000, "invalid_seed")
    rng = np.random.default_rng(seed)
    angles = np.arange(6) * (2 * np.pi / 6)
    # Elliptical convex polygon, asymmetric radial variation; centre stays inside.
    radii = 1 + rng.uniform(-0.035, 0.035, 6)
    rim = np.column_stack([1.1 * radii * np.cos(angles), .8 * radii * np.sin(angles)])
    r = {"schema": "chimera.artificial_protein.recipe.v1", "id": f"ap01_{seed}",
         "law": LAW, "units": UNITS.copy(), "rim_xy": rim.tolist(),
         "domain": list(DOMAIN), "ports": {"support": "fixed_rim", "test": "centre_z_rail"},
         "seed": seed}
    validate_recipe(r)
    return r

def validate_recipe(r):
    require(isinstance(r, dict) and set(r) == {"schema","id","law","units","rim_xy","domain","ports","seed"}, "recipe_fields")
    require(r["schema"] == "chimera.artificial_protein.recipe.v1" and r["law"] == LAW, "unsupported_law")
    require(isinstance(r["id"], str) and r["id"].isascii() and r["id"].replace("_", "").isalnum(), "invalid_id")
    require(type(r['seed']) is int and 0 <= r['seed'] <= 1000, 'invalid_seed')
    require(r["units"] == UNITS, "unit_mismatch")
    require(r["domain"] == list(DOMAIN), "unsupported_domain")
    require(r["ports"] == {"support":"fixed_rim", "test":"centre_z_rail"}, "unsupported_ports")
    try:
        rim = np.asarray(r["rim_xy"], dtype=float)
    except (ValueError, TypeError) as e:
        raise Refusal("invalid_rim") from e
    require(rim.shape == (6, 2) and np.isfinite(rim).all(), "invalid_rim")
    require(np.max(np.abs(rim)) <= 1.2 and np.min(np.linalg.norm(rim, axis=1)) >= .7, "rim_out_of_domain")
    edge = np.roll(rim,-1,axis=0)-rim
    cross = lambda a,b: a[:,0]*b[:,1]-a[:,1]*b[:,0]
    require(np.all(cross(edge, np.roll(edge,-1,axis=0)) > .1), "nonconvex_rim")
    require(np.all(cross(rim, np.roll(rim,-1,axis=0)) > .1), "centre_outside_rim")
    return r

def geometry(r, h, scale=1.0):
    validate_recipe(r)
    require(finite(scale) and .5 <= scale <= 2, "scale_out_of_domain")
    require(finite(h) and DOMAIN[0] <= h / scale <= DOMAIN[1], "port_out_of_domain")
    pos = np.vstack([np.column_stack([r["rim_xy"], np.zeros(6)]) * scale, [0., 0., h]])
    faces = np.array([[6,i,(i+1)%6] for i in range(6)], dtype=np.int64)
    return pos, faces

def detailed(r, h, scale=1.0, gamma=1.0):
    require(finite(gamma) and 0 <= gamma <= 2, "gamma_out_of_domain")
    pos, faces = geometry(r, h, scale)
    ev = evaluate_surface(pos, faces, gamma)
    return {"energy": float(ev.energy), "reaction": float(-ev.vertex_forces[6,2]),
            "positions": pos.tolist(), "forces": ev.vertex_forces.tolist(), "faces": faces.tolist()}

def table_from_samples(x, reaction, energy_at_left, *, recipe_hash, lineage=None):
    x=np.asarray(x, dtype=float); f=np.asarray(reaction, dtype=float)
    require(x.ndim==1 and f.shape==x.shape and 2 <= len(x) <= 1025 and np.isfinite(x).all() and np.isfinite(f).all(), "invalid_samples")
    require(np.all(np.diff(x)>0) and np.all(np.diff(f)>0), "nonmonotone_response")
    require(finite(energy_at_left), "invalid_energy")
    # Piecewise-linear force, integrated exactly: energy and force remain consistent.
    energy=np.r_[energy_at_left, energy_at_left+np.cumsum(np.diff(x)*(f[:-1]+f[1:])*.5)]
    artifact={"schema":"chimera.artificial_protein.table.v1", "recipe_hash":recipe_hash,
              "units":UNITS.copy(), "x":x.tolist(), "reaction":f.tolist(), "energy":energy.tolist(),
              "source_hashes":source_hashes(), "lineage":lineage or [], "scope":"scalar quasistatic rail-port response"}
    artifact["sha256"]=digest(artifact)
    return artifact

def validate_table(a, check_sources=True):
    require(isinstance(a,dict) and a.get("schema")=="chimera.artificial_protein.table.v1", "table_schema")
    require(a.get("units")==UNITS, "unit_mismatch")
    require(a.get("sha256")==digest({k:v for k,v in a.items() if k!="sha256"}), "artifact_hash_mismatch")
    if check_sources:
        require(a.get("source_hashes")==source_hashes(), "stale_sources")
    x=np.asarray(a['x']);f=np.asarray(a['reaction']);e=np.asarray(a['energy'])
    require(x.ndim==1 and 2 <= len(x) <= 1025 and f.shape==x.shape and e.shape==x.shape and np.isfinite(x).all() and np.isfinite(f).all() and np.isfinite(e).all(),"invalid_table")
    require(np.all(np.diff(x)>0) and np.all(np.diff(f)>0),"nonmonotone_response")
    require(np.allclose(np.diff(e),np.diff(x)*(f[:-1]+f[1:])*.5,rtol=1e-12,atol=1e-12),"energy_force_inconsistent")
    return a

class Response:
    """An immutable-by-copy checked artifact; validate once, evaluate many times."""
    def __init__(self, artifact):
        a=json.loads(json.dumps(artifact));validate_table(a)
        self.artifact=a;self.x=np.array(a['x']);self.f=np.array(a['reaction']);self.e=np.array(a['energy'])
        self.domain=(float(self.x[0]),float(self.x[-1]))
    def __call__(self, h, scale=1.0, gamma=1.0):
        require(finite(scale) and .5<=scale<=2 and finite(gamma) and 0<=gamma<=2,"parameter_out_of_domain")
        require(finite(h) and self.domain[0]<=h/scale<=self.domain[1],"port_out_of_domain")
        require(not self.artifact['lineage'] or (scale==1.0 and gamma==1.0),'composite_scaling_unqualified')
        u=h/scale;i=min(int(np.searchsorted(self.x,u,side='right'))-1,len(self.x)-2);i=max(i,0)
        dx=u-self.x[i];k=(self.f[i+1]-self.f[i])/(self.x[i+1]-self.x[i])
        return {"reaction":float(gamma*scale*(self.f[i]+k*dx)),"energy":float(gamma*scale**2*(self.e[i]+self.f[i]*dx+.5*k*dx*dx))}

def equilibrium(parts, load, interval, *, tolerance=1e-10):
    """parts=(callable response, anchor). One shared rail DOF; no simulated time."""
    require(finite(load) and finite(tolerance) and tolerance==1e-10,"invalid_solve_contract")
    lo,hi=map(float,interval);require(math.isfinite(lo) and math.isfinite(hi) and lo<hi,"invalid_interval")
    require(len(parts)>0,"empty_assembly")
    def residual(q):return sum(fn(float(q-anchor))['reaction'] for fn,anchor in parts)-load
    flo,fhi=residual(lo),residual(hi)
    require(flo<=0<=fhi,"load_out_of_domain")
    for iteration in range(80):
        q=(lo+hi)/2;f=residual(q)
        if abs(f)<=tolerance:
            return {"q":q,"residual_n":f,"iterations":iteration+1,
                    "reactions":[fn(float(q-anchor))['reaction'] for fn,anchor in parts],
                    "energy":sum(fn(float(q-anchor))['energy'] for fn,anchor in parts)}
        if f>0:hi=q
        else:lo=q
    raise Refusal("equilibrium_not_converged")
