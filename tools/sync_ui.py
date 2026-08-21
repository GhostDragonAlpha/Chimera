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
    ROOT / ".tmp/qualify/source246_sheet.png",              # -> donor_sheet.png
    ROOT / ".tmp/qualify/source_donor/source_score.json",   # -> donor_gate.json
    ROOT / "models/littlebear/donor.splat",                 # -> donor.splat (APPROVED DONOR: littleBear, SuperSplat dcb0a76d)
    ROOT / "models/triposplat/static/viewer/_qualify/regions.splat",  # -> ui/regions.splat (verification paint)
    ROOT / ".tmp/hunt/regions_sheet.png",                   # -> ui/regions_sheet.png
    ROOT / "models/littlebear/genomes/regions.json",        # -> ui/regions.json (region stats = training targets)
    ROOT / ".tmp/preview/patches_sheet.png",                # -> ui/patches_sheet.png (operator-approved corpus preview)
    ROOT / ".tmp/qualify_littlebear_fur/report.json",       # -> ui/fur_qualify.json (the eye's verdicts)
    ROOT / ".tmp/qualify_littlebear_fur/rejects_sheet.png", # -> ui/fur_rejects.png (operator audit)
    ROOT / "tools/specs/bear34_parts_plan.json",            # -> parts_plan.json
    ROOT / "Chimera/docs/THE_STORY.md",
    ROOT / "ChimeraEngine/docs_THE_STORY.md",
]

RENAMES = {
    "sources.png": "sources_sheet.png",
    "sources_furry.png": "sources_sheet.png",
    "source246_sheet.png": "donor_sheet.png",
    "source_score.json": "donor_gate.json",
    "co3d246_dense.splat": "donor.splat",
    "bear34_parts_plan.json": "parts_plan.json",
    "report.json": "fur_qualify.json",
    "rejects_sheet.png": "fur_rejects.png",
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
