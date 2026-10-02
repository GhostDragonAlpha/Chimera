"""Pinned file packages and fixed runner slots. Never creates a Git worktree/clone.

The filesystem is cooperative, not a hostile-code sandbox. Each task explicitly
declares reads/writes; execution happens in runner-owned disposable directories.

Storage control (wk-storage wave, 2026-10-01): a job's declared budget is
reserved before admission against free disk minus aggregate active-lease
reservations; every running job holds a lease whose identity is verified before
cleanup deletes anything; run receipts carry a byte-accounting block (created /
retained / reclaimed); anything preserved indefinitely is recorded in the holds
ledger with owner, reason and next action. Directory policy separates protected
evidence (results/), regenerable input caches (package files/, rebuilt from the
source Git object database at the pinned base) and temporary scratch
(slot-*/scratch); unknown paths are never touched. Budget checks are admission
and polling controls, not OS quotas; RAM is never treated as a cleanup
substitute.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile
import time
import uuid
import runner_resources

PACKAGE_LIMIT = 256 * 1024**2
JOB_LIMIT = 2 * 1024**3
OUTPUT_LIMIT = PACKAGE_LIMIT
RESULTS_LIMIT = 20 * 1024**3
RUNNER = Path('E:/ChimeraWork/task-runner')
JOB_SCHEMA='chimera.runner_job.v1'
LEASE_SCHEMA='chimera.runner_lease.v1'
HOLDS_SCHEMA='chimera.holds_ledger.v1'
BYTES_SCHEMA='chimera.byte_accounting.v1'


class SlotBusy(OSError):pass


def sha(data): return hashlib.sha256(data).hexdigest()


def write_json(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name+'.tmp')
    tmp.write_text(json.dumps(value, indent=2), encoding='utf-8')
    os.replace(tmp, p)


def relpath(s):
    s = str(s).replace('\\', '/')
    if not s or s.startswith('/') or ':' in s or any(x in ('', '.', '..', '.git') for x in s.split('/')):
        raise ValueError('unsafe_relative_path: '+s)
    if any(x.rstrip('. ') != x for x in s.split('/')):
        raise ValueError('ambiguous_windows_path')
    return s


def inside(root, rel):
    root = Path(root).resolve(strict=True)
    p = root/relpath(rel)
    q = p
    while q != root:
        if q.is_symlink() or (hasattr(q, 'is_junction') and q.is_junction()):
            raise ValueError('reparse_entry_refused')
        q = q.parent
    if not p.resolve().is_relative_to(root): raise ValueError('path_escape')
    return p


def git(repo, *args, env=None, data=None):
    p = subprocess.run(['git', '-c', 'safe.directory='+str(repo), '-C', str(repo), *args],
                       input=data, capture_output=True, timeout=120, env=env)
    if p.returncode: raise ValueError('git_failed: '+p.stderr.decode(errors='replace')[-1800:])
    return p.stdout


@contextmanager
def lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as f:
        f.seek(0); f.write(b'0'); f.flush(); f.seek(0)
        if os.name == 'nt':
            import msvcrt
            try:msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:raise SlotBusy(str(path)) from exc
        else:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try: yield
        finally:
            if os.name == 'nt':
                f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)


def inventory(root):
    out = {}
    for base, dirs, files in os.walk(root):
        for name in dirs+files:
            p = Path(base)/name
            if p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()):
                raise ValueError('reparse_entry_refused')
        for name in files:
            p = Path(base)/name
            out[p.relative_to(root).as_posix()] = p.stat().st_size
    return out


def remove_owned(path, parent):
    path = Path(path).absolute(); parent = Path(parent).resolve(strict=True)
    if path.parent != parent or path.name != 'scratch':
        raise ValueError('not_runner_owned_scratch')
    if not path.exists(): return
    inside(parent, path.name)
    # Do not traverse links while deleting; refuse ambiguous trees.
    inventory(path)
    def writable(fn, p, exc): os.chmod(p, 0o700); fn(p)
    shutil.rmtree(path, onerror=writable)
    if path.exists(): raise ValueError('cleanup_failed')


def free_bytes(path):
    """Free space on the volume holding path. Admission input; polled control, not an OS quota."""
    return shutil.disk_usage(str(path)).free


def record_hold(root, kind, owner, reason, next_action, path=''):
    """Holds ledger: anything preserved indefinitely gets a named owner, reason,
    and resolution action. Append-only evidence; nothing is deleted based on it."""
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    entry=dict(date=time.strftime('%Y-%m-%dT%H:%M:%S%z'),kind=kind,owner=owner,
               reason=reason,next_action=next_action,path=str(path))
    with lock(root/'holds.lock'):
        p=root/'holds_ledger.json'
        ledger=json.loads(p.read_text(encoding='utf-8')) if p.exists() else dict(schema=HOLDS_SCHEMA,holds=[])
        if ledger.get('schema')!=HOLDS_SCHEMA:raise ValueError('invalid_holds_ledger_preserved')
        entry['index']=len(ledger['holds']);ledger['holds'].append(entry)
        write_json(p,ledger)
    return entry


def read_holds(root=RUNNER):
    p=Path(root)/'holds_ledger.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else dict(schema=HOLDS_SCHEMA,holds=[])


def classify_runner(root, path):
    """Directory policy for the runner root: protected evidence / temporary
    scratch / runner metadata / unknown. Unknown paths are never touched."""
    root=Path(root).resolve();p=Path(path).resolve()
    try:r=p.relative_to(root)
    except ValueError:return 'outside'
    if not r.parts:return 'runner_root'
    if r.parts[0]=='results':return 'protected_evidence'
    if r.parts[0].startswith('slot-'):
        if len(r.parts)>=2 and r.parts[1]=='scratch':return 'temporary_scratch'
        if len(r.parts)==2 and r.parts[1] in ('job.json','lease.json','slot.lock'):return 'runner_metadata'
        return 'unknown'
    return 'unknown'


def classify_package(package, path):
    """Worker package policy: files/ is a regenerable cache rebuilt from the
    source Git object database at the pinned base; sealed/ is pinned proposal
    history retained until published."""
    package=Path(package).resolve();p=Path(path).resolve()
    try:r=p.relative_to(package)
    except ValueError:return 'outside'
    if not r.parts:return 'package_root'
    if r.parts[0]=='files':return 'regenerable_cache'
    if r.parts[0]=='sealed':return 'pinned_package_history'
    return 'unknown'


def verify_lease(sroot, jid):
    """A running job holds the lease; cleanup may delete scratch only under the
    lease that matches this exact job identity."""
    p=Path(sroot)/'lease.json'
    if not p.exists():raise ValueError('active_lease_missing_preserved')
    d=json.loads(p.read_text(encoding='utf-8'))
    if d.get('schema')!=LEASE_SCHEMA or d.get('job')!=jid:
        raise ValueError('lease_identity_mismatch_preserved')
    return d


def active_reservations(root):
    """Aggregate declared budgets of all leases across slots, including stale
    leases not yet recovered (conservative while a crashed slot is pending)."""
    total=0
    for lease in Path(root).glob('slot-*/lease.json'):
        d=json.loads(lease.read_text(encoding='utf-8'))
        if d.get('schema')!=LEASE_SCHEMA:raise ValueError('invalid_lease_preserved: '+str(lease))
        total+=int(d.get('declared_bytes',0))
    return total


def space_admission(root, incoming):
    """Space reservation before admission: the job's declared budget must fit
    the free space beyond what active leases already reserve. This is an
    admission/polling control, not an OS disk quota; a fast writer can overshoot."""
    free=free_bytes(root);reserved=active_reservations(root)
    return dict(allowed=free>=reserved+incoming,free_bytes=free,reserved_bytes=reserved,
                incoming_bytes=incoming,required_bytes=reserved+incoming)


def create(repo, base, package, owner, task, reads, writes):
    repo = Path(repo).resolve(strict=True); package = Path(package).absolute()
    if package.exists(): raise ValueError('package_already_exists_preserved')
    if not owner or not task: raise ValueError('identity_required')
    prefixes = [relpath(x.rstrip('/')) for x in reads+writes]
    writes = [relpath(x.rstrip('/')) for x in writes]
    if not writes: raise ValueError('write_scope_required')
    base = git(repo, 'rev-parse', '--verify', base+'^{commit}').decode().strip()
    tree = git(repo, 'ls-tree', '-r', '-z', '-l', base)
    selected = {}; total = 0
    for raw in tree.split(b'\0'):
        if not raw: continue
        meta, rawname = raw.split(b'\t', 1); mode, typ, oid, size = meta.split()
        name = relpath(os.fsdecode(rawname))
        if not any(name == p or name.startswith(p+'/') for p in prefixes): continue
        if typ != b'blob' or mode not in (b'100644', b'100755'):
            raise ValueError('symlink_or_submodule_dependency_refused: '+name)
        total += int(size)
        if total > PACKAGE_LIMIT: raise ValueError('package_budget_exceeded_use_external_data_reference')
        selected[name] = {'oid':oid.decode(), 'mode':mode.decode(), 'size':int(size)}
    package.mkdir(parents=True); (package/'files').mkdir()
    m = dict(schema='chimera.file_package.v1', id=uuid.uuid4().hex, owner=owner, task=task,
             source=str(repo), base=base, reads=prefixes, writes=writes, inputs=selected)
    try:
        for name, rec in selected.items():
            data = git(repo, 'cat-file', 'blob', rec['oid'])
            rec['sha256'] = sha(data)
            p = inside(package/'files', name); p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
        write_json(package/'package.json', m)
    except Exception:
        write_json(package/'PROVISION_FAILED.json', {'state':'INCOMPLETE_NO_AUTOMATIC_REUSE'})
        raise
    return dict(state='PREPARED', package=str(package), working_directory=str(package/'files'),
                base=base, file_count=len(selected), bytes=total, git_checkout_created=False)


def permitted(name, scopes): return any(name == p or name.startswith(p+'/') for p in scopes)


def seal(package):
    package = Path(package).resolve(strict=True)
    with lock(package/'package.lock'):
        if sum(inventory(package).values()) > 1024**3:
            raise ValueError('package_history_budget_exceeded_preserve_and_publish')
        m = json.loads((package/'package.json').read_text())
        files = package/'files'; sizes = inventory(files)
        if sum(sizes.values()) > PACKAGE_LIMIT: raise ValueError('package_budget_exceeded')
        contents = {n:inside(files,n).read_bytes() for n in sizes}
        changes = []
        for name in sorted(set(m['inputs']) | set(contents)):
            old = m['inputs'].get(name)
            current = sha(contents[name]) if name in contents else None
            if current == (old['sha256'] if old else None): continue
            if not permitted(name, m['writes']): raise ValueError('write_outside_scope: '+name)
            changes.append(name)
        # A private index and object directory build the patch without modifying
        # the canonical checkout, index, branch, or object store.
        repo = Path(m['source'])
        objects = git(repo, 'rev-parse', '--path-format=absolute', '--git-path', 'objects').decode().strip()
        with tempfile.TemporaryDirectory(prefix='chimera-patch-index-') as tmp:
            t = Path(tmp); (t/'objects').mkdir()
            env = dict(os.environ, GIT_INDEX_FILE=str(t/'index'),
                       GIT_OBJECT_DIRECTORY=str(t/'objects'), GIT_ALTERNATE_OBJECT_DIRECTORIES=objects)
            git(repo, 'read-tree', m['base'], env=env)
            for name in changes:
                if name not in contents:
                    git(repo, 'update-index', '--force-remove', '--', name, env=env)
                else:
                    oid = git(repo, 'hash-object', '-w', '--stdin', '--no-filters', env=env, data=contents[name]).decode().strip()
                    mode = m['inputs'].get(name, {}).get('mode', '100644')
                    git(repo, 'update-index', '--add', '--cacheinfo', mode, oid, name, env=env)
            patch = git(repo, 'diff', '--cached', '--binary', '--full-index', '--no-ext-diff',
                        '--no-textconv', m['base'], '--', env=env)
        sid = uuid.uuid4().hex
        dest = package/'sealed'/sid; (dest/'files').mkdir(parents=True)
        for name, data in contents.items():
            p = inside(dest/'files', name); p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
        (dest/'change.patch').write_bytes(patch)
        receipt = dict(schema='chimera.sealed_package.v1', package=m, changes=changes,
                       files={n:sha(b) for n,b in contents.items()}, patch_sha256=sha(patch),
                       created_at=time.time())
        write_json(dest/'manifest.json', receipt)
        return {'sealed':str(dest), 'manifest_sha256':sha((dest/'manifest.json').read_bytes()),
                'patch':str(dest/'change.patch'), 'changed_files':changes}


def verify(sealed):
    sealed = Path(sealed).resolve(strict=True)
    m = json.loads((sealed/'manifest.json').read_text())
    actual = inventory(sealed/'files')
    if set(actual) != set(m['files']): raise ValueError('sealed_file_set_changed')
    for name, h in m['files'].items():
        if sha(inside(sealed/'files',name).read_bytes()) != h: raise ValueError('sealed_file_changed: '+name)
    if sha((sealed/'change.patch').read_bytes()) != m['patch_sha256']: raise ValueError('patch_changed')
    return m


class ProcessTree:
    """A Windows Job owns all child processes before the command can execute."""
    def __init__(self, command, cwd, output, env, job_name=None, memory_limit_bytes=None):
        self.job = None
        if os.name == 'nt':
            import ctypes as c
            from ctypes import wintypes as w
            class Basic(c.Structure):
                _fields_=[('PerProcessUserTimeLimit',c.c_longlong),('PerJobUserTimeLimit',c.c_longlong),
                          ('LimitFlags',w.DWORD),('MinimumWorkingSetSize',c.c_size_t),('MaximumWorkingSetSize',c.c_size_t),
                          ('ActiveProcessLimit',w.DWORD),('Affinity',c.c_size_t),('PriorityClass',w.DWORD),('SchedulingClass',w.DWORD)]
            class IO(c.Structure): _fields_=[(x,c.c_ulonglong) for x in ('ReadOperationCount','WriteOperationCount','OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount')]
            class Extended(c.Structure):
                _fields_=[('BasicLimitInformation',Basic),('IoInfo',IO),('ProcessMemoryLimit',c.c_size_t),
                          ('JobMemoryLimit',c.c_size_t),('PeakProcessMemoryUsed',c.c_size_t),('PeakJobMemoryUsed',c.c_size_t)]
            k=c.WinDLL('kernel32',use_last_error=True); self.k=k
            k.CreateJobObjectW.argtypes=[c.c_void_p,w.LPCWSTR];k.CreateJobObjectW.restype=w.HANDLE
            k.SetInformationJobObject.argtypes=[w.HANDLE,c.c_int,c.c_void_p,w.DWORD]
            k.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE]
            k.TerminateJobObject.argtypes=[w.HANDLE,w.UINT]; k.CloseHandle.argtypes=[w.HANDLE]
            self.job=k.CreateJobObjectW(None,job_name)
            info=Extended();info.BasicLimitInformation.LimitFlags=0x2000
            if memory_limit_bytes:
                info.BasicLimitInformation.LimitFlags |= 0x200
                info.JobMemoryLimit=memory_limit_bytes
            if not self.job or not k.SetInformationJobObject(self.job,9,c.byref(info),c.sizeof(info)):
                if self.job:k.CloseHandle(self.job);self.job=None
                raise OSError('job_object_setup_failed')
            try:
                self.p=subprocess.Popen(command,cwd=cwd,stdout=output,stderr=subprocess.STDOUT,env=env,
                                        creationflags=0x4|0x08000000)
                if not k.AssignProcessToJobObject(self.job,w.HANDLE(int(self.p._handle))):
                    self.p.kill();self.p.wait();raise OSError('process_ownership_failed')
                nt=c.WinDLL('ntdll');nt.NtResumeProcess.argtypes=[w.HANDLE];nt.NtResumeProcess.restype=c.c_long
                if nt.NtResumeProcess(w.HANDLE(int(self.p._handle))) != 0:
                    self.close();raise OSError('process_resume_failed')
            except Exception:
                if self.job: k.CloseHandle(self.job);self.job=None
                raise
        else:
            self.p=subprocess.Popen(command,cwd=cwd,stdout=output,stderr=subprocess.STDOUT,env=env,start_new_session=True)

    def close(self):
        if os.name == 'nt' and self.job:
            import ctypes as c
            from ctypes import wintypes as w
            self.k.TerminateJobObject(self.job,1)
            self.p.wait(timeout=15)
            class Accounting(c.Structure):
                _fields_=[('u',c.c_longlong),('k',c.c_longlong),('pu',c.c_longlong),('pk',c.c_longlong),
                          ('faults',w.DWORD),('total',w.DWORD),('active',w.DWORD),('terminated',w.DWORD)]
            self.k.QueryInformationJobObject.argtypes=[w.HANDLE,c.c_int,c.c_void_p,w.DWORD,c.c_void_p]
            until=time.monotonic()+15
            while True:
                a=Accounting()
                if not self.k.QueryInformationJobObject(self.job,1,c.byref(a),c.sizeof(a),None):
                    raise OSError('process_drain_unverifiable')
                if a.active==0:break
                if time.monotonic()>until:raise TimeoutError('process_tree_not_drained')
                time.sleep(.05)
            self.k.CloseHandle(self.job);self.job=None
        elif os.name != 'nt':
            import signal
            try: os.killpg(self.p.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            self.p.wait(timeout=15)


def recover_locked(root, sroot):
    """Recover only our recorded job, with slot lock held and child ownership checked.
    Anything that cannot be provably owned is preserved and recorded as a hold."""
    lease=sroot/'lease.json';stale=None
    if lease.exists():
        stale=json.loads(lease.read_text(encoding='utf-8'))
        if stale.get('schema')!=LEASE_SCHEMA:
            record_hold(root,'lease_preserved','unidentified (invalid slot lease)','invalid_stale_lease_schema',
                        'operator inspection; runner refuses to discard an unidentifiable lease',lease)
            raise ValueError('invalid_stale_lease_preserved')
    scratch=sroot/'scratch'
    if not scratch.exists():
        if stale is not None:
            marker=sroot/'job.json'
            if marker.exists() and json.loads(marker.read_text()).get('job')==stale.get('job'):
                lease.unlink()  # crashed writer left a lease but created no scratch
            else:
                record_hold(root,'lease_preserved','unidentified (lease/job identity mismatch)','stale_lease_identity_mismatch',
                            'operator inspection; lease kept until its owner is identified',lease)
                raise ValueError('stale_lease_identity_mismatch_preserved')
        return
    marker=sroot/'job.json'
    if not marker.exists():
        record_hold(root,'scratch_preserved','unidentified (scratch without job identity)','scratch_without_job_identity',
                    'owner identification then explicit human decision; runner never guesses data is disposable',scratch)
        raise ValueError('slot_recovery_required_existing_scratch_preserved')
    m=json.loads(marker.read_text())
    jid=m.get('job','')
    if len(jid)!=32 or any(c not in '0123456789abcdef' for c in jid):
        record_hold(root,'scratch_preserved','unidentified (invalid job identity)','invalid_recovery_identity',
                    'owner identification then explicit human decision; scratch preserved',scratch)
        raise ValueError('invalid_recovery_identity')
    result=inside(root,'results/'+jid)
    if str(result)!=m.get('result') or m.get('schema')!=JOB_SCHEMA:
        record_hold(root,'scratch_preserved','unidentified (job marker does not own its result)','unowned_recovery',
                    'operator inspection; result-pointer mismatch preserved',scratch)
        raise ValueError('unowned_recovery_preserved')
    if not (scratch/'.chimera-runner-id').is_file() or (scratch/'.chimera-runner-id').read_text()!=jid:
        record_hold(root,'scratch_preserved','job '+jid,'recovery_scratch_identity_mismatch',
                    'operator inspection; scratch identity does not match the recorded job',scratch)
        raise ValueError('recovery_scratch_identity_mismatch_preserved')
    if os.name != 'nt':raise ValueError('crash_recovery_process_check_only_implemented_on_windows')
    import ctypes as c
    from ctypes import wintypes as w
    k=c.WinDLL('kernel32',use_last_error=True)
    k.OpenJobObjectW.argtypes=[w.DWORD,w.BOOL,w.LPCWSTR];k.OpenJobObjectW.restype=w.HANDLE
    k.TerminateJobObject.argtypes=[w.HANDLE,w.UINT];k.CloseHandle.argtypes=[w.HANDLE]
    k.QueryInformationJobObject.argtypes=[w.HANDLE,c.c_int,c.c_void_p,w.DWORD,c.c_void_p]
    h=k.OpenJobObjectW(0x0004|0x0008,False,'Local\\ChimeraTask-'+jid)
    if h:
        try:
            if not k.TerminateJobObject(h,1):raise OSError('recovery_process_termination_failed')
            class Accounting(c.Structure):
                _fields_=[('u',c.c_longlong),('k',c.c_longlong),('pu',c.c_longlong),('pk',c.c_longlong),
                          ('faults',w.DWORD),('total',w.DWORD),('active',w.DWORD),('terminated',w.DWORD)]
            until=time.monotonic()+15
            while True:
                a=Accounting()
                if not k.QueryInformationJobObject(h,1,c.byref(a),c.sizeof(a),None):raise OSError('recovery_process_check_failed')
                if not a.active:break
                if time.monotonic()>until:raise TimeoutError('recovery_process_drain_timeout')
                time.sleep(.05)
        finally:k.CloseHandle(h)
    elif c.get_last_error()!=2:
        raise OSError('recovery_job_lookup_failed')
    pre_total=sum(inventory(scratch).values())
    result.mkdir(parents=True,exist_ok=True)
    artifacts={};total=0;log_bytes=0
    for name in m.get('keep',[]):
        name=relpath(name);p=inside(scratch,name)
        if not p.is_file():continue
        total+=p.stat().st_size
        if total>PACKAGE_LIMIT:raise ValueError('recovery_output_budget_exceeded_preserved')
        dest=result/'artifacts'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(p,dest);hsh=sha(p.read_bytes())
        if sha(dest.read_bytes())!=hsh:raise ValueError('recovery_copy_verification_failed')
        artifacts[name]=hsh
    log=inside(scratch,'runner.log')
    if log.is_file():
        with log.open('rb') as f:f.seek(max(0,log.stat().st_size-1024**2));data=f.read()
        (result/'runner.log').write_bytes(data);artifacts['runner.log']=sha(data);log_bytes=len(data)
    receipt=dict(job=jid,state='INTERRUPTED_RECOVERED',artifacts=artifacts,cleanup_verified=False,
                 bytes={'schema':BYTES_SCHEMA,'units':'bytes','scratch_peak_bytes':pre_total,
                        'scratch_at_cleanup_bytes':pre_total,'retained_bytes':total+log_bytes,
                        'reclaimed_bytes':pre_total-total-log_bytes,
                        'declared_budget_bytes':(stale or {}).get('declared_bytes')})
    write_json(result/'recovery.json',receipt)
    remove_owned(scratch,sroot)
    if stale is not None:lease.unlink()  # stale lease consumed together with its scratch
    receipt['cleanup_verified']=True;write_json(result/'recovery.json',receipt)


def run(sealed, command, keep=(), timeout=600, root=RUNNER, slot=None, job_limit=JOB_LIMIT):
    p=runner_resources.profile()
    job_limit=int(job_limit)
    if slot is not None:
        return _run_slot(sealed,command,keep,timeout,root,slot,job_limit,p)
    for candidate in range(p['cpu_slots']):
        try:return _run_slot(sealed,command,keep,timeout,root,candidate,job_limit,p)
        except SlotBusy:continue
    return {'state':'BUSY','reason':'all_cpu_slots_in_use','retry_after_seconds':10,'cpu_slots':p['cpu_slots']}


def _run_slot(sealed, command, keep, timeout, root, slot, job_limit, resources):
    if type(slot) is not int or slot not in range(resources['cpu_slots']): raise ValueError('slot_outside_configured_pool')
    if timeout<=0 or not command: raise ValueError('command_and_positive_timeout_required')
    sealed=Path(sealed).resolve(strict=True);m=verify(sealed)
    root=Path(root).absolute();root.mkdir(parents=True,exist_ok=True)
    if root.resolve()!=root:raise ValueError('runner_root_reparse_refused')
    sroot=inside(root,'slot-'+str(slot));sroot.mkdir(exist_ok=True)
    jid=uuid.uuid4().hex; result=root/'results'/jid
    with lock(sroot/'slot.lock'):
        scratch=sroot/'scratch'
        recover_locked(root,sroot)
        memory=runner_resources.admission(resources)
        if not memory['allowed']:
            return {'state':'BUSY','reason':'memory_reserve','retry_after_seconds':10,'memory':memory}
        # A1/A2: space reservation BEFORE admission. The job is admitted only if
        # its declared budget fits free disk beyond aggregate active reservations.
        space=space_admission(root,job_limit+OUTPUT_LIMIT)
        if not space['allowed']:
            return {'state':'BUSY','reason':'disk_space_reserve','retry_after_seconds':10,'space':space}
        if sum(inventory(root/'results').values()) > RESULTS_LIMIT:
            record_hold(root,'results_preserved','campaign results store','retained_results_budget_exceeded',
                        'anchor required evidence via anchor.py, then retire results; admission refused meanwhile',root/'results')
            raise ValueError('retained_results_budget_exceeded_anchor_and_retire_results')
        scratch.mkdir();result.mkdir(parents=True)
        receipt={'job':jid,'state':'STARTING','sealed_manifest_sha256':sha((sealed/'manifest.json').read_bytes()),
                 'base':m['package']['base'],'command':command,'slot':slot,'cleanup_verified':False,
                 'declared_budget_bytes':job_limit}
        receipt['resource_profile']=resources
        receipt['memory_admission']=memory
        receipt['space_admission']=space
        receipt['artifact_store_class']=classify_runner(root,result)
        tree=None;drained=True;preserved=False;peak=0
        write_json(sroot/'job.json',dict(schema=JOB_SCHEMA,job=jid,sealed=str(sealed),keep=list(keep),result=str(result)))
        # A3: the running job holds a lease; cleanup verifies lease identity first.
        write_json(sroot/'lease.json',dict(schema=LEASE_SCHEMA,job=jid,pid=os.getpid(),slot=slot,started_at=time.time(),
                   declared_bytes=job_limit,retained_cap_bytes=OUTPUT_LIMIT,
                   sealed_manifest_sha256=receipt['sealed_manifest_sha256'],result=str(result)))
        (scratch/'.chimera-runner-id').write_text(jid)
        try:
            shutil.copytree(sealed/'files',scratch,dirs_exist_ok=True)
            (scratch/'outputs').mkdir(exist_ok=True);(scratch/'tmp').mkdir(exist_ok=True)
            env=dict(os.environ,TMP=str(scratch/'tmp'),TEMP=str(scratch/'tmp'),TMPDIR=str(scratch/'tmp'),
                     PYTHONDONTWRITEBYTECODE='1',CHIMERA_OUTPUT_DIR=str(scratch/'outputs'),
                     CHIMERA_BASE_SHA=m['package']['base'],CHIMERA_SOURCE_REPO=m['package']['source'])
            env.update(runner_resources.thread_environment(resources))
            with (scratch/'runner.log').open('wb') as log:
                tree=ProcessTree(command,scratch,log,env,job_name='Local\\ChimeraTask-'+jid,
                                 memory_limit_bytes=resources['job_memory_gib']*1024**3);drained=False
                start=time.monotonic()
                while tree.p.poll() is None:
                    if time.monotonic()-start>timeout: raise TimeoutError('job_timeout')
                    sz=sum(inventory(scratch).values());peak=max(peak,sz)
                    if sz>job_limit:raise ValueError('job_storage_budget_exceeded')
                    time.sleep(.1)
                receipt['exit_code']=tree.p.returncode
                tree.close();drained=True
            receipt['state']='PASSED' if receipt['exit_code']==0 else 'FAILED'
        except Exception as exc:
            receipt.update(state='FAILED',error=str(exc))
        finally:
            if tree and not drained:
                try:tree.close();drained=True
                except Exception as exc:receipt['process_drain_error']=str(exc)
            if drained:
                try:
                    artifacts={};retained=0
                    # Always retain a bounded diagnostic tail, even after timeout.
                    log=scratch/'runner.log'
                    if log.exists():
                        with log.open('rb') as f:
                            f.seek(max(0,log.stat().st_size-1024**2));data=f.read()
                        (result/'runner.log').write_bytes(data);artifacts['runner.log']=sha(data);retained+=len(data)
                    total=0
                    for name in keep:
                        name=relpath(name);p=inside(scratch,name)
                        if not p.is_file():
                            receipt.setdefault('missing_outputs',[]).append(name);continue
                        total+=p.stat().st_size
                        if total>OUTPUT_LIMIT:raise ValueError('retained_output_budget_exceeded')
                        dest=result/'artifacts'/name;dest.parent.mkdir(parents=True,exist_ok=True)
                        shutil.copyfile(p,dest)
                        h=sha(p.read_bytes())
                        if sha(dest.read_bytes())!=h:raise ValueError('output_preservation_failed')
                        artifacts[name]=h
                    retained+=total
                    if receipt.get('missing_outputs'):receipt['state']='FAILED'
                    receipt['artifacts']=artifacts
                    # A7: byte accounting. created-at-cleanup == retained + reclaimed.
                    end_bytes=sum(inventory(scratch).values())
                    receipt['bytes']={'schema':BYTES_SCHEMA,'units':'bytes',
                                      'scratch_peak_bytes':max(peak,end_bytes),
                                      'scratch_at_cleanup_bytes':end_bytes,
                                      'retained_bytes':retained,'reclaimed_bytes':end_bytes-retained,
                                      'declared_budget_bytes':job_limit}
                    # A3/A9: lease identity and directory policy gate deletion.
                    verify_lease(sroot,jid)
                    if classify_runner(root,scratch)!='temporary_scratch':raise ValueError('cleanup_refused_not_scratch')
                    write_json(result/'receipt.json',receipt);preserved=True
                    remove_owned(scratch,sroot);(sroot/'lease.json').unlink(missing_ok=True)
                    receipt['cleanup_verified']=True
                except Exception as exc:
                    receipt['cleanup_error']=str(exc)
                    try:record_hold(root,'scratch_preserved','runner job '+jid,'cleanup_failed: '+str(exc)[:300],
                                    'operator inspection; scratch preserved with its job identity intact',scratch)
                    except Exception as hold_exc:receipt['hold_error']=str(hold_exc)
            else:
                try:record_hold(root,'scratch_preserved','runner job '+jid,'process_tree_not_drained',
                                'operator inspection; scratch and lease preserved until the process tree drains',scratch)
                except Exception as hold_exc:receipt['hold_error']=str(hold_exc)
            if not drained or not preserved or not receipt['cleanup_verified']:receipt['state']='BLOCKED'
            write_json(result/'receipt.json',receipt)
        return {**receipt,'result_directory':str(result)}


def apply(sealed, target):
    sealed=Path(sealed).resolve(strict=True);m=verify(sealed);target=Path(target).resolve(strict=True)
    if Path(git(target,'rev-parse','--show-toplevel').decode().strip()).resolve()!=target:
        raise ValueError('target_not_repository_root')
    gd=Path(git(target,'rev-parse','--path-format=absolute','--git-common-dir').decode().strip())
    with lock(gd/'chimera-package-integration.lock'):
        if git(target,'rev-parse','HEAD').decode().strip()!=m['package']['base']:
            raise ValueError('stale_base_requires_rebase_and_revalidation')
        if git(target,'status','--porcelain').strip():raise ValueError('integration_target_must_be_clean')
        if not m['changes']:return {'state':'NO_CHANGES'}
        patch=str(sealed/'change.patch')
        git(target,'apply','--check','--index',patch)
        git(target,'apply','--index',patch)
        return {'state':'APPLIED_STAGED_NOT_COMMITTED','changed_files':m['changes']}


def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='op',required=True)
    c=sub.add_parser('create');c.add_argument('--source',required=True);c.add_argument('--base',required=True)
    c.add_argument('--package',required=True);c.add_argument('--owner',required=True);c.add_argument('--task',required=True)
    c.add_argument('--read',action='append',default=[]);c.add_argument('--write',action='append',required=True)
    s=sub.add_parser('seal');s.add_argument('package')
    r=sub.add_parser('run');r.add_argument('--sealed',required=True);r.add_argument('--keep',action='append',default=[])
    r.add_argument('--slot',type=int,default=None,help='Omit for automatic selection from the configured pool');r.add_argument('--timeout',type=float,default=600)
    r.add_argument('--job-limit',type=float,default=JOB_LIMIT,help='Declared per-job scratch budget in bytes, reserved before admission')
    r.add_argument('command',nargs=argparse.REMAINDER)
    a=sub.add_parser('apply');a.add_argument('--sealed',required=True);a.add_argument('--target',required=True)
    h=sub.add_parser('holds');h.add_argument('--root',default=None,help='Runner root holding holds_ledger.json')
    x=ap.parse_args()
    if x.op=='create':out=create(x.source,x.base,x.package,x.owner,x.task,x.read,x.write)
    elif x.op=='seal':out=seal(x.package)
    elif x.op=='apply':out=apply(x.sealed,x.target)
    elif x.op=='holds':out=read_holds(x.root) if x.root else read_holds()
    else:out=run(x.sealed,x.command[1:] if x.command[:1]==['--'] else x.command,x.keep,x.timeout,slot=x.slot,job_limit=int(x.job_limit))
    print(json.dumps(out,indent=2))
    if out.get('state')=='BUSY':raise SystemExit(75)
    if out.get('state') in ('FAILED','BLOCKED'):raise SystemExit(2)


if __name__=='__main__':main()
