"""Recompute reported v2 summaries from preserved trials, without new experiments."""
import csv
import json
import math
import statistics as st
from pathlib import Path

root=Path(__file__).parent
rows=list(csv.DictReader((root/'results/derived_v2/workload_summary.csv').open(encoding='utf-8-sig')))
checked=[]
for row in rows:
    dist,n,k=row['distribution'],int(row['points_per_batch']),int(row['batches'])
    records=[json.loads((root/f'revision_v2/results/workloads/{dist}_{n}_{seed}.json').read_text()) for seed in [200,201,202]]
    medians={m:[st.median(sum(t['batch_s'][m][:k]) for t in r['trials']) for r in records] for m in ['B0','B1','M','A1']}
    for method,values in medians.items():
        assert math.isclose(st.mean(values),float(row[f'{method}_cumulative_seed_mean_s']),rel_tol=1e-12)
    ratio=st.mean(a/b for a,b in zip(medians['B1'],medians['M']))
    assert math.isclose(ratio,float(row['direct_over_local_ratio_mean']),rel_tol=1e-12)
    assert math.isclose(st.mean(r['retained_python_bytes'] for r in records),float(row['retained_python_bytes_mean_at_20']),rel_tol=1e-12)
    entries=st.mean(st.mean(sum(t['new_cells'][:k]) for t in r['trials']) for r in records)
    assert math.isclose(entries,float(row['geometry_entries_mean']),rel_tol=1e-12)
    checked.append(dict(distribution=dist,n=n,batches=k,paired_seed_ratio=ratio,summary_matches=True))
evaluation=[json.loads(p.read_text()) for p in (root/'revision_v2/results/evaluation').glob('*.json') if p.name!='freeze.json']
assert len(evaluation)==180
assert all(r['false_safe']==0 and r['quality']['M']['assignment_error']==r['quality']['M']['count_error']==0 for r in evaluation)
result=dict(date='2026-11-15',new_physical_experiments=False,recomputed_summary_rows=len(checked),
            summary_checks=checked,v2_evaluation_records=len(evaluation),
            v2_recorded_interface_exceptions=sum(len(r['exceptions']) for r in evaluation),
            timing_scope=dict(M_constructor='outside measured interval',A1_constructor='inside each batch interval',
                              M_cold_geometry_and_new_cells='inside interval',fine_encoding='outside interval',
                              workload_correctness='Counter equality after timing; separate evaluation checks point assignment'),
            unresolved=['No component timing or per-cache hit counts','No global geometric proof',
                        'M constructor exclusion has not been separately quantified','Only three cost seeds; no significance claim'])
(root/'results/derived/current_results_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in result.items() if k!='summary_checks'},ensure_ascii=False))
