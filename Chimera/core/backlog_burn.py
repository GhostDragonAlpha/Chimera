"""Backlog burn — surfaces the already-recorded-but-never-actioned issue backlog as
core.rehearsal candidates (same tier as dream_loop/gardener: a standalone, periodic pass,
not a step wedged into .claude/workflows/chimera-task-cycling.js's fixed 4-task cycle).

Every existing automated mechanism in this project points forward: dream_loop distills a
mistake into a rule, gardener promotes the rule, collapse_proxy advances a feature's
verification status. Nothing points backward — the phantom-pain and task_progress.md NEXT
backlog those mechanisms accumulate is written once and then only ever read by whoever
happens to look. core.rehearsal already has the right extension point for this
(--candidates-file, described in its own docstring as "how duty cycles/architecture docs
curate structured work") but nothing has ever populated it from the backlog automatically.
This module is that missing supply line. needs_refinement features are already covered by
rehearsal.enumerate_candidates itself — this module supplies the two sources nothing else
does:

  1. Phantom pains (docs/GENERATION_PROTOCOL.md) still open with no --pain-verdict
     disposition. Pains get re-declared forward across phases with no enforced dedup
     convention — some later declarations are a full fresh sentence, others just a short
     pointer back to an earlier pain's id (e.g. "phase_da55128ac...:P1 distiller token-
     coverage suppression"). This module groups any pain whose text starts with a
     recognizable earlier pain id back to that root, so one real issue re-declared five
     times doesn't get counted as five separate candidates. This grouping is a heuristic,
     not a guarantee — printed and written with its raw reaffirm-count so nothing is hidden.

  2. The MOST RECENT task_progress.md session's own "## NEXT" list, keyword-scored for
     bug/gap language ("not wired", "cannot", "doesn't inherit", ...) vs feature-request
     language. Deliberately scoped to only the top entry: the log has no mechanism for
     marking an old NEXT item done when a later session closes it (this session's own
     entry closed a NEXT item from two sessions back by name, but never edited that old
     entry to say so) — scanning the full history would re-surface already-fixed items
     forever. The keyword match is approximate and printed alongside every candidate
     (rehearsal.py's own rule: "confidence exposed, never faked") — verify before trusting.

Usage:
  python -m core.backlog_burn --scan                          # print-only report
  python -m core.backlog_burn --scan --write-candidates FILE  # also write rehearsal JSON
Then, separately — never auto-chained, one tool does one job:
  python -m core.rehearsal --candidates-file FILE --decide
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    from core.graphify_interface import load_dna_graph, collect_inheritance
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from core.graphify_interface import load_dna_graph, collect_inheritance

ROOT = Path(__file__).resolve().parent.parent
TASK_PROGRESS = ROOT.parent / "task_progress.md"
MAX_CANDIDATES = 8

# Deliberately biased toward clear code/design-defect language, not process/authorization
# blockers ("BLOCKED (needs human)" is common, ordinary phrasing and not itself a bug).
BUG_SIGNALS = [
    "not wired", "cannot be", "can never", "doesn't inherit", "does not inherit",
    "no such", "never calls", "never call", "missing method", "not implemented",
    r"no [`*]{0,2}\w+\(\)[`*]{0,2} (function|method)", "silently", "unpickable", "never picked",
    "broken", r"\bbug\b", r"\bdefect\b", "regression", "doesn't work", "does not work",
    "never fires", "never wired", "invisible to",
]
PAIN_REF_RE = re.compile(r"^(phase_[a-f0-9]{6,}:P\d+)\b")
NEXT_ITEM_RE = re.compile(r"(?m)^\d+\.\s+(.+?)(?=\n\d+\.\s|\n---|\Z)", re.DOTALL)


def _dedupe_pains(open_pains):
    """Group re-declared pains back to their root id (see module docstring). Returns
    [{root_id, text, reaffirm_count, max_age_days}] — longest text per group wins as the
    representative (root declarations tend to be the full sentence; re-declarations are
    often just a short pointer)."""
    by_id = {p["id"]: p for p in open_pains}
    groups = {}

    def resolve_root(pain, seen):
        m = PAIN_REF_RE.match(pain["text"].strip())
        if m and m.group(1) in by_id and m.group(1) != pain["id"] and m.group(1) not in seen:
            return resolve_root(by_id[m.group(1)], seen | {pain["id"]})
        return pain["id"]

    for p in open_pains:
        root = resolve_root(p, {p["id"]})
        g = groups.setdefault(root, {"root_id": root, "text": "", "reaffirm_count": 0, "max_age_days": 0})
        g["reaffirm_count"] += 1
        g["max_age_days"] = max(g["max_age_days"], p["age_days"])
        if len(p["text"]) > len(g["text"]):
            g["text"] = p["text"]
    return list(groups.values())


def scan_phantom_pains(nodes):
    inh = collect_inheritance(nodes)
    groups = _dedupe_pains(inh["open_pains"])
    cands = []
    for g in groups:
        value = 1.0 + 0.3 * min(g["reaffirm_count"] - 1, 4) + 0.05 * min(g["max_age_days"], 20)
        cands.append({
            "name": f"PhantomPain_{g['root_id']}",
            "value": round(value, 2),
            "capable_only": True,
            "why": f"open {g['reaffirm_count']}x since, {g['max_age_days']}d old, never dispositioned",
            "recipe": f"Investigate and either fix or explicitly dispose via "
                      f"'python -m core.postflight --pain-verdict {g['root_id']}:confirmed|refuted': "
                      f"{g['text'][:300]}",
        })
    return cands


def _classify_next_item(text):
    lower = text.lower()
    return [kw for kw in BUG_SIGNALS if re.search(kw, lower)]


def scan_next_items():
    """Bug-shaped candidates from the MOST RECENT task_progress.md session's own NEXT
    list only — see module docstring for why the full history is deliberately not scanned."""
    if not TASK_PROGRESS.exists():
        return []
    text = TASK_PROGRESS.read_text(encoding="utf-8")
    m = re.search(r"(?m)^## NEXT\s*$", text)
    if not m:
        return []
    block = text[m.end():]
    end = re.search(r"(?m)^---\s*$", block)
    block = block[:end.start()] if end else block

    cands = []
    for item_m in NEXT_ITEM_RE.finditer(block):
        item_text = " ".join(item_m.group(1).split())
        hits = _classify_next_item(item_text)
        if not hits:
            continue  # no bug signal -- likely a feature/process item, not this tool's job
        digest = hashlib.md5(item_text.encode("utf-8")).hexdigest()[:8]
        cands.append({
            "name": f"NextItemBug_{digest}",
            "value": round(1.0 + 0.2 * len(hits), 2),
            "capable_only": True,
            "why": f"keyword signal(s): {', '.join(hits)} (approximate -- verify before trusting)",
            "recipe": item_text[:400],
        })
    return cands


def main():
    parser = argparse.ArgumentParser(
        description="Surface the phantom-pain + NEXT-item backlog as core.rehearsal candidates")
    parser.add_argument("--scan", action="store_true", help="print the backlog report")
    parser.add_argument("--write-candidates", default=None,
                        help="also write a core.rehearsal --candidates-file JSON here")
    args = parser.parse_args()
    if not args.scan:
        parser.error("use --scan (optionally with --write-candidates FILE)")

    nodes = load_dna_graph().get("nodes", [])
    cands = scan_phantom_pains(nodes) + scan_next_items()
    cands.sort(key=lambda c: -c["value"])
    cands = cands[:MAX_CANDIDATES]

    print(f"[backlog_burn] {len(cands)} candidate(s) surfaced from the never-actioned backlog "
          f"(phantom pains + most-recent NEXT list; both sources are approximate, verify before trusting):")
    for c in cands:
        print(f"  {c['name']:<28} value={c['value']:<5} {c['why']}")
        print(f"      recipe: {c['recipe'][:150]}")
    if not cands:
        print("  backlog empty -- nothing surfaced")

    if args.write_candidates:
        Path(args.write_candidates).write_text(json.dumps(cands, indent=2), encoding="utf-8")
        print(f"\nWrote {len(cands)} candidate(s) to {args.write_candidates}")
        print(f"Next (separate, manual step): python -m core.rehearsal "
              f"--candidates-file {args.write_candidates} --decide")
    elif cands:
        print("\n(dry-run: pass --write-candidates FILE to feed these into core.rehearsal)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
