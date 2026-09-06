"""Reindex existing LPIPS curves by number of masked scales; no inference."""
import argparse
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

LABELS={'object':'Object','color':'Color','shape':'Shape','texture':'Texture','count':'Count','spatial_relation':'Spatial relation'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--curves',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    with args.curves.open() as f:
        rows=[r for r in csv.DictReader(f) if r['metric']=='lpips']
    index={(r['semantic'],r['direction'],int(r['boundary'])):r for r in rows}
    assert len(rows)==len(index)==132
    args.output.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
    ymax=max(float(r['q75']) for r in rows)*1.1
    exported=[]
    for semantic,label in LABELS.items():
        fig,ax=plt.subplots(figsize=(6.6,4.5),layout='constrained')
        for direction,color,legend in [('prefix','#2563eb','Earliest m scales'),('suffix','#e35d2f','Latest m scales')]:
            batch=[]
            for m in range(11):
                k=m if direction=='prefix' else 10-m
                r=index[semantic,direction,k]
                assert int(r['n'])==50
                batch.append(r)
                exported.append(dict(semantic=semantic,selection='earliest' if direction=='prefix' else 'latest',
                                     masked_scale_count=m,original_direction=direction,original_boundary=k,n=50,
                                     mean=r['mean'],q25=r['q25'],q75=r['q75']))
            ax.plot(range(11),[float(r['mean']) for r in batch],color=color,marker='o',markersize=4,lw=2,label=legend)
            ax.fill_between(range(11),[float(r['q25']) for r in batch],[float(r['q75']) for r in batch],color=color,alpha=.12,linewidth=0)
        for k1,k2 in [(0,10),(10,0)]:
            for stat in ['mean','q25','q75']:assert index[semantic,'prefix',k1][stat]==index[semantic,'suffix',k2][stat]
        ax.set_title(f'{label} | LPIPS: early vs. late masking',loc='left',fontsize=13,fontweight='bold')
        ax.set_xlabel('Number of masked scales m');ax.set_ylabel('LPIPS to same-seed baseline')
        ax.set_xticks(range(11));ax.set_ylim(0,ymax);ax.grid(axis='y',color='#dbe1e8',lw=.6)
        ax.legend(loc='upper left',frameon=False,fontsize=9)
        fig.supxlabel('50 prompts · seed 42 · mean and IQR (not CI)\nEarly = prefix(m); late = suffix(10−m) · same scale count, different token counts',fontsize=8,color='#475569')
        fig.savefig(args.output/f'{semantic}_lpips_extent.png',dpi=180)
        fig.savefig(args.output/f'{semantic}_lpips_extent.pdf')
        plt.close(fig)
    with (args.output/'lpips_extent_data.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(exported[0]));w.writeheader();w.writerows(exported)
    print('Six PNG/PDF plots and 132 reindexed rows exported; shared endpoints verified.')

if __name__=='__main__':main()
