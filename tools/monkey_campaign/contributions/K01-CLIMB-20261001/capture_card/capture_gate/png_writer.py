"""Minimal deterministic PNG encoder (8-bit RGB, no external dependencies).

Filter byte 0 per scanline, zlib level 9, fixed strategy-free compression.
Same pixels always produce the same bytes on this platform, so crop artifacts
can be bound by sha256 in the review manifest and in EVIDENCE.md.
"""

import struct
import zlib

import numpy as np

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _chunk(kind, payload):
    return (struct.pack(">I", len(payload)) + kind + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF))


def encode_png(rgb):
    """Encode an (h, w, 3) uint8 array to deterministic PNG bytes."""
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("rgb_hwc_uint8_required")
    height, width = rgb.shape[0], rgb.shape[1]
    contiguous = np.ascontiguousarray(rgb, dtype=np.uint8)
    raw = b"".join(b"\x00" + contiguous[y].tobytes() for y in range(height))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    idat = zlib.compress(raw, 9)
    return (PNG_SIGNATURE + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", idat) + _chunk(b"IEND", b""))


def write_png(path, rgb):
    data = encode_png(rgb)
    with open(path, "wb") as handle:
        handle.write(data)
    return data
