# SPDX-License-Identifier: AGPL-3.0-or-later
"""Size-refusal contract of the shared human/AI transport, without bpy.

Every size refusal must carry BOTH the actual byte count and the limit, and the
bounded fallback reply for an unwritable oversized reply must itself stay within
MAX_REPLY while never claiming the operation failed. Run with any Python 3.8+:
  Libuipc/.venv/Scripts/python.exe -B tests/test_client_protocol_sizes.py
"""
import importlib.util
import tempfile
import traceback
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    'client_protocol', Path(__file__).resolve().parents[1] / 'python/chimera_studio/client_protocol.py')
wire = importlib.util.module_from_spec(spec);spec.loader.exec_module(wire)

checks = []


def check(name, function):
    try:
        function();checks.append({'check': name, 'passed': True})
    except Exception:
        checks.append({'check': name, 'passed': False, 'traceback': traceback.format_exc()})


def refusal_carries_both_numbers(function):
    error = None
    try:
        function()
    except ValueError as caught:
        error = str(caught)
    assert error is not None, 'no size refusal was raised'
    assert 'exceeds the protocol size limit' not in error, 'refusal is still the old unnumbered message'
    return error


def atomic_refusal_numbers():
    value = {'pad': 'x' * (wire.MAX_REPLY + 123)}
    expected = len(wire.canonical(value).encode('utf-8'))
    with tempfile.TemporaryDirectory() as folder:
        error = refusal_carries_both_numbers(
            lambda: wire.atomic(Path(folder) / 'reply.json', value))
    assert str(expected) in error, error
    assert str(wire.MAX_REPLY) in error, error


def atomic_refusal_numbers_custom_limit():
    value = {'pad': 'y' * 200}
    expected = len(wire.canonical(value).encode('utf-8'))
    with tempfile.TemporaryDirectory() as folder:
        error = refusal_carries_both_numbers(
            lambda: wire.atomic(Path(folder) / 'reply.json', value, 64))
    assert str(expected) in error and '64' in error, error


def read_refusal_numbers():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / 'reply.json'
        # read() reads at most limit+1 bytes, so the named actual count is the
        # truncated read size, not the whole file.
        content = b'{' + b'"x":"' + b'z' * 7 + b'"}'
        path.write_bytes(content)
        error = refusal_carries_both_numbers(lambda: wire.read(path, 10))
        assert str(min(len(content), 11)) in error and '10' in error, error
        # The request-side limit must be named as well.
        path.write_bytes(b'x' * (wire.MAX_REQUEST + 5))
        error = refusal_carries_both_numbers(
            lambda: wire.read(path, wire.MAX_REQUEST))
    assert str(wire.MAX_REQUEST + 1) in error, error
    assert str(wire.MAX_REQUEST) in error, error


def fallback_is_bounded_and_truthful():
    numbers = f'JSON is {wire.MAX_REPLY + 54321} bytes; the limit is {wire.MAX_REPLY} bytes'
    reply = wire.oversize_reply(numbers, 'a' * 32, 'b' * 32, 'c' * 64)
    size = len(wire.canonical(reply).encode('utf-8'))
    assert size < wire.MAX_REPLY, size
    assert reply['ok'] is False
    assert reply['schema'] == wire.SCHEMA
    assert reply['session'] == 'a' * 32 and reply['id'] == 'b' * 32
    assert reply['request_sha256'] == 'c' * 64
    assert str(wire.MAX_REPLY + 54321) in reply['error'], reply['error']
    assert str(wire.MAX_REPLY) in reply['error'], reply['error']
    assert 'MAY HAVE EXECUTED' in reply['error'], reply['error']
    # The fallback must never claim the operation failed or completed.
    for wording in ('failed', 'did not run', 'was not executed', 'completed successfully'):
        assert wording not in reply['error'].lower(), reply['error']


def small_roundtrip_still_works():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / 'reply.json'
        value = {'ok': True, 'result': [1, 2, 3]}
        wire.atomic(path, value)
        assert wire.read(path) == value


check('atomic() refusal names actual bytes and MAX_REPLY', atomic_refusal_numbers)
check('atomic() refusal names both numbers for a custom limit', atomic_refusal_numbers_custom_limit)
check('read() refusal names actual bytes and the limit', read_refusal_numbers)
check('oversize_reply() is bounded, carries both numbers and never claims failure', fallback_is_bounded_and_truthful)
check('small values still round-trip through atomic()+read()', small_roundtrip_still_works)

failed = [c for c in checks if not c['passed']]
print(wire.canonical({'checks': checks, 'passed': not failed, 'failed': len(failed)}))
raise SystemExit(1 if failed else 0)
