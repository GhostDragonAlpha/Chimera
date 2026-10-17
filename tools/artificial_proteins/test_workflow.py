import copy
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from .core import (Refusal,recipe,validate_recipe,detailed,digest,table_from_samples,
                   Response,equilibrium,validate_table)
from .verify import analytic,verify_samples
from .runner import run,check,read,write

class PhysicsTests(unittest.TestCase):
    def table(self):
        r=recipe(0);x=np.linspace(-.4,.4,65);v=[detailed(r,float(h)) for h in x]
        return table_from_samples(x,[t['reaction'] for t in v],v[0]['energy'],recipe_hash=digest(r))
    def test_geometric_reference_against_independent_area_formula(self):
        for seed in range(3):
            for scale in [.5,1.,2.]:
                for h in [-.31,.0,.27]:
                    v=detailed(recipe(seed),h*scale,scale);a=analytic(recipe(seed),h*scale,scale)
                    self.assertAlmostEqual(v['energy'],a['energy'],places=11)
                    self.assertAlmostEqual(v['reaction'],a['reaction'],places=11)
    def test_energy_gradient_reaction_and_force_moment_balance(self):
        r=recipe(2);h=.217;eps=1e-6;v=detailed(r,h)
        fd=(detailed(r,h+eps)['energy']-detailed(r,h-eps)['energy'])/(2*eps)
        self.assertLess(abs(fd-v['reaction']),1e-8)
        force=np.array(v['forces']);pos=np.array(v['positions'])
        self.assertLess(np.max(np.abs(force.sum(axis=0))),1e-12)
        self.assertLess(np.max(np.abs(np.cross(pos,force).sum(axis=0))),1e-12)
    def test_invalid_recipe_and_missing_physics(self):
        for field,value in [('units',{'length':'cm'}),('law','muscle'),('domain',[-1,1]),('ports',{})]:
            r=recipe();r[field]=value
            with self.assertRaises(Refusal):validate_recipe(r)
        r=recipe();r['rim_xy'][1]=r['rim_xy'][0]
        with self.assertRaises(Refusal):validate_recipe(r)
    def test_no_extrapolation_or_nonfinite_input(self):
        fn=Response(self.table())
        for h in [.401,float('nan'),float('inf')]:
            with self.assertRaises(Refusal):fn(h)
        with self.assertRaises(Refusal):detailed(recipe(),0.,scale=3.)
    def test_table_energy_derivative_and_copy_isolation(self):
        a=self.table();fn=Response(a);a['reaction'][3]=999
        h=.213;eps=1e-6
        fd=(fn(h+eps)['energy']-fn(h-eps)['energy'])/(2*eps)
        self.assertLess(abs(fd-fn(h)['reaction']),1e-8)
    def test_stale_and_corrupt_artifacts_refused(self):
        a=self.table();a['energy'][5]+=1
        with self.assertRaises(Refusal):Response(a)
        a=self.table();a['source_hashes']={};a['sha256']=digest({k:v for k,v in a.items() if k!='sha256'})
        with self.assertRaises(Refusal):Response(a)
    def test_energy_inconsistency_refused_even_with_recomputed_hash(self):
        a=self.table();a['energy'][5]+=1;a['sha256']=digest({k:v for k,v in a.items() if k!='sha256'})
        with self.assertRaises(Refusal):Response(a)
    def test_excessive_load_refused_and_inputs_unchanged(self):
        a=self.table();before=copy.deepcopy(a);fn=Response(a)
        with self.assertRaises(Refusal):equilibrium([(fn,0.)],100.,(-.4,.4))
        self.assertEqual(a,before)
    def test_zero_gamma_and_scale_law(self):
        r=recipe();base=detailed(r,.2)
        self.assertEqual(detailed(r,.2,gamma=0.)['energy'],0.)
        other=detailed(r,.4,scale=2.)
        self.assertAlmostEqual(other['energy'],4*base['energy'])
        self.assertAlmostEqual(other['reaction'],2*base['reaction'])
    def test_negative_similarity_control(self):
        r=recipe();c={'recipe':r,'h':.4,'scale':2.,'gamma':1.}
        # Reusing an unscaled force/energy must be caught.
        with self.assertRaises(Refusal):verify_samples([c],[detailed(r,.2)],'table')
    def test_complete_workflow_and_recheck_and_resume(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'run';result=run(out)
            self.assertEqual(result['status'],'PASS');self.assertEqual(check(out)['status'],'PASS')
            reuse=result['assembly']['recursive_reuse']
            self.assertEqual(reuse[0]['frozen_composite'],reuse[1]['frozen_composite'])
            self.assertEqual(run(out,resume=True)['status'],'PASS')
            identity=read(out/'identity.json');identity['source_hashes']={};write(out/'identity.json',identity)
            with self.assertRaises(Refusal):run(out,resume=True)
    def test_forged_pass_missing_and_corrupt_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'run';run(out)
            receipt=read(out/'receipt.json');receipt['artifacts']={};write(out/'receipt.json',receipt)
            with self.assertRaises(Refusal):check(out)
    def test_gpu_without_reservation_refused_and_failure_retained(self):
        import os
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {}, clear=True):
            out=Path(d)/'run'
            with self.assertRaisesRegex(Refusal,'managed_gpu_reservation_required'):
                run(out,Path('nonexistent.exe'))
            self.assertEqual(read(out/'failure.json')['status'],'FAIL')
    def test_numerical_forgery_fails_even_when_hashes_rewritten(self):
        from .core import file_hash
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'run';run(out)
            measurements=read(out/'measurements.json');measurements[0]['reaction']+=.1
            write(out/'measurements.json',measurements)
            receipt=read(out/'receipt.json');receipt['artifacts']['measurements.json']=file_hash(out/'measurements.json')
            write(out/'receipt.json',receipt)
            with self.assertRaisesRegex(Refusal,'reference_mismatch'):check(out)
    def test_composite_scaling_requires_separate_qualification(self):
        a=self.table();a['lineage']=[{'artifact':'child'}];a['sha256']=digest({k:v for k,v in a.items() if k!='sha256'})
        with self.assertRaisesRegex(Refusal,'composite_scaling_unqualified'):Response(a)(.1,scale=2.)
    def test_nonmonotone_samples_refused(self):
        with self.assertRaises(Refusal):table_from_samples([0,1,2],[0,2,1],0.,recipe_hash='x')

if __name__=='__main__':unittest.main()
