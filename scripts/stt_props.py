"""Saint-Thibery v28 props, made from scratch with props_usland.Mesh (doc 12 conventions: 1 unit = 1 ft, y up, origin at
ground level, baked shades, one texture each). Asked by the user, shapes from the drone photos of the real track:
  - stake_yellow : yellow marker stake on the bump crests (both lane edges), ~1 m;
  - net_blue     : 8 ft section of the blue turn nets: one blue post at x = -4 (the next section brings the next post) and
                   a dark blue net (alpha) up to x = +4, double-sided; local +z = towards the inside of the turn;
  - start_floor  : ONE big steel floor (square mesh pattern, not diamonds) behind the whole gate row, its front edge cut
                   around each gate; origin = middle of the gate row at the hinge line, local -z = backwards (behind the gates).
Run: python scripts/stt_props.py -> assets/props/stake_yellow.*, net_blue.*, start_floor.*"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
from props_usland import Mesh, palette, OUTD, GATE, _ear_clip
import layouts_sx as LS
import layouts_stt as LT

STAKE = dict(h=3.3, r=0.09, seg=8, col=(236, 196, 18))
NET = dict(L=8.0, post_r=0.13, post_h=4.2, y0=0.25, y1=3.9, post=(24, 70, 196), net=(18, 42, 120))


def prism(m, cx, cz, r, h, seg, side_uv, top_uv, top_r=0.6, cap=0.08):
    """vertical n-sided post from y = 0 to h with a small chamfered top."""
    ang = np.linspace(0, 2 * np.pi, seg + 1)
    ring = lambda y, rr: [np.array([cx + rr * np.cos(t), y, cz + rr * np.sin(t)]) for t in ang]
    A, B, C = ring(0.0, r), ring(h - cap, r), ring(h, r * top_r)
    for k in range(seg):
        n = np.array([np.cos((ang[k] + ang[k + 1]) / 2), 0, np.sin((ang[k] + ang[k + 1]) / 2)])
        m.tri_fan([A[k], A[k + 1], B[k + 1], B[k]], n, [side_uv] * 4)
        nt = n * 0.55 + np.array([0, 0.83, 0]); nt /= np.linalg.norm(nt)
        m.tri_fan([B[k], B[k + 1], C[k + 1], C[k]], nt, [top_uv] * 4)
    m.tri_fan(C[:-1][::-1], np.array([0, 1.0, 0]), [top_uv] * seg)


PADDLE = dict(h=1.6, half=0.20, neck=0.107, foot=0.147, stem=0.035, stem_h=0.2, t=0.04, col=(214, 200, 34), edge=(170, 158, 22))   # v35 (user's green line on a screenshot): 2.2 -> 1.6 ft; v31 (user): one third smaller (was 3.3 ft high)

def paddle_profile():
    """v29: (y, half width) of the flat track-marker paddle (user's picture, the Acerbis kind, no logo): stem in the ground,
    small foot, neck, straight body, half-elliptic top. y = 0 at ground level."""
    P = PADDLE; k = P['h'] / 3.3                                    # v31: the lower part scales with the height
    prof = [(-P['stem_h'], P['stem']), (0.0, P['stem']), (0.001, P['foot']), (0.08 * k, P['foot']),
            (0.16 * k, P['neck'] + 0.02 * k), (0.24 * k, P['neck']), (0.32 * k, P['neck'] + 0.03 * k), (0.40 * k, P['half'] * 0.85), (0.46 * k, P['half'])]
    yt = P['h'] - 1.5 * P['half'] * 1.6
    prof.append((yt, P['half']))
    for a in np.linspace(0, np.pi / 2, 10)[1:]:
        prof.append((yt + (P['h'] - yt) * np.sin(a), max(P['half'] * np.cos(a), 0.004)))
    return prof

def stake():
    """v29: flat yellow paddle marker (all yellow, no logo), faces local +z (the riders) and -z; origin at ground level."""
    img = Image.new('RGB', (256, 256), PADDLE['col'])
    pal = palette(img, ['paint', 'edge'], [PADDLE['col'], PADDLE['edge']])
    m = Mesh(256, 256); t = PADDLE['t'] / 2; prof = paddle_profile()
    face = m.uv_px(64, 64); ed = m.uv_px(*pal['edge'][1])         # plain yellow area of the texture (above the palette)
    for (y0, w0), (y1, w1) in zip(prof[:-1], prof[1:]):
        for sg in (1, -1):
            Q = [np.array([-w0, y0, sg * t]), np.array([w0, y0, sg * t]), np.array([w1, y1, sg * t]), np.array([-w1, y1, sg * t])]
            m.tri_fan(Q, np.array([0, 0, sg * 1.0]), [face] * 4)
        for sx in (1, -1):                                          # thin edges
            Q = [np.array([sx * w0, y0, -t]), np.array([sx * w0, y0, t]), np.array([sx * w1, y1, t]), np.array([sx * w1, y1, -t])]
            n = np.array([sx * (y1 - y0), -(w1 - w0), 0.0]); n /= np.linalg.norm(n) + 1e-12
            m.tri_fan(Q, n, [ed] * 4)
    return m, img


# ------------------------------------------------------------------ v29: continuous net following the ground
NETR = dict(h=4.2, sink=0.3, post_every=8.0, post_h=4.7, post_w=0.11, tile=4.0, TW=1024, TH=1024, NR=896)   # v32: taller (3.6 -> 4.2 ft); one 4 ft
# tile repeated along the net (the 4096 px texture of v31 was too big: the game shrank it and the mesh disappeared)

def net_ribbon_texture():
    """v32: one 4 ft wide tile of black knotted net (1024 px wide = 256 px / ft), repeated along every net: rows 0..NR-1 = net
    height (sink + h), thick ropes top and bottom; rows NR+32.. = solid black for the posts. Square 0.2 ft cells (denser)."""
    W_, H_, NR = NETR['TW'], NETR['TH'], NETR['NR']; img = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    pxu = W_ / NETR['tile']; pyv = NR / (NETR['h'] + NETR['sink']); cell = 0.2
    hem, col, knot = (16, 40, 128, 255), (34, 82, 205, 255), (20, 52, 150, 255)    # v35 (user): blue mesh (v31-v34: black)
    xs = np.arange(0, W_, cell * pxu); ys = np.arange(30, NR - 30, cell * pyv)
    for x in xs: d.rectangle([x - 2, 0, x + 2, NR - 1], fill=col)                 # strands ~0.02 ft thick
    for y in ys: d.rectangle([0, y - 2, W_, y + 2], fill=col)
    for x in xs:
        for y in ys: d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=knot)           # knots
    for y in ys: d.line([(0, y - 2), (W_, y - 2)], fill=(90, 140, 240, 255), width=1)   # a lighter edge so the rope reads
    for x in xs: d.line([(x - 2, 0), (x - 2, NR - 1)], fill=(80, 128, 230, 255), width=1)
    d.rectangle([0, 0, W_, 22], fill=hem); d.rectangle([0, NR - 23, W_, NR - 1], fill=hem)   # top / bottom ropes
    d.rectangle([0, NR + 32, W_, H_ - 1], fill=(128, 90, 54, 255))                 # v35 (user): wooden posts
    return img


NET_SHP = dict(r=0.9, every=1.2, rows=(0.9, 2.5, 3.8), friction=1.0, spring=85, damping=4)   # v33 (user: v32 a bit too hard): 100 / 5 -> 85 / 4. v32: v31 (150 / 250) felt like a wall:
# the damping term (force ~ damping x speed) is what stops the bike; 5 per sphere ~ loses ~25 ft/s going through (estimate)

def net_shape(line_xz, ground, origin):
    """v31 (user: the net must slow the bike down): collision spheres along the net, same frame as net_ribbon (statue yaw 0,
    y = 0 at the ground under the origin). Format (MX Simulator forum): count, then x y z radius friction spring damping.
    Low spring + high damping = soft, the bike sinks in and loses speed (values not tested in game)."""
    from scipy.ndimage import gaussian_filter1d
    ox, oz = origin; g0 = ground(ox, oz); C = NET_SHP
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(line_xz, axis=0), axis=1))]
    gy = gaussian_filter1d(np.array([ground(x, z) for x, z in line_xz]) - g0, 1.0, mode='nearest')
    rows = []
    for s in np.linspace(0, L[-1], max(2, int(L[-1] / C['every']) + 1)):
        x_ = np.interp(s, L, line_xz[:, 0]) - ox; z_ = np.interp(s, L, line_xz[:, 1]) - oz; y_ = np.interp(s, L, gy)
        for h in C['rows']: rows.append(f"{x_:.4f} {y_ + h:.4f} {z_:.4f} {C['r']} {C['friction']} {C['spring']} {C['damping']}")
    return '\n'.join([str(len(rows))] + rows) + '\n'


# ------------------------------------------------------------------ v31: black pylon (user's picture: the right one, all black)
PYLON = dict(H=4.0, base_w=1.85, base_h=0.42, base_r=0.12, cyl_r=0.68, fillet=0.36, dome=0.07, seg=32,
             pad_w=4.5, pad_h=0.45, pad_sink=0.45, pad_r=0.6, pad_in=0.55, col_logo=(0.95, 2.95))
# v36 (user): dirt pad 3x higher (0.15 -> 0.45 ft) and much wider (2.6 -> 4.5 ft); the pylon itself unchanged, standing on it
# (top 3.7 -> 4.0 ft); Fly logo also on the column (vertical, reading upwards, +z and -z sides) between col_logo heights.
# v35 (user): rounder top (fillet 0.14 -> 0.36), Fly Racing logo on two opposite sides of the base (base 0.32 -> 0.42 ft high so
# the logo reads), a small dirt platform under it, a bit wider than the base (pad). Total height unchanged (3.7 ft).
# v33: a bit lower, fatter (v32: H 4.125, r 0.555, base 1.52)
FLY = f'{ROOT}/assets/logos/fly_racing_white.png'

def _smooth(m, P, N, UV):
    """quad / triangle with one normal per vertex (smooth cylinder), front face = average normal side."""
    a = len(m.V); P = [np.asarray(p, float) for p in P]; N = [np.asarray(n, float) / np.linalg.norm(n) for n in N]
    if np.dot(np.cross(P[1] - P[0], P[2] - P[0]), sum(N)) < 0: P, N, UV = P[::-1], N[::-1], UV[::-1]
    for p, n, t in zip(P, N, UV): m.V.append((*p, *n, *t))
    for k in range(1, len(P) - 1): m.I += [a, a + k, a + k + 1]

def _vinyl(h, w, sx, sy, seed, amp=12.0, base=(17, 17, 19.0)):
    """black vinyl with soft folds and creases (tileable noise), (h, w, 3) float."""
    from scipy.ndimage import gaussian_filter
    n = gaussian_filter(np.random.default_rng(seed).normal(0, 1, (h, w)), (sy, sx), mode='wrap'); n = (n - n.mean()) / (n.std() + 1e-9)
    f = gaussian_filter(np.random.default_rng(seed + 50).normal(0, 1, (h, w)), (sy * 1.2, sx * 1.6), mode='wrap'); f = (f - f.mean()) / (f.std() + 1e-9)
    R = 0.55 * np.exp(-(n / 0.35) ** 2) + 0.5 * f
    out = np.array(base) + R[..., None] * np.array([amp, amp, amp * 1.08])
    return out + np.random.default_rng(seed + 9).normal(0, 1.6, out.shape)

def _dirt(h, w, seed):
    """packed dirt, same family of browns as the track (grain + small stones)."""
    from scipy.ndimage import gaussian_filter
    rg = np.random.default_rng(seed); n = gaussian_filter(rg.normal(0, 1, (h, w)), 2.0); n2 = gaussian_filter(rg.normal(0, 1, (h, w)), 9.0)
    out = np.array([118, 88, 62.0]) * (1 + 0.10 * n / n.std() + 0.08 * n2 / n2.std())[..., None]
    st = rg.random((h, w)) > 0.996; out[st] = np.array([150, 128, 104.0]); return out + rg.normal(0, 4, out.shape)

def _paste_logo(img, box, logo_path=None):
    """white logo stretched exactly into box (x0, y0, x1, y1) of a float (h, w, 3) image (box already in texture pixels:
    the caller sizes it from the face's px / ft in u and v, so the logo is not deformed on the model)."""
    lg = logo_path if isinstance(logo_path, Image.Image) else Image.open(logo_path or FLY); x0, y0, x1, y1 = [int(round(v)) for v in box]
    a = np.array(lg.resize((x1 - x0, y1 - y0), Image.LANCZOS))[..., 3:4] / 255.0
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - a) + np.array([236, 236, 238.0]) * a

def pylon_texture():
    """512 x 1024. Rows 0..299 column side (u = angle), 300..399 base sides, 400..511 tops, 512..639 the two base sides that
    carry the Fly logo (u = along the straight side, left -> right seen from outside), 640..1023 dirt of the pad."""
    P = PYLON; img = np.zeros((1024, 512, 3))
    img[0:300] = _vinyl(300, 512, 6, 40, 1); img[300:400] = _vinyl(100, 512, 22, 6, 3, amp=10); img[400:512] = _vinyl(112, 512, 14, 14, 4, amp=6)
    img[512:640] = _vinyl(128, 512, 22, 6, 7, amp=8)
    sl = P['base_w'] - 2 * P['base_r']; yb = P['base_h'] - 0.05; pxu, pxv = 511 / sl, 112 / yb   # logo face: rows 520 (top) .. 632 (bottom)
    lh = 0.62 * yb; lw = lh * 4.43                                   # logo aspect 4.43 : 1
    _paste_logo(img, (256 - lw * pxu / 2, 576 - lh * pxv / 2, 256 + lw * pxu / 2, 576 + lh * pxv / 2))
    # v36b (user): the pad must look like the track: the track's own dirt tile (SX1 tiles/dirt.ppm, 128 px) repeated
    tile = np.asarray(Image.open(f'{ROOT}/tracks/USLAND2026SX1/tiles/dirt.ppm').convert('RGB')).astype(float)
    img[640:1024] = np.tile(tile, (3, 4, 1))
    # v36: vertical logo on the column. u = angle (512 px = 2 pi r), v rows 298 (y = top of base) .. 2 (y = H). On the cylinder
    # u grows towards the viewer's LEFT on both the +z (angle 90) and the -z (angle 270) side -> the logo is mirrored in u.
    yc = P['pad_h'] + P['base_h']; pxu = 512 / (2 * np.pi * P['cyl_r']); pxv = 296 / (P['H'] - yc)
    y0_, y1_ = P['col_logo']; L_ = y1_ - y0_; Wd = L_ / 4.43
    lg = Image.open(FLY).rotate(90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)   # reads bottom -> top, mirrored for u
    for uc in (128, 384):
        r0, r1 = 298 - (y1_ - yc) * pxv, 298 - (y0_ - yc) * pxv
        _paste_logo(img, (uc - Wd * pxu / 2, r0, uc + Wd * pxu / 2, r1), lg)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

def _rsquare(half, r, n=6):
    """rounded square outline (x, z, normal angle), 6 points per corner; the straight sides are the edges (5 -> 6) = +z side
    going +x -> -x, (11 -> 12) = -x, (17 -> 18) = -z side going -x -> +x, (23 -> 0) = +x. Axes: x east, z south (y up): seen
    from outside the +z side (looking -z) right = +x, so both logo edges run right -> left (v35 check: mirrored before)."""
    out = []
    for cx, cz, a0 in ((half - r, half - r, 0), (-(half - r), half - r, 90), (-(half - r), -(half - r), 180), (half - r, -(half - r), 270)):
        for a in np.radians(np.linspace(a0, a0 + 90, n)): out.append((cx + r * np.cos(a), cz + r * np.sin(a), a))
    return out

def pylon():
    """dirt pad, square cushion base with rounded corners (Fly logo on the +z and -z sides), round column with a well rounded
    top; origin at the ground, centre. The export turns each pylon so its +z logo faces the riding line."""
    P = PYLON; m = Mesh(512, 1024); img = pylon_texture(); sg = P['seg']; y0 = P['pad_h']
    hb, wb, rb = P['base_h'], P['base_w'] / 2, P['base_r']; r, H, f = P['cyl_r'], P['H'], P['fillet']
    # --- dirt pad: sloped sides from the ground (sunk pad_sink for slopes) to a flat top, rounded corners
    pw = P['pad_w'] / 2; pin = P['pad_in']; po = _rsquare(pw, P['pad_r']); pt = _rsquare(pw - pin, P['pad_r'] - pin * 0.6)
    duv = lambda x, z: m.uv_px(256 + x / pw * 200, 832 + z / pw * 180)
    for i in range(len(po)):
        j = (i + 1) % len(po); (xa, za, aa), (xb, zb, ab) = po[i], po[j]; (xc, zc, _), (xd, zd, _) = pt[j], pt[i]
        na = np.array([np.cos(aa), 0.5, np.sin(aa)]); nb = np.array([np.cos(ab), 0.5, np.sin(ab)])
        _smooth(m, [(xa, -P['pad_sink'], za), (xb, -P['pad_sink'], zb), (xb, 0, zb), (xa, 0, za)], [na, nb, nb, na],
                [duv(xa * 1.1, za * 1.1), duv(xb * 1.1, zb * 1.1), duv(xb, zb), duv(xa, za)])
        _smooth(m, [(xa, 0, za), (xb, 0, zb), (xc, y0, zc), (xd, y0, zd)], [na, nb, nb, na],
                [duv(xa, za), duv(xb, zb), duv(xc, zc), duv(xd, zd)])
    m.tri_fan([np.array([x, y0, z]) for x, z, _ in pt][::-1], np.array([0, 1.0, 0]), [duv(x, z) for x, z, _ in pt][::-1])
    # --- base cushion on the pad
    out = _rsquare(wb, rb); n = len(out)
    per = np.r_[0, np.cumsum([np.hypot(out[(i + 1) % n][0] - out[i][0], out[(i + 1) % n][1] - out[i][1]) for i in range(n)])]
    inset, yb = 0.05, y0 + hb - 0.05
    for i in range(n):
        j = (i + 1) % n; (xa, za, aa), (xb, zb, ab) = out[i], out[j]
        na = np.array([np.cos(aa), 0, np.sin(aa)]); nb = np.array([np.cos(ab), 0, np.sin(ab)])
        ua, ub = per[i] / per[-1], per[i + 1] / per[-1]
        if i in (5, 17):                                            # the two logo sides (+z, -z): logo strip, readable from outside
            uvs = [m.uv_px(511, 632), m.uv_px(0, 632), m.uv_px(0, 520), m.uv_px(511, 520)]   # edge runs right -> left seen from outside
        else:
            uvs = [m.uv_px(ua * 511, 399), m.uv_px(ub * 511, 399), m.uv_px(ub * 511, 302), m.uv_px(ua * 511, 302)]
        _smooth(m, [(xa, y0, za), (xb, y0, zb), (xb, yb, zb), (xa, yb, za)], [na, nb, nb, na], uvs)
        sa = 1 - inset / np.hypot(xa, za); sb = 1 - inset / np.hypot(xb, zb)
        ta, tb = na * 0.6 + np.array([0, 0.8, 0]), nb * 0.6 + np.array([0, 0.8, 0])
        _smooth(m, [(xa, yb, za), (xb, yb, zb), (xb * sb, y0 + hb, zb * sb), (xa * sa, y0 + hb, za * sa)], [na, nb, tb, ta],
                [m.uv_px(ua * 511, 302), m.uv_px(ub * 511, 302), m.uv_px(ub * 511, 300), m.uv_px(ua * 511, 300)])
    tuv = lambda x, z: m.uv_px(256 + x / wb * 120, 456 + z / wb * 50)
    top = [(x * (1 - inset / np.hypot(x, z)), z * (1 - inset / np.hypot(x, z))) for x, z, _ in out]
    m.tri_fan([np.array([x, y0 + hb, z]) for x, z in top][::-1], np.array([0, 1.0, 0]), [tuv(x, z) for x, z in top][::-1])
    # --- column, then a big quarter-round (rounder top), then a slightly domed cap
    ang = np.linspace(0, 2 * np.pi, sg + 1); yc = y0 + hb; y1 = H - f - P['dome']
    rings = [(yc - 0.02, r, 0.0), (y1, r, 0.0)]
    for t in np.linspace(0, np.pi / 2, 9)[1:]: rings.append((y1 + f * np.sin(t), r - f + f * np.cos(t), t))
    for (ya, ra, ta), (yb_, rb_, tb_) in zip(rings[:-1], rings[1:]):
        for k in range(sg):
            c0, s0, c1, s1 = np.cos(ang[k]), np.sin(ang[k]), np.cos(ang[k + 1]), np.sin(ang[k + 1])
            N = lambda c, s, t: np.array([c * np.cos(t), np.sin(t), s * np.cos(t)])
            u0, u1 = ang[k] / (2 * np.pi) * 511, ang[k + 1] / (2 * np.pi) * 511
            v = lambda y: 298 - (y - yc) / (H - yc) * 296
            _smooth(m, [(ra * c0, ya, ra * s0), (ra * c1, ya, ra * s1), (rb_ * c1, yb_, rb_ * s1), (rb_ * c0, yb_, rb_ * s0)],
                    [N(c0, s0, ta), N(c1, s1, ta), N(c1, s1, tb_), N(c0, s0, tb_)],
                    [m.uv_px(u0, v(ya)), m.uv_px(u1, v(ya)), m.uv_px(u1, v(yb_)), m.uv_px(u0, v(yb_))])
    yt, rt = rings[-1][0], rings[-1][1]
    for k in range(sg):
        c0, s0, c1, s1 = np.cos(ang[k]), np.sin(ang[k]), np.cos(ang[k + 1]), np.sin(ang[k + 1])
        _smooth(m, [(0, H, 0), (rt * c1, yt, rt * s1), (rt * c0, yt, rt * s0)],
                [np.array([0, 1.0, 0]), np.array([c1 * 0.1, 1, s1 * 0.1]), np.array([c0 * 0.1, 1, s0 * 0.1])],
                [m.uv_px(256, 456), m.uv_px(256 + c1 * 40, 456 + s1 * 40), m.uv_px(256 + c0 * 40, 456 + s0 * 40)])
    return m, img

# v35 (user: v34 "ça fait trop tomber direct" - harder to go through, it must stop you but not necessarily throw you down):
# the stopping part is LOW (wheel / engine height) and stiffer; the column above is soft and slippery (low friction) so it
# does not grab the legs / bars and flip the bike. Values not tested in game.
PY_SHP = dict(low=dict(spring=140, damping=9, friction=0.3), high=dict(spring=30, damping=1.5, friction=0.2))
# v33: 60 / 3.3 (all spheres); v32: 60 / 4; v31: 1000 / 200 (concrete block)

def pylon_shape():
    """v35: stiff low spheres (2 up the bottom of the column + 4 in the base corners) and 2 soft high ones."""
    P = PYLON; r = P['cyl_r']; y0 = P['pad_h'] + P['base_h']; rows = []
    lo, hi = PY_SHP['low'], PY_SHP['high']
    def row(x, y, z, rr, c): rows.append(f"{x:.4f} {y:.4f} {z:.4f} {rr:.3f} {c['friction']} {c['spring']} {c['damping']}")
    row(0, y0 + 0.75, 0, 0.8, lo); row(0, y0 + 1.45, 0, 0.75, lo)
    for sx in (1, -1):
        for sz in (1, -1): row(sx * 0.55, P['pad_h'] + 0.3, sz * 0.55, 0.35, lo)
    for y in (P['H'] - 1.25, P['H'] - 0.55): row(0, y, 0, r, hi)
    return '\n'.join([str(len(rows))] + rows) + '\n'

def net_ribbon(line_xz, ground, origin):
    """mesh in the statue's frame (yaw 0, origin on flat ground): a double-sided net whose bottom follows the ground under
    the line (sinks `sink` ft in) and top = ground + h, posts every `post_every` ft. line_xz: (n, 2) world points every ~1 ft;
    ground(x, z) -> height; origin (x, z) -> ground height there is the statue's y = 0."""
    m = Mesh(NETR['TW'], NETR['TH']); ox, oz = origin; g0 = ground(ox, oz)
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(line_xz, axis=0), axis=1))]
    gy = np.array([ground(x, z) for x, z in line_xz]) - g0
    # smooth the ground line a little along the net (no saw teeth from the 0.29 ft grid)
    from scipy.ndimage import gaussian_filter1d
    gy = gaussian_filter1d(gy, 1.0, mode='nearest')
    bot = gy - NETR['sink']; top = gy + NETR['h']
    NR, TH = NETR['NR'], NETR['TH']; Vb, Vt = 1 - (NR - 1) / TH, 1.0; TL = NETR['tile']
    for i in range(len(line_xz) - 1):
        A, B_ = line_xz[i] - (ox, oz), line_xz[i + 1] - (ox, oz)
        t = np.array([B_[0] - A[0], 0, B_[1] - A[1]]); n = np.cross(t, [0, 1, 0]); n /= np.linalg.norm(n) + 1e-12
        cuts = [L[i]] + [k * TL for k in range(int(L[i] // TL) + 1, int(L[i + 1] // TL) + 1) if L[i] < k * TL < L[i + 1]] + [L[i + 1]]
        for sa, sb in zip(cuts[:-1], cuts[1:]):                      # split at the tile borders: u stays in [0, 1]
            fa, fb = (sa - L[i]) / (L[i + 1] - L[i]), (sb - L[i]) / (L[i + 1] - L[i])
            pa, pb = A + (B_ - A) * fa, A + (B_ - A) * fb
            ba, bb = bot[i] + (bot[i + 1] - bot[i]) * fa, bot[i] + (bot[i + 1] - bot[i]) * fb
            ta, tb = top[i] + (top[i + 1] - top[i]) * fa, top[i] + (top[i + 1] - top[i]) * fb
            k0 = np.floor(sa / TL + 1e-9); ua, ub = sa / TL - k0, sb / TL - k0
            P = [np.array([pa[0], ba, pa[1]]), np.array([pb[0], bb, pb[1]]), np.array([pb[0], tb, pb[1]]), np.array([pa[0], ta, pa[1]])]
            uv = [(ua, Vb), (ub, Vb), (ub, Vt), (ua, Vt)]
            for sg in (1, -1):
                Q, T = (P, uv) if sg > 0 else (P[::-1], uv[::-1])
                m.tri_fan(Q, n * sg, T)
    post_uv = (0.5, 1 - (NETR['NR'] + 64) / NETR['TH'])
    for s in np.arange(0, L[-1] + 0.1, L[-1] / max(1, round(L[-1] / NETR['post_every']))):
        x_ = np.interp(s, L, line_xz[:, 0]) - ox; z_ = np.interp(s, L, line_xz[:, 1]) - oz; y_ = np.interp(s, L, gy)
        w = NETR['post_w']
        for (dx, dz, nx, nz) in ((w, 0, 1, 0), (-w, 0, -1, 0), (0, w, 0, 1), (0, -w, 0, -1)):
            ex, ez = (0, w) if dx else (w, 0)
            Q = [np.array([x_ + dx - ex, y_ - NETR['sink'], z_ + dz - ez]), np.array([x_ + dx + ex, y_ - NETR['sink'], z_ + dz + ez]),
                 np.array([x_ + dx + ex, y_ + NETR['post_h'], z_ + dz + ez]), np.array([x_ + dx - ex, y_ + NETR['post_h'], z_ + dz - ez])]
            m.tri_fan(Q, np.array([nx, 0, nz], float), [post_uv] * 4)
        m.tri_fan([np.array([x_ - w, y_ + NETR['post_h'], z_ - w]), np.array([x_ + w, y_ + NETR['post_h'], z_ - w]),
                   np.array([x_ + w, y_ + NETR['post_h'], z_ + w]), np.array([x_ - w, y_ + NETR['post_h'], z_ + w])], np.array([0, 1.0, 0]), [post_uv] * 4)
    return m


def net():
    """texture: left = solid post blue; right = net (knotted mesh, alpha) with a darker top and bottom cord."""
    W_, H_ = 512, 512
    img = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 63, H_ - 1], fill=NET['post'] + (255,))
    x0, x1, y0, y1 = 72, W_ - 8, 8, 376                      # net area (8 ft x 3.65 ft)
    cell = 9
    for x in range(x0, x1 + 1, cell): d.line([(x, y0), (x, y1)], fill=NET['net'] + (235,), width=2)
    for y in range(y0, y1 + 1, cell): d.line([(x0, y), (x1, y)], fill=NET['net'] + (235,), width=2)
    d.rectangle([x0, y0, x1, y0 + 6], fill=(14, 30, 90, 255)); d.rectangle([x0, y1 - 6, x1, y1], fill=(14, 30, 90, 255))
    m = Mesh(W_, H_); L, R = NET['L'], NET['post_r']
    pu = m.uv_px(32, 200)
    prism(m, -L / 2, 0.0, R, NET['post_h'], 8, pu, pu)
    uv = lambda x, y: m.uv_px(x0 + (x + L / 2) / L * (x1 - x0), y1 - (y - NET['y0']) / (NET['y1'] - NET['y0']) * (y1 - y0))
    P = [np.array([-L / 2, NET['y0'], 0.0]), np.array([L / 2, NET['y0'], 0.0]), np.array([L / 2, NET['y1'], 0.0]), np.array([-L / 2, NET['y1'], 0.0])]
    for sg in (1, -1):                                         # double-sided net
        Q = P if sg > 0 else P[::-1]
        m.tri_fan(Q, np.array([0, 0, sg * 1.0]), [uv(q[0], q[1]) for q in Q])
    return m, img


def floor_outline():
    """(x, z) outline of the start floor: front edge on the hinge line, cut back 0.6 ft in the middle of each gate (the gate
    leaf falls forward, the notch marks each gate box), full width of the row + `side`, `back` ft behind the gates."""
    F = LT.START_FLOOR; n = LS.N_GATES; pitch = LS.GATE_PITCH; half = (n - 1) / 2 * pitch + GATE['w'] / 2 + F['side']
    pts = [(-half, -F['back']), (half, -F['back']), (half, 0.0)]
    for k in reversed(range(n)):                                # front edge, right -> left: a notch behind each gate
        c = (k - (n - 1) / 2) * pitch; a, b = c + GATE['w'] / 2 - 0.25, c - GATE['w'] / 2 + 0.25
        pts += [(a, 0.0), (a - 0.15, -0.6), (b + 0.15, -0.6), (b, 0.0)]
    pts.append((-half, 0.0))
    return pts, half


FLOOR_TILE = dict(ft_w=7.5, ft_h=6.5625, px_ft=2048 / 7.5, cell=51.2, bar=10.5, W=2048)   # v36 (user): sharper (2048 px tile) + grip   # v34 (user): squares a quarter smaller:
# 0.25 -> 0.1875 ft (same 1024 x 896 px pattern, the tile now covers 7.5 x 6.5625 ft = 40 x 35 cells); v31: 8 x 7 ft, 32 / 7 px

def floor_texture():
    """v36: one sharp tile of square steel grating (2048 px for 7.5 x 6.5625 ft, 0.1875 ft squares), bars with a rounded
    profile, welded crossings, GRIP: serrated top edge (small teeth every ~0.02 ft) and a fine anti-slip dot pattern on the
    bars; dark holes. Rows 1792..2047: plain steel for the frame. v31-v35: 1024 px, smooth bars."""
    T = FLOOR_TILE; W_ = T['W']; th = int(round(T['ft_h'] * T['px_ft']))     # 1792 rows of pattern
    X, Y = np.meshgrid(np.arange(W_) + 0.5, np.arange(th) + 0.5)
    c, b = T['cell'], T['bar'] / 2
    dx = (X % c) - c / 2; dy = (Y % c) - c / 2
    ex, ey = c / 2 - np.abs(dx), c / 2 - np.abs(dy)
    vb, hb_ = ex <= b, ey <= b
    steel = np.array([172, 176, 181.0]); hole = np.array([30, 26, 22.0])
    img = np.zeros((th, W_, 3)) + hole
    prof_v = 0.74 + 0.36 * np.cos(ex / b * np.pi / 2) - 0.12 * np.sign(dx) * (ex / b)
    prof_h = 0.76 + 0.34 * np.cos(ey / b * np.pi / 2) - 0.12 * np.sign(dy) * (ey / b)
    tooth = 6.0                                                      # serrations along each bar (grip)
    sv = 0.86 + 0.14 * (np.abs(((Y / tooth) % 1.0) - 0.5) * 2)       # vertical bars: teeth along y
    sh_ = 0.86 + 0.14 * (np.abs(((X / tooth) % 1.0) - 0.5) * 2)      # horizontal bars: teeth along x
    img[hb_] = (steel * (prof_h * sh_)[..., None])[hb_]; img[vb] = (steel * (prof_v * sv)[..., None])[vb]
    img[vb & hb_] = steel * 1.06
    dots = ((X % 4) < 1.5) & ((Y % 4) < 1.5) & (vb | hb_) & ~(vb & hb_)
    img[dots] *= 0.82                                                # anti-slip dots
    shd = (~vb & ~hb_) & (((dx < 0) & (ex < b + 6)) | ((dy < 0) & (ey < b + 6)))
    img[shd] *= 0.55
    img += np.random.default_rng(5).normal(0, 2.5, img.shape)
    out = np.zeros((W_, W_, 3)); out[:th] = img; out[th:] = np.array([190, 193, 197.0]); out[th:th + 16] = steel
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def floor():
    """v35 (user): one grate per gate instead of one big floor: each grate is the gate pitch minus 2 squares wide (a 2-square
    gap between neighbours), `back` ft long, tiled sharp square grating + a raised steel frame. v31-v34: one big floor.
    Origin = middle of the gate row at the hinge line, local -z = backwards."""
    T = FLOOR_TILE; F = LT.START_FLOOR; L = F['back']; n = LS.N_GATES; pitch = LS.GATE_PITCH
    gap = 2 * T['cell'] / T['px_ft']; w = pitch - gap
    img = floor_texture(); m = Mesh(T['W'], T['W']); t = 0.06; fr = 0.15; y2 = t + 0.015
    ed = m.uv_px(T['W'] / 2, T['W'] - 68)
    zs = list(np.arange(0, L, T['ft_h'])) + [L]
    for k in range(n):
        c = (k - (n - 1) / 2) * pitch; xa, xb = c - w / 2, c + w / 2
        for j in range(len(zs) - 1):
            da, db = zs[j], zs[j + 1]
            u = lambda x: (x - xa) * T['px_ft']; v = lambda d: (d - zs[j]) * T['px_ft']
            Q = [(xa, -da), (xb, -da), (xb, -db), (xa, -db)]
            m.tri_fan([np.array([x, t, z]) for x, z in Q], np.array([0, 1.0, 0]), [m.uv_px(u(x), v(-z)) for x, z in Q])
        for Q in ([(xa, 0), (xb, 0), (xb, -fr), (xa, -fr)], [(xa, -L + fr), (xb, -L + fr), (xb, -L), (xa, -L)],
                  [(xa, 0), (xa + fr, 0), (xa + fr, -L), (xa, -L)], [(xb - fr, 0), (xb, 0), (xb, -L), (xb - fr, -L)]):
            m.tri_fan([np.array([x, y2, z]) for x, z in Q], np.array([0, 1.0, 0]), [ed] * 4)
        C = [(xa, 0), (xb, 0), (xb, -L), (xa, -L)]
        for q in range(4):
            (ax_, az), (bx, bz) = C[q], C[(q + 1) % 4]; e = np.array([bx - ax_, bz - az]); N = np.array([e[1], 0, -e[0]]); N /= np.linalg.norm(N)
            if np.dot(N[[0, 2]], np.array([(ax_ + bx) / 2 - c, (az + bz) / 2 + L / 2])) < 0: N = -N
            m.quad([np.array([ax_, 0, az]), np.array([bx, 0, bz]), np.array([bx, y2, bz]), np.array([ax_, y2, az])], N, lambda p: ed)
    return m, img


def floor_v28():
    F = LT.START_FLOOR; pts, half = floor_outline(); L = F['back']
    PX = 23.0                                                   # px / ft: 2 * 46.5 ft -> ~2140 px -> 2048 wide texture
    W_ = 2048; PX = (W_ - 16) / (2 * half); H_ = 1024
    img = Image.new('RGB', (W_, H_), (96, 76, 56)); d = ImageDraw.Draw(img)
    steel, hole, edge = (176, 180, 184), (66, 58, 50), (205, 208, 212)
    x0, y0 = 8, 8; x1, y1 = int(x0 + 2 * half * PX), int(y0 + L * PX)
    assert y1 < H_ - 136, 'floor runs into the palette squares'
    d.rectangle([x0, y0, x1, y1], fill=steel)
    c = 0.42 * PX; bar = max(2, int(0.07 * PX))                 # square mesh: 0.42 ft cells, bars 0.07 ft
    for xx in np.arange(x0 + bar, x1 - bar, c):
        for yy in np.arange(y0 + bar, y1 - bar, c):
            d.rectangle([xx + bar / 2, yy + bar / 2, xx + c - bar / 2, yy + c - bar / 2], fill=hole)
    P_ = [(x0 + (x + half) * PX, y0 + (-z) * PX) for x, z in pts]
    d.line(P_ + [P_[0]], fill=edge, width=int(0.25 * PX), joint='curve')
    pal = palette(img, ['steel', 'edge'], [steel, edge])
    m = Mesh(W_, H_); t = 0.06
    uv = lambda x, z: m.uv_px(x0 + (x + half) * PX, y0 + (-z) * PX)
    ed = m.uv_px(*pal['edge'][1])
    # top: convex pieces (the front edge points are collinear: ear clipping fails there): the big sheet behind the notches,
    # then the tabs between the notches along the front strip
    gates = []                                                  # (b, a) x range of each notch at the hinge line, left -> right
    for k in range(LS.N_GATES):
        c = (k - (LS.N_GATES - 1) / 2) * LS.GATE_PITCH; gates.append((c - GATE['w'] / 2 + 0.25, c + GATE['w'] / 2 - 0.25))
    pieces = [[(-half, -L), (half, -L), (half, -0.6), (-half, -0.6)]]
    xs_ = [-half] + [v for b, a in gates for v in (b, a)] + [half]
    for q in range(0, len(xs_), 2):
        l_, r_ = xs_[q], xs_[q + 1]                              # tab from the right edge of one notch to the left edge of the next
        lb = l_ - (0.15 if q > 0 else 0.0); rb = r_ + (0.15 if q < len(xs_) - 2 else 0.0)   # notches narrow towards the back
        pieces.append([(l_, 0.0), (lb, -0.6), (rb, -0.6), (r_, 0.0)])
    for pc in pieces:
        m.tri_fan([np.array([x_, t, z_]) for x_, z_ in pc], np.array([0, 1.0, 0]), [uv(x_, z_) for x_, z_ in pc])
    n = len(pts)
    for q in range(n):
        (ax_, az), (bx, bz) = pts[q], pts[(q + 1) % n]; e = np.array([bx - ax_, bz - az])
        if np.linalg.norm(e) < 1e-9: continue
        N = np.array([e[1], 0, -e[0]]); N /= np.linalg.norm(N)
        if np.dot(N[[0, 2]], np.array([(ax_ + bx) / 2, (az + bz) / 2 + L / 2])) < 0: N = -N
        m.quad([np.array([ax_, 0, az]), np.array([bx, 0, bz]), np.array([bx, t, bz]), np.array([ax_, t, az])], N, lambda p: ed)
    return m, img


GATE_BAR = 0.78   # ft above the hinge (user's drawing on the in-game top view: ~1/3 of the 2.3 ft gate)

def gate_frame():
    """v30 (user): the USLAND start gate WITHOUT its black plate (no USLAND icon): only the red round-tube frame (inverted U,
    rounded top corners) and the hinge tube - same size, hinge at the origin, laid flat like gate01 (as props_usland.gate_model)."""
    from props_usland import pipe
    img = Image.new('RGB', (256, 256), (22, 22, 24)); pal = palette(img, ['red'], [(22, 22, 24)])   # v35 (user): black tube, no more red
    m = Mesh(256, 256); w, h, r = GATE['w'], GATE['h'], GATE['r_tube']; yh = 0.0
    cr = 0.34; x0, x1, y1 = -w / 2 + r, w / 2 - r, h
    path = [(x0, yh, 0.0)]
    for t in np.radians(np.linspace(180, 90, 12)): path.append((x0 + cr + cr * np.cos(t), y1 - cr + cr * np.sin(t), 0.0))
    for t in np.radians(np.linspace(90, 0, 12)): path.append((x1 - cr + cr * np.cos(t), y1 - cr + cr * np.sin(t), 0.0))
    path.append((x1, yh, 0.0))
    pipe(m, path, r, pal['red'], closed=False, seg=12)
    pipe(m, [(-GATE['pitch'] / 2, yh, 0.0), (GATE['pitch'] / 2, yh, 0.0)], r * 1.15, pal['red'], seg=12)
    yb_ = GATE_BAR                                                   # v36 (user's mark): cross tube a third of the way up
    pipe(m, [(x0, yb_, 0.0), (x1, yb_, 0.0)], r, pal['red'], seg=12)
    for i, v in enumerate(m.V):                                     # laid flat towards +z (same as the USLAND gate)
        m.V[i] = (v[0], -v[2], v[1], v[3], -v[5], v[4], v[6], v[7])
    return m, img


# ------------------------------------------------------------------ v35: straw bale (user: white, rounded edges, hay texture)
BALE = dict(L=4.6, W=1.75, H=1.6, r=0.3, sink=0.22, px=128)   # v36 (user): a bit smaller (v35: 5.5 x 2.0 x 1.85)
BALE_SHP = dict(r=0.9, every=1.0, spring=150, damping=8, friction=0.6)    # firm: stops you, not a wall (not tested in game)

def _axis_coords(h, r, k_in, k_band=5):
    """1-D vertex coordinates from -h to h: dense in the rounded bands, sparse in the flat middle."""
    band = np.linspace(-h, -h + r, k_band)
    mid = np.linspace(-h + r, h - r, k_in)[1:-1]
    return np.r_[band, mid, -band[::-1]]

def _rounded_box(m, hx, hy, hz, r, cy, faces, k_in=6):
    """rounded box centred at (0, cy, 0): every face is a grid on the outer box, each vertex pushed onto the rounded surface
    (inner box + r along the local normal), smooth normals. faces: {(axis, sign): uvf(q) -> (u, v)} with q the point on the
    outer box (planar mapping per face); missing faces are not built."""
    hs = np.array([hx, hy, hz]); inner = hs - r
    for (ax, sg), uvf in faces.items():
        a1, a2 = [k for k in range(3) if k != ax]
        c1 = _axis_coords(hs[a1], r, k_in); c2 = _axis_coords(hs[a2], r, k_in)
        G = np.zeros((len(c1), len(c2), 3)); N = np.zeros_like(G); UV = np.zeros((len(c1), len(c2), 2))
        for i, x1 in enumerate(c1):
            for j, x2 in enumerate(c2):
                q = np.zeros(3); q[ax] = sg * hs[ax]; q[a1] = x1; q[a2] = x2
                p = np.clip(q, -inner, inner); d = q - p; n = d / np.linalg.norm(d)
                G[i, j] = p + n * r + np.array([0, cy, 0]); N[i, j] = n; UV[i, j] = uvf(q)
        for i in range(len(c1) - 1):
            for j in range(len(c2) - 1):
                idx = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
                _smooth(m, [G[a] for a in idx], [N[a] for a in idx], [tuple(UV[a]) for a in idx])

def _hay(h, w, seed, along=0.0):
    """white straw: cream base, thousands of short fibres mostly along `along` (radians, image axes), lighter and darker
    strands, a little yellow; reads as packed hay up close and as a white bale from far."""
    from scipy.ndimage import gaussian_filter
    rg = np.random.default_rng(seed)
    base = np.array([236, 232, 212.0]) * (1 + 0.05 * gaussian_filter(rg.normal(0, 1, (h, w)), 6)[..., None] / 0.1)
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    cols = [(248, 244, 228), (236, 228, 196), (204, 192, 150), (188, 172, 124), (230, 214, 160), (170, 156, 116)]
    for _ in range(int(h * w / 30)):
        x, y = rg.random() * w, rg.random() * h; a = along + rg.normal(0, 0.45); L = rg.uniform(6, 26)
        c = cols[rg.integers(len(cols))]
        d.line([(x, y), (x + L * np.cos(a), y + L * np.sin(a))], fill=c, width=int(rg.integers(1, 3)))
    out = np.array(im).astype(float)
    out += gaussian_filter(rg.normal(0, 1, (h, w)), 1.2)[..., None] * 10
    return out

def _wrap(h, w, seed):
    """v36 (user: 'du foin empaillé, on ne doit pas voir le foin'): white wrap, white on white, soft crumpled shadows and a few
    creases, slightly cool shadows."""
    from scipy.ndimage import gaussian_filter
    rg = np.random.default_rng(seed)
    big = gaussian_filter(rg.normal(0, 1, (h, w)), 18); big /= big.std() + 1e-9
    mid = gaussian_filter(rg.normal(0, 1, (h, w)), 6); mid /= mid.std() + 1e-9
    cr = gaussian_filter(rg.normal(0, 1, (h, w)), (3, 9)); cr = np.exp(-(cr / (cr.std() * 0.18)) ** 2)   # thin creases
    v = 1.0 - 0.035 * np.abs(big) - 0.025 * mid - 0.07 * cr
    out = np.dstack([243 * v, 243 * v, 246 * v + 2])
    return out + rg.normal(0, 1.2, out.shape)

def bale_texture():
    """1024 x 1024 atlas at `px` px / ft: top (L x W) rows 0.., sides +z / -z, ends (W x H); white crumpled wrap."""
    B = BALE; px = B['px']; img = np.zeros((1024, 1024, 3)) + 240.0
    Lp, Wp, Hp = int(B['L'] * px), int(B['W'] * px), int(B['H'] * px)
    img[0:Wp, 0:Lp] = _wrap(Wp, Lp, 31)
    img[264:264 + Hp, 0:Lp] = _wrap(Hp, Lp, 32); img[510:510 + Hp, 0:Lp] = _wrap(Hp, Lp, 33)
    img[756:756 + Hp, 0:Wp] = _wrap(Hp, Wp, 34); img[756:756 + Hp, 280:280 + Wp] = _wrap(Hp, Wp, 35)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

def bale():
    """rounded straw bale, long axis = local x, bottom sunk `sink` ft; origin at the ground, centre."""
    B = BALE; m = Mesh(1024, 1024); img = bale_texture(); px = B['px']; hx, hy, hz = B['L'] / 2, B['H'] / 2, B['W'] / 2
    cy = hy - B['sink']
    fx = lambda q: (q[0] + hx) * px; fz = lambda q: (q[2] + hz) * px; fy = lambda q: (hy - q[1]) * px
    faces = {(1, 1): lambda q: m.uv_px(fx(q), fz(q)), (1, -1): lambda q: m.uv_px(fx(q), fz(q)),
             (2, 1): lambda q: m.uv_px(B['L'] * px - fx(q), 264 + fy(q)),   # seen from +z: right = -x
             (2, -1): lambda q: m.uv_px(fx(q), 510 + fy(q)),
             (0, 1): lambda q: m.uv_px(fz(q), 756 + fy(q)),
             (0, -1): lambda q: m.uv_px(280 + B['W'] * px - fz(q), 756 + fy(q))}
    _rounded_box(m, hx, hy, hz, B['r'], cy, faces)
    return m, img

def bale_shape():
    B, C = BALE, BALE_SHP; rows = []
    for x in np.arange(-B['L'] / 2 + C['r'], B['L'] / 2 - C['r'] + 1e-6, C['every']):
        rows.append(f"{x:.4f} {C['r'] - B['sink'] + 0.05:.4f} 0 {C['r']} {C['friction']} {C['spring']} {C['damping']}")
    return '\n'.join([str(len(rows))] + rows) + '\n'


# ------------------------------------------------------------------ v35: black foam tube ("boudin", user's photo)
# segments lying on the ground: vertical sides then a half-round top (like the photo), flat ends with a rounded edge,
# white Fly Racing logo on both sides. A bit lower than a whoop (whoops 3.0 ft high here).
BOUDIN = dict(L=6.0, W=2.4, H=2.3, sink=0.1, gap=0.15, seg=20)
BOUDIN_SHP = dict(r=1.1, every=1.0, spring=150, damping=8, friction=0.6)

def boudin_texture(logo=True):
    """1024 x 1024: rows 0..255 side +z (vertical part, u = along, left -> right as read from outside), 256..511 side -z,
    512..1023 vinyl for the round top and the ends."""
    B = BOUDIN; img = np.zeros((1024, 1024, 3))
    img[0:256] = _vinyl(256, 1024, 60, 14, 41, amp=4); img[256:512] = _vinyl(256, 1024, 60, 14, 42, amp=4)   # smooth vinyl (photo)
    img[512:1024] = _vinyl(512, 1024, 60, 30, 43, amp=4)
    ys = B['H'] - B['W'] / 2; pxu, pxv = 1024 / B['L'], 255 / (ys + B['sink'])
    lh = 0.55 * ys; lw = lh * 4.43
    for r0 in ((0, 256) if logo else ()):
        cy = r0 + 255 - (B['sink'] + ys * 0.52) * pxv
        _paste_logo(img, (512 - lw * pxu / 2, cy - lh * pxv / 2, 512 + lw * pxu / 2, cy + lh * pxv / 2))
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

def boudin(plain=False):
    """one segment, long axis = local x (length L - gap), origin at the ground, centre. plain (v36, freestyle gap): no logo and
    no gap, the segments touch."""
    B = BOUDIN; m = Mesh(1024, 1024); img = boudin_texture(not plain); hx = (B['L'] - (0.0 if plain else B['gap'])) / 2; R = B['W'] / 2; ys = B['H'] - R
    y_b = -B['sink']; sg = B['seg']
    # cross-section (z, y, normal) from the +z foot, up the side, over the top, down to the -z foot
    sec = [(R, y_b, (0, 0, 1)), (R, ys, (0, 0, 1))]
    for t in np.linspace(0, np.pi, sg + 1)[1:-1]: sec.append((R * np.cos(t), ys + R * np.sin(t), (0, np.sin(t), np.cos(t))))
    sec += [(-R, ys, (0, 0, -1)), (-R, y_b, (0, 0, -1))]
    pxu = 1024 / B['L']; pxv = 255 / (ys + B['sink'])
    xs = np.linspace(-hx, hx, 7)
    for k in range(len(sec) - 1):
        (za, ya, na), (zb, yb, nb) = sec[k], sec[k + 1]
        for i in range(len(xs) - 1):
            xa, xb = xs[i], xs[i + 1]
            if k == 0:                                               # +z side: seen from +z (looking -z), right = +x
                uv = [m.uv_px((xa + B['L'] / 2) * pxu, 255 - (ya - y_b) * pxv), m.uv_px((xb + B['L'] / 2) * pxu, 255 - (ya - y_b) * pxv),
                      m.uv_px((xb + B['L'] / 2) * pxu, 255 - (yb - y_b) * pxv), m.uv_px((xa + B['L'] / 2) * pxu, 255 - (yb - y_b) * pxv)]
            elif k == len(sec) - 2:                                  # -z side, going down: seen from -z (looking +z), right = -x
                uv = [m.uv_px((B['L'] / 2 - xa) * pxu, 511 - (ya - y_b) * pxv), m.uv_px((B['L'] / 2 - xb) * pxu, 511 - (ya - y_b) * pxv),
                      m.uv_px((B['L'] / 2 - xb) * pxu, 511 - (yb - y_b) * pxv), m.uv_px((B['L'] / 2 - xa) * pxu, 511 - (yb - y_b) * pxv)]
            else:
                va, vb = 520 + k / len(sec) * 480, 520 + (k + 1) / len(sec) * 480
                uv = [m.uv_px((xa + B['L'] / 2) * pxu, va), m.uv_px((xb + B['L'] / 2) * pxu, va), m.uv_px((xb + B['L'] / 2) * pxu, vb), m.uv_px((xa + B['L'] / 2) * pxu, vb)]
            _smooth(m, [(xa, ya, za), (xb, ya, za), (xb, yb, zb), (xa, yb, zb)], [na, na, nb, nb], uv)
    # ends: flat caps
    for sx in (1, -1):
        ring_o = [(sx * hx, y, z) for z, y, _ in sec]
        cuv = lambda y, z: m.uv_px(512 + z / R * 200, 760 - (y - ys) / R * 200)
        m.tri_fan([np.array(p) for p in ring_o], np.array([sx * 1.0, 0, 0]), [cuv(p[1], p[2]) for p in ring_o])
    return m, img

def boudin_plain():
    return boudin(plain=True)

def boudin_shape():
    B, C = BOUDIN, BOUDIN_SHP; hx = (B['L'] - B['gap']) / 2; rows = []
    for x in np.arange(-hx + C['r'] * 0.6, hx - C['r'] * 0.6 + 1e-6, C['every']):
        rows.append(f"{x:.4f} {C['r'] - B['sink'] + 0.05:.4f} 0 {C['r']} {C['friction']} {C['spring']} {C['damping']}")
    return '\n'.join([str(len(rows))] + rows) + '\n'


def build(outd=OUTD):
    os.makedirs(outd, exist_ok=True); out = {}
    for name, fn, mat in (('start_gate_frame', gate_frame, (16, 1, 0.35, 0.35, 0.35)), ('stake_yellow', stake, (8, 0.4, 1, 1, 1)), ('net_blue', net, (0, 0, 0, 0, 0)),
                          ('start_floor', floor, (24, 0.6, 1, 1, 1)), ('pylon_black', pylon, (20, 0.5, 0.4, 0.4, 0.4)),
                          ('bale_straw', bale, (0, 0, 0, 0, 0)), ('boudin_black', boudin, (24, 0.5, 0.4, 0.4, 0.4)),
                          ('boudin_plain', boudin_plain, (24, 0.5, 0.4, 0.4, 0.4))):
        m, img = fn(); nv, nt = m.write(f'{outd}/{name}.jm', mat); img.save(f'{outd}/{name}.png')
        V = np.array([v[:3] for v in m.V]); out[name] = (nv, nt, V.min(0).round(2).tolist(), V.max(0).round(2).tolist())
    net_ribbon_texture().save(f'{outd}/net_ribbon.png')
    open(f'{outd}/pylon_black.shp', 'w', newline='\n').write(pylon_shape())
    open(f'{outd}/bale_straw.shp', 'w', newline='\n').write(bale_shape())
    open(f'{outd}/boudin_black.shp', 'w', newline='\n').write(boudin_shape())
    open(f'{outd}/boudin_plain.shp', 'w', newline='\n').write(boudin_shape())
    return out


if __name__ == '__main__':
    for k, v in build().items(): print(k, v)
