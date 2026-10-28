"""Toiture : surface issue du MNS LiDAR (lissé), raccordée au bord supérieur de la couronne.

Méthode :
 1. MNS ramené au repère local, masqué hors emprise et dans les patios, lissé (σ = 2 m)
    -> supprime les équipements et le bruit, garde l'ondulation réelle (voûte : faîtage 44,9 m,
       rives longues 31,2 m, Sud 26,4 m).
 2. Grille régulière (1,5 m) à l'intérieur de l'emprise (marge 3,5 m), puis « fermeture éclair »
    entre le bord de la grille et la ligne de faîte de couronne (contour décalé de -1,2 m).
 3. Mêmes raccords autour des deux patios des bureaux.
"""
import numpy as np

from . import dims, survey
from .geo2d import signed_dist, point_in_poly, dist_to_poly, smooth_closed
from .mesh import Mesh

EDGE_OFFSET = -1.2       # ligne haute de la couronne / rive du toit
GRID = 3.0
MARGIN = 3.5


class RoofField:
    """MNS lissé et masqué, échantillonnable en (X, Y)."""

    def __init__(self, step=0.5, sigma_m=2.0):
        self.x0, self.y0, self.step = -105.0, -95.0, step
        xs = np.arange(self.x0, 125.0 + 1e-9, step)
        ys = np.arange(self.y0, 95.0 + 1e-9, step)
        X, Y = np.meshgrid(xs, ys, indexing="ij")
        h = survey.dsm(X, Y)
        P = np.stack([X, Y], -1)
        poly = dims.outline(0.0, 1.0)["p"]
        mask = signed_dist(P, poly) < -1.6
        for pa in (dims.PATIO_A, dims.PATIO_B):
            mask &= ~point_in_poly(P, pa) & (dist_to_poly(P, pa) > 1.5)
        h = np.where(mask, h, np.nan)
        self.h = survey.smooth2d(h, sigma_m / step)
        # combler les trous restants (patios, bords) par diffusion simple
        for _ in range(60):
            nan = ~np.isfinite(self.h)
            if not nan.any():
                break
            pad = np.pad(self.h, 1, mode="edge")
            nb = np.stack([pad[:-2, 1:-1], pad[2:, 1:-1], pad[1:-1, :-2], pad[1:-1, 2:]])
            with np.errstate(invalid="ignore"):
                m = np.nanmean(nb, 0)
            self.h[nan] = m[nan]
        self.xs, self.ys = xs, ys

    def __call__(self, X, Y):
        X = np.asarray(X, float); Y = np.asarray(Y, float)
        c = (X - self.x0) / self.step; r = (Y - self.y0) / self.step
        c0 = np.clip(np.floor(c).astype(int), 0, len(self.xs) - 2)
        r0 = np.clip(np.floor(r).astype(int), 0, len(self.ys) - 2)
        fc = np.clip(c - c0, 0, 1); fr = np.clip(r - r0, 0, 1)
        h = self.h
        return ((h[c0, r0] * (1 - fc) + h[c0 + 1, r0] * fc) * (1 - fr)
                + (h[c0, r0 + 1] * (1 - fc) + h[c0 + 1, r0 + 1] * fc) * fr)


_FIELD = None

# Creux du toit entre le patio B et la façade Nord (terrasse basse à ≈31,5 m dans le relevé) :
# il creusait le haut de la façade Nord en « V » près de l'angle Nord-Est. On le comble pour un
# couronnement plat (choix de l'utilisateur, 27/10/2026).
NE_FILL = (90.0, 112.0, -68.0, -34.0)   # x0, x1, y0, y1


def _fill_ne_notch(f):
    x0, x1, y0, y1 = NE_FILL
    ci = np.nonzero((f.xs >= x0) & (f.xs <= x1))[0]
    rj = np.nonzero((f.ys >= y0) & (f.ys <= y1))[0]
    ja, jb = rj[0], rj[-1]
    w = (f.ys[rj] - f.ys[ja]) / (f.ys[jb] - f.ys[ja])
    for i in ci:
        plane = f.h[i, ja] * (1 - w) + f.h[i, jb] * w
        f.h[i, rj] = np.maximum(f.h[i, rj], plane)


def field():
    """Champ de hauteur mis en cache dans build/roof_field.npz (recalculé si absent)."""
    global _FIELD
    if _FIELD is None:
        import os
        cache = os.path.join(survey.ROOT, "build", "roof_field.npz")
        if os.path.exists(cache):
            d = np.load(cache)
            f = RoofField.__new__(RoofField)
            f.x0, f.y0, f.step = float(d["x0"]), float(d["y0"]), float(d["step"])
            f.h, f.xs, f.ys = d["h"], d["xs"], d["ys"]
            _FIELD = f
        else:
            _FIELD = RoofField()
            np.savez_compressed(cache, x0=_FIELD.x0, y0=_FIELD.y0, step=_FIELD.step,
                                h=_FIELD.h, xs=_FIELD.xs, ys=_FIELD.ys)
        _fill_ne_notch(_FIELD)     # appliqué après le cache (le cache reste le relevé brut lissé)
    return _FIELD


def edge_loop(ds=1.0):
    """Ligne haute de couronne : points, normales, hauteur H (LiDAR à 2,5 m en retrait, lissée)."""
    L = dims.outline(EDGE_OFFSET, ds)
    f = field()
    inner = L["p"] - L["n"] * 2.0
    H = f(inner[:, 0], inner[:, 1])
    H = smooth_closed(H, max(1, int(4.0 / ds)))   # lissage léger : garde la montée vers les angles
    L["H"] = np.maximum(H, 24.0)
    return L


def _clean_mask(K):
    """Supprime les connexions en diagonale seule (sommets pincés)."""
    K = K.copy()
    for _ in range(50):
        a = K[:-1, :-1]; b = K[1:, :-1]; c = K[:-1, 1:]; d = K[1:, 1:]
        p1 = a & d & ~b & ~c
        p2 = b & c & ~a & ~d
        if not (p1.any() or p2.any()):
            break
        K[:-1, :-1][p1] = False
        K[1:, :-1][p2] = False
    return K


def _boundary_loops(K):
    """Boucles de bord d'un masque de cellules (intérieur à gauche). Retourne listes de (i,j)."""
    ni, nj = K.shape
    nxt = {}

    def k(i, j):
        return 0 <= i < ni and 0 <= j < nj and K[i, j]

    for i in range(ni + 1):
        for j in range(nj + 1):
            # arête +X de (i,j) à (i+1,j) : gauche = cellule (i,j), droite = (i,j-1)
            if i < ni:
                if k(i, j) and not k(i, j - 1):
                    nxt[(i, j)] = (i + 1, j)
                elif k(i, j - 1) and not k(i, j):
                    nxt[(i + 1, j)] = (i, j)
            # arête +Y de (i,j) à (i,j+1) : gauche = cellule (i-1,j), droite = (i,j)
            if j < nj:
                if k(i - 1, j) and not k(i, j):
                    nxt[(i, j)] = (i, j + 1)
                elif k(i, j) and not k(i - 1, j):
                    nxt[(i, j + 1)] = (i, j)
    loops, seen = [], set()
    for start in list(nxt.keys()):
        if start in seen:
            continue
        loop, cur = [], start
        while cur not in seen:
            seen.add(cur)
            loop.append(cur)
            cur = nxt[cur]
        loops.append(loop)
    return loops


def _stitch(A, B):
    """A, B : (n,3) boucles fermées de même orientation. Triangulation en bande (indices locaux)."""
    nA, nB = len(A), len(B)
    j0 = int(np.argmin(np.linalg.norm(B[:, :2] - A[0, :2], axis=1)))
    B_idx = (np.arange(nB) + j0) % nB
    tris = []
    i = j = 0
    while i < nA or j < nB:
        a0, a1 = i % nA, (i + 1) % nA
        b0, b1 = B_idx[j % nB], B_idx[(j + 1) % nB]
        if i >= nA:
            adv_a = False
        elif j >= nB:
            adv_a = True
        else:
            adv_a = np.linalg.norm(A[a1, :2] - B[b0, :2]) <= np.linalg.norm(A[a0, :2] - B[b1, :2])
        if adv_a:
            tris.append(("A", a0, "A", a1, "B", b0)); i += 1
        else:
            tris.append(("A", a0, "B", b1, "B", b0)); j += 1
    return tris


def build(ds_edge=2.0):
    f = field()
    L = edge_loop(ds_edge)
    poly = dims.outline(0.0, 1.0)["p"]
    xs = np.arange(-96, 118 + 1e-9, GRID)
    ys = np.arange(-84, 84 + 1e-9, GRID)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    P = np.stack([X, Y], -1)
    ok = signed_dist(P, poly) < -(MARGIN - EDGE_OFFSET)
    for pa in (dims.PATIO_A, dims.PATIO_B):
        ok &= ~point_in_poly(P, pa) & (dist_to_poly(P, pa) > 2.0)
    K = ok[:-1, :-1] & ok[1:, :-1] & ok[:-1, 1:] & ok[1:, 1:]
    K = _clean_mask(K)
    Z = f(X, Y)

    V = [np.stack([X.ravel(), Y.ravel(), Z.ravel()], -1)]
    nid = lambda i, j: i * len(ys) + j
    F = []
    ii, jj = np.nonzero(K)
    for i, j in zip(ii, jj):
        a, b, c, d = nid(i, j), nid(i + 1, j), nid(i + 1, j + 1), nid(i, j + 1)
        F += [(a, b, c), (a, c, d)]
    base = len(V[0])

    loops = _boundary_loops(K)
    loops.sort(key=len, reverse=True)
    Vall = V[0]
    extra = []
    # boucle extérieure <-> ligne de couronne (inversée pour être anti-horaire)
    Lp = L["p"][::-1]
    LH = L["H"][::-1]
    Bpts = np.column_stack([Lp, LH])
    targets = [Bpts]
    hole_polys = []
    for pa, fl in ((dims.PATIO_A, None), (dims.PATIO_B, None)):
        q = np.asarray(pa, float)
        # densifie le polygone (sens horaire = orientation des trous)
        dense = []
        for k in range(len(q)):
            a, b = q[k], q[(k + 1) % len(q)]
            n = max(1, int(np.ceil(np.linalg.norm(b - a) / 1.5)))
            dense += [a + (b - a) * t / n for t in range(n)]
        dense = np.array(dense)
        hole_polys.append(dense)
    off = base
    loop_meta = []
    for lp in loops:
        A_idx = np.array([nid(i, j) for i, j in lp])
        A = Vall[A_idx]
        cen = A[:, :2].mean(0)
        if lp is loops[0]:
            Bp = Bpts
        else:
            # trou : choisir le patio le plus proche
            k = int(np.argmin([np.linalg.norm(hp.mean(0) - cen) for hp in hole_polys]))
            hp = hole_polys[k]
            out = hp + 0.0
            Bp = np.column_stack([out, f(out[:, 0], out[:, 1])])
            loop_meta.append((k, Bp))
        B_idx = np.arange(len(Bp)) + off
        extra.append(Bp)
        off += len(Bp)
        for t in _stitch(A, Bp):
            idx = []
            for which, n in zip(t[0::2], t[1::2]):
                idx.append(A_idx[n] if which == "A" else B_idx[n])
            F.append(tuple(idx))
    Vfin = np.vstack([Vall] + extra)
    F = np.array(F, int)
    # orientation : normales vers le haut
    a, b, c = Vfin[F[:, 0]], Vfin[F[:, 1]], Vfin[F[:, 2]]
    nz = np.cross(b - a, c - a)[:, 2]
    F[nz < 0] = F[nz < 0][:, ::-1]
    used = np.unique(F)
    remap = np.full(len(Vfin), -1); remap[used] = np.arange(len(used))
    Vu = Vfin[used]
    m = Mesh(Vu, np.zeros_like(Vu), np.column_stack([Vu[:, 0] / 8.0, Vu[:, 1] / 8.0]), remap[F])
    m.recompute_normals().drop_degenerate(1e-6)
    return m, L, loop_meta
