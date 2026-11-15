"""Reproduce in a new directory, preserving the published evidence snapshots."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--version", choices=["v1", "v2"], required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--prepare-only", action="store_true")
args = parser.parse_args()
root = Path(__file__).parent
source = root / "revision_v2" if args.version == "v2" else root
names = ["methods.py", "datasets.py", "supplement.py", "develop_distributions.py", "evaluate.py", "workloads.py"]
if args.version == "v2":
    names.append("methods_v2.py")
assert all((source / name).is_file() for name in names)
args.output.mkdir(parents=True, exist_ok=False)
for name in names:
    shutil.copyfile(source / name, args.output / name)
manifest = dict(version=args.version, python=sys.version,
                files={name: hashlib.sha256((args.output / name).read_bytes()).hexdigest() for name in names},
                environment=dict(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1"))
(args.output / "reproduction_manifest.json").write_text(json.dumps(manifest, indent=2))
if not args.prepare_only:
    env = dict(os.environ, **manifest["environment"])
    for name in ["supplement.py", "develop_distributions.py", "evaluate.py", "workloads.py"]:
        with (args.output / (name + ".log")).open("xb") as log:
            subprocess.run([sys.executable, "-u", str((args.output / name).resolve())],
                           cwd=args.output, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        if args.version == "v2" and name == "supplement.py":
            checks = json.loads((args.output / "results/supplement/boundary_probes.json").read_text())
            assert all(not row["failures"] for row in checks), "Boundary failures retained. Stop before evaluation."
print(args.output.resolve())
