"""export_pose.py — export the current engine state as a JSON snapshot.

Reads the HTTP twins (/keys, /cameras, /show, /scene) and writes a
timestamped JSON file to Saved/poses/. No engine rebuild needed —
pure Python over the existing API.

Usage:
    python tools/export_pose.py                    # auto-name
    python tools/export_pose.py --name rest        # named pose
    python tools/export_pose.py --out my_pose.json # custom path
"""
import argparse
import json
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

URL = "http://localhost:8090"


def get(path, timeout=5):
    with urllib.request.urlopen(URL + path, timeout=timeout) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser(description="export current engine state as JSON")
    ap.add_argument("--name", default=None, help="pose name (default: auto-timestamp)")
    ap.add_argument("--out", default=None, help="output file path")
    a = ap.parse_args()

    # Gather all state from the HTTP twins
    state = {}
    for key, path in [("keys", "/keys"), ("cameras", "/cameras"),
                       ("show", "/show"), ("scene", "/scene"),
                       ("studio", "/studio")]:
        try:
            state[key] = get(path)
        except Exception as e:
            state[key] = {"error": str(e)}

    # Metadata
    name = a.name or datetime.now().strftime("%Y%m%d_%H%M%S")
    state["export_name"] = name
    state["export_time"] = datetime.now().isoformat(timespec="seconds")

    # Write to disk
    if a.out:
        out_path = Path(a.out)
    else:
        out_dir = Path("Saved/poses")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{name}.json"

    out_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"exported to {out_path}")
    print(f"  keys: {len(state.get('keys', {}).get('keys', []))} poses")
    print(f"  cameras: {len(state.get('cameras', {}).get('bookmarks', []))} bookmarks")
    print(f"  show: {state.get('show', {}).get('clock', '?')} "
          f"t={state.get('show', {}).get('time', 0):.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
