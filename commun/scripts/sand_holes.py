"""v13b - trous dans le sable de SX3 (demandé : « le sable est plat, je veux de vrais trous creusés dans le terrain »).

Tracé, emplacement et surface sable inchangés (stamps Glendale GR + GL). On CREUSE seulement (jamais de bosse ajoutée) :
  - creux réguliers le long de la ligne de course du stamp, perpendiculaires à la ligne (abscisse = point le plus proche
    de la ligne), sur toute la largeur du sable ;
  - profil mesuré sur le sable de JGSX 2026 Scuttle (piste JGSX installée, « Sand Exit » / « Sand Straight ») :
    espacement 36,5 ft (médiane 36,8, écart-type 1,7 sur 20 colonnes), profondeur crête -> creux 2,16 ft,
    forme en cosinus (écart < 0,06 au profil moyen mesuré) -> bords arrondis. Le stamp Glendale du dépôt ne peut pas servir :
    ses creux (jusqu'à -0,84 ft) ont été ramenés à 0 à la mesure (doc 03 § 5) et il n'a que 3 petites ondulations ;
  - même profondeur partout ; un nombre entier de périodes, centré sur la longueur de sable, qui commence et finit
    au niveau de la piste (entrée / sortie progressives sur une demi-période, aucune bosse à la sortie) ;
  - seulement le fond du sable du J (GL, la longue section) : les petites ondulations (< 1 ft) sont remplacées par les creux,
    les tables (> 1,5 ft) ne sont pas entamées, les creux s'arrêtent en douceur (2 -> 10 ft du pied d'une table) et remontent sur les 4 derniers
    pieds du bord du sable ; champ lissé (1,5 ft). Le virage de sable en S (GR, surtout un berm) est laissé tel quel.
Appelé par build_sx.py après le rendu du terrain."""
import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from engine import render_stamp

SPACING, DEPTH = 36.5, 2.16          # Scuttle sand (JGSX 2026), measured
FLOOR_LO, FLOOR_HI = 1.0, 1.5        # stamp height: holes replace the small sand ripples (< 1 ft); tables / berms (> 1.5 ft) kept
EDGE = 4.0                           # ft: holes fade to zero towards the edge of the sand
FEAT = (2.0, 10.0)                   # ft from the toe of a sand table / berm: no hole closer than 2 ft, full depth from 10 ft
SMOOTH = 1.5                         # ft: gaussian smoothing of the dug field (no seam in the turn of the J, no steps)
STAMPS = ('GL',)                     # the long sand section (the J); GR is a sand berm turn, left as it is

def _smooth(w):
    w = np.clip(w, 0, 1); return w * w * (3 - 2 * w)

def profile(s, s0, n):
    """depth (>= 0) along the line: n cosine periods starting at s0, zero outside."""
    u = (s - s0) / SPACING
    return np.where((u >= 0) & (u <= n), DEPTH * (1 - np.cos(2 * np.pi * u)) / 2, 0.0)

def apply(G, H, path, tile_map, sand_tiles):
    """dig the holes into H (in place) for every sand stamp segment of path; returns a report per stamp."""
    rep = {}
    for g in path.segs:
        if g['kind'] != 'P' or g['stamp'] not in STAMPS: continue
        h = np.zeros_like(H); t = np.full(H.shape, 255, np.int16)
        sl = render_stamp(G, h, t, g, tile_map)
        hs, ts = h[sl], t[sl]
        sand = np.isin(ts, sand_tiles)
        # riding line, resampled every 0.25 ft, arc length s
        W = g['pts']; cum = g['cum']; u = np.arange(0.0, cum[-1], 0.05)
        L = np.c_[np.interp(u, cum, W[:, 0]), np.interp(u, cum, W[:, 1])]
        i0, j0 = sl[0].start, sl[1].start
        ii, jj = np.nonzero(sand)
        d, k = cKDTree(L).query(np.c_[(jj + j0) * G.s, (ii + i0) * G.s]); s = u[k]
        near = d < 8.0
        sa, sb = float(s[near].min()), float(s[near].max()); n = int((sb - sa) // SPACING)
        s0 = sa + (sb - sa - n * SPACING) / 2
        dep = profile(s, s0, n)
        w_floor = _smooth((FLOOR_HI - hs[ii, jj]) / (FLOOR_HI - FLOOR_LO))
        w_edge = _smooth(ndi.gaussian_filter(ndi.distance_transform_edt(sand) * G.s, 1.0 / G.s)[ii, jj] / EDGE)   # smooth edge (tiles are 2 px blocks)
        dfeat = ndi.distance_transform_edt(hs < FLOOR_LO)[ii, jj] * G.s           # plan distance to a table / berm toe
        w_feat = _smooth((dfeat - FEAT[0]) / (FEAT[1] - FEAT[0]))
        field = np.zeros(hs.shape); field[ii, jj] = dep * w_floor * w_feat
        field = ndi.gaussian_filter(field, SMOOTH / G.s)
        w = np.zeros(hs.shape); w[ii, jj] = (dep > 0) * w_floor * w_feat; w = ndi.gaussian_filter(w, SMOOTH / G.s)
        w = w[ii, jj] * w_edge * w_floor
        cut = field[ii, jj] * w_edge * w_floor + w * hs[ii, jj]            # ripples under the holes levelled to the track floor
        Hs = H[sl]; Hs[ii, jj] -= cut; H[sl] = Hs
        rep[g['stamp']] = dict(holes=n, spacing=SPACING, depth=DEPTH, s_first=round(s0, 1), s_last=round(s0 + n * SPACING, 1),
                               sand_on_line=[round(sa, 1), round(sb, 1)], deepest=round(float(cut.max()), 2),
                               px_dug=int((cut > 0.01).sum()))
    return rep
