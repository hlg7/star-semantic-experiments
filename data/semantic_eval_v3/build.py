"""Freeze general lexical/attribute definitions for exploratory full-set scoring."""
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
DEFINITIONS={
 'notebook':'A paper notebook is a bound set of paper pages for writing. A laptop or notebook computer is excluded.',
 'plate':'A plate is a shallow individual eating or serving dish. A loaf pan, deep bowl, cutting board, table, or solid pyramid is not a plate. A rectangular plate may exist; shape alone does not establish identity.',
 'tray':'A tray is a separate portable flat serving carrier, usually with a rim or handles. A tabletop itself is not a tray.',
 'bowl':'A bowl is an open relatively deep dish for food or contents. Distinguish it from a flower vase and from a cooking or loaf pan by visible structure; use unclear if this is unresolved.',
 'vase':'A vase is an upright vessel intended to hold flowers, identifiable by its vessel structure. Do not assign vase versus bowl using the desired relative position.',
 'picture frame':'A picture frame is a physical border intended to hold a picture. A computer monitor, window frame or clock bezel is excluded.',
 'mirror':'A mirror is a reflective surface. An open doorway, window or empty architectural opening is excluded. When reflection versus opening cannot be established, use unclear.',
 'sign':'A sign is a physical signboard or plaque intended to display information. An architectural opening or pillar is excluded even if its outline fits an answer.',
 'remote control':'A remote control is a handheld device for operating equipment at a distance. A gamepad or console controller is excluded; unresolved device identity is unclear.',
 'pencil case':'A pencil case is a small container or pouch for writing implements. Do not substitute a computer, binder, or unidentified box.'}
COLOR=('For color, judge the dominant visible exterior material of the identified object. Include a permanently attached frame or body; '
       'exclude contents seen through transparent walls, empty openings, reflections and illumination. '
       'Use the tint of transparent material only when the tint itself is visible; colorless transparent material is other. '
       'If no single exterior color dominates, use multicolored. Do not use the expected color to select a part.')
SURFACE=('Judge the dominant visible surface area. Rough requires discernible grain, pits or irregularities; smooth requires a visibly even surface. '
         'Use mixed when both rough and smooth areas are substantial and neither dominates. Structural edges, shadows, material names, blur or sharpness alone are insufficient evidence.')

def build():
    source=HERE.parent/'semantic_eval_v2/checks.json'
    records=copy.deepcopy(json.loads(source.read_text())['records'])
    for r in records:
        e=r['evaluator_input'];nouns=e['detector_queries'][:]
        definitions=[DEFINITIONS[n] for n in nouns if n in DEFINITIONS]
        e['category_definitions']=definitions
        e['detector_queries']=['paper notebook' if n=='notebook' else n for n in nouns]
        e['detector_label_aliases']=[['paper notebook','notebook'] if n=='notebook' else [n] for n in nouns]
        e['qwen_system']+=' Category definitions for this task: '+' '.join(definitions) if definitions else ''
        if r['semantic']=='color':e['qwen_system']+=' '+COLOR
        if r['semantic']=='texture' and r['subtype']=='surface':e['qwen_system']+=' '+SURFACE
        r['protocol_version']='semantic_eval_v3_exploratory'
    payload={'version':'semantic_eval_v3_exploratory','status':'frozen_for_exploratory_full_scoring_not_validated',
             'parent_checks_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'records':records}
    (HERE/'checks.json').write_text(json.dumps(payload,indent=2)+'\n')
    metrics=[json.loads(x) for x in (ROOT/'reports/2026-09-06/metrics.jsonl').read_text().splitlines()]
    assert len(metrics)==6000 and len({x['name'] for x in metrics})==6000
    assert set(Counter(x['input_id'] for x in metrics).values())=={20}
    assert len({x['input_id'] for x in metrics})==300
    keys=['name','input_id','seed','masked_scales','aliases','image_sha256']
    rows=[{k:x[k] for k in keys}|{'split':'full'} for x in metrics]
    (HERE/'full_sample.json').write_text(json.dumps({'version':payload['version'],'source_metrics_sha256':hashlib.sha256((ROOT/'reports/2026-09-06/metrics.jsonl').read_bytes()).hexdigest(),'rows':rows},indent=2)+'\n')
    smoke_targets={'object':'notebook','color':'hourglass','shape':'plate','texture':'stone','count':'remote control','spatial_relation':'bowl'}
    ids=[]
    for sem,noun in smoke_targets.items():
        ids.append(next(r['input_id'] for r in records if r['semantic']==sem and (noun in r['evaluator_input']['detector_queries'] or noun=='notebook' and 'paper notebook' in r['evaluator_input']['detector_queries'])))
    smoke=[dict(r,split='smoke') for r in rows if r['input_id'] in ids and len(r['masked_scales']) in [0,10]]
    assert len(smoke)==12
    (HERE/'smoke_sample.json').write_text(json.dumps({'purpose':'Execution/schema check only, selected by task/noun before v3 results; not a semantic pass gate','rows':smoke},indent=2)+'\n')
    print('Built frozen exploratory specifications for 300 prompts / 6000 conditions; 12-image smoke sample.')

if __name__=='__main__':build()
