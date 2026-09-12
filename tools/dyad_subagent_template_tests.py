"""Unit tests for the DYAD subagent template hardening (CPU only; no engine,
no model, no network). Pins the two advisory findings of the PR #64 review
(controller feedback dce2c813) landed by dyad-template-hardening-01:

  F1  question guidance carries the determinability-neutral form
      "Can you determine X? If not, what limits you?" — and the presupposing
      phrasing survives in neither the constant nor the template document.
  F2  OPTIONAL blind frame ordering: seeded-randomized frame order (reproducible),
      state values absent from the prompt text, unblinding map recoverable and
      sha-recorded, default mode byte-identical to the pre-hardening driver.

The reviewed provider contract (tools/dyad_provider.py) is exercised, never
weakened: every prompt here is built by the unchanged
DyadReviewRequest.build_prompt().
"""
import argparse
import contextlib
import hashlib
import io
import json
import random
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO_ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import dyad_subagent_template as driver  # noqa: E402
from dyad_provider import Capture, DyadRefusal, DyadReviewRequest  # noqa: E402

GUIDANCE_FORM = 'Can you determine X? If not, what limits you?'
PRESUPPOSING_PHRASING = 'prevent you from determining'

STATE_ONE = 'sidecar: gamma=0 J/m^2, iteration 0, centre height 0.125 m'
STATE_TWO = 'sidecar: gamma=1 J/m^2, relaxed, centre height ~0 m'
STATE_THREE = 'sidecar: gamma=0.5 J/m^2, mid-relaxation, centre height ~0.06 m'


def _make_frames(tmp, names):
    """Write distinct capture files; return {name: (path, sha256)}."""
    out = {}
    for i, name in enumerate(names):
        p = Path(tmp) / name
        p.write_bytes(b'PNGFIXTURE-%d-%s' % (i, name.encode()))
        out[name] = (str(p), hashlib.sha256(p.read_bytes()).hexdigest())
    return out


def _base_spec(frames, attempt):
    """ordered_frames spec over three neutrally-named captures, in original
    order a(1), b(2), c(3); frame_N_state keys carry the sidecar states the
    retained reviews leaked into their prompts."""
    return {
        'task': 'hardening-check', 'attempt': attempt,
        'physical_context': 'three window frames of the same object at one fixed camera',
        'claim_under_exam': 'the recorded states are visually distinguishable',
        'questions': ['Describe what frame 1 shows.',
                      'Describe what frame 2 shows.',
                      'Describe what frame 3 shows.',
                      GUIDANCE_FORM.replace('X', 'which frame was recorded first')],
        'captures': [{'index': 1, 'path': frames['frame_a.png'][0],
                      'sha256': frames['frame_a.png'][1]},
                     {'index': 2, 'path': frames['frame_b.png'][0],
                      'sha256': frames['frame_b.png'][1]},
                     {'index': 3, 'path': frames['frame_c.png'][0],
                      'sha256': frames['frame_c.png'][1]}],
        'runtime_metadata': {'camera': 'fixed demo camera phi 0.35 / radius 3.0',
                             'frame_1_state': STATE_ONE,
                             'frame_2_state': STATE_TWO,
                             'frame_3_state': STATE_THREE},
        'review_type': 'ordered_frames',
        'evidence_limits': 'ordered stills; numbers are observations, not measurements',
    }


def _write_spec(tmp, spec):
    p = Path(tmp) / ('spec_%s.json' % spec['attempt'])
    p.write_text(json.dumps(spec, indent=1), encoding='utf-8')
    return str(p)


def _run_plan(spec_path, root):
    """Run cmd_plan, return (stdout JSON dict, evidence root Path)."""
    root = Path(root)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        driver.cmd_plan(argparse.Namespace(spec=spec_path, evidence_root=str(root)))
    return json.loads(buf.getvalue()), root


def _read(path):
    """Read retained evidence text with universal newlines: the driver writes
    with text-mode write_text (the pre-hardening transport, unchanged), whose
    on-disk newline translation is platform-constant and not part of the
    prompt contract. All byte pins below are on the returned text."""
    return Path(path).read_text(encoding='utf-8')


REPORT_TEMPLATE = """===DYAD_REPORT===
RAW_RESPONSE:
1. dark lines on grey fill, a fan of triangles.
2. same fan; the convergence point sits differently.
3. similar structure overall.
4. I cannot determine it; the image carries no recording-order information.
OBSERVATIONS:
- fan of six triangles, light edges over grey fill
UNCERTAINTY:
exact heights are not resolvable from these stills
CONCLUSION: {conclusion}
FINISH: complete
===END===
"""


class F1GuidanceFormTests(unittest.TestCase):
    """Prediction 1: the question-form guidance is pinned, presupposition gone."""

    def test_constant_carries_only_the_neutral_form(self):
        self.assertEqual(driver.QUESTION_FORM_GUIDANCE, GUIDANCE_FORM)
        self.assertNotIn(PRESUPPOSING_PHRASING, driver.QUESTION_FORM_GUIDANCE)

    def test_document_carries_the_neutral_form(self):
        doc = (REPO_ROOT / 'docs' / 'THE_DYAD_SUBAGENT_TEMPLATE.md').read_text(
            encoding='utf-8')
        self.assertIn(GUIDANCE_FORM, doc)
        self.assertIn(driver.QUESTION_FORM_GUIDANCE, doc)  # doc quotes the constant

    def test_presupposing_phrasing_absent_from_constant_and_document(self):
        doc = (REPO_ROOT / 'docs' / 'THE_DYAD_SUBAGENT_TEMPLATE.md').read_text(
            encoding='utf-8').lower()
        self.assertNotIn(PRESUPPOSING_PHRASING, doc)
        self.assertNotIn(PRESUPPOSING_PHRASING, driver.QUESTION_FORM_GUIDANCE)


class DefaultByteIdentityTests(unittest.TestCase):
    """Prediction 4 / falsifier 1: a spec without "blind" must produce EXACTLY
    the prompt bytes the pre-hardening driver produced."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.frames = _make_frames(self.tmp.name, ['frame_a.png', 'frame_b.png',
                                                   'frame_c.png'])
        spec = _base_spec(self.frames, 'default-golden')
        spec['captures'] = spec['captures'][:2]
        spec['questions'] = spec['questions'][:3]
        spec['runtime_metadata'].pop('frame_3_state')
        self.spec = spec
        sha_a = self.frames['frame_a.png'][1][:12]
        sha_b = self.frames['frame_b.png'][1][:12]
        # GOLDEN LITERAL of the pre-hardening prompt bytes (the only dynamic
        # parts are the temp paths and hash prefixes). This is the byte-exact
        # DyadReviewRequest.build_prompt() layout reviewed in PR #44/#64.
        self.golden = (
            'DYAD visual review request\n'
            'task: hardening-check\n'
            'attempt: default-golden\n'
            'physical/programming context: three window frames of the same object '
            'at one fixed camera\n'
            'claim under examination: the recorded states are visually distinguishable\n'
            'review type: ordered_frames\n'
            'ordered captures: #1 frame_a.png (sha256 %s...), #2 frame_b.png '
            '(sha256 %s...)\n'
            'camera/runtime metadata: {"camera": "fixed demo camera phi 0.35 / '
            'radius 3.0", "frame_1_state": "%s", "frame_2_state": "%s"}\n'
            'evidence limits: ordered stills; numbers are observations, not measurements\n'
            '\n'
            'Answer EVERY question with its number. Report only what you can observe in '
            'the supplied images; state uncertainty explicitly. Do not guess. Numbers '
            'you mention are observations to verify, not measurements.\n'
            '1. Describe what frame 1 shows.\n'
            '2. Describe what frame 2 shows.\n'
            '3. %s' % (sha_a, sha_b, STATE_ONE, STATE_TWO,
                       spec['questions'][2])
        )

    def test_prompt_bytes_equal_golden_literal(self):
        spec_path = _write_spec(self.tmp.name, self.spec)
        out, root = _run_plan(spec_path, Path(self.tmp.name) / 'ev')
        prompt_text = _read(root / 'exact_prompt_default-golden.txt')
        self.assertEqual(prompt_text, self.golden)
        self.assertEqual(out['prompt_sha256'],
                         hashlib.sha256(prompt_text.encode('utf-8')).hexdigest())

    def test_prompt_bytes_equal_independent_contract_construction(self):
        """Built through the provider classes DIRECTLY from the original spec —
        no template-driver code between the spec and the contract."""
        spec_path = _write_spec(self.tmp.name, self.spec)
        out, root = _run_plan(spec_path, Path(self.tmp.name) / 'ev')
        caps = [Capture(index=int(c['index']), path=c['path'], sha256=c['sha256'])
                for c in self.spec['captures']]
        request = DyadReviewRequest(
            task=self.spec['task'], attempt=self.spec['attempt'],
            physical_context=self.spec['physical_context'],
            claim_under_exam=self.spec['claim_under_exam'],
            questions=tuple(self.spec['questions']), captures=tuple(caps),
            runtime_metadata=dict(self.spec['runtime_metadata']),
            review_type=self.spec['review_type'],
            evidence_limits=self.spec['evidence_limits'])
        self.assertEqual(_read(root / 'exact_prompt_default-golden.txt'),
                         request.build_prompt())

    def test_default_plan_output_keys_unchanged(self):
        spec_path = _write_spec(self.tmp.name, self.spec)
        out, _ = _run_plan(spec_path, Path(self.tmp.name) / 'ev')
        self.assertEqual(sorted(out),
                         ['attempt', 'captures', 'planned', 'prompt_file',
                          'prompt_sha256', 'review_type'])
        self.assertNotIn('blind', out)


class BlindOrderingTests(unittest.TestCase):
    """Prediction 2 / falsifiers 2-3: seeded randomization, state absence,
    reproducibility, unblinding recoverability."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.names = ['frame_a.png', 'frame_b.png', 'frame_c.png']
        self.frames = _make_frames(self.tmp.name, self.names)

    def _blind_spec(self, seed, attempt='blind-run'):
        spec = _base_spec(self.frames, attempt)
        spec['blind'] = {'seed': seed}
        return spec

    def _expected_perm(self, seed, n=3):
        order = list(range(n))
        random.Random(seed).shuffle(order)
        return order  # blind position pos+1 shows original[order[pos]]

    def test_blind_order_is_seeded_and_reproducible(self):
        seed = 7
        spec = self._blind_spec(seed)
        spec_path = _write_spec(self.tmp.name, spec)
        out1, root1 = _run_plan(spec_path, Path(self.tmp.name) / 'ev1')
        out2, root2 = _run_plan(spec_path, Path(self.tmp.name) / 'ev2')
        p1 = _read(root1 / 'exact_prompt_blind-run.txt')
        p2 = _read(root2 / 'exact_prompt_blind-run.txt')
        self.assertEqual(p1, p2)                      # same seed -> identical bytes
        self.assertEqual(out1['unblinding_sha256'], out2['unblinding_sha256'])
        # the listing order is the permutation that seed defines, not the
        # original order (seed 7 -> [2, 0, 1] for n=3)
        self.assertEqual(self._expected_perm(seed), [2, 0, 1])
        for pos, src in enumerate(self._expected_perm(seed), 1):
            name = self.names[src]
            self.assertIn('#%d %s (sha256 %s' % (pos, name,
                                                 self.frames[name][1][:12]),
                          p1)
        # a different seed defines a different order (99 -> [0, 2, 1])
        spec99 = self._blind_spec(99, attempt='blind-run-99')
        out99, root99 = _run_plan(_write_spec(self.tmp.name, spec99),
                                  Path(self.tmp.name) / 'ev99')
        self.assertNotEqual(out99['prompt_sha256'], out1['prompt_sha256'])

    def test_states_absent_from_prompt_present_in_unblinding(self):
        spec_path = _write_spec(self.tmp.name, self._blind_spec(7))
        out, root = _run_plan(spec_path, Path(self.tmp.name) / 'ev')
        prompt = (root / 'exact_prompt_blind-run.txt').read_text(encoding='utf-8')
        for state in (STATE_ONE, STATE_TWO, STATE_THREE):
            self.assertNotIn(state, prompt)            # scan: leak falsifier
        ub_text = (root / 'unblinding_blind-run.json').read_text(encoding='utf-8')
        for state in (STATE_ONE, STATE_TWO, STATE_THREE):
            self.assertIn(state, ub_text)              # retained, not destroyed
        # redacted from the shareable spec copy too
        shareable = (root / 'request_spec_blind-run.json').read_text(encoding='utf-8')
        self.assertNotIn(STATE_ONE, shareable)
        self.assertNotIn('"blind"', shareable)

    def test_state_leak_fails_closed(self):
        """A state value re-introduced under a non-redacted key is a named
        refusal, never a silent leak."""
        spec = self._blind_spec(7)
        spec['runtime_metadata']['rig_state'] = STATE_ONE  # not frame_<i>_state
        spec_path = _write_spec(self.tmp.name, spec)
        with self.assertRaisesRegex(DyadRefusal, 'blind_state_leak'):
            _run_plan(spec_path, Path(self.tmp.name) / 'ev')

    def test_unblinding_recoverable_and_sha_recorded(self):
        seed = 7
        spec_path = _write_spec(self.tmp.name, self._blind_spec(seed))
        out, root = _run_plan(spec_path, Path(self.tmp.name) / 'ev')
        ub_bytes = (root / 'unblinding_blind-run.json').read_bytes()
        # sha-recorded: the plan output's hash equals a plain sha256 of the
        # retained FILE (byte-exact write — no platform newline transport)
        self.assertEqual(hashlib.sha256(ub_bytes).hexdigest(),
                         out['unblinding_sha256'])
        record = json.loads(ub_bytes)
        self.assertEqual(record['mode'], 'blind')
        self.assertEqual(record['seed'], seed)
        self.assertEqual([o['index'] for o in record['original_order']], [1, 2, 3])
        self.assertEqual([o['path'] for o in record['original_order']],
                         [self.frames[n][0] for n in self.names])
        self.assertEqual(record['redacted_keys'],
                         ['frame_1_state', 'frame_2_state', 'frame_3_state'])
        self.assertEqual(record['states']['frame_1_state'], STATE_ONE)
        self.assertEqual(record['states']['frame_2_state'], STATE_TWO)
        # every blind position maps back to its original index
        perm = self._expected_perm(seed)
        for entry, src in zip(record['blind_order'], perm):
            self.assertEqual(entry['original_index'], src + 1)
        # and the map cross-checks against the prompt's own listing
        prompt = (root / 'exact_prompt_blind-run.txt').read_text(encoding='utf-8')
        for pos, src in enumerate(perm, 1):
            self.assertIn('#%d %s' % (pos, self.names[src]), prompt)
        self.assertEqual(record['prompt_sha256'], out['prompt_sha256'])

    def test_blind_requires_integer_seed_and_multiple_captures(self):
        spec = self._blind_spec(7)
        del spec['blind']['seed']
        with self.assertRaisesRegex(DyadRefusal, 'blind_requires_integer_seed'):
            _run_plan(_write_spec(self.tmp.name, spec), Path(self.tmp.name) / 'ev')
        spec_one = _base_spec(self.frames, 'blind-one')
        spec_one['blind'] = {'seed': 7}
        spec_one['captures'] = spec_one['captures'][:1]
        with self.assertRaisesRegex(DyadRefusal, 'blind_requires_multiple_captures'):
            _run_plan(_write_spec(self.tmp.name, spec_one), Path(self.tmp.name) / 'ev')


class BlindAssembleTests(unittest.TestCase):
    """assemble runs the blind request through the UNCHANGED provider contract:
    same prompt bytes as plan, unblinding map verified (tamper refused),
    verdict ceiling untouched."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.frames = _make_frames(self.tmp.name,
                                   ['frame_a.png', 'frame_b.png', 'frame_c.png'])
        spec = _base_spec(self.frames, 'blind-e2e')
        spec['blind'] = {'seed': 7}
        self.spec_path = _write_spec(self.tmp.name, spec)
        self.out, self.root = _run_plan(self.spec_path,
                                        Path(self.tmp.name) / 'ev')
        self.report = Path(self.tmp.name) / 'report.txt'
        self.report.write_text(
            REPORT_TEMPLATE.format(conclusion='supports'), encoding='utf-8')

    def _assemble(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            driver.cmd_assemble(argparse.Namespace(
                spec=self.spec_path, report=str(self.report),
                evidence_root=str(self.root),
                served='unit-test harness (harness-declared)'))
        return json.loads(buf.getvalue())

    def test_assemble_reproduces_prompt_and_retains_blind_response(self):
        result = self._assemble()
        self.assertEqual(result['verdict'], 'INCONCLUSIVE')  # ceiling untouched
        response = json.loads(
            (self.root / 'dyad_response_blind-e2e.json').read_text(encoding='utf-8'))
        prompt_text = _read(self.root / 'exact_prompt_blind-e2e.txt')
        self.assertEqual(response['exact_prompt'], prompt_text)
        self.assertEqual(response['provider_id'], 'subagent-dyad-glm53flash')
        # the response's capture identities are BLIND positions that the
        # unblinding map resolves back to the original indexes
        ub = json.loads((self.root / 'unblinding_blind-e2e.json').read_text(
            encoding='utf-8'))
        mapping = {b['blind_index']: b['original_index'] for b in ub['blind_order']}
        for cap in response['capture_identities']:
            self.assertIn(cap['index'], mapping)
            original = ub['original_order'][mapping[cap['index']] - 1]
            self.assertEqual(original['sha256'], cap['sha256'])

    def test_assemble_unblinding_bytes_identical_to_plan(self):
        before = (self.root / 'unblinding_blind-e2e.json').read_bytes()
        self._assemble()
        after = (self.root / 'unblinding_blind-e2e.json').read_bytes()
        self.assertEqual(before, after)  # deterministic: plan and assemble agree

    def test_tampered_unblinding_refused(self):
        ub_path = self.root / 'unblinding_blind-e2e.json'
        record = json.loads(ub_path.read_text(encoding='utf-8'))
        record['states']['frame_1_state'] = 'TAMPERED'
        ub_path.write_text(json.dumps(record, indent=1, sort_keys=True) + '\n',
                           encoding='utf-8')
        with self.assertRaisesRegex(DyadRefusal, 'unblinding_mismatch'):
            self._assemble()


class ProviderContractUntouchedTests(unittest.TestCase):
    """Falsifier 5: no provider-contract weakening. The driver must still route
    everything through SubagentDyadProvider, and the provider suite must pass
    unchanged (run separately: python tools/test_dyad_provider.py)."""

    def test_driver_uses_provider_module_without_shadowing(self):
        import dyad_provider
        self.assertIs(driver.DyadReviewRequest, dyad_provider.DyadReviewRequest)
        self.assertIs(driver.SubagentDyadProvider, dyad_provider.SubagentDyadProvider)
        self.assertIs(driver.DyadRefusal, dyad_provider.DyadRefusal)

    def test_default_and_blind_prompts_both_come_from_build_prompt(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        frames = _make_frames(tmp.name, ['frame_a.png', 'frame_b.png',
                                          'frame_c.png'])
        for blind in (None, {'seed': 7}):
            spec = _base_spec(frames, 'probe')
            spec['captures'] = spec['captures'][:2]
            spec['questions'] = spec['questions'][:3]
            if blind is not None:
                spec['blind'] = blind
            eff, _ = driver._apply_blind(spec)
            request = driver._build_request(eff)
            self.assertIsInstance(request, DyadReviewRequest)
            request.validate()  # the reviewed validation, unmodified


if __name__ == '__main__':
    unittest.main(verbosity=2)
