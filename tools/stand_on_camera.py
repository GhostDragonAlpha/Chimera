"""stand_on_camera.py -- THE MUSCULOSKELETAL STAND, ON CAMERA. M9's last unbuilt bridge.

docs/THE_RECORDED_SESSION_2.md named it: the session is driven by the Walker mover, so the stand
port "is proven in its own harness and has never been recorded." This records it -- through the
SAME rollout f3_stand.py judges (the proven stand_theta, the real parser, the two phases), just
with a dense frame grab, so the video and the number cannot disagree silently. The membrane is
stated in that doc; the falsifier is the frames themselves.

    python tools/stand_on_camera.py     # -> ChimeraEngine/output/ports/stand_on_camera/
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body
from stand_port import derive_stand_port, MYOBODY
from train_stand import joint_ids, seat_in_limits
from parser import Parser, default_registry
from f3_stand import THETA, CTRL_EVERY, PHASE1_SECS, PHASE2_MAX

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports" / "stand_on_camera"
FRAME_DT = 0.25               # s between frames -- ~28 frames over the two phases
RW, RH = 640, 480             # big enough to judge a posture by


def run() -> int:
    import mujoco
    from PIL import Image, ImageDraw
    if not THETA.exists():
        raise SystemExit(f"no {THETA} -- run `python tools/train_stand.py` first (rule 20).")
    theta = np.load(THETA)
    P = derive_stand_port()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    nu, jids = m.nu, joint_ids(m, mujoco)
    tgt = P["OUT pelvis_target_m"]
    parser = Parser(default_registry(theta, tgt, nu))

    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)      # one-time, at reset -- f3_stand's own construction

    ren = mujoco.Renderer(m, height=RH, width=RW)
    steps = int((PHASE1_SECS + PHASE2_MAX) / m.opt.timestep)
    phase2_start = int(PHASE1_SECS / m.opt.timestep)
    grab_every = int(FRAME_DT / m.opt.timestep)
    frames, zs = [], []
    slumped_at = None
    for k in range(steps):
        stand_on = k < phase2_start
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            q = d.qpos[3:7]
            pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]),
                                     1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            roll = float(np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]),
                                    1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            parser.set_verb("STAND", stand_on)
            u, _ = parser.command({"z": z, "pitch": pitch, "roll": roll})
            d.ctrl[:] = u if u is not None else 0.0
        mujoco.mj_step(m, d)
        if k % CTRL_EVERY == 0:
            zs.append(float(d.qpos[2]))
        if k % grab_every == 0 or k == steps - 1:
            ren.update_scene(d)
            px = ren.render().copy()
            img = Image.fromarray(px)
            draw = ImageDraw.Draw(img)
            t = k * m.opt.timestep
            draw.text((8, 6), f"t={t:4.2f}s  STAND {'ON ' if stand_on else 'OFF'}  "
                              f"pelvis {100.0 * float(d.qpos[2]) / tgt:.0f}%",
                      fill=(255, 255, 255))
            frames.append(img)
        if not stand_on and float(d.qpos[2]) < 0.5 * tgt:
            slumped_at = k * m.opt.timestep - PHASE1_SECS
            break                          # f3_stand's own phase-2 construction: stop at the slump
    ren.close()

    OUTDIR.mkdir(parents=True, exist_ok=True)
    for stale in OUTDIR.glob("frame_*.jpg"):
        stale.unlink()                      # this tool's own outputs only, never another run's
    for i, img in enumerate(frames):
        img.save(OUTDIR / f"frame_{i:02d}.jpg", quality=90)
    # the contact sheet -- the whole video at a glance, the blind read's WATCH shape
    cols = 4
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * RW // 2, rows * RH // 2), (10, 10, 20))
    for i, img in enumerate(frames):
        sheet.paste(img.resize((RW // 2, RH // 2)), ((i % cols) * RW // 2, (i // cols) * RH // 2))
    sheet_path = OUTDIR / "stand_on_camera_sheet.jpg"
    sheet.save(sheet_path, quality=92)

    held = 100.0 * min(zs[:int(PHASE1_SECS / (CTRL_EVERY * m.opt.timestep)) + 1]) / tgt
    print(f"[stand_on_camera] {len(frames)} frames -> {OUTDIR}")
    print(f"[stand_on_camera] phase 1 pelvis MIN {held:.1f}% of target "
          f"(f3_stand's bar: >= 90%)")
    print(f"[stand_on_camera] phase 2: "
          + (f"slumped in {slumped_at:.2f}s after release" if slumped_at is not None
             else "still upright -- the parser is decorative, FALSIFIER FIRED"))
    print(f"[stand_on_camera] sheet: {sheet_path} -- read it before believing this log.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
