"""v43 (user): the US-flag skirt of Crowd5 (2022 Miami Beach Race crowd picture) recoloured as a French flag (vertical
blue / white / red, folds kept from a blurred luminance). Writes mxsim/assets/crowd/Crowd5_fr.png."""
import numpy as np, sys
from PIL import Image
from scipy.ndimage import gaussian_filter, binary_closing, uniform_filter
G = 'C:/Program Files (x86)/MX Simulator/2022Miamibeachrace/billboard/'
im = Image.open(G + 'Crowd5.png').convert('RGBA'); a = np.asarray(im).astype(float); r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
Y, X = np.mgrid[0:1024, 0:1024]; lum = 0.3 * r + 0.59 * g + 0.11 * b; mx = a[..., :3].max(2); mn = a[..., :3].min(2)
skin = (r > b + 30) & (g > b + 5) & (r < g + 75) & (r > 100) & ~(r > g + 45)
box = (X >= 436) & (X <= 494) & (Y >= 953) & (al > 40)
red = box & (r > g + 45) & (r > b + 40); white = box & (mn > 140) & (mx - mn < 60)
canton = box & (Y <= 990) & (X >= 443) & (X <= 483) & ~skin
low = box & (Y >= 1005) & (X <= 452) & ((b >= r + 10) | (mn > 140))
m = binary_closing(red | white | canton | low, iterations=1) & box
m = m & ~skin | (box & skin & (uniform_filter(m.astype(float), 5) > 0.55))      # pinkish stripe edges inside the flag
xs = X[m]; x0, x1 = np.percentile(xs, 2), np.percentile(xs, 98)
L = lum * m; w = gaussian_filter(m.astype(float), 3.0); Ls = gaussian_filter(L, 3.0) / np.maximum(w, 1e-3)
sh = np.clip(Ls / np.median(Ls[m]), 0.6, 1.15)
blue = np.array([0, 85, 164.]); wht = np.array([240, 240, 240.]); rd = np.array([239, 65, 53.])
t = (X - x0) / (x1 - x0); col = np.where((t < 1 / 3)[..., None], blue, np.where((t < 2 / 3)[..., None], wht, rd))
out = a.copy(); out[..., :3][m] = (col * sh[..., None])[m]
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA').save(sys.argv[1] if len(sys.argv) > 1 else 'mxsim/assets/crowd/Crowd5_fr.png')
print('flag pixels', int(m.sum()))
