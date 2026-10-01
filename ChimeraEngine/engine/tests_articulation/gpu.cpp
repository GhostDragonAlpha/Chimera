// Executes the actual production joints.comp kernel; no window or scene replacement.
#include "../joint_binding.hpp"
#include "../../native/viewer3rd/json.hpp"
#include <vulkan/vulkan.h>
#include <array>
#include <fstream>
#include <iostream>
using namespace chimera::articulation;
using json=nlohmann::json;
void vkcheck(VkResult r){if(r!=VK_SUCCESS)throw std::runtime_error("Vulkan failure "+std::to_string(r));}
std::vector<uint8_t> read(const char* path){std::ifstream f(path,std::ios::binary);if(!f)throw std::runtime_error("missing input");return {std::istreambuf_iterator<char>(f),{}};}
uint32_t word(const std::vector<uint8_t>& a,size_t i){uint32_t n;std::memcpy(&n,a.data()+i,4);return n;}
template<class T> std::vector<uint8_t> bytes(const std::vector<T>& v){std::vector<uint8_t>b(v.size()*sizeof(T));if(!v.empty())std::memcpy(b.data(),v.data(),b.size());return b;}
struct GPU {
    VkInstance instance{};VkPhysicalDevice physical{};VkDevice device{};VkQueue queue{};
    VkDescriptorSetLayout layout{};VkPipelineLayout pl{};VkPipeline pipeline{};VkCommandPool commands{};
    VkPhysicalDeviceMemoryProperties memory{};std::string name;uint32_t family=0;
    GPU(const char* shader){
        VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};app.pApplicationName="Chimera articulation check";app.apiVersion=VK_API_VERSION_1_1;
        VkInstanceCreateInfo ic{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};ic.pApplicationInfo=&app;vkcheck(vkCreateInstance(&ic,nullptr,&instance));
        uint32_t count=0;vkcheck(vkEnumeratePhysicalDevices(instance,&count,nullptr));
        std::vector<VkPhysicalDevice> devices(count);vkcheck(vkEnumeratePhysicalDevices(instance,&count,devices.data()));
        for(auto d:devices){VkPhysicalDeviceProperties p;vkGetPhysicalDeviceProperties(d,&p);if(!physical||p.deviceType==VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU){physical=d;name=p.deviceName;}}
        if(!physical)throw std::runtime_error("no Vulkan device");
        vkGetPhysicalDeviceQueueFamilyProperties(physical,&count,nullptr);std::vector<VkQueueFamilyProperties> qs(count);
        vkGetPhysicalDeviceQueueFamilyProperties(physical,&count,qs.data());bool found=false;
        for(uint32_t i=0;i<count;++i)if(qs[i].queueFlags&VK_QUEUE_COMPUTE_BIT){family=i;found=true;break;}
        if(!found)throw std::runtime_error("no compute queue");
        float priority=1;VkDeviceQueueCreateInfo qc{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};qc.queueFamilyIndex=family;qc.queueCount=1;qc.pQueuePriorities=&priority;
        VkDeviceCreateInfo dc{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};dc.queueCreateInfoCount=1;dc.pQueueCreateInfos=&qc;vkcheck(vkCreateDevice(physical,&dc,nullptr,&device));
        vkGetDeviceQueue(device,family,0,&queue);vkGetPhysicalDeviceMemoryProperties(physical,&memory);
        std::array<VkDescriptorSetLayoutBinding,12> binds{};
        for(uint32_t i=0;i<12;++i)binds[i]={i,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1,VK_SHADER_STAGE_COMPUTE_BIT,nullptr};
        VkDescriptorSetLayoutCreateInfo lc{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};lc.bindingCount=12;lc.pBindings=binds.data();vkcheck(vkCreateDescriptorSetLayout(device,&lc,nullptr,&layout));
        VkPushConstantRange range{VK_SHADER_STAGE_COMPUTE_BIT,0,32};VkPipelineLayoutCreateInfo pc{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
        pc.setLayoutCount=1;pc.pSetLayouts=&layout;pc.pushConstantRangeCount=1;pc.pPushConstantRanges=&range;vkcheck(vkCreatePipelineLayout(device,&pc,nullptr,&pl));
        auto raw=read(shader);if(raw.size()%4)throw std::runtime_error("bad SPIR-V");std::vector<uint32_t> code(raw.size()/4);std::memcpy(code.data(),raw.data(),raw.size());
        VkShaderModuleCreateInfo sc{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};sc.codeSize=raw.size();sc.pCode=code.data();VkShaderModule module{};vkcheck(vkCreateShaderModule(device,&sc,nullptr,&module));
        VkComputePipelineCreateInfo cp{VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO};cp.layout=pl;cp.stage.sType=VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
        cp.stage.stage=VK_SHADER_STAGE_COMPUTE_BIT;cp.stage.module=module;cp.stage.pName="main";auto result=vkCreateComputePipelines(device,VK_NULL_HANDLE,1,&cp,nullptr,&pipeline);vkDestroyShaderModule(device,module,nullptr);vkcheck(result);
        VkCommandPoolCreateInfo pool{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};pool.queueFamilyIndex=family;vkcheck(vkCreateCommandPool(device,&pool,nullptr,&commands));
    }
    ~GPU(){if(device){vkDeviceWaitIdle(device);vkDestroyCommandPool(device,commands,nullptr);vkDestroyPipeline(device,pipeline,nullptr);vkDestroyPipelineLayout(device,pl,nullptr);vkDestroyDescriptorSetLayout(device,layout,nullptr);vkDestroyDevice(device,nullptr);}if(instance)vkDestroyInstance(instance,nullptr);}
    std::vector<float> run(std::array<std::vector<uint8_t>,12> input,uint32_t n,uint32_t nj){
        struct Buffer{VkBuffer buffer{};VkDeviceMemory memory{};void* mapped{};};std::array<Buffer,12>b{};
        std::array<VkDescriptorBufferInfo,12> bi{};
        for(uint32_t i=0;i<12;++i){
            if(input[i].size()<4)input[i].resize(4);
            VkBufferCreateInfo bc{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};bc.size=input[i].size();bc.usage=VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;bc.sharingMode=VK_SHARING_MODE_EXCLUSIVE;
            vkcheck(vkCreateBuffer(device,&bc,nullptr,&b[i].buffer));VkMemoryRequirements req;vkGetBufferMemoryRequirements(device,b[i].buffer,&req);
            uint32_t type=memory.memoryTypeCount;
            for(uint32_t t=0;t<memory.memoryTypeCount;++t)if((req.memoryTypeBits&(1u<<t))&&
                (memory.memoryTypes[t].propertyFlags&(VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT))==(VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)){type=t;break;}
            if(type==memory.memoryTypeCount)throw std::runtime_error("coherent test buffer unavailable");
            VkMemoryAllocateInfo ai{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};ai.allocationSize=req.size;ai.memoryTypeIndex=type;vkcheck(vkAllocateMemory(device,&ai,nullptr,&b[i].memory));
            vkcheck(vkBindBufferMemory(device,b[i].buffer,b[i].memory,0));vkcheck(vkMapMemory(device,b[i].memory,0,VK_WHOLE_SIZE,0,&b[i].mapped));
            std::memcpy(b[i].mapped,input[i].data(),input[i].size());bi[i]={b[i].buffer,0,input[i].size()};
        }
        VkDescriptorPoolSize size{VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,12};VkDescriptorPoolCreateInfo dp{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};dp.maxSets=1;dp.poolSizeCount=1;dp.pPoolSizes=&size;
        VkDescriptorPool pool{};vkcheck(vkCreateDescriptorPool(device,&dp,nullptr,&pool));VkDescriptorSetAllocateInfo da{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};da.descriptorPool=pool;da.descriptorSetCount=1;da.pSetLayouts=&layout;
        VkDescriptorSet set{};vkcheck(vkAllocateDescriptorSets(device,&da,&set));std::array<VkWriteDescriptorSet,12>w{};
        for(uint32_t i=0;i<12;++i){w[i].sType=VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;w[i].dstSet=set;w[i].dstBinding=i;w[i].descriptorCount=1;w[i].descriptorType=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;w[i].pBufferInfo=&bi[i];}
        vkUpdateDescriptorSets(device,12,w.data(),0,nullptr);
        VkCommandBufferAllocateInfo ca{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};ca.commandPool=commands;ca.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY;ca.commandBufferCount=1;
        VkCommandBuffer cmd{};vkcheck(vkAllocateCommandBuffers(device,&ca,&cmd));VkCommandBufferBeginInfo begin{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};vkcheck(vkBeginCommandBuffer(cmd,&begin));
        vkCmdBindPipeline(cmd,VK_PIPELINE_BIND_POINT_COMPUTE,pipeline);vkCmdBindDescriptorSets(cmd,VK_PIPELINE_BIND_POINT_COMPUTE,pl,0,1,&set,0,nullptr);
        struct Push{uint32_t n,nj;int32_t paint;uint32_t flags;float k,y,iters,pad;} push{n,nj,-1,0,0,0,0,0};
        vkCmdPushConstants(cmd,pl,VK_SHADER_STAGE_COMPUTE_BIT,0,32,&push);vkCmdDispatch(cmd,(n+255)/256,1,1);
        VkMemoryBarrier mb{VK_STRUCTURE_TYPE_MEMORY_BARRIER};mb.srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT;mb.dstAccessMask=VK_ACCESS_HOST_READ_BIT;
        vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_PIPELINE_STAGE_HOST_BIT,0,1,&mb,0,nullptr,0,nullptr);vkcheck(vkEndCommandBuffer(cmd));
        VkFenceCreateInfo fc{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};VkFence fence{};vkcheck(vkCreateFence(device,&fc,nullptr,&fence));
        VkSubmitInfo submit{VK_STRUCTURE_TYPE_SUBMIT_INFO};submit.commandBufferCount=1;submit.pCommandBuffers=&cmd;vkcheck(vkQueueSubmit(queue,1,&submit,fence));
        vkcheck(vkWaitForFences(device,1,&fence,VK_TRUE,10'000'000'000ull));
        std::vector<float> out(n*9ull);std::memcpy(out.data(),b[4].mapped,out.size()*4);
        vkDestroyFence(device,fence,nullptr);vkFreeCommandBuffers(device,commands,1,&cmd);vkDestroyDescriptorPool(device,pool,nullptr);
        for(auto& x:b){vkUnmapMemory(device,x.memory);vkDestroyBuffer(device,x.buffer,nullptr);vkFreeMemory(device,x.memory,nullptr);}return out;
    }
};
// Independent oracle: rotate each point about the leaf first, then walk upward.
std::array<double,3> oracle(std::array<double,3> p,int j,const JointBinding& b,const std::vector<float>& angles,bool position){
    for(;j>=0;j=b.parents[j]){
        std::array<double,3>a{},q{},pivot{};
        for(int k=0;k<3;++k){a[k]=b.axes[3*j+k];pivot[k]=position?b.pivots[3*j+k]:0.;q[k]=p[k]-pivot[k];}
        double c=std::cos(double(angles[j])),s=std::sin(double(angles[j])),dot=a[0]*q[0]+a[1]*q[1]+a[2]*q[2];
        for(int k=0;k<3;++k)p[k]=pivot[k]+q[k]*c+a[k]*dot*(1-c)+s*(a[(k+1)%3]*q[(k+2)%3]-a[(k+2)%3]*q[(k+1)%3]);
    }return p;
}
int main(int argc,char**argv){try{
    if(argc!=4)throw std::runtime_error("usage: articulation_gpu joints.spv monkey_birth.bin monkey_joints.bin");
    auto mesh=read(argv[2]);if(mesh.size()<8)throw std::runtime_error("short mesh");uint32_t n=word(mesh,0),nf=word(mesh,4);
    if(mesh.size()!=8ull+12ull*n+12ull*nf)throw std::runtime_error("mesh format mismatch");
    JointBinding b;std::string error;if(!decode_joint_binding(read(argv[3]),n,b,error))throw std::runtime_error(error);
    std::vector<float>rest(n*9ull);for(uint32_t i=0;i<n;++i){std::memcpy(rest.data()+9ull*i,mesh.data()+8+12ull*i,12);rest[9ull*i+4]=1;rest[9ull*i+6]=.7f;rest[9ull*i+7]=.5f;rest[9ull*i+8]=.3f;}
    GPU gpu(argv[1]);json checks=json::array();int failed=0;
    for(int c=0;c<3;++c){
        std::vector<float>a(b.joint_count,0),state(b.joint_count*8ull,0);
        for(uint32_t j=0;j<b.joint_count;++j){
            if(c==1 && (b.names[j]=="hip_L"||b.names[j]=="knee_L"))a[j]=.45f;
            if(c==2)a[j]=float(int(j%7)-3)*.11f;
            for(int k=0;k<3;++k){state[8*j+k]=b.pivots[3*j+k];state[8*j+3+k]=b.axes[3*j+k];}state[8*j+7]=a[j];
        }
        std::array<std::vector<uint8_t>,12> inputs;inputs[0]=bytes(rest);inputs[1]=bytes(b.owner);inputs[2]=bytes(b.weight);inputs[3]=bytes(state);inputs[4]=bytes(rest);inputs[5]=bytes(b.parents);inputs[11]=bytes(b.secondary);
        auto output=gpu.run(inputs,n,b.joint_count);double pe=0,ne=0,ce=0;
        for(uint32_t i=0;i<n;++i)for(int kind=0;kind<2;++kind){
            std::array<double,3>p{rest[9ull*i+kind*3],rest[9ull*i+kind*3+1],rest[9ull*i+kind*3+2]};
            int j=b.owner[i],second=b.secondary[i]>=0?b.secondary[i]:b.parents[j];
            auto p1=oracle(p,j,b,a,kind==0),p2=oracle(p,second,b,a,kind==0);double w=b.weight[i],norm=0;
            for(int k=0;k<3;++k){p[k]=w*p1[k]+(1-w)*p2[k];norm+=p[k]*p[k];}
            if(kind==1 && norm>1e-20)for(double& value:p)value/=std::sqrt(norm);
            for(int k=0;k<3;++k){double got=output[9ull*i+kind*3+k];double delta=std::isfinite(got)?std::fabs(got-p[k]):1e100;if(kind==0)pe=std::max(pe,delta);else ne=std::max(ne,delta);}
            for(int k=6;k<9;++k)ce=std::max(ce,double(std::fabs(output[9ull*i+k]-rest[9ull*i+k])));
        }
        bool ok=pe<2e-5 && ne<2e-5 && ce==0;if(!ok)++failed;
        checks.push_back({{"case",c==0?"rest":c==1?"hip_and_knee":"whole_body_mixed_axes"},{"pass",ok},{"vertices",n},{"max_position_error_world_units",pe},{"max_normal_error",ne},{"max_color_error",ce}});
    }
    std::cout<<json({{"adapter",gpu.name},{"checks",checks},{"failed",failed},{"scope","production articulation shader, not coupled forces or locomotion"}}).dump(2)<<"\n";return failed?1:0;
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 2;}}