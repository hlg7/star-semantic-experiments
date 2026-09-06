"""Plot per-prompt CLIPScore changes from existing scores; no model inference."""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

LABELS={'object':'Object','color':'Color','shape':'Shape','texture':'Texture','count':'Count','spatial_relation':'Spatial relation'}
EPS=1e-6  # Numerical tolerance for display counts, not a significance threshold.

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--metrics',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    summary=args.metrics/'metric_summary.json'
    if not summary.exists():summary=args.metrics/'summary.json'
    if json.loads(summary.read_text())['status']!='passed':raise ValueError('Incomplete evaluation')
    rows=[json.loads(x) for x in (args.metrics/'metrics.jsonl').read_text().splitlines()]
    if len({r['name'] for r in rows})!=len(rows):raise ValueError('Duplicate score records')
    baselines={(r['input_id'],r['seed']):r for r in rows if not r['masked_scales']}
    groups=defaultdict(list)
    for r in rows:
        baseline=baselines[r['input_id'],r['seed']]
        assert r['prompt']==baseline['prompt'] and r['baseline_name']==baseline['name']
        assert abs(r['baseline_clipscore']-baseline['clipscore'])<1e-10
        r['delta']=r['clipscore']-baseline['clipscore']
        assert np.isfinite(r['delta']) and abs(r['delta']+r['clipscore_drop'])<1e-10
        for alias in r['aliases']:groups[r['semantic'],alias['direction'],alias['boundary']].append(r)
    limit=max(abs(r['delta']) for r in rows)*1.12
    args.output.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
    table=[]
    for semantic,label in LABELS.items():
        fig,axes=plt.subplots(1,2,figsize=(12,4.9),sharey=True,layout='constrained')
        for ax,direction,color in zip(axes,['prefix','suffix'],['#2563eb','#e35d2f']):
            means=[];series=[]
            rng=np.random.default_rng(0) # Visual jitter only; never modifies scores.
            jitter=rng.uniform(-.19,.19,50)
            for k in range(11):
                batch=sorted(groups[semantic,direction,k],key=lambda r:(r['input_id'],r['seed']))
                assert len(batch)==50 and len({(r['input_id'],r['seed']) for r in batch})==50
                assert {r['seed'] for r in batch}=={42}
                values=np.array([r['delta'] for r in batch]);series.append(values);means.append(values.mean())
                ax.scatter(k+jitter,values,s=9,color=color,alpha=.38,edgecolors='none',zorder=2)
                table.append(dict(semantic=semantic,direction=direction,boundary=k,n=50,
                    mean=float(values.mean()),median=float(np.median(values)),q25=float(np.quantile(values,.25)),q75=float(np.quantile(values,.75)),
                    min=float(values.min()),max=float(values.max()),up=int((values>EPS).sum()),down=int((values<-EPS).sum()),unchanged=int((np.abs(values)<=EPS).sum())))
            ax.boxplot(series,positions=range(11),widths=.48,showfliers=False,manage_ticks=False,patch_artist=True,
                       boxprops={'facecolor':'#cbd5e1','alpha':.4,'edgecolor':'#64748b'},
                       medianprops={'color':'#111827','linewidth':1.5},
                       whiskerprops={'color':'#94a3b8'},capprops={'color':'#94a3b8'})
            ax.plot(range(11),means,color=color,marker='D',markersize=4,lw=1.7,zorder=4)
            ax.axhline(0,color='#111827',linestyle='--',lw=1,zorder=1)
            ax.set_title('Prefix: mask scales 1..k' if direction=='prefix' else 'Suffix: mask scales k+1..10',loc='left',fontsize=11)
            ax.set_xticks(range(11));ax.set_xlabel('Scale boundary k');ax.set_ylim(-limit,limit)
            ax.grid(axis='y',color='#e2e8f0',lw=.6)
        full=next(r for r in table if r['semantic']==semantic and r['direction']=='prefix' and r['boundary']==10)
        fig.suptitle(f'{label} | Paired CLIPScore change\nFull mask: {full["up"]} up / {full["down"]} down / {full["unchanged"]} unchanged',fontsize=13,fontweight='bold')
        axes[0].set_ylabel('CLIPScore(mask) − CLIPScore(baseline)')
        axes[1].legend(handles=[Line2D([],[],marker='o',ls='',color='#64748b',label='One prompt'),
            Line2D([],[],marker='D',color='#64748b',label='Mean'),Line2D([],[],color='#111827',label='Box median')],loc='lower left',fontsize=8,frameon=False)
        fig.supxlabel('50 prompts · seed 42 · boxes: IQR; whiskers: 1.5×IQR · dots include all outliers · positive = higher CLIPScore',fontsize=8)
        fig.savefig(args.output/f'{semantic}_clipscore_delta.png',dpi=180)
        fig.savefig(args.output/f'{semantic}_clipscore_delta.pdf')
        plt.close(fig)
        print(semantic,full)
        for k1,k2 in [(0,10),(10,0)]:
            assert sorted((r['name'],r['delta']) for r in groups[semantic,'prefix',k1])==sorted((r['name'],r['delta']) for r in groups[semantic,'suffix',k2])
    with (args.output/'clipscore_delta_summary.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(table[0]));writer.writeheader();writer.writerows(table)
    print('Wrote six paired-distribution PNG/PDF figures and 132 condition summaries.')

if __name__=='__main__':main()
