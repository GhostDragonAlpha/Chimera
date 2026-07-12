"""
Mandatory Hard Gates — the Self-Sculpting Loop's alignment enforcement.

Every gate is a function that returns True (pass) or raises GateViolation (fail).
Gates are composable into chains. If ANY gate in a chain fails, the entire
pipeline stage is blocked and the violation is recorded to the DNA graph.

The fundamental rule: soft warnings produce soft compliance. Hard gates produce
alignment. No pipeline stage proceeds past a red gate — ever.
"""

import os
import sys
from pathlib import Path
from typing import Callable, List, Optional

# Ensure core/ is on sys.path for graphify_interface imports
_core_dir = Path(__file__).parent
if str(_core_dir) not in sys.path:
    sys.path.insert(0, str(_core_dir))


class GateViolation(Exception):
    """Raised when a mandatory gate check fails.

    The pipeline MUST NOT catch this silently. It propagates upward,
    terminates the current stage, and prevents downstream stages.
    """
    def __init__(self, gate_name: str, reason: str, severity: str = "blocker",
                 remediation: str = ""):
        self.gate_name = gate_name
        self.reason = reason
        self.severity = severity
        self.remediation = remediation
        super().__init__(f"[GATE FAIL] {gate_name}: {reason}")

    def short_str(self) -> str:
        return f"[{self.severity.upper()}] {self.gate_name} — {self.reason}"


class GateChain:
    """A chain of gates that must ALL pass before proceeding.

    Usage:
        gates = GateChain("Pre-Build", [
            gate_no_junk_nodes,
            gate_gpa_not_critically_falling,
        ])
        gates.check()  # raises GateViolation on first failure
    """

    def __init__(self, name: str, gates: List[Callable[[], bool]]):
        self.name = name
        self.gates = gates

    def check(self) -> bool:
        """Execute all gates in order. Returns True if all pass.
        Raises GateViolation on the FIRST failure — no silent continuation."""
        failed_gates = []
        for gate_fn in self.gates:
            gate_name = gate_fn.__name__ if hasattr(gate_fn, '__name__') else str(gate_fn)
            try:
                result = gate_fn()
                if result is False:
                    raise GateViolation(gate_name, f"Gate returned False", "blocker")
            except GateViolation:
                raise  # re-raise — these are the hard failures we propagate
            except Exception as e:
                raise GateViolation(gate_name, f"Gate raised: {e}", "error")
        return True


# ---------------------------------------------------------------------------
# Graph health gates
# ---------------------------------------------------------------------------

def gate_no_junk_nodes() -> bool:
    """Hard fail if any unknown_* junk nodes remain in the graph.
    The fix script must be run first — it's mandatory, not optional."""
    from graphify_interface import load_dna_graph
    dna = load_dna_graph()
    nodes = dna.get("nodes", [])
    junk = [n for n in nodes
            if n.get("feature_name") == "unknown_feature"
            or (n.get("tool") == "unknown_tool" and n.get("action") == "unknown_action")]
    if junk:
        raise GateViolation(
            "gate_no_junk_nodes",
            f"{len(junk)} junk nodes found in graph. Run fix_dna_key_mismatch_pollution.py first.",
            "blocker",
            "python fix_dna_key_mismatch_pollution.py"
        )
    return True


def gate_gpa_not_critically_falling() -> bool:
    """Hard fail if the cumulative project GPA is below 1.0 (D average).

    Uses the ProfessorGPA cumulative node (scope=project_overall) rather than
    raw recent grades, because auto-graded F/C from test-bench runs (e.g.,
    deliberate gate testing without UE) would otherwise block production work.

    If no cumulative node exists yet, falls back to the last 10 unique grades
    with deduplication to handle auto-fixer retries that record duplicate Fs."""
    from graphify_interface import load_dna_graph
    dna = load_dna_graph()
    nodes = dna.get("nodes", [])

    # Prefer the cumulative GPA node
    overall = [n for n in nodes if n.get("type") == "ProfessorGPA"
               and n.get("scope") == "project_overall"]
    if overall:
        latest = sorted(overall, key=lambda n: n.get("timestamp", ""), reverse=True)[0]
        gpa = latest.get("gpa")
        if gpa is not None and gpa < 1.0:
            raise GateViolation(
                "gate_gpa_not_critically_falling",
                f"Cumulative GPA is {gpa:.1f} (below 1.0 threshold). "
                f"Systemic issues must be resolved.",
                "blocker",
                "Review recent build failures and visual verification results."
            )
        return True  # cumulative GPA >= 1.0 — fine

    # Fallback: deduplicate grades by (feature, grade, timestamp truncated to minute)
    grade_map = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}
    all_grades = [n for n in nodes if n.get("type") == "ProfessorGrade"
                  and n.get("grade") in grade_map]
    seen = set()
    unique = []
    for g in sorted(all_grades, key=lambda n: n.get("timestamp", ""), reverse=True):
        key = (g.get("feature", ""), g.get("grade", ""),
               str(g.get("timestamp", ""))[:16])  # minute-granularity dedup
        if key not in seen:
            seen.add(key)
            unique.append(g)

    if len(unique) < 3:
        return True  # not enough unique data

    recent = unique[:10]
    scores = [grade_map[g["grade"]] for g in recent if g.get("grade") in grade_map]
    avg = sum(scores) / len(scores) if scores else 4.0

    if avg < 1.0:
        raise GateViolation(
            "gate_gpa_not_critically_falling",
            f"GPA critically low: {avg:.1f} over last {len(scores)} unique grades. "
            f"Systemic issues must be resolved.",
            "blocker",
            "Review recent build failures and visual verification results."
        )
    return True


def gate_provenance_complete() -> bool:
    """Hard fail if any node in the graph lacks provenance (recorded_by).
    Every node must be traceable to its origin."""
    from graphify_interface import load_dna_graph
    dna = load_dna_graph()
    nodes = dna.get("nodes", [])
    no_prov = [n for n in nodes if not n.get("recorded_by")]
    if no_prov:
        raise GateViolation(
            "gate_provenance_complete",
            f"{len(no_prov)} nodes lack provenance. Load the graph through save_dna_graph "
            f"to stamp legacy_provenance on all unmarked nodes.",
            "blocker"
        )
    return True


def gate_node_count_bounded() -> bool:
    """Runaway-growth sanity ceiling. The old 2000 cap existed because the DNA
    graph was a flat JSON file loaded/rewritten whole on every op — a real
    performance cliff. With the SQLite substrate (core.world_store, indexed +
    FTS) there is no whole-file bottleneck, so this is now just a very high
    backstop against an unbounded-loop bug, not an archival trigger."""
    import os as _os
    from graphify_interface import load_dna_graph
    ceiling = int(_os.environ.get("CHIMERA_MAX_NODES", 5_000_000))
    dna = load_dna_graph()
    nodes = dna.get("nodes", [])
    if len(nodes) > ceiling:
        raise GateViolation(
            "gate_node_count_bounded",
            f"Graph has {len(nodes):,} nodes (ceiling {ceiling:,}) — likely a "
            f"runaway loop, not legitimate growth.",
            "warning",
            "Investigate the writer that exploded the node count; the substrate "
            "itself scales, so the fix is the bug, not archival."
        )
    return True


def gate_lm_available() -> bool:
    """Check that LM Studio is reachable with the mandatory model loaded.

    The mandatory model (qwen3.6-35b-a3b-mtp@iq2_m) is text-only — this gate
    verifies LM Studio is online and responsive, not that vision is available.
    Visual verification uses text-based game state analysis instead of pixel analysis.
    """
    try:
        from visual_verifier import _check_lm_model
        ok, msg = _check_lm_model()
        if not ok:
            raise GateViolation(
                "gate_lm_available",
                f"LM Studio not ready: {msg}",
                "blocker",
                "Ensure LM Studio is running with qwen3.6-35b-a3b-mtp@iq2_m loaded."
            )
        return True
    except GateViolation:
        raise
    except Exception as e:
        raise GateViolation(
            "gate_lm_available",
            f"Cannot reach LM Studio: {e}",
            "warning"
        )


def gate_lm_studio_online() -> bool:
    """Hard fail if LM Studio is required but not reachable."""
    try:
        import urllib.request
        resp = urllib.request.urlopen("http://localhost:1234/v1/models", timeout=3)
        return resp.status == 200
    except Exception:
        raise GateViolation(
            "gate_lm_studio_online",
            "LM Studio is not reachable on localhost:1234. "
            "Required for professor review and visual analysis.",
            "blocker",
            "Start LM Studio and load a model (lms load ...)"
        )


def gate_unreal_editor_running() -> bool:
    """Hard fail if Unreal Editor is not running and we need it."""
    try:
        import subprocess
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq UnrealEditor.exe"],
            capture_output=True, text=True, timeout=5,
        ).stdout
        if "UnrealEditor.exe" not in out:
            raise GateViolation(
                "gate_unreal_editor_running",
                "Unreal Editor is not running. Required for playtests and screenshot capture.",
                "blocker",
                "Launch the UE Editor project before running the pipeline."
            )
        return True
    except GateViolation:
        raise
    except Exception as e:
        raise GateViolation(
            "gate_unreal_editor_running",
            f"Cannot check UE process: {e}",
            "warning"
        )


# ---------------------------------------------------------------------------
# Build gates
# ---------------------------------------------------------------------------

def gate_build_succeeded(build_result: dict) -> bool:
    """Hard fail if build did not succeed."""
    if not build_result.get("success"):
        error = build_result.get("error", "unknown error")
        raise GateViolation(
            "gate_build_succeeded",
            f"Build failed: {error}",
            "blocker",
            "Review UBT output in the graph (ubt_output_excerpt field). "
            "Fix compilation errors and re-run."
        )
    return True


def gate_auto_fixer_attempted(build_result: dict) -> bool:
    """Warn if build failed and auto-fixer didn't run."""
    if not build_result.get("success"):
        if not build_result.get("auto_fixer_ran"):
            raise GateViolation(
                "gate_auto_fixer_attempted",
                "Build failed but auto-fixer was not attempted.",
                "warning",
                "Enable auto_fix_brace_error before re-running build."
            )
    return True


def gate_no_stale_trees() -> bool:
    """Hard fail if stale module trees exist under Source/. Draconian
    because stale trees shadow canonical files and cause silent bugs."""
    source_root = Path("E:/PythonChimera/Chimera/Source")
    allowed = {"Chimera", "Chimera.Target.cs", "ChimeraEditor.Target.cs"}
    if source_root.exists():
        stale = sorted(p.name for p in source_root.iterdir() if p.name not in allowed)
        if stale:
            raise GateViolation(
                "gate_no_stale_trees",
                f"Stale module trees under Source/: {stale}. "
                f"Clean them with: git rm -r Chimera/Source/{stale[0]} && "
                f"rm -rf Chimera/Source/{stale[0]}",
                "blocker"
            )
    return True


# ---------------------------------------------------------------------------
# Inter-stage gates
# ---------------------------------------------------------------------------

def gate_playtest_no_failures(playtest_report) -> bool:
    """Hard fail if playtest had actual test failures (not skips)."""
    if playtest_report is None:
        return True
    failed = playtest_report.summary.get("failed", 0)
    if failed > 0:
        raise GateViolation(
            "gate_playtest_no_failures",
            f"{failed} playtest(s) failed. Fix before proceeding to visual verification.",
            "blocker",
            "Review test suggestions in the playtest report."
        )
    return True


# ---------------------------------------------------------------------------
# Post-flight gates
# ---------------------------------------------------------------------------

def gate_git_clean() -> bool:
    """Warn if working tree has uncommitted changes
    (not a blocker — changes are expected during development)."""
    try:
        import subprocess
        out = subprocess.run(
            ["git", "-C", "E:/PythonChimera", "status", "--short"],
            capture_output=True, text=True, timeout=5,
        ).stdout
        lines = [l for l in out.splitlines() if l.strip()]
        if lines:
            print(f"  [GATE] {len(lines)} uncommitted change(s) — review before commit")
            return True
        return True
    except Exception:
        return True


# ============================================================================
# Convenience: pre-built gate chains
# ============================================================================

PRE_FLIGHT_GATES = GateChain("Pre-Flight", [
    gate_no_junk_nodes,
    gate_gpa_not_critically_falling,
    gate_node_count_bounded,
    gate_no_stale_trees,
])

BUILD_GATES = GateChain("Build", [
    gate_no_stale_trees,
    gate_build_succeeded,
    gate_auto_fixer_attempted,
])

POST_FLIGHT_GATES = GateChain("Post-Flight", [
    gate_git_clean,
    gate_node_count_bounded,
])
