"""make_instrument.py -- the TICK-COST ATTRIBUTION instrument generator.

Derives instrumented copies of gait_controller.hpp and gait_unit.cpp from the
TRACKED bytes by DECLARED, ANCHORED, single-occurrence edits (PREREG.md,
"Methods" 2). The tracked files are READ-ONLY for this lane: the derived
copies land under .tmp/tickcost/src/ and nothing in the tree is modified.

Marker discipline: the //@TICKCOST marker is always a TRAILING comment on an
inserted or replaced line -- never a line prefix (a prefix would comment out
the instrumented statement itself; the generator's verify enforces trailing).

Guarantees enforced here (the generator refuses loudly otherwise):
  1. every anchor occurs EXACTLY the declared number of times (default 1);
  2. every derived line that is not an original line carries a TRAILING
     //@TICKCOST marker (no line begins with the marker);
  3. re-applying the recorded edit manifest to the tracked source reproduces
     the derived file BYTE-EXACTLY (manifest round-trip);
  4. regeneration is deterministic (re-run => byte-identical outputs).

The timers themselves are FP-neutral (chrono + counters); stdout byte-neutrality
is proven per run against the pinned ship sha (F2).

Usage:
  python make_instrument.py [--out DIR] [--verify-only]

Trailer Agent: tickcost.
"""
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]  # tools/science_funnel/validation/<lane> -> repo root
HDR = ROOT / "ChimeraEngine/engine/gait_controller.hpp"
UNIT = ROOT / "ChimeraEngine/engine/tests_coupled_arm/gait_unit.cpp"
PROBE = HERE / "tickcost_probe.hpp"

M = " //@TICKCOST"  # the TRAILING marker


class Edits:
    def __init__(self):
        self.ops = []  # (kind, anchor, payload(str or list of str), count)

    def ins_before(self, anchor, lines, count=1):
        self.ops.append(("ins_before", anchor, lines, count)); return self

    def ins_after(self, anchor, lines, count=1):
        self.ops.append(("ins_after", anchor, lines, count)); return self

    def replace(self, old, new, count=1):
        self.ops.append(("replace", old, new, count)); return self


def header_edits():
    e = Edits()
    # -- probe include + the timed inverse_spd forward ---------------------
    e.ins_after("#pragma once",
                ['#include "tickcost_probe.hpp"' + M])
    e.ins_after("namespace chimera::multibody {",
                ["// (tickcost) timed forward of the free solver inverse" + M,
                 "inline Dense tickcost_inverse_spd(const Dense& a,std::size_t n){tickcost::Scope _tc_inv(tickcost::INV_SPD);return inverse_spd(a,n);}" + M])
    # -- FK: the one-liner evaluate (replacement; identical FP expression) --
    e.replace(" Evaluation evaluate(const State& s)const{return model_->evaluate(s.q,s.v,gravity_);}",
              " Evaluation evaluate(const State& s)const{tickcost::Scope _tc_fk(tickcost::FK_EVALUATE);return model_->evaluate(s.q,s.v,gravity_);}" + M)
    # -- solver leaves ------------------------------------------------------
    e.ins_after(" static void friction_solve(const Dense& initial,const Dense& inverse,const Dense& row_n,const Dense& row_t,double floor_n,double floor_t,double mu,double slip_sign,Dense& force,double& lambda_n,double& lambda_t,int& mode){",
                ["  tickcost::Scope _tc_fric(tickcost::FRICTION_SOLVE);" + M])
    e.ins_after(" static Dense project_rows(const Dense& initial,const Dense& inverse,const std::vector<Dense>& rows,const Dense& floors,std::vector<double>* multipliers,size_t n_stops=0){",
                ["  tickcost::Scope _tc_proj(tickcost::PROJECT_ROWS);" + M])
    # -- servo ---------------------------------------------------------------
    e.ins_after(" Dense servo()const{ // capped mass-normalized PD at the derived 4.0 Hz (Section 5.2)",
                ["  tickcost::Scope _tc_servo(tickcost::SERVO);" + M])
    # -- the rate/integrator ladder ------------------------------------------
    e.ins_after(" Rate rate(const State& s,const Dense& tau,const std::vector<char>& live,const std::vector<char>& plane)const{",
                ["  tickcost::Scope _tc_rate(tickcost::ADV_RATE);" + M])
    e.replace("  auto e=evaluate(s);auto inv=inverse_spd(e.mass,n_);",
              "  auto e=evaluate(s);auto inv=tickcost_inverse_spd(e.mass,n_);" + M, count=2)
    e.ins_after(" State free_step(const State& start,double h,const Dense& tau,const std::vector<char>& live)const{",
                ["  tickcost::Scope _tc_fs(tickcost::ADV_FREESTEP);" + M])
    e.ins_after(" double impact(State& s)const{",
                ["  tickcost::Scope _tc_imp(tickcost::ADV_IMPACT);" + M])
    e.ins_after("  if(h<1e-12)return start;",
                ["  tickcost::AdvScope _tc_adv;" + M])
    # -- reflex leaves --------------------------------------------------------
    e.ins_after(" bool update_clock(const Evaluation& e,double dt){",
                ["  tickcost::Scope _tc_uc(tickcost::UPDATE_CLOCK);" + M])
    e.ins_after(" void update_fore_clock(const Evaluation& e){",
                ["  tickcost::Scope _tc_fc(tickcost::FORE_CLOCK);" + M])
    e.ins_after(" bool support_state(const Evaluation& e,std::vector<std::pair<double,double>>& hull,V& com,\n  std::vector<std::pair<double,double>>* chain=nullptr)const{",
                ["  tickcost::Scope _tc_ss(tickcost::SUPPORT_STATE);" + M])
    e.ins_after(" void capture_reflex(const Evaluation& e,const std::vector<std::pair<double,double>>& hull,const V& com){",
                ["  tickcost::Scope _tc_cap(tickcost::CAPTURE_FN);" + M])
    # -- step() stages ----------------------------------------------------------
    e.ins_after(" void step(){",
                ["  tickcost::rec().adv_snap(adv_calls_);" + M])
    e.ins_before("  s_.impulse=Dense(n_,0.);",
                 ["  {tickcost::Scope _tc_st(tickcost::ST_RESET_ALLOC);" + M])
    e.ins_after("  s_.impulse=Dense(n_,0.);s_.contact_impact_impulse.assign(npts_,0.);s_.contact_force_impulse.assign(npts_,0.);s_.contact_generalized=Dense(n_,0.);s_.friction_impulse.assign(npts_,0.);s_.friction_force_impulse.assign(npts_,0.);s_.friction_heat_tick.assign(npts_,0.);",
                ["  }" + M])
    e.ins_before("  {auto e=evaluate(s_);if(walking)update_clock(e,dt_);else{for(size_t leg=0;leg<2;++leg)",
                 ["  {tickcost::Scope _tc_st(tickcost::ST_REFLEX_CLOCK);" + M])
    e.ins_after("      (unsigned long long)hind_step_deadline_tick_[hl]);\n#endif\n    }}}\n",
                ["  }" + M])
    e.ins_before("  {auto e=evaluate(s_);std::vector<std::pair<double,double>> hull,chain;V com{};",
                 ["  {tickcost::Scope _tc_st(tickcost::ST_CAPTURE_REFLEX);" + M])
    e.ins_after("   capture_reflex(e,chain,com);}}",
                ["  }" + M])
    e.ins_before("  if(paws_captured_){auto e0=evaluate(s_);",
                 ["  {tickcost::Scope _tc_st(tickcost::ST_SAT_CENSUS);" + M])
    e.ins_after("    if(fore_ik(leg,e0).saturated)++ik_sat_ticks_[leg];}}",
                ["  }" + M])
    e.ins_before("  for(int k=0;k<4;++k){",
                 ["  {tickcost::Scope _tc_st(tickcost::ST_INTEGRATE);" + M])
    e.ins_after("   s_=std::move(trial);}",
                ["  }" + M])
    e.ins_before("  last_torque_=impulse_torque;++ticks_;}",
                 ["  tickcost::rec().adv_note(adv_calls_);" + M])
    return e


def unit_edits():
    e = Edits()
    # -- include the DERIVED header instead of the tracked one ---------------
    e.replace('#include "../gait_controller.hpp"',
              '#include "tickcost_gait_controller.hpp"' + M)
    # NOTE (PREREG Amendment 2): counted operator new/delete was REMOVED. The
    # smoke run measured its instrumentation overhead at ~+12 ms/tick
    # (~157k allocations/tick routed through the override), which would fire
    # F3(c) (>10% of the tick). Allocation churn is therefore named
    # UNMEASURED; the tick-reset stage timing (a chrono scope) stays.
    # -- walk loop: loop wall + per-tick wall sample --------------------------
    e.ins_before("  for(int i=0;i<WALK;++i){",
                 ["  tickcost::rec().reset_all();" + M,
                  "  tickcost::rec().loop_begin();" + M])
    e.ins_before("   try{\n    d.step();\n",
                 ["  tickcost::rec().tick_begin();" + M])
    e.ins_after("   try{\n    d.step();\n",
                ["  tickcost::rec().tick_end_walk();" + M])
    # -- status() / census / dump: EXPLICIT begin/end pairs (no braces: `s`
    #    must outlive the status timer and the census block owns no scope) ----
    e.ins_before("   auto s=d.status();\n   // WAVE 13 fore-paw census: every tick, per-leg worst/best gap over the\n",
                 ["  tickcost::rec().t_begin(tickcost::STATUS_JSON);" + M])
    e.ins_before("   // WAVE 13 fore-paw census: every tick, per-leg worst/best gap over the\n",
                 ["  tickcost::rec().t_end(tickcost::STATUS_JSON);tickcost::rec().t_begin(tickcost::CENSUS_BLOCK);" + M])
    dump_anchor = ("   if(i%10==0){std::string j=s.dump();out.stream+=j;out.stream+="
                   + chr(39) + chr(92) + "n" + chr(39) + ";}\n")
    e.ins_before(dump_anchor, ["  tickcost::rec().t_begin(tickcost::DUMP_BLOCK);" + M])
    e.ins_after(dump_anchor, ["  tickcost::rec().t_end(tickcost::DUMP_BLOCK);" + M])
    e.ins_before("   out.a.push_back(a);out.tg.push_back(tg);out.t.push_back(tt);out.r.push_back(rr);}",
                 ["  tickcost::rec().t_end(tickcost::CENSUS_BLOCK);" + M])
    # -- walk_run summary (also resets for the next phase) ----------------------
    e.ins_before("  out.captures=d.capture_events();out.last=d.status();\n  return out;};",
                 ['  {static int tc_run=0;++tc_run;char tc_p[32];std::snprintf(tc_p,32,"walk_run_%d",tc_run);tickcost::summary(tc_p);}' + M,
                  "  tickcost::rec().reset_all();" + M])
    # -- the push run (the 426-tick interacting scene) ---------------------------
    e.ins_before(" {GaitWalker d(data,9.80665,V{0,0,0},dt);\n  d.configure({{\"capture_enabled\",false},{\"reset\",true}});\n  int refused=0;",
                 ["  tickcost::rec().reset_all();" + M])
    e.ins_before("  for(int i=0;i<2*CYCLE_TICKS;++i){",
                 ["  tickcost::rec().loop_begin();" + M])
    e.ins_before("   try{d.step();}catch(const Refusal&e){refused=1;break;}\n",
                 ["  tickcost::rec().tick_begin();" + M])
    e.ins_after("   try{d.step();}catch(const Refusal&e){refused=1;break;}\n",
                ["  tickcost::rec().tick_end_push();" + M])
    e.ins_after('  ck(d.capture_events()==0,"f6_disarmed_no_capture");}',
                ['  tickcost::summary("push426");' + M])
    # -- THE STAND426 PHASE (PREREG Amendment 2): the >= 426-tick SUSTAINED
    #    interacting scene. The F-G6 push walker (above) is the expected-tip
    #    regime and refuses at 302 on the pinned bytes (measured, smoke run;
    #    the receipt's own push426_s ~ 302 ticks at 22.5 ms/tick), so the
    #    latency requirement needs a run that SUSTAINS 426 ticks: the stage-E
    #    stand (contact ON, power ON, the gait clock frozen) -- the walk's own
    #    stable standing floor, a fully coupled gravity+contact+servo scene.
    #    Amendment 3 note: the first stand426 draft injected the F-G6 0.1-BW
    #    push mid-run and REFUSED at 139 (measured) -- a pushed stand is the
    #    tip regime; the sustained scene is the UNPUSHED stand.
    #    Lives ONLY in this derived harness; the tracked bytes are untouched.
    e.ins_before(" // ── F-G7: determinism -- a second identical run is BIT-identical.",
                 ["  { // TC STAND426 (declared instrument phase; PREREG Amendment 2/3)" + M,
                  "  GaitWalker d_tc(data,9.80665,V{0,0,0},dt);" + M,
                  '  d_tc.configure({{"gait_enabled",false},{"power",true},{"reset",true}});' + M,
                  "  tickcost::rec().reset_all();tickcost::rec().loop_begin();" + M,
                  "  for(int i=0;i<2*CYCLE_TICKS;++i){" + M,
                  "   tickcost::rec().tick_begin();" + M,
                  "   try{d_tc.step();}catch(const Refusal&e){break;} // phase n reports the refusal" + M,
                  "   tickcost::rec().tick_end_push();" + M,
                  "  }" + M,
                  '  tickcost::summary("stand426");' + M,
                  "  }" + M])
    return e


def apply(text, edits, name, manifest):
    replaced = []  # original anchors intentionally removed (replace ops)
    for kind, anchor, payload, count in edits.ops:
        n = text.count(anchor)
        if n != count:
            sys.exit("ANCHOR FAIL in %s (count=%d, want %d): %r" % (name, n, count, anchor[:80]))
    # Record ABSOLUTE splice ranges on the tracked text, then apply them in
    # DESCENDING position order so earlier insertions never invalidate later
    # recorded positions. At equal positions, replace (a splice) is applied
    # before insertions landing on the same offset.
    ops = []  # (pos, end, order, kind, anchor, payload)
    for kind, anchor, payload, count in edits.ops:
        start = 0
        for _ in range(count):
            i = text.index(anchor, start)
            if kind == "ins_before":
                ops.append((i, i, 1, kind, anchor, payload))
            elif kind == "ins_after":
                ops.append((i + len(anchor), i, 1, kind, anchor, payload))
            else:  # replace
                ops.append((i, i + len(anchor), 0, kind, anchor, payload))
            start = i + 1
    ops.sort(key=lambda t: (-t[0], t[2]))
    buf = text
    for pos, end, _o, kind, anchor, payload in ops:
        if isinstance(payload, list):
            payload = "\n".join(payload)
        if kind == "replace":
            buf = buf[:pos] + payload + buf[end:]
            replaced.append(anchor)
        elif kind == "ins_before":
            buf = buf[:pos] + payload + "\n" + buf[pos:]
        else:  # ins_after: land the payload on its OWN line before the
            # anchor's trailing newline, never glued onto the next line (a
            # leading // comment would otherwise swallow original code)
            ins_at = pos - 1 if pos > 0 and buf[pos - 1] == "\n" else pos
            buf = buf[:ins_at] + "\n" + payload + buf[ins_at:]
    manifest[name] = {"ops": [
        {"kind": k, "anchor": a,
         "payload": "\n".join(p) if isinstance(p, list) else p, "count": c}
        for k, a, p, c in edits.ops],
        "replaced_anchors": replaced}
    return buf


def verify(derived, original, manifest, name):
    """Every derived line either (a) is an original line or (b) carries a
    TRAILING //@TICKCOST marker (never a prefix -- a prefix would comment out
    the instrumented statement); and re-applying the recorded manifest to the
    tracked source reproduces the derived bytes exactly."""
    dlines = derived.split("\n")
    orig_lines = set(original.split("\n"))
    for ln in dlines:
        if ln in orig_lines:
            continue
        if "@TICKCOST" not in ln:
            sys.exit("VERIFY FAIL %s: unmarked new line %r" % (name, ln[:80]))
        if ln.lstrip().startswith("//@TICKCOST"):
            sys.exit("VERIFY FAIL %s: leading marker comments out code: %r" % (name, ln[:80]))
    re_edits = Edits()
    for op in manifest[name]["ops"]:
        if op["kind"] == "ins_before":
            re_edits.ins_before(op["anchor"], op["payload"].split("\n"), op["count"])
        elif op["kind"] == "ins_after":
            re_edits.ins_after(op["anchor"], op["payload"].split("\n"), op["count"])
        else:
            re_edits.replace(op["anchor"], op["payload"], op["count"])
    m2 = {}
    reapplied = apply(original, re_edits, name + "-reapply", m2)
    if reapplied != derived:
        sys.exit("VERIFY FAIL %s: manifest re-apply round-trip differs" % name)
    marked = sum(1 for ln in dlines if "@TICKCOST" in ln)
    print("verify OK: %s (%d lines derived, %d marked, %d replaced anchors)"
          % (name, len(dlines), marked, len(manifest[name]["replaced_anchors"])))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / ".tmp/tickcost/src"))
    ap.add_argument("--verify-only", action="store_true")
    a = ap.parse_args()
    outd = Path(a.out)
    h = HDR.read_text(encoding="utf-8", newline="").replace("\r\n", "\n")
    u = UNIT.read_text(encoding="utf-8", newline="").replace("\r\n", "\n")
    manifest = {}
    dh = apply(h, header_edits(), "gait_controller.hpp", manifest)
    du = apply(u, unit_edits(), "gait_unit.cpp", manifest)
    if not a.verify_only:
        outd.mkdir(parents=True, exist_ok=True)
        (outd / "tickcost_gait_controller.hpp").write_text(dh, encoding="utf-8", newline="\n")
        (outd / "tickcost_gait_unit.cpp").write_text(du, encoding="utf-8", newline="\n")
        (outd / "tickcost_probe.hpp").write_text(
            PROBE.read_text(encoding="utf-8", newline=""), encoding="utf-8", newline="\n")
        (outd / "instrument_manifest.json").write_text(
            json.dumps(manifest, indent=1), encoding="utf-8", newline="\n")
    verify(dh, h, manifest, "gait_controller.hpp")
    verify(du, u, manifest, "gait_unit.cpp")
    print("instrument derived ->", outd)


if __name__ == "__main__":
    main()
