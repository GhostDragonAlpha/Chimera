"""run_dyad_gpu_demo_review.py -- GLM-GPU-DEMO-03: the dyad reads the
GPU-DRIVEN demo captures.

Same law as tools/run_dyad_membrane_review.py (GLM-DYAD-01/02), applied to
the GPU runtime gate's captures (docs/evidence/membrane_gpu_demo_runtime/):
- ONE image per senses.watch_one call (the one-image wall).
- PYTHONIOENCODING=utf-8; no timeouts added (operator decree).
- Structured, NON-LEADING questions (the r7 contamination lesson is law):
  ask what is visible, never whether the expected feature is visible.
- The PHYSICAL CONTEXT briefing (operator-supplied text, quoted verbatim)
  precedes the questions; actual camera/state/render facts come from the
  recorded sidecars, not guessed screen directions.
- Observations are kept separate from numerical facts: numerical evidence --
  not screenshots -- establishes energy and force correctness. The dyad is
  told this explicitly.
- Everything recorded: served model, prompts, full context, image sha256,
  raw responses, finish reasons -> evidence JSON + dyad_log.jsonl.

Verdict classes stay separate: this tool produces the DYAD verdict ONLY. It
never manufactures human acceptance and makes no GPU-dynamics claim beyond
what the runtime record already certifies numerically.
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

RUN = ROOT / "docs" / "evidence" / "membrane_gpu_demo_runtime"

PHYSICAL_BRIEFING = (
    "This object is six triangles joined around one centre vertex. "
    "The six outer vertices are fixed in a flat hexagonal rim. "
    "The centre can move only perpendicular to the rim plane.\n\n"
    "Its energy is U = gamma x total triangle area. Forces are the "
    "negative gradient of that energy. For positive gamma, the optimizer "
    "seeks less area, so the raised centre approaches the rim plane. "
    "At gamma=0 this model produces no force, so the initial bump remains.\n\n"
    "This is an area-minimization experiment. It contains no certified "
    "elasticity, bending stiffness, water pressure, gravity or contact "
    "dynamics. Optimization iterations are not physical time.\n\n"
    "At identical geometry, doubling gamma doubles calculated energy "
    "and force; that alone does not require a visible shape change."
)

# The GPU runtime facts, from the recorded sidecars of the run under review
# (20260909T135205.479224Z; GPU-computed, RTX-class desktop Vulkan path --
# device identity not printed by this engine build, so hardware is NOT named).
RUN_FACTS = {
    "source": "docs/evidence/membrane_gpu_demo_runtime/20260909T135205.479224Z",
    "engine": "chimera_engine.exe (isolated MSVC build), port 8091, --no-restore",
    "camera": {"cam_radius": 6.0, "cam_theta": 0.0, "cam_phi": 0.7,
               "note": "camera POSTed to /camera before /frame; oblique view, "
                       "phi 0.7 rad above the rim plane; engine world y-up"},
    "render": {"mode": "fill only (mesh_mode_ 0): the demo path sets no "
                       "render mode and the wire pass requires mesh_mode_ >= 1, "
                       "so NO wireframe edges are drawn (CORRECTED during "
                       "GLM-GPU-DEMO-03: the earlier 'slotmode 2' claim was "
                       "imported from the CPU-demo /mesh_bin law and does not "
                       "apply to the GPU demo path)",
               "presentation": "rigid B2(z-up)->engine(y-up) rotation plus a "
                               "0.5 m presentation lift; the lift is render "
                               "presentation only"},
    "states": {
        "raised": {"gamma_J_m2": 0.0, "terminal": "stationary", "iteration": 0,
                   "energy_J": 0.0, "centre_xyz_m": [0.0, 0.0, 0.125],
                   "note": "centre raised 0.125 m over a 1.0 m rim radius"},
        "relaxed": {"gamma_J_m2": 1.0, "terminal": "stagnated", "iteration": 126,
                    "energy_J": 2.59807611,
                    "note": "GPU-relaxed; CPU law terminal energy "
                            "2.5980761647224426 J; centre height ~0 m"},
    },
}


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    if len(sys.argv) < 2:
        run_dir = sorted(RUN.glob("2*"))[-1]
    else:
        run_dir = RUN / sys.argv[1]
    images = [
        ("gpu_demo_raised_gamma0", run_dir / "raised_gamma0.png",
         "The INITIAL-HEIGHT state under ZERO gamma: the optimizer took zero "
         "steps (stationary at iteration 0), so this is the untouched initial "
         "fixture -- centre raised 0.125 m above the rim plane."),
        ("gpu_demo_final_relaxed", run_dir / "final_relaxed.png",
         "The FINAL state after 126 accepted optimization steps at gamma = "
         "1 J/m^2 (terminal 'stagnated'): the centre should now lie close to "
         "the rim plane."),
    ]

    ok, served, reason = senses.can_see()
    if not ok:
        print(f"BLOCKED: the dyad eye is dark: {reason}", flush=True)
        print("OPERATOR ACTION REQUIRED: load the vision model in LM Studio "
              "(Chimera never loads or picks a model for you). Then rerun.",
              flush=True)
        return 2

    out = {
        "what": "GLM-GPU-DEMO-03 dyad review of the GPU-driven membrane demo",
        "utc": datetime.now(timezone.utc).isoformat(),
        "served_model": served,
        "run_facts": RUN_FACTS,
        "physical_briefing": PHYSICAL_BRIEFING,
        "calls": [],
    }

    for label, png, state_text in images:
        if not png.exists():
            out["calls"].append({"label": label, "error": f"missing {png}"})
            continue
        ctx = json.dumps(RUN_FACTS, indent=1)
        prompt = (
            "You are reviewing one screenshot of a real-time 3D engine. "
            "Answer with observations and uncertainty; say plainly when "
            "something cannot be judged from this image.\n\n"
            "PHYSICAL CONTEXT (what the object is):\n" + PHYSICAL_BRIEFING + "\n\n"
            "THE STATE THIS IMAGE SHOWS:\n" + state_text + "\n\n"
            "RECORDED RUN FACTS (camera, render mode, numerical state):\n"
            + ctx + "\n\n"
            "QUESTIONS (answer by number):\n"
            "1. What geometry is visibly distinguishable in this image? "
            "Describe what you actually see, including any floor, grid, "
            "panels, or other scene content.\n"
            "2. Can you locate the membrane's centre vertex and its outer "
            "rim? What tells you where each is?\n"
            "3. Based on what is visible, is the centre's offset from the "
            "rim plane resolvable in this view? Say 'resolvable', "
            "'not resolvable', or 'uncertain', and justify from the image.\n"
            "4. Are the image contents consistent with the stated state, "
            "inconsistent, or cannot you tell? Explain from what is visible.\n"
            "5. Could viewpoint, occlusion, lighting, or rendering explain "
            "any apparent discrepancy? What additional evidence would "
            "distinguish it?\n"
            "6. Name the single worst visual problem in this image, if any.\n\n"
            "Note: numerical evidence (recorded energies, forces, state IDs) "
            "establishes the law's correctness; this review is about what a "
            "viewer can SEE."
        )
        print(f"[dyad] {label}: calling senses.watch_one ...", flush=True)
        report = senses.watch_one(str(png), prompt)
        rec = {
            "label": label,
            "image": str(png),
            "image_sha256": sha256_file(png),
            "served_model": served,
            "prompt_chars": len(prompt),
            "report": report,
        }
        out["calls"].append(rec)
        print(f"[dyad] {label}: {'OK' if report else 'NO REPORT'}", flush=True)

    ev = run_dir / "dyad_gpu_demo_review.json"
    ev.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"evidence: {ev}", flush=True)

    for c in out["calls"]:
        if c.get("report"):
            print(f"\n===== {c['label']} =====\n{c['report'][:2000]}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
