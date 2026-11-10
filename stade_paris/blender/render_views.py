"""Rendu des vues de contrôle dans Blender (exécuté par blender -b -P render_views.py -- <args>).

Arguments (après --) :
  --root DIR        racine du projet
  --views a,b,c     noms des vues (blender/views.json) ; 'all' par défaut
  --res 1600x900    résolution
  --samples N       échantillons EEVEE
  --save-blend      enregistre aussi build/arena_preview.blend
"""
import bpy
import json
import math
import os
import sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None):
    if name in argv:
        i = argv.index(name)
        return argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("--") else True
    return default


ROOT = arg("--root", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
OBJ_DIR = os.path.join(ROOT, "build", "obj")
TEX_DIR = os.path.join(ROOT, "build", "textures")
OUT_DIR = os.path.join(ROOT, "renders")
VIEWS = json.load(open(os.path.join(ROOT, "blender", "views.json")))
MANIFEST = json.load(open(os.path.join(ROOT, "build", "materials.json")))
res = arg("--res", "1600x900").split("x")
want = arg("--views", "all")
samples = int(arg("--samples", 32))

# ------------------------------------------------------------------ scène vierge
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        scene.render.engine = eng
        break
    except TypeError:
        pass
scene.render.resolution_x, scene.render.resolution_y = int(res[0]), int(res[1])
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast" if False else "None"
try:
    scene.eevee.shadow_pool_size = "1024"
except Exception:
    pass
try:
    scene.eevee.taa_render_samples = samples
    scene.eevee.use_shadows = True
    scene.eevee.use_raytracing = True
    scene.eevee.ray_tracing_options.resolution_scale = "2"
    scene.eevee.use_fast_gi = True
except Exception as e:
    print("eevee opts:", e)


# ------------------------------------------------------------------ matériaux
def make_material(name, spec):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = nodes.get("Principled BSDF")
    tex_path = os.path.join(TEX_DIR, spec["tex"])
    img = bpy.data.images.load(tex_path, check_existing=True)
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Linear"
    if "-repeat" not in spec["tex"] and "-hrepeat" not in spec["tex"]:
        tex.extension = "EXTEND"
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = spec.get("rough", 0.6)
    bsdf.inputs["Metallic"].default_value = spec.get("metal", 0.0)
    if spec.get("env", 0) > 0:
        bsdf.inputs["Roughness"].default_value = min(bsdf.inputs["Roughness"].default_value, 0.12)
    # carte normale
    nn = spec["tex"].replace("-repeat.png", "_norm-repeat.png") if "-repeat" in spec["tex"] else spec["tex"].replace(".png", "_norm.png")
    npath = os.path.join(TEX_DIR, nn)
    if os.path.exists(npath):
        ntex = nodes.new("ShaderNodeTexImage")
        ntex.image = bpy.data.images.load(npath, check_existing=True)
        ntex.image.colorspace_settings.name = "Non-Color"
        nmap = nodes.new("ShaderNodeNormalMap")
        links.new(ntex.outputs["Color"], nmap.inputs["Color"])
        links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    if spec.get("unlit"):
        links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = spec.get("emit", 1.0)
    if spec.get("alpha"):
        links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
        try:
            mat.surface_render_method = "DITHERED"
        except Exception:
            mat.blend_method = "CLIP"
    mat.use_backface_culling = not spec.get("two_sided", False)
    return mat


MATS = {k: make_material(k, v) for k, v in MANIFEST.items()}
# matériaux de prévisualisation du sol (terrain MX)
for k, f in (("ground_plaza", "plaza_preview.png"), ("ground_floor", "floor_preview.png")):
    if os.path.exists(os.path.join(TEX_DIR, f)):
        MATS[k] = make_material(k, {"tex": f, "rough": 0.85})

# ------------------------------------------------------------------ import
for f in sorted(os.listdir(OBJ_DIR)):
    if not f.endswith(".obj") or f.startswith("seatslod"):
        continue
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=os.path.join(OBJ_DIR, f), forward_axis="Y", up_axis="Z")
    for ob in set(bpy.data.objects) - before:
        base = ob.name.split(".")[0]
        ob.name = f[:-4] + ":" + base
        for slot in ob.material_slots:
            mname = slot.material.name.split(".")[0] if slot.material else base
            if mname in MATS:
                slot.material = MATS[mname]
        if ob.type == "MESH":
            for p in ob.data.polygons:
                p.use_smooth = True


# matériaux propres aux écailles (lavage LED de nuit, sans toucher aux autres pièces blanches)
SCALE_MATS = {}
for ob in bpy.data.objects:
    if ob.name.startswith("scales_r"):
        for slot in ob.material_slots:
            if slot.material is None:
                continue
            base = slot.material.name.split(".")[0]
            if base not in SCALE_MATS:
                SCALE_MATS[base] = slot.material.copy()
                SCALE_MATS[base].name = base + "_scales"
            slot.material = SCALE_MATS[base]


# ------------------------------------------------------------------ éclairages
def world_sky(strength=1.0, sun_el=25, sun_az=200):
    w = bpy.data.worlds.new("sky")
    scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes.get("Background")
    sky = nt.nodes.new("ShaderNodeTexSky")
    try:
        sky.sky_type = "NISHITA"
        sky.sun_elevation = math.radians(sun_el)
        sky.sun_rotation = math.radians(sun_az)
        sky.sun_disc = False
    except Exception:
        pass
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength


def world_flat(col, strength):
    w = bpy.data.worlds.new("flat")
    scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (*col, 1)
    bg.inputs["Strength"].default_value = strength


def sun(el, az, energy, col=(1, 0.97, 0.92)):
    d = bpy.data.lights.new("sun", "SUN")
    d.energy = energy
    d.color = col
    d.angle = math.radians(1.0)
    o = bpy.data.objects.new("sun", d)
    scene.collection.objects.link(o)
    o.rotation_euler = (math.radians(90 - el), 0, math.radians(az))
    return o


def area_grid(z, xs, ys, size, energy, col=(1, 1, 1)):
    for x in xs:
        for y in ys:
            d = bpy.data.lights.new("flood", "AREA")
            d.size = size
            d.energy = energy
            d.color = col
            o = bpy.data.objects.new("flood", d)
            o.location = (x, y, z)
            scene.collection.objects.link(o)


def clear_lights():
    for o in list(scene.objects):
        if o.type == "LIGHT":
            bpy.data.objects.remove(o)


def set_emission(matname, strength, col=(1, 1, 1)):
    m = MATS.get(matname)
    if not m:
        return
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Emission Color"].default_value = (*col, 1)
    b.inputs["Emission Strength"].default_value = strength


def setup_lighting(mode):
    clear_lights()
    scene.view_settings.exposure = {"day": -0.9, "dusk": 0.0, "night": 0.0}.get(mode, 0.0)
    led = {"dusk": 25.0, "night": 40.0}.get(mode, 0.0)
    set_emission("led_strip", led, (0.85, 0.82, 1.0))
    wash = {"dusk": 0.6, "night": 1.4}.get(mode, 0.0)
    for m in SCALE_MATS.values():
        b = m.node_tree.nodes.get("Principled BSDF")
        b.inputs["Emission Color"].default_value = (0.80, 0.70, 1.0, 1)
        b.inputs["Emission Strength"].default_value = wash
    if mode == "day":
        world_sky(0.8, 28, 215)
        sun(28, 215, 3.5)
    elif mode == "dusk":
        world_flat((0.32, 0.42, 0.6), 0.6)
        sun(4, 250, 0.4, (0.8, 0.85, 1.0))
    elif mode == "night":
        world_flat((0.01, 0.012, 0.02), 1.0)
    elif mode == "interior":
        world_flat((0.02, 0.02, 0.025), 1.0)
        scene.view_settings.exposure = -1.6
        area_grid(28.5, range(-50, 61, 22), range(-36, 37, 24), 8.0, 14000)
        set_emission("light", 40.0)
    elif mode == "inspect":
        # inspection de la charpente : ambiance uniforme + projecteurs + lumière montante depuis le sol
        world_flat((0.6, 0.6, 0.62), 0.35)
        scene.view_settings.exposure = -0.6
        area_grid(28.5, range(-50, 61, 22), range(-36, 37, 24), 8.0, 6000)
        for x in range(-40, 61, 25):
            for y in (-25, 25):
                d = bpy.data.lights.new("up", "AREA"); d.size = 12; d.energy = 30000
                o = bpy.data.objects.new("up", d); o.location = (x, y, 3.0); o.rotation_euler = (3.14159, 0, 0)
                scene.collection.objects.link(o)
        set_emission("light", 20.0)
    elif mode == "interior_dark":
        world_flat((0.005, 0.005, 0.008), 1.0)
        area_grid(29.0, range(-40, 51, 30), (-30, 30), 3.0, 8000, (0.6, 0.75, 1.0))


# ------------------------------------------------------------------ caméras & rendu
cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam_data.clip_start = 0.3
cam_data.clip_end = 3000

if arg("--save-blend"):
    setup_lighting("day")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "build", "arena_preview.blend"))

names = list(VIEWS.keys()) if want == "all" else want.replace("+", ",").split(",")
for name in names:
    v = VIEWS[name]
    setup_lighting(v.get("light", "day"))
    cam.location = Vector(v["loc"])
    d = Vector(v["look"]) - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cam_data.lens = v.get("lens", 24)
    cam_data.sensor_width = 36
    scene.render.filepath = os.path.join(OUT_DIR, "view_%s.png" % name)
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)
