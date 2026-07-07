"""One-command Pre-Flight — the Contract's mandatory session-start checks in one shot.

Usage:
    python -m core.preflight            (from E:/PythonChimera/Chimera)
    python core/preflight.py

Prints: graph health, GPA trend, spiral loop board (latest status per feature),
pending technical_research tasks, last pipeline run, environment reachability
(LM Studio / DNA API / Unreal Editor), and residual junk-node count.
"""
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

try:
    from core.graphify_interface import (load_dna_graph, graphify_query,
                                         collect_inheritance, collect_observation_queue)
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from graphify_interface import (load_dna_graph, graphify_query,
                                    collect_inheritance, collect_observation_queue)

LOOP_NAMES = {
    0: "The Player", 1: "The Ground", 2: "Basic Verbs", 3: "The Sky", 4: "Tools",
    5: "Other Dots", 6: "Shelter", 7: "Travel", 8: "Systems", 9: "The Universe",
}

DONE_STATUSES = {"verified", "encoded", "deferred", "observed"}
# 'verified' = system's eyes (preliminary measurement); 'observed' = human's eyes
# (the true collapse). Loops complete on 'verified' show [DONE*] until observed.
HUMAN_DONE_STATUSES = {"encoded", "deferred", "observed"}


def _http_ok(url, timeout=3):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def _ue_running():
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq UnrealEditor.exe"],
            capture_output=True, text=True, timeout=10,
        ).stdout
        return "UnrealEditor.exe" in out
    except Exception:
        return None  # unknown


def _latest_feature_statuses(nodes):
    """Latest FeatureUpdate status per feature name (by timestamp)."""
    latest = {}
    for n in nodes:
        if n.get("type") != "FeatureUpdate":
            continue
        name = n.get("feature_name")
        if not name or name == "unknown_feature":
            continue
        ts = n.get("timestamp", "")
        if name not in latest or ts > latest[name][0]:
            latest[name] = (ts, n.get("status", "?"), n.get("loop"))
    return latest


def main():
    dna = load_dna_graph()
    nodes = dna.get("nodes", [])

    print("=" * 64)
    print("CHIMERA PRE-FLIGHT")
    print("=" * 64)

    # 1. Graph health
    counts = {}
    for n in nodes:
        counts[n.get("type", "?")] = counts.get(n.get("type", "?"), 0) + 1
    top = sorted(counts.items(), key=lambda kv: -kv[1])[:8]
    print(f"\n[1] Graph health: {len(nodes)} nodes, {len(dna.get('edges', []))} edges")
    for t, c in top:
        print(f"    {t}: {c}")

    # 2. GPA + Build failure trend
    gpa = graphify_query("gpa", "trend") or {}
    print(f"\n[2] GPA: {gpa.get('gpa')}  trend: {gpa.get('trend')}  grades: {gpa.get('grades_count')}")

    # Build failure trend: analyze recent compilation results
    compilations = [n for n in nodes
                    if n.get("compilation_result") in ("pass", "fail")
                    and n.get("error_category") in ("none", "compilation_error")]
    recents = sorted(compilations, key=lambda n: n.get("timestamp", ""), reverse=True)[:20]
    recent_fails = [n for n in recents if n.get("compilation_result") == "fail"]
    recent_pass = [n for n in recents if n.get("compilation_result") == "pass"]
    if recents:
        fail_rate = len(recent_fails) / len(recents) * 100
        print(f"    Build trend (last {len(recents)}): {len(recent_pass)} pass, "
              f"{len(recent_fails)} fail ({fail_rate:.0f}% failure rate)")
        if recent_fails:
            # Extract unique error signatures from recent failures
            error_sigs = {}
            for n in recent_fails:
                sig = n.get("fix_description", n.get("error_signature", "unknown"))[:100]
                error_sigs[sig] = error_sigs.get(sig, 0) + 1
            top_errors = sorted(error_sigs.items(), key=lambda kv: -kv[1])[:3]
            if top_errors:
                print(f"    Most common errors:")
                for err, count in top_errors:
                    print(f"      - ({count}x) {err}")
                if fail_rate > 50:
                    print(f"    !! WARNING: Failure rate > 50% — investigate before proceeding")
    else:
        print(f"    Build trend: (no compilation records)")

    # Continuous verification health
    health_nodes = [n for n in nodes if n.get("type") == "Health"]
    if health_nodes:
        latest_health = sorted(health_nodes, key=lambda n: n.get("timestamp", ""), reverse=True)[0]
        hstatus = latest_health.get("status", "unknown")
        htime = str(latest_health.get("timestamp", ""))[:19]
        print(f"    Health: {hstatus} @ {htime}")
    else:
        print(f"    Health: no health checks recorded")

    # 3. Spiral loop board
    print("\n[3] Spiral loop board (ledger + latest FeatureUpdate):")
    ledger = {}  # loop -> [feature names]
    for n in nodes:
        if n.get("type") == "Feature" and n.get("spiral_loop", "").startswith("Loop"):
            try:
                loop_num = int(n["spiral_loop"].split()[-1])
            except (ValueError, IndexError):
                continue
            ledger.setdefault(loop_num, {})[n.get("name")] = n.get("status", "not_started")
    updates = _latest_feature_statuses(nodes)
    current_loop = None
    for loop_num in sorted(ledger):
        feats = ledger[loop_num]
        statuses = {}
        for fname, ledger_status in feats.items():
            status = updates.get(fname, (None, ledger_status))[1]
            statuses[fname] = status
        done = sum(1 for s in statuses.values() if s in DONE_STATUSES)
        open_feats = [f"{f}({s})" for f, s in statuses.items() if s not in DONE_STATUSES]
        human_done = sum(1 for s in statuses.values() if s in HUMAN_DONE_STATUSES)
        if done == len(feats):
            marker = "DONE" if human_done == len(feats) else "DONE*"
        else:
            marker = f"{done}/{len(feats)}"
        if open_feats and current_loop is None:
            current_loop = loop_num
        print(f"    Loop {loop_num} {LOOP_NAMES.get(loop_num, '?'):<14} [{marker}]"
              + (f"  open: {', '.join(open_feats[:4])}{' ...' if len(open_feats) > 4 else ''}" if open_feats else ""))
    if current_loop is not None:
        print(f"    -> NEXT: Loop {current_loop} ({LOOP_NAMES.get(current_loop)})")

    # 4. Pending technical_research
    pending = [n for n in nodes
               if n.get("feature_type") == "technical_research"
               and n.get("compilation_result") == "pending_discovery"]
    print(f"\n[4] Pending technical_research tasks: {len(pending)}")
    for n in pending[:5]:
        print(f"    - {n.get('target_action', n.get('id'))[:90]}")

    # 4.5. Generation Protocol inheritance — the Will + open phantom pains + dream report
    inh = collect_inheritance(nodes)
    pending_heuristics = 0
    pending_path = Path(__file__).parent.parent / "docs" / "PENDING_HEURISTICS.md"
    if pending_path.exists():
        import re as _re
        pending_heuristics = len(_re.findall(r"^- status: pending$",
                                             pending_path.read_text(encoding="utf-8"),
                                             _re.MULTILINE))
    obs_queue = collect_observation_queue(nodes)
    if inh["will"] or inh["open_pains"] or pending_heuristics or obs_queue:
        print("\n[4.5] Inheritance from the previous generation:")
        if pending_heuristics:
            print(f"    Dream Report: {pending_heuristics} candidate heuristic(s) awaiting "
                  f"Gardener approval (docs/PENDING_HEURISTICS.md)")
        if obs_queue:
            print(f"    Observation queue: {len(obs_queue)} system-finalized feature(s) "
                  f"awaiting the human's eyes — the true collapse")
            print(f"      (record: python -m core.graphify_record observe --feature X "
                  f"--verdict accepted|rejected --notes ... --loop N)")
            for q in obs_queue[:6]:
                hint = f"  {q['grade_hint']}" if q["grade_hint"] else ""
                shots = f"  [{q['evidence_hint']}]" if q["evidence_hint"] else ""
                print(f"      Loop {q['loop']} {q['feature']}{hint}{shots}")
            if len(obs_queue) > 6:
                print(f"      ... and {len(obs_queue) - 6} more")
        if inh["will"]:
            print(f"    Will ({inh['will']['timestamp'][:19]} — {inh['will']['phase'][:50]}):")
            print(f"      {inh['will']['inheritance'][:300]}")
        if inh["open_pains"]:
            print(f"    Open phantom pains ({len(inh['open_pains'])}) — confirm or refute this "
                  f"session (postflight --pain-verdict):")
            for p in inh["open_pains"][:5]:
                flag = " [still-open]" if p.get("still_open") else ""
                print(f"      {p['id']}  [{p['age_days']}d]{flag}  {p['text'][:80]}")
            stale = [p for p in inh["open_pains"] if p["age_days"] >= 14]
            if stale:
                print(f"    !! {len(stale)} pain(s) >= 14 days old — the 2-week horizon has "
                      f"arrived; disposition them this session.")

    # 5. Last pipeline run
    def latest(pred):
        cands = [n for n in nodes if pred(n)]
        return max(cands, key=lambda n: n.get("timestamp", "")) if cands else None

    last_parse = latest(lambda n: str(n.get("template_file", "")).startswith("dsl_parse"))
    last_build = latest(lambda n: n.get("compilation_result") in ("pass", "fail", "error")
                        and (n.get("error_category") == "compilation_error"
                             or n.get("fix_description") == "build_completed"
                             or "ubt_output_excerpt" in n))
    last_visual = latest(lambda n: n.get("template_file") == "visual_verification/screenshot_analysis")

    # 4.6. Sleepwalker / Rehearsal — the automation half of the balance
    last_sim = latest(lambda n: n.get("type") == "SimPlaytest")
    last_roll = latest(lambda n: n.get("type") == "SimulationRollout")
    if last_sim or last_roll:
        print("\n[4.6] Sleepwalker (agent-sim; the human's word overrides everything here):")
        if last_sim:
            print(f"    Last sleepwalk: {last_sim.get('session')} — "
                  f"{last_sim.get('beats_reached')}/{last_sim.get('beats_total')} beats "
                  f"({last_sim.get('demo')}) @ {str(last_sim.get('timestamp',''))[:19]}")
            print(f"      {str(last_sim.get('temperature',''))[:100]}")
        if last_roll:
            print(f"    Last rehearsal decision: {last_roll.get('chosen')} "
                  f"@ {str(last_roll.get('timestamp',''))[:19]}"
                  f"{'  [VETOED]' if last_roll.get('vetoed') else ''}")

    print("\n[5] Last pipeline run:")
    for label, n in (("parse", last_parse), ("build", last_build), ("visual", last_visual)):
        if n:
            print(f"    {label}: {n.get('compilation_result')} @ {n.get('timestamp', '')[:19]}"
                  f" — {str(n.get('fix_description', ''))[:70]}")
        else:
            print(f"    {label}: (none recorded)")

    # 6. Environment
    lm = _http_ok("http://localhost:1234/v1/models")
    dna_api = _http_ok("http://localhost:8766/dna/health")
    ue = _ue_running()
    print("\n[6] Environment:")
    print(f"    LM Studio (localhost:1234): {'UP' if lm else 'DOWN — Professor Review must be deferred'}")
    print(f"    DNA API   (localhost:8766): {'UP' if dna_api else 'down (optional)'}")
    print(f"    Unreal Editor process:      {'RUNNING' if ue else ('NOT RUNNING' if ue is not None else 'unknown')}")

    # 7. Residual junk
    junk = [n for n in nodes if n.get("feature_name") == "unknown_feature"
            or (n.get("tool") == "unknown_tool" and n.get("action") == "unknown_action")]
    print(f"\n[7] Junk nodes remaining: {len(junk)}"
          + ("  -> run: python fix_dna_key_mismatch_pollution.py" if junk else "  (clean)"))

    # MANDATORY GATE: critical violations return exit code 1
    # This makes `python -m core.preflight && python pipeline.py` impossible
    # if pre-flight conditions aren't met.
    critical_violations = []

    # Check 1: Junk nodes must be zero
    if gpa.get("gpa") is not None and gpa.get("gpa") < 1.0:
        critical_violations.append("GPA critically low")

    # Check 2: Junk nodes (reported in [7])
    junk = [n for n in nodes if n.get("feature_name") == "unknown_feature"
            or (n.get("tool") == "unknown_tool" and n.get("action") == "unknown_action")]
    if junk:
        critical_violations.append("Junk nodes must be cleaned first")

    # Check 3: Build failure rate check (from [2] trend)
    compilations = [n for n in nodes
                    if n.get("compilation_result") in ("pass", "fail")
                    and n.get("error_category") in ("none", "compilation_error")]
    recents = sorted(compilations, key=lambda n: n.get("timestamp", ""), reverse=True)[:10]
    recent_fails = [n for n in recents if n.get("compilation_result") == "fail"]
    if len(recents) >= 3 and len(recent_fails) > len(recents) * 0.5:
        critical_violations.append(f"Build failure rate > 50% in last {len(recents)} runs")

    if critical_violations:
        print(f"\n!! {len(critical_violations)} CRITICAL VIOLATION(S):")
        for v in critical_violations:
            print(f"   - {v}")
        print("!! Pre-Flight FAILED — resolve violations before proceeding.")
        return 1

    print("\nPre-Flight complete. All gates pass.")
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
