"""Baseline snapshot manifest — sha256 of every frozen baseline file.

Law: byte-identical copies; originals under .tmp/ and agent_logs/ stay untouched.
This snapshot is the canonical input revision for every audit in this campaign.
Stdlib only. Usage: python make_manifest.py [git_head_rev]
"""
import hashlib
import json
import os
import sys
import time

PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAP = os.path.join(PKG, "baseline_snapshot")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def collect() -> dict:
    files = {}
    for dirpath, dirnames, filenames in os.walk(SNAP):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        for fn in sorted(filenames):
            if fn == "MANIFEST.json":
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, SNAP).replace("\\", "/")
            st = os.stat(p)
            files[rel] = {
                "sha256": sha256(p),
                "bytes": st.st_size,
                "mtime": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(st.st_mtime)),
            }
    return files


def crosscheck(files: dict) -> dict:
    """Compare snapshot bytes against hashes declared by the session-5 artifacts."""
    admission = json.load(open(os.path.join(SNAP, "runs", "admission_actual_monkey.json"), encoding="utf-8"))
    meta = admission.get("meta", {})
    candidates = json.load(open(os.path.join(SNAP, "runs", "attachment_candidates.json"), encoding="utf-8"))
    declared_fit = None
    for key in ("provenance_hashes", "provenance", "meta"):
        block = candidates.get(key)
        if isinstance(block, dict):
            for name, value in block.items():
                if "fitted_packet" in name and isinstance(value, str) and len(value) == 64:
                    declared_fit = value
                    break
        if declared_fit:
            break

    def cmp(label, expected, actual):
        if expected is None or actual is None:
            return {"expected": expected, "actual": actual, "match": None}
        return {"expected": expected.lower(), "actual": actual.lower(),
                "match": expected.lower() == actual.lower()}

    fit_json = files.get("runs/actual_monkey_fit.json", {}).get("sha256")
    cand_json = files.get("runs/attachment_candidates.json", {}).get("sha256")
    checks = {
        "chimanoid.xml == admission.meta.source_sha256 (675e00d0..)": cmp(
            "xml", meta.get("source_sha256"), files.get("source_xml/chimanoid.xml", {}).get("sha256")),
        "monkey_birth.bin == admission.meta.target_mesh_sha256": cmp(
            "mesh", meta.get("target_mesh_sha256"), files.get("inputs/monkey_birth.bin", {}).get("sha256")),
        "monkey_joints.bin == admission.meta.target_pack_sha256": cmp(
            "pack", meta.get("target_pack_sha256"), files.get("inputs/monkey_joints.bin", {}).get("sha256")),
        "H-1 fitted_packet_sha256 declared in candidates packet": {
            "declared_value": declared_fit,
            "sha256_of_runs/actual_monkey_fit.json": fit_json,
            "sha256_of_runs/attachment_candidates.json": cand_json,
            "names_fit_packet": declared_fit is not None and declared_fit.lower() == fit_json,
            "names_candidates_packet": declared_fit is not None and declared_fit.lower() == cand_json,
            "names_neither": declared_fit is not None and declared_fit.lower() not in (fit_json, cand_json),
        },
    }
    return checks


def main() -> None:
    files = collect()
    manifest = {
        "campaign": "forearm anatomy package - grasp qualification (monkey)",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_head_at_snapshot": sys.argv[1] if len(sys.argv) > 1 else None,
        "law": "byte-identical copies of frozen originals; originals untouched; this snapshot is the canonical audit input revision",
        "originals": [
            ".tmp/anatomy_compiler/ (code + runs, gitignored)",
            ".tmp/chimanoid.xml (gitignored)",
            "agent_logs/bigpickle/anatomy_compiler_01..05.md (gitignored)",
            "Saved/meshes/monkey_birth.bin, Saved/meshes/monkey_joints.bin",
        ],
        "crosscheck_against_session5_declarations": crosscheck(files),
        "files": files,
    }
    out = os.path.join(SNAP, "MANIFEST.json")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"manifest written: {out} ({len(files)} files)")
    print(json.dumps(manifest["crosscheck_against_session5_declarations"], indent=2))


if __name__ == "__main__":
    main()
