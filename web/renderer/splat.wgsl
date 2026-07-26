// Chimera renderer v2 -- SPIKE. The whole frame on the GPU: preprocess -> radix sort -> tile raster.
// No host in the per-frame path; the raster writes the canvas texture directly (bgra8unorm-storage).
//
// Key packing: tile_id (14 bits) << 18 | quantised depth (18 bits) -> ONE u32 sort key, so a single
// 32-bit radix sort gives tile-major, near-to-far order in one shot (the reference 3DGS approach).

const TILE: u32 = 16u;
const WG: u32 = 256u;          // radix workgroup = 1 item per thread
const RADIX: u32 = 16u;        // 4-bit digit -> 8 passes
const DEPTH_BITS: u32 = 18u;
const DEPTH_MAX: f32 = 262143.0;

struct Splat {
  pos: vec3f, scale: f32,
  col: vec3f, opa: f32,
  nrm: vec3f, _pad: f32,
};

struct Proj {
  xy: vec2f,
  depth: f32,
  radius: f32,     // 3-sigma cutoff radius in px; 0 => culled
  conic: vec3f,
  opa: f32,
  col: vec3f,
  _p: f32,
};

struct U {
  view0: vec4f,          // rows of the 3x4 rigid view matrix (xyz = rotation row, w = translation)
  view1: vec4f,
  view2: vec4f,
  screen: vec4f,         // w, h, tilesX, tilesY
  cfg: vec4f,            // focal, near, far, nSplats
  cfg2: vec4f,           // maxPairs, numWG_radix, radixPassShift, nPairs(unused on gpu)
  bg: vec4f,
};

@group(0) @binding(0) var<uniform> U_: U;
@group(0) @binding(1) var<storage, read>        splats: array<Splat>;
@group(0) @binding(2) var<storage, read_write>  proj:   array<Proj>;
@group(0) @binding(3) var<storage, read_write>  keysIn:  array<u32>;
@group(0) @binding(4) var<storage, read_write>  valsIn:  array<u32>;
@group(0) @binding(5) var<storage, read_write>  keysOut: array<u32>;
@group(0) @binding(6) var<storage, read_write>  valsOut: array<u32>;
@group(0) @binding(7) var<storage, read_write>  counter: array<atomic<u32>>;   // [0]=pairCount
@group(0) @binding(8) var<storage, read_write>  hist:    array<atomic<u32>>;   // [digit*numWG + wg]
@group(0) @binding(9) var<storage, read_write>  tileRange: array<vec2u>;
@group(0) @binding(10) var outTex: texture_storage_2d<bgra8unorm, write>;
@group(0) @binding(11) var<storage, read_write> indirect: array<u32>;   // [0..2] radix/pair dispatch args

// The pair count is only known ON the GPU. Deriving the workgroup count here (and dispatching
// indirectly) is what keeps the host out of the frame loop -- reading it back would stall every frame.
@compute @workgroup_size(1)
fn setupDispatch() {
  let n = atomicLoad(&counter[0]);
  let numWG = (n + WG - 1u) / WG;
  atomicStore(&counter[1], max(numWG, 1u));
  indirect[0] = max(numWG, 1u); indirect[1] = 1u; indirect[2] = 1u;
  let nChunks = (RADIX * max(numWG, 1u) + WG - 1u) / WG;      // scanReduce / scanAdd workgroups
  indirect[4] = max(nChunks, 1u); indirect[5] = 1u; indirect[6] = 1u;
}

// ─────────────────────────────────────────────────────────────────────────────
// PASS 1 -- preprocess: cull (frustum + back-face), project, conic, emit (key,val) per touched tile
// ─────────────────────────────────────────────────────────────────────────────
@compute @workgroup_size(256)
fn preprocess(@builtin(global_invocation_id) gid: vec3u) {
  let i = gid.x;
  if (i >= u32(U_.cfg.w)) { return; }
  proj[i].radius = 0.0;

  let s = splats[i];
  let vx = dot(U_.view0.xyz, s.pos) + U_.view0.w;
  let vy = dot(U_.view1.xyz, s.pos) + U_.view1.w;
  let vz = dot(U_.view2.xyz, s.pos) + U_.view2.w;
  if (vz >= 0.0) { return; }                 // behind the camera (view looks down -z)
  let z = -vz;
  if (z < U_.cfg.y || z > U_.cfg.z) { return; }

  // BACK-FACE CULL: a normal facing away is occluded by the near surface (v1's proven win)
  if (U_.bg.w > 0.5 && any(s.nrm != vec3f(0.0, 0.0, 0.0))) {
    let nx = dot(U_.view0.xyz, s.nrm);
    let ny = dot(U_.view1.xyz, s.nrm);
    let nz = dot(U_.view2.xyz, s.nrm);
    if (nx * vx + ny * vy + nz * vz > 0.0) { return; }
  }

  let focal = U_.cfg.x;
  let W = U_.screen.x; let H = U_.screen.y;
  let sx = W * 0.5 + focal * vx / z;
  let sy = H * 0.5 - focal * vy / z;
  let sigma = focal * s.scale * U_.cfg2.w / z; // isotropic screen-space sigma (cfg2.w = live scale knob)
  if (sigma < 0.05) { return; }
  let R = 3.0 * sigma;                        // 3-sigma cutoff (exp(-4.5) ~ 1%)
  if (sx + R < 0.0 || sx - R > W || sy + R < 0.0 || sy - R > H) { return; }

  let inv = 1.0 / (sigma * sigma);
  proj[i] = Proj(vec2f(sx, sy), z, R, vec3f(inv, 0.0, inv), s.opa, s.col, 0.0);

  let tilesX = u32(U_.screen.z); let tilesY = u32(U_.screen.w);
  let tx0 = u32(clamp(floor((sx - R) / f32(TILE)), 0.0, f32(tilesX - 1u)));
  let tx1 = u32(clamp(floor((sx + R) / f32(TILE)), 0.0, f32(tilesX - 1u)));
  let ty0 = u32(clamp(floor((sy - R) / f32(TILE)), 0.0, f32(tilesY - 1u)));
  let ty1 = u32(clamp(floor((sy + R) / f32(TILE)), 0.0, f32(tilesY - 1u)));
  let cnt = (tx1 - tx0 + 1u) * (ty1 - ty0 + 1u);

  let base = atomicAdd(&counter[0], cnt);
  let maxPairs = u32(U_.cfg2.x);
  if (base + cnt > maxPairs) { return; }

  let dq = u32(clamp((z - U_.cfg.y) / (U_.cfg.z - U_.cfg.y), 0.0, 1.0) * DEPTH_MAX);
  var k = 0u;
  for (var ty = ty0; ty <= ty1; ty = ty + 1u) {
    for (var tx = tx0; tx <= tx1; tx = tx + 1u) {
      let tile = ty * tilesX + tx;
      keysIn[base + k] = (tile << DEPTH_BITS) | dq;
      valsIn[base + k] = i;
      k = k + 1u;
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// PASS 2 -- radix sort (4-bit digit, 8 passes): histogram -> scan -> scatter
// ─────────────────────────────────────────────────────────────────────────────
var<workgroup> sHist: array<atomic<u32>, RADIX>;

@compute @workgroup_size(256)
fn radixHistogram(@builtin(global_invocation_id) gid: vec3u,
                  @builtin(local_invocation_id) lid: vec3u,
                  @builtin(workgroup_id) wid: vec3u) {
  // Accumulate in WORKGROUP memory, then one global write per bucket. The naive version did a GLOBAL
  // atomicAdd per key -- 480k x 8 passes = 3.8M contended global atomics per frame.
  if (lid.x < RADIX) { atomicStore(&sHist[lid.x], 0u); }
  workgroupBarrier();
  let n = atomicLoad(&counter[0]);
  let i = gid.x;
  if (i < n) {
    let d = (keysIn[i] >> u32(U_.cfg2.z)) & (RADIX - 1u);
    atomicAdd(&sHist[d], 1u);
  }
  workgroupBarrier();
  if (lid.x < RADIX) {
    let numWG = atomicLoad(&counter[1]);
    atomicStore(&hist[lid.x * numWG + wid.x], atomicLoad(&sHist[lid.x]));   // overwrites -> no clear needed
  }
}

var<workgroup> sScan: array<u32, WG>;
var<workgroup> wNumWG: u32;

// ── HIERARCHICAL SCAN (3 dispatches) ───────────────────────────────────────────────────────────
// A single-workgroup scan is pinned to ONE SM: 118 chunks x 16 barriers ~= 1900 serialised barriers,
// which is why the grid-stride version barely beat the 16-thread one. Split it so every SM works:
//   scanReduce  -- every chunk scanned IN PARALLEL, chunk totals parked past the histogram
//   scanChunks  -- one workgroup scans the (<=489) chunk totals
//   scanAdd     -- every chunk adds its offset, in parallel
// Chunk totals live in the tail of `hist` (it is sized for the worst case and mostly unused).
fn scanTail() -> u32 { return RADIX * u32(U_.cfg2.y); }

fn wgInclusiveScan(tid: u32) {                       // in-place Hillis-Steele over sScan[0..WG)
  for (var off = 1u; off < WG; off = off << 1u) {
    var add = 0u;
    if (tid >= off) { add = sScan[tid - off]; }
    workgroupBarrier();
    if (tid >= off) { sScan[tid] = sScan[tid] + add; }
    workgroupBarrier();
  }
}

@compute @workgroup_size(256)
fn scanReduce(@builtin(local_invocation_id) lid: vec3u, @builtin(workgroup_id) wid: vec3u) {
  let tid = lid.x;
  if (tid == 0u) { wNumWG = atomicLoad(&counter[1]); }
  let total = RADIX * workgroupUniformLoad(&wNumWG);
  let idx = wid.x * WG + tid;
  let v = select(0u, atomicLoad(&hist[idx]), idx < total);
  sScan[tid] = v;
  workgroupBarrier();
  wgInclusiveScan(tid);
  if (idx < total) { atomicStore(&hist[idx], sScan[tid] - v); }          // chunk-local exclusive
  if (tid == WG - 1u) { atomicStore(&hist[scanTail() + wid.x], sScan[tid]); }
}

@compute @workgroup_size(256)
fn scanChunks(@builtin(local_invocation_id) lid: vec3u) {
  let tid = lid.x;
  if (tid == 0u) { wNumWG = atomicLoad(&counter[1]); }
  let nChunks = (RADIX * workgroupUniformLoad(&wNumWG) + WG - 1u) / WG;
  let tail = scanTail();
  var running = 0u;
  var base = 0u;
  loop {
    if (base >= nChunks) { break; }
    let i = base + tid;
    let v = select(0u, atomicLoad(&hist[tail + i]), i < nChunks);
    sScan[tid] = v;
    workgroupBarrier();
    wgInclusiveScan(tid);
    if (i < nChunks) { atomicStore(&hist[tail + i], running + sScan[tid] - v); }
    let ct = sScan[WG - 1u];
    workgroupBarrier();
    running = running + ct;
    base = base + WG;
  }
}

@compute @workgroup_size(256)
fn scanAdd(@builtin(local_invocation_id) lid: vec3u, @builtin(workgroup_id) wid: vec3u) {
  let tid = lid.x;
  if (tid == 0u) { wNumWG = atomicLoad(&counter[1]); }
  let total = RADIX * workgroupUniformLoad(&wNumWG);
  let idx = wid.x * WG + tid;
  if (idx < total) {
    atomicStore(&hist[idx], atomicLoad(&hist[idx]) + atomicLoad(&hist[scanTail() + wid.x]));
  }
}

var<workgroup> sDigit: array<u32, WG>;
var<workgroup> sValid: array<u32, WG>;

@compute @workgroup_size(256)
fn radixScatter(@builtin(global_invocation_id) gid: vec3u,
                @builtin(local_invocation_id) lid: vec3u,
                @builtin(workgroup_id) wid: vec3u) {
  let n = atomicLoad(&counter[0]);
  let i = gid.x;
  let shift = u32(U_.cfg2.z);
  let valid = select(0u, 1u, i < n);
  sValid[lid.x] = valid;
  sDigit[lid.x] = select(0u, (keysIn[min(i, max(n, 1u) - 1u)] >> shift) & (RADIX - 1u), valid == 1u);
  workgroupBarrier();
  // one thread per digit walks the workgroup's items IN ORDER -> stable placement
  if (lid.x < RADIX) {
    let numWG = atomicLoad(&counter[1]);
    var out = atomicLoad(&hist[lid.x * numWG + wid.x]);
    for (var j = 0u; j < WG; j = j + 1u) {
      if (sValid[j] == 1u && sDigit[j] == lid.x) {
        let src = wid.x * WG + j;
        keysOut[out] = keysIn[src];
        valsOut[out] = valsIn[src];
        out = out + 1u;
      }
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// PASS 3 -- tile ranges from the sorted keys
// ─────────────────────────────────────────────────────────────────────────────
@compute @workgroup_size(256)
fn tileRanges(@builtin(global_invocation_id) gid: vec3u) {
  let n = atomicLoad(&counter[0]);
  let i = gid.x;
  if (i >= n) { return; }
  let tile = keysIn[i] >> DEPTH_BITS;
  if (i == 0u || (keysIn[i - 1u] >> DEPTH_BITS) != tile) { tileRange[tile].x = i; }
  if (i == n - 1u || (keysIn[i + 1u] >> DEPTH_BITS) != tile) { tileRange[tile].y = i + 1u; }
}

@compute @workgroup_size(256)
fn clearTiles(@builtin(global_invocation_id) gid: vec3u) {
  let t = gid.x;
  let nt = u32(U_.screen.z) * u32(U_.screen.w);
  if (t >= nt) { return; }
  tileRange[t] = vec2u(0u, 0u);
  if (t == 0u) { atomicStore(&counter[0], 0u); atomicStore(&counter[1], 1u); }
}

@compute @workgroup_size(256)
fn clearHist(@builtin(global_invocation_id) gid: vec3u) {
  let maxWG = u32(U_.cfg2.y);
  if (gid.x >= RADIX * maxWG) { return; }
  atomicStore(&hist[gid.x], 0u);
}

// ─────────────────────────────────────────────────────────────────────────────
// PASS 4 -- rasterise: ONE WORKGROUP PER TILE, cooperative shared-memory batching,
// front-to-back alpha with a WORKGROUP-WIDE early-out (the thing v1 could not express).
// ─────────────────────────────────────────────────────────────────────────────
var<workgroup> bXY: array<vec2f, WG>;
var<workgroup> bConicOpa: array<vec4f, WG>;
var<workgroup> bCol: array<vec4f, WG>;
var<workgroup> nDone: atomic<u32>;
var<workgroup> wRange: vec2u;      // broadcast so the loop bound is PROVABLY uniform (barriers need that)
var<workgroup> wAllDone: u32;

@compute @workgroup_size(16, 16, 1)
fn rasterize(@builtin(workgroup_id) wid: vec3u,
             @builtin(local_invocation_id) lid: vec3u,
             @builtin(local_invocation_index) li: u32) {
  let tilesX = u32(U_.screen.z);
  let tile = wid.y * tilesX + wid.x;
  let px = wid.x * TILE + lid.x;
  let py = wid.y * TILE + lid.y;
  let inb = px < u32(U_.screen.x) && py < u32(U_.screen.y);

  // A storage-buffer load is not provably uniform, so WGSL rejects barriers in a loop bounded by it.
  // workgroupUniformLoad broadcasts it (with a barrier) and GIVES the compiler that guarantee.
  if (li == 0u) { wRange = tileRange[tile]; wAllDone = 0u; }
  let range = workgroupUniformLoad(&wRange);

  var col = U_.bg.rgb;
  var T = 1.0;
  var done = !inb;
  let fx = f32(px) + 0.5; let fy = f32(py) + 0.5;

  var i = range.x;
  loop {
    if (i >= range.y) { break; }                        // uniform: range and i are uniform
    let batch = min(WG, range.y - i);
    if (li == 0u) { atomicStore(&nDone, 0u); }
    workgroupBarrier();
    if (li < batch) {                                   // cooperative prefetch into shared memory
      let p = proj[valsIn[i + li]];
      bXY[li] = p.xy;
      bConicOpa[li] = vec4f(p.conic, p.opa);
      bCol[li] = vec4f(p.col, p.radius);
    }
    workgroupBarrier();

    if (!done) {
      for (var j = 0u; j < batch; j = j + 1u) {
        let d = vec2f(fx, fy) - bXY[j];
        let R = bCol[j].w;
        if (dot(d, d) > R * R) { continue; }
        let c = bConicOpa[j];
        let g = d.x * d.x * c.x + 2.0 * d.x * d.y * c.y + d.y * d.y * c.z;
        if (g > 9.0) { continue; }
        let a = exp(-0.5 * g) * c.w;                    // the splat's OWN alpha = opacity * gaussian
        if (a < 0.004) { continue; }
        col = col + bCol[j].rgb * (a * T);              // contribution weighted by transmittance so far
        T = T * (1.0 - a);                              // decay by the splat's OWN alpha, NOT by a*T.
        if (T < 0.01) { done = true; break; }           // opaque: line of sight stops here
      }
    }
    i = i + batch;

    workgroupBarrier();                                 // workgroup-wide early-out: is EVERY pixel opaque?
    if (done) { atomicAdd(&nDone, 1u); }
    workgroupBarrier();
    if (li == 0u) { wAllDone = select(0u, 1u, atomicLoad(&nDone) == 256u); }
    let all = workgroupUniformLoad(&wAllDone);
    if (all == 1u) { break; }                           // uniform break -> the occluded tail is never loaded
  }

  if (inb) {
    textureStore(outTex, vec2i(i32(px), i32(py)), vec4f(clamp(col, vec3f(0.0), vec3f(1.0)), 1.0));
  }
}
