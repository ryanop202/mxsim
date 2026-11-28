"""v43f (« j'aime pas, les noms coupés ; fais une autre proposition, peut-être pas les 22 ») : 2 propositions dessinées à l'échelle de
l'écran (4 panneaux de 256 px côte à côte), pas encore dans la piste :
  B : top 10 sur les 2 panneaux du milieu réunis (512 px) : place, marque, numéro, NOM ENTIER, écart ; dernier panneau : logo MX Sim
  C : les 22 comme aujourd'hui, l'écart à la place du numéro (nom entier)
    py -3.15 pistes/paris-2026/apercu_ecarts2.py <dossier de la piste construite> <sortie.png>"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tableau_direct as TD   # noqa: E402

NOMS = ["OPPLIGER", "THOMAS", "HARRIS", "CLARK", "PIETERS", "MILLER", "COEN", "HICKS", "MANZI", "SOULE", "POLLET", "LOPEZ",
        "VINCENT", "BRUN", "SIMON", "LEBEAU", "LAMARQUE", "BRIAND", "HUDSON", "EKER", "TURNER", "BAZO"]
NUMS = [202, 21, 9, 47, 151, 16, 348, 33, 77, 5, 12, 64, 88, 101, 3, 27, 55, 909, 18, 71, 24, 7]
ECARTS = ["", "+1.4", "+2.9", "+3.3", "+5.8", "+7.0", "+9.6", "+12.1", "+14.7", "+18.2", "+21.5", "+25.0", "+28.4",
          "+33.9", "+41.2", "+48.6", "+55.3", "+1L", "+1L", "+1L", "+2L", "+2L"]
COUL = list(TD.BANDES.values())
F = lambda px: ImageFont.truetype(TD.FONT_B, px)
BLANC = (255, 255, 255)


def ligne(d, x0, y, w, h, k, nom_x, ecart_x1, num=True, fs=17):
    d.rounded_rectangle([x0, y, x0 + w, y + h - 3], 4, fill=TD.VIOLET2)
    d.rounded_rectangle([x0 + 4, y + 2, x0 + 40, y + h - 5], 4, fill=(248, 248, 250))
    p = "%02d" % (k + 1); f = F(fs); tw = d.textlength(p, font=f); d.text((x0 + 22 - tw / 2, y + (h - 3) / 2), p, font=f, fill=(24, 10, 36), anchor="lm")
    d.rectangle([x0 + 44, y + 2, x0 + 50, y + h - 5], fill=COUL[k % len(COUL)])
    if num:
        d.text((x0 + 56, y + (h - 3) / 2), "%d -" % NUMS[k], font=f, fill=TD.ROSE, anchor="lm")
    d.text((x0 + nom_x, y + (h - 3) / 2), NOMS[k], font=f, fill=BLANC, anchor="lm")
    if ECARTS[k]:
        fe = F(fs - 1); te = d.textlength(ECARTS[k], font=fe)
        d.text((x0 + ecart_x1 - te, y + (h - 3) / 2), ECARTS[k], font=fe, fill=TD.ROSE if "L" in ECARTS[k] else BLANC, anchor="lm")


def apercu(T, out):
    D_ = os.path.join(T, *TD.SUB.split("/"))
    fa = Image.open(os.path.join(D_, "fond_a.png")).convert("RGBA"); fb = Image.open(os.path.join(D_, "fond_b.png")).convert("RGBA")
    p1 = fa.crop((0, 0, 256, 256)); p4 = fb.crop((0, 256, 256, 512))
    dt = ImageDraw.Draw(p1); s = "04:32 + 1L"; ft = F(35); dt.text((128, 190), s, font=ft, fill=BLANC, anchor="mm")
    imgs = []
    # B : top 10, 2 panneaux réunis
    B = Image.new("RGBA", (1024, 256), TD.VIOLET + (255,)); B.paste(p1, (0, 0))
    d = ImageDraw.Draw(B); h = 25
    for k in range(10):
        ligne(d, 260, 3 + k * h, 504, h, k, 120, 494, fs=16)
    lg = Image.new('RGBA', (256, 256), TD.VIOLET + (255,)); lg.paste(p4.crop((0, 198, 256, 256)), (0, 99)); B.paste(lg, (768, 0))   # logo MX Sim seul, centré
    imgs.append(("B : top 10, noms entiers + écarts", B))
    # C : 22, écart à la place du numéro
    C = Image.new("RGBA", (1024, 256), TD.VIOLET + (255,)); C.paste(p1, (0, 0)); d = ImageDraw.Draw(C)
    for k in range(22):
        col = k // 8; r = k % 8
        ligne(d, 256 * (col + 1) + 2, 3 + r * 32, 250, 32, k, 56, 246, num=False)
    imgs.append(("C : les 22, écart à la place du numéro", C))
    W = 2048; out_im = Image.new("RGB", (W, 2 * (int(256 * 2 * 55.8 / 52.5) + 50)), (18, 18, 22)); y = 0; dd = ImageDraw.Draw(out_im)
    for titre, im in imgs:
        dd.text((14, y + 8), titre, font=F(28), fill=BLANC); y += 50
        r = im.resize((W, int(256 * 2 * 55.8 / 52.5)), Image.LANCZOS); out_im.paste(r, (0, y)); y += r.height
    out_im.save(out)
    return out


if __name__ == "__main__":
    print(apercu(sys.argv[1], sys.argv[2]))
