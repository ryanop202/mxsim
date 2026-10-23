"""Lightmap (shading.ppm) generator calibrated on a reference track's own shading.ppm."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import numpy as np, sys
from scipy import ndimage as ndi
def lambert_shadow(H, s, sun, shadow=True, max_dist=400.0):
    sun = np.asarray(sun, float); sun = sun / np.linalg.norm(sun)
    gz, gx = np.gradient(H, s)
    n = np.dstack([-gx, np.ones_like(H), -gz]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    lam = np.clip(n @ sun, 0, 1)
    if not shadow: return lam, np.ones_like(H)
    # horizon test along the sun azimuth (march in pixel steps)
    hx, hz = sun[0], sun[2]; hl = np.hypot(hx, hz); tan_el = sun[1] / max(hl, 1e-6)
    dx, dz = hx / hl, hz / hl
    lit = np.ones_like(H, bool); N = H.shape[0]
    ii, jj = np.mgrid[0:N, 0:N].astype(np.float32)
    for k in range(1, int(max_dist / s), 2):
        d = k * s
        hk = ndi.map_coordinates(H, [ii + dz * k, jj + dx * k], order=1, mode='nearest')
        lit &= ~(hk > H + d * tan_el + 0.05)
        if k > 40 and k % 40 == 1 and lit.all(): break
    return lam, lit.astype(float)
if __name__ == '__main__':
    sys.path.insert(0, ROOT + '/scripts'); from mxs import Track
    from PIL import Image
    f = REF + '/JGMXDesertSand/JGMXDesertSand'
    T = Track(f); Hs = T.H[::2, ::2]; ref = np.array(Image.open(f + '/shading.ppm'))[::2, ::2, 0].astype(float)
    lam, lit = lambert_shadow(Hs, T.s * 2, [0.5128, 0.50, 0.3164], shadow=True, max_dist=150)
    m = np.isfinite(ref)
    for name, feat in (('lambert', lam), ('lambert*shadow', lam * lit)):
        A = np.c_[np.ones(m.sum()), feat[m]]; coef, *_ = np.linalg.lstsq(A, ref[m], rcond=None)
        pred = A @ coef; r = np.corrcoef(pred, ref[m])[0, 1]
        print(name, 'fit shade = %.1f + %.1f*x' % tuple(coef), 'corr %.3f' % r, 'rmse %.1f' % np.sqrt(np.mean((pred - ref[m]) ** 2)))
