"""v1 : « USLAND Paris SXTour » - la piste USLAND Paris (version Zion, build_zion.py) aux proportions des pistes SX Tour
(Saint-Thibéry et Saint-Georges) : « refais une autre version à côté, avec les proportions de ces 2 pistes, mêmes enchaînements,
juste les proportions, grandeur des bords, tout ça ».

Comparaison (profils des couloirs, voir le commit) : bosses Paris 4,2 ft (médiane) contre 3,7 (STT) / 3,5 (SG) ; dessus de piste
34 ft + flancs 7 ft (coupe RF) contre 30,4 ft JGSX ; 180 de 24,5 ft (couloirs à 49 ft) contre 21,5 ft (couloirs à 43 ft).
Changé ici, rien d'autre (mêmes enchaînements, même nombre de bosses, mêmes écarts, même arène, même habillage) :
  - hauteur des obstacles x SX_K (0,87 : 4,2 -> 3,6 ft en médiane) ;
  - coupe en travers JGSX (dessus 30,4 ft, flanc mesuré sx_wall), comme Saint-Thibéry / Saint-Georges ;
  - 180 T1 et T_C au rayon JGSX 21,5 ft (couloirs voisins à 43 ft), virage après l'arrivée 32 -> 21,5 ft ;
  - extérieur des 180 x1,0 (comme STT) au lieu de x1,15.
Gardé tel quel (demandé par Ryan : « whoops garde ceux que j'ai, toute la ligne garde-la, et saut freestyle garde-le ») :
  - toute la ligne L1 (whoops, table, bosse), hauteurs et coupe ;
  - le saut du freestyle (L3, appel + gros saut rond du milieu) ;
  - T_D (virage avant L2, réglé à la main en v28t-w) : son rayon dépend de la place de L3.
Sortie : tracks/USLANDParisSXTour (piste à part, USLAND Paris n'est pas touchée).

  py -3.15 -I pistes/paris-2026/build_sxtour.py      (après pistes/paris-2026/stade_paris/src/build.py --mx)
"""
import os
import sys
import numpy as np
os.environ['PARIS_ZION'] = '1'
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_zion as BZ           # noqa: E402  (réglages de la version Zion = USLAND Paris)
import build_paris as BP          # noqa: E402
import layout_paris as LP         # noqa: E402
from engine import sx_wall        # noqa: E402

BP.FOLDER = "USLANDParisSXTour"
BP.DESC = "USLAND Paris SXTour"
BP.OUT = os.path.join(BP.ROOT, "tracks", BP.FOLDER)
BP.AP = os.path.join(HERE, "apercu_sxtour")

SX_K = 0.87                                    # hauteur des obstacles (médiane des bosses 4,2 -> 3,6 ft, SX Tour 3,5 - 3,7)
KEEP = ('PAR-L1', LP.L3_SEC)                   # gardés tels quels : toute la ligne des whoops, saut du freestyle
LP.R180 = LP.RB                                # 24,5 -> 21,5 ft (couloirs voisins à 43 ft, comme STT / SG)
LP.RB_L5B = LP.RB                              # virage après l'arrivée 32 -> 21,5 ft
LP.BERM180_GAIN = 1.0                          # extérieur des 180 comme STT (était 1,15)


def keep(name):
    return any(name.startswith(k) for k in KEEP)


_paris0 = LP.paris


def paris_sxtour(*a, **k):
    p = _paris0(*a, **k)
    for g in p.segs:
        if g['kind'] == 'S':
            g['sections'] = [s if keep(s[2]) else (np.asarray(s[0], float) * SX_K,) + tuple(s[1:]) for s in g['sections']]
    return p


LP.paris = paris_sxtour
_lane0 = BZ.lane_zion


def lane_sxtour(out, g, prof, u0, top, side, kl=1.0, kr=1.0, band=10.0):
    """coupe JGSX (dessus 30,4 ft, flanc mesuré), sauf la ligne gardée (L1) qui garde la coupe de USLAND Paris."""
    if g['tag'].startswith('L1'):
        return _lane0(out, g, prof, u0, top, side, kl, kr, band)
    top = BP.TW; L = len(prof) * 0.1; c, s_ = np.cos(g['t']), np.sin(g['t']); half = top / 2 + 8.0
    pts = np.array([(g['x0'] + uu * c - vv * s_, g['z0'] + uu * s_ + vv * c) for uu in (u0, u0 + L) for vv in (-half, half)])
    sl, X, Z = BZ.G.window(pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max())
    dx, dz = X - g['x0'], Z - g['z0']; u = dx * c + dz * s_ - u0; vs = -dx * s_ + dz * c
    pu = np.interp(u / 0.1, np.arange(len(prof)), prof, left=0, right=0)
    if kl != 1.0 or kr != 1.0:
        w = np.clip(vs / band + 0.5, 0, 1); w = w * w * (3 - 2 * w); pu = pu * (kl * (1 - w) + kr * w)
    out[sl] = np.maximum(out[sl], pu * sx_wall(np.abs(vs) - top / 2))


BZ.lane_zion = lane_sxtour


if __name__ == "__main__":
    BZ._open_retry()
    BP.main()
