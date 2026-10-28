"""Tribunes en U : gradins bas et hauts, loges, escaliers, vomitoires, garde-corps et sièges.

Coupe type (distance d au bord du sol, hauteur z) [PHO P5, P7, P9, P10 + coupe ACDP] :
  0,0–2,0   circulation au pied des tribunes (niveau sol)
  2,0       mur de front (1,10 m) + panneaux LED
  2,0–21,2  tribune basse : 24 rangs de 0,80 m, contremarches 0,36 -> 0,46 m (≈ 27°)
  21,2–23,0 coursive haute de la tribune basse ; vitrage des loges à d = 23,0 (z 11,4–14,2)
  19,4      nez de la tribune haute (bandeau blanc + anneau LED, z 14,2–15,6), en surplomb
  19,8–…    tribune haute : jusqu'à 19 rangs, contremarches 0,55 -> 0,62 m (≈ 36°),
            limitée par la façade et la sous-face de toiture (moins de rangs côté Sud)
Escaliers tous les 8 m (radiaux dans les angles), vomitoires dans la tribune basse.
"""
import numpy as np

from . import dims
from .facade import Ref
from .mesh import Mesh, box, beam, quad, grid_surface, tube, concat, flat_from_tris
from .geo2d import point_in_poly
from .roof import field

SEAT_PITCH = 0.50
ROW_DEPTH = 0.80
AISLE_W = 1.20
AISLE_SPACING = 8.0

LOWER = dict(d0=2.0, z0=1.10, rows=24, r0=0.36, r1=0.46)
UPPER = dict(d0=19.8, z0=15.60, rows=19, r0=0.55, r1=0.62)
FRONT_UPPER_D = 19.4
SOFFIT_Z = 14.2
BOX_GLASS_D = 23.0
CROSS_AISLE_Z = None   # calculé


def tier_profile(t, nrows=None):
    n = t["rows"] if nrows is None else nrows
    d = t["d0"] + ROW_DEPTH * np.arange(n + 1)
    r = t["r0"] + (t["r1"] - t["r0"]) * (np.arange(n) / max(1, t["rows"] - 1)) ** 1.2
    z = t["z0"] + np.concatenate([[0], np.cumsum(r)])
    return d, z      # d[k], z[k] : bord avant et niveau du rang k (k=n : arrière)


def floor_ref(ds=0.5):
    f = dims.floor_outline(ds)
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(f, axis=0), axis=1))])
    t = np.gradient(f, axis=0)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    n = np.stack([-t[:, 1], t[:, 0]], -1)          # parcours horaire -> extérieur à gauche
    return Ref(f, n, s)


def _scale(ref, s, d):
    """Facteur longueur réelle / longueur de base à l'offset d (1 sur les droites)."""
    eps = 0.05
    a, _ = ref.at(s - eps, d); b, _ = ref.at(s + eps, d)
    return np.linalg.norm(b - a, axis=-1) / (2 * eps)


def segments(ref):
    """Découpage en blocs de sièges / escaliers (abscisses de base)."""
    S = ref.length
    n = int(np.round(S / AISLE_SPACING))
    cs = np.linspace(0, S, n + 1)[1:-1]            # axes d'escaliers (pas aux extrémités)
    return cs


def facade_limit(ref, s):
    """Distance d max (le long de la normale) jusqu'à l'intérieur de la couronne (offset -2,6)."""
    poly = dims.outline(-2.6, 1.0)["p"]
    out = []
    for si in np.atleast_1d(s):
        lo, hi = 0.0, 60.0
        for _ in range(30):
            mid = (lo + hi) / 2
            p, _ = ref.at(si, mid)
            if point_in_poly(p[None], poly)[0]:
                lo = mid
            else:
                hi = mid
        out.append(lo)
    return np.array(out)


def roof_under(X, Y):
    return field()(X, Y) - 1.4      # bac + pannes


def upper_rows_for(ref, s):
    """Nombre de rangs hauts possibles en s (façade + garde sous toiture 2,6 m)."""
    dmax = facade_limit(ref, s)[0] - 0.8
    d, z = tier_profile(UPPER)
    n = 0
    for k in range(UPPER["rows"]):
        p, _ = ref.at(s, d[k + 1])
        if d[k + 1] <= dmax and z[k + 1] + 2.6 <= roof_under(p[0], p[1]):
            n = k + 1
        else:
            break
    return n


# ------------------------------------------------------------------ surfaces de gradins
def _strip(ref, s0, s1, d0, d1, z0, z1, ds=3.0, flip=False, uvs=0.5):
    n = max(2, int(np.ceil((s1 - s0) / ds)) + 1)
    ss = np.linspace(s0, s1, n)
    pa, _ = ref.at(ss, d0); pb, _ = ref.at(ss, d1)
    P = np.stack([np.column_stack([pa, np.full(n, z0)]), np.column_stack([pb, np.full(n, z1)])], 1)
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pa, axis=0), axis=1))])
    w = np.hypot(d1 - d0, z1 - z0)
    UV = np.stack([np.stack([L * uvs, np.zeros(n)], -1), np.stack([L * uvs, np.full(n, w * uvs)], -1)], 1)
    return grid_surface(P[:, ::-1] if flip else P, UV[:, ::-1] if flip else UV)


def steps(ref, s0, s1, tier, nrows, mat_scene, part):
    d, z = tier_profile(tier, nrows)
    out = Mesh()
    for k in range(nrows):
        # giron (horizontal, face vers le haut) : la courbe tourne en sens horaire -> 'flip' selon orientation
        out.add(_strip(ref, s0, s1, d[k], d[k + 1], z[k], z[k], flip=False))
        # contremarche (verticale, face vers le sol de l'arène)
        out.add(_strip(ref, s0, s1, d[k + 1], d[k + 1], z[k], z[k + 1], flip=False))
    return out


# ------------------------------------------------------------------ sièges
def seat_template():
    """Siège à assise relevée (P7, P8) : coque dossier+assise, pied ; repère : x le long du rang,
    y vers l'avant (vers le sol de l'arène), z haut ; origine au niveau du giron."""
    from .mesh import Rx, T, _drop_box_faces
    # coque (dossier + assise relevée) légèrement inclinée vers l'arrière ; face inférieure supprimée
    shell = _drop_box_faces(box((0.46, 0.14, 0.52)), (5,))
    shell = shell.transformed(T(0, -0.30, 0.64) @ Rx(np.radians(-10)))
    # pied : simple plaque frontale (seule face visible)
    leg = quad((-0.04, -0.24, 0.0), (0.04, -0.24, 0.0), (0.04, -0.24, 0.40), (-0.04, -0.24, 0.40))
    if leg.N[0][1] < 0:
        leg = leg.flipped()
    used = np.unique(shell.F)
    remap = np.full(shell.nv, -1); remap[used] = np.arange(len(used))
    shell = Mesh(shell.V[used], shell.N[used], shell.UV[used], remap[shell.F])
    m = concat([shell, leg])
    m.UV[:] = (0.25, 0.5)          # zone unie de l'atlas seat_atlas.png
    return m


def seat_row_strip(ref, s0, s1, dk, zk):
    """Version lointaine (LOD) d'un rang : bande verticale texturée (silhouettes de sièges, alpha)."""
    dseat = dk + 0.42 - 0.30
    n = max(2, int(np.ceil((s1 - s0) / 1.5)) + 1)
    ss = np.linspace(s0, s1, n)
    P, N = ref.at(ss, dseat)
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    # un quad indépendant par paire de sièges (1,0 m) : UV dans la moitié droite de l'atlas
    out = Mesh()
    nseg = max(1, int(np.ceil(L[-1] / (2 * SEAT_PITCH))))
    for i in range(nseg):
        l0 = i * 2 * SEAT_PITCH; l1 = min(L[-1], l0 + 2 * SEAT_PITCH)
        if l1 - l0 < 0.2:
            continue
        a = np.array([np.interp(l0, L, P[:, 0]), np.interp(l0, L, P[:, 1])])
        b = np.array([np.interp(l1, L, P[:, 0]), np.interp(l1, L, P[:, 1])])
        u1 = 0.5 + 0.5 * (l1 - l0) / (2 * SEAT_PITCH)
        q = quad((*a, zk + 0.36), (*b, zk + 0.36), (*b, zk + 0.92), (*a, zk + 0.92), uv=((0.5, 0), (u1, 0), (u1, 1), (0.5, 1)))
        out.add(q)                    # parcours horaire : normale = vers le sol de l'arène
    return out


def seat_band(ref, s0, s1, dk, zk, skip=(), ds=3.0):
    """Rang de sièges allégé : bande inclinée opaque texturée (un siège = 0,50 m de texture).
    Remplace ~24 sommets par siège par ~4 sommets tous les 3 m. Coupée au droit des vomitoires."""
    ranges = [(s0, s1)]
    for a, b in skip:
        nr = []
        for x0, x1 in ranges:
            if b <= x0 or a >= x1:
                nr.append((x0, x1))
            else:
                if a > x0:
                    nr.append((x0, a))
                if b < x1:
                    nr.append((b, x1))
        ranges = nr
    out = Mesh()
    for x0, x1 in ranges:
        n = max(2, int(np.ceil((x1 - x0) / ds)) + 1)
        ss = np.linspace(x0, x1, n)
        lo, _ = ref.at(ss, dk + 0.60)
        hi, _ = ref.at(ss, dk + 0.70)
        L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(lo, axis=0), axis=1))])
        P = np.stack([np.column_stack([lo, np.full(n, zk + 0.38)]), np.column_stack([hi, np.full(n, zk + 0.92)])], 1)
        UV = np.stack([np.column_stack([L / SEAT_PITCH, np.zeros(n)]), np.column_stack([L / SEAT_PITCH, np.ones(n)])], 1)
        out.add(grid_surface(P, UV))     # parcours horaire + montée : face vers le sol de l'arène
    return out


def instance_z(tmpl, pos, yaw):
    """Instancie un gabarit avec rotation autour de Z + translation (vectorisé)."""
    n = len(pos)
    c, s = np.cos(yaw), np.sin(yaw)
    V = tmpl.V[None, :, :]
    X = V[..., 0] * c[:, None] - V[..., 1] * s[:, None] + pos[:, 0:1]
    Y = V[..., 0] * s[:, None] + V[..., 1] * c[:, None] + pos[:, 1:2]
    Z = V[..., 2] + pos[:, 2:3]
    N = tmpl.N[None, :, :]
    NX = N[..., 0] * c[:, None] - N[..., 1] * s[:, None]
    NY = N[..., 0] * s[:, None] + N[..., 1] * c[:, None]
    NZ = np.broadcast_to(N[..., 2], NX.shape)
    nv = tmpl.nv
    F = (tmpl.F[None, :, :] + (np.arange(n) * nv)[:, None, None]).reshape(-1, 3)
    return Mesh(np.stack([X, Y, Z], -1).reshape(-1, 3), np.stack([NX, NY, NZ], -1).reshape(-1, 3),
                np.tile(tmpl.UV, (n, 1)), F)


def seats_in_row(ref, s0, s1, dk, zk, skip=None):
    """Positions des sièges d'un rang entre s0 et s1 (base), au pas réel de 0,50 m."""
    dseat = dk + 0.42        # position du siège dans le giron (dossier vers l'arrière)
    ss = np.linspace(s0, s1, max(3, int((s1 - s0) * 8)))
    P, N = ref.at(ss, dseat)
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    if L[-1] < SEAT_PITCH:
        return np.zeros((0, 3)), np.zeros(0)
    nseat = int(np.floor((L[-1] - 0.10) / SEAT_PITCH))
    if nseat <= 0:
        return np.zeros((0, 3)), np.zeros(0)
    start = (L[-1] - nseat * SEAT_PITCH) / 2 + SEAT_PITCH / 2
    li = start + SEAT_PITCH * np.arange(nseat)
    si = np.interp(li, L, ss)
    if skip is not None:
        keep = ~np.any([(si > a) & (si < b) for a, b in skip], axis=0) if len(skip) else np.ones(len(si), bool)
        si = si[keep]
    p, n = ref.at(si, dseat)
    # le siège regarde vers le sol de l'arène : y local = -normale sortante
    yaw = np.arctan2(-n[:, 1], -n[:, 0]) - np.pi / 2
    pos = np.column_stack([p, np.full(len(p), zk)])
    return pos, yaw


# ------------------------------------------------------------------ construction
def build(scene, with_seats=True):
    ref = floor_ref()
    S = ref.length
    cs = segments(ref)
    tmpl = seat_template()
    rng = np.random.default_rng(7)
    seat_count = {"lower": 0, "upper": 0}
    dL, zL = tier_profile(LOWER)
    edges = np.concatenate([[0.0], cs, [S]])
    # vomitoires : un escalier sur trois dans les longs pans, au centre du bloc suivant
    vom_blocks = set(range(1, len(edges) - 1, 3))

    # ---- mur de front et circulation basse
    scene.add("bowl", "wall_black", _strip(ref, 0, S, LOWER["d0"], LOWER["d0"], 0.0, LOWER["z0"], flip=False))
    scene.add("bowl", "led_off", _strip(ref, 0, S, LOWER["d0"] - 0.08, LOWER["d0"] - 0.08, 0.15, 0.95, flip=False, uvs=1 / 3))
    scene.add("bowl", "concrete_grey", _strip(ref, 0, S, LOWER["d0"] - 0.08, LOWER["d0"], LOWER["z0"], LOWER["z0"], flip=False))

    upper_counts = []
    for b in range(len(edges) - 1):
        s0, s1 = edges[b], edges[b + 1]
        mid = (s0 + s1) / 2
        upper_counts.append(upper_rows_for(ref, mid))
    upper_counts = np.array(upper_counts)

    for b in range(len(edges) - 1):
        s0, s1 = edges[b], edges[b + 1]
        # ---------------- tribune basse
        scene.add("bowl_lower", "concrete_grey", steps(ref, s0, s1, LOWER, LOWER["rows"], None, None))
        # ---------------- tribune haute (rangs limités)
        nu = int(upper_counts[b])
        if nu > 0:
            scene.add("bowl_upper", "concrete_grey", steps(ref, s0, s1, UPPER, nu, None, None))
            dU, zU = tier_profile(UPPER, nu)
            # mur arrière jusqu'à la toiture
            ss = np.linspace(s0, s1, max(2, int((s1 - s0) / 3.0) + 1))
            pb, _ = ref.at(ss, dU[-1] + 0.4)
            ztop = roof_under(pb[:, 0], pb[:, 1]) + 0.6
            P = np.stack([np.column_stack([pb, np.full(len(ss), zU[-1])]), np.column_stack([pb, ztop])], 1)
            scene.add("bowl_upper", "wall_black", grid_surface(P))
            scene.add("bowl_upper", "concrete_grey", _strip(ref, s0, s1, dU[-1], dU[-1] + 0.4, zU[-1], zU[-1], flip=False))
            # côtés des blocs voisins de hauteurs différentes : joue verticale
            for sb, other in ((s0, upper_counts[b - 1] if b > 0 else 0), (s1, upper_counts[b + 1] if b + 1 < len(upper_counts) else 0)):
                if other < nu:
                    d2, z2 = tier_profile(UPPER, nu)
                    poly = [(d2[0], z2[0])]
                    for k in range(int(other), nu):
                        poly += [(d2[k + 1], z2[k]), (d2[k + 1], z2[k + 1])]
                    poly += [(d2[-1] + 0.4, z2[-1]), (d2[-1] + 0.4, z2[int(other)] if other > 0 else z2[0]), ]
                    _cheek(scene, ref, sb, poly, d2[int(other)] if other > 0 else d2[0])
        # ---------------- sièges
        if with_seats:
            aisle_a = s0 if b == 0 else s0
            for tier, name, nrows in ((LOWER, "lower", LOWER["rows"]), (UPPER, "upper", nu)):
                d, z = tier_profile(tier, nrows)
                for k in range(nrows):
                    sc = _scale(ref, np.array([s0 + 0.01, s1 - 0.01]), d[k] + 0.42)
                    a = s0 + (AISLE_W / 2 / sc[0] if b > 0 else 0.3)
                    c = s1 - (AISLE_W / 2 / sc[1] if b < len(edges) - 2 else 0.3)
                    skip = []
                    if name == "lower" and b in vom_blocks and 10 <= k <= 17:
                        m = (s0 + s1) / 2
                        skip = [(m - 2.0, m + 2.0)]
                    pos, yaw = seats_in_row(ref, a, c, d[k], z[k], skip)
                    if len(pos):
                        seat_count[name] += len(pos)          # comptage des places (pas de géométrie par siège)
                        scene.add("seats_" + name, "seat", seat_band(ref, a, c, d[k], z[k], skip))
        # ---------------- vomitoire (tribune basse)
        if b in vom_blocks:
            _vomitory(scene, ref, (s0 + s1) / 2)
    # ---------------- escaliers (marches intermédiaires + main courante)
    for c in cs:
        b = int(np.searchsorted(edges, c)) - 1
        nu = int(min(upper_counts[max(0, b)], upper_counts[min(len(upper_counts) - 1, b + 1)]))
        for tier, nrows, part in ((LOWER, LOWER["rows"], "stairs_lower"), (UPPER, nu, "stairs_upper")):
            if nrows <= 0:
                continue
            d, z = tier_profile(tier, nrows)
            for k in range(nrows):
                sc = float(_scale(ref, np.array([c]), d[k] + 0.4)[0])
                p0, n0 = ref.at(c, d[k] + 0.6)
                t = np.array([n0[1], -n0[0]])
                r = z[k + 1] - z[k]
                ctr = np.array([p0[0], p0[1], z[k] + r / 4])
                from .mesh import frame
                M = frame(ctr, (t[0], t[1], 0), (n0[0], n0[1], 0))
                from .mesh import _drop_box_faces
                scene.add(part, "concrete_grey", _drop_box_faces(box((AISLE_W, 0.4, r / 2), M, 0.5), (0, 1, 2, 5)))
            # main courante axiale
            pa, _ = ref.at(c, d[0] + 0.2); pb, _ = ref.at(c, d[-1] - 0.2)
            scene.add(part, "steel_galv", tube((pa[0], pa[1], z[0] + 0.95), (pb[0], pb[1], z[-1] + 0.95), 0.025, 4))
            for k in range(0, nrows, 8):
                pk, _ = ref.at(c, d[k] + 0.4)
                scene.add(part, "steel_galv", tube((pk[0], pk[1], z[k]), (pk[0], pk[1], z[k] + 0.95), 0.02, 4))

    # ---------------- coursive, loges, sous-face, nez de la tribune haute
    dLb, zLb = dL[-1], zL[-1]
    scene.add("bowl", "concrete_grey", _strip(ref, 0, S, dLb, BOX_GLASS_D, zLb, zLb, flip=False))
    scene.add("bowl", "railing", _strip(ref, 0, S, dLb + 0.05, dLb + 0.05, zLb, zLb + 1.0, flip=False, uvs=1.0).double_sided())
    scene.add("bowl", "glass_dark", _strip(ref, 0, S, BOX_GLASS_D, BOX_GLASS_D, zLb, SOFFIT_Z, flip=False, uvs=0.25))
    for s in np.arange(2.0, S, 4.0):        # meneaux des loges
        p, n = ref.at(s, BOX_GLASS_D - 0.05)
        scene.add("bowl", "steel_black", box((0.08, 0.08, SOFFIT_Z - zLb)).transformed(_TT(p[0], p[1], (zLb + SOFFIT_Z) / 2)))
    scene.add("bowl", "concrete_grey", _strip(ref, 0, S, FRONT_UPPER_D, BOX_GLASS_D, SOFFIT_Z, SOFFIT_Z, flip=True))
    # nez : bandeau blanc (bas), anneau LED (milieu), garde-corps vitré (haut)
    scene.add("bowl", "alu_white", _strip(ref, 0, S, FRONT_UPPER_D, FRONT_UPPER_D, SOFFIT_Z, SOFFIT_Z + 0.35, flip=False))
    scene.add("bowl", "led_ribbon", _strip(ref, 0, S, FRONT_UPPER_D - 0.02, FRONT_UPPER_D - 0.02, SOFFIT_Z + 0.35, UPPER["z0"] - 0.15, flip=False, uvs=1 / 6.0))
    scene.add("bowl", "alu_white", _strip(ref, 0, S, FRONT_UPPER_D, FRONT_UPPER_D, UPPER["z0"] - 0.15, UPPER["z0"], flip=False))
    scene.add("bowl", "concrete_grey", _strip(ref, 0, S, FRONT_UPPER_D, UPPER["d0"], UPPER["z0"], UPPER["z0"], flip=False))
    scene.add("bowl", "railing", _strip(ref, 0, S, FRONT_UPPER_D + 0.1, FRONT_UPPER_D + 0.1, UPPER["z0"], UPPER["z0"] + 1.05, flip=False, uvs=1.0).double_sided())
    return dict(seats=seat_count, seats_total=int(sum(seat_count.values())), blocks=len(edges) - 1,
                upper_rows_min=int(upper_counts.min()), upper_rows_max=int(upper_counts.max()))


def _TT(x, y, z):
    M = np.eye(4); M[:3, 3] = (x, y, z); return M


def _cheek(scene, ref, s, poly_dz, d_start):
    """Joue verticale en bout de bloc (profil (d, z) fermé jusqu'au rang de départ)."""
    P2, n = ref.at(s, 0.0)
    pts = []
    for d, z in poly_dz:
        p, _ = ref.at(s, d)
        pts.append((p[0], p[1], z))
    pts = np.array(pts)
    tris = [[pts[0], pts[i], pts[i + 1]] for i in range(1, len(pts) - 1)]
    scene.add("bowl_upper", "concrete_grey", flat_from_tris(np.array(tris)).double_sided())


def _vomitory(scene, ref, s):
    """Débouché de vomitoire dans la tribune basse (rangs 10–17) : ouverture sombre + joues + garde-corps."""
    d, z = tier_profile(LOWER)
    k0, k1 = 10, 18
    w = 3.6
    p0, n0 = ref.at(s, d[k0])
    t = np.array([n0[1], -n0[0]])
    from .mesh import frame
    M = frame((p0[0], p0[1], z[k0]), (t[0], t[1], 0), (n0[0], n0[1], 0))
    depth = d[k1] - d[k0]
    h = z[k1] - z[k0]
    # sol du vomitoire
    scene.add("bowl_lower", "concrete_grey", box((w, depth, 0.1), M @ _TT(0, depth / 2, -0.05)))
    # fond sombre (tunnel)
    scene.add("bowl_lower", "wall_black", box((w, 0.2, h + 0.4), M @ _TT(0, depth, h / 2 + 0.2)))
    # joues latérales + linteau
    for sx in (-1, 1):
        prof = np.array([(0, 0), (depth, 0), (depth, h + 0.6), (0, 0.9)])
        V = np.array([[sx * w / 2, y, zz] for y, zz in prof])
        Vw = (M @ np.column_stack([V, np.ones(len(V))]).T).T[:, :3]
        m = flat_from_tris(np.array([[Vw[0], Vw[1], Vw[2]], [Vw[0], Vw[2], Vw[3]]])).double_sided()
        scene.add("bowl_lower", "concrete_grey", m)
        a = (M @ np.array([sx * w / 2, 0, 0.9, 1]))[:3]; b = (M @ np.array([sx * w / 2, depth, h + 0.6 + 0.9, 1]))[:3]
        scene.add("bowl_lower", "steel_galv", tube(a, b, 0.03, 6))
    scene.add("bowl_lower", "concrete_grey", box((w + 0.6, 1.2, 0.4), M @ _TT(0, depth - 0.6, h + 0.2)))
