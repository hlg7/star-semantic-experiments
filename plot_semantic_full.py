"""Plot descriptive v3 semantic curves with explicit valid/pair denominators."""
import argparse,json,math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
LABELS={'object':'Object','color':'Color','shape':'Shape','texture':'Texture','count':'Count','spatial_relation':'Spatial relation'}
COLORS={'prefix':'#2563eb','suffix':'#dc6837'}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--report',type=Path,required=True);a=ap.parse_args();data=json.loads((a.report/'summary.json').read_text());out=a.report/'plots';out.mkdir(exist_ok=True)
    lookup={(r['semantic'],r['subtype'],r['direction'],r['boundary']):r for r in data['curves']}
    plt.rcParams.update({'font.size':10,'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
    def plot(sem,sub,metric,filename):
        fig,ax=plt.subplots(figsize=(6.6,4.5),layout='constrained');base=lookup[sem,sub,'prefix',0]
        denom='n_pairs' if metric=='paired_delta' else ('baseline_correct_n' if metric=='retention' else 'n_valid')
        if metric=='count_mae':denom='count_numeric_n'
        ds=[];ys=[]
        for direction in ['prefix','suffix']:
            rs=[lookup[sem,sub,direction,k] for k in range(11)];ds.extend(r[denom] for r in rs)
            vals=[(r[metric]*(1 if metric=='count_mae' else 100)) if r[metric] is not None else math.nan for r in rs];ys+=vals
            ax.plot(range(11),vals,marker='o',markersize=3.5,lw=2,color=COLORS[direction],label='Prefix: mask 1..k' if direction=='prefix' else 'Suffix: mask k+1..10')
        title={'success_rate':'Confirmed semantic success','paired_delta':'Paired change from baseline','uncertain_rate':'Ambiguous / unclear outputs','retention':'Retention on baseline-correct pairs','count_mae':'Count deviation from requested count'}[metric]
        ylabel={'success_rate':'Success (%)','paired_delta':'Change (percentage points)','uncertain_rate':'Uncertain (%)','retention':'Retention (%)','count_mae':'Mean absolute count deviation'}[metric]
        if metric in ['success_rate','uncertain_rate','retention']:ax.set_ylim(-3,103)
        elif metric=='paired_delta':
            bound=max(10,math.ceil(max(abs(x) for x in ys if not math.isnan(x))/5)*5+5);ax.set_ylim(-bound,bound);ax.axhline(0,color='#64748b',ls='--',lw=1)
        else:ax.set_ylim(bottom=0)
        if metric in ['success_rate','count_mae'] and base[metric] is not None:ax.axhline(base[metric]*(1 if metric=='count_mae' else 100),color='#64748b',ls='--',lw=1,label='Unmasked baseline mean')
        ax.set_title(LABELS[sem]+(' · '+sub.replace('_',' ') if sub!='all' else '')+'\n'+title,loc='left',fontsize=13)
        ax.set_xlabel('Scale boundary k (0..10)');ax.set_ylabel(ylabel);ax.set_xticks(range(11));ax.grid(axis='y',alpha=.22);ax.legend(fontsize=8,frameon=False,loc='best')
        n=f'{min(ds)}' if min(ds)==max(ds) else f'{min(ds)}–{max(ds)}'
        fig.supxlabel(f'Exploratory automatic scores · seed 42 · {denom}={n} per point\nDescriptive means; no confidence intervals. Errors excluded, not scored zero.',fontsize=8,color='#475569')
        for ext in ['png','pdf']:fig.savefig(out/f'{filename}.{ext}',dpi=180)
        plt.close(fig)
    for sem in LABELS:
        for metric in ['success_rate','paired_delta','uncertain_rate','retention']:plot(sem,'all',metric,f'{sem}_{metric}')
    for sem in ['texture','spatial_relation']:
        subs=sorted({r['subtype'] for r in data['curves'] if r['semantic']==sem and r['subtype']!='all'})
        for sub in subs:plot(sem,sub,'success_rate',f'{sem}_{sub}_success_rate')
    plot('count','all','count_mae','count_mae')
    for filename,metrics in [('overview',['success_rate','paired_delta']),('coverage_overview',['uncertain_rate','retention'])]:
        sheet=Image.new('RGB',(1584,3240),'white')
        for i,sem in enumerate(LABELS):
            for j,metric in enumerate(metrics):
                im=Image.open(out/f'{sem}_{metric}.png').convert('RGB');im.thumbnail((792,540));sheet.paste(im,(j*792,i*540))
        sheet.save(out/f'{filename}.jpg',quality=92)
    print('Wrote',len(list(out.glob('*.png'))),'PNG/PDF plot pairs and two overview sheets.')
if __name__=='__main__':main()
