"""Shared comparison helpers + comparison ledger for MAT2-B02 probes.

Every individual field comparison goes through expect_* and is counted.
Counter and label list are deterministic; the diagnostics artifact records
the totals (frozen prediction P-COUNT).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

WORK = Path(__file__).resolve().parent
RUNS = WORK / "runs"
COUPONS = WORK / "coupons"
FROZEN_TOOLS = WORK / "frozen" / "1af0bbde" / "tools"

COUNTS = {"comparisons": 0, "labels": []}


def _count(label):
    COUNTS["comparisons"] += 1
    COUNTS["labels"].append(label)


def tol1(actual, expected, label):
    """T1: 1e-12 relative where |expected| >= 1, else 1e-12 absolute."""
    _count(label)
    expected = float(expected)
    actual = float(actual)
    if abs(expected) >= 1.0:
        ok = abs(actual - expected) / abs(expected) <= 1e-12
    else:
        ok = abs(actual - expected) <= 1e-12
    if not ok:
        raise AssertionError(
            f"T1 violation {label}: actual={actual!r} expected={expected!r} "
            f"diff={actual - expected!r}")


def tol1_rel(actual, expected, label):
    """T1 pure relative (for sweep relations with huge expected values)."""
    _count(label)
    expected = float(expected)
    actual = float(actual)
    if expected == 0.0:
        ok = actual == 0.0
    else:
        ok = abs(actual - expected) / abs(expected) <= 1e-12
    if not ok:
        raise AssertionError(
            f"T1rel violation {label}: actual={actual!r} expected={expected!r}")


def tol2(actual, expected, label):
    """T2 (large-coordinate budget): 1e-9 relative for inertia, and the same
    1e-9 threshold as an absolute bound for COM-sized values (|expected|<1)."""
    _count(label)
    expected = float(expected)
    actual = float(actual)
    if abs(expected) >= 1.0:
        ok = abs(actual - expected) / abs(expected) <= 1e-9
    else:
        ok = abs(actual - expected) <= 1e-9
    if not ok:
        raise AssertionError(
            f"T2 violation {label}: actual={actual!r} expected={expected!r}")


def expect_equal(actual, expected, label):
    _count(label)
    if actual != expected:
        raise AssertionError(f"equality violation {label}: "
                             f"actual={actual!r} expected={expected!r}")


def expect_true(condition, label):
    _count(label)
    if not condition:
        raise AssertionError(f"condition violation {label}")


def load_coupon(tag):
    def read(kind):
        return json.loads((COUPONS / f"coupon_{tag}_{kind}.json").read_text())
    return read("manifest"), read("partition"), read("groups")


def export_in_process(tag):
    """Run the pinned exporter in-process on a coupon tag."""
    import sys
    if str(FROZEN_TOOLS) not in sys.path:
        sys.path.insert(0, str(FROZEN_TOOLS))
    import material_volume_body_export as exporter
    manifest, partition, groups = load_coupon(tag)
    return exporter.build_export_report(manifest, partition, groups)


def mass_fields(report):
    """Flatten every mass-property number of the report, with labels."""
    fields = []
    for group in report["body_groups"]:
        bid = group["body_id"]
        props = group["mass_properties"]
        if not props:
            continue
        fields.append((f"{bid}.mass", props["mass"]["value"]))
        fields.append((f"{bid}.volume", props["volume"]["value"]))
        for axis, value in enumerate(props["center_of_mass"]["value"]):
            fields.append((f"{bid}.com_body[{axis}]", value))
        tensor = props["inertia_tensor_about_com"]["value"]
        for i in range(3):
            for j in range(3):
                fields.append((f"{bid}.inertia_com[{i}][{j}]", tensor[i][j]))
    return fields


def compare_report_vs_expected(report, expected, tol, prefix):
    """expected: body_id -> dict(mass, volume, com_body(3), inertia(3x3))."""
    expect_equal(len(report["body_groups"]), len(expected), f"{prefix}.body_count")
    for group in report["body_groups"]:
        bid = group["body_id"]
        props = group["mass_properties"]
        exp = expected[bid]
        tol(props["mass"]["value"], exp["mass"], f"{prefix}.{bid}.mass")
        tol(props["volume"]["value"], exp["volume"], f"{prefix}.{bid}.volume")
        for axis in range(3):
            tol(props["center_of_mass"]["value"][axis], exp["com_body"][axis],
                f"{prefix}.{bid}.com_body[{axis}]")
        for i in range(3):
            for j in range(3):
                tol(props["inertia_tensor_about_com"]["value"][i][j],
                    exp["inertia"][i][j],
                    f"{prefix}.{bid}.inertia[{i}][{j}]")


def exact_body_expectations(cells, density_by_cell, frame):
    """Exact oracle values for one body, expressed in its authored body frame.

    frame: (rotation 3x3, origin 3) applied as the pinned exporter does:
    x_body = R^T (x_domain - o), I_body = R^T I_domain R; R entries must be
    exact Fractions/ints.
    """
    import b02_oracle
    from fractions import Fraction
    rotation, origin = frame
    volume, mass, com, inertia = b02_oracle.body_properties_exact(
        cells, density_by_cell)
    centered = [com[k] - Fraction(origin[k]) for k in range(3)]
    com_body = [sum(rotation[k][d] * centered[k] for k in range(3))
                for d in range(3)]
    inertia_body = [[sum(rotation[k][a] * inertia[k][l] * rotation[l][b]
                         for k in range(3) for l in range(3))
                     for b in range(3)] for a in range(3)]
    return {"mass": mass, "volume": volume, "com_domain": com,
            "inertia_domain": inertia, "com_body": com_body,
            "inertia_body": inertia_body}


def oracle_float(value):
    import b02_oracle
    return b02_oracle.to_float(value)


SQRT2_OVER_2 = math.sqrt(2.0) / 2.0
