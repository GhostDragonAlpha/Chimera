"""MAT2-G08 pinned-dependency materializer for sealed package runs.

The sealed package carries ONLY this card's write scope
(tools/monkey_campaign/contributions/MAT2-G08). The preregistered upstream
interfaces live in the shared repository's Git object database at the
package's pinned base commit; the runner provisions CHIMERA_SOURCE_REPO and
CHIMERA_BASE_SHA for exactly this resolution. ensure() extracts each pinned
blob byte-exactly, asserts its sha256 against the frozen table (the prereg
section 9 pin table plus the two campaign visual-gate modules), and writes it
into the scratch tree at its canonical repo-relative path. Reading the object
database mutates nothing: no checkout, no index, no branch, no new objects
(cat-file only). Refusals are named codes; nothing is silently repaired.

Base: 5f82a3ddb35aac8b59bc4b087a90353e1fb69c1d (origin/review/MAT2-G08 as
seeded; carries the merged G-chain winners G01 #296, G04 #298, G05 #300,
F05 #302, G07 #303, G06 #305). The G08 preregistration commit
f5ae83ce92cf6cb33c14151f491d2e339117ee7f is the published prereg pin
(separate-first commit on exactly this base; the prereg files are frozen in
the package write scope, so the candidate patch vs base and vs the prereg
commit differ only by implementation files).
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
CARD_DIR = HERE                      # .../contributions/MAT2-G08
CONTRIB = HERE.parent                # .../contributions
TOOLS = CONTRIB.parent               # .../tools

DEFAULT_REPO = 'E:/PythonChimera'
DEFAULT_BASE = ('5f82a3ddb35aac8b59bc4b087a90353e1fb69c1d')
PREREG_COMMIT = 'f5ae83ce92cf6cb33c14151f491d2e339117ee7f'

# (repo-relative path, sha256 of the blob bytes) -- the prereg
# PREREGISTRATION.md section 9 repo pin table verbatim, plus the two
# campaign visual-gate modules. All hashes were computed from this exact
# base commit before the preregistration was frozen.
DEPS = (
    ('tools/monkey_campaign/contributions/MAT2-M06/local_contact.py',
     '1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc'),
    ('tools/monkey_campaign/contributions/MAT2-M06/test_local_contact.py',
     'b832d0dc07c1762a190d4b662ceed2b1b6dd469cbd22343cb39934e90eb08e77'),
    ('tools/monkey_campaign/contributions/MAT2-M06/contact_law.json',
     '583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b'),
    ('tools/monkey_campaign/contributions/MAT2-M06/experiment_receipt.json',
     '2956dd7aaf3682fc18de9b724ddd8a695011ec74c9a12a5a56744b3d738a9397'),
    ('tools/monkey_campaign/contributions/MAT2-F03/assets/trunk_01_mesh.json',
     '3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7'),
    ('tools/monkey_campaign/contributions/MAT2-F03/assets/'
     'trunk_01_material_state.json',
     '91c17a5c59ce79af3dc0e8a6dadb00c92a039075775a0a1de618da12dfca61bd'),
    ('tools/monkey_campaign/contributions/MAT2-G04/grip_contact.py',
     '0d6375484c350039468b31a2f7db2895d3365412aee52ce98de72b4173d69245'),
    ('tools/monkey_campaign/contributions/MAT2-G04/test_g04_checks.py',
     'a01b167e4393e2e513ba343f2bc6ba3fdf4d01ee08170f7fe8c3cb1c5c9a0ae1'),
    ('tools/monkey_campaign/contributions/MAT2-G05/contact_support_obs.py',
     '3dae0a3805cec86bba8dbae9a6fc563f43cddc98fcd01a693f725e4f31c46bd3'),
    ('tools/monkey_campaign/contributions/MAT2-G05/test_g05_checks.py',
     '83ba17604f66fdbe623b71ce481b539862ec39ebf81ee4c8bea2e5af29f9985b'),
    ('tools/monkey_campaign/contributions/MAT2-G06/transfer_sequence.py',
     'a3f376f9feafc07897ea331219320b6393bfb69916781a6beb80792c7bd068f9'),
    ('tools/monkey_campaign/contributions/MAT2-G06/test_g06_checks.py',
     'aa03fd9c77663eba41f3fe9f2641245e28318c259a83b6eddcf5d861772f4aed'),
    ('tools/monkey_campaign/contributions/MAT2-G06/experiment_receipt.json',
     'cf5c9cc5b7d51a23f282313974f853edca83ca30c19edd51a36eb9ddf0d3feff'),
    ('tools/monkey_campaign/contributions/MAT2-G06/experiment_trace.json',
     'eec274ded637a4cb10049bc7d427037e3a1e54e72a3c11b55ddf80ec5d18f2f9'),
    ('tools/monkey_campaign/contributions/MAT2-G06/falsifier_receipt.json',
     '97b95e09481e7f02dfd873470b49cb114e2c856aa4fc0cf04bb2d6caeed004bf'),
    ('tools/monkey_campaign/contributions/MAT2-G07/release_fall_account.py',
     '78b5cc66f7019fa181765eb0366fe6c98525941840f57723d0ae99cb55b2a8c5'),
    ('tools/monkey_campaign/contributions/MAT2-G07/test_g07_checks.py',
     '89ce29d6f9b606f6c81df802818715c52a4b0779e816300671a8b5a8b5728522'),
    ('tools/monkey_campaign/contributions/MAT2-G07/experiment_receipt.json',
     'c539617b098190918187d9a7dcbb0a5e33a85998adaa58f6b781703bbdeb88f8'),
    ('tools/monkey_campaign/contributions/MAT2-G07/experiment_trace.json',
     'b8a9e139d85bd7cc116ea3d6ca94f655e41ec7ae67c15f7686e057ca0706eb9b'),
    ('tools/monkey_campaign/contributions/MAT2-G07/falsifier_receipt.json',
     '3f23c828de4845d175c5c92ef8d921768596997d80f0b970ec1f147ab77fe1cc'),
    ('tools/monkey_campaign/contributions/MAT2-G01/run_feasibility.py',
     '2926527383cfe8ea425bb9251844e28c9a0e0479566f472fb5d2b77ae68b98d3'),
    ('tools/monkey_campaign/contributions/MAT2-G01/test_g01_checks.py',
     '4ae01f5f5d07f6bf898f8f04988636797a944a39fb00d21f85974f0a78b229b9'),
    ('tools/monkey_campaign/contributions/MAT2-G01/feasibility_receipt.json',
     '4061d8ec604ddea5dfbdf605f0244874129a69a88d771d4f593c7a927c16be42'),
    ('tools/monkey_campaign/contributions/MAT2-F05/implementation.py',
     'd07acb20f4e0a4e813afc8783fff4098eae531f0c808ac6e6e67242a3342d529'),
    ('tools/monkey_campaign/contributions/MAT2-F05/report.md',
     '0a640c131f067241d3d20f595bd825e2e4319102cc2d200ac04805f702c6ba6d'),
    ('tools/monkey_campaign/visual_capture.py',
     '5ee55d5ab52beb05ffc33e9b66858f94b706cb22c290786db4a79ab344a4ff05'),
    ('tools/monkey_campaign/visual_gate.py',
     '13cf07f47fc73f0c7fa9b5208752f6afadbdcfc66cf30b83457d756d2bc6c8c3'),
)

# (repo-relative path, sha256) resolved from the shared repository WORKING
# TREE (never the base commit; declared provenance): visual_gate imports the
# campaign hashing helper, which is not present at the base commit. The
# G05/G06 heritage convention, carried verbatim.
WORKTREE_PINS = (
    ('tools/monkey_campaign/integrity.py',
     'c3ff77401c1abb5ca657afeee59fb95bac739ebef2cfd688f174b4f97caf82b2'),
)

# The regression closure (prereg section 11 + section 9): the upstream
# suites re-run UNMODIFIED. These card dirs are extracted WHOLESALE at the
# pinned base commit (git blob addresses make the extraction exactly the
# base content; the pinned files among them carry their explicit sha256
# assertions above). F05 is data-bound, not wholesale: its harness
# materializes host stores outside package scope (prereg section 11).
WHOLESALE_DIRS = (
    'tools/monkey_campaign/contributions/MAT2-M01',
    'tools/monkey_campaign/contributions/MAT2-M02',
    'tools/monkey_campaign/contributions/MAT2-M04',
    'tools/monkey_campaign/contributions/MAT2-M06',
    'tools/monkey_campaign/contributions/MAT2-G04',
    'tools/monkey_campaign/contributions/MAT2-G05',
    'tools/monkey_campaign/contributions/MAT2-G06',
    'tools/monkey_campaign/contributions/MAT2-G07',
    'tools/monkey_campaign/contributions/MAT2-G01',
)

HOST_PINS = (
    ('E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G01/numerical/'
     'feasibility_receipt.json',
     '4061d8ec604ddea5dfbdf605f0244874129a69a88d771d4f593c7a927c16be42'),
    ('E:/ChimeraWork/research-data/20260929/benchmark-grasp/'
     'GRASP_BENCHMARK.md',
     'd936cebe38b1416dfc417db727ea81396eb8eb9217efed3f05b344db17f71610'),
    ('E:/ChimeraWork/monkey-coordination/g04-friction/FRICTION_SOURCES.md',
     '336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b'),
    ('E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G04/report/'
     'REPORT.md',
     'dfca5b5556efe018ca09be4577bf6fbb5df38bb5c9ebc33d15bd18646ba349c8'),
    ('E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G05/report/'
     'REPORT.md',
     '1e5fcc7f81b5bd7b0ae3b460c72d5ed190510f66db4793c6b2e99756da8c8524'),
    ('E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G06/report/'
     'REPORT.md',
     '2e4343191591322dca4667e428c09d1dc8dcae39c8a90a53cb5298d90ab2f206'),
)


def _repo_and_base():
    repo = os.environ.get('CHIMERA_SOURCE_REPO', DEFAULT_REPO)
    base = os.environ.get('CHIMERA_BASE_SHA', DEFAULT_BASE)
    return repo, base


def _blob(repo, base, rel):
    proc = subprocess.run(['git', '-c', 'safe.directory=' + repo, '-C', repo,
                           'cat-file', 'blob', base + ':' + rel],
                          capture_output=True, timeout=120)
    if proc.returncode != 0:
        raise ValueError('dep_blob_missing:%s (%s)'
                         % (rel, proc.stderr.decode(errors='replace')[:200]))
    return proc.stdout


def _blob_by_oid(repo, oid):
    proc = subprocess.run(['git', '-c', 'safe.directory=' + repo, '-C', repo,
                           'cat-file', 'blob', oid],
                          capture_output=True, timeout=300)
    if proc.returncode != 0:
        raise ValueError('dep_blob_missing:oid:%s' % oid[:12])
    return proc.stdout


def _ls_tree(repo, base, path):
    proc = subprocess.run(['git', '-c', 'safe.directory=' + repo, '-C', repo,
                           'ls-tree', '-r', '-z', base, '--', path],
                          capture_output=True, timeout=300)
    if proc.returncode != 0:
        raise ValueError('dep_tree_missing:' + path + ':'
                         + proc.stderr.decode(errors='replace')[:200])
    out = []
    for raw in proc.stdout.split(b'\0'):
        if not raw:
            continue
        meta, name = raw.split(b'\t', 1)
        mode, typ, oid = meta.split()[:3]
        if typ == b'blob' and mode in (b'100644', b'100755'):
            out.append((os.fsdecode(name), oid.decode()))
    return out


def _write_pinned(root, rel, data, want, written):
    got = hashlib.sha256(data).hexdigest()
    if got != want:
        raise ValueError('dep_pin_drift:' + rel + ':' + got)
    target = root / rel.replace('/', os.sep)
    if target.is_file():
        existing = hashlib.sha256(target.read_bytes()).hexdigest()
        if existing == want:
            return
        raise ValueError('dep_pin_drift:on_disk:' + rel + ':' + existing)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    written.append(rel)


def verify_host_pins():
    """Assert the host pin table (prereg section 9). Returns the verified
    pin dict; refusals: input_pin_missing / input_pin_drift."""
    out = {}
    for path, want in HOST_PINS:
        p = pathlib.Path(path)
        if not p.is_file():
            raise ValueError('input_pin_missing:' + path)
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        if got != want:
            raise ValueError('input_pin_drift:' + path + ':' + got)
        out[path] = 'ok'
    return out


def ensure():
    """Extract every pinned dependency at the pinned base commit, assert its
    bytes, and place it at its canonical repo-relative path under the
    package root; then extract the wholesale regression-closure card dirs.
    Idempotent; refusals: dep_pin_missing / dep_pin_drift."""
    repo, base = _repo_and_base()
    # the package root is the run root: this card dir lives at
    # <root>/tools/monkey_campaign/contributions/MAT2-G08, so repo-relative
    # paths resolve from parents[3]
    root = CARD_DIR.parents[3]
    written = []
    for rel, want in DEPS:
        _write_pinned(root, rel, _blob(repo, base, rel), want, written)
    for rel, want in WORKTREE_PINS:
        src = pathlib.Path(repo) / rel.replace('/', os.sep)
        if not src.is_file():
            raise ValueError('dep_pin_missing:worktree:' + rel)
        _write_pinned(root, rel, src.read_bytes(), want, written)
    wholesale = 0
    pinned = {rel for rel, _ in DEPS} | {rel for rel, _ in WORKTREE_PINS}
    for d in WHOLESALE_DIRS:
        for rel, oid in _ls_tree(repo, base, d):
            if rel in pinned:
                continue            # already asserted and written above
            target = root / rel.replace('/', os.sep)
            if target.is_file():
                wholesale += 1
                continue
            data = _blob_by_oid(repo, oid)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            wholesale += 1
    return {'schema': 'chimera.g08_deps.v1', 'base': base, 'repo': repo,
            'prereg_commit': PREREG_COMMIT, 'extracted': written,
            'pinned_count': len(DEPS) + len(WORKTREE_PINS),
            'wholesale_files': wholesale}


if __name__ == '__main__':
    import json
    print(json.dumps(ensure(), indent=1))
