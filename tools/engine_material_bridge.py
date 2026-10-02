"""engine_material_bridge.py -- the engine's material parameter path as
tools/material_iface's FIRST consumer (zero importers existed before this
module; verified by git grep over tools/ + ChimeraEngine/ at master
522e4ae2f77b3bf0b011c932e0565d8a01f24e9b).

The engine's membrane material parameters are the compiled constants of
ChimeraEngine/engine/membrane_tick.hpp:

    sigma_n_   = 4000.f  (skin working tension, N/m; the press law
                          delta = F/(4 pi sigma), Gaussian falloff r0)
    press_r0_  = 0.03f   (falloff radius, m)
    tau_relax_ = 0.5f    (soft-tissue stress relaxation, s)

This bridge binds those parameters to a validated material_iface
MaterialModel + MaterialPreset (units, provenance citations, validity
metadata) and EMITS the engine parameter payload consumed by the native
whole-game gate (tools/monkey_campaign/engine_wiring_gate/membrane_gate.cpp),
which bit-compares it against the compiled constants. The flow is the
consumer loop: preset -> validated ParameterSet -> payload -> native
parity check; drift on either side refuses BY NAME.

No physics claim is made here: the preset's provenance is the engine's own
derivation notes (Yamada-sourced working values plus engine-declared
geometric scales), and the combination is AUTO-LABELED SYNTHETIC by the
material_iface law because the values trace to more than one source
identity. That label is asserted by the test; relabeling it "measured"
without a single measured source must fail.
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

# Importable both as tools.engine_material_bridge (root on path) and as a
# direct script: make the checkout root importable before the iface imports.
_ROOT = str(Path(__file__).resolve().parents[1])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from tools.material_iface.model import MaterialModel  # noqa: E402
from tools.material_iface.parameters import ParameterMeta  # noqa: E402
from tools.material_iface.presets import (  # noqa: E402
    CitedValue, MaterialPreset)
from tools.material_iface.units import Quantity  # noqa: E402

from tools.material_iface.model import MaterialModel
from tools.material_iface.parameters import ParameterMeta
from tools.material_iface.presets import CitedValue, MaterialPreset
from tools.material_iface.units import Quantity

SCHEMA = "chimera.engine_material_payload.v1"

ENGINE_MODEL_ID = "engine.membrane_skin/v1"

# The engine constants this bridge consumes (membrane_tick.hpp, compiled
# defaults; the native gate bit-compares its compiled values against the
# payload emitted here -- line refs recorded per parameter).
ENGINE_CONSTANTS = {
    "sigma_n_per_m": {
        "value_f32": 4000.0,   # float sigma_n_ = 4000.f
        "pin": "ChimeraEngine/engine/membrane_tick.hpp:float sigma_n_ = 4000.f",
        "unit": "N/m",
    },
    "press_falloff_radius_m": {
        "value_f32": 0.03,     # float press_r0_ = 0.03f
        "pin": "ChimeraEngine/engine/membrane_tick.hpp:float press_r0_ = 0.03f",
        "unit": "m",
    },
    "stress_relaxation_time_s": {
        "value_f32": 0.5,      # float tau_relax_ = 0.5f
        "pin": "ChimeraEngine/engine/membrane_tick.hpp:float tau_relax_ = 0.5f",
        "unit": "s",
    },
}

ENGINE_SKIN_MODEL = MaterialModel(
    model_id=ENGINE_MODEL_ID,
    equations=(
        "The engine's native membrane material path (membrane_tick.cpp): "
        "press dimple delta = F/(4*pi*sigma_n) with Gaussian falloff "
        "exp(-d^2/r0^2) around the press point (active presses SET offsets; "
        "released offsets decay exp(-dt/tau_relax) to the 0.1 mm cutoff); "
        "implemented natively in ChimeraEngine/engine/membrane_tick.cpp -- "
        "this bridge validates and transports parameters, it does not "
        "reimplement the law."),
    parameters=(
        ParameterMeta(
            name="sigma_n_per_m", unit="N/m", family="elasticity",
            description="Skin working tension sigma_n of the linear-membrane "
                        "press law; engine derivation: Yamada ULS 8 MPa x "
                        "1.5 mm / safety 3",
            lo=1.0, hi=1.0e6, default=4000.0, scale="log"),
        ParameterMeta(
            name="press_falloff_radius_m", unit="m", family="elasticity",
            description="Gaussian falloff radius r0 of the press law; "
                        "engine-declared geometric scale (0.03 m)",
            lo=1e-3, hi=1.0, default=0.03, scale="log"),
        ParameterMeta(
            name="stress_relaxation_time_s", unit="s", family="relaxation",
            description="Soft-tissue stress relaxation time tau of the "
                        "hydraulic-return decay; named at the Yamada "
                        "skin-creep scale",
            lo=1e-3, hi=1e3, default=0.5, scale="log"),
    ),
    state_spec=(),
    history=False,
    law_import="ChimeraEngine/engine/membrane_tick.cpp",
    implemented=True,
)

# Provenance: the engine's own derivation notes, cited per parameter. Two
# distinct source identities (the Yamada derivation vs the engine-declared
# geometric scale) -- combine_values' auto-labeling law therefore labels the
# preset SYNTHETIC with the citations preserved. Asserted by the test.
_PRESET_PARTS = {
    "sigma_n_per_m": CitedValue(
        quantity=Quantity(4000.0, "N/m"),
        citation="engine membrane_tick.hpp derivation (Yamada ULS 8 MPa x "
                 "1.5 mm, safety 3)",
        species="synthetic creature (human-scaled Yamada skin values)",
        source_id="engine.membrane.derivation"),
    "press_falloff_radius_m": CitedValue(
        quantity=Quantity(0.03, "m"),
        citation="engine membrane_tick.hpp declared geometric scale "
                 "(press falloff radius)",
        species="synthetic creature (engine design constant)",
        source_id="engine.membrane.design"),
    "stress_relaxation_time_s": CitedValue(
        quantity=Quantity(0.5, "s"),
        citation="engine membrane_tick.hpp derivation (named at Yamada "
                 "skin-creep scale; HR bar test)",
        species="synthetic creature (human-scaled Yamada skin values)",
        source_id="engine.membrane.derivation"),
}


def build_preset() -> MaterialPreset:
    """The validated engine membrane preset (ParameterSet bound to the model
    metadata; provenance auto-labeled)."""
    return MaterialPreset.combine_values(
        preset_id="engine.membrane_skin.shipped/v1",
        model=ENGINE_SKIN_MODEL,
        parts=_PRESET_PARTS,
    )


def _f32_hex(value: float) -> str:
    """The exact float32 value as C99 hexfloat (the native gate parses this
    with strtod and bit-compares against the compiled constant)."""
    packed = struct.pack("<f", value)
    as_f32 = struct.unpack("<f", packed)[0]  # float32 round-trip (widened)
    return float(as_f32).hex()


def emit_payload() -> dict:
    """The canonical engine material payload, built FROM the validated
    preset's ParameterSet (never from raw constants): drift on the model
    metadata, the units, or the range law refuses before anything emits."""
    preset = build_preset()
    values = preset.values
    parameters = {}
    for name in sorted(ENGINE_CONSTANTS):
        quantity = values.quantity(name)          # refuses unknown names
        meta = ENGINE_SKIN_MODEL.meta(name)
        accepted = meta.accept(quantity)          # re-validates unit+range
        parameters[name] = {
            "value": _f32_hex(accepted),
            "unit": meta.unit,
            "engine_pin": ENGINE_CONSTANTS[name]["pin"],
        }
    return {
        "schema": SCHEMA,
        "model_id": ENGINE_SKIN_MODEL.model_id,
        "preset_id": preset.preset_id,
        "preset_kind": preset.kind,
        "preset_citation": preset.provenance.citation,
        "consumer": {
            "first_consumer": "tools/monkey_campaign/engine_wiring_gate/"
                              "membrane_gate.cpp (native bit-parity check)",
            "consumer_law": "the compiled engine constants must bit-match "
                            "this payload; drift refuses by name",
        },
        "parameters": parameters,
    }


def canonical_payload_bytes() -> bytes:
    return (json.dumps(emit_payload(), sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1:
        print("usage: python -B engine_material_bridge.py OUT_PATH",
              flush=True)
        return 2
    Path(argv[0]).write_bytes(canonical_payload_bytes())
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
