"""B4 three-layer hash matrix: raw disk bytes vs git blob bytes vs canonical text.

Frozen prereg: work/prereg.md sha256 5e0226330ffcf07ea7fbde497232e9c7cddd281eb3f53fd39593dfd69566283e
Run law: PYTHONDONTWRITEBYTECODE=1, writes confined to agents/B4_crosscheckout/.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

B4 = Path(r"E:/ChimeraWork/mvc-20260924/material_volume_campaign/agents/B4_crosscheckout")
REPO = Path(r"E:/ChimeraWork/mvc-20260924")
ARCHIVE_TOOLS = B4 / "work" / "archive_extract" / "tools"
RECEIPTS = B4 / "receipts"

sys.path.insert(0, str(ARCHIVE_TOOLS))
import material_volume_body_export as exporter  # noqa: E402  (HEAD bytes, from git archive)

TARGETS = (
    [f"tools/{n}" for n in [
        "material_volume.py",
        "material_volume_admission.py",
        "material_volume_admission_checks.py",
        "material_volume_body_export.py",
        "material_volume_body_export_checks.py",
        "material_volume_body_export_reader.py",
        "material_volume_checks.py",
        "material_volume_export_proof_prereg_derivation.py",
        "material_volume_export_proof_verify.py",
        "material_volume_frame_composition_proof.py",
        "material_volume_shared_interface_proof.py",
    ]]
    + [f"tools/{n}" for n in [
        "material_volume_admission_manifest_example.json",
        "material_volume_admission_partition_example.json",
        "material_volume_admission_schema.json",
        "material_volume_body_export_example_report.json",
        "material_volume_body_export_groups_example.json",
        "material_volume_body_export_manifest_example.json",
        "material_volume_body_export_partition_example.json",
        "material_volume_body_export_schema.json",
        "material_volume_example.json",
        "material_volume_frame_composition_groups_composed_example.json",
        "material_volume_frame_composition_groups_shared_example.json",
        "material_volume_frame_composition_manifest_example.json",
        "material_volume_frame_composition_partition_example.json",
        "material_volume_shared_interface_groups_example.json",
        "material_volume_shared_interface_manifest_example.json",
        "material_volume_shared_interface_partition_example.json",
    ]]
    + [f"Chimera/docs/matter/{n}" for n in [
        "material_volume_admission.md",
        "material_volume_body_export.md",
        "material_volume_compiler.md",
        "material_volume_export_proof_prereg_frame_composition.md",
        "material_volume_export_proof_prereg_shared_interface.md",
        "material_volume_export_proof_results.md",
        "material_volume_export_verification_prereg.md",
        "material_volume_export_verification_receipt.md",
        "matter_library.json",
        "rigid_body_mass_export_consumption_contract_v1_proposal.md",
    ]]
)

CLASS_R = {"tools/material_volume_body_export_example_report.json"}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def census(b: bytes) -> dict:
    crlf = b.count(b"\r\n")
    lf = b.count(b"\n")
    cr = b.count(b"\r")
    return {
        "bytes": len(b),
        "sha256": sha(b),
        "crlf": crlf,
        "lf_total": lf,
        "cr_total": cr,
        "bare_lf": lf - crlf,
        "bare_cr": cr - crlf,
        "bom": b.startswith(b"\xef\xbb\xbf"),
        "non_ascii": any(x > 127 for x in b[:1_000_000]) or len(b) > 1_000_000 and any(x > 127 for x in b),
    }


def lf_normalize(b: bytes) -> bytes:
    return b.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def git(*args: str) -> bytes:
    out = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, check=True)
    return out.stdout


def git_text(*args: str) -> str:
    return git(*args).decode("utf-8")


def parse_via_exporter(blob: bytes, tag: str):
    """Parse bytes with the exporter's own loader (duplicate-key/NaN rejecting)."""
    tmp = B4 / "work" / "run_tmp" / f"parse_{tag}.json"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_bytes(blob)
    try:
        return exporter.read_json_file(str(tmp)), None
    except exporter.ExportInputError as error:
        return None, f"{error.reason}: {error.detail}"


REV = sys.argv[1] if len(sys.argv) > 1 else "HEAD"

rows = []
for path in TARGETS:
    disk_bytes = (REPO / path).read_bytes()
    blob_bytes = git("cat-file", "blob", f"{REV}:{path}")
    blob_oid = git_text("rev-parse", f"{REV}:{path}").strip()
    extract_bytes = (B4 / "work" / "archive_extract" / path).read_bytes()
    disk, blob = census(disk_bytes), census(blob_bytes)
    lfd = lf_normalize(disk_bytes)
    row = {
        "path": path,
        "json": path.endswith(".json"),
        "file_class": "R" if path in CLASS_R else ("I" if path.endswith(".json") else "T"),
        "disk": disk,
        "blob": blob,
        "blob_oid": blob_oid,
        "blob_eq_disk": disk_bytes == blob_bytes,
        "blob_eq_lf_disk": blob_bytes == lfd,
        "extract_eq_blob": extract_bytes == blob_bytes,
    }
    if row["json"]:
        parsed_blob, err_blob = parse_via_exporter(blob_bytes, "blob")
        parsed_disk, err_disk = parse_via_exporter(disk_bytes, "disk")
        if err_blob or err_disk:
            row["canon_of_blob_sha"] = None
            row["blob_eq_canon"] = None
            row["disk_eq_canon"] = None
            row["parse_equal"] = None
            row["parse_errors"] = [e for e in (err_blob, err_disk) if e]
        else:
            canon_blob = exporter.canonical_json(parsed_blob).encode("ascii")
            canon_disk = exporter.canonical_json(parsed_disk).encode("ascii")
            row["canon_of_blob_sha"] = sha(canon_blob)
            row["canon_of_disk_sha"] = sha(canon_disk)
            row["canon_of_blob"] = census(canon_blob)
            row["blob_eq_canon"] = blob_bytes == canon_blob
            row["disk_eq_canon"] = disk_bytes == canon_disk
            row["lf_disk_eq_canon"] = lfd == canon_blob
            row["parse_equal"] = parsed_blob == parsed_disk
            row["parse_errors"] = []
    rows.append(row)

(RECEIPTS / "01_hash_matrix.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")

# Corroborating receipts bound to the same HEAD.
(RECEIPTS / "02_eol_lsfiles.txt").write_text(
    git_text("ls-files", "--eol", "--", *TARGETS), encoding="utf-8")
(RECEIPTS / "03_check_attr.txt").write_text(
    git_text("check-attr", "text", "eol", "--", *TARGETS), encoding="utf-8")
(RECEIPTS / "04_blob_oids.txt").write_text(
    git_text("ls-tree", REV, "--", *TARGETS), encoding="utf-8")

# Console digest for the run log.
surprises = []
for r in rows:
    if not r["blob"]["cr_total"] == 0:
        surprises.append(("BLOB_HAS_CR", r["path"], r["blob"]["cr_total"]))
    if not r["blob_eq_lf_disk"]:
        surprises.append(("BLOB_NE_LF_DISK", r["path"]))
    if r["blob_eq_disk"]:
        surprises.append(("DISK_EQ_BLOB", r["path"]))
    if not r["extract_eq_blob"]:
        surprises.append(("EXTRACT_NE_BLOB", r["path"]))
    if r["json"] and r.get("blob_eq_canon") is False:
        surprises.append(("BLOB_NE_CANON", r["path"], r["file_class"]))
    if r["json"] and r.get("parse_equal") is False:
        surprises.append(("PARSE_DRIFT", r["path"]))
    if r["json"] and r.get("parse_errors"):
        surprises.append(("PARSE_ERROR", r["path"], r["parse_errors"]))
print(json.dumps({
    "rev_pinned": REV,
    "head_at_matrix_time": git_text("rev-parse", "HEAD").strip(),
    "n_files": len(rows),
    "n_disk_eq_blob": sum(1 for r in rows if r["blob_eq_disk"]),
    "n_blob_eq_lf_disk": sum(1 for r in rows if r["blob_eq_lf_disk"]),
    "n_blob_cr_free": sum(1 for r in rows if r["blob"]["cr_total"] == 0),
    "n_extract_eq_blob": sum(1 for r in rows if r["extract_eq_blob"]),
    "n_json": sum(1 for r in rows if r["json"]),
    "n_blob_eq_canon": sum(1 for r in rows if r.get("blob_eq_canon")),
    "n_parse_equal": sum(1 for r in rows if r.get("parse_equal")),
    "surprises": surprises,
}, indent=1))
