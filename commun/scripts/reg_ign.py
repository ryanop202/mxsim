"""register the IGN z19 mosaic onto sat170 (both north-up): scale / small rotation search, FFT correlation of gradient images."""
import json, numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, sobel, rotate
def grad(a):
    a = gaussian_filter(a, 1.5); g = np.hypot(sobel(a, 0), sobel(a, 1)); g = g - g.mean(); return g / (g.std() + 1e-9)
S = np.asarray(Image.open('sat/sat170.jpg').convert('L'), float); gs = grad(S); h, w = gs.shape
I0 = Image.open('ign_z19.jpg').convert('L'); best = None
for k in np.linspace(0.54, 0.65, 23):
    for rot in (-2, -1, 0, 1, 2):
        I = np.asarray(I0.resize((int(I0.width * k), int(I0.height * k)), Image.BILINEAR), float)
        if rot: I = rotate(I, rot, reshape=False, order=1)
        gi = grad(I); H, W = gi.shape
        F = np.fft.rfft2(gi); T = np.zeros_like(gi); T[:h, :w] = gs
        c = np.fft.irfft2(F * np.conj(np.fft.rfft2(T)), s=gi.shape)
        j = np.unravel_index(np.argmax(c), c.shape); v = c[j] / (h * w)
        if best is None or v > best[0]: best = (v, k, rot, j)
    print('k %.3f best so far %s' % (k, best[:3]), flush=True)
v, k, rot, (ty, tx) = best; print('best', best)
json.dump(dict(k=k, rot=rot, tx=int(tx), ty=int(ty), score=v), open('ign_to_sat170.json', 'w'))
