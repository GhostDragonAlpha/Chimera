"""SUPPORTED-LANDING capture card renderer: deterministic synthetic sidecar
fixture views of the declared release/floor fixture.

Card-owned capture script per capture-gate-template README step 3. The
``render`` callback returns (beauty, mask) uint8 (h, w, 3) pairs; the mask
buffer is a SEPARATE object-ID channel painted from the card view-spec's
per-object ``mask_code`` constants and is never composited into beauty.

HONEST PROVENANCE OF THE PIXELS: every rendered scene state is a fixture
projection of RECORDED run state (pad vertex sets translated by the
recorded cumulative displacements, the recorded pad contact modes, the
recorded first-contact tick, the derived floor plane z) captured from the
landing battery in the same process. Nothing is invented at render time.
This is a rendered fixture view (the G04/K02 heritage pattern), not a
screenshot substitute; the profile's numerical evidence is the receipt
suite. FIXTURE-CLASS: nothing here is evidence about a grasp.

The declared ground_plane body is rendered as its projected quad (the
declared 0.6 m x 0.6 m plane at the derived z_floor); the projections
declare their centers RELATIVE to the floor surface (center_floor_rel_z)
because z_floor is derived at run from pinned constants - the spec freezes
the relation, the renderer resolves it deterministically from the recorded
state.

Defect injection exists ONLY to prove the normal pipeline rejects the four
planted defect classes through THIS card's spec (fixture-only). In this
card's declared classes pad_0 is the VISIBLE subject and the declared
occluder in every view (pads 1/2 are declared occluded behind it), so the
defects target pad_0 and the trunk per the K02 targeting law (a defect
must bite on an expectation the class actually declares):
- WRONG_BODY_COLOR_SHARE: pad_0 renders (mask intact) but its beauty
  pixels carry pad_1's palette color. Co-location kills it.
- SHARED_COLOR_INFLATION_ABSENT: pad_1 absent while a 20% band of the
  trunk silhouette carries pad_1's exact base color (beauty inside the
  TRUNK's mask footprint without the trunk palette; the trunk
  co-location ratio kills it).
- SUBJECT_ABSENT: pad_0 is not rendered at all (its mask floor and its
  occluder floor both bite).
- UNDECLARED_OCCLUSION: pad_1 (declared occluded behind pad_0 in the
  midfall class) is fixture-composed to the front-most fully-visible
  azimuth slot with pad_0 dropped - an arrangement the class never
  preregistered, so the occluded-subject-visible accounting bites.

CPU-only, stdlib + numpy, deterministic (no RNG, no wall clock).
"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

FRAME_WH = [320, 240]

# view_class name -> family ; families declared in the spec.
_FAMILIES = ("midfall", "contact", "rest")


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

    ``state`` keys:
      kind: 'landing'
      pad_verts: [pad][4][3] recorded pad vertex sets (m, M06 frame)
      pad_modes: [pad] recorded contact mode ('stick'|'slip'|'still'|
                 'no_contact'; diagnostic views recolor stick/slip)
      attach/normals: [pad][3] facet centroid + outward normal
      disp / fall_disp: [pad] recorded cumulative downward displacement (m)
      floor_z_m: the derived floor-plane z (m, recorded from the placement)
      floor_half_m: the declared floor half-extent (m)
      ground_contacts: recorded floor-contact events up to the frame tick
      defect: injected defect label (fixture-only)
    """
    objects = spec["objects"]
    background = spec["background"]
    geom = spec["fixture_geometry"]
    projections = geom["projections"]
    trunk_r = geom["trunk_radius_m"]
    trunk_h = geom["trunk_height_m"]
    facet_az = geom["facet_azimuth_deg"]

    floor_z = state["floor_z_m"]
    floor_half = state["floor_half_m"]
    defect = state.get("defect")

    def resolve(view):
        v = dict(view)
        if "center_floor_rel_z" in v:
            v["center_xyz"] = [0.0, 0.0,
                               floor_z + float(v["center_floor_rel_z"])]
        return v

    def palette(name, idx=0):
        return tuple(objects[name]["beauty_palette"][idx])

    def code_of(name):
        return tuple(objects[name]["mask_code"])

    def pad_color(k, family, diag):
        base = palette("pad_%d" % k, 0)
        if not diag:
            if defect == "WRONG_BODY_COLOR_SHARE" and k == 0:
                # pad_0 is the VISIBLE subject in every declared class:
                # painting its beauty with pad_1's palette color (mask
                # intact) is the shared-color defect the co-location
                # defense bites on (the K02 law: the defect must target a
                # subject the class expects VISIBLE).
                return palette("pad_1", 0)
            return base
        modes = state.get("pad_modes") or []
        mode = modes[k] if k < len(modes) else None
        if mode == "stick":
            return palette("pad_%d" % k, 1)
        if mode == "slip":
            return palette("pad_%d" % k, 2)
        if defect == "WRONG_BODY_COLOR_SHARE" and k == 0:
            return palette("pad_1", 1)
        return base

    def render(view_class, frame_id, defect=None):
        del frame_id
        parts = view_class.split("_")
        diag = "diag" in parts
        family = next((f for f in _FAMILIES if f in parts), None)
        if family is None or ("clean" not in parts and not diag):
            raise ValueError("unknown_view_class:" + str(view_class))
        view = resolve(projections[family])
        painter = _Painter()
        painter.paint(_rect_pixels(0, 0, FRAME_WH[0] - 1, FRAME_WH[1] - 1),
                      tuple(background["beauty_color"]),
                      tuple(background["mask_code"]))
        shapes = []  # (depth, painter_fn, color, code)

        # the declared ground_plane body: its projected quad (farthest)
        h = floor_half
        corners = [(-h, -h, floor_z), (h, -h, floor_z),
                   (h, h, floor_z), (-h, h, floor_z)]
        proj = [_project(view, c) for c in corners]
        floor_depth = sum(p[2] for p in proj) / len(proj)
        shapes.append((floor_depth,
                       (lambda poly=[(p[0], p[1]) for p in proj]:
                        _hull_pixels(poly)),
                       palette("ground_plane", 0), code_of("ground_plane")))

        # trunk silhouette (orthographic cylinder: image-space rect)
        p0 = _project(view, (0.0, 0.0, 0.0))
        p1 = _project(view, (0.0, 0.0, trunk_h))
        half = trunk_r * view["scale_px_per_m"]
        tx0, tx1 = p0[0] - half, p0[0] + half
        ty0, ty1 = min(p0[1], p1[1]), max(p0[1], p1[1])
        shapes.append((0.0,
                       (lambda rect=(tx0, ty0, tx1, ty1):
                        _rect_pixels(*rect)),
                       palette("trunk", 0), code_of("trunk")))

        pads = state.get("pad_verts")
        if pads:
            inj_angle = None
            drop_front = False
            if defect == "UNDECLARED_OCCLUSION" and family == "contact":
                # fixture-only: rotate pad_1 (declared occluded behind
                # pad_0 in the contact class) into pad_0's azimuth slot
                # and drop pad_0, so pad_1 renders front-most fully
                # visible -- an arrangement the class never preregistered.
                # The contact class is the calibrated composition site:
                # its production rear-pad counts (120/131 px) sit far
                # under its cap, and the composed pad_1 renders at
                # pad_0-like scale (~5000 px) so the cap accounting bites
                # with wide deterministic margins (a class-wide cap
                # cannot separate the midfall production counts: pad_2's
                # genuine 760 px EXCEEDS the composed pad_1's 490 px).
                # Rotation: pad_1 is rotated INTO pad_0's azimuth slot,
                # i.e. by (az(pad_0) - az(pad_1)) around z (the K02 law's
                # phi - az(subject), with phi == az(pad_0) in this card).
                inj_angle = math.radians(
                    facet_az["pad_0"] - facet_az["pad_1"])
                drop_front = True
            for k, verts in enumerate(pads):
                if drop_front and k == 0:
                    continue
                if defect == "SUBJECT_ABSENT" and k == 0:
                    # pad_0 is the VISIBLE subject and the declared
                    # occluder in every class: its absence is the
                    # subject-absence defect the mask floor bites on (the
                    # K02 law: the dropped body must be one the class
                    # expects VISIBLE with a floor).
                    continue
                if defect == "SHARED_COLOR_INFLATION_ABSENT" and k == 1:
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

        shapes.sort(key=lambda sh: -sh[0])   # far first
        for _depth, fn, color, code in shapes:
            painter.paint(fn(), color, code)

        if defect == "SHARED_COLOR_INFLATION_ABSENT":
            # fixture-only: pad_1's exact base color painted onto a band
            # of the trunk silhouette (beauty WITHOUT mask support). In
            # this card's classes pad_1 is declared occluded (its absence
            # alone fires nothing), so the isolated failure mode is the
            # TRUNK co-location mismatch: the band is 20% of the trunk's
            # in-frame extent, driving the trunk's declared-palette ratio
            # below the 0.9 floor.
            band_y1 = ty1
            band_y0 = ty1 - 0.20 * (ty1 - ty0)
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

            # the floor datum line across the declared plane (the
            # declared landing.ground_plane surface trace)
            gz = state.get("floor_z_m")
            if gz is not None:
                dseg((-0.15, 0.0, gz), (0.15, 0.0, gz), dcol0, 1.0)
            # the recorded per-pad fall displacement (from the fallen
            # position back up to the release band)
            fdisp = state.get("fall_disp") or []
            pads_ = state.get("pad_verts") or []
            for k in range(len(pads_)):
                cen = [sum(v[i] for v in pads_[k]) / 4.0 for i in range(3)]
                fd = fdisp[k] if k < len(fdisp) else 0.0
                if fd > 0.0:
                    dseg(cen, (cen[0], cen[1], cen[2] + fd), dcol1, 1.0)
            # markers for recorded floor-contact events up to the frame
            # tick (recorded evidence; the supporting classification lives
            # in the numerical receipts, never in the pixels)
            tick_abs = state.get("tick_abs")
            for ev in state.get("ground_contacts") or []:
                if tick_abs is not None and ev.get("tick", 0) > tick_abs:
                    continue
                site = ev.get("site")
                if isinstance(site, str) and site.startswith("grip.pad_"):
                    try:
                        k = int(site.rsplit("_", 1)[1])
                    except ValueError:
                        continue
                    if k < len(pads_):
                        cen = [sum(v[i] for v in pads_[k]) / 4.0
                               for i in range(3)]
                        dseg((cen[0] - 0.01, cen[1], cen[2]),
                             (cen[0] + 0.01, cen[1], cen[2]), dcol1, 2.0)
        return painter.beauty, painter.mask

    return render
