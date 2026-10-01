#include "../../../ChimeraEngine/engine/thermal_actuator.hpp"
#include <chrono>
#include <fstream>
#include <iostream>
#include <sstream>
using namespace chimera::forces;
int main(int argc,char**argv) {
    try {
        require(argc==2,"usage_thermal_native_scene");
        std::ifstream input(argv[1]);require(bool(input),"scene_missing");
        json bundle;input>>bundle;ThermalActuator sim(bundle.at("models"),bundle.at("scene"));
        std::string line;
        while(std::getline(std::cin,line)) {
            json before=sim.status();
            try {
                const auto q=json::parse(line);
                if(q.value("reset",false)) sim.reset();
                if(q.contains("heater")) number(q.at("heater"));
                const int count=q.value("steps",0),sample=q.value("sample_every",30);
                require(count>=0 && count<=30000 && sample>0,"step_count");
                const double heater=q.value("heater",0.);
                std::vector<double> ms;json samples=json::array();
                for(int i=0;i<count;++i) {
                    before=sim.status();
                    const auto t0=std::chrono::steady_clock::now();
                    sim.step(heater);
                    const auto t1=std::chrono::steady_clock::now();
                    ms.push_back(std::chrono::duration<double,std::milli>(t1-t0).count());
                    if((i+1)%sample==0) samples.push_back(sim.status());
                }
                std::sort(ms.begin(),ms.end());
                auto percentile=[&](double q){return ms.empty()?0:ms[std::min(ms.size()-1,size_t(q*ms.size()))];};
                std::cout<<json({{"ok",true},{"state",sim.status()},{"samples",samples},
                    {"timing_ms",{{"median",percentile(.5)},{"p95",percentile(.95)},{"p99",percentile(.99)}}}}).dump()<<'\n';
            } catch(const std::exception& e) {
                std::cout<<json({{"ok",false},{"error",e.what()},{"state",sim.status()},
                                {"failed_step_unchanged",before==sim.status()}}).dump()<<'\n';
            }
        }
        return 0;
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 2;}
}
