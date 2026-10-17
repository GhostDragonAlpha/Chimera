// Adapter only: the existing probe core and membrane shader do all GPU physics.
#include "probe_core.hpp"
#include <chrono>
int main(int argc, char** argv) {
  try {
    if(argc!=4) throw std::runtime_error("usage: batch INPUT OUTPUT SHADER");
    std::ifstream in(argv[1]);
    unsigned version=0,nv=0,nf=0;
    if(!(in>>version>>nv>>nf) || version!=1 || nv<3 || nv>32768 || nf<1 || nf>32768)
      throw std::runtime_error("invalid_bounded_input");
    std::vector<F4> pos(nv); std::vector<U4> idx(nf); std::vector<float> gamma(nf);
    for(auto& p:pos) {
      if(!(in>>p.x>>p.y>>p.z) || !std::isfinite(p.x) || !std::isfinite(p.y) || !std::isfinite(p.z))
        throw std::runtime_error("invalid_position"); p.w=0;
    }
    std::vector<std::vector<uint32_t>> adjacency(nv);
    for(unsigned i=0;i<nf;i++) {
      auto& f=idx[i];
      if(!(in>>f.x>>f.y>>f.z>>gamma[i]) || f.x>=nv || f.y>=nv || f.z>=nv || f.x==f.y || f.x==f.z || f.y==f.z || !std::isfinite(gamma[i]) || gamma[i]<0 || gamma[i]>2)
        throw std::runtime_error("invalid_face"); f.w=0;
      adjacency[f.x].push_back(i*3);adjacency[f.y].push_back(i*3+1);adjacency[f.z].push_back(i*3+2);
    }
    std::string trailing; if(in>>trailing) throw std::runtime_error("trailing_input");
    std::vector<uint32_t> off(nv+1),ci;
    for(unsigned i=0;i<nv;i++){off[i]=(uint32_t)ci.size();ci.insert(ci.end(),adjacency[i].begin(),adjacency[i].end());}
    off[nv]=(uint32_t)ci.size();
    std::vector<Face> faces(nf);std::vector<F4> forces(nv);std::vector<uint32_t> valid(nf);float energy=0;
    auto start=std::chrono::steady_clock::now();
    VkProbe gpu(argv[3]);gpu.run_case(pos,idx,gamma,off,ci,faces,forces,valid,energy);
    double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
    for(auto v:valid)if(v!=1)throw std::runtime_error("gpu_invalid_geometry");
    if(!std::isfinite(energy))throw std::runtime_error("gpu_nonfinite_energy");
    for(auto f:forces)if(!std::isfinite(f.x)||!std::isfinite(f.y)||!std::isfinite(f.z))throw std::runtime_error("gpu_nonfinite_force");
    for(auto f:faces)if(!std::isfinite(f.normal_area.w))throw std::runtime_error("gpu_nonfinite_area");
    std::ofstream out(argv[2]);if(!out)throw std::runtime_error("output_open_failed");
    // Device names are escaped rather than assumed to be safe JSON strings.
    std::string device;for(char c:gpu.device_name){if(c=='"'||c=='\\')device+='\\';if((unsigned char)c>=32)device+=c;}
    out<<std::setprecision(12)<<"{\"schema\":\"chimera.ap.gpu_batch.v1\",\"device\":\""<<device<<"\",\"setup_and_dispatch_s\":"<<seconds<<",\"total_energy\":"<<energy<<",\"areas\":[";
    for(unsigned i=0;i<nf;i++){if(i)out<<",";out<<faces[i].normal_area.w;}
    out<<"],\"forces\":[";
    for(unsigned i=0;i<nv;i++){if(i)out<<",";out<<"["<<forces[i].x<<","<<forces[i].y<<","<<forces[i].z<<"]";}
    out<<"]}\n";out.flush();if(!out)throw std::runtime_error("output_write_failed");
    return 0;
  } catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 2;}
}
