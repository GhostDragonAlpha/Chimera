#pragma once
#include "force_models.hpp"
#include <cstdint>

namespace chimera::forces {
// A sealed, ideal bellows driving a load and an ideal small-deflection beam.
// The graph specifies geometry/limits; source data supplies E(T), gas thermo, GM.
// No contact impact, leak, plasticity, combustion, or scripted pose is implied.
class ThermalActuator {
public:
    struct State {
        uint64_t ticks=0;
        double x=0,v=0,T=0,U=0,Q=0,dissipated=0,dwell=0;
        bool won=false,exhausted=false;
        int iterations=0;
    };
private:
    Library lib_;
    json spec_;
    Inventory inventory_;
    double mass_,area_,V0_,gravity_,spring_,damper_,battery_,power_,h_,initial_energy_;
    State state_,initial_;
    double volume(double x) const { return finite(V0_+area_*x); }
    double stored(const State& s) const {
        return finite(s.U+0.5*mass_*s.v*s.v+mass_*gravity_*s.x+0.5*spring_*s.x*s.x);
    }
    Mixture gas_from_U(double U,double x) const { return lib_.from_energy(inventory_,U,volume(x)); }
    void envelope(const State& s) const {
        const auto& b=spec_.at("operating_envelope");
        require(s.x>=number(b.at("position_min_m")) && s.x<=number(b.at("position_max_m")),
                "actuator_position_out_of_regime");
        require(s.T>=number(b.at("gas_temperature_min_K")) &&
                s.T<=number(b.at("gas_temperature_max_K")),"actuator_temperature_out_of_regime");
        for(double v:{s.x,s.v,s.T,s.U,s.Q,s.dissipated,s.dwell}) finite(v);
    }
    void heat(State& s,double q) const {
        const auto gas=gas_from_U(s.U+q,s.x);
        s.U=gas.U; s.T=gas.T; s.Q+=q;
        envelope(s);
    }
    void mechanical(State& s) const {
        const double x0=s.x, v0=s.v;
        const auto before=lib_.mixture(inventory_,s.T,volume(x0));
        const double entropy=before.S;
        int evaluations=0;
        struct Trial {double x,residual; Mixture gas;};
        auto trial=[&](double x) {
            ++evaluations;
            const auto gas=lib_.from_entropy(inventory_,entropy,volume(x));
            const double dx=x-x0;
            // Fundamental theorem: -(U1-U0)/dx = integral_0^1 p(S,V(x0+t*dx))*A dt.
            // Evaluate that same discrete gradient without subtracting nearly
            // equal energies. Independent 2/4-point quadrature checks its error;
            // the end-to-end energy ledger is checked separately below.
            auto pressure=[&](double t) {
                return lib_.from_entropy(inventory_,entropy,volume(x0+t*dx)).p*area_;
            };
            double force=before.p*area_;
            if(dx!=0) {
                const double f2=.5*(pressure(.2113248654051871)+pressure(.7886751345948129));
                const double f4=.1739274225687269*(pressure(.06943184420297371)+pressure(.9305681557970262))+
                                .3260725774312731*(pressure(.33000947820757187)+pressure(.6699905217924281));
                require(std::abs(f4-f2)<=1e-9*(std::max)(1.0,std::abs(f4)),"actuator_pressure_quadrature_failed");
                force=f4;
            }
            const double residual=(2*mass_/(h_*h_)+damper_/h_)*dx+
                                  mass_*gravity_+spring_*(x0+x)*0.5-force-2*mass_*v0/h_;
            return Trial{x,finite(residual),gas};
        };
        const auto center=trial(x0);
        Trial best=center;
        if(std::abs(center.residual)>1e-11 || std::abs(v0)>1e-14) {
            double radius=(std::max)(1e-7,2*h_*std::abs(v0)+2*h_*h_*std::abs(center.residual)/mass_);
            Trial left=trial(x0-radius),right=trial(x0+radius);
            for(int j=0; j<12 && !(left.residual<=0 && right.residual>=0);++j) {
                radius*=2;
                left=trial(x0-radius);right=trial(x0+radius);
            }
            require(left.residual<=0 && right.residual>=0,"actuator_root_not_bracketed");
            best=std::abs(left.residual)<std::abs(right.residual)?left:right;
            for(int j=0;j<50;++j) {
                // Bracketed secant on a monotone scalar coupled force residual.
                double x=(left.x*right.residual-right.x*left.residual)/
                         (right.residual-left.residual);
                if(!(x>left.x && x<right.x)) x=left.x+(right.x-left.x)*.5;
                Trial mid=trial(x);
                if(std::abs(mid.residual)<std::abs(best.residual)) best=mid;
                if(std::abs(mid.residual)<1e-9) break;
                if(mid.residual<0) left=mid;else right=mid;
                if(right.x-left.x<2e-16) break;
            }
            require(std::abs(best.residual)<1e-7,"actuator_force_solve_failed");
        }
        s.x=best.x;
        s.v=2*(s.x-x0)/h_-v0;
        s.U=best.gas.U;s.T=best.gas.T;
        const double vbar=.5*(v0+s.v);
        s.dissipated+=damper_*h_*vbar*vbar;
        s.iterations=evaluations;
        envelope(s);
    }
public:
    ThermalActuator(const json& packet,const json& spec):lib_(packet),spec_(spec) {
        require(spec_.at("schema")=="chimera.thermal_salvage.v1","actuator_schema");
        const auto& g=spec_.at("geometry");
        mass_=positive(number(g.at("moving_mass_kg")),"actuator_mass");
        area_=positive(number(g.at("piston_area_m2")),"actuator_area");
        V0_=positive(number(g.at("volume0_m3")),"actuator_volume");
        const auto& init=spec_.at("initial");
        const double modulus=number(lib_.solid("young_modulus",
                         number(init.at("beam_temperature_K"))).at("value_si"));
        const double width=positive(number(g.at("beam_width_m")),"beam_width");
        const double thick=positive(number(g.at("beam_thickness_m")),"beam_thickness");
        const double length=positive(number(g.at("beam_length_m")),"beam_length");
        spring_=3*modulus*(width*thick*thick*thick/12)/(length*length*length);
        const auto& grav=spec_.at("gravity");
        const double distance=positive(number(grav.at("center_distance_m")),"gravity_distance");
        const auto field=lib_.gravity(grav.at("naif_body"),{distance,0,0},1);
        require(field.at("mass_scope")=="body","actuator_requires_body_gravity");
        gravity_=-number(field.at("acceleration_m_s2")[0]);
        state_.T=number(init.at("gas_temperature_K"));
        state_.x=number(init.at("position_m"));state_.v=number(init.at("velocity_m_s"));
        require(state_.x==0 && state_.v==0,"actuator_initial_equilibrium_required");
        const std::string name=init.at("gas_species");
        const double n=mass_*gravity_*V0_/(area_*lib_.R()*state_.T);
        inventory_[name]=n;
        const auto gas=lib_.mixture(inventory_,state_.T,V0_);
        state_.U=gas.U;
        const auto thermo=lib_.species(name,state_.T);
        const double gas_k=(thermo.cp/thermo.cv)*gas.p*area_*area_/V0_;
        const double zeta=number(spec_.at("derived").at("zeta"));
        require(zeta>=0,"negative_damping_ratio");
        damper_=2*zeta*std::sqrt(mass_*(spring_+gas_k));
        const auto& controls=spec_.at("controls");
        battery_=positive(number(controls.at("battery_J")),"battery_capacity");
        power_=positive(number(controls.at("max_heater_W")),"heater_rating");
        h_=1/positive(number(spec_.at("time").at("tick_hz")),"actuator_tick_rate");
        envelope(state_);
        initial_=state_;initial_energy_=stored(state_);
    }
    void reset() {state_=initial_;}
    const State& state() const {return state_;}
    double timestep() const {return h_;}
    const Library& library() const {return lib_;}
    void step(double heater_fraction) {
        finite(heater_fraction);
        require(heater_fraction>=0 && heater_fraction<=1,"heater_fraction_out_of_range");
        State next=state_;
        const double requested=(next.won || next.exhausted)?0:heater_fraction*power_*h_;
        const double available=(std::max)(0.0,battery_-next.Q);
        const double q=(std::min)(available,requested);
        heat(next,.5*q);
        mechanical(next);
        heat(next,.5*q);
        next.Q=state_.Q+q; // one inventory debit for the two half-heater transfers
        require(next.Q<=battery_+1e-12,"battery_energy_overdraw");
        if(available<=requested && requested>0) next.exhausted=true;
        const auto& goal=spec_.at("goal");
        if(!next.won && !next.exhausted) {
            if(next.x>=number(goal.at("position_min_m")) && next.x<=number(goal.at("position_max_m")) &&
               std::abs(next.v)<=number(goal.at("max_speed_m_s"))) next.dwell+=h_;
            else next.dwell=0;
            if(next.dwell+1e-12>=number(goal.at("hold_seconds"))) next.won=true;
        }
        ++next.ticks;
        const double balance=stored(next)+next.dissipated-next.Q-initial_energy_;
        require(std::abs(balance)<=1e-8+1e-8*(std::max)(1.0,next.Q),"actuator_energy_balance_failed");
        // Publish together only after all coupled state and accounting checks pass.
        state_=next;
    }
    json status() const {
        const auto& s=state_;auto gas=lib_.mixture(inventory_,s.T,volume(s.x));
        return {{"tick",s.ticks},{"sim_time_s",double(s.ticks)*h_},{"position_m",s.x},
                {"velocity_m_s",s.v},{"gas",gas.to_json()},{"heat_supplied_J",s.Q},
                {"battery_remaining_J",(std::max)(0.0,battery_-s.Q)},{"damper_heat_J",s.dissipated},
                {"kinetic_J",.5*mass_*s.v*s.v},{"gravity_J",mass_*gravity_*s.x},
                {"spring_J",.5*spring_*s.x*s.x},{"gas_work_J",s.Q-(s.U-initial_.U)},
                {"energy_balance_J",stored(s)+s.dissipated-s.Q-initial_energy_},
                {"gas_force_N",gas.p*area_},{"weight_N",mass_*gravity_},
                {"spring_force_N",-spring_*s.x},{"damping_force_N",-damper_*s.v},
                {"dwell_s",s.dwell},{"won",s.won},{"battery_exhausted",s.exhausted},
                {"phase",s.won?"recovered":s.exhausted?"charge_spent":s.Q>0?"operating":"ready"},
                {"solver_evaluations",s.iterations},
                {"derived",{{"gravity_m_s2",gravity_},{"spring_k_N_m",spring_},{"damper_N_s_m",damper_},
                            {"n_mol",gas.n},{"tick_seconds",h_}}},
                {"goal",spec_.at("goal")},{"packet_sha256",lib_.packet().at("packet_sha256")}};
    }
};
}
