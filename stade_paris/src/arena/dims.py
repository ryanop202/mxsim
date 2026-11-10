"""Paramètres architecturaux (mètres, repère local, voir survey.py).

Chaque valeur est suivie de sa source :
  [DOC]  publiée (élévation d'architecte, IGN, fiche technique)
  [LID]  mesurée sur le relevé LiDAR IGN HD
  [PHO]  estimée sur les photographies de l'utilisateur
  [HYP]  hypothèse de cohérence géométrique (documentée)
"""
import numpy as np

# ---------------------------------------------------------------- plan
HALF_W = 82.5         # [LID] demi-largeur au nu de la couronne (rives à v=+79,5 / -85,5)
X_SOUTH = -92.0       # [LID] nu de la couronne, milieu de l'extrémité Sud
R_CORNER = 32.0       # [LID] rayon des angles Sud (ajusté : bord à u=-85 pour |v|=70)
X_CORNER = X_SOUTH + R_CORNER          # -60 : centre des arcs
Y_CORNER = HALF_W - R_CORNER           # 50.5
X_STAGE = 62.0        # [LID]/[PHO] nu intérieur du mur de scène (rupture du toit à u≈62-65)
X_RIBBON_END = 64.0   # [PHO]/[LID] fin du ruban d'écailles sur les façades longues
X_OFFICE_N = 112.0    # [LID]/[DOC] façade Nord des bureaux (rue des Sorins)

# ---------------------------------------------------------------- hauteurs façade
Z_PLINTH_TOP = 3.21   # [DOC] haut du socle vitré (57,21 NGF - 54,00)
Z_BAND_TOP = 4.05     # [PHO] haut du bandeau blanc de signalétique
Z_SCALES_TOP = 19.46  # [DOC] haut des écailles = bas de couronne (73,46 NGF)
SCALE_ROWS = (        # [DOC] 3 rangs sur 16,25 m ; [PHO] rang haut plus grand
    (3.95, 9.15),     # rang bas    5,2 m
    (8.70, 14.10),    # rang milieu 5,4 m (chevauchement 0,45 m)
    (13.60, 19.70),   # rang haut   6,1 m (passe derrière la sous-face de couronne)
)
SCALE_PITCH = 2.30    # [DOC] 592 écailles / 3 rangs sur ~446 m de ruban -> ~2,3 m
SCALE_CHORD = 2.75    # [PHO] corde d'une écaille (recouvrement latéral visible P1-P3)
SCALE_YAW = np.radians(34.0)   # [PHO] rotation de l'écaille par rapport au plan de façade
SCALE_SAG = 0.22      # [PHO] flèche de la courbure (portion de cylindre)

# entrées (centre en X sur la façade, largeur auvent) [PHO] P1-P4, P6
ENTRANCES = {
    "west": dict(side=+1, x=15.0, canopy_w=31.0, canopy_d=6.5, z0=5.2, z1=9.3,
                 screen_w=13.8, screen_h=9.0, screen_z=4.2, glass_w=26.0, sign=True),
    "east": dict(side=-1, x=36.0, canopy_w=18.0, canopy_d=5.0, z0=5.2, z1=8.8,
                 screen_w=13.0, screen_h=9.0, screen_z=4.2, glass_w=14.0, sign=False),
}
LEDGE = dict(z=8.92, t=0.42, off_out=-1.75, x_west=-35.0, y_end=0.0)   # [PHO] P2, P3
LEDGE_Z = 8.95        # [PHO] débord horizontal entre rang bas et rang milieu (angle SO)

# offsets en plan (négatif = vers l'intérieur) par rapport au nu de couronne
OFF_CROWN_BOTTOM = -2.60   # [PHO P2/P3] bas de couronne très en retrait : lèvre bombée en porte-à-faux
OFF_SCALES = -2.90         # [PHO P2/P3] écailles en retrait sous la lèvre de couronne
OFF_INNER_SKIN = -4.20     # [DOC] peau intérieure vitrée (double peau)
OFF_PLINTH = -3.60         # [PHO] nu du socle vitré

# hauteur du haut de couronne (bord du toit) le long du périmètre  [LID]
CROWN_TOP_LONG = 31.2      # façades longues
CROWN_TOP_SOUTH = 26.4     # milieu de l'extrémité Sud
CROWN_TOP_CORNER = 29.6    # dans les arcs d'angle

# ---------------------------------------------------------------- intérieur
FLOOR_HALF_W = 45.0        # [DOC] sol 90 m de large (dUCKS)
FLOOR_X_SOUTH = -60.0      # [LID]/[DOC] front de tribune Sud (sol ≈ 122 m de long)
FLOOR_R = 18.0             # [PHO] rayon des angles du bol côté Sud (P7, P10)
ROOF_SOFFIT_MIN = 28.5     # [HYP] sous-face de toiture en rive (bord 31 m - 2,5 m)
TRUSS_BOTTOM = 30.5        # [DOC] membrure basse (45 m - 14 m de charpente)


# ---------------------------------------------------------------- contour complet
# Sommets dans le sens horaire (vu de dessus), arête k = OUTLINE[k] -> OUTLINE[k+1]
#   0 : façade Est (NE -> SE)   1 : extrémité Sud   2 : façade Ouest   3 : façade Nord (rue des Sorins)
NORTH_X0, NORTH_SLOPE = 93.0, -0.21   # [LID] façade Nord : X = 92 - 0,2·Y (biais visible sur MNS/BD TOPO)
OUTLINE = [
    (NORTH_X0 + NORTH_SLOPE * -HALF_W, -HALF_W),   # NE (108.5, -82.5)
    (X_SOUTH, -HALF_W),                            # SE
    (X_SOUTH, HALF_W),                             # SW
    (NORTH_X0 + NORTH_SLOPE * HALF_W, HALF_W),     # NW (75.5, 82.5)
]
OUTLINE_R = [10.0, R_CORNER, R_CORNER, 6.0]          # [LID] congés NE/NO, [LID] arcs Sud
# patios des bureaux [LID] (polygones horaires)
PATIO_A = [(65.0, 26.3), (73.8, 26.0), (83.8, -21.0), (66.0, -22.5)]   # fond ≈ +10 m
PATIO_B = [(81.3, -45.0), (96.3, -43.8), (97.5, -60.0), (83.8, -62.5)]  # fond = sol
PATIO_A_FLOOR = 10.0
PATIO_B_FLOOR = 0.0


def outline(offset=0.0, ds=1.0):
    from .geo2d import rounded_polygon
    return rounded_polygon(OUTLINE, OUTLINE_R, offset, ds, start_edge=0)


def _arc(cx, cy, r, a0, a1, ds):
    n = max(2, int(np.ceil(abs(a1 - a0) * r / ds)) + 1)
    a = np.linspace(a0, a1, n)
    return np.stack([cx + r * np.cos(a), cy + r * np.sin(a)], -1)


def _line(p0, p1, ds):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    n = max(2, int(np.ceil(np.linalg.norm(p1 - p0) / ds)) + 1)
    t = np.linspace(0, 1, n)[:, None]
    return p0 + (p1 - p0) * t


def envelope(offset=0.0, ds=1.0, x_end=X_RIBBON_END):
    """Courbe en U de l'enveloppe à 'offset' du nu de couronne.

    Parcours : façade Est (Y<0) du Nord vers le Sud, arc SE, extrémité Sud, arc SO,
    façade Ouest vers le Nord. Retourne (points Nx2, tangentes, normales sortantes, abscisse s).
    """
    w = HALF_W + offset
    r = R_CORNER + offset
    xs = X_SOUTH - offset
    segs = [
        _line((x_end, -w), (X_CORNER, -w), ds),
        _arc(X_CORNER, -Y_CORNER, r, -np.pi / 2, -np.pi, ds),
        _line((xs, -Y_CORNER), (xs, Y_CORNER), ds),
        _arc(X_CORNER, Y_CORNER, r, np.pi, np.pi / 2, ds),
        _line((X_CORNER, w), (x_end, w), ds),
    ]
    pts = [segs[0]] + [s[1:] for s in segs[1:]]
    p = np.concatenate(pts)
    t = np.gradient(p, axis=0)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    nrm = np.stack([-t[:, 1], t[:, 0]], -1)   # sens horaire vu du dessus -> extérieur à gauche
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))])
    return p, t, nrm, s


def crown_top_height(p):
    """Hauteur du haut de couronne [LID] en fonction de la position en plan (X, Y)."""
    X, Y = p[..., 0], p[..., 1]
    # extrémité Sud : 26,4 au milieu -> 28,5 à |Y|=50 -> 29,6 dans les arcs -> 31,2 sur les longs pans
    h_south = CROWN_TOP_SOUTH + (28.5 - CROWN_TOP_SOUTH) * (np.clip(np.abs(Y) / Y_CORNER, 0, 1) ** 2)
    # paramètre d'avancement le long des longs pans depuis l'arc
    t = np.clip((X - (X_SOUTH + 2)) / (X_CORNER + 20 - (X_SOUTH + 2)), 0, 1)
    t = t * t * (3 - 2 * t)
    side = np.abs(Y) > Y_CORNER - 0.01
    h_arc = h_south * (1 - t) + CROWN_TOP_LONG * t
    h = np.where(side | (X > X_SOUTH + 0.5), h_arc, h_south)
    # remontée vers le Nord à l'approche du bloc de scène/bureaux [LID] (u>60 : 42-44 m)
    k = np.clip((X - 54.0) / 12.0, 0, 1)
    k = k * k * (3 - 2 * k)
    return h * (1 - k) + 43.5 * k


def debug_outlines():
    out = []
    o = outline(0.0, 1.0)["p"]
    out.append(("couronne", np.vstack([o, o[:1]]), (255, 60, 60)))
    for pa in (PATIO_A, PATIO_B):
        out.append(("patio", np.vstack([pa, pa[:1]]), (0, 200, 255)))
    p, *_ = envelope(OFF_SCALES, 2.0, X_RIBBON_END)
    out.append(("ecailles", p, (255, 200, 0)))
    f = floor_outline(2.0)
    out.append(("sol", np.vstack([f, f[:1]]), (0, 255, 120)))
    out.append(("bureaux", np.array([(X_STAGE, -HALF_W), (X_STAGE, HALF_W)]), (255, 0, 255)))
    out.append(("nord", np.array([(X_OFFICE_N, -HALF_W), (X_OFFICE_N, HALF_W)]), (255, 0, 255)))
    return out


def floor_outline(ds=1.0):
    """Contour du sol (bol) : angles arrondis au Sud, droit contre le mur de scène."""
    w, r = FLOOR_HALF_W, FLOOR_R
    xs = FLOOR_X_SOUTH
    segs = [
        _line((X_STAGE, -w), (xs + r, -w), ds),
        _arc(xs + r, -w + r, r, -np.pi / 2, -np.pi, ds),
        _line((xs, -w + r), (xs, w - r), ds),
        _arc(xs + r, w - r, r, np.pi, np.pi / 2, ds),
        _line((xs + r, w), (X_STAGE, w), ds),
    ]
    return np.concatenate([segs[0]] + [s[1:] for s in segs[1:]])
