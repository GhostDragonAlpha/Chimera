"""M05 comparison harness: byte layer + physical layer vs the frozen prereg.

Byte layer: sha256 table + recursive JSON-path diff of parsed stdout reports.
Physical layer: exact float comparison (float.hex) of preregistered fields,
ownership/accounting equality, admission hash invariance, analytic anchors.
Verdicts per prereg.md section 3.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
REC = HERE.parent / "receipts"

RUNS = ["P0a", "P0b", "P1-cells-reversed", "P2-cells-shuffled", "P3-groups-reordered",
        "P4-group-cell-records-reversed", "P5-manifest-entries-reversed"]
PERMS = RUNS[2:]
# Which input_hashes field is ALLOWED to change per permutation (prereg E-BYTE-1..5)
ALLOWED = {
    "P1-cells-reversed": "partition_sha256",
    "P2-cells-shuffled": "partition_sha256",
    "P3-groups-reordered": "body_groups_sha256",
    "P4-group-cell-records-reversed": "body_groups_sha256",
    "P5-manifest-entries-reversed": "manifest_sha256",
}
# Which input document's BYTES actually changed in the fixture (from build step)
CHANGED_INPUT = dict(ALLOWED)


def load(run: str):
    raw = (REC / f"run_{run}.stdout.json").read_bytes()
    return raw, json.loads(raw)


def paths_diff(a, b, path="$"):
    """Recursive diff of parsed JSON; returns list of (path, a_value, b_value)."""
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b)):
            if key not in a or key not in b:
                out.append((f"{path}.{key}", "<absent>" if key not in a else a[key],
                            "<absent>" if key not in b else b[key]))
            else:
                out.extend(paths_diff(a[key], b[key], f"{path}.{key}"))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append((f"{path}[len]", len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            out.extend(paths_diff(x, y, f"{path}[{i}]"))
    else:
        if a != b:
            out.append((path, a, b))
    return out


def hexf(x):
    return float(x).hex()


def physical_extract(report):
    """Preregistered physical + ownership fields, floats as hex for exactness."""
    bodies = {}
    for row in report.get("body_groups", []):
        props = row.get("mass_properties") or {}
        mass = props.get("mass", {})
        vol = props.get("volume", {})
        com = props.get("center_of_mass", {})
        inertia = props.get("inertia_tensor_about_com", {})
        bodies[row.get("body_id")] = {
            "export_status": row.get("export_status"),
            "owned_cell_ids": row.get("owned_cell_ids"),
            "admission_status": row.get("admission_status"),
            "cell_provenance": row.get("cell_provenance"),
            "mass": hexf(mass.get("value")) if mass else None,
            "volume": hexf(vol.get("value")) if vol else None,
            "com": [hexf(v) for v in com.get("value", [])],
            "inertia": [[hexf(v) for v in r] for r in inertia.get("value", [])],
            "admission_report_sha256": row.get("admission_report_sha256"),
        }
    return {"export_status": report.get("export_status"),
            "admission_status": report.get("admission_status"),
            "admission_reason_codes": report.get("admission_reason_codes"),
            "unassigned_cell_ids": report.get("unassigned_cell_ids"),
            "all_supplied_cells_assigned": report.get("all_supplied_cells_assigned"),
            "admission_report_sha256": report.get("admission_report_sha256"),
            "bodies": bodies}


def main() -> int:
    raw = {}
    docs = {}
    for run in RUNS:
        raw[run], docs[run] = load(run)

    print("== BYTE LAYER ==")
    print("| run | stdout sha256 | bytes |")
    print("|---|---|---|")
    for run in RUNS:
        print(f"| {run} | `{hashlib.sha256(raw[run]).hexdigest()}` | {len(raw[run])} |")

    det_ok = raw["P0a"] == raw["P0b"]
    print(f"\nE-BYTE-0 rerun determinism P0a==P0b: {det_ok}")

    for perm in PERMS:
        diff = paths_diff(docs["P0a"], docs[perm])
        allowed = ALLOWED[perm]
        in_hash_paths = [p for p, _, _ in diff
                         if p.startswith("$.input_hashes.") or ".input_hashes." in p]
        outside = [(p, x, y) for p, x, y in diff if p not in in_hash_paths]
        fields_changed = sorted({p.rsplit(".", 1)[-1] for p in in_hash_paths})
        only_allowed = fields_changed == [allowed]
        # the new hash value must equal the sha256 the exporter computes over the
        # permuted fixture document (identity of the exact serialized inputs)
        verdict = "PASS-PROMISED"
        if not diff:
            verdict = "FAIL: no byte change at all (hash did not track input order)"
        elif outside or not only_allowed:
            verdict = "FALSIFIER-HIT: byte change outside the promised hash field"
        print(f"\n{perm}: diff paths = {len(diff)}, changed fields = {fields_changed}, "
              f"allowed = ['{allowed}'] -> {verdict}")
        for p, x, y in diff:
            print(f"  {p}: {str(x)[:20]}.. -> {str(y)[:20]}..")
        if outside:
            for p, x, y in outside:
                print(f"  OUTSIDE-PROMISE {p}: {x!r} -> {y!r}")

    print("\n== PHYSICAL LAYER ==")
    ref = physical_extract(docs["P0a"])
    print("| run | verdict | note |")
    print("|---|---|---|")
    for run in RUNS:
        cur = physical_extract(docs[run])
        if cur == ref:
            print(f"| {run} | PASS-EXACT | all preregistered physical/ownership fields "
                  f"bit-identical to P0a (float.hex equality) |")
            continue
        diffs = paths_diff(ref, cur)
        print(f"| {run} | DIFFERS | {len(diffs)} path(s) |")
        for p, x, y in diffs:
            print(f"    {p}: {x} -> {y}")

    print("\n== ANALYTIC ANCHORS (P0a) ==")
    for body, expect_v, expect_m in (("body-alpha", 0.5, 6.0), ("body-beta", 1 / 3, 2.0),
                                     ("body-gamma", 1 / 6, 3.5 / 6)):
        b = ref["bodies"][body]
        v = float.fromhex(b["volume"])
        m = float.fromhex(b["mass"])
        print(f"{body}: volume={v!r} (expect {expect_v!r}, delta {v - expect_v:+.3e}); "
              f"mass={m!r} (expect {expect_m!r}, delta {m - expect_m:+.3e})")

    adm = {run: docs[run].get("admission_report_sha256") for run in RUNS}
    print(f"\nE-PHYS-3 admission_report_sha256 invariant: {len(set(adm.values())) == 1} "
          f"(distinct values: {len(set(adm.values()))})")

    # input_hashes identity: the changed hash must equal the exporter's own canonical
    # hash of the permuted input document (recomputed here the same way for the receipt)
    import sys
    sys.path.insert(0, str(HERE / "modules"))
    import material_volume_body_export as exporter  # module copy, read-only use
    print("\n== INPUT-HASH IDENTITY CHECK (hash value == canonical hash of permuted doc) ==")
    fix_for = {"P0a": "base", "P0b": "base", **{p: p for p in PERMS}}
    for run in RUNS:
        fixture = fix_for[run]
        manifest = json.loads((HERE.parent / "fixtures" / fixture / "manifest.json")
                              .read_text(encoding="utf-8"))
        partition = json.loads((HERE.parent / "fixtures" / fixture / "partition.json")
                               .read_text(encoding="utf-8"))
        groups = json.loads((HERE.parent / "fixtures" / fixture / "groups.json")
                            .read_text(encoding="utf-8"))
        expect = exporter._hashes(manifest, partition, groups)
        got = docs[run]["input_hashes"]
        ok = all(expect[k] == got[k] for k in
                 ("manifest_sha256", "partition_sha256", "body_groups_sha256"))
        print(f"{run}: input_hashes == canonical hashes of its own fixture triple: {ok}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
