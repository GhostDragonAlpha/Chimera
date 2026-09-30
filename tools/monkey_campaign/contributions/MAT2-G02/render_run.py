"""{{CARD_FULL}} visual capture renderer - card-kit REFERENCE STUB.

Copy-adapted from the merged MAT2-M08 render_run.py. This stub keeps the
card-INDEPENDENT parts verbatim (the registry 16-field camera record, the
binding assertion discipline, the fixed-bookmark law) and marks the
card-specific rendering body as FILL. It is a reference, not a working
renderer: replace render_body_for_tick with your geometry.

Non-negotiable laws kept from M08:
  - FIXED BOOKMARKS: the camera never moves; the SUBJECT moves. Every
    sample carries position, target, distance, orientation (quaternion
    wxyz camera-to-frame) at EVERY snapshot tick - identical pose, declared
    sample_mode 'fixed_bookmark'.
  - 16 registry camera fields, always: frame_id, coordinate_unit,
    handedness, orientation_convention, forward_axis, up_axis,
    near_far_planes, viewport_resolution, aspect_ratio, projection,
    sample_mode, samples, camera_motion_or_bookmark_sequence,
    state_or_tick_interval, + vertical_fov_degrees OR orthographic_span.
  - BINDING ASSERTION: rendered geometry must reproduce the snapshot's own
    diagnostic volume (or your world's equivalent invariant) BEFORE any
    pixel is written: require(..., 'render_replay_diverged_from_gpu_...').
  - Deterministic render (no wall-clock, no RNG); frames + evidence written
    to the attempt capture directory passed as argv[1]; frame hashes to
    evidence/frame_hashes.json; camera records to evidence/cameras.json.
  - Secondary cameras (side+front pairs) are FULLY declared with the same
    16 fields, never partially.
  - Diagnostic layers and labels are RENDERED, not merely claimed (hidden
    constraint/support is a profile falsifier: render and label the pinned
    support and anchors).
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent

W_VP, H_VP = 640, 360
ASPECT = 16.0 / 9.0
SHEET = (4 * W_VP, 2 * H_VP + 120)     # FILL: your sheet layout
VIEW_IDS = []                           # FILL: the registry view ids
LAYERS = []                             # FILL: the registry diagnostic layers
TICK_MAP = ('FILL: units per tick; frames are the declared snapshot ticks '
            'at 1 video second per frame')

CARD_FULL = '{{CARD_FULL}}'
if CARD_FULL.startswith('{{'):
    raise SystemExit('render_run_template.py is UNFILLED: replace the '
                     '{{...}} placeholders before running.')


def require(condition, code):
    if not condition:
        raise ValueError(code)


def mat_to_quat(m):
    """Rotation matrix -> quaternion (wxyz, camera-to-frame). Verbatim M08
    helper (card-independent math; keep)."""
    t = m[0, 0] + m[1, 1] + m[2, 2]
    if t > 0.0:
        s = math.sqrt(t + 1.0) * 2.0
        w = 0.25 * s
        x = (m[2, 1] - m[1, 2]) / s
        y = (m[0, 2] - m[2, 0]) / s
        z = (m[1, 0] - m[0, 1]) / s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2.0
        w = (m[2, 1] - m[1, 2]) / s
        x = 0.25 * s
        y = (m[0, 1] + m[1, 0]) / s
        z = (m[1, 0] + m[0, 1]) / s
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2.0
        w = (m[0, 2] - m[2, 0]) / s
        x = (m[0, 1] + m[2, 1]) / s
        y = 0.25 * s
        z = (m[1, 2] + m[2, 1]) / s
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2.0
        w = (m[1, 0] - m[0, 1]) / s
        x = (m[0, 2] + m[2, 0]) / s
        y = (m[1, 2] + m[2, 1]) / s
        z = 0.25 * s
    q = np.array([w, x, y, z], dtype=np.float64)
    return [float(c) for c in q / np.linalg.norm(q)]


class Camera:
    """Fixed-bookmark camera with the full registry record. Keep verbatim;
    FILL only the camera constructions in main()."""

    def __init__(self, name, position, target, resolution, projection,
                 fov_degrees=None, span=None):
        self.name = name
        self.position = np.array(position, dtype=np.float64)
        self.target = np.array(target, dtype=np.float64)
        self.resolution = list(resolution)
        self.projection = projection
        self.fov = fov_degrees
        self.span = span
        f = self.target - self.position
        self.dist = float(np.linalg.norm(f))
        self.forward = f / self.dist
        w = np.array([0.0, 0.0, 1.0])
        r = np.cross(self.forward, w)
        r = r / np.linalg.norm(r)
        up = np.cross(r, self.forward)
        self.right, self.up = r, up
        self._m = np.column_stack([r, up, -self.forward])
        self.quat = mat_to_quat(self._m)

    def project(self, points):
        pts = np.atleast_2d(np.asarray(points, dtype=np.float64))
        rel = pts - self.position
        x = rel @ self.right
        y = rel @ self.up
        z = rel @ (-self.forward)
        w_px, h_px = self.resolution
        if self.projection == 'perspective':
            t = math.tan(math.radians(self.fov) / 2.0)
            depth = z
            px = w_px / 2.0 + (x / (z * t * ASPECT)) * (w_px / 2.0)
            py = h_px / 2.0 - (y / (z * t)) * (h_px / 2.0)
        else:
            depth = z
            scale = h_px / self.span
            px = w_px / 2.0 + x * scale
            py = h_px / 2.0 - y * scale
        return np.column_stack([px, py]), depth

    def record(self, ticks):
        samples = []
        for tick in ticks:
            samples.append({
                'tick': int(tick),
                'position': [float(c) for c in self.position],
                'target': [float(c) for c in self.target],
                'distance_to_target': self.dist,
                'orientation': list(self.quat),
            })
        rec = {
            'frame_id': '{{CARD_ID_LOWER}}_resident_' + self.name
                        + '_canvas_m',
            'coordinate_unit': 'm',
            'handedness': 'right',
            'orientation_convention': 'quaternion_wxyz_camera_to_frame',
            'forward_axis': '-Z',
            'up_axis': '+Y',
            'near_far_planes': [0.01, 100.0],
            'viewport_resolution': list(self.resolution),
            'aspect_ratio': ASPECT,
            'projection': self.projection,
            'sample_mode': 'fixed_bookmark',
            'samples': samples,
            'camera_motion_or_bookmark_sequence':
                'fixed_bookmark: identical pose at every snapshot tick; '
                'the SUBJECT moves, not the camera',
            'state_or_tick_interval': TICK_MAP,
        }
        if self.projection == 'perspective':
            rec['vertical_fov_degrees'] = self.fov
        else:
            rec['orthographic_span'] = self.span
        return rec


def main():
    out_dir = pathlib.Path(sys.argv[1])
    frames_dir = out_dir / 'frames'
    evidence_dir = out_dir / 'evidence'
    frames_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    receipt = json.loads((HERE / 'experiment_receipt.json').read_text(
        encoding='utf-8'))
    snaps = receipt['snapshots']

    # FILL: your cameras - whole/side/front/closeup with DECLARED poses;
    # distance, projection, fov/span chosen so the subject fills the frame
    # without clipping the load path (profile falsifier: clipped load path).
    cams = {
        'whole': Camera('whole', (0, -1, 0.4), (0, 0, 0),
                        [W_VP, H_VP], 'perspective', fov_degrees=42.0),
    }
    try:
        fonts = {'title': ImageFont.load_default(14),
                 'small': ImageFont.load_default(11),
                 'footer': ImageFont.load_default(12)}
    except Exception:
        fonts = {'title': None, 'small': None, 'footer': None}

    snap_ticks = sorted(int(k) for k in snaps.keys())
    frame_hashes = {}
    for frame_no, tick in enumerate(snap_ticks):
        snap = snaps[str(tick)]
        verts = np.array(snap['FILL_SNAPSHOT_VERT_KEY'], dtype=np.float64)
        gblock = snap['gpu_block']
        # FILL: build your renderable from the GPU-solved snapshot ...
        # BINDING ASSERTION (keep the discipline; swap in your invariant):
        # require(abs(renderable.signed_volume() - gblock[VOL_SLOT]) < 1e-15,
        #         'render_replay_diverged_from_gpu_snapshot')
        img = Image.new('RGB', SHEET, (252, 252, 250))
        draw = ImageDraw.Draw(img)
        # FILL: render_body_for_tick(draw, cams, snap, fonts) - diagnostic
        # row (all declared layers, labels RENDERED, support/anchors drawn
        # AND labeled), clean row (identical cameras, geometry only),
        # trace strip + honest footer (residency evidence).
        draw.text((6, 4), f'{{{{CARD_ID}}}} tick {tick} - FILL renderer',
                  fill=(20, 20, 20), font=fonts['title'])
        frame_path = frames_dir / f'frame_{frame_no:02d}.png'
        img.save(frame_path)
        frame_hashes[str(tick)] = hashlib.sha256(
            frame_path.read_bytes()).hexdigest()
    # CRLF law: byte-level writes (write_text translates \n to
    # os.linesep on Windows)
    (evidence_dir / 'frame_hashes.json').write_bytes(
        json.dumps(frame_hashes, indent=1, sort_keys=True).encode('utf-8'))
    cameras = {f'{name}:{mode}': [cam.record(snap_ticks)]
               for name, cam in cams.items()
               for mode in ('diagnostic', 'clean')}
    (evidence_dir / 'cameras.json').write_bytes(
        json.dumps(cameras, indent=1, sort_keys=True).encode('utf-8'))
    print('frames:', len(snap_ticks), 'ticks:', snap_ticks)


if __name__ == '__main__':
    main()
