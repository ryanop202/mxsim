"""Saint-Georges v26 (user: no mountains in the background, it is farmland there): a sky side of the SX1 sky box with the
mountains / desert replaced. Above `cut` the original sky is kept; from `cut` down to the horizon the sky colour of the cut
row (smoothed) fades into a pale haze; below the horizon, flat fields in perspective (green / straw / ploughed patches,
dark tree lines), which the night export then darkens like the rest of the sky."""
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d, gaussian_filter

def flatten(src, dst, cut=0.33, horizon=0.47, seed=1):
    a = np.asarray(Image.open(src).convert('RGB')).astype(float); H, W, _ = a.shape
    yc, yh = int(cut * H), int(horizon * H)
    top = gaussian_filter1d(a[yc - 6:yc].mean(0), 25, axis=0, mode='wrap')            # (W, 3) sky colour just above the cut
    haze = np.array([196.0, 204.0, 214.0])
    for y in range(yc, yh):
        t = (y - yc) / max(1, yh - yc); t = t * t * (3 - 2 * t)
        a[y] = top * (1 - t) + haze * t
    # fields: ground-plane coordinates for every pixel below the horizon (depth ~ 1 / (y - horizon))
    r = np.random.default_rng(seed); ys = np.arange(yh, H); depth = 1.0 / ((ys - yh + 2) / H)
    X = (np.arange(W)[None, :] / W - 0.5) * depth[:, None] * 3.0; Z = depth[:, None] * np.ones((1, W))
    nz = gaussian_filter(r.normal(size=(512, 512)), 18, mode='wrap'); nz = (nz - nz.mean()) / nz.std()
    nz2 = gaussian_filter(r.normal(size=(512, 512)), 4, mode='wrap'); nz2 = (nz2 - nz2.mean()) / nz2.std()
    ii = (np.floor(Z * 9.0).astype(int)) % 512; jj = (np.floor(X * 9.0).astype(int)) % 512
    t_ = np.clip(0.5 + 0.35 * nz[ii, jj], 0, 1)[..., None]
    g = np.array([84.0, 104.0, 58.0]) * (1 - t_) + np.array([132.0, 118.0, 76.0]) * t_
    g = g * (1 + 0.04 * nz2[ii, jj])[..., None]
    hedge = np.abs(nz[(ii + 97) % 512, (jj + 211) % 512]) < 0.035
    g[hedge] = [52, 66, 40]
    fade = np.clip((ys - yh) / (0.06 * H), 0, 1)[:, None, None]                        # hazy near the horizon
    g = g * fade + haze * (1 - fade)
    a[yh:] = gaussian_filter(g, (0.8, 0.8, 0))
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(dst)

if __name__ == '__main__':
    import sys; flatten(sys.argv[1], sys.argv[2])
