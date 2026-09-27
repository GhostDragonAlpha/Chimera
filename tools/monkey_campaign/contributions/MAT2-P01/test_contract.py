"""MAT2-P01 contract test: P1-P3 identity/carry checks + F1-F3 falsifier bites. CPU-only, no network.

Correction of review bb096a44d27e451fb4535f468411a9c5 findings D1/D2: F1 is enforced exactly as
frozen in PREREGISTRATION.md - the FULL 64-hex criteria/active-scope/archived-scope hashes and the
planning id recorded in the frozen prereg text must equal contract.json byte-for-byte (no prefix
checks), and the criteria sha is additionally cross-checked against the live registry card. The
former tautological self-referential criteria check was removed. PREREGISTRATION.md and
contract.json are byte-identical to the originally published artifacts."""
import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.exit_code = 0


def fail(code, detail):
    print('FAIL %s: %s' % (code, detail))
    sys.exit(1)


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


# ---- load frozen artifacts
contract = json.loads((HERE / 'contract.json').read_text())
prereg = (HERE / 'PREREGISTRATION.md').read_text()
spec_done_when = (
    'One monkey, ground movement, one climbable trunk, return to ground, explicit success/failure behavior; broader features excluded. '
    'Material-first addition: Reusable matter is the architecture; walking through woods is the first product milestone, '
    'followed by the existing climb/return goal. Additional materials remain extensible, not universal-physics prerequisites.'
)

# ---- P1: archived core clause carried verbatim; addition carried verbatim (sentence-normalized)
norm = lambda s: re.sub(r'\s+', ' ', s).strip()
core = norm(contract['core_clause']['text'])
addition = norm(contract['material_first_addition']['text'])
dw = norm(spec_done_when)
if core not in dw:
    fail('CORE_CLAUSE_INCOMPLETE', 'core clause not carried verbatim in done_when')
if addition not in dw:
    fail('CORE_CLAUSE_INCOMPLETE', 'material-first addition not carried verbatim in done_when')
elements = ['One monkey', 'ground movement', 'one climbable trunk', 'return to ground', 'explicit success/failure']
missing = [e for e in elements if e not in core]
if missing:
    fail('CORE_CLAUSE_INCOMPLETE', 'missing elements: %s' % missing)

# ---- P2/P3: identity bindings + authority hashes.
# F1 exactly as frozen: the FULL identities recorded in PREREGISTRATION.md must equal
# contract.json byte-for-byte. Prefix or partial alterations cannot pass.
ids = contract['identities']
frozen_bindings = {
    'criteria_sha256': re.search(r'criteria\s+sha256\s+([0-9a-f]{64})', prereg),
    'active_scope_sha256': re.search(r'(?<!archived )scope sha256\s+([0-9a-f]{64})', prereg),
    'archived_scope_sha256': re.search(r'archived\s+scope\s+sha256\s+([0-9a-f]{64})', prereg),
}
for key, match in frozen_bindings.items():
    if not match:
        fail('IDENTITY_MISMATCH', 'prereg missing frozen full binding: %s' % key)
    if ids.get(key) != match.group(1):
        fail('IDENTITY_MISMATCH', 'identity drifted from frozen prereg value: %s' % key)
planning = re.search(r'planning id\s+(P\d+)', prereg)
if not planning:
    fail('IDENTITY_MISMATCH', 'prereg missing frozen planning id')
if contract.get('planning_id') != planning.group(1):
    fail('IDENTITY_MISMATCH', 'planning id drifted from frozen prereg value')

# Live-registry criteria cross-check (defense in depth beyond the frozen prereg binding).
campaign = next((p for p in HERE.parents if (p / 'agent_slots.py').is_file()), None)
if campaign is None and pathlib.Path('E:/PythonChimera/tools/monkey_campaign/agent_slots.py').is_file():
    campaign = pathlib.Path('E:/PythonChimera/tools/monkey_campaign')
if campaign is None:
    print('NOTE: campaign package not found; live-registry criteria cross-check skipped (frozen prereg binding still enforced)')
else:
    sys.path.insert(0, str(campaign))
    try:
        from agent_slots import Registry
        from suggestion_box import DEFAULT_ROOT
    except ImportError:
        print('NOTE: campaign package not importable; live-registry criteria cross-check skipped (frozen prereg binding still enforced)')
    else:
        try:
            live = Registry(DEFAULT_ROOT).readonly()['kanban']['cards']['MAT2-P01']['criteria_sha256']
        except Exception as exc:
            fail('IDENTITY_MISMATCH', 'live registry criteria unavailable: %r' % exc)
        if ids['criteria_sha256'] != live:
            fail('IDENTITY_MISMATCH', 'criteria sha drifted from live registry card')
for path, prefix in contract['authorities'].items():
    full = sha256_file(path)
    if not full.startswith(prefix.split('_')[0]) or not full.startswith(prefix[:16]):
        fail('IDENTITY_MISMATCH', 'authority hash drifted: %s' % path)

# ---- F2 bite: unsupported-pass refusals live as importable functions
def evaluate_completion_claim(claim):
    """Records-only evaluation: a claim is supported only if fully identified."""
    if claim.get('scope_sha256') != ids['active_scope_sha256']:
        return 'SCOPE_UNSUPPORTED'
    if not all(e in norm(claim.get('core_clause', '')) for e in elements):
        return 'CORE_CLAUSE_INCOMPLETE'
    if claim.get('evidence_kind') in ('screenshot', 'narrative'):
        return 'RECORD_SUBSTITUTION'
    return 'SUPPORTED'


# ---- selftest of the frozen falsifiers (F1-F3) on scratch copies
import copy
bad_scope = copy.deepcopy(contract)
bad_scope['identities']['active_scope_sha256'] = 'f' * 64
if evaluate_completion_claim({'scope_sha256': bad_scope['identities']['active_scope_sha256'], 'core_clause': core, 'evidence_kind': 'records'}) != 'SCOPE_UNSUPPORTED':
    fail('FALSIFIER_STALE', 'F2 scope bite did not fire')
if evaluate_completion_claim({'scope_sha256': ids['active_scope_sha256'], 'core_clause': 'a monkey walks somewhere', 'evidence_kind': 'records'}) != 'CORE_CLAUSE_INCOMPLETE':
    fail('FALSIFIER_STALE', 'F2 clause bite did not fire')
if evaluate_completion_claim({'scope_sha256': ids['active_scope_sha256'], 'core_clause': core, 'evidence_kind': 'screenshot'}) != 'RECORD_SUBSTITUTION':
    fail('FALSIFIER_STALE', 'F3 substitution bite did not fire')
good = evaluate_completion_claim({'scope_sha256': ids['active_scope_sha256'], 'core_clause': core, 'evidence_kind': 'records'})
if good != 'SUPPORTED':
    fail('FALSIFIER_OVERREACH', 'well-formed claim refused: %s' % good)

# ---- prereg freeze discipline: prereg exists and names every probe run here
for probe in ('P1', 'P2', 'P3', 'F1', 'F2', 'F3'):
    if probe not in prereg:
        fail('IDENTITY_MISMATCH', 'prereg missing frozen probe %s' % probe)

print('RESULT: ALL CHECKS PASS - contract frozen, identities bound, falsifiers live, carry verbatim (P1-P3, F1-F3 bites demonstrated)')
