"""v28-v30 de Bazo (branche usland-paris-by-bazo, reprise en v35 sans le terrain) - v28 (review en jeu de la v27d, 2026-11-26) : objets en plus, posés par build_zion.deco_v21 (fin du fichier statues).

- bottes de paille aux endroits montrés sur les captures (virages : entrée, intérieur, sortie ; abords des sauts) ;
- boudins aux couleurs des sponsors qui SORTENT DU SOL 20 s après la chute de la grille (« de 0 à 20 s il n'y a rien, à 20 s ils
  apparaissent ») : le long de la ligne de départ (des 2 côtés) et un boudin Automoto au bout du saut AMV, vers le virage T_D ;
  nofrills.js les déplace (mx.move_statue), comme le long tuff block de la version USLAND et les boudins de Saint-Thibéry ;
- poteau de virage (bâton rouge sur socle, on tombe si on le touche ; forme créée, façon poteaux de RF) à l'intérieur du 2e virage
  après l'arrivée ;
- bâche noire derrière les grilles de départ (celle de Saint-Georges, bannière passée en noir, sans sponsor).
Repère des bottes : s le long du tour, v > 0 = droite du sens de course (comme build_paris)."""
import os
import shutil
import numpy as np
from PIL import Image, ImageDraw

import hab_kit as K
from hab_kit import Mesh, fit

LATE_S = 20.0
BOUDIN_KEYS = ['mxsim', 'five', 'honda', 'yamaha', 'automoto', 'motoverte', 'minerva', 'amv', 'milwaukee', '50factory']


class Placer:
    """positions sur le tour : seg (début du tag) + u (ft depuis le début du segment, le long de la trajectoire) + v (ft, droite > 0)."""

    def __init__(self, path, Hf):
        self.path, self.Hf = path, Hf
        sm = path.samples(0.25); self.s, self.x, self.z = sm['s'], sm['x'], sm['z']; self.th = np.unwrap(sm['th'])

    def seg(self, tag):
        return next(g for g in self.path.segs if g['tag'].startswith(tag))

    def at(self, s, v):
        x, z, th = (np.interp(s, self.s, a) for a in (self.x, self.z, self.th))
        return np.array([x - v * np.sin(th), z + v * np.cos(th)]), float(th)

    def flat_s(self, s, v, slide, half=(1.9, 0.8)):
        """abscisse la plus plate (écart de hauteur sous l'objet) dans [s - slide, s + slide]."""
        best = None
        for s_ in np.arange(s - slide, s + slide + 1e-6, 0.25):
            P, th = self.at(s_, v); t = np.array([np.cos(th), np.sin(th)]); n = np.array([-t[1], t[0]])
            Q = [P + t * a + n * b for a in (-half[0], 0, half[0]) for b in (-half[1], half[1])]
            h = [float(np.ravel(self.Hf(q[0], q[1]))[0]) for q in Q]; r = max(h) - min(h)
            if best is None or r < best[0] - 1e-3 or (abs(r - best[0]) <= 1e-3 and abs(s_ - s) < abs(best[1] - s)):
                best = (r, s_)
        return best[1], best[0]


def bales(P, spec, slide=1.5):
    """spec : [(tag, u, v, clé)] -> [(x, z, yaw, clé, pente)] ; u < 0 ou > L : déborde sur le segment voisin (abscisse du tour)."""
    out = []
    for tag, u, v, key in spec:
        g = P.seg(tag); s, r = P.flat_s(g['s0'] + u, v, slide); Q, th = P.at(s, v)
        out.append((float(Q[0]), float(Q[1]), float(np.arctan2(-np.sin(th), np.cos(th))), key, round(r, 2)))
    return out


def boudin_skin(sd, key, props):
    """peau du boudin de 18 ft (modèle boudin_logo3 de Saint-Georges) : fond du sponsor + son logo dans les 2 bandes (une par côté),
    même mise en page que la peau FLY (boudin_flyrouge3.png) ; le bas de l'image (bouts) gardé."""
    name = 'boudin_%s3.png' % key; p = os.path.join(sd, name)
    if os.path.exists(p):
        return name
    import sponsors as SP
    bg, lg = SP.panel(key)
    im = Image.open(os.path.join(props, 'boudin_flyrouge3.png')).convert('RGB').copy(); W, H = im.size; hb = int(H * 0.915)
    im.paste(Image.new('RGB', (W, hb), bg), (0, 0))
    if lg is not None:
        for yc in (0.245, 0.705):
            fit(im, lg, (int(0.20 * W), int((yc - 0.115) * H), int(0.80 * W), int((yc + 0.115) * H)), 0.0)
    im.save(p, optimize=True)
    return name


def boudins_line(P, tag, u0, u1, v, keys, step=18.0):
    """boudins de 18 ft bout à bout le long du tour entre u0 et u1 (centres), face à la piste ; -> [(x, z, yaw, clé)]."""
    g = P.seg(tag); out = []; n = max(1, int(round((u1 - u0) / step)) + 1)
    for k, u in enumerate(np.linspace(u0, u1, n)):
        Q, th = P.at(g['s0'] + u, v); f = -np.array([-np.sin(th), np.cos(th)]) * np.sign(v)
        out.append((float(Q[0]), float(Q[1]), float(np.arctan2(f[0], f[1])), keys[k % len(keys)]))
    return out


def corner_stick(sd):
    """poteau de virage : socle rond gris foncé (r 1,1 ft, 0,45 ft) + bâton rouge (r 0,16 ft, 5 ft) à 2 bandes blanches ; collision
    dure (boules de 0,35 ft le long du bâton, réglages des murs : on tombe si on le touche). Forme créée."""
    # v29 (« le piqué rouge, mets-le bien plus haut, et pas de truc blanc dessus ») : bâton tout rouge de 8 ft
    W = 64; im = Image.new('RGB', (W, W), (48, 48, 52)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 31, W - 1], fill=(206, 24, 30))
    im.save(os.path.join(sd, 'poteau_virage.png'))
    m = Mesh(); red = K.R((0, 0, 32, W), W, W); base = K.R((40, 40, 60, 60), W, W)
    m.tube((0, 0.0, 0), (0, 0.45, 0), 1.1, base, 16)
    m.tube((0, 0.45, 0), (0, 8.45, 0), 0.17, red, 10)
    m.write(os.path.join(sd, 'poteau_virage.jm'))
    K.shp(os.path.join(sd, 'poteau_virage.shp'), [(0, y, 0) for y in np.arange(0.9, 8.3, 0.55)], 0.35, par=(1.5, 1000, 200))
    return 'poteau_virage.jm', 'poteau_virage.png', 'poteau_virage.shp'


def start_tarp_black(sd, sgm_statue):
    """bâche du départ de Saint-Georges (90 ft le long de x local, origine au sol au milieu, face imprimée = -z local) : bannière
    passée en noir uni (« sans les sponsors, juste du noir »), filet noir gardé."""
    shutil.copy(os.path.join(sgm_statue, 'start_tarp.jm'), os.path.join(sd, 'start_tarp_noir.jm'))
    im = Image.open(os.path.join(sgm_statue, 'start_tarp.png')).convert('RGBA'); a = np.asarray(im).copy()
    a[:1302, :, :3] = (16, 16, 18); a[:1302, :, 3] = 255
    Image.fromarray(a, 'RGBA').save(os.path.join(sd, 'start_tarp_noir.png'))
    return 'start_tarp_noir.jm', 'start_tarp_noir.png', None


def nofrills_js(rows):
    """script : statues de rows ([rang, x, z, yaw]) enterrées (y -200) jusqu'à LATE_S s après la chute de la grille ; sans chute
    de grille (entraînement libre) elles sont là. Texte ASCII."""
    return '\n'.join([
        '/*', 'USLAND Paris v28 - boudins sponsors de la ligne de depart et boudin Automoto du virage apres le saut AMV :',
        'invisibles de 0 a 20 s, ils sortent du sol 20 s apres la chute de la grille. Texte ASCII expres.', '*/', '',
        'var g_lt = [' + ', '.join('[%d, %.3f, %.3f, %.6f]' % tuple(r) for r in rows) + '];', 'var LATE_AFTER = %.1f;' % LATE_S,
        'var g_lt_shown = -1;', 'var g_lt_t = -1.0;', '',
        'function ltSet(show) {', '    var i, s;', '    for (i = 0; i < g_lt.length; i++) {', '        s = g_lt[i];',
        '        mx.move_statue(s[0], s[1], show ? 0.0 : -200.0, s[2], s[3]);', '    }', '    g_lt_shown = show;', '}', '',
        'function lateTuff(seconds) {', '    var d = mx.get_gate_drop_time();', '    var show = (d < 0 || mx.seconds >= d + LATE_AFTER);',
        '    if (show != g_lt_shown || mx.seconds < g_lt_t || mx.seconds - g_lt_t > 1.0) {', '        ltSet(show);',
        '        g_lt_t = mx.seconds;', '    }', '    if (lateTuffPrev)', '        lateTuffPrev(seconds);', '}', '',
        'var lateTuffPrev = mx.frame_handler;', 'mx.frame_handler = lateTuff;', ''])


def write_late(OUT, late_lines):
    """rangs des statues « tardives » dans statues (et le même rang dans chaque variante), puis nofrills.js."""
    files = ["statues"] + ["variants/" + v for v in os.listdir(os.path.join(OUT, "variants")) if v.startswith("statues")]
    idx = None
    for f in files:
        L = [l for l in open(os.path.join(OUT, f)).read().split("\n") if l.strip()]
        pos = {l: i for i, l in enumerate(L)}
        k = [pos[l] for l in late_lines]
        assert len(set(k)) == len(late_lines), ("boudins tardifs : lignes en double", f)
        assert idx is None or k == idx, ("rangs différents entre statues et variante", f)
        idx = k
    rows = []
    for i, l in zip(idx, late_lines):
        v_ = l.split(']')[0][1:].split(); rows.append((i, float(v_[0]), float(v_[2]), float(l.split(']')[1].split()[0])))
    open(os.path.join(OUT, "nofrills.js"), "w", newline="\n", encoding="ascii").write(nofrills_js(rows))
    return len(rows)


def booth(sd, wp, key='mxsim', X=2.25, Z=2.0, Hc=4.5):
    """v29 (dessin de l'utilisateur sur la capture : « une cabane noire avec le logo ; dedans juste un socle qu'on voit pas, pour que le
    monsieur dépasse avec son drapeau ») : guérite fermée 4,5 x 4 ft, murs 4,5 ft, logo du sponsor sur les 4 faces (lu à l'endroit de
    l'extérieur), dedans noir ; le signaleur (fichier flaggers) a les pieds 1,2 ft au-dessus du socle : il dépasse à partir de la taille.
    Repère local : +z = vers la piste ; wp(x, y, z) -> point monde (relatif à l'origine)."""
    import deco_v22 as D22
    import sponsors as SP
    bg, lg = SP.panel(key); Wt, Ht = 1024, 512; im = Image.new('RGB', (Wt, Ht), (14, 14, 15)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 511, 511], fill=bg)
    if lg is not None:
        fit(im, lg, (24, 150, 488, 400), 0.04)
    d.rectangle([600, 0, 700, 100], fill=(14, 14, 15))
    im = K.grain(im, 1.2); im.save(os.path.join(sd, 'guerite_%s.png' % key))
    pan, blk = K.R((0, 0, 512, 512), Wt, Ht), K.R((600, 0, 700, 100), Wt, Ht)
    m = Mesh(); up = np.array([0.0, 1.0, 0.0])
    nw = lambda v: tuple(np.subtract(wp(*v), wp(0, 0, 0)))
    for n, half, dist in (((0, 0, 1), X, Z), ((0, 0, -1), X, Z), ((1, 0, 0), Z, X), ((-1, 0, 0), Z, X)):
        n_ = np.array(n, float); r = np.cross(-n_, up); c = n_ * dist
        P = [c - r * half, c + r * half, c + r * half + up * Hc, c - r * half + up * Hc]          # bas gauche, bas droite, haut droite, haut gauche vus de dehors
        uv = [(pan[0], pan[1]), (pan[2], pan[1]), (pan[2], pan[3]), (pan[0], pan[3])]
        D22._face(m, [wp(*p) for p in P], uv, [nw(n)] * 4)
        D22._face(m, [wp(*p) for p in P[::-1]], [(blk[0], blk[1])] * 4, [nw(-n_)] * 4)       # dedans noir
    m.write(os.path.join(sd, 'guerite_%s.jm' % key), D22.MAT_MAT)
    K.shp(os.path.join(sd, 'guerite_%s.shp' % key), [wp(x, 1.8, z) for x in (-1.2, 1.2) for z in (-1.0, 1.0)], 1.3, par=(1.5, 1000, 200))
    return 'guerite_%s.jm' % key, 'guerite_%s.png' % key, 'guerite_%s.shp' % key


def polyline_boudins(pts, keys, face_right, step=18.0):
    """boudins de 18 ft bout à bout le long d'une ligne brisée (points monde x, z) ; face_right : le logo regarde à droite de la ligne
    (sens des points) ; -> [(x, z, yaw, clé)]."""
    pts = np.asarray(pts, float); seg = np.diff(pts, axis=0); ls = np.hypot(seg[:, 0], seg[:, 1]); cum = np.r_[0, np.cumsum(ls)]
    n = max(1, int(np.ceil(cum[-1] / step))); out = []
    for k, t in enumerate(np.linspace(step / 2, cum[-1] - step / 2, n) if n > 1 else [cum[-1] / 2]):
        i = min(int(np.searchsorted(cum, t, side='right')) - 1, len(seg) - 1); d = seg[i] / ls[i]; P = pts[i] + d * (t - cum[i])
        f = np.array([-d[1], d[0]]) * (1 if face_right else -1)
        out.append((float(P[0]), float(P[1]), float(np.arctan2(f[0], f[1])), keys[min(k, len(keys) - 1)] if k < len(keys) else keys[k % len(keys)]))
    return out


def poly_at(pts, t):
    """point à la fraction t (0..1) de la longueur d'une ligne brisée."""
    pts = np.asarray(pts, float); seg = np.diff(pts, axis=0); ls = np.hypot(seg[:, 0], seg[:, 1]); cum = np.r_[0, np.cumsum(ls)]; L = t * cum[-1]
    i = min(int(np.searchsorted(cum, L, side='right')) - 1, len(seg) - 1); return pts[i] + seg[i] / ls[i] * (L - cum[i])


def regate(OUT, A, B, box):
    """v29 : les portes de chrono du tour dans box (x0, x1, z0, z1, demi-largeur <= 20) remplacées, au même rang, par des portes en travers
    du couloir de boudins A / B (milieu des 2 lignes, largeur du couloir), réparties le long du couloir."""
    p = os.path.join(OUT, 'timing_gates'); L = open(p).read().split('\n'); i0 = L.index('checkpoints:'); k = []
    import re
    for i in range(i0 + 1, len(L)):
        m = re.match(r'([\d.]+) \[([-\d.]+) [-\d.]+ ([-\d.]+)\]', L[i])
        if not m:
            break
        h, x, z = map(float, m.groups())
        if h <= 20.0 and box[0] <= x <= box[1] and box[2] <= z <= box[3]:
            k.append(i)
    assert k == list(range(k[0], k[0] + len(k))) and len(k) >= 3, ("portes du couloir de départ introuvables", k)
    new = []
    for j, t in enumerate(np.linspace(0.12, 0.9, len(k))):
        a, b = poly_at(A, t), poly_at(B, t); c = (a + b) / 2; half = float(np.hypot(*(a - b)) / 2 - 1.0)
        c1 = (poly_at(A, min(t + 0.03, 1)) + poly_at(B, min(t + 0.03, 1))) / 2; c0 = (poly_at(A, max(t - 0.03, 0)) + poly_at(B, max(t - 0.03, 0))) / 2
        d = (c1 - c0) / np.hypot(*(c1 - c0)) * half
        new.append('%.6f [%.6f 0.000000 %.6f] [%.6f 0.000000 %.6f]' % (half, c[0], c[1], d[0], d[1]))
    for i, l in zip(k, new):
        L[i] = l
    open(p, 'w', newline='\n').write('\n'.join(L))
    return len(k)


def led_board_v29(path_png, logo_dir, stade_src):
    """v29 (« les banderoles du stade : buggées, des traits noirs et gris ; USLAND, puis le logo Supercross de Paris que je t'ai envoyé,
    USLAND, puis le logo MX Sim Racing en long ; un motif de 4 qui se répète ») : texture du bandeau LED (2048 x 128 = 12,8 x 0,8 m), fond
    uni sans séparateurs."""
    import sys
    from scipy import ndimage
    sys.path.insert(0, stade_src)
    from arena import branding as BR
    W, H = 2048, 128; bgc = (10, 12, 24); im = Image.new('RGB', (W, H), bgc); q = W // 4
    def us(x0):
        BR._paste(im, BR.logo_rgba(), (x0 + q * 0.12, H * 0.16, x0 + q * 0.88, H * 0.84))
    us(0); us(2 * q)
    ph = Image.open(os.path.join(logo_dir, 'logo paris26.jpg')).convert('RGB'); a = np.asarray(ph, int)
    bgm = (a.min(-1) > 205) & ((a.max(-1) - a.min(-1)) < 40); lab, _ = ndimage.label(bgm)
    edge = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}; out_ = np.isin(lab, list(edge))
    al = np.where(out_, 0, 255).astype(np.uint8); al = np.asarray(Image.fromarray(al).filter(__import__('PIL.ImageFilter', fromlist=['x']).GaussianBlur(1.2)))
    pr = Image.fromarray(np.dstack([a.astype(np.uint8), al]), 'RGBA'); pr = pr.crop(pr.getbbox())
    fit(im, pr, (q + 10, 6, 2 * q - 10, H - 6), 0.02)
    mx = Image.open(os.path.join(logo_dir, 'logo mxsim racing.png')).convert('RGBA'); b_ = np.asarray(mx).copy()
    b_[..., 3] = np.where(b_[..., :3].max(-1) > 38, 255, 0); mx = Image.fromarray(b_, 'RGBA'); mx = mx.crop(mx.getbbox())
    fit(im, mx, (3 * q + 40, 14, 4 * q - 40, H - 14), 0.04)
    im.save(path_png)
    return path_png
