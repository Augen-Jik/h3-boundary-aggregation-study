"""Summaries use seeds as replicate units and preserve region/distribution strata."""
import csv
import json
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

root = Path(__file__).parent
source = root / "snapshot/results/evaluation"
rows = [json.loads(p.read_text()) for p in source.glob("*_*_*_*.json")]
assert len(rows) == 180
assert len({(r["region"], r["distribution"], r["fine"], r["coarse"], r["seed"]) for r in rows}) == 180
assert all(r["false_safe"] == 0 and r["quality"]["M"]["assignment_error"] == 0 for r in rows)
out = root / "results/derived"
out.mkdir(parents=True, exist_ok=True)
figures = root / "figures"
figures.mkdir(exist_ok=True)
groups = defaultdict(list)
for r in rows:
    groups[(r["region"], r["distribution"], r["fine"], r["coarse"])].append(r)
summary = []
for (region, distribution, fine, coarse), records in sorted(groups.items()):
    assert {r["seed"] for r in records} == set(range(100, 110))
    item = dict(region=region, distribution=distribution, fine=fine, coarse=coarse, seeds=10,
                point_evaluations=sum(r["n"] for r in records))
    for field in ["assignment_error", "count_error", "hotspot_jaccard"]:
        values = [r["quality"]["B0"][field] for r in records]
        item[field + "_mean"] = float(np.mean(values))
        item[field + "_seed_sd"] = float(np.std(values, ddof=1))
    item["recoding_ratio_mean"] = float(np.mean([r["recoding_ratio"] for r in records]))
    for method in ["B0", "B1", "M", "A1"]:
        medians = [np.median(r["warm_same_batch_timing_s"][method]) for r in records]
        item[method + "_seed_mean_median_s"] = float(np.mean(medians))
    summary.append(item)
with (out / "independent_summary.csv").open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(summary[0]))
    writer.writeheader()
    writer.writerows(summary)

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "pdf.fonttype": 42})
strata = [(region, dist) for region in ["hangzhou", "nanjing"] for dist in ["U", "C", "B"]]
pairs = [(9, 8), (10, 8), (10, 9)]
lookup = {(r["region"], r["distribution"], r["fine"], r["coarse"]): r for r in summary}
for field, title, name in [
        ("assignment_error_mean", "Logical-parent assignment difference (%)", "assignment_difference"),
        ("count_error_mean", "Logical-parent normalized count difference (%)", "count_difference"),
        ("hotspot_jaccard_mean", "Logical-parent vs direct Top-10 Jaccard", "hotspot_overlap"),
        ("recoding_ratio_mean", "Points re-encoded by the local method (%)", "recoding_ratio")]:
    scale = 1 if field.startswith("hotspot") else 100
    values = np.array([[lookup[(region, dist, fine, coarse)][field] * scale
                        for fine, coarse in pairs] for region, dist in strata])
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    image = ax.imshow(values, cmap="cividis", vmin=0,
                      vmax=1 if field.startswith("hotspot") else float(values.max()), aspect="auto")
    ax.set_xticks(range(3), [f"r{fine} to r{coarse}" for fine, coarse in pairs])
    ax.set_yticks(range(6), [region.title() + " / " + dist for region, dist in strata])
    ax.set_title(title, pad=12)
    for i in range(6):
        for j in range(3):
            ax.text(j, i, f"{values[i, j]:.2f}", ha="center", va="center",
                    color="white" if values[i, j] < (1 if field.startswith("hotspot") else values.max()) * .5 else "black")
    fig.colorbar(image, ax=ax, pad=.03)
    fig.text(.5, .015, "Each entry averages 10 independent seeds; U/C routine, B boundary stress.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=[0, .04, 1, 1])
    for extension in ["pdf", "svg", "png"]:
        fig.savefig(figures / (name + "." + extension), dpi=180)
    plt.close(fig)
print(json.dumps(dict(scenarios=len(rows), strata=len(summary),
                      point_evaluations=sum(r["n"] for r in rows), false_safe=0)))
