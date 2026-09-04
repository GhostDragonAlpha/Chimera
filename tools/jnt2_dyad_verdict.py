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
            lines.append(f"{jj['name']}: theta={jj.get('theta', 0):.3f} deg "
                         f"(pack flex stop {jj['flex']:.1f}) — posed to FULL FLEXION")
    try:
        ch = get("/studio_chrome")
        lines.append(f"fps: {ch.get('fps', 0):.0f} (under capture load)")
    except Exception:
        pass
    return "\n".join(lines)


THE_ASK = """## THE ASK
The creature's arms are posed with BOTH ELBOWS AT FULL FLEXION (+125 degrees,
the anatomically measured bone stop). The skin at a deep fold is the hardest
case for any rig: this is exactly where the previous skinning law TEARED the
surface, and the fix being verified tonight is a new 2-bone blend.

Look at the ELBOWS — where each forearm folds against its upper arm, both sides:
1. Is the skin CONTINUOUS across each elbow crease, or do you see a tear,
   gap, hole, or overlap at the fold? (Judge each arm separately.)
2. Does each folded arm read as a plausible bent limb (a smooth crease), or
   does the surface look stretched, pinched, smeared, or rubbery?
3. Any other visible defect anywhere in the frame?

Answer in three numbered parts matching these questions. Judge only what you
can see in this one image."""

message = BRIEFING.read_text(encoding="utf-8", errors="replace").strip() + \
    "\n\n## LIVE STATE (the engine's own numbers at this instant)\n" + \
    live_state_lines() + "\n\n---\n\n" + THE_ASK

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
