"""Synthetic architecture-table TIFF generator for the Vanhoof prestage lane.

Renders the realistic degradation class of the real target (PMC supplementary
tables-in-images): wide tables, muscles as rows, specimen x quantity columns
plus a mean±sd column -- the layout class of Vanhoof Part II S1/S2.  Varied
system fonts, small rotations, salt-pepper noise, blur, contrast loss,
optional grid rules.  All values are DERIVED from the closure laws the
admission adapter enforces (mass/FL seeded; PCSA := m/(rho*FL); volume :=
m/rho; MTU := FL + tendon_ext + tendon_int) -- no cell value is a free
parameter.  Deterministic under seed.
"""
import json
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

RHO_KG_M3 = 1060.0
FONT_PX = 48   # the table text size class (the GlyphBank renders at this size);
               # matches the real 600-dpi supplementary-table class (~40-60 px text)

# Lining-figure fonts only: the target class (PMC typeset supplementary
# tables) uses lining figures; old-style-figure fonts (e.g. Georgia) are
# outside the class and excluded (a real table typeset in such a font
# degrades to refusals, never to misreads -- the safe failure mode).
FONT_CANDIDATES = [
    'times.ttf', 'arial.ttf', 'cambria.ttc', 'calibri.ttf',
    'tahoma.ttf', 'verdana.ttf', 'segoeui.ttf', 'cour.ttf', 'consola.ttf',
]
FONTS_DIR = Path('C:/Windows/Fonts')

MUSCLE_NAMES = [
    'brachioradialis', 'ext carpi radialis longus', 'ext carpi radialis brevis',
    'ext carpi ulnaris', 'ext digitorum communis', 'ext digiti minimi',
    'ext indicis', 'ext pollicis brevis', 'ext pollicis longus',
    'abductor pollicis longus', 'flex carpi radialis', 'flex carpi ulnaris',
    'palmaris longus', 'flex digitorum superficialis', 'flex digitorum profundus',
    'flex pollicis longus', 'pronator teres', 'pronator quadratus',
    'supinator', 'anconeus', 'abductor digiti minimi',
    'opponens digiti minimi', 'flex digiti minimi brevis', 'opponens pollicis',
    'abductor pollicis brevis', 'flex pollicis brevis', 'adductor pollicis',
    'interosseus dorsalis 1', 'interosseus dorsalis 2', 'interosseus volaris 1',
    'lumbricalis 1', 'lumbricalis 2', 'lumbricalis 3', 'lumbricalis 4',
    'ext digitorum lateralis', 'flex digitorum radialis', 'pronator radii teres',
    'flexor brevis profundus 2', 'contrahentes 1', 'contrahentes 4',
]

SPECIMENS = ['Mm1', 'Mm2', 'Mm3', 'Mm4', 'Mm5', 'Mm6', 'Mm7']

# (field, header label, decimal places, plausible magnitude band)
FIELDS = [
    ('mass_g', 'mass (g)', 2, (1.0, 40.0)),
    ('volume_cm3', 'volume (cm3)', 2, (1.0, 38.0)),
    ('fl_mm', 'FL (mm)', 1, (5.0, 60.0)),
    ('mtu_mm', 'MTU (mm)', 1, (20.0, 140.0)),
    ('tendon_ext_mm', 'tendon ext (mm)', 1, (1.0, 60.0)),
    ('tendon_int_mm', 'tendon int (mm)', 1, (1.0, 40.0)),
    ('pcsa_mm2', 'PCSA (mm2)', 2, (0.2, 12.0)),
]
FIELD_NAMES = [f[0] for f in FIELDS]
N_NUMERIC = len(SPECIMENS) * len(FIELDS) + 1     # + the mean±sd column


def available_fonts():
    out = []
    for name in FONT_CANDIDATES:
        if (FONTS_DIR / name).is_file():
            out.append(name)
    return out[:4]


def build_rows(seed, n_rows=30):
    """Ground-truth rows whose values CLOSE under the admission laws."""
    rng = random.Random(seed * 1000 + 7)
    names = MUSCLE_NAMES[:]
    rng.shuffle(names)
    rows = []
    for i in range(n_rows):
        row = {'muscle': names[i % len(names)]}
        masses = []
        for spec in SPECIMENS:
            # DERIVED VALUES: the closure identities hold by construction at
            # the printed precision.  Sample FL and PCSA so that mass lands
            # in band, then define mass BY the PCSA law: every row closes
            # within the 2% law band AFTER rounding (the printed values are
            # the table's own data, as in the real S1/S2).
            fl = round(rng.uniform(5.0, 60.0), 1)
            # PCSA in TRUE mm2: PCSA_cm2 = mass_g / (1.06 g/cm3 * FL_cm)
            # => mass_g = PCSA_mm2 * FL_mm * 0.00106.  Sample FL and PCSA so
            # mass lands in (1, 40) g, then define mass BY the PCSA law.
            pcsa_lo = max(10.0, 1.0 / (0.00106 * fl))
            pcsa_hi = min(1200.0, 40.0 / (0.00106 * fl))
            pcsa = round(rng.uniform(pcsa_lo, pcsa_hi), 2)
            mass = round(pcsa * 0.00106 * fl, 2)
            volume = round(mass / (RHO_KG_M3 / 1000.0), 2)     # g / (g/cm3)
            tendon_ext = round(rng.uniform(1.0, 60.0), 1)
            tendon_int = round(rng.uniform(1.0, 40.0), 1)
            mtu = round(fl + tendon_ext + tendon_int, 1)       # closes exactly
            row[spec] = dict(mass_g=f'{mass:.2f}', volume_cm3=f'{volume:.2f}',
                             fl_mm=f'{fl:.1f}', mtu_mm=f'{mtu:.1f}',
                             tendon_ext_mm=f'{tendon_ext:.1f}',
                             tendon_int_mm=f'{tendon_int:.1f}',
                             pcsa_mm2=f'{pcsa:.2f}')
            masses.append(mass)
        mean_m = sum(masses) / len(masses)
        sd_m = (sum((m - mean_m) ** 2 for m in masses) / (len(masses) - 1)) ** 0.5
        row['mean_sd'] = f'{mean_m:.2f}±{sd_m:.2f}'
        rows.append(row)
    return rows


def corrupt_cell(rows, row_index, specimen, field, factor):
    """Ground-truth copy with ONE numeric cell inflated: the image will show
    the corrupted value perfectly legibly -- the row LAWS must catch it (the
    Guimaraes corrupted-row-quarantines-exactly-itself falsifier)."""
    import copy
    out = copy.deepcopy(rows)
    cell = out[row_index][specimen]
    decimals = 2 if field in ('mass_g', 'volume_cm3', 'pcsa_mm2') else 1
    cell[field] = f'{float(cell[field]) * factor:.{decimals}f}'
    return out


def _cell_text(row, col):
    if col == 0:
        return row['muscle']
    if col == len(SPECIMENS) * len(FIELDS) + 1:
        return row['mean_sd']
    idx = col - 1
    spec = SPECIMENS[idx // len(FIELDS)]
    field = FIELD_NAMES[idx % len(FIELDS)]
    return row[spec][field]


def headers():
    out = ['muscle']
    for spec in SPECIMENS:
        for _, label, _, _ in FIELDS:
            out.append(f'{spec} {label}')
    out.append('mass mean±sd')
    return out


def render_table(rows, font_name, rotation_deg, noise_density, blur_sigma,
                 contrast, grid, seed, supersample=2):
    """Render one table to a grayscale PIL image (deterministic)."""
    font_px = FONT_PX * supersample
    font = ImageFont.truetype(str(FONTS_DIR / font_name), font_px)
    head_font = ImageFont.truetype(str(FONTS_DIR / font_name), font_px)

    probe = Image.new('L', (8, 8))
    probe_draw = ImageDraw.Draw(probe)

    def text_w(s, fnt):
        b = probe_draw.textbbox((0, 0), s, font=fnt)
        return b[2] - b[0]

    cols = headers()
    col_w = []
    for c in range(len(cols)):
        widest = max([text_w(cols[c], head_font)]
                     + [text_w(_cell_text(r, c), font) for r in rows])
        col_w.append(widest + 24 * supersample)
    row_h = int(72 * supersample)
    margin = 20 * supersample
    W = int(margin * 2 + sum(col_w))
    H = int(margin * 2 + row_h * (len(rows) + 1))

    img = Image.new('L', (W, H), 255)
    draw = ImageDraw.Draw(img)
    xs = [margin + sum(col_w[:c]) for c in range(len(col_w) + 1)]
    ys = [margin + row_h * r for r in range(len(rows) + 2)]

    if grid:
        for x in xs:
            draw.line([(x, ys[0]), (x, ys[-1])], fill=0, width=supersample)
        for y in ys:
            draw.line([(xs[0], y), (xs[-1], y)], fill=0, width=supersample)

    for c, label in enumerate(cols):
        draw.text((xs[c] + 8 * supersample, ys[0] + 6 * supersample),
                  label, font=head_font, fill=0)
    for r, row in enumerate(rows):
        y = ys[r + 1] + 6 * supersample
        for c in range(len(cols)):
            draw.text((xs[c] + 8 * supersample, y), _cell_text(row, c),
                      font=font, fill=0)

    arr = np.asarray(img, dtype=np.float32)
    if contrast < 1.0:
        arr = 255.0 - (255.0 - arr) * contrast
    out = Image.fromarray(arr.astype(np.uint8))
    if blur_sigma > 0:
        from PIL import ImageFilter
        out = out.filter(ImageFilter.GaussianBlur(blur_sigma))
    if rotation_deg:
        out = out.rotate(rotation_deg, expand=True, resample=Image.BICUBIC,
                         fillcolor=255)
    if noise_density > 0:
        a = np.asarray(out, dtype=np.uint8).copy()
        mask = np.random.RandomState(seed * 1000 + 29).random_sample(a.shape)
        a[mask < noise_density / 2] = 0
        a[(mask > 1 - noise_density / 2) & (a < 128)] = 255
        out = Image.fromarray(a)

    # the scan/render class: rotate+noise happen at high resolution, then the
    # table is downsampled to its delivery size (the 600-dpi TIFF class)
    if supersample > 1:
        out = out.resize((max(1, out.width // supersample),
                          max(1, out.height // supersample)), Image.LANCZOS)
    return out


def save_tiff(img, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format='TIFF', compression='tiff_lzw', dpi=(600, 600))
    return str(path)


def emit_ground_truth(rows, path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rows, indent=1), encoding='utf-8')
    return str(p)


# ---------------------------------------------------- crafted ambiguity plates
# Each plate is a 6-row single-column numeric mini-table: rows 0,2,3,4,5 are
# context ('24.5' class values: they set the median glyph metrics and the
# decimal-register column mode), row 1 carries the crafted ambiguity.  The
# extractor must refuse row 1 BY NAME -- never guess.  Glyph geometry is
# measured from the rasterizer, never guessed.

_PLATE_CONTEXT = ['24.5', '31.2', '28.7', '27.9', '22.3']


def _draw_string(draw, xy, s, font):
    draw.text(xy, s, font=font, fill=0)
    x0, y0, x1, y1 = draw.textbbox(xy, s, font=font)
    return (x0, y0, x1, y1)


def render_plate(kind, font_name, out_path):
    """Render one crafted-ambiguity plate; returns (path, kind)."""
    font = ImageFont.truetype(str(FONTS_DIR / font_name), FONT_PX)
    texts = _PLATE_CONTEXT[:]
    W, H = 340, 56 * 6 + 20
    img = Image.new('L', (W, H), 255)
    d = ImageDraw.Draw(img)
    row_y = []
    for i, t in enumerate(texts):
        row_y.append(20 + 56 * i)
        if i != 1:
            _draw_string(d, (16, row_y[-1]), t, font)

    if kind == 'glyph_merge':
        # two digits drawn with interleaved strokes (second starts inside the
        # first) so the component merges with no clean internal valley
        b1 = _draw_string(d, (16, row_y[1]), '3', font)
        _draw_string(d, (16 + (b1[2] - b1[0]) - 8, row_y[1]), '8', font)
    elif kind == 'decimal_ambiguous':
        # '31.2' drawn as three separate strings so the dot's box is KNOWN,
        # then the dot is erased: only the column register law can tell 31.2
        # from 312 (a 10x-class value error -- refusal is the only legal read)
        b1 = _draw_string(d, (16, row_y[1]), '24', font)
        bx = _draw_string(d, (b1[2] + 2, row_y[1]), '.', font)
        _draw_string(d, (bx[2] + 5, row_y[1]), '9', font)
        d.rectangle((bx[0] - 1, bx[1] - 1, bx[2] + 1, bx[3] + 1), fill=255)
    elif kind == 'ambiguous_glyph':
        # a plain '1': at this scale its NCC ties with I/l (top1-top2 < 0.03)
        # -- pixel-undecidable, so only the margin rule may refuse it, never
        # guess.  (Measured: 0.865 vs 0.845 on the bank.)
        _draw_string(d, (16, row_y[1]), '1', font)
    elif kind == 'low_contrast':
        _draw_string(d, (16, row_y[1]), '31.2', font)
        row = img.crop((0, row_y[1] - 4, W, row_y[1] + 52))
        row = Image.fromarray(
            (255.0 - (255.0 - np.asarray(row, dtype=np.float32)) * 0.12)
            .astype(np.uint8))
        img.paste(row, (0, row_y[1] - 4))
    elif kind == 'grid_collision':
        # strike-through across the CELL's text width only (not the full
        # image, or the row profiler would treat it as a band separator)
        b = _draw_string(d, (16, row_y[1]), '31.2', font)
        d.line((b[0] - 4, (b[1] + b[3]) // 2, b[2] + 4, (b[1] + b[3]) // 2),
               fill=0, width=2)
    elif kind == 'cell_clipped':
        # digits run past the right image edge: partially outside the canvas
        _draw_string(d, (W - 58, row_y[1]), '8888', font)
    else:
        raise ValueError(kind)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, format='TIFF', compression='tiff_lzw', dpi=(600, 600))
    return str(out), kind
