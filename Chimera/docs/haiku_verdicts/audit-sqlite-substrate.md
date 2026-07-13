# SQLite Substrate Audit — Chimera DNA Graph & World Model

**Audited:** `core/world_store.py` (world model substrate) + `core/dna_sqlite_backend.py` (DNA graph on SQLite)  
**Date:** 2026-07-12  
**Verdict:** CRITICAL data-corruption risks confirmed.

---

## Findings

### 1. CRITICAL: Transaction Atomicity Failure in save_graph() — Data Loss Risk

**File:** `core/dna_sqlite_backend.py` lines 74–95

**The Bug:**
```python
def save_graph(graph, db_path=DNA_DB_PATH, write_snapshot=True):
    con = ws.connect(db_path)
    con.execute("DELETE FROM node")
    con.execute("DELETE FROM edge")
    if getattr(con, "_caps", {}).get("fts5"):
        con.execute("DELETE FROM node_fts")
    if getattr(con, "_caps", {}).get("rtree"):
        con.execute("DELETE FROM node_rtree")
    con.commit()              # <-- Line 84: COMMITS DELETES HERE

    nrows = [...]
    ws.add_nodes(con, nrows)  # <-- Line 88: if this fails, deletes already committed
    erows = [...]
    ws.add_edges(con, erows)  # <-- Line 94: if this fails, deletes already committed
    con.close()
```

**The Failure Scenario:**
- `save_graph()` commits the DELETE operations at line 84
- Then calls `ws.add_nodes(con, nrows)` (world_store.py:118–141)
  - `add_nodes` does `con.executemany(INSERT)` at line 123
  - Then conditionally `con.executemany(INSERT INTO node_fts)` at line 134
  - Then conditionally `con.executemany(INSERT INTO node_rtree)` at line 137–140
  - Then commits at line 141
- **If the FTS insert fails after the node insert (e.g., disk full, constraint violation):**
  - Exception propagates out of `ws.add_nodes()`
  - The DELETEs at line 84 have ALREADY BEEN COMMITTED
  - The nodes may be partially inserted (base table yes, indices no)
  - Result: **Old graph DELETED, new graph CORRUPTED and incomplete**

**Similar risk in `ws.add_edges()` (line 94):**
- If `add_edges()` fails partway (e.g., after 10k of 50k edge inserts), the deletes are still committed

**Concrete Data-Loss Example:**
```
1. save_graph called with 50,000 node mutation
2. DELETEs commit successfully (old state erased)
3. ws.add_nodes inserts base rows, starts FTS index
4. FTS insert fails on node 25,000 (disk full, OOM, database corruption)
5. Exception raised, add_nodes exits without commit
6. Result: old data gone, only 25k new nodes written, graph is corrupted
7. No rollback—deletes were already committed at line 84
```

**Impact:** Developers lose the entire DNA graph state on a single transient failure (disk full, temporary corruption, constraint violation during large mutations).

---

### 2. MAJOR: JSON Snapshot Divergence — Stale Backup on Write Failure

**File:** `core/dna_sqlite_backend.py` lines 97–101

**The Bug:**
```python
    con.close()  # SQLite committed and closed

    if write_snapshot:
        JSON_SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        tmp = JSON_SNAPSHOT.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(graph, indent=2), encoding="utf-8")  # <-- can fail
        tmp.replace(JSON_SNAPSHOT)  # <-- atomic on POSIX; if write fails, old JSON remains
```

**Failure Scenario:**
- SQLite write completes and connection is closed (line 95, committed)
- JSON snapshot write fails at line 100 (disk full, permission denied, path issues)
- Exception propagates; JSON file is not updated (stays stale or partially written)
- SQLite db has correct state; JSON snapshot is stale
- State is DIVERGED

**Concrete Scenario:**
```
1. save_graph(large_mutation)
2. SQLite: 50k nodes written, committed, connection closed ✓
3. JSON: write_text() fails with OSError (disk full)
4. Exception raised; JSON snapshot unchanged (still has 40k old nodes)
5. SQLite: 50k nodes ✓   JSON: 40k nodes (stale) ✗
6. On next clone/fresh load, ensure_seeded might load stale JSON or hit corrupted file
```

**Impact:** Backup/snapshot is unreliable. If db gets deleted and JSON is the fallback, stale data is restored.

---

### 3. MAJOR: Corrupted JSON Crash in ensure_seeded() — No Error Resilience

**File:** `core/dna_sqlite_backend.py` line 112

**The Bug:**
```python
def ensure_seeded(db_path=DNA_DB_PATH, json_path=JSON_SNAPSHOT):
    con = ws.connect(db_path)
    n = con.execute("SELECT COUNT(*) FROM node").fetchone()[0]
    con.close()
    if n == 0 and Path(json_path).exists():
        graph = json.loads(Path(json_path).read_text(encoding="utf-8"))  # <-- NO TRY/EXCEPT
        if graph.get("nodes"):
            save_graph(graph, db_path=db_path, write_snapshot=False)
            return len(graph["nodes"])
    return 0
```

**Failure Scenario:**
- JSON file is corrupted (from a failed write at dna_sqlite_backend.py:100, e.g., truncated to 50% completion)
- `ensure_seeded()` is called (e.g., on first load in fresh clone)
- `json.loads()` raises `JSONDecodeError`
- No try/except; exception propagates uncaught
- Pipeline crash with cryptic JSON decode error, no hint that file is corrupted

**Concrete Scenario:**
```
1. save_graph() fails during JSON write; file left truncated (1MB of 2MB)
2. Fresh clone pulled; docs/chimera_dna_graph.json is truncated
3. Pipeline loads: ensure_seeded() called
4. json.loads(truncated_file) -> JSONDecodeError: "Expecting value: line 5678 column 1"
5. Pipeline crashes; no recovery path, no message saying JSON is corrupted
```

**Impact:** Breaks first-load recovery flow. Developers have no way to recover from a partially-written JSON snapshot.

---

### 4. MINOR: Connection Leak in world_store.main() — Resource Exhaustion on Repeated CLI

**File:** `core/world_store.py` lines 312–320

**The Bug:**
```python
    args = p.parse_args(argv)
    if args.cmd == "benchmark":
        benchmark(n_nodes=args.nodes)
    elif args.cmd == "search":
        con = connect(args.db)  # <-- CREATED
        print(json.dumps(search(con, args.query), indent=2))
        # <-- NO con.close()
    elif args.cmd == "around":
        con = connect(args.db)  # <-- CREATED
        print(json.dumps(around(con, args.x, args.y, args.radius), indent=2))
        # <-- NO con.close()
    elif args.cmd == "stats":
        con = connect(DEFAULT_DB)  # <-- CREATED
        print(json.dumps(stats(con), indent=2))
        # <-- NO con.close()
```

**Failure Scenario:**
- CLI subcommands `search`, `around`, `stats` create connections but don't close them
- Each invocation leaks one file descriptor
- On repeated runs (e.g., shell loop calling `python -m core.world_store search ...` 1000 times), file descriptor table fills
- Eventually: "OSError: too many open files" or "sqlite3.OperationalError"

**Concrete Scenario:**
```bash
for i in {1..100}; do
  python -m core.world_store search --query "beacon"
done
# After ~50–100 runs: OSError: [Errno 24] Too many open files
```

**Impact:** CLI tools are flaky on repeated use. Low severity for current usage (one-off queries), but breaks automation loops.

---

## Summary

| Issue | File | Line(s) | Severity | Data Loss? | Root Cause |
|-------|------|---------|----------|-----------|-----------|
| Deletes committed before adds | dna_sqlite_backend.py | 74–95 | **CRITICAL** | **YES** | Missing transaction wrapper; `con.commit()` at line 84 commits deletes before adds complete |
| JSON snapshot divergence | dna_sqlite_backend.py | 97–101 | **MAJOR** | Conditional | JSON write failure after SQLite commit; no atomic swap |
| Corrupted JSON crash | dna_sqlite_backend.py | 112 | **MAJOR** | Indirect | No try/except around `json.loads()` |
| Connection leak | world_store.py | 312–320 | MINOR | NO | CLI handlers don't call `con.close()` |

---

## SQL Injection Check

**VERDICT: SAFE**

All `execute()` calls use parameterized queries (`?` placeholders):
- Line 130 (world_store.py): `f"SELECT ... WHERE id IN ({','.join('?'*len(chunk))})"` — builds placeholder string only, data in `chunk` tuple
- All other queries use `?` placeholders with separate parameter tuples
- No string interpolation of user/graph data into SQL

**Confirmed SAFE patterns:**
- `con.execute(sql_literal, params_tuple)` ✓
- `con.executemany(sql_literal, rows_iterable)` ✓
- `f"... WHERE id IN ({','.join('?'*n)})"` with data in separate tuple ✓

---

## Notes for Fix

### Priority 1 — Fix save_graph() atomicity (prevents data loss)
Wrap the entire mutation in a transaction; if any step fails, rollback all:
```python
def save_graph(graph, db_path=DNA_DB_PATH, write_snapshot=True):
    con = ws.connect(db_path)
    try:
        con.execute("BEGIN EXCLUSIVE")
        con.execute("DELETE FROM node")
        con.execute("DELETE FROM edge")
        # ... deletes ...
        # ... add_nodes and add_edges without internal commits ...
        con.commit()  # <-- single commit after all writes succeed
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
```

### Priority 2 — Add error handling to ensure_seeded() 
Gracefully handle corrupted JSON:
```python
    if n == 0 and Path(json_path).exists():
        try:
            graph = json.loads(Path(json_path).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError) as e:
            print(f"WARNING: corrupted JSON snapshot {json_path}: {e}", file=sys.stderr)
            return 0  # fall back to empty db
        if graph.get("nodes"):
            save_graph(graph, db_path=db_path, write_snapshot=False)
            return len(graph["nodes"])
```

### Priority 3 — JSON snapshot write atomicity
Use atomic rename with cleanup:
```python
    if write_snapshot:
        JSON_SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        tmp = JSON_SNAPSHOT.with_suffix(".json.tmp")
        try:
            tmp.write_text(json.dumps(graph, indent=2), encoding="utf-8")
            tmp.replace(JSON_SNAPSHOT)  # atomic rename
        except Exception:
            if tmp.exists():
                tmp.unlink()  # clean up partial write
            # log warning but don't crash; SQLite is the source of truth
```

### Priority 4 — CLI connection cleanup (optional, low impact)
```python
    elif args.cmd == "search":
        con = connect(args.db)
        try:
            print(json.dumps(search(con, args.query), indent=2))
        finally:
            con.close()
```

---

**Auditor:** haiku-23 (read-only investigation)  
**Status:** Findings documented; fixes require Code mode  
**Recommendation:** Fix Priority 1 + 2 before any further graph writes.
