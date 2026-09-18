"""ansur_derive.py -- Rule 1 derivation for lane local-refs-20260918.

Reads the repo-resident ANSUR II public CSVs (research_references/human/, cp1252)
and writes the two deterministic per-sex derived tables under
tools/science_funnel/data/ansur2_derived_20260918/ -- EXACTLY the ten columns the
existing anchors' own derivation reads (tools/build_ansur_anchors.py) with the
anchors' unit laws, plus per-subject derived ratios and BMI computed from the raw
values exactly as the anchors compute them.

Rule 0 (banked first as work.data.local_refs_20260918): the anchors' published
aggregates must reproduce from the raw rows under this recorded derivation --
checked here BEFORE any table is written; any mismatch refuses loudly.

Privacy law: raw CSV rows remain only in the repo-resident
research_references/human/ source location; this intake directory contains
only deterministic derived tables and their provenance receipt. The graph
admits aggregates only.

Deterministic: fixed column order, fixed row order (file order), repr() float
formatting, no locale, no timestamps beyond the receipt's fixed day stamp.
"""
import csv
import io
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path.cwd()
HERE = ROOT / "research_references" / "human"
OUT = ROOT / "tools" / "science_funnel" / "data" / "ansur2_derived_20260918"
DAY = "2026-09-18"

# The anchors' own column set (tools/build_ansur_anchors.py) -- the recorded
# selection rule. Nothing else enters the derivation.
RAW_COLUMNS = ["stature", "trochanterionheight", "weightkg", "tragiontopofhead",
               "footlength", "footbreadthhorizontal", "handlength", "handbreadth",
               "handcircumference", "waistheightomphalion"]
SI_COLUMNS = ["stature_m", "trochanterion_m", "mass_kg", "head_height_m",
              "foot_length_m", "foot_breadth_m", "hand_length_m", "hand_breadth_m",
              "hand_circumference_m", "waist_height_m"]
DERIVED_COLUMNS = ["leg_frac_of_stature", "eye_frac_of_stature",
                   "waist_frac_of_stature", "bmi"]
COLUMNS = sorted(SI_COLUMNS + DERIVED_COLUMNS)

SEXES = {
    "male": ("ANSUR_II_MALE_Public.csv", 4082),
    "female": ("ANSUR_II_FEMALE_Public.csv", 1986),
}


def fnum(text):
    """Strict float parse; refuse empty/garbage (the row quarantines itself)."""
    value = float(text)
    if value != value or value in (float("inf"), float("-inf")):
        raise ValueError("nonfinite")
    return value


def read_rows(path):
    with open(path, newline="", encoding="cp1252") as stream:
        reader = csv.DictReader(stream)
        missing = [c for c in RAW_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit("REFUSE: raw columns missing from %s: %s" % (path.name, missing))
        return reader.fieldnames, list(reader)


def derive_sex(rows):
    """Per-subject derived rows. A row failing any law quarantines EXACTLY itself
    (1-based CSV data-row index + reason); nothing else is dropped or altered."""
    derived, quarantine = [], []
    for index, row in enumerate(rows, 2):  # CSV data row number (header = 1)
        try:
            raw = {}
            for column in RAW_COLUMNS:
                cell = (row.get(column) or "").strip()
                if cell == "":
                    raise ValueError("empty_cell:" + column)
                value = fnum(cell)
                if value <= 0:
                    raise ValueError("nonpositive:" + column + "=" + repr(value))
                raw[column] = value
            s, t = raw["stature"], raw["trochanterionheight"]
            w, e = raw["weightkg"], raw["tragiontopofhead"]
            waist = raw["waistheightomphalion"]
            values = {
                "stature_m": s * 0.001,
                "trochanterion_m": t * 0.001,
                "mass_kg": w * 0.1,
                "head_height_m": e * 0.001,
                "foot_length_m": raw["footlength"] * 0.001,
                "foot_breadth_m": raw["footbreadthhorizontal"] * 0.001,
                "hand_length_m": raw["handlength"] * 0.001,
                "hand_breadth_m": raw["handbreadth"] * 0.001,
                "hand_circumference_m": raw["handcircumference"] * 0.001,
                "waist_height_m": waist * 0.001,
                "leg_frac_of_stature": t / s,
                "eye_frac_of_stature": (s - e) / s,
                "waist_frac_of_stature": waist / s,
                "bmi": w * 0.1 / (s * 0.001) ** 2,
            }
            derived.append({c: values[c] for c in COLUMNS})
        except (ValueError, TypeError) as exc:
            quarantine.append({"location": "csv_row:%d" % index,
                               "refusal": {"code": "row_law_violation",
                                           "detail": str(exc)}})
    return derived, quarantine


def aggregate(values_per_column):
    """The anchors' own aggregation law: median, p5 = sorted[int(0.05*n)],
    p95 = sorted[min(n-1, int(0.95*n))], mean (fmean), n. All admitted values
    are positive by the row law, so the anchors' positive filter is a no-op."""
    out = {}
    for column, vals in values_per_column.items():
        ordered = sorted(vals)
        n = len(ordered)
        out[column] = {"median": st.median(ordered),
                       "p5": ordered[int(0.05 * n)],
                       "p95": ordered[min(n - 1, int(0.95 * n))],
                       "mean": st.fmean(ordered),
                       "n": n}
    return out


def verify_anchors(derived, sex):
    """Rule 0 gate: the published anchors must reproduce from the raw rows under
    this derivation (relative tolerance 1e-9 on every median/p5/p95/mean; n exact)."""
    anchors = json.loads((HERE / "ansur_anchors.json").read_text(encoding="utf-8"))
    fields = {
        "stature_m": ["stature_m"], "trochanterion_m": ["trochanterion_m"],
        "leg_frac_of_stature": ["leg_frac_of_stature"],
        "eye_frac_of_stature": ["eye_frac_of_stature"], "bmi": ["bmi"],
        "mass_kg": ["mass_kg"], "foot_length_m": ["foot_length_m"],
        "foot_breadth_m": ["foot_breadth_m"], "hand_length_m": ["hand_length_m"],
        "hand_breadth_m": ["hand_breadth_m"],
        "hand_circumference_m": ["hand_circumference_m"],
        "head_height_m": ["head_height_m"],
        "waist_frac_of_stature": ["waist_frac_of_stature"],
    }
    report = {}
    ok_all = True
    for anchor_field, columns in fields.items():
        for column in columns:
            vals = [row[column] for row in derived]
            stats = aggregate({column: vals})[column]
            published = anchors[sex][anchor_field]
            field_ok = (stats["n"] == published["n"]
                        and abs(stats["median"] - published["median"]) <= 1e-9 * max(1.0, abs(published["median"]))
                        and abs(stats["p5"] - published["p5"]) <= 1e-9 * max(1.0, abs(published["p5"]))
                        and abs(stats["p95"] - published["p95"]) <= 1e-9 * max(1.0, abs(published["p95"]))
                        and abs(stats["mean"] - published["mean"]) <= 1e-9 * max(1.0, abs(published["mean"])))
            report[column] = {"matches_anchor_" + anchor_field: bool(field_ok),
                              "computed_median": stats["median"],
                              "published_median": published["median"]}
            ok_all = ok_all and field_ok
    return ok_all, report


def write_csv(path, rows):
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(COLUMNS)
    for row in rows:
        writer.writerow([repr(row[c]) for c in COLUMNS])
    path.write_bytes(buffer.getvalue().encode("utf-8"))


def canonical_source_bytes(src):
    """Hash the resident source in its committed LF form without copying
    person-level rows into the intake data directory."""
    return src.read_bytes().replace(b"\r\n", b"\n")


def main() -> int:
    if not HERE.is_dir() or not OUT.parent.is_dir():
        print("REFUSE: run from the worktree root")
        return 1
    OUT.mkdir(exist_ok=True)
    receipt = {
        "schema": "chimera.local_refs.derive.v1",
        "derived_utc_day": DAY,
        "rule": "derive, never sweep -- exactly the anchors' own column set and laws",
        "selection_rule": {
            "columns_raw": RAW_COLUMNS,
            "columns_si": SI_COLUMNS,
            "columns_derived": DERIVED_COLUMNS,
            "provenance_of_rule": "tools/build_ansur_anchors.py (the existing anchors' own derivation)",
            "unit_laws": ["lengths mm -> m", "weightkg is 100-g units -> kg (x0.1)"],
            "derived_formulas": {
                "leg_frac_of_stature": "trochanterionheight / stature",
                "eye_frac_of_stature": "(stature - tragiontopofhead) / stature",
                "waist_frac_of_stature": "waistheightomphalion / stature",
                "bmi": "weightkg*0.1 / (stature*0.001)^2",
            },
            "aggregation_law": "median; p5 = sorted[int(0.05*n)]; p95 = sorted[min(n-1,int(0.95*n))]; mean (fmean); n",
            "row_law": "all ten raw cells present, parseable, positive; a failing row quarantines exactly itself",
            "row_retention": "full rows per sex (the anchors' aggregates are full-population summaries)",
        },
        "privacy_law": {
            "aggregate_only_admission": True,
            "statement": "SOURCES.md records the CSVs as 'DOWNLOADED (mirror of the Penn State "
                         "OPEN Design Lab release; US Gov work, public since 2017)' and grants no "
                         "person-level redistribution; raw rows stay repo-resident and are pinned "
                         "here only as bundle bytes; the graph admits per-sex aggregates only. "
                         "A recorded redistribution grant would falsify this decision.",
        },
        "source_repo_files": {},
        "files": [],
        "sexes": {},
    }

    def add_file_entry(path, url, raw):
        import hashlib
        receipt["files"].append({"path": path, "url": url, "bytes": len(raw),
                                 "sha256": hashlib.sha256(raw).hexdigest()})

    for sex, (filename, expected_rows) in SEXES.items():
        src = HERE / filename
        if not src.is_file():
            print("REFUSE: missing source", src)
            return 1
        fieldnames, rows = read_rows(src)
        derived, quarantine = derive_sex(rows)
        if len(rows) != expected_rows:
            print("REFUSE: %s has %d data rows, expected %d" % (filename, len(rows), expected_rows))
            return 1
        ok, report = verify_anchors(derived, sex)
        if not ok:
            print("REFUSE: anchors do not reproduce for", sex)
            for column, entry in report.items():
                if not entry.get("matches_anchor_stature_m") and not entry.get("matches_anchor_mass_kg") \
                        and not any(v is True for k, v in entry.items() if k.startswith("matches_anchor_")):
                    print("  ", column, entry)
            return 1
        table = OUT / ("ansur2_%s_derived.csv" % sex)
        write_csv(table, derived)
        source_bytes = canonical_source_bytes(src)
        import hashlib
        receipt["source_repo_files"]["research_references/human/" + filename] = {
            "bytes": len(source_bytes),
            "sha256": hashlib.sha256(source_bytes).hexdigest(),
            "source": "repo-resident research_references/human/" + filename,
            "admission": "source remains resident; person-level rows are not copied "
                         "into the intake bundle"}
        receipt["sexes"][sex] = {
            "derived_table": table.name,
            "source_csv_rows": len(rows),
            "derived_rows": len(derived),
            "quarantined_rows": len(quarantine),
            "quarantine": quarantine,
            "anchor_verification": report,
            "aggregates": aggregate({c: [row[c] for row in derived] for c in COLUMNS}),
        }
        print("%s: %d rows derived, %d quarantined, anchors verified" %
              (sex, len(derived), len(quarantine)))
    for table_name in ("ansur2_male_derived.csv", "ansur2_female_derived.csv"):
        add_file_entry(table_name,
                       "derived by tools/science_funnel/derive_local_refs_ansur.py "
                       "from repo-resident research_references/human/ ANSUR II CSVs "
                       "(anchors' own column set and laws)",
                       (OUT / table_name).read_bytes())
    (OUT / "download_receipt.json").write_text(
        json.dumps(receipt, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="")
    print("wrote", OUT / "download_receipt.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
