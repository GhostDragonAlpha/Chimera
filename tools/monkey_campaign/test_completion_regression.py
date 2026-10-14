import unittest
from test_campaign import fixture, run_plan


class CompletionRegression(unittest.TestCase):
    def test_integrated_tasks_do_not_prove_visual_or_human_acceptance(self):
        parts = fixture()
        for task in parts[1]['snapshot']['tasks'].values():
            task.update(state='INTEGRATED', integration={'commit': 'b'*40, 'evidence': 'receipt'})
        self.assertFalse(run_plan(parts)['goal_complete'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
