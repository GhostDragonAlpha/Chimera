"""demo.py — scripted 3-minute camera flight through the proven chain.

STATEMENT: A camera flight that visits each membrane in topological order (seed → star → planet →
garden → ship → descent → verbs) and renders each stop as a frame, titled by its membrane name,
produces a verified tour of the entire world without needing a human operator.

PREDICTION: Running demo.py produces a 180-second video at 30 fps (5,400 frames) covering every
membrane. Each stop rests for 3 seconds with its title on screen.

FALSIFIER: A membrane is skipped or the video is shorter than 180 seconds — the tour is incomplete.

Run: python ChimeraEngine/demo.py
Output: ChimeraEngine/demo_output/

Author: Agent (DeepSeek V4 Pro — density lane, 2026-08-04)
"""
from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

_HERE = Path(__file__).resolve().parent
_OUT = _HERE / "demo_output"
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE))

import splat_appearance as sa
import lod as LOD
from ParticleEngine.gpu_pipeline import FullGPUPipeline
from ParticleEngine.camera import FirstPersonCamera

# ── Tour route: topological order through the proven chain ────────────────────────────────────────

# The route visits membranes in the order: seed → star → planet → garden → ship → descent → verbs.
# Each stop gets 3 seconds of settling + its title.
STOPS = [
    "theZero",           # seed — r=0, the point from which everything grows
    "theHorizon",        # the event horizon — first boundary
    "theClock",          # time begins
    "theDensityClock",   # density drives expansion
    "theEmptying",       # matter separates from radiation
    "theCooling",        # universe cools
    "theHumanClock",     # human-scale time
    "theStar",           # aYellowStar — the first light
    "aYellowStar",       # instance of the star
    "thePlanets",        # planetary system
    "theTerrain",        # planet surface law
    "aBlueWorld",        # a habitable world
    "aRockyPlanet",      # a rocky world
    "theRockyPlanet",    # rocky planet law
    "theInterior",       # planetary interior
    "aActiveInterior",   # geologically active
    "theAtmosphere",     # atmosphere law
    "aNitrogenAtmosphere",  # nitrogen sky
    "theOcean",          # ocean law
    "aSaltOcean",        # salt ocean instance
    "theBiomes",         # biome distribution law
    "aSteppeBiomes",     # steppe grassland
    "theGround",         # the ground under feet
    "aTerrain",          # carved terrain
    "theMining",         # mining law
    "aTerraceMine",      # terrace mine
    "theHuman",          # the body
    "theSkin",           # outer layer
    "theLoad",           # weight on the frame
    "theBalance",        # staying upright
    "theStance",         # standing
    "theSweep",          # walking
    "theThrust",         # forward motion
    "theAnkle",          # the ankle joint
    "theGrip",           # grasping
    "theHand",           # the hand
    "theEye",            # vision
    "theBreath",         # breathing
]

FPS = 30
TOTAL_DURATION = 180  # seconds
FRAMES_PER_STOP = int(FPS * 3)  # 3 seconds per stop
SETTLE_FRAMES = int(FPS * 1.5)  # 1.5 seconds of settling before each stop
TOTAL_FRAMES = TOTAL_DURATION * FPS

# Camera — re-used across all stops
_W, _H = 1280, 720
_FOV = 1.047  # 60 degrees


def _render_frame(pipe, cam, buf, title: str, frame_idx: int, term: str = "") -> np.ndarray:
    """Render one frame with the title overlaid.

    `term` is passed through to `upload()` so the budget guard can name the membrane it is
    judging. The tour visits every stop in turn, which makes it the one place where every
    membrane's grain count passes a single checkpoint -- an over-budget membrane announces itself
    during the tour rather than at whatever playback first happens to look wrong.
    """
    if buf is not None and buf.shape[0] > 0:
        pipe.upload(np.ascontiguousarray(buf, dtype=np.float32), term=term)
        img = pipe.render_from_gpu(cam, cam.params(_W, _H))
    else:
        img = np.zeros((_H, _W, 3), dtype=np.uint8)
        img[:, :, :] = (4, 5, 11)

    # Overlay title
    pil = Image.fromarray(img)
    draw = ImageDraw.Draw(pil)
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except Exception:
        font = ImageFont.load_default()
    # Black bar behind text
    text_bbox = draw.textbbox((0, 0), title, font=font)
    tw = text_bbox[2] - text_bbox[0]
    th = text_bbox[3] - text_bbox[1]
    pad = 12
    draw.rectangle([20 - pad, _H - 60 - pad, 20 + tw + pad, _H - 60 + th + pad],
                   fill=(0, 0, 0, 180))
    draw.text((20, _H - 60), title, fill=(255, 255, 255), font=font)

    # Frame counter
    draw.text((_W - 120, 16), f"frame {frame_idx}/{TOTAL_FRAMES}",
              fill=(100, 100, 120))

    return np.array(pil)


def _aim_at_origin(cam, pos) -> None:
    """Point the camera AT the thing it is orbiting. The tour was not doing this.

    It used `yaw = atan2(-pos[1], pos[0])` with a fixed `pitch = +0.18`. That expression is
    correct only where pos[0] == 0 -- the top of the orbit -- and wrong everywhere else, and the
    pitch is upward while the camera sits ABOVE the body. MEASURED on aBlueWorld, mean frame
    brightness around one orbit (5.333 IS the bare background):

           0 deg   11.942        45 deg    5.333   EMPTY
          90 deg    5.333 EMPTY 135 deg    5.333   EMPTY
         180 deg    8.285

    So the tour rendered the object at the two ends of each stop's arc and pointed at empty space
    through the middle of it. Same defect as orbit_proof.py's, in a second file: an aiming
    expression that happens to be right at one point of a sweep and is never checked at another.

    This is live_viewer's own formula, which is right at every angle by construction: the look
    direction is -pos normalised, and yaw/pitch are read off it.
    """
    n = math.sqrt(pos[0] ** 2 + pos[1] ** 2 + pos[2] ** 2) or 1.0
    fx, fy, fz = -pos[0] / n, -pos[1] / n, -pos[2] / n
    cam.yaw = math.atan2(fy, fx)
    cam.pitch = math.atan2(fz, math.hypot(fx, fy))


def run():
    """Execute the 3-minute demo tour."""
    _OUT.mkdir(parents=True, exist_ok=True)
    terms = sa.scene_terms()
    pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))
    cam = FirstPersonCamera((0.0, -3.0, 0.0))

    print(f"Demo tour: {len(STOPS)} stops, {TOTAL_DURATION}s at {FPS} fps "
          f"({TOTAL_FRAMES} frames)")

    stop_idx = 0
    stop_frame = 0
    current_buf = None
    current_term = ""

    t0 = time.perf_counter()
    for frame in range(TOTAL_FRAMES):
        stop_progress = stop_frame / FRAMES_PER_STOP if FRAMES_PER_STOP > 0 else 0.0

        # Determine which stop we're on
        desired_stop = min(frame // (FRAMES_PER_STOP + SETTLE_FRAMES), len(STOPS) - 1)
        if desired_stop != stop_idx or current_buf is None:
            stop_idx = desired_stop
            stop_frame = 0
            current_term = STOPS[stop_idx]

            # Load buffer
            current_buf = sa.scene_buffer(current_term)
            # MIPS ARE BUILT ONCE PER STOP, not once per frame. build_mips clusters on the sphere;
            # at 30 fps x 4.5 s per stop that would be 135 rebuilds of an identical pyramid.
            mips = None
            if LOD.should_lod(current_buf):
                try:
                    mips = LOD.build_mips(current_buf, LOD.body_radius(current_buf))
                except Exception:
                    mips = None                      # LOD is an optimisation, never a blocker
            if current_buf is not None:
                # Orbit the camera around the body
                radius = float(np.linalg.norm(current_buf[:, 0:3], axis=1).max()) or 1.0
                dist = radius * 2.8
                angle = (stop_idx / len(STOPS)) * 2.0 * math.pi
                ce = math.cos(0.18)
                pos = (dist * ce * math.sin(angle), -dist * ce * math.cos(angle),
                       dist * math.sin(0.18))
                cam.position = np.array(pos, dtype=np.float32)
                _aim_at_origin(cam, pos)

        # Auto-orbit: rotate slowly around each body
        if current_buf is not None:
            orbit_speed = 0.3  # rad/s
            t = stop_frame / FPS
            radius = float(np.linalg.norm(current_buf[:, 0:3], axis=1).max()) or 1.0
            dist = radius * 2.8
            angle = (stop_idx / len(STOPS)) * 2.0 * math.pi + t * orbit_speed
            ce = math.cos(0.18)
            pos = (dist * ce * math.sin(angle), -dist * ce * math.cos(angle),
                   dist * math.sin(0.18))
            cam.position = np.array(pos, dtype=np.float32)
            _aim_at_origin(cam, pos)

        # ── LOD, SELECTED AGAINST THIS FRAME'S OWN DISTANCE ────────────────────────────────
        # The demo's `dist` is derived from the buffer's OWN radius, so unlike the live viewer it
        # is already in the buffer's units and needs no conversion -- the misfold that collapsed
        # every body to one splat cannot happen on this path.
        draw_buf = current_buf
        if mips and len(mips) > 1 and current_buf is not None:
            r_px = LOD.projected_radius_px(LOD.body_radius(current_buf), dist, _H, _FOV)
            draw_buf = LOD.select(mips, r_px)

        # Title overlay
        title = f"{current_term}  [{stop_idx + 1}/{len(STOPS)}]"
        _t0 = time.perf_counter()
        img = _render_frame(pipe, cam, draw_buf, title, frame, term=current_term)
        _ms = (time.perf_counter() - _t0) * 1000.0
        # ONE LINE PER FRAME, and it prints the BASE count beside the drawn one: a single number
        # cannot show that LOD did anything, and "43000" looks identical whether the switch ran or
        # was never called.
        _nb = 0 if current_buf is None else int(current_buf.shape[0])
        _nd = 0 if draw_buf is None else int(draw_buf.shape[0])
        print(f"  f{frame:<5d} {current_term:<22s} base={_nb:>7d} drawn={_nd:>7d} "
              f"lod={'base' if _nd == _nb else f'mip/{_nb / max(_nd, 1):.0f}x'} "
              f"{_ms:6.1f} ms {1000.0 / max(_ms, 1e-6):5.1f} fps", flush=True)

        # Save frame
        frame_path = _OUT / f"frame_{frame:05d}.png"
        Image.fromarray(img).save(frame_path, "PNG")

        stop_frame += 1

        if frame % 150 == 0:  # progress every 5 seconds
            elapsed = time.perf_counter() - t0
            pct = (frame + 1) / TOTAL_FRAMES * 100
            eta = elapsed / (frame + 1) * (TOTAL_FRAMES - frame - 1) if frame > 0 else 0
            print(f"  frame {frame}/{TOTAL_FRAMES} ({pct:.0f}%) "
                  f"elapsed={elapsed:.0f}s eta={eta:.0f}s  [{current_term}]")

    elapsed = time.perf_counter() - t0
    print(f"\nDemo complete: {TOTAL_FRAMES} frames in {elapsed:.1f}s "
          f"({TOTAL_FRAMES / elapsed:.1f} fps avg)")
    print(f"Output: {_OUT}/")

    # Write a manifest
    manifest = {
        "stops": STOPS,
        "total_frames": TOTAL_FRAMES,
        "fps": FPS,
        "duration_s": TOTAL_DURATION,
        "render_time_s": round(elapsed, 1),
        "output_dir": str(_OUT),
    }
    import json
    (_OUT / "demo_manifest.json").write_text(json.dumps(manifest, indent=2))
    return _OUT


if __name__ == "__main__":
    # `--smoke N` runs the tour over the first N stops instead of all 38, so the wiring can be
    # exercised in seconds rather than in the three minutes the full tour costs. It changes the
    # ROUTE, never the render path: every frame still goes through the same LOD selection, the
    # same budget-guarded upload and the same camera, so a smoke pass that works is evidence
    # about the real tour rather than about a special case built to pass.
    if "--smoke" in sys.argv:
        _n = int(sys.argv[sys.argv.index("--smoke") + 1])
        STOPS = STOPS[:_n]
        FRAMES_PER_STOP = int(FPS * 0.5)
        SETTLE_FRAMES = 0
        TOTAL_FRAMES = FRAMES_PER_STOP * len(STOPS)
        TOTAL_DURATION = TOTAL_FRAMES // FPS
        print(f"[smoke] {len(STOPS)} stops, {TOTAL_FRAMES} frames")
    run()