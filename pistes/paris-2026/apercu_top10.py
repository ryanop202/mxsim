"""v43g (« refais-moi une affiche pour le top 10, plus propre ; là c'est vide ; fais-en plusieurs ») : 3 propositions de l'écran
géant (4 panneaux de 256 px de texture côte à côte, dessinés x2 puis mis au rapport réel de l'écran). Pas encore dans la piste.
Tout ce qui bouge en jeu (places, numéros, noms, marques, écarts, temps) est du texte / des rectangles ; le reste est le fond fixe.
    py -3.15 pistes/paris-2026/apercu_top10.py <dossier de la piste construite> <dossier de sortie>"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tableau_direct as TD   # noqa: E402

K = 2                                   # dessin x2 (texture 256 -> 512)
W, H = 4 * 256 * K, 256 * K
ROSE, VIO, VIO2, VIO3 = TD.ROSE, TD.VIOLET, TD.VIOLET2, (74, 24, 110)
BLANC, GRIS, NOIR = (255, 255, 255), (178, 160, 196), (20, 8, 30)
COUL = dict(HONDA=(214, 24, 36), KTM=(250, 110, 0), KAWASAKI=(60, 180, 60), YAMAHA=(30, 70, 210), SUZUKI=(245, 205, 0),
            HUSQVARNA=(235, 238, 244), GASGAS=(200, 20, 40), TRIUMPH=(120, 120, 128))
PIL_ = [(202, "OPPLIGER", "HONDA", ""), (21, "THOMAS", "YAMAHA", "+1.4"), (9, "HARRIS", "KAWASAKI", "+2.9"), (47, "CLARK", "KTM", "+3.3"),
        (151, "PIETERS", "HUSQVARNA", "+5.8"), (16, "MILLER", "SUZUKI", "+7.0"), (348, "COEN", "GASGAS", "+9.6"),
        (33, "HICKS", "HONDA", "+12.1"), (77, "MANZI", "TRIUMPH", "+14.7"), (5, "SOULE", "KTM", "+18.2")]
MT = (202, "OPPLIGER", "1:52.341")       # meilleur tour


def F(px, bold=True):
    return ImageFont.truetype(TD.FONT_B if bold else r"C:/Windows/Fonts/arialbd.ttf", int(px * K))


def t(d, xy, s, px, fill, anchor="lm", bold=True):
    d.text((xy[0] * K, xy[1] * K), s, font=F(px, bold), fill=fill, anchor=anchor)


def rr(d, box, r, fill):
    d.rounded_rectangle([v * K for v in box], int(r * K), fill=fill)


def para(d, x0, y0, x1, y1, sl, fill):      # bande penchée (bord droit en biais)
    d.polygon([(x0 * K, y0 * K), (x1 * K, y0 * K), ((x1 - sl) * K, y1 * K), (x0 * K, y1 * K)], fill=fill)


def base(T):
    D_ = os.path.join(T, *TD.SUB.split("/"))
    fa = Image.open(os.path.join(D_, "fond_a.png")).convert("RGBA"); fb = Image.open(os.path.join(D_, "fond_b.png")).convert("RGBA")
    im = Image.new("RGBA", (W, H), VIO + (255,))
    p1 = fa.crop((0, 0, 256, 256)).resize((256 * K, 256 * K), Image.LANCZOS); d1 = ImageDraw.Draw(p1)
    d1.text((128 * K, 190 * K), "04:32 + 1L", font=F(35), fill=BLANC, anchor="mm"); im.paste(p1, (0, 0))
    logo = fb.crop((0, 454, 256, 512)).resize((256 * K, 58 * K), Image.LANCZOS)
    return im, logo


def carte_mt(im, d, logo, x0=768):          # panneau 4 : meilleur tour + logo MX Sim
    rr(d, (x0 + 10, 14, x0 + 246, 150), 10, VIO2)
    para(d, x0 + 10, 14, x0 + 200, 44, 14, ROSE)
    t(d, (x0 + 22, 29), "MEILLEUR TOUR", 15, BLANC)
    t(d, (x0 + 128, 82), MT[2], 34, BLANC, "mm")
    t(d, (x0 + 128, 124), "%d - %s" % MT[:2], 17, ROSE, "mm")
    im.alpha_composite(logo, (x0 * K, 176 * K))


def prop_a(T, out):
    """A : bandeau TV, 10 lignes sur 2 panneaux ; place, filet de marque, numéro en pastille rose, nom, marque en gris, écart ;
    leader en rose, lignes alternées."""
    im, logo = base(T); d = ImageDraw.Draw(im); x0, x1, h = 262, 762, 25.2
    for k, (num, nom, mq, ec) in enumerate(PIL_):
        y = 2 + k * h; lead = k == 0
        para(d, x0, y, x1, y + h - 3, 10, (ROSE if lead else (VIO3 if k % 2 == 0 else VIO2)))
        rr(d, (x0 + 3, y + 2, x0 + 37, y + h - 5), 3, BLANC); t(d, (x0 + 20, y + h / 2 - 1.5), "%d" % (k + 1), 15, NOIR, "mm")
        rr(d, (x0 + 51, y + 3, x0 + 97, y + h - 6), 4, (BLANC if lead else ROSE)); t(d, (x0 + 74, y + h / 2 - 1.5), str(num), 14, (ROSE if lead else BLANC), "mm")
        t(d, (x0 + 106, y + h / 2 - 1.5), nom, 16, BLANC)
        t(d, (x1 - 18, y + h / 2 - 1.5), "LEADER" if lead else ec, 15 if not lead else 12, BLANC, "rm")
    carte_mt(im, d, logo); fin(im, out)


def prop_b(T, out):
    """B : le leader en grand (carte), 2 et 3 en moyen, 4 à 10 en liste à côté."""
    im, logo = base(T); d = ImageDraw.Draw(im)
    num, nom, mq, _ = PIL_[0]; x0 = 262
    rr(d, (x0, 4, x0 + 246, 132), 10, ROSE)
    t(d, (x0 + 28, 34), "1", 46, BLANC); t(d, (x0 + 70, 26), "LEADER", 13, (255, 220, 245))
    t(d, (x0 + 70, 56), nom, 24, BLANC); t(d, (x0 + 28, 100), "#%d" % num, 22, NOIR)
    for j in (1, 2):
        num, nom, mq, ec = PIL_[j]; y = 138 + (j - 1) * 58
        rr(d, (x0, y, x0 + 246, y + 54), 8, VIO3)
        t(d, (x0 + 24, y + 27), str(j + 1), 30, BLANC); t(d, (x0 + 58, y + 18), nom, 17, BLANC)
        t(d, (x0 + 58, y + 40), "#%d" % num, 11, ROSE, bold=False); t(d, (x0 + 238, y + 27), ec, 17, BLANC, "rm")
    x0 = 518; h = 36
    for j in range(3, 10):
        num, nom, mq, ec = PIL_[j]; y = 4 + (j - 3) * h
        para(d, x0, y, x0 + 244, y + h - 4, 8, VIO2 if j % 2 else VIO3)
        rr(d, (x0 + 4, y + 4, x0 + 36, y + h - 8), 3, BLANC); t(d, (x0 + 20, y + h / 2 - 2), str(j + 1), 15, NOIR, "mm")
        t(d, (x0 + 52, y + h / 2 - 2), str(num), 14, ROSE); t(d, (x0 + 92, y + h / 2 - 2), nom, 15, BLANC)
        t(d, (x0 + 228, y + h / 2 - 2), ec, 14, BLANC, "rm")
    carte_mt(im, d, logo); fin(im, out)


def prop_c(T, out):
    """C : 2 colonnes de 5 grandes lignes (1-5 | 6-10), nom en grand + numéro et marque dessous, écart à droite."""
    im, logo = base(T); d = ImageDraw.Draw(im); h = 50.4
    for k, (num, nom, mq, ec) in enumerate(PIL_):
        x0 = 262 if k < 5 else 518; y = 2 + (k % 5) * h; lead = k == 0
        rr(d, (x0, y, x0 + 244, y + h - 4), 8, ROSE if lead else VIO2)
        rr(d, (x0 + 5, y + 6, x0 + 47, y + h - 10), 6, BLANC); t(d, (x0 + 26, y + h / 2 - 2), str(k + 1), 24, NOIR, "mm")
        t(d, (x0 + 65, y + 17), nom, 18, BLANC)
        t(d, (x0 + 65, y + 36), "#%d" % num, 11, (255, 225, 248) if lead else ROSE, bold=False)
        t(d, (x0 + 236, y + h / 2 - 2), "LEADER" if lead else ec, 12 if lead else 17, BLANC, "rm")
    carte_mt(im, d, logo); fin(im, out)


def prop_d(T, out):
    """D (« complètement différente, en gardant la DA de Paris : le placement, tout ça ») : podium néon au centre (2 panneaux) devant
    un soleil rétro et une grille en perspective, logo Supercross Paris au-dessus ; places 4 à 10 à gauche ; chrono, meilleur tour et
    logo MX Sim à droite."""
    D_ = os.path.join(T, *TD.SUB.split("/"))
    fa = Image.open(os.path.join(D_, "fond_a.png")).convert("RGBA"); fb = Image.open(os.path.join(D_, "fond_b.png")).convert("RGBA")
    im = Image.new("RGBA", (W, H), (16, 4, 28, 255)); d = ImageDraw.Draw(im)
    # centre : ciel dégradé, soleil rayé, grille au sol
    cx, top, hz = 512, 0, 168
    for y in range(top, hz):
        f = (y - top) / (hz - top); c = tuple(int(a + (b - a) * f) for a, b in zip((22, 6, 40), (92, 18, 110)))
        d.line([((256 + 2) * K, y * K), ((768 - 2) * K, y * K)], fill=c, width=K)
    sun = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sun); R = 78
    for y in range(hz - R, hz):
        f = (y - (hz - R)) / R; c = tuple(int(a + (b - a) * f) for a, b in zip((255, 214, 90), (236, 48, 196)))
        if (y > hz - 40 and (y // 5) % 2 == 0):
            continue
        dx = (R * R - (hz - y) ** 2) ** 0.5
        ds.line([((cx - dx) * K, y * K), ((cx + dx) * K, y * K)], fill=c + (255,), width=K)
    im.alpha_composite(sun)
    d.rectangle([258 * K, hz * K, 766 * K, 256 * K], fill=(26, 6, 44))
    for i in range(-12, 13):
        d.line([(cx * K, hz * K), ((cx + i * 60) * K, 256 * K)], fill=(150, 40, 170), width=K)
    for j, yy in enumerate((174, 184, 198, 218, 246)):
        d.line([(258 * K, yy * K), (766 * K, yy * K)], fill=(150, 40, 170), width=K)
    d.rectangle([0, hz * K, 257 * K, 256 * K], fill=(16, 4, 28)); d.rectangle([767 * K, hz * K, 1024 * K, 256 * K], fill=(16, 4, 28))   # grille : centre seulement
    # logo Supercross Paris en haut au centre
    LOGOS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'commun', 'assets', 'logos')
    sp = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'refs', 'paddock2026', 'logos', 'supercross_paris.webp')).convert('RGBA')
    sp = sp.crop(sp.getbbox()); lw = 150; sp = sp.resize((lw * K, int(lw * sp.height / sp.width) * K), Image.LANCZOS)
    im.alpha_composite(sp, (int((cx - lw / 2) * K), 6 * K))
    rr(d, (cx + 84, 14, cx + 134, 32), 9, (236, 30, 60)); t(d, (cx + 109, 23), "LIVE", 11, BLANC, "mm")
    # podium (2 | 1 | 3)
    steps = [(1, cx - 165, 152, 110), (0, cx - 55, 124, 110), (2, cx + 55, 172, 110)]
    for k, x0, ytop, w in steps:
        num, nom, mq, ec = PIL_[k]
        d.rectangle([x0 * K, ytop * K, (x0 + w) * K, 252 * K], fill=(38, 10, 62))
        d.rectangle([x0 * K, ytop * K, (x0 + w) * K, (ytop + 4) * K], fill=ROSE)
        d.rectangle([x0 * K, (ytop + 4) * K, (x0 + w) * K, (ytop + 8) * K], fill=COUL[mq])
        t(d, (x0 + w / 2, ytop + 32), str(k + 1), 30, ROSE if k else BLANC, "mm")
        t(d, (x0 + w / 2, ytop - 30), nom, 15, BLANC, "mm"); t(d, (x0 + w / 2, ytop - 13), "#%d  %s" % (num, mq), 10, (255, 200, 240), "mm", bold=False)
        if ec:
            t(d, (x0 + w / 2, ytop + 60), ec, 14, BLANC, "mm")
        else:
            t(d, (x0 + w / 2, ytop + 60), "LEADER", 11, (255, 214, 90), "mm")
    # gauche : 4 à 10
    t(d, (14, 18), "CLASSEMENT", 15, BLANC); d.rectangle([14 * K, 30 * K, 120 * K, 33 * K], fill=ROSE)
    h = 30.5
    for j in range(3, 10):
        num, nom, mq, ec = PIL_[j]; y = 40 + (j - 3) * h
        d.line([(10 * K, (y + h - 2) * K), (246 * K, (y + h - 2) * K)], fill=(70, 26, 100), width=K)
        t(d, (24, y + h / 2), str(j + 1), 18, ROSE, "mm")
        d.rectangle([40 * K, (y + 6) * K, 44 * K, (y + h - 8) * K], fill=COUL[mq])
        t(d, (52, y + h / 2), nom, 15, BLANC); t(d, (52 + 0, y + h / 2), "", 10, BLANC)
        t(d, (176, y + h / 2), "#%d" % num, 11, (200, 160, 220), "rm", bold=False)
        t(d, (244, y + h / 2), ec, 14, BLANC, "rm")
    # droite : chrono, meilleur tour, logo MX Sim
    x0 = 768
    t(d, (x0 + 128, 22), "TEMPS RESTANT", 12, (200, 160, 220), "mm", bold=False)
    t(d, (x0 + 128, 56), "04:32 + 1L", 30, BLANC, "mm")
    d.rectangle([(x0 + 40) * K, 80 * K, (x0 + 216) * K, 82 * K], fill=ROSE)
    t(d, (x0 + 128, 102), "MEILLEUR TOUR", 12, (200, 160, 220), "mm", bold=False)
    t(d, (x0 + 128, 132), MT[2], 26, (255, 214, 90), "mm"); t(d, (x0 + 128, 158), "%d - %s" % MT[:2], 14, ROSE, "mm")
    import numpy as np
    mx_ = np.asarray(Image.open(os.path.join(LOGOS, 'user', 'logo mxsim racing.png')).convert('RGB'), float)
    mx_ = Image.fromarray(np.dstack([mx_, np.clip((mx_.max(-1) - 25) * 4, 0, 255)]).astype(np.uint8), 'RGBA'); mx_ = mx_.crop(mx_.getbbox())   # fond noir -> transparent
    mw = 170; mx_ = mx_.resize((mw * K, int(mw * mx_.height / mx_.width) * K), Image.LANCZOS)
    im.alpha_composite(mx_, (int((x0 + 128 - mw / 2) * K), 186 * K))
    for xs in (256, 768):                   # séparations néon entre les zones
        d.line([(xs * K, 6 * K), (xs * K, 250 * K)], fill=ROSE, width=K)
    fin(im, out)


def fin(im, out):
    im.convert("RGB").resize((W, int(H * 55.8 / 52.5)), Image.LANCZOS).save(out)


if __name__ == "__main__":
    T, O = sys.argv[1], sys.argv[2]; os.makedirs(O, exist_ok=True)
    for n, f in (("A", prop_a), ("B", prop_b), ("C", prop_c)):
        f(T, os.path.join(O, "ecran_top10_%s.png" % n))
    print("ok")
