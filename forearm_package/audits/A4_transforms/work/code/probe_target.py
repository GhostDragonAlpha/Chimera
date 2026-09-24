"""Probe: source chimanoid bone lengths vs mesh-measured target lengths (both in m)."""
from __future__ import annotations
import numpy as np
from synthetic_fixtures import load_real
from intake import global_site_positions
from mesh_target import MonkeyTarget


def main() -> int:
    real = load_real()
    mt = MonkeyTarget()
    sw = global_site_positions(real)

    def src_len(body: str) -> float:
        b = real.body_by_name[body]
        child = next((x for x in real.bodies if x.parent == body), None)
        if child is not None:
            return float(np.linalg.norm(child.pos_global - b.pos_global))
        own = [s for s in real.sites if s.body == body and s.referenced_by]
        far = max((sw[s.name] for s in own), key=lambda p: np.linalg.norm(p - b.pos_global))
        return float(np.linalg.norm(far - b.pos_global))

    pairs = {
        "femur_r": ("hip_L", "knee_L"), "tibia_r": ("knee_L", "ankle_L"),
        "humerus": ("shoulder_L", "elbow_L"), "ulna": ("elbow_L", "wrist_L"),
        "thorax_dummy": ("spine_lower", "spine_mid"), "thorax": ("spine_mid", "spine_upper"),
    }
    print(f"{'segment':13s} {'source_m':>9s} {'target_m':>9s} {'ratio':>7s}")
    for src, (a, b) in pairs.items():
        s = src_len(src)
        t = mt.bone_len(a, b)
        print(f"{src:13s} {s:9.4f} {t:9.4f} {t / s:7.2f}")

    print()
    print("foot/hand tip measures (probe for plausibility):")
    for tip in ("hand_tip", "foot_tip", "toe_tip"):
        print(f"  {tip} = {np.round(mt.tips[tip], 4)} m  |wrist-tip|={np.linalg.norm(mt.tips[tip]-mt.joint_pos('wrist_L')):.4f}" if tip == "hand_tip" else f"  {tip} = {np.round(mt.tips[tip], 4)} m")
    print(f"  ankle_L = {np.round(mt.joint_pos('ankle_L'),4)}  knee_L = {np.round(mt.joint_pos('knee_L'),4)}")
    print(f"  foot_tip dist from ankle = {np.linalg.norm(mt.tips['foot_tip']-mt.joint_pos('ankle_L')):.4f}")
    print(f"  tail_tip = {np.round(mt.joint_pos('tail_tip'),4)} (is toe_tip near the tail? |toe_tip-tail_tip|={np.linalg.norm(mt.tips['toe_tip']-mt.joint_pos('tail_tip')):.4f})")
    print(f"  toe_tip dist from ankle = {np.linalg.norm(mt.tips['toe_tip']-mt.joint_pos('ankle_L')):.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())