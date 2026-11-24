"""v22 (version Zion) : murs des virages et arche 50 Factory refaits d'après 4 vraies photos de Paris envoyées par l'utilisateur
(paris2026/refs/photos_murs_v22/) : « comment est la bâche dans les virages, le mur de paille entouré de bâches grises, comment les
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

BLK = dict(W=4.6, H=3.4, rnd=0.35, flare=0.35, back=0.3, sink=1.0)   # v23 (« enterre plus ; plus près du sommet du virage ») : sink 0,3 -> 1,0, back 0,9 -> 0,3   # bloc de paille bâché (ft) ; back = écart crête -> face avant
AIRF = dict(ra=0.95, mod=10.0, gap=0.45, end=0.7, squash=0.9, rb=0.72, nmin=3, nmax=4)   # v23 : fagot de 3 boudins (rb), modules fixes de 10 ft (3 ou 4)
# v23 (« les trucs FIVE : tout noir, pas FIVE partout, en fonction du sponsor ») : sponsor du mur de chaque virage (code couleur de l'utilisateur)
TURN_SPONSOR = {'T_L5a': 'minerva', 'T_Bb': None, 'T_D ': 'automoto', 'T1 1': 'honda', 'T_TR': 'motoverte', 'T_E ': 'yamaha', 'T_C ': 'five'}      # boudins AIR : rayon, module, jour entre modules, bout arrondi
NETV = dict(above=8.0, pole_r=0.10, cap=0.35, pad_r=0.32, pad_h=4.5, epad=(1.5, 0.9), epad_h=5.5, off=0.25)
RED_AIR = (200, 18, 26); YELLOW_CAP = (250, 200, 30); RED_POLE = (190, 20, 24)
BANNERS = ('five', 'five_rouge')


# ---------------------------------------------------------------- textures
def tarp_texture(out):
    """bâche grise du bloc de paille : u = le long du mur (tuile de 8 ft), v = le tour de la section (pied avant en bas de l'image ->
    pied arrière en haut). Plis verticaux mous + plis cassés en diagonale + reflet doux sur l'arête du dessus (photos)."""
    from scipy.ndimage import gaussian_filter
    W, H = 512, 1024; rng = np.random.default_rng(22)
    fold = gaussian_filter(rng.normal(0, 1, (H, W)), (90, 9), mode='wrap'); fold /= fold.std()          # plis verticaux
    diag = gaussian_filter(rng.normal(0, 1, (H, W)), (22, 22), mode='wrap'); diag /= diag.std()
    yy, xx = np.mgrid[0:H, 0:W]; diag = np.roll(diag, 0, 0) * (0.6 + 0.4 * np.sin(xx / W * 2 * np.pi * 3 + yy / H * 9))
    crease = np.clip(np.abs(gaussian_filter(rng.normal(0, 1, (H, W)), (14, 14), mode='wrap')) * 6 - 4.2, 0, 1)   # cassures fines
    v = 1 - (np.arange(H) + 0.5)[:, None] / H
    hi = 0.5 * np.exp(-((v - 0.42) / 0.05) ** 2) + 0.35 * np.exp(-((v - 0.62) / 0.05) ** 2)          # arêtes du dessus
    base = np.array([108.0, 109, 113]); sh = 0.82 + 0.18 * np.sin(np.pi * np.clip(v * 1.1, 0, 1))
    a = base * sh[..., None] + (fold * 13 + diag * 6 - crease * 18 + hi * 45)[..., None] + rng.normal(0, 1.5, (H, W, 1))
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
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
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
WALL23 = dict(vis=1.6, depth=1.0, n90=3, n180=4, entry=0.02)
TURN_SPONSOR.update({'T_Bb': 'mxsim', 'T_Ba': 'mxsim'})


def bundle_texture_v23(out, key, Lm=9.3):
    """bâche du fagot : fond = couleur du sponsor, logo côté piste (v 0,10 - 0,44) ; bande noire en haut de l'image (v > 0,975) pour les
    bouts des 3 boudins."""
    import sponsors as SP
    bg, lg = SP.panel(key); P = float(np.sum(np.hypot(*np.diff(_tri_section(AIRF['rb'])[:, :2], axis=0).T))); W = H = 2048
    from scipy.ndimage import gaussian_filter
    rng = np.random.default_rng(7); n = gaussian_filter(rng.normal(0, 1, (H, W)), (40, 6)); n /= n.std()
    a = np.asarray(bg, float)[None, None, :] * (1 + 0.035 * n[..., None]); im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if lg is not None:
        l2 = lg.resize((lg.size[0], max(1, int(lg.size[1] * Lm / P))), Image.LANCZOS)
        fit(im, l2, (int(W * 0.10), int(H * (1 - 0.44)), int(W * 0.90), int(H * (1 - 0.10))), 0.05)
    ImageDraw.Draw(im).rectangle([0, 0, W, int(H * 0.02)], fill=(18, 18, 20))
    fn = 'fagot23_%s.png' % (key or 'noir'); _save(im, os.path.join(out, fn)); return fn


def turn_wall_v23(out, k, g, Hf, key):
    """mur droit à l'entrée du virage g (3 modules pour un 90°, 4 pour un 180°) ; origine du modèle : centre du virage, lacet 0."""
    sg = 1.0 if g['ang'] > 0 else -1.0; th_in = g['t0'] + sg * np.pi / 2; ang = np.radians(g['ang']); th = lambda f: th_in - ang * f
    cx, cz = g['cx'], g['cz']; h0 = float(np.ravel(Hf(cx, cz))[0]); H1 = lambda x, z: float(np.ravel(Hf(x, z))[0])
    f_a = g.get('berm_from', 0.0) + WALL23['entry']; nmod = WALL23['n180'] if abs(g['ang']) > 100 else WALL23['n90']
    tm = th(f_a + 0.15); rr = np.arange(g['r'], g['r'] + 40, 0.5)
    r_crest = float(rr[int(np.argmax(Hf(cx + np.cos(tm) * rr, cz + np.sin(tm) * rr)))])
    W = BLK['W']; rc = r_crest + BLK['back'] + W / 2; df = AIRF['mod'] / (abs(ang) * rc)
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
        for d_, y_ in ((-rb, rb), (rb, rb), (0.0, rb * (1 + np.sqrt(3)))):
            a3 = V3(A + t * 0.12, dcen + d_, yb2 + y_); b3 = V3(B - t * 0.12, dcen + d_, yb2 + y_)
            a2.tube(a3, b3, rb * 0.97, (0.02, 0.985, 0.98, 0.998), 14)
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
    d.rectangle([0, 0, 1024, 928], fill=bg)
    if lg is not None:
        for cx in (256, 768):
            fit(im, lg, (cx - 90, 120, cx + 90, 820), 0.0, rot=90)
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
