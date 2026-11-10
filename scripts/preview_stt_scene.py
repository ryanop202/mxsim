"""Perspective preview of an exported track folder (terrain + statues), software z-buffer, NOT a game render.
Terrain: heights from terrain.png, colour = tile (dirt / grass) x lightmap (shading.ppm). Statues: .jm (JM1) with their
texture (alpha < 0.5 discarded), placed like the game: local +z -> (sin a, cos a), local +x -> (cos a, -sin a), put on the
ground under the origin (no tilt here).
usage: python scripts/preview_stt_scene.py <track folder> <out.png> view1 [view2 ...]
view = name:eye_x,eye_y_above_ground,eye_z:target_x,target_z:half_extent_ft"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 0.28975
GAME = r'C:/Program Files (x86)/MX Simulator'


def load_track(T):
    global S
    hf = open(f'{T}/terrain.hf').read().split(); hmin, hmax = float(hf[2]), float(hf[3]); S = float(hf[1])   # v62: step from the file
    H = np.asarray(Image.open(f'{T}/terrain.png'), np.float32) / 65535 * (hmax - hmin) + hmin
    N = H.shape[0]
    raw = open(f'{T}/shading.ppm', 'rb').read(); hdr = f'P6\n{N} {N}\n255\n'.encode()
    sh = np.frombuffer(raw[len(hdr):], np.uint8).reshape(N, N, 3)[:, :, 0].astype(np.float32) / 255
    tiles = np.fromfile(f'{T}/tilemap', np.uint8).reshape(2048, 2048)
    return H, sh, tiles


def resolve(ref, T):
    ref = ref.lstrip('@'); folder, rest = ref.split('/', 1)
    for base in (os.path.dirname(T), GAME):
        p = os.path.join(base, folder, rest)
        if os.path.exists(p): return p
    return None


def load_jm(path):
    L = open(path).read().splitlines()
    k = next(i for i, l in enumerate(L) if i > 0 and len(l.split()) == 2 and all(t.isdigit() for t in l.split()))
    out = []
    while k < len(L) and len(L[k].split()) == 2:
        nv, nt = map(int, L[k].split())
        V = np.array([[float(t) for t in l.split()[:8]] for l in L[k + 1:k + 1 + nv]], np.float32)
        I = np.array([int(l) for l in L[k + 1 + nv:k + 1 + nv + 3 * nt]], np.int64).reshape(-1, 3)
        out.append((V, I)); k = k + 1 + nv + 3 * nt
        if k < len(L) and len(L[k].split()) == 5: k += 1
    V = np.vstack([o[0] for o in out]); off = np.cumsum([0] + [len(o[0]) for o in out[:-1]])
    I = np.vstack([o[1] + f for o, f in zip(out, off)])
    return V, I


class Cam:
    def __init__(self, eye, target, W=960, H=600, fov=55):
        self.e = np.array(eye, np.float32); f = np.array(target, np.float32) - self.e; f /= np.linalg.norm(f)
        r = np.cross(f, [0, 1, 0]); r /= np.linalg.norm(r); u = np.cross(r, f)
        self.f, self.r, self.u = f, r, u; self.W, self.H = W, H; self.k = (W / 2) / np.tan(np.radians(fov / 2))
    def proj(self, P):
        d = P - self.e; z = d @ self.f; x = d @ self.r; y = d @ self.u
        return np.stack([self.W / 2 + self.k * x / z, self.H / 2 - self.k * y / z, z], -1)


def raster(img, zb, cam, P, I, colfn, alphafn=None):
    """P (n,3) world, I (m,3); colfn(tri_index, bary (k,3)) -> (k,3) rgb 0..1"""
    Q = cam.proj(P)
    for ti, t in enumerate(I):
        q = Q[t]
        if (q[:, 2] < 0.5).any(): continue
        x0, x1 = max(int(q[:, 0].min()), 0), min(int(q[:, 0].max()) + 1, cam.W - 1)
        y0, y1 = max(int(q[:, 1].min()), 0), min(int(q[:, 1].max()) + 1, cam.H - 1)
        if x1 < x0 or y1 < y0: continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        (ax, ay, _), (bx, by, _), (cx, cy, _) = q
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-9: continue
        l0 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den
        l1 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / den; l2 = 1 - l0 - l1
        m = (l0 >= 0) & (l1 >= 0) & (l2 >= 0)
        if not m.any(): continue
        B = np.stack([l0[m], l1[m], l2[m]], 1)
        iz = 1 / q[:, 2]; w = B * iz; zz = 1 / w.sum(1); Bp = w * zz[:, None]          # perspective-correct
        iy = (ys[m] - 0.5).astype(int); ix = (xs[m] - 0.5).astype(int)
        front = zz < zb[iy, ix]
        if not front.any(): continue
        Bp, iy, ix, zz = Bp[front], iy[front], ix[front], zz[front]
        if alphafn is not None:
            a = alphafn(ti, Bp) >= 0.5; Bp, iy, ix, zz = Bp[a], iy[a], ix[a], zz[a]
            if not len(zz): continue
        zb[iy, ix] = zz; img[iy, ix] = colfn(ti, Bp)


def render(T, view, H, sh, tiles, statues):
    name, eye, tgt, half = view
    ey = float(H[int(eye[2] / S), int(eye[0] / S)]) + eye[1]
    ty = float(H[int(tgt[1] / S), int(tgt[0] / S)]) + 2.0
    cam = Cam((eye[0], ey, eye[2]), (tgt[0], ty, tgt[1]))
    img = np.zeros((cam.H, cam.W, 3), np.float32); img[:] = (0.05, 0.06, 0.12)
    zb = np.full((cam.H, cam.W), np.inf, np.float32)
    # terrain patch around the target (and the eye)
    cx, cz = (eye[0] + tgt[0]) / 2, (eye[2] + tgt[1]) / 2; st = 1.0
    xs = np.arange(cx - half, cx + half, st); zs = np.arange(cz - half, cz + half, st)
    GX, GZ = np.meshgrid(xs, zs); hy = H[(GZ / S).astype(int), (GX / S).astype(int)]
    lit = sh[(GZ / S).astype(int), (GX / S).astype(int)]
    tc = tiles[(GZ / S / 2).astype(int), (GX / S / 2).astype(int)]
    base = np.where((tc == 9)[..., None], np.array([0.30, 0.48, 0.22]), np.array([0.66, 0.48, 0.33]))
    colg = base * (0.25 + 1.0 * lit[..., None])
    P = np.stack([GX, hy, GZ], -1).reshape(-1, 3); n = len(xs)
    C = colg.reshape(-1, 3)
    ii, jj = np.meshgrid(np.arange(len(zs) - 1), np.arange(n - 1), indexing='ij'); a = (ii * n + jj).ravel()
    I = np.concatenate([np.stack([a, a + 1, a + n], 1), np.stack([a + 1, a + n + 1, a + n], 1)])
    raster(img, zb, cam, P, I, lambda ti, B: (C[I[ti]] * B[:, :, None]).sum(1))
    # statues near the view
    for (x, z, ang, jm, png, *yo_) in statues:
        if abs(x - cx) > half or abs(z - cz) > half: continue
        V, Ii = jm
        ca, sa = np.cos(ang), np.sin(ang)
        wx = V[:, 0] * ca + V[:, 2] * sa; wz = -V[:, 0] * sa + V[:, 2] * ca
        gy = float(H[int(z / S), int(x / S)]) + (yo_[0] if yo_ else 0.0)   # the statue's y = height above the ground
        Pw = np.stack([x + wx, gy + V[:, 1], z + wz], 1)
        nrm = np.stack([V[:, 3] * ca + V[:, 5] * sa, V[:, 4], -V[:, 3] * sa + V[:, 5] * ca], 1)
        tex, tw, th = png
        def col(ti, B, Ii=Ii, V=V, nrm=nrm, tex=tex, tw=tw, th=th):
            uv = (V[Ii[ti], 6:8][None] * B[:, :, None]).sum(1); nn = (nrm[Ii[ti]][None] * B[:, :, None]).sum(1)
            px = np.clip((uv[:, 0] % 1.0) * tw, 0, tw - 1).astype(int); py = np.clip((1 - uv[:, 1] % 1.0) * th, 0, th - 1).astype(int)
            c = tex[py, px, :3]; L = np.array([-0.5, 0.75, 0.45]); L /= np.linalg.norm(L)
            return c * (0.55 + 0.5 * np.abs(nn @ L))[:, None]
        def alp(ti, B, Ii=Ii, V=V, tex=tex, tw=tw, th=th):
            uv = (V[Ii[ti], 6:8][None] * B[:, :, None]).sum(1)
            px = np.clip((uv[:, 0] % 1.0) * tw, 0, tw - 1).astype(int); py = np.clip((1 - uv[:, 1] % 1.0) * th, 0, th - 1).astype(int)
            return tex[py, px, 3]
        raster(img, zb, cam, Pw, Ii, col, alp)
    out = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    ImageDraw.Draw(out).text((10, 8), name, fill=(255, 255, 255))
    return out


def main():
    T, outp = sys.argv[1], sys.argv[2]
    H, sh, tiles = load_track(T)
    cache = {}; statues = []
    for l in open(f'{T}/statues'):
        if not l.strip().startswith('['): continue
        v = l.split(']')[0][1:].split(); rest = l.split(']')[1].split()
        jp, tp = resolve(rest[1], T), resolve(rest[2], T)
        if not jp or not tp: continue
        if jp not in cache: cache[jp] = load_jm(jp)
        if tp not in cache:
            t = np.asarray(Image.open(tp).convert('RGBA'), np.float32) / 255; cache[tp] = (t, t.shape[1], t.shape[0])
        statues.append((float(v[0]), float(v[2]), float(rest[0]), cache[jp], cache[tp], float(v[1])))   # v86: + y offset
    views = []
    for s in sys.argv[3:]:
        nm, e, t, h = s.split(':'); views.append((nm, [float(q) for q in e.split(',')], [float(q) for q in t.split(',')], float(h)))
    tiles_im = [render(T, v, H, sh, tiles, statues) for v in views]
    cols = 2; rows = (len(tiles_im) + 1) // 2
    sheet = Image.new('RGB', (960 * cols, 600 * rows))
    for k, im in enumerate(tiles_im): sheet.paste(im, ((k % cols) * 960, (k // cols) * 600))
    sheet.save(outp); print('saved', outp)


if __name__ == '__main__':
    main()
