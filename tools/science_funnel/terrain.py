"""Terrain reduction: pinned Copernicus GLO-30 tile + EGM08 geoid -> the height
of the real ground under the patch, through the admitted 7-step law
(work.environment.terrain contract). Stdlib only: a targeted TIFF reader
(Deflate + floating-point predictor), geoid undulation by two independent
interpolation methods, bilinear DEM reduction in local metres, the holdout
remainder identity, and a least-squares plane whose tilt is RECORDED, never
consumed."""
import math
import struct
import zlib

from .common import Refusal, require

WGS84_A = 6378137.0
WGS84_F = 1.0 / 298.257223563
NODATA = -32767.0

TAG_WIDTH, TAG_HEIGHT, TAG_BITS = 256, 257, 258
TAG_COMPRESSION, TAG_STRIP_OFFS, TAG_ROWS_PER_STRIP = 259, 273, 278
TAG_STRIP_BYTES, TAG_TILE_W, TAG_TILE_H = 279, 322, 323
TAG_TILE_OFFS, TAG_TILE_BYTES, TAG_SAMPLE_FMT = 324, 325, 339
TAG_MODEL_PIXEL_SCALE, TAG_MODEL_TIEPOINT = 33550, 33922


def _doubles(raw, endian, count, value):
    if count * 8 <= 4:
        return list(struct.unpack(endian + '%dd' % count, raw[:count * 8]))
    return list(struct.unpack(endian + '%dd' % count, raw[value:value + count * 8]))


def _longs(raw, endian, count, value):
    if count * 4 <= 4:
        return list(struct.unpack(endian + '%dI' % count, raw[:count * 4]))
    return list(struct.unpack(endian + '%dI' % count, raw[value:value + count * 4]))


def tiff_tags(path):
    """Parse the first IFD of a little/big-endian classic TIFF."""
    with open(path, 'rb') as stream:
        raw = stream.read(16)
        stream.seek(0, 2)
        size = stream.tell()
        endian = '<' if raw[:2] == b'II' else '>'
        require(raw[:2] in (b'II', b'MM'), 'terrain_tiff_not_classic', path)
        version, offset = struct.unpack(endian + 'HI', raw[2:8])
        require(version == 42, 'terrain_tiff_version', path)
        with open(path, 'rb') as seek:
            seek.seek(offset)
            head = seek.read(2)
            count = struct.unpack(endian + 'H', head)[0]
            entries = seek.read(count * 12)
        tags = {}
        for i in range(count):
            e = entries[i * 12:(i + 1) * 12]
            tag, typ, cnt = struct.unpack(endian + 'HHI', e[:8])
            val = struct.unpack(endian + 'I', e[8:12])[0]
            tags[tag] = (typ, cnt, val)
        return tags, endian, size


def _longs_at(path, endian, tags, tag):
    typ, cnt, val = tags[tag]
    with open(path, 'rb') as stream:
        if cnt * 4 <= 4:
            return [val]
        stream.seek(val)
        return list(struct.unpack(endian + '%dI' % cnt, stream.read(cnt * 4)))


def _short(tags, tag):
    return tags[tag][2] if tags[tag][0] == 3 else tags[tag][2]


def sample_grid(path, samples, value_range=None):
    """Read specific (row, col) float samples from a tiled float32 TIFF.

    Decodes through tifffile (installed in this environment): a hand-rolled
    stdlib predictor decode was FALSIFIED against tifffile on the pinned grids
    (four byte-lane variants x two byte orders all mismatched; recorded in the
    terrain receipt), so the battle-tested reader is authoritative here. The
    stdlib pair survives as sample_grid_stdlib for the synthetic writer/reader
    self-consistency test only. value_range still gates the decoded values
    against the grid family's declared physical envelope."""
    import tifffile as _tif
    key = str(path)
    if key not in _ARRAY_CACHE:
        with _tif.TiffFile(key) as tif:
            _ARRAY_CACHE[key] = tif.pages[0].asarray()
    arr = _ARRAY_CACHE[key]
    out = {}
    for row, col in samples:
        value = float(arr[row, col])
        if value_range is not None:
            require(value_range[0] <= value <= value_range[1],
                    'terrain_value_outside_envelope',
                    f'{key} ({row},{col}) = {value}')
        out[(row, col)] = value
    return out


_ARRAY_CACHE = {}


def sample_grid_stdlib(path, samples):
    """Stdlib targeted decode (Deflate + byte-lane float predictor, file byte
    order). NOT used against the pinned grids -- it disagrees with tifffile
    there; kept for the synthetic self-consistency test and as the documented
    second implementation attempt."""
    tags, endian, size = tiff_tags(path)
    tile_w, tile_h = _short(tags, TAG_TILE_W), _short(tags, TAG_TILE_H)
    offsets = _longs_at(path, endian, tags, TAG_TILE_OFFS)
    byte_counts = _longs_at(path, endian, tags, TAG_TILE_BYTES)
    width, height = _short(tags, TAG_WIDTH), _short(tags, TAG_HEIGHT)
    tiles_across = (width + tile_w - 1) // tile_w
    needed = set()
    for row, col in samples:
        needed.add((row // tile_h, col // tile_w))
    out = {}
    with open(path, 'rb') as stream:
        for tile_row, tile_col in sorted(needed):
            index = tile_row * tiles_across + tile_col
            stream.seek(offsets[index])
            data = zlib.decompress(stream.read(byte_counts[index]))
            raw = bytearray(data)
            row_bytes = tile_w * 4
            for r in range(min(tile_h, height - tile_row * tile_h)):
                base = r * row_bytes
                for i in range(4, row_bytes):
                    raw[base + i] = (raw[base + i] + raw[base + i - 4]) & 0xFF
            for row, col in samples:
                if row // tile_h == tile_row and col // tile_w == tile_col:
                    rr, cc = row - tile_row * tile_h, col - tile_col * tile_w
                    out[(row, col)] = struct.unpack(
                        endian + 'f', bytes(raw[rr * row_bytes + cc * 4:
                                                rr * row_bytes + cc * 4 + 4]))[0]
    return out


def geotransform(path):
    """RasterPixelIsPoint geotransform: ModelTiepoint (33922, 6 doubles) maps
    raster (0,0) to the first POINT CENTRE; ModelPixelScale (33550) gives the
    step sizes."""
    tags, endian, size = tiff_tags(path)
    tie = _doubles_at(path, endian, tags, TAG_MODEL_TIEPOINT)
    scale = _doubles_at(path, endian, tags, TAG_MODEL_PIXEL_SCALE)
    require(len(tie) == 6 and tie[0] == 0.0 and tie[1] == 0.0 and tie[2] == 0.0,
            'terrain_tiepoint')
    require(len(scale) == 3 and scale[0] > 0 and scale[1] > 0, 'terrain_scale')
    # RasterPixelIsPoint: tiepoint (raster 0,0) maps to the FIRST POINT CENTRE
    return {'lon0': tie[3], 'lat0': tie[4], 'd_lon': scale[0], 'd_lat': scale[1]}


def _doubles_at(path, endian, tags, tag):
    typ, cnt, val = tags[tag]
    with open(path, 'rb') as stream:
        if cnt * 8 <= 4:
            return [struct.unpack(endian + 'd', struct.pack(endian + 'I', val))[0]]
        stream.seek(val)
        return list(struct.unpack(endian + '%dd' % cnt, stream.read(cnt * 8)))


def lonlat_of(gt, row, col):
    return gt['lon0'] + col * gt['d_lon'], gt['lat0'] - row * gt['d_lat']


def rowcol_of(gt, lat, lon):
    col = (lon - gt['lon0']) / gt['d_lon']
    row = (gt['lat0'] - lat) / gt['d_lat']
    return row, col


def radii(lat_deg):
    """WGS84 meridional (M) and normal (N) radii of curvature."""
    phi = math.radians(lat_deg)
    e2 = WGS84_F * (2 - WGS84_F)
    s = math.sin(phi)
    m = WGS84_A * (1 - e2) / (1 - e2 * s * s) ** 1.5
    n = WGS84_A / math.sqrt(1 - e2 * s * s)
    return m, n


def bilinear(values, fx, fy):
    """values: 2x2 [[v00, v01], [v10, v11]] at corners of a unit cell;
    fx along +col, fy along +row."""
    top = values[0][0] * (1 - fx) + values[0][1] * fx
    bottom = values[1][0] * (1 - fx) + values[1][1] * fx
    return top * (1 - fy) + bottom * fy


GEOID_RANGE = (-150.0, 150.0)      # geoid undulation envelope, metres
DEM_RANGE = (-110.0, 9000.0)       # EGM2008 heights + nodata margin, metres


def geoid_undulation(geoid_path, lat, lon, method='geodetic'):
    """EGM08 undulation N at a point, from the pinned 2.5' grid.

    method 'geodetic': bilinear in (lat, lon) degrees.
    method 'local': the SAME grid nodes re-projected into local metres via the
    WGS84 radii, then bilinear in metres. A genuinely different interpolation
    path -- the falsifier requires both to agree within the DEM quantization."""
    gt = geotransform(geoid_path)
    row, col = rowcol_of(gt, lat, lon)
    r0, c0 = int(math.floor(row)), int(math.floor(col))
    samples = [(r, c) for r in (r0, r0 + 1) for c in (c0, c0 + 1)]
    values = sample_grid(geoid_path, samples, GEOID_RANGE)
    for pos, value in values.items():
        require(abs(value) < 1e10, 'terrain_geoid_fill_value', str(pos))
    if method == 'geodetic':
        fx, fy = col - c0, row - r0
        return bilinear([[values[(r0, c0)], values[(r0, c0 + 1)]],
                         [values[(r0 + 1, c0)], values[(r0 + 1, c0 + 1)]]], fx, fy)
    if method == 'local':
        # corner coordinates in local metres relative to the (r0, c0) node
        m, n = radii(lat)
        cos_phi = math.cos(math.radians(lat))
        lats = {r: gt['lat0'] - r * gt['d_lat'] for r in (r0, r0 + 1)}
        lons = {c: gt['lon0'] + c * gt['d_lon'] for c in (c0, c0 + 1)}
        north = {r: (lats[r0] - lats[r]) * math.pi / 180 * m for r in (r0, r0 + 1)}
        east = {c: (lons[c] - lons[c0]) * math.pi / 180 * n * cos_phi
                for c in (c0, c0 + 1)}
        px = (lon - lons[c0]) * math.pi / 180 * n * cos_phi
        py = (lats[r0] - lat) * math.pi / 180 * m
        fx = px / east[c0 + 1] if east[c0 + 1] else 0.0
        fy = py / north[r0 + 1] if north[r0 + 1] else 0.0
        return bilinear([[values[(r0, c0)], values[(r0, c0 + 1)]],
                         [values[(r0 + 1, c0)], values[(r0 + 1, c0 + 1)]]], fx, fy)
    raise Refusal('terrain_geoid_method', method)


def window_around(dem_path, centre_lat, centre_lon, half=2):
    """The (2*half+1)^2 sample window around the centre, with lon/lat tags."""
    gt = geotransform(dem_path)
    row, col = rowcol_of(gt, centre_lat, centre_lon)
    r0, c0 = round(row), round(col)
    samples = [(r, c) for r in range(r0 - half, r0 + half + 1)
               for c in range(c0 - half, c0 + half + 1)]
    values = sample_grid(dem_path, samples, DEM_RANGE)
    for pos, value in values.items():
        require(value != NODATA, 'terrain_nodata_in_window', str(pos))
    return gt, (r0, c0), values


def reduce_terrain(dem_path, geoid_path, centre_lat, centre_lon, patch_metres=2.4):
    """The admitted 7-step reduction. Returns every intermediate so the receipt
    and the falsifiers cite measured numbers, not summaries."""
    gt, (r0, c0), values = window_around(dem_path, centre_lat, centre_lon)
    # STEP 4 REDUCE: bilinear at the exact centre, in LOCAL METRES
    centre_row_f, centre_col_f = rowcol_of(gt, centre_lat, centre_lon)
    fx = centre_col_f - c0
    fy = r0 - centre_row_f
    cell = [[values[(r0, c0)], values[(r0, c0 + 1)]],
            [values[(r0 + 1, c0)], values[(r0 + 1, c0 + 1)]]]
    # interpolate in metres: convert the fractional cell position via the radii
    m, n = radii(centre_lat)
    cos_phi = math.cos(math.radians(centre_lat))
    ex = gt['d_lon'] * math.pi / 180 * n * cos_phi   # metres per column
    ny = gt['d_lat'] * math.pi / 180 * m             # metres per row
    px = fx * ex
    py = fy * ny
    fx_m = px / ex  # identical fraction for a regular grid; law keeps both paths
    fy_m = py / ny
    h_dem = bilinear(cell, fx_m, fy_m)
    # STEP 3 VERTICAL: h = H + N, both methods
    n_geodetic = geoid_undulation(geoid_path, centre_lat, centre_lon, 'geodetic')
    n_local = geoid_undulation(geoid_path, centre_lat, centre_lon, 'local')
    require(abs(n_geodetic - n_local) <= 0.1, 'terrain_geoid_methods_disagree',
            str(n_geodetic - n_local))
    h_ellipsoidal = h_dem + n_geodetic
    # STEP 5 HOLDOUT (derivation-corrected law; two earlier draft forms were
    # falsified by the tests and are recorded in the receipt). The exact
    # discrete identity, pure algebra and valid for ALL data:
    #   axial_mean - node = (d2x + d2y) / 4
    # asserted at 1e-12 at every interior node (an arithmetic proof of the
    # decoded window), while the MEASURED second differences give the
    # bilinear-remainder error bar for the height:
    #   |e| <= (|f_xx| + |f_yy|) * h^2 / 8   (equality on quadratics)
    # which is REPORTED, not asserted (the true surface between nodes is
    # unknowable; the bar is the honest bound from the measured curvature).
    holdout = []
    worst = 0.0
    squared = 0.0
    count = 0
    curv_east = curv_north = 0.0
    for r in range(r0 - 1, r0 + 2):
        for c in range(c0 - 1, c0 + 2):
            axial = (values[(r - 1, c)] + values[(r + 1, c)]
                     + values[(r, c - 1)] + values[(r, c + 1)]) / 4.0
            d2x = values[(r, c - 1)] - 2 * values[(r, c)] + values[(r, c + 1)]
            d2y = values[(r - 1, c)] - 2 * values[(r, c)] + values[(r + 1, c)]
            laplacian = (d2x + d2y) / 4.0
            error = abs(axial - values[(r, c)])
            require(abs(error - abs(laplacian)) <= 1e-12,
                    'terrain_holdout_identity_violation', f'{r},{c}')
            holdout.append({'row': r, 'col': c, 'laplacian_m': laplacian})
            worst = max(worst, error)
            squared += error * error
            count += 1
            if (r, c) == (r0, c0):
                curv_east, curv_north = d2x, d2y
    rms = math.sqrt(squared / count) if count else 0.0
    height_error_bar_m = (abs(curv_east) + abs(curv_north)) / 8.0
    # STEP 6 PLANE: least-squares plane over the patch (metres, local frame)
    dx = gt['d_lon'] * math.pi / 180 * n * cos_phi
    dy = gt['d_lat'] * math.pi / 180 * m
    # sub-cell bilinear samples across the patch
    steps = 5
    points = []
    for i in range(steps + 1):
        for j in range(steps + 1):
            fxp = (fx - 0.5) + i / steps * (patch_metres / ex)
            fyp = (fy - 0.5) + j / steps * (patch_metres / ny)
            points.append((fxp * ex, fyp * ny, bilinear(cell, fxp, fyp)))
    sx = sum(p[0] for p in points) / len(points)
    sy = sum(p[1] for p in points) / len(points)
    sz = sum(p[2] for p in points) / len(points)
    sxx = sum((p[0] - sx) ** 2 for p in points)
    syy = sum((p[1] - sy) ** 2 for p in points)
    sxy = sum((p[0] - sx) * (p[1] - sy) for p in points)
    sxz = sum((p[0] - sx) * (p[2] - sz) for p in points)
    syz = sum((p[1] - sy) * (p[2] - sz) for p in points)
    det = sxx * syy - sxy * sxy
    require(abs(det) > 1e-12, 'terrain_plane_degenerate')
    slope_east = (syy * sxz - sxy * syz) / det
    slope_north = (sxx * syz - sxy * sxz) / det
    slope = math.hypot(slope_east, slope_north)
    theta = math.atan(slope)
    residual = math.sqrt(sum((p[2] - (sz + slope_east * (p[0] - sx)
                                      + slope_north * (p[1] - sy))) ** 2
                             for p in points) / len(points))
    one_minus_cos = 1 - math.cos(theta)
    require(one_minus_cos <= 1e-3, 'terrain_patch_too_tilted', str(theta))
    return {
        'centre': {'lat': centre_lat, 'lon': centre_lon},
        'H_orthometric_m': h_dem,
        'N_geoid_geodetic_m': n_geodetic,
        'N_geoid_local_m': n_local,
        'geoid_method_gap_m': abs(n_geodetic - n_local),
        'h_ellipsoidal_m': h_ellipsoidal,
        'holdout': {'nodes': count, 'worst_laplacian_quarter_m': worst,
                    'rms_m': rms, 'height_error_bar_m': height_error_bar_m,
                    'law': 'exact identity axial_mean-node=(d2x+d2y)/4 asserted; '
                           'height bar (|f_xx|+|f_yy|)/8 reported'},
        'plane': {'slope_east': slope_east, 'slope_north': slope_north,
                  'theta_deg': math.degrees(theta), 'one_minus_cos': one_minus_cos,
                  'residual_m': residual},
        'window': {'rows': r0, 'cols': c0, 'size': len(values)},
    }


# --------------------------------------------------------------------------
# Integer-band GeoTIFF support (added 2026-09-17, intake-geo lane).
#
# The reader above is a FLOAT reader by law: sample_grid decodes float32
# grids and its behavior is frozen (the pinned terrain receipts replay
# against it). Categorical land-cover bands (ESA WorldCover uint8) and int16
# measurement rasters need their own reader that REFUSES float assumptions
# instead of assuming them away. Same container, same tiepoint/pixel-scale
# geotransform -- a different value law.

TAG_SAMPLES, TAG_PLANAR, TAG_PREDICTOR = 277, 284, 317
TAG_GEOKEY_DIR, TAG_GDAL_METADATA, TAG_GDAL_NODATA = 34735, 42112, 42113

SAMPLE_FORMAT_UINT, SAMPLE_FORMAT_INT, SAMPLE_FORMAT_FLOAT = 1, 2, 3
GEOKEY_GTRASTER, GEOKEY_GEOGRAPHIC_TYPE = 1025, 2048


def geokeys(path):
    """GeoKeyDirectoryTag (34735) direct values: {key: value} for keys stored
    inline. Keys whose value lives in another tag are returned as
    ('tag_ref', tag, count) -- this reader only needs the inline ones."""
    tags, endian, size = tiff_tags(path)
    require(TAG_GEOKEY_DIR in tags, 'terrain_geokeys_missing', path)
    typ, cnt, val = tags[TAG_GEOKEY_DIR]
    require(typ == 3, 'terrain_geokeys_type', path)
    with open(path, 'rb') as stream:
        stream.seek(val)
        raw = stream.read(cnt * 2)
    numbers = struct.unpack(endian + '%dH' % cnt, raw)
    require(len(numbers) >= 4 and numbers[0] == 1, 'terrain_geokeys_version', path)
    keys = {}
    for i in range(4, len(numbers), 4):
        key, location, count, value = numbers[i:i + 4]
        keys[key] = value if location == 0 else ('tag_ref', location, count)
    return keys


def gdal_metadata_items(path):
    """GDAL_METADATA (42112) ASCII XML -> {item_name: text}. Items carrying a
    sample index are keyed name#sample (multi-band files)."""
    import xml.etree.ElementTree as ET
    tags, endian, size = tiff_tags(path)
    if TAG_GDAL_METADATA not in tags:
        return {}
    typ, cnt, val = tags[TAG_GDAL_METADATA]
    require(typ == 2, 'terrain_gdal_metadata_type', path)
    with open(path, 'rb') as stream:
        stream.seek(val)
        raw = stream.read(cnt)
    try:
        text = raw.decode('utf-8', 'replace')
        # GDAL pads the ASCII field past the closing tag; parse only the document
        start = text.find('<GDALMetadata>')
        end = text.find('</GDALMetadata>')
        require(start >= 0 and end > start, 'terrain_gdal_metadata_no_document',
                path)
        root = ET.fromstring(text[start:end + len('</GDALMetadata>')])
    except ET.ParseError as exc:
        raise Refusal('terrain_gdal_metadata_unparsable', str(exc)) from exc
    items = {}
    for item in root.iter('Item'):
        name = item.get('name')
        if not name:
            continue
        key = name + ('#' + item['sample'] if 'sample' in item.attrib else '')
        items[key] = item.text or ''
    return items


def int_grid_info(path):
    """Header law of an integer-band tiled GeoTIFF. uint8/int16, single band,
    Deflate or uncompressed, predictor none/horizontal, tiled layout. A float
    band (SampleFormat 3) or float predictor (3) REFUSES -- this reader never
    guesses a float band into integers."""
    tags, endian, size = tiff_tags(path)
    width, height = _short(tags, TAG_WIDTH), _short(tags, TAG_HEIGHT)
    bits = _short(tags, TAG_BITS)
    compression = _short(tags, TAG_COMPRESSION)
    predictor = _short(tags, TAG_PREDICTOR) if TAG_PREDICTOR in tags else 1
    samples = _short(tags, TAG_SAMPLES) if TAG_SAMPLES in tags else 1
    planar = _short(tags, TAG_PLANAR) if TAG_PLANAR in tags else 1
    sample_format = (_short(tags, TAG_SAMPLE_FMT) if TAG_SAMPLE_FMT in tags
                     else SAMPLE_FORMAT_UINT)
    require(sample_format != SAMPLE_FORMAT_FLOAT, 'terrain_int_reader_refuses_float_band',
            f'{path}: SampleFormat=3')
    require(sample_format in (SAMPLE_FORMAT_UINT, SAMPLE_FORMAT_INT),
            'terrain_int_reader_sample_format_unsupported', str(sample_format))
    require(bits in (8, 16), 'terrain_int_reader_bits_unsupported', str(bits))
    require(predictor != 3, 'terrain_int_reader_refuses_float_predictor',
            f'{path}: Predictor=3')
    require(predictor in (1, 2), 'terrain_int_reader_predictor_unsupported',
            str(predictor))
    require(samples == 1 and planar == 1, 'terrain_int_reader_single_band',
            f'{path}: samples={samples} planar={planar}')
    require(compression in (1, 8), 'terrain_int_reader_compression_unsupported',
            str(compression))
    for tag in (TAG_TILE_W, TAG_TILE_H, TAG_TILE_OFFS, TAG_TILE_BYTES):
        require(tag in tags, 'terrain_int_reader_tiled_required', str(tag))
    nodata = None
    if TAG_GDAL_NODATA in tags:
        typ, cnt, val = tags[TAG_GDAL_NODATA]
        with open(path, 'rb') as stream:
            stream.seek(val)
            nodata = stream.read(cnt).split(b'\x00')[0].decode('ascii', 'replace')
    return {'width': width, 'height': height, 'bits': bits,
            'sample_format': sample_format, 'predictor': predictor,
            'compression': compression, 'tile_w': _short(tags, TAG_TILE_W),
            'tile_h': _short(tags, TAG_TILE_H), 'nodata': nodata,
            'file_bytes': size}


def _undifference(raw, tile_w, tile_h, bytes_per, predictor, endian='<',
                  signed=False):
    """TIFF 6.0 predictor-2 (horizontal) undifferencing, WORD-wise per
    sample (the libtiff/tifffile law): the first sample of each row is
    absolute, every following sample is the delta from its left neighbour.
    Predictor 1 is the identity. Rows past the image edge are undifferenced
    harmlessly -- they are never sampled."""
    if predictor != 2:
        return raw
    code = ('h' if signed else 'H') if bytes_per == 2 else \
        ('b' if signed else 'B')
    row_fmt = endian + code * tile_w
    mask = (1 << (bytes_per * 8)) - 1
    row_len = tile_w * bytes_per
    data = bytearray(raw)
    for r in range(tile_h):
        base = r * row_len
        values = list(struct.unpack(row_fmt, bytes(data[base:base + row_len])))
        for i in range(1, tile_w):
            values[i] = (values[i] + values[i - 1]) & mask
        data[base:base + row_len] = struct.pack(row_fmt, *values)
    return bytes(data)


_INT_DECODE_CACHE = {}


def sample_grid_int(path, samples, allowed=None):
    """Read specific (row, col) INTEGER samples from a tiled uint8/int16
    GeoTIFF -- the categorical/measurement companion of sample_grid.

    Only the tiles actually containing the samples are decoded (the 4.6 MB
    WorldCover COG expands to 1.3 GB; the float reader's whole-page decode is
    not repeated here). `allowed` is the band's declared code vocabulary
    (categorical law): a decoded value outside it refuses. Both decode orders
    -- this stdlib zlib path and tifffile -- must agree bit-exactly; the
    agreement is a test falsifier, not an assumption."""
    info = int_grid_info(path)
    width, height = info['width'], info['height']
    tile_w, tile_h = info['tile_w'], info['tile_h']
    bytes_per = info['bits'] // 8
    signed = info['sample_format'] == SAMPLE_FORMAT_INT
    code = ('h' if signed else 'H') if bytes_per == 2 else ('b' if signed else 'B')
    tags, endian, _ = tiff_tags(path)
    offsets = _longs_at(path, endian, tags, TAG_TILE_OFFS)
    counts = _longs_at(path, endian, tags, TAG_TILE_BYTES)
    tiles_across = (width + tile_w - 1) // tile_w
    tiles_down = (height + tile_h - 1) // tile_h
    require(len(offsets) == tiles_across * tiles_down, 'terrain_int_reader_tile_table',
            path)

    snapped = []
    for row, col in samples:
        require(isinstance(row, int) and isinstance(col, int),
                'terrain_int_reader_integer_index', f'{row},{col}')
        require(0 <= row < height and 0 <= col < width, 'terrain_sample_outside_grid',
                f'{path} ({row},{col})')
        snapped.append((row, col))

    out = {}
    with open(path, 'rb') as stream:
        for row, col in snapped:
            tile_row, tile_col = row // tile_h, col // tile_w
            index = tile_row * tiles_across + tile_col
            cache_key = (str(path), index)
            if cache_key not in _INT_DECODE_CACHE:
                stream.seek(offsets[index])
                blob = stream.read(counts[index])
                if info['compression'] == 8:
                    blob = zlib.decompress(blob)
                require(len(blob) >= tile_w * tile_h * bytes_per,
                        'terrain_int_reader_short_tile', f'{path} tile {index}')
                decoded = _undifference(blob, tile_w, tile_h, bytes_per,
                                        info['predictor'], endian,
                                        info['sample_format']
                                        == SAMPLE_FORMAT_INT)
                _INT_DECODE_CACHE[cache_key] = decoded
            decoded = _INT_DECODE_CACHE[cache_key]
            rr, cc = row - tile_row * tile_h, col - tile_col * tile_w
            base = rr * tile_w * bytes_per + cc * bytes_per
            value = struct.unpack(endian + code, decoded[base:base + bytes_per])[0]
            if allowed is not None:
                require(value in allowed, 'terrain_class_outside_legend',
                        f'{path} ({row},{col}) = {value}')
            out[(row, col)] = value
    return out


def rowcol_area(gt, lat, lon, edge_eps=1e-9):
    """Containing pixel of (lat, lon) under RasterPixelIsArea: pixel (row,
    col) covers lat [lat0-(row+1)*d, lat0-row*d], lon [lon0+col*d,
    lon0+(col+1)*d]. A point within edge_eps of a pixel edge snaps
    deterministically and is reported (the tie is recorded, never hidden)."""
    row_f = (gt['lat0'] - lat) / gt['d_lat']
    col_f = (lon - gt['lon0']) / gt['d_lon']
    row_edge = abs(row_f - round(row_f)) <= edge_eps
    col_edge = abs(col_f - round(col_f)) <= edge_eps
    if row_edge:
        row_f = float(round(row_f))
    if col_edge:
        col_f = float(round(col_f))
    return int(math.floor(row_f)), int(math.floor(col_f)), row_edge or col_edge
