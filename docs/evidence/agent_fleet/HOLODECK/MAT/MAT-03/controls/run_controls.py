"""run_controls.py -- execute the preregistered R1-R4 controls against the
MAT-03 reference model in one process and write the retained check files.

Usage:  python controls/run_controls.py .        (from this MAT-03 directory)
        python controls/run_controls.py <MAT-03-dir>

Writes checks/r1_positive_imports.txt, checks/r2_missing_context_negatives.txt,
checks/r3_falsifier_membership.txt, checks/r4_versioning_immutability.txt.
Bytecode writing is disabled: no __pycache__ is produced or committed.
Every acceptance/refusal is recorded verbatim; every post-state assertion is
computed and printed. Exit 1 if any preregistered threshold misses.
"""
from __future__ import annotations

import dataclasses
import math
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True          # no __pycache__ in the evidence tree
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "reference"))

from mat03_reference_model import (DatasetStore, GATE_ORDER,  # noqa: E402
                                   Mat03Refusal, SourceRegistry,
                                   _canonical_hash, interpolate,
                                   propagate_product, propagate_sum)

CHECKS = HERE / "checks"
CHECKS.mkdir(exist_ok=True)


class Log:
    """Verbatim transcript of one control run."""

    def __init__(self, title, threshold):
        self.lines = [title, "=" * 78, f"threshold: {threshold}", ""]
        self.passed = 0
        self.failed = 0

    def row(self, ok, label, detail=""):
        self.lines.append(f"[{'PASS' if ok else 'FAIL'}] {label}"
                          + (f"\n        {detail}" if detail else ""))
        self.passed += ok
        self.failed += not ok

    def finish(self, path):
        self.lines.append("")
        self.lines.append(f"passed {self.passed}  failed {self.failed}")
        path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")
        return self.failed == 0


def expect_refusal(log, label, reason, fn, *args, **kwargs):
    """Run fn; assert it refuses with the NAMED reason; return the refusal."""
    try:
        fn(*args, **kwargs)
    except Mat03Refusal as r:
        ok = r.reason == reason
        log.row(ok, label, f"refused verbatim: {r!r}"
                + ("" if ok else f"  EXPECTED reason {reason!r}"))
        return r
    except Exception as e:                                   # noqa: BLE001
        log.row(False, label, f"WRONG refusal class {type(e).__name__}: {e}")
        return None
    log.row(False, label, "NO REFUSAL -- the gate did not fire")
    return None


# ---- fixture: a complete measured dataset (and its mutants) ---------------

CIT_A = {"source_id": "FHWA-TUB-2020",
         "locator": "FHWA-HRT-20-054 Table 4-3",
         "note": "polymer tub stiffness versus temperature, conditioned "
                 "coupons"}


def envelope():
    return {"temperature": {"lo": 290, "hi": 330, "unit": "k"},
            "moisture": {"lo": 0.4, "hi": 0.6, "unit": "fraction"},
            "strain_rate": {"lo": 1e-3, "hi": 1e-3, "unit": "1/s"}}


def record_a300(**over):
    r = {"property": "modulus", "value": 1200, "unit": "MPa",
         "uncertainty": 40,
         "conditions": {"temperature": {"value": 300, "unit": "k"},
                        "moisture": {"value": 0.5, "unit": "fraction"},
                        "strain_rate": {"value": 1e-3, "unit": "1/s"}}}
    r.update(over)
    return r


def payload_a(version=1, **over):
    p = {"id": "measured_A", "version": version,
         "envelope": envelope(),
         "records": [record_a300(),
                     record_a300(value=1150, uncertainty=38,
                                 conditions={"temperature": {"value": 320,
                                                             "unit": "k"},
                                             "moisture": {"value": 0.5,
                                                          "unit": "fraction"},
                                             "strain_rate": {"value": 1e-3,
                                                             "unit": "1/s"}})]}
    p.update(over)
    return p


KNOWN = SourceRegistry()
KNOWN.register("FHWA-TUB-2020", "FHWA-HRT-20-054")

W = {}      # cross-row working state (R1 -> R4 post-state assertions)


def run_r1():
    log = Log("R1 -- positive imports (model must ACCEPT)",
              "8/8 legal admissions; source identity retained verbatim; "
              "affine degC->K and percent->fraction exact; versioned "
              "amendment; uncertainty propagation; in-envelope interpolation")
    store = DatasetStore()

    # (a) a complete two-record dataset imports -> version 1 stored
    a1 = store.import_dataset(payload_a(1), CIT_A, KNOWN)
    ok = (a1.version == 1 and store.listing() == {"measured_A": [1]}
          and len(a1.records) == 2)
    log.row(ok, "(a) complete dataset imports, v1 stored",
            f"listing={store.listing()} records={len(a1.records)}")
    W["a1"] = a1
    W["a1_payload"] = payload_a(1)
    W["store"] = store

    # (b) source identity retained: citation verbatim + content hash recomputed
    cit = a1.citation
    ok = (cit.source_id == CIT_A["source_id"]
          and cit.locator == CIT_A["locator"] and cit.note == CIT_A["note"]
          and a1.content_sha256 == _canonical_hash(W["a1_payload"]))
    log.row(ok, "(b) citation verbatim + stored content_sha256 == recomputed",
            f"source_id={cit.source_id!r} sha256={a1.content_sha256[:16]}...")

    # (c) affine temperature: 26.85 degC stores canonical 300.0 K EXACTLY
    p = payload_a(1, id="measured_degc")
    p["records"] = [record_a300(
        conditions={"temperature": {"value": 26.85, "unit": "degc"},
                    "moisture": {"value": 0.5, "unit": "fraction"},
                    "strain_rate": {"value": 1e-3, "unit": "1/s"}})]
    d = store.import_dataset(p, CIT_A, KNOWN)
    t = d.records[0].conditions["temperature"]
    log.row(t == 300.0, "(c) 26.85 degC -> canonical 300.0 K exactly "
            "(offset applied, not a scale)", f"measured {t!r}")
    W["degc_id"] = "measured_degc"

    # (d) moisture scale: 50 percent stores canonical 0.5 fraction
    p = payload_a(1, id="measured_pct")
    p["records"] = [record_a300(
        conditions={"temperature": {"value": 300, "unit": "k"},
                    "moisture": {"value": 50, "unit": "percent"},
                    "strain_rate": {"value": 1e-3, "unit": "1/s"}})]
    d = store.import_dataset(p, CIT_A, KNOWN)
    m = d.records[0].conditions["moisture"]
    log.row(m == 0.5, "(d) 50 percent -> canonical 0.5 fraction",
            f"measured {m!r}")

    # (e) version amendment: v2 imports; v1 stays readable and byte-identical
    v1_sha_before = a1.content_sha256
    v1_records_before = a1.records
    a2 = store.import_dataset(payload_a(2), CIT_A, KNOWN)
    a1_after = store.get("measured_A", 1)
    ok = (a2.version == 2
          and store.listing()["measured_A"] == [1, 2]
          and a1_after.content_sha256 == v1_sha_before
          and a1_after.records == v1_records_before)
    log.row(ok, "(e) v2 amendment imports; v1 byte-identical; history [1, 2]",
            f"listing={store.listing()}")
    W["a2"] = a2

    # (f) uncertainty propagation, sum: u = sqrt(ua^2 + ub^2) (canonical Pa)
    r1, r2 = a1.records[0], a1.records[1]
    s = propagate_sum(r1, r2)
    exp_v = r1.quantity.value + r2.quantity.value
    exp_u = math.sqrt(r1.uncertainty ** 2 + r2.uncertainty ** 2)
    ok = (s.quantity.value == exp_v and s.uncertainty == exp_u
          and s.citation.source_id
          == f"{r1.citation.source_id}+{r2.citation.source_id}"
          and "sqrt(ua^2 + ub^2)" in s.citation.note)
    log.row(ok, "(f) propagate_sum: value a+b, u=sqrt(ua^2+ub^2), "
            "both parent citations carried",
            f"value={s.quantity.value!r} u={s.uncertainty!r} "
            f"dim={s.quantity.dimension!r}")

    # (g) uncertainty propagation, product (relative form), MATH-01 composition
    p = payload_a(1, id="measured_strain")
    p["records"] = [record_a300(property="strain", value=0.004, unit="1",
                                uncertainty=0.0002)]
    ds = store.import_dataset(p, CIT_A, KNOWN)
    st = ds.records[0]
    prod = propagate_product(r1, st)
    exp_v = r1.quantity.value * st.quantity.value
    exp_u = abs(exp_v) * math.sqrt((r1.uncertainty / r1.quantity.value) ** 2
                                   + (st.uncertainty / st.quantity.value) ** 2)
    ok = (prod.quantity.value == exp_v and prod.uncertainty == exp_u
          and prod.quantity.dimension == r1.quantity.dimension)
    log.row(ok, "(g) propagate_product: Pa x dimensionless -> Pa via "
            "MATH-01 algebra; u relative form exact",
            f"value={prod.quantity.value!r} u={prod.uncertainty!r} "
            f"dim={prod.quantity.dimension!r}")

    # (h) interpolation INSIDE the envelope carries both bracket citations
    ip = interpolate(a1, "modulus",
                     {"temperature": {"value": 310, "unit": "k"},
                      "moisture": {"value": 0.5, "unit": "fraction"},
                      "strain_rate": {"value": 1e-3, "unit": "1/s"}})
    exp_val = r1.quantity.value + 0.5 * (r2.quantity.value - r1.quantity.value)
    exp_unc = 0.5 * r1.uncertainty + 0.5 * r2.uncertainty
    ok = (ip.quantity.value == exp_val and ip.uncertainty == exp_unc
          and ip.citations == (r1.citation, r2.citation)
          and ip.interpolated is True)
    log.row(ok, "(h) interpolate at 310 K: linear value + linear "
            "uncertainty, both bracket citations, marked interpolated",
            f"value={ip.quantity.value!r} u={ip.uncertainty!r} "
            f"citations={[c.source_id for c in ip.citations]}")
    W["ip"] = ip
    return log


def run_r2():
    log = Log("R2 -- card-prediction negatives: imports reject missing "
              "physical context (model must REFUSE)",
              "8/8 named refusals verbatim; registry post-state unchanged in "
              "every case")
    store = W["store"]
    before = store.listing()

    def store_unchanged(label):
        log.row(store.listing() == before, f"post-state unchanged after {label}",
                f"listing={store.listing()}")

    # (a) blank citation locator
    bad_cit = dict(CIT_A, locator="   ")
    expect_refusal(log, "(a) blank locator -> missing_source_identity",
                   "missing_source_identity",
                   store.import_dataset, payload_a(1, id="x_a"), bad_cit, KNOWN)
    store_unchanged("a")
    # (b) citation note absent
    bad_cit = {"source_id": "S", "locator": "L"}
    expect_refusal(log, "(b) note absent -> missing_source_identity",
                   "missing_source_identity",
                   store.import_dataset, payload_a(1, id="x_b"), bad_cit, KNOWN)
    store_unchanged("b")
    # (c) record omits the temperature condition
    p = payload_a(1, id="x_c")
    rec = record_a300()
    del rec["conditions"]["temperature"]
    p["records"] = [rec]
    expect_refusal(log, "(c) record without temperature -> missing_condition",
                   "missing_condition", store.import_dataset, p, CIT_A, KNOWN)
    store_unchanged("c")
    # (d) record without uncertainty
    p = payload_a(1, id="x_d")
    rec = record_a300()
    del rec["uncertainty"]
    p["records"] = [rec]
    expect_refusal(log, "(d) record without uncertainty -> "
                   "missing_uncertainty", "missing_uncertainty",
                   store.import_dataset, p, CIT_A, KNOWN)
    store_unchanged("d")
    # (e) NaN value
    p = payload_a(1, id="x_e")
    p["records"] = [record_a300(value=float("nan"))]
    expect_refusal(log, "(e) NaN value -> nonfinite", "nonfinite",
                   store.import_dataset, p, CIT_A, KNOWN)
    store_unchanged("e")
    # (f) negative modulus with a complete citation
    p = payload_a(1, id="x_f")
    p["records"] = [record_a300(value=-5)]
    expect_refusal(log, "(f) negative modulus -> bad_value", "bad_value",
                   store.import_dataset, p, CIT_A, KNOWN)
    store_unchanged("f")
    # (g) undeclared condition unit
    p = payload_a(1, id="x_g")
    p["records"] = [record_a300(
        conditions={"temperature": {"value": 300, "unit": "degF"},
                    "moisture": {"value": 0.5, "unit": "fraction"},
                    "strain_rate": {"value": 1e-3, "unit": "1/s"}})]
    expect_refusal(log, "(g) undeclared unit degF -> unknown_condition_unit",
                   "unknown_condition_unit", store.import_dataset, p, CIT_A,
                   KNOWN)
    store_unchanged("g")
    # (h) version 1 re-import after v2 exists
    expect_refusal(log, "(h) v1 after v2 exists -> version_regression",
                   "version_regression", store.import_dataset,
                   payload_a(1), CIT_A, KNOWN)
    store_unchanged("h")
    return log


def run_r3():
    log = Log("R3 -- CARD FALSIFIER probe: provenance membership is NOT "
              "proof of authentic measurement (model must not let "
              "membership do admission work)",
              "6/6: known-source-but-incomplete refused 3 ways; "
              "unknown-source-but-complete admitted; no membership gate "
              "exists; identity_mismatch fires regardless of membership")
    store = W["store"]
    before = store.listing()

    def strip(axis=None, uncert=False, value_over=None):
        p = payload_a(1, id=f"x_r3_{axis}{uncert}{value_over}")
        rec = record_a300(value=value_over) if value_over else record_a300()
        if axis:
            del rec["conditions"][axis]
        if uncert:
            del rec["uncertainty"]
        p["records"] = [rec]
        return p

    # (a) KNOWN source, moisture stripped -> refused missing_condition
    expect_refusal(log, "(a) known source, moisture stripped -> "
                   "missing_condition", "missing_condition",
                   store.import_dataset, strip("moisture"), CIT_A, KNOWN)
    # (b) KNOWN source, uncertainty stripped
    expect_refusal(log, "(b) known source, uncertainty stripped -> "
                   "missing_uncertainty", "missing_uncertainty",
                   store.import_dataset, strip(uncert=True), CIT_A, KNOWN)
    # (c) KNOWN source, physically impossible value
    expect_refusal(log, "(c) known source, negative modulus -> bad_value",
                   "bad_value", store.import_dataset,
                   strip(value_over=-5), CIT_A, KNOWN)
    log.row(store.listing() == before, "post-state unchanged after a-c",
            f"listing={store.listing()}")

    # (d) INVERSE probe: UNKNOWN source, complete context -> ADMITTED
    new_cit = {"source_id": "NEW-LAB-2026", "locator": "internal lab run 4711",
               "note": "unregistered source, complete physical context"}
    d = store.import_dataset(payload_a(1, id="measured_new"), new_cit, KNOWN)
    log.row(store.listing().get("measured_new") == [1]
            and not KNOWN.knows("NEW-LAB-2026"),
            "(d) unknown source, complete context ADMITTED; registry "
            "membership neither required nor changed",
            f"listing={store.listing()} "
            f"knows(NEW-LAB-2026)={KNOWN.knows('NEW-LAB-2026')}")

    # (e) structural audit: no membership/known-source gate exists; admission
    #     outcome identical with or without a populated registry
    no_member = (all("membership" not in g and "known_source" not in g
                     and "provenance" not in g for g in GATE_ORDER)
                 and len(GATE_ORDER) == 12)
    s1 = DatasetStore()
    d1 = s1.import_dataset(payload_a(1), CIT_A, None)
    s2 = DatasetStore()
    d2 = s2.import_dataset(payload_a(1), CIT_A,
                           SourceRegistry())          # empty registry
    s3 = DatasetStore()
    d3 = s3.import_dataset(payload_a(1), CIT_A, KNOWN)  # populated registry
    same = (d1.content_sha256 == d2.content_sha256 == d3.content_sha256)
    log.row(no_member and same,
            "(e) GATE_ORDER has no membership gate (12 named gates) and "
            "admission is identical with None/empty/populated registry",
            f"gate_list={list(GATE_ORDER)} identical_sha={same}")

    # (f) declared identity mismatch, known source, complete citation
    p = payload_a(1, id="x_r3_f", content_sha256="0" * 64)
    expect_refusal(log, "(f) declared content_sha256 mismatch -> "
                   "identity_mismatch (even known source + complete "
                   "citation)", "identity_mismatch",
                   store.import_dataset, p, CIT_A, KNOWN)
    log.row(store.listing()["measured_new"] == [1],
            "post-state: only the (d) admission landed",
            f"listing={store.listing()}")
    return log


def run_r4():
    log = Log("R4 -- versioned datasets + immutability (card statement)",
              "6/6: frozen records/datasets; v1 byte-identical after v2; "
              "duplicate re-imports refused; bad_version refused; history "
              "order preserved")
    store = W["store"]
    a1 = store.get("measured_A", 1)
    a1_sha = a1.content_sha256
    a1_records = a1.records

    # (a) frozen: attribute assignment raises, record unchanged
    froze = []
    for obj, attr, val, label in ((a1, "version", 5, "dataset.version"),
                                  (a1.records[0], "uncertainty", 0,
                                   "record.uncertainty")):
        try:
            setattr(obj, attr, val)
            froze.append(f"{label}: NO raise")
        except dataclasses.FrozenInstanceError:
            froze.append(f"{label}: FrozenInstanceError")
    ok = (a1.version == 1 and a1.records[0].uncertainty > 0
          and all("FrozenInstanceError" in f for f in froze))
    log.row(ok, "(a) admitted dataset/records are frozen (assignment raises)",
            "; ".join(froze))

    # (b) v1 content byte-identical after the v2 import (R1(e) imported v2)
    ok = (store.get("measured_A", 1).content_sha256 == a1_sha
          and store.get("measured_A", 1).records == a1_records
          and a1_sha == _canonical_hash(W["a1_payload"]))
    log.row(ok, "(b) v1 hash + records byte-identical after v2 exists",
            f"sha256={a1_sha[:16]}...")

    # (c) duplicate (id, version) at the CURRENT max, different content.
    #     Target: measured_new (current max v1). measured_A is at v2, so a
    #     v1 re-import THERE is version_regression (R2(h) semantics), not a
    #     duplicate.
    new_cit = {"source_id": "NEW-LAB-2026", "locator": "internal lab run 4711",
               "note": "unregistered source, complete physical context"}
    new_sha_before = store.get("measured_new", 1).content_sha256
    p = payload_a(1, id="measured_new")
    p["records"] = [record_a300(value=999)]
    expect_refusal(log, "(c) re-import measured_new v1 (current max), "
                   "different content -> duplicate_version",
                   "duplicate_version", store.import_dataset, p, new_cit,
                   KNOWN)
    # (d) duplicate (id, version), identical content
    expect_refusal(log, "(d) re-import measured_new v1 (current max), "
                   "identical content -> duplicate_version (no idempotent "
                   "second row)", "duplicate_version", store.import_dataset,
                   payload_a(1, id="measured_new"), new_cit, KNOWN)
    ok = store.get("measured_new", 1).content_sha256 == new_sha_before
    log.row(ok, "post-state: stored measured_new v1 unchanged after c-d",
            f"sha256={store.get('measured_new', 1).content_sha256[:16]}...")
    # (e) version 0
    expect_refusal(log, "(e) version 0 -> bad_version", "bad_version",
                   store.import_dataset, payload_a(0), CIT_A, KNOWN)
    # (f) listing exposes history order for the datasets in the store
    listing = store.listing()
    ok = (listing.get("measured_A") == [1, 2]
          and listing.get("measured_new") == [1]
          and sorted(listing) == sorted(listing.keys())
          and all(v == sorted(v) for v in listing.values()))
    log.row(ok, "(f) listing exposes (id, versions...) with history order",
            f"listing={listing}")
    return log


def main():
    results = [run_r1().finish(CHECKS / "r1_positive_imports.txt"),
               run_r2().finish(CHECKS / "r2_missing_context_negatives.txt"),
               run_r3().finish(CHECKS / "r3_falsifier_membership.txt"),
               run_r4().finish(CHECKS / "r4_versioning_immutability.txt")]
    if not all(results):
        print("CONTROL FAILURE: a preregistered threshold missed -- "
              "see checks/*.txt (fired runs retained)")
        return 1
    print("R1-R4 all thresholds reached; check files written to checks/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
