# Concurrency Audit — Cross-Process Lock & Heartbeat Primitives

**Date:** 2026-07-12  
**Auditor:** haiku-20 (investigator)  
**Scope:** `core/lm_gateway.py`, `core/editor_scheduler.py`, `core/agent_tunnel.py`, `core/task_board.py`  
**Methodology:** Trace lock acquisition, release, heartbeat refresh, and stale reclamation paths. Identify concrete interleaving sequences that cause stuck locks, orphaned locks, or two holders.

---

## Module 1: `core/lm_gateway.py` — Fair FIFO queue for single LM endpoint

### Lock & Heartbeat Design
- **Advisory file lock:** `msvcrt.locking()` (Windows) / `fcntl.flock()` (Unix)
- **Held:** Only during counter increment in `_next_seq()` (lines 96–107)
- **Tickets:** Files under `docs/world/lm_queue/t_<seq>_<pid>.json`, liveness by mtime
- **Heartbeat:** Daemon thread per ticket refreshes mtime every `HEARTBEAT_S=8s` (lines 136–141)
- **Stale reclamation:** Tickets with mtime > `STALE_TTL=25s` unlinked in `_live_tickets()` (lines 116–117)

### Critical Path: `lm_urlopen()` (lines 191–204)
```python
ticket, waited = _acquire(agent)  # get seq, start heartbeat daemon
try:
    resp = urllib.request.urlopen(req, timeout=timeout)
    data = resp.read()
    return _BufferedResponse(data, getcode())
finally:
    ticket.release()  # stop daemon, unlink ticket file
```

### Hazard Analysis

#### Stuck lock in counter increment
**File:line** `core/lm_gateway.py:96–107`  
**Pattern:** `_next_seq()` acquires lock, increments counter, releases in finally  
**Try/finally guard:** YES (lines 98–107)  
**Status:** ✅ SAFE

#### Two holders from stale ticket reclamation
**File:line** `core/lm_gateway.py:160–166` (cleared check) + `110–123` (stale reclamation)  
**Scenario:** 
1. Agent A calls `lm_urlopen()`, ticket acquired, heartbeat daemon starts (line 134)
2. Agent A enters `urllib.request.urlopen()` (10-minute generation call, line 197)
3. Heartbeat daemon dies (e.g., process SIGKILL before urlopen returns)
4. Ticket's mtime stops being updated
5. After 25 seconds, another agent's `_live_tickets()` reclaims the ticket file
6. Agent B acquires a slot, starts generation
7. Agent A's generation finally completes, but Agent B is ALSO in LM now (two holders)

**Concrete interleaving:**
- 0s: A acquires ticket seq=100, starts daemon, enters urlopen() with 600s timeout
- 8s: daemon refreshes mtime
- 16s: daemon refreshes mtime
- 24s: Process killed (agent A dies unexpectedly)
- 25s: Agent B calls `_live_tickets()`, finds seq=100's mtime > 25s, deletes ticket
- 25s: Agent B acquires ticket seq=101, enters urlopen()
- 26s: Agent A's process is still alive, urlopen() completes its call (late reply from LM)
- Both A and B have slots in the queue

**Verdict:** ✅ SAFE (by design)  
**Reason:** Daemon thread is a side-effect of the Python process. If the process dies, the daemon dies with it. The heartbeat thread only keeps mtime fresh while the process is alive and the main thread is in `urllib.request.urlopen()`. The 25s TTL is strictly longer than the 600s timeout (LM max call time) because:
- Heartbeat ticks every 8s (3 ticks per 25s)
- Even a 10-minute call keeps getting refreshed every 8s
- Only a crashed/killed process stops refreshing
- Once the process is dead, the TTL catching it is acceptable — no "two holders" because the dead process is not making a call anymore

---

## Module 2: `core/editor_scheduler.py` — Exclusive UE editor lock

### Lock & Heartbeat Design
- **Advisory file lock:** `msvcrt.locking()` / `fcntl.flock()` on `editor_scheduler.lock`
- **Held:** Only during state read/write (lines 168–189, 196–204, 207–218, 223–227)
- **State file:** `editor_scheduler_state.json` with owner, mode, acquired_at, heartbeat timestamp
- **Heartbeat:** Updated on every call that touches editor (request/heartbeat/release)
- **Stale reclamation:** `_is_owner_alive()` checks heartbeat, reclaims if stale (lines 108–111, 172–173)
- **TTL:** `HEARTBEAT_TIMEOUT=300s` (5 minutes)

### Critical Path: `request_editor()` (lines 157–191)
```python
deadline = time.time() + timeout
while time.time() < deadline:
    fd = _acquire_lock_fd()  # line 168
    try:
        state = _read_state()
        if state.get("owner") and not _is_owner_alive(state):  # line 172
            state = {"owner": None, ...}  # reclaim
        if state.get("owner") is None:  # line 174
            _ensure_mode(mode)
            _write_state({"owner": agent_id, ...})
            return True
        if state.get("owner") == agent_id:  # line 179, mode upgrade
            ...
            _write_state(state)
            return True
    finally:
        _release_lock_fd(fd)  # line 189
    time.sleep(poll)
return False
```

### Hazard Analysis

#### Stuck lock during state read/write
**File:line** `core/editor_scheduler.py:168–189`  
**Pattern:** Lock acquired, state read/checked/written, released in finally  
**Try/finally guard:** YES (lines 168–189)  
**Status:** ✅ SAFE

#### Two holders from stale owner reclamation
**File:line** `core/editor_scheduler.py:172–173` (reclaim check)  
**Scenario:** 
1. Agent A acquires editor, updates state with heartbeat=T0
2. Agent A starts a slow build (e.g., full recompile, no heartbeat calls for 301+ seconds)
3. Agent B polls, reads state, checks heartbeat: now - T0 > 300s → stale
4. Agent B reclaims editor, acquires it for itself
5. Agent A's build completes, still thinks it owns the editor (heartbeat is stale but build succeeded)
6. Two agents think they own the editor

**Verdict:** ⚠️ DESIGN CONSTRAINT (not a bug per calibration rule, but a contract assumption)  
**Reason:** The 300s TTL is intentional. The contract explicitly states: "a silent owner is reclaimed" (line 55 comment). If an agent holds the editor for >5 minutes without heartbeating, it is expected to be dead. Long builds MUST call `heartbeat(agent_id)` during the build. If they don't, the reclamation is correct behavior — it's not a bug, it's the contract enforcing a rule. Verify in caller code (e.g., `build_orchestrator.py`) that long operations call heartbeat.

---

## Module 3: `core/agent_tunnel.py` — Claim + editor + exit lifecycle

### Lock & Heartbeat Design
- **Task board claim:** Via `task_board.claim_task()` (line 271)
- **Editor lock:** Via `editor_scheduler.request_editor()` (line 278)
- **Session record:** Written to `SESSIONS_DIR/{agent}.json` (line 302)
- **Cleanup on exit:** `exit_tunnel()` releases editor and completes task (lines 339–344)
- **Abandoned cleanup:** `tend()` closes sessions whose board claims vanished (lines 187–207)

### Critical Path: `enter()` (lines 261–307)
```python
def enter(agent_id, task_id, capable, editor_timeout, assemble):
    tend()
    task = claim_task(agent_id, task_id, capable)  # line 271: ACQUIRE TASK CLAIM
    if task is None:
        return None
    
    mode = (task.get("resources") or {}).get("editor", "none")
    editor_held = False
    if mode in ("open", "closed"):
        if not request_editor(mode, agent_id, timeout=editor_timeout):  # line 278
            release_task(agent_id, task["id"], ...)  # line 280: only on timeout
            raise TimeoutError(...)
        editor_held = True  # line 285: EDITOR LOCK ACQUIRED
    
    packet = {...}  # lines 287–295
    if assemble:
        toks = _tokens(...)
        packet["heuristics"] = _relevant_heuristics(toks)  # lines 297–298
        packet["mcp_traps"] = _relevant_traps(toks)  # line 299
        packet.update(_graph_context(...))  # line 300
    
    _write_session({...})  # line 302: WRITE SESSION (can fail)
    return packet
```

### Hazard Analysis

#### ✅ Packet building cannot fail
**File:line** `core/agent_tunnel.py:297–300`  
**Analysis:**
- `_tokens()`: string processing, safe
- `_relevant_heuristics()`: catches OSError, returns [] (line 105)
- `_relevant_traps()`: catches all in `_match_lines()`, returns []
- `_graph_context()`: wraps `load_dna_graph()` in try/except at lines 128–131, returns default
- **Status:** ✅ SAFE (defensive code catches all IO exceptions)

#### ❌ HAZARD: Orphaned task claim if request_editor() raises exception
**File:line** `core/agent_tunnel.py:277–284`  
**Scenario:**
1. Line 271: `claim_task()` succeeds, task claim acquired and written to `task_board_state.json`
2. Line 278: `request_editor()` is called
3. Inside `request_editor()` (line 165): `if mode not in ("open", "closed"): raise ValueError(...)`
   - Mode comes from task config; if corrupted, ValueError raised
   - OR: `_acquire_lock_fd()` raises OSError (file system full)
   - OR: `_ensure_mode()` raises CalledProcessError (subprocess fails)
4. Exception escapes `enter()` without calling `release_task()` (line 280 is ONLY called if `request_editor()` returns False, not if it raises)
5. Task claim remains in `task_board_state.json` with status=CLAIMED, claimed_by=agent_id
6. No session record written (line 302 never reached), so `tend()` cannot clean it up
7. Claim stuck for 2 hours (CLAIM_TTL in task_board.py line 83)

**Concrete interleaving:**
- A1 calls `agent_tunnel.enter()`
- A1 claims task tb-0001 (task claim written to disk)
- A1 calls `request_editor()` with corrupted mode parameter
- `request_editor()` raises ValueError("mode must be...")
- Exception escapes `enter()`, no `release_task()` called
- tb-0001 remains claimed by A1 for 2 hours until heartbeat stales
- Other agents cannot claim tb-0001 even though A1 is dead

**Verdict:** ❌ CONFIRMED HAZARD  
**Root cause:** No try/except wrapping the request_editor call to catch exceptions and release the task claim  
**TTL to recovery:** 2 hours (CLAIM_TTL, task_board.py line 83)  
**Impact:** One task unavailable; parallel frontier blocked by one stuck claim; no immediate crash but convoy effect

#### ❌ HAZARD: Orphaned editor lock AND task claim if _write_session() raises exception
**File:line** `core/agent_tunnel.py:277–306`  
**Scenario:**
1. Line 271: `claim_task()` succeeds, task claim acquired
2. Line 278: `request_editor()` succeeds, editor lock acquired, editor_held = True
3. Lines 287–300: Packet building completes (all defensive)
4. Line 302: `_write_session()` called
   - `SESSIONS_DIR.mkdir()` fails: permission denied, disk full → OSError
   - `_session_path().write_text()` fails: permission denied, disk full → OSError
5. Exception escapes `enter()` without releasing editor or task claim
6. Task claim stuck in task_board_state.json for 2 hours
7. Editor lock stuck in editor_scheduler_state.json for 5 minutes
8. Session record never written, so `tend()` cannot detect and clean

**Concrete interleaving:**
- A2 calls `agent_tunnel.enter()`
- A2 claims task tb-0002 (written to disk)
- A2 acquires editor lock (written to disk as owner=A2)
- All packet building succeeds
- Process hits disk-full condition before writing session
- `_write_session()` raises OSError("No space left on device")
- Exception escapes, releases nothing
- A2 is dead
- tb-0002 stuck for 2 hours (task_board can't heartbeat it)
- editor stuck for 5 minutes (editor_scheduler can't heartbeat it)
- A3 polls editor, gets "owned by A2", waits
- A4 tries to claim a different task, but A2's editor lock blocks "closed" mode tasks

**Verdict:** ❌ CONFIRMED HAZARD  
**Root cause:** No try/except wrapping the critical section (editor acquire + session write) to clean up on failure  
**TTL to recovery:** 5 minutes (HEARTBEAT_TIMEOUT, editor_scheduler.py line 55; task claim waits 2 hours but editor is the blocker)  
**Impact:** Editor inaccessible for 5 minutes; all tasks requiring editor mode blocked; parallel pipeline stalls

---

## Module 4: `core/task_board.py` — Parallel-safe task claims

### Lock & Heartbeat Design
- **Advisory file lock:** `msvcrt.locking()` / `fcntl.flock()` on `task_board.lock`
- **Held:** Only during state read/write (inside `@_locked` decorator, lines 276–288)
- **State file:** `task_board_state.json` with tasks array, each task has claimed_by, heartbeat
- **Stale reclamation:** `_reap_stale()` checks each claimed task's heartbeat, reopens if stale (lines 225–235)
- **TTL:** `CLAIM_TTL = 7200s` (2 hours, line 83)

### Critical Path: `@_locked` decorator (lines 276–288)
```python
def _locked(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        fd = _acquire_lock_fd()  # line 279
        try:
            state = _read_state()  # line 281
            _reap_stale(state)  # line 282
            result = fn(state, *args, **kwargs)  # call mutator under lock
            _write_state(state)  # line 284
            return result
        finally:
            _release_lock_fd(fd)  # line 287
    return wrapper
```

### Atomic state write (lines 141–149)
```python
def _write_state(state):
    tmp = STATE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    if STATE_PATH.exists():
        try:
            STATE_PATH.replace(STATE_PATH.with_suffix(".json.bak"))  # backup old
        except Exception:
            pass
    tmp.replace(STATE_PATH)  # atomic replace (OS-level)
```

### Hazard Analysis

#### All mutations atomic under lock
**File:line** `core/task_board.py:276–288`  
**Pattern:** Every mutating function (`add_task`, `claim_task`, `complete_task`, etc.) wrapped in `@_locked`  
**Try/finally guard:** YES (lines 279–287)  
**Stale reclamation:** Called on every mutation (line 282)  
**Status:** ✅ SAFE  
**Reason:** All read-modify-write of state is atomic. Lock is held for entire duration. Even if `_write_state()` fails (disk full), the lock is released in finally and the in-memory state is discarded (next call reads fresh). No two holders possible.

#### State write crash recovery
**File:line** `core/task_board.py:141–149`  
**Fallback on read:** Lines 132–138, try STATE_PATH then STATE_PATH.bak  
**Status:** ✅ SAFE  
**Reason:** Atomic rename at OS level; .bak fallback ensures one valid copy always exists

#### Stale claim reclamation
**File:line** `core/task_board.py:225–235`  
**Pattern:** Checked on every @_locked operation  
**TTL:** 2 hours (coarse-grained tasks)  
**Status:** ✅ SAFE (design constraint)  
**Reason:** Long operations MUST heartbeat. If not heartbeating, agent is assumed dead after 2 hours. This is by contract. No "two holders" — only one claim per task at a time, and stale reclamation is gated by file lock.

---

## Summary

| Module | Hazard | Severity | TTL | Fixable |
|---|---|---|---|---|
| `lm_gateway.py` | None found | — | — | — |
| `editor_scheduler.py` | Stale reclamation contract violation (caller must heartbeat) | Design constraint | 5m | N/A (by design) |
| **`agent_tunnel.py`** | **Orphaned task claim if `request_editor()` raises** | 🔴 **High** | 2h | ✅ Add try/except around editor acquire; release task on fail |
| **`agent_tunnel.py`** | **Orphaned editor lock + task claim if `_write_session()` fails** | 🔴 **Critical** | 5m (editor), 2h (task) | ✅ Wrap critical section in try/except; release both on fail |
| `task_board.py` | None found | — | — | — |

---

## Recommended Fixes

### Fix 1: agent_tunnel.py — Wrap critical section (lines 277–306)
```python
task = claim_task(agent_id, task_id=task_id, capable=capable)
if task is None:
    return None

mode = (task.get("resources") or {}).get("editor", "none")
editor_held = False
try:
    if mode in ("open", "closed"):
        if not request_editor(mode, agent_id, timeout=editor_timeout):
            release_task(agent_id, task["id"],
                         note=f"tunnel: editor '{mode}' not granted in {editor_timeout}s")
            raise TimeoutError(
                f"editor '{mode}' not granted within {editor_timeout}s — claim on "
                f"{task['id']} released; retry when the editor frees up")
        editor_held = True

    packet = { ... }  # build packet
    
    _write_session({...})  # write session
    return packet
except Exception:
    if editor_held:
        try:
            release_editor(agent_id)
        except Exception:
            pass
    try:
        release_task(agent_id, task["id"], note="tunnel enter failed due to exception")
    except Exception:
        pass
    raise
```

---

## Calibration Notes

- **Stuck lock**: Checked. `lm_gateway` and `task_board` have try/finally guards. `editor_scheduler` has try/finally. `agent_tunnel.enter()` does NOT for the critical section.
- **Two holders**: Checked. `lm_gateway` ticket reclamation is safe (daemon keeps mtime fresh). `editor_scheduler` stale reclamation is by design (5-minute TTL). No "two simultaneous holders" found.
- **Lost update**: Checked. All atomic operations use file-lock + try/finally. No RMW windows without lock.
- **Never-reclaimed**: Checked. All processes have heartbeat/TTL. Worst case: 2 hours for task claim, 5 minutes for editor.

---

## Conclusion

✅ **Verdict:** The primitives are MOSTLY crash-safe with defensive code. 

❌ **Exception:** `agent_tunnel.enter()` has a critical gap: if an exception occurs after acquiring the editor lock but before writing the session record, both locks are orphaned. This is fixable with a try/except wrapper.

**Risk level:** MEDIUM (5-minute window for editor contention; 2-hour window for task queue blocking).
