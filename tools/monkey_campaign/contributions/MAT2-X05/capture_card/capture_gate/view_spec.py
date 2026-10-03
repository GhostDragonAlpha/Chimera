"""Preregistered view-class expectations (schema chimera.visualgate.view_spec.v1).

Law enforced here and by the gate:

1. Each view class declares BEFORE the run: expected visible object IDs with
   per-class pixel floors, expected occluded IDs together with the occluder ID
   and a frozen-law justification, the co-location ratio floor, and occluder
   evidence floors.
2. Thresholds are frozen inside the spec. The gate NEVER adjusts a threshold
   to pass an observed frame. Any threshold or geometry change mints a new
   spec_version and a new prereg hash (sha256 of the canonical JSON). Receipts
   carry the hash of the spec actually applied.
3. An object ID is either expected-visible or expected-occluded in a class,
   never both. Occlusion entries without a machine-checkable justification
   (exception_class, law_ref, geometry_ref) are refused at load time.

The canonical form is stable: sort_keys=True, separators=(',', ':'),
ensure_ascii=True, UTF-8, no wall-clock fields. Two runs of an unchanged spec
produce byte-identical prereg JSON and the same prereg hash.
"""

import copy
import hashlib
import json

SCHEMA = "chimera.visualgate.view_spec.v1"


class SpecInvalid(ValueError):
    """Raised when a view spec violates the schema or the freeze law."""


def canonical_json_bytes(obj):
    """Stable canonical JSON encoding used for prereg hashing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("utf-8")


def spec_prereg_sha256(spec):
    """sha256 of the canonical prereg form of a view spec."""
    return hashlib.sha256(canonical_json_bytes(spec)).hexdigest()


def _is_rgb(value):
    return (isinstance(value, (list, tuple)) and len(value) == 3
            and all(isinstance(c, int) and 0 <= c <= 255 for c in value))


def validate_spec(spec):
    """Return a list of violation strings; empty means the spec is valid."""
    problems = []

    def bad(msg):
        problems.append(msg)

    if not isinstance(spec, dict):
        return ["spec_not_an_object"]
    if spec.get("schema") != SCHEMA:
        bad("schema_must_be_" + SCHEMA)
    if not isinstance(spec.get("spec_id"), str) or not spec.get("spec_id"):
        bad("spec_id_required")
    if not isinstance(spec.get("spec_version"), int) or spec["spec_version"] < 1:
        bad("spec_version_positive_int_required")

    prereg = spec.get("preregistration")
    if not isinstance(prereg, dict) or prereg.get("declared_before_run") is not True:
        bad("preregistration.declared_before_run_must_be_true")
    if not isinstance(prereg, dict) or not isinstance(prereg.get("freeze_law"), str) \
            or not prereg.get("freeze_law"):
        bad("preregistration.freeze_law_required")
    if not isinstance(prereg, dict) or not isinstance(prereg.get("exception_law"), str) \
            or not prereg.get("exception_law"):
        bad("preregistration.exception_law_required")

    background = spec.get("background")
    if not isinstance(background, dict) or not _is_rgb(background.get("beauty_color")) \
            or not _is_rgb(background.get("mask_code")):
        bad("background.beauty_color_and_mask_code_rgb_required")

    objects = spec.get("objects")
    if not isinstance(objects, dict) or not objects:
        bad("objects_required_non_empty")
        objects = {}

    mask_codes = {}
    beauty_colors = {}
    for name, obj in sorted(objects.items()):
        if not isinstance(obj, dict):
            bad("object.%s.not_an_object" % name)
            continue
        code = obj.get("mask_code")
        if not _is_rgb(code):
            bad("object.%s.mask_code_rgb_required" % name)
        elif tuple(code) in mask_codes:
            bad("object.%s.mask_code_duplicate_with_%s" % (name, mask_codes[tuple(code)]))
        else:
            mask_codes[tuple(code)] = name
        palettes = obj.get("beauty_palette")
        if not isinstance(palettes, list) or not palettes or not all(_is_rgb(c) for c in palettes):
            bad("object.%s.beauty_palette_non_empty_rgb_list_required" % name)
            palettes = []
        for color in palettes:
            beauty_colors.setdefault(tuple(color), []).append(name)
        if obj.get("role") not in ("subject", "occluder", "prop"):
            bad("object.%s.role_must_be_subject_occluder_or_prop" % name)

    if isinstance(background, dict):
        bg_code = background.get("mask_code")
        bg_color = background.get("beauty_color")
        if _is_rgb(bg_code) and tuple(bg_code) in mask_codes:
            bad("background.mask_code_collides_with_object_mask_code")
        if _is_rgb(bg_color) and tuple(bg_color) in beauty_colors:
            bad("background.beauty_color_collides_with_object_palette")
    # Decode safety: a mask code must never equal a beauty palette color or the
    # background beauty color, otherwise channel isolation cannot be audited.
    for code, owner in sorted(mask_codes.items()):
        if code in beauty_colors:
            bad("mask_code_of_%s_collides_with_beauty_palette_of_%s"
                % (owner, ",".join(sorted(beauty_colors[code]))))

    classes = spec.get("view_classes")
    if not isinstance(classes, dict) or not classes:
        bad("view_classes_required_non_empty")
        classes = {}

    for cls_name, cls in sorted(classes.items()):
        label = "view_class.%s" % cls_name
        if not isinstance(cls, dict):
            bad(label + ".not_an_object")
            continue
        floors = cls.get("min_visible_pixels")
        if not isinstance(floors, dict) or not floors:
            bad(label + ".min_visible_pixels_required")
            floors = {}
        for obj_id, floor in sorted(floors.items()):
            if obj_id not in objects:
                bad(label + ".floor_for_undeclared_object_%s" % obj_id)
            if not isinstance(floor, int) or isinstance(floor, bool) or floor < 0:
                bad(label + ".floor_%s_must_be_non_negative_int" % obj_id)

        ratio = cls.get("co_location_min_ratio")
        if not isinstance(ratio, (int, float)) or isinstance(ratio, bool) \
                or not 0.0 <= float(ratio) <= 1.0:
            bad(label + ".co_location_min_ratio_float_0_1_required")

        for key in ("occluder_min_pixels", "occluded_subject_max_px"):
            value = cls.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                bad(label + ".%s_non_negative_int_required" % key)

        occluded = cls.get("expected_occluded", [])
        if not isinstance(occluded, list):
            bad(label + ".expected_occluded_list_required")
            occluded = []
        occluded_ids = set()
        for entry in occluded:
            if not isinstance(entry, dict):
                bad(label + ".expected_occluded_entry_not_an_object")
                continue
            subject = entry.get("subject_id")
            occluder = entry.get("occluder_id")
            if subject not in objects:
                bad(label + ".occluded_subject_undeclared_%s" % subject)
            if occluder not in objects:
                bad(label + ".occluder_undeclared_%s" % occluder)
            if subject == occluder:
                bad(label + ".occluded_subject_equals_occluder")
            if subject in occluded_ids:
                bad(label + ".occluded_subject_duplicate_%s" % subject)
            occluded_ids.add(subject)
            if subject in floors:
                bad(label + ".id_%s_both_visible_and_occluded" % subject)
            justification = entry.get("justification")
            if not isinstance(justification, dict):
                bad(label + ".occlusion_%s_justification_object_required" % subject)
                continue
            if justification.get("exception_class") != "DECLARED_OCCLUSION":
                bad(label + ".occlusion_%s_exception_class_must_be_DECLARED_OCCLUSION" % subject)
            if not isinstance(justification.get("law_ref"), str) or not justification.get("law_ref"):
                bad(label + ".occlusion_%s_law_ref_required" % subject)
            if not isinstance(justification.get("geometry_ref"), str) \
                    or not justification.get("geometry_ref"):
                bad(label + ".occlusion_%s_geometry_ref_required" % subject)
            if justification.get("census_required") is not True:
                bad(label + ".occlusion_%s_census_required_true" % subject)

    return problems


def load_spec(spec):
    """Validate and return a deep copy; raises SpecInvalid on any violation."""
    problems = validate_spec(spec)
    if problems:
        raise SpecInvalid(";".join(problems))
    return copy.deepcopy(spec)


def build_fixture_spec():
    """The preregistered spec for the synthetic multi-object fixture.

    Frozen geometry (half-open xyxy rects on a 128x96 frame) lives inside the
    spec, so occluder geometry_ref citations resolve to hashed prereg bytes.
    """
    return {
        "schema": SCHEMA,
        "spec_id": "VISUAL-GATE-1-mask-fixture",
        "spec_version": 1,
        "preregistration": {
            "declared_before_run": True,
            "freeze_law": (
                "Thresholds are frozen in this spec. The gate never adjusts a "
                "threshold to pass an observed frame. Any threshold or geometry "
                "change mints spec_version+1 and a new prereg hash; the receipt "
                "carries the hash of the spec actually applied."),
            "exception_law": (
                "A frame passes only via an exception declared in this spec. "
                "Every exception pass emits a machine receipt row carrying the "
                "frozen law citation and measured census evidence. Prose-only "
                "exceptions are refused."),
        },
        "background": {"beauty_color": [168, 198, 150], "mask_code": [0, 0, 0]},
        "objects": {
            "thorax": {
                "mask_code": [250, 10, 10],
                "beauty_palette": [[120, 80, 60]],
                "role": "subject",
            },
            "leg_left": {
                "mask_code": [10, 250, 10],
                "beauty_palette": [[200, 60, 50]],
                "role": "subject",
            },
            "leg_right": {
                "mask_code": [10, 10, 250],
                "beauty_palette": [[60, 90, 200]],
                "role": "subject",
            },
            "occluder": {
                "mask_code": [250, 250, 10],
                "beauty_palette": [[60, 60, 70]],
                "role": "occluder",
            },
        },
        "fixture_geometry": {
            "frame_wh": [128, 96],
            "draw_order": ["thorax", "leg_left", "leg_right", "occluder"],
            "rects_xyxy": {
                "thorax": [48, 8, 96, 56],
                "leg_left": [8, 52, 40, 88],
                "leg_right": [88, 52, 120, 88],
                "occluder": [4, 48, 60, 92],
            },
        },
        "view_classes": {
            "clean": {
                "min_visible_pixels": {"thorax": 400, "leg_left": 100, "leg_right": 100},
                "co_location_min_ratio": 0.9,
                "occluder_min_pixels": 100,
                "occluded_subject_max_px": 0,
                "expected_occluded": [],
            },
            "close": {
                "min_visible_pixels": {"thorax": 2000, "leg_left": 500, "leg_right": 500},
                "co_location_min_ratio": 0.9,
                "occluder_min_pixels": 100,
                "occluded_subject_max_px": 0,
                "expected_occluded": [],
            },
            "obstructed": {
                "min_visible_pixels": {"thorax": 400, "leg_right": 100},
                "co_location_min_ratio": 0.9,
                "occluder_min_pixels": 100,
                "occluded_subject_max_px": 0,
                "expected_occluded": [
                    {
                        "subject_id": "leg_left",
                        "occluder_id": "occluder",
                        "justification": {
                            "exception_class": "DECLARED_OCCLUSION",
                            "law_ref": "OCCLUDER-LAW-P9-FROZEN-v1",
                            "geometry_ref": (
                                "fixture_geometry.rects_xyxy.occluder = [4,48,60,92] "
                                "@ VISUAL-GATE-1-mask-fixture v1 (covers leg_left "
                                "[8,52,40,88] fully; occluder fill is required content)"),
                            "census_required": True,
                        },
                    }
                ],
            },
        },
    }
