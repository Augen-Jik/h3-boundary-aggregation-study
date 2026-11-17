"""Frozen supplementary protocol. Single-process, no concurrent timing jobs."""
import os
for k in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS"):
    os.environ[k]="1"
import json, sys, time, platform, hashlib, subprocess, tracemalloc, shutil
from pathlib import Path
from collections import Counter
import numpy as np
import h3
from pyproj import Transformer
from datasets import sample, REGIONS
from methods_v2 import LocalRecoder
from methods_count import CountRecoder

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"supplement_v3"
OUT.mkdir(exist_ok=True)
def save(name,obj):
    target=OUT/name
    tmp=target.with_suffix(target.suffix+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")
    tmp.replace(target)
def hashes():
    return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in
            ["methods.py","methods_v2.py","methods_count.py","datasets.py","run_supplement_v3.py","supplement_v3/PROTOCOL.md","test_count_recoder.py"]}
if (OUT/"environment.json").exists():
    assert json.loads((OUT/"environment.json").read_text())["hashes"]==hashes(), "Resume rejected: frozen source changed"
assert shutil.disk_usage(ROOT).free>5*1024**3, "Insufficient free space"
save("environment.json",dict(python=sys.version,platform=platform.platform(),processor=platform.processor(),
    cpu_count=os.cpu_count(),cpu=subprocess.getoutput("lscpu"),versions=h3.versions(),numpy=np.__version__,
    threads={k:os.environ[k] for k in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS")},
    source_sha=os.environ.get("GITHUB_SHA","local"),hashes=hashes(),execution="SSH persistent data disk; connect.westb.seetacloud.com port 37083",cpu_quota=Path("/sys/fs/cgroup/cpu.max").read_text().strip()))
# Existing known failures, retaining exact double-precision coordinates.
old=json.loads((ROOT/"supplement/boundary_probes.json").read_text())
save("old_failure_source.json",old)

def direct(lat,lon,rc,stream=False):
    it=(h3.latlng_to_cell(a,b,rc) for a,b in zip(lat,lon))
    return Counter(it if stream else list(it))
def shifted(n,seed,batch,shift):
    lat,lon=sample("hangzhou","U",n,seed,8,batch)
    if shift:
        f=Transformer.from_crs(4326,32651,always_xy=True)
        inv=Transformer.from_crs(32651,4326,always_xy=True)
        x,y=f.transform(lon,lat);lon,lat=inv.transform(np.asarray(x)+batch*shift,np.asarray(y))
        lat,lon=list(lat),list(lon)
    return lat,lon
def benchmark(distribution,n,seed,batches=20,shift=None):
    filename=f"cost_{distribution}_{n}_{seed}.json" if shift is None else f"drift_{shift}_{seed}.json"
    if (OUT/filename).exists():
        print("REUSE "+filename,flush=True);return
    names=["B1","B1s","M2","M3"] + (["A3"] if shift is None else [])
    data=[]
    for b in range(batches):
        lat,lon=sample("hangzhou",distribution,n,seed,8,b) if shift is None else shifted(n,seed,b,shift)
        fine=[h3.latlng_to_cell(a,c,10) for a,c in zip(lat,lon)]
        data.append((lat,lon,fine))
    # Independent correctness and workload descriptors, outside timers.
    checker=LocalRecoder(8); descriptors=[]
    for lat,lon,fine in data:
        before=len(checker.guarded);a,inside=checker.assign(lat,lon,fine)
        reference=[h3.latlng_to_cell(x,y,8) for x,y in zip(lat,lon)]
        descriptors.append(dict(new_cells=len(checker.guarded)-before,occupied=len(set(fine)),
            risk_fraction=1-sum(inside)/n,point_mismatches=sum(x!=y for x,y in zip(a,reference))))
    trials=[]
    for rep in range(3):
        objects={}; times={name:[] for name in names}; errors=[]
        rng=np.random.default_rng(np.random.SeedSequence([seed,rep,991]))
        for b,(lat,lon,fine) in enumerate(data):
            outputs={}
            for name in rng.permutation(names):
                start=time.perf_counter()
                if name in ("B1","B1s"):
                    result=direct(lat,lon,8,name=="B1s")
                else:
                    if name=="A3":obj=CountRecoder(8)
                    elif name not in objects:
                        obj=LocalRecoder(8) if name=="M2" else CountRecoder(8);objects[name]=obj
                    else:obj=objects[name]
                    result=Counter(obj.assign(lat,lon,fine)[0]) if name=="M2" else obj.count(lat,lon,fine)
                times[name].append(time.perf_counter()-start);outputs[name]=result
            errors.append({name:sum(abs(outputs[name][k]-outputs["B1"][k]) for k in outputs[name].keys()|outputs["B1"].keys()) for name in names})
        trials.append(dict(batch_s=times,count_l1_errors=errors))
    row=dict(distribution=distribution,n=n,seed=seed,batches=batches,shift_m_per_batch=shift,
             repetitions=3,trials=trials,descriptors=descriptors)
    save(filename,row);print(filename,flush=True)

for dist,n in [(d,n) for d in ("U","C") for n in (1000,10000,100000)]+[("B",10000)]:
    for seed in (300,301,302):benchmark(dist,n,seed)
for shift in (0,1000,5000):
    for seed in (400,401,402):benchmark("U",100000,seed,batches=10,shift=shift)

# Reuse the frozen distribution formulas while selecting the actual UTM zone.
# datasets.sample only distinguishes two region labels, so local wrapper replaces
# its Transformer with a narrow proxy, not its random or geometric sampling rules.
import datasets
OriginalTransformer=datasets.Transformer
class ZoneTransformer:
    zone=32650
    @staticmethod
    def from_crs(src,dst,**kwargs):
        return OriginalTransformer.from_crs(src,ZoneTransformer.zone if dst in (32650,32651) else dst,**kwargs)
cities={"beijing":(116.40,39.90,32650),"shenzhen":(114.06,22.55,32650),
        "sydney":(151.21,-33.87,32756),"reykjavik":(-21.94,64.15,32627)}
records=[]
datasets.Transformer=ZoneTransformer
for city,(lon0,lat0,zone) in cities.items():
    REGIONS[city]=(lon0,lat0);ZoneTransformer.zone=zone
    for dist in ("U","C","B"):
        for rf,rc in ((9,8),(10,8),(10,9)):
            for seed in (500,501,502):
                lat,lon=sample(city,dist,5000,seed,rc)
                fine=[h3.latlng_to_cell(a,b,rf) for a,b in zip(lat,lon)]
                ref=[h3.latlng_to_cell(a,b,rc) for a,b in zip(lat,lon)]
                obj=LocalRecoder(rc);assigned,inside=obj.assign(lat,lon,fine)
                counted=CountRecoder(rc).count(lat,lon,fine)
                reference_counts=Counter(ref)
                mismatches=[i for i,(a,b) in enumerate(zip(assigned,ref)) if a!=b]
                records.append(dict(city=city,zone=zone,distribution=dist,rf=rf,rc=rc,seed=seed,n=5000,
                    point_mismatches=len(mismatches),count_l1=sum(abs(counted[k]-reference_counts[k]) for k in counted.keys()|reference_counts.keys()),
                    risk_fraction=1-sum(inside)/5000,exceptions=obj.exceptions,
                    failures=[dict(lat=lat[i],lon=lon[i],fine=fine[i],assigned=assigned[i],reference=ref[i]) for i in mismatches[:100]]))
    print("region",city,flush=True)
datasets.Transformer=OriginalTransformer
save("new_regions.json",records)
# Regression against every preserved failure dictionary, without guessing row structure.
def failure_rows(x):
    if isinstance(x,dict):
        if "point" in x and isinstance(x["point"],list) and len(x["point"])==2:yield dict(lat=x["point"][0],lon=x["point"][1])
        for v in x.values():yield from failure_rows(v)
    elif isinstance(x,list):
        for v in x:yield from failure_rows(v)
regression=[]
for row in failure_rows(old):
    lat,lon=row["lat"],row["lon"]
    for rf,rc in ((9,8),(10,8),(10,9)):
        fine=h3.latlng_to_cell(lat,lon,rf);ref=h3.latlng_to_cell(lat,lon,rc)
        m2=LocalRecoder(rc).assign([lat],[lon],[fine])[0][0]
        m3=CountRecoder(rc).count([lat],[lon],[fine])
        regression.append(dict(lat=lat,lon=lon,rf=rf,rc=rc,m2_ok=m2==ref,m3_ok=m3==Counter([ref])))
save("failure_regression.json",regression)
# Python peak allocations; output lifetime is controlled equally across methods.
data=[]
for b in range(5):
    lat,lon=sample("hangzhou","U",100000,600,8,b)
    data.append((lat,lon,[h3.latlng_to_cell(a,c,10) for a,c in zip(lat,lon)]))
memory={}
for name in ("B1","B1s","M2","M3"):
    tracemalloc.start();obj=None;peak=0
    for lat,lon,fine in data:
        if name in ("B1","B1s"):result=direct(lat,lon,8,name=="B1s")
        else:
            if obj is None:obj=LocalRecoder(8) if name=="M2" else CountRecoder(8)
            result=Counter(obj.assign(lat,lon,fine)[0]) if name=="M2" else obj.count(lat,lon,fine)
        peak=max(peak,tracemalloc.get_traced_memory()[1]);del result
    retained,_=tracemalloc.get_traced_memory();tracemalloc.stop()
    memory[name]=dict(peak_bytes=peak,retained_bytes=retained)
save("memory.json",memory)
save("completion.json",dict(cost_workloads=21,drift_workloads=9,new_region_cases=len(records),
    new_region_points=sum(r["n"] for r in records),new_region_point_mismatches=sum(r["point_mismatches"] for r in records),
    regression_rows=len(regression),hashes=hashes()))
print("COMPLETE",flush=True)

