"""Modèles de l'habillage « comme en vrai » de Paris, d'après les photos du Supercross de Paris (paris2026/refs/photos2025,
local). Tout est créé ici (formes nouvelles, pas des mesures), sauf : les boudins et les poteaux ronds de Saint-Georges
(modèles repris, nouvelles peaux). Non testé en jeu.

  tuff_arc      demi-tonneau de 3,9 ft (les « tuff blocks » des photos), une peau par sponsor, collision
  boudin / boudin3   boudins de 6 / 18 ft de Saint-Georges, peaux Motul, Seong, Honda, Thor, « R »
  mur           mur de virage : ballots bâchés gris + bandeau du sponsor, 8 ft, collision
  filet         filet derrière les virages : poteaux rembourrés + filet + bandeau Venum, 8 ft
  amv_jupe      bâche AMV du saut du milieu (panneau central + 2 triangles)
  rampe_honda   rampe en acier + coins rouges Honda sur l'appel du saut d'arrivée (suit le terrain)
  fmx_jupe      habillage noir Venum des tremplins FMX (sous le tremplin acier ramp_50)
  minerva       portique Minerva Oil avec podium / rampe (collision)
  arche_50      arche jaune 50 Factory
  depart        bandeau START (Venum / Monster) sur treillis + mur de fond
  finish        panneau FINISH suspendu au toit
  canette       canette Monster gonflable géante
  semi_<équipe> camion du paddock (tracteur + remorque + auvent), provisoire
"""
import os
import numpy as np
from PIL import Image, ImageDraw
import hab_kit as K
from hab_kit import Mesh, R, logo, fit

MAT_MAT = (0, 0, 0, 0, 0)
MAT_BACHE = (20, 0.35, 0.4, 0.4, 0.4)              # bâche PVC un peu brillante (comme les boudins de Saint-Georges)


def _save(img, path, alpha=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    (img if alpha else img.convert('RGB')).save(path)


# ---------------------------------------------------------------- tuff blocks (demi-tonneaux)
TUFF = dict(yamaha=((24, 52, 140), 'yamaha', None, (12, 12, 14)), honda=((214, 22, 28), 'honda', None, (120, 10, 14)),
            seong=((0, 160, 172), 'seong', (10, 10, 10), (205, 30, 36)), amv=((245, 245, 242), 'amv', None, (0, 150, 64)),
            monster=((14, 14, 15), 'monster', None, (14, 14, 15)), motul=((214, 22, 28), 'motul', None, (150, 12, 16)),
            venum=((14, 14, 15), 'venum', None, (60, 60, 62)), thor=((120, 122, 126), 'thor', None, (60, 60, 62)))
ARC_L, ARC_W, ARC_H = 1.95, 1.2, 1.5


def tuff_arc(out):
    m = Mesh(); W = H = 512; n = 14
    pan, inn, rim = R((0, 0, 512, 262), W, H), R((4, 276, 246, 330), W, H), R((264, 276, 506, 330), W, H)
    th = np.linspace(0, np.pi, n + 1)
    pt = lambda t, k=1.0: (-ARC_W * k * np.cos(t), ARC_H * k * np.sin(t))
    nr = lambda t: np.array([0, np.sin(t) / ARC_H, -np.cos(t) / ARC_W]) / np.hypot(np.sin(t) / ARC_H, np.cos(t) / ARC_W)
    seg = np.hypot(np.diff([pt(t)[0] for t in th]), np.diff([pt(t)[1] for t in th])); s = np.r_[0, np.cumsum(seg)]; half = s[-1] / 2
    for i in range(n):
        (z0, y0), (z1, y1) = pt(th[i]), pt(th[i + 1])
        a_side = th[i + 1] <= np.pi / 2 + 1e-9
        # hauteur dans le panneau : 0 au pied, 1 au faîte, des deux côtés ; u vers la droite de celui qui regarde
        f0, f1 = (s[i] / half, s[i + 1] / half) if a_side else ((s[-1] - s[i]) / half, (s[-1] - s[i + 1]) / half)
        v0, v1 = pan[1] + (pan[3] - pan[1]) * f0, pan[1] + (pan[3] - pan[1]) * f1
        ua, ub = (pan[2], pan[0]) if a_side else (pan[0], pan[2])            # u à x = -L et à x = +L
        P = [(-ARC_L, y0, z0), (ARC_L, y0, z0), (ARC_L, y1, z1), (-ARC_L, y1, z1)]
        UV = [(ua, v0), (ub, v0), (ub, v1), (ua, v1)]; N = [nr(th[i]), nr(th[i]), nr(th[i + 1]), nr(th[i + 1])]
        if a_side:                                                           # sens direct vu de l'extérieur
            m.tri([P[1], P[0], P[3]], [UV[1], UV[0], UV[3]], [N[1], N[0], N[3]]); m.tri([P[1], P[3], P[2]], [UV[1], UV[3], UV[2]], [N[1], N[3], N[2]])
        else:
            m.tri([P[1], P[0], P[3]], [UV[1], UV[0], UV[3]], [N[1], N[0], N[3]]); m.tri([P[1], P[3], P[2]], [UV[1], UV[3], UV[2]], [N[1], N[3], N[2]])
        # intérieur (sombre) et tranches des deux bouts
        (zi0, yi0), (zi1, yi1) = pt(th[i], 0.86), pt(th[i + 1], 0.86)
        m.quad([(-ARC_L, yi0, zi0), (ARC_L, yi0, zi0), (ARC_L, yi1, zi1), (-ARC_L, yi1, zi1)], inn)
        m.quad([(ARC_L, y0, z0), (ARC_L, yi0, zi0), (ARC_L, yi1, zi1), (ARC_L, y1, z1)], rim)
        m.quad([(-ARC_L, yi0, zi0), (-ARC_L, y0, z0), (-ARC_L, y1, z1), (-ARC_L, yi1, zi1)], rim)
    # contrôle du sens des faces de la coque (normale géométrique = normale donnée)
    V = np.array(m.V); I = np.array(m.I).reshape(-1, 3)
    g = np.cross(V[I[:, 1], :3] - V[I[:, 0], :3], V[I[:, 2], :3] - V[I[:, 0], :3])
    bad = np.einsum('ij,ij->i', g, V[I[:, 0], 3:6]) < 0
    I[bad] = I[bad][:, ::-1]; m.I = I.ravel().tolist()
    m.write(os.path.join(out, 'tuff_arc.jm'), MAT_BACHE)
    K.shp(os.path.join(out, 'tuff_arc.shp'), [(-1.15, 0.72, 0), (0, 0.72, 0), (1.15, 0.72, 0)], 0.78)
    for name, (bg, lg, ink, end) in TUFF.items():
        im = Image.new('RGB', (W, H), bg); d = ImageDraw.Draw(im)
        if name == 'amv':                                                    # blanc, cadre vert (photos)
            d.rectangle([0, 0, 511, 261], fill=(0, 150, 64)); d.rounded_rectangle([14, 14, 497, 247], 18, fill=bg)
        if name == 'seong':                                                  # bleu-vert, bande noire, SEONG + emblème
            d.rectangle([0, 60, 511, 200], fill=(10, 10, 10))
            fit(im, K.hstack([logo('seong_icon').resize((120, 134)), logo('seong')], 40), (20, 60, 492, 200), 0.12)
        elif name == 'monster':
            fit(im, K.hstack([logo('monster_claw'), logo('monster_text')], 30), (20, 30, 492, 232), 0.06)
        else:
            lgo = logo(lg) if ink is None else K.tint(logo(lg), ink)
            fit(im, lgo, (20, 30, 492, 232), 0.08)
        im = K.shade_v(im, (0, 0, 512, 262), 1.0, 0.74)
        d = ImageDraw.Draw(im); d.rectangle([0, 266, 255, 340], fill=(16, 16, 18)); d.rectangle([256, 266, 511, 340], fill=end)
        _save(K.grain(im, 2.0), os.path.join(out, 'tuff_arc_%s.png' % name))
    return list(TUFF)


# ---------------------------------------------------------------- boudins (modèles de Saint-Georges, nouvelles peaux)
BOUDIN = dict(motul=((214, 22, 28), 'motul', None), seong=((0, 160, 172), 'seong', (10, 10, 10)), honda=((214, 22, 28), 'honda', None),
              thor=((120, 122, 126), 'thor', None), r=((214, 22, 28), 'r', None), monster=((14, 14, 15), 'monster_text', None))


def boudins(out):
    for long3, W, L, nlogo in ((False, 1024, 6.0, 1), (True, 2048, 18.0, 3)):
        for name, (bg, lg, ink) in BOUDIN.items():
            row = Image.new('RGB', (int(L * 142), 512), bg); lgo = logo(lg) if ink is None else K.tint(logo(lg), ink)
            rw = row.size[0] / nlogo
            for k in range(nlogo):
                if name == 'r':                                              # « R » répété (boudins des whoops)
                    for q in range(2):
                        fit(row, lgo, (k * rw + q * rw / 2, 120, k * rw + (q + 1) * rw / 2, 392), 0.05)
                else:
                    fit(row, lgo, (k * rw, 110, (k + 1) * rw, 402), 0.1)
            row = K.shade_v(row, (0, 0, row.size[0], 512), 1.0, 0.8).resize((W, 512), Image.LANCZOS)
            im = Image.new('RGB', (W, 1024), tuple(int(c * 0.7) for c in bg)); im.paste(row, (0, 0)); im.paste(row, (0, 512))
            ImageDraw.Draw(im).rectangle([0, 994, W, 1024], fill=tuple(int(c * 0.6) for c in bg))
            _save(im, os.path.join(out, 'boudin%s_%s.png' % ('3' if long3 else '', name)))
    return list(BOUDIN)


# ---------------------------------------------------------------- poteaux ronds (modèle de Saint-Georges, nouvelles peaux)
def pylones(out, sgm_statue):
    for name, bg, lg, base in (('monster', (14, 14, 15), 'monster_claw', 'pylon_round.png'), ('honda', (214, 22, 28), 'honda', 'pylon_round_motul.png'),
                               ('venum', (14, 14, 15), 'venum', 'pylon_round.png')):
        im = Image.open(os.path.join(sgm_statue, base)).convert('RGB'); d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 1024, 928], fill=bg)
        for cx in (256, 768):
            if lg == 'monster_claw':
                fit(im, logo(lg), (cx - 130, 240, cx + 130, 700), 0.0)
            else:
                fit(im, logo(lg), (cx - 80, 120, cx + 80, 820), 0.0, rot=90)
        im = K.shade_v(im, (0, 0, 1024, 928), 1.0, 0.8)
        _save(im, os.path.join(out, 'pylone_%s.png' % name))


# ---------------------------------------------------------------- mur de virage (ballots bâchés + bandeau)
MUR = dict(honda=((214, 22, 28), 'honda', None, 1), seong=((0, 160, 172), 'seong', (10, 10, 10), 1), amv=((245, 245, 242), 'amv', None, 3),
           five=((245, 245, 242), 'five', None, 1), automoto=((16, 16, 18), 'automoto', None, 1), motoverte=((225, 225, 222), 'motoverte', None, 1),
           venum=((16, 16, 18), 'venum', None, 1))
MUR_L = 4.0


def mur(out):
    m = Mesh(); W, H = 1024, 512
    ban, tarp, top = R((0, 0, 1024, 256), W, H), R((0, 262, 1024, 506), W, H), R((8, 480, 120, 504), W, H)
    x0, x1 = -MUR_L, MUR_L
    m.box((x0, 0, -1.25), (x1, 2.6, 1.25), tarp, 'xXzZ')                     # ballots sous bâche grise
    m.quad([(x0, 2.6, 1.25), (x1, 2.6, 1.25), (x1, 4.6, 0.35), (x0, 4.6, 0.35)], ban)          # bandeau incliné, côté piste
    m.quad([(x0, 4.6, 0.35), (x1, 4.6, 0.35), (x1, 4.6, -0.9), (x0, 4.6, -0.9)], top)
    m.quad([(x1, 2.6, -1.25), (x0, 2.6, -1.25), (x0, 4.6, -0.9), (x1, 4.6, -0.9)], top)
    for x, sg in ((x0, -1), (x1, 1)):                                        # bouts du boudin du haut
        P = [(x, 2.6, 1.25), (x, 2.6, -1.25), (x, 4.6, -0.9), (x, 4.6, 0.35)]
        m.quad(P if sg > 0 else P[::-1], top)
    m.write(os.path.join(out, 'mur.jm'), MAT_BACHE)
    K.shp(os.path.join(out, 'mur.shp'), [(x, y, 0) for x in (-3, -1, 1, 3) for y in (1.3, 3.2)], 1.4, (1.5, 1000, 200))
    rng = np.random.default_rng(4)
    for name, (bg, lg, ink, n) in MUR.items():
        im = Image.new('RGB', (W, H), (132, 134, 138)); d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 1024, 256], fill=bg)
        if name == 'amv':
            d.rectangle([0, 0, 1023, 255], outline=(0, 150, 64), width=14)
        lgo = logo(lg) if ink is None else K.tint(logo(lg), ink)
        if name == 'seong':
            lgo = K.hstack([logo('seong_icon').resize((120, 134)), lgo], 40)
        for k in range(n):
            fit(im, lgo, (k * 1024 / n, 20, (k + 1) * 1024 / n, 236), 0.1)
        im = K.shade_v(im, (0, 0, 1024, 256), 1.0, 0.86)
        a = np.asarray(im, float)                                            # plis de la bâche grise
        xs = np.arange(1024); fold = sum(np.sin(xs / p + rng.uniform(0, 6)) * q for p, q in ((23, 5), (61, 7), (140, 6)))
        a[262:, :, :] += fold[None, :, None]; a[262:, :, :] *= np.linspace(1.0, 0.62, 250)[:, None, None]
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        ImageDraw.Draw(im).rectangle([0, 474, 130, 512], fill=tuple(int(c * 0.8) for c in bg))
        _save(K.grain(im, 2.5), os.path.join(out, 'mur_%s.png' % name))
    return list(MUR)


# ---------------------------------------------------------------- filet derrière les virages
FILET_H = 13.0


def filet(out):
    m = Mesh(); W = H = 512
    net, post, ban = R((0, 0, 512, 320), W, H), R((4, 330, 60, 506), W, H), R((70, 330, 510, 440), W, H)
    m.quad([(-4, 4.6, 0), (4, 4.6, 0), (4, FILET_H, 0), (-4, FILET_H, 0)], net, two=True)
    for x in (-4, 4):
        m.tube((x, 0, 0), (x, FILET_H + 0.4, 0), 0.28, post, 8)
    m.quad([(-4, 4.7, 0.06), (4, 4.7, 0.06), (4, 6.7, 0.06), (-4, 6.7, 0.06)], ban)             # bandeau côté piste (+z)
    m.write(os.path.join(out, 'filet.jm'), MAT_MAT)
    for name, pcol, bcol, lg in (('venum', (200, 24, 30), (200, 24, 30), 'venum'), ('noir', (20, 20, 22), (16, 16, 18), 'monster_text')):
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        for k in range(0, 512, 8):                                           # maille fine noire
            d.line([(k, 0), (k, 320)], fill=(18, 18, 20, 235), width=1); d.line([(0, k * 320 // 512), (512, k * 320 // 512)], fill=(18, 18, 20, 235), width=1)
        d.rectangle([0, 0, 511, 5], fill=(18, 18, 20, 255)); d.rectangle([0, 322, 64, 512], fill=pcol + (255,))
        d.rectangle([66, 326, 512, 444], fill=bcol + (255,))
        for k in range(2):
            fit(im, logo(lg), (70 + k * 220, 336, 290 + k * 220, 434), 0.14)
        _save(im, os.path.join(out, 'filet_%s.png' % name), alpha=True)


# ---------------------------------------------------------------- bâche AMV du saut du milieu
def _mascotte(d, cx, cy, s, G=(0, 150, 64)):
    """petit bonhomme casqué vert (silhouette simple, redessinée)."""
    d.ellipse([cx - s, cy - 2.2 * s, cx + s, cy - 0.2 * s], fill=G)                              # casque
    d.rounded_rectangle([cx - 0.7 * s, cy - 1.5 * s, cx + 0.7 * s, cy - 0.95 * s], int(0.2 * s), fill=(250, 250, 250))
    d.ellipse([cx - 0.28 * s, cy - 1.4 * s, cx - 0.08 * s, cy - 1.1 * s], fill=(20, 20, 20)); d.ellipse([cx + 0.08 * s, cy - 1.4 * s, cx + 0.28 * s, cy - 1.1 * s], fill=(20, 20, 20))
    d.rounded_rectangle([cx - 0.55 * s, cy - 0.15 * s, cx + 0.55 * s, cy + 1.5 * s], int(0.25 * s), fill=(25, 25, 28))   # corps
    d.line([(cx - 0.5 * s, cy + 0.2 * s), (cx - 1.3 * s, cy + 0.9 * s)], fill=(25, 25, 28), width=int(0.3 * s))
    d.line([(cx + 0.5 * s, cy + 0.2 * s), (cx + 1.3 * s, cy - 0.3 * s)], fill=(25, 25, 28), width=int(0.3 * s))


def amv_jupe(out, half_c=10.0, wing=22.0, h=10.0, head=2.6):
    G = (0, 150, 64); W, H = 2048, 512; px = 31.0
    cw, ch, ww, wh = int(2 * half_c * px), int((h + head) * px), int(wing * px), int(h * px)
    im = Image.new('RGB', (W, H), (245, 245, 242)); d = ImageDraw.Draw(im)
    bc = (ww + 4, 0, ww + 4 + cw, ch)                                        # panneau central
    d.rectangle(bc, fill=G); d.rectangle([bc[0] + 10, int(head * px), bc[2] - 10, bc[3] - 10], fill=(248, 248, 246))
    d.rectangle([bc[0] + 10, 8, bc[2] - 10, int(head * px) - 8], fill=(248, 248, 246))
    for k in range(3):                                                       # bandeau du haut : AMV AMV AMV
        fit(im, logo('amv'), (bc[0] + 10 + k * (cw - 20) / 3, 8, bc[0] + 10 + (k + 1) * (cw - 20) / 3, int(head * px) - 8), 0.16)
    d.rounded_rectangle([bc[0] + cw * 0.3, int(head * px) + 14, bc[0] + cw * 0.7, int(head * px) + 62], 8, fill=G)
    fit(im, K.tint(logo('amv_fr'), (255, 255, 255)), (bc[0] + cw * 0.3, int(head * px) + 14, bc[0] + cw * 0.7, int(head * px) + 62), 0.12)
    y = int(head * px) + 84
    for line in ("L'ASSURANCE", "DES DEUX-ROUES", "QUI COMPREND", "LES DEUX-ROUES !"):
        t = K.text_img(line, 40, (30, 60, 40), 'arialbd.ttf'); fit(im, t, (bc[0] + 20, y, bc[2] - 20, y + 50), 0.02); y += 54
    boxes = {}
    for side, x0 in (('g', 0), ('d', ww + 8 + cw)):                          # triangles : bonhomme + AMV.fr
        tri = [(x0, wh), (x0 + ww, wh), (x0 + ww, 0)] if side == 'g' else [(x0, 0), (x0, wh), (x0 + ww, wh)]
        d.polygon(tri, fill=(248, 248, 246)); d.line(tri + [tri[0]], fill=G, width=16)
        cx = x0 + ww * (0.66 if side == 'g' else 0.34)
        _mascotte(d, cx, wh * 0.52, wh * 0.13)
        fit(im, logo('amv_fr'), (cx - ww * 0.3, wh * 0.74, cx + ww * 0.3, wh * 0.95), 0.05)
        boxes[side] = x0
    im = K.shade_v(im, (0, 0, W, ch), 1.0, 0.86)
    _save(K.grain(im, 2.0), os.path.join(out, 'amv_jupe.png'))
    m = Mesh(); u = lambda x: (x + 0.5) / W; v = lambda y: 1 - (y + 0.5) / H
    m.quad([(-half_c, 0, 0), (half_c, 0, 0), (half_c, h + head, 0), (-half_c, h + head, 0)], R(bc, W, H), two=False)
    xg, xd = boxes['g'], boxes['d']
    m.tri([(-half_c - wing, 0, 0), (-half_c, 0, 0), (-half_c, h, 0)], [(u(xg), v(wh)), (u(xg + ww), v(wh)), (u(xg + ww), v(0))])
    m.tri([(half_c, 0, 0), (half_c + wing, 0, 0), (half_c, h, 0)], [(u(xd), v(wh)), (u(xd + ww), v(wh)), (u(xd), v(0))])
    back = R((1960, 440, 2040, 500), W, H)                                   # dos : bâche blanche unie
    m.quad([(half_c, 0, -0.05), (-half_c, 0, -0.05), (-half_c, h + head, -0.05), (half_c, h + head, -0.05)], back)
    m.write(os.path.join(out, 'amv_jupe.jm'), MAT_BACHE)
    return dict(half=half_c + wing, h=h + head)


# ---------------------------------------------------------------- rampe acier + coins Honda (saut d'arrivée)
def _steel(d, box, dark=(58, 60, 64), light=(96, 99, 104)):
    x0, y0, x1, y1 = box; d.rectangle(box, fill=dark)
    for y in range(y0, y1, 10):
        d.line([(x0, y), (x1, y)], fill=light, width=2)
    for x in range(x0, x1, 22):
        d.line([(x, y0), (x, y1)], fill=(40, 41, 44), width=2)


def rampe_honda(out, prof_u, prof_h, width=6.0):
    """prof_u / prof_h : coupe du terrain le long du couloir, du pied de la rampe (u = 0) à la crête. Origine au pied."""
    W = H = 1024; im = Image.new('RGB', (W, H), (214, 22, 28)); d = ImageDraw.Draw(im)
    _steel(d, (0, 0, 256, 1024)); steel = R((0, 0, 256, 1024), W, H)
    wd, wg = (270, 0, 1024, 420), (270, 430, 1024, 850)                       # coin rouge : aile + HONDA, côté haut à droite / à gauche
    fit(im, logo('honda'), (wd[0] + 250, wd[1] + 190, wd[2] - 20, wd[3] - 20), 0.04)
    fit(im, logo('honda'), (wg[0] + 20, wg[1] + 190, wg[2] - 250, wg[3] - 20), 0.04)
    im = K.shade_v(im, (270, 0, 1024, 850), 1.0, 0.85)
    _save(K.grain(im, 2.0), os.path.join(out, 'rampe_honda.png'))
    m = Mesh(); h0 = prof_h[0]; n = len(prof_u); L = prof_u[-1]
    for i in range(n - 1):                                                    # tôle posée sur la terre (+0,12 ft), +z = sens de course
        a, b = prof_u[i], prof_u[i + 1]; ya, yb = prof_h[i] - h0 + 0.12, prof_h[i + 1] - h0 + 0.12
        m.quad([(width / 2, ya, a), (-width / 2, ya, a), (-width / 2, yb, b), (width / 2, yb, b)],
               (steel[0], steel[1] + (steel[3] - steel[1]) * a / L, steel[2], steel[1] + (steel[3] - steel[1]) * b / L))
    hgt = lambda u: float(np.interp(u, prof_u, prof_h)) - h0
    rd, rg = R(wd, W, H), R(wg, W, H); red = (rd[0] + 0.01, rd[3] - 0.01)
    for xs, u0 in ((-width / 2 - 1.3, L * 0.28), (-width / 2 - 1.3, L * 0.62), (width / 2 + 1.3, L * 0.45)):   # 3 coins, comme la photo
        u1 = u0 + 7.5; top = (xs, hgt(u1) + 4.6, u1)
        Ap, Bp = (xs + 0.9, hgt(u0) - 0.3, u0), (xs + 0.9, hgt(u1) - 0.3, u1)   # face +x : le haut (côté crête) est à gauche
        m.tri([Bp, Ap, top], [(rg[0], rg[1]), (rg[2], rg[1]), (rg[0], rg[3])])
        Am, Bm = (xs - 0.9, hgt(u0) - 0.3, u0), (xs - 0.9, hgt(u1) - 0.3, u1)   # face -x : le haut est à droite
        m.tri([Am, Bm, top], [(rd[0], rd[1]), (rd[2], rd[1]), (rd[2], rd[3])])
        m.tri([Bm, Bp, top], [red] * 3); m.tri([Ap, Am, top], [red] * 3)        # dos et dessus
    m.write(os.path.join(out, 'rampe_honda.jm'), (30, 0.6, 0.6, 0.6, 0.6))


# ---------------------------------------------------------------- habillage noir Venum des tremplins FMX (ramp_50)
def fmx_jupe(out, ramp_jm):
    L = open(ramp_jm).read().splitlines(); nv = int(L[2].split()[0])
    V = np.array([[float(t) for t in l.split()[:3]] for l in L[3:3 + nv]])
    zs = np.linspace(V[:, 2].min(), V[:, 2].max(), 24)                        # dessus du tremplin : y max par tranche
    top = np.array([V[np.abs(V[:, 2] - z) < 0.9, 1].max() for z in zs]); top = np.maximum.accumulate(top[::-1])[::-1]
    zl, hl = zs[0], top[0]; W, H = 1024, 512; px = W / abs(zl)
    im = Image.new('RGB', (W, H), (14, 14, 15)); d = ImageDraw.Draw(im)
    fit(im, logo('venum'), (30, 345, 430, 486), 0.05); fit(im, logo('venum'), (594, 345, 994, 486), 0.05)   # sous la lèvre, des deux côtés
    im = K.shade_v(im, (0, 0, W, H), 1.0, 0.8); _save(K.grain(im, 2.0), os.path.join(out, 'fmx_jupe.png'))
    m = Mesh(); xw = float(np.abs(V[:, 0]).max()) + 0.15
    for xs in (-xw, xw):
        for i in range(len(zs) - 1):
            za, zb = zs[i], zs[i + 1]; ya, yb = top[i] - 0.05, top[i + 1] - 0.05
            # image : lèvre (z = zl) à gauche vue du côté -x ; à droite vue du côté +x (texte toujours à l'endroit)
            uu = (lambda z: (z - zl) / -zl) if xs < 0 else (lambda z: 1 - (z - zl) / -zl)
            P = [(xs, 0, za), (xs, 0, zb), (xs, yb, zb), (xs, ya, za)]; UV = [(uu(za), 0.02), (uu(zb), 0.02), (uu(zb), 0.02 + 0.96 * yb / hl), (uu(za), 0.02 + 0.96 * ya / hl)]
            if xs < 0:
                P, UV = [P[1], P[0], P[3], P[2]], [UV[1], UV[0], UV[3], UV[2]]
            m.tri([P[0], P[1], P[2]], [UV[0], UV[1], UV[2]]); m.tri([P[0], P[2], P[3]], [UV[0], UV[2], UV[3]])
    V2 = np.array(m.V); I2 = np.array(m.I).reshape(-1, 3)                     # faces tournées vers l'extérieur (x du même signe que la normale)
    g = np.cross(V2[I2[:, 1], :3] - V2[I2[:, 0], :3], V2[I2[:, 2], :3] - V2[I2[:, 0], :3])[:, 0] * V2[I2[:, 0], 0] < 0
    I2[g] = I2[g][:, ::-1]; m.I = I2.ravel().tolist()
    for k in range(0, len(m.I), 3):
        a_, b_, c_ = m.I[k:k + 3]; n_ = np.cross(V2[b_, :3] - V2[a_, :3], V2[c_, :3] - V2[a_, :3]); n_ /= np.linalg.norm(n_) or 1
        for q in (a_, b_, c_):
            m.V[q][3:6] = list(n_)
    m.quad([(xw, 0, zl), (-xw, 0, zl), (-xw, hl - 0.05, zl), (xw, hl - 0.05, zl)], (0.9, 0.02, 0.98, 0.1))   # dos (sous la lèvre)
    m.write(os.path.join(out, 'fmx_jupe.jm'), MAT_MAT)


# ---------------------------------------------------------------- portique Minerva Oil + podium
def minerva(out):
    G = (0, 150, 64); W = H = 1024; im = Image.new('RGB', (W, H), (14, 14, 15)); d = ImageDraw.Draw(im)
    hd = (0, 0, 1024, 250)                                                    # fronton 12,4 x 3 ft
    d.rectangle([0, 0, 1023, 14], fill=G); d.rectangle([0, 236, 1023, 250], fill=(240, 240, 238))
    fit(im, logo('minerva'), (150, 24, 874, 226), 0.04)
    for x0 in (30, 910):                                                      # chevrons
        for k in range(3):
            xx = x0 + k * 28; pts = [(xx, 70), (xx + 30, 125), (xx, 180)] if x0 < 500 else [(xx + 30, 70), (xx, 125), (xx + 30, 180)]
            d.line(pts, fill=(240, 240, 238), width=10)
    pb = (0, 256, 190, 1024)                                                  # bandeau vert d'un pilier 2,2 x 9 ft
    d.rectangle(pb, fill=G); d.rectangle([pb[0] + 8, pb[1] + 8, pb[2] - 8, pb[3] - 8], outline=(240, 240, 238), width=5)
    fit(im, logo('minerva_v'), (pb[0] + 20, pb[1] + 40, pb[2] - 20, pb[3] - 40), 0.0, rot=90)
    _steel(d, (200, 256, 712, 768)); st = R((200, 256, 712, 768), W, H); blk = R((730, 300, 1000, 500), W, H)
    _save(K.grain(im, 2.0), os.path.join(out, 'minerva.png'))
    m = Mesh(); hw, pw, ph, hh, dz = 4.0, 2.2, 9.0, 3.0, 3.0
    for zf, facing in ((dz, 'Z'), (-dz, 'z')):                                # deux cadres (avant / arrière)
        z0, z1 = (zf - 0.5, zf) if facing == 'Z' else (zf, zf + 0.5)
        for sx in (-1, 1):
            x0, x1 = sorted((sx * hw, sx * (hw + pw)))
            m.box((x0, 0, z0), (x1, ph, z1), blk, 'xXzZ', {facing: R(pb, W, H)})
        m.box((-hw - pw, ph, z0), (hw + pw, ph + hh, z1), blk, 'xXzZYy', {facing: R(hd, W, H)})
    for sx in (-1, 1):                                                        # côtés noirs pleins entre les deux cadres
        x0, x1 = sorted((sx * (hw + pw - 0.3), sx * (hw + pw)))
        m.box((x0, 0, -dz + 0.5), (x1, ph + hh, dz - 0.5), blk, 'xX')
    m.box((-hw - pw, ph + hh - 0.3, -dz + 0.5), (hw + pw, ph + hh, dz - 0.5), blk, 'Yy')
    yp, lr = 2.4, 9.0                                                         # podium acier + 2 rampes (on roule dessus)
    m.box((-hw, 0, -dz), (hw, yp, dz), st, 'xXY')
    for sg in (-1, 1):
        A = [(-hw, yp, sg * dz), (hw, yp, sg * dz), (hw, 0, sg * (dz + lr)), (-hw, 0, sg * (dz + lr))]
        m.quad(A if sg > 0 else A[::-1], st)
        for sx in (-1, 1):
            T = [(sx * hw, 0, sg * dz), (sx * hw, 0, sg * (dz + lr)), (sx * hw, yp, sg * dz)]
            m.tri(T if sx * sg > 0 else T[::-1], [(blk[0], blk[1])] * 3)
    m.write(os.path.join(out, 'minerva.jm'), MAT_MAT)
    sp = []; r = 1.0                                                          # collision : boules sous la surface (comme ramp_50.shp)
    for z in np.arange(-dz - lr, dz + lr + 0.01, 0.75):
        y = yp if abs(z) <= dz else yp * (1 - (abs(z) - dz) / lr)
        ny = 1.0 if abs(z) <= dz else lr / np.hypot(lr, yp)
        for x in np.arange(-hw + 0.6, hw - 0.59, 0.75):
            sp.append((x, y - r * ny, z))
    for sx in (-1, 1):                                                        # piliers
        for z in (-dz + 0.25, dz - 0.25):
            sp += [(sx * (hw + pw / 2), y, z) for y in (1.1, 3.3, 5.5, 7.7)]
    K.shp(os.path.join(out, 'minerva.shp'), sp, r, (1.5, 1000, 200))
    return dict(n_boules=len(sp))


# ---------------------------------------------------------------- arche jaune 50 Factory
def arche_50(out, drop=0.0, half=21.0, leg=3.6, hleg=17.0, hbeam=4.6):
    Y = (250, 224, 22); W, H = 1024, 512; im = Image.new('RGB', (W, H), Y); d = ImageDraw.Draw(im)
    bw = 2 * half + leg; bb = (0, 0, 1024, int(1024 * hbeam / bw))            # face de la poutre
    fit(im, logo('50factory'), (bb[0] + 250, bb[1], bb[2] - 250, bb[3]), 0.14)
    lb = (0, 130, int(380 * leg / hleg), 510)                                 # face d'un pied (logo vertical)
    fit(im, logo('50factory'), (lb[0], lb[1] + 30, lb[2], lb[3] - 30), 0.14, rot=90)
    ft = (120, 130, 520, 290); fit(im, logo('50factory'), ft, 0.12)           # pied en biais : logo à plat
    pl = R((600, 300, 900, 480), W, H)
    im = K.shade_v(im, (0, 0, W, bb[3]), 1.0, 0.9); _save(K.grain(im, 2.0), os.path.join(out, 'arche_50.png'))
    m = Mesh(); y0 = -drop
    for sx in (-1, 1):
        x0, x1 = sx * half - leg / 2, sx * half + leg / 2
        m.box((x0, y0, -leg / 2), (x1, y0 + hleg, leg / 2), pl, 'xXzZ', {'Z': R(lb, W, H), 'z': R(lb, W, H)})
        for sz in (-1, 1):                                                    # contreforts en biais devant / derrière
            zf = sz * (leg / 2 + 5.0); P = [(x0, y0, zf), (x1, y0, zf), (x1, y0 + 6.5, sz * leg / 2), (x0, y0 + 6.5, sz * leg / 2)]
            m.quad(P if sz > 0 else [P[1], P[0], P[3], P[2]], R(ft, W, H))
            for x, s2 in ((x0, -1), (x1, 1)):
                T = [(x, y0, sz * leg / 2), (x, y0, zf), (x, y0 + 6.5, sz * leg / 2)]
                m.tri(T if s2 * sz < 0 else T[::-1], [(pl[0], pl[1])] * 3)
    m.box((-half - leg / 2, y0 + hleg, -leg / 2), (half + leg / 2, y0 + hleg + hbeam, leg / 2), pl, 'xXzZYy', {'Z': R(bb, W, H), 'z': R(bb, W, H)})
    m.write(os.path.join(out, 'arche_50.jm'), MAT_BACHE)
    return dict(clear=hleg - 0.0, half=half)


# ---------------------------------------------------------------- départ : bandeau START + mur de fond
def depart(out, width=96.0):
    W, H = 2048, 512; im = Image.new('RGB', (W, H), (12, 12, 13)); d = ImageDraw.Draw(im)
    bb = (0, 0, 2048, 86)                                                     # bandeau 96 x 4 ft
    mon = K.hstack([logo('monster_claw'), logo('monster_text')], 20)
    for box, lg in (((30, 6, 330, 80), logo('venum')), ((380, 6, 720, 80), mon), ((760, 2, 1288, 84), logo('start')),
                    ((1328, 6, 1668, 80), mon), ((1718, 6, 2018, 80), logo('venum'))):
        fit(im, lg, box, 0.1)
    wb = (0, 100, 2048, 264)                                                  # mur de fond 100 x 8 ft
    seq = [logo('sxparis'), logo('venum'), mon, logo('sxparis'), logo('venum'), mon, logo('sxparis'), logo('venum')]
    for k, lg in enumerate(seq):
        fit(im, lg, (k * 256, 108, (k + 1) * 256, 256), 0.14)
    tr = (0, 280, 96, 512); d.rectangle(tr, fill=(30, 30, 32))                # treillis alu
    for y in range(280, 512, 48):
        d.line([(0, y), (96, y + 48)], fill=(170, 172, 176), width=5); d.line([(96, y), (0, y + 48)], fill=(170, 172, 176), width=5)
        d.line([(0, y), (96, y)], fill=(170, 172, 176), width=5)
    d.line([(3, 280), (3, 512)], fill=(190, 192, 196), width=6); d.line([(92, 280), (92, 512)], fill=(190, 192, 196), width=6)
    red = (120, 280, 400, 500); d.rectangle(red, fill=(196, 22, 28))
    _save(K.grain(im, 1.5), os.path.join(out, 'depart.png'))
    m = Mesh(); hw = width / 2; rb, rw, rt = R(bb, W, H), R(wb, W, H), R(tr, W, H); blk = R((500, 300, 700, 480), W, H)
    zb = -5.0                                                                 # bandeau au-dessus des pilotes, lisible des deux côtés
    m.quad([(-hw, 13, zb + 0.15), (hw, 13, zb + 0.15), (hw, 17, zb + 0.15), (-hw, 17, zb + 0.15)], rb)          # face +z (côté piste)
    m.quad([(hw, 13, zb - 0.15), (-hw, 13, zb - 0.15), (-hw, 17, zb - 0.15), (hw, 17, zb - 0.15)], rb)          # face -z (côté paddock)
    m.box((-hw, 12.6, zb - 0.6), (hw, 13.0, zb + 0.6), rt, 'xXzZYy'); m.box((-hw, 17.0, zb - 0.6), (hw, 17.4, zb + 0.6), rt, 'xXzZYy')
    for sx in (-1, 1):                                                        # tours en treillis
        x0, x1 = sorted((sx * hw, sx * (hw + 1.6)))
        m.box((x0, 0, zb - 0.8), (x1, 18.2, zb + 0.8), rt, 'xXzZY')
    zw = -15.0                                                                # mur de fond noir derrière les grilles + mur rouge plus haut
    m.quad([(-50, 0, zw), (50, 0, zw), (50, 8, zw), (-50, 8, zw)], rw)
    m.quad([(50, 0, zw - 0.3), (-50, 0, zw - 0.3), (-50, 8, zw - 0.3), (50, 8, zw - 0.3)], blk)
    m.box((-50, 8, zw - 0.3), (50, 8.05, zw), blk, 'Y')
    m.write(os.path.join(out, 'depart.jm'), MAT_MAT)


# ---------------------------------------------------------------- panneau FINISH suspendu
def finish(out, drop=0.0, y_bas=34.0, roof=118.0):
    W, H = 1024, 256; im = Image.new('RGB', (W, H), (8, 8, 9)); d = ImageDraw.Draw(im)
    fb = (0, 0, 1024, 200)                                                    # 26 x 5,1 ft, façon écran LED
    fin = K.tint(logo('finish'), (235, 255, 235))
    for k, x in enumerate((60, 110, 160)):
        d.polygon([(x, 150), (x + 26, 150), (x + 76, 40), (x + 50, 40)], fill=(120, 230, 60))
        d.polygon([(1024 - x, 150), (1024 - x - 26, 150), (1024 - x - 76, 40), (1024 - x - 50, 40)], fill=(120, 230, 60))
    fit(im, fin, (250, 30, 774, 150), 0.02); fit(im, logo('venum'), (400, 152, 624, 196), 0.05)
    a = np.asarray(im, float); a[:200:4, :, :] *= 0.55; a[:200, ::4, :] *= 0.75   # trame de LED
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); _save(im, os.path.join(out, 'finish.png'))
    m = Mesh(); y0 = y_bas - drop; rf = R(fb, W, H); blk = R((20, 215, 200, 245), W, H)
    m.box((-13, y0, -0.6), (13, y0 + 5.1, 0.6), blk, 'xXzZYy', {'Z': rf, 'z': rf})
    for x in (-11, 11):                                                       # élingues jusqu'au toit
        m.tube((x, y0 + 5.1, 0), (x, roof - drop, 0), 0.08, blk, 5, caps=False)
    m.write(os.path.join(out, 'finish.jm'), MAT_MAT)


# ---------------------------------------------------------------- canette Monster géante
def canette(out, r=4.6, h=23.0):
    W, H = 1024, 1024; im = Image.new('RGB', (W, H), (14, 14, 15)); d = ImageDraw.Draw(im)
    for cx in (256, 768):
        fit(im, logo('monster_claw'), (cx - 150, 120, cx + 150, 560), 0.0); fit(im, logo('monster_text'), (cx - 200, 600, cx + 200, 740), 0.0)
    d.rectangle([0, 0, 1024, 40], fill=(150, 152, 156)); d.rectangle([0, 800, 1024, 830], fill=(110, 112, 116))
    im = K.shade_v(im, (0, 0, 1024, 800), 1.0, 0.82); _save(im, os.path.join(out, 'canette.png'))
    m = Mesh(); seg = 20; body = R((0, 0, 1024, 800), W, H); top = R((40, 850, 300, 1000), W, H)
    for k in range(seg):
        a0, a1 = 2 * np.pi * k / seg, 2 * np.pi * (k + 1) / seg
        c0, s0, c1, s1 = np.cos(a0), np.sin(a0), np.cos(a1), np.sin(a1)
        u0, u1 = body[0] + (body[2] - body[0]) * k / seg, body[0] + (body[2] - body[0]) * (k + 1) / seg
        m.quad([(r * s0, 0, r * c0), (r * s1, 0, r * c1), (r * s1, h, r * c1), (r * s0, h, r * c0)], (u0, body[1], u1, body[3]),
               N=[(s0, 0, c0), (s1, 0, c1), (s1, 0, c1), (s0, 0, c0)])
        m.tri([(r * s0, h, r * c0), (r * s1, h, r * c1), (0.86 * r * s0, h + 0.9, 0.86 * r * c0)], [(top[0], top[1])] * 3)
        m.tri([(r * s1, h, r * c1), (0.86 * r * s1, h + 0.9, 0.86 * r * c1), (0.86 * r * s0, h + 0.9, 0.86 * r * c0)], [(top[0], top[1])] * 3)
        m.tri([(0, h + 0.9, 0), (0.86 * r * s0, h + 0.9, 0.86 * r * c0), (0.86 * r * s1, h + 0.9, 0.86 * r * c1)], [(top[0], top[1])] * 3, [(0, 1, 0)] * 3)
    m.write(os.path.join(out, 'canette.jm'), MAT_BACHE)


# ---------------------------------------------------------------- camions du paddock (provisoire : la place et les couleurs)
SEMIS = dict(honda=((205, 20, 26), 'honda', None), yamaha=((22, 50, 140), 'yamaha', None), monster=((16, 16, 18), 'monster', None),
             kawasaki=((80, 170, 30), None, 'KAWASAKI'), ktm=((240, 110, 10), None, 'KTM'), triumph=((20, 20, 22), None, 'TRIUMPH'),
             ducati=((200, 16, 22), None, 'DUCATI'), blanc=((235, 235, 232), 'sxparis', None))


def semi(out):
    """remorque 46 x 8,4 x 13,4 ft + tracteur, +z = l'avant ; auvent de 20 ft sur le côté +x."""
    W = H = 1024; m = Mesh()
    side, rear, wh, dark, awn = R((0, 0, 1024, 250), W, H), R((0, 260, 200, 520), W, H), R((220, 260, 300, 340), W, H), \
        R((320, 270, 400, 330), W, H), R((420, 260, 1000, 520), W, H)
    cab, glass = R((0, 540, 400, 800), W, H), R((420, 540, 700, 700), W, H)
    x0, x1 = -4.2, 4.2
    m.box((x0, 3.6, -46), (x1, 13.4, 0), dark, 'xXzZY', {'x': side, 'X': side, 'z': rear, 'Z': rear})
    m.box((x0, 2.0, -44), (x1, 3.6, -2), dark, 'xXzZy')                      # châssis / coffres
    m.box((-3.9, 2.4, 1.0), (3.9, 9.6, 7.0), cab, 'xXzY', {'Y': dark})       # cabine
    m.quad([(-3.9, 2.4, 7.0), (3.9, 2.4, 7.0), (3.9, 6.0, 8.2), (-3.9, 6.0, 8.2)], cab)       # capot
    m.quad([(-3.9, 6.0, 8.2), (3.9, 6.0, 8.2), (3.9, 9.6, 7.0), (-3.9, 9.6, 7.0)], glass)     # pare-brise
    for sx in (-1, 1):
        T = [(sx * 3.9, 2.4, 7.0), (sx * 3.9, 6.0, 8.2), (sx * 3.9, 9.6, 7.0)]
        m.tri(T if sx < 0 else T[::-1], [(cab[0], cab[1])] * 3)
    for z in (-41, -37, -7, 4):                                              # roues
        for sx in (-1, 1):
            m.tube((sx * 4.2, 1.75, z), (sx * 3.0, 1.75, z), 1.75, wh, 12)
    for x, z in ((4.4, -40), (4.4, -6), (24, -40), (24, -6)):                # auvent
        m.tube((x, 0, z), (x, 11.5, z), 0.12, dark, 5, caps=False)
    m.quad([(4.2, 12.6, -42), (24.5, 11.3, -42), (24.5, 11.3, -4), (4.2, 12.6, -4)][::-1], awn, two=True)
    m.write(os.path.join(out, 'semi.jm'), (40, 0.6, 1, 1, 1))
    for name, (bg, lg, txt) in SEMIS.items():
        im = Image.new('RGB', (W, H), bg); d = ImageDraw.Draw(im)
        ink = (20, 20, 22) if sum(bg) > 600 else (255, 255, 255)
        lgo = logo(lg) if lg else K.text_img(txt, 180, ink, 'ariblk.ttf', italic=0.15)
        fit(im, lgo, (260, 20, 764, 230), 0.1); fit(im, lgo, (20, 300, 180, 480), 0.05)          # flancs + portes arrière ; auvent uni
        d.rectangle([0, 236, 1024, 250], fill=tuple(int(c * 0.55) for c in bg))
        d.rectangle([210, 255, 310, 345], fill=(22, 22, 24)); d.ellipse([240, 280, 280, 320], fill=(150, 152, 156))
        d.rectangle([310, 262, 410, 340], fill=(26, 26, 28))
        d.rectangle([410, 532, 710, 710], fill=(40, 52, 66)); d.polygon([(430, 700), (560, 545), (640, 545), (510, 700)], fill=(70, 86, 104))
        im = K.shade_v(im, (0, 0, 1024, 250), 1.0, 0.84)
        _save(im, os.path.join(out, 'semi_%s.png' % name))
    return list(SEMIS)
