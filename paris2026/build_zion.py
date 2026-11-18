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


whoops_walls = BP.whoops_walls        # v18 : déplacé dans build_paris (partagé avec la version RF)


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
                if name == LP.L3_SEC:                           # v18 : saut du milieu de la version USLAND (« le double central du mien »)
                    BP.render_mid(jumps, g, prof, u0, name)
                else:
                    for it in LS.COMBOS[name]['items']:        # v16 : obstacles ZION (coupe ZION), whoops USLAND (coupe USLAND + murets)
                        i0, i1 = int(it[1] / 0.1), min(int(it[2] / 0.1) + 1, len(prof))
                        if it[0].startswith('whoops'):
                            BP.render_lane_block(G, whoops, g, prof[i0:i1], u0 + it[1], BP.TW)
                            whoops_walls(whoops, g, prof, u0, it)
                        else:
                            lane_zion(lay, g, prof[i0:i1], u0 + it[1], *LAT['T'])
                secs.append(dict(lane=g['tag'], name=name, u0=round(u0, 1), L=round(len(prof) * 0.1, 1), H=round(float(prof.max()), 2),
                                 items=[(i[0], round(i[1], 1), round(i[2], 1)) for i in LS.COMBOS[name]['items']]))
        elif g.get('berm'):                                  # v16 : virages USLAND (berms JGSX, comme la version USLAND)
            from engine import render_berm_stamp, turn_mid_angle, berm_ang_scale
            gb = BP.berm_seg(g)
            gain = LP.BERM90_GAIN if abs(abs(gb['ang']) - 90) < 1 else LP.BERM180_GAIN
            gain = LP.BERM_GAIN_TAG.get(g['tag'][:4], gain)
            tmp = np.zeros((N, N))
            sl = render_berm_stamp(G, tmp, g['berm'], g['cx'], g['cz'], turn_mid_angle(gb),
                                   ang_scale=berm_ang_scale(g['berm'], gb['ang']), r_shift=max(0.0, g['r'] - LP.RB))
            berms[sl] = np.maximum(berms[sl], tmp[sl] * gain)
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


def paddock_rect(OUT):
    """v17 : zone des camions (derrière le départ) d'après leurs statues, + 25 ft."""
    import re
    P = [tuple(map(float, re.match(r"\[([-\d.]+) [-\d.]+ ([-\d.]+)\]", l).groups())) for l in open(os.path.join(OUT, "statues")) if "/semi.jm" in l]
    P = np.array(P); return (P[:, 0].min() - 92.0, P[:, 0].max() + 30.0, P[:, 1].min() - 25.0, P[:, 1].max() + 25.0)


def zion_extras(OUT, FOLDER):
    """v17 : dalles grises sous les camions (tuile Road), voile de terre ZION (overlay) en dalles sur tout le sol de terre (pas
    seulement sur le tracé) ; v19 : décals d'obstacles retirés, panneau START suspendu, grilles noires Monster, plus de start_grids."""
    import re
    x0, x1, z0, z1 = paddock_rect(OUT)
    # tuiles : la zone des camions en dalles (Road), sauf à moins de 25 ft du tour / du départ
    from scipy.spatial import cKDTree
    import layouts_sx as LS
    from starts import StartRoute
    path, st = BP.PATH, BP.START
    smp = path.samples(2.0); rs = StartRoute(st, LP.N_GATES, LP.GATE_PITCH).samples(2.0)
    tr = cKDTree(np.r_[np.c_[smp['x'], smp['z']], np.c_[rs['x'], rs['z']]])
    tm = np.fromfile(os.path.join(OUT, "tilemap"), np.uint8); TN = int(np.sqrt(tm.size)); tm = tm.reshape(TN, TN)
    TJ, TI = np.meshgrid(np.arange(TN) * 2 * S, np.arange(TN) * 2 * S)
    box = (TJ >= x0) & (TJ <= x1) & (TI >= z0) & (TI <= z1)
    d, _ = tr.query(np.c_[TJ[box], TI[box]]); sel = np.zeros_like(box); sel[box] = d > 25.0
    tm[sel & (tm == 0)] = 6; tm.astype(np.uint8).tofile(os.path.join(OUT, "tilemap"))
    # décals : l'overlay ZION en dalles de 160 ft sur tout le sol de terre (hors paddock)
    # v19 (« sur chaque bosse, enlève les gradients ; il y a des lignes qu'il faut que tu fondes entre chaque bosse ») : plus de décals
    # d'obstacle (single / Table / triplemiddle) ni de bandes Straight (leurs bords faisaient des lignes) ; v19 (« enlève les grilles de
    # Zion en dessous ») : plus de décals startgate sous les grilles
    drop_ = ("/overlay.png", "/single.png", "/Table.png", "/triplemiddle.png", "/Straight.png", "/startgate.png")
    dl = [l for l in open(os.path.join(OUT, "decals")).read().splitlines() if l.strip() and not any(k in l for k in drop_)]
    fl = BP.mx_poly(BP.arena_dims().floor_outline(1.0)); from geo_tools import inside
    # v19b (capture en jeu : « bug de texture, mets partout ») : overlay.png de ZION = UNE décal pour toute la piste, opaque et sombre
    # sur ses bords ; répétée en dalles (v17) ses bords faisaient une grille de bandes grises. Dalle faite ici : le milieu de l'overlay
    # (terre claire translucide, sans les bords), en miroir 2 x 2 (raccords invisibles), posée bord à bord (160 ft, pas de 160 ft)
    # sur tout le sol (hors paddock)
    from PIL import Image as _I
    ovs = np.asarray(_I.open(os.path.join(ZD, "decal", "overlay.png")).convert("RGBA"))[200:712, 200:712]
    til = np.vstack([np.hstack([ovs, ovs[:, ::-1]]), np.hstack([ovs[::-1], ovs[::-1, ::-1]])])
    _I.fromarray(til, "RGBA").save(os.path.join(OUT, "zdecal", "overlay_tile.png"))
    ov = []; T_ = 160.0
    for xx in np.arange(fl[:, 0].min() + T_ / 2 - 20.0, fl[:, 0].max() + T_ / 2, T_):
        for zz in np.arange(fl[:, 1].min() + T_ / 2 - 20.0, fl[:, 1].max() + T_ / 2, T_):
            cs = np.array([[xx + dx_, zz + dz_] for dx_ in (-T_ / 2, 0, T_ / 2) for dz_ in (-T_ / 2, 0, T_ / 2)])
            if inside(cs, fl).any() and not (x0 <= xx <= x1 and z0 <= zz <= z1):
                ov.append("[%.6f %.6f] 0.000000 %.6f 1.000000 @%s/zdecal/overlay_tile.png" % (xx, zz, T_, FOLDER))
    open(os.path.join(OUT, "decals"), "w", newline=chr(10)).write(chr(10).join(ov + dl) + chr(10))
    # v19 (« le saut d'arrivée, il va pas ; il faut faire les câbles comme sur mon track, avec le finish ») : plus d'arche ZION, le panneau
    # FINISH suspendu (élingues jusqu'au toit) de la version USLAND reste
    # v19 (« enlève ma grille pourrie avec la poutre, elle n'existe pas ; garde nos grilles ») : plus de grilles de Saint-Georges
    # (start_grids, 88 ft avec la poutre) ; « des cordes qui descendent du plafond au-dessus du start, fond noir, START en blanc, comme le
    # finish, à peu près à la même hauteur » : panneau START (hab_objets.finish, mot START) 12 ft devant les grilles, face aux pilotes
    import hab_objets as HO
    assert not BP.REPORT.get('long_tuff_apres_depart'), "nofrills.js référence des rangs de statues"
    sd = os.path.join(OUT, "statue", "paris"); G0 = np.array(st['gate']); h0 = np.radians(st['heading']); f0 = np.array([np.cos(h0), np.sin(h0)])
    q = G0 + f0 * 12.0; rf_ = roof_ft(*q)
    HO.finish(sd, drop=0.0, roof=rf_, word='start', fname='start_banner')
    # v19 : les élingues du FINISH montaient à 118 ft, le toit est à ~146 ft au-dessus de l'arrivée (elles s'arrêtaient dans le vide) :
    # le haut des élingues remonté jusqu'au toit
    import re
    fx_, fz_ = next(tuple(map(float, re.match(r"\[(\S+) \S+ (\S+)\]", l).groups())) for l in open(os.path.join(OUT, "statues")) if "/finish.jm " in l)
    fj = os.path.join(sd, "finish.jm"); Lj = open(fj).read().split(chr(10)); nv_ = int(Lj[2].split()[0]); rfin = roof_ft(fx_, fz_)
    for k_ in range(3, 3 + nv_):
        v_ = Lj[k_].split()
        if abs(float(v_[1]) - 118.0) < 0.01:
            v_[1] = "%.6f" % rfin; Lj[k_] = " ".join(v_)
    open(fj, "w", newline=chr(10)).write(chr(10).join(Lj))
    sline = "[%.6f 0.000000 %.6f] %.6f @%s/statue/paris/start_banner.jm @%s/statue/paris/start_banner.png null" % (q[0], q[1], float(np.arctan2(f0[0], f0[1])), FOLDER, FOLDER)
    for f in ["statues"] + ["variants/" + v for v in os.listdir(os.path.join(OUT, "variants")) if v.startswith("statues")]:
        p = os.path.join(OUT, f); L = [l for l in open(p).read().splitlines() if "/start_grids.jm" not in l]
        open(p, "w", newline=chr(10)).write(chr(10).join(L + [sline]) + chr(10))
    # v19 (« des grilles noires, presque un peu pleines, comme les grilles USLAND, logo Monster Energy ») : modèle des grilles qui tombent
    import gate_monster as GM
    jm, png = GM.make(sd); tg = os.path.join(OUT, "timing_gates"); t_ = open(tg).read()
    t_ = t_.replace("statue/paris/start_gate_frame.jm", "statue/paris/" + jm).replace("statue/paris/start_gate_frame.png", "statue/paris/" + png)
    open(tg, "w", newline=chr(10)).write(t_)
    BP.REPORT['zion_v19'] = dict(paddock=[round(v) for v in (x0, x1, z0, z1)], dalles_tuiles=int(sel.sum()), overlay=len(ov), decals_gardes=len(dl),
                                 start=(round(q[0], 1), round(q[1], 1), round(rf_, 1)), toit_finish=round(rfin, 1), grilles=t_.count(jm))


def roof_ft(x, z):
    """hauteur du toit (ft) au-dessus d'un point du jeu (champ lissé de stade_paris, plan agrandi x PLAN_K)."""
    sys.path.insert(0, os.path.join(BP.ROOT, "stade_paris", "src"))
    from arena import roof
    f = roof.field(); X = (x - LP.OX) / LP.FT / LP.PLAN_K; Y = (LP.OZ - z) / LP.FT / LP.PLAN_K
    i = int(np.clip(round((X - f.xs[0]) / (f.xs[1] - f.xs[0])), 0, len(f.xs) - 1)); j = int(np.clip(round((Y - f.ys[0]) / (f.ys[1] - f.ys[0])), 0, len(f.ys) - 1))
    return float(f.h[i, j]) * LP.FT


_export0 = BP.export


def export_zion(*a, **k):
    _export0(*a, **k)
    zion_ground(BP.OUT, BP.FOLDER)
    zion_extras(BP.OUT, BP.FOLDER)
    import layouts_sx as LS
    BP.whoops_boudins(BP.OUT, BP.FOLDER, BP.PATH, LS.COMBOS)          # v18 : boudins SX TOUR sur les murets
    semis_jgsx(BP.OUT, BP.FOLDER)                                      # v19 : semi-remorques JGSX aux couleurs des équipes


def semis_jgsx(OUT, FOLDER):
    """v19 (« les camions des stands, reprends les semi-remorques d'un track et change les sponsors ») : semi_jgsx.py."""
    import re
    import semi_jgsx as SJ
    sd = os.path.join(OUT, "statue", "paris"); jm, tex = SJ.make(sd); n = 0
    for f in ["statues"] + ["variants/" + v for v in os.listdir(os.path.join(OUT, "variants")) if v.startswith("statues")]:
        p = os.path.join(OUT, f); L = open(p).read().splitlines()
        for k, l in enumerate(L):
            m = re.search(r"/statue/paris/semi\.jm @\S+/statue/paris/semi_(\w+)\.png", l)
            if m:
                L[k] = l.replace("/statue/paris/semi.jm", "/statue/paris/" + jm).replace("/semi_%s.png" % m.group(1), "/" + tex[m.group(1)]); n += f == "statues"
        open(p, "w", newline=chr(10)).write(chr(10).join(L) + chr(10))
    for f in ["semi.jm"] + ["semi_%s.png" % t for t in tex]:
        if os.path.exists(os.path.join(sd, f)):
            os.remove(os.path.join(sd, f))
    BP.REPORT['semis_jgsx'] = n


BP.render = render_zion
BP.export = export_zion

if __name__ == "__main__":
    BP.main()
