"""Habillage « USLAND Supercross Paris 2026 » de l'arène : écrans, enseigne intérieure, bandeau LED du sol.

Le logo est le vrai fichier fourni (assets/usland_logo.png), détouré et posé sans déformation.
Chaque visuel est dessiné au ratio exact de sa surface 3D, dans une texture en puissance de 2 ;
la partie utilisée (u1, v1) est renvoyée pour régler les UV (rien n'est étiré).
Rappel du sens des UV (comme OBJ / Blender) : v = 0 en bas de l'image.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
LOGO = os.path.join(REPO, "assets", "usland_logo.png")

NAVY = (22, 26, 55)
RED = (207, 11, 78)          # rouge des marques du logo (mesuré sur le fichier)
WHITE = (250, 250, 250)
BLACK = (8, 9, 16)

EVENT = "SUPERCROSS"
CITY = "PARIS"
YEAR = "2026"
DATES = "21 & 22 NOVEMBRE 2026"   # dates affichées sur les écrans des visuels de référence

# surfaces (m) -> ratio largeur / hauteur
MAIN = (70.0, 18.0)          # écran central au-dessus du départ
SIDE = (16.0, 9.0)           # écrans latéraux
SIGN = (24.0, 3.0)           # enseigne intérieure sous l'écran
LED_H = 0.8                  # hauteur du bandeau LED au pied des tribunes
LED_SEG = 12.8               # longueur d'un motif du bandeau (m) -> texture 2048 x 128 au ratio exact
PLAN_K = 1.0                 # agrandissement en plan de l'arène (build.py) : les écrans s'élargissent d'autant,
                             # les visuels sont dessinés au ratio FINAL (largeur x K / hauteur) : rien n'est étiré


def aspect(size):
    return size[0] * PLAN_K / size[1]


# ------------------------------------------------------------------ outils
def _font(px, bold=True):
    path = r"C:\Windows\Fonts\bahnschrift.ttf"
    try:
        f = ImageFont.truetype(path, px)
        f.set_variation_by_name("Bold SemiCondensed" if bold else "SemiCondensed")
        return f
    except Exception:
        return ImageFont.truetype(r"C:\Windows\Fonts\ARIALNB.TTF", px)


_LOGO = None


def logo_rgba(colour=WHITE, accent=RED):
    """Logo USLAND détouré : encre -> colour, marques rouges -> accent. Tableau RGBA float (alpha 0..1)."""
    global _LOGO
    if _LOGO is None:
        c = np.array(Image.open(LOGO).convert("RGB")).astype(float)
        ink = c.min(2) < 150
        ys, xs = np.nonzero(ink)
        c = c[ys.min() - 4:ys.max() + 5, xs.min() - 4:xs.max() + 5]
        red = (c[..., 0] > 150) & (c[..., 1] < 110)
        a = np.clip((175 - c.min(2)) / 135, 0, 1)     # l'ombre portée grise du fichier (190-235) est exclue
        a[red] = 1
        _LOGO = (a, red)
    a, red = _LOGO
    rgb = np.where(red[..., None], np.array(accent, float), np.array(colour, float))
    return np.dstack([rgb, a])


def _paste(img, rgba, box):
    """Pose rgba dans box (x0, y0, x1, y1) en gardant ses proportions, centré."""
    x0, y0, x1, y1 = box
    h, w = rgba.shape[:2]
    s = min((x1 - x0) / w, (y1 - y0) / h)
    W, H = max(1, int(round(w * s))), max(1, int(round(h * s)))
    ch = [np.array(Image.fromarray(np.clip(rgba[..., k] * (255 if k == 3 else 1), 0, 255).astype(np.uint8))
                   .resize((W, H), Image.LANCZOS)).astype(float) for k in range(4)]
    A = (ch[3] / 255.0)[..., None]
    ox, oy = int((x0 + x1 - W) / 2), int((y0 + y1 - H) / 2)
    base = np.array(img).astype(float)
    sub = base[oy:oy + H, ox:ox + W]
    rgb = np.dstack(ch[:3])
    if base.shape[2] == 4:
        a0 = sub[..., 3:4] / 255.0
        out_a = A + a0 * (1 - A)
        sub[..., :3] = np.where(out_a > 0, (rgb * A + sub[..., :3] * a0 * (1 - A)) / np.maximum(out_a, 1e-6), 0)
        sub[..., 3:4] = out_a * 255
    else:
        sub[...] = sub * (1 - A) + rgb * A
    base[oy:oy + H, ox:ox + W] = sub
    img.paste(Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)))
    return (ox, oy, ox + W, oy + H)


def _text_line(img, parts, cy, h_px, cx=None, max_w=None):
    """Ligne de texte centrée (cx) faite de morceaux [(texte, couleur), ...] ; h_px = hauteur des capitales."""
    d = ImageDraw.Draw(img)
    size = int(h_px / 0.72)
    while True:
        f = _font(size)
        cap = f.getbbox("H")
        k = h_px / max(1, cap[3] - cap[1])
        f = _font(max(8, int(size * k)))
        widths = [d.textlength(t, font=f) for t, _ in parts]
        total = sum(widths)
        if max_w is None or total <= max_w or size < 10:
            break
        h_px *= max_w / total * 0.995
        size = int(h_px / 0.72)
    cx = img.size[0] / 2 if cx is None else cx
    x = cx - total / 2
    for (t, col), w in zip(parts, widths):
        d.text((x, cy), t, font=f, fill=tuple(col) + ((255,) if img.mode == "RGBA" else ()), anchor="lm")
        x += w
    return total


def _background(w, h, glow=0.55):
    """Fond d'écran : noir -> marine au centre, léger voile rouge en bas (ambiance soirée)."""
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    r = np.hypot((xx - w / 2) / (w * 0.55), (yy - h * 0.45) / (h * 0.75))
    t = np.clip(1 - r, 0, 1) ** 1.4 * glow
    img = np.array(BLACK, float) * (1 - t[..., None]) + np.array(NAVY, float) * t[..., None] * 1.6
    low = np.clip((yy / h - 0.70) / 0.30, 0, 1) ** 2 * 0.22
    img = img * (1 - low[..., None]) + np.array(RED, float) * low[..., None] * 0.55
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")


def _canvas(aspect, W):
    """Texture W x H (puissance de 2) contenant une zone au ratio exact, collée en bas à gauche.
    Renvoie (largeur, hauteur) de la zone et (u1, v1)."""
    h = W / aspect
    H = 1 << int(np.ceil(np.log2(h)))
    if h > H:
        H *= 2
    cw, ch = W, int(round(h))
    return (W, H), (cw, ch), (1.0, ch / H)


def _place_rgba(content, size):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    img.paste(content, (0, size[1] - content.size[1]))
    return img


def _place(content, size, mode="RGB", fill=BLACK):
    W, H = size
    img = Image.new(mode, (W, H), tuple(fill) + ((255,) if mode == "RGBA" else ()))
    img.paste(content, (0, H - content.size[1]))
    return img


# ------------------------------------------------------------------ visuels
def poster_main(W=2048):
    """Écran central 70 x 18 m : logo USLAND, puis « SUPERCROSS PARIS 2026 »."""
    size, (cw, ch), uv = _canvas(aspect(MAIN), W)
    im = _background(cw, ch)
    box = _paste(im, logo_rgba(), (cw * 0.22, ch * 0.10, cw * 0.78, ch * 0.50))
    d = ImageDraw.Draw(im)
    y = ch * 0.585
    d.rectangle([cw * 0.30, y, cw * 0.70, y + max(2, ch * 0.012)], fill=RED)
    _text_line(im, [(EVENT + " ", WHITE), (CITY + " ", RED), (YEAR, WHITE)], ch * 0.77, ch * 0.20, max_w=cw * 0.80)
    return _place(im, size), uv


def poster_side(asp=None, W=1024, dates=True):
    """Écrans latéraux / façade : logo, « SUPERCROSS PARIS », dates."""
    size, (cw, ch), uv = _canvas(asp or aspect(SIDE), W)
    im = _background(cw, ch, glow=0.7)
    _paste(im, logo_rgba(), (cw * 0.12, ch * 0.10, cw * 0.88, ch * 0.42))
    _text_line(im, [(EVENT + " ", WHITE), (CITY, RED)], ch * 0.58, ch * 0.13, max_w=cw * 0.86)
    d = ImageDraw.Draw(im)
    d.rectangle([cw * 0.38, ch * 0.70, cw * 0.62, ch * 0.70 + max(2, ch * 0.008)], fill=RED)
    _text_line(im, [(DATES if dates else YEAR, WHITE)], ch * 0.81, ch * 0.075, max_w=cw * 0.80)
    return _place(im, size), uv


def led_board(W=2048):
    """Motif du bandeau LED (12,8 x 0,8 m, ratio 16:1) : USLAND | SUPERCROSS PARIS 2026.
    Un seul USLAND par motif : deux USLAND ne sont jamais côte à côte."""
    H = int(W * LED_H / LED_SEG)
    im = Image.new("RGB", (W, H), BLACK)
    d = ImageDraw.Draw(im)
    half = W // 2
    d.rectangle([0, 0, half - 1, H], fill=NAVY)
    _paste(im, logo_rgba(), (half * 0.10, H * 0.16, half * 0.90, H * 0.84))
    _text_line(im, [(EVENT + " ", WHITE), (CITY + " ", RED), (YEAR, WHITE)], H * 0.52, H * 0.50,
               cx=half + half / 2, max_w=half * 0.86)
    # séparateurs rouges fins entre les deux moitiés et en bout de motif
    for x in (half - 2, W - 3):
        d.rectangle([x, 0, x + 2, H], fill=RED)
    return im


def sign_interior(W=2048):
    """Enseigne lumineuse sous l'écran (24 x 3 m) : logo + « SUPERCROSS PARIS 2026 », blanc, fond transparent."""
    size, (W, H), uv = _canvas(aspect(SIGN), W)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _paste(im, logo_rgba(WHITE, RED), (W * 0.06, H * 0.12, W * 0.42, H * 0.88))
    _text_line(im, [(EVENT + " ", WHITE), (CITY + " ", RED), (YEAR, WHITE)], H * 0.52, H * 0.50,
               cx=W * 0.71, max_w=W * 0.52)
    return _place_rgba(im, size), uv


# ------------------------------------------------------------------ export
UV = {}     # nom de texture -> (u1, v1)


def entrance_tex(w, h):
    return "poster_entree_%d.png" % int(round(w * 10))


def build_all(outdir, entrances=()):
    """Écrit les textures d'habillage ; entrances = [(largeur, hauteur)] des écrans de façade."""
    os.makedirs(outdir, exist_ok=True)
    written = []
    im, uv = poster_main(); im.save(os.path.join(outdir, "poster_main.png")); UV["poster_main.png"] = uv
    im, uv = poster_side(); im.save(os.path.join(outdir, "poster_side.png")); UV["poster_side.png"] = uv
    written += ["poster_main.png", "poster_side.png"]
    for w, h in entrances:
        name = entrance_tex(w, h)
        im, uv = poster_side(aspect((w, h))); im.save(os.path.join(outdir, name)); UV[name] = uv
        written.append(name)
    led_board().save(os.path.join(outdir, "led_board-hrepeat.png")); written.append("led_board-hrepeat.png")
    im, uv = sign_interior(); im.save(os.path.join(outdir, "signage_usland.png")); UV["signage_usland.png"] = uv
    written.append("signage_usland.png")
    return written


def uv_extent(tex):
    """(u1, v1) d'une texture d'habillage (calculé sans écrire le fichier si besoin)."""
    if tex not in UV:
        if tex == "poster_main.png":
            UV[tex] = _canvas(aspect(MAIN), 2048)[2]
        elif tex == "poster_side.png":
            UV[tex] = _canvas(aspect(SIDE), 1024)[2]
        elif tex == "signage_usland.png":
            UV[tex] = _canvas(aspect(SIGN), 2048)[2]
        else:
            raise KeyError(tex)
    return UV[tex]


def readable(mesh):
    """True si la texture se lit à l'endroit (ni miroir, ni tête en bas) vue de face (repère X, Y, Z haut)."""
    V, F, T = mesh.V, mesh.F, mesh.UV
    a, b, c = F[0]
    e1, e2 = V[b] - V[a], V[c] - V[a]
    d1, d2 = T[b] - T[a], T[c] - T[a]
    det = d1[0] * d2[1] - d1[1] * d2[0]
    tu = (e1 * d2[1] - e2 * d1[1]) / det          # dP/du
    tv = (e2 * d1[0] - e1 * d2[0]) / det          # dP/dv
    n = np.cross(e1, e2)
    n /= np.linalg.norm(n)
    right = np.cross(-n, np.array([0.0, 0.0, 1.0]))
    return float(np.dot(tu, right)) > 0 and float(tv[2]) > 0
