"""MAT2-D-MASSREG register generator (PREREGISTRATION.md, frozen 2026-09-30).

THE LAW: register, not repair. This executable ENUMERATES and CLASSIFIES the
campaign's mass contributors from pinned producer bytes; it changes no
simulation mass and repairs no value. Every entry value is bit-copied from
its pinned producer bytes. Every refusal is a named code (PREREGISTRATION
section 10).

Modes (one process each, CPU-only, no GPU, no wall-clock in receipts):
  main       verify pins; enumerate; classify; run the implied-BW
             measurement; write mass_register.json + implied_bw_receipt.json
             + enumeration_receipt.json.
  rerun      second fresh main-equivalent for X2 byte-identity (writes
             *_rerun2.json copies).
  compare    X2 determinism: mass_register.json is the declared determinism
             unit; byte-identity across the two runs.
  falsify    the four FA arms (PREREG 7.4): clean control FIRST, named
             premature guard, receipt row; tampered copies live in the
             attempt scratch, never committed.
  regression the sealed b07 mass_audit.py re-run UNMODIFIED at this
             revision; its receipt byte-stable (pre/post sha equality).
  zerodelta  the zero-mass-delta proof Z1-Z4 (PREREG 8); run LAST so its
             base..head diff covers every other receipt; the receipt commit
             itself is excluded by construction and disclosed in the report.

Determinism: canonical JSON bytes (sorted keys, no spaces, ensure_ascii=False,
allow_nan=False, UTF-8, LF). Floats round-trip from pinned bytes; no value is
re-derived to replace a pinned literal.
"""
from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
CHECKOUT = HERE.parents[3]          # .../<attempt>/checkout
WORKSPACE = CHECKOUT.parent         # .../<attempt>/ (attempt workspace)
SCRATCH = WORKSPACE / 'scratch'     # OUTSIDE the checkout worktree
REPO = 'E:/PythonChimera'

CARD_FULL = 'MAT2-D-MASSREG'
ATTEMPT_ID = '33f33eb7fed04003857b6a3fbaedf9ed'
CRITERIA_SHA256 = ('fce0e3b30b21ae0f45493fd7d493c9ad694120bb6edc870e1f2cee'
                   '56f65afa2f')
BASE_SHA = 'c525b82c7c3ce0128565424764293a3c85811ab3'
PREFIX = 'tools/monkey_campaign/contributions/MAT2-D-MASSREG/'
FLOAT_FLOOR = 1e-12
PENDING_CLASS = 'PENDING_IMPLIED_BW'

MODES = ('main', 'rerun', 'compare', 'falsify', 'regression', 'zerodelta')

STORE = 'E:/ChimeraWork/monkey-coordination/evidence-store'
ANCHOR_CARD = 'MAT2-D-MASSREG'

# ---- frozen pins (PREREGISTRATION section 5) -----------------------------
PINNED_FILES = {
    'dw04': ('E:/ChimeraWork/monkey-coordination/b07-prereqs/inputs/'
             'dw04_mass_matrix.json',
             '6a32229438f59158a0995b6b90043639e8b103eedf2d09243502faaa9a68ff39'),
    'producer_fit': ('E:/ChimeraWork/monkey-coordination/b07-prereqs/inputs/'
                     'actual_monkey_fit@43b599a7.json',
                     '7b5d6345f6d56ec77c072aecefde2ae592e3bc3fc96b439e5eff164'
                     '425834268'),
    'b03': ('E:/ChimeraWork/monkey-coordination/b07-prereqs/inputs/'
            'b03_material.json',
            '6e8033f26c823f410eb5beb8fdaaefd4c0c37db61327a86221e087bc832b9dd'
            'c'),
    'b05_ports': ('E:/ChimeraWork/monkey-coordination/b07-prereqs/inputs/'
                  'b05_ports.json',
                  'ef69ee740262cc5783e763517e4d27e0306f31d059b8273bb125486a'
                  'd7647f3d'),
    'b06_audit_receipt': ('E:/ChimeraWork/monkey-coordination/b07-prereqs/'
                          'numerical/mass_audit_receipt.json',
                          '3aea85bc7e07ebceb3d1f6f9e969fc9af14edc198620d28ef'
                          '955da619d351922'),
    'b06_audit_script': ('E:/ChimeraWork/monkey-coordination/b07-prereqs/'
                         'mass_audit.py',
                         '8191f724a6fa3a19dd4f78ac311f8dabaa228b9550aaf968c0'
                         'c8650ea5e2e886'),
    'm28_csv': ('E:/ChimeraWork/research-data/20260929/cheng_tables/'
                'M2-8_regressions.csv',
                'b185ee8e98b6e663defed0abd4d004fec053eb6417e027c54801070cd8'
                '94ec22'),
    'm26_csv': ('E:/ChimeraWork/research-data/20260929/cheng_tables/'
                'M2-6_mulatta_inertials.csv',
                '1948a2d8399b5253461c6ed70eed87ea38c5df4083b75437e1e3dbd1a4'
                'ce93f3'),
    'm02_regions': ('E:/ChimeraWork/monkey-coordination/kanban-attempts/'
                    'MAT2-M02/9abf87253e91484cabbb825acb44a7e3/checkout/'
                    'tools/monkey_campaign/contributions/MAT2-M02/'
                    'monkey_arm_regions.json',
                    '15ae0e5a3d540d52b9a0e5c9b8af2f8a6bf7f2c9770a5f2cd7c1e9'
                    'e8758366f1'),
    'gaitscene_source': ('E:/ChimeraWork/research-data/20260929/gait-bench'
                         'mark/GAIT_BENCHMARK.md',
                         'cb98a8f9ffd67b272215a2e7667bc9dfff99b81fad5eefba5'
                         'd96263d5d5f851a'),
    'repin_study': ('E:/ChimeraWork/monkey-coordination/re-pin/'
                    'REPIN_STUDY.md',
                    '99cde4758566784b5b98ad45db19f50beba2c81d8b1761428af19e'
                    '32290c318b'),
}
GIT_BLOBS = {
    'gait_scene': {
        'blob': '5c8792aef60f9eb2eb2e10549546ff12a2efe21b',
        'commit': '33e7a444fe7b4c35aa99afe7ef898046877025b4',
        'path': 'tools/science_funnel/gait_scene.py',
        'sha256': ('92d3011f7f728c6f6f2dcb40c39497737c4e5af67033c92da6a3b46'
                   'dd2d42f9d'),
    },
    'derived_numbers': {
        'blob': '8b6d75fbd408a8e1e2db31cdf15fc4a104b9a36a',
        'commit': '33e7a444fe7b4c35aa99afe7ef898046877025b4',
        'path': ('tools/science_funnel/validation/gait_controller_20260918/'
                 'derived_numbers.json'),
        'sha256': ('013810f87a6ca7c1e01916ef7a5454e61e8d0e88f8d6a589fbfdd15'
                   '14017a173'),
    },
    'derive_k_fill': {
        'blob': 'bfce9681049b7d9354bd498fbf011a633f0ed26f',
        'commit': '33e7a444fe7b4c35aa99afe7ef898046877025b4',
        'path': ('tools/science_funnel/validation/k_fill_20260920/'
                 'derive_k_fill.py'),
        'sha256': ('5150792591a63252abc6a150148b6519b4704abf020e563db5a4a1c'
                   '20f392bea'),
    },
    'derive_adjudication': {
        'blob': '53c324f354576f32d99bbc67b70fce2dc7744f6a',
        'commit': '33e7a444fe7b4c35aa99afe7ef898046877025b4',
        'path': ('tools/science_funnel/validation/ankle_adjudication_202609'
                 '20/derive_adjudication.py'),
        'sha256': ('5912fb21e57d963780a4b81200f8746235243aa64a172f492a8a582'
                   '0afe2db8b'),
    },
    'producer_fit_blob': {
        'blob': 'b76546c2ffbd022639ebeba3fd7dc26d2d5b50bf',
        'commit': '43b599a7c1f11e789cd414b40d7305b9be05066d',
        'path': ('forearm_package/baseline_snapshot/runs/'
                 'actual_monkey_fit.json'),
        'sha256': ('7b5d6345f6d56ec77c072aecefde2ae592e3bc3fc96b439e5eff164'
                   '425834268'),
    },
}

# store-relative anchor paths (anchored BEFORE main runs; build verifies each
# anchor row exists in the store manifest with exactly these bytes)
ANCHOR_PATHS = {
    'dw04': ANCHOR_CARD + '/source/dw04_mass_matrix.json',
    'producer_fit': ANCHOR_CARD + '/source/actual_monkey_fit@43b599a7.json',
    'b03': ANCHOR_CARD + '/source/b03_material.json',
    'b05_ports': ANCHOR_CARD + '/source/b05_ports.json',
    'b06_audit_receipt': ANCHOR_CARD + '/numerical/mass_audit_receipt.json',
    'b06_audit_script': ANCHOR_CARD + '/source/mass_audit.py',
    'm28_csv': ANCHOR_CARD + '/source/M2-8_regressions.csv',
    'm26_csv': ANCHOR_CARD + '/source/M2-6_mulatta_inertials.csv',
    'm02_regions': ANCHOR_CARD + '/source/monkey_arm_regions.json',
    'gait_scene': ANCHOR_CARD + '/source/gait_scene@33e7a444.py',
    'derived_numbers': ANCHOR_CARD + '/source/derived_numbers@33e7a444.json',
    'derive_k_fill': ANCHOR_CARD + '/source/derive_k_fill@33e7a444.py',
    'derive_adjudication': (ANCHOR_CARD +
                            '/source/derive_adjudication@33e7a444.py'),
    'gaitscene_source': ANCHOR_CARD + '/source/GAIT_BENCHMARK.md',
    'repin_study': ANCHOR_CARD + '/source/REPIN_STUDY.md',
}
PIN_SHA_FOR_ANCHOR = dict(
    [(name, PINNED_FILES[name][1]) for name in
     ('dw04', 'producer_fit', 'b03', 'b05_ports', 'b06_audit_receipt',
      'b06_audit_script', 'm28_csv', 'm26_csv', 'm02_regions',
      'gaitscene_source', 'repin_study')]
    + [(name, GIT_BLOBS[name]['sha256']) for name in
       ('gait_scene', 'derived_numbers', 'derive_k_fill',
        'derive_adjudication')]
)

# ---- frozen sealed numbers (PREREGISTRATION sections 7.2/7.3) ------------
FROZEN = {
    'scene_body_total': 10.038,
    'scene_carve': 10.037998,
    'transported_under_assumption': 5.262978509953907,
    'all_transported': 17.039978509953905,
    'root_reference_share': 0.6911393692850295,
    'b03_counted_total': 0.0447023937544344,
    'excluded_osim_claims': 0.406,
    'band_midpoint': 6.15,
    'acceptance_denominator': 13824.5,
    'atlas_c1': {'upper_arm': 7.8779, 'forearm': 7.8795, 'hand': 7.7978},
    'atlas_c2': {'upper_arm': 5.2326, 'forearm': 6.0938, 'hand': 4.9097},
    'male_class_window': (9.0, 11.0),
    'female_band_window': (5.4, 6.9),
}
FAMILY_COUNTS = {
    'scene.walk': 14,
    'scene.acceptance_denominator': 1,
    'buffy.transported': 9,
    'buffy.unresolved': 9,
    'b03.counted': 5,
    'b03.zero_shell': 2,
    'b03.density': 1,
    'osim.regions': 7,
    'reference.turnquist': 3,
}
SYSTEMS = {
    'scene': ('masses the simulation law consumes or carries: the sealed '
              'walk scene family (gait_scene.py @33e7a444, scene f6844eea '
              'identity) and the acceptance-denominator membrane inventory'),
    'biological-reference': ('masses living in biological/specimen reference '
                             'ledgers: the Buffy transported assembly, the '
                             'B03 counted bone set, the osim '
                             'effective-segment claims, the Turnquist '
                             'body-weight band'),
}
LAW_TEXT = ('register-not-repair: the scene law and the biological-reference '
            'law are TWO DISTINCT, never-reconciled mass systems; the '
            'register records both, admits nothing, and changes no '
            'simulation mass')
SPECIMEN_CLASSES = ('cheng-consistent-male-class',
                    'internally-inconsistent-female-band',
                    'intermediate-unresolved')
OUT_OF_SCOPE = [
    {'contributor_id': 'out_of_scope.m03_membrane', 'value_kg': 0.05,
     'reason': 'M03 synthetic_authored demonstrator membrane; not a '
               'contributor to either registered system (REPIN_STUDY 1.5)'},
    {'contributor_id': 'out_of_scope.m05_body_a', 'value_kg': 0.05,
     'reason': 'M05 fixture body (REPIN_STUDY 1.6)'},
    {'contributor_id': 'out_of_scope.m05_body_b', 'value_kg': 0.02,
     'reason': 'M05 fixture body (REPIN_STUDY 1.6)'},
    {'contributor_id': 'out_of_scope.m05_body_c', 'value_kg': 0.002,
     'reason': 'M05 fixture body (REPIN_STUDY 1.6)'},
    {'contributor_id': 'out_of_scope.m07_m08_fixture_a', 'value_kg': 0.02,
     'reason': 'M07/M08 sealed two-component fixture (REPIN_STUDY 1.8; M08 '
               'introduces no new mass)'},
    {'contributor_id': 'out_of_scope.m07_m08_fixture_b', 'value_kg': 0.02,
     'reason': 'M07/M08 sealed two-component fixture (REPIN_STUDY 1.8)'},
    {'contributor_id': 'out_of_scope.m07_m08_mount', 'value_kg': 0.0,
     'reason': 'M07/M08 fixture zero-mass row (REPIN_STUDY 1.8)'},
]
GAPS = [
    {'gap_id': 'GAP-2', 'statement': 'mass-lineage anomaly 10.038 vs '
     '5.4-6.9 kg; adjudicated register-not-repair (REPIN_STUDY 3)'},
    {'gap_id': 'GAP-3', 'statement': 'walk-scene arm segment split 0.2737/'
     '0.1323 is the admitted hind-borrowed split; only the 0.406001 kg '
     'total traces to a source'},
    {'gap_id': 'GAP-4', 'statement': 'B03 bone density 1800 kg/m3 is '
     'authored literature-typical; no measured conditioned density exists'},
    {'gap_id': 'GAP-8', 'statement': 'M02 sternum 6.6 kg is osim '
     'effective-segment bookkeeping; the 7.006 kg arm total is referenced '
     'by no downstream consumer as a body mass'},
]
SUBSUMPTION_HAZARD = ('a future decomposition that counts transported '
                      'segment masses for humerus/radius must SUBSUME '
                      '(replace), never add to, the B03 counted bone masses '
                      'of the same bones (B06 CHK-7)')


class RegisterRefusal(ValueError):
    """Named refusal (PREREGISTRATION section 10)."""


def refuse(code, detail=''):
    raise RegisterRefusal(code + ('' if not detail else ': ' + str(detail)))


def sha256_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def refuse_vacuous_comparison(a, b, code='vacuous_comparison_refused'):
    """A window/tolerance gate whose two sides are identically zero cannot
    fail; such comparisons are REFUSED (M07/M08 law via card-kit)."""
    if a == 0.0 and b == 0.0:
        raise RegisterRefusal(code)


def vacuous_guard_selftest():
    """Must be True in every receipt of the executable that gates a
    tolerance comparison (the guard is tested on every run)."""
    fired = False
    try:
        refuse_vacuous_comparison(0.0, 0.0)
    except RegisterRefusal as exc:
        fired = str(exc) == 'vacuous_comparison_refused'
    return fired


def canonical(value):
    """The one serializer for register/receipt bytes (card-kit byte law)."""
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def write_bytes(path, raw):
    pathlib.Path(path).write_bytes(raw)


# ---- pin verification ------------------------------------------------------
def verify_input_pins():
    pins = {}
    for name, (path, expected) in PINNED_FILES.items():
        p = pathlib.Path(path)
        if not p.exists():
            refuse('input_pin_missing', name + ' ' + path)
        got = sha256_bytes(p.read_bytes())
        if got != expected:
            refuse('input_pin_drift', '%s %s != %s' % (name, got, expected))
        pins[name] = {'path': path, 'sha256': got}
    return pins


def git(*args):
    proc = subprocess.run(['git', '-c', 'safe.directory=' + REPO, '-C', REPO]
                          + list(args), capture_output=True, timeout=120)
    if proc.returncode:
        refuse('producer_blob_missing',
               'git ' + ' '.join(args[:3]) + ' failed: '
               + proc.stderr.decode('utf-8', 'replace')[-300:])
    return proc.stdout


def git_checkout(*args):
    """Git in the ATTEMPT checkout (branch-1 head, shared object store).
    rev-parse HEAD / diff must run HERE - the source repo's HEAD is a
    different branch entirely."""
    checkout = str(CHECKOUT)
    proc = subprocess.run(['git', '-c', 'safe.directory=' + checkout,
                           '-C', checkout] + list(args),
                          capture_output=True, timeout=120)
    if proc.returncode:
        refuse('producer_blob_missing',
               'git(checkout) ' + ' '.join(args[:3]) + ' failed: '
               + proc.stderr.decode('utf-8', 'replace')[-300:])
    return proc.stdout


def git_blob_bytes(name):
    pin = GIT_BLOBS[name]
    tree_sha = git('rev-parse',
                   pin['commit'] + ':' + pin['path']).decode().strip()
    if tree_sha != pin['blob']:
        refuse('producer_blob_drift',
               '%s tree %s != pinned blob %s' % (name, tree_sha, pin['blob']))
    raw = git('cat-file', 'blob', pin['blob'])
    got = sha256_bytes(raw)
    if got != pin['sha256']:
        refuse('producer_blob_drift',
               '%s bytes %s != %s' % (name, got, pin['sha256']))
    return raw


def load_json_bytes(raw, label):
    try:
        return json.loads(raw.decode('utf-8'))
    except Exception as exc:
        refuse('input_pin_drift', label + ' unparsable: ' + str(exc))


def check_anchor(name, digest):
    """The write-time gate: the anchor row must exist in the store manifest
    with exactly these bytes."""
    manifest = load_json_bytes(
        pathlib.Path(STORE, 'MANIFEST.json').read_bytes(), 'store_manifest')
    rows = {r['stored_rel_path']: r for r in manifest['files']}
    rel = ANCHOR_PATHS[name]
    if rel not in rows:
        refuse('anchor_missing', rel)
    if rows[rel]['sha256'] != digest:
        refuse('anchor_sha_mismatch',
               '%s manifest %s != observed %s'
               % (rel, rows[rel]['sha256'], digest))


# ---- enumerators -----------------------------------------------------------
def extract_scene(scene_blob, derived, dw04):
    seg = derived['body_model']['segments_Table1']
    hat = seg['HAT']['mass_kg']
    thigh = seg['thigh']['mass_kg']
    shank = seg['shank']['mass_kg']
    foot = seg['foot']['mass_kg']
    toe = seg['phalanges']['mass_kg']
    text = scene_blob.decode('utf-8')
    m = re.search(r'2\*(0\.406001)', text)
    if not m:
        refuse('row_absent_from_producer', 'carve constant 0.406001')
    carve = float(m.group(1))
    ms = re.search(r'\("upperarm", (0\.2737), 0\.125\), \("forearm", '
                   r'(0\.1323), 0\.132\)', text)
    if not ms:
        refuse('row_absent_from_producer', 'forelimb strut constants')
    upperarm = float(ms.group(1))
    forearm = float(ms.group(2))
    mg = re.search(r"'name':'ground','mass_kg':(0\.0)", text)
    if not mg:
        refuse('row_absent_from_producer', 'ground zero-mass body')
    ground = float(mg.group(1))

    hind = thigh + shank + foot + toe
    body_total = hat + 2 * hind
    if body_total != FROZEN['scene_body_total']:
        refuse('register_total_mismatch',
               'body-model order %r != %r'
               % (body_total, FROZEN['scene_body_total']))
    carve_sum = (hat - 2 * carve) + 2 * hind + 2 * (upperarm + forearm)
    if carve_sum != FROZEN['scene_carve']:
        refuse('register_total_mismatch',
               'carve order %r != %r' % (carve_sum, FROZEN['scene_carve']))
    if derived['body_model']['mass_kg'] != FROZEN['scene_body_total']:
        refuse('register_total_mismatch', 'derived_numbers mass_kg')
    if dw04['masses'][1]['kg'] != FROZEN['scene_body_total']:
        refuse('register_total_mismatch', 'dw04 masses[1].kg')
    mtot = 0.0
    for value in [ground, hat - 2 * carve,
                  thigh, shank, foot, toe,
                  thigh, shank, foot, toe,
                  upperarm, forearm, upperarm, forearm]:
        mtot += value
    floor_ok = abs(mtot - FROZEN['scene_carve']) <= FLOAT_FLOOR * max(
        1.0, abs(mtot), abs(FROZEN['scene_carve']))

    anchor_builder = {'path': ANCHOR_PATHS['gait_scene'],
                      'sha256': GIT_BLOBS['gait_scene']['sha256']}
    anchor_derived = {'path': ANCHOR_PATHS['derived_numbers'],
                      'sha256': GIT_BLOBS['derived_numbers']['sha256']}
    sha_builder = GIT_BLOBS['gait_scene']['sha256']
    sha_derived = GIT_BLOBS['derived_numbers']['sha256']
    gap3 = ('builder verbatim: measured total arm mass and documented '
            'lengths; the quad-share lane hind-thigh:shank split supplies '
            'the two segment masses (GAP-3): biological reading of the '
            'split is UNVALIDATED; the pair sum traces to the Oku carve')

    def entry(cid, value, note, anchor, producer_sha, klass):
        return {
            'contributor_id': cid,
            'system': 'scene',
            'source_kind': 'pinned-producer',
            'value_kg': value,
            'value_literal': repr(value),
            'unit': 'kg',
            'quantity': 'mass',
            'producer_receipt_sha256': producer_sha,
            'validation_state': 'validated',
            'validation_note': note,
            'evidence_anchor': anchor,
            'specimen_class': klass,
            'role': {'is_training_body': cid != 'scene.walk.ground',
                     'is_cot_denominator': False},
        }

    entries = [
        entry('scene.walk.ground', ground,
              'declared zero-mass world body of the sealed scene builder',
              anchor_builder, sha_builder, PENDING_CLASS),
        entry('scene.walk.pelvis', hat - 2 * carve,
              'pelvis = HAT 8.184 - 2x0.406001 Oku arm-chain carve (builder '
              'lines 70-72; assembly doc section 2)',
              anchor_builder, sha_builder, PENDING_CLASS),
        entry('scene.walk.thigh_left', thigh,
              'Oku 2021 Table 1 thigh segment mass (scene-scope certified: '
              'bit-identity with the sealed trainer-consumed scene bytes)',
              anchor_derived, sha_derived, PENDING_CLASS),
        entry('scene.walk.shank_left', shank,
              'Oku 2021 Table 1 shank segment mass (scene-scope certified)',
              anchor_derived, sha_derived, PENDING_CLASS),
        entry('scene.walk.foot_left', foot,
              'Oku 2021 Table 1 foot segment mass (scene-scope certified)',
              anchor_derived, sha_derived, PENDING_CLASS),
        entry('scene.walk.toe_left', toe,
              'Oku 2021 Table 1 phalanges segment mass (scene-scope '
              'certified)', anchor_derived, sha_derived, PENDING_CLASS),
        entry('scene.walk.thigh_right', thigh,
              'Oku 2021 Table 1 thigh segment mass (scene-scope certified)',
              anchor_derived, sha_derived, PENDING_CLASS),
        entry('scene.walk.shank_right', shank,
              'Oku 2021 Table 1 shank segment mass (scene-scope certified)',
              anchor_derived, sha_derived, PENDING_CLASS),
        entry('scene.walk.foot_right', foot,
              'Oku 2021 Table 1 foot segment mass (scene-scope certified)',
              anchor_derived, sha_derived, PENDING_CLASS),
        entry('scene.walk.toe_right', toe,
              'Oku 2021 Table 1 phalanges segment mass (scene-scope '
              'certified)', anchor_derived, sha_derived, PENDING_CLASS),
        entry('scene.walk.upperarm_fore_left', upperarm, gap3,
              anchor_builder, sha_builder, PENDING_CLASS),
        entry('scene.walk.forearm_fore_left', forearm, gap3,
              anchor_builder, sha_builder, PENDING_CLASS),
        entry('scene.walk.upperarm_fore_right', upperarm, gap3,
              anchor_builder, sha_builder, PENDING_CLASS),
        entry('scene.walk.forearm_fore_right', forearm, gap3,
              anchor_builder, sha_builder, PENDING_CLASS),
    ]
    facts = {
        'hat': hat, 'carve': carve, 'upperarm': upperarm,
        'forearm': forearm, 'hind_sum': hind,
        'body_total_bit_exact': body_total == FROZEN['scene_body_total'],
        'carve_sum_bit_exact': carve_sum == FROZEN['scene_carve'],
        'builder_order_sum': mtot,
        'builder_order_bit_exact': mtot == FROZEN['scene_carve'],
        'builder_order_within_floor': floor_ok,
        'strut_pair_sum': upperarm + forearm,
        'strut_pair_bit_equal_carve': (upperarm + forearm) == carve,
        'dw04_masses1_literal': dw04['masses'][1]['literal'],
    }
    return entries, facts


def enumerate_denominator(dw04):
    m0 = dw04['masses'][0]
    if m0['kg'] != FROZEN['acceptance_denominator']:
        refuse('register_total_mismatch', 'dw04 masses[0].kg')
    raw = pathlib.Path(PINNED_FILES['dw04'][0]).read_bytes()
    return {
        'contributor_id': 'scene.acceptance_denominator.membrane_inventory',
        'system': 'scene',
        'source_kind': 'pinned-producer',
        'value_kg': m0['kg'],
        'value_literal': repr(m0['kg']),
        'unit': 'kg',
        'quantity': 'mass',
        'producer_receipt_sha256': sha256_bytes(raw),
        'validation_state': 'unvalidated-density',
        'validation_note': '13.824536 m3 sealed matter cells at authored '
                           'water density 1000 kg/m3 (D-W04 masses[0]); the '
                           'CoT denominator, NOT a body; '
                           'selection-invariant mismatch ratio 1377.2166 '
                           'recorded',
        'evidence_anchor': {'path': ANCHOR_PATHS['dw04'],
                            'sha256': sha256_bytes(raw)},
        'specimen_class': PENDING_CLASS,
        'specimen_class_receipt_sha256': None,
        'role': {'is_training_body': False, 'is_cot_denominator': True},
    }


def enumerate_buffy(fit, dw04, pins):
    raw_sha = pins['producer_fit']['sha256']
    anchor = {'path': ANCHOR_PATHS['producer_fit'], 'sha256': raw_sha}
    adm = fit['admission']
    totals = adm['totals_mass_kg']
    phys = fit['physiology']
    if len(phys) != 9:
        refuse('count_mismatch', 'physiology rows %d != 9' % len(phys))
    unresolved = adm['bodies']['unresolved']
    if len(unresolved) != 9:
        refuse('count_mismatch', 'unresolved %d != 9' % len(unresolved))
    entries = []
    products_exact = True
    for p in phys:
        pelvis = p['body'] == 'pelvis'
        if pelvis:
            state = 'non-physical-reference'
            note = ('mass_kind root_ref_frame_unscaled, det_scale 1.0; the '
                    'producer excludes it from physical admission: identity '
                    'scale carries the original mass as a reference-frame '
                    'quantity (69.11 percent of the total, non-physical)')
            kind = 'pinned-producer'
        else:
            state = 'unvalidated-density'
            note = ('source_effective_x_det_scale under the producer '
                    'uniform_constant_density_scale assumption; '
                    'requires_density_validation, density_validated false; '
                    'nothing admitted')
            kind = 'det-scaled'
        if p['mass'] != p['mass_src'] * p['det_scale']:
            products_exact = False
            refuse('value_not_bit_copied',
                   '%s mass != mass_src*det_scale' % p['body'])
        entries.append({
            'contributor_id': 'buffy.transported.' + p['body'],
            'system': 'biological-reference',
            'source_kind': kind,
            'value_kg': p['mass'],
            'value_literal': repr(p['mass']),
            'unit': 'kg',
            'quantity': 'mass',
            'producer_receipt_sha256': raw_sha,
            'validation_state': state,
            'validation_note': note,
            'evidence_anchor': dict(anchor),
            'specimen_class': 'unmeasured-det-scaled-assumption',
            'specimen_class_receipt_sha256': None,
            'role': {'mass_src_kg': p['mass_src'],
                     'det_scale': p['det_scale'], 'counted': False},
        })
    for body in unresolved:
        entries.append({
            'contributor_id': 'buffy.unresolved.' + body,
            'system': 'biological-reference',
            'source_kind': 'pinned-producer',
            'value_kg': 0.0,
            'value_literal': repr(0.0),
            'unit': 'kg',
            'quantity': 'mass',
            'producer_receipt_sha256': raw_sha,
            'validation_state': 'non-physical-reference',
            'validation_note': 'producer-unresolved body, zero transported '
                               'mass, not silently repaired (B06 CHK-8); '
                               'the B05 carried-load question has no '
                               'transported backing',
            'evidence_anchor': dict(anchor),
            'specimen_class': 'unmeasured-no-source',
            'specimen_class_receipt_sha256': None,
            'role': {'counted': False, 'unresolved': True},
        })
    tua = 0.0
    for p in phys:
        if p['body'] != 'pelvis':
            tua += p['mass']
    if tua != totals['transported_under_assumption']:
        refuse('register_total_mismatch', 'CHK-2 recomputed %r' % tua)
    total = (totals['transported_under_assumption']
             + totals['physically_admitted'] + totals['flagged_only']
             + totals['root_reference_only'])
    if total != totals['all_transported']:
        refuse('register_total_mismatch', 'CHK-3 recomputed %r' % total)
    if total != FROZEN['all_transported']:
        refuse('register_total_mismatch',
               'all_transported %r != sealed %r'
               % (total, FROZEN['all_transported']))
    if dw04['masses'][3]['kg'] != total:
        refuse('register_total_mismatch', 'dw04 masses[3].kg')
    share = totals['root_reference_only'] / totals['all_transported']
    if share != FROZEN['root_reference_share']:
        refuse('register_total_mismatch', 'root share %r' % share)
    facts = {
        'transported_under_assumption': tua,
        'all_transported': total,
        'root_share': share,
        'physically_admitted': totals['physically_admitted'],
        'flagged_only': totals['flagged_only'],
        'density_validated': adm['mass_admission']['density_validated'],
        'assumption': adm['mass_admission']['assumption'],
        'products_bit_exact': products_exact,
        'sums_bit_exact': True,
    }
    return entries, facts


def enumerate_b03(b03, pins):
    raw = pathlib.Path(PINNED_FILES['b03'][0]).read_bytes()
    raw_sha = sha256_bytes(raw)
    anchor = {'path': ANCHOR_PATHS['b03'], 'sha256': raw_sha}
    counted_regions = b03['provenance']['counted_set']['regions']
    if len(counted_regions) != 5:
        refuse('count_mismatch', 'counted regions')
    by_region = {}
    for matter in b03['matter']:
        region = matter['id'].replace('bone_', '').replace('shell_', '')
        by_region[region] = matter
    entries = []
    for region in counted_regions:
        matter = by_region[region]
        if 'counted region' not in matter['provenance']:
            refuse('row_absent_from_producer', 'counted region ' + region)
        entries.append({
            'contributor_id': 'b03.counted.' + region,
            'system': 'biological-reference',
            'source_kind': 'pinned-producer',
            'value_kg': matter['mass_kg'],
            'value_literal': repr(matter['mass_kg']),
            'unit': 'kg',
            'quantity': 'mass',
            'producer_receipt_sha256': raw_sha,
            'validation_state': 'unvalidated-density',
            'validation_note': 'volume-owned m = integral rho dV at the '
                               'AUTHORED 1800 kg/m3 density (GAP-4); '
                               'counted region (R-MASS-01)',
            'evidence_anchor': dict(anchor),
            'role': {'counted': True, 'density_kg_m3': 1800.0},
        })
    for zero_id in ('shell_hand', 'shell_scapula'):
        matter = next(m for m in b03['matter'] if m['id'] == zero_id)
        if matter['mass_kg'] != 0.0:
            refuse('value_not_bit_copied', zero_id)
        entries.append({
            'contributor_id': 'b03.zero_shell.'
                              + zero_id.replace('shell_', ''),
            'system': 'biological-reference',
            'source_kind': 'pinned-producer',
            'value_kg': 0.0,
            'value_literal': repr(0.0),
            'unit': 'kg',
            'quantity': 'mass',
            'producer_receipt_sha256': raw_sha,
            'validation_state': 'non-physical-reference',
            'validation_note': 'open surface, zero volume-owned mass by '
                               'refusal (shell_volume_claim_refused)',
            'evidence_anchor': dict(anchor),
            'role': {'counted': False},
        })
    density = None
    band = None
    for region in b03.get('regions', []):
        mv = region.get('material_volume') if isinstance(region, dict) \
            else None
        if mv and mv.get('density_kg_m3') is not None:
            density = mv['density_kg_m3']
            band = mv.get('density_band_kg_m3')
            break
    if density is None:
        text = raw.decode('utf-8')
        mm = re.search(r'"density_kg_m3": (1800\.0)', text)
        mb = re.search(r'"density_band_kg_m3":\s*\[\s*(1650\.0),\s*'
                       r'(1950\.0)', text)
        if not mm or not mb:
            refuse('row_absent_from_producer', 'density literals')
        density = float(mm.group(1))
        band = [float(mb.group(1)), float(mb.group(2))]
    if density != 1800.0 or band != [1650.0, 1950.0]:
        refuse('value_not_bit_copied', 'density/band literals')
    entries.append({
        'contributor_id': 'b03.density.bone_assumed',
        'system': 'biological-reference',
        'source_kind': 'reference-constant',
        'value_kg': None,
        'value_literal': repr(density),
        'unit': 'kg/m3',
        'quantity': 'density',
        'value': density,
        'producer_receipt_sha256': raw_sha,
        'validation_state': 'unvalidated-density',
        'validation_note': 'AUTHORED literature-typical cortical density, '
                           'band [%r, %r]; no gravimetric macaque wet '
                           'density exists (Astra gap; GAP-4)'
                           % (band[0], band[1]),
        'evidence_anchor': dict(anchor),
        'role': {'density_band_kg_m3': band},
    })
    total = 0.0
    for region in counted_regions:
        total += by_region[region]['mass_kg']
    if total != b03['provenance']['counted_set']['counted_total_kg']:
        refuse('register_total_mismatch', 'b03 counted sum %r' % total)
    if total != FROZEN['b03_counted_total']:
        refuse('register_total_mismatch', 'b03 counted sealed')
    facts = {'counted_total': total,
             'counted_ids': list(counted_regions),
             'density': density, 'density_band': band,
             'sum_bit_exact': True}
    return entries, facts


def enumerate_osim(m02, pins):
    raw = pathlib.Path(PINNED_FILES['m02_regions'][0]).read_bytes()
    raw_sha = sha256_bytes(raw)
    anchor = {'path': ANCHOR_PATHS['m02_regions'], 'sha256': raw_sha}
    entries = []
    free = {}
    for matter in m02['matter']:
        if not matter['id'].startswith('mass_'):
            continue
        region = matter['id'][len('mass_'):]
        free[region] = matter['mass_kg']
        entries.append({
            'contributor_id': 'osim.regions.' + region,
            'system': 'biological-reference',
            'source_kind': 'pinned-producer',
            'value_kg': matter['mass_kg'],
            'value_literal': repr(matter['mass_kg']),
            'unit': 'kg',
            'quantity': 'mass',
            'producer_receipt_sha256': raw_sha,
            'validation_state': 'non-physical-reference',
            'validation_note': 'sealed osim effective-segment bookkeeping '
                               '(authored arm reference, NOT a measured '
                               'specimen quantity); S-MASS-05 screened '
                               'INSIDE-1SD vs Cheng M2-6, never validated '
                               'for this specimen; counted=false; excluded '
                               'claim' + (' (GAP-8: unreferenced '
                                          'bookkeeping convention)'
                                          if region == 'sternum' else ''),
            'evidence_anchor': dict(anchor),
            'role': {'counted': False, 'excluded_claim': True},
        })
    if len(entries) != 7:
        refuse('count_mismatch', 'osim regions %d' % len(entries))
    excluded = free['humerus'] + free['radius'] + free['ulna'] + free['hand']
    facts = {'regions': free, 'excluded_free_limb_sum': excluded,
             'excluded_sealed': FROZEN['excluded_osim_claims'],
             'excluded_within_floor': abs(
                 excluded - FROZEN['excluded_osim_claims'])
             <= FLOAT_FLOOR * max(1.0, abs(excluded)),
             'arm_total': sum(free.values())}
    return entries, facts


def enumerate_reference(dw04, kfill_blob, adj_blob):
    m2 = dw04['masses'][2]
    if m2['kg'] != FROZEN['band_midpoint']:
        refuse('register_total_mismatch', 'band midpoint')
    mb = re.search(r'band (5\.4)-(6\.9) kg', m2['semantic_identity'])
    if not mb:
        refuse('row_absent_from_producer', 'band literals in dw04 masses[2]')
    low = float(mb.group(1))
    high = float(mb.group(2))
    if 'AF_MIDPOINT_KG = 6.15' not in kfill_blob.decode('utf-8'):
        refuse('row_absent_from_producer', 'AF_MIDPOINT_KG')
    if 'BAND_MIDPOINT_KG = 6.15' not in adj_blob.decode('utf-8'):
        refuse('row_absent_from_producer', 'BAND_MIDPOINT_KG')
    raw_sha = PINNED_FILES['dw04'][1]
    anchor = {'path': ANCHOR_PATHS['dw04'], 'sha256': raw_sha}

    def entry(cid, value, band_role, note):
        return {
            'contributor_id': cid,
            'system': 'biological-reference',
            'source_kind': 'reference-constant',
            'value_kg': value,
            'value_literal': repr(value),
            'unit': 'kg',
            'quantity': 'mass',
            'producer_receipt_sha256': raw_sha,
            'validation_state': 'validated',
            'validation_note': note,
            'evidence_anchor': dict(anchor),
            'specimen_class': 'adult-female-band',
            'specimen_class_receipt_sha256': None,
            'role': {'band': band_role},
        }

    band_note = ('receipted adult-female M. mulatta body band, Turnquist & '
                 'Kessler 1989 (D-W04 masses[2]; derive_adjudication.py '
                 'BAND_MIDPOINT_KG; the adjudicated BW reference for every '
                 'BW-normalized claim)')
    entries = [
        entry('reference.turnquist.band_low', low, 'low', band_note),
        entry('reference.turnquist.band_midpoint', m2['kg'], 'midpoint',
              'band midpoint (5.4+6.9)/2 = 6.15 exactly; AF_MIDPOINT_KG / '
              'BAND_MIDPOINT_KG; book context, NOT the walker rigid mass '
              '(D-W04 masses[2])'),
        entry('reference.turnquist.band_high', high, 'high', band_note),
    ]
    facts = {'low': low, 'mid': m2['kg'], 'high': high,
             'midpoint_bit_exact': True}
    return entries, facts


# ---- implied-BW measurement (PREREG 7.3, frozen design) --------------------
def implied_bw_measurement(pins, scene_facts, m02_facts):
    m28_raw = pathlib.Path(PINNED_FILES['m28_csv'][0]).read_bytes()
    m26_raw = pathlib.Path(PINNED_FILES['m26_csv'][0]).read_bytes()
    rows28 = list(csv.reader(io.StringIO(m28_raw.decode('utf-8-sig'))))
    mrow = next(r for r in rows28
                if r[0] == 'Segment mass' and r[1].startswith('m ('))
    brow = next(r for r in rows28
                if r[0] == 'Segment mass' and r[1].startswith('b ('))
    m = {'upper_arm': float(mrow[2]), 'forearm': float(mrow[3]),
         'hand': float(mrow[4]), 'forearm_hand': float(mrow[5])}
    b = {'upper_arm': float(brow[2]), 'forearm': float(brow[3]),
         'hand': float(brow[4]), 'forearm_hand': float(brow[5])}
    rows26 = list(csv.reader(io.StringIO(m26_raw.decode('utf-8-sig'))))
    mass26 = next(r for r in rows26 if r[0] == 'Segment mass (g)')
    means = {}
    sds = {}
    for col, key in ((1, 'upper_arm'), (2, 'forearm'), (3, 'hand')):
        mm = re.match(r'([0-9.]+) ± ([0-9.]+)', mass26[col])
        means[key] = float(mm.group(1))
        sds[key] = float(mm.group(2))

    def implied(group, mass_g):
        return (mass_g - b[group]) / m[group]

    evals = []
    ua_g = scene_facts['upperarm'] * 1000.0
    fa_g = scene_facts['forearm'] * 1000.0
    carve_g = scene_facts['carve'] * 1000.0
    e1 = implied('upper_arm', ua_g)
    evals.append({'id': 'E1_upper_arm_at_scene_strut', 'group': 'upper_arm',
                  'scene_mass_g': ua_g, 'implied_bw_kg': e1,
                  'caveat': 'split-dependent: the 0.2737/0.1323 split is '
                            'the admitted hind-borrowed split (GAP-3)'})
    e2 = implied('forearm', fa_g)
    evals.append({'id': 'E2_forearm_at_scene_strut', 'group': 'forearm',
                  'scene_mass_g': fa_g, 'implied_bw_kg': e2,
                  'caveat': 'split-dependent (GAP-3)'})
    evals.append({'id': 'E3_hand_at_scene_hand', 'group': 'hand',
                  'scene_mass_g': None, 'implied_bw_kg': None,
                  'refusal': 'hand_row_no_scene_mass',
                  'note': 'the sealed scene carries no hand segment; the '
                          'M2-8 hand row is also the not-significant '
                          'high-leverage row (transcription: Segment mass '
                          'p = UA*, FA*, Hand empty, F+H*)'})
    m_sum2 = m['upper_arm'] + m['forearm']
    b_sum2 = b['upper_arm'] + b['forearm']
    e4 = (carve_g - b_sum2) / m_sum2
    evals.append({'id': 'E4_PRIMARY_split_free_per_arm',
                  'group': 'upper_arm+forearm summed coefficients',
                  'm_sum_g_per_kg': m_sum2, 'b_sum_g': b_sum2,
                  'scene_mass_g': carve_g, 'implied_bw_kg': e4,
                  'note': 'the only scene arm quantity with a source is '
                          'the Oku carve 0.406001 kg; the hand row is NOT '
                          'consumed (no scene hand segment); coefficient '
                          'summation assumes conditional independence '
                          '(atlas A4 analog)'})
    m_sum3 = m_sum2 + m['hand']
    b_sum3 = b_sum2 + b['hand']
    e5 = (carve_g - b_sum3) / m_sum3
    evals.append({'id': 'E5_stress_with_hand_row',
                  'group': 'upper_arm+forearm+hand summed coefficients',
                  'm_sum_g_per_kg': m_sum3, 'b_sum_g': b_sum3,
                  'scene_mass_g': carve_g, 'implied_bw_kg': e5,
                  'note': 'STRESS ONLY: consumes the not-significant '
                          'high-leverage hand row'})
    c1 = {k: round(implied(k, means[k]), 4)
          for k in ('upper_arm', 'forearm', 'hand')}
    c1_ok = c1 == FROZEN['atlas_c1']
    claims_g = {'upper_arm': m02_facts['regions']['humerus'] * 1000.0,
                'forearm': (m02_facts['regions']['radius']
                            + m02_facts['regions']['ulna']) * 1000.0,
                'hand': m02_facts['regions']['hand'] * 1000.0}
    c2 = {k: round(implied(k, claims_g[k]), 4)
          for k in ('upper_arm', 'forearm', 'hand')}
    c2_ok = c2 == FROZEN['atlas_c2']
    t_pi = {k: {'z': abs(claims_g[k] - means[k]) / sds[k],
                'inside_1sd': abs(claims_g[k] - means[k]) <= sds[k],
                't_pi_half_width': 2.776546 * sds[k]} for k in claims_g}
    scene_z = {'upper_arm': abs(ua_g - means['upper_arm'])
               / sds['upper_arm'],
               'forearm': abs(fa_g - means['forearm']) / sds['forearm']}
    low, high = FROZEN['female_band_window']
    mlow, mhigh = FROZEN['male_class_window']
    if mlow <= e4 <= mhigh:
        klass = 'cheng-consistent-male-class'
        branch = 'two-class-registration-close'
    elif low <= e4 <= high:
        klass = 'internally-inconsistent-female-band'
        branch = 'escalation-flagged'
    else:
        klass = 'intermediate-unresolved'
        branch = 'no-reclassification-tension-recorded'
    refused = branch == 'escalation-flagged'
    receipt = {
        'schema': 'chimera.massreg.implied_bw.v1',
        'card': CARD_FULL,
        'attempt_id': ATTEMPT_ID,
        'method': 'implied BW kg = (mass_g - b_g) / (m_g/kg); M2-8 Segment '
                  'mass m/b rows; atlas section 5 discipline',
        'input_pins': {'m28_csv': pins['m28_csv']['sha256'],
                       'm26_csv': pins['m26_csv']['sha256']},
        'm2_8_coefficients': {'m_g_per_kg': m, 'b_g': b,
                              'significance': 'Segment mass p = UA*, FA*, '
                                              'Hand empty, F+H* (hand row '
                                              'not significant)'},
        'm2_6_bands_g': {k: {'mean': means[k], 'sd': sds[k]}
                         for k in means},
        'evaluations': evals,
        'calibration': {
            'C1_m26_means_implied_bw_kg': c1,
            'C1_matches_atlas': c1_ok,
            'C2_osim_claims_implied_bw_kg': c2,
            'C2_matches_atlas': c2_ok,
            'C3_claim_bands': t_pi,
            'C3_scene_strut_z': scene_z,
            't_pi_multiplier': 2.776546,
            'discipline': 'atlas A1-A5 carried; M2-8 prints no dispersion: '
                          'every implied-BW number is an '
                          'UNCERTAINTY-UNCALIBRATED order-of-magnitude '
                          'screen (A5), never a calibrated bound',
        },
        'decision': {
            'rule': 'applied to E4-primary ONLY (frozen PREREG 7.3)',
            'e4_primary_implied_bw_kg': e4,
            'windows': {'male_class_kg': list(FROZEN['male_class_window']),
                        'female_band_kg':
                            list(FROZEN['female_band_window'])},
            'specimen_class': klass,
            'branch': branch,
            'reconciliation_claim': (
                'REFUSED: reconciliation_refused_internal_inconsistency'
                if refused else 'registered per branch; never reconciled'),
            'escalation': (
                'flagged to the walk-tier scene card: the sealed scene '
                'total 10.038 kg coexists with arm masses implying a '
                'female-band body; carried as-is, not repaired'
                if refused else None),
        },
        'determinism': {'canonical_json': True, 'newline': '\\n',
                        'rerun_command':
                            'python -B build_register.py main'},
    }
    return receipt, klass, branch, (c1_ok and c2_ok)


def apply_specimen_class(entries, klass, receipt_raw):
    digest = sha256_bytes(receipt_raw)
    for row in entries:
        if row['system'] == 'scene':
            if row.get('specimen_class') == PENDING_CLASS:
                row['specimen_class'] = klass
            row['specimen_class_receipt_sha256'] = digest
    return digest


# ---- build -----------------------------------------------------------------
def build():
    pins = verify_input_pins()
    for name in ANCHOR_PATHS:
        check_anchor(name, PIN_SHA_FOR_ANCHOR[name])
    scene_blob = git_blob_bytes('gait_scene')
    derived = load_json_bytes(git_blob_bytes('derived_numbers'),
                              'derived_numbers')
    kfill_blob = git_blob_bytes('derive_k_fill')
    adj_blob = git_blob_bytes('derive_adjudication')
    fit_blob = git_blob_bytes('producer_fit_blob')
    fit = load_json_bytes(fit_blob, 'producer_fit')
    if sha256_bytes(fit_blob) != pins['producer_fit']['sha256']:
        refuse('producer_blob_drift', 'fit blob vs pinned copy')
    dw04 = load_json_bytes(pathlib.Path(PINNED_FILES['dw04'][0]).read_bytes(),
                           'dw04')
    b03 = load_json_bytes(pathlib.Path(PINNED_FILES['b03'][0]).read_bytes(),
                          'b03')
    m02 = load_json_bytes(pathlib.Path(PINNED_FILES['m02_regions'][0])
                          .read_bytes(), 'm02')
    audit = load_json_bytes(
        pathlib.Path(PINNED_FILES['b06_audit_receipt'][0]).read_bytes(),
        'b06_audit_receipt')
    if audit['audit_number_kg'] != FROZEN['all_transported']:
        refuse('register_total_mismatch', 'sealed audit number')

    scene_entries, scene_facts = extract_scene(scene_blob, derived, dw04)
    denom = enumerate_denominator(dw04)
    buffy_entries, buffy_facts = enumerate_buffy(fit, dw04, pins)
    b03_entries, b03_facts = enumerate_b03(b03, pins)
    osim_entries, osim_facts = enumerate_osim(m02, pins)
    ref_entries, ref_facts = enumerate_reference(dw04, kfill_blob, adj_blob)

    bw_receipt, klass, branch, calib_ok = implied_bw_measurement(
        pins, scene_facts, osim_facts)
    if not calib_ok:
        refuse('register_total_mismatch',
               'implied-BW calibration C1/C2 vs atlas')
    bw_raw = canonical(bw_receipt)
    apply_specimen_class(scene_entries + [denom], klass, bw_raw)
    for row in buffy_entries:
        row['specimen_class_receipt_sha256'] = sha256_bytes(bw_raw)

    entries = scene_entries + [denom] + buffy_entries + b03_entries \
        + osim_entries + ref_entries
    register = {
        'schema': 'chimera.massreg.register.v1',
        'card': CARD_FULL,
        'attempt_id': ATTEMPT_ID,
        'criteria_sha256': CRITERIA_SHA256,
        'composed_against': 'CARD_STARTER v3; PREREGISTRATION.md frozen '
                            '2026-09-30 commit c5d44831',
        'law': {'text': LAW_TEXT, 'two_systems_declared_distinct': True,
                'reconciliation_declared': False},
        'systems': {k: {'definition': v, 'reconciled_into_one': False}
                    for k, v in SYSTEMS.items()},
        'input_pins': pins,
        'git_object_pins': GIT_BLOBS,
        'entries': entries,
        'totals': {
            'scene_body_total_kg': {
                'value': FROZEN['scene_body_total'],
                'literal': repr(FROZEN['scene_body_total']),
                'source': 'D-W04 masses[1].kg; derived_numbers '
                          'body_model.mass_kg',
                'reproduced_bit_exact': True},
            'scene_carve_sum_kg': {
                'value': FROZEN['scene_carve'],
                'literal': repr(FROZEN['scene_carve']),
                'source': 'D-W04 masses[1].derivation_recomputed; '
                          'GAIT_BENCHMARK scene f6844eea model sum',
                'reproduced_bit_exact': True},
            'builder_order_sum_kg': {
                'value': scene_facts['builder_order_sum'],
                'literal': repr(scene_facts['builder_order_sum']),
                'bit_exact': scene_facts['builder_order_bit_exact'],
                'within_float_floor':
                    scene_facts['builder_order_within_floor'],
                'note': 'the builder ordered 14-body sum; not bit-equal to '
                        'the carve literal (declared honestly, PREREG '
                        '7.2c)'},
            'buffy_transport_under_assumption_kg': {
                'value': buffy_facts['transported_under_assumption'],
                'literal': repr(
                    buffy_facts['transported_under_assumption']),
                'reproduced_bit_exact': True},
            'buffy_all_transported_kg': {
                'value': buffy_facts['all_transported'],
                'literal': repr(buffy_facts['all_transported']),
                'reproduced_bit_exact': True},
            'buffy_root_reference_share': {
                'value': buffy_facts['root_share'],
                'literal': repr(buffy_facts['root_share'])},
            'b03_counted_set_kg': {
                'value': b03_facts['counted_total'],
                'literal': repr(b03_facts['counted_total']),
                'reproduced_bit_exact': True},
            'osim_excluded_free_limb_kg': {
                'value': FROZEN['excluded_osim_claims'],
                'literal': repr(FROZEN['excluded_osim_claims']),
                'recomputed': osim_facts['excluded_free_limb_sum'],
                'within_float_floor': osim_facts['excluded_within_floor']},
            'reference_band_kg': {'low': ref_facts['low'],
                                  'midpoint': ref_facts['mid'],
                                  'high': ref_facts['high']},
            'acceptance_denominator_kg': {
                'value': FROZEN['acceptance_denominator'],
                'literal': repr(FROZEN['acceptance_denominator'])},
        },
        'subsumption_hazard': SUBSUMPTION_HAZARD,
        'double_count_scan': {
            'assembly_counted_mass_kg': 0.0,
            'ledgers_disjoint': True,
            'name_overlap': ['humerus', 'radius'],
            'statement': 'no double count exists in the current ledger; '
                         'the B03 counted set is a separate parallel '
                         'ledger (B06 CHK-7)'},
        'declared_out_of_scope': OUT_OF_SCOPE,
        'gaps': GAPS,
        'specimen_classification': {
            'scene_class': klass,
            'branch': branch,
            'receipt_sha256': sha256_bytes(bw_raw),
            'reconciliation_claim':
                ('REFUSED: reconciliation_refused_internal_inconsistency'
                 if branch == 'escalation-flagged'
                 else 'registered per branch; never reconciled')},
        'anchor_manifest': {name: ANCHOR_PATHS[name]
                            for name in ANCHOR_PATHS},
        'zero_mass_delta': {'receipt': 'zero_mass_delta_receipt.json',
                            'law': 'the register changes no simulation '
                                   'mass; see the receipt'},
        'determinism': {'canonical_json': True, 'newline': '\\n',
                        'rerun_command':
                            'python -B build_register.py main'},
    }
    facts = {'scene': scene_facts, 'buffy': buffy_facts, 'b03': b03_facts,
             'osim': osim_facts, 'reference': ref_facts}
    return register, bw_receipt, facts, pins


# ---- checks (shared by the suite and the falsifier arms) -------------------
FAMILY_PREFIXES = {
    'scene.walk.': 'scene.walk',
    'scene.acceptance_denominator.': 'scene.acceptance_denominator',
    'buffy.transported.': 'buffy.transported',
    'buffy.unresolved.': 'buffy.unresolved',
    'b03.counted.': 'b03.counted',
    'b03.zero_shell.': 'b03.zero_shell',
    'b03.density.': 'b03.density',
    'osim.regions.': 'osim.regions',
    'reference.turnquist.': 'reference.turnquist',
}


def check_register(register, receipts):
    """Return the list of failure codes; [] = green. receipts carries
    anchor_manifest, implied_bw_sha256 and the enumeration facts."""
    failures = []
    if register.get('schema') != 'chimera.massreg.register.v1':
        failures.append('schema_wrong')
    if not register.get('law', {}).get('two_systems_declared_distinct') \
            or register.get('law', {}).get('text') != LAW_TEXT:
        failures.append('reconciliation_declared')
    if sorted(register.get('systems', {})) != ['biological-reference',
                                               'scene']:
        failures.append('reconciliation_declared')
    anchors = receipts.get('anchor_manifest', {})
    fam_counts = {}
    for row in register.get('entries', []):
        cid = row.get('contributor_id', '')
        fam = next((f for p, f in FAMILY_PREFIXES.items()
                    if cid.startswith(p)), None)
        if fam is None:
            failures.append('family_prefix_unknown:' + cid)
            continue
        fam_counts[fam] = fam_counts.get(fam, 0) + 1
        if row.get('system') not in ('scene', 'biological-reference'):
            failures.append('system_vocabulary:' + cid)
        if row.get('source_kind') not in ('pinned-producer', 'det-scaled',
                                          'reference-constant'):
            failures.append('source_kind_vocabulary:' + cid)
        if row.get('validation_state') not in (
                'validated', 'unvalidated-density',
                'non-physical-reference'):
            failures.append('validation_state_vocabulary:' + cid)
        anchor = row.get('evidence_anchor') or {}
        if not anchor:
            failures.append('anchor_missing:' + cid)
        else:
            if not re.fullmatch(r'[0-9a-f]{64}', anchor.get('sha256', '')):
                failures.append('anchor_sha_mismatch:' + cid)
            elif anchors.get(anchor.get('path')) not in (None,
                                                         anchor['sha256']):
                failures.append('anchor_sha_mismatch:' + cid)
        if not re.fullmatch(r'[0-9a-f]{64}',
                            row.get('producer_receipt_sha256', '')):
            failures.append('producer_receipt_sha_missing:' + cid)
        if row.get('value_kg') is not None and \
                repr(row['value_kg']) != row.get('value_literal'):
            failures.append('value_literal_mismatch:' + cid)
        if row.get('system') == 'scene':
            if row.get('specimen_class') not in SPECIMEN_CLASSES:
                failures.append('specimen_class_unbacked:' + cid)
            elif row.get('specimen_class_receipt_sha256') != \
                    receipts.get('implied_bw_sha256'):
                failures.append('specimen_class_unbacked:' + cid)
    for fam, count in FAMILY_COUNTS.items():
        if fam_counts.get(fam, 0) != count:
            failures.append('family_count_mismatch:' + fam)
    # recompute the family sums from the entries themselves
    walk = 0.0
    bt = 0.0
    pelvis = None
    bsum = 0.0
    for row in register.get('entries', []):
        cid = row['contributor_id']
        if cid.startswith('scene.walk.'):
            walk += row['value_kg']
        elif cid.startswith('buffy.transported.'):
            if cid == 'buffy.transported.pelvis':
                pelvis = row['value_kg']
            else:
                bt += row['value_kg']
        elif cid.startswith('b03.counted.'):
            bsum += row['value_kg']
    if walk != FROZEN['scene_carve']:
        refuse_vacuous_comparison(walk, FROZEN['scene_carve'])
        if abs(walk - FROZEN['scene_carve']) > FLOAT_FLOOR * max(
                1.0, abs(walk), abs(FROZEN['scene_carve'])):
            # the builder-order sum is honestly NOT bit-equal to the carve
            # literal (PREREG 7.2c); the floor is the declared discipline
            failures.append('register_total_mismatch:scene_recomputed')
    if bt != FROZEN['transported_under_assumption'] or \
            (bt + (pelvis or 0.0)) != FROZEN['all_transported']:
        failures.append('register_total_mismatch:buffy_recomputed')
    if bsum != FROZEN['b03_counted_total']:
        failures.append('register_total_mismatch:b03_recomputed')
    totals = register.get('totals', {})
    if totals.get('scene_body_total_kg', {}).get('value') != \
            FROZEN['scene_body_total'] or \
            totals.get('scene_carve_sum_kg', {}).get('value') != \
            FROZEN['scene_carve']:
        failures.append('register_total_mismatch:scene')
    tua_total = totals.get('buffy_transport_under_assumption_kg', {}) \
        .get('value')
    if totals.get('buffy_all_transported_kg', {}).get('value') != \
            FROZEN['all_transported'] or \
            tua_total != FROZEN['transported_under_assumption']:
        failures.append('register_total_mismatch:buffy')
    if totals.get('b03_counted_set_kg', {}).get('value') != \
            FROZEN['b03_counted_total']:
        failures.append('register_total_mismatch:b03')
    facts = receipts.get('enumeration', {}).get('families', {}).get(
        'scene', {})
    if not facts.get('body_total_bit_exact') or \
            not facts.get('carve_sum_bit_exact'):
        failures.append('float_order_law_broken')
    return failures


# ---- modes -----------------------------------------------------------------
def emit_main(rerun=False):
    register, bw_receipt, facts, pins = build()
    suffix = '_rerun2' if rerun else ''
    bw_raw = canonical(bw_receipt)
    write_bytes(HERE / ('implied_bw_receipt%s.json' % suffix), bw_raw)
    reg_raw = canonical(register)
    write_bytes(HERE / ('mass_register%s.json' % suffix), reg_raw)
    enum = {
        'schema': 'chimera.massreg.enumeration.v1',
        'card': CARD_FULL,
        'attempt_id': ATTEMPT_ID,
        'criteria_sha256': CRITERIA_SHA256,
        'register_sha256': sha256_bytes(reg_raw),
        'implied_bw_receipt_sha256': sha256_bytes(bw_raw),
        'entry_count': len(register['entries']),
        'family_counts': FAMILY_COUNTS,
        'declared_out_of_scope_count': len(OUT_OF_SCOPE),
        'input_pins_verified': {k: v['sha256'] for k, v in pins.items()},
        'git_blob_pins_verified': {k: v['sha256']
                                   for k, v in GIT_BLOBS.items()},
        'anchor_manifest': {ANCHOR_PATHS[name]: PIN_SHA_FOR_ANCHOR[name]
                            for name in ANCHOR_PATHS},
        'value_bit_copy_verified': {
            'scene': facts['scene']['body_total_bit_exact']
            and facts['scene']['carve_sum_bit_exact'],
            'buffy': facts['buffy']['products_bit_exact']
            and facts['buffy']['sums_bit_exact'],
            'b03': facts['b03']['sum_bit_exact'],
            'osim': facts['osim']['excluded_within_floor'],
            'reference': facts['reference']['midpoint_bit_exact'],
        },
        'vacuous_guard_selftest': vacuous_guard_selftest(),
        'families': facts,
        'specimen_classification': register['specimen_classification'],
        'totals': register['totals'],
    }
    write_bytes(HERE / ('enumeration_receipt%s.json' % suffix),
                canonical(enum))
    print(json.dumps({'entry_count': enum['entry_count'],
                      'scene_class': register['specimen_classification']
                      ['scene_class'],
                      'branch': register['specimen_classification']
                      ['branch'],
                      'register_sha256': enum['register_sha256']},
                     indent=1))


def mode_main():
    emit_main(rerun=False)


def mode_rerun():
    emit_main(rerun=True)
    print('rerun written')


def mode_compare():
    a = sha256_bytes((HERE / 'mass_register.json').read_bytes())
    b = sha256_bytes((HERE / 'mass_register_rerun2.json').read_bytes())
    enum1 = json.loads((HERE / 'enumeration_receipt.json')
                       .read_text('utf-8'))
    enum2 = json.loads((HERE / 'enumeration_receipt_rerun2.json')
                       .read_text('utf-8'))
    only1 = sorted(set(enum1) - set(enum2))
    only2 = sorted(set(enum2) - set(enum1))
    shared_differ = sorted(k for k in set(enum1) & set(enum2)
                           if enum1[k] != enum2[k])
    receipt = {
        'schema': 'chimera.massreg.determinism.v1',
        'register_sha_run1': a,
        'register_sha_run2': b,
        'X2_register_byte_identical': a == b,
        'receipt_keys_only_in_run1': only1,
        'receipt_keys_only_in_run2': only2,
        'receipt_shared_keys_differing': shared_differ,
        'X2_pass': a == b and not only1 and not only2 and not shared_differ,
        'determinism_unit': 'mass_register.json (canonical bytes)',
        'augmentation_keys': [],
    }
    write_bytes(HERE / 'determinism_receipt.json', canonical(receipt))
    print(json.dumps(receipt, indent=1))


def _tamper_copy(register, kind):
    bad = copy.deepcopy(register)
    if kind == 'fb1':
        for i, row in enumerate(bad['entries']):
            if row['contributor_id'] == 'buffy.transported.femur_r':
                del bad['entries'][i]
                return bad
        refuse('falsifier_fixture_missing', 'fb1')
    if kind == 'fb2':
        for row in bad['entries']:
            if row['contributor_id'] == 'scene.walk.pelvis':
                row['value_kg'] = row['value_kg'] + 0.0001
                row['value_literal'] = repr(row['value_kg'])
                return bad
        refuse('falsifier_fixture_missing', 'fb2')
    if kind == 'fb3':
        bad['entries'][0]['evidence_anchor']['sha256'] = '0' * 64
        return bad
    if kind == 'fb4':
        bad['law']['two_systems_declared_distinct'] = False
        bad['law']['text'] = 'one reconciled mass system (TAMPERED)'
        bad['law']['reconciliation_declared'] = True
        return bad
    refuse('falsifier_fixture_missing', kind)


def mode_falsify():
    register, bw_receipt, facts, pins = build()
    receipts = {
        'anchor_manifest': {
            ANCHOR_PATHS[name]: PIN_SHA_FOR_ANCHOR[name]
            for name in ANCHOR_PATHS},
        'implied_bw_sha256': sha256_bytes(canonical(bw_receipt)),
        'enumeration': {'families': facts},
    }
    clean = check_register(register, receipts)
    if clean:
        refuse('massreg_fb_premature',
               'clean register not green: ' + ','.join(clean))
    SCRATCH.mkdir(parents=True, exist_ok=True)
    arms = {}
    specs = [
        ('FB1_row_omission_bites', 'fb1', 'massreg_fb1_premature',
         ['family_count_mismatch:buffy.transported',
          'register_total_mismatch:buffy_recomputed']),
        ('FB2_value_perturbation_bites', 'fb2', 'massreg_fb2_premature',
         ['register_total_mismatch:scene_recomputed']),
        ('FB3_anchor_mismatch_bites', 'fb3', 'massreg_fb3_premature',
         ['anchor_sha_mismatch']),
        ('FB4_reconciliation_declaration_bites', 'fb4',
         'massreg_fb4_premature', ['reconciliation_declared']),
    ]
    for name, kind, guard, expect in specs:
        bad = _tamper_copy(register, kind)
        got = check_register(bad, receipts)
        bit = any(any(obs.startswith(g) for obs in got) for g in expect)
        arms[name] = {
            'tamper': kind,
            'clean_control': {'failures': clean, 'green': not clean,
                              'guard': guard, 'within_scope': True},
            'expected_codes': expect,
            'observed_codes': got,
            'bit': bit,
        }
        write_bytes(SCRATCH / ('tampered_%s.json' % kind), canonical(bad))
    receipt = {
        'schema': 'chimera.massreg.falsifiers.v1',
        'card': CARD_FULL,
        'arms': arms,
        'F_all_green': all(a['bit'] for a in arms.values()),
        'scratch_dir': str(SCRATCH),
        'note': 'tampered copies live in the attempt scratch, never '
                'committed; the clean control ran FIRST in this same '
                'executable',
    }
    write_bytes(HERE / 'falsifier_receipt.json', canonical(receipt))
    print(json.dumps({'F_all_green': receipt['F_all_green'],
                      'arms': {k: v['bit'] for k, v in arms.items()}},
                     indent=1))


def mode_regression():
    target = PINNED_FILES['b06_audit_script'][0]
    pre = sha256_bytes(pathlib.Path(
        PINNED_FILES['b06_audit_receipt'][0]).read_bytes())
    proc = subprocess.run([sys.executable, '-B', target],
                          capture_output=True, text=True, timeout=1800)
    post = sha256_bytes(pathlib.Path(
        PINNED_FILES['b06_audit_receipt'][0]).read_bytes())
    receipt = {
        'schema': 'chimera.massreg.regression.v1',
        'suite': target,
        'exit_code': proc.returncode,
        'tail': proc.stdout[-1200:],
        'receipt_sha_before': pre,
        'receipt_sha_after': post,
        'sealed_receipt_sha_unchanged': pre == post == PINNED_FILES[
            'b06_audit_receipt'][1],
        'P_regression_suite_green': proc.returncode == 0 and pre == post,
    }
    write_bytes(HERE / 'regression_receipt.json', canonical(receipt))
    print(json.dumps({k: receipt[k] for k in (
        'exit_code', 'P_regression_suite_green',
        'sealed_receipt_sha_unchanged')}, indent=1))


def mode_zerodelta():
    head = git_checkout('rev-parse', 'HEAD').decode().strip()
    diff = git_checkout('diff', '--name-status', BASE_SHA + '..' + head)
    changed = [line for line in diff.decode('utf-8').splitlines() if line]
    outside = [c for c in changed
               if not c.split('\t', 1)[-1].startswith(PREFIX)]
    producer_checks = {}
    for name, pin in GIT_BLOBS.items():
        raw1 = git_blob_bytes(name)
        raw2 = git('cat-file', 'blob', pin['blob'])
        producer_checks[name] = {
            'sha256': sha256_bytes(raw2),
            'equal_at_both_extractions': raw1 == raw2,
            'matches_pin': sha256_bytes(raw2) == pin['sha256'],
        }
    audit = load_json_bytes(
        pathlib.Path(PINNED_FILES['b06_audit_receipt'][0]).read_bytes(),
        'b06_audit_receipt')
    dw04 = load_json_bytes(pathlib.Path(PINNED_FILES['dw04'][0]).read_bytes(),
                           'dw04')
    reg = json.loads((HERE / 'mass_register.json').read_text('utf-8'))
    z3 = {
        'all_transported_matches_sealed':
            reg['totals']['buffy_all_transported_kg']['value']
            == audit['audit_number_kg'],
        'tua_matches_sealed':
            reg['totals']['buffy_transport_under_assumption_kg']['value']
            == audit['decomposition_kg']['transported_under_assumption'],
        'scene_body_matches_dw04':
            reg['totals']['scene_body_total_kg']['value']
            == dw04['masses'][1]['kg'] == FROZEN['scene_body_total'],
        'scene_carve_matches_dw04':
            reg['totals']['scene_carve_sum_kg']['value']
            == FROZEN['scene_carve'],
    }
    enum = json.loads((HERE / 'enumeration_receipt.json')
                      .read_text('utf-8'))
    receipt = {
        'schema': 'chimera.massreg.zero_delta.v1',
        'card': CARD_FULL,
        'base_sha': BASE_SHA,
        'head_sha_at_proof_time': head,
        'Z1_all_changed_paths_under_card_prefix': not outside,
        'changed_paths': changed,
        'changed_paths_outside_prefix': outside,
        'Z2_producer_blobs_unchanged': producer_checks,
        'Z3_totals_bit_exact': z3,
        'Z4_register_values_bit_copied':
            enum.get('value_bit_copy_verified', {}),
        'scope_note': 'the zero-delta receipt commit itself is excluded '
                      'from its own diff by construction; head_sha at '
                      'proof time is the artifact commit this receipt was '
                      'generated at',
        'zero_mass_delta': all([
            not outside,
            all(v['equal_at_both_extractions'] and v['matches_pin']
                for v in producer_checks.values()),
            all(z3.values()),
        ]),
    }
    write_bytes(HERE / 'zero_mass_delta_receipt.json', canonical(receipt))
    print(json.dumps({'zero_mass_delta': receipt['zero_mass_delta'],
                      'changed': len(changed), 'outside': len(outside)},
                     indent=1))


def main(argv):
    mode = argv[1] if len(argv) > 1 else 'main'
    if mode not in MODES:
        raise SystemExit('unknown mode: ' + mode + ' (valid: '
                         + ', '.join(MODES) + ')')
    getattr(sys.modules[__name__], 'mode_' + mode)()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
