"""Predeclared numerical-boundary probes and unchanged-data strong baseline."""
import json
import time
from collections import Counter
from pathlib import Path

import h3
import numpy as np

from datasets import REGIONS, sample
from methods_v2 import LocalRecoder

root = Path(__file__).parent
out = root / "results/supplement"
out.mkdir(parents=True, exist_ok=True)
boundary = []
for region in REGIONS:
    for fine_resolution, coarse in [(9, 8), (10, 8), (10, 9)]:
        lat, lon = sample(region, "U", 10000, 0, coarse)
        cells = sorted({h3.latlng_to_cell(a, b, fine_resolution) for a, b in zip(lat, lon)})[:128]
        points = []
        for cell in cells:
            vertices = list(h3.cell_to_boundary(cell))
            for a, b in zip(vertices, vertices[1:] + vertices[:1]):
                for p in [a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)]:
                    points.extend([p, (np.nextafter(p[0], np.inf), p[1]),
                                   (np.nextafter(p[0], -np.inf), p[1]),
                                   (p[0] + 1e-7, p[1] + 1e-7),
                                   (p[0] - 1e-7, p[1] - 1e-7)])
        actual_fine = [h3.latlng_to_cell(a, b, fine_resolution) for a, b in points]
        target = [h3.latlng_to_cell(a, b, coarse) for a, b in points]
        method = LocalRecoder(coarse)
        assigned, safe = method.assign([p[0] for p in points], [p[1] for p in points], actual_fine)
        failures = [dict(point=list(p), actual_fine=f, assigned=a, reference=t, interior=s)
                    for p, f, a, t, s in zip(points, actual_fine, assigned, target, safe) if a != t]
        boundary.append(dict(region=region, fine=fine_resolution, coarse=coarse, tested_points=len(points),
                             source_cells=len(cells), failures=failures, interior_points=sum(safe)))
(out / "boundary_probes.json").write_text(json.dumps(boundary, indent=2))
print("boundary", [(r["region"], r["fine"], r["coarse"], len(r["failures"])) for r in boundary], flush=True)
unchanged = []
for n in [10000, 100000]:
    lat, lon = sample("hangzhou", "U", n, 100, 8)
    reference = Counter(h3.latlng_to_cell(a, b, 8) for a, b in zip(lat, lon))
    timings = dict(direct=[], saved_counts_copy=[])
    for repeat in range(7):
        for method in (list(timings) if repeat % 2 else list(reversed(timings))):
            start = time.perf_counter()
            if method == "direct":
                result = Counter(h3.latlng_to_cell(a, b, 8) for a, b in zip(lat, lon))
            else:
                result = reference.copy()
            elapsed = time.perf_counter() - start
            assert result == reference
            timings[method].append(elapsed)
    unchanged.append(dict(n=n, seed=100, timings_s=timings, scope="same unchanging dataset; saved counts already available",
                          setup_cost="initial direct encoding measured by direct path; retention and invalidation outside scope"))
(out / "unchanged_data_baseline.json").write_text(json.dumps(unchanged, indent=2))
