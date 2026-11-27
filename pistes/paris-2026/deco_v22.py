"""v22 (version Zion) : murs des virages et arche 50 Factory refaits d'après 4 vraies photos de Paris envoyées par l'utilisateur
(pistes/paris-2026/refs/photos_murs_v22/) : « comment est la bâche dans les virages, le mur de paille entouré de bâches grises, comment les
filets sont faits ; il faut que tu les recrées parfaitement » + « l'arche 50 Factory, les logos pile où il faut ».

  MUR (photos mur_filet_*.jpg) : bloc de paille rectangulaire (BLK) emballé dans une bâche grise pleine de plis, plat dessus, la
  bâche tombe jusqu'au sol derrière ; posé juste derrière la crête du berm (la terre du berm monte jusqu'au pied de la bâche).
  Dessus : boudins gonflables « AIR » en modules (AIRF) : 2 tubes côte à côte, housse rouge, bouts blancs, une bannière blanche
  sponsor (FIVE) sur la face côté piste de chaque module. Derrière, sur le bord arrière du bloc : filet rouge maillé sans inscription,
  poteaux rouges dans le plan du filet (bouchon jaune en haut) à chaque raccord de modules ; poteaux du milieu dans une mousse ronde
  noire, poteaux des bouts dans une grosse mousse rectangulaire noire. Plus de ficelles (aucune sur les photos).
  ARCHE (photo arche_50factory.jpg) : cadre en tissu jaune à bords noirs : 2 colonnes pleine hauteur (logo vertical sur les côtés),
  poutre entre les colonnes (gros 50FACTORY.com des deux côtés), colonnes posées sur la pointe de 2 tentes triangulaires jaunes
  (triangle vu depuis le côté de la piste, logo horizontal dessus, logo le long de la pente, jupe noire en bas).
DIMENSIONS ESTIMÉES SUR LES PHOTOS (pas des mesures). Repère des modèles (doc 12) : y vers le haut.
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import hab_kit as K                       # noqa: E402
from hab_kit import Mesh, R, logo, fit    # noqa: E402
from deco_v21 import _face, _save, BLACK, MAT_MAT, MAT_BACHE, NET_RED, _tri_section   # noqa: E402

BLK = dict(W=3.0, H=3.4, rnd=0.25, flare=0.35, back=0.3, sink=1.0)   # v25c (« même largeur que les 3 boudins, ça dépasse ») : 4,6 -> 3,0 ft   # v23 (« enterre plus ; plus près du sommet du virage ») : sink 0,3 -> 1,0, back 0,9 -> 0,3   # bloc de paille bâché (ft) ; back = écart crête -> face avant
AIRF = dict(ra=0.95, mod=10.0, gap=0.45, end=0.7, squash=0.9, rb=0.72, nmin=3, nmax=4)   # v23 : fagot de 3 boudins (rb), modules fixes de 10 ft (3 ou 4)
# v23 (« les trucs FIVE : tout noir, pas FIVE partout, en fonction du sponsor ») : sponsor du mur de chaque virage (code couleur de l'utilisateur)
TURN_SPONSOR = {'T_L5a': 'minerva', 'T_Bb': None, 'T_D ': 'automoto', 'T1 1': 'honda', 'T_TR': 'motoverte', 'T_E ': 'yamaha', 'T_C ': 'five'}      # boudins AIR : rayon, module, jour entre modules, bout arrondi
NETV = dict(above=8.0, pole_r=0.10, cap=0.35, pad_r=0.32, pad_h=4.5, epad=(1.5, 0.9), epad_h=5.5, off=0.25)
RED_AIR = (200, 18, 26); YELLOW_CAP = (250, 200, 30); RED_POLE = (190, 20, 24)
BANNERS = ('five', 'five_rouge')


# ---------------------------------------------------------------- textures
def tarp_texture(out):
    """bâche grise du bloc de paille ; v25e (« trop de noir dans les murs, la texture pas bien, un reflet pourri ; fais plus simple, plus
    lisse, moins de détails ») : gris moyen presque uni, quelques grands plis très doux, pas de cassures sombres (et mat, pas de reflet)."""
    from scipy.ndimage import gaussian_filter
    W, H = 512, 1024; rng = np.random.default_rng(22)
    fold = gaussian_filter(rng.normal(0, 1, (H, W)), (120, 18), mode='wrap'); fold /= fold.std()
    a = np.array([118.0, 119, 122])[None, None, :] + (fold * 5)[..., None] + rng.normal(0, 0.8, (H, W, 1))
    _save(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), os.path.join(out, 'bache_paille.png'))
    return 'bache_paille.png'


def air_texture(out):
    """atlas des boudins AIR : housse rouge (le tour du tube), bout blanc avec valve grise, 2 bannières blanches (FIVE noir / FIVE
    rouge, bande rouge en bas comme sur la photo). Échelle identique en u et v sur les bannières : logo jamais déformé."""
    W, H = 2048, 1024; im = Image.new('RGB', (W, H), RED_AIR); d = ImageDraw.Draw(im); rng = np.random.default_rng(5)
    # housse rouge (0..1024 x 0..512) : coutures + plis légers
    for x in range(0, 1024, 128):
        d.line([(x, 0), (x, 512)], fill=(170, 12, 20), width=3)
    d.rectangle([0, 500, 1024, 512], fill=(150, 10, 16))
    # bout blanc (1024..1280 x 0..256) : disque blanc, valve grise
    d.rectangle([1024, 0, 1280, 256], fill=(236, 236, 234)); d.ellipse([1124, 100, 1180, 156], fill=(120, 122, 126))
    d.ellipse([1138, 114, 1166, 142], fill=(70, 72, 76))
    # noirs / rouge poteau / jaune bouchon (petits carrés de couleur unie)
    d.rectangle([1300, 0, 1360, 60], fill=BLACK); d.rectangle([1380, 0, 1440, 60], fill=RED_POLE); d.rectangle([1460, 0, 1520, 60], fill=YELLOW_CAP)
    # bannières : 2 bandes de 2048 x 230 px (ratio = longueur / hauteur de la bannière posée)
    L5 = logo('five'); ban = {}
    for k, key in enumerate(BANNERS):
        y0 = 540 + k * 240; bb = (0, y0, 2048, y0 + 230); d.rectangle(bb, fill=(244, 244, 242))
        d.rectangle([0, y0 + 196, 2048, y0 + 230], fill=RED_AIR)
        lg = L5 if key == 'five' else K.tint(L5, (214, 24, 30))
        fit(im, lg, (300, y0 + 18, 1748, y0 + 190), 0.04)
        ban[key] = bb
    im = K.grain(im, 1.4); _save(im, os.path.join(out, 'airfence.png'))
    return dict(png='airfence.png', body=R((0, 0, 1024, 512), W, H), cap=R((1024, 0, 1280, 256), W, H), blk=R((1300, 0, 1360, 60), W, H),
                red=R((1380, 0, 1440, 60), W, H), yel=R((1460, 0, 1520, 60), W, H), ban={k: R(b, W, H) for k, b in ban.items()},
                ban_ratio=2048 / 230)


def bundle_texture(out, key, Lm=9.55):
    """v23 : bâche NOIRE autour du fagot de 3 boudins, logo du sponsor (key) sur la face côté piste (v de 0,10 à 0,44 du tour : pied
    intérieur -> dessus), centré sur le module ; logo pré-étiré pour ne pas être déformé (u = Lm ft, v = tour de la section)."""
    from scipy.ndimage import gaussian_filter
    P = float(np.sum(np.hypot(*np.diff(_tri_section(AIRF['rb'])[:, :2], axis=0).T))); W = H = 2048
    rng = np.random.default_rng(7); n = gaussian_filter(rng.normal(0, 1, (H, W)), (40, 6)); n /= n.std()
    a = np.full((H, W, 3), 24.0) + (n * 4)[..., None]; im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if key:
        lg = logo(key) if key != 'five' else K.tint(logo('five'), (236, 236, 236))
        if key in ('automoto', 'honda', 'minerva', 'motoverte', 'yamaha'):
            pass
        lg = lg.resize((lg.size[0], max(1, int(lg.size[1] * Lm / P))), Image.LANCZOS)        # pré-étiré : pas déformé une fois posé
        y0, y1 = int(H * (1 - 0.44)), int(H * (1 - 0.10)); fit(im, lg, (int(W * 0.12), y0, int(W * 0.88), y1), 0.05)
    _save(im, os.path.join(out, 'fagot_%s.png' % (key or 'noir'))); return 'fagot_%s.png' % (key or 'noir')


def net_texture(out):
    """filet rouge maillé de la v21 (stt_props) ; dans la zone opaque du bas : noir (mousses), rouge (poteaux), jaune (bouchons)."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "commun/scripts"))
    import stt_props as SPn
    im = SPn.net_ribbon_texture(NET_RED, cell=0.16, strand=2, knot=4); a = np.array(im)
    NR, TH = SPn.NETR['NR'], SPn.NETR['TH']; Wn = a.shape[1]
    a[NR + 32:, :, :3] = (24, 24, 26); a[NR + 32:, :, 3] = 255
    q = (TH - (NR + 32)) // 2 + NR + 32
    a[q - 6:q + 6, Wn // 2 - 40:Wn // 2 - 20, :3] = RED_POLE; a[q - 6:q + 6, Wn // 2 + 20:Wn // 2 + 40, :3] = YELLOW_CAP
    Image.fromarray(a, 'RGBA').save(os.path.join(out, 'filet_rouge_v22.png'), optimize=True)
    uv = lambda px, py: ((px + 0.5) / Wn, 1 - (py + 0.5) / TH)
    return dict(png='filet_rouge_v22.png', v=(1 - (NR - 1) / TH, 1.0), blk=uv(Wn // 2, q), red=uv(Wn // 2 - 30, q), yel=uv(Wn // 2 + 30, q))


# ---------------------------------------------------------------- mur de paille + boudins AIR + filet
def _sec_block(yf, yt, yb):
    """section du bloc (d vers l'extérieur du virage, y) du pied avant (jupe) au pied arrière, arêtes du dessus arrondies."""
    W, rn, fl = BLK['W'], BLK['rnd'], BLK['flare']; P = [(-W / 2 - fl, yf), (-W / 2, yf + 0.5)]
    P += [(-W / 2 + rn - rn * np.cos(a), yt - rn + rn * np.sin(a)) for a in np.linspace(0, np.pi / 2, 5)]
    P += [(W / 2 - rn + rn * np.cos(a), yt - rn + rn * np.sin(a)) for a in np.linspace(np.pi / 2, 0, 5)]
    P += [(W / 2, yb + 0.5), (W / 2 + fl, yb)]
    P = np.array(P); t = np.gradient(P, axis=0); n = np.c_[-t[:, 1], t[:, 0]]; n /= np.linalg.norm(n, axis=1, keepdims=True)
    if n[len(P) // 2, 1] < 0:
        n = -n
    return np.c_[P, n]


def _obox(m, c, tg, e, w, dp, y0, y1, uv):
    """boîte orientée : centre au sol c (x, z), tg = tangente, e = normale (unitaires, horizontales), largeur w (le long de tg),
    profondeur dp (le long de e), de y0 à y1 ; une seule couleur (uv)."""
    c, tg, e = np.asarray(c, float), np.asarray(tg, float), np.asarray(e, float)
    co = lambda a, b, y: (c[0] + tg[0] * a + e[0] * b, y, c[1] + tg[1] * a + e[1] * b)
    for (a0, b0), (a1, b1), nn in ((((-1, -1), (1, -1), -e)), (((1, -1), (1, 1), tg)), (((1, 1), (-1, 1), e)), (((-1, 1), (-1, -1), -tg))):
        P = [co(a0 * w / 2, b0 * dp / 2, y0), co(a1 * w / 2, b1 * dp / 2, y0), co(a1 * w / 2, b1 * dp / 2, y1), co(a0 * w / 2, b0 * dp / 2, y1)]
        _face(m, P, [uv] * 4, [(nn[0], 0, nn[1])] * 4)
    _face(m, [co(-w / 2, -dp / 2, y1), co(w / 2, -dp / 2, y1), co(w / 2, dp / 2, y1), co(-w / 2, dp / 2, y1)], [uv] * 4, [(0, 1, 0)] * 4)


def turn_wall(out, k, g, Hf, f0, f1, AT, NT):
    """mur d'un virage, de la fraction f0 à f1 ; Hf(x, z) = hauteur du terrain. Modèles en coordonnées du virage : origine au centre
    (sol plat), lacet 0. AT = atlas des boudins (air_texture), NT = filet (net_texture)."""
    sg = 1.0 if g['ang'] > 0 else -1.0; th_in = g['t0'] + sg * np.pi / 2; ang = np.radians(g['ang'])
    th = lambda f: th_in - ang * f
    cx, cz = g['cx'], g['cz']; h0 = float(np.ravel(Hf(cx, cz))[0])
    tm = th((f0 + f1) / 2); rr = np.arange(g['r'], g['r'] + 40, 0.5)
    r_crest = float(rr[int(np.argmax(Hf(cx + np.cos(tm) * rr, cz + np.sin(tm) * rr)))])
    W, Hb = BLK['W'], BLK['H']; rc = r_crest + BLK['back'] + W / 2
    # v23 (« ne change pas la taille : plus court 3, plus long 4 ») : 3 ou 4 modules de 10 ft, centrés sur le même milieu
    nmod_ = int(np.clip(round(abs(ang * (f1 - f0)) * rc / AIRF['mod']), AIRF['nmin'], AIRF['nmax'])); fm_ = (f0 + f1) / 2
    hf_ = nmod_ * AIRF['mod'] / (2 * abs(ang) * rc); f0, f1 = fm_ - hf_, fm_ + hf_
    L_arc = abs(ang * (f1 - f0)) * rc; ns = max(8, int(L_arc / 1.2)); fs = np.linspace(f0, f1, ns + 1); sarc = np.linspace(0, L_arc, ns + 1)
    yf = np.empty(len(fs)); yb = np.empty(len(fs))
    for i, f in enumerate(fs):
        e = np.array([np.cos(th(f)), np.sin(th(f))]); rr_ = r_crest + np.linspace(-4, 4, 9)
        hc = float(np.max(Hf(cx + e[0] * rr_, cz + e[1] * rr_)))
        yf[i] = hc - BLK['sink']                                                          # pied avant : à la crête du berm
        dd = np.linspace(0, W / 2 + BLK['flare'], 6); yb[i] = float(np.min(Hf(cx + e[0] * (rc + dd), cz + e[1] * (rc + dd)))) - BLK['sink']
    from scipy.ndimage import gaussian_filter1d
    yf = gaussian_filter1d(yf, 1.5, mode='nearest'); yt = yf + Hb; yb = np.minimum(yb, yf)
    E = lambda f: np.array([np.cos(th(f)), np.sin(th(f))])
    # --- bloc bâché
    m = Mesh(); ring = []
    for i, f in enumerate(fs):
        e = E(f); sec = _sec_block(yf[i], yt[i], yb[i]); sl = np.r_[0, np.cumsum(np.hypot(*np.diff(sec[:, :2], axis=0).T))]
        ring.append([((e[0] * (rc + d), y - h0, e[1] * (rc + d)), (e[0] * nd, ny, e[1] * nd), (sarc[i] / 8.0, sl[j] / 9.0))
                     for j, (d, y, nd, ny) in enumerate(sec)])
    for i in range(len(ring) - 1):
        for j in range(len(ring[0]) - 1):
            a_, b_, c_, d_ = ring[i][j], ring[i + 1][j], ring[i + 1][j + 1], ring[i][j + 1]
            _face(m, [a_[0], b_[0], c_[0], d_[0]], [a_[2], b_[2], c_[2], d_[2]], [a_[1], b_[1], c_[1], d_[1]])
    for i, sgn in ((0, -1), (len(ring) - 1, 1)):                                          # bouts coupés droit (photo 3)
        tdir = np.array([-np.sin(th(fs[i])), np.cos(th(fs[i]))]) * np.sign(-ang) * sgn; nrm = (tdir[0], 0.0, tdir[1])
        pts = [q[0] for q in ring[i]]; cen = np.mean(pts, axis=0)
        for j in range(len(pts) - 1):
            _face(m, [cen, pts[j], pts[j + 1]], [(0.3, 0.5), (0.3 + 0.02 * j, 0.1), (0.32 + 0.02 * j, 0.1)], [nrm] * 3)
    m.write(os.path.join(out, 'mur_virage_%d.jm' % k), MAT_BACHE)
    K.shp(os.path.join(out, 'mur_virage_%d.shp' % k),
          [(np.cos(th(f)) * rc, yf[i] + 1.6 - h0, np.sin(th(f)) * rc) for i, f in enumerate(fs) if i % 2 == 0], 2.2)
    ytop = lambda s: float(np.interp(s, sarc, yt)); fof = lambda s: float(np.interp(s, sarc, fs))
    # --- v23 : fagots de 3 boudins (2 en bas + 1 dessus) sous une bâche noire, logo du sponsor côté piste ; modules de 10 ft fixes
    nmod = max(1, int(round(L_arc / AIRF['mod']))); edges = np.linspace(0, L_arc, nmod + 1); a2 = Mesh()
    sec = _tri_section(AIRF['rb'], 30); dcen = -W / 2 + 2 * AIRF['rb'] + 0.15; ra = AIRF['rb']
    for q in range(nmod):
        sa, sb = edges[q] + AIRF['gap'] / 2, edges[q + 1] - AIRF['gap'] / 2; Lm = sb - sa
        ss = np.unique(np.r_[np.linspace(sa, sb, max(6, int(Lm / 0.8)) + 1), sa + np.linspace(0, AIRF['end'], 5), sb - np.linspace(0, AIRF['end'], 5)])
        rows = []
        for s_ in ss:
            x_ = min(s_ - sa, sb - s_); kk = np.sqrt(np.clip(x_ / AIRF['end'], 0, 1) * (2 - np.clip(x_ / AIRF['end'], 0, 1))); kk = 0.3 + 0.7 * kk
            f = fof(s_); e = E(f); y0 = ytop(s_) - 0.12 - h0; fu = (s_ - sa) / Lm; fu = 1 - fu if ang > 0 else fu
            rows.append([((e[0] * (rc + dcen + d * kk), y0 + y * kk, e[1] * (rc + dcen + d * kk)), (e[0] * nd, ny, e[1] * nd), (fu, j / (len(sec) - 1)))
                         for j, (d, y, nd, ny) in enumerate(sec)])
        for i in range(len(rows) - 1):
            for j in range(len(sec) - 1):
                A, B, C, D = rows[i][j], rows[i + 1][j], rows[i + 1][j + 1], rows[i][j + 1]
                _face(a2, [A[0], B[0], C[0], D[0]], [A[2], B[2], C[2], D[2]], [A[1], B[1], C[1], D[1]])
        for i, sgn in ((0, -1), (len(rows) - 1, 1)):
            f = fof(ss[i]); tdir = np.array([-np.sin(th(f)), np.cos(th(f))]) * np.sign(-ang) * sgn; nrm = (tdir[0], 0, tdir[1])
            pts = [r_[0] for r_ in rows[i]]; cen = np.mean(pts, axis=0)
            for j in range(len(pts) - 1):
                _face(a2, [cen, pts[j], pts[j + 1]], [(0.02, 0.98)] * 3, [nrm] * 3)
    a2.write(os.path.join(out, 'air_virage_%d.jm' % k), MAT_BACHE)
    K.shp(os.path.join(out, 'air_virage_%d.shp' % k),
          [(np.cos(th(fof(s))) * (rc + dcen), ytop(s) + ra - h0, np.sin(th(fof(s))) * (rc + dcen)) for s in np.arange(0.5, L_arc, 2.0)],
          1.2, par=(0.6, 150, 8))
    # --- filet sur le bord arrière du bloc + poteaux rouges (bouchon jaune) + mousses noires
    rn = rc + W / 2 - NETV['off']; n2 = Mesh(); Vb, Vt = NT['v']; TL = 4.0; sph = []
    sv = np.linspace(0, L_arc, max(2, int(L_arc / 1.0) + 1)); bot = np.array([ytop(s) for s in sv]) - 0.2 - h0
    upp = bot + 0.2 + ra * (2 + np.sqrt(3)) + NETV['above']
    P2 = lambda f, r_: (np.cos(th(f)) * r_, np.sin(th(f)) * r_)
    for i in range(len(sv) - 1):
        cuts = [sv[i]] + [q * TL for q in range(int(sv[i] // TL) + 1, int(sv[i + 1] // TL) + 1) if sv[i] < q * TL < sv[i + 1]] + [sv[i + 1]]
        for sa, sb in zip(cuts[:-1], cuts[1:]):
            fa, fb = fof(sa), fof(sb); ba, bb = np.interp(sa, sv, bot), np.interp(sb, sv, bot)
            ta, tb = np.interp(sa, sv, upp), np.interp(sb, sv, upp); q0 = np.floor(sa / TL + 1e-9); ua, ub_ = sa / TL - q0, sb / TL - q0
            (xa, za), (xb, zb) = P2(fa, rn), P2(fb, rn); e = np.array([np.cos(th((fa + fb) / 2)), 0, np.sin(th((fa + fb) / 2))])
            Q = [(xa, ba, za), (xb, bb, zb), (xb, tb, zb), (xa, ta, za)]; UV = [(ua, Vb), (ub_, Vb), (ub_, Vt), (ua, Vt)]
            _face(n2, Q, UV, [-e] * 4); _face(n2, Q, UV, [e] * 4)
    for s_ in sv[::2]:
        x_, z_ = P2(fof(s_), rn); sph += [(x_, np.interp(s_, sv, bot) + h_, z_) for h_ in (3.0, 4.6, 6.2)]
    dot = lambda u: (u[0], u[1], u[0] + 0.0005, u[1] + 0.0005)
    for qi, s_ in enumerate(edges):
        s_ = float(np.clip(s_, 0.15, L_arc - 0.15)); f = fof(s_); x_, z_ = P2(f, rn + 0.12); yb_ = ytop(s_) - h0 - 0.2
        yt_ = float(np.interp(s_, sv, upp)) + 0.35
        n2.tube((x_, yb_, z_), (x_, yt_, z_), NETV['pole_r'], dot(NT['red']), 8)
        n2.tube((x_, yt_, z_), (x_, yt_ + NETV['cap'], z_), NETV['pole_r'] * 1.25, dot(NT['yel']), 8)
        ya = ytop(s_) - h0 - 0.05
        if qi in (0, len(edges) - 1):                                                     # bouts : grosse mousse rectangulaire
            e2 = E(f); tg = np.array([-e2[1], e2[0]]); w_, dp_ = NETV['epad']
            sh_ = 1 if qi == 0 else -1; cen = (x_ + tg[0] * sh_ * np.sign(-ang) * (w_ / 2 - 0.3) * 0, z_)
            _obox(n2, (x_ - e2[0] * (dp_ / 2 - 0.1), z_ - e2[1] * (dp_ / 2 - 0.1)), tg, e2, w_, dp_, ya, ya + NETV['epad_h'], NT['blk'])
        else:                                                                             # milieu : mousse ronde noire
            n2.tube((x_, ya, z_), (x_, ya + NETV['pad_h'], z_), NETV['pad_r'], dot(NT['blk']), 10)
    n2.write(os.path.join(out, 'filet_virage_%d.jm' % k), MAT_MAT)
    K.shp(os.path.join(out, 'filet_virage_%d.shp' % k), sph, 0.9, par=(1.0, 85, 4))
    return dict(origin=(cx, cz), r_wall=round(rc, 1), arc_ft=round(L_arc, 1), modules=nmod, h0=round(h0, 2),
                files=(('mur_virage_%d.jm' % k, 'bache_paille.png', 'mur_virage_%d.shp' % k),
                       ('air_virage_%d.jm' % k, AT, 'air_virage_%d.shp' % k),
                       ('filet_virage_%d.jm' % k, NT['png'], 'filet_virage_%d.shp' % k)))


# ---------------------------------------------------------------- arche 50 Factory (photo arche_50factory.jpg)
AR = dict(xc=20.0, B=10.0, Ht=7.0, T=3.0, cw=3.0, ct=1.6, top=19.0, bh=5.0, bd=1.2, skirt=0.5)   # v23 : triangles beaucoup plus gros (7,5 x 5 -> 10 x 7 ft)   # poutre haute comme sur la photo


def _fabric(im, box, amp=10, seed=1):
    """plis de tissu (bandes diagonales douces) dans un rectangle de l'image."""
    from scipy.ndimage import gaussian_filter
    x0, y0, x1, y1 = box; h, w = y1 - y0, x1 - x0; rng = np.random.default_rng(seed)
    n = gaussian_filter(rng.normal(0, 1, (h, w)), (3, 22)); n /= n.std() or 1
    yy, xx = np.mgrid[0:h, 0:w]; n = n * (0.6 + 0.4 * np.sin((xx + yy * 0.6) / 35.0))
    a = np.asarray(im, float); a[y0:y1, x0:x1] += (n * amp)[..., None]; return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def arche_50f(out, drop=0.0, xc=None):
    """repère : +z = sens de la piste ; pieds à x = +-xc ; triangles dans le plan (z, y), vus depuis le côté de la piste ;
    colonnes de Ht à top, poutre entre les colonnes (bh de haut, même dessus que les colonnes)."""
    a = dict(AR); xc = xc or a['xc']; B, Ht, T, cw, ct, top, bh, bd = (a[k] for k in ('B', 'Ht', 'T', 'cw', 'ct', 'top', 'bh', 'bd'))
    Y = (246, 220, 40); W, H = 2048, 2048; im = Image.new('RGB', (W, H), Y); d = ImageDraw.Draw(im); L50 = logo('50factory'); ol = 12
    S = 100                                                                                     # 100 px / ft
    tri = (0, 0, int(B * S), int(Ht * S)); d.rectangle(tri, fill=BLACK)
    d.polygon([(ol * 1.9, tri[3] - ol), (tri[2] - ol * 1.9, tri[3] - ol), (tri[2] / 2, ol * 2.2)], fill=Y)
    fit(im, L50, (tri[2] * 0.2, tri[3] * 0.60, tri[2] * 0.8, tri[3] * 0.90), 0.02)          # logo horizontal, bas du triangle
    sl = float(np.hypot(B / 2, Ht)); slope = (1020, 0, 1020 + int(T * S), int(sl * S))
    d.rectangle(slope, fill=Y); d.rectangle([slope[0], 0, slope[0] + ol, slope[3]], fill=BLACK); d.rectangle([slope[2] - ol, 0, slope[2], slope[3]], fill=BLACK)
    fit(im, L50.rotate(90, expand=True), (slope[0] + ol + 10, 40, slope[2] - ol - 10, slope[3] - 40), 0.02)   # le long de la pente
    ch = top - Ht + 0.3; cs = (1340, 0, 1340 + int(cw * S), int(ch * S))                       # colonne, faces de côté (larges)
    d.rectangle(cs, fill=BLACK); d.rectangle([cs[0] + ol, cs[1] + ol, cs[2] - ol, cs[3] - ol], fill=Y)
    fit(im, L50.rotate(90, expand=True), (cs[0] + ol + 12, cs[1] + 30, cs[2] - ol - 12, cs[3] - 30), 0.02)
    cf = (1660, 0, 1660 + int(ct * S), int(ch * S)); d.rectangle(cf, fill=BLACK); d.rectangle([cf[0] + ol, cf[1] + ol, cf[2] - ol, cf[3] - ol], fill=Y)
    bw = 2 * xc - ct; ban = (0, 1520, 2048, 1520 + int(round(bh * 2048 / bw)))                 # poutre : même échelle en u et en v
    d.rectangle(ban, fill=BLACK); d.rectangle([ban[0] + 8, ban[1] + 8, ban[2] - 8, ban[3] - 8], fill=Y)
    fit(im, L50, (ban[0] + 200, ban[1] + 6, ban[2] - 200, ban[3] - 6), 0.03)
    d.rectangle([1850, 100, 1900, 150], fill=Y); d.rectangle([1905, 100, 1955, 150], fill=BLACK); d.rectangle([1960, 100, 2010, 150], fill=(40, 40, 44))
    for bx in (tri, slope, cs, cf, ban):
        im = _fabric(im, bx, 9, seed=bx[0] + bx[1])
    im = K.shade_v(im, tri, 1.0, 0.86); im = K.grain(im, 1.0); _save(im, os.path.join(out, 'arche_50f.png'))
    m = Mesh(); rt, rs, rcs, rcf, rb = (R(b, W, H) for b in (tri, slope, cs, cf, ban))
    ry = R((1850, 100, 1900, 150), W, H); rk = R((1905, 100, 1955, 150), W, H); rsk = R((1960, 100, 2010, 150), W, H)
    for sx in (-1, 1):
        x0, x1 = sx * xc - T / 2, sx * xc + T / 2
        for xf, nx in ((x0, -1.0), (x1, 1.0)):                                                  # triangles, jamais en miroir
            fu = (lambda z: (B / 2 - z) / B) if nx > 0 else (lambda z: (z + B / 2) / B)
            UVt = [(rt[0] + (rt[2] - rt[0]) * fu(z), rt[1] + (rt[3] - rt[1]) * y / Ht) for z, y in ((-B / 2, 0), (B / 2, 0), (0, Ht))]
            _face(m, [(xf, 0, -B / 2), (xf, 0, B / 2), (xf, Ht, 0)], UVt, [(nx, 0, 0)] * 3)
        for zf, nz in ((-B / 2, -1.0), (B / 2, 1.0)):                                           # pentes, logo le long
            n = (0, B / 2, nz * Ht); lo_, hi_ = (rs[2], rs[0]) if nz < 0 else (rs[0], rs[2])
            _face(m, [(x0, 0, zf), (x1, 0, zf), (x1, Ht, 0), (x0, Ht, 0)], [(lo_, rs[1]), (hi_, rs[1]), (hi_, rs[3]), (lo_, rs[3])], [n] * 4)
        m.box((x0 - 0.06, 0, -B / 2 - 0.15), (x1 + 0.06, a['skirt'], B / 2 + 0.15), rsk, 'xXzZ')   # jupe noire au pied
        xm = sx * xc; y0c = Ht - 0.3                                                            # colonne pleine hauteur
        m.box((xm - ct / 2, y0c, -cw / 2), (xm + ct / 2, top, cw / 2), ry, 'xXzZY', {'x': rcs, 'X': rcs, 'z': rcf, 'Z': rcf})
    m.box((-xc + ct / 2, top - bh, -bd / 2), (xc - ct / 2, top, bd / 2), rk, 'zZYy', {'z': rb, 'Z': rb, 'Y': ry, 'y': ry})
    if drop:
        m.V = [[v[0], v[1] - drop] + list(v[2:]) for v in m.V]
    m.write(os.path.join(out, 'arche_50f.jm'), MAT_MAT)
    sph = [(sx * xc, 1.2 - drop, dz) for sx in (-1, 1) for dz in (-2.3, 0.0, 2.3)] + [(sx * xc, 3.2 - drop, 0) for sx in (-1, 1)]
    K.shp(os.path.join(out, 'arche_50f.shp'), sph, 1.3)
    return 'arche_50f.jm', 'arche_50f.png', 'arche_50f.shp'


# ================================================================ v23c : murs droits (review en jeu de la v23b)
# « les filets sur la fin du virage, alors que c'est sur l'entrée qu'il faut les mettre » ; « jamais tordu, pas de vague : une botte de
# foin ne fait pas de vague ; enterré sous la terre, des trucs droits, angles droits, tout à la même hauteur » ; « petits bugs de
# triangle sur les incrustations dans la terre » (bouts mal fermés) ; « pas de bâche sur les côtés des 3 boudins : qu'on voie que ce
# sont 3 boudins » ; « la couleur du logo que je t'ai envoyé » (fond + logo du sponsor, sponsors.py).
# Chaque module de 10 ft = un bloc DROIT (corde de l'arc), dessus à la même hauteur sur tout le mur (VIS ft au-dessus de la plus haute
# crête du berm), bas enterré ; fagot de 3 boudins noirs (bouts visibles) sous une bâche aux couleurs du sponsor ; filet droit par module.
WALL23 = dict(vis=0.5, depth=1.0, n90=3, n180=4, entry=0.02)   # v23e (« le mur est trop haut : le boudin au sommet de l'appui touche presque la terre, un petit peu de gris ») : 1,6 -> 0,5 ft
# v23e (« un peu plus vers le milieu du virage ; enlève le 1er bloc et mets-le de l'autre côté ») : décalage du mur en modules, par virage
WALL_SHIFT = {'T_L5a': 1, 'T_Bb': 1, 'T_D ': 0, 'T1 1': 2, 'T_TR': 1, 'T_E ': 1, 'T_C ': 3}
# v23f (« rajoute un filet Automoto à gauche » ; « Honda : rajoute-en un vers la droite, qu'ils finissent plus tard » ; « FIVE : un de plus vers la
# sortie ») : nombre de modules par virage (T_D : un de plus au début -> décalage 1 -> 0)
WALL_NMOD = {'T_D ': 5, 'T1 1': 5, 'T_C ': 5}
TURN_SPONSOR.update({'T_Bb': 'mxsim', 'T_Ba': 'mxsim'})


def bundle_texture_v23(out, key, Lm=9.3):
    """bâche du fagot : fond = couleur du sponsor, logo côté piste (v 0,10 - 0,44) ; bande noire en haut de l'image (v > 0,975) pour les
    bouts des 3 boudins."""
    import sponsors as SP
    # v25e (« les logos tout flous, bizarres avant qu'on soit collé ») : texture aux proportions du fagot (pas carrée : le logo était étiré
    # dans un sens, flou de loin), 1024 x 512
    bg, lg = SP.panel(key); P = float(np.sum(np.hypot(*np.diff(_tri_section(AIRF['rb'])[:, :2], axis=0).T))); W, H = 1024, 512
    from scipy.ndimage import gaussian_filter
    rng = np.random.default_rng(7); n = gaussian_filter(rng.normal(0, 1, (H, W)), (40, 6)); n /= n.std()
    a = np.asarray(bg, float)[None, None, :] * (1 + 0.035 * n[..., None]); im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if lg is not None:
        l2 = lg.resize((lg.size[0], max(1, int(lg.size[1] * (Lm / W) / (P / H)))), Image.LANCZOS)
        fit(im, l2, (int(W * 0.10), int(H * (1 - 0.44)), int(W * 0.90), int(H * (1 - 0.10))), 0.05)
    ImageDraw.Draw(im).rectangle([0, 0, W, int(H * 0.02)], fill=(150, 150, 148))   # v23e : intérieur des boudins gris ; v23f : plus foncé
    fn = 'fagot23_%s.png' % (key or 'noir'); _save(im, os.path.join(out, fn)); return fn


def turn_wall_v23(out, k, g, Hf, key):
    """mur droit à l'entrée du virage g (3 modules pour un 90°, 4 pour un 180°) ; origine du modèle : centre du virage, lacet 0."""
    sg = 1.0 if g['ang'] > 0 else -1.0; th_in = g['t0'] + sg * np.pi / 2; ang = np.radians(g['ang']); th = lambda f: th_in - ang * f
    cx, cz = g['cx'], g['cz']; h0 = float(np.ravel(Hf(cx, cz))[0]); H1 = lambda x, z: float(np.ravel(Hf(x, z))[0])
    f_a = g.get('berm_from', 0.0) + WALL23['entry']; nmod = WALL23['n180'] if abs(g['ang']) > 100 else WALL23['n90']
    sh_ = next((v for k_, v in WALL_SHIFT.items() if g['tag'].startswith(k_)), 0)
    nmod = next((v for k_, v in WALL_NMOD.items() if g['tag'].startswith(k_)), nmod)
    tm = th(f_a + 0.15); rr = np.arange(g['r'], g['r'] + 40, 0.5)
    r_crest = float(rr[int(np.argmax(Hf(cx + np.cos(tm) * rr, cz + np.sin(tm) * rr)))])
    W = BLK['W']; rc = r_crest + BLK['back'] + W / 2; df = AIRF['mod'] / (abs(ang) * rc); f_a += sh_ * df
    f_b = min(1.0, f_a + nmod * df); f_a = f_b - nmod * df
    P2 = lambda f, r_: np.array([np.cos(th(f)) * r_, np.sin(th(f)) * r_])
    fs = f_a + df * np.arange(nmod + 1); hc = []
    for f in np.linspace(f_a, f_b, 4 * nmod + 1):
        e = np.array([np.cos(th(f)), np.sin(th(f))]); rr_ = r_crest + np.linspace(-4, 4, 9); hc.append(float(np.max(Hf(cx + e[0] * rr_, cz + e[1] * rr_))))
    ytop = max(hc) + WALL23['vis'] - h0                                         # même hauteur sur tout le mur
    m = Mesh(); a2 = Mesh(); n2 = Mesh(); rb = AIRF['rb']; dcen = -W / 2 + 2 * rb + 0.15; sec_b = _tri_section(rb, 30)
    Vb, Vt = NT_['v']; TL = 4.0; sph_w, sph_a, sph_n = [], [], []; dot = lambda u: (u[0], u[1], u[0] + 0.0005, u[1] + 0.0005)
    net_top = ytop - 0.15 + rb * (2 + np.sqrt(3)) + NETV['above']
    for q in range(nmod):
        A, B = P2(fs[q], rc), P2(fs[q + 1], rc); L = float(np.linalg.norm(B - A)); t = (B - A) / L; nn = np.array([-t[1], t[0]])
        if np.dot(nn, (A + B) / 2) < 0:
            nn = -nn                                                            # nn : vers l'extérieur du virage
        right = np.array([-nn[1], nn[0]]); rev = np.dot(t, right) < 0          # vu de la piste (regard vers l'extérieur)
        A = A - t * 0.04; B = B + t * 0.04; L += 0.08
        gnd = min(H1(cx + p_[0], cz + p_[1]) for s_ in np.linspace(0, 1, 5) for w_ in (-W / 2, 0, W / 2) for p_ in [A + (B - A) * s_ + nn * w_]) - h0
        yb = gnd - WALL23['depth']
        # --- bloc de paille : section rectangulaire à arêtes du dessus arrondies, balayée sur la corde ; bouts fermés
        sec = [(-W / 2, yb)] + [(-W / 2 + BLK['rnd'] - BLK['rnd'] * np.cos(a_), ytop - BLK['rnd'] + BLK['rnd'] * np.sin(a_)) for a_ in np.linspace(0, np.pi / 2, 5)]
        sec += [(W / 2 - BLK['rnd'] + BLK['rnd'] * np.cos(a_), ytop - BLK['rnd'] + BLK['rnd'] * np.sin(a_)) for a_ in np.linspace(np.pi / 2, 0, 5)] + [(W / 2, yb)]
        sec = np.array(sec); tg_ = np.gradient(sec, axis=0); nr = np.c_[-tg_[:, 1], tg_[:, 0]]; nr /= np.linalg.norm(nr, axis=1, keepdims=True)
        if nr[len(sec) // 2, 1] < 0:
            nr = -nr
        sl_ = np.r_[0, np.cumsum(np.hypot(*np.diff(sec, axis=0).T))]
        V3 = lambda p, d, y: (p[0] + nn[0] * d, y, p[1] + nn[1] * d)
        for j in range(len(sec) - 1):
            Q = [V3(A, *sec[j]), V3(B, *sec[j]), V3(B, *sec[j + 1]), V3(A, *sec[j + 1])]
            N_ = [(nn[0] * nr[j][0], nr[j][1], nn[1] * nr[j][0])] * 2 + [(nn[0] * nr[j + 1][0], nr[j + 1][1], nn[1] * nr[j + 1][0])] * 2
            _face(m, Q, [(0, sl_[j] / 9), (L / 8, sl_[j] / 9), (L / 8, sl_[j + 1] / 9), (0, sl_[j + 1] / 9)], N_)
        for P_, sgn in ((A, -1), (B, 1)):                                       # bouts : polygone convexe fermé
            pts = [V3(P_, *p) for p in sec]; cen = np.mean(pts, axis=0); nrm = (t[0] * sgn, 0.0, t[1] * sgn)
            for j in range(len(pts)):
                _face(m, [cen, pts[j], pts[(j + 1) % len(pts)]], [(0.3, 0.5), (0.3 + 0.01 * j, 0.1), (0.31 + 0.01 * j, 0.1)], [nrm] * 3)
        for s_ in (0.25, 0.75):
            c_ = A + (B - A) * s_; sph_w.append((c_[0], ytop - 1.2, c_[1]))
        # --- fagot : bâche (sans bouts) + 3 boudins noirs dont on voit les bouts
        yb2 = ytop - 0.15; A2, B2 = A + t * 0.45, B - t * 0.45
        for j in range(len(sec_b) - 1):
            (d0, y0, nd0, ny0), (d1, y1, nd1, ny1) = sec_b[j], sec_b[j + 1]; v0, v1 = 0.975 * j / (len(sec_b) - 1), 0.975 * (j + 1) / (len(sec_b) - 1)
            u0_, u1_ = (1.0, 0.0) if rev else (0.0, 1.0)
            Q = [V3(A2, dcen + d0, yb2 + y0), V3(B2, dcen + d0, yb2 + y0), V3(B2, dcen + d1, yb2 + y1), V3(A2, dcen + d1, yb2 + y1)]
            N_ = [(nn[0] * nd0, ny0, nn[1] * nd0)] * 2 + [(nn[0] * nd1, ny1, nn[1] * nd1)] * 2
            _face(a2, Q, [(u0_, v0), (u1_, v0), (u1_, v1), (u0_, v1)], N_)
        for d_, y_ in ((-rb, rb), (rb, rb), (0.0, rb * (1 + np.sqrt(3)))):   # v23e : coupés pile au ras de la bâche, gris clair
            a3 = V3(A2, dcen + d_, yb2 + y_); b3 = V3(B2, dcen + d_, yb2 + y_)
            # v23f (« les boudins : la couleur de la bâche sur leur extérieur, l'intérieur gris, un peu plus foncé ») : tour = fond du sponsor
            # (coin bas de l'image, sans logo), bouts = disques gris
            a2.tube(a3, b3, rb * 0.97, (0.02, 0.02, 0.05, 0.05), 14, caps=False)
            ax_ = np.subtract(b3, a3); ax_ = ax_ / np.linalg.norm(ax_); s1 = np.cross(ax_, [0, 1, 0]); s1 /= np.linalg.norm(s1); s2 = np.cross(ax_, s1)
            for cen_, sg_ in ((np.asarray(a3), -1), (np.asarray(b3), 1)):
                ring_ = [cen_ + (np.cos(t_) * s1 + np.sin(t_) * s2) * rb * 0.97 for t_ in np.linspace(0, 2 * np.pi, 15)]
                for j_ in range(14):
                    _face(a2, [cen_, ring_[j_], ring_[j_ + 1]], [(0.5, 0.993)] * 3, [tuple(ax_ * sg_)] * 3)
        for s_ in np.arange(0.5, L, 2.0):
            c_ = A + t * s_; sph_a.append((c_[0] + nn[0] * dcen, yb2 + rb * 1.3, c_[1] + nn[1] * dcen))
        # --- filet droit sur le bord arrière du bloc, tuiles de 4 ft
        An, Bn = A + nn * (W / 2 - NETV['off']), B + nn * (W / 2 - NETV['off']); cuts = list(np.arange(0, L, TL)) + [L]
        for sa, sb in zip(cuts[:-1], cuts[1:]):
            pa, pb = An + t * sa, An + t * sb; ua, ub = (sa % TL) / TL, (sa % TL + (sb - sa)) / TL
            Q = [(pa[0], ytop - 0.2, pa[1]), (pb[0], ytop - 0.2, pb[1]), (pb[0], net_top, pb[1]), (pa[0], net_top, pa[1])]
            UV = [(ua, Vb), (ub, Vb), (ub, Vt), (ua, Vt)]; e3 = (nn[0], 0, nn[1])
            _face(n2, Q, UV, [tuple(-np.array(e3))] * 4); _face(n2, Q, UV, [e3] * 4)
        for s_ in np.arange(1.0, L, 2.0):
            c_ = An + t * s_; sph_n += [(c_[0], ytop + h_, c_[1]) for h_ in (1.5, 3.0, 4.5)]
    for qi in range(nmod + 1):                                                  # poteaux aux raccords + mousses
        f = fs[qi]; p_ = P2(f, rc); e_ = p_ / np.linalg.norm(p_); pp = p_ + e_ * (W / 2 - NETV['off'] + 0.12)
        if qi in (0, nmod):                                                     # v23e : poteau du bout sur le bloc, pas dans le vide
            t_in = P2(fs[1 if qi == 0 else nmod - 1], rc) - p_; pp = pp + t_in / np.linalg.norm(t_in) * 0.9
        yb_ = ytop - 0.2; yt_ = net_top + 0.35
        n2.tube((pp[0], yb_, pp[1]), (pp[0], yt_, pp[1]), NETV['pole_r'], dot(NT_['red']), 8)
        n2.tube((pp[0], yt_, pp[1]), (pp[0], yt_ + NETV['cap'], pp[1]), NETV['pole_r'] * 1.25, dot(NT_['yel']), 8)
        if qi in (0, nmod):
            tg2 = np.array([-e_[1], e_[0]]); w2, d2 = NETV['epad']
            _obox(n2, (pp[0] - e_[0] * (d2 / 2 - 0.1), pp[1] - e_[1] * (d2 / 2 - 0.1)), tg2, e_, w2, d2, ytop - 0.05, ytop + NETV['epad_h'], NT_['blk'])
        else:
            n2.tube((pp[0], ytop - 0.05, pp[1]), (pp[0], ytop + NETV['pad_h'], pp[1]), NETV['pad_r'], dot(NT_['blk']), 10)
    m.write(os.path.join(out, 'mur_virage_%d.jm' % k), MAT_BACHE); K.shp(os.path.join(out, 'mur_virage_%d.shp' % k), sph_w, 2.2)
    a2.write(os.path.join(out, 'air_virage_%d.jm' % k), MAT_BACHE); K.shp(os.path.join(out, 'air_virage_%d.shp' % k), sph_a, 1.1, par=(0.6, 150, 8))
    n2.write(os.path.join(out, 'filet_virage_%d.jm' % k), MAT_MAT); K.shp(os.path.join(out, 'filet_virage_%d.shp' % k), sph_n, 0.9, par=(1.0, 85, 4))
    return dict(modules=nmod, f=(round(f_a, 3), round(f_b, 3)), top=round(ytop + h0, 2),
                files=(('mur_virage_%d.jm' % k, 'bache_paille.png', 'mur_virage_%d.shp' % k),
                       ('air_virage_%d.jm' % k, bundle_texture_v23(out, key), 'air_virage_%d.shp' % k),
                       ('filet_virage_%d.jm' % k, NT_['png'], 'filet_virage_%d.shp' % k)))


NT_ = {}


def pylon_skin(out, sgm_statue, key):
    """v23c (« les trucs gonflables aux intérieurs de virage ») : poteau rond de Saint-Georges aux couleurs du sponsor du virage."""
    import sponsors as SP
    bg, lg = SP.panel(key); im = Image.open(os.path.join(sgm_statue, 'pylon_round.png')).convert('RGB'); d = ImageDraw.Draw(im)
    if key == 'motoverte' and lg is not None:                                # v25 (« pas le MV, juste le moto verte ») : le texte seul
        c_ = lg.crop((int(0.30 * lg.size[0]), 0, lg.size[0], lg.size[1])); lg = c_.crop(c_.getbbox())
    d.rectangle([0, 0, 1024, 928], fill=bg)
    if lg is not None:
        for cx in (256, 768):
            fit(im, lg, (cx - 95, 30, cx + 95, 680), 0.0, rot=90)   # v23e : centré sur le corps gonflable (pas le socle)
    im = K.shade_v(im, (0, 0, 1024, 928), 1.0, 0.82); fn = 'pylone23_%s.png' % (key or 'noir'); _save(im, os.path.join(out, fn)); return fn


def drape_tarp(out, name, Hf, g, ua, ub, side, key, step=0.6, nv=18, lift=0.3):
    """v23c (« fais les bords de la bosse Milwaukee en Milwaukee » ; « la plaque AMV sur les bords de la réception du freestyle, un
    rectangle comme le Milwaukee ») : bâche drapée sur le flanc d'un saut (side -1 = gauche, +1 = droite du sens de course), de u = ua à
    ub ; elle suit le terrain construit du haut du flanc (h < 0,92 h de l'axe) au pied (h < 0,25 ft), 0,08 ft au-dessus ; jupe noire
    en bas ; logo du sponsor projeté à plat (lisible de côté, jamais en miroir). Renvoie la ligne de statue (origine au sol à côté)."""
    import sponsors as SP
    c, s_ = np.cos(g['t']), np.sin(g['t']); nrm = np.array([-s_, c]) * side; H1 = lambda p: float(np.ravel(Hf(p[0], p[1]))[0])
    base = lambda u: np.array([g['x0'] + u * c, g['z0'] + u * s_])
    us = np.arange(ua, ub + 1e-6, step); vv = np.arange(0, 70, 0.5); cols = []
    for u in us:
        hs = np.array([H1(base(u) + nrm * v) for v in vv]); hc = hs[0]
        if hc < 0.6:
            cols.append(None); continue
        vt = vv[int(np.argmax(hs < 0.92 * hc))]; vf = vv[int(np.argmax(hs < 0.25))]; cols.append((max(0.0, vt - 0.5), vf + 0.5))
    ok = [i for i, cl in enumerate(cols) if cl]; us = us[ok[0]:ok[-1] + 1]; cols = cols[ok[0]:ok[-1] + 1]
    cols = [cl if cl else cols[i - 1] for i, cl in enumerate(cols)]
    vfm = max(cl[1] for cl in cols); um = (us[0] + us[-1]) / 2; O = base(um) + nrm * (vfm + 4.0); h_o = H1(O)
    pts = [[(base(u) + nrm * v) for v in np.linspace(cl[0], cl[1], nv)] for u, cl in zip(us, cols)]
    Y = [[H1(p) for p in row] for row in pts]; hmax = max(max(r) for r in Y) - h_o
    L = us[-1] - us[0]; W, H = 2048, 512; bg, lg = SP.panel(key); im = Image.new('RGB', (W, H), bg)
    if lg is not None:
        l2 = lg.resize((lg.size[0], max(1, int(lg.size[1] * (H / hmax) / (W / L)))), Image.LANCZOS)
        fit(im, l2, (int(0.18 * W), int(0.22 * H), int(0.82 * W), int(0.78 * H)), 0.02)
    ImageDraw.Draw(im).rectangle([0, int(H * 0.90), W, H], fill=(16, 16, 18)); im = K.grain(im, 1.2); png = name + '.png'; _save(im, os.path.join(out, png))
    m = Mesh(); fu = (lambda u: (u - us[0]) / L) if side > 0 else (lambda u: 1 - (u - us[0]) / L)
    V = lambda i, j: (pts[i][j][0] - O[0], Y[i][j] - h_o + lift, pts[i][j][1] - O[1])
    UV = lambda i, j: (fu(us[i]), float(np.clip((Y[i][j] - h_o) / hmax, 0, 1)))
    for i in range(len(us) - 1):
        for j in range(nv - 1):
            q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            P_ = [V(*k) for k in q]; U_ = [UV(*k) for k in q]
            m.tri([P_[0], P_[1], P_[2]], [U_[0], U_[1], U_[2]]); m.tri([P_[0], P_[2], P_[3]], [U_[0], U_[2], U_[3]])
            m.tri([P_[0], P_[2], P_[1]], [U_[0], U_[2], U_[1]]); m.tri([P_[0], P_[3], P_[2]], [U_[0], U_[3], U_[2]])
    m.write(os.path.join(out, name + '.jm'), MAT_BACHE)
    return O, name + '.jm', png


# ================================================================ v23d : panneaux « carton » le long des sauts (objets 3D, pas de la couleur sur la terre)
# « pas mettre de la couleur sur la bosse, mais un genre de carton qui se met autour de la bosse, un truc 3D, un modèle ; pareil pour le
# Milwaukee : le logo pas centré et ça fait pas effet carton ; que ça fasse un objet, un peu comme le truc 50 Factory » + photo de côté
# de la réception du freestyle à Paris (triangle mascotte / grand panneau blanc AMV au centre / triangle mascotte + AMV.FR).
def _profile_along(Hf, g, ua, ub, step=0.25):
    c, s_ = np.cos(g['t']), np.sin(g['t']); us = np.arange(ua, ub + 1e-6, step)
    hc = np.array([float(np.ravel(Hf(g['x0'] + u * c, g['z0'] + u * s_))[0]) for u in us]); return us, hc


def board_v23(out, name, Hf, g, ua, ub, side, kind, lift=None, head=3.5, th=0.25):
    """panneau vertical droit au pied du flanc (côté side), silhouette = profil du saut sur l'axe (+ lift) ; kind 'milwaukee' ou 'amv'
    (AMV : le panneau du centre, au-dessus du plat, dépasse de head ft). Texture : u le long du saut, v = hauteur (logo jamais en miroir)."""
    lift = lift if lift is not None else (2.5 if kind == 'amv' else 0.35)   # v23e (« ça fait presque des barrières, ça remonte plus haut sur le sommet »)
    c, s_ = np.cos(g['t']), np.sin(g['t']); nrm = np.array([-s_, c]) * side; tg = np.array([c, s_])
    H1 = lambda p: float(np.ravel(Hf(p[0], p[1]))[0]); base = lambda u: np.array([g['x0'] + u * c, g['z0'] + u * s_])
    us, hc = _profile_along(Hf, g, ua, ub); h0 = float(np.min(hc)); k = hc > h0 + 0.4; us, hc = us[k], hc[k]
    um = us[int(np.argmax(hc))]; vv = np.arange(0, 80, 0.5); hs = np.array([H1(base(um) + nrm * v) for v in vv])
    vb = float(vv[int(np.argmax(hs < h0 + 0.12 * (hc.max() - h0)))]) - 0.5           # pied du flanc
    top_ = np.nonzero(hc >= hc.max() - (3.5 if kind == 'amv' else 0.6))[0]; ua_t, ub_t = us[top_[0]], us[top_[-1]]   # le plat (AMV : panneau du centre plus large)
    ext = np.where((us >= ua_t) & (us <= ub_t), head, 0.0) if kind == 'amv' else np.zeros_like(us)
    O = base(um) + nrm * (vb + 4.0); h_o = H1(O); yt = hc - h_o + lift + ext
    if kind == 'amv':                                                                   # panneau du centre : haut plat (rectangle)
        yt = np.where(ext > 0, float(hc.max()) - h_o + lift + head, yt)
    ymax = float(yt.max()); L = us[-1] - us[0]
    yb = np.array([H1(base(u) + nrm * vb) for u in us]) - h_o - 0.6
    W, Ht = 2048, 1024; px_u, px_v = W / L, Ht / ymax; U = lambda u: (u - us[0]) / L
    sil = [(int(U(u) * W), int(Ht - y * px_v)) for u, y in zip(us, yt)]
    im = _board_texture(kind, W, Ht, sil, U(ua_t), U(ub_t), px_u, px_v, ymax); png = name + '.png'; _save(im, os.path.join(out, png))
    m = Mesh(); fu = (lambda u: U(u)) if side > 0 else (lambda u: 1 - U(u)); fv = lambda y: float(np.clip(y / ymax, 0, 1))
    P = lambda u, d, y: tuple(np.r_[base(u) + nrm * (vb + d) - O][[0]].tolist() + [y] + (base(u) + nrm * (vb + d) - O)[[1]].tolist())
    blk = (0.001, 0.001)
    for i in range(len(us) - 1):
        u0_, u1_ = us[i], us[i + 1]
        out_ = [P(u0_, th / 2, yb[i]), P(u1_, th / 2, yb[i + 1]), P(u1_, th / 2, yt[i + 1]), P(u0_, th / 2, yt[i])]
        uvo = [(fu(u0_), fv(yb[i])), (fu(u1_), fv(yb[i + 1])), (fu(u1_), fv(yt[i + 1])), (fu(u0_), fv(yt[i]))]
        n_o = tuple(np.r_[nrm[0], 0, nrm[1]]); n_i = tuple(-np.r_[nrm[0], 0, nrm[1]])
        _face(m, out_, uvo, [n_o] * 4)                                                  # face extérieure (logo)
        in_ = [P(u0_, -th / 2, yb[i]), P(u1_, -th / 2, yb[i + 1]), P(u1_, -th / 2, yt[i + 1]), P(u0_, -th / 2, yt[i])]
        _face(m, in_, uvo, [n_i] * 4)                                                   # face intérieure (même dessin, vue de la piste)
        _face(m, [P(u0_, -th / 2, yt[i]), P(u1_, -th / 2, yt[i + 1]), P(u1_, th / 2, yt[i + 1]), P(u0_, th / 2, yt[i])], [blk] * 4, [(0, 1, 0)] * 4)
    for i, sg in ((0, -1), (len(us) - 1, 1)):                                           # tranches des bouts
        u_ = us[i]; n3 = (tg[0] * sg, 0, tg[1] * sg)
        _face(m, [P(u_, -th / 2, yb[i]), P(u_, th / 2, yb[i]), P(u_, th / 2, yt[i]), P(u_, -th / 2, yt[i])], [blk] * 4, [n3] * 4)
    m.write(os.path.join(out, name + '.jm'), MAT_MAT)
    K.shp(os.path.join(out, name + '.shp'), [tuple(np.r_[(base(u) + nrm * vb - O)[0], 2.0, (base(u) + nrm * vb - O)[1]]) for u in us[::12]], 1.0)
    return O, name + '.jm', png, name + '.shp'


def _board_texture(kind, W, H, sil, ua_t, ub_t, px_u, px_v, ymax):
    """dessin du panneau (silhouette sil en pixels) ; coin (0,0)-(4,4) noir pour les tranches."""
    import sponsors as SP
    from PIL import ImageFont
    yat = lambda x: min(H, max(0, int(np.interp(x, [p[0] for p in sil], [p[1] for p in sil]))))   # haut du panneau à la colonne x
    if kind == 'milwaukee':
        bg, lg = SP.panel('milwaukee'); im = Image.new('RGB', (W, H), bg); d = ImageDraw.Draw(im)
        xa, xb = int(ua_t * W), int(ub_t * W); xm = (xa + xb) // 2; ytop = max(yat(xa), yat(xb)); half = int(0.30 * W)
        l2 = lg.resize((lg.size[0], max(1, int(lg.size[1] * px_v / px_u))), Image.LANCZOS)
        fit(im, l2, (xm - half, ytop + int(0.12 * (H - ytop)), xm + half, H - int(0.30 * (H - ytop))), 0.04)
        d.rectangle([0, H - int(1.2 * px_v), W, H], fill=(16, 16, 18))                  # jupe noire
    else:
        G_ = (0, 166, 81); WH = (250, 250, 248); im = Image.new('RGB', (W, H), G_); d = ImageDraw.Draw(im)
        src = Image.open(os.path.join(SP.U, SP.FILES['amv'])).convert('RGBA')
        girl, boy, bubble = src.crop((130, 200, 300, 440)), src.crop((490, 200, 680, 440)), src.crop((140, 0, 670, 380))
        xa, xb = int(ua_t * W), int(ub_t * W); yt_c = yat((xa + xb) // 2)
        d.rectangle([xa, 0, xb, H], fill=WH)                                             # grand panneau blanc du centre
        for x0, x1, flip in ((0, xa, False), (xb, W, True)):                             # triangles : blanc en diagonale, bord vert
            d.polygon([(x0, H), (x1, H), (x1 if not flip else x0, yat(x1 - 2) if not flip else yat(x0 + 2))], fill=WH)
        fh = ImageFont.truetype('C:/Windows/Fonts/ariblk.ttf', max(16, int(min(1.6 * px_v, (xb - xa) / 3 / 2.4))))
        hb = int(3.2 * px_v)                                                             # bandeau « AMV AMV AMV » (dépasse du plat)
        d.rectangle([xa, yt_c, xb, yt_c + hb], fill=WH); d.rectangle([xa, yt_c + hb, xb, yt_c + hb + 6], fill=G_)
        for k_ in range(3):
            cx_ = xa + (xb - xa) * (k_ + 0.5) / 3; d.text((cx_, yt_c + int(0.62 * hb)), 'AMV', font=fh, fill=G_, anchor='mm')
        sq = lambda img: img.resize((img.size[0], max(1, int(img.size[1] * px_v / px_u))), Image.LANCZOS)
        fit(im, sq(src.crop((150, 0, 660, 370))), (xa + 14, yt_c + hb + 16, xb - 14, H - int(1.4 * px_v)), 0.0)   # la bulle (AMV + texte), au centre, en grand
        hl = H - yat(int(xa * 0.70)); fit(im, sq(girl), (int(xa * 0.30), H - int(0.98 * hl), xa - 10, H - 8), 0.0)
        hr = H - yat(int(xb + (W - xb) * 0.30)); fit(im, sq(boy), (xb + 10, H - int(0.98 * hr), xb + int((W - xb) * 0.62), H - 8), 0.0)
        ft = ImageFont.truetype('C:/Windows/Fonts/ariblk.ttf', max(20, int(2.2 * px_v)))
        d.text((xb + int((W - xb) * 0.58), H - int(1.6 * px_v)), 'AMV.FR', font=ft, fill=G_, anchor='lm')
        d.text((int(xa * 0.05), H - int(1.2 * px_v)), 'AMV', font=fh, fill=G_, anchor='lm')
        bw = max(6, int(0.9 * px_v))                                                     # liserés verts (bord du haut, bas, panneau du centre)
        for x in range(0, W, 4):
            y_ = yat(x); d.rectangle([x, y_, x + 4, y_ + bw], fill=G_)
        d.rectangle([0, H - bw, W, H], fill=G_); d.rectangle([xa - 6, yt_c, xa + 6, H], fill=G_); d.rectangle([xb - 6, yt_c, xb + 6, H], fill=G_)
        fs_ = ImageFont.truetype('C:/Windows/Fonts/ariblk.ttf', max(14, int(0.9 * px_v)))   # v23e : petits AMV le long de la barrière du haut
        for x in list(range(int(0.04 * W), xa - 60, int(7 * px_u))) + list(range(xb + 60, int(0.96 * W), int(7 * px_u))):
            d.text((x, yat(x) + bw + int(0.8 * px_v)), 'AMV', font=fs_, fill=G_, anchor='mm')
    d.rectangle([0, 0, 4, 4], fill=(16, 16, 18)); return K.grain(im, 1.0)


# ================================================================ v24 : panneaux d'après les dessins de l'utilisateur (contours tracés sur les vues de côté)
# Milwaukee : « ça monte droit un peu après l'appel, un plateau sur le dessus à la hauteur du truc, avec les 2 ballots dessus, la descente ; le
# logo centré par rapport à la forme » ; AMV : « suis les traits verts ; le design AMV avec les traits blancs ; le dessus : la barrière AMV
# blanche, plusieurs AMV de la taille d'une banderole, comme les sponsors autour du stade ».
import layout_paris as _LP                                                          # noqa: E402
BOARD_POLY = _LP.BOARD_POLY                                                         # u (ft depuis la sortie du virage), hauteur (ft)
AMV_BARRIER = (163.8, 184.0, 23.4, 27.1)


def board_v24(out, name, Hf, g, side, kind, th=None):
    """panneau plan vertical au pied du flanc, contour = polygone dessiné par l'utilisateur (+ barrière AMV) ; deux faces + tranches."""
    c, s_ = np.cos(g['t']), np.sin(g['t']); nrm = np.array([-s_, c]) * side; tg = np.array([c, s_])
    H1 = lambda p: float(np.ravel(Hf(p[0], p[1]))[0]); base = lambda u: np.array([g['x0'] + u * c, g['z0'] + u * s_])
    th = th or _LP.BOARD_TH; poly = BOARD_POLY[kind]; ua, ub = poly[0][0], poly[-1][0]; um = (ua + ub) / 2
    vb = _LP.BOARD_VB[kind]; h0 = H1(base(um) + nrm * (vb + 12.0))                     # v24b : au bord du dessus du saut (flanc enlevé derrière)
    O = base(um) + nrm * (vb + 4.0); h_o = H1(O)
    shapes = [poly] + ([[(AMV_BARRIER[0], AMV_BARRIER[2]), (AMV_BARRIER[1], AMV_BARRIER[2]), (AMV_BARRIER[1], AMV_BARRIER[3]), (AMV_BARRIER[0], AMV_BARRIER[3])]]
                       if kind == 'amv' else [])
    ymax = max(y for sh in shapes for _, y in sh); L = ub - ua; W = 2048; Ht = int(min(2048, max(256, round(W * ymax / L / 64) * 64)))
    px_u, px_v = W / L, Ht / ymax
    im = _board_texture_v24(kind, W, Ht, px_u, px_v, ua, ymax); png = name + '.png'; _save(im, os.path.join(out, png))
    m = Mesh(); fu = (lambda u: (u - ua) / L) if side > 0 else (lambda u: 1 - (u - ua) / L); fv = lambda y: y / ymax
    P = lambda u, d, y: (base(u)[0] + nrm[0] * (vb + d) - O[0], y + (h0 - h_o) - (0.6 if y < 0.01 else 0.0), base(u)[1] + nrm[1] * (vb + d) - O[1])   # bas enfoncé de 0,6 ft
    n_o = (nrm[0], 0.0, nrm[1]); n_i = (-nrm[0], 0.0, -nrm[1]); blk = (0.001, 0.999)
    for sh in shapes:
        for k in range(1, len(sh) - 1):                                                 # convexe : éventail
            tri = [sh[0], sh[k], sh[k + 1]]
            # v25 (« des deux côtés dans le bon sens : AMV et pas AVMA à l'intérieur ») : la face intérieure a le dessin retourné en u
            _face(m, [P(u, th / 2, y) for u, y in tri], [(fu(u), fv(y)) for u, y in tri], [n_o] * 3)
            _face(m, [P(u, -th / 2, y) for u, y in tri], [(1 - fu(u), fv(y)) for u, y in tri], [n_i] * 3)
        for k in range(len(sh)):                                                        # tranches
            (u0_, y0_), (u1_, y1_) = sh[k], sh[(k + 1) % len(sh)]
            e_ = np.array([u1_ - u0_, y1_ - y0_]); nn_ = np.array([e_[1], -e_[0]]) / (np.linalg.norm(e_) or 1)
            n3 = (tg[0] * nn_[0], nn_[1], tg[1] * nn_[0])
            _face(m, [P(u0_, -th / 2, y0_), P(u1_, -th / 2, y1_), P(u1_, th / 2, y1_), P(u0_, th / 2, y0_)], [blk] * 4, [n3] * 4)
    m.write(os.path.join(out, name + '.jm'), MAT_MAT)
    K.shp(os.path.join(out, name + '.shp'), [P(u, 0, 2.0) for u in np.arange(ua + 2, ub - 1, 3.0)], 1.0)
    return O, name + '.jm', png, name + '.shp'


def _board_texture_v24(kind, W, H, px_u, px_v, ua, ymax):
    import sponsors as SP
    from PIL import ImageFont
    X = lambda u: int((u - ua) * px_u); Y = lambda y: int(H - y * px_v)
    poly = [(X(u), Y(y)) for u, y in BOARD_POLY[kind]]
    if kind == 'milwaukee':
        bg, lg = SP.panel('milwaukee'); im = Image.new('RGB', (W, H), bg); d = ImageDraw.Draw(im)
        l2 = lg.resize((lg.size[0], max(1, int(lg.size[1] * px_v / px_u))), Image.LANCZOS)
        (u0, _), (u1, yt), (u2, _), (u3, _) = BOARD_POLY['milwaukee']; ucx = (u0 + u1 + u2 + u3) / 4      # centre de la forme
        fit(im, l2, (X(ucx - 0.19 * (u3 - u0)), Y(0.64 * yt), X(ucx + 0.19 * (u3 - u0)), Y(0.24 * yt)), 0.02)   # v24b : logo un peu plus petit
        d.rectangle([0, Y(2.3), W, H], fill=(16, 16, 18))                               # v24b : noir du sol jusqu'à la forme rouge
    else:
        G_ = (0, 158, 79); WH = (250, 250, 248); im = Image.new('RGB', (W, H), WH); d = ImageDraw.Draw(im)
        (u0, _), (u1, yt), (u2, _), (u3, _) = BOARD_POLY['amv']; bw = max(6, int(1.0 * px_v))
        d.line([(X(u0), Y(0)), (X(u1), Y(yt))], fill=G_, width=2 * bw); d.line([(X(u2), Y(yt)), (X(u3), Y(0))], fill=G_, width=2 * bw)   # bords verts
        d.rectangle([0, Y(0.9), W, H], fill=G_)
        d.rectangle([X(u1), Y(yt), X(u2), Y(0)], outline=G_, width=bw)                 # panneau du centre (cadre vert)
        for x_ in (X(u1), X(u2)):                                                       # traits blancs de séparation
            d.rectangle([x_ - 3, Y(yt), x_ + 3, Y(0.9)], fill=WH)
        src = Image.open(os.path.join(SP.U, SP.FILES['amv'])).convert('RGBA'); sq = lambda img: img.resize((img.size[0], max(1, int(img.size[1] * px_v / px_u))), Image.LANCZOS)
        fit(im, sq(src.crop((272, 30, 522, 372))), (X(u1) + bw + 8, Y(yt) + bw + 8, X(u2) - bw - 8, Y(1.2)), 0.02)   # la bulle (AMV + texte) au centre
        girl, boy = src.crop((130, 200, 290, 440)), src.crop((512, 200, 680, 440))
        fit(im, sq(girl), (X(u1 - 0.55 * (u1 - u0)), Y(0.62 * yt), X(u1) - bw - 6, Y(1.0)), 0.0)
        fit(im, sq(boy), (X(u2) + bw + 6, Y(0.62 * yt), X(u2 + 0.45 * (u3 - u2)), Y(1.0)), 0.0)
        ft = ImageFont.truetype('C:/Windows/Fonts/ariblk.ttf', max(20, int(2.6 * px_v)))
        d.text((X(u2 + 0.62 * (u3 - u2)), Y(2.4)), 'AMV.FR', font=ft, fill=G_, anchor='mm')
        d.text((X(u0 + 0.45 * (u1 - u0)), Y(1.9)), 'AMV', font=ft, fill=G_, anchor='mm')
        b0, b1, y0, y1 = AMV_BARRIER                                                    # barrière blanche, AMV comme une banderole
        d.rectangle([X(b0), Y(y1), X(b1), Y(y0)], fill=WH, outline=G_, width=max(3, bw // 2))
        _, la = SP.panel('amv'); hb = (y1 - y0) * 0.58; wb = hb * la.size[0] / la.size[1]; n_ = max(3, int((b1 - b0) / (wb * 1.25)))
        for k in range(n_):
            uc = b0 + (b1 - b0) * (k + 0.5) / n_
            fit(im, sq(la), (X(uc - wb / 2), Y(y0 + (y1 - y0) / 2 + hb / 2), X(uc + wb / 2), Y(y0 + (y1 - y0) / 2 - hb / 2)), 0.0)
    im = _fabric(im, (0, 0, W, H), 7, seed=24); im = _fabric(im, (0, 0, W, H), 4, seed=25)   # v24b : un peu de texture (bâche tendue), pas lisse
    d = ImageDraw.Draw(im); d.rectangle([0, 0, 4, 4], fill=(16, 16, 18)); return K.grain(im, 2.0)


# ================================================================ v25 : murs de virage façon Paris IRL (message de l'utilisateur)
# « tous les virages ont un mur gris dès l'entrée jusqu'à la sortie ; le filet est que sur 3 moments décisifs du virage » ; Honda : 7 boudins,
# filets sur 3 (1-2 à l'entrée et 2-3 à la fin sans filet) ; FIVE : 8, alterné logo FIVE / 5, filets du 2e au 6e ; Minerva : 2 filets au
# milieu ; MX Sim : 2 filets ; Automoto, Moto Verte, Yamaha (4 boudins) : pas de filet ; « les murs moins hauts : que ce soit le boudin qui
# touche, presque pas de gris au sommet » -> dessus de chaque module à la crête locale + VIS25 ; gris plus foncé.
WALL_N = {'T1 1': 8, 'T_C ': 8, 'T_E ': 4}   # v25d : Honda « commence 1 trop tôt, il en manque 2 à la sortie » : 7 -> 8, un module plus tard
WALL_START_MOD = {'T1 1': 1}
# v25e (traits rouges / bleus sur les captures) : modules enlevés au début, modules en plus (+) ou en moins (-) à la fin
WALL_TRIM = {'T_D ': (1, -2), 'T_TR': (1, -1), 'T_C ': (1, 2), 'T_L5a': (1, -1), 'T_Bb': (1, -1)}                     # nombre de modules imposé ; sinon tout l'appui (berm) couvert
WALL_START = {'T1 1': 0.10, 'T_C ': 0.10, 'T_E ': 0.12}         # début (fraction du virage) quand le nombre est imposé
WALL_NETS = {'T1 1': (1, 2, 3), 'T_C ': (0, 1, 2, 3, 4), 'T_D ': (), 'T_TR': (), 'T_E ': ()}   # modules à filet ; sinon 2 au milieu
WALL_KEYS = {'T_C ': ('five', 'five5')}                         # logos alternés
VIS25 = 0.15


WALL_GEOM = {}                                                  # v25c : géométrie des murs calculée au rendu du terrain (build_zion.wall_fill)


def wall_geom(g, Hf):
    """v25c : géométrie d'un mur de virage (modules, filets, logos) et UNE hauteur pour tout le mur (« fais droit, pas des escaliers ») :
    la plus haute crête du berm le long du mur + VIS25 ; ytop_rel est relatif à la hauteur du centre du virage."""
    tg_ = lambda d: next((v for k_, v in d.items() if g['tag'].startswith(k_)), None)
    sg = 1.0 if g['ang'] > 0 else -1.0; th_in = g['t0'] + sg * np.pi / 2; ang = np.radians(g['ang']); th = lambda f: th_in - ang * f
    cx, cz = g['cx'], g['cz']; h0 = float(np.ravel(Hf(cx, cz))[0])
    fb0 = g.get('berm_from', 0.0); tm = th((fb0 + 1) / 2); rr = np.arange(g['r'], g['r'] + 40, 0.5)
    r_crest = float(rr[int(np.argmax(Hf(cx + np.cos(tm) * rr, cz + np.sin(tm) * rr)))])
    W = BLK['W']; rc = r_crest + BLK['back'] + W / 2; df = AIRF['mod'] / (abs(ang) * rc)
    nmod = tg_(WALL_N)
    if nmod:
        f_a = fb0 + (tg_(WALL_START) or 0.08) + (tg_(WALL_START_MOD) or 0) * df
    else:
        nmod = max(2, int(round((1 - fb0) / df))); f_a = fb0 + ((1 - fb0) - nmod * df) / 2
    tr_ = tg_(WALL_TRIM) or (0, 0); f_a += tr_[0] * df; nmod = nmod - tr_[0] + tr_[1]
    fs = f_a + df * np.arange(nmod + 1)
    nets = tg_(WALL_NETS)
    if nets is None:
        nets = (nmod // 2 - 1, nmod // 2)
    E = lambda f: np.array([np.cos(th(f)), np.sin(th(f))]); rr_ = r_crest + np.linspace(-4, 4, 9)
    hc = max(float(np.max(Hf(cx + E(f)[0] * rr_, cz + E(f)[1] * rr_))) for f in np.linspace(fs[0], fs[-1], 6 * nmod + 1))
    return dict(rc=rc, r_crest=r_crest, W=W, fs=fs, nmod=nmod, nets=tuple(nets), ang=ang, th_in=th_in, cx=cx, cz=cz, h0=h0, ytop_rel=hc + VIS25 - h0)


def turn_wall_v25(out, k, g, Hf, key):
    tg_ = lambda d: next((v for k_, v in d.items() if g['tag'].startswith(k_)), None)
    Gm = WALL_GEOM.get(g['tag']) or wall_geom(g, Hf)
    sg = 1.0 if g['ang'] > 0 else -1.0; th_in = g['t0'] + sg * np.pi / 2; ang = np.radians(g['ang']); th = lambda f: th_in - ang * f
    cx, cz = g['cx'], g['cz']; h0 = float(np.ravel(Hf(cx, cz))[0]); H1 = lambda x, z: float(np.ravel(Hf(x, z))[0])
    r_crest, W, rc, nmod, fs, nets = Gm['r_crest'], Gm['W'], Gm['rc'], Gm['nmod'], Gm['fs'], Gm['nets']; YT = Gm['ytop_rel']
    keys = tg_(WALL_KEYS) or (key,)
    P2 = lambda f, r_: np.array([np.cos(th(f)) * r_, np.sin(th(f)) * r_]); E = lambda f: np.array([np.cos(th(f)), np.sin(th(f))])
    crest = lambda f: max(float(np.max(Hf(cx + E(f)[0] * (r_crest + np.linspace(-4, 4, 9)), cz + E(f)[1] * (r_crest + np.linspace(-4, 4, 9))))) for _ in [0])
    m = Mesh(); airs = {kk: Mesh() for kk in keys}; n2 = Mesh(); rb = AIRF['rb']; dcen = 0.0; sec_b = _tri_section(rb, 30)   # v25c : fagot centré sur le bloc
    Vb, Vt = NT_['v']; TL = 4.0; sph_w, sph_a, sph_n = [], [], []; dot = lambda u: (u[0], u[1], u[0] + 0.0005, u[1] + 0.0005)
    tops = []
    for q in range(nmod):
        A, B = P2(fs[q], rc), P2(fs[q + 1], rc); L = float(np.linalg.norm(B - A)); t = (B - A) / L; nn = np.array([-t[1], t[0]])
        if np.dot(nn, (A + B) / 2) < 0:
            nn = -nn
        right = np.array([-nn[1], nn[0]]); rev = np.dot(t, right) < 0
        A = A - t * 0.04; B = B + t * 0.04; L += 0.08
        ytop = YT; tops.append(ytop + h0)                                        # v25c : même hauteur sur tout le mur
        gnd = min(H1(cx + p_[0], cz + p_[1]) for s_ in np.linspace(0, 1, 5) for w_ in (-W / 2, 0, W / 2) for p_ in [A + (B - A) * s_ + nn * w_]) - h0
        yb = gnd - WALL23['depth']
        sec = [(-W / 2, yb)] + [(-W / 2 + BLK['rnd'] - BLK['rnd'] * np.cos(a_), ytop - BLK['rnd'] + BLK['rnd'] * np.sin(a_)) for a_ in np.linspace(0, np.pi / 2, 5)]
        sec += [(W / 2 - BLK['rnd'] + BLK['rnd'] * np.cos(a_), ytop - BLK['rnd'] + BLK['rnd'] * np.sin(a_)) for a_ in np.linspace(np.pi / 2, 0, 5)] + [(W / 2, yb)]
        sec = np.array(sec); tg2 = np.gradient(sec, axis=0); nr = np.c_[-tg2[:, 1], tg2[:, 0]]; nr /= np.linalg.norm(nr, axis=1, keepdims=True)
        if nr[len(sec) // 2, 1] < 0:
            nr = -nr
        sl_ = np.r_[0, np.cumsum(np.hypot(*np.diff(sec, axis=0).T))]
        V3 = lambda p, d, y: (p[0] + nn[0] * d, y, p[1] + nn[1] * d)
        for j in range(len(sec) - 1):
            Q = [V3(A, *sec[j]), V3(B, *sec[j]), V3(B, *sec[j + 1]), V3(A, *sec[j + 1])]
            N_ = [(nn[0] * nr[j][0], nr[j][1], nn[1] * nr[j][0])] * 2 + [(nn[0] * nr[j + 1][0], nr[j + 1][1], nn[1] * nr[j + 1][0])] * 2
            _face(m, Q, [(0, sl_[j] / 9), (L / 8, sl_[j] / 9), (L / 8, sl_[j + 1] / 9), (0, sl_[j + 1] / 9)], N_)
        for P_, sgn in ((A, -1), (B, 1)):
            pts = [V3(P_, *p) for p in sec]; cen = np.mean(pts, axis=0); nrm = (t[0] * sgn, 0.0, t[1] * sgn)
            for j in range(len(pts)):
                _face(m, [cen, pts[j], pts[(j + 1) % len(pts)]], [(0.3, 0.5), (0.3 + 0.01 * j, 0.1), (0.31 + 0.01 * j, 0.1)], [nrm] * 3)
        for s_ in (0.25, 0.75):
            c_ = A + (B - A) * s_; sph_w.append((c_[0], ytop - 1.2, c_[1]))
        a2 = airs[keys[q % len(keys)]]; yb2 = ytop - 0.15; A2, B2 = A + t * 0.45, B - t * 0.45
        for j in range(len(sec_b) - 1):
            (d0, y0, nd0, ny0), (d1, y1, nd1, ny1) = sec_b[j], sec_b[j + 1]; v0, v1 = 0.975 * j / (len(sec_b) - 1), 0.975 * (j + 1) / (len(sec_b) - 1)
            u0_, u1_ = (1.0, 0.0) if rev else (0.0, 1.0)
            Q = [V3(A2, dcen + d0, yb2 + y0), V3(B2, dcen + d0, yb2 + y0), V3(B2, dcen + d1, yb2 + y1), V3(A2, dcen + d1, yb2 + y1)]
            _face(a2, Q, [(u0_, v0), (u1_, v0), (u1_, v1), (u0_, v1)], [(nn[0] * nd0, ny0, nn[1] * nd0)] * 2 + [(nn[0] * nd1, ny1, nn[1] * nd1)] * 2)
        for d_, y_ in ((-rb, rb), (rb, rb), (0.0, rb * (1 + np.sqrt(3)))):
            a3 = V3(A2, dcen + d_, yb2 + y_); b3 = V3(B2, dcen + d_, yb2 + y_)
            a2.tube(a3, b3, rb * 0.97, (0.02, 0.02, 0.05, 0.05), 14, caps=False)
            ax_ = np.subtract(b3, a3); ax_ = ax_ / np.linalg.norm(ax_); s1 = np.cross(ax_, [0, 1, 0]); s1 /= np.linalg.norm(s1); s2 = np.cross(ax_, s1)
            for cen_, sg_ in ((np.asarray(a3), -1), (np.asarray(b3), 1)):
                ring_ = [cen_ + (np.cos(t_) * s1 + np.sin(t_) * s2) * rb * 0.97 for t_ in np.linspace(0, 2 * np.pi, 15)]
                for j_ in range(14):
                    _face(a2, [cen_, ring_[j_], ring_[j_ + 1]], [(0.5, 0.993)] * 3, [tuple(ax_ * sg_)] * 3)
        for s_ in np.arange(0.5, L, 2.0):
            c_ = A + t * s_; sph_a.append((c_[0] + nn[0] * dcen, yb2 + rb * 1.3, c_[1] + nn[1] * dcen))
        if q in nets:                                                            # filet de ce module
            net_top = ytop - 0.15 + rb * (2 + np.sqrt(3)) + NETV['above']
            An = A + nn * (W / 2 - NETV['off']); cuts = list(np.arange(0, L, TL)) + [L]
            for sa, sb in zip(cuts[:-1], cuts[1:]):
                pa, pb = An + t * sa, An + t * sb; ua, ub = (sa % TL) / TL, (sa % TL + (sb - sa)) / TL
                Q = [(pa[0], ytop - 0.2, pa[1]), (pb[0], ytop - 0.2, pb[1]), (pb[0], net_top, pb[1]), (pa[0], net_top, pa[1])]
                UV = [(ua, Vb), (ub, Vb), (ub, Vt), (ua, Vt)]; e3 = (nn[0], 0, nn[1])
                _face(n2, Q, UV, [tuple(-np.array(e3))] * 4); _face(n2, Q, UV, [e3] * 4)
            for s_ in np.arange(1.0, L, 2.0):
                c_ = An + t * s_; sph_n += [(c_[0], ytop + h_, c_[1]) for h_ in (1.5, 3.0, 4.5)]
    nets = sorted(q for q in nets if q < nmod)
    if nets:                                                                     # poteaux : aux raccords des modules à filet + mousses
        runs = []; r_ = [nets[0]]
        for q in nets[1:]:
            if q == r_[-1] + 1:
                r_.append(q)
            else:
                runs.append(r_); r_ = [q]
        runs.append(r_)
        for run in runs:
            ytr = max(tops[q] for q in run) - h0; net_top = ytr - 0.15 + rb * (2 + np.sqrt(3)) + NETV['above']
            for qi in range(run[0], run[-1] + 2):
                f = fs[qi]; p_ = P2(f, rc); e_ = p_ / np.linalg.norm(p_); pp = p_ + e_ * (W / 2 - NETV['off'] + 0.12)
                ends = qi in (run[0], run[-1] + 1)
                if ends:
                    t_in = P2(fs[qi + 1] if qi == run[0] else fs[qi - 1], rc) - p_; pp = pp + t_in / np.linalg.norm(t_in) * 0.9
                yb_ = tops[min(qi, nmod - 1)] - h0 - 0.2; yt_ = net_top + 0.35
                n2.tube((pp[0], yb_, pp[1]), (pp[0], yt_, pp[1]), NETV['pole_r'], dot(NT_['red']), 8)
                n2.tube((pp[0], yt_, pp[1]), (pp[0], yt_ + NETV['cap'], pp[1]), NETV['pole_r'] * 1.25, dot(NT_['yel']), 8)
                if ends:
                    tg3 = np.array([-e_[1], e_[0]]); w2, d2 = NETV['epad']
                    _obox(n2, (pp[0] - e_[0] * (d2 / 2 - 0.1), pp[1] - e_[1] * (d2 / 2 - 0.1)), tg3, e_, w2, d2, yb_ + 0.15, yb_ + 0.15 + NETV['epad_h'], NT_['blk'])
                else:
                    n2.tube((pp[0], yb_ + 0.15, pp[1]), (pp[0], yb_ + 0.15 + NETV['pad_h'], pp[1]), NETV['pad_r'], dot(NT_['blk']), 10)
    files = [('mur_virage_%d.jm' % k, 'bache_paille.png', 'mur_virage_%d.shp' % k)]
    m.write(os.path.join(out, 'mur_virage_%d.jm' % k), MAT_MAT); K.shp(os.path.join(out, 'mur_virage_%d.shp' % k), sph_w, 2.2)   # v25e : mat
    for i_, kk in enumerate(keys):
        nm_ = 'air_virage_%d%s' % (k, '' if i_ == 0 else '_%d' % i_)
        airs[kk].write(os.path.join(out, nm_ + '.jm'), MAT_BACHE)
        K.shp(os.path.join(out, nm_ + '.shp'), sph_a if i_ == 0 else [sph_a[0]], 1.1, par=(0.6, 150, 8))
        files.append((nm_ + '.jm', bundle_texture_v23(out, kk), nm_ + '.shp'))
    if len(n2.V):
        n2.write(os.path.join(out, 'filet_virage_%d.jm' % k), MAT_MAT); K.shp(os.path.join(out, 'filet_virage_%d.shp' % k), sph_n, 0.9, par=(1.0, 85, 4))
        files.append(('filet_virage_%d.jm' % k, NT_['png'], 'filet_virage_%d.shp' % k))
    return dict(modules=nmod, nets=list(nets), f=(round(fs[0], 3), round(fs[-1], 3)), files=tuple(files))


# ================================================================ v25 : cabane du signaleur (MX Sim Racing) et portique holeshot Milwaukee
def cabin_v25(out, wp, key='mxsim'):
    """cabane noire fermée (7 x 6 x 8,5 ft), fenêtre ouverte vers la piste (+z), toit qui déborde, logo du sponsor sur les 3 autres
    faces ; wp(x, y, z) -> point monde relatif (le modèle est posé au lacet 0, déjà tourné par wp)."""
    import sponsors as SP
    bg, lg = SP.panel(key); Wt, Ht = 1024, 512; im = Image.new('RGB', (Wt, Ht), (14, 14, 15)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 512, 512], fill=bg)
    if lg is not None:
        fit(im, lg, (20, 120, 492, 392), 0.04)
    d.rectangle([600, 0, 700, 100], fill=(14, 14, 15)); d.rectangle([720, 0, 820, 100], fill=(40, 40, 42))
    im = K.grain(im, 1.5); _save(im, os.path.join(out, 'cabane_mxsim.png'))
    pan, blk, grey = R((0, 0, 512, 512), Wt, Ht), R((600, 0, 700, 100), Wt, Ht), R((720, 0, 820, 100), Wt, Ht)
    m = Mesh(); X, Z, Hc, hw = 3.5, 3.0, 6.5, (3.0, 6.5)                              # v25e : murs plus bas (le signaleur se voit), devant ouvert à 3 ft
    q = lambda P, r, n: _face(m, [wp(*p) for p in P], [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])], [n] * 4)
    nw = lambda v: tuple(np.subtract(wp(*v), wp(0, 0, 0)))
    for sx in (-1, 1):                                                                   # côtés (logo), dehors et dedans
        P = [(sx * X, 0, -Z), (sx * X, 0, Z), (sx * X, Hc, Z), (sx * X, Hc, -Z)]
        q(P, (pan[2], pan[1], pan[0], pan[3]) if sx > 0 else pan, nw((sx, 0, 0)))   # v25 : logo à l'endroit des 2 côtés (_face règle le sens)
        q(P[::-1] if sx > 0 else P, blk, nw((-sx, 0, 0)))
    P = [(X, 0, -Z), (-X, 0, -Z), (-X, Hc, -Z), (X, Hc, -Z)]; q(P, pan, nw((0, 0, -1))); q(P[::-1], blk, nw((0, 0, 1)))   # dos
    for y0, y1 in [q_ for q_ in ((0, hw[0]), (hw[1], Hc)) if q_[1] > q_[0] + 0.01]:  # devant : bas (+ haut), ouvert au-dessus
        P = [(-X, y0, Z), (X, y0, Z), (X, y1, Z), (-X, y1, Z)]; q(P, blk, nw((0, 0, 1))); q(P[::-1], blk, nw((0, 0, -1)))
    # v25e (« pas de toit, il faut mettre quelqu'un dedans avec un drapeau ») : plus de toit, le signaleur est dans la cabane
    m.write(os.path.join(out, 'cabane_mxsim.jm'), MAT_MAT)
    K.shp(os.path.join(out, 'cabane_mxsim.shp'), [wp(x, 2.5, z) for x in (-2, 2) for z in (-1.5, 1.5)], 1.6, par=(1.5, 1000, 200))
    return 'cabane_mxsim.jm', 'cabane_mxsim.png', 'cabane_mxsim.shp'


def holeshot_v25(out, wp, span=17.0, hp=13.0, bh=5.0, pw=1.4, mir=False, t2=0.25):   # v25c : moins épais (« moins fat »)
    """portique « Heavy Duty Holeshot » Milwaukee en L renversé (photo) : poteau rouge large (texte vertical du bas en haut) au bord de la
    piste, bannière Milwaukee au-dessus de la piste (logo près du poteau, perceuse au bout) ; repère local : x = vers l'intérieur de la
    piste (la bannière part en +x), z = vers les pilotes. v25b : bannière 2x moins longue, plus haute, poteau plus large."""
    import sponsors as SP
    from PIL import ImageFont
    bg, lg = SP.panel('milwaukee'); Wt, Ht = 2048, 2048; im = Image.new('RGB', (Wt, Ht), bg); d = ImageDraw.Draw(im)
    bh_px = int(round(Wt * bh / span)); a = pw / 2
    # v25c (« centre le Milwaukee ») : centré sur la partie de la bannière que la perceuse ne cache pas (sa moitié gauche dépasse du bord)
    wd, hf_ = drill_geom(); x_vis = span - hf_ * wd - 0.3
    fit(im, lg, (int(Wt * 0.3 / span), 16, int(Wt * x_vis / span), bh_px - 16), 0.04)
    ph_px = Ht - bh_px - 60; pc_w = int(round(ph_px * pw / (hp + bh))); pcol = (0, bh_px + 40, pc_w, bh_px + 40 + ph_px)
    # v25d (« inverse les deux gras : HEAVY DUTY pas en gras, la taille du HOLESHOT ; HOLESHOT en gras, la taille du HEAVY DUTY ; il
    # commence trop tôt, le H est presque dans la terre ; le T touche pas le truc ») : une ligne le long du poteau, entre 1,5 ft du sol et
    # 0,6 ft sous la pancarte
    f1 = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 200); f2 = ImageFont.truetype('C:/Windows/Fonts/arialbi.ttf', 260)
    l1 = Image.new('RGBA', (2600, 330), (0, 0, 0, 0)); ImageDraw.Draw(l1).text((1300, 165), 'HEAVY DUTY', font=f1, fill=(250, 250, 250, 255), anchor='mm')
    l2 = Image.new('RGBA', (2600, 360), (0, 0, 0, 0)); ImageDraw.Draw(l2).text((1300, 180), 'HOLESHOT', font=f2, fill=(250, 250, 250, 255), anchor='mm', stroke_width=5, stroke_fill=(250, 250, 250, 255))
    l1, l2 = l1.crop(l1.getbbox()), l2.crop(l2.getbbox()); hT = l2.size[1]; l1 = l1.resize((int(l1.size[0] * 0.72 * hT / l1.size[1]), int(0.72 * hT)), Image.LANCZOS)
    timg = Image.new('RGBA', (l1.size[0] + 80 + l2.size[0], hT), (0, 0, 0, 0)); timg.paste(l1, (0, hT - l1.size[1]), l1); timg.paste(l2, (l1.size[0] + 80, 0), l2)
    py = lambda y: int(pcol[3] - y * (pcol[3] - pcol[1]) / (hp + bh))                 # ligne de l'image du poteau à la hauteur y (ft)
    d.rectangle(pcol, fill=bg); fit(im, timg.rotate(90, expand=True), (pcol[0] + 4, py(hp - 0.6), pcol[2] - 4, py(1.5)), 0.0)
    xb0 = pc_w + 40; bwB = Wt - xb0; bB = (xb0, bh_px + 40, Wt, bh_px + 40 + int(round(bwB * bh / span)))   # bannière du dos : logo près du poteau aussi
    fit(im, lg, (xb0 + int(bwB * (1 - x_vis / span)), bB[1] + 16, xb0 + int(bwB * (1 - 0.3 / span)), bB[3] - 16), 0.04)
    d.rectangle([1980, 2000, 2030, 2040], fill=(16, 16, 18)); im = K.grain(im, 1.2); _save(im, os.path.join(out, 'holeshot.png'))
    rb_, rp_, rk = R((0, 0, Wt, bh_px), Wt, Ht), R(pcol, Wt, Ht), R((1980, 2000, 2030, 2040), Wt, Ht); rbB = R(bB, Wt, Ht)
    m = Mesh(); nw = lambda v: tuple(np.subtract(wp(*v), wp(0, 0, 0)))
    rf_ = (lambda r: (r[2], r[1], r[0], r[3])) if mir else (lambda r: r)     # v25c : objet posé à l'envers (poteau à gauche) : u retourné
    q = lambda P, r, n: _face(m, [wp(*p) for p in P], [(rf_(r)[0], r[1]), (rf_(r)[2], r[1]), (rf_(r)[2], r[3]), (rf_(r)[0], r[3])], [n] * 4)

    for zf, nz in ((a, 1), (-a, -1)):                                                    # poteau : faces avant / arrière avec le texte
        P = [(-a, 0, zf), (a, 0, zf), (a, hp + bh, zf), (-a, hp + bh, zf)]; q([P[1], P[0], P[3], P[2]] if nz > 0 else P, rp_, nw((0, 0, nz)))
    for xf, nx in ((a, 1), (-a, -1)):
        P = [(xf, 0, -a), (xf, 0, a), (xf, hp + bh, a), (xf, hp + bh, -a)]; q(P if nx > 0 else P[::-1], rk if nx > 0 else rp_, nw((nx, 0, 0)))
    for zf, nz in ((t2, 1), (-t2, -1)):                                                  # bannière, des deux côtés
        P = [(a, hp, zf), (a + span, hp, zf), (a + span, hp + bh, zf), (a, hp + bh, zf)]; q([P[1], P[0], P[3], P[2]] if nz > 0 else P, (rbB if nz > 0 else rb_) if not mir else (rb_ if nz > 0 else rbB), nw((0, 0, nz)))
    for y_, ny in ((hp, -1), (hp + bh, 1)):
        P = [(a, y_, -t2), (a + span, y_, -t2), (a + span, y_, t2), (a, y_, t2)]; q(P if ny > 0 else P[::-1], rk, nw((0, ny, 0)))
    P = [(a + span, hp, -t2), (a + span, hp, t2), (a + span, hp + bh, t2), (a + span, hp + bh, -t2)]; q(P, rk, nw((1, 0, 0)))
    m.write(os.path.join(out, 'holeshot.jm'), MAT_MAT)
    K.shp(os.path.join(out, 'holeshot.shp'), [wp(0, y, 0) for y in (1.0, 3.0, 5.0)], 1.4, par=(1.5, 1000, 200))
    return 'holeshot.jm', 'holeshot.png', 'holeshot.shp'


def drill_geom(h=None):
    """largeur (ft) de la perceuse détourée et position de sa poignée (fraction de la largeur, depuis la gauche)."""
    import sponsors as SP
    from scipy.ndimage import binary_fill_holes, binary_opening
    h = h or DRILL_H; a = np.asarray(Image.open(os.path.join(SP.U, 'perceuse milwaukee.jpg')).convert('RGB'), float)
    fg = binary_fill_holes(binary_opening(np.linalg.norm(a - 255, axis=-1) > 28, iterations=1)); ys, xs = np.nonzero(fg)
    fg = fg[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; row = np.nonzero(fg[int(0.58 * fg.shape[0])])[0]
    return h * (fg.shape[1] + 52) / (fg.shape[0] + 52), (row.min() + row.max()) / 2 / fg.shape[1]


DRILL_H, DRILL_AR = 7.0, 0.80          # v25b : la perceuse (hauteur ft, largeur / hauteur de l'image détourée), bas au bas de la bannière


def drill_cutout_v25(out, wp, x_right, y0, h=None, mir=False, x_handle=None):
    """v25b (« colle-la là où je t'ai mis, sur le bord, à la même hauteur que le Milwaukee en bas, elle dépasse en haut ; un contour blanc
    autour ») : la perceuse Milwaukee en carton découpé avec un liseré blanc, debout contre le bout de la bannière, deux faces lisibles."""
    import sponsors as SP
    from scipy.ndimage import gaussian_filter, binary_fill_holes, binary_opening, binary_dilation
    h = h or DRILL_H
    im = Image.open(os.path.join(SP.U, 'perceuse milwaukee.jpg')).convert('RGB'); a = np.asarray(im, float)
    fg = np.linalg.norm(a - 255, axis=-1) > 28; fg = binary_fill_holes(binary_opening(fg, iterations=1))
    pad = 24; a = np.pad(a, ((pad, pad), (pad, pad), (0, 0)), constant_values=255); fg = np.pad(fg, pad)
    ys, xs = np.nonzero(fg); a = a[ys.min() - pad:ys.max() + pad + 1, xs.min() - pad:xs.max() + pad + 1]; fg = fg[ys.min() - pad:ys.max() + pad + 1, xs.min() - pad:xs.max() + pad + 1]
    out_m = binary_dilation(fg, iterations=14)                                          # liseré blanc
    rgb = np.where(fg[..., None], a, 250.0); al = np.clip(gaussian_filter(out_m.astype(float), 1.0) * 255, 0, 255)
    rgba = Image.fromarray(np.dstack([rgb, al]).astype(np.uint8), 'RGBA')
    rgba = rgba.resize((512, int(512 * rgba.size[1] / rgba.size[0])), Image.LANCZOS); Wt = Ht = 1024
    sheet = Image.new('RGBA', (Wt, Ht), (0, 0, 0, 0)); sheet.paste(rgba, (0, 0), rgba); sheet.paste(rgba.transpose(Image.FLIP_LEFT_RIGHT), (512, 0))
    sheet.save(os.path.join(out, 'perceuse.png'))
    w = h * rgba.size[0] / rgba.size[1]; vh = rgba.size[1] / Ht; x0 = x_right - w
    if x_handle is not None:                                      # v25c (« que le bord soit le manche ») : milieu de la poignée sur x_handle
        row = fg[int(0.58 * fg.shape[0])]; cols = np.nonzero(row)[0]; hf = (cols.min() + cols.max()) / 2 / fg.shape[1]
        x0 = x_handle - hf * w
    m = Mesh(); nw = lambda v: tuple(np.subtract(wp(*v), wp(0, 0, 0)))
    P = [(x0, y0, 0.31), (x0 + w, y0, 0.31), (x0 + w, y0 + h, 0.31), (x0, y0 + h, 0.31)]
    uf_ = (0.5, 1.0) if mir else (1.0, 0.5); ub_ = (0.0, 0.5) if mir else (0.5, 0.0)
    _face(m, [wp(*p) for p in P], [(uf_[0], 1 - vh), (uf_[1], 1 - vh), (uf_[1], 1), (uf_[0], 1)], [nw((0, 0, 1))] * 4)
    P2 = [(x0 + w, y0, -0.31), (x0, y0, -0.31), (x0, y0 + h, -0.31), (x0 + w, y0 + h, -0.31)]
    _face(m, [wp(*p) for p in P2], [(ub_[0], 1 - vh), (ub_[1], 1 - vh), (ub_[1], 1), (ub_[0], 1)], [nw((0, 0, -1))] * 4)
    m.write(os.path.join(out, 'perceuse.jm'), MAT_MAT)
    return 'perceuse.jm', 'perceuse.png', None


# ================================================================ v25d : panneaux pleins, 2 faces dessinées, tranches fermées
# « le Milwaukee : moins de texture, centré sur la forme rouge (pas la noire) » ; « l'AMV : écritures plus nettes, moins de texture, le AMV
# qui touche pas le sol, la dame plus petite, pas le vert derrière les persos » ; « l'intérieur côté piste : tout blanc avec juste les logos
# AMV comme sur la barrière » ; « que l'objet soit plein et pas 2 feuilles : on voit à travers ».
def _cut_bg(img, keep_bottom=True):
    """personnage découpé : les zones vertes du fond de la bulle reliées aux bords (haut, gauche, droite) deviennent transparentes."""
    from scipy.ndimage import label, binary_dilation
    a = np.asarray(img.convert('RGBA')).copy(); rgb = a[..., :3].astype(float)
    green = (rgb[..., 1] > 120) & (rgb[..., 0] < 90) & (rgb[..., 2] < 140); lab, n = label(green)
    edge = set(np.unique(lab[0])) | set(np.unique(lab[:, 0])) | set(np.unique(lab[:, -1]))
    if not keep_bottom:
        edge |= set(np.unique(lab[-1]))
    kill = np.isin(lab, [e for e in edge if e > 0]); kill = binary_dilation(kill, iterations=2) & ~((rgb.min(-1) < 60))
    a[kill, 3] = 0; return Image.fromarray(a, 'RGBA')


def _board_side_v25(kind, W, H, px_u, px_v, ua, inner, top=None, mir=None):
    """dessin d'une face (W x H) ; inner : face côté piste ; mir : coordonnées u en miroir (par défaut = inner). v28 (« le côté gauche du
    carton AMV pas bien fait ») : le panneau de GAUCHE a ses UV inversés (texte lisible) -> le dessin doit l'être aussi, sinon la forme
    imprimée (contour de la bosse) part à l'envers du panneau."""
    mir = inner if mir is None else mir
    import sponsors as SP
    from PIL import ImageFont
    X = (lambda u: int(W - (u - ua) * px_u)) if mir else (lambda u: int((u - ua) * px_u)); Y = lambda y: int(H - y * px_v)
    sq = lambda img: img.resize((img.size[0], max(1, int(img.size[1] * px_v / px_u))), Image.LANCZOS)
    (u0, _), (u1, yt), (u2, _), (u3, _) = BOARD_POLY[kind]
    if top is not None and kind == 'amv':                                               # v25e : contour = la forme de la bosse
        tu, ty = np.array([q[0] for q in top]), np.array([q[1] for q in top]); yt = float(ty.max()); kk = np.nonzero(ty >= yt - 1.2)[0]
        u0, u1, u2, u3 = float(tu[0]), float(tu[kk[0]]), float(tu[kk[-1]]), float(tu[-1])
    if kind == 'milwaukee':
        bg, lg = SP.panel('milwaukee'); im = Image.new('RGB', (W, H), bg); d = ImageDraw.Draw(im); ysk = 2.3
        d.rectangle([0, Y(ysk), W, H], fill=(16, 16, 18))                               # noir du sol jusqu'à la forme rouge
        yc = ysk + 0.47 * (yt - ysk); hh = 0.42 * (yt - ysk)                            # centré sur la partie ROUGE
        wl = lambda y: (u3 - (u3 - u2) * y / yt) - (u0 + (u1 - u0) * y / yt)              # largeur du trapèze à la hauteur y
        uc = (u0 + (u1 - u0) * yc / yt + u3 - (u3 - u2) * yc / yt) / 2; ww = 0.80 * wl(yc + hh / 2)
        xa, xb = sorted((X(uc - ww / 2), X(uc + ww / 2)))
        fit(im, sq(lg), (xa, Y(yc + hh / 2), xb, Y(yc - hh / 2)), 0.0)
        return im
    G_ = (0, 158, 79); WH = (250, 250, 248); im = Image.new('RGB', (W, H), WH); d = ImageDraw.Draw(im); bw = max(6, int(1.0 * px_v))
    if top is not None:                                                                 # liseré vert le long du haut (la forme de la bosse)
        d.line([(X(u_), Y(y_) + bw) for u_, y_ in top], fill=G_, width=2 * bw, joint='curve')
    else:
        d.line([(X(u0), Y(0)), (X(u1), Y(yt))], fill=G_, width=2 * bw); d.line([(X(u2), Y(yt)), (X(u3), Y(0))], fill=G_, width=2 * bw)
    d.rectangle([0, Y(0.9), W, H], fill=G_)
    b0, b1, y0, y1 = AMV_BARRIER; _, la = SP.panel('amv')
    if top is not None:
        b0, b1, y0, y1 = u1, u2, yt, yt + (AMV_BARRIER[3] - AMV_BARRIER[2])
    def row(ua_, ub_, yb_, yh_, n_min=3):
        hb = (yh_ - yb_) * 0.58; wb = hb * la.size[0] / la.size[1] * (px_v / px_u) * (px_u / px_v); n_ = max(n_min, int((ub_ - ua_) / (wb * 1.3)))
        for k in range(n_):
            uc = ua_ + (ub_ - ua_) * (k + 0.5) / n_; xa, xb = sorted((X(uc - wb / 2), X(uc + wb / 2)))
            fit(im, sq(la), (xa, Y((yb_ + yh_) / 2 + hb / 2), xb, Y((yb_ + yh_) / 2 - hb / 2)), 0.0)
    xa, xb = sorted((X(b0), X(b1))); d.rectangle([xa, Y(y1), xb, Y(y0)], fill=WH, outline=G_, width=max(3, bw // 2))
    row(b0, b1, y0, y1)                                                                 # barrière : AMV comme une banderole
    if inner:                                                                           # côté piste : tout blanc + une rangée de logos AMV
        ym = 0.45 * yt; ul, ur = u0 + (u1 - u0) * (ym + 2) / yt, u3 - (u3 - u2) * (ym + 2) / yt
        if top is not None:
            ab = np.nonzero(np.array([q[1] for q in top]) >= ym + 2.5)[0]; ul, ur = top[ab[0]][0], top[ab[-1]][0]
        row(ul + 2, ur - 2, ym - 2.2, ym + 2.2, 4)
        return im
    xa, xb = sorted((X(u1), X(u2))); d.rectangle([xa, Y(yt), xb, Y(0)], outline=G_, width=bw)
    for x_ in (xa, xb):
        d.rectangle([x_ - 3, Y(yt), x_ + 3, Y(0.9)], fill=WH)
    src = Image.open(os.path.join(SP.U, SP.FILES['amv'])).convert('RGBA')
    fit(im, sq(src.crop((272, 30, 522, 372))), (xa + bw + 10, Y(yt) + bw + 10, xb - bw - 10, Y(1.4)), 0.02)   # la bulle, au centre
    girl, boy = _cut_bg(src.crop((130, 200, 290, 440))), _cut_bg(src.crop((512, 200, 680, 440)))
    gx0, gx1 = sorted((X(u1 - 0.50 * (u1 - u0)), X(u1) - bw - 8 if not inner else X(u1) + bw + 8))
    fit(im, sq(girl), (gx0, Y(0.48 * yt), gx1, Y(1.4)), 0.0)                           # la dame, plus petite
    bx0, bx1 = sorted((X(u2) + bw + 8, X(u2 + 0.45 * (u3 - u2))))
    fit(im, sq(boy), (bx0, Y(0.58 * yt), bx1, Y(1.4)), 0.0)
    ft = ImageFont.truetype('C:/Windows/Fonts/ariblk.ttf', max(20, int(2.4 * px_v)))
    uR_, uL_ = u2 + 0.64 * (u3 - u2), u0 + 0.50 * (u1 - u0)
    if top is not None:                                                                 # v25e : là où la bosse fait au moins 8 ft (pas coupé par le bord)
        uL_, uR_ = u0 + 0.40 * (u1 - u0), u2 + 0.64 * (u3 - u2)                        # v25f : entre le pied et chaque perso
    # v38d (« le AMV.fr mord dans le vert, décale-le dans le blanc ou enlève-le, des 2 côtés ») : enlevés
    return im


def board_v25(out, name, Hf, g, side, kind, th=None):
    """panneau PLEIN (épaisseur th) : face extérieure (dessin), face côté piste (dessin à part, à l'endroit), tranches fermées tournées vers
    l'extérieur ; texture = 2 moitiés (haut : extérieur, bas : côté piste)."""
    c, s_ = np.cos(g['t']), np.sin(g['t']); nrm = np.array([-s_, c]) * side; tg = np.array([c, s_])
    H1 = lambda p: float(np.ravel(Hf(p[0], p[1]))[0]); base = lambda u: np.array([g['x0'] + u * c, g['z0'] + u * s_])
    th = th or _LP.BOARD_TH; poly = BOARD_POLY[kind]; ua, ub = poly[0][0], poly[-1][0]; um = (ua + ub) / 2
    vb = _LP.BOARD_VB[kind]; h0 = H1(base(um) + nrm * (vb + 12.0)); O = base(um) + nrm * (vb + 4.0); h_o = H1(O)
    shapes = [poly] + ([[(AMV_BARRIER[0], AMV_BARRIER[2]), (AMV_BARRIER[1], AMV_BARRIER[2]), (AMV_BARRIER[1], AMV_BARRIER[3]), (AMV_BARRIER[0], AMV_BARRIER[3])]]
                       if kind == 'amv' else [])
    ymax = max(y for sh in shapes for _, y in sh); L = ub - ua; W = 2048; Ht = int(min(1024, max(256, round(W * ymax / L / 32) * 32)))
    px_u, px_v = W / L, Ht / ymax
    outer, inner = _board_side_v25(kind, W, Ht, px_u, px_v, ua, False), _board_side_v25(kind, W, Ht, px_u, px_v, ua, True)
    im = Image.new('RGB', (W, 2 * Ht)); im.paste(outer, (0, 0)); im.paste(inner, (0, Ht))
    im = _fabric(im, (0, 0, W, 2 * Ht), 3, seed=24); im = K.grain(im, 0.8)            # v25d : beaucoup moins de texture
    ImageDraw.Draw(im).rectangle([0, 0, 4, 4], fill=(16, 16, 18)); png = name + '.png'; _save(im, os.path.join(out, png))
    m = Mesh(); fu = (lambda u: (u - ua) / L) if side > 0 else (lambda u: 1 - (u - ua) / L)
    fvo = lambda y: 0.5 + 0.5 * y / ymax; fvi = lambda y: 0.5 * y / ymax; blk = (0.001, 0.999)
    P = lambda u, d, y: (base(u)[0] + nrm[0] * (vb + d) - O[0], y + (h0 - h_o) - (0.6 if y < 0.01 else 0.0), base(u)[1] + nrm[1] * (vb + d) - O[1])
    n_o = (nrm[0], 0.0, nrm[1]); n_i = (-nrm[0], 0.0, -nrm[1])
    for sh in shapes:
        cu, cy = np.mean([q[0] for q in sh]), np.mean([q[1] for q in sh])
        for k in range(1, len(sh) - 1):
            tri = [sh[0], sh[k], sh[k + 1]]
            _face(m, [P(u, th / 2, y) for u, y in tri], [(fu(u), fvo(y)) for u, y in tri], [n_o] * 3)
            _face(m, [P(u, -th / 2, y) for u, y in tri], [(1 - fu(u), min(0.499, fvi(y))) for u, y in tri], [n_i] * 3)
        for k in range(len(sh)):                                                        # tranches, normale vers l'extérieur du contour
            (u0_, y0_), (u1_, y1_) = sh[k], sh[(k + 1) % len(sh)]
            e_ = np.array([u1_ - u0_, y1_ - y0_]); nn_ = np.array([e_[1], -e_[0]]) / (np.linalg.norm(e_) or 1)
            if np.dot(nn_, [(u0_ + u1_) / 2 - cu, (y0_ + y1_) / 2 - cy]) < 0:
                nn_ = -nn_
            n3 = (tg[0] * nn_[0], nn_[1], tg[1] * nn_[0])
            _face(m, [P(u0_, -th / 2, y0_), P(u1_, -th / 2, y1_), P(u1_, th / 2, y1_), P(u0_, th / 2, y0_)], [blk] * 4, [n3] * 4)
    m.write(os.path.join(out, name + '.jm'), MAT_MAT)
    K.shp(os.path.join(out, name + '.shp'), [P(u, 0, 2.0) for u in np.arange(ua + 2, ub - 1, 3.0)], 1.0)
    return O, name + '.jm', png, name + '.shp'


def board_v25b(out, name, Hf, g, side, kind, th=None):
    """v25e (« baisse la hauteur des rebords, ça remonte sur les côtés de la bosse ; même angle que la bosse ; le trait vert sous les logos
    doit toucher le plat » ; Milwaukee : « les rebords dépassent en haut : à ras, même hauteur que la bosse, l'angle est bien ») :
    AMV : le haut du panneau = la forme de la bosse (+0,1 ft), barrière posée dessus ; Milwaukee : trapèze (BOARD_POLY), haut au ras.
    Panneau plein (bandes verticales), 2 faces dessinées, tranches fermées."""
    c, s_ = np.cos(g['t']), np.sin(g['t']); nrm = np.array([-s_, c]) * side; tg = np.array([c, s_])
    H1 = lambda p: float(np.ravel(Hf(p[0], p[1]))[0]); base = lambda u: np.array([g['x0'] + u * c, g['z0'] + u * s_])
    th = th or _LP.BOARD_TH; poly = BOARD_POLY[kind]; ua, ub = poly[0][0], poly[-1][0]; um = (ua + ub) / 2
    vb = _LP.BOARD_VB[kind]; h0 = H1(base(um) + nrm * (vb + 12.0)); O = base(um) + nrm * (vb + 4.0); h_o = H1(O)
    if kind == 'amv':
        us = np.arange(ua, ub + 0.01, 1.0); ys = np.array([max(0.0, H1(base(u)) - h0) + 0.1 for u in us]); k = np.nonzero(ys > 0.45)[0]
        us, ys = us[k[0]:k[-1] + 1], ys[k[0]:k[-1] + 1]
        # v25f (« les bords droits, sans courbe ; léger petit angle au début, le reste droit ») : pied -> 2 ft (petit angle), puis ligne droite
        # jusqu'au bord du plat (à la hauteur du plat), plat droit
        ytp = float(ys.max()); kk_ = np.nonzero(ys >= ytp - 1.2)[0]; i1, i2 = kk_[0], kk_[-1]
        iL = int(np.nonzero(ys[:i1 + 1] >= 2.0)[0][0]); iR = i2 + int(np.nonzero(ys[i2:] <= 2.0)[0][0])
        ku = [us[0], us[iL], us[i1], us[i2], us[iR], us[-1]]; ky = [0.3, ys[iL], ytp, ytp, ys[iR], 0.3]
        ys = np.interp(us, ku, ky)
    else:
        us = np.arange(ua, ub + 0.01, 0.5); ys = np.interp(us, [q[0] for q in poly], [q[1] for q in poly])
    top = list(zip(us.tolist(), ys.tolist())); ytop = float(ys.max()); hb_ = AMV_BARRIER[3] - AMV_BARRIER[2]
    kk = np.nonzero(ys >= ytop - 1.2)[0]; bu0, bu1 = float(us[kk[0]]), float(us[kk[-1]])
    ymax = ytop + (hb_ + 0.2 if kind == 'amv' else 0.0); L = ub - ua; W = 2048; Ht = int(min(1024, max(256, round(W * ymax / L / 32) * 32)))
    px_u, px_v = W / L, Ht / ymax
    outer = _board_side_v25(kind, W, Ht, px_u, px_v, ua, False, top if kind == 'amv' else None, mir=side < 0)   # v28 : UV de la face = 1 - fu à gauche
    inner = _board_side_v25(kind, W, Ht, px_u, px_v, ua, True, top if kind == 'amv' else None, mir=side > 0)
    im = Image.new('RGB', (W, 2 * Ht)); im.paste(outer, (0, 0)); im.paste(inner, (0, Ht))
    im = _fabric(im, (0, 0, W, 2 * Ht), 3, seed=24); im = K.grain(im, 0.8)
    ImageDraw.Draw(im).rectangle([0, 0, 4, 4], fill=(16, 16, 18)); png = name + '.png'; _save(im, os.path.join(out, png))
    m = Mesh(); fu = (lambda u: (u - ua) / L) if side > 0 else (lambda u: 1 - (u - ua) / L)
    fvo = lambda y: 0.5 + 0.5 * y / ymax; fvi = lambda y: min(0.499, 0.5 * y / ymax); blk = (0.001, 0.999)
    P = lambda u, d, y: (base(u)[0] + nrm[0] * (vb + d) - O[0], y + (h0 - h_o) - (0.6 if y < 0.01 else 0.0), base(u)[1] + nrm[1] * (vb + d) - O[1])
    n_o = (nrm[0], 0.0, nrm[1]); n_i = (-nrm[0], 0.0, -nrm[1])
    def strip(tp, bt, vmap=None):
        """bande verticale entre bt(u) et tp(u) (listes (u, y)), 2 faces + tranches haut / bas / bouts."""
        for (ua_, ta), (ub_, tb), (_, ba), (_, bb) in zip(tp[:-1], tp[1:], bt[:-1], bt[1:]):
            Q = [(ua_, ba), (ub_, bb), (ub_, tb), (ua_, ta)]
            vo = [fvo(y) for _, y in Q] if vmap is None else [vmap(0.5, y_, b_) for (_, y_), b_ in zip(Q, (1, 1, 0, 0))]
            vi = [fvi(y) for _, y in Q] if vmap is None else [vmap(0.0, y_, b_) for (_, y_), b_ in zip(Q, (1, 1, 0, 0))]
            _face(m, [P(u, th / 2, y) for u, y in Q], [(fu(u), v) for (u, _), v in zip(Q, vo)], [n_o] * 4)
            _face(m, [P(u, -th / 2, y) for u, y in Q], [(1 - fu(u), v) for (u, _), v in zip(Q, vi)], [n_i] * 4)
            for (p0, p1, sgn) in (((ua_, ta), (ub_, tb), 1), ((ua_, ba), (ub_, bb), -1)):
                e_ = np.array([p1[0] - p0[0], p1[1] - p0[1]]); nn_ = np.array([-e_[1], e_[0]]) * sgn / (np.linalg.norm(e_) or 1)
                n3 = (tg[0] * nn_[0], nn_[1], tg[1] * nn_[0])
                _face(m, [P(p0[0], -th / 2, p0[1]), P(p1[0], -th / 2, p1[1]), P(p1[0], th / 2, p1[1]), P(p0[0], th / 2, p0[1])], [blk] * 4, [n3] * 4)
        for (u_, t_), (_, b_), sgn in ((tp[0], bt[0], -1), (tp[-1], bt[-1], 1)):
            n3 = (tg[0] * sgn, 0.0, tg[1] * sgn)
            _face(m, [P(u_, -th / 2, b_), P(u_, th / 2, b_), P(u_, th / 2, t_), P(u_, -th / 2, t_)], [blk] * 4, [n3] * 4)
    strip(top, [(u, 0.0) for u in us])
    if kind == 'amv':                                                                   # barrière posée sur le plat, même dessin que le texte
        k2 = [i for i, u in enumerate(us) if bu0 - 1e-6 <= u <= bu1 + 1e-6]; bt = [top[i] for i in k2]; tp = [(u, y + hb_) for u, y in bt]
        vm = lambda off, y, isb: off + 0.5 * ((ytop if isb else ytop + hb_) / ymax) if off > 0 else min(0.499, 0.5 * ((ytop if isb else ytop + hb_) / ymax))
        strip(tp, bt, vm)
    m.write(os.path.join(out, name + '.jm'), MAT_MAT)
    K.shp(os.path.join(out, name + '.shp'), [P(u, 0, 2.0) for u in np.arange(ua + 2, ub - 1, 3.0)], 1.0)
    return O, name + '.jm', png, name + '.shp'
