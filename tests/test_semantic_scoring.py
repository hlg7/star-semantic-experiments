import json
import unittest
from pathlib import Path
from semantic_scoring import judge, parse_qwen, geometry

class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.records=json.loads(Path('data/semantic_eval_v1/checks.json').read_text())['records']
    def check(self,semantic): return next(r for r in self.records if r['semantic']==semantic)
    def test_count_error_and_boolean_rejected(self):
        c=self.check('count')
        self.assertEqual(judge({'status':'ok','answer':3},c)['absolute_error'],1)
        with self.assertRaises(ValueError):judge({'status':'ok','answer':True},c)
    def test_numeric_string_normalization(self):
        c=self.check('count')
        self.assertEqual(parse_qwen('{"status":"ok","answer":"4"}',c)['absolute_error'],2)
        for value in ['four','4 mugs','3.5','-1']:
            with self.assertRaises(ValueError):parse_qwen(json.dumps({'status':'ok','answer':value}),c)
    def test_ok_null_remains_error(self):
        with self.assertRaises(ValueError):parse_qwen('{"status":"ok","answer":null}',self.check('shape'))
    def test_unknown_not_numeric_mae(self):
        self.assertEqual(judge({'status':'unclear','answer':None},self.check('count')),{'status':'unclear','success':0,'absolute_error':None})
    def test_malformed_is_error(self):
        with self.assertRaises(ValueError):parse_qwen('probably red',self.check('color'))
        with self.assertRaises(ValueError):judge({'status':'missing','answer':'red'},self.check('color'))
    def test_geometry_direction_and_boundary(self):
        boxes=[[[0,0,10,10]],[[20,20,30,30]]]
        self.assertEqual(geometry(boxes,'x',.02,100)['answer'],'left')
        self.assertEqual(geometry(boxes,'y',.02,100)['answer'],'above')
        self.assertEqual(geometry(boxes,'x',.2,100)['answer'],'aligned')
        self.assertEqual(geometry([[],boxes[1]],'x',.02,100)['status'],'missing')
        self.assertEqual(geometry([boxes[0]*2,boxes[1]],'x',.02,100)['status'],'ambiguous')
    def test_samples_disjoint_and_matched(self):
        rows=json.loads(Path('data/semantic_eval_v1/pilot/sample.json').read_text())['rows']
        a={r['input_id'] for r in rows if r['split']=='development'}
        b={r['input_id'] for r in rows if r['split']=='held_out'}
        self.assertEqual((len(a),len(b),len(a&b)),(60,60,0))
        for identity in a|b:
            r=[x for x in rows if x['input_id']==identity]
            self.assertEqual(sorted(len(x['masked_scales']) for x in r),[0,1,1,10])

if __name__=='__main__':unittest.main()
