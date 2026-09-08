import copy
import json
import unittest
from pathlib import Path
from semantic_scoring import parse_qwen

class GeneralRules(unittest.TestCase):
    def setUp(self):
        self.rows=json.loads(Path('data/semantic_eval_v2/checks.json').read_text())['records']
    def test_missing_identity_cannot_claim_shape_success(self):
        c=next(r for r in self.rows if r['semantic']=='shape')
        with self.assertRaises(ValueError):
            parse_qwen(json.dumps(dict(identity_status='missing',status='ok',answer='round')),c)
        self.assertEqual(parse_qwen(json.dumps(dict(identity_status='missing',status='missing',answer=None)),c)['success'],0)
    def test_unseen_noun_uses_same_rule(self):
        c=copy.deepcopy(next(r for r in self.rows if r['semantic']=='color'))
        c['input_id']='unseen_example';c['evaluator_input']['detector_queries']=['helmet']
        c['scoring_only']['expected_answer']='blue'
        self.assertEqual(parse_qwen(json.dumps(dict(identity_status='present',status='ok',answer='blue')),c)['success'],1)
        with self.assertRaises(ValueError):
            parse_qwen(json.dumps(dict(identity_status='ambiguous',status='ok',answer='blue')),c)
    def test_count_not_limited_to_prompt_range(self):
        c=next(r for r in self.rows if r['semantic']=='count')
        result=parse_qwen(json.dumps(dict(identity_status='present',status='ok',answer=17)),c)
        self.assertEqual(result['absolute_error'],15)
    def test_questions_do_not_reveal_expected_count(self):
        rows=[r for r in self.rows if r['semantic']=='count' and r['evaluator_input']['detector_queries']==['mug']]
        self.assertEqual(len({r['evaluator_input']['qwen_question'] for r in rows}),1)
    def test_identity_required_only_in_new_protocol(self):
        c=next(r for r in self.rows if r['semantic']=='shape')
        with self.assertRaises(ValueError):parse_qwen('{"status":"ok","answer":"round"}',c)

if __name__=='__main__':unittest.main()
