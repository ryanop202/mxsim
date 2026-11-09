"""v12b : autocollant « icône U » (USLAND) moulé sur les flancs du camion-citerne JGSX (watertruck.jm), sans toucher au modèle
ni à la texture de JG : un petit modèle à nous (watertruck_u.jm), posé avec la même position / le même angle que le camion.
La surface de la citerne est mesurée par lancer de rayons horizontaux sur le maillage JGSX ; l'autocollant suit la courbe,
0,03 ft devant, découpé autour du logo (cases hors du logo retirées). Lisible des deux côtés (un autocollant par flanc).
Run: python3 scripts/sticker_usland.py   (lit tracks/<SX1>/statue/watertruck.jm, écrit assets/props/watertruck_u.*)"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
import numpy as np
from PIL import Image
from names import FOLDERS
import props_usland as PU

SRC = f'{ROOT}/tracks/{FOLDERS["SX1"]}/statue/watertruck.jm'
STICK = dict(zc=-4.0, yc=7.7, w=2.9, h=2.4, nu=40, nv=32)      # centre on the tank side (upper flank, v12b: higher), size (ft), grid

def load_jm2(path):
    L = open(path).read().splitlines(); k = next(i for i, l in enumerate(L) if len(l.split()) == 2 and all(t.isdigit() for t in l.split()))
    nv, nt = map(int, L[k].split()); V = np.array([[float(t) for t in l.split()] for l in L[k + 1:k + 1 + nv]])
    I = np.array([int(l) for l in L[k + 1 + nv:k + 1 + nv + 3 * nt]]).reshape(-1, 3); return V, I

def raycast(O, D, A, B, C):
    """first hit distance of rays O + t D on triangles (Moller-Trumbore), inf if none."""
    e1, e2 = B - A, C - A; out = np.full(len(O), np.inf)
    for i in range(len(O)):
        p = np.cross(D[i], e2); det = np.einsum('ij,ij->i', e1, p); ok = np.abs(det) > 1e-9
        inv = np.where(ok, 1 / np.where(ok, det, 1), 0); s = O[i] - A; u = np.einsum('ij,ij->i', s, p) * inv
        q = np.cross(s, e1); v = (q @ D[i]) * inv; t = np.einsum('ij,ij->i', e2, q) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
        if hit.any(): out[i] = t[hit].min()
    return out

def build(outd=PU.OUTD):
    V, I = load_jm2(SRC); P = V[:, :3]; A, B, C = P[I[:, 0]], P[I[:, 1]], P[I[:, 2]]
    s = STICK; zs = np.linspace(s['zc'] - s['w'] / 2, s['zc'] + s['w'] / 2, s['nu']); ys = np.linspace(s['yc'] - s['h'] / 2, s['yc'] + s['h'] / 2, s['nv'])
    # texture: the U icon (dark version, readable on a light tank), mask = where the plate is kept (logo + small margin)
    W = 512; img = Image.new('RGB', (W, W), (250, 250, 250))
    PU.logo(img, 'ICON', (W * 0.04, W * 0.04, W * 0.96, W * 0.96), on='light')
    from scipy import ndimage as ndi
    lum = np.array(img.convert('L')).astype(float); mask = ndi.binary_dilation(lum < 200, iterations=10)
    tex = Image.new('RGB', (1024, 1024), (250, 250, 250)); tex.paste(img, (8, 8))
    m = PU.Mesh(1024, 1024); rect = (8, 8, 8 + W, 8 + W); report = {}
    for side, x0, dx in (('gauche', -12.0, 1.0), ('droite', 12.0, -1.0)):
        O = np.array([[x0, y, z] for y in ys for z in zs]); D = np.tile([dx, 0.0, 0.0], (len(O), 1))
        t = raycast(O, D, A, B, C).reshape(len(ys), len(zs))
        X = x0 + dx * (t - 0.03)                                             # 0.03 ft in front of the tank
        report[side] = (round(float(np.nanmin(X[np.isfinite(X)])), 2), round(float(np.nanmax(X[np.isfinite(X)])), 2), int(np.isinf(t).sum()))
        for j in range(len(ys) - 1):
            for i in range(len(zs) - 1):
                # texture coords: u along the viewer's right (+z seen from -x, -z seen from +x), v up
                uu = lambda ii: (ii / (len(zs) - 1)) if dx > 0 else 1 - ii / (len(zs) - 1)
                cu, cv = (uu(i) + uu(i + 1)) / 2, 1 - (j + 0.5) / (len(ys) - 1)
                if not mask[int(cv * (W - 1)), int(cu * (W - 1))]: continue
                if not np.all(np.isfinite(t[j:j + 2, i:i + 2])): continue
                q = [np.array([X[jj, ii], ys[jj], zs[ii]]) for jj, ii in ((j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i))]
                N = np.cross(q[1] - q[0], q[3] - q[0]); N = N / np.linalg.norm(N)
                if np.sign(N[0]) == np.sign(dx): N = -N                         # facing out of the tank
                uv = [m.uv_px(rect[0] + uu(ii) * W, rect[1] + (1 - (jj / (len(ys) - 1))) * W) for jj, ii in ((j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i))]
                m.tri_fan(q, N, uv)
    tex.save(f'{outd}/watertruck_u.png'); nvx, ntr = m.write(f'{outd}/watertruck_u.jm', (8, 0.5, 0.5, 0.5, 0.5))
    return report, ntr

if __name__ == '__main__':
    rep, ntr = build()
    for k, (a, b, miss) in rep.items(): print(f'flanc {k} : surface x {a} .. {b} ft, rayons sans impact {miss}')
    print('watertruck_u.jm :', ntr, 'triangles')
