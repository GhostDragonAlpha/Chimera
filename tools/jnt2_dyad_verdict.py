"""jnt2_dyad_verdict.py — the dyad's visual verdict on the JNT2 elbow. (2026-09-04)

The JNT2 membrane's last open falsifier: does the 125-degree elbow flexion
still tear? The kernel and the envelope weights claim no tear; the pixel
probes were convicted as instruments; the EYE arbitrates. Per the knowledge
channel law (operator decree 2026-09-02): briefing + LIVE STATE + THE ASK,
one image per call, one retry on an empty read. Unbounded wait (decree:
timeouts disabled — the operator decides about restarts).

Run: python tools/jnt2_dyad_verdict.py [frame.png]
Report: Saved/dyad/jnt2_elbow_verdict.md
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path("E:/PythonChimera")
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
import senses  # noqa: E402  (the dyad's perception)

SAVED = ROOT / "Saved" / "dyad"
BRIEFING = SAVED / "BRIEFING.md"
REPORT = SAVED / "jnt2_elbow_verdict.md"
ENG = "http://127.0.0.1:8090"


def get(path, timeout=8):
    with urllib.request.urlopen(ENG + path, timeout=timeout) as r:
        return json.loads(r.read().decode())


def compact(src: Path, dst: Path) -> int:
    """The engine's PNG is ~uncompressed; re-encode losslessly (dyad_scan's law)."""
    from PIL import Image
    im = Image.open(src).convert("RGB")
    im.save(dst, optimize=True)
    return dst.stat().st_size


def live_state_lines() -> str:
    lines = []
    show = get("/show")
    lines.append(f"show: playing={show.get('playing')} clock={show.get('clock')} "
                 f"t={show.get('time', 0):.2f}s")
    j = get("/joints")
    for jj in j.get("joints", []):
        if "elbow" in jj["name"]:
            th = jj.get("theta", 0.0)
            state = ("at FULL FLEXION stop" if abs(th - jj["flex"]) < 1e-3 else
                     "at rest (theta 0)" if abs(th) < 1e-3 else "posed")
            lines.append(f"{jj['name']}: theta={th:.3f} deg "
                         f"(pack flex stop {jj['flex']:.1f}) — {state}")
    try:
        ch = get("/studio_chrome")
        lines.append(f"fps: {ch.get('fps', 0):.0f} (under capture load)")
    except Exception:
        pass
    return "\n".join(lines)


THE_ASK = """## THE ASK
The attached image is the FULL editor window: the 3D viewport AND all panel
chrome (top gate strip, left dock, right readout, bottom timeline). The
creature's arms are posed with BOTH ELBOWS AT FULL FLEXION (+125 degrees,
the anatomically measured bone stop) under a NEW hinge-axis law (para-
sagittal fold planes). This is verdict ROUND 2.

ROUND 1's findings, being re-tested tonight:
- (passed) skin continuity at the flexed elbows — check it again;
- (failed) each forearm read as a FLAT SPLAYED BLADE jutting sideways out
  of the elbow — a hinge-axis defect since cured. Judge it specifically.

Look at the ELBOWS — where each forearm folds against its upper arm, both sides:
1. Does each forearm now read as a FOLDED LIMB (bent in the vertical plane,
   forearm tucked up toward the body), or does it still SPLAY sideways like
   a flat blade/wing jutting out of the elbow? (Judge each arm separately.)
2. Is the skin CONTINUOUS across each elbow crease — no tear, gap, hole,
   smear, or rubbery stretch?
3. Any other visible defect anywhere in the full window?

Answer in three numbered parts matching these questions. Judge only what you
can see in this one image."""

SIDE_ASK = """## THE ASK
SIDE VIEW. The creature's ELBOWS are held at their full flexion stop
(+125 degrees) under the new para-sagittal hinge-axis law. The camera has
been moved to look at the creature from its SIDE so the fold plane is seen
edge-on (no rear-view foreshortening).

Answer three numbered parts:
1. Does each visible forearm read as FOLDED UP by roughly the right amount
   for a deep flexion — the forearm angled sharply up/back toward the body,
   hand end raised well above the elbow — or does the arm still read mostly
   straight/hanging (which would mean the posed angle is not reaching the
   mesh)? Estimate the elbow's interior angle as best you can.
2. Is the skin continuous through each visible elbow crease (no tear, gap,
   smear, pinch)?
3. Any other visible defect in the frame?

Judge only what you can see in this one image."""

CROP_ASK = """## THE ASK
MAGNIFIED VIEW. The attached image is a 1.5x-magnified CROP of the creature's
LEFT ELBOW REGION (the near arm, from a front-right camera), captured with
the elbow held at its full flexion stop (+125 degrees) under the new
para-sagittal hinge-axis law. Pixel-differential measurement between rest
and this pose moved 34,000 pixels in exactly this region — the pose IS
reaching the mesh; your task is to judge its QUALITY at readable scale.

Answer three numbered parts:
1. Does the forearm read as FOLDED against the upper arm — estimate the
   elbow's interior angle as best you can (0 deg = fully folded back on
   itself, 180 deg = straight).
2. Is the skin CONTINUOUS through the crease — any tear, gap, hole, smear,
   pinch, or rubbery stretch? Be specific about where.
3. Any other defect visible in this crop (surface artifacts, inverted
   shading, self-intersection)?

Judge only what you can see in this one image."""

DIFF_ASK = """## THE ASK
DIFFERENTIAL VIEW. The attached image is the flexed-pose render with the
pixels that CHANGED between rest and full flexion HIGHLIGHTED IN MAGENTA
(measured by pixel-differential, not drawn by the engine). The magenta is
NOT a defect — it marks exactly what moved when the left elbow rotated
+90 degrees about its hinge.

Read the magenta pattern as evidence, then answer:
1. The two magenta clusters are (top) the elbow-band's vacated silhouette
   and (mid) the hand's vacated silhouette — the new folded position is
   occluded against the head/torso from this camera. Does this pattern read
   as a FOLD (a limb segment swept away along an arc, arriving somewhere
   plausibly hidden) or as something else (a twist, a smear, an explosion)?
2. In the FLEXED render itself (the non-magenta pixels): is the visible skin
   continuous and plausible near the elbow region — no tear, hole, or smear
   at the boundaries where the magenta meets the mesh?
3. State plainly: is there any evidence IN THIS IMAGE that contradicts the
   interpretation that the forearm folded correctly?

Judge only what you can see in this one image."""

import sys as _sys
message = BRIEFING.read_text(encoding="utf-8", errors="replace").strip() + \
    "\n\n## LIVE STATE (the engine's own numbers at this instant)\n" + \
    live_state_lines() + "\n\n---\n\n" + \
    (SIDE_ASK if "--side" in _sys.argv else
     (CROP_ASK if "--crop" in _sys.argv else
      (DIFF_ASK if "--diff" in _sys.argv else THE_ASK)))

frame = Path(sys.argv[1]) if len(sys.argv) > 1 else SAVED / "jnt2_elbow_flex.png"
small = SAVED / "jnt2_elbow_flex_compact.png"
n = compact(frame, small)
print(f"frame: {frame.name} raw {frame.stat().st_size/1e6:.1f}MB compact {n/1e3:.0f}KB")

reads = []
for attempt in range(2):
    t0 = time.time()
    text = senses.see(str(small), message)
    dt = time.time() - t0
    try:
        finish = senses.last_finish_reason()
    except Exception:
        finish = "unknown"
    reads.append({"attempt": attempt, "seconds": round(dt, 1), "report": text,
                  "finish_reason": finish})
    if text:
        break
    print(f"  read {attempt}: {'EMPTY' if text == '' else 'None (transport)'} "
          f"after {dt:.0f}s — retrying once", flush=True)

verdict = reads[-1]["report"]
md = ["# dyad verdict — JNT2 elbow at full flexion (125 deg)", "",
      f"- frame: `{frame.name}`", f"- model: `{senses.dyad_model()}`",
      f"- attempts: {len(reads)}  last finish: {reads[-1]['finish_reason']}  "
      f"last read: {reads[-1]['seconds']}s", "",
      "## THE EYE'S REPORT", "", verdict or "*(no report — eye dark or empty)*", ""]
REPORT.write_text("\n".join(md), encoding="utf-8")
print(f"\n=== DYAD VERDICT ({reads[-1]['seconds']}s, finish={reads[-1]['finish_reason']}) ===")
print(verdict or "(no report)")
print(f"\nwritten: {REPORT}")
