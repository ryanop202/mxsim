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
import hab_objets2 as HO2          # v9 : objets refaits (tuffs pleins, ballots bâchés, bâche AMV sur le profil, arches fermées, camions)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SGM = os.path.join(ROOT, "tracks", "USLAND2026SaintGeorgesbyBazo")
PROPS = os.path.join(ROOT, "assets", "props")
SUB = "statue/paris"
LANE_SKIN = {'L5': 'honda', 'L3': 'amv', 'L2': 'seong', 'L1': 'monster', 'LR': 'motul', 'L6': 'yamaha', 'LD': 'monster'}
# v9 (Ryan : « les blocs à l'extérieur des virages, il y en a beaucoup trop ») : murs seulement aux 5 grands virages
TURN_SKIN = {'T1 ': ('honda', 'noir'), 'T_C ': ('five', 'noir'), 'T_E ': ('seong', 'venum'), 'T_TR': ('seong', 'venum'),
             'T_D': ('motoverte', None)}
MUR_SPAN = 0.7                     # part du virage couverte par les ballots (au milieu)
PADDOCK = ['ktm', 'kawasaki', 'yamaha', 'monster', 'honda', 'honda', 'blanc', 'triumph', 'ducati', 'yamaha', 'kawasaki']


PYLON_T5B = []
LATE = []          # lignes de statues qui sortent du sol ~20 s après le départ (h)


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
    HO2.tuff_arc(D); HO.boudins(D); HO2.mur(D); HO.filet(D); HO2.minerva(D); HO.depart(D); HO.canette(D); HO2.semi(D)
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
    # v9 (Ryan : « les trucs FLY sur le côté des whoops ne sont pas alignés, ils bougent, pas droits ») : une ligne DROITE de
    # boudins de 18 ft BOUT À BOUT de chaque côté, sur le sol plat juste après le pied des whoops (même distance tout du long),
    # à la hauteur du sol (y = 0) - comme le long boudin de la capture de Ryan / photo 9
    pts_r = []
    for gi, (ua, ub) in whoops_rng.items():
        g = path.segs[gi]; c, s_ = np.cos(g['t']), np.sin(g['t']); nrm = np.array([-s_, c]); dl = np.array([c, s_])
        n_b = max(1, int(np.ceil((ub - ua) / 18.0))); u_s = (ua + ub) / 2 - n_b * 9.0
        for side in (-1, 1):
            vv = np.arange(10.0, 30.0, 0.25); foot = 10.0
            for u in np.linspace(u_s, u_s + 18.0 * n_b, 40):
                q0 = np.array([g['x0'] + u * c, g['z0'] + u * s_])
                hv = np.array([hgt(*(q0 + nrm * side * v)) for v in vv]); hi = np.nonzero(hv > 0.05)[0]
                if len(hi):
                    foot = max(foot, float(vv[hi[-1]]))
            off = foot + 1.2 + 0.4
            for k in range(n_b):
                u = u_s + 9.0 + 18.0 * k
                p = np.array([g['x0'] + u * c, g['z0'] + u * s_]) + nrm * side * off
                put('boudins FLY Racing (whoops)', p[0], p[1], ang(*(-nrm * side)), 'boudin_logo3.jm', 'boudin3_fly.png', 'boudin_logo3.shp')
                pts_r += [p + dl * q for q in (-6.0, 0.0, 6.0)]

    # ---- 2. tuff blocks (demi-tonneaux) comme ZION 2025 (relevé sur ses 322 blocs, Ryan : « regarde ZION comment ils les placent ») :
    #      une rangée continue au bord de CHAQUE couloir (14,5 ft de l'axe = bord du dessus des sauts), un bloc tous les ~12,4 ft,
    #      sur le plat comme sur les bosses ; le long du bloc DANS le sens du couloir (+z local en travers, comme ZION) ;
    #      pas sur les whoops (boudins FLY), pas sur la grosse butte, pas sur un autre couloir.
    for gi, g in enumerate(path.segs):
        if g['kind'] != 'S' or g['L'] < 40:
            continue
        skin = next((v for k, v in LANE_SKIN.items() if g['tag'].startswith(k)), None)
        if skin is None or g['tag'].startswith('LD'):
            continue
        c, s_ = np.cos(g['t']), np.sin(g['t']); nrm = np.array([-s_, c])
        n_ = max(2, int(round((g['L'] - 12.0) / 12.4)) + 1)
        for u in np.linspace(6.0, g['L'] - 6.0, n_):
            if gi in whoops_rng and whoops_rng[gi][0] <= u <= whoops_rng[gi][1]:
                continue
            for side in (-1, 1):
                p = np.array([g['x0'] + u * c, g['z0'] + u * s_]) + nrm * side * 14.5
                if hgt(*p) > 6.0 or any(np.hypot(*(p - q)) < 7.0 for q in pts_r):
                    continue
                near = [q for q in tree.query_ball_point(p, 13.0) if abs(smp['s'][q] - (g['s0'] + u)) > 40]
                if near:                                                             # un autre couloir passe là
                    continue
                put('tuffs ' + skin, p[0], p[1], ang(*(nrm * side)), 'tuff_arc.jm', 'tuff_arc_%s.png' % skin, 'tuff_arc.shp')

    # ---- 3. virages : mur bâché + bandeau du sponsor au dos du berm, filet derrière les grands virages, poteau rond à l'intérieur
    skins_py = ['pylone_monster.png', 'pylone_honda.png', 'pylone_venum.png']; n_py = 0
    for g in path.segs:
        if g['kind'] != 'T':
            continue
        mid = turn_mid_angle(g)
        if abs(g['ang']) >= 90:
            r = max(1.5, g['r'] - 15.2 - 1.5); x, z = g['cx'] + r * np.cos(mid), g['cz'] + r * np.sin(mid)
            if g['tag'].startswith('T_L5b'):                                  # v8 (croix de Ryan) : pas de poteau ici
                PYLON_T5B[:] = [x, z]
                continue
            if libre((x, z), lap=10.0, extra=1.0):
                put('poteaux ronds', x, z, ang(np.cos(mid), np.sin(mid)), 'pylon_round.jm', skins_py[n_py % 3], 'pylon_round.shp'); n_py += 1
        sk = next((v for k, v in TURN_SKIN.items() if g['tag'].startswith(k)), None)
        if not g.get('berm') or sk is None:
            continue
        gb = g
        if g.get('berm_from'):                                                # v9 : 180 L3 -> L2, berm sur la 2e moitié seulement
            a_ = np.radians(g['ang']) * g['berm_from']
            gb = dict(g, t0=g['t0'] - a_, ang=g['ang'] * (1 - g['berm_from'])); mid = turn_mid_angle(gb)
        rr = np.arange(g['r'], g['r'] + 60, 0.5)
        hh = np.array([hgt(g['cx'] + r * np.cos(mid), g['cz'] + r * np.sin(mid)) for r in rr])
        crest_r = float(rr[int(np.argmax(hh))])                                  # haut du berm
        span = np.radians(abs(gb['ang'])) * 0.5 + np.radians(6)
        # v9 : filet sur le sol plat juste derrière le berm (droit, pas de travers sur la pente)
        flat_r = float(next((r for r, h_ in zip(rr, hh) if r > crest_r and h_ < 0.1), crest_r + 8.0))
        # (c) photos (20.png) : blocs durs gris un peu DANS le virage (bord extérieur du couloir), mur à sponsor EN HAUT du berm,
        #     filet juste derrière. Les murs suivent le haut du berm (pas sur la face).
        # v7 (Ryan, aperçu : « c'est quoi ça dans le virage, ça va pas », « le filet est pas aussi long ») : plus de blocs gris ;
        # le filet ne couvre que le milieu du virage (60 % de la longueur du mur)
        # v9 (Ryan : « pas réalistes, tout carrés, beaucoup trop, ils flottent en l'air, mal posés ») : ballots ronds bâchés
        # (photo 12) sur 70 % du virage, abaissés à la hauteur la plus basse sous leur emprise (jupe de 3 ft) -> jamais en l'air
        for kind, rad, model, tex, shp_, step, k_span in (('murs ' + sk[0] + ' (haut du berm)', crest_r + 1.0, 'mur.jm', 'mur_%s.png' % sk[0], 'mur.shp', 8.0, MUR_SPAN),
                                                          ('filets', flat_r + 2.0, 'filet.jm', 'filet_%s.png' % sk[1], None, 8.0, 0.6)):
            if tex.endswith('None.png'):
                continue
            n = max(2, int(round(2 * span * k_span * rad / step)))
            for a in (mid + (np.arange(n) - (n - 1) / 2) * (step / rad)):
                x, z = g['cx'] + rad * np.cos(a), g['cz'] + rad * np.sin(a)
                near = [q for q in tree.query_ball_point((x, z), 12.0) if abs(smp['s'][q] - (g['s0'] + g['L'] / 2)) > g['L'] / 2 + 30]
                if near or not libre((x, z), lap=12.0, extra=1.0):
                    continue
                yaw = ang(-np.cos(a), -np.sin(a))
                y_ = 0.0
                if model == 'mur.jm':                                         # le point le plus bas sous l'emprise (8 x 4,2 ft)
                    t_ = np.array([-np.sin(a), np.cos(a)]); n_ = np.array([np.cos(a), np.sin(a)]); h0 = hgt(x, z)
                    y_ = min(hgt(*(np.array([x, z]) + t_ * du + n_ * dv)) for du in (-4, -2, 0, 2, 4) for dv in (-2.1, 0, 2.1)) - h0
                put(kind, x, z, yaw, model, tex, shp_, y=y_)

    # ---- 4. arrivée : panneau FINISH suspendu au-dessus de la ligne, rampe acier + coins Honda sur l'appel, cage du drapeau
    sF, _ = finish_s_fn
    i = int(np.argmin(np.abs(smp['s'] - sF))); fx, fz, th = smp['x'][i], smp['z'][i], smp['th'][i]
    d = np.array([np.cos(th), np.sin(th)]); hF = hgt(fx, fz)
    HO.finish(D, drop=hF); put('panneau FINISH suspendu', fx, fz, ang(*d), 'finish.jm', 'finish.png')
    # (Ryan, v6 : « saut d'arrivée enlève ce truc ») : plus de rampe acier + coins Honda sur l'appel
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
    it = [i_ for i_ in combos[name]['items'] if 'butte' in i_[0]][0]
    bp = prof[int(it[1] / 0.1):int(it[2] / 0.1)]; Hb = float(bp.max())
    top = np.nonzero(bp >= Hb - 0.4)[0]; ut0, ut1 = top[0] * 0.1, top[-1] * 0.1        # dessus de la réception
    nz = np.nonzero(bp > 0.3)[0]; uf0, uf1 = nz[0] * 0.1, nz[-1] * 0.1                  # pieds
    half_c = (ut1 - ut0) / 2; w_up, w_dn = ut0 - uf0, uf1 - ut1
    uc = u0 + it[1] + (ut0 + ut1) / 2
    c, s_ = np.cos(g3['t']), np.sin(g3['t']); dl = np.array([c, s_]); nrm = np.array([-s_, c]); pc = np.array([g3['x0'] + uc * c, g3['z0'] + uc * s_])
    # v9 (Ryan : « les plaques sur le bord du saut du milieu, ça va pas, elles sont buggées ») : bâche dessinée sur le bord RÉEL
    # du saut (hauteur relevée dans le terrain à 2 ft à l'intérieur du pied), posée verticale au pied, des deux côtés
    amv = {}
    for sd in (-1, 1):
        vv = np.arange(8.0, 60.0, 0.25); hv = np.array([hgt(*(pc + nrm * sd * v)) for v in vv])
        ve = float(vv[np.nonzero(hv >= 0.97 * hv.max())[0][-1]])             # bord du dessus (flancs presque verticaux)
        vf = ve + 1.3; p = pc + nrm * sd * vf; y_b = -hgt(*p)                  # bâche contre le flanc ; y : bas de la bâche au sol
        out_ = nrm * sd; xloc = np.array([out_[1], -out_[0]]); sg = float(np.sign(np.dot(xloc, dl)))
        us = np.arange(u0 + it[1] + uf0 - 1.0, u0 + it[1] + uf1 + 1.0, 0.5)
        tops = np.array([max(hgt(*(np.array([g3['x0'] + u * c, g3['z0'] + u * s_]) + nrm * sd * ve)), 0.0) for u in us])
        xs_ = (us - uc) * sg; o_ = np.argsort(xs_)
        nm_ = 'amv_bache_%s' % ('p' if sd > 0 else 'm')
        HO2.amv_bache(D, nm_, xs_[o_], tops[o_])
        put('bâche AMV (côtés de la réception)', p[0], p[1], ang(*out_), nm_ + '.jm', nm_ + '.png', y=y_b); amv[sd] = round(vf, 1)
    ramp_jm = os.path.join(ROOT, "assets", "fmx_ramp_user", LP.FMX_MODEL['model'] + ".jm")
    HO.fmx_jupe(D, ramp_jm)
    for r in LP.fmx_ramps(path):
        (x, z), h = r['lip'], r['heading']; dd = np.array([np.cos(h), np.sin(h)])
        put('habillage Venum des tremplins', x - dd[0] * LP.FMX_MODEL['model_len'], z - dd[1] * LP.FMX_MODEL['model_len'], ang(-dd[0], -dd[1]),
            'fmx_jupe.jm', 'fmx_jupe.png')

    # ---- 6. arche 50 Factory sur la PREMIÈRE bosse du couloir de la tribune Sud (L6)
    g6 = next(g for g in path.segs if g['kind'] == 'S' and g['tag'].startswith('L6'))
    prof, u0, name = g6['sections'][0]; it = combos[name]['items'][0]          # (e) première bosse
    i0, i1 = int(it[1] / 0.1), int(it[2] / 0.1); ua = u0 + it[1] + float(np.argmax(prof[i0:i1])) * 0.1
    c, s_ = np.cos(g6['t']), np.sin(g6['t']); pa = np.array([g6['x0'] + ua * c, g6['z0'] + ua * s_]); ha = hgt(*pa)
    A = HO2.arche_50(D, drop=ha, half=23.5, hleg=24.5); put('arche 50 Factory', pa[0], pa[1], ang(c, s_), 'arche_50.jm', 'arche_50.png')
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
    # (g) Ryan : « ça va pas du tout » -> plus de boudins Motul le long du couloir de départ
    xw = (path.lanes['xLR'] + 15.2 + path.lanes['xT5'] - 15.2) / 2
    for z in np.arange(path.lanes['zL5'] + 30.0, path.lanes['zLD'] + 52.0, 8.05):
        if libre((xw, z), lap=17.0):
            put('murs automoto', xw, z, ang(1.0, 0.0), 'mur.jm', 'mur_automoto.png', 'mur.shp')

    # ---- 7b. v7 (Ryan : « le départ ça va pas du tout, enlève tout ça, je veux juste la sortie du virage qui indique où ça va,
    #      en diagonale ») : 8 tuffs en diagonale côté extérieur de la sortie du 180 (T_L5b -> LD), de 36 à 16 ft de l'axe sur 45 ft.
    #      Ils sont dans le passage du départ (le départ tourne là) : enterrés au départ, ils sortent 20 s après la chute de la grille.
    gLD = next(g for g in path.segs if g['kind'] == 'S' and g['tag'].startswith('LD'))
    c, s_ = np.cos(gLD['t']), np.sin(gLD['t']); nrm = np.array([-s_, c]); late = []
    # v8 (Ryan : croix sur la diagonale, double trait du bout du mur Automoto jusqu'au poteau) : ligne de tuffs Monster serrés
    #      (4 ft) du bout Nord du mur Automoto jusqu'à la place du poteau de T_L5b ; dans le passage du départ -> sort après le départ
    # v8b (capture de Ryan) : sur ce trait, un long boudin noir FLY / RBT / SX TOUR (boudins de 18 ft bout à bout, collision)
    # v9b (capture en jeu de Ryan, « place-le comme ça », trait bleu) : le long boudin noir n'est plus du bout du mur Automoto
    #      au poteau ; c'est une barre de 2 boudins (36 ft) DANS le U (L5 -> T_L5a -> T_L5b -> ligne de départ), du sommet du U
    #      vers la ligne de départ, penchée comme le trait (relevé sur la capture : direction (38, 21)). Reculée jusqu'à être à
    #      >= 16 ft de la ligne du tour et >= 2,5 ft du couloir de départ : elle reste sortie tout le temps (plus d'apparition tardive).
    ln_ = path.lanes; dd_ = np.array([38.0, 21.1]); dd_ /= np.linalg.norm(dd_)
    top_ = np.array([ln_['xT5'] + LP.RB + 2.5, (ln_['zL5'] + ln_['zLD']) / 2 - 5.4])

    def _ok(t_):
        for q_ in np.linspace(t_, t_ + dd_ * 36.0, 13):
            d_, j_ = rtree.query(q_)
            if tree.query(q_)[0] < 16.0 or d_ < rw[j_] / 2 + 2.5:
                return False
        return True
    k_ = 0
    while not _ok(top_) and k_ < 40:
        top_ = top_ + np.array([-0.25 * dd_[1], 0.25 * dd_[0]]) * -1.0 - dd_ * 0.25; k_ += 1   # vers le sommet du U, loin du départ
    on_start = not _ok(top_)
    for k_ in range(2):
        p = top_ + dd_ * (9.0 + 18.0 * k_)
        if on_start:
            late.append(len(st))
        put('long boudin noir FLY / RBT / SX TOUR (dans le U)', p[0], p[1], ang(dd_[1], -dd_[0]), 'boudin_logo3.jm', 'boudin3_noir.png', 'boudin_logo3.shp')
    LATE[:] = [st[k] for k in late]

    # ---- 8. paddock : camions entre le départ et le mur de scène (cabine côté mur, auvent sur le côté)
    from arena import dims as _dims                                           # (i) nez du tracteur à 3 ft du mur de scène
    x_wall = LP.arena_to_mx(_dims.X_STAGE, 0.0)[0]
    xs = x_wall - 3.0 - 8.2                                                   # origine du modèle = avant de la remorque
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
