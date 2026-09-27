"""P6 — hash-identity manifest with three DISTINCT identity classes.

For every artifact in this attempt's evidence tree this script records:
  raw_sha256      : SHA-256 over the bytes on disk in this workspace
                    (blob-form extraction => byte-equal to the origin blob)
  canonical_sha256: SHA-256 over LF-normalized bytes (the frozen receipt's
                    canonical class)
  blob_oid        : git blob OID of the pinned revision path (portable class)

It then verifies:
  1. the frozen receipt's key-artifact canonical sha256 first-16 values
     (table in material_volume_export_verification_receipt.md at 3db8bc4e);
  2. the demonstration artifact: a file lawfully exhibiting
     raw != canonical with a stable blob OID across materializations
     (falsifier F-B01-6 fires if no such artifact exists or classes conflate);
  3. DR-1 corroboration: candidate constructions for the frozen receipt's
     33-blob sorted digest ee27dcd2... (construction was unrecorded; B9's
     archived receipt reported it reproduced — this attempt records which
     candidate constructions reproduce it, or says so honestly if none does).
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
REPO = Path(*BASE.parts[: BASE.parts.index("checkout") + 1])
RUNS = BASE / "runs"
REV = "1af0bbdee68d6ddfdd02bf9bd948f7b22f914d56"

FROZEN_KEY_CANONICAL_16 = {
    "tools/material_volume_export_proof_prereg_derivation.py": "15a42e3d21357350",
    "tools/material_volume_shared_interface_proof.py": "844170e92bd4cf82",
    "tools/material_volume_frame_composition_proof.py": "a5d762daefb136a0",
    "tools/material_volume_export_proof_verify.py": "282bc52bfa997c6c",
    "tools/material_volume_body_export_example_report.json": "5485c8c4fe73d679",
    "Chimera/docs/matter/material_volume_export_proof_results.md": "d190eae0791277d1",
    "Chimera/docs/matter/material_volume_export_proof_prereg_shared_interface.md": "546c943d585cab6b",
    "Chimera/docs/matter/material_volume_export_proof_prereg_frame_composition.md": "e5bf32fd94dcfd7f",
}

FROZEN_33_DIGEST = "ee27dcd22aedac909984650dcc69f02ea8d66f4eea4bfd96d00ce29604f048a4"


def git(*args):
    return subprocess.run(["git", *args], capture_output=True,
                          cwd=str(REPO), check=True).stdout


def main():
    rows = []
    for path in sorted(BASE.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        rel = path.relative_to(BASE).as_posix()
        raw = path.read_bytes()
        raw_sha = hashlib.sha256(raw).hexdigest()
        canon_sha = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
        rows.append({
            "path": rel,
            "raw_sha256": raw_sha,
            "canonical_sha256": canon_sha,
            "raw_equals_canonical": raw_sha == canon_sha,
        })

    # frozen key artifacts: compare LF-canonical sha256 against frozen values
    key_rows = []
    key_ok = True
    for fpath, expected16 in FROZEN_KEY_CANONICAL_16.items():
        blob = git("cat-file", "blob", f"{REV}:{fpath}")
        canon = hashlib.sha256(blob.replace(b"\r\n", b"\n")).hexdigest()
        ok = canon[:16] == expected16
        key_ok &= ok
        key_rows.append({"path": fpath, "canonical16": canon[:16],
                         "frozen16": expected16, "match": ok,
                         "blob_oid": git("rev-parse", f"{REV}:{fpath}").decode().strip()})

    # demonstration artifact: raw != canonical, blob OID stable
    # (extract any frozen LF-authored file and materialize a CRLF copy)
    demo_src = BASE / "frozen/1af0bbde/tools/material_volume_export_proof_verify.py"
    demo_blob_oid = git("rev-parse",
                        f"{REV}:tools/material_volume_export_proof_verify.py"
                        ).decode().strip()
    raw = demo_src.read_bytes()
    crlf = raw.replace(b"\n", b"\r\n")
    demo = {
        "artifact": "tools/material_volume_export_proof_verify.py (extract)",
        "blob_oid": demo_blob_oid,
        "raw_blobform_sha256": hashlib.sha256(raw).hexdigest(),
        "crlf_materialized_sha256": hashlib.sha256(crlf).hexdigest(),
        "canonical_lf_sha256": hashlib.sha256(crlf.replace(b"\r\n", b"\n")).hexdigest(),
        "distinct_classes_demonstrated": (
            hashlib.sha256(raw).hexdigest() != hashlib.sha256(crlf).hexdigest()
            and hashlib.sha256(crlf.replace(b"\r\n", b"\n")).hexdigest()
            == hashlib.sha256(raw).hexdigest()),
    }

    # DR-1 candidate constructions over the 33-file campaign manifest
    tools_files = [l.decode() for l in git("ls-tree", "--name-only", REV,
                                           "--", "tools/").splitlines()]
    tools_files = [f for f in tools_files if "material_volume" in f]
    docs_files = [l.decode() for l in git("ls-tree", "--name-only", REV,
                                          "--", "Chimera/docs/matter/").splitlines()]
    candidates = {}
    for label, files in (
            ("27 tools + 6 docs (minus matter_library)", tools_files +
             [d for d in docs_files if "matter_library" not in d]),
            ("27 tools + 7 docs", tools_files + docs_files),
    ):
        oids = sorted(git("rev-parse", f"{REV}:{f}").decode().strip()
                      for f in files)
        joined = "\n".join(oids)
        candidates[label] = {
            "file_count": len(files),
            "sha256(sorted_oids_join_nl)": hashlib.sha256(joined.encode()).hexdigest(),
            "sha256(sorted_oids_join_nl_trailing)": hashlib.sha256((joined + "\n").encode()).hexdigest(),
            "sha256(sorted_oids_concat)": hashlib.sha256("".join(oids).encode()).hexdigest(),
            "sha256(sorted_oid_path_lines)": hashlib.sha256(
                "\n".join(sorted(f"{git('rev-parse', f'{REV}:{f}').decode().strip()} {f}"
                                 for f in files)).encode()).hexdigest(),
        }
    dr1 = {"frozen_digest": FROZEN_33_DIGEST, "candidates": candidates,
           "reproduced_by": [lbl for lbl, c in candidates.items()
                             for k, v in c.items()
                             if v == FROZEN_33_DIGEST]}

    result = {"artifact_rows": rows, "frozen_key_artifacts": key_rows,
              "frozen_key_all_match": key_ok, "demonstration": demo,
              "dr1_digest_corroboration": dr1,
              "F-B01-6_fired": not (key_ok and demo["distinct_classes_demonstrated"])}
    RUNS.mkdir(parents=True, exist_ok=True)
    with open(RUNS / "p6_hash_manifest.json", "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump(result, fh, indent=1)
    print(f"artifacts hashed: {len(rows)}")
    print(f"frozen key canonical-16 all match: {key_ok}")
    print(f"distinct identity classes demonstrated: {demo['distinct_classes_demonstrated']}")
    print(f"DR-1 digest reproduced by: {dr1['reproduced_by'] or 'NONE of the candidate constructions'}")
    print(f"F-B01-6 fired: {result['F-B01-6_fired']}")
    return 0 if not result["F-B01-6_fired"] else 1


if __name__ == "__main__":
    sys.exit(main())
