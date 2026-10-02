"""Deterministic synthetic multi-object fixture (pure NumPy, no RNG).

Renders a declared scene twice per frame:

- ``beauty``: what a normal frame would show (per-object palette colors on a
  background color),
- ``mask``: the object-ID identity channel. Every declared object paints its
  stable flat ID code into the SEPARATE mask buffer. The mask channel is never
  composited into the beauty frame; the two buffers only ever coexist as a
  sidecar pair.

Determinism: integer fills only, no RNG, no float math, fixed draw order from
the spec's frozen geometry. Two invocations with the same arguments produce
byte-identical buffers.

Defect injection exists ONLY to prove the gate fails as designed:

- ``WRONG_BODY_COLOR_SHARE``: leg_left renders (its mask footprint is intact)
  but its beauty pixels are painted with leg_right's palette color. Per-body
  palette totals stay high, so a totals-style palette gate would pass; the
  co-location check fails it.
- ``SHARED_COLOR_INFLATION_ABSENT``: leg_left is truly absent, and thorax is
  painted with leg_left's exact palette color. A totals-style palette gate
  counts thorax's surface as leg_left evidence (false positive); the mask
  floor fails it.
- ``SUBJECT_ABSENT``: leg_right is not rendered at all.
- ``UNDECLARED_OCCLUSION``: the occluder slab covers leg_left in a class that
  did not preregister the occlusion (undeployable occlusion exceptions).
"""

import hashlib

import numpy as np

DEFECT_NONE = None
DEFECT_WRONG_BODY_COLOR_SHARE = "WRONG_BODY_COLOR_SHARE"
DEFECT_SHARED_COLOR_INFLATION_ABSENT = "SHARED_COLOR_INFLATION_ABSENT"
DEFECT_SUBJECT_ABSENT = "SUBJECT_ABSENT"
DEFECT_UNDECLARED_OCCLUSION = "UNDECLARED_OCCLUSION"

ALL_DEFECTS = (
    DEFECT_WRONG_BODY_COLOR_SHARE,
    DEFECT_SHARED_COLOR_INFLATION_ABSENT,
    DEFECT_SUBJECT_ABSENT,
    DEFECT_UNDECLARED_OCCLUSION,
)

def _rect_slices(rect_xyxy):
    x0, y0, x1, y1 = rect_xyxy
    return slice(y0, y1), slice(x0, x1)


def _class_occluder_ids(cls):
    return {entry["occluder_id"] for entry in cls.get("expected_occluded", [])}


class RenderedFrame:
    """A sidecar pair: beauty frame + object-ID mask buffer plus metadata."""

    __slots__ = ("beauty", "mask", "view_class", "defect", "frame_wh")

    def __init__(self, beauty, mask, view_class, defect, frame_wh):
        self.beauty = beauty
        self.mask = mask
        self.view_class = view_class
        self.defect = defect
        self.frame_wh = frame_wh


def _class_occluder_ids(cls):
    return {entry["occluder_id"] for entry in cls.get("expected_occluded", [])}


def render_frame(spec, view_class, defect=DEFECT_NONE):
    """Render one deterministic (beauty, mask) pair for a view class."""
    geometry = spec["fixture_geometry"]
    width, height = geometry["frame_wh"]
    background = spec["background"]
    objects = spec["objects"]
    cls = spec["view_classes"][view_class]

    beauty = np.empty((height, width, 3), dtype=np.uint8)
    beauty[:, :] = np.array(background["beauty_color"], dtype=np.uint8)
    mask = np.empty((height, width, 3), dtype=np.uint8)
    mask[:, :] = np.array(background["mask_code"], dtype=np.uint8)

    occluder_active_names = set(_class_occluder_ids(cls))
    if defect == DEFECT_UNDECLARED_OCCLUSION:
        # The planted defect: an occluder covers the subject although this
        # class never declared the occlusion.
        occluder_active_names.add("occluder")

    rects = geometry["rects_xyxy"]
    for name in geometry["draw_order"]:
        if defect == DEFECT_SUBJECT_ABSENT and name == "leg_right":
            continue
        if objects[name]["role"] == "occluder" and name not in occluder_active_names:
            continue  # occluder slabs render only when active for this frame
        color = objects[name]["beauty_palette"][0]
        if defect == DEFECT_WRONG_BODY_COLOR_SHARE and name == "leg_left":
            color = objects["leg_right"]["beauty_palette"][0]
        if defect == DEFECT_SHARED_COLOR_INFLATION_ABSENT:
            if name == "leg_left":
                continue  # subject truly absent from both channels
            if name == "thorax":
                color = objects["leg_left"]["beauty_palette"][0]
        ys, xs = _rect_slices(rects[name])
        beauty[ys, xs] = np.array(color, dtype=np.uint8)
        mask[ys, xs] = np.array(objects[name]["mask_code"], dtype=np.uint8)

    return RenderedFrame(beauty=beauty, mask=mask, view_class=view_class,
                         defect=defect, frame_wh=[width, height])


def frame_sha256(rendered):
    """Stable content hash of a rendered sidecar pair (beauty then mask)."""
    digest = hashlib.sha256()
    for buffer in (rendered.beauty, rendered.mask):
        digest.update(str(buffer.shape).encode("ascii"))
        digest.update(np.ascontiguousarray(buffer).tobytes())
    return digest.hexdigest()
