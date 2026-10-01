"""test_tile_eviction_lossless.py -- the tile-eviction falsifier (engine fix #2).

REGRESSION (measured 2026-09-28 on the 2.38M-splat 1600x900 scene): FullGPUPipeline
binned splats per 32-px screen tile under a fixed MAX_PER_TILE cap, and over-cap tiles
EVICTED their farthest splats. Between 21 and 80 tiles were over cap on that one scene
and the survivors did not always cover the tile, so the frame showed hard-edged BLACK
RECTANGLES on the tile grid (worst ~60x90 px of bare background). Raising the cap
(4096 -> 16384, 2026-07-29) deferred the defect; it never fixed it, because the cause is
big soft-field splats spanning up to 144 tiles, not too many grains.

THE FIX (ASTRA ROUND 6 R2, 2026-09-29): eviction is REPLACED by lossless, totally
ordered processing. The total order key is (tile ID, ordered depth, persistent splat
ID); the splats are globally sorted by (depth, persistent ID) first (`_depth_order`'s
stable argsort ties on emit order -- deterministic ID-ordered emission, and NaN depths
sort after finite ones, which DEFINES the nonfinite case); tile overlaps are enumerated
in that order; at most `tile_budget` records are processed per pass; each pass is
stably regrouped by tile; and every pass continues the exact per-splat arithmetic
sequence C += T*alpha*c; T *= (1-alpha) held in persistent per-pixel accumulators, one
pass completing before the next consumes. Compositing chunks independently would change
the FP association and is exactly what this architecture refuses.

THE ACCEPTANCE THIS TEST PINS (R2: BOTH halves are mandatory -- matching hashes alone
could preserve the same deterministic omission, and counts alone say nothing about
bytes):

  1. ZERO LOST OVERLAPS, COUNT-VERIFIED on pathological scenes -- all-splats-in-one-tile
     (18,000 splats over the 16,384 old cap, one tile) and dense overlap. The binner's
     reported `expansions` must equal an independent host-side count of the (tile, splat)
     overlap records, `kept` (the records the compositor was actually handed, summed from
     the measured per-pass sizes) must equal `expansions`, and the hottest tile's
     independent count must exceed MAX_PER_TILE -- proving the old code would have
     evicted on exactly this scene.
  2. BYTE-IDENTICAL OUTPUT across repeated runs AND across at least two pass budgets
     (here 977 / 50,000 / single-pass), on scenes whose records far exceed the small
     budget -- only a chunking that never disturbs the arithmetic sequence can do this.
     Equal-depth ties and a NaN-depth splat are in the scene, so the DEFINED tie and
     nonfinite handling is what the hashes are betting on.
  3. THE PREVIOUSLY EVICTED SPLAT RENDERS. A far opaque splat sharing a tile with
     >MAX_PER_TILE nearer splats used to be evicted (the cap kept the NEAREST): the probe
     pixel under the old code was bare background. Now it must equal -- byte for byte --
     the same far splat rendered ALONE.

    python ParticleEngine/test_tile_eviction_lossless.py   # the gate
    python -m unittest ParticleEngine.test_tile_eviction_lossless -v
    python ParticleEngine/test_tile_eviction_lossless.py --hash-once   # one fresh-process render, prints its SHA (used by the fresh-process test)
"""
from __future__ import annotations

import hashlib
import math
import os
import subprocess
import sys
import unittest

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

W = H = 96
FOV = math.radians(60.0)
# FOOTPRINT IS IMPORTED, NEVER RETYPED. It is a DERIVED constant in gpu_pipeline
# (sqrt(-2*ln(0.001))/3); the first draft of this test typed 1.23894931... from memory
# instead of the true 1.23897421..., and the count check caught it as a one-record
# discrepancy (binner 33421 vs counter 33420) on the dense scene. A hand-copied derived
# constant is a defect injector: import the derivation.
MAX_PER_TILE = 16384

try:                                    # the gate is a GPU gate; say so loudly if there is none
    from numba import cuda
    _HAS_GPU = len(cuda.gpus) > 0
except Exception:                       # pragma: no cover - CPU-only host
    _HAS_GPU = False


def _splat(x_cm, depth_cm, size_cm, rgb, alpha):
    """One TYPE=3 splat on the optical axis column of a yaw=0/pitch=0 camera at the origin.

    TYPE=3: size scale 1.0, opacity from the ALPHA column, isotropic covariance, no
    back-face cull. The camera looks along +x, so PX is depth and (PY, PZ) are screen
    up/right offsets in world cm.
    """
    row = np.zeros(28, np.float32)
    row[0] = depth_cm                                   # PX (camera looks along +x)
    row[1] = x_cm                                       # PY (screen vertical offset)
    row[11] = 3                                         # TYPE=3: disc, opacity from ALPHA
    row[16], row[17], row[18] = rgb                     # CR, CG, CB
    row[19] = alpha                                     # ALPHA
    row[20] = size_cm                                   # SIZE (cm, pre base_scale)
    return row


def _cloud_scene(n, rng, spread_cm=2.0, depth0=1000.0):
    """n splats packed into a few-pixel blob near the frame centre, distinct depths and
    per-splat colours: any change in processing ORDER or any LOST record moves bytes."""
    rows = np.zeros((n, 28), np.float32)
    cols = rng.uniform(0.05, 0.95, size=(n, 3)).astype(np.float32)
    offs = rng.uniform(-spread_cm, spread_cm, size=(n, 2)).astype(np.float32)
    rows[:, 0] = depth0 + np.arange(n, dtype=np.float32) * 0.05      # distinct depth per splat
    rows[:, 1] = offs[:, 0]
    rows[:, 2] = offs[:, 1]
    rows[:, 11] = 3
    rows[:, 16:19] = cols
    rows[:, 19] = rng.uniform(0.3, 0.9, size=n).astype(np.float32)
    rows[:, 20] = rng.uniform(20.0, 60.0, size=n).astype(np.float32)
    return rows


def _render(buf, pipe=None):
    os.environ.setdefault("NUMBA_CACHE_DIR",
                          os.path.join(_HERE, "__pycache__", "numba_cache"))
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera
    pipe = pipe or FullGPUPipeline(bg=(0.01, 0.01, 0.05))
    pipe.upload(np.ascontiguousarray(buf.reshape(-1, 28), dtype=np.float32))
    cam = FirstPersonCamera(position=(0.0, 0.0, 0.0), yaw=0.0, pitch=0.0,
                            fov=FOV, far=100000.0)
    return pipe.render_from_gpu(cam, cam.params(W, H)), pipe


def _sha(img):
    return hashlib.sha256(np.ascontiguousarray(img).tobytes()).hexdigest()


def _independent_per_tile_counts(pipe, nv, tiles_x, tiles_y, tile_sz):
    """Re-derive the (tile, splat) overlap histogram FROM THE FRAME'S OWN PROJECTED INPUTS,
    by an independent path: the documented bbox rule (clamped, FOOTPRINT reach, integer
    boxes) applied splat-by-splat with a slice increment -- not the binner's
    repeat/argsort machinery. Reads back the gathered arrays the composite actually
    consumed, so the two counts are about the SAME frame."""
    from ParticleEngine.gpu_pipeline import FOOTPRINT      # the derived constant, imported
    kx = pipe._kx.copy_to_host()[:nv]
    ky = pipe._ky.copy_to_host()[:nv]
    krad = pipe._krad.copy_to_host()[:nv]
    # THE ARITHMETIC IS THE BINNER'S PRECISION, NOT MINE TO IMPROVE: the box reach is
    # defined by float32 `srad * FOOTPRINT` truncated to int (the device arrays are
    # float32 and cupy keeps them so). Counting in float64 flips one boundary pixel on
    # some splat and the count is off by exactly that record -- measured 33421 vs 33420
    # before this was pinned to float32.
    span = tiles_x * tile_sz + tiles_y * tile_sz
    srad = np.nan_to_num(krad, nan=np.float32(0.0), posinf=np.float32(span), neginf=np.float32(0.0))
    sx = np.nan_to_num(kx, nan=np.float32(-1e9), posinf=np.float32(1e9), neginf=np.float32(-1e9))
    sy = np.nan_to_num(ky, nan=np.float32(-1e9), posinf=np.float32(1e9), neginf=np.float32(-1e9))
    r = np.clip(srad * FOOTPRINT, np.float32(0.0), np.float32(span)).astype(np.int64) + 1
    px = np.clip(sx, np.float32(-span), np.float32(span)).astype(np.int64)
    py = np.clip(sy, np.float32(-span), np.float32(span)).astype(np.int64)
    tx0 = np.clip((px - r) // tile_sz, 0, tiles_x - 1)
    tx1 = np.clip((px + r) // tile_sz, 0, tiles_x - 1)
    ty0 = np.clip((py - r) // tile_sz, 0, tiles_y - 1)
    ty1 = np.clip((py + r) // tile_sz, 0, tiles_y - 1)
    per_tile = np.zeros((tiles_y, tiles_x), np.int64)
    for i in range(nv):                     # one slice increment per splat: independent of the binner
        per_tile[ty0[i]:ty1[i] + 1, tx0[i]:tx1[i] + 1] += 1
    return per_tile


@unittest.skipUnless(_HAS_GPU, "no CUDA device: the tile stage is a GPU pipeline, the gate cannot run")
class TestTileEvictionLossless(unittest.TestCase):
    TOL = 1

    @classmethod
    def setUpClass(cls):
        cls.rng = np.random.default_rng(20260929)
        # ALL-SPLATS-IN-ONE-TILE: 18,000 splats packed at the frame centre -- the centre
        # tile holds all of them, 18,000 > MAX_PER_TILE, so the OLD code evicted ~1,600
        # splats from that tile every frame. Distinct depths + distinct colours: bytes bind.
        cls.one_tile = _cloud_scene(18000, cls.rng)
        # DENSE OVERLAP: 24,000 splats in a ~33-px blob -- the centre tile again far over
        # the old cap, its neighbours heavily spilled into, cross-splat overlap everywhere.
        cls.dense = _cloud_scene(24000, cls.rng, spread_cm=300.0, depth0=1500.0)
        # EQUAL DEPTH + NONFINITE DEPTH: 500 same-depth splats (ties -> persistent-ID
        # order) plus one NaN-depth splat (sorts after every finite depth -- the DEFINED
        # nonfinite handling). Nothing here may depend on which budget cut the stream.
        cls.ties = _cloud_scene(500, cls.rng, depth0=2200.0)
        cls.ties[:, 0] = 2200.0                       # every depth identical -> all ties
        nan_row = _splat(0.0, 0.0, 40.0, (0.9, 0.1, 0.1), 0.5)
        nan_row[0] = np.float32("nan")                # NaN depth: defined order, reproducible bytes
        cls.ties_with_nan = np.concatenate([cls.ties, nan_row[None, :]])

    # ── 1. ZERO LOST OVERLAPS, COUNT-VERIFIED ───────────────────────────────────────────
    def _assert_zero_lost_overlaps(self, buf, label):
        img, pipe = _render(buf)
        st = pipe.tile_stats()
        nv = int(st["nv"])
        self.assertGreater(nv, 0, f"{label}: nothing survived the cull; scene is broken")
        tiles_x = (W + 31) // 32
        per_tile = _independent_per_tile_counts(pipe, nv, tiles_x, (H + 31) // 32, 32)
        independent_total = int(per_tile.sum())
        # (a) the binner enumerated exactly the documented record set
        self.assertEqual(int(st["expansions"]), independent_total,
                         f"{label}: binner expansions {st['expansions']} != independent "
                         f"overlap count {independent_total}")
        # (b) the compositor was handed every one of them (the old cap made kept < expansions)
        self.assertEqual(int(st["kept"]), int(st["expansions"]),
                         f"{label}: compositor received {st['kept']} of "
                         f"{st['expansions']} records -- OVERLAPS WERE LOST")
        # (c) this scene is genuinely pathological: its hottest tile exceeds the old cap,
        #     so the old code was EVICTING here and this test would have caught it
        self.assertGreater(int(per_tile.max()), MAX_PER_TILE,
                           f"{label}: hottest tile {int(per_tile.max())} does not exceed the "
                           f"old MAX_PER_TILE cap -- the scene is no longer pathological")
        self.assertGreaterEqual(int(st["passes"]), 1)
        return st, per_tile

    def test_all_splats_one_tile_zero_lost_overlaps(self):
        st, per_tile = self._assert_zero_lost_overlaps(self.one_tile, "all-splats-one-tile")
        centre_tile = per_tile[H // 2 // 32, W // 2 // 32]
        self.assertEqual(centre_tile, int(per_tile.max()),
                         "the centre tile is not the hottest: the scene no longer concentrates")
        self.assertGreaterEqual(int(st["passes"]), 1)

    def test_dense_overlap_zero_lost_overlaps(self):
        self._assert_zero_lost_overlaps(self.dense, "dense-overlap")

    def test_small_budget_still_lossless(self):
        """The count law holds under a budget far below the scene's record count: many
        passes, every record still handed to the compositor."""
        from ParticleEngine.gpu_pipeline import FullGPUPipeline
        pipe = FullGPUPipeline(bg=(0.01, 0.01, 0.05), tile_budget=977)
        img, pipe = _render(self.one_tile, pipe)
        st = pipe.tile_stats()
        self.assertEqual(int(st["kept"]), int(st["expansions"]),
                         f"budget 977 lost records: kept {st['kept']} of {st['expansions']}")
        self.assertGreater(int(st["passes"]), 1,
                           "budget 977 should have needed multiple passes on this scene")

    # ── 2. BYTE-IDENTICAL OUTPUT: REPEATS, BUDGETS, TIES, NONFINITE ─────────────────────
    def test_byte_identical_across_repeat_runs(self):
        a, _ = _render(self.one_tile)
        b, _ = _render(self.one_tile)           # fresh pipeline, same budget, same process
        self.assertEqual(_sha(a), _sha(b), "the same scene rendered twice differs byte-wise")

    def test_byte_identical_across_budgets(self):
        """977 / 50,000 / single-pass must produce THE SAME BYTES on a scene whose record
        count forces the small budget into dozens of passes. This is the chunk-boundary
        proof: only a partition that never disturbs the per-splat arithmetic sequence
        C += T*alpha*c; T *= (1-alpha) can pass it."""
        hashes = {}
        for budget in (977, 50000, 1 << 60):
            from ParticleEngine.gpu_pipeline import FullGPUPipeline
            pipe = FullGPUPipeline(bg=(0.01, 0.01, 0.05), tile_budget=budget)
            img, pipe = _render(self.one_tile, pipe)
            hashes[budget] = _sha(img)
        self.assertEqual(hashes[977], hashes[50000],
                         "budget 977 and 50000 disagree: chunking changed the arithmetic")
        self.assertEqual(hashes[50000], hashes[1 << 60],
                         "multi-pass and single-pass disagree: chunking changed the arithmetic")

    def test_equal_depth_ties_and_nonfinite_deterministic(self):
        """Equal depths tie-break on the persistent splat ID and a NaN depth sorts last:
        both are DEFINED points of the total order, and both must survive re-runs and
        budget changes byte-identically."""
        hashes = set()
        for budget in (977, 1 << 60):
            from ParticleEngine.gpu_pipeline import FullGPUPipeline
            pipe = FullGPUPipeline(bg=(0.01, 0.01, 0.05), tile_budget=budget)
            img, _ = _render(self.ties_with_nan, pipe)
            hashes.add(_sha(img))
            img2, _ = _render(self.ties_with_nan, pipe)
            hashes.add(_sha(img2))
        self.assertEqual(len(hashes), 1,
                         f"ties/NaN scene is not deterministic across runs and budgets: {hashes}")

    def test_fresh_process_determinism(self):
        """Two FRESH INTERPRETERS must hash the same frame identically -- the guard
        against poisoned shared kernel caches and per-process module state (the failure
        mode the TILE_SIZE sweep once hit)."""
        env = dict(os.environ)
        env.setdefault("NUMBA_CACHE_DIR", os.path.join(_HERE, "__pycache__", "numba_cache"))
        shas = []
        for _ in range(2):
            out = subprocess.run(
                [sys.executable, os.path.abspath(__file__), "--hash-once"],
                capture_output=True, text=True, env=env, timeout=900)
            self.assertEqual(out.returncode, 0,
                             f"fresh-process render failed: {out.stderr[-800:]}")
            shas.append(out.stdout.strip().splitlines()[-1].strip())
        self.assertEqual(shas[0], shas[1],
                         f"fresh processes disagree: {shas}")

    # ── 3. THE PREVIOUSLY EVICTED SPLAT RENDERS ─────────────────────────────────────────
    def test_previously_evicted_far_splat_renders(self):
        """The defect, reproduced small and pinned shut. The frame-centre tile holds 17,000
        faint near splats (over the 16,384 old cap) in a couple-of-pixels blob, plus one
        big OPAQUE FAR splat covering the whole tile. The cap kept the NEAREST records, so
        the far splat was EVICTED from that tile's list and its pixels showed bare
        background -- a hard black 32x32 rectangle on the tile grid. Now a probe pixel
        INSIDE that tile, far enough from the blob that no near splat reaches it, must be
        byte-identical to the far splat rendered ALONE and must NOT be background."""
        far = _splat(0.0, 9000.0, 3200.0, (0.85, 0.35, 0.15), 1.0)   # rad ~44 px: covers the tile
        near = _cloud_scene(17000, self.rng, spread_cm=1.0, depth0=1000.0)
        near[:, 19] = 0.05                                            # faint: filler, not painter
        near[:, 1] *= 0.1; near[:, 2] *= 0.1                          # blob within one pixel
        near[:, 20] = 20.0                                            # rad <= ~4 px: short reach
        buf = np.concatenate([near, far[None, :]])
        img, pipe = _render(buf)
        st = pipe.tile_stats()

        # the centre tile really is over the old cap, and the far splat really is farthest
        tiles_x = (W + 31) // 32
        per_tile = _independent_per_tile_counts(pipe, int(st["nv"]), tiles_x, (H + 31) // 32, 32)
        centre = per_tile[H // 2 // 32, W // 2 // 32]
        self.assertGreater(int(centre), MAX_PER_TILE,
                           f"centre tile holds {int(centre)} -- not over the old cap; "
                           "the scene is not the defect")
        # ...and the compositor received everything (zero lost overlaps, counted)
        self.assertEqual(int(st["kept"]), int(st["expansions"]),
                         f"kept {st['kept']} != expansions {st['expansions']}")

        probe = (38, 38)              # inside the over-cap tile, ~14 px from the blob, ~0.96 sigma
        alone, _ = _render(far.reshape(1, 28))
        got = tuple(int(v) for v in img[probe])
        want = tuple(int(v) for v in alone[probe])
        bg = tuple(int(v) for v in (np.array([0.01, 0.01, 0.05]) * 255).astype(np.int32))
        self.assertEqual(got, want,
                         f"probe pixel {got} != far-splat-alone {want}: the far splat is "
                         f"still not rendering as if alone -- overlap processing is not lossless here")
        self.assertNotEqual(got, bg,
                            f"probe pixel is bare background {bg}: the black-rectangle "
                            f"defect is present (far splat evicted)")


if __name__ == "__main__":
    if "--hash-once" in sys.argv:
        # One fresh-process render of the pathological scene; the SHA on stdout is what
        # test_fresh_process_determinism compares across interpreters.
        rng = np.random.default_rng(20260929)
        buf = _cloud_scene(18000, rng)
        img, _ = _render(buf)
        print(_sha(img), flush=True)
        sys.exit(0)
    if not _HAS_GPU:
        print("SKIP (loud): no CUDA device -- the tile stage is a GPU pipeline, the "
              "losslessness gate cannot run on this host.", flush=True)
        sys.exit(2)
    unittest.main(verbosity=2)
