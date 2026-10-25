"""v12 : pose les objets USLAND (props_usland.py) dans les 3 pistes, à la place des objets JGSX, 1 pour 1.
  - semi JGSX (semi_1)          -> hospitality USLAND (même place, même axe ; décalé de 13 ft vers l'extérieur du grillage)
                                   + stand de bannières centré sur le tapis rouge : les 4 dans le même ordre de chaque côté,
                                   + 2 bannières en retour à chaque bout (props_place.stand_banners)
  - vans JGSX (transit) x3      -> pick-ups USLAND (même place, même angle) + un vélo sur home-trainer dans chaque benne
  - grilles JGSX (gate01)       -> grilles USLAND (lignes startinggate de timing_gates : le jeu les fait tomber)
  - arche FINISH sur la porte d'arrivée, portique au-dessus de la rangée de grilles, une grate par grille
  - commissaire d'arrivée déplacé à côté de l'arche (jamais sur un poteau)
  - copie assets/props/* dans tracks/<SX1>/statue/ (référencés @USLAND2026SX1/statue/...)
v12b : citerne -> pick-up USLAND (+ vélo) ; tente -> tente USLAND ; Matrix, bulldozer, bobcat retirés ; camion-citerne gardé
      + autocollant icône U sur les deux flancs (watertruck_u, sticker_usland.py, même position / angle).
Relançable : retire d'abord les objets USLAND déjà posés. Lancé par make_all.sh juste après dress_sx.py ; marche aussi seul
(sans les archives de référence) sur les pistes déjà construites :  python3 scripts/place_props.py"""
import os, sys, json, shutil, re
ROOT = os.environ.get('MXSIM_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
import numpy as np
from names import FOLDERS as F
import props_place as PP
import props_usland as PU

OUT = ROOT + '/tracks'; P = '@' + F['SX1']; A = f'{OUT}/{F["SX1"]}'
OURS = ('finish_arch_SX1', 'finish_arch_SX2', 'finish_arch_SX3', 'hospitality_usland', 'pickup_usland', 'bike_trainer', 'banner', 'finish_arch', 'start_gantry', 'start_grate', 'tent_usland', 'watertruck_u')
REPLACED = ('semi_1', 'transit', 'watertank', 'matrixa2', 'dozer', 'bobcat', 'ezup')   # watertruck kept (asked)

def line(x, y, z, a, model, tex):
    a = float((a + np.pi) % (2 * np.pi) - np.pi)        # v13b: yaw in [-pi, pi) (bikes at a + pi = 4.7 / 6.27 sat crosswise in some pickups)
    return f'[{x:.6f} {y:.6f} {z:.6f}] {a:.6f} {P}/statue/{model}.jm {P}/statue/{tex}.png null'

def parse(l):
    nums = [float(t) for t in re.findall(r'-?\d+\.?\d*(?:e-?\d+)?', l.split('@')[0])]
    return nums[0], nums[1], nums[2], nums[3], l.split()[4].split('/')[-1][:-3]

def outward(x, z, rects):
    """unit vector from the nearest fence side towards the outside (the paddock strip)."""
    best = None
    for x0, x1, z0, z1 in rects:
        for d, o in ((abs(z - z0), (0.0, -1.0)), (abs(z - z1), (0.0, 1.0)), (abs(x - x0), (-1.0, 0.0)), (abs(x - x1), (1.0, 0.0))):
            if best is None or d < best[0]: best = (d, np.array(o))
    return best[1]

def main():
    T = PP.load_terrain()
    rep = json.load(open(f'{ROOT}/build/dress_report.json')); rects = [rep[k]['fence'] for k in ('SX1', 'SX2', 'SX3')]
    # base = the statues written by dress_sx.py (JGSX objects). A fresh dress_sx output (none of our objects in it) becomes the
    # saved base; on a re-run (our objects already there) the saved base is used, so nothing is lost (v12b)
    BASE = f'{ROOT}/build/statues_jgsx_base.txt'; cur = open(f'{A}/statues').read()
    if not any(f'/{m}.jm' in cur for m in OURS):
        open(BASE, 'w', newline='\n').write(cur)
    elif not os.path.exists(BASE):
        raise SystemExit('statues already dressed and no build/statues_jgsx_base.txt: run dress_sx.py first')
    stat = open(BASE).read().split('\n')
    keep, new = [], []
    for l in stat:
        if not l.strip(): continue
        m = l.split()[4].split('/')[-1][:-3] if len(l.split()) > 4 else ''
        if m in OURS: continue                                          # ours from a previous run
        if m == 'semi_1':
            x, y, z, a, _ = parse(l); o = outward(x, z, rects); c = np.array([x, z]) + o * 13.0
            # local +x (entrance module, stairs, carpet) -> world (cos a, -sin a) (statue convention, v12b):
            # turn the trailer round if needed so the entrance faces the outside of the fence
            if np.dot(np.array([np.cos(a), -np.sin(a)]), o) < 0: a += np.pi
            new.append(line(c[0], 0.0, c[1], a, 'hospitality_usland', 'hospitality_usland'))
            for bx, bz, ba, nm in PP.stand_banners(c, a):            # v13b: stand centred on the red carpet, with returns
                new.append(line(bx, 0.0, bz, ba, 'banner', 'banner_' + nm.lower()))
            continue
        if m == 'ezup':                                            # v12b: JGSX tent -> USLAND tent (USLAND / RBT / FOX)
            x, y, z, a, _ = parse(l); new.append(line(x, 0.0, z, a, 'tent_usland', 'tent_usland')); continue
        if m == 'matrixa2': continue                               # v12b: the car under the tent: removed (a pickup does not fit)
        if m == 'watertank':                                       # v12b: JGSX tank -> USLAND pickup (+ bike); the water truck stays
            x, y, z, a, _ = parse(l)
            new.append(line(x, 0.0, z, a, 'pickup_usland', 'pickup_usland'))
            b = PP.bike_in_pickup(x, 0.0, z, a); new.append(line(b['x'], b['y'], b['z'], b['a'], 'bike_trainer', 'bike_trainer'))
            continue
        if m == 'watertruck':                                      # v12b: JGSX water truck kept + our U sticker (same pose)
            x, y, z, a, _ = parse(l); keep.append(l); new.append(line(x, y, z, a, 'watertruck_u', 'watertruck_u')); continue
        if m in ('dozer', 'bobcat'): continue                      # v12b: third-party, removed
        if m == 'transit':
            x, y, z, a, _ = parse(l)
            new.append(line(x, 0.0, z, a, 'pickup_usland', 'pickup_usland'))
            b = PP.bike_in_pickup(x, 0.0, z, a); new.append(line(b['x'], b['y'], b['z'], b['a'], 'bike_trainer', 'bike_trainer'))
            continue
        keep.append(l)
    for key in ('SX1', 'SX2', 'SX3'):
        Ac = PP.centred_arch(key, T); new.append(line(Ac['x'], Ac['y'], Ac['z'], Ac['a'], Ac['model'], 'finish_arch'))   # v13b: origin in the middle
        g = PP.gantry_pose(key, T); new.append(line(g['x'], g['y'], g['z'], g['a'], 'start_gantry', 'start_gantry'))
        for x, y, z, a in PP.grate_poses(key, T): new.append(line(x, y, z, a, 'start_grate', 'start_grate'))
    out = '\n'.join(keep + new) + '\n'
    for key, folder in F.items():
        d = f'{OUT}/{folder}'
        open(f'{d}/statues', 'w', newline='\n').write(out)
        # start gates: our gate model on every startinggate line (the game raises / drops it like gate01)
        tg = open(f'{d}/timing_gates').read().split('\n'); sec = None; o2 = []
        for l in tg:
            if l.endswith(':'): sec = l
            elif sec == 'startinggate:' and l.startswith('['):
                l = ' '.join(l.split()[:4]) + f' {P}/statue/start_gate.jm {P}/statue/start_gate.png @startgate.shp'
            o2.append(l)
        open(f'{d}/timing_gates', 'w', newline='\n').write('\n'.join(o2))
        # finish flagger next to the arch (21.5 ft from the lane, beside a pillar, never on it)
        fl = PP.finish_flagger(key)
        L = open(f'{d}/flaggers').read().split('\n'); idx = [i for i, l in enumerate(L) if l.startswith('[') and not l.startswith('[0.0')]
        L[idx[2]] = f'[{fl[0]:.6f} 0.000 {fl[1]:.6f}]'; open(f'{d}/flaggers', 'w', newline='\n').write('\n'.join(L))
    os.makedirs(f'{A}/statue', exist_ok=True)
    for f in os.listdir(f'{ROOT}/assets/props'): shutil.copy(f'{ROOT}/assets/props/{f}', f'{A}/statue/{f}')
    n = {m: sum(1 for l in new if f'/{m}.jm' in l) for m in OURS}
    print('objets USLAND posés :', n, '| statues au total :', len(keep) + len(new))

if __name__ == '__main__':
    main()
