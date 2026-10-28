"""Noyau géométrique minimal (numpy) : maillages triangulés avec normales et UV par sommet.

Convention : mètres, Z vers le haut, triangles en sens anti-horaire vus de l'extérieur.
"""
import numpy as np


def _n(v):
    l = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.where(l < 1e-12, 1, l)


class Mesh:
    __slots__ = ("V", "N", "UV", "F")

    def __init__(self, V=None, N=None, UV=None, F=None):
        self.V = np.zeros((0, 3)) if V is None else np.asarray(V, float).reshape(-1, 3)
        self.N = np.zeros((0, 3)) if N is None else np.asarray(N, float).reshape(-1, 3)
        self.UV = np.zeros((0, 2)) if UV is None else np.asarray(UV, float).reshape(-1, 2)
        self.F = np.zeros((0, 3), int) if F is None else np.asarray(F, int).reshape(-1, 3)

    @property
    def nv(self):
        return len(self.V)

    @property
    def nf(self):
        return len(self.F)

    def copy(self):
        return Mesh(self.V.copy(), self.N.copy(), self.UV.copy(), self.F.copy())

    def add(self, other):
        if other is None or other.nv == 0:
            return self
        off = self.nv
        self.V = np.vstack([self.V, other.V])
        self.N = np.vstack([self.N, other.N])
        self.UV = np.vstack([self.UV, other.UV])
        self.F = np.vstack([self.F, other.F + off])
        return self

    def transformed(self, M):
        """M : matrice 4x4 (rotation/échelle uniforme + translation)."""
        m = self.copy()
        R = M[:3, :3]
        m.V = self.V @ R.T + M[:3, 3]
        m.N = _n(self.N @ np.linalg.inv(R))  # normale = inverse transposée
        if np.linalg.det(R) < 0:
            m.F = m.F[:, ::-1]
        return m

    def flipped(self):
        m = self.copy()
        m.F = m.F[:, ::-1].copy()
        m.N = -m.N
        return m

    def double_sided(self):
        return self.copy().add(self.flipped())

    def recompute_normals(self, smooth=True):
        a, b, c = self.V[self.F[:, 0]], self.V[self.F[:, 1]], self.V[self.F[:, 2]]
        fn = np.cross(b - a, c - a)
        if smooth:
            n = np.zeros_like(self.V)
            for k in range(3):
                np.add.at(n, self.F[:, k], fn)
            self.N = _n(n)
        else:
            raise ValueError("flat : utiliser flat_from_tris")
        return self

    def drop_degenerate(self, eps=1e-10):
        a, b, c = self.V[self.F[:, 0]], self.V[self.F[:, 1]], self.V[self.F[:, 2]]
        area = np.linalg.norm(np.cross(b - a, c - a), axis=1)
        self.F = self.F[area > eps]
        return self

    def bounds(self):
        return self.V.min(0), self.V.max(0)


def concat(meshes):
    out = Mesh()
    for m in meshes:
        out.add(m)
    return out


# ------------------------------------------------------------------ transformations
def T(x=0, y=0, z=0):
    M = np.eye(4)
    M[:3, 3] = (x, y, z)
    return M


def Rz(a):
    c, s = np.cos(a), np.sin(a)
    M = np.eye(4)
    M[:2, :2] = [[c, -s], [s, c]]
    return M


def Rx(a):
    c, s = np.cos(a), np.sin(a)
    M = np.eye(4)
    M[1:3, 1:3] = [[c, -s], [s, c]]
    return M


def Ry(a):
    c, s = np.cos(a), np.sin(a)
    M = np.eye(4)
    M[0, 0], M[0, 2], M[2, 0], M[2, 2] = c, s, -s, c
    return M


def S(k):
    M = np.eye(4)
    M[0, 0] = M[1, 1] = M[2, 2] = k
    return M


def frame(origin, xdir, ydir):
    """Matrice locale -> monde avec axes X=xdir, Y=ydir (orthonormalisé), Z = X×Y."""
    x = _n(np.asarray(xdir, float))
    y = np.asarray(ydir, float)
    y = _n(y - x * np.dot(x, y))
    z = np.cross(x, y)
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, y, z, origin
    return M


# ------------------------------------------------------------------ primitives
def flat_from_tris(P, UV=None):
    """P : (m,3,3) triangles indépendants -> normales plates."""
    P = np.asarray(P, float).reshape(-1, 3, 3)
    fn = _n(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]))
    V = P.reshape(-1, 3)
    N = np.repeat(fn, 3, axis=0)
    UVa = np.zeros((len(V), 2)) if UV is None else np.asarray(UV, float).reshape(-1, 2)
    F = np.arange(len(V)).reshape(-1, 3)
    return Mesh(V, N, UVa, F)


def quad(p0, p1, p2, p3, uv=((0, 0), (1, 0), (1, 1), (0, 1))):
    """Quad plat p0..p3 anti-horaire vu de devant."""
    P = np.array([p0, p1, p2, p3], float)
    n = _n(np.cross(P[1] - P[0], P[3] - P[0]) + np.cross(P[2] - P[1], P[0] - P[1]) * 0 + np.cross(P[3] - P[2], P[1] - P[2]) * 0)
    n2 = _n(np.cross(P[2] - P[0], P[3] - P[1]))
    n = n2 if np.linalg.norm(n2) > 0 else n
    return Mesh(P, np.repeat(n[None], 4, 0), np.array(uv, float), [[0, 1, 2], [0, 2, 3]])


def grid_surface(P, UV=None, smooth=True, closed_u=False):
    """P : (nu, nv, 3) grille de points -> surface. Les faces regardent du côté de dP/du × dP/dv."""
    P = np.asarray(P, float)
    nu, nv = P.shape[:2]
    if UV is None:
        uu, vv = np.meshgrid(np.linspace(0, 1, nu), np.linspace(0, 1, nv), indexing="ij")
        UV = np.stack([uu, vv], -1)
    idx = np.arange(nu * nv).reshape(nu, nv)
    if closed_u:
        idx = np.vstack([idx, idx[:1]])
    a = idx[:-1, :-1].ravel(); b = idx[1:, :-1].ravel(); c = idx[1:, 1:].ravel(); d = idx[:-1, 1:].ravel()
    F = np.concatenate([np.stack([a, b, c], 1), np.stack([a, c, d], 1)])
    m = Mesh(P.reshape(-1, 3), np.zeros((nu * nv, 3)), np.asarray(UV, float).reshape(-1, 2), F)
    if smooth:
        m.recompute_normals()
    else:
        m = unweld(m)
    return m.drop_degenerate()


def unweld(m):
    """Duplique les sommets par triangle -> normales plates (UV conservées)."""
    P = m.V[m.F]
    UVp = m.UV[m.F]
    return flat_from_tris(P, UVp)


def box(size, M=None, uv_scale=1.0):
    """Boîte centrée, dimensions (sx, sy, sz), 24 sommets (normales plates), UV en mètres*uv_scale."""
    sx, sy, sz = np.asarray(size, float) / 2
    faces = [
        ((+1, 0, 0), [(sx, -sy, -sz), (sx, sy, -sz), (sx, sy, sz), (sx, -sy, sz)], (1, 2)),
        ((-1, 0, 0), [(-sx, sy, -sz), (-sx, -sy, -sz), (-sx, -sy, sz), (-sx, sy, sz)], (1, 2)),
        ((0, +1, 0), [(sx, sy, -sz), (-sx, sy, -sz), (-sx, sy, sz), (sx, sy, sz)], (0, 2)),
        ((0, -1, 0), [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, -sy, sz), (-sx, -sy, sz)], (0, 2)),
        ((0, 0, +1), [(-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)], (0, 1)),
        ((0, 0, -1), [(-sx, sy, -sz), (sx, sy, -sz), (sx, -sy, -sz), (-sx, -sy, -sz)], (0, 1)),
    ]
    V, N, UV, F = [], [], [], []
    for k, (n, pts, ax) in enumerate(faces):
        for p in pts:
            V.append(p); N.append(n); UV.append((p[ax[0]] * uv_scale, p[ax[1]] * uv_scale))
        F += [[4 * k, 4 * k + 1, 4 * k + 2], [4 * k, 4 * k + 2, 4 * k + 3]]
    m = Mesh(V, N, UV, F)
    return m if M is None else m.transformed(M)


def beam(p0, p1, w, h, up=(0, 0, 1), uv_scale=1.0, caps=True):
    """Poutre rectangulaire de section w (latéral) x h (selon 'up') entre p0 et p1."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    L = np.linalg.norm(d)
    if L < 1e-6:
        return Mesh()
    x = d / L
    up = np.asarray(up, float)
    if abs(np.dot(_n(up), x)) > 0.98:
        up = np.array([1.0, 0, 0]) if abs(x[0]) < 0.9 else np.array([0, 1.0, 0])
    M = frame((p0 + p1) / 2, x, np.cross(up, x))  # Y latéral, Z ~ up
    m = box((L, w, h), M, uv_scale)
    if not caps:
        m = _drop_box_faces(m, (0, 1))
    return m


def _drop_box_faces(m, faces):
    keep = [k for k in range(6) if k not in faces]
    F = np.concatenate([m.F[2 * k:2 * k + 2] for k in keep])
    return Mesh(m.V, m.N, m.UV, F)


def tube(p0, p1, r, sides=8, uv_scale=1.0):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    L = np.linalg.norm(d)
    if L < 1e-6:
        return Mesh()
    x = d / L
    ref = np.array([0, 0, 1.0]) if abs(x[2]) < 0.9 else np.array([1.0, 0, 0])
    a = _n(np.cross(x, ref)); b = np.cross(x, a)
    ang = np.linspace(0, 2 * np.pi, sides + 1)
    ring = np.cos(ang)[:, None] * a + np.sin(ang)[:, None] * b
    P = np.stack([p0 + r * ring, p1 + r * ring], 0)          # (2, sides+1, 3)
    UV = np.stack(np.meshgrid([0, L * uv_scale], ang / (2 * np.pi), indexing="ij"), -1)
    m = grid_surface(P, UV, smooth=False)
    # normales lisses radiales
    m.N = _n(m.V - (p0 + np.clip(((m.V - p0) @ x), 0, L)[:, None] * x))
    return m


def prism(poly2d, z0, z1, uv_scale=1.0, top=True, bottom=True, sides=True):
    """Extrusion verticale d'un polygone (sens anti-horaire) entre z0 et z1."""
    P = np.asarray(poly2d, float)
    out = Mesh()
    n = len(P)
    if sides:
        for i in range(n):
            a, b = P[i], P[(i + 1) % n]
            L = np.linalg.norm(b - a)
            if L < 1e-9:
                continue
            out.add(quad((a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1),
                         uv=((0, z0 * uv_scale), (L * uv_scale, z0 * uv_scale), (L * uv_scale, z1 * uv_scale), (0, z1 * uv_scale))))
    if top or bottom:
        tris = triangulate(P)
        if top:
            V = np.column_stack([P, np.full(n, z1)])
            out.add(Mesh(V, np.tile([0, 0, 1.0], (n, 1)), P * uv_scale, tris))
        if bottom:
            V = np.column_stack([P, np.full(n, z0)])
            out.add(Mesh(V, np.tile([0, 0, -1.0], (n, 1)), P * uv_scale, tris[:, ::-1]))
    return out


def triangulate(poly):
    """Ear clipping pour polygone simple anti-horaire. Retourne (k,3) indices."""
    P = np.asarray(poly, float)
    idx = list(range(len(P)))
    area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    if area < 0:
        idx.reverse()
    tris = []

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    guard = 0
    while len(idx) > 3 and guard < 100000:
        guard += 1
        n = len(idx)
        ear = False
        for k in range(n):
            i0, i1, i2 = idx[(k - 1) % n], idx[k], idx[(k + 1) % n]
            a, b, c = P[i0], P[i1], P[i2]
            if cross(a, b, c) <= 1e-12:
                continue
            ok = True
            for j in idx:
                if j in (i0, i1, i2):
                    continue
                p = P[j]
                if cross(a, b, p) >= 0 and cross(b, c, p) >= 0 and cross(c, a, p) >= 0:
                    ok = False
                    break
            if ok:
                tris.append((i0, i1, i2))
                idx.pop(k)
                ear = True
                break
        if not ear:
            idx.pop(0)
    if len(idx) == 3:
        tris.append(tuple(idx))
    t = np.array(tris, int)
    return t if area >= 0 else t[:, ::-1][:, [0, 1, 2]]


def sweep(profile, path, normals2d, up=(0, 0, 1), closed_profile=False, uv_s=None, uv_t=None, smooth=True):
    """Balaye un profil 2D (offset, z) le long d'une courbe en plan.

    profile : (k,2) -> (décalage horizontal le long de la normale sortante, z absolu ou relatif)
    path    : (n,2) points en plan ; normals2d : (n,2) normales sortantes
    Le profil peut dépendre de la position : passer profile de forme (n,k,2).
    """
    path = np.asarray(path, float)
    nrm = np.asarray(normals2d, float)
    prof = np.asarray(profile, float)
    if prof.ndim == 2:
        prof = np.broadcast_to(prof, (len(path),) + prof.shape)
    xy = path[:, None, :] + prof[..., 0:1] * nrm[:, None, :]
    P = np.concatenate([xy, prof[..., 1:2]], -1)   # (n,k,3)
    if uv_s is None:
        uv_s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))])
    if uv_t is None:
        seg = np.linalg.norm(np.diff(prof, axis=1), axis=-1)
        uv_t = np.concatenate([np.zeros((len(path), 1)), np.cumsum(seg, axis=1)], 1)
    else:
        uv_t = np.broadcast_to(uv_t, (len(path), prof.shape[1]))
    UV = np.stack([np.broadcast_to(np.asarray(uv_s)[:, None], uv_t.shape), uv_t], -1)
    return grid_surface(P, UV, smooth=smooth)


# ------------------------------------------------------------------ scène
class Scene:
    """Regroupe les maillages par (partie, matériau)."""

    def __init__(self):
        self.parts = {}

    def add(self, part, material, mesh):
        if mesh is None or mesh.nv == 0:
            return
        key = (part, material)
        if key not in self.parts:
            self.parts[key] = []
        self.parts[key].append(mesh)

    def merged(self):
        return {k: concat(v) for k, v in self.parts.items()}

    def stats(self):
        rows = []
        for (p, m), lst in sorted(self.parts.items()):
            nv = sum(x.nv for x in lst); nf = sum(x.nf for x in lst)
            rows.append((p, m, nv, nf))
        return rows
