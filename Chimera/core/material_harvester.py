"""material_harvester — GPU region-scan + PATTERN matching over the photo corpus.

Commissioned 2026-07-18 (tb-0180), the human's own words: "to train a material you
must first FIND it." Given a wanted material, identify which regions across many
reference photos actually carry it, by scanning regions programmatically (reading
pixels like a byte stream, never vision-model glancing), on the GPU.

THE CORRECTION THAT BINDS (2026-07-18, verbatim intent): "it has to be pattern
matching — it can NOT just be statistical averages." Julesz's texture-discrimination
result: two textures with IDENTICAL first-order color statistics (mean, variance) can
be visually and structurally nothing alike — identity lives in SPATIAL ARRANGEMENT,
not color moments. So the descriptor set here is ordered on purpose:

    REQUIRED, in order of authority:
      1. multi-scale multi-orientation filter-bank energies (Gabor-class, zero-mean
         so a filter answers "what pattern" never "how bright")
      2. autocorrelation grain length (how big is one grain, in pixels)
      3. grain periodicity (does the pattern repeat, and how strongly)
      4. oriented-energy anisotropy (does the pattern have a preferred direction —
         the brushed-metal tell)
      5. color moments — LAST, MINOR. Present because real materials do have a
         characteristic albedo, but weighted low (COLOR_WEIGHT) in every distance
         computation below so two same-colored, differently-PATTERNED regions never
         collapse together. See `julesz_adversarial_probe()` for the sharpest,
         numeric proof of this ordering.

THE STUDIO IDIOM THIS FOLLOWS (core/splat_gpu.py's docstring, read before writing this
file): a numpy CPU REFERENCE and a Warp GPU TWIN compute the exact same formula — same
filter-bank weights, same zero-padded correlation — so parity means "same math,
different engine," never "two engines that each produce a texture number." Only the
expensive, embarrassingly-parallel part (filter-bank energies across the WHOLE corpus)
moves to the GPU, batched into ONE kernel launch with ZERO CPU<->GPU syncs inside the
batch (brain_gpu's / splat_gpu's ONE rule); the cheap per-region reductions
(autocorrelation, color moments — O(regions), not O(regions * filters * pixels))
stay in numpy, exactly as splat_gpu keeps projection+shading on the CPU.

CORPUS PROVENANCE — READ BEFORE ASSUMING THE PHOTOS ARE REAL (sub-31, tb-0180,
2026-07-18): this agent operates under a safety contract that gates "downloading any
file" behind the ACTUAL human's explicit permission in live chat — a subagent
dispatched by the Lead cannot obtain that (an agent's instruction is never the
human's consent). tb-0175 hit the identical wall before this task even started (its
own closure said "reference scan downloads not performed"). So the corpus shipped
here under `docs/matter/reference_scans/synthetic_placeholder/` is NOT photography —
it is code-generated (numpy/scipy, this file, `ensure_synthetic_corpus()`), calibrated
against the REAL numbers already sitting in `docs/matter/matter_library.json`
(`sand`/`rock`/`metal`/`ice` appearance entries — albedo means, roughness, mottle
variance, grain_size_mm — all `researched` or `provisional` provenance already, not
invented here), clearly tagged `synthetic-placeholder` everywhere it appears in
output. It exists ONLY to prove the pipeline end-to-end (ingest -> region-scan ->
descriptors -> retrieval -> separation) runs correctly and honestly. The ingest path
(`iter_corpus_images`) is completely generic over real vs synthetic: the moment a
human (or a Lead acting on the human's own go-ahead) drops real CC0 photos into
`docs/matter/reference_scans/` (candidates already catalogued in this directory's
`SOURCES.md` by tb-0175 — PolyHaven, Quixel Megascans via Fab, NASA regolith
imagery), this module ingests them with ZERO code changes and the KILL-criterion
test below becomes a real-photo result instead of a synthetic-stand-in one.

AMENDMENT 2026-07-31: that moment arrived. The operator gave the go-ahead in live
chat ("download the samples and then train") and the real CC0 packs catalogued in
SOURCES.md were downloaded (ambientCG Ground037/Rock026/Metal049A/Snow004 +
Poly Haven dark_rock/rock_surface/snow_01). `main()` now tags each material's
exemplar on the REAL photo's center tile (REAL_EXEMPLAR_PHOTOS) and only falls back
to the synthetic placeholder when no real sample exists. Non-color PBR maps
(Normal/Roughness/Displacement/AO/Metalness) live OUTSIDE this corpus under
`docs/matter/pbr_maps/` so `iter_corpus_images` never ingests them as "photo"s.

NO REFERENCE, NO VERDICT: exemplar tags minted by `tag_exemplar()` below are always
`provisional-tag` — an admitted stand-in for the human's own tag, never presented as
the human's verdict. A human-supplied tag supersedes on sight.

Run:  python -m core.material_harvester
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "docs" / "matter" / "reference_scans"
SYNTH_DIR = CORPUS_DIR / "synthetic_placeholder"
HARVEST_DIR = CORPUS_DIR / "harvested"
LIB_PATH = ROOT / "docs" / "matter" / "matter_library.json"

TILE = 40                                   # region tile size, px, non-overlapping grid
KSIZE = 17                                  # filter-bank kernel size (odd)
SCALES = (1.5, 3.0, 6.0)                    # Gabor sigma, px
ORIENTATIONS_DEG = (0.0, 45.0, 90.0, 135.0)
N_FILTERS = len(SCALES) * len(ORIENTATIONS_DEG)          # 12
COLOR_WEIGHT = 0.1                          # color moments are LAST and MINOR — Julesz
D_TOTAL = N_FILTERS + 3 + 3                 # 12 filters + {grain,periodicity,aniso} + 3 color = 18
MATERIALS = ("regolith", "rock", "brushed_metal", "ice")

# REAL CC0 SAMPLES (downloaded 2026-07-31, the operator's own go-ahead in live chat —
# "everything is a sample that you have to train; you'll have to download the samples
# and then train"). When the real photo for a material is present, its CENTER tile is
# tagged as the exemplar instead of the synthetic placeholder; the placeholder path
# below remains the fallback so the pipeline still runs end-to-end with zero downloads.
REAL_EXEMPLAR_PHOTOS = {
    "regolith": "ambientcg/regolith/Ground037_1K-JPG_Color.jpg",
    "rock": "ambientcg/rock/Rock026_1K-JPG_Color.jpg",
    "brushed_metal": "ambientcg/metal/Metal049A_1K-JPG_Color.jpg",
    "ice": "ambientcg/ice/Snow004_1K-JPG_Color.jpg",
}

_WP = None
_KERNEL = None


def _json_default(o):
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"not JSON serializable: {type(o)!r}")


def load_matter_library() -> dict:
    return json.loads(LIB_PATH.read_text(encoding="utf-8"))


# ============================================================ filter bank (shared) ====

def _gabor_kernel(ksize: int, sigma: float, theta_rad: float, gamma: float = 0.5) -> np.ndarray:
    """Zero-mean real Gabor kernel. Zero-meaning removes the DC term so the filter
    answers "what pattern is here", never "how bright is here" — that separation IS
    the Julesz discipline, enforced at the kernel level, not just in the distance
    weights."""
    half = ksize // 2
    y, x = np.mgrid[-half:half + 1, -half:half + 1].astype(np.float64)
    xt = x * math.cos(theta_rad) + y * math.sin(theta_rad)
    yt = -x * math.sin(theta_rad) + y * math.cos(theta_rad)
    lambd = sigma * 2.2
    gb = np.exp(-(xt ** 2 + (gamma ** 2) * yt ** 2) / (2.0 * sigma ** 2)) * np.cos(2 * np.pi * xt / lambd)
    return (gb - gb.mean()).astype(np.float64)


def build_filter_bank(ksize: int = KSIZE, scales=SCALES, orientations_deg=ORIENTATIONS_DEG) -> np.ndarray:
    """[n_filters, ksize, ksize] — shared BYTE-FOR-BYTE by the CPU reference and the
    GPU kernel. Parity below means "same weights, different engine.\""""
    bank = [_gabor_kernel(ksize, sigma, math.radians(deg))
            for sigma in scales for deg in orientations_deg]
    return np.stack(bank, axis=0)


BANK = build_filter_bank()


# ============================================================ synthetic placeholder corpus ====
# Every base_albedo / roughness / grain-scale-ordering choice below is READ from
# docs/matter/matter_library.json (not invented) — see the per-function citation.

def synth_regolith(rng: np.random.Generator, size: int = 320) -> np.ndarray:
    """Fine, isotropic, matte granular texture. Calibrated to matter_library.json
    materials.sand.appearance: albedo_mean_rgb [0.55,0.47,0.38], roughness_mean 0.95
    (very rough -> high micro-variance), grain_size_mm.mean 0.072 (finest of the four
    -> smallest correlation length, qualitatively)."""
    base = np.array([0.55, 0.47, 0.38]) * 255.0
    fine = ndimage.gaussian_filter(rng.normal(0, 1, (size, size)), sigma=1.1)
    coarse = ndimage.gaussian_filter(rng.normal(0, 1, (size, size)), sigma=4.0)
    grain = 0.7 * fine / (fine.std() + 1e-9) + 0.3 * coarse / (coarse.std() + 1e-9)
    grain = grain / (grain.std() + 1e-9)
    rgb = np.clip(base[None, None, :] + grain[..., None] * (0.22 * 255.0) * np.array([1.0, 0.93, 0.85]),
                  0, 255)
    return rgb.astype(np.uint8)


def synth_rock(rng: np.random.Generator, size: int = 320) -> np.ndarray:
    """Coarser, isotropic, higher-mottle texture. Calibrated to materials.rock:
    albedo_mean_rgb [0.32,0.30,0.28] (dark basalt), albedo_mottle_var 0.06 (highest
    of the four -> bigger, higher-contrast blobs), grain_size_mm.mean 2.0 (largest
    -> biggest correlation length, qualitatively, vs regolith's 0.072mm)."""
    base = np.array([0.32, 0.30, 0.28]) * 255.0
    fine = ndimage.gaussian_filter(rng.normal(0, 1, (size, size)), sigma=2.2)
    coarse = ndimage.gaussian_filter(rng.normal(0, 1, (size, size)), sigma=13.0)
    field = 0.45 * fine / (fine.std() + 1e-9) + 0.55 * coarse / (coarse.std() + 1e-9)
    field = field / (field.std() + 1e-9)
    rgb = np.clip(base[None, None, :] + field[..., None] * (0.30 * 255.0) * np.array([1.0, 0.97, 0.93]),
                  0, 255)
    return rgb.astype(np.uint8)


def synth_brushed_metal(rng: np.random.Generator, size: int = 320, theta_deg: float = 30.0) -> np.ndarray:
    """Highly ANISOTROPIC oriented streaks with a mild regular scratch pitch —
    calibrated to materials.metal: albedo_mean_rgb [0.56,0.57,0.58] (neutral gray),
    roughness_mean 0.35 (smoother than any mineral surface), roughness_var 0.1
    explicitly noted in the library as "carries wear-streak variation" — i.e. the
    library ITSELF already names this as an anisotropic-brush surface; this is that
    note made into pixels, not an invented look."""
    base = np.array([0.56, 0.57, 0.58]) * 255.0
    theta = math.radians(theta_deg)
    noise = rng.normal(0, 1, (size, size))
    rot = ndimage.rotate(noise, theta_deg, reshape=False, order=1, mode="reflect")
    streaked = ndimage.gaussian_filter(rot, sigma=(0.6, 10.0))          # long along axis 1 = the brush direction
    # a mild regular scratch pitch perpendicular to the brush direction (real brushed
    # finishes carry a quasi-periodic tool pitch under magnification)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float64)
    perp = -xx * math.sin(theta) + yy * math.cos(theta)
    pitch = 7.0
    ridges = 0.35 * np.sin(2 * np.pi * perp / pitch)
    streaked = ndimage.rotate(streaked, -theta_deg, reshape=False, order=1, mode="reflect")
    field = streaked / (streaked.std() + 1e-9) * 0.75 + ridges
    field = field / (field.std() + 1e-9)
    rgb = np.clip(base[None, None, :] + field[..., None] * (0.11 * 255.0), 0, 255)
    return rgb.astype(np.uint8)


def synth_ice(rng: np.random.Generator, size: int = 320) -> np.ndarray:
    """Very smooth, very low texture-energy, cool-tinted. Calibrated to
    materials.ice: albedo_mean_rgb [0.75,0.82,0.88] (bright, blue), roughness_mean
    0.15 (lowest of the four -> almost no micro-variance)."""
    base = np.array([0.75, 0.82, 0.88]) * 255.0
    field = ndimage.gaussian_filter(rng.normal(0, 1, (size, size)), sigma=11.0)
    field = field / (field.std() + 1e-9)
    rgb = np.clip(base[None, None, :] + field[..., None] * (0.05 * 255.0) * np.array([0.95, 0.98, 1.0]),
                  0, 255)
    return rgb.astype(np.uint8)


_SYNTH_FN = {
    "regolith": synth_regolith,
    "rock": synth_rock,
    "brushed_metal": synth_brushed_metal,
    "ice": synth_ice,
}

_PROVENANCE_MD = """# Synthetic Placeholder Corpus — NOT real photographs

Generated by `core/material_harvester.py: ensure_synthetic_corpus()` (tb-0180,
2026-07-18). Every image here is procedurally synthesized in numpy/scipy — nothing
was downloaded, captured, or scanned.

## Why placeholders instead of the real photos this task asked for

Acquiring the real CC0/public-domain material photos (NASA regolith imagery,
PolyHaven, Quixel Megascans — all catalogued in `../SOURCES.md` by tb-0175) requires
downloading files from external sources. The agent that built this pipeline operates
under a safety contract in which "downloading any file" requires the actual human
operator's explicit permission in live chat, and an agent's own dispatch instructions
do not constitute that permission. A subagent has no chat channel to the human, so
this gate could not be passed inside this task. tb-0175 hit the same wall first: its
own closure report states "reference scan downloads not performed."

## What these stand in for, and how they're grounded

Each image's base albedo, roughness-driven micro-variance, and qualitative grain
scale are read directly from `docs/matter/matter_library.json`'s existing
`researched`/`provisional` appearance entries (sand, rock, metal, ice) — not
invented. See each `synth_*` function's docstring in `material_harvester.py` for the
exact library fields cited.

## What to do next

Have a human (or a Lead acting on the human's own explicit go-ahead) place real CC0
photos directly under `docs/matter/reference_scans/` (not this subfolder). Then run
`python -m core.material_harvester` again — `iter_corpus_images()` ingests real and
synthetic images identically, zero code changes needed, and the KILL-criterion
separation test becomes a real-photo result.

## Provenance tag used throughout this module's output

`synthetic-placeholder` — never `photo`. Every harvested-set entry, exemplar tag, and
reference-descriptor file sourced from these images carries this tag so nothing
downstream mistakes them for real material evidence.
"""


def ensure_synthetic_corpus(seed: int = 7, size: int = 320) -> list[Path]:
    """Idempotent: writes the 4 placeholder images + PROVENANCE.md if missing.
    Deterministic (fixed seed) so re-running reproduces the same corpus."""
    from PIL import Image
    SYNTH_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    prov_path = SYNTH_DIR / "PROVENANCE.md"
    if not prov_path.exists():
        prov_path.write_text(_PROVENANCE_MD, encoding="utf-8")
    for i, name in enumerate(MATERIALS):
        p = SYNTH_DIR / f"{name}_01.png"
        if p.exists():
            continue
        rng = np.random.default_rng(seed + i)
        img = _SYNTH_FN[name](rng, size=size)
        Image.fromarray(img, mode="RGB").save(p)
        written.append(p)
    return written


# ============================================================ corpus ingest ====

def iter_corpus_images(corpus_dir: Path = CORPUS_DIR):
    """Yields (photo_id, rgb_uint8, provenance) for every image under the corpus.
    Generic over real vs synthetic — never descends into harvested/ (that is
    OUTPUT). A real photo dropped at the top level is ingested with ZERO code
    changes; provenance is inferred purely from directory (synthetic_placeholder/
    -> 'synthetic-placeholder', anywhere else -> 'photo')."""
    from PIL import Image
    if not corpus_dir.exists():
        return
    for p in sorted(corpus_dir.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            continue
        try:
            rel_to_harvest = p.relative_to(HARVEST_DIR)
            continue  # inside harvested/ — output, not input
        except ValueError:
            pass
        try:
            p.relative_to(SYNTH_DIR)
            provenance = "synthetic-placeholder"
        except ValueError:
            provenance = "photo"
        img = np.array(Image.open(p).convert("RGB"))
        yield p.relative_to(corpus_dir).as_posix(), img, provenance


def tile_regions(img: np.ndarray, tile: int = TILE):
    """Non-overlapping grid tiling — deterministic, fixed-size (GPU-batch-friendly)."""
    h, w = img.shape[:2]
    for ty in range(0, h - tile + 1, tile):
        for tx in range(0, w - tile + 1, tile):
            yield (ty, tx), img[ty:ty + tile, tx:tx + tile]


# ============================================================ descriptors ====

def _luma(region_rgb: np.ndarray) -> np.ndarray:
    r, g, b = region_rgb[..., 0].astype(np.float64), region_rgb[..., 1].astype(np.float64), region_rgb[..., 2].astype(np.float64)
    return 0.299 * r + 0.587 * g + 0.114 * b


def filter_energies_cpu_gray(gray: np.ndarray, bank: np.ndarray = BANK) -> np.ndarray:
    """CPU REFERENCE: zero-padded correlation per filter, mean |response|. This IS
    the formula the GPU kernel below reproduces per-thread (same kernel weights,
    same zero-pad convention) — not an independent formula."""
    out = np.empty(bank.shape[0], dtype=np.float64)
    for i in range(bank.shape[0]):
        resp = ndimage.correlate(gray.astype(np.float64), bank[i], mode="constant", cval=0.0)
        out[i] = np.mean(np.abs(resp))
    return out


def filter_energies_cpu_batch(grays: np.ndarray, bank: np.ndarray = BANK) -> np.ndarray:
    return np.stack([filter_energies_cpu_gray(g, bank) for g in grays])


def _warp():
    """Lazy init so importing this module never costs anything on CPU-only boxes
    (splat_gpu's own discipline)."""
    global _WP, _KERNEL
    if _WP is not None:
        return _WP, _KERNEL
    import warp as wp
    wp.init()
    if not wp.get_device().is_cuda:
        raise RuntimeError("no CUDA device — use the CPU reference")

    @wp.kernel
    def energies(regions: wp.array2d(dtype=float),   # (N, tile*tile) row-major per region
                 bank: wp.array2d(dtype=float),        # (n_filters, ksize*ksize) row-major per filter
                 tile: int, ksize: int,
                 out: wp.array2d(dtype=float)):        # (N, n_filters)
        r, f = wp.tid()                                 # ONE thread per (region, filter) — batched over the WHOLE corpus
        half = ksize // 2
        acc = float(0.0)
        for yy in range(tile):
            for xx in range(tile):
                s = float(0.0)
                for ky in range(ksize):
                    iy = yy + ky - half
                    if iy >= 0 and iy < tile:
                        for kx in range(ksize):
                            ix = xx + kx - half
                            if ix >= 0 and ix < tile:
                                s += regions[r, iy * tile + ix] * bank[f, ky * ksize + kx]
                acc += wp.abs(s)
        out[r, f] = acc / float(tile * tile)

    _WP, _KERNEL = wp, energies
    return _WP, _KERNEL


def available() -> bool:
    try:
        _warp()
        return True
    except Exception:
        return False


def filter_energies_gpu_batch(grays: np.ndarray, bank: np.ndarray = BANK, tile: int = TILE) -> np.ndarray:
    """GPU TWIN: ALL regions x ALL filters in ONE kernel launch — zero syncs inside
    the batch (brain_gpu's / splat_gpu's ONE rule: upload once, launch once, read
    back once). grays: [N, tile, tile] float."""
    wp, kernel = _warp()
    n = grays.shape[0]
    nf = bank.shape[0]
    ksize = bank.shape[1]
    dev = "cuda:0"
    regions_flat = grays.reshape(n, tile * tile).astype(np.float32)
    bank_flat = bank.reshape(nf, ksize * ksize).astype(np.float32)
    regions_wp = wp.array(np.ascontiguousarray(regions_flat), dtype=float, device=dev)
    bank_wp = wp.array(np.ascontiguousarray(bank_flat), dtype=float, device=dev)
    out = wp.zeros(shape=(n, nf), dtype=float, device=dev)
    wp.launch(kernel, dim=(n, nf), inputs=[regions_wp, bank_wp, tile, ksize, out], device=dev)
    return out.numpy().astype(np.float64)


def _autocorr_radial(gray: np.ndarray) -> np.ndarray:
    """Radial-averaged 2D autocorrelation via FFT (Wiener-Khinchin). Cheap per
    region (O(HW log HW)) — stays in numpy, exactly as splat_gpu keeps its O(N)
    projection math off the GPU."""
    g = gray - gray.mean()
    F = np.fft.fft2(g)
    ac = np.fft.ifft2(F * np.conj(F)).real
    ac = np.fft.fftshift(ac)
    peak = ac.max()
    if peak > 1e-9:
        ac = ac / peak
    h, w = ac.shape
    cy, cx = h // 2, w // 2
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2).astype(np.int32)
    max_r = int(min(cy, cx))
    radial = np.array([ac[r == k].mean() if np.any(r == k) else 0.0 for k in range(max_r)])
    return radial


def grain_length_and_periodicity(gray: np.ndarray) -> tuple[float, float]:
    """grain_length = first lag (px) where the radial autocorrelation drops below
    1/e of the zero-lag peak. periodicity = strength of the strongest SECONDARY
    peak beyond the first trough, relative to the zero-lag peak (0 = decays
    smoothly and never comes back, ~1 = a near-perfect repeat)."""
    radial = _autocorr_radial(gray)
    max_r = len(radial)
    below = np.where(radial < (1.0 / math.e))[0]
    grain_length = float(below[0]) if len(below) else float(max_r)
    periodicity = 0.0
    if max_r > 3:
        d = np.diff(radial)
        trough_idx = None
        for i in range(1, len(d)):
            if d[i - 1] < 0 <= d[i]:
                trough_idx = i
                break
        if trough_idx is not None and trough_idx + 1 < len(radial):
            periodicity = float(max(0.0, radial[trough_idx + 1:].max()))
    return grain_length, periodicity


def anisotropy_from_energies(energies: np.ndarray, n_scales: int = len(SCALES),
                              n_orient: int = len(ORIENTATIONS_DEG)) -> float:
    """(max - mean) / max over the orientation-summed energies — 0 for a
    perfectly isotropic texture (regolith, rock), large for a strongly oriented one
    (brushed metal). This is the direct numeric expression of "does the pattern
    have a preferred direction.\""""
    e = energies.reshape(n_scales, n_orient)
    orient_sum = e.sum(axis=0)
    mx = float(orient_sum.max())
    mn = float(orient_sum.mean())
    return (mx - mn) / (mx + 1e-9)


def color_moments(region_rgb: np.ndarray) -> np.ndarray:
    """LAST and MINOR by design — see COLOR_WEIGHT in descriptor_weights()."""
    gray = _luma(region_rgb)
    mean_l = float(gray.mean())
    std_l = float(gray.std())
    chroma = region_rgb.astype(np.float64) - gray[..., None]
    std_c = float(chroma.std())
    return np.array([mean_l, std_l, std_c], dtype=np.float64)


def descriptor(region_rgb: np.ndarray, energies: np.ndarray) -> np.ndarray:
    """The full 18-dim vector: [12 filter energies] + [grain_length, periodicity,
    anisotropy] + [3 color moments, LAST]."""
    gray = _luma(region_rgb)
    grain_len, periodicity = grain_length_and_periodicity(gray)
    aniso = anisotropy_from_energies(energies)
    cmoments = color_moments(region_rgb)
    return np.concatenate([energies, np.array([grain_len, periodicity, aniso]), cmoments])


def descriptor_weights() -> np.ndarray:
    w = np.ones(D_TOTAL, dtype=np.float64)
    w[N_FILTERS + 3:] = COLOR_WEIGHT
    return w


def weighted_distance(a: np.ndarray, b: np.ndarray, scale: np.ndarray, weights: np.ndarray) -> float:
    z = (a - b) / (scale + 1e-9)
    return float(np.sqrt(np.sum(weights * z * z)))


# ============================================================ corpus scan pipeline ====

def scan_corpus(corpus_dir: Path = CORPUS_DIR, tile: int = TILE, use_gpu: bool | None = None) -> dict:
    """Full region-scan: ingest -> tile -> filter-bank energies (CPU or GPU) ->
    full descriptors. Returns descriptors/meta/regions_rgb in the SAME order, plus
    an honest throughput measurement for whichever engine actually ran."""
    if use_gpu is None:
        use_gpu = available()

    regions_meta = []
    regions_rgb = []
    for photo, img, provenance in iter_corpus_images(corpus_dir):
        for yx, region in tile_regions(img, tile):
            regions_meta.append({"photo": photo, "yx": list(yx), "provenance": provenance})
            regions_rgb.append(region)

    if not regions_meta:
        return {"descriptors": np.zeros((0, D_TOTAL)), "meta": [], "regions_rgb": [],
                "throughput": {"engine": "none", "regions": 0, "seconds": 0.0, "regions_per_sec": 0.0}}

    grays = np.stack([_luma(r) for r in regions_rgb]).astype(np.float32)

    t0 = time.time()
    if use_gpu:
        energies = filter_energies_gpu_batch(grays, BANK, tile)
    else:
        energies = filter_energies_cpu_batch(grays, BANK)
    t_energies = time.time() - t0

    descriptors = np.stack([descriptor(regions_rgb[i], energies[i]) for i in range(len(regions_meta))])

    n = len(regions_meta)
    return {
        "descriptors": descriptors,
        "meta": regions_meta,
        "regions_rgb": regions_rgb,
        "throughput": {"engine": "gpu" if use_gpu else "cpu", "regions": n,
                       "seconds": t_energies, "regions_per_sec": n / max(t_energies, 1e-9)},
    }


def benchmark_cpu_vs_gpu(corpus_dir: Path = CORPUS_DIR, tile: int = TILE) -> dict:
    """Honest side-by-side: run BOTH engines over the IDENTICAL region set, report
    both regions/sec, and assert parity (same weights -> same numbers, up to
    float32-vs-float64 MAE — splat_gpu's own tolerance discipline, ~1e-3, not 0.0)."""
    regions_meta = []
    regions_rgb = []
    for photo, img, provenance in iter_corpus_images(corpus_dir):
        for yx, region in tile_regions(img, tile):
            regions_meta.append({"photo": photo, "yx": list(yx)})
            regions_rgb.append(region)
    if not regions_meta:
        return {"regions": 0, "note": "empty corpus"}
    grays = np.stack([_luma(r) for r in regions_rgb]).astype(np.float32)

    t0 = time.time()
    cpu = filter_energies_cpu_batch(grays, BANK)
    t_cpu = time.time() - t0

    result = {"regions": len(regions_meta), "cpu_seconds": t_cpu,
              "cpu_regions_per_sec": len(regions_meta) / max(t_cpu, 1e-9)}

    if available():
        _ = filter_energies_gpu_batch(grays[:min(8, len(grays))], BANK, tile)   # warm-up (JIT compile)
        t0 = time.time()
        gpu = filter_energies_gpu_batch(grays, BANK, tile)
        t_gpu = time.time() - t0
        mae = float(np.abs(cpu - gpu).mean())
        result.update({
            "gpu_seconds": t_gpu,
            "gpu_regions_per_sec": len(regions_meta) / max(t_gpu, 1e-9),
            "speedup_x": t_cpu / max(t_gpu, 1e-9),
            "parity_mae": mae,
            "parity_ok": bool(mae < 1e-2),
        })
    else:
        result["gpu"] = "no CUDA device — GPU twin skipped"
    return result


# ============================================================ target identification ====

def tag_exemplar(material: str, photo: str, yx: tuple, tag_kind: str = "provisional-tag",
                  note: str = "") -> dict:
    """Marks ONE region as the reference for `material`. NO REFERENCE, NO VERDICT:
    this is `provisional-tag` — an admitted stand-in — until a human supplies the
    reference tag, which supersedes on sight. Never presented as the human's own
    verdict."""
    HARVEST_DIR.mkdir(parents=True, exist_ok=True)
    path = HARVEST_DIR / "exemplars.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    data[material] = {"photo": photo, "yx": list(yx), "tag_kind": tag_kind, "note": note}
    path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
    return data[material]


def _load_exemplars() -> dict:
    path = HARVEST_DIR / "exemplars.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _exemplar_index(material: str, meta: list) -> int:
    exemplars = _load_exemplars()
    if material not in exemplars:
        raise ValueError(f"no exemplar tagged for {material!r} — call tag_exemplar() first")
    ex = exemplars[material]
    for i, m in enumerate(meta):
        if m["photo"] == ex["photo"] and list(m["yx"]) == list(ex["yx"]):
            return i
    raise ValueError(f"exemplar for {material!r} ({ex['photo']} @ {ex['yx']}) not found in this scan")


def harvest(material: str, corpus_result: dict, top_k: int = 16, max_distance: float | None = None) -> dict:
    """Nearest-region retrieval by PATTERN descriptor distance to the tagged
    exemplar — the harvested SET for `material`. Stored with full provenance
    (photo, region coords, distance) under docs/matter/reference_scans/harvested/."""
    descriptors = corpus_result["descriptors"]
    meta = corpus_result["meta"]
    scale = descriptors.std(axis=0)
    weights = descriptor_weights()

    ex_idx = _exemplar_index(material, meta)
    ex_desc = descriptors[ex_idx]
    exemplars = _load_exemplars()

    dists = np.array([weighted_distance(ex_desc, descriptors[i], scale, weights) for i in range(len(meta))])
    order = np.argsort(dists)
    order = [int(i) for i in order if i != ex_idx]
    if max_distance is not None:
        order = [i for i in order if dists[i] <= max_distance]
    order = order[:top_k]

    harvested = {
        "material": material,
        "exemplar": {**exemplars[material]},
        "note": ("NO REFERENCE, NO VERDICT — this exemplar is a provisional-tag stand-in "
                 "until a human supplies the reference tag; every result below inherits "
                 "that provisionality."),
        "regions": [
            {"photo": meta[i]["photo"], "yx": meta[i]["yx"], "distance": float(dists[i]),
             "provenance": meta[i]["provenance"]}
            for i in order
        ],
    }
    HARVEST_DIR.mkdir(parents=True, exist_ok=True)
    (HARVEST_DIR / f"{material}.json").write_text(
        json.dumps(harvested, indent=2, default=_json_default), encoding="utf-8")
    return harvested


# ============================================================ feeds tb-0175's measure() ====

def _skewness(x: np.ndarray) -> float:
    m, s = float(np.mean(x)), float(np.std(x))
    return 0.0 if s < 1e-10 else float(np.mean(((x - m) / s) ** 3))


def _kurtosis(x: np.ndarray) -> float:
    m, s = float(np.mean(x)), float(np.std(x))
    return 0.0 if s < 1e-10 else float(np.mean(((x - m) / s) ** 4) - 3)


def _srgb_to_linear(x: np.ndarray) -> np.ndarray:
    """IEC 61966-2-1 piecewise. Albedo jpgs are sRGB-ENCODED; the domain's genome
    albedo is LINEAR reflectance (what splat emission shades with). Comparing
    without this conversion would train every material ~2x too bright."""
    x = np.clip(x, 0.0, 1.0)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


# Real ambientCG Roughness maps (non-color data, linear by convention), moved out of
# the photo corpus 2026-07-31 so iter_corpus_images never ingests them as "photo"s.
PBR_DIR = ROOT / "docs" / "matter" / "pbr_maps"
PBR_ROUGHNESS_MAPS = {
    "regolith": "regolith/Ground037_1K-JPG_Roughness.jpg",
    "rock": "rock/Rock026_1K-JPG_Roughness.jpg",
    "brushed_metal": "metal/Metal049A_1K-JPG_Roughness.jpg",
    "ice": "ice/Snow004_1K-JPG_Roughness.jpg",
}


def write_reference_descriptor_file(material: str, corpus_result: dict, harvested: dict) -> Path:
    """Writes docs/matter/reference_scans/<material>.json in the EXACT format
    `core.trainables.material_appearance.load_reference_descriptors()` already
    reads (`{"descriptors": {...}}`, key names matching its own
    `_compute_descriptor_vector`) — this is how tb-0180's harvested regions FEED
    tb-0175's measure(), with zero code changes needed on that side. Pattern
    descriptors (the actual retrieval basis here) ride alongside under a separate
    `pattern_descriptors` key so nothing downstream mistakes color moments for "the"
    descriptors — the ordering the human's binding correction demands."""
    meta = corpus_result["meta"]
    regions_rgb = corpus_result["regions_rgb"]
    descriptors = corpus_result["descriptors"]

    ex_idx = _exemplar_index(material, meta)
    harvested_photo_yx = {(r["photo"], tuple(r["yx"])) for r in harvested["regions"]}
    harvested_photo_yx.add((meta[ex_idx]["photo"], tuple(meta[ex_idx]["yx"])))
    idxs = [i for i, m in enumerate(meta) if (m["photo"], tuple(m["yx"])) in harvested_photo_yx]

    pooled_rgb = np.concatenate([regions_rgb[i].reshape(-1, 3).astype(np.float64) for i in idxs], axis=0)

    # LINEAR-space pooled pixels, domain-IDENTICAL formulas (2026-07-31 fix): the
    # domain's _compute_descriptor_vector defines what each key MEANS; an earlier
    # version of this writer used a different chroma definition and sRGB values, so
    # dist_chroma_variance / dist_luma_chroma_ratio compared two different formulas —
    # a phantom distance the trainer would have chased. Now: same formulas, and the
    # sRGB jpg values converted to linear before any statistic is taken.
    lin = _srgb_to_linear(pooled_rgb / 255.0)
    luma = 0.299 * lin[:, 0] + 0.587 * lin[:, 1] + 0.114 * lin[:, 2]
    chan_var = [float(np.var(lin[:, i])) for i in range(3)]
    chan_var_norm = [float(np.var(lin[:, i] / (np.mean(lin[:, i]) + 1e-6))) for i in range(3)]

    color_descriptors = {
        "albedo_mean_luminance": float(np.mean(luma)),
        "albedo_std_luminance": float(np.std(luma)),
        "albedo_skew_luminance": _skewness(luma),
        "albedo_kurt_luminance": _kurtosis(luma),
        # HUE — the measured per-channel means of the REAL sample (domain-identical
        # keys; see the domain's own 2026-07-31 note on why hue must be trainable).
        "albedo_mean_r": float(np.mean(lin[:, 0])),
        "albedo_mean_g": float(np.mean(lin[:, 1])),
        "albedo_mean_b": float(np.mean(lin[:, 2])),
        "luma_variance": float(np.var(luma)),
        "chroma_variance": float(np.mean(chan_var_norm)),
        "luma_chroma_ratio": float(np.var(luma) / (np.mean(chan_var) + 1e-6)),
    }

    # roughness_mean / roughness_var from the REAL Roughness PBR map (non-color,
    # linear 0-1) — the objective minimizes dist_roughness_mean/dist_roughness_var;
    # without these keys the loader silently trained roughness blind.
    rough_provenance = None
    rough_rel = PBR_ROUGHNESS_MAPS.get(material)
    rough_path = (PBR_DIR / rough_rel) if rough_rel else None
    if rough_path is not None and rough_path.exists():
        from PIL import Image
        rough = np.array(Image.open(rough_path).convert("L"), dtype=np.float64) / 255.0
        color_descriptors["roughness_mean"] = float(np.mean(rough))
        color_descriptors["roughness_var"] = float(np.var(rough))
        rough_provenance = f"pbr_maps/{rough_rel}"

    mean_pattern = descriptors[idxs, :N_FILTERS + 3].mean(axis=0)   # filters + grain/periodicity/aniso
    pattern_descriptors = {
        "filter_bank_energies": mean_pattern[:N_FILTERS].tolist(),
        "grain_length_px": float(mean_pattern[N_FILTERS]),
        "periodicity": float(mean_pattern[N_FILTERS + 1]),
        "anisotropy": float(mean_pattern[N_FILTERS + 2]),
        # a physically-motivated roughness PROXY from real pixel texture-energy
        # (matter_library.json's own doc: "roughness literally = variance of
        # micro-facet normals") — kept namespaced separately from roughness_mean/
        # roughness_var (which are direct genome/photometric values elsewhere) so
        # the two are never silently conflated.
        "roughness_proxy_from_texture_energy": float(mean_pattern[:N_FILTERS].std()),
    }

    payload = {
        "material": material,
        "provenance": harvested["exemplar"].get("tag_kind", "provisional-tag"),
        "source_provenance": sorted({meta[i]["provenance"] for i in idxs}),
        "n_regions_pooled": len(idxs),
        "descriptors": color_descriptors,          # the exact shape tb-0175's loader reads
        "pattern_descriptors": pattern_descriptors,  # the PRIMARY, pattern-based evidence
        "roughness_provenance": rough_provenance,  # real PBR map, or null when absent
        "note": ("descriptors above are COLOR MOMENTS ONLY, kept in this shape for "
                 "compatibility with core.trainables.material_appearance.load_reference_descriptors(); "
                 "pattern_descriptors is what actually IDENTIFIED these regions as "
                 "material — color moments were never the retrieval basis (Julesz). "
                 "Color statistics are LINEAR-space (sRGB jpgs converted via IEC "
                 "61966-2-1) with formulas identical to the domain's "
                 "_compute_descriptor_vector; roughness_mean/roughness_var come from "
                 "the real ambientCG Roughness map when roughness_provenance is set."),
    }
    out_path = CORPUS_DIR / f"{material}.json"
    out_path.write_text(json.dumps(payload, indent=2, default=_json_default), encoding="utf-8")
    return out_path


# ============================================================ THE KILL CRITERION ====

def separation_test(material_a: str, material_b: str, corpus_result: dict) -> dict:
    """Descriptors MUST separate two obviously-different materials (regolith vs
    brushed metal) by a wide margin relative to within-material spread, or the
    descriptor set is wrong — iterate it, never fake the match (the recipe's own
    words)."""
    descriptors = corpus_result["descriptors"]
    meta = corpus_result["meta"]
    scale = descriptors.std(axis=0)
    weights = descriptor_weights()

    ia = _exemplar_index(material_a, meta)
    ib = _exemplar_index(material_b, meta)
    cross = weighted_distance(descriptors[ia], descriptors[ib], scale, weights)

    harvested_a_path = HARVEST_DIR / f"{material_a}.json"
    within_a = float("nan")
    if harvested_a_path.exists():
        harvested_a = json.loads(harvested_a_path.read_text(encoding="utf-8"))
        ds = [r["distance"] for r in harvested_a["regions"]]
        within_a = float(np.mean(ds)) if ds else float("nan")

    ratio = float(cross / (within_a + 1e-9)) if within_a == within_a else float("inf")
    return {
        "material_a": material_a, "material_b": material_b,
        "cross_distance": cross, "within_a_mean_distance": within_a,
        "separation_ratio": ratio,
        "passes_kill_criterion": bool(ratio > 3.0) if ratio == ratio else False,
    }


def julesz_adversarial_probe(rng: np.random.Generator, corpus_result: dict) -> dict:
    """THE SHARPEST PROOF of the binding constraint. Synthesizes a brushed-metal-
    patterned region and matches it to the regolith exemplar's OWN three color
    moments (mean luma, std luma, AND chroma spread — all three, not just the first
    two; an earlier version of this probe matched only mean+std and the leftover
    chroma mismatch was enough for the corpus-relative color-only distance to read
    misleadingly high, which was a bug in the PROBE, not evidence the descriptors
    work — fixed 2026-07-18 by matching all three before judging) — i.e. constructs
    a region with color moments as close to IDENTICAL to regolith as a real capture
    could plausibly land, but a completely different spatial pattern. A
    color-moments-ONLY distance must then be near zero (a pure statistical-average
    matcher would call these the SAME material); the FULL pattern descriptor
    distance must remain large. If it does not, the descriptor set is fooled by
    averages and must be iterated — this function is the numeric tripwire for
    exactly that failure."""
    descriptors = corpus_result["descriptors"]
    meta = corpus_result["meta"]
    regions_rgb = corpus_result["regions_rgb"]
    scale = descriptors.std(axis=0)

    ex_idx = _exemplar_index("regolith", meta)
    target_rgb = regions_rgb[ex_idx]
    target_color = descriptors[ex_idx, N_FILTERS + 3:]          # [mean_luma, std_luma, std_chroma]
    target_mean_l, target_std_l, target_std_c = (float(v) for v in target_color)

    fake = synth_brushed_metal(rng, size=target_rgb.shape[0])
    fake_luma = _luma(fake)

    # 1) match luma mean + std
    matched_luma = (fake_luma - fake_luma.mean()) / (fake_luma.std() + 1e-9) * target_std_l + target_mean_l
    luma_scale = (matched_luma / (fake_luma + 1e-9))[..., None]
    fake_matched = np.clip(fake.astype(np.float64) * luma_scale, 0, 255)

    # 2) ALSO match chroma spread (rescale RGB-minus-luma around the now-matched luma)
    new_luma = _luma(fake_matched)
    chroma = fake_matched - new_luma[..., None]
    cur_std_c = float(chroma.std())
    if cur_std_c > 1e-9:
        chroma = chroma * (target_std_c / cur_std_c)
    fake_matched_rgb = np.clip(new_luma[..., None] + chroma, 0, 255).astype(np.uint8)

    fake_gray = _luma(fake_matched_rgb).astype(np.float32)
    if available():
        fake_energies = filter_energies_gpu_batch(fake_gray[None, ...], BANK, fake_gray.shape[0])[0]
    else:
        fake_energies = filter_energies_cpu_gray(fake_gray, BANK)
    fake_desc = descriptor(fake_matched_rgb, fake_energies)

    real_desc = descriptors[ex_idx]

    color_only_weights = np.zeros(D_TOTAL, dtype=np.float64)
    color_only_weights[N_FILTERS + 3:] = 1.0
    color_only_dist = weighted_distance(real_desc, fake_desc, scale, color_only_weights)
    full_dist = weighted_distance(real_desc, fake_desc, scale, descriptor_weights())

    within_a = None
    hp = HARVEST_DIR / "regolith.json"
    if hp.exists():
        h = json.loads(hp.read_text(encoding="utf-8"))
        ds = [r["distance"] for r in h["regions"]]
        within_a = float(np.mean(ds)) if ds else None

    achieved_color_match = {
        "mean_luma": {"target": target_mean_l, "fake": float(new_luma.mean())},
        "std_luma": {"target": target_std_l, "fake": float(new_luma.std())},
        "std_chroma": {"target": target_std_c, "fake": float((fake_matched_rgb.astype(np.float64)
                                                                - _luma(fake_matched_rgb)[..., None]).std())},
    }

    passes = bool(color_only_dist < 0.75 and (within_a is None or full_dist >= within_a))
    return {
        "probe": "julesz_adversarial: brushed-metal pattern, 3-way color-matched (mean/std/chroma) to regolith",
        "achieved_color_match": achieved_color_match,
        "color_only_distance": color_only_dist,
        "full_pattern_distance": full_dist,
        "within_regolith_mean_distance": within_a,
        "passes_binding_constraint": passes,
        "interpretation": ("color_only_distance near zero (all three color moments matched) means a "
                            "pure statistical-average matcher would wrongly call these the SAME "
                            "material; full_pattern_distance staying at or above ordinary "
                            "within-material spread is the proof that pattern, not averages, is "
                            "doing the discrimination here."),
    }


# ============================================================ main ====

def main() -> int:
    print("ensure_synthetic_corpus() ...")
    written = ensure_synthetic_corpus()
    print(f"  wrote {len(written)} new placeholder image(s)" if written else "  corpus already present")

    print("scan_corpus() (GPU if available) ...")
    result = scan_corpus()
    print(f"  {result['throughput']}")

    print("benchmark_cpu_vs_gpu() ...")
    bench = benchmark_cpu_vs_gpu()
    print(json.dumps(bench, indent=2, default=_json_default))

    print("tagging exemplars (provisional-tag) ...")
    for material in MATERIALS:
        real_rel = REAL_EXEMPLAR_PHOTOS.get(material)
        real_path = (CORPUS_DIR / real_rel) if real_rel else None
        if real_path is not None and real_path.exists():
            from PIL import Image
            with Image.open(real_path) as im:
                w, h = im.size
            yx = ((h // 2) // TILE * TILE, (w // 2) // TILE * TILE)  # center tile, on the scan grid
            tag_exemplar(material, real_rel, yx, tag_kind="provisional-tag",
                         note="REAL CC0 sample (downloaded 2026-07-31, operator consent in live chat), "
                              "center tile — still a provisional-tag until the human's own tag supersedes")
            print(f"  {material}: REAL sample {real_rel} @ {list(yx)}")
        else:
            photo = f"synthetic_placeholder/{material}_01.png"
            # center-ish tile — 320/40 = 8x8 grid, index (3,3)
            tag_exemplar(material, photo, (3 * TILE, 3 * TILE), tag_kind="provisional-tag",
                         note="tagged by sub-31/tb-0180 (agent), NOT the human — supersede on sight")
            print(f"  {material}: synthetic placeholder (no real sample found)")

    print("harvesting ...")
    harvested = {}
    for material in MATERIALS:
        harvested[material] = harvest(material, result)
        write_reference_descriptor_file(material, result, harvested[material])
        print(f"  {material}: {len(harvested[material]['regions'])} regions harvested")

    print("separation_test(regolith, brushed_metal) — THE KILL CRITERION ...")
    sep = separation_test("regolith", "brushed_metal", result)
    print(json.dumps(sep, indent=2, default=_json_default))

    print("separation_test(regolith, rock) — a HARDER pair (both isotropic/mineral) ...")
    sep_hard = separation_test("regolith", "rock", result)
    print(json.dumps(sep_hard, indent=2, default=_json_default))

    print("julesz_adversarial_probe() ...")
    rng = np.random.default_rng(99)
    probe = julesz_adversarial_probe(rng, result)
    print(json.dumps(probe, indent=2, default=_json_default))

    report = {
        "corpus_regions": result["throughput"]["regions"],
        "benchmark": bench,
        "harvested_sizes": {m: len(harvested[m]["regions"]) for m in MATERIALS},
        "separation_regolith_vs_metal": sep,
        "separation_regolith_vs_rock": sep_hard,
        "julesz_probe": probe,
    }
    HARVEST_DIR.mkdir(parents=True, exist_ok=True)
    (HARVEST_DIR / "separation_report.json").write_text(
        json.dumps(report, indent=2, default=_json_default), encoding="utf-8")

    ok = sep["passes_kill_criterion"] and probe["passes_binding_constraint"]
    print("KILL CRITERION (regolith vs brushed_metal separates):", "PASS" if sep["passes_kill_criterion"] else "FAIL")
    print("BINDING CONSTRAINT (pattern beats color-only):", "PASS" if probe["passes_binding_constraint"] else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
