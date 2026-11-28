"""v43e (proposition, « mettre les secondes de chaque pilote à côté ») : aperçu de l'écran géant avec l'écart au leader à droite de
chaque ligne (police plus petite, alignée à droite ; nom raccourci à NAME_MAX_E lettres pour laisser la place). Pas encore dans la piste.
    py -3.15 pistes/paris-2026/apercu_ecarts.py <dossier de la piste construite> <sortie.png>"""
import os
import re
import sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tableau_direct as TD   # noqa: E402

NAME_MAX_E = 7
ECART_PX, ECART_X1 = 13, 251          # taille de la police de l'écart, bord droit (px du carré)


def apercu(T, out):
    D_ = os.path.join(T, *TD.SUB.split("/"))
    frames = {"a": Image.open(os.path.join(D_, "fond_a.png")).convert("RGBA"), "b": Image.open(os.path.join(D_, "fond_b.png")).convert("RGBA")}
    f1, N, P, Dg, Tt, by = TD._lettres()
    fe = ImageFont.truetype(TD.FONT_B, ECART_PX)

    def larg(f, s):
        return sum(8 if ch == " " else (f[ch][2] - 1 if ch in f else 0) for ch in s)

    def txt(fr, f, h, x, y, s):
        for ch in s:
            if ch == " ":
                x += 8; continue
            if ch not in f:
                continue
            c = f[ch]; fr.alpha_composite(f1.crop((c[0], c[1], c[0] + c[2], c[1] + h)), (int(round(x)), int(round(y)))); x += c[2] - 1
    noms = ["OPPLIGER", "THOMAS", "HARRIS", "CLARK", "PIETERS", "MILLER", "COEN", "HICKS", "MANZI", "SOULE", "POLLET", "LOPEZ",
            "VINCENT", "BRUN", "SIMON", "LEBEAU", "LAMARQUE", "BRIAND", "HUDSON", "EKER", "TURNER", "BAZO"]
    nums = [202, 21, 9, 47, 151, 16, 348, 33, 77, 5, 12, 64, 88, 101, 3, 27, 55, 909, 18, 71, 24, 7]
    mods = ["crf450", "yz450f", "kx450", "450sxf", "fc450", "rmz450", "mc450f", "crf250"]
    ecarts = ["", "+1.4", "+2.9", "+3.3", "+5.8", "+7.0", "+9.6", "+12.1", "+14.7", "+18.2", "+21.5", "+25.0", "+28.4",
              "+33.9", "+41.2", "+48.6", "+55.3", "+1L", "+1L", "+1L", "+2L", "+2L"]
    temps = "04:32 + 1L"
    txt(frames["a"], Tt, 56, TD.PW / 2 - larg(Tt, temps) / 2, TD.TIME_Y, temps)
    for k in range(22):
        tex, y0 = ("a", 256) if k < TD.NPAN else ("b", 0) if k < 2 * TD.NPAN else ("b", 256)
        yy = y0 + (k % TD.NPAN) * TD.ROW_H + 3; fr = frames[tex]; p = "%02d" % (k + 1)
        txt(fr, Dg, 26, (TD.POS_X0 + TD.POS_X1) / 2 - larg(Dg, p) / 2, yy, p)
        mq = next((kk for r, kk in TD.MARQUES if re.match(r, mods[k % len(mods)])), "none"); bi = list(TD.BANDES).index(mq)
        fr.alpha_composite(f1.crop((bi * 10, by, bi * 10 + TD.BAR_X1 - TD.BAR_X0, by + TD.ROW_H - 4)), (TD.BAR_X0, yy - 1))
        d = ImageDraw.Draw(fr); w = d.textlength(ecarts[k], font=fe) if ecarts[k] else 0
        nm = noms[k][:TD.NAME_MAX]
        while nm and TD.NAME_X + larg(N, nm) > ECART_X1 - w - 6:          # le nom s'arrête avant l'écart (lettres en trop enlevées)
            nm = nm[:-1]
        txt(fr, P, 26, TD.NUM_X, yy, "%d -" % nums[k]); txt(fr, N, 26, TD.NAME_X, yy, nm)
        if ecarts[k]:
            d.text((ECART_X1 - w, yy + 7), ecarts[k], font=fe, fill=(255, 255, 255, 255) if "L" not in ecarts[k] else TD.ROSE + (255,))
    full = Image.new("RGBA", (4 * TD.PW, 256))
    for i, (tex, y0, _) in enumerate(TD.PANNEAUX):
        full.paste(frames[tex].crop((0, y0, TD.PW, y0 + 256)), (i * TD.PW, 0))
    full.resize((4 * TD.PW * 2, int(256 * 2 * 55.8 / 52.5)), Image.LANCZOS).save(out)
    return out


if __name__ == "__main__":
    print(apercu(sys.argv[1], sys.argv[2]))
