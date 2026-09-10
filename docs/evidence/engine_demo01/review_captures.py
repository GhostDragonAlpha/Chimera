"""Review the retained runtime captures, one image per DYAD call.

Requires the owning engine-demo-01 claim and GPU/DYAD admission before execution.
This records visual observations; it does not infer physics or human acceptance.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
import senses

PROMPT = """You are reviewing one actual capture from a C++/Vulkan engineering
demonstration of a triangulated membrane with a fixed boundary. GPU relaxation
minimizes surface energy; its iterations are not physical time. The capture is
from a recorded run, not a live view. No numerical values or state label are
provided because this review concerns only visible evidence.

Prior reviews of this demonstration found height interpretation inconclusive
from some views, and an earlier presentation lacked useful triangle edges.
Those are historical observations, not assertions about this image.

Answer these numbered questions using only the supplied image:
1. Describe the visible geometry, silhouette, triangle edges and background.
2. What visual evidence, if any, establishes the center's height relative to
the boundary? State any ambiguity; do not infer a numerical displacement.
3. Identify the single most important visibility or presentation problem.
4. Which claims cannot be determined from this image alone?
Do not infer correct forces, conservation, convergence, timing, exact GPU
submission identity or human acceptance from a screenshot.
"""


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def main():
    output = Path(__file__).parent / "dyad_round1"
    output.mkdir(exist_ok=False)
    write_json(output / "preregistration.json", {
        "statement": "The retained captures permit bounded visual inspection.",
        "prediction": "The eye returns complete descriptions of both captures.",
        "falsifier": "Missing image, unavailable eye, empty or truncated response.",
        "prompt": PROMPT,
        "acceptance": "VISUAL_OBSERVATIONS_ONLY",
    })
    can_see, served, reason = senses.can_see()
    write_json(output / "can_see.json", {
        "can_see": can_see, "served_model": served, "reason": reason,
        "finish_reason": senses.last_finish_reason(),
    })
    if not can_see:
        return 1
    run = ROOT / "docs/evidence/membrane_gpu_demo_runtime/20260910T153744.673179Z"
    complete = True
    for index, name in enumerate(("raised_gamma0.png", "final_relaxed.png"), 1):
        path = run / name
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        started = time.time()
        response = senses.watch_one(str(path), PROMPT)
        finished = time.time()
        finish_reason = senses.last_finish_reason()
        usable = bool(response) and finish_reason == "stop"
        complete = complete and usable
        write_json(output / f"image_{index}.json", {
            "image": str(path.relative_to(ROOT)), "image_sha256": digest,
            "prompt": PROMPT, "raw_response": response,
            "served_model": senses._last_served_model(),
            "finish_reason": finish_reason, "started_unix": started,
            "finished_unix": finished, "response_complete": usable,
            "physics_acceptance": "NOT_INFERRED", "human_acceptance": "NOT_CLAIMED",
        })
        print(f"image_{index}: complete={usable}; finish={finish_reason}", flush=True)
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
