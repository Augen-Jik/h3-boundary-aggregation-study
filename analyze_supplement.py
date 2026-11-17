from pathlib import Path
import json,hashlib,csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
R=Path(__file__).parent
O=R/"supplement_analysis";O.mkdir(exist_ok=True)
F=O/"figures";F.mkdir(exist_ok=True)
font=Path("C:/Windows/Fonts/msyh.ttc")
if font.exists():
    font_manager.fontManager.addfont(str(font));plt.rcParams["font.family"]=font_manager.FontProperties(fname=str(font)).get_name()
plt.rcParams.update({"axes.unicode_minus":False,"font.size":11,"axes.spines.top":False,"axes.spines.right":False,"figure.dpi":130})
paths=sorted((R/"revision_v2/results/workloads").glob("*.json"))
rows=[];data={}
def stable(v):
    return next((i+1 for i in range(len(v)) if np.all(v[i:])),None)
for p in paths:
    x=json.loads(p.read_text());d=x["distribution"];n=x["n"];seed=x["seed"]
    traces={m:np.array([t["batch_s"][m] for t in x["trials"]]) for m in ("B1","M","A1")}
    cum={m:np.median(np.cumsum(t,axis=1),axis=0) for m,t in traces.items()}
    end=cum["B1"][-1]/cum["M"][-1]
    tail={m:np.median(np.sum(t[:,-5:],axis=1))/5 for m,t in traces.items()}
    news=np.median(np.array([t["new_cells"] for t in x["trials"]]),axis=0)
    r=dict(distribution=d,n=n,seed=seed,ratio20=end,
        saving_pct20=(1-cum["M"][-1]/cum["B1"][-1])*100,
        stable_crossover=stable(cum["M"]<cum["B1"]),
        cold_debt_s=cum["M"][0]-cum["B1"][0],
        tail_B1_s=tail["B1"],tail_M_s=tail["M"],tail_ratio=tail["B1"]/tail["M"],
        repeat_wins20=int(np.sum(np.sum(traces["M"],axis=1)<np.sum(traces["B1"],axis=1))),
        repeats=len(x["trials"]),cache_first=news[0],cache_final=sum(news),
        source_path=str(p.relative_to(R)).replace(chr(92),"/"),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    rows.append(r);data[d,n,seed]=(cum,news,traces)
summary=[]
for d in ("U","C"):
    for n in (1000,10000,100000):
        rs=[r for r in rows if r["distribution"]==d and r["n"]==n]
        ratios=np.array([r["ratio20"] for r in rs])
        summary.append(dict(distribution=d,n=n,ratio_mean=float(ratios.mean()),
          ratio_min=float(ratios.min()),ratio_max=float(ratios.max()),
          loo_min=float(min(np.delete(ratios,i).mean() for i in range(3))),
          loo_max=float(max(np.delete(ratios,i).mean() for i in range(3))),
          crossover=[r["stable_crossover"] for r in rs],
          repeat_wins=sum(r["repeat_wins20"] for r in rs),repeat_total=sum(r["repeats"] for r in rs),
          saving_pct_mean=float(np.mean([r["saving_pct20"] for r in rs])),
          tail_ratio_mean=float(np.mean([r["tail_ratio"] for r in rs])),
          first_cache_fraction=float(np.mean([r["cache_first"]/r["cache_final"] for r in rs]))))
(O/"analysis.json").write_text(json.dumps(dict(source="Existing frozen v2 logs; no new H3 runs",workloads=len(rows),timing_repetitions=sum(r["repeats"] for r in rows),rows=rows,summary=summary),ensure_ascii=False,indent=2),encoding="utf-8")
with (O/"seed_results.csv").open("w",newline="",encoding="utf-8-sig") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def finish(name):
    plt.savefig(F/(name+".png"),bbox_inches="tight",dpi=180);plt.savefig(F/(name+".svg"),bbox_inches="tight");plt.close()
fig,ax=plt.subplots(figsize=(9,4.5))
labels=[f'{s["distribution"]} / {s["n"]:,}' for s in summary]
means=np.array([s["ratio_mean"] for s in summary])
ax.bar(labels,means,color=["#2879B0" if v>1 else "#9AAEBB" for v in means])
ax.errorbar(range(6),means,yerr=np.array([[s["ratio_mean"]-s["ratio_min"] for s in summary],[s["ratio_max"]-s["ratio_mean"] for s in summary]]),fmt="none",ecolor="#222",capsize=4)
ax.axhline(1,color="#D57635",ls="--");ax.set_ylabel("B1 / M2 累计耗时比");ax.set_title("20 批适用范围：密集条件获益，稀疏条件仍慢")
for i,v in enumerate(means):ax.text(i,v+.035,f"{v:.3f}",ha="center")
ax.set_ylim(0,1.35);ax.tick_params(axis="x",labelsize=10);finish("01_scope")
fig,axs=plt.subplots(1,2,figsize=(10,4.2),sharey=True)
for ax,d in zip(axs,("U","C")):
    for seed,color in zip((200,201,202),("#176EA1","#24A59D","#A377B5")):
        c,_,_=data[d,100000,seed]
        ax.plot(range(1,21),1000*(c["B1"]-c["M"]),marker="o",ms=3,label=f"seed {seed}",color=color)
    ax.axhline(0,c="#D57635",ls="--");ax.set_title(d+"  每批 100000 点");ax.set_xlabel("累计新批次数");ax.set_xticks([1,5,10,15,20]);ax.legend(fontsize=8)
axs[0].set_ylabel("累计节省时间 B1 − M2（毫秒）");fig.suptitle("累计收益转正的实际批次");fig.tight_layout();finish("02_break_even")
fig,axs=plt.subplots(1,2,figsize=(10,4.2),sharey=True)
for ax,d in zip(axs,("U","C")):
    matrix=[]
    for n in (1000,10000,100000):
        matrix.append(np.mean([data[d,n,s][0]["B1"]/data[d,n,s][0]["M"] for s in (200,201,202)],axis=0))
    im=ax.imshow(matrix,aspect="auto",vmin=0,vmax=1.25,cmap="YlGnBu")
    ax.set_yticks(range(3),["1000","10000","100000"]);ax.set_xticks([0,4,9,14,19],[1,5,10,15,20]);ax.set_xlabel("累计新批次数");ax.set_title(d+" 分布")
    for y in range(3):
        for x in (0,4,9,14,19):ax.text(x,y,f"{matrix[y][x]:.2f}",ha=("left" if x==0 else "right" if x==19 else "center"),va="center",fontsize=8,color="white" if matrix[y][x]>.7 else "#111")
axs[0].set_ylabel("每批点数");fig.colorbar(im,ax=axs,shrink=.8,label="B1 / M2");finish("03_horizon")
fig,axs=plt.subplots(1,2,figsize=(10,4.2),sharey=True)
for ax,d in zip(axs,("U","C")):
    for n,c in zip((1000,10000,100000),("#A377B5","#24A59D","#176EA1")):
        y=np.mean([np.cumsum(data[d,n,s][1]) for s in (200,201,202)],axis=0)
        ax.plot(range(1,21),y,label=f"N={n:,}",c=c)
    ax.set_title(d+" 分布");ax.set_xlabel("累计新批次数");ax.legend(fontsize=8);ax.set_xticks([1,5,10,15,20])
axs[0].set_ylabel("累计已分类细格条目数");fig.suptitle("几何状态逐渐覆盖工作区域");fig.tight_layout();finish("04_cache")
fig,ax=plt.subplots(figsize=(8,4.2))
for d,y,col in [("U",0,"#176EA1"),("C",1,"#24A59D")]:
    s=next(s for s in summary if s["distribution"]==d and s["n"]==100000)
    rs=[r["ratio20"] for r in rows if r["distribution"]==d and r["n"]==100000]
    ax.scatter(rs,[y-.12]*3,c=col,s=45,label=d+" 单种子")
    ax.plot([s["loo_min"],s["loo_max"]],[y+.12]*2,lw=6,color=col,alpha=.45)
    ax.scatter([s["ratio_mean"]],[y+.12],c=col,marker="D",s=60)
ax.axvline(1,color="#D57635",ls="--");ax.set_yticks([0,1],["U","C"]);ax.set_xlabel("20 批 B1 / M2");ax.set_ylim(-.5,1.5);ax.set_title("种子敏感性：圆点为单种子，线段为留一法均值范围");finish("05_seed_stability")
fig,ax=plt.subplots(figsize=(9,4.2))
tail=[s["tail_ratio_mean"] for s in summary]
ax.bar(labels,tail,color="#2B9D98");ax.axhline(1,color="#D57635",ls="--");ax.set_ylabel("第 16—20 批 B1 / M2");ax.set_title("后段边际成本：缓存建立后是否仍有收益")
for i,v in enumerate(tail):ax.text(i,v+.025,f"{v:.3f}",ha="center")
ax.set_ylim(0,max(tail)*1.18);ax.tick_params(axis="x",labelsize=10);finish("06_tail")
print(json.dumps(summary,ensure_ascii=False,indent=2))

