# DNA Graph Node Key Contract Audit

**Audit Date:** 2026-07-12  
**Auditor:** haiku-22 (read-only investigation)  
**Scope:** core/graphify_interface.py WRITERS vs core/*.py READERS

---

## WRITERS TABLE: Keys Written by Node Type

Each node type is created by a `_mutate_*` function that writes specific keys.

| Node Type | Writer Function | Keys Written |
|-----------|-----------------|--------------|
| **Observation** | `_mutate_observation` (L1722) | `id`, `type`, `timestamp`, `feature_name`, `verdict`, `notes`, `observer`, `derived_from`, `quote`, `tacit`, `error_signature`, `template_file`, `error_category`, `fix_description`, `compilation_result`, `links` |
| **ProfessorGrade** | `_mutate_professor_grade` (L1169) | `id`, `type`, `timestamp`, `feature`, `grade`, `score`, `reasoning`, `error_signature`, `template_file`, `error_category`, `fix_description`, `compilation_result`, `links` |
| **FeatureUpdate** | `_mutate_feature_complete` (L895) | `id`, `type`, `timestamp`, `feature_name`, `loop`, `status`, `parameters`, `error_signature`, `template_file`, `error_category`, `fix_description`, `compilation_result`, `links` |
| **Elimination** | `_mutate_elimination` (L1502) | `id`, `type`, `timestamp`, `feature`, `boundary`, `observed`, `eliminates`, `survives`, `evidence_ref`, `probe`, `tier`, `error_signature`, `template_file`, `error_category`, `fix_description`, `compilation_result`, `links` |
| **SurpriseMoment** | `_mutate_surprise` (L1558) | `id`, `type`, `timestamp`, `context`, `expectation`, `reality`, `lesson_hint`, `source`, `consolidated`, `error_signature`, `template_file`, `error_category`, `fix_description`, `compilation_result`, `links` |
| **SimPlaytest** | `_mutate_simtest` (L1637) | `id`, `type`, `timestamp`, `observer`, `session`, `demo`, `beats_total`, `beats_reached`, `outcomes`, `timeline_path`, `temperature`, `error_signature`, `template_file`, `error_category`, `fix_description`, `compilation_result`, `links` |
| **ResearchDiscovery** | `_mutate_research_discovery` (L998) | `id`, `type`, `timestamp`, `feature`, `campus_sources`, `web_sources`, `corpus_sources`, `sources_consulted`, `parameters`, `acceptance_criteria`, `research_confidence`, `failure_sources`, `error_signature`, `template_file`, `error_category`, `fix_description`, `compilation_result`, `links` |
| **PlaytestObservation** | `_mutate_playtest` (L1596) | `id`, `type`, `timestamp`, `notes`, `build_ref`, `observer`, `error_signature`, `template_file`, `error_category`, `fix_description`, `compilation_result`, `links` |
| **PhaseComplete** | `_mutate_phase_complete` (L1403) | `id`, `type`, `timestamp`, `phase`, `result`, `notes`, `error_signature`, `template_file`, `error_category`, `fix_description`, `compilation_result`, `links` (+ optional: `phantom_pains`, `inheritance`, `pain_verdicts`, `backfilled`) |
| **Decomposition** | `_mutate_decomposition` (L1459) | `id`, `type`, `timestamp`, `target`, `kind`, `evidence`, `parts`, `error_signature`, `template_file`, `error_category`, `fix_description`, `compilation_result`, `links` |
| **Heuristic** | `_mutate_heuristic` (L1867) | `id`, `type`, `timestamp`, `signature`, `rule`, `organ`, `evidence_ids`, `approved_by`, `error_signature`, `template_file`, `error_category`, `fix_description`, `compilation_result`, `links` |
| **ProfessorGPA** | `_update_cumulative_gpa` (L1222) | `id`, `type`, `timestamp`, `scope`, `gpa`, `grades_count`, `trend`, `previous_gpa`, `date`, `error_signature`, `template_file`, `error_category`, `fix_description`, `compilation_result`, `links` |

---

## CONFIRMED MISMATCHES: Reader Reads Wrong Key

### **MISMATCH #1: history_book.py Line 107 — Observation node, feature_name vs feature**

| Property | Value |
|----------|-------|
| **File:Line** | `core/history_book.py:107` |
| **Node Type** | `Observation` |
| **Key Reader Tries** | `"feature"` (primary check), fallback `parameters.get("feature")` |
| **Key Writer Actually Emits** | `"feature_name"` (primary key at L1775) |
| **Silent Default** | Empty string `""` (never finds the key) |
| **Impact** | Observation entries in HISTORY_BOOK.md have blank feature names; the verdicts table can't be indexed by feature |
| **Confidence** | **CERTAIN** — _mutate_observation line 1775 explicitly writes `"feature_name": feature` |

**Code Evidence:**
```python
# Writer (graphify_interface.py:1775)
"feature_name": feature,

# Reader (history_book.py:107-111)
elif ntype == "Observation":
    feat = n.get("feature", (n.get("parameters") or {}).get("feature", ""))  # ← WRONG KEY
    verdict = n.get("verdict", (n.get("parameters") or {}).get("verdict", ""))
    notes = n.get("notes", (n.get("parameters") or {}).get("notes", ""))
    out.append(Entry(n["id"], "verdicts",
                     f"{feat}: {verdict}", str(notes)[:400],
                     feature=str(feat), when=ts))
```

**Fix Required:** Change line 107 to:
```python
feat = n.get("feature_name", (n.get("parameters") or {}).get("feature_name", ""))
```

---

## SAFE READERS: Keys Match Writers

### Observation nodes (type == "Observation")

| Reader | File:Line | Key | Writer Emits? | Status |
|--------|-----------|-----|---------------|--------|
| `n.get("verdict")` | heuristic_distiller.py:103 | `"verdict"` | ✓ YES (L1776) | SAFE |
| `n.get("feature_name")` | heuristic_distiller.py:105 | `"feature_name"` | ✓ YES (L1775) | SAFE |
| `n.get("notes")` | heuristic_distiller.py:106 | `"notes"` | ✓ YES (L1777) | SAFE |
| `n.get("feature_name")` | collapse_proxy.py:179 | `"feature_name"` | ✓ YES (L1775) | SAFE |
| `n.get("verdict")` | collapse_proxy.py:177 | `"verdict"` | ✓ YES (L1776) | SAFE |
| `n.get("feature_name")` | critic.py:113 | `"feature_name"` | ✓ YES (L1775) | SAFE |
| `n.get("derived_from")` | graphify_interface.py:921 | `"derived_from"` | ✓ YES (L1779) | SAFE |
| `n.get("notes")` | history_book.py:109 | `"notes"` | ✓ YES (L1777) | SAFE |

### ProfessorGrade nodes (type == "ProfessorGrade")

| Reader | File:Line | Key | Writer Emits? | Status |
|--------|-----------|-----|---------------|--------|
| `n.get("feature")` | gates.py:139 | `"feature"` | ✓ YES (L1200) | SAFE |
| `n.get("grade")` | gates.py:135, 149 | `"grade"` | ✓ YES (L1201) | SAFE |
| `n.get("feature")` | heuristic_distiller.py:124 | `"feature"` | ✓ YES (L1200) | SAFE |
| `n.get("grade")` | heuristic_distiller.py:123 | `"grade"` | ✓ YES (L1201) | SAFE |
| `n.get("feature")` | critic.py:106, 151 | `"feature"` | ✓ YES (L1200) | SAFE |
| `n.get("grade")` | critic.py:129, 156 | `"grade"` | ✓ YES (L1201) | SAFE |
| `n.get("grade")` | history_book.py:115 | `"grade"` | ✓ YES (L1201) | SAFE |
| `n.get("feature")` | history_book.py:114 | `"feature"` | ✓ YES (L1200) | SAFE |

### FeatureUpdate nodes (type == "FeatureUpdate")

| Reader | File:Line | Key | Writer Emits? | Status |
|--------|-----------|-----|---------------|--------|
| `n.get("feature_name")` | context_package.py:100 | `"feature_name"` | ✓ YES (L940) | SAFE |
| `n.get("status")` | preflight.py:434 | `"status"` | ✓ YES (L942) | SAFE |
| `n.get("loop")` | collect_observation_queue:1830 | `"loop"` | ✓ YES (L941) | SAFE |
| `n.get("status")` | graphify_interface.py:1822 | `"status"` | ✓ YES (L942) | SAFE |

### Elimination nodes (type == "Elimination")

| Reader | File:Line | Key | Writer Emits? | Status |
|--------|-----------|-----|---------------|--------|
| `n.get("feature")` | task_board.py:728 | `"feature"` | ✓ YES (L1522) | SAFE |
| `n.get("feature")` | history_book.py:97 | `"feature"` | ✓ YES (L1522) | SAFE |

### ResearchDiscovery nodes (type == "ResearchDiscovery")

| Reader | File:Line | Key | Writer Emits? | Status |
|--------|-----------|-----|---------------|--------|
| `n.get("feature")` | critic.py:116 | `"feature"` | ✓ YES (L1025) | SAFE |

### SimPlaytest nodes (type == "SimPlaytest")

| Reader | File:Line | Key | Writer Emits? | Status |
|--------|-----------|-----|---------------|--------|
| `o.get("features")` | collapse_proxy.py:73, 156 | `"features"` (in outcomes array) | ✓ YES (configured in outcomes) | SAFE |
| `n.get("outcomes")` | heuristic_distiller.py:109 | `"outcomes"` | ✓ YES (L1662) | SAFE |
| `n.get("error_signature")` | heuristic_distiller.py:107 | `"error_signature"` | ✓ YES (L1665) | SAFE |

### SurpriseMoment nodes (type == "SurpriseMoment")

| Reader | File:Line | Key | Writer Emits? | Status |
|--------|-----------|-----|---------------|--------|
| `n.get("context")` | critic.py:110, 131 | `"context"` | ✓ YES (L1578) | SAFE |
| `n.get("reality")` | critic.py:110, 131 | `"reality"` | ✓ YES (L1580) | SAFE |
| `n.get("context")` | graph_linker.py:169 | `"context"` | ✓ YES (L1578) | SAFE |
| `n.get("context")` | history_book.py:100 | `"context"` | ✓ YES (L1578) | SAFE |

---

## SUMMARY

- **Total Mismatches Found:** 1
- **Status:** Reader bug discovered, writer correct
- **Severity:** Medium — affects `HISTORY_BOOK.md` feature index; observation verdicts are logged but unindexed by feature
- **Root Cause:** history_book.py:107 assumes Observation nodes write `"feature"` key (as ProfessorGrade does), but Observation nodes write `"feature_name"` instead
- **Same Bug Class As Referenced:** Yes — this is exactly the pattern fixed in core/regression.py (line 62), which uses defensive fallback `node.get("feature_name", node.get("feature", "unknown"))` to tolerate the mismatch

**Regression Lesson:** The DNA graph contract requires writers and readers to agree on key names. When readers use fallback patterns (`.get("key1") or .get("key2")`), it masks mismatches and silently produces wrong data (here: blank feature names in the history book).

