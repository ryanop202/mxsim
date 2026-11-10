"""Sol, textures et éclairage de Saint-Thibéry, À L'IDENTIQUE (demande de Ryan, étape 2 de la refonte Paris 2026).

Repris de tracks/USLAND2026SaintThiberybyBazo (version livrée v65) et de son code (export_stt.py, export_stt_night.py) :
  - tileinfo (blocs JGSX + textures SX1 dirt / concrete) et ext/USLAND2026SX1 (tiles, roost, treads, decal) copiés tels quels ;
  - décals : terre 'track' sur tout le sol (26 / 13 / 6 ft, bandes au bord), 5 lignes de 'track' le long du tour tous les
    3,9 ft + la zone de départ, 40 tear-offs, et les décals d'obstacle (whoops, single, table, tripleface) et de virage
    (90 / 180) aux mêmes tailles et règles que export_stt.obstacle_and_turn_decals ;
  - ombrage du sol : sur la piste, l'ombrage « jour » de Saint-Thibéry (Lambert, soleil (-0.6528, 0.3590, 0.6671),
    89,3 + 245,8 x lambert : le relief des bosses se lit comme là-bas), nuit en dehors, fondu sur 25 ft (export_stt_night) ;
  - lighting : le fichier de Saint-Thibéry (soleil, couleurs, ambiance, brouillard, ciel de nuit, flare) ; ciel copié.
"""
import os
import shutil
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STT = os.path.join(ROOT, "tracks", "USLAND2026SaintThiberybyBazo")
STT_NAME = "USLAND2026SaintThiberybyBazo"
SUN = [-0.6528, 0.3590, 0.6671]
NIGHT_GROUND = 45.0          # Saint-Thibéry hors de la piste (ombrage nuit, médiane 36-53)
rng = np.random.default_rng(31)


def ang_of(fx, fz):
    return float(np.arctan2(-fx, -fz))


def copy_assets(OUT, folder):
    """tileinfo + textures du sol + ciel + lighting de Saint-Thibéry (chemins renommés vers le dossier Paris)."""
    for d in ("ext/USLAND2026SX1", "tiles", "sky"):
        dst = os.path.join(OUT, d)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(os.path.join(STT, d), dst)
    for f in ("tileinfo", "lighting"):
        t = open(os.path.join(STT, f)).read().replace("@%s/" % STT_NAME, "@%s/" % folder)
        open(os.path.join(OUT, f), "w", newline="\n").write(t)
    # toutes les références doivent exister
    import re
    for f in ("tileinfo", "lighting"):
        for ref in re.findall(r"@%s/(\S+)" % folder, open(os.path.join(OUT, f)).read()):
            assert os.path.exists(os.path.join(OUT, ref)), ref


def shading(H, S, floor_mask):
    """ombrage jour (piste) / nuit (dehors) de Saint-Thibéry, fondu sur 25 ft depuis le bord du sol."""
    import sys
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    from shading import lambert_shadow
    from scipy.ndimage import distance_transform_edt
    lam, _ = lambert_shadow(H, S, SUN, shadow=False)
    day = np.clip(89.3 + 245.8 * lam, 0, 255)
    d_out = distance_transform_edt(~floor_mask) * S                     # ft hors du sol
    t = np.clip(d_out / 25.0, 0, 1); w = t * t * (3 - 2 * t)
    return np.clip(day * (1 - w) + NIGHT_GROUND * w, 0, 255).astype(np.uint8)


def decals(path, start_route, floor_mask, S, folder, combos):
    from scipy.ndimage import distance_transform_edt
    SH = "@%s/ext/USLAND2026SX1/decal" % folder
    dec = lambda x, z, a, size, tex: "[%.6f %.6f] %.6f %.6f 1.000000 %s/%s.png" % (x, z, a, size, SH, tex)
    out = []
    # 1. terre 'track' sur tout le sol (bandes de Saint-Georges / Saint-Thibéry : le bord suit le contour du sol)
    depth = distance_transform_edt(floor_mask) * S
    sub = 4; dd = depth[::sub, ::sub]; step_px = S * sub
    rg2 = np.random.default_rng(24)
    side = depth.shape[0] * S
    for size, step_, lo, hi in ((26.0, 10.0, 13.0, 1e9), (13.0, 5.0, 6.5, 13.0), (6.0, 2.5, 3.0, 6.5)):
        for zz in np.arange(step_ / 2, side, step_):
            for xx in np.arange(step_ / 2, side, step_):
                x_, z_ = xx + rg2.uniform(-0.3, 0.3) * step_, zz + rg2.uniform(-0.3, 0.3) * step_
                v = dd[min(int(z_ / step_px), dd.shape[0] - 1), min(int(x_ / step_px), dd.shape[1] - 1)]
                if lo < v <= hi:
                    out.append(dec(x_, z_, rg2.uniform(-np.pi, np.pi), size, 'track'))
    n_dirt = len(out)
    # 2. surface du tour : 5 lignes tous les 3,9 ft, zone de départ, 40 tear-offs (export_stt.surface_decals)
    smp = path.samples(3.9)
    for x, z, th in zip(smp['x'], smp['z'], smp['th']):
        nx, nz = -np.sin(th), np.cos(th)
        for v in (-10.4, -5.2, 0.0, 5.2, 10.4):
            j = rng.normal(0, 0.8, 2)
            out.append(dec(x + nx * v + j[0], z + nz * v + j[1], rng.uniform(-np.pi, np.pi), 26.0, 'track'))
    X_, Z_, _, _ = start_route.area_points(4.5, 5.5, margin=2.0)
    for x, z in zip(X_, Z_):
        out.append(dec(x + rng.normal(0, 0.6), z + rng.normal(0, 0.6), rng.uniform(-np.pi, np.pi), 26.0, 'track'))
    for i in rng.choice(len(smp['x']), 40, replace=False):
        out.append(dec(smp['x'][i] + rng.normal(0, 5), smp['z'][i] + rng.normal(0, 5), rng.uniform(-np.pi, np.pi), 4.84, 'Tearoff'))
    # 3. obstacles et virages (export_stt.obstacle_and_turn_decals)
    from engine import turn_mid_angle
    for g in path.segs:
        if g['kind'] == 'S':
            c, s_ = np.cos(g['t']), np.sin(g['t']); a = ang_of(c, s_)
            for prof, u0, name in g['sections']:
                for it in combos[name]['items']:
                    nm, st, en, hh = it[0], it[1], it[2], it[3]
                    L = en - st
                    if nm.startswith('whoops'):
                        for k in range(12):
                            uu = u0 + st + (k + 0.5) * L / 12
                            out.append(dec(g['x0'] + uu * c, g['z0'] + uu * s_, a, 110.0, 'whoops'))
                        continue
                    uu = u0 + (st + en) / 2
                    tex, cl = ('tripleface', 79.1) if hh >= 6.6 else (('table', 63.4) if L >= 52 else ('single', 47.5))
                    out.append(dec(g['x0'] + uu * c, g['z0'] + uu * s_, a, max(110.0, 110.0 * (L + 14) / cl), tex))
        elif g['kind'] == 'T' and g.get('berm'):
            m = turn_mid_angle(g); fx, fz = np.cos(m), np.sin(m)
            if abs(g['ang']) > 120:
                out.append(dec(g['cx'] + fx * 9, g['cz'] + fz * 9, ang_of(fx, fz), 110.0, '180'))
            else:
                out.append(dec(g['cx'] + fx * 14, g['cz'] + fz * 14, ang_of(fx, fz), 110.0, '90'))
    return out, n_dirt
