"""Check full registered experiment coverage; no claim of global correctness."""
import hashlib
import json
import math
from pathlib import Path

root = Path(__file__).parent

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def verify(version, evaluation, workloads, seeds, cost_seeds, source):
    freeze = read(evaluation / "freeze.json")
    assert freeze["seeds"] == list(seeds)
    hashes = {}
    for name, expected in freeze["files"].items():
        actual = hashlib.sha256((source / name).read_bytes()).hexdigest()
        assert actual == expected, (version, name, "source differs from registered evaluator")
        hashes[name] = actual
    records = [read(p) for p in evaluation.glob("*_*_*_*.json")]
    expected = {(region, dist, fine, coarse, seed)
                for region in ["hangzhou", "nanjing"] for dist in ["U", "C", "B"]
                for fine, coarse in [(9, 8), (10, 8), (10, 9)] for seed in seeds}
    observed = {(r["region"], r["distribution"], r["fine"], r["coarse"], r["seed"]) for r in records}
    assert len(records) == len(expected) == len(observed) == 180 and observed == expected
    for r in records:
        assert r["n"] == 10000 and r["false_safe"] == 0
        assert r["quality"]["M"]["assignment_error"] == r["quality"]["M"]["count_error"] == 0
        assert 0 <= r["recoding_ratio"] <= 1
        for method in ["B0", "B1", "M", "A1"]:
            times = r["warm_same_batch_timing_s"][method]
            assert len(times) == 7 and all(math.isfinite(t) and t >= 0 for t in times)
    costs = [read(p) for p in workloads.glob("*.json") if not p.name.startswith("smoke_")]
    expected_costs = {(dist, n, seed) for dist in ["U", "C"]
                      for n in [1000, 10000, 100000] for seed in cost_seeds}
    assert len(costs) == 18
    assert {(r["distribution"], r["n"], r["seed"]) for r in costs} == expected_costs
    for r in costs:
        assert len(r["trials"]) == r["repetitions"] == 7 and r["batches"] == 20
        for trial in r["trials"]:
            assert len(trial["new_cells"]) == 20 and all(n >= 0 for n in trial["new_cells"])
            for method in ["B0", "B1", "M", "A1"]:
                times = trial["batch_s"][method]
                assert len(times) == 20 and all(math.isfinite(t) and t >= 0 for t in times)
    return dict(version=version, scenarios=180, point_evaluations=1800000,
                workload_sequences=18, measured_batch_method_calls=18 * 7 * 20 * 4,
                source_hashes=hashes, coverage_pass=True)

reports = [verify("v1", root / "snapshot/results/evaluation",
                  root / "workload_snapshot/results/workloads", range(100, 110), [100, 101, 102], root)]
original_boundary = read(root / "supplement/boundary_probes.json")
assert sum(len(r["failures"]) for r in original_boundary) == 4
assert sum(r["tested_points"] for r in original_boundary) == 46080
if (root / "revision_v2").exists():
    registration = read(root / "revision_v2/registration.json")
    for name, expected in registration["files"].items():
        assert hashlib.sha256((root / "revision_v2" / name).read_bytes()).hexdigest() == expected
    new_boundary = read(root / "revision_v2/results/supplement/boundary_probes.json")
    assert sum(r["tested_points"] for r in new_boundary) == 46080
    assert all(not r["failures"] for r in new_boundary)
    reports.append(verify("v2", root / "revision_v2/results/evaluation",
                          root / "revision_v2/results/workloads", range(200, 210), [200, 201, 202],
                          root / "revision_v2"))
out = root / "results/derived/experiment_coverage_audit.json"
out.write_text(json.dumps(dict(reports=reports, scope="Coverage, source binding and recorded sample consistency; finite evaluation only"), indent=2))
print(out)
