"""Image de contrôle : MNS dans le repère local + contour de plan théorique (dims.py)."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arena import survey, dims

S = 4  # px par mètre
xs, ys, h, t = survey.local_grid(-110, 130, -110, 110, 1.0 / S)
img = np.nan_to_num(np.clip(h / 46.0, 0, 1)) * 255
rgb = np.stack([img] * 3, -1).astype(np.uint8)
# lignes de niveau tous les 2 m
lv = np.floor(np.nan_to_num(h) / 2.0)
edge = (np.diff(lv, axis=0, prepend=lv[:1]) != 0) | (np.diff(lv, axis=1, prepend=lv[:, :1]) != 0)
rgb[edge] = (rgb[edge] * 0.4 + np.array([0, 90, 160]) * 0.6).astype(np.uint8)
# image : colonnes = X, lignes = -Y (Ouest en haut)
im = Image.fromarray(np.transpose(rgb, (1, 0, 2))[::-1])
d = ImageDraw.Draw(im)


def px(X, Y):
    return ((X - xs[0]) * S, (ys[-1] - Y) * S)


for name, pts, col in dims.debug_outlines():
    d.line([px(x, y) for x, y in pts], fill=col, width=2)
for gx in range(-100, 131, 10):
    d.text(px(gx, -108), str(gx), fill=(255, 255, 0))
for gy in range(-100, 101, 20):
    d.text(px(-108, gy), str(gy), fill=(255, 255, 0))
out = os.path.join(survey.ROOT, "renders", "control_plan_vs_lidar.png")
im.save(out)
print("saved", out)
