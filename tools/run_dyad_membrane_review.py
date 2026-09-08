"""run_dyad_membrane_review.py -- GLM-DYAD-01: the dyad reads the membrane captures.

Follows docs/THE_DYAD_PROTOCOL.md and ChimeraEngine/senses.py:
- ONE image per senses.watch_one call (the one-image wall; N images = N calls,
  aggregated afterwards).
- PYTHONIOENCODING=utf-8 (the caller sets it; the dyad emits typographic chars).
- No timeouts added (operator decree) -- senses handles the wait internally.
- Structured, NON-LEADING questions: ask what is visible, never whether the
  expected feature is visible (the r7 contamination lesson is law).
- The PHYSICAL CONTEXT is supplied as scene briefing (GLM-DYAD-01 amendment):
  what the object is, what the energy/force law is, what the optimizer seeks,
  what gamma=0 does, what doubling does and does not imply. The prediction is
  context, not permission: the dyad is told numerical evidence -- not
  screenshots -- establishes energy and force correctness, and is asked for
  observations and uncertainty.
- Actual run data (camera values, accepted states, geometry, rendering) come
  from the recorded evidence files, not guessed screen directions.
- Everything is recorded: served model, per-image questions, full context,
  image sha256, raw responses, finish reasons -> evidence JSON + the protocol's
  dyad_log.jsonl (written by senses itself).

Verdict classes stay separate: this tool produces the DYAD verdict ONLY. It
never manufactures human (Alan) acceptance and makes no GPU-dynamics claim.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
sys.path.insert(0, str(TOOLS))

import senses  # noqa: E402  (the protocol's documented interface)

CAPTURES = [
    {
        "label": "dyad2top_gamma0_bump_topdown",
        "dir": ROOT / "docs/evidence/membrane_window_demo/20260908T173201.273793Z",
        "png": "dyad2top_gamma0_bump_topdown.png",
        "state": ("zero gamma = 0 J/m^2, viewed near-top-down. The optimizer "
                  "took ZERO steps (status 'stationary' at iteration 0): the "
                  "geometry is the UNTOUCHED initial fixture -- the centre is "
                  "raised 0.125 m above the rim plane (a low cone: height "
                  "0.125 m over a 1.0 m rim radius). Seen from nearly "
                  "overhead, the raised centre should lie near the middle of "
                  "the hexagon with the wireframe spokes converging on it."),
    },
    {
        "label": "dyad2top_gamma1_flat_topdown",
        "dir": ROOT / "docs/evidence/membrane_window_demo/20260908T173204.430256Z",
        "png": "dyad2top_gamma1_flat_topdown.png",
        "state": ("positive gamma = 1 J/m^2, viewed near-top-down from the "
                  "same diagnostic camera. The optimizer RAN to its terminal "
                  "state: status 'stagnated' after 126 accepted steps; energy "
                  "2.5980761647224426 J -- the exact area of a FLAT regular "
                  "hexagon of side 1 m. The expected geometry is essentially "
                  "flat: centre height 4.146e-09 m (numerically zero)."),
    },
]

# The physical context (GLM-DYAD-01 amendment), verbatim scene explanation.
PHYSICS_BRIEF = """PHYSICAL CONTEXT (read before answering; it is background, not a checklist):

The object is six triangles joined around one centre vertex. The six outer
vertices are fixed in a flat hexagonal rim. The centre can move only
perpendicular to the rim plane.

Its energy is U = gamma x total triangle area. Forces are the negative
gradient of that energy. For positive gamma, the optimizer seeks less area,
so the raised centre approaches the rim plane. At gamma=0 this model
produces no force, so the initial bump remains.

This is an area-minimization experiment. It contains no certified
elasticity, bending stiffness, water pressure, gravity or contact dynamics.
Optimization iterations are not physical time.

At identical geometry, doubling gamma doubles calculated energy and force;
that alone does not require a visible shape change.

IMPORTANT LIMIT: numerical evidence (the recorded energy and force values)
establishes energy and force correctness. A screenshot cannot. Your role
here is to report what is VISIBLE, with uncertainty -- the physical
prediction above gives context, not permission to report a feature that is
not visible."""

# Actual run/render facts, from the recorded evidence (not guessed).
RUN_FACTS = """RUN AND RENDER FACTS (from the recorded evidence of the run that produced these images):

- Geometry (frozen fixture B2, mapped into the engine's coordinate system): 7
  vertices, 6 triangles. Rim = 6 vertices on a hexagon of radius 1.0 m lying
  IN the engine's floor plane; the centre sits ON the vertical axis through
  the hexagon centre (height above the floor = the fixture's centre height:
  0.125 m in the zero-gamma image, numerically zero in the positive-gamma
  image). All six rim edges are 1.0 m long. The surface color is a flat
  neutral grey (R=G=B=0.60,0.60,0.65) on every triangle; the render mode is
  FILLED TRIANGLES PLUS WIREFRAME EDGES, so the rim outline and the six
  spokes to the centre should be visible as lines.
- Camera (identical for both images, a DIAGNOSTIC view requested by a
  previous review round, set explicitly and recorded): orbit radius 3.5,
  theta 0.0 rad, phi 1.45 rad (~83 degrees -- NEAR-TOP-DOWN), looking at
  the origin. The engine's Vulkan renderer lights
  the scene from above with default engine lighting; the engine's standard
  ground grid and studio chrome may also be visible.
- Each image is a full 2560x1440 window frame captured over HTTP from a
  separately launched demo engine instance (built from this exact source
  commit; executable hash recorded). No other mesh was uploaded between
  captures; each capture's uploaded vertex bytes were verified byte-identical
  to the engine's persisted snapshot for that capture."""

QUESTIONS = """QUESTIONS (answer each with its number; give observations and your uncertainty; if something is not visible, say NOT VISIBLE rather than guessing):

1. What geometry is visibly distinguishable in this image? Describe shapes,
   edges and surfaces you can actually see, and where they are in the frame.
2. Can you resolve whether the centre of the hexagonal surface is offset
   from the plane of its outer rim (a bump or a depression)? If yes, which
   and how clearly; if not, what prevents it?
3. Is this image consistent with the declared state I gave for it? Answer
   consistent / inconsistent / cannot determine, with your reasoning.
4. Could viewpoint, occlusion, lighting, shading or rendering style explain
   any apparent discrepancy between what you see and the declared state?
   What ADDITIONAL evidence (a different view, marker, overlay or render
   mode) would distinguish a real geometry difference from a rendering
   effect?
5. Name the single worst visual problem in this image, if any."""

SHARED = PHYSICS_BRIEF + "\n\n" + RUN_FACTS + "\n\n" + QUESTIONS


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    round_tag = sys.argv[1] if len(sys.argv) > 1 else "r1"
    outdir = ROOT / "docs" / "evidence" / "membrane_window_demo" / f"dyad_{round_tag}_{stamp}"
    outdir.mkdir(parents=True, exist_ok=False)

    ok, served, reason = senses.can_see()
    record = {
        "schema": "chimera-dyad-membrane-review-v1",
        "utc": stamp,
        "task": "GLM-DYAD-01",
        "eye_ready": ok, "served_model": served, "eye_reason": reason,
        "pinned_model_file": str(Path(ROOT / "Saved" / "dyad_model.txt")
                                  .exists() and
                                  (ROOT / "Saved" / "dyad_model.txt").read_text().strip()),
        "protocol": "docs/THE_DYAD_PROTOCOL.md",
        "one_image_per_call": True,
        "shared_context": SHARED,
        "human_acceptance": "NOT CLAIMED (reserved to Alan)",
        "gpu_dynamics_claim": "NONE",
        "images": [],
    }

    for cap in CAPTURES:
        png_path = cap["dir"] / cap["png"]
        png_bytes = png_path.read_bytes()
        prompt = (f"You are reviewing ONE image from a physics visualization "
                  f"run. Image label: {cap['label']}.\n\n"
                  f"DECLARED STATE OF THIS IMAGE: {cap['state']}\n\n" + SHARED)
        report = senses.watch_one(str(png_path), prompt)
        rec = {
            "label": cap["label"],
            "png": str(png_path.relative_to(ROOT)),
            "png_sha256": hashlib.sha256(png_bytes).hexdigest(),
            "png_bytes": len(png_bytes),
            "declared_state": cap["state"],
            "prompt_chars": len(prompt),
            "served_model": senses._last_served_model(),
            "finish_reason": senses.last_finish_reason(),
            "raw_response": report,
        }
        record["images"].append(rec)
        print(f"=== {cap['label']} (sha256 {rec['png_sha256'][:16]}...) "
              f"served={rec['served_model']} finish={rec['finish_reason']}")
        print((report or "NO RESPONSE (eye dark)")[:4000])
        print()

    (outdir / "dyad_review.json").write_text(
        json.dumps(record, indent=2), encoding="utf-8")
    print(f"recorded -> {outdir / 'dyad_review.json'}")
    return 0 if all(i["raw_response"] for i in record["images"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
