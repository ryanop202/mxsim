"""Saint-Georges v30 (user: "regarde ... la nuit, comment elle est faite ... si tu peux le recreer, fais-le"): night in the
style of the Peneman Moon 2019 track (studied from its files: lighting + ONE huge black decal over the whole track whose alpha
is the darkness - clear pools of light under the poles, and every object casting one shadow per lamp = star-shaped shadows;
warm 'sun' and blue ambient for the bikes, black fog, a flare billboard on every lamp).

overlay(H, S, poles, statues, OUT, NIGHT, DF, fence_off, cfg) -> decal line (and decal/night_overlay.png)
  poles   : [((x, z) world, (ax, az) aim, head ft)]
  statues : statue lines of the track (occluders recognised by model name)
  alpha (darkness) = a_max - k * light^gamma, clipped [a_min, a_max]; light = sum of the pole spots (cone, 1/r^2, incidence)
  each one multiplied by (1 - strength * shadow mask of that pole); faded out past the fence (the night lightmap is used
  there, as before), so there is no seam.
glow_billboards(poles, lamps, head, size, NIGHT) -> billboard lines (+ billboard/lamp_flare.png)
person_js(index, ...) -> nofrills.js text: billboard `index` hidden until the leader starts the last lap (white flag), then shown.
Image orientation of a decal at angle 0 (checked on the Peneman overlay against its statues): columns = +x, rows = +z."""
import os, re
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

# occluders: model name -> (length along local x, width along local z, height, shadow strength)
OCC = {'boudin_logo3': (18.0, 2.6, 2.3, 0.75), 'boudin_logo': (6.0, 2.6, 2.3, 0.75), 'bale_straw': (4.6, 1.75, 1.6, 0.8),
       'bale_hay': (4.6, 1.9, 1.7, 0.8), 'hay_block': (8.5, 2.0, 4.9, 0.85), 'pylon_round': (2.0, 2.0, 4.7, 0.7),
       'pole_concrete': (1.6, 1.6, 44.0, 0.8), 'rider_gate': (8.0, 6.0, 9.0, 0.7), 'start_tarp': (90.0, 0.5, 10.5, 0.85),
       'f50_cylinder': (2.0, 2.0, 7.0, 0.7), 'fence_heras': (11.48, 0.3, 6.4, 0.22), 'flag_cage': (4.0, 4.0, 9.0, 0.5),
       'ramp_50': (18.0, 4.0, 9.0, 0.7), 'scaffold_sign': (17.7, 1.2, 45.0, 0.55), 'cone_orange': (1.2, 1.2, 2.3, 0.6)}

def _statues(lines):
    out = []
    for l in lines:
        m = re.match(r'\[([-\d.]+) ([-\d.]+) ([-\d.]+)\] ([-\d.]+) (\S+)', l)
        if not m: continue
        nm = os.path.basename(m.group(5)).rsplit('.', 1)[0]
        if nm in OCC: out.append((float(m.group(1)), float(m.group(3)), float(m.group(4)), OCC[nm]))
    return out

def overlay(H, S, poles, statues, OUT, NIGHT, DF, fence_off, cfg):
    N = cfg.get('px', 2048); cx, cz = cfg['centre']; SZ = cfg['size']; px = SZ / N
    g = cz - SZ / 2 + (np.arange(N) + 0.5) * px; gx = cx - SZ / 2 + (np.arange(N) + 0.5) * px
    Z, X = np.meshgrid(g, gx, indexing='ij')
    hgt = H[np.clip((Z / S).astype(int), 0, H.shape[0] - 1), np.clip((X / S).astype(int), 0, H.shape[1] - 1)]
    occ = _statues(statues); tilt = cfg.get('tilt', 0.30); light = np.zeros((N, N))
    to_px = lambda x, z: ((x - (cx - SZ / 2)) / px, (z - (cz - SZ / 2)) / px)
    for pl_ in poles:
        (lx, lz), (ax, az), head = pl_[:3]; gain = pl_[3] if len(pl_) > 3 else 1.0
        gy = float(H[int(lz / S), int(lx / S)]); Ly = gy + head
        aim = np.array([ax * np.cos(tilt), -np.sin(tilt), az * np.cos(tilt)])
        vx, vy, vz = lx - X, Ly - hgt, lz - Z; r = np.sqrt(vx * vx + vy * vy + vz * vz)
        cosang = -(vx * aim[0] + vy * aim[1] + vz * aim[2]) / r
        spot = np.clip((cosang - cfg['cone'][0]) / (cfg['cone'][1] - cfg['cone'][0]), 0, 1) ** 1.2
        E = gain * spot * (vy / r) / (r * r + cfg.get('r0', 900.0))
        # shadows of every occluder away from this lamp
        sm = Image.new('L', (N, N), 0); d = ImageDraw.Draw(sm)
        for (ox, oz, A, (Lx, Wz, Hh, st)) in occ:
            if abs(ox - lx) < 1.5 and abs(oz - lz) < 1.5: continue           # the pole itself
            ux, uz = np.cos(A), -np.sin(A)                                       # statue local +x in the world
            nL = max(1, int(np.ceil(Lx / 1.5)))
            for t in np.linspace(-Lx / 2, Lx / 2, nL + 1) if Lx > 2.5 else (0.0,):
                sx, sz = ox + ux * t, oz + uz * t
                dx, dz = sx - lx, sz - lz; rr = np.hypot(dx, dz) + 1e-6
                L_ = min(cfg.get('shadow_max', 70.0), rr * Hh / max(head - Hh, 4.0))
                ex, ez = sx + dx / rr * L_, sz + dz / rr * L_
                wpx = max(1.2, max(Wz, 0.9 if Lx > 2.5 else Lx) * cfg.get('shadow_w', 1.0) / px)
                d.line([to_px(sx, sz), to_px(ex, ez)], fill=int(255 * st * cfg.get('shadow_k', 1.0)), width=int(round(wpx)))
        smf = nd.gaussian_filter(np.asarray(sm, float) / 255, 0.8)
        light += E * (1 - smf)
    dirt = DF[np.clip(Z.astype(int), 0, DF.shape[0] - 1), np.clip(X.astype(int), 0, DF.shape[1] - 1)]
    ref = np.percentile(light[dirt <= 0.5], cfg.get('ref_pct', 60))
    Ln = light / (ref + 1e-12)
    a = np.clip(cfg['a_max'] - cfg['k'] * Ln ** cfg.get('gamma', 0.8), cfg['a_min'], cfg['a_max'])
    t = np.clip((dirt - fence_off) / cfg.get('blend', 25.0), 0, 1); w = t * t * (3 - 2 * t)          # same blend as the lightmap: 0 inside
    a = a * (1 - w)
    edge = np.minimum.reduce([np.arange(N)[:, None].repeat(N, 1), np.arange(N)[None, :].repeat(N, 0)])
    edge = np.minimum(edge, edge[::-1, ::-1]); a *= np.clip(edge / 12.0, 0, 1)        # no hard border at the square edge
    rgba = np.zeros((N, N, 4), np.uint8); rgba[..., 3] = np.clip(a * 255, 0, 255).astype(np.uint8)
    rgba[..., :3] = np.array(cfg.get('tint', (2, 3, 8)), np.uint8)
    os.makedirs(f'{OUT}/decal', exist_ok=True); Image.fromarray(rgba, 'RGBA').save(f'{OUT}/decal/night_overlay.png', optimize=True)
    inside = dirt <= 0.5
    print('night overlay: alpha on the dirt mean %.2f, p10 %.2f, p90 %.2f' % (a[inside].mean(), np.percentile(a[inside], 10), np.percentile(a[inside], 90)))
    return f'[{cx:.6f} {cz:.6f}] 0.000000 {SZ:.6f} 1.000000 @{NIGHT}/decal/night_overlay.png', a

def flare_texture(path, n=256, k=1.0):
    """lamp flare as Peneman's lights.png: hot white core, soft warm halo, a few thin streaks (RGBA)."""
    yy, xx = np.mgrid[0:n, 0:n]; dx, dy = (xx - n / 2 + 0.5) / (n / 2), (yy - n / 2 + 0.5) / (n / 2); r = np.hypot(dx, dy)
    core = np.clip(1 - r / 0.16, 0, 1) ** 1.2; halo = np.clip(1 - r, 0, 1) ** 2.6 * 0.75
    ang = np.arctan2(dy, dx); streak = (np.abs(np.cos(ang * 2)) ** 60 + np.abs(np.cos(ang * 2 + np.pi / 4)) ** 120 * 0.5) * np.clip(1 - r, 0, 1) ** 1.6 * 0.6
    a = np.clip((core + halo + streak) * k, 0, 1)
    rgb = np.dstack([np.full((n, n), 255.0), 250 - 20 * r.clip(0, 1), 225 - 70 * r.clip(0, 1)])
    Image.fromarray(np.dstack([rgb, a * 255]).clip(0, 255).astype(np.uint8), 'RGBA').save(path)

def glow_billboards(poles, lamps, lamp_x, size, NIGHT, OUT, k=1.0):
    os.makedirs(f'{OUT}/billboard', exist_ok=True); flare_texture(f'{OUT}/billboard/lamp_flare.png', k=k); out = []
    for (px_, pz_), (ax, az), _h in poles:
        # pole statue local +x -> world aim (ax, az); local z -> (ax, az) turned 90 deg: world (-az, ax) * ... (statue: +z -> (sin A, cos A))
        a = float(np.arctan2(-az, ax)); zx, zz = np.sin(a), np.cos(a)
        for lz, ly in lamps:
            x, z = px_ + ax * lamp_x + zx * lz, pz_ + az * lamp_x + zz * lz
            out.append(f'[{x:.6f} {ly - size / 2:.6f} {z:.6f}] {size:.6f} 1.000000 @{NIGHT}/billboard/lamp_flare.png')
    return out

def person_js(index):
    return '\n'.join([
        '/*', 'USLAND 2026 Saint Georges by bazo: the person on top of the freestyle landing (billboard ' + str(index) + ')',
        'shows up when the leader starts the last lap (white flag) and stays until the end; hidden before (and in practice).',
        'Same last-lap logic as the Anaheim finish flagger. Plain ASCII on purpose.', '*/', '',
        'var g_ps_index = ' + str(index) + ';', 'var g_ps_drop = -1;', 'var g_ps_last = 1000000;',
        'var g_ps_laps = mx.get_finish_laps();', 'var g_ps_time = mx.get_finish_time();', 'var g_ps_on = -1;', '',
        'mx.color_billboard(g_ps_index, 1, 1, 1, 0);', '',
        'function psUpdate() {', '    var p, l, show = 0;',
        '    if (g_ps_drop < 0)', '        g_ps_drop = mx.get_gate_drop_time();',
        '    if (g_ps_drop >= 0 && mx.seconds >= g_ps_drop) {',
        '        p = mx.get_running_order_position(0);',
        '        if (g_ps_last == 1000000) {',
        '            if (g_ps_time == 0)', '                g_ps_last = g_ps_laps;',
        '            else if (mx.seconds >= g_ps_drop + g_ps_time)', '                g_ps_last = mx.index_to_lap(p) + 1 + g_ps_laps;', '        }',
        '        l = mx.index_to_lap(p + 1);', '        if (l >= g_ps_last - 1)', '            show = 1;', '    }',
        '    if (show != g_ps_on) {', '        mx.color_billboard(g_ps_index, 1, 1, 1, show);', '        g_ps_on = show;', '    }', '}', '',
        'function personFrame(seconds) {', '    psUpdate();', '    if (personPrev)', '        personPrev(seconds);', '}', '',
        'var personPrev = mx.frame_handler;', 'mx.frame_handler = personFrame;', ''])
