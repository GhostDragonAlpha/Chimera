import unittest
from tools.creature_graph.store import CreatureGraph, StoreRefusal


def obj(oid):
    return {"id": oid, "kind": "region", "name": oid,
            "status": "specified", "priority": "P0"}


def graph():
    g = CreatureGraph()
    g.add(obj("a"))
    g.add(obj("b"))
    return g


class StoreRelateGuard(unittest.TestCase):
    def test_honest_relate_unaffected(self):
        g = graph()
        e1 = g.relate("a", "inside", "b", "one")
        e2 = g.relate("a", "inside", "b", "one")
        self.assertNotEqual(e1["rid"], e2["rid"])
        self.assertEqual(len(g.relations), 2)

    def test_set_edge_refused_by_name(self):
        g = graph()
        g.relate("a", "inside", "b")
        g.relations.append({"rid", "src"})
        with self.assertRaises(StoreRefusal) as x:
            g.relate("a", "inside", "b", "after-corrupt")
        self.assertEqual(x.exception.code, "store_corrupt_relation_edge")
        self.assertIn("relations[1]", str(x.exception))
        self.assertIn("set", str(x.exception))

    def test_list_and_str_edges_refused(self):
        for bad in (["rid", "src"], "rid-string", {"rid": 123}, {"no_rid": 1}):
            with self.subTest(bad=repr(bad)[:40]):
                g = graph()
                g.relate("a", "inside", "b")
                g.relations.append(bad)
                with self.assertRaises(StoreRefusal) as x:
                    g.relate("a", "inside", "b")
                self.assertEqual(x.exception.code, "store_corrupt_relation_edge")

    def test_missing_endpoint_still_value_error(self):
        g = graph()
        with self.assertRaises(ValueError):
            g.relate("a", "inside", "missing")


if __name__ == "__main__":
    unittest.main()
