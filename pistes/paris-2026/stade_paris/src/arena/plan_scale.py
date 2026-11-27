"""Agrandissement de l'arène EN PLAN (X, Y × K, hauteurs inchangées) pour faire tenir le tracé Paris 2026.

Ordre (build.py) :
  1. coque construite à la taille réelle (toit, couronne, façade, bureaux, intérieur) ;
  2. scale_scene : X, Y × K (normales recalculées) ; les écrans et enseignes s'élargissent aussi, mais leurs
     visuels ont été dessinés au ratio final (branding.PLAN_K) : les logos ne sont jamais déformés ;
  3. scale_dims + champ de toiture agrandi : les tribunes sont ensuite construites directement à la nouvelle
     taille (rangs, marches et sièges au pas réel, il y a juste plus de sièges).
K = 1 : arène réelle, aucun changement.
"""
import numpy as np

from . import dims, roof


def _k(K):
    """K = facteur unique, ou (KX, KY, DY[, DX]) : X x KX puis X + DX (m), Y x KY puis Y + DY (m).
    v37 Paris (« tout le stade doit bouger pour garder la forme ; tribunes à 3-4 m de la piste sur les 2 côtés ») : le stade
    garde x1,55 dans le sens de la piste (X) et se resserre en travers (Y), décalé de DY pour être centré sur la piste.
    v39 Paris (« le côté ouest à la même distance de la piste que le nord et le sud ») : en X, facteur KX et décalage DX choisis pour
    que le mur de scène (Nord de l'arène, paddock) reste à sa place et que le front de tribune Sud (Ouest dans le jeu) se rapproche."""
    if np.isscalar(K):
        return float(K), float(K), 0.0, 0.0
    K = [float(v) for v in K] + [0.0] * (4 - len(K))
    return K[0], K[1], K[2], K[3]


def scale_scene(scene, K):
    KX, KY, DY, DX = _k(K)
    if (KX, KY, DY, DX) == (1.0, 1.0, 0.0, 0.0):
        return
    M = np.diag([KX, KY, 1.0, 1.0]); M[1, 3] = DY; M[0, 3] = DX
    for (part, mat), lst in scene.parts.items():
        scene.parts[(part, mat)] = [m.transformed(M) for m in lst]


class _ScaledField:
    def __init__(self, f, K):
        self.f, (self.KX, self.KY, self.DY, self.DX) = f, _k(K)

    def __call__(self, X, Y):
        return self.f((np.asarray(X, float) - self.DX) / self.KX, (np.asarray(Y, float) - self.DY) / self.KY)


def _wrap(fn, KX, KY, DY, DX=0.0, key=None):
    """contour construit à la taille réelle puis passé dans le plan agrandi (mêmes arrondis que la coque transformée)."""
    def g(*a, **k):
        cur = {n: getattr(dims, n) for n in _REAL}             # les fonctions d'origine lisent les cotes réelles
        for n, v in _REAL.items():
            setattr(dims, n, v)
        try:
            r = fn(*a, **k)
        finally:
            for n, v in cur.items():
                setattr(dims, n, v)
        T = lambda P: np.column_stack([np.asarray(P)[:, 0] * KX + DX, np.asarray(P)[:, 1] * KY + DY])
        if isinstance(r, dict):
            r = dict(r); r["p"] = T(r["p"])
            if "t" in r:
                t2 = np.column_stack([r["t"][:, 0] * KX, r["t"][:, 1] * KY]); r["t"] = t2 / np.linalg.norm(t2, axis=1, keepdims=True)
            if "n" in r:                                     # normale : inverse transposée
                n2 = np.column_stack([r["n"][:, 0] / KX, r["n"][:, 1] / KY]); r["n"] = n2 / np.linalg.norm(n2, axis=1, keepdims=True)
            if "s" in r:
                r["s"] = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(r["p"], axis=0), axis=1))])
            return r
        if isinstance(r, tuple):
            p, t, n, s = r; p2 = T(p); t2 = np.column_stack([t[:, 0] * KX, t[:, 1] * KY]); t2 /= np.linalg.norm(t2, axis=1, keepdims=True)
            n2 = np.stack([-t2[:, 1], t2[:, 0]], -1); s2 = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(p2, axis=0), axis=1))])
            return p2, t2, n2, s2
        return T(r)
    g._plan = (KX, KY, DY, DX)
    return g


_XN = ("X_SOUTH", "X_CORNER", "X_STAGE", "X_RIBBON_END", "X_OFFICE_N", "NORTH_X0", "FLOOR_X_SOUTH")
_YN = ("HALF_W", "Y_CORNER", "FLOOR_HALF_W")
_RN = ("R_CORNER", "FLOOR_R")
_REAL = {}


def scale_dims(K):
    """Met à l'échelle les cotes en plan utilisées après l'étape 2 (tribunes, sol, terrain MX)."""
    KX, KY, DY, DX = _k(K)
    if (KX, KY, DY, DX) == (1.0, 1.0, 0.0, 0.0):
        return
    if KX == KY and DY == 0.0 and DX == 0.0:
        _scale_dims_uniform(KX)
        return
    # anisotrope : les contours (outline, floor_outline, envelope) sont calculés à la taille réelle puis transformés comme la coque ;
    # les cotes en X (le long de la piste) suivent KX (+ DX : ce sont des positions), celles en travers KY (les rayons ne servent plus
    # qu'à la taille réelle)
    for fn in ("outline", "floor_outline", "envelope"):
        f0 = getattr(dims, fn)
        setattr(dims, fn, _wrap(getattr(f0, "__wrapped_real__", f0), KX, KY, DY, DX))
        getattr(dims, fn).__wrapped_real__ = getattr(f0, "__wrapped_real__", f0)
    # cotes scalaires (lues ailleurs, ex. habillage : mur de scène) : en X x KX + DX, en travers x KY
    if not _REAL:                                             # 1er appel : cotes réelles (appel suivant : même résultat)
        _REAL.update({n: getattr(dims, n) for n in _XN + _YN + _RN + ("OUTLINE", "OUTLINE_R", "PATIO_A", "PATIO_B")})
    for n in _XN:
        setattr(dims, n, _REAL[n] * KX + DX)
    for n in _YN:
        setattr(dims, n, _REAL[n] * KY)
    for n in _RN:
        setattr(dims, n, _REAL[n] * KY)
    dims.PLAN_SCALE = tuple(K) if not np.isscalar(K) else K
    roof._FIELD = _ScaledField(roof.field(), K)


def _scale_dims_uniform(K):
    for name in ("HALF_W", "X_SOUTH", "R_CORNER", "X_CORNER", "Y_CORNER", "X_STAGE", "X_RIBBON_END",
                 "X_OFFICE_N", "NORTH_X0", "FLOOR_HALF_W", "FLOOR_X_SOUTH", "FLOOR_R"):
        setattr(dims, name, getattr(dims, name) * K)
    dims.OUTLINE = [(x * K, y * K) for x, y in dims.OUTLINE]
    dims.OUTLINE_R = [r * K for r in dims.OUTLINE_R]
    dims.PATIO_A = [(x * K, y * K) for x, y in dims.PATIO_A]
    dims.PATIO_B = [(x * K, y * K) for x, y in dims.PATIO_B]
    dims.PLAN_SCALE = K
    roof._FIELD = _ScaledField(roof.field(), K)
