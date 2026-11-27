"""v41e (« rajoute des flammes au départ : à chaque tombée de grille, des flammes des deux côtés, accrochées au panneau START en haut ;
et au panneau FINISH au-dessus de l'arrivée : quand le premier passe au 2e tour, et à l'arrivée quand le premier passe la ligne ») :

- les flammes de Saint-Thibéry (pyro de l'arche d'arrivée de SX1 : js/pyro/finishflames + finishflames2, 41 images, et son son
  startflame.raw), une à chaque bout du panneau, posées sur son bord haut ;
- 4 panneaux (billboards) mis en tête du fichier billboards : 0, 1 = START ; 2, 3 = FINISH ; cachés (alpha 0) hors des tirs ;
- script ajouté à frills.js ET nofrills.js (le jeu lit l'un ou l'autre) : START à chaque chute de grille ; FINISH quand le premier
  finit le 1er tour, et quand le premier finit la course (tours : nombre de tours ; temps + tours : tours faits à la fin du temps + 1
  + tours en plus, comme le classement de l'écran géant).
Statues : y relatif au sol sous leur origine ; billboards : y relatif au sol sous eux.
"""
import os
import re
import shutil
import numpy as np
from PIL import Image

FL_TAILLE = 24.0          # hauteur d'une flamme (ft)
FL_DEBORD = 1.0           # au-delà du bout du panneau (ft)
FL_FPS = 32.0
PANNEAUX = (('start', '/statue/paris/start_banner.jm'), ('finish', '/statue/paris/finish.jm'))


def _jm_panneau(path):
    L = open(path).read().split('\n'); nv = int(L[2].split()[0])
    V = np.array([[float(t) for t in L[3 + i].split()[:3]] for i in range(nv)]); P = V[V[:, 1] < 60.0]   # sans les câbles
    return P[:, 0].min(), P[:, 0].max(), P[:, 1].max(), P[:, 2].mean()


def flammes(OUT, FOLDER, root):
    src = os.path.join(root, 'tracks', 'USLAND2026SaintThiberybyBazo', 'js')
    pd = os.path.join(OUT, 'js', 'pyro'); sd = os.path.join(OUT, 'js', 'sounds'); os.makedirs(pd, exist_ok=True); os.makedirs(sd, exist_ok=True)
    for nm in ('finishflames', 'finishflames2'):
        if os.path.exists(os.path.join(pd, nm)):
            shutil.rmtree(os.path.join(pd, nm))
        shutil.copytree(os.path.join(src, 'pyro', nm), os.path.join(pd, nm))
    seq = {nm: open(os.path.join(src, 'pyro', nm + '.seq')).read().replace('@USLAND2026SaintThiberybyBazo/', '@%s/' % FOLDER) for nm in ('finishflames', 'finishflames2')}
    shutil.copy(os.path.join(src, 'sounds', 'startflame.raw'), os.path.join(sd, 'flamme.raw'))
    t = open(os.path.join(OUT, 'terrain.hf')).read().split(); s_, lo, hi = float(t[1]), float(t[2]), float(t[3])
    H = np.asarray(Image.open(os.path.join(OUT, 'terrain.png')), float) / 65535 * (hi - lo) + lo
    h = lambda x, z: float(H[int(round(z / s_)), int(round(x / s_))])
    st = open(os.path.join(OUT, 'statues')).read().split('\n'); bb, pos, rep = [], [], {}
    for key, jm in PANNEAUX:
        l = next(l for l in st if '@%s%s ' % (FOLDER, jm) in l)
        m = re.match(r'\[([-0-9.]+) ([-0-9.]+) ([-0-9.]+)\] ([-0-9.]+)', l); x, y, z, a = (float(m.group(i)) for i in (1, 2, 3, 4))
        x0, x1, top, zc = _jm_panneau(os.path.join(OUT, jm.lstrip('/')))
        ex, ez = np.array([np.cos(a), -np.sin(a)]), np.array([np.sin(a), np.cos(a)])   # +x / +z locaux dans le monde
        g0 = h(x, z) + y + top                                                          # haut du panneau (absolu)
        for k, (lx, nm) in enumerate(((x1 + FL_DEBORD, 'finishflames2'), (x0 - FL_DEBORD, 'finishflames'))):
            q = np.array([x, z]) + ex * lx + ez * zc; f_ = '%s_%d' % (key, k)
            open(os.path.join(pd, 'flamme_%s.seq' % f_), 'w', newline='\n').write(seq[nm])
            bb.append('[%.6f %.6f %.6f] %.6f 1.000000 @%s/js/pyro/flamme_%s.seq' % (q[0], g0 - h(*q), q[1], FL_TAILLE, FOLDER, f_))
            pos.append((q[0], g0, q[1]))
        rep[key] = [tuple(np.round(p, 1)) for p in pos[-2:]]
    old = [l for l in open(os.path.join(OUT, 'billboards')).read().split('\n') if l.strip()]
    open(os.path.join(OUT, 'billboards'), 'w', newline='\n').write('\n'.join(bb + old) + '\n')
    js = JS.replace('@FOLDER', '@' + FOLDER).replace('FL_POS_', ', '.join('[%.2f, %.2f, %.2f]' % p for p in pos)).replace('FL_FPS_', '%.1f' % FL_FPS)
    n = 0
    for f in ('frills.js', 'nofrills.js'):
        p = os.path.join(OUT, f)
        if os.path.exists(p):
            open(p, 'a', newline='\n').write(js); n += 1
    rep['scripts'] = n
    return rep


JS = r'''
/*
USLAND Paris v41e - flammes : panneau START (billboards 0, 1) a chaque chute de grille ; panneau FINISH (billboards 2, 3) quand le
premier finit le 1er tour et quand il finit la course. Texte ASCII expres.
*/
var FL_POS = [FL_POS_];
var FL_TEX = [mx.read_texture("@FOLDER/js/pyro/flamme_start_0.seq"), mx.read_texture("@FOLDER/js/pyro/flamme_start_1.seq"),
              mx.read_texture("@FOLDER/js/pyro/flamme_finish_0.seq"), mx.read_texture("@FOLDER/js/pyro/flamme_finish_1.seq")];
var FL_SND = [];
var FL_N = 41, FL_FPS = FL_FPS_;
var FL_FIN_TOURS = mx.get_finish_laps(), FL_FIN_TEMPS = mx.get_finish_time();
var fl_k;
for (fl_k = 0; fl_k < 4; fl_k++) {
    FL_SND[fl_k] = mx.add_sound("@FOLDER/js/sounds/flamme.raw");
    mx.set_sound_freq(FL_SND[fl_k], 44100);
    mx.set_sound_vol(FL_SND[fl_k], 1.0);
    mx.set_sound_pos(FL_SND[fl_k], FL_POS[fl_k][0], FL_POS[fl_k][1], FL_POS[fl_k][2]);
    mx.color_billboard(fl_k, 1, 1, 1, 0);
}
var fl_img = [-1, -1], fl_t = [-1.0, -1.0];
var fl_grille = -1, fl_tour = 0, fl_tour_fin_temps = -1, fl_prec_s = -1.0;

function fl_montre(g, a) {
    mx.color_billboard(2 * g, 1, 1, 1, a);
    mx.color_billboard(2 * g + 1, 1, 1, 1, a);
}
function fl_tire(g) {
    fl_img[g] = 0; fl_t[g] = -1.0;
    mx.start_sound(FL_SND[2 * g]);
    mx.start_sound(FL_SND[2 * g + 1]);
}
function fl_tours_course() {
    if (FL_FIN_TEMPS > 0) return fl_tour_fin_temps >= 0 ? fl_tour_fin_temps + 1 + FL_FIN_TOURS : 1000000;
    return FL_FIN_TOURS > 0 ? FL_FIN_TOURS : 1000000;
}
function fl_image(seconds) {
    try {
        var d = mx.get_gate_drop_time(), g, k, o, tour;
        if (mx.seconds < fl_prec_s) { fl_img = [-1, -1]; fl_montre(0, 0); fl_montre(1, 0); }      /* retour en arriere (replay) */
        fl_prec_s = mx.seconds;
        if (d < 0 || mx.seconds < d) {
            fl_grille = -1; fl_tour = 0; fl_tour_fin_temps = -1;
        } else {
            if (fl_grille != d && mx.seconds < d + 3.0) { fl_grille = d; fl_tour = 0; fl_tour_fin_temps = -1; fl_tire(0); }
            o = mx.get_running_order();
            if (o.length > 0 && o[0].position >= 1) {
                tour = mx.index_to_lap(o[0].position);
                if (FL_FIN_TEMPS > 0 && fl_tour_fin_temps < 0 && mx.seconds - d >= FL_FIN_TEMPS) fl_tour_fin_temps = tour;
                if (tour > fl_tour) {
                    if (tour == 1 || tour == fl_tours_course()) fl_tire(1);
                    fl_tour = tour;
                }
            }
        }
        for (g = 0; g < 2; g++) {
            if (fl_img[g] < 0 || (fl_t[g] >= 0 && mx.seconds - fl_t[g] < 1.0 / FL_FPS)) continue;
            fl_t[g] = mx.seconds;
            if (fl_img[g] < FL_N) {
                for (k = 2 * g; k < 2 * g + 2; k++) {
                    mx.begin_custom_frame(FL_TEX[k]);
                    mx.paste_custom_frame(FL_TEX[k], fl_img[g], 0.0, 0.0, 0.0, 0.0, 1.0, 1.0);
                    mx.end_custom_frame(FL_TEX[k]);
                }
                if (fl_img[g] == 0) fl_montre(g, 1);
                fl_img[g]++;
            } else {
                fl_montre(g, 0); fl_img[g] = -1;
            }
        }
    } catch (e) { mx.message("flammes : " + e.toString()); }
    if (fl_prev) fl_prev(seconds);
}
var fl_prev = mx.frame_handler;
mx.frame_handler = fl_image;
'''
