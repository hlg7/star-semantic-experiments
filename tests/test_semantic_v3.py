import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class FullProtocol(unittest.TestCase):
    def setUp(self):
        self.checks=json.loads((ROOT/'data/semantic_eval_v3/checks.json').read_text())['records']
        self.rows=json.loads((ROOT/'data/semantic_eval_v3/full_sample.json').read_text())['rows']
    def test_exact_primary_partition(self):
        byid={r['input_id']:r for r in self.checks}
        d={r['name'] for r in self.rows if byid[r['input_id']]['primary_evaluator'].startswith('grounding_dino')}
        q={r['name'] for r in self.rows if byid[r['input_id']]['primary_evaluator']=='qwen_vlm'}
        self.assertFalse(d&q);self.assertEqual(len(d|q),6000)
    def test_parent_targets_preserved(self):
        parent={r['input_id']:r for r in json.loads((ROOT/'data/semantic_eval_v2/checks.json').read_text())['records']}
        for r in self.checks:
            self.assertEqual(r['scoring_only'],parent[r['input_id']]['scoring_only'])
            self.assertEqual(r['primary_evaluator'],parent[r['input_id']]['primary_evaluator'])
    def test_notebook_general_alias(self):
        matches=[r for r in self.checks if 'paper notebook' in r['evaluator_input']['detector_queries']]
        self.assertGreater(len(matches),1)
        for r in matches:
            e=r['evaluator_input'];i=e['detector_queries'].index('paper notebook')
            self.assertEqual(e['detector_label_aliases'][i],['paper notebook','notebook'])
            self.assertIn('laptop',e['qwen_system'])
    def test_twenty_conditions_each(self):
        from collections import Counter
        self.assertEqual(set(Counter(r['input_id'] for r in self.rows).values()),{20})
        self.assertEqual(len({r['name'] for r in self.rows}),6000)

if __name__=='__main__':unittest.main()
