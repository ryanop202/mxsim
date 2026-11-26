"""v19 (« les camions des stands ne sont pas très beaux ; reprends les semi-remorques qu'il y a déjà sur un track et change les
sponsors ») : la semi-remorque de JGSX2026Scuttle (statue/semi_1.jm, tracteur + remorque détaillés, roues, chromes) à la place de
notre semi faite main, avec les couleurs et logos des équipes du paddock de Paris (hab_objets2.SEMIS : Honda, Yamaha, Monster,
Kawasaki, KTM, Triumph, Ducati) redessinés sur ses deux flancs de remorque.

Modèle : sommets décalés à notre convention (centre de la remorque en x = 0, +z = l'avant), avant de la remorque à z = -12 ft
(le tracteur reste sur le sol de l'arène : la semi JGSX fait 80 ft, la nôtre 70). Texture : la peau JGSX (ws_semiskin.png) avec
les flancs (UV mesurés sur le modèle : flanc -x = bande y 921-1233 px, flanc +x = y 1337-1648 px, x 450-2030, avant à droite / à
gauche) repeints aux proportions réelles du flanc (58 x 11 ft) : logos jamais déformés ; bande du toit (drapeau US) en noir.

  semi_jgsx.make(dossier_statues) -> (modèle, {équipe: texture})
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
SRC = r"C:/Program Files (x86)/MX Simulator/JGSX2026Scuttle/statue"        # piste installée (pas dans le dépôt : pas à nous)
CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "jgsx_semi")   # copie locale hors dépôt
DX, DZ = 5.0, -6.6 - 12.0                                                  # centre de la remorque / avant de la remorque
PANELS = ((450, 921, 2030, 1233), (450, 1337, 2030, 1648))                 # flancs (px de la peau 2048)
ROOF = (450, 740, 2040, 912)
SKIRTS = ((450, 1233, 2030, 1326), (450, 1648, 2030, 1740))                # bas des flancs (restes du décor JGSX) : noir


def _src(name):
    os.makedirs(CACHE, exist_ok=True); p = os.path.join(CACHE, name)
    if not os.path.exists(p):
        import shutil
        shutil.copy(os.path.join(SRC, name), p)
    return p


def model(out):
    L = open(_src("semi_1.jm")).read().split("\n"); i = 1; res = [L[0]]
    while i < len(L) - 1 and L[i].strip():
        mat = L[i]; nv, nt = map(int, L[i + 1].split()); res += [mat, L[i + 1]]
        for l in L[i + 2:i + 2 + nv]:
            v = l.split(); v[0] = "%.6f" % (float(v[0]) + DX); v[2] = "%.6f" % (float(v[2]) + DZ); res.append(" ".join(v))
        j = i + 2 + nv; n_idx = nt if len(L[j].split()) == 3 else 3 * nt
        res += L[j:j + n_idx]; i = j + n_idx
    res.append("")
    open(os.path.join(out, "semi_jgsx.jm"), "w", newline="\n").write("\n".join(res))
    return "semi_jgsx.jm"


def livery(bg, lgo, W, H):
    """un flanc : fond de l'équipe, gros logo centré, bande noire en bas avec le logo SX Paris (comme nos semis)."""
    import hab_kit as K
    im = Image.new("RGB", (W, H), bg); d = ImageDraw.Draw(im)
    band = int(H * 0.2); d.rectangle([0, H - band, W, H], fill=(18, 18, 20)); d.rectangle([0, H - band - 6, W, H - band], fill=tuple(int(c * 0.6) for c in bg))
    K.fit(im, lgo, (int(W * 0.2), int(H * 0.06), int(W * 0.8), H - band - 12), 0.08)
    sx = K.logo('sxparis'); sx = K.tint(sx, (255, 255, 255))
    K.fit(im, sx, (W - int(W * 0.2), H - band + 4, W - 16, H - 4), 0.05); K.fit(im, sx, (16, H - band + 4, int(W * 0.2), H - 4), 0.05)
    return K.shade_v(im, (0, 0, W, H - band), 1.0, 0.86)


def make(out):
    import hab_kit as K
    from hab_objets2 import SEMIS
    m = model(out); base = Image.open(_src("ws_semiskin.png")).convert("RGB"); tex = {}
    for name, (bg, lg, txt) in SEMIS.items():
        ink = (20, 20, 22) if sum(bg) > 600 else (255, 255, 255)
        lgo = K.logo(lg) if lg else K.text_img(txt, 180, ink, 'ariblk.ttf', italic=0.15)
        if name == 'ktm':
            lgo = K.tint(lgo, (12, 12, 12))
        im = base.copy(); d = ImageDraw.Draw(im)
        for (x0, y0, x1, y1) in PANELS:
            im.paste(livery(bg, lgo, x1 - x0, y1 - y0).convert("RGB"), (x0, y0))
        d.rectangle(ROOF, fill=(18, 18, 20))
        for r_ in SKIRTS:
            d.rectangle(r_, fill=(18, 18, 20))
        fn = "semi_jgsx_%s.png" % name; im.save(os.path.join(out, fn), optimize=True); tex[name] = fn
    return m, tex


if __name__ == "__main__":
    print(make(sys.argv[1] if len(sys.argv) > 1 else "."))
