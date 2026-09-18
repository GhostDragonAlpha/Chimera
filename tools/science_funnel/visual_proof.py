"""Visual proof renders of admitted library data -- PROOF OF INTAKE ONLY.

Everything here renders from the PINNED bytes of already-admitted library
data and produces deterministic PNGs. Scope boundary, stated on every output
surface: these are PROOF-OF-INTAKE renders. They prove that pinned inputs
decode (as far as recorded), that the renderer is a deterministic function of
those bytes, and that a one-byte input change cannot leave a PNG unchanged.
They are NOT physics verification and NOT qualification of anything.

Contract: work.data.visual_proof_20260917 (Rule 0 record in the authored
program). Falsifiers, implemented as tests in
tools/science_funnel/tests/test_visual_proof.py:
  1. Determinism -- re-render any family from the pinned inputs; PNG bytes
     must be identical (the --verify pass re-renders the committed validation
     directory and compares byte-for-byte against manifest sha256s).
  2. Input sensitivity -- flip exactly one byte of a pinned input: either
     the PNG hash changes, or the renderer refuses loudly. A corrupted
     compressed container refuses; it can never silently reproduce bytes.

FALSIFIED ASSUMPTIONS (recorded in the admission contract, both mechanical):
  a. The intake brief assumed a pure struct decode of the Smithsonian GLB
     geometry. The pinned artifacts carry KHR_draco_mesh_compression as an
     EXTENSION REQUIRED (accessors have no bufferView), so plain accessor
     reads are impossible.
  b. A draco MESH_SEQUENTIAL_ENCODING decode was attempted next. The pinned
     streams are MESH_EDGEBREAKER_ENCODING (method 1) with the VALENCE
     traversal decoder (type 2), bitstream 2.2.
  c. A pure-python port of the google/draco edgebreaker decoder (HEAD and
     1.3.6 were checked) does NOT parse the pinned topology-split event
     section: under the reference layout the very first event pair fails the
     reference decoder's own validity check, and neither event order yields a
     consistent stream to completion. The pinned producer's exact event
     coding could not be identified within this lane, so the geometry decode
     REFUSES. What IS proven for the GLBs: the glTF-binary container and JSON
     chunk parse with stdlib struct, and the render therefore shows the
     accessor-declared bounding boxes under the document.json camera --
     an intake proof of the geometry METADATA, never of the geometry.

No new dependencies: PNG writing is pure zlib (IDAT chunks). numpy is
already pinned in this environment through tifffile.
"""
import io
import json
import math
import struct
import sys
import zlib
from pathlib import Path

import numpy as np

from .common import Refusal, require

# The label that every render carries, in-image and in the manifest.
PROOF_LABEL = 'PROOF-OF-INTAKE: NOT PHYSICS VERIFICATION'

SIZE = (320, 240)


# ---------------------------------------------------------------------------
# PNG writer (pure zlib; filter 0 rows, 8-bit RGB) -- no imaging dependencies.
# ---------------------------------------------------------------------------

def _chunk(tag, data):
    return (struct.pack('>I', len(data)) + tag + data
            + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF))


def encode_png(width, height, rgb):
    """rgb: bytes/bytearray of width*height*3 bytes, row-major. -> PNG bytes."""
    require(width > 0 and height > 0, 'png_size', f'{width}x{height}')
    require(len(rgb) == width * height * 3, 'png_buffer',
            f'{len(rgb)} != {width * height * 3}')
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    stride = width * 3
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter type 0 (None)
        raw += rgb[y * stride:(y + 1) * stride]
    return (b'\x89PNG\r\n\x1a\n' + _chunk(b'IHDR', ihdr)
            + _chunk(b'IDAT', zlib.compress(bytes(raw), 9))
            + _chunk(b'IEND', b''))


def read_png(png):
    """Minimal PNG reader for the falsifier tests: checks every chunk CRC and
    returns (width, height, rgb bytes) for 8-bit truecolor images."""
    require(png[:8] == b'\x89PNG\r\n\x1a\n', 'png_signature', '')
    pos = 8
    header = None
    idat = bytearray()
    while pos < len(png):
        length, tag = struct.unpack('>I4s', png[pos:pos + 8])
        data = png[pos + 8:pos + 8 + length]
        crc, = struct.unpack('>I', png[pos + 8 + length:pos + 12 + length])
        require(crc == zlib.crc32(tag + data) & 0xFFFFFFFF, 'png_crc', tag)
        if tag == b'IHDR':
            header = struct.unpack('>IIBBBBB', data)
        elif tag == b'IDAT':
            idat += data
        elif tag == b'IEND':
            pos += 12
            break
        pos += 12 + length
    require(header is not None, 'png_ihdr', '')
    width, height, depth, color, comp, filt, inter = header
    require((depth, color, comp, filt, inter) == (8, 2, 0, 0, 0),
            'png_ihdr_params', header)
    raw = zlib.decompress(bytes(idat))
    stride = width * 3
    require(len(raw) == (stride + 1) * height, 'png_raw_len', len(raw))
    out = bytearray(width * height * 3)
    for y in range(height):
        require(raw[y * (stride + 1)] == 0, 'png_filter', y)
        out[y * stride:(y + 1) * stride] = raw[y * (stride + 1) + 1:
                                               (y + 1) * (stride + 1)]
    return width, height, bytes(out)


# ---------------------------------------------------------------------------
# Canvas: RGB pixel buffer + tiny 5x7 uppercase bitmap font (LSB = top row).
# ---------------------------------------------------------------------------

_FONT = {
    'A': (0x7E, 0x11, 0x11, 0x11, 0x7E), 'B': (0x7F, 0x49, 0x49, 0x49, 0x36),
    'C': (0x3E, 0x41, 0x41, 0x41, 0x22), 'D': (0x7F, 0x41, 0x41, 0x22, 0x1C),
    'E': (0x7F, 0x49, 0x49, 0x49, 0x41), 'F': (0x7F, 0x09, 0x09, 0x09, 0x01),
    'G': (0x3E, 0x41, 0x49, 0x49, 0x7A), 'H': (0x7F, 0x08, 0x08, 0x08, 0x7F),
    'I': (0x00, 0x41, 0x7F, 0x41, 0x00), 'J': (0x20, 0x40, 0x41, 0x3F, 0x01),
    'K': (0x7F, 0x08, 0x14, 0x22, 0x41), 'L': (0x7F, 0x40, 0x40, 0x40, 0x40),
    'M': (0x7F, 0x02, 0x0C, 0x02, 0x7F), 'N': (0x7F, 0x04, 0x08, 0x10, 0x7F),
    'O': (0x3E, 0x41, 0x41, 0x41, 0x3E), 'P': (0x7F, 0x09, 0x09, 0x09, 0x06),
    'Q': (0x3E, 0x41, 0x51, 0x21, 0x5E), 'R': (0x7F, 0x09, 0x19, 0x29, 0x46),
    'S': (0x46, 0x49, 0x49, 0x49, 0x31), 'T': (0x01, 0x01, 0x7F, 0x01, 0x01),
    'U': (0x3F, 0x40, 0x40, 0x40, 0x3F), 'V': (0x1F, 0x20, 0x40, 0x20, 0x1F),
    'W': (0x3F, 0x40, 0x38, 0x40, 0x3F), 'X': (0x63, 0x14, 0x08, 0x14, 0x63),
    'Y': (0x07, 0x08, 0x70, 0x08, 0x07), 'Z': (0x61, 0x51, 0x49, 0x45, 0x43),
    '0': (0x3E, 0x51, 0x49, 0x45, 0x3E), '1': (0x00, 0x42, 0x7F, 0x40, 0x00),
    '2': (0x42, 0x61, 0x51, 0x49, 0x46), '3': (0x21, 0x41, 0x45, 0x4B, 0x31),
    '4': (0x18, 0x14, 0x12, 0x7F, 0x10), '5': (0x27, 0x45, 0x45, 0x45, 0x39),
    '6': (0x3C, 0x4A, 0x49, 0x49, 0x30), '7': (0x01, 0x71, 0x09, 0x05, 0x03),
    '8': (0x36, 0x49, 0x49, 0x49, 0x36), '9': (0x06, 0x49, 0x49, 0x29, 0x1E),
    ' ': (0, 0, 0, 0, 0), '-': (0x08, 0x08, 0x08, 0x08, 0x08),
    '.': (0x00, 0x30, 0x30, 0x00, 0x00), ':': (0x00, 0x36, 0x36, 0x00, 0x00),
    '/': (0x20, 0x10, 0x08, 0x04, 0x02), '(': (0x00, 0x08, 0x36, 0x41, 0x00),
    ')': (0x00, 0x41, 0x36, 0x08, 0x00), '+': (0x08, 0x08, 0x3E, 0x08, 0x08),
    '=': (0x14, 0x14, 0x14, 0x14, 0x14), ',': (0x00, 0x28, 0x30, 0x00, 0x00),
}


class Canvas:
    def __init__(self, width, height, color=(255, 255, 255)):
        self.w = width
        self.h = height
        self.buf = bytearray(bytes(color) * (width * height))

    def px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(color)

    def rect(self, x0, y0, x1, y1, color):
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            base = (y * self.w + max(0, x0)) * 3
            span = (min(self.w - 1, x1) - max(0, x0) + 1) * 3
            if span > 0:
                self.buf[base:base + span] = bytes(color) * (span // 3)

    def line(self, x0, y0, x1, y1, color):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.px(x0, y0, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def marker(self, x, y, r, color):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r:
                    self.px(x + dx, y + dy, color)

    def text(self, x, y, message, color=(0, 0, 0), scale=1):
        cx = x
        for ch in message.upper():
            glyph = _FONT.get(ch)
            if glyph is None:
                glyph = _FONT['-']
            for col, bits in enumerate(glyph):
                for row in range(7):
                    if bits & (1 << row):
                        self.rect(cx + col * scale, y + row * scale,
                                  cx + col * scale + scale - 1,
                                  y + row * scale + scale - 1, color)
            cx += 6 * scale
        return cx

    def png(self):
        return encode_png(self.w, self.h, self.buf)


# ---------------------------------------------------------------------------
# GLB container (stdlib struct) + document.json camera handling
# ---------------------------------------------------------------------------

def parse_glb(path):
    raw = Path(path).read_bytes()
    magic, version, length = struct.unpack_from('<III', raw, 0)
    require(magic == 0x46546C67, 'glb_magic', hex(magic))
    require(version == 2, 'glb_version', version)
    require(length <= len(raw), 'glb_length', length)
    pos = 12
    json_doc = None
    bin_chunk = None
    while pos < length:
        clen, ctype = struct.unpack_from('<II', raw, pos)
        data = raw[pos + 8:pos + 8 + clen]
        if ctype == 0x4E4F534A:  # JSON
            json_doc = json.loads(data.decode('utf-8'))
        elif ctype == 0x004E4942:  # BIN
            bin_chunk = data
        pos += 8 + clen
    require(json_doc is not None and bin_chunk is not None, 'glb_chunks', '')
    return json_doc, bin_chunk


def smithsonian_glb_status(glb_path):
    """Parse the pinned GLB as far as stdlib honestly reaches and record why
    the geometry itself refuses to decode. Returns a manifest-ready dict."""
    gltf, bin_chunk = parse_glb(glb_path)
    prim = gltf['meshes'][0]['primitives'][0]
    ext = prim.get('extensions', {}).get('KHR_draco_mesh_compression')
    require(ext is not None, 'glb_draco_required',
            'pinned artifacts are draco-compressed')
    require('KHR_draco_mesh_compression' in gltf.get('extensionsRequired', []),
            'glb_draco_required_ext', '')
    bv = gltf['bufferViews'][ext['bufferView']]
    blob = bytes(bin_chunk[bv.get('byteOffset', 0):
                           bv.get('byteOffset', 0) + bv['byteLength']])
    require(blob[:5] == b'DRACO', 'draco_magic', '')
    major, minor, etype, method, flags = blob[5], blob[6], blob[7], blob[8], \
        struct.unpack_from('<H', blob, 9)[0]
    traversal_type = blob[11]
    pos_acc = gltf['accessors'][prim['attributes']['POSITION']]
    idx_acc = gltf['accessors'][prim['indices']]
    # The reference decoder would refuse right here: under google/draco (HEAD
    # and 1.3.6) the first topology-split event pair already violates the
    # delta check (source delta + last = 667; split delta 6724 > 667), and
    # neither event order parses the section to completion.
    return {
        'container': 'glTF-binary parsed (stdlib struct)',
        'draco': {
            'bitstream': f'{major}.{minor}', 'encoder_type': etype,
            'encoder_method': method,
            'encoder_method_name': 'MESH_EDGEBREAKER_ENCODING' if method == 1
            else 'other',
            'traversal_type': traversal_type,
            'traversal_name': 'MESH_EDGEBREAKER_VALENCE_ENCODING'
            if traversal_type == 2 else 'other',
        },
        'accessors': {
            'position_count': pos_acc['count'], 'index_count': idx_acc['count'],
            'position_min': pos_acc['min'], 'position_max': pos_acc['max'],
        },
        'geometry_decode': 'REFUSED',
        'refusal_cause': 'draco_edgebreaker_event_stream_not_decodable: '
                         'topology-split event section diverges from the '
                         'reference layouts (google/draco HEAD and 1.3.6); '
                         'no producer-matching decoder exists in this lane',
    }


def quat_matrix(q):
    x, y, z, w = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ], dtype=np.float64)


def document_camera(doc, size):
    """Camera pose + perspective from a Voyager document.json, plus the model
    transform. NOTE: the Voyager model transform lives in the `models` entry
    (translation/rotation), the scene node only references it; both are
    composed (node outermost, model entry innermost). Returns a callable
    world->(sx, sy, depth) and metadata."""
    nodes = doc['nodes']
    cam_node = next(n for n in nodes if 'camera' in n)
    model_node = next(n for n in nodes if 'model' in n)
    model_def = doc['models'][model_node['model']]
    cam_R = quat_matrix(cam_node['rotation']) if 'rotation' in cam_node \
        else np.eye(3)
    cam_t = np.array(cam_node.get('translation', [0, 0, 0]), dtype=np.float64)
    node_R = quat_matrix(model_node['rotation']) if 'rotation' in model_node \
        else np.eye(3)
    node_t = np.array(model_node.get('translation', [0, 0, 0]),
                      dtype=np.float64)
    mod_R = quat_matrix(model_def['rotation']) if 'rotation' in model_def \
        else np.eye(3)
    mod_t = np.array(model_def.get('translation', [0, 0, 0]),
                     dtype=np.float64)
    cam = doc['cameras'][cam_node['camera']]['perspective']
    yfov = math.radians(float(cam['yfov']))  # Voyager stores degrees
    znear, zfar = float(cam['znear']), float(cam['zfar'])
    width, height = size
    aspect = width / height
    f = 1.0 / math.tan(yfov / 2)

    def project(points_world):
        # row-vector form of v_cam = R^T (p - t)
        view = (points_world - cam_t) @ cam_R
        w_cam = -view[:, 2]
        with np.errstate(divide='ignore', invalid='ignore'):
            px = (f / aspect) * (view[:, 0] / w_cam)
            py = f * (view[:, 1] / w_cam)
        sx = (px + 1.0) * 0.5 * width
        sy = (1.0 - (py + 1.0) * 0.5) * height
        return sx, sy, w_cam

    def model_to_world(points_local):
        inner = points_local @ mod_R.T + mod_t
        return inner @ node_R.T + node_t

    return project, model_to_world, {'yfov_deg': float(cam['yfov']),
                                     'znear': znear, 'zfar': zfar,
                                     'model_transform_source':
                                         'models entry'}


def render_glb_intake(glb_path, doc_path, size=SIZE):
    """PROOF-OF-INTAKE render of a pinned smithsonian GLB pair.

    The draco-compressed geometry REFUSES to decode (see
    smithsonian_glb_status); this render honestly shows what the pinned
    bytes DO admit through stdlib: the accessor-declared bounding box of the
    geometry, drawn as a wireframe under the document.json camera, with the
    draco refusal recorded in the manifest. NOT a render of the geometry."""
    width, height = size
    status = smithsonian_glb_status(glb_path)
    doc = json.loads(Path(doc_path).read_text(encoding='utf-8'))
    project, model_to_world, cam_meta = document_camera(doc, size)
    amin = np.array(status['accessors']['position_min'], dtype=np.float64)
    amax = np.array(status['accessors']['position_max'], dtype=np.float64)
    corners = np.array([(x, y, z)
                        for x in (amin[0], amax[0])
                        for y in (amin[1], amax[1])
                        for z in (amin[2], amax[2])])
    world = model_to_world(corners)
    sx, sy, w_cam = project(world)
    require(bool(np.all(w_cam > 0)), 'glb_bbox_behind_camera', w_cam.tolist())
    # the projected box must land on the canvas (Voyager frames its subject)
    require(bool(0 <= sx.min() < width and sx.max() >= 0
                 and 0 <= sy.min() < height and sy.max() >= 0),
            'glb_bbox_offscreen', (sx.tolist(), sy.tolist()))
    # background from the document setups[0].background radial gradient
    bg = doc['setups'][0].get('background', {})
    c0 = np.array(bg.get('color0', [0.2, 0.25, 0.3])) * 255
    c1 = np.array(bg.get('color1', [0.01, 0.03, 0.05])) * 255
    yy, xx = np.mgrid[0:height, 0:width]
    r = np.sqrt(((xx - (width - 1) / 2) / ((width - 1) / 2)) ** 2
                + ((yy - (height - 1) / 2) / ((height - 1) / 2)) ** 2)
    t = np.clip(r, 0, 1)
    img = (c1[None, None, :] * t[..., None] + c0[None, None, :] * (1 - t[..., None]))
    canvas = Canvas(width, height)
    canvas.buf = bytearray(np.clip(img, 0, 255).astype(np.uint8).tobytes())
    edges = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7),
             (0, 4), (1, 5), (2, 6), (3, 7)]
    pts = list(zip(sx.round().astype(int), sy.round().astype(int)))
    for ia, ib in edges:
        canvas.line(*pts[ia], *pts[ib], (240, 220, 160))
    for x, y in pts:
        canvas.marker(x, y, 2, (255, 255, 255))
    # the document-declared model bounding box for comparison (olive frame)
    bb = doc['models'][0].get('boundingBox')
    if bb:
        bmin, bmax = np.array(bb['min']), np.array(bb['max'])
        corners2 = np.array([(x, y, z) for x in (bmin[0], bmax[0])
                             for y in (bmin[1], bmax[1])
                             for z in (bmin[2], bmax[2])])
        world2 = model_to_world(corners2)
        sx2, sy2, w2 = project(world2)
        if bool(np.all(w2 > 0)):
            pts2 = list(zip(sx2.round().astype(int),
                            sy2.round().astype(int)))
            for ia, ib in edges:
                canvas.line(*pts2[ia], *pts2[ib], (120, 120, 90))
    band_y = height - 31
    canvas.rect(0, band_y, width - 1, height - 1, (0, 0, 0))
    canvas.text(3, band_y + 3, PROOF_LABEL, (255, 255, 255))
    canvas.text(3, band_y + 12, 'GLB GEOMETRY DRACO-COMPRESSED: DECODE',
                (255, 255, 255))
    canvas.text(3, band_y + 20, 'REFUSED - BBOX INTAKE ONLY', (255, 160, 90))
    metrics = {
        'accessor_min': status['accessors']['position_min'],
        'accessor_max': status['accessors']['position_max'],
        'position_count': status['accessors']['position_count'],
        'index_count': status['accessors']['index_count'],
        'draco': status['draco'], 'camera': cam_meta,
        'geometry_decode': status['geometry_decode'],
        'refusal_cause': status['refusal_cause'],
    }
    return canvas.png(), metrics


# ---------------------------------------------------------------------------
# 2D plot scaffolding (shared by the scatter and the traces)
# ---------------------------------------------------------------------------

def _nice_ticks(lo, hi, max_ticks=6):
    span = hi - lo
    require(span > 0, 'plot_span', (lo, hi))
    step = max(1, int(math.ceil(span / max_ticks)))
    start = int(math.ceil(lo))
    return list(range(start, int(math.floor(hi)) + 1, step))


class Plot:
    def __init__(self, size=SIZE, margins=(38, 6, 24, 30)):
        self.w, self.h = size
        self.ml, self.mt, self.mr, self.mb = margins
        self.canvas = Canvas(self.w, self.h)
        self.plot_w = self.w - self.ml - self.mr
        self.plot_h = self.h - self.mt - self.mb

    def map(self, x, y, xr, yr):
        fx = (x - xr[0]) / (xr[1] - xr[0])
        fy = (y - yr[0]) / (yr[1] - yr[0])
        return (int(round(self.ml + fx * self.plot_w)),
                int(round(self.mt + (1 - fy) * self.plot_h)))

    def frame(self, xlabel, ylabel, title, xr, yr, xticks, xlog=False,
              yticks=None, ylog=False):
        c = self.canvas
        left, top = self.ml, self.mt
        right, bottom = self.ml + self.plot_w, self.mt + self.plot_h
        c.line(left, top, right, top, (0, 0, 0))
        c.line(right, top, right, bottom, (0, 0, 0))
        c.line(right, bottom, left, bottom, (0, 0, 0))
        c.line(left, bottom, left, top, (0, 0, 0))
        for v in xticks:
            x, _ = self.map(v, yr[0], xr, yr)
            c.line(x, bottom, x, bottom + 3, (0, 0, 0))
            label = f'1E{v}' if xlog else str(v)
            c.text(x - 3 * len(label), bottom + 5, label)
        for v in (yticks if yticks is not None else _nice_ticks(yr[0], yr[1])):
            _, y = self.map(xr[0], v, xr, yr)
            c.line(left - 3, y, left, y, (0, 0, 0))
            label = f'1E{v}' if ylog else str(v)
            c.text(left - 3 - 6 * len(label), y - 3, label)
        c.text(left + self.plot_w // 2 - 3 * len(xlabel), self.h - 8, xlabel)
        c.text(2, 2, title)
        self._vlabel(ylabel)

    def _vlabel(self, text):
        c = self.canvas
        x = self.ml - 26
        y0 = self.mt + self.plot_h // 2 - 4 * len(text) // 2
        for i, ch in enumerate(text.upper()):
            if ch == ' ':
                continue
            c.text(x, y0 + i * 8, ch)

    def polyline(self, pts, color):
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            self.canvas.line(xa, ya, xb, yb, color)

    def points(self, pts, color, r=0):
        for x, y in pts:
            if r:
                self.canvas.marker(x, y, r, color)
            else:
                self.canvas.px(x, y, color)

    def label_band(self, lines):
        c = self.canvas
        h = 9 * len(lines) + 4
        c.rect(0, 0, self.w - 1, h - 1, (0, 0, 0))
        for i, ln in enumerate(lines):
            c.text(3, 2 + i * 9, ln, (255, 255, 255))


# ---------------------------------------------------------------------------
# Render: PanTHERIA Macaca BMR vs mass, log-log (proof of intake)
# ---------------------------------------------------------------------------

PANTHERIA_MEMBER = 'PanTHERIA_1-0_WR05_Aug2008.txt'
COL_GENUS = 'MSW05_Genus'
COL_SPECIES = 'MSW05_Binomial'
COL_MASS = '5-1_AdultBodyMass_g'
COL_BMR = '18-1_BasalMetRate_mLO2hr'


def load_pantheria(zip_path):
    import zipfile
    with zipfile.ZipFile(zip_path) as zf:
        names = [n for n in zf.namelist() if n.endswith(PANTHERIA_MEMBER)]
        require(len(names) == 1, 'pantheria_member', names)
        text = zf.read(names[0]).decode('latin-1')
    reader = io.StringIO(text)
    header = reader.readline().rstrip('\r\n').split('\t')
    cloud = []
    macaca = []
    mulatta = None
    n_rows = 0
    for line in reader:
        line = line.rstrip('\r\n')
        if not line:
            continue
        n_rows += 1
        row = dict(zip(header, line.split('\t')))
        try:
            mass = float(row[COL_MASS])
            bmr = float(row[COL_BMR])
        except ValueError:
            continue
        if mass <= 0 or bmr <= 0:
            continue
        pt = (math.log10(mass), math.log10(bmr))
        cloud.append(pt)
        if row[COL_GENUS] == 'Macaca':
            macaca.append((row[COL_SPECIES], mass, bmr, pt))
            if row[COL_SPECIES] == 'Macaca mulatta':
                mulatta = (mass, bmr)
    require(cloud, 'pantheria_empty', '')
    require(macaca, 'pantheria_no_macaca', '')
    return {'rows': n_rows, 'cloud': cloud, 'macaca': macaca,
            'mulatta': mulatta}


def render_pantheria(zip_path):
    data = load_pantheria(zip_path)
    cloud = data['cloud']
    xr = (math.floor(min(p[0] for p in cloud)),
          math.ceil(max(p[0] for p in cloud)))
    yr = (math.floor(min(p[1] for p in cloud)),
          math.ceil(max(p[1] for p in cloud)))
    plot = Plot()
    plot.frame('LOG10 ADULT BODY MASS (G)', 'LOG10 BMR (ML O2/HR)',
               'PANTHERIA: BMR VS MASS', xr, yr,
               list(range(xr[0], xr[1] + 1)), xlog=True, ylog=True)
    plot.points([plot.map(*p, xr, yr) for p in cloud], (150, 150, 150))
    mac_pts = []
    for _sp, _m, _b, pt in sorted(data['macaca']):
        mac_pts.append(plot.map(*pt, xr, yr))
    plot.points(mac_pts, (0, 0, 0), r=3)
    if data['mulatta']:
        mx, my = plot.map(math.log10(data['mulatta'][0]),
                          math.log10(data['mulatta'][1]), xr, yr)
        plot.canvas.marker(mx, my, 4, (180, 0, 0))
    plot.label_band([
        'PROOF-OF-INTAKE: NOT PHYSICS VERIFICATION',
        f"PANTHERIA MACACA BMR VS MASS (LOG-LOG) N={len(data['macaca'])}"
        f' OF {data["rows"]} ROWS',
        'GREY: ALL DUAL-MEASURED; RED: MACACA MULATTA',
    ])
    return plot.canvas.png(), {
        'rows': data['rows'], 'dual_measured': len(cloud),
        'macaca_dual_measured': len(data['macaca']),
        'macaca_species': sorted(sp for sp, _m, _b, _p in data['macaca']),
        'mulatta_mass_g': data['mulatta'][0] if data['mulatta'] else None,
        'mulatta_bmr_ml_o2_hr': data['mulatta'][1] if data['mulatta'] else None,
    }


# ---------------------------------------------------------------------------
# Render: terrain shaded relief at the Luquillo control
# ---------------------------------------------------------------------------

LUQUILLO = (18.425, -65.95)
DATA_DIR = Path(__file__).resolve().parent / 'data'
DEM_PATH = DATA_DIR / 'copernicus_glo30' / \
    'Copernicus_DSM_COG_10_N18_00_W066_00_DEM.tif'
GEOID_PATH = DATA_DIR / 'nga_egm08' / 'us_nga_egm08_25.tif'
HALF = 100  # 201x201 samples ~ 6 km at GLO-30 spacing


def render_terrain(dem_path=DEM_PATH, geoid_path=GEOID_PATH,
                   centre=LUQUILLO, half=HALF):
    from . import terrain as T
    gt = T.geotransform(str(dem_path))
    row_f, col_f = T.rowcol_of(gt, centre[0], centre[1])
    r0, c0 = round(row_f), round(col_f)
    samples = [(rr, cc)
               for rr in range(r0 - half, r0 + half + 1)
               for cc in range(c0 - half, c0 + half + 1)]
    values = T.sample_grid(str(dem_path), samples, T.DEM_RANGE)
    grid = np.empty((2 * half + 1, 2 * half + 1), dtype=np.float64)
    for (rr, cc), v in values.items():
        grid[rr - (r0 - half), cc - (c0 - half)] = v
    require(not np.any(grid == T.NODATA), 'terrain_nodata_in_window', '')
    m_per_lat = gt['d_lat'] * math.pi / 180 * T.radii(centre[0])[0]
    m_per_lon = gt['d_lon'] * math.pi / 180 * T.radii(centre[0])[1] \
        * math.cos(math.radians(centre[0]))
    dzdy, dzdx = np.gradient(grid, m_per_lat, m_per_lon)
    normal = np.dstack([-dzdx, -dzdy, np.ones_like(grid)])
    norm = np.linalg.norm(normal, axis=2, keepdims=True)
    normal = normal / norm
    az, el = math.radians(315.0), math.radians(45.0)
    sun = np.array([math.sin(az) * math.cos(el), math.cos(az) * math.cos(el),
                    math.sin(el)])
    shade = np.clip(normal @ sun, 0.0, None)
    gray = np.clip(25 + 230 * shade, 0, 255).astype(np.uint8)
    h, w = gray.shape
    canvas = Canvas(w, h)
    canvas.buf = bytearray(np.dstack([gray, gray, gray]).tobytes())
    for d in range(-3, 4):
        canvas.px(w // 2 + d, h // 2, (220, 40, 40))
        canvas.px(w // 2, h // 2 + d, (220, 40, 40))
    band_y = h - 31
    canvas.rect(0, band_y, w - 1, h - 1, (0, 0, 0))
    canvas.text(3, band_y + 3, PROOF_LABEL, (255, 255, 255))
    canvas.text(3, band_y + 12,
                'GLO-30 SHADED RELIEF AT LUQUILLO CONTROL (18.425 -65.95)',
                (255, 255, 255))
    canvas.text(3, band_y + 20, 'SUN AZ 315 EL 45; RED CROSS = CONTROL',
                (255, 255, 255))
    reduction = T.reduce_terrain(str(dem_path), str(geoid_path),
                                 *centre, patch_metres=2.4)
    metrics = {
        'window_samples': [w, h], 'centre': list(centre),
        'dem_rows_cols': [r0, c0],
        'H_orthometric_m': reduction['H_orthometric_m'],
        'N_geoid_m': reduction['N_geoid_geodetic_m'],
        'h_ellipsoidal_m': reduction['h_ellipsoidal_m'],
        'geoid_method_gap_m': reduction['geoid_method_gap_m'],
        'theta_deg': reduction['plane']['theta_deg'],
    }
    return canvas.png(), metrics


# ---------------------------------------------------------------------------
# Render: Janisch stride angle traces (angle-angle, MID substrate)
# ---------------------------------------------------------------------------

PALETTE = [
    (31, 119, 180), (255, 127, 14), (44, 160, 44), (214, 39, 40),
    (148, 103, 189), (140, 86, 75), (227, 119, 194), (127, 127, 127),
    (188, 189, 34), (23, 190, 207), (0, 0, 0), (102, 0, 153),
    (0, 109, 44), (255, 215, 0),
]


def load_janisch(csv_path):
    import csv
    text = Path(csv_path).read_text(encoding='utf-8-sig')
    rows = list(csv.DictReader(io.StringIO(text)))
    traces = {}
    for row in rows:
        try:
            hip = float(row.get('hipMID'))
            knee = float(row.get('kneeMID'))
        except (ValueError, TypeError):
            continue  # NA -- honest gap, never filled
        key = (row['Species'], row['Video'])
        traces.setdefault(key, []).append(
            (int(row['stridenumber']), hip, knee))
    require(traces, 'janisch_empty', '')
    out = {}
    for (species, video), items in traces.items():
        out.setdefault(species, {})[video] = [
            (h, k) for _s, h, k in sorted(items)]
    return out


def render_gait(csv_path):
    traces = load_janisch(csv_path)
    hips = [h for sp in traces.values() for v in sp.values() for h, _k in v]
    knees = [k for sp in traces.values() for v in sp.values()
             for _h, k in v]
    xr = (math.floor(min(hips) / 10) * 10, math.ceil(max(hips) / 10) * 10)
    yr = (math.floor(min(knees) / 10) * 10, math.ceil(max(knees) / 10) * 10)
    plot = Plot()
    plot.frame('HIP ANGLE MID (DEG)', 'KNEE ANGLE MID (DEG)',
               'JANISCH STRIDE ANGLE TRACES', xr, yr,
               _nice_ticks(xr[0], xr[1]), xlog=False, ylog=False)
    species = sorted(traces)
    polylines = 0
    for idx, sp in enumerate(species):
        color = PALETTE[idx % len(PALETTE)]
        for video in sorted(traces[sp]):
            pts = [plot.map(h, k, xr, yr)
                   for h, k in sorted(traces[sp][video])]
            if len(pts) > 1:
                plot.polyline(pts, color)
                polylines += 1
            plot.points(pts, color, r=1)
    plot.label_band([
        'PROOF-OF-INTAKE: NOT PHYSICS VERIFICATION',
        f'HIP VS KNEE (MID) PER STRIDE; {len(species)} SPECIES,'
        f' {polylines} VIDEOTRACES',
        'NA ANGLES SKIPPED (HONEST GAPS, NEVER FILLED)',
    ])
    return plot.canvas.png(), {
        'species': species,
        'strides_plotted': sum(len(v) for sp in traces.values()
                               for v in sp.values()),
        'video_traces': polylines,
        'xr_deg': list(xr), 'yr_deg': list(yr),
    }


# ---------------------------------------------------------------------------
# Orchestration: manifest with the input sha256 -> png sha256 chain
# ---------------------------------------------------------------------------

def _sha256_file(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for block in iter(lambda: fh.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def build_renders(smithsonian_dir, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    smithsonian_dir = Path(smithsonian_dir)
    import hashlib
    renders = []
    refusals = []
    repo_root = Path(__file__).resolve().parents[2]

    def emit(rid, png_bytes, metrics, inputs, params):
        name = f'{rid}.png'
        (out / name).write_bytes(png_bytes)
        renders.append({
            'id': rid, 'png': name,
            'png_sha256': hashlib.sha256(png_bytes).hexdigest(),
            'inputs': [{'role': role,
                        'path': str(Path(p).resolve().relative_to(repo_root))
                        .replace('\\', '/'),
                        'sha256': _sha256_file(p)} for role, p in inputs],
            'params': params, 'metrics': metrics,
        })

    # --- smithsonian pair: intake render of what the pinned bytes admit ---
    for rid, glb_name, doc_name, label in (
            ('smithsonian_usnm15259_cranium',
             'USNM15259_cranium_-300_dec-150k-4096-high.glb',
             'USNM15259_cranium_document.json', 'USNM 15259 CRANIUM'),
            ('smithsonian_usnm15259_mandible',
             'USNM15259_mandible_-300-150k-4096-high.glb',
             'USNM15259_mandible_document.json', 'USNM 15259 MANDIBLE')):
        glb = smithsonian_dir / glb_name
        doc = smithsonian_dir / doc_name
        png, metrics = render_glb_intake(glb, doc)
        emit(rid, png, metrics,
             [('geometry_glb', glb), ('camera_document', doc),
              ('download_receipt', smithsonian_dir / 'download_receipt.json')],
             {'renderer': 'accessor-bbox wireframe under the document.json '
                          'camera (320x240); geometry decode REFUSED '
                          '(draco edgebreaker, see refusal_cause)',
              'specimen': label})
        refusals.append({
            'id': rid, 'cause': metrics['refusal_cause'],
            'detail': metrics['draco'],
            'evidence': 'smithsonian_glb_status() in visual_proof.py; '
                        'google/draco HEAD and 1.3.6 reference layouts '
                        'both fail the pinned event stream',
        })

    pantheria_zip = DATA_DIR / 'pantheria' / 'ECOL_90_184.zip'
    png, metrics = render_pantheria(pantheria_zip)
    emit('pantheria_macaca_bmr_vs_mass', png, metrics,
         [('dataset', pantheria_zip),
          ('download_receipt',
           DATA_DIR / 'pantheria' / 'download_receipt.json')],
         {'x': COL_MASS, 'y': COL_BMR, 'scale': 'log10-log10',
          'filter': 'genus Macaca', 'size': list(SIZE)})

    png, metrics = render_terrain()
    emit('terrain_luquillo_relief', png, metrics,
         [('dem', DEM_PATH), ('geoid', GEOID_PATH)],
         {'centre': list(LUQUILLO), 'half_samples': HALF,
          'sun': 'az 315 deg, el 45 deg',
          'reduction_law': 'terrain.reduce_terrain (7-step, recorded)'})

    gait_csv = DATA_DIR / 'janisch_kinematics' / 'wildprimate_kin.csv'
    png, metrics = render_gait(gait_csv)
    emit('janisch_stride_angle_traces', png, metrics,
         [('strides', gait_csv),
          ('download_receipt',
           DATA_DIR / 'janisch_kinematics' / 'download_receipt.json')],
         {'joints': ['hipMID', 'kneeMID'],
          'trace': 'per species+video, stride order'})

    manifest = {
        'kind': 'visual_proof_manifest.v1',
        'label': 'PROOF-OF-INTAKE renders: visual evidence that the pinned '
                 'admitted library data decodes and renders. NOT physics '
                 'verification, NOT qualification.',
        'work_item': 'work.data.visual_proof_20260917',
        'falsified_assumptions': [
            'Pure-struct GLB geometry decode is impossible: the pinned '
            'artifacts REQUIRE KHR_draco_mesh_compression.',
            'A sequential-draco decode was assumed next; the pinned streams '
            'are draco EDGEBREAKER (method 1, VALENCE traversal type 2, '
            'bitstream 2.2).',
            'The topology-split event section does not parse under '
            'google/draco HEAD or 1.3.6 reference layouts; the producer '
            'variant is unidentified; geometry decode REFUSED (see '
            'refusals). The smithsonian renders therefore show the '
            'accessor-declared bounding boxes only.',
        ],
        'refusals': refusals,
        'producer': {
            'python': sys.version.split()[0],
            'zlib': zlib.ZLIB_VERSION,
            'numpy': np.__version__,
            'module_sha256': _sha256_file(Path(__file__)),
        },
        'renders': renders,
    }
    (out / 'manifest.json').write_bytes(
        (json.dumps(manifest, indent=1) + '\n').replace('\n', '\r\n')
        .encode('utf-8'))
    return manifest


def verify(out_dir):
    """Re-render everything and require byte-identical PNGs + intact chain."""
    out = Path(out_dir)
    manifest = json.loads((out / 'manifest.json').read_text('utf-8'))
    root = Path(__file__).resolve().parents[2]
    fresh = build_renders(root / 'tools' / 'science_funnel' / 'data'
                          / 'smithsonian', out)
    require([r['id'] for r in manifest['renders']]
            == [r['id'] for r in fresh['renders']], 'verify_render_set', '')
    results = []
    for recorded, new in zip(manifest['renders'], fresh['renders']):
        require(recorded['id'] == new['id'], 'verify_render_id',
                recorded['id'])
        png_path = out / recorded['png']
        require(recorded['png_sha256'] == new['png_sha256'],
                're_render_byte_identical', recorded['id'])
        require(_sha256_file(png_path) == recorded['png_sha256'],
                'png_hash_chain', recorded['png'])
        for entry in recorded['inputs']:
            require(_sha256_file(root / entry['path']) == entry['sha256'],
                    'input_hash_chain', entry['path'])
        results.append(recorded['id'])
    return results


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    root = Path(__file__).resolve().parents[2]
    out_default = root / 'tools' / 'science_funnel' / 'validation' / \
        'visual_proof_20260917'
    if '--verify' in argv:
        out = Path(argv[argv.index('--out') + 1]) if '--out' in argv \
            else out_default
        for rid in verify(out):
            print(f'VERIFIED {rid}: re-render byte-identical, chain intact')
        return 0
    out = Path(argv[argv.index('--out') + 1]) if '--out' in argv \
        else out_default
    smith = Path(argv[argv.index('--smithsonian') + 1]) \
        if '--smithsonian' in argv else DATA_DIR / 'smithsonian'
    manifest = build_renders(smith, out)
    for r in manifest['renders']:
        print(f"RENDERED {r['id']} -> {r['png']} {r['png_sha256'][:12]}")
    for rf in manifest['refusals']:
        print(f"REFUSED {rf['id']}: {rf['cause']}")
    return 0


# Wave-2 extension is lazy-loaded to preserve the original public API and
# avoid a circular import: visual_proof_wave2 reuses Canvas and Plot here.
def build_wave2_renders(out_dir):
    from .visual_proof_wave2 import build_wave2_renders as _build
    return _build(out_dir)


def verify_wave2(out_dir):
    from .visual_proof_wave2 import verify_wave2 as _verify
    return _verify(out_dir)


if __name__ == '__main__':
    raise SystemExit(main())
