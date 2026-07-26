// Chimera renderer v2 -- SPIKE host. Owns setup only; the frame loop is entirely GPU passes.
// Measures each pass with timestamp-query (no host-side guessing), which is the point of the spike.

const BUILD = 'v3.2-sun-controls';
const TILE = 16, WG = 256, RADIX_PASSES = 8, UNI_STRIDE = 256;
const MAX_PAIRS = 2_000_000;
const MAX_NUMWG = Math.ceil(MAX_PAIRS / WG);

const $ = (id) => document.getElementById(id);
const log = (m) => { $('log').textContent += m + '\n'; };

async function main() {
  if (!navigator.gpu) { log('WebGPU not available'); return; }
  const adapter = await navigator.gpu.requestAdapter({ powerPreference: 'high-performance' });
  const want = ['bgra8unorm-storage', 'timestamp-query'].filter(f => adapter.features.has(f));
  // the pipeline binds 10 storage buffers; the DEFAULT per-stage limit is 8, so it must be raised
  // explicitly (this adapter supports 16). Without it every pipeline silently fails to create.
  const device = await adapter.requestDevice({ requiredFeatures: want, requiredLimits: {
    maxStorageBuffersPerShaderStage: Math.min(12, adapter.limits.maxStorageBuffersPerShaderStage),
    maxStorageBufferBindingSize: Math.min(268435456, adapter.limits.maxStorageBufferBindingSize),
  }});
  const canTime = want.includes('timestamp-query');
  log(`build ${BUILD}`);
  log(`adapter: ${adapter.info?.vendor ?? '?'} / ${adapter.info?.architecture ?? '?'}  features: ${want.join(', ')}`);
  // WebGPU validation errors do NOT reach console.log -- surface them or debug blind
  let nerr = 0;
  device.addEventListener('uncapturederror', (e) => { if (nerr++ < 6) log('GPU ERROR: ' + e.error.message); });

  const term = new URLSearchParams(location.search).get('term') || 'aPlanet';
  const meta = await (await fetch(`data/${term}.json?v=` + Date.now(), { cache: 'no-store' })).json();
  const raw = await (await fetch(`data/${term}.bin?v=` + Date.now(), { cache: 'no-store' })).arrayBuffer();
  const N = meta.count;
  log(`${term}: ${N} splats, ${(raw.byteLength / 1e6).toFixed(2)} MB, radius ${meta.radius.toFixed(1)}`);

  // ── canvas at true 2K ──
  const canvas = $('cv');
  const W = 2560, H = 1440;
  canvas.width = W; canvas.height = H;
  const ctx = canvas.getContext('webgpu');
  ctx.configure({ device, format: 'bgra8unorm', alphaMode: 'opaque',
                  usage: GPUTextureUsage.STORAGE_BINDING | GPUTextureUsage.RENDER_ATTACHMENT | GPUTextureUsage.COPY_SRC });
  const tilesX = Math.ceil(W / TILE), tilesY = Math.ceil(H / TILE), nTiles = tilesX * tilesY;
  log(`raster ${W}x${H}, tiles ${tilesX}x${tilesY} = ${nTiles}`);

  // ── buffers ──
  const SB = GPUBufferUsage.STORAGE, CD = GPUBufferUsage.COPY_DST, CS = GPUBufferUsage.COPY_SRC;
  const mk = (size, usage) => device.createBuffer({ size, usage });
  const splatBuf = mk(raw.byteLength, SB | CD);
  device.queue.writeBuffer(splatBuf, 0, raw);                       // uploaded ONCE -- resident in VRAM
  const projBuf = mk(N * 48, SB | CS);
  const keysA = mk(MAX_PAIRS * 4, SB), valsA = mk(MAX_PAIRS * 4, SB);
  const keysB = mk(MAX_PAIRS * 4, SB), valsB = mk(MAX_PAIRS * 4, SB);
  const counter = mk(16, SB | CD | CS);
  const hist = mk((16 * MAX_NUMWG + 1024) * 4, SB);   // + tail for hierarchical-scan chunk sums
  const tileRange = mk(nTiles * 8, SB);
  // WebGPU forbids a buffer being BOTH writable-storage and an indirect source in one sync scope,
  // so the GPU writes dispatch args to a storage buffer and we copy them into the indirect buffer.
  const dispatchArgs = mk(32, SB | CS);
  const indirect = mk(32, GPUBufferUsage.INDIRECT | CD);
  const uni = mk(UNI_STRIDE * RADIX_PASSES, GPUBufferUsage.UNIFORM | CD);

  const code = await (await fetch('splat.wgsl?v=' + Date.now(), { cache: 'no-store' })).text();
  const mod = device.createShaderModule({ code });
  const info = await mod.getCompilationInfo();
  const errs = info.messages.filter(m => m.type === 'error');
  if (errs.length) { errs.forEach(e => log(`WGSL ${e.lineNum}: ${e.message}`)); return; }

  const layout = device.createBindGroupLayout({ entries: [
    { binding: 0, visibility: GPUShaderStage.COMPUTE, buffer: { type: 'uniform', hasDynamicOffset: true } },
    { binding: 1, visibility: GPUShaderStage.COMPUTE, buffer: { type: 'read-only-storage' } },
    ...[2, 3, 4, 5, 6, 7, 8, 9].map(b => ({ binding: b, visibility: GPUShaderStage.COMPUTE, buffer: { type: 'storage' } })),
    { binding: 10, visibility: GPUShaderStage.COMPUTE, storageTexture: { access: 'write-only', format: 'bgra8unorm' } },
    { binding: 11, visibility: GPUShaderStage.COMPUTE, buffer: { type: 'storage' } },
  ]});
  const pipeOf = {};
  for (const ep of ['preprocess', 'setupDispatch', 'radixHistogram', 'radixScatter',
                    'tileRanges', 'clearTiles', 'clearHist', 'rasterize',
                    'scanReduce', 'scanChunks', 'scanAdd'])
    pipeOf[ep] = device.createComputePipeline({
      layout: device.createPipelineLayout({ bindGroupLayouts: [layout] }),
      compute: { module: mod, entryPoint: ep } });

  // two bind groups: the radix ping-pong swaps in/out each pass (8 passes = even = ends back in A)
  const bg = (kIn, vIn, kOut, vOut, view) => device.createBindGroup({ layout, entries: [
    { binding: 0, resource: { buffer: uni, size: UNI_STRIDE } },
    { binding: 1, resource: { buffer: splatBuf } }, { binding: 2, resource: { buffer: projBuf } },
    { binding: 3, resource: { buffer: kIn } }, { binding: 4, resource: { buffer: vIn } },
    { binding: 5, resource: { buffer: kOut } }, { binding: 6, resource: { buffer: vOut } },
    { binding: 7, resource: { buffer: counter } }, { binding: 8, resource: { buffer: hist } },
    { binding: 9, resource: { buffer: tileRange } }, { binding: 10, resource: view },
    { binding: 11, resource: { buffer: dispatchArgs } } ]});

  // ── timing ──
  const NQ = 16;
  const qset = canTime ? device.createQuerySet({ type: 'timestamp', count: NQ }) : null;
  const qbuf = canTime ? mk(NQ * 8, CS | GPUBufferUsage.QUERY_RESOLVE) : null;
  const readPool = [];
  const ts = (a, b) => canTime ? { querySet: qset, beginningOfPassWriteIndex: a, endOfPassWriteIndex: b } : undefined;
  const PASSES = ['preprocess', 'sort', 'tiles', 'raster', 'clr', 'hist', 'scan', 'scat'];
  let last = {}, frames = 0, tAcc = 0, tPrev = performance.now();

  // ── camera ──
  const fov = 1.0472;                                    // 60deg, matches FirstPersonCamera
  const focal = H / (2 * Math.tan(fov / 2));
  let azim = 0.6, elev = 0.25, radius = meta.cam_distance, spin = true, cullOn = true, scaleMul = 1.0, pan = 0.0, opaMul = 1.0, showAtm = true, forceIso = false, showSurf = true, flatMin = 0.22, backMargin = 0.30, normOn = true, depthEps = 3.0, covK = 1.0;   // measured: thicker discs halve the limb anomaly, at no fps cost
  // SUN: a world-space direction toward the star, plus an ambient floor. `sunOn=false` sends
  // ambient < 0, which the shader reads as "unlit" -- so the default is byte-identical to before
  // and lighting can be switched off to compare.
  let sunOn = true, sunAzim = 0.9, sunElev = 0.15, ambient = 0.06, sunSpin = false;
  const uniData = new Float32Array(44);
  function writeUniforms() {
    const ce = Math.cos(elev);
    const P = [radius * ce * Math.sin(azim), -radius * ce * Math.cos(azim), radius * Math.sin(elev)];
    const n = Math.hypot(...P) || 1, F0 = P.map(v => -v / n);     // look at the origin
    const wup = [0, 0, 1];
    let r0 = [F0[1]*wup[2]-F0[2]*wup[1], F0[2]*wup[0]-F0[0]*wup[2], F0[0]*wup[1]-F0[1]*wup[0]];
    const r0l = Math.hypot(...r0) || 1; r0 = r0.map(v => v / r0l);
    // PAN: tilt the look direction off the origin so the planet centre leaves the screen centre
    const F1 = F0.map((v, k) => v + r0[k] * Math.tan(pan));
    const f1l = Math.hypot(...F1) || 1; const F = F1.map(v => v / f1l);
    let r = [F[1] * wup[2] - F[2] * wup[1], F[2] * wup[0] - F[0] * wup[2], F[0] * wup[1] - F[1] * wup[0]];
    const rl = Math.hypot(...r) || 1; r = r.map(v => v / rl);
    const u = [r[1] * F[2] - r[2] * F[1], r[2] * F[0] - r[0] * F[2], r[0] * F[1] - r[1] * F[0]];
    const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
    const rows = [[...r, -dot(r, P)], [...u, -dot(u, P)], [-F[0], -F[1], -F[2], dot(F, P)]];
    uniData.set([...rows[0], ...rows[1], ...rows[2],
                 W, H, tilesX, tilesY,
                 focal, 1.0, radius * 6, N,
                 MAX_PAIRS, MAX_NUMWG, 0, scaleMul,
                 0.015, 0.015, 0.04, opaMul,
                 showAtm?1:0, forceIso?1:0, showSurf?1:0, flatMin,
                 backMargin, normOn?1:0, depthEps, 0,
                 covK, 0, 0, 0,
                 Math.cos(sunElev)*Math.cos(sunAzim), Math.cos(sunElev)*Math.sin(sunAzim),
                 Math.sin(sunElev), sunOn ? ambient : -1]);
    for (let p = 0; p < RADIX_PASSES; p++) {              // one slot per radix pass; only the shift differs
      uniData[22] = p * 4;
      device.queue.writeBuffer(uni, p * UNI_STRIDE, uniData);
    }
  }

  let grabBuf = null, grabPending = false;
  function frame() {
    if (spin) azim += 0.004;
    // The sun orbiting is not the camera orbiting: this walks the TERMINATOR across the surface
    // while the body stays put, which is the only way to see day break on a fixed feature.
    if (sunSpin) { sunAzim += 0.006; if (sunAzim > 6.283) sunAzim -= 6.283; }
    writeUniforms();
    const tex = ctx.getCurrentTexture();
    const view = tex.createView();
    const A = bg(keysA, valsA, keysB, valsB, view), B = bg(keysB, valsB, keysA, valsA, view);
    const enc = device.createCommandEncoder();

    let p = enc.beginComputePass();                       // clear
    p.setPipeline(pipeOf.clearTiles); p.setBindGroup(0, A, [0]); p.dispatchWorkgroups(Math.ceil(nTiles / WG));
    p.setPipeline(pipeOf.clearHist); p.dispatchWorkgroups(Math.ceil(16 * MAX_NUMWG / WG));
    p.end();

    p = enc.beginComputePass({ timestampWrites: ts(0, 1) });   // preprocess
    p.setPipeline(pipeOf.preprocess); p.setBindGroup(0, A, [0]); p.dispatchWorkgroups(Math.ceil(N / WG));
    p.end();

    p = enc.beginComputePass();
    p.setPipeline(pipeOf.setupDispatch); p.setBindGroup(0, A, [0]); p.dispatchWorkgroups(1);
    p.end();
    enc.copyBufferToBuffer(dispatchArgs, 0, indirect, 0, 32);   // storage -> indirect, outside any pass

    // sort: pass 0 is split into separately-TIMED sub-passes so we can see where the ms actually go
    for (let i = 0; i < RADIX_PASSES; i++) {
      const g = (i % 2 === 0) ? A : B, off = i * UNI_STRIDE;
      if (i === 0) {
        p = enc.beginComputePass({ timestampWrites: ts(8, 9) });
        p.setPipeline(pipeOf.clearHist); p.setBindGroup(0, g, [off]); p.dispatchWorkgroups(Math.ceil(16 * MAX_NUMWG / WG)); p.end();
        p = enc.beginComputePass({ timestampWrites: ts(10, 11) });
        p.setPipeline(pipeOf.radixHistogram); p.setBindGroup(0, g, [off]); p.dispatchWorkgroupsIndirect(indirect, 0); p.end();
        p = enc.beginComputePass({ timestampWrites: ts(12, 13) });
        p.setPipeline(pipeOf.scanReduce); p.setBindGroup(0, g, [off]); p.dispatchWorkgroupsIndirect(indirect, 16);
        p.setPipeline(pipeOf.scanChunks); p.dispatchWorkgroups(1);
        p.setPipeline(pipeOf.scanAdd);    p.dispatchWorkgroupsIndirect(indirect, 16); p.end();
        p = enc.beginComputePass({ timestampWrites: ts(14, 15) });
        p.setPipeline(pipeOf.radixScatter); p.setBindGroup(0, g, [off]); p.dispatchWorkgroupsIndirect(indirect, 0); p.end();
      } else {
        p = enc.beginComputePass();
        p.setPipeline(pipeOf.clearHist); p.setBindGroup(0, g, [off]); p.dispatchWorkgroups(Math.ceil(16 * MAX_NUMWG / WG));
        p.setPipeline(pipeOf.radixHistogram); p.setBindGroup(0, g, [off]); p.dispatchWorkgroupsIndirect(indirect, 0);
        p.setPipeline(pipeOf.scanReduce); p.setBindGroup(0, g, [off]); p.dispatchWorkgroupsIndirect(indirect, 16);
        p.setPipeline(pipeOf.scanChunks); p.dispatchWorkgroups(1);
        p.setPipeline(pipeOf.scanAdd);    p.dispatchWorkgroupsIndirect(indirect, 16);
        p.setPipeline(pipeOf.radixScatter); p.setBindGroup(0, g, [off]); p.dispatchWorkgroupsIndirect(indirect, 0);
        p.end();
      }
    }

    p = enc.beginComputePass({ timestampWrites: ts(4, 5) });   // tile ranges
    p.setPipeline(pipeOf.tileRanges); p.setBindGroup(0, A, [0]); p.dispatchWorkgroupsIndirect(indirect, 0);
    p.end();

    p = enc.beginComputePass({ timestampWrites: ts(6, 7) });   // rasterise: one workgroup per tile
    p.setPipeline(pipeOf.rasterize); p.setBindGroup(0, A, [0]); p.dispatchWorkgroups(tilesX, tilesY);
    p.end();

    if (grabPending) {
      if (!grabBuf) grabBuf = mk(W * H * 4, CD | GPUBufferUsage.MAP_READ);
      enc.copyTextureToBuffer({ texture: tex }, { buffer: grabBuf, bytesPerRow: W * 4 }, [W, H, 1]);
    }
    let rb = null;
    if (canTime) {
      enc.resolveQuerySet(qset, 0, NQ, qbuf, 0);
      rb = readPool.pop() || mk(NQ * 8, CD | GPUBufferUsage.MAP_READ);
      enc.copyBufferToBuffer(qbuf, 0, rb, 0, NQ * 8);
    }
    device.queue.submit([enc.finish()]);

    if (rb) rb.mapAsync(GPUMapMode.READ).then(() => {
      const t = new BigUint64Array(rb.getMappedRange()).slice();
      rb.unmap(); readPool.push(rb);
      const ms = (a, b) => Number(t[b] - t[a]) / 1e6;
      last = { preprocess: ms(0, 1), tiles: ms(4, 5), raster: ms(6, 7),
               clr: ms(8, 9), hist: ms(10, 11), scan: ms(12, 13), scat: ms(14, 15) };
      last.sort = (last.clr + last.hist + last.scan + last.scat) * 8;   // pass 0 x 8 identical passes
      last.gpu = last.preprocess + last.sort + last.tiles + last.raster;
    }).catch(() => {});

    frames++;
    const now = performance.now(); tAcc += now - tPrev; tPrev = now;
    if (tAcc > 400) {
      const fps = frames * 1000 / tAcc;
      const budget = 1000 / 120;
      const parts = PASSES.map(k => `${k} ${(last[k] ?? 0).toFixed(2)}`).join('  ');
      $('hud').innerHTML =
        `<b>${fps.toFixed(1)} fps</b> &nbsp; frame ${(tAcc / frames).toFixed(2)} ms &nbsp;` +
        `<span class="${(last.gpu ?? 99) <= budget ? 'ok' : 'no'}">GPU ${(last.gpu ?? 0).toFixed(2)} ms ` +
        `(120fps budget ${budget.toFixed(2)})</span> <span class="d">${BUILD}</span><br><span class="d">${parts} &nbsp; ${W}x${H} &nbsp; ${N} splats</span>`;
      frames = 0; tAcc = 0;
    }
    requestAnimationFrame(frame);
  }

  // controls
  let drag = false, lx = 0, ly = 0;
  canvas.onpointerdown = e => { drag = true; lx = e.clientX; ly = e.clientY; spin = false; canvas.setPointerCapture(e.pointerId); };
  canvas.onpointerup = () => { drag = false; };
  canvas.onpointermove = e => { if (!drag) return; azim -= (e.clientX - lx) * 0.005; elev = Math.max(-1.4, Math.min(1.4, elev + (e.clientY - ly) * 0.005)); lx = e.clientX; ly = e.clientY; };
  canvas.onwheel = e => { e.preventDefault(); radius = Math.max(meta.radius * 1.2, Math.min(meta.cam_distance * 8, radius * (1 + Math.sign(e.deltaY) * 0.1))); };
  $('spin').onclick = () => { spin = !spin; };

  // debug probe: read the GPU-side counters + a slice of the projected data
  window.__dbg = async () => {
    const rb = device.createBuffer({ size: 16, usage: CD | GPUBufferUsage.MAP_READ });
    const pb = device.createBuffer({ size: 48 * 4, usage: CD | GPUBufferUsage.MAP_READ });
    const e = device.createCommandEncoder();
    e.copyBufferToBuffer(counter, 0, rb, 0, 16);
    e.copyBufferToBuffer(projBuf, 0, pb, 0, 48 * 4);
    device.queue.submit([e.finish()]);
    await rb.mapAsync(GPUMapMode.READ); await pb.mapAsync(GPUMapMode.READ);
    const c = new Uint32Array(rb.getMappedRange()).slice();
    const pr = new Float32Array(pb.getMappedRange()).slice();
    rb.unmap(); pb.unmap();
    return { pairs: c[0], numWG: c[1], proj0: Array.from(pr.slice(0, 12)).map(v => +v.toFixed(2)) };
  };
  // magnified view of a region, drawn into a visible 2D canvas so the artifact can be SEEN
  window.__zoomView = async (half = 70, factor = 5, offx = 0, offy = 0) => {
    grabPending = true; await new Promise(r => setTimeout(r, 120)); grabPending = false;
    await grabBuf.mapAsync(GPUMapMode.READ);
    const d = new Uint8Array(grabBuf.getMappedRange()).slice(); grabBuf.unmap();
    let z = document.getElementById('zoomcv');
    if (!z) { z = document.createElement('canvas'); z.id = 'zoomcv';
              z.style.cssText = 'display:block;margin:10px 14px;border:1px solid #2c3850;border-radius:8px;image-rendering:pixelated';
              document.getElementById('wrap').appendChild(z); }
    z.width = half * 2 * factor; z.height = half * 2 * factor;
    const g2 = z.getContext('2d');
    const img = g2.createImageData(half * 2, half * 2);
    for (let y = 0; y < half * 2; y++) for (let x = 0; x < half * 2; x++) {
      const sxp = (W / 2 + offx - half + x) | 0, syp = (H / 2 + offy - half + y) | 0;
      const i = (syp * W + sxp) * 4, o = (y * half * 2 + x) * 4;
      img.data[o] = d[i + 2]; img.data[o + 1] = d[i + 1]; img.data[o + 2] = d[i]; img.data[o + 3] = 255;
    }
    const t = document.createElement('canvas'); t.width = half * 2; t.height = half * 2;
    t.getContext('2d').putImageData(img, 0, 0);
    g2.imageSmoothingEnabled = false; g2.drawImage(t, 0, 0, z.width, z.height);
    return { shown: `${half*2}x${half*2}px at ${factor}x around screen centre` };
  };
  // TEMPORAL probe -- the artifact is on the SPINNING object, so a still frame cannot show it.
  // Accumulates per-pixel mean/variance over K frames WHILE SPINNING (Welford-style sums, O(1) memory),
  // then reports where the temporal variance is anomalous versus its own neighbourhood.
  window.__temporal = async (K = 12, half = 620) => {
    const w = half * 2, n = w * w;
    const sum = new Float64Array(n), sq = new Float64Array(n);
    const wasSpin = spin; spin = true;
    for (let k = 0; k < K; k++) {
      grabPending = true; await new Promise(r => setTimeout(r, 70)); grabPending = false;
      await grabBuf.mapAsync(GPUMapMode.READ);
      const d = new Uint8Array(grabBuf.getMappedRange());
      for (let y = 0; y < w; y++) {
        const sy2 = (H / 2 - half + y) | 0;
        for (let x = 0; x < w; x++) {
          const i = (sy2 * W + ((W / 2 - half + x) | 0)) * 4;
          const v = d[i] + d[i + 1] + d[i + 2];
          const o = y * w + x; sum[o] += v; sq[o] += v * v;
        }
      }
      grabBuf.unmap();
      await new Promise(r => setTimeout(r, 30));
    }
    spin = wasSpin;
    const sd = new Float32Array(n);
    for (let o = 0; o < n; o++) { const m = sum[o] / K; sd[o] = Math.sqrt(Math.max(0, sq[o] / K - m * m)); }
    // anomaly = temporal sd minus the median sd of a ring 24px out
    const hits = [];
    for (let y = 30; y < w - 30; y += 3) for (let x = 30; x < w - 30; x += 3) {
      const c = sd[y * w + x];
      const ring = [sd[y*w+x-24], sd[y*w+x+24], sd[(y-24)*w+x], sd[(y+24)*w+x],
                    sd[(y-17)*w+x-17], sd[(y+17)*w+x+17], sd[(y-17)*w+x+17], sd[(y+17)*w+x-17]]
                    .sort((a,b)=>a-b);
      const med = (ring[3] + ring[4]) / 2;
      const dev = c - med;
      if (Math.abs(dev) > 6) {
        const gx = x - half, gy = y - half;
        let f = hits.find(h => Math.abs(h.gx-gx) < 50 && Math.abs(h.gy-gy) < 50);
        if (f) { f.n++; if (Math.abs(dev) > Math.abs(f.dev)) { f.gx=gx; f.gy=gy; f.dev=+dev.toFixed(1); f.sd=+c.toFixed(1); f.ring=+med.toFixed(1); } }
        else hits.push({ gx, gy, n:1, dev:+dev.toFixed(1), sd:+c.toFixed(1), ring:+med.toFixed(1) });
      }
    }
    hits.sort((a,b) => Math.abs(b.dev) - Math.abs(a.dev));
    let mx = 0, mo = 0; for (let o = 0; o < n; o++) if (sd[o] > mx) { mx = sd[o]; mo = o; }
    return { frames: K, region: `${w}x${w} around screen centre`,
             maxTemporalSd: +mx.toFixed(1), maxAt: { gx: (mo % w) - half, gy: ((mo / w) | 0) - half },
             nHits: hits.length, top: hits.slice(0, 6) };
  };
  // RADIAL PROFILE -- averages brightness in rings around the disk centre. A dark rim shows as a
  // dip BELOW the interior level before the fall-off to background, so it is unambiguous in numbers.
  window.__radial = async () => {
    grabPending = true; await new Promise(r => setTimeout(r, 120)); grabPending = false;
    await grabBuf.mapAsync(GPUMapMode.READ);
    const d = new Uint8Array(grabBuf.getMappedRange()).slice(); grabBuf.unmap();
    let minX=W,maxX=0,minY=H,maxY=0;
    for (let y=0;y<H;y+=2) for (let x=0;x<W;x+=2){const i=(y*W+x)*4;
      if (d[i]+d[i+1]+d[i+2] > 60){ if(x<minX)minX=x; if(x>maxX)maxX=x; if(y<minY)minY=y; if(y>maxY)maxY=y; } }
    const cx=(minX+maxX)/2, cy=(minY+maxY)/2, R=Math.min((maxX-minX),(maxY-minY))/2;
    const NB = 40, sum = new Float64Array(NB), cnt = new Float64Array(NB);
    for (let y=Math.max(0,cy-R*1.15|0); y<Math.min(H,cy+R*1.15); y++)
      for (let x=Math.max(0,cx-R*1.15|0); x<Math.min(W,cx+R*1.15); x++) {
        const rr = Math.hypot(x-cx, y-cy)/R; if (rr >= 1.14) continue;
        const b = Math.floor(rr/1.14*NB); const i=(y*W+x)*4;
        sum[b] += d[i]+d[i+1]+d[i+2]; cnt[b]++;
      }
    const prof = []; for (let b=0;b<NB;b++) prof.push(+(sum[b]/Math.max(1,cnt[b])).toFixed(1));
    // interior reference = median of bins 10..28 ; find the deepest dip in the limb bins 28..37
    const interior = [...prof.slice(10,29)].sort((a,b)=>a-b)[9];
    let dip = 0, dipAt = 0;
    for (let b=28;b<38;b++){ const above = Math.max(prof[b-1], prof[b+1]||0);
      if (prof[b] < prof[b-1] && above - prof[b] > dip) { dip = above - prof[b]; dipAt = b; } }
    return { diskR: Math.round(R), interior: +interior.toFixed(1),
             rimDip: +dip.toFixed(1), rimDipAtRadius: +(dipAt/NB*1.14).toFixed(2),
             profileFromR070: prof.slice(24,38) };
  };
  window.__pan = (v) => { pan = v; return pan; };
  window.__scale = (v) => { scaleMul = v; return scaleMul; };
  window.__opa = (v) => { opaMul = v; return opaMul; };
  window.__eps = (v) => { depthEps = v; return depthEps; };
  window.__norm = (v) => { normOn = !!v; return normOn; };
  window.__elev = (v) => { elev = v; return elev; };
  window.__margin = (v) => { backMargin = v; return backMargin; };
  window.__cov = (v) => { covK = v; return covK; };
  window.__flat = (v) => { flatMin = v; return flatMin; };
  window.__atm = (v) => { showAtm = !!v; return showAtm; };
  window.__iso = (v) => { forceIso = !!v; return forceIso; };
  window.__surf = (v) => { showSurf = !!v; return showSurf; };
  window.__cull = (v) => { cullOn = !!v; return cullOn; };
  window.__spin = (v) => { spin = !!v; return spin; };
  window.__sun = (v) => { sunOn = !!v; return sunOn; };
  window.__sunspin = (v) => { sunSpin = !!v; return sunSpin; };
  window.__sunstate = () => ({ on: sunOn, spin: sunSpin, azim: sunAzim, elev: sunElev, ambient });
  window.__sunazim = (v) => { sunAzim = v; return sunAzim; };
  window.__sunelev = (v) => { sunElev = v; return sunElev; };
  window.__ambient = (v) => { ambient = v; return ambient; };
  // THE TERMINATOR PROBE -- the renderer's own answer to fields.py L3. Walks the lit disc and
  // reports what fraction of the visible surface is above half brightness. L3 measures 50.2% of a
  // SPHERE lit; the visible hemisphere of a sphere lit from the side is likewise half. Two
  // messengers, one law -- if they disagree, one of them is wrong.
  window.__terminator = async () => {
    grabPending = true; await new Promise(r => setTimeout(r, 120)); grabPending = false;
    await grabBuf.mapAsync(GPUMapMode.READ);
    const d = new Uint8Array(grabBuf.getMappedRange()).slice(); grabBuf.unmap();
    const bg = [d[0], d[1], d[2]];
    let onDisc = 0, bright = 0, maxL = 0, cols = [];
    for (let y = 0; y < H; y += 2) for (let x = 0; x < W; x += 2) {
      const i = (y * W + x) * 4;
      const dev = Math.abs(d[i]-bg[0]) + Math.abs(d[i+1]-bg[1]) + Math.abs(d[i+2]-bg[2]);
      if (dev < 12) continue;                       // background, not the body
      const L = 0.114*d[i] + 0.587*d[i+1] + 0.299*d[i+2];   // bgra8
      onDisc++; maxL = Math.max(maxL, L); cols.push([x, L]);
    }
    for (const [, L] of cols) if (L > maxL * 0.5) bright++;
    return { onDisc, litFraction: onDisc ? +(bright / onDisc).toFixed(4) : 0,
             maxLuma: +maxL.toFixed(1), sunOn, ambient,
             sun: [+Math.cos(sunElev)*Math.cos(sunAzim), +Math.cos(sunElev)*Math.sin(sunAzim),
                   +Math.sin(sunElev)].map(v => +v.toFixed(3)) };
  };
  window.__grab = async () => {
    grabPending = true; await new Promise(r => setTimeout(r, 120)); grabPending = false;
    await grabBuf.mapAsync(GPUMapMode.READ);
    const d = new Uint8Array(grabBuf.getMappedRange()).slice(); grabBuf.unmap();
    // bgra8: find the disk, then dark pixels well inside it
    let minX = W, maxX = 0, minY = H, maxY = 0;
    for (let y = 0; y < H; y += 2) for (let x = 0; x < W; x += 2) {
      const i = (y * W + x) * 4, s = d[i] + d[i+1] + d[i+2];
      if (s > 60) { if (x<minX)minX=x; if (x>maxX)maxX=x; if (y<minY)minY=y; if (y>maxY)maxY=y; } }
    if (maxX <= minX) return { error: 'no lit pixels' };
    const cx=(minX+maxX)/2, cy=(minY+maxY)/2, rx=(maxX-minX)/2, ry=(maxY-minY)/2;
    const cl = [];
    for (let y = minY; y <= maxY; y++) for (let x = minX; x <= maxX; x++) {
      const nx=(x-cx)/rx, ny=(y-cy)/ry; const rr = nx*nx+ny*ny; if (rr > 0.85) continue;
      const i=(y*W+x)*4, s=d[i]+d[i+1]+d[i+2];
      if (s > 34) continue;
      let f = cl.find(c => Math.abs(c.x-x) < 30 && Math.abs(c.y-y) < 30);
      if (f) { f.n++; } else cl.push({ x, y, n:1, rNorm:+Math.sqrt(rr).toFixed(2) });
    }
    // bgra8 -> rgb helper
    const px = (x, y) => { const i = ((y|0) * W + (x|0)) * 4; return [d[i+2], d[i+1], d[i]]; };
    // horizontal scanline across the disk centre
    const scan = [];
    for (let k = -10; k <= 10; k++) scan.push({ f: +(k/10).toFixed(1), rgb: px(cx + k*rx/10.5, cy) });
    // Strongest LOCAL ANOMALY anywhere on the disk (brighter OR darker than a ring 20px out).
    // A "lens"/colour-dominance blob shows up here even when the centre-only probe reads flat.
    const spots = [];
    for (let y = Math.round(cy-ry*0.85); y < cy+ry*0.85; y += 3)
      for (let x = Math.round(cx-rx*0.85); x < cx+rx*0.85; x += 3) {
        const nx=(x-cx)/rx, ny=(y-cy)/ry; const rr = nx*nx+ny*ny; if (rr > 0.72) continue;
        const c = px(x,y), cs = c[0]+c[1]+c[2];
        const ringv = [px(x-20,y),px(x+20,y),px(x,y-20),px(x,y+20),
                       px(x-14,y-14),px(x+14,y+14),px(x-14,y+14),px(x+14,y-14)]
                       .map(p=>p[0]+p[1]+p[2]).sort((a,b)=>a-b);
        const ring = (ringv[3]+ringv[4])/2;                       // median of the 8-ring
        const dev = cs - ring;
        if (Math.abs(dev) > 25) {
          let f = spots.find(s => Math.abs(s.x-x)<45 && Math.abs(s.y-y)<45);
          if (f) { f.n++; if (Math.abs(dev) > Math.abs(f.dev)) { f.x=x; f.y=y; f.dev=Math.round(dev); f.rgb=c; } }
          else spots.push({ x, y, n:1, dev:Math.round(dev), rgb:c,
                            dxFromCentre:x-Math.round(cx), dyFromCentre:y-Math.round(cy),
                            rNorm:+Math.sqrt(rr).toFixed(2) });
        }
      }
    // brightness map around the SCREEN centre (a 16px tile corner) -- 40x40 px, sampled every 2
    const map = [];
    for (let y = H/2 - 20; y < H/2 + 20; y += 2) {
      let row = '';
      for (let x = W/2 - 20; x < W/2 + 20; x += 2) { const c = px(x,y); row += String(Math.round((c[0]+c[1]+c[2])/3)).padStart(4); }
      map.push(row);
    }
    // GRAININESS vs radius: high-frequency energy in a 48px window (pixel minus 5x5 local mean).
    // If individual splats are resolvable somewhere, that is where this spikes.
    const grain = [];
    for (const f of [0.0, 0.2, 0.4, 0.6, 0.8]) {
      const ox = Math.round(cx + f * rx * 0.7), oy = Math.round(cy + f * ry * 0.7);
      let n = 0, s2 = 0, mean = 0;
      const vals = [];
      for (let y = oy - 24; y < oy + 24; y++) for (let x = ox - 24; x < ox + 24; x++) {
        let acc = 0; for (let j = -2; j <= 2; j++) for (let i = -2; i <= 2; i++) { const q = px(x+i, y+j); acc += q[0]+q[1]+q[2]; }
        const c = px(x,y); const hp = (c[0]+c[1]+c[2]) - acc/25;
        vals.push(hp); mean += hp; n++;
      }
      mean /= n; for (const v of vals) s2 += (v-mean)*(v-mean);
      grain.push({ r: f, rms: +Math.sqrt(s2/n).toFixed(2) });
    }
    return { disk:{cx,cy,rx:Math.round(rx),ry:Math.round(ry)}, grain,
             centre: px(cx,cy), screenCentre: px(W/2, H/2), map, scan,
             nSpots: spots.length, spots: spots.sort((a,b)=>(b.ring-b.cs)-(a.ring-a.cs)).slice(0,6) };
  };
  requestAnimationFrame(frame);
}
main().catch(e => log('ERROR: ' + (e.stack || e)));
