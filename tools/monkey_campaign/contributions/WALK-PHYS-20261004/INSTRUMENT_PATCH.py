#!/usr/bin/env python3
"""Build the WALKPHYS instrument: byte-copy of pinned blob a7bfe15e plus the
env-gated, default-OFF telemetry/control hooks (WALK-PHYS-20261004).

Law: with every GAITPHYS_* environment variable unset, no existing byte of
stdout/stderr/qstream changes and no code path changes (the P1 anchor law).
Telemetry goes to FILES only; no new stdout/stderr output exists in any mode.

The source of record is CRLF; every anchor/hook below is written with \n and
translated to CRLF before use, so the patched file keeps CRLF throughout.
"""
import sys
from pathlib import Path

ORIG = Path(sys.argv[1])
OUT = Path(sys.argv[2])
src = ORIG.read_text(encoding="utf-8", newline="")


def CRLF(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\n", "\r\n")


def patch(name: str, anchor: str, hook: str) -> None:
    global src
    a, h = CRLF(anchor), CRLF(hook)
    n = src.count(a)
    assert n == 1, f"{name}: anchor count {n} != 1"
    src = src.replace(a, h)


# ---------------------------------------------------------------- hook 1
patch("hook1-gaitphys-block",
""" int checks=0;int reds=0;std::vector<std::string> measured;""",
""" // ── WALKPHYS INSTRUMENT (WALK-PHYS-20261004; prereg
 // b4326a0971326db3d6267c9e00a9372ce33707d084b11a897417406e319de3fe):
 // env-gated, default-OFF additions ONLY. Unset envs -> byte-identical
 // stdout/stderr/qstream (the P1 anchor law). Telemetry goes to FILES.
 auto wp_env_int=[&](const char* n,int dflt)->int{
  const char* v=std::getenv(n);return (v&&v[0])?std::atoi(v):dflt;};
 const char* wp_tel_path=std::getenv("GAITPHYS_TELEMETRY");
 const int wp_cut=wp_env_int("GAITPHYS_POWER_CUT_TICK",-1);
 const int wp_inj=wp_env_int("GAITPHYS_INJECT_TICK",-1);
 const int wp_max=wp_env_int("GAITPHYS_MAX_TICKS",-1);
 const Dense* wp_speeds=nullptr; // the current run's speed vector
 std::ofstream wp_tel;int wp_run_ord=0;std::string wp_tag;
 auto wp_emit=[&](int i,const J& s){
  if(!wp_tel.is_open()||!wp_speeds)return;
  const Dense& vv=*wp_speeds;
  J row{{"run",wp_tag},{"tick",i},
        {"base_v",{vv[3],vv[4],vv[5]}},
        {"contact",s["contact"]},
        {"support",J{
          {"east",number(s["support"]["com_projection_east_m"])},
          {"south",number(s["support"]["com_projection_south_m"])},
          {"up",number(s["support"]["com_up_m"])},
          {"in_hull",s["support"]["com_in_hull"]},
          {"hull_size",s["support"]["hull_size"]},
          {"mass_kg",number(s["support"]["assembly_mass_kg"])}}},
        {"energy",s["energy"]},{"joints",s["joints"]}};
  wp_tel<<row.dump()<<'\\n';};
 int checks=0;int reds=0;std::vector<std::string> measured;""")

# ---------------------------------------------------------------- hook 2
patch("hook2-walkrun-entry",
"""  const int WALK=10*CYCLE_TICKS;
  WalkOut out;bool prev_t[2]={false,false};int w_ledger_first=-1;double w_ledger_prev=0;""",
"""  const int WALK=10*CYCLE_TICKS;
  ++wp_run_ord;wp_tag="w"+std::to_string(wp_run_ord);
  wp_speeds=&d.speeds();
  if(wp_tel_path&&wp_tel_path[0]&&!wp_tel.is_open())
   wp_tel.open(wp_tel_path,std::ios::binary|std::ios::app);
  WalkOut out;bool prev_t[2]={false,false};int w_ledger_first=-1;double w_ledger_prev=0;""")

# ---------------------------------------------------------------- hook 3
patch("hook3-control-hooks",
"""    d.configure({{"commanded_target_velocity_x",cmd_sched[cmd_i].second}});++cmd_i;} // zero-order hold from this tick boundary
   try{""",
"""    d.configure({{"commanded_target_velocity_x",cmd_sched[cmd_i].second}});++cmd_i;} // zero-order hold from this tick boundary
   // WALKPHYS hooks (env-gated; unset -> no-ops):
   if(wp_cut>=0&&i==wp_cut)d.configure({{"power",false}}); // P6 declared drive-cut arm
   if(wp_inj>=0&&i==wp_inj){const_cast<Dense&>(d.speeds())[3]+=0.05;} // P9 declared state-write probe via the public accessor
   try{""")

# ---------------------------------------------------------------- hook 4
patch("hook4-max-ticks",
"""    std::fprintf(stderr,"%s\\n",b);break;}
   }
   catch(const Refusal&e){""",
"""    std::fprintf(stderr,"%s\\n",b);break;}
   if(wp_max>=0&&i+1>=wp_max){out.refused="GAITPHYS_MAX_TICKS reached";out.refused_tick=i;break;}
   }
   catch(const Refusal&e){""")

# ---------------------------------------------------------------- hook 5
patch("hook5-telemetry-emit",
"""   auto s=d.status();
   // WAVE 13 fore-paw census: every tick, per-leg worst/best gap over the""",
"""   auto s=d.status();
   wp_emit(i,s); // WALKPHYS telemetry (file-only; env-gated)
   // WAVE 13 fore-paw census: every tick, per-leg worst/best gap over the""")

# ---------------------------------------------------------------- hook 6
patch("hook6-close",
"""  if(const char* dp2=std::getenv("GAIT_STATE_DUMP2");dp2&&dp2[0]){std::ofstream f2(dp2,std::ios::binary);f2<<w2.qstream;}}""",
"""  if(const char* dp2=std::getenv("GAIT_STATE_DUMP2");dp2&&dp2[0]){std::ofstream f2(dp2,std::ios::binary);f2<<w2.qstream;}}
 if(wp_tel.is_open())wp_tel.close(); // WALKPHYS: flush telemetry before the summary""")

OUT.write_text(src, encoding="utf-8", newline="")
print("wrote", OUT, len(src), "bytes")
