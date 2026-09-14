// preprocess.wgsl — Tier 0+1+2: project + Mip-Splatting AA + camera-relative LOD
// Camera-relative rebasing (Tier 2.1): subtract camera_pos from particle positions
// before projection, keeping clip-space coordinates well-conditioned at any distance.
// Reversed-Z depth (Tier 2.3): near=1.0, far=0.0 in NDC for max float32 precision.
// Screen-space LOD (Tier 2.5): cull particles below pixel-radius threshold.
const TILE_SIZE: u32 = 16u;
const EPS: f32     = 1e-8f;

struct Params {
    view_proj : mat4x4f,
    resolution : vec2f,
    n_particles : f32,
    camera_pos  : vec3f,   // world-space camera position (Tier 2.1 rebasing)
    lod_rho     : f32,     // grains-per-pixel-squared from trained model (default 0.35)
}

@group(0) @binding(0) var<storage, read>          pos      : array<vec4f>;
@group(0) @binding(1) var<storage, read_write> out_pos   : array<vec4f>;
@group(0) @binding(2) var<storage, read_write> out_cov   : array<vec3f>;
@group(0) @binding(3) var<storage, read_write> out_depth  : array<f32>;
@group(0) @binding(4) var<storage, read_write> out_tile   : array<u32>;
@group(0) @binding(5) var<uniform>             params    : Params;

const LOD_CULL_THRESHOLD: f32 = 2.0f; // below this px radius -> culled (Tier 2.5)

// Mip-Splatting: clamp Gaussian scale to Nyquist limit of the sampling rate.
fn clamp_to_nyquist(sigma_px: f32) -> f32 {
    return max(sigma_px, 0.5f);
}

@compute @workgroup_size(256)
fn main(@builtin(global_invocation_id) gid: vec3u) {
    let i = gid.x;
    let n = u32(params.n_particles);
    if (i >= n) { return; }
    let p    = pos[i];

    // Tier 2.1 - camera-relative rebasing
    let world_pos = vec3f(p.x, p.y, p.z);
    let rebased   = world_pos - params.camera_pos;
    let rp        = vec4f(rebased.x, rebased.y, rebased.z, p.w);

    // Project rebased position (reversed-Z baked into view_proj by caller)
    let hp   = params.view_proj * rp;
    out_pos[i]    = hp;
    out_depth[i]  = hp.w; // reversed-Z: larger = closer

    let inv_w = 1.0f / max(hp.w, EPS);
    let sx = (hp.x * inv_w + 1.0f) * 0.5f * params.resolution.x;
    let sy = (1.0f - hp.y * inv_w - 1.0f) * 0.5f * params.resolution.y;

    out_tile[i] = (u32(sx) / TILE_SIZE) * (u32(params.resolution.y) / TILE_SIZE) + u32(sy) / TILE_SIZE;

    // Tier 2.5 - screen-space LOD: cull particles below pixel-radius threshold
    let cam_pos = params.camera_pos;
    let cam_dist = length(world_pos - cam_pos);
    let r_world  = max(p.w, 0.1f);
    // Screen-space radius in pixels (fov=45deg: tan(22.5)=0.414)
    let r_px    = r_world * params.resolution.y / (2.0f * cam_dist * 0.414f);
    if (r_px < LOD_CULL_THRESHOLD) {
        out_pos[i] = vec4f(0.0f, 0.0f, 0.0f, 0.0f); // hide: w=0 -> culled by raster
    } else {
        let r_aa = clamp_to_nyquist(r_world * params.resolution.y / (2.0f * cam_dist * 0.414f));
        out_cov[i] = vec3f(r_aa, cos(0.785f), sin(0.785f)); // isotropic, AA-clamped
    }
}
