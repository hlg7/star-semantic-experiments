"""Select development/held-out images from committed metadata, without inference."""
import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    root = Path(__file__).resolve().parent
    checks = json.loads((root/'data/semantic_eval_v1/checks.json').read_text())['records']
    metrics = [json.loads(x) for x in (root/'reports/2026-09-06/metrics.jsonl').read_text().splitlines()]
    rng = random.Random(20260908)
    selected = []
    for semantic in sorted({x['semantic'] for x in checks}):
        remaining = [x for x in checks if x['semantic'] == semantic]
        for split in ['development', 'held_out']:
            target_counts, scene_counts = Counter(), Counter()
            for _ in range(10):
                rng.shuffle(remaining)
                r = min(remaining, key=lambda x: (target_counts[str(x['scoring_only']['expected_answer'])], scene_counts[x['scene_family']]))
                remaining.remove(r)
                target_counts[str(r['scoring_only']['expected_answer'])] += 1
                scene_counts[r['scene_family']] += 1
                selected.append((split, r))
    rows = []
    for split, check in selected:
        matches = [r for r in metrics if r['input_id'] == check['input_id'] and r['masked_scales'] in [[], [1], [10], list(range(1, 11))]]
        assert len(matches) == 4
        for r in matches:
            rows.append({k: r[k] for k in ['name','input_id','image_sha256','seed','aliases','masked_scales']} | {'split': split})
    rng.shuffle(rows)
    for i, r in enumerate(rows): r['blind_id'] = f'image_{i+1:04d}'
    a.output.mkdir(parents=True, exist_ok=True)
    (a.output/'sample.json').write_text(json.dumps({'selection_seed':20260908,'method':'greedy target then scene coverage; no image/score selection','rows':rows},indent=2)+'\n')
    by_id = {r['input_id']: r for r in checks}
    annotations = [{'blind_id':r['blind_id'], 'question':by_id[r['input_id']]['evaluator_input']['qwen_question'],
                    'allowed_answers':by_id[r['input_id']]['evaluator_input']['allowed_answers'],
                    'status':None,'answer':None,'notes':''} for r in rows]
    (a.output/'human_labels.template.json').write_text(json.dumps(annotations,indent=2)+'\n')
    print('240 development + 240 held-out images; 120 disjoint prompts. Human labels blank.')

if __name__ == '__main__': main()
