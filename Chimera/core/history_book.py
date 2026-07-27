"""history_book — THE BOOK: everything the studio has learned, written down,
with a working searchable index.

"What good is learning if we can't write it down in the history books?"
(human directive, 2026-07-12). The DNA graph stores the learning; the Book
CURATES it — one chaptered, human-readable volume (docs/HISTORY_BOOK.md,
committed, regenerated nightly by dream_loop) backed by a full-text index
(docs/world/history.db, FTS5, machine-local) so any agent can ask "what do
we know about X?" and get an answer in milliseconds.

CHAPTERS
  I    The Constitution      promoted H-rules (CLAUDE.md) + Heuristic nodes
  II   Closed Doors          Elimination nodes — proven negatives + what survives
  III  Surprises             SurpriseMoment nodes — expectation vs reality, live
  IV   Verdicts & Grades     Observation + ProfessorGrade nodes
  V    Wills & Pains         PhaseComplete nodes — inheritance + phantom pains
  VI   Rep Milestones        promotions + per-feature ledger standing (reps.db)
  VII  The Drift Ledger      DSL spec->code coverage (dsl_drift.json)

CLI
  python -m core.history_book write               reindex + render the Book
  python -m core.history_book search --query X [--chapter closed-doors] [--limit 8]
  python -m core.history_book stats
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK_MD = ROOT / "docs" / "HISTORY_BOOK.md"
INDEX_DB = ROOT / "docs" / "world" / "history.db"
REPS_DB = ROOT / "docs" / "world" / "reps.db"
DRIFT_JSON = ROOT / "docs" / "rep_batteries" / "dsl_drift.json"
CLAUDE_MD = ROOT.parent / "CLAUDE.md"

CHAPTERS = {
    "constitution": "I. The Constitution (promoted heuristics)",
    "closed-doors": "II. Closed Doors (eliminations — proven negatives)",
    "surprises": "III. Surprises (expectation vs reality)",
    "verdicts": "IV. Verdicts & Grades",
    "wills": "V. Wills & Pains (generational inheritance)",
    "rep-milestones": "VI. Rep Milestones (resolution through repetition)",
    "drift": "VII. The Drift Ledger (spec promises vs kept)",
    "breakdowns": "VIII. The Breakdown Ledger (compound targets -> processed parts)",
}

# per-chapter render cap for the MD volume; the FTS INDEX always holds all
# entries — the Book stays readable, the search stays total.
MD_CAP = 40


@dataclass
class Entry:
    entry_id: str
    chapter: str          # key into CHAPTERS
    title: str
    body: str
    feature: str = ""
    when: str = ""


# ---------------------------------------------------------------------------
# entry builders — pure functions over their sources (unit-testable)
# ---------------------------------------------------------------------------

def entries_from_claude_md(md_text: str) -> list:
    out = []
    for h_id, rule in re.findall(r"\*\*\[(H-\d+)[^\]]*\]\*\*\s*(.+)", md_text):
        out.append(Entry(f"claude:{h_id}", "constitution", h_id, rule.strip()))
    return out


def entries_from_graph(nodes: list) -> list:
    out = []
    for n in nodes:
        ntype = n.get("type")
        ts = str(n.get("timestamp", ""))[:16]
        if ntype == "Heuristic":
            out.append(Entry(n["id"], "constitution",
                             n.get("signature", n["id"]),
                             str(n.get("rule", ""))[:600],
                             when=ts))
        elif ntype == "Elimination":
            body = (f"NOT: {n.get('boundary', '')}\n"
                    f"observed: {n.get('observed', '')}\n"
                    f"eliminates: {'; '.join(n.get('eliminates') or [])}\n"
                    f"SURVIVES (the narrowed search space): "
                    f"{'; '.join(n.get('survives') or [])}\n"
                    f"evidence: {n.get('evidence_ref', '')}")
            out.append(Entry(n["id"], "closed-doors",
                             f"{n.get('feature', '?')}: NOT {str(n.get('boundary', ''))[:70]}",
                             body, feature=n.get("feature", ""), when=ts))
        elif ntype == "SurpriseMoment":
            body = (f"context: {n.get('context', '')}\n"
                    f"expected: {n.get('expectation', '')}\n"
                    f"reality: {n.get('reality', '')}\n"
                    f"lesson hint: {n.get('lesson_hint', '')} [{n.get('source', 'agent')}]")
            out.append(Entry(n["id"], "surprises",
                             str(n.get('context', n['id']))[:80], body, when=ts))
        elif ntype == "Observation":
            feat = n.get("feature_name", n.get("feature", (n.get("parameters") or {}).get("feature", "")))
            verdict = n.get("verdict", (n.get("parameters") or {}).get("verdict", ""))
            notes = n.get("notes", (n.get("parameters") or {}).get("notes", ""))
            out.append(Entry(n["id"], "verdicts",
                             f"{feat}: {verdict}", str(notes)[:400],
                             feature=str(feat), when=ts))
        elif ntype == "ProfessorGrade":
            feat = n.get("feature", (n.get("parameters") or {}).get("feature", ""))
            grade = n.get("grade", (n.get("parameters") or {}).get("grade", ""))
            reasoning = n.get("reasoning", (n.get("parameters") or {}).get("reasoning", ""))
            out.append(Entry(n["id"], "verdicts",
                             f"{feat}: grade {grade}", str(reasoning)[:400],
                             feature=str(feat), when=ts))
        elif ntype == "Decomposition":
            parts = n.get("parts") or []
            body = (f"kind: {n.get('kind', '')}\n"
                    f"evidence: {'; '.join(n.get('evidence') or [])}\n"
                    + "\n".join(f"part {p.get('slug')}: {p.get('task_id')} "
                                f"({p.get('feature')})" for p in parts))
            out.append(Entry(n["id"], "breakdowns",
                             f"{n.get('target', '?')} -> {len(parts)} parts",
                             body, feature=n.get("target", ""), when=ts))
        elif ntype == "PhaseComplete":
            params = n.get("parameters") or {}
            inheritance = n.get("inheritance", params.get("inheritance", ""))
            pains = n.get("phantom_pains", params.get("phantom_pains", [])) or []
            phase = n.get("phase", params.get("phase", n["id"]))
            result = n.get("result", params.get("result", ""))
            body = f"result: {str(result)[:300]}"
            if inheritance:
                body += f"\nTHE WILL: {inheritance}"
            for i, p in enumerate(pains, 1):
                body += f"\npain P{i}: {p}"
            out.append(Entry(n["id"], "wills", str(phase)[:80], body, when=ts))
    return out


def entries_from_reps(promo_rows: list, status_rows: list) -> list:
    out = []
    for feature, tier, note in promo_rows:
        out.append(Entry(f"promo:{feature}:{tier}", "rep-milestones",
                         f"{feature} promoted to tier {tier}",
                         f"shaping promotion (streak rule): {note}",
                         feature=feature))
    for line in status_rows:
        feat = line.split()[0]
        out.append(Entry(f"repstat:{feat}", "rep-milestones",
                         f"{feat} — ledger standing", line, feature=feat))
    return out


def entries_from_drift(drift: dict) -> list:
    out = [Entry("drift:coverage", "drift", f"Spec coverage: {drift.get('coverage', '?')}",
                 f"{drift.get('note', '')}\ntriage: {drift.get('triage', '')}\n"
                 + "\n".join(f"{s}: {n} unkept" for s, n
                             in (drift.get("drift_by_spec") or {}).items()))]
    for e in drift.get("entries", []):
        if e.get("verdict") == "drift":
            out.append(Entry(f"drift:{e['token']}", "drift",
                             f"unkept promise: {e['token']}",
                             f"declared in {e['spec_file']}, no trace in Source/ "
                             f"(snake or CamelCase)", feature="System_DSL_Fidelity"))
    return out


# ---------------------------------------------------------------------------
# collection + index + render
# ---------------------------------------------------------------------------

def collect_entries() -> list:
    entries: list = []
    if CLAUDE_MD.exists():
        entries += entries_from_claude_md(CLAUDE_MD.read_text(encoding="utf-8",
                                                              errors="replace"))
    try:
        from core.graphify_interface import load_dna_graph
        entries += entries_from_graph(load_dna_graph().get("nodes", []))
    except Exception:
        pass
    try:
        promo_rows, status_rows = [], []
        if REPS_DB.exists():
            con = sqlite3.connect(REPS_DB)
            promo_rows = con.execute(
                "SELECT feature, tier, note FROM promotions").fetchall()
            con.close()
        from core.rep_engine import status_lines
        status_rows = status_lines(limit=32)
        entries += entries_from_reps(promo_rows, status_rows)
    except Exception:
        pass
    if DRIFT_JSON.exists():
        try:
            entries += entries_from_drift(json.loads(DRIFT_JSON.read_text(encoding="utf-8")))
        except Exception:
            pass
    return entries


def reindex(entries: list, db_path: Path = None) -> int:
    """(Re)build the FTS5 index — derived data, dropped and rebuilt whole."""
    db_path = db_path or INDEX_DB
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.execute("DROP TABLE IF EXISTS book")
    con.execute("CREATE VIRTUAL TABLE book USING fts5"
                "(entry_id, chapter, title, body, feature, whenish)")
    con.executemany(
        "INSERT INTO book(entry_id, chapter, title, body, feature, whenish) "
        "VALUES(?,?,?,?,?,?)",
        [(e.entry_id, e.chapter, e.title, e.body, e.feature, e.when)
         for e in entries])
    con.commit()
    con.close()
    return len(entries)


def _fts_quote(query: str) -> str:
    """Quote every token — hyphens/dots parse as FTS5 operators otherwise
    (the world_store lesson, kept)."""
    return " ".join(f'"{t}"' for t in query.split() if t)


def search(query: str, chapter: str = None, limit: int = 8,
           db_path: Path = None) -> list:
    db_path = db_path or INDEX_DB
    if not db_path.exists():
        reindex(collect_entries(), db_path)
    con = sqlite3.connect(db_path)
    sql = ("SELECT entry_id, chapter, title, "
           "snippet(book, 3, '>>', '<<', ' ... ', 18) FROM book "
           "WHERE book MATCH ?")
    params: list = [_fts_quote(query)]
    if chapter:
        sql += " AND chapter = ?"
        params.append(chapter)
    sql += " ORDER BY rank LIMIT ?"
    params.append(limit)
    rows = con.execute(sql, params).fetchall()
    con.close()
    return rows


def render_md(entries: list) -> str:
    by_chapter: dict = {k: [] for k in CHAPTERS}
    for e in entries:
        by_chapter.setdefault(e.chapter, []).append(e)
    feature_index: dict = {}
    for e in entries:
        if e.feature:
            feature_index.setdefault(e.feature, []).append(e.entry_id)
    lines = [
        "# THE HISTORY BOOK",
        "",
        "> Everything the studio has learned, written down. Regenerated nightly",
        "> by `dream_loop`; full-text search over EVERY entry (this file caps",
        f"> chapters at {MD_CAP} for readability):",
        "> `python -m core.history_book search --query <anything> [--chapter closed-doors]`",
        "",
        f"**{len(entries)} entries** across {sum(1 for v in by_chapter.values() if v)} chapters.",
        "",
    ]
    for key, heading in CHAPTERS.items():
        rows = by_chapter.get(key, [])
        lines += [f"## {heading}", ""]
        if not rows:
            lines += ["*(empty — the studio has not learned this kind of thing yet)*", ""]
            continue
        lines.append(f"*{len(rows)} entries; showing {min(len(rows), MD_CAP)}.*")
        lines.append("")
        for e in rows[:MD_CAP]:
            when = f" `{e.when}`" if e.when else ""
            lines.append(f"### {e.title}{when}")
            lines.append(f"<sub>`{e.entry_id}`</sub>")
            lines.append("")
            for ln in e.body.splitlines():
                lines.append(f"> {ln}")
            lines.append("")
    lines += ["## Index of Features", ""]
    for feat in sorted(feature_index):
        ids = feature_index[feat]
        lines.append(f"- **{feat}** — {len(ids)} entr{'y' if len(ids) == 1 else 'ies'}: "
                     + ", ".join(f"`{i}`" for i in ids[:6])
                     + (" ..." if len(ids) > 6 else ""))
    lines.append("")
    return "\n".join(lines)


def write() -> str:
    entries = collect_entries()
    n = reindex(entries)
    BOOK_MD.write_text(render_md(entries), encoding="utf-8")
    chapters = len({e.chapter for e in entries})
    return (f"[book] {n} entries indexed across {chapters} chapters -> "
            f"{BOOK_MD.relative_to(ROOT)} + FTS at {INDEX_DB.relative_to(ROOT)}")


def stats() -> dict:
    entries = collect_entries()
    out: dict = {}
    for e in entries:
        out[e.chapter] = out.get(e.chapter, 0) + 1
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("write")
    p_search = sub.add_parser("search")
    p_search.add_argument("--query", required=True)
    p_search.add_argument("--chapter", choices=list(CHAPTERS))
    p_search.add_argument("--limit", type=int, default=8)
    sub.add_parser("stats")
    args = parser.parse_args()

    if args.cmd == "write":
        print(write())
    elif args.cmd == "search":
        rows = search(args.query, args.chapter, args.limit)
        if not rows:
            print("(no entries match — the book does not know this yet)")
        for entry_id, chapter, title, snip in rows:
            print(f"[{chapter}] {title}")
            print(f"    {snip}")
            print(f"    ({entry_id})")
    elif args.cmd == "stats":
        for chapter, n in sorted(stats().items()):
            print(f"{CHAPTERS.get(chapter, chapter):58s} {n:>5}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
