#pragma once
#include "thermal_actuator.hpp"
#include <atomic>
#include <chrono>
#include <fstream>
#include <memory>
#include <mutex>
#include <thread>

class GraphThermal {
public:
    using J=chimera::forces::json; using V=std::array<double,3>;
    struct Render {std::vector<float> mesh;std::vector<uint32_t> indices;J state;};
    J bundle;
private:
    std::unique_ptr<chimera::forces::ThermalActuator> sim_;
    mutable std::mutex mutex_;
    std::thread worker_;
    std::atomic<bool> stop_{false};
    double heater_=0,lag_=0;
    bool paused_=false;
    uint64_t revision_=1,render_revision_=0;
    std::string error_;
    std::chrono::steady_clock::time_point lease_{};
    static V sub(V a,V b){return {a[0]-b[0],a[1]-b[1],a[2]-b[2]};}
    static V cross(V a,V b){return {a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]};}
    static double dot(V a,V b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
    J status_locked() const {
        using namespace chimera::forces;
        require(bool(sim_),"thermal_scene_missing");
        J s=sim_->status();
        s["ok"]=error_.empty();s["error"]=error_;s["mode"]="native_thermal_salvage";
        s["scene_revision"]=revision_;s["render_revision"]=render_revision_;
        s["heater_fraction"]=heater_;s["paused"]=paused_;s["clock_lag_s"]=lag_;
        s["graph_hash"]=bundle.at("graph_hash");s["scene_sha256"]=bundle.at("scene_sha256");
        return s;
    }
public:
    ~GraphThermal(){stop();}
    void stop() {
        stop_.store(true);
        if(worker_.joinable())worker_.join();
    }
    bool active() const {return bool(sim_);}
    void load(const std::string& path) {
        using namespace chimera::forces;
        require(!sim_,"thermal_scene_already_loaded");
        std::ifstream f(path);require(bool(f),"thermal_scene_missing");f>>bundle;
        require(bundle.at("schema")=="chimera.thermal_scene.v1","thermal_bundle_schema");
        sim_=std::make_unique<ThermalActuator>(bundle.at("models"),bundle.at("scene"));
    }
    void start() {
        using namespace chimera::forces;
        require(bool(sim_) && !worker_.joinable(),"thermal_worker_state");
        stop_.store(false);
        worker_=std::thread([this] {
            using clock=std::chrono::steady_clock;
            const auto period=std::chrono::duration_cast<clock::duration>(
                                  std::chrono::duration<double>(sim_->timestep()));
            auto deadline=clock::now()+period;
            while(!stop_.load()) {
                std::this_thread::sleep_until(deadline);
                if(stop_.load())break;
                const auto now=clock::now();
                {
                    std::lock_guard<std::mutex> lock(mutex_);
                    lag_=(std::max)(0.,std::chrono::duration<double>(now-deadline).count());
                    if(now>=lease_)heater_=0;
                    if(!paused_ && error_.empty()) {
                        try {sim_->step(heater_);++revision_;}
                        catch(const std::exception& e){error_=e.what();heater_=0;}
                    }
                }
                deadline+=period; // no physics ticks dropped to disguise frame delay
            }
        });
    }
    J status() const {std::lock_guard<std::mutex> lock(mutex_);return status_locked();}
    void rendered(uint64_t revision) {
        std::lock_guard<std::mutex> lock(mutex_);render_revision_=revision;
    }
    J control(const J& q) {
        using namespace chimera::forces;
        require(q.is_object() && !q.empty(),"thermal_control_object");
        for(auto it=q.begin();it!=q.end();++it)
            require(it.key()=="heater_fraction" || it.key()=="reset" || it.key()=="paused","unknown_thermal_control");
        if(q.contains("reset"))require(q.at("reset").is_boolean(),"reset_boolean_required");
        if(q.contains("paused"))require(q.at("paused").is_boolean(),"paused_boolean_required");
        if(q.contains("heater_fraction")) {
            const double h=number(q.at("heater_fraction"));
            require(h>=0 && h<=1,"heater_fraction_out_of_range");
        }
        const bool reset=q.value("reset",false);
        require(!(reset && q.contains("heater_fraction")),"reset_heater_conflict");
        std::lock_guard<std::mutex> lock(mutex_);
        require(bool(sim_),"thermal_scene_missing");
        if(reset){sim_->reset();heater_=0;error_.clear();paused_=false;++revision_;}
        if(q.contains("paused")) {paused_=q.at("paused").get<bool>();if(paused_)heater_=0;}
        if(q.contains("heater_fraction")) {
            heater_=q.at("heater_fraction").get<double>();
            if(paused_ || !error_.empty())heater_=0;
            lease_=std::chrono::steady_clock::now()+std::chrono::milliseconds(500);
        }
        return status_locked();
    }
    static std::string base64(const std::vector<uint8_t>& data) {
        static const char chars[]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        std::string out;out.reserve((data.size()+2)/3*4);
        for(size_t i=0;i<data.size();i+=3) {
            unsigned v=unsigned(data[i])<<16;
            if(i+1<data.size())v|=unsigned(data[i+1])<<8;
            if(i+2<data.size())v|=unsigned(data[i+2]);
            out+=chars[(v>>18)&63];out+=chars[(v>>12)&63];
            out+=i+1<data.size()?chars[(v>>6)&63]:'=';
            out+=i+2<data.size()?chars[v&63]:'=';
        }
        return out;
    }
    Render render() const {
        using namespace chimera::forces;
        Render out;out.state=status();const double x=number(out.state.at("position_m"));
        const auto& scene=bundle.at("scene");const auto& geometry=scene.at("geometry");
        const double A=number(geometry.at("piston_area_m2"));
        const double H=number(geometry.at("volume0_m3"))/A+x;
        const double scale=number(bundle.at("render_m_to_units"));
        double signed_bellows_volume=0;
        auto triangle=[&](V a,V b,V c,V color,bool chamber=false) {
            V n=cross(sub(b,a),sub(c,a));const double norm=std::sqrt(dot(n,n));
            require(norm>0,"thermal_render_degenerate_triangle");
            if(chamber)signed_bellows_volume+=dot(a,cross(b,c))/6;
            for(const auto& v:{a,b,c}) {
                out.indices.push_back(uint32_t(out.mesh.size()/9));
                for(double p:v)out.mesh.push_back(float(p*scale));
                for(double p:n)out.mesh.push_back(float(p/norm));
                for(double p:color)out.mesh.push_back(float(p));
            }
        };
        auto quad=[&](V a,V b,V c,V d,V color,bool chamber=false) {
            triangle(a,b,c,color,chamber);triangle(a,c,d,color,chamber);
        };
        auto box=[&](V lo,V hi,V color) {
            V a{lo[0],lo[1],lo[2]},b{hi[0],lo[1],lo[2]},c{hi[0],hi[1],lo[2]},d{lo[0],hi[1],lo[2]};
            V e{lo[0],lo[1],hi[2]},f{hi[0],lo[1],hi[2]},g{hi[0],hi[1],hi[2]},h{lo[0],hi[1],hi[2]};
            quad(a,d,c,b,color);quad(e,f,g,h,color);quad(a,e,h,d,color);
            quad(b,c,g,f,color);quad(a,b,f,e,color);quad(d,h,g,c,color);
        };
        const V base{.12,.17,.21},metal{.46,.57,.62},load{.72,.57,.29},cyan{.15,.63,.72};
        box({-.34,0,-.09},{.08,.012,.09},base);
        box({-.325,.012,-.045},{-.29,.145,.045},metal);
        // Native bellows geometry has exactly the state's chamber volume:
        // polygonal frustum volumes give a normalization for corrugation radii.
        const int count=48,rings=17;const double pi=3.14159265358979323846;
        double shape[rings],average=0;
        for(int j=0;j<rings;++j)shape[j]=(j%2==0)?1:.83;
        for(int j=0;j<rings-1;++j)
            average+=(shape[j]*shape[j]+shape[j]*shape[j+1]+shape[j+1]*shape[j+1])/(3*(rings-1));
        const double radius=std::sqrt(A/(.5*count*std::sin(2*pi/count)*average));
        const double bottom=.025;
        auto ring=[&](int j,int i) {
            double angle=2*pi*i/count;
            return V{radius*shape[j]*std::cos(angle),bottom+H*j/(rings-1),
                     radius*shape[j]*std::sin(angle)};
        };
        const double heat=(std::min)(1.,(std::max)(0.,(number(out.state.at("gas").at("temperature_K"))-320)/300));
        V bellows{.13+.45*heat,.52-.13*heat,.65-.40*heat};
        for(int j=0;j<rings-1;++j) for(int i=0;i<count;++i)
            quad(ring(j,i),ring(j+1,i),ring(j+1,(i+1)%count),ring(j,(i+1)%count),bellows,true);
        for(int i=0;i<count;++i) {
            triangle({0,bottom,0},ring(0,i),ring(0,(i+1)%count),bellows,true);
            triangle({0,bottom+H,0},ring(rings-1,(i+1)%count),ring(rings-1,i),bellows,true);
        }
        const double expected=number(out.state.at("gas").at("volume_m3"));
        require(std::abs(signed_bellows_volume-expected)<=1e-10*expected,"thermal_render_volume_mismatch");
        const double top=bottom+H;
        box({-.044,top,-.044},{.044,top+.012,.044},load);
        box({-.033,.012,-.033},{.033,bottom,.033},metal);
        // Small-deflection Euler-Bernoulli cantilever shape matches k=3EI/L^3.
        const double L=number(geometry.at("beam_length_m")),t=number(geometry.at("beam_thickness_m")),
                     width=number(geometry.at("beam_width_m"));
        auto beam=[&](double s,double dy,double z) {
            const double w=x*s*s*(3*L-s)/(2*L*L*L);
            return V{s-L,bottom+number(geometry.at("volume0_m3"))/A+w+dy,z};
        };
        for(int i=0;i<32;++i) {
            double a=L*i/32,b=L*(i+1)/32;
            quad(beam(a,0,-width/2),beam(a,0,width/2),beam(b,0,width/2),beam(b,0,-width/2),cyan);
            quad(beam(a,t,width/2),beam(a,t,-width/2),beam(b,t,-width/2),beam(b,t,width/2),cyan);
            quad(beam(a,0,-width/2),beam(b,0,-width/2),beam(b,t,-width/2),beam(a,t,-width/2),cyan);
            quad(beam(a,0,width/2),beam(a,t,width/2),beam(b,t,width/2),beam(b,0,width/2),cyan);
        }
        // Fixed goal markers in physical space, not success decoration.
        const double rest_top=bottom+number(geometry.at("volume0_m3"))/A;
        for(const char* key:{"position_min_m","position_max_m"}) {
            double y=rest_top+number(scene.at("goal").at(key));
            box({.047,y-.0005,-.035},{.065,y+.0005,.035},{.34,.78,.65});
        }
        out.state["mesh_triangles"]=out.indices.size()/3;
        out.state["render_chamber_volume_m3"]=signed_bellows_volume;
        out.state["render_m_to_units"]=scale;
        return out;
    }
};
