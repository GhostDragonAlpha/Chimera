"""M02-MC comparison: observed exporter report vs FROZEN expectations.

Pure Python standard library; imports nothing from tools/. Verifies the frozen
expectations file by sha256 BEFORE comparing (prereg freeze integrity).
Tolerances are read from the frozen expectations (prereg): TOL(exp) =
1e-9 * max(1, |exp|); T_ZERO = 1e-9 absolute; statuses/flags exact.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN_SHA256 = "d8ed7a82b13c168b3bb1e58ba99688455754daf6acbf544125d3f305978feec0"
FROZEN_PATH = os.path.join(HERE, "derivation", "derived_expectations.json")
REPORT_PATH = os.path.join(HERE, "receipts", "run1_report.json")
GROUPS_PATH = os.path.join(HERE, "fixtures", "mc_groups.json")
MANIFEST_PATH = os.path.join(HERE, "fixtures", "mc_manifest.json")
PARTITION_PATH = os.path.join(HERE, "fixtures", "mc_partition.json")

EXPECTED_BODIES = {
    "mc-body-1": {"mass": 27.5, "volume": 3.0},
    "mc-body-2": {"mass": 16.0, "volume": 2.6666666666666665},
}


def tol(exp):
    return 1e-9 * max(1.0, abs(exp))


def canonical_hash(doc):
    serialized = json.dumps(doc, sort_keys=True, separators=(",", ":"),
                            ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(serialized.encode("ascii")).hexdigest()


class Verdicts:
    def __init__(self):
        self.rows = []
        self.fails = 0

    def num(self, label, observed, expected, t=None):
        t = tol(expected) if t is None else t
        dev = abs(observed - expected)
        ok = dev <= t
        self.fails += 0 if ok else 1
        self.rows.append(("NUM", label, observed, expected, dev, t, ok))

    def flag(self, label, observed, expected):
        ok = observed == expected
        self.fails += 0 if ok else 1
        self.rows.append(("EQ", label, observed, expected, None, None, ok))

    def report_text(self):
        lines = []
        for kind, label, obs, exp, dev, t, ok in self.rows:
            mark = "PASS" if ok else "FAIL"
            if kind == "NUM":
                lines.append(f"{mark} | {label} | observed={obs!r} | expected={exp!r} "
                             f"| |dev|={dev:.3e} | tol={t:.3e}")
            else:
                lines.append(f"{mark} | {label} | observed={obs!r} | expected={exp!r}")
        lines.append(f"TOTAL: {len(self.rows)} checks, {self.fails} FAIL")
        return "\n".join(lines)


def main():
    with open(FROZEN_PATH, "rb") as fh:
        frozen_bytes = fh.read()
    got_hash = hashlib.sha256(frozen_bytes).hexdigest()
    assert got_hash == FROZEN_SHA256, f"frozen expectations hash mismatch: {got_hash}"
    frozen = json.loads(frozen_bytes)
    with open(REPORT_PATH, encoding="utf-8") as fh:
        rep = json.load(fh)
    with open(GROUPS_PATH, encoding="utf-8") as fh:
        groups_doc = json.load(fh)
    with open(MANIFEST_PATH, encoding="utf-8") as fh:
        manifest = json.load(fh)
    with open(PARTITION_PATH, encoding="utf-8") as fh:
        partition = json.load(fh)
    groups_by_body = {g["body_id"]: g for g in groups_doc["body_groups"]}
    rot = {bid: g["body_frame"]["domain_from_body"]["rotation"]
           for bid, g in groups_by_body.items()}
    org = {bid: g["body_frame"]["domain_from_body"]["origin_m"]
           for bid, g in groups_by_body.items()}

    v = Verdicts()

    # ---- root-level contract fields ---------------------------------------
    v.flag("root.schema_version", rep["schema_version"], "chimera.rigid_body_mass_export.v1")
    v.flag("root.export_status", rep["export_status"], "complete")
    v.flag("root.admission_status", rep["admission_status"], "validation_only_admissible")
    v.flag("root.mass_authority", rep["mass_authority"], "reconstructed_tissue_mass")
    v.flag("root.validation_only", rep["validation_only"], True)
    v.flag("root.dynamics_readiness_claimed", rep["dynamics_readiness_claimed"], False)
    v.flag("root.physical_state_mutated", rep["physical_state_mutated"], False)
    v.flag("root.production_wired", rep["production_wired"], False)
    v.flag("root.anatomical_completeness_certified", rep["anatomical_completeness_certified"], False)
    v.flag("root.admission_anatomical_completeness_certified",
           rep["admission_anatomical_completeness_certified"], False)
    v.flag("root.all_supplied_cells_assigned", rep["all_supplied_cells_assigned"], True)
    v.flag("root.unassigned_cell_ids", rep["unassigned_cell_ids"], [])
    v.flag("root.unassigned_cells", rep["unassigned_cells"], [])
    v.flag("root.surface_mass_overlay_generated", rep["surface_mass_overlay_generated"], False)
    v.flag("root.source_effective_segment_payloads_consumed",
           rep["source_effective_segment_payloads_consumed"], False)
    v.flag("root.reason_codes", rep["reason_codes"], [])

    # ---- input hashes vs documented canonical serialization -----------------
    v.flag("root.input_hashes.algorithm", rep["input_hashes"]["algorithm"], "sha256")
    v.flag("root.input_hashes.manifest_sha256",
           rep["input_hashes"]["manifest_sha256"], canonical_hash(manifest))
    v.flag("root.input_hashes.partition_sha256",
           rep["input_hashes"]["partition_sha256"], canonical_hash(partition))
    v.flag("root.input_hashes.body_groups_sha256",
           rep["input_hashes"]["body_groups_sha256"], canonical_hash(groups_doc))

    # ---- per-body -----------------------------------------------------------
    exported_masses = []
    domain_recovered = []
    for bid in ("mc-body-1", "mc-body-2"):
        g = next(x for x in rep["body_groups"] if x["body_id"] == bid)
        mp = g["mass_properties"]
        exp = frozen["bodies"][bid]
        v.flag(f"{bid}.export_status", g["export_status"], "exported")
        v.flag(f"{bid}.admission_status", g["admission_status"], "validation_only_admissible")
        v.flag(f"{bid}.owned_cell_ids", g["owned_cell_ids"],
               sorted(groups_by_body[bid]["cell_ids"]))
        bf = g["body_frame"]
        v.flag(f"{bid}.body_frame.frame_id", bf["frame_id"],
               groups_by_body[bid]["body_frame"]["frame_id"])
        v.flag(f"{bid}.body_frame.rotation", bf["domain_from_body"]["rotation"], rot[bid])
        v.flag(f"{bid}.body_frame.origin_m", bf["domain_from_body"]["origin_m"], org[bid])
        v.flag(f"{bid}.mass.unit", mp["mass"]["unit"], "kg")
        v.flag(f"{bid}.mass.coordinate_frame", mp["mass"]["coordinate_frame"], "frame_invariant")
        v.flag(f"{bid}.mass.frame_invariant", mp["mass"]["frame_invariant"], True)
        v.flag(f"{bid}.volume.unit", mp["volume"]["unit"], "m^3")
        v.flag(f"{bid}.volume.frame_invariant", mp["volume"]["frame_invariant"], True)
        v.flag(f"{bid}.com.unit", mp["center_of_mass"]["unit"], "m")
        v.flag(f"{bid}.com.coordinate_frame", mp["center_of_mass"]["coordinate_frame"],
               exp["frame_id"])
        it = mp["inertia_tensor_about_com"]
        v.flag(f"{bid}.inertia.unit", it["unit"], "kg*m^2")
        v.flag(f"{bid}.inertia.coordinate_frame", it["coordinate_frame"], exp["frame_id"])
        v.flag(f"{bid}.inertia.frame_id", it["frame_id"], exp["frame_id"])
        v.flag(f"{bid}.inertia.basis", it["basis"], "authored_body_frame")
        v.flag(f"{bid}.inertia.full_symmetric_tensor", it["full_symmetric_tensor"], True)
        v.flag(f"{bid}.inertia.off_diagonal_terms_preserved",
               it["off_diagonal_terms_preserved"], True)
        v.flag(f"{bid}.inertia.principal_axis_transform_applied",
               it["principal_axis_transform_applied"], False)

        v.num(f"{bid}.mass", mp["mass"]["value"], exp["mass"])
        v.num(f"{bid}.volume", mp["volume"]["value"], exp["volume"])
        exported_masses.append(mp["mass"]["value"])
        for k, label in ((0, "x"), (1, "y"), (2, "z")):
            v.num(f"{bid}.com.{label}", mp["center_of_mass"]["value"][k], exp["com_body"][k])
        obs_I = it["value"]
        for i in range(3):
            for j in range(3):
                v.num(f"{bid}.inertia[{i}][{j}]", obs_I[i][j], exp["inertia_body"][i][j])
        for i in range(3):
            for j in range(3):
                if i < j:
                    asym = abs(obs_I[i][j] - obs_I[j][i])
                    v.num(f"{bid}.symmetry[{i}][{j}]", asym, 0.0)

        # provenance
        prov = g["material_mass_source_provenance"]
        v.flag(f"{bid}.prov.mass_authority", prov["mass_authority"], "reconstructed_tissue_mass")
        v.flag(f"{bid}.prov.mass_source_kind", prov["mass_source_kind"],
               "reconstructed_material_volume")
        v.flag(f"{bid}.prov.integration_model", prov["integration_model"],
               "piecewise_constant_density_over_owned_tetrahedral_cells")
        v.flag(f"{bid}.prov.mass_owner_ids", prov["mass_owner_ids"],
               sorted({"mc-owner-R", "mc-owner-S"} if bid == "mc-body-1" else {"mc-owner-D"}))
        v.flag(f"{bid}.prov.overlay_consumed", prov["surface_mass_overlay_consumed"], False)
        v.flag(f"{bid}.prov.overlay_generated", prov["surface_mass_overlay_generated"], False)
        v.flag(f"{bid}.prov.segments_consumed",
               prov["source_effective_segment_payloads_consumed"], False)
        expected_prov_cells = (["cell-R", "cell-S"] if bid == "mc-body-1" else ["cell-D"])
        v.flag(f"{bid}.cell_provenance.cell_ids",
               [row["cell_id"] for row in g["cell_provenance"]], expected_prov_cells)
        for row in g["cell_provenance"]:
            cid = row["cell_id"]
            v.flag(f"{bid}.prov.{cid}.density", row["density_kg_m3"],
                   {"cell-R": 12.0, "cell-D": 6.0, "cell-S": 9.0}[cid])
            v.flag(f"{bid}.prov.{cid}.owner", row["mass_owner_id"],
                   {"cell-R": "mc-owner-R", "cell-D": "mc-owner-D", "cell-S": "mc-owner-S"}[cid])
            v.flag(f"{bid}.prov.{cid}.region", row["region_id"],
                   {"cell-R": "mc-region-R", "cell-D": "mc-region-D", "cell-S": "mc-region-S"}[cid])
            v.flag(f"{bid}.prov.{cid}.material", row["material_id"],
                   {"cell-R": "mc-tissue-R", "cell-D": "mc-tissue-D", "cell-S": "mc-tissue-S"}[cid])
            v.flag(f"{bid}.prov.{cid}.density_source", row["density_source"],
                   "mc analytic coupon fixture")
            v.flag(f"{bid}.prov.{cid}.conditions", row["density_conditions"], "uniform")

        # map exported values back to domain for the F6 recombination check
        # (inverse of the forward contract transform: x_domain = R x_body + t,
        #  I_domain = R I_body R^T)
        R = rot[bid]
        t = org[bid]
        cb = mp["center_of_mass"]["value"]
        cd = [sum(R[j][i] * cb[i] for i in range(3)) + t[j] for j in range(3)]
        Ib = it["value"]
        Id = [[sum(R[i][k] * sum(Ib[k][l] * R[j][l] for l in range(3))
                   for k in range(3)) for j in range(3)] for i in range(3)]
        domain_recovered.append({"mass": mp["mass"]["value"], "com": cd, "inertia": Id})

    # ---- F6: recombination of the two exported bodies to the whole ----------
    whole = frozen["whole_partition"]
    M = sum(exported_masses)
    v.num("whole.mass_from_bodies", M, whole["mass"])
    tot_vol = sum(x["mass_properties"]["volume"]["value"] for x in rep["body_groups"])
    v.num("whole.volume_from_bodies", tot_vol, whole["volume"])
    C = [sum(d["mass"] * d["com"][a] for d in domain_recovered) / M for a in range(3)]
    for a, lbl in ((0, "x"), (1, "y"), (2, "z")):
        v.num(f"whole.com.{lbl}_recombined", C[a], whole["com"][a])
    I = [[0.0] * 3 for _ in range(3)]
    for d in domain_recovered:
        dd = [d["com"][k] - C[k] for k in range(3)]
        m = d["mass"]
        d2 = dd[0] ** 2 + dd[1] ** 2 + dd[2] ** 2
        for i in range(3):
            for j in range(3):
                # inertia tensors combine as I + m((d.d)E - d d^T)
                I[i][j] += d["inertia"][i][j] + m * (d2 * (1.0 if i == j else 0.0)
                                                     - dd[i] * dd[j])
    for i in range(3):
        for j in range(3):
            v.num(f"whole.inertia[{i}][{j}]_recombined", I[i][j],
                  whole["inertia_about_com"][i][j])

    text = v.report_text()
    print(text)
    with open(os.path.join(HERE, "receipts", "comparison.txt"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write(text + "\n")
    return 0 if v.fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
