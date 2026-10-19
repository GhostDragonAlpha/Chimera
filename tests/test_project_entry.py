# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the actual template/project entry point without starting a GPU helper."""
import copy
import hashlib
import json
import os
from pathlib import Path
import bpy
from chimera_studio import gpu_workspace as w

root = Path(os.environ["CHIMERA_STUDIO_ROOT"])
project = root.parent / "Projects/Membrane Workshop/Chimera Membrane Workshop.blend"
assert Path(bpy.data.filepath).resolve() == project.resolve()
assert hasattr(bpy.types.Scene, "chimera_blocks")
assert w._session is None and not w.busy(), "Opening a project started GPU work"
before = copy.deepcopy(w.document())
assert before and "assembly" in before["spec"]
ids = sorted(o["chimera_block_id"] for o in bpy.data.objects if o.get("chimera_block_id"))
assert len(ids) == 3 and len(set(ids)) == 3
assert len(json.loads(bpy.context.scene.chimera_blocks.connections)) == 2
original_hash = hashlib.sha256(project.read_bytes()).hexdigest()
out = root / ".user/project-entry-check"
out.mkdir(parents=True, exist_ok=True)
check_file = out / "Reopened construction with spaces.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(check_file), check_existing=False)
bpy.ops.wm.open_mainfile(filepath=str(check_file))
assert w._session is None and not w.busy()
assert w.document() == before, "Physical/render checkpoint changed on save/reopen"
assert sorted(o["chimera_block_id"] for o in bpy.data.objects if o.get("chimera_block_id")) == ids
assert len(json.loads(bpy.context.scene.chimera_blocks.connections)) == 2
assert hashlib.sha256(project.read_bytes()).hexdigest() == original_hash
report = {
    "pass": True, "project": str(project), "binary": bpy.app.binary_path,
    "app_template": "ChimeraStudio", "source_films": len(ids), "connections": 2,
    "opened_offline": True, "native_state_and_render_preserved": True,
    "working_project_unchanged": True, "source_ids_preserved": True,
    "scope": "Real Blender project/template launch plus offline save/reopen; no GPU inference or simulation."
}
(root / "evidence/project-entry.json").write_bytes((json.dumps(report, indent=2)+"\n").encode("utf-8"))
print("PASS project entry, native checkpoint, source identity and save/reopen")
import chimera_studio
chimera_studio.unregister()
