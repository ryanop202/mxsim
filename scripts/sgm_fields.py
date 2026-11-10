"""Saint-Georges v27 (user: "les vrais champs autour", just a few fields round the ground, not the whole village).

The IGN BD ORTHO photo (Geoplateforme, open licence Etalab 2.0; work/ign_local.py resampled it into the local frame, 0.5 ft/px,
registered on the drone photo through sat170) is kept only where it shows open fields: not the woods (the tree billboards are
there), not the buildings / tarmac, and away from everything we built (dirt, gravel ring, mounds, roads, pond, yard, trees,
buildings). Writes assets/sgm/fields.png (RGBA, alpha = field mask, dithered edges) for the export (ground-draped meshes).

Run from mxsim:  MX_LAYOUT=layouts_sgm ../venv_mx/Scripts/python.exe scripts/sgm_fields.py
"""
import os, sys, json, importlib
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates, binary_opening, binary_closing, distance_transform_edt, label

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'scripts'))
LT = importlib.import_module(os.environ.get('MX_LAYOUT', 'layouts_sgm'))
SRC = os.path.join(os.path.dirname(ROOT), 'work', 'ign_local.png')
X0, Z0, RES = -380.0, -330.0, 0.5
FEATHER = 8.0                                   # ft of dithered edge

def build():
    A = np.asarray(Image.open(SRC).convert('RGB'), float); n = A.shape[0]
    xs = X0 + (np.arange(n) + 0.5) * RES; GX, GZ = np.meshgrid(xs, Z0 + (np.arange(n) + 0.5) * RES)
    # --- what the photo shows: woods = dark and textured, buildings / tarmac = grey or red roofs
    lum = A.mean(2); lb = gaussian_filter(lum, 4 / RES); tex = np.sqrt(gaussian_filter((lum - gaussian_filter(lum, 2 / RES)) ** 2, 4 / RES))
    sat = A.max(2) - A.min(2); satb = gaussian_filter(sat, 3 / RES)
    gr = gaussian_filter(A[..., 1] - A[..., 0], 3 / RES)                              # green fields: smooth (tex < 5), lum 70..80
    woods = (lb < 65) | ((tex > 6.0) & (lb < 105) & (gr > 0))                          # woods: very dark, or green and textured
    built = ((satb < 12) & (lb > 85)) | (-gr > 30)                                     # tarmac / concrete, red roofs
    ok = ~(woods | built)
    # --- what we built: dirt / gravel ring / mounds (distance to the dirt, terrain height), roads, pond, yard, trees, buildings
    DF = np.load(os.path.join(ROOT, 'build', 'sgm_dist.npy'))
    wx, wz = GX - X0, GZ - Z0                                                        # world ft (terrain origin)
    df = map_coordinates(DF, [wz.ravel(), wx.ravel()], order=1).reshape(n, n)
    H = np.load(os.path.join(ROOT, 'build', 'sgm_H.npy')); S = 0.28975
    h = map_coordinates(H, [(wz / S).ravel(), (wx / S).ravel()], order=1).reshape(n, n)
    raised = distance_transform_edt(~(np.abs(h) > 0.12)) * RES
    ok &= (df > 40.0) & (raised > 12.0)
    rd = np.full((n, n), 1e9)
    for RD in getattr(LT, 'ROADS', []) or []:
        P = np.array(RD['pts'], float)
        for p0, p1 in zip(P[:-1], P[1:]):
            dv = p1 - p0; t = np.clip(((GX - p0[0]) * dv[0] + (GZ - p0[1]) * dv[1]) / (dv @ dv), 0, 1)
            rd = np.minimum(rd, np.hypot(GX - p0[0] - t * dv[0], GZ - p0[1] - t * dv[1]) - RD['w'] / 2)
    ok &= rd > 6.0
    dec = json.load(open(os.path.join(ROOT, 'assets', 'sgm', 'decor.json')))
    from matplotlib.path import Path as MP
    pond = MP(np.array(dec['pond'])); pin = pond.contains_points(np.c_[GX.ravel(), GZ.ravel()]).reshape(n, n)
    ok &= distance_transform_edt(~pin) * RES > 14.0
    T = np.zeros((n, n), bool); tr = np.array(dec['trees'], float)
    ti, tj = ((tr[:, 1] - Z0) / RES).astype(int), ((tr[:, 0] - X0) / RES).astype(int); kk = (ti >= 0) & (ti < n) & (tj >= 0) & (tj < n)
    T[ti[kk], tj[kk]] = True   # v27: trees may stand in the fields (no hole round them)
    LD = getattr(LT, 'LIGHT_DIRT', None)
    if LD: ok &= ~((GX > LD['x'][0] - 10) & (GX < LD['x'][1] + 10) & (GZ > LD['z'][0] - 10) & (GZ < LD['z'][1] + 10))
    for BL in getattr(LT, 'BUILDINGS', []) or []:
        r = max(BL['half']) + 25.0; ok &= np.hypot(GX - BL['c'][0], GZ - BL['c'][1]) > r
    # --- clean: no specks, only real fields (>= 10000 ft2), then a dithered edge
    ok = binary_opening(ok, iterations=int(4 / RES)); ok = binary_closing(ok, iterations=int(3 / RES))
    lab, nl = label(ok); sz = np.bincount(lab.ravel()); mlum = np.bincount(lab.ravel(), lb.ravel()) / np.maximum(sz, 1); mtex = np.bincount(lab.ravel(), tex.ravel()) / np.maximum(sz, 1)
    keep = (sz * RES * RES >= 10000.0) & (mlum >= 68) & (mtex < 7.5); keep[0] = False; ok = keep[lab]   # whole fields only, no hedge scraps
    d = distance_transform_edt(ok) * RES; p = np.clip(d / FEATHER, 0, 1)
    rg = np.random.default_rng(27); alpha = (rg.random((n, n)) < p * p * (3 - 2 * p)) & ok
    img = np.dstack([np.clip(A, 0, 255), alpha * 255.0]).astype(np.uint8)
    os.makedirs(os.path.join(ROOT, 'assets', 'sgm'), exist_ok=True)
    Image.fromarray(img, 'RGBA').save(os.path.join(ROOT, 'assets', 'sgm', 'fields.png'))
    print('fields: %.0f ft2 in %d patches' % (ok.sum() * RES * RES, keep.sum()))

if __name__ == '__main__':
    build()
