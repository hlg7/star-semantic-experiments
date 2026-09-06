"""Plot paired scale interventions, keeping LPIPS and CLIPScore separate."""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

LABELS=dict(object='Object',color='Color',shape='Shape',texture='Texture',count='Count',spatial_relation='Spatial relation')
COLORS={'prefix':'#2563eb','suffix':'#e35d2f'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--metrics',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    records=[json.loads(x) for x in (args.metrics/'metrics.jsonl').read_text().splitlines()]
    if json.loads((args.metrics/'summary.json').read_text())['status']!='passed':raise RuntimeError('Metrics not complete')
    args.output.mkdir(parents=True,exist_ok=True)
    groups=defaultdict(list)
    for r in records:
        for a in r['aliases']:groups[r['semantic'],a['direction'],a['boundary']].append(r)
    table=[];results={}
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','savefig.facecolor':'white'})
    for semantic in LABELS:
        baseline=groups[semantic,'prefix',0]
        if len(baseline)!=50:raise RuntimeError('Expected 50 prompts per semantic')
        results[semantic]=dict(n_prompts=50,seed=42,baseline_clipscore_mean=float(np.mean([r['clipscore'] for r in baseline])),
                              scene_families=len({r['scene_family'] for r in baseline}))
        for metric in ['lpips','clipscore']:
            fig,ax=plt.subplots(figsize=(6.3,4.25),layout='constrained')
            for direction in ['prefix','suffix']:
                means=[];q25=[];q75=[]
                for k in range(11):
                    batch=groups[semantic,direction,k]
                    if len(batch)!=50 or len({(r['input_id'],r['seed']) for r in batch})!=50:raise RuntimeError('Unexpected sample count')
                    values=np.array([r[metric] for r in batch])
                    means.append(values.mean());q25.append(np.quantile(values,.25));q75.append(np.quantile(values,.75))
                    table.append(dict(semantic=semantic,metric=metric,direction=direction,boundary=k,n=50,
                                      mean=float(values.mean()),q25=float(q25[-1]),q75=float(q75[-1]),
                                      mean_clipscore_drop=float(np.mean([r['clipscore_drop'] for r in batch]))))
                color=COLORS[direction]
                label='Prefix: mask scales 1..k' if direction=='prefix' else 'Suffix: mask scales k+1..10'
                ax.plot(range(11),means,color=color,marker='o',markersize=3.5,lw=2,label=label)
                ax.fill_between(range(11),q25,q75,color=color,alpha=.12,linewidth=0)
            if metric=='clipscore':
                ax.axhline(results[semantic]['baseline_clipscore_mean'],color='#64748b',ls='--',lw=1,label='Unmasked baseline mean')
                ax.set_ylabel('CLIPScore (full prompt; higher = more aligned)')
            else:
                ax.axhline(0,color='#64748b',ls='--',lw=1)
                ax.set_ylim(bottom=0);ax.set_ylabel('LPIPS to same-seed baseline (higher = more change)')
            ax.set_title(f'{LABELS[semantic]} · {"LPIPS" if metric=="lpips" else "CLIPScore"}',loc='left',fontsize=14)
            ax.set_xlabel('Scale boundary k (0..10)')
            ax.set_xticks(range(11));ax.grid(axis='y',color='#dbe1e8',lw=.6)
            ax.legend(fontsize=8,frameon=False,loc='best')
            fig.supxlabel('50 prompts · seed 42 · line: mean · shading: interquartile range (not CI)',fontsize=8,color='#475569')
            fig.savefig(args.output/f'{semantic}_{metric}.png',dpi=180)
            fig.savefig(args.output/f'{semantic}_{metric}.pdf')
            plt.close(fig)
        full=groups[semantic,'prefix',10]
        results[semantic].update(full_mask_clipscore_mean=float(np.mean([r['clipscore'] for r in full])),
                                full_mask_clipscore_drop_mean=float(np.mean([r['clipscore_drop'] for r in full])),
                                full_mask_lpips_mean=float(np.mean([r['lpips'] for r in full])))
        # Equivalent schedules must have identical endpoint measurements.
        for left,right in [(('prefix',0),('suffix',10)),(('prefix',10),('suffix',0))]:
            assert sorted((r['input_id'],r['name']) for r in groups[semantic,*left])==sorted((r['input_id'],r['name']) for r in groups[semantic,*right])
    with (args.output/'curve_data.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
    (args.output/'results_summary.json').write_text(json.dumps(results,indent=2)+'\n')
    # Contact sheet for checking all 12 panels together; individual PNG/PDF are the report artifacts.
    from PIL import Image
    sheet=Image.new('RGB',(2268,4590),'white')
    for row,semantic in enumerate(LABELS):
        for col,metric in enumerate(['lpips','clipscore']):
            im=Image.open(args.output/f'{semantic}_{metric}.png').convert('RGB')
            im.thumbnail((1134,765));sheet.paste(im,(col*1134,row*765))
    sheet.save(args.output/'overview.jpg',quality=92)
    print(json.dumps(results,indent=2));print('PLOTS COMPLETE',flush=True)

if __name__=='__main__':main()
