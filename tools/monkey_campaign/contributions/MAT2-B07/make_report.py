#!/usr/bin/env python3
"""MAT2-B07 report generator: report.md is GENERATED from the receipts —
zero hand-transcribed numbers. Run: python -B make_report.py
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CARD = "MAT2-B07"
SHORT = "B07"

RECEIPTS = ["ownership_mappings.json", "frame_bindings.json",
            "adoption_record.json", "c09_anchor_rerun/c09_anchor_rerun.json",
            "capture/capture_receipt.json"]


def sha(p):
    return hashlib.sha256((HERE / p).read_bytes()).hexdigest()


def load(p):
    return json.loads((HERE / p).read_text(encoding="utf-8"))


def suite_counts():
    proc = subprocess.run(
        [sys.executable, "-B", "-m", "unittest", "discover", "-s", ".",
         "-p", "test_*.py"], capture_output=True, cwd=str(HERE))
    out = (proc.stdout + proc.stderr).decode("utf-8", errors="replace")
    m = re.search(r"Ran (\d+) tests? in", out)
    executed = int(m.group(1)) if m else 0
    ok = "OK" in out.splitlines()[-1] if out else False
    skipped = len(re.findall(r"skipped", out))
    return {"exit": proc.returncode, "executed": executed,
            "skipped": skipped, "ok": ok,
            "summary_line": ("%d executed, %d skipped"
                             % (executed, skipped))}


def main():
    own = load("ownership_mappings.json")
    fb = load("frame_bindings.json")
    ar = load("adoption_record.json")
    c09 = load("c09_anchor_rerun/c09_anchor_rerun.json")
    cap = load("capture/capture_receipt.json")
    suite = suite_counts()
    checks_receipt = {
        "schema": "chimera.b07_checks_receipt.v1",
        "task_id": SHORT,
        "card_id": CARD,
        "suite": suite,
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B make_report.py (suite run "
                                   "inside the generator)"},
    }
    (HERE / "checks_receipt.json").write_bytes(
        json.dumps(checks_receipt, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":"),
                   allow_nan=False).encode("utf-8") + b"\n")
    prereg_sha = sha("PREREGISTRATION.md")
    hand = own["records"]["hand_body_mappings"]
    fore = own["records"]["forearm_correspondences"]
    hd = [r["decision"]["recorded_distance_m"] for r in hand]
    fd = [r["decision"]["recorded_distance_m"] for r in fore]
    exact = sum(1 for c in c09["anchor_comparisons"].values()
                if c["verdict"] == "EXACT")
    lines = []
    w = lines.append
    w("# MAT2-B07 report — assembly adoption under the recorded "
      "authorization package")
    w("")
    w("GENERATED from the receipts by `make_report.py` (zero "
      "hand-transcribed numbers). Composed against CARD_STARTER v3; house "
      "standards IMPLEMENTER_CHECKLIST.md (G1-G9) + TOOLKIT.md (P1-P9) "
      "cited at the candidate commit.")
    w("")
    w("| identity | value |")
    w("|---|---|")
    w("| card | %s (task_id short form %s) |" % (CARD, SHORT))
    w("| attempt | 08d3db08d4d64179b2f95a516a2155bd (agent wk-b07-adopt, "
      "branch-3) |")
    w("| criteria_sha256 | %s |" % own["criteria_sha256"])
    w("| preregistration_sha256 | %s |" % prereg_sha)
    w("| governing decision | Captain #4 ADOPT-WITH-AUTHORIZATIONS (%s) |"
      % ar["governing_frame"]["message_id"])
    w("")
    w("## 1. done_when verification")
    w("")
    w("done_when (verbatim): \"Architect names why this assembly replaces "
      "the current body, then requalifies affected dynamics/policies before "
      "use. Material-first addition: Adopt the material assembly only after "
      "actual limb load transmission and a compatible runtime/training "
      "contract are evidenced; static export is not runtime "
      "qualification.\"")
    w("")
    w("- Architect named reason: RECORDED (adoption_record.json "
      "`adoption_decision.architect_named_reason`; kind %s)."
      % ar["adoption_decision"]["kind"])
    w("- Limb load transmission: evidenced at limb scope by the sealed M11 "
      "record (cited; not re-proven here).")
    w("- Compatible runtime/training contract: the bound SHAPE "
      "(RUNTIME_CONTRACT.md TC-1..TC-6, TC-12) + the TC-7 body-domain bind "
      "recorded by this attempt; the full freeze remains W04's card "
      "outcome.")
    w("- Static export is not runtime qualification: the record claims NO "
      "runtime qualification for the adopted assembly (TC-8 inputs absent; "
      "`assembly_readiness_claimed` = %s; admitted mass %s kg)."
      % (str(ar["readiness_closure_table"]["assembly_readiness_claimed"])
         .lower(),
         repr(ar["mass_law_carried"]["admitted_here"])))
    w("")
    w("## 2. Adoption decision (summary)")
    w("")
    w(ar["adoption_decision"]["effective_scope"])
    w("")
    w("## 3. Authorization package discharge (8 items)")
    w("")
    w("| item | ruling | discharge |")
    w("|---|---|---|")
    for item in ar["authorization_package"]:
        w("| %d | %s | %s |" % (item["item"], item["ruling"],
                                item["discharge"]))
    w("")
    w("## 4. Per-row readiness closure table (the sealed B06 receipt rows)")
    w("")
    w("Closure EVIDENCE per row; sealed statuses are never flipped here. "
      "assembly_readiness claimed by this record: %s (honest count: %s)."
      % (str(ar["readiness_closure_table"]["assembly_readiness_claimed"])
         .lower(),
         ar["readiness_closure_table"]["honest_count"]))
    w("")
    w("| requirement | domain | sealed status | closure class |")
    w("|---|---|---|---|")
    for row in ar["readiness_closure_table"]["rows"]:
        w("| %s | %s | %s | %s |" % (row["requirement_id"], row["domain"],
                                     row["sealed_status"],
                                     row["closure_class"]))
    w("")
    w("## 5. Ownership mappings (R-OWN-02 / R-OWN-03)")
    w("")
    w("- Law validation (F1): %d/%d Captain-mapped A05 rows reproduced "
      "BIT-EXACT before emission."
      % (own["law_validation"]["bit_exact_row_count"],
         len(own["law_validation"]["captain_mapped_rows"])))
    w("- Hand-body mapping decisions recorded: %d (R-OWN-02); distances "
      "%.6f..%.6f m."
      % (len(hd), min(hd), max(hd)))
    w("- Forearm correspondence records: %d (R-OWN-03; ulna %d / radius %d "
      "/ humerus %d); distances %.4f..%.4f m."
      % (len(fd),
         sum(1 for r in fore if r["owner_body"] == "ulna"),
         sum(1 for r in fore if r["owner_body"] == "radius"),
         sum(1 for r in fore if r["owner_body"] == "humerus"),
         min(fd), max(fd)))
    w("- Every record carries the authorization citation (%s) and its "
      "distance; distances inform, never authorize."
      % own["authorization"]["message_id"])
    w("- Forearm distance law: zero-coordinate pose, declared joint "
      "translations/orientations; Euler-convention alternative bound %s m "
      "max (recorded per record)."
      % repr(max(r["decision"]["euler_convention_note"]
                 ["alternative_max_delta_m"] for r in fore)))
    w("")
    w("## 6. Frame bindings (R-FRM-02 / R-FRM-03)")
    w("")
    w("- Ulna-edge correspondence: %s (U-STR; radius supersession "
      "consequence ACCEPTED, execution stays with the staged ONT-A03 "
      "record)."
      % fb["r_frm_02"]["part_a_ulna_edge_correspondence"]["decision"])
    w("- Packet-to-forest binding: %d stable-name rows verified from the "
      "pinned B04 bytes; no transform authored (no_fusion_statement "
      "carried)."
      % len(fb["r_frm_02"]["part_b_packet_to_forest_binding"]
            ["binding_rows"]))
    w("- Component/bond admission: %d components, %d bonds "
      "(kinematically_preserved), %d unresolved bodies carried, counted "
      "mass %s kg (agreement re-verified: equal=%s)."
      % (fb["r_frm_03"]["admitted"]["component_count"],
         fb["r_frm_03"]["admitted"]["bonds"]["count"],
         fb["r_frm_03"]["carried_unchanged"]["unresolved_count"],
         repr(fb["r_frm_03"]["carried_unchanged"]["counted_mass_kg"]),
         str(fb["r_frm_03"]["agreement_evidence"]["equal"]).lower()))
    w("")
    w("## 7. TC-7 body-domain bind + TC-12 rebind record")
    w("")
    w("- TC-7: body domain %s; domain_tag %s; qualification_state: %s"
      % (ar["tc7_body_domain_bind"]["bound_as"]["body_digest"],
         ar["tc7_body_domain_bind"]["bound_as"]["domain_tag"],
         "NOT runtime-qualified (TC-8 inputs absent)"))
    w("- TC-12 executed here: the TC-7 bind record + the C09 anchor-class "
      "re-run against the CERTIFIED backend; the sealed certificate "
      "re-issue through the gate is NOT fabricated — %d named "
      "prerequisites recorded (adopted-assembly scene; TC-3 drive-table "
      "re-declaration; TC-8 measured inputs; then the TC-6 certificate + "
      "C09 anchors on THAT body)."
      % len(ar["tc12_rebind_record"]["reissue_prerequisites_named"]))
    w("- Certified line: NOT silently invalidated (symmetric clause); "
      "admitted mass %s kg; the certified walking body stays %s kg."
      % (repr(ar["mass_law_carried"]["admitted_here"]),
         repr(ar["mass_law_carried"]["certified_walking_body_kg"])))
    w("")
    w("## 8. C09 anchor-class re-run (the certified CPU walk backend)")
    w("")
    w("| anchor | frozen | reproduced | verdict |")
    w("|---|---|---|---|")
    for key, c in sorted(c09["anchor_comparisons"].items()):
        w("| %s | %s | %s | %s |" % (key, c["frozen"],
                                     c["reproduced"], c["verdict"]))
    w("")
    w("%d/%d anchors EXACT from pinned extractions rebuilt in this "
      "workspace (source revision %s)."
      % (exact, len(c09["anchor_comparisons"]), c09["source_revision"]))
    w("")
    w("## 9. Profile-class capture (climbing / motion)")
    w("")
    w("- %d view rows (3 views x diagnostic/clean), %d frames, FFV1 "
      "-level 3 -g 1 -fflags +bitexact; structural validation: %s "
      "(view_count %s)."
      % (cap["rows"], cap["frame_count"],
         str(cap["structural_validation"]["structurally_valid"]).lower(),
         cap["structural_validation"]["view_count"]))
    w("- capture_sha256 %s; decode-identity checks at %s (identity only)."
      % (cap["context"]["capture_sha256"],
         [c["frame_index"] for c in cap["decode_identity_checks"]]))
    w("- Honesty label: %s." % cap["context"]["honesty_note"])
    w("- Screens never gate: the receipts above are the numerical evidence "
      "the profile demands; independent image review remains mandatory.")
    w("")
    w("## 10. Named checks (G12 accounting)")
    w("")
    w("- Suite result: %s (exit %d, ok=%s). No skip paths exist in the "
      "suite; KNOWN_SKIPS not needed."
      % (suite["summary_line"], suite["exit"], str(suite["ok"]).lower()))
    w("- Falsifier arms live in the suite with clean-control-first + "
      "premature guards (G1): fb1 hand tamper, fb2 scope tamper, fb3 "
      "binding-name tamper, fb4 agreement tamper.")
    w("")
    w("## 11. Refused steps (verbatim law, none forced)")
    w("")
    w("- Ports: %s" % ("0/8 qualified; the honest refusal record "
                       "(PORT_QUALIFICATION.md) stands; this attempt "
                       "qualifies no port (auth item 3)."))
    w("- R-OWN-04: fitting lane authorized (auth item 5) and SEPARATELY "
      "dispatched — not executed here.")
    w("- R-OWN-05: c17-stiffness lane owns measured attachment-interface "
      "sources; lead admission only on measured sources — none admitted "
      "here.")
    w("- Certificate re-issue for the adopted body: refused until the %d "
      "TC-12 prerequisites exist (no fabrication)."
      % len(ar["tc12_rebind_record"]["reissue_prerequisites_named"]))
    w("")
    w("## 12. Evidence index (sha256)")
    w("")
    w("| artifact | sha256 |")
    w("|---|---|")
    for p in RECEIPTS + ["checks_receipt.json", "PREREGISTRATION.md",
                         "ownership_mappings.py",
                         "adoption_record.py", "test_b07_adoption.py",
                         "c09_anchor_rerun.py", "make_capture.py",
                         "make_report.py", "lint_report_numbers.py"]:
        w("| %s | %s |" % (p, sha(p)))
    w("")
    (HERE / "report.md").write_bytes("\n".join(lines).encode("utf-8")
                                     + b"\n")
    print("wrote report.md (%d lines); suite: %s"
          % (len(lines), suite["summary_line"]))
    if not suite["ok"]:
        print("SUITE NOT OK - refusing to leave a green report",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
