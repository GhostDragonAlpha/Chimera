"""W1 pinned-runner: ALL identity computation happens here, inside the pinned
exporter revision's own code. The W1 driver never hashes, never recomputes
admission, and never regenerates with anything but this runner's result.

Executed as a subprocess:

    python pinned_runner.py <pinned_tools_dir> <manifest> <partition> \\
        <groups> <delivered_report>

The runner replicates the exporter CLI's exact production pipeline
(tools/material_volume_body_export.py::main):
    read_json_file -> build_export_report -> canonical_json
using the modules imported from <pinned_tools_dir> (sys.path precedence), so
"regeneration" is literally the pinned producer's own code path. It also
recomputes `exporter._hashes(manifest, partition, groups)` (the exporter's OWN
input-hash definition) and `build_admission_report` + `exporter._canonical_hash`
(the definition the exporter embeds in `admission_report_sha256`).

Output: exactly one JSON object on stdout (ASCII). Identity hashes are computed
ONLY by the pinned exporter's functions — the runner reimplements no hashing
except plain byte digests explicitly labeled as materialized-file receipts
(non-portable, B4 layer 1), which are never used for any verdict.

Structured outcomes: status in {"ok", "source_unusable", "delivered_unparseable",
"producer_error"}. Unexpected exceptions exit 3 with a traceback on stderr (the
driver maps that to PRODUCER-ERROR as well).
"""
from __future__ import annotations

import hashlib
import json
import sys
import traceback
from pathlib import Path


def _materialized_digest(path: str) -> dict:
    data = Path(path).read_bytes()
    return {"path": path,
            "materialized_bytes_sha256": hashlib.sha256(data).hexdigest(),
            "materialized_bytes": len(data),
            "note": "checkout/disk materialization receipt (B4 layer 1); "
                    "NOT a portable identity and NEVER used for a verdict"}


def main(argv: list[str]) -> int:
    pinned_tools_dir, manifest_path, partition_path, groups_path, report_path = argv
    sys.path.insert(0, str(pinned_tools_dir))
    import material_volume_body_export as exporter
    import material_volume_admission as admission  # resolves to the pinned copy

    result = {"status": "ok",
              "pinned_tools_dir": str(pinned_tools_dir),
              "source_materialized_receipts": [
                  _materialized_digest(p)
                  for p in (manifest_path, partition_path, groups_path, report_path)]}

    try:
        manifest = exporter.read_json_file(manifest_path)
        partition = exporter.read_json_file(partition_path)
        groups = exporter.read_json_file(groups_path)
    except exporter.ExportInputError as error:
        result["status"] = "source_unusable"
        result["reason"] = error.reason
        result["detail"] = error.detail
        _emit(result)
        return 0

    # The exporter's OWN canonical input-hash definition (no reimplementation).
    input_hashes = exporter._hashes(manifest, partition, groups)
    # The exporter's OWN admission recomputation + canonical digest definition.
    admission_report = admission.build_admission_report(manifest, partition)
    admission_sha256 = exporter._canonical_hash(admission_report)
    # The pinned producer's regeneration: the CLI's exact pipeline.
    regenerated = exporter.build_export_report(manifest, partition, groups)
    regenerated_canonical = exporter.canonical_json(regenerated)

    try:
        delivered = exporter.read_json_file(report_path)
        delivered_canonical = exporter.canonical_json(delivered)
        delivered_export_status = delivered.get("export_status")
        delivered_admission_status = delivered.get("admission_status")
    except exporter.ExportInputError as error:
        result["delivered_parse_error"] = {"reason": error.reason,
                                           "detail": error.detail}
        delivered_canonical = None
        delivered_export_status = None
        delivered_admission_status = None

    result.update({
        "input_hashes_recomputed": input_hashes,
        "source_canonical_hashes": {
            "manifest_sha256": exporter._canonical_hash(manifest),
            "partition_sha256": exporter._canonical_hash(partition),
            "body_groups_sha256": exporter._canonical_hash(groups),
            "definition": "exporter._canonical_hash: sha256 of UTF-8 canonical "
                          "JSON (sorted object keys; array order preserved)"},
        "admission_report_sha256_recomputed": admission_sha256,
        "admission_decision_recomputed": admission_report.get("decision"),
        "regenerated_canonical_json": regenerated_canonical,
        "regenerated_canonical_sha256":
            hashlib.sha256(regenerated_canonical.encode("ascii")).hexdigest(),
        "regenerated_export_status": regenerated.get("export_status"),
        "regenerated_admission_status": regenerated.get("admission_status"),
        "delivered_canonical_json": delivered_canonical,
        "delivered_canonical_sha256":
            None if delivered_canonical is None
            else hashlib.sha256(delivered_canonical.encode("ascii")).hexdigest(),
        "delivered_export_status": delivered_export_status,
        "delivered_admission_status": delivered_admission_status,
        "producer": "pinned revision modules imported from the byte-verified "
                    "blob materialization (git blob bytes, B4 layer 2)",
    })
    _emit(result)
    return 0


def _emit(result: dict) -> None:
    sys.stdout.write(json.dumps(result, sort_keys=True, ensure_ascii=True,
                                allow_nan=False) + "\n")


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001 — any crash is a PRODUCER-ERROR, never a pass
        sys.stdout.write(json.dumps({
            "status": "producer_error",
            "kind": type(sys.exc_info()[1]).__name__,
            "detail": str(sys.exc_info()[1]),
            "traceback_tail": traceback.format_exc()[-2000:]},
            sort_keys=True, ensure_ascii=True) + "\n")
        raise SystemExit(3)
