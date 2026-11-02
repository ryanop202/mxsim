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


PADDLE = dict(h=3.3, half=0.30, neck=0.16, foot=0.22, stem=0.05, stem_h=0.3, t=0.04, col=(214, 200, 34), edge=(170, 158, 22))

def paddle_profile():
    """v29: (y, half width) of the flat track-marker paddle (user's picture, the Acerbis kind, no logo): stem in the ground,
    small foot, neck, straight body, half-elliptic top. y = 0 at ground level."""
    P = PADDLE; prof = [(-P['stem_h'], P['stem']), (0.0, P['stem']), (0.001, P['foot']), (0.08, P['foot']),
                        (0.16, P['neck'] + 0.02), (0.24, P['neck']), (0.32, P['neck'] + 0.03), (0.40, P['half'] * 0.85), (0.46, P['half'])]
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
NETR = dict(h=3.6, sink=0.3, post_every=8.0, post_h=4.1, post_w=0.11, Lmax=140.0, TW=4096, TH=320)

def net_ribbon_texture():
    """one texture for every turn net: u = arc length / Lmax, net (alpha mesh, square cells) in rows 0..255 with a dark blue
    hem top and bottom; solid blue for the posts in rows 272..319."""
    W_, H_ = NETR['TW'], NETR['TH']; img = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    pxu = W_ / NETR['Lmax']; cell = 0.30                            # 0.30 ft square cells
    hem, col = (16, 34, 96, 255), (26, 56, 150, 225)
    for x in np.arange(0, W_, cell * pxu): d.line([(x, 0), (x, 255)], fill=col, width=2)
    pyv = 256 / (NETR['h'] + NETR['sink'])
    for y in np.arange(0, 256, cell * pyv): d.line([(0, y), (W_, y)], fill=col, width=2)
    d.rectangle([0, 0, W_, 9], fill=hem); d.rectangle([0, 246, W_, 255], fill=hem)
    d.rectangle([0, 272, W_, H_ - 1], fill=(30, 76, 205, 255))
    return img

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
    U = lambda s: s / NETR['Lmax']; Vb, Vt = 1 - 255 / NETR['TH'], 1.0
    for i in range(len(line_xz) - 1):
        (xa, za), (xb, zb) = line_xz[i] - (ox, oz), line_xz[i + 1] - (ox, oz)
        t = np.array([xb - xa, 0, zb - za]); n = np.cross(t, [0, 1, 0]); n /= np.linalg.norm(n) + 1e-12
        P = [np.array([xa, bot[i], za]), np.array([xb, bot[i + 1], zb]), np.array([xb, top[i + 1], zb]), np.array([xa, top[i], za])]
        uv = [(U(L[i]), Vb), (U(L[i + 1]), Vb), (U(L[i + 1]), Vt), (U(L[i]), Vt)]
        for sg in (1, -1):
            Q, T = (P, uv) if sg > 0 else (P[::-1], uv[::-1])
            m.tri_fan(Q, n * sg, T)
    post_uv = (0.5, 1 - 296 / NETR['TH'])
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


def floor():
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


def build(outd=OUTD):
    os.makedirs(outd, exist_ok=True); out = {}
    for name, fn, mat in (('stake_yellow', stake, (8, 0.4, 1, 1, 1)), ('net_blue', net, (0, 0, 0, 0, 0)),
                          ('start_floor', floor, (24, 0.6, 1, 1, 1))):
        m, img = fn(); nv, nt = m.write(f'{outd}/{name}.jm', mat); img.save(f'{outd}/{name}.png')
        V = np.array([v[:3] for v in m.V]); out[name] = (nv, nt, V.min(0).round(2).tolist(), V.max(0).round(2).tolist())
    net_ribbon_texture().save(f'{outd}/net_ribbon.png')
    return out


if __name__ == '__main__':
    for k, v in build().items(): print(k, v)
