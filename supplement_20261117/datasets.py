"""Synthetic metre-based observations with independent batches."""
import h3
import numpy as np
from pyproj import Transformer

REGIONS = {"hangzhou": (120.15, 30.25), "nanjing": (118.80, 32.06)}
CLUSTERS = np.array([[-2500., -2000.], [2000., 2200.], [1800., -1700.]])


def sample(region, distribution, n, seed, coarse_resolution, batch=0):
    forward = Transformer.from_crs(4326, 32651 if region == "hangzhou" else 32650, always_xy=True)
    inverse = Transformer.from_crs(forward.target_crs, 4326, always_xy=True)
    center = np.array(forward.transform(*REGIONS[region]))
    rng = np.random.default_rng(np.random.SeedSequence([seed, batch]))
    if distribution == "U":
        xy = rng.uniform(-5000, 5000, (n, 2)) + center
    elif distribution == "C":
        xy = rng.uniform(-5000, 5000, (n, 2))
        use_cluster = rng.random(n) < 0.8
        m = int(use_cluster.sum())
        # Cluster centres are fixed before measuring H3 differences.
        clusters = CLUSTERS[rng.integers(0, len(CLUSTERS), m)]
        xy[use_cluster] = np.clip(clusters + rng.normal(0, 350, (m, 2)), -5000, 5000)
        xy += center
    elif distribution == "B":
        # Include cells whose centres fall inside an expanded rectangle, then
        # retain boundary-band samples inside the registered square.
        square = center + np.array([[-6500, -6500], [6500, -6500], [6500, 6500], [-6500, 6500]])
        lon, lat = inverse.transform(square[:, 0], square[:, 1])
        cells = sorted(h3.h3shape_to_cells(h3.LatLngPoly(list(zip(lat, lon))), coarse_resolution))
        segments = {}
        for cell in cells:
            vertices = list(h3.cell_to_boundary(cell))
            for a, b in zip(vertices, vertices[1:] + vertices[:1]):
                key = tuple(sorted((a, b)))
                segments[key] = (a, b)
        starts, ends = [], []
        for a, b in segments.values():
            starts.append(forward.transform(a[1], a[0]))
            ends.append(forward.transform(b[1], b[0]))
        starts, ends = np.array(starts), np.array(ends)
        delta = ends - starts
        lengths = np.linalg.norm(delta, axis=1)
        normal = np.column_stack((-delta[:, 1], delta[:, 0])) / lengths[:, None]
        chunks = []
        remaining = n
        while remaining:
            index = rng.choice(len(starts), max(remaining * 2, 128), p=lengths / lengths.sum())
            candidates = starts[index] + rng.random((len(index), 1)) * delta[index]
            candidates += rng.uniform(-20, 20, (len(index), 1)) * normal[index]
            candidates = candidates[(np.abs(candidates - center) <= 5000).all(axis=1)][:remaining]
            chunks.append(candidates)
            remaining -= len(candidates)
        xy = np.concatenate(chunks)
    else:
        raise ValueError(distribution)
    lon, lat = inverse.transform(xy[:, 0], xy[:, 1])
    return lat.tolist(), lon.tolist()

