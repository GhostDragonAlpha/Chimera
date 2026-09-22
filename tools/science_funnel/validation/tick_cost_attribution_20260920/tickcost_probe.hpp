// tickcost_probe.hpp -- the TICK-COST ATTRIBUTION recorder (lane
// lane/tick-cost-attribution-20260920, prereg PREREG.md in this directory).
//
// Included ONLY by the derived instrument copies that make_instrument.py
// generates under .tmp/ -- the tracked engine bytes are never modified.
// Everything here is FP-neutral: chrono accumulation + counters, stderr-only
// output, no per-tick fprintf in the hot path. The byte-neutrality is proven
// per run: the instrumented binary's stdout sha256 must equal the pinned ship
// sha (F2, PREREG.md).
//
// Trailer Agent: tickcost.
#pragma once
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <algorithm>
#include <vector>

namespace tickcost {

// The timed classes. The five step() stages close the tick EXCLUSIVELY
// (PREREG F3d: their sum must reach >= 95% of the loop wall); the rest are
// INCLUSIVE shares inside those stages (labeled in the receipt).
enum Cls {
  ST_RESET_ALLOC = 0, // step() tick-start buffer reset (exclusive stage)
  ST_REFLEX_CLOCK,    // tick-start stage: evaluate + update_clock + fore clock
                      // + height emergency + hind step law (exclusive stage)
  ST_CAPTURE_REFLEX,  // support hull + chain + capture_reflex (exclusive stage)
  ST_SAT_CENSUS,      // planted-strut saturation census (exclusive stage)
  ST_INTEGRATE,       // the 4-substep loop stage (exclusive stage, inclusive
                      // of servo + advance + battery bookkeeping)
  ADV_TOTAL,          // inclusive inside ST_INTEGRATE: all advance() time
  ADV_IMPACT,         // inclusive inside ADV_TOTAL: impact()
  ADV_FREESTEP,       // inclusive inside ADV_TOTAL: free_step() (RK4)
  ADV_RATE,           // inclusive inside ADV_FREESTEP: rate() x4
  SERVO,              // inclusive inside ST_INTEGRATE: servo() x4
  FK_EVALUATE,        // inclusive leaf: model_->evaluate() across ALL sites
  INV_SPD,            // inclusive leaf: inverse_spd() at the gait call sites
  FRICTION_SOLVE,     // inclusive leaf: friction_solve()
  PROJECT_ROWS,       // inclusive leaf: project_rows()
  UPDATE_CLOCK,       // inclusive inside ST_REFLEX_CLOCK: update_clock()
  FORE_CLOCK,         // inclusive inside ST_REFLEX_CLOCK: update_fore_clock()
  CAPTURE_FN,         // inclusive inside ST_CAPTURE_REFLEX: capture_reflex()
  SUPPORT_STATE,      // inclusive inside ST_CAPTURE_REFLEX: support_state() x2
  STATUS_JSON,        // harness: d.status() per tick (observation assembly)
  CENSUS_BLOCK,       // harness: the per-tick census/parse block
  DUMP_BLOCK,         // harness: the every-10-tick s.dump() stream append
  CLS_COUNT
};
static const char* CLS_NAME[CLS_COUNT] = {
  "step.reset_alloc", "step.reflex_clock", "step.capture_reflex",
  "step.sat_census", "step.integrate",
  "adv.total", "adv.impact", "adv.free_step", "adv.rate",
  "servo", "fk.evaluate", "solver.inverse_spd",
  "solver.friction_solve", "solver.project_rows",
  "clock.update_clock", "clock.fore_clock", "reflex.capture_fn",
  "reflex.support_state",
  "obs.status_json", "harness.census", "harness.dump" };

struct Rec {
  double ns[CLS_COUNT];
  unsigned long long hits[CLS_COUNT];
  // per-tick advance()-call bookkeeping (the store-bisection + event share)
  unsigned long long adv_base;
  std::vector<unsigned long long> adv_per_tick;
  // per-tick wall samples (nanoseconds)
  std::vector<long long> walk_ticks, push_ticks;
  // allocation bookkeeping (counted operator new in the harness TU)
  unsigned long long alloc_count, alloc_bytes;
  unsigned long long ac_base, ab_base;
  std::vector<std::pair<unsigned long long, unsigned long long> > alloc_per_tick;
  // full-loop wall (the loop the phase summary covers)
  std::chrono::steady_clock::time_point loop_t0; bool loop_on;
  // tick wall sample plumbing
  std::chrono::steady_clock::time_point tick_t0; bool tick_on;
  // explicit per-class begin/end plumbing (used where a RAII block would
  // break scoping, e.g. `s` must outlive the status timer)
  std::chrono::steady_clock::time_point pt_t[CLS_COUNT];
  // re-entrancy depth for recursively-called scopes (ADV_TOTAL: advance()
  // recurses on events; a plain RAII scope would accumulate the recursion
  // depth-over-time integral, inflating the total)
  int adv_depth; std::chrono::steady_clock::time_point adv_t0;

  Rec(){reset_all();}
  void reset_all(){
    for(int i=0;i<CLS_COUNT;++i){ns[i]=0.;hits[i]=0;}
    adv_base=0;adv_per_tick.clear();
    walk_ticks.clear();push_ticks.clear();
    alloc_count=0;alloc_bytes=0;ac_base=0;ab_base=0;alloc_per_tick.clear();
    loop_on=false;tick_on=false;adv_depth=0;}
  void t_begin(Cls c){pt_t[c]=std::chrono::steady_clock::now();}
  void t_end(Cls c){ns[c]+=std::chrono::duration<double,std::nano>(
    std::chrono::steady_clock::now()-pt_t[c]).count();++hits[c];}
  void adv_enter(){if(adv_depth++==0)adv_t0=std::chrono::steady_clock::now();}
  void adv_leave(){if(--adv_depth==0){ns[ADV_TOTAL]+=std::chrono::duration<
    double,std::nano>(std::chrono::steady_clock::now()-adv_t0).count();++hits[ADV_TOTAL];}}
  void adv_snap(unsigned long long cur){(void)cur;}
  // adv_calls_ is reset to 0 INSIDE step() every tick (the production code's
  // own work-budget line), so the value read at step end IS this tick's count.
  void adv_note(unsigned long long cur){adv_per_tick.push_back(cur);}
  void alloc_snap(){ac_base=alloc_count;ab_base=alloc_bytes;}
  void alloc_note(){alloc_per_tick.push_back(std::make_pair(
    alloc_count-ac_base,alloc_bytes-ab_base));}
  void loop_begin(){loop_t0=std::chrono::steady_clock::now();loop_on=true;}
  void tick_begin(){tick_t0=std::chrono::steady_clock::now();tick_on=true;}
  void tick_end_walk(){if(tick_on){
    walk_ticks.push_back((long long)std::chrono::duration<double,std::nano>(
      std::chrono::steady_clock::now()-tick_t0).count());tick_on=false;}}
  void tick_end_push(){if(tick_on){
    push_ticks.push_back((long long)std::chrono::duration<double,std::nano>(
      std::chrono::steady_clock::now()-tick_t0).count());tick_on=false;}}
};

inline Rec& rec(){static Rec r;return r;}

// RAII scope; zero per-tick I/O.
struct Scope {
  std::chrono::steady_clock::time_point t;const Cls c;
  explicit Scope(Cls c_):t(std::chrono::steady_clock::now()),c(c_){}
  ~Scope(){rec().ns[c]+=std::chrono::duration<double,std::nano>(
    std::chrono::steady_clock::now()-t).count();++rec().hits[c];}
};

// Re-entrancy-aware scope for advance(): advance() recurses on events, so a
// plain scope would accumulate the recursion depth-over-time integral; only
// the OUTERMOST frame books wall time here.
struct AdvScope {
  AdvScope(){rec().adv_enter();}
  ~AdvScope(){rec().adv_leave();}
};

inline unsigned long long tc_p95(std::vector<unsigned long long>& v){
  std::sort(v.begin(),v.end());
  return v[(size_t)(0.95*double(v.size()-1))];}

inline void summary(const char* phase){
  Rec&R=rec();
  double loop_ns=0;
  if(R.loop_on)loop_ns=std::chrono::duration<double,std::nano>(
    std::chrono::steady_clock::now()-R.loop_t0).count();
  for(int i=0;i<CLS_COUNT;++i)
    std::fprintf(stderr,"[tc] phase=%s cls=%s ms=%.4f hits=%llu\n",phase,
      CLS_NAME[i],R.ns[i]/1e6,R.hits[i]);
  if(loop_ns>0){
    size_t n=R.walk_ticks.size()+R.push_ticks.size();
    if(n)std::fprintf(stderr,"[tc] phase=%s loop_wall_ms=%.3f ticks=%zu full_loop_us_per_tick=%.2f\n",
      phase,loop_ns/1e6,n,loop_ns/1e3/double(n));}
  if(!R.adv_per_tick.empty()){
    std::vector<unsigned long long> s(R.adv_per_tick);
    double mean=0;for(size_t i=0;i<s.size();++i)mean+=double(s[i]);
    mean/=double(s.size());
    std::fprintf(stderr,"[tc] phase=%s adv_calls mean=%.3f p95=%llu max=%llu n=%zu\n",
      phase,mean,tc_p95(s),s.back(),s.size());}
  if(!R.alloc_per_tick.empty()){
    double mc=0,mb=0;for(size_t i=0;i<R.alloc_per_tick.size();++i){
      mc+=double(R.alloc_per_tick[i].first);mb+=double(R.alloc_per_tick[i].second);}
    mc/=double(R.alloc_per_tick.size());mb/=double(R.alloc_per_tick.size());
    std::fprintf(stderr,"[tc] phase=%s alloc mean_count=%.1f mean_bytes=%.0f n=%zu (standard new/delete only)\n",
      phase,mc,mb,R.alloc_per_tick.size());}
  if(!R.walk_ticks.empty()){
    std::fprintf(stderr,"[tc-ticks] phase=%s kind=walk n=%zu ",phase,R.walk_ticks.size());
    for(size_t i=0;i<R.walk_ticks.size();++i)
      std::fprintf(stderr,"%s%lld",i?",":"",R.walk_ticks[i]);
    std::fprintf(stderr,"\n");}
  if(!R.push_ticks.empty()){
    std::fprintf(stderr,"[tc-ticks] phase=%s kind=push n=%zu ",phase,R.push_ticks.size());
    for(size_t i=0;i<R.push_ticks.size();++i)
      std::fprintf(stderr,"%s%lld",i?",":"",R.push_ticks[i]);
    std::fprintf(stderr,"\n");}
}

} // namespace tickcost
