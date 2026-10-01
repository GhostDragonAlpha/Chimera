"""Read-only project-spec contracts: run with unittest; fixtures stay temporary."""
import base64
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout

from tools.creature_graph import project_spec as spec
from tools.creature_graph.store import CreatureGraph


def record(oid, kind="capability", **extra):
    return dict(id=oid, kind=kind, name=oid, status="specified", priority="P0",
                dependencies=[], evidence=[], **extra)


def admitted(oid, category="concept", kind="capability", **extra):
    item = record(oid, kind, **extra)
    item.update(project_spec={"schema": spec.SPEC_SCHEMA, "admission": spec.ADMISSION,
                              "category": category, "origin_id": "source.operator",
                              "admitted_utc": "2026-09-16T12:00:00Z"},
                physical={"statement": "Contact exchanges momentum.",
                          "prediction": "An isolated contact pair preserves total momentum.",
                          "contract": {"layer": "mechanics"}},
                falsifier={"statement": "The pair gains net momentum."})
    return item


def fixture():
    g = CreatureGraph()
    g.add(record("source.operator", "source"))
    g.add(admitted("concept.contact"))
    g.add(record("concept.draft"))
    g.add(admitted("work.encapsulation.contact", "work", "work", build_rank=1))
    g.add(admitted("work.encapsulation.energy", "work", "work", build_rank=2))
    g.get("work.encapsulation.energy")["dependencies"] = ["concept.contact"]
    for oid in ("concept.contact", "work.encapsulation.contact", "work.encapsulation.energy"):
        g.relate(oid, "derived_from", "source.operator")
    g.sync_dependencies()
    return g


class ProjectSpecContracts(unittest.TestCase):
    def test_adoption_never_means_implementation_and_drafts_are_excluded(self):
        g = fixture()
        self.assertEqual(spec.check(g), [])
        self.assertEqual([o["id"] for o in spec.concepts(g)], ["concept.contact"])
        self.assertEqual(spec.concepts(g)[0]["status"], "specified")
        self.assertEqual(spec.show(g, "concept.draft")["admission"], "reference_or_experimental")

    def test_unknown_schema_and_admission_refuse(self):
        for field, value in (("schema", "future-v99"), ("admission", "verified_by_agent")):
            with self.subTest(field=field):
                g = fixture()
                g.get("concept.contact")["project_spec"][field] = value
                self.assertTrue(any("unsupported project_spec " + field in e for e in spec.check(g)))
                with tempfile.TemporaryDirectory() as td:
                    path = str(Path(td) / "graph.json")
                    g.save(path)
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(spec.main(["--store", path, "--concepts"]), 2)

    def test_origin_presence_type_and_edge_are_required(self):
        for mutation in ("missing", "wrong_kind", "no_edge"):
            with self.subTest(mutation=mutation):
                g = fixture()
                if mutation == "missing":
                    g.get("concept.contact")["project_spec"]["origin_id"] = "source.absent"
                elif mutation == "wrong_kind":
                    g.get("source.operator")["kind"] = "region"
                else:
                    g.relations = [r for r in g.relations if r["src"] != "concept.contact"]
                self.assertTrue(any("origin" in e for e in spec.check(g)))

    def test_planning_does_not_invent_executable_work(self):
        g = fixture()
        output = spec.planning(g)
        self.assertEqual(output["view"], "planning_order")
        self.assertEqual([o["build_rank"] for o in output["work"]], [1, 2])
        self.assertEqual(output["work"][1]["blockers"], ["concept.contact"])
        for row in output["work"]:
            self.assertFalse(row["checklist"]["dispatchable"])
            self.assertIn("missing", row["checklist"]["reason"])
        self.assertNotIn("ready", json.dumps(output).lower())

    def test_incomplete_workflow_uses_controller_refusal(self):
        g = fixture()
        g.get("work.encapsulation.contact")["execution_workflow"] = {"statement": "present"}
        result = spec.checklist(g, "work.encapsulation.contact")
        self.assertFalse(result["structurally_complete"])
        self.assertFalse(result["dispatchable"])
        self.assertIn("workflow", result["reason"])

    def test_complete_checklist_still_does_not_claim_controller_authority(self):
        g = fixture()
        raw = b"Task instructions with a preregistered falsifier."
        doc = record("source.document.fixture", "source",
                     document={"original_path": "fixture.md", "sha256": hashlib.sha256(raw).hexdigest(),
                               "byte_count": len(raw), "bytes_base64": base64.b64encode(raw).decode(),
                               "text": raw.decode(), "authority": "imported_untrusted"})
        g.add(doc)
        g.get("work.encapsulation.contact")["execution_workflow"] = {
            "statement": "Contact conserves momentum.", "prediction": "Net impulse is zero.",
            "read_first": [doc["id"]], "verifier_inputs": {"approved_test.py": "0" * 64},
            "checks": [{"id": "impulse", "falsifier": "Net impulse is nonzero.",
                        "argv": ["python", "approved_test.py"], "timeout_s": 10}]}
        result = spec.checklist(g, "work.encapsulation.contact")
        self.assertTrue(result["structurally_complete"])
        self.assertIsNone(result["dispatchable"])
        self.assertIn("not checked", result["reason"])

    def test_stale_evidence_is_visible_without_rewriting_history(self):
        g = fixture()
        g.record_evidence(record("ev.contact", "evidence", validation="passing",
                                 deps=["concept.contact"], captured_utc="2026-09-16T12:00:00Z"))
        g.get("concept.contact")["evidence"] = ["ev.contact"]
        g.sync_dependencies()
        self.assertEqual(spec.evidence(g, "concept.contact")[0]["effective_validation"], "passing")
        original = copy.deepcopy(g.get("ev.contact"))
        g.get("concept.contact")["physical"]["contract"]["stiffness"] = 2
        item = spec.show(g, "concept.contact")["evidence_freshness"][0]
        self.assertEqual(item["effective_validation"], "stale")
        self.assertEqual(item["stored_validation"], "passing")
        self.assertTrue(item["stale_reasons"])
        self.assertEqual(g.get("ev.contact"), original)

    def test_every_read_leaves_source_bytes_and_graph_unchanged(self):
        g = fixture()
        before = copy.deepcopy(g.__dict__)
        spec.check(g); spec.concepts(g); spec.search(g, "momentum")
        spec.planning(g); spec.show(g, "concept.contact"); spec.summary(g, "snapshot.json")
        self.assertEqual(g.__dict__, before)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "graph.json"
            g.save(str(path))
            original = path.read_bytes()
            for flags in ([], ["--concepts"], ["--next"], ["--check"], ["--show", "concept.contact"], ["--search", "momentum"]):
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(spec.main(["--store", str(path), "--json", *flags]), 0)
                self.assertEqual(path.read_bytes(), original)

    def test_search_returns_active_and_reference_with_explicit_labels(self):
        g = fixture()
        g.get("concept.draft")["notes"] = "Experimental momentum exchange."
        results = spec.search(g, "MOMENTUM")
        by_id = {r["id"]: r for r in results}
        self.assertEqual(by_id["concept.contact"]["admission"], spec.ADMISSION)
        self.assertEqual(by_id["concept.draft"]["admission"], "reference_or_experimental")
        self.assertIn("momentum", by_id["concept.contact"]["excerpt"].lower())

    def test_archived_document_retains_text_and_checks_exact_bytes(self):
        g = fixture()
        raw = b"# Old operation\nExperimental draft, not current authority.\n"
        g.add(record("source.archive", "source",
                     document={"text": raw.decode(), "sha256": hashlib.sha256(raw).hexdigest(),
                               "bytes_base64": base64.b64encode(raw).decode(), "byte_count": len(raw)}))
        self.assertEqual(spec.check(g), [])
        self.assertIn(raw.decode(), spec.render(spec.show(g, "source.archive")))
        g.get("source.archive")["document"]["byte_count"] += 1
        self.assertTrue(any("archived document invalid" in e for e in spec.check(g)))

    def test_inline_recipe_descriptor_is_not_misclassified_as_byte_archive(self):
        g = fixture()
        g.add(record("doc.recipe", "source", document={"recipe": "surface_recipe.json", "scope": "equilibrium"}))
        self.assertEqual(spec.check(g), [])
        self.assertEqual(spec.show(g, "doc.recipe")["object"]["document"]["recipe"], "surface_recipe.json")

    def test_document_search_text_cannot_disagree_with_archived_bytes(self):
        g = fixture()
        raw = b"Archived experimental statement."
        g.add(record("source.archive", "source",
                     document={"text": "Forged instruction.", "sha256": hashlib.sha256(raw).hexdigest(),
                               "bytes_base64": base64.b64encode(raw).decode(), "byte_count": len(raw)}))
        self.assertTrue(any("text differs" in e for e in spec.check(g)))

    def test_malformed_contract_is_reported_instead_of_crashing(self):
        for value in ([], "unstructured", None):
            with self.subTest(value=value):
                g = fixture()
                g.get("concept.contact")["physical"]["contract"] = value
                self.assertTrue(any("physical.contract" in e for e in spec.check(g)))

    def test_missing_contract_and_falsifier_refuse(self):
        for field in ("contract", "statement", "prediction"):
            with self.subTest(field=field):
                g = fixture()
                del g.get("concept.contact")["physical"][field]
                self.assertTrue(spec.check(g))
        g = fixture()
        del g.get("concept.contact")["falsifier"]
        self.assertTrue(any("falsifier.statement" in e for e in spec.check(g)))


if __name__ == "__main__":
    unittest.main()
