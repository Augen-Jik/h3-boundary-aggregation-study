"""Development-only counterexample, with fixed seed and metre-based sampling."""
import json
from pathlib import Path

import h3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pyproj import Transformer

out = Path(__file__).parent / "results" / "pilot"
out.mkdir(parents=True, exist_ok=True)
forward = Transformer.from_crs("EPSG:4326", "EPSG:32651", always_xy=True)
inverse = Transformer.from_crs("EPSG:32651", "EPSG:4326", always_xy=True)
cx, cy = forward.transform(120.15, 30.25)
rng = np.random.default_rng(0)
xy = rng.uniform(-5000, 5000, (1000, 2)) + [cx, cy]
lon, lat = inverse.transform(xy[:, 0], xy[:, 1])
fine = [h3.latlng_to_cell(a, b, 9) for a, b in zip(lat, lon)]
parent = [h3.cell_to_parent(h, 8) for h in fine]
direct = [h3.latlng_to_cell(a, b, 8) for a, b in zip(lat, lon)]
bad = [i for i in range(len(fine)) if parent[i] != direct[i]]
if not bad:
    raise RuntimeError("No counterexample in preregistered pilot")
i = bad[0]
record = dict(seed=0, n=1000, fine_resolution=9, coarse_resolution=8,
              versions=h3.versions(), mismatch_count=len(bad),
              point=dict(latitude=float(lat[i]), longitude=float(lon[i]),
                         fine=fine[i], logical_parent=parent[i], direct_coarse=direct[i]))
(out / "counterexample.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
fig, ax = plt.subplots(figsize=(7, 6))
for cell, label, color in [(parent[i], "Logical parent (r8)", "#d55e00"),
                            (direct[i], "Direct encoding (r8)", "#0072b2"),
                            (fine[i], "Fine cell (r9)", "#009e73")]:
    boundary = list(h3.cell_to_boundary(cell))
    boundary.append(boundary[0])
    x, y = forward.transform([v[1] for v in boundary], [v[0] for v in boundary])
    ax.plot(np.asarray(x) - xy[i, 0], np.asarray(y) - xy[i, 1], color=color, label=label)
ax.scatter([0], [0], color="black", marker="x", label="Same observation point", zorder=5)
ax.set(xlabel="East displacement (m)", ylabel="North displacement (m)",
       title="H3 hierarchy and direct coarse encoding")
ax.set_aspect("equal")
ax.legend()
fig.tight_layout()
for ext in ["png", "pdf", "svg"]:
    fig.savefig(out / ("counterexample." + ext), dpi=180)
print(json.dumps(record))
