"""Register and run a separate post-diagnosis revision with fresh seeds."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).parent
revision = root / "revision_v2"
revision.mkdir(exist_ok=False)
for name in ["methods.py", "methods_v2.py", "datasets.py"]:
    (revision / name).write_bytes((root / name).read_bytes())
for name in ["supplement.py", "develop_distributions.py", "evaluate.py", "workloads.py"]:
    text = (root / name).read_text().replace("from methods import LocalRecoder", "from methods_v2 import LocalRecoder")
    # metrics is shared and remains in the original module.
    text = text.replace("from methods_v2 import LocalRecoder, metrics", "from methods_v2 import LocalRecoder\nfrom methods import metrics")
    if name == "evaluate.py":
        text = text.replace("range(100, 110)", "range(200, 210)").replace('["methods.py", "datasets.py", "evaluate.py"]', '["methods.py", "methods_v2.py", "datasets.py", "evaluate.py"]')
    if name == "workloads.py":
        text = text.replace("[100, 101, 102]", "[200, 201, 202]")
    (revision / name).write_text(text)
record = dict(reason="Four numerical-boundary false-safe records in v1; no point-ID exception list",
              revision="full-margin-v2", margin_degrees=1e-9,
              independent_seeds=list(range(200, 210)), cost_seeds=[200, 201, 202],
              interpretation="Empirical finite guard; no proof of global zero error",
              files={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in revision.glob("*.py")})
(revision / "registration.json").write_text(json.dumps(record, indent=2))
env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
for name in ["supplement.py", "develop_distributions.py", "evaluate.py", "workloads.py"]:
    with (revision / (name + ".log")).open("xb") as log:
        subprocess.run([sys.executable, "-u", str(revision / name)], cwd=revision, env=env,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    if name == "supplement.py":
        results = json.loads((revision / "results/supplement/boundary_probes.json").read_text())
        assert all(not r["failures"] for r in results), "Boundary failure retained; stop expansion"
print("revision_v2_complete", flush=True)
