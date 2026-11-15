"""Additional measured scatter and an explicitly schematic method diagram."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

root = Path(__file__).parent
revision = "--revision-v2" in sys.argv
figures = root / ("figures_v2" if revision else "figures")
figures.mkdir(exist_ok=True)
source = root / ("revision_v2/results/evaluation" if revision else "snapshot/results/evaluation")
rows = [json.loads(p.read_text()) for p in source.glob("*_*_*_*.json")]
assert len(rows) == 180
colors = dict(U="#0072b2", C="#009e73", B="#d55e00")
fig, ax = plt.subplots(figsize=(6.4, 4.8))
for distribution in colors:
    points = [r for r in rows if r["distribution"] == distribution]
    ax.scatter([r["quality"]["B0"]["assignment_error"] * 100 for r in points],
               [r["quality"]["B0"]["count_error"] * 100 for r in points],
               s=22, alpha=.6, color=colors[distribution], label=distribution)
ax.plot([0, 45], [0, 45], color="gray", linestyle="--", lw=1, label="Equal rates")
ax.set(xlim=(0, 45), ylim=(0, 45), xlabel="Point assignment difference (%)",
       ylabel="Normalized count difference (%)", title="Aggregation can hide point-level changes")
ax.legend(frameon=False, loc="upper left")
fig.text(.5, .015, "Each marker is one region / distribution / resolution / seed scenario.",
         ha="center", fontsize=8)
fig.tight_layout(rect=[0, .04, 1, 1])
for ext in ["png", "pdf", "svg"]:
    fig.savefig(figures / ("point_vs_count." + ext), dpi=180)
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 4.6))
ax.set(xlim=(0, 10), ylim=(0, 6))
ax.axis("off")
boxes = [(.25, 4.1, 2.3, 1.1, "Coordinates + fine IDs\nGroup occupied cells"),
         (3.45, 4.1, 3.0, 1.1, "Full filter + margin probes\nVersioned geometry cache" if revision else "Logical parent + full filter\nVersioned geometry cache"),
         (7.35, 4.1, 2.3, 1.1, "Candidate interior\nUse parent ID"),
         (3.8, 1.9, 2.3, 1.1, "Risk / uncertainty\nEncode coordinates"),
         (7.35, 1.9, 2.3, 1.1, "Aggregate counts\nAudit against direct IDs")]
for x, y, width, height, label in boxes:
    patch = FancyBboxPatch((x, y), width, height, boxstyle="round,pad=0.08",
                          edgecolor="#334155", facecolor="#eef3f6", linewidth=1)
    ax.add_patch(patch)
    ax.text(x + width / 2, y + height / 2, label, ha="center", va="center", fontsize=9)
for start, end in [((2.65, 4.65), (3.3, 4.65)), ((6.55, 4.65), (7.2, 4.65)),
                   ((4.95, 4), (4.95, 3.15)), ((6.2, 2.45), (7.2, 2.45)),
                   ((8.5, 4), (8.5, 3.15))]:
    ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="->", color="#334155"))
ax.text(5, 5.7, "Local recoding and geometry reuse", ha="center", fontsize=13)
ax.text(5, .8, "Schematic. Full filtering is a candidate rule, with empirical correctness checks.\n"
        "Cache contains geometry only. Original coordinates are required for risk cells.",
        ha="center", fontsize=9)
fig.tight_layout()
for ext in ["png", "pdf", "svg"]:
    fig.savefig(figures / ("method_flow." + ext), dpi=180)
plt.close(fig)
