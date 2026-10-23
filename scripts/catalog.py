"""Build obstacle catalog from all reference tracks: as-built profiles along gradient lines that match the heightmap."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np; sys.path.insert(0,ROOT + '/scripts')
from mxs import *; from profiles import *
R=REF + '/'
REFS={'SX_Detroit':(R+'JGSX2026TestTracks/JGSX2026Detroit','sx'),'SX_Custom':(R+'JGSX2026TestTracks/JGSX2026Custom','sx'),
 'SX_Arlington':(R+'JGSX2026TestTracks/JGSX2026Arlington','sx'),'SX_Glendale':(R+'JGSX2026TestTracks/JGSX2026Glendale','sx'),
 'SX_Cleveland':(R+'JGSX2026TestTracks/JGSX2026Custom1','sx'),'MX_DrDew':(R+'JGMXDrDew/JGMXDrDew','mx'),'MX_DesertSand':(R+'JGMXDesertSand/JGMXDesertSand','mx')}

def cross_section(T, x, z, ux, uz, half=30.0, step=0.1):
    vx, vz = -uz, ux; t = np.arange(-half, half + 1e-9, step)
    return t, T.h(x + vx * t, z + vz * t)

def xs_metrics(t, h, base):
    r = h - base; c = len(t)//2; top = r[c]
    if top < 0.5: return None
    # walk outwards from centre
    def edge(level, sgn):
        i = c
        while 0 < i < len(t)-1 and r[i] > level: i += sgn
        return abs(t[i])
    top_w = edge(top - 0.25, -1) + edge(top - 0.25, +1)
    foot_w = edge(0.1 * top, -1) + edge(0.1 * top, +1)
    w50 = edge(0.5 * top, -1) + edge(0.5 * top, +1)
    side = (foot_w - top_w) / 2
    return dict(top_w=top_w, w50=w50, foot_w=foot_w, side_run=side, side_deg=float(np.degrees(np.arctan(top / max(side, 0.1)))))

out = []
for ref, (f, mode) in REFS.items():
    T = Track(f, 'xz'); seen = set()
    for gi, g in enumerate(T.gradients):
        P = g['pts']
        if len(P) < 3 or g['len'] < 8: continue
        key = tuple(np.round(np.r_[g['a'], g['b']], 0))
        if key in seen: continue
        d, h = T.line(*g['a'], *g['b'], step=0.1)
        ref_h = np.interp(d, P[:, 1], P[:, 2])
        if mode == 'mx':  # gradients on MX may be absolute or relative: compare detrended shapes
            hd = h - np.polyval(np.polyfit(d, h, 1), d); rd = ref_h - np.polyval(np.polyfit(d, ref_h, 1), d)
            if hd.std() < 0.3: continue
            corr = np.corrcoef(hd, rd)[0, 1] if rd.std() > 0.05 else 0; err = np.median(np.abs(hd - rd))
        else:
            if h.std() < 0.1: continue
            corr = np.corrcoef(h, ref_h)[0, 1] if ref_h.std() > 0.05 else 0; err = np.median(np.abs(h - ref_h))
        if not (corr > 0.93 and err < 0.45): continue
        seen.add(key)
        ux, uz = (g['b'][0] - g['a'][0]) / g['len'], (g['b'][1] - g['a'][1]) / g['len']
        res, base = analyze(d, h, mode, thr=0.35 if mode == 'sx' else 0.6)
        for k, m in enumerate(res):
            x = g['a'][0] + ux * m['crest']; z = g['a'][1] + uz * m['crest']
            t, hx = cross_section(T, x, z, ux, uz, half=35 if mode == 'mx' else 25)
            bi = int(np.searchsorted(d, m['crest'])); xs = xs_metrics(t, hx, base[min(bi, len(base)-1)])
            i0, i1 = np.searchsorted(d, m['foot0'] - 1.0), np.searchsorted(d, m['foot1'] + 1.0)
            prof = (h[i0:i1] - base[i0:i1])
            out.append(dict(ref=ref, file=_os.path.relpath(f, REF) + '/terrain.png', grad=gi, idx=k, mode=mode,
                            a=list(g['a']), b=list(g['b']), crest_xz=[float(x), float(z)], corr=float(corr), err=float(err),
                            **{kk: v for kk, v in m.items() if kk not in ('up', 'down')}, up=m['up'], down=m['down'], xs=xs,
                            prof_d0=float(d[i0]), prof=np.round(prof, 3).tolist()))
    print(ref, 'matched gradients:', len(seen), 'mounds so far', len(out))
json.dump(out, open(ROOT + '/analysis/catalog_raw.json', 'w'))
