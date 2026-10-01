// sort.wgsl — Tier 0, pass 2: GPU bitonic sort by (tile ASC, depth DESC)
//
// Particles are sorted within each tile from far to near so the rasterizer can
// blend front-to-back correctly.
//
// Algorithm: bitonic sort, log2(N) parallel passes. Each pass compares pairs
// separated by a fixed distance d = 1, 2, 4, ..., N/2. All comparisons within
// a single pass are independent (no intra-pass barrier needed).
//
// Input: indices[] — current permutation of [0..N-1]
//        tile[]    — tile index per particle (from preprocess output)
//        depth[]   — reversed-Z depth per particle (larger = closer in NDC)
//
// Output: indices[] — reordered so particles sort by ascending tile then descending depth.

const WG_SIZE: u32 = 256u;

struct SortParams {
    count : u32,
    dist  : u32,  // comparison distance for this pass (1, 2, 4, ..., N/2)
}

@group(0) @binding(0) var<storage, read_write> indices  : array<u32>;
@group(0) @binding(1) var<storage, read>         tile_in   : array<u32>;
@group(0) @binding(2) var<storage, read>         depth_in  : array<f32>;
@group(0) @binding(3) var<uniform>               sparams   : SortParams;

// Returns true if particle `a` should come BEFORE particle `b`.
// Sort key: (tile ASC, depth DESC) — farther particles first within each tile.
fn sort_key_less(a_idx: u32, b_idx: u32) -> bool {
    let tile_a = tile_in[indices[a_idx]];
    let tile_b = tile_in[indices[b_idx]];
    if (tile_a != tile_b) { return tile_a < tile_b; }
    // Reversed-Z: larger depth value means closer to camera.
    // Front-to-back blend wants far first → descending depth.
    return depth_in[indices[a_idx]] > depth_in[indices[b_idx]];
}

// Single bitonic sort pass at distance `dist`.
// Workgroup `wid.x` handles indices [base .. base + WG_SIZE).
// Each invocation `local_id` handles one comparison pair.
@compute @workgroup_size(WG_SIZE)
fn sort_pass(@builtin(global_invocation_id) gid: vec3u,
             @builtin(workgroup_id)    wid: vec3u) {
    let count = sparams.count;
    let dist  = sparams.dist;

    // Clamp to power-of-2 boundary (bitonic sort requires N to be a power of 2).
    // Particles beyond the real count are left untouched (they hold identity indices).
    let base      = wid.x * WG_SIZE;
    let local_id  = gid.x;

    // Each invocation handles one pair: (base + k*2*dist, base + k*2*dist + dist)
    for (var k: u32 = 0u; k < WG_SIZE / 2u; k += 1u) {
        let idx_a = base + k * 2u * dist;
        let idx_b = idx_a + dist;
        if (idx_b >= count) { continue; }

        let a = indices[idx_a];
        let b = indices[idx_b];
        if (sort_key_less(b, a)) {
            indices[idx_a] = b;
            indices[idx_b] = a;
        }
    }
}
