"""v26 : ESTIMATION balistique d'un enchaînement (point matériel, pas le moteur du jeu) sur le vrai profil d'un couloir (côté gauche /
droit avec la coupe SPLIT_Z). Sortie de virage à V_EXIT ft/s, moteur a(v) = A0 (1 - v / VM), gravité sur la pente, 12 % d'énergie perdue
par bosse enroulée, POP ft/s verticaux ajoutés au décollage (le pilote « pompe »). Pour chaque saut prévu (bosse de départ -> bosse
cible), on cherche la vitesse mini pour poser 2 ft après la crête cible ; marge = vitesse qu'on a - vitesse qu'il faut (> 0 = ça passe).
Réglage (POP 10, V_EXIT 30) calé sur L2 v25f tel que Ryan l'a décrit après son test : double d'entrée tout juste, triple derrière raté de
peu, simple-triple impossible à gauche, triple d'entrée impossible.

  py -3.15 -I pistes/paris-2026/sim_rythme.py            (L2 actuel)
"""
import os
import sys
import numpy as np
os.environ.setdefault('PARIS_ZION', '1')
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "commun/scripts"))
g = 32.2
V_EXIT, POP, A0, VM, ROLL_LOSS = 30.0, 10.0, 20.0, 95.0, 0.88


def face_angle(h, i):
    hc = h[i]; j = i
    while j > 0 and h[j] > 0.9 * hc:
        j -= 1
    j9 = j
    while j > 0 and h[j] > 0.5 * hc:
        j -= 1
    return np.arctan((h[j9] - h[j]) / max((j9 - j) * 0.1, 0.1))


def fly(u, h, i, v):
    th = face_angle(h, i); i0 = i - 12; vx, vy = v * np.cos(th), v * np.sin(th) + POP; x0, y0 = u[i0], h[i0]
    for k in range(i + 3, len(u)):
        t = (u[k] - x0) / vx; y = y0 + vy * t - 0.5 * g * t * t
        if y <= h[k] + 0.05:
            vyl = vy - g * t; sl = np.arctan((h[min(k + 3, len(h) - 1)] - h[k - 3]) / 0.6)
            return k, max(vx * np.cos(sl) + vyl * np.sin(sl), 0.0), t
    return len(u) - 1, 0.0, 9.0


def need(u, h, i, j):
    lo, hi = 10.0, 100.0
    if u[fly(u, h, i, hi)[0]] <= u[j] + 2.0:
        return 99.0
    for _ in range(14):
        m = (lo + hi) / 2
        if u[fly(u, h, i, m)[0]] > u[j] + 2.0:
            hi = m
        else:
            lo = m
    return hi


def margins(u, H, pk, plan):
    jumps = dict(plan); k = 0; v = V_EXIT; out = []
    while k < len(u) - 2:
        bi = pk.index(k) if k in pk else None
        if bi is not None and bi in jumps:
            vn = need(u, H, k, pk[jumps[bi]]); out.append(round(v - vn, 1))
            if v < vn or len(out) == len(plan):
                return out
            k, v = fly(u, H, k, vn + 0.5)[:2]; continue
        if bi is not None:
            v *= np.sqrt(ROLL_LOSS)
        sl = (H[k + 1] - H[k]) / 0.1; c = 1 / np.sqrt(1 + sl * sl); a = A0 * max(1 - v / VM, 0) - g * sl * c
        v = np.sqrt(max(v * v + 2 * a * 0.1 / c, 1.0)); k += 1
    return out


def lane_sides(tag='L2'):
    import layout_paris as LP
    p = LP.paris(); s = next(s for s in p.segs if s['kind'] == 'S' and s['tag'].startswith(tag)); prof, u0, name = s['sections'][0]
    u = np.arange(0, s['L'], 0.1); h = np.interp(u, u0 + np.arange(len(prof)) * 0.1, prof, left=0, right=0)
    sides = []
    for k_ in (0, 1):                                    # 0 gauche (kl), 1 droite (kr) du sens de course
        f = np.ones_like(h)
        for a, b, kl, kr in LP.SPLIT_Z.get(name, []):
            f[(u >= u0 + a - 0.05) & (u <= u0 + b + 0.05)] = (kl, kr)[k_]
        sides.append(h * f)
    import layouts_sx as LS
    pk = [int(round((u0 + it[1] + float(np.argmax(prof[int(it[1] / 0.1):int(it[2] / 0.1) + 1])) * 0.1) / 0.1)) for it in LS.COMBOS[name]['items']]
    return u, sides, pk, name, s['L']


LINES = [("droite", "double - triple - triple (voulu)", [(0, 1), (2, 4), (5, 7)]), ("droite", "double - quadruple (non voulu)", [(0, 1), (2, 5)]),
         ("droite", "triple d'entrée (non voulu)", [(0, 2)]), ("gauche", "simple - triple (intérieur)", [(1, 3)])]

if __name__ == "__main__":
    u, (HL, HR), pk, name, L = lane_sides()
    print(name, "L = %.1f ft" % L)
    for nm, H in (("droite", HR), ("gauche", HL)):
        print("  %-6s crêtes %s  hauteurs %s" % (nm, [round(u[k], 1) for k in pk], [round(float(H[k]), 1) for k in pk]))
    for side, nm, plan in LINES:
        print("  %-6s %-36s marges %s" % (side, nm, margins(u, HR if side == "droite" else HL, pk, plan)))
