"""W4 quote verification: every quote in the ERRATUM section of
CAMPAIGN_REPORT.md is checked (whitespace-normalized, since receipts wrap
lines) against the archived receipt copies in receipts/.

Run:  python verify_quotes.py   (from impl/W4_erratum/)
Exit 0 = all quotes verified; exit 1 = any quote not found verbatim.
"""
import re
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def main() -> int:
    files = {
        p.name: norm(p.read_text(encoding="utf-8"))
        for p in (ROOT / "receipts").glob("*.md")
    }
    checks = [
        ("M01_reproduce_report.md", "Falsifier status: **none fired.** F-M01-1…6 all quiet."),
        ("M01_reproduce_report.md", 'that is the pre-declared "finding candidate" outcome, not a reproduction failure'),
        ("M01_reproduce_report.md", "fixed before any frozen-rev run"),
        ("M01_reproduce_report.md", "no legacy test exercises the reader; exporter-side unsupported status is what is covered"),
        ("M01_reproduce_report.md", "blocked/refused/`not_exported` group branches (including `blocked_group_has_mass`) exist and are untested."),
        ("M01_reproduce_report.md", "unsupported authority without mass reads"),
        ("M02_multicell_report.md", "NOT FIRED (after comparator corrections, §6)"),
        ("M02_multicell_report.md", "Two comparator (my own test-harness) defects fired F6 spuriously during comparison; both were preserved before correction, per the frozen protocol"),
        ("M02_multicell_report.md", "No exporter/compiler/admission defect was found."),
        ("M03_scale_report.md", "falsifier FIRED on 7 quantities"),
        ("M03_scale_report.md", "any quantity deviating beyond tolerance, or any refusal/error on schema-valid input"),
        ("M03_scale_ERRATA.md", "Root cause: agent-side anchor derivation errors, NOT exporter defects."),
        ("M03_scale_ERRATA.md", "The frozen prereg's falsifier FIRED on 7 quantities (E1: 4, E2: 3)."),
        ("M04_rigid_report.md", "did not fire against the exporter; it fired once against my expectation code"),
        ("M04_rigid_report.md", "any quantity of any run outside tolerance, or refusal/non-complete status on schema-valid fixtures"),
        ("M04_rigid_report.md", "adding tr(C) to every entry instead of tr(C)*delta_ij"),
        ("M04_rigid_report.md", "A whole-body Monte Carlo (assumption-free) sided with the exporter"),
        ("M04_rigid_report.md", "fired exactly once — against my own expectation code, not the exporter (iteration 2"),
        ("M05_order_report.md", "| **Falsifiers** | None fired."),
        ("M05_order_report.md", "anchor-side artifact, not a pipeline deviation"),
        ("M05_order_report.md", "Harness bug, not pipeline behavior"),
        ("M06_malformed_report.md", "FINAL RESULT: **falsifier did NOT trip** — no malformed case exported mass."),
        ("M06_malformed_report.md", "HARNESS ARTIFACT, not a tool defect"),
        ("M06_malformed_report.md", "D-1 (DEFECT — SILENT-PASS, exit-signal class)"),
        ("M06_malformed_report.md", "EXIT-DEVIATION / matrix erratum"),
        ("M06_malformed_report.md", "misderived at freeze time"),
        ("M06_malformed_report.md", "Severity: NOT mass leakage (no mass emitted; refusal named in the report body); it is an exit-classification defect"),
        ("M06_malformed_report.md", "any case where invalid input yields a successful export = critical defect"),
        ("M07_ownership_report.md", "No falsifier fired."),
        ("M07_ownership_report.md", "measured, not a falsifier hit"),
        ("M07_ownership_report.md", "agent-side, not a product defect"),
        ("M08_robustness_report.md", "all three frozen-rule DEFECT-CANDIDATEs are diagnosed below to harness, derivation, or fixture causes."),
        ("M08_robustness_report.md", "Zero implementation defects found."),
        ("M08_robustness_report.md", "derivation omission"),
        ("M08_robustness_report.md", "INVALID RUNG"),
        ("M08_robustness_report.md", "no anatomical mesh is tested"),
        ("M09_diagnostic_report.md", "F1 (writes/modifies inputs): CLEAN."),
        ("M09_diagnostic_report.md", "F2 (displays readiness != false): CLEAN"),
        ("M09_diagnostic_report.md", "F3 (invents a status): CLEAN"),
        ("M09_diagnostic_report.md", "Defect found and fixed in MY tool during the campaign"),
        ("M09_diagnostic_report.md", "summary thinning, not a defect"),
        ("M10_validator_report.md", "no unplanned-bypass fixture exists in the probe set"),
        ("M10_validator_report.md", "The frozen membrane's prediction held on all points."),
        ("M10_validator_report.md", "ACCEPT — as PREDICTED in the frozen preregistration."),
        ("M10_validator_report.md", "the pre-declared static LIMIT L2"),
        ("M10_validator_report.md", "the one ACCEPT under adversarial pressure is the pre-named limit class, measured and mitigated"),
        ("M10_validator_report.md", "(presence, 64-lowercase-hex, root↔body consistency on `complete`, optional recomputation against a supplied admission document)"),
        ("B2a_review_m09_report.md", "all three M09 falsifiers (F1/F2/F3) clean under my runs"),
        ("B2a_review_m09_report.md", "I fixed nothing"),
        ("B2a_review_m09_report.md", "All three defects require hostile input that the READER accepts"),
        ("B2a_review_m09_report.md", "complete/partial/blocked/unsupported/refused -> 0"),
        ("B3_roundtrip_report.md", "Falsifier ledger: F-B3-1 held · F-B3-2 FIRED (42 rows, classified §4) · F-B3-3 held · F-B3-4 held."),
        ("B3_roundtrip_report.md", "DEFECT-CLASS (contract-contradicting information loss; U7-sibling, defect/change queue — NOT fixed here, tools/ read-only)"),
        ("B3_roundtrip_report.md", "150 PASS_EXACT / 42 DROP / 0 DIFF"),
        ("B4_crosscheckout_report.md", "No falsifier fired (F1, F2, F3, F4 all clean)."),
        ("B4_crosscheckout_report.md", "166 EXPECTED · 0 UNEXPECTED · 16 UNPROMISED"),
        ("B5_subdivision_report.md", "0 falsifiers fired"),
        ("B5_subdivision_report.md", "FALSIFIER: never fired. DONE."),
        ("B5_subdivision_report.md", "Preserved harness findings (not exporter defects, kept per preserve-failures law)"),
        ("B6_tensors_report.md", "C route_C_origin rel = 2.936e-12 > frozen 1e-12"),
        ("B6_tensors_report.md", "Preserved exactly as measured in"),
        ("B6_tensors_report.md", "not tuned away."),
        ("B6_tensors_report.md", "B6 derivation error: **NO**"),
        ("B6_tensors_report.md", "Exporter defect: **NO**"),
        ("B6_tensors_report.md", "Instrument/tolerance defect: **YES**"),
        ("B6_tensors_report.md", "the bound's derivation was mine, and it was wrong"),
        ("B6_tensors_report.md", "The FAIL verdict stands on the record"),
        ("B7_faultinjection_report.md", "any predicted-DETECTED row that passes silently is the headline finding"),
        ("B7_faultinjection_report.md", "**HELD.** No predicted-detectable mutation passed silently."),
        ("B7_faultinjection_report.md", "8 detected / 9 missed / 0 surprises / 0 falsified."),
        ("B7_faultinjection_report.md", "reader, PATH-DIFFERS — finding F6"),
        ("B7_faultinjection_report.md", "`admission_report_sha256` and `input_hashes` are computed honestly at generation and copied through unverified at consumption; no consumer can recompute them without the original inputs."),
        ("B7_faultinjection_report.md", "A regeneration-diff would have flagged 15/15 report-level mutations"),
        ("B7_faultinjection_report.md", "no such check exists"),
        ("B7_faultinjection_report.md", "as an uncaught numpy `ValueError` traceback instead of the reader's named `ExportInputError` discipline"),
        ("B7x_validator_probe_report.md", "5 ACCEPT / 4 REJECT — every outcome matched its prediction; falsifier held (§4); zero surprises."),
        ("B7x_validator_probe_report.md", "a tamper applied UNIFORMLY to root and all body hashes (or to `input_hashes`) passes R4's static form/consistency checks"),
        ("B7x_validator_probe_report.md", "as deployed (document optional) it stays open."),
        ("B7x_validator_probe_report.md", "**R4(d)'s recomputation path does not rescue the value class:**"),
        ("B7x_validator_probe_report.md", "the hash binds the admission *document*, not the report's mass values — editing body values leaves the binding valid."),
        ("B7x_validator_probe_report.md", "any mutation that keeps every field well-formed and internally consistent is indistinguishable from an honest report without reference documents"),
        ("B8_fixes_fixes.md", "NOT HIT"),
        ("B8_fixes_fixes.md", "17/17 tests green, genuine outputs byte-identical"),
        ("B9_doccheck_report.md", "Falsifier: any documented command that fails or any promised behavior absent. NOT FIRED at the level of executable claims."),
        ("material_volume_export_verification_receipt.md", "| U7 | reader behavior on `blocked` / `refused` reports in the integrated verification (legacy tests cover `unsupported`) |"),
        ("material_volume_export_verification_receipt.md", "anything beyond the two synthetic coupons: no anatomical, mechanical, or dynamics claim is tested anywhere"),
        ("material_volume_export_verification_receipt.md", "falsifier V3-F FIRED (preserved)"),
    ]
    fails = 0
    for fname, needle in checks:
        if fname not in files:
            print(f"MISSING FILE {fname}")
            fails += 1
            continue
        if norm(needle) not in files[fname]:
            print(f"QUOTE NOT FOUND in {fname}: {needle[:100]}")
            fails += 1
    print(f"{len(checks)} quotes checked, {fails} failures")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
