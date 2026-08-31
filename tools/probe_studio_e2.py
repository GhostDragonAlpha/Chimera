"""probe_studio_e2.py — E2 DEEP LINKS (docs/THE_ENGINE_STUDIO.md §E2), executed.

RULE-0 MEMBRANE (stated before the run):
  STATEMENT : a dock row is a link when its TARGET is derived from the doc by
              tools/studio_board.py and its LANDING is resolved through the live
              wrap map in prepare() — so the glass click on the envelope's
              [docs ->] row and POST /link land identically BY CONSTRUCTION,
              not by two code paths being kept in sync.
  PREDICTION: every stage's link lands the DOCS dock at exactly its own doc
              line; a synthetic click on the FALSIFIER row's hotspot produces
              the same (doc, top_src) as POST /link for the same stage; the
              wrap map is monotonic and total.
  FALSIFIERS (named before the run):
    A: any board-JSON row_line/spec_line whose doc line does NOT contain that
       stage's glance-table row / ### envelope heading -> the link target is a
       lie (offline; no engine needed).
    B: POST /link {"stage":i} for ANY i fails to land — GET /studio_doc never
       shows doc 0 with top_src == the stage's derived line within 6 s.
    C: the synthetic click on the FALSIFIER row's hotspot lands a DIFFERENT
       (doc, top_src) than POST /link for the same stage -> two resolution
       laws exist; the "one law" claim is false.
    D: the wrap map breaks — either the live top_src sweep over scroll is not
       non-decreasing, or the byte-exact re-derivation of docs_rewrap at the
       dock's own width disagrees with the engine's display count, or some
       source line maps to zero display lines.

Usage:  python tools/probe_studio_e2.py        (engine left running on :8090)
"""
from __future__ import annotations

import ctypes
import json
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path("E:/PythonChimera")
EXE = ROOT / "ChimeraEngine" / "engine" / "build" / "Release" / "chimera_engine.exe"
CWD = EXE.parent
BOARD_JSON = CWD / "studio_board.json"
DOC = ROOT / "docs" / "THE_BODY_PIPELINE.md"
OUT = ROOT / ".tmp" / "e2_probe"
URL = "http://localhost:8090"
DETACHED = 0x00000008 | 0x00000200   # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP

results: dict = {}


def req(method, path, payload=None, timeout=15):
    data = json.dumps(payload).encode() if payload is not None else None
    r = urllib.request.Request(URL + path, data=data, method=method,
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read())


def up() -> bool:
    try:
        req("GET", "/debug", timeout=2)
        return True
    except Exception:
        return False


def poll_until(fn, what, timeout=6.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if fn():
            return True
        time.sleep(0.15)
    print(f"  !! never landed: {what}")
    return False


def scroll_to(n, what) -> bool:
    """Land the docs scroll at exactly n and PROVE it (a pending deep link can
    still be in flight from an earlier leg — a landing poll that already sees
    its target would pass before the frame resolves it)."""
    req("POST", "/studio_doc", {"scroll": float(n)})
    return poll_until(lambda: float(req("GET", "/studio_doc")["scroll"]) == float(n), what)


def quiescent(timeout=6.0) -> bool:
    """Two identical reads a beat apart = no in-flight state change."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        a = req("GET", "/studio_doc")
        time.sleep(0.3)
        b = req("GET", "/studio_doc")
        if (a["scroll"], a["top_src"]) == (b["scroll"], b["top_src"]):
            return True
    print("  !! docs state never went quiescent")
    return False


def target_of(stage: dict) -> int:
    """The same resolution law as docs_link_line(): the ### envelope's heading
    when the doc has one, else the glance-table row."""
    return stage["spec_line"] if stage["spec_line"] >= 0 else stage["row_line"]


# ── FALSIFIER A (offline): the board JSON's line numbers point at real lines ──

def falsifier_a() -> bool:
    board = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    lines = DOC.read_text(encoding="utf-8").split("\n")
    bad = []
    for s in board["stages"]:
        sid, row, spec = s["id"], s["row_line"], s["spec_line"]
        if not (0 <= row < len(lines)) or f"**{sid}**" not in lines[row]:
            bad.append(f"{sid}: row_line {row} -> {lines[row][:60]!r}")
        if spec >= 0:
            # the tool's own law: a ### B7b envelope attaches to stage B7
            ok = (0 <= spec < len(lines)
                  and re.match(rf"^###\s+{re.escape(sid)}\w*\b", lines[spec]))
            if not ok:
                bad.append(f"{sid}: spec_line {spec} -> {lines[spec][:60]!r}")
    results["A"] = "PASS" if not bad else f"FAIL ({len(bad)})"
    for b in bad[:8]:
        print("  A:", b)
    return not bad


# ── engine lifecycle (a fresh process: default dock widths, clean log) ───────

def launch_engine():
    if up():
        print("engine already on :8090 — killing it for a clean run")
        subprocess.run(["taskkill", "/F", "/IM", "chimera_engine.exe"],
                       capture_output=True)
        t0 = time.time()
        while up() and time.time() - t0 < 15:
            time.sleep(0.3)
    OUT.mkdir(parents=True, exist_ok=True)
    logf = open(OUT / "engine_stdout.log", "wb")
    proc = subprocess.Popen([str(EXE), "8090"], cwd=str(CWD), stdout=logf,
                            stderr=subprocess.STDOUT, creationflags=DETACHED)
    t0 = time.time()
    while not up() and time.time() - t0 < 45:
        time.sleep(0.5)
    if not up():
        print("FATAL: engine HTTP never came up")
        sys.exit(2)
    time.sleep(1.0)   # let a few frames prepare (board poll, docs poll)
    return proc


# ── FALSIFIER B: POST /link lands the DOCS dock at the stage's own line ──────

def falsifier_b(stages: list[dict]) -> bool:
    req("POST", "/studio", {"on": True})
    bad = []
    for i, s in enumerate(stages):
        tgt = target_of(s)
        r = req("POST", "/link", {"stage": i})
        if not (r.get("ok") and r.get("line") == tgt and r.get("doc") == 0):
            bad.append(f"{s['id']}: /link response {r}")
            continue

        def landed(t=tgt):
            d = req("GET", "/studio_doc")
            return (d.get("doc") == 0 and "THE_BODY_PIPELINE" in d.get("path", "")
                    and d.get("top_src") == t)
        if not poll_until(landed, f"{s['id']} -> top_src {tgt}"):
            bad.append(f"{s['id']}: never landed at line {tgt}")
    results["B"] = "PASS" if not bad else f"FAIL ({len(bad)})"
    for b in bad[:8]:
        print("  B:", b)
    return not bad


# ── FALSIFIER C: the glass click and POST /link land identically ─────────────

def falsifier_c(stages: list[dict]) -> bool:
    st = req("GET", "/studio")
    w, lh = float(st["w"]), float(st["lh"])
    n = len(stages)
    bw = (w - 2 * 8.0 - (n - 1) * 6.0) / n          # pad 8, gap 6 (ui.cpp strip law)
    node_h = max(92.0 - 30.0 - lh - 12.0, 14.0)     # strip_.size default 92

    i = next(k for k, s in enumerate(stages) if s["spec_line"] >= 0)
    sid, tgt = stages[i]["id"], target_of(stages[i])

    def node_center(k):
        return (int(8 + k * (bw + 6) + bw / 2), int(30 + node_h / 2))

    # select the stage on the strip -> its envelope (left dock, mode 0)
    req("POST", "/ui_click", {"x": node_center(i)[0], "y": node_center(i)[1]})
    if not poll_until(lambda: req("GET", "/studio").get("selected") == sid
                      and req("GET", "/studio").get("left_mode") == 0,
                      f"envelope for {sid}"):
        results["C"] = "FAIL (envelope never selected)"
        return False
    time.sleep(0.4)   # a frame must draw the envelope so link_hot_ is live

    st = req("GET", "/studio")
    lx, ly, lw, lh2 = (float(v) for v in st.get("link", [0, 0, 0, 0]))
    if lw <= 1.0:
        results["C"] = "FAIL (no link rect served — the FALSIFIER row is not a hotspot)"
        return False

    landed = lambda: (lambda d: d.get("doc") == 0 and d.get("top_src") == tgt)(req("GET", "/studio_doc"))

    # glass path: start from a KNOWN-OTHER scroll so the landing is unambiguous,
    # then click the FALSIFIER row's hotspot center
    if not (scroll_to(0, "pre-glass scroll 0") and quiescent()):
        results["C"] = "FAIL (could not set up a clean start)"
        return False
    req("POST", "/ui_click", {"x": int(lx + lw / 2), "y": int(ly + lh2 / 2)})
    if not poll_until(landed, f"click landing {sid} -> {tgt}"):
        results["C"] = "FAIL (glass click never landed)"
        return False
    glass = req("GET", "/studio_doc")
    L1 = (glass.get("doc"), glass.get("top_src"))

    # HTTP path: the twin for the same stage, from the same clean start
    if not (scroll_to(0, "pre-http scroll 0") and quiescent()):
        results["C"] = "FAIL (could not set up a clean start)"
        return False
    req("POST", "/link", {"stage": i})
    if not poll_until(landed, f"/link landing {sid} -> {tgt}"):
        results["C"] = "FAIL (/link never landed)"
        return False
    httpd = req("GET", "/studio_doc")
    L2 = (httpd.get("doc"), httpd.get("top_src"))

    ok = L1 == L2 == (0, tgt)
    results["C"] = "PASS" if ok else f"FAIL (glass {L1} vs http {L2}, expected {(0, tgt)})"
    print(f"  C: glass={L1} http={L2} expected={(0, tgt)}")
    return ok


# ── FALSIFIER D: the wrap map is monotonic and total ─────────────────────────

def split_like_cpp(raw: bytes) -> list[bytes]:
    """The exact docs_poll() loop — note it appends one trailing empty line
    even when the file does NOT end with a newline (start <= size)."""
    lines, start, size = [], 0, len(raw)
    while start <= size:
        nl = raw.find(b"\n", start)
        if nl == -1:
            lines.append(raw[start:])
            break
        lines.append(raw[start:nl])
        start = nl + 1
    return [l[:-1] if l.endswith(b"\r") else l for l in lines]


def rewrap_bytes(lines: list[bytes], maxc: int):
    """Byte-exact emulation of StudioUI::docs_rewrap (std::string = bytes)."""
    if maxc < 8:
        maxc = 8
    display_src = []
    for src, line in enumerate(lines):   # C++'s own counter (not the display count)
        para = line                      # \r already stripped by split_like_cpp
        if not para:
            display_src.append(src)
            continue
        while para:
            if len(para) <= maxc:
                display_src.append(src)
                break
            cut = para.rfind(b" ", 0, maxc + 1)     # C++ rfind(' ', maxc): index <= maxc
            if cut == -1 or cut == 0:
                cut = maxc
            display_src.append(src)
            skip = 1 if cut < len(para) and para[cut] == 0x20 else 0
            para = para[cut + skip:]                 # bytes slicing (substr's twin)
    return display_src


def falsifier_d() -> bool:
    bad = []
    if not quiescent():   # a pending deep link from an earlier leg would jump
        return False      # the scroll mid-sweep and fake an inversion

    # D-live: sweep the readable scroll range; top_src must be non-decreasing.
    d0 = req("GET", "/studio_doc")
    n_display, s_max = int(d0["n_display"]), int(float(d0["scroll_max"]))
    sweep = []
    for N in range(0, s_max + 1):
        req("POST", "/studio_doc", {"scroll": float(N)})
        sweep.append(req("GET", "/studio_doc")["top_src"])
    mono_live = all(a <= b for a, b in zip(sweep, sweep[1:]))
    if not mono_live:
        bad.append(f"live top_src sweep not non-decreasing (n_display={n_display})")

    # D-derive: re-wrap the doc's exact bytes at the dock's own width and prove
    # the engine ran the same law (same display count, same map on the prefix).
    st = req("GET", "/studio")
    advance = float(st["advance"])
    lines = split_like_cpp(DOC.read_bytes())
    n_lines = len(lines)
    hit = None
    for cand in (int(266.0 / advance),) + tuple(int(266.0 / advance) + d for d in (-2, -1, 1, 2)):
        m = rewrap_bytes(lines, cand)
        if len(m) == n_display:
            hit = (cand, m)
            break
    if hit is None:
        bad.append(f"no maxc near {int(266.0 / advance)} reproduces the engine's "
                   f"{n_display} display lines — the wrap law drifted")
    else:
        cand, m = hit
        mono_map = all(a <= b for a, b in zip(m, m[1:]))
        missing_set = set(range(n_lines)) - set(m)
        if not mono_map:
            bad.append(f"derived map (maxc={cand}) not non-decreasing")
        if missing_set:
            bad.append(f"{len(missing_set)} source lines map to zero display "
                       f"lines, e.g. {sorted(missing_set)[:8]}")
        prefix_ok = all(sweep[k] == m[k] for k in range(len(sweep))) if mono_live else False
        if not prefix_ok:
            bad.append("live sweep disagrees with the derived map on the readable prefix")
        print(f"  D: maxc={cand} n_display={n_display} n_lines={n_lines} "
              f"sweep={len(sweep)} pts, live==derived={prefix_ok}")

    results["D"] = "PASS" if not bad else f"FAIL ({len(bad)})"
    for b in bad:
        print("  D:", b)
    return not bad


def vk_errors() -> list[str]:
    log = (OUT / "engine_stdout.log").read_text(errors="replace")
    pat = re.compile(r"(?i)(validation layer|vk\w+ failed|VK_ERROR|device lost)")
    return [l.strip() for l in log.splitlines() if pat.search(l)]


def main() -> int:
    board = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    stages = board["stages"]

    print("== A: board JSON line numbers vs the doc (offline) ==")
    a = falsifier_a()

    print("== launching fresh engine on :8090 ==")
    launch_engine()

    print(f"== B: POST /link lands every one of the {len(stages)} stages ==")
    b = falsifier_b(stages)

    print("== C: glass click vs POST /link — one resolution law ==")
    c = falsifier_c(stages)

    print("== D: wrap-map integrity (monotonic + total) ==")
    d = falsifier_d()

    errs = vk_errors()
    results["VK_ERRORS"] = "PASS" if not errs else f"FAIL ({len(errs)})"
    for e in errs[:8]:
        print("  VK:", e)

    (OUT / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    allpass = a and b and c and d and not errs
    print("\n" + json.dumps(results, indent=2))
    print(f"\nVERDICT: {'ALL PASS' if allpass else 'FAIL'}  (engine left running on :8090)")
    return 0 if allpass else 1


if __name__ == "__main__":
    sys.exit(main())
