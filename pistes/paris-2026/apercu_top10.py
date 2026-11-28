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
        d.rectangle([(x0 + 41) * K, (y + 2) * K, (x0 + 46) * K, (y + h - 5) * K], fill=COUL[mq])
        rr(d, (x0 + 51, y + 3, x0 + 97, y + h - 6), 4, (BLANC if lead else ROSE)); t(d, (x0 + 74, y + h / 2 - 1.5), str(num), 14, (ROSE if lead else BLANC), "mm")
        t(d, (x0 + 106, y + h / 2 - 1.5), nom, 16, BLANC)
        t(d, (x0 + 300, y + h / 2 - 1.5), mq, 11, (255, 220, 245) if lead else GRIS, bold=False)
        t(d, (x1 - 18, y + h / 2 - 1.5), "LEADER" if lead else ec, 15 if not lead else 12, BLANC, "rm")
    carte_mt(im, d, logo); fin(im, out)


def prop_b(T, out):
    """B : le leader en grand (carte), 2 et 3 en moyen, 4 à 10 en liste à côté."""
    im, logo = base(T); d = ImageDraw.Draw(im)
    num, nom, mq, _ = PIL_[0]; x0 = 262
    rr(d, (x0, 4, x0 + 246, 132), 10, ROSE); d.rectangle([(x0 + 10) * K, 16 * K, (x0 + 16) * K, 120 * K], fill=COUL[mq])
    t(d, (x0 + 28, 34), "1", 46, BLANC); t(d, (x0 + 70, 26), "LEADER", 13, (255, 220, 245))
    t(d, (x0 + 70, 56), nom, 24, BLANC); t(d, (x0 + 28, 100), "#%d" % num, 22, NOIR); t(d, (x0 + 120, 102), mq, 14, (255, 230, 248), bold=False)
    for j in (1, 2):
        num, nom, mq, ec = PIL_[j]; y = 138 + (j - 1) * 58
        rr(d, (x0, y, x0 + 246, y + 54), 8, VIO3); d.rectangle([(x0 + 8) * K, (y + 9) * K, (x0 + 13) * K, (y + 45) * K], fill=COUL[mq])
        t(d, (x0 + 24, y + 27), str(j + 1), 30, BLANC); t(d, (x0 + 58, y + 18), nom, 17, BLANC)
        t(d, (x0 + 58, y + 40), "#%d  %s" % (num, mq), 11, ROSE, bold=False); t(d, (x0 + 238, y + 27), ec, 17, BLANC, "rm")
    x0 = 518; h = 36
    for j in range(3, 10):
        num, nom, mq, ec = PIL_[j]; y = 4 + (j - 3) * h
        para(d, x0, y, x0 + 244, y + h - 4, 8, VIO2 if j % 2 else VIO3)
        rr(d, (x0 + 4, y + 4, x0 + 36, y + h - 8), 3, BLANC); t(d, (x0 + 20, y + h / 2 - 2), str(j + 1), 15, NOIR, "mm")
        d.rectangle([(x0 + 40) * K, (y + 4) * K, (x0 + 45) * K, (y + h - 8) * K], fill=COUL[mq])
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
        d.rectangle([(x0 + 52) * K, (y + 6) * K, (x0 + 57) * K, (y + h - 10) * K], fill=COUL[mq])
        t(d, (x0 + 65, y + 17), nom, 18, BLANC)
        t(d, (x0 + 65, y + 36), "#%d  ·  %s" % (num, mq), 11, (255, 225, 248) if lead else ROSE, bold=False)
        t(d, (x0 + 236, y + h / 2 - 2), "LEADER" if lead else ec, 12 if lead else 17, BLANC, "rm")
    carte_mt(im, d, logo); fin(im, out)


def fin(im, out):
    im.convert("RGB").resize((W, int(H * 55.8 / 52.5)), Image.LANCZOS).save(out)


if __name__ == "__main__":
    T, O = sys.argv[1], sys.argv[2]; os.makedirs(O, exist_ok=True)
    for n, f in (("A", prop_a), ("B", prop_b), ("C", prop_c)):
        f(T, os.path.join(O, "ecran_top10_%s.png" % n))
    print("ok")
