"""Independent-visual-review hook: export crops for exception frames only.

The strengthened gate must remain auditable by humans: every frame that passed
only via an exception gets a deterministic side-by-side crop (beauty | mask)
around the occluder footprint, plus a manifest that binds crop bytes, frame
buffers, law citation and census by sha256. A human or sergeant visual pass
then reviews exactly the exception set instead of re-watching full captures.

This module builds the hook and its artifacts; commissioning the independent
review pass is the Lieutenant's call, not this lane's.
"""

import hashlib
import json
import os

import numpy as np

from . import png_writer

MANIFEST_SCHEMA = "chimera.visualgate.review_manifest.v1"
CROP_PAD_PX = 4
DIVIDER_PX = 2
DIVIDER_COLOR = (0, 0, 0)


def _crop(image, bbox):
    rmin, cmin, rmax, cmax = bbox
    rmin = max(0, rmin - CROP_PAD_PX)
    cmin = max(0, cmin - CROP_PAD_PX)
    rmax = min(image.shape[0], rmax + 1 + CROP_PAD_PX)
    cmax = min(image.shape[1], cmax + 1 + CROP_PAD_PX)
    return np.ascontiguousarray(image[rmin:rmax, cmin:cmax])


def _side_by_side(beauty_crop, mask_crop):
    height = max(beauty_crop.shape[0], mask_crop.shape[0])
    width = beauty_crop.shape[1] + DIVIDER_PX + mask_crop.shape[1]
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    canvas[:, :] = np.array(DIVIDER_COLOR, dtype=np.uint8)
    canvas[:beauty_crop.shape[0], :beauty_crop.shape[1]] = beauty_crop
    offset = beauty_crop.shape[1] + DIVIDER_PX
    canvas[:mask_crop.shape[0], offset:offset + mask_crop.shape[1]] = mask_crop
    return canvas


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def export_exception_crops(reports, frames_by_id, out_dir):
    """Write one deterministic crop per exception row plus the review manifest.

    ``frames_by_id`` maps frame_id -> RenderedFrame (beauty/mask sidecar pair).
    Returns the manifest dict. GREEN frames without exceptions export nothing:
    the independent visual pass reviews exactly the exception set.
    """
    os.makedirs(out_dir, exist_ok=True)
    entries = []
    for report in reports:
        for exception in report["exceptions"]:
            frame = frames_by_id[exception["frame_id"]]
            bbox = exception["census"].get("occluder_bbox")
            if bbox is None:
                raise ValueError("exception_without_occluder_bbox: "
                                 + exception["frame_id"])
            crop = _side_by_side(_crop(frame.beauty, bbox), _crop(frame.mask, bbox))
            filename = "%s_crop.png" % exception["frame_id"]
            path = os.path.join(out_dir, filename)
            png_writer.write_png(path, crop)
            entries.append({
                "frame_id": exception["frame_id"],
                "view_class": exception["view_class"],
                "exception_class": exception["exception_class"],
                "subject_id": exception["subject_id"],
                "occluder_id": exception["occluder_id"],
                "law_ref": exception["law_ref"],
                "geometry_ref": exception["geometry_ref"],
                "census": exception["census"],
                "crop_file": os.path.relpath(path, out_dir),
                "crop_sha256": _sha256_file(path),
                "beauty_sha256": hashlib.sha256(
                    np.ascontiguousarray(frame.beauty).tobytes()).hexdigest(),
                "mask_sha256": hashlib.sha256(
                    np.ascontiguousarray(frame.mask).tobytes()).hexdigest(),
                "review_purpose": ("independent visual pass over exception "
                                   "frames only; commissioned by the Lieutenant"),
            })
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "exception_count": len(entries),
        "entries": entries,
        "crop_encoder": "png_rgb8_filter0_zlib9_deterministic",
    }
    manifest_path = os.path.join(out_dir, "review_manifest.json")
    with open(manifest_path, "wb") as handle:
        handle.write(json.dumps(manifest, sort_keys=True,
                                separators=(",", ":")).encode("utf-8"))
    manifest["manifest_path"] = manifest_path
    manifest["manifest_sha256"] = _sha256_file(manifest_path)
    return manifest
