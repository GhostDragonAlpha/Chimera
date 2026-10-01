"""adapter_stvk.py -- REFERENCE ADAPTER over the existing repo M-law.

Wraps tools/elastic_foundation (STVK membrane: law.evaluate_elastic) in the
mechanism protocol end-to-end. The law is IMPORTED, never edited or
reimplemented: equations, validation and named refusals stay owned by the
existing module; this adapter only translates its Evaluation into
MechanismContribution records.

Model identity: "elastic_foundation.stvk_membrane/v1".
The law is history-free (state_spec empty); damping/thermal behavior are NOT
claimed -- heat flux and dissipation are reported as exactly 0.0 because the
law is conservative, not because they are unsupported silently.
"""
from __future__ import annotations

from .model import MaterialModel, StateVar
from .mechanism import (Mechanism, MechanismContribution, MechanismRefusal,
                        SolverConstraints)
from .parameters import ParameterMeta
from .presets import MaterialPreset
from .units import Quantity


def _import_law():
    try:
        import tools.elastic_foundation.law as law
        import tools.elastic_foundation.materials as materials
        return law, materials
    except ImportError as exc:
        raise MechanismRefusal(
            "law_import_failed",
            f"the existing STVK law (tools/elastic_foundation) is not "
            f"importable from this environment: {exc}") from None


STVK_MODEL = MaterialModel(
    model_id="elastic_foundation.stvk_membrane/v1",
    equations=(
        "STVK plane-stress membrane (existing repo law tools/elastic_foundation/"
        "law.py): F=[d1 d2]B; C=F^T F; E=(C-I)/2; "
        "Wbar = 0.5*lambda_bar*tr(E)^2 + mu_bar*tr(E:E); "
        "S = lambda_bar*tr(E)*I + 2*mu_bar*E; P = F S; "
        "corner force = -A0 * dW/dy; lambda_bar=E*nu/(1-nu^2), "
        "mu_bar=E/(2*(1+nu))"),
    parameters=(
        ParameterMeta(
            name="young_modulus", unit="Pa", family="elasticity",
            description="Young modulus E of the isotropic plane-stress sheet; "
                        "sets extensional stiffness",
            lo=1e0, hi=1e12, default=1e2, scale="log"),
        ParameterMeta(
            name="poisson_ratio", unit="1", family="compression",
            description="Poisson ratio nu; sets the volumetric/compression "
                        "coupling (lambda_bar). The repo measures no nu for any "
                        "material, so measured presets cannot cover it",
            lo=1e-3, hi=0.499, default=0.3, scale="linear"),
        ParameterMeta(
            name="thickness", unit="m", family="bending",
            description="Sheet thickness h; the geometric scale of plate "
                        "bending stiffness (D ~ E h^3)",
            lo=1e-6, hi=1e0, default=1.0, scale="log"),
    ),
    state_spec=(),          # the existing law is history-free
    history=False,
    law_import="tools.elastic_foundation.law",
    implemented=True,
)

# A strictly-metadata demonstration model: every control family the interface
# can expose, with NO implemented equations. generate_controls() works from its
# metadata; require_implemented() refuses any evaluation. This proves the
# control generator is metadata-driven and that this lane does not fabricate
# physics for laws the repo does not carry.
DECLARATION_ONLY_MODEL = MaterialModel(
    model_id="iface.demo.viscoelastic_thermal_declaration/v1",
    equations=(
        "DECLARATION ONLY: a generalized visco-elastic-thermal response "
        "(elasticity, compression, shear, bending, viscosity, relaxation, "
        "yielding, thermal). No equations implemented in this lane; listed to "
        "exercise metadata-generated controls and the evaluation refusal."),
    parameters=(
        ParameterMeta("young_modulus", "Pa", "elasticity",
                      "extensional stiffness", 1e0, 1e12, 1e2, "log"),
        ParameterMeta("bulk_modulus", "Pa", "compression",
                      "volumetric stiffness", 1e0, 1e11, 2.2e9, "log"),
        ParameterMeta("shear_modulus", "Pa", "shear",
                      "shape-preserving stiffness", 1e0, 1e11, 5e1, "log"),
        ParameterMeta("plate_thickness", "m", "bending",
                      "bending stiffness scale", 1e-6, 1e0, 1e-3, "log"),
        ParameterMeta("dynamic_viscosity", "Pa*s", "viscosity",
                      "rate-dependent stress", 1e-6, 1e6, 1e-3, "log"),
        ParameterMeta("relaxation_time", "s", "relaxation",
                      "internal-state relaxation timescale", 1e-9, 1e3,
                      1e-2, "log"),
        ParameterMeta("yield_stress", "Pa", "yielding",
                      "onset of permanent deformation", 1e0, 1e10, 1e6, "log"),
        ParameterMeta("thermal_conductivity", "W/(m*K)", "thermal",
                      "conductive heat transport", 1e-2, 5e2, 0.6, "log"),
        ParameterMeta("specific_heat", "J/(kg*K)", "thermal",
                      "heat capacity per mass", 1e2, 4e3, 1.5e3, "linear"),
        ParameterMeta("thermal_expansion", "1/K", "thermal",
                      "thermal strain coefficient", 1e-7, 1e-3, 2.3e-5, "log"),
    ),
    state_spec=(StateVar("viscous_strain", "1", "internal viscoelastic strain"),
                StateVar("plastic_strain", "1", "accumulated plastic strain")),
    history=True,
    law_import="",
    implemented=False,
)


class StvkMembraneMechanism(Mechanism):
    """Adapts the existing STVK law into the mechanism protocol."""

    adapters_model_id = "elastic_foundation.stvk_membrane/v1"

    def __init__(self, model: MaterialModel = STVK_MODEL,
                 mechanism_id: str = "adapter.stvk_membrane/v1"):
        super().__init__(mechanism_id=mechanism_id, model_id=model.model_id,
                         declares=("positions", "presets", "geometry",
                                   "temperature_K"))
        if model.model_id != STVK_MODEL.model_id or not model.implemented:
            raise MechanismRefusal(
                "mechanism_model_mismatch",
                f"this adapter implements {STVK_MODEL.model_id!r} only; "
                f"got {model.model_id!r} (implemented={model.implemented})")
        self.model = model
        self._law, self._materials = _import_law()

    def evaluate(self, inputs) -> tuple[MechanismContribution, ...]:
        self.require_inputs(inputs)
        geometry = inputs["geometry"]
        presets = inputs["presets"]
        positions = inputs["positions"]
        temperature_k = float(inputs["temperature_K"])
        preset = presets.get(self.model.model_id)
        if preset is None:
            raise MechanismRefusal(
                "unresolved_dependency",
                f"{self.mechanism_id}: no MaterialPreset for "
                f"{self.model.model_id!r} in the assembly presets")
        if preset.model_id != self.model.model_id:
            raise MechanismRefusal(
                "mechanism_model_mismatch",
                f"preset {preset.preset_id!r} is for {preset.model_id!r}, not "
                f"{self.model.model_id!r}")
        if geometry.representation != "surface":
            raise MechanismRefusal(
                "representation_mismatch",
                f"{self.mechanism_id}: STVK membrane needs a surface binding, "
                f"got {geometry.representation!r}")

        ok, reason = preset.applicability(
            {"temperature_K": Quantity(temperature_k, "K")})
        if not ok:
            return self._inapplicable(geometry, reason)

        meta = {m.name: m for m in self.model.parameters}
        try:
            material = self._materials.ElasticMaterial2D(
                E=preset.values.value("young_modulus", "Pa"),
                nu=preset.values.value("poisson_ratio", "1"),
                h=preset.values.value("thickness", "m"),
                name=preset.preset_id,
                provenance=f"{preset.kind}:{preset.provenance.citation}",
            )
            rest = geometry.binding["rest"]
            np_positions = _to_numpy(positions)
            ev = self._law.evaluate_elastic(rest, material, np_positions)
        except MechanismRefusal:
            raise
        except Exception as exc:
            reason_txt = getattr(exc, "reason", exc.__class__.__name__)
            raise MechanismRefusal(
                "law_refused",
                f"the existing STVK law refused the evaluation "
                f"[{reason_txt}]: {exc}") from None

        solver = SolverConstraints(
            analytic_force_jacobian=True,
            recommended_max_dt_s=None,
            tolerance_energy_scale_j=float(ev.energy_scale),
            notes="STVK membrane: conservative, history-free; analytic "
                  "vertex forces; degeneracy floor enforced by the law")
        records = []
        for i, vertex_id in enumerate(geometry.point_ids):
            fx, fy, fz = (float(c) for c in ev.vertex_forces[i])
            records.append(MechanismContribution(
                mechanism_id=self.mechanism_id,
                channel="force",
                point=vertex_id,
                force=(fx, fy, fz),
                stress_voigt=None,
                heat_flux_w_per_m2=0.0,
                stored_energy_j=0.0,
                dissipated_power_w=0.0,
                state_proposal=None,
                solver=solver,
                applicable=True))
        rest_areas = rest.areas0
        for f_idx in range(len(ev.per_face.Wbar)):
            s = ev.per_face.S[f_idx]
            records.append(MechanismContribution(
                mechanism_id=self.mechanism_id,
                channel="stored_energy",
                point=f"f{f_idx}",
                force=None,
                stress_voigt=(float(s[0, 0]), float(s[1, 1]), float(s[0, 1]),
                              0.0, 0.0, 0.0),
                heat_flux_w_per_m2=0.0,
                stored_energy_j=float(ev.per_face.Wbar[f_idx] * rest_areas[f_idx]),
                dissipated_power_w=0.0,
                state_proposal=None,
                solver=solver,
                applicable=True))
        return tuple(records)

    def _inapplicable(self, geometry, reason: str) -> tuple[MechanismContribution, ...]:
        out = []
        for pid in geometry.point_ids:
            out.append(MechanismContribution(
                mechanism_id=self.mechanism_id, channel="force", point=pid,
                force=None, stress_voigt=None, heat_flux_w_per_m2=0.0,
                stored_energy_j=0.0, dissipated_power_w=0.0,
                state_proposal=None, solver=None,
                applicable=False, inapplicable_reason=reason))
        faces = geometry.binding["faces"]
        for f_idx in range(len(faces)):
            out.append(MechanismContribution(
                mechanism_id=self.mechanism_id, channel="stored_energy",
                point=f"f{f_idx}", force=None, stress_voigt=None,
                heat_flux_w_per_m2=0.0, stored_energy_j=0.0,
                dissipated_power_w=0.0, state_proposal=None, solver=None,
                applicable=False, inapplicable_reason=reason))
        return tuple(out)


def _to_numpy(positions):
    import numpy as np
    return np.asarray(positions, dtype=float)


def bind_surface_to_stvk(geometry):
    """Build the law's RestGeometry once for a lane surface Geometry record."""
    law, _ = _import_law()
    from tools.elastic_foundation.geometry import build_rest_geometry
    import numpy as np
    if geometry.representation != "surface":
        raise MechanismRefusal("representation_mismatch",
                               f"STVK binds surface geometry, got "
                               f"{geometry.representation!r}")
    pts = np.asarray(geometry.binding["rest_positions"], dtype=float)
    faces = np.asarray(geometry.binding["faces"], dtype=np.int64)
    rest = build_rest_geometry(pts, faces)
    geometry.binding["rest"] = rest
    return rest


def stored_energy_scales_with_modulus(preset: MaterialPreset, factor: float) -> float:
    """Analytic note used by the energy-attribution test: at FIXED geometry the
    STVK energy is linear in E, so a runtime E change by `factor` must move the
    stored energy by exactly (factor - 1) * previous. lambda_bar and mu_bar are
    both proportional to E."""
    return factor - 1.0
