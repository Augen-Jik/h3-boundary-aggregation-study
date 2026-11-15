"""Distinct new batches, cold starts and increments included in each repeat."""
import json
import sys
import time
import tracemalloc
from collections import Counter
from pathlib import Path

import h3
import numpy as np

from datasets import sample
from methods import LocalRecoder

root = Path(__file__).parent
out = root / "results/workloads"
out.mkdir(parents=True, exist_ok=True)
smoke = "--smoke" in sys.argv
sizes = [1000] if smoke else [1000, 10000, 100000]
seeds = [0] if smoke else [100, 101, 102]
repeats = 1 if smoke else 7
batches = 2 if smoke else 20
for distribution in ["U", "C"]:
    for n in sizes:
        for seed in seeds:
            path = out / f"{'smoke_' if smoke else ''}{distribution}_{n}_{seed}.json"
            if path.exists():
                continue
            data = []
            for batch in range(batches):
                lat, lon = sample("hangzhou", distribution, n, seed, 8, batch)
                fine = [h3.latlng_to_cell(a, b, 10) for a, b in zip(lat, lon)]
                data.append((lat, lon, fine))
            trials = []
            for repeat in range(repeats):
                local = LocalRecoder(8)
                parents = {}
                elapsed = {name: [] for name in ["B0", "B1", "M", "A1"]}
                increments = []
                order = np.random.default_rng(seed + repeat * 1000)
                for lat, lon, fine in data:
                    results = {}
                    before = len(local.parents)
                    for name in order.permutation(list(elapsed)):
                        start = time.perf_counter()
                        if name == "B0":
                            for cell in set(fine):
                                if cell not in parents:
                                    parents[cell] = h3.cell_to_parent(cell, 8)
                            assigned = [parents[cell] for cell in fine]
                        elif name == "B1":
                            assigned = [h3.latlng_to_cell(a, b, 8) for a, b in zip(lat, lon)]
                        else:
                            recoder = local if name == "M" else LocalRecoder(8)
                            assigned, _ = recoder.assign(lat, lon, fine)
                        results[name] = Counter(assigned)
                        elapsed[name].append(time.perf_counter() - start)
                    assert results["M"] == results["B1"] == results["A1"]
                    increments.append(len(local.parents) - before)
                trials.append(dict(batch_s=elapsed, new_cells=increments))
            # Memory is measured separately and never included in timing.
            tracemalloc.start()
            local = LocalRecoder(8)
            for lat, lon, fine in data:
                local.assign(lat, lon, fine)
            retained, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            row = dict(region="hangzhou", distribution=distribution, fine=10, coarse=8,
                       n=n, seed=seed, batches=batches, repetitions=repeats,
                       trials=trials, versions=h3.versions(), retained_python_bytes=retained,
                       peak_python_bytes=peak, memory_scope="Python allocations, excludes C library RSS")
            path.write_text(json.dumps(row, indent=2))
            print(path.name, flush=True)
