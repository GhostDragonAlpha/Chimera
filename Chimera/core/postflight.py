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


def _gate_broken(name: str, exc: Exception):
    """A gate that RAISED is not a gate that PASSED (2026-07-16).

    Every gate here was wrapped in `except Exception: print("... — passing open")`. The
    intent was to tolerate a missing module; the effect was that ANY error inside ANY
    gate — NameError, TypeError, KeyError, a load_dna_graph() failure — silently turned
    that gate into a no-op announced by one friendly line. This is not hypothetical:
    core/critic.py used os.environ with NO `import os`, so every call raised NameError,
    and the swallow meant nobody found out for as long as it has been there.

    ABSENT and BROKEN are different facts and now get different treatment:
      ImportError  -> the module genuinely is not here. Pass open, say so. Honest.
      anything else-> the gate is BROKEN. It cannot have checked anything, so claiming
                      it "passed" is a lie about work that never happened.

    Exit 2, per the exit-code contract: 0 pass, 1 gate violation (blocked), 2 unexpected
    error. A broken gate is not a violation — it is an error — and the doctrine is "a
    gate fails -> exit non-zero -> halt; never fake a default."
    """
    print(f"\n!! {name} — BROKEN, not absent: {type(exc).__name__}: {exc}")
    print(f"   A gate that raised has verified NOTHING. Refusing to record this as a")
    print(f"   pass. Fix the gate, or set its CHIMERA_*_GATE=off to disable it EXPLICITLY.")
    try:
        from core.capcom import post_safe as _bp
        _bp("gate", f"{name} BROKEN ({type(exc).__name__}: {str(exc)[:80]}) — postflight "
                    f"refused rather than passing open", level="warn", source="postflight")
    except Exception:
        pass
    raise SystemExit(2)


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
    parser.add_argument("--training-waiver", default="", dest="training_waiver",
                        help="Training Gate: reasoned waiver when curriculum/rep training genuinely "
                             "doesn't apply (every feature is otherwise forced through school)")
    parser.add_argument("--council-waiver", default="", dest="council_waiver",
                        help="Council (second-system) gate: reasoned override when the deep brain "
                             "REJECTS but you have a justified reason to finalize anyway "
                             "(only relevant with CHIMERA_COUNCIL_GATE=block)")
    parser.add_argument("--why-waiver", default="", dest="why_waiver",
                        help="Why Gate: reasoned waiver when a finalized claim's why-chain "
                             "genuinely cannot reach PHYSICS or THE HUMAN. Recorded and read — "
                             "'nothing measured it' is the finding, not the exception")
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
            waiver=getattr(args, "research_waiver", "") or "",
            topic=(getattr(args, "phase", "") or getattr(args, "feature", "") or ""))
        # "unwaivable" (2026-07-16): a seed-build task cannot waive research — its own
        # premise is that the thing does not exist, so there is nothing here to inherit
        # the answer from. Blocks like "missing" because it IS missing: the waiver just
        # named the reason it cannot be waived.
        if _rg_status in ("missing", "unwaivable") and _rg_enforced():
            if _rg_status == "unwaivable":
                print(f"\n!! RESEARCH GATE - refused: {_rg_detail}")
            else:
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
            # NOT truncated (was [:110], 2026-07-16). The clipped line was the weapon:
            # an agent copied "...Sky (Earth/Moon/Sun" - cut off mid-parenthesis - into
            # its report as a research waiver it never made. If the gate has something
            # to say about provenance, the agent has to be able to READ all of it.
            print(f"\n[Research Gate] {_rg_status}: {_rg_detail}")
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
    except ImportError as _rg_e:          # ABSENT: the module is not here
        print(f"[Research Gate] not installed ({_rg_e}) — passing open")
    except Exception as _rg_e:            # BROKEN: it raised. That is not a pass.
        _gate_broken("Research Gate", _rg_e)

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
    except ImportError as _gg_e:          # ABSENT: the module is not here
        print(f"[Generator Guard] not installed ({_gg_e}) — passing open")
    except Exception as _gg_e:            # BROKEN: it raised. That is not a pass.
        _gate_broken("Generator Guard", _gg_e)

    # ---------------------------------------------------------------------------
    # THE GATE STACK WAS OPT-IN, AND NOBODY OPTED IN (fixed 2026-07-17).
    # ---------------------------------------------------------------------------
    # Everything below gates on `args.feature and args.status in FINAL`. MEASURED on a
    # real LEAD session: 9 of 9 postflights passed NO --feature and NO --status. So
    # Witness, WHY, Visual, Training, Coin and Council DID NOT RUN. Not once. Every
    # gate this studio has ever built was dead in the flow agents actually use, because
    # agents postflight a PHASE ("Witness & collapse: Social_Trade") and the gates want
    # a FEATURE.
    #
    # That is the mechanism behind the 76 assertions: the checks that would catch an
    # unearned `verified` are unreachable from the command everyone runs. A gate you
    # have to opt into is a suggestion.
    #
    # THE FEATURE NAME IS ALREADY IN THE PHASE. "Witness & collapse: Social_Trade".
    # So derive it — and gate ONLY when the derived name matches a feature whose LEDGER
    # says it is finalized. That keeps the blast radius exactly where it belongs;
    # measured against the same session:
    #   Witness & collapse: Social_Trade          -> REFUSE (verified, why=unasked)
    #                                                the collapse genuinely never ran
    #   Witness & collapse: Tool_Scanner_Material -> n/a (needs_refinement — an honest
    #                                                rejection is not a claim)
    #   Build toward the seed: ADotCharacter      -> n/a (no finalized status)
    #   rep_promotion:Game_Feel / SMOKE:          -> n/a (not feature claims)
    # It refuses the one that overclaimed and nothing else.
    #
    # The STATUS comes from the ledger, never from the agent: this is the gate asking
    # "the record says X is verified — what makes that true?", which is a question
    # about the RECORD and cannot be dodged by declining to mention it.
    #
    # A DERIVED FEATURE GATES; IT NEVER RECORDS. `_derived_feature` exists because my
    # first cut set args.feature and stopped looking — and line ~677 ALSO reads it, to
    # `record_feature(args.feature, args.loop, args.status)`. So deriving a name for a
    # READ-ONLY check would have tripped `--feature requires --loop and --status`
    # (exit 2), and with --loop present would have WRITTEN A DUPLICATE FeatureUpdate to
    # the ledger — a name invented for gating, laundered into the record as a claim.
    # I wired it to the gates and did not ask what else reads it, which is the exact
    # trap the onboarding names: "half-doing the honest thing looks exactly like doing
    # it."
    _derived_feature = False
    if not args.feature and args.phase:
        _final = {"verified", "accepted", "observed", "observed_provisional"}
        _ledger = {}
        for _n in load_dna_graph().get("nodes", []):
            if _n.get("type") == "FeatureUpdate" and _n.get("feature_name"):
                _t = _n.get("timestamp", "")
                if _n["feature_name"] not in _ledger or _t > _ledger[_n["feature_name"]][1]:
                    _ledger[_n["feature_name"]] = (_n.get("status"), _t)
        # after the colon first ("Witness & collapse: Social_Trade"), else any known
        # feature named anywhere in the phase. Longest match wins — Tool_Scanner_Material
        # must not resolve to Tool_Scanner.
        _cand = args.phase.split(":")[-1].strip() if ":" in args.phase else ""
        _hit = _cand if _cand in _ledger else next(
            (f for f in sorted(_ledger, key=len, reverse=True) if f and f in args.phase), "")
        if _hit and _ledger[_hit][0] in _final:
            args.feature, args.status = _hit, _ledger[_hit][0]
            _derived_feature = True
            print(f"[postflight] no --feature given; DERIVED '{_hit}' from the phase — "
                  f"the ledger says it is '{_ledger[_hit][0]}', so the gate stack applies "
                  f"(it GATES only; nothing is recorded from a derived name). "
                  f"Pass --feature explicitly to control this.")

    # WHY GATE (2026-07-16) — runs for BOTH explicit and DERIVED features, and it is
    # the ONLY gate that does. The others below police the ACT of marking ("you are
    # claiming verified NOW — show fresh evidence NOW": witness/visual have 12h
    # windows, training wants enrollment, the Coin judges the claim being made).
    # A DERIVED feature has no marking act — the postflight merely NAMED a feature the
    # ledger already finalized — so those questions are category errors against it:
    # measured, Sky_Earth_Model (honestly observed days ago, chain reaches PHYSICS)
    # would have been REFUSED by the witness gate's 12-hour window purely for being
    # MENTIONED in a phase. My own matrix tests missed this because every one ran with
    # CHIMERA_*_GATE=warn; under production defaults the refusal is live. An
    # instrument wrong in that direction teaches everyone to route around it.
    #
    # The WHY question alone is TIMELESS — "the record says X is finalized; does its
    # chain reach something that needed no observer?" — so it is the one question a
    # mere mention can honestly be held to.
    if args.feature and args.status in {"verified", "observed", "observed_provisional"}:
        try:
            from core.why_gate import (check as _yg_check, enforced as _yg_enforced,
                                       GUIDANCE as _yg_guide)
            _yg_state, _yg_detail = _yg_check(
                feature=(getattr(args, "feature", "") or ""),
                status=args.status,
                waiver=getattr(args, "why_waiver", "") or "")
            # DERIVED = a MENTION, and a mention is ASKED, never sentenced (2026-07-17).
            # Proven in a membrane before this landed: the refusal's own escape path can
            # be legitimately closed — Social_Trade's collapse is blocked by the rep
            # gate (4/50 reps, and reps accumulate across NIGHTS by design), so an agent
            # whose witness ran clean and whose collapse was honestly refused could not
            # even postflight that partial result, because its phase NAMED a feature
            # whose OLD record is a lie the agent did not write and cannot fix today.
            # Block on a mention and every honest bystander is hostage to the worst
            # record it stands near — the observation queue jams wholesale.
            # So: derived -> the question is asked LOUDLY and posted to CAPCOM, every
            # time, until the record is repaired. Explicit claim -> refused, as before.
            # The lie still cannot PROGRESS: record_observation, collapse_proxy and
            # task closure keep their hard gates at the write-moments.
            # refused_waiver is a LIE, not a dead end — it ALWAYS hard-blocks, even on
            # a derived feature and even under =warn, because a false attestation is
            # worse than a missing one: an honest gap gets fixed, a lie gets trusted.
            # The other states (dead_end/unasked) advise on a mere mention; a waiver is
            # never a mere mention — the agent typed it to get past the gate.
            if _yg_state == "refused_waiver":
                print(f"\n!! WHY GATE - waiver REFUSED: {args.feature} '{args.status}' — {_yg_detail}")
                try:
                    from core.capcom import post_safe as _yg_ps
                    _yg_ps("why", f"FALSE WAIVER REFUSED: {args.feature} '{args.status}' — the "
                           f"waiver claimed the why-chain passes; the walk reached no terminal",
                           level="warn", source="why-gate")
                except Exception:
                    pass
                raise SystemExit(1)
            if _yg_state in ("dead_end", "unasked") and _derived_feature:
                print(f"\n?? WHY GATE (advisory — feature was DERIVED, not claimed): "
                      f"{args.feature} '{args.status}' — {_yg_detail}")
                print("   The RECORD is unbacked. This will be said on every mention "
                      "until someone repairs it; it does not block THIS postflight, "
                      "because you did not write that record by mentioning it.")
                try:
                    from core.capcom import post_safe as _yg_ps
                    _yg_ps("why", f"UNBACKED RECORD (mentioned in '{args.phase[:48]}'): "
                           f"{args.feature} is '{args.status}' with {_yg_detail[:100]}",
                           level="warn", source="why-gate")
                except Exception:
                    pass
            elif _yg_state in ("dead_end", "unasked") and _yg_enforced():
                print(f"\n!! WHY GATE - refused: {args.feature} '{args.status}' — {_yg_detail}")
                print(_yg_guide)
                try:
                    from core.graphify_interface import record_surprise as _yg_rs
                    _yg_rs(context=f"postflight refused by why gate: {args.feature} -> {args.status}",
                           reality=_yg_detail,
                           expectation="a finalized claim's why-chain reaches PHYSICS or THE HUMAN",
                           source="agent")
                except Exception:
                    pass
                try:
                    from core.capcom import post_safe as _yg_ps
                    _yg_ps("why", f"postflight BLOCKED: {args.feature} '{args.status}' — {_yg_detail}",
                           level="warn", source="why-gate")
                except Exception:
                    pass
                raise SystemExit(1)
            print(f"[Why Gate] {_yg_state}: {_yg_detail}")
            if _yg_state == "waived":
                try:
                    from core.capcom import post_safe as _yg_ps
                    _yg_ps("why", f"why WAIVED: {args.feature} {args.status} - {_yg_detail}",
                           level="note", source="why-gate")
                except Exception:
                    pass
        except SystemExit:
            raise
        except ImportError as _yg_e:
            print(f"[Why Gate] not installed ({_yg_e}) — passing open")
        except Exception as _yg_e:
            _gate_broken("Why Gate", _yg_e)

    if _derived_feature and args.status in {"verified", "observed", "observed_provisional"}:
        print("[postflight] act gates (Witness/Visual/Training/Coin/Council) SKIPPED for the "
              "derived feature: they police the act of MARKING, and nothing was marked here — "
              "the name was derived from the phase. The Why Gate above still held the record "
              "to its question. (Pass --feature/--status/--loop explicitly to claim, which "
              "runs the full stack.)")

    # Witness Gate — a feature can't be recorded verified/observed on a compile
    # alone (H-14: a compile is not proof). Requires witness evidence this session
    # (SimPlaytest/telemetry/observation), --witnessed, or a reasoned
    # --witness-waiver. Only fires on a verify/observe transition.
    if args.feature and not _derived_feature and args.status in {"verified", "observed", "observed_provisional"}:
        try:
            from core.witness_gate import check as _wg_check, enforced as _wg_enforced, GUIDANCE as _wg_guide
            _wg_nodes = load_dna_graph().get("nodes", [])
            _wg_status, _wg_detail = _wg_check(
                _wg_nodes, status=args.status,
                witnessed=getattr(args, "witnessed", "") or "",
                waiver=getattr(args, "witness_waiver", "") or "",
                feature=(getattr(args, "feature", "") or ""))
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
            # NOT truncated (2026-07-16). I fixed the Research Gate's [:110] this
            # morning after a clipped line became a weapon -- an agent copied
            # "...Sky (Earth/Moon/Sun" (cut mid-parenthesis) into its report as a
            # waiver it never made -- and left the other three call sites clipping.
            # Fixing the instance you can see is not fixing the defect.
            print(f"[Witness Gate] {_wg_status}: {_wg_detail}")
            if _wg_status == "waived":
                try:
                    from core.capcom import post_safe as _wg_ps
                    _wg_ps("witness", f"witness WAIVED: {args.feature} {args.status} - {_wg_detail[:48]}",
                           level="note", source="witness-gate")
                except Exception:
                    pass
        except SystemExit:
            raise
        except ImportError as _wg_e:          # ABSENT: the module is not here
            print(f"[Witness Gate] not installed ({_wg_e}) — passing open")
        except Exception as _wg_e:            # BROKEN: it raised. That is not a pass.
            _gate_broken("Witness Gate", _wg_e)

        # (The WHY gate ran ABOVE this block — it is the one gate that applies to
        # derived features too, so it lives outside the act-gate stack.)

        # Visual Gate — the local model must have LOOKED at a verified feature: a
        # feature can't be marked verified/observed without a recorded LM screenshot
        # analysis this session, --visual-analysis, or a reasoned --visual-waiver.
        try:
            from core.visual_gate import check as _vg_check, enforced as _vg_enforced, GUIDANCE as _vg_guide
            _vg_nodes = load_dna_graph().get("nodes", [])
            _vg_status, _vg_detail = _vg_check(
                _vg_nodes, status=args.status,
                analysis=getattr(args, "visual_analysis", "") or "",
                waiver=getattr(args, "visual_waiver", "") or "",
                feature=(getattr(args, "feature", "") or ""))
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
            print(f"[Visual Gate] {_vg_status}: {_vg_detail}")
            if _vg_status == "waived":
                try:
                    from core.capcom import post_safe as _vg_ps
                    _vg_ps("visual", f"visual analysis WAIVED: {args.feature} {args.status} - {_vg_detail[:44]}",
                           level="note", source="visual-gate")
                except Exception:
                    pass
        except SystemExit:
            raise
        except ImportError as _vg_e:          # ABSENT: the module is not here
            print(f"[Visual Gate] not installed ({_vg_e}) — passing open")
        except Exception as _vg_e:            # BROKEN: it raised. That is not a pass.
            _gate_broken("Visual Gate", _vg_e)

        # Training Gate — every feature is FORCED through training, one piece at
        # a time (the human's goal, 2026-07-14): verified requires curriculum
        # enrollment + reps begun; observed requires the full rep gate. A silent
        # skip is refused; --training-waiver records the honest exception.
        try:
            from core.training_gate import check as _tg_check, enforced as _tg_enforced, guidance as _tg_guide
            _tg_status, _tg_detail = _tg_check(
                args.feature, status=args.status,
                waiver=getattr(args, "training_waiver", "") or "")
            if _tg_status == "missing" and _tg_enforced():
                print(f"\n!! TRAINING GATE - refused: {args.feature} -> '{args.status}' without training: {_tg_detail}")
                print(_tg_guide(args.feature))
                try:
                    from core.graphify_interface import record_surprise as _tg_rs
                    _tg_rs(context=f"postflight refused by training gate: {args.feature} -> {args.status}",
                           reality=_tg_detail[:200],
                           expectation="every feature goes through the curriculum + rep training before verification",
                           source="agent")
                except Exception:
                    pass
                try:
                    from core.capcom import post_safe as _tg_ps
                    _tg_ps("training", f"postflight BLOCKED: {args.feature} {args.status} untrained - {_tg_detail[:60]}",
                           level="warn", source="training-gate")
                except Exception:
                    pass
                raise SystemExit(1)
            print(f"[Training Gate] {_tg_status}: {_tg_detail}")
            if _tg_status == "waived":
                try:
                    from core.capcom import post_safe as _tg_ps
                    _tg_ps("training", f"training WAIVED: {args.feature} {args.status} - {_tg_detail[:52]}",
                           level="note", source="training-gate")
                except Exception:
                    pass
        except SystemExit:
            raise
        except ImportError as _tg_e:          # ABSENT: the module is not here
            print(f"[Training Gate] not installed ({_tg_e}) — passing open")
        except Exception as _tg_e:            # BROKEN: it raised. That is not a pass.
            _gate_broken("Training Gate", _tg_e)

        # THE COIN (top layer, the human's design 2026-07-14) — the existence
        # gates above check evidence EXISTS; the coin checks the two faces MATCH:
        # HEADS = the claim being recorded, TAILS = this session's evidence. The
        # LM judges both directions (evidence proves claim / claim honest to
        # evidence). NOT the same coin -> refused. LM unavailable -> pass open
        # (cannot-judge is not judged-false). CHIMERA_COIN_GATE=warn softens.
        try:
            from core.coin_verifier import (judge as _coin_judge, enforced as _coin_enforced,
                                            assemble_claim as _coin_claim,
                                            assemble_evidence as _coin_evidence,
                                            format_judgment as _coin_fmt)
            _coin_nodes = load_dna_graph().get("nodes", [])
            _cj = _coin_judge(
                _coin_claim(args.feature, args.status, args.result, args.notes),
                _coin_evidence(_coin_nodes, feature=args.feature),
                kind="feature_verify")
            if _cj is None:
                print("[Coin] LM unavailable/unparseable — passing open (existence gates still held)")
            else:
                print("[Coin] " + ("SAME COIN" if _cj.get("same_coin") else "NOT THE SAME COIN"))
                print(_coin_fmt(_cj))
                try:
                    from core.capcom import post_safe as _coin_ps
                    _coin_ps("coin", f"{args.feature} {args.status}: "
                             f"{'same coin' if _cj.get('same_coin') else 'NOT SAME COIN'} "
                             f"({_cj.get('verdict')})",
                             level=("info" if _cj.get("same_coin") else "warn"),
                             source="coin-verifier", data=_cj)
                except Exception:
                    pass
                if not _cj.get("same_coin") and _coin_enforced():
                    print("!! COIN GATE - refused: the claim and the evidence are not "
                          "faces of the same coin. Fix the mismatch (or CHIMERA_COIN_GATE=warn).")
                    try:
                        from core.graphify_interface import record_surprise as _coin_rs
                        _coin_rs(context=f"postflight refused by THE COIN: {args.feature} -> {args.status}",
                                 reality="; ".join(str(m) for m in (_cj.get("mismatches") or [])[:3])
                                         or "claim/evidence mismatch",
                                 expectation="claim and evidence must be faces of the same coin",
                                 source="agent")
                    except Exception:
                        pass
                    raise SystemExit(1)
        except SystemExit:
            raise
        except ImportError as _coin_e:          # ABSENT: the module is not here
            print(f"[Coin] not installed ({_coin_e}) — passing open")
        except Exception as _coin_e:            # BROKEN: it raised. That is not a pass.
            _gate_broken("Coin", _coin_e)

        # THE COUNCIL — THE PARACLETE (rebuilt 2026-07-16 on the human's reading).
        # It ASKS; the GRAPH answers; nobody here decides. The deep brain (ds4, a
        # DIFFERENT model) names the evidence that would have to exist for this claim to
        # hold — especially what a confident agent forgets to look for. Deterministic
        # checks then answer what they can, with no LLM in the loop.
        #
        # A QUESTION CANNOT BE FABRICATED. That is why this block no longer needs the
        # schema validation, the H-3 retry ladder, or the UNAVAILABLE-not-ENDORSE guard
        # that the old verdict path required: there is no verdict to forge. What blocks
        # here is THE GRAPH's answer — "you claim it was playtested; there is no
        # SimPlaytest for it" is a FACT, not an opinion — and what survives unanswered is
        # the human's, arriving EARNED, with every machine-checkable question already
        # stripped out.
        try:
            from core import council as _council
            _cmode = _council.gate_mode()
            if _cmode != "off":
                print("\n[Council] the deep brain is asking what would have to be true (slow)...")
                _cr = _council.review(args.feature, args.status, args.result, args.notes,
                                      nodes=load_dna_graph().get("nodes", []))
                if not _cr.get("up"):
                    print("[Council] deep brain unavailable — no questions asked "
                          "(start it: python -m core.ds4_brain serve)")
                else:
                    _refuted = _cr.get("refuted") or []
                    _open = _cr.get("open") or []
                    print(f"[Council] {_cr.get('asked')}")
                    for _a in (_cr.get("questions") or []):
                        _mark = {True: "yes ", False: "NO  ", None: "open"}[_a["answered"]]
                        print(f"   [{_mark}] {str(_a['q'])[:88]}")
                    if _refuted:
                        # THE GRAPH refuted these, not a model. These are facts.
                        print(f"\n!! COUNCIL — the graph REFUTES {len(_refuted)} question(s) "
                              f"this claim depends on:")
                        for _a in _refuted:
                            print(f"   x {str(_a['q'])[:96]}")
                            print(f"     -> {_a['evidence']} ({_a['check']})")
                        try:
                            from core.capcom import post_safe as _cp
                            _cp("council", f"{args.feature} {args.status}: the graph refutes "
                                f"{len(_refuted)} question(s) — e.g. "
                                f"{str(_refuted[0]['q'])[:80]}",
                                level="warn", source="council")
                        except Exception:
                            pass
                        try:
                            from core.graphify_interface import record_surprise as _crs
                            _crs(context=f"council questions refuted by the graph: "
                                         f"{args.feature} -> {args.status}",
                                 reality="; ".join(str(a["q"])[:90] for a in _refuted[:3]),
                                 expectation="the evidence this claim depends on exists in the graph",
                                 source="agent")
                        except Exception:
                            pass
                        if _cmode == "block" and not (getattr(args, "council_waiver", "") or ""):
                            print("   Refusing: CHIMERA_COUNCIL_GATE=block and the graph says "
                                  "this evidence is absent. Produce it, or pass "
                                  "--council-waiver with a reason.")
                            raise SystemExit(1)
                    if _open:
                        print(f"\n[Council] {len(_open)} question(s) no check can answer — "
                              f"THESE ARE YOURS (everything machine-answerable is resolved):")
                        for _a in _open:
                            print(f"   ? {str(_a['q'])[:96]}")
        except SystemExit:
            raise
        except ImportError as _cg_e:            # ABSENT: not installed
            print(f"[Council] not installed ({_cg_e}) — no second opinion")
        except Exception as _cg_e:              # BROKEN: it raised. That is not a pass.
            _gate_broken("Council", _cg_e)
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

    # Confirmed pains become WORK (2026-07-15): a confirmed verdict is a proven
    # real problem — spawn a board follow-up fix task so the confirmation is a
    # beginning, not the end of the line (tb-0056: zero-callers confirmed,
    # nothing spawned "wire a caller"). Guarded — spawning never blocks the record.
    try:
        _pv = parse_pain_verdicts(args.pain_verdict)
        _confirmed = [k for k, v in _pv.items() if v == "confirmed"]
        if _confirmed:
            from core.ripener import spawn_followups
            for _tid in spawn_followups(pain_ids=_confirmed):
                print(f"  confirmed pain -> follow-up fix task {_tid}")
    except Exception as _fu_e:
        print(f"  (confirmed-pain follow-up spawn skipped: {_fu_e})")

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

    # `not _derived_feature`: a name DERIVED from the phase for gating must never reach
    # the ledger. The gates above ask "the record says X is verified — what makes that
    # true?"; recording here would make postflight ANSWER its own question by writing
    # the claim it was checking.
    if args.feature and not _derived_feature:
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
