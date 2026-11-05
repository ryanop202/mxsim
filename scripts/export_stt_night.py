"""Saint-Thibery NIGHT version (v21, asked by the user: "une version de nuit avec des poteaux tout autour du terrain qui eclairent").
Copies the day folder tracks/USLAND2026StThibery -> tracks/USLAND2026StThiberyNuit (same terrain, track, statues), then:
  - light poles (@USLAND2026SX1 lightpole model, copied) on the bank all around the arena, lamps aimed at the track;
  - lightmap (shading.ppm / shadingx2.ppm) re-baked: dark night base + the light of every pole (spot cone, distance falloff,
    terrain normal) - the game has no real-time lights on the ground, the lightmap is how the ground gets lit;
  - lighting: low moon-like sun for the bikes, dark ambient, dark blue fog, night sky (the day sky darkened + stars), no sun flare.
Run after export_stt.py: python scripts/export_stt_night.py"""
import os, sys, shutil, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
import numpy as np
from PIL import Image
from scipy.ndimage import zoom
import layouts_stt as LT, props_place as PP

S = 0.28975; DAY = 'USLAND2026StThibery'; NG = LT.NIGHT; NIGHT = NG['folder']
SRC, OUT = f'{ROOT}/tracks/{DAY}', f'{ROOT}/tracks/{NIGHT}'
POLE = dict(head=42.4, src=f'{ROOT}/tracks/USLAND2026SX1/statue', tilt=0.30)   # lamp height above the pole foot, aim tilt (rad, down)

def poles():
    """v28 (user): 3 poles on the L1 side (north) facing 3 on the whoops side (south), same x, low in the steep slope right
    behind the fence (DF = POLES['d'] ft from the dirt area), lamps aimed across the track."""
    PO = getattr(LT, 'POLES', None)
    if PO:
        x0, x1, z0, z1 = LT.ARENA; ox, oz = LT.STT_ORIGIN; DF = np.load(f'{ROOT}/build/stt_dist.npy'); out = []
        for k in range(PO['n']):
            x = x0 + (x1 - x0) * (k + 0.5) / PO['n']; col = DF[:, int(round(x + ox))]
            for zs, step, aim in ((z0, -1, (0.0, 1.0)), (z1, 1, (0.0, -1.0))):
                zi = int(round(zs + oz))
                while 0 < zi < len(col) - 1 and col[zi] < PO['d']: zi += step
                out.append(((x, zi - oz), aim))
        return out
    x0, x1, z0, z1 = LT.ARENA; d = NG['d']; out = []
    for i in range(1, NG['n_long'], 2):                                         # v22: one out of two (user)
        x = x0 + (x1 - x0) * (i + 0.5) / NG['n_long']
        out += [((x, z0 - d), (0.0, 1.0)), ((x, z1 + d), (0.0, -1.0))]
    out.append(((x1 + d, (z0 + z1) / 2), (-1.0, 0.0)))                          # east side middle
    sx0 = LT.GRASS_OUTSIDE['keep'][0][0]; zc = (z0 + z1) / 2
    out.append(((sx0 - d, zc), (1.0, 0.0)))                                    # behind the start, lights the gates
    for cx, cz, ax, az in ((x0, z0, 1, 1), (x1, z0, -1, 1), (x1, z1, -1, -1), (x0, z1, 1, -1)):   # corners
        out.append(((cx - ax * d * 0.8, cz - az * d * 0.8), (ax / np.sqrt(2), az / np.sqrt(2))))
    return out

def bake(H, P):
    """night lightmap (0-255): base + sum of the poles' light. Computed on a 2x coarser grid, then upsampled."""
    ox, oz = LT.STT_ORIGIN; h2 = H[::2, ::2]; s2 = 2 * S; n = h2.shape[0]
    gz, gx = np.gradient(h2, s2); nrm = np.dstack([-gx, np.ones_like(h2), -gz]); nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
    X = (np.arange(n) * s2)[None, :].repeat(n, 0); Z = (np.arange(n) * s2)[:, None].repeat(n, 1)
    moon = np.array([-0.30, 0.90, 0.30]); moon /= np.linalg.norm(moon)
    E = 14.0 + 18.0 * np.clip(nrm @ moon, 0, 1)                                 # dark night base + a little moonlight
    for (px, pz), (ax, az) in P:
        fx, fz = px + ox, pz + oz; gy = float(H[int(fz / S), int(fx / S)]); L = np.array([fx, gy + POLE['head'], fz])
        aim = np.array([ax * np.cos(POLE['tilt']), -np.sin(POLE['tilt']), az * np.cos(POLE['tilt'])])
        v = np.dstack([L[0] - X, L[1] - h2, L[2] - Z]); r = np.linalg.norm(v, axis=2); u = v / r[:, :, None]
        lam = np.clip((nrm * u).sum(2), 0, 1)                                   # surface facing the lamp
        cosang = -(u @ aim); spot = np.clip((cosang - 0.55) / 0.35, 0, 1) ** 1.5    # flood cone aimed at the far side of the track
        E += 8.0e6 * lam * spot / (r * r + 15000.0)                         # v22: 10 poles (was 20) -> stronger lamps
    E = 255.0 * (1 - np.exp(-E / 170.0))                                        # soft exposure (v24 key-light modulation removed)
    full = zoom(E, H.shape[0] / n, order=1)[:H.shape[0], :H.shape[1]]
    return np.clip(full, 0, 255).astype(np.uint8)

def night_sky(src, dst):
    """day sky darkened to a deep blue night, a few stars where the day image is sky (bluish, bright)."""
    a = np.asarray(Image.open(src).convert('RGB'), float); r = np.random.default_rng(abs(hash(os.path.basename(src))) % 2 ** 32)
    sky = (a[:, :, 2] > a[:, :, 0] + 8) & (a.mean(2) > 120)
    out = a * np.array([0.05, 0.06, 0.12]) + np.array([2, 3, 8])
    st = (r.random(sky.shape) < 0.0009) & sky; out[st] = r.uniform(160, 255, (st.sum(), 1))
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(dst, optimize=True)

GLOW = dict(lamps=[(-6.7, 44.1), (-2.0, 44.1), (2.3, 44.1), (6.9, 44.1)], x=1.9, size=5.0)   # lamp faces (local z, y) of lightpole.jm

def pads(H, P):
    """v22: a flat round pad under every pole (objects tilt with the ground): flat within pad[0] ft, blended out to pad[1] ft."""
    ox, oz = LT.STT_ORIGIN; PO = getattr(LT, 'POLES', None); r0, r1 = PO['pad'] if PO else NG['pad']; H = H.copy()
    for (px, pz), _ in P:
        fx, fz = px + ox, pz + oz; i0, j0 = int(fz / S), int(fx / S); k = int(r1 / S) + 2
        sl = (slice(i0 - k, i0 + k + 1), slice(j0 - k, j0 + k + 1)); ii, jj = np.mgrid[sl]
        r = np.hypot(ii * S - fz, jj * S - fx); t = np.clip((r - r0) / (r1 - r0), 0, 1); w = t * t * (3 - 2 * t)
        if PO:                                   # v28: platform CUT into the slope (level = lowest point of the flat disc)
            h0 = float(H[sl][r <= (r1 if PO.get('floor') else r0)].min()); hs = H[sl]   # v36: floor -> dug down to the floor
            H[sl] = np.where(hs > h0, h0 + (hs - h0) * w, hs)
        else:
            h0 = float(H[i0, j0]); H[sl] = h0 + (H[sl] - h0) * w
    return H

def glow_model(path_jm, path_png):
    """v22: light points: at each of the 4 lamps, 3 crossed double-sided quads with a radial glow (RGBA, alpha), in the pole's
    own coordinates (same position and angle as the pole statue). Not a real light: the ground light is baked in the lightmap."""
    n = 128; yy, xx = np.mgrid[0:n, 0:n]; r = np.hypot(xx - n / 2 + 0.5, yy - n / 2 + 0.5) / (n / 2)
    a = np.clip(1 - r, 0, 1) ** 1.6; rgb = np.dstack([np.full((n, n), 255), np.full((n, n), 246), 228 - 40 * r.clip(0, 1)])
    Image.fromarray(np.dstack([rgb, a * 255]).clip(0, 255).astype(np.uint8), 'RGBA').save(path_png)
    V, I = [], []; h = GLOW['size'] / 2
    def quad(c, e1, e2, nrm):
        for sg in (1, -1):
            b0 = len(V); nn = nrm * sg
            for (u, v) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                q = c + e1 * u * h + e2 * v * h; V.append((*q, *nn, (u + 1) / 2, (v + 1) / 2))
            I.extend([b0, b0 + 1, b0 + 2, b0, b0 + 2, b0 + 3] if sg > 0 else [b0, b0 + 2, b0 + 1, b0, b0 + 3, b0 + 2])
    X, Y, Z = np.eye(3)
    for z, y in GLOW['lamps']:
        c = np.array([GLOW['x'], y, z]); quad(c, Y, Z, X); quad(c, X, Y, Z); quad(c, X, Z, Y)
    L = ['JM1', '0.000000 0.000000 1.000000 1.000000 1.000000', f'{len(V)} {len(I) // 3}']
    L += [' '.join(f'{v:.6f}' for v in row) for row in V] + [str(i) for i in I] + ['']
    open(path_jm, 'w', newline='\n').write('\n'.join(L))

def main():
    H = np.load(f'{ROOT}/build/stt_H.npy').astype(np.float64); ox, oz = LT.STT_ORIGIN
    if os.path.exists(OUT): shutil.rmtree(OUT)
    shutil.copytree(SRC, OUT)
    for root, _, files in os.walk(OUT):                                         # self-contained: day refs -> night folder
        for f in files:
            pth = os.path.join(root, f)
            if f.split('.')[-1] in ('ppm', 'png', 'jm', 'shp', 'npy') or '.' in f and f.endswith('tilemap'): continue
            try: t = open(pth, encoding='utf-8').read()
            except Exception: continue
            if f'@{DAY}/' in t: open(pth, 'w', encoding='utf-8', newline='\n').write(t.replace(f'@{DAY}/', f'@{NIGHT}/'))
    open(f'{OUT}/desc', 'w', newline='\n').write(NG['desc'] + '\n')
    # poles
    for e in ('jm', 'png', '_norm.png', '_spec.png'):
        f = f"lightpole{'.' + e if e in ('jm', 'png') else e}"
        if os.path.exists(f"{POLE['src']}/{f}"): shutil.copy(f"{POLE['src']}/{f}", f'{OUT}/statue/{f}')
    # v43 (user): white poles. Every dark part of the texture turned white (relief kept from its brightness), the LED panel
    # (texture px 496..784 x 250..536) unchanged
    tx_ = np.asarray(Image.open(f'{OUT}/statue/lightpole.png').convert('RGB')).astype(float); lum_ = tx_.mean(2)
    Yt_, Xt_ = np.mgrid[0:tx_.shape[0], 0:tx_.shape[1]]
    led_ = (Xt_ >= 496) & (Xt_ <= 784) & (Yt_ >= 250) & (Yt_ <= 536) & (lum_ > 90)
    wh_ = np.clip(150 + lum_ * 1.3, 0, 250)[..., None] * np.array([1.0, 1.0, 1.01])
    tx_ = np.where(led_[..., None], tx_, wh_)
    Image.fromarray(np.clip(tx_, 0, 255).astype(np.uint8)).save(f'{OUT}/statue/lightpole.png')
    P = poles(); st = open(f'{OUT}/statues').read().rstrip('\n').split('\n')
    H = pads(H, P)                                                              # v22: flat pads under the poles (night terrain)
    hmin, hmax = float(H.min()) - 0.5, float(H.max()) + 0.5
    open(f'{OUT}/terrain.hf', 'w', newline='\n').write(f'11 {S:.6f} {hmin:.6f} {hmax:.6f}\n')
    Image.fromarray(np.round((H - hmin) / (hmax - hmin) * 65535).astype(np.uint16)).save(f'{OUT}/terrain.png')
    glow_model(f'{OUT}/statue/lamp_glow.jm', f'{OUT}/statue/lamp_glow.png')
    for (px, pz), (ax, az) in P:                                                # lamps face local +x -> world (cos a, -sin a)
        a = float(np.arctan2(-az, ax))
        st.append(f'[{px + ox:.6f} 0.000000 {pz + oz:.6f}] {a:.6f} @{NIGHT}/statue/lightpole.jm @{NIGHT}/statue/lightpole.png null')
        st.append(f'[{px + ox:.6f} 0.000000 {pz + oz:.6f}] {a:.6f} @{NIGHT}/statue/lamp_glow.jm @{NIGHT}/statue/lamp_glow.png null')
    open(f'{OUT}/statues', 'w', newline='\n').write('\n'.join(st) + '\n')
    SBD = getattr(LT, 'START_BOUDINS', None)
    if SBD:                                        # v50: nofrills.js (part of the track checksum, always run): start boudins
        rows_ = []                                 # shown until hide_after s after the gate drop, then sunk under the ground
        for i_, l_ in enumerate(st):
            if '/statue/startb_' in l_:
                v_ = l_.split(']')[0][1:].split(); rows_.append(f"[{i_}, {float(v_[0]):.3f}, {float(v_[2]):.3f}, {float(l_.split(']')[1].split()[0]):.6f}]")
        js_ = ['/*', 'USLAND 2026 Saint-Thibery (night): start-only boudins.',
               'Statues using the startb_*.png textures (no collision) stay until ' + str(SBD['hide_after']) + ' s after the gate drop,',
               'then they are moved under the ground. Before a gate drop (practice) they stay. Plain ASCII on purpose.', '*/', '',
               'var g_sb = [' + ', '.join(rows_) + '];', 'var g_sb_after = ' + str(SBD['hide_after']) + ';', 'var g_sb_hidden = -1;', 'var g_sb_t = -1.0;', '',
               'function sbSet(hide) {', '    var i, s;', '    for (i = 0; i < g_sb.length; i++) {', '        s = g_sb[i];',
               '        mx.move_statue(s[0], s[1], hide ? -200.0 : 0.0, s[2], s[3]);', '    }', '    g_sb_hidden = hide;', '}', '',
               'function startBoudins(seconds) {', '    var d = mx.get_gate_drop_time();', '    var hide = (d >= 0 && mx.seconds >= d + g_sb_after);',
               '    if (hide != g_sb_hidden || mx.seconds < g_sb_t || mx.seconds - g_sb_t > 1.0) {', '        sbSet(hide);', '        g_sb_t = mx.seconds;', '    }', '    if (startBoudinsPrev)', '        startBoudinsPrev(seconds);', '}', '',
               'var startBoudinsPrev = mx.frame_handler;', 'mx.frame_handler = startBoudins;', '']
        PY = getattr(LT, 'START_PYRO', None)
        if PY: js_ += start_pyro(PY, H, st)
        open(f'{OUT}/nofrills.js', 'w', newline='\n', encoding='ascii').write('\n'.join(js_))
        print('nofrills.js: start boudins', len(rows_))
    # lightmap
    sh = bake(H, P); N = H.shape[0]
    # v25: inside the fence the ground keeps the DAY lightmap (bumps exactly as by day), night outside, blended over 25 ft
    day = np.fromfile(f'{SRC}/shading.ppm', dtype=np.uint8, offset=len(f'P6\n{N} {N}\n255\n'.encode())).reshape(N, N, 3)[:, :, 0].astype(float)
    DF = np.load(f'{ROOT}/build/stt_dist.npy'); jj = np.arange(N) * S
    dN = DF[np.clip(jj.astype(int), 0, DF.shape[0] - 1)][:, np.clip(jj.astype(int), 0, DF.shape[1] - 1)]
    t = np.clip((dN - LT.FENCE['off']) / 25.0, 0, 1); w = t * t * (3 - 2 * t)
    sh = np.clip(day * (1 - w) + sh.astype(float) * w, 0, 255).astype(np.uint8)
    for nm, img in (('shading.ppm', sh), ('shadingx2.ppm', (sh // 2).astype(np.uint8))):
        with open(f'{OUT}/{nm}', 'wb') as fh: fh.write(f'P6\n{N} {N}\n255\n'.encode()); fh.write(np.repeat(img[:, :, None], 3, axis=2).tobytes())
    # sky + lighting
    os.makedirs(f'{OUT}/sky', exist_ok=True)
    lt = open(f'{SRC}/lighting').read(); sky = dict(re.findall(r'(sky_\w+) (@\S+)', lt))
    for k, ref in sky.items():
        src = f"{ROOT}/tracks/{ref[1:]}"; night_sky(src, f'{OUT}/sky/{os.path.basename(ref)}')
    # v26: one strong flood from the side, same angle as the day sun -> relief on the bumps and the bikes (the game has only
    # this one light; v22 put it overhead and weak: no shading, the bumps were hard to read)
    L = ['sun_vector [ -0.6528\t0.3590\t0.6671 ]', 'sun_color [ 0.85 0.85 0.80 ]', 'ambient [ 0.30 0.31 0.36 ]', 'fog [ 0.02 0.025 0.045 ] 0.00010']
    L += [f'{k} @{NIGHT}/sky/{os.path.basename(v)}' for k, v in sky.items()]
    L += ['flare_vector [ -0.30\t0.90\t0.30 ]', 'dynamic_lighting 1']
    open(f'{OUT}/lighting', 'w', newline='\n').write('\n'.join(L) + '\n')
    RF = getattr(LT, 'REFRAME', None)
    if RF: reframe(RF)
    MS = getattr(LT, 'MAP_SHOT', None)
    if MS: night_map(MS, H, RF)
    lit = sh[int((oz + 120) / S), int((ox + 180) / S)]
    return dict(pads=NG['pad'], poles=len(P), statues=len(st), shade_track_centre=int(lit), shade_min=int(sh.min()), shade_max=int(sh.max()))

def start_pyro(PY, H, st):
    """v60 (user): the SX1 / RaceTrack finish flames on the 2 burners of the START sign, fired at the gate drop (again after
    each New Race), with the flame sound at each torch. Billboards 0 and 1 (put first in the billboards file)."""
    import stt_ads as AD_
    src = f'{ROOT}/tracks/USLAND2026SX1/js'; os.makedirs(f'{OUT}/js/pyro', exist_ok=True); os.makedirs(f'{OUT}/js/sounds', exist_ok=True)
    for nm in ('finishflames', 'finishflames2'):
        if os.path.exists(f'{OUT}/js/pyro/{nm}'): shutil.rmtree(f'{OUT}/js/pyro/{nm}')
        shutil.copytree(f'{src}/pyro/{nm}', f'{OUT}/js/pyro/{nm}')
        open(f'{OUT}/js/pyro/{nm}.seq', 'w', newline='\n').write(open(f'{src}/pyro/{nm}.seq').read().replace('@USLAND2026SX1/', f'@{NIGHT}/'))
    a = np.fromfile(f'{src}/sounds/finishlineflame.raw', np.int16).astype(float) / 32768.0
    b = np.tanh(PY['boost'] * a) / np.tanh(PY['boost'])                       # louder: soft-limited gain (peak stays < 1)
    (np.clip(b, -1, 1) * 32000).astype(np.int16).tofile(f'{OUT}/js/sounds/startflame.raw')
    sg = [l for l in st if '/statue/start_sign.jm' in l][0]; v = sg.split(']')[0][1:].split(); bx, bz = float(v[0]), float(v[2])
    an = float(sg.split(']')[1].split()[0]); ux, uz = np.cos(an), -np.sin(an); fx, fz = np.sin(an), np.cos(an)   # local +x / +z in the world
    g0 = float(H[int(bz / S), int(bx / S)]); top = AD_.SIGN['top'] + AD_.SIGN['burner'][0]
    bb, pos = [], []
    for k, (sx, nm) in enumerate(((1, 'finishflames2'), (-1, 'finishflames'))):
        x_ = bx + ux * sx * PY['local_x'] + fx * AD_.SIGN['z']; z_ = bz + uz * sx * PY['local_x'] + fz * AD_.SIGN['z']
        y_ = g0 + top - float(H[int(z_ / S), int(x_ / S)])                    # billboard y = height above the ground under it
        bb.append(f'[{x_:.6f} {y_:.6f} {z_:.6f}] {PY["size"]:.6f} 1.000000 @{NIGHT}/js/pyro/{nm}.seq'); pos.append((x_, g0 + top, z_))
        print('pyro', nm, 'at', round(x_, 1), round(z_, 1), 'y', round(y_, 2))
    old = [l for l in open(f'{OUT}/billboards').read().split('\n') if l.strip()]
    open(f'{OUT}/billboards', 'w', newline='\n').write('\n'.join(bb + old) + '\n')
    P_ = f'@{NIGHT}/js'
    js = ['', '/* v60: START sign flames (billboards 0 and 1) + flame sound, fired at the gate drop (again after each New Race). */',
          'var g_py_snd = [];', 'var g_py_pos = [' + ', '.join(f'[{x:.2f}, {y:.2f}, {z:.2f}]' for x, y, z in pos) + '];',
          'var g_py_i;', 'for (g_py_i = 0; g_py_i < 2; g_py_i++) {',
          f'    g_py_snd[g_py_i] = mx.add_sound("{P_}/sounds/startflame.raw");',
          '    mx.set_sound_freq(g_py_snd[g_py_i], 44100);', '    mx.set_sound_vol(g_py_snd[g_py_i], 1.0);',
          '    mx.set_sound_pos(g_py_snd[g_py_i], g_py_pos[g_py_i][0], g_py_pos[g_py_i][1], g_py_pos[g_py_i][2]);', '}',
          f"var g_py_tex = [mx.read_texture('{P_}/pyro/finishflames2.seq'), mx.read_texture('{P_}/pyro/finishflames.seq')];",
          'var g_py_frames = 41;', 'var g_py_frame = -1;', 'var g_py_fired = -1;', 'var g_py_t = -1.0;',
          'mx.color_billboard(0, 1, 1, 1, 0);', 'mx.color_billboard(1, 1, 1, 1, 0);', '',
          'function pyroShow(a) {', '    mx.color_billboard(0, 1, 1, 1, a);', '    mx.color_billboard(1, 1, 1, 1, a);', '}', '',
          'function startPyro(seconds) {', '    var d = mx.get_gate_drop_time();', '    var k;',
          '    if (d < 0 || mx.seconds < d || mx.seconds < g_py_t) {', '        if (g_py_frame >= 0) pyroShow(0);',
          '        g_py_frame = -1;', '        if (d < 0 || mx.seconds < d) g_py_fired = -1;', '        g_py_t = mx.seconds;', '    }',
          '    else if (g_py_fired != d && mx.seconds < d + 3.0) {', '        g_py_fired = d;', '        g_py_frame = 0;', '        g_py_t = -1.0;',
          '        for (k = 0; k < 2; k++) mx.start_sound(g_py_snd[k]);', '    }',
          f'    if (g_py_frame >= 0 && mx.seconds - g_py_t >= {1.0 / PY["fps"]:.5f}) {{', '        g_py_t = mx.seconds;',
          '        if (g_py_frame < g_py_frames) {',
          '            for (k = 0; k < 2; k++) {', '                mx.begin_custom_frame(g_py_tex[k]);',
          '                mx.paste_custom_frame(g_py_tex[k], g_py_frame, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0);', '                mx.end_custom_frame(g_py_tex[k]);', '            }',
          '            if (g_py_frame == 0) pyroShow(1);', '            g_py_frame++;', '        } else {', '            pyroShow(0);', '            g_py_frame = -1;', '        }', '    }',
          '    if (startPyroPrev)', '        startPyroPrev(seconds);', '}', '',
          'var startPyroPrev = mx.frame_handler;', 'mx.frame_handler = startPyro;', '']
    return js

def reframe(RF):
    """v62 (user: minimap too small): cut the night terrain down to the square [x0, x0 + side] x [z0, z0 + side] (same
    4097 px, finer step) and shift every position by (-x0, -z0): terrain, lightmaps, tilemap, statues, billboards, decals,
    timing gates (only the centre of each line, never the gate vector), flaggers, nofrills.js (boudins, flame sounds)."""
    from scipy import ndimage as ndi_
    x0, z0, side = RF['x0'], RF['z0'], RF['side']; hf = open(f'{OUT}/terrain.hf').read().split()
    a_, b_ = float(hf[2]), float(hf[3]); T0 = np.asarray(Image.open(f'{OUT}/terrain.png'), np.float64)
    N = T0.shape[0]; S1 = side / (N - 1); g = np.arange(N) * S1
    cx_, cz_ = (x0 + g) / S, (z0 + g) / S                                     # new pixel -> old pixel
    ZZ, XX = np.meshgrid(cz_, cx_, indexing='ij')
    Hn = ndi_.map_coordinates(T0 / 65535 * (b_ - a_) + a_, [ZZ, XX], order=1, mode='nearest')
    hmin, hmax = float(Hn.min()) - 0.5, float(Hn.max()) + 0.5
    open(f'{OUT}/terrain.hf', 'w', newline='\n').write(f'{hf[0]} {S1:.6f} {hmin:.6f} {hmax:.6f}\n')
    Image.fromarray(np.round((Hn - hmin) / (hmax - hmin) * 65535).astype(np.uint16)).save(f'{OUT}/terrain.png')
    for nm in ('shading.ppm', 'shadingx2.ppm'):
        raw = open(f'{OUT}/{nm}', 'rb').read(); hd = f'P6\n{N} {N}\n255\n'.encode(); assert raw.startswith(hd), nm
        im_ = np.frombuffer(raw[len(hd):], np.uint8).reshape(N, N, 3)[:, :, 0].astype(float)
        sh_ = np.clip(np.round(ndi_.map_coordinates(im_, [ZZ, XX], order=1, mode='nearest')), 0, 255).astype(np.uint8)
        with open(f'{OUT}/{nm}', 'wb') as fh: fh.write(hd); fh.write(np.repeat(sh_[:, :, None], 3, axis=2).tobytes())
    tm = np.fromfile(f'{OUT}/tilemap', np.uint8); TN = int(round(np.sqrt(tm.size))); tm = tm.reshape(TN, TN)
    gt = (np.arange(TN) + 0.5) * side / TN; it = np.clip(((z0 + gt) / (2 * S)).astype(int), 0, TN - 1); jt = np.clip(((x0 + gt) / (2 * S)).astype(int), 0, TN - 1)
    tm[np.ix_(it, jt)].astype(np.uint8).tofile(f'{OUT}/tilemap')
    v3 = re.compile(r'\[\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\]'); v2 = re.compile(r'^\[\s*([-\d.]+)\s+([-\d.]+)\s*\]')
    def sh3(m):
        x, y, z = (float(m.group(i)) for i in (1, 2, 3))
        if x == 0.0 and z == 0.0: return m.group(0)                          # flaggers: unused flagger placeholder
        return f'[{x - x0:.6f} {m.group(2)} {z - z0:.6f}]'
    n_ = {}
    for nm in ('statues', 'billboards', 'timing_gates', 'flaggers'):
        out = []
        for l in open(f'{OUT}/{nm}').read().split('\n'):
            l2 = v3.sub(sh3, l, count=1); n_[nm] = n_.get(nm, 0) + (l2 != l); out.append(l2)
        open(f'{OUT}/{nm}', 'w', newline='\n').write('\n'.join(out))
    out = []
    for l in open(f'{OUT}/decals').read().split('\n'):
        m = v2.match(l)
        if m: l = f'[{float(m.group(1)) - x0:.6f} {float(m.group(2)) - z0:.6f}]' + l[m.end():]; n_['decals'] = n_.get('decals', 0) + 1
        out.append(l)
    open(f'{OUT}/decals', 'w', newline='\n').write('\n'.join(out))
    js = open(f'{OUT}/nofrills.js').read().split('\n')
    for i, l in enumerate(js):
        if l.startswith('var g_sb = ['):
            js[i] = re.sub(r'\[(\d+), ([-\d.]+), ([-\d.]+), ([-\d.]+)\]',
                           lambda m: f'[{m.group(1)}, {float(m.group(2)) - x0:.3f}, {float(m.group(3)) - z0:.3f}, {m.group(4)}]', l)
        if l.startswith('var g_py_pos = ['):
            js[i] = re.sub(r'\[([-\d.]+), ([-\d.]+), ([-\d.]+)\]',
                           lambda m: f'[{float(m.group(1)) - x0:.2f}, {m.group(2)}, {float(m.group(3)) - z0:.2f}]', l)
    open(f'{OUT}/nofrills.js', 'w', newline='\n', encoding='ascii').write('\n'.join(js))
    print('reframe: x %.0f..%.0f z %.0f..%.0f, step %.4f ft, shifted' % (x0, x0 + side, z0, z0 + side, S1), n_)

def night_map(MS, H, RF=None):
    """v61 (user): map.png from the user's in-game top view. The game stretches map.png over the WHOLE terrain, so the shot is
    resampled into terrain coordinates (similarity fitted on the pylons: rotation, scale, shift), kept inside the arena's
    rounded edge, transparent elsewhere; START written on the start grid."""
    from PIL import ImageDraw, ImageFont
    from scipy import ndimage as ndi_
    shot = np.asarray(Image.open(f"{ROOT}/{MS['img']}").convert('RGB')).astype(float)
    w = np.array([complex(*p[0]) for p in MS['pts']]); q = np.array([complex(*p[1]) for p in MS['pts']])
    (a, b), *_ = np.linalg.lstsq(np.c_[w, np.ones_like(w)], q, rcond=None)
    res = np.abs(q - (a * w + b)); print('map fit: %.3f px/ft, rot %.2f deg, max residual %.1f px' % (abs(a), np.degrees(np.angle(a)), res.max()))
    M = MS['M']; N = H.shape[0]
    fx0, fz0, side = (RF['x0'], RF['z0'], RF['side']) if RF else (0.0, 0.0, (N - 1) * S)     # v62: map over the (cut) terrain
    g = (np.arange(M) + 0.5) * side / M
    X, Z = np.meshgrid(fx0 + g, fz0 + g); p = a * (X + 1j * Z) + b
    px = np.clip(p.real, 0, shot.shape[1] - 1); py = np.clip(p.imag, 0, shot.shape[0] - 1)   # just outside the shot: edge pixels
    rgb = np.dstack([ndi_.map_coordinates(shot[:, :, c], [py, px], order=1) for c in range(3)])
    # v61b (user: crop inside the arena's rounded edge, straight): rounded rectangle, world-axis aligned, from the floor edge
    # seen in the shot (px) -> world
    inv = lambda u, v: ((complex(u, v) - b) / a)
    x0_, y0_, x1_, y1_ = MS['rect']; ym_, xm_ = (y0_ + y1_) / 2, (x0_ + x1_) / 2
    wx0, wx1 = inv(x0_, ym_).real, inv(x1_, ym_).real; wz0, wz1 = inv(xm_, y0_).imag, inv(xm_, y1_).imag; rr = MS['r_px'] / abs(a)
    cxr, czr, hx_, hz_ = (wx0 + wx1) / 2, (wz0 + wz1) / 2, (wx1 - wx0) / 2 - rr, (wz1 - wz0) / 2 - rr
    qx, qz = np.abs(X - cxr) - hx_, np.abs(Z - czr) - hz_
    sd = np.hypot(np.maximum(qx, 0), np.maximum(qz, 0)) + np.minimum(np.maximum(qx, qz), 0) - rr      # < 0 inside
    al = np.clip(-sd / MS['soft'] + 0.5, 0, 1)
    print('map frame: x %.1f-%.1f z %.1f-%.1f, corner r %.1f ft' % (wx0, wx1, wz0, wz1, rr))
    im = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), al * 255]).astype(np.uint8), 'RGBA')
    gx_, gz_ = LT.START_GATE[0] + LT.STT_ORIGIN[0], LT.START_GATE[1] + LT.STT_ORIGIN[1]
    # v61c (user): START smaller, along the grid (reads top -> bottom), inside the start descent (box in world ft)
    k = M / side; bx0, bz0, bx1, bz1 = MS['text_box']; up = 4
    fnt = ImageFont.truetype('C:/Windows/Fonts/impact.ttf', 200); sw = 14
    tb = ImageDraw.Draw(Image.new('L', (1, 1))).textbbox((0, 0), MS['text'], font=fnt, stroke_width=sw)
    t = Image.new('RGBA', (tb[2] - tb[0], tb[3] - tb[1]), (0, 0, 0, 0))
    ImageDraw.Draw(t).text((-tb[0], -tb[1]), MS['text'], font=fnt, fill=(255, 255, 255, 255), stroke_width=sw, stroke_fill=(0, 0, 0, 255))
    t = t.rotate(90, expand=True)                                    # map: x right, z down -> reads from the bottom up (v61d, user)
    bw, bh = (bx1 - bx0) * k, (bz1 - bz0) * k; f_ = min(bw / t.width, bh / t.height)
    t = t.resize((max(1, int(t.width * f_)), max(1, int(t.height * f_))), Image.LANCZOS)
    cx, cy = ((bx0 + bx1) / 2 - fx0) * k, ((bz0 + bz1) / 2 - fz0) * k
    im.alpha_composite(t, (int(round(cx - t.width / 2)), int(round(cy - t.height / 2))))
    if MS.get('title'):                                               # v62 (user): signature over the arena (like other maps)
        f2 = ImageFont.truetype(MS['title_font'], 200); sw2 = 10
        tb = ImageDraw.Draw(Image.new('L', (1, 1))).textbbox((0, 0), MS['title'], font=f2, stroke_width=sw2)
        t2 = Image.new('RGBA', (tb[2] - tb[0], tb[3] - tb[1]), (0, 0, 0, 0))
        ImageDraw.Draw(t2).text((-tb[0], -tb[1]), MS['title'], font=f2, fill=(255, 255, 255, 255), stroke_width=sw2, stroke_fill=(0, 0, 0, 255))
        X0, Z0, X1, Z1 = MS['title_box']; f_ = min((X1 - X0) * k / t2.width, (Z1 - Z0) * k / t2.height)
        t2 = t2.resize((max(1, int(t2.width * f_)), max(1, int(t2.height * f_))), Image.LANCZOS)
        im.alpha_composite(t2, (int(round(((X0 + X1) / 2 - fx0) * k - t2.width / 2)), int(round(((Z0 + Z1) / 2 - fz0) * k - t2.height / 2))))
    im.save(f'{OUT}/map.png'); print('map.png from the top view, START in', MS['text_box'], 'size %.0f x %.0f ft' % (t.width / k, t.height / k))

if __name__ == '__main__':
    print(main())
