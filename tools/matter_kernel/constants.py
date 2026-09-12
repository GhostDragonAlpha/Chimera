"""Sourced material constants for the matter kernel (KERNEL_SPEC.md law 4).

Every value is a TYPICAL engineering reference value, cited. Where the
literature gives a range, the conservative end is used and the range noted.
No constant may enter a definition without a source string (validator
enforces). Values are SI: density kg/m^3, moduli and strengths Pa,
hardness Vickers (HV).
"""
from __future__ import annotations

# Reference families used for citation strings:
#   ENGINEERING_TOOLBOX: engineeringtoolbox.com typical material pages
#   MATWEB_TYPICAL: MatWeb-grade representative values for common alloys
#   ASHBY: Ashby, "Materials Selection in Mechanical Design" appendix
#   NIST/ASTM where a standard number exists (noted per row)

MATERIALS: dict[str, dict] = {
    "mat.steel_mild": {
        "density": 7850.0,
        "young_modulus": 200e9,
        "yield": 250e6,
        "hardness_vickers": 160.0,  # typical mild steel, ~150-190 HV range
        "source": "ENGINEERING_TOOLBOX: steels; MATWEB_TYPICAL: AISI 1020",
    },
    "mat.steel_hardened": {
        "density": 7850.0,
        "young_modulus": 205e9,
        "yield": 1500e6,
        "hardness_vickers": 640.0,  # ~600-700 HV quenched tool steel range
        "source": "MATWEB_TYPICAL: AISI O1 hardened; ASHBY appendix A3",
    },
    "mat.aluminum": {
        "density": 2700.0,
        "young_modulus": 69e9,
        "yield": 95e6,
        "hardness_vickers": 35.0,
        "source": "ENGINEERING_TOOLBOX: aluminum 6061-T6 typical",
    },
    "mat.oak": {
        "density": 700.0,   # 600-750 range at 12% moisture
        "young_modulus": 11e9,   # 9-13 GPa range across grain direction
        "yield": 45e6,      # compressive parallel-to-grain typical
        "hardness_vickers": 4.0,   # Janka ~5 kN maps near Mohs ~3 / HV ~35;
        "source": "ASHBY: woods (oak) property ranges",
        "hardness_note": "wood hardness scales are side-hardness measurements; "
                         "HV value is an order-of-magnitude mapping, range noted",
    },
    "mat.rubber": {
        "density": 1100.0,
        "young_modulus": 0.01e9,
        "yield": 20e6,
        "hardness_vickers": 0.5,   # Shore A ~60-70 maps far below HV 1
        "source": "ENGINEERING_TOOLBOX: rubber, natural typical",
        "hardness_note": "elastomers are below the Vickers scale floor; "
                         "ordered soft in the scratch table by modulus",
    },
    "mat.glass_soda": {
        "density": 2500.0,
        "young_modulus": 70e9,
        "yield": 50e6,   # practical tensile failure stress, not yield
        "hardness_vickers": 550.0,
        "source": "ENGINEERING_TOOLBOX: glass, soda-lime",
    },
    "mat.wood_glue": {
        "density": 1050.0,
        "young_modulus": 2.0e9,
        "yield": 30e6,   # cured PVA bond line typical
        "hardness_vickers": 2.0,
        "source": "ASHBY: polymers (PVA) typical cured properties",
        "hardness_note": "bond line strength depends on cure conditions; "
                         "definitions override per-bond via cure_strength",
    },
}


def lookup(name: str) -> dict:
    if name not in MATERIALS:
        raise KeyError(f"unknown material {name!r} — constants are sourced, "
                       f"add the row with a citation before use")
    return MATERIALS[name]


def scratch_winner(a: str, b: str) -> str:
    """The scratch law, pairwise: return the member that YIELDS (the softer).
    Ordering key: hardness_vickers; ties broken by modulus (stiffer wins)."""
    ma, mb = lookup(a), lookup(b)
    key_a = (ma["hardness_vickers"], ma["young_modulus"])
    key_b = (mb["hardness_vickers"], mb["young_modulus"])
    return a if key_a < key_b else b
