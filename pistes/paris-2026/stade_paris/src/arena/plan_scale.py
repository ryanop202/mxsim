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

def scale_scene(scene, K):
    if K == 1:
        return
    M = np.diag([K, K, 1.0, 1.0])
    for (part, mat), lst in scene.parts.items():
        scene.parts[(part, mat)] = [m.transformed(M) for m in lst]


class _ScaledField:
    def __init__(self, f, K):
        self.f, self.K = f, K

    def __call__(self, X, Y):
        return self.f(np.asarray(X, float) / self.K, np.asarray(Y, float) / self.K)


def scale_dims(K):
    """Met à l'échelle les cotes en plan utilisées après l'étape 2 (tribunes, sol, terrain MX)."""
    if K == 1:
        return
    for name in ("HALF_W", "X_SOUTH", "R_CORNER", "X_CORNER", "Y_CORNER", "X_STAGE", "X_RIBBON_END",
                 "X_OFFICE_N", "NORTH_X0", "FLOOR_HALF_W", "FLOOR_X_SOUTH", "FLOOR_R"):
        setattr(dims, name, getattr(dims, name) * K)
    dims.OUTLINE = [(x * K, y * K) for x, y in dims.OUTLINE]
    dims.OUTLINE_R = [r * K for r in dims.OUTLINE_R]
    dims.PATIO_A = [(x * K, y * K) for x, y in dims.PATIO_A]
    dims.PATIO_B = [(x * K, y * K) for x, y in dims.PATIO_B]
    dims.PLAN_SCALE = K
    roof._FIELD = _ScaledField(roof.field(), K)
