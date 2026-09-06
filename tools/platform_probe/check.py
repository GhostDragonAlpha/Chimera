#!/usr/bin/env python3
"""Compile actual engine PNG code and independently check byte transport.

CPU instrument only: no window, Vulkan, renderer, simulation or DYAD verdict.
Run from any directory. Temporary artifacts stay under repo/.tmp/platform_probe/.
Requires stdlib + a C++17 compiler, or --executable pointing to a CMake-built fixture.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import json
from pathlib import Path
import platform
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = [(1, 1, 0), (7, 3, 0), (257, 65, 0), (7, 3, 1)]


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def decode(data):
    """Independent strict decoder for the encoder's declared RGBA8/filter-0 scope."""
    require(data[:8] == b'\x89PNG\r\n\x1a\n', 'signature')
    at, kinds, payloads = 8, [], []
    while at < len(data):
        require(at + 12 <= len(data), 'truncated chunk')
        n = struct.unpack_from('>I', data, at)[0]
        require(at + 12 + n <= len(data), 'chunk length')
        kind = data[at + 4:at + 8]
        body = data[at + 8:at + 8 + n]
        crc = struct.unpack_from('>I', data, at + 8 + n)[0]
        require(binascii.crc32(kind + body) & 0xffffffff == crc, 'CRC')
        kinds.append(kind)
        payloads.append(body)
        at += n + 12
    require(kinds == [b'IHDR', b'IDAT', b'IEND'], 'chunk sequence')
    require(len(payloads[0]) == 13 and not payloads[-1], 'header/end size')
    w, h, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', payloads[0])
    require(w > 0 and h > 0, 'dimensions')
    require((depth, color, compression, filtering, interlace) == (8, 6, 0, 0, 0), 'format')
    inflater = zlib.decompressobj()
    raw = inflater.decompress(payloads[1]) + inflater.flush()
    require(inflater.eof and not inflater.unused_data and not inflater.unconsumed_tail,
            'deflate termination')
    stride = 4 * w + 1
    require(len(raw) == stride * h, 'scanline size')
    require(all(raw[y * stride] == 0 for y in range(h)), 'filter')
    return w, h, b''.join(raw[y * stride + 1:(y + 1) * stride] for y in range(h))


def expected(w, h, phase):
    return bytes(c & 255 for y in range(h) for x in range(w)
                 for c in (x + 17 * phase, 3 * y + 29 * phase,
                           x ^ y ^ phase, 7 * x + 11 * y + 13 * phase))


def check_image(data, fixture):
    w, h, pixels = decode(data)
    ew, eh, phase = fixture
    require((w, h) == (ew, eh), 'unexpected dimensions')
    require(pixels == expected(ew, eh, phase), 'pixels')
    return len(pixels)


def control_png(w, h, pixels):
    """Use stdlib zlib, independently of the engine's stored-block implementation."""
    def chunk(kind, payload):
        return (struct.pack('>I', len(payload)) + kind + payload +
                struct.pack('>I', binascii.crc32(kind + payload) & 0xffffffff))
    raw = b''.join(b'\0' + pixels[y * w * 4:(y + 1) * w * 4] for y in range(h))
    return (b'\x89PNG\r\n\x1a\n' +
            chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', help='C++ compiler executable (GCC/Clang or MSVC cl)')
    parser.add_argument('--executable', type=Path, help='already built capture_fixture')
    args = parser.parse_args()
    root = ROOT / '.tmp' / 'platform_probe'
    root.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix='run_', dir=root))
    report = {'platform': platform.platform(), 'artifact_directory': str(run),
              'scope': 'synthetic byte-transport instrument; not renderer/DYAD',
              'checked_out_header_sha256': hashlib.sha256(
                  (ROOT / 'ChimeraEngine/engine/png_encoder.hpp').read_bytes()).hexdigest(),
              'build_provenance': ('supplied_executable_not_rebuilt_here' if args.executable
                                   else 'compile_in_this_run'),
              'checks': [], 'runtime': 'NOT RUN', 'visual': 'NOT RUN', 'human': 'PENDING'}
    try:
        executable = args.executable.resolve() if args.executable else run / (
            'capture_fixture.exe' if sys.platform == 'win32' else 'capture_fixture')
        if not args.executable:
            compiler = args.compiler or next((shutil.which(c) for c in
                ('c++', 'g++', 'clang++', 'cl') if shutil.which(c)), None)
            require(compiler is not None, 'C++17 compiler unavailable')
            source = Path(__file__).with_name('capture_fixture.cpp')
            include = ROOT / 'ChimeraEngine/engine'
            if Path(compiler).name.lower() in ('cl', 'cl.exe'):
                command = [compiler, '/nologo', '/std:c++17', '/EHsc', '/W4',
                           f'/I{include}', str(source), f'/Fe:{executable}']
            else:
                command = [compiler, '-std=c++17', '-Wall', '-Wextra', '-Wpedantic',
                           '-I', str(include), str(source), '-o', str(executable)]
            report['compile_command'] = command
            compiled = subprocess.run(command, cwd=run, capture_output=True, text=True, timeout=60)
            (run / 'compile.txt').write_text(compiled.stdout + compiled.stderr)
            require(compiled.returncode == 0, f'compile failed: {run / "compile.txt"}')
            report['checks'].append({'name': 'standalone_native_compile', 'status': 'PASS'})
        report['executable_sha256'] = hashlib.sha256(executable.read_bytes()).hexdigest()
        generated = subprocess.run([str(executable), str(run)], cwd=run,
                                   capture_output=True, text=True, timeout=30)
        (run / 'fixture.txt').write_text(generated.stdout + generated.stderr)
        require(generated.returncode == 0, 'fixture executable failed')
        images = [(run / f'fixture_{i}.png').read_bytes() for i in range(len(FIXTURES))]
        for i, (data, fixture) in enumerate(zip(images, FIXTURES)):
            count = check_image(data, fixture)
            report['checks'].append({'name': f'lossless_fixture_{i}', 'status': 'PASS',
                                     'channels_checked': count, 'channel_errors': 0})
        require(images[1] != images[3], 'distinct phases encoded identically')
        report['checks'].append({'name': 'distinct_input_phases', 'status': 'PASS'})
        corrupt = bytearray(images[1])
        corrupt[29] ^= 1  # IHDR CRC, outside dimensions/format payload
        w, h, pixels = decode(images[1])
        swapped = bytearray(pixels)
        for i in range(0, len(swapped), 4):
            swapped[i], swapped[i + 1] = swapped[i + 1], swapped[i]
        controls = [('corrupt_crc', bytes(corrupt), FIXTURES[1], 'CRC'),
                    ('swapped_phase', images[3], FIXTURES[1], 'pixels'),
                    ('swapped_channels', control_png(w, h, swapped), FIXTURES[1], 'pixels')]
        for name, data, fixture, reason in controls:
            try:
                check_image(data, fixture)
            except ValueError as error:
                require(str(error) == reason, f'{name}: wrong rejection: {error}')
            else:
                raise ValueError(f'{name}: negative control survived')
            report['checks'].append({'name': name, 'status': 'PASS', 'rejected_for': reason})
        require(len(report['checks']) == (8 if args.executable else 9), 'check count')
        report['status'] = 'PASS'
        code = 0
    except (ValueError, OSError, subprocess.TimeoutExpired, zlib.error, struct.error) as error:
        report.update(status='FAIL', error=str(error))
        code = 1
    (run / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return code


if __name__ == '__main__':
    sys.exit(main())
