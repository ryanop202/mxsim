"""v41d : sans objets, découpée au bord de la terre, START plus gros. v41c (« fais la minimap aussi, comme d'hab, mais mets USLAND à la place de BAZOWURX ») : map.png de la piste, comme Saint-Georges
(export_stt_night.night_map) : l'arène détourée, START le long de la grille, le logo au-dessus, transparent ailleurs.

Pas de vue de dessus prise en jeu pour Paris : l'image est calculée à partir des fichiers de la piste (sortie du build) :
couleur des tuiles (tilemap + textures de tileinfo), décals posés dans l'ordre du fichier (terre, béton, planches, grates), relief
(ombrage Lambert du terrain), objets bas vus de dessus (boudins, ballots, rampes, grilles de départ, panneaux : triangles des .jm
remplis à la couleur moyenne de leur texture). Le jeu étire map.png sur TOUT le terrain : l'image couvre le terrain entier.
"""
import os
import re
import numpy as np
from PIL import Image, ImageDraw, ImageFont

M = 1024                                   # côté de map.png (px)
CADRE_X1 = 733.0                           # le paddock (à l'est) n'est pas dans la carte
CADRE_MARGE, CADRE_R = 6.0, 18.0           # marge autour du sol, rayon des coins (ft)
OBJ_HAUT, OBJ_LONG = 30.0, 120.0           # objets dessinés : sommet < 30 ft, longueur < 120 ft (pas le stade, ni les bannières)
LUM = np.array([-0.55, 0.75, -0.35])       # lumière (x, y, z) pour l'ombrage du relief
START_BOX = (652.0, 505.0, 676.0, 597.0)   # START devant la grille, le long de la ligne (x0, z0, x1, z1 en ft) ; v41e (« un entre-deux ») : 24 x 92 ft (v41c 16 x 74, v41d 32 x 110)
LOGO_PLEINE_LARGEUR, LOGO_ECART = True, 8.0   # v41e : logo aussi large que la carte, 8 ft au-dessus
DECOUPE_RECT = 32.0                         # v41e : découpe = rectangle calé sur la terre, coins arrondis de 32 ft (0 = suit le bord de la terre)
OBJETS = False                              # v41d (« simplifie la minimap, sans objet ») : plus de boudins / rampes / grilles dessinés
SOL_PAS_TERRE = ('Road', 'Beton', 'Paddock', 'Grass')   # v41d (« découpe autour du terrain ») : la carte = la terre seulement (pas le béton)
DECOUPE_MARGE, DECOUPE_FERME = 1.5, 6       # marge autour de la terre (ft), fermeture des petits creux (cases de 0,58 ft x itérations)
LOGO_BOX = (380.0, 352.0, 620.0, 392.0)    # USLAND au-dessus de l'arène (nord)


def _res(OUT, folder, p):
    return os.path.join(OUT, p.split('/', 1)[1]) if p.startswith('@' + folder + '/') else None


def _jm(path, cache={}):
    if path not in cache:
        L = open(path).read().split('\n'); nv, nt = map(int, L[2].split()[:2])
        V = np.array([[float(a) for a in l.split()[:3]] for l in L[3:3 + nv]])
        ix = []
        for l in L[3 + nv:]:
            if len(ix) >= 3 * nt:
                break
            ix += [int(float(v)) for v in l.split()]
        ix = ix[:3 * nt]
        cache[path] = (V, np.array(ix, int).reshape(-1, 3))
    return cache[path]


def _couleur(path, cache={}):
    if path not in cache:
        a = np.asarray(Image.open(path).convert('RGBA').resize((64, 64)), float); w = a[..., 3:] / 255.0
        cache[path] = tuple(int(c) for c in ((a[..., :3] * w).sum((0, 1)) / max(w.sum(), 1e-6)))
    return cache[path]


def logo_usland(src):
    """logo USLAND (lettres marine sur fond blanc) -> lettres blanches cernées de noir, triangles rouges gardés, fond transparent."""
    from scipy.ndimage import binary_dilation
    a = np.asarray(Image.open(src).convert('RGB'), float)
    lettres = (a.sum(-1) < 300) & (a[..., 2] >= a[..., 0])            # marine
    rouge = (a[..., 0] > 150) & (a[..., 1] < 110) & (a[..., 2] < 140)
    ys, xs = np.nonzero(lettres | rouge); y0, y1, x0, x1 = ys.min() - 12, ys.max() + 12, xs.min() - 12, xs.max() + 12
    lt, rg = lettres[y0:y1, x0:x1], rouge[y0:y1, x0:x1]
    cerne = binary_dilation(lt | rg, iterations=7)
    out = np.zeros(lt.shape + (4,), np.uint8)
    out[cerne] = (0, 0, 0, 255); out[lt] = (255, 255, 255, 255); out[rg] = (225, 30, 60, 255)
    return Image.fromarray(out, 'RGBA')


def make_map(OUT, folder, fl, start, logo_src):
    side = None
    t = open(os.path.join(OUT, 'terrain.hf')).read().split(); s_, lo, hi = float(t[1]), float(t[2]), float(t[3])
    Hm = np.asarray(Image.open(os.path.join(OUT, 'terrain.png')), float) / 65535 * (hi - lo) + lo
    side = (Hm.shape[0] - 1) * s_; k = M / side                         # px / ft
    # 1. couleur des tuiles
    tm = np.fromfile(os.path.join(OUT, 'tilemap'), np.uint8); N = int(np.sqrt(tm.size)); tm = tm.reshape(N, N)
    cols = []
    for b in [b for b in open(os.path.join(OUT, 'tileinfo')).read().split('addtile') if 'name' in b]:
        p = _res(OUT, folder, re.search(r'texture (\S+)', b).group(1))
        cols.append(np.asarray(Image.open(p).convert('RGB'), float).reshape(-1, 3).mean(0) if p and os.path.exists(p) else np.zeros(3))
    cols = np.array(cols + [[0, 0, 0]] * (256 - len(cols))).astype(np.uint8)
    idx = ((np.arange(M) + 0.5) / M * N).astype(int)
    im = Image.fromarray(cols[tm[np.ix_(idx, idx)]]).convert('RGBA')
    # 2. décals dans l'ordre du fichier
    cache = {}
    for l in open(os.path.join(OUT, 'decals')):
        a = l.split()
        if len(a) < 6:
            continue
        x, z, ang, s = float(a[0][1:]), float(a[1][:-1]), float(a[2]), float(a[3])
        p = _res(OUT, folder, a[5])
        if not p or not os.path.exists(p) or x > CADRE_X1 + 30:
            continue
        sz = max(2, int(round(s * k)))
        if (p, sz) not in cache:
            cache[(p, sz)] = Image.open(p).convert('RGBA').resize((sz, sz), Image.LANCZOS)
        tt = cache[(p, sz)].rotate(np.degrees(ang), resample=Image.BILINEAR, expand=True)
        im.alpha_composite(tt, (int(round(x * k - tt.size[0] / 2)), int(round(z * k - tt.size[1] / 2))))
    # 3. relief : ombrage (sol plat = 1)
    from scipy.ndimage import zoom
    Hs = zoom(Hm, M / Hm.shape[0], order=1); gz, gx = np.gradient(Hs, side / M)
    n = np.dstack([-gx, np.ones_like(gx), -gz]); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    lv = LUM / np.linalg.norm(LUM); sh = np.clip(n @ lv, 0, 1) / lv[1]
    rgb = np.asarray(im, float)[..., :3] * np.clip(0.35 + 0.65 * sh, 0.35, 1.35)[..., None]
    im = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), np.full((M, M), 255.0)]).astype(np.uint8), 'RGBA')
    # 4. objets bas vus de dessus (triangles des modèles, couleur moyenne de la texture), dans l'ordre de hauteur
    d = ImageDraw.Draw(im); objs = []
    txt = open(os.path.join(OUT, 'statues')).read() if OBJETS else ''
    for m in re.finditer(r'\[([-0-9.]+) ([-0-9.]+) ([-0-9.]+)\] ([-0-9.]+) (@\S+\.jm) (@\S+\.png)', txt):
        x, y, z, a = (float(m.group(i)) for i in (1, 2, 3, 4)); pj, pp = _res(OUT, folder, m.group(5)), _res(OUT, folder, m.group(6))
        if not pj or not pp or not os.path.exists(pj) or not os.path.exists(pp) or x > CADRE_X1 or not (fl[:, 1].min() - 5 < z < fl[:, 1].max() + 5) or x < fl[:, 0].min() - 5:
            continue
        V, F = _jm(pj)
        if y + V[:, 1].max() > OBJ_HAUT or np.ptp(V[:, 0]) > OBJ_LONG or np.ptp(V[:, 2]) > OBJ_LONG:
            continue
        ex, ez = np.array([np.cos(a), -np.sin(a)]), np.array([np.sin(a), np.cos(a)])
        W = (np.array([x, z]) + np.outer(V[:, 0], ex) + np.outer(V[:, 2], ez)) * k
        objs.append((y + V[:, 1].max(), W, F, _couleur(pp)))
    for _, W, F, c in sorted(objs, key=lambda o: o[0]):
        for f in F:
            d.polygon([tuple(W[i]) for i in f], fill=c + (255,))
    # 5. détourage : le sol de l'arène (sans le paddock), coins arrondis, bord fondu
    from matplotlib.path import Path as MPath
    from scipy.ndimage import distance_transform_edt
    X, Z = np.meshgrid((np.arange(M) + 0.5) / k, (np.arange(M) + 0.5) / k)
    inside = MPath(fl).contains_points(np.c_[X.ravel(), Z.ravel()]).reshape(M, M) & (X <= CADRE_X1)
    if SOL_PAS_TERRE:   # v41d : découpe au bord de la terre (tuiles de terre / sable), creux bouchés, bord lissé
        from scipy.ndimage import binary_closing, binary_fill_holes, gaussian_filter
        noms = [re.search(r'name ([^\r\n]+)', b).group(1).strip() for b in open(os.path.join(OUT, 'tileinfo')).read().split('addtile') if 'name' in b]
        pas_terre = np.isin(tm, [i for i, n_ in enumerate(noms) if n_ in SOL_PAS_TERRE])
        terre = ~pas_terre[np.ix_(idx, idx)] & inside
        terre = binary_fill_holes(binary_closing(terre, np.ones((3, 3)), iterations=DECOUPE_FERME))
        inside = gaussian_filter(terre.astype(float), 2.0) > 0.5
    CADRE_MARGE_ = DECOUPE_MARGE if SOL_PAS_TERRE else CADRE_MARGE
    dout = distance_transform_edt(~inside) / k
    al = np.clip((CADRE_MARGE_ - dout) * k + 0.5, 0, 1)
    if SOL_PAS_TERRE and DECOUPE_RECT:   # v41e (« fais une découpe plus propre autour ») : rectangle aux coins arrondis calé sur la terre
        cs_, rs_ = terre.sum(0), terre.sum(1)                            # colonnes / lignes de terre (les encoches ne comptent pas)
        jx = np.nonzero(cs_ > 0.5 * cs_.max())[0]; iz = np.nonzero(rs_ > 0.5 * rs_.max())[0]
        rx0, rx1, rz0, rz1 = jx[0] / k, (jx[-1] + 1) / k, iz[0] / k, (iz[-1] + 1) / k; rr_ = DECOUPE_RECT
        qx, qz = np.abs(X - (rx0 + rx1) / 2) - ((rx1 - rx0) / 2 - rr_), np.abs(Z - (rz0 + rz1) / 2) - ((rz1 - rz0) / 2 - rr_)
        sd_ = np.hypot(np.maximum(qx, 0), np.maximum(qz, 0)) + np.minimum(np.maximum(qx, qz), 0) - rr_   # < 0 dedans (ft)
        al = np.clip(-sd_ * k + 0.5, 0, 1)
    im.putalpha(Image.fromarray((al * 255).astype(np.uint8)))
    # 6. START le long de la grille (se lit de bas en haut) et le logo USLAND au-dessus
    fnt = ImageFont.truetype('C:/Windows/Fonts/impact.ttf', 200); sw = 14
    tb = ImageDraw.Draw(Image.new('L', (1, 1))).textbbox((0, 0), 'START', font=fnt, stroke_width=sw)
    tx = Image.new('RGBA', (tb[2] - tb[0], tb[3] - tb[1]), (0, 0, 0, 0))
    ImageDraw.Draw(tx).text((-tb[0], -tb[1]), 'START', font=fnt, fill=(255, 255, 255, 255), stroke_width=sw, stroke_fill=(0, 0, 0, 255))
    lg_ = logo_usland(logo_src); box_ = LOGO_BOX
    if SOL_PAS_TERRE and DECOUPE_RECT and LOGO_PLEINE_LARGEUR:   # v41e (« le logo USLAND aussi large que la minimap ») : largeur du cadre
        hl_ = (rx1 - rx0) * lg_.height / lg_.width; box_ = (rx0, rz0 - LOGO_ECART - hl_, rx1, rz0 - LOGO_ECART)
    for img, (X0, Z0, X1, Z1), rot in ((tx, START_BOX, 90), (lg_, box_, 0)):
        img = img.rotate(rot, expand=True); f_ = min((X1 - X0) * k / img.width, (Z1 - Z0) * k / img.height)
        img = img.resize((max(1, int(img.width * f_)), max(1, int(img.height * f_))), Image.LANCZOS)
        im.alpha_composite(img, (int(round((X0 + X1) / 2 * k - img.width / 2)), int(round((Z0 + Z1) / 2 * k - img.height / 2))))
    im.save(os.path.join(OUT, 'map.png'))
    return dict(px_par_ft=round(k, 3), objets=len(objs), arene_px=int(round((min(CADRE_X1, fl[:, 0].max()) - fl[:, 0].min()) * k)))
