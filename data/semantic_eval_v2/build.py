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
SYSTEM = (
    'Judge visible evidence only. The question names an object to search for; it does not establish its presence. '
    'First identify the requested object independently of the attribute being tested. Do not substitute another object '
    'because its color, shape, pattern or position fits a possible answer. '
    'For attribute/relation tasks require exactly one identifiable instance of each named object. '
    'Multiple eligible instances are ambiguous even if their attributes agree; do not pick the most favorable instance. '
    'Use identity_status=present only when all required objects are present and uniquely identifiable; '
    'otherwise use missing, ambiguous, or unclear. '
    'For presence/count tasks, identity_status may be present, absent, or unclear; multiple objects are allowed. '
    'Count physical instances over the entire image, including recognizable partial instances and background instances, '
    'but not reflections or depictions. If an exact count cannot be established use unclear, not a guessed count. '
    'Do not infer attributes from object stereotypes. '
    'Return JSON only with keys identity_status, status, answer, evidence. '
    'status must be ok, missing, ambiguous, or unclear. For status=ok, answer must be a non-null allowed answer. '
    'For other statuses answer must be null. For attribute/relation tasks a non-present identity_status must equal status. '
    'Confirmed absence is status=ok with answer=false for presence, or answer=0 for count. '
    'Counts must be JSON integers. Evidence must briefly describe the visible object and relevant property.'
)

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
            question = f'After confirming the identity of the {obj}, what is its overall boundary shape, excluding patterns, holes, parts and shadows? Use the object shape when perspective is identifiable; otherwise use unclear. Round means circular rather than merely curved; oval means elongated rounded outline; square and non-square rectangular are separate. Do not substitute a face of a different 3D object.'
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
                question = f'Is the {a} inside, outside, or partially inserted into the interior space of the {b}? Inside means seated or contained in the interior; extension above an opening does not by itself make it partial. Outside means not occupying the interior. Partial means crossing the opening without clear settled containment. Use unclear when the physical relation cannot be established. Bounding-box overlap alone is not containment.'
        if sem in ['object', 'count']:
            schema = ('For this task, identity_status must be present, absent, or unclear; '
                      'never missing or ambiguous. If the object is absent, use identity_status=absent, '
                      'status=ok, answer=' + ('false' if sem == 'object' else '0') + '. '
                      'If presence or exact enumeration cannot be resolved, use identity_status=unclear, '
                      'status=unclear, answer=null. Otherwise use identity_status=present, status=ok '
                      'and an allowed answer. Multiple instances do not make this task ambiguous.')
        else:
            schema = ('For this task, identity_status must be present, missing, ambiguous, or unclear. '
                      'For a non-present identity use the same status and answer=null. '
                      'With present identity, an unresolved property may use status=unclear, answer=null; '
                      'otherwise use status=ok and an allowed answer.')
        question += ' Response schema for this task: ' + schema
        records.append({
            'input_id': r['id'], 'semantic': sem, 'subtype': r['subtype'], 'scene_family': r['scene_family'],
            'primary_evaluator': primary, 'protocol_version': 'semantic_eval_v2',
            'require_identity_status': True, 'instance_policy': selection,
            'evaluator_input': {'detector_queries': objects, 'qwen_system': SYSTEM,
                                'qwen_question': question, 'response_schema': schema, 'allowed_answers': answers},
            'scoring_only': {'expected_answer': expected, 'source_target_text': target},
            'qwen_role': 'primary' if primary == 'qwen_vlm' else 'independent_audit_no_override'})
    assert len(records) == len({r['input_id'] for r in records}) == 300
    assert set(Counter(r['semantic'] for r in records).values()) == {50}
    payload = {'version': 'semantic_eval_v2_draft', 'status': 'not_calibrated_not_run',
               'source_sha256': hashlib.sha256(raw).hexdigest(), 'records': records}
    (HERE / 'checks.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n')
    lines = ['# Evaluation question review', '', 'Revised general protocol: v2 has not been run. Historical v1 pilot results are preserved separately.', '',
             '| ID | Primary | Objects | Expected (scorer only) | Question |', '|---|---|---|---|---|']
    for r in records:
        e = r['evaluator_input']
        lines.append(f"| {r['input_id']} | {r['primary_evaluator']} | {', '.join(e['detector_queries'])} | {r['scoring_only']['expected_answer']} | {e['qwen_question']} |")
    (HERE / 'review.md').write_text('\n'.join(lines) + '\n')
    print('Built 300 specifications; 50 per semantic. No inference.')

if __name__ == '__main__':
    build()
