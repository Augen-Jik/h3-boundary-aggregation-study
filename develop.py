"""Run only preregistered development seeds 0--4, never evaluation seeds."""
import json
from pathlib import Path

import h3
import numpy as np
from pyproj import Transformer

from methods import LocalRecoder, metrics

forward = Transformer.from_crs(4326, 32651, always_xy=True)
inverse = Transformer.from_crs(32651, 4326, always_xy=True)
cx, cy = forward.transform(120.15, 30.25)
rows = []
for seed in range(5):
    xy = np.random.default_rng(seed).uniform(-5000, 5000, (10000, 2)) + [cx, cy]
    lon, lat = inverse.transform(xy[:, 0], xy[:, 1])
    for fine_resolution, coarse_resolution in [(9, 8), (10, 8), (10, 9)]:
        fine = [h3.latlng_to_cell(a, b, fine_resolution) for a, b in zip(lat, lon)]
        reference = [h3.latlng_to_cell(a, b, coarse_resolution) for a, b in zip(lat, lon)]
        recoder = LocalRecoder(coarse_resolution)
        output, interior = recoder.assign(lat, lon, fine)
        result = dict(seed=seed, fine_resolution=fine_resolution, coarse_resolution=coarse_resolution,
                      versions=h3.versions(), n=len(lat), occupied=len(set(fine)),
                      recoding_ratio=1 - sum(interior) / len(lat),
                      interior_false_safe=sum(s and a != b for s, a, b in zip(interior, output, reference)),
                      local=metrics(output, reference),
                      parent=metrics([h3.cell_to_parent(h, coarse_resolution) for h in fine], reference),
                      exceptions=recoder.exceptions)
        rows.append(result)
        print(json.dumps(result), flush=True)
out = Path(__file__).parent / "results/development"
out.mkdir(parents=True, exist_ok=True)
(out / "uniform_correctness.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
assert all(r["interior_false_safe"] == 0 and r["local"]["assignment_error"] == 0 for r in rows)
