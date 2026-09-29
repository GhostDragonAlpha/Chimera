"""Measure V1 pixel extents of the declared subjects in the committed gate
still (review-blocker C1 correction, sgt-pr257-b76fb4d).

The previous report hand-wrote a qualitative scale claim ("sub-2-px") that
pixel measurement of the committed still contradicted. This probe makes the
disclosure MEASURED: it reads evidence/checks.json (p7 marker positions and
the capture binding), re-measures the committed gate artifact still with a
fixed deterministic blob method and emits evidence/pixel_extents.json, from
which make_report.py generates the disclosure sentence. Every measured value
is computed here -- none is hand-typed:

- background ground RGB is measured at the marker_spawn ground marker;
- subject list, marker names and marker pixel positions come from
  checks.json p7_markers;
- the still is bound by sha256 to checks.capture.capture_sha256.

Method (fixed, deterministic, integer-only): anchor = truncated marker
coordinates; window = inclusive offsets [-16, +16] px in both axes, clamped
to the still; a pixel passes if its squared euclidean RGB distance from the
measured background exceeds 15**2; recorded per subject: threshold-passing
pixel count and the axis-aligned bounding box of the passing pixels.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"

SCHEMA = "chimera.mat2_f07.pixel_extents.v1"
VIEW = "V1_clearing_overview"
GROUND_MARKER = "marker_spawn"
WINDOW_HALF_WIDTH_PX = 16
THRESHOLD_GT = 15
SUB_TWO_PX_MAX_WIDTH = 2


class Refusal(Exception):
    def __init__(self, code, detail=""):
        super().__init__("%s: %s" % (code, detail))


def require(condition, code, detail=""):
    if not condition:
        raise Refusal(code, detail)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def decode_bmp(raw):
    require(raw[:2] == b"BM", "f07_pixel_probe_not_a_bmp")
    data_offset = struct.unpack_from("<I", raw, 10)[0]
    width, height = struct.unpack_from("<ii", raw, 18)
    bpp = struct.unpack_from("<H", raw, 28)[0]
    require(bpp == 24, "f07_pixel_probe_unsupported_bpp", str(bpp))
    require(width > 0 and height > 0, "f07_pixel_probe_bad_size")
    row_size = (width * 3 + 3) // 4 * 4
    require(len(raw) >= data_offset + row_size * height,
            "f07_pixel_probe_truncated_bmp")
    rows = []
    for y in range(height):
        base = data_offset + (height - 1 - y) * row_size  # bottom-up
        row = []
        for x in range(width):
            b, g, r = raw[base + 3 * x: base + 3 * x + 3]
            row.append((r, g, b))
        rows.append(row)
    return width, height, rows


def blob(width, height, rows, anchor_x, anchor_y, background):
    x0 = max(0, anchor_x - WINDOW_HALF_WIDTH_PX)
    x1 = min(width - 1, anchor_x + WINDOW_HALF_WIDTH_PX)
    y0 = max(0, anchor_y - WINDOW_HALF_WIDTH_PX)
    y1 = min(height - 1, anchor_y + WINDOW_HALF_WIDTH_PX)
    br, bg_, bb = background
    passing = []
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            r, g, b = rows[y][x]
            if (r - br) ** 2 + (g - bg_) ** 2 + (b - bb) ** 2 > \
                    THRESHOLD_GT * THRESHOLD_GT:
                passing.append((x, y))
    if not passing:
        return {"pixels": 0, "bbox_w_px": 0, "bbox_h_px": 0,
                "min_x_px": -1, "max_x_px": -1, "min_y_px": -1,
                "max_y_px": -1}
    xs = [p[0] for p in passing]
    ys = [p[1] for p in passing]
    return {"pixels": len(passing),
            "bbox_w_px": max(xs) - min(xs) + 1,
            "bbox_h_px": max(ys) - min(ys) + 1,
            "min_x_px": min(xs), "max_x_px": max(xs),
            "min_y_px": min(ys), "max_y_px": max(ys)}


def main():
    checks_bytes = (EVIDENCE / "checks.json").read_bytes()
    checks = json.loads(checks_bytes)
    capture = checks["capture"]
    gate_artifact = capture["gate_artifact"]
    still_path = HERE / gate_artifact
    require(still_path.is_file(), "f07_pixel_probe_still_missing",
            gate_artifact)
    still_bytes = still_path.read_bytes()
    still_sha = sha_bytes(still_bytes)
    require(still_sha == capture["capture_sha256"],
            "f07_pixel_probe_still_sha_mismatch", gate_artifact)

    p7 = checks["p7_markers"]
    rows = p7["rows"]
    v1_rows = [r for r in rows if r["view"] == VIEW]
    require(v1_rows, "f07_pixel_probe_no_v1_rows")
    spawn_rows = [r for r in v1_rows if r["marker"] == GROUND_MARKER]
    require(len(spawn_rows) == 1, "f07_pixel_probe_spawn_row_not_unique")
    spawn = spawn_rows[0]

    width, height, pixels = decode_bmp(still_bytes)

    anchor = (int(spawn["pixel_px"][0]), int(spawn["pixel_px"][1]))
    require(0 <= anchor[0] < width and 0 <= anchor[1] < height,
            "f07_pixel_probe_spawn_marker_off_still", str(anchor))
    background = pixels[anchor[1]][anchor[0]]

    obstacle_ids = [ob["id"] for ob in checks["p1_tied_assets"]
                    ["per_obstacle"]]

    subjects = []
    for row in v1_rows:
        if row["marker"] == GROUND_MARKER:
            continue
        sx, sy = row["pixel_px"]
        subject_anchor = (int(sx), int(sy))
        require(0 <= subject_anchor[0] < width
                and 0 <= subject_anchor[1] < height,
                "f07_pixel_probe_subject_marker_off_still",
                row["marker"])
        measured = blob(width, height, pixels,
                        subject_anchor[0], subject_anchor[1], background)
        subjects.append({
            "marker": row["marker"],
            "hit_surface_id": row["hit_surface_id"],
            "pixel_px": [sx, sy],
            "anchor_px": [subject_anchor[0], subject_anchor[1]],
            "declared_obstacle": row["hit_surface_id"] in obstacle_ids,
            "sub_two_px_width":
                measured["bbox_w_px"] <= SUB_TWO_PX_MAX_WIDTH,
            **measured,
        })
    subjects.sort(key=lambda s: s["marker"])

    doc = {
        "schema": SCHEMA,
        "generated_by": "measure_pixel_extents.py",
        "method": {
            "still": gate_artifact,
            "still_sha256": still_sha,
            "checks_sha256": sha_bytes(checks_bytes),
            "still_size_px": [width, height],
            "background_rule":
                "pixel measured at the %s ground marker truncated anchor"
                % GROUND_MARKER,
            "background_rgb": list(background),
            "threshold_rule": "squared euclidean rgb distance from the "
                              "measured background exceeds the square of "
                              "the threshold",
            "threshold_gt": THRESHOLD_GT,
            "window_rule": "inclusive pixel offsets around the truncated "
                           "marker anchor, clamped to the still",
            "window_half_width_px": WINDOW_HALF_WIDTH_PX,
            "bbox_rule": "axis-aligned bounding box of the threshold-"
                         "passing pixels inside the window",
            "sub_two_px_max_width_px": SUB_TWO_PX_MAX_WIDTH,
        },
        "obstacle_order": obstacle_ids,
        "subjects": subjects,
        "sub_two_px_subjects": [s["marker"] for s in subjects
                                if s["sub_two_px_width"]],
    }
    out = EVIDENCE / "pixel_extents.json"
    out.write_bytes(canonical(doc))
    print("pixel_extents.json written: %d subjects; background rgb %s"
          % (len(subjects), list(background)))
    for s in subjects:
        print("  %-24s px=%4d bbox=%2dx%-2d%s"
              % (s["marker"], s["pixels"], s["bbox_w_px"], s["bbox_h_px"],
                 " SUB_2PX" if s["sub_two_px_width"] else ""))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Refusal as refusal:
        print("REFUSAL %s" % refusal)
        sys.exit(1)
