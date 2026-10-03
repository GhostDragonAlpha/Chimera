"""Sidecar mask-buffer capture (schema chimera.capture_gate.capture_manifest.v1).

A card capture script renders every planned frame as a SIDECAR PAIR:

- ``beauty``: the normal frame a viewer would see;
- ``mask``: the object-ID identity buffer. Every declared object paints its
  stable flat ID code (declared in the card's view-spec) into this separate
  buffer; the mask channel is never composited into the beauty frame.

This module is the capture-side contract the template pipeline calls for
every frame. The card supplies ``render_fn(view_class, frame_id, defect)``
returning ``(beauty, mask)`` as uint8 (h, w, 3) arrays. The contract:

- geometry must match the spec's declared frame size;
- channel isolation is audited at capture time (fail fast): beauty colors
  must stay inside the declared palettes plus the background color, mask
  codes inside the declared ID codes plus the background code, and no mask
  code may ever appear in the beauty channel. Violations refuse the capture
  (CaptureRefused) independently of the acceptance gate; the stage-1 gate
  re-checks declared-code accounting as defense in depth;
- every frame gets content hashes (beauty, mask, pair) and the capture
  manifest binds the spec identity and the card prereg file by sha256
  BEFORE any gating happens.

Deterministic: no RNG, no wall-clock fields in the manifest.
"""

import hashlib
import json
import os

import numpy as np

SCHEMA = "chimera.capture_gate.capture_manifest.v1"

CAPTURE_MANIFEST_FILENAME = "capture_manifest.json"


class CaptureRefused(ValueError):
    """Raised when a rendered sidecar pair violates the capture contract."""


class SidecarFrame(object):
    """One captured (beauty, mask) pair with content hashes."""

    __slots__ = ("frame_id", "view_class", "defect", "beauty", "mask",
                 "frame_wh", "beauty_sha256", "mask_sha256", "frame_sha256")

    @property
    def defect_label(self):
        return self.defect if self.defect else "NONE"


def _rgb_array(value, name):
    array = np.asarray(value)
    if array.ndim != 3 or array.shape[2] != 3:
        raise CaptureRefused(name + "_must_be_hwc_rgb")
    if array.dtype != np.uint8:
        raise CaptureRefused(name + "_must_be_uint8")
    return array


def _unique_colors(array):
    return {tuple(int(c) for c in row) for row in np.unique(array.reshape(-1, 3), axis=0)}


def pair_sha256(beauty, mask):
    digest = hashlib.sha256()
    for buffer in (beauty, mask):
        digest.update(str(buffer.shape).encode("ascii"))
        digest.update(np.ascontiguousarray(buffer).tobytes())
    return digest.hexdigest()


def buffer_sha256(buffer):
    return hashlib.sha256(np.ascontiguousarray(buffer).tobytes()).hexdigest()


def audit_channel_isolation(spec, beauty, mask):
    """Return a list of machine problem codes; empty means the pair is clean."""
    problems = []
    allowed_beauty = {tuple(int(c) for c in spec["background"]["beauty_color"])}
    mask_codes = {tuple(int(c) for c in spec["background"]["mask_code"])}
    allowed_mask = set(mask_codes)
    for obj in spec["objects"].values():
        allowed_beauty |= {tuple(int(c) for c in color) for color in obj["beauty_palette"]}
        code = tuple(int(c) for c in obj["mask_code"])
        allowed_mask.add(code)
        mask_codes.add(code)
    beauty_colors = _unique_colors(beauty)
    mask_colors = _unique_colors(mask)
    leaks = sorted(beauty_colors & mask_codes)
    if leaks:
        problems.append("beauty_carries_mask_code:" +
                        ";".join("%d,%d,%d" % code for code in leaks))
    stray_beauty = sorted(beauty_colors - allowed_beauty)
    if stray_beauty:
        problems.append("beauty_undeclared_color:" +
                        ";".join("%d,%d,%d" % code for code in stray_beauty))
    stray_mask = sorted(mask_colors - allowed_mask)
    if stray_mask:
        problems.append("mask_undeclared_code:" +
                        ";".join("%d,%d,%d" % code for code in stray_mask))
    return problems


def capture_frame(spec, view_class, render_fn, frame_id, defect=None):
    """Capture one sidecar pair through the card render callback."""
    if view_class not in spec["view_classes"]:
        raise CaptureRefused("view_class_undeclared_in_spec:" + str(view_class))
    geometry = spec["fixture_geometry"]
    width, height = (int(v) for v in geometry["frame_wh"])
    beauty, mask = render_fn(view_class=view_class, frame_id=frame_id, defect=defect)
    beauty = _rgb_array(beauty, "beauty")
    mask = _rgb_array(mask, "mask")
    if beauty.shape[0] != height or beauty.shape[1] != width:
        raise CaptureRefused("beauty_frame_geometry_mismatch")
    if mask.shape[0] != height or mask.shape[1] != width:
        raise CaptureRefused("mask_frame_geometry_mismatch")
    problems = audit_channel_isolation(spec, beauty, mask)
    if problems:
        raise CaptureRefused(";".join(problems))
    frame = SidecarFrame()
    frame.frame_id = frame_id
    frame.view_class = view_class
    frame.defect = defect
    frame.beauty = beauty
    frame.mask = mask
    frame.frame_wh = [width, height]
    frame.beauty_sha256 = buffer_sha256(beauty)
    frame.mask_sha256 = buffer_sha256(mask)
    frame.frame_sha256 = pair_sha256(beauty, mask)
    return frame


def build_capture_manifest(spec, prereg_binding, frames):
    """Bind spec identity + prereg file hash + every captured frame."""
    return {
        "schema": SCHEMA,
        "capture_order": "spec_fixture_geometry_draw_order_sidecar_pairs",
        "view_spec": {
            "schema": spec["schema"],
            "spec_id": spec["spec_id"],
            "spec_version": spec["spec_version"],
            "prereg_sha256": prereg_binding["prereg_sha256"],
        },
        "card_prereg": {
            "file": prereg_binding["prereg_file"],
            "sha256": prereg_binding["prereg_file_sha256"],
            "declared_before_capture": True,
        },
        "frames": [
            {
                "frame_id": frame.frame_id,
                "view_class": frame.view_class,
                "defect": frame.defect_label,
                "frame_wh": list(frame.frame_wh),
                "beauty_sha256": frame.beauty_sha256,
                "mask_sha256": frame.mask_sha256,
                "frame_sha256": frame.frame_sha256,
            }
            for frame in frames
        ],
        "frames_total": len(frames),
    }


def write_capture_manifest(out_dir, manifest):
    """Write canonical bytes; return (path, sha256)."""
    data = json.dumps(manifest, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("utf-8")
    path = os.path.join(out_dir, CAPTURE_MANIFEST_FILENAME)
    with open(path, "wb") as handle:
        handle.write(data)
    digest = hashlib.sha256(data).hexdigest()
    return path, digest
