"""clay_export.py -- turn a membrane into a white-model blockout a video model can be steered by.

WHY THIS EXISTS. Seedance 2.5 (ByteDance, 2026-07-31) takes a TEXTURELESS 3D MODEL as a control
input -- their "clay render referencing" / "3D white-model blockout", which they describe as
locking spatial layout, character poses, motion paths and camera angles while text directs the
material and lighting. That is a socket, and this story has been emitting exactly what plugs into
it for weeks without anyone noticing: every membrane's `emit()` produces geometry with a known
camera, which is what a clay render IS.

WHAT THAT MAKES POSSIBLE, and it is not cutscenes. `Construction/SPLAT_DNA_WORKFLOW.md` turns real
3DGS scans into material genomes. The thing it has always been short of is SCANS OF THINGS THAT DO
NOT EXIST -- this world's rock, a suit nobody has sewn, a creature nobody has photographed. A video
model conditioned on our geometry is a SYNTHETIC CAPTURE RIG for exactly those:

    membrane emits clay -> the model renders it -> 3DGS reconstructs -> material genome
           ^                                                                 |
           +--------------------- back into the membrane --------------------+

AND IT DOES NOT BREAK THE PROJECT'S OWN RULE. THE_GROWTH says: measure -> sample -> prove, never
generate -> trust. Under clay conditioning the model is NOT inventing the scene. We supply the
geometry and the camera; it supplies appearance only -- and appearance is already the one thing
this pipeline sources from measurement rather than derivation. Better, it is CHECKABLE: reconstruct
from the generated views and compare against the clay that was fed in. If the reconstruction's
geometry does not match the membrane's own emit, the model hallucinated structure and the take is
refused. Two independent messengers, our geometry and its reconstruction. That is a dyad, and the
prove gate becomes the acceptance test for synthetic capture.

WHAT "CLAY" MEANS HERE, precisely:
  * ALL COLOUR IS STRIPPED. Albedo, emission, material tint -- gone, replaced by one neutral grey.
    A clay render that carries colour is not a control input, it is a suggestion, and the whole
    point is that the generator supplies appearance and we supply form.
  * SHADING IS FORM ONLY. One key light, Lambert on the surface normal, a little ambient so the
    unlit side does not go black and lose its silhouette. Nothing physical is being claimed --
    this frame is not a render of the world, it is a description of its SHAPE.
  * THE CAMERA IS WRITTEN DOWN. Every frame's pose is exported beside it, because the poses are
    what a reconstruction needs later, and because a camera you cannot state is a camera you
    cannot reproduce.

RUN:
    python tools/clay_export.py theHuman --frames 48
    python tools/clay_export.py aTerraceMine --frames 24 --orbit 120 --still
    python tools/clay_export.py theInterior --frames 30 --cycle      (also advance the membrane's
                                                                      own clock across the shot)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "story"))

# THE ONE GREY. Mid-grey with a hint of warmth, which is what physical modelling clay reads as and
# what every white-model convention in film layout uses. It is not a colour choice about the world;
# it is the ABSENCE of one, stated once so nothing downstream has to guess.
CLAY_RGB = (0.62, 0.60, 0.575)
# THE KEY RIDES WITH THE CAMERA, and the first version got this wrong. A world-fixed light means
# the subject is backlit on whichever frames the camera swings past it -- measured: frames 3 and 4
# of an eight-frame orbit went to near-silhouette, which is the one thing a blockout must never do,
# because a frame with no readable form is a frame that controls nothing. Film turntables light
# from the camera for exactly this reason. Stated as an offset from the camera's own direction.
KEY_OFFSET_DEG = (-38.0, 30.0)   # (yaw left of camera, elevation above it)
AMBIENT = 0.28                 # enough that the shadow side keeps its silhouette


def key_for(yaw, pitch):
    """The key light direction for a camera at this yaw and pitch -- see KEY_OFFSET_DEG."""
    y = yaw + math.radians(KEY_OFFSET_DEG[0])
    p = pitch + math.radians(KEY_OFFSET_DEG[1])
    # the camera looks ALONG (cos y cos p, sin y cos p, -sin p); the key shines the same way, so
    # the vector FROM the surface TO the light is its negation.
    return (-math.cos(y) * math.cos(p), -math.sin(y) * math.cos(p), math.sin(p))


def clay(buf, key=None):
    """Strip a membrane's buffer down to form: one grey, shaded by normal, nothing else.

    THE COLOUR HAS TO GO. A membrane's buffer carries hard-won appearance -- theSkin's measured
    melanin filter, theBiomes' Whittaker cells, theInterior's blackbody ramp. All of it is deleted
    here on purpose. Sending a coloured frame to a generator asks it to reproduce a colour we
    already have; sending clay asks it for the one thing we cannot derive."""
    import numpy as np
    from matter import PX, PZ, CR, CB, ALPHA, SIZE, NX, NZ, TYPE, SOLID, AR, AB

    b = np.array(buf, dtype=np.float32, copy=True)
    n = len(b)
    if not n:
        return b

    nrm = b[:, NX:NZ + 1]
    mag = np.linalg.norm(nrm, axis=1)
    k = np.array(key if key is not None else (0.45, -0.78, 0.44), np.float32)
    k = k / np.linalg.norm(k)
    # points with no normal (a volume, a glow) get flat ambient -- they have no surface to shade
    lam = np.where(mag > 1e-6, np.clip(nrm @ k / np.maximum(mag, 1e-9), 0.0, 1.0), 0.0)
    shade = (AMBIENT + (1.0 - AMBIENT) * lam).astype(np.float32)

    col = (np.array(CLAY_RGB, np.float32)[None, :] * shade[:, None]).astype(np.float32)
    b[:, CR:CB + 1] = col
    b[:, AR:AB + 1] = np.array(CLAY_RGB, np.float32)[None, :]
    # EVERYTHING IS OPAQUE MATTER. A glow is a light source, and a light source in a blockout is a
    # lie about shape -- theInterior's molten core would read as a hole. Solid, so it has an
    # outline the generator can hold onto.
    b[:, TYPE] = SOLID
    b[:, ALPHA] = np.clip(b[:, ALPHA] * 0.0 + 0.98, 0.0, 1.0)
    return b


def orbit_camera(extent, i, n, arc_deg, elev_deg, dist_mult):
    """A camera on a circle around the subject. Returns (position, yaw, pitch).

    THE PATH IS A CIRCLE ON PURPOSE. A reconstruction wants views spread around the subject with
    known baselines, and an orbit is the shortest description of that which a person can also
    reproduce by hand. The radius comes from the membrane's OWN extent -- a boundary supplies its
    own scale, so nothing here is hand-framed."""
    a = math.radians(arc_deg) * (i / max(n - 1, 1)) if n > 1 else 0.0
    r = dist_mult * max(extent, 1e-9)
    el = math.radians(elev_deg)
    pos = (r * math.cos(a) * math.cos(el), r * math.sin(a) * math.cos(el), r * math.sin(el))
    yaw = math.atan2(-pos[1], -pos[0])
    pitch = math.atan2(-pos[2], math.hypot(pos[0], pos[1]))
    return pos, yaw, pitch


def export(term, frames, arc_deg, elev_deg, dist_mult, width, height, cycle, still, out_dir):
    import numpy as np
    from PIL import Image
    from ChimeraEngine import splat_appearance as SA
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera
    from matter import PX, PZ

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    probe = SA.membrane_buffer(term, 1.0)
    if probe is None or not len(probe):
        print(f"{term} emits nothing")
        return 1
    extent = float(np.linalg.norm(np.asarray(probe)[:, PX:PZ + 1], axis=1).max()) or 1.0

    pipe = FullGPUPipeline(bg=(0.5, 0.5, 0.5))     # a NEUTRAL backdrop: no sky, no space, no world
    cams = []
    for i in range(frames):
        # the membrane's own clock advances across the shot unless the subject is meant to hold
        t = 0.0 if still else (i / frames if cycle else 1.0)
        pos, yaw, pitch = orbit_camera(extent, i, frames, arc_deg, elev_deg, dist_mult)
        cam = FirstPersonCamera(pos, yaw=yaw, pitch=pitch)
        p = cam.params(width, height)
        pipe.upload(clay(SA.membrane_buffer(term, t), key_for(yaw, pitch)))
        Image.fromarray(pipe.render_from_gpu(cam, p)).save(out / f"clay_{i:04d}.png")
        cams.append({"frame": i, "t": t, "position": list(pos), "yaw": yaw, "pitch": pitch,
                     "fov": float(p.fov), "width": width, "height": height})

    # THE POSES TRAVEL WITH THE FRAMES. A reconstruction needs them, and a camera nobody wrote
    # down is a camera nobody can reproduce.
    (out / "cameras.json").write_text(json.dumps({
        "membrane": term,
        "what": ("a white-model blockout: geometry and camera only. ALL COLOUR IS STRIPPED on "
                 "purpose -- the generator supplies appearance, this supplies form."),
        "extent_local": extent,
        "clay_rgb": list(CLAY_RGB),
        "key_light": "camera-relative", "key_offset_deg": list(KEY_OFFSET_DEG),
        "ambient": AMBIENT,
        "orbit_arc_deg": arc_deg,
        "elevation_deg": elev_deg,
        "distance_over_extent": dist_mult,
        "membrane_clock": "held at t=0" if still else ("advanced 0..1 across the shot" if cycle
                                                       else "held at t=1"),
        "frames": cams,
    }, indent=1), encoding="utf8")
    print(f"{term}: {frames} clay frames + cameras.json -> {out}")
    print(f"   extent {extent:.4g} local, orbit {arc_deg:g} deg at {elev_deg:g} deg elevation")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("membrane")
    ap.add_argument("--frames", type=int, default=48)
    ap.add_argument("--orbit", type=float, default=360.0, help="arc swept, degrees")
    ap.add_argument("--elev", type=float, default=12.0, help="camera elevation, degrees")
    ap.add_argument("--dist", type=float, default=2.6, help="camera distance / membrane extent")
    ap.add_argument("--width", type=int, default=768)
    ap.add_argument("--height", type=int, default=768)
    ap.add_argument("--cycle", action="store_true",
                    help="advance the membrane's own clock across the shot as well as the camera")
    ap.add_argument("--still", action="store_true", help="hold the membrane at t=0")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or (ROOT / "clay_exports" / a.membrane)
    return export(a.membrane, a.frames, a.orbit, a.elev, a.dist, a.width, a.height,
                  a.cycle, a.still, out)


if __name__ == "__main__":
    sys.exit(main())
