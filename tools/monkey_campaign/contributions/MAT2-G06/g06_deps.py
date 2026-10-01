"""MAT2-G06 pinned-dependency materializer for sealed package runs.

The sealed package carries ONLY this card's write scope
(tools/monkey_campaign/contributions/MAT2-G06). The preregistered upstream
interfaces live in the shared repository's Git object database at the
package's pinned base commit; the runner provisions CHIMERA_SOURCE_REPO and
CHIMERA_BASE_SHA for exactly this resolution. ensure() extracts each pinned
blob byte-exactly, asserts its sha256 against the frozen table (the prereg
section 9 input pins plus the two campaign visual-gate modules), and writes
it into the scratch tree at its canonical repo-relative path. Reading the
object database mutates nothing: no checkout, no index, no branch, no new
objects (cat-file only). Refusals are named codes; nothing is silently
repaired.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
CARD_DIR = HERE                      # .../contributions/MAT2-G06
CONTRIB = HERE.parent                # .../contributions
TOOLS = CONTRIB.parent               # .../tools

DEFAULT_REPO = 'E:/PythonChimera'
DEFAULT_BASE = '39ee4884dbd096259298b4b1bb7e84088acdad7f'  # the published
# MAT2-G06 preregistration commit (parent = fa02f075, the MAT2-G05 merge).

# (repo-relative path, sha256 of the blob bytes). The MAT2-M06 / MAT2-F03 /
# MAT2-G04 / MAT2-G05 rows are the prereg PREREGISTRATION.md section 9 pin
# table verbatim. The two visual-gate rows pin the campaign validator
# modules as they exist at the same prereg base commit (imported by
# make_capture.py; declared here so the extraction is hash-asserted too).
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
    ('tools/monkey_campaign/visual_capture.py',
     '5ee55d5ab52beb05ffc33e9b66858f94b706cb22c290786db4a79ab344a4ff05'),
    ('tools/monkey_campaign/visual_gate.py',
     '13cf07f47fc73f0c7fa9b5208752f6afadbdcfc66cf30b83457d756d2bc6c8c3'),
    # visual_gate imports the campaign hashing helper. It is not present at
    # the prereg base commit (added on master after fa02f075); the bytes are
    # pinned from the shared repository working tree, 2026-10-01, by this
    # card (the G05 legacy-checkout runs used the same module live).
    # Declared in WORKTREE_PINS below.
)

# (repo-relative path, sha256) resolved from the shared repository WORKING
# TREE (never the base commit; declared provenance above).
WORKTREE_PINS = (
    ('tools/monkey_campaign/integrity.py',
     'c3ff77401c1abb5ca657afeee59fb95bac739ebef2cfd688f174b4f97caf82b2'),
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


# The regression closure (prereg section 11): the three upstream suites
# re-run UNMODIFIED, and the M06 suite re-runs the M01/M02/M04 suites and
# consumes its committed receipts/trace. These card dirs are extracted
# WHOLESALE at the same pinned base commit (git blob addresses make the
# extraction exactly the base content; the fourteen prereg-pinned files
# among them carry their explicit sha256 assertions above).
WHOLESALE_DIRS = (
    'tools/monkey_campaign/contributions/MAT2-M01',
    'tools/monkey_campaign/contributions/MAT2-M02',
    'tools/monkey_campaign/contributions/MAT2-M04',
    'tools/monkey_campaign/contributions/MAT2-M06',
    'tools/monkey_campaign/contributions/MAT2-G04',
    'tools/monkey_campaign/contributions/MAT2-G05',
)


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


def ensure():
    """Extract every pinned dependency at the pinned base commit, assert its
    bytes, and place it at its canonical repo-relative path under the
    package root; then extract the wholesale regression-closure card dirs.
    Idempotent; refusals: dep_pin_missing / dep_pin_drift."""
    repo, base = _repo_and_base()
    # the package root is the run root: this card dir lives at
    # <root>/tools/monkey_campaign/contributions/MAT2-G06, so repo-relative
    # paths resolve from parents[3]
    root = CARD_DIR.parents[3]
    written = []
    for rel, want in DEPS:
        data = _blob(repo, base, rel)
        got = hashlib.sha256(data).hexdigest()
        if got != want:
            raise ValueError('dep_pin_drift:' + rel + ':' + got)
        target = root / rel.replace('/', os.sep)
        if target.is_file():
            existing = hashlib.sha256(target.read_bytes()).hexdigest()
            if existing == want:
                continue
            raise ValueError('dep_pin_drift:on_disk:' + rel + ':' + existing)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        written.append(rel)
    for rel, want in WORKTREE_PINS:
        src = pathlib.Path(repo) / rel.replace('/', os.sep)
        if not src.is_file():
            raise ValueError('dep_pin_missing:worktree:' + rel)
        data = src.read_bytes()
        got = hashlib.sha256(data).hexdigest()
        if got != want:
            raise ValueError('dep_pin_drift:' + rel + ':' + got)
        target = root / rel.replace('/', os.sep)
        if target.is_file():
            existing = hashlib.sha256(target.read_bytes()).hexdigest()
            if existing == want:
                continue
            raise ValueError('dep_pin_drift:on_disk:' + rel + ':' + existing)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        written.append(rel)
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
    return {'schema': 'chimera.g06_deps.v1', 'base': base, 'repo': repo,
            'extracted': written, 'pinned_count': len(DEPS),
            'wholesale_files': wholesale}


if __name__ == '__main__':
    import json
    print(json.dumps(ensure(), indent=1))
