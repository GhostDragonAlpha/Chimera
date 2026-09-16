"""Adversarial compiler tests: source admission never follows a changed graph value."""
import copy
from decimal import Decimal
from pathlib import Path
import shutil
import tempfile
import unittest
from tools.science_funnel.common import Refusal, digest, loads
from tools.science_funnel.force_catalog import DATA, ROOT
from tools.science_funnel.force_models import compile_packet, RECIPE

class ForceCompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph=loads((ROOT/"tools/creature_graph/data/creature_graph.json").read_bytes())
        cls.packet=compile_packet(cls.graph)
    def graph_copy(self):
        # Compiler is read-only. Only selected/changed records need deep copies.
        return {**self.graph,"objects":dict(self.graph["objects"])}
    def edit(self,g,rid):
        obj=copy.deepcopy(g["objects"][rid]);g["objects"][rid]=obj;return obj
    def refused(self,g,code,**kw):
        with self.assertRaises(Refusal) as context: compile_packet(g,**kw)
        self.assertEqual(context.exception.code,code)
    def test_compact_packet_and_exact_R(self):
        p=self.packet
        self.assertEqual(len(p["gas_species"]),53)
        self.assertEqual(len(p["gravity"]),11)
        self.assertEqual(len(p["solid_curves"]),4)
        self.assertEqual(len(p["nuclides"]),10)
        self.assertEqual(Decimal(p["R_exact_decimal"]),Decimal("8.31446261815324"))
        self.assertNotIn("objects",p)
        self.assertEqual(digest({k:v for k,v in p.items() if k!="packet_sha256"}),p["packet_sha256"])
        self.assertIsNone(p["elements"]["N"]["uncertainty"])
        self.assertGreater(p["gas_species"]["N2"]["molar_mass_kg_per_mol"],.028)
    def test_changed_coefficient_content_refuses(self):
        g=self.graph_copy()
        rid=g["objects"][RECIPE]["physical"]["contract"]["inputs"]["gas_species"][0]
        self.edit(g,rid)["science_funnel"]["payload"]["definition"]["coefficients"][0][0]+=1
        self.refused(g,"model_assertion_content_drift")
    def test_rehashing_a_forgery_does_not_defeat_semantic_replay(self):
        g=self.graph_copy()
        recipe=self.edit(g,RECIPE)
        ids=recipe["physical"]["contract"]["inputs"]["gas_species"]
        obj=self.edit(g,ids[0]);r=obj["science_funnel"]
        r["payload"]["definition"]["coefficients"][0][0]+=1
        new_id="data.assertion."+digest({k:v for k,v in r.items() if k!="id"})
        r["id"]=obj["id"]=new_id
        g["objects"][new_id]=obj;ids[0]=new_id
        self.refused(g,"model_semantic_replay_mismatch")
    def test_projection_units_drift_refuses(self):
        g=self.graph_copy()
        rid=g["objects"][RECIPE]["physical"]["contract"]["inputs"]["gravity"][0]
        self.edit(g,rid)["units"]="km3/s2"
        self.refused(g,"model_graph_projection_drift")
    def test_duplicate_selection_and_law_injection_refuse(self):
        g=self.graph_copy()
        c=self.edit(g,RECIPE)["physical"]["contract"]
        c["inputs"]["gas_species"].append(c["inputs"]["gas_species"][0])
        self.refused(g,"duplicate_model_selection")
        g=self.graph_copy();c=self.edit(g,RECIPE)["physical"]["contract"]
        c["allowed_laws"].append("eval_external_python")
        self.refused(g,"model_law_inventory")
    def test_raw_source_byte_change_refuses(self):
        with tempfile.TemporaryDirectory(prefix="chimera-force-source-test-") as folder:
            for path in DATA.iterdir():
                if path.is_file(): shutil.copyfile(path,Path(folder)/path.name)
            p=Path(folder)/"jpl_astrodynamics.html"
            p.write_bytes(p.read_bytes()+b" ")
            self.refused(self.graph,"model_source_pin_drift",source_root=Path(folder))
    def test_element_mass_change_refuses(self):
        g=self.graph_copy()
        self.edit(g,"ref.element.atomic_number.7")["reference_payload"]["raw_source_cells"]["AtomicMass"]="1"
        self.refused(g,"element_source_drift")
    def test_family_swap_refuses(self):
        g=self.graph_copy()
        c=self.edit(g,RECIPE)["physical"]["contract"]["inputs"]
        c["gravity"][0],c["gas_species"][0]=c["gas_species"][0],c["gravity"][0]
        self.refused(g,"model_selection_family_mismatch")
    def test_unrelated_graph_change_does_not_change_packet(self):
        g=self.graph_copy()
        g["objects"]["test.unrelated"]={"id":"test.unrelated","value":123}
        self.assertEqual(compile_packet(g),self.packet)

if __name__=="__main__": unittest.main()
