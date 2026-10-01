// Unit seam for CoupledDynamics::friction_solve (review F1/F3 fixes,
// 2026-09-17). Standard and third-party headers are included FIRST so the
// #define private public test seam only ever applies to the engine headers.
#include "../../native/viewer3rd/json.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

// Test seam: the engine classes use IMPLICIT default-private access (there is
// no `private:` token in coupled_dynamics.hpp), so the classic
// #define private public macro alone cannot open them; the seam also maps
// class->struct for the engine headers only (all standard and third-party
// headers are already included above, and the chain contains no
// template<class ...> -- verified by grep -- so the substitution is local and
// layout-neutral in this TU).
#define private public
#define class struct
#include "../coupled_dynamics.hpp"
#undef class
#undef private

using namespace chimera::multibody;

static int failures=0,checks=0;
static void ck(bool ok,const char* what){++checks;if(!ok){++failures;std::cerr<<"FAIL "<<what<<"\n";}}
static void near_ck(double a,double b,double tol,const char* what){ck(std::abs(a-b)<=tol,what);}
static Dense add2(Dense a,const Dense& b){for(int i=0;i<2;++i)a[i]+=b[i];return a;}

int main(){try{
 // Decoupled rows with identity mass: every expected number is an exact
 // rational, so 1e-12 is a real margin, not a rounding budget.
 Dense ident{1,0,0,1},row_n{1,0},row_t{0,1},initial{-1,-2};
 Dense force;double n,t;int mode;

 // F1 falsifier, exact rest (slip_sign=0): free tangential acceleration -2
 // means impending slip along -t; friction must OPPOSE it: lambda_t=+0.5.
 // The shipped inverted fallback returned -0.5 here.
 CoupledDynamics::friction_solve(initial,ident,row_n,row_t,0,0,.5,0,force,n,t,mode);
 ck(mode==2,"rest_mode_slide");
 near_ck(n,1,1e-12,"rest_lambda_n");
 near_ck(t,.5,1e-12,"rest_lambda_t_opposes_impending_slip");
 near_ck(inner(row_n,add2(initial,multiply(ident,force))),0,1e-12,"rest_normal_floor_reached");
 near_ck(t,-(-1.)*.5*n,1e-12,"rest_cap_s_minus_one");

 // Moving along +t (slip_sign=+1): same magnitude, sign flips to -0.5.
 CoupledDynamics::friction_solve(initial,ident,row_n,row_t,0,0,.5,1,force,n,t,mode);
 ck(mode==2,"moving_mode_slide");
 near_ck(n,1,1e-12,"moving_lambda_n");
 near_ck(t,-.5,1e-12,"moving_lambda_t_caps_positive_slip");

 // Moving along -t (slip_sign=-1): +0.5 again.
 CoupledDynamics::friction_solve(initial,ident,row_n,row_t,0,0,.5,-1,force,n,t,mode);
 near_ck(t,.5,1e-12,"counter_slip_lambda_t_positive");

 // Stick: the joint solve keeps |t|<=mu*n and reaches BOTH floors.
 Dense stick_initial{-1,-.3};
 CoupledDynamics::friction_solve(stick_initial,ident,row_n,row_t,0,0,.5,0,force,n,t,mode);
 ck(mode==1,"stick_mode");
 near_ck(n,1,1e-12,"stick_lambda_n");
 near_ck(t,.3,1e-12,"stick_lambda_t");
 Dense held=add2(stick_initial,multiply(ident,force));
 near_ck(inner(row_n,held),0,1e-12,"stick_normal_floor");
 near_ck(inner(row_t,held),0,1e-12,"stick_tangential_floor");
 ck(std::abs(t)<=.5*n+1e-12,"stick_inside_cone");

 // Separating (free normal acceleration +1 away from the floor): mode 0,
 // no force, no adhesion.
 CoupledDynamics::friction_solve(Dense{1,0},ident,row_n,row_t,0,0,.5,0,force,n,t,mode);
 ck(mode==0&&n==0&&t==0&&force[0]==0&&force[1]==0,"separating_mode_zero_no_force");

 // Cross-coupled mass M={2,.5;.5,1} (inverse via the engine's own SPD
 // factorization), sliding along +t: the capped slide solve must satisfy KKT
 // stationarity to 1e-12 -- the normal acceleration lands exactly on its
 // floor, the cap t=-s*mu*n is exactly active, and the generalized force is
 // the J^T decomposition lambda_n*row_n + lambda_t*row_t (review F3's
 // construction, now guarded).
 Dense mass{2,.5,.5,1};Dense inverse=inverse_spd(mass,2);
 Dense coupled_initial{-1,-2};
 CoupledDynamics::friction_solve(coupled_initial,inverse,row_n,row_t,0,0,.5,1,force,n,t,mode);
 ck(mode==2,"coupled_mode_slide");
 ck(n>0,"coupled_lambda_n_positive");
 Dense projected=add2(coupled_initial,multiply(inverse,force));
 near_ck(inner(row_n,projected),0,1e-12,"coupled_kkt_normal_stationarity");
 near_ck(t,-.5*n,1e-12,"coupled_kkt_cap_active");
 near_ck(n,1.4,1e-12,"coupled_lambda_n_exact_rational");
 near_ck(t,-.7,1e-12,"coupled_lambda_t_exact_rational");
 near_ck(force[0],n*row_n[0]+t*row_t[0],1e-12,"coupled_force_jt_row0");
 near_ck(force[1],n*row_n[1]+t*row_t[1],1e-12,"coupled_force_jt_row1");

 // Same coupled case at exact rest with rt>0: friction still opposes the
 // impending slip (+t side), so lambda_t=+mu*lambda_n.
 CoupledDynamics::friction_solve(coupled_initial,inverse,row_n,row_t,0,0,.5,0,force,n,t,mode);
 ck(mode==2,"coupled_rest_mode_slide");
 ck(t>0,"coupled_rest_friction_positive");
 near_ck(t,.5*n,1e-12,"coupled_rest_cap_opposes_impending_slip");

 std::cout<<J({{"checks",checks},{"failures",failures},{"pass",failures==0}}).dump(2)<<"\n";
 return failures?1:0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
