// relax.cpp -- GLM-RELAX-GPU-01: the VERIFIED KERNELS DRIVE the declared
// overdamped descent on B2 gamma=1, standalone.
//
// Rule-0 membrane: docs/THE_RELAX_GPU01_PREREGISTRATION.md (preregistered
// before this build). No engine, no window, no optimizer import into the
// engine, no GPU-dynamics claim beyond this numerical gate.
//
// Semantics mirrored 1:1 from tools/overdamped_descent.py (the declared
// law of record), with ONE preregistered representation difference: the
// GPU loop's state of record lives in the SAME f32 buffers the frozen
// fixtures verify (the trial add happens IN-KERNEL; forces/energies are
// read back f32). The trial update is one new derived stage-4 kernel
// (x+ = x + alpha*p, no physics); evaluation always re-runs the VERIFIED
// stage0+1+2 path verbatim.
//
// Loop order matches run_descent:
//   top of iteration: verified eval of the CURRENT state (fresh F, E)
//     -> residual test (free DOF: P*max|F_free| <= residual_tol) -> STATIONARY
//     -> p = P*F, pins exactly zero; p_norm == 0 -> STATIONARY (D2)
//     -> guard alpha_max = min(1, GUARD_FRAC*min_edge/p_norm)
//     -> backtrack alpha <- alpha/2 (<= MAX_BACKTRACKS):
//          trial state built by the stage-4 KERNEL from persistent buffers
//          trial evaluated by the VERIFIED kernels (invalid geometry ->
//          backtracks, like the law's refusal)
//          accept iff Armijo: E+ <= E - c1*alpha*<F,p>   (host f64 math)
//     -> accept: state <- kernel output; stagnation test on the decrease
//     -> step budget exhausted -> STEP_LIMIT
#include "probe_core.hpp"

#include <cstdlib>

// The derived stage-4 kernel: trial update x+ = x + alpha*p, one vec4 per
// vertex. Pins are already exactly zero inside p (host-side, the pinned-
// direction law), so the kernel needs no pin list.
static const char* kTrialSource = R"(
#version 450
layout(local_size_x = 64) in;
layout(std430, set = 0, binding = 0) buffer Positions { vec4 positions[]; };
layout(std430, set = 0, binding = 1) readonly buffer Direction { vec4 direction[]; };
layout(push_constant) uniform PC { float alpha; uint vertex_count; } pc;
void main() {
    uint v = gl_GlobalInvocationID.x;
    if (v >= pc.vertex_count) return;
    positions[v] = vec4(positions[v].xyz + pc.alpha * direction[v].xyz, 0.0);
}
)";

static std::vector<char> compile_trial_shader() {
    const char* sdk = std::getenv("VULKAN_SDK");
    std::string glslc = (sdk && *sdk) ? (std::string(sdk) + "/Bin/glslc.exe") : std::string("glslc");
    fs::path src = fs::temp_directory_path() / "chimera_relax_trial.comp";
    fs::path out(src.string() + ".spv");
    { std::ofstream f(src, std::ios::binary); f << kTrialSource; }
    std::string cmd = glslc + " -O -o " + out.string() + " " + src.string();
    if (std::system(cmd.c_str()) != 0) throw std::runtime_error("glslc failed for trial shader: " + cmd);
    return read_binary(out);
}

// Constants IMPORTED from the declared law (overdamped_descent.py) --
// never re-tuned; the audit lives there.
static constexpr double ARMIJO_C1 = 1.0e-4;
static constexpr double BACKTRACK_FACTOR = 0.5;
static constexpr int MAX_BACKTRACKS = 50;
static constexpr double GUARD_FRAC = 1.0e-3;
static constexpr double RESIDUAL_TOL_FRAC = 1.0e-12;
static constexpr double STAGNATION_FRAC = 8.0;
static constexpr int DEFAULT_MAX_STEPS = 200;
static constexpr double EPS_F64 = 2.220446049250313e-16;  // numpy float64 eps

struct StepTrail { double alpha, f_dot_p, u_before, u_after; };

struct RelaxResult {
    std::string status, reason;
    std::vector<F4> positions;        // final GPU state of record (f32)
    double energy = 0.0;              // final f32-read-back energy [J]
    std::vector<double> energies;     // E after each accepted step
    std::vector<StepTrail> trail;
    int n_accepted = 0, n_trials = 0;
    double free_residual = 0.0;       // final P*max|F_free| [m]
    double initial_energy = 0.0;
};

struct TrialPipe {
    VkProbe& vk;
    VkPipeline pipeline = VK_NULL_HANDLE;
    VkPipelineLayout layout = VK_NULL_HANDLE;
    VkDescriptorSetLayout dsl = VK_NULL_HANDLE;
    VkDescriptorPool dp = VK_NULL_HANDLE;
    explicit TrialPipe(VkProbe& v) : vk(v) {
        auto spv = compile_trial_shader();
        VkShaderModuleCreateInfo smi{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};
        smi.codeSize = spv.size(); smi.pCode = (const uint32_t*)spv.data();
        VkShaderModule sm; VkProbe::check(vkCreateShaderModule(vk.device, &smi, nullptr, &sm), "trial shader module");
        VkDescriptorSetLayoutBinding bs[2] = {};
        bs[0] = {0, VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, 1, VK_SHADER_STAGE_COMPUTE_BIT, nullptr};  // positions (rw)
        bs[1] = {1, VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, 1, VK_SHADER_STAGE_COMPUTE_BIT, nullptr};  // direction (r)
        VkDescriptorSetLayoutCreateInfo lci{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};
        lci.bindingCount = 2; lci.pBindings = bs;
        VkProbe::check(vkCreateDescriptorSetLayout(vk.device, &lci, nullptr, &dsl), "trial dsl");
        VkPushConstantRange pc{VK_SHADER_STAGE_COMPUTE_BIT, 0, 8};   // float alpha + uint count
        VkPipelineLayoutCreateInfo plci{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
        plci.setLayoutCount = 1; plci.pSetLayouts = &dsl;
        plci.pushConstantRangeCount = 1; plci.pPushConstantRanges = &pc;
        VkProbe::check(vkCreatePipelineLayout(vk.device, &plci, nullptr, &layout), "trial pipeline layout");
        VkComputePipelineCreateInfo cp{VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO};
        cp.stage = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO};
        cp.stage.stage = VK_SHADER_STAGE_COMPUTE_BIT; cp.stage.module = sm; cp.stage.pName = "main";
        cp.layout = layout;
        VkProbe::check(vkCreateComputePipelines(vk.device, VK_NULL_HANDLE, 1, &cp, nullptr, &pipeline), "trial pipeline");
        vkDestroyShaderModule(vk.device, sm, nullptr);
        VkDescriptorPoolSize ps{VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, 2};
        VkDescriptorPoolCreateInfo dpi{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
        dpi.flags = VK_DESCRIPTOR_POOL_CREATE_FREE_DESCRIPTOR_SET_BIT;
        dpi.maxSets = 1; dpi.poolSizeCount = 1; dpi.pPoolSizes = &ps;
        VkProbe::check(vkCreateDescriptorPool(vk.device, &dpi, nullptr, &dp), "trial descriptor pool");
    }
    ~TrialPipe() {
        if (dp) vkDestroyDescriptorPool(vk.device, dp, nullptr);
        if (pipeline) vkDestroyPipeline(vk.device, pipeline, nullptr);
        if (layout) vkDestroyPipelineLayout(vk.device, layout, nullptr);
        if (dsl) vkDestroyDescriptorSetLayout(vk.device, dsl, nullptr);
    }
    // x <- x + alpha*p on the device (persistent host-mapped buffers).
    void update(VkBuffer pos, VkBuffer dir, float alpha, uint32_t n) {
        VkDescriptorSet ds; VkDescriptorSetAllocateInfo dai{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};
        dai.descriptorPool = dp; dai.descriptorSetCount = 1; dai.pSetLayouts = &dsl;
        VkProbe::check(vkAllocateDescriptorSets(vk.device, &dai, &ds), "trial ds alloc");
        VkDescriptorBufferInfo bi[2] = {{pos, 0, VK_WHOLE_SIZE}, {dir, 0, VK_WHOLE_SIZE}};
        VkWriteDescriptorSet ws[2] = {};
        for (int z = 0; z < 2; ++z) {
            ws[z].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET; ws[z].dstSet = ds;
            ws[z].dstBinding = (uint32_t)z; ws[z].descriptorCount = 1;
            ws[z].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER; ws[z].pBufferInfo = &bi[z];
        }
        vkUpdateDescriptorSets(vk.device, 2, ws, 0, nullptr);
        VkCommandBufferBeginInfo b{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
        b.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
        VkProbe::check(vkResetCommandBuffer(vk.cmd, 0), "reset");
        VkProbe::check(vkBeginCommandBuffer(vk.cmd, &b), "begin");
        vkCmdBindPipeline(vk.cmd, VK_PIPELINE_BIND_POINT_COMPUTE, pipeline);
        vkCmdBindDescriptorSets(vk.cmd, VK_PIPELINE_BIND_POINT_COMPUTE, layout, 0, 1, &ds, 0, nullptr);
        struct { float alpha; uint32_t n; } pc{alpha, n};
        vkCmdPushConstants(vk.cmd, layout, VK_SHADER_STAGE_COMPUTE_BIT, 0, sizeof(pc), &pc);
        vkCmdDispatch(vk.cmd, ceil_groups(n), 1, 1);
        VkMemoryBarrier mb{VK_STRUCTURE_TYPE_MEMORY_BARRIER};
        mb.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
        mb.dstAccessMask = VK_ACCESS_SHADER_READ_BIT | VK_ACCESS_SHADER_WRITE_BIT;
        vkCmdPipelineBarrier(vk.cmd, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, 0, 1, &mb, 0, nullptr, 0, nullptr);
        VkProbe::check(vkEndCommandBuffer(vk.cmd), "end");
        VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO}; si.commandBufferCount = 1; si.pCommandBuffers = &vk.cmd;
        VkProbe::check(vkQueueSubmit(vk.queue, 1, &si, vk.fence), "submit");
        VkProbe::check(vkWaitForFences(vk.device, 1, &vk.fence, VK_TRUE, UINT64_MAX), "wait");
        VkProbe::check(vkResetFences(vk.device, 1, &vk.fence), "reset fence");
        vkFreeDescriptorSets(vk.device, dp, 1, &ds);
    }
};

static double geom_stats(const std::vector<F4>& pos, const std::vector<U4>& ind,
                         double& min_edge, double& mean_edge) {
    double e_sq_min = 1e300, e_sq_sum = 0; long e_cnt = 0;
    for (const auto& t : ind) {
        double ax = pos[t.x].x, ay = pos[t.x].y, az = pos[t.x].z;
        double bx = pos[t.y].x, by = pos[t.y].y, bz = pos[t.y].z;
        double cx = pos[t.z].x, cy = pos[t.z].y, cz = pos[t.z].z;
        double eab = (bx-ax)*(bx-ax)+(by-ay)*(by-ay)+(bz-az)*(bz-az);
        double ebc = (cx-bx)*(cx-bx)+(cy-by)*(cy-by)+(cz-bz)*(cz-bz);
        double eca = (ax-cx)*(ax-cx)+(ay-cy)*(ay-cy)+(az-cz)*(az-cz);
        e_sq_min = std::min({e_sq_min, eab, ebc, eca});
        e_sq_sum += std::sqrt(eab) + std::sqrt(ebc) + std::sqrt(eca);
        e_cnt += 3;
    }
    min_edge = std::sqrt(e_sq_min);
    mean_edge = e_sq_sum / e_cnt;
    return min_edge;
}

int main(int argc, char** argv) {
    try {
        fs::path root = "docs/evidence/gpu_fixtures";
        std::string fixture_name = "b2";
        std::string gamma_case = "gamma1";
        int max_steps = DEFAULT_MAX_STEPS;
        for (int i = 1; i < argc; ++i) {
            std::string a = argv[i];
            if (a == "--fixtures" && i + 1 < argc) root = argv[++i];
            else if (a == "--fixture" && i + 1 < argc) fixture_name = argv[++i];
            else if (a == "--gamma-case" && i + 1 < argc) gamma_case = argv[++i];
            else if (a == "--max-steps" && i + 1 < argc) max_steps = std::atoi(argv[++i]);
        }
        fs::path fx = root / fixture_name;
        auto p32 = values<float>(fx / "geometry/positions_f32.npy");
        auto ix = values<uint32_t>(fx / "geometry/indices_u32.npy");
        auto off64 = values<int64_t>(fx / "adjacency/csr_offsets_i64.npy");
        auto ci64 = values<int64_t>(fx / "adjacency/csr_corner_idx_i64.npy");
        auto gam = values<float>(fx / ("geometry/" + gamma_case + "_f32.npy"));
        std::vector<uint32_t> offsets(off64.begin(), off64.end()), corners(ci64.begin(), ci64.end());
        std::vector<F4> pos(p32.size() / 3);
        for (size_t i = 0; i < pos.size(); ++i) pos[i] = {p32[i*3], p32[i*3+1], p32[i*3+2], 0.f};
        std::vector<U4> ind(ix.size() / 3);
        for (size_t i = 0; i < ind.size(); ++i) ind[i] = {ix[i*3], ix[i*3+1], ix[i*3+2], 0u};
        const uint32_t NV = (uint32_t)pos.size(), NF = (uint32_t)ind.size();

        // The declared B2 constraint set (the window demo's): rim 0..5
        // pinned, centre 6 free. B2-only gate (documented).
        if (fixture_name != "b2") { std::cerr << "RELAX_RESULT NOT_TESTED: only b2 is wired\n"; return 2; }
        const int CENTRE = (int)NV - 1;

        double gmax = 0; for (float g : gam) gmax = std::max(gmax, (double)g);
        if (gmax <= 0) { std::cout << "RELAX_RESULT NOT_TESTED: gamma_max<=0\n"; return 2; }
        const double P = 1.0 / gmax;    // [m^2/J] with 1 wu = 1 m (declared)

        double min_edge = 0, mean_edge = 0;
        geom_stats(pos, ind, min_edge, mean_edge);
        double residual_tol = RESIDUAL_TOL_FRAC * mean_edge;

        VkProbe vk(CHIMERA_PROBE_SHADER_PATH);
        std::cout << "device: " << vk.device_name << "\n";
        TrialPipe trial(vk);
        VkProbe::Buf pos_buf = vk.buffer(NV * sizeof(F4));   // kernel-local state
        VkProbe::Buf dir_buf = vk.buffer(NV * sizeof(F4));

        RelaxResult result;
        result.positions = pos;

        std::vector<Face> faces(NF); std::vector<F4> vf(NV);
        std::vector<uint32_t> valid(NF);
        float U = 0;                     // f32 read-back: the GPU state's energy

        for (int it = 0; it < max_steps; ++it) {
            // 1) verified evaluation of the CURRENT state
            vk.run_case(pos, ind, gam, offsets, corners, faces, vf, valid, U);
            bool all_valid = true;
            for (auto x : valid) if (x != 1) all_valid = false;
            if (!all_valid) { result.status = "invalid_surface"; result.reason = "gpu_eval_invalid"; break; }
            if (it == 0) result.initial_energy = U;
            result.energy = U;

            // 2) residual test on free DOFs (law R4-U2.1, free mask = {centre})
            double p_norm = 0, pdotf = 0, free_res = 0;
            std::vector<F4> pdir(NV);
            for (uint32_t v = 0; v < NV; ++v) {
                double px = 0, py = 0, pz = 0;
                if ((int)v == CENTRE) {
                    px = P * (double)vf[v].x; py = P * (double)vf[v].y; pz = P * (double)vf[v].z;
                    free_res = std::max({free_res, std::abs(P * (double)vf[v].x),
                                         std::abs(P * (double)vf[v].y),
                                         std::abs(P * (double)vf[v].z)});
                }
                pdir[v] = {(float)px, (float)py, (float)pz, 0.f};
                pdotf += px * (double)vf[v].x + py * (double)vf[v].y + pz * (double)vf[v].z;
                p_norm = std::max(p_norm, std::sqrt(px*px + py*py + pz*pz));
            }
            result.free_residual = free_res;
            if (free_res <= residual_tol) { result.status = "stationary"; break; }
            if (p_norm == 0.0) { result.status = "stationary"; break; }   // D2

            // 3) guard
            double alpha_max = std::min(1.0, (GUARD_FRAC * min_edge) / p_norm);

            // 4) backtracking Armijo; the TRIAL is built by the kernel
            bool accepted = false;
            double alpha = alpha_max;
            for (int bt = 0; bt <= MAX_BACKTRACKS; ++bt) {
                ++result.n_trials;
                std::memcpy(dir_buf.p, pdir.data(), NV * sizeof(F4));
                std::memcpy(pos_buf.p, pos.data(), NV * sizeof(F4));
                trial.update(pos_buf.b, dir_buf.b, (float)alpha, NV);
                std::vector<F4> xplus(NV);
                std::memcpy(xplus.data(), pos_buf.p, NV * sizeof(F4));
                float Uplus = 0; std::vector<Face> fplus(NF);
                std::vector<F4> vfplus(NV); std::vector<uint32_t> vplus(NF);
                vk.run_case(xplus, ind, gam, offsets, corners, fplus, vfplus, vplus, Uplus);
                bool geo_ok = true; for (auto x : vplus) if (x != 1) geo_ok = false;
                if (geo_ok && (double)Uplus <= U - ARMIJO_C1 * alpha * pdotf) {
                    accepted = true;
                    result.trail.push_back({alpha, pdotf, U, (double)Uplus});
                    result.energies.push_back(Uplus);
                    ++result.n_accepted;
                    pos = xplus;                    // kernel output IS the state
                    result.positions = pos;         // report the real final state
                    geom_stats(pos, ind, min_edge, mean_edge);
                    residual_tol = RESIDUAL_TOL_FRAC * mean_edge;
                    break;
                }
                alpha *= BACKTRACK_FACTOR;
            }
            if (!accepted) { result.status = "no_descent_step"; result.reason = "no_descent_step"; break; }

            // 5) stagnation on this step's decrease (law R4-U2.2; the law
            // reports it on the accepted decrease of the CURRENT step).
            const auto& t = result.trail.back();
            if (t.u_before - t.u_after <=
                STAGNATION_FRAC * EPS_F64 * std::max(t.u_before, 1.0)) {
                result.status = "stagnated"; result.reason = "decrease_below_machine_scale";
                break;
            }
        }
        if (result.status.empty()) result.status = "step_limit";

        // Final evaluation so the harness gets final forces/energy at the
        // exact final state (the loop may have broken before re-evaluating).
        if (result.status != "invalid_surface") {
            float Ufin = 0;
            vk.run_case(pos, ind, gam, offsets, corners, faces, vf, valid, Ufin);
            result.energy = Ufin;
        }

        std::cout << "RELAX_RESULT status=" << result.status
                  << " reason=" << result.reason
                  << " n_accepted=" << result.n_accepted
                  << " n_trials=" << result.n_trials
                  << " initial_energy=" << std::setprecision(9) << result.initial_energy
                  << " energy=" << result.energy
                  << " free_residual=" << result.free_residual
                  << " n_trail=" << result.trail.size();
        for (size_t i = 0; i < result.trail.size(); ++i)
            std::cout << " a" << i << "=" << result.trail[i].alpha
                      << " f" << i << "=" << result.trail[i].f_dot_p
                      << " e" << i << "=" << result.trail[i].u_after;
        std::cout << "\nRELAX_FINAL_POS";
        for (const auto& v : result.positions)
            std::cout << " " << std::setprecision(9) << v.x << "," << v.y << "," << v.z;
        std::cout << "\n";
        // All FIVE named states are legitimate exits (the law's taxonomy);
        // the harness's CPU comparison decides PASS/FAIL, not this code.
        bool named = result.status == "stationary" || result.status == "stagnated" ||
                     result.status == "step_limit" || result.status == "no_descent_step" ||
                     result.status == "invalid_surface";
        return named ? 0 : 1;
    } catch (const std::exception& e) {
        std::cerr << "RELAX_RESULT NOT_TESTED: " << e.what() << "\n";
        return 2;
    }
}
