"""MAT2-M01 frozen-probe tests: P1-P4 positive predictions and F1-F3 falsifier bites.

CPU-only, stdlib-only, python -B, no engine, no network, no GPU. Fixture is the
committed teddy material-state document built from the pinned base revision
(see build_teddy_fixture.py). Run from the checkout root:
    python -B tools/monkey_campaign/contributions/MAT2-M01/test_material_state.py
"""
from __future__ import annotations

import copy
import json
import pathlib
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import material_state as ms  # noqa: E402

FIXTURE_PATH = HERE / 'teddy_fixture.json'
BASE = 'c525b82c7c3ce0128565424764293a3c85811ab3'
MEMBRANES_PATH = 'ChimeraEngine/native/teddy_membranes.json'

CHECKS = []


def check(name, ok, detail=''):
    CHECKS.append((name, bool(ok), detail))


def refused(code_substring, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except ValueError as exc:
        return code_substring in str(exc)
    return False


def refused_code(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except ValueError as exc:
        return str(exc)
    return None


class MaterialStateTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(FIXTURE_PATH.read_text(encoding='utf-8'))

    # ---------------- P1: schema validates, canonical round-trip, stable IDs
    def test_p1_schema_round_trip_and_ids(self):
        summary = ms.validate_material_state(self.doc)
        check('P1.region_count', summary['region_count'] == 30, str(summary['region_count']))
        check('P1.total_mass', summary['total_mass_kg'] == 2.0, str(summary['total_mass_kg']))
        reloaded = ms.decode(ms.canonical(self.doc))
        check('P1.canonical_round_trip', ms.canonical(reloaded) == ms.canonical(self.doc))
        import re
        id_re = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}')
        ids = summary['region_ids'] + [m['id'] for m in self.doc['matter']]
        ids += [b['id'] for b in self.doc['bonds']] + [c['id'] for c in self.doc['contacts']]
        check('P1.stable_id_shape', all(id_re.fullmatch(i) for i in ids), str(len(ids)))

    # ---------------- P2: single ownership, mass counted once
    def test_p2_single_ownership(self):
        summary = ms.validate_material_state(self.doc)
        check('P2.owner_count', summary['owner_count'] == summary['matter_count'] == 2,
              'owners=%d matter=%d' % (summary['owner_count'], summary['matter_count']))
        check('P2.references_present', summary['reference_count'] == 58,
              str(summary['reference_count']))
        check('P2.mass_once', ms.total_mass_once(self.doc) == 2.0)
        check('P2.mass_summary_once', ms.display(self.doc)['mass_summary']['total_mass_kg'] == 2.0)
        # second owner claim for the same matter id must be refused
        bad = copy.deepcopy(self.doc)
        bad['regions'][0]['matter_claims'] = [
            {'matter_id': 'fur_matter', 'role': 'owner'}]
        belly = next(r for r in bad['regions'] if r['id'] == 'belly')
        belly['matter_claims'].append({'matter_id': 'fur_matter', 'role': 'owner'})
        check('F1.double_owner_refused',
              refused('duplicate_matter_owner', ms.validate_material_state, bad))
        # reference claim does not change the total
        ref = copy.deepcopy(self.doc)
        head = next(r for r in ref['regions'] if r['id'] == 'head')
        head['matter_claims'].append({'matter_id': 'fur_matter', 'role': 'reference'})
        s2 = ms.validate_material_state(ref)
        check('P2.reference_keeps_total', s2['total_mass_kg'] == 2.0
              and s2['reference_count'] == 59)
        # unowned matter refused
        unowned = copy.deepcopy(self.doc)
        belly = next(r for r in unowned['regions'] if r['id'] == 'belly')
        belly['matter_claims'] = [c for c in belly['matter_claims'] if c['role'] != 'owner']
        check('F1.unowned_matter_refused',
              refused('unowned_matter', ms.validate_material_state, unowned))

    # ---------------- P3: distinct relation types, endpoints, display
    def test_p3_distinct_relations(self):
        d = ms.display(self.doc)
        rel = d['relations']
        check('P3.containment_listed', len(rel['containment']) == 1, str(rel['containment']))
        check('P3.bonds_listed', len(rel['bonds']) == 1, str(rel['bonds']))
        check('P3.contacts_listed', len(rel['contacts']) == 2)
        check('P3.relation_note', 'containment is not a bond' in rel['note'])
        # the containment edge and the bond are separate relation records
        bond_endpoint_regions = {e['region_id'] for b in rel['bonds']
                                 for e in b['endpoints']}
        containment_children = {e['child'] for e in rel['containment']}
        check('P3.containment_not_bond',
              rel['containment'][0]['child'] == 'ankle_left'
              and rel['bonds'][0]['id'] == 'bond_belly_chest_surface'
              and 'ankle_left' not in bond_endpoint_regions
              and len(rel['bonds']) == 1)
        # bond endpoints must name existing ports
        missing = copy.deepcopy(self.doc)
        missing['bonds'][0]['endpoints'][1]['port'] = 'no_such_port'
        check('P3.missing_port_refused',
              refused('missing_endpoint_port', ms.validate_material_state, missing))
        # a bond needs two explicit endpoints
        single = copy.deepcopy(self.doc)
        single['bonds'][0]['endpoints'] = [single['bonds'][0]['endpoints'][0]]
        check('F2.bond_requires_explicit_endpoints',
              refused('bond_requires_explicit_endpoints',
                      ms.validate_material_state, single))

    # ---------------- F2: removing the explicit bond removes the load path
    def test_f2_bond_removal_is_explicit(self):
        without = copy.deepcopy(self.doc)
        without['bonds'] = []
        s1 = ms.validate_material_state(self.doc)
        s2 = ms.validate_material_state(without)
        check('F2.bond_count_drops', s1['bond_count'] == 1 and s2['bond_count'] == 0)
        check('F2.regions_unchanged', s1['region_count'] == s2['region_count'] == 30)
        check('F2.mass_unchanged', s1['total_mass_kg'] == s2['total_mass_kg'] == 2.0)
        # containment survives bond removal (containment is not mechanical)
        check('F2.containment_survives',
              len(ms.display(without)['relations']['containment']) == 1)

    # ---------------- P4: fixture reuses the pinned prototype regions
    def test_p4_pinned_region_reuse(self):
        try:
            raw = subprocess.run(['git', 'show', '%s:%s' % (BASE, MEMBRANES_PATH)],
                                 capture_output=True, text=True, check=True,
                                 encoding='utf-8', cwd=str(HERE)).stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.skipTest('git unavailable or pinned blob not reachable')
        membranes = json.loads(raw)
        pinned = set(membranes['membranes'])
        fixture_regions = {r['id'] for r in self.doc['regions']}
        check('P4.regions_match_pinned', fixture_regions == pinned,
              'missing=%s extra=%s' % (sorted(pinned - fixture_regions)[:3],
                                       sorted(fixture_regions - pinned)[:3]))
        prov = self.doc['provenance']['source_blobs']
        import hashlib
        actual = hashlib.sha256(raw.encode('utf-8')).hexdigest()
        check('P4.blob_hash_recorded', prov[MEMBRANES_PATH] == actual, actual[:16])

    # ---------------- F3: identity drift vs declared rename
    def test_f3_region_identity_drift(self):
        rev2 = copy.deepcopy(self.doc)
        rev2['revision'] = 2
        rev2['regions'] = [r for r in rev2['regions'] if r['id'] != 'muzzle']
        # dropping a region that existed at revision 1 without a rename -> refused
        check('F3.drift_refused',
              refused('region_identity_drift', ms.check_revision_compatibility,
                      self.doc, rev2))
        # with a declared rename the same change is lawful
        rev2_renamed = copy.deepcopy(rev2)
        rev2_renamed['renames'] = {'muzzle': 'toes_left'}
        rev2_renamed['provenance'] = {'rename_reason': 'declared rename probe'}
        result = ms.check_revision_compatibility(self.doc, rev2_renamed)
        check('F3.rename_accepted', result['current_revision'] == 2
              and 'muzzle' in [r for r, _ in result['renames_applied']])
        # stable ids survive re-serialization identically
        d1 = ms.display(self.doc)['canonical_sha256']
        reloaded = ms.decode(ms.canonical(self.doc))
        d2 = ms.display(reloaded)['canonical_sha256']
        check('F3.digest_stable', d1 == d2, d1[:16])

    # ---------------- additional schema strictness probes
    def test_schema_strictness(self):
        bad_schema = copy.deepcopy(self.doc)
        bad_schema['schema'] = 'chimera.material_state.v0'
        check('S.wrong_schema_refused',
              refused('unsupported_material_state_schema', ms.validate_material_state,
                      bad_schema))
        bad_rev = copy.deepcopy(self.doc)
        bad_rev['revision'] = 0
        check('S.bad_revision_refused',
              refused('invalid_revision', ms.validate_material_state, bad_rev))
        nan_doc = copy.deepcopy(self.doc)
        nan_doc['matter'][0]['mass_kg'] = float('inf')
        check('S.nonfinite_mass_refused',
              refused('nonfinite_number', ms.validate_material_state, nan_doc))
        neg = copy.deepcopy(self.doc)
        neg['matter'][0]['mass_kg'] = -1.0
        check('S.negative_mass_refused',
              refused('negative_mass', ms.validate_material_state, neg))
        zero_dir = copy.deepcopy(self.doc)
        zero_dir['directions'][0]['axis'] = [0.0, 0.0, 0.0]
        check('S.zero_direction_refused',
              refused('zero_material_direction', ms.validate_material_state, zero_dir))
        unknown_law_region = copy.deepcopy(self.doc)
        unknown_law_region['laws'][0]['regions'] = ['no_such_region']
        check('S.unknown_law_region_refused',
              refused('missing_law_region', ms.validate_material_state,
                      unknown_law_region))
        drift_renames = copy.deepcopy(self.doc)
        drift_renames['renames'] = {'toes_left': 'toes_right'}
        check('S.rename_of_live_region_refused',
              refused('rename_of_live_region', ms.validate_material_state,
                      drift_renames))
        renames_no_prov = copy.deepcopy(self.doc)
        renames_no_prov.pop('provenance', None)
        renames_no_prov['renames'] = {'old': 'toes_left'}
        check('S.renames_require_provenance',
              refused('renames_require_provenance', ms.validate_material_state,
                      renames_no_prov))

    @classmethod
    def tearDownClass(cls):
        fails = [c for c in CHECKS if not c[1]]
        print('\nPROBE SUMMARY: %d named checks, %d failed' % (len(CHECKS), len(fails)))
        for name, _, detail in fails:
            print('FAILED: %s :: %s' % (name, detail))


if __name__ == '__main__':
    unittest.main(verbosity=2)
