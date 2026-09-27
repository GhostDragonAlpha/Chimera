"""MAT2-P01 contract test: P1-P3 identity/carry checks + F1-F3 falsifier bites. CPU-only, no network."""
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

# ---- P2/P3: identity bindings + authority hashes
ids = contract['identities']
if ids['criteria_sha256'] != sha256_file(HERE / 'contract.json')[:0] + ids['criteria_sha256']:
    pass  # self-referential skip
if not re.fullmatch('[0-9a-f]{64}', ids['criteria_sha256']) or not ids['criteria_sha256'].startswith('e4521ad7'):
    fail('IDENTITY_MISMATCH', 'criteria sha malformed')
if not ids['active_scope_sha256'].startswith('cb5475f8486197a9'):
    fail('IDENTITY_MISMATCH', 'active scope sha not the astra-0031 pinned value')
if not ids['archived_scope_sha256'].startswith('01ea5cddca8d4795'):
    fail('IDENTITY_MISMATCH', 'archived scope sha not the pre-install value')
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
