"""mcp_studio.py — the Chimera STUDIO's MCP twin: the running engine (the Vulkan
window + HTTP API on :8090) as a bounded tool surface for any MCP-speaking AI,
plus the one-call BRIEFING — the human-to-AI context transfer.

THE MEMBRANE (Rule 0, stated 2026-08-30 BEFORE the build):
  STATEMENT : an MCP twin over the studio HTTP API gives any AI full,
              sanctioned control of the RUNNING engine with ZERO new engine
              surface — every tool routes through the existing endpoints (the
              F1 console law at process scale: one path, no side channels) —
              and one call, `briefing`, transfers complete working context
              (where the project stands, what the engine shows right now,
              what just happened) to an AI that has never seen this session.
  PREDICTION: every tool's payload equals the same-moment HTTP read (modulo
              live-clock fields); the briefing contains the standing rule
              VERBATIM, all 11 stage rows, and the log tail; a fresh AI given
              only the briefing can answer "what stage is next, and why"
              without opening a single repo file.
  FALSIFIERS (named before the run):
    A: any tool disagreeing with the same-moment curl beyond live-clock
       tolerance (time/theta advance while playing; paused they are exact).
    B: the briefing missing the standing rule or any of the 11 stages.
    C: any tool dumping a stack trace when the engine is DOWN — it must say
       "ENGINE DOWN" plainly (an AI cannot fix what it cannot parse).
    D: a paused screenshot through the tool not md5-matching a direct /frame
       grab (the D1 freeze law makes paused frames bit-identical).

Dual use:
  python ChimeraEngine/mcp_studio.py                 -> stdio MCP server (chimera-studio)
  python ChimeraEngine/mcp_studio.py --briefing      -> print the briefing (human copies it)
  python ChimeraEngine/mcp_studio.py --screenshot [path]
"""
import hashlib
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # E:/PythonChimera
BASE = "http://localhost:8090"
BOARD_JSON = ROOT / "ChimeraEngine/engine/build/Release/studio_board.json"
SHOT_DIR = ROOT / ".tmp/studio_shots"


class EngineDown(Exception):
    pass


def _req(method, path, payload=None, timeout=15, raw=False):
    url = BASE + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
    except (urllib.error.URLError, ConnectionError, OSError) as e:
        raise EngineDown(f"ENGINE DOWN: {BASE} unreachable ({e.__class__.__name__}). "
                         f"Start chimera_engine.exe (port 8090) and retry.")
    if raw:
        return body
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"_raw": body.decode("utf-8", "replace")}


def _guard(fn, *a, **k):
    """Every tool answers plainly when the engine is down (falsifier C)."""
    try:
        return fn(*a, **k)
    except EngineDown as e:
        return str(e)


# ── tool implementations (importable + MCP-wrapped below) ─────────────────────

def t_state() -> dict:
    """One-shot vitals: chrome (fps/frame-time/GPU/stage line), overlay state,
    show clock, joints owner."""
    chrome = _req("GET", "/studio_chrome")
    studio = _req("GET", "/studio")
    show = _req("GET", "/show")
    joints = _req("GET", "/joints")
    gait = _req("GET", "/gait")
    water = _req("GET", "/water_clock")
    volp = _req("GET", "/volp")
    return {"chrome": {k: chrome.get(k) for k in
                       ("bar_on", "fps", "ft_avg", "ft_max", "gpu", "stage")
                       if k in chrome},
            "studio": studio,
            "show": show,
            "joints": {k: joints.get(k) for k in ("owner", "selected", "n_joints")
                       if k in joints},
            "gait": {k: gait.get(k) for k in ("loaded", "on", "steps_total") if k in gait},
            "water_clock": water,
            "volp": {k: volp.get(k) for k in ("mode",) if k in volp}}


def t_screenshot(path: str = "") -> dict:
    """Grab the live render (/frame — the dyad's pixel-clean channel; the
    overlay never touches it) and save it as a PNG. Returns path + md5."""
    png = _req("GET", "/frame", raw=True, timeout=30)
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    if not path:
        path = str(SHOT_DIR / f"shot_{time.strftime('%Y%m%d_%H%M%S')}.png")
    Path(path).write_bytes(png)
    return {"path": path, "bytes": len(png), "md5": hashlib.md5(png).hexdigest()}


def t_transport(playing=None, time_s=None, speed=None, step=None) -> dict:
    """The show clock's transport (D1): play/pause, absolute scrub, speed,
    frame steps of exactly 1/240 s. No args = just read the clock."""
    payload = {}
    if playing is not None:
        payload["playing"] = bool(playing)
    if time_s is not None:
        payload["time"] = float(time_s)
    if speed is not None:
        payload["speed"] = float(speed)
    if step is not None:
        payload["step"] = float(step)
    if payload:
        _req("POST", "/show", payload)
    return _req("GET", "/show")


def t_pose_joint(joint: str, theta=None) -> dict:
    """Pose one joint to theta degrees (an ownership claim — the editor owns
    the pose until play resumes; the pack's derived ROM clamps hard). With
    theta omitted, selects the joint (gizmo + weight-paint)."""
    payload = {"joint": joint}
    if theta is not None:
        payload["theta"] = float(theta)
    return _req("POST", "/joint", payload)


def t_joints() -> dict:
    """The full joints editor document: owner, selected, every joint's ROM +
    live theta + center/axis."""
    return _req("GET", "/joints")


def t_click(x: int, y: int) -> dict:
    """Aim a click at window pixel (x,y) — panels consume, the viewport orbits.
    Row/node geometry is served by /studio and /joints (aim before you click)."""
    return _req("POST", "/ui_click", {"x": int(x), "y": int(y)})


def t_console(line: str) -> dict:
    """The escape hatch that is still ONE PATH: a request line
    'METHOD /path [json]' through the F1 console — the SAME handler the HTTP
    server runs. Anything without a dedicated tool goes through here."""
    _req("POST", "/console", {"line": line})
    time.sleep(0.3)
    log = _req("GET", "/console")
    entries = log.get("scrollback", [])
    return {"entered": line, "last": entries[-1] if entries else None}


def t_log_tail(n: int = 20) -> dict:
    """The F4 recorder's tail: the last n gate-relevant events (uploads, mode
    flips, intents, posted verdicts) — the session's live edge."""
    log = _req("GET", "/log")
    entries = log.get("lines", [])[-n:]
    tail = [f"{e['t']} [{e['kind']}] {e['detail']}" if isinstance(e, dict) else str(e)
            for e in entries]
    return {"file": log.get("file"), "total": log.get("n"), "tail": tail}


def t_reel() -> dict:
    """The D3 reel: the last 12 captures with their grab-time metadata."""
    return _req("GET", "/reel")


def t_stages() -> dict:
    """The pipeline board truth (the repo's own feed — tools/studio_board.py
    writes it from docs/THE_BODY_PIPELINE.md; this reads, never owns)."""
    if not BOARD_JSON.exists():
        raise EngineDown(f"BOARD MISSING: {BOARD_JSON} — run `python tools/studio_board.py`.")
    return json.loads(BOARD_JSON.read_text(encoding="utf-8"))


def t_link(stage: int) -> dict:
    """E2: the deep link — open the DOCS dock on the pipeline doc at the
    membrane section that named `stage`'s falsifier/spec. The SAME jump the
    glass click on the envelope's [docs ->] row makes (one resolution law for
    both). ok=false means the stage has no doc target; check `line`."""
    return _req("POST", "/link", {"stage": int(stage)})


def t_briefing() -> str:
    """THE CONTEXT TRANSFER. One call = everything a fresh AI (or a returning
    one) needs: where the project stands (the board's own words), what the
    engine shows right now, what just happened (the recorder's tail), and how
    to drive it. Paste the whole output into any AI session."""
    board = t_stages()
    st = t_state()
    log = t_log_tail(15)
    show = st["show"]
    L = []
    L.append("# CHIMERA STUDIO BRIEFING")
    L.append(f"generated {time.strftime('%Y-%m-%d %H:%M:%S')} | engine {BASE}")
    ch = st["chrome"]
    L.append(f"vitals: {ch.get('fps', 0):.0f} fps, ft {ch.get('ft_avg', 0):.3f} ms | "
             f"{ch.get('gpu', '?')} | overlay {'on' if st['studio'].get('on') else 'OFF'}")
    L.append("")
    L.append("## THE STANDING RULE (computed, never edited)")
    L.append(board.get("standing", "(board has no standing line)"))
    L.append("")
    L.append("## THE STAGES (the strip's live colors)")
    for s in board.get("stages", []):
        cell = (s.get("cell") or "").replace("\n", " ")
        if len(cell) > 110:
            cell = cell[:107] + "..."
        L.append(f"- {s['id']:4s} {s['name']:16s} [{s['status']:8s}] {cell}")
    L.append("")
    L.append(f"(board updated {board.get('updated', '?')}; full envelopes: "
             f"docs/THE_BODY_PIPELINE.md; feed: {BOARD_JSON.name})")
    L.append("")
    L.append("## THE ENGINE, RIGHT NOW")
    L.append(f"- show clock: {'PLAYING' if show.get('playing') else 'paused'} "
             f"t={show.get('time', 0):.2f}s speed={show.get('speed', 1)}x | "
             f"current joint: {show.get('current', '?')} theta={show.get('theta', 0):.2f}deg")
    L.append(f"- joints: owner={st['joints'].get('owner', '?')} "
             f"selected={st['joints'].get('selected', '?')} | gait on={st['gait'].get('on')} "
             f"| volp mode={st['volp'].get('mode', '?')} | water steps={st['water_clock'].get('steps_total', '?')}")
    sel = st["studio"].get("selected")
    L.append(f"- studio: stage selected={sel or 'none'} left_mode={st['studio'].get('left_mode')}")
    L.append("")
    L.append("## WHAT JUST HAPPENED (the F4 recorder's tail)")
    for ln in log.get("tail", []):
        L.append(f"- {ln}")
    L.append(f"(session file: {log.get('file')}, {log.get('total')} events total)")
    L.append("")
    L.append("## HOW TO DRIVE THIS ENGINE (the chimera-studio MCP tools)")
    L.append("state · screenshot · transport(play/pause/time/speed/step) · "
             "pose_joint(joint,theta) · joints · click(x,y) · "
             "console('METHOD /path [json]') — the one-path escape hatch · "
             "log_tail · reel · stages · link(stage) — E2: jump the docs dock "
             "to a stage's own section · briefing (this)")
    L.append("Rules of the house: the overlay never touches /frame (screenshots "
             "are pixel-clean); the UI proposes, the engine owns; read "
             "docs/THE_ENGINE_STUDIO.md for the shipped-feature ledger.")
    return "\n".join(L)


# ── MCP surface ───────────────────────────────────────────────────────────────
try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("chimera-studio")

    @mcp.tool()
    def state() -> str:
        """Live engine vitals: fps/frame-time/GPU, the stage line, the show clock,
        joints owner, gait/water/volp states. Cheap; call often."""
        return json.dumps(_guard(t_state), indent=2)

    @mcp.tool()
    def screenshot(path: str = "") -> str:
        """Grab the live render as a PNG (the pixel-clean /frame channel — the
        overlay never touches it). Returns the saved path + md5."""
        return json.dumps(_guard(t_screenshot, path))

    @mcp.tool()
    def transport(playing: bool | None = None, time_s: float | None = None,
                  speed: float | None = None, step: float | None = None) -> str:
        """The show clock: play/pause, scrub to time_s, set speed (0.25-4x),
        step N frames of exactly 1/240 s. No args = read the clock."""
        return json.dumps(_guard(t_transport, playing, time_s, speed, step), indent=2)

    @mcp.tool()
    def pose_joint(joint: str, theta: float | None = None) -> str:
        """Pose a joint to theta degrees (ROM-clamped; an ownership claim until
        play resumes). Omit theta to select it (gizmo + weight-paint)."""
        return json.dumps(_guard(t_pose_joint, joint, theta))

    @mcp.tool()
    def joints() -> str:
        """The joints editor document: owner, selected, every joint's ROM,
        live theta, center and axis."""
        return json.dumps(_guard(t_joints))

    @mcp.tool()
    def click(x: int, y: int) -> str:
        """Click window pixel (x,y). Aim from the geometry /studio and /joints
        serve — panels publish their rects, never hide them."""
        return json.dumps(_guard(t_click, x, y))

    @mcp.tool()
    def console(line: str) -> str:
        """The one-path escape hatch: 'METHOD /path [json]' through the SAME
        handler the HTTP server runs (the F1 console). Returns the response."""
        return json.dumps(_guard(t_console, line))

    @mcp.tool()
    def log_tail(n: int = 20) -> str:
        """The F4 recorder's last n events — uploads, mode flips, intents,
        posted verdicts, with outcomes."""
        return json.dumps(_guard(t_log_tail, n), indent=2)

    @mcp.tool()
    def reel() -> str:
        """The D3 reel: the last 12 captures and their grab-time metadata."""
        return json.dumps(_guard(t_reel), indent=2)

    @mcp.tool()
    def stages() -> str:
        """The pipeline board: all 11 stages with status + verbatim cells and
        the standing rule (the repo's own feed, read never owned)."""
        return json.dumps(_guard(t_stages), indent=2)

    @mcp.tool()
    def link(stage: int) -> str:
        """E2 deep link: open the DOCS dock at the membrane section that named
        `stage` (B0-B10). The context-transfer channel — follow the board row
        to its spec. Returns ok + the doc line it landed on."""
        return json.dumps(_guard(t_link, stage))

    @mcp.tool()
    def briefing() -> str:
        """THE CONTEXT TRANSFER: one call = the standing rule, every stage,
        the engine's live state, the recorder's tail, and the driving manual.
        Paste it into any AI session — it is all the context needed to work."""
        return _guard(t_briefing)

except ImportError:
    mcp = None


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--briefing" in args:
        print(_guard(t_briefing))
    elif "--screenshot" in args:
        i = args.index("--screenshot")
        path = args[i + 1] if i + 1 < len(args) else ""
        print(json.dumps(_guard(t_screenshot, path)))
    elif mcp is not None:
        mcp.run()                                    # stdio server
    else:
        print("the `mcp` package is not installed; CLI flags still work "
              "(--briefing, --screenshot)", file=sys.stderr)
        sys.exit(1)
