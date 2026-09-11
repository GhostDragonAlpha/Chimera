"""Synthetic contract tests for the DYAD provider interface (CPU only; no
engine, no model, no network). Covers the preregistered falsifiers."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dyad_provider import (  # noqa: E402
    Capture, DyadRefusal, DyadReviewRequest, LocalSensesDyadProvider,
    RemoteDyadProvider, SubagentDyadProvider, build_verdict, parse_numeric_mentions,
    select_provider)


def make_capture(tmp, index, content=b'frame'):
    p = Path(tmp) / ('cap_%d.png' % index)
    p.write_bytes(content)
    import hashlib
    return Capture(index=index, path=str(p), sha256=hashlib.sha256(content).hexdigest(),
                   metadata={'camera': 'front'})


def make_request(captures, review_type='still', **kw):
    base = dict(task='t1', attempt='a1', physical_context='render of the teddy shell',
                claim_under_exam='the shell reads as one closed surface',
                questions=('What shapes do you observe in the foreground?', 'Name the worst visual issue.'),
                captures=tuple(captures), runtime_metadata={'engine_head': 'x' * 40},
                review_type=review_type,
                evidence_limits='still images cannot certify motion or timing')
    base.update(kw)
    return DyadReviewRequest(**base)


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_request_validation(self):
        one = [make_capture(self.tmp.name, 1)]
        two = [make_capture(self.tmp.name, 1), make_capture(self.tmp.name, 2, b'frame2')]
        with self.assertRaisesRegex(DyadRefusal, 'invalid_review_type'):
            make_request(two, review_type='hologram').validate()
        with self.assertRaisesRegex(DyadRefusal, 'captures_required'):
            make_request([], review_type='still').validate()
        with self.assertRaisesRegex(DyadRefusal, 'still_requires_exactly_one_capture'):
            make_request(two, review_type='still').validate()
        with self.assertRaisesRegex(DyadRefusal, 'temporal_review_requires_multiple_captures'):
            make_request(one, review_type='ordered_frames').validate()
        with self.assertRaisesRegex(DyadRefusal, 'movie_requires_artifact_reference'):
            make_request(two, review_type='movie').validate()
        bad = Capture(1, 'x.png', 'deadbeef', {})
        with self.assertRaisesRegex(DyadRefusal, 'invalid_capture_hash'):
            make_request([bad]).validate()
        with self.assertRaisesRegex(DyadRefusal, 'missing_claim_under_exam'):
            make_request(one, claim_under_exam='  ').validate()
        # index set must be exactly 1..n (no duplicates, no gaps)
        dup = [Capture(1, 'a.png', 'f' * 64, {}), Capture(1, 'b.png', 'f' * 64, {})]
        with self.assertRaisesRegex(DyadRefusal, 'invalid_capture_order_or_duplicate'):
            make_request(dup, review_type='ordered_frames').validate()
        gap = [Capture(1, 'a.png', 'f' * 64, {}), Capture(3, 'b.png', 'f' * 64, {})]
        with self.assertRaisesRegex(DyadRefusal, 'invalid_capture_order_or_duplicate'):
            make_request(gap, review_type='ordered_frames').validate()
        make_request(two, review_type='ordered_frames').validate()
        make_request(two, review_type='movie',
                     runtime_metadata={'movie_artifact': 'rot.mp4'}).validate()

    def test_capture_integrity_fail_closed(self):
        one = [make_capture(self.tmp.name, 1)]
        prov = SubagentDyadProvider(lambda *a: ('', None, 'stop', [], '', 'unclear'))
        missing = Capture(1, str(Path(self.tmp.name) / 'nope.png'), one[0].sha256, {})
        with self.assertRaisesRegex(DyadRefusal, 'capture_missing'):
            prov.review(make_request([missing]))
        corrupt = make_capture(self.tmp.name, 2, b'tampered')
        corrupt = Capture(1, corrupt.path, one[0].sha256, {})
        with self.assertRaisesRegex(DyadRefusal, 'capture_hash_mismatch'):
            prov.review(make_request([corrupt]))

    def test_temporal_capability_ladder(self):
        one = [make_capture(self.tmp.name, 1)]
        two = [make_capture(self.tmp.name, 1), make_capture(self.tmp.name, 2, b'f2')]
        still_only = SubagentDyadProvider(lambda *a: ('raw', None, 'stop', [], '', 'unclear'),
                                          provider_id='still-only')
        still_only.temporal = 'none'  # pin to still-only for the ladder test
        still_only.review(make_request(one))
        with self.assertRaisesRegex(DyadRefusal, 'provider_cannot_verify_temporal_claim'):
            still_only.review(make_request(two, review_type='ordered_frames'))
        with self.assertRaisesRegex(DyadRefusal, 'provider_cannot_verify_temporal_claim'):
            still_only.review(make_request(two, review_type='movie',
                                           runtime_metadata={'movie_artifact': 'm.mp4'}))
        frames = SubagentDyadProvider(lambda *a: ('raw', None, 'stop', [], '', 'unclear'))
        frames.temporal = 'frames'
        frames.review(make_request(two, review_type='ordered_frames'))
        with self.assertRaisesRegex(DyadRefusal, 'provider_cannot_verify_temporal_claim'):
            frames.review(make_request(two, review_type='movie',
                                       runtime_metadata={'movie_artifact': 'm.mp4'}))

    def test_no_vision_refusal(self):
        from dyad_provider import DyadProvider
        one = [make_capture(self.tmp.name, 1)]
        with self.assertRaisesRegex(DyadRefusal, 'no_vision'):
            DyadProvider().review(make_request(one))

    def test_subagent_adapter_retains_evidence(self):
        one = [make_capture(self.tmp.name, 1)]
        seen = {}

        def callback(prompt, paths):
            seen['prompt'], seen['paths'] = prompt, paths
            return ('Frame shows a smooth shell with 3 visible seams.',
                    'subagent-test-eye', 'stop', ['shell reads closed'], 'low light', 'supports')

        prov = SubagentDyadProvider(callback, provider_id='w-reviewer')
        resp = prov.review(make_request(one))
        self.assertEqual(resp.exact_prompt, seen['prompt'])
        self.assertEqual(seen['paths'], [one[0].path])
        self.assertEqual(resp.raw_response,
                         'Frame shows a smooth shell with 3 visible seams.')  # raw retained verbatim
        self.assertEqual(resp.served_model, 'subagent-test-eye')
        self.assertEqual(resp.finish_status, 'stop')
        self.assertEqual(resp.capture_identities[0]['sha256'], one[0].sha256)
        self.assertIn('DYAD visual review request', resp.exact_prompt)
        self.assertIn('1. What shapes do you observe in the foreground?', resp.exact_prompt)
        # numeric mention retained but tagged, never asserted
        mentions = [m for m in resp.verdict.numeric_mentions if '3' in m['text']]
        self.assertTrue(mentions and all(m['tag'] == 'unverified_numeric_mention' for m in mentions))
        # model agreement is never acceptance
        self.assertEqual(resp.verdict.status, 'INCONCLUSIVE')
        self.assertTrue(resp.verdict.supports_claim)

    def test_missing_served_identity_is_named_uncertainty(self):
        one = [make_capture(self.tmp.name, 1)]
        prov = SubagentDyadProvider(lambda *a: ('raw', None, 'stop', [], '', 'unclear'))
        resp = prov.review(make_request(one))
        self.assertIsNone(resp.served_model)
        self.assertIn('named uncertainty', resp.served_identity_note)
        self.assertIn('no substitution', resp.served_identity_note)

    def test_verdict_mapping_and_contradiction(self):
        v = build_verdict('contradicts', ['the mesh tears at the shoulder'], 'tear visible')
        self.assertEqual((v.status, v.supports_claim), ('FAIL', False))
        v = build_verdict('unclear', [], '')
        self.assertEqual((v.status, v.supports_claim), ('NOT_CLAIMED', None))
        v = build_verdict('supports', ['angle looks plausible'], 'consistent')
        self.assertEqual((v.status, v.supports_claim), ('INCONCLUSIVE', True))

    def test_numeric_mentions_only_tagged(self):
        ms = parse_numeric_mentions('moved 12 px and 77% of the band is dark')
        self.assertEqual(len(ms), 2)
        self.assertTrue(all(m['tag'] == 'unverified_numeric_mention' for m in ms))

    def test_provider_selection_no_fallback(self):
        sub = select_provider({'kind': 'subagent', 'callback': lambda *a: ('', None, 'stop', [], '', '')})
        self.assertIsInstance(sub, SubagentDyadProvider)
        rem = select_provider({'kind': 'remote', 'endpoint': 'https://eye.example', 'auth_env_var': 'EYE'})
        self.assertIsInstance(rem, RemoteDyadProvider)
        loc = select_provider({'kind': 'local'})
        self.assertIsInstance(loc, LocalSensesDyadProvider)
        with self.assertRaisesRegex(DyadRefusal, 'unknown_provider_kind'):
            select_provider({'kind': 'telepathy'})
        with self.assertRaisesRegex(DyadRefusal, 'remote_endpoint_must_be_https'):
            select_provider({'kind': 'remote', 'endpoint': 'http://eye.example', 'auth_env_var': 'EYE'})

    def test_local_adapter_contract(self):
        loc = LocalSensesDyadProvider(temporal='frames')
        self.assertEqual((loc.vision, loc.temporal), (True, 'frames'))
        with self.assertRaisesRegex(DyadRefusal, 'local_eye_temporal_capability'):
            LocalSensesDyadProvider(temporal='movie')
        # Live eye wiring stays in ChimeraEngine/senses.py under THE_DYAD_PROTOCOL;
        # the adapter names that boundary instead of executing it here.
        try:
            loc.review(make_request([make_capture(self.tmp.name, 1)]))
            self.fail('local adapter executed without engine wiring')
        except NotImplementedError as e:
            self.assertIn('senses.py', str(e))

    def test_malformed_callback_is_named_refusal(self):
        one = [make_capture(self.tmp.name, 1)]
        for bad in (lambda *a: None,
                    lambda *a: (None, 'm', 'stop', [], '', 'unclear'),
                    lambda *a: ('', None, 'stop', [], '', 'unclear'),
                    lambda *a: ('raw', 7, 'stop', [], '', 'unclear'),
                    lambda *a: ('raw', None, 'stop', 'not-a-list', '', 'unclear'),
                    lambda *a: ('raw', None, 'stop', [], None, 'unclear')):
            prov = SubagentDyadProvider(bad)
            with self.assertRaisesRegex(DyadRefusal, 'subagent_callback_malformed'):
                prov.review(make_request(one))

    def test_capability_validated_at_construction(self):
        from dyad_provider import DyadProvider as Base
        class Bogus(Base):
            def __init__(self):
                self.temporal = 'hologram'
                self.vision = True
                super().__init__()
        with self.assertRaisesRegex(DyadRefusal, 'invalid_temporal_capability'):
            Bogus()
        with self.assertRaisesRegex(DyadRefusal, 'invalid_temporal_capability'):
            RemoteDyadProvider('https://eye.example', 'EYE', temporal='bogus')

    def test_remote_review_refuses_unwired_by_name(self):
        rem = RemoteDyadProvider('https://eye.example', 'EYE')
        one = [make_capture(self.tmp.name, 1)]
        try:
            rem.review(make_request(one))
            self.fail('remote review executed without transport wiring')
        except NotImplementedError as e:
            self.assertIn('deployment', str(e))

    def test_prompt_deterministic_and_not_leading(self):
        one = [make_capture(self.tmp.name, 1)]
        r1, r2 = make_request(one), make_request(one)
        self.assertEqual(r1.build_prompt(), r2.build_prompt())
        prompt = r1.build_prompt()
        self.assertIn('claim under examination', prompt)
        self.assertNotIn('expected defect', prompt.lower())


if __name__ == '__main__':
    unittest.main(verbosity=2)
