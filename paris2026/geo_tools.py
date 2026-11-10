"""Point dans polygone (vectorisé, par tranches pour les grilles 4097²)."""
import numpy as np
from matplotlib.path import Path as _MPath


def inside(pts, poly, chunk=2_000_000):
    mp = _MPath(np.asarray(poly, float))
    pts = np.asarray(pts, float)
    out = np.zeros(len(pts), bool)
    for i in range(0, len(pts), chunk):
        out[i:i + chunk] = mp.contains_points(pts[i:i + chunk])
    return out
