"""Summarize every frozen supplement case; retain failures and negative results."""
import csv, json, hashlib, statistics as st
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).parent
BASE=ROOT/'supplement_20261117'
RAW=BASE/'supplement_v3'
OUT=BASE/'derived';OUT.mkdir(exist_ok=True)
FIG=OUT/'figures';FIG.mkdir(exist_ok=True)
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def finish(name):
    plt.savefig(FIG/(name+'.png'),dpi=180,bbox_inches='tight')
    plt.savefig(FIG/(name+'.svg'),bbox_inches='tight');plt.close()
completion=read(RAW/'completion.json')
assert completion['cost_workloads']==21 and completion['drift_workloads']==9 and completion['new_region_cases']==108
env=read(RAW/'environment.json')
for name,sha in env['hashes'].items():assert hashlib.sha256((BASE/name).read_bytes()).hexdigest()==sha,(name,'source mismatch')
cost=[read(p) for p in sorted(RAW.glob('cost_*.json'))]
drift=[read(p) for p in sorted(RAW.glob('drift_*.json'))]
assert len(cost)==21 and len(drift)==9
all_records=cost+drift
count_bad=[];point_bad=[];seeds=[]
for r in all_records:
    assert len(r['trials'])==3 and len(r['descriptors'])==r['batches']
    for rep,t in enumerate(r['trials']):
        assert all(len(v)==r['batches'] for v in t['batch_s'].values())
        for batch,errors in enumerate(t['count_l1_errors']):
            for method,error in errors.items():
                if error:count_bad.append(dict(seed=r['seed'],n=r['n'],batch=batch,method=method,error=error))
    for batch,d in enumerate(r['descriptors']):
        if d['point_mismatches']:point_bad.append(dict(seed=r['seed'],n=r['n'],batch=batch,error=d['point_mismatches']))
    med={m:st.median(sum(t['batch_s'][m]) for t in r['trials']) for m in r['trials'][0]['batch_s']}
    strong=min(med['B1'],med['B1s'])
    row=dict(distribution=r['distribution'],n=r['n'],seed=r['seed'],shift=r['shift_m_per_batch'],batches=r['batches'],
             **{m+'_s':v for m,v in med.items()},strong_over_M3=strong/med['M3'],M2_over_M3=med['M2']/med['M3'],
             B1_over_M3=med['B1']/med['M3'],B1s_over_M3=med['B1s']/med['M3'],
             new_cells=sum(d['new_cells'] for d in r['descriptors']),risk_fraction=st.mean(d['risk_fraction'] for d in r['descriptors']))
    seeds.append(row)
fields=sorted(set().union(*(row.keys() for row in seeds)))
with (OUT/'seed_results.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(seeds)
groups=[]
for dist,n in [('U',1000),('U',10000),('U',100000),('C',1000),('C',10000),('C',100000),('B',10000)]:
    rs=[r for r in seeds if r['shift'] is None and r['distribution']==dist and r['n']==n]
    assert len(rs)==3
    out=dict(distribution=dist,n=n,seeds=3)
    for k in ['B1_s','B1s_s','M2_s','M3_s','A3_s','strong_over_M3','M2_over_M3','B1_over_M3','B1s_over_M3','risk_fraction']:
        out[k]=st.mean(r[k] for r in rs)
    out['ratio_min']=min(r['strong_over_M3'] for r in rs);out['ratio_max']=max(r['strong_over_M3'] for r in rs)
    groups.append(out)
regions=read(RAW/'new_regions.json');regression=read(RAW/'failure_regression.json');memory=read(RAW/'memory.json')
assert len(regions)==108 and sum(r['n'] for r in regions)==540000 and len(regression)==12
result=dict(environment=env,cost_groups=groups,new_region_cases=108,new_region_points=540000,
            new_region_point_mismatches=sum(r['point_mismatches'] for r in regions),
            new_region_count_l1=sum(r['count_l1'] for r in regions),
            workload_count_errors=count_bad,workload_point_errors=point_bad,
            regression_rows=12,regression_failures=[r for r in regression if not r['m2_ok'] or not r['m3_ok']],
            memory=memory,raw_hashes={str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(RAW.glob('*.json'))})
(OUT/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
labels=[f"{g['distribution']} / {g['n']:,}" for g in groups]
fig,ax=plt.subplots(figsize=(10,4.2))
for offset,key,color,label in [(-.22,'M2_over_M3','#7896b0','M2 / M3'),(0,'B1_over_M3','#247aab','B1 / M3'),(.22,'B1s_over_M3','#27a08d','B1s / M3')]:
    ax.bar([i+offset for i in range(7)],[g[key] for g in groups],width=.22,color=color,label=label)
ax.axhline(1,c='#bc6b38',ls='--');ax.set_xticks(range(7),labels,rotation=20);ax.set_ylabel('Cumulative time ratio (20 batches)');ax.legend(ncol=3);finish('01_strong_baselines')
fig,axs=plt.subplots(1,2,figsize=(10,4))
for ax,dist in zip(axs,['U','C']):
    rs=[r for r in cost if r['distribution']==dist and r['n']==100000]
    for method in ['B1','B1s','M2','M3','A3']:
        y=[st.mean(st.median(sum(t['batch_s'][method][:k]) for t in r['trials']) for r in rs) for k in range(1,21)]
        ax.plot(range(1,21),y,label=method)
    ax.set_title(dist+' / 100,000 points per batch');ax.set_xlabel('Different new batches');ax.set_ylabel('Cumulative seconds');ax.legend(fontsize=8)
fig.tight_layout();finish('02_dense_cumulative')
fig,axs=plt.subplots(1,2,figsize=(10,4))
for shift,color in zip([0,1000,5000],['#247aab','#27a08d','#bc6b38']):
    rs=[r for r in seeds if r['shift']==shift]
    ratio=[r['strong_over_M3'] for r in rs]
    axs[0].scatter([shift/1000]*3,ratio,color=color);axs[0].plot([shift/1000],[st.mean(ratio)],marker='D',color=color)
    source=[r for r in drift if r['shift_m_per_batch']==shift]
    axs[1].plot(range(1,11),[st.mean(sum(d['new_cells'] for d in r['descriptors'][:k]) for r in source) for k in range(1,11)],label=f'{shift/1000:g} km/batch')
axs[0].axhline(1,c='gray',ls='--');axs[0].set_xlabel('Eastward displacement per batch (km)');axs[0].set_ylabel('min(B1, B1s) / M3 (10 batches)')
axs[1].set_xlabel('Different new batches');axs[1].set_ylabel('Cumulative classified fine cells');axs[1].legend();fig.tight_layout();finish('03_drift')
fig,axs=plt.subplots(1,2,figsize=(10,4))
cities=['beijing','shenzhen','sydney','reykjavik']
for j,(rf,rc) in enumerate([(9,8),(10,8),(10,9)]):
    vals=[sum(r['point_mismatches'] for r in regions if r['city']==city and r['rf']==rf and r['rc']==rc) for city in cities]
    axs[0].bar([i+(j-1)*.22 for i in range(4)],vals,.22,label=f'{rf} to {rc}')
    risks=[st.mean(r['risk_fraction'] for r in regions if r['city']==city and r['rf']==rf and r['rc']==rc) for city in cities]
    axs[1].plot(range(4),risks,marker='o',label=f'{rf} to {rc}')
for ax in axs:ax.set_xticks(range(4),cities,rotation=15);ax.legend(fontsize=8)
axs[0].set_ylabel('Point mismatches, all registered cases');axs[0].set_ylim(bottom=0,top=max(1,sum(r['point_mismatches'] for r in regions)*1.1));axs[1].set_ylabel('Risk-point fraction, U/C/B pooled descriptively');fig.tight_layout();finish('04_new_regions')
fig,ax=plt.subplots(figsize=(7,4));names=list(memory)
ax.bar(names,[memory[n]['peak_bytes']/1024**2 for n in names],color='#247aab',label='Peak')
ax.bar(names,[memory[n]['retained_bytes']/1024**2 for n in names],color='#27a08d',label='Retained')
ax.set_ylabel('Python allocations (MiB), 5 new batches');ax.legend();finish('05_memory')
print(json.dumps({k:v for k,v in result.items() if k not in ['environment','raw_hashes']},ensure_ascii=False,indent=2))
