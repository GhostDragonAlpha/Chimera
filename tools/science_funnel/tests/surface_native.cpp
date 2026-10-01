#include "../../../ChimeraEngine/engine/graph_surface.hpp"
#include <iostream>
int main(int argc,char**argv){
  try{
    GraphSurface s;s.load(argv[1]);GraphSurface::J checks=GraphSurface::J::array();
    auto check=[&](std::string name,bool ok,double value){checks.push_back({{"test",name},{"pass",ok},{"value",value}});if(!ok){std::cerr<<checks.dump(2)<<std::endl;throw std::runtime_error(name);}};
    s.force=0;
    for(size_t i=0;i<s.h.size();++i)if(!s.pinned[i])s.h[i]=-0.0008*std::exp(-GraphSurface::dot(s.rest[i],s.rest[i])/0.00004);
    std::vector<double> g;double e=s.eval(s.h,&g),worst=0;
    for(int i:{46,110,200,220,310,370}){
        auto plus=s.h,minus=s.h;plus[i]+=1e-8;minus[i]-=1e-8;
        double fd=(s.eval(plus)-s.eval(minus))/2e-8;
        worst=(std::max)(worst,std::abs(fd-g[i])/(std::max)(1e-8,std::abs(g[i])));
    }
    check("energy_derivative",worst<1e-5,worst);
    s.gamma*=2;std::vector<double> g2;double e2=s.eval(s.h,&g2);
    check("fixed_geometry_gamma_energy",std::abs(e2/e-2)<1e-12,e2/e);
    check("fixed_geometry_gamma_force",std::abs(g2[220]/g[220]-2)<1e-12,g2[220]/g[220]);
    double depths[2]={};
    for(int m=0;m<2;++m){
      s.control({{"material",m?"Ethanol":"Water"},{"reset",true}});
      s.control({{"force_N",0.00025}});
      for(int k=0;k<50&&!s.converged;++k)s.step();
      check(m?"ethanol_settles":"water_settles",s.converged&&s.error.empty(),s.residual);
      check(m?"ethanol_force_balance":"water_force_balance",std::abs(s.reaction-s.force)<1e-7,std::abs(s.reaction-s.force));
      depths[m]=s.status()["depth_m"];
      double pinmax=0;for(size_t i=0;i<s.h.size();++i)if(s.pinned[i])pinmax=(std::max)(pinmax,std::abs(s.h[i]));
      check("pinned_boundary",pinmax==0,pinmax);
    }
    check("material_changes_deformation",depths[1]>depths[0]*2,depths[1]/depths[0]);
    s.control({{"force_N",s.spec.at("max_force_N")}});
    for(int k=0;k<50&&!s.converged;++k)s.step();
    check("advertised_max_load_settles",s.converged&&s.error.empty()&&std::abs(s.reaction-s.force)<1e-7,s.residual);
    auto saved=s.status();bool refused=false;try{s.control({{"force_N",-1.0}});}catch(...){refused=true;}
    check("bad_control_is_atomic",refused&&s.status()==saved,refused?1:0);
    s.control({{"force_N",0.0}});for(int k=0;k<50&&!s.converged;++k)s.step();
    double release=s.status()["depth_m"];check("release_returns_flat",s.converged&&std::abs(release)<1e-7,release);
    auto mesh=s.mesh();auto pos=s.positions();double render_error=0;
    for(size_t i=0;i<pos.size();++i)for(int j=0;j<3;++j)render_error=(std::max)(render_error,std::abs((mesh[i*9+j]-s.translation[j])/s.scale-pos[i][j]));
    check("render_uses_physical_positions",render_error<2e-9,render_error);
    std::cout<<GraphSurface::J{{"checks",checks},{"water_depth_m",depths[0]},{"ethanol_depth_m",depths[1]}}.dump(2)<<std::endl;
    return 0;
  }catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}
}

