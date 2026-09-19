"""Scenario qualification: tiered test escalation.

Agents default to targeted tests (seconds) and only escalate to the full
suite (5 minutes) before pushing. The graph maps changed objects to
affected test modules, so the escalation is derived from the work record's
owned files, not guessed.

Tiers:
  0 = unit tests only (the changed module + direct dependencies) — seconds
  1 = subsystem integration (affected test groups) — tens of seconds
  2 = full funnel suite — ~5 minutes (parallel_test.ps1)
  3 = full suite + graphify + native — before publishing

Usage:
    python -m tools.science_funnel.test_escalation --files tools/science_funnel/coupled_scene.py
    # Returns: {"tier": 1, "modules": ["test_coupled_scene", "test_coupled_arm"], "commands": [...]}
"""
import argparse
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TESTS_DIR = os.path.join(ROOT, "tools", "science_funnel", "tests")

# Map file paths to test module groups (derived from the project's structure)
FILE_TO_TESTS = {
    # Engine
    "coupled_dynamics.hpp": ["test_coupled_scene", "test_coupled_arm"],
    "coupled_multidynamics.hpp": ["test_coupled_scene", "test_coupled_arm"],
    "free_root_dynamics.hpp": ["test_coupled_scene", "test_coupled_arm"],
    "gait_controller.hpp": ["test_coupled_scene"],
    "coupled_grasp.hpp": ["test_coupled_scene"],
    "coupled_articulation.hpp": ["test_coupled_arm"],
    "graph_earth.hpp": ["test_coupled_scene", "test_earth_scene"],

    # Scene
    "coupled_scene.py": ["test_coupled_scene"],
    "coupled_arm.py": ["test_coupled_arm", "test_coupled_scene"],
    "gait_scene.py": ["test_coupled_scene"],
    "macaque_scene.py": ["test_coupled_scene"],
    "coupled_free_scene.py": ["test_coupled_scene"],
    "earth_scene.py": ["test_earth_scene", "test_surface_scene"],
    "surface_scene.py": ["test_surface_scene"],
    "force_models.py": ["test_force_compiler"],
    "force_scene.py": ["test_force_compiler"],

    # Graph
    "project_program.json": ["test_batch", "test_class_contracts"],
    "creature_graph.json": ["test_batch", "test_class_contracts"],
    "class_contracts.json": ["test_class_contracts"],
    "store.py": ["test_class_contracts"],
    "build_graph.py": ["test_class_contracts", "test_project_spec"],
    "batch_qualify.py": ["test_batch"],
    "schema.py": ["test_class_contracts", "test_project_spec"],

    # Batch pipeline
    "batch/": ["test_batch", "test_batch_muscle", "test_batch_gait", "test_batch_geo"],
    "adapters": ["test_batch", "test_batch_muscle"],
    "pipeline.py": ["test_batch"],
    "graph.py": ["test_batch", "test_force_compiler"],

    # Surface geometry
    "surface_geometry.py": ["test_surface_geometry", "test_curve_integral"],
    "curve_integral.py": ["test_curve_integral"],
    "gpu_curve_integral.py": [],  # GPU tests (separate)
    "terrain.py": ["test_terrain", "test_coupled_scene"],
    "visual_proof.py": ["test_visual_proof", "test_visual_proof_wave2"],
    "visual_scene.py": ["test_visual_scene"],

    # Review
    "review_candidate.py": ["test_review_candidate"],
    "check_packet.py": ["test_packet_checker"],
    "gpu_oracle.py": [],  # GPU tests
    "compute_harness.py": [],  # meta-tool, no tests
    "parallel_test.ps1": [],  # meta-tool
    "graph_server.py": [],  # server, no tests
    "incremental_graph.py": [],  # meta-tool
}

# The full suite order (for tier 2+)
FULL_MODULES = sorted(
    f[:-3] for f in os.listdir(TESTS_DIR)
    if f.startswith("test_") and f.endswith(".py")
)


def determine_tier(changed_files):
    """Determine the appropriate test tier from the changed files.

    Returns (tier, test_modules, commands) where tier is:
      0 = minimal (only direct tests for changed files)
      1 = subsystem (direct + dependencies)
      2 = full suite (all test modules)
    """
    modules = set()

    for filepath in changed_files:
        basename = os.path.basename(filepath)
        rel = os.path.relpath(filepath, ROOT).replace("\\", "/")

        # Direct match
        if basename in FILE_TO_TESTS:
            modules.update(FILE_TO_TESTS[basename])

        # Directory match (e.g., "batch/connectors.py" matches "batch/")
        for pattern, tests in FILE_TO_TESTS.items():
            if "/" in pattern and pattern in rel:
                modules.update(tests)

        # If any test file itself changed, include it
        if basename.startswith("test_") and basename.endswith(".py"):
            modules.add(basename[:-3])

    # Remove empty modules and non-existent ones
    modules = {m for m in modules if os.path.exists(os.path.join(TESTS_DIR, m + ".py"))}

    if not modules:
        # Unknown files: conservative — full suite
        return 2, FULL_MODULES, [_full_command()]

    # Tier 0: direct tests only
    tier0_modules = sorted(modules)

    # Tier 1: add closely related modules
    tier1_modules = set(tier0_modules)
    for m in tier0_modules:
        if "coupled" in m:
            tier1_modules.update(m for m in FULL_MODULES if "coupled" in m)
        if "batch" in m:
            tier1_modules.update(m for m in FULL_MODULES if "batch" in m)
        if "surface" in m:
            tier1_modules.update(m for m in FULL_MODULES if "surface" in m)
        if "visual" in m:
            tier1_modules.update(m for m in FULL_MODULES if "visual" in m)
    tier1_modules = sorted(tier1_modules)

    # Build commands
    tier0_cmd = f"python -B -m unittest {' '.join(tier0_modules)} -v"
    tier1_cmd = f"python -B -m unittest {' '.join(tier1_modules)} -v"

    return 0, tier0_modules, [tier0_cmd, tier1_cmd]


def _full_command():
    return "powershell -File tools/parallel_test.ps1"


def escalation_plan(changed_files):
    """The full escalation plan for an agent.

    Returns a dict with the tier, modules, and commands at each escalation
    level. Agents run level 0 by default, level 1 after changes, level 2
    before pushing, level 3 before publishing.
    """
    tier, modules, commands = determine_tier(changed_files)

    return {
        "tier": tier,
        "tier0": {
            "description": "unit tests for changed files only",
            "modules": modules,
            "estimated_time": "seconds",
            "command": f"python -B -m unittest {' '.join(modules)} -v" if modules else "skip (no matching tests)",
        },
        "tier1": {
            "description": "subsystem integration (related modules)",
            "modules": sorted(set(
                m for m in FULL_MODULES
                for prefix in {m2.split("_")[0] for m2 in modules}
                if m.startswith(prefix)
            )),
            "estimated_time": "30-60 seconds",
            "command": "python -B -m unittest <related modules> -v",
        },
        "tier2": {
            "description": "full funnel suite (parallel)",
            "modules": FULL_MODULES,
            "estimated_time": "~5 minutes",
            "command": _full_command(),
        },
        "tier3": {
            "description": "full suite + graphify + native suite (pre-publish)",
            "modules": FULL_MODULES + ["graphify", "native"],
            "estimated_time": "~10 minutes",
            "command": "powershell -File tools/compute_harness.py test-python-full; graphify_consumer; native suite",
        },
        "rule": "Run tier 0 during development, tier 1 after changes stabilize, "
                "tier 2 before pushing, tier 3 before publishing. Never skip tier 3.",
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--files", nargs="+", required=True,
                    help="changed file paths (relative to repo root)")
    args = ap.parse_args()

    plan = escalation_plan(args.files)
    print(json.dumps(plan, indent=1))
