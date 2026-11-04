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
    if name in ('santamaria', 'tme', 'sudtracto', 'occigardin'): return _from_light_bg(LG + name + '.jpg')   # v44 (user)
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

BL = dict(rows=480, logo_h=1.40, logo_s=1.50, logo_w=5.2)   # v39 (user): logo bigger and higher (v38: 0.8 ft, vertical part only)

def _boudin_arc():
    """cross-section of the boudin (stt_props.BOUDIN) from the +z foot over the top to the -z foot: list of (z, y, normal, s)
    with s = arc length from the +z foot."""
    import stt_props as SP
    B = SP.BOUDIN; R = B['W'] / 2; ys = B['H'] - R; y_b = -B['sink']; sg = B['seg']
    sec = [(R, y_b, (0, 0, 1)), (R, ys, (0, 0, 1))]
    for t in np.linspace(0, np.pi, sg + 1)[1:-1]: sec.append((R * np.cos(t), ys + R * np.sin(t), (0, np.sin(t), np.cos(t))))
    sec += [(-R, ys, (0, 0, -1)), (-R, y_b, (0, 0, -1))]
    out, acc = [], 0.0
    for k, (z, y, n) in enumerate(sec):
        if k: acc += np.hypot(z - sec[k - 1][0], y - sec[k - 1][1])
        out.append((z, y, n, acc))
    return out

def boudin_logo_texture(name):
    """1024 x 1024: rows 0..479 = +z half (row 479 = foot, row 0 = top of the round), rows 480..959 = -z half (same), rows
    960.. plain (ends). u = along the boudin, read left -> right from outside on both halves. Logo centred `logo_s` ft of arc
    above the foot (over the shoulder), `logo_h` ft high."""
    import stt_props as SP
    B = SP.BOUDIN; sec = _boudin_arc(); half = sec[-1][3] / 2; RW = BL['rows']
    img = np.zeros((1024, 1024, 3)); img[:] = SP._vinyl(1024, 1024, 60, 30, 44, amp=4)
    pxu, pxv = 1024 / B['L'], RW / half
    lg = logo(name, dark=True)
    for r0 in (0, RW):
        cy = r0 + RW - BL['logo_s'] * pxv
        paste(img, fit(lg, 512, cy, BL['logo_w'] * pxu, BL['logo_h'] * pxv), lg)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

def boudin_logo():
    """same shape as stt_props.boudin_plain (segments touching), sides mapped by arc length so the logo can go over the
    shoulder without being deformed (developable surface)."""
    import stt_props as SP
    B = SP.BOUDIN; m = Mesh(1024, 1024); sec = _boudin_arc(); half = sec[-1][3] / 2; RW = BL['rows']
    hx = B['L'] / 2; pxu, pxv = 1024 / B['L'], RW / half; xs = np.linspace(-hx, hx, 9)
    def uv(x, s_):
        if s_ <= half + 1e-9: return m.uv_px((x + hx) * pxu, RW - s_ * pxv)                   # +z half: right = +x
        return m.uv_px((hx - x) * pxu, RW + RW - (sec[-1][3] - s_) * pxv)                   # -z half: right = -x
    for k in range(len(sec) - 1):
        (za, ya, na, sa), (zb, yb, nb, sb) = sec[k], sec[k + 1]
        if sa < half < sb:                                                                   # never: the top point is a vertex
            raise ValueError('top not a vertex')
        for i in range(len(xs) - 1):
            xa, xb = xs[i], xs[i + 1]
            if sb <= half + 1e-9: U = [uv(xa, sa), uv(xb, sa), uv(xb, sb), uv(xa, sb)]
            else:                                                                            # -z half: measure from its foot
                U = [uv(xa, sa + 1e-6), uv(xb, sa + 1e-6), uv(xb, sb), uv(xa, sb)]
            SP._smooth(m, [(xa, ya, za), (xb, ya, za), (xb, yb, zb), (xa, yb, zb)], [na, na, nb, nb], U)
    cu = m.uv_px(512, 990)
    for sx in (1, -1):
        m.tri_fan([np.array((sx * hx, y, z)) for z, y, _, _ in sec], np.array([sx * 1.0, 0, 0]), [cu] * len(sec))
    return m

# ------------------------------------------------------------------ advertising tarps on the fence
TARP = dict(w=7.2, y0=0.85, y1=3.25, z=0.43, every=4, gap=0,   # v44 (user): on almost every section: 3 out of 4 (v39: 1 in 6)
           order=('usland', 'santamaria', 'mcst', 'tme', 'rbt', 'sudtracto', 'motopark', 'occigardin', 'sxtour'))   # v44: + 4 sponsors
TARP_BG = dict(usland=(246, 246, 246), mcst=(14, 14, 16), rbt=(246, 246, 246), motopark=(14, 14, 16), sxtour=(246, 246, 246),
               santamaria=(246, 246, 246), tme=(246, 246, 246), sudtracto=(246, 246, 246), occigardin=(246, 246, 246))

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
    paste(img, fit(lg, W / 2, Hf / 2, W * 0.80, Hf * (0.80 if lg.width < 2 * lg.height else 0.62)), lg)   # v44: squarish logos taller
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
BANNER = dict(h=2.9, top=3.6, blocks=('suttel', 'mcst', 'START', 'mcst', 'motopark'), aspect=10.86, z=0.9, leg_r=0.09,
              n_legs=5, px=2048)
# v39 (user): the pattern only ONCE ('comme le zoom sur un tiers'), as big as possible: top at the fence top (3.6 ft), 2.9 ft
# high, the zoom's proportions (10.86 : 1) -> 31.5 ft long, centred behind the gates; a steel frame under it (legs, rail,
# braces, foot plates). Placed just in front of the fence on top of the start wall, facing the gates.

def start_banner_texture(length_ft=None, height_ft=None, px_ft=130):
    """black banner, white italic START in the middle, sponsor logos either side (the user's photo / the zoom he approved)."""
    height_ft = height_ft or BANNER['h']; length_ft = length_ft or height_ft * BANNER['aspect']
    W, H = int(length_ft * px_ft), int(height_ft * px_ft)
    from scipy.ndimage import gaussian_filter
    n = gaussian_filter(np.random.default_rng(7).normal(0, 1, (H, W)), (12, 40)); n /= n.std() + 1e-9
    img = np.zeros((H, W, 3)) + 13.0 + n[..., None] * 2.5
    blocks = list(BANNER['blocks']); bw = W / len(blocks)
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
    pp = max(4, int(H * 0.02)); img[:pp] = 200; img[-pp:] = 200            # white piping top and bottom (as the photo)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

def start_banner():
    """mesh + texture. Texture 2048 x 1024: banner in 2 strips (left half rows 0..376, right half rows 384..760), black back
    / edges at (1000, 900), steel at (1000, 980). Origin: centre, on the ground; front = +z."""
    Bn = BANNER; ban = start_banner_texture(); L = Bn['h'] * Bn['aspect']; Wt = Bn['px']
    hh = int(round(ban.height * (Wt / (ban.width / 2)))); assert hh <= 380, hh
    tex = Image.new('RGB', (Wt, 1024), (16, 16, 18))
    tex.paste(ban.crop((0, 0, ban.width // 2, ban.height)).resize((Wt, hh), Image.LANCZOS), (0, 0))
    tex.paste(ban.crop((ban.width // 2, 0, ban.width, ban.height)).resize((Wt, hh), Image.LANCZOS), (0, 384))
    d = ImageDraw.Draw(tex); d.rectangle((1500, 940, 2047, 1023), fill=(150, 154, 160)); d.rectangle((1500, 860, 2047, 939), fill=(14, 14, 16))
    m = Mesh(Wt, 1024); y0, y1 = Bn['top'] - Bn['h'], Bn['top']; z = Bn['z']; t = 0.06; hx = L / 2
    blk, stl = m.uv_px(1700, 900), ('steel', (1700, 985))
    for k, (xa, xb) in enumerate(((-hx, 0.0), (0.0, hx))):                    # front, seen from +z: right = +x
        r0 = 384 * k
        m.tri_fan([np.array(p) for p in [(xa, y0, z + t), (xb, y0, z + t), (xb, y1, z + t), (xa, y1, z + t)]], np.array([0, 0, 1.0]),
                  [m.uv_px(0, r0 + hh), m.uv_px(Wt, r0 + hh), m.uv_px(Wt, r0), m.uv_px(0, r0)])
    m.tri_fan([np.array(p) for p in [(hx, y0, z - t), (-hx, y0, z - t), (-hx, y1, z - t), (hx, y1, z - t)]], np.array([0, 0, -1.0]), [blk] * 4)
    for P_, N_ in (([(-hx, y1, z - t), (hx, y1, z - t), (hx, y1, z + t), (-hx, y1, z + t)], (0, 1, 0)),
                   ([(-hx, y0, z + t), (hx, y0, z + t), (hx, y0, z - t), (-hx, y0, z - t)], (0, -1, 0)),
                   ([(hx, y0, z - t), (hx, y1, z - t), (hx, y1, z + t), (hx, y0, z + t)], (1, 0, 0)),
                   ([(-hx, y0, z + t), (-hx, y1, z + t), (-hx, y1, z - t), (-hx, y0, z - t)], (-1, 0, 0))):
        m.tri_fan([np.array(p, float) for p in P_], np.array(N_, float), [blk] * 4)
    # steel frame behind / under the banner: legs from the ground to the top, a rail under the banner, X braces, feet
    from props_usland import pipe
    r = Bn['leg_r']; zl = z - t - r - 0.02; xs = np.linspace(-hx + 0.4, hx - 0.4, Bn['n_legs'])
    for x in xs:
        pipe(m, [(x, -0.3, zl), (x, y1 - 0.1, zl)], r, stl, seg=10)
        pipe(m, [(x, 0.0, zl - 1.4), (x, y0 + 0.4, zl)], r * 0.8, stl, seg=8)              # back strut (keeps it up)
        m.tri_fan([np.array(p) for p in [(x - 0.35, 0.02, zl - 1.6), (x + 0.35, 0.02, zl - 1.6), (x + 0.35, 0.02, zl + 0.35), (x - 0.35, 0.02, zl + 0.35)]],
                  np.array([0, 1.0, 0]), [m.uv_px(1700, 985)] * 4)                       # foot plate
    pipe(m, [(-hx + 0.2, y0 - 0.12, zl + 0.05), (hx - 0.2, y0 - 0.12, zl + 0.05)], r, stl, seg=10)   # rail under the banner
    pipe(m, [(-hx + 0.2, 0.35, zl), (hx - 0.2, 0.35, zl)], r * 0.8, stl, seg=8)                   # low rail
    for a, b in zip(xs[:-1], xs[1:]):                                                           # X braces
        pipe(m, [(a, 0.35, zl), (b, y0 - 0.12, zl)], r * 0.6, stl, seg=6)
        pipe(m, [(a, y0 - 0.12, zl), (b, 0.35, zl)], r * 0.6, stl, seg=6)
    return m, tex

BOARD = dict(w=60.0, y0=0.8, top=12.6, z=1.1, px=68, n_legs=7)
# v40 (user's black rectangle on the in-game shot): a BIG start board standing on the start platform at the foot of the wall,
# its top level with the fence top (wall 19 ft + fence 3.6 ft, platform 10 ft -> 12.6 ft), 60 ft wide (the user's box), steel
# frame behind it. Same logos and order as the approved zoom, laid out for a tall board: Suttel over Moto Club on the left,
# a huge START in the middle, Moto Club over Moto Park on the right.

def start_board_texture():
    B = BOARD; px = B['px']; W, H = int(B['w'] * px), int((B['top'] - B['y0']) * px)
    from scipy.ndimage import gaussian_filter
    n = gaussian_filter(np.random.default_rng(8).normal(0, 1, (H, W)), (14, 50)); n /= n.std() + 1e-9
    img = np.zeros((H, W, 3)) + 13.0 + n[..., None] * 2.5
    side = W * 0.315; cxl, cxr = side / 2, W - side / 2
    for cx, (a, b) in ((cxl, ('suttel', 'mcst')), (cxr, ('mcst', 'motopark'))):
        for cy, nm in ((H * 0.28, a), (H * 0.72, b)):
            lg = logo(nm, dark=True); paste(img, fit(lg, cx, cy, side * 0.80, H * (0.36 if nm != 'mcst' else 0.34)), lg)
    fs = int(H * 0.66); font = ImageFont.truetype('C:/Windows/Fonts/impact.ttf', fs)
    while ImageDraw.Draw(Image.new('L', (1, 1))).textlength('START', font=font) > (W - 2 * side) * 0.92: fs -= 8; font = ImageFont.truetype('C:/Windows/Fonts/impact.ttf', fs)
    t = Image.new('L', (int(W - 2 * side), H), 0); d = ImageDraw.Draw(t); tw = d.textlength('START', font=font)
    bb = d.textbbox((0, 0), 'START', font=font); th = bb[3] - bb[1]
    d.text(((t.width - tw) / 2, (H - th) / 2 - bb[1]), 'START', fill=255, font=font)
    t = t.transform(t.size, Image.AFFINE, (1, 0.20, -0.10 * H, 0, 1, 0), Image.BICUBIC)        # italic
    al = np.asarray(t).astype(float)[..., None] / 255.0; x0 = int(side)
    img[:, x0:x0 + t.width] = img[:, x0:x0 + t.width] * (1 - al) + 244 * al
    pp = max(6, int(H * 0.015)); img[:pp] = 205; img[-pp:] = 205; img[:, :pp] = 205; img[:, -pp:] = 205   # white piping (photo)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

def start_board():
    """mesh + 2048 x 2048 texture: left half rows 0.., right half rows 1024.., black at (1700, 1990), steel at (1900, 1990).
    Origin: centre, on the platform; front = +z (towards the gates)."""
    from props_usland import pipe
    B = BOARD; ban = start_board_texture(); hx = B['w'] / 2; y0, y1 = B['y0'], B['top']; z = B['z']; t = 0.08; T = 2048
    hh = int(round(ban.height * T / (ban.width / 2))); assert hh <= 1000, hh
    tex = Image.new('RGB', (T, T), (16, 16, 18))
    tex.paste(ban.crop((0, 0, ban.width // 2, ban.height)).resize((T, hh), Image.LANCZOS), (0, 0))
    tex.paste(ban.crop((ban.width // 2, 0, ban.width, ban.height)).resize((T, hh), Image.LANCZOS), (0, 1024))
    d = ImageDraw.Draw(tex); d.rectangle((1600, 2000, 1799, 2047), fill=(14, 14, 16)); d.rectangle((1800, 2000, 2047, 2047), fill=(150, 154, 160))
    m = Mesh(T, T); blk = m.uv_px(1700, 2024); stl = ('steel', (1920, 2024))
    for k, (xa, xb) in enumerate(((-hx, 0.0), (0.0, hx))):                    # front, seen from +z: right = +x
        r0 = 1024 * k
        m.tri_fan([np.array(p) for p in [(xa, y0, z + t), (xb, y0, z + t), (xb, y1, z + t), (xa, y1, z + t)]], np.array([0, 0, 1.0]),
                  [m.uv_px(0, r0 + hh), m.uv_px(T, r0 + hh), m.uv_px(T, r0), m.uv_px(0, r0)])
    for P_, N_ in (([(hx, y0, z - t), (-hx, y0, z - t), (-hx, y1, z - t), (hx, y1, z - t)], (0, 0, -1)),
                   ([(-hx, y1, z - t), (hx, y1, z - t), (hx, y1, z + t), (-hx, y1, z + t)], (0, 1, 0)),
                   ([(-hx, y0, z + t), (hx, y0, z + t), (hx, y0, z - t), (-hx, y0, z - t)], (0, -1, 0)),
                   ([(hx, y0, z - t), (hx, y1, z - t), (hx, y1, z + t), (hx, y0, z + t)], (1, 0, 0)),
                   ([(-hx, y0, z + t), (-hx, y1, z + t), (-hx, y1, z - t), (-hx, y0, z - t)], (-1, 0, 0))):
        m.tri_fan([np.array(p, float) for p in P_], np.array(N_, float), [blk] * 4)
    r = 0.13; zl = z - t - r - 0.02; xs = np.linspace(-hx + 0.6, hx - 0.6, B['n_legs'])
    for x in xs:                                                                  # steel frame: legs, back struts, feet
        pipe(m, [(x, -0.3, zl), (x, y1 - 0.2, zl)], r, stl, seg=10)
        pipe(m, [(x, 0.0, zl - 3.0), (x, y1 * 0.6, zl)], r * 0.8, stl, seg=8)
        m.tri_fan([np.array(p) for p in [(x - 0.4, 0.02, zl - 3.2), (x + 0.4, 0.02, zl - 3.2), (x + 0.4, 0.02, zl + 0.4), (x - 0.4, 0.02, zl + 0.4)]],
                  np.array([0, 1.0, 0]), [m.uv_px(1920, 2024)] * 4)
    for yy in (0.4, y0 - 0.15, (y0 + y1) / 2, y1 - 0.4):                       # rails
        pipe(m, [(-hx + 0.3, yy, zl), (hx - 0.3, yy, zl)], r * 0.75, stl, seg=8)
    for a, b in zip(xs[:-1], xs[1:]):                                             # X braces (lower half)
        pipe(m, [(a, 0.4, zl), (b, (y0 + y1) / 2, zl)], r * 0.55, stl, seg=6); pipe(m, [(a, (y0 + y1) / 2, zl), (b, 0.4, zl)], r * 0.55, stl, seg=6)
    return m, tex

CAGE = dict(w=5.0, h=3.4, rails=(0.45, 1.8, 3.3), r=0.07, bars=1.0)
# v40 (user): the flagger on his platform at the finish take-off, inside a small steel cage, open at the top.

def flag_cage():
    from props_usland import pipe
    C = CAGE; m = Mesh(256, 256); hw = C['w'] / 2; stl = ('steel', (128, 128)); r = C['r']
    tex = Image.new('RGB', (256, 256), (152, 156, 162))
    corners = [(-hw, -hw), (hw, -hw), (hw, hw), (-hw, hw)]
    for x, z in corners: pipe(m, [(x, -0.2, z), (x, C['h'], z)], r * 1.4, stl, seg=8)
    for yy in C['rails']: pipe(m, [(x, yy, z) for x, z in corners], r, stl, closed=True, seg=8)
    for k in range(4):                                                            # vertical bars between the lower rails
        (xa, za), (xb, zb) = corners[k], corners[(k + 1) % 4]; n = int(round(C['w'] / C['bars']))
        for i in range(1, n): f = i / n; pipe(m, [(xa + (xb - xa) * f, C['rails'][0], za + (zb - za) * f), (xa + (xb - xa) * f, C['rails'][1], za + (zb - za) * f)], r * 0.7, stl, seg=6)
    return m, tex

SIGN = dict(w=84.0, h=7.5, top=12.6, z=1.1, px=68, posts=8, post_r=0.22, strips=3)   # v44 (user): wider (60 -> 84 ft), SX Tour at both ends
# v41 (user's drawing): a big black SIGN on steel posts (6), START in the middle and the sponsors on ONE row (v40: two rows,
# and a braced frame behind that showed as a weird lattice from far away). Top level with the fence top.

def start_sign_texture():
    S_ = SIGN; px = S_['px']; W, H = int(S_['w'] * px), int(S_['h'] * px)
    from scipy.ndimage import gaussian_filter
    n = gaussian_filter(np.random.default_rng(9).normal(0, 1, (H, W)), (12, 50)); n /= n.std() + 1e-9
    img = np.zeros((H, W, 3)) + 13.0 + n[..., None] * 2.5
    blocks = [('sxtour', 1.3), ('suttel', 1.0), ('mcst', 1.0), ('START', 1.55), ('mcst', 1.0), ('motopark', 1.0), ('sxtour', 1.3)]
    tot = sum(w for _, w in blocks); x = 0.0
    for b, wgt in blocks:
        bw = W * wgt / tot; cx = x + bw / 2; x += bw
        if b == 'START':
            fs = int(H * 0.74); font = ImageFont.truetype('C:/Windows/Fonts/impact.ttf', fs)
            while ImageDraw.Draw(Image.new('L', (1, 1))).textlength('START', font=font) > bw * 0.90: fs -= 6; font = ImageFont.truetype('C:/Windows/Fonts/impact.ttf', fs)
            t = Image.new('L', (int(bw), H), 0); d = ImageDraw.Draw(t); tw = d.textlength('START', font=font)
            bb = d.textbbox((0, 0), 'START', font=font); d.text(((t.width - tw) / 2, (H - (bb[3] - bb[1])) / 2 - bb[1]), 'START', fill=255, font=font)
            t = t.transform(t.size, Image.AFFINE, (1, 0.20, -0.10 * H, 0, 1, 0), Image.BICUBIC)
            al = np.asarray(t).astype(float)[..., None] / 255.0; x0 = int(cx - t.width / 2)
            img[:, x0:x0 + t.width] = img[:, x0:x0 + t.width] * (1 - al) + 244 * al
        else:
            lg = logo(b, dark=True); paste(img, fit(lg, cx, H / 2, bw * (0.86 if b == 'sxtour' else 0.82), H * (0.62 if b != 'mcst' else 0.58)), lg)
    pp = max(6, int(H * 0.02)); img[:pp] = 205; img[-pp:] = 205; img[:, :pp] = 205; img[:, -pp:] = 205
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

def start_sign():
    """mesh + 2048 x 2048 texture (left half rows 0.., right half rows 1024..). Origin: centre, on the ground; front = +z."""
    from props_usland import pipe
    S_ = SIGN; ban = start_sign_texture(); hx = S_['w'] / 2; y1 = S_['top']; y0 = y1 - S_['h']; z = S_['z']; t = 0.22; T = 2048   # v42: a thicker board, the posts (r 0.2) fit under it
    NS = S_.get('strips', 2); pitch = 1990 // NS
    hh = int(round(ban.height * T / (ban.width / NS))); assert hh <= pitch, hh
    tex = Image.new('RGB', (T, T), (16, 16, 18))
    for k in range(NS):                                                         # v44: the sign in NS strips stacked in the texture
        tex.paste(ban.crop((ban.width * k // NS, 0, ban.width * (k + 1) // NS, ban.height)).resize((T, hh), Image.LANCZOS), (0, pitch * k))
    d = ImageDraw.Draw(tex); d.rectangle((1600, 2000, 1799, 2047), fill=(14, 14, 16)); d.rectangle((1800, 2000, 2047, 2047), fill=(150, 154, 160))
    m = Mesh(T, T); blk = m.uv_px(1700, 2024); stl = ('steel', (1920, 2024))
    for k in range(NS):
        xa, xb = -hx + 2 * hx * k / NS, -hx + 2 * hx * (k + 1) / NS
        r0 = pitch * k
        m.tri_fan([np.array(p) for p in [(xa, y0, z + t), (xb, y0, z + t), (xb, y1, z + t), (xa, y1, z + t)]], np.array([0, 0, 1.0]),
                  [m.uv_px(0, r0 + hh), m.uv_px(T, r0 + hh), m.uv_px(T, r0), m.uv_px(0, r0)])
    for P_, N_ in (([(hx, y0, z - t), (-hx, y0, z - t), (-hx, y1, z - t), (hx, y1, z - t)], (0, 0, -1)),
                   ([(-hx, y1, z - t), (hx, y1, z - t), (hx, y1, z + t), (-hx, y1, z + t)], (0, 1, 0)),
                   ([(-hx, y0, z + t), (hx, y0, z + t), (hx, y0, z - t), (-hx, y0, z - t)], (0, -1, 0)),
                   ([(hx, y0, z - t), (hx, y1, z - t), (hx, y1, z + t), (hx, y0, z + t)], (1, 0, 0)),
                   ([(-hx, y0, z + t), (-hx, y1, z + t), (-hx, y1, z - t), (-hx, y0, z - t)], (-1, 0, 0))):
        m.tri_fan([np.array(p, float) for p in P_], np.array(N_, float), [blk] * 4)
    r = S_['post_r']; zl = z                                                    # v42 (user): posts stop at the sign's bottom edge,
    for x in np.linspace(-hx + 2.0, hx - 2.0, S_['posts']):                    # centred under it (v41: up behind it, they showed through)
        pipe(m, [(x, -0.4, zl), (x, y0, zl)], min(r, t * 0.95), stl, seg=12)
        m.tri_fan([np.array(p) for p in [(x - 0.45, 0.03, zl - 0.45), (x + 0.45, 0.03, zl - 0.45), (x + 0.45, 0.03, zl + 0.45), (x - 0.45, 0.03, zl + 0.45)]],
                  np.array([0, 1.0, 0]), [m.uv_px(1920, 2024)] * 4)                # base plate
    return m, tex

def stake_sprite():
    """v41: the yellow paddle stake as a BILLBOARD (always upright, whatever the slope: a statue is tilted by the game with
    the ground under it). 256 x 256 RGBA = 1.8 x 1.8 ft (billboard size 1.8), bottom row = ground: stick 0..0.3 ft, paddle
    0.3..1.6 ft, 0.42 ft wide, round top."""
    px = 256 / 1.8; im = Image.new('RGBA', (256, 256), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    yb = lambda f: 256 - f * px; cx = 128; w = 0.42 * px / 2
    d.rectangle((cx - 6, yb(0.36), cx + 6, 256), fill=(150, 128, 18, 255))
    d.rounded_rectangle((cx - w, yb(1.6), cx + w, yb(0.3)), radius=int(w), fill=(232, 200, 24, 255), outline=(150, 126, 16, 255), width=3)
    a = np.asarray(im).astype(float); xs = np.arange(256)[None, :]
    sh = 1.0 + 0.10 * np.cos((xs - cx + w * 0.4) / w * np.pi / 2).clip(-1, 1)    # rounded look
    a[..., :3] *= np.where(a[..., 3:4] > 0, sh[..., None], 1.0)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')

def build(outd=OUTD):
    os.makedirs(outd, exist_ok=True); out = {}
    for n in BOUDIN_LOGOS: boudin_logo_texture(n).save(f'{outd}/boudin_{n}.png'); out[f'boudin_{n}'] = 'png'
    m = tarp(); nv, nt = m.write(f'{outd}/ad_tarp.jm', (0, 0, 0, 0, 0)); out['ad_tarp'] = (nv, nt)
    for n in TARP['order']: tarp_texture(n).save(f'{outd}/ad_{n}.png')
    m = boudin_logo(); out['boudin_logo'] = m.write(f'{outd}/boudin_logo.jm', (24, 0.5, 0.4, 0.4, 0.4))   # v39
    import stt_props as SP; open(f'{outd}/boudin_logo.shp', 'w', newline='\n').write(SP.boudin_shape())
    m, tex = start_sign(); out['start_sign'] = m.write(f'{outd}/start_sign.jm', (0, 0, 0, 0, 0)); tex.save(f'{outd}/start_sign.png')   # v41
    stake_sprite().save(f'{outd}/stake_sprite.png')
    m, tex = flag_cage(); out['flag_cage'] = m.write(f'{outd}/flag_cage.jm', (16, 0.6, 0.6, 0.6, 0.6)); tex.save(f'{outd}/flag_cage.png')
    return out

if __name__ == '__main__':
    for k, v in build().items(): print(k, v)
    if len(sys.argv) > 1: start_banner_texture().save(sys.argv[1]); print('banner', sys.argv[1])
