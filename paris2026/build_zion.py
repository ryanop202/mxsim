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

BP.FOLDER = "USLANDParis"                     # v22d (« renomme-la usland paris ») ; était USLAND2026SupercrossParisZion
BP.DESC = "USLAND Paris"                        # v22d (« renomme-la usland paris »)
BP.OUT = os.path.join(BP.ROOT, "tracks", BP.FOLDER)
BP.AP = os.path.join(HERE, "apercu_zion")
BP.SAND_TL5 = False; BP.SAND_RUTS = False   # v23 : virage après l'arrivée en terre ; sable sans ornières
BP.SAND_LD = 0.0                   # v19d (« le virage après le saut d'arrivée en sable, que le virage ») : pas sur la ligne de départ
ZD = BP.ZD
ZF = np.load(os.path.join(HERE, "data", "zion_formes.npz"))
LAT = dict(T=(34.0, 7.0), W=(40.0, 2.2))      # dessus plat, flanc (ft) : obstacles, whoops ; v20 (« la coupe RF, celle d'Anaheim, en
#   gardant la forme des bosses ») : obstacles à la coupe mesurée sur RF Anaheim 1 (dessus 34 ft, flancs 7 ft ; était 35,1 / 5,2)
ZION_R = 28.3
TERRE_RGB = (166, 113, 68)                  # v19d : terre plus orange-marron (ZION : 158 136 85)
G, N, S = BP.G, BP.N, BP.S


def lane_zion(out, g, prof, u0, top, side, kl=1.0, kr=1.0, band=10.0):
    """kl / kr (v22) : facteur de hauteur côté gauche / droit du sens de course, passage doux au milieu (bande de band ft)."""
    L = len(prof) * 0.1; c, s_ = np.cos(g['t']), np.sin(g['t']); half = top / 2 + side + 1.0
    pts = np.array([(g['x0'] + uu * c - vv * s_, g['z0'] + uu * s_ + vv * c) for uu in (u0, u0 + L) for vv in (-half, half)])
    sl, X, Z = G.window(pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max())
    dx, dz = X - g['x0'], Z - g['z0']; u = dx * c + dz * s_ - u0; vs = -dx * s_ + dz * c; v = np.abs(vs)
    pu = np.interp(u / 0.1, np.arange(len(prof)), prof, left=0, right=0)
    if kl != 1.0 or kr != 1.0:                                   # v > 0 = droite du sens de course
        w = np.clip(vs / band + 0.5, 0, 1); w = w * w * (3 - 2 * w); pu = pu * (kl * (1 - w) + kr * w)
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


def post_finish(out, path, sm=1.2):
    """v22d (photo IRL + croquis validé « fais plutôt la 1re ... ») : après l'arrivée (T_L5a 90° gauche, petite ligne droite, T_L5b 90° gauche) :
    (1) bosse basse à moitié dans le virage : à l'intérieur (gauche) 1,9 ft, presque rien à l'extérieur (« le virage sort encore un peu
    dans la bosse »), passage doux ; (2) bosse 2,8 ft dans la petite ligne droite ; (3) fusionnée : on coupe la descente de la 2 à
    mi-hauteur et le plateau (1,5 ft) part direct, sans creux, tourne avec le 2e 90°, puis redescend sur la ligne du bas.
    h(s, v) lu sur la trajectoire (s depuis l'entrée de T_L5a, v > 0 = droite du sens de course = extérieur), lissé (pas de trait)."""
    from scipy.spatial import cKDTree
    from scipy.ndimage import gaussian_filter
    ga = next(g for g in path.segs if g['tag'].startswith('T_L5a')); gb = next(g for g in path.segs if g['tag'].startswith('T_L5b'))
    e1 = ga['L']; e3 = gb['s0'] + gb['L'] - ga['s0']
    smp = path.samples(0.25); sr = smp['s'] - ga['s0']; keep = (sr > -15) & (sr < e3 + 30)
    sx, sz, st_, th = smp['x'][keep], smp['z'][keep], sr[keep], smp['th'][keep]
    P1 = LP.pts_prof(LP.POST_FIN['b1'], 1.0); P23 = LP.pts_prof(LP.POST_FIN['b23'], 1.0)
    P1o = LP.pts_prof(LP.POST_FIN.get('b1o', LP.POST_FIN['b1']), 0.7)            # v23e : extérieur (droite) en appel
    R = 40.0; sl, X, Z = G.window(sx.min() - R, sx.max() + R, sz.min() - R, sz.max() + R)
    tree = cKDTree(np.c_[sx, sz]); d_, i_ = tree.query(np.c_[X.ravel(), Z.ravel()]); i_ = i_.reshape(X.shape)
    dx, dz = X - sx[i_], Z - sz[i_]; v = -dx * np.sin(th[i_]) + dz * np.cos(th[i_]); s_ = st_[i_]
    u0_ = 0.0                                                   # les points de POST_FIN sont déjà en s absolu
    h1i = np.interp((s_ - u0_) / 0.1, np.arange(len(P1)), P1, left=0, right=0); h1o = np.interp((s_ - u0_) / 0.1, np.arange(len(P1o)), P1o, left=0, right=0)
    wq = np.clip(v / 10.0 + 0.5, 0, 1); wq = wq * wq * (3 - 2 * wq); h1 = h1i * (1 - wq) + h1o * wq
    u2_ = 0.0
    h23 = np.interp((s_ - u2_) / 0.1, np.arange(len(P23)), P23, left=0, right=0)
    tw = LP.TOP_W; ss = lambda t: (lambda t_: t_ * t_ * (3 - 2 * t_))(np.clip(t, 0, 1))
    side = LP.POST_FIN['out_k'] + (1 - LP.POST_FIN['out_k']) * ss((tw / 2 - v) / tw)          # intérieur (v < 0) 1 -> extérieur out_k
    lat = ss((tw / 2 + 4.0 - np.abs(v)) / 4.0)                # bord sur 4 ft (le centre du virage, origine du mur, reste à plat)
    h = (h1 * side + h23) * lat * (d_.reshape(X.shape) < R)
    for g_ in (ga, gb):                                       # centre des virages (origine des murs) : disque plat de 4 ft, fondu sur 4 ft
        h = h * ss((np.hypot(X - g_['cx'], Z - g_['cz']) - 4.0) / 4.0)
    h = gaussian_filter(h, sm / S)
    out[sl] = np.maximum(out[sl], h)
    BP.REPORT['apres_arrivee'] = dict(b1=round(float(P1.max()), 2), b23=round(float(P23.max()), 2), plateau=LP.POST_FIN['b23'][3][1])


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
                            whoops_walls(walls, g, prof, u0, it, with_whoops=False, left=False)   # v22c : pas de talus à gauche
                        else:
                            sp_ = [q for q in LP.SPLIT_Z.get(name, []) if q[0] - 0.5 <= it[1] and it[2] <= q[1] + 0.5]   # v22
                            kk_ = sp_[0][2:] if sp_ else (1.0, 1.0)
                            lane_zion(lay, g, prof[i0:i1], u0 + it[1], *LAT['T'], kl=kk_[0], kr=kk_[1])
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
    post_finish(jumps, path)                                  # v22d : bosses + plateau du virage après l'arrivée
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


SABLE_JAUNE = (226, 196, 118)


def sand_texture(path, base=(214, 182, 128)):
    """v23f : sable beige clair (au-dessus de la terre orange-marron TERRE_RGB), grain fin + petites ondulations ; 512 x 512, raccordable."""
    from scipy.ndimage import gaussian_filter
    rng = np.random.default_rng(23); n1 = gaussian_filter(rng.normal(0, 1, (512, 512)), 1.0, mode='wrap'); n2 = gaussian_filter(rng.normal(0, 1, (512, 512)), 12, mode='wrap')
    a = np.asarray(base, float)[None, None, :] * (1 + 0.05 * (n1 / n1.std())[..., None] + 0.04 * (n2 / n2.std())[..., None])
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(path)
RF_SAND_DECALS = False


def jaunir(path, target=SABLE_JAUNE):
    """v22c (« fais le sable jaune ») : même grain, couleur moyenne ramenée à un sable jaune (garde l'alpha s'il y en a)."""
    im = Image.open(path); has_a = im.mode in ('RGBA', 'LA'); a = np.asarray(im.convert('RGBA'), float)
    rgb = a[..., :3]; m = rgb.reshape(-1, 3).mean(0); lum = rgb.mean(-1, keepdims=True) / max(m.mean(), 1.0)
    out = np.clip(lum * np.array(target, float), 0, 255)
    res = np.concatenate([out, a[..., 3:]], -1) if has_a else out
    Image.fromarray(res.astype(np.uint8), 'RGBA' if has_a else 'RGB').save(path)


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
    # v23 : sable USLAND (SX1) ; v23c (« la texture toute verte ») : copié dans ztile (le chemin ext/ ne se charge pas dans ces tuiles)
    zb = [re.sub(r"texture @\S+/ztile/2\.png", "texture @%s/ztile/sand_usland.ppm" % FOLDER, b) if re.search(r"name (viraplasable|turnsable)", b) else b for b in zb]
    # v23e (« t'as toujours pas mis de sable ; une texture sable, que ça freine la moto, comme on a l'habitude ») : les tuiles sable de
    # ZION remplacées par les vraies tuiles sable des pistes USLAND (SX1 : Sand Straight / Sand Exit : freinage, érosion, traces et
    # poussière de sable), fichiers copiés dans sx1sand/
    sx1 = open(os.path.join(BP.ROOT, "tracks", "USLAND2026SX1", "tileinfo")).read().split("addtile")
    def sxb(nm, newname):
        b_ = next(b for b in sx1 if re.search(r"name %s\s*$" % nm, b, re.M)).replace("@USLAND2026SX1/", "@%s/sx1sand/" % FOLDER)
        return re.sub(r"name [^\r\n]+", "name " + newname, b_, count=1)
    zb = [sxb("Sand Straight", "viraplasable") if re.search(r"name viraplasable", b) else sxb("Sand Exit", "turnsable") if re.search(r"name turnsable", b) else b for b in zb]
    for sub_ in ("tiles", "roost", "treads"):
        shutil.copytree(os.path.join(BP.ROOT, "tracks", "USLAND2026SX1", sub_), os.path.join(OUT, "sx1sand", sub_), dirs_exist_ok=True)
    # v23f (« le sable est toujours buggé, il est vert ») : la texture 16x16 de SX1 (130, 100, 60) rend vert-olive sous l'éclairage ZION ;
    # texture de sable beige faite maison (grain fin), la physique des tuiles USLAND est gardée
    sand_texture(os.path.join(OUT, "sx1sand", "tiles", "sand.ppm"))
    # v21d (« le sol derrière le terrain, là où il y a les camions, de la tribune à l'autre côté : des dalles noires un peu de plastique,
    # noir gris ») : une tuile de plus, « Paddock » (index PADDOCK_TILE), réglages de la tuile Road, texture dalles_noires.png
    road = next(b for b in pick if re.search(r"name Road", b))
    pad = re.sub(r"name Road", "name Paddock", road); pad = re.sub(r"texture @\S+", "texture @%s/ztile/dalles_noires.png" % FOLDER, pad, count=1)
    assert len(zb) + len(pick) == PADDOCK_TILE
    open(os.path.join(OUT, "tileinfo"), "w", newline=chr(10)).write("addtile".join(zb + pick + [pad]) + "addtile" + chr(10))
    shutil.copytree(os.path.join(ZD, "tile"), os.path.join(OUT, "ztile"), dirs_exist_ok=True)
    # v19d (« essaie de faire la terre un peu plus orange marron ») : la tuile de terre ZION (couleur unie 158 136 85) -> TERRE_RGB
    t2 = os.path.join(OUT, "ztile", "2.png"); Image.new("RGB", Image.open(t2).size, TERRE_RGB).save(t2)
    shutil.copy(os.path.join(BP.ROOT, "tracks", "USLAND2026SX1", "tiles", "sand.ppm"), os.path.join(OUT, "ztile", "sand_usland.ppm"))
    dalles_texture(os.path.join(OUT, "ztile", "dalles_noires.png"))
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


PADDOCK_TILE = 8
PADDOCK_MARGIN = 35.0                      # ft au-delà de la ligne de course des virages Ouest (dos des berms compris)
FINISH_DOWN = 5.0                          # v21d (« baisse le truc de finish, il est légèrement trop haut ») : 34 -> 29 ft
N_SEMIS = 7                                # v21d (« en mettre moins, t'en enlèves 3 ; pas tous dans le même sens »)


def dalles_texture(path):
    """dalles de plastique noir-gris (2 x 2 par carreau de texture), joints un peu plus sombres, petit grain antidérapant."""
    from scipy.ndimage import gaussian_filter
    n = 512; rng = np.random.default_rng(8); a = np.full((n, n), 46.0)
    a += gaussian_filter(rng.normal(0, 1, (n, n)), 1.0, mode='wrap') * 2.2 + gaussian_filter(rng.normal(0, 1, (n, n)), 40, mode='wrap') * 25
    yy, xx = np.mgrid[0:n, 0:n]; a[((xx % 16) < 3) & ((yy % 16) < 3)] += 5                # plots antidérapants
    for k in (0, n // 2):
        a[k:k + 3, :] = 30; a[:, k:k + 3] = 30                                           # joints
    g = np.clip(np.dstack([a, a + 1, a + 4]), 0, 255).astype(np.uint8); Image.fromarray(g).save(path)


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
    # v21d : toute la bande derrière les virages Ouest, d'une tribune à l'autre, en dalles noires (tuile Paddock) ; plus de dalles grises
    XPAD = float(smp['x'].max()) + PADDOCK_MARGIN; fl_ = BP.mx_poly(BP.arena_dims().floor_outline(1.0)); from geo_tools import inside as _in
    box = TJ >= XPAD; ii_ = np.nonzero(box & (tm == 0)); inn = _in(np.c_[TJ[ii_], TI[ii_]], fl_)
    tm[ii_[0][inn], ii_[1][inn]] = PADDOCK_TILE; tm.astype(np.uint8).tofile(os.path.join(OUT, "tilemap"))
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
    for f_ in ("sand2.png", "sand3.png"):                                # v22c (« fais le sable jaune »)
        jaunir(os.path.join(sd_, f_))
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
            if inside(np.array([[x_, z_]]), fl)[0] and x_ < XPAD - 4.0 and sand_t.query([x_, z_])[0] > 34.0                     and ride_t.query([x_, z_])[0] > 12.0:
                put_(x_, z_)
    ov = ov + (sand if RF_SAND_DECALS else [])           # v23 (« pas un sable blanc avec des taches ») : plus de décals sable RF
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
        elif float(v_[1]) < 100.0:                                       # v21d : panneau (et bas des élingues) FINISH_DOWN ft plus bas
            v_[1] = "%.6f" % (float(v_[1]) - FINISH_DOWN); Lj[k_] = " ".join(v_)
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
    BP.REPORT['zion_v19'] = dict(paddock=[round(v) for v in (x0, x1, z0, z1)], dalles_tuiles=int(inn.sum()), x_paddock=round(XPAD, 1), overlay=len(ov), decals_gardes=len(dl),
                                 start=(round(q[0], 1), round(q[1], 1), round(rf_, 1)), toit_finish=round(rfin, 1), grilles=t_.count(jm))


START_Y = 15.0
BALE_V, BALE_STEP, BALE_GAP = 15.5, 9.6, 25.0
BALE_STEP2, BALE_SLIDE, ARCH_XC = 2 * 9.6, 4.0, 18.0   # v23 : pieds au bord de la piste (était 26)
BP.BOARD_CUT = True                # v24b : flancs coupés derrière les panneaux Milwaukee / AMV
BP.ARCH_CUT = None                 # v23c : pas de découpe sous les pieds
    # v21d : 1 sur 2, glissement max, pieds de l'arche   # v21c : ballots comme RF Anaheim 1 (|v| 15-16 ft, pas 9,6 ft)


def bale_sponsor(g, u, n):
    """v23c : sponsor des ballots selon la zone (code couleur de l'utilisateur) ; n alterne FIVE / « 5 »."""
    t, f = g['tag'][:2], u / g['L']; five = 'five' if n % 2 == 0 else 'five5'
    if t == 'L5':
        return five if f < 0.4 else 'minerva'
    if t == 'L2':
        return 'automoto' if f < 0.5 else 'honda'
    if t == 'L1':
        return 'mv'
    if t == 'LR':
        if LP.SAND_LR and u <= LP.SAND_LR[1]:
            return '50factory'
        return 'milwaukee' if u <= LP.CAMEL_U + len(LP.CAMEL) * 0.1 + 3.0 else 'yamaha'
    if t == 'L6':
        return 'yamaha' if f < 0.45 else five
    return 'mxsim'


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
    import deco_v22 as D22                                            # v22 : murs + arche refaits d'après les vraies photos (deco_v22.py)
    D22.tarp_texture(sd); AT = D22.air_texture(sd); NT = D22.net_texture(sd)
    bj, bp, bs = DV.bale_u(sd, 'noir')
    D22.NT_.update(NT)
    for k, g in enumerate(g_ for g_ in BP.PATH.segs if g_['kind'] == 'T' and g_.get('berm')):
        sp_ = next((v for k_, v in D22.TURN_SPONSOR.items() if g['tag'].startswith(k_)), None)       # v23 : logo du sponsor du virage
        # v23c : murs droits, même hauteur, à l'entrée du virage (3 modules pour un 90°, 4 pour un 180°), couleurs du sponsor
        w = D22.turn_wall_v25(sd, k, g, Hf, sp_); rep_['murs'].append((g['tag'][:5], sp_, w['f'], w['modules'], w['nets']))   # v25 : mur entrée -> sortie, filets choisis
        gy, gx = np.gradient(Hm[int(g['cz'] / s_) - 2:int(g['cz'] / s_) + 3, int(g['cx'] / s_) - 2:int(g['cx'] / s_) + 3], s_)
        assert max(abs(gx).max(), abs(gy).max()) < 0.02, ("origine du mur pas à plat", g['tag'])
        for jm, png, shp_ in w['files']:
            lines.append(line(g['cx'], g['cz'], 0.0, jm, png, shp_))
    # v21c (« place les bottes de paille comme les tracks RF le font ; dans les enchaînements uniquement, pas les virages ; et pas les
    # whoops puisqu'on a déjà mis ») : mesuré sur RF Anaheim 1 (608 bottes) : une rangée de chaque côté du couloir à 15-16 ft de l'axe
    # (bord du dessus des bosses), 9,6 ft de centre à centre, dans le sens de la piste. Ici : nos ballots en U noirs, le long de chaque
    # enchaînement (blocs d'au moins 2 obstacles à moins de BALE_GAP ft l'un de l'autre), ni whoops, ni saut du freestyle, ni virages.
    nb_ = 0; bale_files = {}
    for g in BP.PATH.segs:
        if g['kind'] != 'S' or not g.get('sections'):
            continue
        c, s2 = np.cos(g['t']), np.sin(g['t']); nrm = np.array([-s2, c]); yaw = float(np.arctan2(-s2, c))
        for prof, u0, name in g['sections']:
            if name == LP.L3_SEC or 'roller' in name:
                continue
            its = [(u0 + it_[1], u0 + it_[2]) for it_ in combos[name]['items'] if not it_[0].startswith('whoops')]
            blocks, cur = [], []
            for a_, b_ in its:
                if cur and a_ - cur[-1][1] > BALE_GAP:
                    blocks.append(cur); cur = []
                cur.append((a_, b_))
            if cur:
                blocks.append(cur)
            for bl in blocks:
                if len(bl) < 2:
                    continue
                ua, ub = max(bl[0][0], 4.0), min(bl[-1][1], g['L'] - 4.0)
                # v21d (« mets-en 1 sur 2 ; évite d'en mettre sur les angles en haut des bosses, décale légèrement ») : un pas sur deux
                # (19,2 ft) ; chaque ballot glisse de +-BALE_SLIDE ft vers l'endroit le plus plat de sa rangée (pente + courbure)
                for side_ in (-1, 1):
                    uu = np.arange(ua, ub + 0.01, 0.25); P_ = np.c_[g['x0'] + uu * c, g['z0'] + uu * s2] + nrm * side_ * BALE_V
                    hh = Hf(P_[:, 0], P_[:, 1]); sl_ = np.abs(np.gradient(hh, 0.25)); cv_ = np.abs(np.gradient(np.gradient(hh, 0.25), 0.25))
                    from scipy.ndimage import maximum_filter1d
                    bad = maximum_filter1d(0.25 * sl_ + 4.0 * cv_, int(1.6 / 0.25))        # surtout les arêtes (courbure) ; le pied entier compte
                    t_ = ua + (ub - ua - BALE_STEP2 * int((ub - ua) / BALE_STEP2)) / 2; nk_ = 0
                    while t_ <= ub + 1e-6:
                        w_ = np.nonzero(np.abs(uu - t_) <= BALE_SLIDE)[0]; k_ = w_[int(np.argmin(bad[w_]))]
                        # v23c (« enlève les deux bottes de paille à l'intérieur ») : pas les 2 premières à droite de L6
                        skip_ = g['tag'].startswith('L6') and side_ > 0 and bl is blocks[0] and nk_ < 2
                        if bad[k_] < 0.5 and not skip_:
                            key_ = bale_sponsor(g, uu[k_], nb_); fb_ = bale_files.setdefault(key_, DV.bale_u(sd, key_))
                            lines.append(line(P_[k_, 0], P_[k_, 1], yaw, *fb_)); nb_ += 1
                        nk_ += 1; t_ += BALE_STEP2
    rep_['ballots'] = nb_
    # arche 50 Factory : couloir Est (LR) ; v21d (« tu l'as mise entre les deux bosses, mets-la à l'appel, sur la première bosse ») :
    # origine sur la crête du saut de sortie (le modèle descend jusqu'au sol), pieds à +-ARCH_XC ft, hors des flancs de la bosse
    gL = next(g for g in BP.PATH.segs if g['kind'] == 'S' and g['tag'].startswith('LR'))
    prof, u0, name = gL['sections'][0]; it = combos[name]['items'][0]; i0_, i1_ = int(it[1] / 0.1), int(it[2] / 0.1)
    ua = u0 + it[1] + float(np.argmax(prof[i0_:i1_])) * 0.1
    c, s2 = np.cos(gL['t']), np.sin(gL['t']); pa = (gL['x0'] + ua * c, gL['z0'] + ua * s2); ha = float(Hf(*pa)[0])
    feet = Hf(pa[0] + np.array([-s2, s2]) * ARCH_XC, pa[1] + np.array([c, -c]) * ARCH_XC)
    assert float(np.max(feet)) < 1.2, ("pieds de l'arche trop enterrés", feet)   # v23c : plus de découpe carrée (« évite les carrés autour »)
    aj, ap, as_ = D22.arche_50f(sd, drop=ha, xc=ARCH_XC)
    lines.append(line(pa[0], pa[1], float(np.arctan2(c, s2)), aj, ap, as_)); rep_['arche'] = (round(pa[0], 1), round(pa[1], 1), round(ha, 2))
    # v23 (« à l'intérieur, mets un truc pour pas que ça puisse couper ») : un boudin noir de 18 ft entre les centres des 2 virages après l'arrivée
    ga_ = next(g for g in BP.PATH.segs if g['tag'].startswith('T_L5a')); gb_ = next(g for g in BP.PATH.segs if g['tag'].startswith('T_L5b'))
    for f_ in ("boudin_logo3.jm", "boudin_logo3.shp"):
        shutil.copy(os.path.join(BP.ROOT, "assets", "props", f_), os.path.join(sd, f_))
    bk_ = np.asarray(Image.open(os.path.join(BP.ROOT, "assets", "props", "boudin_fly3.png")).convert('RGB')).copy(); hb_ = int(bk_.shape[0] * 0.915)
    bk_[:hb_] = (22, 22, 24); Image.fromarray(bk_).save(os.path.join(sd, "boudin_noir3.png"))
    d_ = np.array([gb_['cx'] - ga_['cx'], gb_['cz'] - ga_['cz']]); d_ /= np.linalg.norm(d_)
    lines.append(line((ga_['cx'] + gb_['cx']) / 2, (ga_['cz'] + gb_['cz']) / 2, float(np.arctan2(d_[1], -d_[0])), "boudin_logo3.jm", "boudin_noir3.png", "boudin_logo3.shp"))
    # v23c (« les trucs gonflables qu'on mettait aux intérieurs de virage ») : poteau rond de Saint-Georges à l'intérieur de chaque virage,
    # aux couleurs du sponsor du virage (pas dans les 2 virages après l'arrivée : boudin anti-coupe)
    from engine import turn_mid_angle
    sgm_st = os.path.join(BP.ROOT, "tracks", "USLAND2026SaintGeorgesbyBazo", "statue")
    for f_ in ("pylon_round.jm", "pylon_round.shp"):
        shutil.copy(os.path.join(sgm_st, f_), os.path.join(sd, f_))
    npy = 0
    for g in BP.PATH.segs:
        if g['kind'] != 'T' or abs(g['ang']) < 89 or g['tag'].startswith(('T_L5a', 'T_L5b')):
            continue
        mid = turn_mid_angle(g); r_ = max(1.5, g['r'] - 15.2 - 1.5); x_, z_ = g['cx'] + r_ * np.cos(mid), g['cz'] + r_ * np.sin(mid)
        key_ = next((v for k_, v in D22.TURN_SPONSOR.items() if g['tag'].startswith(k_)), 'mxsim')
        lines.append(line(x_, z_, float(np.arctan2(np.cos(mid), np.sin(mid))), "pylon_round.jm", D22.pylon_skin(sd, sgm_st, key_), "pylon_round.shp")); npy += 1
    rep_['poteaux'] = npy
    # v23c (« la réception du saut freestyle, AMV : 2 bottes de paille dans la descente, et sur le dessus ») : 4 ballots AMV
    g3 = next(g for g in BP.PATH.segs if g['kind'] == 'S' and g['tag'].startswith('L3'))
    for prof, u0, name in g3['sections']:
        if name != LP.L3_SEC:
            continue
        it = [i for i in combos[name]['items'] if 'butte' in i[0]][0]; i0_, i1_ = int(it[1] / 0.1), int(it[2] / 0.1)
        uc = u0 + it[1] + float(np.argmax(prof[i0_:i1_])) * 0.1; ue = u0 + it[2]
        top_ = np.nonzero(prof[i0_:i1_] >= prof[i0_:i1_].max() - 1.2)[0]; ut0, ut1 = u0 + it[1] + top_[0] * 0.1, u0 + it[1] + top_[-1] * 0.1
        c, s2 = np.cos(g3['t']), np.sin(g3['t']); nrm = np.array([-s2, c]); yaw = float(np.arctan2(-s2, c)); fa = DV.bale_u(sd, 'amv')
        for u_ in (ut0 + 1.5, ut1 - 1.5):   # v23f (« sur les bords de la bosse, juste avant l'angle, pas au milieu »)
            for side_ in (-1, 1):
                p_ = np.array([g3['x0'] + u_ * c, g3['z0'] + u_ * s2]) + nrm * side_ * BALE_V; lines.append(line(p_[0], p_[1], yaw, *fa))
    # v23c : bâches drapées sur les flancs : saut Milwaukee (LR) et réception du freestyle (plaque AMV)
    gR = next(g for g in BP.PATH.segs if g['kind'] == 'S' and g['tag'].startswith('LR'))
    for side_, nm_ in ((-1, 'bache_milwaukee_g'), (1, 'bache_milwaukee_d')):
        # v23d : panneau « carton » (objet) au lieu de la bâche drapée
        O_, jm_, png_, shp_ = D22.board_v24(sd, nm_.replace('bache', 'panneau'), Hf, gR, side_, 'milwaukee')   # v24 : forme dessinée par l'utilisateur
        lines.append(line(O_[0], O_[1], 0.0, jm_, png_, shp_))
    for prof, u0, name in g3['sections']:
        if name == LP.L3_SEC:
            it = [i for i in combos[name]['items'] if 'butte' in i[0]][0]
            for side_, nm_ in ((-1, 'bache_amv_g'), (1, 'bache_amv_d')):
                O_, jm_, png_, shp_ = D22.board_v24(sd, nm_.replace('bache', 'panneau'), Hf, g3, side_, 'amv')   # v24 : forme dessinée par l'utilisateur
                lines.append(line(O_[0], O_[1], 0.0, jm_, png_, shp_))
    # v24 (« avec les 2 ballots de paille posés sur le dessus ») : 2 ballots Milwaukee au milieu du plateau du saut, un de chaque côté
    (pu0, _), (pu1, _), (pu2, _), (pu3, _) = D22.BOARD_POLY['milwaukee']; cR, sR2 = np.cos(gR['t']), np.sin(gR['t']); nR = np.array([-sR2, cR])
    fM = DV.bale_u(sd, 'milwaukee')
    for side_ in (-1, 1):
        p_ = np.array([gR['x0'] + (pu1 + pu2) / 2 * cR, gR['z0'] + (pu1 + pu2) / 2 * sR2]) + nR * side_ * BALE_V
        lines.append(line(p_[0], p_[1], float(np.arctan2(-sR2, cR)), *fM))
    # v25 : cabane noire MX Sim Racing à gauche du saut d'arrivée, signaleur (drapeau) dedans ; portique holeshot Milwaukee
    g5_ = next(g for g in BP.PATH.segs if g['kind'] == 'S' and g['tag'].startswith('L5')); s5_ = g5_['sections'][0]; it5_ = combos[s5_[2]]['items'][2]
    i0c, i1c = int(it5_[1] / 0.1), int(it5_[2] / 0.1); ucab = s5_[1] + it5_[1] + float(np.argmax(s5_[0][i0c:i1c])) * 0.1
    c5, s5 = np.cos(g5_['t']), np.sin(g5_['t']); n5 = np.array([-s5, c5])            # n5 = droite du sens de course
    from scipy.spatial import cKDTree as _KD2
    smp_ = BP.PATH.samples(1.0); other = np.array([BP.PATH.segs[int(k)]['tag'][:2] != 'L5' for k in smp_['seg']]); trO = _KD2(np.c_[smp_['x'][other], smp_['z'][other]])
    # v25 : sur du sol plat (pas contre la pente de l'appel), loin des autres couloirs
    Pc_ = lambda v: np.array([g5_['x0'] + ucab * c5, g5_['z0'] + ucab * s5]) - n5 * v
    flat_ = lambda v: max(float(Hf(*(Pc_(v) + np.array([c5, s5]) * a_ + n5 * b_))[0]) for a_ in (-4, 4) for b_ in (-4, 4)) < 0.25
    vcab = next((v for v in np.arange(28.0, 50.0, 1.0) if flat_(v) and trO.query(Pc_(v))[0] > 16.0), 40.0)
    Cc = np.array([g5_['x0'] + ucab * c5, g5_['z0'] + ucab * s5]) - n5 * vcab        # à gauche
    fz = n5; fx = np.array([fz[1], -fz[0]])                                          # +z de la cabane = vers la piste
    wp = lambda x, y, z: (fx[0] * x + fz[0] * z, y, fx[1] * x + fz[1] * z)
    lines.append(line(Cc[0], Cc[1], 0.0, *D22.cabin_v25(sd, wp))); rep_['cabane'] = (round(ucab, 1), vcab)
    st_ = BP.START; G0 = np.array(st_['gate']); f0 = np.array([np.cos(np.radians(st_['heading'])), np.sin(np.radians(st_['heading']))]); r0 = np.array([-f0[1], f0[0]])
    Ls = float(st_.get('straight', 120.0)); Hp = G0 + f0 * max(20.0, Ls - 12.0) + r0 * 18.0    # bord droit, juste avant le 1er virage
    fzh = -f0; fxh = -r0                                                              # z vers les pilotes, x vers l'intérieur de la piste
    wph = lambda x, y, z: (fxh[0] * x + fzh[0] * z, y, fxh[1] * x + fzh[1] * z)
    lines.append(line(Hp[0], Hp[1], 0.0, *D22.holeshot_v25(sd, wph))); rep_['holeshot'] = (round(float(Hp[0]), 1), round(float(Hp[1]), 1))
    lines.append(line(Hp[0], Hp[1], 0.0, *D22.drill_cutout_v25(sd, wph, 0.9 + 34.0 - 5.6, 13.0 + 1.2)))   # v25 : la perceuse au bout de la bannière
    # signaleurs : panneau 30 s derrière les grilles + signaleur animé (drapeau) dans la cabane ; fichiers repris de Saint-Georges
    shutil.copytree(os.path.join(BP.ROOT, "tracks", "USLAND2026SaintGeorgesbyBazo", "ext", "2024Bh1Conway", "flaggerfiles"),
                    os.path.join(OUT, "ext", "2024Bh1Conway", "flaggerfiles"), dirs_exist_ok=True)
    os.makedirs(os.path.join(OUT, "billboard"), exist_ok=True); Image.new('RGBA', (64, 64), (0, 0, 0, 0)).save(os.path.join(OUT, "billboard", "blank.png"))
    half_ = (LP.N_GATES - 1) / 2 * LP.GATE_PITCH; b1 = G0 - f0 * 25 + r0 * (half_ - 15); b2 = G0 - f0 * 25 - r0 * (half_ - 15)
    ff = "@%s/ext/2024Bh1Conway/flaggerfiles/" % FOLDER
    open(os.path.join(OUT, "flaggers"), "w", newline=chr(10)).write(chr(10).join([
        "[%.6f 0.000 %.6f]" % tuple(b1), "[%.6f 0.000 %.6f]" % tuple(b2), "8.4 1", "10", "@30sec_30.png", "@30sec_turn.seq", "@30sec_5.png",
        "@30sec_run.seq", "@%s/billboard/blank.png" % FOLDER, "", "[%.6f 0.000 %.6f]" % tuple(Cc), "10.5 1", ff + "defaultflag.png", ff + "halfway.png",
        ff + "lastlap.png", ff + "rf.flagger_waving.seq", "", "", "", "[0.00000000 0.000 0.00000000]", "9.6 1", "3 4 5 -1", "@flagger_resting.png",
        "@flagger_waving.seq", ""]))
    # v23e : murs INVISIBLES (collision seule), assez hauts pour ne pas gêner un saut normal : (1) entre la petite table et l'appel du
    # freestyle (« ça saute derrière l'appel ») ; (2) après le Milwaukee, au-dessus du 1er obstacle du triple (« pas sauter dans la 2e,
    # ça fait monter très haut ») ; (3) entre la réception du double et l'appel du triple d'arrivée (« pas sauter par-dessus le triple »)
    def inv_wall(nm, g, u, lo, hi):
        c, s2 = np.cos(g['t']), np.sin(g['t']); nrm = np.array([-s2, c]); P0 = np.array([g['x0'] + u * c, g['z0'] + u * s2])
        h_ = float(Hf(*P0)[0]); sph = [(nrm[0] * v, h_ - h_ + y, nrm[1] * v) for v in np.arange(-16.0, 16.01, 2.6) for y in np.arange(lo, hi + 0.01, 2.6)]
        m = DV.Mesh(); m.tri([(0, -20, 0), (0.01, -20, 0), (0, -20, 0.01)], [(0.5, 0.5)] * 3); m.write(os.path.join(sd, nm + '.jm'))
        DV.K.shp(os.path.join(sd, nm + '.shp'), sph, 1.4, par=(1.5, 1000, 200)); lines.append(line(P0[0], P0[1], 0.0, nm + '.jm', 'bache_paille.png', nm + '.shp'))
        rep_.setdefault('murs_invisibles', []).append((nm, round(u, 1), round(h_ + lo, 1), round(h_ + hi, 1)))
    it_ = combos[LP.L3_SEC]['items'][0]; s3 = next(sec for sec in g3['sections'] if sec[2] == LP.L3_SEC); pr3 = s3[0]
    i0_, i1_ = int(it_[1] / 0.1), int(it_[2] / 0.1); kc_ = i0_ + int(np.argmax(pr3[i0_:i1_]))
    # v23f (« le mur invisible à l'appel du freestyle est complètement buggé, même en enroulant ça fait tomber ; au pire n'en mets pas ») : retiré
    sR = gR['sections'][0]; itR = combos[sR[2]]['items']; kM = next(i for i, it in enumerate(itR) if 'Milwaukee' in it[0])
    inv_wall('invisible_milwaukee', gR, sR[1] + (itR[kM + 1][1] + itR[kM + 1][2]) / 2, 15.0, 40.0)   # v23f : plus haut (« buggés »)
    g5 = next(g for g in BP.PATH.segs if g['kind'] == 'S' and g['tag'].startswith('L5')); s5 = g5['sections'][0]; it5 = combos[s5[2]]['items']
    inv_wall('invisible_arrivee', g5, s5[1] + (it5[1][2] + it5[2][1]) / 2, 13.0, 30.0)   # v23f : « le plus haut pour le saut d'arrivée encore »
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
    BP.WHOOPS_LEFT_GROUND = True                                       # v22c : boudins FLY, au sol à gauche (plus de talus)
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
    # v21d (« pas tous dans le même sens, en mettre un peu dans les deux sens ; en mettre moins, t'en enlèves 3 ») : N_SEMIS camions (on
    # enlève d'abord les équipes en double), espacés régulièrement sur la même longueur, un sur deux tourné de 180° (même emprise)
    V_ = [l.split() for l in open(os.path.join(sd, jm)).read().splitlines()[1:] if len(l.split()) == 8]
    zmn, zmx = min(float(v[2]) for v in V_), max(float(v[2]) for v in V_)
    for f in ["statues"] + ["variants/" + v for v in os.listdir(os.path.join(OUT, "variants")) if v.startswith("statues")]:
        p = os.path.join(OUT, f); L = open(p).read().splitlines(); ks = [k for k, l in enumerate(L) if "/statue/paris/%s " % jm in l]
        if not ks:
            continue
        rows = [(k, re.match(r"\[(\S+) (\S+) (\S+)\] (\S+) (.*)", L[k]).groups()) for k in ks]
        first, dup = [], []
        for k, g_ in rows:
            team = re.search(r"semi_jgsx_(\w+)\.png", g_[4]).group(1)
            (dup if any(team == t for t, _ in first) else first).append((team, (k, g_)))
        keep = sorted([kg for _, kg in first + dup][:N_SEMIS], key=lambda kg: float(kg[1][2]))
        zs_ = [float(g_[2]) for _, g_ in rows]; zz = np.linspace(min(zs_), max(zs_), len(keep)); new = []
        for i, ((k, g_), z_) in enumerate(zip(keep, zz)):
            x_, yaw = float(g_[0]), float(g_[3])
            if i % 2:
                x_ = x_ + (zmn + zmx) * np.sin(yaw); yaw = yaw + np.pi
            new.append("[%.6f %s %.6f] %.6f %s" % (x_, g_[1], z_, yaw, g_[4]))
        L = [l for k, l in enumerate(L) if k not in ks] + new
        open(p, "w", newline=chr(10)).write(chr(10).join(L) + chr(10))
    for f in ["semi.jm"] + ["semi_%s.png" % t for t in tex]:
        if os.path.exists(os.path.join(sd, f)):
            os.remove(os.path.join(sd, f))
    BP.REPORT['semis_jgsx'] = n


BP.render = render_zion
BP.export = export_zion

if __name__ == "__main__":
    BP.main()
