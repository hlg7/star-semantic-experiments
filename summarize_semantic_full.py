"""Verify and aggregate frozen v3 scores. No model inference; errors are never zeros."""
import argparse
import csv
import hashlib
import json
from collections import Counter,defaultdict
from pathlib import Path
from semantic_scoring import judge,parse_qwen,geometry

def read(p):return json.loads(p.read_text())
def mean(xs):return sum(xs)/len(xs) if xs else None

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--raw-root',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    repo=Path(__file__).resolve().parent;v3=repo/'data/semantic_eval_v3';freeze=read(v3/'freeze.json')
    for p,h in freeze['sha256'].items():assert hashlib.sha256((repo/p).read_bytes()).hexdigest()==h,p
    checks={r['input_id']:r for r in read(v3/'checks.json')['records']};sample=read(v3/'full_sample.json')['rows'];byname={r['name']:r for r in sample}
    original={r['name']:r for r in (json.loads(x) for x in (repo/'reports/2026-09-06/metrics.jsonl').read_text().splitlines())}
    config=read(repo/'data/semantic_eval_v1/calibration.json');records=[];manifests={}
    assert len(byname)==6000
    for tool in ['grounding_dino','qwen_vlm']:
        path=a.raw_root/tool;m=read(path/'manifest.json');manifests[tool]=m
        assert m['scope']=='primary_only' and m['split']=='full' and m['limit'] is None and m['config']==config
        for p,h in m['hashes'].items():
            local=repo/Path(p).name if Path(p).is_absolute() else repo/p
            assert hashlib.sha256(local.read_bytes()).hexdigest()==h,p
        expected={r['name'] for r in sample if checks[r['input_id']]['primary_evaluator'].startswith(tool)}
        assert {p.stem for p in (path/'predictions').glob('*.json')}==expected
        assert set(m['png_sha256'])==expected
        for name in sorted(expected):
            s=byname[name];c=checks[s['input_id']];o=original[name];q=read(path/'predictions'/(name+'.json'))
            assert q['name']==name
            for k in ['input_id','seed','masked_scales','aliases','image_sha256']:assert s[k]==o[k],(name,k)
            if q['status']=='evaluation_error':score={'status':'evaluation_error','success':None,'absolute_error':None};obs=None
            else:
                assert q['input_id']==s['input_id'] and q['image_sha256']==s['image_sha256']
                if tool=='qwen_vlm':
                    score=parse_qwen(q['raw'],c);obs=json.loads(q['raw'])
                else:
                    boxes=[r['retained_boxes'] for r in q['raw']]
                    if c['semantic']=='object':obs={'status':'ok','answer':bool(boxes[0])}
                    elif c['semantic']=='count':obs={'status':'ok','answer':len(boxes[0])}
                    else:
                        axis='x' if c['subtype']=='left_right' else 'y'
                        obs=geometry(boxes,axis,config['geometry']['epsilon_'+axis],256)
                    score=judge(obs,c)
                assert all(q[k]==value for k,value in score.items()),name
            records.append({**s,'semantic':c['semantic'],'subtype':c['subtype'],'scene_family':c['scene_family'],'baseline_name':o['baseline_name'],
                'primary_evaluator':c['primary_evaluator'],'observation':obs,**score,'png_sha256':m['png_sha256'][name],
                'expected':c['scoring_only']['expected_answer'],'raw_prediction':q})
    assert len(records)==6000
    byname={r['name']:r for r in records};errors=[]
    for r in records:
        b=byname[r['baseline_name']];assert b['input_id']==r['input_id'] and b['seed']==r['seed'] and not b['masked_scales']
        r['baseline_success']=b['success'];r['paired_delta']=r['success']-b['success'] if r['success'] is not None and b['success'] is not None else None
        if r['status']=='evaluation_error':errors.append({'name':r['name'],'semantic':r['semantic'],'aliases':r['aliases'],'error':r['raw_prediction']['error'],'raw':r['raw_prediction']['raw']})
    def summarize(rs):
        valid=[r for r in rs if r['success'] is not None];pairs=[r for r in valid if r['paired_delta'] is not None];positive=[r for r in pairs if r['baseline_success']==1]
        return {'n_total':len(rs),'n_valid':len(valid),'n_errors':len(rs)-len(valid),'n_pairs':len(pairs),'success_rate':mean([r['success'] for r in valid]),
          'paired_delta':mean([r['paired_delta'] for r in pairs]),'gained_success_n':sum(r['paired_delta']==1 for r in pairs),'lost_success_n':sum(r['paired_delta']==-1 for r in pairs),'paired_baseline_rate':mean([r['baseline_success'] for r in pairs]),
          'uncertain_rate':mean([int(r['status'] in ['unclear','ambiguous']) for r in valid]),'missing_rate':mean([int(r['status']=='missing') for r in valid]),
          'baseline_correct_n':len(positive),'retention':mean([r['success'] for r in positive]),
          'count_mae':mean([r['absolute_error'] for r in valid if r['absolute_error'] is not None]),
          'count_numeric_n':sum(r['absolute_error'] is not None for r in valid),'statuses':dict(Counter(r['status'] for r in rs))}
    groups=defaultdict(list)
    for r in records:
        for alias in r['aliases']:
            d,k=alias['direction'],alias['boundary'];assert d in ['prefix','suffix'] and 0<=k<=10
            masked=list(range(1,k+1)) if d=='prefix' else list(range(k+1,11));assert r['masked_scales']==masked,(r['name'],alias)
            groups[r['semantic'],'all',d,k].append(r);groups[r['semantic'],r['subtype'],d,k].append(r)
    curves=[]
    for (sem,sub,d,k),rs in sorted(groups.items()):
        assert len({r['input_id'] for r in rs})==len(rs)
        if sub=='all':assert len(rs)==50
        curves.append({'semantic':sem,'subtype':sub,'direction':d,'boundary':k,**summarize(rs)})
    summary={}
    for sem in sorted({r['semantic'] for r in records}):
        summary[sem]={'all_conditions':summarize([r for r in records if r['semantic']==sem]),'baseline':summarize(groups[sem,'all','prefix',0]),'full_mask':summarize(groups[sem,'all','prefix',10])}
        for left,right in [(('prefix',0),('suffix',10)),(('prefix',10),('suffix',0))]:assert {r['name'] for r in groups[(sem,'all')+left]}=={r['name'] for r in groups[(sem,'all')+right]}
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'metrics.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in sorted(records,key=lambda r:r['name'])))
    payload={'status':'complete_with_explicit_errors' if errors else 'complete','scientific_status':'exploratory_not_validated_accuracy','n_records':len(records),'n_valid':len(records)-len(errors),'errors':errors,'summary':summary,'curves':curves,'freeze':freeze,'manifests':manifests}
    (a.output/'summary.json').write_text(json.dumps(payload,indent=2)+'\n')
    table=[{k:(json.dumps(v,sort_keys=True) if isinstance(v,dict) else v) for k,v in r.items()} for r in curves]
    with (a.output/'curve_data.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(table[0]),lineterminator="\n");w.writeheader();w.writerows(table)
    print(json.dumps({'n_records':len(records),'n_valid':len(records)-len(errors),'errors':errors,'endpoints':{s:{k:{x:v[k][x] for x in ['success_rate','n_valid','uncertain_rate']} for k in ['baseline','full_mask']} for s,v in summary.items()}},indent=2))
if __name__=='__main__':main()
