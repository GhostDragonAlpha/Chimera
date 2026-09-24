"""M07 propagation verifier: checks every preregistered matrix prediction.

Reads receipts (exporter/reader outputs produced by the CLI) and the fixtures,
recomputes admission independently from the work/ module copies, and records a
PASS/FAIL verdict per prediction. Nothing is fixed or tuned; failures are
reported as-is. Writes receipts/verify-results.json only.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
AG = HERE.parent
FIX = AG / "fixtures"
REC = AG / "receipts"

import material_volume_admission as admission  # work/ copy
import material_volume_body_export as exporter  # work/ copy

RESULTS = []


def check(case: str, claim: str, ok: bool, evidence: str) -> None:
    RESULTS.append({"case": case, "claim": claim, "verdict": "PASS" if ok else "FAIL",
                    "evidence": evidence})
    print(f"[{'PASS' if ok else 'FAIL'}] {case}: {claim} :: {evidence}")


def load_case(cid: str) -> dict:
    return json.loads((REC / f"case-{cid}-export.json").read_text(encoding="utf-8"))


def load_fixture(name: str):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def exit_code(cid: str) -> int:
    return int((REC / f"case-{cid}-export.exit").read_text().strip())


def canonical_hash(doc) -> str:
    return hashlib.sha256(json.dumps(doc, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True, allow_nan=False)
                          .encode("ascii")).hexdigest()


def fresh_admission(man, par) -> dict:
    return admission.build_admission_report(man, par)


def input_hash_checks(cid: str, man, par, grp) -> None:
    hashes = load_case(cid)["input_hashes"]
    check(cid, "input_hashes bind fixture documents (Q-HASH)",
          hashes["manifest_sha256"] == canonical_hash(man)
          and hashes["partition_sha256"] == canonical_hash(par)
          and hashes["body_groups_sha256"] == canonical_hash(grp),
          f"manifest={hashes['manifest_sha256'][:12]} partition={hashes['partition_sha256'][:12]} "
          f"groups={hashes['body_groups_sha256'][:12]}")


def no_mass_anywhere(cid: str, report: dict) -> bool:
    if report.get("body_groups") != []:
        return False
    return "mass_properties" not in json.dumps(report)


def main() -> int:
    print(f"admission module copy: {admission.__file__}")
    print(f"exporter module copy:  {exporter.__file__}")

    man1, par1, grp1 = (load_fixture("case-c1-manifest.json"),
                        load_fixture("case-c1-partition.json"),
                        load_fixture("case-c1-groups.json"))

    # ---------- F7 determinism ----------
    a = (REC / "case-c1-export.json").read_bytes()
    b = (REC / "case-c1-export-rerun.json").read_bytes()
    check("F7", "identical inputs -> byte-identical report", a == b,
          f"{len(a)} bytes, rerun {'IDENTICAL' if a == b else 'DIFFERS'}")

    # ---------- C1 happy path ----------
    r1 = load_case("c1")
    fresh1 = fresh_admission(man1, par1)
    check("C1", "export_status complete (Q-STATUSES)", r1["export_status"] == "complete",
          f"status={r1['export_status']}")
    check("C1", "CLI exit 0", exit_code("c1") == 0, f"exit={exit_code('c1')}")
    check("C1", "both bodies exported", [g["export_status"] for g in r1["body_groups"]]
          == ["exported", "exported"],
          f"{[g['body_id'] for g in r1['body_groups']]}")
    masses = {g["body_id"]: g["mass_properties"]["mass"]["value"] for g in r1["body_groups"]}
    check("C1", "masses 2 kg / 1 kg (coupon contract)", masses ==
          {"coupon-body-A": 2.0, "coupon-body-B": 1.0}, f"masses={masses}")
    check("C1", "root admission_status validation_only_admissible (Q-HASH)",
          r1["admission_status"] == "validation_only_admissible",
          f"status={r1['admission_status']}")
    check("C1", "root admission_report_sha256 binds freshly recomputed report (F6)",
          r1["admission_report_sha256"] == canonical_hash(fresh1),
          f"root={r1['admission_report_sha256'][:12]} fresh={canonical_hash(fresh1)[:12]}")
    body_hashes_ok = all(g["admission_report_sha256"] == canonical_hash(fresh1)
                         for g in r1["body_groups"])
    check("C1", "each exported body's admission_report_sha256 == root == fresh report (Q-HASH)",
          body_hashes_ok,
          f"body hashes {[g['admission_report_sha256'][:12] for g in r1['body_groups']]}")
    check("C1", "no unassigned cells flagged", r1["unassigned_cell_ids"] == []
          and r1["all_supplied_cells_assigned"] is True,
          f"unassigned={r1['unassigned_cell_ids']}")
    input_hash_checks("c1", man1, par1, grp1)

    # ---------- C2 duplicate cell ownership ----------
    r2 = load_case("c2")
    check("C2", "export_status refused (Q-INPUT/Q-REFUSED, F1)", r2["export_status"] == "refused",
          f"status={r2['export_status']}")
    check("C2", "reason names duplicate_cell_ownership", r2["reason_codes"] ==
          ["duplicate_cell_ownership"], f"reasons={r2['reason_codes']}")
    check("C2", "detail names the cell and both bodies",
          "cell-A" in r2["detail"] and "body-1" in r2["detail"] and "body-2" in r2["detail"],
          f"detail={r2['detail']!r}")
    check("C2", "no body records / no mass properties (F1)", no_mass_anywhere("c2", r2),
          f"body_groups={r2['body_groups']}")
    check("C2", "admission not_evaluated (refusal precedes recomputation)",
          r2["admission_status"] == "not_evaluated" and r2["admission_report_sha256"] is None,
          f"status={r2['admission_status']} hash={r2['admission_report_sha256']}")
    check("C2", "CLI exit 1", exit_code("c2") == 1, f"exit={exit_code('c2')}")
    input_hash_checks("c2", man1, par1, load_fixture("case-c2-groups.json"))

    # ---------- C2b duplicate body_id ----------
    r2b = load_case("c2b")
    check("C2b", "export_status refused", r2b["export_status"] == "refused",
          f"status={r2b['export_status']}")
    check("C2b", "reason names duplicate_body_id", r2b["reason_codes"] == ["duplicate_body_id"],
          f"reasons={r2b['reason_codes']}")
    check("C2b", "no body records / no mass properties (F1)", no_mass_anywhere("c2b", r2b),
          f"body_groups={r2b['body_groups']}")
    check("C2b", "admission not_evaluated", r2b["admission_status"] == "not_evaluated"
          and r2b["admission_report_sha256"] is None,
          f"status={r2b['admission_status']} hash={r2b['admission_report_sha256']}")
    check("C2b", "CLI exit 1", exit_code("c2b") == 1, f"exit={exit_code('c2b')}")

    # ---------- C3 unassigned cell ----------
    man3, par3, grp3 = (load_fixture("case-c3-manifest.json"),
                        load_fixture("case-c3-partition.json"),
                        load_fixture("case-c3-groups.json"))
    r3 = load_case("c3")
    fresh3 = fresh_admission(man3, par3)
    check("C3", "export_status partial with unassigned cells (Q-STATUSES/Q-UNASSIGNED)",
          r3["export_status"] == "partial" and r3["reason_codes"] == ["unassigned_cells"],
          f"status={r3['export_status']} reasons={r3['reason_codes']}")
    check("C3", "unassigned_cell_ids == [cell-C] (F2)", r3["unassigned_cell_ids"] == ["cell-C"],
          f"unassigned={r3['unassigned_cell_ids']}")
    rows = r3["unassigned_cells"]
    check("C3", "unassigned_cells row: resolved + explicit reason, never absorbed (F2)",
          rows == [{"cell_id": "cell-C", "assignment_status": "resolved",
                    "reason": "not_assigned_to_an_authored_body_group"}],
          f"rows={rows}")
    check("C3", "all_supplied_cells_assigned false",
          r3["all_supplied_cells_assigned"] is False,
          f"flag={r3['all_supplied_cells_assigned']}")
    masses3 = {g["body_id"]: g["mass_properties"]["mass"]["value"] for g in r3["body_groups"]}
    check("C3", "both groups still exported with correct masses (Q-UNASSIGNED)",
          [g["export_status"] for g in r3["body_groups"]] == ["exported", "exported"]
          and masses3 == {"coupon-body-A": 2.0, "coupon-body-B": 1.0},
          f"statuses={[g['export_status'] for g in r3['body_groups']]} masses={masses3}")
    serialized_groups = json.dumps(r3["body_groups"])
    check("C3", "cell-C appears in NO body record (not silently absorbed, F2)",
          "cell-C" not in serialized_groups, f"cell-C in groups payload: {'cell-C' in serialized_groups}")
    check("C3", "root admission binds fresh report; stays admissible (F6)",
          r3["admission_status"] == "validation_only_admissible"
          and r3["admission_report_sha256"] == canonical_hash(fresh3),
          f"root={r3['admission_report_sha256'][:12]} fresh={canonical_hash(fresh3)[:12]}")
    check("C3", "cell-C accounted in fresh admission report (never omitted from accounting)",
          fresh3["assignments"]["resolved_cell_ids"] == ["cell-A", "cell-B", "cell-C"],
          f"resolved={fresh3['assignments']['resolved_cell_ids']}")
    check("C3", "CLI exit 0 (partial is admissible output)", exit_code("c3") == 0,
          f"exit={exit_code('c3')}")
    input_hash_checks("c3", man3, par3, grp3)

    # ---------- C4 blocked (missing density) ----------
    man4, par4 = (load_fixture("case-c4-manifest.json"),
                  load_fixture("case-c4-partition.json"))
    r4 = load_case("c4")
    fresh4 = fresh_admission(man4, par4)
    check("C4", "fresh admission not_admitted with missing_density (Q-DENSITY)",
          fresh4["decision"] == "not_admitted" and "missing_density" in fresh4["reason_codes"],
          f"decision={fresh4['decision']} codes={fresh4['reason_codes']}")
    check("C4", "root export_status blocked (Q-BLOCK/Q-STATUSES)",
          r4["export_status"] == "blocked"
          and r4["reason_codes"] == ["reconstructed_mass_admission_required"],
          f"status={r4['export_status']} reasons={r4['reason_codes']}")
    check("C4", "root admission_status not_admitted, binds fresh report (F6)",
          r4["admission_status"] == "not_admitted"
          and r4["admission_report_sha256"] == canonical_hash(fresh4),
          f"root={r4['admission_report_sha256'][:12]} fresh={canonical_hash(fresh4)[:12]}")
    by_body = {g["body_id"]: g for g in r4["body_groups"]}
    good, bad = by_body["coupon-body-A"], by_body["coupon-body-B"]
    check("C4", "both group records not_exported, mass_properties null (F4)",
          good["export_status"] == "not_exported" and bad["export_status"] == "not_exported"
          and good["mass_properties"] is None and bad["mass_properties"] is None,
          f"A={good['export_status']} B={bad['export_status']}")
    check("C4", "BAD body blocking lists name cell-B with status missing_density (F5)",
          bad["blocking_cell_ids"] == ["cell-B"]
          and bad["blocking_assignment_statuses"] ==
          [{"cell_id": "cell-B", "status": "missing_density"}],
          f"blocking={bad['blocking_cell_ids']} statuses={bad['blocking_assignment_statuses']}")
    check("C4", "GOOD body blocking lists EMPTY - bad cell not attributed to good body (F3)",
          good["blocking_cell_ids"] == [] and good["blocking_assignment_statuses"] == [],
          f"blocking={good['blocking_cell_ids']} statuses={good['blocking_assignment_statuses']}")
    good_serialized = json.dumps(good)
    bad_serialized = json.dumps(bad)
    check("C4", "no status leak: GOOD record never mentions cell-B; BAD never mentions cell-A (F3)",
          "cell-B" not in good_serialized and "cell-A" not in bad_serialized,
          f"cell-B in GOOD: {'cell-B' in good_serialized}; cell-A in BAD: {'cell-A' in bad_serialized}")
    check("C4", "both bodies carry root admission_status",
          good["admission_status"] == bad["admission_status"] == r4["admission_status"],
          f"A={good['admission_status']} B={bad['admission_status']}")
    reduced4 = canonical_hash({"reason_codes": fresh4["reason_codes"],
                               "decision": fresh4["decision"]})
    full4 = canonical_hash(fresh4)
    bad_binds = ("reduced {decision,reason_codes}" if bad["admission_report_sha256"] == reduced4
                 else "full report" if bad["admission_report_sha256"] == full4 else "NEITHER")
    check("C4", "O1 measured: body-level admission_report_sha256 binding (decision request)",
          True, f"body hash={bad['admission_report_sha256'][:12]} binds: {bad_binds}; "
                f"full={full4[:12]} reduced={reduced4[:12]}")
    check("C4", "no default density substituted: BAD provenance absent (mass_properties null)",
          "density_kg_m3" not in json.dumps(bad.get("mass_properties")),
          "mass_properties is null")
    check("C4", "CLI exit 1", exit_code("c4") == 1, f"exit={exit_code('c4')}")
    input_hash_checks("c4", man4, par4, load_fixture("case-c4-groups.json"))

    # ---------- C5 mixed groups (unresolved cell-B) ----------
    man5, par5 = (load_fixture("case-c5-manifest.json"),
                  load_fixture("case-c5-partition.json"))
    r5 = load_case("c5")
    fresh5 = fresh_admission(man5, par5)
    check("C5", "fresh admission not_admitted: unresolved_assignments + incomplete_cell_ownership",
          fresh5["decision"] == "not_admitted"
          and fresh5["reason_codes"] == ["incomplete_cell_ownership", "unresolved_assignments"],
          f"decision={fresh5['decision']} codes={fresh5['reason_codes']}")
    check("C5", "root export_status blocked", r5["export_status"] == "blocked"
          and r5["admission_status"] == "not_admitted",
          f"status={r5['export_status']} adm={r5['admission_status']}")
    by_body5 = {g["body_id"]: g for g in r5["body_groups"]}
    good5, bad5 = by_body5["coupon-body-A"], by_body5["coupon-body-B"]
    check("C5", "BAD body blocking names cell-B status unresolved; GOOD body blocking EMPTY (F5/F3)",
          bad5["blocking_assignment_statuses"] == [{"cell_id": "cell-B", "status": "unresolved"}]
          and good5["blocking_assignment_statuses"] == [],
          f"B={bad5['blocking_assignment_statuses']} A={good5['blocking_assignment_statuses']}")
    good5s, bad5s = json.dumps(good5), json.dumps(bad5)
    check("C5", "bad cell does not corrupt good body's record: no cell-B in GOOD, no cell-A in BAD (F3)",
          "cell-B" not in good5s and "cell-A" not in bad5s,
          f"cell-B in GOOD: {'cell-B' in good5s}; cell-A in BAD: {'cell-A' in bad5s}")
    check("C5", "no mass properties anywhere in blocked report (F4)",
          all(g["mass_properties"] is None for g in r5["body_groups"]),
          f"{[g['mass_properties'] for g in r5['body_groups']]}")
    check("C5", "GOOD body record structure intact: owned_cell_ids preserved (uncorrupted)",
          good5["owned_cell_ids"] == ["cell-A"] and good5["reason_codes"] ==
          ["reconstructed_mass_admission_required"],
          f"owned={good5['owned_cell_ids']} reasons={good5['reason_codes']}")
    check("C5", "both bodies carry root admission_status (no leak)",
          good5["admission_status"] == bad5["admission_status"] == r5["admission_status"],
          f"A={good5['admission_status']} B={bad5['admission_status']}")
    check("C5", "CLI exit 1", exit_code("c5") == 1, f"exit={exit_code('c5')}")

    # ---------- C6 group claims absent cell ----------
    r6 = load_case("c6")
    fresh6 = fresh_admission(man1, par1)
    check("C6", "export_status refused naming unknown_group_cell_id + cell-Z (Q-REFUSED, F5)",
          r6["export_status"] == "refused" and r6["reason_codes"] == ["unknown_group_cell_id"]
          and "cell-Z" in r6["detail"],
          f"status={r6['export_status']} reasons={r6['reason_codes']} detail={r6['detail']!r}")
    check("C6", "admission IS recomputed and bound: status admissible, hash == fresh full report (F6)",
          r6["admission_status"] == "validation_only_admissible"
          and r6["admission_report_sha256"] == canonical_hash(fresh6),
          f"root={r6['admission_report_sha256'][:12]} fresh={canonical_hash(fresh6)[:12]}")
    check("C6", "admission hash equals C1's (same manifest/partition -> same fresh report)",
          r6["admission_report_sha256"] == r1["admission_report_sha256"],
          f"c6={r6['admission_report_sha256'][:12]} c1={r1['admission_report_sha256'][:12]}")
    check("C6", "no body records / no mass properties (F1)", no_mass_anywhere("c6", r6),
          f"body_groups={r6['body_groups']}")
    check("C6", "no exported body despite admissible partition (phantom claim refuses request)",
          r6["body_groups"] == [], "body_groups empty")
    check("C6", "CLI exit 1", exit_code("c6") == 1, f"exit={exit_code('c6')}")
    input_hash_checks("c6", man1, par1, load_fixture("case-c6-groups.json"))

    # ---------- Reader probes (U7-adjacent) ----------
    s1 = json.loads((REC / "probe-r1-reader.json").read_text(encoding="utf-8"))
    check("R1", "reader accepts complete report, surfaces masses/status/hashes",
          exit_ok("r1") == 0 and s1["export_status"] == "complete"
          and {b["body_id"]: b.get("mass_kg") for b in s1["bodies"]} ==
          {"coupon-body-A": 2.0, "coupon-body-B": 1.0},
          f"exit={exit_ok('r1')} bodies={[(b['body_id'], b.get('mass_kg')) for b in s1['bodies']]}")
    s2 = json.loads((REC / "probe-r2-reader.json").read_text(encoding="utf-8"))
    check("R2", "reader surfaces unassigned_cell_ids on partial report (U7-adjacent)",
          exit_ok("r2") == 0 and s2["unassigned_cell_ids"] == ["cell-C"]
          and s2["export_status"] == "partial",
          f"exit={exit_ok('r2')} unassigned={s2['unassigned_cell_ids']}")
    s3 = json.loads((REC / "probe-r3-reader.json").read_text(encoding="utf-8"))
    check("R3", "reader ACCEPTS blocked report: bodies with mass_properties null (U7)",
          exit_ok("r3") == 0 and s3["export_status"] == "blocked"
          and all(b["mass_properties"] is None for b in s3["bodies"])
          and s3["bodies"][0]["admission_status"] == "not_admitted",
          f"exit={exit_ok('r3')} bodies={[(b['body_id'], b['export_status']) for b in s3['bodies']]}")
    s4 = json.loads((REC / "probe-r4-reader.json").read_text(encoding="utf-8"))
    check("R4", "reader ACCEPTS refused report: empty bodies, admission_status surfaced (U7)",
          exit_ok("r4") == 0 and s4["export_status"] == "refused" and s4["bodies"] == []
          and s4["admission_status"] == "not_evaluated",
          f"exit={exit_ok('r4')} bodies={s4['bodies']} adm={s4['admission_status']}")
    check("R5", "reader REJECTS blocked-with-mass tamper (guard vs F3/F4)",
          exit_ok("r5") == 2 and "blocked_group_has_mass" in
          (REC / "probe-r5-reader.stderr").read_text(encoding="utf-8"),
          f"exit={exit_ok('r5')} stderr={(REC / 'probe-r5-reader.stderr').read_text(encoding='utf-8').strip()!r}")

    fails = [row for row in RESULTS if row["verdict"] == "FAIL"]
    (REC / "verify-results.json").write_text(json.dumps(
        {"results": RESULTS, "pass": len(RESULTS) - len(fails), "fail": len(fails)},
        indent=2) + "\n", encoding="utf-8")
    print(f"\nTOTAL {len(RESULTS)} checks: {len(RESULTS) - len(fails)} PASS, {len(fails)} FAIL")
    return 1 if fails else 0


def exit_ok(probe: str) -> int:
    text = (REC / f"probe-{probe}-reader.exit").read_text().strip()
    return int(text) if text else -1


if __name__ == "__main__":
    sys.exit(main())
