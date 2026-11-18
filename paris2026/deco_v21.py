"""v21 (version Zion), photos de Paris 2025 envoyées par l'utilisateur :
  (1) virages : « des gros murs de paille enroulés d'une bâche, encastrés à l'extérieur du virage, avec des poteaux et des filets ;
      il fait un quart du virage » puis (v21b, « t'as fait vite ») : « des bâches qui brillent ; comme les boudins qu'on a faits mais
      en forme de triangle, remplis de 3 cylindres ; autour des filets, rien d'écrit sur les filets ; les filets devant, les poteaux
      derrière, tendus avec des ficelles » : boudin triangulaire (enveloppe de 3 cylindres de 1,3 ft de rayon, 2 en bas + 1 dessus,
      5,2 x 4,9 ft) en bâche grise brillante, encastré dans le dos du berm ; filet rouge maillé (transparent, sans inscription) juste
      derrière le haut du boudin, poteaux noirs derrière le filet, une ficelle de chaque poteau au sol derrière ; premier quart de tour
      (90°) de chaque virage à berm (tout le virage pour un 90°) ;
  (2) « les ballots : un demi-cercle, un U, creux à l'intérieur, la couleur du sponsor avec son logo, un socle noir et autour un truc
      noir ; taille d'un ballot normal ; pour l'instant mets les noirs » : tunnel en U de 3,6 x 2,6 x 2,3 ft (socle compris), coque de
      0,28 ft, socle et tranches noirs ; SPONSORS = couleurs + logos prêts (noir par défaut) ;
  (3) « l'arche 50 Factory pile comme ça : un triangle, un petit truc en carton dessus avec le logo qui monte vers le ciel, le gros
      50 Factory au-dessus, symétrique » ; v21b : « les triangles sont dans le sens de la piste, sur le côté ; la colonne mange le
      logo ; un contour noir sur les triangles ; centre les logos » : pieds = prismes triangulaires jaunes dont le triangle (7 ft de
      base le long de la piste, 6 ft de haut, 2,5 ft d'épaisseur) se voit depuis le côté, contour noir, logo centré en bas ; colonne
      de carton sur la pointe (logo vertical centré sur la partie au-dessus du triangle, des deux côtés) ; bannière 50 FACTORY en haut
      (42,5 x 3,5 ft, bas à 12,5 ft), contour noir, face aux pilotes.
FORMES CRÉÉES d'après les photos (pas des mesures). Repère des modèles (doc 12) : y vers le haut, +z = l'avant.
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import hab_kit as K                       # noqa: E402
from hab_kit import Mesh, R, logo, fit    # noqa: E402

MAT_MAT = (0, 0, 0, 0, 0)
MAT_BACHE = (20, 0.35, 0.4, 0.4, 0.4)
BLACK = (20, 20, 22)


def _save(img, path):
    img.convert('RGB').save(path, optimize=True)


def _face(m, P, UV, N):
    """polygone convexe (3 ou 4 points) avec normales par sommet ; l'ordre est corrigé pour que la face se voie du côté des normales."""
    P = [np.asarray(p, float) for p in P]; N = [np.asarray(n, float) / (np.linalg.norm(n) or 1.0) for n in N]; UV = list(UV)
    if np.dot(np.cross(P[1] - P[0], P[2] - P[0]), sum(N)) < 0:
        P, UV, N = P[::-1], UV[::-1], N[::-1]
    for k in range(1, len(P) - 1):
        m.tri([P[0], P[k], P[k + 1]], [UV[0], UV[k], UV[k + 1]], [N[0], N[k], N[k + 1]])


# ================================================================ (2) ballot creux en U
BU = dict(L=4.2, a=1.15, hs=0.7, t=0.10, tb=0.22, lip=0.15)    # v21b (« la bâche qui fait l'arc est plus fine ; un peu plus longues ») : 0,28 -> 0,10 ft, 3,6 -> 4,2 ft
SPONSORS = dict(noir=(BLACK, None, None), honda=((204, 8, 18), 'honda', None), yamaha=((22, 50, 140), 'yamaha', None),
                seong=((0, 160, 172), 'seong', (10, 10, 10)), cinquante=((249, 229, 42), '50factory', None), monster=((16, 16, 18), 'monster', None))


def _u_curve(a, hs, y0, n=26):
    """section en U renversé, du pied gauche (z = -a) au pied droit : (z, y, nz, ny) + abscisse curviligne s."""
    pts = [(-a, y, -1.0, 0.0) for y in np.linspace(y0, y0 + hs, 4)]
    pts += [(a * np.cos(t), y0 + hs + a * np.sin(t), np.cos(t), np.sin(t)) for t in np.linspace(np.pi, 0, n)[1:-1]]
    pts += [(a, y, 1.0, 0.0) for y in np.linspace(y0 + hs, y0, 4)]
    s = np.r_[0, np.cumsum([np.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)])]
    return pts, s


def bale_u(out, key='noir'):
    """tunnel en U (axe = x), socle noir ; écrit bale_u.jm / .shp (communs) et bale_u_<key>.png."""
    body, lg, ink = SPONSORS[key]; L, a, hs, t, tb, lip = (BU[k] for k in ('L', 'a', 'hs', 't', 'tb', 'lip'))
    po, so = _u_curve(a, hs, tb); pi_, si = _u_curve(a - t, hs, tb); stot = so[-1]
    W, H = 1024, 2048; kpx = W / L; rows = int(round(stot * kpx))                     # même échelle en u et en v : logos jamais déformés
    im = Image.new('RGB', (W, H), body); d = ImageDraw.Draw(im)
    a_ = np.asarray(im, float); y_ = np.arange(H)[:, None]                           # ombre cuite : pieds plus sombres que le dessus
    sh = 0.78 + 0.22 * np.sin(np.pi * np.clip(y_ / rows, 0, 1)); a_[:rows] *= sh[:rows, :, None]; im = Image.fromarray(np.clip(a_, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    band = int(0.025 * W); d.rectangle([0, 0, band, rows], fill=BLACK); d.rectangle([W - band, 0, W, rows], fill=BLACK)   # bord noir
    if lg:
        lo = K.logo(lg) if ink is None else K.tint(K.logo(lg), ink)
        sc = int(1.05 * kpx); hb = int(0.42 * kpx)
        fit(im, lo.rotate(180, expand=True), (band + 40, sc - hb, W - band - 40, sc + hb), 0.04)      # flanc -z : vu de dehors, à l'endroit
        sc2 = int((stot - 1.05) * kpx); fit(im, lo, (band + 40, sc2 - hb, W - band - 40, sc2 + hb), 0.04)  # flanc +z
    inn = tuple(int(c * 0.42) for c in body) if key != 'noir' else (12, 12, 13)
    d.rectangle([0, 1440, W, 1700], fill=inn); d.rectangle([0, 1720, W, 1800], fill=BLACK)
    im = K.grain(im, 1.5); _save(im, os.path.join(out, 'bale_u_%s.png' % key))
    m = Mesh(); r_out = R((0, 0, W, rows), W, H); r_in = R((0, 1440, W, 1700), W, H); blk = R((0, 1720, W, 1800), W, H)
    uv = lambda r, fu, fv: (r[0] + (r[2] - r[0]) * fu, r[3] - (r[3] - r[1]) * fv)
    for P_, S_, rr, sg in ((po, so, r_out, 1.0), (pi_, si, r_in, -1.0)):
        for i in range(len(P_) - 1):
            (za, ya, nza, nya), (zb, yb, nzb, nyb) = P_[i], P_[i + 1]
            fa, fb = S_[i] / S_[-1], S_[i + 1] / S_[-1]
            _face(m, [(-L / 2, ya, za), (L / 2, ya, za), (L / 2, yb, zb), (-L / 2, yb, zb)],
                  [uv(rr, 0, fa), uv(rr, 1, fa), uv(rr, 1, fb), uv(rr, 0, fb)],
                  [(0, sg * nya, sg * nza)] * 2 + [(0, sg * nyb, sg * nzb)] * 2)
    for sx in (-1, 1):                                                                # tranches noires (le U vu du bout)
        for i in range(len(po) - 1):
            _face(m, [(sx * L / 2, po[i][1], po[i][0]), (sx * L / 2, po[i + 1][1], po[i + 1][0]), (sx * L / 2, pi_[i + 1][1], pi_[i + 1][0]),
                      (sx * L / 2, pi_[i][1], pi_[i][0])], [blk[:2]] * 4, [(sx, 0, 0)] * 4)
    m.box((-L / 2 - lip, 0, -a - lip), (L / 2 + lip, tb, a + lip), blk, 'xXzZY')    # socle noir
    m.write(os.path.join(out, 'bale_u.jm'), MAT_BACHE)
    K.shp(os.path.join(out, 'bale_u.shp'), [(-1.1, 1.0, 0), (0, 1.0, 0), (1.1, 1.0, 0)], 1.1)
    return 'bale_u.jm', 'bale_u_%s.png' % key, 'bale_u.shp'


# ================================================================ (3) arche 50 Factory
AR = dict(xc=20.0, B=7.0, Ht=6.0, T=2.5, cw=1.6, ct=0.6, Hb=12.5, bh=3.5)


def arche_50f(out):
    """repère : +z = sens de la piste ; pieds à x = +-xc ; triangles dans le plan (z, y), vus depuis le côté de la piste."""
    xc, B, Ht, T, cw, ct, Hb, bh = (AR[k] for k in ('xc', 'B', 'Ht', 'T', 'cw', 'ct', 'Hb', 'bh'))
    Y = (249, 222, 30); W, H = 2048, 1024; im = Image.new('RGB', (W, H), Y); d = ImageDraw.Draw(im); L50 = logo('50factory'); ol = 14
    tri = (0, 0, 700, 600)                                                              # triangle : 100 px / ft ; contour noir
    d.rectangle(tri, fill=BLACK); poly = [(0, 600), (700, 600), (350, 0)]
    d.polygon(poly, fill=BLACK); d.polygon([(ol * 1.9, 600 - ol), (700 - ol * 1.9, 600 - ol), (350, ol * 2.2)], fill=Y)
    fit(im, L50, (350 - 205, 395, 350 + 205, 565), 0.02)                               # logo centré dans le bas du triangle
    slope = (720, 0, 970, 700); d.rectangle(slope, fill=Y); d.rectangle([720, 0, 720 + ol, 700], fill=BLACK); d.rectangle([970 - ol, 0, 970, 700], fill=BLACK)
    fit(im, L50.rotate(90, expand=True), (720 + ol + 12, 60, 970 - ol - 12, 640), 0.02)    # v21b : le logo monte le long de la pente
    ch = Hb - (Ht - 0.8); col = (1000, 0, 1160, int(ch * 100))                         # colonne : 100 px / ft
    d.rectangle(col, fill=BLACK); d.rectangle([col[0] + 8, col[1] + 8, col[2] - 8, col[3] - 8], fill=Y)
    vis = int((Hb - (Ht + 0.4)) * 100)                                                  # partie visible au-dessus de la pointe
    fit(im, L50.rotate(90, expand=True), (col[0] + 14, col[1] + 40, col[2] - 14, vis - 30), 0.02)
    bw = 2 * (xc + T / 2); ban = (0, 780, 2048, 780 + int(round(bh * 2048 / bw)))      # bannière : même échelle en u et en v
    d.rectangle(ban, fill=BLACK); d.rectangle([ban[0] + 8, ban[1] + 8, ban[2] - 8, ban[3] - 8], fill=Y)
    fit(im, L50, (ban[0] + 300, ban[1] + 10, ban[2] - 300, ban[3] - 10), 0.04)
    d.rectangle([1200, 100, 1250, 150], fill=Y); d.rectangle([1260, 100, 1310, 150], fill=BLACK)
    im = K.shade_v(im, tri, 1.0, 0.84); im = K.shade_v(im, col, 1.0, 0.9); im = K.shade_v(im, ban, 1.0, 0.92); im = K.grain(im, 1.0)
    _save(im, os.path.join(out, 'arche_50f.png'))
    m = Mesh(); rt = R(tri, W, H); rs = R(slope, W, H); rc = R(col, W, H); rb = R(ban, W, H); ry = R((1200, 100, 1250, 150), W, H)
    rk = R((1260, 100, 1310, 150), W, H)
    for sx in (-1, 1):
        x0, x1 = sx * xc - T / 2, sx * xc + T / 2
        for xf, nx in ((x0, -1.0), (x1, 1.0)):                                          # triangles (vus du côté), jamais en miroir
            fu = (lambda z: (B / 2 - z) / B) if nx > 0 else (lambda z: (z + B / 2) / B)
            UVt = [(rt[0] + (rt[2] - rt[0]) * fu(z), rt[1] + (rt[3] - rt[1]) * y / Ht) for z, y in ((-B / 2, 0), (B / 2, 0), (0, Ht))]
            _face(m, [(xf, 0, -B / 2), (xf, 0, B / 2), (xf, Ht, 0)], UVt, [(nx, 0, 0)] * 3)
        for zf, nz in ((-B / 2, -1.0), (B / 2, 1.0)):                                   # pentes (vers / dos aux pilotes), bords noirs
            n = (0, B / 2, nz * Ht); lo_, hi_ = (rs[2], rs[0]) if nz < 0 else (rs[0], rs[2])   # vu de face : jamais en miroir
            _face(m, [(x0, 0, zf), (x1, 0, zf), (x1, Ht, 0), (x0, Ht, 0)], [(lo_, rs[1]), (hi_, rs[1]), (hi_, rs[3]), (lo_, rs[3])], [n] * 4)
        xm = sx * xc                                                                    # colonne de carton, logo vers le ciel des 2 côtés
        m.box((xm - ct / 2, Ht - 0.8, -cw / 2), (xm + ct / 2, Hb, cw / 2), ry, 'xXzZ', {'x': rc, 'X': rc})
    m.box((-bw / 2, Hb, -0.6), (bw / 2, Hb + bh, 0.6), rk, 'xXzZYy', {'z': rb, 'Z': rb})
    m.write(os.path.join(out, 'arche_50f.jm'), MAT_MAT)
    sph = [(sx * xc, 1.3, dz) for sx in (-1, 1) for dz in (-2.2, 0.0, 2.2)] + [(sx * xc, 3.4, 0) for sx in (-1, 1)]
    K.shp(os.path.join(out, 'arche_50f.shp'), sph, 1.3)
    return 'arche_50f.jm', 'arche_50f.png', 'arche_50f.shp'


# ================================================================ (1) boudins triangulaires bâchés + filets rouges
WV = dict(rb=1.3, sink=0.5, vis=3.0, taper=3.0, back=2.0, post=8.0, net_h=4.6, net_low=1.6, net_off=0.55, post_off=0.28,
          post_up=0.3, guy=4.0, tile=4.0)
NET_RED = ((120, 8, 12, 255), (196, 22, 28, 255), (150, 12, 18, 255), (236, 74, 70, 255), (226, 62, 60, 255))


def _tri_section(rb, n=40):
    """enveloppe convexe de 3 cylindres (2 en bas posés au sol, 1 dessus) = section du boudin, du pied intérieur au pied
    extérieur par-dessus : (d, y, nd, ny) ; d vers l'extérieur du virage."""
    C = np.array([(-rb, rb), (rb, rb), (0.0, rb + rb * np.sqrt(3))]); a = np.linspace(0, 2 * np.pi, 360, endpoint=False)
    P = np.vstack([np.c_[cx + rb * np.cos(a), cy + rb * np.sin(a)] for cx, cy in C])
    phi = np.radians(np.linspace(240, -60, 400)); Nn = np.c_[np.cos(phi), np.sin(phi)]
    Q = P[np.argmax(P @ Nn.T, axis=0)]                                                    # point d'appui pour chaque normale
    keep = np.r_[True, np.hypot(*np.diff(Q, axis=0).T) > 1e-6]; Q = Q[keep]
    L = np.r_[0, np.cumsum(np.hypot(*np.diff(Q, axis=0).T))]; s = np.linspace(0, L[-1], n)
    Q = np.c_[np.interp(s, L, Q[:, 0]), np.interp(s, L, Q[:, 1])]
    t = np.gradient(Q, axis=0); nn = np.c_[-t[:, 1], t[:, 0]]; nn /= np.linalg.norm(nn, axis=1, keepdims=True)
    if nn[n // 2, 1] < 0:
        nn = -nn
    return np.c_[Q, nn]


def tarp_texture(out):
    """bâche grise BRILLANTE (comme nos boudins) : u = le long (8 ft, raccordable), v = le tour du boudin (pied intérieur en bas de
    l'image -> pied extérieur en haut) ; plis doux, reflet peint sur l'épaule côté piste (la lumière vient d'en haut)."""
    from scipy.ndimage import gaussian_filter
    W, H = 512, 1024; rng = np.random.default_rng(21)
    n = gaussian_filter(rng.normal(0, 1, (H, W)), (6, 40), mode='wrap'); n /= n.std()
    f = gaussian_filter(rng.normal(0, 1, (H, W)), (30, 12), mode='wrap'); f /= f.std()
    v = 1 - (np.arange(H) + 0.5)[:, None] / H                                           # 0 = pied intérieur, 1 = pied extérieur
    hi = 0.85 * np.exp(-((v - 0.36) / 0.07) ** 2) + 0.35 * np.exp(-((v - 0.55) / 0.06) ** 2)   # reflets (épaule, haut)
    sh = 0.80 + 0.20 * np.sin(np.pi * v)                                                 # pieds plus sombres
    base = np.array([116.0, 119, 124]); a = base * sh[..., None] + (hi * 95)[..., None] + (n * 5 + f * 6)[..., None]
    a += rng.normal(0, 1.2, a.shape); _save(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), os.path.join(out, 'bache_grise.png'))
    return 'bache_grise.png'


def net_texture(out):
    """filet rouge maillé, sans inscription (mêmes mailles que les filets de Saint-Thibéry / Saint-Georges, stt_props), transparent
    entre les mailles ; en bas : noir des poteaux et des ficelles."""
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
    import stt_props as SPn
    im = SPn.net_ribbon_texture(NET_RED, cell=0.16, strand=2, knot=4); a = np.array(im)
    NR = SPn.NETR['NR']; a[NR + 32:, :, :3] = (24, 24, 26); a[NR + 32:, :, 3] = 255
    Image.fromarray(a, 'RGBA').save(os.path.join(out, 'filet_rouge.png'), optimize=True)
    TH = SPn.NETR['TH']; return 'filet_rouge.png', (1 - (NR - 1) / TH, 1.0), (0.5, 1 - (NR + 64) / TH)


def turn_wall(out, k, g, Hf, f0, f1, net_tex, vnet, uv_blk):
    """boudin triangulaire + filet + poteaux + ficelles d'un virage, de la fraction f0 à f1 ; Hf(x, z) = hauteur du terrain.
    Modèles en coordonnées du virage : origine au centre (sol plat), lacet 0."""
    sg = 1.0 if g['ang'] > 0 else -1.0; th_in = g['t0'] + sg * np.pi / 2; ang = np.radians(g['ang'])
    th = lambda f: th_in - ang * f
    cx, cz = g['cx'], g['cz']; h0 = float(np.ravel(Hf(cx, cz))[0]); H1 = lambda x, z: float(np.ravel(Hf(x, z))[0])
    tm = th((f0 + f1) / 2); rr = np.arange(g['r'], g['r'] + 40, 0.5)
    r_crest = float(rr[int(np.argmax(Hf(cx + np.cos(tm) * rr, cz + np.sin(tm) * rr)))])
    rb = WV['rb']; sec = _tri_section(rb); Wd = sec[:, 0].max() - sec[:, 0].min(); Hh = sec[:, 1].max(); rc = r_crest + WV['back']
    L_arc = abs(ang * (f1 - f0)) * rc; ns = max(8, int(L_arc / 1.5)); fs = np.linspace(f0, f1, ns + 1); sarc = np.linspace(0, L_arc, ns + 1)
    base = np.empty(len(fs)); scl = np.empty(len(fs))
    for i, f in enumerate(fs):
        e = np.array([np.cos(th(f)), np.sin(th(f))]); dd = np.linspace(-Wd / 2, Wd / 2, 7)
        hh = Hf(cx + e[0] * (rc + dd), cz + e[1] * (rc + dd)); rr_ = r_crest + np.linspace(-4, 4, 9)
        hc = float(np.max(Hf(cx + e[0] * rr_, cz + e[1] * rr_)))
        base[i] = max(hh.min() - WV['sink'], hc + WV['vis'] - Hh)                        # encastré dans le dos du berm
        e_ = min(sarc[i], L_arc - sarc[i]) / WV['taper']; e_ = np.clip(e_, 0, 1); scl[i] = 0.35 + 0.65 * np.sqrt(e_ * (2 - e_))
    top = base + Hh * scl
    m = Mesh(); ring = []
    for i, f in enumerate(fs):
        e = np.array([np.cos(th(f)), np.sin(th(f))]); row = []
        for j, (d, y, nd, ny) in enumerate(sec):
            r_ = rc + d * scl[i]; row.append(((e[0] * r_ + cx - cx, base[i] + y * scl[i] - h0, e[1] * r_), (e[0] * nd, ny, e[1] * nd),
                                              (sarc[i] / 8.0, j / (len(sec) - 1))))
        ring.append(row)
    for i in range(len(ring) - 1):
        for j in range(len(sec) - 1):
            a_, b_, c_, d_ = ring[i][j], ring[i + 1][j], ring[i + 1][j + 1], ring[i][j + 1]
            _face(m, [a_[0], b_[0], c_[0], d_[0]], [a_[2], b_[2], c_[2], d_[2]], [a_[1], b_[1], c_[1], d_[1]])
    for i, sgn in ((0, -1), (len(ring) - 1, 1)):                                        # bouts arrondis (section réduite) + fond
        tdir = np.array([-np.sin(th(fs[i])), np.cos(th(fs[i]))]) * np.sign(-ang) * sgn; nrm = (tdir[0], 0.0, tdir[1])
        pts = [q[0] for q in ring[i]]; cen = np.mean(pts, axis=0)
        for j in range(len(pts) - 1):
            _face(m, [cen, pts[j], pts[j + 1]], [(0.5, 0.5)] * 3, [nrm] * 3)
    m.write(os.path.join(out, 'mur_virage_%d.jm' % k), MAT_BACHE)
    K.shp(os.path.join(out, 'mur_virage_%d.shp' % k),
          [(np.cos(th(f)) * rc, base[i] + Hh * 0.45 - h0, np.sin(th(f)) * rc) for i, f in enumerate(fs) if i % 2 == 0], 2.2)
    # filet : juste derrière le haut du boudin, du bas caché dans le boudin à net_h au-dessus ; tuiles de 4 ft (u dans [0, 1])
    ok = np.nonzero(scl > 0.97)[0]; s0_, s1_ = sarc[ok[0]], sarc[ok[-1]]; rn = rc + WV['net_off']; rp = rn + WV['post_off']
    sv = np.linspace(s0_, s1_, max(2, int((s1_ - s0_) / 1.0) + 1)); fv = np.interp(sv, sarc, fs); tv = np.interp(sv, sarc, top)
    from scipy.ndimage import gaussian_filter1d
    tv = gaussian_filter1d(tv, 2.0, mode='nearest'); bot = tv - WV['net_low'] - h0; upp = tv + WV['net_h'] - WV['net_low'] - h0
    n2 = Mesh(); Vb, Vt = vnet; TL = WV['tile']; sph = []
    P2 = lambda f, r_: (np.cos(th(f)) * r_, np.sin(th(f)) * r_)
    for i in range(len(sv) - 1):
        cuts = [sv[i]] + [q * TL for q in range(int(sv[i] // TL) + 1, int(sv[i + 1] // TL) + 1) if sv[i] < q * TL < sv[i + 1]] + [sv[i + 1]]
        for sa, sb in zip(cuts[:-1], cuts[1:]):
            fa, fb = np.interp(sa, sv, fv), np.interp(sb, sv, fv); ba, bb = np.interp(sa, sv, bot), np.interp(sb, sv, bot)
            ta, tb = np.interp(sa, sv, upp), np.interp(sb, sv, upp); q0 = np.floor(sa / TL + 1e-9); ua, ub = sa / TL - q0, sb / TL - q0
            (xa, za), (xb, zb) = P2(fa, rn), P2(fb, rn); e = np.array([np.cos(th((fa + fb) / 2)), 0, np.sin(th((fa + fb) / 2))])
            Q = [(xa, ba, za), (xb, bb, zb), (xb, tb, zb), (xa, ta, za)]; UV = [(ua, Vb), (ub, Vb), (ub, Vt), (ua, Vt)]
            _face(n2, Q, UV, [-e] * 4); _face(n2, Q, UV, [e] * 4)                       # filet des deux côtés
    for s_ in sv[::2]:
        f = np.interp(s_, sv, fv); x_, z_ = P2(f, rn); sph += [(x_, np.interp(s_, sv, bot) + h_, z_) for h_ in (2.0, 3.4, 4.8)]
    npst = max(2, int(round((s1_ - s0_) / WV['post'])) + 1)
    for s_ in np.linspace(s0_, s1_, npst):                                              # poteaux noirs derrière le filet + ficelle
        f = np.interp(s_, sv, fv); x_, z_ = P2(f, rp); yb_ = np.interp(s_, sarc, base) - h0; yt_ = np.interp(s_, sv, upp) + WV['post_up']
        n2.tube((x_, yb_, z_), (x_, yt_, z_), 0.11, (uv_blk[0], uv_blk[1], uv_blk[0] + 0.001, uv_blk[1] + 0.001), 8)
        gx, gz = P2(f, rp + WV['guy']); gy = H1(gx + cx, gz + cz) - h0 - 0.2
        n2.tube((x_, yt_ - 0.2, z_), (gx, gy, gz), 0.025, (uv_blk[0], uv_blk[1], uv_blk[0] + 0.001, uv_blk[1] + 0.001), 4, caps=False)
    n2.write(os.path.join(out, 'filet_virage_%d.jm' % k), MAT_MAT)
    K.shp(os.path.join(out, 'filet_virage_%d.shp' % k), sph, 0.9, par=(1.0, 85, 4))
    return dict(origin=(cx, cz), r_wall=round(rc, 1), arc_ft=round(L_arc, 1), posts=npst, h0=round(h0, 2),
                files=(('mur_virage_%d.jm' % k, 'bache_grise.png', 'mur_virage_%d.shp' % k),
                       ('filet_virage_%d.jm' % k, net_tex, 'filet_virage_%d.shp' % k)))
