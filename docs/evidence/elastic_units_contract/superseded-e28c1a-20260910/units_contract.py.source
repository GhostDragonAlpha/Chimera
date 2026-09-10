"""Explicit dimensional contract for the existing 2-D STVK law.

This adapter does not change the historical law: its lambda/mu inputs are
surface moduli (force/length), with the old API's implicit unit thickness
preserved as a named compatibility mode.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np
from .geometry import build_rest_geometry
from .law import evaluate_elastic
from .materials import synthetic

class UnitsRefusal(ValueError):
    pass

@dataclass(frozen=True)
class SurfaceContract:
    E3d_pa: float
    thickness_m: float
    nu: float
    surface_modulus_n_per_m: float
    mode: str

    def __post_init__(self):
        if not math.isfinite(self.surface_modulus_n_per_m) or self.surface_modulus_n_per_m <= 0:
            raise UnitsRefusal("invalid_surface_modulus")

    @property
    def provenance_record(self):
        return {"kind": "explicit_3d_to_2d", "E_unit": "Pa", "h_unit": "m", "surface_unit": "N/m", "mode": self.mode}

def contract(E3d_pa, thickness_m, nu, *, mode="physical"):
    vals=(E3d_pa, thickness_m, nu)
    if any(isinstance(x,bool) or not isinstance(x,(int,float)) for x in vals):
        raise UnitsRefusal("numeric_material_required")
    if any(not math.isfinite(float(x)) for x in vals): raise UnitsRefusal("nonfinite_material")
    if E3d_pa <= 0: raise UnitsRefusal("nonpositive_young_modulus")
    if thickness_m <= 0: raise UnitsRefusal("nonpositive_thickness")
    if not -1 < nu < .5: raise UnitsRefusal("poisson_out_of_range")
    if mode == "physical":
        surface=E3d_pa*thickness_m
        if not math.isfinite(surface): raise UnitsRefusal("surface_modulus_overflow")
    elif mode == "legacy_implicit_unit_thickness": surface=E3d_pa
    else: raise UnitsRefusal("unsupported_units_mode")
    return SurfaceContract(float(E3d_pa),float(thickness_m),float(nu),float(surface),mode)

def evaluate_physical(rest, positions, E3d_pa, thickness_m, nu, *, provenance=None):
    c=contract(E3d_pa, thickness_m, nu, mode="physical")
    if not isinstance(provenance,dict) or provenance.get("kind") not in ("synthetic", "sourced") or not provenance.get("source"):
        raise UnitsRefusal("structured_provenance_required")
    return evaluate_elastic(rest, synthetic("physical-equivalent-2d", E=c.surface_modulus_n_per_m, nu=c.nu, h=c.thickness_m), positions)

def compare_fixture(path):
    z=np.load(path); rest=build_rest_geometry(z["rest_pos"].astype(float),z["faces_int32"].astype(int))
    cur=z["cur_pos"].astype(float); E=float(z["E_f64"]); h=float(z["h_f64"]); nu=float(z["nu_f64"])
    physical=evaluate_physical(rest,cur,E,h,nu,provenance={"kind":"sourced","source":str(path)})
    physical_2h=evaluate_physical(rest,cur,E,2*h,nu,provenance={"kind":"sourced","source":str(path)})
    legacy=evaluate_elastic(rest,synthetic("legacy",E=E,nu=nu,h=h),cur)
    return {"physical_energy":physical.energy,"legacy_energy":legacy.energy,
            "physical_force":physical.vertex_forces.tolist(),"legacy_force":legacy.vertex_forces.tolist(),
            "energy_ratio_physical_legacy":physical.energy/legacy.energy,
            "force_ratio_physical_legacy":float(np.linalg.norm(physical.vertex_forces)/np.linalg.norm(legacy.vertex_forces)),
            "physical_w_vol": physical.per_face.w_vol.tolist(), "physical_2h_w_vol": physical_2h.per_face.w_vol.tolist(),
            "thickness_scaling": {"energy_h": physical.energy, "energy_2h": physical_2h.energy,
                                  "energy_ratio": physical_2h.energy/physical.energy,
                                  "force_ratio": float(np.linalg.norm(physical_2h.vertex_forces)/np.linalg.norm(physical.vertex_forces)),
                                  "force_component_delta_from_2x": (physical_2h.vertex_forces-2*physical.vertex_forces).tolist()},
            "contract":{**contract(E,h,nu).provenance_record, "source":str(path), "kind":"sourced"}}

def main():
    import argparse,json
    p=argparse.ArgumentParser(); p.add_argument("--E",type=float); p.add_argument("--h",type=float); p.add_argument("--nu",type=float); p.add_argument("--mode",default="physical"); p.add_argument("--fixture"); a=p.parse_args()
    if a.fixture: print(json.dumps(compare_fixture(a.fixture),sort_keys=True)); return 0
    if a.E is None or a.h is None or a.nu is None: p.error("E, h and nu are required without --fixture")
    print(json.dumps(contract(a.E,a.h,a.nu,mode=a.mode).__dict__,sort_keys=True)); return 0
if __name__ == "__main__": raise SystemExit(main())
