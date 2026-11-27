"""v19 (version Zion, « fais des grilles noires, presque un peu pleines, un peu comme les grilles qu'on avait USLAND, et tu mets le
logo Monster Energy ») : la grille de départ USLAND (commun/scripts/props_usland.py : plaque pleine, cadre en tube, charnière continue,
même encombrement que gate01, pas de 4 ft) en NOIR (plaque + tubes), logo Monster Energy sur la face visible une fois tombée.
Logo : celui du fichier de l'utilisateur s'il existe (commun/assets/logos/monster_energy.png), sinon la griffe + le texte relevés sur ZION
(hab_kit.logo) en attendant.

  gate_monster.make(dossier) -> écrit start_gate_monster.jm / .png
"""
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "commun/scripts")); sys.path.insert(0, HERE)
import props_usland as PU      # noqa: E402

BLACK, TUBE = (14, 14, 16), (30, 30, 33)
USER_LOGO = os.path.join(ROOT, "commun/assets", "logos", "monster_energy.png")


def _monster(box_w, box_h):
    """logo RGBA (griffe verte + texte) à coller sur la plaque."""
    if os.path.exists(USER_LOGO):
        return Image.open(USER_LOGO).convert("RGBA")
    import hab_kit as K
    claw, txt = K.logo('monster_claw').convert("RGBA"), K.logo('monster_text').convert("RGBA")
    w = max(claw.width, txt.width); im = Image.new("RGBA", (w, claw.height + txt.height + 8), (0, 0, 0, 0))
    im.alpha_composite(claw, ((w - claw.width) // 2, 0)); im.alpha_composite(txt, ((w - txt.width) // 2, claw.height + 8))
    return im


def _user_logo(kind):
    """v38 (« une grille sur 2 : le logo Venum que je te remets, en blanc ; et le logo Monster, celui que je t'envoie ») : logos de
    l'utilisateur (commun/assets/logos/user/), fond blanc / transparent enlevé ; Venum passé en blanc."""
    from scipy import ndimage
    U = os.path.join(ROOT, "commun/assets", "logos", "user")
    if kind == 'venum':
        im = Image.open(os.path.join(U, "logo venum full.webp")).convert("RGBA"); a = np.asarray(im).astype(float)
        dark = a[..., :3].mean(-1) < 128; al = (a[..., 3] / 255.0) * dark
        out = np.dstack([np.full(al.shape + (3,), 245.0), al * 255]).astype(np.uint8)
    else:
        a = np.asarray(Image.open(os.path.join(U, "logo monster energy.jpg")).convert("RGB")).astype(int)
        bg = (a.min(-1) > 215) & ((a.max(-1) - a.min(-1)) < 30); lab, _ = ndimage.label(bg)
        edge = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
        al = np.where(np.isin(lab, list(edge)), 0, 255).astype(np.uint8); out = np.dstack([a.astype(np.uint8), al])
    im = Image.fromarray(out, "RGBA"); return im.crop(im.getbbox())


def texture(kind=None):
    img = Image.new('RGB', (1024, 1024), BLACK)

    def plate(im):
        W, H = im.size; im.paste(BLACK, (0, 0, W, H))
        lg = _user_logo(kind) if kind else _monster(W, H); s = min(W * 0.62 / lg.width, H * 0.80 / lg.height)
        lg = lg.resize((max(1, int(lg.width * s)), max(1, int(lg.height * s))), Image.LANCZOS)
        base = im.convert("RGBA"); base.alpha_composite(lg, ((W - lg.width) // 2, (H - lg.height) // 2)); im.paste(base.convert("RGB"))
    img.paste(PU.panel((PU.GATE['w'] - 0.26, PU.GATE['h'] - 0.3), 1008, plate).resize((1008, 464), Image.LANCZOS), (8, 8))
    pal = PU.palette(img, ['black', 'red'], [BLACK, TUBE])          # 'red' = la couleur des tubes du modèle USLAND -> noir
    pal.update(plate=('r', (8, 8, 1016, 472)))
    return img, pal


def make_pair(out):
    """v38 : modèle commun, 2 textures (Monster de l'utilisateur / Venum blanc) -> jm, png_monster, png_venum."""
    jm, _ = make(out)
    for kind in ('monster', 'venum'):
        img, _ = texture(kind); img.save(os.path.join(out, 'start_gate_%s.png' % kind))
    return jm, 'start_gate_monster.png', 'start_gate_venum.png'


def make(out):
    img, pal = texture()
    img.save(os.path.join(out, 'start_gate_monster.png'))
    PU.gate_model(pal).write(os.path.join(out, 'start_gate_monster.jm'), (16, 1, 0.35, 0.35, 0.35))   # matière de gate01
    return 'start_gate_monster.jm', 'start_gate_monster.png'


if __name__ == "__main__":
    print(make(sys.argv[1] if len(sys.argv) > 1 else "."))
