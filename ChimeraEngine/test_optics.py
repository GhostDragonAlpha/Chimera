"""test_optics.py -- the falsifiers for THE TWO-FORCE READER's light half, all runnable as one gate.

    python ChimeraEngine/test_optics.py

What is on trial (docs/THE_TWO_FORCES.md; plan: two-forces-gaussian-splat-light):

  T1  STAGE 0 CLOSURE -- density alone, pushed through Lorentz-Lorenz (story/matter.py), must land
      on numbers it was never fitted to: pure water's literature n, and aSaltOcean's OWN published
      sunglint (the membrane derived its glint from a sourced n = 1.34; we re-derive n from its
      published density and must meet it). Tolerances pre-registered in core/optics.py.
  T2  ONE SOURCE OF TRUTH -- the referee module defines no refraction law of its own (ast-checked),
      and the column contract between story.matter and the GPU pipeline agrees bit-for-bit.
  T3  KERNEL vs REFEREE -- the float32 GPU specular term against the float64 CPU referee, same
      declared model, two implementations, on BOTH falsifier membranes' published numbers
      (aSaltOcean water; aTerrain slope statistic + theGround bulk density). |max| and median
      gates pre-registered in core/optics.py BEFORE the first comparison ran.
  T4  THE CLAY CONTROLS -- zeroed specular columns under a light, and populated columns under NO
      light, must both render BIT-IDENTICAL to the baseline: the instrument must be silent before
      it may convict or acquit (the 2026-08-01 lesson).
  T5  REAL OUTPUT -- on/off frames written to agent_logs/ so the operator can see the glint.
"""
from __future__ import annotations

import ast
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "story")):                # story dir itself: walker.py's idiom --
    if _p not in sys.path:                                 # `from story import ...` loses to
        sys.path.insert(0, _p)                             # ChimeraEngine/story.py from this dir

import matter                                              # noqa: E402
from ChimeraEngine.core import optics                      # noqa: E402
from ParticleEngine import gpu_pipeline as gp              # noqa: E402
from ParticleEngine.camera import FirstPersonCamera        # noqa: E402

_PASS = 0
_FAIL = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global _PASS, _FAIL
    tag = "ok  " if ok else "FAIL"
    print(f"[{tag}] {name}" + (f" -- {detail}" if detail else ""), flush=True)
    if ok:
        _PASS += 1
    else:
        _FAIL += 1


def published(leaf: str) -> dict:
    """A membrane's numbers.json, found by its NAME so a timeline remake cannot strand this test.
    Reads PUBLISHED numbers only -- the instrument holds no copy of the membrane."""
    hits = sorted(ROOT.glob(f"story/**/{leaf}/numbers.json"))
    if not hits:
        raise FileNotFoundError(f"no published numbers for {leaf} -- refusing to invent them")
    return json.loads(hits[0].read_text())


# ═══ T1 -- STAGE 0 CLOSURE ═══════════════════════════════════════════════════════════════════════
def t1_stage0_closure():
    sea = published("aSaltOcean")
    n_pure = matter.refractive_index(1000.0, matter.SPECIFIC_REFRACTION_CM3_G["water"])
    check("T1 pure water n from density alone vs literature 1.333",
          abs(n_pure - 1.333) / 1.333 <= optics.EPS_N_REL, f"n = {n_pure:.4f}")

    n_sea = matter.refractive_index(sea["density_surface_kg_m3"],
                                    matter.SPECIFIC_REFRACTION_CM3_G["water"])
    # The membrane's own implied n, recovered from ITS published glint: F0 = ((n-1)/(n+1))^2.
    f0_pub = float(sea["sunglint_intensity"])
    n_implied = (1.0 + math.sqrt(f0_pub)) / (1.0 - math.sqrt(f0_pub))
    check("T1 seawater n from density vs aSaltOcean's own implied n",
          abs(n_sea - n_implied) / n_implied <= optics.EPS_N_REL,
          f"n(rho) = {n_sea:.4f}, membrane implies {n_implied:.4f}")

    f0_sea = matter.fresnel_f0(n_sea)
    check("T1 F0 from density vs published sunglint_intensity",
          abs(f0_sea - f0_pub) / f0_pub <= optics.EPS_F0_REL,
          f"F0 = {f0_sea:.5f}, published {f0_pub:.5f}")

    n_qtz = matter.refractive_index(2650.0, matter.SPECIFIC_REFRACTION_CM3_G["silicate"])
    check("T1 solid quartz n restated through the law vs 1.548",
          abs(n_qtz - 1.548) / 1.548 <= optics.EPS_N_REL, f"n = {n_qtz:.4f}")

    gnd = published("theGround")
    n_gnd = matter.refractive_index(gnd["bulk_density"],
                                    matter.SPECIFIC_REFRACTION_CM3_G["silicate"])
    check("T1 porosity lowers reflectance BY THE LAW (regolith F0 < solid quartz F0)",
          matter.fresnel_f0(n_gnd) < matter.fresnel_f0(n_qtz),
          f"regolith F0 = {matter.fresnel_f0(n_gnd):.5f} at rho {gnd['bulk_density']:.0f}, "
          f"quartz {matter.fresnel_f0(n_qtz):.5f} at 2650")

    m = matter.grain_mass(sea["density_surface_kg_m3"], 0.02)
    check("T1 grain mass/density roundtrip is exact",
          abs(matter.grain_density(m, 0.02) - sea["density_surface_kg_m3"]) < 1e-9)


# ═══ T2 -- ONE SOURCE OF TRUTH ═══════════════════════════════════════════════════════════════════
def t2_one_source():
    src = (ROOT / "ChimeraEngine" / "core" / "optics.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    defs = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    check("T2 referee defines no refraction law of its own (ast)",
          "refractive_index" not in defs and "fresnel_f0" not in defs,
          f"functions defined: {sorted(defs)}")
    check("T2 referee imports the one source (story/matter.py)",
          "from matter import" in src and '_STORY = _ROOT / "story"' in src)
    check("T2 column contract: SPEC_F0 is the pipeline's PROP0, SPEC_SLOPE its PROP1",
          matter.SPEC_F0 == gp.PROP0 and matter.SPEC_SLOPE == gp.PROP1,
          f"{matter.SPEC_F0}=={gp.PROP0}, {matter.SPEC_SLOPE}=={gp.PROP1}")
    same = all(getattr(matter, k) == getattr(gp, k)
               for k in ("PX", "PY", "PZ", "MASS", "TYPE", "CR", "CG", "CB",
                         "ALPHA", "SIZE", "NX", "NY", "NZ", "NCOLS"))
    check("T2 column contract: every shared column name agrees bit-for-bit", same)


# ═══ T6 -- THE SLIDER (the closure test: move density and every consequence must move) ═══════════
def t6_slider_closure():
    """Whatever does not move when density moves is TYPED, not derived (the 2026-07-29 law).
    Also the two-granularity gravity scope, stated in docs/THE_TWO_FORCES.md: gravity reads
    AGGREGATE density (the membrane tree -- the parent carries g and the child consumes it);
    light and contact read LOCAL density (the grain buffer)."""
    sea = published("aSaltOcean")
    gnd = published("theGround")
    for name, r, rho0 in (("water", matter.SPECIFIC_REFRACTION_CM3_G["water"],
                           float(sea["density_surface_kg_m3"])),
                          ("silicate", matter.SPECIFIC_REFRACTION_CM3_G["silicate"],
                           float(gnd["bulk_density"]))):
        n_lo = matter.refractive_index(0.9 * rho0, r)
        n_mid = matter.refractive_index(rho0, r)
        n_hi = matter.refractive_index(1.1 * rho0, r)
        check(f"T6 slider: {name} density up -> n up, strictly",
              n_lo < n_mid < n_hi, f"{n_lo:.4f} < {n_mid:.4f} < {n_hi:.4f}")
        f_lo, f_hi = matter.fresnel_f0(n_lo), matter.fresnel_f0(n_hi)
        check(f"T6 slider: {name} density up -> F0 up, strictly",
              f_lo < matter.fresnel_f0(n_mid) < f_hi, f"{f_lo:.5f} .. {f_hi:.5f}")
    blue = published("aBlueWorld")
    check("T6 gravity scope: the parent carries g and the ocean consumes it (one aggregate field)",
          abs(float(sea["g"]) - float(blue["g"])) < 1e-9,
          f"aSaltOcean g = {sea['g']:.6f}, aBlueWorld g = {blue['g']:.6f}")


# ═══ T3/T4/T5 -- THE RENDER-SIDE TRIALS ══════════════════════════════════════════════════════════
def sphere_buffer(n_grains: int, rgb, rho: float, f0: float, slope: float) -> np.ndarray:
    """A unit sphere of surface grains, every number derived: positions and normals from the
    golden-angle sphere, grain size from the packing law, mass from the stated density."""
    d = matter.fibonacci_sphere(n_grains, jitter=0.35, seed=7).astype(np.float32)
    b = matter.blank(n_grains)
    b[:, matter.PX] = d[:, 0]; b[:, matter.PY] = d[:, 1]; b[:, matter.PZ] = d[:, 2]
    b[:, matter.NX] = d[:, 0]; b[:, matter.NY] = d[:, 1]; b[:, matter.NZ] = d[:, 2]
    size = matter.surface_grain(n_grains)
    matter.paint(b, rgb, 1.0, size, matter.SOLID)
    b[:, matter.MASS] = matter.grain_mass(rho, size)
    matter.paint_specular(b, f0, slope)
    return b


def grain_colours(pipe, n: int) -> np.ndarray:
    return np.stack([pipe._scr.copy_to_host()[:n],
                     pipe._scg.copy_to_host()[:n],
                     pipe._scb.copy_to_host()[:n]], axis=1)


def render_case(name: str, rho: float, f0: float, slope: float, rgb, save_png: bool):
    n = 4096
    buf = sphere_buffer(n, rgb, rho, f0, slope)
    cam = FirstPersonCamera(position=(0.0, -2.5, 0.0), yaw=np.pi / 2, pitch=0.0)
    prm = cam.params(width=640, height=480)
    light_dir = (0.35, -0.9, 0.5)          # over the camera's left shoulder, so the glint faces us
    light_rgb = (1.0, 0.97, 0.92)

    pipe = gp.FullGPUPipeline()
    pipe.upload(buf)

    pipe.set_light(None)
    img_off = pipe.render_from_gpu(cam, prm)
    base = grain_colours(pipe, n)

    pipe.set_light(light_dir, light_rgb)
    img_on = pipe.render_from_gpu(cam, prm)
    shaded = grain_colours(pipe, n)

    kernel_add = shaded.astype(np.float64) - base.astype(np.float64)
    ref_add = optics.specular_reference(buf, np.asarray(cam.position, dtype=np.float64),
                                        light_dir, light_rgb)

    diff = np.abs(kernel_add - ref_add)
    lit = ref_add.max(axis=1) > 0.0
    n_lit = int(lit.sum())
    max_d = float(diff.max())
    med_d = float(np.median(diff[lit])) if n_lit else 0.0
    check(f"T3 {name}: kernel vs float64 referee, max |diff| <= {optics.EPS_KERNEL_MAX}",
          max_d <= optics.EPS_KERNEL_MAX,
          f"max {max_d:.2e} over {n} grains ({n_lit} lit), spec peak {ref_add.max():.3f}")
    check(f"T3 {name}: median |diff| on lit grains <= {optics.EPS_KERNEL_MED}",
          med_d <= optics.EPS_KERNEL_MED, f"median {med_d:.2e}")
    check(f"T3 {name}: the term is not silent (some grains actually glint)", n_lit > 0,
          f"{n_lit} grains carry specular energy")
    check(f"T3 {name}: the glint SHOWS in the frame (on != off)",
          int((img_on != img_off).sum()) > 0,
          f"{int((img_on != img_off).sum())} subpixel values changed")

    # ── T4 THE CLAY CONTROLS ──────────────────────────────────────────────────────────────────
    clay = buf.copy()
    clay[:, matter.SPEC_F0] = 0.0
    clay[:, matter.SPEC_SLOPE] = 0.0
    pipe.upload(clay)                        # light is still set from above
    img_clay = pipe.render_from_gpu(cam, prm)
    clay_cols = grain_colours(pipe, n)
    check(f"T4 {name}: zeroed columns under a light -> BIT-IDENTICAL grains",
          np.array_equal(clay_cols, base), "the instrument is silent with no published F0/slope")
    check(f"T4 {name}: zeroed columns under a light -> bit-identical frame",
          np.array_equal(img_clay, img_off))

    pipe.upload(buf)
    pipe.set_light(None)
    img_dark = pipe.render_from_gpu(cam, prm)
    dark_cols = grain_colours(pipe, n)
    check(f"T4 {name}: populated columns with NO light -> bit-identical grains",
          np.array_equal(dark_cols, base), "no caller that never asks can be changed by this pass")
    check(f"T4 {name}: populated columns with NO light -> bit-identical frame",
          np.array_equal(img_dark, img_off))

    if save_png:
        try:
            from PIL import Image
            outdir = ROOT / "agent_logs"
            outdir.mkdir(exist_ok=True)
            Image.fromarray(img_off).save(outdir / f"optics_{name}_off.png")
            Image.fromarray(img_on).save(outdir / f"optics_{name}_on.png")
            print(f"[art ] agent_logs/optics_{name}_off.png + _on.png written", flush=True)
        except Exception as e:                                    # pragma: no cover
            print(f"[art ] PNG save skipped: {e}", flush=True)


# ═══ T7/T8/T9 -- THE LENSING CHAIN ═══════════════════════════════════════════════════════════════
def water_over_floor(n_side=48, wave_amp=0.0, wave_k=1.0, floor_z=-1.0, span=2.4):
    """A water surface strip over a checkered floor plane -- the lensing chain's test membrane.
    Surface at z=0 with normals tilted as a sine wave of the STATED amplitude (0 = flat); floor
    grains one per cell so the grid lookup is exact. Returns (buf, n_surf, grid args...)."""
    s = np.linspace(-0.9, 0.9, n_side, dtype=np.float64)
    sx, sy = np.meshgrid(s, s)
    n_surf = n_side * n_side
    surf = matter.blank(n_surf)
    surf[:, matter.PX] = sx.ravel(); surf[:, matter.PY] = sy.ravel(); surf[:, matter.PZ] = 0.0
    slope = wave_amp * wave_k * np.cos(wave_k * sx.ravel())
    nz = np.ones(n_surf); nrm = np.stack([-slope, np.zeros(n_surf), nz], axis=1)
    nrm /= np.linalg.norm(nrm, axis=1)[:, None]
    surf[:, matter.NX] = nrm[:, 0]; surf[:, matter.NY] = nrm[:, 1]; surf[:, matter.NZ] = nrm[:, 2]
    matter.paint(surf, (0.02, 0.05, 0.08), 1.0, matter.surface_grain(n_surf, radius=0.9), matter.SOLID)
    sea = published("aSaltOcean")
    n_w = matter.refractive_index(sea["density_surface_kg_m3"],
                                  matter.SPECIFIC_REFRACTION_CM3_G["water"])
    matter.paint_specular(surf, matter.fresnel_f0(n_w), float(sea["surface_slope_mean"]))
    surf[:, matter.REFRACT] = 1.0

    n_f = 96
    f = np.linspace(-span / 2, span / 2, n_f, dtype=np.float64)
    fx, fy = np.meshgrid(f, f)
    floor = matter.blank(n_f * n_f)
    floor[:, matter.PX] = fx.ravel(); floor[:, matter.PY] = fy.ravel(); floor[:, matter.PZ] = floor_z
    floor[:, matter.NZ] = 1.0
    checker = ((np.floor(fx / 0.15) + np.floor(fy / 0.15)) % 2).ravel()
    cell = float(f[1] - f[0])
    matter.paint(floor, (0.0, 0.0, 0.0), 1.0, matter.surface_grain(n_f * n_f, radius=span / 2), matter.SOLID)
    floor[:, matter.CR] = np.where(checker > 0, 0.85, 0.10)
    floor[:, matter.CG] = np.where(checker > 0, 0.75, 0.10)
    floor[:, matter.CB] = np.where(checker > 0, 0.55, 0.12)
    origin, cell, grid_rgb, grid_has = optics.build_floor_grid(floor, cell)
    return (np.concatenate([surf, floor]).astype(np.float32), n_surf, n_w,
            origin, cell, grid_rgb, grid_has, floor_z)


def t7_refraction():
    buf, n_surf, n_w, origin, cell, grid_rgb, grid_has, floor_z = water_over_floor()
    sea = published("aSaltOcean")
    absorb = [float(a) for a in sea["absorption_rgb_measured"]]
    eta = 1.0 / n_w
    cam = FirstPersonCamera(position=(0.0, -2.2, 1.5), yaw=np.pi / 2, pitch=-0.6)
    prm = cam.params(width=640, height=480)
    n_all = len(buf)

    pipe = gp.FullGPUPipeline()
    pipe.upload(buf)
    pipe.set_light(None)
    pipe.set_refraction(None)
    img_base = pipe.render_from_gpu(cam, prm)
    base = grain_colours(pipe, n_all)

    pipe.set_refraction((eta, eta, eta), floor_z, absorb, origin, cell, grid_rgb, grid_has)
    img_on = pipe.render_from_gpu(cam, prm)
    shaded = grain_colours(pipe, n_all)
    kadd = shaded.astype(np.float64) - base.astype(np.float64)

    ref_add, ref_hits = optics.refraction_reference(
        buf, np.asarray(cam.position, np.float64), (eta, eta, eta), floor_z, absorb,
        origin, cell, grid_rgb, grid_has)
    diff = np.abs(kadd - ref_add)
    lit = ref_add.max(axis=1) > 0.0
    check("T7 refraction: kernel vs float64 referee, max |diff|",
          float(diff.max()) <= optics.EPS_TRANS_MAX,
          f"max {float(diff.max()):.2e} over {int(lit.sum())} transmitting grains")
    check("T7 refraction: the floor is actually SEEN through the water", int(lit.sum()) > n_surf // 2,
          f"{int(lit.sum())} of {n_surf} surface grains transmit")
    check("T7 refraction: the picture changed (floor visible through surface)",
          int((img_on != img_base).sum()) > 0, f"{int((img_on != img_base).sum())} subpixels")

    # THE CLAY CONTROL, derived: eta = 1 is a uniform-density world -- no interface, no bend.
    # The refracted ray must continue STRAIGHT: hits == the straight-line plane intersection.
    ref_add1, hits1 = optics.refraction_reference(
        buf, np.asarray(cam.position, np.float64), (1.0, 1.0, 1.0), floor_z, absorb,
        origin, cell, grid_rgb, grid_has)
    p = buf[:n_surf, [matter.PX, matter.PY, matter.PZ]].astype(np.float64)
    d = p - np.asarray(cam.position, np.float64)[None, :]
    ss = (floor_z - p[:, 2]) / d[:, 2]
    straight = p[:, :2] + d[:, :2] * ss[:, None]
    fin = np.isfinite(hits1[:n_surf, 0, 0])
    gap = np.abs(hits1[:n_surf, 0, :][fin] - straight[fin])
    check("T7 clay control: eta=1 (uniform density) bends NOTHING -- straight-line identity",
          float(gap.max()) <= optics.EPS_HIT, f"max deviation {float(gap.max()):.2e}")

    pipe.set_refraction(None)
    img_off2 = pipe.render_from_gpu(cam, prm)
    check("T7 control: REFRACT-flagged buffer with no set_refraction -> bit-identical",
          np.array_equal(img_off2, img_base))

    try:
        from PIL import Image
        Image.fromarray(img_base).save(ROOT / "agent_logs" / "optics_refraction_off.png")
        Image.fromarray(img_on).save(ROOT / "agent_logs" / "optics_refraction_on.png")
        print("[art ] agent_logs/optics_refraction_{off,on}.png written", flush=True)
    except Exception as e:
        print(f"[art ] PNG save skipped: {e}", flush=True)
    return buf, n_surf, n_w, origin, cell, grid_rgb, grid_has, floor_z, cam, prm


def t8_caustics(n_w: float):
    amp, k, depth = 0.0119, 12.566, 4.2 * 0.5            # g ~ 2: bands exist and are separated
    eta = 1.0 / n_w
    depth = 1.0 / ((1.0 - eta) * amp * k * k) * 2.0      # DERIVE depth so g = 2 exactly
    xs = np.linspace(0.0, 1.0, 2000)
    ys = np.linspace(0.0, 0.05, 12)
    gx, gy = np.meshgrid(xs, ys)
    pos = np.stack([gx.ravel(), gy.ravel(), np.zeros(gx.size)], axis=1)
    slope = amp * k * np.cos(k * pos[:, 0])
    nrm = np.stack([-slope, np.zeros(len(pos)), np.ones(len(pos))], axis=1)
    cell = 0.005
    hist, n_dep = optics.caustic_deposit(pos, nrm, (0.0, 0.0, 1.0), eta, -depth,
                                         (-0.25, -0.25), cell, (120, 300))
    check("T8 caustics: energy is conserved EXACTLY (redistribution, never creation)",
          float(hist.sum()) == float(n_dep), f"deposited {n_dep}, summed {hist.sum():.0f}")

    pred = optics.sine_caustic_zeros(amp, k, eta, depth)
    check("T8 caustics: the geometry folds (analytic bands exist at derived depth)", pred is not None,
          f"depth {depth:.3f}")
    col = hist.sum(axis=0)
    xcents = -0.25 + (np.arange(300) + 0.5) * cell
    period = 2.0 * np.pi / k
    win = (xcents >= 0.0) & (xcents < period)
    cw = col[win].copy(); xw = xcents[win]
    p1 = float(xw[np.argmax(cw)])
    half = period / 2.0
    other = (xw < p1 - 0.05) | (xw > p1 + 0.05)
    p2 = float(xw[other][np.argmax(cw[other])])
    got = sorted([p1 % period, p2 % period])
    want = sorted([p % period for p in pred])
    err = max(abs(g - w) for g, w in zip(got, want))
    check("T8 caustics: deposited band positions match the analytic det-J zeros",
          err <= optics.EPS_CAUSTIC_CELLS * cell,
          f"got {got[0]:.4f}/{got[1]:.4f}, analytic {want[0]:.4f}/{want[1]:.4f}, err {err:.4f}")


def t9_dispersion(t7_state):
    buf, n_surf, n_w, origin, cell, grid_rgb, grid_has, floor_z, cam, prm = t7_state
    sea = published("aSaltOcean")
    absorb = [float(a) for a in sea["absorption_rgb_measured"]]
    rho = float(sea["density_surface_kg_m3"])
    r_d = matter.SPECIFIC_REFRACTION_CM3_G["water"]
    n_d_lit = matter.WATER_N_BY_CHANNEL["G"]
    etas = []
    for c in ("R", "G", "B"):
        r_c = matter.dispersive_refraction(r_d, n_d_lit, matter.WATER_N_BY_CHANNEL[c])
        etas.append(1.0 / matter.refractive_index(rho, r_c))
    check("T9 dispersion: measured indices order the etas (red bends least)",
          etas[0] > etas[1] > etas[2], f"etas {etas[0]:.5f} > {etas[1]:.5f} > {etas[2]:.5f}")

    n_all = len(buf)
    pipe = gp.FullGPUPipeline()
    pipe.upload(buf)
    pipe.set_light(None)
    pipe.set_refraction(None)
    base = grain_colours(pipe, n_all); img_base = pipe.render_from_gpu(cam, prm)
    base = grain_colours(pipe, n_all)
    pipe.set_refraction(tuple(etas), floor_z, absorb, origin, cell, grid_rgb, grid_has)
    img_on = pipe.render_from_gpu(cam, prm)
    kadd = grain_colours(pipe, n_all).astype(np.float64) - base.astype(np.float64)

    ref_add, ref_hits = optics.refraction_reference(
        buf, np.asarray(cam.position, np.float64), etas, floor_z, absorb,
        origin, cell, grid_rgb, grid_has)
    diff = np.abs(kadd - ref_add)
    check("T9 dispersion: kernel vs float64 referee per channel, max |diff|",
          float(diff.max()) <= optics.EPS_TRANS_MAX, f"max {float(diff.max()):.2e}")

    fin = np.isfinite(ref_hits[:n_surf, 0, 0]) & np.isfinite(ref_hits[:n_surf, 2, 0])
    sep = np.linalg.norm(ref_hits[:n_surf, 0, :][fin] - ref_hits[:n_surf, 2, :][fin], axis=1)
    # THE GATE IS FLOAT NOISE, NOT THE GRID CELL. The first version of this check demanded the
    # R-B separation exceed one floor cell and FAILED on correct physics: water's measured
    # dispersion (delta-n ~ 0.006) separates the rays by ~0.006 scene units here, which IS the
    # right magnitude -- the cell is a property of the container, not of dispersion. A threshold
    # must come from outside the thing measured: 10x EPS_HIT says "geometric, not numeric".
    check("T9 dispersion: R and B rays land in DIFFERENT places (separation >> float noise)",
          float(np.median(sep)) > 10.0 * optics.EPS_HIT,
          f"median separation {float(np.median(sep)):.5f} vs noise gate {10.0 * optics.EPS_HIT:.0e}; "
          f"cell {cell:.4f} -- fringes surface on the ~{100.0 * float(np.median(sep)) / cell:.0f}% "
          f"of grains whose R/B cells differ")
    try:
        from PIL import Image
        Image.fromarray(img_on).save(ROOT / "agent_logs" / "optics_dispersion_on.png")
        print("[art ] agent_logs/optics_dispersion_on.png written", flush=True)
    except Exception as e:
        print(f"[art ] PNG save skipped: {e}", flush=True)


# ═══ T10 -- ONE-BOUNCE INTERREFLECTION (Stage 6) ═════════════════════════════════════════════════
def _two_planes(n_b_side: int):
    """An emitting wall (x=0, facing +x, radiance L=5) and a receiving floor (z=0, facing +z).
    Every geometric factor derived from the construction; albedo mid-grey."""
    sa = 14
    a = np.linspace(0.05, 0.95, sa)
    ay, az = np.meshgrid(a, a)
    pa = np.stack([np.zeros(sa * sa), ay.ravel(), az.ravel()], axis=1)
    na = np.tile([1.0, 0.0, 0.0], (sa * sa, 1))
    La = np.full(sa * sa, 5.0)
    area_a = np.full(sa * sa, float(a[1] - a[0]) ** 2)
    b1 = np.linspace(0.02, 1.0, n_b_side)
    b2 = np.linspace(0.0, 1.0, n_b_side)
    bx, by = np.meshgrid(b1, b2)
    pb = np.stack([bx.ravel(), by.ravel(), np.zeros(bx.size)], axis=1)
    nb = np.tile([0.0, 0.0, 1.0], (bx.size, 1))
    Lb = np.zeros(bx.size)
    area_b = np.full(bx.size, float(b1[1] - b1[0]) * float(b2[1] - b2[0]))
    pos = np.concatenate([pa, pb]); nrm = np.concatenate([na, nb])
    L = np.concatenate([La, Lb]); A = np.concatenate([area_a, area_b])
    alb = np.tile([0.5, 0.45, 0.40], (len(pos), 1))
    return pos, nrm, L, A, alb, sa * sa


def t10_bounce():
    import time
    pos, nrm, L, A, alb, n_src = _two_planes(28)
    ref = optics.bounce_reference(pos, nrm, A, L, alb)
    # THE FIRST CAP CONSTRUCTION WAS REFUTED BY ITS OWN TEST and replaced: comparing the tail
    # BOUND to the prefix BOUND let grazing receivers drop >1% of their ACTUAL energy (bounds use
    # cos <= 1). bounce_gather_guaranteed stops on tail_bound <= frac * actual_kept, which bounds
    # the true relative error by frac, provably. The refuted version stays in optics.py history.
    got, pairs = optics.bounce_gather_guaranteed(pos, nrm, A, L, alb, frac=0.01)
    lit = ref.max(axis=1) > 0.0
    rel = np.abs(got[lit] - ref[lit]) / np.maximum(ref[lit], 1e-300)
    check("T10 bounce: guaranteed gather vs uncapped float64 referee (rel err <= frac, PROVABLY)",
          float(rel.max()) <= optics.EPS_BOUNCE_REL,
          f"max rel {float(rel.max()):.2e}; used {pairs} of {len(pos) * n_src} pairs "
          f"({100.0 * pairs / (len(pos) * n_src):.0f}% -- a near-uniform wall is the cap's "
          f"hardest scene, and it says so rather than lying)")
    check("T10 bounce: the wall actually lights the floor", int(lit.sum()) > len(pos) // 2,
          f"{int(lit.sum())} of {len(pos)} grains receive")
    zero, _ = optics.bounce_gather_guaranteed(pos, nrm, A, L, np.zeros_like(alb), frac=0.01)
    check("T10 bounce: albedo -> 0 makes the bounce vanish BIT-FOR-BIT",
          float(np.abs(zero).max()) == 0.0)
    x = pos[n_src:, 0]
    near = ref[n_src:][x < 0.3].mean()
    far = ref[n_src:][x > 0.7].mean()
    check("T10 bounce: irradiance falls off with distance from the wall (1/r^2 is alive)",
          near > 2.0 * far, f"near {near:.4f} vs far {far:.4f}")

    times, ns = [], []
    for side in (22, 30, 42, 58):
        p2, n2, L2, A2, alb2, _ = _two_planes(side)
        t0 = time.perf_counter()
        optics.bounce_gather_guaranteed(p2, n2, A2, L2, alb2, frac=0.01)
        times.append(time.perf_counter() - t0)
        ns.append(len(p2))
    ns_a = np.asarray(ns, float); ts = np.asarray(times, float)
    slope, icpt = np.polyfit(ns_a, ts, 1)
    pred = slope * ns_a + icpt
    r2 = 1.0 - float(np.sum((ts - pred) ** 2)) / float(np.sum((ts - ts.mean()) ** 2))
    check(f"T10 bounce: gather cost is LINEAR in N at fixed sources (R^2 >= {optics.EPS_BOUNCE_R2})",
          r2 >= optics.EPS_BOUNCE_R2,
          f"R^2 = {r2:.4f} over N = {ns} ({[f'{t*1000:.0f}ms' for t in times]})")


def main() -> int:
    t1_stage0_closure()
    t2_one_source()
    t6_slider_closure()

    sea = published("aSaltOcean")
    ter = published("aTerrain")
    gnd = published("theGround")

    n_sea = matter.refractive_index(sea["density_surface_kg_m3"],
                                    matter.SPECIFIC_REFRACTION_CM3_G["water"])
    render_case("water",
                rho=sea["density_surface_kg_m3"],
                f0=matter.fresnel_f0(n_sea),
                slope=float(sea["surface_slope_mean"]),
                rgb=tuple(np.clip(sea["ocean_rgb_shallow"], 0.0, 1.0) * 0.35),
                save_png=True)

    n_gnd = matter.refractive_index(gnd["bulk_density"],
                                    matter.SPECIFIC_REFRACTION_CM3_G["silicate"])
    render_case("ground",
                rho=float(gnd["bulk_density"]),
                f0=matter.fresnel_f0(n_gnd),
                slope=float(np.tan(np.radians(ter["mean_slope_deg"]))),
                rgb=(0.30, 0.25, 0.20),
                save_png=True)

    t7_state = t7_refraction()
    t8_caustics(t7_state[2])
    t9_dispersion(t7_state)
    t10_bounce()

    print(f"\n{_PASS} passed, {_FAIL} failed", flush=True)
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
