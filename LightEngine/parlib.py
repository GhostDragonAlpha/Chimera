"""parlib -- reusable on-GPU parallel primitives (operator directive, MASTER_LIST §12).

Operator rule: EVERY build is multi-threaded by default; if the primitive is missing,
BUILD IT ONCE and reuse it. This module IS that build-once layer for data-parallel
primitives. Do NOT hand-roll sort/scan in feature code -- compose from here instead.

Off-the-shelf decision (measured 2026-08-23, continuation-5): repo python has CuPy
14.1.1; its ``ndarray.argsort(kind='stable')`` is a GPU-resident compiled core kernel
(verified behaviorally: bit-equal permutation to numpy argsort kind='stable' incl. ties)
and ``cp.cumsum`` is the on-device prefix sum. CUB via nvcc (CUDA v12.8, path measured in
MASTER_LIST §12) remains the documented fallback ONLY for segmented sort / tighter perf.

Primitives (the standard for all future data-parallel builds):
  stable_sort_by_key(keys, *vals) -> (perm, *reordered)
      keys: 1-D int64 (host or device). perm = cp.argsort(kind='stable') on the keys
      (= CUB StableRadixSort-equivalent behavior); equal keys keep original order.
  parallel_scan(x, mode)        -> 1-D array, same dtype/shape as x
      mode='inclusive' -> prefix sums incl. last element (= CUB DeviceScan inclusive).
      mode='exclusive' -> prefix sums excl. last (out[i] = sum(x[:i])).

Returns CuPy DEVICE arrays (GPU-resident pipeline; the octree builder and any consumer
stay on-device until a final host copy is explicitly requested by the caller).

Self-test:  C:/Python314/python LightEngine/parlib.py   (seeded random data, numpy referee)
"""
from __future__ import annotations

import numpy as np
import cupy as cp


def _as_1d_int64(a):
    a = cp.asarray(a, dtype=np.int64) if isinstance(a, cp.ndarray) else \
        np.ascontiguousarray(a).astype(np.int64, copy=False)
    if a.ndim != 1:
        raise ValueError("parlib primitives are 1-D only")
    return a


def _as_1d_num(a):
    a = cp.asarray(a)
    if a.ndim != 1:
        raise ValueError("parlib primitives are 1-D only")
    if a.dtype not in (np.int64, np.float32, np.float64):
        raise TypeError(f"parallel_scan supports int64/float32/float64, got {a.dtype}")
    return a


def stable_sort_by_key(keys, *vals):
    """Stable on-GPU sort of ``keys`` carrying ``vals`` along.

    Returns (perm, v0', v1', ...) where keys[perm] is non-decreasing and equal keys
    preserve original relative order; vi' = vals_i[perm].
    """
    k = _as_1d_int64(keys)
    perm = cp.argsort(k, kind='stable')
    out = [perm]
    for v in vals:
        v = cp.asarray(v)
        if v.shape != (k.shape[0],):
            raise ValueError("carried value must be 1-D with len == len(keys)")
        out.append(v[perm])
    return tuple(out)


def parallel_scan(x, mode='exclusive'):
    """On-GPU prefix sum. 'inclusive': out[i]=sum(x[:i+1]). 'exclusive': out[i]=sum(x[:i])."""
    x = _as_1d_num(x)
    n = x.shape[0]
    if n == 0:
        return cp.empty(0, dtype=x.dtype)
    inc = cp.cumsum(x)                       # inclusive, on-device
    if mode == 'inclusive':
        return inc
    if mode != 'exclusive':
        raise ValueError("mode must be 'inclusive' or 'exclusive'")
    out = cp.empty(n, dtype=x.dtype)
    out[0] = 0
    if n > 1:
        out[1:] = inc[:-1]
    return out


def self_test(seed: int = 0, n: int = 100_003):
    """Numpy-referee check on seeded random data (seed/n are test fixtures, not physics)."""
    rng = np.random.default_rng(seed)
    keys = cp.asarray(rng.integers(0, 50, size=n))          # ties forced by small range
    vals_f = cp.asarray(rng.standard_normal(n))
    vals_i = cp.asarray(rng.integers(0, 1 << 31, size=n, dtype=np.int64) % (n * 7919))

    perm, vf, vi = stable_sort_by_key(keys, vals_f, vals_i)
    kh = keys.get(); fh = vals_f.get(); ih = vals_i.get()
    p_ref = np.argsort(kh, kind='stable')
    assert (perm.get() == p_ref).all(), "stable perm != numpy referee"
    assert np.allclose(fh[p_ref], vf.get()), "carried float values reordered wrong"
    assert (ih[p_ref] == vi.get()).all(), "carried int64 values reordered wrong"

    x = cp.asarray(rng.integers(-10, 10, size=n).astype(np.int64))
    xh = x.get()
    inc_h = parallel_scan(x, 'inclusive').get(); exc_h = parallel_scan(x, 'exclusive').get()
    assert (inc_h == np.cumsum(xh)).all(), "inclusive scan != numpy referee"
    ex_ref = np.concatenate([[0], np.cumsum(xh)[:-1]])
    assert (exc_h == ex_ref).all(), "exclusive scan != numpy referee"

    xf = cp.asarray(rng.standard_normal(n))                 # float64 path too
    assert np.allclose(parallel_scan(xf, 'inclusive').get(), np.cumsum(xf.get())), \
        "float inclusive scan wrong"
    print(f"parlib self_test PASS  n={n} seed={seed} (perm bit-equal incl. ties; scans exact)")


if __name__ == '__main__':
    self_test()
