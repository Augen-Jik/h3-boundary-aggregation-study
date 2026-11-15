"""Point-assignment methods. Geometry cache never stores point-level answers."""
from collections import Counter

import h3


class LocalRecoder:
    def __init__(self, coarse_resolution):
        self.coarse_resolution = coarse_resolution
        self.version = tuple(sorted(h3.versions().items()))
        self.parents = {}
        self.full_cells = {}
        self.exceptions = []

    def classify(self, fine):
        key = (fine, self.coarse_resolution, self.version, "full-v1")
        if key in self.parents:
            return self.parents[key]
        parent = h3.cell_to_parent(fine, self.coarse_resolution)
        resolution = h3.get_resolution(fine)
        group = (parent, resolution)
        safe = False
        if not h3.is_pentagon(fine) and not h3.is_pentagon(parent):
            try:
                if group not in self.full_cells:
                    polygon = h3.LatLngPoly(h3.cell_to_boundary(parent))
                    self.full_cells[group] = set(h3.h3shape_to_cells_experimental(
                        polygon, resolution, contain="full"))
                safe = fine in self.full_cells[group]
            except h3.H3BaseException as error:
                self.exceptions.append(dict(fine=fine, error=repr(error)))
        self.parents[key] = (parent, safe)
        return parent, safe

    def assign(self, latitudes, longitudes, fine_cells):
        classifications = {cell: self.classify(cell) for cell in set(fine_cells)}
        output = []
        interior = []
        for lat, lon, fine in zip(latitudes, longitudes, fine_cells, strict=True):
            parent, safe = classifications[fine]
            output.append(parent if safe else h3.latlng_to_cell(lat, lon, self.coarse_resolution))
            interior.append(safe)
        return output, interior


def metrics(output, reference):
    if len(output) != len(reference) or not reference:
        raise ValueError("nonempty matched assignments required")
    n = len(reference)
    actual, target = Counter(output), Counter(reference)
    cells = actual.keys() | target.keys()
    k = min(10, len(target))
    top_actual = set(sorted(actual, key=lambda h: (-actual[h], h))[:k])
    top_target = set(sorted(target, key=lambda h: (-target[h], h))[:k])
    return dict(assignment_error=sum(a != b for a, b in zip(output, reference)) / n,
                count_error=sum(abs(actual[h] - target[h]) for h in cells) / (2 * n),
                hotspot_jaccard=len(top_actual & top_target) / len(top_actual | top_target),
                effective_k=k)
