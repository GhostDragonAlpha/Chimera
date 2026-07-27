# Saturation Audit — Growing Corpus False-Matches

**Date**: 2026-07-12  
**Auditor**: haiku-11 (read-only investigator)  
**Task**: Find dedup/coverage/similarity/novelty logic that compares candidates against a GROWING GLOBAL corpus with FIXED thresholds (saturation risk pattern), rather than per-entry or normalized comparisons.

**Precedent**: `core/heuristic_distiller.py` had a known saturation bug in old `coverage_check` (fixed 2026-07-07): summed token presence over the ENTIRE (monotonically growing) PENDING_HEURISTICS document, so as the corpus grew, any 3-4 common game-dev words were "present" and suppressed genuinely-new lessons.

---

## FINDINGS

### 1. FIXED: `core/heuristic_distiller.py:coverage_check` (lines 148–174)

**Status**: SAFE — Already fixed  
**File path**: E:\PythonChimera\Chimera\core\heuristic_distiller.py:148–174  
**Function**: `coverage_check(signature: str) -> str`

**Mechanism Fixed**:
- **OLD (saturation bug)**: Accumulated token union across the ENTIRE `COVERAGE_SOURCES` documents (monotonically growing file size)
- **NEW (fixed 2026-07-07)**: Per-entry whole-word overlap — iterates lines in each source and checks if >=80% of signature tokens hit the SAME LINE (lines 169–173)

```python
# Fixed code (line 169–173):
for line in text.splitlines():
    if len(sig_tokens & _tokens(line)) >= threshold:
        return src.name
```

**Why safe now**: Adding unrelated entries to COVERAGE_SOURCES can never raise a candidate's apparent coverage. Each line is independent. Saturation eliminated.

---

### 2. CLEAR: `core/gardener.py` (lines 83–112)

**Status**: SAFE  
**File path**: E:\PythonChimera\Chimera\core\gardener.py:83–112  
**Functions**: `_append_claude_md_bullet`, `_append_pathway_trap`

**Mechanism**: Before appending a rule to constitution organs (CLAUDE.md, MCP_PATHWAYS.md), checks `if rule in text:` (lines 86, 98). This is a safety check (prevent duplicate appends), not a dedup against a growing corpus. Each organ is checked independently; the rule is compared against the CURRENT document state, not accumulated history.

**Why safe**: Per-organ, per-rule check. No threshold that gets easier to meet as the document grows.

---

### 3. CLEAR: `core/heuristic_distiller.py:conflict_check` (lines 177–191)

**Status**: SAFE  
**File path**: E:\PythonChimera\Chimera\core\heuristic_distiller.py:177–191  
**Function**: `conflict_check(signature: str, nodes: list, pending_text: str) -> list`

**Mechanism**: Flags existing Heuristic nodes whose topic OVERLAPS (>=2 shared significant tokens). Per-rule, fixed threshold of 2 tokens (lines 185–186). No accumulation across the graph; each rule is checked independently.

```python
overlap = sig_tokens & _tokens(f"{n.get('signature','')} {n.get('rule','')}")
if len(overlap) >= 2:  # Fixed threshold, per-node
    conflicts.append(...)
```

**Why safe**: Overlap check is BINARY (>= 2 tokens), evaluated per existing Heuristic node. Growing graph adds more checks, not lower threshold.

---

### 4. CLEAR: `core/rep_engine.py` (batches 1–7, lines 587–815)

**Status**: SAFE  
**File path**: E:\PythonChimera\Chimera\core\rep_engine.py  
**Functions**: `build()`, `run()`, `status()`, `rep_gate()`, `maybe_promote()`

**Mechanism**: Per-feature batteries (constraint atoms). Rep gate compares a feature's total reps + recent pass-rate streak against FIXED thresholds (lines 700–724):
- `total >= required` (required = min_reps, battery-size-scaled)
- `recent streak >=95% for >=8 runs`

**Why safe**: Thresholds are per-feature, not global. Adding new features doesn't make old features' thresholds easier to hit. Rep gate is INVARIANT to battery growth.

---

### 5. CLEAR: `core/collapse_proxy.py` (lines 99–248)

**Status**: SAFE  
**File path**: E:\PythonChimera\Chimera\core\collapse_proxy.py:99–248  
**Functions**: `tend()`, `sweep()`, `_clean_exercises()`

**Mechanism**: Exercised feature tracking is per-feature (lines 65–80). For each feature, collects `simtest_id` list where ALL beats reached 'reached'. Min-sessions gate is ABSOLUTE (`len(evidence) >= min_sessions`), not threshold-relative.

```python
if len(evidence) >= min_sessions:  # Absolute check, not relative
    record_observation(...)
```

**Why safe**: Gate is per-feature, not corpus-wide. Growing simulation history just adds to per-feature `evidence` list; threshold doesn't become easier.

---

### 6. CLEAR: `core/faculty.py:_h_rules_already_pinned` (lines 104–109)

**Status**: SAFE (but nuanced)  
**File path**: E:\PythonChimera\Chimera\core\faculty.py:104–109  
**Function**: `_h_rules_already_pinned() -> set`

**Mechanism**: Combines curriculum text + pending heuristics JSON, searches for literal H-rule IDs (`\bH-\d+\b`). Binary check per rule: either ID exists or it doesn't.

```python
text = _curriculum_text() + "\n" + json.dumps(_read_pending())
return set(re.findall(r"\bH-\d+\b", text))
```

**Why safe (nominally)**: Presence/absence of an H-rule ID is binary, not threshold-based. However, the INTENT is to prevent re-proposing, and if a rule's presence is EVER recorded (even if later removed), it would still block re-proposal. This is idempotent by design (rules are never deleted), so no saturation occurs in practice. The combining of curriculum + pending is necessary for the real dedup goal.

---

### 7. CLEAR: `core/solver.py:_prior_solutions` (lines 46–58)

**Status**: SAFE  
**File path**: E:\PythonChimera\Chimera\core\solver.py:46–58  
**Function**: `_prior_solutions(blocker: str, nodes) -> list`

**Mechanism**: Per-node token overlap score (line 54). Each pathway_attempt node gets a fresh `blob = json.dumps(n, ...)`, and token hits are counted PER blob. Threshold `>= max(2, len(toks)//3)` is ABSOLUTE, not relative.

```python
for n in nodes:
    # ... per-node:
    blob = json.dumps(n, default=str).lower()
    score = sum(1 for t in toks if t in blob)
    if score >= max(2, len(toks) // 3):  # Fixed threshold per node
```

**Why safe**: Per-node comparison. Growing node graph just adds more candidates, not lower threshold.

---

### 8. CLEAR: `core/agent_tunnel.py:_match_lines` (lines 86–98)

**Status**: SAFE  
**File path**: E:\PythonChimera\Chimera\core\agent_tunnel.py:86–98  
**Function**: `_match_lines(text: str, tokens: set, ...) -> list`

**Mechanism**: Per-line token hit count (line 94). Ranks lines by distinct-token hits; capped at 6 results. No accumulation; each line is scored independently.

```python
for line in (text or "").splitlines():
    # ... per-line:
    hits = sum(1 for t in tokens if t in low)
    if hits:
        scored.append((hits, line.strip()))
```

**Why safe**: Per-line ranking, not corpus-wide. Growing input document just adds more lines to rank; hit-counting logic doesn't change.

---

### 9. CLEAR: `core/muse.py:merge_muse_proposals_to_candidates` (lines 132–192)

**Status**: SAFE  
**File path**: E:\PythonChimera\Chimera\core\muse.py:169–172  
**Function**: `merge_muse_proposals_to_candidates()`

**Mechanism**: Dedup check (line 170): `if any(c.get("name") == title for c in existing_candidates)`. Compares proposal title against `existing_candidates` (a finite list loaded fresh from rehearsal_candidates.json). Binary match, no threshold.

```python
if any(c.get("name") == title for c in existing_candidates):
    print(f"[muse] '{title}' already in candidates — skipping")
```

**Why safe**: Finite existing list, exact-match dedup. No threshold that gets easier to hit with growth.

---

### 10. CLEAR: `core/ripener.py:already_cited` (lines 32–34)

**Status**: SAFE  
**File path**: E:\PythonChimera\Chimera\core\ripener.py:32–34  
**Function**: `already_cited(pain_id: str, tasks: list) -> bool`

**Mechanism**: Checks if `pain_id` string appears in any task's recipe. Tasks are loaded fresh per `tend()` call; finite set. Binary presence check.

```python
return any(pain_id in (t.get("recipe") or "") and t.get("status") != "abandoned"
           for t in tasks)
```

**Why safe**: Per-run finite task list, substring match, no threshold.

---

## SUMMARY

| File | Function | Risk | Notes |
|------|----------|------|-------|
| `heuristic_distiller.py` | `coverage_check` | ✅ FIXED | Per-line checks; saturation eliminated 2026-07-07 |
| `gardener.py` | `_append_*` | ✅ SAFE | Per-organ, per-rule checks; no threshold growth |
| `heuristic_distiller.py` | `conflict_check` | ✅ SAFE | Fixed 2-token overlap; per-node evaluation |
| `rep_engine.py` | all | ✅ SAFE | Per-feature gates; absolute thresholds |
| `collapse_proxy.py` | all | ✅ SAFE | Per-feature evidence lists; absolute thresholds |
| `faculty.py` | `_h_rules_already_pinned` | ✅ SAFE | Binary ID presence check; idempotent by design |
| `solver.py` | `_prior_solutions` | ✅ SAFE | Per-node blob scoring; fixed threshold |
| `agent_tunnel.py` | `_match_lines` | ✅ SAFE | Per-line ranking; no corpus-wide accumulation |
| `muse.py` | `merge_muse_proposals_to_candidates` | ✅ SAFE | Finite existing list; exact-match dedup |
| `ripener.py` | `already_cited` | ✅ SAFE | Per-run finite task set; substring match |

---

## BLOCKERS / CONCERNS

**None detected.** The saturation-risk pattern (fixed-threshold comparisons against UNBOUNDED growing corpus) was endemic to `heuristic_distiller.py::coverage_check` and has been addressed. No active saturation logic remains in the auditedpaths.

---

## METHODOLOGY NOTES

- Searched for keyword patterns: `coverage`, `dedup`, `overlap`, `similar`, `duplicate`, `novelty`, `already`, `seen`, `token`, `in text`, `for.*in.*nodes`
- Read all likely-suspect modules: gardener, rehearsal, collapse_proxy, heuristic_distiller, rep_engine, faculty, agent_tunnel, solver, ripener, muse, critic, history_book, dream_loop
- Focused on functions that make pass/fail or inclusion/exclusion decisions based on string/token similarity
- Checked both the MECHANISM (what grows?) and the DECISION (how is threshold applied?)
- Confirmed per-entry/per-line/per-node evaluation where thresholds are fixed and independent of corpus growth
