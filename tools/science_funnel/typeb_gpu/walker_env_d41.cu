// walker_env.cu -- extern "C" ctypes-loadable batched walk environment.
// Mirrors walker_nb_split_env.py's semantics EXACTLY: one reset_kernel at
// [E,1], then per tick tick_plan -> tick_integ -> tick_post on the default
// stream, ordered, a_rc carrying the integration verdict. The SoA arrays use
// the same per-env strides as the host allocation table (walker_nb_split_env.py
// lines 35-62). Host builds mdl/mdi/cst/csti from the compiled scene via
// walker_model.py + build_model_arrays and hands the flat arrays to
// env_create. Trailer: Agent: GLM 5.3.
#include <cuda_runtime.h>
#include <stdio.h>
#include "probe_kernels_d41.cuh"

struct WalkerEnv {
    int E, block, grid;
    double phi_l0, phi_r0, store_post;
    int settle_total;
    double* d_mdl; int* d_mdi; double* d_cst; int* d_csti; double* d_reset_store;
    double *a_q, *a_v, *a_work, *a_last_torque, *a_battery, *a_battery_post, *a_phi;
    int *a_touching, *a_captured, *a_settle, *a_ik_branch;
    double *a_paw_target, *a_paw_plant_y, *a_swing_from, *a_swing_to;
    double *a_fore_t, *a_fore_stance, *a_fore_cycle;
    int *a_fore_mode, *a_fore_entry, *a_fore_conv, *a_fore_td_plant, *a_fore_clamped, *a_fore_replants, *a_fore_td_count;
    int *a_hind_mode; double *a_hind_t, *a_hind_from, *a_hind_to, *a_hind_plant_y, *a_hind_ap, *a_hind_mp;
    int *a_hind_branch, *a_hind_held;
    long long *a_hind_last_fire, *a_hind_last_td;
    int *a_hind_fires, *a_hind_tds;
    double *a_hind_xoff; int *a_height_latched;
    double *a_cmd_vx; int *a_cmd_live; long long *a_cmd_first_tick; int *a_cmd_fires;
    long long *a_ticks; int *a_adv_calls, *a_refused, *a_refused_class, *a_collapsed, *a_rc;
    double *rb; int *rbi;
};

#define CU_OK(call) do { cudaError_t err_ = (call); if (err_ != cudaSuccess) { \
    fprintf(stderr, "CUDA error %s at %s:%d: %s\n", #call, __FILE__, __LINE__, cudaGetErrorString(err_)); \
    return 0; } } while (0)

template <typename T>
static T* dev_alloc(size_t n) {
    T* p = nullptr;
    if (cudaMalloc(&p, n * sizeof(T)) != cudaSuccess) return nullptr;
    if (cudaMemset(p, 0, n * sizeof(T)) != cudaSuccess) { cudaFree(p); return nullptr; }
    return p;
}

extern "C" {

#ifdef _WIN32
#define ENV_API __declspec(dllexport)
#else
#define ENV_API
#endif

ENV_API void* env_create(int E, int block,
                         const double* mdl, int n_mdl,
                         const int* mdi, int n_mdi,
                         const double* cst, int n_cst,
                         const int* csti, int n_csti,
                         const double* store_floor, int n_store,
                         double phi_l0, double phi_r0,
                         int settle_total, double store_post) {
    WalkerEnv* e = new WalkerEnv();
    e->E = E; e->block = block;
    e->grid = (E + block - 1) / block;
    e->phi_l0 = phi_l0; e->phi_r0 = phi_r0;
    e->settle_total = settle_total; e->store_post = store_post;
    long long e18 = (long long)E * 18;
    CU_OK(cudaMemcpyToSymbol(cu_total_q, &e18, sizeof(long long)));
    size_t E6 = (size_t)E * 6, E2 = (size_t)E * 2, E12 = (size_t)E * 12, sE = (size_t)E;

    CU_OK(cudaMalloc(&e->d_mdl, n_mdl * sizeof(double)));
    CU_OK(cudaMemcpy(e->d_mdl, mdl, n_mdl * sizeof(double), cudaMemcpyHostToDevice));
    CU_OK(cudaMalloc(&e->d_mdi, n_mdi * sizeof(int)));
    CU_OK(cudaMemcpy(e->d_mdi, mdi, n_mdi * sizeof(int), cudaMemcpyHostToDevice));
    CU_OK(cudaMalloc(&e->d_cst, n_cst * sizeof(double)));
    CU_OK(cudaMemcpy(e->d_cst, cst, n_cst * sizeof(double), cudaMemcpyHostToDevice));
    CU_OK(cudaMalloc(&e->d_csti, n_csti * sizeof(int)));
    CU_OK(cudaMemcpy(e->d_csti, csti, n_csti * sizeof(int), cudaMemcpyHostToDevice));
    CU_OK(cudaMalloc(&e->d_reset_store, n_store * sizeof(double)));
    CU_OK(cudaMemcpy(e->d_reset_store, store_floor, n_store * sizeof(double), cudaMemcpyHostToDevice));

    if (!(e->a_q = dev_alloc<double>(sE * 18))) return 0;
    if (!(e->a_v = dev_alloc<double>(sE * 18))) return 0;
    if (!(e->a_work = dev_alloc<double>(sE * 18))) return 0;
    if (!(e->a_last_torque = dev_alloc<double>(sE * 18))) return 0;
    if (!(e->a_battery = dev_alloc<double>(E12))) return 0;
    if (!(e->a_battery_post = dev_alloc<double>(sE))) return 0;
    if (!(e->a_phi = dev_alloc<double>(E2))) return 0;
    if (!(e->a_touching = dev_alloc<int>(E2))) return 0;
    if (!(e->a_captured = dev_alloc<int>(sE))) return 0;
    if (!(e->a_settle = dev_alloc<int>(sE))) return 0;
    if (!(e->a_ik_branch = dev_alloc<int>(E2))) return 0;
    if (!(e->a_paw_target = dev_alloc<double>(E6))) return 0;
    if (!(e->a_paw_plant_y = dev_alloc<double>(E2))) return 0;
    if (!(e->a_swing_from = dev_alloc<double>(E6))) return 0;
    if (!(e->a_swing_to = dev_alloc<double>(E6))) return 0;
    if (!(e->a_fore_t = dev_alloc<double>(E2))) return 0;
    if (!(e->a_fore_stance = dev_alloc<double>(E2))) return 0;
    if (!(e->a_fore_cycle = dev_alloc<double>(E2))) return 0;
    if (!(e->a_fore_mode = dev_alloc<int>(E2))) return 0;
    if (!(e->a_fore_entry = dev_alloc<int>(E2))) return 0;
    if (!(e->a_fore_conv = dev_alloc<int>(E2))) return 0;
    if (!(e->a_fore_td_plant = dev_alloc<int>(E2))) return 0;
    if (!(e->a_fore_clamped = dev_alloc<int>(E2))) return 0;
    if (!(e->a_fore_replants = dev_alloc<int>(E2))) return 0;
    if (!(e->a_fore_td_count = dev_alloc<int>(E2))) return 0;
    if (!(e->a_hind_mode = dev_alloc<int>(E2))) return 0;
    if (!(e->a_hind_t = dev_alloc<double>(E2))) return 0;
    if (!(e->a_hind_from = dev_alloc<double>(E6))) return 0;
    if (!(e->a_hind_to = dev_alloc<double>(E6))) return 0;
    if (!(e->a_hind_plant_y = dev_alloc<double>(E2))) return 0;
    if (!(e->a_hind_ap = dev_alloc<double>(E2))) return 0;
    if (!(e->a_hind_mp = dev_alloc<double>(E2))) return 0;
    if (!(e->a_hind_branch = dev_alloc<int>(E2))) return 0;
    if (!(e->a_hind_held = dev_alloc<int>(E2))) return 0;
    if (!(e->a_hind_last_fire = dev_alloc<long long>(E2))) return 0;
    if (!(e->a_hind_last_td = dev_alloc<long long>(E2))) return 0;
    if (!(e->a_hind_fires = dev_alloc<int>(E2))) return 0;
    if (!(e->a_hind_tds = dev_alloc<int>(E2))) return 0;
    if (!(e->a_hind_xoff = dev_alloc<double>(E2))) return 0;
    if (!(e->a_height_latched = dev_alloc<int>(sE))) return 0;
    if (!(e->a_cmd_vx = dev_alloc<double>(sE))) return 0;
    if (!(e->a_cmd_live = dev_alloc<int>(sE))) return 0;
    if (!(e->a_cmd_first_tick = dev_alloc<long long>(sE))) return 0;
    if (!(e->a_cmd_fires = dev_alloc<int>(sE))) return 0;
    if (!(e->a_ticks = dev_alloc<long long>(sE))) return 0;
    if (!(e->a_adv_calls = dev_alloc<int>(sE))) return 0;
    if (!(e->a_refused = dev_alloc<int>(sE))) return 0;
    if (!(e->a_refused_class = dev_alloc<int>(sE))) return 0;
    if (!(e->a_collapsed = dev_alloc<int>(sE))) return 0;
    if (!(e->a_rc = dev_alloc<int>(sE))) return 0;
    if (!(e->rb = dev_alloc<double>(E6))) return 0;
    if (!(e->rbi = dev_alloc<int>(E6))) return 0;
    return e;
}

ENV_API int env_reset(void* handle, const double* q0, const double* v0, const int* touching0) {
    WalkerEnv* e = (WalkerEnv*)handle;
    double *d_q0, *d_v0; int* d_t0;
    size_t nq = (size_t)e->E * 18 * sizeof(double), nt = (size_t)e->E * 2 * sizeof(int);
    CU_OK(cudaMalloc(&d_q0, nq)); CU_OK(cudaMemcpy(d_q0, q0, nq, cudaMemcpyHostToDevice));
    CU_OK(cudaMalloc(&d_v0, nq)); CU_OK(cudaMemcpy(d_v0, v0, nq, cudaMemcpyHostToDevice));
    CU_OK(cudaMalloc(&d_t0, nt)); CU_OK(cudaMemcpy(d_t0, touching0, nt, cudaMemcpyHostToDevice));
    reset_kernel<<<e->E, 1>>>(d_q0, d_v0, d_t0, e->phi_l0, e->phi_r0, e->settle_total,
                              e->d_reset_store, e->store_post,
                              e->a_q, e->a_v, e->a_work, e->a_last_torque,
                              e->a_battery, e->a_battery_post, e->a_phi, e->a_touching,
                              e->a_captured, e->a_settle, e->a_ik_branch, e->a_paw_target,
                              e->a_paw_plant_y, e->a_swing_from, e->a_swing_to,
                              e->a_fore_t, e->a_fore_stance, e->a_fore_cycle, e->a_fore_mode,
                              e->a_fore_entry, e->a_fore_conv, e->a_fore_td_plant,
                              e->a_fore_clamped, e->a_fore_replants, e->a_fore_td_count,
                              e->a_hind_mode, e->a_hind_t, e->a_hind_from, e->a_hind_to,
                              e->a_hind_plant_y, e->a_hind_ap, e->a_hind_mp, e->a_hind_branch,
                              e->a_hind_held, e->a_hind_last_fire, e->a_hind_last_td,
                              e->a_hind_fires, e->a_hind_tds, e->a_hind_xoff,
                              e->a_height_latched, e->a_cmd_vx, e->a_cmd_live,
                              e->a_cmd_first_tick, e->a_cmd_fires, e->a_ticks, e->a_adv_calls,
                              e->a_refused, e->a_refused_class, e->a_collapsed);
    cudaError_t err = cudaDeviceSynchronize();
    cudaFree(d_q0); cudaFree(d_v0); cudaFree(d_t0);
    if (err != cudaSuccess) { fprintf(stderr, "reset sync: %s\n", cudaGetErrorString(err)); return 0; }
    return 1;
}

ENV_API int env_set_command(void* handle, double v) {
    // scalar command: fill vx=v, live=1 for every env (walker_nb_split_env.py
    // set_command semantics with env_mask=None)
    WalkerEnv* e = (WalkerEnv*)handle;
    double* vx = (double*)malloc(e->E * sizeof(double));
    int* live = (int*)malloc(e->E * sizeof(int));
    if (!vx || !live) { free(vx); free(live); return 0; }
    for (int i = 0; i < e->E; ++i) { vx[i] = v; live[i] = 1; }
    CU_OK(cudaMemcpy(e->a_cmd_vx, vx, e->E * sizeof(double), cudaMemcpyHostToDevice));
    CU_OK(cudaMemcpy(e->a_cmd_live, live, e->E * sizeof(int), cudaMemcpyHostToDevice));
    free(vx); free(live);
    return 1;
}

ENV_API int env_set_command_flat(void* handle, const double* v, const int* live) {
    WalkerEnv* e = (WalkerEnv*)handle;
    CU_OK(cudaMemcpy(e->a_cmd_vx, v, e->E * sizeof(double), cudaMemcpyHostToDevice));
    CU_OK(cudaMemcpy(e->a_cmd_live, live, e->E * sizeof(int), cudaMemcpyHostToDevice));
    return 1;
}

// csti access for the probe phase (bars_fullport.py toggles power/contact/
// gait between probes exactly like the numba env's d_csti copy-modify)
ENV_API int env_csti_get(void* handle, int* out20) {
    WalkerEnv* e = (WalkerEnv*)handle;
    CU_OK(cudaMemcpy(out20, e->d_csti, 20 * sizeof(int), cudaMemcpyDeviceToHost));
    return 1;
}

ENV_API int env_csti_set(void* handle, const int* in20) {
    WalkerEnv* e = (WalkerEnv*)handle;
    CU_OK(cudaMemcpy(e->d_csti, in20, 20 * sizeof(int), cudaMemcpyHostToDevice));
    return 1;
}

// a_hind_xoff readback for F-FULLPORT-COMMAND-AUTHORITY (the plant-law
// consumption xoff = cmd*(DUTY_SAMPLED*T_CYCLE)/2 is written to a_hind_xoff
// at each hind fire; E*2 doubles)
ENV_API int env_read_xoff(void* handle, double* out2E) {
    WalkerEnv* e = (WalkerEnv*)handle;
    CU_OK(cudaMemcpy(out2E, e->a_hind_xoff, (size_t)e->E * 2 * sizeof(double), cudaMemcpyDeviceToHost));
    return 1;
}

// diagnostic: env-0 q/v/a_rc/a_adv_calls/a_refused/a_ticks raw readback
ENV_API int env_dbg_read(void* handle, double* q18, double* v18,
                         int* rc, int* adv, int* refused, long long* ticks) {
    WalkerEnv* e = (WalkerEnv*)handle;
    CU_OK(cudaMemcpy(q18, e->a_q, 18 * sizeof(double), cudaMemcpyDeviceToHost));
    CU_OK(cudaMemcpy(v18, e->a_v, 18 * sizeof(double), cudaMemcpyDeviceToHost));
    CU_OK(cudaMemcpy(rc, e->a_rc, sizeof(int), cudaMemcpyDeviceToHost));
    CU_OK(cudaMemcpy(adv, e->a_adv_calls, sizeof(int), cudaMemcpyDeviceToHost));
    CU_OK(cudaMemcpy(refused, e->a_refused, sizeof(int), cudaMemcpyDeviceToHost));
    CU_OK(cudaMemcpy(ticks, e->a_ticks, sizeof(long long), cudaMemcpyDeviceToHost));
    return 1;
}

ENV_API int env_step(void* handle, int n) {
    WalkerEnv* e = (WalkerEnv*)handle;
    for (int t = 0; t < n; ++t) {
        tick_plan_kernel<<<e->grid, e->block>>>(e->d_mdl, e->d_mdi, e->d_cst, e->d_csti,
            e->a_q, e->a_v, e->a_work, e->a_last_torque, e->a_battery, e->a_battery_post,
            e->a_phi, e->a_touching, e->a_captured, e->a_settle, e->a_ik_branch,
            e->a_paw_target, e->a_paw_plant_y, e->a_swing_from, e->a_swing_to,
            e->a_fore_t, e->a_fore_stance, e->a_fore_cycle, e->a_fore_mode,
            e->a_fore_entry, e->a_fore_conv, e->a_fore_td_plant, e->a_fore_clamped,
            e->a_fore_replants, e->a_fore_td_count, e->a_hind_mode, e->a_hind_t,
            e->a_hind_from, e->a_hind_to, e->a_hind_plant_y, e->a_hind_ap, e->a_hind_mp,
            e->a_hind_branch, e->a_hind_held, e->a_hind_last_fire, e->a_hind_last_td,
            e->a_hind_fires, e->a_hind_tds, e->a_hind_xoff, e->a_height_latched,
            e->a_cmd_vx, e->a_cmd_live, e->a_cmd_first_tick, e->a_cmd_fires,
            e->a_ticks, e->a_adv_calls, e->a_refused, e->a_refused_class, e->a_collapsed,
            e->rb, e->rbi, e->a_rc);
        tick_integ_kernel<<<e->grid, e->block>>>(e->d_mdl, e->d_mdi, e->d_cst, e->d_csti,
            e->a_q, e->a_v, e->a_work, e->a_last_torque, e->a_battery, e->a_battery_post,
            e->a_phi, e->a_touching, e->a_captured, e->a_settle, e->a_ik_branch,
            e->a_paw_target, e->a_paw_plant_y, e->a_swing_from, e->a_swing_to,
            e->a_fore_t, e->a_fore_stance, e->a_fore_cycle, e->a_fore_mode,
            e->a_fore_entry, e->a_fore_conv, e->a_fore_td_plant, e->a_fore_clamped,
            e->a_fore_replants, e->a_fore_td_count, e->a_hind_mode, e->a_hind_t,
            e->a_hind_from, e->a_hind_to, e->a_hind_plant_y, e->a_hind_ap, e->a_hind_mp,
            e->a_hind_branch, e->a_hind_held, e->a_hind_last_fire, e->a_hind_last_td,
            e->a_hind_fires, e->a_hind_tds, e->a_hind_xoff, e->a_height_latched,
            e->a_cmd_vx, e->a_cmd_live, e->a_cmd_first_tick, e->a_cmd_fires,
            e->a_ticks, e->a_adv_calls, e->a_refused, e->a_refused_class, e->a_collapsed,
            e->rb, e->rbi, e->a_rc);
        tick_post_kernel<<<e->grid, e->block>>>(e->d_mdl, e->d_mdi, e->d_cst, e->d_csti,
            e->a_q, e->a_v, e->a_work, e->a_last_torque, e->a_battery, e->a_battery_post,
            e->a_phi, e->a_touching, e->a_captured, e->a_settle, e->a_ik_branch,
            e->a_paw_target, e->a_paw_plant_y, e->a_swing_from, e->a_swing_to,
            e->a_fore_t, e->a_fore_stance, e->a_fore_cycle, e->a_fore_mode,
            e->a_fore_entry, e->a_fore_conv, e->a_fore_td_plant, e->a_fore_clamped,
            e->a_fore_replants, e->a_fore_td_count, e->a_hind_mode, e->a_hind_t,
            e->a_hind_from, e->a_hind_to, e->a_hind_plant_y, e->a_hind_ap, e->a_hind_mp,
            e->a_hind_branch, e->a_hind_held, e->a_hind_last_fire, e->a_hind_last_td,
            e->a_hind_fires, e->a_hind_tds, e->a_hind_xoff, e->a_height_latched,
            e->a_cmd_vx, e->a_cmd_live, e->a_cmd_first_tick, e->a_cmd_fires,
            e->a_ticks, e->a_adv_calls, e->a_refused, e->a_refused_class, e->a_collapsed,
            e->rb, e->rbi, e->a_rc);
        cudaError_t err = cudaGetLastError();
        if (err != cudaSuccess) {
            fprintf(stderr, "launch error at tick %d: %s\n", t, cudaGetErrorString(err));
            return 0;
        }
    }
    return 1;
}

ENV_API int env_sync(void* handle) {
    (void)handle;
    cudaError_t err = cudaDeviceSynchronize();
    return err == cudaSuccess ? 1 : 0;
}

// status readback: all out-arrays preallocated by the host with the sizes noted
ENV_API int env_status(void* handle,
                       double* rb_out, int* rbi_out,
                       int* refused_out, int* refused_class_out, int* collapsed_out,
                       long long* ticks_out, int* cmd_fires_out, long long* cmd_first_tick_out,
                       int* hind_tds_out, int* fore_td_count_out) {
    WalkerEnv* e = (WalkerEnv*)handle;
    size_t E6 = (size_t)e->E * 6, E2 = (size_t)e->E * 2, sE = (size_t)e->E;
    CU_OK(cudaMemcpy(rb_out, e->rb, E6 * sizeof(double), cudaMemcpyDeviceToHost));
    CU_OK(cudaMemcpy(rbi_out, e->rbi, E6 * sizeof(int), cudaMemcpyDeviceToHost));
    CU_OK(cudaMemcpy(refused_out, e->a_refused, sE * sizeof(int), cudaMemcpyDeviceToHost));
    CU_OK(cudaMemcpy(refused_class_out, e->a_refused_class, sE * sizeof(int), cudaMemcpyDeviceToHost));
    CU_OK(cudaMemcpy(collapsed_out, e->a_collapsed, sE * sizeof(int), cudaMemcpyDeviceToHost));
    CU_OK(cudaMemcpy(ticks_out, e->a_ticks, sE * sizeof(long long), cudaMemcpyDeviceToHost));
    CU_OK(cudaMemcpy(cmd_fires_out, e->a_cmd_fires, sE * sizeof(int), cudaMemcpyDeviceToHost));
    CU_OK(cudaMemcpy(cmd_first_tick_out, e->a_cmd_first_tick, sE * sizeof(long long), cudaMemcpyDeviceToHost));
    CU_OK(cudaMemcpy(hind_tds_out, e->a_hind_tds, E2 * sizeof(int), cudaMemcpyDeviceToHost));
    CU_OK(cudaMemcpy(fore_td_count_out, e->a_fore_td_count, E2 * sizeof(int), cudaMemcpyDeviceToHost));
    return 1;
}

ENV_API void env_free(void* handle) {
    WalkerEnv* e = (WalkerEnv*)handle;
    if (!e) return;
    cudaFree(e->d_mdl); cudaFree(e->d_mdi); cudaFree(e->d_cst); cudaFree(e->d_csti);
    cudaFree(e->d_reset_store);
    cudaFree(e->a_q); cudaFree(e->a_v); cudaFree(e->a_work); cudaFree(e->a_last_torque);
    cudaFree(e->a_battery); cudaFree(e->a_battery_post); cudaFree(e->a_phi);
    cudaFree(e->a_touching); cudaFree(e->a_captured); cudaFree(e->a_settle);
    cudaFree(e->a_ik_branch); cudaFree(e->a_paw_target); cudaFree(e->a_paw_plant_y);
    cudaFree(e->a_swing_from); cudaFree(e->a_swing_to); cudaFree(e->a_fore_t);
    cudaFree(e->a_fore_stance); cudaFree(e->a_fore_cycle); cudaFree(e->a_fore_mode);
    cudaFree(e->a_fore_entry); cudaFree(e->a_fore_conv); cudaFree(e->a_fore_td_plant);
    cudaFree(e->a_fore_clamped); cudaFree(e->a_fore_replants); cudaFree(e->a_fore_td_count);
    cudaFree(e->a_hind_mode); cudaFree(e->a_hind_t); cudaFree(e->a_hind_from);
    cudaFree(e->a_hind_to); cudaFree(e->a_hind_plant_y); cudaFree(e->a_hind_ap);
    cudaFree(e->a_hind_mp); cudaFree(e->a_hind_branch); cudaFree(e->a_hind_held);
    cudaFree(e->a_hind_last_fire); cudaFree(e->a_hind_last_td); cudaFree(e->a_hind_fires);
    cudaFree(e->a_hind_tds); cudaFree(e->a_hind_xoff); cudaFree(e->a_height_latched);
    cudaFree(e->a_cmd_vx); cudaFree(e->a_cmd_live); cudaFree(e->a_cmd_first_tick);
    cudaFree(e->a_cmd_fires); cudaFree(e->a_ticks); cudaFree(e->a_adv_calls);
    cudaFree(e->a_refused); cudaFree(e->a_refused_class); cudaFree(e->a_collapsed);
    cudaFree(e->a_rc); cudaFree(e->rb); cudaFree(e->rbi);
    delete e;
}

} // extern "C"
