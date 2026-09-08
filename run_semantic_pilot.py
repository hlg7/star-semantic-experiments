"""CUDA-only pilot evaluator for existing, hash-verified images. One model per run."""
import argparse
import hashlib
import importlib.metadata
import json
import re
import traceback
from pathlib import Path
from semantic_scoring import judge, parse_qwen, geometry


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--images',type=Path,required=True)
    p.add_argument('--sample',type=Path,required=True)
    p.add_argument('--config',type=Path,default=Path('data/semantic_eval_v1/calibration.json'))
    p.add_argument('--checks',type=Path,default=Path('data/semantic_eval_v1/checks.json'))
    p.add_argument('--tool',choices=['grounding_dino','qwen_vlm'],required=True)
    p.add_argument('--split',choices=['development','held_out'],default='development')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--preflight',action='store_true')
    p.add_argument('--limit',type=int,help='Smoke test: first N sampled images')
    a = p.parse_args()
    config = json.loads(a.config.read_text()); c = config[a.tool]
    if not re.fullmatch('[0-9a-f]{40}',c['revision']): raise ValueError('Pin checkpoint SHA')
    checks = {r['input_id']:r for r in json.loads(a.checks.read_text())['records']}
    rows = [r for r in json.loads(a.sample.read_text())['rows'] if r['split']==a.split]
    if a.limit is not None:
        if a.limit < 1: raise ValueError('limit must be positive')
        rows=rows[:a.limit]
    if not rows or len({r['name'] for r in rows})!=len(rows): raise ValueError('Empty/duplicate sample')
    from PIL import Image
    original={r['name']:r for r in (json.loads(line) for line in (a.images/'runs.jsonl').read_text().splitlines())}
    png_hashes={}
    for r in rows:
        path = a.images/(r['name']+'.png')
        if path.parent.resolve()!=a.images.resolve(): raise ValueError('Invalid image name')
        source=original[r['name']]
        if any(source[k]!=r[k] for k in ['input_id','image_sha256','seed','masked_scales']): raise ValueError('Generation provenance mismatch')
        png_hashes[r['name']]=hashlib.sha256(path.read_bytes()).hexdigest()
        with Image.open(path) as im:
            im.load()
            if im.size!=(256,256) or im.mode!='RGB': raise ValueError('Unexpected image size/mode')
        if r['input_id'] not in checks: raise ValueError('Missing check')
    if a.preflight:
        print(f'Verified {len(rows)} generation records and PNG decodes; PNG hashes recorded on inference. No model loaded.'); return
    import torch
    from PIL import Image
    from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection, Qwen3VLForConditionalGeneration
    if not torch.cuda.is_available(): raise RuntimeError('Run inference on RunPod CUDA')
    torch.manual_seed(42)
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.benchmark=False
    manifest = {'png_sha256':png_hashes,'generation_runs_sha256':hashlib.sha256((a.images/'runs.jsonl').read_bytes()).hexdigest(),'config':config,'tool':a.tool,'split':a.split,'limit':a.limit,
                'hashes':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [a.sample,a.checks,Path(__file__),Path(__file__).with_name('semantic_scoring.py')]},
                'versions':{x:importlib.metadata.version(x) for x in ['torch','torchvision','transformers','Pillow']}}
    a.output.mkdir(parents=True,exist_ok=True)
    mpath = a.output/'manifest.json'
    if mpath.exists() and json.loads(mpath.read_text())!=manifest: raise ValueError('Output configuration mismatch; use new directory')
    mpath.write_text(json.dumps(manifest,indent=2)+'\n')
    result_dir=a.output/'predictions'; result_dir.mkdir(exist_ok=True)
    kwargs = {'revision':c['revision']}
    if a.tool=='qwen_vlm': kwargs.update(c['image_pixel_limits'])
    processor=AutoProcessor.from_pretrained(c['checkpoint'],**kwargs)
    if a.tool=='grounding_dino':
        from torchvision.ops import nms
        model=AutoModelForZeroShotObjectDetection.from_pretrained(c['checkpoint'],revision=c['revision']).to('cuda').eval()
    else:
        model=Qwen3VLForConditionalGeneration.from_pretrained(c['checkpoint'],revision=c['revision'],torch_dtype=torch.bfloat16,attn_implementation='sdpa').to('cuda').eval()
    for i,r in enumerate(rows):
        dest=result_dir/(r['name']+'.json')
        if dest.exists() and json.loads(dest.read_text()).get('status')!='evaluation_error': continue
        check=checks[r['input_id']]; e=check['evaluator_input']; raw=None; attempts=[]
        try:
            with Image.open(a.images/(r['name']+'.png')) as im: image=im.convert('RGB')
            with torch.inference_mode():
                if a.tool=='qwen_vlm':
                    messages=[{'role':'system','content':[{'type':'text','text':e['qwen_system']}]},{'role':'user','content':[
                        {'type':'image','image':image}, {'type':'text','text':e['qwen_question']+' Allowed answers: '+json.dumps(e['allowed_answers'])}]}]
                    # Fixed schema-only retry policy, identical for every invalid response.
                    for attempt in range(2):
                        inputs=processor.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,return_dict=True,return_tensors='pt').to('cuda')
                        output=model.generate(**inputs,**c['decoding'])
                        raw=processor.decode(output[0,inputs['input_ids'].shape[1]:],skip_special_tokens=True)
                        attempts.append(raw)
                        try:
                            score=parse_qwen(raw,check)
                            break
                        except (ValueError,TypeError):
                            if attempt==1: raise
                            messages[1]['content'][1]['text']+=' Schema reminder: output a JSON object with identity_status, status, answer and evidence. An ok answer must be a non-null allowed value. For missing, ambiguous or unclear use answer=null. Counts are nonnegative integers. If you cannot identify the requested objects, do not assign their attributes. Do not guess.' + ' ' + e.get('response_schema', '')
                else:
                    raw=[]; retained=[]
                    for query in e['detector_queries']:
                        inputs=processor(images=image,text=query.lower()+'.',return_tensors='pt').to('cuda')
                        output=model(**inputs)
                        detected=processor.post_process_grounded_object_detection(output,inputs.input_ids,threshold=c['box_threshold'],text_threshold=c['text_threshold'],target_sizes=[(image.height,image.width)])[0]
                        # Require the full query phrase, not just one matching component.
                        normalize=lambda s:' '.join(re.findall(r'\w+',s.lower()))
                        valid=[j for j,label in enumerate(detected['text_labels']) if normalize(label)==normalize(query)]
                        b=detected['boxes'][valid]; scores=detected['scores'][valid]
                        keep=nms(b,scores,c['nms_iou'])
                        boxes=b[keep].cpu().tolist(); retained.append(boxes)
                        raw.append({'query':query,'all_boxes':detected['boxes'].cpu().tolist(),'all_scores':detected['scores'].cpu().tolist(),'text_labels':detected['text_labels'],'retained_boxes':boxes})
                    if check['semantic']=='object': answer={'status':'ok','answer':bool(retained[0])}
                    elif check['semantic']=='count': answer={'status':'ok','answer':len(retained[0])}
                    elif check['primary_evaluator']=='grounding_dino_geometry':
                        expected=check['scoring_only']['expected_answer']
                        axis='x' if expected in ['left','right'] else 'y'
                        answer=geometry(retained,axis,config['geometry']['epsilon_'+axis],image.width if axis=='x' else image.height)
                    else: answer=None
                    score=judge(answer,check) if answer else {'status':'localization_only','success':None,'absolute_error':None}
            result={'name':r['name'],'input_id':r['input_id'],'image_sha256':r['image_sha256'],'raw':raw,'attempts':attempts,
                    'role':'primary' if check['primary_evaluator'].startswith(a.tool) else 'audit',**score}
        except torch.cuda.OutOfMemoryError:
            raise
        except Exception as exc:
            result={'name':r['name'],'status':'evaluation_error','raw':raw,'attempts':attempts,'error':str(exc),'traceback':traceback.format_exc()}
        tmp=dest.with_suffix('.tmp'); tmp.write_text(json.dumps(result,indent=2)+'\n');tmp.replace(dest)
        print(i+1,'/',len(rows),r['name'],result['status'],flush=True)
    outcomes=[json.loads((result_dir/(r['name']+'.json')).read_text()) for r in rows]
    errors=sum(r['status']=='evaluation_error' for r in outcomes)
    print(f'Complete: {len(outcomes)} predictions, {errors} evaluation errors. Pilot only.')
    if errors: raise SystemExit(1)

if __name__ == '__main__': main()
