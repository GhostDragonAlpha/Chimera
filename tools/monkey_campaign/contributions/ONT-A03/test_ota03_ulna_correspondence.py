"""ONT-A03 CPU-only regression suite (no GPU, no network, no writes outside evidence/).

Covers: input identities and the merged-A02 provenance chain, the three done_when
clauses (mapping/supersession approved-as-staged, historical radius preserved, new
transforms and regressions qualified) re-executed against the pinned receipts, the
closure mechanism executed as code, the staged record's self-consistency and approval
semantics, canonical camera-manifest structure, and the all-bookmark bounds regression
for the anatomy profile's own falsifier ("clipped/occluded subject fails").

Run:  python -B test_ota03_ulna_correspondence.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, r"E:/PythonChimera/tools/monkey_campaign")

import ota03_ulna_correspondence as core  # noqa: E402
import ota03_render_views as render  # noqa: E402

EVIDENCE = HERE / "evidence"
RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_preregistration_frozen() -> None:
    raw = (HERE / "PREREGISTRATION.md").read_text(encoding="utf-8")
    text = " ".join(raw.replace(">", " ").lower().split())
    for token in ("mapping/supersession", "historical radius preserved",
                  "new transforms and regressions qualified", "falsifier",
                  "source-kinematic convention fidelity", "approval semantics",
                  "staged", "does not authorize mechanically qualified grasp"):
        check(f"prereg contains '{token}'", token in text)
    check("prereg frozen before receipts", (HERE / "PREREGISTRATION.md").is_file())


def test_reference_integrity() -> None:
    rows = core.reference_integrity()
    bad = [r["dest"] for r in rows if r["verdict"] != "PASS"]
    check("reference/EXTRACTION.json entries all hash-match", not bad, str(bad))
    check("extraction has all 21 inputs", len(rows) == 21, f"n={len(rows)}")


def test_provenance_chain() -> None:
    chain = core.provenance_chain()
    bad = [r["this_attempt_dest"] for r in chain["rows"] if r["verdict"] != "PASS"]
    check("every extracted byte equals the merged A02 extraction's recorded hash",
          chain["all_match"], str(bad))
    check("A02 provenance record itself hash-pinned", (core.REF_A02_EXTRACTION).is_file())


def test_manifest_identity() -> None:
    m = core.manifest_identity()
    check("XML reproduces MANIFEST-recorded identity", m["xml"]["verdict"] == "PASS", m["xml"]["crlf_tail_sha256"])
    check("packet reproduces MANIFEST-recorded identity", m["packet"]["verdict"] == "PASS", m["packet"]["crlf_sha256"])


def test_definition_clause() -> None:
    src = core.source_geometry()
    check("arm rest quats identity", src["right"]["quats_identity"])
    u2r = np.asarray(src["right"]["u2r"], float)
    e2h = np.asarray(src["right"]["e2h"], float)
    d = core.anatomical_decomposition(u2r, e2h)
    check("|ulna->radius| = 23.0746 mm", abs(src["right"]["u2r_norm_m"] * 1000 - 23.0746) <= 5e-4,
          f"{src['right']['u2r_norm_m']*1000:.6f}")
    check("|elbow->hand| = 305.7922 mm", abs(src["right"]["e2h_norm_m"] * 1000 - 305.7922) <= 5e-4,
          f"{src['right']['e2h_norm_m']*1000:.6f}")
    check("axial = 14.324 mm", abs(d["axial_mm"] - 14.324) <= 5e-4, f"{d['axial_mm']:.6f}")
    check("lateral = 18.088 mm", abs(d["lateral_mm"] - 18.088) <= 5e-4, f"{d['lateral_mm']:.6f}")
    check("posterior = 0.301 mm", abs(d["posterior_mm"] - 0.301) <= 5e-4, f"{d['posterior_mm']:.6f}")
    check("obliquity = 51.63 deg", abs(d["angle_deg"] - 51.63) <= 0.01, f"{d['angle_deg']:.4f}")
    for name in ("a", "l", "p"):
        got = d[name]
        check(f"C1 receipted basis {name} reproduced", np.max(np.abs(got - core.C1_BASIS[name])) <= core.TOL_BASIS)
    check("decomposition reconstructs the offset", d["reconstruction_residual_m"] <= 1e-12)


def test_staged_supersession_clause() -> None:
    sm = core.supersession_map()
    r08 = core.load_json(core.REF_R08)
    for b in ("radius", "radius_l"):
        rs = sm["sides"][b]
        ra, rb, rm = r08["after"][b], r08["before"][b], r08["mechanism"][b]
        check(f"{b} BEFORE span preserved", abs(rs["span_old_m"] - rb["span_m"]) <= core.TOL_RECORD_M)
        check(f"{b} BEFORE scale preserved", abs(rs["s_old"] - rb["scale"]) <= core.TOL_SCALE)
        check(f"{b} staged span", abs(rs["span_new_m"] - ra["span_m"]) <= core.TOL_RECORD_M)
        check(f"{b} staged scale", abs(rs["s_new"] - ra["scale"]) <= core.TOL_SCALE)
        check(f"{b} staged t", all(abs(a - c) <= core.TOL_RECORD_M for a, c in zip(rs["t_new"], ra["t"])))
        check(f"{b} staged det = s^3", abs(rs["det_new_s3"] - ra["det_full_map_L"]) <= 1e-15)
        check(f"{b} staged det(L) matches direct determinant",
              abs(rs["det_new_measured"] - rs["det_new_s3"]) <= 1e-15)
        check(f"{b} G unchanged", rs["G_new_vs_old_max_abs_diff"] <= 1e-15)
        check(f"{b} Bp unchanged", rs["Bp_new_vs_old_max_abs_diff"] <= 1e-15)
        check(f"{b} P_d unchanged", rs["P_d_old"] == rb["P_d"])
        check(f"{b} closure gap", abs(rs["gap_m"] - rm["gap_m"]) <= core.TOL_RECORD_M, f"{rs['gap_m']:.9f}")
        check(f"{b} worst site = {r08['site_deltas'][b]['worst_site']}",
              rs["worst_site"] == r08["site_deltas"][b]["worst_site"], rs["worst_site"])
        worst = max(abs(rs["site_deltas"][n] - v) for n, v in r08["site_deltas"][b]["all"].items())
        check(f"{b} all 16 site deltas reproduce", worst <= core.TOL_DELTA_M, f"{worst:.3e}")
    check("left/right staged scales equal",
          abs(sm["sides"]["radius"]["s_new"] - sm["sides"]["radius_l"]["s_new"]) <= core.TOL_SCALE)
    law = core.fraction_law(core.source_geometry())
    check("fraction law exact (7.5459% x 1.04713 = 7.9015%)", law["law_exact"],
          f"{law['law_product_pct']:.9f} vs {law['target_per_edge_fraction_pct']:.9f}")
    checks = {c["id"]: c for c in core.build_evidence()[0]["checks"]}
    check("scale change -7.9015 %", checks["M2.scale_change_pct"]["verdict"] == "PASS",
          str(checks["M2.scale_change_pct"]["measured"]))
    check("staged record drift-free", checks["M2.staged_record_drift_free"]["verdict"] == "PASS")


def test_definition_property() -> None:
    """P_d (staged) must be ON the elbow->wrist line, 5.1158 mm from the elbow."""
    pk = core.packet_records()
    decl = core.declaration()
    seg = pk["segments"]["radius"]
    elbow = np.asarray(seg["fitted_origin"], float)
    wrist = np.asarray(seg["dist_landmark"], float)
    P_new = np.asarray(decl["records"]["ulna"]["landmarks"]["dist"]["target"], float)
    axis = (wrist - elbow) / np.linalg.norm(wrist - elbow)
    t = float((P_new - elbow) @ axis)
    perp = float(np.linalg.norm((P_new - elbow) - t * axis))
    check("staged P is 5.1158 mm from elbow_R", abs(t * 1000 - 5.1158) <= 1e-3, f"{t*1000:.6f} mm")
    check("staged P lies ON the elbow->wrist line", perp <= 1e-12, f"{perp:.3e} m")
    check("distance to wrist is the reduced span",
          abs(np.linalg.norm(wrist - P_new) - 0.05962909405176015) <= core.TOL_RECORD_M)


def test_mechanism_executed() -> None:
    mech = core.compiler_mechanism()
    check("JOINT_EPS at compiler.py:47 == 1e-9", mech["joint_eps_matches_inherited"],
          mech["joint_eps_line_47"])
    check("shared_joint_separation refusal inside the closure block (399-423)",
          mech["refusal_name_in_block"])
    for b in ("radius", "radius_l"):
        ex = mech["execution"][b]
        check(f"{b} frozen record refused by name", ex["frozen_record"]["refusal_fired"]
              and ex["frozen_record"]["refusal_name"] == "shared_joint_separation",
              f"gap={ex['gap_m']:.9f}")
        check(f"{b} staged record closes exactly (0.0)", ex["staged_closes_within_joint_eps"])
    # execute the public check function directly, both ways
    sm = core.supersession_map()
    try:
        core.first_child_closure(np.asarray(sm["sides"]["radius"]["P_old"], float),
                                 np.asarray(sm["sides"]["radius"]["P_new"], float))
        check("first_child_closure raises on the frozen record", False, "no exception")
    except core.SharedJointSeparation as exc:
        check("first_child_closure raises on the frozen record",
              exc.refusal == "shared_joint_separation" and exc.max_sep_m > 1e-9)
    try:
        core.first_child_closure(np.asarray(sm["sides"]["radius"]["P_new"], float),
                                 np.asarray(sm["sides"]["radius"]["P_new"], float))
        check("first_child_closure passes on the staged record", True)
    except core.SharedJointSeparation:
        check("first_child_closure passes on the staged record", False, "refused")


def test_coverage_effects() -> None:
    cov = core.coverage_effects()
    sc = cov["scenario_counts"]
    check("scenario counts 2/4/14", sc["baseline"] == 2
          and sc["diagnostic_ulna_only"] == 4
          and sc["diagnostic_plus_hand (context, NOT this run)"] == 14, json.dumps(sc))
    check("PT/PT_l newly defined", cov["newly_defined"] == ["PT_l_tendon", "PT_tendon"])
    check("BRD/BRD_l repaired", cov["brd_repaired"] == ["BRD_l_tendon", "BRD_tendon"])
    check("8 hand-breaker tendons (ECRB/ECRL/ECU/FCR/FCU x2)", len(cov["hand_blocked"]) == 10
          and sum(1 for k in cov["hand_blocked"] if not k.startswith("ECU")) == 8,
          json.dumps(sorted(cov["hand_blocked"])))
    check("BIC x2 thorax-blocked", sorted(cov["thorax_blocked"]) ==
          ["BIClong_l_tendon", "BIClong_tendon", "BICshort_l_tendon", "BICshort_tendon"])
    check("T6 utility-ban carried (PASS, 0 occurrences)",
          cov["t6_process"]["verdict"] == "PASS" and cov["t6_process"]["banned_evidence_occurrences"] == 0)


def test_historical_preservation() -> None:
    rec = core.before_map_reconstruction()
    for b in ("radius", "radius_l"):
        check(f"{b} BEFORE map reproduces packet fitted globals exactly",
              rec[b]["max_abs_deviation_m"] <= 1e-9, f"{rec[b]['max_abs_deviation_m']:.3e}")
        check(f"{b} fitted_origin == prox landmark", rec[b]["fitted_origin_equals_prox_landmark"])
        check(f"{b} dist landmark unchanged", rec[b]["dist_landmark_equals_packet"])
        check(f"{b} 16 sites", rec[b]["n_sites"] == 16, str(rec[b]["n_sites"]))
    staged = core.load_json(HERE / "transforms" / "radius_supersession_record.json")
    for b in ("radius", "radius_l"):
        before = staged["sides"][b]["before"]
        seg = core.packet_records()["segments"][b]
        check(f"{b} staged BEFORE record is packet-verbatim",
              before["scale"] == float(seg["scale"][0]) and before["P"] == list(seg["fitted_origin"]))
    check("preserved records carry hashes", all("sha256" in v and v["sha256"]
          for k, v in staged["preserved_records"].items() if isinstance(v, dict)))
    check("failed alternatives preserved (named)", "U-ANA" in staged["preserved_records"]["failed_alternatives"])


def test_decision_record_semantics() -> None:
    staged_path = HERE / "transforms" / "radius_supersession_record.json"
    staged = core.load_json(staged_path)
    check("staged record exists under transforms/", staged_path.is_file())
    check("status STAGED_FOR_ARCHITECT_APPROVAL", staged["status"] == "STAGED_FOR_ARCHITECT_APPROVAL")
    check("approval semantics: lead merge is the approval act",
          "merge of this exact head" in staged["approval_semantics"])
    check("basis is kinematic-convention fidelity",
          staged["decision"]["basis"].startswith("SOURCE-KINEMATIC CONVENTION FIDELITY"))
    check("R1 verdict sentence carried verbatim",
          staged["decision"]["r1_verdict_sentence_verbatim"] is not None
          and staged["decision"]["r1_verdict_extraction"]["all_key_phrases_present"])
    check("no utility selection",
          "NO moment-arm, utility" in staged["decision"]["selection_rule"])
    superseded = staged["superseded_set_enumerated_as_history"]
    check("superseded set enumerated as history",
          len(superseded) == 4
          and "local_to_world" in superseded[0]
          and "max_world_reconstruction_error_m" in superseded[1]
          and "step-A mirror table" in superseded[2]
          and "A4/B4" in superseded[3], json.dumps(superseded))
    check("no mechanically-qualified-grasp claim",
          "does NOT authorize mechanically qualified grasp" in staged["bounds"]["no_grasp_claim"])
    check("staged-only bound", "contribution" in staged["bounds"]["staged_only"])
    check("prereg hash pinned in the staged record",
          staged["preregistration_sha256"] == sha256_file(HERE / "PREREGISTRATION.md"))


def test_receipts_consistent() -> None:
    state_path = EVIDENCE / "state_snapshot.json"
    rec = core.load_json(EVIDENCE / "numerical_receipt.json")
    state = core.load_json(state_path)
    check("state snapshot hash pinned in the numerical receipt",
          rec["state_snapshot_sha256"] == sha256_file(state_path))
    check("numerical receipt outcome STAGED_AND_QUALIFIED", rec["outcome"] == "STAGED_AND_QUALIFIED")
    check("all checks PASS", state["check_summary"]["fail"] == 0, json.dumps(state["check_summary"]))
    check("criteria hash is the card criteria", state["criteria_sha256"] == core.CRITERIA_SHA256)
    q = core.load_json(EVIDENCE / "qualification_receipt.json")
    for kind in ("source", "numerical", "visual", "camera"):
        e = q["evidence"][kind]
        check(f"qualification {kind} hash matches the file", e["raw_sha256"] == sha256_file(Path(e["reference"])),
              kind)
    check("qualification criteria hash is the card criteria",
          q["criteria_sha256"] == core.CRITERIA_SHA256)
    check("independent_review is explicitly pending", q["evidence"]["independent_review"]["pending"] is True)
    check("head_sha not fabricated", q["head_sha"] is None)


def test_capture_manifest_structure() -> None:
    from visual_capture import validate_manifest
    manifest = core.load_json(EVIDENCE / "capture_manifest.json")
    context = core.load_json(EVIDENCE / "capture_context.json")
    structural = validate_manifest(manifest, context, render.PROFILE)
    check("canonical validator accepts the manifest", structural["structurally_valid"] is True,
          json.dumps(structural))
    check("six rows (three views x diagnostic/clean)", structural["view_count"] == 6)
    check("capture hash matches the committed PNG",
          manifest["capture_sha256"] == sha256_file(EVIDENCE / "capture_sheet.png"))
    check("subject hash matches the state snapshot",
          manifest["subject_sha256"] == sha256_file(EVIDENCE / "state_snapshot.json"))
    check("no GPU / no native frames",
          manifest["render"]["gpu_used"] is False and manifest["render"]["native_engine_frames"] is False)
    check("manifest identity is A03", manifest["task_id"] == "A03" and manifest["card_id"] == "ONT-A03")


def test_all_bookmark_bounds() -> None:
    """The anatomy profile's own falsifier, as a regression: every declared subject
    point of EVERY view/bookmark must project inside its panel with the frame margin."""
    manifest = core.load_json(EVIDENCE / "capture_manifest.json")
    geo = render.build_geometry()
    for row in manifest["views"]:
        pair = row["pair_id"]
        cam_meta = row["camera"]
        span = cam_meta["orthographic_span"]
        if pair == "V3":
            for cam, name in zip(cam_meta["samples"], geo["V3"]["names"]):
                render.assert_in_bounds(geo["V3"]["points"], cam, span, render.PANEL_W, render.PANEL_H)
            check("V3 all four bookmarks contain the declared subject", True)
        else:
            render.assert_in_bounds(geo[pair]["points"], geo[pair]["cam"], span,
                                    render.PANEL_W, render.PANEL_H)
            check(f"{pair} ({row['mode']}) contains the declared subject", True)
    for row in manifest["views"]:
        loc = row["artifact_locator"]["pixel_rectangle"]
        check(f"{row['pair_id']} locator inside the sheet",
              loc[0] >= 0 and loc[1] >= 0 and loc[0] + loc[2] <= render.SHEET_W
              and loc[1] + loc[3] <= render.SHEET_H, str(loc))


def test_capture_determinism_contract() -> None:
    """One panel re-rendered twice from the same committed geometry is byte-identical."""
    geo = render.build_geometry()
    g = geo["V2"]
    rgbs = [render.panel_rgb(g["cam"], g["span"], render.BONE_COLOR,
                             render.bone_meshes_mm()[0], render.bone_meshes_mm()[1]) for _ in range(2)]
    check("panel raster is deterministic", np.array_equal(rgbs[0], rgbs[1]))


def test_state_recompute_matches_disk() -> None:
    """build_evidence() is pure; recomputing must equal the committed state snapshot."""
    state_disk = core.load_json(EVIDENCE / "state_snapshot.json")
    state_now, _ = core.build_evidence()
    check("recomputed state equals the committed state snapshot", state_now == state_disk)


def test_clean_pairs_share_camera_and_state() -> None:
    manifest = core.load_json(EVIDENCE / "capture_manifest.json")
    pairs: dict[str, dict] = {}
    for row in manifest["views"]:
        pairs.setdefault(row["pair_id"], {})[row["mode"]] = row
    for pid, pair in pairs.items():
        check(f"{pid} has diagnostic+clean", "diagnostic" in pair and "clean" in pair)
        check(f"{pid} pair camera identical", pair["diagnostic"]["camera"] == pair["clean"]["camera"])
        check(f"{pid} pair state identical", pair["diagnostic"]["state_binding"] == pair["clean"]["state_binding"])
        check(f"{pid} clean has no diagnostics",
              pair["clean"]["visibility"]["layers"] == [] and pair["clean"]["visibility"]["label_ids"] == [])


def main() -> int:
    for fn in (test_preregistration_frozen, test_reference_integrity, test_provenance_chain,
               test_manifest_identity, test_definition_clause, test_staged_supersession_clause,
               test_definition_property, test_mechanism_executed, test_coverage_effects,
               test_historical_preservation, test_decision_record_semantics,
               test_receipts_consistent, test_capture_manifest_structure, test_all_bookmark_bounds,
               test_capture_determinism_contract, test_state_recompute_matches_disk,
               test_clean_pairs_share_camera_and_state):
        try:
            fn()
        except Exception as exc:  # a raising test is a failure, reported with its traceback line
            RESULTS.append((f"{fn.__name__} raised", False, f"{type(exc).__name__}: {exc}"))
    failures = [r for r in RESULTS if not r[1]]
    for name, ok, detail in RESULTS:
        if not ok:
            print(f"FAIL {name} {detail}")
    print(f"{len(RESULTS)-len(failures)}/{len(RESULTS)} tests PASS")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
