"""Rendu logiciel (numpy, z-buffer) des modèles .jm de l'habillage, quand l'aperçu three.js n'est pas disponible (WebGL bloqué).
Ce n'est PAS un rendu du jeu : il sert à vérifier les formes, les faces (rien de transparent), les logos (à l'endroit) et la pose
sur le terrain. Faces arrière masquées comme en jeu (une face vue de dos n'est pas dessinée).

  py -3.15 -I paris2026/rendu_objets.py      -> paris2026/apercu/v9_*.png
"""
import os
import re
import sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
T = os.path.join(ROOT, "tracks", "USLAND2026SupercrossParis")
D = os.path.join(T, "statue", "paris")
AP = os.path.join(HERE, "apercu")


def read_jm(path):
    L = open(path).read().splitlines(); nv, nt = map(int, L[2].split())
    V = np.array([[float(t) for t in l.split()[:8]] for l in L[3:3 + nv]]); I = np.array([int(l) for l in L[3 + nv:3 + nv + 3 * nt]]).reshape(-1, 3)
    return V, I


class Scene:
    def __init__(self):
        self.items = []

    def add(self, P, N, UV, I, tex, two=False):
        self.items.append((np.asarray(P, float), np.asarray(N, float), np.asarray(UV, float), np.asarray(I, int), tex, two))

    def add_jm(self, name, tex, x=0.0, y=0.0, z=0.0, yaw=0.0, ground=0.0):
        V, I = read_jm(os.path.join(D, name)); c, s = np.cos(yaw), np.sin(yaw)
        P = np.empty((len(V), 3)); N = np.empty((len(V), 3))
        P[:, 0] = x + V[:, 0] * c + V[:, 2] * s; P[:, 2] = z - V[:, 0] * s + V[:, 2] * c; P[:, 1] = ground + y + V[:, 1]
        N[:, 0] = V[:, 3] * c + V[:, 5] * s; N[:, 2] = -V[:, 3] * s + V[:, 5] * c; N[:, 1] = V[:, 4]
        im = np.asarray(Image.open(os.path.join(D, tex)).convert('RGBA'), np.float64) / 255
        self.add(P, N, V[:, 6:8], I, im)

    def render(self, eye, target, W=1100, H=700, fov=50.0, sun=(-0.5, 0.75, -0.45), bg=(26, 28, 36)):
        eye, target = np.asarray(eye, float), np.asarray(target, float)
        f = target - eye; f /= np.linalg.norm(f); r = np.cross(f, [0, 1, 0]); r /= np.linalg.norm(r); u = np.cross(r, f)
        fl = 0.5 * H / np.tan(np.radians(fov) / 2); sun = np.asarray(sun, float); sun /= np.linalg.norm(sun)
        zb = np.full((H, W), np.inf); img = np.zeros((H, W, 3)); img[:] = np.array(bg) / 255
        for P, N, UV, I, tex, two in self.items:
            q = P - eye; cx, cy, cz = q @ r, q @ u, q @ f
            sx, sy = W / 2 + fl * cx / np.maximum(cz, 1e-3), H / 2 - fl * cy / np.maximum(cz, 1e-3)
            th, tw = tex.shape[:2]
            for a, b, c in I:
                if min(cz[a], cz[b], cz[c]) < 0.3:
                    continue
                x0, y0, x1, y1, x2, y2 = sx[a], sy[a], sx[b], sy[b], sx[c], sy[c]
                area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
                if abs(area) < 1e-9 or (area > 0 and not two):            # vue de dos -> pas dessinée (comme en jeu)
                    continue
                xa, xb = int(max(0, np.floor(min(x0, x1, x2)))), int(min(W - 1, np.ceil(max(x0, x1, x2))))
                ya, yb = int(max(0, np.floor(min(y0, y1, y2)))), int(min(H - 1, np.ceil(max(y0, y1, y2))))
                if xa > xb or ya > yb:
                    continue
                X, Y = np.meshgrid(np.arange(xa, xb + 1) + 0.5, np.arange(ya, yb + 1) + 0.5)
                w0 = ((x1 - X) * (y2 - Y) - (x2 - X) * (y1 - Y)) / area; w1 = ((x2 - X) * (y0 - Y) - (x0 - X) * (y2 - Y)) / area; w2 = 1 - w0 - w1
                ins = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
                if not ins.any():
                    continue
                iz = w0 / cz[a] + w1 / cz[b] + w2 / cz[c]; z = 1 / iz
                sub = zb[ya:yb + 1, xa:xb + 1]; ok = ins & (z < sub)
                if not ok.any():
                    continue
                p0, p1, p2 = w0 / cz[a] * z, w1 / cz[b] * z, w2 / cz[c] * z
                uu = p0 * UV[a, 0] + p1 * UV[b, 0] + p2 * UV[c, 0]; vv = p0 * UV[a, 1] + p1 * UV[b, 1] + p2 * UV[c, 1]
                tx = np.clip((uu % 1.0001) * (tw - 1), 0, tw - 1).astype(int); ty = np.clip((1 - vv % 1.0001) * (th - 1), 0, th - 1).astype(int)
                col = tex[ty, tx]
                ok &= col[..., 3] > 0.5
                n = (p0[..., None] * N[a] + p1[..., None] * N[b] + p2[..., None] * N[c]); n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
                if area > 0:
                    n = -n
                lam = 0.42 + 0.68 * np.clip(n @ sun, 0, 1)
                sub[ok] = z[ok]; img[ya:yb + 1, xa:xb + 1][ok] = np.clip(col[..., :3][ok] * lam[ok][:, None], 0, 1)
        return Image.fromarray((img * 255).astype(np.uint8))


def terrain_patch(sc, x0, x1, z0, z1, step=1.0):
    n, s, hmin, hmax = open(os.path.join(T, "terrain.hf")).read().split(); s, hmin, hmax = float(s), float(hmin), float(hmax)
    Hm = np.asarray(Image.open(os.path.join(T, "terrain.png")), np.float64) / 65535 * (hmax - hmin) + hmin
    xs, zs = np.arange(x0, x1, step), np.arange(z0, z1, step); X, Z = np.meshgrid(xs, zs)
    from scipy.ndimage import map_coordinates
    Y = map_coordinates(Hm, [Z / s, X / s], order=1)
    gy, gx = np.gradient(Y, step); Nn = np.dstack([-gx, np.ones_like(Y), -gy]); Nn /= np.linalg.norm(Nn, axis=-1, keepdims=True)
    P = np.c_[X.ravel(), Y.ravel(), Z.ravel()]; ny, nx = X.shape; idx = np.arange(ny * nx).reshape(ny, nx)
    a, b, c, d = idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()
    I = np.r_[np.c_[a, c, b], np.c_[a, d, c]]
    tex = np.ones((2, 2, 4)); tex[..., :3] = np.array([150, 112, 76]) / 255
    sc.add(P, Nn.reshape(-1, 3), np.zeros((len(P), 2)), I, tex, two=True)
    return lambda x, z: float(map_coordinates(Hm, [[z / s], [x / s]], order=1)[0])


def statues():
    out = []
    for l in open(os.path.join(T, "statues")):
        m = re.match(r'\[([-\d.]+) ([-\d.]+) ([-\d.]+)\] ([-\d.]+) @\S+?/statue/paris/(\S+) @\S+?/statue/paris/(\S+)', l)
        if m:
            out.append((float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)), m.group(5), m.group(6)))
    return out


def scene_at(cx, cz, half, step=1.0):
    sc = Scene(); h = terrain_patch(sc, cx - half, cx + half, cz - half, cz + half, step)
    for x, y, z, a, mdl, tex in statues():
        if abs(x - cx) < half and abs(z - cz) < half:
            sc.add_jm(mdl, tex, x, y, z, a, ground=h(x, z))
    return sc, h


if __name__ == "__main__":
    os.makedirs(AP, exist_ok=True)
    # objets seuls (sur un sol plat)
    for name, tex, views in (('tuff_arc.jm', 'tuff_arc_honda.png', [((6, 3, 7), (0, 0.7, 0)), ((-6, 3, -7), (0, 0.7, 0))]),
                             ('mur.jm', 'mur_motoverte.png', [((10, 5, 14), (0, 2.5, 0)), ((-9, 6, -12), (0, 2.5, 0))]),
                             ('minerva.jm', 'minerva.png', [((14, 7, 22), (0, 5, 0)), ((3, 4, 9), (0, 7, -2))]),
                             ('arche_50.jm', 'arche_50.png', [((30, 14, 45), (0, 12, 0)), ((-20, 30, -30), (0, 18, 0))]),
                             ('semi.jm', 'semi_ktm.png', [((40, 15, 30), (0, 6, -20)), ((-35, 12, -70), (0, 6, -20))])):
        ims = []
        for eye, tgt in views:
            sc = Scene()
            g = np.ones((2, 2, 4)); g[..., :3] = np.array([150, 112, 76]) / 255
            sc.add([(-80, -0.01, -90), (80, -0.01, -90), (80, -0.01, 60), (-80, -0.01, 60)], [(0, 1, 0)] * 4, np.zeros((4, 2)), [(0, 2, 1), (0, 3, 2)], g)
            sc.add_jm(name, tex); ims.append(sc.render(eye, tgt, 700, 460))
        out = Image.new('RGB', (1400, 460)); out.paste(ims[0], (0, 0)); out.paste(ims[1], (700, 0))
        out.save(os.path.join(AP, 'v9_%s.png' % name.split('.')[0])); print(name)
