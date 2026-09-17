"""Terrain reduction tests: the falsifiers are these tests, not prose.
Synthetic TIFF round-trips prove the reader bit-exactly (Deflate + float
predictor); quadratic surfaces prove the holdout remainder identity; the real
grids prove the two-method geoid agreement and the full reduction law."""
import math
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from tools.science_funnel.common import Refusal
from tools.science_funnel import terrain as T

DATA = Path(__file__).resolve().parents[1] / 'data'
DEM = DATA / 'copernicus_glo30' / 'Copernicus_DSM_COG_10_N18_00_W066_00_DEM.tif'
GEOID = DATA / 'nga_egm08' / 'us_nga_egm08_25.tif'
CAYO = (18.1565, -65.7350)


def write_tiff(path, grid, tile=4, d_lon=1.0 / 60, d_lat=1.0 / 60):
    """Encode a small float32 tiled Deflate+predictor-3 GeoTIFF. The float
    predictor is applied by imagecodecs.floatpred_encode -- the exact inverse
    of the decoder tifffile uses, so the authoritative reader accepts the
    file by construction."""
    import numpy as np
    from imagecodecs import floatpred_encode
    rows, cols = len(grid), len(grid[0])
    tiles_across = (cols + tile - 1) // tile
    tiles_down = (rows + tile - 1) // tile
    blobs = []
    for tr in range(tiles_down):
        for tc in range(tiles_across):
            block = np.zeros((tile, tile), dtype='<f4')
            for r in range(tile):
                for c in range(tile):
                    rr, cc = tr * tile + r, tc * tile + c
                    if rr < rows and cc < cols:
                        block[r, c] = grid[rr][cc]
            payload = floatpred_encode(block).tobytes()
            blobs.append(zlib.compress(payload, 9))
    # IFD layout: header(8) + IFD + out-of-line arrays + tile blobs
    entries = []

    def entry(tag, typ, count, value_bytes):
        entries.append((tag, typ, count, value_bytes))

    scale = struct.pack('<3d', d_lon, d_lat, 1.0)
    tie = struct.pack('<6d', 0.0, 0.0, 0.0, -66.0, 19.0, 0.0)  # (i,j,k, X,Y,Z)
    entry(256, 3, 1, struct.pack('<H', cols))
    entry(257, 3, 1, struct.pack('<H', rows))
    entry(258, 3, 1, struct.pack('<H', 32))
    entry(259, 3, 1, struct.pack('<H', 8))       # deflate
    entry(262, 3, 1, struct.pack('<H', 1))
    entry(277, 3, 1, struct.pack('<H', 1))
    entry(284, 3, 1, struct.pack('<H', 1))
    entry(317, 3, 1, struct.pack('<H', 3))       # float predictor
    entry(322, 3, 1, struct.pack('<H', tile))
    entry(323, 3, 1, struct.pack('<H', tile))
    entry(339, 3, 1, struct.pack('<H', 3))       # float32
    entry(33550, 12, 3, scale)
    entry(33922, 12, 6, tie)
    # sort entries by tag (TIFF requires ascending) and place big values later
    entries.sort(key=lambda e: e[0])
    # header(8) + count(2) + entries + tile-tags(2) + next-IFD pointer(4)
    ifd_size = 2 + 12 * (len(entries) + 2) + 4
    extra_base = 8 + ifd_size
    offsets_pos = extra_base
    counts_pos = offsets_pos + 4 * len(blobs)
    scale_pos = counts_pos + 4 * len(blobs)
    tie_pos = scale_pos + len(scale)
    blob_base = tie_pos + len(tie)
    offs, pos = [], blob_base
    for blob in blobs:
        offs.append(pos)
        pos += len(blob)
    tile_offsets = struct.pack('<%dI' % len(offs), *offs)
    tile_counts = struct.pack('<%dI' % len(blobs), *[len(b) for b in blobs])
    raw = bytearray(b'II' + struct.pack('<HI', 42, 8))
    raw += struct.pack('<H', len(entries) + 2)
    for tag, typ, count, value_bytes in entries:
        if tag == 33550:
            value = struct.pack('<I', scale_pos)
        elif tag == 33922:
            value = struct.pack('<I', tie_pos)
        elif tag in (256, 257, 258, 259, 262, 277, 284, 317, 322, 323, 339):
            value = value_bytes + b'\0' * (4 - len(value_bytes))
        else:
            raise AssertionError(tag)
        raw += struct.pack('<HHI', tag, typ, count) + value
    raw += struct.pack('<HHI', 324, 4, len(offs)) + struct.pack('<I', offsets_pos)
    raw += struct.pack('<HHI', 325, 4, len(blobs)) + struct.pack('<I', counts_pos)
    raw += struct.pack('<I', 0)  # next IFD
    raw += tile_offsets + tile_counts + scale + tie
    for blob in blobs:
        raw += blob
    Path(path).write_bytes(bytes(raw))


class ReaderExactness(unittest.TestCase):
    def test_synthetic_round_trip_bit_exact(self):
        """The synthetic writer encodes through imagecodecs.floatpred_encode
        (the exact inverse of the authoritative decoder), so tifffile must
        read the grid back bit-exactly."""
        grid = [[math.sin(r * 0.3) * 100 + c * 0.25 - 50 for c in range(10)]
                for r in range(9)]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'grid.tif'
            write_tiff(path, grid, tile=4)
            gt = T.geotransform(str(path))
            self.assertAlmostEqual(gt['lon0'], -66.0)
            self.assertAlmostEqual(gt['lat0'], 19.0)
            samples = T.sample_grid(str(path),
                                    [(r, c) for r in range(9) for c in range(10)],
                                    (-1e6, 1e6))
            for r in range(9):
                for c in range(10):
                    expected = struct.unpack('<f', struct.pack('<f', grid[r][c]))[0]
                    self.assertEqual(samples[(r, c)], expected,
                                     f'bit mismatch at {r},{c}')


class HoldoutIdentity(unittest.TestCase):
    def test_laplacian_identity_exact_on_arbitrary_data(self):
        # axial_mean - node == (d2x + d2y)/4 is pure algebra: it must hold
        # bit-tight on arbitrary (random-ish) data, not just smooth surfaces.
        import hashlib
        seed = 7
        for trial in range(3):
            values = {}
            for r in range(5):
                for c in range(5):
                    seed = (seed * 1103515245 + 12345) % (1 << 31)
                    values[(r, c)] = (seed / (1 << 31) - 0.5) * 200.0
            for r in range(1, 4):
                for c in range(1, 4):
                    axial = (values[(r - 1, c)] + values[(r + 1, c)]
                             + values[(r, c - 1)] + values[(r, c + 1)]) / 4.0
                    d2x = values[(r, c - 1)] - 2 * values[(r, c)] + values[(r, c + 1)]
                    d2y = values[(r - 1, c)] - 2 * values[(r, c)] + values[(r + 1, c)]
                    self.assertAlmostEqual(
                        axial - values[(r, c)], (d2x + d2y) / 4.0, places=9)

    def test_error_bar_tight_on_quadratics(self):
        # (|f_xx| + |f_yy|)/8 is exactly the bilinear centre remainder for
        # quadratics: derived bar, no free parameter.
        for fxx, fyy in ((2.0, 4.0), (1.0, 0.0), (0.0, 3.0)):
            values = {(r, c): 0.5 * fxx * (c - 2) ** 2 + 0.5 * fyy * (r - 2) ** 2
                      for r in range(5) for c in range(5)}
            cell = [[values[(2, 2)], values[(2, 3)]],
                    [values[(3, 2)], values[(3, 3)]]]
            bilinear_centre = T.bilinear(cell, 0.5, 0.5)
            exact_centre = 0.5 * fxx * 0.25 + 0.5 * fyy * 0.25
            d2x = values[(2, 1)] - 2 * values[(2, 2)] + values[(2, 3)]
            d2y = values[(1, 2)] - 2 * values[(2, 2)] + values[(3, 2)]
            bar = (abs(d2x) + abs(d2y)) / 8.0
            self.assertAlmostEqual(abs(bilinear_centre - exact_centre), bar, places=9)

    def test_bilinear_linear_exact(self):
        cell = [[1.0, 2.0], [3.0, 4.0]]
        self.assertAlmostEqual(T.bilinear(cell, 0.25, 0.75), 2.75)


class RealGrids(unittest.TestCase):
    def test_reader_matches_tifffile_second_implementation(self):
        """The two-implementation decode falsifier: the stdlib reader and
        tifffile+imagecodecs must agree on the pinned bytes."""
        import tifffile
        for path, nodes, rng in ((GEOID, [(1724, 2742), (1725, 2743)], T.GEOID_RANGE),
                                 (DEM, [(3037, 1133), (1500, 1500)], T.DEM_RANGE)):
            mine = T.sample_grid(str(path), nodes, rng)
            with tifffile.TiffFile(str(path)) as tif:
                arr = tif.pages[0].asarray()
            for r, c in nodes:
                self.assertLessEqual(abs(mine[(r, c)] - float(arr[r, c])), 1e-9,
                                     f'{path} node ({r},{c})')

    def test_geoid_two_methods_agree_at_cayo(self):
        lat, lon = CAYO
        n_geo = T.geoid_undulation(str(GEOID), lat, lon, 'geodetic')
        n_loc = T.geoid_undulation(str(GEOID), lat, lon, 'local')
        self.assertLess(abs(n_geo - n_loc), 0.1)
        # both near the rough regional undulation (~ -35 to -25 m in the
        # Caribbean); the exact assertion is method agreement, not a magnitude
        self.assertGreater(n_geo, -60.0)
        self.assertLess(n_geo, 0.0)

    def test_geoid_interpolation_matches_manual_bilinear(self):
        """Node-exactness via MY math: undulation at the centre of a known
        2x2 node block must equal the manual bilinear of the four stored
        nodes (tests the interpolation, not the geotransform roundtrip)."""
        gt = T.geotransform(str(GEOID))
        r0, c0 = 2000, 4000
        lats = [gt['lat0'] - r * gt['d_lat'] for r in (r0, r0 + 1)]
        lons = [gt['lon0'] + c * gt['d_lon'] for c in (c0, c0 + 1)]
        nodes = [(r, c) for r in (r0, r0 + 1) for c in (c0, c0 + 1)]
        v = T.sample_grid(str(GEOID), nodes, T.GEOID_RANGE)
        mid_lat = (lats[0] + lats[1]) / 2
        mid_lon = (lons[0] + lons[1]) / 2
        manual = (v[(r0, c0)] + v[(r0, c0 + 1)] + v[(r0 + 1, c0)] + v[(r0 + 1, c0 + 1)]) / 4
        got = T.geoid_undulation(str(GEOID), mid_lat, mid_lon, 'geodetic')
        self.assertAlmostEqual(got, manual, places=6)

    def test_dem_window_readable(self):
        gt, (r0, c0), values = T.window_around(str(DEM), *CAYO)
        self.assertEqual(len(values), 25)
        self.assertTrue(all(v != T.NODATA for v in values.values()))

    def test_full_reduction_law(self):
        result = T.reduce_terrain(str(DEM), str(GEOID), *CAYO)
        # falsifier outcomes (require()s already enforce violations; assert the
        # recorded numbers are sane and present)
        self.assertLess(result['geoid_method_gap_m'], 0.1)
        self.assertGreaterEqual(result['holdout']['height_error_bar_m'], 0.0)
        self.assertEqual(result['holdout']['nodes'], 9)
        self.assertLessEqual(result['plane']['one_minus_cos'], 1e-3)
        self.assertLess(abs(result['h_ellipsoidal_m']), 1000.0)
        self.assertIn('H_orthometric_m', result)


if __name__ == '__main__':
    unittest.main()
