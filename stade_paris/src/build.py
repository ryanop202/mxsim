"""Point d'entrée : régénère toute l'arène.

  py -3.12 -I src/build.py              -> textures + géométrie + OBJ (build/obj) + rapport
  py -3.12 -I src/build.py --mx         -> + dossier de piste MX Simulator (export/ParisLaDefenseArena)
  py -3.12 -I src/build.py --only facade,roof
"""
import os
import sys
import json
import time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, ".."))

from arena import dims, roof, facade, office, bowl, interior, textures, export
from arena.mesh import Scene, Mesh, quad
from arena.materials import MATERIALS

BUILD = os.path.join(ROOT, "build")
OBJ = os.path.join(BUILD, "obj")
TEX = os.path.join(BUILD, "textures")


def log(*a):
    print("[%6.1fs]" % (time.time() - T0), *a, flush=True)


def ground(scene):
    """Sol de prévisualisation (dans MX, c'est le terrain qui joue ce rôle)."""
    g = quad((-260, -260, -0.02), (260, -260, -0.02), (260, 260, -0.02), (-260, 260, -0.02),
             uv=((0, 0), (520 / 8, 0), (520 / 8, 520 / 8), (0, 520 / 8)))
    scene.add("_ground", "ground_plaza", g)
    f = dims.floor_outline(1.0)
    from arena.mesh import triangulate
    tri = triangulate(f[::-1])
    V = np.column_stack([f[::-1], np.full(len(f), 0.0)])
    scene.add("_ground", "ground_floor", Mesh(V, np.tile([0, 0, 1.0], (len(V), 1)), f[::-1] / 2.0, tri))


NOSEATS = False


def build(only=None):
    scene = Scene()
    want = lambda k: only is None or k in only
    log("textures")
    textures.build_all(TEX)
    textures.build_terrain_tiles(TEX)
    from PIL import Image
    for src, dst in (("plaza.ppm", "plaza_preview.png"), ("floor_tiles.ppm", "floor_preview.png")):
        Image.open(os.path.join(TEX, src)).save(os.path.join(TEX, dst))
    info = {}
    log("toiture (LiDAR)")
    rm, L, _ = roof.build()
    if want("roof"):
        scene.add("roof", "roof", rm)
    if want("facade"):
        log("couronne")
        cref = facade.build_crown(L, scene)
        info["crown_panels"] = int(cref.extra["panels"][0])
        ref = facade.ribbon_ref()
        info["ribbon_length_m"] = round(float(ref.length), 1)
        log("entrées / écrans")
        excl, gaps = facade.build_entrances(ref, scene)
        log("socle / peau intérieure")
        facade.build_base(ref, scene, gaps)
        log("écailles")
        n, counts = facade.build_scales(ref, scene, excl)
        info["scales"] = n
        info["scales_by_type"] = counts
        log("  écailles :", n, counts)
        facade.build_ledge(ref, scene)
    if want("office"):
        log("bureaux Nord")
        office.build(L, scene)
    if want("bowl"):
        log("tribunes et sièges")
        info["bowl"] = bowl.build(scene, with_seats=not NOSEATS)
        log("  ", info["bowl"])
    if want("interior"):
        log("mur de scène, charpente, équipements")
        info["interior"] = interior.build(scene, rm)
    ground(scene)
    return scene, info


def write_obj(scene):
    os.makedirs(OBJ, exist_ok=True)
    for f in os.listdir(OBJ):
        if f.endswith(".obj"):
            os.remove(os.path.join(OBJ, f))
    by_part = {}
    for (part, mat), m in scene.merged().items():
        by_part.setdefault(part, {})[mat] = m
    for part, mats in by_part.items():
        export.write_obj(mats, os.path.join(OBJ, part + ".obj"))
    export.write_material_manifest(os.path.join(BUILD, "materials.json"), TEX)


if __name__ == "__main__":
    T0 = time.time()
    only = None
    NOSEATS = "--no-seats" in sys.argv
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    scene, info = build(only)
    rows = scene.stats()
    tv = sum(r[2] for r in rows if not r[0].startswith("_")); tf = sum(r[3] for r in rows if not r[0].startswith("_"))
    for r in rows:
        log("  %-16s %-14s %8d v %8d t" % r)
    log("TOTAL (hors sol) : %d sommets, %d triangles" % (tv, tf))
    write_obj(scene)
    info.update(total_vertices=tv, total_triangles=tf, parts=[list(map(str, r)) for r in rows])
    with open(os.path.join(BUILD, "build_info.json"), "w") as f:
        json.dump(info, f, indent=1)
    if "--mx" in sys.argv:
        from arena import mxtrack
        mxtrack.write_track(scene, ROOT, log)
    log("terminé")
