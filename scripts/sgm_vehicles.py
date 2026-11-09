"""SGM yard vehicles, made from scratch with props_usland.Mesh (doc 12 rules: 1 unit = 1 ft, y up, one texture per model,
baked shades, matte, real proportions, flat glass panes in black frames, text never mirrored).

tractor_tank.jm / .png / .shp : the track's watering rig. A generic farm tractor (no brand: green body, light grey rims,
  5.5 ft rear tyres, 3.3 ft front tyres, glass cab with a black roof, exhaust stack, front weights) towing a galvanised
  water tanker (13 ft x 5 ft tank on a single axle, top manhole, rear ladder, rear spray bar, A-frame drawbar on the
  tractor's pick-up hitch, PTO shaft to the vacuum pump). ~31 ft long.
fire_van.jm / .png / .shp : small French fire-brigade van, Ducato-like high-roof shape (no badge): red body, white band,
  POMPIERS on both sides and the back (readable), blue light bar, dark glass, black bumpers, silver hubs, rear doors with
  red / white chevrons. 19.5 x 6.7 x 8.5 ft.

Conventions (both models): origin on the ground at the centre of the footprint, length along local +x, FRONT = +x.
Collision .shp: "x y z radius friction spring damping" spheres filling the volume (solid: 1.0 400 40).
Run: python scripts/sgm_vehicles.py   -> assets/props/ + ../apercus_sgm/vehicles_3d.png (software preview, NOT a game render)"""
import os, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.ndimage import gaussian_filter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
from props_usland import Mesh, palette, pipe, rim_face, tread_strip, OUTD

TW = 2048
FONT_B = 'C:/Windows/Fonts/arialbd.ttf'
MATTE = (0, 0, 0, 0, 0)
SOLID = (1.0, 400, 40)          # collision: friction, spring, damping (stops a bike, not rideable)


def retry(fn, *a, **k):
    """Windows sometimes fails a write with errno 22: retry a few times."""
    for t in range(8):
        try: return fn(*a, **k)
        except OSError as e:
            if getattr(e, 'errno', None) != 22 or t == 7: raise
            time.sleep(0.4)


def font(sz):
    for p in (FONT_B, 'C:/Windows/Fonts/arial.ttf'):
        try: return ImageFont.truetype(p, int(sz))
        except OSError: pass
    return ImageFont.load_default(size=int(sz))


def text_c(im, txt, cx, cy, cap_px, fill):
    """text centred on (cx, cy), capital height cap_px (pixels), drawn the right way round."""
    f = font(cap_px * 1.4); l, t, r, b = f.getbbox('H'); f = font(cap_px * 1.4 * cap_px / (b - t))
    l, t, r, b = f.getbbox(txt)
    ImageDraw.Draw(im).text((cx - (l + r) / 2, cy - (t + b) / 2), txt, font=f, fill=fill)


# ------------------------------------------------------------------ geometry helpers
def newell(P):
    n = np.zeros(3)
    for i in range(len(P)): n += np.cross(P[i], P[(i + 1) % len(P)])
    return n


def sfan(m, P, Ns, UV, Nf=None):
    """convex polygon with per-vertex normals; Nf = face normal (outside, used for the winding and the baked shade)."""
    P = [np.asarray(p, float) for p in P]; Ns = [np.asarray(n, float) for n in Ns]; UV = list(UV)
    keep = [i for i in range(len(P)) if np.linalg.norm(P[i] - P[(i + 1) % len(P)]) > 1e-7]
    if len(keep) < 3: return
    P, Ns, UV = [P[i] for i in keep], [Ns[i] for i in keep], [UV[i] for i in keep]
    Nf = np.sum(Ns, 0) if Nf is None else np.asarray(Nf, float); Nf = Nf / (np.linalg.norm(Nf) + 1e-12)
    UV = m._shade(UV, np.array(P), Nf)
    if np.dot(newell(P), Nf) < 0: P, Ns, UV = P[::-1], Ns[::-1], UV[::-1]
    a = len(m.V)
    for p, n, t in zip(P, Ns, UV):
        n = n / (np.linalg.norm(n) + 1e-12); m.V.append((*p, *n, *t))
    for k in range(1, len(P) - 1): m.I += [a, a + k, a + k + 1]


def rsec(y0, y1, wb, wt, rt, rb, nc=4):
    """rounded section in the (z, y) plane, counter-clockwise (z first): half width wb at the bottom, wt at the top."""
    out = []
    for cz, cy, r, a0 in ((wb - rb, y0 + rb, rb, -90), (wt - rt, y1 - rt, rt, 0), (-(wt - rt), y1 - rt, rt, 90), (-(wb - rb), y0 + rb, rb, 180)):
        for a in np.radians(np.linspace(a0, a0 + 90, nc + 1)): out.append((cz + r * np.cos(a), cy + r * np.sin(a)))
    return out


def loft_x(m, X, secf, uvf, nc=4, cap_front=None, cap_back=None, crease=0.8):
    """body lofted along +x through rounded sections secf(x) -> (y0, y1, wb, wt, rt, rb). uvf(p, Nface, (nz, ny) of the
    section edge) -> uv. Smooth normals inside the crease angle. Caps: uv functions of the point (flat polygons)."""
    X = sorted(X); G = [np.array([(x, y, z) for z, y in rsec(*secf(x), nc=nc)]) for x in X]; npt = len(G[0])
    F = {}
    for i in range(len(X) - 1):
        for k in range(npt):
            k1 = (k + 1) % npt; P = [G[i][k], G[i + 1][k], G[i + 1][k1], G[i][k1]]
            N = np.cross(P[2] - P[0], P[3] - P[1]); L = np.linalg.norm(N)
            if L > 1e-9: F[(i, k)] = (P, N / L)
    def vn(i, k, N):
        acc = np.zeros(3)
        for fi in (i - 1, i):
            for fk in ((k - 1) % npt, k):
                f = F.get((fi, fk))
                if f is not None and np.dot(f[1], N) > crease: acc += f[1]
        return acc if np.linalg.norm(acc) > 1e-9 else N
    for (i, k), (P, N) in F.items():
        k1 = (k + 1) % npt; idx = [(i, k), (i + 1, k), (i + 1, k1), (i, k1)]
        a, b = (G[i][k] + G[i + 1][k]) / 2, (G[i][k1] + G[i + 1][k1]) / 2
        en = np.array([b[1] - a[1], -(b[2] - a[2])]); en /= (np.linalg.norm(en) + 1e-12)     # (nz, ny) of the edge
        sfan(m, P, [vn(ii, kk, N) for ii, kk in idx], [uvf(p, N, en) for p in P], N)
    for sec, f, nx in ((G[-1], cap_front, 1.0), (G[0], cap_back, -1.0)):
        if f is None: continue
        N = np.array([nx, 0, 0]); sfan(m, list(sec), [N] * len(sec), [f(p) for p in sec], N)


def revolve(m, c, axis, prof, seg, uvf, crease=0.75, e1=None):
    """surface of revolution: prof = [(h, r)] along `axis` (silhouette from the bottom axis point to the top one, so the
    normals point out); uvf(segment j, profile point i, k around) -> uv."""
    a = np.asarray(axis, float); a /= np.linalg.norm(a)
    if e1 is None: e1 = np.array([0, 1.0, 0]) if abs(a[1]) < 0.9 else np.array([0, 0, 1.0])
    e1 = e1 - a * np.dot(a, e1); e1 /= np.linalg.norm(e1); e2 = np.cross(a, e1); c = np.asarray(c, float); n = len(prof)
    sn = []
    for j in range(n - 1):
        dh, dr = prof[j + 1][0] - prof[j][0], prof[j + 1][1] - prof[j][1]; sn.append(np.array([-dr, dh]) / np.hypot(dh, dr))
    ang = np.linspace(0, 2 * np.pi, seg + 1)
    P = lambda i, t: c + a * prof[i][0] + prof[i][1] * (np.cos(t) * e1 + np.sin(t) * e2)
    Nv = lambda q, t: a * q[0] + q[1] * (np.cos(t) * e1 + np.sin(t) * e2)
    for j in range(n - 1):
        ends = []
        for nb in (j - 1, j + 1):
            v = sn[j].copy()
            if 0 <= nb < n - 1 and np.dot(sn[nb], sn[j]) > crease: v = sn[j] + sn[nb]
            ends.append(v / np.linalg.norm(v))
        for k in range(seg):
            t0, t1 = ang[k], ang[k + 1]
            sfan(m, [P(j, t0), P(j, t1), P(j + 1, t1), P(j + 1, t0)],
                 [Nv(ends[0], t0), Nv(ends[0], t1), Nv(ends[1], t1), Nv(ends[1], t0)],
                 [uvf(j, j, k), uvf(j, j, k + 1), uvf(j, j + 1, k + 1), uvf(j, j + 1, k)], Nv(sn[j], (t0 + t1) / 2))


def solid(m, src):
    uv = m.uv_px(*src[1]); return lambda *a: uv


def arc_shell(m, c, r0, r1, z0, z1, a0, a1, n, src):
    """curved plate around the z axis (mudguard): centre c = (x, y), radii r0 < r1, angles a0 -> a1 (deg, from +x to +y)."""
    g = solid(m, src); A = np.radians(np.linspace(a0, a1, n + 1)); cx, cy = c
    p = lambda r, a, z: np.array([cx + r * np.cos(a), cy + r * np.sin(a), z])
    for k in range(n):
        a, b = A[k], A[k + 1]; md = (a + b) / 2; rad = np.array([np.cos(md), np.sin(md), 0])
        m.quad([p(r1, a, z0), p(r1, b, z0), p(r1, b, z1), p(r1, a, z1)], rad, g)
        m.quad([p(r0, a, z0), p(r0, b, z0), p(r0, b, z1), p(r0, a, z1)], -rad, g)
        m.quad([p(r0, a, z1), p(r0, b, z1), p(r1, b, z1), p(r1, a, z1)], (0, 0, 1), g)
        m.quad([p(r0, a, z0), p(r0, b, z0), p(r1, b, z0), p(r1, a, z0)], (0, 0, -1), g)
    for a, s in ((A[0], -1), (A[-1], 1)):
        m.quad([p(r0, a, z0), p(r1, a, z0), p(r1, a, z1), p(r0, a, z1)], s * np.array([-np.sin(a), np.cos(a), 0]), g)


def pane(m, bl, br, tr, tl, rect, e=1.0):
    """flat glass pane, corners as seen from outside (bottom-left, bottom-right, top-right, top-left)."""
    x0, y0, x1, y1 = rect; P = [np.asarray(q, float) for q in (bl, br, tr, tl)]; N = newell(P); N /= np.linalg.norm(N)
    m.tri_fan(P, N, [m.uv_px(x0 + e, y1 - e), m.uv_px(x1 - e, y1 - e), m.uv_px(x1 - e, y0 + e), m.uv_px(x0 + e, y0 + e)])


def solid_wheel(m, c, R, w, tread_rect, rim_rect, side_src, seg=24):
    """closed tyre + rim turning about z, every face wound counter-clockwise seen from outside (the game culls back faces).
    v32 fix: props_usland Mesh.wheel flips its two SIDEWALLS inwards (its 'point away from the axis' test is wrong for an
    axial normal), so in game both sidewalls were culled and the tyres looked hollow. Here the outward normal comes from
    the profile direction: the ring goes outer-rim (+o side) -> over the tread -> inner-rim (-o side), so the outward
    normal of a segment (dr, do) is (-do, dr) in (radial, axial). Closed by a dished rim disc on both sides."""
    c = np.asarray(c, float); ax = np.array([0, 0, 1.0]); u_ = np.array([0, 1.0, 0]); v_ = np.cross(ax, u_)
    Rr = R * 0.64; h = w / 2
    ring = [(Rr * 0.97, h - 0.10), (Rr, h - 0.02), (R - 0.16, h), (R - 0.04, h - 0.09), (R, h - 0.24),
            (R, -h + 0.24), (R - 0.04, -h + 0.09), (R - 0.16, -h), (Rr, -h + 0.02), (Rr * 0.97, -h + 0.10)]
    ang = np.linspace(0, 2 * np.pi, seg + 1); dirn = lambda t: np.cos(t) * u_ + np.sin(t) * v_
    sc = m.uv_px(*side_src[1]); tx0, ty0, tx1, ty1 = tread_rect
    for i in range(len(ring) - 1):
        (ra, oa), (rb, ob) = ring[i], ring[i + 1]; n2 = np.array([-(ob - oa), rb - ra]); n2 /= np.linalg.norm(n2)
        tread = (ra == R and rb == R)
        for k in range(seg):
            t0, t1 = ang[k], ang[k + 1]
            pts = [c + dirn(t0) * ra + ax * oa, c + dirn(t1) * ra + ax * oa, c + dirn(t1) * rb + ax * ob, c + dirn(t0) * rb + ax * ob]
            ns = [dirn(t) * n2[0] + ax * n2[1] for t in (t0, t1, t1, t0)]
            if tread:
                uvs = [m.uv_px(tx0 + (tx1 - tx0) * s, ty0 + (ty1 - ty0) * (h - o) / w) for s, o in
                       ((k / seg, oa), ((k + 1) / seg, oa), ((k + 1) / seg, ob), (k / seg, ob))]
            else: uvs = [sc] * 4
            sfan(m, pts, ns, uvs, dirn((t0 + t1) / 2) * n2[0] + ax * n2[1])
    px0, py0, px1, py1 = rim_rect
    for sg in (1, -1):                                                         # dished rim discs, outer and inner
        o = sg * (h - 0.10); ctr = c + ax * (o - sg * 0.12)
        rimp = [c + dirn(t) * Rr * 0.97 + ax * o for t in ang[:-1]]
        uvs = [m.uv_px((px0 + px1) / 2 + np.cos(t) * (px1 - px0) / 2 * sg, (py0 + py1) / 2 - np.sin(t) * (py1 - py0) / 2) for t in ang[:-1]]
        cuv = m.uv_px((px0 + px1) / 2, (py0 + py1) / 2)
        for k in range(seg):
            j = (k + 1) % seg; sfan(m, [ctr, rimp[k], rimp[j]], [ax * sg] * 3, [cuv, uvs[k], uvs[j]], ax * sg)


def hub(m, c, s, prof, src, seg=10):
    """hub cap on the outer face of a wheel turning about z; s = +1 / -1 side; prof = [(h, r)] from the wheel centre."""
    revolve(m, c, (0, 0, s), prof, seg, solid(m, src))


def shift(m, dx, dz):
    m.V = [(v[0] + dx, v[1], v[2] + dz) + tuple(v[3:]) for v in m.V]


def write_shp(path, spheres):
    rows = [str(len(spheres))] + [f'{x:.3f} {y:.3f} {z:.3f} {r:.3f} {SOLID[0]:g} {SOLID[1]:g} {SOLID[2]:g}' for x, y, z, r in spheres]
    retry(lambda: open(path, 'w', newline='\n').write('\n'.join(rows) + '\n'))


# ------------------------------------------------------------------ 2D helpers
def grad_poly(im, poly, top, bot, streak=True):
    """fill a polygon with a vertical gradient (tinted glass), plus a soft diagonal sky reflection."""
    W, H = im.size; mk = Image.new('L', (W, H), 0); ImageDraw.Draw(mk).polygon([tuple(map(float, p)) for p in poly], fill=255)
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]; x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    yy, xx = np.mgrid[:H, :W].astype(np.float32)
    t = np.clip((yy - y0) / max(1, y1 - y0), 0, 1)[..., None]
    g = np.array(top, np.float32) * (1 - t) + np.array(bot, np.float32) * t
    if streak:
        u = (xx - x0) / max(1, x1 - x0); v = (yy - y0) / max(1, y1 - y0); q = u * 0.55 + v
        g *= (1 + 0.30 * np.exp(-((q - 0.45) / 0.07) ** 2) + 0.15 * np.exp(-((q - 0.68) / 0.03) ** 2))[..., None]
    im.paste(Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)), (0, 0), mk)


def ao_rows(im, amount=0.20, top=0.04):
    """baked light: the lower part of a face darkens towards the ground, a hint of light on the top edge."""
    a = np.asarray(im).astype(np.float32); t = np.linspace(0, 1, a.shape[0])[:, None, None]
    k = 1 - amount * np.clip((t - 0.5) / 0.5, 0, 1) ** 1.4 + top * np.clip((0.12 - t) / 0.12, 0, 1)
    return Image.fromarray(np.clip(a * k, 0, 255).astype(np.uint8))


def grain(img, rect, amp=3.0, seed=1):
    x0, y0, x1, y1 = rect; a = np.asarray(img.crop(rect)).astype(np.float32)
    a += np.random.default_rng(seed).normal(0, amp, a.shape[:2])[..., None]
    img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), (x0, y0))


def lug_strip(img, rect, n, seed=3):
    """agricultural tyre tread unrolled (u around, v across): staggered chevron lugs, a little dried mud."""
    x0, y0, x1, y1 = rect; S = 2; W, H = (x1 - x0) * S, (y1 - y0) * S
    im = Image.new('RGB', (W, H), (17, 17, 18)); d = ImageDraw.Draw(im); p = W / n
    for k in range(n):
        for o in (-W, 0, W):
            u = o + k * p
            d.polygon([(u, 0), (u + 0.42 * p, 0), (u + 1.05 * p, 0.57 * H), (u + 0.63 * p, 0.57 * H)], fill=(40, 39, 38))
            u2 = u + 0.5 * p
            d.polygon([(u2, H), (u2 + 0.42 * p, H), (u2 + 1.05 * p, 0.43 * H), (u2 + 0.63 * p, 0.43 * H)], fill=(40, 39, 38))
    rg = np.random.default_rng(seed)
    for _ in range(int(n * 6)):
        cx, cy, r = rg.uniform(0, W), rg.uniform(0, H), rg.uniform(1.5, 5) * S
        c = tuple(int(v) for v in np.array([92, 74, 56]) * rg.uniform(0.7, 1.0))
        d.ellipse([cx - r, cy - r * 0.7, cx + r, cy + r * 0.7], fill=c)
    img.paste(im.resize((x1 - x0, y1 - y0), Image.LANCZOS), (x0, y0))


def tractor_rim(img, rect, metal, dark, holes=8):
    """pressed-steel tractor rim (fills the square rect = the rim disc): lip, dished centre with oval holes, hub, bolts."""
    x0, y0, x1, y1 = rect; S = 2; W = (x1 - x0) * S; im = Image.new('RGB', (W, W), dark); d = ImageDraw.Draw(im)
    c = W / 2; R = W / 2
    ring = lambda f, col: d.ellipse([c - R * f, c - R * f, c + R * f, c + R * f], fill=col)
    lite = tuple(min(255, int(v * 1.08)) for v in metal); shad = tuple(int(v * 0.72) for v in metal)
    ring(0.99, shad); ring(0.95, lite); ring(0.86, shad); ring(0.83, metal)
    for k in range(holes):
        t = 2 * np.pi * (k + 0.5) / holes; ax, ay = np.cos(t), np.sin(t)
        pts = [(c + R * 0.60 * ax + R * (0.16 * np.cos(s) * ax - 0.09 * np.sin(s) * ay), c + R * 0.60 * ay + R * (0.16 * np.cos(s) * ay + 0.09 * np.sin(s) * ax)) for s in np.linspace(0, 2 * np.pi, 20)]
        d.polygon(pts, fill=dark)
    ring(0.40, shad); ring(0.37, tuple(int(v * 0.86) for v in metal))
    for k in range(10):
        t = 2 * np.pi * k / 10; px, py = c + np.cos(t) * R * 0.28, c + np.sin(t) * R * 0.28
        d.ellipse([px - R * 0.035, py - R * 0.035, px + R * 0.035, py + R * 0.035], fill=(60, 60, 60))
    ring(0.15, tuple(int(v * 0.62) for v in metal))
    img.paste(im.resize((x1 - x0, y1 - y0), Image.LANCZOS), (x0, y0))


# ================================================================== FIRE VAN
VAN = dict(X0=-9.75, X1=9.75, Y0=0.9, Y1=8.6, ZM=3.4, xf=6.6, xr=-6.6, R=1.12, Ra=1.45, wz=2.86, ww=0.74, sill=1.15, roof=8.15)
V_SIDE = {1: (8, 8, 1568, 624), -1: (8, 632, 1568, 1248)}     # 80 px / ft, x from rear (left of the image) on the +z side
V_REAR, V_FRONT = (1576, 8, 2040, 533), (1576, 544, 2040, 1069)
V_TREAD, V_RIM, V_WS = (8, 1260, 1032, 1330), (1040, 1260, 1296, 1516), (1304, 1260, 1560, 1516)
RED_F, SKIRT, BAND, GL_T, GL_B = (200, 20, 22), (44, 44, 46), (242, 242, 240), (64, 72, 84), (20, 24, 30)
V_TOP = [(-9.6, 8.15), (4.0, 8.15), (4.5, 7.95), (4.9, 7.5), (5.5, 7.4), (5.85, 7.2), (7.7, 4.3), (8.6, 3.95), (9.3, 3.6), (9.55, 3.35)]
V_WB = [(-9.6, 3.22), (-9.45, 3.33), (-9.2, 3.35), (8.6, 3.35), (9.2, 3.28), (9.4, 3.15), (9.5, 3.0), (9.55, 2.85)]
V_TUM = [(-9.6, 0.12), (4.0, 0.12), (4.9, 0.32), (9.55, 0.35)]
V_RT = [(-9.6, 0.5), (4.0, 0.5), (4.9, 0.4), (7.7, 0.35), (9.55, 0.3)]
POMP_SIDE = dict(x=-4.3, y=5.95, cap=1.05)                     # POMPIERS on the box sides (centre x, y, capital height ft)


def _wsx(y): return 7.7 - (y - 4.3) / 2.9 * 1.85                  # windscreen line x(y)


def van_side_img(s):
    x0, y0, x1, y1 = V_SIDE[s]; S = 2; W, H = (x1 - x0) * S, (y1 - y0) * S
    im = Image.new('RGB', (W, H), RED_F); d = ImageDraw.Draw(im)
    L, HY = VAN['X1'] - VAN['X0'], VAN['Y1'] - VAN['Y0']
    X = lambda x: (x - VAN['X0']) / L * W; Y = lambda y: (VAN['Y1'] - y) / HY * H; P = lambda pts: [(X(a), Y(b)) for a, b in pts]
    d.rectangle([0, Y(1.62), W, H], fill=SKIRT); d.line([0, Y(1.62), W, Y(1.62)], fill=(78, 78, 80), width=3)   # black plastic sill
    for xa in (VAN['xf'], VAN['xr']):                                                                 # black arch mouldings
        for r, cl in ((1.70, SKIRT), (1.46, (20, 20, 22))):
            d.ellipse([X(xa - r), Y(1.12 + r), X(xa + r), Y(1.12 - r)], fill=cl)
    d.rectangle([0, Y(3.6), W, Y(3.05)], fill=BAND)                                                    # white reflective band
    for yy in (3.6, 3.05): d.line([0, Y(yy), W, Y(yy)], fill=(160, 160, 162), width=2)
    seam = (118, 10, 12)
    d.line(P([(4.99, 1.65), (4.2, 1.65), (4.2, 7.1), (_wsx(7.1) - 0.15, 7.1), (_wsx(4.3) - 0.15, 4.3), (_wsx(4.3) - 0.15, 2.53)]), fill=seam, width=3)
    win = [(4.42, 4.85), (_wsx(4.85) - 0.42, 4.85), (_wsx(6.85) - 0.42, 6.85), (4.42, 6.85)]               # cab door glass
    d.polygon(P([(a + (0.07 if a > 4.5 else -0.07), b + (0.07 if b > 5 else -0.07)) for a, b in win]), fill=(14, 14, 16))
    grad_poly(im, P(win), GL_T, GL_B)
    for xa in (0.55, 3.95): d.line(P([(xa, 1.65), (xa, 7.5)]), fill=seam, width=3)                     # sliding door
    d.line(P([(0.55, 7.5), (3.95, 7.5)]), fill=seam, width=3)
    d.rounded_rectangle([X(0.88), Y(6.92), X(3.62), Y(5.08)], radius=14, fill=(14, 14, 16))
    grad_poly(im, P([(0.95, 5.15), (3.55, 5.15), (3.55, 6.85), (0.95, 6.85)]), (84, 90, 98), (50, 54, 60))
    for xa in (4.55, 3.35): d.rounded_rectangle([X(xa), Y(4.62), X(xa + 0.45), Y(4.47)], radius=5, fill=(26, 26, 28))
    for xa in (8.75, -9.45): d.rectangle([X(xa), Y(2.05), X(xa + 0.3), Y(1.85)], fill=(245, 140, 20))   # side markers
    d.rounded_rectangle([X(8.05), Y(2.9), X(8.35), Y(2.75)], radius=4, fill=(245, 140, 20))             # turn repeater
    if s < 0: im = ImageOps.mirror(im)
    cx = X(POMP_SIDE['x']) if s > 0 else W - X(POMP_SIDE['x'])                                         # text after the mirror
    text_c(im, 'POMPIERS', cx, Y(POMP_SIDE['y']), POMP_SIDE['cap'] / HY * H, (250, 250, 250))
    im = ao_rows(im, 0.18)
    return im.resize((x1 - x0, y1 - y0), Image.LANCZOS)


def van_rear_img():
    x0, y0, x1, y1 = V_REAR; S = 2; W, H = (x1 - x0) * S, (y1 - y0) * S; ZM = VAN['ZM']
    im = Image.new('RGB', (W, H), RED_F); d = ImageDraw.Draw(im); HY = VAN['Y1'] - VAN['Y0']
    Z = lambda z: (z + ZM) / (2 * ZM) * W; Y = lambda y: (VAN['Y1'] - y) / HY * H                  # seen from behind: right = +z
    d.rectangle([0, Y(1.9), W, H], fill=SKIRT)
    yy, xx = np.mgrid[:H, :W].astype(np.float32); zf = xx / W * 2 * ZM - ZM; yf = VAN['Y1'] - yy / H * HY  # red / white chevrons (up)
    a = np.asarray(im).copy(); m_ = (yf > 1.95) & (yf < 2.95) & (np.abs(zf) < 2.72)
    wht = (np.floor((np.abs(zf) + yf) / 0.42) % 2) == 0
    a[m_ & wht] = BAND; im = Image.fromarray(a); d = ImageDraw.Draw(im)
    d.rectangle([0, Y(3.6), W, Y(3.05)], fill=BAND)
    seam = (118, 10, 12)
    d.rectangle([Z(-3.0), Y(7.95), Z(3.0), Y(1.6)], outline=seam, width=3); d.line([Z(0), Y(7.95), Z(0), Y(1.6)], fill=seam, width=4)
    for za, zb in ((0.3, 2.6), (-2.6, -0.3)):
        d.rounded_rectangle([Z(za) - 5, Y(7.42), Z(zb) + 5, Y(5.53)], radius=12, fill=(14, 14, 16))
        grad_poly(im, [(Z(za), Y(7.35)), (Z(zb), Y(7.35)), (Z(zb), Y(5.6)), (Z(za), Y(5.6))], GL_T, GL_B)
    text_c(im, 'POMPIERS', Z(0), Y(4.6), 0.62 / HY * H, (250, 250, 250))
    for s in (-1, 1):
        za, zb = sorted((s * 2.82, s * 3.2))
        d.rectangle([Z(za), Y(3.0), Z(zb), Y(2.25)], fill=(175, 12, 14)); d.rectangle([Z(za), Y(2.25), Z(zb), Y(1.95)], fill=(240, 135, 20))
        d.rectangle([Z(za), Y(1.95), Z(zb), Y(1.62)], fill=(225, 225, 228))
        for yh in (2.3, 7.0): d.rectangle([Z(s * 3.08) - 6, Y(yh + 0.15), Z(s * 3.08) + 6, Y(yh - 0.15)], fill=(26, 26, 28))
    d.rectangle([Z(-0.45), Y(8.08), Z(0.45), Y(7.98)], fill=(175, 12, 14))
    d.rounded_rectangle([Z(0.12), Y(4.12), Z(0.5), Y(4.0)], radius=4, fill=(26, 26, 28))
    im = ao_rows(im, 0.18)
    return im.resize((x1 - x0, y1 - y0), Image.LANCZOS)


def van_front_img():
    x0, y0, x1, y1 = V_FRONT; S = 2; W, H = (x1 - x0) * S, (y1 - y0) * S; ZM = VAN['ZM']
    im = Image.new('RGB', (W, H), RED_F); d = ImageDraw.Draw(im); HY = VAN['Y1'] - VAN['Y0']
    Z = lambda z: (ZM - z) / (2 * ZM) * W; Y = lambda y: (VAN['Y1'] - y) / HY * H                  # seen from the front: right = -z
    P = lambda pts: [(Z(a), Y(b)) for a, b in pts]
    d.rectangle([0, Y(2.2), W, H], fill=SKIRT)
    d.polygon(P([(2.78, 4.22), (-2.78, 4.22), (-2.78, 7.32), (2.78, 7.32)]), fill=(16, 16, 18))           # windscreen frame
    d.polygon(P([(1.75, 3.12), (-1.75, 3.12), (-1.55, 2.25), (1.55, 2.25)]), fill=(18, 18, 20))           # grille
    for k in range(5):
        yb = 2.38 + k * 0.17; d.line(P([(1.6, yb), (-1.6, yb)]), fill=(58, 58, 62), width=4)
    for s in (-1, 1):
        (ax, ay), (bx, by) = P([(s * 1.2, 2.5), (s * 1.45, 2.38)])
        d.rectangle([min(ax, bx), min(ay, by), max(ax, bx), max(ay, by)], fill=(40, 90, 245))            # blue grille flashers
        hl = [(s * 1.85, 2.55), (s * 3.15, 2.75), (s * 3.15, 3.45), (s * 1.85, 3.25)]
        d.polygon(P(hl), fill=(150, 152, 156))
        grad_poly(im, P([(s * 1.92, 2.62), (s * 3.08, 2.8), (s * 3.08, 3.38), (s * 1.92, 3.18)]), (232, 236, 240), (178, 184, 192), streak=False)
        d = ImageDraw.Draw(im)
        for zc in (2.3, 2.75):
            cx, cy, r = Z(s * zc), Y(3.0), 0.17 / HY * H; d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(120, 124, 132))
            d.ellipse([cx - r * 0.5, cy - r * 0.5, cx + r * 0.5, cy + r * 0.5], fill=(250, 250, 250))
        d.polygon(P([(s * 2.95, 2.74), (s * 3.15, 2.77), (s * 3.15, 3.0), (s * 2.95, 2.97)]), fill=(245, 140, 20))
    im = ao_rows(im, 0.15)
    return im.resize((x1 - x0, y1 - y0), Image.LANCZOS)


def windscreen_img(rect, top=GL_T, bot=GL_B, wipers=True):
    x0, y0, x1, y1 = rect; W = (x1 - x0) * 2; im = Image.new('RGB', (W, W), (14, 14, 16))
    grad_poly(im, [(4, 4), (W - 4, 4), (W - 4, W - 4), (4, W - 4)], top, bot)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, W * 0.08], fill=tuple(int(v * 0.6) for v in top))                  # tinted strip at the top
    if wipers:
        d.line([(W * 0.12, W * 0.97), (W * 0.47, W * 0.80)], fill=(10, 10, 10), width=5)
        d.line([(W * 0.52, W * 0.97), (W * 0.88, W * 0.80)], fill=(10, 10, 10), width=5)
    return im.resize((x1 - x0, y1 - y0), Image.LANCZOS)


def van_texture():
    img = Image.new('RGB', (TW, TW), (60, 60, 62))
    for s in (1, -1): img.paste(van_side_img(s), V_SIDE[s][:2])
    img.paste(van_rear_img(), V_REAR[:2]); img.paste(van_front_img(), V_FRONT[:2]); img.paste(windscreen_img(V_WS), V_WS[:2])
    tread_strip(img, V_TREAD, blocks=40); rim_face(img, V_RIM, metal=(196, 198, 203), dark=(38, 38, 42), spokes=8)
    pal = palette(img, ['red', 'under', 'black', 'tyre', 'blue', 'white', 'silver', 'amber', 'tail', 'grey'],
                  [RED_F, (30, 30, 32), (20, 20, 22), (28, 28, 30), (35, 90, 245), (236, 236, 236), (196, 198, 203),
                   (245, 140, 20), (175, 12, 14), (120, 122, 126)])
    return img, pal


def van_secf(x):
    y1 = np.interp(x, *zip(*V_TOP)); y0 = VAN['sill']
    for xa in (VAN['xf'], VAN['xr']):
        dx = x - xa
        if abs(dx) < VAN['Ra']: y0 = max(y0, 1.12 + np.sqrt(VAN['Ra'] ** 2 - dx * dx))
    wb = np.interp(x, *zip(*V_WB)); return (y0, y1, wb, wb - np.interp(x, *zip(*V_TUM)), np.interp(x, *zip(*V_RT)), 0.18)


def van_model(pal):
    m = Mesh(TW, TW); col = lambda n: m.uv_px(*pal[n][1]); ZM = VAN['ZM']; HY = VAN['Y1'] - VAN['Y0']; L = VAN['X1'] - VAN['X0']
    def side_uv(p, s):
        x0, y0, x1, y1 = V_SIDE[s]; u = (p[0] - VAN['X0']) / L; u = u if s > 0 else 1 - u
        return m.uv_px(x0 + u * (x1 - x0), y0 + (VAN['Y1'] - p[1]) / HY * (y1 - y0))
    def fr_uv(p, rect, s):
        x0, y0, x1, y1 = rect; u = np.clip((ZM - s * p[2]) / (2 * ZM), 0, 1)
        return m.uv_px(x0 + u * (x1 - x0), y0 + np.clip((VAN['Y1'] - p[1]) / HY, 0, 1) * (y1 - y0))
    front_uv = lambda p: fr_uv(p, V_FRONT, 1); rear_uv = lambda p: fr_uv(p, V_REAR, -1)
    def body_uv(p, N, en):
        nz, ny = en
        if ny < -0.5: return col('under')
        if ny > 0.5:
            if N[0] > 0.6: return front_uv(p)
            if N[0] < -0.6: return rear_uv(p)
            return col('red')
        if N[0] > 0.75: return front_uv(p)
        if N[0] < -0.75: return rear_uv(p)
        return side_uv(p, 1 if nz > 0 else -1)
    X = set(round(x, 3) for x, _ in V_TOP + V_WB) | {-3.0, 0.5, 2.5}
    for xa in (VAN['xf'], VAN['xr']): X |= set(np.round(xa + VAN['Ra'] * np.cos(np.linspace(0, np.pi, 9)), 3))
    loft_x(m, sorted(X), van_secf, body_uv, nc=4, cap_front=front_uv, cap_back=rear_uv)
    # windscreen: flat dark pane on the flat part of the screen, inside the black frame
    n = np.array([2.9, 1.85]) / np.hypot(2.9, 1.85); o = 0.03
    pb = (_wsx(4.45) + n[0] * o, 4.45 + n[1] * o); pt = (_wsx(7.05) + n[0] * o, 7.05 + n[1] * o)
    pane(m, (pb[0], pb[1], 2.62), (pb[0], pb[1], -2.62), (pt[0], pt[1], -2.5), (pt[0], pt[1], 2.5), V_WS)
    # chassis / inner arch walls, bumpers
    m.box(-9.2, 9.1, 0.8, 2.6, -2.45, 2.45, {'*': pal['under']})
    m.rbox(9.25, 9.75, 0.95, 2.2, -3.2, 3.2, 0.22, 1, {'*': pal['black']}, pal['black'], seg=4)
    m.rbox(-9.75, -9.4, 1.0, 1.9, -3.2, 3.2, 0.15, 1, {'*': pal['black']}, pal['black'], seg=3)
    # light bar (front of the roof) + two blue beacons at the back
    m.rbox(3.0, 3.9, 8.12, 8.26, -2.3, 2.3, 0.06, 2, {'*': pal['black']}, pal['black'], seg=2)
    for s in (-1, 1):
        za, zb = sorted((s * 0.5, s * 2.2)); m.rbox(3.05, 3.85, 8.26, 8.5, za, zb, 0.1, 2, {'*': pal['blue']}, pal['blue'], seg=3)
        revolve(m, (-9.12, 8.12, s * 2.75), (0, 1, 0), [(0, 0.2), (0.08, 0.2), (0.1, 0.15), (0.3, 0.13), (0.34, 0)], 10,
                lambda j, i, k: col('black') if j < 1 else col('blue'))
    m.rbox(3.1, 3.8, 8.26, 8.46, -0.5, 0.5, 0.06, 2, {'*': pal['grey']}, pal['grey'], seg=2)
    # mirrors
    for s in (-1, 1):
        m.tube((7.05, 5.1, s * 3.15), (7.0, 5.25, s * 3.7), 0.05, pal['black'])
        za, zb = sorted((s * 3.6, s * 3.98)); m.rbox(6.88, 7.1, 4.85, 6.15, za, zb, 0.08, 0, {'*': pal['black']}, pal['black'], seg=2)
    # wheels with silver hubs
    for xa in (VAN['xf'], VAN['xr']):
        for s in (-1, 1):
            c = (xa, VAN['R'], s * VAN['wz'])
            solid_wheel(m, c, VAN['R'], VAN['ww'], V_TREAD, V_RIM, pal['tyre'], seg=20)
            hub(m, c, s, [(0.12, 0.22), (0.3, 0.22), (0.36, 0.1), (0.37, 0)], pal['silver'], seg=10)
    return m


def van_spheres():
    out = []
    for x in np.linspace(-8.4, 8.3, 8):
        y1 = np.interp(x, *zip(*V_TOP)); r = min(1.68, (y1 - VAN['sill']) / 2); lo, hi = VAN['sill'] + r, y1 - r
        ys = [lo] if hi <= lo + 0.05 else list(np.linspace(lo, hi, int(np.ceil((hi - lo) / (1.4 * r))) + 1))
        for y in ys:
            for s in (-1, 1): out.append((x, y, s * (3.35 - r), r))
    for xa in (VAN['xf'], VAN['xr']):
        for s in (-1, 1): out.append((xa, 1.1, s * 2.85, 1.0))
    return out


# ================================================================== TRACTOR + WATER TANKER
TR = dict(Rr=2.75, wr=1.6, zr=3.05, xf=8.6, Rf=1.65, wf=1.15, zf=2.9)
TK = dict(Tf=-5.3, L=16.0, yc=5.5, R=3.1, rings=(5.4, 10.6), xa=-14.6, Rw=1.8, ww=1.4, zw=3.8)   # v32 (user): bigger tank (v31 L 13, R 2.5)
DOME = [(0.0, 0.0), (0.05, 0.9), (0.15, 1.6), (0.3, 2.1), (0.45, 2.4), (0.62, 2.5)]
GREEN = (30, 30, 32)   # v32 (user): black tractor (v31 green (46, 112, 46))
TRACTOR_SCALE = 1.25   # v32 (user): the whole rig bigger
T_TREAD_R, T_TREAD_S = (8, 8, 1032, 112), (8, 120, 1032, 200)
T_RIM_R, T_RIM_S = (1040, 8, 1296, 264), (1304, 8, 1560, 264)
T_TANK, T_HOOD, T_GRILLE, T_GLASS = (8, 280, 1032, 1304), (1040, 280, 2040, 602), (1040, 612, 1340, 827), (1350, 612, 1606, 868)
H_X, H_Y, H_Z = (3.0, 10.6), (2.65, 5.0), 1.15                  # hood extent (side image / grille image)
H_TOP = [(3.0, 5.0), (10.1, 4.55), (10.4, 4.38), (10.6, 4.15)]
H_WB = [(3.0, 1.25), (10.1, 1.15), (10.45, 1.12), (10.6, 1.02)]
H_RT = [(3.0, 0.5), (10.1, 0.45), (10.6, 0.3)]


def dome():
    """dished head scaled to the tank radius TK['R'] (DOME is drawn for R = 2.5)."""
    f = TK['R'] / 2.5; return [(dd * f, r * f) for dd, r in DOME]


def dome_depth(r):
    """how far behind the tip the head surface is at radius r."""
    d = dome(); return float(np.interp(r, [q[1] for q in d], [q[0] for q in d]))


def tank_profile():
    Tb = TK['Tf'] - TK['L']; R = TK['R']; D = dome(); pr = [(Tb + dd, r) for dd, r in D]
    for rx in TK['rings']:
        x = Tb + rx; pr += [(x - 0.1, R), (x - 0.06, R + 0.06), (x + 0.06, R + 0.06), (x + 0.1, R)]
    pr += [(TK['Tf'] - dd, r) for dd, r in D[::-1]]
    s = np.concatenate([[0], np.cumsum([np.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pr[:-1], pr[1:])])])
    return pr, s / s[-1]


def tank_img():
    """galvanised steel (spangle crystals, soft mottling), weld seams and rings, baked light around the tank
    (u = angle from the top, v = along the tank), road dirt on the lower half."""
    from scipy.spatial import cKDTree
    x0, y0, x1, y1 = T_TANK; W, H = x1 - x0, y1 - y0; rg = np.random.default_rng(21)
    pts = rg.random((W * H // 260, 2)) * [W, H]; val = rg.normal(0, 1, len(pts))
    yy, xx = np.mgrid[:H, :W]; _, lab = cKDTree(pts).query(np.stack([xx.ravel(), yy.ravel()], 1))
    base = 168 + 6.5 * val[lab].reshape(H, W) + rg.normal(0, 1.6, (H, W))
    low = gaussian_filter(rg.normal(0, 1, (H, W)), 36); base += 9 * low / low.std()
    img = np.stack([base * 0.985, base, base * 1.02], -1)
    phi = np.arange(W) / W * 2 * np.pi; sh = 0.74 + 0.26 * np.cos(phi)
    dirt = np.clip((-np.cos(phi) - 0.15) / 0.85, 0, 1)[None, :, None] * np.clip(0.30 + 0.12 * low / low.std(), 0, 1)[..., None]
    img = img * (1 - dirt) + np.array([104, 88, 68]) * dirt
    pr, s = tank_profile()
    rows = [s[5], s[-6]] + [s[6 + 4 * k + j] for k in range(2) for j in (0, 3)]
    for r in rows:
        py = int(r * (H - 1)); img[max(0, py - 2):py + 2] *= 0.72; img[py + 2:py + 4] *= 1.06
    for k in range(2):                                                         # rings: slightly darker band
        a, b = int(s[6 + 4 * k] * H), int(s[9 + 4 * k] * H); img[a:b] *= 0.88
    img[:, W // 2 - 2:W // 2 + 2] *= 0.75                                     # bottom weld
    img *= sh[None, :, None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def hood_side_img():
    x0, y0, x1, y1 = T_HOOD; S = 2; W, H = (x1 - x0) * S, (y1 - y0) * S
    im = Image.new('RGB', (W, H), GREEN); d = ImageDraw.Draw(im)
    X = lambda x: (x - H_X[0]) / (H_X[1] - H_X[0]) * W; Y = lambda y: (H_Y[1] - y) / (H_Y[1] - H_Y[0]) * H
    d.rectangle([0, Y(2.82), W, H], fill=(24, 24, 26))                                     # black lower trim
    d.line([0, Y(4.38), W, Y(4.38)], fill=tuple(min(255, int(v * 1.22)) for v in GREEN), width=4)   # crease highlight
    d.line([X(4.15), Y(2.82), X(4.15), Y(4.6)], fill=(18, 18, 20), width=3)                 # panel seam
    d.rounded_rectangle([X(8.0), Y(4.2), X(10.25), Y(3.0)], radius=10, fill=(22, 24, 24))     # side vent
    for k in range(8):
        yb = 3.12 + k * 0.135; d.line([X(8.1), Y(yb), X(10.15), Y(yb + 0.04)], fill=(44, 44, 47), width=6)
    im = ao_rows(im, 0.22)
    return im.resize((x1 - x0, y1 - y0), Image.LANCZOS)


def grille_img():
    x0, y0, x1, y1 = T_GRILLE; S = 2; W, H = (x1 - x0) * S, (y1 - y0) * S
    im = Image.new('RGB', (W, H), GREEN); d = ImageDraw.Draw(im)
    Z = lambda z: (H_Z - z) / (2 * H_Z) * W; Y = lambda y: (4.2 - y) / (4.2 - H_Y[0]) * H
    d.rounded_rectangle([Z(0.86), Y(3.86), Z(-0.86), Y(2.98)], radius=12, fill=(14, 14, 15))   # honeycomb grille
    for j in range(9):
        for i in range(14):
            cx = Z(0.8) + (i + 0.5 * (j % 2)) * (Z(-0.8) - Z(0.8)) / 14; cy = Y(3.8) + j * (Y(3.04) - Y(3.8)) / 8
            d.regular_polygon((cx, cy, 6), 6, fill=(34, 34, 36))
    for s in (-1, 1):                                                                          # LED headlights
        za, zb = Z(s * 0.2), Z(s * 0.75); za, zb = min(za, zb), max(za, zb)
        d.rounded_rectangle([za, Y(4.04), zb, Y(3.88)], radius=5, fill=(150, 152, 156))
        d.rounded_rectangle([za + 3, Y(4.02), zb - 3, Y(3.9)], radius=4, fill=(240, 242, 246))
    im = ao_rows(im, 0.15)
    return im.resize((x1 - x0, y1 - y0), Image.LANCZOS)


def tractor_texture():
    img = Image.new('RGB', (TW, TW), (60, 60, 62))
    lug_strip(img, T_TREAD_R, 26); lug_strip(img, T_TREAD_S, 22, seed=5)
    tractor_rim(img, T_RIM_R, (206, 206, 200), (40, 40, 40)); tractor_rim(img, T_RIM_S, (206, 206, 200), (40, 40, 40), holes=6)
    img.paste(tank_img(), T_TANK[:2]); img.paste(hood_side_img(), T_HOOD[:2]); img.paste(grille_img(), T_GRILLE[:2])
    img.paste(windscreen_img(T_GLASS, (62, 76, 76), (22, 30, 30), wipers=False), T_GLASS[:2])
    for k, r in enumerate((T_TREAD_R, T_TREAD_S, T_TANK)): grain(img, r, 2.5, seed=k)
    pal = palette(img, ['green', 'black', 'dark', 'tyre', 'rim', 'galv', 'orange', 'red', 'lens', 'amber', 'weight', 'pipe'],
                  [GREEN, (22, 22, 24), (58, 60, 62), (30, 30, 31), (206, 206, 200), (160, 165, 168), (245, 125, 20),
                   (185, 18, 18), (232, 234, 238), (245, 150, 20), (66, 68, 70), (30, 30, 32)])
    return img, pal


def hood_secf(x):
    wb = np.interp(x, *zip(*H_WB)); return (H_Y[0], np.interp(x, *zip(*H_TOP)), wb, wb - 0.08, np.interp(x, *zip(*H_RT)), 0.1)


def tractor_model(pal):
    m = Mesh(TW, TW); P = pal; col = lambda n: m.uv_px(*P[n][1])
    # ---- hood (lofted, rounded), side panels + grille drawn at their real size
    def hood_side(p):
        x0, y0, x1, y1 = T_HOOD; u = np.clip((p[0] - H_X[0]) / (H_X[1] - H_X[0]), 0, 1)
        return m.uv_px(x0 + u * (x1 - x0), y0 + np.clip((H_Y[1] - p[1]) / (H_Y[1] - H_Y[0]), 0, 1) * (y1 - y0))
    def grille(p):
        x0, y0, x1, y1 = T_GRILLE; u = np.clip((H_Z - p[2]) / (2 * H_Z), 0, 1)
        return m.uv_px(x0 + u * (x1 - x0), y0 + np.clip((4.2 - p[1]) / (4.2 - H_Y[0]), 0, 1) * (y1 - y0))
    def hood_uv(p, N, en):
        if en[1] < -0.5: return col('dark')
        if en[1] > 0.5: return grille(p) if N[0] > 0.6 else col('green')
        return grille(p) if N[0] > 0.75 else hood_side(p)
    loft_x(m, [3.0, 4.0, 5.5, 7.0, 8.5, 9.6, 10.1, 10.25, 10.4, 10.5, 10.6], hood_secf, hood_uv, nc=3, cap_front=grille, cap_back=lambda p: col('dark'))
    # ---- under the hood: sump / engine, front axle, weight carrier + front weights
    m.rbox(3.0, 10.45, 1.8, 2.7, -0.85, 0.85, 0.15, 0, {'*': P['dark']}, P['dark'], seg=2)
    pipe(m, [(TR['xf'], TR['Rf'], -2.6), (TR['xf'], TR['Rf'], 2.6)], 0.24, P['dark'], seg=8)     # ends inside the closed wheels
    m.box(TR['xf'] - 0.5, TR['xf'] + 0.5, 1.4, 2.0, -0.55, 0.55, {'*': P['dark']})
    m.box(10.45, 10.8, 1.5, 2.7, -0.9, 0.9, {'*': P['dark']})
    for k in range(7):
        z0 = -1.25 + k * 0.36; m.rbox(10.78, 11.9, 1.45, 3.05, z0, z0 + 0.29, 0.16, 2, {'*': P['weight']}, P['weight'], seg=2)
    m.rbox(11.15, 11.6, 3.05, 3.3, -0.35, 0.35, 0.08, 2, {'*': P['weight']}, P['weight'], seg=2)
    # ---- transmission, rear axle housings, pick-up hitch, 3-point linkage, PTO
    m.rbox(-1.0, 3.0, 1.55, 4.1, -0.95, 0.95, 0.2, 2, {'*': P['dark']}, P['dark'], seg=2)
    for s in (-1, 1): pipe(m, [(0, TR['Rr'], s * 0.9), (0, TR['Rr'], s * 2.6)], 0.38, P['dark'], seg=8)
    m.box(-2.95, -1.0, 1.3, 1.65, -0.32, 0.32, {'*': P['dark']})
    for s in (-1, 1): m.tube((-0.9, 2.1, s * 0.85), (-2.55, 1.75, s * 0.75), 0.08, P['black'])
    pipe(m, [(-1.2, 4.0, 0), (-2.4, 3.7, 0)], 0.1, P['black'], seg=6)
    # ---- cab: green floor box, black posts, flat tinted panes, black roof, mirrors, lights, beacon
    m.rbox(-1.3, 3.0, 4.1, 4.85, -2.15, 2.15, 0.12, 2, {'*': P['green']}, P['green'], seg=3)
    yb, yt = 4.85, 8.95
    for xc in (-1.2, 2.9):
        for s in (-1, 1): m.box(xc - 0.12, xc + 0.12, yb, yt, s * 2.05 - 0.12, s * 2.05 + 0.12, {'*': P['black']})
    for s in (-1, 1): m.box(0.6, 0.8, yb, yt, min(s * 2.1, s * 2.2), max(s * 2.1, s * 2.2), {'*': P['black']})
    G = T_GLASS
    pane(m, (2.97, yb, 1.95), (2.97, yb, -1.95), (2.97, yt, -1.95), (2.97, yt, 1.95), G)            # front (right = -z)
    pane(m, (-1.27, yb, -1.95), (-1.27, yb, 1.95), (-1.27, yt, 1.95), (-1.27, yt, -1.95), G)        # back
    pane(m, (-1.08, yb, 2.12), (2.78, yb, 2.12), (2.78, yt, 2.12), (-1.08, yt, 2.12), G)            # +z side
    pane(m, (2.78, yb, -2.12), (-1.08, yb, -2.12), (-1.08, yt, -2.12), (2.78, yt, -2.12), G)        # -z side
    for s in (-1, 1): pipe(m, [(2.55, 5.2, s * 2.2), (2.55, 7.4, s * 2.2)], 0.04, P['black'], seg=6)   # door handrails
    m.rbox(-1.55, 3.3, 8.9, 9.45, -2.4, 2.4, 0.22, 0, {'*': P['black']}, P['black'], seg=4)
    for s in (-1, 1):
        za, zb = sorted((s * 1.15, s * 1.6))
        m.box(3.25, 3.42, 9.0, 9.3, za, zb, {'*': P['black'], '+x': P['lens']})                      # work lights
        m.box(-1.67, -1.5, 9.0, 9.3, za, zb, {'*': P['black'], '-x': P['lens']})
        m.tube((2.95, 8.3, s * 2.15), (3.12, 8.45, s * 2.85), 0.04, P['black'])                       # mirrors
        za, zb = sorted((s * 2.75, s * 3.25)); m.box(3.05, 3.2, 7.5, 8.5, za, zb, {'*': P['black']})
    revolve(m, (-0.8, 9.45, -1.7), (0, 1, 0), [(0, 0.26), (0.1, 0.26), (0.1, 0.2), (0.42, 0.2), (0.5, 0.11), (0.53, 0)], 10,
            lambda j, i, k: col('black') if j < 2 else col('orange'))
    # ---- exhaust stack (right front corner of the cab)
    ex = (3.6, 0.95)
    pipe(m, [(ex[0], 4.6, ex[1]), (ex[0], 9.85, ex[1])], 0.16, P['pipe'], seg=10)
    revolve(m, (ex[0], 5.4, ex[1]), (0, 1, 0), [(0, 0.16), (0.06, 0.28), (2.0, 0.28), (2.06, 0.16)], 12, solid(m, P['black']))
    revolve(m, (ex[0], 9.78, ex[1]), (0, 1, 0), [(0, 0.155), (0, 0)], 10, solid(m, P['black']))
    # ---- access steps (left side, ahead of the rear wheel)
    for y in (1.45, 2.4, 3.35): m.box(2.95, 3.7, y - 0.05, y + 0.05, -2.62, -2.02, {'*': P['black']})
    for xs in (2.95, 3.6): m.box(xs, xs + 0.1, 1.3, 4.1, -2.66, -2.56, {'*': P['black']})
    # ---- wheels, hubs, fenders
    for s in (-1, 1):
        c = (0, TR['Rr'], s * TR['zr']); solid_wheel(m, c, TR['Rr'], TR['wr'], T_TREAD_R, T_RIM_R, P['tyre'], seg=22); h = TR['wr'] / 2
        hub(m, c, s, [(h - 0.25, 0.55), (h + 0.02, 0.55), (h + 0.05, 0.42), (h + 0.08, 0.24), (h + 0.16, 0.0)], P['rim'], seg=10)
        c = (TR['xf'], TR['Rf'], s * TR['zf']); solid_wheel(m, c, TR['Rf'], TR['wf'], T_TREAD_S, T_RIM_S, P['tyre'], seg=16); h = TR['wf'] / 2
        hub(m, c, s, [(h - 0.25, 0.3), (h, 0.3), (h + 0.04, 0.18), (h + 0.08, 0)], P['rim'], seg=8)
        za, zb = sorted((s * 2.15, s * 4.05))
        arc_shell(m, (0, TR['Rr']), 2.98, 3.05, za, zb, 18, 168, 10, P['green'])
        a = np.radians(160); m.box(3.05 * np.cos(a) - 0.12, 3.05 * np.cos(a) + 0.12, TR['Rr'] + 3.05 * np.sin(a), TR['Rr'] + 3.05 * np.sin(a) + 0.2,
                                   min(s * 3.6, s * 3.95), max(s * 3.6, s * 3.95), {'*': P['black'], '-x': P['red']})
        za, zb = sorted((s * 2.25, s * 3.6))
        arc_shell(m, (TR['xf'], TR['Rf']), 1.86, 1.92, za, zb, 20, 160, 6, P['black'])
        m.tube((TR['xf'], TR['Rf'], s * 2.25), (TR['xf'], TR['Rf'] + 1.88, s * 2.25), 0.06, P['black'])
    # ================= water tanker
    Tf, Tb, yc = TK['Tf'], TK['Tf'] - TK['L'], TK['yc']
    pr, s_ = tank_profile(); x0, y0, x1, y1 = T_TANK; seg = 22
    revolve(m, (0, yc, 0), (1, 0, 0), pr, seg, lambda j, i, k: m.uv_px(x0 + 0.5 + (x1 - x0 - 1) * k / seg, y0 + 0.5 + s_[i] * (y1 - y0 - 1)))
    # chassis, saddles, axle, springs (v32: everything follows TK: tank radius R, wheel size / track)
    R, xa, Rw, ww, zw = TK['R'], TK['xa'], TK['Rw'], TK['ww'], TK['zw']; top = yc + R
    zt = lambda y: np.sqrt(max(R * R - (y - yc) ** 2, 0.0))                       # tank half width at height y
    for s in (-1, 1):
        za, zb = sorted((s * 0.95, s * 1.3))
        m.rbox(Tb + 0.5, Tf - 0.5, 1.85, 2.4, za, zb, 0.06, 0, {'*': P['dark']}, P['dark'], seg=2)
        m.box(xa - 1.2, xa + 1.2, 1.7, 1.86, za, zb, {'*': P['dark']})
    ys = yc - np.sqrt(R * R - 1.7 ** 2) + 0.05
    for xs in (Tf - 1.1, xa, Tb + 1.1): m.box(xs - 0.15, xs + 0.15, 2.35, ys, -1.7, 1.7, {'*': P['dark']})
    pipe(m, [(xa, Rw, -(zw - ww / 2 + 0.3)), (xa, Rw, zw - ww / 2 + 0.3)], 0.2, P['dark'], seg=8)   # ends inside the wheels
    r0 = Rw + 0.2
    for s in (-1, 1):
        c = (xa, Rw, s * zw); solid_wheel(m, c, Rw, ww, T_TREAD_S, T_RIM_S, P['tyre'], seg=16); h = ww / 2
        hub(m, c, s, [(h - 0.3, 0.36), (h, 0.36), (h + 0.04, 0.22), (h + 0.09, 0)], P['rim'], seg=8)
        zi, zo = zw - ww / 2 - 0.12, zw + ww / 2 + 0.12; za, zb = sorted((s * zi, s * zo))
        arc_shell(m, (xa, Rw), r0, r0 + 0.06, za, zb, 15, 165, 8, P['galv'])
        yt = Rw + r0 + 0.6
        for dx in (-0.9, 0.9): m.tube((xa + dx, Rw + np.sqrt(r0 ** 2 - dx * dx) + 0.02, s * (zi + 0.06)), (xa + dx, yt, s * (zt(yt) - 0.1)), 0.06, P['galv'])
    # drawbar (A-frame) on the tractor hitch, jack, PTO shaft, vacuum pump + pipe into the front head
    m.tube((-3.35, 1.62, 0), (-2.65, 1.62, 0), 0.12, P['dark'])
    for s in (-1, 1): m.tube((-3.3, 1.62, s * 0.12), (Tf - 0.9, 2.12, s * 1.12), 0.15, P['dark'])
    m.tube((-5.0, 1.95, -0.75), (-5.0, 1.95, 0.75), 0.08, P['dark'])
    m.tube((-4.4, 0.75, 0.62), (-4.4, 2.0, 0.62), 0.09, P['dark']); m.box(-4.65, -4.15, 0.66, 0.74, 0.37, 0.87, {'*': P['dark']})
    pipe(m, [(-1.25, 2.35, 0), (-4.3, 2.75, 0)], 0.1, P['black'], seg=8)
    m.box(-4.95, -4.35, 1.85, 2.4, -0.12, 0.12, {'*': P['dark']})
    m.rbox(-5.0, -4.3, 2.4, 3.2, -0.4, 0.4, 0.1, 2, {'*': P['black']}, P['black'], seg=2)
    pipe(m, [(-4.65, 3.15, 0.2), (-4.65, yc + 0.6, 0.2), (Tf - dome_depth(1.5) - 0.12, yc + 1.5, 0.2)], 0.09, P['galv'], seg=8)
    # manhole on the top, overflow vent
    revolve(m, (Tf - 2.2, top - 0.2, 0), (0, 1, 0), [(0, 0.85), (0.5, 0.85), (0.5, 0.95), (0.58, 0.95), (0.62, 0.55), (0.64, 0)], 12, solid(m, P['galv']))
    m.box(Tf - 3.15, Tf - 2.95, top + 0.2, top + 0.42, -0.25, 0.25, {'*': P['dark']})             # hinge
    m.box(Tf - 1.45, Tf - 1.2, top + 0.15, top + 0.38, -0.12, 0.12, {'*': P['red']})              # clamp handle
    pipe(m, [(Tb + 2.5, top - 0.1, 0), (Tb + 2.5, top + 0.55, 0), (Tb + 2.1, top + 0.55, 0)], 0.07, P['galv'], seg=6)
    # rear: ladder, outlet, valve, spray bar with nozzles, light bar
    xl = Tb - 0.35; xt = Tb + dome()[-1][0] + 0.4
    for s in (-1, 1):
        pipe(m, [(xl, 2.9, s * 0.55), (xl, top + 0.35, s * 0.55), (xt, top + 0.35, s * 0.55), (xt, top - 0.03, s * 0.55)], 0.06, P['galv'], seg=6)
        m.tube((xl, 3.2, s * 0.55), (Tb + dome_depth(np.hypot(yc - 3.3, 0.55)) + 0.1, 3.3, s * 0.55), 0.04, P['galv'])
    for y in np.arange(3.45, top + 0.1, 0.8): pipe(m, [(xl, y, -0.55), (xl, y, 0.55)], 0.045, P['galv'], seg=6)
    xb = Tb - 0.75; xo = Tb + dome()[-1][0] + 0.25
    pipe(m, [(xo, yc - R + 0.2, 0), (xo, 2.05, 0), (xb, 1.95, 0)], 0.14, P['galv'], seg=8)
    m.box(Tb - 0.35, Tb - 0.05, 1.8, 2.2, -0.2, 0.2, {'*': P['galv']}); m.tube((Tb - 0.2, 2.2, 0), (Tb - 0.2, 2.6, 0.25), 0.04, P['red'])
    pipe(m, [(xb, 1.95, -3.5), (xb, 1.95, 3.5)], 0.13, P['galv'], seg=8)
    for s in (-1, 1): m.box(xb - 0.16, xb + 0.16, 1.79, 2.11, s * 3.5 - 0.06, s * 3.5 + 0.06, {'*': P['dark']})
    for z in np.linspace(-3.1, 3.1, 7): m.box(xb - 0.2, xb + 0.05, 1.68, 1.84, z - 0.07, z + 0.07, {'*': P['black']})
    for s in (-1, 1): m.tube((Tb + 0.5, 2.1, s * 1.1), (xb, 1.97, s * 1.5), 0.07, P['dark'])
    m.tube((Tb + 0.55, 2.15, -3.0), (Tb + 0.55, 2.15, 3.0), 0.08, P['dark'])
    for s in (-1, 1):
        za, zb = sorted((s * 2.6, s * 3.05)); m.box(Tb + 0.35, Tb + 0.6, 2.25, 2.6, za, zb, {'*': P['black'], '-x': P['red']})
    return m


def tractor_spheres():
    out = []
    for s in (-1, 1):
        zc = s * TR['zr']; out.append((0, TR['Rr'], zc, 1.1))
        out += [(1.95 * np.cos(t), TR['Rr'] + 1.95 * np.sin(t), zc, 0.8) for t in np.linspace(0, 2 * np.pi, 8)[:-1] + 0.2]
        out += [(TR['xf'] + 1.05 * np.cos(t), TR['Rf'] + 1.05 * np.sin(t), s * TR['zf'], 0.6) for t in np.linspace(0, 2 * np.pi, 6)[:-1]]
        out += [(TK['xa'] + 0.62 * TK['Rw'] * np.cos(t), TK['Rw'] + 0.62 * TK['Rw'] * np.sin(t), s * TK['zw'], 0.38 * TK['Rw']) for t in np.linspace(0, 2 * np.pi, 6)[:-1]]
        for x in (-0.3, 1.9):
            for y in (5.6, 7.8): out.append((x, y, s * 1.0, 1.2))
        out.append((11.35, 2.3, s * 0.65, 0.75))
    out += [(x, 3.8, 0, 1.15) for x in (4.2, 6.3, 8.4, 10.0)] + [(1.0, 2.9, 0, 1.2), (-4.6, 2.6, 0, 0.7)]
    out += [(x, TK['yc'], 0, TK['R'] - 0.05) for x in np.linspace(TK['Tf'] - 1.3, TK['Tf'] - TK['L'] + 1.3, 7)]
    return out


# ------------------------------------------------------------------ build
XF = {}                                           # name -> (scale, dx, dz) applied by finish (model -> file coordinates)


def finish(name, m, img, spheres, outd, k=1.0):
    if k != 1.0:                                  # v32: uniform scale (positions only; normals unchanged)
        m.V = [(v[0] * k, v[1] * k, v[2] * k) + tuple(v[3:]) for v in m.V]; spheres = [(x * k, y * k, z * k, r * k) for x, y, z, r in spheres]
    P = np.array([v[:3] for v in m.V]); lo, hi = P.min(0), P.max(0); dx, dz = -(lo[0] + hi[0]) / 2, -(lo[2] + hi[2]) / 2
    shift(m, dx, dz); spheres = [(x + dx, y, z + dz, r) for x, y, z, r in spheres]
    XF[name] = (k, dx, dz)
    V = np.array([v[:6] for v in m.V]); I = np.array(m.I).reshape(-1, 3); A, B, C = V[I[:, 0], :3], V[I[:, 1], :3], V[I[:, 2], :3]
    wind = np.cross(B - A, C - A); nrm = V[I[:, 0], 3:6] + V[I[:, 1], 3:6] + V[I[:, 2], 3:6]
    bad = int(((wind * nrm).sum(1) < 0).sum())    # game front face = counter-clockwise seen from outside = along the normal
    if bad: raise SystemExit(f'{name}: {bad} triangles wound against their normal (would be culled in game)')
    nv, nt = retry(m.write, f'{outd}/{name}.jm', MATTE)
    retry(img.save, f'{outd}/{name}.png', optimize=True); write_shp(f'{outd}/{name}.shp', spheres)
    P = np.array([v[:3] for v in m.V])
    print(f'{name}: {nv} vertices, {nt} triangles, {len(spheres)} spheres, bbox min {P.min(0).round(2)} max {P.max(0).round(2)} ft')
    return nt, P.min(0), P.max(0)


def build(outd=OUTD):
    os.makedirs(outd, exist_ok=True); info = {}
    img, pal = tractor_texture(); info['tractor_tank'] = finish('tractor_tank', tractor_model(pal), img, tractor_spheres(), outd, k=TRACTOR_SCALE)
    img, pal = van_texture(); info['fire_van'] = finish('fire_van', van_model(pal), img, van_spheres(), outd)
    return info


# ------------------------------------------------------------------ preview (software z-buffer, NOT a game render)
def preview(out_path, outd=OUTD, custom=None):
    from preview_stt_scene import Cam, raster, load_jm
    from rider_gate import scale_person
    from PIL import ImageDraw as _D
    def obj(name, off=(0, 0, 0)):
        V, I = load_jm(f'{outd}/{name}.jm'); V = V.copy(); V[:, :3] += np.array(off, np.float32)
        return V, I, np.asarray(Image.open(f'{outd}/{name}.png').convert('RGBA'), np.float32) / 255
    tr, vn = obj('tractor_tank'), obj('fire_van')
    Lg = np.array([0.35, 0.8, 0.45]); Lg /= np.linalg.norm(Lg)
    def shot(objs, eye, tgt, label, W=900, H=560, fov=50):
        cam = Cam(eye, tgt, W, H, fov); img = np.zeros((H, W, 3), np.float32)
        sky = np.linspace(0, 1, H)[:, None, None]; img[:] = np.array([0.55, 0.70, 0.90]) * (1 - sky) + np.array([0.82, 0.86, 0.90]) * sky
        zb = np.full((H, W), np.inf, np.float32)
        gs = np.arange(-60, 61, 5.0); GX, GZ = np.meshgrid(gs, gs); Pg = np.stack([GX, np.zeros_like(GX), GZ], -1).reshape(-1, 3)
        n = len(gs); ii, jj = np.meshgrid(np.arange(n - 1), np.arange(n - 1), indexing='ij'); a = (ii * n + jj).ravel()
        Ig = np.concatenate([np.stack([a, a + 1, a + n], 1), np.stack([a + 1, a + n + 1, a + n], 1)])
        C = np.array([0.58, 0.45, 0.33]) * (0.9 + 0.15 * np.random.default_rng(0).random((len(Pg), 1)))
        raster(img, zb, cam, Pg, Ig, lambda ti, B: (C[Ig[ti]] * B[:, :, None]).sum(1))
        for V_, I_, tx in objs:
            th, tw = tx.shape[:2]
            A_, B_, C_ = V_[I_[:, 0], :3], V_[I_[:, 1], :3], V_[I_[:, 2], :3]          # back-face culling, like the game:
            I_ = I_[(np.cross(B_ - A_, C_ - A_) * (np.array(eye, np.float32) - A_)).sum(1) > 0]   # keep counter-clockwise seen from the eye
            def col(ti, B, V_=V_, I_=I_, tx=tx, tw=tw, th=th):
                uv = (V_[I_[ti], 6:8][None] * B[:, :, None]).sum(1); nn = (V_[I_[ti], 3:6][None] * B[:, :, None]).sum(1)
                py = np.clip((1 - uv[:, 1]) * th, 0, th - 1).astype(int); px = np.clip(uv[:, 0] * tw, 0, tw - 1).astype(int)
                return tx[py, px, :3] * (0.68 + 0.38 * np.clip(nn @ Lg, 0, 1))[:, None]
            raster(img, zb, cam, V_[:, :3], I_, col)
        im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)); _D.Draw(im).text((10, 8), label, fill=(0, 0, 0))
        return im
    pt, pv = scale_person((12.0, 0, 6.5)), scale_person((5.0, 0, 5.0))
    if custom:                                    # debug close-ups: (model, eye, target, fov, label)
        views = [shot([tr] if w == 't' else [vn], e, t, lb, fov=f) for w, e, t, f, lb in custom]
    else: views = [shot([tr, pt], (44, 12, 31), (0, 5, 0), 'tractor_tank 3/4 front'),
             shot([tr, pt], (-44, 13, -29), (-3, 5, 0), 'tractor_tank 3/4 back'),
             shot([vn, pv], (19, 6.5, 15), (1, 3.8, 0), 'fire_van 3/4 front (+z side)'),
             shot([vn, pv], (-19, 7.5, -14), (0, 3.8, 0), 'fire_van 3/4 back (-z side)'),
             shot([tr, pt], (0, 4.0, 56), (0, 4.5, 0), 'tractor_tank side (+z)'),
             shot([vn, pv], (-3, 3.0, -27), (-0.5, 3.5, 0), 'fire_van side (-z)')]
    W_, H_ = views[0].size; sheet = Image.new('RGB', (W_ * 2, H_ * ((len(views) + 1) // 2)), (255, 255, 255))
    for k, v in enumerate(views): sheet.paste(v, ((k % 2) * W_, (k // 2) * H_))
    os.makedirs(os.path.dirname(out_path), exist_ok=True); retry(sheet.save, out_path); print('preview', out_path)
    if custom or 'tractor_tank' not in XF: return
    # back-face check (culling ON, as in game): every tyre close-up, outer side and inner side (from under the vehicle),
    # mudguards and tank heads from below -> any missing / inward face shows as a hole (sky or ground seen through)
    k, dx, dz = XF['tractor_tank']; T = lambda x, y, z: (k * x + dx, k * y, k * z + dz)
    chk = []
    for nm, (x, y, z, R) in (('rear', (0, TR['Rr'], TR['zr'], TR['Rr'])), ('front', (TR['xf'], TR['Rf'], TR['zf'], TR['Rf'])),
                             ('tanker', (TK['xa'], TK['Rw'], TK['zw'], TK['Rw']))):
        c = T(x, y, z); r = k * R
        chk.append(shot([tr], (c[0] + 1.6 * r, c[1] + 0.5 * r, c[2] + 2.6 * r), c, f'CULLED {nm} tyre, outer side', fov=55))
        chk.append(shot([tr], (c[0] + 2.2 * r, 0.35, c[2] - 2.4 * r - k * 1.5), c, f'CULLED {nm} tyre, inner side (from under)', fov=60))
    Tb = TK['Tf'] - TK['L']
    chk.append(shot([tr], T(Tb - 6, 0.6, 2.5), T(Tb + 3, TK['yc'], 0), 'CULLED tank rear head + spray bar, low', fov=60))
    chk.append(shot([tr], T(TK['Tf'] + 0.5, 0.4, 0), T(TK['xa'], 2.5, 0), 'CULLED under the tank: mudguards, chassis', fov=75))
    chk.append(shot([tr], T(-1.0, 0.4, 0), T(6, 3, 0), 'CULLED under the tractor: rear wheels inner, cab', fov=80))
    chk.append(shot([vn], (VAN['xf'] + 3.0, 0.3, -1.0), (VAN['xf'], VAN['R'], VAN['wz']), 'CULLED van front tyre, inner side', fov=60))
    W_, H_ = chk[0].size; sheet = Image.new('RGB', (W_ * 2, H_ * ((len(chk) + 1) // 2)), (255, 255, 255))
    for i, v in enumerate(chk): sheet.paste(v, ((i % 2) * W_, (i // 2) * H_))
    p = out_path.replace('.png', '_backface_check.png'); retry(sheet.save, p); print('back-face check', p)


if __name__ == '__main__':
    build()
    if '--no-preview' not in sys.argv: preview(os.path.join(os.path.dirname(ROOT), 'apercus_sgm', 'vehicles_3d.png'))
