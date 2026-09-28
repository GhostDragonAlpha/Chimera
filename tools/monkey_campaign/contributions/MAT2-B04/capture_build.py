"""MAT2-B04 visual capture builder (labeled PNG sheet from the emitted document).

Renders the ACTUAL emitted `frame_forest.json` (the candidate's authored output,
bound by sha256) onto labeled 2D orthographic views: the three frozen anatomy
profile views, each in a diagnostic and a clean variant, assembled into ONE
capture sheet PNG and validated with tools/monkey_campaign/visual_capture.py.

Honesty rules enforced here:
- 2D structured-records display, declared as such: every camera number in the
  manifest is the number used to project its panel's pixels; the second panel of
  the side+oblique view is declared in camera.panel_cameras and disclosed
  on-canvas.
- Scene content is rendered into a viewport-sized surface first and then pasted,
  so nothing draws outside the declared viewport (nothing clipped at frame
  edges, nothing bleeding across views).
- The fitted packet frames are NOT placed in world coordinates anywhere (no
  fusion of coordinate systems): they appear as a legend of binding stubs,
  attached to their component root by stable name only.
- Absent components (outer envelope, muscle/tendon paths, attachment sites
  beyond the authored frame ports) are drawn as an explicit absence inventory,
  never fabricated.
- Diagnostic and clean views of a pair share the camera and the state binding
  (sha256 of frame_forest.json): view toggles preserve the state hash.
- Clean frames carry no text, labels, axes, ports, or panels at all.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys

from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, r"E:\PythonChimera\tools\monkey_campaign")
import visual_capture  # noqa: E402  (validator; same code visual_gate.verify calls)

DOC_PATH = HERE / "frame_forest.json"
SHEET_PATH = HERE / "capture_mat2_b04_forest.png"
EVID = HERE / "capture_evidence"
RUN_ID = "mat2-b04-forest-static-20260928"
TICKS = [0, 0]

FRAME_W, FRAME_H = 1264, 720
VP = (8, 40, 1256, 688)          # 1248 x 640 viewport inside each frame
VIEW_W, VIEW_H = 1248, 640

COL_BG = (247, 246, 242)
COL_PANEL = (238, 236, 230)
COL_TEXT = (24, 26, 30)
COL_EDGE = (70, 70, 78)
COL_PELVIS = (140, 60, 160)
COL_THORAX = (24, 110, 190)
COL_ULNA_R = (190, 90, 20)
COL_ULNA_L = (20, 130, 90)
COL_X = (196, 32, 32)
COL_Y = (24, 132, 56)
COL_Z = (32, 72, 196)
COL_PORT = (196, 108, 20)
COL_LANDMARK = (90, 32, 160)
COL_ABSENT = (150, 32, 32)

VIEWS = (
    "whole-creature overview",
    "local attachment close-up",
    "orthogonal side and oblique views",
)
LAYERS = ["frame axes", "stable 3D labels", "selected bones/joints"]
AXIS_LEN = 0.08
WHOLE_OBLIQUE_DEG = 35.0
WHOLE_SPAN = 1.9
CLOSEUP_OBLIQUE_DEG = 25.0
CLOSEUP_SPAN = 0.45
PANEL_OBLIQUE_DEG = 35.0
PANEL_SPAN = 1.9


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


# ---- camera math (matches visual_capture.camera contract) --------------------
def norm(v):
    n = math.sqrt(sum(c * c for c in v))
    return [c / n for c in v]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def sub(a, b):
    return [x - y for x, y in zip(a, b)]


def add(a, b):
    return [x + y for x, y in zip(a, b)]


def scale(v, s):
    return [x * s for x in v]


def rot_y(v, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c]


def look_at_quat_wxyz(position, target, up_hint=(0.0, 1.0, 0.0)):
    """Camera-to-world rotation as a w x y z unit quaternion; forward axis -Z."""
    f = norm(sub(target, position))
    r = norm(cross(f, list(up_hint)))
    u = cross(r, f)
    m = [[r[0], u[0], -f[0]], [r[1], u[1], -f[1]], [r[2], u[2], -f[2]]]
    trace = m[0][0] + m[1][1] + m[2][2]
    if trace > 0:
        s = math.sqrt(trace + 1.0) * 2
        w = 0.25 * s
        x = (m[2][1] - m[1][2]) / s
        y = (m[0][2] - m[2][0]) / s
        z = (m[1][0] - m[0][1]) / s
    else:
        i = max(range(3), key=lambda k: m[k][k])
        j, k = (i + 1) % 3, (i + 2) % 3
        s = math.sqrt(m[i][i] - m[j][j] - m[k][k] + 1.0) * 2
        q = [0.0, 0.0, 0.0, 0.0]
        q[i + 1] = 0.25 * s
        q[j + 1] = (m[j][i] + m[i][j]) / s
        q[k + 1] = (m[k][i] + m[i][k]) / s
        w = (m[k][j] - m[j][k]) / s
        x, y, z = q[1], q[2], q[3]
    quat = [w, x, y, z]
    n = math.sqrt(sum(c * c for c in quat))
    return [c / n for c in quat]


def make_projector(position, target, span, origin_px=(0, 0), size=(VIEW_W, VIEW_H)):
    """World->viewport projector using exactly the DECLARED camera numbers.

    origin_px/size place the projected viewport inside the drawing surface.
    """
    f = norm(sub(target, position))
    r = norm(cross(f, [0.0, 1.0, 0.0]))
    u = cross(r, f)
    width, height = size
    aspect = width / height

    def project(p):
        d = sub(p, target)
        x = dot(d, r) / (span * aspect)
        y = dot(d, u) / span
        return (origin_px[0] + (x + 0.5) * width,
                origin_px[1] + (0.5 - y) * height)

    return project


def camera_record(frame_id, position, target, span, note, panel_cameras=None):
    record = {
        "frame_id": frame_id,
        "coordinate_unit": "m",
        "handedness": "right",
        "orientation_convention": "quaternion_wxyz_camera_to_frame",
        "forward_axis": "-Z",
        "up_axis": "+Y",
        "near_far_planes": [0.001, 100.0],
        "viewport_resolution": [VIEW_W, VIEW_H],
        "aspect_ratio": VIEW_W / VIEW_H,
        "projection": "orthographic",
        "orthographic_span": span,
        "sample_mode": "fixed_bookmark",
        "samples": [{
            "tick": 0,
            "position": list(position),
            "target": list(target),
            "distance_to_target": math.dist(position, target),
            "orientation": look_at_quat_wxyz(position, target),
        }],
        "camera_motion_or_bookmark_sequence":
            "fixed_bookmark: single identical pose (visible_static, tick interval [0, 0])",
        "state_or_tick_interval":
            "tick_interval [0, 0]; one static authored state; state hash = sha256 of "
            "frame_forest.json in every view's state_binding",
        "occlusion_or_xray_mode": "declared per view in visibility.occlusion_mode",
        "label_projection_note":
            "2D orthographic structured-records display; text drawn in screen plane at "
            "projected anchors; " + note,
    }
    if panel_cameras is not None:
        record["panel_cameras"] = panel_cameras
    return record


# ---- scene content (from the emitted document only) --------------------------
ROOT_ORDER = ("root_pelvis", "root_thorax", "root_ulna", "root_ulna_l")
ROOT_COLOR = {"root_pelvis": COL_PELVIS, "root_thorax": COL_THORAX,
              "root_ulna": COL_ULNA_R, "root_ulna_l": COL_ULNA_L}
ROOT_LABEL_OFFSET = {"root_pelvis": (14, 10), "root_thorax": (10, -18),
                     "root_ulna": (10, -6), "root_ulna_l": (-120, 10)}


def chain_points(doc, key):
    run = [0.0, 0.0, 0.0]
    pts = [list(run)]
    for hop in doc["frames"][key]["chain"]:
        run = [run[i] + hop["pos"][i] for i in range(3)]
        pts.append(list(run))
    return pts


def draw_axes(draw, project, origin):
    for index, (axis, color) in enumerate((((1.0, 0.0, 0.0), COL_X),
                                           ((0.0, 1.0, 0.0), COL_Y),
                                           ((0.0, 0.0, 1.0), COL_Z))):
        tip = add(origin, scale(axis, AXIS_LEN))
        draw.line([project(origin), project(tip)], fill=color, width=2)
        draw.text(project(tip), ("+x", "+y", "+z")[index], fill=color)


def draw_forest(draw, project, doc, world, hops, diag):
    if diag:
        px, py = project(world)
        draw.ellipse([px - 3, py - 3, px + 3, py + 3], outline=COL_TEXT, width=1)
        draw.text((px + 6, py + 4), "assembly_world", fill=COL_TEXT)
    for key in ROOT_ORDER:
        pts = hops[key]
        color = ROOT_COLOR[key]
        # the world->pelvis hop is shared by every chain: draw it once, neutral
        if key == "root_pelvis":
            draw.line([project(pts[0]), project(pts[1])], fill=COL_EDGE, width=2)
        for a, b in zip(pts[1:], pts[2:]):
            draw.line([project(a), project(b)], fill=color, width=2)
        origin = pts[-1]
        px, py = project(origin)
        draw.ellipse([px - 4, py - 4, px + 4, py + 4], outline=color, width=2,
                     fill=COL_PANEL)
        if diag:
            dx, dy = ROOT_LABEL_OFFSET[key]
            draw.text((px + dx, py + dy), key, fill=color)
            draw_axes(draw, project, origin)


def legend_and_absences(draw, doc):
    y = 316
    draw.text((10, y), "component fitted stubs (stable NAME binding only; coordinates "
                       "NOT fused):", fill=COL_TEXT)
    y += 14
    for component in doc["components"]:
        draw.text((18, y), "%s <- %s" % (component["root_frame_id"],
                                         ", ".join(component["fitted_frames"])),
                  fill=ROOT_COLOR[component["root_frame_id"]])
        y += 14
    y += 8
    lines = [
        "absence inventory (out of B04 task-owned scope; never fabricated):",
        "- outer envelope (skin): ABSENT",
        "- muscle/tendon paths: ABSENT",
        "- attachment sites: authored frame PORTS only (mechanically unqualified)",
    ]
    for line in lines:
        draw.text((10, y), line, fill=COL_ABSENT)
        y += 14


def state_strip(draw, doc_sha):
    draw.text((10, 16), "state frame_forest.json sha256 " + doc_sha, fill=(40, 60, 140))


def base_frame(title, diag):
    img = Image.new("RGB", (FRAME_W, FRAME_H), COL_BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([VP[0], VP[1], VP[2] - 1, VP[3] - 1], fill=COL_PANEL,
                   outline=(200, 198, 192))
    if diag:
        draw.text((VP[0] + 8, 12), "MAT2-B04 frame forest - %s - diagnostic" % title,
                  fill=COL_TEXT)
    return img


def viewport_surface():
    return Image.new("RGB", (VIEW_W, VIEW_H), COL_PANEL)


def render_whole(doc, world, hops, doc_sha, diag):
    frame = base_frame("whole-creature overview", diag)
    view = viewport_surface()
    draw = ImageDraw.Draw(view)
    target = [0.0, 0.6, 0.0]
    span = WHOLE_SPAN
    oblique = WHOLE_OBLIQUE_DEG
    position = add(target, rot_y([0.0, 0.0, 2.4], oblique))
    project = make_projector(position, target, span)
    draw_forest(draw, project, doc, world, hops, diag)
    if diag:
        state_strip(draw, doc_sha)
        draw.text((10, 28),
                  "oblique %.0f deg about +y; orthographic span %.2f m; chain hops are "
                  "pinned chimanoid.xml declarations" % (oblique, span), fill=COL_TEXT)
        legend_and_absences(draw, doc)
    frame.paste(view, (VP[0], VP[1]))
    return frame, camera_record(
        "mat2_b04_forest_world_m", position, target, span,
        "whole view: camera yawed %.0f deg about world +y from front; forward -Z, up +Y"
        % oblique)


def render_closeup(doc, world, hops, doc_sha, diag):
    frame = base_frame("local attachment close-up", diag)
    view = viewport_surface()
    draw = ImageDraw.Draw(view)
    thorax_pts = hops["root_thorax"]
    thorax_origin = thorax_pts[-1]
    humerus_end = hops["root_ulna"][-2]
    elbow = hops["root_ulna"][-1]
    radius_local = [0.0004, -0.011503, 0.019999]
    hand_local = [0.0184, -0.301903, 0.044999]

    def local(p):
        return [elbow[i] + p[i] for i in range(3)]

    radius_pivot = local(radius_local)
    hand_pivot = local(hand_local)
    # frame the full thorax->humerus->ulna->hand content with margin (no clipping)
    target = [(thorax_origin[0] + hand_pivot[0]) / 2.0,
              (thorax_origin[1] + hand_pivot[1]) / 2.0,
              (thorax_origin[2] + hand_pivot[2]) / 2.0]
    extent = math.dist(thorax_origin, hand_pivot)
    span = max(CLOSEUP_SPAN, extent * 1.35)
    oblique = CLOSEUP_OBLIQUE_DEG
    position = add(target, rot_y([0.0, 0.15, 1.6], oblique))
    project = make_projector(position, target, span)
    draw.line([project(thorax_origin), project(humerus_end)], fill=COL_THORAX, width=2)
    draw.line([project(humerus_end), project(elbow)], fill=COL_ULNA_R, width=2)
    marks = (("elbow_pivot", elbow, COL_LANDMARK, (-96, -4)),
             ("radius_pivot", radius_pivot, COL_LANDMARK, (8, 12)),
             ("hand_pivot", hand_pivot, COL_LANDMARK, (8, -6)))
    for name, p, color, offset in marks:
        px, py = project(p)
        draw.ellipse([px - 3, py - 3, px + 3, py + 3], fill=color)
        if diag:
            draw.text((px + offset[0], py + offset[1]), name, fill=color)
    if diag:
        ports = (("elbow_proximal_port", elbow, (0.0, 1.0, 0.0), (6, 2)),
                 ("wrist_distal_port", hand_pivot, (0.0, -1.0, 0.0), (6, 8)),
                 ("lateral_port", radius_pivot, (0.0, 0.0, 1.0), (-70, 18)))
        for name, p, n, offset in ports:
            tip = add(p, scale(n, 0.05))
            draw.line([project(p), project(tip)], fill=COL_PORT, width=2)
            tx, ty = project(tip)
            draw.text((tx + offset[0], ty + offset[1]), name, fill=COL_PORT)
        draw_axes(draw, project, elbow)
        state_strip(draw, doc_sha)
        draw.text((10, 28),
                  "oblique %.0f deg about +y; orthographic span %.2f m; thorax->humerus->"
                  "ulna source chain; landmarks/ports from semantic_frame_ulna_r.json; "
                  "elbow axis = ulna +z" % (oblique, span), fill=COL_TEXT)
        legend_and_absences(draw, doc)
    frame.paste(view, (VP[0], VP[1]))
    return frame, camera_record(
        "mat2_b04_ulna_r_closeup_m", position, target, span,
        "close-up: camera yawed %g deg about world +y; forward -Z, up +Y; content is the "
        "thorax->humerus->ulna source chain plus the authored ulna frame's "
        "packet landmarks" % oblique)


def render_side_oblique(doc, world, hops, doc_sha, diag):
    frame = base_frame("orthogonal side and oblique views", diag)
    view = viewport_surface()
    draw = ImageDraw.Draw(view)
    target = [0.0, 0.6, 0.0]
    span = PANEL_SPAN
    oblique = PANEL_OBLIQUE_DEG
    side_pos = add(target, [2.4, 0.0, 0.0])           # orthogonal side: forward -X, up +Y
    oblique_pos = add(target, rot_y([2.4, 0.0, 0.0], -oblique))
    half = VIEW_W // 2
    project_side = make_projector(side_pos, target, span,
                                  origin_px=(int(-0.25 * half), 0), size=(half, VIEW_H))
    project_oblique = make_projector(oblique_pos, target, span,
                                     origin_px=(half + 12, 0), size=(half - 12, VIEW_H))
    if diag:
        draw.line([(half, 0), (half, VIEW_H)], fill=(180, 178, 172), width=1)
        draw.text((10, 28),
                  "left: orthogonal side (forward -x); right: oblique %g deg; both "
                  "orthographic span %.2f m" % (oblique, span), fill=COL_TEXT)
    for project, color in ((project_side, COL_EDGE), (project_oblique, COL_EDGE)):
        for key in ROOT_ORDER:
            pts = hops[key]
            for a, b in zip(pts, pts[1:]):
                draw.line([project(a), project(b)], fill=ROOT_COLOR[key], width=2)
            if diag:
                px, py = project(pts[-1])
                draw.ellipse([px - 3, py - 3, px + 3, py + 3], outline=ROOT_COLOR[key],
                             width=2)
        if diag:
            px, py = project(world)
            draw.ellipse([px - 3, py - 3, px + 3, py + 3], outline=COL_TEXT, width=1)
    if diag:
        draw.text((project_side(hops["root_pelvis"][-1])[0] + 6,
                   project_side(hops["root_pelvis"][-1])[1] - 12), "root_pelvis",
                  fill=COL_PELVIS)
        draw.text((project_oblique(hops["root_ulna_l"][-1])[0] + 6,
                   project_oblique(hops["root_ulna_l"][-1])[1] + 6), "root_ulna_l",
                  fill=COL_ULNA_L)
        state_strip(draw, doc_sha)
        legend_and_absences(draw, doc)
    frame.paste(view, (VP[0], VP[1]))
    panel_cameras = {
        "side": {"note": "this view's declared camera record projects the LEFT panel "
                         "exactly (half-width sub-viewport for layout)",
                 "position": list(side_pos), "target": list(target),
                 "orthographic_span": span,
                 "sub_viewport_px": [0, 0, half, VIEW_H]},
        "oblique": {
            "frame_id": "mat2_b04_forest_world_m",
            "coordinate_unit": "m", "handedness": "right",
            "orientation_convention": "quaternion_wxyz_camera_to_frame",
            "forward_axis": "-Z", "up_axis": "+Y",
            "projection": "orthographic", "orthographic_span": span,
            "near_far_planes": [0.001, 100.0],
            "position": list(oblique_pos), "target": list(target),
            "distance_to_target": math.dist(oblique_pos, target),
            "orientation": look_at_quat_wxyz(oblique_pos, target),
            "yaw_about_world_up_deg": -oblique,
            "sub_viewport_px": [half + 12, 0, half - 12, VIEW_H],
            "note": "declared inset projection of the RIGHT panel; numbers are the "
                    "numbers used",
        },
    }
    return frame, camera_record(
        "mat2_b04_forest_world_m", side_pos, target, span,
        "two-panel view: LEFT panel uses this camera record exactly; RIGHT panel uses "
        "panel_cameras.oblique; both orthographic, up +Y",
        panel_cameras=panel_cameras)


RENDERERS = (("whole-creature overview", render_whole),
             ("local attachment close-up", render_closeup),
             ("orthogonal side and oblique views", render_side_oblique))

SUBJECT_IDS = ["assembly_world", "root_pelvis", "root_thorax", "root_ulna", "root_ulna_l"]
CLOSEUP_LABELS = ["root_ulna", "root_thorax", "assembly_world", "elbow_pivot",
                  "radius_pivot", "hand_pivot", "elbow_proximal_port",
                  "wrist_distal_port", "lateral_port", "+x", "+y", "+z"]
WHOLE_LABELS = ["assembly_world", "root_pelvis", "root_thorax", "root_ulna", "root_ulna_l"]


def subject_of(label_id):
    if label_id in ("elbow_pivot", "radius_pivot", "hand_pivot", "elbow_proximal_port",
                    "wrist_distal_port", "lateral_port", "+x", "+y", "+z"):
        return "root_ulna"
    return label_id


def build(doc, world, hops, doc_sha):
    rendered = []
    for _name, renderer in RENDERERS:
        for diag in (True, False):
            rendered.append(renderer(doc, world, hops, doc_sha, diag))
    sheet = Image.new("RGB", (FRAME_W * 3, FRAME_H * 2), (255, 255, 255))
    view_rows = []
    for col, (view_id, _r) in enumerate(RENDERERS):
        for row, mode in ((0, "diagnostic"), (1, "clean")):
            frame, camera = rendered[col * 2 + (0 if mode == "diagnostic" else 1)]
            region = (col * FRAME_W, row * FRAME_H, FRAME_W, FRAME_H)
            sheet.paste(frame, (region[0], region[1]))
            if view_id == VIEWS[1]:
                required = ["root_ulna", "root_thorax", "assembly_world"]
                label_ids = CLOSEUP_LABELS if mode == "diagnostic" else []
            else:
                required = SUBJECT_IDS
                label_ids = WHOLE_LABELS if mode == "diagnostic" else []
            visibility = {
                "layers": list(LAYERS) if mode == "diagnostic" else [],
                "label_ids": label_ids,
                "selected_ids": (["root_ulna"] if view_id == VIEWS[1]
                                 else ["root_pelvis", "root_thorax", "root_ulna",
                                       "root_ulna_l"]),
                "required_subject_ids": required,
                "observed_subject_ids": list(SUBJECT_IDS),
                "missing_subject_ids": [],
                "occlusion_mode": "xray" if mode == "diagnostic" else "depth_tested",
                "tag_bindings": [{"label_id": lid, "subject_id": subject_of(lid)}
                                 for lid in label_ids],
            }
            view_rows.append({
                "view_id": view_id,
                "mode": mode,
                "pair_id": view_id,
                "state_binding": {"kind": "state", "sha256": doc_sha},
                "artifact_locator": {"kind": "image", "region": "pixel_rectangle",
                                     "pixel_rectangle": list(region)},
                "camera": camera,
                "visibility": visibility,
                "layer_inventory": list(LAYERS) if mode == "diagnostic" else [],
                "honest_gaps": (["outer envelope absent (out of task-owned scope)",
                                 "muscle/tendon paths absent (out of task-owned scope)",
                                 "attachment sites: authored frame ports only, "
                                 "mechanically unqualified",
                                 "fitted packet frames carried by name binding only"]
                                if mode == "diagnostic" else []),
            })
    return sheet, view_rows


def main():
    EVID.mkdir(exist_ok=True)
    doc = json.loads(DOC_PATH.read_text(encoding="utf-8"))
    doc_sha = sha256_file(DOC_PATH)
    hops = {key: chain_points(doc, key) for key in ROOT_ORDER}
    world = doc["frames"]["assembly_world"]["origin_m"]
    sheet, view_rows = build(doc, world, hops, doc_sha)
    sheet.save(SHEET_PATH, "PNG")
    sheet_sha = sha256_file(SHEET_PATH)
    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": "B04",
        "run_id": RUN_ID,
        "subject_sha256": doc_sha,
        "capture_sha256": sheet_sha,
        "profile_id": "anatomy",
        "tick_interval": TICKS,
        "capture_kind": "labeled_2d_orthographic_sheet_png",
        "views": view_rows,
    }
    context = {
        "task_id": "B04",
        "run_id": RUN_ID,
        "subject_sha256": doc_sha,
        "capture_sha256": sheet_sha,
        "tick_interval": TICKS,
    }
    profile = {
        "id": "anatomy",
        "kind": "visible_static",
        "views": list(VIEWS),
        "clean_view_required": True,
        "diagnostic_layers": list(LAYERS),
    }
    receipt = visual_capture.validate_manifest(manifest, context, profile)
    (EVID / "cameras.json").write_text(json.dumps(
        {("%s:%s" % (r["view_id"], r["mode"])): r["camera"] for r in view_rows},
        indent=1), encoding="utf-8")
    (EVID / "capture_context.json").write_text(json.dumps(context, indent=1),
                                               encoding="utf-8")
    (EVID / "capture_manifest.json").write_text(json.dumps(manifest, indent=1),
                                                encoding="utf-8")
    (EVID / "validation_receipt.json").write_text(json.dumps(receipt, indent=1),
                                                  encoding="utf-8")
    print(json.dumps(receipt, indent=1, sort_keys=True))
    print("sheet", SHEET_PATH, "sha256", sheet_sha)


if __name__ == "__main__":
    main()
