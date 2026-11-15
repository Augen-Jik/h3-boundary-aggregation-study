import csv
import json
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

root = Path(__file__).parent
rows = [json.loads(p.read_text()) for p in (root / "workload_snapshot/results/workloads").glob("*.json")
        if not p.name.startswith("smoke_")]
assert len(rows) == 18
assert {(r["distribution"], r["n"], r["seed"]) for r in rows} == {
    (dist, n, seed) for dist in ["U", "C"] for n in [1000, 10000, 100000] for seed in [100, 101, 102]}
groups = defaultdict(list)
for r in rows:
    assert r["repetitions"] == 7 and r["batches"] == 20
    groups[(r["distribution"], r["n"])].append(r)
output = root / "results/derived"
summary = []
colors = {"B0": "#777777", "B1": "#0072b2", "M": "#d55e00", "A1": "#009e73"}
for (dist, n), records in sorted(groups.items()):
    curves = {}
    for method in colors:
        curves[method] = np.array([np.median([np.cumsum(t["batch_s"][method]) for t in r["trials"]], axis=0)
                                   for r in records])
    for batches in [1, 5, 20]:
        row = dict(distribution=dist, points_per_batch=n, batches=batches, seeds=3,
                   repetitions_per_seed=7)
        for method in colors:
            values = curves[method][:, batches - 1]
            row[method + "_cumulative_seed_mean_s"] = float(values.mean())
            row[method + "_seed_min_s"] = float(values.min())
            row[method + "_seed_max_s"] = float(values.max())
        ratios = curves["B1"][:, batches - 1] / curves["M"][:, batches - 1]
        row["direct_over_local_ratio_mean"] = float(ratios.mean())
        row["geometry_entries_mean"] = float(np.mean([
            sum(r["trials"][0]["new_cells"][:batches]) for r in records]))
        row["retained_python_bytes_mean_at_20"] = float(np.mean([r["retained_python_bytes"] for r in records]))
        summary.append(row)
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    for method, values in curves.items():
        ax.plot(range(1, 21), values.mean(axis=0), label=method, color=colors[method])
        ax.fill_between(range(1, 21), values.min(axis=0), values.max(axis=0), alpha=.12, color=colors[method])
    ax.set(xlabel="Different new batches", ylabel="Cumulative runtime (s)",
           title=f"{dist} synthetic workload / {n:,} points per batch", xlim=(1, 20), ylim=(0, None))
    ax.legend(frameon=False)
    fig.text(.5, .015, "Lines average seed medians; shading spans 3 seeds; 7 timing repeats each.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=[0, .04, 1, 1])
    for extension in ["png", "svg", "pdf"]:
        fig.savefig(root / "figures" / f"cumulative_{dist}_{n}.{extension}", dpi=180)
    plt.close(fig)
with (output / "workload_summary.csv").open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=list(summary[0]))
    writer.writeheader()
    writer.writerows(summary)
lines = ["| 分布 | 每批点数 | 批数 | B1累计秒 | M累计秒 | B1/M |", "|---|---|---|---|---|---|"]
for r in summary:
    lines.append(f"| {r['distribution']} | {r['points_per_batch']} | {r['batches']} | "
                 f"{r['B1_cumulative_seed_mean_s']:.4f} | {r['M_cumulative_seed_mean_s']:.4f} | "
                 f"{r['direct_over_local_ratio_mean']:.3f} |")
(output / "workload_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps(dict(workloads=len(rows), ratio_range=[min(r["direct_over_local_ratio_mean"] for r in summary),
                                                       max(r["direct_over_local_ratio_mean"] for r in summary)])))
