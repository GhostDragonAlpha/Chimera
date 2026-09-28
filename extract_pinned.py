"""MAT2-W03 sergeant attempt: extract pinned blobs READ-ONLY from the
E:/PythonChimera git object store into this attempt workspace.

Training revisions:
  17ba94b948ca217c1bbf8f7dee5b51b995b387bb  viswalk lane (walk-anchor statedump + scene generator)
  a62b286effa27ee2db7bbcb65507a2ac45ad0d0c  SHUTDOWN CHECKPOINT (walker_env_v2 build state)

Every extracted file's sha256 is recorded. Blob identity for
gait_unit_viswalk_dump.cpp must equal a7bfe15e34e25a34c5316d65038b072d79ac529a
(the pinned statedump source blob cited by MAT2-P02 reproduction/build_statedump.json).
No writes outside this attempt workspace; the source repos are opened read-only.
Agent: arrival-db26712d6a264e4899c951f55b074d80
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

SRC_REPO = "E:/PythonChimera"
HERE = Path(__file__).resolve().parent
RECORD = {}

REV_WALK = "17ba94b948ca217c1bbf8f7dee5b51b995b387bb"
REV_SHUTDOWN = "a62b286effa27ee2db7bbcb65507a2ac45ad0d0c"

WALK_FILES = [
    "tools/science_funnel/gait_scene.py",
    "tools/science_funnel/common.py",
    "tools/science_funnel/coupled_arm.py",
    "tools/science_funnel/macaque_anatomy.py",
    "tools/science_funnel/__init__.py",
    "tools/creature_graph/store.py",
    "tools/creature_graph/schema.py",
    "tools/creature_graph/views.py",
    "tools/creature_graph/data/creature_graph.json",
] + [f"tools/creature_graph/data/creature_graph.bulk_{i:02d}.json" for i in range(11)] + [
    "tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json",
    "tools/science_funnel/validation/gait_zero_20260919/derived_entry_pose.json",
    "tools/science_funnel/validation/gait_zero_20260919/derived_load_strut_trade.json",
    "tools/science_funnel/validation/gait_zero_20260919/derived_leaned_entry.json",
    "tools/science_funnel/validation/gait_zero_20260919/trunk_vault_reachable.json",
    "tools/science_funnel/validation/gait_zero_20260919/trunk_pitch_table.json",
    "tools/science_funnel/validation/gait_zero_20260919/derived_height_hold.json",
    # statedump + include closure
    "tools/science_funnel/validation/visible_walk_20260923/native/gait_unit_viswalk_dump.cpp",
    "ChimeraEngine/engine/gait_controller.hpp",
    "ChimeraEngine/engine/coupled_articulation.hpp",
    "ChimeraEngine/engine/earth_environment.hpp",
    "ChimeraEngine/engine/force_models.hpp",
    "ChimeraEngine/native/viewer3rd/json.hpp",
]


def blob(rev, path):
    r = subprocess.run(["git", "-C", SRC_REPO, "cat-file", "blob", f"{rev}:{path}"],
                       capture_output=True)
    if r.returncode != 0:
        return None
    return r.stdout


def extract(rev, paths, dest_root):
    for p in paths:
        b = blob(rev, p)
        if b is None:
            RECORD[f"{rev}:{p}"] = {"status": "MISSING"}
            print("MISSING", p)
            continue
        dest = dest_root / p
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b)
        RECORD[f"{rev}:{p}"] = {
            "status": "EXTRACTED",
            "sha256": hashlib.sha256(b).hexdigest(),
            "bytes": len(b),
        }
        print("ok", p, len(b))


def main():
    extract(REV_WALK, WALK_FILES, HERE / "engine_tree17")
    # The pinned statedump source identity gate: the MAT2-P02 record cites git
    # OBJECT id a7bfe15e34e25a34c5316d65038b072d79ac529a (sha1 of "blob <len>\\0"),
    # whose raw content sha256 is dea2be78762860b201a348824fd6a4a4fe9f2a1dd3f9552157187729568f1cab.
    key = f"{REV_WALK}:tools/science_funnel/validation/visible_walk_20260923/native/gait_unit_viswalk_dump.cpp"
    rec = RECORD.get(key, {})
    ls = subprocess.run(["git", "-C", SRC_REPO, "ls-tree", REV_WALK, "--",
                         key.split(":", 1)[1]], capture_output=True, text=True).stdout
    obj_id = ls.split()[2] if len(ls.split()) >= 3 else None
    if obj_id != "a7bfe15e34e25a34c5316d65038b072d79ac529a" or \
       rec.get("sha256") != "dea2be78762860b201a348824fd6a4a4fe9f2a1dd3f9552157187729568f1cab":
        print("FATAL: statedump blob identity mismatch", obj_id, rec)
        sys.exit(1)
    print("statedump identity OK (git object a7bfe15e, content sha256 dea2be78)")

    # Walker v2 build inputs from the shutdown checkpoint, with transitive
    # local includes resolved inside tools/science_funnel/typeb_gpu.
    base = "tools/science_funnel/typeb_gpu/"
    seen, queue = set(), ["walker_env.cu", "host_loop.cxx"]
    include_guards = []
    while queue:
        rel = queue.pop(0)
        if rel in seen:
            continue
        seen.add(rel)
        b = blob(REV_SHUTDOWN, base + rel)
        if b is None:
            RECORD[f"{REV_SHUTDOWN}:{base}{rel}"] = {"status": "MISSING"}
            print("MISSING", base + rel)
            continue
        dest = HERE / "typeb_build" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b)
        RECORD[f"{REV_SHUTDOWN}:{base}{rel}"] = {
            "status": "EXTRACTED",
            "sha256": hashlib.sha256(b).hexdigest(),
            "bytes": len(b),
        }
        print("ok", base + rel, len(b))
        text = b.decode("utf-8", "replace")
        for line in text.splitlines():
            ls = line.strip()
            if ls.startswith("#include"):
                inc = ls.split('"')[1] if '"' in ls else None
                if inc and not inc.startswith("<"):
                    cand = inc
                    if cand not in seen:
                        queue.append(cand)
                    include_guards.append((rel, cand))
    (HERE / "extract_record.json").write_text(
        json.dumps(RECORD, indent=1, sort_keys=True), encoding="utf-8")
    print("wrote extract_record.json with", len(RECORD), "entries")


if __name__ == "__main__":
    main()
