# =============================================================================
# material_volume_diagnostic -- PROMOTION COPY (W5, 2026-09-24)
# =============================================================================
# TOOL IDENTITY
#   name:    material_volume_diagnostic
#   role:    read-only diagnostic CLI for chimera.rigid_body_mass_export.v1
#            reports (root/per-body statuses, omitted bodies + reasons,
#            unassigned cells, frames, units; readiness is DISPLAYED, never
#            promoted). Static, standalone, CPU-only; no runtime wiring.
#   version: 1.0.0 (promotion candidate; first versioned release = the
#            post-B8 code, byte-identified by the source blob below)
#   source:  material_volume_campaign/agents/M09_diagnostic/
#            material_volume_diagnostic.py
#   source blob at pinned revision feb01661bedb81063d88937d4c284ee9b4fa3ebd:
#            f9763b4318e6954b9141b8bc954c10a856c39cf2
#   diff vs that blob: THIS HEADER ONLY (comment lines; zero behavior edits --
#            proved by receipts/home_header_diff.txt and the CLI battery).
#
# RECEIPT TRAIL
#   M09  commit 7701d8db -- implemented + integrated (11/11 tests; U7 finding:
#        the reader summary drops CON-4/6/7 diagnostics, so this CLI passes
#        blocking_cell_ids / blocking_assignment_statuses / top-level
#        reason_codes+detail / unassigned_cells rows through for display).
#   B2a  independent non-author review (agents/B2a_review_m09/report.md):
#        ACCEPT-WITH-NOTES; hostile-input-only defects D1 (argparse usage exit
#        collided with reader-rejected 2), D2 (human-mode crash on non-object
#        unassigned_cells rows), D3 (string unassigned_cell_ids mangled per
#        character). Genuine exporter output cannot trigger any of them.
#   B8   commit 8c4f8ba2 -- D1/D2/D3 fixed failing-first (17/17; genuine
#        outputs byte-identical pre/post; agents/B8_fixes/fixes.md receipt).
#   W5   this file: promotion preparation ONLY (dependency pinning + docs +
#        clean home copy + suite equivalence). Publication/integration is the
#        coordinator's, via the existing publisher path, after a non-author
#        review of this dir.
#
# EXIT CONTRACT (frozen; M09 preregistration.md, "Exit codes (frozen)")
#   0   every report accepted by the reader (any status, incl. refused, is a
#       successfully DIAGNOSED report)
#   2   reader rejected a report (exporter.ExportInputError)
#   4   readiness-violation alarm (falsifier F2; must never fire)
#   64  usage error (argparse; BSD sysexits EX_USAGE convention, distinct from
#       {0, 2, 4}; B8 decision for the frozen "other nonzero" slot)
#   NOTE: this is THIS TOOL's own frozen contract. The 0/2/1 mapping discussed
#   under M06-H04 belongs to the VALIDATION CLI, NOT to this diagnostic.
#
# STATIC / READ-ONLY CLAIMS
#   - writes nothing: input files are never mutated; sys.dont_write_bytecode
#     is set BEFORE the reader import so no __pycache__ can appear in tools/;
#   - validates nothing of its own: every status/summary/hash comes from the
#     reader (summarize_export_report / canonical_json); the raw parsed
#     mapping is used ONLY for display passthrough of fields the summary
#     drops; no status is ever invented;
#   - promotes nothing: readiness is displayed as-is and stays false (CON-14);
#     the final human-mode line is always "readiness: false" (F2 sentinel);
#   - static analysis only: no runtime wiring into any engine or pipeline.
#
# DEPENDENCY STATEMENT (pinned; full manifest: docs/dependency_manifest.md)
#   All parsing/validation lives in ONE dependency directory, located by
#   --tools-dir, env M09_TOOLS_DIR, or the nearest ancestor tools/ containing
#   material_volume_body_export_reader.py:
#     material_volume_body_export_reader.py   DIRECT (summarize_export_report,
#         canonical_json) -- blob bd7e08d98399ad75fc2534b12632e0524bde1e01 at
#         rev feb01661bedb81063d88937d4c284ee9b4fa3ebd (includes W3's landed
#         M13 repair, integrated af735b7f)
#     material_volume_body_export.py  DIRECT + transitive (read_json_file,
#         ExportInputError) -- blob f6fd2af161705371cb9a59df941460ca2b8e2b84
#     material_volume_admission.py, material_volume.py, numpy -- TRANSITIVE
#         (module-load imports of the two above; OIDs in the manifest)
#   RE-PIN RULE: final integration re-pins docs/dependency_manifest.md against
#   the then-current landed revision (W3's reader repair was in flight when W5
#   was dispatched; it landed at af735b7f BEFORE this pin was taken -- verify
#   nothing moved again at integration time).
# =============================================================================
"""Read-only diagnostic CLI for ``chimera.rigid_body_mass_export.v1`` reports.

M09 tool of the 2026-09-24 material-volume campaign. It rides entirely on the
public interface of ``tools/material_volume_body_export_reader.py``:

- ``material_volume_body_export.read_json_file``  (all file parsing; strict:
  duplicate keys and nonstandard constants rejected)
- ``material_volume_body_export_reader.summarize_export_report``  (all
  validation; the ONLY source of statuses, per-body summaries, and readiness)
- ``material_volume_body_export_reader.canonical_json``  (machine output)
- ``material_volume_body_export.ExportInputError`` / ``EXPORT_SCHEMA``

The raw reader-parsed mapping is used only to pass through, for DISPLAY,
fields the reader summary drops (``blocking_cell_ids``,
``blocking_assignment_statuses``, top-level ``reason_codes``/``detail``,
per-cell ``unassigned_cells`` rows). Nothing is re-validated, no status is
invented, no input file is ever written or mutated, and no status is ever
promoted: readiness is displayed as-is from the reader and stays ``false``
(CON-14). ``sys.dont_write_bytecode`` is set before the reader import so no
``__pycache__`` can appear in ``tools/``.

Run:
    python material_volume_diagnostic.py REPORT [REPORT ...] [--json] [--tools-dir DIR]

Exit codes: 0 every report accepted (any status, incl. ``refused``, is a
successfully diagnosed report) · 2 reader rejected a report · 4 readiness
violation alarm (falsifier F2; must never fire) · 64 usage error (argparse;
frozen contract requires "other nonzero", distinct from the reader codes).
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Mapping, Sequence

sys.dont_write_bytecode = True  # F1: never write __pycache__ anywhere, esp. tools/

TOOL_NAME = "material_volume_diagnostic"
READER_MODULE = "material_volume_body_export_reader"
EXPORTER_MODULE = "material_volume_body_export"
# Frozen exit contract (preregistration.md): 0 accepted · 2 reader-rejected ·
# 4 readiness alarm · usage errors "other nonzero". argparse's default usage
# exit IS 2, colliding with reader-rejected (B2a defect D1), so usage errors
# exit 64 — the BSD sysexits.h EX_USAGE convention, distinct from {0, 2, 4}.
EXIT_USAGE = 64
STATUSES = ("complete", "partial", "blocked", "unsupported", "refused")
OMITTED_PASSTHROUGH_KEYS = ("blocking_cell_ids", "blocking_assignment_statuses",
                            "admission_reason_codes")
UNASSIGNED_ROW_KEYS = ("cell_id", "assignment_status", "reason")


class _UsageErrorParser(argparse.ArgumentParser):
    """ArgumentParser whose usage errors do not collide with exit code 2.

    Overrides only the exit STATUS of argparse's error(): the stderr text is
    byte-identical to the default (usage line + "prog: error: message"), but
    the frozen contract reserves 2 for "reader rejected a report" and requires
    usage errors to exit "other nonzero" (B2a defect D1; frozen decision:
    EXIT_USAGE = 64).
    """

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, f"{self.prog}: error: {message}\n")


def find_tools_dir(explicit: str | None = None) -> Path:
    """Locate the directory holding the reader module.

    Precedence: --tools-dir flag, M09_TOOLS_DIR env var, then the nearest
    ancestor of this file that contains tools/material_volume_body_export_reader.py.
    """
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    env = os.environ.get("M09_TOOLS_DIR")
    if env:
        candidates.append(Path(env))
    here = Path(__file__).resolve().parent
    for ancestor in [here, *here.parents]:
        candidate = ancestor / "tools"
        if (candidate / f"{READER_MODULE}.py").is_file():
            candidates.append(candidate)
            break
    for candidate in candidates:
        if (candidate / f"{READER_MODULE}.py").is_file():
            return candidate.resolve()
    raise SystemExit(f"{TOOL_NAME}: cannot locate {READER_MODULE}.py; "
                     f"use --tools-dir or M09_TOOLS_DIR")


def load_reader(tools_dir: Path):
    """Import the reader + exporter modules from tools_dir (sys.path insert)."""
    tools_text = str(tools_dir)
    if tools_text not in sys.path:
        sys.path.insert(0, tools_text)
    import importlib
    reader = importlib.import_module(READER_MODULE)
    exporter = importlib.import_module(EXPORTER_MODULE)
    return reader, exporter


def _raw_row_passthrough(row: Mapping, keys: Sequence[str]) -> dict:
    """Display passthrough: report values verbatim; missing keys -> null."""
    return {key: row.get(key) for key in keys}


def diagnose_report(path: str, report_doc: object, summary: Mapping) -> dict:
    """Build one per-report entry from the reader summary (+display passthrough)."""
    bodies = []
    omitted = []
    frames = set()
    units = set()
    raw_rows = {}
    raw_groups = report_doc.get("body_groups") if isinstance(report_doc, Mapping) else None
    if isinstance(raw_groups, list):
        for row in raw_groups:
            if isinstance(row, Mapping) and isinstance(row.get("body_id"), str):
                raw_rows[row["body_id"]] = row
    for body in summary["bodies"]:
        status = body["export_status"]
        entry = {"body_id": body["body_id"],
                 "export_status": status,
                 "owned_cell_ids": body["owned_cell_ids"],
                 "omitted": status != "exported"}
        if status == "exported":
            com = body["center_of_mass"]
            inertia = body["inertia_tensor_about_com"]
            entry["mass_kg"] = body["mass_kg"]
            entry["com"] = {"value": com["value"], "unit": com["unit"],
                            "coordinate_frame": com["coordinate_frame"]}
            entry["inertia"] = {"unit": inertia["unit"],
                                "coordinate_frame": inertia["coordinate_frame"],
                                "basis": inertia["basis"]}
            units.update(value for value in (com["unit"], inertia["unit"]) if value)
            units.add("kg")  # summary["mass_kg"] is kilograms by definition (frozen T1)
            for frame in (com["coordinate_frame"], inertia["coordinate_frame"]):
                if frame:
                    frames.add(frame)
        else:
            entry["reason_codes"] = body.get("reason_codes", [])
            raw = raw_rows.get(body["body_id"])
            if isinstance(raw, Mapping):
                for key in OMITTED_PASSTHROUGH_KEYS:
                    if key in raw:
                        entry[key] = raw[key]
            omitted.append(entry)
        bodies.append(entry)

    unassigned_cells = None
    if isinstance(report_doc, Mapping) and isinstance(report_doc.get("unassigned_cells"), list):
        unassigned_cells = [_raw_row_passthrough(row, UNASSIGNED_ROW_KEYS)
                            if isinstance(row, Mapping) else row
                            for row in report_doc["unassigned_cells"]]

    entry = {"path": path,
             "ok": True,
             "schema_version": summary["schema_version"],
             "export_status": summary["export_status"],
             "admission_status": (summary["admission_status"]
                                  if summary["admission_status"] is not None
                                  else "not_reported"),
             "readiness_claimed": summary["dynamics_readiness_claimed"],
             "physical_state_mutated": summary["physical_state_mutated"],
             "bodies": bodies,
             "omitted_bodies": omitted,
             "frames": sorted(frames),
             "units": sorted(units)}
    if unassigned_cells is not None:
        entry["unassigned_cells"] = unassigned_cells
    if isinstance(report_doc, Mapping):
        if "reason_codes" in report_doc:
            entry["top_level_reason_codes"] = report_doc["reason_codes"]
        if "detail" in report_doc:
            entry["detail"] = report_doc["detail"]
    entry["unassigned_cell_ids"] = summary["unassigned_cell_ids"]
    entry["input_hashes"] = summary["input_hashes"]
    return entry


def _plural_list(values: Sequence, none_text: str = "(none)") -> str:
    if isinstance(values, str):
        # D3 (B2a probe P4): a str IS a Sequence — without this guard a bare
        # string would join per CHARACTER ("c, e, l, l, -, B"). A string value
        # is ONE value; join whole values. Same defect class M09 locked for
        # blocking_assignment_statuses.
        values = [values]
    return ", ".join(str(value) for value in values) if values else none_text


def render_human(entries: Sequence[Mapping]) -> str:
    lines = []
    for entry in entries:
        lines.append(f"report: {entry['path']}")
        if not entry["ok"]:
            lines.append("  ok: false")
            lines.append(f"  error_reason: {entry['error']['reason']}")
            lines.append(f"  error_detail: {entry['error']['detail']}")
            continue
        lines.append("  ok: true")
        lines.append(f"  schema_version: {entry['schema_version']}")
        lines.append(f"  export_status: {entry['export_status']}")
        lines.append(f"  admission_status: {entry['admission_status']}")
        lines.append(f"  readiness_claimed: {str(entry['readiness_claimed']).lower()}")
        lines.append(f"  physical_state_mutated: "
                     f"{str(entry['physical_state_mutated']).lower()}")
        lines.append(f"  top_level_reason_codes: "
                     f"{_plural_list(entry.get('top_level_reason_codes', []))}")
        lines.append(f"  detail: {entry.get('detail', '(none)')}")
        lines.append(f"  bodies: {len(entry['bodies'])}")
        omitted = entry["omitted_bodies"]
        lines.append(f"  omitted_bodies: {len(omitted)}")
        for index, body in enumerate(omitted):
            blocking = body.get("blocking_cell_ids")
            statuses = body.get("blocking_assignment_statuses")
            if isinstance(statuses, list):
                statuses = [f"{row.get('cell_id')}:{row.get('status')}"
                            for row in statuses if isinstance(row, Mapping)]
            lines.append(f"    omitted[{index}] body_id={body['body_id']} "
                         f"export_status={body['export_status']} "
                         f"reason_codes={_plural_list(body['reason_codes'])} "
                         f"blocking_cell_ids={_plural_list(blocking or [])} "
                         f"blocking_assignment_statuses={_plural_list(statuses or [])} "
                         f"admission_reason_codes="
                         f"{_plural_list(body.get('admission_reason_codes') or [])}")
        unassigned_ids = entry["unassigned_cell_ids"]
        lines.append(f"  unassigned_cell_ids: {_plural_list(unassigned_ids)}")
        rows = entry.get("unassigned_cells")
        lines.append(f"  unassigned_cells: {len(rows) if rows is not None else '(not reported)'}")
        for index, row in enumerate(rows or []):
            if isinstance(row, Mapping):
                lines.append(f"    unassigned[{index}] cell_id={row.get('cell_id')} "
                             f"assignment_status={row.get('assignment_status')} "
                             f"reason={row.get('reason')}")
            else:
                # D2 (B2a probe P5): a reader-accepted non-object row must not
                # crash human mode (pre-fix: AttributeError, exit 1). Render
                # the value verbatim (repr, so type stays unambiguous); it is
                # never treated as a cell_id/status — display only, exactly
                # like the JSON passthrough.
                lines.append(f"    unassigned[{index}] <non-object row: {row!r}>")
        lines.append(f"  frames: {_plural_list(entry['frames'], '(none)')}")
        lines.append(f"  units: {_plural_list(entry['units'], '(none)')}")
        exported = [body for body in entry["bodies"] if not body["omitted"]]
        lines.append(f"  exported_masses: {len(exported) if exported else '(none)'}")
        for index, body in enumerate(exported):
            lines.append(f"    mass[{index}] body_id={body['body_id']} "
                         f"mass={body['mass_kg']} kg "
                         f"com_frame={body['com']['coordinate_frame']} "
                         f"com_unit={body['com']['unit']} "
                         f"inertia_frame={body['inertia']['coordinate_frame']} "
                         f"inertia_unit={body['inertia']['unit']} "
                         f"inertia_basis={body['inertia']['basis']}")
    lines.append("readiness: false")
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = _UsageErrorParser(
        prog=TOOL_NAME,
        description="Read-only diagnostic for rigid-body mass export reports "
                    "(rides on tools/material_volume_body_export_reader.py; "
                    "never writes, never promotes; readiness stays false).")
    parser.add_argument("reports", nargs="+", metavar="REPORT",
                        help="export report JSON path(s), read-only")
    parser.add_argument("--json", action="store_true",
                        help="emit the frozen machine contract (canonical JSON)")
    parser.add_argument("--tools-dir", default=None,
                        help="directory holding material_volume_body_export_reader.py "
                             "(default: nearest ancestor tools/; env M09_TOOLS_DIR)")
    args = parser.parse_args(argv)

    reader, exporter = load_reader(find_tools_dir(args.tools_dir))

    entries = []
    readiness_violation = False
    for path in args.reports:
        try:
            report_doc = exporter.read_json_file(path)
            summary = reader.summarize_export_report(report_doc)
        except exporter.ExportInputError as error:
            entries.append({"path": path, "ok": False,
                            "error": {"reason": error.reason,
                                      "detail": error.detail}})
            continue
        entry = diagnose_report(path, report_doc, summary)
        if entry["readiness_claimed"] is not False:
            readiness_violation = True
        entries.append(entry)

    payload = {"tool": TOOL_NAME, "readiness": False, "reports": entries}
    if args.json:
        sys.stdout.write(reader.canonical_json(payload))
    else:
        sys.stdout.write(render_human(entries))
    sys.stdout.flush()
    if readiness_violation:
        sys.stderr.write(f"{TOOL_NAME}: READINESS-VIOLATION: a summary carried "
                         f"dynamics_readiness_claimed != false\n")
        return 4
    if any(not entry["ok"] for entry in entries):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
