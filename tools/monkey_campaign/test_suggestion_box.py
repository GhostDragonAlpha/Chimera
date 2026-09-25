from concurrent.futures import ThreadPoolExecutor
import tempfile
import unittest
from unittest.mock import patch

from suggestion_box import SuggestionBox


def question(i=0):
    return dict(agent_id=f'worker-{i}', task_id=f'task-{i}', subject='Frame clarification',
                question='Which declared frame owns this quantity?', evidence_reference='fixture only',
                attempts='Read the contract; found two conflicting declarations.',
                recommendation='Use the authored frame, pending lead review.', instruction_revision='astra-0001', blocking=True)


class SuggestionBoxTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.box = SuggestionBox(self.temp.name); self.box.initialize()

    def response(self, q, sequence=0):
        return dict(lead_id='astra-codex', question_id=q['question_id'], expected_question_sha256=q['question_sha256'],
                    expected_answer_sequence=sequence, status='ANSWERED', answer='Use the declared frame in fixture A.',
                    reason='Fixture reference establishes it.', next_action='Run the scoped frame regression.',
                    evidence_reference='fixture A', instruction_revision='astra-0001', user_message_reference='test operator turn')

    def test_concurrent_submissions_survive_and_exact_retry_is_idempotent(self):
        with ThreadPoolExecutor(max_workers=10) as pool:
            submitted = list(pool.map(lambda i: SuggestionBox(self.temp.name).submit(question(i)), range(10)))
        self.assertEqual(len({q['question_id'] for q in submitted}), 10)
        retry = self.box.submit(question())
        self.assertEqual(retry['question_id'], submitted[0]['question_id'])
        self.assertTrue(retry['exact_retry'])
        self.assertEqual(self.box.listing()['counts'], {'OPEN': 10})

    def test_answers_are_append_only_and_stale_or_wrong_inputs_refuse(self):
        q = self.box.submit(question()); response = self.response(q)
        for bad, error in [({'lead_id':'worker'}, 'designated_lead'),
                           ({'expected_question_sha256':'wrong'}, 'fingerprint'),
                           ({'expected_answer_sequence':1}, 'stale_answer')]:
            with self.assertRaisesRegex(ValueError, error): self.box.answer({**response, **bad})
        self.box.answer(response)
        with self.assertRaisesRegex(ValueError, 'stale_answer'): self.box.answer(response)
        self.box.answer({**self.response(q, 1), 'answer':'Addendum: fixture B confirms.', 'status':'NEEDS_EVIDENCE'})
        record = self.box.listing(pending=True)['questions'][0]
        self.assertEqual(record['question'], question())
        self.assertEqual(len(record['answers']), 2)
        self.assertEqual(record['answers'][0]['answer'], response['answer'])

    def test_bounded_payload_and_queue_never_silently_discard(self):
        with self.assertRaisesRegex(ValueError, 'invalid_question'): self.box.submit({**question(), 'question':'x'*8001})
        with self.assertRaisesRegex(ValueError, 'invalid_blocking'): self.box.submit({**question(), 'blocking':'yes'})
        with patch('suggestion_box.MAX_PENDING', 1):
            q = self.box.submit(question())
            with self.assertRaisesRegex(ValueError, 'capacity'): self.box.submit(question(1))
            self.assertTrue(self.box.submit(question())['exact_retry'])
        self.box.answer(self.response(q))
        self.assertEqual(self.box.listing(pending=True)['questions'], [])
        self.assertEqual(self.box.listing()['counts'], {'ANSWERED':1})

    def test_review_requires_user_turn_reference_and_does_not_answer_questions(self):
        q = self.box.submit(question())
        data = dict(lead_id='astra-codex', summary='Read pending question.', reviewed_question_ids=[q['question_id']])
        with self.assertRaisesRegex(ValueError, 'user_message_reference'): self.box.record_review(data)
        review = self.box.record_review({**data, 'user_message_reference':'operator turn at test time'})
        self.assertEqual(review['trigger'], 'operator_message_only')
        self.assertEqual(self.box.listing()['counts'], {'OPEN':1})
        self.assertEqual(self.box.initialize()['last_lead_review'], review)

    def test_concurrent_answers_cannot_overwrite(self):
        q = self.box.submit(question())
        def answer(_):
            try: return SuggestionBox(self.temp.name).answer(self.response(q))
            except ValueError as exc: return str(exc)
        with ThreadPoolExecutor(max_workers=2) as pool: results = list(pool.map(answer, range(2)))
        self.assertEqual(sum(isinstance(r, dict) for r in results), 1)
        self.assertIn('stale_answer_sequence', results)
        self.assertEqual(len(self.box.listing()['questions'][0]['answers']), 1)


if __name__ == '__main__': unittest.main(verbosity=2)
