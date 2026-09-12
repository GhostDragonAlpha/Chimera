"""Owned Linux service lifecycle; no name-based or bare-PID signal fallback.

Requires procfs plus os.pidfd_open/signal.pidfd_send_signal. These operations
only target the process whose persisted identity and listening socket match.
"""
import os
from pathlib import Path
import select
import signal


def identity(pid):
    if type(pid) is not int or pid <= 0:
        raise ValueError('invalid_process_id')
    stat = Path(f'/proc/{pid}/stat').read_text()
    # comm (field 2) can contain whitespace and parentheses; fields after its
    # final closing parenthesis begin with state (field 3).
    fields = stat.rsplit(')', 1)[1].split()
    return {'pid': pid, 'start_ticks': int(fields[19]),
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}


def owns_listener(pid, port):
    inodes = set()
    for family in ('tcp', 'tcp6'):
        table = Path(f'/proc/{pid}/net/{family}')
        if not table.exists():
            continue
        for line in table.read_text().splitlines()[1:]:
            fields = line.split()
            if len(fields) >= 10 and fields[3] == '0A' and int(fields[1].rsplit(':', 1)[1], 16) == port:
                inodes.add('socket:[' + fields[9] + ']')
    for entry in Path(f'/proc/{pid}/fd').iterdir():
        try:
            if os.readlink(entry) in inodes:
                return True
        except FileNotFoundError:
            continue  # Another thread may close an unrelated descriptor.
    return False


def stop_owned(pid, expected_identity, port, wait_seconds=5.0):
    if not hasattr(os, 'pidfd_open') or not hasattr(signal, 'pidfd_send_signal'):
        raise RuntimeError('linux_pidfd_unavailable')
    fd = os.pidfd_open(pid)
    try:
        if not expected_identity or identity(pid) != expected_identity:
            raise RuntimeError('linux_process_identity_mismatch')
        if not owns_listener(pid, port):
            raise RuntimeError('linux_listener_identity_mismatch')
        try:
            signal.pidfd_send_signal(fd, signal.SIGTERM)
        except ProcessLookupError:
            pass  # It exited after identity validation; the pidfd stays bound.
        if not select.select([fd], [], [], wait_seconds)[0]:
            signal.pidfd_send_signal(fd, signal.SIGKILL)
            if not select.select([fd], [], [], wait_seconds)[0]:
                raise RuntimeError('linux_process_drain_incomplete')
    finally:
        os.close(fd)
