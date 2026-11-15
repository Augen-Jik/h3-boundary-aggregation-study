"""Frozen independent evaluation. Per-scenario files support safe resumption."""
import hashlib
import json
import platform
import sys
import time
from collections import Counter
from pathlib import Path

import h3
import numpy as np

from datasets import REGIONS, sample
from methods import LocalRecoder, metrics

root = Path(__file__).parent
out = root / "results/evaluation"
out.mkdir(parents=True, exist_ok=True)
manifest = dict(seeds=list(range(100, 110)), regions=REGIONS,
                distributions=["U", "C", "B"], pairs=[[9, 8], [10, 8], [10, 9]],
                n=10000, timing_repetitions=7, versions=h3.versions(),
                python=sys.version, platform=platform.platform(),
                files={name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                       for name in ["methods.py", "datasets.py", "evaluate.py"]})
freeze = out / "freeze.json"
if freeze.exists():
    assert json.loads(freeze.read_text()) == json.loads(json.dumps(manifest))
else:
    freeze.write_text(json.dumps(manifest, indent=2))
dev = json.loads((root / "results/development/distributions.json").read_text())
assert len(dev) == 90 and all(r["false_safe"] == 0 and r["local"]["assignment_error"] == 0 for r in dev)

for region in REGIONS:
    for distribution in manifest["distributions"]:
        for fine_resolution, coarse in manifest["pairs"]:
            for seed in manifest["seeds"]:
                path = out / f"{region}_{distribution}_{fine_resolution}_{coarse}_{seed}.json"
                if path.exists():
                    continue
                lat, lon = sample(region, distribution, manifest["n"], seed, coarse)
                start = time.perf_counter()
                fine = [h3.latlng_to_cell(a, b, fine_resolution) for a, b in zip(lat, lon)]
                upstream = time.perf_counter() - start
                reference = [h3.latlng_to_cell(a, b, coarse) for a, b in zip(lat, lon)]
                method = LocalRecoder(coarse)
                t0 = time.perf_counter()
                local, safe = method.assign(lat, lon, fine)
                setup = time.perf_counter() - t0
                parent_map = {h: h3.cell_to_parent(h, coarse) for h in set(fine)}
                parent = [parent_map[h] for h in fine]
                quality = {"B0": metrics(parent, reference), "M": metrics(local, reference)}
                false_safe = sum(s and a != b for s, a, b in zip(safe, local, reference))
                timings = {m: [] for m in ["B0", "B1", "M", "A1"]}
                # Shared Counter aggregation. All methods produce point assignments.
                def invoke(name):
                    if name == "B0":
                        assigned = [parent_map[h] for h in fine]
                    elif name == "B1":
                        assigned = [h3.latlng_to_cell(a, b, coarse) for a, b in zip(lat, lon)]
                    elif name == "M":
                        assigned, _ = method.assign(lat, lon, fine)
                    else:
                        assigned, _ = LocalRecoder(coarse).assign(lat, lon, fine)
                    return Counter(assigned)
                for name in timings:
                    invoke(name)
                order = np.random.default_rng(seed + 20000)
                for repetition in range(7):
                    for name in order.permutation(list(timings)):
                        start = time.perf_counter()
                        counts = invoke(name)
                        elapsed = time.perf_counter() - start
                        if name != "B0":
                            assert counts == Counter(reference)
                        timings[name].append(elapsed)
                result = dict(region=region, distribution=distribution, fine=fine_resolution,
                              coarse=coarse, seed=seed, n=len(lat), occupied=len(set(fine)),
                              upstream_fine_encoding_s=upstream, local_first_assignment_s=setup,
                              warm_same_batch_timing_s=timings,
                              timing_scope="warm same batch M; A1 includes rebuild; new-batch workloads separate",
                              quality=quality, false_safe=false_safe,
                              recoding_ratio=1 - sum(safe) / len(lat), exceptions=method.exceptions)
                temporary = path.with_suffix(".tmp")
                temporary.write_text(json.dumps(result, indent=2))
                temporary.replace(path)
                print(json.dumps(dict(file=path.name, false_safe=false_safe,
                                      local_error=quality["M"]["assignment_error"])), flush=True)
                if false_safe or quality["M"]["assignment_error"]:
                    raise RuntimeError("Independent evaluation failure retained; do not tune against it")
