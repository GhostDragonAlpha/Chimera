// C1r desk-check: the EXACT find_colon_after + get_bool code from main.cpp,
// exercised against the route bodies the battery will send. Not the engine
// build -- a syntax+logic check of the trap-prone parsing only.
#include <string>
#include <cstdio>
#include <cstddef>

static size_t find_colon_after(const std::string& body, const char* key) {
    std::string needle = std::string("\"") + key + "\"";
    size_t pos = 0;
    while ((pos = body.find(needle, pos)) != std::string::npos) {
        size_t after_quote = pos + needle.size();
        if (after_quote < body.size() && body[after_quote] == '"') {
            pos = after_quote;
            continue;
        }
        size_t after_key = after_quote;
        while (after_key < body.size() && (body[after_key] == ' ' || body[after_key] == '\t')) ++after_key;
        if (after_key < body.size() && body[after_key] == ':') return after_key + 1;
        pos = after_quote;
    }
    return std::string::npos;
}

static bool get_bool(const std::string& body, const char* key, bool def) {
    size_t p = find_colon_after(body, key);
    if (p == std::string::npos) return def;
    while (p < body.size() && (body[p] == ' ' || body[p] == '\t')) ++p;
    if (p >= body.size()) return def;
    if (body[p] == 't') return true;
    if (body[p] == 'f') return false;
    return def;
}

// the route's master-arm law (the literal-substring hazard, verbatim)
static bool route_master(const std::string& body, bool& has_on) {
    has_on = body.find("\"on\"") != std::string::npos;
    return body.find("\"on\":true") != std::string::npos;
}

static int fails = 0;
static void expect(const char* what, bool got, bool want) {
    bool ok = got == want;
    if (!ok) ++fails;
    printf("  [%s] %s: got %s want %s\n", ok ? "PASS" : "FAIL", what,
           got ? "true" : "false", want ? "true" : "false");
}

int main() {
    printf("master-arm law (compact-JSON hazard):\n");
    bool h = false;
    expect("{\"on\":true} arms", route_master("{\"on\":true}", h), true);
    expect("{\"on\":true} has_on", h, true);
    expect("{\"on\": false} (space) DISARMS", route_master("{\"on\": false}", h), false);
    expect("{\"on\": false} has_on", h, true);
    expect("{\"on\":false} disarms", route_master("{\"on\":false}", h), false);
    expect("{} no master", route_master("{}", h) , false);
    expect("{} has_on false", h, false);
    printf("get_bool (stod-on-booleans trap):\n");
    expect("pressure_coupling:false", get_bool("{\"pressure_coupling\":false}", "pressure_coupling", true), false);
    expect("breathing:true", get_bool("{\"breathing\":true}", "breathing", true), true);
    expect("flinch:true spaced", get_bool("{\"flinch\": true}", "flinch", false), true);
    expect("missing key -> default true", get_bool("{}", "startle", true), true);
    expect("malformed value -> default", get_bool("{\"startle\":tru}", "startle", true), true);
    expect("value-shadow: note first", get_bool("{\"note\":\"flinch\",\"flinch\":true}", "flinch", false), true);
    expect("prefix key rejected (flinchy)", get_bool("{\"flinchy\":false,\"flinch\":true}", "flinch", true), true);
    printf("nerve-cut battery body:\n");
    expect("cut: on+cut body master", route_master("{\"on\":true,\"pressure_coupling\":false}", h), true);
    expect("cut: pressure_coupling false", get_bool("{\"on\":true,\"pressure_coupling\":false}", "pressure_coupling", true), false);
    printf(fails ? "DESK-CHECK: %d FAILURES\n" : "DESK-CHECK: all parse cases pass\n", fails);
    return fails ? 1 : 0;
}
