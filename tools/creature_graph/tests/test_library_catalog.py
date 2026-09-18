"""Falsifiers for the generated catalog (work.data.library_catalog_20260918).

The catalog's falsifier, as admitted under RULE 0 BEFORE the generator
existed:
  * regeneration from an unchanged store must reproduce the document
    byte-identically;
  * any graph mutation that does NOT change a count (or quoted fact) the
    catalog reports is a bug in the catalog -- flipping one admitted
    record's identity-bearing field must change the catalog bytes;
  * every count in the document must equal a recount taken directly from
    the store (the doc cites only facts present in the graph).

Test rules follow tools/creature_graph/tests/harness.py: TEST-ONLY, nothing
here ever writes inside tools/creature_graph/data/ (the canonical store path
STORE_PATH is never used for saving; every mutation happens on a copy in a
per-test temp directory).

Run (from the checkout root):
    python -B -m unittest tools.creature_graph.tests.test_library_catalog -v
"""
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
GRAPH_DIR = os.path.dirname(HERE)                      # tools/creature_graph
ROOT = os.path.dirname(os.path.dirname(GRAPH_DIR))     # checkout root
CANONICAL_STORE = os.path.join(GRAPH_DIR, "data", "creature_graph.json")

if GRAPH_DIR not in sys.path:
    sys.path.insert(0, GRAPH_DIR)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import library_catalog as lc  # noqa: E402
from store import CreatureGraph  # noqa: E402


def _write_store(g: CreatureGraph, path: str) -> str:
    return g.save(path)


def _copy_store(dst_dir: str) -> str:
    """Copy the canonical store (core + bulk shards) into dst_dir."""
    os.makedirs(dst_dir, exist_ok=True)
    with open(CANONICAL_STORE, encoding="utf-8") as f:
        payload = json.load(f)
    shards = (payload.get("meta", {}) or {}).get("bulk_shards", [])
    for name in shards:
        shutil.copy2(os.path.join(os.path.dirname(CANONICAL_STORE), name),
                     os.path.join(dst_dir, name))
    dst = os.path.join(dst_dir, os.path.basename(CANONICAL_STORE))
    shutil.copy2(CANONICAL_STORE, dst)
    return dst


def _make_source(g: CreatureGraph, source_id: str, manifest_source: str,
                 license_text: str, quarantine=None, count_identity=None):
    """Add one admitted source object carrying the batch-membrane fields."""
    receipt = {"accepted": 2, "quarantined": len(quarantine or [])}
    if count_identity:
        receipt["count_identity"] = {"law": count_identity, "closed": True}
    g.add({"id": source_id, "kind": "source", "name": manifest_source,
           "status": "extracted",
           "science_funnel": {
               "schema_version": "1.0.0", "authority": "external_assertion",
               "runtime_ready": False, "bundle_id": source_id.split(".")[-1],
               "storage": "chimera-intake:" + source_id.split(".")[-1],
               "manifest": {"adapter": "fixture_adapter", "schema_version": "1.0.0",
                            "source": {"id": manifest_source,
                                       "release": "fixture release",
                                       "url": "https://fixture.example/db",
                                       "license": license_text,
                                       "known_gaps": ["fixture gap one"]}},
               "receipt": receipt,
               "quarantine": list(quarantine or []),
           }})


def _make_record(g: CreatureGraph, rid: str, source_id: str, label: str,
                 contract=None):
    obj = {"id": rid, "kind": "reference_entity", "name": label,
           "status": "extracted",
           "provenance": {"source_id": source_id, "external_id": label,
                          "source_version": "fixture"},
           "science_funnel": {"adapter": "fixture_adapter", "record_type": "entity",
                              "external_id": label, "label": label,
                              "authority": "external_assertion",
                              "runtime_ready": False, "schema_version": "1.0.0",
                              "payload": {"label": label},
                              "producer_hash": "0" * 64, "unknowns": []},
           "unknowns": [], "spatial": None, "geometry": None,
           "physical": None, "notes": "fixture"}
    if contract:
        obj["class_contract"] = contract
    g.add(obj)
    g.relate(rid, "derived_from", source_id, note="fixture")


def _fixture_graph(label_a: str = "fixture record A",
                   quarantine_code: str = "fixture_refusal") -> CreatureGraph:
    g = CreatureGraph()
    src = "data.source." + "f" * 64
    _make_source(g, src, "fixture.database", "CC0 1.0 (fixture manifest license)",
                 quarantine=[{"artifact": "fixture.csv", "location": "row:1",
                              "sha256": "a" * 64,
                              "refusal": {"code": quarantine_code,
                                          "detail": "row 1"}}],
                 count_identity="fetched == admitted + quarantined + conflicts, zero silent drops")
    _make_record(g, "data.assertion." + "1" * 64, src, label_a,
                 contract={"class_id": "batch.entity.external", "version": 1})
    _make_record(g, "data.assertion." + "2" * 64, src, "fixture record B",
                 contract={"class_id": "batch.entity.external", "version": 1})
    return g


class _TmpPaths:
    """Per-test temp dirs; the canonical data dir is never written."""

    def __init__(self):
        self.base = tempfile.mkdtemp(prefix="library_catalog_tests_")

    def child(self, name: str) -> str:
        return os.path.join(self.base, name)


class LibraryCatalogFalsifiers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = _TmpPaths()
        cls.live_copy = _copy_store(cls.tmp.child("live"))
        g = CreatureGraph.load(cls.live_copy)
        cls.live_doc = lc.build_catalog(g).encode("utf-8")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp.base, ignore_errors=True)

    # ------------------------------------------------------------- T1 ----
    def test_byte_identity(self):
        """FALSIFIER: regenerating from an unchanged store must reproduce
        the document bytes."""
        g2 = CreatureGraph.load(self.live_copy)
        again = lc.build_catalog(g2).encode("utf-8")
        self.assertEqual(self.live_doc, again,
                         "regeneration from an unchanged store changed bytes")

    # ------------------------------------------------------------- T2 ----
    def test_mutation_changes_bytes(self):
        """FALSIFIER: any graph mutation that does NOT change the catalog
        bytes is a bug in the catalog. Flip one counted field of one
        admitted record; the catalog must change AND the targeted count
        must move."""
        baseline = self.live_doc

        # (a) flip one record's name on one bulk-shard source
        g = CreatureGraph.load(self.live_copy)
        victim_src = next(s["id"] for s in sorted(
            (o for o in g.objects.values()
             if o["kind"] == "source" and isinstance(o.get("science_funnel"), dict)),
            key=lambda o: o["id"])
            if sum(1 for o in g.objects.values()
                   if (o.get("provenance") or {}).get("source_id") == s["id"]) > 100)
        victim = next(o for o in g.objects.values()
                      if (o.get("provenance") or {}).get("source_id") == victim_src)
        before_digest = None
        old_name = victim["name"]
        victim["name"] = old_name + " CORRUPTED"
        mutated_doc = lc.build_catalog(g).encode("utf-8")
        self.assertNotEqual(baseline, mutated_doc,
                            "flipping one admitted record's name did not "
                            "change the catalog bytes")
        # the targeted count (record-set digest line of that source) moved
        def digest_of(doc: bytes, src: str) -> str:
            m = re.search(re.escape(src) + r".*?record-set digest: `([0-9a-f]{16})`",
                          doc.decode("utf-8"), re.S)
            return m.group(1)
        self.assertNotEqual(digest_of(baseline, victim_src),
                            digest_of(mutated_doc, victim_src))

        # (b) flip one quarantine refusal code on one source
        g = CreatureGraph.load(self.live_copy)
        q_src = next(o for o in g.objects.values()
                     if o["kind"] == "source" and isinstance(o.get("science_funnel"), dict)
                     and (o["science_funnel"].get("quarantine")))
        q_src["science_funnel"]["quarantine"][0]["refusal"]["code"] = \
            str(q_src["science_funnel"]["quarantine"][0]["refusal"]["code"]) + "_flipped"
        self.assertNotEqual(baseline, lc.build_catalog(g).encode("utf-8"),
                            "flipping one quarantine refusal code did not "
                            "change the catalog bytes")

        # (c) flip the license text on one source
        g = CreatureGraph.load(self.live_copy)
        l_src = next(o for o in g.objects.values()
                     if o["kind"] == "source" and isinstance(o.get("science_funnel"), dict)
                     and ((o["science_funnel"].get("manifest") or {}).get("source") or {}).get("license"))
        l_src["science_funnel"]["manifest"]["source"]["license"] = \
            "MUTATED LICENSE TEXT"
        mutated = lc.build_catalog(g).encode("utf-8")
        self.assertNotEqual(baseline, mutated,
                            "flipping one license line did not change the "
                            "catalog bytes")
        self.assertIn("MUTATED LICENSE TEXT", mutated.decode("utf-8"))

    def test_fixture_mutation_changes_fixture_catalog(self):
        """Same falsifier on a fully controlled fixture graph: the count of
        records must move when a record is removed, and the refusal count
        must move when a quarantine entry is added."""
        base = lc.build_catalog(_fixture_graph()).encode("utf-8")
        self.assertIn("| records |", base.decode("utf-8"))

        # remove one record -> the source's record count changes
        g = _fixture_graph()
        g.objects.pop("data.assertion." + "2" * 64)
        g.relations = [r for r in g.relations if r["src"] != "data.assertion." + "2" * 64]
        self.assertNotEqual(base, lc.build_catalog(g).encode("utf-8"))

        # add one quarantine entry -> the quarantined count changes
        g = _fixture_graph()
        src_id = next(o["id"] for o in g.objects.values() if o["kind"] == "source")
        g.objects[src_id]["science_funnel"]["quarantine"].append(
            {"artifact": "fixture.csv", "location": "row:2", "sha256": "b" * 64,
             "refusal": {"code": "fixture_refusal", "detail": "row 2"}})
        mutated = lc.build_catalog(g).encode("utf-8")
        self.assertNotEqual(base, mutated)
        self.assertIn("quarantined at admission: 2", mutated.decode("utf-8"))

    # ------------------------------------------------------------- T3 ----
    def test_counts_match_store_recount(self):
        """FALSIFIER: every count in the document must equal a recount
        taken directly from the store (the catalog cites only facts
        present in the graph)."""
        g = CreatureGraph.load(self.live_copy)
        doc = self.live_doc.decode("utf-8")

        # store totals
        total_objects = len(g.objects)
        total_relations = len(g.relations)
        sources = sorted((o for o in g.objects.values()
                          if o["kind"] == "source" and isinstance(o.get("science_funnel"), dict)),
                         key=lambda o: o["id"])
        records_by_source = {s["id"]: [] for s in sources}
        for o in g.objects.values():
            src = (o.get("provenance") or {}).get("source_id")
            if src in records_by_source and o.get("science_funnel") is not None:
                records_by_source[src].append(o)

        self.assertIn(f"- store objects: {total_objects}", doc)
        self.assertIn(f"- store relations: {total_relations}", doc)
        self.assertIn(f"- admitted sources (kind=source with an intake "
                      f"bundle): {len(sources)}", doc)
        self.assertIn(f"- admitted records (objects citing an admitted "
                      f"source): {sum(len(v) for v in records_by_source.values())}",
                      doc)

        # per-source rows: every bundle id appears with its own recount
        rows = re.findall(r"^\| ([^|]+) \| `(data\.source\.[0-9a-f]{64})` \| (\d+) \|",
                          doc, re.M)
        self.assertEqual(len(rows), len(sources),
                         "summary table row count != source count")
        for _, bundle, n in rows:
            self.assertEqual(int(n), len(records_by_source[bundle]),
                             f"summary row count mismatch for {bundle}")

        # per-source sections: quarantine counts and kind counts recount
        for s in sources:
            sfn = s.get("science_funnel") or {}
            section = doc.split(f"### {s['id']}", 1)[1]
            section = section.split("\n### ", 1)[0]
            self.assertIn(f"- quarantined at admission: "
                          f"{len(sfn.get('quarantine') or [])}", section,
                          f"quarantine count mismatch for {s['id']}")
            kinds = {}
            for r in records_by_source[s["id"]]:
                kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
            for kind, n in kinds.items():
                self.assertIn(f"  - kind {kind}: {n}", section,
                              f"kind count mismatch for {s['id']} / {kind}")
            self.assertIn(f"- records: {len(records_by_source[s['id']])} total",
                          section, f"record count mismatch for {s['id']}")

        # standing gaps: the exact gap strings from the owning record
        owner = g.objects.get(lc.GAPS_OWNER) or {}
        hunt = (owner.get("observation") or {}).get(lc.GAPS_KEY) or {}
        for gap in hunt.get(lc.GAPS_FIELD) or []:
            self.assertIn(f"- \"{gap}\"", doc,
                          f"gap text not quoted verbatim: {gap}")

        # receipt citations: every cited path appears with its citing record
        for cite in lc.collect(g)["receipt_citations"]:
            self.assertIn(f"- `{cite['path']}` -- cited by graph record "
                          f"`{cite['object']}`", doc)

        # every data.source id printed in the doc exists in the store
        for m in set(re.findall(r"data\.source\.[0-9a-f]{64}", doc)):
            self.assertIn(m, g.objects, f"document cites unknown source {m}")

    def test_rebuild_matches_committed_document(self):
        """The committed docs/THE_LIBRARY.md is exactly what the generator
        produces from the canonical store -- regeneration is the contract."""
        committed_path = os.path.join(ROOT, "docs", "THE_LIBRARY.md")
        if not os.path.exists(committed_path):
            self.skipTest("docs/THE_LIBRARY.md not committed yet")
        with open(committed_path, "rb") as f:
            committed = f.read()
        g = CreatureGraph.load(_copy_store(self.tmp.child("rebuild")))
        self.assertEqual(lc.build_catalog(g).encode("utf-8"), committed,
                         "committed docs/THE_LIBRARY.md does not match a "
                         "fresh regeneration from the canonical store")

    def test_fixture_license_classification_is_graph_only(self):
        """The license class label is a documented bookkeeping derivation
        over the record's own quoted license text -- never an external
        lookup. The quoted text always appears verbatim in the section."""
        g = _fixture_graph(label_a="fixture record A")
        doc = lc.build_catalog(g)
        self.assertIn('> "CC0 1.0 (fixture manifest license)"', doc)


if __name__ == "__main__":
    unittest.main(verbosity=2)
