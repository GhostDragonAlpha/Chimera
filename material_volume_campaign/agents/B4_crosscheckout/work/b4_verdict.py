"""B4 verdict matrix: deterministic classification of every layer comparison per the frozen rubric."""
import csv
import hashlib
import json
from pathlib import Path

B4 = Path(r"E:/ChimeraWork/mvc-20260924/material_volume_campaign/agents/B4_crosscheckout")
REPO = Path(r"E:/ChimeraWork/mvc-20260924")
rows = json.loads((B4 / "receipts" / "01_hash_matrix.json").read_text(encoding="utf-8"))

RULE_DISK_VS_BLOB = ('.gitattributes "* text=auto" + repo-local core.autocrlf=true: clean filter '
                     "stores LF blobs; smudge materializes CRLF working copies (M-1a rule)")
RULE_ARCHIVE = ('git archive applies the checkout EOL conversion ("* text=auto"): archive extract is '
                "the SMUDGED (CRLF) form, equal to disk bytes, not to blob bytes")
RULE_CANON_R = ("C-1: saved-example serialization regenerated as canonical CLI bytes "
                "(example report is CLASS R: canonical REQUIRED)")
RULE_STDOUT = ("CPython text-mode sys.stdout (newline=None) translates \\n to os.linesep on win32 "
               "when captured")

out_rows = []
counts = {"EXPECTED": 0, "UNEXPECTED": 0, "UNPROMISED": 0}
extract_eq_disk_all = True
for r in rows:
    path = r["path"]
    ext_bytes = (B4 / "work" / "archive_extract" / path).read_bytes()
    ext_eq_disk = hashlib.sha256(ext_bytes).hexdigest() == r["disk"]["sha256"]
    extract_eq_disk_all &= ext_eq_disk

    def add(comparison, result, verdict, rule):
        counts[verdict] += 1
        out_rows.append({"path": path, "file_class": r["file_class"], "comparison": comparison,
                         "result": result, "verdict": verdict, "rule": rule})

    # Layer (a) vs (b): disk bytes vs git blob bytes.
    if r["blob_eq_disk"]:
        add("disk_vs_blob", "EQUAL (unexpected under text=auto+autocrlf)", "UNEXPECTED", RULE_DISK_VS_BLOB)
    else:
        add("disk_vs_blob", "DIFFER", "EXPECTED", RULE_DISK_VS_BLOB)
    # Falsifier F1: blob must equal LF-normalization of disk.
    if r["blob_eq_lf_disk"]:
        add("blob_vs_LF(disk)", "EQUAL (F1 clean)", "EXPECTED", RULE_DISK_VS_BLOB)
    else:
        add("blob_vs_LF(disk)", "DIFFER", "UNEXPECTED", "F1 FIRED: clean-filter contract broken")
    # Archive extract layer (operational note on the brief's materialization method).
    if ext_eq_disk:
        add("archive_extract_vs_disk", "EQUAL", "EXPECTED", RULE_ARCHIVE)
    else:
        add("archive_extract_vs_disk", "DIFFER", "UNEXPECTED", "F1-class: archive smudge anomaly")
    if not r["extract_eq_blob"]:
        add("archive_extract_vs_blob", "DIFFER", "EXPECTED", RULE_ARCHIVE)

    # Layer (c) for JSON files.
    if r["json"]:
        if r.get("parse_errors"):
            add("parse(blob)/parse(disk)", "PARSE ERROR", "UNEXPECTED", "F4-class: exporter loader rejected a layer")
        elif r.get("parse_equal") is False:
            add("parse(blob)_vs_parse(disk)", "CONTENT DRIFT", "UNEXPECTED", "F4 FIRED: layers disagree beyond whitespace")
        else:
            add("parse(blob)_vs_parse(disk)", "EQUAL", "EXPECTED", "JSON parse is EOL-insensitive; layers hold one content")
        if r.get("blob_eq_canon"):
            add("blob_vs_canonical", "EQUAL", "EXPECTED", RULE_CANON_R if r["file_class"] == "R"
                else "byte-canonical authoring (no rule needed; equality recorded)")
        elif r["file_class"] == "R":
            add("blob_vs_canonical", "DIFFER", "UNEXPECTED", "F2 FIRED: saved report not canonical (defeats C-1)")
        else:
            add("blob_vs_canonical", "DIFFER", "UNPROMISED",
                "no rule promises canonical bytes for input/schema/library JSON (C-1 scope = saved REPORT only); "
                "decision request: canonize or declare pretty-form as the artifact contract")

with (B4 / "receipts" / "07_verdict_matrix.csv").open("w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=["path", "file_class", "comparison", "result", "verdict", "rule"])
    writer.writeheader()
    writer.writerows(out_rows)

print(json.dumps({"extract_eq_disk_all_37": extract_eq_disk_all, "verdict_counts": counts,
                  "n_rows": len(out_rows),
                  "files": len(rows),
                  "unexpected_rows": [o for o in out_rows if o["verdict"] == "UNEXPECTED"]}, indent=1))
