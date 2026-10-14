"""make_fkred.py -- the FK-REDUCTION lane instrument/reduction generator.

Derives instrumented (census) and byte-neutral-reduction (reduce) copies of
gait_controller.hpp and gait_unit.cpp from the TRACKED bytes by DECLARED,
ANCHORED, single-occurrence edits (PREREG record.md, METHODS 1-2; the
tickcost make_instrument.py pattern). The tracked files are READ-ONLY: the
derived copies land under .tmp/fkred/src/ and nothing in the tree is modified.

Marker discipline: the //@FKRED marker is always a TRAILING comment on an
inserted or replaced line -- never a line prefix (the generator's verify
enforces this, same as the tickcost lane).

Guarantees enforced here (the generator refuses loudly otherwise):
  1. every anchor occurs EXACTLY the declared number of times;
  2. every derived line that is not an original line carries a TRAILING
     //@FKRED marker;
  3. re-applying the recorded edit manifest to the tracked source reproduces
     the derived file BYTE-EXACTLY (manifest round-trip);
  4. regeneration is deterministic (re-run => byte-identical outputs).

CENSUS mode (--census): integer bump counters at every GaitWalker::evaluate
call site (census_sites.md, FROZEN with the prereg) + call-site counters at
every free_step/impact/advance call site + a stderr-only per-walk-run report.
FP-neutral: integer increments, stderr-only, zero stdout bytes.

REDUCE mode (--reduce): ONLY the (a)-class byte-neutral reuses R1/R2/R3
(reduction_map.md, each with its purity + no-mutation proof):
  R1  rate() accepts a precomputed Evaluation for its state (reused by
      free_step's rate-a, which evaluates the SAME start state);
  R2  advance's estart (computed AFTER impact mutated the state) is passed
      into every free_step of the SAME advance call -- start is never
      mutated there, so evaluate(start) is input-identical at each site;
  R2b the clamp path's evaluate(start) == estart (same no-mutation proof);
  R3  the poscorr block reuses its own ec Evaluation for u_before and the
      arows rows (the state is not mutated between those reads).

Usage:
  python make_fkred.py --census [--out DIR]
  python make_fkred.py --reduce [--out DIR]

Trailer Agent: fkred.
"""
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]  # tools/science_funnel/validation/<lane> -> repo root
HDR = ROOT / "ChimeraEngine/engine/gait_controller.hpp"
UNIT = ROOT / "ChimeraEngine/engine/tests_coupled_arm/gait_unit.cpp"

M = " //@FKRED"  # the TRAILING marker


class Edits:
    def __init__(self):
        self.ops = []  # (kind, anchor, payload(list of str), count)

    def ins_before(self, anchor, lines, count=1):
        self.ops.append(("ins_before", anchor, lines, count)); return self

    def ins_after(self, anchor, lines, count=1):
        self.ops.append(("ins_after", anchor, lines, count)); return self

    def replace(self, old, new_lines, count=1):
        self.ops.append(("replace", old, new_lines, count)); return self


B = lambda s: ("  FKRED_SITE(%s);" % s) + M   # site bump line
C = lambda s: ("  FKRED_CALL(%s);" % s) + M   # call bump line


# ─────────────────────────────────────────────────────────────────────────────
# CENSUS edits (site table = census_sites.md, FROZEN with the prereg)
# ─────────────────────────────────────────────────────────────────────────────

def census_header_edits():
    e = Edits()
    e.ins_after("#pragma once", ['#include "fkred_probe.hpp"' + M])
    # -- wrapper-internal sites ---------------------------------------------
    e.replace(" double mechanical(const State& s)const{auto e=evaluate(s);return .5*inner(s.v,multiply(e.mass,s.v))+e.potential;}",
              [" double mechanical(const State& s)const{FKRED_SITE(S_MECH);auto e=evaluate(s);return .5*inner(s.v,multiply(e.mass,s.v))+e.potential;}" + M])
    e.replace(" void capture_paws(){\n  auto e=evaluate(s_);",
              [" void capture_paws(){" + M, B("S_CAP"), "  auto e=evaluate(s_);" + M])
    e.replace("  auto e=evaluate(s_);\n  auto sh=e.point(fore_mount_body_[leg],fore_mount_local_[leg]).first;",
              [B("S_FORE"), "  auto e=evaluate(s_);" + M,
               "  auto sh=e.point(fore_mount_body_[leg],fore_mount_local_[leg]).first;" + M])
    e.replace("if(!have_fe){fe=evaluate(s_);have_fe=true;}",
              ["if(!have_fe){FKRED_SITE(S_LAWFE);fe=evaluate(s_);have_fe=true;}" + M], count=4)
    # -- rate / free_step / impact / advance ----------------------------------
    e.replace(" Rate rate(const State& s,const Dense& tau,const std::vector<char>& live,const std::vector<char>& plane)const{\n  auto e=evaluate(s);auto inv=inverse_spd(e.mass,n_);",
              [" Rate rate(const State& s,const Dense& tau,const std::vector<char>& live,const std::vector<char>& plane)const{" + M,
               B("S_RATE"),
               "  auto e=evaluate(s);auto inv=inverse_spd(e.mass,n_);" + M])
    e.replace(" double impact(State& s)const{\n  auto e=evaluate(s);auto inv=inverse_spd(e.mass,n_);",
              [" double impact(State& s)const{" + M, B("S_IMP"),
               "  auto e=evaluate(s);auto inv=inverse_spd(e.mass,n_);" + M])
    e.replace("  if(contact_&&mu_>0){auto e0=evaluate(start);double gate=1e-6+1e-3*joint_speed_scale(start);",
              [B("S_FSE0"),
               "  if(contact_&&mu_>0){auto e0=evaluate(start);double gate=1e-6+1e-3*joint_speed_scale(start);" + M])
    e.replace("  auto p0=vector(evaluate(start).frames[0].t,V{},1),p1=vector(evaluate(end).frames[0].t,V{},1);",
              [B("S_FSP0"),
               "  auto p0=vector(evaluate(start).frames[0].t,V{},1);" + M,
               B("S_FSP1"),
               "  auto p1=vector(evaluate(end).frames[0].t,V{},1);" + M])
    e.replace("   {auto ec=evaluate(s);",
              [B("S_PCEC"), "   {auto ec=evaluate(s);" + M])
    e.replace("    double u_before=evaluate(s).potential;",
              [B("S_PCUB"), "    double u_before=evaluate(s).potential;" + M])
    e.replace("    std::vector<Dense> arows;for(size_t k:pen)arows.push_back(contact_row(evaluate(s),k));",
              ["    std::vector<Dense> arows;for(size_t k:pen){FKRED_SITE(S_PCAR);arows.push_back(contact_row(evaluate(s),k));}" + M])
    e.replace("     double du=evaluate(s).potential-u_before;",
              [B("S_PCDU"), "     double du=evaluate(s).potential-u_before;" + M])
    e.replace("  std::vector<char> live(npts_,0);auto estart=evaluate(start);",
              [B("S_ES"),
               "  std::vector<char> live(npts_,0);auto estart=evaluate(start);" + M])
    e.replace("  if(contact_){auto eend=evaluate(end);",
              ["  if(contact_){FKRED_SITE(S_EE);auto eend=evaluate(end);" + M])
    e.replace("    double u_pin=evaluate(pinned).potential-evaluate(start).potential;",
              [B("S_PIN1"),
               "    double u_pin_p=evaluate(pinned).potential;" + M,
               B("S_PIN2"),
               "    double u_pin=u_pin_p-evaluate(start).potential;" + M])
    e.replace('   require(std::abs(gap_of(evaluate(crossing),size_t(khit)))<1e-9,"gait_contact_localization");impact(crossing);',
              ["   FKRED_SITE(S_CROSS);FKRED_CALL(C_IMP_CROSS);require(std::abs(gap_of(evaluate(crossing),size_t(khit)))<1e-9,\"gait_contact_localization\");impact(crossing);" + M])
    # -- step() stage sites -----------------------------------------------------
    e.replace("  {auto e=evaluate(s_);if(walking)update_clock(e,dt_);else{for(size_t leg=0;leg<2;++leg)",
              ["  {FKRED_SITE(S_REFLEX);auto e=evaluate(s_);if(walking)update_clock(e,dt_);else{for(size_t leg=0;leg<2;++leg)" + M])
    e.replace("  {auto e=evaluate(s_);std::vector<std::pair<double,double>> hull,chain;V com{};",
              ["  {FKRED_SITE(S_HULL);auto e=evaluate(s_);std::vector<std::pair<double,double>> hull,chain;V com{};" + M])
    e.replace("  if(paws_captured_){auto e0=evaluate(s_);",
              ["  if(paws_captured_){FKRED_SITE(S_SAT);auto e0=evaluate(s_);" + M])
    e.replace(" J status()const{\n  auto e=evaluate(s_);",
              [" J status()const{" + M, B("S_STATUS"), "  auto e=evaluate(s_);" + M])
    e.replace("  double u0;{State r;r.q=model_->defaults;r.v=Dense(n_,0.);u0=evaluate(r).potential;}",
              ["  double u0;{FKRED_SITE(S_U0);State r;r.q=model_->defaults;r.v=Dense(n_,0.);u0=evaluate(r).potential;}" + M])
    e.replace('  auto e=evaluate(s_);\n  for(size_t leg=0;leg<2;++leg){bool touching=false;const char* prefix=leg==0?"left":"right";',
              [B("S_RESET"), "  auto e=evaluate(s_);" + M,
               '  for(size_t leg=0;leg<2;++leg){bool touching=false;const char* prefix=leg==0?"left":"right";' + M])
    # -- call-site counters -------------------------------------------------------
    e.replace("  double caught=impact(start);",
              ["  FKRED_CALL(C_IMP_ENT);double caught=impact(start);" + M])
    e.replace("  if(mu_>0&&caught>1e-9&&depth<5)return advance(advance(start,h/2,tau,depth+3),h/2,tau,depth+3);",
              ["  FKRED_CALL(C_CAUGHT);if(mu_>0&&caught>1e-9&&depth<5)return advance(advance(start,h/2,tau,depth+3),h/2,tau,depth+3);" + M])
    e.replace("  auto end=free_step(start,h,tau,live);int which=-1,khit=-1;double hit=h,wall=0;",
              ["  FKRED_CALL(C_FS_MAIN);auto end=free_step(start,h,tau,live);int which=-1,khit=-1;double hit=h,wall=0;" + M])
    e.replace("   for(int j=0;j<42;++j){double mid=(left+right)/2;double q=free_step(start,mid,tau,live).q[c];if(low?q<=bound:q>=bound)right=mid;else left=mid;}",
              ["   for(int j=0;j<42;++j){FKRED_CALL(C_FS_DRV);double mid=(left+right)/2;double q=free_step(start,mid,tau,live).q[c];if(low?q<=bound:q>=bound)right=mid;else left=mid;}" + M])
    e.replace("    for(int j=0;j<42;++j){double mid=(left+right)/2;if(gap_of(evaluate(free_step(start,mid,tau,probe)),k)<=0)right=mid;else left=mid;}",
              ["    for(int j=0;j<42;++j){FKRED_CALL(C_FS_CON);FKRED_SITE(S_BISECT_GAP);double mid=(left+right)/2;if(gap_of(evaluate(free_step(start,mid,tau,probe)),k)<=0)right=mid;else left=mid;}" + M])
    e.replace("   if(hit<=1e-12){",
              ["   if(hit<=1e-12){" + M, "   FKRED_CALL(C_CLAMP);" + M])
    e.replace("   impact(pinned);\n   return advance(pinned,h,tau,depth,clamps+1);}",
              ["   FKRED_CALL(C_IMP_PIN);impact(pinned);" + M,
               "   return advance(pinned,h,tau,depth,clamps+1);}" + M])
    e.replace("  if(which==-2&&khit>=0){auto probe=live;probe[size_t(khit)]=0;auto crossing=free_step(start,hit,tau,probe);",
              ["  if(which==-2&&khit>=0){FKRED_CALL(C_EVT_CON);FKRED_CALL(C_FS_CROSS);auto probe=live;probe[size_t(khit)]=0;auto crossing=free_step(start,hit,tau,probe);" + M])
    e.replace('  require(which>=0&&which<(int)nd_,"gait_event_namespace");size_t c=drives_[size_t(which)].coordinate;auto wall_state=free_step(start,hit,tau,live);',
              ["  require(which>=0&&which<(int)nd_,\"gait_event_namespace\");size_t c=drives_[size_t(which)].coordinate;FKRED_CALL(C_EVT_WALL);FKRED_CALL(C_FS_WALL);auto wall_state=free_step(start,hit,tau,live);" + M])
    e.replace('  require(std::abs(wall_state.q[c]-wall)<1e-9,"gait_impact_localization");wall_state.q[c]=wall;impact(wall_state);',
              ["  require(std::abs(wall_state.q[c]-wall)<1e-9,\"gait_impact_localization\");wall_state.q[c]=wall;FKRED_CALL(C_IMP_WALL);impact(wall_state);" + M])
    e.replace("   auto trial=advance(s_,dt_/4,effort());",
              ["   FKRED_CALL(C_ADV_TRIAL);auto trial=advance(s_,dt_/4,effort());" + M])
    e.replace("       auto candidate=advance(s_,dt_/4,effort());",
              ["       FKRED_CALL(C_ADV_BISECT);auto candidate=advance(s_,dt_/4,effort());" + M])
    e.replace("    trial=advance(s_,dt_/4,effort());",
              ["    FKRED_CALL(C_ADV_RETRY);trial=advance(s_,dt_/4,effort());" + M])
    return e


def census_unit_edits():
    e = Edits()
    e.replace('#include "../gait_controller.hpp"',
              ['#include "fkred_gait_controller.hpp"' + M])
    e.ins_before("  for(int i=0;i<WALK;++i){", ["  fkred::reset();" + M])
    e.ins_before("  out.captures=d.capture_events();out.last=d.status();\n  return out;};",
                 ['  fkred::report("walk_run");' + M])
    return e


# ─────────────────────────────────────────────────────────────────────────────
# REDUCE edits (the (a)-class byte-neutral reuses R1/R2/R2b/R3)
# ─────────────────────────────────────────────────────────────────────────────

def reduce_header_edits():
    e = Edits()
    # R1: rate() takes the caller's precomputed Evaluation for its state.
    # PROOF: Model::evaluate is a pure function of (q,v,gravity) with no
    # statics/RNG (coupled_articulation.hpp 82-91); rate() only reads e; the
    # only rate() caller is free_step, whose rate-a evaluates the SAME start
    # state free_step's e0 already evaluated -- identical inputs, therefore
    # bit-identical Evaluation. b/c/d pass nullptr => original behavior.
    e.replace(" Rate rate(const State& s,const Dense& tau,const std::vector<char>& live,const std::vector<char>& plane)const{\n  auto e=evaluate(s);auto inv=inverse_spd(e.mass,n_);",
              [" Rate rate(const State& s,const Dense& tau,const std::vector<char>& live,const std::vector<char>& plane,const Evaluation* e_pre)const{" + M,
               "  Evaluation e_local;if(e_pre==nullptr)e_local=evaluate(s);const Evaluation& e=e_pre?*e_pre:e_local;auto inv=inverse_spd(e.mass,n_);" + M])
    # R2: free_step takes the caller advance's estart for ALL its reads of
    # `start`. PROOF: start is passed by const& and never mutated between
    # estart and every free_step of the same advance (shifted() copies;
    # impact() mutates BEFORE estart is computed; the event search only
    # reads), so evaluate(start) at e0/rate-a/p0 is input-identical to estart.
    e.replace(" State free_step(const State& start,double h,const Dense& tau,const std::vector<char>& live)const{",
              [" State free_step(const State& start,double h,const Dense& tau,const std::vector<char>& live,const Evaluation& e_start)const{" + M])
    e.replace("  if(contact_&&mu_>0){auto e0=evaluate(start);double gate=1e-6+1e-3*joint_speed_scale(start);",
              ["  if(contact_&&mu_>0){const Evaluation& e0=e_start;double gate=1e-6+1e-3*joint_speed_scale(start);" + M])
    e.replace("  auto a=rate(start,tau,live,plane),b=rate(shifted(a,h/2),tau,live,plane),c=rate(shifted(b,h/2),tau,live,plane),d=rate(shifted(c,h),tau,live,plane);",
              ["  auto a=rate(start,tau,live,plane,&e_start),b=rate(shifted(a,h/2),tau,live,plane,nullptr),c=rate(shifted(b,h/2),tau,live,plane,nullptr),d=rate(shifted(c,h),tau,live,plane,nullptr);" + M])
    e.replace("  auto p0=vector(evaluate(start).frames[0].t,V{},1),p1=vector(evaluate(end).frames[0].t,V{},1);",
              ["  auto p0=vector(e_start.frames[0].t,V{},1),p1=vector(evaluate(end).frames[0].t,V{},1);" + M])
    # every free_step caller inside advance passes estart
    e.replace("  auto end=free_step(start,h,tau,live);int which=-1,khit=-1;double hit=h,wall=0;",
              ["  auto end=free_step(start,h,tau,live,estart);int which=-1,khit=-1;double hit=h,wall=0;" + M])
    e.replace("   for(int j=0;j<42;++j){double mid=(left+right)/2;double q=free_step(start,mid,tau,live).q[c];if(low?q<=bound:q>=bound)right=mid;else left=mid;}",
              ["   for(int j=0;j<42;++j){double mid=(left+right)/2;double q=free_step(start,mid,tau,live,estart).q[c];if(low?q<=bound:q>=bound)right=mid;else left=mid;}" + M])
    e.replace("    for(int j=0;j<42;++j){double mid=(left+right)/2;if(gap_of(evaluate(free_step(start,mid,tau,probe)),k)<=0)right=mid;else left=mid;}",
              ["    for(int j=0;j<42;++j){double mid=(left+right)/2;if(gap_of(evaluate(free_step(start,mid,tau,probe,estart)),k)<=0)right=mid;else left=mid;}" + M])
    e.replace("  if(which==-2&&khit>=0){auto probe=live;probe[size_t(khit)]=0;auto crossing=free_step(start,hit,tau,probe);",
              ["  if(which==-2&&khit>=0){auto probe=live;probe[size_t(khit)]=0;auto crossing=free_step(start,hit,tau,probe,estart);" + M])
    e.replace('  require(which>=0&&which<(int)nd_,"gait_event_namespace");size_t c=drives_[size_t(which)].coordinate;auto wall_state=free_step(start,hit,tau,live);',
              ["  require(which>=0&&which<(int)nd_,\"gait_event_namespace\");size_t c=drives_[size_t(which)].coordinate;auto wall_state=free_step(start,hit,tau,live,estart);" + M])
    # the GAIT_EVENT_TRACE-only free_step(pinned,...) call: pinned is a LOCAL
    # state with no precomputed evaluation -- evaluate it fresh (the SAME
    # arithmetic as the original; a debug-only path, +1 evaluate there).
    e.replace("   auto endp=free_step(pinned,h,tau,live);",
              ["   auto endp=free_step(pinned,h,tau,live,evaluate(pinned));" + M])
    # R2b: the clamp path's evaluate(start) == estart (start unmutated).
    e.replace("    double u_pin=evaluate(pinned).potential-evaluate(start).potential;",
              ["    double u_pin=evaluate(pinned).potential-estart.potential;" + M])
    # R3: the poscorr block reuses its own ec for u_before and the arows.
    # PROOF: s is not mutated between ec and u_before/arows; du still
    # evaluates AFTER the q correction. Pure function => bit-identical.
    e.replace("   {auto ec=evaluate(s);\n    for(size_t k=0;k<npts_;++k){if(!sole_representative(k))continue;double g=gap_of(ec,k);if(g<-1e-6){pen.push_back(k);gaps.push_back(g);}}}",
              ["   const Evaluation& ec=evaluate(s);" + M,
               "    for(size_t k=0;k<npts_;++k){if(!sole_representative(k))continue;double g=gap_of(ec,k);if(g<-1e-6){pen.push_back(k);gaps.push_back(g);}}" + M])
    e.replace("    double u_before=evaluate(s).potential;\n    std::vector<Dense> arows;for(size_t k:pen)arows.push_back(contact_row(evaluate(s),k));",
              ["    double u_before=ec.potential;" + M,
               "    std::vector<Dense> arows;for(size_t k:pen)arows.push_back(contact_row(ec,k));" + M])
    return e


def reduce_unit_edits():
    e = Edits()
    e.replace('#include "../gait_controller.hpp"',
              ['#include "fkred_gait_controller.hpp"' + M])
    return e


# ─────────────────────────────────────────────────────────────────────────────
# apply/verify (the tickcost machinery, verbatim discipline)
# ─────────────────────────────────────────────────────────────────────────────

def apply(text, edits, name, manifest):
    replaced = []
    for kind, anchor, payload, count in edits.ops:
        n = text.count(anchor)
        if n != count:
            sys.exit("ANCHOR FAIL in %s (count=%d, want %d): %r" % (name, n, count, anchor[:100]))
    ops = []
    for kind, anchor, payload, count in edits.ops:
        start = 0
        for _ in range(count):
            i = text.index(anchor, start)
            if kind == "ins_before":
                ops.append((i, i, 1, kind, anchor, payload))
            elif kind == "ins_after":
                ops.append((i + len(anchor), i, 1, kind, anchor, payload))
            else:
                ops.append((i, i + len(anchor), 0, kind, anchor, payload))
            start = i + 1
    ops.sort(key=lambda t: (-t[0], t[2]))
    buf = text
    for pos, end, _o, kind, anchor, payload in ops:
        joined = "\n".join(payload)
        if kind == "replace":
            buf = buf[:pos] + joined + buf[end:]
            replaced.append(anchor)
        elif kind == "ins_before":
            buf = buf[:pos] + joined + "\n" + buf[pos:]
        else:
            ins_at = pos - 1 if pos > 0 and buf[pos - 1] == "\n" else pos
            buf = buf[:ins_at] + "\n" + joined + buf[ins_at:]
    manifest[name] = {"ops": [
        {"kind": k, "anchor": a, "payload": "\n".join(p), "count": c}
        for k, a, p, c in edits.ops],
        "replaced_anchors": replaced}
    return buf


def verify(derived, original, manifest, name):
    dlines = derived.split("\n")
    orig_lines = set(original.split("\n"))
    for ln in dlines:
        if ln in orig_lines:
            continue
        if "@FKRED" not in ln:
            sys.exit("VERIFY FAIL %s: unmarked new line %r" % (name, ln[:100]))
        if ln.lstrip().startswith("//@FKRED"):
            sys.exit("VERIFY FAIL %s: leading marker comments out code: %r" % (name, ln[:100]))
    re_edits = Edits()
    for op in manifest[name]["ops"]:
        if op["kind"] == "ins_before":
            re_edits.ins_before(op["anchor"], op["payload"].split("\n"), op["count"])
        elif op["kind"] == "ins_after":
            re_edits.ins_after(op["anchor"], op["payload"].split("\n"), op["count"])
        else:
            re_edits.replace(op["anchor"], op["payload"].split("\n"), op["count"])
    m2 = {}
    reapplied = apply(original, re_edits, name + "-reapply", m2)
    if reapplied != derived:
        sys.exit("VERIFY FAIL %s: manifest re-apply round-trip differs" % name)
    # brace/paren DELTA guard: every edit here is statement-level, so the net
    # {} () [] balance of the derived text must equal the original's (this
    # catches a marker commenting out a line tail -- the mechanical(20260920)
    # failure the compile then caught independently).
    for o, c, nm in [("{", "}", "braces"), ("(", ")", "parens"), ("[", "]", "brackets")]:
        d = (derived.count(o) - derived.count(c)) - (original.count(o) - original.count(c))
        if d != 0:
            sys.exit("VERIFY FAIL %s: net %s balance moved by %+d" % (name, nm, d))
    marked = sum(1 for ln in dlines if "@FKRED" in ln)
    print("verify OK: %s (%d lines derived, %d marked, %d replaced anchors)"
          % (name, len(dlines), marked, len(manifest[name]["replaced_anchors"])))


PROBE = r'''// fkred_probe.hpp -- the FK-REDUCTION census counters (lane
// lane/fk-reduction-20260920). Included ONLY by the derived census copy under
// .tmp/fkred/src/ -- the tracked engine bytes are never modified. Integer
// bumps + a stderr-only report: FP-neutral, zero stdout bytes. The site enum
// is FROZEN in census_sites.md (PREREG). Trailer Agent: fkred.
#pragma once
#include <cstdint>
#include <cstdio>
namespace fkred {
enum Site { S_MECH, S_CAP, S_FORE, S_LAWFE, S_RATE, S_FSE0, S_FSP0, S_FSP1,
 S_IMP, S_PCEC, S_PCUB, S_PCAR, S_PCDU, S_ES, S_EE, S_PIN1, S_PIN2, S_CROSS,
 S_BISECT_GAP, S_REFLEX, S_HULL, S_SAT, S_STATUS, S_U0, S_RESET, SITE_COUNT };
enum Call { C_FS_MAIN, C_FS_DRV, C_FS_CON, C_FS_CROSS, C_FS_WALL,
 C_IMP_ENT, C_IMP_PIN, C_IMP_CROSS, C_IMP_WALL,
 C_ADV_TRIAL, C_ADV_BISECT, C_ADV_RETRY, C_CAUGHT, C_CLAMP, C_EVT_CON,
 C_EVT_WALL, CALL_COUNT };
static const char* SITE_NAME[SITE_COUNT] = {
 "S_MECH","S_CAP","S_FORE","S_LAWFE","S_RATE","S_FSE0","S_FSP0","S_FSP1",
 "S_IMP","S_PCEC","S_PCUB","S_PCAR","S_PCDU","S_ES","S_EE","S_PIN1","S_PIN2",
 "S_CROSS","S_BISECT_GAP","S_REFLEX","S_HULL","S_SAT","S_STATUS","S_U0","S_RESET"};
static const char* CALL_NAME[CALL_COUNT] = {
 "C_FS_MAIN","C_FS_DRV","C_FS_CON","C_FS_CROSS","C_FS_WALL",
 "C_IMP_ENT","C_IMP_PIN","C_IMP_CROSS","C_IMP_WALL",
 "C_ADV_TRIAL","C_ADV_BISECT","C_ADV_RETRY","C_CAUGHT","C_CLAMP","C_EVT_CON",
 "C_EVT_WALL"};
inline unsigned long long g_site[SITE_COUNT];
inline unsigned long long g_call[CALL_COUNT];
inline void reset(){for(int i=0;i<SITE_COUNT;++i)g_site[i]=0;for(int i=0;i<CALL_COUNT;++i)g_call[i]=0;}
inline void report(const char* phase){
  unsigned long long tot=0;
  for(int i=0;i<SITE_COUNT;++i)tot+=g_site[i];
  std::fprintf(stderr,"[fkred] phase=%s evaluates_total=%llu\n",phase,tot);
  for(int i=0;i<SITE_COUNT;++i)
    std::fprintf(stderr,"[fkred] phase=%s site=%s n=%llu\n",phase,SITE_NAME[i],g_site[i]);
  for(int i=0;i<CALL_COUNT;++i)
    std::fprintf(stderr,"[fkred] phase=%s call=%s n=%llu\n",phase,CALL_NAME[i],g_call[i]);
  reset();
}
}
#define FKRED_SITE(x) (++::fkred::g_site[::fkred::x])
#define FKRED_CALL(x) (++::fkred::g_call[::fkred::x])
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--census", action="store_true")
    ap.add_argument("--reduce", action="store_true")
    ap.add_argument("--out", default=str(ROOT / ".tmp/fkred/src"))
    a = ap.parse_args()
    if a.census == a.reduce:
        sys.exit("pick exactly one of --census / --reduce")
    outd = Path(a.out)
    h = HDR.read_text(encoding="utf-8", newline="").replace("\r\n", "\n")
    u = UNIT.read_text(encoding="utf-8", newline="").replace("\r\n", "\n")
    manifest = {}
    if a.census:
        dh = apply(h, census_header_edits(), "gait_controller.hpp", manifest)
        du = apply(u, census_unit_edits(), "gait_unit.cpp", manifest)
    else:
        dh = apply(h, reduce_header_edits(), "gait_controller.hpp", manifest)
        du = apply(u, reduce_unit_edits(), "gait_unit.cpp", manifest)
    outd.mkdir(parents=True, exist_ok=True)
    if a.census:
        (outd / "fkred_probe.hpp").write_text(PROBE, encoding="utf-8", newline="\n")
    (outd / "fkred_gait_controller.hpp").write_text(dh, encoding="utf-8", newline="\n")
    (outd / "fkred_gait_unit.cpp").write_text(du, encoding="utf-8", newline="\n")
    (outd / "fkred_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8", newline="\n")
    verify(dh, h, manifest, "gait_controller.hpp")
    verify(du, u, manifest, "gait_unit.cpp")
    print("fkred derived ->", outd, ("(census)" if a.census else "(reduce)"))


if __name__ == "__main__":
    main()
