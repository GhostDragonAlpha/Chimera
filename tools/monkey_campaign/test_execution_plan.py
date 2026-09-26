import copy
import json
from pathlib import Path
import unittest

from execution_plan import build_plan


class ExecutionPlanTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((Path(__file__).parent / 'monkey_completion_map.json').read_text(encoding='utf-8-sig'))

    def test_all_acceptance_and_calculation_contracts_preserved(self):
        before = copy.deepcopy(self.catalog)
        result = build_plan(self.catalog)
        self.assertEqual(self.catalog, before)
        self.assertEqual(result['task_count'], 83)
        self.assertEqual(result['selected_count'], 76)
        packets = {p['id']: p for p in result['tasks']}
        calculations = {c['id']: c for c in self.catalog['calculations']}
        for source in self.catalog['tasks']:
            packet = packets[source['id']]
            for field, value in source.items():
                self.assertEqual(packet[field], value)
            self.assertEqual(packet['calculation_contracts'], [calculations[c] for c in source['calculation_ids']])
            self.assertEqual([p['id'] for p in packet['phases']], ['reconcile', 'decide', 'implement', 'verify', 'runtime', 'visual', 'review', 'integrate'])
            self.assertFalse(packet['assignment_authorized'])
        inactive = [p for p in packets.values() if not p['selected']]
        self.assertEqual(len(inactive), 7)
        self.assertTrue(all(p['initial_state'] == 'CONDITIONAL_INACTIVE' for p in inactive))
        self.assertFalse(result['goal_complete'])

    def test_deterministic_and_no_automatic_decisions(self):
        first = build_plan(self.catalog)
        self.assertEqual(first, build_plan(self.catalog))
        for task in first['tasks']:
            self.assertEqual(task['phases'][1]['required'], 'decision' in task['kind'].split('+'))

    def test_missing_calculation_contract_refused(self):
        self.catalog['calculations'].pop(0)
        with self.assertRaisesRegex(ValueError, 'unknown_calculation'):
            build_plan(self.catalog)

    def test_missing_acceptance_and_graph_cycle_refused(self):
        broken = copy.deepcopy(self.catalog)
        broken['tasks'][0]['done_when'] = ''
        with self.assertRaisesRegex(ValueError, 'missing_acceptance'):
            build_plan(broken)
        self.catalog['tasks'][0]['depends_on'] = [self.catalog['tasks'][0]['id']]
        with self.assertRaisesRegex(ValueError, 'dependency_cycle'):
            build_plan(self.catalog)


if __name__ == '__main__':
    unittest.main()
