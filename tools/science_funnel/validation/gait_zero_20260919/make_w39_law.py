"""Apply the WAVE-39 SIXTH CLAUSE (the stay-era haul restoration) to the
working-tree gait_controller.hpp (the wave-38 shipped law bytes), exactly as
frozen in receipt_wave39.json:
  - the certificate: the launch-time link flag (the wave-38 guard's own
    stall_era_link arithmetic carried per leg) AND the lift-first hold still
    armed at the era's own tair bound;
  - the completion read: the certified stay does not certify the replant --
    the machine re-fires the swing (the wave-28 fire sequence re-run at the
    tick-start state; the glide clock reset to its own initialization value;
    the re-fired era's predecessor ran exactly tair, so the link flag
    re-sets);
  - the pin read: the wave-33 carrier's stand-first hold disarms on the
    riding swing's re-fire and may not re-arm while the certificate stands;
    it restores on the swing's genuine lift (the release) or completion;
  - the census counters hind_step_refires_ / hind_step_refire_first_ per leg
    and the status keys refires / refire_first_tick.
"""
import sys

p = "ChimeraEngine/engine/gait_controller.hpp"
src = open(p, "rb").read().decode("utf-8")
NL = "\r\n"

def frag(lines):
    return NL.join(lines)

# 1. the state (next to the guard counters)
a = frag([
" uint64_t hind_step_guard_blocks_[2]={0,0}; // the calendar-arithmetic waive scope guard's blocks (the census)",
" int hind_step_guard_first_[2]={-1,-1};     // the first guard block's tick (the census)",
])
b = a + NL + frag([
" bool hind_step_link_[2]={false,false};     // the launch-time link flag (the guard's own arithmetic, carried: the sixth clause)",
" bool hind_step_refire_[2]={false,false};   // the stay-era re-fire certificate (the sixth clause)",
" uint64_t hind_step_refires_[2]={0,0};      // the stay-era re-fires (the census)",
" int hind_step_refire_first_[2]={-1,-1};    // the first re-fire's tick (the census)",
])
assert src.count(a) == 1, "counters site"
src = src.replace(a, b)

# 2. the reset site
a = frag([
"  hind_step_guard_blocks_[0]=hind_step_guard_blocks_[1]=0;",
"  hind_step_guard_first_[0]=hind_step_guard_first_[1]=-1;",
])
b = a + NL + frag([
"  hind_step_link_[0]=hind_step_link_[1]=false;",
"  hind_step_refire_[0]=hind_step_refire_[1]=false;",
"  hind_step_refires_[0]=hind_step_refires_[1]=0;",
"  hind_step_refire_first_[0]=hind_step_refire_first_[1]=-1;",
])
assert src.count(a) == 1, "reset site"
src = src.replace(a, b)

# 3. the status keys (the F-G39 harvest reads them by contains)
a = frag([
"      {\"guard_blocks\",hind_step_guard_blocks_[hl]},",
"      {\"guard_first_tick\",hind_step_guard_first_[hl]},",
])
b = a + NL + frag([
"      // THE STAY-ERA HAUL RESTORATION's census fields (wave 39). Read-only.",
"      {\"refires\",hind_step_refires_[hl]},",
"      {\"refire_first_tick\",hind_step_refire_first_[hl]},",
])
assert src.count(a) == 1, "status site"
src = src.replace(a, b)

# 4. the launch-link flag at the fire (the guard's own arithmetic, read
#    BEFORE the fire book updates; the fresh launch clears the certificate)
a = frag([
"     hind_step_mode_[hl]=1;hind_step_t_[hl]=0.;",
"     hind_step_alt_[hl]=live_slot?0:1;",
"     hind_step_held_[hl]=true;hind_step_clear_tick_[hl]=-1;hind_step_stall_[hl]=0;",
"     ++hind_step_fires_[hl];hind_step_last_fire_[hl]=ticks_;",
])
b = frag([
"     hind_step_link_[hl]=hind_step_last_td_[hl]!=0&&",
"      hind_step_last_td_[hl]-hind_step_last_fire_[hl]==tair;",
"     hind_step_refire_[hl]=false;",
"     hind_step_mode_[hl]=1;hind_step_t_[hl]=0.;",
"     hind_step_alt_[hl]=live_slot?0:1;",
"     hind_step_held_[hl]=true;hind_step_clear_tick_[hl]=-1;hind_step_stall_[hl]=0;",
"     ++hind_step_fires_[hl];hind_step_last_fire_[hl]=ticks_;",
])
assert src.count(a) == 1, "fire site"
src = src.replace(a, b)

# 5. the release site: a genuine lift restores the pin premise
a = frag([
"      if((g1<g2?g1:g2)>kTouch+kReleaseBand){hind_step_held_[hl]=false;hind_step_clear_tick_[hl]=(int)ticks_;}",
])
b = frag([
"      if((g1<g2?g1:g2)>kTouch+kReleaseBand){hind_step_held_[hl]=false;hind_step_clear_tick_[hl]=(int)ticks_;hind_step_refire_[hl]=false;}",
])
assert src.count(a) == 1, "release site"
src = src.replace(a, b)

# 6. THE COMPLETION READ at the bound: the certified stay does not certify
#    the replant -- the machine re-fires the swing (the wave-28 sequence
#    re-run at the tick-start state)
a = frag([
"     if(hind_step_t_[hl]>=tair){",
"      double g1=gap_of(e,hind_heel_pt_[hl]),g2=gap_of(e,hind_mp_pt_[hl]);",
"      if((g1<g2?g1:g2)<=kTouch){ // the band entry: the replant IS a touchdown",
"      hind_step_mode_[hl]=0;hind_step_t_[hl]=0.; // touch reset re-syncs phi",
"      hind_step_held_[hl]=false;",
"      hind_step_last_td_[hl]=ticks_;++hind_step_tds_[hl];",
"#ifdef GAIT_EVENT_TRACE",
"      std::fprintf(stderr,\"[hindstep] td leg=%zu tick=%llu tds=%llu\\n\",",
"       hl,(unsigned long long)ticks_,(unsigned long long)hind_step_tds_[hl]);",
"#endif",
"      }",
"#ifdef GAIT_EVENT_TRACE",
"      else std::fprintf(stderr,\"[hindstep] holdreturn leg=%zu tick=%llu t=%d pairmin=%.4e\\n\",",
"       hl,(unsigned long long)ticks_,(int)hind_step_t_[hl],(g1<g2?g1:g2));",
"#endif",
"     }}",
])
b = frag([
"     if(hind_step_t_[hl]>=tair){",
"      double g1=gap_of(e,hind_heel_pt_[hl]),g2=gap_of(e,hind_mp_pt_[hl]);",
"      // THE STAY-ERA HAUL RESTORATION (wave 39, the sixth clause): an era",
"      // whose launch was chain-linked (the guard's own link arithmetic,",
"      // carried from the launch) and whose lift-first hold is STILL ARMED",
"      // at its own tair bound has falsified the lift premise -- the pads",
"      // never left the band, the haul was never commanded (the wave-29",
"      // hold's static spot+arch demand commands none BY CONSTRUCTION), and",
"      // the wave-31 band entry would certify a STAY as a touchdown. The",
"      // certified stay does not complete the replant: the machine RE-FIRES",
"      // the swing (the wave-28 fire sequence re-run at the tick-start",
"      // state; the glide clock reset to its own initialization value; the",
"      // re-fired era's predecessor ran exactly tair, so the link flag",
"      // re-sets). The carrier's stand-first hold -- whose premise IS the",
"      // swing's lift in progress -- disarms on the same certificate (the",
"      // columns resume, the vault's pivot re-establishes) and may not",
"      // re-arm until the swing's genuine lift (the release) or completion",
"      // restores the premise. Zero new numeric constants: the held_ read,",
"      // the machine's own tair clock, the guard's own link arithmetic.",
"      bool stay_cert=hind_step_link_[hl]&&hind_step_held_[hl];",
"      if(!stay_cert&&(g1<g2?g1:g2)<=kTouch){ // the band entry: the replant IS a touchdown",
"      hind_step_mode_[hl]=0;hind_step_t_[hl]=0.; // touch reset re-syncs phi",
"      hind_step_held_[hl]=false;",
"      hind_step_last_td_[hl]=ticks_;++hind_step_tds_[hl];",
"      hind_step_refire_[hl]=false;",
"#ifdef GAIT_EVENT_TRACE",
"      std::fprintf(stderr,\"[hindstep] td leg=%zu tick=%llu tds=%llu\\n\",",
"       hl,(unsigned long long)ticks_,(unsigned long long)hind_step_tds_[hl]);",
"#endif",
"      }",
"      else if(stay_cert){",
"      hind_step_t_[hl]=0.;",
"      hind_step_held_[hl]=true;hind_step_clear_tick_[hl]=-1;hind_step_stall_[hl]=0;",
"      ++hind_step_fires_[hl];hind_step_last_fire_[hl]=ticks_;",
"      hind_step_link_[hl]=true; // the re-fired era's predecessor ran exactly tair",
"      hind_step_refire_[hl]=true;hind_step_stand_[hl==0?1:0]=false;",
"      ++hind_step_refires_[hl];",
"      if(hind_step_refire_first_[hl]<0)hind_step_refire_first_[hl]=(int)ticks_;",
"      {auto p1=e.point(points_[hind_heel_pt_[hl]].index,points_[hind_heel_pt_[hl]].local).first;",
"       auto p2=e.point(points_[hind_mp_pt_[hl]].index,points_[hind_mp_pt_[hl]].local).first;",
"       V from{(p1[0]+p2[0])/2,(p1[1]+p2[1])/2,(p1[2]+p2[2])/2};",
"       hind_step_from_[hl]=from;hind_step_plant_y_[hl]=from[1];",
"       hind_step_ap_[hl]=s_.q[hind_coord_[hl][0]]+s_.q[hind_coord_[hl][1]]+s_.q[hind_coord_[hl][2]];",
"       hind_step_mp_[hl]=s_.q[hind_coord_[hl][3]];",
"       hind_step_branch_[hl]=s_.q[hind_coord_[hl][1]]>=0.?1:-1;",
"       double xoff=(std::max)(0.,s_.v[3])*(DUTY_SAMPLED*T_CYCLE)/2.;",
"       auto hip=e.point(pelvis_row_,hind_mount_[hl]).first;",
"       double h=(std::max)(0.,hip[1]-hind_step_plant_y_[hl]);",
"       double a2m=hind_L1_+hind_L2_;",
"       double dxs=hind_xm_*std::cos(hind_step_ap_[hl]);",
"       double dys=h+hind_xm_*std::sin(hind_step_ap_[hl]);",
"       double under=a2m*a2m-dys*dys;",
"       double xmax=dxs+(under>0.?std::sqrt(under):0.);",
"       if(xoff>xmax){xoff=xmax;++hind_step_clamped_[hl];}",
"       hind_step_xoff_[hl]=xoff;",
"       hind_step_to_[hl]=V{hip[0]+xoff,hind_step_plant_y_[hl],from[2]};",
"       {double qh,qk,qa;hind_step_ik(hl,e,from,qh,qk,qa);",
"        hind_step_qerr_[hl]=(std::max)(std::abs(qh-s_.q[hind_coord_[hl][0]]),",
"         (std::max)(std::abs(qk-s_.q[hind_coord_[hl][1]]),std::abs(qa-s_.q[hind_coord_[hl][2]])));}}",
"#ifdef GAIT_EVENT_TRACE",
"      std::fprintf(stderr,\"[hindstep] refire leg=%zu tick=%llu dl=%llu\\n\",",
"       hl,(unsigned long long)ticks_,(unsigned long long)hind_step_deadline_tick_[hl]);",
"#endif",
"      }",
"#ifdef GAIT_EVENT_TRACE",
"      else std::fprintf(stderr,\"[hindstep] holdreturn leg=%zu tick=%llu t=%d pairmin=%.4e\\n\",",
"       hl,(unsigned long long)ticks_,(int)hind_step_t_[hl],(g1<g2?g1:g2));",
"#endif",
"     }}",
])
assert src.count(a) == 1, "completion site"
src = src.replace(a, b)

# 7. THE PIN READ: the carrier's stand-first hold may not arm while the
#    riding swing's certificate stands
a = frag([
"     if(hind_stand_hold(hl)){",
])
b = frag([
"     if(hind_stand_hold(hl)&&!hind_step_refire_[o]){ // the sixth clause: the certified stay's premise is falsified -- the columns resume",
])
assert src.count(a) == 1, "pin arm site"
src = src.replace(a, b)

open(p, "wb").write(src.encode("utf-8"))
print("sixth clause applied,", len(src), "chars")
