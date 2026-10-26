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
    """pole feet (local x, z) on the bank, d ft outside the dirt arena box, and the inward aim (unit, local)."""
    x0, x1, z0, z1 = LT.ARENA; d = NG['d']; out = []
    for i in range(NG['n_long']):
        x = x0 + (x1 - x0) * (i + 0.5) / NG['n_long']
        out += [((x, z0 - d), (0.0, 1.0)), ((x, z1 + d), (0.0, -1.0))]
    for i in range(NG['n_short']):
        z = z0 + (z1 - z0) * (i + 0.5) / NG['n_short']
        out.append(((x1 + d, z), (-1.0, 0.0)))
        if i != NG['n_short'] // 2: out.append(((x0 - d, z), (1.0, 0.0)))   # west side: not behind the start area (middle)
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
        E += 4.5e6 * lam * spot / (r * r + 15000.0)
    E = 255.0 * (1 - np.exp(-E / 170.0))                                        # soft exposure: no burnt white near the poles
    full = zoom(E, H.shape[0] / n, order=1)[:H.shape[0], :H.shape[1]]
    return np.clip(full, 0, 255).astype(np.uint8)

def night_sky(src, dst):
    """day sky darkened to a deep blue night, a few stars where the day image is sky (bluish, bright)."""
    a = np.asarray(Image.open(src).convert('RGB'), float); r = np.random.default_rng(abs(hash(os.path.basename(src))) % 2 ** 32)
    sky = (a[:, :, 2] > a[:, :, 0] + 8) & (a.mean(2) > 120)
    out = a * np.array([0.05, 0.06, 0.12]) + np.array([2, 3, 8])
    st = (r.random(sky.shape) < 0.0009) & sky; out[st] = r.uniform(160, 255, (st.sum(), 1))
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(dst, optimize=True)

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
    P = poles(); st = open(f'{OUT}/statues').read().rstrip('\n').split('\n')
    for (px, pz), (ax, az) in P:                                                # lamps face local +x -> world (cos a, -sin a)
        a = float(np.arctan2(-az, ax))
        st.append(f'[{px + ox:.6f} 0.000000 {pz + oz:.6f}] {a:.6f} @{NIGHT}/statue/lightpole.jm @{NIGHT}/statue/lightpole.png null')
    open(f'{OUT}/statues', 'w', newline='\n').write('\n'.join(st) + '\n')
    # lightmap
    sh = bake(H, P); N = H.shape[0]
    for nm, img in (('shading.ppm', sh), ('shadingx2.ppm', (sh // 2).astype(np.uint8))):
        with open(f'{OUT}/{nm}', 'wb') as fh: fh.write(f'P6\n{N} {N}\n255\n'.encode()); fh.write(np.repeat(img[:, :, None], 3, axis=2).tobytes())
    # sky + lighting
    os.makedirs(f'{OUT}/sky', exist_ok=True)
    lt = open(f'{SRC}/lighting').read(); sky = dict(re.findall(r'(sky_\w+) (@\S+)', lt))
    for k, ref in sky.items():
        src = f"{ROOT}/tracks/{ref[1:]}"; night_sky(src, f'{OUT}/sky/{os.path.basename(ref)}')
    L = ['sun_vector [ -0.30\t0.90\t0.30 ]', 'sun_color [ 0.55 0.55 0.52 ]', 'ambient [ 0.20 0.21 0.26 ]', 'fog [ 0.02 0.025 0.045 ] 0.00010']
    L += [f'{k} @{NIGHT}/sky/{os.path.basename(v)}' for k, v in sky.items()]
    L += ['flare_vector [ -0.30\t0.90\t0.30 ]', 'dynamic_lighting 1']
    open(f'{OUT}/lighting', 'w', newline='\n').write('\n'.join(L) + '\n')
    lit = sh[int((oz + 120) / S), int((ox + 180) / S)]
    return dict(poles=len(P), statues=len(st), shade_track_centre=int(lit), shade_min=int(sh.min()), shade_max=int(sh.max()))

if __name__ == '__main__':
    print(main())
