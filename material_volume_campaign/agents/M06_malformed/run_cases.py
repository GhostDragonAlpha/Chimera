"""M06 case runner: builds fixtures from the FROZEN matrix, executes both CLIs,
captures receipts, and issues verdicts against the preregistered expectations.

Falsifier (from the brief): any case where invalid input yields a SUCCESSFUL
EXPORT (exit 0 with exported mass properties, or an admissible report emitting
reconstructed_mass_properties) is a CRITICAL defect; preserved verbatim.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cases as cases_mod  # noqa: E402
from cases import CASES, MUT, RAW, BASE  # noqa: E402

# ---- RESUME HARNESS FIXES (frozen cases.py/matrix.md left byte-identical) ----
# (1) REGISTRATION FIX: F05 ("groups rotation entry as string") has a mutation
# function in cases.py (_rot_str) but was never registered in MUT — the only
# unregistered case id of 62. First pass therefore ran the UNMUTATED baseline and
# produced a FALSE CRITICAL-DEFECT (preserved verbatim:
# receipts/failures/first_pass/). Register it here.
EXTRA_MUT = {"F05": (cases_mod._rot_str, ())}
# (2) REALIZATION FIX: C01/C04/C05/C06 are specified by the frozen matrix as the
# decimal literal 1e400 ("parses to float inf", runtime class nonfinite_input).
# The Python-level mutation 1e400 == float('inf') serializes via json.dumps as the
# NONSTANDARD Infinity token, which exercises the C02/C03/C07 reader class
# (input_read_error) instead. Honor the frozen matrix text byte-level: write the
# literal `1e400` with raw-text patches (same target field as the original MUT
# function in every case). Anchors verified unique in the baseline bytes.
TEXT_FIX = {
    "C01": [("partition", '"position": [1.0, 0.0, 0.0]',
             '"position": [1e400, 0.0, 0.0]')],
    "C04": [("partition", '"density_kg_m3": 12.0', '"density_kg_m3": 1e400')],
    "C05": [("groups", '"rotation": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]',
             '"rotation": [[1e400, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]')],
    "C06": [("groups", '"origin_m": [0.0, 0.0, 0.0]', '"origin_m": [0.0, 0.0, 1e400]')],
}
EFFECTIVE_MUT = {k: v for k, v in MUT.items() if k not in TEXT_FIX}
EFFECTIVE_MUT.update(EXTRA_MUT)

FIX = HERE / "fixtures" / "cases"
REC = HERE / "receipts" / "cases"
FIX.mkdir(parents=True, exist_ok=True)
REC.mkdir(parents=True, exist_ok=True)

ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
ADM = [sys.executable, "work/material_volume_admission.py"]
EXP = [sys.executable, "work/material_volume_body_export.py"]


def build_case(cid: str) -> dict[str, Path]:
    files = {}
    for name in ("manifest", "partition", "groups"):
        src = HERE / BASE / f"{name}.json"
        dst = FIX / f"{cid}_{name}.json"
        if name in [n for n, _o, _n in RAW.get(cid, [])]:
            continue  # patched below
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        files[name] = dst
    if cid in RAW:
        for name, old, new in RAW[cid]:
            dst = FIX / f"{cid}_{name}.json"
            text = (HERE / BASE / f"{name}.json").read_text(encoding="utf-8")
            assert old in text, f"{cid}: raw patch anchor not found in {name}"
            dst.write_text(text.replace(old, new, 1), encoding="utf-8")
            files[name] = dst
    if cid in EFFECTIVE_MUT:
        fn, args = EFFECTIVE_MUT[cid]
        names = tuple(args) if args else ("groups",)
        docs = {n: json.loads((HERE / BASE / f"{n}.json").read_text(encoding="utf-8"))
                for n in names}
        fn(*[docs[n] for n in names])
        for n, doc in docs.items():
            dst = FIX / f"{cid}_{n}.json"
            dst.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
            files[n] = dst
    if cid in TEXT_FIX:
        for name, old, new in TEXT_FIX[cid]:
            dst = FIX / f"{cid}_{name}.json"
            text = dst.read_text(encoding="utf-8")
            assert old in text, f"{cid}: TEXT_FIX anchor not found in {name}"
            assert text.count(old) == 1, f"{cid}: TEXT_FIX anchor not unique in {name}"
            dst.write_text(text.replace(old, new, 1), encoding="utf-8")
    assert set(files) == {"manifest", "partition", "groups"}, f"{cid}: incomplete fixtures"
    # RESUME ASSERTION: every case id must carry an actual mutation, else the case
    # silently re-runs the green baseline (the F05 first-pass failure mode).
    assert cid in EFFECTIVE_MUT or cid in RAW or cid in TEXT_FIX, \
        f"{cid}: no mutation registered — would run the unmutated baseline"
    return files


def run(cmd: list[str], args: list[str], tag: str) -> tuple[int, str, str]:
    proc = subprocess.run(cmd + args, cwd=str(HERE), env=ENV,
                          capture_output=True, text="utf-8", errors="replace")
    (REC / f"{tag}.cmd").write_text(" ".join(cmd + args) + "\n", encoding="utf-8")
    (REC / f"{tag}.stdout").write_text(proc.stdout, encoding="utf-8")
    (REC / f"{tag}.stderr").write_text(proc.stderr, encoding="utf-8")
    (REC / f"{tag}.exit").write_text(f"{proc.returncode}\n", encoding="utf-8")
    return proc.returncode, proc.stdout, proc.stderr


def names_in(report: object) -> list[str]:
    """Collect every machine-readable refusal name present in a report."""
    found: list[str] = []
    if isinstance(report, dict):
        for key in ("reason_codes", "admission_reason_codes"):
            value = report.get(key)
            if isinstance(value, list):
                found += [str(v) for v in value]
        ref = report.get("compiler_refusal")
        if isinstance(ref, dict) and ref.get("reason"):
            found.append(str(ref["reason"]))
        for group in report.get("body_groups", []) or []:
            if isinstance(group, dict):
                for key in ("reason_codes", "admission_reason_codes"):
                    value = group.get(key)
                    if isinstance(value, list):
                        found += [str(v) for v in value]
        dec = report.get("decision") or report.get("export_status")
        if dec:
            found.append(str(dec))
    return found


def mass_emitted(report: object) -> bool:
    """FALSIFIER probe: did any mass property get exported/emitted?"""
    if not isinstance(report, dict):
        return False
    for group in (report.get("body_groups") or []):
        if isinstance(group, dict) and group.get("mass_properties") is not None:
            return True
    auth = report.get("mass_authority")
    if isinstance(auth, dict) and auth.get("reconstructed_mass_properties") is not None:
        return True
    if isinstance(report.get("reconstructed_mass_properties"), dict):
        return True
    return False


def _exit_ok(expected: str, actual: int) -> bool:
    """Preregistered exit mapping: admission doc pins 0/1/2; exporter is undocumented."""
    if expected == "nonzero":
        return actual != 0
    return str(actual) == expected


def judge(cid: str, tool: str, spec: dict, exit_code: int, stdout: str) -> dict:
    try:
        report = json.loads(stdout)
    except json.JSONDecodeError:
        report = None
    if spec["expect"] == "doc_behavior_no_mass":
        problems = []
        if report is None:
            problems.append("stdout is not a JSON report")
        elif tool == "adm":
            if exit_code != 0:
                problems.append(f"exit {exit_code} != 0")
            if report.get("decision") != "validation_only_admissible":
                problems.append(f"decision={report.get('decision')!r}")
            auth = report.get("mass_authority") or {}
            if auth.get("reconstructed_mass_properties") is not None:
                problems.append("reconstructed_mass_properties EMITTED under source authority")
            if auth.get("reconstructed_mass_properties_emitted") is not False:
                problems.append("reconstructed_mass_properties_emitted is not false")
            if mass_emitted(report):
                problems.append("FALSIFIER: mass emitted")
        else:
            if exit_code != 0:
                problems.append(f"exit {exit_code} != 0")
            if report.get("export_status") != "unsupported":
                problems.append(f"export_status={report.get('export_status')!r}")
            if report.get("source_effective_segment_payloads_consumed") is not False:
                problems.append("source payloads consumed flag is not false")
            for group in (report.get("body_groups") or []):
                if group.get("mass_properties") is not None:
                    problems.append(f"group {group.get('body_id')!r} exported mass")
                if "source_effective_segment_mass_unsupported" not in (group.get("reason_codes") or []):
                    problems.append(f"group {group.get('body_id')!r} missing named unsupported reason")
            if mass_emitted(report):
                problems.append("FALSIFIER: mass emitted")
        return {"case": cid, "tool": tool,
                "verdict": "DOC-CONFIRMED" if not problems else "CRITICAL-DEFECT",
                "exit": exit_code, "expected_reason": "documented unsupported/no-mass",
                "found_names": names_in(report) if report else ["<unparseable>"],
                "notes": "; ".join(problems) if problems else
                         "doc-promised behavior reproduced exactly (no mass exported)"}
    # refusal expectation
    expected_reason = spec["reason"]
    reason_ok = expected_reason in stdout
    if exit_code == 0:
        if mass_emitted(report):
            verdict, notes = "CRITICAL-DEFECT", "FALSIFIER TRIPPED: exit 0 with exported mass"
        else:
            verdict, notes = "SILENT-PASS", "exit 0, no refusal name matched"
    elif not reason_ok:
        verdict = "WRONG-NAME"
        notes = f"refused (exit {exit_code}) but expected reason {expected_reason!r} absent"
    elif not _exit_ok(spec["exit"], exit_code):
        verdict = "EXIT-DEVIATION"
        notes = (f"named refusal matched, but exit {exit_code} deviates from "
                 f"preregistered expectation {spec['exit']!r}")
    else:
        verdict = "NAMED-REFUSAL"
        notes = ""
    return {"case": cid, "tool": tool, "verdict": verdict, "exit": exit_code,
            "expected_reason": expected_reason,
            "expected_exit": spec["exit"], "found_names": names_in(report) if report else ["<unparseable>"],
            "notes": notes}


def main() -> int:
    results = []
    for cid, _cat, _desc, runs, _doc in CASES:
        files = build_case(cid)
        base_args = ["--manifest", str(files["manifest"].relative_to(HERE)),
                     "--partition", str(files["partition"].relative_to(HERE))]
        for spec in runs:
            tool = spec["tool"]
            if tool == "adm":
                code, out, err = run(ADM, base_args, f"{cid}__adm")
            else:
                code, out, err = run(EXP, base_args + ["--groups",
                                     str(files["groups"].relative_to(HERE))], f"{cid}__exp")
            if err.strip():
                (REC / f"{cid}__{tool}.stderr").write_text(err, encoding="utf-8")
            results.append(judge(cid, tool, spec, code, out))
    (HERE / "receipts" / "verdicts.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8")
    counts: dict[str, int] = {}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        flag = "" if r["verdict"] in ("NAMED-REFUSAL", "DOC-CONFIRMED") else "  <<<"
        print(f"{r['case']:4s} {r['tool']:3s} exit={r['exit']:2d} "
              f"{r['verdict']:15s} exp={r['expected_reason'][:44]:44s}{flag}")
        if r["verdict"] not in ("NAMED-REFUSAL", "DOC-CONFIRMED"):
            print(f"      found: {r['found_names']} | {r['notes']}")
    print("\nSUMMARY:", json.dumps(counts, sort_keys=True),
          f"| runs={len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
