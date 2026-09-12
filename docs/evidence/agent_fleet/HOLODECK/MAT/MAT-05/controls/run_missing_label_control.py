"""run_missing_label_control.py -- the missing_label coverage control that
the MAT-05 review found missing (verdict FINDINGS F1, quoted verbatim in
docs/evidence/agent_fleet/FOLLOWUPS_BATCH_04/PREREGISTRATION.txt):

  "[F1, severity 2, non-blocking] R2 negative suite has no missing_label
  probe; a model copy with the label gate stripped passes the full suite
  (teeth-6 expectation not met for the literal gate); fix = add R2 probe
  author_preset(label='   ') -> missing_label."

Two fixed phases, N=2 (preregistered in FOLLOWUPS_BATCH_04/PREREGISTRATION.txt):

  phase P (pristine): author(..., label='   ') against the reference model
    in ../reference must refuse with reason EXACTLY 'missing_label'.
    Writes checks/r2_missing_label_control.txt (verdict HOLD iff matched).

  phase S (stripped): the SAME probe against a TEMP COPY of the model whose
    label gate is stripped by text edit must ACCEPT (a frozen PresetRecord
    is returned). Writes checks/r2_missing_label_control.stripped-FIRED.txt
    with verdict FIRED -- the retained flip demonstration: the control
    FAILS when the gate is stripped, so it cannot pass with the gate gone.

The committed run_controls.py, reference model, and all prior checks/*.txt of
the merged MAT-05 lane are byte-untouched by this instrument; the stripped
copy lives in a temp directory that is removed after the run. Exit 0 iff
P==HOLD and S==FIRED-by-acceptance; anything else exits 1 (a fired run is
retained, never patched).
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # .../MAT-05/controls
LANE = HERE.parent                              # .../MAT-05
REF = LANE / "reference"
CHECKS = LANE / "checks"
MODEL = REF / "mat05_reference_model.py"

sys.path.insert(0, str(REF))

LABEL_GATE = (
    "        if not isinstance(label, str) or not label.strip():\n"
    "            raise Mat05Refusal(REASON_MISSING_LABEL,\n"
    "                               \"a synthetic preset without a nonblank \"\n"
    "                               \"synthetic_label is inadmissible\")\n"
)
STRIPPED = "        pass  # mlc strip: label gate removed for the flip probe\n"

BLANK = "   "


def _write(name, title, rows):
    """rows: list of (id, ok, detail). Lane-native evidence-file format."""
    passed = sum(1 for _, ok, _ in rows if ok)
    lines = [title,
             f"threshold: {len(rows)}/{len(rows)} required; "
             f"measured: {passed}/{len(rows)}",
             f"verdict: {'HOLD' if passed == len(rows) else 'FIRED'}",
             ""]
    for rid, ok, detail in rows:
        lines.append(f"[{'PASS' if ok else 'FAIL'}] {rid}")
        lines.append(f"  {detail}")
    out = CHECKS / name
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return passed == len(rows), out


def main():
    fired_runs = []
    CHECKS.mkdir(exist_ok=True)

    # ---- phase P: pristine model must refuse missing_label ----------------
    import mat05_reference_model as m  # noqa: E402
    part = m.MaterialPartition()
    try:
        part.presets.author("mlc_probe", "knit", "density", 100.0, "kg/m^3",
                            BLANK)
        p_ok = False
        p_detail = "NOT REFUSED (accepted!) -- the label gate did not fire"
    except m.Mat05Refusal as e:
        p_ok = e.reason == "missing_label"
        p_detail = f"refused: reason={e.reason!r}, message={e}"
    except Exception as e:  # unexpected exception type is a row failure
        p_ok = False
        p_detail = f"raised {type(e).__name__}: {e}"
    p_hold, p_file = _write(
        "r2_missing_label_control.txt",
        "R2 missing_label coverage control (fleet-followups-batch-04 D4/F1) "
        "-- pristine model must REFUSE a whitespace-only synthetic_label "
        "with reason 'missing_label' (review finding F1 probe: "
        "author_preset(label='   ') -> missing_label)",
        [("MLC-P", p_ok, p_detail)])

    # ---- phase S: stripped copy must ACCEPT (the control flips) -----------
    src = MODEL.read_text(encoding="utf-8")
    count = src.count(LABEL_GATE)
    tmp = LANE / ".mlc_tmp"
    s_accepted, s_detail = False, ""
    try:
        if count != 1:
            s_detail = (f"INSTRUMENT FAILURE: label-gate needle found "
                        f"{count} times in the model source (want exactly 1); "
                        f"the strip was not applied")
        else:
            tmp.mkdir(exist_ok=True)
            (tmp / "mat05_reference_model_stripped.py").write_text(
                src.replace(LABEL_GATE, STRIPPED), encoding="utf-8")
            # Register the module in sys.modules BEFORE exec: dataclasses'
            # kw_only detection resolves cls.__module__ through sys.modules.
            # Bytecode writing is disabled so the temp dir stays file-only.
            spec = importlib.util.spec_from_file_location(
                "mat05_reference_model_stripped",
                tmp / "mat05_reference_model_stripped.py")
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            old_dwb = sys.dont_write_bytecode
            sys.dont_write_bytecode = True
            try:
                spec.loader.exec_module(mod)
            finally:
                sys.dont_write_bytecode = old_dwb
            del sys.modules[spec.name]
            spart = mod.MaterialPartition()
            try:
                rec = spart.presets.author("mlc_probe", "knit", "density",
                                           100.0, "kg/m^3", BLANK)
                s_accepted = (getattr(rec, "synthetic_label", None) == BLANK)
                s_detail = (f"ACCEPTED as predicted with the gate stripped: "
                            f"frozen record {rec.name}.{rec.prop} "
                            f"synthetic_label={rec.synthetic_label!r} -- "
                            f"the control FLIPS when the gate is gone")
            except mod.Mat05Refusal as e:
                s_detail = (f"STILL REFUSED with the gate stripped: "
                            f"reason={e.reason!r} -- strip did not remove "
                            f"the refusal path")
            except Exception as e:
                s_detail = f"raised {type(e).__name__}: {e}"
    finally:
        if tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)

    # FIRED is the EXPECTED verdict for phase S: the control's expectation
    # (refusal) is not met on the stripped copy, which is exactly the flip
    # the packet falsifier demands be impossible to miss.
    s_hold, s_file = _write(
        "r2_missing_label_control.stripped-FIRED.txt",
        "R2 missing_label coverage control run against a STRIPPED model copy "
        "(fleet-followups-batch-04 D4/F1 flip demonstration) -- expected "
        "verdict FIRED: with the label gate removed the blank label is "
        "ACCEPTED, so this control's refusal expectation fails. If this "
        "file ever shows HOLD, the control has no teeth.",
        [("MLC-S", False, s_detail)])
    if not s_hold:
        fired = CHECKS / (s_file.stem + ".txt")
        fired_runs.append(fired.name)

    summary = {
        "control": "r2_missing_label_control (fleet-followups-batch-04, "
                   "mat-05 review F1)",
        "phases": {
            "P_pristine": "HOLD" if p_hold else "FIRED",
            "S_stripped": "FIRED (expected flip)" if not s_hold else "HOLD",
        },
        "flip_proven": bool(p_hold and (not s_hold) and s_accepted),
        "fired_runs_retained": fired_runs,
    }
    (CHECKS / "missing_label_control_summary.txt").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if summary["flip_proven"] else 1


if __name__ == "__main__":
    sys.exit(main())
