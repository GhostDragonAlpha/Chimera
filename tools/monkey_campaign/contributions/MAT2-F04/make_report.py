"""Generate report.md from the committed receipts (checks.json +
determinism.json). Every number in the report is read from the receipts --
nothing is hand-transcribed."""
from __future__ import annotations

import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"


def fmt(x, nd=6):
    if isinstance(x, float):
        return ("%." + str(nd) + "g") % x
    return str(x)


def main():
    checks = json.loads((EVIDENCE / "checks.json").read_bytes())
    det = json.loads((EVIDENCE / "determinism.json").read_bytes())
    val = checks["capture"]["validation"]
    lines = []
    w = lines.append

    w("# MAT2-F04 — source-bound qualification receipt: ground and trunk "
      "contact geometry, frozen cases")
    w("")
    w("**Verdict: BUILT AND SELF-CONSISTENT.** The combined F02 terrain asset "
      "and F03 trunk asset were bound to the unmodified M06 shared contact "
      "path and exercised with frozen crossing, impact, seam and rest "
      "trajectories over FULL tick intervals: every CCD-on first contact is "
      "pre-overlap (worst penetration "
      + fmt(checks["p346_contact_geometry"]["worst_penetration_m"], 3)
      + " m against the frozen 1e-4 bar), every support impulse is a real "
      "per-tick ledger record (worst residual "
      + fmt(checks["p2_shared_path"]["worst_ledger_residual"], 3)
      + "), the collision bodies are element-identical to the rendered assets "
      "(exact array equality; trunk radial gap "
      + fmt(checks["p1_tied_asset_identity"]["trunk"]["worst_radial_gap_to_analytic_m"], 3)
      + " m), all seven falsifier arms bite fail-first, and the "
      "contact-motion capture is structurally valid under the REGISTRY "
      "profile with a single gate-bound video artifact and committed stills. "
      "Visual acceptance itself belongs to the independent visual reviewer.")
    w("")
    w("- card: MAT2-F04; planning id F04; attempt "
      + checks["attempt_id"] + "; arrival " + checks["arrival_id"]
      + "; criteria sha256 " + checks["criteria_sha256"] + "; scope sha256 "
      + checks["scope_sha256"] + "; base revision " + checks["base_revision"]
      + " (branch-3 fast-forwarded to the sealed tip; F02/F03 merged).")
    w("- done_when (verbatim): \"No unacceptable tunnelling, ghost support, "
      "interpenetration or visual/collision disagreement in frozen cases\".")
    w("- discipline: PREREGISTRATION.md committed BEFORE implementation at "
      + checks["prereg_commit"] + "; Amendments A1-A6 are separate commits ("
      + ", ".join(checks["amendment_commits"])
      + "), all before the implementation commit and the first completed "
      "build. This report is GENERATED from evidence/checks.json and "
      "evidence/determinism.json — no observed value is hand-transcribed.")
    w("")
    w("## 1. Reconcile-first (reused published bytes only)")
    w("")
    w("Pins asserted by raw sha256 at every run (see `pins` in "
      "evidence/checks.json): F02's tied terrain asset + query surface + F01 "
      "render law, F03's trunk declaration/mesh, M06's byte-identical "
      "local_contact module and contact law. No physics constant is new: "
      "ground mu 0.9/0.65 thickness 0.002 (F02), trunk mu 0.6/0.6 thickness "
      "0.0 solid (F03, friction remains the declared UNEVIDENCED-PLACEHOLDER, "
      "G04 debt), probes mass_tetra 0.12 kg mu 0.6/0.4 (F02/M06).")
    w("")
    w("## 2. P0 — combined instantiation is REFUSED by the pinned law")
    w("")
    p0 = checks["p0_combined_instantiation"]
    w("Solving ground + trunk together is " + p0["outcome"]
      + " (`" + p0["code"] + "`): the trunk base ring touches the ground "
      "plane at exactly 0.0 m, so the pinned law sees a both-pinned "
      "exact-contact pair (zero inverse-mass sum). F03's A3 heritage, now "
      "measured at the ground/trunk seam. Dynamic scenarios therefore "
      "instantiate exactly the static parts they touch (declared per "
      "scenario); asset identity (P1) is always measured on the FULL pinned "
      "bodies. No seam support is invented by composition.")
    w("")
    w("## 3. P1/P2 — the collision assets ARE the rendered assets, through "
      "the shared path")
    w("")
    p1 = checks["p1_tied_asset_identity"]
    p2 = checks["p2_shared_path"]
    w("- P1 ground: "
      + str(p1["ground"]["vertex_count"]) + " vertices, arrays_exact_equal="
      + str(p1["ground"]["arrays_exact_equal"])
      + ", surface_id " + p1["ground"]["surface_id"]
      + ", contact extent " + fmt(p1["ground"]["contact_extent_max_abs_m"], 3)
      + " m == rendered half width "
      + fmt(p1["ground"]["rendered_half_width_m"], 3) + " m.")
    w("- P1 trunk: "
      + str(p1["trunk"]["vertex_count"]) + " vertices, arrays_exact_equal="
      + str(p1["trunk"]["arrays_exact_equal"]) + ", worst radial gap to the "
      "analytic cylinder "
      + fmt(p1["trunk"]["worst_radial_gap_to_analytic_m"], 4)
      + " m (declared tolerance "
      + fmt(p1["trunk"]["declared_radial_tolerance_m"], 3)
      + "), worst outside-solid "
      + fmt(p1["trunk"]["worst_inside_solid_m"], 4)
      + " m, partition " + json.dumps(p1["trunk"]["triangle_partition"]) + ".")
    w("- P2: " + fmt(p2["contact_record_count_total"])
      + " contact records across all scenarios, every one a "
      "chimera.local_contact.v1 record of the byte-identical M06 module; "
      "worst per-tick ledger residual "
      + fmt(p2["worst_ledger_residual"], 3) + " (bar 1e-12); declarations "
      "match contact_law.json: " + str(p2["declarations_match_law"]) + ".")
    w("")
    w("## 4. P3/P4/P6 — no tunnelling, no interpenetration, contact geometry")
    w("")
    p = checks["p346_contact_geometry"]
    w("| metric | measured | bar |")
    w("|---|---|---|")
    w("| episode-first contacts pre-overlap (kind ccd, gap > 0) | "
      + str(p["episode_first_contacts_pre_overlap"]) + " | required |")
    w("| worst penetration over ALL ticks of all CCD-on runs | "
      + fmt(p["worst_penetration_m"], 3) + " m | <= 1e-4 m |")
    w("| worst ground contact point plane error | "
      + fmt(p["worst_ground_contact_plane_err_m"], 3) + " m | <= 1e-9 m |")
    w("| worst trunk contact point radial error | "
      + fmt(p["worst_trunk_contact_radial_err_m"], 3) + " m | <= 2e-4 m |")
    w("| seam impact altitude | "
      + fmt(p["seam_impact_altitude_m"], 4) + " m | in [0, 0.15] m |")
    r = checks["p45_rest_ghost"]["rests"]
    w("| G_HIGH rest min corner separation | "
      + fmt(r["G_HIGH"]["min_corner_separation_m"], 5) + " m | in "
      + json.dumps(r["G_HIGH"]["window_m"]) + " m, stopped "
      + str(r["G_HIGH"]["stopped"]) + " |")
    w("| G_SEAM_REST (seam approach) rest | "
      + fmt(r["G_SEAM_REST"]["min_corner_separation_m"], 5) + " m | in "
      + json.dumps(r["G_SEAM_REST"]["window_m"]) + " m, trunk clearance "
      + fmt(r["G_SEAM_REST"]["trunk_surface_clearance_m"], 4) + " m |")
    w("| TRUNK_TOP_REST displacement | "
      + fmt(r["TRUNK_TOP_REST"]["max_displacement_m"], 3) + " m | <= 2e-3 m, "
      "cap contact " + str(r["TRUNK_TOP_REST"]["cap_contact_observed"]) + " |")
    w("")
    w("Per-scenario shape (from the receipt): "
      + "; ".join(name + " " + str(s["ticks"]) + " ticks, first contact "
                  + str(s["first_contact_tick"]) + ", "
                  + str(s["contact_records"]) + " records"
                  for name, s in checks["scenario_summary"].items()) + ".")
    w("")
    w("## 5. P5 — no ghost support")
    w("")
    w("Every support impulse appears as a reciprocal local_contact.v1 record "
      "with the per-tick ledger identity enforced by the unmodified module "
      "(worst residual "
      + fmt(checks["p45_rest_ghost"]["worst_ledger_residual"], 3)
      + " <= 1e-12); both rests land inside their frozen windows; the "
      "combined-instantiation refusal (P0) means composition invents no seam "
      "support. FB3/FB4 prove the detectors have teeth (below).")
    w("")
    w("## 6. P7 — no visual/collision disagreement (pure ray/geometry)")
    w("")
    p7 = checks["p7_visual_collision"]
    w("Marker classify per view (markers never read pixels):")
    w("")
    w("| marker | " + " | ".join(p7["per_view"]) + " |")
    w("|---|---|---|")
    keys = sorted(next(iter(p7["per_view"].values())))
    for mid in keys:
        w("| " + mid + " | " + " | ".join(
            p7["per_view"][v].get(mid, "-") for v in p7["per_view"]) + " |")
    w("")
    w("- every view has >= 1 VISIBLE_EXACT trunk surface subject "
      "(`subject_trunk`, F03's frozen-probe pattern: the camera-facing facet "
      "at mid-facet azimuth, exactly on the facet chord).")
    w("- zero VISIBLE_BUT_MISMATCH anywhere; the seam impact marker is "
      "VISIBLE_EXACT in V2 with frame margin "
      + fmt(p7["seam_marker_margin_fraction"], 4)
      + " (required >= " + fmt(p7["margin_required"], 3) + " per side).")
    w("- V3's opposite-side markers are OCCLUDED exactly when the analytic "
      "cylinder silhouette predicts it (depth ordering verified from the "
      "opposite side); OFF_FRAME markers are outside the V3 frustum by "
      "geometry.")
    w("- FB6 proves the decouple detector has teeth (below).")
    w("")
    w("## 7. Falsifier proof (run FIRST; all seven bite fail-first)")
    w("")
    w("| arm | bites | observed |")
    w("|---|---|---|")
    for b in checks["falsifier_bites"]:
        obs = json.dumps(b["observed"], sort_keys=True)
        if len(obs) > 160:
            obs = obs[:157] + "..."
        w("| " + b["bite"] + " | " + str(b["bites"]) + " | `" + obs + "` |")
    w("")
    w("Full observed records in evidence/bites.json inside checks.json "
      "(falsifier_bites). A non-biting arm refuses the whole build "
      "(`f04_falsifier_did_not_bite`).")
    w("")
    w("## 8. Capture (REGISTRY profile contact-motion, kind motion)")
    w("")
    cap = checks["capture"]
    w("- profile read READ-ONLY from " + val["registry_profile"]["read_from"]
      + " (" + val["registry_profile"]["mode"] + "); profile canonical sha256 "
      + val["registry_profile"]["canonical_sha256"] + "; attempt state "
      + val["registry_profile"]["attempt_state"] + ".")
    w("- task_id `" + checks["task_id"] + "` (SHORT form); run_id "
      + checks["run_id"] + "; tick_interval "
      + json.dumps(json.loads((EVIDENCE / "capture_context.json")
                              .read_bytes())["tick_interval"])
      + " (Amendment A6: measured replay length).")
    w("- single gate-bound artifact: " + cap["video_path"] + " sha256 "
      + cap["video_sha256"] + " (" + str(cap["frames"])
      + " lossless FFV1 frames, ffprobe-verified: "
      + json.dumps(cap["video_probe"]) + "); rows bind state_binding "
      "kind=trace to evidence/contact_trace.json (sha256 "
      + cap["trace_sha256"] + ").")
    w("- committed stills (hash-listed supplementary, one per row at the "
      "impact tick): " + "; ".join(
          k.split("_", 1)[0] + "/" + k.split("_", 1)[1] + " = " + v[:16]
          + "..." for k, v in cap["stills"].items()) + ".")
    w("- visual_capture.validate_manifest: structurally_valid="
      + str(val["validate_manifest"]["structurally_valid"]) + " ("
      + val["validate_manifest"]["mode"] + ", profile_id "
      + val["validate_manifest"]["profile_id"] + ", view_count "
      + str(val["validate_manifest"]["view_count"]) + ", capture_kind "
      + val["validate_manifest"]["capture_kind"] + "); visual_gate.verify: "
      "structurally_valid=" + str(val["visual_gate"]["structurally_valid"])
      + ". visual_acceptance="
      + str(val["validate_manifest"]["visual_acceptance"])
      + " BY DESIGN — independent visual review remains mandatory.")
    w("- honest visual note: the V1 overview renders the trunk at sub-2-px "
      "scale (F03's own disclosure); the visually resolvable trunk, probe "
      "arrest and the three diagnostic layers (render/collision wireframes, "
      "probe trajectory polyline, cyan contact normals + yellow tick-ID "
      "markers) are verified in the V2 seam close-up frames; V3 carries the "
      "opposite-side depth check (the trunk partially occludes the far-side "
      "probe).")
    w("")
    w("## 9. Determinism (P8)")
    w("")
    w("Two full builds produced byte-identical artifacts: "
      + str(det["artifacts"]) + " evidence artifacts + the video, identical="
      + str(det["identical"]) + "; video sha256 " + det["video_sha256"]
      + ". No RNG, no wall-clock anywhere in the build. (FFV1 is encoded in "
      "a deterministic AVI container; MKV measured nondeterministic and was "
      "rejected.)")
    w("")
    w("## 10. Honest boundaries")
    w("")
    w("- the pinned M06 law refuses a full ground+trunk co-instantiation at "
      "the seam (P0): the seam crossing is a declared phased composition "
      "(ballistic approach -> trunk phase, handover tick "
      + str(checks["scenario_summary"]["SEAM_HIGH"]["handover_tick"])
      + "); a static seam solve (probe supported by the ground WHILE "
      "touching the trunk) is NOT demonstrated and is recorded as an "
      "unresolved upstream component for the integrator.")
    w("- SEAM_HIGH's trunk phase runs without the ground body; the "
      "post-arrest unsupported sink inside the frozen tail is measured (min "
      "clearance "
      + fmt(checks["seam_composition"]["measured_phase_B_min_clearance_above_query_m"], 4)
      + " m) and disclosed as a composition artifact, excluded from the "
      "interpenetration bar by the declared instantiation scope.")
    w("- CPU-only (stdlib + ffmpeg encode); no engine run, no native change, "
      "no GPU, no training, no runtime or playable-build acceptance.")
    w("- trunk friction 0.6/0.6 is F03's declared UNEVIDENCED-PLACEHOLDER "
      "(acquisition is G04's).")
    w("- structural capture validity only: visual acceptance belongs to the "
      "independent visual reviewer.")
    w("")
    w("## 11. Exact commands (from this directory, Python 3.14, CPU only)")
    w("")
    w("    python -B implementation.py bites    # 7/7 fail-first")
    w("    python -B implementation.py build    # receipt + frames + video")
    w("    python -B implementation.py verify   # P8 double-run determinism")
    w("    python -B make_report.py             # this file, from receipts")
    w("    python -B -m unittest test_implementation -v")
    w("")
    (HERE / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("report.md written:", len(lines), "lines")


if __name__ == "__main__":
    main()
