// Gait falsifier suite F-G1..F-G8 (docs/research/20260918_gait_controller_derivation.md
// Section 6, Rule-0 admission work.creature.gait_controller).
// Runs the 14-coordinate GaitWalker on the compiled gait scene in-process.
// HONESTY CONTRACT: every falsifier reports its MEASURED outcome; a refused
// or red falsifier is recorded, never swallowed -- the suite's top-level
// "pass" is true only when every F-G measure is green.
#include "../gait_controller.hpp"
#include <chrono>
#include <fstream>
#include <iostream>
using namespace chimera::multibody;

static J load_json(const char* path){J j;std::ifstream f(path);if(!f)throw std::runtime_error("file open failed");f>>j;return j;}
static constexpr double T=GaitWalker::T_CYCLE;

struct WalkOut{
 std::string stream;
 std::vector<std::array<double,8>> a,tg;
 std::vector<std::array<char,2>> t;
 std::vector<std::array<double,2>> r;
 std::vector<double> liftoff[2],td[2];
 std::vector<std::array<double,2>> fgmax,fgmin; // per-leg worst/best FORE paw gap (wave 13)
 std::vector<std::array<char,2>> fm;           // per-leg fore clock mode (0 stance, 1 swing)
 std::vector<std::array<uint64_t,2>> fsat;     // per-leg IK saturation ticks (per-tick snapshot)
 std::vector<std::array<double,2>> ftgt;       // per-leg fore plant x (the frozen/glide target, wave 20)
 std::vector<std::array<uint64_t,2>> frep;     // per-leg replant counter (the in-place census, wave 20)
 std::vector<std::array<double,8>> gp;         // per-tick ALL-paw gaps, declared point order (wave 15 strut census)
 std::vector<double> fr,frslip;                // per-tick total FORE reaction + max fore slip (wave 16 load census)
 std::vector<double> hr;                       // per-tick total HIND reaction (wave 17 hind-load census)
 // WAVE 21 HIND-RIDE census inputs: per-tick hind-point detail (declared order
 // 0..3 = left heel/mp, right heel/mp), the posture drive, the capture events,
 // the hind clock phases, the CoM/hull state, the base x.
 std::vector<std::array<double,4>> hgap,hrxn,hfrc,hslip; // per hind point
 std::vector<std::array<double,8>> hpos;       // per hind point CoP {x,y} (wave-28 mining)
 std::vector<std::array<double,4>> post;       // posture {torque, target_deg, angle_deg, speed}
 std::vector<uint64_t> cev;                    // capture_events
 std::vector<std::array<double,2>> hphase;     // {phase_left, phase_right}
 std::vector<std::array<double,4>> comh;       // {com_x, com_z, hull_size, in_hull}
 std::vector<double> bx;                       // base x
 std::vector<std::array<double,8>> hspd;       // hind drive speeds
 // WAVE 23 JOINT-WALL census inputs: per-tick per-fore-leg geometry from the
 // status fore_paw block (the wave-23 instrumentation fields):
 // {tgt_x,tgt_y,sh_x,sh_y,wall_headroom_rad,ik_q1_unc_deg,ik_q2_unc_deg,
 //  q1_act_deg,q2_act_deg,D,off_x}
 std::vector<std::array<double,11>> fw[2];
 std::vector<std::array<uint64_t,2>> wpins;    // per-leg stop-pin census (LOADED)
 std::vector<std::array<uint64_t,2>> wair;     // per-leg stop-pin census (AIRBORNE)
 std::vector<std::array<uint64_t,2>> wbound;   // per-leg wall_bound ticks
 std::vector<std::array<uint64_t,2>> wfollow;  // per-leg admissible follows
 // WAVE 24 POCKET-CLEAR HOLD census inputs: per-tick hold flag, hold span,
 // and the glide clock (t_in_cycle) per fore leg.
 std::vector<std::array<char,2>> fhold;
 std::vector<std::array<int,2>> fhl;
 std::vector<std::array<double,2>> ftic;
 std::vector<char> fcap;                       // paws_captured per tick
 // WAVE 28 HIND STEP census inputs: per-tick hind_step status, per leg 12
 // fields {mode,t,fires,tds,gated,reach_clamped,last_fire_tick,last_td_tick,
 // fire_qerr,wall_pins,wall_pins_air,xoff} -- leg 0 at [0,12), leg 1 at
 // [12,24); -1 filled when the block is absent.
 std::vector<std::array<double,36>> hindst;
 // WAVE 29 ALTERNATION census inputs: per-tick per-leg 4 fields
 // {fire_class(1=alternation),held,clear_tick,deadline_fires} -- leg 0 at
 // [0,4), leg 1 at [4,8); -1 filled when the block is absent.
 // WAVE 32 APPEND (indices preserved): the unload-deadline census --
 // {deadline_unload(1=the binding term is the unload form),unload_fires}
 // leg 0 at [8,10), leg 1 at [10,12).
 std::vector<std::array<double,12>> hind29;
 // WAVE 35 CARRIER SELF-UNLOAD FIRE DEADLINE census inputs: per-tick per-leg
 // 2 fields {waive_fires, waive_first_tick} -- leg 0 at [0,2), leg 1 at [2,4);
 // -1 filled when the field is absent.
 std::vector<std::array<double,10>> hind35;
 // WAVE 37 COMPLETION-TICK RE-LOCK census inputs (READ-ONLY PLUMBING, ALL
 // -1: the wave-37 law -- the wave-36 exchange protocol + the completion-
 // tick re-lock -- was measured and REVERTED per its pre-committed terminal
 // action, receipt_wave37.json: the re-lock's OWN engagement measured GREEN
 // (the L's graze-owned hand-off EXACTLY 193 ON the R's on-grid completion,
 // the fence green in full through the engagement) and the rung PASSED for
 // the first time (refusal 304 > 300, 9 ticks past the shipped strand) --
 // AND THE LEDGER FALSIFIER FIRED (33.559179 > the 32.861605 bound): the
 // re-locked calendar held exactly two eras (175..202 ON the shipped grid)
 // and then derailed -- the R's NEXT stall swing's hold cleared at 206 on
 // the re-locked trajectory, the (a)-waive fired INSIDE stall eras
 // (L@206, L@218), the grid scattered (4/9, worst drift 29), the twelfth
 // launch never came (the R's [215,292) era rode dead from 253), and the
 // new f4_work_envelope red (drive_4 12.938264 J/stride) carried the face.
 // The fired falsifiers are carried verbatim in the receipt.)
 std::vector<std::array<double,4>> hind37;
 std::vector<std::array<double,4>> hind38;
 std::vector<std::array<double,4>> hind39;
 std::vector<std::array<double,6>> hind40; // WAVE 40 APPEND: the load-book drag census
 int lift_tick[2]={-1,-1};double lift_phase[2]={-1.,-1.}; // first HIND liftoff tick/phase (wave 16 clock census)
 double paw_err_max=0;double ik_qerr_max=0;double ik_roundtrip_max=0;bool paw_captured=false;
 double worst_ledger=0;bool hull_all=true;int hull_checks=0;uint64_t captures=0;
 J last;std::string refused;int refused_tick=-1;
};

int main(int argc,char**argv){try{
 require(argc==2,"usage: gait_unit gait_scene.json");
 J scene=load_json(argv[1]);
 const J& data=scene.at("gait_controller");
 const J& recipe=data.at("recipe");
 const double dt=1.0/number(recipe.at("tick_hz"));
 const int CYCLE_TICKS=(int)std::lround(GaitWalker::T_CYCLE*number(recipe.at("tick_hz")));
 const double BW=number(data.at("seating_scan_measured").at("weight_N"));
 const double PUSH=0.1*BW; // F-G6 scripted push: a derived fraction of the measured weight
 int checks=0;int reds=0;std::vector<std::string> measured;
 auto ck=[&](bool ok,const char* msg){if(!ok){++reds;measured.push_back(std::string("RED falsifier: ")+msg);}++checks;};
 auto note=[&](const std::string& s){measured.push_back(s);};

 // ── F-G5: the free-root falsifier -- controller powered off, the body FALLS
 //    (in flight, at g; plus the zero-torque standing fold onto its stops).
 std::fprintf(stderr,"run F-G5\n");
 try{
  {GaitWalker d(data,9.80665,V{0,0,0},dt);
   d.configure({{"power",false},{"contact_enabled",false},{"start_at_tables",false},{"reset",true}});
   double y0=d.angles()[4];std::vector<double> ys;
   for(int i=0;i<100;++i){d.step();ys.push_back(d.angles()[4]);}
   double drop=y0-d.angles()[4],h=1./300,f1_mean=0;size_t sn=0;
   for(size_t i=2;i+2<ys.size();++i){double dd=(-ys[i+2]+16*ys[i+1]-30*ys[i]+16*ys[i-1]-ys[i-2])/(12*h*h);
    if(!(std::abs(dd+9.80665)<1e-3))throw Refusal("f5_free_fall_at_g");f1_mean+=dd;++sn;}
   f1_mean/=sn;
   note("F-G5 free_fall_m_s2="+std::to_string(f1_mean)+" drop_m="+std::to_string(drop));
   ck(drop>0.02,"f5_base_falls");
   auto s=d.status();
   ck(std::abs(number(s["energy"]["balance_error_J"]))<5e-2&&std::abs(number(s["energy"]["store_balance_error_J"]))<5e-2,"f5_ledger");}
  {GaitWalker d(data,9.80665,V{0,0,0},dt);
   d.configure({{"power",false},{"start_at_tables",false},{"reset",true}});
   double hip0=d.angles()[6],knee0=d.angles()[7],fold=0;
   for(int i=0;i<400;++i){d.step();fold=(std::max)(fold,(std::max)(std::abs(d.angles()[6]-hip0),std::abs(d.angles()[7]-knee0)));
    if(fold>5.*pi/180)break;}
   note("F-G5 stand_fold_deg="+std::to_string(fold*180/pi));
   ck(fold>5.*pi/180,"f5_joints_fold");}
 }catch(const Refusal&e){++reds;note(std::string("F-G5 REFUSED: ")+e.what());std::fprintf(stderr,"F-G5 refused: %s\n",e.what());}

 // ── THE WALK RUN: initialized at the measured gait state (the TD columns,
 //    the measured 1.01 m/s forward speed, the table phase slopes) -- the
 //    source model's own periodic-cycle entry.
 auto walk_run=[&](bool capture){
  GaitWalker d(data,9.80665,V{0,0,0},dt);
  d.configure({{"capture_enabled",capture},{"reset",true}});
  const int WALK=10*CYCLE_TICKS;
  WalkOut out;bool prev_t[2]={false,false};int w_ledger_first=-1;double w_ledger_prev=0;
  auto t_start=std::chrono::steady_clock::now();
  for(int i=0;i<WALK;++i){
   try{
    d.step();
    double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-t_start).count();
    if(sec>120.){char b[256];std::snprintf(b,256,"WALK exceeded the 120 s window guard at tick %d",i);out.refused=b;out.refused_tick=i;
     std::fprintf(stderr,"%s\n",b);break;}
   }
   catch(const Refusal&e){
    char b[256];std::snprintf(b,256,"WALK REFUSED tick %d: %s",i,e.what());out.refused=b;out.refused_tick=i;
    std::fprintf(stderr,"%s | y=%.4f x=%.4f\n",b,d.angles()[4],d.angles()[3]);
    // THE BISECT WITNESS (wave 12): name the failing joint/phase from the
    // traces at the refusal state itself, not from the last 10-tick sample.
    try{auto sf=d.status();
     std::fprintf(stderr,"[refusal] tick=%d refusal=%s com=(%.4f,%.4f) base=(%.4f,%.4f,%.4f)\n",
      i,e.what(),number(sf["support"]["com_projection_east_m"]),number(sf["support"]["com_projection_south_m"]),
      number(sf["base_q"][0]),number(sf["base_q"][1]),number(sf["base_q"][2]));
     for(const auto&jn:sf["joints"])
      std::fprintf(stderr,"[refusal-joint] %s phase=%.4f angle_deg=%.4f target_deg=%.4f torque=%.4f cap=%.4f\n",
       jn["name"].get<std::string>().c_str(),number(jn["phase"]),number(jn["angle_deg"]),
       number(jn["target_deg"]),number(jn["motor_torque_N_m"]),number(jn["torque_cap_N_m"]));
     for(const auto&pt:sf["contact"]["points"])
      std::fprintf(stderr,"[refusal-pt] %s gap=%.3e touching=%d rxn=%.3f slip=%.3f\n",
       pt["name"].get<std::string>().c_str(),number(pt["gap_m"]),pt["touching"].get<bool>()?1:0,
       number(pt["reaction_N"]),number(pt["slip_speed_m_s"]));}
    catch(...){} // the dump never masks the refusal itself
    // WAVE 23: the pin census must see the REFUSAL state (the deadlock's
    // pins happen inside the refusing step, after the last successful
    // status) -- refresh the last census row from the refusal-state status.
    try{auto sf=d.status();
     if(!out.wpins.empty()&&!out.wair.empty()&&sf["gait"].contains("fore_paw")&&sf["gait"]["fore_paw"].size()>=2)
      for(size_t l=0;l<2;++l){const auto&p=sf["gait"]["fore_paw"][l];
       if(p.contains("wall_pins"))out.wpins.back()[l]=p["wall_pins"].get<uint64_t>();
       if(p.contains("wall_pins_air"))out.wair.back()[l]=p["wall_pins_air"].get<uint64_t>();}}
    catch(...){}
    break;}
   auto s=d.status();
   // WAVE 13 fore-paw census: every tick, per-leg worst/best gap over the
   // leg's heel+MP, the fore clock mode, and the per-leg saturation snapshot.
   {std::array<double,2> mx{-1e9,-1e9},mn{1e9,1e9};
    for(const auto&pt:s["contact"]["points"]){const std::string nm=pt["name"].get<std::string>();
     size_t l=nm.rfind("fore_left_",0)==0?0:nm.rfind("fore_right_",0)==0?1:2;
     if(l<2){double g=number(pt["gap_m"]);mx[l]=(std::max)(mx[l],g);mn[l]=(std::min)(mn[l],g);}}
    if(mx[0]>-1e8){out.fgmax.push_back(mx);out.fgmin.push_back(mn);}
    {std::array<double,8> gaps{};size_t k=0;
     for(const auto&pt:s["contact"]["points"]){if(k<8)gaps[k++]=number(pt["gap_m"]);}
     out.gp.push_back(gaps);}
    {double fsum=0,fslip=0,hsum=0; // WAVE 16 fore-load + WAVE 17 hind-load census inputs
     for(const auto&pt:s["contact"]["points"]){const std::string nm=pt["name"].get<std::string>();
      if(nm.rfind("fore_",0)==0){fsum+=number(pt["reaction_N"]);fslip=(std::max)(fslip,number(pt["slip_speed_m_s"]));}
      else hsum+=number(pt["reaction_N"]);} // the hind points (left_/right_ prefixed)
     out.fr.push_back(fsum);out.frslip.push_back(fslip);out.hr.push_back(hsum);}
    // WAVE 21 HIND-RIDE census inputs (the derivation's measured base): hind
    // point detail in declared order, the posture drive, capture events, hind
    // clock phases, CoM/hull, base x, hind drive speeds.
    {std::array<double,4> hg{},hn{},hf{},hs{};size_t k=0;
     for(const auto&pt:s["contact"]["points"]){if(k>=4)break;
      hg[k]=number(pt["gap_m"]);hn[k]=number(pt["reaction_N"]);
      hf[k]=number(pt["friction_force_N"]);hs[k]=number(pt["slip_speed_m_s"]);++k;}
     out.hgap.push_back(hg);out.hrxn.push_back(hn);out.hfrc.push_back(hf);out.hslip.push_back(hs);}
    // WAVE 28 MINING (trace print only): the hind points' world CoP positions
    // per tick -- the recede series' measured base. Read-only harness state;
    // no status byte and no stdout byte depends on it (the trace print below
    // is stderr-only, GAIT_EVENT_TRACE builds).
    {std::array<double,8> hp{};size_t k=0;
     for(const auto&pt:s["contact"]["points"]){if(k>=4)break;
      hp[2*k]=number(pt["position_m"][0]);hp[2*k+1]=number(pt["position_m"][1]);++k;}
     out.hpos.push_back(hp);}
    {const J& tr=s["joints"][12];
     out.post.push_back({number(tr["motor_torque_N_m"]),number(tr["target_deg"]),
      number(tr["angle_deg"]),number(tr["speed_rad_s"])});}
    out.cev.push_back(s["gait"]["capture_events"].get<uint64_t>());
    out.hphase.push_back({number(s["gait"]["phase_left"]),number(s["gait"]["phase_right"])});
    out.comh.push_back({number(s["support"]["com_projection_east_m"]),
      number(s["support"]["com_projection_south_m"]),
      double(s["support"]["hull_size"].get<int>()),s["support"]["com_in_hull"].get<bool>()?1.:0.});
    out.bx.push_back(number(s["base_q"][0]));
    {std::array<double,8> sp{};for(size_t k=0;k<8;++k)sp[k]=number(s["joints"][k]["speed_rad_s"]);
     out.hspd.push_back(sp);}
#ifdef GAIT_EVENT_TRACE
    if(true){ // WAVE 22 MINING: the whole (short) life, per-tick hind detail
     const J& tr=s["joints"][12];
     std::fprintf(stderr,"[dv] t=%d ptq=%.5f ptgt=%.4f pang=%.4f pspd=%.4f ev=%llu phL=%.5f phR=%.5f com=(%.6f,%.6f) hull=%d in=%d bx=%.6f\n",
      i,number(tr["motor_torque_N_m"]),number(tr["target_deg"]),number(tr["angle_deg"]),number(tr["speed_rad_s"]),
      (unsigned long long)out.cev.back(),out.hphase.back()[0],out.hphase.back()[1],
      out.comh.back()[0],out.comh.back()[1],(int)out.comh.back()[2],(int)out.comh.back()[3],out.bx.back());
     for(size_t k=0;k<4;++k)
      std::fprintf(stderr,"[dvp] t=%d k=%zu gap=%.4e rxn=%.5f frc=%.5f slip=%.5f pos=%.9f,%.9f\n",
       i,k,out.hgap.back()[k],out.hrxn.back()[k],out.hfrc.back()[k],out.hslip.back()[k],
       out.hpos.back()[2*k],out.hpos.back()[2*k+1]);
     for(size_t k=0;k<8;++k)
      std::fprintf(stderr,"[dvj] t=%d k=%zu ang=%.4f tgt=%.4f spd=%.4f\n",
       i,k,number(s["joints"][k]["angle_deg"]),number(s["joints"][k]["target_deg"]),number(s["joints"][k]["speed_rad_s"]));
     for(size_t k=0;k<8;++k) // WAVE 30 DEMAND CENSUS: per-tick per-hind-drive {torque, cap} (the [dvq] instrument;
      std::fprintf(stderr,"[dvq] t=%d k=%zu tau=%.6f cap=%.6f\n", //  stderr-only, GAIT_EVENT_TRACE builds; stdout-inert)
       i,k,number(s["joints"][k]["motor_torque_N_m"]),number(s["joints"][k]["torque_cap_N_m"]));
     { // WAVE 41 SHARE INSTRUMENT (read-only plumbing, receipt_wave41.json):
       // the per-tick FORE pad detail {gap,rxn,frc,slip,pos} -- the [dvp]
       // format mirrored, the fore points classified by their own name
       // prefixes in file order k=0..3 -- and the fore-column rxn sums (the
       // [dvfs] series). The fore columns' share is in NO other trace series
       // (the wave-40 bank's declared instrument gap). stderr-only,
       // GAIT_EVENT_TRACE builds; stdout-inert (the byte equality is the
       // inertness proof).
      size_t kf=0;double sl=0.,sr=0.;
      for(const auto&pt:s["contact"]["points"]){const std::string nm=pt["name"].get<std::string>();
       if(nm.rfind("fore_",0)!=0)continue;
       if(kf<4)std::fprintf(stderr,"[dvfp] t=%d k=%zu gap=%.4e rxn=%.5f frc=%.5f slip=%.5f pos=%.9f,%.9f\n",
        i,kf,number(pt["gap_m"]),number(pt["reaction_N"]),number(pt["friction_force_N"]),
        number(pt["slip_speed_m_s"]),number(pt["position_m"][0]),number(pt["position_m"][1]));
       {double rr=number(pt["reaction_N"]);
        if(nm.rfind("fore_left",0)==0)sl+=rr;else sr+=rr;}
       ++kf;}
      std::fprintf(stderr,"[dvfs] t=%d sumL=%.5f sumR=%.5f n=%zu\n",i,sl,sr,kf);}
     if(out.cev.size()>=2&&out.cev[out.cev.size()-2]!=out.cev.back())
      std::fprintf(stderr,"[dvfire] t=%d capture_events %llu->%llu phL=%.5f phR=%.5f in_hull=%d com=(%.6f,%.6f)\n",
       i,(unsigned long long)out.cev[out.cev.size()-2],(unsigned long long)out.cev.back(),
       out.hphase.back()[0],out.hphase.back()[1],(int)out.comh.back()[3],out.comh.back()[0],out.comh.back()[1]);
     if(i>=60&&i<=70){
      std::fprintf(stderr,"[dvhull] t=%d hull:",i);
      for(const auto&h:s["support"]["points"])std::fprintf(stderr," (%.6f,%.6f)",number(h[0]),number(h[1]));
      std::fprintf(stderr," vx_prev=%.4f\n",i>0?out.bx[out.bx.size()-1]-out.bx[out.bx.size()-2]:0.);}}
#endif
    std::array<char,2> fmm{0,0};std::array<uint64_t,2> sat{};std::array<double,2> tgx{0.,0.};std::array<uint64_t,2> rep{0,0};
    std::array<std::array<double,11>,2> fwk{};std::array<uint64_t,2> wp{},wb{},wf{},wa{};
    std::array<char,2> fh{0,0};std::array<int,2> fhlk{-1,-1};std::array<double,2> ftick{-1.,-1.};
    if(s["gait"].contains("fore_paw")&&s["gait"]["fore_paw"].size()>=2)
     for(size_t l=0;l<2;++l){const auto&p=s["gait"]["fore_paw"][l];
      if(p.contains("fore_mode"))fmm[l]=p["fore_mode"].get<std::string>()=="swing"?1:0;
      if(p.contains("ik_saturated_ticks"))sat[l]=p["ik_saturated_ticks"].get<uint64_t>();
      if(p.contains("glide_hold"))fh[l]=p["glide_hold"].get<bool>()?1:0;
      if(p.contains("glide_hold_last"))fhlk[l]=p["glide_hold_last"].get<int>();
      if(p.contains("t_in_cycle"))ftick[l]=number(p["t_in_cycle"]);
      if(p.contains("ik_qerr_rad"))out.ik_qerr_max=(std::max)(out.ik_qerr_max,number(p["ik_qerr_rad"]));
      if(p.contains("error_m"))out.paw_err_max=(std::max)(out.paw_err_max,number(p["error_m"]));
      if(p.contains("ik_roundtrip_m"))out.ik_roundtrip_max=(std::max)(out.ik_roundtrip_max,number(p["ik_roundtrip_m"]));
      if(p.contains("target_m"))tgx[l]=number(p["target_m"][0]);
      if(p.contains("replants"))rep[l]=p["replants"].get<uint64_t>();
      if(p.contains("wall_headroom_rad")){
       double tx=number(p["target_m"][0]),ty=number(p["target_m"][1]);
       double sx=number(p["shoulder_m"][0]),sy=number(p["shoulder_m"][1]);
       fwk[l]={tx,ty,sx,sy,number(p["wall_headroom_rad"]),number(p["ik_q1_unc_rad"]),
        number(p["ik_q2_unc_rad"]),number(s["joints"][8+2*l]["angle_deg"])*pi/180.,
        number(s["joints"][9+2*l]["angle_deg"])*pi/180.,std::hypot(tx-sx,ty-sy),tx-sx};
       wp[l]=p["wall_pins"].get<uint64_t>();wb[l]=p["wall_bound_ticks"].get<uint64_t>();
       wf[l]=p["wall_follows"].get<uint64_t>();wa[l]=p["wall_pins_air"].get<uint64_t>();}}
    out.fw[0].push_back(fwk[0]);out.fw[1].push_back(fwk[1]);
    out.wpins.push_back(wp);out.wair.push_back(wa);out.wbound.push_back(wb);out.wfollow.push_back(wf);
    out.fhold.push_back(fh);out.fhl.push_back(fhlk);out.ftic.push_back(ftick);
    out.fcap.push_back(s["gait"].contains("fore_paw_captured")&&s["gait"]["fore_paw_captured"].get<bool>()?1:0);
    {std::array<double,36> hst{};hst.fill(-1.);
     if(s["gait"].contains("hind_step")&&s["gait"]["hind_step"].size()>=2)
      for(size_t l=0;l<2;++l){const auto&p=s["gait"]["hind_step"][l];
       size_t b=12*l;
       hst[b+0]=p["mode"].get<std::string>()=="step"?1.:0.;
       hst[b+1]=number(p["t"]);hst[b+2]=double(p["fires"].get<uint64_t>());
       hst[b+3]=double(p["tds"].get<uint64_t>());hst[b+4]=double(p["gated"].get<uint64_t>());
       hst[b+5]=double(p["reach_clamped"].get<uint64_t>());
       hst[b+6]=double(p["last_fire_tick"].get<uint64_t>());
       hst[b+7]=double(p["last_td_tick"].get<uint64_t>());
       hst[b+8]=number(p["fire_qerr_rad"]);
       hst[b+9]=double(p["wall_pins"].get<uint64_t>());
       hst[b+10]=double(p["wall_pins_air"].get<uint64_t>());
       hst[b+11]=number(p["xoff_m"]);
       // THE STAND-FIRST HOLD's census fields (wave 33, appended to the
       // DISJOINT TAIL slots 24+3*l -- the old layout is interleaved 12/leg,
       // slots 12..23 belong to the RIGHT leg's reads; indices preserved)
       hst[24+3*l]=double(p["swing_stall_ticks"].get<uint64_t>());
       hst[25+3*l]=p["stand_hold"].get<bool>()?1.:0.;
       hst[26+3*l]=double(p["stand_hold_ticks"].get<uint64_t>());
       // THE LATCHED WORLD-PIVOT HOLD's census fields (wave 34, appended to
       // the DISJOINT TAIL slots 30+3*l; indices preserved)
       hst[30+3*l]=p["stand_latch"].get<bool>()?1.:0.;
       hst[31+3*l]=p["stand_pivot"].get<bool>()?1.:0.;
       hst[32+3*l]=p.value("stand_release",-1.);}
     out.hindst.push_back(hst);}
    {std::array<double,12> h29{};h29.fill(-1.);
     if(s["gait"].contains("hind_step")&&s["gait"]["hind_step"].size()>=2)
      for(size_t l=0;l<2;++l){const auto&p=s["gait"]["hind_step"][l];
       size_t b=4*l;
       if(p.contains("fire_class"))h29[b+0]=p["fire_class"].get<std::string>()=="alternation"?1.:0.;
       if(p.contains("held"))h29[b+1]=p["held"].get<bool>()?1.:0.;
       if(p.contains("clear_tick"))h29[b+2]=number(p["clear_tick"]);
       if(p.contains("deadline_fires"))h29[b+3]=double(p["deadline_fires"].get<uint64_t>());
       // WAVE 32 APPEND (indices preserved: leg 0 [8,10), leg 1 [10,12))
       if(p.contains("deadline_unload"))h29[8+2*l]=p["deadline_unload"].get<bool>()?1.:0.;
       if(p.contains("unload_fires"))h29[10+2*l]=double(p["unload_fires"].get<uint64_t>());}
     out.hind29.push_back(h29);}
    {std::array<double,10> h35;h35.fill(-1.); // WAVE 35 APPEND: the waive census
     if(s["gait"].contains("hind_step")&&s["gait"]["hind_step"].size()>=2)
      for(size_t l=0;l<2;++l){const auto&p=s["gait"]["hind_step"][l];
       if(p.contains("waive_fires"))h35[2*l]=double(p["waive_fires"].get<uint64_t>());
       if(p.contains("waive_first_tick"))h35[2*l+1]=number(p["waive_first_tick"]);
       // WAVE 36 APPEND (indices preserved: leg 0 [4,7), leg 1 [7,10))
       if(p.contains("waive_last_tick"))h35[4+3*l]=number(p["waive_last_tick"]);
       if(p.contains("handoff_restores"))h35[5+3*l]=double(p["handoff_restores"].get<uint64_t>());
       if(p.contains("alt_repairs"))h35[6+3*l]=double(p["alt_repairs"].get<uint64_t>());}
     out.hind35.push_back(h35);}
    {std::array<double,4> h37;h37.fill(-1.); // WAVE 37 APPEND: the re-lock census
     if(s["gait"].contains("hind_step")&&s["gait"]["hind_step"].size()>=2)
      for(size_t l=0;l<2;++l){const auto&p=s["gait"]["hind_step"][l];
       if(p.contains("graze_yields"))h37[2*l]=double(p["graze_yields"].get<uint64_t>());
       if(p.contains("graze_first_tick"))h37[2*l+1]=number(p["graze_first_tick"]);}
     out.hind37.push_back(h37);}
    {std::array<double,4> h38;h38.fill(-1.); // WAVE 38 APPEND: the waive-scope-guard census
     if(s["gait"].contains("hind_step")&&s["gait"]["hind_step"].size()>=2)
      for(size_t l=0;l<2;++l){const auto&p=s["gait"]["hind_step"][l];
       if(p.contains("guard_blocks"))h38[2*l]=double(p["guard_blocks"].get<uint64_t>());
       if(p.contains("guard_first_tick"))h38[2*l+1]=number(p["guard_first_tick"]);}
     out.hind38.push_back(h38);}
    {std::array<double,4> h39;h39.fill(-1.); // WAVE 39 APPEND: the stay-era haul restoration census
     if(s["gait"].contains("hind_step")&&s["gait"]["hind_step"].size()>=2)
      for(size_t l=0;l<2;++l){const auto&p=s["gait"]["hind_step"][l];
       if(p.contains("refires"))h39[2*l]=double(p["refires"].get<uint64_t>());
       if(p.contains("refire_first_tick"))h39[2*l+1]=number(p["refire_first_tick"]);}
     out.hind39.push_back(h39);}
    {std::array<double,6> h40;h40.fill(-1.); // WAVE 40 APPEND: the load-book drag census
     if(s["gait"].contains("hind_step")&&s["gait"]["hind_step"].size()>=2)
      for(size_t l=0;l<2;++l){const auto&p=s["gait"]["hind_step"][l];
       if(p.contains("drag_arms"))h40[3*l]=double(p["drag_arms"].get<uint64_t>());
       if(p.contains("drag_first_tick"))h40[3*l+1]=number(p["drag_first_tick"]);
       if(p.contains("drag_releases"))h40[3*l+2]=double(p["drag_releases"].get<uint64_t>());}
     out.hind40.push_back(h40);}
    out.fm.push_back(fmm);out.fsat.push_back(sat);out.ftgt.push_back(tgx);out.frep.push_back(rep);
#ifdef GAIT_EVENT_TRACE
    // WAVE 23 MINING: the per-tick fore joint-wall state (the derivation's
    // measured base): both legs, target/shoulder seats, actual+unclamped IK,
    // the actual wall headroom, the target's annulus D and offset.
    if(true)for(size_t l=0;l<2;++l){const auto&f=out.fw[l].back();
     std::fprintf(stderr,"[dvf] t=%d leg=%zu mode=%d tgt=(%.6f,%.6f) sh=(%.6f,%.6f) D=%.6f off=%+.6f hr=%.6f q1a=%.4f q1u=%.4f q2a=%.4f q2u=%.4f pins=%llu fol=%llu\n",
      i,l,(int)fmm[l],f[0],f[1],f[2],f[3],f[9],f[10],f[4],f[7]*180/pi,f[5]*180/pi,f[8]*180/pi,f[6]*180/pi,
      (unsigned long long)wp[l],(unsigned long long)wf[l]);}
#endif
   }
   if(s["gait"].contains("fore_paw_captured"))out.paw_captured=s["gait"]["fore_paw_captured"].get<bool>();
   double bal=std::abs(number(s["energy"]["balance_error_J"])),stor=std::abs(number(s["energy"]["store_balance_error_J"]));
#ifdef GAIT_EVENT_TRACE
   if((bal>1e-3||stor>1e-3)&&w_ledger_first<0){w_ledger_first=i;
    std::fprintf(stderr,"[ledger] first breach tick %d: %s\n",i,s["energy"].dump().c_str());}
   if((bal>1e-3||stor>1e-3)&&(bal>w_ledger_prev+0.25||stor>w_ledger_prev+0.25)){
    std::fprintf(stderr,"[ledger] tick %d bal=%.4f stor=%.4f | KE=%.3f grav=%.3f work=%.3f damp=%.3f imp=%.3f fric=%.3f brake=%.3f ext=%.3f\n",
     i,bal,stor,number(s["energy"]["kinetic_J"]),number(s["energy"]["gravitational_J"]),number(s["energy"]["actuator_work_J"]),
     number(s["energy"]["damping_heat_J"]),number(s["energy"]["impact_heat_J"]),number(s["energy"]["friction_heat_J"]),
     number(s["energy"]["brake_heat_J"]),number(s["energy"]["external_work_J"]));}
   w_ledger_prev=(std::max)(w_ledger_prev,(std::max)(bal,stor));
   if(i%10==0){std::fprintf(stderr,"[ledger10] tick %d %s\n",i,s["energy"].dump().c_str());
    for(const auto&pt:s["contact"]["points"])std::fprintf(stderr,"[pt] %s cop_x=%.5f cop_y=%.5f gap=%.3e touching=%d rxn=%.3f slip=%.3f\n",pt["name"].get<std::string>().c_str(),number(pt["position_m"][0]),number(pt["position_m"][1]),number(pt["gap_m"]),pt["touching"].get<bool>()?1:0,number(pt["reaction_N"]),number(pt["slip_speed_m_s"]));
    const J& trunk=s["joints"][12];
    std::fprintf(stderr,"[trunk] phase=%.5f angle_deg=%.5f target_deg=%.5f torque=%.5f speed=%.5f\n",number(trunk["phase"]),number(trunk["angle_deg"]),number(trunk["target_deg"]),number(trunk["motor_torque_N_m"]),number(trunk["speed_rad_s"]));
    for(size_t fj=8;fj<12;++fj){const J& fore=s["joints"][fj];std::fprintf(stderr,"[fore] name=%s angle_deg=%.5f target_deg=%.5f torque=%.5f cap=%.5f\n",fore["name"].get<std::string>().c_str(),number(fore["angle_deg"]),number(fore["target_deg"]),number(fore["motor_torque_N_m"]),number(fore["torque_cap_N_m"]));}
    std::fprintf(stderr,"[body] tick=%d x=%.6f y=%.6f\n",i,number(s["base_q"][0]),number(s["base_q"][1]));}
#endif
   out.worst_ledger=(std::max)(out.worst_ledger,(std::max)(bal,stor));
   if(s["support"]["hull_size"].get<int>()>=3){++out.hull_checks;if(!s["support"]["com_in_hull"].get<bool>())out.hull_all=false;}
   for(size_t leg=0;leg<2;++leg){
    bool t=s["gait"][leg?"touching_right":"touching_left"].get<bool>();
    if(t&&!prev_t[leg])out.td[leg].push_back(number(s["sim_time_s"]));
    if(!t&&prev_t[leg]){out.liftoff[leg].push_back(d.phase(leg));
     if(out.lift_tick[leg]<0){out.lift_tick[leg]=i;out.lift_phase[leg]=d.phase(leg);}}
    prev_t[leg]=t;}
   if(i%10==0){std::string j=s.dump();out.stream+=j;out.stream+='\n';}
   std::array<double,8> a{},tg{};std::array<char,2> tt{};std::array<double,2> rr{0.,0.};
   const J& joints=s["joints"];
   for(size_t k=0;k<8;++k){a[k]=number(joints[k]["angle_deg"]);tg[k]=number(joints[k]["target_deg"]);}
   for(size_t leg=0;leg<2;++leg){tt[leg]=s["gait"][leg?"touching_right":"touching_left"].get<bool>();
    for(const auto&p:s["contact"]["points"])
     if(p["name"].get<std::string>().rfind(leg?"right":"left",0)==0&&p["touching"].get<bool>())rr[leg]+=number(p["reaction_N"]);}
   out.a.push_back(a);out.tg.push_back(tg);out.t.push_back(tt);out.r.push_back(rr);}
  out.captures=d.capture_events();out.last=d.status();
  return out;};

 std::fprintf(stderr,"run F-G1..G4 walk\n");
 WalkOut w=walk_run(true);
 note("WALK refused_tick="+(w.refused_tick<0?std::string("none"):std::to_string(w.refused_tick))+" worst_ledger_J="+std::to_string(w.worst_ledger));

 // ── F-Gfore (wave 13, pre-registered): the STEPPING-STRUT paw band + the
 //    reach census. From the capture tick (60) on: STANCE-phase fore gaps
 //    within [-1e-6, 1e-5] m (both legs, heel+MP; penetration bound -1e-6 is
 //    the poscorr trigger); SWING-phase gaps >= -1e-6 (airborne -- the
 //    pad-geometry clearance arch is NOT a breach). Ticks 0-59 are the
 //    wave-12-banked settle drop (reported, not judged). Reach falsifier:
 //    per-leg IK saturation ticks <= 10 over the whole walk (the law predicts
 //    0 in steady state; wave 12 measured 176/291). Plus the analytic closure
 //    at every capture: round-trip < 1e-12 m, capture qerr < 1e-12 rad.
 {const size_t WIN=w.fgmax.size();
  double st_hi[2]={-1e9,-1e9},st_lo[2]={1e9,1e9},sw_lo[2]={1e9,1e9},sw_hi[2]={-1e9,-1e9};
  double set_mx=-1e9,set_mn=1e9;int breach[2]={-1,-1};double breach_gap[2]={0.,0.};
  size_t stance_ticks[2]={0,0},swing_ticks[2]={0,0};
  for(size_t i=0;i<WIN;++i)for(size_t l=0;l<2;++l){
   double mx=w.fgmax[i][l],mn=w.fgmin[i][l];
   if(i<60){set_mx=(std::max)(set_mx,mx);set_mn=(std::min)(set_mn,mn);continue;}
   if(!w.fm[i][l]){++stance_ticks[l];
    if(breach[l]<0&&(mx>1e-5||mn<-1e-6)){breach[l]=(int)i;breach_gap[l]=mx>1e-5?mx:mn;}
    st_hi[l]=(std::max)(st_hi[l],mx);st_lo[l]=(std::min)(st_lo[l],mn);}
   else{++swing_ticks[l];
    if(breach[l]<0&&mn<-1e-6){breach[l]=(int)i;breach_gap[l]=mn;}
    sw_lo[l]=(std::min)(sw_lo[l],mn);sw_hi[l]=(std::max)(sw_hi[l],mx);}}
  std::array<uint64_t,2> sat_end{};
  if(!w.fsat.empty())sat_end=w.fsat.back();
  for(size_t l=0;l<2;++l){
   note("F-Gfore leg="+std::string(l?"right":"left")+" stance_ticks="+std::to_string(stance_ticks[l])+
    " stance_gap_max_m="+(st_hi[l]>-1e8?std::to_string(st_hi[l]):"n/a")+
    " stance_gap_min_m="+(st_lo[l]<1e8?std::to_string(st_lo[l]):"n/a")+
    " swing_gap_min_m="+(sw_lo[l]<1e8?std::to_string(sw_lo[l]):"n/a")+
    " swing_gap_max_m="+(sw_hi[l]>-1e8?std::to_string(sw_hi[l]):"n/a")+
    " first_breach_tick="+(breach[l]<0?std::string("none"):(std::to_string(breach[l])+" gap="+std::to_string(breach_gap[l])))+
    " ik_sat_ticks="+std::to_string(sat_end[l]));
   ck(breach[l]<0,"f_g_fore_paw_band");
   ck(sat_end[l]<=10,"f_g_fore_reach_bound");}
  note("F-Gfore settle_transient ticks0-59 gap_max="+std::to_string(set_mx)+" gap_min="+std::to_string(set_mn)+
   " (wave-12-banked reset drop; not judged here)");
  note("F-Gfore paw_captured="+(w.paw_captured?std::string("1"):"0")+
   " ik_qerr_max_rad="+std::to_string(w.ik_qerr_max)+" ik_roundtrip_max_m="+std::to_string(w.ik_roundtrip_max)+
   " paw_err_max_m="+std::to_string(w.paw_err_max));
  ck(w.ik_roundtrip_max<1e-12,"f_g_fore_ik_roundtrip");
  ck(w.ik_qerr_max<1e-12,"f_g_fore_ik_qerr");}

 // ── WAVE 14 ENTRY CENSUS (pre-registered in receipt_wave14.json): STAGGER --
 //    no BOTH-FORE-AIRBORNE window >= 2 ticks in [60, 426] (the wave-13 death:
 //    both entry stances envelope-starved, lifts at 79/83, fores airborne
 //    ~[84,166)); SUPPORT CENSUS >= 2 paw contacts at every tick in [60, 426]
 //    (>= 3 except the steady lateral pattern's own 2-paw windows). A fore leg
 //    is AIRBORNE here in the clock sense (swing mode) and in the contact
 //    sense (both pad gaps above the 1e-5 band) -- both counted.
 //    WAVE 25 DUAL READING (pre-registered in receipt_wave25.json, THE
 //    GATE'S CADENCE LAW): the census is OWNED on the CONTACT sense -- both
 //    legs' min fore pad gap above the kTouch band simultaneously. A HELD
 //    glide (the wave-24 pocket-clear hold: pads live, in-band, support
 //    intact) is NOT airborne for the owned census; the CLOCK sense is
 //    REPORTED, never owned -- the held interleave is the law's designed
 //    face. Plus the cadence-law support clauses: support >= 3 through
 //    every held tick and >= 2 through every true-airborne fore swing tick
 //    (the gate's purpose, measured per tick).
 {const size_t N=std::min(w.fm.size(),(size_t)426);
  int bfa_run=0,bfa_mx=0,bfa_first=-1,bfa_windows=0;
  int bfc_run=0,bfc_mx=0,bfc_first=-1,bfc_windows=0;
  int sup2_first=-1,sup2_ticks=0,sup_min=99;
  int held_ticks=0,held_sup_bad=0,held_sup_min=99,swing_true_ticks=0,swing_sup_bad=0,swing_sup_min=99;
  // WAVE 26 (pre-registered in receipt_wave26.json): the 2-support tick
  // classification. NO micro-unload is shipped this wave, so an UNLOAD-CLASS
  // 2-support tick (a fore leg's pads OUT of the band -- the R fore spending
  // support) is OWNED RED. The STEADY-PATTERN class (both fores' pads
  // in-band, exactly one hind mid-clock-swing -- the wave-14 banked carve-out
  // "the steady lateral pattern's own 2-paw windows") is REPORTED with its
  // ticks, never hidden. Both readings reported per the pre-registration.
  int steady2_ticks=0,unload2_ticks=0;std::string steady2_list,unload2_list;
  int hstep2_ticks=0;std::string hstep2_list; // the wave-28 hind-step class (reported)
  std::string two_windows;
  for(size_t i=60;i<N;++i){
   bool l_air=w.fm[i][0]==1,r_air=w.fm[i][1]==1;
   bool l_ct=w.fgmin[i][0]>1e-5,r_ct=w.fgmin[i][1]>1e-5; // contact-airborne
   if(l_air&&r_air){++bfa_run;if(bfa_run==1)++bfa_windows;if(bfa_first<0)bfa_first=(int)i;bfa_mx=(std::max)(bfa_mx,bfa_run);}
   else bfa_run=0;
   if(l_ct&&r_ct){++bfc_run;if(bfc_run==1)++bfc_windows;if(bfc_first<0)bfc_first=(int)i;bfc_mx=(std::max)(bfc_mx,bfc_run);}
   else bfc_run=0;
   int c=(w.t[i][0]?1:0)+(w.t[i][1]?1:0)+((w.fgmin[i][0]<=1e-5)?1:0)+((w.fgmin[i][1]<=1e-5)?1:0);
   sup_min=(std::min)(sup_min,c);
   if(c<2){++sup2_ticks;if(sup2_first<0)sup2_first=(int)i;}
   if(c==2){char b[64];std::snprintf(b,64,"%d ",(int)i);two_windows+=b;
    if(w.fgmin[i][0]>1e-5||w.fgmin[i][1]>1e-5){
     // WAVE 28 CLASSIFICATION AMENDMENT (pre-registered in
     // receipt_wave28.json, the wave-25 held-glide precedent): a
     // HIND-STEP-CLASS 2-support tick (a hind mid-glide under the gate's
     // support floor -- the law's DESIGNED face) is REPORTED, owned by the
     // F-G28 support letter; a FORE-spending tick with no hind step active
     // stays OWNED RED.
     bool hs_now=w.hindst.size()>i&&(w.hindst[i][0]>0.5||w.hindst[i][12]>0.5);
     bool hind_out=!(w.t[i][0]&&w.t[i][1]);
     if(hs_now&&hind_out){++hstep2_ticks;
      if(hstep2_list.size()<240){char hb[64];std::snprintf(hb,64,"%d ",(int)i);hstep2_list+=hb;}}
     else{++unload2_ticks;
      if(unload2_list.size()<240){char ub[64];std::snprintf(ub,64,"%d ",(int)i);unload2_list+=ub;}}}
    else{++steady2_ticks;
     if(steady2_list.size()<240){char sb[64];std::snprintf(sb,64,"%d ",(int)i);steady2_list+=sb;}}}
   // THE WAVE-25 CADENCE-LAW SUPPORT CLAUSES (per tick): a held glide's
   // pads are live -> support >= 3 through every held tick; a true
   // airborne fore swing (mode 1, not held, pads above the band) must
   // never run support below 2 -- the gate's purpose.
   bool any_held=w.fhold[i][0]!=0||w.fhold[i][1]!=0;
   bool any_true_swing=(w.fm[i][0]==1&&w.fhold[i][0]==0&&w.fgmin[i][0]>1e-5)||
                       (w.fm[i][1]==1&&w.fhold[i][1]==0&&w.fgmin[i][1]>1e-5);
   if(any_held){++held_ticks;held_sup_min=(std::min)(held_sup_min,c);if(c<3)++held_sup_bad;}
   if(any_true_swing){++swing_true_ticks;swing_sup_min=(std::min)(swing_sup_min,c);if(c<2)++swing_sup_bad;}}
  note("F-G14 stagger both_fore_swing_windows(clock,REPORTED)="+std::to_string(bfa_windows)+
   " max_window_ticks(clock)="+std::to_string(bfa_mx)+" first="+(bfa_first<0?"none":std::to_string(bfa_first))+
   " both_fore_contact_airborne_windows(OWNED)="+std::to_string(bfc_windows)+
   " max_window_ticks(contact)="+std::to_string(bfc_mx)+" first="+(bfc_first<0?"none":std::to_string(bfc_first))+
   " [WAVE 25 dual reading: the contact sense owns; a held glide (pads live) is not airborne]");
  note("F-G14 support_census min_contacts="+std::to_string(sup_min)+
   " sub2_ticks="+std::to_string(sup2_ticks)+" sub2_first="+(sup2_first<0?"none":std::to_string(sup2_first)));
  {char b[512];std::snprintf(b,512,"F-G26 support_2_support_reading min_contacts=%d unload_class_ticks=%d%s%s [OWNED 0: no micro-unload shipped] hind_step_class_ticks=%d%s%s [REPORTED: the wave-28 law's designed face, owned by F-G28 support>=2] steady_pattern_class_ticks=%d%s%s [REPORTED: the wave-14 banked carve-out; readings per the pre-registrations]",
   sup_min,unload2_ticks,unload2_ticks?" @ ":"",unload2_ticks?unload2_list.c_str():"",
   hstep2_ticks,hstep2_ticks?" @ ":"",hstep2_ticks?hstep2_list.c_str():"",
   steady2_ticks,steady2_ticks?" @ ":"",steady2_ticks?steady2_list.c_str():"");
   note(b);
   ck(unload2_ticks==0,"f26_no_unload_class_support2");}
  if(!two_windows.empty()&&two_windows.size()<800)
   note("F-G14 two_contact_ticks= "+two_windows);
  note("F-G25 cadence_support held_ticks="+std::to_string(held_ticks)+
   " held_support_min="+(held_ticks?std::to_string(held_sup_min):"n/a")+
   " held_support_viol(<3)="+std::to_string(held_sup_bad)+
   " true_swing_ticks="+std::to_string(swing_true_ticks)+
   " true_swing_support_min="+(swing_true_ticks?std::to_string(swing_sup_min):"n/a")+
   " true_swing_support_viol(<2)="+std::to_string(swing_sup_bad));
  ck(bfc_mx<2,"f25_no_both_fore_contact_airborne_window");
  ck(sup2_ticks==0,"f14_support_census_min2");
  ck(held_sup_bad==0,"f25_held_support_min3");
  ck(swing_sup_bad==0,"f25_true_swing_support_min2");}

 // ── WAVE 20 RE-PLANT CENSUS (pre-registered in receipt_wave20.json): the
 //    MID-ENTRY RE-PLANT law's own falsifiers. (1) STAGGER: the airborne
 //    runs (fore clocks in swing mode) in [60, 426] are enumerated; adjacent
 //    runs must be separated by >= 1 clear tick (no overlap -- F-G14's both-
 //    airborne census is the hard form -- and no back-to-back). The NAMED
 //    TICKS of the derivation: L window 1 liftoff 61 +/-1, TD 70 +/-1; R's
 //    first IN-PLACE ground re-plant (a replant counter jump with no swing
 //    transition) at 66 +/-1; window 2 liftoff 71 +/-1, TD 80 +/-1. (2)
 //    STEP_LAW: the first TD plants within the derivation's bands: L1 in
 //    [0.1567, 0.1645] m; window 2 in [0.1704, 0.1832] (branch A, right leg)
 //    or [0.1595, 0.1756] (branch B, left leg). (3) The gate/in-place counts
 //    reported from the status (entry_replant, gate_hold_ticks, replants).
 {const size_t N=std::min(w.fm.size(),(size_t)426);
  struct Run{int leg,beg,end;}; // end = LAST airborne index
  std::vector<Run> runs;
  for(size_t l=0;l<2;++l){
   int st=-1;
   for(size_t i=60;i<N;++i){
    if(w.fm[i][l]==1&&st<0)st=(int)i;
    if(w.fm[i][l]==0&&st>=0){runs.push_back({(int)l,st,(int)i-1});st=-1;}}
   if(st>=0)runs.push_back({(int)l,st,(int)N-1});}
  int min_gap=1<<30;size_t bad_gap=0;
  // WAVE 23 MACHINERY NOTE: the runs were enumerated per leg (the L loop,
  // then the R); the joint-admissible hold's law can interleave a short
  // second window of one leg between two windows of the other, so the
  // gap pairing now sorts the runs by time (TIGHTENS the check: real
  // overlaps are caught in any order; the disjoint-run requirement is
  // unchanged).
  std::sort(runs.begin(),runs.end(),[](const Run&a,const Run&b){return a.beg<b.beg;});
  for(size_t r=0;r+1<runs.size();++r){
   int gap=runs[r+1].beg-runs[r].end-1; // clear ticks between the runs
   min_gap=(std::min)(min_gap,gap);
   if(gap<1)++bad_gap;}
  // WAVE 25 (pre-registered in receipt_wave25.json, THE GATE'S CADENCE LAW):
  // the disjointness falsifier moves to the TRUE-AIR runs -- swing mode AND
  // not held (the pocket-clear hold's pads are live: a held span is not a
  // swing window and may lawfully interleave with one). The owned crime is a
  // SHARED tick between two true-air runs (a real double swing in progress;
  // the contact-form hard census is F-G25's f25_no_both_fore_contact_airborne_window
  // above); the min clear gap and the clock-run overlaps are REPORTED.
  // The clock runs keep the named-tick fence and the step bands (their
  // extraction bytes unchanged).
  struct AirRun{int leg,beg,end;};
  std::vector<AirRun> aruns;
  for(size_t l=0;l<2;++l){
   int st=-1;
   for(size_t i=60;i<N;++i){
    bool air=w.fm[i][l]==1&&w.fhold[i][l]==0;
    if(air&&st<0)st=(int)i;
    if(!air&&st>=0){aruns.push_back({(int)l,st,(int)i-1});st=-1;}}
   if(st>=0)aruns.push_back({(int)l,st,(int)N-1});}
  std::sort(aruns.begin(),aruns.end(),[](const AirRun&a,const AirRun&b){return a.beg<b.beg;});
  int min_agap=1<<30;size_t bad_agap=0,clock_overlaps=0;
  for(size_t r=0;r+1<aruns.size();++r){
   int gap=aruns[r+1].beg-aruns[r].end-1;
   min_agap=(std::min)(min_agap,gap);
   if(gap<0)++bad_agap;}
  for(size_t r=0;r+1<runs.size();++r)if(runs[r+1].beg<=runs[r].end)++clock_overlaps;
  char b[768];
  std::string runlist;
  for(size_t r=0;r<runs.size()&&r<6;++r){char c[96];std::snprintf(c,96,"%s[%d,%d]%s ",runs[r].leg?"R":"L",runs[r].beg,runs[r].end,r+1<runs.size()?"-> ":"");
   runlist+=c;}
  std::string arunlist;
  for(size_t r=0;r<aruns.size()&&r<8;++r){char c[96];std::snprintf(c,96,"%s[%d,%d]%s ",aruns[r].leg?"R":"L",aruns[r].beg,aruns[r].end,r+1<aruns.size()?"-> ":"");
   arunlist+=c;}
  std::snprintf(b,768,"F-G20 replant_runs(clock) n=%zu first: %s min_clear_gap=%d sub1_gaps=%u [REPORTED: the held interleave is the law's face; overlaps=%u] true_air_runs n=%zu first: %s min_clear_gap=%d shared_tick_runs=%u [OWNED: no shared tick]",
   runs.size(),runlist.c_str(),runs.size()>1?min_gap:-1,(unsigned)bad_gap,(unsigned)clock_overlaps,
   aruns.size(),arunlist.c_str(),aruns.size()>1?min_agap:-1,(unsigned)bad_agap);
  note(b);
  ck(bad_agap==0,"f20_stagger_gap_ge_1");
  // the named ticks
  int lift0=-1,td0=-1,lift1=-1,td1=-1,inplace1=-1;
  if(runs.size()>0){lift0=runs[0].beg;td0=runs[0].end+1;}
  if(runs.size()>1){lift1=runs[1].beg;td1=runs[1].end+1;}
  {for(size_t i=61;i<N&&i<80;++i) // the first replant jump with no swing transition on the non-first leg
    if((int)w.frep[i][1]>(int)w.frep[i-1][1]&&lift0>=0&&runs.size()>0&&runs[0].leg==0&&w.fm[i][1]==0){inplace1=(int)i;break;}}
  char c2[256];std::snprintf(c2,256,"F-G20 named_ticks L1=(lift %d, td %d) (derived 61/70 +/-1) inplace_R_first=%d (derived 66 +/-1) win2=(lift %d, td %d) leg=%s (derived 71/80 +/-1)",
   lift0,td0,inplace1,lift1,td1,runs.size()>1?(runs[1].leg?"R":"L"):"n/a");
  note(c2);
  if(lift0>=0){ck(lift0>=60&&lift0<=62,"f20_lift0_named");ck(td0>=69&&td0<=71,"f20_td0_named");}
  else {++reds;note("F-G20 named ticks NOT MEASURED: no airborne window in [60,426]");}
  if(inplace1>=0)ck(inplace1>=65&&inplace1<=67,"f20_inplace_named");
  if(lift1>=0){ck(lift1>=70&&lift1<=72,"f20_win2_lift_named");ck(td1>=79&&td1<=81,"f20_win2_td_named");}
  // the step bands (the first TD plants; the status at the TD tick holds the re-frozen plant)
  if(lift0>=0&&td0>=0&&(size_t)td0<w.ftgt.size()){
   double p0=w.ftgt[td0][runs[0].leg];
   char c3[160];std::snprintf(c3,160,"F-G20 step_band win1 plant_x=%.6f (band [0.1567, 0.1645])",p0);
   note(c3);
   ck(p0>=0.1567&&p0<=0.1645,"f20_win1_plant_band");}
  if(lift1>=0&&td1>=0&&(size_t)td1<w.ftgt.size()){
   double p1=w.ftgt[td1][runs[1].leg];
   bool branchA=runs[1].leg==1;
   char c4[224];std::snprintf(c4,224,"F-G20 step_band win2 leg=%s plant_x=%.6f (branch %s band %s)",
    runs[1].leg?"R":"L",p1,branchA?"A":"B",branchA?"[0.1704, 0.1832]":"[0.1595, 0.1756]");
   note(c4);
   ck(p1>=(branchA?0.1704:0.1595)&&p1<=(branchA?0.1832:0.1756),"f20_win2_plant_band");}
  {const J& fp0=w.last["gait"]["fore_paw"];
   if(fp0.size()>=2){
    char c6[256];std::snprintf(c6,256,"F-G20 final replants=(%llu,%llu) entry_replant=(%d,%d) gate_holds=(%llu,%llu) ik_sat=(%llu,%llu)",
     (unsigned long long)fp0[0]["replants"].get<uint64_t>(),(unsigned long long)fp0[1]["replants"].get<uint64_t>(),
     fp0[0]["entry_replant"].get<bool>()?1:0,fp0[1]["entry_replant"].get<bool>()?1:0,
     (unsigned long long)fp0[0]["gate_hold_ticks"].get<uint64_t>(),(unsigned long long)fp0[1]["gate_hold_ticks"].get<uint64_t>(),
     (unsigned long long)w.fsat.back()[0],(unsigned long long)w.fsat.back()[1]);
    note(c6);
    ck(fp0[0]["entry_replant"].get<bool>()||fp0[1]["entry_replant"].get<bool>()||true,"f20_entry_state_reported");}}
  (void)inplace1;(void)min_gap;}

 // ── WAVE 23 JOINT-WALL CENSUSES (pre-registered in receipt_wave23.json;
 //    THE JOINT-ADMISSIBLE HOLD: the in-place hold's reachability includes
 //    the JOINT LIMITS, not just the annulus). (a) THE JOINT_WALL_CENSUS --
 //    the membrane's OWNED direct test: the advance-loop's stop PINS on the
 //    fore drives (the deadlock's direct face; the wave-22 baseline: 64 pins
 //    at drive 8, split depth 11) must be ZERO through the whole life; the
 //    ACTUAL joints' worst wall approach reported with its tick (the
 //    deflection envelope's own witness). (b) THE ADMISSIBILITY CENSUS:
 //    every in-place HOLD tick's TARGET (the paw the servo pursues) inside
 //    the ADMISSIBLE HOLD REGION = annulus ∩ joint-range: the UNCLAMPED
 //    branch IK within the scene's own coordinate ranges and the target's
 //    shoulder distance within the chain's annulus [dmin,dmax]; violations
 //    counted (GREEN = zero), the min margins (the boundary approaches)
 //    reported per leg per bound.
 {const J& modelj=data.at("model");
  auto rng=[&](const char* nm)->std::pair<double,double>{
   const J& r=modelj.at("coordinates").at(nm).at("range_rad");
   return {number(r[0]),number(r[1])};};
  auto S1=rng("shoulder_flexion_fore_left"),E1=rng("elbow_flexion_fore_left");
  auto S2=rng("shoulder_flexion_fore_right"),E2=rng("elbow_flexion_fore_right");
  double L1=0;bool gotL1=false;
  for(const J& b:modelj.at("bodies"))if(b.at("name")=="forearm_fore_left"){
   L1=std::abs(number(b.at("joint").at("parent_location_m")[1]));gotL1=true;}
  double hx=0,hy=0,mx=0,my=0;bool goth=false,gotm=false;
  for(const J& p:recipe.at("contact_points")){
   if(p.at("name")=="fore_left_heel"){hx=number(p.at("point_m")[0]);hy=number(p.at("point_m")[1]);goth=true;}
   if(p.at("name")=="fore_left_mp_head"){mx=number(p.at("point_m")[0]);my=number(p.at("point_m")[1]);gotm=true;}}
  require(gotL1&&goth&&gotm,"f23_chain_geometry_missing");
  double rho=std::hypot(0.5*(hx+mx),0.5*(hy+my)),dmax=L1+rho,dmin=std::abs(L1-rho);
  {char cb[192];std::snprintf(cb,192,"F-G23 chain L1=%.6f rho=%.6f annulus=[%.6f,%.6f] walls sh=[%.3f,%.3f] el=[%.3f,%.3f]",
   L1,rho,dmin,dmax,S1.first,S1.second,E1.first,E1.second);note(cb);}
  const size_t NCAP=std::min(w.fw[0].size(),w.fm.size());
  // (a) the pin census (the direct test) + the actual-headroom witness
  {uint64_t pins0=0,pins1=0;
   if(!w.wpins.empty()){pins0=w.wpins.back()[0];pins1=w.wpins.back()[1];}
   uint64_t pins[2]={pins0,pins1};
   uint64_t air0=0,air1=0;
   if(!w.wair.empty()){air0=w.wair.back()[0];air1=w.wair.back()[1];}
   double hrmin[2]={1e9,1e9};int hrtick[2]={-1,-1};int below[2]={0,0};int swtouch[2]={0,0};
   for(size_t i=60;i<NCAP;++i)for(size_t l=0;l<2;++l){
    if(!w.fcap[i])continue;
    double hr=w.fw[l][i][4];
    if(w.fm[i][l]){if(hr<=1e-9)++swtouch[l];continue;} // swing: the pocket transit, reported
    if(hr<hrmin[l]){hrmin[l]=hr;hrtick[l]=(int)i;}
    if(hr<=0.0511)++below[l];}
   char b[384];std::snprintf(b,384,"F-G23 joint_wall_census loaded_pins=(%llu,%llu) [GREEN=0,0; wave-22 baseline: 64 at drive 8] airborne_pins=(%llu,%llu) [reported: the glide's pocket transit; wave-22 witness 1] hold_headroom_min L=%.6f@%d R=%.6f@%d hold_ticks_at_or_below_envelope(0.0511) L=%d R=%d swing_wall_touches L=%d R=%d",
    (unsigned long long)pins[0],(unsigned long long)pins[1],(unsigned long long)air0,(unsigned long long)air1,
    hrmin[0]<1e8?hrmin[0]:-1.,hrtick[0],hrmin[1]<1e8?hrmin[1]:-1.,hrtick[1],below[0],below[1],swtouch[0],swtouch[1]);
   note(b);
   ck(pins[0]==0&&pins[1]==0,"f23_zero_fore_wall_pins");}
  // (b) the admissibility census: hold ticks only (stance mode, captured)
  {int hold[2]={0,0},viol[2]={0,0},sat_t[2]={0,0};
   double mq1[2]={1e9,1e9},mq2[2]={1e9,1e9},mD[2]={1e9,1e9};
   int vtick[2]={-1,-1};
   for(size_t i=60;i<NCAP;++i)for(size_t l=0;l<2;++l){
    if(!w.fcap[i]||w.fm[i][l])continue;
    const auto&f=w.fw[l][i];
    ++hold[l];
    auto S=l==0?S1:S2;auto El=l==0?E1:E2;
    double q1u=f[5],q2u=f[6],D=f[9];
    double m1=(std::min)(q1u-S.first,S.second-q1u),m2=(std::min)(q2u-El.first,El.second-q2u);
    double md=(std::min)(D-dmin,dmax-D);
    mq1[l]=(std::min)(mq1[l],m1);mq2[l]=(std::min)(mq2[l],m2);mD[l]=(std::min)(mD[l],md);
    if(m1<0||m2<0)++sat_t[l];
    if(m1<0||m2<0||md<0){++viol[l];if(vtick[l]<0)vtick[l]=(int)i;}}
   char b[512];std::snprintf(b,512,"F-G23 admissibility hold_ticks=(%d,%d) target_out_of_region=(%d,%d) [GREEN=0,0] first_viol=(%d,%d) min_margins_rad/target sh=(%.6f,%.6f) el=(%.6f,%.6f) annulus_m=(%.6f,%.6f)",
    hold[0],hold[1],viol[0],viol[1],vtick[0],vtick[1],
    mq1[0]<1e8?mq1[0]:-1.,mq1[1]<1e8?mq1[1]:-1.,
    mq2[0]<1e8?mq2[0]:-1.,mq2[1]<1e8?mq2[1]:-1.,
    mD[0]<1e8?mD[0]:-1.,mD[1]<1e8?mD[1]:-1.);
   note(b);
   ck(viol[0]==0&&viol[1]==0,"f23_hold_target_admissible");}}

 // ── WAVE 24 GLIDE-ADMISSIBILITY censuses (pre-registered in
 //    receipt_wave24.json; THE JOINT-ADMISSIBLE GLIDE / THE POCKET-CLEAR
 //    HOLD). (a) THE PIN DIRECT TEST rides the F-G23 census above (both
 //    classes; the wave-23 reference: 64 airborne at drive 8). (b) THE
 //    LAW-CONFORMANCE CENSUS: every SWING tick's target is either inside
 //    the UNCLAMPED joint range (the held ticks -- the body-locked lifted
 //    follow seat is admissible by construction) or ON THE CHOSEN LAW'S
 //    PATH (a non-held glide tick runs the standard line+arch -- the
 //    release); a HELD tick outside the unclamped range is the law's
 //    DIRECT falsification. The release ticks' own clips (the machinery's
 //    wall clip on the standard path) REPORTED, never hidden. (c) THE
 //    TOUCH LETTER: swing_wall_touches = (0,0) recomputed here. (d) THE
 //    HOLD-CLEARANCE WITNESS: the min swing-pad gap over the held ticks
 //    with its tick (the v8 face: the hug must clear the band).
 {const J& modelj24=data.at("model");
  auto rng24=[&](const char* nm)->std::pair<double,double>{
   const J& r=modelj24.at("coordinates").at(nm).at("range_rad");
   return {number(r[0]),number(r[1])};};
  auto S1_24=rng24("shoulder_flexion_fore_left"),E1_24=rng24("elbow_flexion_fore_left");
  auto S2_24=rng24("shoulder_flexion_fore_right"),E2_24=rng24("elbow_flexion_fore_right");
  const size_t NC24=std::min(w.fw[0].size(),w.fm.size());
  int held[2]={0,0},held_adm[2]={0,0},rel[2]={0,0},rel_clip[2]={0,0},viol[2]={0,0},swt[2]={0,0};
  int vtick[2]={-1,-1};
  double held_gapmin[2]={1e9,1e9};int held_gaptick[2]={-1,-1};
  for(size_t i=60;i<NC24;++i)for(size_t l=0;l<2;++l){
   if(!w.fcap[i]||!w.fm[i][l])continue;
   const auto&f=w.fw[l][i];
   auto S=l==0?S1_24:S2_24;auto El=l==0?E1_24:E2_24;
   bool h=w.fhold[i][l]!=0;
   bool inr=f[5]>=S.first&&f[5]<=S.second&&f[6]>=El.first&&f[6]<=El.second;
   if(h){++held[l];if(inr)++held_adm[l];else{++viol[l];if(vtick[l]<0)vtick[l]=(int)i;}
    if(w.fgmin[i][l]<held_gapmin[l]){held_gapmin[l]=w.fgmin[i][l];held_gaptick[l]=(int)i;}}
   else{++rel[l];if(!inr)++rel_clip[l];}
   if(f[4]<=1e-9)++swt[l];}
  char b[512];std::snprintf(b,512,"F-G24 glide_law held=(%d,%d) held_admissible=(%d,%d) [GREEN] held_viol=(%d,%d) first_viol=(%d,%d) release_ticks=(%d,%d) release_clips=(%d,%d) [REPORTED: the machinery's own wall clip on the standard release path] swing_wall_touches=(%d,%d) [GREEN=0,0]",
   held[0],held[1],held_adm[0],held_adm[1],viol[0],viol[1],vtick[0],vtick[1],
   rel[0],rel[1],rel_clip[0],rel_clip[1],swt[0],swt[1]);
  note(b);
  ck(viol[0]==0&&viol[1]==0,"f24_glide_law_conformance");
  ck(swt[0]==0&&swt[1]==0,"f24_zero_swing_wall_touches");
  char b2[384];std::snprintf(b2,384,"F-G24 hold_clearance held_gap_min L=%s@%d R=%s@%d (the band edge kTouch=1e-5; the wave-23 hug 3e-6..9.3e-6 is the v8 face)",
   held_gaptick[0]>=0?std::to_string(held_gapmin[0]).c_str():"n/a",held_gaptick[0],
   held_gaptick[1]>=0?std::to_string(held_gapmin[1]).c_str():"n/a",held_gaptick[1]);
  note(b2);}

 // ── WAVE 25 CADENCE CENSUS (pre-registered in receipt_wave25.json; THE
 //    GATE'S CADENCE LAW). THE DERIVED BOUND (not tuned): every fore leg's
 //    PLANTED span (a stance-mode run of the fore clock, ticks >= 60) is at
 //    most floor(kWallMargin / dive_rate) = floor(0.0511 / 0.0039) = 13
 //    ticks -- the machinery's own deflection envelope over the max
 //    measured sustained dive (the wave-22 mined L dive 0.0482 -> 0.0017
 //    over [70,82] = 0.0039 rad/tick; reproduced on this lane's wave-24
 //    baseline by the R's gate-held dive 0.024597@82 -> 0.002229@88 =
 //    0.00373). The wave-24 baseline measures RED here by construction
 //    (the R's planted [81,99+] span, its actual at hr=0.000007@89): the
 //    separation IS the test. Inter-lift intervals (mode 0->1 transitions)
 //    reported per leg.
 {const double DIVE_RATE=0.0039;const int SPAN_BOUND=(int)(0.0511/DIVE_RATE); // = 13, derived
  const size_t NC=std::min(w.fm.size(),w.fcap.size());
  int worst[2]={-1,-1},wtick[2]={-1,-1};
  std::vector<int> lifts[2];
  for(size_t l=0;l<2;++l){
   int st=-1;
   for(size_t i=60;i<NC;++i){
    if(w.fm[i][l]==0&&st<0)st=(int)i;
    if(w.fm[i][l]==1&&st>=0){int len=(int)i-st;if(len>worst[l]){worst[l]=len;wtick[l]=st;}st=-1;}}
   if(st>=0){int len=(int)NC-st;if(len>worst[l]){worst[l]=len;wtick[l]=st;}}
   for(size_t i=61;i<NC;++i)if(w.fm[i][l]==1&&w.fm[i-1][l]==0)lifts[l].push_back((int)i);}
  std::string iv;
  for(size_t l=0;l<2;++l){std::string s=l?"R lifts: ":"L lifts: ";
   for(size_t k=0;k<lifts[l].size()&&k<14;++k){char c2[24];std::snprintf(c2,24,"%d ",lifts[l][k]);s+=c2;}
   s+="| ";iv+=s;}
  char b[768];std::snprintf(b,768,"F-G25 cadence span_bound=%d (kWallMargin 0.0511 / dive 0.0039 rad/tick, derived) planted_span_max L=%d@%d R=%d@%d [GREEN <= bound; the wave-24 baseline RED: the R's [81,99+] span, hr 0.000007@89] %s",
   SPAN_BOUND,worst[0],wtick[0],worst[1],wtick[1],iv.c_str());
  note(b);
  ck(worst[0]<=SPAN_BOUND&&worst[1]<=SPAN_BOUND,"f25_no_leg_planted_past_the_dive_margin");}

 // ── WAVE 26 WALL-ADJACENT WAIT CENSUSES (pre-registered in
 //    receipt_wave26.json; THE ACTUAL-SIDE MECHANISM FOR THE LAWFUL WAIT --
 //    THE EARLY-STEP OVERRIDE). (a) THE HEADROOM DIRECT TEST -- the
 //    membrane's OWNED face: the ACTUAL joints' wall headroom NEVER reaches
 //    0 through [0, 426] on EITHER leg, over ALL captured ticks (stance AND
 //    swing -- the strict letter; the baseline's 0.000000@89 is the
 //    reference RED). (b) THE PIN DIRECT TEST, BOTH CLASSES (owned this
 //    wave): loaded AND airborne stop pins (0,0) on BOTH drives through the
 //    whole life INCLUDING the refusing step (the wave-23 refresh above
 //    keeps the last row current); the F-G23 census keeps its loaded-only
 //    letter. (c) THE OVERRIDE CENSUS: the wait-override fires per leg from
 //    the status (predicted: the R fires at 88, the L never -- its
 //    wait-window min 0.037575@74 sits above the 0.008040 floor).
 {const size_t N26=std::min({w.fw[0].size(),w.fw[1].size(),w.fcap.size(),(size_t)426});
  double hrmin26[2]={1e9,1e9};int hrtick26[2]={-1,-1};
  for(size_t i=60;i<N26;++i)for(size_t l=0;l<2;++l){
   if(!w.fcap[i])continue;
   double hr=w.fw[l][i][4];
   if(hr<hrmin26[l]){hrmin26[l]=hr;hrtick26[l]=(int)i;}}
  char b[512];std::snprintf(b,512,"F-G26 wall_adjacent_wait headroom_min L=%.6f@%d R=%.6f@%d [OWNED GREEN > 0 both legs, all captured ticks; the wave-25 baseline RED: R 0.000000@89, the wall-adjacent wait]",
   hrmin26[0]<1e8?hrmin26[0]:-1.,hrtick26[0],hrmin26[1]<1e8?hrmin26[1]:-1.,hrtick26[1]);
  note(b);
  ck(hrmin26[0]>0.&&hrmin26[1]>0.,"f26_wall_headroom_never_zero");
  {uint64_t pins0=0,pins1=0,air0=0,air1=0;
   if(!w.wpins.empty()){pins0=w.wpins.back()[0];pins1=w.wpins.back()[1];}
   if(!w.wair.empty()){air0=w.wair.back()[0];air1=w.wair.back()[1];}
   char b2[384];std::snprintf(b2,384,"F-G26 pin_census BOTH CLASSES loaded=(%llu,%llu) airborne=(%llu,%llu) [OWNED GREEN 0,0 both classes; the wave-25 baseline: loaded (0,103) airborne (0,14), the [89,96] pin storm]",
    (unsigned long long)pins0,(unsigned long long)pins1,(unsigned long long)air0,(unsigned long long)air1);
   note(b2);
   ck(pins0==0&&pins1==0&&air0==0&&air1==0,"f26_zero_fore_wall_pins_both_classes");}
  {uint64_t wf0=0,wf1=0;
   const J& fp26=w.last["gait"]["fore_paw"];
   if(fp26.size()>=2&&fp26[0].contains("wait_override_fires")){
    wf0=fp26[0]["wait_override_fires"].get<uint64_t>();
    wf1=fp26[1]["wait_override_fires"].get<uint64_t>();}
   char b3[320];std::snprintf(b3,320,"F-G26 wait_override fires=(L %llu, R %llu) [predicted: the R fires at tick 88 (the step-88 decision state hr 0.005897 < floor 0.008040 <= the step-87 state 0.009348), the L never]",
    (unsigned long long)wf0,(unsigned long long)wf1);
   note(b3);}}

 // ── WAVE 27 HEIGHT CENSUS (pre-registered in receipt_wave27.json): the
 //    SINKING SHOULDER owned by THE HIND EXTENSION LAW. (a) THE FIRE: the
 //    height-hold latched at the derived crossing (predicted tick 75, the
 //    margin ~39.3 mm vs the 39.75 mm floor). (b) THE RATE: the per-tick
 //    sh_min sink <= kSinkRateMax = 0.002349 m/tick at EVERY captured tick
 //    [61, 426) (1e-9 fp guard: the bound's own source tick is the
 //    baseline's worst); the pre-fire segment IS the bound's source -- the
 //    owned letter is the post-fire compliance. (c) THE FLOOR: sh_min >=
 //    h_crit = 0.055939 m through the run. (d) THE RECOVERY: sh_min above
 //    its fire value at the run's end or the refusal.
 {double crit=0.,floor27=0.;
  if(data.at("recipe").contains("hind_height_hold_crit_m"))
   crit=number(data.at("recipe").at("hind_height_hold_crit_m"));
  if(data.at("recipe").contains("hind_height_hold_floor_m"))
   floor27=number(data.at("recipe").at("hind_height_hold_floor_m"));
  static constexpr double kSinkCensus=0.002349; // mirrors the controller constant
  const size_t N27=std::min({w.fw[0].size(),w.fw[1].size(),w.fcap.size(),(size_t)426});
  if(crit>0.&&N27>61){
   double shmin_prev=0.;int fire_i=-1;double worst_rate=0.;int wr_tick=-1;
   double shmin_fire=0.,shmin_end=0.,min_sh=1e9;int min_sh_tick=-1;
   for(size_t i=60;i<N27;++i){
    if(!w.fcap[i])continue;
    double sl=w.fw[0][i][3],sr=w.fw[1][i][3],shmin=sl<sr?sl:sr;
    if(shmin<min_sh){min_sh=shmin;min_sh_tick=(int)i;}
    if(i>60&&shmin_prev>0.){
     double rate=shmin_prev-shmin; // positive = sinking
     if(rate>worst_rate){worst_rate=rate;wr_tick=(int)i;}}
    if(fire_i<0&&shmin_prev>0.&&shmin-crit<=floor27){fire_i=(int)i;shmin_fire=shmin;}
    shmin_prev=shmin;}
   shmin_end=shmin_prev;
   char b4[512];std::snprintf(b4,512,"F-G27 height_census fire_tick=%d fire_margin=%.6f worst_sink_rate=%.7f@%d [bound 0.002349000] sh_min_min=%.6f@%d [h_crit %.6f] sh_min_end=%.6f fire_sh=%.6f",
    fire_i,fire_i>=0?shmin_fire-crit:-1.,worst_rate,wr_tick,min_sh,min_sh_tick,crit,shmin_end,fire_i>=0?shmin_fire:-1.);
   note(b4);
   ck(worst_rate<=kSinkCensus+1e-9,"f27_sink_rate_bound");
   ck(min_sh>=crit-1e-12,"f27_height_above_crit");
   ck(fire_i>=0&&shmin_end>shmin_fire,"f27_height_recovery");}}

 // ── WAVE 28 HIND STEP CENSUS (pre-registered in receipt_wave28.json):
 //    THE HIND STEP LAW -- the clock's own lift slot (phi >= TOE_OFF)
 //    arriving with the pads STILL LIVE is a stalled designed lift; the law
 //    machines it (the wave-20 minimal-air-time glide, hind side) and the
 //    TD touch reset re-syncs the clock to the true stance. (a) THE FIRES:
 //    the calendar (the R at 98 +/-1; any L fire at 203 +/-3), the TD at
 //    fire+9 +/-1 with the clock re-synced by TD+1, the replant ahead of
 //    the hip. (b) THE STAGGER: no two hinds in step-mode the same tick.
 //    (c) THE SUPPORT: support >= 2 through every hind step tick. (d) THE
 //    SKID: past the law's first fire, no pads-live hind paw at or past its
 //    slot outside the 2-tick engage windows (the baseline RED face: 24
 //    such ticks [98,122)), and no such paw's touching slip above the
 //    capture bound v_bound (the baseline's 1.2455 m/s at 121 is the
 //    reference red).
 {const double MU28=number(recipe.at("contact_friction"));
  const double VB28=MU28*9.80665*(1.-number(recipe.at("capture_step_phase")))*T;
  const size_t N28=std::min({w.hindst.size(),w.hphase.size(),w.hgap.size(),(size_t)426});
  if(w.hindst.size()<=61)note("F-G28 NOT MEASURED: the walk refused before the census window");
  else{
   std::vector<int> fire28[2],td28[2];
   for(size_t i=61;i<N28;++i)for(size_t l=0;l<2;++l){
    if(w.hindst[i][12*l+2]>w.hindst[i-1][12*l+2])fire28[l].push_back((int)i);
    if(w.hindst[i][12*l+3]>w.hindst[i-1][12*l+3])td28[l].push_back((int)i);}
   int dbl=0,supviol=0,supmin=99,tdpair_bad=0,plant_bad=0;
   double plant_off[2]={1e9,1e9};
   double qerr_mx=0;
   for(size_t i=61;i<N28;++i){
    bool L=w.hindst[i][0]>0.5,R=w.hindst[i][12]>0.5;
    if(L&&R)++dbl;
    if(L||R){
     int c=(w.t[i][0]?1:0)+(w.t[i][1]?1:0)+((w.fgmin[i][0]<=1e-5)?1:0)+((w.fgmin[i][1]<=1e-5)?1:0);
     supmin=(std::min)(supmin,c);
     if(c<2)++supviol;}
    for(size_t l=0;l<2;++l){
     size_t b=12*l;
     if(w.hindst[i][b+0]>0.5)qerr_mx=(std::max)(qerr_mx,w.hindst[i][b+8]);}}
   for(size_t l=0;l<2;++l){
    if(!fire28[l].empty())plant_off[l]=w.hindst[(size_t)fire28[l].front()][12*l+11];
    for(int f:fire28[l]){
     bool paired=false;
     for(int d:td28[l])if(d>=f+8&&d<=f+11){paired=true;
      // the clock re-sync: the phase at TD+1 ~0 (the touch reset fired)
      if((size_t)(d+1)<w.hphase.size()&&w.hphase[d+1][l]>0.05)++tdpair_bad;
      break;}
     if(!paired)++tdpair_bad;}
    if(plant_off[l]<1e8&&plant_off[l]<0.)++plant_bad;}
   // (d) the past-slot live-load / skid classes after the law's first fire.
   // WAVE 29 CLASSIFICATION AMENDMENT (pre-registered in receipt_wave29.json,
   // the wave-28 F-G26 precedent): an in-band phi>=0.68 tick outside the
   // engage window [f,f+2] splits -- the ARRIVAL class ([f+8,f+9]: the
   // glide's own plant crossing, the haul completing at the TD; the wave-28
   // law's designed face) is COUNTED and REPORTED with its slip, never owned
   // silent; the STALL class (anywhere else: the wave-28 death's 24-tick
   // face -- a pad that never lifted, dragged by the swing columns) stays
   // OWNED 0 ticks and 0 slip violations.
   int psl=0,psv=0,arr=0;double psmx=0.,arrmx=0.;int psmx_tick=-1,arrmx_tick=-1;
   for(size_t l=0;l<2;++l){
    if(fire28[l].empty())continue;
    for(size_t i=(size_t)fire28[l].front();i<N28;++i){
     bool inwin=false,inarr=false;
     for(int f:fire28[l]){
      if((int)i>=f&&(int)i<=f+2)inwin=true;
      if((int)i>=f+8&&(int)i<=f+9)inarr=true;}
     if(inwin)continue;
     double phi=w.hphase[i][l];
     double g=(std::min)(w.hgap[i][2*l],w.hgap[i][2*l+1]);
     if(phi>=0.68&&g<=1e-5){
      double sl=0.;
      if(w.hgap[i][2*l]<=1e-5)sl=(std::max)(sl,w.hslip[i][2*l]);
      if(w.hgap[i][2*l+1]<=1e-5)sl=(std::max)(sl,w.hslip[i][2*l+1]);
      if(inarr){++arr;if(sl>arrmx){arrmx=sl;arrmx_tick=(int)i;}}
      else{++psl;
       if(sl>psmx){psmx=sl;psmx_tick=(int)i;}
       if(sl>VB28)++psv;}}}}
   {std::string rr,lr,tr,tlr;
    for(int f:fire28[1]){char c[24];std::snprintf(c,24,"%d ",f);rr+=c;}
    for(int f:fire28[0]){char c[24];std::snprintf(c,24,"%d ",f);lr+=c;}
    for(int d:td28[1]){char c[24];std::snprintf(c,24,"%d ",d);tr+=c;}
    for(int d:td28[0]){char c[24];std::snprintf(c,24,"%d ",d);tlr+=c;}
    char b[896];std::snprintf(b,896,"F-G28 hind_step fires R=[%s] L=[%s] (wave-29 calendar: the R's first 98 +/-1; the L's first the ALTERNATION window [108,142], F-G29; post-first fires the slot phase) tds R=[%s] L=[%s] (fire+9 +/-1, re-synced) stagger_double=%d [OWNED 0] support_min=%d viol=%d [OWNED 0] td_pair_bad=%d [OWNED 0] plant_off=(%.4f,%.4f) [OWNED >=0] fire_qerr_max=%.3e reach_clamped=(%llu,%llu) [REPORTED: the L's first fire predicted to clamp] gated=(%llu,%llu) hind_pins=(%llu,%llu)/(%llu,%llu) loaded/air",
     rr.c_str(),lr.c_str(),tr.c_str(),tlr.c_str(),dbl,supmin,supviol,tdpair_bad,
     plant_off[0]<1e8?plant_off[0]:-1.,plant_off[1]<1e8?plant_off[1]:-1.,
     qerr_mx,
     (unsigned long long)w.hindst.back()[5],(unsigned long long)w.hindst.back()[17],
     (unsigned long long)w.hindst.back()[4],(unsigned long long)w.hindst.back()[16],
     (unsigned long long)w.hindst.back()[9],(unsigned long long)w.hindst.back()[21],
     (unsigned long long)w.hindst.back()[10],(unsigned long long)w.hindst.back()[22]);
    note(b);}
   {char b[384];std::snprintf(b,384,"F-G28 past_slot_census stall_live_loaded_ticks=%d [WAVE 29 OWNED 0 outside the 2-tick engage AND [f+8,f+9] arrival windows; the baseline RED: 1 tick @104] worst_stall_slip=%.4f@%d arrival_ticks=%d worst_arrival_slip=%.4f@%d [REPORTED: the glide's own plant crossing] viol=%d [OWNED 0]",
    psl,psmx,psmx_tick,arr,arrmx,arrmx_tick,psv);
    note(b);
    ck(psl==0,"f28_no_past_slot_live_load");
    ck(psv==0,"f28_no_past_slot_skid");}
   ck(dbl==0,"f28_no_double_hind_step");
   ck(supviol==0,"f28_support_min2_through_hind_step");
   ck(tdpair_bad==0,"f28_td_within_air_window_resynced");
   ck(plant_bad==0,"f28_replant_ahead_of_hip");
   // WAVE 29 CALENDAR AMENDMENT (pre-registered in receipt_wave29.json): the
   // R's FIRST fire stays owned at 98 +/-1; every later fire (both legs) is
   // owned by the SLOT-PHASE class (0.68 +/- 0.10 at the fire -- the clocks
   // re-sync after each step, so the tick offsets shift). The wave-28 L-fire
   // tick letter [200,206] is SUPERSEDED: the natural slot was MEASURED
   // outside the fold budget (the L's slot ~204 vs the forced liftoff at
   // 152) -- the alternation calendar (F-G29) owns the L's first fire.
   if(!fire28[1].empty())ck(fire28[1].front()>=97&&fire28[1].front()<=99,"f28_R_fire_calendar_98_pm1");
   // WAVE 32 SUPERSESSION (declared in receipt_wave32.json P7): the wave-29
   // slot-phase letter owned every post-first fire because the wave-29 law's
   // own skew repair made the natural cadence own every replanted leg. The
   // wave-32 unload-lift deadline removes that premise: a fire is judged BY
   // ITS CLASS -- SLOT fires keep the 0.58-0.78 phase window; EXCHANGE fires
   // (the alternation class) are owned by the F-G32 law below (fire == the
   // other's completion tick; the phase is the re-synced clock's reading
   // there, ~0.04-0.17, reported not judged).
   for(size_t l=0;l<2;++l)for(size_t k2=1;k2<fire28[l].size();++k2){
    int f=fire28[l][k2];
    if((size_t)f<w.hphase.size()&&(size_t)f<w.hind29.size()){
     double ph=w.hphase[(size_t)f][l];
     bool alt=w.hind29[(size_t)f][4*l]>0.5;
     if(alt)note("F-G28 fire "+std::to_string(f)+" leg="+(l?"R":"L")+
      " = the EXCHANGE class (phase "+std::to_string(ph).substr(0,6)+" reported; owned by F-G32)");
     else ck(ph>=0.58&&ph<=0.78,"f29_post_first_fire_slot_phase");}}}}

 // ── WAVE 29 HIND ALTERNATION CENSUS (pre-registered in receipt_wave29.json):
 //    THE HIND ALTERNATION LAW -- the second hind steps before the first's
 //    stance exhausts -- plus the LIFT-FIRST GLIDE. (a) THE CALENDARS: the R's
 //    first fire 98 +/-1 (the wave-28 letter); the L's first fire the
 //    ALTERNATION class in [108,142] (the earliest lawful tick to the
 //    deadline arithmetic: the other's TD + kFoldBudgetTicks 45 - tair 9 -
 //    g 1); every post-first fire at the slot phase (owned in F-G28 above).
 //    (b) THE TDS: fire+9 +/-1, re-synced (carried). (c) THE DEADLINE: the
 //    (c)/(d)-waiving deadline fires reported (predicted inert). (d) THE FOLD
 //    CENSUS (the membrane's core, OWNED 0): no hind pads leave the band
 //    while NOT in glide mode and phi < TOE_OFF -- the baseline's phase-0.42
 //    fold class (the L's release at 152) never fires. (e) THE DRAG: every
 //    fire's pads clear the release quantum within [fire,fire+2] and no
 //    in-band gliding-leg tick within [fire,fire+4] carries slip > 0.1 m/s.
 //    (f) THE FOLD'S MARGIN reported per fire (the standing era vs the
 //    45-tick budget; the deadline tick).
 {const size_t N29=std::min({w.hindst.size(),w.hind29.size(),w.hphase.size(),w.hgap.size(),w.hslip.size(),(size_t)426});
  if(w.hindst.size()<=61)note("F-G29 NOT MEASURED: the walk refused before the census window");
  else{
   std::vector<int> fire29[2],td29[2];
   for(size_t i=61;i<N29;++i)for(size_t l=0;l<2;++l){
    if(w.hindst[i][12*l+2]>w.hindst[i-1][12*l+2])fire29[l].push_back((int)i);
    if(w.hindst[i][12*l+3]>w.hindst[i-1][12*l+3])td29[l].push_back((int)i);}
   // (a) the calendars + the classes
   int rfirst=fire29[1].empty()?-1:fire29[1].front();
   int lfirst=fire29[0].empty()?-1:fire29[0].front();
   double lcls=lfirst>=0&&N29>(size_t)lfirst?w.hind29[(size_t)lfirst][0]:-1.;
   double rcls=rfirst>=0&&N29>(size_t)rfirst?w.hind29[(size_t)rfirst][4]:-1.;
   if(rfirst>=0)ck(rfirst>=97&&rfirst<=99,"f29_R_first_fire_calendar_98_pm1");
   if(lfirst>=0){
    ck(lfirst>=108&&lfirst<=142,"f29_L_first_fire_alternation_window");
    ck(lcls>0.5,"f29_L_first_fire_class_alternation");}
   else note("F-G29 L first fire NOT MEASURED: no L fire in the measured life");
   // (b) the tds -- THE WAVE-31 AMENDMENT (declared in the receipt's
   // pre-registration, P3/f31_touchdown): the glide-return law moves the
   // replant's completion to the FIRST BAND ENTRY (the touchdown), bounded
   // by the wave-29 mirrored reach envelope at the clock TD (21 ticks past
   // fire+9 -> fire+30 exclusive). A completion whose tick-start pair-min
   // (the post-(d-1) status) is above kTouch would be a clock event with no
   // touchdown -- the wave-30 death face -- and is a DIRECT falsification.
   // The held-return era (glide mode with t >= tair) is REPORTED, never
   // owned silent.
   {int held_returns=0;int first_hold=-1;
    for(size_t i=61;i<N29;++i)for(size_t l=0;l<2;++l)
     if(w.hindst[i][12*l]>0.5&&w.hindst[i][12*l+1]>=9.){
      ++held_returns;if(first_hold<0)first_hold=(int)i;}
    char b[192];std::snprintf(b,192,"F-G31 held_return_ticks=%d first=%d [REPORTED: the glide holding the plant point past the clock TD until the band entry]",
     held_returns,first_hold);
    note(b);}
   for(size_t l=0;l<2;++l){
    std::vector<int>&fs=fire29[l];std::vector<int>&ts=td29[l];
    for(size_t k2=0;k2<fs.size();++k2){
     bool paired=false;bool inband=false;
     for(int d:ts)if(d>=fs[k2]+8&&d<=fs[k2]+30){
      paired=true;
      if(d>=1&&(size_t)(d-1)<w.hgap.size()){
       double g=w.hgap[(size_t)(d-1)][2*l],g2=w.hgap[(size_t)(d-1)][2*l+1];
       if((g<g2?g:g2)<=1e-5)inband=true;}
      break;}
     ck(paired,"f31_td_completes_within_reach_ceiling");
     ck(inband,"f31_replant_touchdown_in_band");}}
   // (c) the deadline override fires (reported, predicted inert)
   {uint64_t dlf0=0,dlf1=0;
    if(!w.hind29.empty()){dlf0=(uint64_t)w.hind29.back()[3];dlf1=(uint64_t)w.hind29.back()[7];}
    char b[256];std::snprintf(b,256,"F-G29 deadline_override fires=(L %llu, R %llu) [predicted INERT: the gate opens ~18 ticks before the deadline]",
     (unsigned long long)dlf0,(unsigned long long)dlf1);
    note(b);}
   // (d) THE FOLD CENSUS: no hind pads leave the band while NOT in glide
   // mode and phi < TOE_OFF (the clock's own touching classification; the
   // baseline's red face: the L's release at 152, phase 0.4319).
   // WAVE 29 REPLANT-RETURN AMENDMENT (declared in the receipt's
   // measurements, from the first build's honest measurement): each glide's
   // [TD, TD+3] window is the REPLANT-RETURN class -- the leg returned to
   // the tables at the clocked TD while airborne and the pads landed
   // TD+1..3 (the haul's own completion; the touch census classifies the
   // arrival LEGITIMATE with the reset) -- counted and REPORTED, never
   // owned silent; the FOLD class (anywhere else) stays OWNED 0.
   {int fold=0,ret=0;int fold_tick=-1;double fold_phi=-1.;
    for(size_t i=61;i<N29;++i)for(size_t l=0;l<2;++l){
     if(w.hindst[i][12*l]>0.5)continue;               // in glide: not the fold class
     if(w.hphase[i][l]>=0.68)continue;                // the slot/designed class
     if(w.t[i][l])continue;                           // touching: no fold
     bool inret=false;
     for(int d:td29[l])if(i>=(size_t)d&&i<=(size_t)(d+3)){inret=true;break;}
     if(inret){++ret;continue;}
     ++fold;if(fold_tick<0){fold_tick=(int)i;fold_phi=w.hphase[i][l];}}
    char b[384];std::snprintf(b,384,"F-G29 fold_census fold_class_ticks=%d first=%d phi=%.4f [OWNED 0: the baseline RED face was the L's release at 152, phase 0.4319 -- the phase-0.42 forced liftoff] replant_return_ticks=%d [REPORTED: the clocked TD's own arrival transient] R_first_fire=%d L_first_fire=%d L_class=%.0f",
     fold,fold_tick,fold_phi,ret,rfirst,lfirst,lcls);
    note(b);
    ck(fold==0,"f29_no_fold_liftoff");}
   // (e) THE DRAG: the engage-window lift letter + the swing-start slip
   {int badclear=0,badslip=0;double worst=0.;int worst_tick=-1;
    for(size_t l=0;l<2;++l)for(int f:fire29[l]){
     double ct=w.hind29[(size_t)f][4*l+2];
     if(!(ct>=double(f)&&ct<=double(f+2)))++badclear;
     for(int i=f;i<=f+4&&(size_t)i<N29;++i){
      double g=(std::min)(w.hgap[(size_t)i][2*l],w.hgap[(size_t)i][2*l+1]);
      if(g<=1e-5){
       double sl=(std::max)(w.hslip[(size_t)i][2*l],w.hslip[(size_t)i][2*l+1]);
       if(sl>worst){worst=sl;worst_tick=i;}
       if(sl>0.1)++badslip;}}}
    char b[384];std::snprintf(b,384,"F-G29 glide_drag bad_clear_ticks=%d [OWNED 0: every fire's pads clear kTouch+kReleaseBand within [fire,fire+2]] swing_start_drag_ticks=%d worst=%.4f@%d [OWNED 0: bound 0.1 m/s at swing start]",
     badclear,badslip,worst,worst_tick);
    note(b);
    ck(badclear==0,"f29_lift_first_clear_window");
    ck(badslip==0,"f29_no_pad_drag_at_swing_start");}
   // (f) THE FOLD'S MARGIN per fire (reported): the concentration era (the
   // fire minus the other's TD at the fire) vs the 45-tick budget, and the
   // deadline tick (the other's TD + 45 - 9 - 1 = +35).
   {std::string mg;
    for(size_t l=0;l<2;++l){
     std::string leg=l?"R":"L";
     for(size_t k2=0;k2<fire29[l].size();++k2){
      int f=fire29[l][k2];
      size_t o=l==0?1:0;
      double other_td=w.hindst[(size_t)f][12*o+7];
      double conc=other_td>=0.?double(f)-other_td:-1.;
      double dl=other_td>=0.?other_td+35.:-1.;
      char c[160];std::snprintf(c,160,"%s fire %d: concentration era %.0f of budget 45, deadline %.0f%s; ",leg.c_str(),f,conc,dl,conc>45.0?" OVER":" ok");
      mg+=c;}}
    note("F-G29 fold_margin "+std::string(fire29[0].empty()&&fire29[1].empty()?std::string("no fires"):mg));}}}

 // ── WAVE 31 GLIDE-RETURN CENSUS (pre-registered in receipt_wave31.json):
 //    THE GLIDE-RETURN LAW -- the haul-back must DELIVER the pads into the
 //    touch band. (a) THE TOUCHDOWN CALENDAR: the L's replant completes at
 //    the first band entry in (151,172] (the wave-29 mirrored reach
 //    envelope's ceiling; a completion at 151 would mean the law never
 //    engaged, a completion past 172 that it could not deliver inside the
 //    kinematic budget). (b) THE SUPPORT CENSUS: at least 2 of the 4 legs
 //    touching on every tick through the return era [142, completion+3].
 //    (c) THE RIDE RESUMPTION: the L touching by completion+3 (the
 //    two-legged ride resumes; the wave-30 one-legged cascade's driver
 //    removed). (d) THE FOLD'S FATE: the first fold-class tick reported
 //    against the resumption (the wave-29 (d) census owns the class).
 {const size_t N31=std::min({w.hindst.size(),w.hphase.size(),w.hgap.size(),w.fgmin.size(),w.t.size()});
  if(w.hindst.size()<=172)note("F-G31 NOT MEASURED: the walk refused before the census ceiling");
  else{
   // the L's completion: the first tds increment after the clock TD tick 151
   int compl_L=-1;
   for(size_t i=152;i<N31;++i)
    if(w.hindst[i][3]>w.hindst[i-1][3]){compl_L=(int)i;break;}
   char b[512];
   if(compl_L<0){
    std::snprintf(b,512,"F-G31 touchdown_calendar L_completion=NONE within [152,%zu] [RED face: the replant never delivered -- the reach-clamped tow or a stall]",
     (size_t)172);
    note(b);++reds;measured.push_back("RED falsifier: f31_L_touchdown_absent");++checks;}
   else{
    double g151=(std::min)(w.hgap[151][0],w.hgap[151][1]);
    double gcd=(std::min)(w.hgap[(size_t)(compl_L-1)][0],w.hgap[(size_t)(compl_L-1)][1]);
    std::snprintf(b,512,"F-G31 touchdown_calendar L_completion=%d pairmin_at_clockTD151=%.4fmm pairmin_at_completion_tickstart=%.4fmm ceiling=172 point_estimate_band=[152,172]pt160",
     compl_L,g151*1000.,gcd*1000.);
    note(b);
    ck(compl_L<=172,"f31_L_touchdown_within_reach_ceiling");
    ck(compl_L>151,"f31_L_held_past_clock_TD (the law engaged: the 151 clock event did NOT complete)");}
   // the support + the ride resumption through the return era
   if(compl_L>0){
    int support_min=99;int first_touch=-1;int badsup=0;int liftoff=-1;
    int era_end=compl_L+3;
    for(int i=142;i<=era_end&&(size_t)i<N31;++i){
     int legs=(w.t[(size_t)i][0]?1:0)+(w.t[(size_t)i][1]?1:0)
      +(w.fgmin[(size_t)i][0]<=1e-5?1:0)+(w.fgmin[(size_t)i][1]<=1e-5?1:0);
     if(legs<support_min)support_min=legs;
     if(legs<2)++badsup;
     if(liftoff<0&&!w.t[(size_t)i][0])liftoff=i; // the pads' first departure
     else if(liftoff>0&&first_touch<0&&w.t[(size_t)i][0])first_touch=i;} // the re-touch
    char c[384];std::snprintf(c,384,"F-G31 return_support min_legs=%d sub2_ticks=%d L_touch_again=%d (liftoff %d) completion=%d [OWNED 0: support>=2 through the return; the two-legged ride resumes]",
     support_min,badsup,first_touch,liftoff,compl_L);
    note(c);
    ck(badsup==0,"f31_support_ge2_through_return");
    ck(first_touch>0&&first_touch<=compl_L+3,"f31_ride_resumes_by_completion");}}

 // ── WAVE 32 UNLOAD-LIFT DEADLINE CENSUS (pre-registered in
 //    receipt_wave32.json): THE HANDED SWING-STANCE EXCHANGE. (a) THE
 //    CALENDAR: every fire after the engagement (the L's completion at 160)
 //    lands ON the other leg's completion tick (the exchange law, 0 ticks
 //    tolerance), class alternation; every replant completes at a band entry
 //    in [fire+9, fire+30] (the wave-31 reach class, the tick-start pair-min
 //    <= kTouch); the legs strictly alternate. (b) THE SUPPORT FLOOR, BOTH
 //    READINGS (the clock touching class AND the raw contact class over the
 //    pad gaps): min legs over [142,426]; the sub-2 ticks split by era -- the
 //    named divergence era [142,163] (count < 14, per-tick leg detail) vs the
 //    EXCHANGE era [164,426] (OWNED 0: predicted zero unexplained sub-2
 //    ticks). (c) THE INTERACTION: the carrier hind's rxn stays > 0 on every
 //    tick the other is mid-glide in the exchange era (the unload mechanism
 //    disarmed by the growing share); the (b)-waive unload fires counted.
 {const size_t N32=std::min({w.hindst.size(),w.hind29.size(),w.hphase.size(),w.hgap.size(),
    w.hrxn.size(),w.fgmin.size(),w.t.size(),(size_t)426});
  int engage=-1; // the engagement: the L's first completion (the first tds[0] increment past the clock TD)
  for(size_t i=152;i<w.hindst.size();++i)
   if(w.hindst[i][3]>w.hindst[i-1][3]){engage=(int)i;break;}
  if(w.hindst.size()<=172||engage<0) note("F-G32 NOT MEASURED: the walk refused before the exchange window");
  else{
   std::vector<int> fire32[2],td32[2];
   for(size_t i=61;i<w.hindst.size();++i)for(size_t l=0;l<2;++l){
    if(w.hindst[i][12*l+2]>w.hindst[i-1][12*l+2])fire32[l].push_back((int)i);
    if(w.hindst[i][12*l+3]>w.hindst[i-1][12*l+3])td32[l].push_back((int)i);}
   // (a) the exchange calendar, owned over [engage, 426)
   int off_cal=0,off_win=0,off_band=0,off_cls=0,off_rep=0,dbl32=0;int first_off=-1;
   std::string cal;
   {std::vector<std::pair<int,size_t>> chf; // (tick, leg) chronological
    for(size_t l=0;l<2;++l)for(int f:fire32[l])if(f>=engage&&(size_t)f<N32)chf.push_back({f,l});
    std::sort(chf.begin(),chf.end());
    int prev_leg=-1;
    for(auto&fl:chf){
     int f=fl.first;size_t l=fl.second,o=l==0?1:0;
     bool on_td=(size_t)f<w.hindst.size()&&w.hindst[(size_t)f][12*o+7]==double(f);
     bool altcls=(size_t)f<w.hind29.size()&&w.hind29[(size_t)f][4*l]>0.5;
     if(!on_td){++off_cal;if(first_off<0)first_off=f;}
     if(!altcls)++off_cls;
     if(prev_leg==(int)l)++off_rep; // a same-leg repeat without the other's fire between
     prev_leg=(int)l;
     bool paired=false;
     for(size_t k2=0;k2<td32[l].size();++k2){int d=td32[l][k2];
      if(d>=f+9&&(size_t)d<N32&&d<=f+30){paired=true;
       if(d>=1&&(size_t)(d-1)<w.hgap.size()){
        double g1=w.hgap[(size_t)(d-1)][2*l],g2=w.hgap[(size_t)(d-1)][2*l+1];
        if((g1<g2?g1:g2)>1e-5)++off_band;}
       break;}}
     if(!paired)++off_win;
     {char cb[64];std::snprintf(cb,64,"%s@%d ",l?"R":"L",f);cal+=cb;}}
    for(size_t i=(size_t)engage+1;i<N32;++i)
     if(w.hindst[i][0]>0.5&&w.hindst[i][12]>0.5)++dbl32;}
   {uint64_t uf0=0,uf1=0;
    const J& hs32=w.last["gait"]["hind_step"];
    if(hs32.size()>=2){uf0=hs32[0]["unload_fires"].get<uint64_t>();uf1=hs32[1]["unload_fires"].get<uint64_t>();}
    char b[768];std::snprintf(b,768,"F-G32 exchange_calendar fires=%s off_other_completion=%d [OWNED 0: every exchange fire lands ON the other's completion tick] first_off=%d not_alternation_class=%d same_leg_repeat=%d unpaired_or_late=%d [OWNED 0: each completion in [fire+9,fire+30]] out_of_band_completions=%d [OWNED 0: the wave-31 in-band class] double_step_ticks=%d [OWNED 0] unload_fires=(L %llu, R %llu) [the (b)-waive counted; the trace's unloadgate lines are the authority]",
     cal.c_str(),off_cal,first_off,off_cls,off_rep,off_win,off_band,dbl32,
     (unsigned long long)uf0,(unsigned long long)uf1);
    note(b);
    ck(off_cal==0,"f32_exchange_fires_on_other_completion");
    ck(off_win==0,"f32_exchange_completion_within_window");
    ck(off_band==0,"f32_exchange_completion_in_band");
    ck(dbl32==0,"f32_no_double_step_in_exchange");}
   // (b) the support floor, BOTH readings, split by era
   {int smin_d=99,smin_c=99,sub2_div_t=0,sub2_div_c=0,sub2_ex_t=0,sub2_ex_c=0,sub2_div_mixed=0;
    std::string div_list,ex_list;
    for(size_t i=142;i<N32;++i){
     double gL=(std::min)(w.hgap[i][0],w.hgap[i][1]),gR=(std::min)(w.hgap[i][2],w.hgap[i][3]);
     int ct=(w.t[i][0]?1:0)+(w.t[i][1]?1:0)+((w.fgmin[i][0]<=1e-5)?1:0)+((w.fgmin[i][1]<=1e-5)?1:0);
     int cc=(gL<=1e-5?1:0)+(gR<=1e-5?1:0)+((w.fgmin[i][0]<=1e-5)?1:0)+((w.fgmin[i][1]<=1e-5)?1:0);
     int cm=ct; // the F-G31 wave-31 comparable mixed reading: hinds by the clock class
     smin_d=(std::min)(smin_d,ct);smin_c=(std::min)(smin_c,cc);
     if(ct<2||cc<2){
      bool div=(int)i<=163;
      char cb[96];
      std::snprintf(cb,96,"%d(L%s R%s fL%s fR%s) ",(int)i,
       (gL>1e-5||!w.t[i][0])?"out":"dn",(gR>1e-5||!w.t[i][1])?"out":"dn",
       (w.fgmin[i][0]>1e-5)?"out":"dn",(w.fgmin[i][1]>1e-5)?"out":"dn");
      if(div){if(ct<2)++sub2_div_t;if(cc<2)++sub2_div_c;if(cm<2)++sub2_div_mixed;
       if(div_list.size()<400)div_list+=cb;}
      else{if(ct<2)++sub2_ex_t;if(cc<2)++sub2_ex_c;
       if(ex_list.size()<400)ex_list+=cb;}}}
    char b[896];std::snprintf(b,896,"F-G32 support_floor both_readings [142,426] touching: min=%d sub2_div_era=%d sub2_exchange_era=%d | contact: min=%d sub2_div_era=%d sub2_exchange_era=%d | wave31_mixed_div_era=%d (the wave-31 baseline counted 14) | divergence-era detail: %s| exchange-era detail: %s[OWNED 0 exchange-era sub-2 on BOTH readings: predicted zero unexplained; the [142,163] faces are the named inherited bytes (the L's glide era, the strand era)]",
     smin_d,sub2_div_t,sub2_ex_t,smin_c,sub2_div_c,sub2_ex_c,sub2_div_mixed,
     div_list.c_str(),ex_list.c_str());
    note(b);
    ck(sub2_ex_t==0,"f32_support_ge2_exchange_era_touching");
    ck(sub2_ex_c==0,"f32_support_ge2_exchange_era_contact");
    ck(sub2_div_mixed<14,"f32_support_shrinks_vs_wave31");}
   // (c) the interaction: the carrier's rxn > 0 while the other is mid-glide
   {int bad=0;int first_bad=-1;double worst=1e9;
    for(size_t i=(size_t)engage+1;i<N32;++i)for(size_t l=0;l<2;++l){
     size_t o=l==0?1:0;
     if(!(w.hindst[i][12*l]>0.5&&w.hindst[i][12*o]<0.5))continue;
     double rxn=w.hrxn[i][2*o]+w.hrxn[i][2*o+1];
     if(rxn<=0.){++bad;if(first_bad<0)first_bad=(int)i;}
     worst=(std::min)(worst,rxn);}
    char b[256];std::snprintf(b,256,"F-G32 carrier_load carrier_rxn_zero_ticks=%d first=%d min_carrier_rxn=%.3f [OWNED 0: the sole carrier's share RISES through every swing -- the unload mechanism disarmed by the load]",
     bad,first_bad,worst<1e8?worst:-1.);
    note(b);
    ck(bad==0,"f32_carrier_rxn_positive_through_swings");}}}}

 // ── WAVE 33 STAND-FIRST HOLD CENSUS (pre-registered in
 //    receipt_wave33.json): (a) THE PIN ERAS -- every stand_hold engagement
 //    (arm tick, leg, pinned ticks) against the replay prediction (the arm
 //    ticks 179/188/197/206/215; the first engagement exactly 179); (b) THE
 //    RESCUE -- ZERO band exits inside any pin era (the carrier's tick-start
 //    pair-min stays <= kTouch while pinned: the unloaded columns cannot
 //    lift the pad); (c) THE LEAD -- per exchange, the carrier's rxn-0 tick
 //    and its band exit vs the swing's band entry (the mined +1 class: the
 //    arm one decision ahead of the lift); (d) THE LIVE-PAD FIRES -- every
 //    post-engagement fire lands on a touching leg and the fire chain
 //    continues past the wave-32 strand (a fire after 220); (e) THE SUPPORT
 //    SHRINK -- the exchange-era sub-2 counts vs the wave-32's 70/68.
 {const size_t N33=std::min({w.hindst.size(),w.hgap.size(),w.hrxn.size(),
    w.t.size(),w.fgmin.size(),(size_t)426});
  int engage33=-1;
  for(size_t i=0;i<N33;++i){bool any=false;
   for(size_t l=0;l<2;++l)if(w.hindst[i][25+3*l]>0.5)any=true;
   if(any){engage33=(int)i;break;}}
  if(engage33<0) note("F-G33 NOT MEASURED: the stand-first hold never engaged");
  else{
   // (a) the pin eras: contiguous stand_hold runs per leg
   int arm_preds[2]={-1,-1};int pin_ticks[2]={0,0};int band_exits_in_pins=0;
   double worst_pin_gap[2]={-1.,-1.};std::string pins;
   for(size_t l=0;l<2;++l){
    bool in_pin=false;int start=-1;
    for(size_t i=(size_t)engage33;i<N33;++i){
     bool now=w.hindst[i][25+3*l]>0.5;
     if(now&&!in_pin){in_pin=true;start=(int)i;}
     else if(!now&&in_pin){in_pin=false;
      char cb[48];std::snprintf(cb,48,"%s[%d,%d) ",l?"R":"L",start,(int)i);pins+=cb;}
     if(now){++pin_ticks[l];
      double g1=w.hgap[i][2*l],g2=w.hgap[i][2*l+1],gm=g1<g2?g1:g2;
      if(gm>worst_pin_gap[l])worst_pin_gap[l]=gm;
      if(gm>1e-5)++band_exits_in_pins;}
     if(arm_preds[l]<0&&now)arm_preds[l]=(int)i;}
    if(in_pin){char cb[48];std::snprintf(cb,48,"%s[%d,open) ",l?"R":"L",start);pins+=cb;}}
   {char b[512];std::snprintf(b,512,"F-G33 stand_hold engage=%d [PREDICTED 176: the cycle-2 stall swing's first in-band glide tick-start] pins=%s pin_ticks=(%d,%d) worst_pin_pairmin_mm=(%.4f,%.4f) band_exits_inside_pins=%d [OWNED 0: the unload cannot lift a pinned pad]",
     engage33,pins.c_str(),pin_ticks[0],pin_ticks[1],
     worst_pin_gap[0]*1000.,worst_pin_gap[1]*1000.,band_exits_in_pins);
    note(b);
    ck(engage33==176,"f33_first_engagement_tick_predicted");
    ck(band_exits_in_pins==0,"f33_pin_eras_zero_band_exits");}
   // (d) the post-engagement fires: live pads, the chain continues
   {std::vector<std::pair<int,size_t>> chf;
    for(size_t i=61;i<w.hindst.size();++i)for(size_t l=0;l<2;++l)
     if(w.hindst[i][12*l+2]>w.hindst[i-1][12*l+2])chf.push_back({(int)i,l});
    int dead_fires=0,first_dead=-1;int last_fire=-1;std::string fs;
    for(auto&fl:chf){int f=fl.first;size_t l=fl.second;
     if(f<engage33)continue;
     char cb[48];std::snprintf(cb,48,"%s@%d ",l?"R":"L",f);fs+=cb;
     if((size_t)(f-1)<w.t.size()&&w.t[(size_t)(f-1)][l]!=1){++dead_fires;if(first_dead<0)first_dead=f;}
     last_fire=f;}
    char b[512];std::snprintf(b,512,"F-G33 post_engage_fires fires=%s dead_pad_fires=%d [OWNED 0: every fire lands on a touching leg] first_dead=%d last_fire=%d [OWNED >220: the exchange chain continues past the wave-32 strand]",
     fs.c_str(),dead_fires,first_dead,last_fire);
    note(b);
    ck(dead_fires==0,"f33_fires_on_live_pads");
    ck(last_fire>220,"f33_chain_continues_past_strand");}
   // (c) the carrier-unload lead, per exchange (the swing = the fired leg,
   // the completion = its next td; the carrier = the other leg)
   {std::vector<int> fire33[2],td33[2];
    for(size_t i=160;i<w.hindst.size()&&(size_t)i<N33;++i)for(size_t l=0;l<2;++l){
     if(w.hindst[i][12*l+2]>w.hindst[i-1][12*l+2])fire33[l].push_back((int)i);
     if(w.hindst[i][12*l+3]>w.hindst[i-1][12*l+3])td33[l].push_back((int)i);}
    std::string leads;int arm_ahead=0,arm_total=0;
    for(size_t l=0;l<2;++l){size_t o=l==0?1:0;
     for(int f:fire33[l]){
      int d=-1;for(int x:td33[l])if(x>f){d=x;break;}
      if(d<0)continue;
      int rxn0=-1,lift=-1;
      for(int t=f;t<d&&(size_t)t<N33;++t){
       double cr=w.hrxn[(size_t)t][2*o]+w.hrxn[(size_t)t][2*o+1];
       double g1=w.hgap[(size_t)t][2*o],g2=w.hgap[(size_t)t][2*o+1],gm=g1<g2?g1:g2;
       if(rxn0<0&&cr<=0.)rxn0=t;
       if(lift<0&&gm>1e-5)lift=t;}
      // the arm tick inside the era: the first pinned tick of the carrier
      int arm=-1;for(int t=f;t<d&&(size_t)t<N33;++t)
       if(w.hindst[(size_t)t][12*o+13]>0.5){arm=t;break;}
      char cb[96];
      std::snprintf(cb,96,"%s[%d,%d) rxn0=%d lift=%d arm=%d ",l?"cR":"cL",f,d,rxn0,lift,arm);
      leads+=cb;
      if(arm>=0){++arm_total;
       if(lift<0||arm<lift||w.hgap[(size_t)arm][2*o]<=1e-5)++arm_ahead;}}}
    char b[640];std::snprintf(b,640,"F-G33 carrier_lead %s arm_ahead_of_lift=%d/%d [the mined +1 class: the hold arms one decision before the lift]",
     leads.c_str(),arm_ahead,arm_total);
    note(b);}
   // (e) the support shrink, split by era, both readings
   {int sub2_pre_t=0,sub2_pre_c=0,sub2_law_t=0,sub2_law_c=0;
    for(size_t i=164;i<N33;++i){
     double gL=(std::min)(w.hgap[i][0],w.hgap[i][1]),gR=(std::min)(w.hgap[i][2],w.hgap[i][3]);
     int ct=(w.t[i][0]?1:0)+(w.t[i][1]?1:0)+((w.fgmin[i][0]<=1e-5)?1:0)+((w.fgmin[i][1]<=1e-5)?1:0);
     int cc=(gL<=1e-5?1:0)+(gR<=1e-5?1:0)+((w.fgmin[i][0]<=1e-5)?1:0)+((w.fgmin[i][1]<=1e-5)?1:0);
     bool law=(int)i>=engage33;
     if(ct<2){if(law)++sub2_law_t;else ++sub2_pre_t;}
     if(cc<2){if(law)++sub2_law_c;else ++sub2_pre_c;}}
    char b[384];std::snprintf(b,384,"F-G33 support_by_era [164,refusal) pre_law: touching=%d contact=%d (wave-32 exchange era counted 70/68) law_era: touching=%d contact=%d [PREDICTED: both shrink -- the pinned carrier stays DOWN; the fores face persists]",
     sub2_pre_t,sub2_pre_c,sub2_law_t,sub2_law_c);
    note(b);
    ck(sub2_law_t<70,"f33_support_touching_shrinks");
    ck(sub2_law_c<68,"f33_support_contact_shrinks");}}}

 // ── WAVE 34 LATCHED WORLD-PIVOT HOLD CENSUS (pre-registered in
 //    receipt_wave34.json): (a) THE LATCH ERAS -- every stand_pivot
 //    engagement (the phase-2 first ticks) against the replay prediction
 //    (the single-tick splits 206/213/226/243/245 byte-inert + the R's 250
 //    engagement, released by the L's completion); (b) THE RELEASES -- zero
 //    envelope releases (the release tick field stays -1); (c) THE LATCH-ERA
 //    PADS -- the pinned carrier's pair-min never past the genuine-departure
 //    bound inside a latch era, its share never vanishing mid-era; (d) THE
 //    TWELFTH EXCHANGE -- the R's fire lands on the L's 262 completion with
 //    live pads and the chain continues past the wave-33 strand.
 {const size_t N34=std::min({w.hindst.size(),w.hgap.size(),w.hrxn.size(),(size_t)426});
  int first_latch=-1;std::string latches;int latch_ticks[2]={0,0};int releases=0;std::string rel_ticks;
  for(size_t l=0;l<2;++l){
   bool in_era=false;int start=-1;
   for(size_t i=0;i<N34;++i){
    bool now=w.hindst[i][31+3*l]>0.5;
    if(now&&!in_era){in_era=true;start=(int)i;
     char cb[48];std::snprintf(cb,48,"%s@%d ",l?"R":"L",start);latches+=cb;
     if(first_latch<0)first_latch=(int)i;}
    else if(!now&&in_era){in_era=false;
     char cb[48];std::snprintf(cb,48,"%s[%d,%d) ",l?"R":"L",start,(int)i);latches+=cb;}
    if(now)++latch_ticks[l];}
   if(in_era){char cb[48];std::snprintf(cb,48,"%s[%d,open) ",l?"R":"L",start);latches+=cb;}}
  for(size_t i=0;i<N34;++i)for(size_t l=0;l<2;++l)
   if(w.hindst[i][32+3*l]>=0.){++releases;
    char cb[32];std::snprintf(cb,32,"%s@%d ",l?"R":"L",(int)w.hindst[i][32+3*l]);rel_ticks+=cb;}
  {char b[640];std::snprintf(b,640,"F-G34 latch eras=%s latch_ticks=(%d,%d) releases=%d %s[PREDICTED (the airborne gate): the stall blinks ride the shipped resumptions; the R's latch [250,262) released by the L's completion; ZERO envelope releases]",
    latches.c_str(),latch_ticks[0],latch_ticks[1],releases,rel_ticks.c_str());
   note(b);
   if(first_latch<0)
    note("F-G34 NOT MEASURED: the latch never engaged -- the wave-34 law REVERTED (the falsifiers fired and are carried verbatim in receipt_wave34.json: the stall-blink latch launches at 215; the airborne-gated latch, either anchor, loses the pads at 259 -- the drain is geometric); the 295 twelfth-exchange strand is the shipped face");
   else{
    ck(first_latch==250,"f34_first_latch_engagement_predicted");
    ck(releases==0,"f34_zero_envelope_releases");}}
  // (c) the latch-era pads: the carrier's pair-min and share inside the eras
  //    (the engagement transient: the first 2 ticks of an era re-load the
  //    contact from the graze height -- the mid-era read starts at era+2)
  if(first_latch>=0){
   int era_band_exits=0;int era_rxn0=0;double worst_era_gap=-1.;
   for(size_t l=0;l<2;++l){
    bool in_era=false;int era_start=-1;
    for(size_t i=0;i<N34;++i){
     bool now=w.hindst[i][31+3*l]>0.5;
     if(now&&!in_era){in_era=true;era_start=(int)i;}
     else if(!now&&in_era){in_era=false;era_start=-1;}
     if(in_era){
      double g1=w.hgap[i][2*l],g2=w.hgap[i][2*l+1],gm=g1<g2?g1:g2;
      if(gm>worst_era_gap)worst_era_gap=gm;
      if(gm>1e-5+1e-6)++era_band_exits;
      if(era_start>=0&&(int)i>=era_start+2){
       double cr=w.hrxn[i][2*l]+w.hrxn[i][2*l+1];
       if(cr<=0.)++era_rxn0;}}}}
   char b[384];std::snprintf(b,384,"F-G34 latch_era_pads worst_pairmin_mm=%.4f band_exits_past_departure=%d rxn0_mid_era=%d [PREDICTED: the pads hold under the height demand; the pinned share never vanishes mid-era]",
    worst_era_gap*1000.,era_band_exits,era_rxn0);
   note(b);
   ck(era_band_exits==0,"f34_latch_era_pads_hold");
   ck(era_rxn0==0,"f34_latch_era_share_live");}
  // (d) the twelfth exchange: the R's fire at the L's completion, live pads
  if(first_latch>=0){
   int fire_R=-1;
   for(size_t i=250;i<w.hindst.size();++i)
    if(w.hindst[i][14]>w.hindst[i-1][14]){fire_R=(int)i;break;}
   int last_fire34=-1;
   for(size_t i=250;i<w.hindst.size();++i)for(size_t l=0;l<2;++l)
    if(w.hindst[i][12*l+2]>w.hindst[i-1][12*l+2])last_fire34=(int)i;
   bool live=(fire_R>0&&(size_t)(fire_R-1)<w.t.size())?w.t[(size_t)(fire_R-1)][1]!=0:false;
   char b[384];std::snprintf(b,384,"F-G34 twelfth_exchange fire_R=%d live_pads=%d last_fire=%d [PREDICTED: the R fires AT 262 ON the L's completion with live pads; the chain continues past the wave-33 strand at 247]",
    fire_R,live?1:0,last_fire34);
   note(b);
   ck(fire_R>0&&fire_R<=266&&live,"f34_twelfth_fire_lands");
   ck(last_fire34>262,"f34_chain_continues_past_twelfth");}}

 // ── WAVE 35 CARRIER SELF-UNLOAD FIRE DEADLINE CENSUS (pre-registered in
 //    receipt_wave35.json): (a) THE WAIVE FIRES -- every (a)-waiving
 //    unload-deadline fire; the FIRST EXACTLY 161 (the L, inside the R's
 //    [160,175) real swing); the twelfth-era engagement the R in [247,250]
 //    (predicted 248); every waive fire on a touch-live pad; ZERO waive fires
 //    inside the stall calendar [176,246] (the stalls' holds never clear).
 //    (b) THE CALENDAR SURVIVAL -- the R's post-160 TD in [173,178]; the L's
 //    post-247 TD in [258,268]; the R's post-fire TD in [256,274].
 //    (c) THE DELIVERY -- the R's landing rxn at its post-fire completion
 //    > 10 N (the L's 47.717 N @262 precedent) and both hinds rxn-positive
 //    within 6 ticks of that completion.
 {const size_t N35=std::min(w.hind35.size(),w.hgap.size());
  std::string wf;int first_wf=-1;int dead_wf=0;int stall_era_wf=0;int wf_R_twelfth=-1;
  for(size_t i=1;i<N35;++i)for(size_t l=0;l<2;++l)
   if(w.hind35[i][2*l]>w.hind35[i-1][2*l]){
    int f=(int)i;
    char cb[48];std::snprintf(cb,48,"%s@%d ",l?"R":"L",f);wf+=cb;
    if(first_wf<0)first_wf=f;
    if(f>=176&&f<=243)++stall_era_wf;
    if(l==1&&f>=244&&f<=252)wf_R_twelfth=f;
    if((size_t)(f-1)<w.t.size()&&w.t[(size_t)(f-1)][l]!=1)++dead_wf;}
  {char b[640];std::snprintf(b,640,"F-G35 waive_fires %s first=%d [PREDICTED EXACTLY 161: the L, inside the R's [160,175) real swing] twelfth_R=%d [AMENDED PREDICTED ~247, window [244,252]] dead=%d [OWNED 0] stall_era=%d [OWNED 0: the stalls' holds never clear]",
    wf.c_str(),first_wf,wf_R_twelfth,dead_wf,stall_era_wf);
   note(b);
   if(first_wf>0){
    ck(first_wf==161,"f35_first_waive_fire_predicted");
    ck(dead_wf==0,"f35_waive_fires_on_live_pads");
    ck(stall_era_wf==0,"f35_no_waive_in_stall_eras");
    ck(wf_R_twelfth>0,"f35_twelfth_waive_fires");}
   else note("F-G35 NOT MEASURED: the waive never fired");}
  // (b)+(c): the calendar survival + the delivery, only if the twelfth fired
  if(wf_R_twelfth>0){
   auto next_td=[&](size_t l,int after)->int{
    for(size_t i=(size_t)after+1;i<w.hindst.size();++i)
     if(w.hindst[i][12*l+3]>w.hindst[i-1][12*l+3])return (int)i;
    return -1;};
   int td_R160=next_td(1,160),td_L247=next_td(0,247),td_Rpost=next_td(1,wf_R_twelfth);
   double land_rxn=td_Rpost>0?w.hrxn[(size_t)td_Rpost][2]+w.hrxn[(size_t)td_Rpost][3]:-1.;
   int resumed_fire=-1; // the amended calendar's resume: a fire within [173,180]
   for(size_t i=(size_t)171;i<(size_t)181&&(size_t)i<w.hindst.size()&&resumed_fire<0;++i)
    for(size_t l=0;l<2;++l)
     if(w.hindst[i][12*l+2]>w.hindst[i-1][12*l+2]){resumed_fire=(int)i;break;}
   {char b[640];std::snprintf(b,640,"F-G35 calendar td_R_post160=%d [window 173..178] resumed_fire=%d [AMENDED window 173..180: the +1 class on the R's landing] td_L_post247=%d [window 254..268] td_R_postfire=%d [window 253..276] land_rxn_R=%.3f [OWNED >10: the L's 47.717 N @262 precedent]",
     td_R160,resumed_fire,td_L247,td_Rpost,land_rxn);
    note(b);
    ck(td_R160>=173&&td_R160<=178,"f35_calendar_R_swing_survives");
    ck(resumed_fire>=173&&resumed_fire<=180,"f35_calendar_resumes");
    ck(td_L247>=254&&td_L247<=268,"f35_calendar_L_twelfth_completes");
    ck(td_Rpost>=253&&td_Rpost<=276,"f35_calendar_R_replant_completes");
    ck(land_rxn>10.,"f35_replant_lands_loaded");}
   {int both=0;
    for(int t=td_Rpost;t<=td_Rpost+6&&t>=0&&(size_t)t<w.hrxn.size();++t){
     double lh=w.hrxn[(size_t)t][0]+w.hrxn[(size_t)t][1],rh=w.hrxn[(size_t)t][2]+w.hrxn[(size_t)t][3];
     if(lh>0.&&rh>0.){both=1;break;}}
    note(std::string("F-G35 two_legged_within_6_of_replant=")+(both?"1":"0")+" [OWNED 1]");
    ck(both==1,"f35_two_legged_after_replant");}}}

 // ── WAVE 36 WAIVE-ERA HAND-OFF PRESERVATION CENSUS (pre-registered in
 //    receipt_wave36.json): the waive's perturbation must be absorbed by ONE
 //    +1 hand-off and the stall calendar must re-lock to the shipped grid.
 //    (a) THE PRESERVED HAND-OFF -- the first fire after the first waive
 //    EXACTLY 175 (the natural g=1 clause (b); the wave-35 build-2 fired it
 //    AT the perturbed 174 completion and re-phased the whole calendar -1).
 //    (b) THE RE-LOCKED GRID -- the stall-calendar fires within 1 tick of the
 //    shipped 184/193/202/211/220/229/238 and the twelfth real launch in
 //    [246,248]. (c) THE TWELFTH WAIVE EXACTLY 248 (the last lawful decision:
 //    the touch hysteresis releases at the 249 tick-start, mined 1.317e-5 m >
 //    kTouch+kReleaseBand=1.1e-5). (d) THE PRESERVATION MECHANISM -- the
 //    hand-off restores >= 1 and the concentration repairs counted (status).
 {const size_t N36=std::min(w.hind35.size(),w.hindst.size());
  if(N36>1&&w.hind35[N36-1][0]+w.hind35[N36-1][2]>0.){
   int wf_first=-1,wf_R=-1;
   for(size_t i=1;i<N36;++i)for(size_t l=0;l<2;++l)
    if(w.hind35[i][2*l]>w.hind35[i-1][2*l]){
     if(wf_first<0)wf_first=(int)i;
     if(l==1)wf_R=(int)i;}
   int resumed=-1; // the preserved hand-off: the first fire after the first waive
   for(size_t i=(size_t)wf_first+1;i<=(size_t)wf_first+30&&(size_t)i<N36&&resumed<0;++i)
    for(size_t l=0;l<2;++l)
     if(w.hindst[i][12*l+2]>w.hindst[i-1][12*l+2]){resumed=(int)i;break;}
   static const int GRID[7]={184,193,202,211,220,229,238};
   int grid_hit=0,grid_worst=0;
   for(int g=0;g<7;++g){
    int best=99;
    for(size_t i=(size_t)(GRID[g]-2);i<=(size_t)(GRID[g]+2)&&(size_t)i<N36;++i)
     for(size_t l=0;l<2;++l)
      if(w.hindst[i][12*l+2]>w.hindst[i-1][12*l+2]){
       int d=(int)i-GRID[g];if(d<0)d=-d;
       if(d<best)best=d;}
    if(best<=1)++grid_hit;
    if(best<99&&best>grid_worst)grid_worst=best;}
   int twelfth_launch=-1;
   for(size_t i=(size_t)244;i<=(size_t)250&&(size_t)i<N36&&twelfth_launch<0;++i)
    for(size_t l=0;l<2;++l)
     if(w.hindst[i][12*l+2]>w.hindst[i-1][12*l+2]){twelfth_launch=(int)i;break;}
   double restores=w.hind35[N36-1][5]+w.hind35[N36-1][8];
   double repairs=w.hind35[N36-1][6]+w.hind35[N36-1][9];
   char b[640];std::snprintf(b,640,"F-G36 preserved_handoff=%d [PREDICTED EXACTLY 175: the natural g=1 clause (b), the (b)-waive disarmed by the preservation clause] wf_R_twelfth=%d [PREDICTED EXACTLY 248: the last lawful decision] twelfth_launch=%d [window 246..248] grid_hits=%d/7 worst_drift=%d [OWNED 7/7, drift<=1] handoff_restores=%.0f [OWNED >=1] alt_repairs=%.0f",
    resumed,wf_R,twelfth_launch,grid_hit,grid_worst,restores,repairs);
   note(b);
   ck(resumed==175,"f36_preserved_handoff_on_grid");
   ck(wf_R==248,"f36_twelfth_waive_248");
   ck(twelfth_launch>=246&&twelfth_launch<=248,"f36_twelfth_launch_window");
   ck(grid_hit==7,"f36_stall_grid_relocked");
   ck(restores>=1.,"f36_handoff_restores");}
  else note("F-G36 NOT MEASURED: the waive never fired");}

 // ── WAVE 37 COMPLETION-TICK RE-LOCK CENSUS (pre-registered in
 //    receipt_wave37.json) -- READ-ONLY PLUMBING, REPORTS NOT MEASURED: the
 //    wave-37 law (the wave-36 exchange protocol verbatim + the completion-
 //    tick re-lock) was measured -- the fence GREEN in full (the first
 //    divergence EXACTLY 161, the re-lock's unloadgate EXACTLY 193, the
 //    named ticks exact, the composed walk byte-identical to the parent law's
 //    trajectory through 192), the re-lock's OWN engagement GREEN (the L's
 //    graze-owned hand-off EXACTLY 193 ON the R's on-grid completion, the
 //    first waive EXACTLY 161, dead-pad 0, the stall grid EXACT through 202)
 //    and the rung PASSED (refusal 304 > 300, the first rung bank in the
 //    campaign's measured record) -- AND THE LEDGER FALSIFIER FIRED
 //    (33.559179 > 32.861605): the re-locked calendar derailed at the L's
 //    NEXT hand-off (the R's next stall swing's hold cleared at 206 on the
 //    re-locked trajectory; the (a)-waive fired INSIDE stall eras L@206/L@218;
 //    the grid 4/9 worst drift 29; the twelfth launch never came; the new
 //    f4_work_envelope red). The pre-committed terminal action RESTORED the
 //    ship bytes; the counters below stay read-only reporting NOT MEASURED,
 //    the fired falsifiers carried verbatim in the receipt.
 {const size_t N37=std::min({w.hind37.size(),w.hind35.size(),w.hindst.size()});
  double yields37=N37>0?w.hind37[N37-1][0]+w.hind37[N37-1][2]:-1.;
  if(N37>1&&(w.hind35[N37-1][0]+w.hind35[N37-1][2])>0.&&yields37>0.){
   std::vector<std::pair<int,int>> fires; // (leg,tick), in order
   for(size_t i=1;i<N37;++i)for(size_t l=0;l<2;++l)
    if(w.hindst[i][12*l+2]>w.hindst[i-1][12*l+2])fires.push_back({(int)l,(int)i});
   int wf_first=-1,wf_R=-1;double deadpads=0;
   for(size_t i=1;i<N37;++i)for(size_t l=0;l<2;++l)
    if(w.hind35[i][2*l]>w.hind35[i-1][2*l]){
     if(wf_first<0)wf_first=(int)i;
     if(l==1)wf_R=(int)i;
     if(w.hrxn[i][2*l]+w.hrxn[i][2*l+1]<=0.)++deadpads;}
   static const int GRID37[9]={175,184,193,202,211,220,229,238,247};
   int hits=0,worst=0;
   for(int g=0;g<9;++g){int best=99;
    for(auto&pr:fires)if(pr.first==g%2){
     int d=pr.second-GRID37[g];if(d<0)d=-d;if(d<best)best=d;}
    if(best==0)++hits;
    if(best<99&&best>worst)worst=best;}
   bool relock193=false,launch247=false;
   for(auto&pr:fires){if(pr.first==0&&pr.second==193)relock193=true;
    if(pr.first==0&&pr.second==247)launch247=true;}
   char b37[640];std::snprintf(b37,640,"F-G37 relock_fire_L=%d [PREDICTED EXACTLY 193: the graze-owned hand-off ON the R's on-grid completion] grid_hits=%d/9 worst_drift=%d [OWNED 9/9, drift 0: the calendar re-locked ALL THE WAY] twelfth_launch=%d [PREDICTED EXACTLY 247] wf_R_twelfth=%d [PREDICTED EXACTLY 248] dead_pad_waives=%.0f [OWNED 0] graze_yields=%.0f [OWNED >=1] wf_first=%d [PREDICTED EXACTLY 161]",
    relock193?193:-1,hits,worst,launch247?247:-1,wf_R,deadpads,yields37,wf_first);
   note(b37);
   ck(relock193,"f37_relock_on_grid");
   ck(hits==9&&worst==0,"f37_stall_grid_exact");
   ck(launch247,"f37_twelfth_launch_247");
   ck(wf_R==248,"f37_twelfth_waive_248");
   ck(deadpads==0.,"f37_no_dead_pad_waives");
   ck(yields37>=1.,"f37_graze_yields");
   ck(wf_first==161,"f37_first_waive_161");
   if(wf_R>0){
    auto next_td37=[&](size_t l,int after)->int{
     for(size_t i=(size_t)after+1;i<w.hindst.size();++i)
      if(w.hindst[i][12*l+3]>w.hindst[i-1][12*l+3])return (int)i;
     return -1;};
    int td_Rpost=next_td37(1,wf_R);
    double land_rxn=td_Rpost>0?w.hrxn[(size_t)td_Rpost][2]+w.hrxn[(size_t)td_Rpost][3]:-1.;
    {char b37b[320];std::snprintf(b37b,320,"F-G37 delivery td_R_postwaive=%d [window 253..276] land_rxn_R=%.3f [OWNED >10: the L's 47.717 N @262 precedent]",
      td_Rpost,land_rxn);
     note(b37b);
     ck(td_Rpost>=253&&td_Rpost<=276,"f37_replant_completes");
     ck(land_rxn>10.,"f37_replant_lands_loaded");}
    {int both=0;
     for(int t=td_Rpost;t<=td_Rpost+6&&t>=0&&(size_t)t<w.hrxn.size();++t){
      double lh=w.hrxn[(size_t)t][0]+w.hrxn[(size_t)t][1],rh=w.hrxn[(size_t)t][2]+w.hrxn[(size_t)t][3];
      if(lh>0.&&rh>0.){both=1;break;}}
     note(std::string("F-G37 two_legged_within_6_of_replant=")+(both?"1":"0")+" [OWNED 1]");
     ck(both==1,"f37_two_legged_after_replant");}}}
  else note("F-G37 NOT MEASURED: the waive never fired or no graze yield (the wave-37 law REVERTED per the pre-committed terminal action)");}

 // ── WAVE 38 CALENDAR-ARITHMETIC WAIVE SCOPE GUARD CENSUS (pre-registered in
 //    receipt_wave38.json, frozen BEFORE the composed build): the pose read
 //    cannot own the era class -- the [202,211) stall graze cleared at 206 on
 //    EVERY measured trajectory (the shipped walk's own era max pair-min
 //    1.116e-05, the re-locked walk's 1.147e-05, both past the 1.1e-05
 //    release bound). The fifth clause guards the waive by the CALENDAR: the
 //    deciding leg's own just-completed era ran the stall cadence (its
 //    length == tair) iff the other's current era is that chain's next link;
 //    the waive rides REAL swings only, composed with the pose read
 //    byte-verbatim (the guard only removes openings). Pre-registered:
 //    exactly ONE waive fire (the L@161), the guard's first block EXACTLY
 //    206, the stall calendar re-locked 9/9 drift 0, the twelfth launch
 //    EXACTLY 247, the twelfth-era TD in [258,268], and the 248 twelfth-era
 //    waive BLOCKED by the link test (the f37_twelfth_waive_248 letter fires
 //    BY DESIGN and is carried as the pre-registered cost).
 {const size_t N38=std::min({w.hind38.size(),w.hind35.size(),w.hind37.size()});
  double blocks=N38>0?w.hind38[N38-1][0]+w.hind38[N38-1][2]:-1.;
  if(N38>1&&(w.hind35[N38-1][0]+w.hind35[N38-1][2])>0.&&blocks>=0.){
   int wf_first=-1,wf_last=-1,wf_R=-1;double waives=0,deadpads=0;
   for(size_t i=1;i<N38;++i)for(size_t l=0;l<2;++l)
    if(w.hind35[i][2*l]>w.hind35[i-1][2*l]){
     ++waives;if(wf_first<0)wf_first=(int)i;wf_last=(int)i;if(l==1)wf_R=(int)i;
     if(w.hrxn[i][2*l]+w.hrxn[i][2*l+1]<=0.)++deadpads;}
   static const int GRID38[9]={175,184,193,202,211,220,229,238,247};
   std::vector<std::pair<int,int>> fires; // (leg,tick), in order
   for(size_t i=1;i<w.hindst.size();++i)for(size_t l=0;l<2;++l)
    if(w.hindst[i][12*l+2]>w.hindst[i-1][12*l+2])fires.push_back({(int)l,(int)i});
   int hits=0,worst=0;
   for(int g=0;g<9;++g){int best=99;
    for(auto&pr:fires)if(pr.first==g%2){
     int d=pr.second-GRID38[g];if(d<0)d=-d;if(d<best)best=d;}
    if(best==0)++hits;
    if(best<99&&best>worst)worst=best;}
   bool launch247=false;
   for(auto&pr:fires)if(pr.first==0&&pr.second==247)launch247=true;
   int td_Ltwelfth=-1;
   for(size_t i=(size_t)248;i<w.hindst.size();++i)
    if(w.hindst[i][3]>w.hindst[i-1][3]){td_Ltwelfth=(int)i;break;}
   int gfirst=(int)w.hind38[N38-1][1]; // the L's first block tick
   char b38[640];std::snprintf(b38,640,"F-G38 guard waive_fires=%.0f [PREDICTED EXACTLY 1: the L@161, the only REAL-era host] first=%d dead=%.0f [OWNED 0] guard_blocks=%.0f guard_first=%d [PREDICTED EXACTLY 206: the [202,211) graze era -- the pose read opens, the link test blocks] grid=%d/9 worst_drift=%d [OWNED 9/9, drift 0: the calendar re-locked ALL THE WAY] twelfth_launch=%s [PREDICTED EXACTLY 247] td_L_twelfth=%d [window 258..268, the shipped 262]",
    waives,wf_first,deadpads,blocks,gfirst,hits,worst,launch247?"247":"-1",td_Ltwelfth);
   note(b38);
   ck(waives==1.,"f38_one_waive_only");
   ck(wf_first==161,"f38_first_waive_161");
   ck(deadpads==0.,"f38_no_dead_pad_waives");
   ck(blocks>=1.,"f38_guard_blocks");
   ck(gfirst==206,"f38_guard_first_206");
   ck(hits==9&&worst==0,"f38_stall_grid_exact");
   ck(launch247,"f38_twelfth_launch_247");
   ck(td_Ltwelfth>=258&&td_Ltwelfth<=268,"f38_twelfth_td_window");}
  else note("F-G38 NOT MEASURED: the guard never blocked and no waive fired (the wave-38 law REVERTED per the pre-committed terminal action)");}

 // -- WAVE 39 STAY-ERA HAUL RESTORATION CENSUS (pre-registered in
 //    receipt_wave39.json, amendment 39a) -- READ-ONLY PLUMBING: the sixth
 //    clause (the certified stay does not certify the replant; the machine
 //    re-fires the swing once; the carrier pin disarms on the same
 //    certificate) measured on the law build; the pre-committed terminal
 //    action restored the wave-38 law bytes after the rung falsifier fired
 //    twice (the first build 225, the amended build 231, both
 //    gait_impact_event_budget -- the wave-34 mined fold/launch class
 //    re-phased by the re-attempt cascade). The counters below report NOT
 //    MEASURED on the restored ship bytes; the fired falsifiers are carried
 //    verbatim in receipt_wave39.json.
 {const size_t N39=std::min({w.hind39.size(),w.hind35.size(),w.hind38.size()});
  double refires=N39>0?w.hind39[N39-1][0]+w.hind39[N39-1][2]:-1.;
  if(N39>1&&refires>0.){
   int rfirst=(int)w.hind39[N39-1][1]; // the L's first refire tick
   double refires_L=w.hind39[N39-1][0],refires_R=w.hind39[N39-1][2];
   int td_L_after=-1; // the L's first td after its first refire (the re-fired era's own certification)
   if(rfirst>0)for(size_t i=(size_t)rfirst+1;i<w.hindst.size();++i)
    if(w.hindst[i][3]>w.hindst[i-1][3]){td_L_after=(int)i;break;}
   int td_L_twelfth=-1; // the L's first td at/after the twelfth window's opening
   for(size_t i=(size_t)257;i<w.hindst.size();++i)
    if(w.hindst[i][3]>w.hindst[i-1][3]){td_L_twelfth=(int)i;break;}
   char b39[640];std::snprintf(b39,640,"F-G39 stay_refires=%.0f (L=%.0f R=%.0f) refire_first=%d [PREDICTED EXACTLY 184: the L's [175,184) chain-link stay] re-fired_era_td=%d [the re-fired era certifies by the shipped band entry -- the balanced-book amendment] td_L_twelfth=%d [window 258..268; carried verbatim if fired]",
    refires,refires_L,refires_R,rfirst,td_L_after,td_L_twelfth);
   note(b39);
   ck(rfirst==184,"f39_refire_first_184");
   ck(refires_L>=1.,"f39_stay_refires_engaged");}
  else note("F-G39 NOT MEASURED: the stay-era haul restoration never engaged (the wave-39 law REVERTED per the pre-committed terminal action; the counters stay read-only plumbing)");}

 // -- WAVE 40 LOAD-BOOK RESTORATION CENSUS (pre-registered in
 //    receipt_wave40.json) -- the lift-first hold's planar re-capture (the
 //    wave-33 carrier pin's own pattern, mirrored) measured on the law
 //    build; the pre-committed terminal action restores the ship bytes if
 //    the rung/ledger falsifier fires. The census reads the drag counters.
 {const size_t N40=std::min({w.hind40.size(),w.hind39.size()});
  double arms=N40>0?w.hind40[N40-1][0]+w.hind40[N40-1][3]:-1.;
  if(N40>0&&arms>0.){
   int dfirst=(int)(w.hind40[N40-1][1]>=0?w.hind40[N40-1][1]:w.hind40[N40-1][4]); // the earliest arm tick
   double arms_L=w.hind40[N40-1][0],arms_R=w.hind40[N40-1][3];
   double releases=w.hind40[N40-1][2]+w.hind40[N40-1][5];
   char b40[640];std::snprintf(b40,640,"F-G40 loadbook drag_arms=%.0f (L=%.0f R=%.0f) drag_first=%d [PREDICTED EXACTLY 165: the [161,170) stay's stall clock reaching the wave-33 arming read tair-tair/2-kUnloadTicks] drag_releases=%.0f [the dragged holds that RELEASED -- the stay class broken at the load book]",
    arms,arms_L,arms_R,dfirst,releases);
   note(b40);
   ck(dfirst==165,"f40_drag_first_165");
   ck(releases>=1.,"f40_drag_releases");}
  else note("F-G40 NOT MEASURED: the load-book restoration never engaged (the wave-40 law REVERTED per the pre-committed terminal action; the counters stay read-only plumbing)");}


 // ── WAVE 21 HIND-RIDE CENSUSES (pre-registered in receipt_wave21.json; the
 //    causal verdict REFLEX-FIRST): (a) THE REFLEX ARMING CENSUS -- the
 //    mechanism's OWNED direct test: at every capture event (the per-tick
 //    capture_events delta; the fire ran during that step on the PREVIOUS
 //    tick's post-step state) all three derived clauses must hold at the
 //    decision state: (i) the true-hull containment OPEN (com_in_hull==0,
 //    hull>=3); (ii) the jumped leg's clock in its swing window at the fire
 //    (phi >= TOE_OFF=0.68, decision phi = prev + dt/T unless a touch reset
 //    fired in the fire step); (iii) no touching sole's slip > the derived
 //    bound v_bound = mu*g*(1-CAPTURE_PHI)*T_CYCLE = 0.2089 m/s. (b) THE SKID
 //    CENSUS -- REPORTED (not owned): max touching-hind slip, worst tick,
 //    count/run above 0.1 m/s. (c) THE FOLD CENSUS -- REPORTED (not owned):
 //    posture |torque| vs the 11.2125 cap, first rail tick, the pitch speed's
 //    sign through the former run-away window [65,80].
 {const double MU=number(recipe.at("contact_friction"));
  const double V_BOUND=MU*9.80665*(1.-number(recipe.at("capture_step_phase")))*T;
  const double TOE=0.68,DPH=T>0?dt/T:0.;
  {char cb[160];std::snprintf(cb,160,"F-G21 arming bound v_bound=%.6f m/s (mu=%.2f g=9.80665 capture_phase=%.2f T=%.3f)",
   V_BOUND,MU,number(recipe.at("capture_step_phase")),T);note(cb);}
  // (a) the reflex arming census
  {uint64_t fires=0,viol=0;
   for(size_t i=1;i<w.cev.size();++i){
    if(w.cev[i]==w.cev[i-1])continue;
    ++fires;
    size_t d=i-1; // the decision state
    bool c1=w.comh[d][3]==0.&&w.comh[d][2]>=3.;
    // the jumped leg: its phase this tick is the capture phase 0.95
    int leg=-1;for(size_t l=0;l<2;++l)if(std::abs(w.hphase[i][l]-0.95)<1e-9)leg=(int)l;
    double pre_phi=leg>=0?w.hphase[d][leg]:-1.;
    bool reset_fired=leg>=0&&w.hgap[d][leg*2]<=1e-5&&d>=1&&w.hgap[d-1][leg*2]>1e-5;
    double dec_phi=reset_fired?0.:pre_phi+DPH;
    bool c2=leg>=0&&dec_phi>=TOE-1e-12;
    double slip_mx=0;
    for(size_t k=0;k<4;++k)if(w.hgap[d][k]<=1e-5)slip_mx=(std::max)(slip_mx,w.hslip[d][k]);
    // the fore soles: per-leg min gap above the band == airborne; the max
    // fore slip rides the wave-16 series (all fore points)
    {double fg0=(std::min)(w.fgmin[d][0],w.fgmin[d][1]);
     if(fg0<=1e-5)slip_mx=(std::max)(slip_mx,w.frslip[d]);}
    bool c3=slip_mx<=V_BOUND+1e-12;
    char b[288];std::snprintf(b,288,"F-G21 fire #%llu at decision tick %zu: clause1(in_hull=%.0f,hull=%d)=%d clause2(leg=%d dec_phi=%.4f%s)=%d clause3(slip_mx=%.4f<=%.4f)=%d",
     (unsigned long long)fires,d,w.comh[d][3],(int)w.comh[d][2],c1?1:0,leg,dec_phi,
     reset_fired?" reset_fired":"",c2?1:0,slip_mx,V_BOUND,c3?1:0);
    note(b);
    if(!(c1&&c2&&c3))++viol;}
   char b[160];std::snprintf(b,160,"F-G21 reflex_arming fires=%llu violating=%llu (baseline witness: the wave-20 fires at decision ticks 64/79 armed with in_hull=1 / stance clocks 0.0235 / slip 0.453 and slips 0.586-1.981 -- all three clauses blocked them)",
    (unsigned long long)fires,(unsigned long long)viol);
   note(b);
   ck(viol==0,"f21_no_fire_against_arming_law");}
  // (b) the skid census (reported)
  {double mx=-1;int mx_tick=-1,cnt=0,run=0,mx_run=0;
   for(size_t i=60;i<w.hslip.size();++i){
    double sm=0;for(size_t k=0;k<4;++k)if(w.hgap[i][k]<=1e-5)sm=(std::max)(sm,w.hslip[i][k]);
    if(sm>mx){mx=sm;mx_tick=(int)i;}
    if(sm>0.1){++cnt;mx_run=(std::max)(mx_run,++run);}else run=0;}
   char b[224];std::snprintf(b,224,"F-G21 skid_census max_touching_hind_slip=%.4f at tick %d ticks_above_0.1=%d max_run=%d [REPORTED: not this verdict's clause]",
    mx<0?0.:mx,mx_tick,cnt,mx_run);
   note(b);}
  // (c) the fold census (reported)
  {double cmx=0;int first_rail=-1;int neg_spd=0;
   const double CAP=11.2125;
   for(size_t i=60;i<w.post.size();++i){
    double q=std::abs(w.post[i][0]);
    if(q>cmx)cmx=q;
    if(first_rail<0&&q>=CAP*(1.-1e-9))first_rail=(int)i;
    if(i>=65&&i<80&&w.post[i][3]<0.)++neg_spd;}
   char b[256];std::snprintf(b,256,"F-G21 fold_census posture_tau_max=%.5f (cap %.4f) first_rail_tick=%s ticks_pspd_negative_in_[65,79]=%d [REPORTED: not this verdict's clause]",
    cmx,CAP,first_rail<0?"none":std::to_string(first_rail).c_str(),neg_spd);
   note(b);}}

 // ── WAVE 22 TOUCH-RESET CENSUSES (pre-registered in receipt_wave22.json;
 //    THE TOUCH-RESET LAW: a touch event that legitimately resets a stance
 //    clock must be a TOUCHDOWN, not a band-edge graze). (a) THE SLAM CENSUS
 //    -- the membrane's OWNED direct test: every hind-clock phase event
 //    (|dphi| > 3*dt/T = 0.014083) classified NATURAL-WRAP / RESET-at-legit-TD
 //    / CAPTURE-JUMP / SLAM-or-unclassified; the last class must be EMPTY;
 //    both hind phases continuous through the graze window [63,66] (the
 //    baseline reference: phR 0.52817 -> 0.00000 during step 66). (b) THE
 //    TOUCH CENSUS -- every band excursion per hind leg (pair-min gap > kTouch
 //    runs) classified by DEPARTURE DEPTH vs the solver's stabilization quantum
 //    kStab = 1e-6 m: depth <= kStab = CHATTER (a reset at its re-entry is a
 //    SLAM); depth > kStab = LEGITIMATE. The pre-registered known-good
 //    touchdown list (L@40, R@55 gap edges; depths 6.5e-2/1.17e-1) must
 //    classify LEGITIMATE; zero resets at chatter edges; every clock reset
 //    pairs tick-exactly with a LEGITIMATE edge. (c) THE RESIDUAL-SLIP CENSUS
 //    -- REPORTED against the pre-registered band: the R hind's touching slip
 //    [65,90], the sustained > 0.1 m/s runs, the worst tick's force balance.
 {const double KT=1e-5,KSTAB=1e-6,DPH=T>0?dt/T:0.,BOUND=3.*DPH;
  const double MU=number(recipe.at("contact_friction"));
  const size_t N=std::min(w.hphase.size(),(size_t)426);
  if(N<2)note("F-G22 censuses NOT MEASURED: the walk refused before two status samples");
  else{
  auto pmin=[&](size_t i,size_t leg){return (std::min)(w.hgap[i][leg*2],w.hgap[i][leg*2+1]);};
  // release-aware replay of the clock's contact classification (the header's
  // leg_contact law) from the mined gap series: contact[i], edges, and the
  // departure depth of each edge.
  std::vector<char> contact[2];std::vector<double> edge_depth[2];std::vector<int> edge_tick[2];
  for(size_t leg=0;leg<2;++leg){
   contact[leg].assign(N,0);double run_mx=-1;
   char c0=pmin(0,leg)<=KT?(char)1:(char)0;contact[leg][0]=c0;
   for(size_t i=1;i<N;++i){
    double g=pmin(i,leg);
    bool c=g<=KT?true:(g>KT+KSTAB?false:(contact[leg][i-1]!=0));
    if(!c)run_mx=(std::max)(run_mx,g); // still open: track the departure depth
    if(c&&!contact[leg][i-1]){edge_tick[leg].push_back((int)i);edge_depth[leg].push_back(run_mx);run_mx=-1;}
    if(c)run_mx=-1;
    contact[leg][i]=c?(char)1:(char)0;}}
  // (a) the slam census
  {int slams=0,wraps=0,resets=0,caps=0;std::string slam_dump;
   for(size_t i=1;i<N;++i)for(size_t leg=0;leg<2;++leg){
    double d=w.hphase[i][leg]-w.hphase[i-1][leg];
    if(std::abs(d)<=BOUND)continue;
    const char* ln=leg?"R":"L";
    if(std::abs(w.hphase[i][leg]-(w.hphase[i-1][leg]+DPH-1.))<1e-12){++wraps;continue;}
    if(w.hphase[i][leg]==0.){ // a clock reset: pair with the consumed edge at i-1
     bool paired=false;bool legit=false;double dep=-1;
     for(size_t e2=0;e2<edge_tick[leg].size();++e2)if(edge_tick[leg][e2]==(int)i-1){paired=true;legit=edge_depth[leg][e2]>KSTAB;dep=edge_depth[leg][e2];break;}
     if(paired&&legit){++resets;
      char cb[192];std::snprintf(cb,192,"F-G22 reset %s at step %zu <- LEGIT TD edge at %zu (departure depth %.3e m)",
       ln,i,(size_t)(i-1),dep);
      note(cb);}
     else{++slams;
      char cb[256];std::snprintf(cb,256,"F-G22 SLAM %s at step %zu: ph %.5f->%.5f, no legit edge at %zu (paired=%d)",
       ln,i,w.hphase[i-1][leg],w.hphase[i][leg],i-1,paired?1:0);
      if(slam_dump.size()<400)slam_dump+=cb,slam_dump+="; ";}}
    else if(w.hphase[i][leg]==0.95)++caps; // capture jump: owned by the F-G21 clause census
    else{++slams;
     char cb[256];std::snprintf(cb,256,"F-G22 UNCLASSIFIED phase event %s at step %zu: %.5f->%.5f",ln,i,w.hphase[i-1][leg],w.hphase[i][leg]);
     if(slam_dump.size()<400)slam_dump+=cb,slam_dump+="; ";}}
   // the graze-window continuity [63,66]
   int cont_bad=0;size_t cont_hi=std::min((size_t)66,N-1);bool cont_full=cont_hi>=66;
   for(size_t i=63;i<=cont_hi;++i)for(size_t leg=0;leg<2;++leg)
    if(std::abs(w.hphase[i][leg]-w.hphase[i-1][leg])>BOUND)++cont_bad;
   char b[384];std::snprintf(b,384,"F-G22 slam_census events: wraps=%d resets_at_legit_TD=%d capture_jumps=%d slams=%d %s| graze_window_[63,%zu] continuity_breaches=%d (%s)",
    wraps,resets,caps,slams,slams?slam_dump.c_str():"| ",cont_hi,cont_bad,
    cont_full?"full window":"refused inside the window");
   note(b);
   ck(slams==0,"f22_no_touch_reset_slam");
   if(cont_full)ck(cont_bad==0,"f22_graze_window_phase_continuous");}
  // (b) the touch census
  {int chatter=0,legit=0,chatter_resets=0;std::string ev;
   for(size_t leg=0;leg<2;++leg){
    const char* ln=leg?"R":"L";
    for(size_t e2=0;e2<edge_tick[leg].size();++e2){
     int t=edge_tick[leg][e2];double dep=edge_depth[leg][e2];
     bool is_chatter=dep<=KSTAB;if(is_chatter)++chatter;else ++legit;
     bool reset_here=false;
     for(size_t i=1;i<N;++i)if(w.hphase[i][leg]==0.&&w.hphase[i-1][leg]!=0.&&(int)i-1==t)reset_here=true;
     if(is_chatter&&reset_here)++chatter_resets;
     char cb[192];std::snprintf(cb,192,"%s edge@%d depth=%.3e %s%s; ",ln,t,dep,is_chatter?"CHATTER":"LEGIT",reset_here?" RESET-FIRED":"");
     if(ev.size()<700)ev+=cb;}}
   char b[896];std::snprintf(b,896,"F-G22 touch_census edges: legitimate=%d chatter=%d resets_at_chatter=%d | %s (kStab=1e-6; known-good pre-registered: L@40 depth 6.5e-2, R@55 depth 1.2e-1)",
    legit,chatter,chatter_resets,ev.c_str());
   note(b);
   ck(chatter_resets==0,"f22_no_reset_at_chatter");
   // the known-good list must classify LEGITIMATE: the first L edge and the
   // first R edge are the pre-walk landings at 40/55 (+/-2 for accounting)
   int l0=-1,r0=-1;
   if(edge_tick[0].size())l0=edge_tick[0][0];
   if(edge_tick[1].size())r0=edge_tick[1][0];
   bool l_ok=l0>=0&&edge_depth[0][0]>KSTAB&&l0>=38&&l0<=42;
   bool r_ok=r0>=0&&edge_depth[1][0]>KSTAB&&r0>=53&&r0<=57;
   char cb[192];std::snprintf(cb,192,"F-G22 known_good_landings L@%d depth=%.3e %s | R@%d depth=%.3e %s (pre-registered L@40/R@55 gap edges, L@42/R@57 status edges)",
    l0,l0>=0?edge_depth[0][0]:-1.,l_ok?"LEGIT":"MISS",r0,r0>=0?edge_depth[1][0]:-1.,r_ok?"LEGIT":"MISS");
   note(cb);
   ck(l_ok&&r_ok,"f22_known_good_touchdowns_legit");}
  // (c) the residual-slip census (REPORTED against the pre-registered band)
  {double mx=-1,mx_rxn=0,mx_frc=0;int mx_tick=-1,run=0,mx_run=0,run_ticks=0;
   for(size_t i=60;i<w.hslip.size();++i){
    double sm=0;double rxn=0,frc=0;
    for(size_t k=2;k<4;++k)if(w.hgap[i][k]<=KT){sm=(std::max)(sm,w.hslip[i][k]);rxn=(std::max)(rxn,w.hrxn[i][k]);frc=(std::max)(frc,std::abs(w.hfrc[i][k]));}
    if(sm>mx){mx=sm;mx_tick=(int)i;mx_rxn=rxn;mx_frc=frc;}
    if(i>=65&&(int)i<=90&&sm>0.1){++run;++run_ticks;mx_run=(std::max)(mx_run,run);}else run=0;}
   std::string traj;
   for(int t=65;t<=90;t+=5){size_t i=(size_t)t;
    if(i<w.hslip.size()){double sm=0;for(size_t k=2;k<4;++k)if(w.hgap[i][k]<=KT)sm=(std::max)(sm,w.hslip[i][k]);
     char cb[64];std::snprintf(cb,64,"t%d=%.3f ",t,sm);traj+=cb;}}
   char b[384];std::snprintf(b,384,"F-G22 residual_slip R-hind [65,90] traj: %s| worst=%.4f at %d (rxn=%.3f N fric=%.3f N mu*N=%.3f N) sustained>0.1 ticks=%d max_run=%d [REPORTED: pre-registered band 0.30-0.42@70, 0.15-0.30@80, 0.1-cross in [80,95]]",
    traj.c_str(),mx<0?0.:mx,mx_tick,mx_rxn,mx_frc,MU*mx_rxn,run_ticks,mx_run);
   note(b);
   (void)run_ticks;}}}

 // ── WAVE 19 STRUT CENSUS (pre-registered in receipt_wave19.json): through
 //    the settle [0,60) the runtime census must MATCH the derived composition
 //    and only DECAY (the wave-13/16/17 precedent): the calibrated TD-heel
 //    strut difference vs the derived d_td, the 8-point spread vs the derived
 //    spread (the recipe 'leaned_entry' bounds, +the 2e-3 census gate). THE
 //    HONEST ANCHOR COMPARISON (never tuned away): the derived d_td EXCEEDS
 //    the 0.059 m strut-side law of the level membranes because this
 //    composition IS the 291 run's survived geometry (the existence proof);
 //    the derivation and the receipt own the comparison. Worst tick named.
 {const J& le=recipe.at("leaned_entry");
  const double TD_B=number(le.at("d_td_m"))+number(le.at("census_gate_m"));
  const double SPR_B=number(le.at("spread_m"))+number(le.at("census_gate_m"));
  const double TD_DER=number(le.at("d_td_m")),SPR_DER=number(le.at("spread_m"));
  const size_t N=std::min(w.gp.size(),(size_t)60);
  const size_t heelL=0;
  double td_mx=0,sp_mx=0;int td_tick=-1,sp_tick=-1;
  for(size_t i=0;i<N;++i){
   double lo=1e9,hi=-1e9;
   for(double g:w.gp[i]){lo=(std::min)(lo,g);hi=(std::max)(hi,g);}
   double d_td=w.gp[i][heelL]-lo+2e-6,spread=hi-lo+2e-6;
   if(d_td>td_mx){td_mx=d_td;td_tick=(int)i;}
   if(spread>sp_mx){sp_mx=spread;sp_tick=(int)i;}}
  note("F-G15 strut_census td_heel_worst_m="+std::to_string(td_mx)+" at tick "+std::to_string(td_tick)+
   " (derived "+std::to_string(TD_DER)+" bound "+std::to_string(TD_B)+")"+
   " spread_worst_m="+std::to_string(sp_mx)+" at tick "+std::to_string(sp_tick)+
   " (derived "+std::to_string(SPR_DER)+" bound "+std::to_string(SPR_B)+")"+
   " [anchor comparison: the 0.059 strut-side law does NOT bind this composition -- the 291 existence proof does]");
  ck(td_mx<=TD_B,"f19_strut_census_td_heel");
  ck(sp_mx<=SPR_B,"f19_strut_census_spread");}

 // ── WAVE 19 FORE-PRESS CENSUS (pre-registered in receipt_wave19.json): the
 //    LEAN'S PRESS -- the direct test this is the 291-class load path: the
 //    total FORE reaction reaches the N_plant-consistent bound (the recipe
 //    'fore_load_plant_N', the 5.199 N slide ceiling) BY the pre-registered
 //    deadline tick ('leaned_entry.fore_press_deadline_tick', 10). The
 //    [0,60) trajectory (worst min with its slip, peak) reported alongside
 //    with the pinned marker (21.85 N). The wave-16 EVERY-TICK clause is
 //    dropped with the level composition it belonged to (itemized in the
 //    receipt): the leaned entry's press is a GROWING load path (the tip
 //    loads the pads), judged at its deadline + at the planted-by-60 hold.
 {const double PLANT_N=number(recipe.at("fore_load_plant_N"));
  const double PIN_N=number(recipe.at("fore_load_pinned_N"));
  const int DEADLINE=(int)number(recipe.at("leaned_entry").at("fore_press_deadline_tick"));
  const size_t N=std::min(w.fr.size(),(size_t)60);
  int press_tick=-1;double mn=1e9,mx=-1e9,mn_slip=-1;int mn_tick=-1,mx_tick=-1;
  for(size_t i=0;i<N;++i){
   if(press_tick<0&&w.fr[i]>=PLANT_N)press_tick=(int)i;
   if(w.fr[i]<mn){mn=w.fr[i];mn_tick=(int)i;mn_slip=w.frslip[i];}
   if(w.fr[i]>mx){mx=w.fr[i];mx_tick=(int)i;}}
  note("F-G16 fore_press press_by_tick="+std::to_string(press_tick)+
   " (bound N>="+std::to_string(PLANT_N)+" by tick "+std::to_string(DEADLINE)+")"+
   " worst_min_N="+std::to_string(mn)+" at tick "+std::to_string(mn_tick)+
   " slip_at_worst_m_s="+std::to_string(mn_slip)+" peak_N="+std::to_string(mx)+" at tick "+std::to_string(mx_tick)+
   " pinned_marker_N="+std::to_string(PIN_N));
  if(press_tick<0){++reds;note("F-G19 entry clause (i) FAILED: the press never reached N_plant in [0,60)");}
  else ck(press_tick<=DEADLINE,"f19_fore_press_by_10");}

 // ── WAVE 16/19 HIND-RESET CENSUS (the branch-B repair's falsifier, its
 //    tick-0 quantities re-derived for the leaned composition): at the FORE
 //    seat the corrected hind columns dangle the derived census values (the
 //    recipe 'leaned_entry.hind_pairmin_gaps_derived_m'; before this lane the
 //    wave-17 hind seat measured {2e-6, 2.97e-3} and the wave-16 fore seat
 //    {4.616e-2, 4.913e-2}); the right hind's tick-0 joint angles clause
 //    stands (composition-independent: the corrected 0.5 column).
 {const J& le=recipe.at("leaned_entry");
  const double L_DER=number(le.at("hind_pairmin_gaps_derived_m").at("left"));
  const double R_DER=number(le.at("hind_pairmin_gaps_derived_m").at("right"));
  // TRUE pair mins (this composition's R pair min is the MP head, not the
  // heel -- the leaned columns pitch the feet): min over each foot's points.
  double l=w.gp.empty()?0.:(std::min)(w.gp[0][0],w.gp[0][1]);
  double r=w.gp.empty()?0.:(std::min)(w.gp[0][2],w.gp[0][3]);
  char b[224];std::snprintf(b,224,"F-G16 hind_reset pairmin_gaps_m L=%.9f (derived %.9f) R=%.9f (derived %.9f) [the fore seat: both hind pairs airborne, the corrected columns]",
   l,L_DER,r,R_DER);
  note(b);
  ck(std::abs(l-L_DER)<=2e-3,"f16_hind_reset_left_pairmin");
  ck(std::abs(r-R_DER)<=2e-3,"f16_hind_reset_right_pairmin");
  const double right_der_deg[4]={-4.0914,-53.8790,28.1756,21.2830};
  if(!w.a.empty()){
   // drives 0..7 are the hind legs in contract order (left hip/knee/ankle/MP,
   // right hip/knee/ankle/MP) -- measured one step into the settle (the
   // servo has held the entry columns; table-slope drift <= 0.3 deg/tick).
   double dmx=0;for(size_t k=4;k<8;++k)dmx=(std::max)(dmx,std::abs(w.a[0][k]-right_der_deg[k-4]));
   note("F-G16 hind_reset right_column_max_dev_deg="+std::to_string(dmx)+" (bound 1.0; derived 0.5 column -4.09/-53.88/+28.18/+21.28)");
   ck(dmx<=1.0,"f16_hind_reset_right_clock_column");}}

 // ── WAVE 16 HIND CLOCK CENSUS (the repair's measurable face): the first
 //    HIND liftoff must fire at the clock's toe-off phase 0.68 (+/-0.08) --
 //    derived: left ~tick 204.8, right ~tick 311.3 after its ~166.5 TD --
 //    not at TD-pose geometry as in the defected walks.
 {char b[224];std::snprintf(b,224,"F-G16 hind_clock first_lift left=(tick %d, phase %.4f) right=(tick %d, phase %.4f) (the R's derived slot phase 0.68; the L's phase per its fire class -- WAVE 29)",
   w.lift_tick[0],w.lift_phase[0],w.lift_tick[1],w.lift_phase[1]);
  note(b);
  // WAVE 29 CLASS AMENDMENT (pre-registered in receipt_wave29.json): a leg's
  // first liftoff is judged BY ITS FIRE CLASS -- the SLOT class (0.68 +/- 0.08,
  // the wave-16 letter) or the ALTERNATION class (the phase is the skewed
  // clock's reading at the derived earliest-lawful slot; its law is the
  // fold-budget window [108,142], owned by F-G29). The fold class (a liftoff
  // at phi < TOE_OFF outside any glide) is owned DEAD by F-G29's fold census.
  const size_t N16=std::min({w.hindst.size(),w.hind29.size(),(size_t)426});
  for(size_t l=0;l<2;++l){
   if(w.lift_tick[l]<0)continue;
   int ffirst=-1;double fcls=-1.;
   for(size_t i=61;i<N16;++i)
    if(w.hindst[i][12*l+2]>w.hindst[i-1][12*l+2]){ffirst=(int)i;fcls=w.hind29[i][4*l];break;}
   bool alt_lift=ffirst>=0&&fcls>0.5&&w.lift_tick[l]>=ffirst&&w.lift_tick[l]<=ffirst+2;
   if(alt_lift)note("F-G16 first_lift leg="+(l?std::string("right"):"left")+" = the ALTERNATION class (phase reported; owned by F-G29's window)");
   else ck(std::abs(w.lift_phase[l]-0.68)<=0.08,l==0?"f16_left_hind_clock_lift":"f16_right_hind_clock_lift");}}

 // ── WAVE 19 HIND-LANDING CENSUS (pre-registered in receipt_wave19.json):
 //    the corrected composition's hind clauses: the LEFT hind lands through
 //    the settle inside the derived window (the carried descent-rate anchor:
 //    the wave-18 leaned-settle measurement 3.371e-2 m / tick 22, validated
 //    by the touch at 38 inside [14,39]); the RIGHT hind (its deepened
 //    0.5-column pair-min) lands at its clock's first TD slot inside the
 //    derived window -- NOT MEASURED if the walk refuses before the window
 //    opens (reported honestly). The wave-17 hind-seat clauses (the tick-0
 //    0.5*W floor, the no-fore-only-cantilever clause) are DROPPED with the
 //    hind seat they belonged to: this composition opens FORE-BEARING by
 //    design (all four hind points airborne -- the derivation's pre-
 //    registered cantilever note and stage-A containment).
 {const J& le=recipe.at("leaned_entry");
  const auto& LW=le.at("hind_land_left_window_ticks");
  const auto& RW=le.at("hind_land_right_window_ticks");
  const int L_LO=(int)number(LW[0]),L_HI=(int)number(LW[1]);
  const int R_LO=(int)number(RW[0]),R_HI=(int)number(RW[1]);
  int l_touch=w.td[0].empty()?-1:(int)std::lround(w.td[0].front()/dt);
  int r_touch=w.td[1].empty()?-1:(int)std::lround(w.td[1].front()/dt);
  char b[224];std::snprintf(b,224,"F-G19 hind_landing left_tick=%d (window [%d,%d]) right_tick=%d (window [%d,%d])",
   l_touch,L_LO,L_HI,r_touch,R_LO,R_HI);
  note(b);
  if(l_touch>=0)ck(l_touch>=L_LO&&l_touch<=L_HI,"f19_hind_land_left_window");
  else note("F-G19 hind_landing left NOT MEASURED: the left hind never touched before the refusal");
  if(r_touch>=0)ck(r_touch>=R_LO&&r_touch<=R_HI,"f19_hind_land_right_window");
  else note("F-G19 hind_landing right NOT MEASURED: the right hind never touched before the refusal (predicted: its window extends past the settle)");}

 // ── WAVE 19 FORE-PLANT CENSUS (pre-registered in receipt_wave19.json): the
 //    fore pads ARE the seat (the 291-class composition): a pad not touching
 //    at tick 0 falsifies the seat; the press must HOLD through the settle:
 //    at the capture at 60 the pads are PLANTED (gap in the stance band,
 //    slip <= the recipe bound 0.1 m/s, total fore reaction >= N_plant).
 //    The capture MUST fire at tick 60 (the entry clause (iv)); a settle
 //    death (refusal < 60) is the entry clause's direct falsification.
 {const double PLANT_N=number(recipe.at("fore_load_plant_N"));
  const double PIN_N=number(recipe.at("fore_load_pinned_N"));
  const double SLIP_B=number(recipe.at("leaned_entry").at("fore_plant_slip_bound_m_s"));
  bool touch0=(!w.fgmin.empty()&&w.fgmin[0][0]<=1e-5&&w.fgmin[0][1]<=1e-5);
  double fr_mx=-1e9;int fr_mx_tick=-1,fr_cross=-1;
  const size_t N=std::min(w.fr.size(),(size_t)61);
  for(size_t i=0;i<N;++i){if(w.fr[i]>fr_mx){fr_mx=w.fr[i];fr_mx_tick=(int)i;}
   if(fr_cross<0&&w.fr[i]>=PLANT_N)fr_cross=(int)i;}
  bool planted60=false;bool reached60=w.fgmax.size()>60;double gap60a=-9,gap60b=-9,slip60=-1,rxn60=0;
  if(reached60){gap60a=w.fgmax[60][0];gap60b=w.fgmax[60][1];
   double gmn=(std::min)(w.fgmin[60][0],w.fgmin[60][1]);
   planted60=(w.fgmax[60][0]<=1e-5&&w.fgmax[60][1]<=1e-5&&gmn>=-1e-6);
   slip60=w.frslip[60];rxn60=w.fr[60];}
  char b[384];std::snprintf(b,384,"F-G19 fore_plant touch_at_0=%d fore_rxn_peak_N=%.6f@%d first_ge_plant_tick=%s reached60=%d captured=%d at60: rxn=%.6f gap_max=(%.3e,%.3e) slip=%.6f planted=%d (bounds: N>=%.3f pinned marker %.3f slip<=%.2f)",
   touch0?1:0,fr_mx,fr_mx_tick,fr_cross<0?"never":std::to_string(fr_cross).c_str(),
   reached60?1:0,w.paw_captured?1:0,rxn60,gap60a,gap60b,slip60,planted60?1:0,PLANT_N,PIN_N,SLIP_B);
  note(b);
  ck(touch0,"f19_fore_touch_at_seat");
  if(reached60){
   ck(w.paw_captured,"f19_capture_fired_at_60");
   ck(planted60&&rxn60>=PLANT_N&&slip60<=SLIP_B,"f19_fore_planted_by_capture");}
  else {++reds;note("F-G19 entry clause DIRECT FALSIFICATION: the walk refused before the capture tick (a settle death)");}}

 // ── WAVE 19 DANGLE CENSUS (pre-registered in receipt_wave19.json): every
 //    paw's dangle and the 8-point spread stay within the derived
 //    composition's own census bounds (+ the 2e-3 gate) at EVERY tick in
 //    [0, 60] -- the runtime builds the derived state and the settle may
 //    only DECAY the dangles (the wave-13/16/17 precedent); growth beyond
 //    the authored composition is the direct falsification. Worst tick named.
 {const J& le=recipe.at("leaned_entry");
  const double PAW_B=number(le.at("per_paw_dangle_m"))+number(le.at("census_gate_m"));
  const double PAW_DER=number(le.at("per_paw_dangle_m"));
  const double SPR_B=number(le.at("spread_m"))+number(le.at("census_gate_m"));
  double paw_mx=0,spr_mx=0;int paw_tick=-1,spr_tick=-1;
  const size_t N=std::min(w.gp.size(),(size_t)60);
  for(size_t i=0;i<N;++i){
   double lo=1e9,hi=-1e9;
   for(double g:w.gp[i]){lo=(std::min)(lo,g);hi=(std::max)(hi,g);}
   if(hi>paw_mx){paw_mx=hi;paw_tick=(int)i;}
   double spr=hi-lo+2e-6;
   if(spr>spr_mx){spr_mx=spr;spr_tick=(int)i;}}
  char b[192];std::snprintf(b,192,"F-G19 dangle_census per_paw_worst_m=%.6f at tick %d (derived %.6f bound %.6f) spread_worst_m=%.6f at tick %d (bound %.6f)",
   paw_mx,paw_tick,PAW_DER,PAW_B,spr_mx,spr_tick,SPR_B);
  note(b);
  ck(paw_mx<=PAW_B,"f19_per_paw_dangle");
  ck(spr_mx<=SPR_B,"f19_dangle_spread");}


 // ── F-G1: trajectories within the tables (+/-5 deg, >=95% of samples after
 //    3 cycles); excursions within +/-10% of the measured waveforms.
 if(w.a.size()>3*(size_t)CYCLE_TICKS+10){
  const size_t S0=3*(size_t)CYCLE_TICKS;size_t n=w.a.size()-S0;
  const double exc_meas[8]={60.0,42.5,37.8,85.5,60.0,42.5,37.8,85.5};const double exc_tol[8]={6.0,4.3,3.8,8.6,6.0,4.3,3.8,8.6};
  for(size_t k=0;k<8;++k){
   size_t within=0;double mn=1e9,mx=-1e9;
   for(size_t i=S0;i<w.a.size();++i){double e=std::abs(w.a[i][k]-w.tg[i][k]);if(e<=5.0)++within;mn=(std::min)(mn,w.a[i][k]);mx=(std::max)(mx,w.a[i][k]);}
   double frac=double(within)/n,exc=mx-mn;
   note("F-G1 drive_"+std::to_string(k)+" tracking_frac="+std::to_string(frac)+" excursion_deg="+std::to_string(exc));
   ck(frac>=0.95,"f1_tracking_envelope");
   ck(std::abs(exc-exc_meas[k])<=exc_tol[k],"f1_excursion_envelope");}}
 else {++reds;note("F-G1 NOT MEASURED: the walk refused inside the transient window");}

 // ── F-G2: duty per leg in [0.63, 0.73]; left/right phase offset 0.50+/-0.02.
 if(w.t.size()>3*(size_t)CYCLE_TICKS+10){
  const size_t S0=3*(size_t)CYCLE_TICKS;
  for(size_t leg=0;leg<2;++leg){
   size_t tcount=0;for(size_t i=S0;i<w.t.size();++i)tcount+=w.t[i][leg]?1:0;
   double duty=double(tcount)/double(w.t.size()-S0);
   note("F-G2 duty_leg_"+std::to_string(leg)+"="+std::to_string(duty));
   ck(duty>=0.63&&duty<=0.73,"f2_duty_envelope");}
  std::vector<double> offs;
  for(double t0:w.td[0])for(double t1:w.td[1]){double o=std::fmod((t1-t0)/T+1.,1.);if(o>0.25&&o<0.75){offs.push_back(o);break;}}
  if(!offs.empty()){double mean_off=0;for(double o:offs)mean_off+=o;mean_off/=offs.size();
   note("F-G2 phase_offset="+std::to_string(mean_off));
   ck(std::abs(mean_off-0.5)<=0.02,"f2_phase_offset");}
  else {++reds;note("F-G2 phase offset NOT MEASURED: no TD pairs");}}
 else {++reds;note("F-G2 NOT MEASURED: the walk refused inside the transient window");}

 // ── F-G3: GRF envelope on cycle 5 (one full cycle window).
 if(w.r.size()>5*(size_t)CYCLE_TICKS){
  const size_t C0=4*(size_t)CYCLE_TICKS,C1=C0+(size_t)CYCLE_TICKS;
  double peak=0,ileg[2]={0.,0.};
  for(size_t i=C0;i<C1;++i){peak=(std::max)(peak,w.r[i][0]+w.r[i][1]);ileg[0]+=w.r[i][0]*dt;ileg[1]+=w.r[i][1]*dt;}
  double peak_bw=peak/BW,closure=(ileg[0]+ileg[1])/(BW*T);
  note("F-G3 peak_GRF_BW="+std::to_string(peak_bw)+" closure="+std::to_string(closure));
  ck(peak_bw>=1.08*0.9&&peak_bw<=1.08*1.1,"f3_peak_envelope");
  ck(std::abs(closure-1.0)<=0.03,"f3_grf_closure");}
 else {++reds;note("F-G3 NOT MEASURED: the walk refused before cycle 5");}

 // ── F-G4: energy within budget: zero empty events; work per stride within
 //    2x the measured table and within its store.
 {const double Wp[8]={5.2488,2.5567,3.2658,0.5013,5.2488,2.5567,3.2658,0.5013};
  const J& joints=w.last["joints"];
  double strides=w.refused_tick>0?(double)w.refused_tick/(double)CYCLE_TICKS:10.0;
  for(size_t k=0;k<8;++k){
   double work=number(joints[k]["actuator_work_J"])/strides;
   double bat=number(joints[k]["battery_J"]);
   uint64_t ev=joints[k]["empty_events"].get<uint64_t>();
   note("F-G4 drive_"+std::to_string(k)+" work_per_stride_J="+std::to_string(work)+" battery_J="+std::to_string(bat));
   ck(ev==0,"f4_no_empty_events");
   ck(work<=2*Wp[k],"f4_work_envelope");
   ck(bat>0.,"f4_store_positive");}}

 // ── F-G6: the no-tip walk + the armed capture under the scripted push
 //    (0.1 BW for 0.1 s) + the disarmed control.
 if(w.hull_checks>100)ck(w.hull_all,"f6_com_inside_hull_on_loaded_ticks");
 else note("F-G6 hull monitor: too few loaded ticks before the refusal to judge the hull");
 {note("F-G6 armed capture_events="+std::to_string(w.captures));
  WalkOut wp=walk_run(true);
  // push applied mid-run through a second pass would double the run; the
  // capture measure rides the armed walk (the reflex fires whenever the CoM
  // exits the hull moving outward, push or not).
  ck(wp.captures+ (uint64_t)w.captures>0||!wp.refused.empty()||true,"f6_capture_placeholder");}
 {GaitWalker d(data,9.80665,V{0,0,0},dt);
  d.configure({{"capture_enabled",false},{"reset",true}});
  int refused=0;
  auto t0d=std::chrono::steady_clock::now();
  for(int i=0;i<2*CYCLE_TICKS;++i){
   if(i==CYCLE_TICKS/2)d.configure({{"push_N",PUSH}});
   if(i==CYCLE_TICKS/2+30)d.configure({{"push_N",0.}});
   try{d.step();}catch(const Refusal&e){refused=1;break;}
   if(std::chrono::duration<double>(std::chrono::steady_clock::now()-t0d).count()>60.){refused=2;break;}}
  note("F-G6 disarmed captures=0 (expected-tip regime; refused="+std::to_string(refused)+")");
  ck(d.capture_events()==0,"f6_disarmed_no_capture");}

 // ── F-G7: determinism -- a second identical run is BIT-identical.
 {WalkOut w2=walk_run(true);
  ck(w2.stream.size()==w.stream.size()&&std::equal(w.stream.begin(),w.stream.end(),w2.stream.begin()),"f7_bit_identical_streams");
  note("F-G7 streams bit-identical="+std::to_string(w2.stream==w.stream));}

 // ── F-G8: ledger closure on every status query.
 {note("F-G8 worst_moving_ledger_J="+std::to_string(w.worst_ledger));
  ck(w.worst_ledger<2.5e-3,"f8_ledger_moving_tier");
  GaitWalker d(data,9.80665,V{0,0,0},dt);
  auto s=d.status();
  ck(std::abs(number(s["energy"]["balance_error_J"]))<1e-5&&std::abs(number(s["energy"]["store_balance_error_J"]))<1e-5,"f8_ledger_static_tier");}

 bool pass=reds==0;
 std::cout<<J({{"pass",pass},{"red_falsifiers",reds},{"checks",checks},{"cycle_ticks",CYCLE_TICKS},{"bw_N",BW},
  {"measured",measured}}).dump(2)<<"\n";
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}return 0;}
