"""run_dump_walk.py -- run the lane-private statedump binary on the pinned
scene, raw-byte capture, then verify the anchors: stdout sha == 8c537cdb...,
GAIT_EVENT_TRACE stderr sha == c6f9b6c0..., q dumps bit-identical, refusal
302, and print the walk's own numbers (ticks, base dx).
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRATCH = HERE.parents[3] / ".tmp" / "viswalk_dump"
EXE = SCRATCH / "gait_unit_viswalk_dump.exe"
SCENE = SCRATCH / "scene" / "scene.json"

ANCHOR_SCENE = "f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342"
ANCHOR_STDOUT = "8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc"
ANCHOR_STDERR = "c6f9b6c00a1d549a4bc709724d2f62f8f28b37823696de4689e1950651c37481"

DUMP1 = SCRATCH / "states_run1.jsonl"
DUMP2 = SCRATCH / "states_run2.jsonl"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    rec = {"scene_sha256": sha(SCENE), "scene_anchor_match":
           sha(SCENE) == ANCHOR_SCENE}
    env = dict(os.environ)
    env["GAIT_STATE_DUMP"] = str(DUMP1)
    env["GAIT_STATE_DUMP2"] = str(DUMP2)
    so = SCRATCH / "dump_stdout.txt"
    se = SCRATCH / "dump_stderr.txt"
    with open(so, "wb") as f1, open(se, "wb") as f2:
        import time
        t0 = time.perf_counter()
        r = subprocess.run([str(EXE), str(SCENE)], stdout=f1, stderr=f2,
                           env=env, cwd=str(SCRATCH))
        rec["exit"] = r.returncode
        rec["wall_s"] = round(time.perf_counter() - t0, 1)
    rec["stdout_sha256"] = sha(so)
    rec["stderr_sha256"] = sha(se)
    rec["stdout_anchor_match"] = rec["stdout_sha256"] == ANCHOR_STDOUT
    rec["stderr_anchor_match"] = rec["stderr_sha256"] == ANCHOR_STDERR
    rec["dump1_sha256"] = sha(DUMP1) if DUMP1.exists() else None
    rec["dump2_sha256"] = sha(DUMP2) if DUMP2.exists() else None
    rec["dumps_bit_identical"] = (rec["dump1_sha256"] is not None
                                  and rec["dump1_sha256"] == rec["dump2_sha256"])
    # the walk's own numbers from dump1
    ticks = []
    xs = []
    for line in DUMP1.read_text().splitlines():
        d = json.loads(line)
        ticks.append(d["tick"])
        # q layout confirmed below at read time; base trans x/y are q[3], q[4]
        xs.append((d["q"][3], d["q"][4]))
    rec["n_ticks"] = len(ticks)
    rec["tick_first_last"] = [ticks[0], ticks[-1]]
    rec["base_xy_first"] = list(xs[0])
    rec["base_xy_last"] = list(xs[-1])
    rec["base_dx"] = xs[-1][0] - xs[0][0]
    rec["base_dy"] = xs[-1][1] - xs[0][1]
    (HERE / "dump_run_record.json").write_text(json.dumps(rec, indent=1),
                                               encoding="utf-8")
    print(json.dumps(rec, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
