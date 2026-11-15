"""Draw actual library boundaries for a preserved false-safe test point."""
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(__file__).parent
r = json.loads((root / "results/boundary_failure_geometry.json").read_text())
lat0, lon0 = r["point"]
radius = 6371008.8
fig, ax = plt.subplots(figsize=(6.6, 4.8))
for key, label, color in [("assigned", "V1 assigned parent (r8)", "#d55e00"),
                           ("reference", "Direct coarse ID (r8)", "#0072b2"),
                           ("actual_fine", "Actual fine ID (r10)", "#009e73")]:
    vertices = r["boundaries"][r[key]]
    vertices = vertices + vertices[:1]
    x = [math.radians(lon - lon0) * radius * math.cos(math.radians(lat0)) for lat, lon in vertices]
    y = [math.radians(lat - lat0) * radius for lat, lon in vertices]
    ax.plot(x, y, color=color, label=label, lw=2.6 if key == "assigned" else 1.8,
            linestyle="--" if key == "assigned" else "-", zorder=4 if key == "assigned" else 2)
ax.scatter([0], [0], marker="x", color="black", s=60, zorder=10, label="Preserved false-safe point")
ax.set(xlim=(-80, 80), ylim=(-60, 60), xlabel="East displacement (m, local tangent approximation)",
       ylabel="North displacement (m)", title="A numerical boundary case missed by the full filter")
ax.set_aspect("equal")
ax.legend(frameon=False, fontsize=8, loc="lower right")
fig.text(.5, .015, "H3 4.5.0; stored library boundaries; exact point coordinates retained in source JSON.",
         ha="center", fontsize=8)
fig.tight_layout(rect=[0, .04, 1, 1])
for extension in ["png", "svg", "pdf"]:
    fig.savefig(root / "figures" / ("boundary_failure." + extension), dpi=180)
