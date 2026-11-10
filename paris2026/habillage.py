"""Habillage « comme en vrai » de la piste Paris 2026 (demande de Ryan, 2026-11-10) : remplace objets.py (ZION + Saint-Georges).

D'après les photos du Supercross de Paris (paris2026/refs/photos2025, local). Les modèles sont dans hab_objets.py.
Le tracé 2026 n'est pas celui des photos : chaque sponsor est posé à l'endroit ÉQUIVALENT (voir PLAN ci-dessous).
Plus rien de ZION dans la piste. Repris de Saint-Georges : grilles de départ + cadres, poteaux ronds, boudins, cage du drapeau.

PLAN (couloir / virage -> sponsor)
  L5 arrivée : tuffs Honda, rampe acier + coins Honda sur l'appel, panneau FINISH suspendu au-dessus de la ligne
  L3 saut du milieu : bâche AMV des deux côtés de l'appel, tuffs AMV, tremplins FMX habillés noir Venum
  L2 singles : tuffs Seong            L1 whoops : boudins rouges « R » des deux côtés, puis tuffs Monster
  LR tribune Est : tuffs Motul        L6 tribune Sud : tuffs Yamaha, arche 50 Factory sur la dernière bosse
  LD ligne de départ : boudins Motul le long de l'entonnoir, mur Automoto à l'extérieur du premier virage
  virages : murs bâchés + bandeau (T1 Honda, T_C Five, T_E / T_TR Seong, T_L5a AMV, T_D / T_Bb Moto Verte),
            filets derrière les quatre grands virages (bandeau Venum rouge côté tribunes)
  départ : bandeau START Venum / Monster sur treillis, mur de fond, 2 canettes Monster, portique Minerva Oil (podium, collision)
  paddock : 11 camions entre le départ et le mur de scène (provisoire)
"""
import os
import re
import shutil
import numpy as np
import hab_objets as HO

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SGM = os.path.join(ROOT, "tracks", "USLAND2026SaintGeorgesbyBazo")
PROPS = os.path.join(ROOT, "assets", "props")
SUB = "statue/paris"
LANE_SKIN = {'L5': 'honda', 'L3': 'amv', 'L2': 'seong', 'L1': 'monster', 'LR': 'motul', 'L6': 'yamaha', 'LD': 'monster'}
TURN_SKIN = {'T1 ': ('honda', 'noir'), 'T_C ': ('five', 'noir'), 'T_E ': ('seong', 'venum'), 'T_TR': ('seong', 'venum'),
             'T_L5a': ('amv', None), 'T_D': ('motoverte', None), 'T_Bb': ('motoverte', None)}
PADDOCK = ['ktm', 'kawasaki', 'yamaha', 'monster', 'honda', 'honda', 'blanc', 'triumph', 'ducati', 'yamaha', 'kawasaki']


def ang(fx, fz):
    """yaw d'une statue dont le +z local doit pointer vers (fx, fz) (props_place.statue_ang), entre -pi et pi."""
    return float(np.arctan2(fx, fz))


def build(out, folder, H, S, path, start, combos, finish_s_fn):
    from scipy.spatial import cKDTree
    from engine import turn_mid_angle
    from starts import StartRoute
    import layout_paris as LP
    D = os.path.join(out, *SUB.split('/')); os.makedirs(D, exist_ok=True)
    ref = lambda f: '@%s/%s/%s' % (folder, SUB, f) if f else 'null'
    st = []; cnt = {}

    def put(kind, x, z, yaw, model, tex, shp=None, y=0.0):
        st.append('[%.6f %.6f %.6f] %.6f %s %s %s' % (x, y, z, yaw, ref(model), ref(tex), ref(shp)))
        cnt[kind] = cnt.get(kind, 0) + 1

    hgt = lambda x, z: float(H[int(np.clip(round(z / S), 0, H.shape[0] - 1)), int(np.clip(round(x / S), 0, H.shape[1] - 1))])
    smp = path.samples(1.0); tree = cKDTree(np.c_[smp['x'], smp['z']]); seg_of = smp['seg']
    RT = StartRoute(start, LP.N_GATES, LP.GATE_PITCH); rs = RT.samples(1.0); rtree = cKDTree(np.c_[rs['x'], rs['z']])
    rw = np.array([RT.width(s) for s in rs['s']])

    def libre(p, lap=16.5, extra=1.5):
        """True si p est hors du tour (>= lap ft de la ligne) et hors du couloir de départ (demi-largeur + extra)."""
        if tree.query(p)[0] < lap:
            return False
        d, j = rtree.query(p)
        return d >= rw[j] / 2 + extra

    # ---- modèles
    HO.tuff_arc(D); HO.boudins(D); HO.mur(D); HO.filet(D); HO.amv_jupe(D); HO.minerva(D); HO.depart(D); HO.canette(D); HO.semi(D)
    HO.pylones(D, os.path.join(SGM, "statue"))
    for f in ('boudin_logo.jm', 'boudin_logo.shp', 'boudin_logo3.jm', 'boudin_logo3.shp'):                # boudins de Saint-Georges
        shutil.copy(os.path.join(PROPS, f), os.path.join(D, f))
    for f in ('pylon_round.jm', 'pylon_round.shp', 'flag_cage.jm', 'flag_cage.png', 'start_grids.jm', 'start_grids.png', 'start_grids.shp',
              'start_gate_frame.jm', 'start_gate_frame.png'):
        shutil.copy(os.path.join(SGM, "statue", f), os.path.join(D, f))
    for e in ('', '_norm', '_spec'):
        for b in ('start_grids', 'start_gate_frame', 'flag_cage'):
            f = os.path.join(SGM, "statue", b + e + '.png')
            if e and os.path.exists(f):
                shutil.copy(f, os.path.join(D, b + e + '.png'))

    # ---- 1. whoops : boudins rouges « R » de 18 ft des deux côtés (photo), pas de tuffs à cet endroit
    whoops_rng = {}
    for gi, g in enumerate(path.segs):
        if g['kind'] == 'S':
            for prof, u0, name in g['sections']:
                for it in combos[name]['items']:
                    if it[0].startswith('whoops'):
                        whoops_rng[gi] = (u0 + it[1] - 4.0, u0 + it[2] + 4.0)
    pts_r = []
    for gi, (ua, ub) in whoops_rng.items():
        g = path.segs[gi]; c, s_ = np.cos(g['t']), np.sin(g['t']); nrm = np.array([-s_, c])
        for side in (-1, 1):
            a0 = np.array([g['x0'] + (ua + ub) / 2 * c, g['z0'] + (ua + ub) / 2 * s_])
            probe = [j for j in tree.query_ball_point(a0 + nrm * side * 43.0, 12.0) if abs(smp['s'][j] - (g['s0'] + (ua + ub) / 2)) > 40]
            off = (abs(np.dot(np.array([smp['x'][probe[0]], smp['z'][probe[0]]]) - a0, nrm)) / 2) if probe else 19.0
            for u in np.arange(ua + 9.3, ub - 9.2, 18.6):
                p = np.array([g['x0'] + u * c, g['z0'] + u * s_]) + nrm * side * off
                put('boudins R (whoops)', p[0], p[1], ang(*(-nrm * side)), 'boudin_logo3.jm', 'boudin3_r.png', 'boudin_logo3.shp')
                pts_r += [p + np.array([c, s_]) * q for q in (-6.0, 0.0, 6.0)]

    # ---- 2. tuff blocks (demi-tonneaux) le long des couloirs, un sponsor par couloir
    for gi, g in enumerate(path.segs):
        if g['kind'] != 'S' or g['L'] < 40:
            continue
        skin = next((v for k, v in LANE_SKIN.items() if g['tag'].startswith(k)), None)
        if skin is None:
            continue
        c, s_ = np.cos(g['t']), np.sin(g['t']); nrm = np.array([-s_, c]); hmax = 9.0 if g['tag'].startswith('L3') else 3.0
        for side in (-1, 1):
            for u in np.arange(6.0, g['L'] - 6.0, 13.0):
                if gi in whoops_rng and whoops_rng[gi][0] <= u <= whoops_rng[gi][1]:
                    continue
                a0 = np.array([g['x0'] + u * c, g['z0'] + u * s_])
                # couloir voisin parallèle de ce côté (< 60 ft) : UNE seule rangée au milieu, posée une fois
                probe = [j for j in tree.query_ball_point(a0 + nrm * side * 43.0, 12.0) if abs(smp['s'][j] - (g['s0'] + u)) > 40]
                if probe:
                    j = probe[int(np.argmin([np.hypot(smp['x'][q] - a0[0] - nrm[0] * side * 43, smp['z'][q] - a0[1] - nrm[1] * side * 43) for q in probe]))]
                    if seg_of[j] < gi:
                        continue
                    p = a0 + nrm * side * abs(np.dot(np.array([smp['x'][j], smp['z'][j]]) - a0, nrm)) / 2
                else:
                    p = a0 + nrm * side * 20.0
                if not libre(p) or hgt(*p) > hmax or any(np.hypot(*(p - q)) < 7.0 for q in pts_r):   # pas sur un boudin des whoops
                    continue
                put('tuffs ' + skin, p[0], p[1], ang(*(-nrm * side)), 'tuff_arc.jm', 'tuff_arc_%s.png' % skin, 'tuff_arc.shp')

    # ---- 3. virages : mur bâché + bandeau du sponsor au dos du berm, filet derrière les grands virages, poteau rond à l'intérieur
    skins_py = ['pylone_monster.png', 'pylone_honda.png', 'pylone_venum.png']; n_py = 0
    for g in path.segs:
        if g['kind'] != 'T':
            continue
        mid = turn_mid_angle(g)
        if abs(g['ang']) >= 90:
            r = max(1.5, g['r'] - 15.2 - 1.5); x, z = g['cx'] + r * np.cos(mid), g['cz'] + r * np.sin(mid)
            if libre((x, z), lap=10.0, extra=1.0):
                put('poteaux ronds', x, z, ang(np.cos(mid), np.sin(mid)), 'pylon_round.jm', skins_py[n_py % 3], 'pylon_round.shp'); n_py += 1
        sk = next((v for k, v in TURN_SKIN.items() if g['tag'].startswith(k)), None)
        if not g.get('berm') or sk is None:
            continue
        rr = np.arange(g['r'], g['r'] + 60, 0.5)
        hh = np.array([hgt(g['cx'] + r * np.cos(mid), g['cz'] + r * np.sin(mid)) for r in rr])
        k0 = int(np.argmax(hh)); out_r = rr[k0 + int(np.argmax(hh[k0:] < 0.3))] + 2.0
        span = np.radians(abs(g['ang'])) * 0.5 + np.radians(6)
        for kind, rad, model, tex, shp_ in (('murs ' + sk[0], out_r, 'mur.jm', 'mur_%s.png' % sk[0], 'mur.shp'),
                                            ('filets', out_r + 3.6, 'filet.jm', 'filet_%s.png' % sk[1], None)):
            if tex.endswith('None.png'):
                continue
            n = max(2, int(round(2 * span * rad / 8.05)))
            for a in (mid + (np.arange(n) - (n - 1) / 2) * (8.05 / rad)):
                x, z = g['cx'] + rad * np.cos(a), g['cz'] + rad * np.sin(a)
                if not libre((x, z), lap=17.0) or hgt(x, z) > 1.0:
                    continue
                put(kind, x, z, ang(-np.cos(a), -np.sin(a)), model, tex, shp_)

    # ---- 4. arrivée : panneau FINISH suspendu au-dessus de la ligne, rampe acier + coins Honda sur l'appel, cage du drapeau
    sF, _ = finish_s_fn
    i = int(np.argmin(np.abs(smp['s'] - sF))); fx, fz, th = smp['x'][i], smp['z'][i], smp['th'][i]
    d = np.array([np.cos(th), np.sin(th)]); hF = hgt(fx, fz)
    HO.finish(D, drop=hF); put('panneau FINISH suspendu', fx, fz, ang(*d), 'finish.jm', 'finish.png')
    us = np.arange(-26.0, 0.01, 1.0)                                          # coupe de l'appel, 26 ft avant la crête
    HO.rampe_honda(D, us + 26.0, np.array([hgt(fx + d[0] * u, fz + d[1] * u) for u in us]))
    put('rampe + coins Honda', fx - d[0] * 26.0, fz - d[1] * 26.0, ang(*d), 'rampe_honda.jm', 'rampe_honda.png')
    n_ = np.array([-d[1], d[0]])
    side_ = min((-1, 1), key=lambda sd: -tree.query(np.array([fx, fz]) + n_ * sd * 30.0)[0]); n_ = n_ * side_
    q = np.array([fx, fz]) - d * 13.0 + n_ * 26.0
    put('cage du drapeau', q[0], q[1], ang(*(-n_)), 'flag_cage.jm', 'flag_cage.png')
    for sd in (-1, 1):                                                        # boudins gris Thor au pied de l'appel (photo)
        for k in range(3):
            p = np.array([fx, fz]) - d * (30.0 + 6.4 * k) + np.array([-d[1], d[0]]) * sd * 19.0
            if libre(p):
                put('boudins Thor', p[0], p[1], ang(*(np.array([d[1], -d[0]]) * sd)), 'boudin_logo.jm', 'boudin_thor.png', 'boudin_logo.shp')

    # ---- 5. saut du milieu : bâche AMV des deux côtés de l'appel ; tremplins FMX : habillage noir Venum
    g3 = next(g for g in path.segs if g['kind'] == 'S' and any(n == LP.L3_SEC for _, _, n in g['sections']))
    prof, u0, name = next(sc for sc in g3['sections'] if sc[2] == LP.L3_SEC)
    it = [i_ for i_ in combos[name]['items'] if 'appel' in i_[0]][0]
    i0, i1 = int(it[1] / 0.1), int(it[2] / 0.1); uc = u0 + it[1] + float(np.argmax(prof[i0:i1])) * 0.1
    c, s_ = np.cos(g3['t']), np.sin(g3['t']); nrm = np.array([-s_, c]); pc = np.array([g3['x0'] + uc * c, g3['z0'] + uc * s_])
    amv = {}
    for sd in (-1, 1):
        vv = np.arange(8.0, 45.0, 0.25); hv = np.array([hgt(*(pc + nrm * sd * v)) for v in vv])
        vf = float(vv[int(np.argmax(hv < 0.4))]) + 0.4; p = pc + nrm * sd * vf - np.array([c, s_]) * 6.0
        put('bâche AMV', p[0], p[1], ang(*(nrm * sd)), 'amv_jupe.jm', 'amv_jupe.png'); amv[sd] = round(vf, 1)
    ramp_jm = os.path.join(ROOT, "assets", "fmx_ramp_user", LP.FMX_MODEL['model'] + ".jm")
    HO.fmx_jupe(D, ramp_jm)
    for r in LP.fmx_ramps(path):
        (x, z), h = r['lip'], r['heading']; dd = np.array([np.cos(h), np.sin(h)])
        put('habillage Venum des tremplins', x - dd[0] * LP.FMX_MODEL['model_len'], z - dd[1] * LP.FMX_MODEL['model_len'], ang(-dd[0], -dd[1]),
            'fmx_jupe.jm', 'fmx_jupe.png')

    # ---- 6. arche 50 Factory sur la dernière bosse du couloir de la tribune Sud (L6), juste avant le virage du fond
    g6 = next(g for g in path.segs if g['kind'] == 'S' and g['tag'].startswith('L6'))
    prof, u0, name = g6['sections'][0]; it = combos[name]['items'][-1]
    i0, i1 = int(it[1] / 0.1), int(it[2] / 0.1); ua = u0 + it[1] + float(np.argmax(prof[i0:i1])) * 0.1
    c, s_ = np.cos(g6['t']), np.sin(g6['t']); pa = np.array([g6['x0'] + ua * c, g6['z0'] + ua * s_]); ha = hgt(*pa)
    A = HO.arche_50(D, drop=ha, half=23.5, hleg=24.5); put('arche 50 Factory', pa[0], pa[1], ang(c, s_), 'arche_50.jm', 'arche_50.png')
    feet = [hgt(*(pa + np.array([-s_, c]) * sd * A['half'])) for sd in (-1, 1)]

    # ---- 7. départ : grilles de Saint-Georges, bandeau START + mur de fond, canettes Monster, portique Minerva Oil
    G0 = np.array(start['gate']); h0 = np.radians(start['heading']); f0 = np.array([np.cos(h0), np.sin(h0)]); n0 = np.array([-f0[1], f0[0]])
    import objets as OB
    Gr, phir = OB.gate_frame(OB.gate_lines(os.path.join(SGM, 'timing_gates'))); phi0 = float(np.arctan2(f0[0], f0[1]))
    for l in open(os.path.join(SGM, 'statues')).read().splitlines():
        if re.search(r'start_grids', l):
            x, y, z, a, m, t, s = OB.parse(l); p = G0 + OB.rot(np.array([x, z]) - Gr, phi0 - phir)
            a2 = (a + (phi0 - phir) + np.pi) % (2 * np.pi) - np.pi
            put('grilles de départ', p[0], p[1], a2, 'start_grids.jm', 'start_grids.png', 'start_grids.shp', y=y)
    put('bandeau START + mur de fond', G0[0], G0[1], ang(*f0), 'depart.jm', 'depart.png')
    for sd in (-1, 1):
        p = G0 - f0 * 19.0 + n0 * sd * 55.0
        put('canettes Monster', p[0], p[1], ang(*f0), 'canette.jm', 'canette.png')
    pm = G0 - f0 * 15.0 + n0 * (-70.0 if n0[1] < 0 else 70.0)                 # côté Sud du départ (z +), dans l'alignement du mur de fond
    put('portique Minerva Oil', pm[0], pm[1], ang(*f0), 'minerva.jm', 'minerva.png', 'minerva.shp')
    # boudins Motul le long de l'entonnoir (photo du premier virage), mur Automoto à l'extérieur du premier virage
    for s in np.arange(150.0, RT.s_straight - 4.0, 12.0):
        j = int(np.argmin(np.abs(rs['s'] - s))); p0 = np.array([rs['x'][j], rs['z'][j]])
        for sd in (-1, 1):
            p = p0 + n0 * sd * (RT.width(s) / 2 + 2.2)
            if libre(p, lap=16.5, extra=0.5):
                put('boudins Motul', p[0], p[1], ang(*(-n0 * sd)), 'boudin_logo.jm', 'boudin_motul.png', 'boudin_logo.shp')
    xw = (path.lanes['xLR'] + 15.2 + path.lanes['xT5'] - 15.2) / 2
    for z in np.arange(path.lanes['zL5'] + 30.0, path.lanes['zLD'] + 52.0, 8.05):
        if libre((xw, z), lap=17.0):
            put('murs automoto', xw, z, ang(1.0, 0.0), 'mur.jm', 'mur_automoto.png', 'mur.shp')

    # ---- 8. paddock : camions entre le départ et le mur de scène (cabine côté mur, auvent sur le côté)
    xs = G0[0] - f0[0] * 70.0                                                 # avant de la remorque
    for k, team in enumerate(PADDOCK):
        z = 422.0 + 33.0 * k                                                  # l'auvent (24 ft, côté Nord) reste sur le sol de l'arène
        if abs(z - pm[1]) < 20.0:                                             # passage libre devant le portique Minerva Oil
            continue
        put('camions du paddock', xs, z, ang(-f0[0], -f0[1]), 'semi.jm', 'semi_%s.png' % team)

    gate_model = ' '.join([ref('start_gate_frame.jm'), ref('start_gate_frame.png'), '@startgate.shp'])
    info = dict(objets=cnt, total=len(st), amv_pied_ft=amv, arche=dict(crete_ft=round(ha, 2), sol_pieds_ft=[round(v, 2) for v in feet],
                                                                   libre_sous_poutre_ft=round(A['clear'] - ha, 1)),
                finish=dict(crete_ft=round(hF, 2)), logos_redessines=__import__('hab_kit').LOGOS_REDESSINES)
    return st, gate_model, info
