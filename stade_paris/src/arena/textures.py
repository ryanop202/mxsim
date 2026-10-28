"""Textures procédurales (numpy + PIL). Toutes reproductibles (graine fixe).

Nommage MX Simulator : '-repeat' juste avant l'extension => texture répétée ;
compagnons '_norm' (normales tangentes) et '_spec' (couleur spéculaire, alpha = exposant/128).
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

RNG = np.random.default_rng(92)


def _noise(size, scale, octaves=4, seed=0):
    """Bruit fractal lissé périodique (valeurs ~[0,1])."""
    rng = np.random.default_rng(seed)
    out = np.zeros((size, size))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        cells = max(2, int(size / scale * (2 ** o)))
        g = rng.random((cells, cells))
        img = Image.fromarray((g * 255).astype(np.uint8)).resize((size, size), Image.BICUBIC)
        # rendre périodique : moyenne avec la version décalée
        a = np.asarray(img, float) / 255
        a = 0.5 * (a + np.roll(np.roll(a, size // 2, 0), size // 2, 1))
        out += amp * a
        tot += amp
        amp *= 0.5
    out /= tot
    return (out - out.min()) / max(1e-9, out.max() - out.min())


def _save(arr, path, mode="RGB"):
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    Image.fromarray(arr, mode).save(path)


def _rgb(c, size):
    return np.broadcast_to(np.array(c, float), (size, size, 3)).copy()


def _normal_from_height(h, strength):
    gy, gx = np.gradient(h)
    n = np.stack([-gx * strength, -gy * strength, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return (n * 0.5 + 0.5) * 255


def concrete_white(size=1024):
    n1 = _noise(size, 64, 5, 1); n2 = _noise(size, 8, 2, 2)
    base = _rgb((233, 231, 225), size)
    v = (n1 - 0.5) * 10 + (n2 - 0.5) * 7
    grain = RNG.normal(0, 3.0, (size, size))
    return base + (v + grain)[..., None], (n1 * 0.6 + n2 * 0.4 + grain / 40)


def crown_panel(size=512):
    """Panneau de couronne : béton blanc hydrogommé + joint fin périphérique (≈2 cm)."""
    col, h = concrete_white(size)
    j = max(2, size // 256)
    m = np.zeros((size, size))
    m[:j, :] = m[-j:, :] = m[:, :j] = m[:, -j:] = 1
    col = col * (1 - 0.16 * m[..., None])        # joints fins et discrets (couronne lisse sur P1-P4)
    # léger ombrage sous le joint horizontal supérieur
    sh = np.zeros((size, size)); sh[j:3 * j, :] = 0.03
    col = col * (1 - sh[..., None])
    h = h * 0.3 - m * 1.5
    return col, h


def alu_white(size=512):
    streak = _noise(size, 4, 2, 5)
    streak = np.repeat(streak.mean(1, keepdims=True), size, 1)
    base = _rgb((238, 239, 240), size)
    return base + ((streak - 0.5) * 6)[..., None], streak * 0.1


def glass_frit(size=512):
    """Verre sérigraphié des écailles (P1-P3) : centre clair laissant voir la structure (bleu-gris),
    sérigraphie blanche dense sur une bande périphérique, potelet et traverses visibles par transparence."""
    y = np.linspace(0, 1, size)[:, None]; x = np.linspace(0, 1, size)[None, :]
    border = np.minimum(np.minimum(x, 1 - x), np.minimum(y, 1 - y))
    edge = np.clip(1 - border * 9, 0, 1)
    yy, xx = np.mgrid[0:size, 0:size]
    dots = (((xx % 6) - 2.5) ** 2 + ((yy % 6) - 2.5) ** 2) < 4
    clear = np.array([176, 192, 204], float) + (1 - y) * np.array([10, 8, 6])     # reflet du ciel en haut
    frit = np.array([242, 244, 245], float)
    k = np.clip(0.18 + 0.82 * edge + dots * 0.10, 0, 1)[..., None]
    col = clear * (1 - k) + frit * k
    # structure derrière le verre : potelet vertical + 2 traverses (P1 : lignes sombres fines)
    bars = np.exp(-((x - 0.62) / 0.010) ** 2) + np.exp(-((y - 0.22) / 0.008) ** 2) * 0.7 + np.exp(-((y - 0.82) / 0.008) ** 2) * 0.7
    col = col * (1 - 0.35 * np.clip(bars, 0, 1)[..., None] * (1 - k))
    return col, k[..., 0] * 0.05


def night_wash(col, tint=(0.80, 0.70, 1.0), lo=1.0, hi=0.35):
    """Version nocturne : lavage LED depuis le pied de l'écaille (fort en bas, faible en haut)."""
    size = col.shape[0]
    g = np.linspace(hi, lo, size)[:, None, None]          # ligne 0 = haut de l'image
    return np.clip(col * np.array(tint) * g * 1.1, 0, 255)


def glass_dark(size=512):
    y = np.linspace(0, 1, size)[:, None]
    col = np.zeros((size, size, 3))
    col[...] = np.array([52, 66, 74]) + (1 - y)[..., None] * np.array([40, 46, 50])
    return col, np.zeros((size, size))


def curtain_wall(size=1024, cols=4, rows=2, mullion=0.018):
    """Mur-rideau : vitrage sombre + meneaux blancs (texture en 1 module de 'cols' x 'rows' cases)."""
    col, _ = glass_dark(size)
    yy, xx = np.mgrid[0:size, 0:size] / size
    m = (np.abs(((xx * cols) % 1) - 0.5) > 0.5 - mullion * cols) | (np.abs(((yy * rows) % 1) - 0.5) > 0.5 - mullion * rows)
    col[m] = (226, 228, 230)
    h = m.astype(float)
    return col, h


def roof_kalzip(size=1024, seams=16):
    n = _noise(size, 128, 4, 7)
    base = _rgb((196, 194, 186), size)
    xx = np.arange(size)[None, :] / size * seams
    f = np.abs((xx % 1) - 0.5)
    seam = np.exp(-((f - 0.5) / 0.02) ** 2)
    shade = np.clip((f - 0.42) * 6, 0, 1) * 0.06
    col = base * (1 - shade[..., None]) + ((n - 0.5) * 10)[..., None] - seam[..., None] * 35
    col += (seam > 0.5)[..., None] * 0
    h = np.broadcast_to(seam, (size, size)) * 2.0
    return col, h


def concrete_grey(size=1024):
    n = _noise(size, 48, 5, 11); g = RNG.normal(0, 4, (size, size))
    return _rgb((150, 150, 147), size) + ((n - 0.5) * 22 + g)[..., None], n


def seat_black(size=256):
    n = _noise(size, 32, 3, 13)
    return _rgb((34, 35, 38), size) + ((n - 0.5) * 6)[..., None], n * 0.2


def steel_black(size=256):
    n = _noise(size, 32, 3, 17)
    return _rgb((30, 31, 33), size) + ((n - 0.5) * 6)[..., None], n * 0.1


def steel_galv(size=256):
    n = _noise(size, 16, 3, 19)
    streak = np.repeat(_noise(size, 4, 2, 21).mean(0, keepdims=True), size, 0)
    return _rgb((168, 172, 176), size) + ((n - 0.5) * 18 + (streak - 0.5) * 20)[..., None], n * 0.1


def wall_black(size=512, panel=8):
    col = _rgb((24, 24, 26), size)
    yy, xx = np.mgrid[0:size, 0:size]
    m = ((xx % (size // panel)) < 2) | ((yy % (size // panel)) < 2)
    col[m] = (14, 14, 15)
    return col, m * 1.0


def projection_screen(size=1024):
    """Écran de projection (photos P8/P10 : surface blanc mat, légèrement grise)."""
    y = np.linspace(0, 1, size)[:, None]
    col = _rgb((214, 216, 218), size) - (np.abs(y - 0.5) * 18)[..., None]
    return col, np.zeros((size, size))


def led_panel_off(size=512, pitch=6):
    """Écran LED éteint : noir avec trame de pixels."""
    col = _rgb((18, 19, 21), size)
    yy, xx = np.mgrid[0:size, 0:size]
    m = ((xx % pitch) < 2) & ((yy % pitch) < 2)
    col[m] = (36, 38, 42)
    return col, m * 0.5


def white_matte(size=64):
    return _rgb((240, 240, 238), size), np.zeros((size, size))


def light_emit(size=64):
    return _rgb((255, 253, 240), size), np.zeros((size, size))


def led_ribbon(w=2048, h=128):
    """Anneau LED intérieur : bandes vertes/blanches sur fond noir (cf. P9) – motif générique."""
    img = Image.new("RGB", (w, h), (8, 8, 10))
    d = ImageDraw.Draw(img)
    for i in range(0, w, 128):
        d.rectangle([i + 8, 22, i + 104, h - 22], fill=(60, 210, 70))
    return np.asarray(img, float), None


def railing_bars(size=256, bars=16):
    """Garde-corps : lisse haute + barreaux, alpha découpé (seuil MX 0,75)."""
    rgba = np.zeros((size, size, 4))
    rgba[..., :3] = (205, 207, 210)
    yy, xx = np.mgrid[0:size, 0:size]
    bar = (xx % (size // bars)) < 3
    rail = (yy < 14) | ((yy > size - 22) & (yy < size - 14))
    rgba[..., 3] = np.where(bar | rail, 255, 0)
    return rgba


def _fonts(size):
    font_path = r"C:\Windows\Fonts\bahnschrift.ttf"
    try:
        f1 = ImageFont.truetype(font_path, size); f1.set_variation_by_name("Bold SemiCondensed")
        f2 = ImageFont.truetype(font_path, size); f2.set_variation_by_name("SemiCondensed")
    except Exception:
        f1 = f2 = ImageFont.truetype(r"C:\Windows\Fonts\ARIALNB.TTF", size)
    return f1, f2


def signage(w=4096, h=512):
    """Enseigne « PARIS LA DEFENSE ARENA » : lettres boîtier anthracite + logo vert (P1).

    Ratio largeur/hauteur de l'image = 8 : le panneau 3D doit respecter ce ratio.
    """
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    logo_w = sum(h * (0.40 - 0.03 * k) * 0.45 * 1.15 for k in range(7)) + h * 0.06
    # taille de police ajustée pour remplir la largeur restante
    size = int(h * 0.8)
    while True:
        f1, f2 = _fonts(size)
        tw = d.textlength("PARIS LA DEFENSE ", font=f1) + d.textlength("ARENA", font=f2)
        if logo_w + tw + h * 0.25 <= w * 0.985 or size < 20:
            break
        size -= 4
    # logo : 7 « feuilles » (demi-ellipses pointues), hauteur décroissante, séparées
    x = h * 0.06
    base = h * 0.76
    for k in range(7):
        hh = h * (0.40 - 0.03 * k)
        ww = hh * 0.45
        top = base - hh
        d.pieslice([x, top, x + ww * 2, base + hh * 0.05], 180, 270, fill=(52, 205, 56, 255))
        d.rectangle([x, top + hh * 0.5, x + ww, base], fill=(52, 205, 56, 255))
        x += ww * 1.15
    x = logo_w + h * 0.10
    d.text((x, h * 0.53), "PARIS LA DEFENSE", font=f1, fill=(38, 44, 52, 255), anchor="lm")
    x += d.textlength("PARIS LA DEFENSE ", font=f1)
    d.text((x, h * 0.53), "ARENA", font=f2, fill=(38, 44, 52, 255), anchor="lm")
    return np.asarray(img, float)


def signage_interior(w=2048, h=256):
    """Enseigne intérieure blanche sous l'écran (P8, P9)."""
    a = signage(w, h)
    m = a[..., 3] > 0
    green = (a[..., 1] > 150) & (a[..., 0] < 120)
    a[m & ~green, :3] = (235, 235, 235)
    return a


def floor_tiles_ppm(size=256, tiles=2):
    """Dalles de protection du sol (Terraplas, P8/P10) – tuile terrain."""
    n = _noise(size, 16, 3, 23)
    col = _rgb((150, 153, 156), size) + ((n - 0.5) * 18)[..., None]
    yy, xx = np.mgrid[0:size, 0:size]
    m = ((xx % (size // tiles)) < 2) | ((yy % (size // tiles)) < 2)
    col[m] = (110, 112, 115)
    return col


def plaza_ppm(size=256):
    """Parvis : dalles claires en bandes de gris (P2)."""
    n = _noise(size, 32, 3, 29)
    col = _rgb((196, 198, 200), size) + ((n - 0.5) * 16)[..., None]
    rng = np.random.default_rng(31)
    for r in range(0, size, size // 8):
        col[r:r + size // 8] *= rng.uniform(0.86, 1.02)
    col[::size // 8] = (150, 152, 155)
    return col


def yellow_line_ppm(size=256):
    col = floor_tiles_ppm(size)
    col[:, size // 2 - 10:size // 2 + 10] = (210, 175, 40)
    return col


def office_ribbon(size=1024):
    """Façade de bureaux : panneau blanc + fenêtre en bandeau (1 tuile = 1 étage de 3,52 m x 7 m)."""
    col, h = concrete_white(size)
    yy, xx = np.mgrid[0:size, 0:size] / size
    win = (yy > 0.30) & (yy < 0.78)                 # bandeau vitré 1,7 m (image : v=0 en bas -> ligne inversée)
    win = win[::-1]
    g, _ = glass_dark(size)
    col[win] = g[win] * 0.9 + 12
    mull = win & (np.abs(((xx * 5) % 1) - 0.5) > 0.485)
    col[mull] = (210, 212, 214)
    h = h * 0.2 - win * 1.0
    return col, h


def skin_light(size=512, mull=4):
    """Peau intérieure derrière les écailles (P1-P3) : vitrage clair gris-bleu, montants blancs.
    Remplace le verre sombre qui créait des rayures noires entre les écailles."""
    y = np.linspace(0, 1, size)[:, None]
    col = np.zeros((size, size, 3))
    col[...] = np.array([188, 200, 208]) + (1 - y)[..., None] * np.array([18, 16, 12])
    yy, xx = np.mgrid[0:size, 0:size]
    m = (xx % (size // mull)) < 5
    col[m] = (232, 234, 236)
    return col, None


def roof_under(size=512, ribs=8):
    """Sous-face du bac acier de toiture (intérieur) : gris très sombre nervuré."""
    n = _noise(size, 32, 3, 37)
    xx = np.arange(size)[None, :] / size * ribs
    rib = (np.abs((xx % 1) - 0.5) < 0.12)
    col = _rgb((40, 41, 44), size) + ((n - 0.5) * 6)[..., None]
    col[np.broadcast_to(rib, (size, size))] = (52, 53, 57)
    return col, np.broadcast_to(rib, (size, size)) * 1.0


def seat_row(size=128):
    """Silhouette d'un siège (pas 0,50 m) pour la version lointaine des rangs, alpha découpé."""
    rgba = np.zeros((size, size, 4))
    rgba[..., :3] = (36, 37, 40)
    yy, xx = np.mgrid[0:size, 0:size] / size
    yy = yy[::-1]                                  # v=0 en bas de l'image
    body = (xx > 0.06) & (xx < 0.94) & (yy < 0.93)
    corner = ((xx - 0.18) ** 2 + (yy - 0.80) ** 2 < 0.13 ** 2) | ((xx - 0.82) ** 2 + (yy - 0.80) ** 2 < 0.13 ** 2)
    top_ok = (yy < 0.80) | ((xx > 0.18) & (xx < 0.82)) | corner
    leg = (xx > 0.44) & (xx < 0.56) & (yy < 0.30)
    a = (body & top_ok & (yy > 0.28)) | leg
    rgba[..., 3] = np.where(a, 255, 0)
    shade = 1 - 0.25 * yy
    rgba[..., :3] *= shade[..., None]
    return rgba[::-1]


def seat_band(w=128, h=128):
    """Rangée de sièges opaque (1 siège = 1 tuile en u) : dossier plastique noir, joint sombre entre
    sièges, coins hauts arrondis sur fond d'ombre, arête haute éclairée, ligne de l'assise relevée."""
    yy, xx = np.mgrid[0:h, 0:w] / np.array([h, w], float)[:, None, None]
    yy = 1 - yy                                     # v=0 en bas de l'image
    col = np.zeros((h, w, 3)); col[...] = (14, 14, 16)            # ombre / jour entre sièges
    body = (xx > 0.05) & (xx < 0.95)
    r = 0.16
    corner_out = ((xx < 0.05 + r) & (yy > 1 - r) & (((xx - 0.05 - r) / r) ** 2 + ((yy - 1 + r) / r) ** 2 > 1)) |                  ((xx > 0.95 - r) & (yy > 1 - r) & (((xx - 0.95 + r) / r) ** 2 + ((yy - 1 + r) / r) ** 2 > 1))
    seat = body & ~corner_out
    shade = 36 + 10 * yy - 8 * np.abs(xx - 0.5)
    col[seat] = np.stack([shade, shade + 1, shade + 4], -1)[seat]
    col[seat & (yy > 0.93)] += 18                                   # arête haute
    col[seat & (np.abs(yy - 0.42) < 0.02)] -= 12                    # bord de l'assise relevée
    return col, None


def grating(size=256):
    """Caillebotis de passerelle technique, alpha découpé."""
    rgba = np.zeros((size, size, 4)); rgba[..., :3] = (70, 72, 75)
    yy, xx = np.mgrid[0:size, 0:size]
    m = ((xx % 16) < 3) | ((yy % 32) < 3)
    rgba[..., 3] = np.where(m, 255, 0)
    return rgba


# ------------------------------------------------------------------ catalogue
# nom fichier -> (fonction, force normale (0 = pas de normal map))
CATALOG = {
    "concrete_white-repeat.png": (lambda: concrete_white(512), 0),
    "crown_panel.png": (crown_panel, 3.0),
    "alu_white-repeat.png": (alu_white, 0),
    "glass_frit.png": (glass_frit, 0),
    "glass_dark-repeat.png": (glass_dark, 0),
    "curtain_wall-repeat.png": (lambda: curtain_wall(512), 2.0),
    "roof_kalzip-repeat.png": (lambda: roof_kalzip(512, 8), 2.5),
    "concrete_grey-repeat.png": (lambda: concrete_grey(512), 0),
    "seat_black-repeat.png": (seat_black, 0),
    "steel_black-repeat.png": (steel_black, 0),
    "steel_galv-repeat.png": (steel_galv, 0),
    "wall_black-repeat.png": (wall_black, 0),
    "projection_screen.png": (lambda: projection_screen(256), 0),
    "led_off-repeat.png": (led_panel_off, 0),
    "white_matte.png": (white_matte, 0),
    "light_emit.png": (light_emit, 0),
    "skin_light-repeat.png": (skin_light, 0),
    "office_ribbon-repeat.png": (lambda: office_ribbon(512), 1.5),
    "roof_under-repeat.png": (roof_under, 0),
}


def build_all(outdir):
    os.makedirs(outdir, exist_ok=True)
    for f in os.listdir(outdir):           # repartir propre (évite d'exporter d'anciennes cartes _norm)
        if f.endswith(".png"):
            os.remove(os.path.join(outdir, f))
    written = []
    for name, (fn, nstr) in CATALOG.items():
        col, h = fn()
        _save(col, os.path.join(outdir, name))
        written.append(name)
        if nstr and h is not None:
            nn = name.replace("-repeat.png", "_norm-repeat.png") if "-repeat" in name else name.replace(".png", "_norm.png")
            _save(_normal_from_height(np.asarray(h, float), nstr), os.path.join(outdir, nn))
            written.append(nn)
    col, _ = led_ribbon(); _save(col, os.path.join(outdir, "led_ribbon-hrepeat.png")); written.append("led_ribbon-hrepeat.png")
    _save(railing_bars(), os.path.join(outdir, "railing-repeat.png"), "RGBA"); written.append("railing-repeat.png")
    _save(grating(), os.path.join(outdir, "grating-repeat.png"), "RGBA"); written.append("grating-repeat.png")
    # variantes nocturnes des écailles (matériaux non éclairés dans MX)
    _save(night_wash(glass_frit()[0]), os.path.join(outdir, "glass_frit_nuit.png")); written.append("glass_frit_nuit.png")
    _save(night_wash(alu_white()[0]), os.path.join(outdir, "alu_nuit.png")); written.append("alu_nuit.png")
    _save(seat_band()[0], os.path.join(outdir, "seat_band-repeat.png")); written.append("seat_band-repeat.png")
    # atlas sièges : moitié gauche = plastique uni (sièges 3D), moitié droite = 2 silhouettes (LOD)
    sr = seat_row(128)
    atlas = np.zeros((128, 512, 4))
    atlas[:, :256, :3] = (34, 35, 38); atlas[:, :256, 3] = 255
    atlas[:, 256:384] = sr; atlas[:, 384:] = sr
    _save(atlas, os.path.join(outdir, "seat_atlas.png"), "RGBA"); written.append("seat_atlas.png")
    _save(signage(), os.path.join(outdir, "signage.png"), "RGBA"); written.append("signage.png")
    _save(signage_interior(), os.path.join(outdir, "signage_interior.png"), "RGBA"); written.append("signage_interior.png")
    return written


def write_ppm(arr, path):
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    h, w = arr.shape[:2]
    with open(path, "wb") as f:
        f.write(b"P6\n%d %d\n255\n" % (w, h))
        f.write(arr.tobytes())


def build_terrain_tiles(outdir):
    os.makedirs(outdir, exist_ok=True)
    write_ppm(floor_tiles_ppm(), os.path.join(outdir, "floor_tiles.ppm"))
    write_ppm(plaza_ppm(), os.path.join(outdir, "plaza.ppm"))
    return ["floor_tiles.ppm", "plaza.ppm"]
