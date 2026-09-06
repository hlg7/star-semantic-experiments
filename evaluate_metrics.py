"""RunPod-only, offline CLIPScore and LPIPS for completed masking experiments."""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import importlib.metadata
import os


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--batch-size',type=int,default=32)
    args=p.parse_args()
    summary=json.loads((args.run/'summary.json').read_text())
    if summary.get('status')!='passed':raise RuntimeError('Generation checks not complete')
    manifest=json.loads((args.run/'manifest.json').read_text())
    items={x['id']:x for x in manifest['inputs']}
    records=[]
    with (args.run/'runs.jsonl').open() as f:
        for line in f:
            r=json.loads(line)
            if not r['aliases']:continue # reference/full-mask repeat are diagnostics, not new observations
            records.append({k:r[k] for k in ['name','input_id','prompt','semantic','seed','masked_scales','aliases','image_sha256']})
    expected=len(items)*len(manifest['config']['seeds'])*20
    if len(records)!=expected or len({r['name'] for r in records})!=len(records):
        raise RuntimeError('Incomplete or duplicated canonical schedules')
    baselines={(r['input_id'],r['seed']):r for r in records if not r['masked_scales']}
    for r in records:
        r['baseline_name']=baselines[r['input_id'],r['seed']]['name']
        r['scene_family']=items[r['input_id']].get('scene_family','unassigned')
        r['subtype']=items[r['input_id']].get('subtype',r['semantic'])
        if not (args.run/(r['name']+'.png')).is_file():raise FileNotFoundError(r['name'])
    os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
    import numpy as np
    import torch
    from PIL import Image
    import clip
    import lpips
    if not torch.cuda.is_available():raise RuntimeError('Run this on RunPod CUDA')
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    torch.backends.cudnn.benchmark=False
    torch.use_deterministic_algorithms(True)
    config=dict(generation_manifest_sha256=hashlib.sha256((args.run/'manifest.json').read_bytes()).hexdigest(),
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                clip_model='ViT-B/32',clip_commit='d05afc436d78f1c48dc0dbf8e5980a9d471f35f6',
                clip_prefix='A photo depicts ',clip_formula='2.5*max(cosine,0)',
                precision='float32; TF32 disabled',lpips_net='alex',lpips_version='0.1',
                lpips_package=importlib.metadata.version('lpips'),torch=torch.__version__,
                batch_size=args.batch_size,canonical_images=len(records),
                note='Full-prompt alignment and paired perceptual change; no VQA or semantic correctness score.')
    args.output.mkdir(parents=True,exist_ok=True)
    configpath=args.output/'metric_manifest.json'
    if configpath.exists() and json.loads(configpath.read_text())!=config:
        raise RuntimeError('Output has a different metric configuration')
    configpath.write_text(json.dumps(config,indent=2)+'\n')
    def load_cache(name):
        path=args.output/name
        if path.exists():
            values=json.loads(path.read_text())
            if set(values)!={r['name'] for r in records}:raise RuntimeError('Incomplete cache')
            return values
    clips=load_cache('clip_scores.json')
    if clips is None:
        model,preprocess=clip.load('ViT-B/32',device='cuda',jit=False,download_root='/workspace/star-metric-assets/clip')
        model=model.float().eval()
        texts=list(dict.fromkeys(r['prompt'] for r in records));text_features={}
        with torch.inference_mode():
            for start in range(0,len(texts),args.batch_size):
                batch=texts[start:start+args.batch_size]
                tokens=clip.tokenize([config['clip_prefix']+x for x in batch],truncate=False).cuda()
                feat=model.encode_text(tokens).float();feat=feat/feat.norm(dim=-1,keepdim=True)
                text_features.update(zip(batch,feat))
            clips={}
            for start in range(0,len(records),args.batch_size):
                batch=records[start:start+args.batch_size]
                images=torch.stack([preprocess(Image.open(args.run/(r['name']+'.png')).convert('RGB')) for r in batch]).cuda()
                feat=model.encode_image(images).float();feat=feat/feat.norm(dim=-1,keepdim=True)
                target=torch.stack([text_features[r['prompt']] for r in batch])
                scores=2.5*(feat*target).sum(-1).clamp(min=0)
                if not torch.isfinite(scores).all():raise RuntimeError('Nonfinite CLIPScore')
                clips.update(zip([r['name'] for r in batch],scores.cpu().tolist()))
                if start%320==0:print('CLIP',start,'/',len(records),flush=True)
        (args.output/'clip_scores.json').write_text(json.dumps(clips))
        del model,text_features,feat,target,images,scores,tokens
        gc.collect();torch.cuda.empty_cache()
    distances=load_cache('lpips_scores.json')
    if distances is None:
        metric=lpips.LPIPS(net='alex',version='0.1').cuda().eval()
        def pixels(name):
            with Image.open(args.run/(name+'.png')) as im:
                array=np.array(im.convert('RGB'),dtype=np.float32)/127.5-1
            if array.shape!=(256,256,3):raise RuntimeError('Unexpected image dimensions')
            return torch.from_numpy(array).permute(2,0,1)
        distances={}
        with torch.inference_mode():
            for start in range(0,len(records),args.batch_size):
                batch=records[start:start+args.batch_size]
                x=torch.stack([pixels(r['name']) for r in batch]).cuda()
                y=torch.stack([pixels(r['baseline_name']) for r in batch]).cuda()
                values=metric(x,y).flatten()
                if not torch.isfinite(values).all():raise RuntimeError('Nonfinite LPIPS')
                distances.update(zip([r['name'] for r in batch],values.cpu().tolist()))
                if start%320==0:print('LPIPS',start,'/',len(records),flush=True)
        (args.output/'lpips_scores.json').write_text(json.dumps(distances))
    with (args.output/'metrics.jsonl').open('w') as f:
        for r in records:
            r.update(clipscore=clips[r['name']],baseline_clipscore=clips[r['baseline_name']],
                     clipscore_drop=clips[r['baseline_name']]-clips[r['name']],lpips=distances[r['name']])
            if not r['masked_scales'] and (abs(r['lpips'])>1e-6 or abs(r['clipscore_drop'])>1e-8):
                raise RuntimeError('Baseline self comparison failed')
            f.write(json.dumps(r)+'\n')
    (args.output/'summary.json').write_text(json.dumps(dict(status='passed',images_scored=len(records),
         prompts=len(items),baseline_self_comparisons=len(baselines),
         baseline_self_checks_passed=True),indent=2)+'\n')
    print('METRICS COMPLETE',len(records),flush=True)

if __name__=='__main__':main()
