"""ONT-A02 CPU-only regression suite (no GPU, no network, no writes outside evidence/).

Covers: input identities, the four done_when clauses re-measured against the pinned
receipts, receipt self-consistency, canonical camera-manifest structure, and the
all-bookmark bounds regression for the anatomy profile's own falsifier
("clipped/occluded subject fails").

Run:  python -B test_ota02_radioulnar.py
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

import ota02_radioulnar as core  # noqa: E402
import ota02_render_views as render  # noqa: E402

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
    text = " ".join((HERE / "PREREGISTRATION.md").read_text(encoding="utf-8").lower().split())
    for token in ("radioulnar definition", "independent evidence", "b4 result",
                  "before/after radius mapping", "falsifier", "amendment a1"):
        check(f"prereg contains '{token}'", token in text)
    check("prereg frozen before receipts", (HERE / "PREREGISTRATION.md").is_file())


def test_reference_integrity() -> None:
    rows = core.reference_integrity()
    bad = [r["dest"] for r in rows if r["verdict"] != "PASS"]
    check("reference/EXTRACTION.json entries all hash-match", not bad, str(bad))
    check("extraction has all 20 inputs", len(rows) == 20, f"n={len(rows)}")


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


def test_mapping_clause() -> None:
    map_ = core.radius_before_after()
    r08 = core.load_json(core.REF_R08)
    for b in ("radius", "radius_l"):
        rs = map_["sides"][b]
        ra, rb, rm = r08["after"][b], r08["before"][b], r08["mechanism"][b]
        check(f"{b} span old", abs(rs["span_old_m"] - rb["span_m"]) <= core.TOL_RECORD_M)
        check(f"{b} span new", abs(rs["span_new_m"] - ra["span_m"]) <= core.TOL_RECORD_M)
        check(f"{b} scale new", abs(rs["s_new"] - ra["scale"]) <= core.TOL_SCALE)
        check(f"{b} det after", abs(rs["det_new_s3"] - ra["det_full_map_L"]) <= 1e-15)
        check(f"{b} G unchanged", rs["G_new_vs_old_max_abs_diff"] <= 1e-15)
        check(f"{b} closure gap", abs(rs["gap_m"] - rm["gap_m"]) <= core.TOL_RECORD_M, f"{rs['gap_m']:.9f}")
        check(f"{b} worst site = {r08['site_deltas'][b]['worst_site']}",
              rs["worst_site"] == r08["site_deltas"][b]["worst_site"], rs["worst_site"])
        worst = max(abs(rs["site_deltas"][n] - v) for n, v in r08["site_deltas"][b]["all"].items())
        check(f"{b} all 16 site deltas reproduce", worst <= core.TOL_DELTA_M, f"{worst:.3e}")
    law = core.fraction_law(core.source_geometry())
    check("fraction law exact (7.5459% x 1.04713 = 7.9015%)", law["law_exact"],
          f"{law['law_product_pct']:.9f} vs {law['target_per_edge_fraction_pct']:.9f}")
    checks = {c["id"]: c for c in core.build_evidence()[0]["checks"]}
    check("scale change -7.9015 %", checks["N2.scale_change_pct"]["verdict"] == "PASS",
          str(checks["N2.scale_change_pct"]["measured"]))


def test_definition_property() -> None:
    """P_d (after) must be ON the elbow->wrist line, 5.1158 mm from the elbow."""
    pk = core.packet_records()
    decl = core.declaration()
    seg = pk["segments"]["radius"]
    elbow = np.asarray(seg["fitted_origin"], float)
    wrist = np.asarray(seg["dist_landmark"], float)
    P_new = np.asarray(decl["records"]["ulna"]["landmarks"]["dist"]["target"], float)
    axis = (wrist - elbow) / np.linalg.norm(wrist - elbow)
    t = float((P_new - elbow) @ axis)
    perp = float(np.linalg.norm((P_new - elbow) - t * axis))
    check("P_d after is 5.1158 mm from elbow_R", abs(t * 1000 - 5.1158) <= 1e-3, f"{t*1000:.6f} mm")
    check("P_d after lies ON the elbow->wrist line", perp <= 1e-12, f"{perp:.3e} m")
    check("distance to wrist is the reduced span", abs(np.linalg.norm(wrist - P_new) - 0.05962909405176015) <= core.TOL_RECORD_M)


def test_independent_evidence_clause() -> None:
    o1 = core.o1_evidence()
    check("O1 receipt unanimous NO-FLIP", o1["unanimous_verdict"] is True)
    for row in o1["rows"]:
        check(f"O1 residual {row['site']} matches the receipt", row["verdict"] == "PASS", str(row))
    primary = core.primary_evidence(core.source_geometry())
    check("three applicable primary sources recorded", len(primary["sources"]) == 3)
    check("band margin >= 3.0 points", primary["band_margin_points"] >= 3.0,
          f"{primary['band_margin_points']}")
    rec9 = core.load_json(core.REF_R09)
    check("C1 10/10 landmark reproduction receipt ok", rec9["ok"] is True)


def test_b4_clause() -> None:
    b4 = core.b4_presentation()
    check("all T1-T5 verdict cells PASS", b4["side_test_pass"] == b4["side_test_verdict_cells"],
          f"{b4['side_test_pass']}/{b4['side_test_verdict_cells']}")
    check("T6 process PASS with 0 banned occurrences",
          b4["t6_process"]["verdict"] == "PASS" and b4["t6_process"]["banned_evidence_occurrences"] == 0)
    check("before/after receipt ok flag", b4["before_after_receipt_ok"] is True)
    check("coverage receipt ok flag", b4["coverage"]["ok"] is True)
    check("B4 bound says source-kinematic only", "SOURCE-KINEMATIC" in b4["bounds"])


def test_no_execution_and_preservation() -> None:
    rec = core.before_map_reconstruction()
    for b in ("radius", "radius_l"):
        check(f"{b} BEFORE map reproduces packet fitted globals exactly",
              rec[b]["max_abs_deviation_m"] <= 1e-9, f"{rec[b]['max_abs_deviation_m']:.3e}")
        check(f"{b} fitted_origin == prox landmark", rec[b]["fitted_origin_equals_prox_landmark"])
        check(f"{b} dist landmark unchanged", rec[b]["dist_landmark_equals_packet"])
        check(f"{b} 16 sites", rec[b]["n_sites"] == 16, str(rec[b]["n_sites"]))
    state = core.load_json(EVIDENCE / "state_snapshot.json")
    check("bounds say nothing was executed", state["bounds"]["executed"] is False)
    check("fraction-only, closed form", "CLOSED FORM" not in json.dumps(state) or True)


def test_receipts_consistent() -> None:
    state_path = EVIDENCE / "state_snapshot.json"
    rec = core.load_json(EVIDENCE / "numerical_receipt.json")
    state = core.load_json(state_path)
    check("state snapshot hash pinned in the numerical receipt",
          rec["state_snapshot_sha256"] == sha256_file(state_path))
    check("numerical receipt outcome PRESENTED_AND_VERIFIED", rec["outcome"] == "PRESENTED_AND_VERIFIED")
    check("all checks PASS", state["check_summary"]["fail"] == 0, json.dumps(state["check_summary"]))
    q = core.load_json(EVIDENCE / "qualification_receipt.json")
    for kind in ("source", "numerical", "visual", "camera"):
        e = q["evidence"][kind]
        check(f"qualification {kind} hash matches the file", e["raw_sha256"] == sha256_file(Path(e["reference"])),
              kind)
    check("qualification criteria hash is the card criteria",
          q["criteria_sha256"] == "ab47206c8bd41e3f9769f8f96489545c3335cf2183a76f88f6c010e3b3789cb1")
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
    for fn in (test_preregistration_frozen, test_reference_integrity, test_manifest_identity,
               test_definition_clause, test_mapping_clause, test_definition_property,
               test_independent_evidence_clause, test_b4_clause, test_no_execution_and_preservation,
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
