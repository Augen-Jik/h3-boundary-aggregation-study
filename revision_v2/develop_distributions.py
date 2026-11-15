import json
from pathlib import Path

import h3
from datasets import REGIONS, sample
from methods_v2 import LocalRecoder
from methods import metrics

out = Path(__file__).parent / "results/development"
out.mkdir(parents=True, exist_ok=True)
rows = []
for region in REGIONS:
    for distribution in ["U", "C", "B"]:
        for seed in range(5):
            for fine_resolution, coarse in [(9, 8), (10, 8), (10, 9)]:
                lat, lon = sample(region, distribution, 10000, seed, coarse)
                fine = [h3.latlng_to_cell(a, b, fine_resolution) for a, b in zip(lat, lon)]
                target = [h3.latlng_to_cell(a, b, coarse) for a, b in zip(lat, lon)]
                method = LocalRecoder(coarse)
                assigned, safe = method.assign(lat, lon, fine)
                r = dict(region=region, distribution=distribution, seed=seed,
                         fine=fine_resolution, coarse=coarse, n=len(lat),
                         local=metrics(assigned, target),
                         parent=metrics([h3.cell_to_parent(h, coarse) for h in fine], target),
                         recoding_ratio=1 - sum(safe) / len(lat),
                         false_safe=sum(s and a != b for s, a, b in zip(safe, assigned, target)))
                rows.append(r)
                print(json.dumps(r), flush=True)
(out / "distributions.json").write_text(json.dumps(rows, indent=2))
assert len(rows) == 90
assert all(r["false_safe"] == 0 and r["local"]["assignment_error"] == 0 for r in rows)
