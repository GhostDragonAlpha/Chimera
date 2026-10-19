// SPDX-License-Identifier: AGPL-3.0-or-later
// Native adapter only: the pinned B2Scene physics source is unchanged.
#include "b2_scene.hpp"
#include <string>
#include <stdexcept>
#include <cmath>
#define API extern "C" __declspec(dllexport)
struct Context { B2Scene scene; std::string response; };
static std::string escaped(const std::string &s) {
  std::string r;
  for (unsigned char c : s) {
    if (c=='"' || c=='\\') r+='\\';
    if(c<32) { r+=' '; continue; } r+=c;
  } return r;
}
static std::string result(const std::string &err) {
  return err.empty()?"{\"ok\":true}":"{\"ok\":false,\"error\":\""+escaped(err)+"\"}";
}
API int cs_abi_version() { return 1; }
API void* cs_create() { try { return new Context; } catch(...) {return nullptr;} }
API void cs_destroy(void* ptr) { delete static_cast<Context*>(ptr); }
API const char* cs_call(void* ptr, const char* operation, const char* payload) {
  if (!ptr || !operation || !payload) return "{\"ok\":false,\"error\":\"invalid bridge arguments\"}";
  Context& c=*static_cast<Context*>(ptr); std::string op(operation),arg(payload),err;
  try {
    if(op=="admit") err=c.scene.admit(arg,"Chimera Studio");
    else if(op=="restore") err=c.scene.restore(arg);
    else if(op=="save") {c.response=c.scene.save_json(); return c.response.c_str();}
    else if(op=="state") {c.response=c.scene.telemetry_json(); return c.response.c_str();}
    else if(op=="parts") {c.response=c.scene.parts_json(); return c.response.c_str();}
    else if(op=="hash") {c.response="{\"hash\":\""+c.scene.state_hash()+"\"}"; return c.response.c_str();}
    else if(op=="inspect") {auto x=c.scene.inspect(arg,err); if(err.empty()){c.response=x;return c.response.c_str();}}
    else if(op=="clear") c.scene.clear();
    else if(op=="pause" || op=="gravity" || op=="support") {
      if(arg!="true" && arg!="false") throw std::runtime_error("boolean required");
      bool on=arg=="true";
      err=op=="pause"?c.scene.set_pause(on):op=="gravity"?c.scene.set_gravity(on):c.scene.set_support(on);
    }
    else if(op=="load") err=c.scene.set_load(arg);
    else if(op=="patch") err=c.scene.patch(arg);
    else if(op=="place") err=c.scene.place(arg);
    else if(op=="remove") err=c.scene.remove_part(arg);
    else if(op=="weld") err=c.scene.set_weld(arg);
    else if(op=="weld_remove") err=c.scene.remove_weld(arg);
    else throw std::runtime_error("unknown bridge operation");
    c.response=result(err);
  } catch(const std::exception& e) {c.response=result(e.what());}
    catch(...) {c.response=result("native exception");}
  return c.response.c_str();
}
API const char* cs_step(void* ptr, int steps) {
  if(!ptr) return "{\"ok\":false,\"error\":\"closed bridge\"}";
  auto& c=*static_cast<Context*>(ptr);
  try {
    if(steps<1 || steps>200) throw std::runtime_error("step batch must be 1..200 native substeps");
    if(!c.scene.active()) throw std::runtime_error("no admitted scene");
    if(c.scene.paused()) throw std::runtime_error("scene paused");
    c.response=result(c.scene.step(steps/4000.0)?"":"native integration failed");
  } catch(const std::exception& e) { c.response=result(e.what()); }
    catch(...) { c.response=result("native step exception"); }
  return c.response.c_str();
}
