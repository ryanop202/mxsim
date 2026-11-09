"""50FACTORY.com RIDER GATE (user's 4 photos) + the yellow 50FACTORY inflatable cylinder, made from scratch with props_usland.Mesh
(doc 12: 1 unit = 1 ft, y up, baked shades, one texture per model, rounded pads, real logo never distorted / mirrored).

rider_gate.jm / .png : black box platform (painted wood, steel corners) with a yellow "50FACTORY.com Rider Gate" banner on both
  long sides, two steel ramps (one-piece diamond expanded metal in a steel frame, see-through: alpha) to ride up and down, and
  the yellow padded arch: two vertical pads hanging beside the box (full-width diagonal cut at the bottom, real logo reading
  upwards) and a header pad (chamfered top corners, real logo + RIDER GATE). Pads: soft rounded edges with a black piping,
  black velcro tabs. Origin = ground, centre of the box footprint; riding direction ramp -> box -> ramp along local x; the arch
  stands at the -x end of the box and faces +-x (riders pass through it along x).
f50_cylinder.jm / .png : yellow inflatable cylinder 0.6 m x 1.42 m, rounded top, round black base, logo x3 reading upwards.
Sizes estimated from the photos (bike / rider for scale): see G and CYL (metres converted to ft).
Run: python scripts/rider_gate.py [--preview]  -> assets/props/ (+ ../apercus_sgm/rider_gate_3d.png with --preview)"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.ndimage import distance_transform_edt, gaussian_filter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
from props_usland import Mesh, palette, OUTD

FT = 1 / 0.3048
LOGO = f'{ROOT}/assets/logos/50factory.png'          # the user's real logo (RGBA: black backing, yellow 50, white FACTORY)
FONT = 'C:/Windows/Fonts/ERASBD.TTF'                   # RIDER GATE: heavy geometric font, slanted and widened like the photos
G = dict(L=2.20 * FT, W=1.25 * FT, H=0.92 * FT, top_t=0.035 * FT, lip=0.02 * FT, edge_r=0.025 * FT,     # box
         ramp_w=0.75 * FT, ramp_len=2.10 * FT, rail=0.022 * FT, hook=0.07 * FT,                        # ramps (each end)
         post_w=0.65 * FT, tip=0.22 * FT, cham=0.70 * FT, open_h=2.08 * FT, head_h=0.78 * FT,         # arch pads
         head_cham=0.12 * FT, pad_t=0.13 * FT, gap=0.012 * FT, arch_dx=0.10 * FT)                    # arch_dx: from the -x end
CYL = dict(R=0.30 * FT, H=1.42 * FT, top=0.20 * FT, base_r=0.335 * FT, base_h=0.135 * FT, seg=24)
YEL, BLK, BOX, STEEL = (246, 222, 38), (20, 20, 22), (36, 36, 38), (56, 54, 52)
TW = 2048
PHI = (90, 55, 22, 8, -8, -22, -55, -90)               # pad edge profile (deg): front face -> back face, piping between +-8

# ------------------------------------------------------------------ 2D artwork helpers
_LG = None
TABS = False
LOGO_RIM = None   # v27b (user): logos as before, full black backing; v27 tried 8.0          # v27: px of black round the letters on the 1062 x 148 logo (was up to ~17)
def logo_img():
    global _LG
    if _LG is None:
        im = Image.open(LOGO).convert('RGBA'); A = np.asarray(im).astype(float)
        # v27 (user: black outlines too thick, letters touching): the black backing kept only LOGO_RIM px round the letters
        ink = (A[..., 3] > 10) & (A[..., :3].max(-1) >= 110); d = distance_transform_edt(~ink)
        if LOGO_RIM: A[..., 3] *= np.clip(LOGO_RIM + 0.5 - d, 0, 1); im = Image.fromarray(A.astype(np.uint8), 'RGBA')
        a = A[..., 3]; ys, xs = np.nonzero(a > 10)
        _LG = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    return _LG

def paste(img, rgba, box):
    """alpha-paste a PIL RGBA image exactly into box (x0, y0, x1, y1) (the caller keeps the aspect)."""
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    img.paste(rgba.resize((x1 - x0, y1 - y0), Image.LANCZOS), (x0, y0), rgba.resize((x1 - x0, y1 - y0), Image.LANCZOS))

def fit(ar, cx, cy, mw, mh):
    w, h = mw, mw / ar
    if h > mh: h, w = mh, mh * ar
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)

def words(txt, fill=(18, 18, 20), stretch=1.12, italic=0.24, weight=0.0, track=0.07):   # v27 (user): thinner, letters apart (was 1.28 / 0.05 / 0)
    """bold slanted wide lettering (RIDER GATE), RGBA cropped to the ink."""
    try: f = ImageFont.truetype(FONT, 240)
    except OSError: f = ImageFont.load_default(size=240)
    sw = int(240 * weight); l, t, r, b = f.getbbox(txt, stroke_width=sw); pad = 80
    m = Image.new('L', (int(r - l + 2 * pad + len(txt) * track * 240), b - t + 2 * pad), 0); dr_ = ImageDraw.Draw(m); x_ = pad - l
    for ch in txt:                                                   # letter by letter: extra spacing (tracking)
        dr_.text((x_, pad - t), ch, font=f, fill=255, stroke_width=sw, stroke_fill=255); x_ += f.getlength(ch) + track * 240
    m = m.transform(m.size, Image.AFFINE, (1, italic, -italic * m.size[1] / 2, 0, 1, 0), Image.BICUBIC)
    a = np.asarray(m); ys, xs = np.nonzero(a > 8); m = m.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    m = m.resize((int(m.width * stretch), m.height), Image.LANCZOS)
    out = Image.new('RGBA', m.size, fill + (0,)); out.putalpha(m); return out

def grain(a, amp, seed):
    """light grain for matte materials (painted wood, raw steel)."""
    rg = np.random.default_rng(seed)
    return a + rg.normal(0, amp, a.shape[:2])[..., None] + gaussian_filter(rg.normal(0, 1, a.shape[:2]), 12)[..., None] * amp * 6

# ------------------------------------------------------------------ pads (arch)
def outline_normals(P):
    n = len(P); E = [P[(k + 1) % n] - P[k] for k in range(n)]
    return [np.array([e[1], -e[0]]) / np.linalg.norm(e) for e in E]       # outward, polygon CCW in (z, y)

def inset(P, r):
    N = outline_normals(P); n = len(P)
    return [P[k] - r * (N[k - 1] + N[k]) / (1 + N[k - 1] @ N[k]) for k in range(n)]

def arch_polys():
    g = G; zi = g['W'] / 2 + g['gap']; zo = zi + g['post_w']; yb = g['H'] + g['open_h']; yt = yb + g['head_h']; c = g['head_cham']
    head = [(-zo, yb), (zo, yb), (zo, yt - c), (zo - c, yt), (-zo + c, yt), (-zo, yt - c)]
    post_p = [(zi, g['tip']), (zo, g['tip'] + g['cham']), (zo, yb), (zi, yb)]                 # +z post (outer edge at zo)
    post_m = [(-zi, g['tip']), (-zi, yb), (-zo, yb), (-zo, g['tip'] + g['cham'])]             # -z post
    return {k: np.array(v, float) for k, v in dict(head=head, post_p=post_p, post_m=post_m).items()}

def face_map(P, side):
    """(z, y) -> (s, t) in ft inside the outline bbox, s along the viewer's right: front (+x) right = -z, back (-x) right = +z."""
    zmin, zmax = P[:, 0].min(), P[:, 0].max(); ymin = P[:, 1].min()
    return lambda q: ((zmax - q[0]) if side > 0 else (q[0] - zmin), q[1] - ymin)

def pad_art(kind, P, side, ppf):
    """front artwork of one pad face, drawn at its real size (ppf px / ft) over the outline bbox."""
    g = G; r = g['pad_t'] / 2; fm = face_map(P, side)
    w_ft, h_ft = np.ptp(P[:, 0]), np.ptp(P[:, 1]); W, H = int(round(w_ft * ppf)), int(round(h_ft * ppf))
    px = lambda st: (st[0] * ppf, (h_ft - st[1]) * ppf)
    Q = [px(fm(q)) for q in inset(P, r)]
    # yellow vinyl, puffy: darker towards the edges, light AO on the low part of the posts (beside the box, near the ground)
    mk = Image.new('L', (W, H), 0); ImageDraw.Draw(mk).polygon(Q, fill=255); inside = np.asarray(mk) > 0
    d = distance_transform_edt(inside) / ppf
    k = 1 - 0.10 * np.clip(1 - d / 0.35, 0, 1) ** 2
    yy = (h_ft - (np.arange(H)[:, None] + 0.5) / ppf) + P[:, 1].min()             # model y (ft) of each row
    k = k * (1 + 0.035 * np.clip((yy - g['H'] - 3) / 6, -1, 1)) * (1 - 0.20 * np.clip((g['H'] * 1.05 - yy) / (g['H'] * 1.05), 0, 1) ** 1.3)
    a = np.ones((H, W, 3)) * np.array(YEL, float) * k[..., None]
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); dr = ImageDraw.Draw(img)
    # v27 (user: liked without): no printed black outline round the pads any more (was dr.line(..., width 2 x 0.018 ft))
    tab = 0.075 * FT * ppf
    def tab_at(st, ax=0.0, ay=0.0):                      # black velcro tab, inside the face, anchored on the edge
        if not TABS: return                              # v27b (user): no small black squares
        x, y = px(st); dr.rectangle([x - tab / 2 + ax * tab / 2, y - tab / 2 + ay * tab / 2, x + tab / 2 + ax * tab / 2, y + tab / 2 + ay * tab / 2], fill=BLK)
    lg = logo_img(); ar = lg.width / lg.height
    if kind == 'head':
        fw = w_ft - 2 * r; ht = h_ft
        bx = fit(ar, W / 2, 0, 0.90 * fw * ppf, 1e9); lh = bx[3] - bx[1]
        top = 0.17 * ht * ppf; paste(img, lg, (bx[0], top, bx[2], top + lh))
        wd = words('RIDER GATE'); cap = 0.19 * ht * ppf; ww = cap * wd.width / wd.height
        x0 = bx[0] + 0.085 * (bx[2] - bx[0]); y0 = top + lh * 0.97
        paste(img, wd, (x0, y0, x0 + ww, y0 + cap))
        for s in (0.30, 0.70): tab_at((r + s * fw, h_ft - r), ay=1)                    # top edge
        for s in (r, w_ft - r): tab_at((s, r), ax=(1 if s < w_ft / 2 else -1), ay=-1)   # bottom outer corners
        for s in (r + g['post_w'] - r, w_ft - g['post_w']): tab_at((s, r), ay=-1)        # above the posts' inner edges
    else:
        zs = [fm(q)[0] for q in P]; out_left = fm(P[np.argmax(np.abs(P[:, 0]))])[0] < w_ft / 2
        rect_lo = g['cham'] * 0.86; rect_hi = h_ft - 0.10 * FT; L_ = rect_hi - rect_lo
        lgv = lg.rotate(90, expand=True)                                               # reads bottom -> top, never mirrored
        fw = w_ft - 2 * r; lw = min(L_ / ar, 0.56 * fw)
        cx = w_ft / 2 * ppf; cyl = (h_ft - (rect_lo + rect_hi) / 2) * ppf
        paste(img, lgv, (cx - lw * ppf / 2, cyl - lw * ar * ppf / 2, cx + lw * ppf / 2, cyl + lw * ar * ppf / 2))
        for s in (r, w_ft - r):
            sgn = 1 if s < w_ft / 2 else -1
            tab_at((s, h_ft - r), ax=sgn, ay=1); tab_at((s, h_ft * 0.52), ax=sgn)        # top corners, mid-height
        so = r if out_left else w_ft - r; tab_at((so, g['cham'] + r * 0.6), ax=(1 if out_left else -1))   # outer edge, above the cut
        del zs
    return img

def pad(m, P, xc, rect_f, rect_b, pal):
    """soft pad: flat printed faces (outline inset by r) + a half-round edge all around (r = half the thickness, black piping
    at the middle), in-plane corners rounded with the same radius."""
    r = G['pad_t'] / 2; N = outline_normals(P); Q = inset(P, r); n = len(P)
    path = []
    for k in range(n):
        a0 = np.arctan2(N[k - 1][1], N[k - 1][0]); da = (np.arctan2(N[k][1], N[k][0]) - a0) % (2 * np.pi)
        ns = max(1, int(np.ceil(np.degrees(da) / 30)))
        for j in range(ns + 1):
            a = a0 + da * j / ns; path.append((Q[k], np.array([np.cos(a), np.sin(a)])))
    ph = np.radians(PHI)
    def pt(e, f):
        q, dd = e; zy = q + r * np.cos(f) * dd; return np.array([xc + r * np.sin(f), zy[1], zy[0]])
    def nr(e, f):
        dd = e[1]; return np.array([np.sin(f), np.cos(f) * dd[1], np.cos(f) * dd[0]])
    for i in range(len(path)):
        e0, e1 = path[i], path[(i + 1) % len(path)]
        for j in range(len(ph) - 1):
            pts = [pt(e0, ph[j]), pt(e1, ph[j]), pt(e1, ph[j + 1]), pt(e0, ph[j + 1])]
            u = []
            for p in pts:
                if not any(np.allclose(p, q, atol=1e-6) for q in u): u.append(p)
            if len(u) < 3: continue
            N3 = nr(e0, ph[j]) + nr(e1, ph[j]) + nr(e0, ph[j + 1]) + nr(e1, ph[j + 1]); N3 /= np.linalg.norm(N3)
            src = pal['blk'] if abs(PHI[j] + PHI[j + 1]) < 1 and abs(PHI[j]) < 10 else pal['yel']
            uv = m.uv_px(*src[1]); m.tri_fan(u, N3, [uv] * len(u))
    for side, rect in ((1, rect_f), (-1, rect_b)):
        fm = face_map(P, side); w_ft, h_ft = np.ptp(P[:, 0]), np.ptp(P[:, 1]); px0, py0, px1, py1 = rect
        pts = [np.array([xc + side * r, q[1], q[0]]) for q in Q]
        uvs = [m.uv_px(px0 + fm(q)[0] / w_ft * (px1 - px0), py1 - fm(q)[1] / h_ft * (py1 - py0)) for q in Q]
        m.tri_fan(pts, np.array([side * 1.0, 0, 0]), uvs)

# ------------------------------------------------------------------ box + ramps artwork
def banner(w_ft, h_ft, ppf):
    """box side banner: yellow, black border, real logo + RIDER GATE (as on the photos), grommets."""
    W, H = int(w_ft * ppf), int(h_ft * ppf); img = Image.new('RGB', (W, H), BLK); d = ImageDraw.Draw(img)
    b = int(0.035 * FT * ppf); d.rectangle([b, b, W - 1 - b, H - 1 - b], fill=YEL)
    lg = logo_img(); ar = lg.width / lg.height
    bx = fit(ar, W / 2, 0, 0.84 * (W - 2 * b), 1e9); lh = bx[3] - bx[1]; top = (H - lh * 1.75) / 2
    paste(img, lg, (bx[0], top, bx[2], top + lh))
    wd = words('RIDER GATE'); cap = lh * 0.42; ww = cap * wd.width / wd.height; x0 = bx[0] + 0.10 * (bx[2] - bx[0])
    paste(img, wd, (x0, top + lh * 1.02, x0 + ww, top + lh * 1.02 + cap))
    gr = b * 0.42
    for x in (b * 0.5, W / 2, W - b * 0.5):
        for y in (b * 0.5, H - b * 0.5): d.ellipse([x - gr, y - gr, x + gr, y + gr], fill=(150, 150, 152)); d.ellipse([x - gr / 2, y - gr / 2, x + gr / 2, y + gr / 2], fill=(40, 40, 40))
    return img

def box_side(w_ft, h_ft, ppf, with_banner, seed):
    """black painted box side, steel corner angles and top / bottom rails, light grain, AO towards the ground."""
    W, H = int(w_ft * ppf), int(h_ft * ppf)
    a = grain(np.ones((H, W, 3)) * np.array(BOX, float), 1.6, seed)
    st = int(0.045 * FT * ppf)
    for sl in (np.s_[:, :st], np.s_[:, W - st:], np.s_[:st, :], np.s_[H - st:, :]): a[sl] = np.array(STEEL, float) * 0.95
    a[:, st:st + 2] *= 0.6; a[:, W - st - 2:W - st] *= 0.6; a[st:st + 2, :] *= 0.6; a[H - st - 2:H - st, :] *= 0.6
    for x in np.arange(W / 3, W - 1, W / 3)[:2] if w_ft > 5 else ():                    # plywood panel joints
        a[:, int(x):int(x) + 2] *= 0.55
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if with_banner:
        bw, bh = 1.80 * FT, h_ft - 0.13 * FT; bn = banner(bw, bh, ppf)
        img.paste(bn, (int((W - bn.width) / 2), int(0.06 * FT * ppf)))
    a = np.asarray(img).astype(float); t = np.linspace(0, 1, H)[:, None, None]
    a = a * (1 - 0.26 * np.clip((t - 0.45) / 0.55, 0, 1) ** 1.4)
    dust = np.clip((t - 0.80) / 0.20, 0, 1) * 0.35; a = a * (1 - dust) + np.array([118, 96, 72.0]) * dust * 0.55 + a * dust * 0.45
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def box_top(w_ft, h_ft, ppf, seed=5):
    """black-grey painted plywood top, worn and dusty, a lighter tyre track along x (riding line)."""
    W, H = int(w_ft * ppf), int(h_ft * ppf); rg = np.random.default_rng(seed)
    a = grain(np.ones((H, W, 3)) * np.array((50, 50, 52), float), 1.8, seed)
    z = np.abs(np.linspace(-1, 1, H))[:, None, None]
    a = a + np.array([30, 26, 20.0]) * np.exp(-(z / 0.22) ** 2) * (0.6 + 0.4 * gaussian_filter(rg.random((H, W)), 6)[..., None])
    for _ in range(60):
        x, y, rr = rg.random() * W, rg.random() * H, rg.uniform(1, 4)
        yy, xx = np.ogrid[:H, :W]; mk = (xx - x) ** 2 + (yy - y) ** 2 < rr * rr; a[mk] = a[mk] * 0.5 + np.array([120, 100, 78.0]) * 0.5
    e = int(0.012 * FT * ppf); a[:e] *= 0.75; a[-e:] *= 0.75; a[:, :e] *= 0.75; a[:, -e:] *= 0.75
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def mesh_tile(w_ft, l_ft, ppf):
    """expanded metal sheet, ONE piece: diamonds (long axis across the ramp), strands lit on their upper edge; RGBA (holes = 0)."""
    W, H = int(w_ft * ppf), int(l_ft * ppf); S = 4
    big = Image.new('L', (W * S, H * S), 255); d = ImageDraw.Draw(big)
    lw, sw = 0.046 * FT * ppf * S, 0.022 * FT * ppf * S; strand = 0.0062 * FT * ppf * S
    hw, hh = lw / 2 - strand, sw / 2 - strand * 0.62
    for j, y in enumerate(np.arange(0, H * S + sw, sw / 2)):
        off = lw / 2 * (j % 2)
        for x in np.arange(-lw + off, W * S + lw, lw):
            d.polygon([(x - hw, y), (x, y - hh), (x + hw, y), (x, y + hh)], fill=0)
    al = np.asarray(big.resize((W, H), Image.LANCZOS)).astype(float) / 255
    up = np.roll(al, 1, axis=0); edge = np.clip(al - up, 0, 1)                        # strand edge facing up the ramp: lighter
    rgb = np.ones((H, W, 3)) * np.array((60, 58, 55), float)
    rgb = rgb * (1 + 0.55 * edge[..., None]) * (1 - 0.25 * np.clip(np.roll(al, -1, 0) - al, 0, 1)[..., None])
    rgb = grain(rgb, 2.0, 11)
    alpha = np.where(al > 0.45, 255, 0)
    return np.dstack([np.clip(rgb, 0, 255), alpha]).astype(np.uint8)

def gate_texture():
    g = G; img = Image.new('RGBA', (TW, TW), YEL + (255,)); R = {}
    P = arch_polys(); r = g['pad_t'] / 2
    def place(name, im, x, y):
        img.paste(im.convert('RGBA') if im.mode != 'RGBA' else im, (x, y)); R[name] = (x, y, x + im.width, y + im.height); return im
    hd = place('head', pad_art('head', P['head'], 1, 190), 8, 8)
    pa = pad_art('post', P['post_p'], 1, 115); pb = pad_art('post', P['post_p'], -1, 115)
    place('post_a', pa, 8, 512); place('post_b', pb, 8 + pa.width + 16, 512)
    xs = 8 + 2 * pa.width + 40
    sd = place('side', box_side(g['L'] - 2 * g['edge_r'], g['H'] - g['top_t'], 136, True, 3), xs, 512)
    en = place('end', box_side(g['W'] - 2 * g['edge_r'], g['H'] - g['top_t'], 100, False, 4), xs, 512 + sd.height + 16)
    place('top', box_top(g['L'] + 2 * g['lip'], g['W'] + 2 * g['lip'], 80), xs + en.width + 16, 512 + sd.height + 16)
    ms = Image.fromarray(mesh_tile(g['ramp_w'] - 2 * g['rail'], g['ramp_len'], 150), 'RGBA')
    place('mesh', ms, TW - ms.width - 8, 8)
    for k, v in R.items():
        assert v[2] <= TW and v[3] <= TW - 136, (k, v)
    for a_, b_ in [(a_, b_) for a_ in R for b_ in R if a_ < b_]:
        A, B = R[a_], R[b_]; assert A[2] <= B[0] or B[2] <= A[0] or A[3] <= B[1] or B[3] <= A[1], ('overlap', a_, b_)
    rgb = img.convert('RGB')
    pal = palette(rgb, ['yel', 'blk', 'box', 'steel', 'mesh'], [YEL, (30, 30, 32), BOX, STEEL, (64, 62, 58)])
    out = rgb.convert('RGBA'); out.putalpha(img.getchannel('A')); pal.update(R)
    return out, pal

# ------------------------------------------------------------------ gate model
def ramp(m, pal, sgn):
    """steel ramp at the +x (sgn 1) or -x (sgn -1) end: hook plate on the box top, frame of square tubes, mesh sheet
    (double-sided, see-through), foot bar on the ground."""
    g = G; a = g['rail']; w = g['ramp_w']; L2 = g['L'] / 2; tp = 0.01 * FT
    run = np.sqrt(g['ramp_len'] ** 2 - g['H'] ** 2)
    A = np.array([sgn * L2, g['H'] + tp, 0.0]); B = np.array([sgn * (L2 + run), 2 * a, 0.0])
    d = (B - A) / np.linalg.norm(B - A); n = np.cross(d, [0, 0, 1.0]) * -sgn
    if n[1] < 0: n = -n
    Ls = np.linalg.norm(B - A); S = lambda s, z: A + d * s + np.array([0, 0, z])
    # hook plate lying on the box top
    x0, x1 = sorted([sgn * (L2 - g['hook']), sgn * L2])
    m.box(x0, x1, g['H'], g['H'] + tp, -w / 2, w / 2, {'*': pal['steel']})
    zr = w / 2 - a
    for z in (-zr, zr): m.tube(S(0.06 * FT, z) - n * a, S(Ls, z) - n * a + d * 0.0, a, pal['steel'])          # side rails
    for z in (-w / 6, w / 6): m.tube(S(0.08 * FT, z) - n * a * 1.1, S(Ls - 0.05 * FT, z) - n * a * 1.1, a * 0.8, pal['steel'])   # stiffeners
    for s in (0.08 * FT, Ls * 0.5): m.tube(S(s, -zr) - n * a, S(s, zr) - n * a, a * 0.85, pal['steel'])    # cross bars
    m.tube(S(Ls, -w / 2) - n * a, S(Ls, w / 2) - n * a, a, pal['steel'])                                  # foot bar
    px0, py0, px1, py1 = pal['mesh']
    for side in (1, -1):
        off = n * (0.004 if side > 0 else -0.004)
        P_ = [S(0, -zr) + off, S(0, zr) + off, S(Ls, zr) + off, S(Ls, -zr) + off]
        uv = [m.uv_px(px0, py0), m.uv_px(px1, py0), m.uv_px(px1, py1), m.uv_px(px0, py1)]
        m.tri_fan(P_, n * side, uv)

def gate_model(pal):
    g = G; m = Mesh(TW, TW); L2, W2, H = g['L'] / 2, g['W'] / 2, g['H']; e = g['edge_r']
    # box body: rounded vertical edges, sides / ends textured, top sheet with a small overhang
    faces = {'+z': ('r', pal['side']), '-z': ('r', pal['side']), '+x': ('r', pal['end']), '-x': ('r', pal['end'])}
    m.rbox(-L2, L2, 0.0, H - g['top_t'], -W2, W2, e, 1, faces, pal['steel'], seg=3)
    lp = g['lip']
    m.box(-L2 - lp, L2 + lp, H - g['top_t'], H, -W2 - lp, W2 + lp, {'+y': ('r', pal['top']), '+x': pal['box'], '-x': pal['box'],
                                                                     '+z': pal['box'], '-z': pal['box'], '-y': pal['box']})
    ramp(m, pal, 1); ramp(m, pal, -1)
    # arch pads at the -x end
    P = arch_polys(); xc = -L2 + g['arch_dx']
    pad(m, P['head'], xc, pal['head'], pal['head'], pal)
    # +z post: front (+x) sees the outer edge on its left -> art 'post_a' (drawn with side +1 of post_p); back -> 'post_b'
    pad(m, P['post_p'], xc, pal['post_a'], pal['post_b'], pal)
    pad(m, P['post_m'], xc, pal['post_b'], pal['post_a'], pal)
    return m

# ------------------------------------------------------------------ inflatable cylinder
def _smooth(m, P, N, UV):
    a = len(m.V); P = [np.asarray(p, float) for p in P]; N = [np.asarray(n, float) / np.linalg.norm(n) for n in N]
    if np.dot(np.cross(P[1] - P[0], P[2] - P[0]), sum(N)) < 0: P, N, UV = P[::-1], N[::-1], UV[::-1]
    for p, n, t in zip(P, N, UV): m.V.append((*p, *n, *t))
    for k in range(1, len(P) - 1): m.I += [a, a + k, a + k + 1]

CT = dict(body=(0, 767), shoulder=(784, 900), base=(916, 1010))     # texture rows

def cyl_profile():
    """lathe profile [(r, y, part)] bottom -> top: black base (rounded top edge), yellow body (slight bulge), rounded top."""
    c = CYL; R, Ht, a = c['R'], c['H'], c['top']; br, bh = c['base_r'], c['base_h']; f = 0.03 * FT
    base = [(br, 0.0), (br, bh - f)] + [(br - f + f * np.cos(t), bh - f + f * np.sin(t)) for t in np.linspace(0, np.pi / 2, 3)[1:]] + [(R * 0.97, bh)]
    ys = Ht - a; body = [(R * 0.995, bh - 0.02 * FT), (R * 1.0, bh + 0.05 * FT), (R * 1.018, (bh + ys) / 2), (R * 1.0, ys)]
    top = []
    for th in np.linspace(0, np.pi / 2, 8)[1:]:
        p = 2.6; top.append((R * np.cos(th) ** (2 / p), ys + a * np.sin(th) ** (2 / p)))
    top[-1] = (0.0, Ht)
    return base, body, top

def cyl_texture(body_rgb=YEL, logo=True, lg_src=None, L_m=1.00, ucs=(1 / 6, 1 / 2, 5 / 6), centred=False):
    c = CYL; img = np.zeros((1024, 1024, 3)) + np.array(body_rgb, float)
    b0, b1 = CT['body']; base, body, top = cyl_profile()
    y_lo, y_hi = body[0][1], body[-1][1]
    pxu = 1024 / (2 * np.pi * c['R']); pxv = (b1 - b0) / (y_hi - y_lo)
    rows = np.arange(1024)[:, None, None]
    yv = y_hi - (rows - b0) / pxv                                                     # model y of each body row
    img[b0:b1 + 1] *= (1 - 0.22 * np.clip((c['base_h'] + 0.9 - yv[b0:b1 + 1]) / 0.9, 0, 1) ** 1.5)   # AO near the base
    s0, s1 = CT['shoulder']; img[s0:s1 + 1] *= np.linspace(1.0, 1.06, s1 - s0 + 1)[:, None, None]
    img[b0:b0 + 3] *= 0.80; img[s0:s0 + 3] *= 0.80                                   # sewn seam where the top cap joins
    img[b0:b1 + 1, 0:2] *= 0.94; img[b0:b1 + 1, 1022:1024] *= 0.94                    # vertical seam (between two logos)
    k0, k1 = CT['base']; img[k0:k1 + 1] = np.array((24, 24, 26.0)) * np.linspace(1.15, 0.75, k1 - k0 + 1)[:, None, None]
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.rectangle([505, k0 + 22, 535, k0 + 52], fill=(205, 205, 205)); d.rectangle([509, k0 + 26, 531, k0 + 48], fill=(60, 60, 64))   # small valve label
    if not logo: return im
    lg = (lg_src or logo_img()).rotate(90, expand=True); ar = lg.height / lg.width     # vertical, reads bottom -> top
    Lft = L_m * FT; Wft = Lft / ar; yc = c['base_h'] + 0.06 * FT + Lft / 2
    if centred is True: yc = (y_lo + y_hi) / 2                                         # v28 (user): centred on the body
    elif centred: yc = min(float(centred), y_hi - Lft / 2 - 0.02)                      # v29 (user): centred on the inflatable (ft)
    for uc in ucs:
        cx, cy = uc * 1024, b0 + (y_hi - yc) * pxv
        paste(im, lg, (cx - Wft * pxu / 2, cy - Lft * pxv / 2, cx + Wft * pxu / 2, cy + Lft * pxv / 2))
    return im

def cyl_model(body_rgb=YEL, logo=True):
    c = CYL; m = Mesh(1024, 1024); sg = c['seg']; base, body, top = cyl_profile()
    ang = np.linspace(0, 2 * np.pi, sg + 1)
    def ring_pts(prof):
        out = []
        for i, (r, y) in enumerate(prof):
            a_, b_ = prof[max(i - 1, 0)], prof[min(i + 1, len(prof) - 1)]
            tr, ty = b_[0] - a_[0], b_[1] - a_[1]; nr_, ny_ = ty, -tr; L_ = np.hypot(nr_, ny_); out.append((r, y, nr_ / L_, ny_ / L_))
        return out
    def lathe(prof, vrow):
        pr = ring_pts(prof)
        for i in range(len(pr) - 1):
            for k in range(sg):
                q = []
                for (r, y, nr_, ny_), vv in ((pr[i], vrow(i)), (pr[i + 1], vrow(i + 1))):
                    for kk in (k, k + 1):
                        t = ang[kk]; q.append(((r * np.cos(t), y, -r * np.sin(t)), (nr_ * np.cos(t), ny_, -nr_ * np.sin(t)), m.uv_px(kk / sg * 1023.5, vv)))
                P_ = [q[0][0], q[1][0], q[3][0], q[2][0]]; N_ = [q[0][1], q[1][1], q[3][1], q[2][1]]; U_ = [q[0][2], q[1][2], q[3][2], q[2][2]]
                if pr[i][0] < 1e-6: P_, N_, U_ = P_[1:], N_[1:], U_[1:]
                if pr[i + 1][0] < 1e-6: P_, N_, U_ = [P_[0], P_[1], P_[2]], [N_[0], N_[1], N_[2]], [U_[0], U_[1], U_[2]]
                _smooth(m, P_, N_, U_)
    k0, k1 = CT['base']; lathe(base, lambda i: k1 - i / (len(base) - 1) * (k1 - k0))
    b0, b1 = CT['body']; y_lo, y_hi = body[0][1], body[-1][1]
    lathe(body, lambda i: b0 + (y_hi - body[i][1]) / (y_hi - y_lo) * (b1 - b0))
    s0, s1 = CT['shoulder']; tp = [body[-1]] + top
    lathe(tp, lambda i: s0 + i / (len(tp) - 1) * (s1 - s0))
    return m, cyl_texture(body_rgb, logo)

# ------------------------------------------------------------------ collision (.shp: "x y z radius friction spring damping" spheres)
def _rows(rows): return '\n'.join([str(len(rows))] + [' '.join(f'{v:.4f}' if k < 4 else f'{v:g}' for k, v in enumerate(r)) for r in rows]) + '\n'

def cyl_shape():
    """v27: the track pylons / the inflatable: stiff low (wheel / engine height), soft and slippery above (like the v35 pylons)."""
    R = CYL['R'] * 0.95
    return _rows([(0, y, 0, R, 0.3, 140, 9) for y in (1.0, 1.9)] + [(0, y, 0, R, 0.2, 30, 1.5) for y in (2.9, 3.7)])

RIDE = (1.5, 1000, 200)                 # rideable steel (same as the user's FMX ramp ramp_50.shp)
PADS = (0.5, 300, 30)                   # arch pads: softer
def gate_shape():
    """v27 (user: physics on the box and the ramps): sphere carpets under the box top and the two ramps (centres one radius
    under the surface, like ramp_50.shp), the box body filled, the arch posts / head as small soft spheres."""
    g = G; L2, W2, H = g['L'] / 2, g['W'] / 2, g['H']; rows = []
    r = 0.5
    for x in np.arange(-L2 + 0.3, L2 - 0.3 + 1e-6, (2 * L2 - 0.6) / round((2 * L2 - 0.6) / 0.35)):
        for z in np.linspace(-W2 + 0.3, W2 - 0.3, 11): rows.append((x, H - r, z, r) + RIDE)
    rb = 0.75
    for x in np.linspace(-L2 + 0.6, L2 - 0.6, 10):
        for z in np.linspace(-W2 + 0.6, W2 - 0.6, 4):
            for y in (0.75, 1.75): rows.append((x, y, z, rb) + RIDE)
    run = np.sqrt(g['ramp_len'] ** 2 - H ** 2); w = g['ramp_w']
    for sgn in (1, -1):
        A = np.array([sgn * L2, H, 0.0]); B = np.array([sgn * (L2 + run), 0.0, 0.0]); Ls = np.linalg.norm(B - A); d = (B - A) / Ls
        n = np.array([-d[1], d[0], 0.0]) * sgn
        if n[1] < 0: n = -n
        for s_ in np.linspace(0.15, Ls - 0.1, 20):
            for z in np.linspace(-w / 2 + 0.25, w / 2 - 0.25, 6):
                c_ = A + d * s_ - n * r; rows.append((c_[0], c_[1], z, r) + RIDE)
    xc = -L2 + g['arch_dx']; P = arch_polys(); rp = 0.3
    from matplotlib.path import Path as MP
    for k_, Pp in P.items():
        mp = MP(Pp); zs = np.arange(Pp[:, 0].min() + rp, Pp[:, 0].max() - rp + 1e-6, 0.45); ys = np.arange(Pp[:, 1].min() + rp, Pp[:, 1].max() - rp + 1e-6, 0.45)
        for z in zs:
            for y in ys:
                if mp.contains_point((z, y)): rows.append((xc, y, z, rp) + PADS)
    return _rows(rows)

PYLON_RGB = dict(pylon_round=(24, 24, 26), pylon_round_motul=(196, 30, 34))   # v27 (user): the track pylons = this inflatable
PYLON_LOGO = dict(pylon_round=('fly', 1.0), pylon_round_motul=('motul', 1.0))   # v29 (user): almost the full height (was 0.70 / 0.60 m)   # v28 (user): logos back (Fly / Motul), centred, facing +-z

# ------------------------------------------------------------------ preview (software z-buffer, NOT a game render)
CYL_AT = (G['L'] / 2 + 0.9 * FT, 0, -G['W'] / 2 - 1.6 * FT)    # preview only: cylinder beside the exit ramp (photo 185)

def scale_person(pos):
    """grey 1.78 m stand-in person (preview only, not exported): legs, torso, arms, head."""
    img = Image.new('RGB', (512, 512), (128, 128, 128)); pal = palette(img, ['jeans', 'shirt', 'skin'], [(46, 56, 78), (120, 122, 128), (196, 156, 126)])
    m = Mesh(512, 512); M = FT
    for z in (-0.1, 0.1): m.rbox(-0.08 * M, 0.08 * M, 0, 0.86 * M, (z - 0.07) * M, (z + 0.07) * M, 0.05 * M, 1, {'*': pal['jeans']}, pal['jeans'], seg=3)
    m.rbox(-0.12 * M, 0.12 * M, 0.84 * M, 1.46 * M, -0.21 * M, 0.21 * M, 0.08 * M, 1, {'*': pal['shirt']}, pal['shirt'], seg=3)
    for z in (-0.26, 0.26): m.rbox(-0.05 * M, 0.05 * M, 0.82 * M, 1.42 * M, (z - 0.05) * M, (z + 0.05) * M, 0.04 * M, 1, {'*': pal['shirt']}, pal['skin'], seg=3)
    m.rbox(-0.1 * M, 0.1 * M, 1.50 * M, 1.78 * M, -0.085 * M, 0.085 * M, 0.07 * M, 1, {'*': pal['skin']}, pal['skin'], seg=3)
    V = np.array(m.V, np.float32); V[:, :3] += np.array(pos, np.float32)
    t = np.asarray(img.convert('RGBA'), np.float32) / 255
    return V, np.array(m.I, np.int64).reshape(-1, 3), t

def preview(out_path, custom=None):
    """custom: list of (eye, target, fov, solo) for extra close-ups (debug)."""
    from preview_stt_scene import Cam, raster, load_jm
    objs = []
    for name, pos in (('rider_gate', (0, 0, 0)), ('f50_cylinder', CYL_AT)):
        V, I = load_jm(f'{OUTD}/{name}.jm'); t = np.asarray(Image.open(f'{OUTD}/{name}.png').convert('RGBA'), np.float32) / 255
        V = V.copy(); V[:, :3] += np.array(pos, np.float32); objs.append((V, I, t))
    objs.append(scale_person((-0.6 * FT, 0, -G['W'] / 2 - 0.9 * FT)))       # 1.78 m person for scale (preview only)
    Lg = np.array([-0.45, 0.8, 0.4]); Lg /= np.linalg.norm(Lg)
    def shot(eye, tgt, W=900, H=760, fov=50, solo=None):
        cam = Cam(eye, tgt, W, H, fov); img = np.zeros((H, W, 3), np.float32)
        sky = np.linspace(0, 1, H)[:, None, None]; img[:] = np.array([0.55, 0.70, 0.90]) * (1 - sky) + np.array([0.82, 0.86, 0.90]) * sky
        zb = np.full((H, W), np.inf, np.float32)
        gs = np.arange(-40, 41, 4.0); GX, GZ = np.meshgrid(gs, gs); P = np.stack([GX, np.zeros_like(GX), GZ], -1).reshape(-1, 3)
        n = len(gs); ii, jj = np.meshgrid(np.arange(n - 1), np.arange(n - 1), indexing='ij'); a = (ii * n + jj).ravel()
        I = np.concatenate([np.stack([a, a + 1, a + n], 1), np.stack([a + 1, a + n + 1, a + n], 1)])
        rg = np.random.default_rng(0); C = np.array([0.55, 0.43, 0.31]) * (0.92 + 0.12 * rg.random((len(P), 1)))
        raster(img, zb, cam, P, I, lambda ti, B: (C[I[ti]] * B[:, :, None]).sum(1))
        for V, Ii, tex in (objs if solo is None else [objs[solo]]):
            th, tw = tex.shape[:2]
            def uvpx(ti, B, V=V, Ii=Ii, tw=tw, th=th):
                uv = (V[Ii[ti], 6:8][None] * B[:, :, None]).sum(1)
                return np.clip((uv[:, 1] * 0 + 1 - uv[:, 1]) * th, 0, th - 1).astype(int), np.clip(uv[:, 0] * tw, 0, tw - 1).astype(int)
            def col(ti, B, V=V, Ii=Ii, tex=tex):
                py, px = uvpx(ti, B); nn = (V[Ii[ti], 3:6][None] * B[:, :, None]).sum(1)
                return tex[py, px, :3] * (0.62 + 0.45 * np.clip(nn @ Lg, 0, 1))[:, None]
            raster(img, zb, cam, V[:, :3], Ii, col, lambda ti, B, tex=tex: tex[uvpx(ti, B)][:, 3])
        return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    L2 = G['L'] / 2
    if custom:
        views = [shot(e, t, fov=f, solo=so) for e, t, f, so in custom]
    else:
      views = [shot((L2 + 15.0, 6.2, 3.5), (-1.0, 5.0, 0.3)),                 # like photo 185: from the exit ramp, arch behind
             shot((-L2 - 22.0, 5.5, -4.0), (0.0, 6.0, 0.0), fov=42),        # like 186 / 188: facing the arch (entry side)
             shot((L2 + 9.0, 3.2, 10.0), (-1.5, 4.5, 0.0)),                 # like 187: low 3/4, ramp and side banner
             shot((CYL_AT[0] + 6.5, 3.6, CYL_AT[2] - 7.0), (CYL_AT[0], 2.4, CYL_AT[2]), fov=40, solo=1)]
    W_, H_ = views[0].size; sheet = Image.new('RGB', (W_ * 2, H_ * 2), (255, 255, 255))
    for k, v in enumerate(views): sheet.paste(v, ((k % 2) * W_, (k // 2) * H_))
    os.makedirs(os.path.dirname(out_path), exist_ok=True); sheet.save(out_path); print('preview', out_path)

def build(outd=OUTD):
    os.makedirs(outd, exist_ok=True); info = {}
    img, pal = gate_texture(); m = gate_model(pal)
    info['rider_gate'] = m.write(f'{outd}/rider_gate.jm', (16, 0.4, 0.4, 0.4, 0.4)); img.save(f'{outd}/rider_gate.png', optimize=True)
    info['rider_gate'] += (np.array([v[:3] for v in m.V]).min(0).round(2), np.array([v[:3] for v in m.V]).max(0).round(2))
    cm, ci = cyl_model()
    info['f50_cylinder'] = cm.write(f'{outd}/f50_cylinder.jm', (20, 0.5, 0.4, 0.4, 0.4)); ci.save(f'{outd}/f50_cylinder.png', optimize=True)
    info['f50_cylinder'] += (np.array([v[:3] for v in cm.V]).min(0).round(2), np.array([v[:3] for v in cm.V]).max(0).round(2))
    open(f'{outd}/f50_cylinder.shp', 'w', newline='\n').write(cyl_shape())
    open(f'{outd}/rider_gate.shp', 'w', newline='\n').write(gate_shape())
    # v27 (user): the track pylons rebuilt as the real inflatable (0.6 x 1.42 m, round black base), plain black (1st one red), no logo
    pm, _ = cyl_model(PYLON_RGB['pylon_round'], logo=False)
    info['pylon_round'] = pm.write(f'{outd}/pylon_round.jm', (20, 0.5, 0.4, 0.4, 0.4)) + ((), ())
    import stt_ads as AD_
    for nm, rgb in PYLON_RGB.items():
        ln_, Lm_ = PYLON_LOGO[nm]
        cyl_texture(rgb, True, AD_.logo(ln_), Lm_, ucs=(0.25, 0.75), centred=(CYL['base_h'] + CYL['H']) / 2).save(f'{outd}/{nm}.png', optimize=True)
    open(f'{outd}/pylon_round.shp', 'w', newline='\n').write(cyl_shape())
    for k, (nv, nt, lo, hi) in info.items(): print(f'{k}: {nv} vertices, {nt} triangles, bbox {lo} .. {hi} ft')
    return info

if __name__ == '__main__':
    build()
    if '--preview' in sys.argv: preview(os.path.join(os.path.dirname(ROOT), 'apercus_sgm', 'rider_gate_3d.png'))
