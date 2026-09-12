import unittest
import numpy as np
from .geometry import build_rest_geometry
from .units_contract import contract, evaluate_physical, UnitsRefusal

class UnitsContractTests(unittest.TestCase):
    def setUp(self):
        self.rest=build_rest_geometry(np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]]),np.array([[0,1,2]]))
        self.cur=np.array([[0.,0.,0.],[1.2,0.,0.],[0.,.8,0.]])
        self.p={"kind":"synthetic","source":"test-explicit-nonunit"}
    def test_physical_evaluator_scales_components_and_volume(self):
        a=evaluate_physical(self.rest,self.cur,1000.,.002,.3,provenance=self.p)
        b=evaluate_physical(self.rest,self.cur,1000.,.004,.3,provenance=self.p)
        np.testing.assert_allclose(b.vertex_forces,2*a.vertex_forces)
        np.testing.assert_allclose(b.per_face.w_vol,a.per_face.w_vol)
    def test_provenance_and_overflow_refuse(self):
        with self.assertRaisesRegex(UnitsRefusal,"structured_provenance_required"):
            evaluate_physical(self.rest,self.cur,1000.,.002,.3,provenance="invented")
        with self.assertRaisesRegex(UnitsRefusal,"surface_modulus_overflow"):
            contract(1e308,1e308,.3)
        with self.assertRaisesRegex(UnitsRefusal,"numeric_material_required"):
            contract("1000",.002,.3)

if __name__ == "__main__": unittest.main()
