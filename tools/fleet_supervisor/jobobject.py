# fleet_supervisor/jobobject.py -- Windows Job Object primitives via ctypes.
# No new dependencies. Every function here is a thin, honest wrapper over the
# Win32 API; policy lives in launcher/lifecycle/broker, never here.
#
# Astra's contract this layer exists for (astra-round6-answer-20260922.md):
#   "The appropriate Windows primitive is a small supervisor using Job Objects.
#    Windows supports grouping processes, enforcing limits, and terminating the
#    group; KILL_ON_JOB_CLOSE terminates members when the last job handle closes."
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import os

k32 = ctypes.WinDLL("kernel32", use_last_error=True)

# ---------------------------------------------------------------- constants
CREATE_SUSPENDED = 0x00000004
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_NO_WINDOW = 0x08000000
CREATE_BREAKAWAY_FROM_JOB = 0x01000000  # reference only: launcher NEVER passes this
NORMAL_PRIORITY_CLASS = 0x00000020
BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
SW_SHOWMINNOACTIVE = 7
STARTF_USESHOWWINDOW = 0x00000001
CTRL_BREAK_EVENT = 1
INVALID_HANDLE_VALUE = -1  # as unsigned 0xFFFF...
ERROR_ACCESS_DENIED = 5
ERROR_INVALID_PARAMETER = 87

PROCESS_QUERY_LIMITED_INFORMATION = 0x00001000
PROCESS_TERMINATE = 0x00000001
PROCESS_SET_QUOTA = 0x00000100

JOB_OBJECT_QUERY = 0x0004
JOB_OBJECT_TERMINATE = 0x0008
JOB_OBJECT_ASSIGN_PROCESS = 0x0001
JOB_OBJECT_ALL_ACCESS = 0x1F001F

# JobObjectInformationClass -- PINNED BY MEASUREMENT on this host
# (Win11 build 26200), NOT copied from the classic header enum, which is
# SHIFTED here for the classes >= 7: the classic numbering made
# SetInformationJobObject(EXT) fail with err 24 and -- the dangerous part --
# the primitives gate caught a build where plausible-looking accounting
# numbers came back from the WRONG class. Each constant below is verified by
# tests_primitives.py against MEASURED EFFECTS (limit readbacks, tree kills,
# allocation failures), not against API return values.
JobObjectBasicAccountingInformation = 1   # accepts 48 B
JobObjectBasicLimitInformation = 2        # accepts 64 B
JobObjectBasicProcessIdList = 3           # variable
JobObjectBasicAndIoAccountingInformation = 8   # accepts 96 B here (classic says 7)
JobObjectExtendedLimitInformation = 9          # accepts 144 B here (classic says 8)
JobObjectCpuRateControlInformation = 14        # 16-byte struct here (MinRate/MaxRate)

# JOBOBJECT basic limit flags -- NOTE: BREAKAWAY_OK and SILENT_BREAKAWAY_OK are
# deliberately ABSENT: not setting them is exactly how breakaway is prohibited.
JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x00000008
JOB_OBJECT_LIMIT_AFFINITY = 0x00000001
JOB_OBJECT_LIMIT_PRIORITY_CLASS = 0x00000020
JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000

JOB_OBJECT_CPU_RATE_CONTROL_ENABLE = 0x00000001
JOB_OBJECT_CPU_RATE_CONTROL_HARD_CAP = 0x00000002

# F-CPURATE (measured 2026-09-22, Win11 build 26200): the CPU rate control
# primitive could NOT be pinned through any JobObjectInformationClass:
#   - SET at class 7 "succeeds" and is a measured NO-OP (a spinner ran at
#     0.955 of one core under a claimed 10% cap -- silent failure, the worst
#     kind);
#   - class 14 rejects every rate value with ERROR_INVALID_PARAMETER (with
#     both the 8- and 16-byte struct; only flags-only no-ops are accepted);
#   - no other class caps a measured spinner (0.962 baseline, all candidates
#     > 0.9).
# Per Rule 0 the launcher therefore REFUSES cpu_pct instead of pretending.
# Memory and active-process limits are the load-bearing limits and are
# verified by tests_primitives.py against measured effects.

TH32CS_SNAPPROCESS = 0x00000002

# ---------------------------------------------------------------- structures
class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]

class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", ctypes.c_ulong),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", ctypes.c_ulong),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", ctypes.c_ulong),
        ("SchedulingClass", ctypes.c_ulong),
    ]

class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]

class JOBOBJECT_CPU_RATE_CONTROL_INFORMATION(ctypes.Structure):
    # 16 bytes on this build (newer SDK adds MinRate/MaxRate). The 8-byte
    # classic form fails SetInformationJobObject with err 87 here -- measured.
    _fields_ = [
        ("ControlFlags", ctypes.c_ulong),
        ("CpuRate", ctypes.c_ushort),
        ("Weighting", ctypes.c_ushort),
        ("MinRate", ctypes.c_ulong),
        ("MaxRate", ctypes.c_ulong),
    ]

class JOBOBJECT_BASIC_ACCOUNTING_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("TotalUserTime", ctypes.c_longlong),
        ("TotalKernelTime", ctypes.c_longlong),
        ("ThisPeriodTotalUserTime", ctypes.c_longlong),
        ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
        ("TotalPageFaultCount", ctypes.c_ulong),
        ("TotalProcesses", ctypes.c_ulong),
        ("ActiveProcesses", ctypes.c_ulong),
        ("TotalTerminatedProcesses", ctypes.c_ulong),
    ]

class JOBOBJECT_BASIC_AND_IO_ACCOUNTING_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("Basic", JOBOBJECT_BASIC_ACCOUNTING_INFORMATION),
        ("IoCounters", IO_COUNTERS),
    ]

class STARTUPINFOW(ctypes.Structure):
    _fields_ = [
        ("cb", wt.DWORD), ("lpReserved", wt.LPWSTR), ("lpDesktop", wt.LPWSTR),
        ("lpTitle", wt.LPWSTR), ("dwX", wt.DWORD), ("dwY", wt.DWORD),
        ("dwXSize", wt.DWORD), ("dwYSize", wt.DWORD),
        ("dwXCountChars", wt.DWORD), ("dwYCountChars", wt.DWORD),
        ("dwFillAttribute", wt.DWORD), ("dwFlags", wt.DWORD),
        ("wShowWindow", wt.WORD), ("cbReserved2", wt.WORD),
        ("lpReserved2", ctypes.c_void_p), ("hStdInput", wt.HANDLE),
        ("hStdOutput", wt.HANDLE), ("hStdError", wt.HANDLE),
    ]

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", wt.HANDLE), ("hThread", wt.HANDLE),
        ("dwProcessId", wt.DWORD), ("dwThreadId", wt.DWORD),
    ]

class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wt.DWORD), ("cntUsage", wt.DWORD), ("th32ProcessID", wt.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wt.DWORD), ("cntThreads", wt.DWORD),
        ("th32ParentProcessID", wt.DWORD), ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wt.DWORD), ("szExeFile", wt.WCHAR * 260),
    ]

# ---------------------------------------------------------------- signatures
k32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wt.LPCWSTR]
k32.CreateJobObjectW.restype = wt.HANDLE
k32.SetInformationJobObject.argtypes = [wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD]
k32.SetInformationJobObject.restype = wt.BOOL
k32.QueryInformationJobObject.argtypes = [wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD, ctypes.POINTER(wt.DWORD)]
k32.QueryInformationJobObject.restype = wt.BOOL
k32.AssignProcessToJobObject.argtypes = [wt.HANDLE, wt.HANDLE]
k32.AssignProcessToJobObject.restype = wt.BOOL
k32.TerminateJobObject.argtypes = [wt.HANDLE, wt.UINT]
k32.TerminateJobObject.restype = wt.BOOL
k32.OpenJobObjectW.argtypes = [wt.DWORD, wt.BOOL, wt.LPCWSTR]
k32.OpenJobObjectW.restype = wt.HANDLE
k32.IsProcessInJob.argtypes = [wt.HANDLE, wt.HANDLE, ctypes.POINTER(wt.BOOL)]
k32.IsProcessInJob.restype = wt.BOOL
k32.CreateProcessW.argtypes = [wt.LPCWSTR, wt.LPWSTR, ctypes.c_void_p, ctypes.c_void_p,
                               wt.BOOL, wt.DWORD, ctypes.c_void_p, wt.LPCWSTR,
                               ctypes.POINTER(STARTUPINFOW), ctypes.POINTER(PROCESS_INFORMATION)]
k32.CreateProcessW.restype = wt.BOOL
k32.ResumeThread.argtypes = [wt.HANDLE]
k32.ResumeThread.restype = wt.DWORD
k32.TerminateProcess.argtypes = [wt.HANDLE, wt.UINT]
k32.TerminateProcess.restype = wt.BOOL
k32.GetProcessTimes.argtypes = [wt.HANDLE, ctypes.POINTER(wt.FILETIME), ctypes.POINTER(wt.FILETIME),
                                ctypes.POINTER(wt.FILETIME), ctypes.POINTER(wt.FILETIME)]
k32.GetProcessTimes.restype = wt.BOOL
k32.GetProcessId.argtypes = [wt.HANDLE]
k32.GetProcessId.restype = wt.DWORD
k32.GenerateConsoleCtrlEvent.argtypes = [wt.UINT, wt.DWORD]
k32.GenerateConsoleCtrlEvent.restype = wt.BOOL
k32.CloseHandle.argtypes = [wt.HANDLE]
k32.CloseHandle.restype = wt.BOOL
k32.WaitForSingleObject.argtypes = [wt.HANDLE, wt.DWORD]
k32.WaitForSingleObject.restype = wt.DWORD
k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
k32.Process32FirstW.argtypes = [wt.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
k32.Process32FirstW.restype = wt.BOOL
k32.Process32NextW.argtypes = [wt.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
k32.Process32NextW.restype = wt.BOOL
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.OpenProcess.restype = wt.HANDLE
k32.QueryFullProcessImageNameW.argtypes = [wt.HANDLE, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD)]
k32.QueryFullProcessImageNameW.restype = wt.BOOL
k32.GlobalMemoryStatusEx.argtypes = [ctypes.c_void_p]
k32.GlobalMemoryStatusEx.restype = wt.BOOL
k32.DuplicateHandle.argtypes = [wt.HANDLE, wt.HANDLE, wt.HANDLE, ctypes.POINTER(wt.HANDLE),
                                wt.DWORD, wt.BOOL, wt.DWORD]
k32.DuplicateHandle.restype = wt.BOOL
k32.GetExitCodeProcess.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
k32.GetExitCodeProcess.restype = wt.BOOL

# ---------------------------------------------------------------- helpers
class WinError(OSError):
    def __init__(self, what: str):
        super().__init__(f"{what}: WinError {ctypes.get_last_error()}")
        self.what = what


def close_handle(handle: int) -> None:
    if handle:
        k32.CloseHandle(handle)


def _filetime_to_u64(ft: wt.FILETIME) -> int:
    return (ft.dwHighDateTime << 32) | ft.dwLowDateTime


def process_creation_time_us(handle: int) -> int:
    """Creation time as the raw FILETIME (100 ns units since 1601) -- the
    authoritative half of process identity (pid + creation time), because
    PIDs are reused (Astra's law)."""
    c, e, k, u = wt.FILETIME(), wt.FILETIME(), wt.FILETIME(), wt.FILETIME()
    if not k32.GetProcessTimes(wt.HANDLE(handle), ctypes.byref(c), ctypes.byref(e), ctypes.byref(k), ctypes.byref(u)):
        raise WinError("GetProcessTimes")
    return _filetime_to_u64(c)


def process_image_name(pid: int) -> str | None:
    h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return None
    try:
        buf = ctypes.create_unicode_buffer(1024)
        sz = wt.DWORD(1024)
        if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(sz)):
            return buf.value
        return None
    finally:
        close_handle(h)


def process_alive_identity(pid: int, creation_time_us: int) -> bool:
    """True iff a process OBJECT exists with EXACTLY this (pid, creation time).
    NOTE: a TERMINATED member whose object lingers (some external handle still
    holds it) also matches here -- use process_running for the honest
    'is it still executing' test."""
    h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return False
    try:
        return process_creation_time_us(h) == creation_time_us
    except WinError:
        return False
    finally:
        close_handle(h)


def process_running(pid: int, creation_time_us: int) -> bool:
    """The honest liveness test: identity matches AND the process has not
    terminated (exit code still STILL_ACTIVE). A terminated zombie object
    keeps its (pid, creation time) resolvable -- measured this lane -- so an
    identity check alone over-reports survivors."""
    h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return False
    try:
        if process_creation_time_us(h) != creation_time_us:
            return False
        code = wt.DWORD(0)
        if not k32.GetExitCodeProcess(h, ctypes.byref(code)):
            return False
        return code.value == STILL_ACTIVE
    except WinError:
        return False
    finally:
        close_handle(h)


def memory_status() -> dict:
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", wt.DWORD), ("dwMemoryLoad", wt.DWORD),
            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]
    m = MEMORYSTATUSEX()
    m.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    if not k32.GlobalMemoryStatusEx(ctypes.byref(m)):
        raise WinError("GlobalMemoryStatusEx")
    return {
        "mem_load_pct": m.dwMemoryLoad,
        "total_phys_gib": m.ullTotalPhys / 2**30,
        "free_phys_gib": m.ullAvailPhys / 2**30,
        "total_commit_gib": m.ullTotalPageFile / 2**30,
        "free_commit_gib": m.ullAvailPageFile / 2**30,
    }


def enumerate_processes() -> list[dict]:
    """Read-only snapshot: pid, parent pid, exe name for every process."""
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == wt.HANDLE(-1).value or not snap:
        raise WinError("CreateToolhelp32Snapshot")
    out = []
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        ok = k32.Process32FirstW(snap, ctypes.byref(entry))
        while ok:
            out.append({
                "pid": entry.th32ProcessID,
                "ppid": entry.th32ParentProcessID,
                "name": entry.szExeFile,
            })
            ok = k32.Process32NextW(snap, ctypes.byref(entry))
    finally:
        close_handle(snap)
    return out


# ---------------------------------------------------------------- job api
def create_job(job_name: str, *, mem_gib: float | None, max_procs: int | None,
               cpu_pct: int | None = None, priority_class: int = NORMAL_PRIORITY_CLASS,
               set_priority_limit: bool = False,
               affinity_mask: int | None = None) -> int:
    """Create a NAMED job whose handle is non-inheritable (SECURITY_ATTRIBUTES
    = NULL => the returned handle is not inheritable) with the declared limits:
    KILL_ON_JOB_CLOSE (always), job+process committed-memory, active-process
    count, optional forced priority class, optional AFFINITY mask.
    Breakaway is prohibited by NOT setting either breakaway flag.
    cpu_pct is REFUSED (measured: see F-CPURATE above) -- never silently ignored.
    affinity_mask is the phase-2 measured ALTERNATIVE (P-CPUAFFINITY): a hard
    partition of logical processors IS enforceable on this build where a
    CPU-rate cap is not -- verified by readback here and by measured effect in
    tests_gpu_broker.py."""
    if cpu_pct:
        raise NotImplementedError(
            f"cpu_pct={cpu_pct} refused: the CPU-rate primitive could not be pinned "
            "on this build (F-CPURATE: silent no-op at class 7, err 87 at 14); "
            "refusing beats pretending")
    h = k32.CreateJobObjectW(None, job_name)
    if not h:
        raise WinError("CreateJobObjectW")
    ext = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    flags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if affinity_mask:
        ext.BasicLimitInformation.Affinity = int(affinity_mask)
        flags |= JOB_OBJECT_LIMIT_AFFINITY
    if mem_gib:
        b = int(mem_gib * (1 << 30))
        ext.ProcessMemoryLimit = b
        ext.JobMemoryLimit = b
        flags |= JOB_OBJECT_LIMIT_PROCESS_MEMORY | JOB_OBJECT_LIMIT_JOB_MEMORY
    if max_procs:
        ext.BasicLimitInformation.ActiveProcessLimit = max_procs
        flags |= JOB_OBJECT_LIMIT_ACTIVE_PROCESS
    if set_priority_limit:
        ext.BasicLimitInformation.PriorityClass = priority_class
        flags |= JOB_OBJECT_LIMIT_PRIORITY_CLASS
    ext.BasicLimitInformation.LimitFlags = flags
    if not k32.SetInformationJobObject(h, JobObjectExtendedLimitInformation,
                                       ctypes.byref(ext), ctypes.sizeof(ext)):
        err = ctypes.get_last_error()
        close_handle(h)
        raise WinError(f"SetInformationJobObject(extended) err={err}")
    # verify the limits LANDED (the wrong-class trap: plausible garbage on readback)
    rb = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    if not k32.QueryInformationJobObject(wt.HANDLE(h), JobObjectExtendedLimitInformation,
                                         ctypes.byref(rb), ctypes.sizeof(rb), None):
        err = ctypes.get_last_error()
        close_handle(h)
        raise WinError(f"QueryInformationJobObject(extended) err={err}")
    if rb.BasicLimitInformation.LimitFlags & JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE == 0:
        close_handle(h)
        raise WinError("limit readback: KILL_ON_JOB_CLOSE not applied -- refusing to own a job we cannot enforce")
    if mem_gib and not (rb.BasicLimitInformation.LimitFlags & JOB_OBJECT_LIMIT_JOB_MEMORY):
        close_handle(h)
        raise WinError("limit readback: JOB_MEMORY flag not applied")
    if mem_gib and rb.JobMemoryLimit != int(mem_gib * (1 << 30)):
        close_handle(h)
        raise WinError(f"limit readback: JobMemoryLimit={rb.JobMemoryLimit} != requested")
    if affinity_mask and not (rb.BasicLimitInformation.LimitFlags & JOB_OBJECT_LIMIT_AFFINITY):
        close_handle(h)
        raise WinError("limit readback: AFFINITY flag not applied")
    if affinity_mask and rb.BasicLimitInformation.Affinity != int(affinity_mask):
        close_handle(h)
        raise WinError(f"limit readback: Affinity={rb.BasicLimitInformation.Affinity:#x} "
                       f"!= requested {int(affinity_mask):#x}")
    return h


def assign_process_to_job(job_handle: int, process_handle: int) -> None:
    if not k32.AssignProcessToJobObject(wt.HANDLE(job_handle), wt.HANDLE(process_handle)):
        raise WinError("AssignProcessToJobObject")


def query_job_accounting(job_handle: int) -> dict:
    info = JOBOBJECT_BASIC_AND_IO_ACCOUNTING_INFORMATION()
    if not k32.QueryInformationJobObject(wt.HANDLE(job_handle), JobObjectBasicAndIoAccountingInformation,
                                         ctypes.byref(info), ctypes.sizeof(info), None):
        raise WinError("QueryInformationJobObject(accounting)")
    b = info.Basic
    io = info.IoCounters
    return {
        "total_processes": b.TotalProcesses,
        "active_processes": b.ActiveProcesses,
        "total_terminated_processes": b.TotalTerminatedProcesses,
        "io_bytes_total": io.ReadTransferCount + io.WriteTransferCount + io.OtherTransferCount,
        "io_ops_total": io.ReadOperationCount + io.WriteOperationCount + io.OtherOperationCount,
    }


def query_job_pids(job_handle: int) -> list[int]:
    class PIDLIST(ctypes.Structure):
        _fields_ = [("NumberOfAssignedProcesses", wt.DWORD),
                    ("NumberOfProcessIdsInList", wt.DWORD),
                    ("ProcessIdList", ctypes.c_size_t * 4096)]
    lst = PIDLIST()
    ret = wt.DWORD(0)
    if not k32.QueryInformationJobObject(wt.HANDLE(job_handle), JobObjectBasicProcessIdList,
                                         ctypes.byref(lst), ctypes.sizeof(lst), ctypes.byref(ret)):
        raise WinError("QueryInformationJobObject(pid_list)")
    return [lst.ProcessIdList[i] for i in range(lst.NumberOfProcessIdsInList)]


def set_job_cpu_rate(job_handle: int, cpu_pct: int) -> None:
    raise NotImplementedError(
        "cpu caps not enforceable on this build (F-CPURATE); see create_job")


def open_job(job_name: str, *, terminate_access: bool = False) -> int | None:
    """Open an existing named job. Returns None if the job object no longer
    exists (all handles closed => with KILL_ON_JOB_CLOSE, members are dead)."""
    access = JOB_OBJECT_ALL_ACCESS if terminate_access else JOB_OBJECT_QUERY
    h = k32.OpenJobObjectW(access, False, job_name)
    return h if h else None


def terminate_job(job_handle: int, exit_code: int = 1) -> None:
    if not k32.TerminateJobObject(wt.HANDLE(job_handle), exit_code):
        raise WinError("TerminateJobObject")


def is_process_in_job(process_handle: int, job_handle: int) -> bool:
    b = wt.BOOL(False)
    if not k32.IsProcessInJob(wt.HANDLE(process_handle), wt.HANDLE(job_handle), ctypes.byref(b)):
        raise WinError("IsProcessInJob")
    return bool(b.value)


def pid_in_job(pid: int, job_handle: int) -> bool | None:
    """Identity-safe membership check by pid. None => pid not openable (dead)."""
    h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return None
    try:
        return is_process_in_job(h, job_handle)
    finally:
        close_handle(h)


# ------------------------------------------------------- process creation
STARTF_USESTDHANDLES = 0x00000100
HANDLE_FLAG_INHERIT = 0x00000001
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_RW = FILE_SHARE_READ | FILE_SHARE_WRITE  # stdout+stderr may share one log
CREATE_ALWAYS = 2
# NOTE (measured): OPEN_ALWAYS fails with err 2 for absent files under this
# harness sandbox; CREATE_ALWAYS works. Session logs are unique-named anyway,
# so a fresh log per launch is the correct semantic.
CREATE_DETACHED = 0x00000008

k32.CreateFileW.argtypes = [wt.LPCWSTR, wt.DWORD, wt.DWORD, ctypes.c_void_p, wt.DWORD, wt.DWORD, wt.HANDLE]
k32.CreateFileW.restype = wt.HANDLE
k32.SetHandleInformation.argtypes = [wt.HANDLE, wt.DWORD, wt.DWORD]
k32.SetHandleInformation.restype = wt.BOOL


def _log_handle(path: str) -> int:
    h = k32.CreateFileW(path, GENERIC_WRITE, FILE_SHARE_RW, None, CREATE_ALWAYS, 0, None)
    err = ctypes.get_last_error()
    # CreateFileW signals failure with INVALID_HANDLE_VALUE, not NULL -- both
    # must be checked (a truthy -1 once slipped through as a "valid" handle).
    if not h or h == 0xFFFFFFFFFFFFFFFF:
        raise WinError(f"CreateFileW({path}) err={err}")
    if not k32.SetHandleInformation(h, HANDLE_FLAG_INHERIT, HANDLE_FLAG_INHERIT):
        err = ctypes.get_last_error()
        close_handle(h)
        raise WinError(f"SetHandleInformation(inherit) err={err}")
    return h


def create_suspended_process(command: list[str], cwd: str | None, *,
                             priority_class: int = NORMAL_PRIORITY_CLASS,
                             new_process_group: bool = True,
                             no_window: bool = True,
                             detached: bool = False,
                             stdout_file: str | None = None,
                             stderr_file: str | None = None) -> dict:
    """CreateProcessW with CREATE_SUSPENDED. The JOB handle in the caller is
    non-inheritable; the ONLY inheritable handles are the optional log-file
    std streams -- never the job (Astra's law). detached=True gives the root
    NO console at all (no conhost member joins the job). Returns raw handles
    + pid + the creation time read while suspended. The caller MUST either
    resume or terminate the returned process."""
    import subprocess
    cmdline = subprocess.list2cmdline(command)
    si = STARTUPINFOW()
    si.cb = ctypes.sizeof(si)
    si.dwFlags = STARTF_USESHOWWINDOW
    si.wShowWindow = SW_SHOWMINNOACTIVE  # even if a window were legal, never active/front
    inherit = False
    log_handles = []
    out_h = err_h = None
    if stdout_file:
        out_h = _log_handle(stdout_file); log_handles.append(out_h)
        si.hStdOutput = wt.HANDLE(out_h); inherit = True
    if stderr_file:
        # one shared log file => one shared handle (CREATE_ALWAYS would
        # otherwise truncate between the two opens and the streams would
        # overwrite each other -- measured in the primitives gate)
        err_h = out_h if stderr_file == stdout_file else _log_handle(stderr_file)
        if err_h not in log_handles:
            log_handles.append(err_h)
        si.hStdError = wt.HANDLE(err_h); inherit = True
    if inherit:
        si.dwFlags |= STARTF_USESTDHANDLES
    pi = PROCESS_INFORMATION()
    flags = CREATE_SUSPENDED
    if new_process_group:
        flags |= CREATE_NEW_PROCESS_GROUP
    if detached:
        flags |= CREATE_DETACHED
    elif no_window:
        flags |= CREATE_NO_WINDOW
    app = command[0] if os.path.isabs(command[0]) else None
    ok = k32.CreateProcessW(app, cmdline, None, None, inherit, flags, None,
                            cwd, ctypes.byref(si), ctypes.byref(pi))
    err = ctypes.get_last_error()
    for h in log_handles:
        close_handle(h)  # the child owns its inherited duplicate now
    if not ok:
        raise WinError(f"CreateProcessW({cmdline[:120]}) err={err}")
    creation = process_creation_time_us(pi.hProcess)
    return {
        "process_handle": pi.hProcess,
        "thread_handle": pi.hThread,
        "pid": pi.dwProcessId,
        "creation_time_us": creation,
    }


def resume_process(proc: dict) -> None:
    if k32.ResumeThread(wt.HANDLE(proc["thread_handle"])) == 0xFFFFFFFF:
        raise WinError("ResumeThread")


def duplicate_handle(handle: int) -> int:
    """Duplicate into this process (DUPLICATE_SAME_ACCESS). Declared argtypes
    are load-bearing: the undeclared call truncated 64-bit handle values and
    produced silent garbage waits."""
    dup = wt.HANDLE()
    if not k32.DuplicateHandle(k32.GetCurrentProcess(), wt.HANDLE(handle),
                               k32.GetCurrentProcess(), ctypes.byref(dup), 0, False, 2):
        raise WinError("DuplicateHandle")
    return dup.value or 0


def wait_process(handle: int, timeout_ms: int) -> bool:
    """True iff the process object is signaled (exited)."""
    return k32.WaitForSingleObject(wt.HANDLE(handle), wt.DWORD(timeout_ms)) == 0


def exit_code(handle: int) -> int | None:
    code = wt.DWORD(0)
    if not k32.GetExitCodeProcess(wt.HANDLE(handle), ctypes.byref(code)):
        return None
    return code.value


STILL_ACTIVE = 259


def terminate_pid_by_handle(process_handle: int, exit_code: int = 1) -> None:
    """Terminate a process WE HOLD A HANDLE TO (launch-failure cleanup of a
    suspended root). Never by name/port/age."""
    if not k32.TerminateProcess(wt.HANDLE(process_handle), exit_code):
        # already exited is fine
        ctypes.set_last_error(0)
