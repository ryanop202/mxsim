"""Bloc de bureaux Nord (≈31 000 m², 9 niveaux) et façade rue des Sorins.

Source principale : élévation ACDP « Façade rue des Sorins » (oct. 2015), niveaux NGF :
  sol 54,00 ; sous-face du porte-à-faux 63,00 (colonnade 9 m) ; volume vitré 63,00–72,24 ;
  bandeau 72,24–74,30 ; étages de bureaux N5–N9 (pas 3,52 m) ; toiture aluminium au-dessus.
Côtés Est/Ouest au-delà du ruban d'écailles : bureaux sous la couronne (fenêtres en bandeau).
"""
import numpy as np

from . import dims
from .facade import Ref, _band, _surf
from .mesh import box, quad, Mesh, grid_surface, prism
from .roof import field

Z_COLONNADE = 9.0       # [DOC] 63,00 - 54,00
Z_GLAZED_TOP = 18.24    # [DOC] 72,24
Z_BAND_N = 20.30        # [DOC] 74,30
FLOOR_H = 3.52          # [DOC]
Z_N1 = 5.76             # [DOC] 59,76 (lecture possible 58,76)


def office_refs(ds=0.5):
    """Deux courbes : 'sides' (bureaux sous couronne, hors arête 3) et 'north' (arête 3)."""
    o = dims.outline(0.0, ds)
    e, p = o["edge"], o["p"]
    n = len(p)
    in_off = ((e == 0) | (e == 2)) & (p[:, 0] > dims.X_RIBBON_END)
    in_off |= (e == -1) | (e == -4) | (e == 3)
    # séquence contiguë : rouler pour démarrer au premier point de l'arête 2 au-delà du ruban
    idx = np.nonzero(in_off)[0]
    start = idx[np.argmax((e[idx] == 2) & (p[idx, 0] > dims.X_RIBBON_END))]
    order = [(start + k) % n for k in range(n)]
    order = [i for i in order if in_off[i]]
    pp, nn, ee = p[order], o["n"][order], e[order]
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pp, axis=0), axis=1))])
    ref = Ref(pp, nn, s, {"edge": ee.astype(float)})
    on_north = ee == 3
    s_n0, s_n1 = s[on_north].min(), s[on_north].max()
    return ref, (s_n0, s_n1)


def build(L, scene):
    ref, (sn0, sn1) = office_refs()
    S = ref.length
    # ---------------- côtés (et congés) : rez-de-chaussée vitré + bureaux jusqu'au bas de couronne
    for a, b in ((0.0, sn0), (sn1, S)):
        if b - a < 0.5:
            continue
        P, UV = _band(ref, a, b, dims.OFF_PLINTH, dims.OFF_PLINTH, 0.0, dims.Z_PLINTH_TOP, 0.5)
        scene.add("office", "curtain_wall", _surf(P, UV, flip=True, uscale=1 / 6.0, vscale=1 / dims.Z_PLINTH_TOP))
        for (o0, o1, z0, z1, fl) in ((dims.OFF_PLINTH + 1.45, dims.OFF_PLINTH + 1.45, dims.Z_PLINTH_TOP, dims.Z_BAND_TOP, True),
                                     (dims.OFF_PLINTH, dims.OFF_PLINTH + 1.45, dims.Z_BAND_TOP, dims.Z_BAND_TOP, False),
                                     (dims.OFF_PLINTH, dims.OFF_PLINTH + 1.45, dims.Z_PLINTH_TOP, dims.Z_PLINTH_TOP, True)):
            P, UV = _band(ref, a, b, o0, o1, z0, z1, 0.5)
            scene.add("office", "alu_white", _surf(P, UV, flip=fl, uscale=.5, vscale=.5))
        P, UV = _band(ref, a, b, -2.6, -2.6, dims.Z_BAND_TOP, dims.Z_SCALES_TOP + 0.05, 0.5)
        UV[..., 1] = (UV[..., 1] - Z_N1) / FLOOR_H * FLOOR_H
        scene.add("office", "office", _surf(P, UV, flip=True, uscale=1 / 7.0, vscale=1 / FLOOR_H))
        # sous-face de couronne au-dessus des bureaux
        P, UV = _band(ref, a, b, -2.6, dims.OFF_INNER_SKIN + 0.05, dims.Z_SCALES_TOP + 0.05, dims.Z_SCALES_TOP + 0.15, 0.5)
        scene.add("office", "alu_white", _surf(P, UV, flip=False, uscale=.5, vscale=.5))

    # ---------------- façade Nord
    H = np.interp(np.linspace(sn0, sn1, 200), *_edge3_heights(L, ref))
    ss = np.linspace(sn0, sn1, 200)
    # colonnade : vitrage en retrait + sous-face + poteaux
    P, UV = _band(ref, sn0, sn1, -6.0, -6.0, 0.0, Z_COLONNADE, 0.5)
    scene.add("office_north", "curtain_wall", _surf(P, UV, flip=True, uscale=1 / 6.0, vscale=2 / Z_COLONNADE))
    P, UV = _band(ref, sn0, sn1, -6.0, -0.6, Z_COLONNADE, Z_COLONNADE, 0.5)
    scene.add("office_north", "alu_white", _surf(P, UV, flip=True, uscale=.5, vscale=.5))
    ncol = int((sn1 - sn0) / 7.5)
    for k in range(ncol + 1):
        s = sn0 + 1.0 + (sn1 - sn0 - 2.0) * k / ncol
        p, nrm = ref.at(s, -1.4)
        t = np.array([nrm[1], -nrm[0]])
        from .mesh import frame
        M = frame((p[0], p[1], Z_COLONNADE / 2), (t[0], t[1], 0), (nrm[0], nrm[1], 0))
        scene.add("office_north", "concrete_white", box((0.9, 0.9, Z_COLONNADE), M, 0.5))
    # nez du porte-à-faux
    P, UV = _band(ref, sn0, sn1, -0.6, -0.6, Z_COLONNADE - 0.6, Z_COLONNADE, 0.5)
    scene.add("office_north", "alu_white", _surf(P, UV, flip=True, uscale=.5, vscale=.5))
    # volume vitré 9,0–18,24 : mur-rideau + ailettes verticales
    P, UV = _band(ref, sn0, sn1, -0.6, -0.6, Z_COLONNADE, Z_GLAZED_TOP, 0.5)
    scene.add("office_north", "curtain_wall", _surf(P, UV, flip=True, uscale=1 / 6.0, vscale=1 / (Z_GLAZED_TOP - Z_COLONNADE)))
    nf = int((sn1 - sn0) / 1.5)
    for k in range(1, nf):
        s = sn0 + (sn1 - sn0) * k / nf
        p, nrm = ref.at(s, -0.3)
        t = np.array([nrm[1], -nrm[0]])
        from .mesh import frame
        M = frame((p[0], p[1], (Z_COLONNADE + Z_GLAZED_TOP) / 2), (t[0], t[1], 0), (nrm[0], nrm[1], 0))
        scene.add("office_north", "alu_white", box((0.08, 0.6, Z_GLAZED_TOP - Z_COLONNADE), M, 0.5))
    # bandeau blanc
    P, UV = _band(ref, sn0, sn1, -0.4, -0.4, Z_GLAZED_TOP, Z_BAND_N, 0.5)
    scene.add("office_north", "concrete_white", _surf(P, UV, flip=True, uscale=.25, vscale=.25))
    P, UV = _band(ref, sn0, sn1, -0.6, -0.4, Z_GLAZED_TOP, Z_GLAZED_TOP, 0.5)
    scene.add("office_north", "alu_white", _surf(P, UV, flip=True))
    # étages N5-N9 jusqu'à la rive de toiture (hauteur variable, LiDAR)
    n = len(ss)
    pa, _ = ref.at(ss, -1.2)
    zt = np.maximum(H, Z_BAND_N + 2.0)
    P = np.stack([np.column_stack([pa, np.full(n, Z_BAND_N)]), np.column_stack([pa, zt])], 1)
    UV = np.stack([np.stack([ss / 7.0, np.full(n, (Z_BAND_N - Z_N1) / FLOOR_H)], -1),
                   np.stack([ss / 7.0, (zt - Z_N1) / FLOOR_H], -1)], 1)
    scene.add("office_north", "office", grid_surface(P[:, ::-1], UV[:, ::-1]))
    # retour bandeau -> nu des étages
    P, UV = _band(ref, sn0, sn1, -1.2, -0.4, Z_BAND_N, Z_BAND_N, 0.5)
    scene.add("office_north", "concrete_white", _surf(P, UV, flip=False, uscale=.25, vscale=.25))

    # ---------------- fermetures aux extrémités du ruban (X = 64) : retour de la peau intérieure
    from .facade import ribbon_ref
    rr = ribbon_ref()
    for s_end in (0.0, rr.length):
        pa, nrm = rr.at(s_end, dims.OFF_INNER_SKIN)
        pb, _ = rr.at(s_end, -2.6)
        q = quad((*pa, dims.Z_BAND_TOP), (*pb, dims.Z_BAND_TOP), (*pb, dims.Z_SCALES_TOP + 0.2), (*pa, dims.Z_SCALES_TOP + 0.2),
                 uv=((0, 0), (0.6, 0), (0.6, 4), (0, 4)))
        scene.add("office", "concrete_white", q.double_sided())

    # ---------------- patios
    f = field()
    for poly, zf in ((dims.PATIO_A, dims.PATIO_A_FLOOR), (dims.PATIO_B, dims.PATIO_B_FLOOR)):
        q = np.asarray(poly, float)
        m = len(q)
        for k in range(m):
            a, b = q[k], q[(k + 1) % m]
            nseg = max(1, int(np.ceil(np.linalg.norm(b - a) / 1.5)))
            pts = np.array([a + (b - a) * t / nseg for t in range(nseg + 1)])
            zt = f(pts[:, 0], pts[:, 1])
            sl = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
            P = np.stack([np.column_stack([pts, np.full(len(pts), zf)]), np.column_stack([pts, zt])], 1)
            UV = np.stack([np.stack([sl / 7.0, np.full(len(pts), (zf - Z_N1) / FLOOR_H)], -1),
                           np.stack([sl / 7.0, (zt - Z_N1) / FLOOR_H], -1)], 1)
            # polygone horaire : l'intérieur du patio est à droite -> faces vers l'intérieur du patio
            scene.add("office", "office", grid_surface(P, UV))
        if zf > 0.1:
            scene.add("office", "concrete_grey", prism(q[::-1], zf - 0.3, zf, uv_scale=0.25, sides=False, bottom=False))
    return ref


def _edge3_heights(L, ref):
    """Hauteur de rive (loop L) projetée sur l'abscisse de la courbe 'north'."""
    sel = L["edge"] == 3
    p = L["p"][sel] + L["n"][sel] * 1.2
    # abscisse s la plus proche sur ref
    d = np.linalg.norm(ref.p[None, :, :] - p[:, None, :], axis=-1)
    s = ref.s[np.argmin(d, axis=1)]
    order = np.argsort(s)
    return s[order], L["H"][sel][order]
