"""Saint-Georges v23 decor from the user's Google satellite views (registered on the drone photo, work/register_sat.py):
trees where the satellite shows trees, the pond (shape from the satellite, placed east of our start area), the east road
corridor. Writes mxsim/assets/sgm/decor.json (local ft). Run from work/sat."""
import json, os, sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0, '../../mxsim/scripts'); os.environ['MX_LAYOUT'] = 'layouts_sgm'
import build_stt as B, layouts_sgm as T

A0 = np.array(json.load(open('sat170_to_local.json'))); A1 = np.array(json.load(open('sat171_to_local.json')))
inv = lambda A: np.linalg.inv(np.vstack([A, [0, 0, 1]]))[:2]
S0 = np.asarray(Image.open('sat170.webp').convert('RGB')).astype(float); S1 = np.asarray(Image.open('sat171.webp').convert('RGB')).astype(float)
ox, oz = T.STT_ORIGIN

# ---------------- trees (satellite 170)
R, G, Bc = S0[..., 0], S0[..., 1], S0[..., 2]; L = S0.mean(2)
loc0 = ndi.uniform_filter(L, 7); var0 = ndi.uniform_filter(L * L, 7) - loc0 ** 2
tree = (G - R > 12) & (Bc > R) & (L < 105) & (L > 15) & (var0 > 25)   # this capture's trees are blue-green; the pond is flat (low variance)
tree = ndi.binary_opening(ndi.binary_closing(tree, iterations=2), iterations=2)
tree[130:200, 240:430] = ndi.binary_dilation(tree, iterations=3)[130:200, 240:430]          # under the Google label
d, iz, ix, GX, GZ = B.region_dist(1.0); mh = B.mounds_h(1.0)
side = d.shape[0]
def at(arr, x, z):
    j, i = int(round(x + ox)), int(round(z + oz))
    return arr[i, j] if 0 <= i < side and 0 <= j < side else 1e9
rg = np.random.default_rng(23); Si = inv(A0); trees = []
for z in np.arange(-330, 857, 17.0):
    for x in np.arange(-380, 807, 17.0):
        xj, zj = x + rg.uniform(-6, 6), z + rg.uniform(-6, 6)
        u, v = Si @ np.array([xj, zj, 1.0])
        if not (0 <= u < S0.shape[1] and 0 <= v < S0.shape[0]): continue
        if not tree[int(v), int(u)]: continue
        if at(d, xj, zj) < 28 or at(mh, xj, zj) > 0.2: continue
        trees.append((round(xj, 1), round(zj, 1)))
print('trees', len(trees))

# ---------------- pond (satellite 171: the user's black circle, the dark still water inside it)
R, G, Bc = S1[..., 0], S1[..., 1], S1[..., 2]; L = S1.mean(2)
ink = (L < 40) & (np.abs(R - G) < 12) & (np.abs(G - Bc) < 12)
lab, n = ndi.label(ndi.binary_dilation(ink, iterations=1))
# the circle around the pond = the ink component whose bbox is in the top-right part
best = None
for k, sl in enumerate(ndi.find_objects(lab), 1):
    h_, w_ = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
    if h_ > 80 and w_ > 100 and sl[1].start > S1.shape[1] * 0.45 and sl[0].start < S1.shape[0] * 0.3:
        if best is None or h_ * w_ > best[1]: best = (k, h_ * w_, sl)
k, _, sl = best; ring = lab == k
inside = ndi.binary_fill_holes(ring) & ~ndi.binary_dilation(ring, iterations=3)
loc = ndi.uniform_filter(L, 9); var = ndi.uniform_filter(L * L, 9) - loc ** 2
water = inside & (L < 80) & (var < 120)
water = ndi.binary_opening(ndi.binary_closing(water, iterations=3), iterations=2)
lw, nw = ndi.label(water); sizes = ndi.sum(water, lw, range(1, nw + 1)); water = lw == (int(np.argmax(sizes)) + 1)
water = ndi.binary_fill_holes(ndi.binary_closing(water, iterations=4))
from skimage.measure import find_contours
cs = max(find_contours(water.astype(float), 0.5), key=len)[::2]           # (row, col) = (v, u)
poly = np.array([A1 @ np.array([c[1], c[0], 1.0]) for c in cs])
# placed just east of our start area (its fence ~ x 340): keep the satellite shape and orientation, west edge at x 358
poly[:, 0] += 358.0 - poly[:, 0].min(); poly[:, 1] += 85.0 - poly[:, 1].mean()
from scipy.ndimage import gaussian_filter1d
poly = np.c_[gaussian_filter1d(poly[:, 0], 2, mode='wrap'), gaussian_filter1d(poly[:, 1], 2, mode='wrap')]
print('pond: %d points, x %.0f..%.0f, z %.0f..%.0f' % (len(poly), poly[:, 0].min(), poly[:, 0].max(), poly[:, 1].min(), poly[:, 1].max()))
from matplotlib.path import Path as MP
pp = MP(poly)
# keep the trees off the pond and its bank (30 ft)
def far_from_pond(t):
    dd = np.min(np.hypot(poly[:, 0] - t[0], poly[:, 1] - t[1])); return dd > 14 and not pp.contains_point(t)
trees = [t for t in trees if far_from_pond(t)]
print('trees after pond', len(trees))
json.dump(dict(trees=trees, pond=poly.round(2).tolist()), open('../../mxsim/assets/sgm/decor.json', 'w'))
# preview
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 2, figsize=(16, 9))
ax[0].imshow(S1.astype(np.uint8)); ax[0].contour(water, [0.5], colors='cyan'); ax[0].contour(ring, [0.5], colors='red', linewidths=0.6); ax[0].set_title('lac detecte (cyan)')
H = np.load('../../mxsim/build/sgm_H.npy'); S = 0.28975; x0, x1, z0, z1 = -300, 600, -250, 800
ax[1].imshow(H[int((z0 + oz) / S):int((z1 + oz) / S):4, int((x0 + ox) / S):int((x1 + ox) / S):4], extent=(x0, x1, z1, z0), cmap='terrain', vmin=-5, vmax=22)
t_ = np.array(trees); ax[1].plot(t_[:, 0], t_[:, 1], '.', color='#1b5e20', ms=3); ax[1].fill(poly[:, 0], poly[:, 1], color='#1565c0', alpha=0.8)
ax[1].set_title('arbres + lac sur le terrain'); plt.tight_layout(); plt.savefig('decor_preview.png', dpi=80)
