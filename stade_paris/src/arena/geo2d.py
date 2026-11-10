"""Géométrie plane : polygones convexes à angles arrondis, distances, appartenance."""
import numpy as np


def _n2(v):
    l = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.where(l < 1e-12, 1, l)


def rounded_polygon(corners, radii, offset=0.0, ds=1.0, start_edge=0):
    """Contour d'un polygone convexe (sommets dans le sens horaire vu de dessus) à angles arrondis,
    décalé de 'offset' (positif = vers l'extérieur).

    Retourne dict : p (n,2), t tangentes, n normales sortantes, s abscisse curviligne,
    edge (indice de l'arête d'origine, -1-k pour l'arc du sommet k).
    Le parcours commence au début de l'arête 'start_edge' et est fermé (dernier point != premier).
    """
    C = np.asarray(corners, float)
    m = len(C)
    pts, eid = [], []
    # arête k : de C[k] à C[k+1]
    for kk in range(m):
        k = (start_edge + kk) % m
        a, b = C[k], C[(k + 1) % m]
        t = _n2(b - a)
        nout = np.array([-t[1], t[0]])           # sens horaire -> extérieur à gauche
        ra, rb = radii[k], radii[(k + 1) % m]
        # points tangents des arcs (sur le polygone d'origine) : recul de r*tan(theta/2)
        def setback(i, r):
            p, q0, q1 = C[i], C[(i - 1) % m], C[(i + 1) % m]
            u0, u1 = _n2(q0 - p), _n2(q1 - p)
            ang = np.arccos(np.clip(np.dot(u0, u1), -1, 1))
            return r / np.tan(ang / 2)
        pa = a + t * setback(k, ra) + nout * offset
        pb = b - t * setback((k + 1) % m, rb) + nout * offset
        L = np.linalg.norm(pb - pa)
        nseg = max(1, int(np.ceil(L / ds)))
        for i in range(nseg):
            pts.append(pa + (pb - pa) * i / nseg)
            eid.append(k)
        # arc au sommet k+1
        j = (k + 1) % m
        r = rb + offset
        t2 = _n2(C[(j + 1) % m] - C[j])
        n1 = nout
        n2 = np.array([-t2[1], t2[0]])
        center = pb - n1 * r
        a0 = np.arctan2(n1[1], n1[0]); a1 = np.arctan2(n2[1], n2[0])
        da = (a1 - a0 + np.pi) % (2 * np.pi) - np.pi  # sens horaire -> négatif
        narc = max(1, int(np.ceil(abs(da) * max(r, 1e-3) / ds))) if r > 1e-6 else 1
        for i in range(narc):
            ang = a0 + da * i / narc
            pts.append(center + r * np.array([np.cos(ang), np.sin(ang)]) if r > 1e-6 else pb)
            eid.append(-1 - j)
    p = np.array(pts)
    tng = _n2(np.roll(p, -1, 0) - np.roll(p, 1, 0))
    nrm = np.stack([-tng[:, 1], tng[:, 0]], -1)
    seg = np.linalg.norm(np.roll(p, -1, 0) - p, axis=1)
    s = np.concatenate([[0], np.cumsum(seg[:-1])])
    return dict(p=p, t=tng, n=nrm, s=s, edge=np.array(eid), length=seg.sum())


def point_in_poly(P, poly):
    """Even-odd, vectorisé. P (...,2)."""
    P = np.asarray(P, float)
    x, y = P[..., 0], P[..., 1]
    inside = np.zeros(x.shape, bool)
    q = np.asarray(poly, float)
    for i in range(len(q)):
        x0, y0 = q[i]; x1, y1 = q[(i + 1) % len(q)]
        cond = ((y0 > y) != (y1 > y))
        with np.errstate(divide="ignore", invalid="ignore"):
            xi = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
        inside ^= cond & (x < xi)
    return inside


def dist_to_poly(P, poly):
    P = np.asarray(P, float)
    q = np.asarray(poly, float)
    d = np.full(P.shape[:-1], np.inf)
    for i in range(len(q)):
        a = q[i]; b = q[(i + 1) % len(q)]
        ab = b - a
        t = np.clip(((P - a) @ ab) / max(1e-12, ab @ ab), 0, 1)
        proj = a + t[..., None] * ab
        d = np.minimum(d, np.linalg.norm(P - proj, axis=-1))
    return d


def signed_dist(P, poly):
    """Négatif à l'intérieur."""
    d = dist_to_poly(P, poly)
    return np.where(point_in_poly(P, poly), -d, d)


def resample_closed(p, ds):
    p = np.asarray(p, float)
    q = np.vstack([p, p[:1]])
    seg = np.linalg.norm(np.diff(q, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    n = max(3, int(np.round(s[-1] / ds)))
    st = np.linspace(0, s[-1], n, endpoint=False)
    return np.stack([np.interp(st, s, q[:, 0]), np.interp(st, s, q[:, 1])], -1)


def smooth_closed(a, win):
    """Moyenne glissante circulaire (win échantillons)."""
    if win <= 1:
        return a
    k = np.ones(win) / win
    pad = np.concatenate([a[-win:], a, a[:win]])
    return np.convolve(pad, k, mode="same")[win:-win]
