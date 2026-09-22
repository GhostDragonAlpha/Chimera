"""TypeB-P1 declared patch applier (Rule-0 declared instrument, prereg_typeb_p1.json).

Applies the M1 timing-instrument patch and/or the M1-minimized (census-stripped)
variant to ChimeraEngine/engine/tests_coupled_arm/gait_unit.cpp IN THE WORKING
TREE ONLY. Never committed; `git diff` captures it for the receipt; `git
checkout --` restores the ship bytes. Every anchor must match exactly once or
the script refuses (loudly) -- a silent partial patch is worse than no patch.

Usage:
  python apply_tb1_patch.py instrument    # timing + [tb1] per-tick series
  python apply_tb1_patch.py minimize      # instrument + strip status/census/dump
  python apply_tb1_patch.py restore       # git checkout -- the file
"""
import subprocess, sys

REPO = r"E:\ChimeraWork\tb1-agent"
SRC = REPO + r"\ChimeraEngine\engine\tests_coupled_arm\gait_unit.cpp"

NS = """
// ==== TYPEB-P1 DECLARED TIMING INSTRUMENT (working-tree patch, NEVER COMMITTED;
// stderr-only, stdout bytes unchanged -- prereg_typeb_p1.json M1/M2) ====
namespace tb1 {
struct Timing {
  double fG5=0, push426=0, report=0;
  double walk_startup=0, walk_step=0, walk_status=0, walk_census=0;
  double walk_step_ss=0, walk_status_ss=0, walk_census_ss=0; // ticks>=20 per run
  long long walk_ticks=0, walk_ticks_ss=0; int walk_runs=0;
  std::chrono::steady_clock::time_point t;
  void begin(){t=std::chrono::steady_clock::now();}
  double end(){return std::chrono::duration<double>(std::chrono::steady_clock::now()-t).count();}
};
inline Timing& tm(){static Timing x;return x;}
inline void summary(){
  Timing&T=tm();const long long n=T.walk_ticks,ns=T.walk_ticks_ss;
  std::fprintf(stderr,"[tb1-timing] runs=%d ticks=%lld ss_ticks=%lld startup_s=%.3f step_s=%.3f status_s=%.3f census_s=%.3f fG5_s=%.3f push426_s=%.3f report_s=%.3f\\n",
    T.walk_runs,n,ns,T.walk_startup,T.walk_step,T.walk_status,T.walk_census,T.fG5,T.push426,T.report);
  if(n){std::fprintf(stderr,"[tb1-timing] per_tick_ms step=%.4f status=%.4f census=%.4f | ticks_per_s_step_only=%.2f ticks_per_s_full_loop=%.2f | ss(t>=20) step_only=%.2f full_loop=%.2f\\n",
    1e3*T.walk_step/n,1e3*T.walk_status/n,1e3*T.walk_census/n,
    n/T.walk_step,n/(T.walk_step+T.walk_status+T.walk_census),
    ns?ns/T.walk_step_ss:0.,ns?ns/(T.walk_step_ss+T.walk_status_ss+T.walk_census_ss):0.);}
}
}
// ==== END TYPEB-P1 INSTRUMENT ====
int main(int argc,char**argv){try{"""

A_FG5_BEGIN = ' std::fprintf(stderr,"run F-G5\\n");\n'
A_FG5_END = 'std::fprintf(stderr,"F-G5 refused: %s\\n",e.what());}\n'
A_WR_BEGIN = ' auto walk_run=[&](bool capture){\n  GaitWalker d(data,9.80665,V{0,0,0},dt);\n  d.configure({{"capture_enabled",capture},{"reset",true}});\n'
A_TICK = '  for(int i=0;i<WALK;++i){\n   try{\n    d.step();\n'
A_STATUS = '   auto s=d.status();\n   // WAVE 13 fore-paw census'
A_CENSUS_END = 'out.a.push_back(a);out.tg.push_back(tg);out.t.push_back(tt);out.r.push_back(rr);}\n'
A_RETURN = '  out.captures=d.capture_events();out.last=d.status();\n'
A_PUSH_BEGIN = ' {GaitWalker d(data,9.80665,V{0,0,0},dt);\n  d.configure({{"capture_enabled",false},{"reset",true}});\n  int refused=0;\n'
A_PUSH_END = '  ck(d.capture_events()==0,"f6_disarmed_no_capture");}\n'
A_REPORT = ' bool pass=reds==0;\n std::cout<<J'
A_REPORT_END = '{"measured",measured}}).dump(2)<<"\\n";\n'

TICK_INSTR = ('  for(int i=0;i<WALK;++i){\n'
              '   {auto&T=tb1::tm();T.begin();'
              'std::fprintf(stderr,"[tb1] run=%d tick=%d bx=%.6f by=%.6f\\n",T.walk_runs,i,d.angles()[3],d.angles()[4]);}\n'
              '   double t_step=0,t_stat=0,t_cen=0;{auto&T=tb1::tm();T.begin();}\n'
              '   try{\n    d.step();\n'
              '   {auto&T=tb1::tm();double e=T.end();T.walk_step+=e;if(i>=20)T.walk_step_ss+=e;}\n')

STATUS_INSTR = ('   tb1::tm().begin();\n'
                '   auto s=d.status();\n'
                '   {auto&T=tb1::tm();double e=T.end();T.walk_status+=e;if(i>=20)T.walk_status_ss+=e;}\n'
                '   tb1::tm().begin();\n'
                '   // WAVE 13 fore-paw census')

CENSUS_INSTR = ('out.a.push_back(a);out.tg.push_back(tg);out.t.push_back(tt);out.r.push_back(rr);\n'
                '   {auto&T=tb1::tm();double e=T.end();T.walk_census+=e;if(i>=20){T.walk_census_ss+=e;++T.walk_ticks_ss;}'
                '++T.walk_ticks;}}\n')

SUMMARY = ('  {auto&T=tb1::tm();(void)T;tb1::summary();}\n'
           '  out.captures=d.capture_events();out.last=d.status();\n')

def rd():
    with open(SRC, "r", encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")  # normalize CRLF -> LF for anchor math

def wr(s):
    with open(SRC, "w", encoding="utf-8", newline="") as f:
        f.write(s.replace("\n", "\r\n"))  # write back CRLF (the file is fully CRLF)

def sub1(s, anchor, repl):
    n = s.count(anchor)
    if n != 1:
        sys.exit("ANCHOR FAIL (count=%d): %r" % (n, anchor[:70]))
    return s.replace(anchor, repl)

def main():
    mode = sys.argv[1]
    if mode == "restore":
        subprocess.run(["git", "-C", REPO, "checkout", "--",
                        "ChimeraEngine/engine/tests_coupled_arm/gait_unit.cpp"], check=True)
        print("RESTORED ship bytes")
        return
    minimize = mode == "minimize"
    s = rd()
    # idempotence guard
    if "TYPEB-P1 DECLARED TIMING INSTRUMENT" in s:
        sys.exit("patch already applied")
    # 1. namespace before main
    s = sub1(s, "int main(int argc,char**argv){try{", NS)
    # 2. F-G5 block timer
    s = sub1(s, A_FG5_BEGIN, ' tb1::tm().begin();\n' + A_FG5_BEGIN)
    s = sub1(s, A_FG5_END, 'std::fprintf(stderr,"F-G5 refused: %s\\n",e.what());}\n tb1::tm().fG5+=tb1::tm().end();\n')
    # 3. walk_run startup timer + run counter
    s = sub1(s, A_WR_BEGIN, ' auto walk_run=[&](bool capture){\n  {auto&T=tb1::tm();T.begin();}\n'
             '  GaitWalker d(data,9.80665,V{0,0,0},dt);\n  d.configure({{"capture_enabled",capture},{"reset",true}});\n'
             '  {auto&T=tb1::tm();T.walk_startup+=T.end();++T.walk_runs;}\n')
    # 4. per-tick: [tb1] series print + step timer
    s = sub1(s, A_TICK, TICK_INSTR)
    if minimize:
        # strip status + census + dump; keep the loop close
        i = s.index(A_STATUS)
        j = s.index(A_CENSUS_END) + len(A_CENSUS_END)
        s = s[:i] + "   ++tb1::tm().walk_ticks;\n" + s[j:]
        # the loop close brace was consumed with the block; re-add
        s = sub1(s, "   ++tb1::tm().walk_ticks;\n  out.captures=",
                 "   ++tb1::tm().walk_ticks;\n  }\n  out.captures=")
    else:
        s = sub1(s, A_STATUS, STATUS_INSTR)
        s = sub1(s, A_CENSUS_END, CENSUS_INSTR)
    # 5. summary before the post-loop status
    s = sub1(s, A_RETURN, SUMMARY)
    # 6. push-run timer
    s = sub1(s, A_PUSH_BEGIN, ' tb1::tm().begin();\n' + A_PUSH_BEGIN)
    s = sub1(s, A_PUSH_END, '  ck(d.capture_events()==0,"f6_disarmed_no_capture");}\n tb1::tm().push426+=tb1::tm().end();\n')
    # 7. report timer
    s = sub1(s, A_REPORT, ' tb1::tm().begin();\n bool pass=reds==0;\n std::cout<<J')
    s = sub1(s, A_REPORT_END, '{"measured",measured}}).dump(2)<<"\\n";\n tb1::tm().report+=tb1::tm().end();\n')
    wr(s)
    print("PATCH APPLIED:", mode)

if __name__ == "__main__":
    main()
