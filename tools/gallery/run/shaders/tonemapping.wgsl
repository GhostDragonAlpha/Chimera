// tonemapping.wgsl — Tier 1, pass 4: HDR → LDR tonemap
// Applies ACES filmic tonemap to linear HDR input and outputs sRGB-clamped LDR.
//
// Input:  hdr_color (vec3) — linear HDR color from raster pass
// Output: ldr_color (vec3) — tone-mapped sRGB-ready color

const WG_SIZE: u32 = 8u;

struct TonemapParams {
    exposure : f32,       // global exposure multiplier (default 1.0)
    _pad     : vec3f,     // padding to 16 bytes
}

@group(0) @binding(0) var<storage, read>  hdr_tex   : texture_2d<f32>;
@group(0) @binding(1) var<sampled>        hdr_sampler : sampler;
@group(0) @binding(2) var<uniform>        tparams     : TonemapParams;

// ACES filmic tonemap (from "An Invertible HDR Tone Map for Real-Time Rendering")
// Input: linear HDR value in [-1, 1] range (approximate log2 scale)
// Output: tone-mapped value in [0, 1]
fn aces_tonemap(x: f32) -> f32 {
    // ACES constants (simplified for f32 precision)
    let a = 2.51f;
    let b = 0.03f;
    let c = 2.43f;
    let d = 0.59f;
    let e = 0.14f;
    return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0f, 1.0f);
}

// Convert linear HDR to ACES space, apply tonemap, convert back to linear-ish output
fn tonemap_linear_to_srgb(c: vec3f) -> vec3f {
    // Apply exposure
    let exposed = c * tparams.exposure;

    // ACES filmic (operates on log2-scale approximations)
    let aces = exposed * 1.046f - 0.046f; // slight contrast lift
    let tonemapped = vec3f(
        aces_tonemap(aces.x),
        aces_tonemap(aces.y),
        aces_tonemap(aces.z)
    );

    // Simple gamma correction (sRGB approximation: pow(x, 1.0/2.2))
    return vec3f(pow(max(tonemapped.x, 0.0f), 1.0f / 2.2f),
                 pow(max(tonemapped.y, 0.0f), 1.0f / 2.2f),
                 pow(max(tonemapped.z, 0.0f), 1.0f / 2.2f));
}

@fragment
fn main(@builtin(position) frag: vec4f) -> @location(0) vec4f {
    let px = i32(frag.x);
    let py = i32(frag.y);
    let res = vec2f(textureDimensions(hdr_tex));

    // Sample HDR color (use nearest for exact pixel alignment)
    let hdr_color = textureSampleLevel(hdr_tex, hdr_sampler,
                                       vec2f(f32(px), f32(py)) / res, 0.0f);

    let ldr = tonemap_linear_to_srgb(hdr_color.rgb);
    return vec4f(ldr, 1.0f);
}

@compute @workgroup_size(WG_SIZE, WG_SIZE)
fn main(@builtin(global_invocation_id) gid: vec3u) {
    // Full-screen quad rasterization handles this — compute pass not needed
}