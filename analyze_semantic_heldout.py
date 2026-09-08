"""Analyze frozen AI review against fixed held-out evaluators; no model imports."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from semantic_scoring import judge, parse_qwen, geometry


def read(p):
    return json.loads(p.read_text())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();repo=Path(__file__).resolve().parent
    protocol=repo/'data/semantic_eval_v2/validation'
    frozen=read(protocol/'freeze.json');plan=read(protocol/'plan.json')
    for p,h in frozen['sha256'].items():
        assert hashlib.sha256((repo/p).read_bytes()).hexdigest()==h,p
    label_freeze=read(a.review_root/'labels.freeze.json')
    assert hashlib.sha256((a.review_root/'ai_labels.reviewed.json').read_bytes()).hexdigest()==label_freeze['sha256']
    labels={r['blind_id']:r for r in read(a.review_root/'ai_labels.reviewed.json')['rows']}
    sample=[r for r in read(repo/'data/semantic_eval_v1/pilot/sample.json')['rows'] if r['split']=='held_out']
    assert set(labels)=={r['blind_id'] for r in sample} and len(sample)==240
    checks={r['input_id']:r for r in read(repo/'data/semantic_eval_v2/checks.json')['records']}
    config=read(repo/'data/semantic_eval_v1/calibration.json');manifests={}
    for tool in ['dino','qwen']:
        path=a.review_root/tool;manifest=read(path/'manifest.json');manifests[tool]=manifest
        assert manifest['split']=='held_out' and manifest['limit'] is None
        assert manifest['config']==config
        for p,h in manifest['hashes'].items():
            local=repo/p if not Path(p).is_absolute() else repo/Path(p).name
            assert hashlib.sha256(local.read_bytes()).hexdigest()==h,p
        assert {p.stem for p in (path/'predictions').glob('*.json')}=={r['name'] for r in sample}
    assert manifests['dino']['png_sha256']==manifests['qwen']['png_sha256']
    rows=[]
    for s in sample:
        c=checks[s['input_id']];ref=labels[s['blind_id']];refscore=judge(ref,c)
        d=read(a.review_root/'dino/predictions'/(s['name']+'.json'))
        q=read(a.review_root/'qwen/predictions'/(s['name']+'.json'))
        assert q['status']!='evaluation_error' and d['status']!='evaluation_error'
        qs=parse_qwen(q['raw'],c);assert all(q[k]==v for k,v in qs.items())
        qo=json.loads(q['raw'])
        if c['semantic']=='count' and isinstance(qo['answer'],str):qo['answer']=int(qo['answer'])
        if c['primary_evaluator'].startswith('grounding_dino'):
            if c['semantic']=='object':obs={'status':'ok','answer':bool(d['raw'][0]['retained_boxes'])}
            elif c['semantic']=='count':obs={'status':'ok','answer':len(d['raw'][0]['retained_boxes'])}
            else:
                axis='x' if c['subtype']=='left_right' else 'y'
                obs=geometry([x['retained_boxes'] for x in d['raw']],axis,config['geometry']['epsilon_'+axis],256)
            score=judge(obs,c);assert all(d[k]==v for k,v in score.items())
        else:obs=qo;score=qs
        clear=ref['status'] not in ['unclear','ambiguous']
        match=obs['status']==ref['status'] and type(obs['answer']) is type(ref['answer']) and obs['answer']==ref['answer']
        rows.append({**s,'semantic':c['semantic'],'subtype':c['subtype'],'primary_evaluator':c['primary_evaluator'],
          'reference':ref,'reference_success':refscore['success'],'review_clear':clear,'primary_observation':obs,
          'primary_score':score,'binary_agreement':score['success']==refscore['success'],'answer_agreement':match,
          'count_error_to_review':abs(obs['answer']-ref['answer']) if c['semantic']=='count' and clear and type(obs['answer']) is int and type(ref['answer']) is int else None,
          'qwen':q,'dino':d})
    gates=plan['screening_criteria']
    def summarize(rs):
        clear=[r for r in rs if r['review_clear']];pos=[r for r in clear if r['reference_success']==1];neg=[r for r in clear if r['reference_success']==0]
        ratio=lambda n,d:n/d if d else None
        binary=sum(r['binary_agreement'] for r in clear);answers=sum(r['answer_agreement'] for r in clear)
        fp=sum(r['primary_score']['success']==1 for r in neg);fn=sum(r['primary_score']['success']==0 for r in pos)
        unknown=sum(r['primary_score']['status'] in ['ambiguous','unclear'] for r in rs)
        errs=[r['count_error_to_review'] for r in rs if r['count_error_to_review'] is not None]
        result={'n':len(rs),'clear_n':len(clear),'clear_prompts':len({r['input_id'] for r in clear}),
          'review_statuses':dict(Counter(r['reference']['status'] for r in rs)),
          'primary_statuses':dict(Counter(r['primary_score']['status'] for r in rs)),
          'binary_matches':binary,'binary_agreement':ratio(binary,len(clear)),
          'answer_matches':answers,'answer_agreement':ratio(answers,len(clear)),
          'false_successes':fp,'reference_failures':len(neg),'false_success_rate':ratio(fp,len(neg)),
          'false_failures':fn,'reference_successes':len(pos),'false_failure_rate':ratio(fn,len(pos)),
          'evaluator_uncertain_fraction':ratio(unknown,len(rs)),'count_mae_to_review':ratio(sum(errs),len(errs)),'count_numeric_coverage_n':len(errs)}
        checks_gate={'clear_images':len(clear)>=gates['minimum_clear_review_images'],
          'clear_prompts':result['clear_prompts']>=gates['minimum_clear_review_prompts'],
          'reference_success_denominator':len(pos)>=gates['minimum_review_success_images_for_false_failure_rate'],
          'reference_failure_denominator':len(neg)>=gates['minimum_review_failure_images_for_false_success_rate'],
          'binary_agreement':result['binary_agreement'] is not None and result['binary_agreement']>=gates['minimum_binary_agreement'],
          'answer_agreement':result['answer_agreement'] is not None and result['answer_agreement']>=gates['minimum_observed_answer_agreement'],
          'false_success_rate':result['false_success_rate'] is not None and result['false_success_rate']<=gates['maximum_false_success_rate_on_review_failures'],
          'false_failure_rate':result['false_failure_rate'] is not None and result['false_failure_rate']<=gates['maximum_false_failure_rate_on_review_successes'],
          'evaluator_uncertainty':result['evaluator_uncertain_fraction']<=gates['maximum_evaluator_uncertain_fraction']}
        result['gates']=checks_gate
        adequate=all(checks_gate[k] for k in ['clear_images','clear_prompts','reference_success_denominator','reference_failure_denominator'])
        result['decision']='pass_exploratory_screen' if all(checks_gate.values()) else ('fail_screen' if adequate else 'inconclusive_insufficient_reference_coverage')
        return result
    summary={s:summarize([r for r in rows if r['semantic']==s]) for s in sorted({r['semantic'] for r in rows})}
    subtypes={}
    for key in sorted({(r['semantic'],r['subtype']) for r in rows}):
        rs=[r for r in rows if (r['semantic'],r['subtype'])==key];ss=summarize(rs)
        ss.pop('gates');ss['decision']='descriptive_only';ss['minimum_10_clear_met']=ss['clear_n']>=10
        subtypes['/'.join(key)]=ss
    prompts={k:summarize([r for r in rows if r['input_id']==k]) for k in sorted({r['input_id'] for r in rows})}
    for p in prompts.values():p.pop('gates');p['decision']='descriptive_prompt_summary'
    payload={'caveat':'AI-reviewed exploratory held-out screen, not human validated accuracy. All labels frozen before model predictions were inspected. Four conditions per prompt are correlated. See frozen plan for limitations.','label_freeze':label_freeze,'protocol_freeze':frozen,'manifests':manifests,'summary':summary,'subtypes':subtypes,'per_prompt':prompts,'rows':rows}
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'comparison.json').write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
