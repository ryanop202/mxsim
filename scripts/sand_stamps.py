"""Glendale sand sections -> 2D stamps (exact as-built heights + tile ids) with their riding line (channel skeleton)."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np; sys.path.insert(0, ROOT + '/scripts')
from mxs import Track, parse_tileinfo
from scipy import ndimage as ndi
from skimage.morphology import skeletonize
from scipy.ndimage import uniform_filter1d
from engine import sx_wall
F = REF + '/JGSX2026TestTracks/JGSX2026Glendale'
T = Track(F, 'xz'); H = np.clip(T.H - np.median(T.H), 0, None); s = T.s
names = [t.get('name', '?') for t in parse_tileinfo(F + '/tileinfo')]
SAND_T = [i for i, n in enumerate(names) if n in ('Sand Exit', 'Sand Bump Solo')]
tile_full = np.repeat(np.repeat(T.tiles, 2, 0), 2, 1); tile_full = np.pad(tile_full, ((0, 1), (0, 1)), mode='edge')
sand = np.isin(tile_full, SAND_T)
BOX = {'GL': (0, 205, 95, 470), 'GR': (360, 575, 225, 420)}
out = {}
for key, (x0, x1, z0, z1) in BOX.items():
    j0, j1, i0, i1 = [int(v / s) for v in (x0, x1, z0, z1)]
    h = H[i0:i1, j0:j1]; sd = sand[i0:i1, j0:j1]; tl = tile_full[i0:i1, j0:j1]
    # channel = largest sand component, holes filled
    lab, n = ndi.label(ndi.binary_closing(sd, iterations=3)); sizes = ndi.sum(sd, lab, range(1, n + 1))
    chan = ndi.binary_fill_holes(lab == (np.argmax(sizes) + 1))
    if key == 'GL':
        # every floor-separated relief component lying mostly in the sand channel (sand tables, ripples, organic berms)
        comp, nc = ndi.label(h > 0.25); keep = np.zeros_like(chan)
        for k in range(1, nc + 1):
            m = comp == k; ov = (m & chan).sum() / m.sum()
            border = m[0, :].any() or m[-1, :].any() or m[:, 0].any() or m[:, -1].any()
            if ov >= 0.5 and not border: keep |= m
        # grow each kept feature down to the floor (connected low pixels only)
        grown = keep.copy(); low = h > 0.005
        for _ in range(int(8 / s)):
            nxt = (ndi.binary_dilation(grown) & low & (h <= 0.3)) | grown
            if (nxt == grown).all(): break
            grown = nxt
        zz = np.arange(h.shape[0])[:, None] * s + z0; xx = np.arange(h.shape[1])[None, :] * s + x0
        top = (zz < 172) & (xx < 122)
        # plus every low feature inside the sand channel itself (Glendale sand ripples, 0.1-0.8 ft)
        others = ndi.binary_dilation((comp > 0) & ~keep, iterations=int(5 / s))
        region = (ndi.binary_dilation(grown, iterations=2) | (ndi.binary_dilation(chan, iterations=int(1 / s)) & ~others)) & ~top
        P = np.where(region, h, 0.0)
        edge_cut = float(np.where(region & ~ndi.binary_erosion(region), h, 0).max())
        dist = ndi.distance_transform_edt(region) * s
        P = P * np.clip((dist - s) / 2.0, 0, 1)
        # top-left sand crescent (entry turn of the J): it touches the neighbouring Glendale crescent/blocks,
        # so take the sand-tiled area + 1.5 ft and let it fall off with the measured JGSX lateral wall
        rt = ndi.binary_dilation(sd, iterations=int(1.5 / s)) & top
        dout, (ri, rj) = ndi.distance_transform_edt(~rt, return_indices=True); dout = dout * s
        from engine import sx_wall
        Pt = np.where(rt, h, np.minimum(h, h[ri, rj] * sx_wall(dout)))
        Pt = np.where((dout > 9) | ~(zz < 182) | ~(xx < 128), 0.0, Pt)
        P = np.maximum(P, Pt)
    else:
        # GR: the organic sand berm is built against the neighbouring Glendale lanes (no floor between them).
        # Keep the sand channel + 4 ft; drop the dirt singles at the channel entry/exit (they belong to the
        # Glendale lanes cp10 / cp12); outside the region, the height falls off with the measured JGSX
        # lateral wall (10-90 % over ~4 ft) from the boundary height, so nothing is cut.
        comp, nc = ndi.label(h > 0.15)
        drop = np.zeros_like(chan)
        jj = np.arange(h.shape[1]) * s + x0
        for k in range(1, nc + 1):
            m = comp == k; ii_, jj_ = np.nonzero(m); cx = jj_.mean() * s + x0; cz = ii_.mean() * s + z0
            if (abs(cx - 480) < 15 and abs(cz - 255) < 20) or cx < 425: drop |= m      # cp10 single, cp12-lane single/berm
        drop = ndi.binary_dilation(drop, iterations=int(3 / s))
        region = ndi.binary_dilation(chan, iterations=int(1.5 / s)) & ~drop
        zz = np.arange(h.shape[0])[:, None] * s + z0; region &= (zz < 397)
        region[:, :int((425 - x0) / s)] = False
        dout, (ri, rj) = ndi.distance_transform_edt(~region, return_indices=True)
        dout = dout * s
        hb = h[ri, rj]                                   # height at the nearest region pixel
        P = np.where(region, h, np.minimum(h, hb * sx_wall(dout - 0.0)))
        P = np.where(dout > 9, 0.0, P)
        edge_cut = float(np.where((dout > 8.5) & (dout <= 9), P, 0).max())
        region = P > 0.005
    # riding line = channel skeleton, ordered end to end
    sk = skeletonize(chan); pts = np.argwhere(sk)
    nb = ndi.convolve(sk.astype(int), np.ones((3, 3), int), mode='constant') - 1
    ends = np.argwhere(sk & (nb == 1))
    # walk the longest path between end points (graph BFS on skeleton pixels)
    from collections import deque
    S = set(map(tuple, pts))
    def bfs(a):
        prev = {a: None}; dq = deque([a]); last = a
        while dq:
            p = dq.popleft(); last = p
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    q = (p[0] + di, p[1] + dj)
                    if q in S and q not in prev: prev[q] = p; dq.append(q)
        return last, prev
    a, _ = bfs(tuple(ends[0])); b, prev = bfs(a)
    path = []; p = b
    while p is not None: path.append(p); p = prev[p]
    path = np.array(path[::-1], float)
    X = (path[:, 1] + j0) * s; Z = (path[:, 0] + i0) * s
    # travel direction (Glendale lap order): GL from its top end (cp4) to its NE end (cp9); GR from the east-heading top arm (cp10) to the west end (cp12)
    first = np.array({'GL': (96, 139), 'GR': (474, 263)}[key])
    if np.hypot(X[0] - first[0], Z[0] - first[1]) > np.hypot(X[-1] - first[0], Z[-1] - first[1]): X, Z = X[::-1], Z[::-1]
    # resample 1 ft, smooth 15 ft
    d = np.r_[0, np.cumsum(np.hypot(np.diff(X), np.diff(Z)))]; dd = np.arange(0, d[-1], 1.0)
    X = uniform_filter1d(np.interp(dd, d, X), 15, mode='nearest'); Z = uniform_filter1d(np.interp(dd, d, Z), 15, mode='nearest')
    if key == 'GR':
        keepl = X >= 428; X, Z = X[keepl], Z[keepl]
        ax_ = np.arange(434.0, X[0], 1.0); X = np.r_[ax_, X]; Z = np.r_[np.full(len(ax_), Z[0]), Z]          # approach heading east (Glendale cp0 side)
    else:
        ax_ = np.arange(147.0, X[0], -1.0); X = np.r_[ax_, X]; Z = np.r_[np.full(len(ax_), Z[0]), Z]         # approach heading west (Glendale cp3 lane)
    out[key] = dict(x0=j0 * s, z0=i0 * s, s=s, shape=P.shape, line=np.c_[X, Z].round(2).tolist(), edge_cut=edge_cut, hmax=float(P.max()),
                    tile_names={int(t): names[t] for t in np.unique(tl[region])})
    tmask = region | ndi.binary_dilation(chan, iterations=int(2 / s))
    np.save(f'{ROOT}/lib/sand_{key}.npy', P.astype(np.float32)); np.save(f'{ROOT}/lib/sand_{key}_tiles.npy', np.where(tmask, tl, 255).astype(np.uint8))
    np.save(f'{ROOT}/lib/sand_{key}_chan.npy', chan)
    hd = lambda k0, k1: np.degrees(np.arctan2(Z[k1] - Z[k0], X[k1] - X[k0]))
    print(key, 'line', len(X), 'ft; start', (round(X[0]), round(Z[0])), 'end', (round(X[-1]), round(Z[-1])), 'heading start %.0f end %.0f' % (hd(0, 20), hd(-21, -1)),
          'hmax %.2f, edge cut before feather %.3f' % (P.max(), edge_cut), out[key]['tile_names'])
json.dump(out, open(ROOT + '/lib/sand_stamps.json', 'w'))
