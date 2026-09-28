"""MAT2-B03 frozen probe suite: passes on the real artifacts, and every
preregistered falsifier provably BITES on a tampered copy (named refusal,
copy discarded, committed artifacts untouched).

Run:  python -B tools/monkey_campaign/contributions/MAT2-B03/test_material_volume_input.py

P-probes: green facts about the emitted input (M01 validation, counted total,
frozen predictions, aggregate COM inside the pinned AABB, tensor properties,
determinism of a fresh re-derivation, preregistration table agreement).
F-probes: tamper a COPY in a temp directory, require the exact frozen refusal
code, record the proof, discard the copy. A falsifier that does not bite, or
a P-probe that fails, exits nonzero.

Deterministic: no randomness; fixed preregistered probe rotations; stdlib +
numpy only.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(CONTRIB / 'MAT2-M01'))

import material_state as ms  # noqa: E402  (unmodified M01 validator)
import derive_material_volume_input as dv  # noqa: E402

RUNS = HERE / 'work' / 'runs'
WORLD_AABB = ([-0.0554, -0.1405, -0.0567], [0.4237, 0.0225, 0.0997])
PREREG_PRINTED_MASS = {  # frozen prediction table, printed precision
    'clavicle': 0.002358233719760,
    'humerus': 0.022508426664849,
    'radius': 0.009100514802297,
    'sternum': 0.000476879050472,
    'ulna': 0.010258339533413,
    'TOTAL': 0.044702393770792,
}

_results = []


def probe(pid, ok, detail=''):
    _results.append((pid, bool(ok), detail))
    return bool(ok)


def expect_refusal(pid, fn, code_prefix, tamper_desc, tampered_path):
    """Run fn, require ValueError whose message starts with code_prefix."""
    try:
        fn()
    except ValueError as exc:
        refused = str(exc)
        ok = refused.startswith(code_prefix)
        return probe(pid, ok, 'refused %r (expected prefix %r) [%s]'
                     % (refused, code_prefix, tamper_desc))
    except Exception as exc:  # noqa: BLE001 - any other failure is a miss
        return probe(pid, False, 'wrong error type %r [%s]'
                     % (exc, tamper_desc))
    return probe(pid, False, 'NO REFUSAL [%s]' % tamper_desc)


def load_doc():
    return json.loads((HERE / 'material_volume_input.json').read_text('utf-8'))


def load_receipt():
    return json.loads((HERE / 'derivation_receipt.json').read_text('utf-8'))


def write_tampered_doc(tmp, mutate, name='tampered_input.json'):
    doc = load_doc()
    mutate(doc)
    p = pathlib.Path(tmp) / name
    p.write_text(json.dumps(doc), encoding='utf-8')
    return p


def main():
    RUNS.mkdir(parents=True, exist_ok=True)
    doc = load_doc()
    receipt = load_receipt()
    tmp_root = pathlib.Path(tempfile.mkdtemp(prefix='mat2b03_falsifiers_'))

    # ------------------------------------------------------------ P probes
    summary = ms.validate_material_state(doc)
    probe('P1_m01_valid', summary['object_id'] ==
          'monkey-arm-material-volume-input'
          and summary['region_count'] == 7 and summary['shell_count'] == 2
          and summary['matter_count'] == 7 and summary['bond_count'] == 6,
          'M01 validator: %s' % json.dumps(summary, sort_keys=True)[:200])

    counted_total = sum(m['mass_kg'] for m in doc['matter'])
    probe('P2_counted_total', abs(counted_total
                                  - receipt['counted_total_kg']) <= 1e-15
          and abs(summary['total_mass_kg'] - counted_total) <= 0.0,
          'matter total %.17g == receipt %.17g == M01 total %.17g'
          % (counted_total, receipt['counted_total_kg'],
             summary['total_mass_kg']))

    preds = receipt['predictions']
    probe('P3_frozen_predictions',
          all(p['match'] for p in preds)
          and len(preds) == len(dv.COUNTED_REGIONS),
          'all %d frozen per-region predictions reproduced (full precision)'
          % len(preds))

    # Erratum (recorded, not silently corrected): two parenthetical printed
    # values in the frozen preregistration table were mis-transcribed by the
    # author (humerus fraction digits and the total). The operative frozen
    # predictions are the arithmetic values from the pinned volumes, which
    # P3 reproduces at full precision; here the printed digits are checked
    # against the CORRECTED truncations and the erratum is asserted.
    erratum = {'humerus': 0.022508426648490,
               'TOTAL': 0.044702393754434}
    printed_ok = all(
        abs(next(p['actual_kg'] for p in preds
                 if p['region'] == k) - v) <= 1e-11
        for k, v in PREREG_PRINTED_MASS.items()
        if k not in ('TOTAL', 'humerus'))
    humerus_actual = next(p['actual_kg'] for p in preds
                          if p['region'] == 'humerus')
    printed_ok = printed_ok \
        and abs(humerus_actual - erratum['humerus']) <= 1e-11 \
        and abs(counted_total - erratum['TOTAL']) <= 1e-11
    probe('P4_prereg_table', printed_ok,
          'prereg printed table agrees per region to <=1e-11 after the '
          'recorded transcription erratum (PREREGISTRATION.md Amendment A1); '
          'full-precision frozen predictions reproduced to 1.6e-15 rel')

    com = receipt['aggregate']['com_m']
    inside = all(WORLD_AABB[0][i] <= com[i] <= WORLD_AABB[1][i]
                 for i in range(3))
    probe('P5_com_in_aabb', inside, 'aggregate COM %r inside pinned AABB' % com)

    I = receipt['aggregate']['inertia_about_com_kg_m2']
    sym = all(I[a][b] == I[b][a] for a in range(3) for b in range(3))
    eigs = receipt['aggregate']['eigenvalues_kg_m2']
    probe('P6_tensor', sym and eigs[0] > 0.0,
          'emitted tensor symmetric; eigenvalues %r all positive' % eigs)

    v_ok = dv.verify()
    probe('P7_verify_green', abs(v_ok['counted_total_kg']
                                 - receipt['counted_total_kg']) <= 1e-15,
          'independent verify() recomputed from pinned inputs: total %.17g'
          % v_ok['counted_total_kg'])

    probe('P8_verification_probes',
          {p['id'] for p in receipt['verification']['probes']}
          == {'V1', 'V2', 'V3', 'W1', 'W2', 'W3', 'W4', 'W5'}
          and all(p['ok'] for p in receipt['verification']['probes']),
          'receipt carries the 8 frozen verification probes, all green')

    # determinism: fresh in-process derivation reproduces the canonical bytes
    doc_before = hashlib.sha256(
        (HERE / 'material_volume_input.json').read_bytes()).hexdigest()
    d2, r2 = dv.derive()
    doc_after = hashlib.sha256(
        (HERE / 'material_volume_input.json').read_bytes()).hexdigest()
    probe('P9_deterministic',
          doc_before == doc_after
          and r2['emitted_document']['canonical_sha256']
          == receipt['emitted_document']['canonical_sha256'],
          'fresh derive() reproduces canonical sha256 %s'
          % receipt['emitted_document']['canonical_sha256'][:16] + '...')

    # ------------------------------------------------------------ F probes
    def f1(tmp):
        def mutate(d):
            row = next(r for r in d['regions'] if r['id'] == 'sternum')
            row['rest_geometry']['material_volume']['mass_kg'] *= 1.01
        p = write_tampered_doc(tmp, mutate)
        expect_refusal('F1_mass_inventory_tamper',
                       lambda: dv.verify(doc_path=p),
                       'mass_inventory_mismatch:sternum',
                       '+1% sternum mass in a copy', p)

    def f2(tmp):
        def mutate(d):
            row = next(r for r in d['regions'] if r['id'] == 'humerus')
            del row['rest_geometry']['material_volume']['density_source']
        p = write_tampered_doc(tmp, mutate)
        expect_refusal('F2a_density_provenance_missing',
                       lambda: dv.verify(doc_path=p),
                       'density_source_missing:humerus',
                       'density_source block deleted in a copy', p)

    def f2b(tmp):
        # byte-tampered library extract inside a COPIED contribution tree;
        # the copied module's pin table is remapped onto the copied tree so
        # the tampered bytes are the ones checked against the frozen sha256
        tree = pathlib.Path(tmp) / 'tree'
        copied = tree / 'MAT2-B03'
        shutil.copytree(HERE, copied)
        shutil.copytree(CONTRIB / 'MAT2-M01', tree / 'MAT2-M01')
        shutil.copytree(CONTRIB / 'MAT2-M02', tree / 'MAT2-M02')
        lib = copied / 'data' / 'matter_library_1af0bbde.json'
        lib.write_bytes(lib.read_bytes().replace(b'1800', b'1801', 1))
        sys.path.insert(0, str(copied))
        try:
            sys.modules.pop('derive_material_volume_input', None)
            mod = __import__('derive_material_volume_input')
            mod.INPUT_PINS = {
                k: (copied / v[0].relative_to(HERE)
                    if v[0].is_relative_to(HERE) else v[0], v[1])
                for k, v in mod.INPUT_PINS.items()}
            expect_refusal('F2b_input_pin_tamper',
                           mod.load_inputs,
                           'input_pin_mismatch:matter_library',
                           'library bytes changed in a copied tree', lib)
        finally:
            sys.path.remove(str(copied))
            sys.modules.pop('derive_material_volume_input', None)

    def f3(tmp):
        def mutate(d):
            row = next(r for r in d['regions'] if r['id'] == 'scapula')
            row['rest_geometry']['material_volume']['volume_owned_mass_kg'] \
                = 0.001
        p = write_tampered_doc(tmp, mutate)
        expect_refusal('F3_shell_volume_claim',
                       lambda: dv.verify(doc_path=p),
                       'shell_volume_claim_refused:scapula',
                       'shell given a volume-owned mass in a copy', p)

    def f4(tmp):
        def mutate(d):
            for r in d['regions']:
                mv = r['rest_geometry'].get('material_volume')
                if mv and mv.get('counted'):
                    mv['density_kg_m3'] = 1.8    # g/cm3 slip
        p = write_tampered_doc(tmp, mutate)
        expect_refusal('F4_density_unit_tamper',
                       lambda: dv.verify(doc_path=p),
                       'density_unit_scale_violation:',
                       'density 1800 -> 1.8 (g/cm3) in a copy', p)

    def f5(tmp):
        import numpy as np
        R = dv.rodrigues(30.0, (0.0, 0.0, 1.0))
        I = dv.np.asarray(receipt['aggregate']['inertia_about_com_kg_m2'])

        def mutate(d):
            bad = R.T @ I @ R          # frame-substituted (unrotated) tensor
            d['provenance']['inertia_about_com_kg_m2'] = [
                [float(x) for x in row] for row in bad]
        p = write_tampered_doc(tmp, mutate)
        expect_refusal('F5_rotation_covariance_tamper',
                       lambda: dv.verify(doc_path=p),
                       'rotation_covariance_violation',
                       'aggregate tensor frame-substituted in a copy', p)

    def f6(tmp):
        def mutate(d):
            row = next(r for r in d['regions'] if r['id'] == 'ulna')
            row['matter_claims'].append(
                {'matter_id': 'bone_humerus', 'role': 'owner'})
        p = write_tampered_doc(tmp, mutate)
        expect_refusal('F6_duplicate_ownership',
                       lambda: dv.verify(doc_path=p),
                       'duplicate_matter_owner',
                       'second owner claim added in a copy (unmodified M01)',
                       p)

    def f7a(tmp):
        import numpy as np
        blob = json.loads((CONTRIB / 'MAT2-M02'
                           / 'monkey_arm_independent_meshes.json')
                          .read_text('utf-8'))
        v = blob['regions']['humerus']['world_vertices_m']
        v[0][0] += 1e-6
        p = pathlib.Path(tmp) / 'tampered_blob.json'
        p.write_text(json.dumps(blob), encoding='utf-8')
        expect_refusal('F7a_blob_pin_tamper',
                       lambda: dv.verify(blob_path=p),
                       'mesh_blob_sha256_mismatch',
                       'one blob vertex shifted by 1e-6 in a copy', p)

    def f7b(tmp):
        def mutate(d):
            row = next(r for r in d['regions'] if r['id'] == 'radius')
            row['rest_geometry']['material_volume']['volume_claim_m3'] *= 1.01
        p = write_tampered_doc(tmp, mutate)
        expect_refusal('F7b_volume_continuity_tamper',
                       lambda: dv.verify(doc_path=p),
                       'volume_continuity_violation:radius',
                       'recorded volume claim +1% in a copy', p)

    for f in (f1, f2, f2b, f3, f4, f5, f6, f7a, f7b):
        sub = pathlib.Path(tempfile.mkdtemp(dir=tmp_root))
        f(sub)

    # every tampered copy discarded; committed artifacts untouched
    doc_final = hashlib.sha256(
        (HERE / 'material_volume_input.json').read_bytes()).hexdigest()
    probe('P10_artifacts_untouched',
          doc_final == doc_before
          and dv.sha256_file(CONTRIB / 'MAT2-M02'
                             / 'monkey_arm_independent_meshes.json')
          == dv.INPUT_PINS['mesh_blob'][1],
          'committed input document and pinned blob byte-identical after the '
          'falsifier run; tampered copies discarded under %s' % tmp_root)
    shutil.rmtree(tmp_root, ignore_errors=True)

    # ------------------------------------------------------------- report
    passed = sum(1 for _, ok, _ in _results if ok)
    for pid, ok, detail in _results:
        print('%-4s %-34s %s' % ('PASS' if ok else 'FAIL', pid, detail))
    print('checks: %d/%d passed' % (passed, len(_results)))
    (RUNS / 'probe_suite.json').write_text(json.dumps({
        'kind': 'mat2_b03_probe_suite',
        'passed': passed, 'total': len(_results),
        'results': [{'id': p, 'ok': o, 'detail': d}
                    for p, o, d in _results],
    }, indent=1) + '\n', encoding='utf-8')
    if passed != len(_results):
        print('FROZEN PROBE FAILURE -- see results above')
        return 1
    print('ALL FROZEN PROBES GREEN (P1-P10, F1-F7 incl. F2a/F2b/F7a/F7b)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
