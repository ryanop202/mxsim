"""v15 : « USLAND: Supercross Paris 2026 (version Zion) » - le même tracé et les mêmes obstacles de 2026 que la version USLAND,
mais construits comme ZION.2025.SupercrossParis (son archive, paris2026/refs/zion25_full) :
  - formes des bosses, tables, whoops MESURÉES sur ZION (paris2026/data/zion_formes.npz, layout_paris mode ZION), saut central et
    triple d'arrivée ZION non retouchés ; écarts ZION ; rayon des virages ZION (28,3 ft, couloirs à 56,6 ft) ;
  - coupe en travers ZION : dessus plat de 35 ft (whoops 40 ft), flancs de 5,2 ft (whoops 2,2 ft) ;
  - appuis : le croissant d'un 180 de ZION (8,1 ft, crête à 52 ft du centre) découpé dans son relief et reposé sur chaque virage
    (comprimé sur les 90, décalé sur le 180 de 37 ft) ;
  - sol : tileinfo, texture, projections, traces de ZION ; décals ZION ; éclairage et ciel ZION ; ombrage calé sur le sien
    (294,2 x lambert + 41,3 avec son soleil).
Sortie : tracks/USLAND2026SupercrossParisZion (piste à part, la version USLAND n'est pas touchée).

  py -3.12 -I paris2026/build_zion.py      (après stade_paris/src/build.py --mx)
"""
import os
import sys
import shutil
import numpy as np
os.environ['PARIS_ZION'] = '1'
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_paris as BP          # noqa: E402
import layout_paris as LP         # noqa: E402
from PIL import Image             # noqa: E402
from scipy.ndimage import map_coordinates   # noqa: E402

BP.FOLDER = "USLAND2026SupercrossParisZion"
BP.DESC = "USLAND: Supercross Paris 2026 (version Zion)"
BP.OUT = os.path.join(BP.ROOT, "tracks", BP.FOLDER)
BP.AP = os.path.join(HERE, "apercu_zion")
ZD = BP.ZD
ZF = np.load(os.path.join(HERE, "data", "zion_formes.npz"))
LAT = dict(T=(35.1, 5.2), W=(40.0, 2.2))      # dessus plat, flanc (ft) : obstacles, whoops
ZION_R = 28.3
G, N, S = BP.G, BP.N, BP.S


def lane_zion(out, g, prof, u0, top, side):
    L = len(prof) * 0.1; c, s_ = np.cos(g['t']), np.sin(g['t']); half = top / 2 + side + 1.0
    pts = np.array([(g['x0'] + uu * c - vv * s_, g['z0'] + uu * s_ + vv * c) for uu in (u0, u0 + L) for vv in (-half, half)])
    sl, X, Z = G.window(pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max())
    dx, dz = X - g['x0'], Z - g['z0']; u = dx * c + dz * s_ - u0; v = np.abs(-dx * s_ + dz * c)
    pu = np.interp(u / 0.1, np.arange(len(prof)), prof, left=0, right=0)
    lat = np.where(v <= top / 2, 1.0, 0.5 * (1 + np.cos(np.pi * np.clip((v - top / 2) / side, 0, 1))))
    out[sl] = np.maximum(out[sl], pu * lat)


def berm_zion(out, g):
    """croissant d'un 180 de ZION (carte polaire r, angle relatif) reposé sur le virage g."""
    from engine import turn_mid_angle
    B, rr, tt = ZF['berm'], ZF['berm_r'], ZF['berm_t']
    gb = BP.berm_seg(g); mid = turn_mid_angle(gb); a = abs(gb['ang']); asc = 180.0 / a if a < 170 else 1.0
    rs = g['r'] - ZION_R; R = rr.max() + max(rs, 0) + 2
    sl, X, Z = G.window(g['cx'] - R, g['cx'] + R, g['cz'] - R, g['cz'] + R)
    dx, dz = X - g['cx'], Z - g['cz']; r = np.hypot(dx, dz) - rs
    th = np.degrees(np.angle(np.exp(1j * (np.arctan2(dz, dx) - mid)))) * asc
    val = map_coordinates(B, [(r - rr[0]) / (rr[1] - rr[0]), (th - tt[0]) / (tt[1] - tt[0])], order=1, cval=0.0)
    w = np.clip((88.0 - np.abs(th)) / 10.0, 0, 1); w = w * w * (3 - 2 * w)        # au-delà : un bloc voisin dans ZION
    out[sl] = np.maximum(out[sl], val * w)


def render_zion(path, st):
    import layouts_sx as LS
    jumps = np.zeros((N, N)); whoops = np.zeros((N, N)); berms = np.zeros((N, N)); fmx = np.zeros((N, N)); secs = []
    for g in path.segs:
        if g['kind'] == 'S':
            for prof, u0, name in g['sections']:
                lay = whoops if 'whoops' in name else jumps
                lane_zion(lay, g, prof, u0, *LAT['T'])
                for it in LS.COMBOS[name]['items']:
                    if it[0].startswith('whoops'):
                        i0, i1 = int(it[1] / 0.1), int(it[2] / 0.1)
                        lane_zion(whoops, g, prof[i0:i1], u0 + it[1], *LAT['W'])
                if name == LP.L3_SEC:                           # butte ZION : sa largeur mesurée
                    it = [i for i in LS.COMBOS[name]['items'] if 'butte' in i[0]][0]
                    i0, i1 = int(it[1] / 0.1), int(it[2] / 0.1)
                    BP.render_wide(jumps, g, prof[i0:i1], u0 + it[1], *LP.Z25_BUTTE_W)
                secs.append(dict(lane=g['tag'], name=name, u0=round(u0, 1), L=round(len(prof) * 0.1, 1), H=round(float(prof.max()), 2),
                                 items=[(i[0], round(i[1], 1), round(i[2], 1)) for i in LS.COMBOS[name]['items']]))
        elif g.get('berm'):
            berm_zion(berms, g)
    BP.REPORT['sections'] = secs
    return jumps, whoops, berms, fmx


def zion_ground(OUT, FOLDER):
    """après l'export : tileinfo ZION (6 tuiles) + Road / Grass de la version USLAND, tilemap renuméroté, éclairage + ciel ZION,
    ombrage recalculé avec le soleil ZION et sa formule."""
    import re
    zt = open(os.path.join(ZD, "tileinfo")).read()
    zt = zt.replace("@ZION.2025.SupercrossParis/roost/", "@%s/ztile/" % FOLDER).replace("@ZION.2025.SupercrossParis/tile/", "@%s/ztile/" % FOLDER)
    ours = open(os.path.join(OUT, "tileinfo")).read().split("addtile")
    pick = [b for b in ours if re.search(r"name (Road|Grass)", b)]
    zb = [b for b in zt.split("addtile") if b.strip()]
    open(os.path.join(OUT, "tileinfo"), "w", newline=chr(10)).write("addtile".join(zb + pick) + "addtile" + chr(10))
    shutil.copytree(os.path.join(ZD, "tile"), os.path.join(OUT, "ztile"), dirs_exist_ok=True)
    tm = np.fromfile(os.path.join(OUT, "tilemap"), np.uint8)
    remap = np.array([0, 0, 0, 3, 4, 4, 5, 4, 6, 7] + [6] * 246, np.uint8)
    remap[tm.max() + 1:] = 6
    remap[tm].astype(np.uint8).tofile(os.path.join(OUT, "tilemap"))
    lt = [l for l in open(os.path.join(ZD, "lighting")).read().splitlines() if not l.startswith(("flare_element", "flare_point"))]
    lt = [l.replace("@ZION.2025.SupercrossParis/sky/", "@%s/zsky/" % FOLDER) for l in lt]
    open(os.path.join(OUT, "lighting"), "w", newline=chr(10)).write(chr(10).join(lt) + chr(10))
    shutil.copytree(os.path.join(ZD, "sky"), os.path.join(OUT, "zsky"), dirs_exist_ok=True)
    n, s, hmin, hmax = open(os.path.join(OUT, "terrain.hf")).read().split(); s, hmin, hmax = float(s), float(hmin), float(hmax)
    H = np.asarray(Image.open(os.path.join(OUT, "terrain.png")), float) / 65535 * (hmax - hmin) + hmin
    from shading import lambert_shadow
    sun = np.array([12049, 12000, -8049.0]); sun /= np.linalg.norm(sun)
    lam, _ = lambert_shadow(H, s, list(sun), shadow=False); sh = np.clip(294.2 * lam + 41.3, 0, 255).astype(np.uint8)
    BP.ppm(os.path.join(OUT, "shading.ppm"), sh); BP.ppm(os.path.join(OUT, "shadingx2.ppm"), (sh // 2).astype(np.uint8))
    BP.REPORT['sol_zion'] = dict(tuiles=len(zb) + len(pick), ombrage_plat=int(np.median(sh)))


_export0 = BP.export


def export_zion(*a, **k):
    _export0(*a, **k)
    zion_ground(BP.OUT, BP.FOLDER)


BP.render = render_zion
BP.export = export_zion

if __name__ == "__main__":
    BP.main()
