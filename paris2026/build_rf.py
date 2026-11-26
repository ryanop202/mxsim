"""v18 : « USLAND: Supercross Paris 2026 (version RF) » - le même tracé et les mêmes obstacles de 2026 que la version USLAND, mais
avec les formes de RF Anaheim 1 2026 (refs/rf/sx2026r01anaheim1.medium.saf, mesures : mesure_rf.py -> data/rf_a1_formes.*) :
  - bosses, tables, whoops, saut d'arrivée, table à double étage : profils RF (layout_paris mode RF), écarts RF (~10,5 ft) ;
  - coupe en travers RF : dessus plat de 34 ft, flancs de 7 ft ;
  - whoops : « garde nos whoops dans la version RF » -> celles de la version Zion (Saint-Georges x1,15, murets plats de 3 ft) avec
    des boudins SX TOUR dessus ; 9 (comme A1) : les 11 ne tiennent pas avec la table et les 2 bosses RF derrière (39 ft de trop) ;
  - virages RF : profil radial mesuré (180 : crête 8 ft ; 90 : petit appui de 3,9 ft hors de la ligne), qui monte de l'entrée vers
    la sortie comme sur A1, reposé sur nos virages (même ligne de course : décalé de r - r_RF) ;
  - sol RF : décals de A1 (terre de piste « ontrack » en 3 rangées le long du tour, terre « offtrack » partout, contreplaqué le long
    du mur, usure des lignes droites / bosses / sauts / 180 / whoops / départ) et traces de pneus de A1 ;
  - gardé de la version USLAND : le saut du milieu (appel + butte) et les tremplins FMX (« le saut du freestyle, tu le gardes »),
    l'arène, l'habillage, l'éclairage ; dalles grises sous les camions (comme la version Zion v17).
Sortie : tracks/USLAND2026SupercrossParisRF (piste à part).

  py -3.12 -I paris2026/build_rf.py      (après stade_paris/src/build.py --mx)
"""
import os
import sys
import shutil
import numpy as np
os.environ['PARIS_RF'] = '1'
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_paris as BP          # noqa: E402
import layout_paris as LP         # noqa: E402

BP.FOLDER = "USLAND2026SupercrossParisRF"
BP.DESC = "USLAND: Supercross Paris 2026 (version RF)"
BP.OUT = os.path.join(BP.ROOT, "tracks", BP.FOLDER)
BP.AP = os.path.join(HERE, "apercu_rf")
RFF = LP.RFF
RFD = os.path.join(os.path.dirname(BP.ROOT), "rf_ext", "sx2026r01anaheim1")      # archive RF extraite (extract_saf.py refs/rf/...)
TOP, SIDE = (float(v) for v in RFF['lat'])
G, N, S = BP.G, BP.N, BP.S


def lane_rf(out, g, prof, u0):
    """coupe RF : dessus plat TOP ft, flancs en cosinus sur SIDE ft."""
    L = len(prof) * 0.1; c, s_ = np.cos(g['t']), np.sin(g['t']); half = TOP / 2 + SIDE + 1.0
    pts = np.array([(g['x0'] + uu * c - vv * s_, g['z0'] + uu * s_ + vv * c) for uu in (u0, u0 + L) for vv in (-half, half)])
    sl, X, Z = G.window(pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max())
    dx, dz = X - g['x0'], Z - g['z0']; u = dx * c + dz * s_ - u0; v = np.abs(-dx * s_ + dz * c)
    pu = np.interp(u / 0.1, np.arange(len(prof)), prof, left=0, right=0)
    lat = np.where(v <= TOP / 2, 1.0, 0.5 * (1 + np.cos(np.pi * np.clip((v - TOP / 2) / SIDE, 0, 1))))
    out[sl] = np.maximum(out[sl], pu * lat)


def berm_rf(out, g):
    """virage RF : profil radial mesuré sur A1 (normalisé) x hauteur de crête selon l'avancement dans le virage (entrée -> sortie),
    ligne de course de A1 calée sur la nôtre ; au-delà des bouts du virage, fondu sur 15 % de l'angle (entrée) / 40 % (sortie)."""
    from engine import turn_mid_angle
    k = 'b180' if abs(g['ang']) > 135 else 'b90'
    rr, P, tt, cc, ride = (np.asarray(RFF[k + s_], float) for s_ in ('_r', '_p', '_t', '_c', '_ride'))
    P = np.maximum(P, 0.0) / P.max()
    gb = BP.berm_seg(g); mid = turn_mid_angle(gb); half_a = np.radians(abs(gb['ang'])) / 2
    rs = g['r'] - float(ride); R = rr.max() + max(rs, 0.0) + 2.0
    sl, X, Z = G.window(g['cx'] - R, g['cx'] + R, g['cz'] - R, g['cz'] + R)
    dx, dz = X - g['cx'], Z - g['cz']; rp = np.hypot(dx, dz) - rs
    rel = np.angle(np.exp(1j * (np.arctan2(dz, dx) - mid)))
    t = rel * -np.sign(gb['ang']) / half_a                       # -1 entrée, +1 sortie (sens de course)
    crest = np.interp(np.clip(t, -1, 1), tt, cc)
    over = np.clip((np.abs(t) - 1.0) / np.where(t > 0, 0.40, 0.15), 0, 1); crest = crest * (1 - over * over * (3 - 2 * over))   # sortie : fondu plus long (pas de marche)
    h = np.interp(rp, rr, P, left=0.0, right=0.0) * crest * (rp > 0)
    out[sl] = np.maximum(out[sl], h)


def render_rf(path, st):
    import layouts_sx as LS
    jumps = np.zeros((N, N)); whoops = np.zeros((N, N)); berms = np.zeros((N, N)); fmx = np.zeros((N, N)); secs = []
    for g in path.segs:
        if g['kind'] == 'S':
            for prof, u0, name in g['sections']:
                if name == LP.L3_SEC:                       # saut du freestyle : celui de la version USLAND
                    BP.render_mid(jumps, g, prof, u0, name)
                else:
                    for it in LS.COMBOS[name]['items']:
                        i0, i1 = int(it[1] / 0.1), min(int(it[2] / 0.1) + 1, len(prof))
                        if it[0].startswith('whoops'):     # « garde nos whoops » : celles de la version Zion (coupe USLAND + murets)
                            BP.render_lane_block(G, whoops, g, prof[i0:i1], u0 + it[1], BP.TW)
                            BP.whoops_walls(whoops, g, prof, u0, it)
                        else:
                            lane_rf(jumps, g, prof[i0:i1], u0 + it[1])
                secs.append(dict(lane=g['tag'], name=name, u0=round(u0, 1), L=round(len(prof) * 0.1, 1), H=round(float(prof.max()), 2),
                                 items=[(i[0], round(i[1], 1), round(i[2], 1)) for i in LS.COMBOS[name]['items']]))
        elif g.get('berm'):
            berm_rf(berms, g)
    BP.REPORT['sections'] = secs
    return jumps, whoops, berms, fmx


def paddock(OUT):
    """dalles grises (tuile Road) sous les camions, à plus de 25 ft du tour et du départ (comme la version Zion v17) ; renvoie la zone."""
    import re
    from scipy.spatial import cKDTree
    from starts import StartRoute
    P = np.array([tuple(map(float, re.match(r"\[([-\d.]+) [-\d.]+ ([-\d.]+)\]", l).groups())) for l in open(os.path.join(OUT, "statues")) if "/semi.jm" in l])
    x0, x1, z0, z1 = P[:, 0].min() - 45.0, P[:, 0].max() + 30.0, P[:, 1].min() - 25.0, P[:, 1].max() + 25.0
    smp = BP.PATH.samples(2.0); rs = StartRoute(BP.START, LP.N_GATES, LP.GATE_PITCH).samples(2.0)
    tr = cKDTree(np.r_[np.c_[smp['x'], smp['z']], np.c_[rs['x'], rs['z']]])
    tm = np.fromfile(os.path.join(OUT, "tilemap"), np.uint8); TN = int(np.sqrt(tm.size)); tm = tm.reshape(TN, TN)
    TJ, TI = np.meshgrid(np.arange(TN) * 2 * S, np.arange(TN) * 2 * S)
    box = (TJ >= x0) & (TJ <= x1) & (TI >= z0) & (TI <= z1)
    d, _ = tr.query(np.c_[TJ[box], TI[box]]); sel = np.zeros_like(box); sel[box] = d > 25.0
    tm[sel & (tm == BP.T_MAIN)] = BP.T_ROAD; tm.astype(np.uint8).tofile(os.path.join(OUT, "tilemap"))
    BP.REPORT['paddock_dalles'] = int(sel.sum())
    return x0, x1, z0, z1


def rf_ground(OUT, FOLDER):
    """textures de décals + traces de pneus de A1 ; décals posés comme sur A1 (ordre de son fichier decals)."""
    import layouts_sx as LS
    from engine import turn_mid_angle
    from starts import StartRoute
    from geo_tools import inside
    for d_ in ("textures", "treadmarks"):
        shutil.copytree(os.path.join(RFD, d_), os.path.join(OUT, "rf" + d_), dirs_exist_ok=True)
    # traces de pneus : celles de A1 sur les tuiles de terre (la terre, les projections et la physique restent celles de la version USLAND)
    ti = os.path.join(OUT, "tileinfo"); blocks = open(ti).read().split("addtile"); out = []
    tread = ["treadmark texture=@%s/rftreadmarks/dirt2x4.png size=4 aspect=0.5 spacing=3 speed_threshold=-20" % FOLDER,
             "treadmark texture=@%s/rftreadmarks/dirt2x8.png size=8 aspect=0.25 spacing=6" % FOLDER]
    for b in blocks:
        if "/ztile/darkdirt_" in b:
            keep = [l for l in b.splitlines() if not l.startswith("treadmark")]
            while keep and not keep[-1].strip():
                keep.pop()
            b = chr(10).join(keep + tread) + chr(10)
        out.append(b)
    open(ti, "w", newline=chr(10)).write("addtile".join(out))
    x0, x1, z0, z1 = paddock(OUT)
    rng = np.random.default_rng(2026)
    SH = "@%s/rftextures" % FOLDER
    ang_ = lambda fx, fz: float(np.arctan2(-fx, -fz))
    dec = lambda x, z, a, size, tex: "[%.6f %.6f] %.6f %.6f 1.000000 %s/%s.png" % (x, z, a, size, SH, tex)
    rnd = lambda: float(rng.uniform(-np.pi, np.pi))
    fl = BP.mx_poly(BP.arena_dims().floor_outline(1.0))
    in_pad = lambda x, z: x0 <= x <= x1 and z0 <= z <= z1
    D = {k: [] for k in ('ply', 'offtrack', 'ontrack', 'start', 'straight', 'jump', 'single', '180', 'whoops')}
    # contreplaqué le long du mur (A1 : une rangée de dalles de 22 ft juste à l'intérieur du mur)
    P = np.r_[fl, fl[:1]]; seg = np.diff(P, axis=0); Ls = np.hypot(seg[:, 0], seg[:, 1]); cum = np.r_[0, np.cumsum(Ls)]
    cen = fl.mean(0)
    for s_ in np.arange(0, cum[-1], 11.0):
        i = min(int(np.searchsorted(cum, s_, side='right')) - 1, len(seg) - 1); f = (s_ - cum[i]) / max(Ls[i], 1e-6)
        p = P[i] + seg[i] * f; tng = seg[i] / max(Ls[i], 1e-6); nrm = np.array([-tng[1], tng[0]])
        if np.dot(cen - p, nrm) < 0:
            nrm = -nrm
        q = p + nrm * 9.0
        if not in_pad(*q):
            D['ply'].append(dec(q[0], q[1], ang_(*tng) + float(rng.uniform(-0.05, 0.05)), 22.0, 'ply'))
    # terre hors piste partout (A1 : 28 ft), puis terre de piste en 3 rangées le long du tour et du départ (A1 : -9 / 0 / +9 ft, tous les ~10 ft)
    for xx in np.arange(fl[:, 0].min(), fl[:, 0].max() + 1, 14.0):
        for zz in np.arange(fl[:, 1].min(), fl[:, 1].max() + 1, 14.0):
            x_, z_ = xx + rng.uniform(-3, 3), zz + rng.uniform(-3, 3)
            if inside(np.array([[x_, z_]]), fl)[0] and not in_pad(x_, z_):
                D['offtrack'].append(dec(x_, z_, rnd(), 28.0, 'offtrack'))
    for smp in (BP.PATH.samples(10.0), StartRoute(BP.START, LP.N_GATES, LP.GATE_PITCH).samples(10.0)):
        for x_, z_, th in zip(smp['x'], smp['z'], smp['th']):
            for v in (-9.0, 0.0, 9.0):
                D['ontrack'].append(dec(x_ - np.sin(th) * v + rng.uniform(-1.5, 1.5), z_ + np.cos(th) * v + rng.uniform(-1.5, 1.5), rnd(), 28.0, 'ontrack'))
    # usure : départ, lignes droites, bosses, sauts, 180, whoops
    gx, gz = BP.START['gate']; h = np.radians(BP.START['heading'])
    for u in (30.0, 100.0):
        D['start'].append(dec(gx + np.cos(h) * u, gz + np.sin(h) * u, ang_(np.cos(h), np.sin(h)), 90.0, 'start'))
    for g in BP.PATH.segs:
        if g['kind'] == 'S':
            c, s_ = np.cos(g['t']), np.sin(g['t']); a = ang_(c, s_); n_ = max(1, int(round(g['L'] / 80.0)))
            for k in range(n_):
                u = (k + 0.5) * g['L'] / n_; D['straight'].append(dec(g['x0'] + u * c, g['z0'] + u * s_, a, 90.0, 'straight'))
            for prof, u0, name in g['sections']:
                for it in LS.COMBOS[name]['items']:
                    nm, st_, en = it[0], it[1], it[2]; L = en - st_
                    if nm.startswith('whoops'):
                        m = max(1, int(L / 45.0))
                        for k in range(m):
                            u_ = u0 + st_ + (k + 0.5) * L / m; D['whoops'].append(dec(g['x0'] + u_ * c, g['z0'] + u_ * s_, a, 55.0, 'whoops'))
                        continue
                    uu = u0 + (st_ + en) / 2; hh = float(np.max(prof[int(st_ / 0.1):int(en / 0.1) + 1]))
                    big = L >= 45.0 or hh >= 6.0
                    D['jump' if big else 'single'].append(dec(g['x0'] + uu * c, g['z0'] + uu * s_, a, 90.0 if big else 55.0, 'jump' if big else 'single'))
        elif g['kind'] == 'T' and g.get('berm') and abs(g['ang']) > 135:
            m = turn_mid_angle(g); fx, fz = np.cos(m), np.sin(m)
            D['180'].append(dec(g['cx'] + fx * g['r'] * 0.6, g['cz'] + fz * g['r'] * 0.6, ang_(fx, fz), 90.0, '180'))
    lines = [l for k in D for l in D[k]]
    open(os.path.join(OUT, "decals"), "w", newline=chr(10)).write(chr(10).join(lines) + chr(10))
    shutil.rmtree(os.path.join(OUT, "zdecal"), ignore_errors=True)
    BP.REPORT['decals_rf'] = {k: len(v) for k, v in D.items()}
    BP.REPORT['export']['decals'] = len(lines)


_export0 = BP.export


def export_rf(*a, **k):
    _export0(*a, **k)
    rf_ground(BP.OUT, BP.FOLDER)
    import layouts_sx as LS
    BP.whoops_boudins(BP.OUT, BP.FOLDER, BP.PATH, LS.COMBOS)              # boudins SX TOUR sur les murets des whoops


BP.render = render_rf
BP.export = export_rf

if __name__ == "__main__":
    BP.main()
