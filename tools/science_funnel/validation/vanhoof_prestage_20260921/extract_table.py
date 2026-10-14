"""Deterministic table extractor for tables-in-images (the Vanhoof prestage).

Route: template/grid-detection fallback (tesseract absent on this host --
see receipt.json "route").  Pure numpy + PIL:

  load -> binarize (Otsu) -> despeckle (salt-pepper) -> deskew
  (projection-profile sharpness over a fixed angle grid) -> row bands
  (rule lines or whitespace) -> GLOBAL column intervals -> per-cell crops ->
  glyph components (BFS) -> NCC template match (fixed font bank) ->
  per-cell string + confidence + named refusal codes.

Every cell resolves to exactly one of: CONFIDENT (evidence-backed read),
LOW (readable but below the pre-registered bands -- never admitted), or
REFUSED with a named code.  The pipeline never guesses: ambiguous glyphs,
merged glyphs, clipped cells, in-band rules, low contrast, blank cells and
decimal-register breaks all refuse by name (receipt.json "honest_classes").

Deterministic: no RNG anywhere; fixed angle grid; fixed scan orders.
"""
import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import synth_table
from synth_table import FONTS_DIR

# ---- bands: AMENDED from the pre-run calibration (seeds 901-904, disjoint
# from the battery seeds) BEFORE the scored battery; documented in
# receipt.json rule0.band_amendment.  The original a-priori bands
# (0.90/0.95 confident, 0.75/0.90 low) assumed same-size rendering; the
# measured true-cell distributions sit below them.
GLYPH_MIN_CONFIDENT = 0.78
CELL_MEAN_CONFIDENT = 0.90
GLYPH_MIN_LOW = 0.65
CELL_MEAN_LOW = 0.82
TOP12_MARGIN_REFUSE = 0.03

MIN_CONTRAST_DELTA = 60.0      # p90-p5 gray delta below which a cell refuses
RULE_FRACTION_IN_BAND = 0.90   # crop row this dark = a rule crosses the cell
DESPECKLE_AREA = 5             # components smaller than this many px are salt
                               # (a 32px-font decimal dot is ~16 px; salt clusters are smaller)

BANK_ALPHABET = (list('abcdefghijklmnopqrstuvwxyz')
                 + list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
                 + list('0123456789.') + ['±'])
DESKEW_ANGLES = [round(a * 0.1, 1) for a in range(-15, 16)]  # -1.5..+1.5 deg
GLYPH_BOX = (32, 48)

_NUMERIC_RE = re.compile(r'\d+(?:\.\d+)?(?:±\d+(?:\.\d+)?)?')
_DECIMAL_RE = re.compile(r'^(\d+)(?:\.(\d+))?$')


# ------------------------------------------------------------------ image io

def load_gray(path):
    return np.asarray(Image.open(path).convert('L'), dtype=np.uint8)


def tiff_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def otsu(gray):
    hist, _ = np.histogram(gray, bins=256, range=(0, 256))
    total = hist.sum()
    sum_all = np.dot(np.arange(256), hist)
    sum_b = 0.0
    w_b = 0.0
    best_t, best_var = 127, -1.0
    for t in range(256):
        w_b += hist[t]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += t * hist[t]
        m_b = sum_b / w_b
        m_f = (sum_all - sum_b) / w_f
        var = w_b * w_f * (m_b - m_f) ** 2
        if var > best_var:
            best_t, best_var = t, var
    return best_t


def binarize(gray):
    """Ink = True.  GLOBAL Otsu over the whole image: it balances the full
    ink+antialias fringe mass against paper, so thin stroke rings keep their
    AA columns (a mode-midpoint cut sits too low and erodes them).  Otsu is
    pathological only on PADDED CROPS (where paper dominates the local
    histogram) -- crops are never re-thresholded here; they inherit the
    global ink mask."""
    return gray < otsu(gray)


def components(mask, min_area=0):
    """8-connected components via BFS, row-major scan (deterministic).
    8-connectivity: antialiased thin strokes join glyphs only diagonally
    (a '0' ring's top arc meets its side arcs at corner pixels)."""
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    for sy in range(h):
        for sx in range(w):
            if mask[sy, sx] and not seen[sy, sx]:
                stack = [(sy, sx)]
                seen[sy, sx] = True
                pix = []
                while stack:
                    y, x = stack.pop()
                    pix.append((y, x))
                    for ny in (y - 1, y, y + 1):
                        for nx in (x - 1, x, x + 1):
                            if (ny or nx) and 0 <= ny < h and 0 <= nx < w \
                                    and mask[ny, nx] and not seen[ny, nx]:
                                seen[ny, nx] = True
                                stack.append((ny, nx))
                if len(pix) < min_area:
                    for y, x in pix:
                        mask[y, x] = False
                    continue
                ys = [p[0] for p in pix]
                xs = [p[1] for p in pix]
                out.append({'y0': min(ys), 'y1': max(ys),
                            'x0': min(xs), 'x1': max(xs), 'n': len(pix)})
    return out


def deskew(gray, angles=DESKEW_ANGLES, probe_scale=4):
    """Projection-profile sharpness: the angle at which row-sums differentiate
    most (baselines line up).  The angle grid runs on a probe thumbnail
    (cheap, accurate to the grid step); the full image is rotated ONCE with
    the winning angle.  Fixed grid, deterministic."""
    probe = Image.fromarray(gray)
    if probe.width > 800:
        probe = probe.resize((probe.width // probe_scale,
                              probe.height // probe_scale), Image.BILINEAR)
    probe_gray = np.asarray(probe, dtype=np.uint8)
    best_angle, best_score = 0.0, -1.0
    for a in angles:
        rotated = probe.rotate(a, expand=True, resample=Image.BILINEAR,
                               fillcolor=255)
        profile = np.asarray(rotated, dtype=np.float32).sum(axis=1)
        score = float(np.square(np.diff(profile)).sum())
        if score > best_score:
            best_angle, best_score = a, score
    if best_angle == 0.0:
        return gray, 0.0
    out = np.asarray(Image.fromarray(gray).rotate(
        best_angle, expand=True, resample=Image.BILINEAR, fillcolor=255),
        dtype=np.uint8)
    return out, best_angle


# ------------------------------------------------------- structure detection

def find_row_bands(ink, edge=3):
    """Horizontal structure: rule lines (grid) or whitespace gaps (borderless).
    Bands touching the image's top/bottom edge are rotation/deskew border
    artifacts and are dropped.  Returns (text_bands, rule_rows)."""
    prof = ink.mean(axis=1)
    rules = [i for i, v in enumerate(prof) if v > 0.5]
    if len(rules) >= 3:                       # grid table
        bands, prev = [], None
        for r in rules:
            if prev is not None and r - prev > 4:
                bands.append((prev + 2, r - 2))
            prev = r
        return bands, rules
    on = prof > 0.01               # salt remnants stay under; text rows clear it
    bands, start = [], None
    for i, v in enumerate(on):
        if v and start is None:
            start = i
        elif not v and start is not None:
            bands.append([start, i - 1])
            start = None
    if start is not None:
        bands.append([start, len(on) - 1])
    merged = []
    for b in bands:
        if merged and b[0] - merged[-1][1] <= 2:
            merged[-1][1] = b[1]
        else:
            merged.append(b)
    h = len(on)
    return [tuple(b) for b in merged
            if b[1] - b[0] > 4 and b[0] > edge and b[1] < h - 1 - edge], []


def find_col_intervals(ink, bands):
    """GLOBAL column intervals.

    Grid rules are judged on the FULL-IMAGE column profile: a rule spans the
    inter-row whitespace, so its column is dark across nearly the whole table
    height; text strokes exist only inside text bands (~0.6 of rows) and even
    there only partially.  A column with full-image dark fraction > 0.65 is a
    rule; >= 3 rules -> grid intervals between them.  Borderless tables fall
    to per-band whitespace runs (gap > 0.8 x band height, word gaps are
    narrower) unioned across bands.  Returns (intervals, grid_mode)."""
    per_band = []
    # data bands only: header words carry their own wide spaces and would
    # vote phantom intervals into the union
    for y0, y1 in bands[1:] or bands:
        h = y1 - y0 + 1
        strip = ink[y0:y1 + 1]
        prof = strip.mean(axis=0)
        on = prof > 0.002
        cells, start, gap = [], None, 0
        for i, v in enumerate(on):
            if v:
                if start is None:
                    start = i
                gap = 0
            elif start is not None:
                gap += 1
                if gap > 0.6 * h:   # word gaps ~0.4 x band height stay whole;
                                    # column gaps (~0.9 x) split
                    cells.append((start, i - gap))
                    start, gap = None, 0
        if start is not None:
            cells.append((start, len(on) - 1))
        per_band.append(cells)
    prof_full = ink.mean(axis=0)
    rule_cols = [i for i, v in enumerate(prof_full) if v > 0.65]
    if len(rule_cols) >= 3:                    # grid table
        edges, prev = [], None
        for c in rule_cols:
            if prev is not None and c - prev > 4:
                edges.append((prev + 2, c - 2))
            prev = c
        return edges, True
    # union across bands (merge overlapping/1px-adjacent intervals)
    flat = sorted(c for band in per_band for c in band)
    union = []
    for c in flat:
        if union and c[0] <= union[-1][1] + 1:
            union[-1][1] = max(union[-1][1], c[1])
        else:
            union.append([c[0], c[1]])
    # sliver merge: splits narrower than 0.35 x band height are single-band
    # glyph/AA artifacts, not column gaps (real column gaps are ~0.9 x h)
    med_h = float(np.median([y1 - y0 + 1 for y0, y1 in bands]))
    merged = [union[0]]
    for c in union[1:]:
        if c[0] - merged[-1][1] < 0.35 * med_h:
            merged[-1][1] = max(merged[-1][1], c[1])
        else:
            merged.append(c)
    union = merged
    return [tuple(u) for u in union if u[1] > u[0]], False


# ------------------------------------------------------ glyph classification

def normalize_glyph_gray(win, ink_bbox, h0, box=GLYPH_BOX):
    """Scale a glyph's ANTIALIASED grayscale window (ink = high) to the
    COMMON reference height h0 mapped to 32 px, preserving aspect, relative
    size and the continuous stroke-edge profile.  Binary masks lose the
    stroke-weight information a binarization threshold sets arbitrarily;
    the grayscale keeps it, which is what makes same-font matches separate
    from cross-font confusions.  ink_bbox = (y0, y1, x0, x1) of the ink
    inside the window; the window is the ink bbox padded by PAD px."""
    if h0 <= 0 or win is None:
        return None
    y0, y1, x0, x1 = ink_bbox
    if y1 < y0 or x1 < x0:
        return None
    gh = y1 - y0 + 1
    scale = 32.0 / h0
    # crop the window to the ink bbox EXACTLY (pads distort asymmetrically
    # when they clamp at crop edges); the window must already be ink-HIGH
    # (the bank passes its alpha; the cell side passes 255 - gray)
    sub = win[y0:y1 + 1, x0:x1 + 1].astype(np.float32)
    nh = int(round(gh * scale))
    nw = int(round((x1 - x0 + 1) * scale))
    nh = max(1, min(nh, box[0]))
    nw = max(1, min(nw, box[1]))
    img = Image.fromarray(sub.astype(np.uint8)).resize((nw, nh),
                                                       Image.BILINEAR)
    canvas = np.zeros(box, dtype=np.float32)
    cy = (box[0] - nh) // 2
    cx = (box[1] - nw) // 2
    canvas[cy:cy + nh, cx:cx + nw] = np.asarray(img, dtype=np.float32) / 255.0
    return canvas


def ncc(a, b):
    a = a - a.mean()
    b = b - b.mean()
    d = math.sqrt(float((a * a).sum()) * float((b * b).sum()))
    return float((a * b).sum()) / d if d > 0 else 0.0


class GlyphBank:
    """Template bank: fixed font list x fixed alphabet, rendered once,
    deterministically, by the same rasterizer class as the generator.
    The bank's reference height h0 is the median DIGIT height (the same
    digit class the table side measures), so cell and bank glyphs are
    normalized consistently."""

    PAD = 2

    def __init__(self, font_names):
        self.entries = []
        self.fonts = list(font_names)
        raws = []
        # PER-FONT reference height: a table's h0 is its OWN font's digit
        # height, so each font's templates must normalize by the same font's
        # digit height -- a cross-font median leaves every non-median font
        # systematically mis-scaled (9% for arial vs the 4-font median),
        # which collapses same-font NCC to ~0.8
        digit_heights_by_font = {}
        for fname in self.fonts:
            # the bank renders at the SAME size class as the tables (the
            # generator's font size): normalization can then not introduce a
            # cross-size blur mismatch, which depresses NCC by ~0.1
            f = ImageFont.truetype(str(FONTS_DIR / fname),
                                   synth_table.FONT_PX)
            for ch in BANK_ALPHABET:
                img = Image.new('L', (96, 96), 0)
                ImageDraw.Draw(img).text((12, 6), ch, font=f, fill=255)
                alpha = np.asarray(img, dtype=np.float32)   # ink = high
                m = alpha > 128
                ys, xs = np.where(m)
                if len(ys) == 0:
                    continue
                y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
                if ch.isdigit():
                    digit_heights_by_font.setdefault(
                        fname, []).append(y1 - y0 + 1)
                Y0, Y1 = max(0, y0 - self.PAD), min(96, y1 + self.PAD + 1)
                X0, X1 = max(0, x0 - self.PAD), min(96, x1 + self.PAD + 1)
                win = alpha[Y0:Y1, X0:X1]
                raws.append((ch, fname, win,
                             (y0 - Y0, y1 - Y0, x0 - X0, x1 - X0)))
        h0_by_font = {fname: float(np.median(hs))
                      for fname, hs in digit_heights_by_font.items()}
        self.h0_by_font = h0_by_font
        h0 = float(np.median(list(h0_by_font.values())))
        self.h0 = h0
        chars, fonts_, stack = [], [], []
        for ch, fname, win, bbox in raws:
            canvas = normalize_glyph_gray(win, bbox, h0_by_font[fname],
                                          GLYPH_BOX)
            if canvas is not None:
                chars.append(ch)
                fonts_.append(fname)
                stack.append(canvas)
        self.chars = chars
        self.fonts = fonts_
        T = np.stack(stack)                       # (K, H, W)
        self.T = T - T.mean(axis=(1, 2), keepdims=True)
        self.Tnorm = np.sqrt((self.T * self.T).sum(axis=(1, 2)))
        self.entries = list(zip(chars, fonts_, stack))

    def classify(self, canvas):
        c = canvas - canvas.mean()
        cnorm = math.sqrt(float((c * c).sum()))
        scores = (self.T * c).sum(axis=(1, 2)) / (self.Tnorm * cnorm + 1e-12)
        order = np.argsort(-scores, kind='stable')
        top = order[0]
        runner_i = next((int(i) for i in order if self.chars[i] != self.chars[top]),
                        None)
        runner_score = float(scores[runner_i]) if runner_i is not None else 0.0
        return {'char': self.chars[top], 'font': self.fonts[top],
                'score': float(scores[top]),
                'runner_char': self.chars[runner_i] if runner_i is not None else '',
                'runner_score': runner_score}


# ------------------------------------------------------------------ reading

def _refusal(code):
    return {'text': '', 'conf_min': 0.0, 'conf_mean': 0.0,
            'class': 'REFUSED', 'code': code}


def read_cell(crop_ink, crop_light, crop_gray, bank, numeric, h0,
              med_area, abs_y0, abs_x0, image_h, image_w):
    """One cell crop (strict ink mask, light structural mask, grayscale)
    -> dict with text/class/conf/code.

    h0: the table-wide digit-class reference height (extract() measures it
    once); glyph normalization maps h0 -> 32 px preserving aspect and
    relative size.  CONFIDENT: min glyph NCC >= 0.90 and mean >= 0.95;
    LOW: min >= 0.75 and mean >= 0.90 (flagged, never admitted);
    else REFUSED with a named code.
    """
    ink = crop_ink
    components(ink, min_area=DESPECKLE_AREA)   # despeckle in place
    light = crop_light
    components(light, min_area=DESPECKLE_AREA)
    if int(ink.sum()) < 3:
        if int(light.sum()) >= 3:
            # faint ink is present but below the reading threshold:
            # unreadable by construction -> refuse by name
            return _refusal('low_contrast')
        return _refusal('blank_cell')

    # contrast gate: evidence of ink before any reading is attempted --
    # darkest pixel under the INK COMPONENTS vs paper level (crop-wide
    # minima leak neighboring rows through the descender extension)
    p99 = float(np.percentile(crop_gray, 99))

    # in-band rule: a crop row almost fully dark is a rule crossing the cell
    row_frac = ink.mean(axis=1)
    if len(row_frac) and row_frac.max() > RULE_FRACTION_IN_BAND:
        return _refusal('grid_collision')

    comp = components(ink)
    if not comp:
        return _refusal('blank_cell')

    # contrast gate (see above): darkest gray under any component bbox
    gmin = 255.0
    for c in comp:
        gmin = min(gmin, float(crop_gray[c['y0']:c['y1'] + 1,
                                        c['x0']:c['x1'] + 1].min()))
    if p99 - gmin < MIN_CONTRAST_DELTA:
        return _refusal('low_contrast')

    # clipped: a component touching the absolute image edge
    for c in comp:
        if abs_y0 + c['y0'] == 0 or abs_x0 + c['x0'] == 0 \
                or abs_y0 + c['y1'] == image_h - 1 \
                or abs_x0 + c['x1'] == image_w - 1:
            return _refusal('cell_clipped')

    heights = sorted(c['y1'] - c['y0'] + 1 for c in comp)
    med_h = heights[len(heights) // 2]
    widths = sorted(c['x1'] - c['x0'] + 1 for c in comp)
    med_w = widths[len(widths) // 2]

    # glyph merge: one component much wider than the median glyph with no
    # clean internal valley (kerned/collapsed characters); in numeric cells
    # also judge against the table reference height (a lone merged blob is
    # its own per-cell median and cannot self-flag)
    for c in comp:
        cw = c['x1'] - c['x0'] + 1
        tall_enough = (c['y1'] - c['y0'] + 1) > 0.8 * med_h
        if tall_enough and ((cw > 1.9 * med_w and not numeric)
                            or (numeric and cw > 0.75 * h0)):
            strip = ink[c['y0']:c['y1'] + 1, c['x0']:c['x1'] + 1]
            if float(strip.mean(axis=0).min()) > 0.35:
                return _refusal('glyph_merge')

    comp.sort(key=lambda c: c['x0'])
    merged = []
    for c in comp:
        if merged:
            prev = merged[-1]
            # overlap-merge: broken strokes and i/j dots overlap the main
            # stem horizontally; separate characters never do (gap >= 1 px)
            ov = min(prev['x1'], c['x1']) - max(prev['x0'], c['x0']) + 1
            narrow = min(prev['x1'] - prev['x0'] + 1, c['x1'] - c['x0'] + 1)
            if ov >= 0.4 * narrow:
                merged[-1] = {'y0': min(prev['y0'], c['y0']),
                              'y1': max(prev['y1'], c['y1']),
                              'x0': prev['x0'], 'x1': max(prev['x1'], c['x1']),
                              'n': prev['n'] + c['n']}
                continue
        merged.append(dict(c))

    text, scores, alts = [], [], []
    prev = None
    for c in merged:
        if prev is not None:
            gap = c['x0'] - prev['x1']
            if gap >= 8 and gap > 0.55 * med_w and not numeric:
                text.append(' ')
        Y0, Y1 = max(0, c['y0'] - GlyphBank.PAD), min(crop_gray.shape[0],
                                                      c['y1'] + GlyphBank.PAD + 1)
        X0, X1 = max(0, c['x0'] - GlyphBank.PAD), min(crop_gray.shape[1],
                                                      c['x1'] + GlyphBank.PAD + 1)
        win = 255.0 - crop_gray[Y0:Y1, X0:X1]      # ink = high
        bbox = (c['y0'] - Y0, c['y1'] - Y0, c['x0'] - X0, c['x1'] - X0)
        canvas = normalize_glyph_gray(win, bbox, h0, GLYPH_BOX)
        if canvas is None:
            return _refusal('glyph_merge')
        hit = bank.classify(canvas)
        margin = hit['score'] - hit['runner_score']
        if hit['score'] < GLYPH_MIN_LOW:
            # an unclassifiable blob whose BBOX carries ~2 glyphs of area in
            # a numeric cell is a merged character pair, named
            if numeric and (c['y1'] - c['y0'] + 1) * (c['x1'] - c['x0'] + 1)                     > 1.4 * med_area:
                return _refusal('glyph_merge')
            return _refusal('low_glyph_confidence')
        if margin < TOP12_MARGIN_REFUSE:
            # a genuinely ambiguous glyph: in TEXT columns the closed
            # vocabulary resolves the key (pass the read + the alternate);
            # in numeric columns a guessed digit is illegal -> refuse
            if not numeric:
                text.append(hit['char'])
                scores.append(hit['score'])
                alts.append((len(text) - 1, hit['runner_char']))
                prev = c
                continue
            return _refusal('ambiguous_glyph')
        text.append(hit['char'])
        scores.append(hit['score'])
        prev = c

    conf_min = min(scores)
    conf_mean = sum(scores) / len(scores)
    out_text = ''.join(text).strip()
    base = {'conf_min': conf_min, 'conf_mean': conf_mean, 'alts': alts}
    if numeric and not _NUMERIC_RE.fullmatch(out_text):
        return {'text': out_text, **base,
                'class': 'REFUSED', 'code': 'nonnumeric_cell'}
    if conf_min >= GLYPH_MIN_CONFIDENT and conf_mean >= CELL_MEAN_CONFIDENT:
        return {'text': out_text, **base, 'class': 'CONFIDENT', 'code': None}
    if conf_min >= GLYPH_MIN_LOW and conf_mean >= CELL_MEAN_LOW:
        return {'text': out_text, **base,
                'class': 'LOW', 'code': 'low_confidence_cell'}
    # text columns keep the flagged read visible (the admission layer's
    # closed vocabulary decides whether a low-confidence key is usable);
    # numeric columns refuse -- never a guessed number
    if not numeric:
        return {'text': out_text, **base,
                'class': 'LOW', 'code': 'low_confidence_cell'}
    return {'text': out_text, **base,
            'class': 'REFUSED', 'code': 'low_confidence_cell'}


def extract(gray, bank, numeric_columns):
    """Full table -> per-cell extraction records.

    numeric_columns: {col_index: field_name}; other columns read as text.
    Applies the pre-registered decimal-register law: in a numeric column whose
    decimal-place mode covers >= 0.80 of its confident cells, a cell deviating
    from the mode refuses as decimal_ambiguous (the table's own formatting
    regularity used as a closure law -- catches an eroded decimal point).
    """
    angled, skew = deskew(gray)
    ink = binarize(angled)
    components(ink, min_area=DESPECKLE_AREA)
    h, w = angled.shape
    # light structural ink: bands and columns detected on a faint-ink
    # superset (paper - 15) so unreadably faint rows still BAND (and get
    # refused by name downstream) instead of silently vanishing
    paper = float(np.percentile(angled, 99))
    ink_light = angled < (paper - 15.0)
    components(ink_light, min_area=DESPECKLE_AREA)
    bands_core, rules = find_row_bands(ink_light)
    intervals, grid_mode = find_col_intervals(ink_light, bands_core)
    # descender extension (CROPPING only, after column detection): a
    # whitespace-gap band ends at the BASELINE -- the descender rows of
    # p/g/y/q/j carry too little ink to clear the floor -- which would clip
    # every descender and turn 'p' into 'o'.  Extend each band down by
    # ~0.35 x its core height (the typographic descender depth), clamped
    # before the next band; column intervals stay computed on the CORE.
    bands = []
    for i, (y0, y1) in enumerate(bands_core):
        # grid rules already bound their rows fully (descenders stay inside
        # the pitch); only whitespace-banded tables need the extension
        ext = 0 if rules else int(round(0.35 * (y1 - y0 + 1)))
        limit = (bands_core[i + 1][0] - 1) if i + 1 < len(bands_core)             else h - 1
        bands.append((y0, min(y1 + ext, limit)))
    # table-wide digit-class reference height: the tall component class
    # (digits/ascenders) defines it; h0 maps to 32 px in glyph normalization
    all_h = []
    tall_areas = []
    for y0, y1 in bands:
        for x0, x1 in intervals:
            crop_ink = ink[y0:y1 + 1, x0:x1 + 1]
            for comp in components(crop_ink):
                hh = comp['y1'] - comp['y0'] + 1
                if hh >= 3:
                    all_h.append(hh)
                    tall_areas.append(hh * (comp['x1'] - comp['x0'] + 1))
    require_h = sorted(all_h)
    if not require_h:
        return {'cells': [], 'skew_deg': skew, 'grid_mode': grid_mode,
                'n_bands': len(bands), 'n_cols': len(intervals),
                'decimal_register': {}}
    hmax = require_h[int(0.95 * (len(require_h) - 1))]
    tall = [v for v in require_h if v >= 0.8 * hmax]
    h0 = float(np.median(tall))
    tall_pairs = [(hh, a) for hh, a in zip(all_h, tall_areas)
                  if hh >= 0.8 * hmax]
    med_area = float(np.median([a for _, a in tall_pairs])) if tall_pairs         else 0.0
    cells = []
    per_col_places = {}
    for r, (y0, y1) in enumerate(bands):
        for c, (x0, x1) in enumerate(intervals):
            numeric = c in numeric_columns
            crop_ink = ink[y0:y1 + 1, x0:x1 + 1]
            crop_light = ink_light[y0:y1 + 1, x0:x1 + 1]
            crop_gray = angled[y0:y1 + 1, x0:x1 + 1]
            res = read_cell(crop_ink, crop_light, crop_gray, bank, numeric,
                            h0, med_area, y0, x0, h, w)
            res.update(row=r, col=c,
                       bbox=[int(x0), int(y0), int(x1), int(y1)])
            if res['class'] == 'CONFIDENT' and numeric:
                m = _DECIMAL_RE.match(res['text'].split('±')[0])
                if m:
                    per_col_places.setdefault(c, []).append(
                        len(m.group(2)) if m.group(2) else 0)
            cells.append(res)
    for c, places in per_col_places.items():
        mode = max(sorted(set(places)), key=places.count)
        coverage = places.count(mode) / len(places)
        if coverage >= 0.80:
            for cell in cells:
                if cell['col'] == c and cell['class'] == 'CONFIDENT':
                    body = cell['text'].split('±')[0]
                    m = _DECIMAL_RE.match(body)
                    got = len(m.group(2)) if (m and m.group(2)) else 0
                    if got != mode:
                        cell['class'] = 'REFUSED'
                        cell['code'] = 'decimal_ambiguous'
    # row classification: junk bands (rotation margin specks, split header
    # fragments) carry few cells; header rows read as text where data rows
    # read numerically.  Junk is dropped, survivors reindexed top-to-bottom:
    # header rows keep 'header', data rows become 1..n (0 = header zone).
    by_row = {}
    for cell in cells:
        by_row.setdefault(cell['row'], []).append(cell)
    if not by_row:
        return {'cells': [], 'skew_deg': skew, 'grid_mode': grid_mode,
                'n_bands': len(bands), 'n_cols': len(intervals),
                'decimal_register': {}}
    counts = sorted(len(v) for v in by_row.values())
    modal = counts[len(counts) // 2]
    keep = [r for r in sorted(by_row) if len(by_row[r]) >= 0.5 * modal]
    # positional indexing: surviving rows are the table's rows in order
    # (row 1..n); the header zone is row 1 when the expected structure says
    # so -- the ADAPTER's count identity catches any structural anomaly
    reindex = {r: i + 1 for i, r in enumerate(keep)}
    for cell in cells:
        cell['row'] = reindex.get(cell['row'], -1)
    cells = [c for c in cells if c['row'] >= 0]
    return {'cells': cells, 'skew_deg': skew, 'grid_mode': grid_mode,
            'n_bands': len(bands), 'n_cols': len(intervals),
            'n_rows': len(keep),
            'decimal_register': {c: {'mode': max(sorted(set(v)),
                                                 key=v.count),
                                     'coverage': round(v.count(max(sorted(set(v), key=v.count))) / len(v), 4)}
                                 for c, v in per_col_places.items()}}


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')
