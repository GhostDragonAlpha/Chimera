"""One-command Post-Flight — records the Contract's end-of-phase results.

Usage:
    python -m core.postflight --phase "Loop 8 System_Economy apply" --result "UBT pass" \
        [--notes "..."] [--feature System_Economy --loop 8 --status verified]

Records a PhaseComplete node (plus an optional FeatureUpdate), then prints the
GPA trend and the Post-Flight checklist so nothing gets skipped.
"""
import argparse
import subprocess
import sys
from pathlib import Path

try:
    from core.graphify_interface import (graphify_query, record_phase, record_feature,
                                         parse_pain_verdicts, load_dna_graph,
                                         collect_inheritance)
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from graphify_interface import (graphify_query, record_phase, record_feature,
                                    parse_pain_verdicts, load_dna_graph,
                                    collect_inheritance)


def main():
    parser = argparse.ArgumentParser(description="Record Post-Flight results to the DNA graph")
    parser.add_argument("--phase", required=True, help="Phase name, e.g. 'Loop 8 System_Economy apply'")
    parser.add_argument("--result", required=True, help="What happened, verbatim where possible")
    parser.add_argument("--notes", default="", help="Extra context")
    parser.add_argument("--feature", help="Optionally also update a Feature Ledger entry")
    parser.add_argument("--loop", type=int, help="Loop number for --feature")
    parser.add_argument("--status", help="Status for --feature (researching/applying/verified/encoded/blocked)")
    parser.add_argument("--phantom-pain", action="append", dest="phantom_pain",
                        help="Generation Protocol: predicted failure point the next session must "
                             "confirm/refute (repeatable, <=5, aim for 3 sharp ones)")
    parser.add_argument("--inheritance", default="",
                        help="Generation Protocol: the Will — <=3 sentences on what this session "
                             "sacrificed itself to teach")
    parser.add_argument("--pain-verdict", action="append", dest="pain_verdict",
                        help="Disposition an inherited pain: "
                             "'<phase_node_id>:P<n>:confirmed|refuted|still-open' (repeatable)")
    parser.add_argument("--eliminated", action="append", dest="eliminated",
                        help="Inversion record, the pain's proven twin: "
                             "'<feature> : <boundary now PROVEN wrong> : <evidence ref>' "
                             "(repeatable; becomes an Elimination node + narrows the "
                             "next agent's search space)")
    parser.add_argument("--researched", default="",
                        help="Research Gate: what you looked up + sources/URLs this session "
                             "(satisfies the gate — covers technical/infra research, not just assets)")
    parser.add_argument("--research-waiver", default="", dest="research_waiver",
                        help="Research Gate: a reasoned waiver when this change genuinely needed "
                             "no external research (recorded + auditable; a silent skip is refused)")
    parser.add_argument("--generator-waiver", default="", dest="generator_waiver",
                        help="Generator Guard: reasoned waiver when a generator-owned C++ edit is "
                             "intentional (e.g. migrating a loop-built file to generator ownership)")
    parser.add_argument("--witnessed", default="",
                        help="Witness Gate: what you observed in PIE + the simtest/telemetry id "
                             "(satisfies the gate when marking a feature verified/observed)")
    parser.add_argument("--witness-waiver", default="", dest="witness_waiver",
                        help="Witness Gate: reasoned waiver when a witness genuinely doesn't apply")
    parser.add_argument("--visual-analysis", default="",
                        help="Visual Gate: the LM screenshot analysis (what the model saw + "
                             "VERIFIED/NEEDS_REFINEMENT + shot path) when marking a feature verified")
    parser.add_argument("--visual-waiver", default="", dest="visual_waiver",
                        help="Visual Gate: reasoned waiver (non-visual feature, or editor/bridge down)")
    args = parser.parse_args()

    # Research Gate — the mandated research must be EXPLICIT, not silently skipped
    # (2026-07-13). Evidence recorded this session OR --researched sails through;
    # otherwise a reasoned --research-waiver proceeds; a bare skip is refused (like
    # bare 'blocked'). Agent-agnostic: any harness running postflight inherits it.
    try:
        from core.research_gate import check as _rg_check, enforced as _rg_enforced, GUIDANCE as _rg_guide
        _rg_nodes = load_dna_graph().get("nodes", [])
        _rg_status, _rg_detail = _rg_check(
            _rg_nodes, researched=getattr(args, "researched", "") or "",
            waiver=getattr(args, "research_waiver", "") or "")
        if _rg_status == "missing" and _rg_enforced():
            print("\n!! RESEARCH GATE - refused: this postflight records work but no research is evident.")
            print(_rg_guide)
            try:
                from core.graphify_interface import record_surprise as _rg_rs
                _rg_rs(context=f"postflight refused by research gate: {args.phase[:80]}",
                       reality="no research recorded this session; postflight blocked",
                       expectation="Research Depth Protocol requires research (incl. technical/infra) before shipping",
                       source="agent")
            except Exception:
                pass
            try:
                from core.capcom import post_safe as _rg_ps
                _rg_ps("research", f"postflight BLOCKED (no research): {args.phase[:64]}",
                       level="warn", source="research-gate")
            except Exception:
                pass
            raise SystemExit(1)
        if _rg_status == "missing":
            print(f"\n[Research Gate] WARN (not enforced): {_rg_detail}")
        else:
            print(f"\n[Research Gate] {_rg_status}: {_rg_detail[:110]}")
            if _rg_status == "waived":
                try:
                    from core.graphify_interface import record_surprise as _rg_rs
                    _rg_rs(context=f"research waived: {args.phase[:70]}",
                           reality=_rg_detail[:200],
                           expectation="research per Research Depth Protocol",
                           source="agent")
                except Exception:
                    pass
                try:
                    from core.capcom import post_safe as _rg_ps
                    _rg_ps("research", f"research WAIVED: {args.phase[:52]} - {_rg_detail[:52]}",
                           level="note", source="research-gate")
                except Exception:
                    pass
            elif _rg_status == "provided":
                try:
                    from core.graphify_interface import record_research as _rg_rr
                    _rg_rr(args.feature or args.phase[:60], web_sources=[_rg_detail[:300]])
                except Exception:
                    pass
    except SystemExit:
        raise
    except Exception as _rg_e:
        print(f"[Research Gate] unavailable ({_rg_e}) — passing open")

    # Generator Guard — refuse to record a session that hand-edited generator-owned
    # C++ (it'll be silently clobbered on the next pipeline run) unless explicitly
    # waived. LM-judged (may take a minute on the local model — only fires when
    # generated files are dirty and the generator itself wasn't changed).
    try:
        from core.generator_guard import (check as _gg_check, enforced as _gg_enforced,
                                           format_violations as _gg_fmt)
        _gg_viol = _gg_check()
        if _gg_viol:
            print(f"\n!! GENERATOR GUARD - {len(_gg_viol)} hand-edit(s) to generator-owned "
                  f"C++ (clobbered on the next pipeline run):")
            print(_gg_fmt(_gg_viol))
            _gg_waiver = (getattr(args, "generator_waiver", "") or "").strip()
            if _gg_enforced() and not _gg_waiver:
                print("Fix the generator template in core/game_code_generator.py, not the C++. "
                      "If intentional (e.g. migrating a file to generator ownership), pass "
                      "--generator-waiver \"<reason>\".")
                try:
                    from core.graphify_interface import record_surprise as _gg_rs
                    _gg_rs(context=f"postflight refused by generator guard: {args.phase[:70]}",
                           reality=f"{len(_gg_viol)} hand-edit(s) to generator-owned C++: "
                                   + ", ".join(v['path'].split('/')[-1] for v in _gg_viol[:6]),
                           expectation="fix the generator template, never the generated C++",
                           source="agent")
                except Exception:
                    pass
                try:
                    from core.capcom import post_safe as _gg_ps
                    _gg_ps("generator-guard", f"postflight BLOCKED: {len(_gg_viol)} hand-edit(s) "
                           f"to generator-owned C++ ({args.phase[:44]})",
                           level="warn", source="generator-guard")
                except Exception:
                    pass
                raise SystemExit(1)
            if _gg_waiver:
                print(f"[Generator Guard] WAIVED: {_gg_waiver[:100]}")
                try:
                    from core.capcom import post_safe as _gg_ps
                    _gg_ps("generator-guard", f"generator hand-edit WAIVED: {_gg_waiver[:60]}",
                           level="note", source="generator-guard")
                except Exception:
                    pass
    except SystemExit:
        raise
    except Exception as _gg_e:
        print(f"[Generator Guard] unavailable ({_gg_e}) — passing open")

    # Witness Gate — a feature can't be recorded verified/observed on a compile
    # alone (H-14: a compile is not proof). Requires witness evidence this session
    # (SimPlaytest/telemetry/observation), --witnessed, or a reasoned
    # --witness-waiver. Only fires on a verify/observe transition.
    if args.feature and args.status in {"verified", "observed", "observed_provisional"}:
        try:
            from core.witness_gate import check as _wg_check, enforced as _wg_enforced, GUIDANCE as _wg_guide
            _wg_nodes = load_dna_graph().get("nodes", [])
            _wg_status, _wg_detail = _wg_check(
                _wg_nodes, status=args.status,
                witnessed=getattr(args, "witnessed", "") or "",
                waiver=getattr(args, "witness_waiver", "") or "")
            if _wg_status == "missing" and _wg_enforced():
                print(f"\n!! WITNESS GATE - refused: marking {args.feature} '{args.status}' with no witness.")
                print(_wg_guide)
                try:
                    from core.graphify_interface import record_surprise as _wg_rs
                    _wg_rs(context=f"postflight refused by witness gate: {args.feature} -> {args.status}",
                           reality="no SimPlaytest/telemetry/observation evidence this session",
                           expectation="H-14: a compile is not proof; witness the feature before verifying",
                           source="agent")
                except Exception:
                    pass
                try:
                    from core.capcom import post_safe as _wg_ps
                    _wg_ps("witness", f"postflight BLOCKED: {args.feature} marked {args.status} with no witness",
                           level="warn", source="witness-gate")
                except Exception:
                    pass
                raise SystemExit(1)
            print(f"[Witness Gate] {_wg_status}: {_wg_detail[:110]}")
            if _wg_status == "waived":
                try:
                    from core.capcom import post_safe as _wg_ps
                    _wg_ps("witness", f"witness WAIVED: {args.feature} {args.status} - {_wg_detail[:48]}",
                           level="note", source="witness-gate")
                except Exception:
                    pass
        except SystemExit:
            raise
        except Exception as _wg_e:
            print(f"[Witness Gate] unavailable ({_wg_e}) — passing open")

        # Visual Gate — the local model must have LOOKED at a verified feature: a
        # feature can't be marked verified/observed without a recorded LM screenshot
        # analysis this session, --visual-analysis, or a reasoned --visual-waiver.
        try:
            from core.visual_gate import check as _vg_check, enforced as _vg_enforced, GUIDANCE as _vg_guide
            _vg_nodes = load_dna_graph().get("nodes", [])
            _vg_status, _vg_detail = _vg_check(
                _vg_nodes, status=args.status,
                analysis=getattr(args, "visual_analysis", "") or "",
                waiver=getattr(args, "visual_waiver", "") or "")
            if _vg_status == "missing" and _vg_enforced():
                print(f"\n!! VISUAL GATE - refused: marking {args.feature} '{args.status}' with no LM screenshot analysis.")
                print(_vg_guide)
                try:
                    from core.graphify_interface import record_surprise as _vg_rs
                    _vg_rs(context=f"postflight refused by visual gate: {args.feature} -> {args.status}",
                           reality="no LM screenshot analysis on record this session",
                           expectation="the local model must LOOK at a verified feature (viewport screenshot analysis)",
                           source="agent")
                except Exception:
                    pass
                try:
                    from core.capcom import post_safe as _vg_ps
                    _vg_ps("visual", f"postflight BLOCKED: {args.feature} marked {args.status} with no LM screenshot analysis",
                           level="warn", source="visual-gate")
                except Exception:
                    pass
                raise SystemExit(1)
            print(f"[Visual Gate] {_vg_status}: {_vg_detail[:110]}")
            if _vg_status == "waived":
                try:
                    from core.capcom import post_safe as _vg_ps
                    _vg_ps("visual", f"visual analysis WAIVED: {args.feature} {args.status} - {_vg_detail[:44]}",
                           level="note", source="visual-gate")
                except Exception:
                    pass
        except SystemExit:
            raise
        except Exception as _vg_e:
            print(f"[Visual Gate] unavailable ({_vg_e}) — passing open")

    # Verbatim check (advisory) — the Contract says "report exact UBT output
    # verbatim, never summarize." If a build/compile phase's --result looks like a
    # SUMMARY (short, no compiler/UBT markers), warn. Not blocked — too fuzzy to
    # gate hard, but the smell is recorded.
    try:
        _vb_blob = (args.phase + " " + args.result).lower()
        if any(k in _vb_blob for k in ("build", "ubt", "compil")):
            _markers = ("error", "warning", "succeeded", "===", "build.bat", "cl ",
                        ".cpp", "ubt", "link", "\n")
            if len(args.result) < 120 and not any(m in args.result.lower() for m in _markers):
                print("[Verbatim] WARN: build/compile phase but --result looks summarized "
                      "(short, no UBT/compiler markers). The Contract requires exact output verbatim.")
                try:
                    from core.capcom import post_safe as _vb_ps
                    _vb_ps("verbatim", f"possibly-summarized build result: {args.phase[:56]}",
                           level="note", source="verbatim-check")
                except Exception:
                    pass
    except Exception:
        pass

    # Reverted-attempt honesty (advisory) — ".roo: a reverted attempt is a FAILURE,
    # not a fix; describing restored-broken-state as 'fixed' is the deadliest lie in
    # this constitution." Cheap, low-false-positive signal: the SAME report claims
    # both a revert/rollback AND success.
    try:
        _ra = (args.phase + " " + args.result + " " + args.notes).lower()
        _revert = any(w in _ra for w in ("revert", "rolled back", "roll back",
                                         "restored", "backed out", "checkout --"))
        _success = any(w in _ra for w in ("fixed", "working now", "now works",
                                          "resolved", "now verified", "passes now", "fix in place"))
        if _revert and _success:
            print("[Honesty] WARN: this report mentions BOTH a revert/rollback AND a success "
                  "claim. A reverted attempt is a FAILURE, not a fix — say 'attempt failed and "
                  "was reverted', never describe restored-broken-state as fixed.")
            try:
                from core.capcom import post_safe as _ra_ps
                _ra_ps("honesty", f"revert+success claim in one report: {args.phase[:52]}",
                       level="warn", source="honesty-check")
            except Exception:
                pass
    except Exception:
        pass

    node_id = record_phase(args.phase, args.result, args.notes,
                           phantom_pains=args.phantom_pain or [],
                           inheritance=args.inheritance,
                           pain_verdicts=parse_pain_verdicts(args.pain_verdict))
    print(f"PhaseComplete recorded: {node_id}")
    if str(node_id).startswith("rejected_"):
        raise SystemExit(1)
    for i, pain in enumerate(args.phantom_pain or [], start=1):
        print(f"  phantom pain declared -> {node_id}:P{i}  {pain[:80]}")

    for spec in args.eliminated or []:
        parts = [s.strip() for s in spec.split(":", 2)]
        if len(parts) < 2:
            print(f"  !! --eliminated needs '<feature> : <boundary> [: <evidence>]' — got: {spec[:60]}")
            continue
        feature, boundary = parts[0], parts[1]
        evidence = parts[2] if len(parts) > 2 else ""
        try:
            from core.graphify_interface import record_elimination
            eid = record_elimination(feature, boundary, evidence_ref=evidence)
            print(f"  elimination recorded -> {eid}  {feature}: NOT {boundary[:60]}")
        except Exception as e:
            print(f"  !! elimination failed to record: {e}")

    if args.feature:
        if args.loop is None or not args.status:
            parser.error("--feature requires --loop and --status")
        fid = record_feature(args.feature, args.loop, args.status)
        print(f"FeatureUpdate recorded: {args.feature} (loop {args.loop}) = {args.status} -> {fid}")

    gpa = graphify_query("gpa", "trend") or {}
    print(f"GPA: {gpa.get('gpa')}  trend: {gpa.get('trend')}  grades: {gpa.get('grades_count')}")
    if gpa.get("trend") == "falling":
        print("!! GPA is FALLING — the Contract requires reporting this with corrective action.")

    # CAPCOM — push a completion signal onto the operator channel so the NEXT
    # agent's brief shows what this phase did (and flags a falling GPA) without
    # having to dig. Agent-agnostic; post_safe never raises.
    try:
        from core.capcom import post_safe
        post_safe("phase", f"{args.phase[:80]} -> {args.result[:120]}",
                  level=("warn" if gpa.get("trend") == "falling" else "info"),
                  source="postflight",
                  data={"phase": args.phase, "result": args.result,
                        "gpa": gpa.get("gpa"), "trend": gpa.get("trend"),
                        "feature": args.feature, "loop": args.loop,
                        "status": args.status, "node_id": node_id})
    except Exception:
        pass

    # Tunnel containment — a session that postflights while still inside the
    # tunnel is the #1 leak (claim + editor left dangling for the reaper).
    try:
        from core.agent_tunnel import active_sessions
        open_sessions = active_sessions()
        if open_sessions:
            print("\n!! STILL IN THE TUNNEL — exit with evidence before you finish:")
            for s in open_sessions:
                print(f"   {s['agent']} holds {s['task_id']} ({s['task_title'][:48]})"
                      f"{' + editor ' + s['editor_mode'] if s.get('editor_held') else ''}")
                print(f"   -> python -m core.task_board done --agent {s['agent']} "
                      f"--id {s['task_id']} --result \"<verbatim evidence>\"  "
                      f"(or block --reason / release --note)")
    except Exception:
        pass

    # Git status check — surfaces uncommitted changes
    print()
    try:
        git_out = subprocess.run(
            ["git", "-C", str(Path(__file__).parent.parent), "status", "--short"],
            capture_output=True, text=True, timeout=10
        )
        git_lines = [l for l in git_out.stdout.splitlines() if l.strip()]
        # Snapshot choreography (tuning pass 2026-07-12): every postflight
        # dirties docs/chimera_dna_graph.json by design (save_dna_graph
        # refreshes the durability copy). When the snapshot is the ONLY dirt,
        # commit it here — the recording step finishes its own paperwork
        # instead of leaving a trailing chore for every session.
        # NB: `git -C Chimera/` prints paths relative to Chimera/, so the
        # snapshot appears as docs/... here (first-run bug: compared against
        # the repo-root Chimera/docs/... form and never matched).
        chim = str(Path(__file__).parent.parent)
        snapshot_rel = "docs/chimera_dna_graph.json"
        if git_lines and all(l[3:].strip().strip('"') == snapshot_rel for l in git_lines):
            try:
                subprocess.run(["git", "-C", chim, "add", snapshot_rel],
                               check=True, timeout=15, capture_output=True)
                subprocess.run(["git", "-C", chim, "commit", "-q", "-m",
                                "chore(dna): snapshot via postflight\n\n"
                                "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"],
                               check=True, timeout=30, capture_output=True)
                subprocess.run(["git", "-C", chim, "push", "-q"],
                               timeout=120, capture_output=True)
                print("[Git] DNA snapshot auto-committed + pushed (only dirt was the snapshot)")
                git_lines = []
            except Exception as e:
                print(f"[Git] snapshot auto-commit failed ({e}) — commit manually")
        if git_lines:
            print(f"[Git] {len(git_lines)} uncommitted change(s):")
            for l in git_lines[:10]:
                print(f"      {l}")
            if len(git_lines) > 10:
                print(f"      ... and {len(git_lines) - 10} more")
            # Check for untracked files
            untracked = [l for l in git_lines if l.startswith("??")]
            if untracked:
                print(f"      ({len(untracked)} untracked — add or .gitignore before committing)")
        else:
            print("[Git] Working tree is clean")
    except Exception as e:
        print(f"[Git] Status check failed: {e}")

    # Generation Protocol: warn if inherited pains remain un-dispositioned
    try:
        inh = collect_inheritance(load_dna_graph().get("nodes", []))
        undispositioned = [p for p in inh["open_pains"] if p["id"].split(":P")[0] != node_id]
        if undispositioned:
            print(f"\n[Inheritance] {len(undispositioned)} phantom pain(s) still open "
                  f"(confirm/refute with --pain-verdict):")
            for p in undispositioned[:5]:
                flag = " (still-open)" if p.get("still_open") else ""
                print(f"      {p['id']}  [{p['age_days']}d]{flag}  {p['text'][:70]}")
    except Exception as e:
        print(f"[Inheritance] scan failed: {e}")

    print("\nPost-Flight checklist:")
    print("  [ ] Exact UBT output reported verbatim (never summarized)")
    print("  [ ] Feature Ledger updated for every touched feature")
    print("  [ ] Every MCP call recorded as a pathway_attempt")
    print("  [ ] New discoveries recorded (research_discovery / technical_discovery)")
    print("  [ ] Phantom pains declared for next session + inherited pains dispositioned")
    print("  [ ] Evidenced features collapsed by AUTOMATED observation (sleepwalker/telemetry/grading — the measure)")
    print("  [ ] Git status reviewed and staged appropriate changes")
    print("  [ ] task_progress.md updated for the next session")


if __name__ == "__main__":
    main()
