"""K01 capture card renderer: deterministic synthetic sidecar fixture views.

Card-owned capture script per capture-gate-template README step 3. The
``render`` callback returns (beauty, mask) uint8 (h, w, 3) pairs; the mask
buffer is a SEPARATE object-ID channel painted from the card view-spec's
per-object ``mask_code`` constants and is never composited into beauty.

HONEST PROVENANCE OF THE PIXELS: every rendered scene state is a fixture
projection of RECORDED run state (pad vertex sets, pad contact modes,
measured pad displacements, the declared approach terminal pose) captured
from the K01 battery trace in the same process. Nothing is invented at
render time: a state field that is absent switches the corresponding
content off (pads/base/diag layer), it never falls back to a synthetic
constant. This is a rendered fixture view (the G04 heritage pattern), not a
screenshot substitute; the profile's numerical evidence is the receipt suite.

Defect injection exists ONLY to prove the normal pipeline rejects the four
planted defect classes through THIS card's spec (fixture-only, same classes
as the VISUAL-GATE-1 suite):

- WRONG_BODY_COLOR_SHARE: pad_1 renders (mask intact) but its beauty pixels
  carry pad_0's current palette color. Co-location kills it.
- SHARED_COLOR_INFLATION_ABSENT: pad_1 truly absent while a small band of
  the trunk silhouette carries pad_1's exact base color (totals inflate;
  the pad_1 mask floor kills it; the trunk band stays under the
  co-location floor so the isolated failure mode stays readable).
- SUBJECT_ABSENT: pad_2 is not rendered at all.
- UNDECLARED_OCCLUSION: in detail_clean (which declares pad_0 VISIBLE with
  a floor and pad_2 as the only occluded subject) pad_0 is force-drawn as
  if it were the front-most pad: the class never preregistered that
  arrangement, so the occluded-subject-visible accounting bites.

CPU-only, stdlib + numpy, deterministic (no RNG, no wall clock).
"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

FRAME_WH = [320, 240]

# view_class name -> (family, diagnostic) ; families declared in the spec.
_FAMILIES = ("normal", "detail", "alternate")


def load_card_spec():
    """Load and validate the card view-spec (fresh per call; no cache)."""
    from capture_gate import view_spec
    with open(os.path.join(HERE, "view_spec.json"), "rb") as handle:
        return view_spec.load_spec(json.loads(handle.read().decode("utf-8")))


def _project(view, p):
    """Declared orthographic camera: phi azimuth, elev elevation, scale.

    right = (-sin phi, cos phi, 0); up = (-sin el cos phi, -sin el sin phi,
    cos el); view dir (into the scene) = (-cos el cos phi, -cos el sin phi,
    -sin el). Returns (image_x_px, image_y_px, depth_m) with image y down.
    """
    phi = math.radians(view["phi_deg"])
    el = math.radians(view["elev_deg"])
    cp, sp, ce, se = math.cos(phi), math.sin(phi), math.cos(el), math.sin(el)
    cx, cy, cz = view["center_xyz"]
    s = view["scale_px_per_m"]
    icx, icy = view["image_center_px"]
    rx, ry = -sp, cp
    ux, uy, uz = -se * cp, -se * sp, ce
    dx, dy, dz = -ce * cp, -ce * sp, -se
    rel = (p[0] - cx, p[1] - cy, p[2] - cz)
    x = rel[0] * rx + rel[1] * ry
    y = rel[0] * ux + rel[1] * uy + rel[2] * uz
    d = rel[0] * dx + rel[1] * dy + rel[2] * dz
    return (icx + s * x, icy - s * y, d)


def _px(v):
    return int(math.floor(v + 0.5))


def _hull_pixels(pts):
    """Convex-hull rasterization (monotone chain), inclusive fill."""
    pts = sorted(set(pts))
    if len(pts) <= 2:
        return _seg_pixels(pts[0], pts[-1], 0.6) if pts else []

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    out = []
    for i in range(1, len(hull) - 1):
        out.extend(_tri_pixels(hull[0], hull[i], hull[i + 1]))
    return out


def _tri_pixels(a, b, c):
    """Triangle rasterization: inclusive edge-function fill over the bbox."""
    xs = [a[0], b[0], c[0]]
    ys = [a[1], b[1], c[1]]
    x0, x1 = max(0, _px(min(xs))), min(FRAME_WH[0] - 1, _px(max(xs)) + 1)
    y0, y1 = max(0, _px(min(ys))), min(FRAME_WH[1] - 1, _px(max(ys)) + 1)
    if x0 > x1 or y0 > y1:
        return []
    ax, ay = a
    bx, by = b
    cx, cy = c
    det = (bx - ax) * (cy - ay) - (cx - ax) * (by - ay)
    if det == 0.0:
        return []
    out = []
    for yy in range(y0, y1 + 1):
        for xx in range(x0, x1 + 1):
            w1 = ((xx - ax) * (cy - ay) - (cx - ax) * (yy - ay)) / det
            w2 = ((bx - ax) * (yy - ay) - (xx - ax) * (by - ay)) / det
            w0 = 1.0 - w1 - w2
            if w0 >= -1e-9 and w1 >= -1e-9 and w2 >= -1e-9:
                out.append((xx, yy))
    return out


def _disc_pixels(center, radius):
    cx, cy = center
    x0, x1 = max(0, _px(cx - radius)), min(FRAME_WH[0] - 1, _px(cx + radius) + 1)
    y0, y1 = max(0, _px(cy - radius)), min(FRAME_WH[1] - 1, _px(cy + radius) + 1)
    out = []
    r2 = radius * radius
    for yy in range(y0, y1 + 1):
        for xx in range(x0, x1 + 1):
            dx, dy = xx + 0.0 - cx, yy + 0.0 - cy
            if dx * dx + dy * dy <= r2:
                out.append((xx, yy))
    return out


def _rect_pixels(x0, y0, x1, y1):
    x0, x1 = max(0, _px(x0)), min(FRAME_WH[0] - 1, _px(x1))
    y0, y1 = max(0, _px(y0)), min(FRAME_WH[1] - 1, _px(y1))
    return [(xx, yy) for yy in range(y0, y1 + 1)
            for xx in range(x0, x1 + 1)]


def _seg_pixels(a, b, radius=1.2):
    """Thick segment: stamped discs (hard edges, deterministic)."""
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(1, int(math.ceil(length / (radius * 0.6))))
    out = []
    for i in range(n + 1):
        t = i / n
        out.extend(_disc_pixels(
            (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), radius))
    return out


class _Painter:
    def __init__(self):
        beauty = np.zeros((FRAME_WH[1], FRAME_WH[0], 3), dtype=np.uint8)
        mask = np.zeros((FRAME_WH[1], FRAME_WH[0], 3), dtype=np.uint8)
        self.beauty, self.mask = beauty, mask

    def paint(self, pixels, color, code):
        if not pixels:
            return
        xs = np.fromiter((p[0] for p in pixels), dtype=np.int64)
        ys = np.fromiter((p[1] for p in pixels), dtype=np.int64)
        self.beauty[ys, xs] = color
        if code is not None:
            self.mask[ys, xs] = code


def make_renderer(state, spec):
    """Build the sidecar render callback bound to one recorded case state.

    ``state`` keys (all optional; absent = content not drawn):
      kind: 'contact' | 'approach' | 'geometry'
      pad_verts: [pad][4][3] recorded pad vertex sets (m, M06 frame)
      pad_modes: [pad] 'stick'|'slip' (diagnostic views recolor pads)
      attach/normals: [pad][3] facet centroid + outward normal
      disp: [pad] measured cumulative downward displacement (m)
      base_pos: [3] declared base pose (m)
      d0/d_term/window: approach scaffold script numbers (m)
      span_m/diameter_m/grasp_z: recorded-config geometry numbers (m)
      defect: injected defect label (fixture-only)
    """
    objects = spec["objects"]
    background = spec["background"]
    geom = spec["fixture_geometry"]
    projections = geom["projections"]
    trunk_r = geom["trunk_radius_m"]
    trunk_h = geom["trunk_height_m"]

    defect = state.get("defect")

    def palette(name, idx=0):
        return tuple(objects[name]["beauty_palette"][idx])

    def code_of(name):
        return tuple(objects[name]["mask_code"])

    def pad_color(k, family, diag):
        base = palette("pad_%d" % k, 0)
        if not diag:
            if defect == "WRONG_BODY_COLOR_SHARE" and k == 1:
                return palette("pad_0", 0)
            return base
        modes = state.get("pad_modes") or []
        mode = modes[k] if k < len(modes) else None
        if mode == "stick":
            return palette("pad_%d" % k, 1)
        if mode == "slip":
            return palette("pad_%d" % k, 2)
        if defect == "WRONG_BODY_COLOR_SHARE" and k == 1:
            return palette("pad_0", 1)
        return base

    def render(view_class, frame_id, defect=None):
        del frame_id
        parts = view_class.split("_")
        diag = "diag" in parts
        family = next((f for f in _FAMILIES if f in parts), None)
        if family is None or ("clean" not in parts and not diag):
            raise ValueError("unknown_view_class:" + str(view_class))
        view = projections[family]
        painter = _Painter()
        painter.paint(_rect_pixels(0, 0, FRAME_WH[0] - 1, FRAME_WH[1] - 1),
                      tuple(background["beauty_color"]),
                      tuple(background["mask_code"]))
        shapes = []  # (depth, painter_fn)

        # trunk silhouette (orthographic cylinder: image-space rect)
        p0 = _project(view, (0.0, 0.0, 0.0))
        p1 = _project(view, (0.0, 0.0, trunk_h))
        half = trunk_r * view["scale_px_per_m"]
        tx0, tx1 = p0[0] - half, p0[0] + half
        ty0, ty1 = min(p0[1], p1[1]), max(p0[1], p1[1])
        trunk_paint = (lambda rect=(tx0, ty0, tx1, ty1):
                       _rect_pixels(*rect))
        shapes.append((0.0, trunk_paint, palette("trunk", 0), code_of("trunk")))

        pads = state.get("pad_verts")
        if pads and defect != "SHARED_COLOR_INFLATION_ABSENT" \
                and defect != "SUBJECT_ABSENT":
            inj_angle = None
            if defect == "UNDECLARED_OCCLUSION" and family == "normal":
                # fixture-only: rotate pad_1 (declared occluded in the
                # normal class, measured 30-33 visible px behind the trunk
                # band) to the camera azimuth slot so it renders front-most
                # at ~pad_0's fully-visible count (~120 px > the 90 px
                # bound) -- an arrangement the class never preregistered.
                inj_angle = math.radians(
                    projections["normal"]["phi_deg"]
                    - geom["facet_azimuth_deg"]["pad_1"])
            for k, verts in enumerate(pads):
                if defect == "SUBJECT_ABSENT" and k == 2:
                    continue
                if inj_angle is not None and k == 0:
                    # fixture-only: drop pad_0 in this defect frame so the
                    # rotated pad_1 (same front-center slot) is not hidden
                    # behind pad_0's projection; the defect composes the
                    # fixture scene to prove the gate bites.
                    continue
                quad = [tuple(v) for v in verts]
                if inj_angle is not None and k == 1:
                    quad = [(v[0] * math.cos(inj_angle)
                             - v[1] * math.sin(inj_angle),
                             v[0] * math.sin(inj_angle)
                             + v[1] * math.cos(inj_angle), v[2])
                            for v in quad]
                proj = [_project(view, v) for v in quad]
                depth = sum(p[2] for p in proj) / len(proj)
                pts = [(p[0], p[1]) for p in proj]
                col = pad_color(k, family, diag)
                shapes.append((depth,
                               (lambda poly=pts: _hull_pixels(poly)),
                               col, code_of("pad_%d" % k)))

        base_pos = state.get("base_pos")
        if base_pos is not None and family != "detail":
            pb = _project(view, base_pos)
            side = 0.06 * view["scale_px_per_m"]
            shapes.append((pb[2],
                           (lambda c=(pb[0], pb[1]), s=side:
                            _rect_pixels(c[0] - s, c[1] - 2.0 * s,
                                         c[0] + s, c[1])),
                           palette("base_marker", 0), code_of("base_marker")))

        shapes.sort(key=lambda sh: -sh[0])   # far first
        for _depth, fn, color, code in shapes:
            painter.paint(fn(), color, code)

        if defect == "SHARED_COLOR_INFLATION_ABSENT":
            # fixture-only: pad_1's exact base color painted onto a small
            # band of the trunk silhouette (beauty WITHOUT mask support).
            # Band height ~8% of the trunk's in-frame extent keeps the
            # trunk co-location ratio above its floor so the isolated
            # failure mode is the pad_1 mask-floor miss.
            band_y1 = ty1
            band_y0 = ty1 - 0.08 * (ty1 - ty0)
            painter.paint(_rect_pixels(tx0, band_y0, tx1, band_y1),
                          palette("pad_1", 0), None)

        if diag:
            dcol0 = palette("diag_layer", 0)
            dcol1 = palette("diag_layer", 1)
            dcode = code_of("diag_layer")

            def dseg(a3, b3, color, radius=1.2):
                pa, pb_ = _project(view, a3), _project(view, b3)
                painter.paint(_seg_pixels((pa[0], pa[1]), (pb_[0], pb_[1]),
                                          radius), color, dcode)

            kind = state.get("kind")
            if kind == "approach":
                d0 = state["d0"]
                dterm = state["d_term"]
                lo, hi = state["window"]
                dseg((d0, 0.0, 0.0), (dterm, 0.0, 0.0), dcol0, 1.0)
                for edge in (lo, hi):
                    dseg((edge, 0.0, 0.0), (edge, 0.0, 0.25), dcol1, 1.0)
                dseg((dterm, 0.0, 0.0), (dterm, 0.0, 0.12), dcol1, 1.0)
            if kind == "geometry":
                gz = state["grasp_z"]
                dspan = state["span_m"]
                ddiam = state["diameter_m"]
                dseg((-ddiam / 2.0, 0.0, gz), (ddiam / 2.0, 0.0, gz), dcol0, 1.0)
                dseg((-dspan / 2.0, 0.0, gz - 0.035),
                     (dspan / 2.0, 0.0, gz - 0.035), dcol1, 1.0)
                dseg((dspan / 2.0, 0.0, gz - 0.035),
                     (ddiam / 2.0, 0.0, gz), dcol1, 1.0)
            if kind == "contact" and pads:
                normals = state.get("normals") or []
                attach = state.get("attach") or []
                for k in range(len(pads)):
                    if k < len(normals) and k < len(attach):
                        a = attach[k]
                        n = normals[k]
                        tip = (a[0] + n[0] * 0.03,
                               a[1] + n[1] * 0.03, a[2] + n[2] * 0.03)
                        dseg(a, tip, dcol0, 1.0)
                    disp = (state.get("disp") or [0.0, 0.0, 0.0])
                    if k < len(disp) and disp[k] > 0.0:
                        cen = [sum(v[i] for v in verts) / 4.0
                               for i in range(3)]
                        dseg(cen, (cen[0], cen[1], cen[2] - disp[k]), dcol1,
                             1.0)
        return painter.beauty, painter.mask

    return render
