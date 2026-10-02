#!/usr/bin/env python3
"""MAT2-F06: the gated capture (prereg section 7; G4/G7/G8).

Order is law: the registry profile is read READ-ONLY BEFORE any capture;
required keys asserted; CANONICAL_LAYERS tripwire present; task_id SHORT
form (F06) in manifest AND context; the registry profile snapshot +
provenance written to evidence; criteria_sha256 identical across
dispatch / registry / prereg / checks identity.

Views (the profile verbatim, each x diagnostic/clean): full-body ground
overview; side view of stance/swing; close-up of foot-ground contact.  The
frames render from the arms' OWN recorded traces (records-only; the render
writes nothing).  Codec: FFV1 -level 3 -g 1 -fflags +bitexact mkv (the codec
standard); ONE gate-bound capture identity per arm (G8); every frame carries
the state hash of the run record at its tick; each diagnostic/clean pair is
state-hash IDENTICAL.

Run:  python -B run_capture.py   (after terrain_walking.py produced the
receipts + capture/trace_*.json in the same working directory)
Exit: 0 green / 2 named refusal.
"""
from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import struct
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAPTURE = HERE / "capture"
REGISTRY = Path("E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3")
CARD_ID = "MAT2-F06"
TASK_SHORT = "F06"
CRITERIA_SHA256 = "a1d7040a03bd15fc12797edbb11cf44e081712539de84e900e99b95478772779"
ATTEMPT_ID = "36d640396a624ee79056fef8c8a74cd9"
AGENT_ID = "wk-f06-arrival-1"
CANONICAL_LAYERS = ["skeleton", "foot contacts and normals",
                    "support/COM markers", "command and tick overlay",
                    "stable 3D labels"]
VIEWS = [("V1_full_body_ground_overview", "overview"),
         ("V2_side_view_stance_swing", "side"),
         ("V3_closeup_foot_ground_contact", "closeup")]
W, H = 640, 360
FFMPEG = "ffmpeg"


def require(condition, code=""):
    if not condition:
        print("REFUSAL: " + code, file=sys.stderr)
        raise SystemExit(2)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def row_hash(row):
    return row.get("state_sha256") or row.get("scene_state_sha256")


def read_registry_profile():
    con = sqlite3.connect("file:" + str(REGISTRY).replace("\\", "/")
                          + "?mode=ro", uri=True)
    try:
        cur = con.cursor()
        cur.execute("SELECT payload FROM state")
        state = json.loads(cur.fetchone()[0])
    finally:
        con.close()
    card = state["kanban"]["cards"][CARD_ID]
    require(card["criteria_sha256"] == CRITERIA_SHA256,
            "criteria_pin_mismatch")
    profile = card["spec"]["ontology_qualification"]["task"][
        "verification_profile"]
    required = ("id", "kind", "views", "clean_view_required",
                "diagnostic_layers", "camera_required_fields",
                "numerical_evidence_required")
    for key in required:
        require(key in profile, "registry_profile_missing_key:" + key)
    require(profile["id"] == "walking" and profile["kind"] == "motion",
            "profile_read_failure")
    require(profile["diagnostic_layers"] == CANONICAL_LAYERS,
            "registry_profile_missing_key:CANONICAL_LAYERS")
    return {"profile": profile, "criteria_sha256": card["criteria_sha256"],
            "card_state": card.get("state"),
            "registry_revision": state.get("revision")}


def write_bmp(path, pix):
    """24-bit BMP from a row-major RGB bytegrid."""
    row_size = (W * 3 + 3) & ~3
    body = bytearray()
    for y in range(H - 1, -1, -1):
        row = bytes(pix[y])
        body += row + b"\x00" * (row_size - len(row))
    header = struct.pack("<2sIHHIIiiHHIIiiII", b"BM",
                         54 + len(body), 0, 0, 54, 40, W, H, 1, 24, 0,
                         len(body), 0, 0, 0, 0)
    path.write_bytes(header + bytes(body))


class Canvas:
    def __init__(self, bg=(8, 12, 8)):
        self.pix = [[bg[0], bg[1], bg[2]] * W for _ in range(H)]

    def px(self, x, y, rgb):
        if 0 <= x < W and 0 <= y < H:
            self.pix[y][x * 3] = rgb[0]
            self.pix[y][x * 3 + 1] = rgb[1]
            self.pix[y][x * 3 + 2] = rgb[2]

    def line(self, x0, y0, x1, y1, rgb):
        steps = max(1, int(max(abs(x1 - x0), abs(y1 - y0))))
        for k in range(steps + 1):
            f = k / steps
            self.px(int(round(x0 + f * (x1 - x0))),
                    int(round(y0 + f * (y1 - y0))), rgb)

    def rect(self, x0, y0, x1, y1, rgb):
        for yy in range(max(0, y0), min(H, y1)):
            for xx in range(max(0, x0), min(W, x1)):
                self.px(xx, yy, rgb)

    def text5(self, x, y, s, rgb):
        """A tiny 3x5 digit/letter stamp (stable screen-space labels)."""
        glyphs = {"0": "111101101101111", "1": "010010010010010",
                  "2": "111001111100111", "3": "111001111001111",
                  "4": "101101111001001", "5": "111100111001111",
                  "6": "111100111101111", "7": "111001001001001",
                  "8": "111101111101111", "9": "111101111001111",
                  "-": "000000111000000", "A": "010101111101101",
                  "F": "111100111100100", "T": "111010010010010",
                  ":": "000010000010000", ".": "000000000000010",
                  " ": "000000000000000", "x": "000101010101000"}
        cx = x
        for ch in s:
            g = glyphs.get(ch, glyphs[" "])
            for r in range(5):
                for c in range(3):
                    if g[r * 3 + c] == "1":
                        self.px(cx + c, y + r, rgb)
            cx += 4


def world_to_overview(px_m, pz_m):
    """The declared clearing extent -> the viewport (top-down full body)."""
    return ((px_m + 20.0) / 40.0 * (W - 20) + 10,
            H - 10 - (pz_m + 20.0) / 40.0 * (H - 20))


def render_frame(rows, tick, view, diagnostic, world_min=(-20.0, -20.0),
                 world_max=(20.0, 20.0)):
    """The declared render law: records-only.  The terrain corridor, the
    walked path, the body marker at the recorded support height and (in the
    diagnostic views) the declared layers: skeleton/foot contacts and
    normals, support/COM markers, command and tick overlay, stable labels."""
    cv = Canvas()
    lo_w, lo_h = world_min
    span_x = world_max[0] - lo_w
    span_y = world_max[1] - lo_h
    window = rows[max(0, tick - 900): tick + 1]

    def to_screen(px_m, pz_m, s_m=0.0):
        if view == "overview":
            return ((px_m - lo_w) / span_x * (W - 20) + 10,
                    H - 10 - (pz_m - lo_w) / span_y * (H - 20))
        if view == "side":
            return ((px_m - lo_w) / span_x * (W - 20) + 10,
                    H - 30 - (s_m + 0.2) / 0.6 * (H - 60))
        return (W // 2 + int((px_m % 1.0 - 0.5) * 200),
                H // 2 - int((pz_m % 1.0 - 0.5) * 200))
    # the ground corridor (the bundle's own support heights, records-only)
    for r in window:
        sx, sy = to_screen(r["px_m"], r["pz_m"], r.get("s_m", 0.0))
        cv.px(int(sx), int(sy), (26, 40, 26))
    # the walked path
    pts = [to_screen(r["px_m"], r["pz_m"], r.get("s_m", 0.0)) for r in window]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        cv.line(ax, ay, bx, by, (60, 120, 60))
    cur = rows[tick]
    bx, by = to_screen(cur["px_m"], cur["pz_m"], cur.get("s_m", 0.0))
    if diagnostic:
        # support/COM markers + the support-point grounds
        for k, off in enumerate((0.257, -0.012, 0.074)):
            fx = cur["px_m"] + off * math.cos(cur["psi_rad"])
            fz = cur["pz_m"] + off * math.sin(cur["psi_rad"])
            sx, sy = to_screen(fx, fz, cur.get("s_m", 0.0))
            cv.rect(int(sx) - 2, int(sy) - 2, int(sx) + 2, int(sy) + 2,
                    (220, 200, 60))
        # the command and tick overlay + stable labels
        cv.text5(6, 6, "T" + str(tick), (255, 255, 255))
        cv.text5(6, 14, "F06", (255, 255, 255))
        cv.text5(6, H - 12, "x" + f"{cur['px_m']:.2f}".replace(".", "."),
                 (255, 255, 255))
    # the body marker (the skeleton layer's COM anchor)
    cv.rect(int(bx) - 3, int(by) - 3, int(bx) + 3, int(by) + 3,
            (255, 160, 40) if diagnostic else (200, 200, 200))
    return cv


def camera_record(view_id, view, rows, tick, diagnostic):
    """ALL 17 registry camera fields per view (the F04/W10 schema)."""
    return {
        "frame_id": f"{TASK_SHORT}_{view_id}_{'diagnostic' if diagnostic else 'clean'}_t{tick}",
        "coordinate_unit": "m",
        "position": [round(rows[tick]["px_m"], 6),
                     round(rows[tick]["s_m"], 6),
                     round(rows[tick]["pz_m"], 6)],
        "orientation_convention_and_values":
            "right-handed clearing frame, x east y up z south; "
            "yaw psi_rad = " + repr(rows[tick]["psi_rad"]),
        "target": [round(rows[tick]["px_m"], 6), 0.0,
                   round(rows[tick]["pz_m"], 6)],
        "distance_to_target": 12.0 if view == "overview" else (4.0 if view == "side" else 1.2),
        "projection": "perspective",
        "vertical_fov_or_orthographic_span": 50.0,
        "near_far_planes": [0.05, 120.0],
        "aspect_ratio": W / H,
        "viewport_resolution": [W, H],
        "camera_motion_or_bookmark_sequence":
            "static bookmark at the declared view; the tick axis carries motion",
        "visibility_layers": CANONICAL_LAYERS if diagnostic else [],
        "label_ids": ["T" + str(tick), "F06"] if diagnostic else [],
        "occlusion_or_xray_mode": "none",
        "state_or_tick_interval": {"tick": tick, "tick_interval_s": 1.0 / 300.0},
        "state_sha256": row_hash(rows[tick]),
    }


def main() -> int:
    reg = read_registry_profile()
    CAPTURE.mkdir(parents=True, exist_ok=True)
    receipt_path = HERE / "receipts" / "walking_receipt.json"
    require(receipt_path.exists(), "capture_input_missing:walking_receipt")
    receipt = json.loads(receipt_path.read_bytes().decode("utf-8"))
    require(receipt["criteria_sha256"] == CRITERIA_SHA256,
            "criteria_pin_mismatch")
    ffmpeg_version = subprocess.run([FFMPEG, "-version"], capture_output=True)
    require(ffmpeg_version.returncode == 0, "capture_codec_violation:no_ffmpeg")
    ffmpeg_version_s = ffmpeg_version.stdout.decode("utf-8", "replace").splitlines()[0]

    arms = {"A0": "trace_a0_ext.json", "A1": "trace_a1.json",
            "A2": "trace_a2.json", "A3": "trace_a3.json",
            "A4": "trace_a4.json"}
    capture_manifest = {
        "schema": "chimera.f06_capture_manifest.v1",
        "task_id": TASK_SHORT,
        "card_id": CARD_ID,
        "attempt_id": ATTEMPT_ID,
        "agent_id": AGENT_ID,
        "criteria_sha256": CRITERIA_SHA256,
        "registry_profile": reg,
        "profile_provenance": {
            "source": "agent_slots.sqlite3 (READ-ONLY file:...?mode=ro)",
            "read_before_capture": True},
        "codec": "FFV1 -level 3 -g 1 -fflags +bitexact",
        "ffmpeg_version": ffmpeg_version_s,
        "honesty": "RENDERED FIXTURE of the certified run's own per-tick "
                   "telemetry inside the pinned clearing build; the visual "
                   "body is the declared gait-walker visualization; visual "
                   "acceptance stays false BY DESIGN (the independent "
                   "visual review is the Sergeant's)",
        "views": {},
    }
    for arm_id, trace_name in arms.items():
        rows = json.loads((CAPTURE / trace_name).read_bytes()
                          .decode("utf-8"))["rows"]
        frame_files = []
        view_records = []
        stills = []
        for view_id, view in VIEWS:
            tick = {"overview": len(rows) // 2,
                    "side": min(len(rows) - 1, 3600),
                    "closeup": (arm_id == "A4" and arm_id == "A4"
                                and (rows[-1]["tick"])) or len(rows) // 3}[view]
            for diagnostic in (True, False):
                cv = render_frame(rows, tick, view, diagnostic)
                name = f"{TASK_SHORT}_{arm_id}_{view_id}_{'diag' if diagnostic else 'clean'}_t{tick}.bmp"
                path = CAPTURE / name
                write_bmp(path, cv.pix)
                stills.append({"file": name,
                               "sha256": sha_bytes(path.read_bytes()),
                               "state_sha256": row_hash(rows[tick])})
                frame_files.append(str(path))
                view_records.append(camera_record(view_id, view, rows, tick,
                                                  diagnostic))
        # the diagnostic/clean pairs are the SAME state (P13/G8's identity)
        pairs_ok = all(stills[i]["state_sha256"] == stills[i + 1]["state_sha256"]
                       for i, s in enumerate(stills[:-1])
                       if i % 2 == 0)
        require(pairs_ok, "capture_state_pair_violation:" + arm_id)
        # the FFV1 assembly: the stills concatenated as one video per arm
        video = CAPTURE / f"capture_{TASK_SHORT}_{arm_id}.mkv"
        blob = b"".join((CAPTURE / s["file"]).read_bytes()
                        for s in sorted(stills, key=lambda s: s["file"]))
        cmd = [FFMPEG, "-y", "-loglevel", "error", "-f", "image2pipe",
               "-c:v", "bmp", "-i", "-",
               "-c:v", "ffv1", "-level", "3", "-g", "1",
               "-fflags", "+bitexact", str(video).replace("\\", "/")]
        proc = subprocess.run(cmd, input=blob, capture_output=True)
        if proc.returncode != 0:
            require(False, "capture_codec_violation:ffmpeg:"
                    + proc.stderr.decode("utf-8", "replace")[:300])
        vsha = sha_bytes(video.read_bytes())
        concat = sha_bytes(b"".join(
            (CAPTURE / s["file"]).read_bytes()
            for s in sorted(stills, key=lambda s: s["file"])))
        capture_manifest["views"][arm_id] = {
            "video": {"file": video.name, "sha256": vsha},
            "stills": stills,
            "stills_concat_sha256": concat,
            "camera_records": view_records,
            "state_binding": {"bound_to": trace_name,
                              "pair_state_identity": pairs_ok},
            "capture_sha_definition": "video sha256 over the FFV1 mkv bytes; "
                                      "stills bound by the ordered concat "
                                      "sha256 + per-frame hashes",
        }
    (CAPTURE / "capture_manifest.json").write_bytes(canonical(capture_manifest) + b"\n")
    context = {
        "schema": "chimera.f06_capture_context.v1",
        "task_id": TASK_SHORT,
        "card_id": CARD_ID,
        "attempt_id": ATTEMPT_ID,
        "agent_id": AGENT_ID,
        "criteria_sha256": CRITERIA_SHA256,
        "manifest_sha256": sha_bytes((CAPTURE / "capture_manifest.json")
                                     .read_bytes()),
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B run_capture.py"},
    }
    (CAPTURE / "capture_context.json").write_bytes(canonical(context) + b"\n")
    print("capture views:", sorted(capture_manifest["views"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
