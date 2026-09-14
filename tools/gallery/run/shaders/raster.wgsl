// raster.wgsl — Tier 0+1, pass 3: tile rasterizer (HDR output)
// Renders each tile by reading the sorted particle list and blending front-to-back.
// One workgroup per tile; shared memory batches particles for that tile.
//
// Outputs HDR linear color to rgba16float (or equivalent float format).
// Tonemap is applied in a separate full-screen pass (tonemapping.wgsl).
//
// Inputs (from preprocess + sort):
//   pos[]     — vec4 clip-space position
//   cov[]     — vec3 covariance {scale, angle_cos, angle_sin}  (AA-clamped)
//   colors[]  — vec3f particle colour in linear HDR space
//   sizes[]   — f32 per-particle size
//   sorted_idx[] — u32 index into above arrays (sorted by tile+depth)
//   tile_counts[] — u32 particles per tile
//   tile_offsets[]  — u32 start index in sorted_idx per tile

const TILE_SIZE: u32 = 16u;
const MAX_PARTICLES_PER_TILE: u32 = 64u;
const EPS: f32 = 1e-8f;

struct RasterParams {
    resolution   : vec2f,
    inv_res      : vec2f,
}

@group(0) @binding(0) var<storage, read>  pos      : array<vec4f>;
@group(0) @binding(1) var<storage, read>  cov      : array<vec3f>;
@group(0) @binding(2) var<storage, read>  colors   : array<vec3f>;
@group(0) @binding(3) var<storage, read>  sizes    : array<f32>;
@group(0) @binding(4) var<storage, read>  sorted_idx : array<u32>;
@group(0) @binding(5) var<storage, read>  tile_counts: array<u32>;  // particles per tile
@group(0) @binding(6) var<storage, read_write>  tile_offsets : array<u32>;  // start index in sorted_idx per tile
@group(0) @binding(7) var<uniform>             rparams   : RasterParams;

// Output: HDR color attachment (rgba16float or similar float format)
@fragment
fn main(@builtin(position) frag_pos: vec4f) -> @location(0) vec4f {
    let px  = u32(frag_pos.x);
    let py  = u32(frag_pos.y);
    let res = rparams.resolution;

    // Tile coordinate of this fragment
    let tx = px / TILE_SIZE;
    let ty = py / TILE_SIZE;
    let tile_id = ty * (u32(res.x) / TILE_SIZE) + tx;

    // Load particle count for this tile
    let n_tile = tile_counts[tile_id];
    if (n_tile == 0u) {
        return vec4f(0.0f, 0.0f, 0.0f, 1.0f);  // black in HDR — tonemap will handle
    }

    let base = tile_offsets[tile_id];

    var accum_r: f32 = 0.0f;
    var accum_g: f32 = 0.0f;
    var accum_b: f32 = 0.0f;
    var accum_a: f32 = 0.0f;
    var occ: f32 = 1.0f;  // occupancy (1 - accumulated alpha)

    for (var k: u32 = 0u; k < n_tile && k < MAX_PARTICLES_PER_TILE; k += 1u) {
        let idx = sorted_idx[base + k];
        let p   = pos[idx];
        if (p.w <= 0.0f) { continue; }

        let inv_w = 1.0f / p.w;
        let sx = (p.x * inv_w + 1.0f) * 0.5f * res.x;
        let sy = (1.0f - p.y * inv_w - 1.0f) * 0.5f * res.y;

        // Distance from particle center to fragment in screen space
        let dx = f32(px) - sx;
        let dy = f32(py) - sy;

        let cov = cov[idx];
        let scale = cov.x;
        let c = cov.y;  // cos angle
        let s = cov.z;  // sin angle

        // Rotate distance by covariance angle, then evaluate Gaussian
        let rx =  dx * c + dy * s;
        let ry = -dx * s + dy * c;
        let d2 = (rx * rx + ry * ry) / (scale * scale);

        if (d2 > 4.0f) { continue; }  // outside Gaussian falloff

        // Mip-Splatting 2D box filter approximation:
        // Convolve the Gaussian with a 1x1 pixel box → additional variance of 1.0
        // This smooths high frequencies and removes the "dancing dots" artifact.
        let d2_filtered = d2 + (d2 / (scale * scale));
        if (d2_filtered > 4.0f) { continue; }

        let alpha = exp(-0.5f * d2_filtered) * clamp(scale / 8.0f, 0.0f, 1.0f);
        if (alpha < 0.004f) { continue; }

        let col = colors[idx];
        accum_r += col.x * alpha * occ;
        accum_g += col.y * alpha * occ;
        accum_b += col.z * alpha * occ;
        accum_a += alpha * occ;
        occ *= (1.0f - alpha);

        if (occ < 0.01f) { break; }  // early-out: mostly occluded
    }

    let a = min(accum_a, 1.0f);
    let rgb = vec3f(
        accum_r / max(a, EPS),
        accum_g / max(a, EPS),
        accum_b / max(a, EPS)
    );
    return vec4f(rgb, 1.0f);  // HDR linear color — tonemap applied in next pass
}