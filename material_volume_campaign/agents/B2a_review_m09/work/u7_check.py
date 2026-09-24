"""B2a P3b (corrected out-of-vocabulary probe) + Area-5 U7 verification."""
from __future__ import annotations
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
MY = Path(__file__).resolve().parent
WORKTREE = Path("E:/ChimeraWork/mvc-20260924")
TOOLS = WORKTREE / "tools"
CLI = MY / "m09_copy" / "material_volume_diagnostic.py"
READER_CLI = TOOLS / "material_volume_body_export_reader.py"
PROBE = MY / "probes"
sys.path.insert(0, str(TOOLS))
import material_volume_body_export as exporter  # noqa: E402
import material_volume_body_export_reader as reader  # noqa: E402
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
lines = []


def run(cmd):
    return subprocess.run([sys.executable, *[str(c) for c in cmd]],
                          capture_output=True, text=True, env=ENV)


# ---------- P3b: per-body status outside {exported, not_exported}, no mass ----------
doc = {
    "schema_version": "chimera.rigid_body_mass_export.v1",
    "export_status": "partial",
    "body_groups": [
        {"body_id": "body-A", "export_status": "exported",
         "owned_cell_ids": ["cell-A"],
         "mass_properties": {
             "mass": {"value": 2.0, "unit": "kg"},
             "center_of_mass": {"value": [0.0, 0.0, 0.0], "unit": "m",
                                "coordinate_frame": "frame-A"},
             "inertia_tensor_about_com": {
                 "value": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                 "unit": "kg*m^2", "coordinate_frame": "frame-A",
                 "basis": "diagonal-in-body-frame",
                 "full_symmetric_tensor": True,
                 "off_diagonal_terms_preserved": True,
                 "principal_axis_transform_applied": False}}},
        {"body_id": "body-B", "export_status": "exploded",
         "owned_cell_ids": ["cell-B"], "mass_properties": None}],
    "unassigned_cell_ids": [], "unassigned_cells": [], "input_hashes": None,
}
p3b = PROBE / "P3b_out_of_vocab_body_status.json"
p3b.write_text(json.dumps(doc), encoding="utf-8")
try:
    summary = reader.summarize_export_report(exporter.read_json_file(str(p3b)))
    lines.append(f"### P3b: reader ACCEPTED status={summary['export_status']} "
                 f"body statuses={[b['export_status'] for b in summary['bodies']]}")
except exporter.ExportInputError as error:
    summary = None
    lines.append(f"### P3b: reader REJECTED reason={error.reason}")
proc = run([CLI, str(p3b), "--json"])
lines.append(f"  json: exit={proc.returncode}")
if summary is not None:
    entry = json.loads(proc.stdout)["reports"][0]
    b_b = [b for b in entry["bodies"] if b["body_id"] == "body-B"][0]
    lines.append(f"  CLI body-B as displayed: export_status={b_b['export_status']!r} "
                 f"omitted={b_b['omitted']}")
    lines.append(f"  note: CLI displays out-of-vocabulary per-body status verbatim "
                 f"(no flag); reader summary carried it unchanged")

# ---------- Area 5: U7 on MY OWN genuine blocked + refused fixtures ----------
for name in ("blocked", "refused"):
    fixture = MY / f"fx_{name}.json"
    raw = exporter.read_json_file(str(fixture))
    lines.append(f"### U7 {name}: RAW report top-level keys with diagnostics: "
                 f"reason_codes={raw.get('reason_codes')!r} detail={str(raw.get('detail'))[:70]!r}")
    summary = reader.summarize_export_report(raw)
    lines.append(f"  reader summary top-level keys={sorted(summary)}")
    lines.append(f"  summary has reason_codes: {'reason_codes' in summary}; "
                 f"detail: {'detail' in summary}; "
                 f"unassigned_cells rows: {'unassigned_cells' in summary}; "
                 f"unassigned_cell_ids={summary['unassigned_cell_ids']!r}")
    for i, b in enumerate(summary["bodies"]):
        dropped = [k for k in ("blocking_cell_ids", "blocking_assignment_statuses",
                               "admission_reason_codes") if k in b]
        lines.append(f"  summary body[{i}] {b['body_id']} status={b['export_status']} "
                     f"blocking-diagnostics present: {dropped if dropped else 'NONE'}")
    raw_rows = {r["body_id"]: r for r in raw.get("body_groups", []) if isinstance(r, dict)}
    for bid, r in raw_rows.items():
        present = [k for k in ("blocking_cell_ids", "blocking_assignment_statuses",
                               "admission_reason_codes") if k in r]
        lines.append(f"  RAW row {bid}: blocking diagnostics present: "
                     f"{present if present else 'NONE'}"
                     + (f" blocking_cell_ids={r.get('blocking_cell_ids')!r}" if present else ""))
    # reader CLI subprocess (M09's receipt method)
    proc = run([READER_CLI, str(fixture)])
    out = json.loads(proc.stdout) if proc.returncode == 0 else None
    lines.append(f"  reader CLI: exit={proc.returncode} stderr={'(none)' if not proc.stderr.strip() else proc.stderr.strip()[:80]} "
                 f"status={out.get('export_status') if out else None} "
                 f"readiness={out.get('dynamics_readiness_claimed') if out else None}")
    # M09 CLI must surface what the summary drops
    proc = run([CLI, str(fixture), "--json"])
    entry = json.loads(proc.stdout)["reports"][0]
    lines.append(f"  M09 CLI: exit={proc.returncode} surfaced top_level_reason_codes="
                 f"{entry.get('top_level_reason_codes')!r} detail={str(entry.get('detail'))[:60]!r} "
                 f"unassigned_cells rows={entry.get('unassigned_cells')!r}")
    for b in entry.get("omitted_bodies", []):
        lines.append(f"    omitted {b['body_id']}: blocking_cell_ids={b.get('blocking_cell_ids')!r} "
                     f"blocking_assignment_statuses={b.get('blocking_assignment_statuses')!r} "
                     f"admission_reason_codes={str(b.get('admission_reason_codes'))[:60]!r}")

(Path(__file__).resolve().parents[1] / "receipts" / "b2a_u7_receipt.txt").write_text(
    "\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
