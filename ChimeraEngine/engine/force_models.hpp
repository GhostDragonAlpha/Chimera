#pragma once
// Effective continuum models compiled from explicit graph selections.
// SI throughout: mol, not kmol; no implicit extrapolation or nuclear heat model.
#include "../native/viewer3rd/json.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

namespace chimera::forces {
using json = nlohmann::json;
struct Refusal : std::runtime_error {
    explicit Refusal(const std::string& code) : std::runtime_error(code) {}
};
inline void require(bool ok, const char* code) { if (!ok) throw Refusal(code); }
inline double finite(double x) {
    require(std::isfinite(x), "nonfinite_model_number"); return x;
}
inline double number(const json& v) {
    require(v.is_number() && !v.is_boolean(), "invalid_model_number");
    return finite(v.get<double>());
}
inline double positive(double x, const char* code) {
    finite(x); require(x > 0, code); return x;
}
inline double poly(const json& a, double x) {
    double y = 0;
    for (auto it = a.rbegin(); it != a.rend(); ++it) y = y*x + number(*it);
    return finite(y);
}
struct Thermo {
    double cp, h, s, u, cv;
    json to_json() const { return {{"cp",cp},{"h",h},{"s",s},{"u",u},{"cv",cv}}; }
};
using Inventory = std::map<std::string,double>;
struct Mixture {
    double n, mass, T, V, p, U, H, S, Cv;
    json to_json() const {
        return {{"n_mol",n},{"mass_kg",mass},{"temperature_K",T},{"volume_m3",V},
                {"pressure_Pa",p},{"internal_energy_J",U},{"enthalpy_J",H},
                {"entropy_J_K",S},{"Cv_J_K",Cv}};
    }
};
class Library {
    json packet_;
    static const json& find(const json& table, const std::string& key) {
        auto it = table.find(key);
        require(it != table.end(), "model_identity_unknown");
        return *it;
    }
    struct Part { const json* def; double n; };
    std::vector<Part> parts(const Inventory& inventory) const {
        require(!inventory.empty(), "empty_gas_inventory");
        std::vector<Part> out;
        double total = 0;
        for (const auto& item : inventory) {
            finite(item.second);
            require(item.second >= 0, "negative_gas_inventory");
            const auto& d = find(packet_.at("gas_species"), item.first);
            if (item.second > 0) { out.push_back({&d,item.second}); total += item.second; }
        }
        positive(total, "empty_gas_inventory");
        return out;
    }
    Thermo species_def(const json& d, double T) const {
        positive(T, "nonpositive_temperature");
        const auto& r = d.at("temperature_ranges_K");
        require(T >= number(r[0]) && T <= number(r[2]), "gas_temperature_out_of_range");
        const auto& a = d.at("coefficients")[T <= number(r[1]) ? 0 : 1];
        const double a0=number(a[0]), a1=number(a[1]), a2=number(a[2]),
                     a3=number(a[3]), a4=number(a[4]), a5=number(a[5]), a6=number(a[6]);
        const double cp = R()*((((a4*T+a3)*T+a2)*T+a1)*T+a0);
        const double h = R()*T*((((a4*T/5+a3/4)*T+a2/3)*T+a1/2)*T+a0+a5/T);
        const double s = R()*(a0*std::log(T)+(((a4*T/4+a3/3)*T+a2/2)*T+a1)*T+a6);
        Thermo t{finite(cp),finite(h),finite(s),finite(h-R()*T),finite(cp-R())};
        require(t.cv > 0, "nonpositive_heat_capacity");
        return t;
    }
    Mixture mixture_parts(const std::vector<Part>& items, double T, double V) const {
        positive(V, "nonpositive_gas_volume");
        Mixture m{0,0,T,V,0,0,0,0,0};
        for (const auto& item : items) {
            const auto& d = *item.def;
            auto t = species_def(d,T);
            m.n += item.n;
            m.mass += item.n*number(d.at("molar_mass_kg_per_mol"));
            m.U += item.n*t.u; m.H += item.n*t.h; m.Cv += item.n*t.cv;
            // Partial-pressure log avoids underflow in a trace mole fraction.
            const double log_ratio = std::log(item.n)+std::log(R())+std::log(T)-
                                     std::log(V)-std::log(number(d.at("reference_pressure_Pa")));
            m.S += item.n*(t.s - R()*log_ratio);
        }
        m.p = m.n*R()*T/V;
        for (double v : {m.n,m.mass,m.U,m.H,m.Cv,m.S,m.p}) finite(v);
        positive(m.p,"gas_pressure_underflow");
        return m;
    }
    double invert(const Inventory& inv, double target, double V, bool entropy) const {
        finite(target); positive(V,"nonpositive_gas_volume");
        const auto items = parts(inv);
        double low=0, high=std::numeric_limits<double>::infinity(), n=0;
        std::set<double> knots;
        for (const auto& part : items) {
            const auto& r=part.def->at("temperature_ranges_K");
            low=std::max(low,number(r[0])); high=std::min(high,number(r[2]));
            knots.insert(number(r[1])); n += part.n;
        }
        require(low < high,"gas_range_intersection_empty");
        // Residual per mole avoids changing the answer with inventory scale.
        const double goal=finite(target/n);
        auto value = [&](double t) {
            const auto m=mixture_parts(items,t,V);
            return finite((entropy ? m.S : m.U)/n);
        };
        std::vector<double> edges{low};
        for(double t:knots) if(t>low && t<high) edges.push_back(t);
        edges.push_back(high);
        std::vector<double> candidates;
        const double tol=8*std::numeric_limits<double>::epsilon()*std::max(1.0,std::abs(goal));
        for(size_t i=1;i<edges.size();++i) {
            double a=edges[i-1], b=edges[i];
            // A knot belongs to the lower polynomial; its right limit is distinct.
            if(i>1) a=std::nextafter(a,std::numeric_limits<double>::infinity());
            double va=value(a), vb=value(b);
            require(vb>va,"gas_energy_not_monotone");
            if(goal < va-tol || goal > vb+tol) continue;
            double best=std::abs(va-goal)<std::abs(vb-goal)?a:b;
            double err=std::min(std::abs(va-goal),std::abs(vb-goal));
            for(int j=0;j<90;++j) {
                const double mid=a+(b-a)*0.5;
                if(mid==a || mid==b) break;
                const double v=value(mid), e=std::abs(v-goal);
                if(e<err) {best=mid;err=e;}
                if(v<goal) a=mid; else b=mid;
            }
            if(err<=std::max(tol,1e-10)) candidates.push_back(best);
        }
        require(!candidates.empty(),"gas_energy_out_of_range_or_fit_gap");
        require(candidates.size()==1,"gas_fit_inverse_ambiguous");
        return candidates.front();
    }
    void validate() const {
        require(packet_.at("schema")=="chimera.force_models.v1","force_model_schema");
        require(packet_.at("gravity").is_object() && packet_.at("gas_species").is_object() &&
                packet_.at("solid_curves").is_object() && packet_.at("nuclides").is_object(),
                "force_model_tables");
        positive(R(),"invalid_gas_constant");
        const auto& c=packet_.at("constants");
        const double k=number(c.at("Boltzmann constant").at("value_si"));
        const double na=number(c.at("Avogadro constant").at("value_si"));
        require(std::abs(R()-k*na)<=2e-15*R(),"derived_gas_constant_mismatch");
        require(!packet_.at("gas_species").empty(),"empty_species_library");
        for(const auto& d:packet_.at("gas_species")) {
            require(d.at("model")=="NASA7","gas_model_family");
            const auto& r=d.at("temperature_ranges_K");
            require(r.is_array() && r.size()==3 && number(r[0])>0 &&
                    number(r[0])<number(r[1]) && number(r[1])<number(r[2]),"gas_range_shape");
            const auto& a=d.at("coefficients");
            require(a.is_array() && a.size()==2,"gas_coefficient_shape");
            for(const auto& row:a) {
                require(row.is_array() && row.size()==7,"gas_coefficient_shape");
                for(const auto& v:row) number(v);
            }
            positive(number(d.at("reference_pressure_Pa")),"gas_reference_pressure");
            positive(number(d.at("molar_mass_kg_per_mol")),"gas_molar_mass");
        }
        for(const auto& d:packet_.at("gravity")) {
            require(d.at("model")=="point_mass","gravity_model_family");
            positive(number(d.at("mu_m3_s2")),"gravity_parameter");
            require(d.at("mass_scope")=="body" || d.at("mass_scope")=="planetary_system",
                    "gravity_mass_scope");
        }
        for(const auto& d:packet_.at("solid_curves")) {
            const std::string model=d.at("model");
            require(model=="polynomial" || model=="log10_polynomial" ||
                    model=="polynomial_low_constant","solid_model_family");
            const auto& r=d.at("temperature_range_K");
            require(r.is_array() && r.size()==2 && number(r[0])>0 &&
                    number(r[1])>number(r[0]),"solid_range_shape");
            const auto& a=d.at("coefficients");
            require(a.is_array() && !a.empty(),"solid_coefficient_shape");
            for(const auto& v:a) number(v);
            positive(number(d.at("output_scale_to_SI")),"solid_output_scale");
            if(model=="polynomial_low_constant") {
                positive(number(d.at("low_temperature_K")),"solid_low_temperature");
                number(d.at("low_constant"));
            }
        }
    }
public:
    Library()=default;
    explicit Library(const json& p) { load(p); }
    void load(const json& p) {
        Library next; next.packet_=p; next.validate(); packet_=std::move(next.packet_);
    }
    double R() const { return number(packet_.at("R_J_per_mol_K")); }
    const json& packet() const { return packet_; }
    Thermo species(const std::string& name, double T) const {
        return species_def(find(packet_.at("gas_species"),name),T);
    }
    Mixture mixture(const Inventory& n, double T, double V) const {
        return mixture_parts(parts(n),T,V);
    }
    Mixture from_energy(const Inventory& n, double U, double V) const {
        return mixture(n,invert(n,U,V,false),V);
    }
    Mixture from_entropy(const Inventory& n, double S, double V) const {
        return mixture(n,invert(n,S,V,true),V);
    }
    json gravity(const std::string& body, const std::array<double,3>& r, double mass) const {
        finite(mass); require(mass>=0,"negative_test_mass");
        for(double x:r) finite(x);
        const auto& d=find(packet_.at("gravity"),body);
        const double mu=number(d.at("mu_m3_s2"));
        const double norm=positive(std::hypot(r[0],r[1],r[2]),"gravity_center_singularity");
        const double acceleration=finite(-(mu/norm)/norm);
        std::array<double,3> a{},f{};
        for(size_t i=0;i<3;++i) {a[i]=finite(acceleration*(r[i]/norm));f[i]=finite(mass*a[i]);}
        return {{"acceleration_m_s2",a},{"force_N",f},{"potential_energy_J",finite(-mass*(mu/norm))},
                {"mass_scope",d.at("mass_scope")},{"source_record",d.at("record_id")}};
    }
    json solid(const std::string& quantity, double T) const {
        positive(T,"nonpositive_temperature");
        const auto& d=find(packet_.at("solid_curves"),quantity);
        const auto& range=d.at("temperature_range_K");
        require(T>=number(range[0]) && T<=number(range[1]),"solid_temperature_out_of_range");
        const std::string model=d.at("model");
        double y;
        if(model=="polynomial_low_constant" && T<number(d.at("low_temperature_K")))
            y=number(d.at("low_constant"));
        else if(model=="log10_polynomial") y=std::pow(10.0,poly(d.at("coefficients"),std::log10(T)));
        else y=poly(d.at("coefficients"),T);
        y=finite(y*number(d.at("output_scale_to_SI")));
        return {{"value_si",y},{"unit_si",d.at("unit_si")},
                {"curve_fit_error_percent",d.at("curve_fit_relative_error_percent")},
                {"error_semantics",d.at("error_semantics")},{"source_record",d.at("record_id")}};
    }
    json decay(const std::string& isotope, double dt) const {
        finite(dt); require(dt>=0,"negative_decay_time");
        const auto& d=find(packet_.at("nuclides"),isotope);
        require(d.at("level").at("resolved_ground_state")==true,"decay_level_unresolved");
        const auto& hl=d.at("half_life");
        double remaining=1, lost=0;
        if(hl.at("kind")!="stable") {
            require(hl.at("kind")=="estimate" && hl.at("operator")=="",
                    "decay_half_life_not_scalar");
            const double half=positive(number(hl.at("seconds")),"invalid_half_life");
            // dt/half may overflow to infinity: exp(-infinity)=0 is the correct limit.
            const double exponent=-std::log(2.0)*(dt/half);
            remaining=std::exp(exponent); lost=-std::expm1(exponent);
        }
        return {{"remaining_fraction",remaining},{"decayed_fraction",lost},
                {"deposited_heat_J",nullptr},{"daughter_network_complete",false},
                {"interpretation","Expected parent population, not a single-nucleus event"},
                {"source_record",d.at("record_id")}};
    }
    json binding(const std::string& isotope) const {
        const auto& d=find(packet_.at("nuclides"),isotope);
        require(d.at("level").at("resolved_ground_state")==true,"binding_level_unresolved");
        const double keV=number(d.at("binding_energy_per_nucleon_keV"));
        require(keV>=0,"binding_energy_invalid");
        const double e=positive(number(packet_.at("constants").at("elementary charge").at("value_si")),
                                "invalid_elementary_charge");
        const double per=finite(keV*1000*e);
        return {{"binding_J_per_nucleon",per},{"total_binding_J",finite(per*number(d.at("A")))},
                {"available_heat_J",nullptr},{"source_record",d.at("record_id")}};
    }
};
} // namespace chimera::forces
