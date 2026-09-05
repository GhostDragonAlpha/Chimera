"""dyad_shot.py — THE ONE-SHOT LAW (operator directive, 2026-09-04).

"you only focus on taking one picture and then getting a response and then
programming based on that ... you can supply the camera angle for each shot
as it'll be mandatory to move the camera for between each shot"

So: NO batch scans. One deliberate shot -> one eye read -> the answer drives
the next edit -> repeat. The camera angle is MANDATORY (--theta or a full
--v); a shot that reuses the previous angle is refused, because a question
asked from a lazy framing gets a lazy answer.

Flow:
  1. verify the eye (served model reported, never assumed)
  2. save the operator's current view (restored at the end)
  3. stage the demanded camera: scratch bookmark with exact v[8] -> recall
  4. quiesce the glass (structure-stable, the scan's own law)
  5. capture glass (default) or frame, compact losslessly
  6. one eye read: briefing + live engine state + THE ASK
  7. write report.json, print the answer, restore the operator's view

The shared dyad log (Saved/dyad/dyad_log.jsonl) receives the read via
senses.see as usual — one log, one source of truth.
"""
import argparse
import json
import sys
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import dyad_scan as scan          # noqa: E402  (grab/compact/quiesce/briefing/live_state)
import senses                     # noqa: E402  (the eye; timeouts disabled by decree)
from dyad_scan import req_json    # noqa: E402

ENGINE = scan.URL


def cam_bookmarks() -> dict:
    d = req_json("GET", "/cameras")
    return {b["name"]: b["v"] for b in d.get("bookmarks", [])}


def cam_save_exact(name: str, v) -> str:
    r = req_json("POST", "/cameras", {"op": "save", "name": name, "v": list(v)})
    if not r.get("ok"):
        raise RuntimeError(f"bookmark save failed: {r}")
    return r.get("name", name)


def cam_recall(name: str) -> None:
    r = req_json("POST", "/cameras", {"op": "recall", "name": name})
    if not r.get("ok"):
        raise RuntimeError(f"recall '{name}' failed: {r}")


def derive_v(args) -> list:
    """Full 8-float camera from a known base + the demanded angle. theta is
    mandatory — a shot without a moved camera is refused by law."""
    marks = cam_bookmarks()
    base_name = args.base_bookmark
    if base_name not in marks:
        raise RuntimeError(f"base bookmark '{base_name}' not found; have: {sorted(marks)}")
    v = list(marks[base_name])[:8]
    if args.v:
        parts = [float(x) for x in args.v.split(",")]
        if len(parts) != 8:
            raise RuntimeError("--v needs exactly 8 floats: r,theta,phi,tx,ty,tz,px,py")
        return parts
    if args.theta is None:
        raise RuntimeError(
            "THE ONE-SHOT LAW: the camera angle is mandatory. Pass --theta "
            "(radians) or --v \"r,theta,phi,tx,ty,tz,px,py\". A shot from the "
            "previous angle is a lazy shot.")
    v[1] = args.theta
    if args.radius is not None:
        v[0] = args.radius
    if args.phi is not None:
        v[2] = args.phi
    if args.target:
        v[3], v[4], v[5] = [float(x) for x in args.target.split(",")]
    return v


def main() -> int:
    ap = argparse.ArgumentParser(description="one shot -> one eye read")
    ap.add_argument("--theta", type=float, default=None,
                    help="camera azimuth (MANDATORY unless --v)")
    ap.add_argument("--radius", type=float, default=None)
    ap.add_argument("--phi", type=float, default=None)
    ap.add_argument("--target", default=None, help='"tx,ty,tz"')
    ap.add_argument("--v", default=None,
                    help='full camera "r,theta,phi,tx,ty,tz,px,py"')
    ap.add_argument("--base-bookmark", default="fit_dyad",
                    help="bookmark supplying the values you do not override")
    ap.add_argument("--name", default="shot", help="shot label for files")
    ap.add_argument("--channel", default="glass", choices=["glass", "frame"])
    ap.add_argument("--crop", default=None, help='"x,y,w,h"')
    ap.add_argument("--prompt", default=None, help="THE ASK (inline)")
    ap.add_argument("--prompt-file", default=None)
    ap.add_argument("--save-view", default=None,
                    help="bookmark name for the operator's pre-shot view "
                         "(default: auto '_pre_shot_<ts>'); '' disables restore")
    a = ap.parse_args()

    if not a.prompt and not a.prompt_file:
        ap.error("the ask is mandatory: --prompt or --prompt-file")
    ask = (Path(a.prompt_file).read_text(encoding="utf-8").strip()
           if a.prompt_file else a.prompt.strip())
    if a.crop:
        scan.CROP = tuple(int(x) for x in a.crop.split(","))

    # 1. the eye must be alive before anything moves
    model = senses.dyad_model()
    print(f"eye: {model}")

    out = scan.SAVED / "dyad_shots" / f"{time.strftime('%Y-%m-%d_%H%M%S')}_{a.name}"
    out.mkdir(parents=True, exist_ok=True)
    scan.OUT = out

    # 2. preserve the operator's framing (recall-restorable by name)
    pre_name = ""
    if a.save_view != "":
        pre_name = a.save_view or f"_pre_shot_{time.strftime('%H%M%S')}"
        nm = req_json("POST", "/cameras", {"op": "save", "name": pre_name})
        pre_name = nm.get("name", pre_name)
        print(f"operator view saved as '{pre_name}' (restored at the end)")

    # 3. stage the demanded camera — exact v through the render-thread discipline
    v = derive_v(a)
    scratch = "_shot_scratch"
    cam_save_exact(scratch, v)
    cam_recall(scratch)
    print(f"camera: r={v[0]:.3f} theta={v[1]:.3f} phi={v[2]:.3f} "
          f"target=({v[3]:.2f},{v[4]:.2f},{v[5]:.2f})")
    time.sleep(0.8)

    # 4. the glass must settle before the shutter
    scan.quiesce("shot")

    # 5. capture + compact (crop applies inside compact, the scan's law)
    raw = out / f"{a.name}.png"
    raw.write_bytes(scan.grab(a.channel))
    small = out / f"{a.name}_compact.png"
    nbytes = scan.compact(raw, small)
    print(f"shot: {raw.name} -> {small.name} ({nbytes} B)")

    # 6. one read: knowledge channel + THE ASK
    message = scan.compose_message(ask)
    t0 = time.time()
    answer = senses.see(str(small), message)
    dt = time.time() - t0

    report = {
        "run_id": out.name, "model": model,
        "camera": {"v": v, "base_bookmark": a.base_bookmark,
                   "theta_demanded": a.theta if a.v is None else None},
        "channel": a.channel, "crop": scan.CROP,
        "ask": ask, "answer": answer,
        "read_seconds": round(dt, 1),
        "operator_view_bookmark": pre_name,
    }
    (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"read: {dt:.0f}s -> {out / 'report.json'}")

    # 7. hand the machine back to the operator
    if pre_name:
        cam_recall(pre_name)
        print(f"operator view restored from '{pre_name}'")

    print("\n=== THE EYE SAYS ===\n")
    print(answer or "(the eye returned nothing)")
    return 0 if answer else 1


if __name__ == "__main__":
    sys.exit(main())
