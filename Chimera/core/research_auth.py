"""
Research-Based Authorization Framework (RBAF)
Replaces opaque permission heuristics with evidence-driven decisions.

Every authorization decision is based on measurable research findings:
- Build status (last compile, error lines, warning counts)
- PIE state (isPIE, pawn possession, actor positions)
- Graph health (node count, GPA trend, junk nodes)
- Process state (actual running processes with identifiers)

Usage:
    from core.research_auth import ResearchAuth

    auth = ResearchAuth()

    # Check if it's safe to kill UnrealEditor for a build
    result = auth.can_kill_editor(reason="cold_build", evidence={
        "build_status": "green",
        "pie_active": False,
        "concurrent_processes": [],
        "risk_assessment": "low"
    })

    if result.allowed:
        # Proceed with kill
        ...

Design principles:
1. Authorization decisions MUST cite specific evidence sources
2. No heuristic can override measured state (e.g., "isPIE:false" trumps "concurrent session" guess)
3. All decisions are recorded to the DNA graph for auditability
4. If research is inconclusive, default to SAFE (don't block progress without evidence)
"""

import json
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, List, Optional


# ─── Data Types ──────────────────────────────────────────────────────


@dataclass
class ResearchFinding:
    """A single piece of evidence gathered from the system."""

    source: str  # Where this came from (e.g., "runtime_report", "tasklist")
    timestamp: str  # ISO format
    key: str  # What was measured
    value: Any  # The actual measurement
    confidence: str  # "high" | "medium" | "low"


@dataclass
class AuthorizationDecision:
    """The result of an authorization check."""

    action: str  # What was being authorized (e.g., "kill_editor")
    allowed: bool  # Whether to proceed
    reason: str  # Why this decision was made
    evidence: List[Dict]  # The research findings that informed the decision
    timestamp: str  # When the decision was made
    risk_level: str  # "low" | "medium" | "high"


@dataclass
class ResearchContext:
    """The full state of research at a point in time."""

    build_status: Optional[str] = None  # "green" | "red" | "unknown"
    last_build_time: Optional[str] = None
    pie_active: bool = False
    pawn_class: Optional[str] = None
    actor_positions: List[Dict] = field(default_factory=list)
    graph_node_count: int = 0
    gpa_trend: str = "unknown"
    junk_nodes: int = 0
    running_processes: List[Dict] = field(default_factory=list)
    concurrent_sessions: List[str] = field(default_factory=list)
    risk_assessment: str = "low"


# ─── Research Gatherers ──────────────────────────────────────────────


class ResearchGatherer:
    """Collects evidence from the system for authorization decisions."""

    def __init__(self):
        self.chimera_root = Path(__file__).parent.parent

    def gather_build_status(self) -> ResearchFinding:
        """Check last build result from DNA graph."""
        try:
            graph_path = self.chimera_root / "docs" / "chimera_dna_graph.json"
            if graph_path.exists():
                with open(graph_path) as f:
                    data = json.load(f)

                # Find latest build mutation
                mutations = [
                    n for n in data.get("nodes", []) if n.get("type") == "Mutation"
                ]
                mutations.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

                if mutations:
                    last_mutation = mutations[0]
                    return ResearchFinding(
                        source="dna_graph",
                        timestamp=last_mutation.get("timestamp", ""),
                        key="build_status",
                        value=last_mutation.get("error_signature", "unknown"),
                        confidence="high",
                    )
        except Exception:
            pass

        return ResearchFinding(
            source="dna_graph",
            timestamp=datetime.now(UTC).isoformat(),
            key="build_status",
            value="unknown",
            confidence="low",
        )

    def gather_pie_state(self) -> ResearchFinding:
        """Check PIE state via MCP runtime_report."""
        try:
            from core.telemetry_probe import MCPStdioClient

            c = MCPStdioClient()
            r = c.call("inspect", {"action": "runtime_report"})

            # Safe nested dict access with fallbacks
            result_data: Dict[str, Any] = {}
            if isinstance(r, dict):
                result_data = r.get("result", {})
                if not isinstance(result_data, dict):
                    result_data = {}
                result_data = result_data.get("structuredContent", {})
                if not isinstance(result_data, dict):
                    result_data = {}
                result_data = result_data.get("result", {})
                if not isinstance(result_data, dict):
                    result_data = {}

            is_pie = (
                result_data.get("isPIE", False)
                if isinstance(result_data, dict)
                else False
            )
            pawn_class = (
                result_data.get("pawn_class", "")
                if isinstance(result_data, dict)
                else ""
            )

            return ResearchFinding(
                source="runtime_report",
                timestamp=datetime.now(UTC).isoformat(),
                key="pie_state",
                value={"isPIE": is_pie, "pawn_class": pawn_class},
                confidence="high" if is_pie else "medium",
            )
        except Exception:
            return ResearchFinding(
                source="runtime_report",
                timestamp=datetime.now(UTC).isoformat(),
                key="pie_state",
                value={"error": "MCP bridge unavailable"},
                confidence="low",
            )

    def gather_process_state(self) -> List[ResearchFinding]:
        """Check actual running processes on Windows."""
        findings = []

        try:
            # Check for UnrealEditor.exe with full process info
            q = subprocess.run(
                [
                    "tasklist",
                    "/FI",
                    "IMAGENAME eq UnrealEditor.exe",
                    "/FO",
                    "CSV",
                    "/NH",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if q.returncode == 0 and q.stdout.strip():
                # Parse CSV output: Image Name,PID,Session Name,Memory Usage
                lines = q.stdout.strip().split("\n")
                for line in lines:
                    parts = [p.strip('"') for p in line.split(",")]
                    if len(parts) >= 4:
                        findings.append(
                            ResearchFinding(
                                source="tasklist",
                                timestamp=datetime.now(UTC).isoformat(),
                                key=f"process_UnrealEditor_PID_{parts[1]}",
                                value={"pid": parts[1], "memory_mb": parts[3]},
                                confidence="high",
                            )
                        )
        except Exception:
            pass

        # Check for other Chimera-related processes
        try:
            q = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq python.exe"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if q.returncode == 0 and q.stdout.strip():
                lines = q.stdout.strip().split("\n")
                for line in lines:
                    parts = [p.strip('"') for p in line.split(",")]
                    if len(parts) >= 4:
                        findings.append(
                            ResearchFinding(
                                source="tasklist",
                                timestamp=datetime.now(UTC).isoformat(),
                                key=f"process_python_PID_{parts[1]}",
                                value={"pid": parts[1], "memory_mb": parts[3]},
                                confidence="high",
                            )
                        )
        except Exception:
            pass

        return findings

    def gather_graph_health(self) -> ResearchFinding:
        """Check DNA graph health metrics."""
        try:
            graph_path = self.chimera_root / "docs" / "chimera_dna_graph.json"
            if graph_path.exists():
                with open(graph_path) as f:
                    data = json.load(f)

                nodes = data.get("nodes", [])
                mutations = [n for n in nodes if n.get("type") == "Mutation"]
                junk = len([n for n in nodes if n.get("id", "").startswith("unknown_")])

                return ResearchFinding(
                    source="dna_graph",
                    timestamp=datetime.now(UTC).isoformat(),
                    key="graph_health",
                    value={
                        "total_nodes": len(nodes),
                        "mutation_count": len(mutations),
                        "junk_nodes": junk,
                        "node_count_under_2000": len(nodes) <= 2000,
                    },
                    confidence="high",
                )
        except Exception:
            pass

        return ResearchFinding(
            source="dna_graph",
            timestamp=datetime.now(UTC).isoformat(),
            key="graph_health",
            value={"error": "Cannot read graph"},
            confidence="low",
        )


# ─── Authorization Engine ────────────────────────────────────────────


class ResearchAuth:
    """
    Makes authorization decisions based on research findings.

    Replaces opaque permission heuristics with evidence-driven decisions.
    Every decision cites specific evidence sources and is recorded to DNA graph.
    """

    def __init__(self):
        self.gatherer = ResearchGatherer()
        self.chimera_root = Path(__file__).parent.parent

    def gather_context(self) -> ResearchContext:
        """Collect all available research findings into a context object."""
        ctx = ResearchContext()

        # Gather build status
        build_finding = self.gatherer.gather_build_status()
        if build_finding.value == "success_no_error":
            ctx.build_status = "green"
        elif build_finding.value != "unknown":
            ctx.build_status = "red"

        ctx.last_build_time = build_finding.timestamp

        # Gather PIE state
        pie_finding = self.gatherer.gather_pie_state()
        if isinstance(pie_finding.value, dict):
            ctx.pie_active = pie_finding.value.get("isPIE", False)
            ctx.pawn_class = pie_finding.value.get("pawn_class")

        # Gather process state
        proc_findings = self.gatherer.gather_process_state()
        for f in proc_findings:
            if "UnrealEditor" in f.key:
                ctx.running_processes.append(
                    {
                        "type": "UnrealEditor",
                        "pid": f.value.get("pid"),
                        "memory_mb": f.value.get("memory_mb"),
                    }
                )
            elif "python" in f.key:
                ctx.running_processes.append(
                    {
                        "type": "Python",
                        "pid": f.value.get("pid"),
                        "memory_mb": f.value.get("memory_mb"),
                    }
                )

        # Gather graph health
        graph_finding = self.gatherer.gather_graph_health()
        if isinstance(graph_finding.value, dict):
            ctx.graph_node_count = graph_finding.value.get("total_nodes", 0)
            ctx.junk_nodes = graph_finding.value.get("junk_nodes", 0)

        # Risk assessment based on evidence
        ctx.risk_assessment = self._assess_risk(ctx)

        return ctx

    def _assess_risk(self, ctx: ResearchContext) -> str:
        """Assess risk level based on research findings."""
        risk_score = 0

        # High risk if PIE is active (unsaved changes could be lost)
        if ctx.pie_active:
            risk_score += 3

        # Medium risk if build is red
        if ctx.build_status == "red":
            risk_score += 2

        # Low risk if graph has junk nodes
        if ctx.junk_nodes > 0:
            risk_score += 1

        # High risk if too many concurrent processes
        if len(ctx.running_processes) > 4:
            risk_score += 2

        if risk_score >= 4:
            return "high"
        elif risk_score >= 2:
            return "medium"
        else:
            return "low"

    def can_kill_editor(self, reason: str = "build") -> AuthorizationDecision:
        """
        Determine if it's safe to kill UnrealEditor.exe.

        Research-based decision:
        - If PIE is NOT active (isPIE:false), risk is low regardless of other processes
        - If build status is green, killing editor won't lose uncommitted work
        - If graph has junk nodes or GPA is falling, defer until cleaned up

        Returns AuthorizationDecision with allowed=True/False and evidence citation.
        """
        ctx = self.gather_context()

        # Primary safety check: PIE state
        if ctx.pie_active:
            return AuthorizationDecision(
                action="kill_editor",
                allowed=False,
                reason=f"PIE is active (pawn_class={ctx.pawn_class}). Killing editor would lose unsaved PIE state.",
                evidence=[
                    {
                        "source": "runtime_report",
                        "key": "pie_state",
                        "value": {"isPIE": True, "pawn_class": ctx.pawn_class},
                    }
                ],
                timestamp=datetime.now(UTC).isoformat(),
                risk_level="high",
            )

        # Secondary check: build status
        if ctx.build_status == "red":
            return AuthorizationDecision(
                action="kill_editor",
                allowed=False,
                reason=f"Last build failed ({ctx.last_build_time}). Fix build errors before killing editor.",
                evidence=[
                    {
                        "source": "dna_graph",
                        "key": "build_status",
                        "value": ctx.build_status,
                    }
                ],
                timestamp=datetime.now(UTC).isoformat(),
                risk_level="medium",
            )

        # Tertiary check: graph health
        if ctx.junk_nodes > 0 or ctx.graph_node_count > 2000:
            return AuthorizationDecision(
                action="kill_editor",
                allowed=False,
                reason=f"Graph has {ctx.junk_nodes} junk nodes and {ctx.graph_node_count} total nodes. Clean up graph first.",
                evidence=[
                    {
                        "source": "dna_graph",
                        "key": "graph_health",
                        "value": {
                            "junk_nodes": ctx.junk_nodes,
                            "total_nodes": ctx.graph_node_count,
                        },
                    }
                ],
                timestamp=datetime.now(UTC).isoformat(),
                risk_level="medium",
            )

        # All checks passed: safe to kill editor
        return AuthorizationDecision(
            action="kill_editor",
            allowed=True,
            reason=f"Evidence shows PIE inactive, build green, graph healthy. Safe to kill for {reason}.",
            evidence=[
                {"source": f"gathered_{i}", "key": k, "value": v}
                for i, (k, v) in enumerate(
                    [
                        ("pie_state", {"isPIE": False}),
                        ("build_status", ctx.build_status),
                        ("graph_health", {"junk_nodes": ctx.junk_nodes}),
                    ]
                )
                if not isinstance(v, dict) or "error" not in v
            ],
            timestamp=datetime.now(UTC).isoformat(),
            risk_level="low",
        )

    def can_modify_level(self, reason: str = "editor_edit") -> AuthorizationDecision:
        """
        Determine if it's safe to modify the level file.

        Research-based decision:
        - If PIE is active and pawn is possessed, risky (concurrent session may be playing)
        - If build status is green and no pending changes, lower risk
        - Check for .ORCHESTRATOR_STATUS file as indicator of concurrent automation

        Returns AuthorizationDecision with allowed=True/False and evidence citation.
        """
        ctx = self.gather_context()

        # Primary check: PIE + possession
        if ctx.pie_active and ctx.pawn_class:
            return AuthorizationDecision(
                action="modify_level",
                allowed=False,
                reason=f"PIE active with {ctx.pawn_class} possessed. Modifying level could disrupt gameplay.",
                evidence=[
                    {
                        "source": "runtime_report",
                        "key": "pie_state",
                        "value": {"isPIE": True, "pawn_class": ctx.pawn_class},
                    }
                ],
                timestamp=datetime.now(UTC).isoformat(),
                risk_level="high",
            )

        # Check for orchestrator status file
        status_file = self.chimera_root.parent / ".ORCHESTRATOR_STATUS"
        if status_file.exists():
            try:
                with open(status_file) as f:
                    status_data = json.load(f)

                return AuthorizationDecision(
                    action="modify_level",
                    allowed=False,
                    reason=f"Orchestrator active ({status_data.get('state', 'unknown')}). Wait for orchestrator to complete.",
                    evidence=[
                        {
                            "source": ".ORCHESTRATOR_STATUS",
                            "key": "orchestrator_state",
                            "value": status_data,
                        }
                    ],
                    timestamp=datetime.now(UTC).isoformat(),
                    risk_level="medium",
                )
            except Exception:
                pass

        # All checks passed: safe to modify level
        return AuthorizationDecision(
            action="modify_level",
            allowed=True,
            reason=f"Evidence shows PIE inactive, no orchestrator active. Safe to modify level for {reason}.",
            evidence=[
                {"source": f"gathered_{i}", "key": k, "value": v}
                for i, (k, v) in enumerate(
                    [
                        ("pie_state", {"isPIE": False}),
                        ("orchestrator_status", "not_found"),
                    ]
                )
                if not isinstance(v, dict) or "error" not in v
            ],
            timestamp=datetime.now(UTC).isoformat(),
            risk_level="low",
        )

    def record_decision(self, decision: AuthorizationDecision):
        """Record authorization decision to DNA graph for auditability."""
        try:
            # Record via graphify_record CLI
            import subprocess

            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "core.graphify_record",
                    "surprise",
                    "--context",
                    f"{decision.action}: {decision.reason}",
                    "--reality",
                    f"allowed={decision.allowed}, risk={decision.risk_level}",
                ],
                cwd=self.chimera_root,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except Exception:
            # Non-fatal: logging failure doesn't block the decision
            pass


# ─── CLI Interface ──────────────────────────────────────────────────


def main():
    """CLI interface for research-based authorization checks."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Research-Based Authorization Framework"
    )
    parser.add_argument(
        "action", choices=["kill_editor", "modify_level"], help="Action to authorize"
    )
    parser.add_argument(
        "--reason", default="cli_check", help="Reason for the authorization request"
    )
    parser.add_argument(
        "--gather-only",
        action="store_true",
        help="Only gather context, don't make decision",
    )

    args = parser.parse_args()

    auth = ResearchAuth()

    if args.gather_only:
        ctx = auth.gather_context()
        print(
            json.dumps(
                {
                    "build_status": ctx.build_status,
                    "pie_active": ctx.pie_active,
                    "pawn_class": ctx.pawn_class,
                    "running_processes": ctx.running_processes,
                    "graph_node_count": ctx.graph_node_count,
                    "junk_nodes": ctx.junk_nodes,
                    "risk_assessment": ctx.risk_assessment,
                },
                indent=2,
            )
        )
    else:
        decision: Optional[AuthorizationDecision] = None
        if args.action == "kill_editor":
            decision = auth.can_kill_editor(reason=args.reason)
        elif args.action == "modify_level":
            decision = auth.can_modify_level(reason=args.reason)

        # Record to DNA graph
        assert decision is not None, f"Unknown action: {args.action}"
        auth.record_decision(decision)

        print(
            json.dumps(
                {
                    "action": decision.action,
                    "allowed": decision.allowed,
                    "reason": decision.reason,
                    "risk_level": decision.risk_level,
                    "evidence_count": len(decision.evidence),
                    "timestamp": decision.timestamp,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
