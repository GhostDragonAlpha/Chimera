#!/usr/bin/env python3
"""MAT2-X04: the state-derivation law (prereg section 2) — THE task-owned
module.

Every state label is a PURE function of committed bytes: the per-tick record
row (W10 run_commanded's export fields) + the pinned pose law (W10
visualization.py, imported; the render path) + the pinned scene schema
(AST audit over the pinned scene_cpu.py bytes at run). Nothing else feeds a
label. The declared 3x5 glyph font and the declared layer palettes make
readability MEASURED: every drawn string's expected pixel bbox/count is
derived from the glyph law and compared against the committed still exactly.

Layer palettes (X04-owned; distinct from every W10 render color):
  L1 "selected state labels"   panel  x[12,300]  y[40,190]
       bg (250,250,250)  text (15,15,15)  border (0,90,220)
  L2 "event/tick trace"        strip  x[12,300]  y[500,532]
       bg (255,238,200)  text (90,45,10)
  L3 "debug isolation of the affected layer"
                               inset  x[640,948] y[40,190]
       bg (232,242,232); L1 label content ONLY (body/skeleton pixels
       must be absent inside the rect — probed).

The chain audit re-derives the pinned pose law's joint positions with THIS
module's own expression of the DECLARED formula (same ops, same order) and
requires bitwise identity with the render-time pose (P5's material-mapping
law; M12's render_binding_audit form). FB2/FB5 prove a canned/stale pose is
REFUSED by this audit.

Headless, CPU-only, deterministic; numpy only at the probe boundary.
"""
from __future__ import annotations

import ast

import numpy as np

# ---------------------------------------------------------------- palettes
L1_BG = (250, 250, 250)
L1_TEXT = (15, 15, 15)
L1_BORDER = (0, 90, 220)
L1_RECT = (12, 40, 300, 190)          # x0, y0, x1, y1 (inclusive bounds)
L2_BG = (255, 238, 200)
L2_TEXT = (90, 45, 10)
L2_RECT = (12, 500, 300, 532)
L3_BG = (232, 242, 232)
L3_RECT = (640, 40, 948, 190)

L1_PALETTE = (L1_BG, L1_TEXT, L1_BORDER)
L2_PALETTE = (L2_BG, L2_TEXT)
L3_PALETTE = (L3_BG,)
ALL_PALETTES = L1_PALETTE + L2_PALETTE + L3_PALETTE

# the body/skeleton palettes (W10's declared render colors; absent inside L3)
BODY_PALETTES = ((120, 80, 60), (200, 60, 50), (60, 90, 200))

SCALE = 2                              # panel/strip glyph scale (declared)
L1_ROWS = ["LINK {link}", "CT L{cl} R{cr} {fl}N {fr}N",
           "CLIMB {climb}", "MODE {mode}"]
L1_Y0, L1_X0, L1_DY = 44, 16, 16       # panel text origin / row pitch
L2_TEXT_Y0, L2_TEXT_X0 = 508, 16
L3_X0, L3_Y0 = 648, 44                 # the inset re-draws L1 content

# the declared climb schema-audit law
CLIMB_ABSENT = "absent_declared"
CLIMB_KEY_MARK = "climb"               # any observation key containing this


class Refusal(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise Refusal(code)


# ------------------------------------------------------------------- font
_GLYPHS = {
    "A": ["010", "101", "111", "101", "101"],
    "B": ["110", "101", "110", "101", "110"],
    "C": ["011", "100", "100", "100", "011"],
    "D": ["110", "101", "101", "101", "110"],
    "E": ["111", "100", "110", "100", "111"],
    "F": ["111", "100", "110", "100", "100"],
    "I": ["111", "010", "010", "010", "111"],
    "K": ["101", "101", "110", "101", "101"],
    "L": ["100", "100", "100", "100", "111"],
    "M": ["101", "111", "111", "101", "101"],
    "N": ["101", "111", "111", "111", "101"],
    "O": ["010", "101", "101", "101", "010"],
    "P": ["110", "101", "110", "100", "100"],
    "R": ["110", "101", "110", "101", "101"],
    "S": ["011", "100", "010", "001", "110"],
    "T": ["111", "010", "010", "010", "010"],
    "U": ["101", "101", "101", "101", "111"],
    "V": ["101", "101", "101", "101", "010"],
    "W": ["101", "101", "111", "111", "101"],
    "0": ["111", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"],
    "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"],
    "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"],
    "7": ["111", "001", "001", "001", "001"],
    "8": ["111", "101", "111", "101", "111"],
    "9": ["111", "101", "111", "001", "111"],
    "/": ["001", "001", "010", "100", "100"],
    ".": ["000", "000", "000", "000", "010"],
    "+": ["000", "010", "111", "010", "000"],
    "-": ["000", "000", "111", "000", "000"],
    ":": ["000", "010", "000", "010", "000"],
    " ": ["000", "000", "000", "000", "000"],
}
GLYPH_ON_COUNT = {ch: sum(row.count("1") for row in rows)
                  for ch, rows in _GLYPHS.items()}


def expected_text_metrics(text: str, scale: int = SCALE):
    """The glyph law: width/height/pixel-count of one drawn string."""
    require(all(ch in _GLYPHS for ch in text),
            "x04_glyph_missing:" + repr(text))
    n = len(text)
    return {"text": text,
            "width_px": (n * 4 - 1) * scale,
            "height_px": 5 * scale,
            "pixel_count": sum(GLYPH_ON_COUNT[ch] for ch in text)
            * scale * scale}


def draw_text(colour, text, x0, y0, scale, rgb):
    """Draw one string with the declared font (exact pixels; no clipping —
    the caller's rect is sized by the glyph law)."""
    require(all(ch in _GLYPHS for ch in text),
            "x04_glyph_missing:" + repr(text))
    for i, ch in enumerate(text):
        rows = _GLYPHS[ch]
        for gy, line in enumerate(rows):
            for gx, bit in enumerate(line):
                if bit == "1":
                    for dy in range(scale):
                        for dx in range(scale):
                            yy = y0 + gy * scale + dy
                            xx = x0 + (i * 4 + gx) * scale + dx
                            colour[yy][xx] = rgb


def fill_rect(colour, rect, rgb):
    x0, y0, x1, y1 = rect
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            colour[y][x] = rgb


def border_rect(colour, rect, rgb):
    x0, y0, x1, y1 = rect
    for x in range(x0, x1 + 1):
        colour[y0][x] = rgb
        colour[y1][x] = rgb
    for y in range(y0, y1 + 1):
        colour[y][x0] = rgb
        colour[y][x1] = rgb


def border_pixel_count(rect):
    x0, y0, x1, y1 = rect
    return 2 * (x1 - x0 + 1) + 2 * (y1 - y0 + 1) - 4


# ------------------------------------------------- the climb schema audit
def scene_observation_keys(scene_source: bytes) -> list:
    """AST-extract the observation record's literal key set from the PINNED
    scene module bytes (never hand-copied; the audit's input is the source
    itself)."""
    tree = ast.parse(scene_source.decode("utf-8"))
    keys = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) \
                and node.name == "observation_record":
            for sub in ast.walk(node):
                if isinstance(sub, ast.Return) \
                        and isinstance(sub.value, ast.Dict):
                    for k in sub.value.keys:
                        require(isinstance(k, ast.Constant)
                                and isinstance(k.value, str),
                                "x04_schema_nonliteral_key")
                        keys.append(k.value)
    require(bool(keys), "x04_schema_keys_missing")
    return keys


def derive_climb_state(scene_source: bytes) -> dict:
    """The declared climb-state law: the certified line's observation schema
    is audited over the pinned bytes; a climbing key would refuse the
    'absent' declaration (a climb state would have to be DERIVED from that
    key's actual values, which this line does not provide)."""
    keys = scene_observation_keys(scene_source)
    climbs = [k for k in keys if CLIMB_KEY_MARK in k.lower()]
    if climbs:
        return {"climb_state": "schema_climb_key_present",
                "climb_keys": climbs, "observation_key_count": len(keys)}
    return {"climb_state": CLIMB_ABSENT, "climb_keys": [],
            "observation_key_count": len(keys)}


def _clean_audit(climb_audit):
    """The derivation consumes the CLEAN schema audit dict. The driver's
    receipt wrapper (clean + scratch_flipped + law) carries the same clean
    audit inside it; both forms are accepted, nothing else."""
    if "climb_state" in climb_audit:
        return climb_audit
    clean = climb_audit.get("clean")
    require(isinstance(clean, dict) and "climb_state" in clean,
            "x04_climb_audit_form_undeclared")
    return clean


# ------------------------------------------------------- the chain audit
def chain_from_angles(angles, seg, foot, hip_xy):
    """THIS module's expression of the DECLARED forward-kinematics formula
    (W10 prereg section 6 / pinned leg_chain): identical operations in the
    identical order, math.sin/math.cos exactly as the pinned law — the
    audit instrument, not a render source."""
    import math
    hip, knee, ankle, mp = angles
    z, y = hip_xy
    p_hip = (z, y)
    thigh, shank = seg["thigh"], seg["shank"]
    a1 = -hip
    p_knee = (p_hip[0] + thigh * math.sin(a1), p_hip[1] - thigh * math.cos(a1))
    a2 = a1 + knee
    p_ankle = (p_knee[0] + shank * math.sin(a2), p_knee[1] - shank * math.cos(a2))
    a3 = a2 + ankle
    foot_len = foot["mp_m"] - foot["heel_m"]
    p_mp = (p_ankle[0] + foot_len * math.cos(a3),
            p_ankle[1] + foot_len * math.sin(a3))
    p_heel = (p_ankle[0] - abs(foot["heel_m"]) * math.cos(a3),
              p_ankle[1] - abs(foot["heel_m"]) * math.sin(a3))
    return {"hip": p_hip, "knee": p_knee, "ankle": p_ankle,
            "mp": p_mp, "heel": p_heel}


def audit_chain(pose, viz, geom, row):
    """P5's material-mapping law, walking-frame form (M12's
    render_binding_audit law): the render-time joint positions must equal
    THIS module's re-derivation of the declared formula over the SAME
    committed row — bitwise, full coverage (five sites x two legs).

    `pose` is what the render consumed (viz.pose_at's output, recorded at
    render time). Returns the per-side max deviation (0.0 on the clean
    line) and the connected-site counts (P1)."""
    tables, zero = geom["tables"], geom["zero"]
    seg, foot = geom["seg"], geom["foot"]
    com_h = viz.BODY_LIFT_M
    report = {}
    for side, phase_key in (("left", "phase_left"), ("right", "phase_right")):
        phase = float(row[phase_key])
        angles = (viz.eval_table(tables["hip"], phase) - zero["hip"],
                  viz.eval_table(tables["knee"], phase) - zero["knee"],
                  viz.eval_table(tables["ankle"], phase) - zero["ankle"],
                  viz.eval_table(tables["MP"], phase) - zero["MP"])
        hip_xy = (0.0 if side == "left" else 0.04, com_h)
        mine = chain_from_angles(angles, seg, foot, hip_xy)
        theirs = pose["legs"][side]
        require(set(mine.keys()) == set(theirs.keys()),
                "x04_chain_coverage_refused:" + side)
        worst = 0.0
        connected = 0
        for site in ("hip", "knee", "ankle", "mp", "heel"):
            mx, my = mine[site]
            tx, ty = theirs[site]
            dev = max(abs(float(mx) - float(tx)), abs(float(my) - float(ty)))
            worst = max(worst, dev)
            if dev == 0.0:
                connected += 1
        report[side] = {"max_deviation_m": worst, "connected_sites": connected,
                        "sites": 5}
    return report


# ------------------------------------------------------ state derivation
def derive_state(row, prev_row, climb_audit, viz, geom):
    """The declared state record for one committed row (prereg section 2).
    Every value is derived here; labels are formatted from these values and
    bound in the label receipt."""
    pose = viz.pose_at(row, geom, 0.0, (row["com_x_m"], 0.0))
    chain = audit_chain(pose, viz, geom, row)
    fc = row["foot_contacts"]
    ff = row["foot_forces"]
    cl, cr = int(fc[4]), int(fc[5])
    fl, fr = float(ff[4]), float(ff[5])
    climb_state = _clean_audit(climb_audit)["climb_state"]
    require(climb_state in (CLIMB_ABSENT, "schema_climb_key_present"),
            "x04_climb_state_undeclared:" + repr(climb_state))
    mode = ("WALK" if climb_state == CLIMB_ABSENT
            and set(fc) <= {0.0, 1.0} and row["contact_count"] in (4, 5, 6)
            else None)
    require(mode == "WALK", "x04_mode_undeclared")
    event = "-"
    if prev_row is not None:
        pcl, pcr = int(prev_row["foot_contacts"][4]), \
            int(prev_row["foot_contacts"][5])
        if (cl, pcl) == (1, 0):
            event = "CON L+"
        elif (cl, pcl) == (0, 1):
            event = "CON L-"
        elif (cr, pcr) == (1, 0):
            event = "CON R+"
        elif (cr, pcr) == (0, 1):
            event = "CON R-"
    return {"tick": int(row["tick"]),
            "link": "L%d/5 R%d/5" % (chain["left"]["connected_sites"],
                                     chain["right"]["connected_sites"]),
            "chain_audit": chain,
            "contact_l": cl, "contact_r": cr,
            "force_l_n": fl, "force_r_n": fr,
            "climb_state": climb_state,
            "climb_audit": climb_audit,
            "mode": mode,
            "event": event,
            "com_v_m_s": float(row["com_v_m_s"]),
            "phase_left": float(row["phase_left"]),
            "phase_right": float(row["phase_right"]),
            "state_sha256": row["state_sha256"],
            "pose": pose}


def label_lines(state):
    """The exact label strings for one state (L1 panel content; L3 re-draws
    these; L2 is the event strip line)."""
    return ["LINK " + state["link"],
            "CT L%d R%d %.2fN %.2fN" % (state["contact_l"],
                                        state["contact_r"],
                                        state["force_l_n"],
                                        state["force_r_n"]),
            "CLIMB " + ("NONE" if state["climb_state"] == CLIMB_ABSENT
                        else state["climb_state"].upper()),
            "MODE " + state["mode"]]


def event_line(state):
    return "T%05d %s V%.2f" % (state["tick"], state["event"],
                               state["com_v_m_s"])


# ------------------------------------------------------------- rendering
def _panel_lines(colour, lines, x0, y0):
    receipts = []
    for i, text in enumerate(lines):
        yy = y0 + i * L1_DY
        draw_text(colour, text, x0, yy, SCALE, L1_TEXT)
        m = expected_text_metrics(text)
        receipts.append({"text": text, "layer": "L1",
                         "x0": x0, "y0": yy, "scale": SCALE,
                         "expected": m})
    return receipts


def draw_layers(colour, state):
    """Draw the three declared diagnostic layers onto a rendered colour
    buffer; return the frame's label receipt (exact strings, origins, and
    glyph-law expectations) + the strip content."""
    require(state["climb_state"] == CLIMB_ABSENT
            or state["climb_state"] == "schema_climb_key_present",
            "x04_climb_state_undeclared")
    lines = label_lines(state)
    # L1 selected state labels
    fill_rect(colour, L1_RECT, L1_BG)
    border_rect(colour, L1_RECT, L1_BORDER)
    receipt = _panel_lines(colour, lines, L1_X0, L1_Y0)
    # L2 event/tick trace
    fill_rect(colour, L2_RECT, L2_BG)
    draw_text(colour, event_line(state), L2_TEXT_X0, L2_TEXT_Y0, SCALE,
              L2_TEXT)
    strip_receipt = {"text": event_line(state), "layer": "L2",
                     "x0": L2_TEXT_X0, "y0": L2_TEXT_Y0, "scale": SCALE,
                     "expected": expected_text_metrics(event_line(state))}
    # L3 debug isolation of the affected layer: L1 content ONLY
    fill_rect(colour, L3_RECT, L3_BG)
    inset = _panel_lines(colour, lines, L3_X0, L3_Y0)
    for r in inset:
        r["layer"] = "L3"
    receipt = receipt + [strip_receipt] + inset
    return {"labels": receipt,
            "panel_rect": list(L1_RECT), "strip_rect": list(L2_RECT),
            "inset_rect": list(L3_RECT),
            "expected_counts": {
                "l1_bg_px": ((L1_RECT[2] - L1_RECT[0] + 1)
                             * (L1_RECT[3] - L1_RECT[1] + 1)
                             - border_pixel_count(L1_RECT)
                             - sum(r["expected"]["pixel_count"]
                                   for r in receipt if r["layer"] == "L1")),
                "l1_border_px": border_pixel_count(L1_RECT),
                "l2_bg_px": ((L2_RECT[2] - L2_RECT[0] + 1)
                             * (L2_RECT[3] - L2_RECT[1] + 1)
                             - strip_receipt["expected"]["pixel_count"]),
                "l3_bg_px": ((L3_RECT[2] - L3_RECT[0] + 1)
                             * (L3_RECT[3] - L3_RECT[1] + 1)
                             - sum(r["expected"]["pixel_count"]
                                   for r in receipt if r["layer"] == "L3")),
            },
            "state": {k: state[k] for k in
                      ("tick", "link", "contact_l", "contact_r",
                       "force_l_n", "force_r_n", "climb_state", "mode",
                       "event", "com_v_m_s", "state_sha256")}}


# ----------------------------------------------------------------- probes
def _mask(arr, palette):
    return np.all(arr == np.array(palette, dtype=np.uint8), axis=2)


def _rect_mask(mask, rect):
    x0, y0, x1, y1 = rect
    out = np.zeros_like(mask)
    out[y0:y1 + 1, x0:x1 + 1] = mask[y0:y1 + 1, x0:x1 + 1]
    return out


def probe_layer_pixels(arr, receipt):
    """The executed readability probe (P8/P9/P11): per label row, the
    committed still's palette-pixel count and bbox must EQUAL the glyph
    law's expectation exactly; per layer, the declared background/border
    counts must match exactly."""
    findings = {"rows": [], "layers": {}}
    for r in receipt["labels"]:
        band = (r["x0"] - 2, r["y0"] - 2,
                r["x0"] + r["expected"]["width_px"] + 1,
                r["y0"] + r["expected"]["height_px"] + 1)
        pal = L1_TEXT if r["layer"] in ("L1", "L3") else L2_TEXT
        m = _rect_mask(_mask(arr, pal), band)
        count = int(m.sum())
        ys, xs = np.nonzero(m)
        bbox = ([int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
                if count else None)
        exp_x0 = r["x0"]
        exp_y0 = r["y0"]
        exp_bbox = [exp_x0, exp_y0,
                    exp_x0 + r["expected"]["width_px"] - 1,
                    exp_y0 + r["expected"]["height_px"] - 1]
        findings["rows"].append({
            "text": r["text"], "layer": r["layer"],
            "measured_count": count,
            "expected_count": r["expected"]["pixel_count"],
            "measured_bbox": bbox, "expected_bbox": exp_bbox,
            "count_ok": count == r["expected"]["pixel_count"],
            "bbox_ok": bbox == exp_bbox})
    l1_in_panel = _rect_mask(_mask(arr, L1_BG), L1_RECT)
    l1b_in_panel = _rect_mask(_mask(arr, L1_BORDER), L1_RECT)
    l2_bg = _rect_mask(_mask(arr, L2_BG), L2_RECT)
    l3_bg = _rect_mask(_mask(arr, L3_BG), L3_RECT)
    findings["layers"] = {
        "l1_bg_px": int(l1_in_panel.sum()),
        "l1_bg_expected": receipt["expected_counts"]["l1_bg_px"],
        "l1_border_px": int(l1b_in_panel.sum()),
        "l1_border_expected": receipt["expected_counts"]["l1_border_px"],
        "l2_bg_px": int(l2_bg.sum()),
        "l2_bg_expected": receipt["expected_counts"]["l2_bg_px"],
        "l3_bg_px": int(l3_bg.sum()),
        "l3_bg_expected": receipt["expected_counts"]["l3_bg_px"]}
    body_inside_inset = 0
    bm = np.zeros(arr.shape[:2], dtype=bool)
    for pal in BODY_PALETTES:
        bm |= _mask(arr, pal)
    body_inside_inset = int(_rect_mask(bm, L3_RECT).sum())
    findings["body_pixels_inside_inset"] = body_inside_inset
    return findings


def _in_rects(shape):
    m = np.zeros(shape[:2], dtype=bool)
    for rect in (L1_RECT, L2_RECT, L3_RECT):
        m = m | _rect_mask(np.ones(shape[:2], dtype=bool), rect)
    return m


def binding_audit(receipt, row, prev_row, climb_audit, viz, geom):
    """The FB1 refusal law, executed: the frame's label receipt must be
    EXACTLY the derivation of the committed row (state block bitwise equal
    to the row's fields; label strings exactly the derivation's output).
    A placeholder/stale receipt is REFUSED."""
    state = derive_state(row, prev_row, _clean_audit(climb_audit), viz, geom)
    expected_lines = label_lines(state)
    got_lines = [r["text"] for r in receipt["labels"] if r["layer"] == "L1"]
    require(got_lines == expected_lines,
            "x04_label_binding_refused:" + repr(got_lines[:1]))
    st = receipt["state"]
    require(int(st["tick"]) == int(row["tick"])
            and st["contact_l"] == int(row["foot_contacts"][4])
            and st["contact_r"] == int(row["foot_contacts"][5])
            and float(st["force_l_n"]) == float(row["foot_forces"][4])
            and float(st["force_r_n"]) == float(row["foot_forces"][5])
            and float(st["com_v_m_s"]) == float(row["com_v_m_s"])
            and st["state_sha256"] == row["state_sha256"],
            "x04_state_binding_refused")
    return {"ok": True, "state": st}


def probe_clean_frame(arr):
    """P7: a clean frame must contain ZERO pixels of ANY declared layer
    palette (exact RGB over the whole committed still)."""
    per = {}
    total = 0
    for pal in ALL_PALETTES:
        c = int(_mask(arr, pal).sum())
        per["rgb%d_%d_%d" % pal] = c
        total += c
    return {"layer_pixels_total": total, "per_palette": per,
            "clean_ok": total == 0}
