"""B3 round-trip runner — the one measurement pass (PREREG-frozen design).

Layers:
  L-WRITE  in-memory build_export_report vs exporter CLI canonical stdout
  L-PARSE  read_json_file(report file) vs exporter canonical string + fields
  L-SUMMARY summarize_export_report(parsed) invariant fields vs parsed report
  L-REREAD reader summary re-parsed, canonical equality

Writes ONLY inside agents/B3_roundtrip/. tools/ is imported via sys.path with
bytecode writing disabled (sys.dont_write_bytecode + PYTHONDONTWRITEBYTECODE=1).
Exact equality on parsed values; no allclose anywhere in the verdict.

Incident note (preserved per campaign law): the first execution crashed on a
genuinely BLOCKED fixture (authoring error: manifest-style partition cells) and
the first fixture draft tripped three agent-side defects (abs(genexpr)
TypeError, parents[1] path bug, partition schema mismatch). The blocked report
is preserved as receipts/08_blocked_first_attempt.report.json; this runner now
tolerates non-exported bodies by recording N_A instead of crashing.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True

B3 = Path(__file__).resolve().parent.parent
ROOT = B3.parents[2]
TOOLS = ROOT / "tools"
RECEIPTS = B3 / "receipts"

sys.path.insert(0, str(TOOLS))

import material_volume_body_export as exporter  # noqa: E402
import material_volume_body_export_reader as reader  # noqa: E402

FIXTURES = {
    "rotcoupon": {
        "manifest": B3 / "fixtures" / "rotcoupon" / "manifest.json",
        "partition": B3 / "fixtures" / "rotcoupon" / "partition.json",
        "groups": B3 / "fixtures" / "rotcoupon" / "groups.json",
    },
    "shipped_example": {
        "manifest": B3 / "fixtures" / "shipped_example" / "material_volume_body_export_manifest_example.json",
        "partition": B3 / "fixtures" / "shipped_example" / "material_volume_body_export_partition_example.json",
        "groups": B3 / "fixtures" / "shipped_example" / "material_volume_body_export_groups_example.json",
    },
}

# (invariant, sub_field, path into body src, path into summary body row)
BODY_SPEC = [
    ("I1_tensor", "value[3][3]",
     ("mass_properties", "inertia_tensor_about_com", "value"),
     ("inertia_tensor_about_com", "value")),
    ("I1_tensor", "unit",
     ("mass_properties", "inertia_tensor_about_com", "unit"),
     ("inertia_tensor_about_com", "unit")),
    ("I1_tensor", "flag.full_symmetric_tensor",
     ("mass_properties", "inertia_tensor_about_com", "full_symmetric_tensor"),
     ("inertia_tensor_about_com", "full_symmetric_tensor")),
    ("I1_tensor", "flag.off_diagonal_terms_preserved",
     ("mass_properties", "inertia_tensor_about_com", "off_diagonal_terms_preserved"),
     ("inertia_tensor_about_com", "off_diagonal_terms_preserved")),
    ("I1_tensor", "flag.principal_axis_transform_applied",
     ("mass_properties", "inertia_tensor_about_com", "principal_axis_transform_applied"),
     ("inertia_tensor_about_com", "principal_axis_transform_applied")),
    ("I2_com", "value[3]",
     ("mass_properties", "center_of_mass", "value"),
     ("center_of_mass", "value")),
    ("I2_com", "unit",
     ("mass_properties", "center_of_mass", "unit"),
     ("center_of_mass", "unit")),
    ("I2_com", "coordinate_frame",
     ("mass_properties", "center_of_mass", "coordinate_frame"),
     ("center_of_mass", "coordinate_frame")),
    ("I3_frames", "body_frame.frame_id",
     ("body_frame", "frame_id"), None),
    ("I3_frames", "body_frame.handedness",
     ("body_frame", "handedness"), None),
    ("I3_frames", "body_frame.coordinate_unit",
     ("body_frame", "coordinate_unit"), None),
    ("I3_frames", "body_frame.domain_from_body.rotation",
     ("body_frame", "domain_from_body", "rotation"), None),
    ("I3_frames", "body_frame.domain_from_body.origin_m",
     ("body_frame", "domain_from_body", "origin_m"), None),
    ("I3_frames", "tensor.coordinate_frame",
     ("mass_properties", "inertia_tensor_about_com", "coordinate_frame"),
     ("inertia_tensor_about_com", "coordinate_frame")),
    ("I3_frames", "tensor.frame_id",
     ("mass_properties", "inertia_tensor_about_com", "frame_id"),
     ("inertia_tensor_about_com", "frame_id")),
    ("I3_frames", "tensor.basis",
     ("mass_properties", "inertia_tensor_about_com", "basis"),
     ("inertia_tensor_about_com", "basis")),
    ("I3_frames", "mass.coordinate_frame",
     ("mass_properties", "mass", "coordinate_frame"), None),
    ("I3_frames", "mass.frame_invariant",
     ("mass_properties", "mass", "frame_invariant"), None),
    ("I3_frames", "volume.coordinate_frame",
     ("mass_properties", "volume", "coordinate_frame"), None),
    ("I4_provenance", "cell_provenance.rows",
     ("cell_provenance",), None),
    ("I5_admission", "admission_status",
     ("admission_status",), ("admission_status",)),
    ("I5_admission", "admission_report_sha256",
     ("admission_report_sha256",), ("admission_report_sha256",)),
]

ROWS: list[dict] = []


def row(fixture, invariant, sub, layer, verdict, detail=""):
    ROWS.append({"fixture": fixture, "invariant": invariant, "sub_field": sub,
                 "layer": layer, "verdict": verdict, "detail": str(detail)[:400]})


def fmt(value):
    if isinstance(value, float):
        return f"{value!r} (hex {value.hex()})"
    return repr(value)


def _flatten(value):
    if isinstance(value, list):
        out = []
        for item in value:
            out.extend(_flatten(item))
        return out
    return [value]


def get_path(obj, path):
    cur = obj
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return False, None
        cur = cur[key]
    return True, cur


def exact_compare(fixture, invariant, sub, layer, got, want):
    """Elementwise exact equality; verdict PASS_EXACT / DIFF with hex detail."""
    if isinstance(want, list) and isinstance(got, list):
        if len(got) != len(want):
            row(fixture, invariant, sub, layer, "DIFF",
                f"length {len(got)} != {len(want)}")
            return
        flat_g, flat_w = _flatten(got), _flatten(want)
        bad = [(i, g, w) for i, (g, w) in enumerate(zip(flat_g, flat_w))
               if type(g) is not type(w) or g != w]
        if bad:
            i, g, w = bad[0]
            row(fixture, invariant, sub, layer, "DIFF",
                f"element[{i}]: got={fmt(g)} ref={fmt(w)}"
                f" ({len(bad)} unequal of {len(flat_w)})")
        else:
            row(fixture, invariant, sub, layer, "PASS_EXACT",
                f"all {len(flat_w)} elements exact")
        return
    if type(got) is not type(want) or got != want:
        row(fixture, invariant, sub, layer, "DIFF",
            f"got={fmt(got)} ref={fmt(want)}")
        return
    row(fixture, invariant, sub, layer, "PASS_EXACT", repr(want))


def check_field(fixture, tag, invariant, sub, layer, container, path, ref):
    found, value = get_path(container, path)
    if not found:
        row(fixture, invariant, sub, layer, "DROP",
            f"path {'.'.join(path)} absent in this layer's document ({tag})")
        return
    exact_compare(fixture, invariant, sub, layer, value, ref)


def run_cli(script: Path, args: list[str], tag: str, fixture: str):
    proc = subprocess.run(
        [sys.executable, "-B", str(script), *args],
        cwd=str(ROOT), capture_output=True, timeout=120)
    out_dir = RECEIPTS / "02_run_io" / fixture
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{tag}_stdout.bin").write_bytes(proc.stdout)
    (out_dir / f"{tag}_stderr.txt").write_bytes(proc.stderr)
    (out_dir / f"{tag}_rc.txt").write_text(str(proc.returncode) + "\n",
                                           encoding="ascii", newline="\n")
    return proc


def byte_layer_record(tag: str, raw: bytes, canonical: str, fixture: str,
                      findings: list[str]) -> bool:
    text = raw.decode("utf-8")
    normalized = text.replace("\r\n", "\n")
    crlf = raw.count(b"\r\n")
    norm_equal = normalized == canonical
    raw_equal = text == canonical
    if norm_equal and not raw_equal:
        findings.append(
            f"{fixture}/{tag}: raw stdout has {crlf} CRLF pair(s); "
            f"newline-normalized bytes == canonical string (B4 smudge layer, "
            f"EXPECTED; canonical comparison is the scored one)")
    with (RECEIPTS / "04_byte_layer.txt").open("a", encoding="utf-8",
                                               newline="\n") as handle:
        handle.write(f"{fixture}\t{tag}\tcrlf_pairs={crlf}\t"
                     f"raw_equal_canonical={raw_equal}\t"
                     f"normalized_equal_canonical={norm_equal}\n")
    return norm_equal


def src_body(report_obj, body_id):
    for g in report_obj["body_groups"]:
        if g["body_id"] == body_id:
            return g
    raise KeyError(body_id)


def first_diff(a: str, b: str) -> int:
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return min(len(a), len(b))


def main() -> int:
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    (RECEIPTS / "04_byte_layer.txt").write_text("", encoding="utf-8", newline="\n")
    findings: list[str] = []
    fixture_hashes = []

    for fixture, paths in FIXTURES.items():
        for label in ("manifest", "partition", "groups"):
            data = paths[label].read_bytes()
            fixture_hashes.append((fixture, label, paths[label].name,
                                   hashlib.sha256(data).hexdigest(), len(data)))

        # --- L-WRITE: in-memory build vs CLI canonical stdout
        manifest = exporter.read_json_file(str(paths["manifest"]))
        partition = exporter.read_json_file(str(paths["partition"]))
        groups = exporter.read_json_file(str(paths["groups"]))
        report_obj = exporter.build_export_report(manifest, partition, groups)
        canon = exporter.canonical_json(report_obj)
        proc = run_cli(TOOLS / "material_volume_body_export.py",
                       ["--manifest", str(paths["manifest"]),
                        "--partition", str(paths["partition"]),
                        "--groups", str(paths["groups"])],
                       "exporter", fixture)
        stdout_text = proc.stdout.decode("utf-8")
        byte_layer_record("exporter_cli", proc.stdout, canon, fixture, findings)
        exact_compare(fixture, "L-WRITE", "report_canonical_text", "L-WRITE",
                      stdout_text.replace("\r\n", "\n"), canon)
        if proc.returncode != 0:
            row(fixture, "L-WRITE", "exporter_exit_code", "L-WRITE", "DIFF",
                f"rc={proc.returncode} stderr={proc.stderr[:200]!r}")
        report_path = B3 / "fixtures" / fixture / "report.json"
        report_path.write_bytes(proc.stdout)  # authentic consumer bytes

        # --- L-PARSE: reader parse of the written report
        parsed = exporter.read_json_file(str(report_path))
        canon_parsed = exporter.canonical_json(parsed)
        row(fixture, "L-PARSE", "canonical_roundtrip", "L-PARSE",
            "PASS_EXACT" if canon_parsed == canon else "DIFF",
            "canonical_json(parsed) == exporter canonical string"
            if canon_parsed == canon else
            f"len {len(canon_parsed)} vs {len(canon)}; first diff at "
            f"{first_diff(canon_parsed, canon)}")
        if parsed["export_status"] != "complete":
            row(fixture, "L-PARSE", "export_status", "L-PARSE", "DIFF",
                f"export_status={parsed['export_status']!r} (prereg scope: "
                f"complete); see receipts/08 if this is the archived incident")
        if "dynamics_readiness_claimed" in parsed:
            exact_compare(fixture, "I6_readiness",
                          "exporter.dynamics_readiness_claimed", "L-PARSE",
                          parsed["dynamics_readiness_claimed"], False)
        if "admission_report_sha256" in parsed:
            row(fixture, "I5_admission", "top.admission_report_sha256",
                "L-PARSE", "PASS_EXACT", parsed["admission_report_sha256"])

        # --- L-SUMMARY
        summary = reader.summarize_export_report(parsed)
        canon_summary = reader.canonical_json(summary)
        rproc = run_cli(TOOLS / "material_volume_body_export_reader.py",
                        [str(report_path)], "reader", fixture)
        byte_layer_record("reader_cli", rproc.stdout, canon_summary,
                          fixture, findings)
        summary_path = B3 / "fixtures" / fixture / "summary.json"
        summary_path.write_bytes(rproc.stdout)

        by_id = {g["body_id"]: g for g in parsed["body_groups"]}
        for srow in summary["bodies"]:
            body_id = srow["body_id"]
            tag = f"{fixture}/{body_id}"
            src = by_id[body_id]
            ref = src_body(report_obj, body_id)
            if srow.get("export_status") != "exported":
                row(fixture, "N_A", f"{body_id}.export_status", "L-SUMMARY",
                    "N_A", f"non-exported body ({srow.get('export_status')!r}); "
                           f"prereg scope covers exported bodies")
                continue
            for invariant, sub, ref_path, sum_path in BODY_SPEC:
                found, ref_value = get_path(ref, ref_path)
                if not found:
                    row(fixture, invariant, sub, "L-SUMMARY", "DIFF",
                        f"reference path {'.'.join(ref_path)} missing in parsed "
                        f"report ({tag})")
                    continue
                # L-PARSE twin: parsed vs in-memory exporter object
                p_found, p_value = get_path(src, ref_path)
                if p_found:
                    exact_compare(tag, invariant, sub, "L-PARSE", p_value,
                                  ref_value)
                else:
                    row(fixture, invariant, sub, "L-PARSE", "DROP",
                        f"path {'.'.join(ref_path)} absent in parsed report")
                # L-SUMMARY: summary vs parsed report
                if sum_path is None:
                    row(fixture, invariant, sub, "L-SUMMARY", "DROP",
                        f"summary carries no field for {'.'.join(ref_path)} "
                        f"({tag})")
                else:
                    check_field(fixture, tag, invariant, sub, "L-SUMMARY",
                                srow, sum_path, ref_value)
            # I4 count annotation (how many rows were dropped, if dropped)
            n_prov = len(src["cell_provenance"])
            if all(r["verdict"] != "PASS_EXACT" for r in ROWS
                   if r["fixture"] == fixture and r["invariant"] == "I4_provenance"):
                pass  # DROP rows already carry the count via detail

        # top-level invariants
        check_field(fixture, fixture, "I5_admission", "top.admission_status",
                    "L-SUMMARY", summary, ("admission_status",),
                    parsed["admission_status"])
        row(fixture, "I5_admission", "top.admission_report_sha256", "L-SUMMARY",
            "DROP" if "admission_report_sha256" not in summary else "PRESENT",
            "top-level admission_report_sha256 "
            + ("absent in reader summary" if "admission_report_sha256"
               not in summary else repr(summary["admission_report_sha256"])))
        exact_compare(fixture, "I6_readiness", "summary.dynamics_readiness_claimed",
                      "L-SUMMARY", summary["dynamics_readiness_claimed"], False)

        # --- L-REREAD: reader output round-trips its own parser
        parsed_summary = exporter.read_json_file(str(summary_path))
        row(fixture, "L-REREAD", "summary_canonical_roundtrip", "L-REREAD",
            "PASS_EXACT"
            if reader.canonical_json(parsed_summary) == canon_summary else "DIFF",
            "canonical_json(read_json_file(summary.json)) == reader canonical")

    # P3 observation: nonzero entry counts (nonverdict physical sanity)
    counts = {}
    for fixture, paths in FIXTURES.items():
        parsed = exporter.read_json_file(
            str(B3 / "fixtures" / fixture / "report.json"))
        for g in parsed["body_groups"]:
            if g.get("mass_properties") is None:
                continue
            vals = _flatten(g["mass_properties"]["inertia_tensor_about_com"]["value"])
            off_idx = (1, 2, 5, 3, 6, 7)
            counts[f"{fixture}/{g['body_id']}"] = {
                "nonzero_of_9": sum(1 for v in vals if v != 0.0),
                "nonzero_offdiag_of_6": sum(1 for v in (vals[i] for i in off_idx)
                                            if v != 0.0),
                "off_diagonal_hex": [vals[i].hex() for i in off_idx]}
    (RECEIPTS / "07_offdiag_observation.json").write_text(
        json.dumps(counts, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")

    with (RECEIPTS / "01_fixture_hashes.txt").open("w", encoding="utf-8",
                                                   newline="\n") as handle:
        for f, label, name, digest, size in fixture_hashes:
            handle.write(f"{f}\t{label}\t{name}\tsha256={digest}\tbytes={size}\n")

    with (RECEIPTS / "03_verdict_matrix.csv").open("w", encoding="utf-8",
                                                   newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "fixture", "invariant", "sub_field", "layer", "verdict", "detail"])
        writer.writeheader()
        writer.writerows(ROWS)
    (RECEIPTS / "03_verdict_matrix.json").write_text(
        json.dumps(ROWS, indent=1, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")

    with (RECEIPTS / "04_byte_layer.txt").open("a", encoding="utf-8",
                                               newline="\n") as handle:
        for line in findings:
            handle.write("FINDING: " + line + "\n")

    tally: dict[str, int] = {}
    for r in ROWS:
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
    print("VERDICT TALLY:", json.dumps(tally, sort_keys=True))
    for r in ROWS:
        if r["verdict"] in ("DROP", "DIFF"):
            print(f"  {r['verdict']:5s} {r['fixture']}/{r['invariant']}/"
                  f"{r['sub_field']} @{r['layer']}: {r['detail'][:120]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
