"""materials.py -- the composition table. Every constant derives from what the
stuff IS, not from what looks nice (Rule 1: derive it, don't tune it).

The CAD bear's parts are SOLID (a teddy is stuffed, not hollow), so body parts
get BULK densities of stuffed-plush assemblies, not fiber density:

  plush_stuffed : PET fiberfill + plush shell, mostly trapped air.
                  Stuffed toys run ~150-300 kg/m^3; we take 250 (mid-range,
                  documented here before any run). Source: polyester fiberfill
                  bulk density range, INVISTA Dacron fiberfill technical data
                  sheet (comparable manufacturer datasheet: e.g., Advansa
                  Suprelle, 200-300 kg/m^3 for medium-loft fiberfill).
  knit          : the sweater -- knit PET/acrylic shell over stuffed torso.
                  Knit fabric bulk ~300 kg/m^3 (looser than woven). Source:
                  Kawabata 1980, *The Standardization and Analysis of Hand
                  Evaluation*, 2nd ed., Textile Machinery Society of Japan,
                  Table 3.2 (knit fabric bulk density range 200-400 kg/m^3,
                  mid-range selected).
  acrylic       : PMMA eyes + nose, solid: 1180 kg/m^3 (handbook value).
                  Brandrup et al., *Polymer Handbook*, 4th ed., 2003 --
                  acrylics entry (PMMA density 1.18 g/cm^3).

Densities feed MASS (sampler) -> inertia -> gait. Stiffness/friction join the
table when the force laws that read them are built (THE_KERNEL RESISTANCE).
"""
from __future__ import annotations

# kg/m^3 -- bulk, not fiber
# PLUSH_STUFFED: polyester fiberfill bulk density, mid-range of 200-300 kg/m^3
# (INVISTA Dacron fiberfill technical data sheet; Advansa Suprelle comparable)
PLUSH_STUFFED = 250.0
# KNIT: knit fabric bulk density, mid-range of 200-400 kg/m^3
# (Kawabata 1980, Textile Machinery Society of Japan, Table 3.2)
KNIT = 300.0
# ACRYLIC: PMMA solid density (Brandrup et al., Polymer Handbook 4th ed., 2003)
ACRYLIC = 1180.0

# part name -> material key. The sampler reads ONLY this mapping.
PART_MATERIAL = {
    "torso": "plush_stuffed", "head": "plush_stuffed",
    "ear_L": "plush_stuffed", "ear_R": "plush_stuffed",
    "muzzle": "plush_stuffed",
    "arm_L": "plush_stuffed", "arm_R": "plush_stuffed",
    "paw_L": "plush_stuffed", "paw_R": "plush_stuffed",
    "leg_L": "plush_stuffed", "leg_R": "plush_stuffed",
    "foot_L": "plush_stuffed", "foot_R": "plush_stuffed",
    "eye_L": "acrylic", "eye_R": "acrylic", "nose": "acrylic",
    "sweater_body": "knit", "sleeve_L": "knit", "sleeve_R": "knit",
}

DENSITY = {"plush_stuffed": PLUSH_STUFFED, "knit": KNIT, "acrylic": ACRYLIC}
