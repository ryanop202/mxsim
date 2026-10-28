"""Mur de scène, écrans, sous-face de toiture et charpente métallique intérieure.

Charpente [DOC] : cadre de 4 méga-poutres (≈150 x 110 m, 14 m de hauteur, 6 100 t) porté par
4 tours d'angle ; [PHO P8, P9, P10] fermes treillis noires, rampes de projecteurs longitudinales,
passerelles, gaines argentées, grappes de haut-parleurs.
Hypothèse [HYP] : membrure basse des méga-poutres à 30,0 m, membrure haute sous la toiture
(hauteur variable suivant la voûte, comme sur la coupe ACDP).
"""
import numpy as np

from . import dims
from .mesh import Mesh, box, beam, quad, grid_surface, tube, frame, concat
from .roof import field

STAGE_X = dims.X_STAGE
LIGHT = True        # version allégée pour MX
MEGA_Y = 44.0
MEGA_X_SOUTH = -52.0
MEGA_X_NORTH = 58.0
BOTTOM_MEGA = 30.0
BOTTOM_SEC = 33.5


def under(x, y):
    """Sous-face de toiture (bac + pannes)."""
    return field()(x, y) - 1.4


def _T(x, y, z):
    M = np.eye(4); M[:3, 3] = (x, y, z); return M


# ------------------------------------------------------------------ mur de scène et écrans
def stage_wall(scene):
    half = dims.HALF_W - 3.2
    ys = np.linspace(-half, half, 84)
    top = under(np.full_like(ys, STAGE_X), ys) + 1.0
    P = np.stack([np.column_stack([np.full_like(ys, STAGE_X), ys, np.zeros_like(ys)]),
                  np.column_stack([np.full_like(ys, STAGE_X), ys, top])], 1)
    UV = np.stack([np.column_stack([ys / 4, np.zeros_like(ys)]), np.column_stack([ys / 4, top / 4])], 1)
    scene.add("stage", "wall_black", grid_surface(P[::-1], UV[::-1]))     # face vers -X (vers le sol)

    def panel(mat, y0, y1, z0, z1, x_off, uv=None):
        x = STAGE_X - x_off
        q = quad((x, y1, z0), (x, y0, z0), (x, y0, z1), (x, y1, z1),
                 uv=uv or ((0, 0), (1, 0), (1, 1), (0, 1)))
        return q

    # écran de projection central [PHO P8/P10, DOC 1 400–2 600 m²] : 70 x 18 m
    scene.add("stage", "steel_black", box((0.5, 71.0, 19.0), _T(STAGE_X - 0.25, 0, 18.0)))
    scene.add("stage", "screen_proj", panel("screen_proj", -35, 35, 9.0, 27.0, 0.52))
    # écrans latéraux 16 x 9 m
    for sy in (-1, 1):
        yc = sy * 54.0
        scene.add("stage", "steel_black", box((0.5, 17.0, 10.0), _T(STAGE_X - 0.25, yc, 18.5)))
        scene.add("stage", "screen_proj", panel("screen_proj", yc - 8, yc + 8, 14.0, 23.0, 0.52))
    # enseigne intérieure sous l'écran (24 x 3 m)
    scene.add("stage", "signage_int", panel("signage_int", -12, 12, 5.2, 8.2, 0.08))
    # grande porte de chargement (rideau métallique)
    scene.add("stage", "steel_black", box((0.3, 24.0, 8.0), _T(STAGE_X - 0.15, 0, 4.0)))
    for z in np.arange(0.5, 8.0, 0.5):
        scene.add("stage", "steel_galv", box((0.05, 24.0, 0.04), _T(STAGE_X - 0.32, 0, z)))
    # portes latérales vers les coulisses
    for sy in (-1, 1):
        scene.add("stage", "steel_black", box((0.2, 5.0, 4.0), _T(STAGE_X - 0.1, sy * 30.0, 2.0)))


# ------------------------------------------------------------------ treillis
def truss(p0, p1, top_fn, bottom_fn, panel=6.0, chord=(0.6, 0.7), web=(0.3, 0.3), width=0.0, mat="steel_black",
          scene=None, part="roof_structure"):
    """Poutre treillis (Pratt) entre p0 et p1 (plan XY). top_fn/bottom_fn(x, y) -> z.
    width > 0 : poutre-caisson (deux treillis + entretoises)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    L = np.linalg.norm(p1 - p0)
    n = max(2, int(np.ceil(L / panel)))
    t = np.linspace(0, 1, n + 1)
    pts = p0 + (p1 - p0) * t[:, None]
    dirv = (p1 - p0) / L
    side = np.array([-dirv[1], dirv[0]])
    zt = top_fn(pts[:, 0], pts[:, 1])
    zb = np.minimum(bottom_fn(pts[:, 0], pts[:, 1]), zt - 1.5)
    out = Mesh()
    offs = [0.0] if width <= 0 else [-width / 2, width / 2]
    for o in offs:
        q = pts + side * o
        T_ = np.column_stack([q, zt]); B_ = np.column_stack([q, zb])
        for i in range(n):
            out.add(beam(T_[i], T_[i + 1], chord[0], chord[1], caps=False))
            out.add(beam(B_[i], B_[i + 1], chord[0], chord[1], caps=False))
            out.add(beam(B_[i], T_[i], web[0], web[1], up=(dirv[0], dirv[1], 0), caps=False))
            # diagonale orientée vers le milieu (Pratt)
            if i < n / 2:
                out.add(beam(B_[i + 1], T_[i], web[0], web[1], up=(dirv[0], dirv[1], 0), caps=False))
            else:
                out.add(beam(B_[i], T_[i + 1], web[0], web[1], up=(dirv[0], dirv[1], 0), caps=False))
        out.add(beam(B_[n], T_[n], web[0], web[1], up=(dirv[0], dirv[1], 0), caps=False))
    if width > 0:
        for i in range(0, n + 1, 2):
            a = np.append(pts[i] - side * width / 2, zb[i]); b = np.append(pts[i] + side * width / 2, zb[i])
            out.add(beam(a, b, web[0], web[1], caps=False))
            a[2] = b[2] = zt[i]
            out.add(beam(a, b, web[0], web[1], caps=False))
    if scene is not None:
        scene.add(part, mat, out)
    return out, pts, zt, zb


def catwalk(scene, pts, z, width=0.9):
    """Passerelle technique en caillebotis + garde-corps le long d'une polyligne (plan XY)."""
    pts = np.asarray(pts, float)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        d = b - a
        L = np.linalg.norm(d)
        if L < 1e-6:
            continue
        s = np.array([-d[1], d[0]]) / L * width / 2
        q = quad((*(a - s), z), (*(b - s), z), (*(b + s), z), (*(a + s), z), uv=((0, 0), (L, 0), (L, width), (0, width)))
        scene.add("catwalks", "grating", q.double_sided())
        for sg in (-1, 1):
            r0 = a + sg * s; r1 = b + sg * s
            rq = quad((*r0, z), (*r1, z), (*r1, z + 1.1), (*r0, z + 1.1), uv=((0, 0), (L, 0), (L, 1), (0, 1)))
            scene.add("catwalks", "railing", rq.double_sided())


def roof_structure(scene):
    top = lambda x, y: under(x, y) - 0.4
    bmega = lambda x, y: np.full_like(np.asarray(x, float), BOTTOM_MEGA)
    bsec = lambda x, y: np.full_like(np.asarray(x, float), BOTTOM_SEC)
    info = {}
    # ---- méga-poutres (caissons 3 m)
    for sy in (-1, 1):
        truss((MEGA_X_SOUTH, sy * MEGA_Y), (MEGA_X_NORTH, sy * MEGA_Y), top, bmega, 6.0, (1.0, 1.2), (0.55, 0.55), 3.0, scene=scene)
        catwalk(scene, [(MEGA_X_SOUTH, sy * MEGA_Y), (MEGA_X_NORTH, sy * MEGA_Y)], BOTTOM_MEGA + 0.75)
    for x in (MEGA_X_SOUTH, MEGA_X_NORTH):
        truss((x, -MEGA_Y), (x, MEGA_Y), top, bmega, 6.0, (1.0, 1.2), (0.55, 0.55), 3.0, scene=scene)
        catwalk(scene, [(x, -MEGA_Y), (x, MEGA_Y)], BOTTOM_MEGA + 0.75)
    # ---- fermes secondaires transversales entre méga-poutres
    xs = np.arange(MEGA_X_SOUTH + 11.0, MEGA_X_NORTH - 5.0, 11.0)
    for x in xs:
        truss((x, -MEGA_Y), (x, MEGA_Y), top, bsec, 6.0, (0.55, 0.65), (0.28, 0.28), scene=scene)
        catwalk(scene, [(x, -MEGA_Y + 2), (x, MEGA_Y - 2)], BOTTOM_SEC + 0.35, 0.7)
    info["secondary_trusses"] = len(xs)
    # ---- consoles vers les façades longues (porte-à-faux depuis les méga-poutres)
    edge_y = dims.HALF_W - 3.0
    allx = np.concatenate([[MEGA_X_SOUTH], xs, [MEGA_X_NORTH]])
    for x in allx[::2]:                     # une console sur deux (22 m)
        for sy in (-1, 1):
            p0 = (x, sy * (MEGA_Y + 1.5)); p1 = (x, sy * edge_y)
            bot = lambda xx, yy, sy=sy: np.minimum(BOTTOM_MEGA + (np.abs(yy) - MEGA_Y) * 0.0, under(xx, yy) - 1.6)
            # console peu profonde (2,2 m) qui suit la sous-face : ne descend pas sur les tribunes hautes
            truss(p0, p1, top, lambda xx, yy: top(xx, yy) - 2.2, 6.0, (0.45, 0.55), (0.22, 0.22), scene=scene)
    # ---- consoles vers l'extrémité Sud (radiales dans les angles)
    ys = np.arange(-MEGA_Y, MEGA_Y + 0.1, 22.0)
    for y in ys:
        xe = dims.X_SOUTH + 3.0
        truss((MEGA_X_SOUTH - 1.5, y), (xe, y), top, lambda xx, yy: np.minimum(np.full_like(xx, BOTTOM_MEGA), top(xx, yy) - 1.6),
              6.0, (0.5, 0.6), (0.25, 0.25), scene=scene)
    for sy in (-1, 1):
        c = np.array([dims.X_CORNER, sy * dims.Y_CORNER])
        for ang in np.radians([30, 60]):
            dirv = np.array([-np.cos(ang), sy * np.sin(ang)])
            p1 = c + dirv * (dims.R_CORNER - 3.0)
            truss((MEGA_X_SOUTH - 1.0, sy * (MEGA_Y - 1.0)), p1, top,
                  lambda xx, yy: np.minimum(np.full_like(xx, BOTTOM_MEGA), top(xx, yy) - 1.6), 6.0, (0.5, 0.6), (0.25, 0.25), scene=scene)
    # ---- pannes : supprimées dans la version allégée (nervures portées par la texture de sous-face)
    for i in ([] if LIGHT else range(len(allx) - 1)):
        for y in np.arange(-MEGA_Y + 5.5, MEGA_Y - 1, 5.5):
            a = (allx[i], y); b = (allx[i + 1], y)
            za, zb_ = top(np.array([a[0]]), np.array([y]))[0], top(np.array([b[0]]), np.array([y]))[0]
            scene.add("roof_structure", "steel_black", beam((a[0], y, za + 0.2), (b[0], y, zb_ + 0.2), 0.25, 0.45))
    # ---- tours d'angle (béton, 9 x 6 m) [DOC] : visibles derrière les tribunes hautes ? -> masquées, non modélisées
    return info


def rigging(scene):
    """Rampes de projecteurs, grappes de haut-parleurs, gaines [PHO P8, P9, P10]."""
    z_light = 29.2
    # rampes longitudinales (treillis 0,8 x 0,8 m) avec projecteurs tous les 2,2 m
    for sy in (-1, 1):
        y = sy * 34.0
        x0, x1 = -46.0, 54.0
        for zz in (z_light, z_light + 0.8):
            for yy in (y - 0.4, y + 0.4):
                scene.add("rigging", "steel_black", beam((x0, yy, zz), (x1, yy, zz), 0.08, 0.08, caps=False))
        for x in np.arange(x0, x1, 4.0):
            scene.add("rigging", "steel_black", beam((x, y - 0.4, z_light), (x, y + 0.4, z_light + 0.8), 0.05, 0.05, caps=False))
        for x in np.arange(x0 + 1.0, x1, 4.4):
            _flood(scene, (x, y, z_light - 0.45), aim=(0, -sy * 0.55, -1))
        # suspentes vers les fermes
        for x in np.arange(x0, x1 + 1, 11.0):
            scene.add("rigging", "steel_galv", tube((x, y, z_light + 0.8), (x, y, BOTTOM_SEC), 0.02, 4))
    # rampe transversale Sud et grappes près de la scène
    for y in np.arange(-30.0, 30.1, 4.8):
        _flood(scene, (-46.0, y, z_light - 0.45), aim=(0.6, 0, -1))
    scene.add("rigging", "steel_black", beam((-46.0, -34, z_light + 0.2), (-46.0, 34, z_light + 0.2), 0.6, 0.6))
    for sy in (-1, 1):
        for i in range(4):
            for j in range(3):
                _flood(scene, (54.0 - j * 0.7, sy * (14.0 + i * 0.8), 28.0 + j * 0.5), aim=(-1, 0, -0.7))
        scene.add("rigging", "steel_black", box((2.6, 3.6, 0.3), _T(53.4, sy * 15.2, 29.6)))
    # grappes de haut-parleurs (line arrays) [PHO P10]
    for x in (-12.0, 26.0):
        for sy in (-1, 1):
            y = sy * 20.0
            ztop = 31.0
            scene.add("rigging", "steel_galv", tube((x, y, ztop), (x, y, BOTTOM_SEC), 0.03, 4))
            for k in range(5):
                tilt = np.radians(5.0 * k)
                M = _T(x, y, ztop - 0.6 - k * 1.24) @ _rotx(sy * tilt)
                scene.add("rigging", "steel_black", box((1.3, 0.55, 1.20), M))
    # gaines de ventilation argentées
    for y in (-14.0, 14.0, -56.0, 56.0):
        zz = 35.0 if abs(y) < 20 else 33.0
        scene.add("rigging", "steel_galv", tube((MEGA_X_SOUTH + 2, y, zz), (MEGA_X_NORTH - 2, y, zz), 0.55, 8))
        for x in np.arange(MEGA_X_SOUTH + 8, MEGA_X_NORTH - 2, 28.0):
            scene.add("rigging", "steel_galv", tube((x, y, zz - 0.55), (x, y, zz - 1.4), 0.3, 6))


def _rotx(a):
    c, s = np.cos(a), np.sin(a)
    M = np.eye(4); M[1:3, 1:3] = [[c, -s], [s, c]]; return M


def _flood(scene, p, aim=(0, 0, -1)):
    """Projecteur LED : corps noir + face émissive orientée."""
    aim = np.asarray(aim, float); aim /= np.linalg.norm(aim)
    ref = np.array([1.0, 0, 0]) if abs(aim[0]) < 0.9 else np.array([0, 1.0, 0])
    x = np.cross(ref, aim); x /= np.linalg.norm(x)
    y = np.cross(aim, x)
    M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, y, aim, p
    scene.add("rigging", "steel_black", box((0.55, 0.55, 0.35), M))
    face = quad((-0.24, -0.24, 0.18), (-0.24, 0.24, 0.18), (0.24, 0.24, 0.18), (0.24, -0.24, 0.18))
    if face.N[0] @ np.array([0, 0, 1]) < 0:
        face = face.flipped()
    scene.add("rigging", "light", face.transformed(M))


def roof_underside(scene, roof_mesh):
    m = roof_mesh.flipped()
    m.V = m.V.copy(); m.V[:, 2] -= 1.0
    m.UV = np.column_stack([m.V[:, 1] / 6.0, m.V[:, 0] / 6.0])
    scene.add("roof_under", "roof_under", m)


def build(scene, roof_mesh):
    stage_wall(scene)
    roof_underside(scene, roof_mesh)
    info = roof_structure(scene)
    rigging(scene)
    return info
