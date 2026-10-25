"""v12 aperçu 3D des objets USLAND (props_usland.py) avant de les mettre en jeu : une page HTML autonome (three.js) avec
  - Paddock : hospitality + pick-ups + bannières de sponsors, un pilote de 6 ft pour l'échelle ;
  - Arrivée SX1 / SX2 / SX3 : le portique posé sur la vraie porte d'arrivée (terrain réel autour, lu dans tracks/) ;
  - Départ SX1 : les grates derrière les 22 grilles (grilles JGSX remplacées par des cadres rouges simples, juste pour voir).
Le placement de l'arche est celui que dress_sx.py utilisera (props_place.arch_pose). Ce n'est PAS un rendu du jeu.
Run: python3 scripts/preview_props.py [dossier des modèles] [page.html]"""
import os, sys, json, base64, io
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
import numpy as np
from PIL import Image
from names import FOLDERS
import props_usland as PU
import props_place as PP

def jm_arrays(path):
    L = open(path).read().splitlines()                                          # JM1 (ours) or JM2 (JGSX: name + material lines)
    k = next(i for i, l in enumerate(L) if i > 0 and len(l.split()) == 2 and all(t.isdigit() for t in l.split())); nv, nt = map(int, L[k].split())
    V = np.array([[float(t) for t in l.split()[:8]] for l in L[k + 1:k + 1 + nv]], np.float32)
    I = np.array([int(l) for l in L[k + 1 + nv:k + 1 + nv + 3 * nt]], np.uint32)
    b = lambda a: base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()
    return dict(pos=b(V[:, 0:3]), nrm=b(V[:, 3:6]), uv=b(V[:, 6:8]), idx=b(I))

def png_uri(path, max_side=2048):
    im = Image.open(path).convert('RGB')
    if max(im.size) > max_side: im = im.resize((max_side, max_side * im.size[1] // im.size[0]))
    buf = io.BytesIO(); im.save(buf, 'JPEG', quality=88); return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()   # preview only

def terrain_patch(T, cx, cz, half, step=3):
    """heights + colours (shading x ground type) around (cx, cz); returns grid origin, spacing and base64 arrays."""
    S = T['S']; i0 = int(max(0, (cz - half) / S)); i1 = int(min(T['H'].shape[0] - 1, (cz + half) / S))
    j0 = int(max(0, (cx - half) / S)); j1 = int(min(T['H'].shape[1] - 1, (cx + half) / S))
    h = T['H'][i0:i1 + 1:step, j0:j1 + 1:step].astype(np.float32)
    sh = T['shade'][i0:i1 + 1:step, j0:j1 + 1:step].astype(np.float32) / 255.0
    ti = T['tiles'][(np.arange(i0, i1 + 1, step) // 2).clip(0, 2047)][:, (np.arange(j0, j1 + 1, step) // 2).clip(0, 2047)]
    base = np.tile(np.array([0.50, 0.38, 0.26], np.float32), h.shape + (1,))
    base[np.isin(ti, (4, 5, 6, 7))] = (0.78, 0.68, 0.50)        # sand
    base[ti == 8] = (0.55, 0.55, 0.56)                           # concrete road
    col = (base * (0.35 + 0.85 * sh[..., None])).clip(0, 1)
    b = lambda a: base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()
    return dict(x0=j0 * S, z0=i0 * S, d=S * step, nx=h.shape[1], nz=h.shape[0], h=b(h), c=b((col * 255).astype(np.uint8)))

def main(models, out):
    T = PP.load_terrain(); scenes = {}; report = {}
    for key in ('SX1', 'SX2', 'SX3'):
        A = PP.arch_pose(key, T)
        report[key] = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in A.items() if k not in ('pillars',)}
        scenes['arch_' + key] = dict(terrain=terrain_patch(T, A['cx'], A['cz'], 80),
                                     objs=[dict(m=PP.ARCH_MODEL[key], t=PP.ARCH_MODEL[key], x=A['x'], y=A['y'], z=A['z'], a=A['a'])],
                                     cam=[A['cx'], A['crest'] + 6, A['cz']], back=A['f'], info=dict(A, x=A['cx'], z=A['cz']))
    G = PP.start_gates('SX1')
    objs = [dict(m='start_grate', t='start_grate', x=x, y=y, z=z, a=a) for x, y, z, a in PP.grate_poses('SX1', T)]
    objs += [dict(m='start_gate', t='start_gate', x=g[0], y=g[1], z=g[2], a=g[3]) for g in PP.start_gates('SX1')]
    gp = PP.gantry_pose('SX1', T); objs.append(dict(m='start_gantry', t='start_gantry', x=gp['x'], y=gp['y'], z=gp['z'], a=gp['a']))
    cx = np.mean([g[0] for g in G]); cz = np.mean([g[2] for g in G])
    scenes['start_SX1'] = dict(terrain=terrain_patch(T, cx - 8, cz, 62, step=2), objs=objs, cam=[cx, 0, cz])
    pad = [dict(m='hospitality_usland', t='hospitality_usland', x=0, y=0, z=0, a=-np.pi / 2)]   # entrance (+x local) towards +z       # long side along x, module towards +z
    for k in range(3):
        pad.append(dict(m='pickup_usland', t='pickup_usland', x=75 + k * 10, y=0, z=14, a=0.0))
        b = PP.bike_in_pickup(75 + k * 10, 0, 14, 0.0); pad.append(dict(m='bike_trainer', t='bike_trainer', **b))
    for bx, bz, ba, nm in PP.stand_banners((0.0, 0.0), -np.pi / 2):              # v13b: same stand as in the tracks
        pad.append(dict(m='banner', t='banner_' + nm.lower(), x=bx, y=0, z=bz, a=ba))
    pad.append(dict(m='tent_usland', t='tent_usland', x=-30, y=0, z=-26, a=0.0))
    pad.append(dict(m='watertruck', t='watertruck', x=40, y=0, z=-26, a=-np.pi / 2))      # JGSX water truck (kept) + our U sticker
    pad.append(dict(m='watertruck_u', t='watertruck_u', x=40, y=0, z=-26, a=-np.pi / 2))
    scenes['paddock'] = dict(objs=pad, cam=[-5, 3, 10])
    names = {o['m'] for s in scenes.values() for o in s['objs']}
    texs = {o['t'] for s in scenes.values() for o in s['objs']}
    src = lambda f: f'{models}/{f}' if os.path.exists(f'{models}/{f}') else f'{ROOT}/tracks/{FOLDERS["SX1"]}/statue/{f}'   # JGSX models kept in the tracks
    data = dict(models={n: jm_arrays(src(f'{n}.jm')) for n in names}, tex={t: png_uri(src(f'{t}.png')) for t in texs},
                scenes=scenes, team=PU.TEAM)
    html = open(f'{ROOT}/scripts/preview_props.html', encoding='utf-8').read().replace('/*DATA*/null', json.dumps(data, default=float))
    open(out, 'w', encoding='utf-8').write(html)
    print(out, f'{os.path.getsize(out) / 1e6:.1f} Mo'); print(json.dumps(report, indent=1, default=float))

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else PU.OUTD, sys.argv[2] if len(sys.argv) > 2 else f'{ROOT}/viewer/props_preview.html')
