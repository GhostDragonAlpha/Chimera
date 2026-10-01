#include "../../../ChimeraEngine/engine/force_models.hpp"
#include <fstream>
#include <iostream>
#include <sstream>
using namespace chimera::forces;
json strict_parse(const std::string& text) {
    require(text.size()<=4*1024*1024,"request_size_limit");
    std::vector<std::set<std::string>> keys;
    auto callback=[&](int, json::parse_event_t event, json& value) {
        if(event==json::parse_event_t::object_start) keys.emplace_back();
        if(event==json::parse_event_t::key)
            require(keys.back().insert(value.get<std::string>()).second,"duplicate_json_key");
        if(event==json::parse_event_t::object_end) keys.pop_back();
        return true;
    };
    return json::parse(text,callback);
}
Inventory inventory(const json& j) {
    require(j.is_object(),"gas_inventory_object");
    Inventory out;
    for(auto it=j.begin();it!=j.end();++it) out.emplace(it.key(),number(it.value()));
    return out;
}
json query(Library& lib,const json& q) {
    const std::string op=q.at("op");
    if(op=="species") return lib.species(q.at("species"),number(q.at("T"))).to_json();
    if(op=="mixture") return lib.mixture(inventory(q.at("n")),number(q.at("T")),
                                       number(q.at("V"))).to_json();
    if(op=="energy") return lib.from_energy(inventory(q.at("n")),number(q.at("U")),
                                           number(q.at("V"))).to_json();
    if(op=="entropy") return lib.from_entropy(inventory(q.at("n")),number(q.at("S")),
                                             number(q.at("V"))).to_json();
    if(op=="gravity") {
        const auto& p=q.at("r");
        require(p.is_array() && p.size()==3,"position_shape");
        return lib.gravity(q.at("body"),{number(p[0]),number(p[1]),number(p[2])},number(q.at("mass")));
    }
    if(op=="solid") return lib.solid(q.at("quantity"),number(q.at("T")));
    if(op=="decay") return lib.decay(q.at("isotope"),number(q.at("dt")));
    if(op=="binding") return lib.binding(q.at("isotope"));
    if(op=="reload") {lib.load(q.at("packet"));return {{"loaded",true}};}
    throw Refusal("operation_unknown");
}
int main(int argc,char** argv) {
    try {
        require(argc==2,"usage_force_probe_packet");
        std::ifstream input(argv[1],std::ios::binary);
        require(bool(input),"packet_missing");
        std::ostringstream bytes;bytes<<input.rdbuf();
        Library lib(strict_parse(bytes.str()));
        std::string line;
        while(std::getline(std::cin,line)) {
            try {std::cout<<json({{"ok",true},{"result",query(lib,strict_parse(line))}}).dump()<<'\n';}
            catch(const Refusal& e) {std::cout<<json({{"ok",false},{"error",e.what()}}).dump()<<'\n';}
            catch(const std::exception& e) {
                std::cout<<json({{"ok",false},{"error","invalid_model_request"},{"detail",e.what()}}).dump()<<'\n';
            }
        }
        return 0;
    } catch(const std::exception& e) {
        std::cerr<<json({{"ok",false},{"error",e.what()}}).dump()<<'\n';
        return 2;
    }
}
