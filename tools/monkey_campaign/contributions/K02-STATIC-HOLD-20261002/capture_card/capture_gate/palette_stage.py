"""Stage-0 palette gate: blank-frame detector + totals smoke census
(schema chimera.capture_gate.palette_stage.v1).

This stage carries the U07 palette-gate law forward at its proven strength:
a uniform (blank) frame fails immediately. Per-subject palette totals are
recorded as a SMOKE census only. The campaign proved that totals alone cannot
distinguish a present subject from palette sharing between bodies, so stage-0
totals are never a pass determinant. The stage-1 object-ID mask gate
(mask_gate) owns acceptance; a frame passes the two-stage gate only when BOTH
stages are GREEN (stage-1 GREEN via a declared-occlusion exception still
counts as GREEN, with machine receipt rows).

No wall-clock fields; deterministic; pure NumPy.
"""

import numpy as np

SCHEMA = "chimera.capture_gate.palette_stage.v1"

VERDICT_GREEN = "GREEN"
VERDICT_RED = "RED"

BLANK_UNIFORM = "BLANK_UNIFORM"

MAX_OBSERVED_COLORS = 8

SMOKE_NOTE = (
    "stage-0 palette totals are a smoke counterfactual only; they never pass "
    "a frame. Stage-1 (mask co-location) owns acceptance.")


def evaluate_frame_palette(beauty):
    """Blank/uniform detector over one beauty frame."""
    flat = np.asarray(beauty).reshape(-1, 3)
    unique = np.unique(flat, axis=0)
    blank = unique.shape[0] == 1
    failures = []
    if blank:
        failures.append({
            "code": BLANK_UNIFORM,
            "object_id": "*",
            "observed": [int(v) for v in unique[0]],
            "threshold": "non_uniform_required",
        })
    return {
        "schema": SCHEMA,
        "verdict": VERDICT_RED if failures else VERDICT_GREEN,
        "unique_color_count": int(unique.shape[0]),
        "observed_colors": [[int(c) for c in row] for row in unique[:MAX_OBSERVED_COLORS]],
        "observed_colors_truncated": bool(unique.shape[0] > MAX_OBSERVED_COLORS),
        "failures": failures,
        "totals_census_note": SMOKE_NOTE,
    }


def palette_totals_census(spec, view_class, beauty):
    """Old totals-style gate counterfactual (informational, never decisive).

    Mirrors the U07-era single-total palette check so every receipt can show
    what the smoke gate alone would have said about the same frame.
    """
    cls = spec["view_classes"][view_class]
    visible = cls["min_visible_pixels"]
    flat = np.asarray(beauty).reshape(-1, 3).astype(np.int32)
    per_part = {}
    for subject_id in sorted(visible):
        count = 0
        for color in spec["objects"][subject_id]["beauty_palette"]:
            count += int(np.count_nonzero(np.all(flat == np.array(color, dtype=np.int32), axis=1)))
        per_part[subject_id] = count
    total = sum(per_part.values())
    floor = max(visible.values())
    return {
        "per_part_palette_px": per_part,
        "total_palette_px": total,
        "counterfactual_floor": floor,
        "old_totals_gate_would_pass": bool(total >= floor),
        "note": SMOKE_NOTE,
    }
