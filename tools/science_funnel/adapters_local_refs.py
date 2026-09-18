"""LOCAL-REFERENCES-INTAKE lane adapters (2026-09-18). Three repo-resident human
datasets admitted through the batch connector machinery as Homo sapiens
(comparative) evidence for the macaque project -- work.data.local_refs_20260918:

  ansur2_aggregates       ANSUR II public CSVs (male 4,082 + female 1,986
                          subjects): the DERIVED per-sex tables (exactly the ten
                          columns the existing anchors' derivation reads, with
                          the anchors' unit laws and per-subject derived ratios)
                          are pinned bundle bytes; this adapter emits per-sex
                          AGGREGATE measurement records only -- person-level
                          rows are never admitted (SOURCES.md grants no
                          person-level redistribution; see the work record).
  mocap_walk_series       mocap_walk_reference.json-derived long-form curve
                          CSVs: the three gait-cycle mean joint-angle curves
                          (hip/knee/ankle, 101 samples, n_cycles=4) as series
                          records under batch.property.series.
  muscle_inventory_doc    MUSCLE_INVENTORY.md as ONE documentation-reference
                          entity pinned by its sha256 -- a citation, never
                          measurements.

Rule 1 (derive, never sweep): the selection rule, unit laws, derived formulas
and aggregation law are the anchors' own (tools/build_ansur_anchors.py and
research_references/human/ansur_anchors.json), recorded in the download
receipts and the work record. A corrupted subject row quarantines exactly
itself; nothing is dropped silently.
"""
import csv
import hashlib
import io
import statistics as st

from .adapters import ADAPTERS, rejection
from .common import Refusal, draft, number, require, text
from .units import convert

# The anchors' own derived-column set (see derive_local_refs_ansur.py; the lane
# test cross-checks this list against the deriver's).
ANSUR_COLUMNS = [
    "bmi", "eye_frac_of_stature", "foot_breadth_m", "foot_length_m",
    "hand_breadth_m", "hand_circumference_m", "hand_length_m", "head_height_m",
    "leg_frac_of_stature", "mass_kg", "stature_m", "trochanterion_m",
    "waist_frac_of_stature", "waist_height_m",
]
ANSUR_FIELD_META = {
    "stature_m": ("m", "length", "stature"),
    "trochanterion_m": ("m", "length", "trochanterion height"),
    "mass_kg": ("kg", "mass", "body mass"),
    "head_height_m": ("m", "length", "tragion-to-top-of-head height"),
    "foot_length_m": ("m", "length", "foot length"),
    "foot_breadth_m": ("m", "length", "foot breadth, horizontal"),
    "hand_length_m": ("m", "length", "hand length"),
    "hand_breadth_m": ("m", "length", "hand breadth"),
    "hand_circumference_m": ("m", "length", "hand circumference"),
    "waist_height_m": ("m", "length", "waist height, omphalion"),
    "leg_frac_of_stature": ("1", "dimensionless", "leg fraction of stature"),
    "eye_frac_of_stature": ("1", "dimensionless", "eye height fraction of stature"),
    "waist_frac_of_stature": ("1", "dimensionless", "waist height fraction of stature"),
    "bmi": ("1", "dimensionless", "body mass index"),
}
ANSUR_STATISTICS = ("median", "p5", "p95", "mean", "n")
HOMO_TAG = "Homo sapiens (comparative)"
ANSUR_UNKNOWNS = [
    "aggregate_only_person_level_rows_not_admitted",
    "ansur_ii_is_a_2012_military_population",
    "uncertainty",
]


def _read_derived_csv(raw, origin):
    """The deriver's long-format table: header + one row per subject."""
    rows = list(csv.reader(io.StringIO(raw.decode("utf-8"), newline="")))
    require(rows and rows[0] == ANSUR_COLUMNS, "ansur_header_unexpected", origin)
    out = []
    for index, cells in enumerate(rows[1:], 2):
        require(len(cells) == len(ANSUR_COLUMNS), "ansur_row_width", origin + ":row%d" % index)
        out.append((index, cells))
    require(out, "empty_capture", origin)
    return out


def _per_subject_values(cells):
    """One subject's derived row, strictly parsed and law-checked; a failing row
    refuses exactly itself (the caller quarantines that row alone)."""
    values = {}
    for column, cell in zip(ANSUR_COLUMNS, cells):
        cell = cell.strip()
        if cell == "":
            raise Refusal("empty_cell", column)
        value = float(cell)
        require(value == value and value not in (float("inf"), float("-inf")),
                "nonfinite_number", column)
        require(value > 0, "nonpositive_derived_value", column + "=" + repr(value))
        values[column] = value
    # cross-field sanity inside the derived row (the ratios must be ratios):
    require(0.3 < values["leg_frac_of_stature"] < 0.7, "derived_ratio_implausible",
            "leg_frac=" + repr(values["leg_frac_of_stature"]))
    require(0.8 < values["eye_frac_of_stature"] < 1.0, "derived_ratio_implausible",
            "eye_frac=" + repr(values["eye_frac_of_stature"]))
    require(0.3 < values["waist_frac_of_stature"] < 1.2, "derived_ratio_implausible",
            "waist_frac=" + repr(values["waist_frac_of_stature"]))
    require(10.0 < values["bmi"] < 80.0, "derived_bmi_implausible",
            repr(values["bmi"]))
    return values


def _aggregate(column, vals):
    """The anchors' own aggregation law (build_ansur_anchors.py _stats, positive
    filter a no-op because the row law refuses nonpositive values)."""
    ordered = sorted(vals)
    n = len(ordered)
    return {"median": st.median(ordered),
            "p5": ordered[int(0.05 * n)],
            "p95": ordered[min(n - 1, int(0.95 * n))],
            "mean": st.fmean(ordered),
            "n": n}


def _ansur_sex_records(sex, derived_rows):
    out = []
    per_column = {column: [] for column in ANSUR_COLUMNS}
    for origin_row, cells in derived_rows:
        try:
            values = _per_subject_values(cells)
        except (Refusal, ValueError, TypeError) as exc:
            out.append(rejection("ansur2:%s:row%d" % (sex, origin_row), exc))
            continue
        for column in ANSUR_COLUMNS:
            per_column[column].append(values[column])
    n_subjects = len(per_column["stature_m"])
    # Subject counts (male 4082, female 1986) are asserted by the lane tests on
    # the clean tables; here a quarantine must stay exactly that row's blast
    # radius, so counts are never a hard refusal inside the adapter.
    for column in ANSUR_COLUMNS:
        unit, quantity, human_name = ANSUR_FIELD_META[column]
        stats = _aggregate(column, per_column[column])
        require(stats["n"] == n_subjects, "count_identity_failed", column)
        for stat in ANSUR_STATISTICS:
            payload = convert(stats[stat], unit, quantity)
            payload.update(
                subject="ANSUR II %s population %s" % (sex, human_name),
                conditions={
                    "subject_species": HOMO_TAG,
                    "dataset": "ANSUR II (US Army Anthropometric Survey 2012, "
                               "public release 2017), %s subjects" % sex,
                    "statistic": stat,
                    "n_subjects": n_subjects,
                    "derived_column": column,
                    "derivation_provenance": "tools/build_ansur_anchors.py column "
                                             "selection + unit laws; anchors verified "
                                             "to 1e-9 by derive_local_refs_ansur.py",
                    "privacy": "aggregate only; person-level rows pinned as bundle "
                               "bytes but never admitted (SOURCES.md grants no "
                               "person-level redistribution)",
                })
            row = draft("ansur2:%s:%s:%s" % (sex, column, stat), "measurement", payload,
                        unknowns=ANSUR_UNKNOWNS,
                        label="ANSUR II %s %s %s" % (sex, human_name, stat))
            row["class_contract"] = {"class_id": "batch.property.measurement",
                                     "version": 1}
            out.append(row)
    return out


def ansur2_aggregates(raw, manifest, path):
    """Male derived table is the data artifact; the female table rides as a
    companion pinned by sha256 (the bp3d companion pattern). Both are parsed;
    only per-sex aggregates are emitted."""
    pin = manifest.get("constants", {}).get("female_derived_sha256")
    require(pin, "missing_text", "constants.female_derived_sha256")
    # Identity of the data artifact is enforced by the per-sex subject counts
    # (4082/1986) inside _ansur_sex_records -- a swapped pin refuses loudly there.
    female_raw = path.parent.joinpath(pin).read_bytes()
    out = _ansur_sex_records("male", _read_derived_csv(raw, "ansur2_male_derived.csv"))
    out += _ansur_sex_records("female",
                              _read_derived_csv(female_raw, "ansur2_female_derived.csv"))
    require(out, "empty_capture")
    return out


# ------------------------------------------------------------ mocap series

MOCAP_JOINTS = ("ankle", "hip", "knee")  # sorted, companion order
MOCAP_PREFIX = "mocap_cmus35_walk_"
MOCAP_SCALARS = ("fps", "frames", "duration_s", "cadence_steps_per_min",
                 "stride_length_m", "stride_length_leg_lengths",
                 "stride_time_s", "duty_factor", "speed_m_s", "leg_length_m")


def _mocap_series_records(joint, raw, conditions):
    """One series record per joint; ANY refusal inside a series (header, width,
    series id, sample laws) rejects that series record whole and visibly --
    never a silent drop, never a hard abort of the sibling joints."""
    try:
        rows = list(csv.reader(io.StringIO(raw.decode("utf-8"), newline="")))
        require(rows and rows[0] == ["series_id", "x_fraction", "y_deg"],
                "mocap_header_unexpected", joint)
        expected_id = MOCAP_PREFIX + joint + "_mean_cycle"
        samples, metadata = [], None
        external_id = expected_id
        for index, cells in enumerate(rows[1:], 2):
            require(len(cells) == 3, "mocap_row_width", "%s:row%d" % (joint, index))
            require(cells[0] == expected_id, "mocap_series_id_mismatch",
                    "%s:row%d:%s" % (joint, index, cells[0]))
            x = convert(number(cells[1]), "1", "dimensionless")
            y = convert(number(cells[2]), "deg", "angle")
            current = {"subject": "CMU MoCap subject 35 walk (35_01), mean "
                                  "gait cycle over 4 cycles",
                       "conditions": dict(conditions),
                       "x_quantity": x["quantity"], "x_unit_si": x["unit_si"],
                       "quantity": y["quantity"], "unit_si": y["unit_si"]}
            require(metadata is None or current == metadata,
                    "series_context_changed", external_id)
            metadata = current
            require(not samples or x["value_si"] > samples[-1]["x"],
                    "axis_not_increasing", external_id)
            samples.append({"x": x["value_si"], "value": y["value_si"],
                            "uncertainty": None})
        require(len(samples) == 101, "mocap_sample_count_unexpected",
                "%s:%d" % (joint, len(samples)))
    except Refusal as exc:
        return [rejection("mocap_cmus35:" + joint, exc)]
    row = draft(external_id, "series", {**metadata, "samples": samples,
                                        "interpolation": "unspecified",
                                        "n_cycles": 4},
                unknowns=["n_cycles_4_average_not_per_cycle_data",
                          "source_degrees_rounded_to_2dp",
                          "bvh_raw_unit_scale_measured_by_source_file",
                          "no_per_sample_uncertainty"],
                label="CMU 35 walk %s mean gait-cycle angle" % joint)
    row["class_contract"] = {"class_id": "batch.property.series", "version": 1}
    return [row]


def mocap_walk_series(raw, manifest, path):
    """The hip curve is the data artifact; knee and ankle ride as companions
    pinned by sha256 (the bp3d companion pattern)."""
    pins = manifest.get("constants", {})
    companions = {"knee": pins.get("knee_curve_sha256"),
                  "ankle": pins.get("ankle_curve_sha256")}
    require(all(companions.values()), "missing_text",
            "constants.knee_curve_sha256/ankle_curve_sha256")
    # The data artifact must carry the hip series_id; a swapped pin refuses
    # loudly inside _mocap_series_records (per-row series_id check).
    conditions = {
        "subject_species": HOMO_TAG,
        "source": "CMU MoCap subject 35 walk trial 35_01 via the una-dinosauria "
                  "BVH mirror; repo-resident research_references/human/"
                  "mocap_walk_reference.json",
        "x_semantics": "percent of gait cycle (0..100) / 100 -> dimensionless "
                       "fraction; cycle 0% = heel strike",
        "y_semantics": "sagittal vector-based joint angle: +flexion (hip, knee), "
                       "+dorsiflexion (ankle); source degrees -> SI rad",
        "signal_kind": "gait-cycle mean joint-angle envelope",
        "license": "CMU MoCap: free for research AND commercial inclusion; may "
                   "not resell the data itself; credit mocap.cs.cmu.edu + NSF "
                   "EIA-0196217",
    }
    scalars = manifest.get("constants", {}).get("spatiotemporal_scalars")
    require(isinstance(scalars, dict) and scalars, "missing_text",
            "constants.spatiotemporal_scalars")
    for key in MOCAP_SCALARS:
        require(key in scalars, "missing_text", "scalars." + key)
    conditions["spatiotemporal_scalars"] = scalars
    conventions = manifest.get("constants", {}).get("conventions_verbatim")
    require(isinstance(conventions, str) and conventions, "missing_text",
            "constants.conventions_verbatim")
    conditions["conventions_verbatim"] = conventions
    out = _mocap_series_records("hip", raw, conditions)
    for joint in ("knee", "ankle"):
        companion = path.parent.joinpath(companions[joint]).read_bytes()
        out += _mocap_series_records(joint, companion, conditions)
    require(out, "empty_capture")
    return out


# ------------------------------------------------- muscle inventory doc

def muscle_inventory_doc(raw, manifest, path):
    """ONE documentation-reference entity pinned by sha256 -- a citation, never
    measurements. The pin must equal the work record's amended pin."""
    pin = manifest.get("constants", {}).get("muscle_inventory_sha256")
    require(pin, "missing_text", "constants.muscle_inventory_sha256")
    require(hashlib.sha256(raw).hexdigest() == pin, "pin_drift", path.name)
    decoded = raw.decode("utf-8")
    require(decoded.startswith("# "), "muscle_inventory_header_unexpected", path.name)
    title = decoded.split("\n", 1)[0][2:].strip()
    payload = {
        "document": "repo-resident research_references/human/MUSCLE_INVENTORY.md",
        "sha256": pin,
        "bytes": len(raw),
        "title": title,
        "role": "documentation reference: per-muscle mechanical role text and "
                "citations over the myo_sim 290-actuator inventory",
        "cites": ["Neumann, Kinesiology of the Musculoskeletal System",
                  "Ward et al. 2009 (measured cadaver architecture)",
                  "Rajagopal et al. 2016 (leg model)",
                  "Saul et al. 2015 (arm model)",
                  "Christophy et al. 2012 (lumbar spine musculature)",
                  "Caggiano et al. 2022 (MyoSuite)"],
        "subject_species": HOMO_TAG,
    }
    row = draft("muscle_inventory_doc_20260918", "entity", payload,
                unknowns=["prose_document_not_machine_parsed",
                          "muscle_role_text_not_reified_as_records"],
                label="THE MUSCLE INVENTORY (documentation reference, sha-pinned)")
    row["class_contract"] = {"class_id": "batch.entity.external", "version": 1}
    return [row]


LOCAL_REFS_ADAPTERS = {
    "ansur2_aggregates": ansur2_aggregates,
    "mocap_walk_series": mocap_walk_series,
    "muscle_inventory_doc": muscle_inventory_doc,
}
