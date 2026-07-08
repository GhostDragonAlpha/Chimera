"""Gardener-delegate — fully automated heuristic tending (automation amendment 2026-07-07).

Pending heuristics with a real draft_rule and sufficient evidence are auto-ruled;
automated veto-after: edit any entry's status to `vetoed` and the next tend demotes it, doc
line removed, automated veto recorded. Machine signals are final; automated rejection permanently
outranks every other signal.

Deterministic policy (no LM):
  - agent_note recommends VETO / draft_rule marked "(subsumed" -> status `vetoed-auto`
    (tombstone stays in the file so the distiller never re-proposes the signature).
  - draft_rule present AND (count >= min_count OR kind == human_rejection):
      organ claude_md      -> append bullet to CLAUDE.md "Generation Protocol" section,
                              record_heuristic, status `promoted (auto)`.
      organ mcp_pathways   -> append TRAP line to docs/MCP_PATHWAYS.md "Promoted
                              Heuristic Traps" section, record_heuristic, status
                              `promoted (auto)`.
      organ gate           -> status `approved (auto — implementation pending)`:
                              writing gate CODE stays a capable-cycle task (CYCLE_PROMPT
                              branch A); the approval itself no longer waits.
    (agent_note saying "Approve as claude_md" overrides proposed_organ.)
  - no draft_rule -> left pending, flagged NEEDS-DRAFT for a capable cycle.
  - status `vetoed` written by the human on a promoted-auto entry -> DEMOTE: remove the
    doc line, record surprise --source human, status `vetoed (human — demoted <date>)`.

Usage: python -m core.gardener --tend [--dry-run] [--min-count 3]
"""

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from core.graphify_interface import record_heuristic, record_surprise
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from core.graphify_interface import record_heuristic, record_surprise

ROOT = Path(__file__).resolve().parent.parent          # E:/PythonChimera/Chimera
WSROOT = ROOT.parent                                   # E:/PythonChimera
PENDING = ROOT / "docs" / "PENDING_HEURISTICS.md"
CLAUDE_MD = WSROOT / "CLAUDE.md"
PATHWAYS = ROOT / "docs" / "MCP_PATHWAYS.md"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def parse_entries(text: str):
    """Split PENDING_HEURISTICS.md into (header, [entry dicts with raw block])."""
    parts = re.split(r"(?m)^## (H-\d+): ", text)
    header, entries = parts[0], []
    for i in range(1, len(parts), 2):
        hid, block = parts[i], parts[i + 1]
        sig = block.splitlines()[0].strip() if block else ""
        def grab(field, default=""):
            m = re.search(rf"(?m)^- {field}:\s*(.+)$", block)
            return m.group(1).strip() if m else default
        kindline = grab("kind")
        count = 0
        m = re.search(r"count:\s*(\d+)", kindline)
        if m:
            count = int(m.group(1))
        entries.append({
            "id": hid, "signature": sig, "block": block,
            "status": grab("status"),
            "kind": kindline.split("|")[0].strip(),
            "count": count,
            "organ": grab("proposed_organ"),
            "evidence": [e.strip() for e in grab("evidence").split(",") if e.strip()],
            "draft_rule": grab("draft_rule"),
            "agent_note": grab("agent_note"),
        })
    return header, entries


def _set_status(block: str, new_status: str) -> str:
    return re.sub(r"(?m)^- status:.*$", f"- status: {new_status}", block, count=1)


def _append_claude_md_bullet(rule: str, hid: str, dry: bool) -> bool:
    text = CLAUDE_MD.read_text(encoding="utf-8")
    bullet = f"- **[{hid}, auto-promoted {_now()}]** {rule}\n"
    if rule in text:
        return True  # already present
    anchor = "\n## Architecture Overview"
    if anchor not in text:
        return False
    if not dry:
        CLAUDE_MD.write_text(text.replace(anchor, bullet + anchor, 1), encoding="utf-8")
    return True


def _append_pathway_trap(rule: str, hid: str, sig: str, dry: bool) -> bool:
    text = PATHWAYS.read_text(encoding="utf-8")
    if rule in text:
        return True
    section = "## Promoted Heuristic Traps (auto-tended)"
    line = f"- **[{hid}] {sig}** — {rule}\n"
    if not dry:
        if section not in text:
            if not text.endswith("\n"):
                text += "\n"
            text += f"\n{section}\n\n"
        if not text.endswith("\n"):
            text += "\n"
        text += line  # section lives at end of file; the line joins its list
        PATHWAYS.write_text(text, encoding="utf-8")
    return True


def _remove_doc_line(rule: str) -> int:
    """Demote: strip any line containing the rule text from both organs."""
    removed = 0
    for f in (CLAUDE_MD, PATHWAYS):
        text = f.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        kept = [ln for ln in lines if rule not in ln]
        if len(kept) != len(lines):
            f.write_text("".join(kept), encoding="utf-8")
            removed += len(lines) - len(kept)
    return removed


def tend(dry_run: bool = False, min_count: int = 3) -> dict:
    from core.graphify_interface import record_heuristic, record_surprise
    text = PENDING.read_text(encoding="utf-8")
    header, entries = parse_entries(text)
    report = {"promoted": [], "approved_gate": [], "vetoed_auto": [],
              "demoted_human": [], "needs_draft": [], "untouched": []}
    new_blocks = []

    for e in entries:
        block, status = e["block"], e["status"].lower()
        note, rule = e["agent_note"].lower(), e["draft_rule"]
        # "(subsumed..." = duplicate -> tombstone; "(agent: ..." = placeholder -> needs draft
        subsumed = rule.lower().startswith("(subsumed") or "recommend veto" in note
        if rule.startswith("("):
            rule = "" if not subsumed else rule

        if status.startswith("vetoed") and "demoted" not in status and "promoted" not in status \
                and "(auto" not in status and status != "vetoed-auto":
            # human wrote a bare `vetoed` — if we previously promoted it, demote
            if rule and not rule.startswith("(") and not dry_run:
                removed = _remove_doc_line(rule)
                if removed:
                    record_surprise(context=f"Gardener-auto promoted {e['id']} ({e['signature']})",
                                    reality="Human vetoed it — demoted, doc line removed",
                                    source="human")
                    block = _set_status(block, f"vetoed (human — demoted {_now()})")
                    report["demoted_human"].append(e["id"])
                else:
                    report["untouched"].append(f"{e['id']} (vetoed, nothing to demote)")
            elif dry_run and rule and not rule.startswith("("):
                report["demoted_human"].append(f"{e['id']} (would demote)")
            else:
                report["untouched"].append(e["id"])
        elif status == "pending":
            organ = e["organ"]
            if "approve as claude_md" in note:
                organ = "claude_md"
            if subsumed:
                if not dry_run:
                    block = _set_status(block, f"vetoed-auto (tombstone {_now()} — {('subsumed' if rule.startswith('(') else 'per agent_note')})")
                report["vetoed_auto"].append(e["id"])
            elif rule and (e["count"] >= min_count or e["kind"] == "human_rejection"):
                if organ == "gate":
                    if not dry_run:
                        block = _set_status(block, f"approved (auto {_now()} — implementation pending, capable cycle)")
                    report["approved_gate"].append(e["id"])
                elif organ in ("claude_md", "mcp_pathways"):
                    ok = (_append_claude_md_bullet(rule, e["id"], dry_run) if organ == "claude_md"
                          else _append_pathway_trap(rule, e["id"], e["signature"], dry_run))
                    if ok and not dry_run:
                        record_heuristic(e["signature"], rule, organ,
                                         evidence_ids=e["evidence"][:8])
                        block = _set_status(block, f"promoted (auto {_now()})")
                    if ok:
                        report["promoted"].append(f"{e['id']} -> {organ}")
                    else:
                        report["untouched"].append(f"{e['id']} (organ anchor missing)")
                else:
                    report["untouched"].append(f"{e['id']} (unknown organ {organ})")
            elif not rule:
                report["needs_draft"].append(e["id"])
            else:
                report["untouched"].append(f"{e['id']} (count {e['count']} < {min_count})")
        else:
            report["untouched"].append(f"{e['id']} ({e['status']})")
        new_blocks.append((e["id"], e["signature"], block))

    if not dry_run:
        out = header + "".join(f"## {hid}: {blk}" for hid, sig, blk in new_blocks)
        PENDING.write_text(out, encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description="Automated heuristic tending (delegated Gardener)")
    parser.add_argument("--tend", action="store_true", help="process the pending queue")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--min-count", type=int, default=3)
    args = parser.parse_args()
    if not args.tend:
        parser.error("use --tend (optionally with --dry-run)")
    report = tend(dry_run=args.dry_run, min_count=args.min_count)
    mode = "DRY-RUN" if args.dry_run else "APPLIED"
    print(f"[gardener] {mode}")
    for k, v in report.items():
        if v:
            print(f"  {k} ({len(v)}): {', '.join(v)}")
    if not any(report.values()):
        print("  queue empty or nothing actionable")


if __name__ == "__main__":
    main()
