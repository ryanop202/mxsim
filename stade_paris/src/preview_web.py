"""Aperçu 3D dans le navigateur (three.js) de l'arène construite, quand Blender n'est pas disponible.

  py -3.15 -I src/preview_web.py          -> build/web/ (index.html + data.bin + textures)
  py -3.15 -m http.server 8765 -d build/web

Lit build/obj/*.obj et build/textures. Ce n'est PAS un rendu du jeu (éclairage approximatif) :
il sert à vérifier la géométrie et l'habillage (logos à l'endroit, ratios, placement).
"""
import os
import sys
import json
import shutil
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
from arena.materials import MATERIALS

OBJ = os.path.join(ROOT, "build", "obj")
TEX = os.path.join(ROOT, "build", "textures")
OUT = os.path.join(ROOT, "build", "web")
PREVIEW_MATS = {"ground_plaza": dict(tex="plaza_preview.png"), "ground_floor": dict(tex="floor_preview.png"),
                "piste": dict(tex="piste_top.png", unlit=True)}          # terrain de la piste Paris 2026 (paris2026/preview_track.py)


def read_obj(path):
    out, cur = [], None
    V, T, N, F = [], [], [], []
    with open(path) as f:
        for ln in f:
            if ln.startswith("v "):
                V.append(ln.split()[1:4])
            elif ln.startswith("vt "):
                T.append(ln.split()[1:3])
            elif ln.startswith("vn "):
                N.append(ln.split()[1:4])
            elif ln.startswith("usemtl"):
                cur = ln.split()[1]
            elif ln.startswith("f "):
                F.append([int(p.split("/")[0]) - 1 for p in ln.split()[1:4]])
            elif ln.startswith("o ") and F:
                out.append((cur, F)); F = []
    if F:
        out.append((cur, F))
    V = np.array(V, np.float32); T = np.array(T, np.float32); N = np.array(N, np.float32)
    return V, T, N, out


def main():
    shutil.rmtree(os.path.join(OUT, "tex"), ignore_errors=True)     # le dossier lui-même peut être servi en ce moment
    os.makedirs(os.path.join(OUT, "tex"))
    groups, blob, used = [], bytearray(), set()

    def put(a):
        off = len(blob); blob.extend(np.ascontiguousarray(a).tobytes()); return off

    for fn in sorted(os.listdir(OBJ)):
        if not fn.endswith(".obj"):
            continue
        V, T, N, objs = read_obj(os.path.join(OBJ, fn))
        for mat, F in objs:
            F = np.array(F, np.uint32)
            used_v = np.unique(F)
            remap = np.zeros(len(V), np.uint32); remap[used_v] = np.arange(len(used_v))
            P = V[used_v][:, [0, 2, 1]] * np.array([1, 1, -1], np.float32)       # Z haut -> Y haut (three.js)
            Nn = N[used_v][:, [0, 2, 1]] * np.array([1, 1, -1], np.float32)
            spec = MATERIALS.get(mat) or PREVIEW_MATS.get(mat) or dict(tex="white_matte.png")
            used.add(spec["tex"])
            groups.append(dict(part=fn[:-4], mat=mat, tex=spec["tex"], unlit=bool(spec.get("unlit")),
                               alpha=bool(spec.get("alpha")), two=bool(spec.get("two_sided")),
                               n=int(len(used_v)), m=int(F.size),
                               p=put(P.astype(np.float32)), nr=put(Nn.astype(np.float32)),
                               uv=put(T[used_v].astype(np.float32)), i=put(remap[F].ravel())))
    with open(os.path.join(OUT, "data.bin"), "wb") as f:
        f.write(blob)
    for t in used:
        src = os.path.join(TEX, t)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(OUT, "tex", t))
    # public (billboards de la piste Paris 2026) : sprites dans l'aperçu
    bbf = os.path.join(ROOT, "..", "tracks", "USLAND2026SupercrossParis", "billboards")
    crowd = []
    if os.path.exists(bbf):
        import re as _re
        for l in open(bbf):
            m = _re.match(r"\[([-\d.]+) ([-\d.]+) ([-\d.]+)\] ([-\d.]+) ([-\d.]+) @\S+/billboard/(\S+)", l)
            if m:
                x, y, z, h, a, n = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)), float(m.group(5)), m.group(6)
                crowd.append([(x - 549.0) / 3.28084, y / 3.28084, (z - 593.5) / 3.28084, h / 3.28084, a, n])
                src_ = os.path.join(os.path.dirname(bbf), "billboard", n)
                if os.path.exists(src_) and not os.path.exists(os.path.join(OUT, "tex", n)):
                    shutil.copy(src_, os.path.join(OUT, "tex", n))
    with open(os.path.join(OUT, "crowd.json"), "w") as f:
        json.dump(crowd, f)
    with open(os.path.join(OUT, "groups.json"), "w") as f:
        json.dump(groups, f)
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(HTML.replace("__K__", str(json.load(open(os.path.join(ROOT, "build", "build_info.json"))).get("plan_scale", 1))))
    print("aperçu :", OUT, "-", len(groups), "groupes,", len(blob) // 1024, "Ko")


HTML = r"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Arène Paris 2026 - aperçu</title>
<style>html,body{margin:0;height:100%;background:#111;color:#eee;font:14px system-ui}#ui{position:fixed;top:8px;left:8px;z-index:2}
button{margin:2px;padding:6px 10px;background:#222;color:#eee;border:1px solid #444;border-radius:4px;cursor:pointer}</style>
</head><body><div id="ui"></div>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
"three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}</script>
<script type="module">
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const R = new THREE.WebGLRenderer({antialias:true, preserveDrawingBuffer:true});
R.setPixelRatio(devicePixelRatio); R.setSize(innerWidth, innerHeight); R.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(R.domElement);
const S = new THREE.Scene(); S.background = new THREE.Color(0x1a1c24);
const C = new THREE.PerspectiveCamera(50, innerWidth/innerHeight, 0.5, 3000);
const O = new OrbitControls(C, R.domElement);
// éclairage de Saint-Thibéry (lighting : soleil (-0.6528, 0.3590, 0.6671) couleur 0.85, ambiance 0.30 / 0.31 / 0.36)
S.add(new THREE.AmbientLight(new THREE.Color(0.30, 0.31, 0.36), 2.2));
const sun = new THREE.DirectionalLight(new THREE.Color(0.85, 0.85, 0.80), 2.4); sun.position.set(-65.28, 35.90, -66.71); S.add(sun);
const L = new THREE.TextureLoader(), cache = {};
function tex(n){ if(!cache[n]){ const t=L.load('tex/'+n); t.wrapS=t.wrapT=THREE.RepeatWrapping; t.colorSpace=THREE.SRGBColorSpace; t.anisotropy=8; cache[n]=t;} return cache[n]; }
const [G, buf] = await Promise.all([fetch('groups.json').then(r=>r.json()), fetch('data.bin').then(r=>r.arrayBuffer())]);
for (const g of G){
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(buf, g.p, g.n*3), 3));
  geo.setAttribute('normal', new THREE.BufferAttribute(new Float32Array(buf, g.nr, g.n*3), 3));
  geo.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(buf, g.uv, g.n*2), 2));
  geo.setIndex(new THREE.BufferAttribute(new Uint32Array(buf, g.i, g.m), 1));
  const o = {map: tex(g.tex), side: g.two ? THREE.DoubleSide : THREE.FrontSide};
  if (g.alpha) o.alphaTest = 0.75;
  const m = g.unlit ? new THREE.MeshBasicMaterial(o) : new THREE.MeshLambertMaterial(o);
  const mesh = new THREE.Mesh(geo, m); mesh.name = g.part + '/' + g.mat; S.add(mesh);
}
// public : sprites (billboards MX) - x local = (x_mx - 549) / ft ; z three = (z_mx - 593.5) / ft
try { const CR = await fetch('crowd.json').then(r => r.json()); const mats = {};
  for (const [x, y, z, h, a, n] of CR) { if (!mats[n]) { const t = tex(n); t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping; mats[n] = new THREE.SpriteMaterial({map: t, alphaTest: 0.5}); }
    const sp = new THREE.Sprite(mats[n]); sp.center.set(0.5, 0); sp.scale.set(h * a, h, 1); sp.position.set(x, y, z); sp.name = 'public/crowd'; S.add(sp); } } catch (e) {}
// vues (x, y haut, z = -y local), en mètres ; K = agrandissement en plan de l'arène
const K = __K__;
const V = {
  'Tribune Sud -> écran': [[-K*58, 14, 0], [K*60, 12, 0]],
  'Écran central': [[K*12, 12, 0], [K*61, 17, 0]],
  'Bandeau LED (côté)': [[K*10, 2.2, K*15], [K*25, 0.6, -K*46.9]],
  'Bandeau LED (Sud)': [[-K*25, 2.2, 0], [-K*62, 0.6, K*8]],
  'Vue de dessus (toit masqué)': [[0, 300, 1], [0, 0, 0]],
  'Façade': [[-K*60, 25, -K*200], [0, 10, -K*80]],
  'Piste : vue tribune Sud': [[-98, 21, 0], [12, 0, 0]],
  'Piste : depuis la grille': [[61, 2.6, -13.8], [20, 1, -13.8]],
  'Piste : grande table': [[6, 6, 4], [-20, 2, 15.3]],
  'Piste : whoops': [[56, 4.5, 39], [0, 0.5, 48]],
};
const roofParts = ['roof', 'roof_under', 'roof_structure', 'rigging', 'catwalks'];
function go(k){ const [p, t] = V[k]; C.position.set(...p); O.target.set(...t); O.update();
  const hide = k.startsWith('Vue de dessus'); S.traverse(o => { if (o.isMesh) o.visible = !(hide && roofParts.includes(o.name.split('/')[0])); }); }
const ui = document.getElementById('ui');
for (const k in V){ const b = document.createElement('button'); b.textContent = k; b.onclick = () => go(k); ui.appendChild(b); }
window.go = go; window.S = S; window.C = C; window.O = O; go(Object.keys(V)[0]);
addEventListener('resize', () => { C.aspect = innerWidth/innerHeight; C.updateProjectionMatrix(); R.setSize(innerWidth, innerHeight); });
(function loop(){ requestAnimationFrame(loop); R.render(S, C); })();
window.ready = true;
</script></body></html>
"""

if __name__ == "__main__":
    main()
