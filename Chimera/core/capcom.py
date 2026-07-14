"""
CAPCOM — the operator channel.

Why this exists (2026-07-13, the human): "I need a way to get more things
communicated to you the operator as you're using the system — design a system
that isn't reliant upon Claude Code and integrate it with the current system."

The problem is DIRECTIONAL. Almost everything in the studio is PULL: the
system's state (git, build, editor/PIE, task-board claims, circadian phase,
helm heading) only reaches the operating agent if it remembers to run preflight
/ git status / helm. When it doesn't, state is missed — that is how 199 lines of
DNA-graph churn once sat unpushed. And a Claude Code hook only helps INSIDE
Claude Code — useless the moment a weaker successor model or a different harness
drives the project (which SUCCESSOR_RUNBOOK explicitly plans for).

CAPCOM is the inverse: a PUSH channel that lives in the PROJECT itself. Any
subsystem — or the human — drops a signal (post / tell); any operating agent
reads one situational brief (brief). Named for NASA's CAPCOM, the single voice
that talks to the crew during a mission — fitting an EVA game, and fitting
"communicate more to the operator."

Agent-agnostic by construction: pure Python + the world_store SQLite substrate
(FTS-searchable, the same engine as the DNA graph). No Claude Code dependency;
no always-on process. Claude Code, at most, is a thin consumer that runs
`capcom brief`. Every other agent runs the same command.

Design (from reading core/world_store.py):
  - Signals are APPEND-ONLY nodes in their own db (docs/world/capcom.db), kind
    ``capcom_signal``. Never mutated, so the FTS index stays clean (world_store's
    INSERT-OR-REPLACE changes a row's rowid, which would orphan FTS entries on
    update — we sidestep that entirely by never updating a signal).
  - IDs are time-ordered and FIXED-WIDTH (``sig_<20-digit ns>_<pid>_<seq>``), so
    ``ORDER BY id DESC`` is chronological and ``id > watermark`` is a clean
    "newer than" test — no timestamp column needed.
  - Read-state is a WATERMARK (the newest acknowledged id) in a side table, so
    "unread" = signals with id greater than it. Acking never touches a signal.
  - The human's inbound lane is docs/OPERATOR_INBOX.md: edit the file (no tool),
    and each new line is ingested into a signal, idempotently by line-hash.

CLI
---
    python -m core.capcom brief [--all] [--limit N]    # the operator's read
    python -m core.capcom tell "message" [--level ...]  # human -> operator note
    python -m core.capcom post --channel X --msg "..." [--level ...] [--source ...]
    python -m core.capcom ack [--id SIG]                # mark read (default: all)
    python -m core.capcom log [--limit N]               # raw recent signals
    python -m core.capcom search --query "..."          # FTS over signals
    python -m core.capcom ingest                         # pull OPERATOR_INBOX.md now
    python -m core.capcom prune [--days D] [--keep N]
    python -m core.capcom stats

Integration (called fire-and-forget via post_safe, which never raises):
    from core.capcom import post_safe
    post_safe("build", "UBT ChimeraEditor Succeeded (16s)", level="info", source="build")
"""
import argparse
import hashlib
import itertools
import json
import os
import subprocess
import sys
import time
from pathlib import Path

try:
    from core import world_store
except ImportError:  # allow `python core/capcom.py`
    sys.path.insert(0, str(Path(__file__).parent))
    import world_store  # type: ignore

HERE = Path(__file__).parent
ROOT = HERE.parent                                  # .../Chimera
# The git repo root is E:/PythonChimera (one above Chimera/). git -C also walks
# up to find .git, so either works; prefer the env the project already sets.
GIT_ROOT = os.environ.get("CHIMERA_ROOT") or str(ROOT)
CAPCOM_DB = Path(os.environ.get("CHIMERA_CAPCOM_DB", ROOT / "docs" / "world" / "capcom.db"))
INBOX = Path(os.environ.get("CHIMERA_OPERATOR_INBOX", ROOT / "docs" / "OPERATOR_INBOX.md"))

SIGNAL_KIND = "capcom_signal"
LEVELS = ("info", "note", "warn", "alert")
LEVEL_MARK = {"info": "i", "note": ">", "warn": "!", "alert": "*"}

_counter = itertools.count()

_INBOX_HEADER = """\
# OPERATOR INBOX — notes to whoever is operating Chimera
#
# Type a note on its own line below. The next `python -m core.capcom brief`
# turns each new line into a signal the operating agent reads. One note per
# line. Lines starting with '#' are ignored. No tool required — just edit this
# file (or run `python -m core.capcom tell "..."`).

"""


# --------------------------------------------------------------------------
# storage
# --------------------------------------------------------------------------
def _con():
    con = world_store.connect(CAPCOM_DB)
    try:
        con.execute("PRAGMA busy_timeout=4000")
        con.execute("CREATE TABLE IF NOT EXISTS capcom_meta(k TEXT PRIMARY KEY, v TEXT)")
        con.execute("CREATE TABLE IF NOT EXISTS capcom_inbox_seen(h TEXT PRIMARY KEY)")
        con.commit()
    except Exception:
        pass
    return con


def _meta_get(con, k, default=None):
    r = con.execute("SELECT v FROM capcom_meta WHERE k=?", (k,)).fetchone()
    return r[0] if r else default


def _meta_set(con, k, v):
    con.execute("INSERT OR REPLACE INTO capcom_meta(k,v) VALUES(?,?)", (k, str(v)))
    con.commit()


def _iso(ts):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts or time.time()))


def _ago(secs):
    secs = max(0, int(secs))
    if secs < 60:
        return f"{secs}s"
    if secs < 3600:
        return f"{secs // 60}m"
    if secs < 86400:
        return f"{secs // 3600}h"
    return f"{secs // 86400}d"


def _ascii(s):
    """Fold to ASCII so the brief renders on any console (the Windows cp1252
    terminal mangles em-dashes / middot into replacement glyphs). Display-only —
    stored signal data keeps its original text."""
    for a, b in (("—", "-"), ("–", "-"), ("·", "-"), ("→", "->"),
                 ("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'),
                 ("…", "...")):
        s = s.replace(a, b)
    return s.encode("ascii", "replace").decode("ascii")


# --------------------------------------------------------------------------
# post — any subsystem or the human drops a signal
# --------------------------------------------------------------------------
def _emit(con, channel, msg, level="info", data=None, source="system", commit=True):
    """Write one signal node on an EXISTING connection. Sharing the caller's
    connection (rather than opening a second one) is what keeps ingest_inbox from
    deadlocking against itself: SQLite allows a single writer, so opening a second
    connection to write while the first holds an uncommitted txn self-locks
    ('database is locked'). commit=False folds the write into the caller's
    transaction so a batch (e.g. inbox ingest) is atomic."""
    if level not in LEVELS:
        level = "info"
    now = time.time()
    # fixed-width, time-ordered, collision-proof across processes:
    sig_id = f"sig_{time.time_ns():020d}_{os.getpid():07d}_{next(_counter):04d}"
    rec = {"channel": str(channel), "level": level, "msg": str(msg),
           "data": data, "source": str(source), "ts": now, "ts_iso": _iso(now)}
    label = f"[{level}][{channel}] {msg}"[:220]
    world_store.add_nodes(con, [(sig_id, SIGNAL_KIND, label, None, None, None, rec)],
                          commit=commit)
    return sig_id


def post(channel, msg, level="info", data=None, source="system"):
    """Append a signal to the operator channel. Returns its id."""
    con = _con()
    try:
        return _emit(con, channel, msg, level=level, data=data, source=source)
    finally:
        con.close()


def post_safe(channel, msg, level="info", data=None, source="system"):
    """Fire-and-forget for integration points — never raises, so a CAPCOM
    hiccup can't break the subsystem that is reporting to it."""
    try:
        return post(channel, msg, level=level, data=data, source=source)
    except Exception:
        return None


def tell(msg, level="note", source="human"):
    """The HUMAN drops a note to whoever is operating."""
    return post("human", msg, level=level, source=source)


# --------------------------------------------------------------------------
# read
# --------------------------------------------------------------------------
def _row_to_sig(row):
    rec = json.loads(row[2]) if row[2] else {}
    rec["id"] = row[0]
    return rec


def unread(con, limit=50):
    wm = _meta_get(con, "ack_watermark", "")
    rows = con.execute(
        "SELECT id,label,data FROM node WHERE kind=? AND id>? ORDER BY id DESC LIMIT ?",
        (SIGNAL_KIND, wm, limit)).fetchall()
    return [_row_to_sig(r) for r in rows]


def recent(con, limit=50):
    rows = con.execute(
        "SELECT id,label,data FROM node WHERE kind=? ORDER BY id DESC LIMIT ?",
        (SIGNAL_KIND, limit)).fetchall()
    return [_row_to_sig(r) for r in rows]


def unread_count(con):
    wm = _meta_get(con, "ack_watermark", "")
    return con.execute("SELECT COUNT(*) FROM node WHERE kind=? AND id>?",
                       (SIGNAL_KIND, wm)).fetchone()[0]


def total_count(con):
    return con.execute("SELECT COUNT(*) FROM node WHERE kind=?", (SIGNAL_KIND,)).fetchone()[0]


def ack(con, sig_id=None):
    """Move the read-watermark. Default: mark every current signal read."""
    if sig_id is None:
        r = con.execute("SELECT id FROM node WHERE kind=? ORDER BY id DESC LIMIT 1",
                        (SIGNAL_KIND,)).fetchone()
        sig_id = r[0] if r else _meta_get(con, "ack_watermark", "")
    _meta_set(con, "ack_watermark", sig_id)
    return sig_id


# --------------------------------------------------------------------------
# the human's inbound lane: OPERATOR_INBOX.md (edit a file, no tool needed)
# --------------------------------------------------------------------------
def ensure_inbox():
    if not INBOX.exists():
        INBOX.parent.mkdir(parents=True, exist_ok=True)
        INBOX.write_text(_INBOX_HEADER, encoding="utf-8")


def ingest_inbox(con=None):
    """Turn new lines in OPERATOR_INBOX.md into signals, idempotently by line
    hash (so re-running never double-posts a note the human left in the file).
    Creates the template inbox on first call so the human can discover + edit it."""
    ensure_inbox()
    if not INBOX.exists():
        return 0
    own = con is None
    con = con or _con()
    posted = 0
    try:
        for raw in INBOX.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("<!--"):
                continue
            h = hashlib.sha1(line.encode("utf-8")).hexdigest()
            if con.execute("SELECT 1 FROM capcom_inbox_seen WHERE h=?", (h,)).fetchone():
                continue
            # write signal + seen-mark on the SAME connection, committed together
            # below — atomic, and no second-connection self-lock.
            _emit(con, "inbox", line, level="note", source="operator-inbox", commit=False)
            con.execute("INSERT OR REPLACE INTO capcom_inbox_seen(h) VALUES(?)", (h,))
            posted += 1
        con.commit()
    finally:
        if own:
            con.close()
    return posted


# --------------------------------------------------------------------------
# the live snapshot — cheap, high-value facts, each gathered DEFENSIVELY so a
# subsystem change can never crash the brief (mirrors preflight's own guards).
# --------------------------------------------------------------------------
def _git_line():
    try:
        def g(*a):
            return subprocess.run(["git", "-C", GIT_ROOT, *a],
                                  capture_output=True, text=True, timeout=12)
        branch = g("rev-parse", "--abbrev-ref", "HEAD").stdout.strip() or "?"
        head = g("rev-parse", "--short", "HEAD").stdout.strip() or "?"
        dirty = len([l for l in g("status", "--porcelain").stdout.splitlines() if l.strip()])
        ahead = behind = 0
        ab = g("rev-list", "--left-right", "--count", "@{u}...HEAD")
        if ab.returncode == 0 and ab.stdout.strip():
            parts = ab.stdout.split()
            if len(parts) == 2:
                behind, ahead = int(parts[0]), int(parts[1])
        state = "clean" if dirty == 0 else f"{dirty} dirty"
        sync = []
        if ahead:
            sync.append(f"UP{ahead} UNPUSHED")
        if behind:
            sync.append(f"DOWN{behind} behind")
        tail = ("  " + ", ".join(sync)) if sync else "  in sync"
        return f"{branch} @{head}  {state}{tail}"
    except Exception as e:
        return f"(unavailable: {e})"


def _editor_line():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq UnrealEditor.exe"],
                             capture_output=True, text=True, timeout=10).stdout
        return "RUNNING" if "UnrealEditor.exe" in out else "not running"
    except Exception:
        return "unknown"


def _phase_line():
    from core.circadian import preflight_line as f
    return f().strip()


def _heading_line():
    from core.helm import preflight_line as f
    return f().strip()


def _board_line():
    from core.task_board import board_summary
    s = board_summary()
    if not s.get("total"):
        return "no tasks"
    return (f"{s['total']} task(s), {len(s.get('claims', []))} claimed, "
            f"{len(s.get('frontier', []))} on frontier")


# --------------------------------------------------------------------------
# the brief — one situational read for whoever is operating
# --------------------------------------------------------------------------
def brief(limit=40, show_all=False, do_ingest=True):
    con = _con()
    if do_ingest:
        try:
            ingest_inbox(con)
        except Exception:
            pass

    out = ["=" * 68, f"CAPCOM — operator brief    {_iso(time.time())}", "=" * 68]

    sigs = recent(con, limit) if show_all else unread(con, limit)
    un, tot = unread_count(con), total_count(con)
    out.append(f"\nSIGNALS ({'all' if show_all else 'unread'}): "
               f"{len(sigs)} shown | {un} unread | {tot} total")
    if not sigs:
        out.append("  (nothing" + ("" if show_all else " unread") + ")")
    else:
        now = time.time()
        for s in sigs:
            mark = LEVEL_MARK.get(s.get("level", "info"), " ")
            age = _ago(now - s.get("ts", now))
            src = s.get("source", "")
            out.append(f"  [{mark}] {age:>4}  ({s.get('channel', '?')}) {s.get('msg', '')}"
                       + (f"   <{src}>" if src and src != "system" else ""))

    out.append("\nSITUATION:")
    out.append(f"  git    : {_git_line()}")
    out.append(f"  editor : {_editor_line()}")
    for label, fn in (("phase", _phase_line), ("heading", _heading_line), ("board", _board_line)):
        try:
            v = fn()
            out.append(f"  {label:<7}: {v.replace(chr(10), ' / ') if v else '(none)'}")
        except Exception:
            out.append(f"  {label:<7}: (unavailable)")

    out.append("\n  ack read: python -m core.capcom ack     "
               "leave me a note: python -m core.capcom tell \"...\"")
    con.close()
    return _ascii("\n".join(out))


def signals_block(limit=8, ingest=True):
    """A compact ASCII block of just the UNREAD signals, for embedding in another
    tool's output (e.g. preflight, which already shows git/phase/board so it wants
    the signals, not the full snapshot). Empty string when nothing is unread."""
    con = _con()
    try:
        if ingest:
            try:
                ingest_inbox(con)
            except Exception:
                pass
        sigs = unread(con, limit)
        un = unread_count(con)
    finally:
        con.close()
    if not sigs:
        return ""
    now = time.time()
    lines = [f"[CAPCOM] {un} unread operator signal(s) - newest first:"]
    for s in sigs:
        mark = LEVEL_MARK.get(s.get("level", "info"), " ")
        lines.append(f"    [{mark}] {_ago(now - s.get('ts', now)):>4} "
                     f"({s.get('channel', '?')}) {s.get('msg', '')}")
    lines.append("    ack: python -m core.capcom ack    full brief: python -m core.capcom brief")
    return _ascii("\n".join(lines))


# --------------------------------------------------------------------------
# search / prune
# --------------------------------------------------------------------------
def search_signals(query, limit=25):
    con = _con()
    out = []
    for h in world_store.search(con, query, limit=limit * 3):
        if h.get("kind") != SIGNAL_KIND:
            continue
        n = world_store.get_node(con, h["id"])
        if n:
            rec = n.get("data") or {}
            rec["id"] = n["id"]
            out.append(rec)
        if len(out) >= limit:
            break
    con.close()
    return out


def prune(days=None, keep=None):
    con = _con()
    ids = [r[0] for r in con.execute(
        "SELECT id FROM node WHERE kind=? ORDER BY id DESC", (SIGNAL_KIND,)).fetchall()]
    doomed = set()
    if keep is not None and len(ids) > keep:
        doomed.update(ids[keep:])
    if days is not None:
        cutoff_id = f"sig_{time.time_ns() - int(days * 86400 * 1e9):020d}"
        doomed.update(i for i in ids if i < cutoff_id)
    for i in doomed:
        con.execute("DELETE FROM node WHERE id=?", (i,))
    con.commit()
    con.close()
    return len(doomed)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main(argv=None):
    p = argparse.ArgumentParser(prog="capcom", description="CAPCOM — the operator channel")
    sub = p.add_subparsers(dest="cmd", required=True)

    pb = sub.add_parser("brief", help="the operator's situational read")
    pb.add_argument("--all", action="store_true", help="show acknowledged signals too")
    pb.add_argument("--limit", type=int, default=40)

    pt = sub.add_parser("tell", help="the human leaves a note for the operator")
    pt.add_argument("message")
    pt.add_argument("--level", default="note", choices=LEVELS)

    pp = sub.add_parser("post", help="a subsystem posts a signal")
    pp.add_argument("--channel", required=True)
    pp.add_argument("--msg", required=True)
    pp.add_argument("--level", default="info", choices=LEVELS)
    pp.add_argument("--source", default="system")

    pa = sub.add_parser("ack", help="mark signals read (default: all current)")
    pa.add_argument("--id", default=None)

    pl = sub.add_parser("log", help="raw recent signals (newest first)")
    pl.add_argument("--limit", type=int, default=30)

    psr = sub.add_parser("search", help="full-text search over signals")
    psr.add_argument("--query", required=True)
    psr.add_argument("--limit", type=int, default=25)

    sub.add_parser("ingest", help="pull new lines from OPERATOR_INBOX.md now")

    pr = sub.add_parser("prune", help="drop old signals")
    pr.add_argument("--days", type=float, default=None)
    pr.add_argument("--keep", type=int, default=None)

    sub.add_parser("stats")

    args = p.parse_args(argv)

    if args.cmd == "brief":
        print(brief(limit=args.limit, show_all=args.all))
    elif args.cmd == "tell":
        print(f"noted -> {tell(args.message, level=args.level)}")
    elif args.cmd == "post":
        print(f"posted -> {post(args.channel, args.msg, level=args.level, source=args.source)}")
    elif args.cmd == "ack":
        con = _con()
        wm = ack(con, args.id)
        con.close()
        print(f"acknowledged up to {wm}")
    elif args.cmd == "log":
        con = _con()
        sigs = recent(con, args.limit)
        con.close()
        for s in sigs:
            print(_ascii(f"{_iso(s.get('ts', 0))}  [{s.get('level')}] "
                         f"({s.get('channel')}) {s.get('msg')}  <{s.get('source')}>"))
    elif args.cmd == "search":
        for s in search_signals(args.query, args.limit):
            print(_ascii(f"{_iso(s.get('ts', 0))}  ({s.get('channel')}) {s.get('msg')}"))
    elif args.cmd == "ingest":
        print(f"ingested {ingest_inbox()} new inbox line(s)")
    elif args.cmd == "prune":
        print(f"pruned {prune(days=args.days, keep=args.keep)} signal(s)")
    elif args.cmd == "stats":
        con = _con()
        print(json.dumps({"db": str(CAPCOM_DB), "total": total_count(con),
                          "unread": unread_count(con)}, indent=2))
        con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
