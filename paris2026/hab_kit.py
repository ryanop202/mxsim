"""Outils pour l'habillage « comme en vrai » de Paris (habillage.py) : petit maillage texturé, logos, écriture .jm / .shp.

Repère d'un modèle (doc 12) : pieds, y vers le haut, +z = l'avant. v = 0 = bas de l'image.
Logos : vrais fichiers quand on les a (assets/logos : Motul, 50 Factory, SX Tour ; textures de ZION 2025 : Honda, Yamaha, Seong,
Monster, Automoto, Supercross Paris). Les autres (AMV, Venum, Minerva Oil, Thor, Five, Moto Verte, « R ») sont REDESSINÉS
en texte, en attendant les fichiers officiels -> LOGOS_REDESSINES.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ZSRC = os.path.join(HERE, "refs", "zion25_full", "ZION.2025.SupercrossParis")
LOGOS = os.path.join(ROOT, "assets", "logos")
FONTS = "C:/Windows/Fonts/"
LOGOS_REDESSINES = ['amv', 'venum', 'minerva', 'thor', 'five', 'motoverte', 'r']


# ---------------------------------------------------------------- maillage
class Mesh:
    def __init__(self):
        self.V, self.I = [], []

    def tri(self, P, UV, N=None):
        P = [np.asarray(p, float) for p in P]
        if N is None:
            n = np.cross(P[1] - P[0], P[2] - P[0]); n = n / (np.linalg.norm(n) or 1.0); N = [n, n, n]
        k = len(self.V)
        for p, n, uv in zip(P, N, UV):
            self.V.append([p[0], p[1], p[2], n[0], n[1], n[2], uv[0], uv[1]])
        self.I += [k, k + 1, k + 2]

    def quad(self, P, r, two=False, N=None):
        """P = 4 points (bas gauche, bas droite, haut droite, haut gauche) vus de l'extérieur ; r = (u0, v0, u1, v1)."""
        uv = [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])]
        self.tri([P[0], P[1], P[2]], [uv[0], uv[1], uv[2]], None if N is None else [N[0], N[1], N[2]])
        self.tri([P[0], P[2], P[3]], [uv[0], uv[2], uv[3]], None if N is None else [N[0], N[2], N[3]])
        if two:
            self.tri([P[1], P[0], P[3]], [uv[1], uv[0], uv[3]]); self.tri([P[1], P[3], P[2]], [uv[1], uv[3], uv[2]])

    def box(self, lo, hi, r, faces='xXzZY', rs=None):
        """boîte ; r = rectangle UV par défaut, rs = {face: rectangle}. Faces : x / X (côtés), z / Z (arrière / avant), y / Y."""
        x0, y0, z0 = lo; x1, y1, z1 = hi; rs = rs or {}
        F = {'Z': [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], 'z': [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)],
             'X': [(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)], 'x': [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
             'Y': [(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)], 'y': [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)]}
        for f in faces:
            self.quad(F[f], rs.get(f, r))

    def tube(self, a, b, rad, r, seg=8, caps=True):
        """cylindre de a à b ; l'image fait le tour (u) et va de a (v0) à b (v1)."""
        a, b = np.asarray(a, float), np.asarray(b, float); ax = b - a; ax /= np.linalg.norm(ax)
        s = np.cross(ax, [0, 1, 0] if abs(ax[1]) < 0.9 else [1, 0, 0]); s /= np.linalg.norm(s); t = np.cross(ax, s)
        for k in range(seg):
            a0, a1 = 2 * np.pi * k / seg, 2 * np.pi * (k + 1) / seg
            n0, n1 = np.cos(a0) * s + np.sin(a0) * t, np.cos(a1) * s + np.sin(a1) * t
            u0, u1 = r[0] + (r[2] - r[0]) * k / seg, r[0] + (r[2] - r[0]) * (k + 1) / seg
            self.quad([a + n0 * rad, a + n1 * rad, b + n1 * rad, b + n0 * rad], (u0, r[1], u1, r[3]), N=[n0, n1, n1, n0])
            if caps:
                c = ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)
                self.tri([b, b + n0 * rad, b + n1 * rad], [c, c, c], [ax, ax, ax])
                self.tri([a, a + n1 * rad, a + n0 * rad], [c, c, c], [-ax, -ax, -ax])

    def write(self, path, material=(0, 0, 0, 0, 0)):
        V = np.array(self.V)
        L = ['JM1', ' '.join('%.6f' % v for v in material), '%d %d' % (len(V), len(self.I) // 3)]
        L += [' '.join('%.6f' % v for v in row) for row in V] + [str(i) for i in self.I] + ['']
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, 'w', newline='\n').write('\n'.join(L))
        return len(V), len(self.I) // 3


def shp(path, spheres, r, par=(0.6, 150, 8)):
    """collision : boules (x y z) de rayon r ; par = 3 nombres repris des .shp existants (boudins 0.6 150 8, tremplin 1.5 1000 200)."""
    L = [str(len(spheres))] + ['%.4f %.4f %.4f %.4f %s' % (p[0], p[1], p[2], r, ' '.join('%g' % v for v in par)) for p in spheres]
    open(path, 'w', newline='\n').write('\n'.join(L) + '\n')


def R(box, W, H):
    """rectangle en pixels (x0, y0, x1, y1 ; y vers le bas) -> (u0, v0, u1, v1), marge d'un demi-pixel."""
    x0, y0, x1, y1 = box
    return ((x0 + 0.5) / W, 1 - (y1 - 0.5) / H, (x1 - 0.5) / W, 1 - (y0 + 0.5) / H)


# ---------------------------------------------------------------- dessin
def font(name, px):
    return ImageFont.truetype(FONTS + name, int(px))


def text_img(txt, px, fill, fname='ariblk.ttf', italic=0.0, stroke=0, stroke_fill=None, squeeze=1.0):
    f = font(fname, px); l, t, r, b = f.getbbox(txt, stroke_width=stroke)
    im = Image.new('RGBA', (r - l + 8, b - t + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - l, 4 - t), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    if italic:
        w, h = im.size; sh = int(h * italic)
        im = im.transform((w + sh, h), Image.AFFINE, (1, italic, -sh, 0, 1, 0), Image.BICUBIC)
    if squeeze != 1.0:
        im = im.resize((max(1, int(im.size[0] * squeeze)), im.size[1]), Image.LANCZOS)
    return im.crop(im.getbbox())


def hstack(ims, gap=0, align='c'):
    h = max(i.size[1] for i in ims); w = sum(i.size[0] for i in ims) + gap * (len(ims) - 1)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0)); x = 0
    for i in ims:
        out.alpha_composite(i, (x, {'c': (h - i.size[1]) // 2, 'b': h - i.size[1], 't': 0}[align])); x += i.size[0] + gap
    return out


def vstack(ims, gap=0):
    w = max(i.size[0] for i in ims); h = sum(i.size[1] for i in ims) + gap * (len(ims) - 1)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0)); y = 0
    for i in ims:
        out.alpha_composite(i, ((w - i.size[0]) // 2, y)); y += i.size[1] + gap
    return out


def tint(im, col):
    """logo en une seule couleur (garde l'alpha)."""
    a = im.split()[3]; out = Image.new('RGBA', im.size, tuple(col) + (0,)); out.putalpha(a); return out


def fit(img, logo, box, pad=0.08, rot=0):
    """colle un logo centré dans box (x0, y0, x1, y1), sans le déformer."""
    if rot:
        logo = logo.rotate(rot, expand=True, resample=Image.BICUBIC)
    x0, y0, x1, y1 = box; bw, bh = (x1 - x0) * (1 - 2 * pad), (y1 - y0) * (1 - 2 * pad)
    k = min(bw / logo.size[0], bh / logo.size[1]); w, h = max(1, int(logo.size[0] * k)), max(1, int(logo.size[1] * k))
    lg = logo.resize((w, h), Image.LANCZOS)
    img.paste(lg, (int((x0 + x1 - w) / 2), int((y0 + y1 - h) / 2)), lg)


def grain(img, amp=3.0, seed=3):
    """grain léger (matières mates) + légère usure."""
    a = np.asarray(img.convert('RGB'), float); g = np.random.default_rng(seed).normal(0, amp, a.shape[:2])
    return Image.fromarray(np.clip(a + g[..., None], 0, 255).astype(np.uint8))


def shade_v(img, box, top=1.0, bot=0.72):
    """dégradé vertical (plus sombre vers le sol) dans box : ombre « cuite »."""
    x0, y0, x1, y1 = [int(v) for v in box]; a = np.asarray(img, float).copy()
    k = np.linspace(top, bot, y1 - y0)[:, None, None]; a[y0:y1, x0:x1, :3] *= k
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), img.mode)


# ---------------------------------------------------------------- logos
def _zcrop(rel, box, rot, mode):
    im = Image.open(os.path.join(ZSRC, rel)).convert('RGB').crop(box)
    a = np.asarray(im, float)
    if mode == 'white_on_red':
        al = np.clip((np.minimum(a[..., 1], a[..., 2]) - 45) / 110, 0, 1); rgb = np.full(a.shape, 255.0)
    elif mode == 'white_on_blue':
        al = np.clip((a[..., 0] - 60) / 130, 0, 1); rgb = np.full(a.shape, 255.0)
    else:                                                    # couleurs sur fond noir
        al = np.clip(a.max(-1) / 90, 0, 1); rgb = a / np.maximum(al[..., None], 0.25)
    out = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), al * 255]).astype(np.uint8), 'RGBA')
    if rot:
        out = out.rotate(rot, expand=True)
    return out.crop(out.getbbox())


_CACHE = {}


def logo(name):
    """logo RGBA, fond transparent (voir l'en-tête pour l'origine de chacun)."""
    if name in _CACHE:
        return _CACHE[name]
    G = (0, 150, 64)                                         # vert AMV / Minerva
    if name == 'honda':
        im = _zcrop('statue/honda.png', (485, 15, 605, 520), 90, 'white_on_red')
    elif name == 'yamaha':
        im = _zcrop('statue/yamaha.png', (500, 45, 645, 500), 90, 'white_on_blue')
    elif name == 'seong':
        im = _zcrop('statue/thor.png', (1445, 10, 1601, 830), -90, 'on_black')
    elif name == 'seong_icon':
        im = _zcrop('statue/thor.png', (1205, 318, 1408, 545), -90, 'on_black')
    elif name == 'automoto':
        im = _zcrop('statue/start.png', (15, 143, 365, 232), 0, 'on_black')
    elif name == 'monster':
        im = _zcrop('statue/warning_light_zion.png', (345, 588, 582, 822), 0, 'on_black')
    elif name == 'monster_claw':
        im = _zcrop('statue/warning_light_zion.png', (410, 588, 518, 748), 0, 'on_black')
    elif name == 'monster_text':
        im = _zcrop('statue/warning_light_zion.png', (345, 752, 582, 822), 0, 'on_black')
    elif name == 'sxparis':
        im = _zcrop('statue/fenceKTM.png', (440, 556, 1222, 894), 0, 'on_black')
    elif name == 'motul':                                    # blanc sur rouge dans le fichier : on garde le blanc
        a = np.asarray(Image.open(os.path.join(LOGOS, 'motul.png')).convert('RGB'), float)
        al = np.clip((np.minimum(a[..., 1], a[..., 2]) - 60) / 150, 0, 1)
        im = Image.fromarray(np.dstack([np.full(a.shape, 255.0), al * 255]).astype(np.uint8), 'RGBA'); im = im.crop(im.getbbox())
    elif name == '50factory':
        im = Image.open(os.path.join(LOGOS, '50factory.png')).convert('RGBA'); im = im.crop(im.getbbox())
    elif name == 'sxtour':
        im = Image.open(os.path.join(LOGOS, 'sxtour_long.png')).convert('RGBA'); im = im.crop(im.getbbox())
    # ---- redessinés (pas de fichier officiel pour l'instant)
    elif name == 'amv':
        im = text_img('AMV', 200, G, 'ariblk.ttf', squeeze=1.05)
    elif name == 'amv_fr':
        im = hstack([text_img('AMV', 200, G, 'ariblk.ttf', squeeze=1.05), text_img('.fr', 110, G, 'arialbd.ttf')], 6, 'b')
    elif name == 'venum':
        im = text_img('VENUM', 200, (255, 255, 255), 'arialbd.ttf', squeeze=1.25)
    elif name == 'minerva':
        top = hstack([text_img('MINERVA', 150, G, 'ariblk.ttf', italic=0.2), text_img('OIL', 150, (255, 255, 255), 'ariblk.ttf', italic=0.2,
                                                                                       stroke=10, stroke_fill=G)], 26)
        im = vstack([top, text_img('NOUS SIGNONS LA QUALITÉ !', 44, (255, 255, 255), 'arialbi.ttf')], 14)
    elif name == 'minerva_v':                                # bandeau vertical : MINERVA OIL blanc
        im = hstack([text_img('MINERVA', 150, (255, 255, 255), 'ariblk.ttf', italic=0.15),
                     text_img('OIL', 150, (255, 255, 255), 'ariblk.ttf', italic=0.15)], 40)
    elif name == 'thor':
        im = text_img('THOR', 200, (255, 255, 255), 'ariblk.ttf', italic=0.18, squeeze=1.15)
    elif name == 'five':
        im = hstack([text_img('5', 230, (215, 25, 32), 'ariblk.ttf', italic=0.2), text_img('FIVE', 200, (15, 15, 15), 'ariblk.ttf', italic=0.2)], 30)
    elif name == 'motoverte':
        im = hstack([text_img('moto', 200, (214, 30, 36), 'ariblk.ttf'), text_img('verte', 150, (0, 140, 60), 'segoescb.ttf')], -10, 'b')
    elif name == 'r':
        im = text_img('R', 220, (255, 255, 255), 'ariblk.ttf', italic=0.3, squeeze=1.2)
    elif name == 'start':
        im = text_img('START', 200, (255, 255, 255), 'arialbd.ttf', squeeze=1.35)
    elif name == 'finish':
        im = text_img('FINISH', 200, (255, 255, 255), 'arialbd.ttf', squeeze=1.25)
    else:
        raise KeyError(name)
    _CACHE[name] = im
    return im
