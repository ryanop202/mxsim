"""v28-v30 de Bazo (branche usland-paris-by-bazo, reprise en v35 sans le terrain) - v28 (review en jeu de la v27d, 2026-11-26) : objets en plus, posés par build_zion.deco_v21 (fin du fichier statues).

- tuff blocks (tunnels en U, appelés « bottes » / « ballots » dans l'historique ; v36 : « nos bottes de paille sont des tuff blocks,
  remplace leur nom ») aux endroits montrés sur les captures (virages : entrée, intérieur, sortie ; abords des sauts) ;
- boudins aux couleurs des sponsors qui SORTENT DU SOL 20 s après la chute de la grille (« de 0 à 20 s il n'y a rien, à 20 s ils
  apparaissent ») : le long de la ligne de départ (des 2 côtés) et un boudin Automoto au bout du saut AMV, vers le virage T_D ;
  nofrills.js les déplace (mx.move_statue), comme le long tuff block de la version USLAND et les boudins de Saint-Thibéry ;
- poteau de virage (bâton rouge sur socle, on tombe si on le touche ; forme créée, façon poteaux de RF) à l'intérieur du 2e virage
  après l'arrivée ;
- bâche noire derrière les grilles de départ (celle de Saint-Georges, bannière passée en noir, sans sponsor).
Repère des tuff blocks : s le long du tour, v > 0 = droite du sens de course (comme build_paris)."""
import os
import shutil
import numpy as np
from PIL import Image, ImageDraw

import hab_kit as K
from hab_kit import Mesh, fit

LATE_S = 20.0
BOUDIN_KEYS = ['mxsim', 'five', 'honda', 'yamaha', 'automoto', 'motoverte', 'minerva', 'amv', 'milwaukee', '50factory']
BOUDIN_COURT = 18.0      # v39 (« que ça passe sur 3 : un logo tous les 3 petits d'origine ») : 12 -> 18 ft ; v38d (« 2 boudins font 1, un seul gros logo sur les 2 ») : 6 -> 12 ft ;
BOUDIN_COURT_V36 = 6.0      # v36 (photo du vrai Paris : boudins plus courts, « collés ») : boudins de 6 ft bout à bout au lieu de 18 ft


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


def boudins_line(P, tag, u0, u1, v, keys, step=BOUDIN_COURT):
    """boudins de 18 ft bout à bout le long du tour entre u0 et u1 (centres), face à la piste ; -> [(x, z, yaw, clé)]."""
    g = P.seg(tag); out = []; n = max(1, int(round((u1 - u0) / step)) + 1)
    for k, u in enumerate(np.linspace(u0, u1, n)):
        Q, th = P.at(g['s0'] + u, v); f = -np.array([-np.sin(th), np.cos(th)]) * np.sign(v)
        out.append((float(Q[0]), float(Q[1]), float(np.arctan2(f[0], f[1])), keys[k % len(keys)]))
    return out




def boudin_court(sd, props, L=BOUDIN_COURT):
    """v36 : boudin_logo3 (18 ft le long de x local) raccourci à L ft (x x L / 18, même section, mêmes u v) ; collision : boules du
    modèle de 18 ft ramenées sur L ft (une sur trois). -> noms jm, shp."""
    k = L / 18.0; out = []
    for l in open(os.path.join(props, 'boudin_logo3.jm')).read().split('\n'):
        v = l.split()
        if len(v) == 8:
            v[0] = '%.6f' % (float(v[0]) * k); l = ' '.join(v)
        out.append(l)
    open(os.path.join(sd, 'boudin_court.jm'), 'w', newline='\n').write('\n'.join(out))
    S = [l.split() for l in open(os.path.join(props, 'boudin_logo3.shp')).read().split('\n')[1:] if l.split()]
    S = S[::3] + ([S[-1]] if (len(S) - 1) % 3 else [])
    S = ['%.4f %s' % (float(v[0]) * k, ' '.join(v[1:])) for v in S]
    open(os.path.join(sd, 'boudin_court.shp'), 'w', newline='\n').write('\n'.join([str(len(S))] + S) + '\n')
    return 'boudin_court.jm', 'boudin_court.shp'


def boudin_court_skin(sd, key, props, L=BOUDIN_COURT, rgb=None):
    """v36 : peau du boudin court. Le modèle garde les u de 18 ft : la texture est écrasée x 18 / L le long du boudin ; on la dessine
    donc aux vraies proportions (largeur W x L / 18) puis on l'étire à W (logo jamais déformé une fois en jeu). Bouts gardés.
    rgb : couleur unie sans logo (boudins tricolores)."""
    name = 'boudin_court_%s.png' % (key if rgb is None else 'uni_%02x%02x%02x' % rgb); p = os.path.join(sd, name)
    if os.path.exists(p):
        return name
    base = Image.open(os.path.join(props, 'boudin_flyrouge3.png')).convert('RGB').copy(); W, H = base.size; hb = int(H * 0.915)
    Wt = max(64, int(round(W * L / 18.0)))
    if rgb is None:
        import sponsors as SP
        bg, lg = SP.panel(key)
    else:
        bg, lg = rgb, None
    top = Image.new('RGB', (Wt, hb), bg)
    if lg is not None:
        for yc in (0.245, 0.705):
            fit(top, lg, (int(0.08 * Wt), int((yc - 0.115) * H), int(0.92 * Wt), int((yc + 0.115) * H)), 0.0)
    base.paste(top.resize((W, hb), Image.LANCZOS), (0, 0)); base.save(p, optimize=True)
    return name


def corner_stick(sd):
    """poteau de virage : socle rond gris foncé (r 1,1 ft, 0,45 ft) + bâton rouge (r 0,16 ft, 5 ft) à 2 bandes blanches ; collision
    dure (boules de 0,35 ft le long du bâton, réglages des murs : on tombe si on le touche). Forme créée."""
    # v29 (« le piqué rouge, mets-le bien plus haut, et pas de truc blanc dessus ») : bâton tout rouge de 8 ft
    W = 64; im = Image.new('RGB', (W, W), (48, 48, 52)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 31, W - 1], fill=(206, 24, 30))
    im.save(os.path.join(sd, 'poteau_virage.png'))
    m = Mesh(); red = K.R((0, 0, 32, W), W, W); base = K.R((40, 40, 60, 60), W, W)
    # v36k (photo du vrai Paris : piquet rouge sur un gros socle ; « prends la base de la RF si tu l'as, sinon un plus grand ; rouge c'est
    # la bonne couleur ») : le modèle RF (sx2026/models/corners/corner_post.jm) n'est pas dans nos archives (paquet sx2026 du jeu) ->
    # forme créée plus grande : socle rond 3,6 ft de diamètre, 0,55 ft, bord arrondi (2 anneaux qui rentrent), bâton rouge 0,5 ft de
    # diamètre, 8 ft au-dessus du socle
    m.tube((0, 0.0, 0), (0, 0.45, 0), 1.8, base, 24)
    m.tube((0, 0.45, 0), (0, 0.55, 0), 1.7, base, 24)
    m.tube((0, 0.55, 0), (0, 0.62, 0), 1.5, base, 24)
    # v36n (pack d'objets RF sx2026 envoyé par l'utilisateur : « reprends le piquet, fais-le tout rouge ; mets-le dans le terrain » ; socle
    # gardé) : bâton = modèle RF sx2026/models/corners/corner_post (0,25 ft de diamètre, 10 ft, 0,25 ft sous le sol) et sa collision,
    # copiés dans commun/assets/props/rf_corner_post.* (accord de l'utilisateur), texture rouge unie à nous (l'original est jaune / blanc) ;
    # socle = le nôtre (rond noir 3,6 ft, bord arrondi) ; 2 statues au même point
    m.write(os.path.join(sd, 'poteau_virage.jm'))
    K.shp(os.path.join(sd, 'poteau_virage.shp'), [(x, 0.35, z) for x, z in ((0.9, 0), (-0.9, 0), (0, 0.9), (0, -0.9))], 0.4, par=(1.5, 1000, 200))
    props = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'commun', 'assets', 'props')
    for f_ in ('rf_corner_post.jm', 'rf_corner_post.shp'):
        shutil.copy(os.path.join(props, f_), os.path.join(sd, f_))
    # v38 (« le piqué à l'intérieur, fais-le monter un tiers plus haut ») : bâton RF x4/3 en hauteur (sommets et boules de collision)
    kY = 4.0 / 3.0; L_ = open(os.path.join(sd, 'rf_corner_post.jm')).read().split(chr(10))
    for i_, l_ in enumerate(L_):
        v_ = l_.split()
        if len(v_) == 8 and float(v_[1]) > 0:
            v_[1] = '%.6f' % (float(v_[1]) * kY); L_[i_] = ' '.join(v_)
    open(os.path.join(sd, 'rf_corner_post.jm'), 'w', newline=chr(10)).write(chr(10).join(L_))
    S_ = open(os.path.join(sd, 'rf_corner_post.shp')).read().split(chr(10)); out_ = [S_[0]]
    for l_ in S_[1:]:
        v_ = l_.split()
        if len(v_) >= 4 and float(v_[1]) > 0:
            v_[1] = '%.4f' % (float(v_[1]) * kY)
        out_.append(' '.join(v_))
    open(os.path.join(sd, 'rf_corner_post.shp'), 'w', newline=chr(10)).write(chr(10).join(out_))
    Image.new('RGB', (64, 64), (206, 24, 30)).save(os.path.join(sd, 'rf_corner_post_rouge.png'))
    return [('poteau_virage.jm', 'poteau_virage.png', 'poteau_virage.shp'), ('rf_corner_post.jm', 'rf_corner_post_rouge.png', 'rf_corner_post.shp')]


def start_tarp_black(sd, sgm_statue):
    """bâche du départ de Saint-Georges (90 ft le long de x local, origine au sol au milieu, face imprimée = -z local) : bannière
    passée en noir uni (« sans les sponsors, juste du noir »), filet noir gardé."""
    shutil.copy(os.path.join(sgm_statue, 'start_tarp.jm'), os.path.join(sd, 'start_tarp_noir.jm'))
    im = Image.open(os.path.join(sgm_statue, 'start_tarp.png')).convert('RGBA'); a = np.asarray(im).copy()
    a[:1302, :, :3] = (16, 16, 18); a[:1302, :, 3] = 255
    im = Image.fromarray(a, 'RGBA')
    if TARP_LOGOS:
        # v38d (« 6 logos, le même espace entre chaque : Venum (tête + logo), Monster (griffe + Monster Energy, comme les grilles), Supercross
        # Paris rose (comme les bandeaux du stade), puis Venum, Monster, Supercross Paris ») : bannière de 90 ft à 80 px / ft dessinée d'un
        # bloc (7200 x 320 px) puis découpée dans les 4 bandes de 2048 px de la texture (rangées k x 326), comme le START de Saint-Georges
        import gate_monster as GM
        ROOT_ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        lg = {'venum': GM._user_logo('venum'), 'monster': GM._user_logo('monster'), 'paris': paris_logo(os.path.join(ROOT_, 'commun', 'assets', 'logos', 'user'))}
        PPF, BH = 80, 320; V = Image.new('RGBA', (4 * 2048, BH), (16, 16, 18, 255))
        for i, k in enumerate(['venum', 'monster', 'paris'] * 2):
            c = (7.5 + 15.0 * i) * PPF; w = 11.0 * PPF
            fit(V, lg[k], (int(c - w / 2), int(BH * 0.10), int(c + w / 2), int(BH * 0.90)), 0.02)
        for k in range(4):
            im.paste(V.crop((k * 2048, 0, (k + 1) * 2048, BH)), (0, k * (BH + 6)))
        # v38e (« du côté des grilles, tout noir complet ; de l'autre côté les logos, à l'endroit ») : tout le reste (filet, cadre) en noir plein
        a2 = np.asarray(im).copy(); a2[1302:, :, :3] = (16, 16, 18); a2[1302:, :, 3] = 255; im = Image.fromarray(a2, 'RGBA')
    im.save(os.path.join(sd, 'start_tarp_noir.png'))
    return 'start_tarp_noir.jm', 'start_tarp_noir.png', None


TARP_LOGOS = True


def start_tarp_panel(sd, L=90.0, Hh=10.5):
    """v39 (« le mur noir derrière le départ : aligné à la grille, logos côté grilles, centrés sur la bâche ») : panneau plein à nous (L x Hh
    ft, le long de x local, origine au sol au milieu), face imprimée = -z local (vers les grilles, comme la bâche de Saint-Georges), dos noir.
    Texture 4096 x 1024 : moitié haute = face (6 logos, 15 ft d'écart, centrés en hauteur), moitié basse = noir (dos)."""
    import gate_monster as GM
    from deco_v21 import _face, MAT_MAT
    ROOT_ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    lg = {'venum': GM._user_logo('venum'), 'monster': GM._user_logo('monster'), 'paris': paris_logo(os.path.join(ROOT_, 'commun', 'assets', 'logos', 'user'))}
    W, Hp = 4096, 512; ppf_x, ppf_y = W / L, Hp / Hh; im = Image.new('RGBA', (W, 2 * Hp), (16, 16, 18, 255))
    for i, k in enumerate(['venum', 'monster', 'paris'] * 2):
        c = (L / 12.0 + L / 6.0 * i) * ppf_x; w = 11.0 * ppf_x; h0, h1 = Hh * 0.18, Hh * 0.82
        l_ = lg[k]; l_ = l_.resize((max(1, int(l_.width * ppf_x / ppf_y)), l_.height), Image.LANCZOS)   # px / ft différents en x et y -> logo jamais déformé en jeu
        fit(im, l_, (int(c - w / 2), int(h0 * ppf_y), int(c + w / 2), int(h1 * ppf_y)), 0.02)
    im.convert('RGB').save(os.path.join(sd, 'bache_depart.png'))
    m = Mesh(); y0 = 0.0
    F = [(-L / 2, y0, 0.0), (L / 2, y0, 0.0), (L / 2, Hh, 0.0), (-L / 2, Hh, 0.0)]
    uvF = [(1.0, 0.5), (0.0, 0.5), (0.0, 1.0), (1.0, 1.0)]          # vu depuis -z : +x à gauche -> u = 0 à +x
    _face(m, F, uvF, [(0, 0, -1)] * 4)
    _face(m, F, [(0.5, 0.25)] * 4, [(0, 0, 1)] * 4)                   # dos noir
    m.write(os.path.join(sd, 'bache_depart.jm'), MAT_MAT)
    return 'bache_depart.jm', 'bache_depart.png', None


def paris_logo(logo_dir):
    """logo Supercross Paris de l'utilisateur (logo paris26.jpg) détouré (fond blanc enlevé depuis les bords)."""
    from scipy import ndimage
    from PIL import ImageFilter
    ph = Image.open(os.path.join(logo_dir, 'logo paris26.jpg')).convert('RGB'); a = np.asarray(ph, int)
    bgm = (a.min(-1) > 205) & ((a.max(-1) - a.min(-1)) < 40); lab, _ = ndimage.label(bgm)
    edge = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}; out_ = np.isin(lab, list(edge))
    al = np.asarray(Image.fromarray(np.where(out_, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)))
    pr = Image.fromarray(np.dstack([a.astype(np.uint8), al]), 'RGBA'); return pr.crop(pr.getbbox())


def nofrills_js(rows):
    """script : chaque statue de rows ([rang, x0, y0, z0, yaw0, x1, y1, z1, yaw1]) est à la place 0 jusqu'à LATE_S s après la chute de
    la grille, puis à la place 1 ; sans chute de grille (entraînement libre) elle est à la place 1. Boudin « tardif » : place 0 =
    enterré (y -200), place 1 = posé ; v39 : boudin « déplacé » (ligne Minerva : place du départ, puis place du reste de la manche).
    Texte ASCII."""
    return '\n'.join([
        '/*', 'USLAND Paris - boudins de la ligne de depart : place 0 de 0 a 20 s apres la chute de la grille, puis place 1',
        '(boudins tardifs : enterres puis sortis ; ligne Minerva : deplacee). Texte ASCII expres.', '*/', '',
        'var g_lt = [' + ', '.join('[%d, %.3f, %.3f, %.3f, %.6f, %.3f, %.3f, %.3f, %.6f]' % tuple(r) for r in rows) + '];',
        'var LATE_AFTER = %.1f;' % LATE_S,
        'var g_lt_shown = -1;', 'var g_lt_t = -1.0;', '',
        'function ltSet(show) {', '    var i, s;', '    for (i = 0; i < g_lt.length; i++) {', '        s = g_lt[i];',
        '        if (show) mx.move_statue(s[0], s[5], s[6], s[7], s[8]);', '        else mx.move_statue(s[0], s[1], s[2], s[3], s[4]);',
        '    }', '    g_lt_shown = show;', '}', '',
        'function lateTuff(seconds) {', '    var d = mx.get_gate_drop_time();', '    var show = (d < 0 || mx.seconds >= d + LATE_AFTER);',
        '    if (show != g_lt_shown || mx.seconds < g_lt_t || mx.seconds - g_lt_t > 1.0) {', '        ltSet(show);',
        '        g_lt_t = mx.seconds;', '    }', '    if (lateTuffPrev)', '        lateTuffPrev(seconds);', '}', '',
        'var lateTuffPrev = mx.frame_handler;', 'mx.frame_handler = lateTuff;', ''])


def write_late(OUT, late_lines, moves=None):
    """rangs des statues « tardives » dans statues (et le même rang dans chaque variante), puis nofrills.js.
    v39 : moves = {ligne de statue : (x, z, yaw) après 20 s, ou None = enterrée après 20 s} : statues posées au départ puis déplacées
    (elles sont aussi dans late_lines). Hauteur : celle de la ligne de statue (avant : 0 forcé)."""
    moves = moves or {}
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
        v_ = l.split(']')[0][1:].split(); x, y, z, a = float(v_[0]), float(v_[1]), float(v_[2]), float(l.split(']')[1].split()[0])
        if l in moves:                                   # posée au départ, déplacée (ou enterrée) après 20 s
            m_ = moves[l]
            rows.append((i, x, y, z, a) + ((m_[0], y, m_[1], m_[2]) if m_ is not None else (x, -200.0, z, a)))
        else:                                            # tardive : enterrée, puis sortie à sa place
            rows.append((i, x, -200.0, z, a, x, y, z, a))
    open(os.path.join(OUT, "nofrills.js"), "w", newline="\n", encoding="ascii").write(nofrills_js(rows))
    fj = os.path.join(OUT, "frills.js")
    if os.path.exists(fj):   # v38c : la v37 ajoute frills.js (classement) : même code des boudins tardifs, noms à part (ne se gênent pas)
        js2 = nofrills_js(rows).replace('g_lt', 'g_lt2').replace('LATE_AFTER', 'LATE_AFTER2').replace('ltSet', 'ltSet2').replace('lateTuff', 'lateTuff2')
        open(fj, "a", newline="\n", encoding="ascii").write("\n" + js2)
    return len(rows)


def booth(sd, wp, key='mxsim', X=2.25, Z=2.0, Hc=4.5, y0=0.0):
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
        if y0 < 0:   # v38c (« mets du noir jusqu'au sol autour du plot de terre, qu'on voie pas la terre, une longue cabane ») : jupe noire
            Q = [c - r * half + up * y0, c + r * half + up * y0, c + r * half, c - r * half]
            D22._face(m, [wp(*p) for p in Q], [(blk[0], blk[1])] * 4, [nw(n)] * 4)
    if y0 < 0:   # v38e (« qu'on ne voie pas la terre du tout dans la cabane ») : fond noir posé sur le socle (vu d'en haut, les 2 faces)
        F = [np.array(p_, float) for p_ in ((-X, 0.03, -Z), (X, 0.03, -Z), (X, 0.03, Z), (-X, 0.03, Z))]
        D22._face(m, [wp(*p) for p in F], [(blk[0], blk[1])] * 4, [nw(up)] * 4)
        D22._face(m, [wp(*p) for p in F[::-1]], [(blk[0], blk[1])] * 4, [nw(up)] * 4)
    m.write(os.path.join(sd, 'guerite_%s.jm' % key), D22.MAT_MAT)
    K.shp(os.path.join(sd, 'guerite_%s.shp' % key), [wp(x, 1.8, z) for x in (-1.2, 1.2) for z in (-1.0, 1.0)], 1.3, par=(1.5, 1000, 200))
    return 'guerite_%s.jm' % key, 'guerite_%s.png' % key, 'guerite_%s.shp' % key


def polyline_boudins(pts, keys, face_right, step=BOUDIN_COURT):
    """boudins de 18 ft bout à bout le long d'une ligne brisée (points monde x, z) ; face_right : le logo regarde à droite de la ligne
    (sens des points) ; -> [(x, z, yaw, clé)]."""
    pts = np.asarray(pts, float); seg = np.diff(pts, axis=0); ls = np.hypot(seg[:, 0], seg[:, 1]); cum = np.r_[0, np.cumsum(ls)]
    n = max(1, int(np.ceil(cum[-1] / step))); out = []
    for k, t in enumerate(np.linspace(step / 2, cum[-1] - step / 2, n) if n > 1 else [cum[-1] / 2]):
        i = min(int(np.searchsorted(cum, t, side='right')) - 1, len(seg) - 1); d = seg[i] / ls[i]; P = pts[i] + d * (t - cum[i])
        f = np.array([-d[1], d[0]]) * (1 if face_right else -1)
        out.append((float(P[0]), float(P[1]), float(np.arctan2(f[0], f[1])), keys[min(k, len(keys) - 1)] if k < len(keys) else keys[k % len(keys)]))
    return out


def n_boudins(pts, step=BOUDIN_COURT):
    """nombre de boudins que polyline_boudins pose sur cette ligne brisée."""
    pts = np.asarray(pts, float); return max(1, int(np.ceil(np.hypot(*np.diff(pts, axis=0).T).sum() / step)))


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


RAMP_HEAD_U = 0.11      # v38e : centre de la tête de serpent sur la bande du dessus de la rampe (u, 0,005 = lèvre)


def ramp_black_venum(statue_dir, logo_dir):
    """v38 (« les rampes de freestyle : fais-les toutes noires, avec un logo Venum en haut de la rampe, là où roule la moto ») : texture
    du tremplin ramp_50 passée en noir (relief gardé), logo Venum blanc sur la bande du dessus (UV u 0,005 (lèvre) - 0,997 (pied) = le long de la rampe,
    v 0,81-0,992 = en travers ; u croît vers le pied) ; logo tourné de 180° : il se lit du pied vers la lèvre, jamais en miroir vu du dessus."""
    p = os.path.join(statue_dir, 'ramp_50.png'); im = Image.open(p).convert('RGBA'); a = np.asarray(im).astype(float)
    lum = a[..., :3].mean(-1, keepdims=True); a[..., :3] = 14.0 + 0.16 * lum
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA'); W, H = im.size
    lg = Image.open(os.path.join(logo_dir, 'logo venum full.webp')).convert('RGBA'); b = np.asarray(lg).astype(float)
    al = (b[..., 3] / 255.0) * (b[..., :3].mean(-1) < 128); lg = Image.fromarray(np.dstack([np.full(al.shape + (3,), 245.0), al * 255]).astype(np.uint8), 'RGBA')
    lg = lg.crop(lg.getbbox())
    # v38c (« enlève le logo Venum, mets juste la tête du serpent, même taille, pivotée dans le sens de la rampe, les dents vers le bas de
    # la rampe ») : la tête = la partie gauche du logo (avant la 1re colonne vide) ; dents (bas de l'image) vers le pied (u croissant) :
    # rotation de +90° (le haut de la tête vers la lèvre)
    al_ = np.asarray(lg)[..., 3] > 20; cols = al_.any(0); x_ = 0
    while x_ < len(cols) and cols[x_]: x_ += 1
    while x_ < len(cols) and not cols[x_]: x_ += 1
    tete = lg.crop((0, 0, max(1, x_ - 2), lg.size[1])); tete = tete.crop(tete.getbbox()).rotate(90, expand=True)
    # v38e (« la tête plus haut, là où j'ai entouré en gris, sur les 3 rampes ») : la bande du dessus va de u 0,005 (lèvre, 9 ft) à 0,997
    # (pied) ; la tête était à u 0,318-0,40 (~3,5 ft, 40 % de la hauteur) ; ronds gris de la capture = ~80 % de la hauteur -> centre à
    # u = RAMP_HEAD_U (~7,3 ft), même taille
    hv = int((0.985 - 0.82) * H); wv = int(hv * tete.size[0] / tete.size[1]) + 8; x0_ = int(RAMP_HEAD_U * W) - wv // 2
    box = (x0_, int((1 - 0.985) * H), x0_ + wv, int((1 - 0.82) * H))
    fit(im, tete, box, 0.04); im.save(p)
    return p


def ramp_tall(statue_dir, k=1.4, name='ramp_50_haut'):
    """v38c (« fais-la plus haute, plus raide, qu'elle kick plus, uniquement celle-là, la plus proche de la bosse ») : tremplin x k en
    hauteur (même longueur : plus raide), collision aussi ; même texture."""
    L = open(os.path.join(statue_dir, 'ramp_50.jm')).read().split(chr(10))
    for i, l in enumerate(L):
        v = l.split()
        if len(v) == 8:
            v[1] = '%.6f' % (float(v[1]) * k); L[i] = ' '.join(v)
    open(os.path.join(statue_dir, name + '.jm'), 'w', newline=chr(10)).write(chr(10).join(L))
    S_ = open(os.path.join(statue_dir, 'ramp_50.shp')).read().split(chr(10)); out = [S_[0]]
    for l in S_[1:]:
        v = l.split()
        if len(v) >= 4:
            v[1] = '%.4f' % (float(v[1]) * k)
        out.append(' '.join(v))
    open(os.path.join(statue_dir, name + '.shp'), 'w', newline=chr(10)).write(chr(10).join(out))
    return name + '.jm', name + '.shp'


def mesh_mat(sd, L, W=4.0, name=None):
    """v38c (« derrière la rampe, une grille métallique en losanges posée au sol, gris noir comme la rampe, petits losanges fins ») :
    plaque au ras du sol (0,06 ft), W x L ft, le long de x local, centrée sur l'origine ; texture : métal déployé gris foncé, losanges
    de ~0,5 ft (répétés par les UV), bords en cornière. Forme créée."""
    name = name or 'grille_rampe_%d' % int(round(L))
    # v38d (« pas ouf : une grille comme les grilles de départ, couleur métal ; les mailles noires, pas de fond noir dessous, la couleur de
    # la rampe ») : seulement les fils (gris foncé métal), les trous transparents (on voit le sol)
    T = 256; im = Image.new('RGBA', (T, T), (0, 0, 0, 0)); d = ImageDraw.Draw(im); n = 4; c = T // n
    # v38e : fil de métal foncé (gris-noir de la rampe) avec un reflet clair au milieu (aspect métal, comme les grilles de départ)
    # v39 (« il n'y a pas du tout les grilles devant les rampes ») : fils trop fins -> invisibles en jeu (transparence moyennée de loin < 50 %) ;
    # fils 2,5 x plus épais (~60 % de métal, petits trous), reflet clair au milieu
    for wd_, col_ in ((20, (30, 30, 33, 255)), (6, (92, 92, 98, 255))):
        for i in range(n + 1):
            for j in range(n + 1):
                x, y = i * c, j * c
                d.polygon([(x, y - c // 2), (x + c // 2, y), (x, y + c // 2), (x - c // 2, y)], outline=col_, width=wd_)
    im.save(os.path.join(sd, 'grille_losanges-repeat.png'))      # « -repeat » : le jeu ne répète une texture que si son nom le dit (comme RF)
    m = Mesh(); y = 0.30; rep_ = 2.0                                  # une tuile de texture = 2 ft ; v39b (Ryan : « la grille ne s'affiche que quand on arrive ») : 0,06 -> 0,30 ft au-dessus du sol (à 0,06 ft, de loin le jeu dessinait la terre par-dessus)
    P = [(-L / 2, y, W / 2), (L / 2, y, W / 2), (L / 2, y, -W / 2), (-L / 2, y, -W / 2)]
    m.quad(P, (0, 0, L / rep_, W / rep_), two=True)
    m.write(os.path.join(sd, name + '.jm'))
    return name + '.jm', 'grille_losanges-repeat.png'


def rf_border(path, floor_poly, xpad, rng, folder, dist_edge=(4.0, 14.0, (18.0, 60.0)), wall_max=50.0):
    """v38c (« reprends les planches et le béton de la RF entre la piste et le stade, mêmes distances, même dégradé ») : comme RF
    Anaheim 1 (décals mesurés : terre « offtrack » 28 ft tous les ~7 ft au bord de la piste, planches « ply » 22 ft tous les ~8,6 ft
    ~10 ft plus loin, disques de béton 35 ft tous les ~13 ft de là jusqu'au mur) ; ici seulement côté stade (sol à moins de wall_max ft
    du bord du sol), pas sur le paddock. -> lignes de décals (@folder/rfborder/...)."""
    from scipy.spatial import cKDTree
    from geo_tools import inside
    sm = path.samples(1.0); P = np.c_[sm['x'], sm['z']]; th = np.array(sm['th']); tr = cKDTree(P)
    fl = np.asarray(floor_poly, float); seg = np.diff(np.vstack([fl, fl[:1]]), axis=0)
    def d_wall(q):
        a = fl; b = fl + seg; ab = b - a; t = np.clip(((q - a) * ab).sum(1) / (ab * ab).sum(1), 0, 1); return float(np.min(np.hypot(*(a + ab * t[:, None] - q).T)))
    def ok(q, e_min):
        dt, _ = tr.query(q); return (inside(q[None, :], fl)[0] and q[0] < xpad - 4.0 and dt - 15.2 >= e_min - 1.0 and d_wall(q) < wall_max and d_wall(q) > 3.0)
    out = []; f = lambda x, z, a, s_, t_: out.append("[%.6f %.6f] %.6f %.6f 1.000000 @%s/rfborder/%s" % (x, z, a, s_, folder, t_))
    def ring(e, step, size, tex, jit):
        placed = []
        for sg in (-1, 1):
            for k in range(0, len(P), 1):
                q = P[k] + sg * (15.2 + e) * np.array([-np.sin(th[k]), np.cos(th[k])])
                if not ok(q, e) or any(np.hypot(*(q - p_)) < step for p_ in placed[-40:]):
                    continue
                placed.append(q); f(q[0], q[1], th[k] + rng.normal(0, jit), size, tex)
        return len(placed)
    n1 = ring(dist_edge[0], 7.2, 28.0, 'offtrack.png', 3.0)
    n2 = ring(dist_edge[1], 8.6, 22.0, 'ply.png', 0.12)
    e0, e1 = dist_edge[2]; n3 = 0; pts = []
    xs, zs = fl[:, 0], fl[:, 1]
    for _ in range(6000):
        q = np.array([rng.uniform(xs.min(), xs.max()), rng.uniform(zs.min(), zs.max())]); dt, _ = tr.query(q)
        if not (e0 <= dt - 15.2 <= e1) or not ok(q, e0) or any(np.hypot(*(q - p_)) < 13.0 for p_ in pts):
            continue
        pts.append(q); f(q[0], q[1], rng.uniform(-np.pi, np.pi), 35.0, 'concrete.png'); n3 += 1
    return out, (n1, n2, n3)


def border_textures(rf_tex, out_dir, terre_png=None):
    """v38e : textures de la bordure.
    - planches.png : UNE plaque OSB de RF (4 x 8 ft) au milieu d'une décal carrée de 8 ft (moitié gauche / droite transparentes),
      long côté vertical = le long de la piste, joints sombres aux bouts ;
    - terre_bord.png : la terre du sol (terre_stt, même grain, même couleur, même échelle : 26 ft pour toute l'image) en décal de 16 ft,
      opaque sur 2 ft en travers, fondue sur 2 ft de chaque côté (nulle au bord des planches), fondue sur 3 ft aux bouts (tous les 8 ft)."""
    ply = Image.open(os.path.join(rf_tex, 'ply.png')).convert('RGB').crop((80, 667, 1120, 1187)).rotate(90, expand=True).resize((512, 1024), Image.LANCZOS)
    P = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0)); P.paste(ply, (256, 0))
    d = ImageDraw.Draw(P); d.rectangle([256, 0, 767, 5], fill=(58, 48, 36, 255)); d.rectangle([256, 1018, 767, 1023], fill=(58, 48, 36, 255))
    P.save(os.path.join(out_dir, 'planches.png'))
    n = 1024; src = Image.open(terre_png).convert('RGB'); w_ = src.size[0]; k = int(round(w_ * 16.0 / 26.0)); c = w_ // 2
    T = src.crop((c - k // 2, c - k // 2, c - k // 2 + k, c - k // 2 + k)).resize((n, n), Image.LANCZOS)
    u = (np.arange(n) + 0.5) / n * 16.0 - 8.0                     # ft depuis le centre
    sst = lambda t: (lambda t_: t_ * t_ * (3 - 2 * t_))(np.clip(t, 0, 1))
    au = sst((3.0 - np.abs(u)) / 2.0)                              # v38e (« la terre s'arrête juste autour du terrain, avant le bois ») : 1 sur |a| <= 1, 0 à |a| = 3 (= bord des planches)
    av = sst((8.0 - np.abs(u)) / 3.0)                              # le long : fondu sur 3 ft aux bouts
    A = (np.outer(av, au) * 255).astype(np.uint8)
    T = T.convert('RGBA'); T.putalpha(Image.fromarray(A)); T.save(os.path.join(out_dir, 'terre_bord.png'))
    return 'planches.png', 'terre_bord.png'


BORD_E0, BORD_PW, BORD_BERM = 10.0, 4.0, 4.0    # v38e : planches de 10 à 14 ft du bord du couloir ; à 4 ft au moins du pied des appuis (relief > 1 ft)


def border_v2(OUT, path, fl, xpad, folder, wall_max=32.0, e0=BORD_E0, pw=BORD_PW, berm=BORD_BERM):
    """v38e (review v38d, photo du tour du stade avec un trait jaune et un trait gris : « les planches commencent au trait jaune et
    s'arrêtent vers le trait gris, voire un peu après ; après c'est du béton, couleur de mon trait ; le béton est sous les planches, pas de
    dégradé entre les deux ; un dégradé avec la terre, régulier, surtout long, pas des taches ; tout le tour en U, rien au paddock ») :
    mesuré sur la photo (ligne des tuff blocks = bord du couloir, à 20 ft du bord du sol) : trait jaune à ~10 ft, trait gris à ~13 ft.
    Grille de 1 ft ; f = min(distance au bord du couloir - e0, distance au relief (> 1 ft : appuis) - berm), lissée (4 ft) :
    f = 0 = bord intérieur des planches. Planches : une plaque de 4 x 8 ft (f de 0 à pw), bout à bout le long de f = pw / 2 ; terre :
    bande le long de f = -3 (opaque de f = -4 à -2, nulle à f = 0 : la terre s'arrête avant le bois) ; béton (tuile Beton) partout où f >= 0
    dans la zone en U, et sur tout le béton hors du sol de terre côté tribunes (x < paddock). -> (décals, filtre des taches de terre,
    nombres)."""
    import contourpy
    from scipy.ndimage import distance_transform_edt, map_coordinates, gaussian_filter
    from scipy.spatial import cKDTree
    from matplotlib.path import Path as MPath
    t = open(os.path.join(OUT, 'terrain.hf')).read().split(); s_, lo, hi = float(t[1]), float(t[2]), float(t[3])
    Hm = np.asarray(Image.open(os.path.join(OUT, 'terrain.png')), float) / 65535 * (hi - lo) + lo
    fl = np.asarray(fl, float); x0, x1, z0, z1 = fl[:, 0].min() - 2, fl[:, 0].max() + 2, fl[:, 1].min() - 2, fl[:, 1].max() + 2
    xs, zs = np.arange(x0, x1, 1.0), np.arange(z0, z1, 1.0); X, Z = np.meshgrid(xs, zs)
    h = map_coordinates(Hm, [Z / s_, X / s_], order=1)
    sm = path.samples(0.5); dp, _ = cKDTree(np.c_[sm['x'], sm['z']]).query(np.c_[X.ravel(), Z.ravel()]); dp = dp.reshape(X.shape)
    dl = dp - 15.2                                                       # distance au bord du couloir (30,4 ft)
    dh = distance_transform_edt(~((h > 1.0) | (dl < 0)))                 # distance au relief (appuis ; le pied bas des bosses ne compte pas)
    f = gaussian_filter(np.minimum(dl - e0, dh - berm), 4.0)          # lissée : courbes rondes aux raccords appui / ligne droite
    floor = MPath(fl).contains_points(np.c_[X.ravel(), Z.ravel()]).reshape(X.shape); dw = distance_transform_edt(floor)
    U = floor & (X < xpad - 4.0) & (dw < wall_max)
    # aux coins arrondis du sol, la courbe des planches sort du sol de 1-3 ft (sur le béton, à 6 ft au moins des tribunes) : gardée
    Ux = (floor | (distance_transform_edt(~floor) <= 3.5)) & (X < xpad - 4.0) & (dw < wall_max)
    ij = lambda x, z: (int(np.clip(round(z - z0), 0, len(zs) - 1)), int(np.clip(round(x - x0), 0, len(xs) - 1)))
    zone = lambda x, z: bool(U[ij(x, z)])
    fval = lambda x, z: float(f[ij(x, z)])
    gen = contourpy.contour_generator(xs, zs, f); out_p, out_t = [], []          # courbes entières, coupées par la zone en U
    def walk(level, step, size, tex, out, ends=False):
        n = 0
        for ln in gen.lines(level):
            ln = np.asarray(ln); seg = np.diff(ln, axis=0); L = np.hypot(*seg.T); cum = np.r_[0, np.cumsum(L)]
            if cum[-1] < 4.0:
                continue
            for tt in np.arange(step / 2, cum[-1], step):
                i = min(int(np.searchsorted(cum, tt, side='right')) - 1, len(seg) - 1)
                if L[i] < 1e-6:
                    continue
                q = ln[i] + seg[i] / L[i] * (tt - cum[i])
                if not Ux[ij(*q)]:
                    continue
                # direction lissée sur ± 3 ft de la courbe (pas de plaque de travers sur un petit cran)
                a_, b_ = np.searchsorted(cum, tt - 4.0), min(np.searchsorted(cum, tt + 4.0), len(ln) - 1)
                dv = ln[b_] - ln[max(a_, 0)]; th = np.arctan2(dv[1], dv[0])
                out.append("[%.6f %.6f] %.6f %.6f 1.000000 @%s/rfborder/%s" % (q[0], q[1], -(th + np.pi / 2), size, folder, tex)); n += 1
        return n
    n_p = walk(pw / 2.0, 7.9, 8.0, 'planches.png', out_p)
    n_t = walk(-3.0, 8.0, 16.0, 'terre_bord.png', out_t)
    # béton : tuile Beton sur la zone en U où f >= 0 (sous les planches et au-delà) + tout le béton (Road) hors du sol côté tribunes
    names = [__import__('re').search(r'name ([^\r\n]+)', b_) for b_ in open(os.path.join(OUT, 'tileinfo')).read().split('addtile')]
    ix = {m.group(1).strip(): i for i, m in enumerate(names) if m}
    beton, road = ix.get('Beton', ix['Road']), ix['Road']
    tm = np.fromfile(os.path.join(OUT, 'tilemap'), np.uint8); TN = int(np.sqrt(tm.size)); tm = tm.reshape(TN, TN); S2 = 2 * 0.28975
    jj, ii = np.meshgrid(np.arange(TN), np.arange(TN)); cx, cz = (jj + 0.5) * S2, (ii + 0.5) * S2
    m = (cx >= x0) & (cx < x1 - 1) & (cz >= z0) & (cz < z1 - 1)
    gi, gj = np.clip(np.round(cz - z0).astype(int), 0, len(zs) - 1), np.clip(np.round(cx - x0).astype(int), 0, len(xs) - 1)
    fi = map_coordinates(f, [cz - z0, cx - x0], order=1, mode='nearest')
    conc = m & U[gi, gj] & (fi >= 0.0)
    hors = (tm == road) & (cx < xpad - 4.0)
    tm[conc | hors] = beton; tm.astype(np.uint8).tofile(os.path.join(OUT, 'tilemap'))
    return out_p + out_t, (lambda x, z, r=9.5: zone(x, z) and fval(x, z) > -r), (n_t, n_p, int(conc.sum()), int(hors.sum()))


# v39 (Ryan, capture de RF Anaheim 1 : « les planches avec le béton, je veux que ce soit pareil ; nous c'est tout droit, il faut que ce soit
# un peu de travers comme ça ; reprends le même dégradé, de la terre aux planches et des planches au béton ; le béton aussi, qu'il
# ressemble ; c'est A1, tu reprends ») : la bordure de RF Anaheim 1 telle quelle, mesurée sur ses décals (rf_ext/sx2026r01anaheim1/decals) :
#   - béton « concrete.png » : disques de 35 ft, bord fondu, ~13 ft entre voisins, angle au hasard, des planches jusqu'au mur ;
#   - planches « ply.png » : un paquet de 5 plaques OSB posées de travers, décal de 22 ft, tous les 8,6 ft (écart-type des angles
#     0,93 rad : angle au hasard) ; centres à 10,5 ft de la rangée de terre ;
#   - terre « offtrack.png » : disques de 28 ft, bord fondu, tous les 7,2 ft, angle au hasard, sur le bord de la piste ;
#   - ordre d'A1 : béton, puis planches par-dessus, puis terre par-dessus (dégradé terre -> planches -> béton).
# Ici : même ordre, mêmes tailles, mêmes pas, mêmes textures (la terre recolorée à la teinte de notre sol) ; la rangée de planches suit
# le contour de border_v2 (au large des appuis), tout le tour côté tribunes (rien au paddock) ; tuile Beton sous le béton.
A1_OFF = (12.0, 4.0)          # terre : taille, pas (ft) ; v39b : A1 = 28 / 7,2 ft, trop gros pour 20 ft entre piste et mur (recouvrait les planches)
# v39b (Ryan, capture en jeu de la v39 : « les planches montent sur les bosses ; elles sont censées être au sol, à plat ; un peu plus loin
# des bords ; pas sur les appuis, que sur le sol plat ; partout, tout le terrain ») : les paquets d'A1 (22 ft) ne tiennent pas sur le plat
# entre les appuis et le mur (20 ft) -> plaques A1 seules (une plaque OSB 4 x 8 ft de ply.png, décal de 8 ft), posées de travers (angle de
# la piste + écart au hasard, comme le vrac d'A1), centres à >= PL_FLAT ft de tout relief (h > 0,03 ft) : la plaque entière est sur le
# plat ; bande de planches de PL_FLAT à PL_FLAT + PL_BAND ft du relief ; terre d'A1 (disques fondus) le long du pied du relief, par-dessus
# le bord des planches ; au-delà des planches, tuile Beton = texture du béton d'A1 jusqu'au mur
PL_SIZE, PL_STEP, PL_FLAT, PL_BAND, PL_WALL = 8.0, 2.4, 5.5, 8.0, 4.5   # v39c (« entre les planches, parfois le béton s'affiche ») : pas 3,4 -> 2,4 ft   # plaque 4 x 8 ft : demi-diagonale 4,47 ft -> centre à 5,5 ft du relief
PL_JIT = 0.45                 # écart-type de l'angle (rad) autour du sens de la piste
REL_H = 0.03                  # relief : terrain > 0,03 ft


def border_a1_textures(rf_tex, out_dir, dirt_png, beton_png=None):
    """textures A1 dans la piste : plaque seule (planche_a1.png), terre (offtrack recolorée à la teinte de notre sol), et (v39b) la tuile
    Beton refaite avec le béton d'A1 (centre opaque du disque concrete.png, à la taille de l'ancienne tuile)."""
    ply = Image.open(os.path.join(rf_tex, 'ply.png')).convert('RGB').crop((80, 667, 1120, 1187)).rotate(90, expand=True).resize((512, 1024), Image.LANCZOS)
    P = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0)); P.paste(ply, (256, 0))
    d = ImageDraw.Draw(P); d.rectangle([256, 0, 767, 5], fill=(58, 48, 36, 255)); d.rectangle([256, 1018, 767, 1023], fill=(58, 48, 36, 255))
    d.rectangle([256, 0, 261, 1023], fill=(70, 58, 42, 255)); d.rectangle([762, 0, 767, 1023], fill=(70, 58, 42, 255))
    P.save(os.path.join(out_dir, 'planche_a1.png'))
    a = np.asarray(Image.open(os.path.join(rf_tex, 'offtrack.png')).convert('RGBA'), float); m = a[..., 3] > 200
    zm = np.asarray(Image.open(dirt_png).convert('RGB'), float).reshape(-1, 3).mean(0)
    a[..., :3] = np.clip(a[..., :3] * (zm / a[..., :3][m].mean(0)), 0, 255)
    Image.fromarray(a.astype(np.uint8), 'RGBA').save(os.path.join(out_dir, 'a1_offtrack.png'))
    if beton_png and os.path.exists(beton_png):
        beton_tile(os.path.join(rf_tex, 'concrete.png'), beton_png)
    return [round(float(v)) for v in zm]


BETON_MOY = np.array([84.0, 84.0, 82.0])   # v39b (Ryan : « le béton plus foncé et avec de la texture ») : gris moyen de la tuile
BETON_CONTRASTE = 2.2                       # grain du béton d'A1 x 2,2 autour de la moyenne
BETON_TACHES = 30.0                         # taches (variations douces, +/- gris) ; v39c (« le béton n'a pas de texture ») : 14 -> 30
BETON_MOYEN, BETON_GRAIN = 16.0, 14.0       # v39c : grain moyen (~6 px) et fin (~1 px), +/- gris
BETON_JOINTS = 2                            # v39c : joints de dalles sombres (2 x 2 dalles par tuile)


def beton_tile(a1_concrete, out_png, n=512, seed=39):
    """tuile Beton : centre opaque du béton d'A1 (512 px au lieu de 128 : plus de détail), assombrie, grain renforcé, taches douces,
    raccord sans couture (moitié décalée fondue en croix)."""
    from scipy.ndimage import gaussian_filter
    c = np.asarray(Image.open(a1_concrete).convert('RGB').crop((312, 312, 712, 712)).resize((n, n), Image.LANCZOS), float)
    m = c.reshape(-1, 3).mean(0); c = BETON_MOY + (c - m) * BETON_CONTRASTE
    rng = np.random.default_rng(seed)
    t = gaussian_filter(rng.normal(0, 1, (n, n)), n / 14, mode='wrap'); t = t / (np.abs(t).max() or 1) * BETON_TACHES
    g = gaussian_filter(rng.normal(0, 1, (n, n)), 1.2, mode='wrap'); g = g / (g.std() or 1) * BETON_GRAIN / 2
    g2 = gaussian_filter(rng.normal(0, 1, (n, n)), 6.0, mode='wrap'); g2 = g2 / (g2.std() or 1) * BETON_MOYEN / 2
    c = c + (t + g + g2)[..., None]
    r = np.roll(np.roll(c, n // 2, 0), n // 2, 1)                       # raccord : la tuile décalée d'une demie au bord
    y = np.abs(np.arange(n) - n / 2 + 0.5) / (n / 2); w = np.clip(1.0 - np.maximum.outer(y, y), 0, 1) ** 0.6
    c = c * w[..., None] + r * (1 - w[..., None])
    for k in range(BETON_JOINTS):                                        # joints de dalles (sciés), raccord gardé (aux bords de la tuile)
        q = k * n // BETON_JOINTS
        for o, f in ((-1, 0.86), (0, 0.62), (1, 0.86)):
            c[(q + o) % n, :, :] *= f; c[:, (q + o) % n, :] *= f
    Image.fromarray(np.clip(c, 0, 255).astype(np.uint8)).save(out_png)
    return out_png


def _poisson(cells, X, Z, step, rng):
    """points d'un tirage de Poisson (écart mini step) parmi les cases (i, j)."""
    ci = cells.copy(); rng.shuffle(ci); grid = {}; out = []
    for i, j in ci:
        q = np.array([X[i, j], Z[i, j]]); key = (int(q[0] // step), int(q[1] // step))
        if any(np.hypot(*(p_ - q)) < step for dx in (-1, 0, 1) for dz in (-1, 0, 1) for p_ in grid.get((key[0] + dx, key[1] + dz), [])):
            continue
        grid.setdefault(key, []).append(q); out.append((q, i, j))
    return out


def border_a1(OUT, path, fl, xpad, folder, rng, wall_max=32.0):
    """bordure v39b (voir plus haut) -> (décals : planches puis terre par-dessus, filtre des taches de terre, nombres)."""
    from scipy.ndimage import distance_transform_edt, map_coordinates
    from scipy.spatial import cKDTree
    from matplotlib.path import Path as MPath
    t = open(os.path.join(OUT, 'terrain.hf')).read().split(); s_, lo, hi = float(t[1]), float(t[2]), float(t[3])
    Hm = np.asarray(Image.open(os.path.join(OUT, 'terrain.png')), float) / 65535 * (hi - lo) + lo
    fl = np.asarray(fl, float); x0, x1, z0, z1 = fl[:, 0].min() - 2, fl[:, 0].max() + 2, fl[:, 1].min() - 2, fl[:, 1].max() + 2
    st = 0.5; xs, zs = np.arange(x0, x1, st), np.arange(z0, z1, st); X, Z = np.meshgrid(xs, zs)
    h = map_coordinates(Hm, [Z / s_, X / s_], order=1)
    sm = path.samples(0.5); PT = np.c_[sm['x'], sm['z']]; TH = np.asarray(sm['th'])
    dp, ip = cKDTree(PT).query(np.c_[X.ravel(), Z.ravel()]); dp = dp.reshape(X.shape); ip = ip.reshape(X.shape)
    rel = (h > REL_H) | (dp < 15.2)                                       # relief ou couloir
    dr = distance_transform_edt(~rel) * st                                # distance au relief / au couloir (ft)
    floor = MPath(fl).contains_points(np.c_[X.ravel(), Z.ravel()]).reshape(X.shape); dw = distance_transform_edt(floor) * st
    U = floor & (X < xpad - 4.0) & (dw < wall_max)
    line_ = lambda q, a, size, tex: "[%.6f %.6f] %.6f %.6f 1.000000 @%s/rfborder/%s" % (q[0], q[1], a, size, folder, tex)
    # planches : tirage de Poisson (écart PL_STEP) dans la bande plate
    band = U & (dr >= PL_FLAT) & (dr <= PL_FLAT + PL_BAND) & (dw >= PL_WALL)
    ply = []
    for q, i, j in _poisson(np.argwhere(band), X, Z, PL_STEP, rng):
        a = -(TH[ip[i, j]] + np.pi / 2) + rng.normal(0.0, PL_JIT) + (np.pi if rng.random() < 0.5 else 0.0)
        ply.append(line_(q, a, PL_SIZE, 'planche_a1.png'))
    # terre d'A1 : disques fondus de 28 ft tous les 7,2 ft le long du pied du relief, côté tribunes (dégradé terre -> planches)
    foot = U & (dr > 0) & (dr <= st * 1.5)
    off = [line_(q, rng.uniform(-np.pi, np.pi), A1_OFF[0], 'a1_offtrack.png') for q, i, j in _poisson(np.argwhere(foot), X, Z, A1_OFF[1], rng)]
    # tuile Beton (béton d'A1) : sur le plat à >= PL_FLAT - 1 ft du relief côté tribunes, + le béton (Road) hors du sol côté tribunes
    names = [__import__('re').search(r'name ([^\r\n]+)', b_) for b_ in open(os.path.join(OUT, 'tileinfo')).read().split('addtile')]
    ix = {m.group(1).strip(): i for i, m in enumerate(names) if m}
    beton, road = ix.get('Beton', ix['Road']), ix['Road']
    tm = np.fromfile(os.path.join(OUT, 'tilemap'), np.uint8); TN = int(np.sqrt(tm.size)); tm = tm.reshape(TN, TN); S2 = 2 * 0.28975
    jj, ii = np.meshgrid(np.arange(TN), np.arange(TN)); cx, cz = (jj + 0.5) * S2, (ii + 0.5) * S2
    m = (cx >= x0) & (cx < x1 - 1) & (cz >= z0) & (cz < z1 - 1)
    gi, gj = np.clip(np.round((cz - z0) / st).astype(int), 0, len(zs) - 1), np.clip(np.round((cx - x0) / st).astype(int), 0, len(xs) - 1)
    conc = m & U[gi, gj] & (dr[gi, gj] >= PL_FLAT - 1.0)
    hors = (tm == road) & (cx < xpad - 4.0)
    tm[conc | hors] = beton; tm.astype(np.uint8).tofile(os.path.join(OUT, 'tilemap'))
    ij = lambda x, z: (int(np.clip(round((z - z0) / st), 0, len(zs) - 1)), int(np.clip(round((x - x0) / st), 0, len(xs) - 1)))
    under_ply = lambda x, z, r=9.5: bool(U[ij(x, z)]) and float(dr[ij(x, z)]) >= 1.0   # v39b (« remets la texture enlevée ») : seules les taches posées SUR le plat (planches) ; avant : tout le couloir aussi
    # contrôle : aucune planche ne touche le relief (plaque de 4 x 8 ft : rayon 4,5 ft)
    hmax = 0.0
    for l in ply:
        x_, z_ = float(l.split()[0][1:]), float(l.split()[1][:-1])
        for a_ in np.linspace(0, 2 * np.pi, 16, endpoint=False):
            for r_ in (0.0, 2.3, 4.5):
                hmax = max(hmax, float(map_coordinates(Hm, [[(z_ + r_ * np.sin(a_)) / s_], [(x_ + r_ * np.cos(a_)) / s_]], order=1)[0]))
    assert hmax <= 0.05, ("planche sur le relief", hmax)
    return ply + off, under_ply, dict(planches=len(ply), terre=len(off), cases_beton=int(conc.sum()), relief_max_sous_planches=round(hmax, 3))


def monster_griffe():
    """v39c : griffe Monster envoyée par Ryan (commun/assets/logos/user/monster_griffe.webp), fond blanc enlevé depuis les bords."""
    from scipy import ndimage
    U = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'commun', 'assets', 'logos', 'user')
    a = np.asarray(Image.open(os.path.join(U, 'monster_griffe.webp')).convert('RGBA')).astype(int)
    bg = (a[..., :3].min(-1) > 225) | (a[..., 3] < 20); lab, _ = ndimage.label(bg)
    edge = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    a[..., 3] = np.where(np.isin(lab, list(edge)), 0, 255)
    im = Image.fromarray(a.astype(np.uint8), 'RGBA'); return im.crop(im.getbbox())


MONSTER_MARGIN = (0.8, 0.7, 0.6)   # marges du logo Monster sur le flanc (ft) : côté lèvre, bas, sous le bord du dessus


def ramp_sides_monster(statue_dir, variants=(('ramp_50', 1.0),)):
    """v39b (Ryan, photo de Paris : « sur les sauts freestyle, il faut le logo Monster ») : logo Monster (griffe + MONSTER ENERGY) sur les
    2 flancs des tremplins FMX, à l'endroit des 2 côtés, jamais déformé. Le modèle ramp_50 donnait aux 2 flancs la même zone de texture
    (le flanc -x la voyait la tête en bas) : texture 1024 x 1024 (quart haut gauche = l'ancienne texture : dessus noir + tête Venum ;
    quart bas gauche = flanc +x, lèvre à droite ; quart bas droit = flanc -x, lèvre à gauche) et UV refaits ; une texture par hauteur de
    tremplin (variants : (nom, k) ; k = hauteur x k de ramp_tall), le logo dessiné à l'échelle réelle du flanc. -> {nom: png}"""
    base = Image.open(os.path.join(statue_dir, 'ramp_50.png')).convert('RGB').resize((512, 512), Image.LANCZOS)
    logo = monster_griffe(); asp = logo.size[0] / logo.size[1]
    out = {}
    for name, k in variants:
        p = os.path.join(statue_dir, name + '.jm'); L = open(p).read().split(chr(10)); nv = int(L[2].split()[0])
        V = np.array([[float(t) for t in L[3 + i].split()] for i in range(nv)])
        Lz, Hy = -float(V[:, 2].min()), float(V[:, 1].max())
        side = np.abs(np.abs(V[:, 3]) - 1.0) < 0.05
        zs = np.linspace(-Lz, 0.0, 200); topz = np.array([V[side & (np.abs(V[:, 2] - z) < 0.6), 1].max(initial=0.0) for z in zs])
        topz = np.maximum.accumulate(topz[::-1])[::-1]                      # hauteur du flanc (décroît de la lèvre au pied)
        top = lambda z: float(np.interp(z, zs, topz))
        ml, mb, mt = MONSTER_MARGIN; best = None
        for h in np.arange(0.5, Hy, 0.05):                                  # le plus grand logo sous le bord, collé côté lèvre
            w = h * asp; z1 = -Lz + ml + w
            if z1 > 0 or top(z1) < mb + h + mt:
                break
            best = (h, w)
        h, w = best
        pxu, pxv = 512.0 / Lz, 512.0 / Hy                                   # px par ft dans un quart de texture
        lg = logo.resize((max(1, int(w * pxu)), max(1, int(h * pxv))), Image.LANCZOS)
        im = Image.new('RGB', (1024, 1024), (14, 14, 15)); im.paste(base, (0, 0))
        yb = 1024 - int((mb + h) * pxv)
        im.paste(lg, (512 - int((ml + w) * pxu), yb), lg)                  # flanc +x : lèvre à droite du quart bas gauche
        im.paste(lg, (512 + int(ml * pxu), yb), lg)                        # flanc -x : lèvre à gauche du quart bas droit
        # v39c (« sur chaque côté de la rampe : gauche, derrière et droite ») : dos (sous la lèvre, z = -Lz) = quart haut droit
        xs_ = V[np.abs(V[:, 5] + 1.0) < 0.1][:, 0]; Wx = float(xs_.max() - xs_.min()) if len(xs_) else 4.0
        pbu, pbv = 512.0 / Wx, 512.0 / Hy; hb = min(Hy - 1.2, (Wx - 0.5) / asp); wb = hb * asp
        lgb = logo.resize((max(1, int(wb * pbu)), max(1, int(hb * pbv))), Image.LANCZOS)
        im.paste(lgb, (512 + (512 - lgb.size[0]) // 2, int(512 - (Hy - 0.6) * pbv)), lgb)
        im = K.grain(im, 1.0); im.save(os.path.join(statue_dir, name + '.png'))
        for i in range(nv):
            v_ = L[3 + i].split()
            x, y, z, nx = float(v_[0]), float(v_[1]), float(v_[2]), float(v_[3])
            if side[i]:
                t = -z / Lz                                                 # 0 = pied, 1 = lèvre
                u = 0.5 * t if nx > 0 else 0.5 + 0.5 * (1.0 - t)
                v = 0.5 * y / Hy
            elif float(v_[5]) < -0.9:                                       # dos : vu de derrière, la droite = -x
                u = 0.5 + 0.5 * (float(xs_.max()) - x) / Wx
                v = 0.5 + 0.5 * y / Hy
            else:
                u, v = float(v_[6]) * 0.5, 0.5 + float(v_[7]) * 0.5
            v_[6], v_[7] = '%.6f' % min(max(u, 0.001), 0.999), '%.6f' % min(max(v, 0.001), 0.999)
            L[3 + i] = ' '.join(v_)
        open(p, 'w', newline=chr(10)).write(chr(10).join(L))
        out[name] = dict(png=name + '.png', logo_ft=(round(w, 1), round(h, 1)), k=k)
    return out
