"""Host profile, memory admission and cooperative library thread budgets."""
import ctypes
import json
import os
from pathlib import Path

PROFILE_PATH=Path(__file__).with_name('runner_profile.json')


def profile():
    p=json.loads(PROFILE_PATH.read_text(encoding='utf-8'))
    if p.get('schema')!='chimera.runner_profile.v1':raise ValueError('invalid_runner_profile')
    for key,lo,hi in [('cpu_slots',1,8),('threads_per_job',1,8),('job_memory_gib',1,32),('free_memory_reserve_gib',16,64)]:
        if type(p.get(key)) is not int or not lo<=p[key]<=hi:raise ValueError('invalid_profile_'+key)
    if p['cpu_slots']*p['threads_per_job']>p['physical_cores']:
        raise ValueError('thread_budget_exceeds_physical_cores')
    if (p['cpu_slots']*p['job_memory_gib']+p['free_memory_reserve_gib'])*1024**3>p['installed_ram_bytes']:
        raise ValueError('memory_budget_exceeds_installed_ram')
    return p


def available_memory():
    if os.name!='nt':raise ValueError('memory_admission_requires_windows')
    class Memory(ctypes.Structure):
        _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(n,ctypes.c_ulonglong) for n in
            ('total_phys','avail_phys','total_page','avail_page','total_virtual','avail_virtual','avail_extended')]
    m=Memory();m.length=ctypes.sizeof(m)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):raise OSError('memory_query_failed')
    return m.avail_phys


def admission(p):
    free=available_memory()
    required=(p['free_memory_reserve_gib']+p['job_memory_gib'])*1024**3
    return dict(allowed=free>=required,available_bytes=free,required_bytes=required)


def thread_environment(p):
    n=str(p['threads_per_job'])
    return {**{k:n for k in ('OMP_NUM_THREADS','OMP_THREAD_LIMIT','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS',
        'NUMEXPR_NUM_THREADS','NUMEXPR_MAX_THREADS','NUMBA_NUM_THREADS','VECLIB_MAXIMUM_THREADS',
        'BLIS_NUM_THREADS','CMAKE_BUILD_PARALLEL_LEVEL','RAYON_NUM_THREADS')},
        'OMP_MAX_ACTIVE_LEVELS':'1','OMP_DYNAMIC':'FALSE','MKL_DYNAMIC':'FALSE'}
