"""Écriture du dossier de piste MX Simulator (export/ParisLaDefenseArena).

Spécification vérifiée sur les pistes installées et les chaînes de mx.exe (docs/03_format_mx_simulator.md) :
  unités : pieds ; axes : Y vers le haut ; statues « [x y z] yaw @modèle.jm @texture.png null »
  y d'une statue = décalage au-dessus du terrain ; un modèle = une texture
  terrain.hf « n espacement min max », terrain.png 16 bits (2^(n+1)+1)², tilemap 2^n x 2^n octets
Le sol intérieur de l'arène est le TERRAIN (plat, carrelage) : la future piste y sera sculptée.
"""
import os
import gzip
import shutil
import numpy as np
from PIL import Image

from . import dims, export
from .export import FT, split_mesh, jm_text
from .materials import MATERIALS
from .mesh import Mesh, box
from .geo2d import point_in_poly

TRACK = "ParisLaDefenseArena"
N_HF = 10                 # terrain 2049 x 2049
SPACING = 0.75            # pieds par pixel -> 1536 ft (468 m) de côté
EXTENT = (2 ** (N_HF + 1)) * SPACING
OX = EXTENT / 2 - 10.0 * FT   # X local = 10 m (milieu de l'emprise -92..112) au centre du terrain
OZ = EXTENT / 2
TILE = 96.0               # découpage spatial des statues (m) : moins d'objets à dessiner
LOD_FT = 7                # *_lod7.jm : bascule à 2^7 = 128 ft (≈ 39 m)  [INFERRED]
# variante nuit : (matériau de jour, matériau de nuit, texture de nuit)
# (préfixe de partie, matériau de jour, texture de nuit) -> modèle *_nuit en bloc non éclairé
NIGHT_SWAP = [("scales_led", "led_strip", "light_emit.png"),
              ("scales_r", "glass_scale", "glass_frit_nuit.png"),
              ("scales_r", "alu_white", "alu_nuit.png"),
              ("stage", "screen_proj", "projection_screen.png")]


def local_to_mx(X, Y, Z=0.0):
    return OX + X * FT, Z * FT, OZ - Y * FT


def _write_model(mesh, mat, path_noext, center):
    """Écrit un modèle JM gzippé centré sur 'center' (X, Y) local."""
    m = mesh.copy()
    m.V[:, 0] -= center[0]; m.V[:, 1] -= center[1]
    txt = jm_text(m, mat)
    with gzip.open(path_noext + ".jm.gz", "wt", newline="\n") as f:
        f.write(txt)


def _spatial_chunks(m, tile):
    c = m.V[m.F].mean(1)
    key = np.floor(c[:, :2] / tile).astype(int)
    out = []
    for k in np.unique(key, axis=0):
        sel = np.all(key == k, axis=1)
        F = m.F[sel]
        used = np.unique(F)
        remap = np.full(m.nv, -1); remap[used] = np.arange(len(used))
        out.append(Mesh(m.V[used], m.N[used], m.UV[used], remap[F]))
    return out


def write_track(scene, root, log=print):
    out = os.path.join(root, "export", TRACK)
    if os.path.exists(out):
        shutil.rmtree(out)
    sdir = os.path.join(out, "statue"); tdir = os.path.join(out, "tex"); ldir = os.path.join(out, "tiles")
    for d in (sdir, tdir, ldir):
        os.makedirs(d)
    merged = scene.merged()
    lines = []
    used_tex = set()
    stats = dict(statues=0, models=0, verts=0, tris=0, lod_models=0)
    lods = {k: v for k, v in merged.items() if k[0].startswith("seatslod_")}
    for (part, mat), m in sorted(merged.items()):
        if part.startswith("_") or part.startswith("seatslod_"):
            continue
        spec = MATERIALS[mat]
        tex = spec["tex"]
        used_tex.add(tex)
        chunks = _spatial_chunks(m, TILE)
        for ci, ch in enumerate(chunks):
            for si, sub in enumerate(split_mesh(ch)):
                c = (sub.V[:, :2].min(0) + sub.V[:, :2].max(0)) / 2
                c = np.round(c, 2)
                name = "%s__%s__%02d_%d" % (part, mat, ci, si)
                _write_model(sub, mat, os.path.join(sdir, name), c)
                stats["models"] += 1
                stats["verts"] += sub.nv; stats["tris"] += sub.nf
                if part.startswith("seats_"):
                    lk = ("seatslod_" + part[len("seats_"):], mat)
                    if lk in lods:
                        _write_model(lods[lk], mat, os.path.join(sdir, name + "_lod%d" % LOD_FT), c)
                        stats["lod_models"] += 1
                x, y, z = local_to_mx(c[0], c[1], 0.0)
                lines.append("[%.4f %.4f %.4f] 0.000000 @%s/statue/%s.jm @%s/tex/%s null"
                             % (x, 0.0, z, TRACK, name, TRACK, tex))
                stats["statues"] += 1
    with open(os.path.join(out, "statues"), "w", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    # variante nuit : réglettes LED et écrans en matériaux non éclairés (modèles *_nuit)
    night = []
    for ln in lines:
        swapped = ln
        for prefix, mat, new_tex in NIGHT_SWAP:
            nm = ln.split("/statue/")[1].split(".jm")[0]
            if nm.startswith(prefix) and "__%s__" % mat in ln:
                name = ln.split("/statue/")[1].split(".jm")[0]
                src_path = os.path.join(sdir, name + ".jm.gz")
                with gzip.open(src_path, "rt") as fh:
                    txt = fh.read()
                head = txt.split("\n")[1]
                txt = txt.replace(head, "-2 0 1 1 1", 1)
                txt = txt.split("\n-1 ")[0].rstrip("\n") + "\n"     # retirer un éventuel bloc de réflexion
                with gzip.open(os.path.join(sdir, name + "_nuit.jm.gz"), "wt", newline="\n") as fh:
                    fh.write(txt)
                tok = ln.replace(name + ".jm", name + "_nuit.jm").split(" ")
                tok[-2] = "@%s/tex/%s" % (TRACK, new_tex)
                swapped = " ".join(tok)
        night.append(swapped)
    vd = os.path.join(out, "variants")
    os.makedirs(vd, exist_ok=True)
    with open(os.path.join(vd, "statues_nuit"), "w", newline="\n") as f:
        f.write("\n".join(night) + "\n")
    # textures (+ cartes normales associées)
    src = os.path.join(root, "build", "textures")
    used_tex |= {t for _, _, t in NIGHT_SWAP}
    for t in sorted(used_tex):
        shutil.copy(os.path.join(src, t), os.path.join(tdir, t))
        nn = t.replace("-repeat.png", "_norm-repeat.png") if "-repeat" in t else t.replace(".png", "_norm.png")
        if os.path.exists(os.path.join(src, nn)):
            shutil.copy(os.path.join(src, nn), os.path.join(tdir, nn))
    log("  MX : %(statues)d statues, %(models)d modèles (+%(lod_models)d LOD), %(verts)d sommets, %(tris)d triangles" % stats)
    _terrain(out, root)
    _lighting(out)
    _gates(out)
    with open(os.path.join(out, "desc"), "w", newline="\n") as f:
        f.write("Paris La Defense Arena - architecture (phase 1, sans piste)\n")
    for empty in ("decals", "billboards"):
        open(os.path.join(out, empty), "w").close()
    stats["folder"] = out
    return stats


def _terrain(out, root):
    n = 2 ** (N_HF + 1) + 1
    with open(os.path.join(out, "terrain.hf"), "w", newline="\n") as f:
        f.write("%d %g 0 10\n" % (N_HF, SPACING))
    Image.fromarray(np.zeros((n, n), np.uint16)).save(os.path.join(out, "terrain.png"))
    # coordonnées monde des pixels -> local
    px = np.arange(n) * SPACING
    Xl = (px - OX) / FT
    Yl = -(px - OZ) / FT
    XX, YY = np.meshgrid(Xl, Yl)       # ligne = z (Y local), colonne = x
    P = np.stack([XX, YY], -1)
    floor = point_in_poly(P, dims.floor_outline(1.0))
    inside = point_in_poly(P, dims.outline(0.0, 2.0)["p"])
    # éclairage précalculé : parvis au soleil, emprise couverte plus sombre, sol de l'arène sous projecteurs
    shade = np.full((n, n), 222.0)
    shade[inside] = 120.0
    # halo des projecteurs sur le sol (rampes longitudinales Y = ±34 m)
    glow = 190 + 30 * np.exp(-((np.abs(YY) - 30) / 22) ** 2)
    shade[floor] = glow[floor]
    sh = np.clip(shade, 0, 255).astype(np.uint8)
    rgb = np.stack([sh] * 3, -1)
    _ppm(rgb, os.path.join(out, "shading.ppm"))
    _ppm((rgb // 2).astype(np.uint8), os.path.join(out, "shadingx2.ppm"))
    # tilemap (2^n) : 0 = parvis, 1 = sol de l'arène
    m = 2 ** N_HF
    pc = (np.arange(m) + 0.5) * 2 * SPACING
    Xc = (pc - OX) / FT; Yc = -(pc - OZ) / FT
    XC, YC = np.meshgrid(Xc, Yc)
    tm = point_in_poly(np.stack([XC, YC], -1), dims.floor_outline(1.0)).astype(np.uint8)
    tm.tofile(os.path.join(out, "tilemap"))
    # tuiles
    src = os.path.join(root, "build", "textures")
    for name in ("plaza.ppm", "floor_tiles.ppm"):
        im = Image.open(os.path.join(src, name)).convert("RGB").resize((128, 128), Image.LANCZOS)
        _ppm(np.asarray(im), os.path.join(out, "tiles", name))
    erode = """erode_depth 0.0
erode_lower 50.0
erode_upper 150.0
erode_displacement 0.0
erode_radius 5.0
erode_inner_depth 0.0
erode_inner_radius 2.0
erode_min_slope -0.75
erode_max_slope 0.75
erode_off_speed 10.0
erode_on_speed 50.0
erode_slip_base_scale 1.0
erode_slip_scale 1.0
erode_slip_lower 0.0
erode_slip_upper 5.0
erode_downhill_scale 0.8
erode_limit 0.00 1.0 2.25
erode_limit 2.5 0.3 0.3
erode_lateral_scale 0.025
"""
    with open(os.path.join(out, "tileinfo"), "w", newline="\n") as f:
        for nm, tex in (("Parvis", "plaza.ppm"), ("Sol arene", "floor_tiles.ppm")):
            f.write("name %s\nfriction 1.0 0\nfriction 1.2 1.5\nfriction 1.1 15\nfriction 1.2 30\n"
                    "roll_resist 40.0 60.0 35.0\nroll_resist 50.0 70.0 45.0\n%s"
                    "texture @%s/tiles/%s\naddtile\n\n" % (nm, erode, TRACK, tex))


def _ppm(arr, path):
    arr = np.ascontiguousarray(arr, np.uint8)
    h, w = arr.shape[:2]
    with open(path, "wb") as f:
        f.write(b"P6\n%d %d\n255\n" % (w, h))
        f.write(arr.tobytes())


LIGHTING = {
    # intérieur éclairé (par défaut) : « soleil » quasi vertical = projecteurs de toiture
    "interieur_eclaire": """sun_vector [ 0.15 1.0 0.25 ]
sun_color [ 0.95 0.95 0.92 ]
ambient [ 0.42 0.42 0.45 ]
global_ambient [ 0.10 0.10 0.10 ]
dynamic_lighting 1
""",
    "interieur_sombre": """sun_vector [ 0.10 1.0 0.20 ]
sun_color [ 0.35 0.38 0.45 ]
ambient [ 0.10 0.10 0.13 ]
global_ambient [ 0.03 0.03 0.04 ]
fog [ 0.02 0.02 0.03 ] 0.0004
dynamic_lighting 1
""",
    "facade_jour": """sun_vector [ -0.55 0.55 0.63 ]
sun_color [ 1.00 0.98 0.92 ]
ambient [ 0.36 0.37 0.40 ]
global_ambient [ 0.10 0.10 0.10 ]
fog [ 0.75 0.80 0.87 ] 0.00005
dynamic_lighting 1
""",
    "facade_nuit": """sun_vector [ -0.3 0.8 0.4 ]
sun_color [ 0.12 0.13 0.18 ]
ambient [ 0.06 0.06 0.09 ]
global_ambient [ 0.02 0.02 0.03 ]
fog [ 0.02 0.02 0.04 ] 0.0002
dynamic_lighting 1
""",
}


def _lighting(out):
    with open(os.path.join(out, "lighting"), "w", newline="\n") as f:
        f.write(LIGHTING["interieur_eclaire"])
    vd = os.path.join(out, "variants")
    os.makedirs(vd, exist_ok=True)
    for k, v in LIGHTING.items():
        with open(os.path.join(vd, "lighting_" + k), "w", newline="\n") as f:
            f.write(v)


def _gates(out):
    """Grille de départ et portes de chronométrage PROVISOIRES (exigées pour charger la piste).
    La vraie piste sera définie en phase 2."""
    gate = box((1.0, 0.15, 0.5)).transformed(np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0.25], [0, 0, 0, 1.0]]))
    path = os.path.join(out, "statue", "gate_placeholder")
    _write_model(gate, "steel_black", path, (0.0, 0.0))
    lines = ["startinggate:"]
    for k in range(12):
        x, _, z = local_to_mx(-48.0, -13.2 + k * 2.4)
        lines.append("[%.4f 0.000000 %.4f] 1.570796 @%s/statue/gate_placeholder.jm @%s/tex/steel_black-repeat.png @startgate.shp"
                     % (x, z, TRACK, TRACK))
    lines.append("checkpoints:")
    # boucle autour du sol : Sud (ligne de départ), Est, Nord, Ouest
    cps = [((-40.0, 0.0), (0.0, 40.0)), ((0.0, -22.0), (22.0, 0.0)), ((45.0, 0.0), (0.0, -40.0)), ((0.0, 22.0), (-22.0, 0.0))]
    for (cx, cy), (vx, vy) in cps:
        x, _, z = local_to_mx(cx, cy)
        hw = np.hypot(vx, vy) * FT
        lines.append("%.4f [%.4f 0.000000 %.4f] [%.4f 0.000000 %.4f]" % (hw, x, z, vx * FT, -vy * FT))
    lines += ["firstlap:", "0 1 2 3 ", "normallap:", "0 1 2 3 "]
    with open(os.path.join(out, "timing_gates"), "w", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
