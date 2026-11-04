"""Saint-Thibery v38 (user, v17 feedback): sponsor logos.
- boudins along the whoops: SX Tour (long) and Moto Club Saint Thibery logos, alternating (same plain boudin mesh, one
  texture per logo);
- advertising tarps hung on the wooden fence (track side), one every `every` fence sections, cycling USLAND, Moto Club
  Saint Thibery, RBT, Moto Park, SX Tour;
- START banner behind the start gates (black panel on a steel frame, as the user's photo): texture design only for now, the
  user wants to see it before it goes in game.
Logos: assets/logos (the user's files). Logos are never mirrored: each face maps u left -> right as read from outside."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
from props_usland import Mesh, OUTD
LG = ROOT + '/assets/logos/'

# ------------------------------------------------------------------ logos (RGBA, cropped to their content)
def _crop(im, thr=40):
    a = np.asarray(im)[..., 3]; ys, xs = np.where(a > thr)
    return im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))

def _from_light_bg(path):
    """logo on a white background (jpg): alpha from the distance to white, colour un-premultiplied."""
    a = np.asarray(Image.open(path).convert('RGB')).astype(float)
    al = np.clip((235 - a.min(2)) / 90.0, 0, 1)
    col = np.where(al[..., None] > 0.02, 255 - (255 - a) / np.maximum(al[..., None], 1e-3), 255)
    return _crop(Image.fromarray(np.dstack([np.clip(col, 0, 255), al * 255]).astype(np.uint8), 'RGBA'))

def _from_dark_bg(path):
    """logo on a black background (jpg): alpha from the brightness, colour un-premultiplied."""
    a = np.asarray(Image.open(path).convert('RGB')).astype(float)
    al = np.clip((a.max(2) - 30) / 160.0, 0, 1)
    col = np.where(al[..., None] > 0.02, a / np.maximum(al[..., None], 1e-3), 0)
    return _crop(Image.fromarray(np.dstack([np.clip(col, 0, 255), al * 255]).astype(np.uint8), 'RGBA'))

def _navy_to_white(im):
    """Moto Club logo on a dark surface: the navy parts (mountain, SAINT THIBERY) turned white, the yellow kept."""
    a = np.asarray(im.convert('RGBA')).astype(float); rgb = a[..., :3]
    navy = (rgb.max(2) < 120) & (rgb[..., 2] >= rgb[..., 0])
    rgb[navy] = 240.0
    return Image.fromarray(np.dstack([rgb, a[..., 3]]).astype(np.uint8), 'RGBA')

def logo(name, dark=False):
    """name in usland, mcst, rbt, motopark, sxtour, suttel. dark = drawn on a black surface."""
    if name == 'usland': return _from_dark_bg(LG + 'usland_white.jpg') if dark else _from_light_bg(LG + 'usland_navy.jpg')
    if name == 'mcst':
        im = _crop(Image.open(LG + 'mc_saint_thibery.webp').convert('RGBA'))
        return _navy_to_white(im) if dark else im
    if name == 'rbt': return _crop(Image.open(LG + 'rbt_wide.png').convert('RGBA'))
    if name == 'motopark': return _from_dark_bg(LG + 'motopark.jpg')
    if name == 'sxtour': return _crop(Image.open(LG + 'sxtour_long.png').convert('RGBA'))
    if name == 'suttel': return _from_dark_bg(LG + 'suttel.jpg')
    raise KeyError(name)

def paste(img, box, lg):
    """paste an RGBA logo (its own colours) into box (x0, y0, x1, y1) of a float (h, w, 3) image."""
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    a = np.asarray(lg.resize((x1 - x0, y1 - y0), Image.LANCZOS)).astype(float)
    al = a[..., 3:4] / 255.0
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - al) + a[..., :3] * al

def fit(lg, cx, cy, max_w, max_h):
    """box centred on (cx, cy), logo aspect kept, inside max_w x max_h (pixels)."""
    ar = lg.width / lg.height; w, h = max_w, max_w / ar
    if h > max_h: h, w = max_h, max_h * ar
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)

# ------------------------------------------------------------------ boudins with logos (whoops)
BOUDIN_LOGOS = ('sxtour', 'mcst')            # alternated along the row

def boudin_logo_texture(name):
    """the plain boudin texture with a logo on both vertical sides (rows 0..255 = +z side, 256..511 = -z side, both read
    left -> right from outside: see stt_props.boudin), as big as the vertical part allows."""
    import stt_props as SP
    B = SP.BOUDIN; img = np.asarray(SP.boudin_texture(False)).astype(float).copy()
    ys = B['H'] - B['W'] / 2; pxu, pxv = 1024 / B['L'], 255 / (ys + B['sink'])
    lg = logo(name, dark=True); lh = 0.80; cyf = B['sink'] + 0.62          # logo 0.8 ft high, centre 0.52 ft above the ground
    for r0 in (0, 256):
        cy = r0 + 255 - cyf * pxv
        paste(img, fit(lg, 512, cy, (B['L'] - 1.2) * pxu, lh * pxv), lg)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

# ------------------------------------------------------------------ advertising tarps on the fence
TARP = dict(w=7.2, y0=0.85, y1=3.25, z=0.43, every=12, order=('usland', 'mcst', 'rbt', 'motopark', 'sxtour'))
TARP_BG = dict(usland=(246, 246, 246), mcst=(14, 14, 16), rbt=(246, 246, 246), motopark=(14, 14, 16), sxtour=(246, 246, 246))

def tarp_texture(name):
    """1024 x 512: rows 0..341 the front (7.2 x 2.4 ft, 142 px / ft), rows 352..511 the back (plain, a bit darker).
    Tarp look: soft folds, darker hem, metal eyelets along the top and bottom edges."""
    from scipy.ndimage import gaussian_filter
    T = TARP; W, Hf = 1024, 341; bg = np.array(TARP_BG[name], float)
    rg = np.random.default_rng(len(name))
    fold = gaussian_filter(rg.normal(0, 1, (Hf, W)), (40, 70)); fold /= fold.std() + 1e-9
    img = np.zeros((512, W, 3)) + bg * 0.8
    face = bg + (fold[..., None] * (6 if bg.mean() > 128 else 4))
    img[:Hf] = face
    lg = logo(name, dark=bg.mean() < 128)
    paste(img, fit(lg, W / 2, Hf / 2, W * 0.80, Hf * 0.62), lg)
    hem = 12; dk = 0.80 if bg.mean() > 128 else 1.9
    img[:hem] *= dk; img[Hf - hem:Hf] *= dk; img[:Hf, :hem] *= dk; img[:Hf, W - hem:] *= dk
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    for x in np.linspace(26, W - 26, 8):
        for y in (22, Hf - 22):
            d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=(150, 152, 156), outline=(80, 80, 84), width=2)
            d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(30, 30, 30))
    return im

def tarp():
    """flat tarp in front of the rails (+z = track side when hung on the fence), front + back face. Origin = fence section
    centre on the ground (same statue position / angle as the fence section)."""
    T = TARP; m = Mesh(1024, 512); hw = T['w'] / 2; z = T['z']
    # front, seen from +z (looking -z): right = +x -> u grows with x
    m.tri_fan([np.array(p) for p in [(-hw, T['y0'], z), (hw, T['y0'], z), (hw, T['y1'], z), (-hw, T['y1'], z)]], np.array([0, 0, 1.0]),
              [m.uv_px(0, 341), m.uv_px(1024, 341), m.uv_px(1024, 0), m.uv_px(0, 0)])
    zb = z - 0.012
    m.tri_fan([np.array(p) for p in [(hw, T['y0'], zb), (-hw, T['y0'], zb), (-hw, T['y1'], zb), (hw, T['y1'], zb)]], np.array([0, 0, -1.0]),
              [m.uv_px(0, 511), m.uv_px(1024, 511), m.uv_px(1024, 352), m.uv_px(0, 352)])
    return m

# ------------------------------------------------------------------ START banner (design only, v38)
def start_banner_texture(length_ft=88.0, height_ft=2.7, px_ft=60):
    """the user's photo: a black banner, white italic START in the middle, sponsor logos on both sides. Pattern repeated
    so it reads along the whole gate line: Suttel | Moto Club | START | Moto Club | Moto Park (x3)."""
    W, H = int(length_ft * px_ft), int(height_ft * px_ft)
    from scipy.ndimage import gaussian_filter
    n = gaussian_filter(np.random.default_rng(7).normal(0, 1, (H, W)), (12, 40)); n /= n.std() + 1e-9
    img = np.zeros((H, W, 3)) + 13.0 + n[..., None] * 2.5
    blocks = ['suttel', 'mcst', 'START', 'mcst', 'motopark'] * 3
    bw = W / len(blocks)
    font = ImageFont.truetype('C:/Windows/Fonts/impact.ttf', int(H * 0.78))
    for i, b in enumerate(blocks):
        cx = (i + 0.5) * bw
        if b == 'START':
            t = Image.new('L', (int(bw * 1.3), H), 0); d = ImageDraw.Draw(t)
            tw = d.textlength('START', font=font); d.text(((t.width - tw) / 2, H * 0.06), 'START', fill=255, font=font)
            t = t.transform(t.size, Image.AFFINE, (1, 0.22, -0.11 * H, 0, 1, 0), Image.BICUBIC)   # italic
            al = np.asarray(t).astype(float)[..., None] / 255.0; x0 = int(cx - t.width / 2)
            img[:, x0:x0 + t.width] = img[:, x0:x0 + t.width] * (1 - al) + 244 * al
        else:
            lg = logo(b, dark=True); paste(img, fit(lg, cx, H / 2, bw * 0.78, H * (0.70 if b != 'mcst' else 0.62)), lg)
    img[:6] = 200; img[-6:] = 200                                    # white piping top and bottom (as the photo)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

def build(outd=OUTD):
    os.makedirs(outd, exist_ok=True); out = {}
    for n in BOUDIN_LOGOS: boudin_logo_texture(n).save(f'{outd}/boudin_{n}.png'); out[f'boudin_{n}'] = 'png'
    m = tarp(); nv, nt = m.write(f'{outd}/ad_tarp.jm', (0, 0, 0, 0, 0)); out['ad_tarp'] = (nv, nt)
    for n in TARP['order']: tarp_texture(n).save(f'{outd}/ad_{n}.png')
    return out

if __name__ == '__main__':
    for k, v in build().items(): print(k, v)
    if len(sys.argv) > 1: start_banner_texture().save(sys.argv[1]); print('banner', sys.argv[1])
