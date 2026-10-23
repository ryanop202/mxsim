"""Rough lap-time estimate (point-mass speed model) - an ESTIMATE, not a measurement in MX Simulator."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np; sys.path.insert(0, ROOT + '/scripts')
FT = 0.3048; g = 9.81
def estimate(path, vmax, a0=7.5, brake=8.0, alat=1.0, sand=None, ds=1.0):
    smp = path.samples(ds); s = smp['s'] * FT; n = len(s); d = ds * FT
    R = np.full(n, 1e9)
    from scipy.ndimage import uniform_filter1d
    for gseg in path.segs:
        m = (smp['s'] >= gseg['s0']) & (smp['s'] < gseg['s0'] + gseg['L'])
        if gseg['kind'] == 'T': R[m] = gseg['r'] * FT
        elif gseg['kind'] == 'P':           # stamp riding line: radius from its curvature (10 ft smoothing)
            th = np.unwrap(smp['th'][m]); k = np.abs(np.gradient(uniform_filter1d(th, 11, mode='nearest'), ds))
            R[m] = 1.0 / np.maximum(k, 1e-4) * FT
            if sand is None: sand = np.zeros(n, bool)
            sand = sand | m
    vlim = np.minimum(vmax, np.sqrt(alat * g * R))
    vm = np.full(n, vmax); am = np.full(n, a0)
    if sand is not None: vm[sand] *= 0.85; am[sand] *= 0.7; vlim = np.minimum(vlim, vm)
    v = vlim.copy()
    for _ in range(2):  # periodic: two passes
        for i in range(1, 2 * n):
            k = i % n; p = (i - 1) % n
            v[k] = min(vlim[k], np.sqrt(v[p] ** 2 + 2 * am[k] * max(1 - v[p] / vm[k], 0) * d))
        for i in range(2 * n - 2, -1, -1):
            k = i % n; q = (i + 1) % n
            v[k] = min(v[k], np.sqrt(v[q] ** 2 + 2 * brake * d))
    t = np.sum(d / np.maximum(v, 1.0))
    return t, float(np.mean(v)), float(v.max())
def _fmt(x): return f'{int(x//60)}:{x%60:04.1f}'


def run_sx():
    """SX compound (current): writes build/laptime.json."""
    import layouts_sx as LS
    out = {}
    for name, p in (('SX1', LS.sx1()), ('SX2', LS.sx2()), ('SX3', LS.sx3())):
        ts = [estimate(p, 20.0, alat=al)[0] for al in (1.6, 1.3, 1.0)]
        t, vavg, vtop = estimate(p, 20.0, alat=1.3)
        out[name] = dict(length_ft=p.s, length_m=p.s * FT, est_lap_s=t, est_range_s=[ts[0], ts[2]], avg_kmh=vavg * 3.6)
        print(f'{name}: {p.s:.0f} ft ({p.s*FT:.0f} m)  estimated lap {_fmt(t)}  (range {_fmt(ts[0])} - {_fmt(ts[2])})  avg {vavg*3.6:.0f} km/h')
    json.dump(out, open(ROOT + '/build/laptime.json', 'w'))


def run_mx_legacy():
    """v1 MX compound (abandoned): writes legacy_mx/build/laptime.json."""
    import layouts
    out = {}
    mx = layouts.mx(); smp = mx.samples(1.0)
    sand = np.zeros(len(smp['s']), bool)
    for gseg in mx.segs:
        if gseg['kind'] == 'S' and 'sand' in gseg['tag']: sand |= (smp['s'] >= gseg['s0'] - 40) & (smp['s'] <= gseg['s0'] + gseg['L'] + 40)
    for name, p, vmax, sd in (('MX', mx, 27.0, sand), ('SX1', layouts.sx1(), 20.0, None), ('SX2', layouts.sx2(), 20.0, None)):
        ts = [estimate(p, vmax, sand=sd, alat=al)[0] for al in (1.6, 1.3, 1.0)]
        t, vavg, vtop = estimate(p, vmax, sand=sd, alat=1.3)
        out[name] = dict(length_ft=p.s, length_m=p.s * FT, est_lap_s=t, est_range_s=[ts[0], ts[2]], avg_kmh=vavg * 3.6)
        print(f'{name}: {p.s:.0f} ft  estimated lap {_fmt(t)}')
    _os.makedirs(ROOT + '/legacy_mx/build', exist_ok=True)
    json.dump(out, open(ROOT + '/legacy_mx/build/laptime.json', 'w'), indent=1)


if __name__ == '__main__':
    run_mx_legacy() if 'mx' in sys.argv[1:] else run_sx()
