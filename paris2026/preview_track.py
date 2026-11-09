"""Ajoute le terrain de la piste Paris 2026 à l'aperçu 3D de l'arène (stade_paris/build/obj + textures).
  py -3.15 -I paris2026/preview_track.py && py -3.15 -I stade_paris/src/preview_web.py
Ce n'est pas un rendu du jeu."""
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "scripts"))
import layout_paris as LP          # noqa: E402
from shading import lambert_shadow  # noqa: E402

T = os.path.join(ROOT, "tracks", "USLAND2026SupercrossParis")
SB = os.path.join(ROOT, "stade_paris", "build")
n, s, hmin, hmax = open(os.path.join(T, "terrain.hf")).read().split()
s, hmin, hmax = float(s), float(hmin), float(hmax)
H = np.asarray(Image.open(os.path.join(T, "terrain.png")), np.float64) / 65535 * (hmax - hmin) + hmin
x0, x1, z0, z1 = 280.0, 826.0, 390.0, 797.0          # sol de l'arène agrandie (+ marge), en ft
step = 1.5
xs = np.arange(x0, x1 + 1e-6, step); zs = np.arange(z0, z1 + 1e-6, step)
J = np.clip(np.round(xs / s).astype(int), 0, H.shape[1] - 1); I = np.clip(np.round(zs / s).astype(int), 0, H.shape[0] - 1)
h = np.maximum(H[np.ix_(I, J)], 0.0)
XX, ZZ = np.meshgrid(xs, zs)
X = (XX - LP.OX) / LP.FT; Y = -(ZZ - LP.OZ) / LP.FT; Zm = h / LP.FT + 0.01
ny, nx = h.shape
U = (XX - x0) / (x1 - x0); V = 1 - (ZZ - z0) / (z1 - z0)
idx = np.arange(nx * ny).reshape(ny, nx)
a, b, c, d = idx[:-1, :-1], idx[:-1, 1:], idx[1:, :-1], idx[1:, 1:]
F = np.concatenate([np.stack([a, c, b], -1).reshape(-1, 3), np.stack([b, c, d], -1).reshape(-1, 3)])
P = np.c_[X.ravel(), Y.ravel(), Zm.ravel()]
# orienter les faces vers le haut
e1 = P[F[:, 1]] - P[F[:, 0]]; e2 = P[F[:, 2]] - P[F[:, 0]]
if np.cross(e1, e2)[:, 2].mean() < 0:
    F = F[:, ::-1]
gz, gx = np.gradient(h, step)
Nn = np.dstack([gx / LP.FT * 0 - gx, -(-gz), np.ones_like(h)]).reshape(-1, 3)
Nn = np.c_[-gx.ravel(), gz.ravel(), np.ones(h.size)]
Nn /= np.linalg.norm(Nn, axis=1, keepdims=True)
with open(os.path.join(SB, "obj", "_piste.obj"), "w") as f:
    f.write("o piste\n")
    f.write("\n".join("v %.3f %.3f %.3f" % tuple(p) for p in P) + "\n")
    f.write("\n".join("vt %.5f %.5f" % (u, v) for u, v in zip(U.ravel(), V.ravel())) + "\n")
    f.write("\n".join("vn %.4f %.4f %.4f" % tuple(q) for q in Nn) + "\n")
    f.write("usemtl piste\n")
    f.write("\n".join("f %d/%d/%d %d/%d/%d %d/%d/%d" % (a + 1, a + 1, a + 1, b + 1, b + 1, b + 1, c + 1, c + 1, c + 1) for a, b, c in F) + "\n")
# texture : terre ombrée (relief), un peu plus foncée sur les obstacles
k = 0.5
xs2 = np.arange(x0, x1, k); zs2 = np.arange(z0, z1, k)
J2 = np.clip(np.round(xs2 / s).astype(int), 0, H.shape[1] - 1); I2 = np.clip(np.round(zs2 / s).astype(int), 0, H.shape[0] - 1)
h2 = np.maximum(H[np.ix_(I2, J2)], 0.0)
# v2 (étape 2) : la terre de Saint-Thibéry (décal 'track', 26 ft) x l'ombrage exporté (shading.ppm), comme dans le jeu
NN = H.shape[0]
shd = np.fromfile(os.path.join(T, "shading.ppm"), dtype=np.uint8, offset=len(b"P6\n%d %d\n255\n" % (NN, NN))).reshape(NN, NN, 3)[:, :, 0]
sh2 = shd[np.ix_(I2, J2)].astype(float)
tile_px = int(round(26.0 / k))
tra = np.asarray(Image.open(os.path.join(T, "ext", "USLAND2026SX1", "decal", "track.png")).convert("RGBA").resize((tile_px, tile_px), Image.LANCZOS), float)
dp = int(round(8.0 / k))                                     # terre de base (dirt.ppm), répétée tous les ~8 ft
base_t = np.asarray(Image.open(os.path.join(T, "ext", "USLAND2026SX1", "tiles", "dirt.ppm")).convert("RGB").resize((dp, dp), Image.LANCZOS), float)
rep = lambda a, n: np.tile(a, (int(np.ceil(h2.shape[0] / n)) + 1, int(np.ceil(h2.shape[1] / n)) + 1, 1))[:h2.shape[0], :h2.shape[1]]
base = rep(base_t, dp)
dec_ = rep(tra, tile_px); al = dec_[..., 3:4] / 255.0
dirt = base * (1 - al) + dec_[..., :3] * al
col = dirt * (sh2 / 175.0)[..., None]
im = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).resize((2048, 2048), Image.LANCZOS)
im.save(os.path.join(SB, "textures", "piste_top.png"))
print("terrain d'aperçu :", P.shape[0], "sommets,", F.shape[0], "triangles")
