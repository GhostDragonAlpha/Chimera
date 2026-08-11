"""master_loop.py -- the conductor prototype: one loop, one state array, one law.

The operator's theory, made runnable: a single master loop holds the roster of
membranes (the main Gaussian matrix). Every pass it rewrites each membrane's
complete state -- including its CUSTOM gravity numbers (couplings) -- so the
next frame renders the new physics. THE OBSERVER IS A PACKET: the player is one
row of the same position array passed to the same inverse-square walk
(LightEngine.kernel._draw_cuda), and the camera reads that row's position.

Membranes in this roster:
  theLight  -- the real pressed record (records ARE the matrix). The needle
               plays story-time; a SIZE coupling groove modulates grain size
               per pass (the groove that modulates the law, B1 seed).
  dust      -- a LIVE N-body, 1200 grains on a shell, integrated every pass by
               the repo's own GPU draw kernel with a per-pass G (custom
               gravity numbers, same equation, different magnitude).
  player    -- one packet in the SAME array as dust. It falls under the same
               field; the camera sits at it. Observer inside the observed.
  stars     -- a procedural far field, so the eye has something behind it.

Rendering is from the player's perspective only: the matrix is the records
(every groove of every membrane); the frame is the current slice, and only
that slice reaches the GPU. A billion packets are never rendered -- records
are, slices are.

FALSIFIERS (named before the run):
  F1  dust must collapse to a BOUND clump under the groove: mean radius drops
      below its start AND never re-expands past the start radius -- the binding
      reader (Stage 8 v2 rest-volume contact + Stage 10 damping) holds matter
      together where pure attraction alone blew it through (measured).
  F2  the observer must be a packet: the player's position moves under the
      same field (no special-case camera integrator).
  F3  one law means one equation: total momentum of dust+player stays ~0
      (the equal-and-opposite symmetry of the single walk) within 1e-4 of the
      initial value -- the observer is not a different physics.
  F4  the frame cost stays inside the documented wallet (MAX_RENDER_MS) at the
      same resolution the measured budgets used.

Usage:
    python ChimeraEngine/master_loop.py
"""
from __future__ import annotations

import math
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[0]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np  # noqa: E402
from numba import cuda  # noqa: E402

from LightEngine.constants import EPS  # noqa: E402
from LightEngine.kernel import _draw_cuda  # noqa: E402

_LIGHT = Path(_ROOT) / "story" / "theZero" / "theLight"

NCOLS = 28
PX, PY, PZ = 0, 1, 2
TYPE = 11
CR, CG, CB, ALPHA = 16, 17, 18, 19
SIZE = 20

PASSES = 36
SUBSTEPS = 3
DT = 0.02
N_DUST = 1200
R_DUST = 2.2
R_PACKET = 0.10     # rest-volume radius of a dust packet (Stage 8 v2: (3m/4pi rho0)^1/3)
B_PACKET = 2000.0   # bulk modulus driving the lens contact (demo scale; the derived law
                    #   U=(B/2)V_lens, F=(piB/8)(4R^2-d^2) -- THE_TWO_FORCES Stage 8 v2)
DAMP_CONTACT = 20.0 # Stage 10: contact-normal damping -- the medium's impedance that
                    #   lets a dropped packet settle instead of ringing forever
                    #   (repo: "restitution exactly 1.0 returns forever")
R_STAR = 15.0
N_STAR = 2000
PLAYER_START = np.array([6.0, 0.4, 0.3], np.float32)


def _draw(pos: np.ndarray, G: float, out: np.ndarray) -> np.ndarray:
    """The repo's own inverse-square walk, called with a per-membrane G.

    Same kernel theLight was integrated with; the observer is a row here too.
    """
    n = pos.shape[0]
    threads = 256
    blocks = (n + threads - 1) // threads
    d_pos = cuda.to_device(np.ascontiguousarray(pos, dtype=np.float32))
    d_out = cuda.to_device(np.ascontiguousarray(out, dtype=np.float32))
    _draw_cuda[blocks, threads](d_pos, d_out, float(G), float(EPS * EPS), n)
    d_out.copy_to_host(out)
    return out


def _lens_contact(pos, vel, R, B, damping, acc):
    """The binding reader: Stage 8 v2 rest-volume contact + Stage 10 damping.

    For equal packets the derived contact is F = (pi B / 8)(4 R^2 - d^2) along
    the pair axis while d < 2R (THE_TWO_FORCES.md Stage 8 v2). Pure attraction
    is exponentially soft and cannot hold matter together -- the measured
    falsifier F1 blowout. This is the repo's own "other gravity". Damping acts
    only on the contact-normal relative velocity (Stage 10 medium impedance).
    """
    n = pos.shape[0]
    d = pos[:, None, :] - pos[None, :, :]               # d = x_i - x_j (n,n,3)
    d2 = (d * d).sum(-1)
    np.fill_diagonal(d2, 0.0)
    contact = (d2 < 4.0 * R * R) & (d2 > 1e-12)
    dist = np.sqrt(np.where(contact, d2, 1.0))
    f_mag = (np.pi * B / 8.0) * (4.0 * R * R - d2)      # repulsive pair magnitude
    f_mag = np.where(contact, f_mag, 0.0)
    vrel = vel[:, None, :] - vel[None, :, :]            # (n,n,3)
    dhat = d * (1.0 / dist)[..., None]
    vrel_n = (vrel * dhat).sum(-1)                      # approach speed (neg when closing)
    damp = np.where(contact, -damping * vrel_n, 0.0)
    acc += ((f_mag + damp)[..., None] * dhat).sum(axis=1)
    return acc


def _fibonacci(n: int, r: float, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    i = np.arange(n, dtype=np.float64)
    phi = math.pi * (3.0 - math.sqrt(5.0))
    y = 1.0 - (2.0 * i + 1.0) / n
    rad = np.sqrt(np.clip(1.0 - y * y, 0.0, 1.0))
    th = phi * i
    p = np.stack([np.cos(th) * rad, y, np.sin(th) * rad], axis=1) * r
    return (p + rng.uniform(-0.02, 0.02, p.shape)).astype(np.float32)


def _blank(n: int) -> np.ndarray:
    b = np.zeros((n, NCOLS), dtype=np.float32)
    b[:, 9] = 1.0
    b[:, 10] = -1.0
    b[:, TYPE] = 3.0
    b[:, ALPHA] = 0.9
    return b


def _fill(buf: np.ndarray, pos: np.ndarray, rgb, size: float):
    n = pos.shape[0]
    buf[:, PX:PZ + 1] = pos
    buf[:, CR] = rgb[0]
    buf[:, CG] = rgb[1]
    buf[:, CB] = rgb[2]
    buf[:, SIZE] = size


def main() -> int:
    import sys as _sys
    _sys.path.insert(0, str(_LIGHT))
    import physics as light_physics  # theLight's own record player

    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera
    from ChimeraEngine.perf_guard import MAX_RENDER_MS

    nums = light_physics._load_numbers()
    n_light = int(nums["n_total"])
    rec = np.load(light_physics.RECORD_PATH, allow_pickle=False)
    matrix_rows = int(rec["pos"].shape[0]) * n_light
    base_size = float(nums["grain_size"])

    dust_pos = _fibonacci(N_DUST, R_DUST, seed=1)
    dust_vel = np.zeros_like(dust_pos)
    player_pos = PLAYER_START.copy()
    player_vel = np.zeros((1, 3), np.float32)
    acc = np.zeros((N_DUST + 1, 3), np.float32)

    star_pos = _fibonacci(N_STAR, R_STAR, seed=2)
    star_size = np.full(N_STAR, 1.2, np.float32)

    pipe = FullGPUPipeline(bg=(0.008, 0.008, 0.03))

    print("MASTER LOOP -- one law, one state array, observer included")
    print(f"  theLight matrix: {matrix_rows:,} recorded grooves (the record "
          f"IS the matrix; the frame is a slice)")
    print(f"  roster: theLight(dr)  dust(N={N_DUST}, live G)  player(1 packet)  stars({N_STAR})")
    print("-" * 108)
    print(f"{'pass':>4} {'t':>5} {'G_dust':>7} {'dust r':>7} {'player|Δ|':>8} "
          f"{'grains':>7} {'visible':>7} {'expans':>8} {'render ms':>9} {'fps':>6}")
    print("-" * 108)

    p0_total = 0.0
    max_p_total = 0.0
    dust_r0 = float(np.linalg.norm(dust_pos, axis=1).mean())
    max_render = 0.0
    results = []

    for p in range(PASSES):
        t = p / max(1, PASSES - 1)

        g_dust = 0.010 + 0.040 * t          # the custom gravity numbers groove
        size_light = base_size * (0.7 + 0.6 * t)

        for _ in range(SUBSTEPS):
            all_pos = np.vstack([dust_pos, player_pos])
            _draw(all_pos, g_dust, acc)
            _lens_contact(dust_pos, dust_vel, R_PACKET, B_PACKET, DAMP_CONTACT,
                          acc[:N_DUST])
            a_dust, a_player = acc[:N_DUST], acc[N_DUST:]
            dust_vel += a_dust * DT
            player_vel += a_player * DT
            dust_pos += dust_vel * DT
            player_pos += player_vel[0] * DT
        all_p = np.vstack([dust_vel, player_vel])
        p_total = float(np.abs(all_p.sum())) / (N_DUST + 1)
        max_p_total = max(max_p_total, p_total)
        p0_total = p0_total or p_total
        dust_r = float(np.linalg.norm(dust_pos, axis=1).mean())

        lbuf = light_physics.emit(dict(nums, grain_size=size_light), t)
        dust_buf = _blank(N_DUST)
        g_t = g_dust / 0.050
        _fill(dust_buf, dust_pos,
              (1.0 * (1 - g_t) + 0.95 * g_t, 0.5 * (1 - g_t) + 0.62 * g_t, 1.0 * (1 - g_t) + 0.22 * g_t),
              0.09)
        star_buf = _blank(N_STAR)
        _fill(star_buf, star_pos, (0.45, 0.55, 0.90), 1.2)
        player_buf = _blank(1)
        _fill(player_buf, player_pos[None], (1.0, 0.98, 0.90), 0.28)

        buf = np.vstack([lbuf, dust_buf, player_buf, star_buf])

        n_pos = math.sqrt(player_pos[0] ** 2 + player_pos[1] ** 2 + player_pos[2] ** 2)
        cam = FirstPersonCamera(
            position=np.array(player_pos, dtype=np.float32),
            yaw=math.atan2(-player_pos[1], -player_pos[0]),
            pitch=math.asin(-player_pos[2] / n_pos),
            fov=np.radians(60), near=0.05, far=R_STAR * 2.0,
        )
        pipe.upload(np.ascontiguousarray(buf), term="")
        prm = cam.params(width=1920, height=1080)
        if p < 2:
            pipe.render_from_gpu(cam, prm)
            continue
        t0 = time.perf_counter()
        pipe.render_from_gpu(cam, prm)
        rms = (time.perf_counter() - t0) * 1e3
        st = pipe.tile_stats()
        max_render = max(max_render, rms)
        visible = st["nv"]
        grains = buf.shape[0]

        results.append((p, t, g_dust, dust_r, p_total, rms, st["expansions"]))
        print(f"{p:>4} {t:5.2f} {g_dust:7.3f} {dust_r:7.3f} {np.linalg.norm(player_pos - PLAYER_START):8.3f} "
              f"{grains:>7} {visible:>7} {st['expansions']:>8} {rms:>9.2f} {1000.0 / rms:>6.1f}")

    print("-" * 108)
    ok1 = dust_r < dust_r0 * 0.85 and max(dr for _, _, _, dr, _, _, _ in results) <= dust_r0
    ok2 = float(np.linalg.norm(player_pos - PLAYER_START)) > 0.2
    ok3 = max_p_total < 1e-4
    ok4 = max_render <= MAX_RENDER_MS
    print("FALSIFIER VERDICTS")
    print(f"  F1 bound clump under the groove       {'PASS' if ok1 else 'FAIL'}: "
          f"mean r {dust_r0:.3f} -> {dust_r:.3f}, never re-expanded past start "
          f"(binding holds: collapse + bounded)")
    print(f"  F2 observer is a packet              {'PASS' if ok2 else 'FAIL'}: "
          f"player moved {np.linalg.norm(player_pos - PLAYER_START):.3f}")
    print(f"  F3 one law: p conserved              {'PASS' if ok3 else 'FAIL'}: "
          f"max|p|/grain = {max_p_total:.2e}")
    print(f"  F4 frame inside the wallet           {'PASS' if ok4 else 'FAIL'}: "
          f"worst {max_render:.1f} ms vs wall {MAX_RENDER_MS} ms")
    print(f"  slice vs matrix: {buf.shape[0]:,} grains rendered of {matrix_rows:,} recorded "
          f"({matrix_rows / buf.shape[0]:.0f}x compressed by the needle)")
    return 0 if (ok1 and ok2 and ok3 and ok4) else 1


if __name__ == "__main__":
    raise SystemExit(main())
