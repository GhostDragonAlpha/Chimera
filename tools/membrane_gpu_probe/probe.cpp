// Standalone Vulkan membrane probe.
// Rule-0 membrane: see docs/THE_MASTER_LIST.md §0.
// This numerical GPU gate keeps face evaluation, fixed-order CSR gather, and
// fixed-order energy reduction separate. It uses no floating-point atomics,
// optimizer, engine runtime, HTTP API, window, or visual/DYAD acceptance.

#include <vulkan/vulkan.h>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;
struct F4 { float x,y,z,w; };
struct U4 { uint32_t x,y,z,w; };
struct Face { F4 normal_area, c0, c1, c2; };
struct Params { uint32_t stage, vertex_count, face_count, corner_count; };
static_assert(sizeof(F4)==16 && sizeof(U4)==16 && sizeof(Face)==64 && sizeof(Params)==16);

struct Npy { std::vector<uint8_t> bytes; size_t data=0; std::string descr; };
static Npy load_npy(const fs::path& p) {
    Npy n; std::ifstream f(p, std::ios::binary|std::ios::ate);
    if (!f) throw std::runtime_error("cannot open " + p.string());
    auto sz=static_cast<size_t>(f.tellg()); f.seekg(0); n.bytes.resize(sz); f.read((char*)n.bytes.data(), sz);
    if (sz<12 || std::memcmp(n.bytes.data(), "\x93NUMPY", 6)!=0) throw std::runtime_error("bad npy " + p.string());
    uint8_t major=n.bytes[6]; size_t hlen=major==1 ? *reinterpret_cast<uint16_t*>(n.bytes.data()+8) : *reinterpret_cast<uint32_t*>(n.bytes.data()+8);
    size_t hs=major==1?10:12; std::string h((char*)n.bytes.data()+hs, hlen);
    auto q=h.find("'descr'"); auto a=h.find("'", q+7); auto b=h.find("'", a+1); n.descr=h.substr(a+1,b-a-1);
    n.data=hs+hlen; return n;
}
template<class T> static std::vector<T> values(const fs::path& p) {
    Npy n=load_npy(p); if (n.bytes.size()<n.data || (n.bytes.size()-n.data)%sizeof(T)) throw std::runtime_error("npy size " + p.string());
    std::vector<T> v((n.bytes.size()-n.data)/sizeof(T)); std::memcpy(v.data(), n.bytes.data()+n.data, v.size()*sizeof(T)); return v;
}
static std::vector<char> read_binary(const fs::path& p) { std::ifstream f(p,std::ios::binary|std::ios::ate); if(!f) throw std::runtime_error("shader open failed"); auto n=(size_t)f.tellg(); f.seekg(0); std::vector<char> b(n); f.read(b.data(),n); return b; }
static double max_abs(const std::vector<float>& a, const std::vector<double>& b) { double m=0; for(size_t i=0;i<a.size();++i)m=std::max(m,std::abs((double)a[i]-b[i])); return m; }
static uint32_t ceil_groups(uint32_t n) { return (n+63u)/64u; }

struct VkProbe {
    VkInstance instance=VK_NULL_HANDLE; VkPhysicalDevice physical=VK_NULL_HANDLE; VkDevice device=VK_NULL_HANDLE;
    VkQueue queue=VK_NULL_HANDLE; uint32_t family=0; VkCommandPool pool=VK_NULL_HANDLE; VkPipeline pipeline=VK_NULL_HANDLE;
    VkPipelineLayout layout=VK_NULL_HANDLE; VkDescriptorSetLayout dsl=VK_NULL_HANDLE; VkDescriptorPool dp=VK_NULL_HANDLE;
    VkCommandBuffer cmd=VK_NULL_HANDLE; VkFence fence=VK_NULL_HANDLE;
    VkProbe(const fs::path& shader) {
        VkApplicationInfo ai{VK_STRUCTURE_TYPE_APPLICATION_INFO}; ai.pApplicationName="chimera_membrane_gpu_probe"; ai.apiVersion=VK_API_VERSION_1_1;
        VkInstanceCreateInfo ici{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO}; ici.pApplicationInfo=&ai; check(vkCreateInstance(&ici,nullptr,&instance),"vkCreateInstance");
        uint32_t nd=0; check(vkEnumeratePhysicalDevices(instance,&nd,nullptr),"enumerate devices"); if(!nd) throw std::runtime_error("no Vulkan device");
        std::vector<VkPhysicalDevice> ds(nd); check(vkEnumeratePhysicalDevices(instance,&nd,ds.data()),"enumerate device list");
        for(auto d:ds){uint32_t nq=0;vkGetPhysicalDeviceQueueFamilyProperties(d,&nq,nullptr);std::vector<VkQueueFamilyProperties> q(nq);vkGetPhysicalDeviceQueueFamilyProperties(d,&nq,q.data());for(uint32_t i=0;i<nq;++i)if(q[i].queueFlags&VK_QUEUE_COMPUTE_BIT){physical=d;family=i;break;}if(physical)break;}
        if(!physical) throw std::runtime_error("no compute queue"); VkPhysicalDeviceProperties pp{};vkGetPhysicalDeviceProperties(physical,&pp); device_name=pp.deviceName;
        float pr=1; VkDeviceQueueCreateInfo qci{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};qci.queueFamilyIndex=family;qci.queueCount=1;qci.pQueuePriorities=&pr;
        VkDeviceCreateInfo dci{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};dci.queueCreateInfoCount=1;dci.pQueueCreateInfos=&qci;check(vkCreateDevice(physical,&dci,nullptr,&device),"vkCreateDevice");vkGetDeviceQueue(device,family,0,&queue);
        VkCommandPoolCreateInfo pci{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};pci.queueFamilyIndex=family;pci.flags=VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;check(vkCreateCommandPool(device,&pci,nullptr,&pool),"command pool");
        VkCommandBufferAllocateInfo cai{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};cai.commandPool=pool;cai.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY;cai.commandBufferCount=1;check(vkAllocateCommandBuffers(device,&cai,&cmd),"command buffer");
        VkFenceCreateInfo fci{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};check(vkCreateFence(device,&fci,nullptr,&fence),"fence");
        auto sp=read_binary(shader); VkShaderModuleCreateInfo smi{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};smi.codeSize=sp.size();smi.pCode=(const uint32_t*)sp.data();VkShaderModule sm;check(vkCreateShaderModule(device,&smi,nullptr,&sm),"shader module");
        std::vector<VkDescriptorSetLayoutBinding> bs;for(uint32_t i=0;i<9;++i)bs.push_back({i,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1,VK_SHADER_STAGE_COMPUTE_BIT,nullptr});
        VkDescriptorSetLayoutCreateInfo lci{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};lci.bindingCount=(uint32_t)bs.size();lci.pBindings=bs.data();check(vkCreateDescriptorSetLayout(device,&lci,nullptr,&dsl),"descriptor layout");
        VkPushConstantRange pc{VK_SHADER_STAGE_COMPUTE_BIT,0,sizeof(Params)};VkPipelineLayoutCreateInfo plci{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};plci.setLayoutCount=1;plci.pSetLayouts=&dsl;plci.pushConstantRangeCount=1;plci.pPushConstantRanges=&pc;check(vkCreatePipelineLayout(device,&plci,nullptr,&layout),"pipeline layout");
        VkComputePipelineCreateInfo cp{VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO};cp.stage={VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO};cp.stage.stage=VK_SHADER_STAGE_COMPUTE_BIT;cp.stage.module=sm;cp.stage.pName="main";cp.layout=layout;check(vkCreateComputePipelines(device,VK_NULL_HANDLE,1,&cp,nullptr,&pipeline),"compute pipeline");vkDestroyShaderModule(device,sm,nullptr);
        VkDescriptorPoolSize ps{VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,9};VkDescriptorPoolCreateInfo dpi{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};dpi.flags=VK_DESCRIPTOR_POOL_CREATE_FREE_DESCRIPTOR_SET_BIT;dpi.maxSets=1;dpi.poolSizeCount=1;dpi.pPoolSizes=&ps;check(vkCreateDescriptorPool(device,&dpi,nullptr,&dp),"descriptor pool");
    }
    std::string device_name;
    static void check(VkResult r,const char* what){if(r!=VK_SUCCESS)throw std::runtime_error(std::string(what)+" VkResult="+std::to_string((int)r));}
    ~VkProbe(){if(device){vkDeviceWaitIdle(device);if(fence)vkDestroyFence(device,fence,nullptr);if(cmd){}if(dp)vkDestroyDescriptorPool(device,dp,nullptr);if(pipeline)vkDestroyPipeline(device,pipeline,nullptr);if(layout)vkDestroyPipelineLayout(device,layout,nullptr);if(dsl)vkDestroyDescriptorSetLayout(device,dsl,nullptr);if(pool)vkDestroyCommandPool(device,pool,nullptr);vkDestroyDevice(device,nullptr);}if(instance)vkDestroyInstance(instance,nullptr);}
    struct Buf { VkBuffer b=VK_NULL_HANDLE;VkDeviceMemory m=VK_NULL_HANDLE;void* p=nullptr;VkDeviceSize size=0; };
    uint32_t mem_type(uint32_t bits,VkMemoryPropertyFlags want){VkPhysicalDeviceMemoryProperties mp{};vkGetPhysicalDeviceMemoryProperties(physical,&mp);for(uint32_t i=0;i<mp.memoryTypeCount;++i)if((bits&(1u<<i))&&(mp.memoryTypes[i].propertyFlags&want)==want)return i;throw std::runtime_error("no host coherent memory");}
    Buf buffer(VkDeviceSize size){Buf x;x.size=size;VkBufferCreateInfo ci{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};ci.size=size;ci.usage=VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;check(vkCreateBuffer(device,&ci,nullptr,&x.b),"buffer");VkMemoryRequirements r{};vkGetBufferMemoryRequirements(device,x.b,&r);VkMemoryAllocateInfo ai{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};ai.allocationSize=r.size;ai.memoryTypeIndex=mem_type(r.memoryTypeBits,VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);check(vkAllocateMemory(device,&ai,nullptr,&x.m),"memory");check(vkBindBufferMemory(device,x.b,x.m,0),"bind");check(vkMapMemory(device,x.m,0,size,0,&x.p),"map");std::memset(x.p,0,(size_t)size);return x;}
    void free(Buf& x){if(x.p)vkUnmapMemory(device,x.m);if(x.m)vkFreeMemory(device,x.m,nullptr);if(x.b)vkDestroyBuffer(device,x.b,nullptr);x={};}
    void run_case(const std::vector<F4>& pos,const std::vector<U4>& ind,const std::vector<float>& gam,const std::vector<uint32_t>& off,const std::vector<uint32_t>& ci,std::vector<Face>& faces,std::vector<F4>& vf,std::vector<uint32_t>& valid,float& energy,const std::vector<F4>* changed_pos=nullptr){
        Buf p=buffer(pos.size()*sizeof(F4)),i=buffer(ind.size()*sizeof(U4)),g=buffer(gam.size()*sizeof(float)),o=buffer(off.size()*4),c=buffer(ci.size()*4),f=buffer(faces.size()*sizeof(Face)),v=buffer(vf.size()*sizeof(F4)),e=buffer(4),ok=buffer(valid.size()*4);std::memcpy(p.p,pos.data(),p.size);std::memcpy(i.p,ind.data(),i.size);std::memcpy(g.p,gam.data(),g.size);std::memcpy(o.p,off.data(),o.size);std::memcpy(c.p,ci.data(),c.size);
        VkDescriptorSet ds;VkDescriptorSetAllocateInfo dai{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};dai.descriptorPool=dp;dai.descriptorSetCount=1;dai.pSetLayouts=&dsl;check(vkAllocateDescriptorSets(device,&dai,&ds),"descriptor set");std::vector<Buf*> all={&p,&i,&g,&o,&c,&f,&v,&e,&ok};std::vector<VkDescriptorBufferInfo> bi(9);std::vector<VkWriteDescriptorSet> ws(9);for(uint32_t z=0;z<9;++z){bi[z]={all[z]->b,0,all[z]->size};ws[z]={};ws[z].sType=VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;ws[z].dstSet=ds;ws[z].dstBinding=z;ws[z].descriptorCount=1;ws[z].descriptorType=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;ws[z].pBufferInfo=&bi[z];}vkUpdateDescriptorSets(device,9,ws.data(),0,nullptr);
        VkCommandBufferBeginInfo b{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
        auto bind_begin=[&](){b.flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;check(vkResetCommandBuffer(cmd,0),"reset command buffer");check(vkBeginCommandBuffer(cmd,&b),"begin");vkCmdBindPipeline(cmd,VK_PIPELINE_BIND_POINT_COMPUTE,pipeline);vkCmdBindDescriptorSets(cmd,VK_PIPELINE_BIND_POINT_COMPUTE,layout,0,1,&ds,0,nullptr);};
        auto submit_wait=[&](){check(vkEndCommandBuffer(cmd),"end");VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};si.commandBufferCount=1;si.pCommandBuffers=&cmd;check(vkQueueSubmit(queue,1,&si,fence),"submit");check(vkWaitForFences(device,1,&fence,VK_TRUE,UINT64_MAX),"wait");check(vkResetFences(device,1,&fence),"reset fence");};
        Params q{0,(uint32_t)pos.size(),(uint32_t)ind.size(),(uint32_t)ci.size()};
        auto stage=[&](uint32_t s,uint32_t groups){q.stage=s;vkCmdPushConstants(cmd,layout,VK_SHADER_STAGE_COMPUTE_BIT,0,sizeof(q),&q);vkCmdDispatch(cmd,groups,1,1);VkMemoryBarrier mb{VK_STRUCTURE_TYPE_MEMORY_BARRIER};mb.srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT;mb.dstAccessMask=VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_SHADER_WRITE_BIT;vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0,1,&mb,0,nullptr,0,nullptr);};
        if(!changed_pos){
            bind_begin();stage(0,ceil_groups((uint32_t)ind.size()));stage(1,ceil_groups((uint32_t)pos.size()));stage(2,1);submit_wait();
        } else {
            // Submit face evaluation before mutating the mapped input. This is
            // the actual stale-buffer sequence, not a pre-submit host write.
            bind_begin();stage(0,ceil_groups((uint32_t)ind.size()));submit_wait();
            std::memcpy(p.p,changed_pos->data(),p.size);
            bind_begin();stage(1,ceil_groups((uint32_t)pos.size()));stage(2,1);submit_wait();
        }
        std::memcpy(faces.data(),f.p,faces.size()*sizeof(Face));std::memcpy(vf.data(),v.p,vf.size()*sizeof(F4));std::memcpy(valid.data(),ok.p,valid.size()*4);std::memcpy(&energy,e.p,4);for(auto* x:all)free(*x);vkFreeDescriptorSets(device,dp,1,&ds);
    }
};

static bool same_faces(const std::vector<Face>& a,const std::vector<Face>& b){return a.size()==b.size()&&std::memcmp(a.data(),b.data(),a.size()*sizeof(Face))==0;}
static bool same_f4(const std::vector<F4>& a,const std::vector<F4>& b){return a.size()==b.size()&&std::memcmp(a.data(),b.data(),a.size()*sizeof(F4))==0;}
static bool same_u32(const std::vector<uint32_t>& a,const std::vector<uint32_t>& b){return a==b;}
static bool same_float(float a,float b){return std::memcmp(&a,&b,sizeof(float))==0;}

static bool check_case(const std::string& name,const std::vector<Face>& gpu,const std::vector<F4>& vf,const std::vector<uint32_t>& valid,const std::vector<uint32_t>& offsets,const std::vector<uint32_t>& corner_indices,float energy,const fs::path& fx,const std::string& gamma,double& worst){
    auto area=values<double>(fx/("case_"+gamma+"/areas_f64.npy"));auto normals=values<double>(fx/("case_"+gamma+"/normals_f64.npy"));auto corners=values<double>(fx/("case_"+gamma+"/corner_forces_f64.npy"));auto complete_ref=values<double>(fx/("case_"+gamma+"/vertex_forces_f64.npy"));auto bud=values<double>(fx/("case_"+gamma+"/assembly_budgets_f64.npy"));auto en=values<double>(fx/("case_"+gamma+"/energy_f64.npy"));bool pass=true;double face_worst=0,force_worst=0,asm_worst=0,complete_worst=0; const double complete_budget=2.5e-5;
    bool area_ok=true, normal_ok=true, corner_ok=true, assembly_ok=true, energy_ok=true, zero_ok=true, validity_ok=true;
    for(auto x:valid) if(x!=1) { pass=false; validity_ok=false; }
    for(size_t f=0;f<gpu.size();++f){double da=std::abs(gpu[f].normal_area.w-area[f]);face_worst=std::max(face_worst,da);if(da>1.1e-5){pass=false;area_ok=false;}double gn[3]={gpu[f].normal_area.x,gpu[f].normal_area.y,gpu[f].normal_area.z};for(int j=0;j<3;++j){double d=std::abs(gn[j]-normals[f*3+j]);face_worst=std::max(face_worst,d);if(d>1.1e-5){pass=false;normal_ok=false;}}const F4* gc[3]={&gpu[f].c0,&gpu[f].c1,&gpu[f].c2};for(int k=0;k<3;++k)for(int j=0;j<3;++j){double gf=(&gc[k]->x)[j];double d2=std::abs(gf-corners[f*9+k*3+j]);force_worst=std::max(force_worst,d2);if(d2>4e-6){pass=false;corner_ok=false;}}}
    size_t bad_i=0; int bad_j=0; double bad_d=0,bad_b=0;
    size_t complete_i=0; int complete_j=0; double complete_d=0;
    std::vector<F4> host_asm(vf.size());
    for(size_t v=0;v<vf.size();++v){F4 s{0,0,0,0};for(uint32_t p=offsets[v];p<offsets[v+1];++p){uint32_t flat=corner_indices[p],face=flat/3,slot=flat%3;const F4* c[3]={&gpu[face].c0,&gpu[face].c1,&gpu[face].c2};s.x+=(&c[slot]->x)[0];s.y+=(&c[slot]->x)[1];s.z+=(&c[slot]->x)[2];}host_asm[v]=s;}
    for(size_t i=0;i<vf.size();++i)for(int j=0;j<3;++j){double assembly_d=std::abs((&vf[i].x)[j]-(&host_asm[i].x)[j]);asm_worst=std::max(asm_worst,assembly_d);if(assembly_d>bud[i*3+j]){pass=false;assembly_ok=false;if(assembly_d>bad_d){bad_d=assembly_d;bad_b=bud[i*3+j];bad_i=i;bad_j=j;}}double complete_d_i=std::abs((&vf[i].x)[j]-complete_ref[i*3+j]);complete_worst=std::max(complete_worst,complete_d_i);if(complete_d_i>complete_budget){pass=false;if(complete_d_i>complete_d){complete_d=complete_d_i;complete_i=i;complete_j=j;}}}
    if(std::abs(energy-en[0])>1.1e-5){pass=false;energy_ok=false;}if(gamma=="gamma0" && (energy!=0.0 || force_worst!=0.0)){pass=false;zero_ok=false;}worst=std::max({worst,face_worst,force_worst,asm_worst,complete_worst});    std::cout<<"  "<<name<<" "<<(pass?"PASS":"FAIL")<<" face_max="<<face_worst<<" corner_max="<<force_worst<<" assembly_max="<<asm_worst<<" complete_max="<<complete_worst<<" energy="<<std::setprecision(9)<<energy<<" predicates(area="<<area_ok<<",normal="<<normal_ok<<",corner="<<corner_ok<<",assembly="<<assembly_ok<<",energy="<<energy_ok<<",zero="<<zero_ok<<",validity="<<validity_ok<<")";if(!assembly_ok)std::cout<<" bad_assembly(v="<<bad_i<<",c="<<bad_j<<",diff="<<bad_d<<",budget="<<bad_b<<")";if(complete_d>complete_budget)std::cout<<" bad_complete(v="<<complete_i<<",c="<<complete_j<<",diff="<<complete_d<<",budget="<<complete_budget<<")";std::cout<<"\n";return pass;
}

static bool stale_fixture(VkProbe& vk,const fs::path& root,const std::string& name){
    fs::path fx=root/name;auto p32=values<float>(fx/"geometry/positions_f32.npy");auto ix=values<uint32_t>(fx/"geometry/indices_u32.npy");auto off=values<int64_t>(fx/"adjacency/csr_offsets_i64.npy");auto ci=values<int64_t>(fx/"adjacency/csr_corner_idx_i64.npy");std::vector<F4> pos(p32.size()/3),changed(pos.size());std::vector<U4> ind(ix.size()/3);std::vector<uint32_t> offsets(off.begin(),off.end()),corners(ci.begin(),ci.end());for(size_t i=0;i<pos.size();++i)pos[i]=changed[i]={(float)p32[i*3],(float)p32[i*3+1],(float)p32[i*3+2],0};changed.back().z += 0.03125f;for(size_t i=0;i<ind.size();++i)ind[i]={ix[i*3],ix[i*3+1],ix[i*3+2],0};bool detected=false;for(const char* cg:{"gamma0","gamma1","gamma2"}){auto gam=values<float>(fx/("geometry/"+std::string(cg)+"_f32.npy"));std::vector<Face> stale_f(ind.size()),fresh_f(ind.size());std::vector<F4> stale_v(pos.size()),fresh_v(pos.size());std::vector<uint32_t> stale_ok(ind.size()),fresh_ok(ind.size());float stale_e=0,fresh_e=0;vk.run_case(pos,ind,gam,offsets,corners,stale_f,stale_v,stale_ok,stale_e,&changed);vk.run_case(changed,ind,gam,offsets,corners,fresh_f,fresh_v,fresh_ok,fresh_e);bool differs=!same_faces(stale_f,fresh_f)||!same_f4(stale_v,fresh_v)||!same_u32(stale_ok,fresh_ok)||!same_float(stale_e,fresh_e);std::cout<<"  "<<name<<"/"<<cg<<" stale_reuse="<<(differs?"DETECTED":"NOT_DETECTED")<<" changed_center_z="<<changed.back().z<<"\n";detected|=differs;}return detected;
}

static bool fixture(VkProbe& vk,const fs::path& root,const std::string& name,double& worst){fs::path fx=root/name;auto p32=values<float>(fx/"geometry/positions_f32.npy");auto ix=values<uint32_t>(fx/"geometry/indices_u32.npy");auto off=values<int64_t>(fx/"adjacency/csr_offsets_i64.npy");auto ci=values<int64_t>(fx/"adjacency/csr_corner_idx_i64.npy");std::vector<F4> pos(p32.size()/3);std::vector<U4> ind(ix.size()/3);std::vector<uint32_t> offsets(off.begin(),off.end()),corners(ci.begin(),ci.end());for(size_t i=0;i<pos.size();++i)pos[i]={(float)p32[i*3],(float)p32[i*3+1],(float)p32[i*3+2],0};for(size_t i=0;i<ind.size();++i)ind[i]={ix[i*3],ix[i*3+1],ix[i*3+2],0};bool all=true;for(const char* cg:{"gamma0","gamma1","gamma2"}){auto gam=values<float>(fx/("geometry/"+std::string(cg)+"_f32.npy"));std::vector<Face> faces(ind.size());std::vector<F4> vf(pos.size());std::vector<uint32_t> valid(ind.size());float energy=0;vk.run_case(pos,ind,gam,offsets,corners,faces,vf,valid,energy);for(auto x:valid)if(x!=1)all=false;bool c=check_case(name+"/"+cg,faces,vf,valid,offsets,corners,energy,fx,cg,worst);all&=c;}return all;}

int main(int argc,char**argv){try{fs::path root="docs/evidence/gpu_fixtures",shader=CHIMERA_PROBE_SHADER_PATH;bool stale=false;for(int i=1;i<argc;++i){std::string a=argv[i];if(a=="--fixtures"&&i+1<argc)root=argv[++i];else if(a=="--shader"&&i+1<argc)shader=argv[++i];else if(a=="--stale-reuse")stale=true;}std::cout<<"GPU membrane probe\n";VkProbe vk(shader);std::cout<<"device: "<<vk.device_name<<"\n";if(stale){bool b=stale_fixture(vk,root,"b2"),f=stale_fixture(vk,root,"fan12");std::cout<<"STALE_REUSE_RESULT "<<(b&&f?"DETECTED":"NOT_DETECTED")<<"\n";return b&&f?0:1;}double worst=0;bool b=fixture(vk,root,"b2",worst),f=fixture(vk,root,"fan12",worst);std::cout<<"GPU_RESULT "<<(b&&f?"PASS":"FAIL")<<" worst_abs="<<std::setprecision(9)<<worst<<"\n";return b&&f?0:1;}catch(const std::exception& e){std::cerr<<"GPU_RESULT NOT_TESTED: "<<e.what()<<"\n";return 2;}}
