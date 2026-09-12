"""inventory.py — THE INVENTORY of state planes in the engine contract route table.

feature-invisible-elements-01 deliverable A. Parses the route dispatch chain in
ChimeraEngine/engine/main.cpp READ-ONLY (never edited by this lane), applies the
authored classification, and writes the classified inventory to the evidence
folder. Every branch in the parsed table must carry a classification entry
(zero unclassified = gate T1); every classification entry must match a parsed
branch (no stale rows).

Classes (the three planes-of-existence, frozen in PREREGISTRATION.txt):
  already-visualized       the engine itself turns the plane into pixels
                           (the route returns image/png, or the plane is
                           consumed by the render the operator already sees)
  renderable-but-inactive  a render path exists behind a switch that the
                           contract exposes but that is OFF / un-uploaded by
                           default (flipping it is Law 1 made real)
  data-only                JSON / binary state served or consumed as data;
                           drives or reports motion with no pixel path of its
                           own

Usage:
  python tools/product_viewer/inventory.py --out <evidence-dir>
  python tools/product_viewer/inventory.py --source <main.cpp> --out <dir>

Exit 0 = every branch classified; exit 2 = unclassified/stale rows (T1 FAIL).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_SOURCE = Path(__file__).resolve().parents[2] / "ChimeraEngine" / "engine" / "main.cpp"

VISUALIZED = "already-visualized"
INACTIVE = "renderable-but-inactive"
DATA_ONLY = "data-only"

# ---------------------------------------------------------------------------
# The dispatch chain is a flat else-if ladder; each branch begins with a
# `p == "<path>"` (optionally two paths ORed) and a method constraint.
# ---------------------------------------------------------------------------

BRANCH_RE = re.compile(
    r'p == "(/?)(?P<paths>[a-z_0-9|]+)"\s*&&\s*method == "(?P<methods>GET|POST|\?\?)'
)

# (path, method) -> (class, evidence). The evidence quotes what the contract
# actually RETURNS or which engine atom the handler sets — read from the
# handler bodies at base f41c8379, not guessed from the names.
CLASSIFICATION: dict[tuple[str, str], tuple[str, str]] = {
    # ── the retired N-body sim (compute path disabled; placeholder data) ──
    ("/state", "GET"): (DATA_ONLY,
        'returns {"n":N,"particles":[[x,y,z,vx,vy,vz,cr,cg,cb,size]..]} JSON; '
        "the N-body compute path is disabled (use_compute=false, main.cpp) so this "
        "drives no rendered pixel"),
    ("/control", "POST"): (DATA_ONLY,
        "sets g_physics params (G,rw,rb,rc,kw,kb,gamma_w,dt); returns {\"ok\":true}; "
        "no GET twin, no pixel path (sim retired)"),
    # ── the body: the plane the operator already sees ──
    ("/membrane", "POST"): (VISUALIZED,
        "loads a splat scene via engine.load_membrane(term,pos,count) -> rendered "
        "into /frame and /glass; returns {\"ok\":true}"),
    ("/membrane_bin", "POST"): (VISUALIZED,
        "binary splat upload (14 floats/splat) -> engine.load_membrane -> the "
        "rendered body (the teddy); returns {\"ok\":true}"),
    ("/mesh_bin", "POST"): (VISUALIZED,
        "triangle mesh upload (slots main/overlay; modes fill/wire/wire+fill) -> "
        "rendered mesh; update_only>=100 streams vertex animation"),
    ("/hinge_bin", "POST"): (VISUALIZED,
        "hinge knee march: nvert weights + JL/JR/axis/rom/period -> the mesh POSES "
        "each frame; visible in motion through the body, no own pixel plane"),
    ("/eye_bin", "POST"): (VISUALIZED,
        "u32 per-splat eye classes (0 sclera/1 iris/2 pupil) consumed by the body "
        "render (eyes are drawn from it)"),
    ("/skin_bin", "POST"): (VISUALIZED,
        "rest splat (14 floats) + bone weights upload -> the skinned body IS the "
        "render surface"),
    # ── pixels themselves ──
    ("/frame", "GET"): (VISUALIZED,
        "returns image/png of the current render (pixel-clean viewport by design; "
        "glass comment: the twin of /frame)"),
    ("/stream", "GET"): (VISUALIZED,
        "same branch as /frame: image/png of the current render"),
    ("/glass", "GET"): (VISUALIZED,
        "returns image/png of the COMPOSITED window (viewport + Studio panels/"
        "status bar/HUD) — the operator's own glass"),
    ("/capture", "POST"): (VISUALIZED,
        "offline render: drives scrub->present->capture->PNG per step and WRITES "
        "captures/<name>/f%04d.png (png::encode_rgba)"),
    # ── light: consumed by the UBO every frame (lit flank + contact shadow) ──
    ("/light", "GET"): (VISUALIZED,
        "returns {x,y,z} of the scene light; the lit flank AND contact shadow "
        "consume this vector through the UBO — visible through the render"),
    ("/light", "POST"): (VISUALIZED,
        "set_light(x,y,z) (zero vector refused); visible in the same frame by "
        "construction (engine comment)"),
    # ── the Studio chrome: the overlay the glass already draws ──
    ("/studio", "GET"): (VISUALIZED,
        "returns {on,left_mode,selected,lh,advance,w,h,link[4],..}: the Studio "
        "overlay IS part of /glass (visibility + panel state)"),
    ("/studio", "POST"): (VISUALIZED,
        "ui_.set_visible / set_left_mode / panel collapse+size — controls the "
        "chrome the glass composites"),
    # ── renderable but INACTIVE: a render path behind an OFF switch ──
    ("/membrane_demo_bin", "POST"): (INACTIVE,
        "MD01 membrane-demo upload (magic 0x3130444D) -> a distinct GPU surface "
        "(gamma relaxation) that renders only after this explicit upload"),
    ("/membrane_demo", "POST"): (INACTIVE,
        "demo control ops reset|step|run|pause|gamma|reject -> drives that demo "
        "surface (inactive until uploaded)"),
    ("/membrane_demo", "GET"): (DATA_ONLY,
        'returns membrane_demo_status_json: {"ok","active","iteration","accepted",'
        '"trials","energy","energy_initial","terminal_state","centre",'
        '"centre_force","accepted_state_id","render_state_id","last_control",'
        '"material_snapshot"} — the demo surface\'s status as data'),
    ("/water_vis", "POST"): (INACTIVE,
        "sets water_vis_on_/water_vis_tri_base_ atomics: the engine's OWN water "
        "tint over the water part of the mesh; default OFF, needs tri_base proof"),
    ("/frost", "POST"): (INACTIVE,
        "frost_on_ + light vector: a render pass (frost shading) that is OFF "
        "until enabled and a frost blob is loaded"),
    ("/strain", "POST"): (INACTIVE,
        "strain_set(on): kernel TINTS the membrane by true area strain (blue "
        "compress / red stretch) — an overlay render, off by default"),
    ("/strain", "GET"): (DATA_ONLY,
        'returns {"on","hinge"} — overlay + hinge status as numbers'),
    ("/matter", "POST"): (INACTIVE,
        "matter_set(on,iters,k): after-LBS surface relaxation pass — changes the "
        "body's shape in motion; OFF by default (JNT2 only)"),
    ("/matter", "GET"): (DATA_ONLY,
        'returns {"on","iters","k","y_ground"} — pass status as numbers'),
    ("/matter_state", "GET"): (DATA_ONLY,
        'the matter truth channel: {"ok","stretch_mean_pct","stretch_max_pct",'
        '"rms_err_pct","below_ground"} read back from the Work half — data measured '
        "against rest edge lengths (needs JNT2 + matter on)"),
    ("/compare", "GET"): (INACTIVE,
        "returns committed A/B compare slots {a_slot,b_slot,a_seq,b_seq}: a "
        "render/display MODE (split compare) that is inactive until set"),
    ("/compare", "POST"): (INACTIVE,
        "queue_ui_compare(slot|clear): commits the A/B compare view before "
        "prepare() — view-mode switch"),
    ("/rig", "GET"): (INACTIVE,
        "returns {on,segments}: the FK parent-link overlay drawn over the body "
        "when on; default off"),
    ("/rig", "POST"): (INACTIVE,
        "set_rig_overlay(on): engine draws authored rig segments (an overlay "
        "render) — off by default"),
    # ── water field: motion-driving, no pixel path of its own ──
    ("/water_bin", "POST"): (DATA_ONLY,
        "binary substrate upload (areas/bed/V0/occ/eij/k_e/l_ij/color_start/inj, "
        "u32 counts + f64 Q,G,c_local) -> the CA pipe network; the FIELD is data, "
        "its engine tint needs /water_vis"),
    ("/water_step", "POST"): (DATA_ONLY,
        '{"n_macro":N,"dt_macro":D} -> solver steps on the render thread; returns '
        '{"ok","sum","min"} — motion driver, no pixels'),
    ("/water_state", "GET"): (DATA_ONLY,
        "returns application/octet-stream [u32 ns][u32 nc][i32 cell volumes] — "
        "the field's truth channel (water-room lane readback law)"),
    ("/water_clock", "POST"): (DATA_ONLY,
        "flags only (water_clock_on_/steps/dt/inj atomics; CA runs inside frame()); "
        "returns {ok,steps_total} — the motion driver"),
    ("/water_clock", "GET"): (DATA_ONLY,
        'returns {"on","steps","inj_target","inj_count","steps_total"} — clock status'),
    ("/water_vis_state", "GET"): (DATA_ONLY,
        "DEBUG (W4): octet-stream [4 u32 indirect][water vertex buffer floats] — "
        "readback of the vis buffer, data for gates"),
    # ── gait CPG: 8 oscillators driving locomotion, served as numbers ──
    ("/gait_bin", "POST"): (DATA_ONLY,
        "binary CPG pack (theta0L/R, phi0*8, consts>=37, edges>=16) -> the "
        "oscillator bank; motion only (the body moves)"),
    ("/gait", "POST"): (DATA_ONLY,
        "flags only (gait_on_/steps/omega atomics; CPG steps inside frame()); "
        "returns {ok,steps_total} — the motion driver"),
    ("/gait", "GET"): (DATA_ONLY,
        'returns {"loaded","on","steps","omega","steps_total","thetaL","thetaR"} — '
        "the CPG's live state as numbers"),
    ("/gait_state", "GET"): (DATA_ONLY,
        "octet-stream [u64 steps_total][u64 cap][f64 ring*cap*8] — the 8-oscillator "
        "phase series ring (bit-exactness gate channel, B15 pattern)"),
    # ── stride: the certified walk stream driving the legs ──
    ("/stride_bin", "POST"): (DATA_ONLY,
        "GAT1 binary stride (n_samples x n_joints thetas, dt, loop0) -> "
        "set_stride_stream; drives the LBS pose — motion through the body"),
    ("/stride", "POST"): (DATA_ONLY,
        'stride_control(on,playing,speed,t) — {"ok":true} — the motion driver'),
    ("/stride", "GET"): (DATA_ONLY,
        'returns {"active","playing","n","j","dt","loop0","t"} — stream status'),
    # ── joints/rig editor: pose state as documents ──
    ("/joints_bin", "POST"): (DATA_ONLY,
        "JNT1 joints pack upload (assignments, weights, table) -> rig + ROM data"),
    ("/joints", "GET"): (DATA_ONLY,
        "joints_editor_json(): full editor document (owner, selected, per-joint "
        "ROM/theta/J/axis)"),
    ("/joints", "POST"): (DATA_ONLY,
        '{"on":bool} — joints_on_: the show owns the pose while on (control flag)'),
    ("/joint", "POST"): (DATA_ONLY,
        "editor HTTP twin: pose claim (joint+theta, clamped) / select; returns "
        "{ok,owner,selected,theta_applied}"),
    ("/project", "POST"): (DATA_ONLY,
        "math channel: world (x,y,z) in -> screen (sx,sy) out through the stashed "
        "VP, plus the cam[8] echo — verification numbers"),
    # ── volp-ARAP knee kernel: pose solve state ──
    ("/volp_bin", "POST"): (DATA_ONLY,
        "VOLP v2 kernel blob upload -> loaded on the render thread"),
    ("/volp", "GET"): (DATA_ONLY,
        'returns {"loaded","mode","manual","M","dV","mu","residual","v_cur",'
        '"frames","thetaL","thetaR"} — solve stats'),
    ("/volp", "POST"): (DATA_ONLY,
        "mode volp|blend, manual thetas, M — atomics; a mode change cold-starts "
        "the solve (motion driver)"),
    ("/volp_state", "GET"): (DATA_ONLY,
        "octet-stream [u32 n_records][f32 verts*n*9] — the full posed vertex "
        "buffer readback (in-engine gate's channel; debug)"),
    # ── frost: state + bit-exact readback ──
    ("/frost_bin", "POST"): (DATA_ONLY,
        "raw frost_engine.bin blob upload (decode tables)"),
    ("/frost", "GET"): (DATA_ONLY,
        'returns {"on","loaded","n_tris","frame","light","view_q","light_q",'
        '"kernel_path","dp4a","coopvec"} — pass status'),
    ("/frost_debug", "POST"): (DATA_ONLY,
        "arms a bit-exactness snapshot -> octet-stream [i32 colors][i32 kernel "
        "inputs] — gate data"),
    # ── skin/pose: drive the visible body through data ──
    ("/pose_store", "POST"): (DATA_ONLY,
        "binary pose slot store [u32 slot][u32 B][f32 B*7 quat+trans]"),
    ("/pose_apply", "POST"): (DATA_ONLY,
        "binary [u32 slot] — copies the slot into pose_buf_, posed next frame "
        "(visible THROUGH the body; control is data)"),
    # ── camera/view: view state as data ──
    ("/camera", "POST"): (DATA_ONLY,
        "cam_radius/theta/phi via the membrane request (render-thread discipline); "
        "moves the view — control data"),
    ("/cameras", "GET"): (DATA_ONLY,
        'returns {"bookmarks":[{name,v[8]}..]} — the bookmark store (the glass '
        "chips draw the same names)"),
    ("/cameras", "POST"): (DATA_ONLY,
        "save/recall/fit/delete — view-state store ops (fit derives from the live "
        "mesh)"),
    # ── studio clock + keys: the timeline as data ──
    ("/show", "POST"): (DATA_ONLY,
        "playing/time/speed/step — show_playing_/show_scrub_ atomics; the clock "
        "that drives motion (returns {ok,time})"),
    ("/show", "GET"): (DATA_ONLY,
        'returns {"playing","time","speed","n_joints","period","total","clock",'
        '"current","theta","joints_loaded","hinge_loaded","rom_ext","rom_flex"}'),
    ("/keys", "GET"): (DATA_ONLY,
        'returns {"keys":[{name,t,joint}..]} — timeline key marks'),
    ("/keys", "POST"): (DATA_ONLY,
        "save/recall/delete/clear key marks (recall scrubs + optionally restores "
        "the whole pose)"),
    # ── twins: the glass's own state served as JSON ──
    ("/reel", "GET"): (DATA_ONLY,
        "reel_json(): the grab ledger, newest first — evidence-tray channel"),
    ("/studio_chrome", "GET"): (DATA_ONLY,
        "the chrome twin: bar_on,fps,ft_*,ring,gpu,stage,hud_rows,gait{on,lamL/lamR/"
        "thL/thR,steps,omega},water{on,steps,dt,inj_t,inj_c},show_row — the SAME "
        "strings the glass drew, served as data"),
    ("/studio_chrome", "POST"): (DATA_ONLY,
        '{"on":bool} — set_bar_on: the status bar kill switch (chrome control)'),
    ("/console", "GET"): (DATA_ONLY,
        "console twin: open,input,hist_n,pending,log[50] — what the glass shows, "
        "served"),
    ("/console", "POST"): (DATA_ONLY,
        "line/open — request_console_ui; the same console path as keyboard input"),
    ("/studio_doc", "GET"): (DATA_ONLY,
        "docs browser twin: doc,path,mtime,fnv,n_lines,n_display,scroll,scroll_max,"
        "top_src — the panel's state as data"),
    ("/studio_doc", "POST"): (DATA_ONLY,
        "doc/scroll navigation — request_ui_doc, acknowledged after the render "
        "thread applies"),
    ("/link", "POST"): (DATA_ONLY,
        "stage deep link — request_ui_link resolves stage/line/doc (control)"),
    ("/ui_click", "POST"): (DATA_ONLY,
        "synthetic click (x,y) queued onto the render thread — agents drive panels"),
    ("/scene", "GET"): (DATA_ONLY,
        "outliner twin: rows {id,label,detail,state,toggleable} + aim rects — the "
        "ONE formatting site the dock draws"),
    ("/scene", "POST"): (DATA_ONLY,
        '{"id":..,"on":..} — scene_exec: the engine\'s OWN element toggles routed '
        "through the console's one path (returns the queued line)"),
    ("/inspect", "GET"): (DATA_ONLY,
        "inspector twin: the SAME inspect_kv document the right dock draws"),
    ("/inspect", "POST"): (DATA_ONLY,
        "select row/id / deselect — pure view state (no scene change)"),
    # ── records + session: data about data ──
    ("/log", "GET"): (DATA_ONLY,
        "recorder tail: file,n,lines[{seq,t,kind,detail}] — the live edge of the "
        "record"),
    ("/log", "POST"): (DATA_ONLY,
        'external gate verdict lands VERBATIM (kind "gate" by convention)'),
    ("/capture", "GET"): (DATA_ONLY,
        "capture session twin: state + capture_kv lines (the CAPTURE dock's doc)"),
    ("/debug", "GET"): (DATA_ONLY,
        'returns {"n","active","vp_valid"} — published so "the grid silently isn\'t '
        'there" has a name'),
    ("/session", "GET"): (DATA_ONLY,
        "snapshot status: per-endpoint blob sizes (mesh_bin,hinge_bin,joints_bin,"
        "gait_bin,stride_bin,water_bin) — what a restore would replay"),
    ("/session", "POST"): (DATA_ONLY,
        "restore/clear: replays snapshot blobs through invoke_api — session data "
        "operations"),
}


def parse_branches(source: str) -> list[dict]:
    """Extract the dispatch branches: paths, methods, line span."""
    lines = source.splitlines()
    branches: list[dict] = []
    for i, line in enumerate(lines, start=1):
        if "p ==" not in line or "method" not in line:
            continue
        m = re.search(r'p == "(/?)([a-z_0-9]+)"(?:\s*\|\|\s*p == "(/?)([a-z_0-9]+)")?', line)
        mm = re.search(r'method == "(GET|POST|GET.*POST.*POST|GET \\?\|\|.*POST)"', line)
        methods_m = re.findall(r'method == "(GET|POST)"', line)
        if not m:
            continue
        paths = ["/" + g for g in (m.group(2), m.group(4)) if g]
        methods = methods_m if methods_m else ["GET|POST"]
        # A branch serving both methods declares them in one condition
        # (p == "/keys" && (method == "GET" || method == "POST")); find the
        # full condition by scanning the line.
        if "method == \"GET\" || method == \"POST\"" in line or \
           ("method == \"GET\"" in line and "method == \"POST\"" in line):
            methods = ["GET|POST"]
        elif not methods_m:
            # two-condition form: (p == "/x" && method == "GET") in one line
            cond = re.findall(r'method == "\s*(GET|POST)\s*"', line)
            methods = cond or ["GET|POST"]
        branches.append({"paths": paths, "methods": methods, "line": i,
                         "text": line.strip()})
    return branches


def expand(branches: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for b in branches:
        for p in b["paths"]:
            for meth in b["methods"]:
                for one in meth.split("|"):
                    rows.append({"path": p, "method": one.strip(),
                                 "line": b["line"], "source": b["text"]})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE,
                    help="path to the read-only engine main.cpp")
    ap.add_argument("--out", type=Path, required=True,
                    help="evidence directory for INVENTORY.txt / INVENTORY.json")
    a = ap.parse_args()

    text = a.source.read_text(encoding="utf-8", errors="replace")
    rows = expand(parse_branches(text))

    problems: list[str] = []
    for r in rows:
        key = (r["path"], r["method"])
        if key not in CLASSIFICATION:
            problems.append(f"UNCLASSIFIED branch: {key[0]} {key[1]} "
                            f"(main.cpp line {r['line']})")
    classified_keys = set(CLASSIFICATION)
    parsed_keys = {(r["path"], r["method"]) for r in rows}
    for key in sorted(classified_keys - parsed_keys):
        problems.append(f"STALE classification: {key[0]} {key[1]} "
                        f"(no such branch in {a.source.name})")

    counts = {VISUALIZED: 0, INACTIVE: 0, DATA_ONLY: 0}
    lines_out: list[str] = []
    lines_out.append("FEATURE_INVISIBLE_ELEMENTS — THE INVENTORY (deliverable A)")
    lines_out.append("=" * 72)
    lines_out.append(f"source : {a.source}  (READ-ONLY; base f41c8379 lane)")
    lines_out.append(f"branches parsed: {len(rows)}  (unique paths: "
                     f"{len({r['path'] for r in rows})})")
    lines_out.append("")
    lines_out.append("CLASS rubric (frozen PREREGISTRATION.txt):")
    lines_out.append(f"  {VISUALIZED}: the engine turns the plane into pixels itself")
    lines_out.append(f"  {INACTIVE}: a render path exists behind an OFF/unloaded switch")
    lines_out.append(f"  {DATA_ONLY}: JSON/binary state; drives or reports motion, no pixels")
    lines_out.append("")
    order = {VISUALIZED: 0, INACTIVE: 1, DATA_ONLY: 2}
    for r in sorted(rows, key=lambda r: (order[CLASSIFICATION[(r["path"], r["method"])][0]],
                                         r["path"], r["method"])):
        cls, ev = CLASSIFICATION[(r["path"], r["method"])]
        counts[cls] += 1
        lines_out.append(f"[{cls}] {r['path']} {r['method']}  (main.cpp:{r['line']})")
        lines_out.append(f"    evidence: {ev}")
        lines_out.append("")

    lines_out.append("SUMMARY")
    lines_out.append("-" * 8)
    for cls, n in counts.items():
        lines_out.append(f"  {cls}: {n}")
    lines_out.append(f"  total classified rows: {sum(counts.values())}")
    lines_out.append("")
    if problems:
        lines_out.append("PROBLEMS (gate T1 FAIL):")
        lines_out.extend("  " + p for p in problems)
    else:
        lines_out.append("gate T1: every parsed branch classified; no stale rows. PASS")

    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "INVENTORY.txt").write_text("\n".join(lines_out) + "\n", encoding="utf-8")
    (a.out / "INVENTORY.json").write_text(json.dumps(
        {"source": str(a.source), "rows": [
            {"path": r["path"], "method": r["method"], "line": r["line"],
             "class": CLASSIFICATION[(r["path"], r["method"])][0],
             "evidence": CLASSIFICATION[(r["path"], r["method"])][1]}
            for r in sorted(rows, key=lambda r: (r["path"], r["method"]))],
         "counts": counts, "problems": problems}, indent=1), encoding="utf-8")

    print("\n".join(lines_out[-12:]))
    return 2 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
