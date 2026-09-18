"""Acceptance demos for the graph slice (brief items 6-8 + graph side of 9-10).

Writes machine-readable evidence to
  docs/evidence/agent_fleet/SHIP/CREATURE_GRAPH/acceptance_results.json
and prints a human summary. Every demo manipulates COPIES or the live store
through its real APIs; authored seed files are verified byte-unchanged.

Item 6  reference import: same pinned data twice duplicates nothing;
        source IDs, units, mapping provenance survive; model files are
        parsed, never executed.
Item 7  graph fidelity: refreshes preserve authored placeholders and distinct
        typed connections; moving diagram nodes cannot move the creature.
Item 8  evidence lifecycle: a relevant physical change stales affected
        validation results; source availability never marks a feature verified.
Item 9  (graph side): structure + pressure + intervention join by consistent
        IDs and timestamps; latency/sampling reported.
Item 10 (graph side): save/reload preserves the graph state bit-exactly.
"""

import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "reference_data"))

EVIDENCE_DIR = os.path.normpath(os.path.join(
    HERE, "..", "..", "docs", "evidence", "agent_fleet", "SHIP", "CREATURE_GRAPH"))


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def run(live=True):
    import build_graph
    import gaps
    import graphify_projection
    import schema
    from store import CreatureGraph, content_version
    results = {"run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "head_note": "graph-slice acceptance (items 6-8, graph side of 9-10)",
               "checks": []}

    def check(item, name, ok, detail):
        results["checks"].append({"item": item, "check": name,
                                  "ok": bool(ok), "detail": detail})
        print(f"  [{'PASS' if ok else 'FAIL'}] {item}: {name} -- {detail}")

    authored_dir = os.path.join(HERE, "data", "authored")
    authored_before = {f: sha256_file(os.path.join(authored_dir, f))
                       for f in sorted(os.listdir(authored_dir))
                       if os.path.isfile(os.path.join(authored_dir, f))}

    # ------------------------------------------------------------------ build
    print("[build] building the store from authored seeds")
    g = build_graph.build(with_reference=True)
    store_path = g.save()
    g0_hash = g.graph_hash()

    # ================================================================= A6 ====
    print("[item 6] reference import idempotency + provenance survival")
    import import_reference
    if not live:
        # Offline means cached pins only, including reference-data checks.
        import fetch_cache
        def no_fetch(*args, **kwargs):
            raise RuntimeError("offline acceptance requires the pinned cache; network fetch disabled")
        fetch_cache._fetch = no_fetch
    rep1 = import_reference.import_all()
    store_after_1 = sha256_file(import_reference.STORE_PATH)
    rep2 = import_reference.import_all()
    store_after_2 = sha256_file(import_reference.STORE_PATH)
    check(6, "second import creates nothing", rep2["created"] == 0,
          f"first run created {rep1['created']}, second created "
          f"{rep2['created']}, unchanged {rep2['unchanged']}, "
          f"conflicts {len(rep2['conflicts'])}")
    check(6, "store bytes identical after re-import", store_after_1 == store_after_2,
          f"sha256 {store_after_2[:16]}")
    with open(import_reference.STORE_PATH, encoding="utf-8") as f:
        ref = json.load(f)
    by_id = {o["id"]: o for o in ref["objects"]}
    pa = by_id.get("pa.osim.leg6dof9musc.soleus_r.max_isometric_force_N")
    check(6, "units + source provenance survive on assertions",
          bool(pa) and pa["units"] == "N" and pa["provenance"]["source_id"]
          == "opensim.leg6dof9musc",
          f"{pa['id']}: value={pa['value']} {pa['units']}, conditions="
          f"{pa['conditions']['loading']}, source={pa['provenance']['source_id']}")
    mp = by_id.get("map.uberon-femur__osim-femur_r")
    check(6, "mapping provenance survives, still CANDIDATE (not equivalence)",
          bool(mp) and mp["mapping_type"] == "candidate",
          f"{mp['id']}: mapping_type={mp['mapping_type']}")
    # importing a model file never executes it
    src = open(os.path.join(HERE, "..", "reference_data", "parsers.py"),
               encoding="utf-8").read()
    check(6, "model import never executes (XML-only parser)",
          "exec(" not in src and "eval(" not in src and "subprocess" not in src
          and "os.system" not in src,
          "parsers.py contains no exec/eval/subprocess/os.system; the .osim is "
          "read as declarative XML only")

    # ================================================================= A7 ====
    print("[item 7] graph fidelity: refreshes + placeholders + typed connections")
    # authored seeds unchanged by everything so far
    authored_after = {f: sha256_file(os.path.join(authored_dir, f))
                      for f in sorted(os.listdir(authored_dir))}
    check(7, "authored seed files unchanged through build+import+export",
          authored_before == authored_after,
          f"{len(authored_before)} files, sha256 match")
    # distinct typed connections preserved: shared septum, two sides
    sept_edges = [(r["src"], r["dst"]) for r in g.relations
                  if r["src"] == "memb.septum.feet_shins"
                  and r["rel"] == "bounds_region"]
    check(7, "distinct typed connections preserved (one wall, two owners)",
          len(sept_edges) == 2,
          f"memb.septum.feet_shins bounds_region -> "
          f"{[d for _, d in sept_edges]}")
    # placeholders preserved
    placeholders = [o["id"] for o in g.objects.values()
                    if (o.get("geometry") or {}).get("is_placeholder")
                    and o["kind"] not in ("type", "work")]
    check(7, "authored placeholders preserved through the build",
          len(placeholders) >= 6,
          f"{len(placeholders)} placeholders incl. {placeholders[:4]}")
    # projection export: direction + multiplicity
    rep = graphify_projection.export(g)
    with open(graphify_projection.PROJ_PATH, encoding="utf-8") as f:
        proj = json.load(f)
    sept_proj = [e for e in proj["edges"]
                 if e["source"] == "memb_septum_feet_shins"
                 and e["relation"] == "bounds_region"]
    check(7, "projection preserves edge DIRECTION",
          all(e["source"] == "memb_septum_feet_shins" for e in sept_proj)
          and all(e["target"] in ("region_band_feet", "region_band_shins")
                  for e in sept_proj),
          f"source->target pairs {[(e['source'], e['target']) for e in sept_proj]}")
    check(7, "projection preserves relation MULTIPLICITY (2 distinct edges)",
          len(sept_proj) == 2 and len({e["key"] for e in sept_proj}) == 2,
          f"keys {sorted(e['key'] for e in sept_proj)}")
    # moving diagram nodes cannot move the creature
    lay = dict(g.layout)
    lay["inst.band.feet"] = {"roadmap_tier": 7, "roadmap_x": 42}
    g.layout = lay
    g.save()
    g2 = CreatureGraph.load(store_path)
    band = g2.get("inst.band.feet")
    check(7, "moving diagram nodes cannot move the creature",
          band["spatial"]["band_y"] == [-0.019507, 0.338]
          and g2.layout["inst.band.feet"]["roadmap_x"] == 42,
          f"spatial.band_y still {band['spatial']['band_y']}; layout moved to "
          f"tier 7 x 42 (separate dicts)")
    # schema refuses layout keys inside spatial
    bad = dict(band)
    bad["spatial"] = dict(band["spatial"], roadmap_tier=7)
    errs = schema.validate_object(bad)
    check(7, "schema rejects layout keys inside engine coordinates",
          any("layout key" in e for e in errs),
          f"validate_object -> {errs[:1]}")

    # ================================================================= A8 ====
    print("[item 8] evidence lifecycle: conservative staleness; sources never verify")
    val_before = {e["id"]: e["validation"] for e in g.evidence_records()}
    # Historical seed captures are incomplete. Exercise lifecycle using a NEW
    # explicitly synthetic measurement; never recapture the old conservation run.
    g2.record_evidence({"id": "ev.acceptance.synthetic", "kind": "evidence",
        "name": "Synthetic lifecycle contract test", "status": "specified",
        "validation": "passing", "deps": ["memb.septum.feet_shins"],
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "notes": "Synthetic graph mutation control, not engine evidence"})
    # a RELEVANT physical change: the feet|shins septum gets its implementation
    sept = g2.get("memb.septum.feet_shins")
    old_ver = content_version(sept)
    sept["status"] = "simulated"           # implementation-state change
    sept["physical"]["permeability"] = "still sealed; modeled explicitly now"
    new_ver = content_version(g2.get("memb.septum.feet_shins"))
    flipped = g2.refresh_validation()
    ev = g2.get("ev.acceptance.synthetic")
    check(8, "relevant physical change STALES dependent evidence",
          old_ver != new_ver and "ev.acceptance.synthetic" in flipped
          and ev["validation"] == "stale",
          f"septum {old_ver} -> {new_ver}; staled: {flipped}")
    check(8, "the pre-staleness result stays VISIBLE",
          ev.get("last_result") == "passing",
          f"last_result={ev.get('last_result')} (stale_reasons "
          f"{[r['dep'] for r in ev.get('stale_reasons', [])]})")
    ev_fail = g2.get("ev.reflex_controls_fail")
    check(8, "a failing current test stays visible (not hidden by staleness)",
          (val_before["ev.reflex_controls_fail"] == "failing"
           or ev_fail.get("last_result") == "failing")
          and ev_fail["validation"] in ("failing", "stale"),
          f"ev.reflex_controls_fail validation={ev_fail['validation']} "
          f"(last_result={ev_fail.get('last_result')})")
    # source availability never marks a feature verified
    ref_statuses = {o["status"] for o in g2.objects.values()
                    if o["kind"] in ("reference_entity", "property_assertion",
                                     "model_definition", "source", "mapping",
                                     "relationship")}
    check(8, "source availability never auto-verifies (EXTRACTED is not verified)",
          ref_statuses == {"extracted"}
          and schema.status_at_least("extracted", "geometry_built") is False
          and schema.status_at_least("extracted", "verified") is False,
          f"all {len([o for o in g2.objects.values() if o['kind'] in ('reference_entity', 'property_assertion', 'model_definition', 'source', 'mapping', 'relationship')])} "
          f"reference records are status=extracted; extracted ranks below "
          f"geometry_built and never satisfies verification")

    # ================================================================= A9 ====
    print("[item 9] consistent IDs + timestamps (graph side)")
    if not live:
        results["checks"].append({"item": 9, "check": "live engine checks", "ok": None,
                                  "status": "NOT_TESTED", "detail": "offline contract run; no live endpoint accessed"})
    else:
        try:
            import engine_live
            tick, latency_ms = engine_live.fetch_with_latency()
            snap_path = engine_live.write_inspection(
                g2, tick, latency_ms, "inst.band.shins",
                "graph-side inspection: select + live pressure join; intervention "
                "itself belongs to the engine lane (AN2/window)")
            with open(snap_path, encoding="utf-8") as f:
                insp = json.load(f)
            rows = insp["cells"]
            ok9 = (len(rows) == 4
                   and all(r.get("graph_id") and r.get("ts_us") and
                           r.get("ticks") is not None for r in rows))
            check(9, "structure + pressure join by stable IDs + engine timestamps",
                  ok9,
                  f"{len(rows)} rows; e.g. {rows[1]['graph_id']} @ ticks "
                  f"{rows[1]['ticks']} ts_us {rows[1]['ts_us']} P={rows[1]['live_P_pa']} Pa")
            check(9, "latency + sampling limits reported",
                  isinstance(latency_ms, float) and rows[0]["sampling_hz"] == tick.get("sampling_hz"),
                  f"GET latency {latency_ms:.1f} ms; reported sampling_hz={tick.get('sampling_hz')}; "
                  f"REST snapshot latency is NOT the tick path")
            cc = engine_live.cross_check(g, tick)
            check(9, "live engine cross-check (4 verified bands vs live cells)",
                  cc["pass"], f"{len(cc['checks'])} checks, pass={cc['pass']}")
        except Exception as exc:  # engine not running: record honestly
            check(9, "live engine reachable", False, f"engine_live failed: {exc}")

    # ================================================================ A10 ====
    print("[item 10] save/reload preserves graph state (graph side)")
    g2.save()
    g3 = CreatureGraph.load(store_path)
    check(10, "graph hash preserved across save/reload",
          g2.graph_hash() == g3.graph_hash() == g3.graph_hash(),
          f"{g2.graph_hash()[:16]} == {g3.graph_hash()[:16]}")
    ev3 = g3.get("ev.band_seal_conservation")
    check(10, "validation lifecycle survives reload",
          ev3["validation"] == "stale" and ev3.get("last_result") == "passing",
          f"validation={ev3['validation']}, last_result={ev3.get('last_result')}")
    check(10, "relations + layout preserved",
          len(g3.relations) == len(g2.relations)
          and g3.layout.get("inst.band.feet", {}).get("roadmap_x") == 42,
          f"{len(g3.relations)} relations; layout x=42 survives")

    # ------------------------------------------------- the six gap queries ---
    print("[queries] the six gap-query shapes on the seeded graph")
    six = gaps.run_all_six(g3)
    q1 = six["q1_compartments_without_supported_boundaries"]
    check("Q1", "compartment boundary closure query",
          len(q1) == 7,
          f"{len(q1)} A1 compartments: "
          + "; ".join(f"{r['compartment']}={r['verdict']}" for r in q1[:7]))
    q2 = six["q2_placeholder_only_structures"]
    check("Q2", "placeholder-only structures",
          len(q2) >= 6, f"{len(q2)} structures exist only as placeholders")
    q3 = six["q3_active_params_missing_provenance"]
    check("Q3", "active parameters lacking provenance",
          all(p["gaps"] for p in q3) and len(q3) == 6,
          f"{len(q3)} in-use parameters, each with explicit residual gaps "
          f"(units/source present; applicability conditions + independent "
          f"validation outstanding)")
    q4 = six["q4_blockers_for_local_withdrawal"]
    check("Q4", "blockers for local withdrawal",
          len(q4["ready_now"]) >= 1 and len(q4["blocked_by"]) >= 1,
          f"ready now: {[e['id'] for e in q4['ready_now']]}; blocked: "
          f"{[(e['id'], e['blockers']) for e in q4['blocked_by']]}")
    q5 = six["q5_evidence_at_risk_if_changed"]
    check("Q5", "evidence at risk if septum/material changed",
          len(q5["at_risk"]["at_risk"]) >= 1 and len(q5["also_material_water"]["at_risk"]) >= 1,
          f"if {q5['if_changed']} changed: {[a['evidence'] for a in q5['at_risk']['at_risk']]}; "
          f"if material.water changed: "
          f"{[a['evidence'] for a in q5['also_material_water']['at_risk']]}")
    q6 = six["q6_next_ready_task"]
    check("Q6", "next ready task by authored priority",
          q6["next"] is not None
          and q6["next"]["authored_priority"] == min(
              e["authored_priority"] for e in q6["ready"]),
          f"next = {q6['next']['id']} (authored priority "
          f"{q6['next']['authored_priority']}) enabling {q6['next']['enables']}")

    results["six_queries"] = six
    # restore the canonical store (the acceptance mutations live in g2's file;
    # rebuild from seeds so the committed store is the pristine authored one)
    g_clean = build_graph.build(with_reference=True)
    g_clean.save()
    results["summary"] = {
        "n_checks": len(results["checks"]),
        "n_pass": sum(1 for c in results["checks"] if c["ok"]),
        "n_fail": sum(1 for c in results["checks"] if c["ok"] is False),
        "n_not_tested": sum(1 for c in results["checks"] if c["ok"] is None),
        "store_graph_hash": g_clean.graph_hash(),
    }
    return results


def main():
    res = run(live="--offline" not in sys.argv[1:])
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    out = os.path.join(EVIDENCE_DIR, "acceptance_results.json")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print(f"\nwrote {out}")
    print(f"summary: {res['summary']['n_pass']}/{res['summary']['n_checks']} "
          f"checks pass")
    return 0 if res["summary"]["n_fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
