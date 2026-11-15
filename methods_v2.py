"""Conservative empirical margin guard, not a global geometric certificate."""
import h3

from methods import LocalRecoder as FullRecoder


class LocalRecoder(FullRecoder):
    margin_degrees = 1e-9

    def __init__(self, coarse_resolution):
        super().__init__(coarse_resolution)
        self.guarded = {}

    def classify(self, fine):
        key = (fine, self.coarse_resolution, self.version, "full-margin-v2-1e-9")
        if key in self.guarded:
            return self.guarded[key]
        parent, safe = super().classify(fine)
        if safe:
            # Keep the library's full boundary. Probe a small neighbourhood
            # around every vertex so touching cells conservatively fall back.
            for lat, lon in h3.cell_to_boundary(fine):
                for dy, dx in [(0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    probe = h3.latlng_to_cell(lat + dy * self.margin_degrees,
                                              lon + dx * self.margin_degrees,
                                              self.coarse_resolution)
                    if probe != parent:
                        safe = False
                        break
                if not safe:
                    break
        self.guarded[key] = (parent, safe)
        return parent, safe
