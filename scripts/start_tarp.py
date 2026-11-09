"""SGM start tarp (user's photos 220 / 223): behind the start gates, a black knitted shade net hiding the fence (ground ->
6.5 ft) on a light scaffold of grey tubes, and above it a long printed banner (6.5 -> 10.5 ft): red / orange background with
black brush strokes, a white graffiti "START" on the left, the SX Tour logo in the middle and a round winged "SHOP MOTO"
emblem on the right.
- 90 ft long along local x, centred on the origin, origin on the ground; FRONT (printed side, riders' side) = local -z.
- banner artwork = one 30 ft tile (START | SX TOUR | SHOP MOTO) repeated 3 times; the tile is stored as two 15 ft strips
  (2048 x 546 px each, 136 px / ft) so the print stays sharp. Back of the banner: plain black.
- net: knitted shade net with small hard cut-out holes (alpha 0 / 255, ~22 % holes so it stays solid in the distance),
  one 10 ft texture tile per bay (between two posts), double sided.
- scaffold: 48 mm grey tubes, a post every 10 ft (10 posts), 4 rails behind them with clamps, a raking shore behind every
  post going back to the ground (whole thing ~1.1 ft deep), base plates.
Run: python scripts/start_tarp.py [--preview]  -> assets/props/start_tarp.jm / .png (+ ../apercus_sgm/start_tarp_3d.png)"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.ndimage import gaussian_filter, map_coordinates, binary_dilation
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
from props_usland import Mesh, palette, pipe, OUTD
import stt_ads as AD

T = dict(L=90.0, net_y=(0.0, 6.5), ban_y=(6.5, 10.5), tile=30.0, bay=10.0, post_top=11.0, tube_r=0.08,
         z_ban=-0.06, ban_t=0.03, z_net=-0.045, net_t=0.01, z_post=0.12, rails=(0.35, 3.4, 6.45, 10.45), shore=1.0)
TW = 2048
# v30 (user): ONE 90 ft banner (no repeated tile): a big START in the middle, the user's Supercross SX Cross Freestyle and
# MX Shop Moto logos alternating on both sides. Printed at 80 px / ft, cut in 4 strips of 2048 px (25.6 ft) stacked in the
# texture; the black net tile on the right below them (the palette squares are bottom left)
PPF = 80.0
BH = int(round((T['ban_y'][1] - T['ban_y'][0]) * PPF))   # 320 px
SL = TW / PPF                                   # strip length (ft)
STRIP = tuple((k * (BH + 6), k * (BH + 6) + BH) for k in range(4))
NET = (1024, 4 * (BH + 6) + 6, 2048, 4 * (BH + 6) + 6 + int(round(1024 / T['bay'] * (T['net_y'][1] - T['net_y'][0]))))   # 10 ft x 6.5 ft
RED, ORANGE, INK, WHITE = (196, 28, 22), (238, 78, 26), (14, 13, 14), (246, 246, 244)
IMPACT = 'C:/Windows/Fonts/impact.ttf'
ARIBLK = 'C:/Windows/Fonts/ariblk.ttf'

# ------------------------------------------------------------------ banner artwork (one 30 ft tile, seamless when repeated)
def _font(path, size):
    try: return ImageFont.truetype(path, size)
    except OSError: return ImageFont.load_default(size=size)

def _stroke(d, pts, w, W, fill=255):
    """tapered brush stroke along a polyline (circles of varying radius), drawn 3x (x-W, x, x+W) so the tile wraps."""
    pts = np.asarray(pts, float); seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)])
    n = max(8, int(s[-1] / 2))
    for t in np.linspace(0, 1, n):
        x = np.interp(t * s[-1], s, pts[:, 0]); y = np.interp(t * s[-1], s, pts[:, 1])
        r = w * np.sin(np.pi * min(max(t, 0.02), 0.98)) ** 0.7 * (1 - 0.35 * t)
        for o in (-W, 0, W): d.ellipse([x + o - r, y - r, x + o + r, y + r], fill=fill)

def _curve(rg, x, y, L, ang, bend, n=7):
    a = ang + np.linspace(0, bend, n); step = L / (n - 1)
    return np.cumsum(np.stack([np.r_[x, np.cos(a[1:]) * step], np.r_[y, np.sin(a[1:]) * step]], 1), axis=0)

def _rough(mask, amp, scale, seed, wrap=True):
    """jagged edges: displace a float mask by a smooth noise field (px)."""
    H, W = mask.shape; rg = np.random.default_rng(seed); md = 'wrap' if wrap else 'nearest'
    dx = gaussian_filter(rg.normal(0, 1, (H, W)), scale, mode=md); dy = gaussian_filter(rg.normal(0, 1, (H, W)), scale, mode=md)
    dx *= amp / (dx.std() + 1e-9); dy *= amp / (dy.std() + 1e-9)
    yy, xx = np.mgrid[:H, :W].astype(float)
    return map_coordinates(mask, [yy + dy, xx + dx], order=1, mode='wrap' if wrap else 'nearest')

def background(W, H, seed=3):
    """red-orange print with black graffiti brush strokes and spray splatters (periodic along x)."""
    rg = np.random.default_rng(seed)
    n = gaussian_filter(rg.normal(0, 1, (H, W)), (H * 0.35, H * 0.6), mode='wrap'); n = (n - n.min()) / (np.ptp(n) + 1e-9)
    t = np.linspace(0, 1, H)[:, None]
    k = np.clip(0.35 + 0.65 * n - 0.25 * np.abs(t - 0.45), 0, 1)[..., None]
    img = np.array(RED, float) * (1 - k) + np.array(ORANGE, float) * k
    img *= (1 + 0.05 * gaussian_filter(rg.normal(0, 1, (H, W)), 1.2, mode='wrap'))[..., None]   # printed fabric grain
    m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
    for _ in range(int(W / H * 7)):                                  # long sweeping strokes, mostly diagonal
        x, y = rg.uniform(0, W), rg.uniform(-0.2 * H, 1.2 * H); ang = rg.choice([-1, 1]) * rg.uniform(0.25, 0.9) + (np.pi if rg.random() < 0.5 else 0)
        _stroke(d, _curve(rg, x, y, rg.uniform(0.5, 1.6) * H, ang, rg.uniform(-0.8, 0.8)), rg.uniform(0.02, 0.075) * H, W)
    for _ in range(int(W / H * 14)):                                 # short spiky flicks
        x, y = rg.uniform(0, W), rg.uniform(0, H); ang = rg.uniform(0, 2 * np.pi)
        _stroke(d, _curve(rg, x, y, rg.uniform(0.08, 0.35) * H, ang, rg.uniform(-1.2, 1.2), 5), rg.uniform(0.008, 0.025) * H, W)
    for _ in range(int(W / H * 40)):                                 # spray dots
        x, y, r = rg.uniform(0, W), rg.uniform(0, H), rg.uniform(1, 0.012 * H)
        for o in (-W, 0, W): d.ellipse([x + o - r, y - r, x + o + r, y + r], fill=255)
    a = _rough(np.asarray(m, float) / 255, 2.5, 3, seed + 1)
    a = np.clip((a - 0.5) * 4 + 0.5, 0, 1)[..., None] * 0.92
    img = img * (1 - a) + np.array(INK, float) * a
    b = int(0.10 * PPF); img[:b] = INK; img[-b:] = INK                # black hem top and bottom
    img[b:b + 2] *= 0.7; img[-b - 2:-b] *= 0.7
    return img

def start_word(h):
    """white graffiti START: heavy letters, each tilted / bounced, slanted, jagged edges, drips, black outline + shadow (RGBA)."""
    f = _font(IMPACT, int(h * 1.05)); rg = np.random.default_rng(11)
    W = int(h * 4.8); Hc = int(h * 1.6); m = Image.new('L', (W, Hc), 0); x = int(h * 0.12)
    for i, ch in enumerate('START'):
        l, t, r, b = f.getbbox(ch); g = Image.new('L', (r - l + 40, b - t + 40), 0)
        ImageDraw.Draw(g).text((20 - l, 20 - t), ch, font=f, fill=255)
        g = g.resize((int(g.width * 1.08), g.height), Image.LANCZOS).rotate(rg.uniform(-7, 5), Image.BICUBIC, expand=True)
        yo = int(h * 0.18 + rg.uniform(-0.06, 0.06) * h - (0.05 * h if i == 0 else 0))
        m.paste(255, (x, yo), g); x += int(g.width * 0.86)
    m = m.transform(m.size, Image.AFFINE, (1, 0.28, -0.28 * Hc / 2, 0, 1, 0), Image.BICUBIC)
    a = np.asarray(m, float) / 255
    # brushy cuts: thin diagonal slashes across the letters (graffiti look)
    sl = Image.new('L', m.size, 0); d = ImageDraw.Draw(sl)
    for _ in range(4):
        cx, cy = rg.uniform(0.05, 0.95) * W, rg.uniform(0.25, 0.85) * Hc; L = rg.uniform(0.15, 0.4) * h; an = rg.uniform(-0.5, -0.2)
        d.line([(cx - L * np.cos(an), cy - L * np.sin(an)), (cx + L * np.cos(an), cy + L * np.sin(an))], fill=255, width=max(2, int(h * 0.015)))
    a = a * (1 - np.asarray(sl.filter(ImageFilter.GaussianBlur(1)), float) / 255)
    # drips under some letters
    dm = Image.new('L', m.size, 0); d = ImageDraw.Draw(dm); ys, xs = np.nonzero(a > 0.5); bot = ys.max()
    for _ in range(4):
        xx = rg.uniform(xs.min() + 0.1 * h, xs.max() - 0.1 * h); col = np.nonzero(a[:, int(xx)] > 0.5)[0]
        if not len(col): continue
        y0 = col.max() - 4; L = rg.uniform(0.08, 0.25) * h; w = rg.uniform(0.012, 0.03) * h
        d.rectangle([xx - w, y0, xx + w, y0 + L], fill=255); d.ellipse([xx - w * 1.5, y0 + L - w * 1.5, xx + w * 1.5, y0 + L + w * 1.5], fill=255)
    a = np.maximum(a, np.asarray(dm, float) / 255)
    a = np.clip((_rough(a, 1.6, 1.5, 12, wrap=False) - 0.5) * 3 + 0.5, 0, 1)
    out = binary_dilation(a > 0.5, iterations=max(2, int(h * 0.035)))
    sh = np.roll(np.roll(out, int(h * 0.05), 0), int(h * 0.04), 1)
    rgb = np.zeros(a.shape + (3,)) + np.array(WHITE, float); rgb *= (0.93 + 0.07 * np.linspace(1, 0, a.shape[0]))[:, None, None]
    al = np.maximum(np.maximum(sh * 0.85, out * 1.0), a)
    rgb = rgb * a[..., None] + np.array(INK, float) * (1 - a[..., None])
    im = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), al * 255]).astype(np.uint8), 'RGBA')
    return AD._crop(im)

def emblem(h):
    """round winged SHOP MOTO emblem (drawn here, not a real logo): black disk, white ring, SHOP / MOTO lettering,
    white feathered wings either side (RGBA, h px high)."""
    S = 2; H = h * S; R = H * 0.40; W = int(H * 2.6); img = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    cx, cy = W / 2, H * 0.50; ow = max(2, int(H * 0.018))
    for s in (-1, 1):                                                 # wings: 6 fanned feathers, longest on top
        for k in range(5, -1, -1):
            an = np.radians(28 - k * 13); L = R * (2.05 - 0.22 * k); hw = R * (0.17 - 0.012 * k)
            px_, py_ = cx + s * R * 0.35, cy - R * 0.05 + k * R * 0.05
            dx, dy = s * np.cos(an), -np.sin(an); nx, ny = -dy, dx
            def P(t, w): return (px_ + dx * L * t + nx * w, py_ + dy * L * t + ny * w)
            outer = [P(0, -hw), P(0.55, -hw * 1.05), P(0.88, -hw * 0.7), P(1.0, 0), P(0.80, hw * 0.75), P(0.45, hw), P(0, hw)]
            d.polygon(outer, fill=INK + (255,))
            g = 238 - 12 * k; i_ = [P(0.02, -hw + ow), P(0.55, -hw * 1.05 + ow), P(0.87, -hw * 0.7 + ow * 0.8), P(0.98, 0),
                                   P(0.79, hw * 0.75 - ow * 0.8), P(0.45, hw - ow), P(0.02, hw - ow)]
            d.polygon(i_, fill=(g, g, g + 3, 255))
            d.line([P(0.25, 0), P(0.9, 0)], fill=(160, 160, 166, 255), width=max(1, ow // 2))
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=INK + (255,))
    d.ellipse([cx - R * 0.90, cy - R * 0.90, cx + R * 0.90, cy + R * 0.90], fill=WHITE + (255,))
    d.ellipse([cx - R * 0.80, cy - R * 0.80, cx + R * 0.80, cy + R * 0.80], fill=INK + (255,))
    for a_ in np.linspace(0, 2 * np.pi, 24, endpoint=False):         # small dots in the white ring
        x, y = cx + np.cos(a_) * R * 0.85, cy + np.sin(a_) * R * 0.85; r = R * 0.018
        if abs(np.sin(a_)) > 0.35: d.ellipse([x - r, y - r, x + r, y + r], fill=INK + (255,))
    f1 = _font(ARIBLK, int(R * 0.30)); f2 = _font(IMPACT, int(R * 0.62))
    for txt, f, yc, col in (('SHOP', f1, cy - R * 0.36, WHITE), ('MOTO', f2, cy + R * 0.06, WHITE)):
        tw = d.textlength(txt, font=f); l, t, r, b = f.getbbox(txt); d.text((cx - tw / 2, yc - (t + b) / 2), txt, font=f, fill=col + (255,))
    d.rectangle([cx - R * 0.46, cy + R * 0.44, cx - R * 0.16, cy + R * 0.52], fill=(30, 70, 190, 255))
    d.rectangle([cx - R * 0.15, cy + R * 0.44, cx + R * 0.15, cy + R * 0.52], fill=WHITE + (255,))
    d.rectangle([cx + R * 0.16, cy + R * 0.44, cx + R * 0.46, cy + R * 0.52], fill=(220, 30, 40, 255))
    img = img.resize((W // S, H // S), Image.LANCZOS)
    return AD._crop(img)

def banner_full():
    """v30: the whole 90 ft x 4 ft banner (7200 x 320 px): START big in the middle, logos alternating outwards."""
    from PIL import Image as _I
    W, H = int(round(T['L'] * PPF)), BH; img = background(W, H)
    ft = lambda v: (T['L'] / 2 + v) * PPF                            # banner x (ft from the middle, reading direction) -> px
    st = start_word(int(H * 0.70)); AD.paste(img, AD.fit(st, ft(0.0), H * 0.50, 17.0 * PPF, H * 0.90), st)
    sx = _I.open(f'{ROOT}/assets/logos/supercross_sgm_white.png').convert('RGBA'); sm = _I.open(f'{ROOT}/assets/logos/mxshopmoto.png').convert('RGBA')
    st_ = AD.logo('sxtour')                                          # v31 (user): START, SX Tour either side, then each logo ONCE per side
    for sg in (-1, 1):
        AD.paste(img, AD.fit(st_, ft(sg * 16.5), H * 0.50, 11.0 * PPF, H * 0.62), st_)
        AD.paste(img, AD.fit(sx, ft(sg * 29.0), H * 0.50, 6.2 * PPF, H * 0.90), sx)
        AD.paste(img, AD.fit(sm, ft(sg * 39.5), H * 0.50, 6.4 * PPF, H * 0.90), sm)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

def banner_tile():
    """30 ft x 4 ft tile (4096 x 546 px), seamless along x."""
    W, H = int(round(T['tile'] * PPF)), BH; img = background(W, H)
    ft = lambda v: v * PPF
    st = start_word(int(H * 0.62)); AD.paste(img, AD.fit(st, ft(5.4), H * 0.50, ft(9.6), H * 0.80), st)
    sx = AD.logo('sxtour'); AD.paste(img, AD.fit(sx, ft(15.6), H * 0.50, ft(10.0), H * 0.70), sx)
    em = emblem(int(H * 0.86)); AD.paste(img, AD.fit(em, ft(25.4), H * 0.50, ft(8.6), H * 0.84), em)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

# ------------------------------------------------------------------ shade net tile
def net_tile(w, h, seed=5):
    """black knitted shade net (RGBA): dark threads in a knit pattern, small cut-out holes (~22 %), slight sag folds,
    darker at the bottom (dust) and lighter on the top edge (hem)."""
    rg = np.random.default_rng(seed); yy, xx = np.mgrid[:h, :w].astype(float)
    cw, ch = 9.0, 7.0                                               # knit cell (px): ~0.09 x 0.07 ft
    off = (np.floor(yy / ch) % 2) * cw / 2
    u = ((xx + off) % cw) / cw - 0.5; v = (yy % ch) / ch - 0.5
    hole = (np.abs(u) / 0.15 + np.abs(v) / 0.17) < 1.0             # v30 (user): tiny holes (~5 %), almost opaque; v29 0.36 / 0.40 (~22 %)
    stitch = 0.5 + 0.5 * np.cos(2 * np.pi * (xx + off) / cw * 2) * np.cos(2 * np.pi * yy / ch)
    base = 11 + 5 * stitch + 2.5 * gaussian_filter(rg.normal(0, 1, (h, w)), 1)   # v30 (user): much blacker (v29 24 + 9)
    fold = gaussian_filter(rg.normal(0, 1, (1, w)), (0, 22), mode='wrap'); fold = fold / (np.abs(fold).max() + 1e-9)
    base = base * (1 + 0.18 * fold) * (1 - 0.25 * np.clip((yy / h - 0.82) / 0.18, 0, 1))
    rgb = np.dstack([base, base, base * 1.04])
    rgb[yy[:, 0] < 0.08 * h / 6.5 * 1, :] *= 1.0
    hem = int(round(h * 0.10 / 6.5)) + 1                            # webbing hem along the top and both sides (no holes)
    alpha = np.where(hole, 0, 255); alpha[:hem] = 255; alpha[:, :hem] = 255; alpha[:, -hem:] = 255; alpha[-hem:] = 255
    rgb[:hem] = 18; rgb[:, :hem] = 18; rgb[:, -hem:] = 18
    for gx in np.linspace(0, w - 1, 5)[1:-1].tolist() + [hem * 0.5, w - hem * 0.5]:   # grommets / ties along the top
        r = hem * 0.5; m = (xx - gx) ** 2 + (yy - hem * 0.5) ** 2 < r * r; rgb[m] = 120
    return np.dstack([np.clip(rgb, 0, 255), alpha]).astype(np.uint8)

def texture():
    img = Image.new('RGBA', (TW, TW), (18, 18, 20, 255)); full = banner_full()
    for k, (r0, r1) in enumerate(STRIP):
        s = full.crop((k * TW, 0, min((k + 1) * TW, full.width), BH)); img.paste(s, (0, r0))
        img.paste(s.crop((0, BH - 1, s.width, BH)).resize((s.width, 6)), (0, r1))          # pad between the strips (mip bleed)
    x0, y0, x1, y1 = NET; img.paste(Image.fromarray(net_tile(x1 - x0, y1 - y0), 'RGBA'), (x0, y0))
    rgb = img.convert('RGB')
    pal = palette(rgb, ['tube', 'black', 'clamp', 'plate'], [(150, 153, 157), (18, 18, 20), (118, 120, 124), (96, 96, 98)])
    out = rgb.convert('RGBA'); a = np.asarray(img)[..., 3].copy(); a[-128:] = 255; out.putalpha(Image.fromarray(a))
    return out, pal

# ------------------------------------------------------------------ model
def model(pal):
    m = Mesh(TW, TW); L2 = T['L'] / 2; e = 0.5                            # e: half-pixel inset of the UVs
    yb0, yb1 = T['ban_y']; zf = T['z_ban']; zb = zf + T['ban_t']
    # banner front (-z): seen from -z the viewer's right is -x, so the print runs from x = +45 (left) to x = -45 (right)
    for k in range(len(STRIP)):                                       # v30: 4 strips of SL ft, the last one shorter
        xa = L2 - k * SL; xb = max(-L2, xa - SL); r0, r1 = STRIP[k]; ue = (xa - xb) * PPF
        m.tri_fan([np.array(p) for p in [(xa, yb0, zf), (xb, yb0, zf), (xb, yb1, zf), (xa, yb1, zf)]], np.array([0, 0, -1.0]),
                  [m.uv_px(e, r1 - e), m.uv_px(ue - e, r1 - e), m.uv_px(ue - e, r0 + e), m.uv_px(e, r0 + e)])
    m.box(-L2, L2, yb0, yb1, zf + 0.001, zb, {'+z': pal['black'], '+y': pal['black'], '-y': pal['black'], '+x': pal['black'], '-x': pal['black']})
    # shade net, one texture tile per bay, front and back
    x0, y0, x1, y1 = NET; ny0, ny1 = T['net_y']; zn = T['z_net']; nb = int(round(T['L'] / T['bay']))
    for k in range(nb):
        xa = L2 - k * T['bay']; xb = xa - T['bay']
        for z, n, (ua, ub) in ((zn, -1.0, (x0 + e, x1 - e)), (zn + T['net_t'], 1.0, (x1 - e, x0 + e))):
            m.tri_fan([np.array(p) for p in [(xa, ny0, z), (xb, ny0, z), (xb, ny1, z), (xa, ny1, z)]], np.array([0, 0, n]),
                      [m.uv_px(ua, y1 - e), m.uv_px(ub, y1 - e), m.uv_px(ub, y0 + e), m.uv_px(ua, y0 + e)])
    # scaffold
    r = T['tube_r']; zp = T['z_post']; zr = zp + 2 * r; xs = np.linspace(-L2, L2, nb + 1)
    xs = np.clip(xs, -L2 + 0.25, L2 - 0.25)
    for x in xs:
        pipe(m, [(x, 0.0, zp), (x, T['post_top'], zp)], r, pal['tube'], seg=8)
        m.box(x - 0.1, x + 0.1, T['post_top'], T['post_top'] + 0.08, zp - 0.1, zp + 0.1, {'*': pal['black'], '-y': None})   # end cap
        m.box(x - 0.3, x + 0.3, 0.0, 0.03, zp - 0.3, zp + 0.3, {'*': pal['plate'], '-y': None})                         # base plate
        for y in T['rails']:
            m.box(x - 0.11, x + 0.11, y - 0.11, y + 0.11, zp - 0.05, zr + 0.11, {'*': pal['clamp']})                 # coupler
        zs = zp + T['shore']                                                       # raking shore to the ground, behind
        pipe(m, [(x, 7.0, zp + r), (x, 0.06, zs)], r * 0.9, pal['tube'], seg=6)
        m.box(x - 0.25, x + 0.25, 0.0, 0.03, zs - 0.2, zs + 0.2, {'*': pal['plate'], '-y': None})
    for y in T['rails']:
        pipe(m, [(-L2, y, zr), (L2, y, zr)], r, pal['tube'], seg=8)
    return m

# ------------------------------------------------------------------ preview (software z-buffer, NOT a game render)
def preview(out_path):
    from preview_stt_scene import Cam, raster, load_jm
    from rider_gate import scale_person
    V, I = load_jm(f'{OUTD}/start_tarp.jm'); tex = np.asarray(Image.open(f'{OUTD}/start_tarp.png').convert('RGBA'), np.float32) / 255
    objs = [(V, I, tex), scale_person((3.0, 0, -4.0))]
    Lg = np.array([0.3, 0.8, -0.5]); Lg /= np.linalg.norm(Lg)
    def shot(eye, tgt, W=900, H=560, fov=50, fence=True):
        cam = Cam(eye, tgt, W, H, fov); img = np.zeros((H, W, 3), np.float32)
        sky = np.linspace(0, 1, H)[:, None, None]; img[:] = np.array([0.55, 0.70, 0.90]) * (1 - sky) + np.array([0.82, 0.86, 0.90]) * sky
        zb = np.full((H, W), np.inf, np.float32)
        # a wooden fence behind the net (to check the see-through holes)
        gs = np.arange(-90, 91, 6.0); GX, GZ = np.meshgrid(gs, gs - 30); P = np.stack([GX, np.zeros_like(GX), GZ], -1).reshape(-1, 3)
        n = len(gs); ii, jj = np.meshgrid(np.arange(n - 1), np.arange(n - 1), indexing='ij'); a = (ii * n + jj).ravel()
        Ig = np.concatenate([np.stack([a, a + 1, a + n], 1), np.stack([a + 1, a + n + 1, a + n], 1)])
        rg = np.random.default_rng(0); C = np.array([0.55, 0.43, 0.31]) * (0.92 + 0.12 * rg.random((len(P), 1)))
        raster(img, zb, cam, P, Ig, lambda ti, B: (C[Ig[ti]] * B[:, :, None]).sum(1))
        if fence:                                                    # grey wooden fence 2.5 ft behind (hidden by the net)
            fq = np.array([[-50, 0, 2.5], [50, 0, 2.5], [50, 5.5, 2.5], [-50, 5.5, 2.5]], np.float32)
            raster(img, zb, cam, fq, np.array([[0, 1, 2], [0, 2, 3]]), lambda ti, B: np.ones((len(B), 3)) * np.array([0.72, 0.70, 0.66]))
        for V_, I_, tx in objs:
            th, tw = tx.shape[:2]
            def uvpx(ti, B, V_=V_, I_=I_, tw=tw, th=th):
                uv = (V_[I_[ti], 6:8][None] * B[:, :, None]).sum(1)
                return np.clip((1 - uv[:, 1]) * th, 0, th - 1).astype(int), np.clip(uv[:, 0] * tw, 0, tw - 1).astype(int)
            def col(ti, B, V_=V_, I_=I_, tx=tx):
                py, px = uvpx(ti, B); nn = (V_[I_[ti], 3:6][None] * B[:, :, None]).sum(1)
                return tx[py, px, :3] * (0.70 + 0.35 * np.clip(nn @ Lg, 0, 1))[:, None]
            raster(img, zb, cam, V_[:, :3], I_, col, lambda ti, B, tx=tx: tx[uvpx(ti, B)][:, 3])
        return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    views = [shot((0.0, 5.5, -62.0), (0.0, 5.5, 0.0), fov=78),           # riders' side, whole length
             shot((14.0, 4.0, -16.0), (6.0, 6.5, 0.0), fov=60),           # behind the gate, 3/4 front, person for scale
             shot((-26.0, 9.0, 22.0), (-12.0, 5.0, 0.0), fov=60, fence=False),         # back: scaffold, plain black back
             shot((19.0, 6.5, -6.5), (19.0, 6.5, 0.0), fov=60)]           # close-up on the net / print
    W_, H_ = views[0].size; sheet = Image.new('RGB', (W_ * 2, H_ * 2), (255, 255, 255))
    for k, v in enumerate(views): sheet.paste(v, ((k % 2) * W_, (k // 2) * H_))
    os.makedirs(os.path.dirname(out_path), exist_ok=True); sheet.save(out_path); print('preview', out_path)

def build(outd=OUTD):
    os.makedirs(outd, exist_ok=True)
    img, pal = texture(); m = model(pal)
    nv, nt = m.write(f'{outd}/start_tarp.jm', (0, 0, 0, 0, 0)); img.save(f'{outd}/start_tarp.png', optimize=True)
    P = np.array([v[:3] for v in m.V]); print(f'start_tarp: {nv} vertices, {nt} triangles, bbox {P.min(0).round(2)} .. {P.max(0).round(2)} ft')
    return nv, nt

if __name__ == '__main__':
    build()
    if '--preview' in sys.argv: preview(os.path.join(os.path.dirname(ROOT), 'apercus_sgm', 'start_tarp_3d.png'))
