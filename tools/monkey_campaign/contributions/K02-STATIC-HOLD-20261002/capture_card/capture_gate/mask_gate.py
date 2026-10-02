"""Object-ID mask gate (schema chimera.visualgate.mask_gate.v1).

Decodes the sidecar (beauty, mask) pair against a preregistered view class and
returns a machine receipt. Checks, in order:

1. BLANK_UNIFORM: both channels uniform (U07's blank-frame power, retained).
2. UNDECLARED_MASK_ID: mask pixels carrying an ID code that the class neither
   expects visible nor expects occluded (and not the background code). Catches
   rogue objects and undeployed occluders.
3. Per visible subject:
   a. SUBJECT_MASK_BELOW_FLOOR: count(mask == id_code) < frozen per-class
      floor. A subject that is not in the mask channel is not proven present;
      palette pixels alone never substitute for ID pixels.
   b. COLOCATION_MISMATCH: within the subject's own mask footprint, the
      fraction of beauty pixels showing one of the subject's declared palette
      colors must reach the frozen co_location_min_ratio. This is the shared-
      color defense: another body painting the subject's color (or the subject
      painted with the wrong body's color) fails here even when palette totals
      look healthy.
4. Per declared occlusion:
   a. OCCLUDED_SUBJECT_VISIBLE: the occluded subject's own ID code appears in
      more than occluded_subject_max_px pixels.
   b. OCCLUDER_MISSING: the occluder's ID code is below occluder_min_pixels.
   c. OCCLUDER_COLOCATION_MISMATCH: the occluder's beauty pixels inside its
      own mask footprint do not match its declared palette.
   A frame that passes only because a declared occlusion is present is GREEN
   via exception: an exception row (machine-generated, no prose) carries the
   frozen law_ref, geometry_ref from the spec and the measured census.

The gate never mutates the spec and never adjusts thresholds. All observed
counts are integers; all verdicts derive from the spec's frozen numbers.
"""

import numpy as np

from . import view_spec

GATE_SCHEMA = "chimera.visualgate.mask_gate.v1"

VERDICT_GREEN = "GREEN"
VERDICT_RED = "RED"

BLANK_UNIFORM = "BLANK_UNIFORM"
UNDECLARED_MASK_ID = "UNDECLARED_MASK_ID"
SUBJECT_MASK_BELOW_FLOOR = "SUBJECT_MASK_BELOW_FLOOR"
COLOCATION_MISMATCH = "COLOCATION_MISMATCH"
OCCLUDED_SUBJECT_VISIBLE = "OCCLUDED_SUBJECT_VISIBLE"
OCCLUDER_MISSING = "OCCLUDER_MISSING"
OCCLUDER_COLOCATION_MISMATCH = "OCCLUDER_COLOCATION_MISMATCH"

EXCEPTION_CLASS_DECLARED_OCCLUSION = "DECLARED_OCCLUSION"


def _code_array(rgb):
    return np.array(rgb, dtype=np.uint8)


def _footprint(mask, code):
    return np.all(mask == _code_array(code), axis=2)


def _bbox_of(footprint):
    rows = np.any(footprint, axis=1)
    cols = np.any(footprint, axis=0)
    if not rows.any():
        return None
    rmin, rmax = int(np.argmax(rows)), int(len(rows) - 1 - np.argmax(rows[::-1]))
    cmin, cmax = int(np.argmax(cols)), int(len(cols) - 1 - np.argmax(cols[::-1]))
    return [rmin, cmin, rmax, cmax]


def _palette_coloc_ratio(beauty, footprint, palettes):
    """Fraction of footprint pixels whose beauty color is a declared palette color."""
    total = int(np.count_nonzero(footprint))
    if total == 0:
        return 0.0, 0, None
    flat = beauty[footprint]
    hit = np.zeros(flat.shape[0], dtype=bool)
    for color in palettes:
        hit |= np.all(flat == _code_array(color), axis=1)
    hits = int(np.count_nonzero(hit))
    return hits / total, hits, total


def _failure(code, object_id, observed, threshold):
    return {"code": code, "object_id": object_id,
            "observed": observed, "threshold": threshold}


def evaluate_frame(spec, view_class, beauty, mask, frame_id):
    """Gate one sidecar pair against a preregistered view class."""
    cls = spec["view_classes"][view_class]
    objects = spec["objects"]
    background = spec["background"]
    failures = []
    exceptions = []
    census = {}
    occlusion_evidence = []

    # 1. Blank/uniform guard (retained from the U07 palette-gate law).
    beauty_unique = np.unique(beauty.reshape(-1, 3), axis=0)
    mask_unique = np.unique(mask.reshape(-1, 3), axis=0)
    beauty_uniform = tuple(int(v) for v in beauty_unique[0]) if len(beauty_unique) == 1 else None
    mask_uniform = tuple(int(v) for v in mask_unique[0]) if len(mask_unique) == 1 else None
    if beauty_uniform is not None and mask_uniform is not None:
        failures.append(_failure(BLANK_UNIFORM, "*",
                                 {"beauty_uniform": list(beauty_uniform),
                                  "mask_uniform": list(mask_uniform)},
                                 "non_uniform_required"))

    # 2. Declared-code accounting over the whole mask channel.
    known_codes = {tuple(int(c) for c in background["mask_code"]): "background"}
    for name, obj in objects.items():
        known_codes[tuple(int(c) for c in obj["mask_code"])] = name
    visible_ids = set(cls["min_visible_pixels"])
    occluded_ids = {entry["subject_id"] for entry in cls.get("expected_occluded", [])}
    occluder_ids = {entry["occluder_id"] for entry in cls.get("expected_occluded", [])}

    flat_codes = mask.reshape(-1, 3)
    unique_codes = np.unique(flat_codes, axis=0)
    present = {}
    for code in unique_codes:
        key = tuple(int(c) for c in code)
        owner = known_codes.get(key)
        if owner is None:
            count = int(np.count_nonzero(np.all(flat_codes == code, axis=1)))
            present["<undeclared:%d,%d,%d>" % key] = count
            failures.append(_failure(UNDECLARED_MASK_ID, None,
                                     {"mask_code": list(key), "pixels": count},
                                     "declared_ids_only"))
            continue
        present[owner] = int(np.count_nonzero(np.all(flat_codes == code, axis=1)))

    for owner in sorted(present):
        if owner.startswith("<undeclared:"):
            continue  # already recorded with the raw code in the first loop
        if owner in ("background",) or owner in visible_ids \
                or owner in occluded_ids or owner in occluder_ids:
            continue
        # A declared object's ID present where the class expects it neither
        # visible nor occluded: an undeployed occluder or rogue rendering.
        failures.append(_failure(UNDECLARED_MASK_ID, owner,
                                 {"pixels": present[owner]}, "declared_ids_only"))

    # 3. Per visible subject: mask floor then beauty co-location.
    for subject_id in sorted(cls["min_visible_pixels"]):
        floor = int(cls["min_visible_pixels"][subject_id])
        code = objects[subject_id]["mask_code"]
        footprint = _footprint(mask, code)
        px = int(np.count_nonzero(footprint))
        if px < floor:
            failures.append(_failure(SUBJECT_MASK_BELOW_FLOOR, subject_id,
                                     px, floor))
            census[subject_id] = {"mask_px": px, "coloc_ratio": None,
                                  "bbox": None, "floor": floor}
            continue
        ratio, hits, total = _palette_coloc_ratio(beauty, footprint,
                                                  objects[subject_id]["beauty_palette"])
        min_ratio = float(cls["co_location_min_ratio"])
        census[subject_id] = {"mask_px": px, "coloc_ratio": round(ratio, 6),
                              "coloc_hits": hits, "footprint_px": total,
                              "bbox": _bbox_of(footprint), "floor": floor}
        if ratio < min_ratio:
            failures.append(_failure(COLOCATION_MISMATCH, subject_id,
                                     round(ratio, 6), min_ratio))

    # 4. Per declared occlusion: occluded absence + occluder identity evidence.
    for entry in cls.get("expected_occluded", []):
        subject_id = entry["subject_id"]
        occluder_id = entry["occluder_id"]
        justification = entry["justification"]
        subject_px = int(present.get(subject_id, 0))
        occluder_px = int(present.get(occluder_id, 0))
        occluder_ratio, occluder_hits, occluder_total = 0.0, 0, 0
        occluder_bbox = None
        if occluder_px:
            footprint = _footprint(mask, objects[occluder_id]["mask_code"])
            occluder_ratio, occluder_hits, occluder_total = _palette_coloc_ratio(
                beauty, footprint, objects[occluder_id]["beauty_palette"])
            occluder_bbox = _bbox_of(footprint)
        evidence = {
            "subject_id": subject_id,
            "occluder_id": occluder_id,
            "occluded_subject_mask_px": subject_px,
            "occluder_mask_px": occluder_px,
            "occluder_coloc_ratio": round(occluder_ratio, 6),
            "occluder_coloc_hits": occluder_hits,
            "occluder_footprint_px": occluder_total,
            "occluder_bbox": occluder_bbox,
        }
        occlusion_evidence.append(evidence)
        if subject_px > int(cls["occluded_subject_max_px"]):
            failures.append(_failure(OCCLUDED_SUBJECT_VISIBLE, subject_id,
                                     subject_px, int(cls["occluded_subject_max_px"])))
        if occluder_px < int(cls["occluder_min_pixels"]):
            failures.append(_failure(OCCLUDER_MISSING, occluder_id,
                                     occluder_px, int(cls["occluder_min_pixels"])))
        elif occluder_ratio < float(cls["co_location_min_ratio"]):
            failures.append(_failure(OCCLUDER_COLOCATION_MISMATCH, occluder_id,
                                     round(occluder_ratio, 6),
                                     float(cls["co_location_min_ratio"])))

    verdict = VERDICT_GREEN if not failures else VERDICT_RED

    # 5. Exception protocol: a GREEN pass that relies on a declared occlusion
    # emits one machine receipt row per occlusion, citing the frozen law and
    # carrying the measured census. No prose-only exceptions.
    if verdict == VERDICT_GREEN:
        for entry, evidence in zip(cls.get("expected_occluded", []), occlusion_evidence):
            exceptions.append({
                "frame_id": frame_id,
                "view_class": view_class,
                "exception_class": EXCEPTION_CLASS_DECLARED_OCCLUSION,
                "subject_id": entry["subject_id"],
                "occluder_id": entry["occluder_id"],
                "law_ref": entry["justification"]["law_ref"],
                "geometry_ref": entry["justification"]["geometry_ref"],
                "census": {k: v for k, v in evidence.items()
                           if k not in ("subject_id", "occluder_id")},
            })

    return {
        "frame_id": frame_id,
        "view_class": view_class,
        "verdict": verdict,
        "census": census,
        "mask_channel_census": present,
        "occlusion_evidence": occlusion_evidence,
        "failures": failures,
        "exceptions": exceptions,
    }


def evaluate_suite(spec, frames):
    """Gate an iterable of (frame_id, view_class, RenderedFrame) triples."""
    reports = []
    for frame_id, view_class, rendered in frames:
        if rendered.view_class != view_class:
            raise ValueError("frame_view_class_mismatch: " + frame_id)
        reports.append(evaluate_frame(spec, view_class, rendered.beauty,
                                      rendered.mask, frame_id))
    gate_green = all(r["verdict"] == VERDICT_GREEN for r in reports)
    return {
        "schema": GATE_SCHEMA,
        "view_spec_schema": view_spec.SCHEMA,
        "spec_id": spec["spec_id"],
        "spec_version": spec["spec_version"],
        "prereg_sha256": view_spec.spec_prereg_sha256(spec),
        "freeze_law": spec["preregistration"]["freeze_law"],
        "exception_law": spec["preregistration"]["exception_law"],
        "frames": reports,
        "frames_total": len(reports),
        "frames_green": sum(1 for r in reports if r["verdict"] == VERDICT_GREEN),
        "frames_red": sum(1 for r in reports if r["verdict"] == VERDICT_RED),
        "exception_rows": [e for r in reports for e in r["exceptions"]],
        "verdict": VERDICT_GREEN if gate_green else VERDICT_RED,
    }
