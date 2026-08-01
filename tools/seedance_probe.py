"""seedance_probe.py -- send a membrane's clay to Seedance and measure whether the shape survived.

THE EXPERIMENT, and it has a sharp prediction attached.

`clay_export.py` turns a membrane into a white-model blockout. Seedance 2.5 accepts exactly that as
a STRUCTURAL control input -- ByteDance calls it clay-render referencing and says it locks spatial
layout while text directs material and lighting. But 2.5 has no public API yet (released 2026-07-31
on Jimeng and Doubao; BytePlus says "coming soon"), and what IS callable is Seedance 2.0 on fal.

READ 2.0'S SCHEMA AND THE PREDICTION FALLS OUT. There is no structural or depth field. Every
reference arrives through one undifferentiated `image_urls` / `video_urls` list, and the only thing
that says "use this for SHAPE" rather than "use this for STYLE" is a sentence in the prompt. That
is suggestion, not conditioning -- which is presumably why clay-render referencing is billed as new
in 2.5. So:

    PREDICTED: 2.0 will treat our clay as one more style hint, and the silhouette IoU of its
    output against our source geometry will be POOR.

If it comes back high, the reference path is stronger than the documentation implies and the
synthetic-capture loop can be built today. If it comes back at chance, we have bought that answer
for about a dollar and the loop waits for 2.5's API. Either result is worth the money; an untested
assumption is not.

HOW THE SHAPE IS SCORED, and its one honest weakness. `clay_check.py` segments on a known neutral
background -- exact, because clay_export renders on one. A GENERATED frame has whatever background
the model felt like, so this file estimates the background from the frame's own border and
thresholds on distance from it. That is a HEURISTIC and it is the weakest link in the measurement:
a busy generated background will degrade it. The prompt therefore asks for a plain backdrop, and
the per-frame numbers are printed so a bad segmentation is visible rather than averaged away.

MONEY. Nothing is spent without `--yes`. The estimate is printed first, every time.

    python tools/seedance_probe.py aHuman                 # dry run: cost and payload, no spend
    python tools/seedance_probe.py aHuman --yes           # actually call it
    python tools/seedance_probe.py aTerrain --tier fast --seconds 5 --yes
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "story"))
sys.path.insert(0, str(ROOT / "tools"))

# fal's published per-second rates. A VIDEO input multiplies the price by 0.6, which is why the
# orbit is sent as one clip rather than nine stills -- it is cheaper AND it stays under the
# 12-file cap that 2.0 imposes across all modalities.
TIERS = {
    "mini": ("bytedance/seedance-2.0/mini/reference-to-video", {"480p": 0.0721, "720p": 0.1547}),
    "fast": ("bytedance/seedance-2.0/fast/reference-to-video", {"480p": 0.2419, "720p": 0.2419}),
    "pro":  ("bytedance/seedance-2.0/reference-to-video",      {"480p": 0.3024, "720p": 0.3024}),
}
VIDEO_INPUT_MULTIPLIER = 0.6

# WHAT WE ASK FOR. Every clause is doing a job: naming @Video1 as the geometry is the only channel
# 2.0 gives us for structure; "plain backdrop" protects the segmentation the score depends on;
# "do not change the shape" is the instruction whose obedience is exactly what is being measured.
PROMPT = (
    "Use the geometry, camera motion and framing of @Video1 exactly. @Video1 is an untextured "
    "grey clay model: keep its silhouette, proportions and camera path unchanged, and do not add, "
    "remove or reshape anything. Replace only the SURFACE, rendering it as {material} under soft "
    "even daylight against a plain uncluttered backdrop. Photoreal, no text, no added objects."
)

# ── CAPTURE MODE: what a SAMPLE has to look like, which is not what a picture has to look like.
#
# The operator's correction, and it is the difference between a render and a measurement. This
# project's splat renderer lights from the viewport at runtime -- theSkin's subsurface wrap,
# theAtmosphere's Rayleigh path, aHuman's visor -- so a captured sample must carry the SURFACE'S
# OWN RESPONSE and nothing else. A key light baked into the sample is a light that can never be
# moved again, and a cast shadow is a piece of the floor pretending to be part of the object.
#
# So a capture take asks for: flat ambient only, no key, no shadow, no ground, black void. That is
# the standard condition for a relightable material capture and it happens to solve the measurement
# problem too -- a black void segments exactly, where the last take's floor and shadow defeated
# three different masks.
#
# NOTE THE ASYMMETRY, because it is easy to get backwards: the clay we SEND stays SHADED. A
# generator reads three-dimensional form from shading, so flat-lit input would hand it only a
# silhouette to work from. Shaded in, ambient out. Different jobs.
CAPTURE_PROMPT = (
    "Use the geometry, camera motion and framing of @Video1 exactly. @Video1 is an untextured grey "
    "clay model: keep its silhouette, proportions, scale in frame and camera path unchanged, and "
    "do not add, remove or reshape anything. Render only the object's own surface as {material}. "
    "LIGHTING: flat uniform ambient light from all directions, no key light, no directional light, "
    "no cast shadow, no contact shadow, no ground plane, no floor, no horizon. The background is "
    "PURE BLACK and completely empty. The object floats with nothing touching it. Photoreal "
    "material detail, no text, no added objects, no lens flare, no depth of field."
)


def clay_video(term, frames, arc, elev, dist, size, out_mp4, fps=12):
    """Render the orbit and write it as one MP4 -- the single video reference we send."""
    import numpy as np
    import cv2
    from PIL import Image
    from ChimeraEngine import splat_appearance as SA
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera
    from clay_export import clay, key_for, orbit_camera
    from matter import PX, PZ

    src = SA.membrane_buffer(term, 1.0)
    extent = float(np.linalg.norm(np.asarray(src)[:, PX:PZ + 1], axis=1).max()) or 1.0
    pipe = FullGPUPipeline(bg=(0.5, 0.5, 0.5))
    w = cv2.VideoWriter(str(out_mp4), cv2.VideoWriter_fourcc(*"mp4v"), fps, (size, size))
    stills = []
    for i in range(frames):
        pos, yaw, pitch = orbit_camera(extent, i, frames, arc, elev, dist)
        cam = FirstPersonCamera(pos, yaw=yaw, pitch=pitch)
        pipe.upload(clay(src, key_for(yaw, pitch)))
        im = np.asarray(Image.fromarray(pipe.render_from_gpu(cam, cam.params(size, size)))
                        .convert("RGB"))
        stills.append(im)
        w.write(im[:, :, ::-1])                       # cv2 wants BGR
    w.release()
    return stills, extent


def silhouette_black(img, tol=0.06):
    """Foreground against a BLACK VOID -- exact, not a heuristic.

    This is what capture mode buys. The previous take's figure stood on a floor with a cast
    shadow and a graded backdrop, and three different masks failed on it: border-colour grabbed
    the wall, edge-structure grabbed the shadow, and an outline matcher turned out to be
    degenerate (a terrain outline scored 0.900 against the astronaut, as well as the astronaut's
    own). Ask for a void and the mask stops being a research problem."""
    import numpy as np
    a = np.asarray(img, dtype=np.float32) / 255.0
    if a.ndim == 2:
        a = a[:, :, None]
    return a.max(axis=2) > tol


def silhouette(img, border=6, tol=0.10):
    """Foreground mask by distance from the frame's OWN border colour.

    THE HEURISTIC, stated plainly. clay_check can segment exactly because it knows the background
    is 0.5 grey. A generated frame has whatever background the model produced, so the border is
    used as a sample of it. This is the weakest measurement in the file: a busy or gradient
    backdrop will bleed into the mask, which is why the prompt asks for a plain one and why every
    frame's score is printed rather than only the mean."""
    import numpy as np
    a = np.asarray(img, dtype=np.float32) / 255.0
    if a.ndim == 2:
        a = a[:, :, None]
    edge = np.concatenate([a[:border].reshape(-1, a.shape[2]), a[-border:].reshape(-1, a.shape[2]),
                           a[:, :border].reshape(-1, a.shape[2]),
                           a[:, -border:].reshape(-1, a.shape[2])])
    bg = np.median(edge, axis=0)
    return np.linalg.norm(a - bg[None, None, :], axis=2) > tol


def iou(m1, m2):
    import numpy as np
    inter = float(np.logical_and(m1, m2).sum())
    union = float(np.logical_or(m1, m2).sum())
    return inter / max(union, 1.0)


def upload(path):
    """Get a public URL for a local file. fal_client if it is installed; otherwise say so plainly
    rather than failing three steps later."""
    try:
        import fal_client
    except ImportError:
        raise SystemExit(
            "This needs a public URL for the clay clip. Either:\n"
            "   pip install fal-client        (then this uploads for you)\n"
            "or pass --video-url <public url> if you have hosted it yourself.")
    return fal_client.upload_file(str(path))


def call_fal(model, payload, key):
    import requests
    r = requests.post(f"https://fal.run/{model}", timeout=900,
                      headers={"Authorization": f"Key {key}", "Content-Type": "application/json"},
                      json=payload)
    if r.status_code != 200:
        raise SystemExit(f"fal returned {r.status_code}: {r.text[:400]}")
    return r.json()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("membrane")
    ap.add_argument("--tier", default="mini", choices=sorted(TIERS))
    ap.add_argument("--resolution", default="480p", choices=["480p", "720p"])
    ap.add_argument("--seconds", type=int, default=4)
    ap.add_argument("--frames", type=int, default=24, help="clay frames in the reference clip")
    ap.add_argument("--arc", type=float, default=120.0)
    ap.add_argument("--elev", type=float, default=16.0)
    ap.add_argument("--dist", type=float, default=2.6)
    ap.add_argument("--size", type=int, default=480)
    ap.add_argument("--material", default="weathered rock and dry soil")
    ap.add_argument("--capture", action="store_true",
                    help="capture mode: ambient only, no shadow, black void -- a relightable "
                         "SAMPLE rather than a picture")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--video-url", default=None, help="skip upload; use this public URL")
    ap.add_argument("--out", default=None)
    ap.add_argument("--yes", action="store_true", help="actually spend money")
    a = ap.parse_args()

    model, rates = TIERS[a.tier]
    cost = rates[a.resolution] * a.seconds * VIDEO_INPUT_MULTIPLIER
    out = Path(a.out or (ROOT / "clay_exports" / f"probe_{a.membrane}"))
    out.mkdir(parents=True, exist_ok=True)

    prompt = (CAPTURE_PROMPT if a.capture else PROMPT).format(material=a.material)
    print(f"MEMBRANE   {a.membrane}")
    print(f"MODEL      {model}")
    print(f"REQUEST    {a.resolution}, {a.seconds}s, seed {a.seed}, 1 video reference")
    print(f"COST       {rates[a.resolution]:.4f}/s x {a.seconds}s x {VIDEO_INPUT_MULTIPLIER} "
          f"(video input) = ${cost:.3f}")
    print(f"PROMPT     {prompt}")
    print()

    print(f"rendering {a.frames} clay frames -> {out/'clay.mp4'}")
    stills, extent = clay_video(a.membrane, a.frames, a.arc, a.elev, a.dist, a.size,
                               out / "clay.mp4")
    print(f"   extent {extent:.4g} local")

    if not a.yes:
        print()
        print("DRY RUN. Nothing was sent and nothing was charged.")
        print(f"   the clay clip is at {out/'clay.mp4'} -- look at it before spending.")
        print(f"   re-run with --yes to spend ${cost:.3f}.")
        return 0

    key = os.environ.get("FAL_KEY")
    if not key:
        raise SystemExit("set FAL_KEY in the environment first")

    url = a.video_url or upload(out / "clay.mp4")
    print(f"reference clip: {url}")
    payload = {"prompt": prompt, "video_urls": [url], "resolution": a.resolution,
               "duration": str(a.seconds), "generate_audio": False, "seed": a.seed}
    (out / "request.json").write_text(json.dumps(payload, indent=1), encoding="utf8")

    t0 = time.time()
    res = call_fal(model, payload, key)
    print(f"generated in {time.time()-t0:.0f}s -> {res.get('video',{}).get('url','?')}")
    (out / "response.json").write_text(json.dumps(res, indent=1), encoding="utf8")

    import requests, cv2, numpy as np
    vid = out / "generated.mp4"
    vid.write_bytes(requests.get(res["video"]["url"], timeout=300).content)

    cap = cv2.VideoCapture(str(vid))
    gen = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        gen.append(fr[:, :, ::-1])
    cap.release()
    print(f"{len(gen)} generated frames")
    if not gen:
        raise SystemExit("no frames decoded from the generated video")

    # THE SCORE. Our clay frames and the generated frames are resampled onto a common count,
    # because the model chooses its own frame rate and duration. Same orbit, same order.
    n = min(len(stills), len(gen))
    print()
    print(f"{'frame':>6} {'silhouette IoU':>16}")
    ious = []
    for i in range(n):
        s = stills[int(i * (len(stills) - 1) / max(n - 1, 1))]
        g = gen[int(i * (len(gen) - 1) / max(n - 1, 1))]
        g = cv2.resize(g, (s.shape[1], s.shape[0]))
        seg = silhouette_black if a.capture else silhouette
        v = iou(silhouette(s), seg(g))     # the clay side is always exact: it renders on 0.5 grey
        ious.append(v)
        print(f"{i:>6} {v:>16.4f}")
    mean = sum(ious) / len(ious)
    worst = min(ious)
    print()
    print(f"MEAN IoU {mean:.4f}   WORST {worst:.4f}")
    print()
    # THE VERDICT, against the floor clay_check measured: appearance drift alone costs ~0.01 IoU,
    # so anything near 0.99 is geometry preserved and anything under ~0.7 is a different object.
    if mean >= 0.90:
        print("SHAPE SURVIVED. 2.0's reference path carries structure better than its schema "
              "implies -- the synthetic-capture loop can be built now.")
    elif mean >= 0.70:
        print("PARTIAL. The subject is recognisable but reshaped. Usable for style harvesting, "
              "NOT for geometry-faithful capture.")
    else:
        print("SHAPE NOT PRESERVED, which is what the schema predicted: with no structural field, "
              "2.0 treats clay as a style hint. The loop waits for 2.5's API.")
    (out / "score.json").write_text(json.dumps(
        {"membrane": a.membrane, "model": model, "mean_iou": mean, "worst_iou": worst,
         "per_frame": ious, "cost_usd": cost, "prompt": prompt}, indent=1), encoding="utf8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
