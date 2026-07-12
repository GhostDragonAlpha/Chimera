"""Heuristic Distiller — the Generation Protocol's autopsy step (WS2).

Deterministically clusters the DNA graph's accumulated failures and surprises,
suppresses lessons already covered by the constitution, checks new candidates
for conflicts with existing heuristics, and stages the survivors in
docs/PENDING_HEURISTICS.md for the human Gardener to approve or veto.

NEVER auto-applies anything. Zero model dependency: clustering is exact-match
and keyword-based; the one-sentence draft rule is written by the driving agent
from the staged evidence, then the human approves before promotion via
`python -m core.graphify_record heuristic ...`.

Usage:
    python -m core.heuristic_distiller [--min-cluster 3] [--max-candidates N]
                                       [--dry-run]
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from core.graphify_interface import load_dna_graph
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from graphify_interface import load_dna_graph

CHIMERA_ROOT = Path(__file__).parent.parent
PENDING_PATH = CHIMERA_ROOT / "docs" / "PENDING_HEURISTICS.md"
# Constitution organs searched for existing coverage of a lesson:
COVERAGE_SOURCES = [
    CHIMERA_ROOT / "docs" / "PENDING_HEURISTICS.md",
    CHIMERA_ROOT / "docs" / "MCP_PATHWAYS.md",
    CHIMERA_ROOT / "core" / "gates.py",
    CHIMERA_ROOT / "CLAUDE.md",
]

SUCCESS_SIGNATURES = {"success_no_error", "", "none", "n/a"}
STOPWORDS = {"the", "a", "an", "to", "of", "in", "on", "for", "and", "or", "not",
             "is", "are", "was", "be", "with", "via", "when", "must", "never",
             "always", "use", "before", "after", "attempt", "failed", "fail"}


def _tokens(text: str) -> set:
    return {t for t in re.findall(r"[a-z0-9_]{3,}", str(text).lower())} - STOPWORDS


def _is_failure_node(n: dict) -> bool:
    sig = str(n.get("error_signature", ""))
    if sig in SUCCESS_SIGNATURES or sig.startswith("surprise_"):
        return False
    # loop/apply progress markers with a passing result are not failures
    if n.get("compilation_result") == "pass" and "complete" in sig:
        return False
    return True


def _normalize_signature(sig: str) -> str:
    """Collapse per-feature noise into signature families so repeats cluster."""
    sig = re.sub(r"ralph_apply_[A-Za-z0-9_]+_step\d+", "ralph_apply_<feature>_step", sig)
    sig = re.sub(r"ralph_research_failed_[A-Za-z0-9_]+", "ralph_research_failed_<feature>", sig)
    return sig


def _is_pathway_success(result) -> bool:
    """Success-family pathway results are not failures. H-10 (promoted
    2026-07-07) had intended UE shutdowns recorded as success with a note —
    they landed as 'success_intended_kill'/'success_unverified' etc., which the
    old exact-match filter kept clustering as failures forever (18x noise
    cluster observed 2026-07-11)."""
    return result is None or str(result).lower().startswith("success")


def collect_clusters(nodes: list, min_cluster: int) -> list:
    """Returns cluster dicts: {signature, kind, count, evidence, samples, last_seen}."""
    clusters = {}

    def add(key: str, kind: str, node: dict, sample: str):
        c = clusters.setdefault(key, {"signature": key, "kind": kind, "count": 0,
                                      "evidence": [], "samples": [], "last_seen": ""})
        c["count"] += 1
        if len(c["evidence"]) < 8:
            c["evidence"].append(node.get("id", "?"))
        if sample and len(c["samples"]) < 3 and sample not in c["samples"]:
            c["samples"].append(sample[:160])
        c["last_seen"] = max(c["last_seen"], str(node.get("timestamp", "")))

    for n in nodes:
        ntype = n.get("type", "")
        if ntype == "Observation" and n.get("verdict") == "rejected":
            # the human's collapse said no — the highest-grade dream fodder there is
            add(f"human_rejection: {n.get('feature_name','?')}", "human_rejection", n,
                str(n.get("notes", ""))[:160])
        elif ntype == "SimPlaytest" and n.get("error_signature") == "sim_beats_failed":
            # the sleepwalker found a gap — ranked below the human's voice, above machines
            for o in n.get("outcomes", []):
                if o.get("outcome") != "reached":
                    add(f"sim_rejection: {n.get('demo','?')}/{o.get('beat','?')}",
                        "sim_rejection", n,
                        f"{o.get('outcome')}: {json.dumps(o.get('evidence', [])[-1:])[:120]}")
        elif ntype == "SurpriseMoment" and not n.get("consolidated"):
            # cluster surprises by their strongest shared tokens (context+reality)
            key = "surprise: " + " ".join(sorted(_tokens(
                f"{n.get('context','')} {n.get('lesson_hint','')}"))[:4])
            add(key, "surprise", n,
                f"expected '{n.get('expectation','')[:60]}' but '{n.get('reality','')[:60]}'")
        elif ntype == "pathway_attempt" and n.get("result") not in ("success", None):
            add(f"pathway: {n.get('tool','?')}.{n.get('action','?')} -> {n.get('result','?')}",
                "pathway", n, str(n.get("error_message") or n.get("fix_description", ""))[:160])
        elif ntype == "ProfessorGrade" and str(n.get("grade", "")).upper() in ("C", "F"):
            add(f"grade_CF: {n.get('feature', n.get('feature_name', '?'))}",
                "grade", n, str(n.get("reasoning", ""))[:160])
        elif _is_failure_node(n):
            add(_normalize_signature(str(n.get("error_signature"))), "failure", n,
                str(n.get("fix_description", ""))[:160])

    # human rejections stage at ANY count (min_cluster does not gate the human's voice)
    # and sort ahead of every machine-detected cluster
    out = [c for c in clusters.values()
           if c["count"] >= min_cluster or c["kind"] == "human_rejection"]
    out.sort(key=lambda c: (0 if c["kind"] == "human_rejection"
                            else (1 if c["kind"] == "sim_rejection" else 2),
                            -c["count"], c["last_seen"]))
    return out


def coverage_check(signature: str) -> str:
    """Returns the covering source name if the lesson already lives in the
    constitution, else ''. Match: signature (or its distinctive tokens) appears
    in a coverage source."""
    sig_tokens = _tokens(signature)
    needle = signature.split(":")[-1].strip().lower()
    for src in COVERAGE_SOURCES:
        if not src.exists():
            continue
        text = src.read_text(encoding="utf-8", errors="replace").lower()
        if needle and len(needle) > 8 and needle in text:
            return src.name
        # token coverage: >=3 distinctive tokens present in one source
        if sig_tokens and len(sig_tokens) >= 3:
            hits = sum(1 for t in sig_tokens if t in text)
            if hits >= max(3, int(len(sig_tokens) * 0.8)):
                return src.name
    return ""


def conflict_check(signature: str, nodes: list, pending_text: str) -> list:
    """Flag existing approved Heuristic nodes / pending entries whose topic
    overlaps this candidate (>=2 shared significant tokens). Human reconciles."""
    sig_tokens = _tokens(signature)
    conflicts = []
    for n in nodes:
        if n.get("type") != "Heuristic":
            continue
        overlap = sig_tokens & _tokens(f"{n.get('signature','')} {n.get('rule','')}")
        if len(overlap) >= 2:
            conflicts.append(f"{n.get('id')} ({n.get('rule','')[:60]})")
    for m in re.finditer(r"^## (H-\d+): (.+)$", pending_text, re.MULTILINE):
        if len(sig_tokens & _tokens(m.group(2))) >= 2 and m.group(2).strip() != signature:
            conflicts.append(m.group(1))
    return conflicts


def synthesize_draft_rule(signature: str, kind: str, samples: list) -> str:
    """Generate an initial actionable draft rule from evidence patterns.

    Deterministic synthesis (no LM): extract failure keywords, propose a fix or
    observation strategy. Returns rule <=25 words, or fallback placeholder if synthesis fails.
    """
    if not samples:
        return "(agent: write ONE sentence from the evidence, <=25 words)"

    # Concatenate all samples for pattern matching
    evidence_text = " ".join(samples).lower()

    # Pattern families for different failure types (ordered by specificity).
    # More specific patterns first; if multiple match, first wins.
    patterns = [
        # Specific missing-item failures
        (r"(atool_shovel|missing.*\btool\b)", "Implement missing tool actor and verify scene spawning."),
        (r"(no|missing).*\b(input|key|binding)\b", "Implement missing input bindings and verify actor registration."),
        (r"(sanddrift|sandrift_fx|missing.*\beffect\b)", "Verify environmental effects spawn and render correctly."),
        (r"(no|missing).*\b(component|actor|asset)\b", "Verify required components and assets are spawned and registered."),
        # Log/output failures (usually indicate silent path)
        (r"(\blog_contains\b|\bdemobeat\b.*false|log.*false|log_hit)", "Verify event logging and signal traces on success path."),
        # Screenshot/state-capture failures (beat schema gap)
        (r"(screenshot|screenshot_taken|screenshot_.*unknown)", "Implement screenshot action and state-capture in sleepwalker beat registry."),
        # Pawn class/rig failures (character setup gap)
        (r"(defaultpawn|pawn_class|incorrect.*pawn)", "Verify correct pawn class and rig bindings on initialization."),
        # Movement/distance failures (navigation gap)
        (r"(\bdist\s*=|\bpawn_within\b|distance.*\d+|too.*far)", "Verify beat spawn location distances and pawn navigation constraints."),
        # Generic log expectation failures
        (r"(\bexpect\b.*log|\blog\b|\bprint\b)", "Verify event logging and signal traces on success path."),
    ]

    # Test each pattern in order; first match wins
    for regex, rule_template in patterns:
        if re.search(regex, evidence_text):
            # Trim to exactly 25 words max
            words = rule_template.split()[:25]
            return " ".join(words) + ("." if not words[-1].endswith(".") else "")

    # Fallback: try to extract prominent keywords and build a generic rule
    sig_tokens = sorted(_tokens(signature))
    if sig_tokens:
        key_sig = " ".join(sig_tokens[:2])  # first 2 significant tokens from signature
        return f"Investigate {key_sig}; verify test harness and beat registration."[:80]

    # Last resort: placeholder
    return "(agent: write ONE sentence from the evidence, <=25 words)"


def propose_organ(signature: str) -> str:
    s = signature.lower()
    if any(k in s for k in ("pathway:", "mcp", "viewport", "screenshot", "window", "camera")):
        return "mcp_pathways"
    if any(k in s for k in ("compilation", "build", "junk", "gpa", "graph", "node")):
        return "gate"
    return "claude_md"


def next_h_number(pending_text: str) -> int:
    nums = [int(m.group(1)) for m in re.finditer(r"^## H-(\d+):", pending_text, re.MULTILINE)]
    return (max(nums) + 1) if nums else 1


def render_entry(num: int, c: dict, conflicts: list) -> str:
    lines = [f"## H-{num}: {c['signature']}",
             f"- status: pending",
             f"- kind: {c['kind']}  |  count: {c['count']}  |  last_seen: {c['last_seen'][:19]}",
             f"- proposed_organ: {propose_organ(c['signature'])}",
             f"- evidence: {', '.join(c['evidence'])}"]
    for s in c["samples"]:
        lines.append(f"- sample: {s}")
    if conflicts:
        lines.append(f"- possible_conflict_with: {'; '.join(conflicts[:4])}  (Gardener: reconcile)")
    # Synthesize a draft rule from evidence; agent can refine or replace
    draft = synthesize_draft_rule(c['signature'], c['kind'], c['samples'])
    lines.append(f"- draft_rule: {draft}")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Distill repeated failures/surprises into candidate heuristics")
    parser.add_argument("--min-cluster", type=int, default=3,
                        help="minimum occurrences before a cluster becomes a candidate (default 3)")
    parser.add_argument("--max-candidates", type=int, default=0,
                        help="cap staged candidates this run (0 = no cap; dream_loop uses 2)")
    parser.add_argument("--dry-run", action="store_true", help="print candidates; write nothing")
    args = parser.parse_args()

    nodes = load_dna_graph().get("nodes", [])
    clusters = collect_clusters(nodes, args.min_cluster)

    pending_text = PENDING_PATH.read_text(encoding="utf-8") if PENDING_PATH.exists() else ""

    staged, suppressed = [], []
    for c in clusters:
        covered_by = coverage_check(c["signature"])
        if covered_by:
            suppressed.append((c, covered_by))
            continue
        if c["signature"] in pending_text:
            suppressed.append((c, "already pending"))
            continue
        staged.append(c)
    if args.max_candidates > 0:
        overflow = staged[args.max_candidates:]
        staged = staged[:args.max_candidates]
    else:
        overflow = []

    print(f"clusters >= {args.min_cluster}: {len(clusters)}  |  "
          f"suppressed (covered/pending): {len(suppressed)}  |  staged: {len(staged)}"
          + (f"  |  deferred by cap: {len(overflow)}" if overflow else ""))
    for c, why in suppressed:
        print(f"  covered   [{c['count']:>3}x] {c['signature'][:70]}  <- {why}")
    for c in staged:
        print(f"  CANDIDATE [{c['count']:>3}x] {c['signature'][:70]}")
    for c in overflow:
        print(f"  deferred  [{c['count']:>3}x] {c['signature'][:70]} (cap; next night)")

    if args.dry_run or not staged:
        if not staged:
            print("nothing new to stage — the constitution already covers today's lessons")
        return 0

    if not pending_text:
        pending_text = ("# PENDING HEURISTICS — the Gardener's queue\n\n"
                        "Candidates distilled from repeated failures/surprises in the DNA graph.\n"
                        "The delegated Gardener (automation) rules each via `dream_loop --tend`:\n"
                        "doc-organ rules with a draft + evidence self-promote; gate-organ rules\n"
                        "queue for a capable cycle to implement, then record via\n"
                        "`python -m core.graphify_record heuristic ...`. A human may veto after the\n"
                        "fact (edit `status:` to `vetoed`). NOTHING here is active until promoted.\n\n")

    num = next_h_number(pending_text)
    additions = []
    for c in staged:
        # include same-batch entries staged so far, so family overlaps get flagged
        conflicts = conflict_check(c["signature"], nodes,
                                   pending_text + "\n".join(additions))
        additions.append(render_entry(num, c, conflicts))
        num += 1

    stamp = datetime.now(timezone.utc).isoformat()[:19]
    pending_text += f"\n<!-- distilled {stamp}Z -->\n" + "\n".join(additions)
    PENDING_PATH.write_text(pending_text, encoding="utf-8")
    print(f"\nstaged {len(staged)} candidate(s) -> {PENDING_PATH}")
    print("next: dream_loop --tend auto-rules the queue (doc-organ rules self-promote; "
          "gate-organ rules queue for a capable cycle); optional human veto-after.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
