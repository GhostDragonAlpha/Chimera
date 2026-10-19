"""Reusable B4 cradle recipe extracted unchanged from its existing acceptance test."""
from tools.construction_packet import b2_scene_gen

G = b2_scene_gen.G
IDS = [l[0] for l in b2_scene_gen.STACK_LAYERS]      # base, mid, top
MASS = {l[0]: l[7] * (l[2] - l[1]) * (l[4] - l[3]) * (l[6] - l[5])
        for l in b2_scene_gen.STACK_LAYERS}
BLOCK_ID = "cradle_block"
# block: 60 x 40 x 60 mm timber (rho 600) -> 0.0864 kg (144 cm^3), standing
# on the ground 40 mm clear of the granite base on its +x side (its -x face
# at x = 0.34, the granite +x face at x = 0.30). The gap is deliberate: the
# granite yaws ~0.5 deg under the stack (measured, B3), and a touching face
# would leak that contact into every weld-force reading. The cradle
# connection is the WELD across the gap (virtual link points, below).
# Weight 0.848 N; ground friction at mu 0.3 caps at 0.254 N.
BLOCK_BOX = (0.34, 0.40, -b2_scene_gen.REST_SINK_M,
             0.04 - b2_scene_gen.REST_SINK_M, 0.12, 0.18)
BLOCK_MASS = 600 * (BLOCK_BOX[1] - BLOCK_BOX[0]) * (BLOCK_BOX[3] - BLOCK_BOX[2]) \
             * (BLOCK_BOX[5] - BLOCK_BOX[4])
BLOCK_COM = ((BLOCK_BOX[0] + BLOCK_BOX[1]) / 2, (BLOCK_BOX[2] + BLOCK_BOX[3]) / 2,
             (BLOCK_BOX[4] + BLOCK_BOX[5]) / 2)
# weld anchors: four rigid links, each pair one world point captured into
# BOTH parts' local frames -> zero rest length, zero preload. Physically a
# bracket bonded into the block's core and bolted to the granite; the
# finite-area connector carries relative motion without any contact across
# the 40 mm gap. The patch is CENTRED ON THE BLOCK COM: a patch centroid
# off the COM transfers a yaw couple through the weld and the tilted
# equilibrium carries the wrong force (measured: 5 cm off, 0.27 deg yaw,
# 0.385 N instead of the parallel-spring value).
WELD_ANCHORS = [(0.355, 0.00, 0.135), (0.385, 0.00, 0.165),
                (0.355, 0.02, 0.135), (0.385, 0.02, 0.165)]


def block_doc(pid: str = BLOCK_ID, x0: float = BLOCK_BOX[0],
              mass_scale: float = 1.0) -> dict:
    d = b2_scene_gen.box_document(
        pid, x0, x0 + (BLOCK_BOX[1] - BLOCK_BOX[0]), BLOCK_BOX[2], BLOCK_BOX[3],
        BLOCK_BOX[4], BLOCK_BOX[5], 600, 0.3)
    if mass_scale != 1.0:
        for key in ("mass_kg",):
            d[key] *= mass_scale
        d["inertia_com_local_kg_m2"] = [v * mass_scale
                                        for v in d["inertia_com_local_kg_m2"]]
        d["ground"]["k_n_per_m"] *= mass_scale
        d["ground"]["c_n_s_per_m"] *= mass_scale
    return d

