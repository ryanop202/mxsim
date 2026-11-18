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
BP.SAND_LD = 0.0                   # v19d (« le virage après le saut d'arrivée en sable, que le virage ») : pas sur la ligne de départ
ZD = BP.ZD
ZF = np.load(os.path.join(HERE, "data", "zion_formes.npz"))
LAT = dict(T=(34.0, 7.0), W=(40.0, 2.2))      # dessus plat, flanc (ft) : obstacles, whoops ; v20 (« la coupe RF, celle d'Anaheim, en
#   gardant la forme des bosses ») : obstacles à la coupe mesurée sur RF Anaheim 1 (dessus 34 ft, flancs 7 ft ; était 35,1 / 5,2)
ZION_R = 28.3
TERRE_RGB = (166, 113, 68)                  # v19d : terre plus orange-marron (ZION : 158 136 85)
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


def fill_berm_dips(berms, path):
    """v20 (« en bas de chaque virage tu as mis une genre de petite ornière bizarre, gênante, retire-la ») : le croissant JGSX décalé
    vers l'extérieur (180 plus larges que 21,5 ft) puis fondu en bas laissait un creux de 0,2 - 0,4 ft au pied de la face du berm, à
    l'intérieur. Dans chaque virage à berm, le profil radial (du centre vers la crête) ne redescend plus : chaque creux est rempli au
    niveau d'avant (jamais rien d'enlevé, rien ne bouge au-delà de la crête)."""
    for g in path.segs:
        if g['kind'] != 'T' or not g.get('berm'):
            continue
        Rm = g['r'] + 45.0; rr = np.arange(0.0, Rm, 0.5); aa = np.radians(np.arange(0.0, 360.0, 0.5))
        X = g['cx'] + np.outer(np.cos(aa), rr); Z = g['cz'] + np.outer(np.sin(aa), rr)
        P = map_coordinates(berms, [Z / S, X / S], order=1, cval=0.0)
        Pin = np.where(rr[None, :] < g['r'] + 22.0, P, 0.0)          # la crête de CE virage (pas un berm voisin plus loin)
        k = np.argmax(Pin, axis=1); ok = Pin.max(axis=1) > 1.5
        M = np.maximum.accumulate(P, axis=1); D = np.where((np.arange(len(rr))[None, :] < k[:, None]) & ok[:, None], M - P, 0.0)
        if D.max() < 0.01:
            continue
        sl, Xw, Zw = G.window(g['cx'] - Rm, g['cx'] + Rm, g['cz'] - Rm, g['cz'] + Rm)
        r_ = np.hypot(Xw - g['cx'], Zw - g['cz']); a_ = np.degrees(np.arctan2(Zw - g['cz'], Xw - g['cx'])) % 360.0
        add = map_coordinates(np.r_[D, D[:1]], [a_ / 0.5, r_ / 0.5], order=1, mode='nearest')     # dernière ligne = 360° (= 0°)
        add = np.where(r_ < Rm - 1.0, add, 0.0)
        berms[sl] += add


def render_zion(path, st):
    import layouts_sx as LS
    jumps = np.zeros((N, N)); whoops = np.zeros((N, N)); berms = np.zeros((N, N)); fmx = np.zeros((N, N)); secs = []
    walls = np.zeros((N, N))      # v20b : murets à part (le pied arrondi des whoops les étalait dans chaque creux = un rebord)
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
                            # v20b : whoops pleine forme jusqu'au pied droit des murets (|v| = 17 ft), murets seuls dans leur couche
                            BP.render_lane_block(G, whoops, g, prof[i0:i1], u0 + it[1], 2 * BP.WALL_TOP[0])
                            whoops_walls(walls, g, prof, u0, it, with_whoops=False)
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
            fe_ = LP.BERM_END_FADE.get(g['tag'][:4])
            if fe_:                                          # v20c : le berm s'arrête avant la sortie du virage, fondu doux
                nx_ = path.segs[path.segs.index(g) + 1]; a_ex = np.arctan2(nx_['z0'] - g['cz'], nx_['x0'] - g['cx'])
                jj_, ii_ = np.meshgrid(np.arange(N)[sl[1]], np.arange(N)[sl[0]])
                th_ = np.arctan2(ii_ * S - g['cz'], jj_ * S - g['cx'])
                phi = np.degrees(np.angle(np.exp(1j * (th_ - a_ex) * (1.0 if g['ang'] > 0 else -1.0))))
                t_ = np.clip((phi - fe_[0]) / fe_[1], 0, 1); tmp[sl] *= t_ * t_ * (3 - 2 * t_)
            berms[sl] = np.maximum(berms[sl], tmp[sl] * gain)
    # v19d (capture en jeu : « regarde, il y a encore le trait gradient ») : (1) les croissants JGSX gardent un fond de 0,02 - 0,1 ft
    # coupé net -> petites marches droites au bout des virages : le bas des berms est fondu à zéro ; (2) pieds des bosses arrondis
    # comme la version USLAND (SOFT_FEET) : plus de pli au pied de chaque bosse
    from scipy.ndimage import gaussian_filter
    # v20b (« il y a toujours une petite berme au pied du virage, dans tous les virages ») : le fondu v19d (seuil 0,12 - 0,62 ft) cassait
    # le pied de chaque berm (pente 0 -> 17° en 2 ft = un pli). Fondu doux à la place : h - 0,15 tanh(h / 0,15) (pente continue, le fond
    # de 0,02 - 0,1 ft tombe sous 0,013 ft, le berm ne baisse que de 0,15 ft)
    berms[:] = berms - 0.15 * np.tanh(berms / 0.15)
    fill_berm_dips(berms, path)
    sf = LP.SOFT_FEET
    for A_ in (jumps, whoops):                                # (pas les berms : leur pied s'étalait sous les grilles)
        t_ = np.clip(A_ / sf['h'], 0, 1); w_ = t_ * t_ * (3 - 2 * t_)
        A_[:] = A_ * w_ + gaussian_filter(A_, sf['sigma'] / S) * (1 - w_)
    np.maximum(whoops, walls, out=whoops)                     # murets après l'arrondi : face droite, rien dans les creux
    # rangée des grilles toujours à plat (le pied arrondi d'une bosse de L5 arrivait à 4 ft de la dernière grille) : fondu sur 3 ft
    G0 = np.array(st['gate']); h0 = np.radians(st['heading']); f0 = np.array([np.cos(h0), np.sin(h0)]); n0 = np.array([-f0[1], f0[0]])
    half = LP.N_GATES * LP.GATE_PITCH / 2 + 2.0; R_ = half + 8.0
    sl, X, Z = G.window(G0[0] - R_, G0[0] + R_, G0[1] - R_, G0[1] + R_)
    du, dv = (X - G0[0]) * f0[0] + (Z - G0[1]) * f0[1], (X - G0[0]) * n0[0] + (Z - G0[1]) * n0[1]
    d = np.hypot(np.maximum(np.abs(du) - 5.0, 0), np.maximum(np.abs(dv) - half, 0)); w = np.clip(d / 3.0, 0, 1); w = w * w * (3 - 2 * w)
    for A_ in (jumps, whoops, berms):
        A_[sl] *= w
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
    # v19d (« en sable, texture sable et tout ») : les tuiles sable de ZION (viraplasable, turnsable) avec la texture sable de ZION
    zb = [re.sub(r"texture @\S+/ztile/2\.png", "texture @%s/ztile/sand.ppm" % FOLDER, b) if re.search(r"name (viraplasable|turnsable)", b) else b for b in zb]
    open(os.path.join(OUT, "tileinfo"), "w", newline=chr(10)).write("addtile".join(zb + pick) + "addtile" + chr(10))
    shutil.copytree(os.path.join(ZD, "tile"), os.path.join(OUT, "ztile"), dirs_exist_ok=True)
    # v19d (« essaie de faire la terre un peu plus orange marron ») : la tuile de terre ZION (couleur unie 158 136 85) -> TERRE_RGB
    t2 = os.path.join(OUT, "ztile", "2.png"); Image.new("RGB", Image.open(t2).size, TERRE_RGB).save(t2)
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
    # v19c (captures en jeu : « il n'y a plus la texture, c'est tout lisse ; remets la texture de base ; on voit les gradients entre
    # chaque bosse, les lignes ») : la tuile de terre ZION est une couleur unie, la terre « rayée » vue en jeu vient de ses décals de
    # virage (couleur + relief _tnorm), dont les bords droits faisaient les lignes. Plus aucune décal ZION entière ; à la place des
    # pastilles de grain (terre_zion.py : rayures + relief de 180.png, à la couleur de la tuile, bord fondu), 56 ft, tous les 22 ft,
    # tournées au hasard, partout sur le sol hors paddock : la texture partout, sans bord ni ligne.
    # v20 (capture en jeu : « la texture, faut pas qu'il y ait de traces en travers du terrain, faut que ce soit comme la texture de
    # Saint-Thibéry, en gardant cette couleur ») : plus de pastilles de grain ZION (leurs rayures venaient du décal de virage 180.png) ;
    # à la place la terre de Saint-Thibéry : track.png (USLAND2026SX1, 26 ft, tournée au hasard) teintée à la couleur de la tuile, posée
    # comme à Saint-Thibéry (dress_sx : 5 en travers tous les 3,9 ft sur le tour et le départ, grille de 11 ft sur le reste du sol)
    from PIL import Image as _I
    tile_col = np.asarray(_I.open(os.path.join(OUT, "ztile", "2.png")).convert("RGB"), float).reshape(-1, 3).mean(0)
    src_ = os.path.join(BP.ROOT, "tracks", "USLAND2026SaintThiberybyBazo", "ext", "USLAND2026SX1", "decal")
    a_ = np.asarray(_I.open(os.path.join(src_, "track.png")).convert("RGBA"), float); m_ = a_[..., 3] > 10
    a_[..., :3] = np.clip(a_[..., :3] * (tile_col / a_[..., :3][m_].mean(0)), 0, 255)
    _I.fromarray(a_.astype(np.uint8), "RGBA").save(os.path.join(OUT, "zdecal", "terre_stt.png"), optimize=True)
    shutil.copy(os.path.join(src_, "track_tnorm.png"), os.path.join(OUT, "zdecal", "terre_stt_tnorm.png"))
    for f_ in ("terre.png", "terre_tnorm.png"):                          # anciennes pastilles de grain (v19c)
        if os.path.exists(os.path.join(OUT, "zdecal", f_)):
            os.remove(os.path.join(OUT, "zdecal", f_))
    tz, tsize = "terre_stt.png", 26.0
    dl = []; ov = []; rng = np.random.default_rng(19)
    # v19d : sable du virage après l'arrivée = décals sable de RF Anaheim 1 (sand2 / sand3, 18 ft, comme leur section sable), le grain
    # de terre s'arrête autour (34 ft)
    from scipy.spatial import cKDTree as _KD
    sand_t = _KD(BP.SAND_SMP); sd_ = os.path.join(OUT, "rfsand"); os.makedirs(sd_, exist_ok=True)
    RFT = os.path.join(os.path.dirname(BP.ROOT), "rf_ext", "sx2026r01anaheim1", "textures")
    for f_ in ("sand2.png", "sand2_tnorm.png", "sand3.png"):
        shutil.copy(os.path.join(RFT, f_), os.path.join(sd_, f_))
    sx0, sz0 = BP.SAND_SMP.min(0) - 30; sx1, sz1 = BP.SAND_SMP.max(0) + 30; sand = []
    for xx in np.arange(sx0, sx1, 8.0):
        for zz in np.arange(sz0, sz1, 8.0):
            x_, z_ = xx + rng.uniform(-2, 2), zz + rng.uniform(-2, 2)
            if sand_t.query([x_, z_])[0] < 18.0:
                sand.append("[%.6f %.6f] %.6f 18.000000 1.000000 @%s/rfsand/%s" % (x_, z_, rng.uniform(-np.pi, np.pi), FOLDER, "sand2.png" if rng.random() < 0.45 else "sand3.png"))
    def put_(x_, z_):
        ov.append("[%.6f %.6f] %.6f %.6f 1.000000 @%s/zdecal/%s" % (x_, z_, rng.uniform(-np.pi, np.pi), tsize, FOLDER, tz))
    ride_ = []
    for sm_ in (path.samples(3.9), StartRoute(st, LP.N_GATES, LP.GATE_PITCH).samples(3.9)):
        for x, z, th in zip(sm_['x'], sm_['z'], sm_['th']):
            nx, nz = -np.sin(th), np.cos(th); ride_.append((x, z))
            for v in (-10.4, -5.2, 0.0, 5.2, 10.4):
                j = rng.normal(0, 0.8, 2); x_, z_ = x + nx * v + j[0], z + nz * v + j[1]
                if sand_t.query([x_, z_])[0] > 18.0:
                    put_(x_, z_)
    ride_t = _KD(np.array(ride_))
    for xx in np.arange(fl[:, 0].min(), fl[:, 0].max() + 1, 11.0):
        for zz in np.arange(fl[:, 1].min(), fl[:, 1].max() + 1, 11.0):
            x_, z_ = xx + rng.uniform(-2.5, 2.5), zz + rng.uniform(-2.5, 2.5)
            if inside(np.array([[x_, z_]]), fl)[0] and not (x0 <= x_ <= x1 and z0 <= z_ <= z1) and sand_t.query([x_, z_])[0] > 34.0                     and ride_t.query([x_, z_])[0] > 12.0:
                put_(x_, z_)
    ov = ov + sand
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
    # v21 (« les câbles du départ, ils descendent bien plus bas pour le truc du start ») : bas du panneau à START_Y ft (était 34)
    HO.finish(sd, drop=0.0, roof=rf_, word='start', fname='start_banner', y_bas=START_Y)
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
        p = os.path.join(OUT, f); L = [l for l in open(p).read().splitlines() if "/start_grids.jm" not in l and "/flag_cage.jm" not in l]   # v19c : « la cabane, faut pas la mettre pour l'instant »
        open(p, "w", newline=chr(10)).write(chr(10).join(L + [sline]) + chr(10))
    # v19 (« des grilles noires, presque un peu pleines, comme les grilles USLAND, logo Monster Energy ») : modèle des grilles qui tombent
    import gate_monster as GM
    jm, png = GM.make(sd); tg = os.path.join(OUT, "timing_gates"); t_ = open(tg).read()
    t_ = t_.replace("statue/paris/start_gate_frame.jm", "statue/paris/" + jm).replace("statue/paris/start_gate_frame.png", "statue/paris/" + png)
    open(tg, "w", newline=chr(10)).write(t_)
    BP.REPORT['zion_v19'] = dict(paddock=[round(v) for v in (x0, x1, z0, z1)], dalles_tuiles=int(sel.sum()), overlay=len(ov), decals_gardes=len(dl),
                                 start=(round(q[0], 1), round(q[1], 1), round(rf_, 1)), toit_finish=round(rfin, 1), grilles=t_.count(jm))


START_Y = 15.0
BALES_PER_TURN = {90: 3, 180: 5}


def deco_v21(OUT, FOLDER, combos):
    """v21 (photos de Paris 2025) : deco_v21.py ; boudins triangulaires bâchés + filets rouges sur le 1er quart de tour (90°) de chaque virage à berm, ballots
    en U noirs à l'intérieur de ces virages, arche 50 Factory au milieu du plat du couloir Est (entre le saut de sortie et la table)."""
    import deco_v21 as DV
    sd = os.path.join(OUT, "statue", "deco"); os.makedirs(sd, exist_ok=True); ref = lambda f: "@%s/statue/deco/%s" % (FOLDER, f)
    t = open(os.path.join(OUT, "terrain.hf")).read().split(); s_, lo_, hi_ = float(t[1]), float(t[2]), float(t[3])
    Hm = np.asarray(Image.open(os.path.join(OUT, "terrain.png")), float) / 65535 * (hi_ - lo_) + lo_
    Hf = lambda x, z: map_coordinates(Hm, [np.atleast_1d(z) / s_, np.atleast_1d(x) / s_], order=1)
    line = lambda x, z, yaw, jm, png, shp_: "[%.6f 0.000000 %.6f] %.6f %s %s %s" % (x, z, yaw, ref(jm), ref(png), ref(shp_) if shp_ else "null")
    lines = []; rep_ = dict(murs=[], ballots=0)
    DV.tarp_texture(sd); ntex, rnet, rblk = DV.net_texture(sd)        # rnet = (v bas, v haut) du filet, rblk = uv du noir
    bj, bp, bs = DV.bale_u(sd, 'noir')
    for k, g in enumerate(g_ for g_ in BP.PATH.segs if g_['kind'] == 'T' and g_.get('berm')):
        f0 = g.get('berm_from', 0.0); f1 = min(1.0, f0 + 90.0 / abs(g['ang']))
        w = DV.turn_wall(sd, k, g, Hf, f0, f1, ntex, rnet, rblk); rep_['murs'].append((g['tag'][:5], w['r_wall'], w['arc_ft'], w['posts']))
        gy, gx = np.gradient(Hm[int(g['cz'] / s_) - 2:int(g['cz'] / s_) + 3, int(g['cx'] / s_) - 2:int(g['cx'] / s_) + 3], s_)
        assert max(abs(gx).max(), abs(gy).max()) < 0.02, ("origine du mur pas à plat", g['tag'])
        for jm, png, shp_ in w['files']:
            lines.append(line(g['cx'], g['cz'], 0.0, jm, png, shp_))
        # ballots en U noirs à l'intérieur du virage, axe le long de la trajectoire
        n_ = BALES_PER_TURN[180 if abs(g['ang']) > 120 else 90]; sg = 1.0 if g['ang'] > 0 else -1.0
        th_in = g['t0'] + sg * np.pi / 2; ang = np.radians(g['ang'])
        for f in (np.arange(n_) + 0.5) / n_:
            th = th_in - ang * f; r_ = g['r'] - 8.0; x_, z_ = g['cx'] + np.cos(th) * r_, g['cz'] + np.sin(th) * r_
            if Hf(x_, z_)[0] > 0.05:
                continue
            tx, tz = -np.sin(th), np.cos(th); lines.append(line(x_, z_, float(np.arctan2(-tz, tx)), bj, bp, bs)); rep_['ballots'] += 1
    # arche 50 Factory : couloir Est (LR), milieu du plat entre le saut de sortie et la table à double étage
    aj, ap, as_ = DV.arche_50f(sd)
    gL = next(g for g in BP.PATH.segs if g['kind'] == 'S' and g['tag'].startswith('LR'))
    prof, u0, name = gL['sections'][0]; it = combos[name]['items']; ua = u0 + (it[0][2] + it[1][1]) / 2
    c, s2 = np.cos(gL['t']), np.sin(gL['t']); pa = (gL['x0'] + ua * c, gL['z0'] + ua * s2)
    assert float(np.max(Hf(pa[0] + np.array([-s2, s2]) * 21.5, pa[1] + np.array([c, -c]) * 21.5))) < 0.05, "pieds de l'arche pas à plat"
    lines.append(line(pa[0], pa[1], float(np.arctan2(c, s2)), aj, ap, as_)); rep_['arche'] = (round(pa[0], 1), round(pa[1], 1))
    for f in ["statues"] + ["variants/" + v for v in os.listdir(os.path.join(OUT, "variants")) if v.startswith("statues")]:
        p = os.path.join(OUT, f); s0 = open(p).read().rstrip(chr(10)) + chr(10)
        open(p, "w", newline=chr(10)).write(s0 + chr(10).join(lines) + chr(10))
    BP.REPORT['deco_v21'] = rep_


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
    deco_v21(BP.OUT, BP.FOLDER, LS.COMBOS)                             # v21 : murs bâchés + filets, ballots en U, arche 50 Factory


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
