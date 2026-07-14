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
# 'verified' = system's preliminary measurement; 'observed' = automated observation (sleepwalker/telemetry) — the true collapse. Loops complete on 'verified' show [DONE*] until observed_provisional or observed.
AUTOMATED_DONE_STATUSES = {"encoded", "deferred", "observed", "observed_provisional"}


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
    """Latest FeatureUpdate status per feature name (by timestamp).

    Backfilled re-records (``backfilled: true``) carry the timestamp of the
    repair RUN, not of the work they describe, so a re-run of the pollution
    fixer can stamp 2026-07-05-era statuses with today's date and shadow every
    genuine status recorded since (observed 2026-07-11: Player_Character_Animation
    showed 'blocked' over a real 'verified'; Verb_Shovel showed 'verified' over a
    real 'needs_refinement'). A live-recorded update therefore always outranks a
    backfilled one; backfilled statuses are used only for features that have no
    live-recorded update at all.
    """
    latest = {}
    for n in nodes:
        if n.get("type") != "FeatureUpdate":
            continue
        name = n.get("feature_name")
        if not name or name == "unknown_feature":
            continue
        ts = n.get("timestamp", "")
        rank = (not bool(n.get("backfilled")), ts)  # live-recorded first, then newest
        if name not in latest or rank > latest[name][0]:
            latest[name] = (rank, n.get("status", "?"), n.get("loop"))
    return latest


def _compute_gpa_trend(nodes: list) -> dict:
    """Fast inline GPA trend computation (replaces graphify_query call).
    Eliminates redundant graph load. Scope='trend' path inlined for speed."""
    gpa_nodes = [n for n in nodes if n.get("type") == "ProfessorGrade"]
    overall_nodes = [n for n in nodes if n.get("type") == "ProfessorGPA" and n.get("scope") == "project_overall"]

    if not overall_nodes and not gpa_nodes:
        return {"scope": "trend", "gpa": None, "trend": "flat", "message": "No GPA data recorded yet"}

    # Compute current GPA
    if overall_nodes:
        latest_overall = sorted(overall_nodes, key=lambda x: x.get("timestamp", ""), reverse=True)[0]
        current_gpa = latest_overall.get("gpa")
    else:
        recent_grades = [g for g in sorted(gpa_nodes, key=lambda x: x.get("timestamp", ""), reverse=True)[:10]
                         if g.get("feature") != "Build_Pipeline"]
        if recent_grades:
            scores = [g.get("score", 0) for g in recent_grades]
            current_gpa = sum(scores) / len(scores)
        else:
            current_gpa = None

    # Trend from overall nodes
    sorted_overall = sorted(overall_nodes, key=lambda x: x.get("timestamp", ""), reverse=True)
    trend = "flat"
    if len(sorted_overall) >= 2:
        prev_gpa = sorted_overall[1].get("gpa", 0)
        curr_gpa = sorted_overall[0].get("gpa", 0)
        if curr_gpa > prev_gpa + 0.05:
            trend = "rising"
        elif curr_gpa < prev_gpa - 0.05:
            trend = "falling"

    return {
        "scope": "trend",
        "gpa": current_gpa,
        "trend": trend,
        "grades_count": len(set(g.get("feature") for g in gpa_nodes))
    }


def main():
    dna = load_dna_graph()
    nodes = dna.get("nodes", [])

    print("=" * 64)
    print("CHIMERA PRE-FLIGHT")
    print("=" * 64)

    # CAPCOM — the operator channel (agent-agnostic push feed, core/capcom.py).
    # Surfaced FIRST so the freshest pushed state — unpushed work, build/verdict
    # signals, the human's OPERATOR_INBOX notes — leads the brief instead of
    # waiting for the agent to pull it. Ingests the inbox as a side effect.
    try:
        from core.capcom import signals_block
        _capcom = signals_block(limit=8)
        if _capcom:
            print("\n" + _capcom)
    except Exception as e:
        print(f"\n[CAPCOM] operator channel unavailable ({e})")

    # Research pulse — surface whether the mandated research is actually happening.
    # The Research Gate at postflight asks for sources or a reasoned waiver; this
    # makes the absence visible at session START, not only caught at the end.
    try:
        from core.research_gate import recent_research
        _rr = recent_research(nodes, hours=12)
        if _rr:
            print(f"\n[research] {len(_rr)} research node(s) recorded in the last 12h")
        else:
            print("\n[research] none in 12h — the Research Depth Protocol covers technical/infra "
                  "decisions too; postflight will require --researched sources or a --research-waiver")
    except Exception:
        pass

    # Generator-owned guard — fast, LM-FREE heads-up: dirty files that look
    # generator-owned get CLOBBERED on the next pipeline run. Postflight does the
    # authoritative LM judgment; this just surfaces the risk at session start.
    try:
        from core.generator_guard import deterministic_flags
        _gf = deterministic_flags()
        if _gf:
            print(f"\n[generator-guard] {len(_gf)} dirty file(s) look GENERATOR-OWNED — "
                  f"hand-edits get clobbered; fix core/game_code_generator.py, not the C++:")
            for _p in _gf[:6]:
                print(f"    x {_p}")
    except Exception:
        pass

    # 0. Circadian — the studio reads its OWN clock (no OS scheduler). This is
    # the qualification: system time determines the phase, and whether a night
    # is due. A 24/7 agent should honor the directive each cycle.
    try:
        from core.circadian import preflight_line
        print("\n" + preflight_line())
    except Exception as e:
        print(f"\n[0] Circadian: unavailable ({e})")

    # 0.7 Helm — the hand on the wheel: seed (CHIMERA_VISION.py) - state = the
    # gap; the helm turns it into this cycle's heading. The agent should work
    # the recommended focus unless it has a sharper reason.
    try:
        from core.helm import preflight_line as _helm_line
        print("\n" + _helm_line())
    except Exception as e:
        print(f"\n[0.7] Helm: unavailable ({e})")

    # 1. Graph health
    counts = {}
    for n in nodes:
        counts[n.get("type", "?")] = counts.get(n.get("type", "?"), 0) + 1
    top = sorted(counts.items(), key=lambda kv: -kv[1])[:8]
    print(f"\n[1] Graph health: {len(nodes)} nodes, {len(dna.get('edges', []))} edges")
    for t, c in top:
        print(f"    {t}: {c}")

    # 2. GPA + Build failure trend (OPTIMIZED: inline computation, no graph reload)
    gpa = _compute_gpa_trend(nodes)
    print(f"\n[2] GPA: {gpa.get('gpa')}  trend: {gpa.get('trend')}  grades: {gpa.get('grades_count')}")

    # Build failure trend: analyze recent compilation results (CACHED for reuse below)
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
        automated_done = sum(1 for s in statuses.values() if s in AUTOMATED_DONE_STATUSES)
        if done == len(feats):
            marker = "DONE" if automated_done == len(feats) else "DONE*"
        else:
            marker = f"{done}/{len(feats)}"
        if open_feats and current_loop is None:
            current_loop = loop_num
        print(f"    Loop {loop_num} {LOOP_NAMES.get(loop_num, '?'):<14} [{marker}]"
              + (f"  open: {', '.join(open_feats[:4])}{' ...' if len(open_feats) > 4 else ''}" if open_feats else ""))
    if current_loop is not None:
        print(f"    -> NEXT: Loop {current_loop} ({LOOP_NAMES.get(current_loop)})")

    # 3.7. Parallel task board — what concurrent agents can claim RIGHT NOW
    try:
        from core.task_board import board_summary
        s = board_summary()
        if s["total"]:
            counts = "  ".join(f"{k}:{v}" for k, v in sorted(s["counts"].items()))
            print(f"\n[3.7] Task board: {s['total']} task(s)  {counts}")
            print(f"    Parallel frontier: {len(s['frontier'])} task(s) can proceed simultaneously")
            for t in s["frontier"][:3]:
                cap = " `capable`" if t.get("capable_only") else ""
                print(f"      - {t['id']} p={t.get('priority', 1):.2g} {t['title'][:70]}{cap}")
            for tid, title, agent in s["claims"][:4]:
                print(f"    claimed: {tid} {title[:56]} <- {agent}")
            print(f"    ENTER HERE: python -m core.task_board claim --agent <your-id>  "
                  f"(opens tunnel: editor + work packet; exit only with evidence)")
            try:
                from core.gauntlet import load_credentials
                creds = load_credentials()
                journeymen = [a for a, e in creds.items()
                              if "journeyman" in (e.get("roles") or [])]
                print(f"    gauntlet: {len(journeymen)} journeyman agent(s) qualified for "
                      f"capable lanes; qualify: python -m core.gauntlet enter --agent <id>")
            except Exception:
                pass
            try:
                from core.curriculum import load_curriculum, band_progress, \
                    _load_transcript, GAUNTLET_DIR as _GD
                bands = load_curriculum()
                enrolled = sorted((_GD / "features").glob("*/transcript.json"))
                if enrolled:
                    print(f"    school: {len(enrolled)} feature(s) enrolled "
                          f"(K->PhD, {sum(len(c['checkpoints']) for b in bands for c in b['courses'])} checkpoints):")
                    for tp in enrolled[:4]:
                        import json as _json
                        tr = _json.loads(tp.read_text(encoding="utf-8"))
                        band, remaining = band_progress(tr, bands)
                        grade = "PhD" if band is None else \
                            f"{band['band']} ({len(remaining)} left)"
                        print(f"      {tr['feature']}: {grade}")
            except Exception:
                pass
            try:
                from core.agent_tunnel import active_sessions
                for sess in active_sessions()[:4]:
                    print(f"    tunnel: {sess['agent']} in {sess['task_id']} "
                          f"since {sess['entered_at'][11:16]}Z")
            except Exception:
                pass
    except Exception as e:
        print(f"\n[3.7] Task board: unavailable ({e})")

    # 3.8. The fractal spiral — the whole structure as a DNA spiral around the
    # player (trunk). Self-similar golden-angle layout; the pattern is the linker.
    try:
        from core.fractal_spiral import build as _spiral
        sp = _spiral()
        depths = sp["counts_by_depth"]
        print(f"\n[3.8] Fractal spiral: {len(sp['nodes'])} nodes around the player "
              f"(trunk); golden angle {sp['golden_angle_deg']}°")
        print(f"    self-similar depth profile {depths}  "
              f"(player -> loops -> features -> exams -> checkpoints)")
        print(f"    render: python -m core.fractal_spiral build --svg   "
              f"link a node: python -m core.fractal_spiral neighborhood --node <id>")
    except Exception as e:
        print(f"\n[3.8] Fractal spiral: unavailable ({e})")

    # 3.9. Rep ledger — resolution through repetition (the dog-sit threshold).
    # A feature earns collapse eligibility by ACCUMULATED constraint reps
    # (>=200 with a >=95% 8-run streak), not by one good night.
    try:
        from core.rep_engine import status_lines, all_battery_features
        feats = all_battery_features()
        if feats:
            print(f"\n[3.9] Rep ledger ({len(feats)} batteries; "
                  f"resolution = reps x constraints):")
            for line in status_lines(limit=8):
                print(f"    {line}")
            print("    run a pass: python -m core.rep_engine tend   "
                  "gate check: python -m core.rep_engine gate --feature <X>")
        else:
            print("\n[3.9] Rep ledger: no batteries yet -> "
                  "python -m core.rep_engine build")
    except Exception as e:
        print(f"\n[3.9] Rep ledger: unavailable ({e})")

    # 3.95. The History Book — everything learned, searchable.
    try:
        from core.history_book import stats as _book_stats, CHAPTERS as _book_chapters
        counts = _book_stats()
        total = sum(counts.values())
        print(f"\n[3.95] History Book: {total} entries / {len(counts)} chapters "
              f"(docs/HISTORY_BOOK.md, rewritten nightly)")
        print("    search it: python -m core.history_book search --query <anything> "
              "[--chapter closed-doors]")
    except Exception as e:
        print(f"\n[3.95] History Book: unavailable ({e})")

    # 3.96. The Container (core.malcolm) — the edge-of-chaos gauge: every
    # wall's pressure, drawn each morning. Breaches gate; floors advise.
    try:
        from core.malcolm import status as _malcolm_status
        rows = _malcolm_status()
        interesting = [r for r in rows if r["state"] != "UNMEASURED"]
        unmeasured = sum(1 for r in rows if r["state"] == "UNMEASURED")
        print(f"\n[3.96] The Container ({len(rows)} walls, {unmeasured} awaiting sensors):")
        for r in interesting[:9]:
            val = "—" if r["value"] is None else (
                f"{r['value']:.1f}" if isinstance(r["value"], float) else str(r["value"]))
            print(f"    {r['state']:>11}  {r['axis']:<32} {val:>9} {r['band']:>14} {r['pct']:>7}")
        pend = []
        try:
            from core.malcolm import load_envelope
            pend = [p for p in load_envelope().get("pending_adjustments", [])
                    if p.get("status") == "pending"]
        except Exception:
            pass
        if pend:
            print(f"    {len(pend)} pending wall adjustment(s) awaiting a ruling "
                  f"(docs/envelope.json)")
        print("    gauge: python -m core.malcolm status   breath: python -m core.malcolm tune")
    except Exception as e:
        print(f"\n[3.96] The Container: unavailable ({e})")

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
                  f"awaiting automated observation — the true collapse")
            print(f"      (record: python -m core.graphify_record observe --feature X "
                  f"--verdict accepted|rejected --notes ... --loop N --derived-from <simtest_id>)")
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

    # 4.55. Demo level integrity — the template-stamp clobber fingerprint
    import hashlib as _hl
    TEMPLATE_MD5 = "B734CFF5B6D6343B7A2BCCA43A1CB756"  # templates/DefaultLevel.umap bytes
    yard = Path(__file__).parent.parent / "Content" / "Levels" / "chimeradefaultlevel.umap"
    if yard.exists():
        cur = _hl.md5(yard.read_bytes()).hexdigest().upper()
        if cur == TEMPLATE_MD5:
            print(f"\n[4.55] !! DEMO LEVEL CLOBBERED to template — restore: copy "
                  f"Content/Levels/L_RegolithYard.umap over chimeradefaultlevel.umap "
                  "(editor closed), relaunch. Root-cause guard lives in build_orchestrator.")

    # 4.6. Sleepwalker / Rehearsal — the automation half of the balance
    last_sim = latest(lambda n: n.get("type") == "SimPlaytest")
    last_roll = latest(lambda n: n.get("type") == "SimulationRollout")
    if last_sim or last_roll:
        print("\n[4.6] Sleepwalker (fully automated verification; machine signals are final in the distiller):")
        if last_sim:
            print(f"    Last sleepwalk: {last_sim.get('session')} — "
                  f"{last_sim.get('beats_reached')}/{last_sim.get('beats_total')} beats "
                  f"({last_sim.get('demo')}) @ {str(last_sim.get('timestamp',''))[:19]}")
            print(f"      {str(last_sim.get('temperature',''))[:100]}")
        prov = {n.get("feature_name") for n in nodes
                if n.get("type") == "FeatureUpdate" and n.get("status") in {"observed_provisional", "observed"}}
        if prov:
            print(f"    Collapsed by automated simulation evidence: {len(prov)}")
        if last_roll:
            print(f"    Last rehearsal decision: {last_roll.get('chosen')} "
                  f"@ {str(last_roll.get('timestamp',''))[:19]}"
                  f"{'  [VETOED]' if last_roll.get('vetoed') else ''}")

    # 4.7. The Critic — ADVISORY ONLY comparative-enjoyment estimate (never a gate)
    last_critic = latest(lambda n: n.get("type") == "CriticJudgment")
    if last_critic:
        top_titles = [t.get("title") for t in (last_critic.get("benchmark_titles") or [])
                     if isinstance(t, dict) and t.get("title")]
        print(f"\n[4.7] The Critic (ADVISORY ONLY — does not gate the pipeline): "
              f"{last_critic.get('feature')} ~ {last_critic.get('overall_percentage')}% "
              f"vs {top_titles[0] if top_titles else '?'} "
              f"@ {str(last_critic.get('timestamp',''))[:19]}")

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

    # 7. Residual junk (CACHED: computed once at start, reused here and below in gate checks)
    junk = [n for n in nodes if n.get("feature_name") == "unknown_feature"
            or (n.get("tool") == "unknown_tool" and n.get("action") == "unknown_action")]
    print(f"\n[7] Junk nodes remaining: {len(junk)}"
          + ("  -> run: python fix_dna_key_mismatch_pollution.py" if junk else "  (clean)"))

    # MANDATORY GATE: critical violations return exit code 1
    # This makes `python -m core.preflight && python pipeline.py` impossible
    # if pre-flight conditions aren't met.
    critical_violations = []

    # Check 1: GPA critically low
    if gpa.get("gpa") is not None and gpa.get("gpa") < 1.0:
        critical_violations.append("GPA critically low")

    # Check 2: Junk nodes (REUSING cached junk list — no re-filter)
    if junk:
        critical_violations.append("Junk nodes must be cleaned first")

    # Check 3: Build failure rate check (REUSING cached compilations — no re-filter)
    recents_for_gate = sorted(compilations, key=lambda n: n.get("timestamp", ""), reverse=True)[:10]
    recent_fails_for_gate = [n for n in recents_for_gate if n.get("compilation_result") == "fail"]
    if len(recents_for_gate) >= 3 and len(recent_fails_for_gate) > len(recents_for_gate) * 0.5:
        critical_violations.append(f"Build failure rate > 50% in last {len(recents_for_gate)} runs")

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
