"""run_dyad_membrane_review.py -- GLM-DYAD-01/02: the dyad reads the membrane captures.

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

# ── GLM-DYAD-02 preregistration (written into the shared context verbatim) ──
PREREG_BRIEF = """PREREGISTERED COMPARISON UNDER TEST (declared before these captures were made):

STATEMENT: removing floor overlap -- a rigid +0.5 m PRESENTATION lift of the
uploaded geometry along the engine's vertical axis, applied IDENTICALLY to
both captures -- improves surface legibility without changing the accepted
physical geometry.
PREDICTION: with the lift, the rim and the centre are distinguishable, so a
raised-centre state and a flat state can be told apart in the images.
FALSIFIER: the earlier depth/banding ambiguity persists, the physical
geometry changed, or the centre height remains visually unresolved (an
unresolved height is recorded INCONCLUSIVE for this visual comparison).

The two images below are a PAIR captured with identical presentation lift,
camera, render mode and lighting; they differ ONLY in their accepted
physical state (declared under each). Use their DIFFERENCE to answer what is
visible -- observations only, with uncertainty.
"""

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


def declared_from_sidecar(label: str, sc: dict) -> str:
    """The declared state of one image, built ONLY from its recorded
    sidecar (never guessed): physical state of record, presentation lift,
    camera, and the at-capture blob corroboration."""
    st = sc.get("state", {})
    lift = sc.get("presentation_lift", {})
    cam = sc.get("camera", {})
    corr = sc.get("blob_corroboration") or sc.get("blob_position_hash_at_capture")
    h = st.get("centre_height_b2_z_m")
    height_txt = (f"The PHYSICAL centre height above the rim plane in this "
                  f"state is {h} m (recorded from the accepted geometry; "
                  f"this is separate from the presentation lift below). ") if \
        h is not None else ""
    return (f"gamma = {st.get('gamma_J_per_m2')} J/m^2; optimizer terminal "
            f"state: iteration {st.get('iteration')}, energy "
            f"{st.get('energy_J')} J. {height_txt}Uploaded geometry carries "
            f"a RIGID PRESENTATION LIFT of +{lift.get('metres')} m along the "
            f"engine's vertical axis, IDENTICAL in both images of this pair "
            f"(the physical geometry of record is hashed unchanged). "
            f"Camera: radius {cam.get('radius')}, theta {cam.get('theta')}, "
            f"phi {cam.get('phi')} rad; render mode fill+wireframe. "
            f"Uploaded position bytes were verified against the engine's "
            f"persisted snapshot at capture time: {corr}.")


def pair_facts_from_sidecars(scs: list[dict]) -> str:
    """RUN AND RENDER FACTS for a comparison pair, derived from the two
    sidecars: what is identical, what differs."""
    a, b = scs
    ca, cb = a["camera"], b["camera"]
    la = a["presentation_lift"]["metres"]
    lb = b["presentation_lift"]["metres"]
    same_cam = ca == cb
    same_lift = la == lb
    ha = a["state"].get("centre_height_b2_z_m")
    hb = b["state"].get("centre_height_b2_z_m")
    return (
        "PAIR FACTS (from the recorded sidecars of these two captures):\n\n"
        f"- Identical presentation: rigid vertical lift = {la} m on BOTH "
        f"images (same lift: {same_lift}); render mode fill+wireframe; "
        "lighting is the engine's default.\n"
        f"- Camera: radius {ca.get('radius')}, theta {ca.get('theta')}, "
        f"phi {ca.get('phi')} rad -- identical in both images: {same_cam}.\n"
        "- The surface sits LIFTED clear of the engine floor plane; the "
        "engine's ground grid, floor and shadow plane are BELOW it and "
        "separated, so any banding/depth-fighting with the floor plane is "
        "a renderer property, not a mesh property.\n"
        "- Render mode: fill + wireframe WITH the opt-in edge-contrast "
        "feature active (the serving engine logged 'edge-contrast wireframe: "
        "created' at start, GLM-DEMO-CONTRAST-01): triangle edges and the "
        "rim are drawn in a CONSTANT LIGHT colour (~8-bit 230,230,242), "
        "distinctly brighter than the grey fill (~157, measured). The "
        "wireframe includes the six spokes that meet at the centre vertex; "
        "fill and lighting are otherwise unchanged from previous rounds.\n"
        f"- The two uploaded states differ ONLY in the centre vertex height "
        f"along the vertical rail: the DECLARED PHYSICAL centre heights are "
        f"{ha} m and {hb} m (recorded from each accepted geometry). The "
        f"visible raised-vs-flat difference comes from these heights, NOT "
        f"from the presentation lift, which is identical on both.\n"
        "- Each image is a full 2560x1440 window frame captured over HTTP "
        "from a separately launched demo engine instance; no other mesh "
        "was uploaded between the two captures.")


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    # CAPTURES may be overridden on the CLI: --captures label=DIR/PNG.png
    # (repeatable). Default: the round-2 top-down pair from GLM-DYAD-01.
    args_iter = sys.argv[2:]
    new_caps = []
    i = 0
    while i < len(args_iter):
        if args_iter[i] == "--captures" and i + 1 < len(args_iter):
            label, path = args_iter[i + 1].split("=", 1)
            p = Path(path)
            if not p.is_absolute():
                p = (ROOT / p).resolve()
            new_caps.append({"label": label, "dir": p.parent, "png": p.name,
                             "state": "(declared in the pair context below)"})
            i += 2
        else:
            i += 1
    caps = new_caps or CAPTURES
    round_tag = sys.argv[1] if len(sys.argv) > 1 else "r1"
    shared = SHARED
    declared_override = {}
    if new_caps:
        # Pair mode: declared states + run facts come from the SIDECARS.
        scs = []
        for cap in caps:
            sc_path = cap["dir"] / (cap["png"].rsplit(".", 1)[0] +
                                    ".capture.json")
            sc = json.loads(sc_path.read_text(encoding="utf-8"))
            scs.append(sc)
            declared_override[cap["label"]] = declared_from_sidecar(
                cap["label"], sc)
        shared = (PHYSICS_BRIEF + "\n\n" + pair_facts_from_sidecars(scs) +
                  "\n\n" + PREREG_BRIEF + "\n\n" + QUESTIONS)
    outdir = ROOT / "docs" / "evidence" / "membrane_window_demo" / f"dyad_{round_tag}_{stamp}"
    outdir.mkdir(parents=True, exist_ok=False)

    ok, served, reason = senses.can_see()
    record = {
        "schema": "chimera-dyad-membrane-review-v1",
        "utc": stamp,
        "task": "GLM-DYAD-01/GLM-DYAD-02",
        "eye_ready": ok, "served_model": served, "eye_reason": reason,
        "pinned_model_file": str(Path(ROOT / "Saved" / "dyad_model.txt")
                                  .exists() and
                                  (ROOT / "Saved" / "dyad_model.txt").read_text().strip()),
        "protocol": "docs/THE_DYAD_PROTOCOL.md",
        "one_image_per_call": True,
        "shared_context": shared,
        "human_acceptance": "NOT CLAIMED (reserved to Alan)",
        "gpu_dynamics_claim": "NONE",
        "comparison_pair": len(caps) == 2,
        "preregistration": PREREG_BRIEF if new_caps else None,
        "images": [],
    }

    for cap in caps:
        png_path = cap["dir"] / cap["png"]
        png_bytes = png_path.read_bytes()
        declared = declared_override.get(cap["label"], cap["state"])
        prompt = (f"You are reviewing ONE image from a physics visualization "
                  f"run. Image label: {cap['label']}.\n\n"
                  f"DECLARED STATE OF THIS IMAGE: {declared}\n\n" + shared)
        report = senses.watch_one(str(png_path), prompt)
        rec = {
            "label": cap["label"],
            "png": str(png_path if png_path.is_absolute()
                       else png_path.relative_to(ROOT.resolve())),
            "png_sha256": hashlib.sha256(png_bytes).hexdigest(),
            "png_bytes": len(png_bytes),
            "declared_state": declared,
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
