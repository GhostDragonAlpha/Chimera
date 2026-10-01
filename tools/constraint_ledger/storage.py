"""L8: SHARED IMMUTABLE STORAGE AND PRIVATE EXECUTION (lane agent/cl-L8-shared-20260921,
pinned to the L0 interface baseline 7181b8ce). New module; touches no existing file.

The operator's demand made concrete: N concurrent jobs against ONE read-only source
snapshot with ZERO source-tree clones. Five pieces, each enforcing by construction:

  SharedSourceStore   one canonical sparse clone = the shared object store. Per-job
                      source views are `git worktree add` sparse checkouts over THAT
                      store -- objects are paid once, bytes/job = working tree only.
                      The view is SEALED read-only (OS 0o444 on every file; POSIX
                      dirs 0o555 so even creation is refused) and the class exposes
                      no write path at all. On Windows, creation of NEW files by a
                      foreign process is not preventable via attrs -- it is DETECTED:
                      every job re-hashes the whole view before/after its run and
                      raises on any difference.                    (F-SOURCE-CLONE,
                                                                      F-CROSS-RUN-WRITE)
  JobWorkspace        a job's PRIVATE writable roots: build/, generated/, trace/,
                      temp/. resolve() refuses any path escaping the root.
                      Outputs are sealed read-only on completion.
                                                                      (F-CROSS-RUN-WRITE)
  BuildCache          content-addressed artifact cache. key = sha256 over canonical
                      JSON of {schema, input content hashes, sorted flags,
                      toolchain digest}. Publish = tmp staging file (same volume)
                      -> fsync -> RE-READ digest verify -> os.replace (atomic
                      same-volume rename) -> fsync of the shard dir where the OS
                      allows it. get() verifies the envelope digest and REFUSES
                      (miss + refusal event, never partial bytes) on any defect.
                                                              (F-CACHE-COLLISION,
                                                              F-PARTIAL-PUBLISH)
  run_build_job       one REAL engine build (g++ compile+link of the constraint-ledger
                      trace harness against the checked-out engine headers) inside a
                      view + workspace, publishing into the cache.
  run_concurrent_wave the harness: N jobs truly simultaneous, a disk-footprint
                      sampler, and the byte census (shared store vs clones).

Prereg: tools/science_funnel/validation/cl_L8_20260921/prereg.json (banked before
any run, incl. the measured PE-timestamp nondeterminism of linked exes on this
toolchain and the .o-projection consequence).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------------
# digests / canonical json
# --------------------------------------------------------------------------

ENVELOPE_MAGIC = b"CLC1"
CACHE_SUFFIX = ".clcache"
TMP_PREFIX = ".tmp-"
PRIVATE = 'private:'          # input-key prefix for job-private (generated) files


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(obj) -> str:
    """The one serialization used for every key: sorted keys, no whitespace,
    ASCII. Two requests are the SAME request iff this string is equal."""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def toolchain_digest(compiler: str = 'g++') -> tuple[str, dict]:
    """Digest of the actual toolchain (Rule 1: derived, not chosen): sha256 over
    the compiler's own version banner + target triple."""
    ver = subprocess.run([compiler, '--version'], capture_output=True, text=True, check=True).stdout
    target = subprocess.run([compiler, '-dumpmachine'], capture_output=True, text=True, check=True).stdout.strip()
    info = {'compiler': compiler, 'version_banner': ver.strip(), 'target': target}
    return sha256_bytes(canonical_json(info).encode()), info


def cache_key(inputs: dict[str, str], flags: list[str], toolchain: str) -> str:
    """THE CACHE-KEY SCHEMA: sha256(canonical_json({
        schema: 'cl-cache-key/1',
        inputs: {repo-rel-path or 'private:<rel>': content_sha256},  # input hashes
        flags:  sorted list of flag strings,                         # build flags
        toolchain: <toolchain digest>,                               # toolchain digest
    })).
    Distinct semantics (input bytes, flags, or toolchain) => distinct canonical
    JSON => distinct key. Equality requires identical semantics or a sha256
    collision. (F-CACHE-COLLISION)"""
    payload = {
        'schema': 'cl-cache-key/1',
        'inputs': dict(sorted(inputs.items())),
        'flags': sorted(flags),
        'toolchain': toolchain,
    }
    return sha256_bytes(canonical_json(payload).encode())


# --------------------------------------------------------------------------
# shared immutable source: one object store, many sealed sparse views
# --------------------------------------------------------------------------

SPARSE_LANES = ['/*', '!/docs/', '!/Saved/']   # the wave lanes' layout, nothing else


def _git(repo: Path, *args: str, check: bool = True) -> str:
    r = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed ({r.returncode}): {r.stderr.strip()}")
    return r.stdout


@dataclass
class SourceView:
    """A per-job sparse READ-ONLY checkout over the shared object store.

    Construction-level sealing: (1) the class has no write method -- harness
    code cannot express a source mutation; (2) every file is OS read-only
    (0o444 / FILE_ATTRIBUTE_READONLY), so even foreign code that guesses a path
    gets PermissionError (POSIX dirs are 0o555: even CREATION is refused);
    (3) on Windows new-file creation by a foreign process is not preventable
    via attributes -- it is DETECTED: integrity_map() re-hashes the working
    tree so the before/after comparison inside every real job proves zero
    mutation under full concurrency."""

    root: Path
    pin: str
    _sealed: bool = False

    def seal(self) -> int:
        """Make every file in the view read-only. Returns file count sealed."""
        n = 0
        for dirpath, _dirnames, filenames in os.walk(self.root):
            for fn in filenames:
                p = Path(dirpath) / fn
                if not p.is_symlink():
                    os.chmod(p, 0o444)
                    n += 1
        if os.name != 'nt':                      # POSIX: also deny file creation
            for dirpath, _d, _f in os.walk(self.root, topdown=False):
                os.chmod(dirpath, 0o555)
        self._sealed = True
        return n

    def unseal(self) -> None:
        for dirpath, _dirnames, filenames in os.walk(self.root):
            for fn in filenames:
                p = Path(dirpath) / fn
                if not p.is_symlink():
                    try:
                        os.chmod(p, 0o644)
                    except PermissionError:
                        pass
        if os.name != 'nt':
            for dirpath, _d, _f in os.walk(self.root, topdown=True):
                os.chmod(dirpath, 0o755)
        self._sealed = False

    def integrity_map(self) -> dict[str, str]:
        """path -> sha256 of working-tree bytes, for EVERY file in the view."""
        out: dict[str, str] = {}
        base = str(self.root)
        for dirpath, _dirnames, filenames in os.walk(base):
            for fn in filenames:
                p = Path(dirpath) / fn
                rel = str(p.relative_to(base)).replace('\\', '/')
                out[rel] = sha256_file(p)
        return out

    def disk_bytes(self) -> int:
        return tree_bytes(self.root)


class SharedSourceStore:
    """The ONE canonical clone; materializes sealed sparse worktrees over it.

    git worktrees share the parent's .git/objects (the per-view .git is a
    pointer FILE, not a copy): the object store is paid exactly once no matter
    how many jobs run. (F-SOURCE-CLONE)"""

    def __init__(self, canonical: Path, views_root: Path, pin: str):
        self.canonical = Path(canonical)
        self.views_root = Path(views_root)
        self.views_root.mkdir(parents=True, exist_ok=True)
        self.pin = pin
        if not _git(self.canonical, 'rev-parse', '--is-inside-work-tree').strip():
            raise ValueError(f"{self.canonical} is not a git repository")

    def object_store_bytes(self) -> int:
        return tree_bytes(self.canonical / '.git' / 'objects')

    def materialize_view(self, job_id: str, retries: int = 3) -> SourceView:
        """A sealed sparse worktree for ONE job. git's own locking serializes
        the short admin phase; brief contention is retried (mechanics, not
        measurement). The build phase afterwards is fully concurrent."""
        path = self.views_root / job_id
        if path.exists():
            raise ValueError(f"view {job_id} already exists")
        last_err: Exception | None = None
        for attempt in range(retries):
            try:
                _git(self.canonical, 'worktree', 'add', '--no-checkout', '--detach', str(path), self.pin)
                _git(path, 'sparse-checkout', 'init', '--no-cone')
                _git(path, 'sparse-checkout', 'set', *SPARSE_LANES)
                _git(path, 'checkout', '-f', '--detach', self.pin)   # -f: --no-checkout left an index
                view = SourceView(root=path, pin=self.pin)
                view.seal()
                return view
            except RuntimeError as e:      # likely lock contention; retry
                last_err = e
                time.sleep(0.5 * (attempt + 1))
        raise RuntimeError(f"materialize_view({job_id}) failed after {retries} tries") from last_err

    def census(self) -> dict:
        views = sorted(p for p in self.views_root.iterdir() if p.is_dir()) if self.views_root.exists() else []
        return {
            'object_store_bytes': self.object_store_bytes(),
            'canonical_worktree_bytes': tree_bytes(self.canonical, skip_dot_git=True),
            'views': {v.name: tree_bytes(v) for v in views},
            'n_views': len(views),
        }


# --------------------------------------------------------------------------
# private execution: one writable root per job, escape-proof
# --------------------------------------------------------------------------

WORKSPACE_DIRS = ('build', 'generated', 'trace', 'temp')


class WorkspaceEscape(ValueError):
    pass


class JobWorkspace:
    """A job's PRIVATE writable dirs. Private by construction: every write the
    harness performs goes through resolve(), which refuses anything outside the
    root; the root name is the job id, so no two jobs share a directory."""

    def __init__(self, jobs_root: Path, job_id: str):
        self.job_id = job_id
        self.root = Path(jobs_root) / job_id
        self.root.mkdir(parents=True, exist_ok=True)
        for d in WORKSPACE_DIRS:
            (self.root / d).mkdir(exist_ok=True)

    def resolve(self, rel: str, subdir: str | None = None) -> Path:
        """The ONLY way harness code gets a writable path. Anything that
        resolves outside this job's root raises (F-CROSS-RUN-WRITE)."""
        p = (self.root / subdir / rel) if subdir else (self.root / rel)
        rp = p.resolve()
        rootp = self.root.resolve()
        if rootp != rp and rootp not in rp.parents:
            raise WorkspaceEscape(
                f"{self.job_id}: path {rel!r} escapes private workspace")
        return p

    def seal(self) -> int:
        """Seal completed outputs read-only: a finished job's artifacts can no
        longer be mutated by anyone on this machine."""
        n = 0
        for dirpath, _d, filenames in os.walk(self.root):
            for fn in filenames:
                os.chmod(Path(dirpath) / fn, 0o444)
                n += 1
        return n

    def disk_bytes(self) -> int:
        return tree_bytes(self.root)


# --------------------------------------------------------------------------
# the build cache: content-addressed, atomic publish, digest-verified reads
# --------------------------------------------------------------------------

@dataclass
class CacheEntry:
    key: str
    payload: bytes
    meta: dict


@dataclass
class Refusal:
    key: str
    reason: str
    detail: str
    at_utc: str


class BuildCache:
    """Content-addressed artifact cache with atomic publication.

    Layout:  <root>/<key[:2]>/<key>.clcache      the ONLY readable entry name
             <root>/<key[:2]>/<key>.<rand>       short-lived staging (ignored by get)
             <root>/refusals.jsonl               every refused read (append-only)

    Publish: write WHOLE envelope to a staging file in the SAME shard dir ->
    flush+fsync -> re-read the staging bytes from DISK and verify -> ATOMIC
    os.replace onto the entry name -> fsync the shard dir (where the OS
    permits). A reader therefore sees the old entry, the new complete entry,
    or a miss -- never a torn one. (F-PARTIAL-PUBLISH)

    Envelope: ENVELOPE_MAGIC | u32 meta_len | meta_json | payload. get()
    re-verifies the payload digest on EVERY read; any defect is a refusal
    (miss), never partial bytes."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.refusals: list[Refusal] = []
        self.stats = {'hits': 0, 'misses': 0, 'refusals': 0, 'publishes': 0}

    # -- paths ------------------------------------------------------------
    def _shard(self, key: str) -> Path:
        return self.root / key[:2]

    def entry_path(self, key: str) -> Path:
        return self._shard(key) / (key + CACHE_SUFFIX)

    # -- read -------------------------------------------------------------
    def get(self, key: str) -> CacheEntry | None:
        """Verified read. Any defect -> refusal event + None (miss). The caller
        rebuilds; PARTIAL BYTES ARE NEVER RETURNED. (F-PARTIAL-PUBLISH)

        Windows sharing semantics (measured, banked in the prereg): while a
        publisher's os.replace swaps the entry, a reader can see a transient
        sharing violation on open. The read retries BOUNDED; exhaustion is a
        recorded 'io-contention' refusal (a miss) -- never a partial return."""
        p = self.entry_path(key)
        if not p.exists():
            self.stats['misses'] += 1
            return None
        last_err: OSError | None = None
        for attempt in range(6):
            try:
                raw = p.read_bytes()
                entry = _parse_envelope(raw, key)
                self.stats['hits'] += 1
                return entry
            except _EnvelopeError as e:
                self._refuse(key, e.reason, e.detail)
                return None
            except OSError as e:                     # transient sharing violation
                last_err = e
                time.sleep(0.02 * (attempt + 1))
        self._refuse(key, 'io-contention', f'{type(last_err).__name__}: {last_err}')
        return None

    def _refuse(self, key: str, reason: str, detail: str) -> None:
        self.stats['refusals'] += 1
        ref = Refusal(key=key, reason=reason, detail=detail,
                      at_utc=datetime.now(timezone.utc).isoformat())
        self.refusals.append(ref)
        with open(self.root / 'refusals.jsonl', 'a', encoding='utf-8', newline='\n') as f:
            f.write(canonical_json({'key': key, 'reason': reason,
                                    'detail': detail, 'at_utc': ref.at_utc}) + '\n')

    # -- write --------------------------------------------------------------
    def publish(self, key: str, payload: bytes, meta: dict | None = None) -> Path:
        """ATOMIC publication (F-PARTIAL-PUBLISH):
        1. stage the complete envelope under a non-entry name in the same shard
        2. flush + fsync the staging file
        3. re-read the staged bytes from DISK and verify the digest -- a
           publisher that wrote garbage promotes nothing
        4. os.replace onto the entry name (atomic same-volume rename)
        5. fsync the shard dir where the OS allows, so the rename survives"""
        shard = self._shard(key)
        shard.mkdir(parents=True, exist_ok=True)
        m = dict(meta or {})
        m.update({'schema': 'cl-cache-entry/1', 'key': key,
                  'payload_sha256': sha256_bytes(payload),
                  'payload_len': len(payload),
                  'published_utc': datetime.now(timezone.utc).isoformat(),
                  'publisher': f"pid{os.getpid()}"})
        meta_b = canonical_json(m).encode('utf-8')
        envelope = ENVELOPE_MAGIC + struct.pack('<I', len(meta_b)) + meta_b + payload
        staging = shard / f"{TMP_PREFIX}{key}.{os.getpid()}.{uuid.uuid4().hex[:8]}"
        try:
            with open(staging, 'wb') as f:
                f.write(envelope)
                f.flush()
                os.fsync(f.fileno())
            landed = staging.read_bytes()               # re-read from disk
            if sha256_bytes(landed) != sha256_bytes(envelope):
                raise RuntimeError('staged bytes do not match the envelope')
            final = self.entry_path(key)
            # ATOMIC on same volume. Windows: replace is REFUSED while a reader
            # holds the entry open (measured) -- retry bounded; readers are
            # millisecond-scale. Exhaustion = clean failure, no torn state.
            for attempt in range(8):
                try:
                    os.replace(staging, final)
                    break
                except PermissionError:
                    if attempt == 7:
                        raise
                    time.sleep(0.05 * (attempt + 1))
            self.stats['publishes'] += 1
            _fsync_dir(shard)
            return final
        finally:
            if staging.exists():                        # interrupted publisher
                try:
                    staging.unlink()
                except OSError:
                    pass

    def disk_bytes(self) -> int:
        return tree_bytes(self.root)

    def n_entries(self) -> int:
        return sum(1 for _ in self.root.rglob('*' + CACHE_SUFFIX))


class _EnvelopeError(Exception):
    def __init__(self, reason: str, detail: str):
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


def _parse_envelope(raw: bytes, key: str) -> CacheEntry:
    if len(raw) < 8:
        raise _EnvelopeError('truncated-envelope', f'{len(raw)} bytes, need >= 8')
    if raw[:4] != ENVELOPE_MAGIC:
        raise _EnvelopeError('bad-magic', f'unexpected prefix {raw[:4]!r}')
    (mlen,) = struct.unpack_from('<I', raw, 4)
    if 8 + mlen > len(raw):
        raise _EnvelopeError('truncated-envelope',
                             f'meta declares {mlen} bytes, file has {len(raw)}')
    try:
        meta = json.loads(raw[8:8 + mlen].decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise _EnvelopeError('corrupt-meta', str(e))
    payload = raw[8 + mlen:]
    if meta.get('payload_len') != len(payload):
        raise _EnvelopeError('truncated-payload',
                             f"meta says {meta.get('payload_len')}, got {len(payload)}")
    digest = sha256_bytes(payload)
    if digest != meta.get('payload_sha256'):
        raise _EnvelopeError('digest-mismatch',
                             f"{digest} != {meta.get('payload_sha256')}")
    if meta.get('key') != key:
        raise _EnvelopeError('key-mismatch', f"{meta.get('key')} != {key}")
    return CacheEntry(key=key, payload=payload, meta=meta)


def _fsync_dir(p: Path) -> None:
    if os.name == 'nt':
        return          # Windows: no dir fds; file fsync + os.replace semantics cover us
    fd = os.open(str(p), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


# --------------------------------------------------------------------------
# the REAL build: trace harness against the checked-out engine headers
# --------------------------------------------------------------------------

ENTRY_TU = 'tools/constraint_ledger/trace_harness.cpp'


def _rebase_includes(text: str, view_root: Path) -> str:
    """A private variant TU lives OUTSIDE the view: rebase its relative quoted
    includes onto the view's absolute paths so the compiler reads the SAME
    headers from the job's own sealed view (deeper includes need no rebasing --
    they are relative to their own files, which sit inside the view)."""
    vr = str(view_root).replace('\\', '/').rstrip('/')

    def sub(m: 're.Match[str]') -> str:
        return f'#include "{vr}/{m.group(2)}"'
    return re.sub(r'#include\s+"((?:\.\./)+)([^"]+)"', sub, text)


def dependency_closure(view: SourceView, ws: JobWorkspace | None, entry: str,
                       extra_flags: list[str] | None = None) -> list[str]:
    """The REAL input set: g++'s own dependency list, run over the job's own
    view, normalized to repo-relative paths (files inside the job's private
    workspace become 'private:<rel>' keys). Derived from the compiler, not
    hand-picked (Rule 1). -MM skips system headers: they are covered by the
    toolchain digest instead."""
    r = subprocess.run(['g++', '-std=c++17', '-MM', *(extra_flags or []), entry],
                       cwd=str(view.root), capture_output=True, text=True, check=True)
    vp = Path(view.root).as_posix().rstrip('/') + '/'
    wp = (Path(ws.root).as_posix().rstrip('/') + '/') if ws else None
    deps: set[str] = set()
    for tok in r.stdout.replace('\\\n', ' ').split():
        if not tok.strip() or tok.strip().endswith(':'):
            continue
        # MEASURED: -MM emits equivalent files under NON-canonical path strings
        # (e.g. 'a/../../b/x.hpp' vs 'b/x.hpp'), and which form appears varies
        # with enumeration order under concurrency. Canonicalize before the
        # path becomes part of a key: identical semantics -> identical key.
        t = Path(os.path.normpath(tok)).as_posix()
        if wp and t.startswith(wp):
            t = PRIVATE + t[len(wp):]
        elif t.startswith(vp):
            t = t[len(vp):]
        deps.add(t)
    e = Path(os.path.normpath(entry)).as_posix()
    deps.add((PRIVATE + e[len(wp):]) if (wp and e.startswith(wp)) else e)
    return sorted(deps)


def compile_two_stage(view: SourceView, ws: JobWorkspace, flags: list[str],
                      entry: str) -> dict:
    """Two-stage REAL build inside the job's private dirs: g++ -c (the .o is
    byte-reproducible on this toolchain -- the reproducibility projection) then
    link (the shipped exe; NOT byte-reproducible: PE timestamps, see prereg).
    All outputs land in the job's private build/ dir."""
    obj = ws.resolve('trace_harness.o', 'build')
    exe = ws.resolve('trace_harness.exe', 'build')
    t0 = time.perf_counter()
    r1 = subprocess.run(['g++', '-std=c++17', '-c', *flags, entry, '-o', str(obj)],
                        cwd=str(view.root), capture_output=True, text=True)
    t1 = time.perf_counter()
    if r1.returncode != 0:
        return {'ok': False, 'stage': 'compile', 'stderr': r1.stderr[-4000:]}
    r2 = subprocess.run(['g++', *flags, str(obj), '-o', str(exe)],
                        cwd=str(view.root), capture_output=True, text=True)
    t2 = time.perf_counter()
    if r2.returncode != 0:
        return {'ok': False, 'stage': 'link', 'stderr': r2.stderr[-4000:]}
    return {'ok': True, 'obj': obj, 'exe': exe,
            'compile_s': round(t1 - t0, 3), 'link_s': round(t2 - t1, 3),
            'obj_sha256': sha256_file(obj), 'exe_bytes': exe.stat().st_size}


@dataclass
class JobSpec:
    job_id: str
    flags: list[str] = field(default_factory=lambda: ['-O2'])
    entry: str = ENTRY_TU                          # repo-relative TU inside the view
    variant_content: str | None = None             # if set: compiled from the job's
                                                   # PRIVATE generated/variant.cpp
    read_cache: bool = True
    publish: bool = True
    toolchain: str | None = None


def run_build_job(spec: JobSpec, store: SharedSourceStore, cache: BuildCache,
                  jobs_root: Path, toolchain: str | None = None) -> dict:
    """ONE job, end to end: sealed view -> private workspace -> real g++ build
    (or verified cache hit) -> atomic publish -> sealed outputs. Every number
    the receipt needs is in the returned record."""
    toolchain = toolchain or spec.toolchain or toolchain_digest()[0]
    rec: dict = {'job_id': spec.job_id, 'flags': sorted(spec.flags), 'toolchain': toolchain}

    t0 = time.perf_counter()
    view = store.materialize_view(spec.job_id)
    ws = JobWorkspace(jobs_root, spec.job_id)

    # the TU: repo file, or a PRIVATE variant written into generated/
    entry = spec.entry
    if spec.variant_content is not None:
        vp = ws.resolve('variant.cpp', 'generated')
        vp.write_text(_rebase_includes(spec.variant_content, view.root), encoding='utf-8')
        entry = vp.as_posix()

    rec['view_bytes'] = view.disk_bytes()
    rec['view_integrity_before'] = view.integrity_map()
    rec['view_files'] = len(rec['view_integrity_before'])
    t_view = time.perf_counter()

    # -- construction guard probes: mutation must be IMPOSSIBLE -----------
    probe = probe_seal(view, ws)

    # -- inputs: the compiler's own dependency closure ---------------------
    deps = dependency_closure(view, ws, entry, spec.flags)
    inputs: dict[str, str] = {}
    for rel in deps:
        if rel.startswith(PRIVATE):
            inputs[rel] = sha256_file(ws.root / rel[len(PRIVATE):])
        else:
            inputs[rel] = sha256_file(view.root / rel)
    key = cache_key(inputs, spec.flags, toolchain)
    rec.update({'key': key, 'n_inputs': len(inputs)})

    # -- cache hit or real build -------------------------------------------
    hit = cache.get(key) if spec.read_cache else None
    rec['cache'] = 'hit' if hit else ('miss' if spec.read_cache else 'bypassed')
    if hit:
        artifact = hit.payload
        rec['determinism_digest'] = hit.meta.get('determinism_digest')
    else:
        built = compile_two_stage(view, ws, spec.flags, entry)
        if not built['ok']:
            raise RuntimeError(f"{spec.job_id}: build failed at {built['stage']}\n{built['stderr']}")
        rec['determinism_digest'] = built['obj_sha256']
        rec['compile_s'] = built['compile_s']
        rec['link_s'] = built['link_s']
        artifact = Path(built['exe']).read_bytes()
        ws.resolve('build_log.txt', 'trace').write_text(
            canonical_json({'key': key, 'inputs': inputs, 'flags': sorted(spec.flags),
                            'toolchain': toolchain, 'obj_sha256': built['obj_sha256']}),
            encoding='utf-8')
        if spec.publish:
            cache.publish(key, artifact, meta={
                'determinism_digest': built['obj_sha256'],
                'flags': sorted(spec.flags),
                'n_inputs': len(inputs),
                'toolchain': toolchain,
                'job_id': spec.job_id,
            })
    rec['artifact_sha256'] = sha256_bytes(artifact)
    rec['artifact_bytes'] = len(artifact)
    rec['elapsed_s'] = round(time.perf_counter() - t0, 3)
    rec['view_materialize_s'] = round(t_view - t0, 3)

    # -- verify: source untouched BY THIS JOB, outputs sealed ---------------
    rec['view_integrity_after'] = view.integrity_map()
    before, after = rec['view_integrity_before'], rec['view_integrity_after']
    mutated = sorted([k for k in set(before) | set(after)
                      if before.get(k) != after.get(k)])
    if mutated:
        raise RuntimeError(
            f"F-CROSS-RUN-WRITE: {spec.job_id} mutated its source view: {mutated[:5]}")
    rec['sealed_outputs'] = ws.seal()
    rec['workspace_bytes'] = ws.disk_bytes()
    rec['probe'] = probe
    if not (probe['view_write_refused'] and probe['escape_refused']
            and probe['sealed_output_refused']):
        raise RuntimeError(f"F-CROSS-RUN-WRITE: {spec.job_id} guard probe WROTE: {probe}")
    return rec


def probe_seal(view: SourceView, ws: JobWorkspace) -> dict:
    """The falsifier's live probes, run INSIDE every real job:
    (a) MODIFY an existing sealed source file  -> must raise PermissionError
    (b) path escape through the workspace API  -> must raise WorkspaceEscape
    (c) append to this job's own sealed output -> must raise PermissionError.
    A probe that does NOT raise fires F-CROSS-RUN-WRITE."""
    out = {'view_write_refused': False, 'escape_refused': False, 'sealed_output_refused': False}
    target = view.root / 'tools' / 'constraint_ledger' / 'trace_harness.cpp'
    assert target.exists(), 'probe target missing from the view'
    try:
        with open(target, 'r+', encoding='utf-8'):
            pass                                   # a content-mutation attempt
    except PermissionError:
        out['view_write_refused'] = True
    except OSError:
        out['view_write_refused'] = True           # any OS refusal counts
    try:
        # resolves OUTSIDE the job's root (root/build -> up 3 = above the jobs tree)
        ws.resolve('../../../l8_escape_probe.exe', 'build')
    except WorkspaceEscape:
        out['escape_refused'] = True
    marker = ws.resolve('.sealed_probe', 'build')
    marker.write_bytes(b'probe')
    os.chmod(marker, 0o444)
    try:
        with open(marker, 'ab') as f:
            f.write(b'mutation')
    except PermissionError:
        out['sealed_output_refused'] = True
    finally:
        os.chmod(marker, 0o644)
        marker.unlink()
    return out


# --------------------------------------------------------------------------
# the concurrent wave + measurements
# --------------------------------------------------------------------------

class FootprintSampler:
    """Samples the runs root's total bytes while the wave runs. Peak = max."""

    def __init__(self, root: Path, interval: float = 0.5):
        self.root = Path(root)
        self.interval = interval
        self.peak = 0
        self.samples: list[tuple[float, int]] = []
        self._stop = threading.Event()
        self._t: threading.Thread | None = None

    def start(self) -> None:
        self._t = threading.Thread(target=self._loop, daemon=True)
        self._t.start()

    def _loop(self) -> None:
        while not self._stop.is_set():
            b = tree_bytes(self.root)
            self.samples.append((round(time.perf_counter(), 2), b))
            if b > self.peak:
                self.peak = b
            self._stop.wait(self.interval)

    def stop(self) -> dict:
        self._stop.set()
        if self._t:
            self._t.join(timeout=self.interval * 4)
        return {'peak_bytes': self.peak, 'n_samples': len(self.samples),
                'final_bytes': self.samples[-1][1] if self.samples else 0}


def run_concurrent_wave(specs: list[JobSpec], store: SharedSourceStore,
                        cache: BuildCache, jobs_root: Path,
                        toolchain: str | None = None) -> dict:
    """N jobs TRULY simultaneous (each its own git worktree + real g++ process
    tree), one footprint sampler over everything. Returns per-job records +
    wave measurements."""
    toolchain = toolchain or toolchain_digest()[0]
    sampler = FootprintSampler(store.views_root.parent)
    sampler.start()
    t0 = time.perf_counter()
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=len(specs)) as ex:
        futures = [ex.submit(run_build_job, s, store, cache, jobs_root, toolchain) for s in specs]
        records = [f.result() for f in futures]
    wall = time.perf_counter() - t0
    foot = sampler.stop()
    return {'records': records, 'wall_s': round(wall, 3), 'footprint': foot,
            'cache_stats': dict(cache.stats),
            'sum_job_s': round(sum(r['elapsed_s'] for r in records), 3)}


# --------------------------------------------------------------------------
# byte census: shared store vs per-lane clones (F-SOURCE-CLONE)
# --------------------------------------------------------------------------

def tree_bytes(root: Path, skip_dot_git: bool = False) -> int:
    total = 0
    for dirpath, dirnames, filenames in os.walk(root):
        if skip_dot_git and '.git' in dirnames:
            dirnames.remove('.git')
        for fn in filenames:
            p = Path(dirpath) / fn
            try:
                if not p.is_symlink():
                    total += p.stat().st_size
            except OSError:
                pass
    return total


REMOTE = 'git@github.com-fleetdeploy:GhostDragonAlpha/Chimera.git'
PIN_BRANCH = 'agent/cl-L0-baseline-20260921'


def measure_full_clone(source: str, dest: Path, pin: str,
                       pin_branch: str = PIN_BRANCH, keep: bool = False) -> dict:
    """The per-lane cost the fleet actually paid: a fresh `git clone
    --filter=blob:none --no-checkout` from the canonical remote (a local-path
    filtered clone is NOT this: local upload-pack ignores filters and a
    promisor source dies packing -- measured, see receipt), then fetch the pin
    branch, sparse-set, checkout. Measured for real -- never estimated.
    Removed afterwards unless keep."""
    dest = Path(dest)
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    r = subprocess.run(['git', 'clone', '--filter=blob:none', '--no-checkout',
                        source, str(dest)], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"clone failed: {r.stderr[-2000:]}")
    _git(dest, 'fetch', 'origin', pin_branch)
    _git(dest, 'cat-file', '-t', pin)
    _git(dest, 'sparse-checkout', 'init', '--no-cone')
    _git(dest, 'sparse-checkout', 'set', *SPARSE_LANES)
    _git(dest, 'checkout', '-f', '--detach', pin)
    out = {'clone_source': source,
           'clone_git_dir_bytes': tree_bytes(dest / '.git'),
           'clone_worktree_bytes': tree_bytes(dest, skip_dot_git=True),
           'clone_total_bytes': tree_bytes(dest)}
    if not keep:
        shutil.rmtree(dest, ignore_errors=True)
    return out
