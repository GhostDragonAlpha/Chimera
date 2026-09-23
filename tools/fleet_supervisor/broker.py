# fleet_supervisor/broker.py -- resource broker, PHASE 1 (machine-wide admission).
#
# Astra's contract (astra-round6-answer-20260922.md):
#   mode file (gaming|fleet|training, default fleet); gaming refuses GPU work
#   and new builds; fleet memory ceiling 48 GiB aggregate committed; per
#   execution session 8 GiB default, build 16 GiB; "refuse admission if free
#   physical memory falls below an initial 32 GiB reserve"; GPU: one exclusive
#   reservation -- "If its expected end passes, it remains occupied until
#   completion is verified. Likewise, a lost heartbeat means ownership
#   uncertain, not permission to start a competing job."
# The broker MANAGES reservations; it never consumes the GPU itself.
from __future__ import annotations

import json
import os
import time

from . import jobobject, registry

DEFAULT_CONTROL_DIR = r"E:\ChimeraWork\control"

MODE_FILE = "fleet_mode"
RESERVATION_FILE = "gpu_reservation"
IDLE_TIMEOUTS_FILE = "fleet_idle_timeouts.json"

MODES = ("gaming", "fleet", "training")

# Astra's starting limits (initial experimental policy, not capacity claims)
FLEET_MEM_CEILING_GIB = 48.0
MIN_FREE_PHYS_GIB = 32.0
DEFAULT_SESSION_MEM_GIB = 8.0
BUILD_MEM_GIB = 16.0
DEFAULT_MAX_PROCS = 64

HEARTBEAT_STALE_S = 60.0  # a reservation heartbeat older than this = OWNERSHIP UNCERTAIN

DEFAULT_IDLE_TIMEOUTS = {
    "browser": 120.0,   # Astra: two minutes for browsers/servers -- starting hypothesis
    "server": 120.0,
    "engine": 300.0,    # five minutes for engine editors -- starting hypothesis
    "build": None,      # finite work; bounded by limits, not idle time
    "gpu_phase": None,  # bounded by its reservation
}


# ------------------------------------------------------------------ mode
def mode_path(control_dir: str = DEFAULT_CONTROL_DIR) -> str:
    return os.path.join(control_dir, MODE_FILE)


def read_mode(control_dir: str = DEFAULT_CONTROL_DIR) -> str:
    """Absent or unreadable file means the default: fleet."""
    try:
        with open(mode_path(control_dir), "r", encoding="utf-8") as f:
            mode = f.read().strip().lower()
        return mode if mode in MODES else "fleet"
    except OSError:
        return "fleet"


def write_mode(mode: str, control_dir: str = DEFAULT_CONTROL_DIR) -> str:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}, got {mode!r}")
    os.makedirs(control_dir, exist_ok=True)
    with open(mode_path(control_dir), "w", encoding="utf-8") as f:
        f.write(mode)
    return mode


# ------------------------------------------------------------------ GPU reservation
def reservation_path(control_dir: str = DEFAULT_CONTROL_DIR) -> str:
    return os.path.join(control_dir, RESERVATION_FILE)


def read_reservation(control_dir: str = DEFAULT_CONTROL_DIR) -> dict | None:
    try:
        with open(reservation_path(control_dir), "r", encoding="utf-8") as f:
            text = f.read().strip()
        return json.loads(text) if text else None
    except (OSError, json.JSONDecodeError):
        return None


def write_reservation(res: dict | None, control_dir: str = DEFAULT_CONTROL_DIR) -> None:
    os.makedirs(control_dir, exist_ok=True)
    with open(reservation_path(control_dir), "w", encoding="utf-8") as f:
        if res is None:
            f.write("")
        else:
            json.dump(res, f, indent=1)


def reservation_state(res: dict | None, now: float | None = None) -> str:
    """Classify a reservation WITHOUT ever auto-freeing it:
      active          -- owner heartbeat fresh, completion not yet verified
      expired_pending -- expected_end passed but the owner never reported
                         completion: STILL OCCUPIED (Astra's rule)
      uncertain       -- heartbeat lost: OWNERSHIP UNCERTAIN, never auto-free
      released        -- the owner itself recorded completion/released
    """
    if not res or not res.get("owner_id"):
        return "none"
    if str(res.get("status", "")).lower() in ("released", "completed"):
        return "released"
    now = time.time() if now is None else now
    hb = res.get("heartbeat_ts")
    if not hb:
        return "uncertain"
    try:
        hb_age = now - float(hb)
    except (TypeError, ValueError):
        return "uncertain"
    if hb_age > HEARTBEAT_STALE_S:
        return "uncertain"
    end = res.get("expected_end_ts")
    if end is not None:
        try:
            if now > float(end):
                return "expired_pending"  # heartbeat may be fresh; end passed, no completion
        except (TypeError, ValueError):
            pass
    return "active"


def touch_reservation(owner_id: str, control_dir: str = DEFAULT_CONTROL_DIR,
                      expected_end_ts: float | None = None, **extra) -> dict:
    """Owner heartbeat. Creating/refreshing a reservation is an OWNER action;
    the broker only READS it (except the trivial admin write below)."""
    res = read_reservation(control_dir) or {}
    if res.get("owner_id") not in (None, owner_id):
        raise PermissionError(f"reservation owned by {res.get('owner_id')!r}, not {owner_id!r}")
    res.update({
        "owner_id": owner_id,
        "heartbeat_ts": time.time(),
        "status": "held",
    })
    if expected_end_ts is not None:
        res["expected_end_ts"] = expected_end_ts
    res.update(extra)
    write_reservation(res, control_dir)
    return res


def release_reservation(owner_id: str, control_dir: str = DEFAULT_CONTROL_DIR) -> dict:
    """Only the owner marks completion; that (and only that) frees the GPU."""
    res = read_reservation(control_dir) or {}
    if res.get("owner_id") != owner_id:
        raise PermissionError(f"cannot release: reservation owned by {res.get('owner_id')!r}, not {owner_id!r}")
    res["status"] = "released"
    res["released_ts"] = time.time()
    write_reservation(res, control_dir)
    return res


# ------------------------------------------------------------------ admission
def kind_defaults(kind: str) -> dict:
    mem = BUILD_MEM_GIB if kind == "build" else DEFAULT_SESSION_MEM_GIB
    # Astra: "A judge or training job that needs more memory must declare a
    # measured reservation; it does not silently inherit an 8 GiB allowance."
    if kind == "gpu_phase":
        mem = None  # must declare measured memory explicitly
    return {"mem_gib": mem, "max_procs": DEFAULT_MAX_PROCS, "cpu_pct": None}


def normalize_spec(spec: dict) -> dict:
    s = dict(spec)
    for key in ("session_id", "owner_lane", "command", "kind"):
        if not s.get(key):
            raise ValueError(f"spec missing {key!r}")
    if s["kind"] not in ("engine", "server", "browser", "build", "gpu_phase"):
        raise ValueError(f"unknown kind {s['kind']!r}")
    res = dict(s.get("resources") or {})
    d = kind_defaults(s["kind"])
    mem = res.get("mem_gib", d["mem_gib"])
    if mem is None:
        raise ValueError("gpu_phase must declare a measured mem_gib reservation")
    res["mem_gib"] = float(mem)
    res["max_procs"] = int(res.get("max_procs") or d["max_procs"])
    res["cpu_pct"] = res.get("cpu_pct") or d["cpu_pct"]
    if res["cpu_pct"]:
        # F-CPURATE: unenforceable on this build -- refusing beats pretending.
        raise ValueError(
            "cpu_pct refused: CPU hard caps are not enforceable on this build "
            "(measured finding F-CPURATE in tools/science_funnel/validation/"
            "fleet_supervisor_20260922/); declare mem_gib/max_procs instead")
    s["resources"] = res
    s["ports"] = sorted({int(p) for p in (s.get("ports") or [])})
    return s


def admit(spec: dict, *, control_dir: str = DEFAULT_CONTROL_DIR,
          registry_path: str = registry.DEFAULT_REGISTRY,
          memory_status_fn=None, now: float | None = None) -> tuple[bool, str]:
    """Machine-wide admission control. Returns (ok, reason). Pure decision:
    it reads mode/reservation/registry/RAM and refuses or permits."""
    s = normalize_spec(spec)
    kind = s["kind"]
    res = s["resources"]
    now = time.time() if now is None else now
    memory_status_fn = memory_status_fn or jobobject.memory_status

    # 1. mode gates
    mode = read_mode(control_dir)
    if mode == "gaming":
        if kind == "gpu_phase":
            return False, "refused: gaming mode admits no fleet GPU work"
        if kind == "build":
            return False, "refused: gaming mode admits no new builds"

    # 2. GPU reservation gate
    if kind == "gpu_phase":
        st = reservation_state(read_reservation(control_dir), now=now)
        if st == "none":
            return False, "refused: gpu_phase requires a reservation; none exists"
        if st == "released":
            return False, "refused: gpu_phase requires a reservation; the last one is released"
        owner = (read_reservation(control_dir) or {}).get("owner_id")
        if st in ("expired_pending", "uncertain"):
            return False, (f"refused: GPU ownership {st.upper()} (Astra: never auto-free, "
                           f"never a competing job); owner={owner!r}")
        if owner != s["session_id"] and owner != s.get("owner_lane"):
            return False, f"refused: reservation owned by {owner!r}, not this session"

    # 3. fleet memory ceiling (declared, active sessions only)
    actives = registry.active_sessions(registry_path)
    declared = sum(registry.declared_mem_gib(r) for r in actives.values())
    if declared + res["mem_gib"] > FLEET_MEM_CEILING_GIB:
        return False, (f"refused: fleet declared memory {declared:.1f} GiB + "
                       f"{res['mem_gib']:.1f} GiB > {FLEET_MEM_CEILING_GIB:.0f} GiB ceiling")

    # 4. port exclusivity among active sessions
    if s["ports"]:
        for sid, r in actives.items():
            clash = sorted(set(r.get("ports") or []) & set(s["ports"]))
            if clash:
                return False, f"refused: ports {clash} already declared by active session {sid}"

    # 5. free physical RAM reserve
    ms = memory_status_fn()
    if ms["free_phys_gib"] < MIN_FREE_PHYS_GIB:
        return False, (f"refused: free physical RAM {ms['free_phys_gib']:.1f} GiB < "
                       f"{MIN_FREE_PHYS_GIB:.0f} GiB reserve")

    return True, f"admitted ({mode} mode; fleet declared {declared:.1f} GiB)"


# ------------------------------------------------------------------ idle timeouts
def idle_timeouts(control_dir: str = DEFAULT_CONTROL_DIR) -> dict[str, float | None]:
    out = dict(DEFAULT_IDLE_TIMEOUTS)
    try:
        with open(os.path.join(control_dir, IDLE_TIMEOUTS_FILE), "r", encoding="utf-8") as f:
            out.update({k: (None if v is None else float(v)) for k, v in json.load(f).items()})
    except (OSError, json.JSONDecodeError, ValueError, AttributeError):
        pass
    return out
