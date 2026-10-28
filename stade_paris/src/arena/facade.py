"""Enveloppe : couronne en béton blanc, socle vitré, bandeau, peau intérieure, écailles, débord,
auvents d'entrée, écrans LED et enseigne.

Toutes les pièces sont placées par rapport à une courbe de référence unique (nu de couronne,
offset 0) décalée le long de sa normale sortante : les arcs restent concentriques, aucun décalage
ne dérive entre les couches.
"""
import numpy as np

from . import dims
from .mesh import Mesh, grid_surface, quad, box, beam, tube, frame, flat_from_tris, concat
from .geo2d import smooth_closed

RIBBON_EDGES = (0, -2, 1, -3, 2)


class Ref:
    """Courbe de référence (offset 0) avec interpolation à l'abscisse s."""

    def __init__(self, p, n, s, extra=None):
        self.p, self.n, self.s = p, n, s
        self.extra = extra or {}
        self.length = s[-1]

    def at(self, s, off=0.0):
        s = np.asarray(s, float)
        x = np.interp(s, self.s, self.p[:, 0]); y = np.interp(s, self.s, self.p[:, 1])
        nx = np.interp(s, self.s, self.n[:, 0]); ny = np.interp(s, self.s, self.n[:, 1])
        nn = np.sqrt(nx * nx + ny * ny)
        nx, ny = nx / nn, ny / nn
        return np.stack([x + off * nx, y + off * ny], -1), np.stack([nx, ny], -1)

    def tangent(self, s):
        _, n = self.at(s)
        return np.stack([n[..., 1], -n[..., 0]], -1)   # sens de parcours (horaire)

    def get(self, key, s):
        return np.interp(s, self.s, self.extra[key])


def ribbon_ref(ds=0.25):
    """Partie en U (façades Est, Sud, Ouest) jusqu'au ruban d'écailles."""
    o = dims.outline(0.0, ds)
    sel = np.isin(o["edge"], RIBBON_EDGES) & (o["p"][:, 0] <= dims.X_RIBBON_END + 1e-6)
    idx = np.nonzero(sel)[0]
    p, n = o["p"][idx], o["n"][idx]
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))])
    return Ref(p, n, s)


def crown_ref(L):
    """Couronne : tout le contour sauf la façade Nord (arête 3). L = boucle de roof.edge_loop."""
    e = L["edge"]
    n = len(e)
    keep = e != 3
    # trouver le début de la séquence contiguë (après la fin de l'arête 3)
    start = int(np.nonzero(~keep)[0][-1] + 1) % n
    order = [(start + k) % n for k in range(n)]
    order = [i for i in order if keep[i]]
    p = L["p"][order] + L["n"][order] * 1.2       # retour au nu (offset 0) depuis la rive à -1,2 m
    nn = L["n"][order]
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))])
    return Ref(p, nn, s, {"H": L["H"][order]})


# ------------------------------------------------------------------ couronne
CROWN_PANEL_W = 5.25    # [DOC] modules simples 3 x 5,25 m (Infociments)


CROWN_FINE = 14         # points de la partie courbe (sous-face en bol + face)
CROWN_UNDER_Z = 19.80   # sous-face plate juste au-dessus des écailles (haut du rang 3 : 19,70 m)
CROWN_UNDER_OFF = -2.60  # départ du bol (les écailles débordent jusqu'à ≈ -2,05 m)
CROWN_BOWL = 0.55        # hauteur relative où le bol rejoint la face (P2/P4 : sous-face ≈ moitié de la couronne)


def crown_profile(H, zb=dims.Z_SCALES_TOP, fine=CROWN_FINE):
    """Profil (offset, z) de la couronne d'après P2/P4 : sous-face en bol, face, rebord arrondi.

    [0] départ intérieur (au-dessus de la peau intérieure)   [1] début du bol (sous-face plate)
    [2 .. 1+fine] quart d'ellipse puis face (répartis à abscisse curviligne constante)
    [-3 .. -1] rebord arrondi jusqu'à la rive du toit (offset -1,2 m, hauteur H mesurée au LiDAR).
    Retourne (points, abscisse curviligne cumulée de la partie [1 .. 1+fine]).
    """
    h = H - zb
    zc = zb + CROWN_BOWL * h                       # fin du bol / début de la face
    a = -0.05 - CROWN_UNDER_OFF                    # demi-axe horizontal du bol
    b = zc - CROWN_UNDER_Z                         # demi-axe vertical
    th = np.linspace(-np.pi / 2, 0, 40)
    bowl = np.stack([CROWN_UNDER_OFF + a * np.cos(th), zc + b * np.sin(th)], -1)
    face = np.array([(-0.03, zc + 0.35 * (H - 0.6 - zc)), (0.0, H - 0.6)])
    curve = np.vstack([bowl, face])
    seg = np.linalg.norm(np.diff(curve, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    t = np.linspace(0, cum[-1], fine + 1)
    res = np.stack([np.interp(t, cum, curve[:, 0]), np.interp(t, cum, curve[:, 1])], -1)
    head = [(dims.OFF_INNER_SKIN - 1.6, CROWN_UNDER_Z)]
    rim = [(-0.12, H - 0.22), (-0.50, H - 0.05), (-1.20, H)]
    pts = np.vstack([head, res, rim])
    return pts, t


def build_crown(L, scene):
    ref = crown_ref(L)
    S = ref.length
    ncol = max(1, int(round(S / CROWN_PANEL_W)))
    # échantillonnage : 3 points par panneau (suffisant pour les arcs de 32 m)
    sub = 3
    ss = np.linspace(0, S, ncol * sub + 1)
    H = smooth_closed(ref.get("H", ss), 3)
    # Profil identique en nombre de points pour toutes les colonnes ; chaque colonne choisit ses joints
    # horizontaux (~2,9 m d'abscisse curviligne) parmi ces points -> pas de fissure entre colonnes.
    zb = dims.Z_SCALES_TOP
    profs, arcs = [], []
    for h in H:
        pr, t = crown_profile(h)
        profs.append(pr); arcs.append(t)
    prof = np.array(profs)                       # (ns, k, 2)
    arcs = np.array(arcs)
    last = prof.shape[1] - 1
    nfine = CROWN_FINE

    def col_joints(cidx):
        t = arcs[cidx]
        rows = max(3, int(round(t[-1] / 2.9)))
        face_j = sorted({1 + int(np.argmin(np.abs(t - t[-1] * j / rows))) for j in range(1, rows)})
        return [0, 1] + face_j + [1 + nfine, last]
    P2, n2 = ref.at(ss)
    xy = P2[:, None, :] + prof[..., 0:1] * n2[:, None, :]
    P = np.concatenate([xy, prof[..., 1:2]], -1)   # (ns, k, 3)
    # normales lisses sur la surface continue
    full = grid_surface(P[:, ::-1], smooth=True)     # ordre k inversé : normales vers l'extérieur
    Nfull = full.N.reshape(P.shape[0], P.shape[1], 3)[:, ::-1]
    out = Mesh()
    npanels = 0
    for c in range(ncol):
        a, b = c * sub, (c + 1) * sub
        joints = col_joints((a + b) // 2)
        npanels += len(joints) - 1
        for r in range(len(joints) - 1):
            k0, k1 = joints[r], joints[r + 1]
            Pp = P[a:b + 1, k0:k1 + 1]
            Np = Nfull[a:b + 1, k0:k1 + 1]
            nu, nv = Pp.shape[:2]
            uu, vv = np.meshgrid(np.linspace(0, 1, nu), np.linspace(0, 1, nv), indexing="ij")
            m = grid_surface(Pp[:, ::-1], np.stack([uu, 1 - vv], -1)[:, ::-1], smooth=True)
            m.N = Np[:, ::-1].reshape(-1, 3)
            out.add(m)
    scene.add("crown", "crown", out)
    # extrémités de couronne contre la façade Nord : flasques verticales
    for s_end, sign in ((0.0, 1), (S, -1)):
        Pe, ne = ref.at(s_end)
        he = float(ref.get("H", s_end))
        pr, _ = crown_profile(he)
        poly3 = np.column_stack([Pe + pr[:, 0:1] * ne, pr[:, 1]])
        tris = [[poly3[0], poly3[i], poly3[i + 1]] for i in range(1, len(poly3) - 1)]
        m = flat_from_tris(np.array(tris))
        if sign < 0:
            m = m.flipped()
        scene.add("crown", "concrete_white", m.double_sided())
    ref.extra["panels"] = np.array([npanels])
    return ref


# ------------------------------------------------------------------ socle, bandeau, peau intérieure
def _band(ref, s0, s1, off0, off1, z0, z1, ds=1.0):
    """Ruban vertical (off0==off1) ou horizontal (z0==z1) entre deux abscisses."""
    n = max(2, int(np.ceil((s1 - s0) / ds)) + 1)
    ss = np.linspace(s0, s1, n)
    pa, _ = ref.at(ss, off0); pb, _ = ref.at(ss, off1)
    P = np.stack([np.column_stack([pa, np.full(n, z0)]), np.column_stack([pb, np.full(n, z1)])], 1)
    UV = np.stack([np.stack([ss, np.full(n, z0)], -1), np.stack([ss, np.full(n, z1)], -1)], 1)
    return P, UV


def _surf(P, UV, flip=False, uscale=1.0, vscale=1.0):
    UV = UV.copy(); UV[..., 0] *= uscale; UV[..., 1] *= vscale
    m = grid_surface(P if not flip else P[:, ::-1], UV if not flip else UV[:, ::-1])
    return m


def build_base(ref, scene, gaps):
    """Socle vitré (0–3,21 m), bandeau de signalétique, peau intérieure et nez de dalles.

    gaps : liste d'intervalles (s0, s1) où le socle est remplacé par les entrées.
    """
    S = ref.length
    rng = np.random.default_rng(3)
    zt = dims.Z_PLINTH_TOP
    # découpage en baies de 6 m : vitrées (70 %) ou panneaux blancs (30 %)
    edges = np.arange(0, S, 6.0).tolist() + [S]
    for a, b in zip(edges[:-1], edges[1:]):
        if any(g0 < (a + b) / 2 < g1 for g0, g1 in gaps):
            continue
        mat = "curtain_wall" if rng.random() < 0.72 else "alu_white"
        P, UV = _band(ref, a, b, dims.OFF_PLINTH, dims.OFF_PLINTH, 0.0, zt)
        scene.add("facade_base", mat, _surf(P, UV, flip=True, uscale=1 / 6.0, vscale=1 / zt) if mat == "curtain_wall"
                  else _surf(P, UV, flip=True, uscale=0.5, vscale=0.5))
    # bandeau blanc : face, dessus, sous-face
    o_in, o_out = dims.OFF_PLINTH, dims.OFF_PLINTH + 1.45
    z0, z1 = zt, dims.Z_BAND_TOP
    P, UV = _band(ref, 0, S, o_out, o_out, z0, z1)
    scene.add("facade_base", "alu_white", _surf(P, UV, flip=True, uscale=.5, vscale=.5))
    P, UV = _band(ref, 0, S, o_in, o_out, z1, z1)
    scene.add("facade_base", "alu_white", _surf(P, UV, flip=False, uscale=.5, vscale=.5))
    P, UV = _band(ref, 0, S, o_in, o_out, z0, z0)
    scene.add("facade_base", "alu_white", _surf(P, UV, flip=True, uscale=.5, vscale=.5))
    # peau intérieure vitrée derrière les écailles + nez de dalles
    zi = dims.Z_BAND_TOP
    P, UV = _band(ref, 0, S, dims.OFF_INNER_SKIN, dims.OFF_INNER_SKIN, zi, dims.Z_SCALES_TOP + 0.2)
    scene.add("facade_skin", "skin_light", _surf(P, UV, flip=True, uscale=1 / 6, vscale=1 / 6))
    for zs in (8.40, 12.90, 17.20):
        P, UV = _band(ref, 0, S, dims.OFF_INNER_SKIN + 0.05, dims.OFF_INNER_SKIN + 0.05, zs, zs + 0.45)
        scene.add("facade_skin", "alu_white", _surf(P, UV, flip=True, uscale=.5, vscale=.5))
    # retour de sous-face entre peau intérieure et couronne (masque le vide au-dessus des écailles)
    P, UV = _band(ref, 0, S, dims.OFF_INNER_SKIN, dims.OFF_INNER_SKIN + 0.05, dims.Z_SCALES_TOP + 0.2, dims.Z_SCALES_TOP + 0.15)
    scene.add("facade_skin", "alu_white", _surf(P, UV, flip=True, uscale=.5, vscale=.5))


# ------------------------------------------------------------------ écailles
LIGHT = True   # version allégée pour MX : surface simple double face, sans chants ni supports


def scale_shell(C, h, sag, yaw, drop=0.55, nu=7, nv=4, thick=0.035, split=None):
    """Une écaille dans son repère local (x tangent, y sortant, z haut ; origine bas-centre).

    Portion de cylindre (flèche 'sag'), bord haut/bas cisaillés (« drop ») comme sur P1-P3.
    split : fraction (0-1) de la largeur en panneau opaque côté bord d'attaque (type mixte).
    Retourne dict matériau -> Mesh.
    """
    a = np.linspace(-0.5, 0.5, nu)
    b = np.linspace(0, 1, nv)
    A, B = np.meshgrid(a, b, indexing="ij")
    x = A * C
    y = sag * (1 - (2 * A) ** 2)
    zb = -drop * (A + 0.5) ** 2
    z = zb + B * h
    c, s = np.cos(yaw), np.sin(yaw)
    X = x * c - y * s
    Y = x * s + y * c
    front = np.stack([X, Y, z], -1)
    # normale approx. du cylindre (vers l'extérieur)
    nx_ = 2 * sag * 4 * A / C * 0 + (-(-8 * sag * A / C)) * 0
    dydx = -8 * sag * A / C
    nloc = np.stack([-dydx, np.ones_like(A), np.zeros_like(A)], -1)
    nloc /= np.linalg.norm(nloc, axis=-1, keepdims=True)
    nrot = np.stack([nloc[..., 0] * c - nloc[..., 1] * s, nloc[..., 0] * s + nloc[..., 1] * c, nloc[..., 2]], -1)
    back = front - nrot * thick
    UV = np.stack([A + 0.5, B], -1)
    out = {}

    def add(mat, mm):
        out.setdefault(mat, Mesh()).add(mm)

    def piece(i0, i1, mat):
        F = front[i0:i1 + 1]; Bk = back[i0:i1 + 1]; uv = UV[i0:i1 + 1]
        mf = grid_surface(F, uv, smooth=True)
        mf.N = nrot[i0:i1 + 1].reshape(-1, 3)
        add(mat, mf)
        if LIGHT:
            add(mat, mf.flipped())
            return
        mb = grid_surface(Bk[:, ::-1], uv[:, ::-1], smooth=True)
        mb.N = -nrot[i0:i1 + 1, ::-1].reshape(-1, 3)
        add(mat, mb)

    if split is None:
        piece(0, nu - 1, "glass_scale")
    elif split >= 1:
        piece(0, nu - 1, "alu_white")
    else:
        k = int(round(split * (nu - 1)))
        k = min(max(k, 1), nu - 2)
        piece(0, k, "glass_scale")
        piece(k, nu - 1, "alu_white")
    if LIGHT:
        return out, front
    # chants (cadre aluminium)
    rim = []
    for (i, j) in [(slice(None), 0), (slice(None), -1)]:
        f = front[i, j]; bk = back[i, j]
        P = np.stack([f, bk], 1)
        rim.append(grid_surface(P if j == 0 else P[:, ::-1]))
    for i in (0, -1):
        f = front[i, :]; bk = back[i, :]
        P = np.stack([f, bk], 1)
        rim.append(grid_surface(P[:, ::-1] if i == 0 else P))
    for r in rim:
        add("alu_white", r)
    return out, front


def build_scales(ref, scene, exclusions, rng_seed=592):
    """Trois rangs d'écailles en quinconce. exclusions : liste de (row, s0, s1)."""
    rng = np.random.default_rng(rng_seed)
    S = ref.length
    pitch = dims.SCALE_PITCH
    n_total = 0
    counts = {"glass": 0, "mixed": 0, "opaque": 0}
    # gabarits par rang et type (instanciés)
    # Orientation symétrique par rapport à l'axe long [PHO] : vues depuis le Sud, les écailles des
    # façades longues apparaissent par la tranche (P2 côté Ouest, P4 côté Est) -> elles regardent
    # vers le Nord des deux côtés. Côté Est (Y<0) le sens de parcours va vers le Sud : yaw +.
    templates = {}
    for r, (z0, z1) in enumerate(dims.SCALE_ROWS):
        h = z1 - z0
        for typ, split in (("glass", None), ("mixed", 0.45), ("opaque", 1.0)):
            for sgn in (1, -1):
                shell, front = scale_shell(dims.SCALE_CHORD, h, dims.SCALE_SAG, sgn * dims.SCALE_YAW, split=split,
                                           nu=5 if LIGHT else 7, nv=2 if LIGHT else 4)
                if sgn < 0:   # miroir : remettre le bord de fuite (a=-0.5) en premier
                    pass
                templates[(r, typ, sgn)] = (shell, front)
    for r, (z0, z1) in enumerate(dims.SCALE_ROWS):
        h = z1 - z0
        n = int(np.floor(S / pitch))
        start = (S - n * pitch) / 2 + (0.5 * pitch if r % 2 else 0.0)
        for i in range(n):
            s = start + i * pitch
            if s > S - pitch * 0.4:
                continue
            if any(rr == r and a <= s <= b for rr, a, b in exclusions):
                continue
            u = rng.random()
            typ = "glass" if u < 0.45 else ("mixed" if u < 0.78 else "opaque")
            counts[typ] += 1
            p, nrm = ref.at(s, dims.OFF_SCALES)
            t = np.array([nrm[1], -nrm[0]])                    # sens de parcours
            M = frame((p[0], p[1], z0), (t[0], t[1], 0), (nrm[0], nrm[1], 0))
            sgn = 1 if p[1] < 0 else -1
            shell, front = templates[(r, typ, sgn)]
            for mat, mm in shell.items():
                scene.add("scales_r%d" % r, mat, mm.transformed(M))
            n_total += 1
            if LIGHT:
                continue
            # support : potelet vertical derrière le bord rentrant + 2 bras vers la peau intérieure
            fr = front[0, :, :] if sgn > 0 else front[-1, :, :]   # bord le plus proche de la peau
            pb = (M @ np.append(fr[0] + [0, -0.12, 0], 1))[:3]
            pt = (M @ np.append(fr[-1] + [0, -0.12, 0], 1))[:3]
            scene.add("scales_frame", "steel_galv", tube(pb, pt, 0.045, sides=6))
            for f in (0.22, 0.82):
                q = pb + (pt - pb) * f
                q2 = np.array([*(ref.at(s, dims.OFF_INNER_SKIN)[0]), q[2]])
                scene.add("scales_frame", "steel_galv", beam(q, q2, 0.07, 0.07))
            # réglette LED au pied de l'écaille (3 000 réglettes documentées)
            lb = (M @ np.append(fr[0] * 0 + [0, -0.05, 0.05], 1))[:3]
            scene.add("scales_led", "led_strip", beam(lb - np.append(t, 0) * 0.9, lb + np.append(t, 0) * 0.9, 0.06, 0.05))
    return n_total, counts


# ------------------------------------------------------------------ débord d'angle Sud-Ouest
def build_ledge(ref, scene):
    L = dims.LEDGE
    ss = ref.s
    pts = ref.p
    # s de début : façade Ouest à X = x_west ; fin : extrémité Sud à Y = y_end
    west = np.nonzero((pts[:, 1] > 80) & (pts[:, 0] <= L["x_west"]))[0]
    south = np.nonzero((pts[:, 0] < dims.X_SOUTH + 0.5) & (pts[:, 1] >= L["y_end"]))[0]
    s1 = ss[west].max() if len(west) else ref.length
    s0 = ss[south].min() if len(south) else 0
    z0, z1 = L["z"] - L["t"] / 2, L["z"] + L["t"] / 2
    for (a, b, za, zb_, flip) in ((dims.OFF_INNER_SKIN, L["off_out"], z1, z1, False),
                                  (dims.OFF_INNER_SKIN, L["off_out"], z0, z0, True),
                                  (L["off_out"], L["off_out"], z0, z1, True)):
        P, UV = _band(ref, s0, s1, a, b, za, zb_, 0.5)
        scene.add("ledge", "concrete_white", _surf(P, UV, flip=flip, uscale=.25, vscale=.25))
    # nez arrondi aux extrémités
    for s_end in (s0, s1):
        pa, nn = ref.at(s_end, dims.OFF_INNER_SKIN)
        pb, _ = ref.at(s_end, L["off_out"])
        t = np.array([nn[1], -nn[0]])
        sign = -1 if s_end == s0 else 1
        poly = [np.append(pa, z0), np.append(pb, z0), np.append(pb, z1), np.append(pa, z1)]
        m = quad(*poly) if sign > 0 else quad(*poly[::-1])
        scene.add("ledge", "concrete_white", m.double_sided())
    return s0, s1


# ------------------------------------------------------------------ entrées, écrans, enseigne
def entrance_s(ref, ent):
    """Abscisse s du centre de l'entrée sur la façade longue."""
    side = ent["side"]
    pts = ref.p
    cand = np.nonzero(np.abs(pts[:, 1] - side * dims.HALF_W) < 0.01)[0]
    k = cand[np.argmin(np.abs(pts[cand, 0] - ent["x"]))]
    return ref.s[k]


def _rounded_rect(w, d, r, n=5):
    """Plan d'auvent (sens anti-horaire) : x ∈ [-w/2, w/2], y ∈ [0, d], angles avant (y=d) arrondis."""
    pts = [(-w / 2, 0.0), (w / 2, 0.0)]
    for k in range(n + 1):                       # angle avant droit : 0 -> 90°
        a = np.pi / 2 * k / n
        pts.append((w / 2 - r + r * np.cos(a), d - r + r * np.sin(a)))
    for k in range(n + 1):                       # angle avant gauche : 90° -> 180°
        a = np.pi / 2 + np.pi / 2 * k / n
        pts.append((-w / 2 + r + r * np.cos(a), d - r + r * np.sin(a)))
    return np.array(pts)


def build_entrances(ref, scene):
    """Auvents, vitrages d'entrée, écrans LED, enseigne. Retourne exclusions écailles et trous du socle."""
    excl, gaps = [], []
    for name, e in dims.ENTRANCES.items():
        sc = entrance_s(ref, e)
        p, nrm = ref.at(sc, 0.0)
        t = np.array([nrm[1], -nrm[0]])
        # repère local : x = sens de parcours de la courbe (s croissant), y vers l'extérieur, z haut
        side = float(e["side"])
        base = np.array([e["x"], side * dims.HALF_W])
        M = frame((base[0], base[1], 0.0), (side, 0, 0), (0, side, 0))
        w, d = e["canopy_w"], e["canopy_d"]
        # auvent : volume blanc à angles arrondis, de la peau intérieure jusqu'à +d
        y0 = dims.OFF_INNER_SKIN
        pl = _rounded_rect(w, d - y0, 1.6) + [0, y0]
        from .mesh import prism
        cm = prism(pl, e["z0"], e["z1"], uv_scale=0.25)
        scene.add("entrances", "alu_white", cm.transformed(M))
        # spots en sous-face
        for xx in np.linspace(-w / 2 + 2, w / 2 - 2, int(w / 3)):
            for yy in (1.0, d * 0.6):
                scene.add("entrances", "light", box((0.35, 0.35, 0.03), M @ _T(xx, yy, e["z0"] - 0.02)))
        # vitrage d'entrée (mur-rideau en retrait sous l'auvent)
        gw = e["glass_w"]
        g = quad((-gw / 2, -2.6, 0), (gw / 2, -2.6, 0), (gw / 2, -2.6, e["z0"]), (-gw / 2, -2.6, e["z0"]),
                 uv=((0, 0), (gw / 6, 0), (gw / 6, e["z0"] / 3.21), (0, e["z0"] / 3.21)))
        # orienté vers +y (extérieur local)
        g = g if g.N[0][1] > 0 else g.flipped()
        scene.add("entrances", "curtain_wall", g.transformed(M))
        # retours latéraux du sas
        for sx in (-1, 1):
            q = quad((sx * gw / 2, -2.6, 0), (sx * gw / 2, 0.0, 0), (sx * gw / 2, 0.0, e["z0"]), (sx * gw / 2, -2.6, e["z0"]))
            scene.add("entrances", "alu_white", q.double_sided().transformed(M))
        gaps.append((sc - gw / 2, sc + gw / 2))
        # enseigne sur le front de l'auvent (ratio image 8:1)
        if e.get("sign"):
            hs = e["z1"] - e["z0"]
            sw = min(w - 1.0, hs * 0.62 * 8)
            sh = sw / 8
            zc = (e["z0"] + e["z1"]) / 2 + 0.15
            yy = d + 0.06
            sg = quad((-sw / 2, yy, zc - sh / 2), (sw / 2, yy, zc - sh / 2), (sw / 2, yy, zc + sh / 2), (-sw / 2, yy, zc + sh / 2))
            sg = sg if sg.N[0][1] > 0 else _flip_uv(sg)
            scene.add("entrances", "signage", sg.transformed(M))
        # écrans LED de part et d'autre
        sw_, sh_ = e["screen_w"], e["screen_h"]
        for sx in (-1, 1):
            xc = sx * (w / 2 + 1.0 + sw_ / 2)
            z0 = e["screen_z"]
            y_face = 0.65
            frame_m = box((sw_ + 0.5, 0.6, sh_ + 0.5), M @ _T(xc, y_face - 0.3, z0 + sh_ / 2))
            scene.add("entrances", "alu_white", frame_m)
            face = quad((xc - sw_ / 2, y_face + 0.01, z0), (xc + sw_ / 2, y_face + 0.01, z0),
                        (xc + sw_ / 2, y_face + 0.01, z0 + sh_), (xc - sw_ / 2, y_face + 0.01, z0 + sh_),
                        uv=((0, 0), (sw_ / 3, 0), (sw_ / 3, sh_ / 3), (0, sh_ / 3)))
            face = face if face.N[0][1] > 0 else _flip_uv(face)
            scene.add("entrances", "led_off", face.transformed(M))
            # consoles vers la structure
            for zz in (z0 + 1.0, z0 + sh_ - 1.0):
                for xo in (-sw_ / 3, sw_ / 3):
                    scene.add("entrances", "steel_galv", beam(_pt(M, xc + xo, dims.OFF_INNER_SKIN, zz), _pt(M, xc + xo, 0.0, zz), 0.15, 0.15))
            a, b = sc + xc - sw_ / 2, sc + xc + sw_ / 2      # x local == sens de s
            for r, (rz0, rz1) in enumerate(dims.SCALE_ROWS):
                if rz0 < z0 + sh_ + 0.3 and rz1 > z0:
                    excl.append((r, a - 1.2, b + 1.2))
        # rang bas supprimé au droit de l'auvent
        excl.append((0, sc - w / 2 - 1.0, sc + w / 2 + 1.0))
        if e["z1"] > dims.SCALE_ROWS[1][0]:
            excl.append((1, sc - w / 2 + 0.5, sc + w / 2 - 0.5))
    return excl, gaps


def _area(p):
    return 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])


def _T(x, y, z):
    M = np.eye(4); M[:3, 3] = (x, y, z); return M


def _pt(M, x, y, z):
    return (M @ np.array([x, y, z, 1.0]))[:3]


def _flip_uv(m):
    f = m.flipped()
    f.UV[:, 0] = f.UV[:, 0].max() + f.UV[:, 0].min() - f.UV[:, 0]
    return f
