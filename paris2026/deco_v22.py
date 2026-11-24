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
from deco_v21 import _face, _save, BLACK, MAT_MAT, MAT_BACHE, NET_RED   # noqa: E402

BLK = dict(W=4.6, H=3.4, rnd=0.35, flare=0.35, back=0.9, sink=0.3)   # bloc de paille bâché (ft) ; back = écart crête -> face avant
AIRF = dict(ra=0.95, mod=10.0, gap=0.45, end=0.7, squash=0.9)      # boudins AIR : rayon, module, jour entre modules, bout arrondi
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
    # --- boudins AIR : modules de AIRF['mod'] ft, 2 tubes, bannière côté piste
    ra, sq = AIRF['ra'], AIRF['squash']; nmod = max(1, int(round(L_arc / AIRF['mod']))); edges = np.linspace(0, L_arc, nmod + 1)
    a2 = Mesh(); ub = AT['body']; uc = AT['cap']; nseg = 18
    dcs = (-W / 2 + ra + 0.12, -W / 2 + 3 * ra + 0.12)
    for q in range(nmod):
        sa, sb = edges[q] + AIRF['gap'] / 2, edges[q + 1] - AIRF['gap'] / 2; Lm = sb - sa
        ss = np.linspace(sa, sb, max(6, int(Lm / 0.8)) + 1); ss = np.unique(np.r_[ss, sa + np.linspace(0, AIRF['end'], 5), sb - np.linspace(0, AIRF['end'], 5)])
        for dc in dcs:
            rings = []
            for s in ss:
                x_ = min(s - sa, sb - s); kk = np.sqrt(np.clip(x_ / AIRF['end'], 0, 1) * (2 - np.clip(x_ / AIRF['end'], 0, 1)))
                kk = 0.25 + 0.75 * kk; f = fof(s); e = E(f); yc = ytop(s) + ra * sq - 0.08 - h0; row = []
                for t in range(nseg + 1):
                    phi = 2 * np.pi * t / nseg; dn, yn = np.cos(phi), np.sin(phi)
                    p = (e[0] * (rc + dc + ra * kk * dn), yc + ra * sq * kk * yn, e[1] * (rc + dc + ra * kk * dn))
                    row.append((p, (e[0] * dn, yn, e[1] * dn), (ub[0] + (ub[2] - ub[0]) * (s - sa) / Lm, ub[1] + (ub[3] - ub[1]) * t / nseg)))
                rings.append(row)
            for i in range(len(rings) - 1):
                for t in range(nseg):
                    A, B, C, D = rings[i][t], rings[i + 1][t], rings[i + 1][t + 1], rings[i][t + 1]
                    _face(a2, [A[0], B[0], C[0], D[0]], [A[2], B[2], C[2], D[2]], [A[1], B[1], C[1], D[1]])
            for i, sgn in ((0, -1), (len(rings) - 1, 1)):                                 # bouts blancs (valve)
                f = fof(ss[i]); tdir = np.array([-np.sin(th(f)), np.cos(th(f))]) * np.sign(-ang) * sgn; nrm = (tdir[0], 0, tdir[1])
                pts = [r_[0] for r_ in rings[i]]; cen = np.mean(pts[:-1], axis=0); cu = ((uc[0] + uc[2]) / 2, (uc[1] + uc[3]) / 2)
                for t in range(nseg):
                    pu = lambda tt: (cu[0] + 0.45 * (uc[2] - uc[0]) * np.cos(2 * np.pi * tt / nseg), cu[1] + 0.45 * (uc[3] - uc[1]) * np.sin(2 * np.pi * tt / nseg))
                    _face(a2, [cen, pts[t], pts[t + 1]], [cu, pu(t), pu(t + 1)], [nrm] * 3)
        # bannière : sur le tube avant, du haut (un peu vers l'arrière) jusqu'au bas de la face côté piste
        key = BANNERS[(q + k) % len(BANNERS)]; rb_ = AT['ban'][key]; ph0, ph1 = np.radians(80), np.radians(245)
        Rb = ra + 0.05; hb = Rb * (ph1 - ph0) * (0.5 * (1 + sq)); lb = min(Lm - 2 * AIRF['end'], hb * AT['ban_ratio']); sm = (sa + sb) / 2
        sb_ = np.linspace(sm - lb / 2, sm + lb / 2, max(4, int(lb / 0.8)) + 1); npp = 10; rows = []
        for s in sb_:
            f = fof(s); e = E(f); yc = ytop(s) + ra * sq - 0.08 - h0; fu = (s - sb_[0]) / lb; fu = 1 - fu if ang > 0 else fu
            row = []
            for t in range(npp + 1):
                phi = ph0 + (ph1 - ph0) * t / npp; dn, yn = np.cos(phi), np.sin(phi)
                p = (e[0] * (rc + dcs[0] + Rb * dn), yc + Rb * sq * yn, e[1] * (rc + dcs[0] + Rb * dn))
                row.append((p, (e[0] * dn, yn, e[1] * dn), (rb_[0] + (rb_[2] - rb_[0]) * fu, rb_[3] - (rb_[3] - rb_[1]) * t / npp)))
            rows.append(row)
        for i in range(len(rows) - 1):
            for t in range(npp):
                A, B, C, D = rows[i][t], rows[i + 1][t], rows[i + 1][t + 1], rows[i][t + 1]
                _face(a2, [A[0], B[0], C[0], D[0]], [A[2], B[2], C[2], D[2]], [A[1], B[1], C[1], D[1]])
    a2.write(os.path.join(out, 'air_virage_%d.jm' % k), MAT_BACHE)
    K.shp(os.path.join(out, 'air_virage_%d.shp' % k),
          [(np.cos(th(fof(s))) * (rc - W / 2 + 2 * ra), ytop(s) + ra - h0, np.sin(th(fof(s))) * (rc - W / 2 + 2 * ra)) for s in np.arange(0.5, L_arc, 2.0)],
          1.2, par=(0.6, 150, 8))
    # --- filet sur le bord arrière du bloc + poteaux rouges (bouchon jaune) + mousses noires
    rn = rc + W / 2 - NETV['off']; n2 = Mesh(); Vb, Vt = NT['v']; TL = 4.0; sph = []
    sv = np.linspace(0, L_arc, max(2, int(L_arc / 1.0) + 1)); bot = np.array([ytop(s) for s in sv]) - 0.2 - h0
    upp = bot + 0.2 + 2 * ra * sq + NETV['above']
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
                       ('air_virage_%d.jm' % k, AT['png'], 'air_virage_%d.shp' % k),
                       ('filet_virage_%d.jm' % k, NT['png'], 'filet_virage_%d.shp' % k)))


# ---------------------------------------------------------------- arche 50 Factory (photo arche_50factory.jpg)
AR = dict(xc=20.0, B=7.5, Ht=5.0, T=2.2, cw=3.0, ct=1.6, top=19.0, bh=5.0, bd=1.2, skirt=0.5)   # poutre haute comme sur la photo


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
    sl = float(np.hypot(B / 2, Ht)); slope = (800, 0, 800 + int(T * S), int(sl * S))
    d.rectangle(slope, fill=Y); d.rectangle([slope[0], 0, slope[0] + ol, slope[3]], fill=BLACK); d.rectangle([slope[2] - ol, 0, slope[2], slope[3]], fill=BLACK)
    fit(im, L50.rotate(90, expand=True), (slope[0] + ol + 10, 40, slope[2] - ol - 10, slope[3] - 40), 0.02)   # le long de la pente
    ch = top - Ht + 0.3; cs = (1100, 0, 1100 + int(cw * S), int(ch * S))                       # colonne, faces de côté (larges)
    d.rectangle(cs, fill=BLACK); d.rectangle([cs[0] + ol, cs[1] + ol, cs[2] - ol, cs[3] - ol], fill=Y)
    fit(im, L50.rotate(90, expand=True), (cs[0] + ol + 12, cs[1] + 30, cs[2] - ol - 12, cs[3] - 30), 0.02)
    cf = (1400, 0, 1400 + int(ct * S), int(ch * S)); d.rectangle(cf, fill=BLACK); d.rectangle([cf[0] + ol, cf[1] + ol, cf[2] - ol, cf[3] - ol], fill=Y)
    bw = 2 * xc - ct; ban = (0, 1520, 2048, 1520 + int(round(bh * 2048 / bw)))                 # poutre : même échelle en u et en v
    d.rectangle(ban, fill=BLACK); d.rectangle([ban[0] + 8, ban[1] + 8, ban[2] - 8, ban[3] - 8], fill=Y)
    fit(im, L50, (ban[0] + 200, ban[1] + 6, ban[2] - 200, ban[3] - 6), 0.03)
    d.rectangle([1700, 100, 1750, 150], fill=Y); d.rectangle([1760, 100, 1810, 150], fill=BLACK); d.rectangle([1820, 100, 1870, 150], fill=(40, 40, 44))
    for bx in (tri, slope, cs, cf, ban):
        im = _fabric(im, bx, 9, seed=bx[0] + bx[1])
    im = K.shade_v(im, tri, 1.0, 0.86); im = K.grain(im, 1.0); _save(im, os.path.join(out, 'arche_50f.png'))
    m = Mesh(); rt, rs, rcs, rcf, rb = (R(b, W, H) for b in (tri, slope, cs, cf, ban))
    ry = R((1700, 100, 1750, 150), W, H); rk = R((1760, 100, 1810, 150), W, H); rsk = R((1820, 100, 1870, 150), W, H)
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
