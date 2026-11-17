"""Count-oriented kernel reusing the unchanged empirical v2 classifier."""
from collections import Counter
import h3
from methods_v2 import LocalRecoder

class CountRecoder(LocalRecoder):
    def count(self, latitudes, longitudes, fine_cells):
        if not (len(latitudes) == len(longitudes) == len(fine_cells)):
            raise ValueError("matched input lengths required")
        occupancy = Counter(fine_cells)
        output = Counter()
        risk = set()
        for fine, n in occupancy.items():
            parent, safe = self.classify(fine)
            if safe:
                output[parent] += n
            else:
                risk.add(fine)
        for lat, lon, fine in zip(latitudes, longitudes, fine_cells, strict=True):
            if fine in risk:
                output[h3.latlng_to_cell(lat, lon, self.coarse_resolution)] += 1
        return output

