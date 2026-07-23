"""Minimal reader for .ksplat (mkkellogg GaussianSplats3D), compressionLevel 1.

Layout (verified against this file's byte budget):
  0      : file header (4096 B)   -> splatCount@16, compressionLevel@20 (uint16)
  4096   : section header (1024 B)-> bucketSize@8, bucketCount@12, bucketBlockSize@16(f32),
                                     compressionScaleRange@24, fullBucketCount@32, partialBucketCount@36
  5120   : section storage = [partial-bucket lengths | bucket centers | splat data]
Splat (24 B): pos 3xu16 (bucket-quantised), scale 3xf16, rot 4xf16, colour 4xu8.
Position decode: center[bucket] + (u16 - 32767) * (bucketBlockSize/2)/32767.
"""
import struct, numpy as np


def load_ksplat(path, full=False):
    with open(path, "rb") as f:
        data = f.read()
    if struct.unpack_from("<H", data, 20)[0] != 1:
        raise ValueError("only compressionLevel 1 is supported")
    N = struct.unpack_from("<I", data, 16)[0]
    S = 4096
    bucketSize = struct.unpack_from("<I", data, S + 8)[0]
    bucketCount = struct.unpack_from("<I", data, S + 12)[0]
    blockSize = struct.unpack_from("<f", data, S + 16)[0]
    compRange = struct.unpack_from("<I", data, S + 24)[0]
    fullBuckets = struct.unpack_from("<I", data, S + 32)[0]
    partialBuckets = struct.unpack_from("<I", data, S + 36)[0]

    store = S + 1024
    partialBytes = partialBuckets * 4
    centerBytes = bucketCount * 12
    nfull = fullBuckets * bucketSize
    target = N - nfull

    def read_partial(off):
        pl = np.frombuffer(data, np.uint32, partialBuckets, off)
        ok = pl.sum() == target and pl.max() <= bucketSize and pl.min() >= 1
        return pl if ok else None
    pl = read_partial(store); centersOff = store + partialBytes           # meta-first
    if pl is None:
        pl = read_partial(store + centerBytes); centersOff = store         # centers-first
    if pl is None:
        raise ValueError("could not locate the partial-bucket-length table")

    centers = np.frombuffer(data, np.float32, bucketCount * 3, centersOff).reshape(-1, 3)
    splatOff = store + partialBytes + centerBytes
    dt = np.dtype([("pos", "<u2", 3), ("scale", "<u2", 3), ("rot", "<u2", 4), ("col", "u1", 4)])
    sp = np.frombuffer(data, dt, N, splatOff)

    bidx = np.empty(N, np.int64)
    bidx[:nfull] = np.arange(nfull) // bucketSize
    bidx[nfull:] = np.repeat(fullBuckets + np.arange(partialBuckets), pl)
    factor = (blockSize / 2.0) / compRange
    pos = centers[bidx] + (sp["pos"].astype(np.float64) - compRange) * factor
    col = sp["col"][:, :3].astype(np.float32) / 255.0
    if full:
        opacity = sp["col"][:, 3].astype(np.float32) / 255.0            # alpha channel = per-splat opacity
        scale = sp["scale"].copy().view(np.float16).astype(np.float32)  # 3x half-float scales (linear)
        quat = sp["rot"].copy().view(np.float16).astype(np.float32)     # 4x half-float rotation quaternion
        return pos.astype(np.float32), col, opacity, scale, quat
    return pos.astype(np.float32), col


if __name__ == "__main__":
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else "E:/PythonChimera/WorldModel/training_data/real_data/stump/stump.ksplat"
    pos, col = load_ksplat(p)
    print(f"loaded {len(pos):,} splats")
    print(f"bbox min {pos.min(0).round(2)}  max {pos.max(0).round(2)}  size {(pos.max(0)-pos.min(0)).round(2)}")
    print(f"centroid {pos.mean(0).round(2)}  finite={np.isfinite(pos).all()}  mean colour {col.mean(0).round(3)}")
