"""Objets de la piste Paris 2026 (étape 3) : ZION 2025 Paris (demande de Ryan : « reprends beaucoup de ZION, affiches, arrivée »)
+ nos objets de Saint-Georges / Saint-Thibéry.

ZION.2025.SupercrossParis (archive de Ryan, refs/zion25_full, local) - fichiers copiés dans <piste>/ext/ZION2025/ :
  - tuff blocks à logos ('bale.jm', textures de marques en séries de 8 comme ZION) le long des deux bords de chaque couloir,
    ~13 ft entre deux blocs (relevé sur ZION) ; Ryan les retouchera dans l'éditeur ;
  - gros blocs courbes ('tuff-bent.jm', collision .shp) au dos de chaque berm, tous les 6,6 ft (ZION) ;
  - banderole FINISH ('finishbanner') sur la crête de l'appel d'arrivée, à la même hauteur que chez ZION (+5 ft) ;
  - structure de départ ('start.jm'), mur de départ ('start_wall.jm') et arches Monster ('monster1.jm') : même position et
    même angle PAR RAPPORT À LA GRILLE DE DÉPART que sur ZION ;
  - paddock derrière le départ (camions 'semi.jm', tentes 'tent_carre.jm') le long du mur de scène.
Nos objets (tracks/USLAND2026SaintGeorgesbyBazo/statue, copiés dans <piste>/statue/usland/) :
  - grilles de départ ('start_grids', collision) au même endroit par rapport à la grille que sur Saint-Georges, et le cadre
    rouge qui tombe ('start_gate_frame') sur chacune des 22 grilles (lignes startinggate) ;
  - un poteau rond par virage ('pylon_round', logos Motul / 50 Factory / noir comme Saint-Georges), au bord intérieur ;
  - la cage du drapeau ('flag_cage') à côté de l'appel d'arrivée.
"""
import os
import re
import glob
import shutil
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ZSRC = os.path.join(HERE, "refs", "zion25_full", "ZION.2025.SupercrossParis")
ZNAME = "ZION.2025.SupercrossParis"
SGM = os.path.join(ROOT, "tracks", "USLAND2026SaintGeorgesbyBazo")
SGM_NAME = "USLAND2026SaintGeorgesbyBazo"
BRANDS = ['yamaha', 'honda', 'ducati', 'thor', 'triumph', 'suzuki', 'kawa', 'husqy', 'vd76', 'gas']
rng = np.random.default_rng(26)


def statue_ang(fx, fz):
    """yaw d'une statue dont le +z local doit pointer vers (fx, fz) (props_place.statue_ang)."""
    return float(np.arctan2(fx, fz))


def rot(v, d):
    """rotation dans le plan (x, z) cohérente avec les yaws des statues (angle = atan2(x, z))."""
    r = np.hypot(v[0], v[1]); a = np.arctan2(v[0], v[1]) + d
    return np.array([r * np.sin(a), r * np.cos(a)])


class Copier:
    """copie les fichiers référencés (+ .gz, _norm, _spec) et réécrit les chemins @SRC/... -> @FOLDER/<dst>/..."""
    def __init__(self, out, folder):
        self.out, self.folder, self.done = out, folder, set()

    def ref(self, src_root, src_name, dst_sub, rel):
        if rel in ('null',) or rel.startswith('@startgate') or not rel.startswith('@' + src_name + '/'):
            return rel
        r = rel[len(src_name) + 2:]
        for cand in [r, r + '.gz'] + [re.sub(r'(\.png)$', s + r'\1', r) for s in ('_norm', '_spec')] + \
                [r.replace('-repeat.png', s + '-repeat.png') for s in ('_norm', '_spec')]:
            src = os.path.join(src_root, cand)
            if os.path.exists(src) and (src_root, cand) not in self.done:
                dst = os.path.join(self.out, dst_sub, cand); os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy(src, dst); self.done.add((src_root, cand))
        return '@%s/%s/%s' % (self.folder, dst_sub, r)

    def line(self, x, y, z, yaw, model, tex, shp, src='zion'):
        root, name, sub = (ZSRC, ZNAME, 'ext/ZION2025') if src == 'zion' else (SGM, SGM_NAME, 'statue/usland')
        return '[%.6f %.6f %.6f] %.6f %s %s %s' % (x, y, z, yaw, self.ref(root, name, sub, model), self.ref(root, name, sub, tex),
                                                  self.ref(root, name, sub, shp))


def zion_lines(pattern):
    return [l for l in open(os.path.join(ZSRC, 'statues')).read().splitlines() if re.search(pattern, l)]


def parse(l):
    m = re.match(r'\[([-\d.]+) ([-\d.]+) ([-\d.]+)\] ([-\d.]+) (\S+) (\S+) (\S+)', l)
    return [float(m.group(i)) for i in range(1, 5)] + [m.group(5), m.group(6), m.group(7)]


def gate_frame(lines):
    """centre et angle « avant » (atan2(x, z) du sens des pilotes) d'une rangée de grilles (lignes startinggate)."""
    P = []; a = None
    for l in lines:
        m = re.match(r'\[([-\d.]+) [-\d.]+ ([-\d.]+)\] ([-\d.]+)', l)
        if m:
            P.append((float(m.group(1)), float(m.group(2)))); a = float(m.group(3))
    f = np.array([-np.sin(a), -np.cos(a)])
    return np.mean(P, axis=0), float(np.arctan2(f[0], f[1]))


def gate_lines(path):
    L = open(path).read().split('\n'); i = L.index('startinggate:'); j = L.index('checkpoints:')
    return L[i + 1:j]


def muret(out, folder):
    """panneau blanc 20 ft x 2,6 ft x 0,4 ft (long suivant +z local), matière 'white_matte' du stade -> statue/usland/muret_blanc.jm"""
    import sys
    sys.path.insert(0, os.path.join(ROOT, "stade_paris", "src"))
    from arena.mesh import box
    from arena.export import jm_text
    FT = 3.28084
    m = box((0.4 / FT, 20.0 / FT, 2.6 / FT))                 # repère de l'arène (m) : X, Y plan, Z haut ; centré
    m.V[:, 2] += 1.3 / FT                                     # posé au sol
    d = os.path.join(out, "statue", "usland"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "muret_blanc.jm"), "w", newline="\n").write(jm_text(m, "white_matte"))
    from PIL import Image                                    # blanc cassé, très léger grain (règle du projet : grain sur le mat)
    g = np.clip(238 + np.random.default_rng(5).normal(0, 3, (64, 64)), 0, 255).astype(np.uint8)
    Image.fromarray(np.dstack([g, g, g - 2])).save(os.path.join(d, "muret_blanc.png"))
    return "@%s/statue/usland/muret_blanc.jm @%s/statue/usland/muret_blanc.png null" % (folder, folder)


def build(out, folder, H, S, path, start, combos, finish_s_fn, lanes_skip=('LD', 'C', 'T_')):
    C = Copier(out, folder); st = []
    hgt = lambda x, z: float(H[int(np.clip(round(z / S), 0, H.shape[0] - 1)), int(np.clip(round(x / S), 0, H.shape[1] - 1))])
    smp = path.samples(1.0)
    from scipy.spatial import cKDTree
    tree = cKDTree(np.c_[smp['x'], smp['z']])
    # ---- 1. tuff blocks ZION le long des couloirs (pas sur la ligne de départ / colonne / virages)
    n_tuff = 0
    seg_of = smp['seg']
    # murets blancs le long des whoops (visuel) : panneaux de 20 ft x 2,6 ft, matière blanche du stade ; pas de tuffs à cet endroit
    wall_model = muret(out, folder)
    whoops_rng = {}
    for gi, g in enumerate(path.segs):
        if g['kind'] == 'S':
            for prof, u0, name in g['sections']:
                for it in combos[name]['items']:
                    if it[0].startswith('whoops'):
                        whoops_rng[gi] = (u0 + it[1] - 4.0, u0 + it[2] + 4.0)
    n_wall = 0
    for gi, (ua, ub) in whoops_rng.items():
        g = path.segs[gi]; c, s_ = np.cos(g['t']), np.sin(g['t']); nrm = np.array([-s_, c])
        for side in (-1, 1):
            a0 = np.array([g['x0'] + (ua + ub) / 2 * c, g['z0'] + (ua + ub) / 2 * s_])
            probe = [j for j in tree.query_ball_point(a0 + nrm * side * 43.0, 12.0) if abs(smp['s'][j] - (g['s0'] + (ua + ub) / 2)) > 40]
            off = (abs(np.dot(np.array([smp['x'][probe[0]], smp['z'][probe[0]]]) - a0, nrm)) / 2) if probe else 20.0
            for u in np.arange(ua + 10.0, ub - 9.9, 20.0):
                p = np.array([g['x0'] + u * c, g['z0'] + u * s_]) + nrm * side * off
                st.append('[%.6f 0.000000 %.6f] %.6f %s' % (p[0], p[1], statue_ang(c, s_), wall_model)); n_wall += 1
    for gi, g in enumerate(path.segs):
        if g['kind'] != 'S' or not g['sections'] or g['L'] < 40:
            continue
        c, s_ = np.cos(g['t']), np.sin(g['t']); nrm = np.array([-s_, c])
        for side in (-1, 1):
            k = 0; brand = BRANDS[rng.integers(len(BRANDS))]
            for u in np.arange(6.0, g['L'] - 6.0, 13.0):
                if gi in whoops_rng and whoops_rng[gi][0] <= u <= whoops_rng[gi][1]:
                    continue
                a0 = np.array([g['x0'] + u * c, g['z0'] + u * s_])
                # couloir voisin parallèle de ce côté (< 60 ft) : UNE seule rangée au milieu (comme le visuel), posée une fois
                probe = [j for j in tree.query_ball_point(a0 + nrm * side * 43.0, 12.0) if abs(smp['s'][j] - (g['s0'] + u)) > 40]
                if probe:
                    j = probe[int(np.argmin([np.hypot(smp['x'][q] - a0[0] - nrm[0] * side * 43, smp['z'][q] - a0[1] - nrm[1] * side * 43) for q in probe]))]
                    if seg_of[j] < gi:
                        continue                                                    # déjà posée par l'autre couloir
                    dn = abs(np.dot(np.array([smp['x'][j], smp['z'][j]]) - a0, nrm))
                    p = a0 + nrm * side * dn / 2
                else:
                    p = a0 + nrm * side * 20.0
                near = tree.query_ball_point(p, 14.0)
                if any(abs(smp['s'][j] - (g['s0'] + u)) > 40 and abs(np.dot(np.array([smp['x'][j], smp['z'][j]]) - a0, nrm)) < 30
                       for j in near):                                            # un autre couloir passe dessus
                    continue
                if hgt(*p) > 3.0:                                                   # sur une grosse butte : non
                    continue
                if k % 8 == 0:
                    brand = BRANDS[rng.integers(len(BRANDS))]
                toward = -nrm * side
                st.append(C.line(p[0], 0.0, p[1], statue_ang(*toward), '@%s/statue/bale.jm' % ZNAME,
                                 '@%s/statue/%s.png' % (ZNAME, brand), 'null'))
                k += 1; n_tuff += 1
    # ---- 2. gros blocs courbes au dos des berms (ZION : tuff-bent, collision)
    from engine import turn_mid_angle
    n_bent = 0
    for g in path.segs:
        if g['kind'] != 'T' or not g.get('berm'):
            continue
        mid = turn_mid_angle(g); rr = np.arange(g['r'], g['r'] + 60, 0.5)
        hh = np.array([hgt(g['cx'] + r * np.cos(mid), g['cz'] + r * np.sin(mid)) for r in rr])
        k0 = int(np.argmax(hh)); out_r = rr[k0 + int(np.argmax(hh[k0:] < 0.3))] + 1.5
        span = np.radians(abs(g['ang'])) * 0.5 + np.radians(8)
        n = int(span * 2 * out_r / 6.6)
        for a in np.linspace(mid - span, mid + span, n):
            x, z = g['cx'] + out_r * np.cos(a), g['cz'] + out_r * np.sin(a)
            if hgt(x, z) > 2.5:
                continue
            tang = np.array([-np.sin(a), np.cos(a)])
            st.append(C.line(x, 0.0, z, statue_ang(*tang), '@%s/statue/tuff-bent.jm' % ZNAME,
                             '@%s/statue/tuff3.png' % ZNAME, '@%s/statue/tuff-bent.shp' % ZNAME))
            n_bent += 1
    # ---- 3. poteau rond par virage (Saint-Georges), bord intérieur
    skins = ['pylon_round_motul', 'pylon_round_f50', 'pylon_round']; n_py = 0
    for g in path.segs:
        if g['kind'] == 'T' and abs(g['ang']) >= 90:
            mid = turn_mid_angle(g); r = max(1.5, g['r'] - 15.2 - 1.5)
            x, z = g['cx'] + r * np.cos(mid), g['cz'] + r * np.sin(mid)
            st.append(C.line(x, 0.0, z, statue_ang(np.cos(mid), np.sin(mid)), '@%s/statue/pylon_round.jm' % SGM_NAME,
                             '@%s/statue/%s.png' % (SGM_NAME, skins[n_py % 3]), '@%s/statue/pylon_round.shp' % SGM_NAME, 'sgm'))
            n_py += 1
    # ---- 4. arrivée : banderole FINISH ZION sur la crête de l'appel + cage du drapeau
    sF, _ = finish_s_fn
    i = int(np.argmin(np.abs(smp['s'] - sF))); fx, fz, th = smp['x'][i], smp['z'][i], smp['th'][i]
    d = np.array([np.cos(th), np.sin(th)])
    fb = parse(zion_lines(r'finishbanner-repeat')[0])
    st.append(C.line(fx, fb[1], fz, statue_ang(-d[0], -d[1]), fb[4], fb[5], fb[6]))   # ZION : +z local opposé au sens de course
    n_ = np.array([-d[1], d[0]])
    side_ = min((-1, 1), key=lambda sd: -tree.query(np.array([fx, fz]) + n_ * sd * 30.0)[0])   # côté le plus dégagé
    n_ = n_ * side_; q = np.array([fx, fz]) - d * 13.0 + n_ * 26.0
    st.append(C.line(q[0], 0.0, q[1], statue_ang(*(-n_)), '@%s/statue/flag_cage.jm' % SGM_NAME, '@%s/statue/flag_cage.png' % SGM_NAME, 'null', 'sgm'))
    # ---- 5. départ : grilles de Saint-Georges + structure / mur / arches de ZION, calés sur la grille
    G0 = np.array(start['gate']); h0 = np.radians(start['heading']); f0 = np.array([np.cos(h0), np.sin(h0)]); phi0 = float(np.arctan2(f0[0], f0[1]))
    skipped = []
    # (le mur de départ de ZION est 216 ft derrière sa grille : chez nous ce serait derrière le mur de scène -> non repris)
    for src, gpath, pat in (('sgm', os.path.join(SGM, 'timing_gates'), r'start_grids'),
                            ('zion', os.path.join(ZSRC, 'timing_gates'), r'/start\.jm|monster1\.jm')):
        Gr, phir = gate_frame(gate_lines(gpath))
        lines = [l for l in open(os.path.join(SGM if src == 'sgm' else ZSRC, 'statues')).read().splitlines() if re.search(pat, l)]
        for l in lines:
            x, y, z, a, m, t, s = parse(l)
            p = G0 + rot(np.array([x, z]) - Gr, phi0 - phir)
            if 'monster1' in m and tree.query(p)[0] < 25.0:                 # pas sur un couloir
                skipped.append(os.path.basename(m)); continue
            st.append(C.line(p[0], y, p[1], a + (phi0 - phir), m, t, s, src))
    # ---- 6. paddock derrière le départ (camions + tentes ZION), le long du mur de scène (camions 77 ft, axe z)
    semis = zion_lines(r'semis/semi\.jm')[:4]; tents = zion_lines(r'tent_carre\.jm')[:4]
    xb = G0[0] + 52.0                                        # entre la grille et le mur de scène
    for k, l in enumerate(semis):
        x, y, z, a, m, t, s = parse(l); zz = 430.0 + k * 90.0
        st.append(C.line(xb + 6.0, 0.0, zz, np.pi, m, t, s))
    for k, l in enumerate(tents):
        x, y, z, a, m, t, s = parse(l); zz = 475.0 + k * 90.0
        st.append(C.line(xb - 20.0, 0.0, zz, 0.0, m, t, s))
    # grilles : le cadre rouge de Saint-Georges sur chacune des 22 grilles
    gate_model = ' '.join([C.ref(SGM, SGM_NAME, 'statue/usland', '@%s/statue/start_gate_frame.jm' % SGM_NAME),
                           C.ref(SGM, SGM_NAME, 'statue/usland', '@%s/statue/start_gate_frame.png' % SGM_NAME), '@startgate.shp'])
    info = dict(tuffs=n_tuff, murets=n_wall, blocs_virages=n_bent, poteaux=n_py, total=len(st), fichiers=len(C.done), ecartes=skipped)
    return st, gate_model, info
