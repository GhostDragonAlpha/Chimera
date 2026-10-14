"""Pilot core-falsifier verification: wiseman_osim reads served FROM THE STORE.

Runs the same 7-taxa parse twice in one process:
  pass 1  CHIMERA_DATA_STORE unset   -> in-repo no-op mode (base behavior)
  pass 2  CHIMERA_DATA_STORE=<store> -> store-resolved mode

Records, per taxon: the resolved byte source (store path vs in-repo path), the
manifest pin verdict, and canonical(parse) -- which must be IDENTICAL across
passes (same bytes, same parse, wherever they are served from). Cross-checks
pass-2 Macaque canonical against the pin-repair receipt's preregistered
fcc119b953cf93d957760770e3d24884f79f9db14396e7f12b7ec4ec7857f792.
Also proves the pin-drift refusal fires under BOTH modes (the load-bearing
test_pin_drift path).
"""
import hashlib
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from tools.science_funnel import data_store as DS
from tools.science_funnel.common import Refusal, canonical
from tools.science_funnel import wiseman_osim as W

STORE = 'E:/ChimeraData'
TAXA = list(W.TAXA)
PINNED_MACAQUE = 'fcc119b953cf93d957760770e3d24884f79f9db14396e7f12b7ec4ec7857f792'  # wiseman_pin_repair_20260921 F4


def one_pass(label):
    out = {'mode': label, 'env': os.environ.get('CHIMERA_DATA_STORE'), 'taxa': {}}
    for t in TAXA:
        rel = W.model_path(t)
        entry = next(f for f in W.MANIFEST['files'] if f['path'] == rel)
        # where would pinned_bytes read from? ask resolve() the same question it answers
        p = DS.resolve('wiseman2026/' + rel, pin=entry['sha256'])
        served_from_store = str(p).lower().startswith(str(Path(STORE)).lower())
        raw = W.pinned_bytes(rel)
        pin_ok = (hashlib.sha256(raw).hexdigest() == entry['sha256'] and len(raw) == entry['bytes'])
        model = W.parse_wiseman(t)
        can = canonical(model)
        if isinstance(can, str):
            can = can.encode('utf-8')
        out['taxa'][t] = {'resolved_path': str(p), 'served_from_store': served_from_store,
                          'pin_verified': bool(pin_ok),
                          'canonical_sha256': hashlib.sha256(can).hexdigest()}
    # drift refusal must fire in this mode too
    original = W.MANIFEST['files'][0]['sha256']
    W.MANIFEST['files'][0]['sha256'] = '0' * 64
    try:
        W.pinned_bytes(W.MANIFEST['files'][0]['path'])
        out['drift_refusal'] = False
    except Refusal as e:
        out['drift_refusal'] = 'source_pin_drift' in str(e)
    finally:
        W.MANIFEST['files'][0]['sha256'] = original
    return out


def main():
    os.environ.pop('CHIMERA_DATA_STORE', None)
    repo_pass = one_pass('env-unset (in-repo no-op)')
    assert os.environ.get('CHIMERA_DATA_STORE') is None

    os.environ['CHIMERA_DATA_STORE'] = STORE
    store_pass = one_pass('CHIMERA_DATA_STORE set (store-resolved)')

    report = {
        'schema': 'chimera.data_store_pilot_verification.v1',
        'repo_pass': repo_pass,
        'store_pass': store_pass,
        'checks': {},
    }
    checks = report['checks']
    checks['all_7_served_from_store'] = all(v['served_from_store'] for v in store_pass['taxa'].values())
    checks['all_7_pins_verified_from_store'] = all(v['pin_verified'] for v in store_pass['taxa'].values())
    checks['canonical_identical_across_modes'] = all(
        repo_pass['taxa'][t]['canonical_sha256'] == store_pass['taxa'][t]['canonical_sha256'] for t in TAXA)
    checks['repo_pass_all_in_repo'] = all(not v['served_from_store'] for v in repo_pass['taxa'].values())
    checks['drift_refusal_both_modes'] = bool(repo_pass['drift_refusal']) and bool(store_pass['drift_refusal'])
    checks['macaque_canonical_matches_pin_repair_receipt'] = (
        store_pass['taxa']['Macaque']['canonical_sha256'] == PINNED_MACAQUE)
    report['verdict'] = ('PASS 7/7 store-served, pins verified, parses byte-identical'
                         if all(checks.values()) else 'FAIL')
    out = Path(__file__).resolve().parent / 'store_verification.json'
    out.write_text(json.dumps(report, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    for k, v in checks.items():
        print(f'{k}: {v}')
    print('macaque canonical sha256:', store_pass['taxa']['Macaque']['canonical_sha256'])
    print('verdict:', report['verdict'])
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
