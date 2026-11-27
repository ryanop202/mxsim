"""v15 : « USLAND: Supercross Paris 2026 (version Zion) » - le même tracé et les mêmes obstacles de 2026 que la version USLAND,
mais construits comme ZION.2025.SupercrossParis (son archive, pistes/paris-2026/refs/zion25_full) :
  - formes des bosses, tables, whoops MESURÉES sur ZION (pistes/paris-2026/data/zion_formes.npz, layout_paris mode ZION), saut central et
    triple d'arrivée ZION non retouchés ; écarts ZION ; rayon des virages ZION (28,3 ft, couloirs à 56,6 ft) ;
  - coupe en travers ZION : dessus plat de 35 ft (whoops 40 ft), flancs de 5,2 ft (whoops 2,2 ft) ;
  - appuis : le croissant d'un 180 de ZION (8,1 ft, crête à 52 ft du centre) découpé dans son relief et reposé sur chaque virage
    (comprimé sur les 90, décalé sur le 180 de 37 ft) ;
  - sol : tileinfo, texture, projections, traces de ZION ; décals ZION ; éclairage et ciel ZION ; ombrage calé sur le sien
    (294,2 x lambert + 41,3 avec son soleil).
Sortie : tracks/USLAND2026SupercrossParisZion (piste à part, la version USLAND n'est pas touchée).

  py -3.12 -I pistes/paris-2026/build_zion.py      (après pistes/paris-2026/stade_paris/src/build.py --mx)
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

BP.FOLDER = os.environ.get("PARIS_FOLDER", "USLANDParis")   # v22d (« renomme-la usland paris ») ; était USLAND2026SupercrossParisZion ; v39 : PARIS_FOLDER=USLANDParisbyRyan (version de Ryan, nom de Bazo v38e)
BP.DESC = os.environ.get("PARIS_DESC", "USLAND Paris")      # v22d (« renomme-la usland paris ») ; v39 : PARIS_DESC="USLAND Paris by Ryan"
BP.OUT = os.path.join(BP.ROOT, "tracks", BP.FOLDER)
BP.AP = os.path.join(HERE, "apercu_zion")
BP.SAND_V25 = True                 # v25e : sable en bande droite + vaguelettes
BP.SAND_TL5 = False; BP.SAND_RUTS = False   # v23 : virage après l'arrivée en terre ; sable sans ornières
BP.SAND_CHOP = 0.0                 # v27 (« le sable pas du tout, retourne sur la version d'avant ») : plus de relief remué ; était 0,7 en v26
BP.SAND_GRAD = 0.0                # v36p : tuiles sable / terre plus mélangées aux bouts (le dégradé = décals RF, voir SABLE_RF)
BP.SAND_BED = 0.3                  # v27 (« surélève, un tout petit peu plus haut qu'à côté ») : couche de sable de 0,3 ft (build_paris.sand_waves)
LP.SAND_HW = 18.5                  # v28 (« que ça dépasse un peu moins sur les côtés ») : bande de 40 -> 37 ft
# LP.SAND_HW = 20.0                  # v27 (« vraiment du sable partout, là on dirait de la terre avec une couleur ») : bande de 28 -> 40 ft (toute la piste)
BP.SAND_LD = 0.0                   # v19d (« le virage après le saut d'arrivée en sable, que le virage ») : pas sur la ligne de départ
ZD = BP.ZD
ZF = np.load(os.path.join(HERE, "data", "zion_formes.npz"))
LAT = dict(T=(34.0, 7.0), W=(40.0, 2.2))      # dessus plat, flanc (ft) : obstacles, whoops ; v20 (« la coupe RF, celle d'Anaheim, en
#   gardant la forme des bosses ») : obstacles à la coupe mesurée sur RF Anaheim 1 (dessus 34 ft, flancs 7 ft ; était 35,1 / 5,2)
ZION_R = 28.3
STT_TERRE = True                            # v29c : terre de Saint-Thibéry (texture, couleur, projections, traces) ; False = TERRE_RGB
TERRE_RGB = (171, 130, 50)                  # v29b (photos de Paris 2025 + capture en jeu : « reprends la texture de Saint-Georges, change juste la couleur ») :
#   terre réelle ~(150, 114, 44) ; le jeu rend ~0,87 x la tuile (166 113 68 -> 145 98 58 sur la capture) -> tuile (171, 130, 50) ; v19d : (166, 113, 68)
G, N, S = BP.G, BP.N, BP.S


def lane_zion(out, g, prof, u0, top, side, kl=1.0, kr=1.0, band=10.0, lenl=1.0, lenr=1.0):
    """kl / kr (v22) : facteur de hauteur côté gauche / droit du sens de course, passage doux au milieu (bande de band ft)."""
    L = len(prof) * 0.1; c, s_ = np.cos(g['t']), np.sin(g['t']); half = top / 2 + side + 1.0
    pts = np.array([(g['x0'] + uu * c - vv * s_, g['z0'] + uu * s_ + vv * c) for uu in (u0, u0 + L) for vv in (-half, half)])
    sl, X, Z = G.window(pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max())
    dx, dz = X - g['x0'], Z - g['z0']; u = dx * c + dz * s_ - u0; vs = -dx * s_ + dz * c; v = np.abs(vs)
    pu = np.interp(u / 0.1, np.arange(len(prof)), prof, left=0, right=0)
    if lenl != 1.0 or lenr != 1.0:
        # v38c : chaque côté a aussi sa longueur (autour de la crête) : hauteur x k et longueur x len -> même raideur si len = k,
        # plus raide si len < 1 à hauteur égale ; passage doux au milieu comme avant
        uc_ = float(np.argmax(prof)) * 0.1; side_p = lambda k_, l_: k_ * np.interp((uc_ + (u - uc_) / l_) / 0.1, np.arange(len(prof)), prof, left=0, right=0)
        w = np.clip(vs / band + 0.5, 0, 1); w = w * w * (3 - 2 * w); pu = side_p(kl, lenl) * (1 - w) + side_p(kr, lenr) * w
    elif kl != 1.0 or kr != 1.0:                                   # v > 0 = droite du sens de course
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


def berm_rf(out, g):
    """v28 : virage RF (copie de build_rf.berm_rf) : profil radial mesuré sur RF Anaheim 1 (normalisé) x hauteur de crête selon
    l'avancement dans le virage (entrée -> sortie), ligne de course de A1 calée sur la nôtre ; fondu au-delà des bouts du virage."""
    from engine import turn_mid_angle
    RFF = LP.RFF
    k = 'b180' if abs(g['ang']) > 135 else 'b90'
    rr, P, tt, cc, ride = (np.asarray(RFF[k + s_], float) for s_ in ('_r', '_p', '_t', '_c', '_ride'))
    P = np.maximum(P, 0.0) / P.max()
    gb = BP.berm_seg(g); mid = turn_mid_angle(gb); half_a = np.radians(abs(gb['ang'])) / 2
    rs = g['r'] - float(ride); R = rr.max() + max(rs, 0.0) + 2.0
    sl, X, Z = G.window(g['cx'] - R, g['cx'] + R, g['cz'] - R, g['cz'] + R)
    dx, dz = X - g['cx'], Z - g['cz']; rp = np.hypot(dx, dz) - rs
    rel = np.angle(np.exp(1j * (np.arctan2(dz, dx) - mid)))
    t = rel * -np.sign(gb['ang']) / half_a
    crest = np.interp(np.clip(t, -1, 1), tt, cc)
    over = np.clip((np.abs(t) - 1.0) / np.where(t > 0, 0.40, 0.15), 0, 1); crest = crest * (1 - over * over * (3 - 2 * over))
    h = np.interp(rp, rr, P, left=0.0, right=0.0) * crest * (rp > 0)
    out[sl] = np.maximum(out[sl], h)


BERM_PLATEAU = {}   # v39b (Ryan, capture de T_D : « ce virage ne va pas du tout, horrible ; compare avec les autres ; fais un truc beau, roulant ») :
#   plus de plateau (dessus plat coupé net) ; la coupe du croissant (débruitée, BERM_SMOOTH) garde son dessus arrondi, comme les autres virages ;
#   v39 Bazo : {'T_D ': 1.15} (face x1,15 coupée au max -> arête + dessus plat (~4 ft) jusqu'au mur)
BERM_SMOOTH = 0.5   # v39b : coupe radiale débruitée (ft) pour tous les berms réguliers (sinon stries concentriques)


BERM_LIKE = {'T_D ': 'T_Bb'}   # v39b (Ryan, captures : « reprends ce virage [MX Sim, T_Bb] et mets le même après le saut freestyle, mais
#   garde la même longueur et la même hauteur qu'on a ; juste sa forme ») : T_D prend la forme du croissant de T_Bb (coupe radiale et
#   montée / descente le long du virage), étirée sur l'angle de T_D, à la hauteur de T_D, crête au même rayon que T_D
BERM_SRC = {}


def _berm_polar(g, sl):
    from engine import turn_mid_angle
    jj_, ii_ = np.meshgrid(np.arange(N)[sl[1]], np.arange(N)[sl[0]])
    X_, Z_ = jj_ * S - g['cx'], ii_ * S - g['cz']; r_ = np.hypot(X_, Z_); th_ = np.arctan2(Z_, X_)
    sg = 1.0 if g['ang'] > 0 else -1.0; a0 = turn_mid_angle(g) + np.radians(g['ang']) / 2
    p_ = np.degrees(np.angle(np.exp(1j * (a0 - th_)))) * sg
    return r_, p_, a0, sg


def _berm_extent(T_, r_, p_):
    """début / fin (degrés, là où le croissant dépasse 3 % de sa hauteur), hauteur, rayon de la crête au sommet."""
    hm = T_.max(); pb = np.arange(-60.0, 200.0, 1.0); env = np.array([T_[np.abs(p_ - b) < 0.5].max(initial=0.0) for b in pb])
    on = pb[env > 0.03 * hm]; pm = float(pb[int(np.argmax(env))]); sel = np.abs(p_ - pm) < 1.0
    rc = float(r_[sel][np.argmax(T_[sel])])
    return float(on.min()), float(on.max()), float(hm), rc


def berm_like(tmp, sl, g, src, sl_s, g_s):
    """v39b : le croissant de g remplacé par la forme de celui de g_s (voir BERM_LIKE)."""
    r_, p_, _, _ = _berm_polar(g, sl); T_ = tmp[sl]
    if T_.max() <= 0:
        return
    pa, pz, H, rc = _berm_extent(T_, r_, p_)
    rs_, ps_, a0s, sgs = _berm_polar(g_s, sl_s); pas, pzs, Hs, rcs = _berm_extent(src[sl_s], rs_, ps_)
    p2 = pas + (p_ - pa) / (pz - pa) * (pzs - pas); r2 = r_ - (rc - rcs)          # même place relative dans le virage modèle
    th2 = a0s - sgs * np.radians(p2); x2 = g_s['cx'] + r2 * np.cos(th2); z2 = g_s['cz'] + r2 * np.sin(th2)
    v = map_coordinates(src, [z2 / S, x2 / S], order=1, mode='constant', cval=0.0) * (H / Hs)
    v[(p_ < pa - 2.0) | (p_ > pz + 2.0) | (r2 < 0)] = 0.0
    tmp[sl] = v
    BP.REPORT.setdefault('berm_forme', {})[g['tag'][:4]] = dict(modele=g_s['tag'][:4], debut=round(pa, 1), fin=round(pz, 1), h=round(H, 2),
                                                              crete_r=round(rc, 1), modele_crete_r=round(rcs, 1), modele_h=round(Hs, 2))


def berm_regular(tmp, sl, g, rg):
    """v35 (« regarde la gueule du virage, pas beau ; fais que ce soit linéaire, en gardant la même hauteur ; la sortie pas belle ; pas
    différent en roulé ») : le croissant (bosse au milieu, bouts qui fondent chacun à sa façon, petit palier bas coupé net à la sortie)
    devient un berm régulier : la coupe radiale la plus haute du croissant (même hauteur, même face, même place), gardée tout le long,
    montée sur rg['rin'] degrés depuis le début du berm d'origine, descente sur rg['rout'] degrés jusqu'à sa fin d'origine."""
    from engine import turn_mid_angle
    jj_, ii_ = np.meshgrid(np.arange(N)[sl[1]], np.arange(N)[sl[0]])
    X_, Z_ = jj_ * S - g['cx'], ii_ * S - g['cz']; r_ = np.hypot(X_, Z_); th_ = np.arctan2(Z_, X_)
    a0 = turn_mid_angle(g) + np.radians(g['ang']) / 2                              # centre -> début du virage
    p_ = np.degrees(np.angle(np.exp(1j * (a0 - th_)))) * (1.0 if g['ang'] > 0 else -1.0)   # avancement dans le virage (degrés)
    T_ = tmp[sl]; hm = T_.max()
    if hm <= 0:
        return
    pb = np.arange(-60.0, abs(g['ang']) + 60.0, 1.0); env = np.array([T_[np.abs(p_ - b) < 0.5].max(initial=0.0) for b in pb])
    on = pb[env > 0.03 * hm]; pa, pz = float(on.min()), float(on.max()); pm = float(pb[int(np.argmax(env))])
    rb = np.arange(0.0, r_[np.abs(p_ - pm) < 2.0].max(), 0.25)
    sel = np.abs(p_ - pm) < 2.0; prof = np.array([T_[sel & (np.abs(r_ - b) < 0.2)].max(initial=0.0) for b in rb])
    ss = lambda t: (lambda t_: t_ * t_ * (3 - 2 * t_))(np.clip(t, 0, 1))
    e_ = ss((p_ - pa) / rg['rin']) * ss((pz - p_) / rg['rout'])
    if BERM_SMOOTH and g['tag'][:4] not in BERM_PLATEAU:
        from scipy.ndimage import gaussian_filter1d
        prof = gaussian_filter1d(prof, BERM_SMOOTH / 0.25)
    if g['tag'][:4] in BERM_PLATEAU:
        # v39 (« l'extérieur fait une patate ; pas d'angle sur le dessus, pas un plat sur le dessus avec des beaux contours ») : la coupe
        # prise sur les pixels (bins de 0,25 ft) était bruitée -> les stries concentriques ; elle est débruitée (0,5 ft), puis la face monte
        # x k plus vite et est coupée à la hauteur max : arête nette, dessus plat jusqu'à la crête d'origine (le mur), arrière inchangé
        from scipy.ndimage import gaussian_filter1d
        k_ = BERM_PLATEAU[g['tag'][:4]]; pr_ = gaussian_filter1d(prof, 0.5 / 0.25); H_ = float(pr_.max()); ic_ = int(np.argmax(pr_))
        prof = np.where(np.arange(len(pr_)) <= ic_, np.minimum(H_, pr_ * k_), pr_)
        BP.REPORT.setdefault('berm_plat', {})[g['tag'][:4]] = dict(h=round(H_, 2), plat_ft=round(float((prof >= H_ - 0.01).sum()) * 0.25, 1))
    tmp[sl] = np.interp(r_, rb, prof, right=0.0) * e_
    BP.REPORT.setdefault('berm_regulier', {})[g['tag'][:4]] = dict(debut=round(pa, 1), fin=round(pz, 1), sommet=round(pm, 1), h=round(float(prof.max()), 2))


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
    P1 = LP.pts_prof(LP.POST_FIN['b1'], 1.0); P23 = LP.pts_prof(LP.POST_FIN['b23'], LP.POST_FIN.get('sig23', 1.0))
    P1o = LP.pts_prof(LP.POST_FIN.get('b1o', LP.POST_FIN['b1']), 0.7)            # v23e : extérieur (droite) en appel
    R = 40.0; sl, X, Z = G.window(sx.min() - R, sx.max() + R, sz.min() - R, sz.max() + R)
    tree = cKDTree(np.c_[sx, sz]); d_, i_ = tree.query(np.c_[X.ravel(), Z.ravel()]); i_ = i_.reshape(X.shape)
    dx, dz = X - sx[i_], Z - sz[i_]; v = -dx * np.sin(th[i_]) + dz * np.cos(th[i_]); s_ = st_[i_]
    u0_ = 0.0                                                   # les points de POST_FIN sont déjà en s absolu
    sk_ = LP.POST_FIN.get('skew', 0.0) * np.minimum(v, 0.0)         # v28 : crête plus loin à l'intérieur (v < 0), droite à l'extérieur
    h1i = np.interp((s_ + sk_ - u0_) / 0.1, np.arange(len(P1)), P1, left=0, right=0); h1o = np.interp((s_ + sk_ - u0_) / 0.1, np.arange(len(P1o)), P1o, left=0, right=0)
    wq = np.clip(v / 10.0 + 0.5, 0, 1); wq = wq * wq * (3 - 2 * wq); h1 = h1i * (1 - wq) + h1o * wq
    h1 = h1 * (LP.POST_FIN.get('in_k', 1.0) + (1.0 - LP.POST_FIN.get('in_k', 1.0)) * wq)   # v28 : intérieur un peu plus bas
    if LP.POST_FIN.get('sm1'):                                    # v29 : 1re bosse adoucie à part (fusion avec l'appui du virage)
        h1 = gaussian_filter(h1, LP.POST_FIN['sm1'] / S)
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


PYLON_IN = {'T_TR': 9.0, 'T_E ': 9.0, 'T_Bb': 2.5}   # v29 : Moto Verte 4 ft plus à l'intérieur (« qui gêne moins »), MX Sim 2,5 ft ; v28 : Yamaha
PYLON_XY = {'T_E ': (4.5, 1.4)}   # v38 (rond rouge vu de dessus : « recentre-le ») : 5,4 ft plus au nord ; v29 : (4.5, 6.8)
_PYLON_XY_V29 = {'T_E ': (4.5, 6.8)}   # v29 (rond blanc vu de dessus) : Yamaha posé à (dx, dz) ft du centre du virage   # v28 (« le plot inter est gênant », cercle rouge) : Yamaha 4 ft plus à l'intérieur   # v25e (« le truc à l'intérieur, décale-le, moins dans la trace » ; carré bleu Yamaha) : ft vers le centre


def pylon_spots(path):
    """v25e : poteaux gonflables à l'intérieur des virages (sponsor du virage) : (x, z, mid, clé)."""
    from engine import turn_mid_angle
    import deco_v22 as D22
    out = []
    for g in path.segs:
        if g['kind'] != 'T' or abs(g['ang']) < 89 or g['tag'].startswith(('T_L5a', 'T_L5b')) or not g.get('berm'):   # v25f : pas sur la ligne de départ (T_Ba)
            continue
        mid = g.get('pylon_mid', turn_mid_angle(g)); r_ = max(0.0, g['r'] - 15.2 - 1.5 - next((v for k_, v in PYLON_IN.items() if g['tag'].startswith(k_)), 0.0))
        key_ = next((v for k_, v in D22.TURN_SPONSOR.items() if g['tag'].startswith(k_)), 'mxsim')
        if g['tag'].startswith('T_Bb') and getattr(LP, 'T_B_PYLONS', None):   # v31 : les 2 poteaux aux points de Ryan
            out += [(x_, z_, mid, key_) for x_, z_ in LP.T_B_PYLONS]; continue
        if g.get('pylon_dxz'):                                # v28u : position donnée à la main
            out.append((g['cx'] + g['pylon_dxz'][0], g['cz'] + g['pylon_dxz'][1], mid, key_)); continue
        xy_ = next((v for k_, v in PYLON_XY.items() if g['tag'].startswith(k_)), None)
        if xy_:
            out.append((g['cx'] + xy_[0], g['cz'] + xy_[1], mid, key_)); continue
        out.append((g['cx'] + r_ * np.cos(mid), g['cz'] + r_ * np.sin(mid), mid, key_))
    return out


def cabin_spot(path):
    """v25e (« la cabine trop loin de la pelle : plus dans la pelle, plus haute ») : à gauche de l'appel du saut d'arrivée, 4 ft avant sa
    crête, à 21 ft de l'axe, sur un socle de terre plat de CAB_PAD ft."""
    import layouts_sx as LS
    g5 = next(g for g in path.segs if g['kind'] == 'S' and g['tag'].startswith('L5')); s5 = g5['sections'][0]; it = LS.COMBOS[s5[2]]['items'][2]
    i0, i1 = int(it[1] / 0.1), int(it[2] / 0.1); uc = s5[1] + it[1] + float(np.argmax(s5[0][i0:i1])) * 0.1 - 4.0
    t5 = np.array([np.cos(g5['t']), np.sin(g5['t'])]); n5 = np.array([-t5[1], t5[0]])
    return np.array([g5['x0'], g5['z0']]) + t5 * uc - n5 * CAB_V, t5, n5, uc


CAB_V, CAB_PAD = 25.0, 4.0         # v38 (« la base coupée droite sous la cabane, aussi large, un peu plus haute ») : socle 3 -> 4 ft, flancs droits
CAB_V_V25F = 25.0         # v25f (« un peu dans l'appui, dans la terre ») : 21 -> 25 ft de l'axe
CAB_MAN = 0.0                      # v29 : guérite (deco_v28.booth) ; le signaleur est placé en hauteur absolue dans flaggers (CAB_PAD + CAB_FLAG)
CAB_FLAG = 3.8                     # v38 (« la cabane un peu plus haute ; le monsieur jusqu'au genou ») : pieds 3,8 ft au-dessus du socle, murs 5,5 ft (le mur arrive au genou)
CAB_HC = 5.5
CAB_FLAG_REL = 3.6                 # v38c (« le personnage beaucoup trop haut, descends-le dans la cabane ») : la hauteur du fichier flaggers est comptée
#                                    depuis le sol sous lui (il flottait à 4 + 7,8 ft) : pieds 3,6 ft au-dessus du dessus du bloc, le mur au genou
CAB_FLAG_V29 = 1.2                     # v29 (« un socle dedans qu'on voit pas, que le monsieur dépasse ») : pieds 1,2 ft au-dessus du socle, murs 4,5 ft
# CAB_MAN = 5.2                      # v25f (« on voit pas le mec : une plateforme pour qu'il soit en haut, qui dépasse la cabane ») : ft au-dessus du socle


# v35 (capture après l'arrivée : « le gauche, il y a un à-coup, ça fait un cran, adoucis ») : côté extérieur de T_L5a, l'appui finit
# et la 1re bosse part juste derrière : creux en V entre les deux (0,4 - 0,6 ft) et pli du pied de l'appui. Le creux est rempli au
# niveau du plus bas des deux sommets, le long de la trajectoire (comme de l'eau entre deux bosses), fondu sur les côtés, adouci :
# rien n'est enlevé, l'appui et la bosse gardent leur hauteur. (virage, s début, s fin depuis le début du virage, v min, v max)
L2_B2_LENL = 0.8                   # v38d (« encore un peu plus raide la partie gauche ») : 0,9 -> 0,8
L2_B2_LENL_V38C = 0.9                   # v38c : 2e bosse de L2, côté gauche 10 % plus courte = un peu plus raide
JUNCTIONS = []   # v38e (« mets-moi ça en jeu [appui + bosse fusionnés tels quels] et juste smooth la ligne de transition entre l'appui et la bosse ») : remplissage retiré ; avant : [('T_L5a', 12.0, 38.0, 1.0, 26.0)]   # v38 (« gomme cette ornière, ce trait qui redescend de l'extérieur ; garde un truc smooth ») : remplissage étendu (s 14-33,5 -> 12-38, v 19 -> 26) ; v35 : ('T_L5a', 14.0, 33.5, 1.0, 19.0)


# v38d (carte des petits reliefs : relief - relief lissé à 2 ft) : (1) appui de T_D couvert de petites crêtes concentriques espacées de
# ~1-1,5 ft = les « stries » (« recrée-le, smooth tout ») ; (2) fine crête en arc sur la face intérieure de l'appui de T_L5a = le « rebord »
# après l'arrivée. Lissage local (flou sigma ft) dans un anneau autour du centre du virage (r_min -> r_max ft, fondu 3 ft) : les petites
# crêtes disparaissent, la forme de l'appui et de la bosse (10-20 ft) reste ; le centre du virage (origine du mur) n'est pas touché
SMOOTH_ZONES = []   # v39 (« le virage après le freestyle fait une patate, pas d'angle, pas de plat dessus ») : flou de T_D retiré (coupe radiale débruitée + plat dans berm_regular) ; v38d : [('T_D ', 22.0, 80.0, 1.2)]   # v38e (« il n'y a plus l'angle de l'appui de base ») : T_L5a retiré (le flou arrondissait tout l'appui) ; raccord appui / bosse : crease_smooth


def smooth_zones(H, path):
    from scipy.ndimage import gaussian_filter
    ss = lambda t: (lambda t_: t_ * t_ * (3 - 2 * t_))(np.clip(t, 0, 1)); H = H.copy(); rep_ = []
    for tag, r0, r1, sg in SMOOTH_ZONES:
        g = next(g for g in path.segs if g['tag'].startswith(tag))
        sl, X, Z = G.window(g['cx'] - r1 - 6, g['cx'] + r1 + 6, g['cz'] - r1 - 6, g['cz'] + r1 + 6)
        r = np.hypot(X - g['cx'], Z - g['cz']); w = ss((r - r0) / 3.0) * ss((r1 - r) / 3.0) * ss((g['cx'] + 2.0 - X) / 3.0)   # côté ouest seulement (L5 / L2 pas touchées)
        hs = gaussian_filter(H[sl], sg / S); d0 = float(np.abs(H[sl] - hs)[w > 0.5].max()); H[sl] = H[sl] * (1 - w) + hs * w
        rep_.append((tag, round(d0, 2)))
    BP.REPORT['zones_lissees'] = rep_
    return H


# v38e (review v38d, « il y a toujours ce petit rebord dans le virage après le saut d'arrivée, enlève-le, ça fait 10 fois » ; « je ne veux
# pas remplir » ; « il n'y a plus l'angle de l'appui de base » ; vues 3D des 2 couches séparées : « mets-moi ça en jeu [appui + bosse
# fusionnés tels quels] et juste smooth la ligne de transition entre l'appui et la bosse ») : à la sortie de T_L5a le roller (couche des
# sauts) bute contre l'appui (couche des virages) ; le sol = le plus haut des deux, d'où un angle vif sur la ligne où ils se croisent. Cette
# ligne seulement est arrondie : union lisse sm(a, b) = (a + b + sqrt((a - b)² + k²)) / 2 au lieu de max(a, b) (ne change que là où les 2
# couches sont à moins de k ft l'une de l'autre ; au plus + k / 2 sur la ligne), dans une zone autour du bout de l'appui (fondus).
# (virage, angle de, à, fondu deg, r min, r max, k ft)
CREASE_SMOOTH = [('T_L5a', -205.0, -135.0, 10.0, 24.0, 48.0, 0.8)]


def _keep_layers():
    """garde les couches du relief (sauts, whoops, virages, fmx) calculées par build_paris.render pour crease_smooth."""
    if getattr(BP, '_render_orig', None) is None:
        BP._render_orig = BP.render
        def render_(path, st):
            r_ = BP._render_orig(path, st); BP._LAYERS = r_; return r_
        BP.render = render_


def crease_smooth(H, path):
    ss = lambda t: (lambda t_: t_ * t_ * (3 - 2 * t_))(np.clip(t, 0, 1)); H = H.copy(); rep_ = []
    jumps, whoops, berms, fmx = BP._LAYERS
    for tag, a0, a1, fd, r0, r1, k in CREASE_SMOOTH:
        g = next(g for g in path.segs if g['tag'].startswith(tag)); cx, cz = g['cx'], g['cz']; R = r1 + 2.0
        sl, X, Z = G.window(cx - R, cx + R, cz - R, cz + R)
        r = np.hypot(X - cx, Z - cz); a = np.degrees(np.arctan2(Z - cz, X - cx))
        am = (a0 + a1) / 2; da = (a - am + 180.0) % 360.0 - 180.0; hw = (a1 - a0) / 2
        w = ss((hw - np.abs(da)) / fd) * ss((r - r0) / 3.0) * ss((r1 - r) / 3.0)
        b_ = berms[sl]; j_ = np.maximum.reduce([jumps[sl], whoops[sl], fmx[sl]])
        add = ((b_ + j_ + np.sqrt((b_ - j_) ** 2 + k * k)) / 2 - np.maximum(b_, j_)) * w
        add = add * ss(np.minimum(b_, j_) / 0.6)             # seulement là où les 2 couches existent (fondu, pas de bord)
        H[sl] = H[sl] + add; rep_.append((tag, round(float(add.max()), 2)))
    BP.REPORT['raccord_appui_bosse'] = rep_
    return H


def mats_clear(H, path):
    """v38d (« la grille passe sous l'appui : arrête l'appui plus derrière, qu'il y ait la place pour la grille ») : sol remis à plat sous
    les grilles des rampes FMX (+1 ft autour), fondu sur 4 ft : l'arrière de l'appui de T_Bb s'arrête avant la grille."""
    ss = lambda t: (lambda t_: t_ * t_ * (3 - 2 * t_))(np.clip(t, 0, 1)); H = H.copy(); n = 0
    for r_, Lm_ in zip(LP.fmx_ramps(path), RAMP_MAT_L):
        h_ = r_['heading']; d_ = np.array([np.cos(h_), np.sin(h_)]); foot_ = np.array(r_['lip']) - d_ * LP.FMX_MODEL['model_len']
        c_ = foot_ - d_ * (Lm_ / 2 + 0.3); R_ = Lm_ / 2 + 6.0
        sl, X, Z = G.window(c_[0] - R_, c_[0] + R_, c_[1] - R_, c_[1] + R_)
        a_ = np.abs((X - c_[0]) * d_[0] + (Z - c_[1]) * d_[1]) - (Lm_ / 2 + 1.0); b_ = np.abs(-(X - c_[0]) * d_[1] + (Z - c_[1]) * d_[0]) - 3.0
        out_ = np.hypot(np.maximum(a_, 0), np.maximum(b_, 0)); H[sl] = H[sl] * ss(out_ / 4.0); n += 1
    BP.REPORT['grilles_a_plat'] = n
    return H


def smooth_junctions(H, path):
    from scipy.ndimage import gaussian_filter, map_coordinates as mc_
    from scipy.spatial import cKDTree
    smp = path.samples(0.25); H = H.copy(); rep_ = []
    ss = lambda t: (lambda t_: t_ * t_ * (3 - 2 * t_))(np.clip(t, 0, 1))
    for tag, sa, sb, va, vb in JUNCTIONS:
        g = next(g for g in path.segs if g['tag'].startswith(tag)); sa, sb = g['s0'] + sa, g['s0'] + sb
        SS = np.arange(sa - 4.0, sb + 4.0, 0.25); VV = np.arange(va - 3.0, vb + 3.0, 0.25)
        k = np.clip(np.searchsorted(smp['s'], SS), 0, len(smp['s']) - 1); th, xs, zs = smp['th'][k], smp['x'][k], smp['z'][k]
        X = xs[None, :] - VV[:, None] * np.sin(th)[None, :]; Z = zs[None, :] + VV[:, None] * np.cos(th)[None, :]
        h = mc_(H, [Z / S, X / S], order=1)
        inn = (SS >= sa) & (SS <= sb); fill = np.zeros_like(h)
        for r in range(len(VV)):
            hr = h[r, inn]; lv = np.minimum(np.maximum.accumulate(hr), np.maximum.accumulate(hr[::-1])[::-1]); fill[r, inn] = lv - hr
        fill = np.maximum(fill, gaussian_filter(fill, (1.0 / 0.25, 1.0 / 0.25))) * (ss((VV - va) / 3.0) * ss((vb - VV) / 3.0))[:, None]
        fill = fill * (ss((SS - sa) / 5.0) * ss((sb - SS) / 5.0))[None, :]   # v38c (« un rebord, enlève-le complètement, toujours smooth ») : fondu aussi aux 2 bouts (coupé net avant)   # adouci sans rien perdre du remplissage
        tr = cKDTree(np.c_[xs, zs]); pad = vb + 6.0
        sl, Xw, Zw = G.window(X.min() - 2, X.max() + 2, Z.min() - 2, Z.max() + 2)
        d_, i_ = tr.query(np.c_[Xw.ravel(), Zw.ravel()]); i_ = i_.reshape(Xw.shape)
        vw = -(Xw - xs[i_]) * np.sin(th[i_]) + (Zw - zs[i_]) * np.cos(th[i_]); sw = SS[i_]
        add = mc_(fill, [(vw - VV[0]) / 0.25, (sw - SS[0]) / 0.25], order=1, cval=0.0) * (d_.reshape(Xw.shape) < pad)
        H[sl] = H[sl] + add
        rep_.append((tag, round(float(sa), 1), round(float(sb), 1), round(float(add.max()), 2)))
    BP.REPORT['raccords_adoucis'] = rep_
    return H


def pads(H, path):
    """v25e (« mets bien des monticules de terre sous les plots intérieurs » ; cabane plus haute) : petits socles de terre plats (le jeu
    ne penche pas un objet posé à plat) : poteaux 0,8 ft (dessus 2,2 ft de rayon, flancs 2,5 ft) ; cabane : dessus plat à CAB_PAD ft."""
    ss = lambda t: (lambda t_: t_ * t_ * (3 - 2 * t_))(np.clip(t, 0, 1)); H = H.copy()
    for x, z, mid, key in pylon_spots(path):
        sl, X, Z = G.window(x - 6, x + 6, z - 6, z + 6); r = np.hypot(X - x, Z - z); h0 = float(map_coordinates(H, [[z / S], [x / S]], order=1)[0])
        gc_ = min((g_ for g_ in path.segs if g_['kind'] == 'T'), key=lambda g_: np.hypot(g_['cx'] - x, g_['cz'] - z))
        kc_ = 1.0 if np.hypot(gc_['cx'] - x, gc_['cz'] - z) < 1.6 else ss((np.hypot(X - gc_['cx'], Z - gc_['cz']) - 1.0) / 1.0)   # poteau AU centre : socle entier ; v29 : le centre du virage (origine du mur) reste plat même si le poteau s'en approche
        H[sl] = np.maximum(H[sl], h0 + 0.8 * ss((3.4 - r) / 1.8) * kc_)   # dessus plat 1,6 ft de rayon, pied à 3,4 ft (le centre du virage reste plat)
    C, t5, n5, uc = cabin_spot(path); sl, X, Z = G.window(C[0] - 12, C[0] + 12, C[1] - 12, C[1] + 12)
    du, dv = (X - C[0]) * t5[0] + (Z - C[1]) * t5[1], (X - C[0]) * n5[0] + (Z - C[1]) * n5[1]
    blk_ = (np.abs(du) <= 1.6) & (np.abs(dv) <= 1.4)                   # v38d (« la terre plus petite, juste un socle pour le mec, qu'on ne la voie pas ») : socle 3,2 x 2,8 ft caché dans la guérite ; v38 : 4,5 x 4
    H[sl] = np.where(blk_, np.maximum(H[sl], CAB_PAD), H[sl])
    inn = (np.abs(du) < 1.6) & (np.abs(dv) < 1.6); H[sl] = np.where(inn, np.maximum(H[sl], CAB_PAD + CAB_MAN), H[sl]) if CAB_MAN else H[sl]   # plateforme du signaleur (cachée par la cabane)
    BP.REPORT['socles'] = len(pylon_spots(path)) + 1
    return H


BOARD_END_FADE = {'amv': 7.0}


def board_cut_layer(lay, g, kind):
    """v25c (« de l'autre côté de la bosse t'as tout coupé, cassé l'enchaînement ») : la terre de CE saut seulement (couche à part) est
    coupée au plan du panneau (|v| > BOARD_VB - 0,2 ft, fondu de 0,8 ft), sur la longueur du panneau ; les autres couloirs ne sont pas touchés."""
    poly = LP.BOARD_POLY[kind]; ua, ub = poly[0][0], poly[-1][0]; vb = LP.BOARD_VB[kind]; c, s_ = np.cos(g['t']), np.sin(g['t']); R = vb + 70
    pts = np.array([(g['x0'] + uu * c - vv * s_, g['z0'] + uu * s_ + vv * c) for uu in (ua - 4, ub + 4) for vv in (-R, R)])
    sl, X, Z = G.window(pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max())
    dx, dz = X - g['x0'], Z - g['z0']; u = dx * c + dz * s_; v = np.abs(-dx * s_ + dz * c)
    ss = lambda t: (lambda t_: t_ * t_ * (3 - 2 * t_))(np.clip(t, 0, 1))
    # v35 (capture du départ : « tu passes au bord du saut AMV, modifie pour qu'on ne prenne pas ce trou ») : au bout du panneau, le flanc
    # coupé reprenait en 1,5 ft (marche de 0,3 - 0,4 ft au coin, là où passe le départ) ; fondu sur BOARD_END_FADE ft
    m = ss((v - (vb - 1.0)) / 0.8) * ss((u - ua) / 1.5) * ss((ub - u) / BOARD_END_FADE.get(kind, 1.5))
    lay[sl] *= (1 - m)


def wall_fill(H, path):
    """v25c (« tous les virages : t'as fait des escaliers, fais droit » ; « quitte à mettre un peu plus de terre à l'entrée et à la sortie
    pour cacher la hauteur des murs en gris ») : la géométrie des murs (deco_v22.wall_geom, une seule hauteur par virage) est calculée ici
    sur le terrain, puis la terre est remontée entre le haut du berm et le pied du mur jusqu'au haut du mur (-0,12 ft), fondu aux bouts."""
    import deco_v22 as D22
    Hf = lambda x, z: map_coordinates(H, [np.atleast_1d(z) / S, np.atleast_1d(x) / S], order=1)
    ss = lambda t: (lambda t_: t_ * t_ * (3 - 2 * t_))(np.clip(t, 0, 1)); H = H.copy(); rep_ = {}
    for g in path.segs:
        if g['kind'] != 'T' or not g.get('berm'):
            continue
        W_ = D22.wall_geom(g, Hf); D22.WALL_GEOM[g['tag']] = W_
        rc, rcr, Wd, fs, ang, th_in, cx, cz, h0 = (W_[k] for k in ('rc', 'r_crest', 'W', 'fs', 'ang', 'th_in', 'cx', 'cz', 'h0'))
        target = h0 + W_['ytop_rel'] - 0.12; R = rc + Wd / 2 + 2
        sl, X, Z = G.window(cx - R, cx + R, cz - R, cz + R); dx, dz = X - cx, Z - cz; r = np.hypot(dx, dz)
        f = -np.angle(np.exp(1j * (np.arctan2(dz, dx) - th_in))) / ang; fp = 8.0 / (abs(ang) * rc)
        wf = ss((f - (fs[0] - fp)) / fp) * ss(((fs[-1] + fp) - f) / fp)
        r_in, r_w = rcr - 9.0, rc - Wd / 2 + 0.3
        wr = ss((r - r_in) / (r_w - r_in)) * (r <= rc + Wd / 2 + 0.5)
        fill = h0 + (target - h0) * wr * wf
        H[sl] = np.maximum(H[sl], fill); rep_[g['tag'][:5]] = round(float(W_['ytop_rel']), 2)
    BP.REPORT['murs_hauteur'] = rep_
    return H


def render_zion(path, st):
    SPECIAL_ = []                                               # v25d : (couche, couloir, panneau) des sauts à panneaux
    import layouts_sx as LS
    jumps = np.zeros((N, N)); whoops = np.zeros((N, N)); berms = np.zeros((N, N)); fmx = np.zeros((N, N)); secs = []
    walls = np.zeros((N, N))      # v20b : murets à part (le pied arrondi des whoops les étalait dans chaque creux = un rebord)
    for g in path.segs:
        if g['kind'] == 'S':
            for prof, u0, name in g['sections']:
                lay = whoops if 'whoops' in name else jumps
                if name == LP.L3_SEC:                           # v18 : saut du milieu de la version USLAND (« le double central du mien »)
                    tmp_ = np.zeros_like(jumps); BP.render_mid(tmp_, g, prof, u0, name)
                    SPECIAL_.append((tmp_, g, 'amv'))           # v25d : fusionné après l'adoucissement des pieds, coupe refaite après
                else:
                    for it in LS.COMBOS[name]['items']:        # v16 : obstacles ZION (coupe ZION), whoops USLAND (coupe USLAND + murets)
                        i0, i1 = int(it[1] / 0.1), min(int(it[2] / 0.1) + 1, len(prof))
                        if it[0].startswith('whoops'):
                            # v20b : whoops pleine forme jusqu'au pied droit des murets (|v| = 17 ft), murets seuls dans leur couche
                            BP.render_lane_block(G, whoops, g, prof[i0:i1], u0 + it[1], 2 * BP.WALL_TOP[0])
                            whoops_walls(walls, g, prof, u0, it, with_whoops=False, left=False)   # v22c : pas de talus à gauche
                        else:
                            sp_ = [q for q in LP.SPLIT_Z.get(name, []) if q[0] - 0.5 <= it[1] and it[2] <= q[1] + 0.5]   # v22
                            kk_ = tuple(sp_[0][2:]) if sp_ else (1.0, 1.0)
                            kk_ = kk_ + (1.0, 1.0)[len(kk_) - 2:]
                            if name.startswith('PAR-L2') and it is LS.COMBOS[name]['items'][1]:
                                kk_ = (kk_[0], kk_[1], L2_B2_LENL, 1.0)   # v38c (« la vraie bosse, à gauche un petit peu plus raide, tout aussi haute, smooth entre les deux »)
                            if it[0].startswith('saut Milwaukee'):      # v25c : coupe sur CE saut seulement
                                tmp_ = np.zeros_like(lay); lane_zion(tmp_, g, prof[i0:i1], u0 + it[1], *LAT['T'], kl=kk_[0], kr=kk_[1], lenl=kk_[2], lenr=kk_[3])
                                SPECIAL_.append((tmp_, g, 'milwaukee'))
                            else:
                                lane_zion(lay, g, prof[i0:i1], u0 + it[1], *LAT['T'], kl=kk_[0], kr=kk_[1], lenl=kk_[2], lenr=kk_[3])
                secs.append(dict(lane=g['tag'], name=name, u0=round(u0, 1), L=round(len(prof) * 0.1, 1), H=round(float(prof.max()), 2),
                                 items=[(i[0], round(i[1], 1), round(i[2], 1)) for i in LS.COMBOS[name]['items']]))
        elif g.get('berm'):                                  # v16 : virages USLAND (berms JGSX, comme la version USLAND)
            from engine import render_berm_stamp, turn_mid_angle, berm_ang_scale
            gb = BP.berm_seg(g)
            gain = LP.BERM90_GAIN if abs(abs(gb['ang']) - 90) < 1 else LP.BERM180_GAIN
            gain = LP.BERM_GAIN_TAG.get(g['tag'][:4], gain)
            tmp = np.zeros((N, N))
            if g['tag'][:4] in LP.RF_BERM_TAGS:              # v28 : berm RF mesuré (profil radial + crête selon l'avancement)
                berm_rf(tmp, g); berms[:] = np.maximum(berms, tmp)
                continue
            sl = render_berm_stamp(G, tmp, g['berm'], g['cx'], g['cz'], turn_mid_angle(gb),
                                   ang_scale=berm_ang_scale(g['berm'], gb['ang']), r_shift=max(0.0, g['r'] - LP.RB))
            fe_ = LP.BERM_END_FADE.get(g['tag'][:4])
            if fe_:                                          # v20c : le berm s'arrête avant la sortie du virage, fondu doux
                nx_ = path.segs[path.segs.index(g) + 1]; a_ex = np.arctan2(nx_['z0'] - g['cz'], nx_['x0'] - g['cx'])
                jj_, ii_ = np.meshgrid(np.arange(N)[sl[1]], np.arange(N)[sl[0]])
                th_ = np.arctan2(ii_ * S - g['cz'], jj_ * S - g['cx'])
                phi = np.degrees(np.angle(np.exp(1j * (th_ - a_ex) * (1.0 if g['ang'] > 0 else -1.0))))
                t_ = np.clip((phi - fe_[0]) / fe_[1], 0, 1); tmp[sl] *= t_ * t_ * (3 - 2 * t_)
            fs_ = getattr(LP, 'BERM_START_FADE', {}).get(g['tag'][:4])
            if fs_:                                          # v28v (« coupe le début du virage ») : berm à zéro sur les fs_[0] premiers degrés, fondu sur fs_[1]
                lf_ = g['ang'] > 0; t0_ = g['t0']
                a_st = np.arctan2(np.cos(t0_), -np.sin(t0_)) if lf_ else np.arctan2(-np.cos(t0_), np.sin(t0_))
                jj_, ii_ = np.meshgrid(np.arange(N)[sl[1]], np.arange(N)[sl[0]])
                th_ = np.arctan2(ii_ * S - g['cz'], jj_ * S - g['cx'])
                phs = np.degrees(np.angle(np.exp(1j * (a_st - th_) * (1.0 if lf_ else -1.0))))
                t_ = np.clip((phs - fs_[0]) / fs_[1], 0, 1); tmp[sl] *= t_ * t_ * (3 - 2 * t_)
            sg_ = LP.BERM_SOFT_TAG.get(g['tag'][:4])
            if sg_:                                          # v27d : berm adouci (face moins raide), même hauteur max
                from scipy.ndimage import gaussian_filter as _gf
                m0_ = tmp[sl].max(); tmp[sl] = _gf(tmp[sl], sg_ / S); tmp[sl] *= m0_ / max(tmp[sl].max(), 1e-6)
            rg_ = getattr(LP, 'BERM_REGULAR', {}).get(g['tag'][:4])
            if g['tag'][:4] in BERM_LIKE and BERM_LIKE[g['tag'][:4]] in BERM_SRC:
                berm_like(tmp, sl, g, *BERM_SRC[BERM_LIKE[g['tag'][:4]]])
            elif rg_:
                berm_regular(tmp, sl, g, rg_)
            if g['tag'][:4] in BERM_LIKE.values():           # v39b : forme gardée pour les virages qui la reprennent
                BERM_SRC[g['tag'][:4]] = (tmp.copy(), sl, g)
            berms[sl] = np.maximum(berms[sl], tmp[sl] * gain)
    # v19d (capture en jeu : « regarde, il y a encore le trait gradient ») : (1) les croissants JGSX gardent un fond de 0,02 - 0,1 ft
    # coupé net -> petites marches droites au bout des virages : le bas des berms est fondu à zéro ; (2) pieds des bosses arrondis
    # comme la version USLAND (SOFT_FEET) : plus de pli au pied de chaque bosse
    from scipy.ndimage import gaussian_filter
    if any(g['tag'].startswith('T_L5b') for g in path.segs) and not LP.ROUND_L5:    # v30 : demi-tour rond et régulier, plus de bosse dans le virage ; v28f : plus de T_L5b (traversée B) -> pas de bosses d'après l'arrivée v22d
        post_finish(jumps, path)                              # v22d : bosses + plateau du virage après l'arrivée
    # v20b (« il y a toujours une petite berme au pied du virage, dans tous les virages ») : le fondu v19d (seuil 0,12 - 0,62 ft) cassait
    # le pied de chaque berm (pente 0 -> 17° en 2 ft = un pli). Fondu doux à la place : h - 0,15 tanh(h / 0,15) (pente continue, le fond
    # de 0,02 - 0,1 ft tombe sous 0,013 ft, le berm ne baisse que de 0,15 ft)
    berms[:] = berms - 0.15 * np.tanh(berms / 0.15)
    fill_berm_dips(berms, path)
    sf = LP.SOFT_FEET
    # v25d (« de la terre avec des pics en bas de la bâche ; la terre monte sur la bâche ») : l'adoucissement des pieds étalait la falaise
    # coupée vers l'extérieur, à travers le panneau ; les 2 sauts à panneaux sont adoucis à part, PUIS coupés, puis fusionnés
    for tmp_, g_, kind_ in SPECIAL_:
        t_ = np.clip(tmp_ / sf['h'], 0, 1); w_ = t_ * t_ * (3 - 2 * t_)
        tmp_[:] = tmp_ * w_ + gaussian_filter(tmp_, sf['sigma'] / S) * (1 - w_)
        board_cut_layer(tmp_, g_, kind_)
        if kind_ == 'amv' and 'venum' in LP.BOARD_POLY:      # v39b : appel du freestyle (même couche que la butte AMV) coupé au plan des triangles Venum
            board_cut_layer(tmp_, g_, 'venum')
    for A_ in (jumps, whoops):                                # (pas les berms : leur pied s'étalait sous les grilles)
        t_ = np.clip(A_ / sf['h'], 0, 1); w_ = t_ * t_ * (3 - 2 * t_)
        A_[:] = A_ * w_ + gaussian_filter(A_, sf['sigma'] / S) * (1 - w_)
    for tmp_, g_, kind_ in SPECIAL_:
        np.maximum(jumps, tmp_, out=jumps)
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
SABLE_GRIS_BAZO = (174, 161, 137)   # Bazo v29 : tuile sable beige-gris comme le grain (v28 : (206, 172, 96))
HOLESHOT_HP = 10.9                 # v25d : pancarte moins haute (5 -> 3,6 ft), bas remonté, haut inchangé (14,5 ft)
HOLESHOT_BH = 3.6
HOLESHOT_V = 22.0                  # v25d (« rapproche-le légèrement de la piste ») : poteau à 22 ft de l'axe (origine sur le plat)
HOLESHOT_HP_V25C = 9.5                  # v25c : bas de la bannière du portique (était 13 ft, « trop haut »)


def sand_texture(path, base=(214, 182, 128)):
    """v23f : sable beige clair (au-dessus de la terre orange-marron TERRE_RGB), grain fin + petites ondulations ; 512 x 512, raccordable."""
    from scipy.ndimage import gaussian_filter
    rng = np.random.default_rng(23); n1 = gaussian_filter(rng.normal(0, 1, (512, 512)), 1.0, mode='wrap'); n2 = gaussian_filter(rng.normal(0, 1, (512, 512)), 12, mode='wrap')
    a = np.asarray(base, float)[None, None, :] * (1 + 0.05 * (n1 / n1.std())[..., None] + 0.04 * (n2 / n2.std())[..., None])
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(path)
RF_SAND_DECALS = False
RAMP_MI_K = 1.2                    # v38d : R2 un peu plus haute
RAMP_TALL_K = 1.4                  # v38c : rampe R1 x1,4 en hauteur
RAMP_MAT_L = (25.0, 25.0, 88.0)    # v38c : longueur des grilles au sol derrière R1, R2, R3 (lues sur les captures)
PUBLIC_RANG_Y, PUBLIC_X = 9.6, 500.0   # v38c : 2e rang de la tribune Sud, à hauteur des whoops
CLASSEMENT_DIRECT = True           # v39 (Ryan : « la télé, on voit rien ; même DA que la retransmission de Paris, en direct ») : refait comme la tour ZION 2025 (tableau_direct.py) ; v38c : False (la v37 s'affichait mal en jeu)
RF_BORDER = True                   # v38c : bordure RF (terre, planches, béton) côté stade
BORDER_A1 = True                   # v39 (Ryan : « comme A1, un peu de travers, même dégradé ») : bordure d'A1 telle quelle (deco_v28.border_a1) ; False = border_v2 (v38e)
SABLE_RF = True     # v36p : tuile sable à la texture de la terre (ZION) + bouts du sable en dégradé de décals (RF Anaheim 1)


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
    # v25c (« t'as juste mis la couleur, pas de texture sable ») : la vraie texture sable de ZION (ztile/sand.ppm, faite pour cet éclairage)
    zb = [re.sub(r"texture @\S+/sx1sand/tiles/sand\.ppm", "texture @%s/ztile/sand.ppm" % FOLDER, b) for b in zb]
    # v36p (« l'entrée du sable est super bizarre, ça change de couleur net ; regarde comment c'est fait sur ZION et RF ») : sur ZION toutes
    # les tuiles (sable compris) ont la même texture ; la couleur du sable ne vient que des décals -> plus de bord de tuile visible
    if SABLE_RF:
        zb = [re.sub(r"texture @\S+/ztile/sand\.ppm", "texture @%s/ztile/2.png" % FOLDER, b) for b in zb]
    # v21d (« le sol derrière le terrain, là où il y a les camions, de la tribune à l'autre côté : des dalles noires un peu de plastique,
    # noir gris ») : une tuile de plus, « Paddock » (index PADDOCK_TILE), réglages de la tuile Road, texture dalles_noires.png
    road = next(b for b in pick if re.search(r"name Road", b))
    pad = re.sub(r"name Road", "name Paddock", road); pad = re.sub(r"texture @\S+", "texture @%s/ztile/dalles_noires.png" % FOLDER, pad, count=1)
    # v29c (« mets la texture et les couleurs de St-Thib ») : tuiles de terre (texture ztile/2.png) = terre de Saint-Thibéry : projections
    # (roost) et traces de pneus (treadmark) de son bloc Main (fichiers SX1, déjà copiés dans sx1sand/) ; texture : voir plus bas
    stt_ = open(os.path.join(BP.ROOT, "tracks", "USLAND2026SaintThiberybyBazo", "tileinfo")).read().split("addtile")
    stt_ = next(b for b in stt_ if re.search(r"name Main\s*$", b, re.M))
    stt_fx = [l.replace("@USLAND2026SaintThiberybyBazo/ext/USLAND2026SX1/", "@%s/sx1sand/" % FOLDER) for l in stt_.splitlines() if l.startswith(("roost", "treadmark"))]
    def _stt(b):
        if "ztile/2.png" not in b:
            return b
        ls_ = [l for l in b.splitlines() if not l.startswith(("roost", "treadmark"))]
        k_ = next(i for i, l in enumerate(ls_) if l.startswith("texture")) + 1
        return chr(10).join(ls_[:k_] + stt_fx + ls_[k_:]) + (chr(10) if b.endswith(chr(10)) else "")
    if STT_TERRE:
        zb = [_stt(b) for b in zb]
    assert len(zb) + len(pick) == PADDOCK_TILE
    # v38e (« après les planches c'est du béton, couleur béton comme la couleur de mon trait ») : tuile « Beton » (index PADDOCK_TILE + 1),
    # réglages de Road, texture béton de SX1 assombrie (moyenne BETON_GRIS : rend ~ le gris du trait, ~ 90 en jeu) ; posée par border_v2
    bet = re.sub(r"name Road", "name Beton", road); bet = re.sub(r"texture @\S+", "texture @%s/ztile/beton.png" % FOLDER, bet, count=1)
    open(os.path.join(OUT, "tileinfo"), "w", newline=chr(10)).write("addtile".join(zb + pick + [pad, bet]) + "addtile" + chr(10))
    shutil.copytree(os.path.join(ZD, "tile"), os.path.join(OUT, "ztile"), dirs_exist_ok=True)
    c_ = np.asarray(Image.open(os.path.join(BP.ROOT, "tracks", "USLAND2026SX1", "tiles", "concrete.ppm")).convert("RGB"), float)
    Image.fromarray(np.clip(c_ * (BETON_GRIS / c_.reshape(-1, 3).mean(0)), 0, 255).astype(np.uint8)).save(os.path.join(OUT, "ztile", "beton.png"))
    # v19d (« essaie de faire la terre un peu plus orange marron ») : la tuile de terre ZION (couleur unie 158 136 85) -> TERRE_RGB
    # v29b : texture de terre de Saint-Georges (tiles/dirt_light.ppm) remise à la couleur de Paris (TERRE_RGB), même taille que la tuile ZION
    t2 = os.path.join(OUT, "ztile", "2.png"); sg_ = np.asarray(Image.open(os.path.join(BP.ROOT, "tracks", "USLAND2026SaintGeorgesbyBazo", "tiles", "dirt_light.ppm")).convert("RGB"), float)
    sg_ = np.clip(sg_ * (np.array(TERRE_RGB, float) / sg_.reshape(-1, 3).mean(0)), 0, 255).astype(np.uint8)
    Image.fromarray(sg_).resize(Image.open(t2).size, Image.LANCZOS).save(t2)
    if STT_TERRE:   # v29c : texture de terre de Saint-Thibéry telle quelle (SX1 tiles/dirt.ppm, 130 100 60), pas recolorée
        Image.open(os.path.join(BP.ROOT, "tracks", "USLAND2026SX1", "tiles", "dirt.ppm")).convert("RGB").resize(Image.open(t2).size, Image.LANCZOS).save(t2)
    shutil.copy(os.path.join(BP.ROOT, "tracks", "USLAND2026SX1", "tiles", "sand.ppm"), os.path.join(OUT, "ztile", "sand_usland.ppm"))
    # Bazo v28-v29 (« la couleur du sable » puis « t'as mis du jaune en dessous qui dépasse, enlève le jaune, laisse la texture sable ») :
    # tuile sable ZION ramenée au beige-gris du grain (décals SX1)
    jaunir(os.path.join(OUT, "ztile", "sand.ppm"), SABLE_GRIS_BAZO)
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
BETON_GRIS = np.array([104.0, 103.0, 100.0])     # v38e : couleur moyenne de la texture de la tuile Beton (béton gris moyen)
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
    if os.path.isdir(RFT):                                               # v26 : sans rf_ext (autre PC), les fichiers déjà dans la piste restent
        for f_ in ("sand2.png", "sand2_tnorm.png", "sand3.png"):
            shutil.copy(os.path.join(RFT, f_), os.path.join(sd_, f_))
        for f_ in ("sand2.png", "sand3.png"):                            # v22c (« fais le sable jaune »)
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
    # v25d (« le sable : toujours pas de texture ; va revoir les pistes USLAND avec du sable ») : sur SX1 / SX3, le grain du sable vient des
    # décals decal/sand.png (+ sand_tnorm.png, relief) de 26 ft posés tous les ~4,5 ft avec une rotation au hasard (1141 sur SX1), pas de la
    # tuile ; mêmes fichiers, même taille, même pas, sur toute la partie sable
    sdd = os.path.join(OUT, "sx1sand", "decal"); os.makedirs(sdd, exist_ok=True)
    for f_ in ("sand.png", "sand_tnorm.png"):
        shutil.copy(os.path.join(BP.ROOT, "tracks", "USLAND2026SX1", "decal", f_), os.path.join(sdd, f_))
    # v29 : grain du sable remis tel quel (SX1) ; v28 : teinté (234, 214, 166)
    ns_ = 0
    # v25e (« pas déborder, coupé droit ») : décals de 10 ft (le sable s'arrête net au bord) dont le centre reste à 5 ft du bord
    XX_, ZZ_ = np.meshgrid(np.arange(sx0, sx1, 3.0), np.arange(sz0, sz1, 3.0)); XX_ = XX_ + rng.uniform(-0.8, 0.8, XX_.shape); ZZ_ = ZZ_ + rng.uniform(-0.8, 0.8, ZZ_.shape)
    # v35 (« pas que ça change de couleur aussi vite : dégradé ») : aux 2 bouts, sur BP.SAND_GRAD ft (comme les tuiles), décals de plus en plus
    # rares et plus petits (5 ft) ; au plein, comme avant (10 ft, centre à 5 ft du bord)
    gS_ = lambda X_, Z_, i_: BP.sand_weight(path, X_, Z_, inset=i_, fade_s=BP.SAND_GRAD, inset_s=-BP.SAND_GRAD / 2)[0]
    XE_, ZE_ = np.meshgrid(np.arange(sx0, sx1, 2.0), np.arange(sz0, sz1, 2.0)); XE_ = XE_ + rng.uniform(-0.5, 0.5, XE_.shape); ZE_ = ZE_ + rng.uniform(-0.5, 0.5, ZE_.shape)
    if SABLE_RF:
        # v36p (« reprends la couleur, les textures de sable de RF, là c'est tout vide ») : le sable de RF (Anaheim 1, pack sx2026) :
        # tuile = couleur unie, tout le sable vient de 3 décals (copiées dans commun/assets/textures/rf_sable -> rfsand/) :
        #  - sand2.png (+ relief sand2_tnorm) : disques de sable de 18 ft à bord fondu, serrés sur toute la partie sable (RF : 1 / 23 ft²) ;
        #  - sand.png : grandes traces de 40 ft (alpha 0,5) en 3 rangs dans le sens de la piste, tous les ~23 ft (RF : 18) ;
        #  - sand3.png : voiles très légers (alpha <= 22) entassés aux 2 bouts (RF : ~140 par bout), qui débordent sur la terre.
        # u = distance au bout (ft, > 0 dans le sable) ; les tuiles ne sont plus mélangées aux bouts (BP.SAND_GRAD = 0, bord sous les décals)
        rfd_ = os.path.join(OUT, "rfsand"); os.makedirs(rfd_, exist_ok=True)
        for f_ in ("sand.png", "sand2.png", "sand2_tnorm.png", "sand3.png"):
            shutil.copy(os.path.join(BP.ROOT, "commun", "assets", "textures", "rf_sable", f_), os.path.join(rfd_, f_))
        s0_, s1_ = BP.sand_range(path); ssf_ = lambda t: (lambda t_: t_ * t_ * (3 - 2 * t_))(np.clip(t, 0, 1))
        smq_ = path.samples(1.0); kq_ = (smq_['s'] > s0_ - 30) & (smq_['s'] < s1_ + 30)
        PQ_, TQ_ = np.c_[smq_['x'][kq_], smq_['z'][kq_]], np.array(smq_['th'])[kq_]; tq_ = _KD(PQ_)
        ang_ = lambda x_, z_: -(TQ_[tq_.query([x_, z_])[1]] + np.pi / 2)          # RF : 0 quand la piste va selon z
        def uS_(X_, Z_, i_):
            w_, s_ = BP.sand_weight(path, X_, Z_, inset=i_, inset_s=-60.0, fade_s=1.0)
            return w_ > 0.5, np.minimum(s_ - s0_, s1_ - s_)
        dec_ = lambda x_, z_, a_, sz_, f_: ov.append("[%.6f %.6f] %.6f %.6f 1.000000 @%s/rfsand/%s" % (x_, z_, a_, sz_, FOLDER, f_))
        nv_ = 0
        # 1) disques sand2 : grille de 4,8 ft, centre à 6,5 ft du bord
        XD_, ZD_ = np.meshgrid(np.arange(sx0, sx1, 4.8), np.arange(sz0, sz1, 4.8)); XD_ = XD_ + rng.uniform(-1.2, 1.2, XD_.shape); ZD_ = ZD_ + rng.uniform(-1.2, 1.2, ZD_.shape)
        in_, u_ = uS_(XD_, ZD_, 6.5); pk_ = in_ & (rng.random(u_.shape) < ssf_((u_ + 2.0) / 8.0))
        for x_, z_ in zip(XD_[pk_], ZD_[pk_]):
            dec_(x_, z_, rng.uniform(-np.pi, np.pi), 18.0, "sand2.png"); ns_ += 1
        # bords coupés droit : 2 rangs de disques de 9 ft tous les 1,5 ft le long de la piste, centres à 2,7 et 5 ft du bord
        for sv_ in np.arange(s0_ - 2.0, s1_ + 2.0, 1.5):
            k_ = int(np.argmin(np.abs(smq_['s'][kq_] - sv_))); x_, z_ = PQ_[k_]; th_ = TQ_[k_]; u_ = min(sv_ - s0_, s1_ - sv_)
            for v_ in (LP.SAND_HW - 2.7, LP.SAND_HW - 5.0, -(LP.SAND_HW - 2.7), -(LP.SAND_HW - 5.0)):
                if rng.random() < ssf_((u_ + 2.0) / 8.0):
                    dec_(x_ - np.sin(th_) * v_, z_ + np.cos(th_) * v_, rng.uniform(-np.pi, np.pi), 9.0, "sand2.png"); ns_ += 1
        # 2) traces sand.png : 3 rangs (-9, 0, +9 ft) tous les 23 ft, de u = 12 jusqu'à l'autre bout
        for sv_ in np.arange(s0_ + 12.0, s1_ - 11.0, 23.0):
            k_ = int(np.argmin(np.abs(smq_['s'][kq_] - sv_))); x_, z_ = PQ_[k_]; th_ = TQ_[k_]
            for v_ in (-9.0, 0.0, 9.0):
                # v38c (« le virage après la bosse de freestyle : toujours des stries, remets la texture de base ; ça fait 2 fois ») : ces traces
                # de 40 ft à |v| 9 débordaient de 20 ft hors du sable, sur l'appui de T_D collé au couloir LR -> taille bornée au sable
                sz_ = min(40.0, 2.0 * (LP.SAND_HW - abs(v_) - 1.0))
                dec_(x_ - np.sin(th_) * v_, z_ + np.cos(th_) * v_, -(th_ + np.pi / 2), sz_, "sand.png"); ns_ += 1
        # 3) voiles sand3 aux 2 bouts : 140 par bout, centres de u = -10 à +8 (plus serrés vers le bout), dans le sens de la piste
        for sb_, sg_ in ((s0_, 1.0), (s1_, -1.0)):
            for _ in range(140):
                u_ = rng.triangular(-10.0, 0.0, 8.0); k_ = int(np.argmin(np.abs(smq_['s'][kq_] - (sb_ + sg_ * u_)))); x_, z_ = PQ_[k_]; th_ = TQ_[k_]
                v_ = rng.uniform(-(LP.SAND_HW - 8.0), LP.SAND_HW - 8.0)
                dec_(x_ - np.sin(th_) * v_, z_ + np.cos(th_) * v_, -(th_ + np.pi / 2) + rng.normal(0, 0.15), 18.0, "sand3.png"); nv_ += 1
        BP.REPORT['decals_sable'] = ns_; BP.REPORT['decals_sable_voiles'] = nv_
    else:
        wS_ = gS_(XX_, ZZ_, 5.0); pk_ = rng.random(wS_.shape) < wS_ * wS_ * (3 - 2 * wS_)
        for x_, z_, w_ in zip(XX_[pk_], ZZ_[pk_], wS_[pk_]):
            ov.append("[%.6f %.6f] %.6f %.6f 1.000000 @%s/sx1sand/decal/sand.png" % (x_, z_, rng.uniform(-np.pi, np.pi), 10.0 if w_ > 0.97 else 5.0, FOLDER)); ns_ += 1
        # Bazo v28 (« la texture va pas vraiment sur les bords ») : une rangée de décals de 5 ft au bord (centre à 2,5 - 4,5 ft du bord)
        wE_ = gS_(XE_, ZE_, 2.5); wI_ = gS_(XE_, ZE_, 4.5); pk_ = (rng.random(wE_.shape) < wE_ * wE_ * (3 - 2 * wE_)) & (wI_ < 0.5)
        for x_, z_ in zip(XE_[pk_], ZE_[pk_]):
            ov.append("[%.6f %.6f] %.6f 5.000000 1.000000 @%s/sx1sand/decal/sand.png" % (x_, z_, rng.uniform(-np.pi, np.pi), FOLDER)); ns_ += 1
        BP.REPORT['decals_sable'] = ns_
    if RF_BORDER:   # v38c : planches + béton de RF entre la piste et le stade (mêmes distances, même dégradé), sous les autres décals
        import deco_v28 as D28b
        rbd_ = os.path.join(OUT, "rfborder"); os.makedirs(rbd_, exist_ok=True)
        # v38d : bordure refaite (border_v2) : béton (tuile Road) en U côté tribunes, rangée régulière de planches, terre fondue régulière ;
        # les taches de terre (terre_stt) de cette zone enlevées
        # v38e : distances mesurées sur la photo (planches de 10 à 14 ft du bord du couloir), tuile Beton (gris du trait), terre du sol en
        # bande régulière ; les taches de terre (terre_stt, ~9 ft de rayon) qui toucheraient les planches enlevées
        rft_ = os.path.join(os.path.dirname(BP.ROOT), "rf_ext", "sx2026r01anaheim1", "textures")
        assert os.path.isdir(rft_), "bordure A1 : extraire refs/rf/sx2026r01anaheim1.medium.saf dans %s (commun/tools/extract_saf.py)" % os.path.dirname(rft_)
        xz_ = lambda l_: (float(l_.split()[0][1:]), float(l_.split()[1][:-1]))
        if BORDER_A1:   # v39 : la bordure de RF Anaheim 1 telle quelle (planches de travers, dégradé terre -> planches -> béton) : deco_v28.border_a1
            teinte_ = D28b.border_a1_textures(rft_, rbd_, os.path.join(OUT, "ztile", "2.png"), os.path.join(OUT, "ztile", "beton.png"))   # terre du sol (tuile 1 de tileinfo) ; v39b : tuile Beton = béton d A1
            rb_, inU_, nrb_ = D28b.border_a1(OUT, path, fl, XPAD, FOLDER, np.random.default_rng(39))
            n0_ = len(ov); ov = [l_ for l_ in ov if not ('terre_stt' in l_ and inU_(*xz_(l_)))]
            BP.REPORT['bordure_a1'] = dict(nrb_, teinte_terre=teinte_, taches_enlevees=n0_ - len(ov))
        else:
            D28b.border_textures(rft_, rbd_, os.path.join(OUT, "zdecal", "terre_stt.png"))
            rb_, inU_, nrb_ = D28b.border_v2(OUT, path, fl, XPAD, FOLDER)
            n0_ = len(ov); ov = [l_ for l_ in ov if not ('terre_stt' in l_ and inU_(*xz_(l_)))]
            BP.REPORT['bordure_v2'] = dict(terre=nrb_[0], planches=nrb_[1], cases_beton=nrb_[2], cases_beton_hors_sol=nrb_[3], taches_enlevees=n0_ - len(ov))
        ov = rb_ + ov
    open(os.path.join(OUT, "decals"), "w", newline=chr(10)).write(chr(10).join(ov + dl) + chr(10))
    # v19 (« le saut d'arrivée, il va pas ; il faut faire les câbles comme sur mon track, avec le finish ») : plus d'arche ZION, le panneau
    # FINISH suspendu (élingues jusqu'au toit) de la version USLAND reste
    # v19 (« enlève ma grille pourrie avec la poutre, elle n'existe pas ; garde nos grilles ») : plus de grilles de Saint-Georges
    # (start_grids, 88 ft avec la poutre) ; « des cordes qui descendent du plafond au-dessus du start, fond noir, START en blanc, comme le
    # finish, à peu près à la même hauteur » : panneau START (hab_objets.finish, mot START) 12 ft devant les grilles, face aux pilotes
    import hab_objets as HO
    assert not BP.REPORT.get('long_tuff_apres_depart'), "nofrills.js référence des rangs de statues"
    sd = os.path.join(OUT, "statue", "paris"); G0 = np.array(st['gate']); h0 = np.radians(st['heading']); f0 = np.array([np.cos(h0), np.sin(h0)])
    q = G0 + f0 * START_ADV; rf_ = roof_ft(*q)   # v38d (« le bandeau START pile au-dessus de la ligne de départ, au-dessus des grilles, pas avancé ») : 12 -> 0 ft
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
    jm, png, png_v = GM.make_pair(sd); tg = os.path.join(OUT, "timing_gates"); t_ = open(tg).read()
    t_ = t_.replace("statue/paris/start_gate_frame.jm", "statue/paris/" + jm).replace("statue/paris/start_gate_frame.png", "statue/paris/" + png)
    # v38 (« alterne une grille sur 2 : logo Venum en blanc, logo Monster ») : une grille sur deux en Venum
    Lg_ = t_.split(chr(10)); k_ = 0
    for i_, l_ in enumerate(Lg_):
        if "statue/paris/" + png in l_:
            if k_ % 2 == 1:
                Lg_[i_] = l_.replace("statue/paris/" + png, "statue/paris/" + png_v)
            k_ += 1
    t_ = chr(10).join(Lg_)
    open(tg, "w", newline=chr(10)).write(t_)
    BP.REPORT['zion_v19'] = dict(paddock=[round(v) for v in (x0, x1, z0, z1)], dalles_tuiles=int(inn.sum()), x_paddock=round(XPAD, 1), overlay=len(ov), decals_gardes=len(dl),
                                 start=(round(q[0], 1), round(q[1], 1), round(rf_, 1)), toit_finish=round(rfin, 1), grilles=t_.count(jm))


START_Y = 15.0
START_ADV = 0.0
BALE_V, BALE_STEP, BALE_GAP = 15.5, 9.6, 25.0
BALE_STEP2, BALE_SLIDE, ARCH_XC = 2 * 9.6, 4.0, 18.0   # v23 : pieds au bord de la piste (était 26)
BP.BOARD_CUT = False               # v24b : flancs coupés derrière les panneaux ; v25c : coupe faite sur la couche du saut seul (board_cut_layer)
BP.EXTRA_H = [lambda H_, p_: smooth_junctions(H_, p_), lambda H_, p_: smooth_zones(H_, p_), lambda H_, p_: crease_smooth(H_, p_), lambda H_, p_: mats_clear(H_, p_), lambda H_, p_: pads(H_, p_)]   # v25e : socles des poteaux et de la cabane ; v25d (« les virages, une catastrophe : des gros monticules de terre partout ; repars sur les virages de base ») : plus de wall_fill
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
                        mp_ = LP.BOARD_POLY['milwaukee']   # v25d (« un trait noir en plus » : 2 ballots l'un dans l'autre) : pas sur le dessus du Milwaukee
                        skip_ = skip_ or (g['tag'].startswith('LR') and abs(uu[k_] - (mp_[1][0] + mp_[2][0]) / 2) < 5.0)
                        # v28 (« celle de l'intérieur, tu l'enlèves ; t'en mets 2 là ») : plus la dernière à droite de L2 (intérieur du virage Honda)
                        skip_ = skip_ or (g['tag'].startswith('L2') and side_ > 0 and uu[k_] > g['L'] - 25.0)
                        if g['tag'].startswith('LR') and LP.CAMEL_U - 3.0 < uu[k_] < LP.CAMEL_U + 14.0:   # v29 (« coincée dans l'appel du Milwaukee, recule-la »)
                            k_ = int(np.argmin(np.abs(uu - (LP.CAMEL_U - 5.0))))
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
    if any(g['tag'].startswith('T_L5b') for g in BP.PATH.segs):   # v28f : boudin anti-coupe seulement avec l'ancien après-arrivée
        ga_ = next(g for g in BP.PATH.segs if g['tag'].startswith('T_L5a')); gb_ = next(g for g in BP.PATH.segs if g['tag'].startswith('T_L5b'))
        for f_ in ("boudin_logo3.jm", "boudin_logo3.shp"):
            shutil.copy(os.path.join(BP.ROOT, "commun/assets", "props", f_), os.path.join(sd, f_))
        bk_ = np.asarray(Image.open(os.path.join(BP.ROOT, "commun/assets", "props", "boudin_fly3.png")).convert('RGB')).copy(); hb_ = int(bk_.shape[0] * 0.915)
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
    for x_, z_, mid, key_ in pylon_spots(BP.PATH):                                     # v25e : sur leur socle de terre (pads)
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
        # v28 (« les bottes AMV sur le dessus, il en faut pas ; que dans la descente du saut, 2 de chaque côté sur le bord, parallèles ») :
        # dans la descente, au ras du panneau (|v| = BOARD_VB - 2,5 ft), le jeu les penche comme la pente
        for f_ in (0.28, 0.58):
            u_ = ut1 + f_ * (ue - ut1)
            for side_ in (-1, 1):
                p_ = np.array([g3['x0'] + u_ * c, g3['z0'] + u_ * s2]) + nrm * side_ * (LP.BOARD_VB['amv'] - 2.5); lines.append(line(p_[0], p_[1], yaw, *fa))
    # v23c : bâches drapées sur les flancs : saut Milwaukee (LR) et réception du freestyle (plaque AMV)
    gR = next(g for g in BP.PATH.segs if g['kind'] == 'S' and g['tag'].startswith('LR'))
    for side_, nm_ in ((-1, 'bache_milwaukee_g'), (1, 'bache_milwaukee_d')):
        # v23d : panneau « carton » (objet) au lieu de la bâche drapée
        O_, jm_, png_, shp_ = D22.board_v25b(sd, nm_.replace('bache', 'panneau'), Hf, gR, side_, 'milwaukee')   # v24 : forme dessinée par l'utilisateur
        lines.append(line(O_[0], O_[1], 0.0, jm_, png_, shp_))
    for prof, u0, name in g3['sections']:
        if name == LP.L3_SEC:
            it = [i for i in combos[name]['items'] if 'butte' in i[0]][0]
            for side_, nm_ in ((-1, 'bache_amv_g'), (1, 'bache_amv_d')):
                O_, jm_, png_, shp_ = D22.board_v25b(sd, nm_.replace('bache', 'panneau'), Hf, g3, side_, 'amv')   # v24 : forme dessinée par l'utilisateur
                lines.append(line(O_[0], O_[1], 0.0, jm_, png_, shp_))
            if 'venum' in LP.BOARD_POLY:                        # v39b : triangles noirs Venum de chaque côté de l'appel du freestyle
                for side_, nm_ in ((-1, 'panneau_venum_g'), (1, 'panneau_venum_d')):
                    O_, jm_, png_, shp_ = D22.board_v25b(sd, nm_, Hf, g3, side_, 'venum')
                    lines.append(line(O_[0], O_[1], 0.0, jm_, png_, shp_))
    # v24 (« avec les 2 ballots de paille posés sur le dessus ») : 2 ballots Milwaukee au milieu du plateau du saut, un de chaque côté
    (pu0, _), (pu1, _), (pu2, _), (pu3, _) = D22.BOARD_POLY['milwaukee']; cR, sR2 = np.cos(gR['t']), np.sin(gR['t']); nR = np.array([-sR2, cR])
    fM = DV.bale_u(sd, 'milwaukee')
    for side_ in (-1, 1):
        p_ = np.array([gR['x0'] + (pu1 + pu2) / 2 * cR, gR['z0'] + (pu1 + pu2) / 2 * sR2]) + nR * side_ * BALE_V
        lines.append(line(p_[0], p_[1], float(np.arctan2(-sR2, cR)), *fM))
    # v25 : cabane noire MX Sim Racing à gauche du saut d'arrivée, signaleur (drapeau) dedans ; portique holeshot Milwaukee
    Cc, t5_, n5, ucab = cabin_spot(BP.PATH); vcab = CAB_V                              # v25e : près de l'appel, sur son socle (pads)
    fz = n5; fx = np.array([fz[1], -fz[0]])                                          # +z de la cabane = vers la piste
    wp = lambda x, y, z: (fx[0] * x + fz[0] * z, y, fx[1] * x + fz[1] * z)
    import deco_v28 as D28_
    lines.append(line(Cc[0], Cc[1], 0.0, *D28_.booth(sd, wp, Hc=CAB_HC, y0=-(CAB_PAD + 1.5)))); rep_['cabane'] = (round(ucab, 1), vcab)   # v38c : noir jusqu'au sol autour du bloc de terre   # v29 : guérite noire MX Sim (dessin)
    st_ = BP.START; G0 = np.array(st_['gate']); f0 = np.array([np.cos(np.radians(st_['heading'])), np.sin(np.radians(st_['heading']))]); r0 = np.array([-f0[1], f0[0]])
    # v25c (« pas du tout au niveau du holeshot : le placer au niveau de la 1re bosse après le saut freestyle » ; « trop haut ») : poteau à gauche
    # de L2, au niveau de la crête de sa 1re bosse, sur du sol PLAT (le jeu penche un objet posé en pente), bannière au-dessus de la piste
    g2_ = next(g for g in BP.PATH.segs if g['kind'] == 'S' and g['tag'].startswith('L2')); s2_ = g2_['sections'][0]; it2_ = combos[s2_[2]]['items'][0]
    i0h, i1h = int(it2_[1] / 0.1), int(it2_[2] / 0.1); uh = s2_[1] + it2_[1] + float(np.argmax(s2_[0][i0h:i1h])) * 0.1
    t2_ = np.array([np.cos(g2_['t']), np.sin(g2_['t'])]); n2_ = np.array([-t2_[1], t2_[0]]); B2_ = np.array([g2_['x0'], g2_['z0']]) + t2_ * uh
    flat2 = lambda P: max(float(Hf(*(P + t2_ * a_ + n2_ * b_))[0]) for a_ in (-2.5, 0, 2.5) for b_ in (-2.5, 0, 2.5)) - min(float(Hf(*(P + t2_ * a_ + n2_ * b_))[0]) for a_ in (-2.5, 0, 2.5) for b_ in (-2.5, 0, 2.5)) < 0.06
    vh = next((v for v in np.arange(19.0, 34.0, 0.5) if flat2(B2_ - n2_ * v)), 26.0); Hp = B2_ - n2_ * vh
    fzh = -t2_; fxh = n2_                                                             # z vers les pilotes, x vers la droite (au-dessus de la piste)
    dxh = vh - HOLESHOT_V                                                             # le poteau se rapproche de la piste, l'origine reste sur le plat
    wph = lambda x, y, z: (fxh[0] * (x + dxh) + fzh[0] * z, y, fxh[1] * (x + dxh) + fzh[1] * z)
    lines.append(line(Hp[0], Hp[1], 0.0, *D22.holeshot_v25(sd, wph, hp=HOLESHOT_HP, bh=HOLESHOT_BH, mir=True))); rep_['holeshot'] = (round(float(Hp[0]), 1), round(float(Hp[1]), 1), round(uh, 1), vh)
    lines.append(line(Hp[0], Hp[1], 0.0, *D22.drill_cutout_v25(sd, wph, 17.7, HOLESHOT_HP, mir=False, x_handle=17.7)))   # v25c : l'embout vers le logo, la poignée sur le bord
    # signaleurs : panneau 30 s derrière les grilles + signaleur animé (drapeau) dans la cabane ; fichiers repris de Saint-Georges
    shutil.copytree(os.path.join(BP.ROOT, "tracks", "USLAND2026SaintGeorgesbyBazo", "ext", "2024Bh1Conway", "flaggerfiles"),
                    os.path.join(OUT, "ext", "2024Bh1Conway", "flaggerfiles"), dirs_exist_ok=True)
    os.makedirs(os.path.join(OUT, "billboard"), exist_ok=True); Image.new('RGBA', (64, 64), (0, 0, 0, 0)).save(os.path.join(OUT, "billboard", "blank.png"))
    half_ = (LP.N_GATES - 1) / 2 * LP.GATE_PITCH; b1 = G0 - f0 * 25 + r0 * (half_ - 15); b2 = G0 - f0 * 25 - r0 * (half_ - 15)
    ff = "@%s/ext/2024Bh1Conway/flaggerfiles/" % FOLDER
    open(os.path.join(OUT, "flaggers"), "w", newline=chr(10)).write(chr(10).join([
        "[%.6f 0.000 %.6f]" % tuple(b1), "[%.6f 0.000 %.6f]" % tuple(b2), "8.4 1", "10", "@30sec_30.png", "@30sec_turn.seq", "@30sec_5.png",
        "@30sec_run.seq", "@%s/billboard/blank.png" % FOLDER, "", "[%.6f %.3f %.6f]" % (Cc[0], CAB_FLAG_REL, Cc[1]), "%.4f 1" % (10.5 - np.pi), ff + "defaultflag.png", ff + "halfway.png",
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
    # v38 (« un mur invisible, pas buggé, entre le petit double avant le saut freestyle et le saut freestyle, comme pour l'arrivée ») : au milieu
    # du creux entre la fin de la petite table et le pied de l'appel, de 12,5 à 35 ft (on roule dessous : rien en dessous de 11 ft)
    st3_ = next(q for q in g3['sections'] if q[2] != LP.L3_SEC); sa3_ = next(q for q in g3['sections'] if q[2] == LP.L3_SEC)
    u_fs = (st3_[1] + combos[st3_[2]]['items'][-1][2] + sa3_[1]) / 2; inv_wall('invisible_freestyle', g3, u_fs, 12.5, 35.0)
    inv_wall('invisible_milwaukee', gR, sR[1] + (itR[kM + 1][1] + itR[kM + 1][2]) / 2, 15.0, 40.0)   # v23f : plus haut (« buggés »)
    g5 = next(g for g in BP.PATH.segs if g['kind'] == 'S' and g['tag'].startswith('L5')); s5 = g5['sections'][0]; it5 = combos[s5[2]]['items']
    inv_wall('invisible_arrivee', g5, s5[1] + (it5[1][2] + it5[2][1]) / 2, 13.0, 30.0)   # v23f : « le plus haut pour le saut d'arrivée encore »
    late_ = deco_v28(OUT, FOLDER, combos, Hf, lines, line, sd, DV, rep_, g3, gR)
    # v28 : les boudins « tardifs » EN TÊTE de statues et de la variante de nuit (même rang dans les 2 fichiers pour nofrills.js)
    ls_ = set(late_); rest_ = [l_ for l_ in lines if l_ not in ls_]
    for f in ["statues"] + ["variants/" + v for v in os.listdir(os.path.join(OUT, "variants")) if v.startswith("statues")]:
        p = os.path.join(OUT, f); s0 = open(p).read().rstrip(chr(10)) + chr(10)
        open(p, "w", newline=chr(10)).write(chr(10).join(late_) + chr(10) + s0 + chr(10).join(rest_) + chr(10))
    import deco_v28 as D28
    rep_['boudins_20s'] = D28.write_late(OUT, late_, getattr(D28, 'MOVES', None))   # v28 : nofrills.js (rangs définitifs des statues) ; v39 : + ligne Minerva déplacée
    BP.REPORT['deco_v21'] = rep_


# v36c (« fais des traits droits, pas comme sur mon dessin ; en bleu enlève les 2 boudins et la fin du nouveau ; tout doit être droit ») :
# chaque ligne = un seul segment droit ; plus les 2 lignes Automoto du départ vers T_D ; ligne « île » coupée avant sa partie verticale
# v36d (« mets le droit sur la ligne des 600 ; l'autre comme sur mon dessin : pas tout droit, ça tourne légèrement tout le long, et à la
# fin un petit peu plus ») : bord sud droit à z = 600 ; bord nord = trait bleu lissé (cubique), fin arrêtée à 16,4 ft de l'axe de la piste
V36_LIGNES = dict(A=[(646.0, 518.7), (633.0, 519.4), (620.0, 520.2), (607.0, 521.1), (594.0, 522.0), (581.0, 523.1), (568.0, 524.2), (555.0, 525.4), (542.0, 526.8), (529.0, 528.2), (516.0, 529.7), (503.0, 531.3), (490.0, 532.9), (477.0, 534.7), (464.0, 536.6), (451.0, 538.5), (438.0, 540.5), (425.0, 542.7), (412.5, 544.8)],
                  B=[(606, 600.0), (396, 600.0)],
                  ile=[(378.9, 588.5), (340.7, 613.1)])   # v36m : début coupé au trait rouge (était (392, 580)) ; v36o (« coupe ça encore ») : les 2 bouts coupés aux traits
# v36m (traits rouges sur la vue v36j : « sur la ligne 600 enlève la 1re partie, coupe entre les 2 traits, coupe la fin ») : boudins du
# bord sud enlevés dans ces plages de x (les autres gardent leur place et leur sponsor)
# v39 (review v38e, capture du départ : « depuis la dernière grille extérieure, les boudins sont en plein milieu ; décale-les vers la droite,
# l'angle de la courbe plus gros, vers mon trait rouge ») : ligne A (MX Sim / Honda / Yamaha) : début 10 ft plus au nord (hors de la
# trajectoire de la grille extérieure, z 513,6), parallèle jusqu'à x ~595 puis rejoint la ligne d'origine vers x 566 (début de la partie Honda)
A_SHIFT_V39 = (10.0, 595.0, 566.0)
_sA = lambda t: (lambda t_: t_ * t_ * (3 - 2 * t_))(min(1.0, max(0.0, t)))
V36_LIGNES['A'] = [(x_, z_ - A_SHIFT_V39[0] * _sA((x_ - A_SHIFT_V39[2]) / (A_SHIFT_V39[1] - A_SHIFT_V39[2]))) for x_, z_ in V36_LIGNES['A']]
# v39 Ryan (capture du départ : « garde le même début, mais que ce soit droit, pas un zigzag : tu prends le premier point et le dernier,
# une ligne droite ») : ligne A = un seul segment, du 1er point (décalé de 10 ft par Bazo) au dernier
V36_LIGNES['A'] = [V36_LIGNES['A'][0], V36_LIGNES['A'][-1]]
# v39 Ryan (vue de dessus annotée : la ligne Minerva entourée « le départ, il doit être comme ça ; dès que le départ est fini, au bout de
# 20 s, tu la mets comme mon autre trait, pour le reste de la manche ; mon trait est nul, prends le premier et le dernier point, en ligne
# droite ») : la ligne Minerva est là dès le départ (plus tardive), puis nofrills.js la déplace à 20 s sur ce segment (boudins en trop
# enterrés) ; logos vers le couloir de LD
ILE_APRES = [(435.5, 600.0), (408.0, 582.0)]
V36_B_COUPES = [(576.0, 607.0), (483.0, 506.0), (395.0, 440.0)]
V36_SANS_AUTOMOTO = True
# v36e (photo du vrai Paris avec 11 points bleus = tuff blocks et 1 point argile = gros poteau gonflable, dans le virage en U après
# l'arrivée ; zone entourée sur la vue de dessus ; « il tourne à gauche puis à droite, c'est tout le long à droite ») : bord nord =
# parabole sans point d'inflexion (pente 0,05 au début, 0,17 à la fin) ; dans la zone : les tuff blocks Minerva de L5 et de T_L5b, le
# boudin noir anti-coupe et le poteau de virage rouge enlevés, à la place exactement 11 tuff blocks et le poteau gonflable, rôle par rôle
# (photo : caméra au bout ouest, L5 à gauche, LD à droite) : 4 le long de l'extérieur de L5 avant le mur, 3 le long de l'intérieur de
# L5, 3 à la pointe intérieure du U autour du poteau, 1 à la sortie après le bout du mur
V36_ZONE = [(502, 470), (475, 452), (405, 450), (350, 462), (330, 500), (335, 545), (360, 573), (385, 572), (410, 555), (435, 540), (475, 530), (500, 515)]
# v36j (« coupe 5 ft ; ajuste pour avoir seulement 4 tuff blocks du haut de la bosse jusqu'au virage, jusqu'au poteau bleu ») : tout ce qui
# est lié au virage en U avance de 5 ft (x + 5) ; L5 : 4 tuff blocks de chaque côté entre la crête du triple (x 446,9) et le poteau bleu
V36_TUFF = [(446.0, 471.3), (427.0, 471.3), (408.0, 471.3), (390.0, 471.3),          # extérieur de L5 : 4
            (446.0, 502.3), (427.4, 502.3), (408.8, 502.3), (390.3, 504.4),          # intérieur de L5 : 4 jusqu'au poteau (le dernier = point jaune + 5)
            (382.7, 508.6), (350.6, 512.4),                                          # points jaunes de l'entrée de T_L5a (+ 5)
            (400.0, 577.5)]                                                          # sortie, après le bout du mur (+ 5)
# v36p (vue de dessus : « tous les points blancs enlève les tuff blocks et les clays faut en mettre ») : 7 tuff blocks enlevés (le plus
# proche de chaque point blanc, à moins de 6 ft) et 5 posés aux points couleur argile (4 autour du poteau bleu au bout de la ligne 600,
# 1 à l'entrée du virage du bas à gauche)
V36_TUFF += [(591.1, 601.1), (601.8, 602.1), (611.4, 608.1), (611.5, 616.2), (668.1, 720.7)]
V36_TUFF_OTER = [(661.3, 460.9), (663.4, 470.9), (685.8, 688.8), (679.9, 727.6), (681.9, 738.5), (678.0, 775.3), (688.8, 777.3)]
V36_L5_X = (387.3, 449.0)                                                            # rangées de L5 vidées entre ces x avant de poser les 4 + 4
V36_POTEAU = (385.4, 504.9)
# v38 (review en jeu de la v36p par l'utilisateur, captures annotées : croix / rond = enlever, rectangle rouge = poser)
_ILE = np.array(V36_LIGNES['ile'], float); _dI = (_ILE[1] - _ILE[0]) / np.hypot(*(_ILE[1] - _ILE[0]))
_ILE = np.array([_ILE[0] - _dI * 12.0, _ILE[1] + _dI * 6.0])   # « rajoute 1 vers le virage (bout sud-ouest) et 2 vers la ligne droite (bout nord-est) » : 8 -> 11
_cI = _ILE.mean(0); _a = np.radians(8.0); _R = np.array([[np.cos(_a), -np.sin(_a)], [np.sin(_a), np.cos(_a)]])
V38_ILE = [tuple(_cI + _R @ (q - _cI)) for q in _ILE]          # « légèrement plus de travers, pas abusé » : +8°
V36_TUFF = [q for q in V36_TUFF if q not in [(591.1, 601.1), (601.8, 602.1), (611.4, 608.1), (611.5, 616.2)]]   # remplacés par la courbe de T_Bb
V38_TUFF_KEY = {(668.1, 720.7): 'honda'}                       # « celle-là c'est une Minerva, ça doit être une Honda »
# courbe de tuff blocks autour du poteau de T_Bb (« pas un carré, un truc rond », traits noirs) : points lus sur la capture
V38_COURBE_TBB = [(613.1, 629.0), (615.2, 622.5), (613.5, 615.7), (611.4, 611.0), (609.1, 607.0), (604.3, 604.3), (597.6, 605.6),
                  (592.2, 606.3), (581.4, 607.6), (576.0, 609.0)]
# v38c (vue de dessus : « supprime ceux à trait marron ; les rectangles noirs, 3 et 3, exactement au même angle, pile poil ») : les 6
# tuff blocks du virage MX Sim, centres et sens lus sur la capture (calée sur le poteau et les tuff blocks en place)
# v38e (review v38d : « pile poil comme les rectangles noirs, dans l'alignement du boudin d'avant ; ceux au trait marron supprimés ; des
# MX Sim, pas des Minerva ») : capture calée sur les 6 tuff blocks Minerva + le poteau + le tuff block MX Sim (écart moyen 0,6 ft) ; les 4
# rectangles noirs mesurés (centre + grand axe) ; les 2 non marqués gardés à leur place, passés en MX Sim
V38C_TBB = [(580.6, 600.0, 0.999, 0.048), (590.9, 600.4, 0.995, 0.098), (600.1, 601.7, 0.961, 0.278),   # 3 rectangles dans la ligne des boudins Five
            (610.5, 611.0, 0.49, 0.87),                                                                  # gardé (pas de trait marron)
            (612.5, 619.2, -0.034, 0.999),                                                               # rectangle du haut (le long de z)
            (609.8, 629.3, -0.51, 0.86)]                                                                 # gardé (pas de trait marron)
V38_TUFF = [(683.8, 776.6, np.pi, 'honda'),                     # entrée des whoops, à gauche
            (329.6, 736.6, np.pi, 'mv'),   # v38c : 1,5 ft vers la bosse (« un entre-deux, pas aligné ») ;                        # intérieur du virage Moto Verte (T_TR)
            (329.8, 456.7, 0.0, 'yamaha'), (317.5, 470.9, np.pi / 2, 'yamaha'),   # virage Yamaha : à la place des 2 croix
            # v39 (« espace-les bien plus, triple l'espace : une plus vers la pelle, l'autre plus près du 50 Factory ») : écart 7,5 -> 22,5 ft, même milieu
            (285.4, 628.9, np.pi / 2, 'milwaukee'), (285.4, 651.4, np.pi / 2, 'milwaukee'),   # pied du Milwaukee : écartées, rouges
            (316.4, 628.9, np.pi / 2, 'milwaukee'), (316.4, 651.4, np.pi / 2, 'milwaukee')]
V38_RIDER = (686.0, 616.0)   # v39 (rectangle jaune : « à droite de la grille de départ, le même angle ») : 19 ft vers les grilles, même angle ; v38 : (705,0 ; 615,6)
V38_OTER = [(326.7, 452.1), (318.8, 476.1), (329.2, 453.3),   # v38d : + botte Yamaha marquée en gris
                                # croix du virage Yamaha
            (285.4, 642.24), (285.4, 638.74), (316.4, 642.49), (316.4, 638.74)]   # paires collées au pied du Milwaukee                                                          # v36i : point bleu de la capture ; v36j : + 5


def deco_v28(OUT, FOLDER, combos, Hf, lines, line, sd, DV, rep_, g3, gR):
    """v28 (review en jeu de la v27d) : tuff blocks (« bottes de paille ») en plus (captures annotées), boudins sponsors qui sortent 20 s après la chute de
    la grille (ligne de départ, bout du saut AMV vers T_D), poteau de virage après l'arrivée, bâche noire derrière les grilles.
    Renvoie les lignes « tardives » (nofrills.js)."""
    import deco_v28 as D28
    from engine import turn_mid_angle
    P = D28.Placer(BP.PATH, Hf); L_ = lambda t: P.seg(t)['L']
    sec_ = lambda g, nm: next(q for q in g['sections'] if q[2] == nm)
    st3 = next(q for q in g3['sections'] if q[2] != LP.L3_SEC); it3 = combos[st3[2]]['items'][-1]; u_tab = st3[1] + it3[2]   # fin de la petite table
    s3 = sec_(g3, LP.L3_SEC); u_app = s3[1]                                                     # pied de l'appel du freestyle
    g5 = P.seg('L5'); u5 = g5['sections'][0][1]; g6 = P.seg('L6'); s6 = g6['sections'][0]; i6 = combos[s6[2]]['items'][0]
    sR = gR['sections'][0]; itR = combos[sR[2]]['items']; uR2 = sR[1] + next((it[1] for it in itR[1:] if 'roller' in it[0]), LP.CAMEL_U - 10.0 - sR[1])
    uArc = sR[1] + (itR[0][1] + itR[0][2]) / 2
    u_tab0 = st3[1] + it3[1]                                                                    # début (appel) de la petite table
    # v29 (review v28, captures annotées : vert = déplacer, blanc = enlever, rectangle rouge = nouvelle place)
    spec = [('T_Bb', L_('T_Bb') - 5.0, -17.0, 'mxsim'),          # sortie, extérieur (gardée)
            ('L3', u_tab0 + 6.0, -BALE_V, 'mxsim'), ('L3', u_tab0 + 6.0, BALE_V, 'mxsim')]   # « une de chaque côté dans la pelle »
    for u_ in (u_tab - 1.9, u_app + 7.3):                         # v39 (rectangles noirs : « bien trop collés, un ici un ici, symétriques, au bord ») : 6,3 -> 17,5 ft ; v29 : (u_tab + 2,5, u_app + 0,5)
        spec += [('L3', u_, -BALE_V, 'amv'), ('L3', u_, BALE_V, 'amv')]
    # 1re bosse de L6 côté droit : en face des 2 premières du côté gauche (« pas vraiment alignées »)
    c6, s6_ = np.cos(g6['t']), np.sin(g6['t'])
    uL6 = sorted(u_ for u_, v_ in ((((x_ - g6['x0']) * c6 + (z_ - g6['z0']) * s6_), (-(x_ - g6['x0']) * s6_ + (z_ - g6['z0']) * c6))
                                   for x_, z_ in ((float(l_.split()[0][1:]), float(l_.split()[2][:-1])) for l_ in lines if 'bale_u' in l_))
                 if abs(v_ + BALE_V) < 1.0 and -2.0 < u_ < s6[1] + i6[2] + 25.0)[:2]
    if len(uL6) < 2:
        uL6 = [s6[1] + i6[1] + 8.0, s6[1] + i6[2] - 6.0]
    spec += [('T1', 6.0, -17.0, 'honda'), ('L1', 1.5, -22.0, 'honda'), ('L1', -7.0, -22.0, 'honda'),   # T1 : entrée extérieure, avant les whoops
             ('T_E', -11.4, -16.0, 'yamaha'),                                                    # « la verte : au rectangle rouge en dessous »
             ('L6', uL6[0], BALE_V, 'yamaha'), ('L6', uL6[1], BALE_V, 'yamaha'),
             ('T_C', 4.0, -16.0, 'five'), ('T_C', L_('T_C') - 6.0, -16.0, 'five')]              # « tu m'en remets une ici »
    # 1re bosse de L5 : la paire de l'appel enlevée et remise au pied de la bosse (« aligne-les à la piste ») ; descente, plat gardés
    c5, s5_ = np.cos(g5['t']), np.sin(g5['t']); uu5 = np.arange(u5, u5 + 40.0, 0.25)
    h5 = np.ravel(Hf(g5['x0'] + uu5 * c5, g5['z0'] + uu5 * s5_)); u_foot = float(uu5[int(np.argmax(h5 > 0.3))])
    for k_, du in enumerate((u_foot + 3.0 - u5, 19.0, 30.0)):
        spec += [('L5', u5 + du, -BALE_V, 'five' if k_ % 2 == 0 else 'five5'), ('L5', u5 + du, BALE_V, 'five5' if k_ % 2 == 0 else 'five')]
    for u_ in np.arange(8.0, uR2 - 8.0, BALE_STEP2):               # « bottes 50 Factory tout le long du sable »
        if abs(u_ - uArc) > 6.0:
            spec += [('LR', float(u_), -BALE_V, '50factory'), ('LR', float(u_), BALE_V, '50factory')]
    Lb = L_('T_L5b')                                               # « au niveau des ballots de paille, un truc comme ça : des Minerva » (2 rangées le long du virage)
    vM_ = 13.5                                                     # v30 (« les ballots, recentre-les un petit peu ») : |v| 15 -> 13,5 ft
    if True:                                                       # v36f (« les 8 du virage, remets-les ») : gardés
        spec += [('T_L5b', f_ * Lb, -vM_, 'minerva') for f_ in (0.2, 0.5, 0.8)] + [('T_L5b', f_ * Lb, vM_, 'minerva') for f_ in (0.1, 0.3, 0.5, 0.7, 0.9)]
    fb = {}
    for x_, z_, yaw_, key_, r_ in D28.bales(P, spec):
        lines.append(line(x_, z_, yaw_, *fb.setdefault(key_, DV.bale_u(sd, key_))))
    # bottes posées vues de dessus (décalage depuis le centre du virage, ft) : intérieur T1 (2 près du poteau), T_E, T_C (2 sous le poteau)
    cen = lambda t: np.array([P.seg(t)['cx'], P.seg(t)['cz']])
    xy = [(cen('T1') + (1.2, -2.9), 0.0, 'honda'), (cen('T1') + (4.7, 9.0), 0.0, 'honda'),
          (cen('T_E') + (-2.6, 16.4), np.pi / 2, 'yamaha'),
          (cen('T_C') + (1.1, -2.6), 0.0, 'five'), (cen('T_C') + (1.1, 3.9), 0.0, 'five5')]
    for q_, yaw_, key_ in xy:
        lines.append(line(q_[0], q_[1], yaw_, *fb.setdefault(key_, DV.bale_u(sd, key_))))
    rep_['bottes_v29'] = len(spec) + len(xy)
    # poteau de virage : intérieur du 2e virage après l'arrivée, sur du plat ; v29 : 3,7 ft plus loin (rond rouge), bâton de 8 ft tout rouge
    gb = P.seg('T_L5b'); mid = turn_mid_angle(gb); cs = D28.corner_stick(sd)
    flat_ = lambda q: np.ptp([float(np.ravel(Hf(q[0] + a, q[1] + b))[0]) for a in (-1.8, 0, 1.8) for b in (-1.8, 0, 1.8)]) < 0.08
    # v36k (« rapproche-le de la piste ») : plus de décalage de 3,7 ft ; l'intérieur de T_L5b monte vers la piste (2,7 ft à 15 ft de l'axe,
    # plat à partir de 23 ft) : posé à 22,5 ft de l'axe (3 ft plus près qu'avant ; écart de hauteur 0,25 ft sous le socle, ~4° de penche)
    r_ = gb['r'] - 22.5
    q_ = np.array([gb['cx'] + r_ * np.cos(mid), gb['cz'] + r_ * np.sin(mid)]); rep_['poteau_virage_axe'] = round(float(gb['r'] - r_), 1)
    for cs_ in (cs if isinstance(cs, list) else [cs]):            # v36n : socle + bâton RF
        lines.append(line(q_[0], q_[1], 0.0, *cs_))
    rep_['poteau_virage'] = (round(float(q_[0]), 1), round(float(q_[1]), 1))
    # bâche noire derrière les grilles (« des grillages noirs comme à Saint-Georges, sans les sponsors »), 35 ft derrière la grille
    st_ = BP.START; G0 = np.array(st_['gate']); f0 = np.array([np.cos(np.radians(st_['heading'])), np.sin(np.radians(st_['heading']))])
    T0 = G0 - f0 * 35.0; tj = D28.start_tarp_black(sd, os.path.join(BP.ROOT, "tracks", "USLAND2026SaintGeorgesbyBazo", "statue"))
    # v39 (« le mur noir est parti en travers ; les logos sont de l'autre côté et pas centrés : retourne-le, aligne-le à la grille, centre les
    # logos ») : panneau noir plein à nous (90 x 10,4 ft, 2 faces), 6 logos centrés en hauteur côté grilles / pilotes, dos noir ; orientation d'origine
    tj = D28.start_tarp_panel(sd)
    lines.append(line(T0[0], T0[1], float(np.arctan2(-f0[0], -f0[1])), *tj))   # v39 : face imprimée vers les grilles (v38e : +pi, de travers en jeu)
    # boudins sponsors qui sortent 20 s après la chute de la grille
    PROPS = os.path.join(BP.ROOT, "commun/assets", "props")
    bcj, bcs = D28.boudin_court(sd, PROPS)                       # v36 (photo du vrai Paris) : boudins de 6 ft collés, mêmes sponsors
    # v29 (« catastrophe : ça doit partir de la réception du saut jusqu'au virage, pour définir où passer pendant le tour ; au moins 5-6 de
    # chaque marque, pas que ça alterne ») : couloir de la réception après l'arrivée (début de LD) jusqu'à l'entrée du virage MX Sim (T_Bb),
    # d'après les traits rouges des 2 captures : bord nord presque droit vers le début du mur du virage, bord sud qui s'élargit puis va au
    # poteau intérieur ; les portes de chrono du tour dans ce couloir suivent (sinon « coupé la piste »)
    # v35 (reprise de Bazo sur le tracé actuel) : Bazo avait posé ces boudins sur SON tracé (traversée en diagonale après l'arrivée) avec des
    # positions absolues ; ici le tour reprend la ligne de départ LD (vers l'est) puis la boucle T_B, et le départ part vers l'ouest sur
    # LD puis monte à T_D. Même idée, recalée sur ce tracé (« couloir de la réception jusqu'au virage MX Sim, au moins 5-6 de chaque marque,
    # pas que ça alterne » ; « boudins Automoto après le saut freestyle, ferme l'arrivée du départ ») ; portes de chrono : celles de LD
    # suivent déjà le couloir (plus de regate)
    sLD = P.seg('LD')['s0']; at_ = lambda u, v: P.at(sLD + u, v)[0]; gLD = P.seg('LD'); VC_ = 19.0
    pyl = {}                                                     # poteau(x) de chaque virage, rattachés au centre de virage le plus proche
    for x_, z_, _, k_ in pylon_spots(BP.PATH):
        gt_ = min((g_ for g_ in BP.PATH.segs if g_['kind'] == 'T'), key=lambda g_: np.hypot(g_['cx'] - x_, g_['cz'] - z_))
        pyl.setdefault(gt_['tag'][:4], []).append(np.array([x_, z_]))
    A = [at_(14.0, -VC_), at_(gLD['L'] - 17.0, -VC_)]                           # bord nord de LD, jusqu'au début du mur de T_Ba
    pB = min(pyl['T_Bb'], key=lambda q: q[1]); B2 = at_(gLD['L'] - 25.0, VC_)   # bord sud, puis vers le 1er poteau de T_Bb (points de Ryan)
    B = [at_(14.0, VC_), B2, pB - (pB - B2) / np.hypot(*(pB - B2)) * 3.0]
    # v36 (capture annotée : traits orange sur la vue de dessus v36) : lignes redessinées par l'utilisateur, points lus sur son dessin
    # (repère MX, ft) ; bord nord 13 ft plus haut et qui descend vers le virage ; bord sud 27 ft plus bas, droit depuis le poteau de
    # T_Bb, qui se referme sur le début de la ligne Automoto ; « île » : 2e ligne Automoto, côté extérieur (île fermée avec la 1re)
    if V36_LIGNES:
        A = [np.array(q, float) for q in V36_LIGNES['A']]; B = [np.array(q, float) for q in V36_LIGNES['B']]
    third = lambda pts, ks: [k for k in ks for _ in range(-(-D28.n_boudins(pts) // len(ks)))]   # 3 marques à parts égales (au moins 5-6 chacune)
    bB = D28.polyline_boudins(B, third(B, ['five', 'motoverte', 'milwaukee']), False)
    if V36_LIGNES:
        bB = [b_ for b_ in bB if not any(lo_ <= b_[0] <= hi_ for lo_, hi_ in V36_B_COUPES)]
    bl = D28.polyline_boudins(A, third(A, ['mxsim', 'honda', 'yamaha']), True) + bB
    ile0_, ile1_ = [], []
    if V36_LIGNES:
        ile0_ = D28.polyline_boudins(V38_ILE, ['minerva'] * 99, True)   # v38 : Minerva (noir, logo Minerva), un peu plus en travers ; v39 : place du départ
        ile1_ = D28.polyline_boudins(ILE_APRES, ['minerva'] * 99, True)  # v39 : place après 20 s
        bl += ile0_
    rep_['couloir_depart'] = dict(A=[tuple(np.round(q, 1)) for q in A], B=[tuple(np.round(q, 1)) for q in B])
    # Automoto : (1) du bout du panneau AMV côté L2 au poteau intérieur de T_D ; (2) du bout du panneau AMV côté LD, autour de l'extérieur
    # du 1er quart de T_D (TD1), 2,5 ft hors piste : coupe la montée du départ vers T_D (le départ est passé à 20 s)
    sL3 = g3['s0']; uB = LP.BOARD_POLY['amv'][-1][0]
    e1 = P.at(sL3 + uB, -LP.BOARD_VB['amv'])[0]; e2 = P.at(sL3 + uB, LP.BOARD_VB['amv'])[0]
    pD = min(pyl.get('T_D ', []) + pyl.get('TD1 ', []), key=lambda q: np.hypot(*(q - e1)))
    if not V36_SANS_AUTOMOTO:
        bl += D28.polyline_boudins([e1, pD - (pD - e1) / np.hypot(*(pD - e1)) * 2.5], ['automoto'] * 6, True)
    gD1 = P.seg('TD1'); cD_ = np.array([gD1['cx'], gD1['cz']]); rD_ = gD1['r'] + LP.TOP_W / 2 + 4.5
    a_e2 = np.degrees(np.arctan2(e2[1] - cD_[1], e2[0] - cD_[0])); uD_ = lambda a: np.array([np.cos(np.radians(a)), np.sin(np.radians(a))])
    l2_ = [e2] + [cD_ + rD_ * uD_(a) for a in np.linspace(min(-90.0, a_e2 - 15.0) if a_e2 < 0 else -90.0, -172.0, 5)]
    l2_ = [q for k, q in enumerate(l2_) if k == 0 or np.hypot(*(q - cD_)) >= rD_ - 0.1]
    rep_['automoto_ligne2'] = [tuple(np.round(q, 1)) for q in l2_]
    if not V36_SANS_AUTOMOTO:
        bl += D28.polyline_boudins(l2_, ['automoto'] * 6, True)
    late = []; moves_ = {}
    for x_, z_, yaw_, key_ in bl:
        l_ = line(x_, z_, yaw_, bcj, D28.boudin_court_skin(sd, key_, PROPS), bcs); lines.append(l_); late.append(l_)
        if (x_, z_, yaw_, key_) in ile0_:                                # v39 : ligne Minerva déplacée à 20 s
            k_ = ile0_.index((x_, z_, yaw_, key_)); moves_[l_] = ile1_[k_][:3] if k_ < len(ile1_) else None
    rep_['minerva_deplacee'] = dict(depart=len(ile0_), apres_20s=min(len(ile0_), len(ile1_)))
    D28.MOVES = moves_
    D28.ramp_black_venum(os.path.join(OUT, "statue"), os.path.join(BP.ROOT, "commun/assets", "logos", "user"))   # v38 : rampes FMX noires ; v38c : tête de serpent seule
    # v38c : rampe la plus proche de la butte (R1) plus haute / plus raide (+ son habillage), grilles en losanges au sol derrière les 3 rampes
    import hab_objets as HO_
    tj_, ts_ = D28.ramp_tall(os.path.join(OUT, "statue"), RAMP_TALL_K)
    tj2_, ts2_ = D28.ramp_tall(os.path.join(OUT, "statue"), RAMP_MI_K, name='ramp_50_mi')   # v38d (« la rampe de gauche, un petit peu plus haute ») : R2
    tmpd_ = os.path.join(OUT, "statue", "_jupe_haut"); os.makedirs(tmpd_, exist_ok=True); HO_.fmx_jupe(tmpd_, os.path.join(OUT, "statue", tj_))
    # v39b (« sur les sauts freestyle, le logo Monster ») : logo Monster sur les 2 flancs des 3 tremplins, une texture par hauteur
    rep_['rampes_monster'] = D28.ramp_sides_monster(os.path.join(OUT, "statue"), (('ramp_50', 1.0), (tj_[:-3], RAMP_TALL_K), (tj2_[:-3], RAMP_MI_K)))
    png_ = {tj_: tj_[:-3] + '.png', tj2_: tj2_[:-3] + '.png'}
    jdir_ = None
    for f in ["statues"] + ["variants/" + v for v in os.listdir(os.path.join(OUT, "variants")) if v.startswith("statues")]:
        p_ = os.path.join(OUT, f); L_ = open(p_).read().split(chr(10)); rl_ = [(float(l.split()[0][1:]), k) for k, l in enumerate(L_) if '/statue/ramp_50.jm ' in l]
        if not rl_:
            continue
        rl_ = sorted(rl_); x1_, k1_ = rl_[0]; xz1_ = (float(L_[k1_].split()[0][1:]), float(L_[k1_].split()[2][:-1]))
        L_[k1_] = L_[k1_].replace('/statue/ramp_50.jm ', '/statue/' + tj_ + ' ').replace('/statue/ramp_50.shp', '/statue/' + ts_).replace('/statue/ramp_50.png', '/statue/' + png_[tj_])
        if len(rl_) > 1:
            k2_ = rl_[1][1]; L_[k2_] = L_[k2_].replace('/statue/ramp_50.jm ', '/statue/' + tj2_ + ' ').replace('/statue/ramp_50.shp', '/statue/' + ts2_).replace('/statue/ramp_50.png', '/statue/' + png_[tj2_])
        jl_ = [k for k, l in enumerate(L_) if 'fmx_jupe.jm' in l and abs(float(l.split()[0][1:]) - xz1_[0]) < 0.5 and abs(float(l.split()[2][:-1]) - xz1_[1]) < 0.5]
        for k in jl_:
            jdir_ = L_[k].split()[4].rsplit('/', 1)[0]
            L_[k] = L_[k].replace('fmx_jupe.jm', 'fmx_jupe_haut.jm').replace('fmx_jupe.png', 'fmx_jupe_haut.png')
        open(p_, 'w', newline=chr(10)).write(chr(10).join(L_))
    if jdir_:
        dd_ = os.path.join(OUT, jdir_.split('/', 1)[1]) if jdir_.startswith('@') else os.path.join(OUT, jdir_)
        for e_ in ('.jm', '.png'):
            shutil.copy(os.path.join(tmpd_, 'fmx_jupe' + e_), os.path.join(dd_, 'fmx_jupe_haut' + e_))
    shutil.rmtree(tmpd_, ignore_errors=True)
    for (lip_, hd_), Lm_ in zip([(r_['lip'], r_['heading']) for r_ in LP.fmx_ramps(BP.PATH)], RAMP_MAT_L):
        d_ = np.array([np.cos(hd_), np.sin(hd_)]); foot_ = np.array(lip_) - d_ * LP.FMX_MODEL['model_len']; c_ = foot_ - d_ * (Lm_ / 2 + 0.3)
        mj_, mp_ = D28.mesh_mat(sd, Lm_); lines.append(line(c_[0], c_[1], float(np.arctan2(-d_[1], d_[0])), mj_, mp_, None))
    rep_['rampes_v38c'] = dict(k=RAMP_TALL_K, grilles=RAMP_MAT_L, jupe=jdir_)
    # v38c : quelqu'un dans le public (photo de l'utilisateur détourée), 2e rang de la tribune Sud, à hauteur des whoops, taille réelle
    pim_ = os.path.join(BP.ROOT, "commun", "assets", "public", "personne_public.png"); im_ = Image.open(pim_); im_ = im_.crop(im_.getbbox())
    im_.save(os.path.join(OUT, "billboard", "personne_public.png")); asp_ = im_.size[0] / im_.size[1]
    bbp_ = os.path.join(OUT, "billboards"); B_ = open(bbp_).read().split(chr(10)); best_ = None
    for k, l in enumerate(B_):
        if 'crowd_' in l:
            v_ = l.split(); x_, y_, z_ = float(v_[0][1:]), float(v_[1]), float(v_[2][:-1])
            dd2 = abs(y_ - PUBLIC_RANG_Y) * 50 + abs(x_ - PUBLIC_X) + (0 if z_ > 770 else 1e6)
            if best_ is None or dd2 < best_[0]:
                best_ = (dd2, k, x_, y_, z_)
    _, kb_, xb_, yb_, zb_ = best_
    B_[kb_] = "[%.4f %.4f %.4f] %.4f %.4f @%s/billboard/personne_public.png" % (xb_, yb_, zb_, 5.7, asp_, FOLDER)
    open(bbp_, 'w', newline=chr(10)).write(chr(10).join(B_)); rep_['personne_public'] = (xb_, yb_, zb_)
    # v38c (« l'écran, de loin il est tout buggé, on le voit pas : qu'on le voie tout le temps ») : version lointaine (LOD, *_lod8.jm,
    # bascule à 256 ft) de la dalle du classement = vide : de loin on voit l'image fixe de l'écran géant juste derrière
    dl_ = os.path.join(OUT, "statue", "paris", "direct")
    if os.path.isdir(dl_) and not CLASSEMENT_DIRECT:                    # v39 : plus de LOD vide (le nouvel écran se voit de partout)
        mm_ = DV.Mesh(); mm_.tri([(0, -50, 0), (0.01, -50, 0), (0, -50, 0.01)], [(0.5, 0.5)] * 3); mm_.write(os.path.join(dl_, "dalle_lod8.jm"))
    # v29 : bandeau LED du pied des tribunes (USLAND | Supercross Paris | USLAND | MX Sim Racing)
    D28.led_board_v29(os.path.join(OUT, "tex", "led_board-hrepeat.png"), os.path.join(BP.ROOT, "commun/assets", "logos", "user"), os.path.join(BP.ROOT, "pistes/paris-2026/stade_paris", "src"))
    rep_['boudins_tardifs'] = len(late)
    if V36_ZONE:
        from matplotlib.path import Path as Path_
        zone = Path_(V36_ZONE); xz_ = lambda l_: (float(l_.split()[0][1:]), float(l_.split()[2][:-1]))
        drop = lambda l_: ('boudin_noir3' in l_ and zone.contains_point(xz_(l_))) or ('bale_u' in l_ and V36_L5_X[0] < xz_(l_)[0] < V36_L5_X[1]
                                                                                    and min(abs(xz_(l_)[1] - 471.3), abs(xz_(l_)[1] - 502.3)) < 1.5)
        n0 = len(lines); lines[:] = [l_ for l_ in lines if not drop(l_)]; rep_['v36_enleves'] = n0 - len(lines)
        oter_ = []
        for x_, z_ in V36_TUFF_OTER:                                # v36p : le tuff block le plus proche de chaque point blanc
            c_ = [(np.hypot(xz_(l_)[0] - x_, xz_(l_)[1] - z_), k_) for k_, l_ in enumerate(lines) if 'bale_u' in l_ and k_ not in oter_]
            d_, k_ = min(c_); assert d_ < 6.0, ("point blanc sans tuff block", x_, z_, round(d_, 1)); oter_.append(k_)
        lines[:] = [l_ for k_, l_ in enumerate(lines) if k_ not in set(oter_)]; rep_['v36p_tuff_oter'] = len(set(oter_))
        sm_ = BP.PATH.samples(0.5); PX, PZ, PT = np.array(sm_['x']), np.array(sm_['z']), np.array(sm_['th'])
        fm = fb.setdefault('minerva', DV.bale_u(sd, 'minerva')); dmin = []
        for x_, z_ in V36_TUFF:                                     # dans le sens de la piste la plus proche (comme les rangées)
            j_ = int(np.argmin(np.hypot(PX - x_, PZ - z_))); dmin.append(round(float(np.hypot(PX[j_] - x_, PZ[j_] - z_)), 1))
            lines.append(line(x_, z_, float(np.arctan2(-np.sin(PT[j_]), np.cos(PT[j_]))), *(fb.setdefault(V38_TUFF_KEY[(x_, z_)], DV.bale_u(sd, V38_TUFF_KEY[(x_, z_)])) if (x_, z_) in V38_TUFF_KEY else fm)))
        sgm_st = os.path.join(BP.ROOT, "tracks", "USLAND2026SaintGeorgesbyBazo", "statue"); import deco_v22 as D22_
        lines.append(line(V36_POTEAU[0], V36_POTEAU[1], 0.0, "pylon_round.jm", D22_.pylon_skin(sd, sgm_st, 'minerva'), "pylon_round.shp"))
        hz = [float(np.ravel(Hf(V36_POTEAU[0] + a_, V36_POTEAU[1] + b_))[0]) for a_ in (-2.5, 0, 2.5) for b_ in (-2.5, 0, 2.5)]
        rep_['v36_virage_U'] = dict(tuff=len(V36_TUFF), dist_axe_min=min(dmin), poteau_pente=round(max(hz) - min(hz), 2))
        # v38 : enlevés (le tuff block à moins de 1,5 ft de chaque point), posés, courbe de T_Bb, rider gate 50 Factory
        n_ot = 0
        for x_, z_ in V38_OTER:
            c_ = [(np.hypot(xz_(l_)[0] - x_, xz_(l_)[1] - z_), k_) for k_, l_ in enumerate(lines) if 'bale_u' in l_]
            if c_ and min(c_)[0] < 1.5:
                del lines[min(c_)[1]]; n_ot += 1
        for x_, z_, yaw_, key_ in V38_TUFF:
            lines.append(line(x_, z_, yaw_, *fb.setdefault(key_, DV.bale_u(sd, key_))))
        n_cb = 0
        for x_, z_, dx_, dz_ in V38C_TBB:
            lines.append(line(x_, z_, float(np.arctan2(-dz_, dx_)), *fb.setdefault('mxsim', DV.bale_u(sd, 'mxsim')))); n_cb += 1
        rep_['v38'] = dict(oter=n_ot, poses=len(V38_TUFF), courbe_tbb=n_cb)
        # rider gate 50 Factory (« là où j'ai entouré le rectangle noir ») : modèle de Saint-Georges, devant la canette Monster la plus proche
        # du départ, côté piste, on passe dessous dans le sens de x (paddock -> piste)
        for f_ in ("rider_gate.jm", "rider_gate.png", "rider_gate.shp"):
            shutil.copy(os.path.join(sgm_st, f_), os.path.join(sd, f_))
        cans_ = [xz_(l_) for l_ in open(os.path.join(OUT, "statues")).read().split(chr(10)) if 'canette_geante' in l_]
        G0_ = np.array(BP.START['gate'])
        if cans_:
            rg_ = V38_RIDER   # là où était la canette du nord en v36p (rectangle noir de la capture, près du départ ; zone libre en v37)
            lines.append(line(rg_[0], rg_[1], np.pi, "rider_gate.jm", "rider_gate.png", "rider_gate.shp")); rep_['rider_gate'] = tuple(np.round(rg_, 1))
    return late


def roof_ft(x, z):
    """hauteur du toit (ft) au-dessus d'un point du jeu (champ lissé de stade_paris, plan agrandi x PLAN_K)."""
    sys.path.insert(0, os.path.join(BP.ROOT, "pistes/paris-2026/stade_paris", "src"))
    from arena import roof
    f = roof.field(); f = getattr(f, "f", f)                                  # champ à la taille réelle (sans _ScaledField)
    X = ((x - LP.OX) / LP.FT - LP.ARENA_DX) / LP.PLAN_KX; Y = ((LP.OZ - z) / LP.FT - LP.ARENA_DY) / LP.PLAN_KZ   # v37 : stade resserré en z ; v39 : x KX + DX (côté Ouest rapproché)
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
    # v22 (photos du paddock de Paris 2026 de Ryan) : paddock refait (paddock26.py) à la place des 7 camions JGSX (semis_jgsx, v19-v21d),
    # écran géant refait devant le mur de scène
    import paddock26 as PD
    BP.REPORT['paddock_2026'] = PD.apply(BP.OUT, BP.FOLDER)
    if CLASSEMENT_DIRECT:   # v38c (vidéo en jeu : la dalle du classement s'affiche en traits / pointillés roses, de près comme de loin) : coupé
        BP.REPORT['classement_direct'] = classement_direct(BP.OUT, BP.FOLDER)   # v37 : classement en direct sur l'écran géant
    deco_v21(BP.OUT, BP.FOLDER, LS.COMBOS)                             # v21 : murs bâchés + filets, ballots en U, arche 50 Factory
    BP.REPORT['chant_grille'] = chant_grille(BP.OUT, BP.FOLDER)       # v39b : chant sur la grille de départ ; v39c : dans nofrills.js (après deco_v21 qui l'écrit)
    BP.REPORT['cameras_tv'] = cameras_tv(BP.OUT)                      # v37 : caméras TV (comme la RF)


CHANT_VOL = 0.7    # volume du chant (le public de ZION est à 0,4)
CHANT_AVANT = 8.0  # v39c : le chant part 8 s avant la chute de la grille (4 s de chant, fini 4 s avant)


def chant_grille(OUT, FOLDER):
    """v39b (Ryan : « quand on est sur la grille de départ, un petit son, quelqu'un qui chante » ; son mp3, « de la 1re à la 5e seconde ;
    à la fin il ne s'arrête pas d'un coup, il descend sur 2 secondes ») : pistes/paris-2026/sons/chant_grille.wav (1-5 s du mp3 de Ryan,
    fondu de sortie sur les 2 dernières secondes, mono 44,1 kHz, normalisé) copié dans OUT/sounds ; frills.js le lance UNE fois quand on
    arrive sur la grille (avant la chute de la grille ; en entraînement libre, à l'arrivée), à la position de la caméra (comme le public de
    ZION 2025 : mx.add_sound / set_sound_pos / start_sound)."""
    src = os.path.join(HERE, "sons", "chant_grille.wav")
    if not os.path.exists(src):
        return None
    os.makedirs(os.path.join(OUT, "sounds"), exist_ok=True); shutil.copy(src, os.path.join(OUT, "sounds", "chant_grille.wav"))
    js = r"""
/* USLAND Paris by Ryan v39b - chant sur la grille de depart (une fois, avant la chute de la grille). Texte ASCII expres. */
var CG_SON = mx.add_sound("@%s/sounds/chant_grille.wav");
mx.set_sound_freq(CG_SON, 44100);
mx.set_sound_vol(CG_SON, %.2f);
var cg_fait = false, cg_p = [], cg_r = [], cg_t0 = -1, CG_AVANT = %.1f;
function cg_image(secs) {
    try {
        var d = mx.get_gate_drop_time();
        mx.get_camera_location(cg_p, cg_r);
        mx.set_sound_pos(CG_SON, cg_p[0], cg_p[1], cg_p[2]);
        if (cg_t0 < 0) cg_t0 = mx.seconds;
        if (!cg_fait && ((d > 0 && mx.seconds >= d - CG_AVANT && mx.seconds < d) || (d < 0 && mx.seconds - cg_t0 >= 2.0))) {
            mx.start_sound(CG_SON); cg_fait = true;
        }
    } catch (e) { mx.message("chant : " + e.toString()); }
    cg_prev(secs);
}
var cg_prev = mx.frame_handler;
if (!cg_prev) cg_prev = function (s) {};
mx.frame_handler = cg_image;
""" % (FOLDER, CHANT_VOL, CHANT_AVANT)
    # v39c (« le chant ne marche pas ») : dans nofrills.js (toujours lancé, même frills coupés) et plus au chargement : CHANT_AVANT s avant
    # la chute de la grille (course) ou 2 s après l'arrivée (entraînement libre, sans grille)
    open(os.path.join(OUT, "nofrills.js"), "a", newline="\n", encoding="ascii").write(js)
    return dict(fichier="sounds/chant_grille.wav", volume=CHANT_VOL)


def classement_direct(OUT, FOLDER):
    """v37 : dalle « classement en direct » devant l'écran géant (tableau_direct.py) + frills.js ; ligne ajoutée aux statues
    (jour et variantes), à la même place et dans le même sens que l'écran géant posé par paddock26."""
    import re
    import tableau_direct as TD
    L = open(os.path.join(OUT, "statues")).read().splitlines()
    e = [l for l in L if "/ecran_geant.jm " in l]; assert len(e) == 1, "classement : écran géant introuvable"
    m = re.match(r"\[(\S+) \S+ (\S+)\] (\S+)", e[0]); line, rep = TD.make(OUT, FOLDER, float(m.group(1)), float(m.group(2)), float(m.group(3)), os.path.join(BP.AP, "apercu_ecran_direct.png"))
    for f in ["statues"] + ["variants/" + v for v in os.listdir(os.path.join(OUT, "variants")) if v.startswith("statues")]:
        p_ = os.path.join(OUT, f); L_ = [l for l in open(p_).read().splitlines() if l.strip() and "/paris/direct/" not in l]   # v39b : 2 statues (direct_a, direct_b)
        open(p_, "w", newline="\n").write("\n".join(L_ + line) + "\n")
    return rep


# v37 (« sur la RF il y a une cam broadcast, fais les caméras TV ») : fichier « cameras » comme RF / ZION : par caméra « autofovsize »
# (largeur cadrée, ft), « gate » = portes de chrono (indices des checkpoints de timing_gates) où le jeu passe sur cette caméra, puis
# « addcamera x y z » (y = hauteur, ft). Caméras en haut des tribunes basses (Nord z 372, Sud z 822, Est x 215) et au-dessus de la
# paddock (x 800, 60 ft : au-dessus des camions), une par enchaînement dans l'ordre du tour (pas la plus proche : ça sauterait d'une caméra à l'autre à chaque porte).
# Chaque porte a une caméra ; contrôlé sur la position des portes (± 30 ft).
CAMERAS_TV = [  # (nom, (x, y, z), autofovsize, [(porte, x attendu, z attendu), ...])
    ("départ, derrière les grilles (au-dessus du paddock)", (800.0, 60.0, 575.0), 35, [(27, 526, 556)]),
    ("1er virage et ligne droite Est", (215.0, 40.0, 600.0), 30, [(28, 345, 623), (18, 301, 642), (19, 301, 550), (20, 307, 444)]),
    ("tribune Nord, ligne droite du haut", (560.0, 45.0, 372.0), 30, [(21, 407, 438), (22, 491, 438), (23, 576, 438), (24, 685, 462)]),
    ("tribune Nord, L5 et virages en U", (450.0, 45.0, 372.0), 30, [(25, 569, 487), (26, 537, 487), (0, 478, 487), (1, 372, 493),
                                                                   (2, 375, 552), (3, 470, 562)]),
    ("virages Ouest (au-dessus du paddock)", (800.0, 60.0, 615.0), 35, [(4, 542, 562), (5, 630, 568), (6, 630, 643)]),
    ("tribune Sud, centre", (480.0, 45.0, 822.0), 30, [(7, 532, 649), (8, 448, 649), (15, 500, 754)]),
    ("tribune Sud, côté Est", (360.0, 45.0, 822.0), 30, [(9, 351, 655), (10, 355, 695), (11, 479, 705), (16, 411, 754), (17, 307, 748)]),
    ("tribune Sud, côté Ouest", (640.0, 45.0, 822.0), 30, [(12, 578, 705), (13, 701, 730), (14, 588, 754)]),
]


def cameras_tv(OUT):
    import re
    tg = open(os.path.join(OUT, "timing_gates")).read()
    cp = tg.split("checkpoints:")[1].split("firstlap:")[0].strip().splitlines()
    G = [tuple(float(v) for v in re.findall(r"\[(\S+) \S+ (\S+)\]", l)[0]) for l in cp]
    vues = sorted(g for _, _, _, gl in CAMERAS_TV for g, _, _ in gl)
    assert vues == list(range(len(G))), "caméras TV : chaque porte doit avoir une caméra (%d portes)" % len(G)
    out = []
    for nom, (x, y, z), fov, gl in CAMERAS_TV:
        for g, xe, ze in gl:
            assert abs(G[g][0] - xe) < 30 and abs(G[g][1] - ze) < 30, ("caméras TV : la porte %d a bougé" % g, G[g])
        out += ["autofovsize %d" % fov, "gate " + " ".join(str(g) for g, _, _ in gl), "addcamera %.1f %.1f %.1f" % (x, y, z), ""]
    open(os.path.join(OUT, "cameras"), "w", newline="\n").write("\n".join(out))
    return dict(cameras=len(CAMERAS_TV), portes=len(G))


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
_keep_layers()                   # v38e : couches du relief gardées pour crease_smooth (après le choix de render)
BP.export = export_zion

def _open_retry():
    """v26 : sous Windows un fichier de la piste juste écrit est parfois verrouillé un instant (Errno 22 / 13 à la réécriture) :
    chaque ouverture en écriture réessaie 8 fois (1,5 s)."""
    import builtins
    import time
    _o = builtins.open

    def op(f, mode='r', *a, **k):
        for i_ in range(8):
            try:
                return _o(f, mode, *a, **k)
            except OSError as e:
                if not any(c in mode for c in 'wax+') or e.errno not in (13, 22) or i_ == 7:
                    raise
                time.sleep(1.5)
    builtins.open = op


if __name__ == "__main__":
    # v37 (« quand il pull git, que ça lance directement la fabrication et que ça mette dans son jeu ») : --out DOSSIER construit la piste
    # ailleurs que dans le dépôt (commun/tools/maj_paris.ps1 : dossier temporaire puis copie dans MX Simulator) ; aperçus à côté
    if "--out" in sys.argv:
        BP.OUT = os.path.abspath(sys.argv[sys.argv.index("--out") + 1]); BP.AP = BP.OUT + "_apercu"
        os.makedirs(BP.AP, exist_ok=True)
    _open_retry()
    BP.main()
