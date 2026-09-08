"""Build evaluation-only specifications; never loads models or changes prompts."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'csfm50_v1' / 'prompts.json'
COLORS = ['black', 'blue', 'brown', 'green', 'orange', 'pink', 'purple', 'red', 'white', 'yellow']
SHAPES = ['round', 'oval', 'square', 'rectangular', 'triangular']
NOUNS = dict(zip(
    ['baskets', 'books', 'bottles', 'bowls', 'flowerpots', 'hats', 'hourglasses', 'mugs', 'remote controls', 'toy cars'],
    ['basket', 'book', 'bottle', 'bowl', 'flowerpot', 'hat', 'hourglass', 'mug', 'remote control', 'toy car']))
NUMBERS = {'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5, 'Six': 6}
RELATIONS = {'to the left of': 'left', 'to the right of': 'right', 'above': 'above', 'below': 'below',
             'in front of': 'front', 'behind': 'behind', 'inside': 'inside', 'outside': 'outside'}
SYSTEM = ('Judge only visible evidence in this image. Do not infer an attribute from typical object properties. '
          'For attribute and relation questions, require a unique instance of each named object; otherwise return ambiguous. '
          'Return JSON only: {"status":"ok|missing|ambiguous|unclear", "answer":null, "evidence":"short visual observation"}. '
          'For ok, answer must be an allowed answer; otherwise answer must be null. '
          'Absence is a valid false answer to presence questions and a valid zero answer to count questions. '
          'Use unclear when visibility is insufficient; do not guess.')

def build():
    raw = SOURCE.read_bytes()
    prompts = json.loads(raw)
    records = []
    for r in prompts:
        sem, obj, target = r['semantic'], r['target_object'], r['target_text']
        objects = obj.split(' relative to ') if sem == 'spatial_relation' else [NOUNS[obj] if sem == 'count' else obj]
        primary = 'qwen_vlm'
        selection = 'unique_instance_required'
        if sem == 'object':
            primary, selection = 'grounding_dino', 'any_valid_instance'
            question, answers, expected = f'Is any {obj} visibly present?', [True, False], True
        elif sem == 'count':
            primary, selection = 'grounding_dino', 'all_visible_instances'
            question = f'How many distinct {obj} are visible? Count physical instances, not reflections or pictures of them.'
            answers, expected = 'nonnegative_integer', NUMBERS[target]
        elif sem == 'color':
            question = f'What is the main surface color of the {obj}? Ignore small decorations, highlights and shadows.'
            answers, expected = COLORS + ['other', 'multicolored'], target
        elif sem == 'shape':
            question = f'What is the overall outer shape of the {obj}, not its printed pattern? Allow ordinary perspective foreshortening only when the object shape is visually identifiable.'
            answers, expected = SHAPES + ['other'], target
        elif sem == 'texture':
            if target in ['rough', 'smooth']:
                question = f'Does the visible surface of the {obj} look rough, smooth, mixed, or other? Use visible surface detail, not material stereotypes.'
                answers = ['rough', 'smooth', 'mixed', 'other']
            else:
                question = f'What is the dominant visible surface pattern on the {obj}, not the background?'
                answers = ['striped', 'checkered', 'polka-dotted', 'plain', 'mixed', 'other']
            expected = target
        else:
            a, b = objects
            expected = RELATIONS[target]
            if expected in ['left', 'right']:
                primary = 'grounding_dino_geometry'
                answers = ['left', 'right', 'aligned']
                question = f'From the viewer perspective, is the {a} left of, right of, or horizontally aligned with the {b}?'
            elif expected in ['above', 'below']:
                primary = 'grounding_dino_geometry'
                answers = ['above', 'below', 'aligned']
                question = f'Is the {a} above, below, or vertically aligned with the {b} in the image?'
            elif expected in ['front', 'behind']:
                answers = ['front', 'behind', 'same_depth']
                question = f'Is the {a} in front of, behind, or at the same depth as the {b}? Use depth and occlusion evidence, not vertical image position alone.'
            else:
                answers = ['inside', 'outside', 'partial']
                question = f'Is the {a} inside, outside, or partially inserted into the interior space of the {b}? A protruding handle alone does not make an otherwise contained object partial. Bounding-box overlap alone is not containment.'
        records.append({
            'input_id': r['id'], 'semantic': sem, 'subtype': r['subtype'], 'scene_family': r['scene_family'],
            'primary_evaluator': primary, 'instance_policy': selection,
            'evaluator_input': {'detector_queries': objects, 'qwen_system': SYSTEM,
                                'qwen_question': question, 'allowed_answers': answers},
            'scoring_only': {'expected_answer': expected, 'source_target_text': target},
            'qwen_role': 'primary' if primary == 'qwen_vlm' else 'independent_audit_no_override'})
    assert len(records) == len({r['input_id'] for r in records}) == 300
    assert set(Counter(r['semantic'] for r in records).values()) == {50}
    payload = {'version': 'semantic_eval_v1_draft', 'status': 'not_calibrated_not_run',
               'source_sha256': hashlib.sha256(raw).hexdigest(), 'records': records}
    (HERE / 'checks.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n')
    lines = ['# Evaluation question review', '', 'Draft: no image scoring has been run.', '',
             '| ID | Primary | Objects | Expected (scorer only) | Question |', '|---|---|---|---|---|']
    for r in records:
        e = r['evaluator_input']
        lines.append(f"| {r['input_id']} | {r['primary_evaluator']} | {', '.join(e['detector_queries'])} | {r['scoring_only']['expected_answer']} | {e['qwen_question']} |")
    (HERE / 'review.md').write_text('\n'.join(lines) + '\n')
    print('Built 300 specifications; 50 per semantic. No inference.')

if __name__ == '__main__':
    build()
