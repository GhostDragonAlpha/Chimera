"""sync_ui.py -- copy the latest pipeline artifacts into the viewer's ui/ dir.

engine.html is dumb on purpose: it reads only what sync_ui.py put there.
Run this after any pipeline step that produces scores, sheets, or plans.

  .venv-gs/Scripts/python.exe tools/sync_ui.py
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UI = ROOT / "models/triposplat/static/viewer/ui"

ARTIFACTS = [
    ROOT / "tools" / "ui" / "engine.html",                # the tracked source of the UI
    ROOT / ".tmp/qualify/sources.json",
    ROOT / ".tmp/qualify/sources_furry.json",
    ROOT / ".tmp/qualify/sources.png",                      # -> sources_sheet.png
    ROOT / ".tmp/qualify/sources_furry.png",                # furry pass WINS the sheet
    ROOT / ".tmp/qualify/full/scores.json",
    ROOT / ".tmp/qualify/full/scored_sheet.png",
    ROOT / "tools/specs/bear34_parts_plan.json",            # -> parts_plan.json
    ROOT / "Chimera/docs/THE_STORY.md",
    ROOT / "ChimeraEngine/docs_THE_STORY.md",
]

RENAMES = {
    "sources.png": "sources_sheet.png",
    "sources_furry.png": "sources_sheet.png",
    "bear34_parts_plan.json": "parts_plan.json",
    "docs_THE_STORY.md": "THE_STORY.md",  # fallback if Chimera/docs copy missing
}


def main() -> int:
    UI.mkdir(parents=True, exist_ok=True)
    copied = []
    for src in ARTIFACTS:
        if not src.exists():
            continue
        if src.suffix == ".html":
            dst = UI.parent / src.name  # pages live at the viewer root, data in ui/
        else:
            dst = UI / RENAMES.get(src.name, src.name)
        if src.suffix == ".md" and (UI / "THE_STORY.md").exists():
            continue  # first story file wins
        shutil.copy(src, dst)
        copied.append(dst.name)
    print("ui/ <-", ", ".join(copied) if copied else "(nothing found)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
