"""mocap_doc_derive.py -- lanes 2 and 3 of local-refs-20260918.

mocap_walk_series_20260918: the three gait-cycle mean curves (hip/knee/ankle,
101 samples, n_cycles=4) from repo-resident mocap_walk_reference.json, written
as long-form series CSVs (series_id, x_fraction, y_deg) -- the adapter converts
y to SI radians via the units table and x is already dimensionless fraction.

muscle_inventory_doc_20260918: MUSCLE_INVENTORY.md copied in its committed (LF)
byte form -- a documentation reference pinned by sha256, never measurements.

Deterministic; refuses on any structural surprise.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
HERE = ROOT / "research_references" / "human"
DAY = "2026-09-18"
OUT_MOCAP = ROOT / "tools" / "science_funnel" / "data" / "mocap_walk_series_20260918"
OUT_DOC = ROOT / "tools" / "science_funnel" / "data" / "muscle_inventory_doc_20260918"


def pinned_copy(src, dest):
    raw = src.read_bytes().replace(b"\r\n", b"\n")
    dest.write_bytes(raw)
    return len(raw), hashlib.sha256(raw).hexdigest()


def main() -> int:
    # ---- mocap series -------------------------------------------------
    src = HERE / "mocap_walk_reference.json"
    if not src.is_file():
        print("REFUSE: missing", src)
        return 1
    doc = json.loads(src.read_text(encoding="utf-8"))
    envelopes = doc.get("envelopes_deg")
    if not isinstance(envelopes, dict) or set(envelopes) != {"hip", "knee", "ankle"}:
        print("REFUSE: envelopes_deg structure unexpected:", sorted(envelopes or {}))
        return 1
    OUT_MOCAP.mkdir(exist_ok=True)
    n_by_joint = {}
    for joint in ("hip", "knee", "ankle"):
        mean = envelopes[joint]["mean"]
        if len(mean) != 101:
            print("REFUSE: %s mean curve has %d points, expected 101" % (joint, len(mean)))
            return 1
        if envelopes[joint].get("n_cycles") != 4:
            print("REFUSE: %s n_cycles unexpected" % joint)
            return 1
        rows = ["series_id,x_fraction,y_deg"]
        for i, y in enumerate(mean):
            rows.append("mocap_cmus35_walk_%s_mean_cycle,%s,%s" % (joint, i / 100.0, y))
        (OUT_MOCAP / ("mocap_cmus35_walk_%s_mean_cycle.csv" % joint)).write_text(
            "\n".join(rows) + "\n", encoding="utf-8", newline="")
        n_by_joint[joint] = len(mean)
    nbytes, sha = pinned_copy(src, OUT_MOCAP / "mocap_walk_reference.json")
    scalars = {k: doc[k] for k in ("fps", "frames", "duration_s", "cadence_steps_per_min",
                                   "stride_length_m", "stride_length_leg_lengths",
                                   "stride_time_s", "duty_factor", "speed_m_s", "leg_length_m")}
    receipt_mocap = {
        "schema": "chimera.local_refs.derive.v1",
        "derived_utc_day": DAY,
        "files": [
            {"path": "mocap_cmus35_walk_hip_mean_cycle.csv",
             "url": "derived by tools/science_funnel/derive_local_refs_mocap_doc.py "
                    "from repo-resident research_references/human/"
                    "mocap_walk_reference.json",
             "bytes": len((OUT_MOCAP / "mocap_cmus35_walk_hip_mean_cycle.csv").read_bytes()),
             "sha256": hashlib.sha256(
                 (OUT_MOCAP / "mocap_cmus35_walk_hip_mean_cycle.csv").read_bytes()).hexdigest()},
            {"path": "mocap_cmus35_walk_knee_mean_cycle.csv",
             "url": "derived by tools/science_funnel/derive_local_refs_mocap_doc.py "
                    "from repo-resident research_references/human/"
                    "mocap_walk_reference.json",
             "bytes": len((OUT_MOCAP / "mocap_cmus35_walk_knee_mean_cycle.csv").read_bytes()),
             "sha256": hashlib.sha256(
                 (OUT_MOCAP / "mocap_cmus35_walk_knee_mean_cycle.csv").read_bytes()).hexdigest()},
            {"path": "mocap_cmus35_walk_ankle_mean_cycle.csv",
             "url": "derived by tools/science_funnel/derive_local_refs_mocap_doc.py "
                    "from repo-resident research_references/human/"
                    "mocap_walk_reference.json",
             "bytes": len((OUT_MOCAP / "mocap_cmus35_walk_ankle_mean_cycle.csv").read_bytes()),
             "sha256": hashlib.sha256(
                 (OUT_MOCAP / "mocap_cmus35_walk_ankle_mean_cycle.csv").read_bytes()).hexdigest()},
            {"path": "mocap_walk_reference.json",
             "url": "repo-resident research_references/human/mocap_walk_reference.json",
             "bytes": nbytes, "sha256": sha},
        ],
        "rule": "admit the gait-cycle mean curves as series records under "
                "batch.property.series; x = percent_of_cycle/100 (dimensionless, 0..1); "
                "y source degrees -> SI rad in the adapter via the units table",
        "source_repo_file": {
            "path": "research_references/human/mocap_walk_reference.json",
            "source": "repo-resident research_references/human/mocap_walk_reference.json",
            "bytes": nbytes, "sha256": sha},
        "series": {
            "joints": ["hip", "knee", "ankle"],
            "samples_per_curve": 101,
            "n_cycles_per_curve": 4,
            "series_id_prefix": "mocap_cmus35_walk_",
            "scalars_carried_on_records": scalars,
            "conventions_verbatim": doc.get("conventions"),
            "events_verbatim": doc.get("events"),
            "units_block_verbatim": doc.get("units"),
            "source_verbatim": doc.get("source"),
        },
        "license_note": "CMU MoCap via una-dinosauria BVH mirror; per SOURCES.md: "
                        "'free for research AND commercial inclusion; may not resell the "
                        "data itself; credit mocap.cs.cmu.edu + NSF EIA-0196217'",
    }
    (OUT_MOCAP / "download_receipt.json").write_text(
        json.dumps(receipt_mocap, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="")
    print("mocap series written:", n_by_joint)

    # ---- muscle inventory doc ------------------------------------------
    src_md = HERE / "MUSCLE_INVENTORY.md"
    if not src_md.is_file():
        print("REFUSE: missing", src_md)
        return 1
    OUT_DOC.mkdir(exist_ok=True)
    md_bytes, md_sha = pinned_copy(src_md, OUT_DOC / "MUSCLE_INVENTORY.md")
    expect = "f16fde6da59c1e6ccf5214734957b6570cc120310b22959ef35c13caab121c71"  # committed LF bytes
    if md_sha != expect:
        print("REFUSE: MUSCLE_INVENTORY.md sha256 %s != work-record pin %s" % (md_sha, expect))
        return 1
    receipt_doc = {
        "schema": "chimera.local_refs.derive.v1",
        "derived_utc_day": DAY,
        "files": [
            {"path": "MUSCLE_INVENTORY.md",
             "url": "repo-resident research_references/human/MUSCLE_INVENTORY.md",
             "bytes": md_bytes, "sha256": md_sha},
        ],
        "rule": "admit MUSCLE_INVENTORY.md as ONE documentation-reference entity "
                "pinned by its sha256 -- a citation, never measurements",
        "source_repo_file": {
            "path": "research_references/human/MUSCLE_INVENTORY.md",
            "source": "repo-resident research_references/human/MUSCLE_INVENTORY.md",
            "bytes": md_bytes, "sha256": md_sha},
        "work_record_pin": expect,
        "license_note": "repository-authored document citing Neumann (Kinesiology), "
                        "Ward et al. 2009, Rajagopal et al. 2016, Saul et al. 2015, "
                        "Christophy et al. 2012, Caggiano et al. 2022 (MyoSuite)",
    }
    (OUT_DOC / "download_receipt.json").write_text(
        json.dumps(receipt_doc, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="")
    print("muscle inventory doc written:", md_sha[:12])
    return 0


if __name__ == "__main__":
    sys.exit(main())
