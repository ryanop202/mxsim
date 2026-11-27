"""v10 : le vrai quartier autour de l'arène (Nanterre / La Défense) - photo aérienne IGN BD ORTHO (Géoplateforme WMTS,
licence ouverte Etalab 2.0), posée à plat tout autour du bâtiment.

L'arène du jeu est agrandie en plan (LP.PLAN_K) : la photo l'est autant, autour de la même origine, pour que les rues tombent
au bon endroit autour de la façade. Repère : pistes/paris-2026/stade_paris/src/arena/survey.local_to_l93 (relevé LiDAR du bâtiment).
Sortie : dalles plates de 1024 ft (texture 512 px, 2 ft/px), à 0,1 ft au-dessus du sol, rien sous le bâtiment.
Le jeu penche une statue selon le sol sous son origine : toutes les dalles ont leur origine sur un même point plat du terrain.

  appelé par build_paris.py ; cache des tuiles IGN : ../ign_paris (hors dépôt)."""
import os
import sys
import math
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "pistes/paris-2026/stade_paris", "src"))
CACHE = os.path.join(os.path.dirname(ROOT), "ign_paris")
Z = 18                      # ~0,39 m / px à Paris
SIDE = 6144.0               # côté du carré couvert, en ft du jeu (~1,15 km réels autour du centre)
TILE = 1024.0               # ft par dalle
TPX = 512                   # px par dalle (2 ft / px)
CELL = 16.0                 # maille des dalles (ft) ; une maille sous le bâtiment est retirée
LIFT = 0.1

# ---------------------------------------------------------------- Lambert 93 <-> WGS84 (RGF93 ~ WGS84)
A_, F_ = 6378137.0, 1 / 298.257222101; E_ = math.sqrt(2 * F_ - F_ * F_)
L0, P0, P1, P2, X0, Y0 = math.radians(3.0), math.radians(46.5), math.radians(44.0), math.radians(49.0), 700000.0, 6600000.0


def _liso(p):
    return np.log(np.tan(np.pi / 4 + p / 2) * ((1 - E_ * np.sin(p)) / (1 + E_ * np.sin(p))) ** (E_ / 2))


_N1, _N2 = A_ / math.sqrt(1 - E_ ** 2 * math.sin(P1) ** 2), A_ / math.sqrt(1 - E_ ** 2 * math.sin(P2) ** 2)
_n = math.log(_N2 * math.cos(P2) / (_N1 * math.cos(P1))) / (_liso(P1) - _liso(P2))
_c = _N1 * math.cos(P1) / _n * math.exp(_n * _liso(P1))
_ys = Y0 + _c * math.exp(-_n * _liso(P0))


def l93_to_lonlat(X, Y):
    X, Y = np.asarray(X, float), np.asarray(Y, float)
    R = np.hypot(X - X0, _ys - Y); g = np.arctan2(X - X0, _ys - Y)
    lon = L0 + g / _n; L = -np.log(R / _c) / _n
    lat = 2 * np.arctan(np.exp(L)) - np.pi / 2
    for _ in range(8):
        lat = 2 * np.arctan(np.exp(L) * ((1 + E_ * np.sin(lat)) / (1 - E_ * np.sin(lat))) ** (E_ / 2)) - np.pi / 2
    return np.degrees(lon), np.degrees(lat)


def merc_px(lon, lat, z=Z):
    """pixel global WebMercator (tuiles 256 px) au niveau z."""
    n = 2 ** z * 256; la = np.radians(lat)
    return (np.asarray(lon) + 180) / 360 * n, (1 - np.log(np.tan(la) + 1 / np.cos(la)) / np.pi) / 2 * n


def tile(z, x, y):
    import subprocess, time
    os.makedirs(CACHE, exist_ok=True); p = os.path.join(CACHE, "%d_%d_%d.jpg" % (z, x, y))
    url = ("https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&STYLE=normal"
           "&TILEMATRIXSET=PM&TILEMATRIX=%d&TILEROW=%d&TILECOL=%d&FORMAT=image/jpeg" % (z, y, x))
    for k in range(5):
        try:
            if os.path.exists(p) and os.path.getsize(p) > 500:
                return np.asarray(Image.open(p).convert("RGB"))
        except Exception:
            pass
        subprocess.run(["curl", "-s", "--max-time", "30", "-o", p, url]); time.sleep(0.3 * (k + 1))
    return np.full((256, 256, 3), (95, 100, 95), np.uint8)


def photo(gx, gz, OX, OZ, K, FT):
    """couleur IGN aux points du jeu (gx, gz en ft) : jeu -> repère local réel (m) -> L93 -> lon/lat -> pixel WebMercator."""
    from arena.survey import local_to_l93
    KX, KY, DY, DX = (K, K, 0.0, 0.0) if np.isscalar(K) else (tuple(K) + (0.0,))[:4]   # v37 : stade resserré en travers (X x KX, Y x KY + DY) ; v39 : + DX
    Xr, Yr = ((gx - OX) / FT - DX) / KX, ((OZ - gz) / FT - DY) / KY
    E, N = local_to_l93(Xr, Yr); lon, lat = l93_to_lonlat(E, N); px, py = merc_px(lon, lat)
    tx0, ty0 = int(np.floor(px.min() / 256)), int(np.floor(py.min() / 256)); tx1, ty1 = int(px.max() // 256), int(py.max() // 256)
    M = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256, 3), np.uint8)
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            M[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = tile(Z, tx, ty)
    u, v = px - tx0 * 256 - 0.5, py - ty0 * 256 - 0.5
    return np.dstack([map_coordinates(M[..., c].astype(float), [v, u], order=1, mode="nearest") for c in range(3)])


def add(OUT, FOLDER, H, S, poly_mx, OX, OZ, K, FT):
    """dalles IGN dans OUT/statue + lignes ajoutées à statues et variants/statues_* ; poly_mx : contour du bâtiment (ft)."""
    from matplotlib.path import Path as MPath
    N = H.shape[0]; ext = (N - 1) * S
    # origine commune sur un sol plat du terrain (coin Nord-Ouest du carré, loin du bâtiment)
    org = None
    for o in np.arange(6.0, 200.0, 2.0):
        i0, i1, j0, j1 = int((o - 4) / S), int((o + 4) / S) + 1, int((o - 4) / S), int((o + 4) / S) + 1
        if float(np.abs(H[i0:i1, j0:j1]).max()) < 1e-4 and not MPath(poly_mx).contains_point((o, o)):
            org = (o, o); break
    assert org, "pas de sol plat pour l'origine des dalles"
    bld = MPath(poly_mx); half = SIDE / 2; n_t = int(SIDE // TILE); lines = []; nt = 0
    for a in range(n_t):
        for b in range(n_t):
            x0, z0 = OX - half + a * TILE, OZ - half + b * TILE
            cs = np.arange(0, TILE, CELL); CX, CZ = np.meshgrid(x0 + cs, z0 + cs)
            corners = [(CX, CZ), (CX + CELL, CZ), (CX, CZ + CELL), (CX + CELL, CZ + CELL)]
            keep = np.ones(CX.shape, bool)
            for qx, qz in corners:
                keep &= ~bld.contains_points(np.c_[qx.ravel(), qz.ravel()]).reshape(CX.shape)
            if not keep.any():
                continue
            # texture : centre des pixels
            pv = x0 + (np.arange(TPX) + 0.5) * TILE / TPX; PX, PZ = np.meshgrid(pv, z0 + (np.arange(TPX) + 0.5) * TILE / TPX)
            img = np.clip(photo(PX, PZ, OX, OZ, K, FT), 0, 255).astype(np.uint8)
            name = "ign_%d_%d" % (a, b)
            Image.fromarray(img).save(os.path.join(OUT, "statue", name + ".png"), optimize=True)
            V, I = [], []
            for (i, j) in zip(*np.nonzero(keep)):
                xa, za = x0 + j * CELL, z0 + i * CELL; k0 = len(V)
                for dx, dz in ((0, 0), (CELL, 0), (CELL, CELL), (0, CELL)):
                    xx, zz = xa + dx, za + dz
                    V.append((xx - org[0], LIFT, zz - org[1], 0.0, 1.0, 0.0, (xx - x0) / TILE, 1.0 - (zz - z0) / TILE))
                I += [k0, k0 + 1, k0 + 2, k0, k0 + 2, k0 + 3, k0, k0 + 2, k0 + 1, k0, k0 + 3, k0 + 2]   # les deux faces
            txt = ["JM1", "0 0 0 0 0", "%d %d" % (len(V), len(I) // 3)] + [" ".join("%.4f" % c for c in v) for v in V] + [str(i) for i in I] + [""]
            open(os.path.join(OUT, "statue", name + ".jm"), "w", newline="\n").write("\n".join(txt))
            lines.append("[%.4f 0.0000 %.4f] 0.000000 @%s/statue/%s.jm @%s/statue/%s.png null" % (org[0], org[1], FOLDER, name, FOLDER, name))
            nt += 1
    for f in ["statues"] + ["variants/" + v for v in os.listdir(os.path.join(OUT, "variants")) if v.startswith("statues")]:
        p = os.path.join(OUT, f); s = open(p).read().rstrip("\n") + "\n"
        open(p, "w", newline="\n").write(s + "\n".join(lines) + "\n")
    print("quartier IGN : %d dalles de %.0f ft autour du bâtiment (x%s comme l'arène), origine %s" % (nt, TILE, K, org))
    return nt
