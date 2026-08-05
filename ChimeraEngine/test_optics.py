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

    print(f"\n{_PASS} passed, {_FAIL} failed", flush=True)
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
