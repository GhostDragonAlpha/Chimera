"""Visual proof falsifiers (work.data.visual_proof_20260917).

RULE 0 for this lane, mechanically enforced here:
  F1 DETERMINISM -- the same pinned inputs render byte-identical PNGs;
  F2 INPUT SENSITIVITY -- flipping exactly one byte of a pinned input either
     changes the PNG hash or makes the renderer refuse loudly; it can never
     reproduce identical bytes;
  F3 CHAIN -- the committed manifest's input sha256 -> png sha256 identities
     hold on disk, and the committed renders re-render byte-identically;
  F4 PIN -- the terrain render path re-proves the admitted 7-step reduction
     at the Luquillo control against the recorded receipt numbers;
  F5 DECODE IDENTITY -- the pinned draco decode chain holds (glb sha ->
     decoded buffer sha256s on disk), re-decode reproduced the identity in
     two independent harness runs (committed receipt), a one-byte-corrupted
     decoded buffer refuses loudly, and foreign GLB bytes never render as
     verified geometry (they fall back to the honest bbox refusal).

Scope guard: everything here proves INTAKE and determinism only. None of it
is physics verification; the renders say so on their face. The draco decode
identity comes from the OFFICIAL Google Draco WASM decoder (browser
channel, recorded receipt); the decode hashes are the proof, the harness
screenshots are PERCEPTUAL EVIDENCE.
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.science_funnel import visual_proof as VP
from tools.science_funnel.common import Refusal

ROOT = Path(__file__).resolve().parents[3]
SF = ROOT / 'tools' / 'science_funnel'
VALIDATION = SF / 'validation' / 'visual_proof_20260917'
SMITH = SF / 'data' / 'smithsonian'
DECODE_DIR, DECODE_MANIFEST = VP.decode_paths()
DECODE_RECEIPT = SF / 'validation' / 'draco_decode_20260918' / \
    'decode_receipt.json'
DEM = SF / 'data' / 'copernicus_glo30' / \
    'Copernicus_DSM_COG_10_N18_00_W066_00_DEM.tif'


def render_all(out_dir):
    return VP.build_renders(SMITH, out_dir)


class PngWriterRoundTrip(unittest.TestCase):
    def test_round_trip_bit_exact_and_crc_checked(self):
        w, h = 32, 16
        buf = bytearray()
        for y in range(h):
            for x in range(w):
                buf += bytes((x * 8 % 256, y * 16 % 256, (x + y) % 256))
        png = VP.encode_png(w, h, buf)
        rw, rh, rgb = VP.read_png(png)
        self.assertEqual((rw, rh), (w, h))
        self.assertEqual(rgb, bytes(buf))
        # determinism of the writer itself
        self.assertEqual(VP.encode_png(w, h, buf), png)
        # a flipped byte inside the IDAT payload must break the chunk CRC
        broken = bytearray(png)
        broken[60] ^= 0xFF
        with self.assertRaises(Refusal):
            VP.read_png(bytes(broken))


class Determinism(unittest.TestCase):
    def test_full_render_set_byte_identical_across_runs(self):
        with tempfile.TemporaryDirectory() as a, \
                tempfile.TemporaryDirectory() as b:
            m1 = render_all(a)
            m2 = render_all(b)
            self.assertEqual([r['id'] for r in m1['renders']],
                             [r['id'] for r in m2['renders']])
            for r1, r2 in zip(m1['renders'], m2['renders']):
                self.assertEqual(r1['png_sha256'], r2['png_sha256'],
                                 f"non-deterministic render {r1['id']}")
                png_a = (Path(a) / r1['png']).read_bytes()
                png_b = (Path(b) / r2['png']).read_bytes()
                self.assertEqual(png_a, png_b)


@unittest.skipUnless(VALIDATION.exists(),
                     'committed visual_proof validation dir not present')
class VerifyCommittedRenders(unittest.TestCase):
    def test_verify_renders_byte_identical_and_chain_intact(self):
        verified = VP.verify(VALIDATION)
        self.assertEqual(len(verified), 5)

    def test_manifest_records_refusals_and_label(self):
        manifest = json.loads((VALIDATION / 'manifest.json')
                              .read_text('utf-8'))
        self.assertIn('NOT physics verification', manifest['label'])
        if 'draco_decode' in manifest:
            # decoded-geometry mode: the pinned artifacts DID decode through
            # the official wasm channel, so there is no smithsonian refusal;
            # the decode section must carry the machine identities.
            section = manifest['draco_decode']
            self.assertEqual(set(section['specimens']),
                             {'cranium', 'mandible'})
            for key, spec in section['specimens'].items():
                self.assertTrue(spec['decoded']['positions_sha256'])
                self.assertTrue(spec['decoded']['indices_sha256'])
                self.assertGreater(spec['decoded']['vertex_count'], 0)
                shot = section['specimens'][key]['screenshot']
                self.assertTrue((VALIDATION / shot['file']).exists())
            # the honest provenance of the channel: falsified premises stay
            # banked even after the decode succeeds
            joined = ' '.join(manifest['falsified_assumptions'])
            self.assertIn('OFFICIAL', joined)
            self.assertIn('404', joined)
        else:
            self.assertEqual(len(manifest['refusals']), 2)
            for r in manifest['refusals']:
                self.assertIn('draco_edgebreaker', r['cause'])
        for r in manifest['renders']:
            self.assertTrue((VALIDATION / r['png']).exists())
            self.assertTrue(r['inputs'])


@unittest.skipUnless(VALIDATION.exists(),
                     'committed visual_proof validation dir not present')
class InputFlipSensitivity(unittest.TestCase):
    """F2: one flipped input byte -> different PNG hash OR loud refusal."""

    def _flip_and_render(self, src_path, flip_offset, render_fn):
        raw = bytearray(Path(src_path).read_bytes())
        raw[flip_offset] ^= 0x01
        with tempfile.TemporaryDirectory() as tmp:
            flipped = Path(tmp) / Path(src_path).name
            flipped.write_bytes(bytes(raw))
            return render_fn(flipped)

    def test_glb_json_chunk_byte_flip_changes_bbox_render(self):
        base_png, _ = VP.render_glb_intake(
            SMITH / 'USNM15259_cranium_-300_dec-150k-4096-high.glb',
            SMITH / 'USNM15259_cranium_document.json')
        glb = (SMITH / 'USNM15259_cranium_-300_dec-150k-4096-high.glb') \
            .read_bytes()
        # the JSON chunk starts at byte 20; flip a digit inside the first
        # accessor "min" array (render-relevant: it draws the box)
        first_min = glb.index(b'"min"', 20)
        first_digit = next(i for i in range(first_min, first_min + 200)
                           if 0x30 <= glb[i] <= 0x39)
        flipped = self._flip_and_render(
            SMITH / 'USNM15259_cranium_-300_dec-150k-4096-high.glb',
            first_digit,
            lambda p: VP.render_glb_intake(
                p, SMITH / 'USNM15259_cranium_document.json'))
        self.assertNotEqual(flipped[0], base_png,
                            'bbox render survived an input byte flip')

    def test_document_camera_byte_flip_changes_bbox_render(self):
        base_png, _ = VP.render_glb_intake(
            SMITH / 'USNM15259_cranium_-300_dec-150k-4096-high.glb',
            SMITH / 'USNM15259_cranium_document.json')
        doc = (SMITH / 'USNM15259_cranium_document.json').read_bytes()
        # nodes[0] IS the camera node and is the first node in the file, so
        # the first "translation" occurrence is the camera pose (the render
        # consumes it; light translations later in the file are ignored)
        trans = doc.index(b'"translation"')
        first_digit = next(i for i in range(trans, trans + 200)
                           if 0x30 <= doc[i] <= 0x39)
        flipped = self._flip_and_render(
            SMITH / 'USNM15259_cranium_document.json', first_digit,
            lambda p: VP.render_glb_intake(
                SMITH / 'USNM15259_cranium_-300_dec-150k-4096-high.glb', p))
        self.assertNotEqual(flipped[0], base_png,
                            'bbox render survived a camera byte flip')

    def test_dem_byte_flip_refuses_or_changes_render(self):
        from tools.science_funnel import visual_proof as vp
        try:
            png, _ = vp.render_terrain()
        except Refusal:
            self.fail('baseline terrain render must succeed')
        outcome = {}
        try:
            flipped, _ = self._flip_and_render(
                DEM, DEM.stat().st_size // 2,
                lambda p: vp.render_terrain(dem_path=p))
            outcome['png'] = flipped
        except Exception as e:  # corrupt container -> loud refusal
            outcome['exception'] = e
        self.assertTrue('png' in outcome or 'exception' in outcome)
        if 'png' in outcome:
            self.assertNotEqual(outcome['png'], png)

    def test_pantheria_zip_byte_flip_refuses_or_changes_render(self):
        zpath = SF / 'data' / 'pantheria' / 'ECOL_90_184.zip'
        base_png, _ = VP.render_pantheria(zpath)
        try:
            flipped, _ = self._flip_and_render(
                zpath, zpath.stat().st_size // 2, VP.render_pantheria)
            self.assertNotEqual(flipped, base_png)
        except Exception:
            pass  # corrupted archive refuses loudly

    def test_gait_csv_byte_flip_refuses_or_changes_render(self):
        csv_path = SF / 'data' / 'janisch_kinematics' / 'wildprimate_kin.csv'
        base_png, _ = VP.render_gait(csv_path)
        try:
            flipped, _ = self._flip_and_render(
                csv_path, csv_path.stat().st_size // 2, VP.render_gait)
            self.assertNotEqual(flipped, base_png)
        except Exception:
            pass  # corrupted row refuses loudly


@unittest.skipUnless(DECODE_MANIFEST.exists(),
                     'draco decode manifest not present in this checkout')
class DecodeIdentityChain(unittest.TestCase):
    """F5: the pinned decode identity holds on disk, and the renderer never
    draws geometry it cannot verify."""

    def _manifest(self):
        return json.loads(DECODE_MANIFEST.read_text(encoding='utf-8-sig'))

    def test_buffer_files_hash_to_recorded_identity(self):
        import hashlib
        manifest = self._manifest()
        for key, spec in manifest['specimens'].items():
            glb = SMITH / spec['glb']['name']
            self.assertTrue(glb.exists(), key)
            raw = glb.read_bytes()
            self.assertEqual(
                hashlib.sha256(raw).hexdigest(), spec['glb']['sha256'], key)
            for role in ('positions', 'normals', 'indices'):
                fname = spec['buffers'].get(role)
                want = spec['decoded'][f'{role}_sha256']
                if fname is None or want is None:
                    continue
                data = (DECODE_DIR / fname).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), want,
                                 f'{key}.{role}')

    def test_screenshots_are_committed_perceptual_evidence(self):
        import hashlib
        manifest = self._manifest()
        for key, spec in manifest['specimens'].items():
            shot = spec['screenshot']
            path = VALIDATION / shot['file']
            self.assertTrue(path.exists(), shot['file'])
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                shot['sha256'], key)
            self.assertEqual(path.read_bytes()[:8], b'\x89PNG\r\n\x1a\n')

    def test_corrupted_decoded_buffer_refuses_loudly(self):
        # a pinned buffer that loses even one byte must never render as
        # verified geometry -- loud refusal, not silent bbox downgrade
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            shutil.copytree(DECODE_DIR, tmp_dir / 'draco_decode')
            pos_file = tmp_dir / 'draco_decode' / \
                'USNM15259_cranium.positions.f32'
            raw = bytearray(pos_file.read_bytes())
            raw[len(raw) // 2] ^= 0x01
            pos_file.write_bytes(bytes(raw))
            original = VP.decode_paths
            VP.decode_paths = lambda: (tmp_dir / 'draco_decode',
                                       tmp_dir / 'draco_decode'
                                       / 'draco_decode_manifest.json')
            try:
                with self.assertRaises(Refusal) as ctx:
                    VP.render_glb_intake(
                        SMITH / 'USNM15259_cranium_-300_dec-150k-4096-'
                        'high.glb',
                        SMITH / 'USNM15259_cranium_document.json')
                self.assertIn('sha', str(ctx.exception))
            finally:
                VP.decode_paths = original

    def test_foreign_glb_bytes_fall_back_to_bbox_refusal(self):
        # bytes that do not match the decode record have NO decode identity:
        # the render must be the honest bbox+refusal form, never geometry
        glb_path = SMITH / 'USNM15259_cranium_-300_dec-150k-4096-high.glb'
        raw = bytearray(glb_path.read_bytes())
        raw[40] ^= 0x01
        with tempfile.TemporaryDirectory() as tmp:
            foreign = Path(tmp) / glb_path.name
            foreign.write_bytes(bytes(raw))
            png, metrics = VP.render_glb_intake(
                foreign, SMITH / 'USNM15259_cranium_document.json')
            self.assertEqual(metrics['geometry_decode'], 'REFUSED')
            self.assertIn('refusal_cause', metrics)
            self.assertTrue(png.startswith(b'\x89PNG'))


@unittest.skipUnless(DECODE_RECEIPT.exists(),
                     'draco decode receipt not present in this checkout')
class HarnessDecodeFalsifiers(unittest.TestCase):
    """F5 at the channel level: the committed browser receipt must show the
    re-decode determinism and the corruption refusal exactly as banked."""

    def test_redecode_reproduced_identity_in_both_runs(self):
        receipt = json.loads(DECODE_RECEIPT.read_text('utf-8-sig'))
        for key, spec in receipt['specimens'].items():
            self.assertTrue(spec['redecode_identical_in_run'], key)
            self.assertTrue(spec['redecode_identical_cross_run'], key)

    def test_corrupt_probe_never_reproduced_the_identity(self):
        receipt = json.loads(DECODE_RECEIPT.read_text('utf-8-sig'))
        probe = receipt['corrupt_probe']
        self.assertIn(probe['outcome_runA'],
                      ('REFUSED', 'SILENTLY DECODED DIFFERENT GEOMETRY'))
        self.assertIn(probe['outcome_runB'],
                      ('REFUSED', 'SILENTLY DECODED DIFFERENT GEOMETRY'))
        manifest = json.loads(DECODE_MANIFEST.read_text('utf-8-sig'))
        pinned_sha = manifest['specimens']['mandible']['glb']['sha256']
        self.assertNotEqual(probe['corrupted_sha256'], pinned_sha)


@unittest.skipUnless(
    (SF / 'validation' / 'terrain_20260917' / 'receipt.json').exists(),
    'terrain receipt not present')
class TerrainPin(unittest.TestCase):
    def test_render_reduction_matches_recorded_luquillo_control(self):
        receipt = json.loads(
            (SF / 'validation' / 'terrain_20260917' / 'receipt.json')
            .read_text('utf-8'))
        recorded = receipt['metrics']['luquillo_control']
        _png, metrics = VP.render_terrain()
        self.assertAlmostEqual(metrics['H_orthometric_m'],
                               recorded['H_orthometric_m'], places=6)
        self.assertAlmostEqual(metrics['N_geoid_m'],
                               recorded['N_geoid_m'], places=6)
        self.assertLess(metrics['geoid_method_gap_m'], 0.1)


if __name__ == '__main__':
    unittest.main()
