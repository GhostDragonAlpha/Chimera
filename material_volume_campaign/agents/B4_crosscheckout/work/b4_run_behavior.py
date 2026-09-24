"""B4 run-behavior reproducibility: same commit, three materializations, same interpreter.

Preregistered arms (P4): WT (worktree files) vs ARC (git archive extract of pinned rev).
Addendum arm (post-prereg, labeled in receipt): BLB (blob bytes materialized via git cat-file).
Each arm x CLI is run twice to expose intra-arm nondeterminism.
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

B4 = Path(r"E:/ChimeraWork/mvc-20260924/material_volume_campaign/agents/B4_crosscheckout")
REPO = Path(r"E:/ChimeraWork/mvc-20260924")
REV = "81ff947504c2eb9809e5381c614d9aa28ba57ea1"
ARC = B4 / "work" / "archive_extract"
BLB = B4 / "work" / "blob_extract"
RECEIPTS = B4 / "receipts"

sys.path.insert(0, str(ARC / "tools"))
import material_volume_body_export as exporter  # noqa: E402


def materialize_blob_form() -> int:
    """Materialize blob (LF) bytes for the whole tools/ tree at REV."""
    n = 0
    listing = subprocess.run(
        ["git", "-C", str(REPO), "ls-tree", "-r", REV, "--", "tools"],
        capture_output=True, check=True).stdout.decode("utf-8")
    for line in listing.splitlines():
        meta, path = line.split("\t", 1)
        _mode, otype, oid = meta.split()
        if otype != "blob":
            continue
        dest = BLB / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = subprocess.run(["git", "-C", str(REPO), "cat-file", "blob", oid],
                              capture_output=True, check=True).stdout
        dest.write_bytes(data)
        n += 1
    return n


if not (BLB / "tools" / "material_volume.py").exists():
    print("materializing blob-form extract:", materialize_blob_form(), "files")

ARMS = {"WT": REPO, "ARC": ARC, "BLB": BLB}
CLIS = [
    ("material_volume.py", ["tools/material_volume_example.json"]),
    ("material_volume_admission.py", ["--manifest", "tools/material_volume_admission_manifest_example.json",
                                      "--partition", "tools/material_volume_admission_partition_example.json"]),
    ("material_volume_body_export.py", ["--manifest", "tools/material_volume_body_export_manifest_example.json",
                                        "--partition", "tools/material_volume_body_export_partition_example.json",
                                        "--groups", "tools/material_volume_body_export_groups_example.json"]),
    ("material_volume_body_export_reader.py", ["tools/material_volume_body_export_example_report.json"]),
]

env = dict(os.environ)
env["PYTHONDONTWRITEBYTECODE"] = "1"

results = []
for cli, args in CLIS:
    for arm, root in ARMS.items():
        script = root / "tools" / cli
        abs_args = [str(root / a) if a.startswith("tools/") else a for a in args]
        for rep in (1, 2):
            proc = subprocess.run([sys.executable, str(script), *abs_args],
                                  capture_output=True, env=env, cwd=str(root))
            out = proc.stdout
            lf_out = out.replace(b"\r\n", b"\n")
            tmp = B4 / "work" / "run_tmp" / f"stdout_{cli.replace('.', '_')}_{arm}_{rep}.json"
            tmp.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_bytes(lf_out)
            try:
                parsed = exporter.read_json_file(str(tmp))
                canon = exporter.canonical_json(parsed).encode("ascii")
                lf_eq_canon = lf_out == canon
                parse_err = None
            except exporter.ExportInputError as error:
                lf_eq_canon = None
                parse_err = f"{error.reason}: {error.detail}"
            results.append({
                "cli": cli, "arm": arm, "rep": rep,
                "returncode": proc.returncode,
                "stdout_sha256": hashlib.sha256(out).hexdigest(),
                "stdout_lf_sha256": hashlib.sha256(lf_out).hexdigest(),
                "stdout_bytes": len(out),
                "stdout_crlf": out.count(b"\r\n"),
                "lf_out_eq_canon_of_parsed": lf_eq_canon,
                "stderr_bytes": len(proc.stderr),
                "stderr_head": proc.stderr[:120].decode("utf-8", "replace"),
                "parse_err": parse_err,
            })

(RECEIPTS / "06_run_behavior.json").write_text(json.dumps(results, indent=1), encoding="utf-8")

# Cross-arm comparison of LF-form stdout (the platform-independent form).
summary = {}
for cli, _ in CLIS:
    arms = {}
    for r in results:
        if r["cli"] == cli:
            arms.setdefault(r["arm"], set()).add(r["stdout_lf_sha256"])
    lf_hashes = {h for hs in arms.values() for h in hs}
    raw_hashes = {r["stdout_sha256"] for r in results if r["cli"] == cli}
    summary[cli] = {
        "arms": {a: sorted(hs)[0][:16] for a, hs in arms.items()},
        "lf_identical_across_arms_and_reps": len(lf_hashes) == 1,
        "raw_identical_across_arms_and_reps": len(raw_hashes) == 1,
        "n_raw_forms": len(raw_hashes),
        "n_lf_forms": len(lf_hashes),
    }
print(json.dumps(summary, indent=1))
