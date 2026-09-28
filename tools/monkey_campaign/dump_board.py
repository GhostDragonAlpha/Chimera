"""Dump live kanban board state for the worker."""
import sqlite3, json
from pathlib import Path

root = Path(r"E:\ChimeraWork\monkey-coordination")
con = sqlite3.connect(str(root / "agent_slots.sqlite3"))
st = json.loads(con.execute("SELECT payload FROM state WHERE id=1").fetchone()[0])
b = st["kanban"]

print("=== CARDS ===")
for k, v in b.get("cards", {}).items():
    print(json.dumps({
        "id": k,
        "state": v["state"],
        "slot": v.get("slot"),
        "pub_branch": v.get("publication_branch"),
        "winner": (v.get("winner") or {}).get("pr_url"),
        "attempts": len(v.get("attempts", {})),
        "prs": list((v.get("prs") or {}).keys()),
    }, indent=1))

print("\n=== BACKLOG IDS ===")
for s in b.get("backlog", []):
    print(s["id"])
