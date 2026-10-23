"""1D obstacle-profile analysis on as-built heightmap profiles."""
import numpy as np
from scipy.ndimage import uniform_filter1d, minimum_filter1d

def slope_deg(d, h):
    g = np.gradient(h, d); return np.degrees(np.arctan(g)), g

def base_line(d, h, mode='sx', win=60.0):
    if mode == 'sx':
        return np.full_like(h, np.percentile(h, 3))
    step = d[1] - d[0]; k = max(3, int(win / step))
    b = minimum_filter1d(h, k, mode='nearest')
    return uniform_filter1d(b, k, mode='nearest')

def mounds(d, h, base, thr=0.35, min_len=2.0):
    r = h - base; on = r > thr; out = []
    i = 0; n = len(h)
    while i < n:
        if on[i]:
            j = i
            while j < n and on[j]: j += 1
            # extend to feet (r ~ 0.05)
            a = i
            while a > 0 and r[a - 1] > 0.05 and r[a-1] < r[a] + 1e-6: a -= 1
            b = j - 1
            while b < n - 1 and r[b + 1] > 0.05 and r[b+1] < r[b] + 1e-6: b += 1
            if d[b] - d[a] >= min_len: out.append((a, b))
            i = j
        else: i += 1
    return out

def face_metrics(d, h, a, c, direction=+1):
    """Face from foot a to crest c (indices). Returns length, height, lip angle, max angle, angles at 25/50/75%, transition radius."""
    if direction < 0: a, c = c, a
    seg = slice(min(a, c), max(a, c) + 1)
    dd = d[seg]; hh = h[seg]
    if len(dd) < 4: return None
    ang, g = slope_deg(dd, hh)
    if direction < 0: ang = -ang
    L = abs(dd[-1] - dd[0]); H = abs(hh[-1] - hh[0]) if direction > 0 else abs(hh[0] - hh[-1])
    n = len(dd)
    # lip: mean angle over last 1.0 ft before crest (top end of face)
    step = abs(dd[1] - dd[0]); k = max(2, int(1.0 / step))
    if direction > 0:
        lip = float(np.mean(ang[-k-2:-2])) if n > k + 3 else float(ang[-2])
    else:
        lip = float(np.mean(ang[2:k+2])) if n > k + 3 else float(ang[1])
    q = lambda f: float(ang[int(f * (n - 1))]) if direction > 0 else float(ang[int((1 - f) * (n - 1))])
    amax = float(np.max(ang))
    # transition radius: arc length / angle change from foot (<=2deg) to where angle reaches 90% of max
    th = np.radians(ang); idx = np.arange(n) if direction > 0 else np.arange(n)[::-1]
    i0 = idx[0]; i1 = idx[np.argmax(ang[idx] >= 0.9 * amax)]
    s = np.cumsum(np.r_[0, np.hypot(np.diff(dd), np.diff(hh))])
    dth = abs(th[i1] - th[i0]); R = abs(s[i1] - s[i0]) / dth if dth > 1e-3 else np.inf
    return dict(L=L, H=H, lip=lip, amax=amax, a25=q(.25), a50=q(.5), a75=q(.75), R=R)

def analyze(d, h, mode='sx', thr=0.35):
    base = base_line(d, h, mode)
    res = []
    for a, b in mounds(d, h, base, thr):
        r = h[a:b+1] - base[a:b+1]; hi = int(np.argmax(r)) + a
        top = h[hi]
        plat = np.where(h[a:b+1] > top - 0.25)[0] + a
        p0, p1 = plat.min(), plat.max()
        up = face_metrics(d, h, a, p0, +1); dn = face_metrics(d, h, p1, b, -1)
        res.append(dict(foot0=d[a], foot1=d[b], crest=d[hi], height=float(top - base[hi]), top_len=float(d[p1] - d[p0]),
                        length=float(d[b] - d[a]), up=up, down=dn, lip_x=float(d[p0]), land_x=float(d[p1])))
    return res, base
