"""Classement EN DIRECT sur TOUT l'écran géant du fond (paddock26.screen).

v39 (Ryan, capture de la retransmission « Supercross Paris 2026 - jour 1 » : « la même DA pour les résultats sur l'écran, en direct : le
temps en haut, les résultats ») ; v39b (capture en jeu de la v39 : la colonne s'affiche ; « les résultats doivent être sur tout le grand
écran, avec nos noms ; ça doit marcher quand on roule en course ») : l'écran (210 x 56 ft) = 4 panneaux carrés côte à côte :
  1. logo Supercross Paris, « CLASSEMENT LIVE », le temps restant dans la case gris foncé à filet blanc (« 04:32 + 1L ») ;
  2. 3. 4. les places 1-8, 9-16, 17-22 (22 grilles) : place dans une case blanche, filet à la couleur de la marque, numéro en rose
     (« 57. »), nom du pilote en blanc (dernier mot du nom, 9 lettres au plus) ; logo USLAND en bas du panneau 4.

Fait EXACTEMENT comme la tour de classement de ZION 2025 Supercross Paris, qui marche en jeu (et la v39 l'a montré : la colonne
s'affichait) : textures « ANIM1 1 2 512 0 » de 2 images 256 x 512 (page 0 : fonds ; page 1 : polices et filets), dessin
(mx.begin_custom_frame / paste_custom_frame / end_custom_frame) À CHAQUE IMAGE du jeu ; 2 textures (direct_a : panneaux 1-2,
direct_b : panneaux 3-4), chaque panneau = un carré 256 x 256 de l'image ; mêmes calculs de temps / tours restants que ZION.

  tableau_direct.make(OUT, FOLDER, x, z, yaw)  -> ligne de statue à ajouter + écrit les fichiers et frills.js
"""
import os
import re
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SUB = "statue/paris/direct"
PW, PH = 256, 512                       # pages (comme ZION : 256 x 512) ; 2 panneaux carrés de 256 par image
NPAN = 8                                # rangées par panneau de classement
ROW_H = 32
POS_X0, POS_X1 = 4, 40                  # case blanche de la place
BAR_X0, BAR_X1 = 44, 50                 # filet de la marque
NUM_X = 55                              # numéro (rose)
NAME_X = 116                            # nom (blanc)
NAME_MAX = 9
FONT_B = r"C:/Windows/Fonts/ariblk.ttf"     # Arial Black (gras, comme l'habillage TV)
NOM = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-'.:+"   # v44 : « : » et « + » (temps du meilleur tour, places gagnées)
NUM = "0123456789.-ABCDEFGHIJKLMNOPQRSTUVWXYZ'"   # v43d : « - » après le numéro ; v45b : lettres roses (« 202 - OPPLIGER » du meilleur tour)
POS = "0123456789"
TEMPS = "0123456789:+L.-"              # v45 : « . » et « - » (meilleur tour 1:52.341, « -:--.--- » avant le 1er)
VIOLET, VIOLET2, ROSE = (34, 10, 52), (52, 16, 78), (236, 48, 196)
BANDES = dict(honda=(214, 24, 36), ktm=(250, 110, 0), kawasaki=(60, 180, 60), yamaha=(30, 70, 210), suzuki=(245, 205, 0),
              husqvarna=(235, 238, 244), gasgas=(200, 20, 40), triumph=(120, 120, 128), none=(150, 60, 190))
MARQUES = [(r"^crf?[0-9]+", "honda"), (r"^[0-9]+sx", "ktm"), (r"^kx[0-9]+", "kawasaki"), (r"^yz[0-9]+", "yamaha"),
           (r"^rmz?[0-9]+", "suzuki"), (r"^fc[0-9]+", "husqvarna"), (r"^mc[0-9]+", "gasgas"), (r"^tf[0-9]+", "triumph")]
# panneaux : (texture, y du carré dans l'image, première place affichée ou None = panneau du temps)
PANNEAUX = [("a", 0, None), ("a", 256, 1), ("b", 0, 9), ("b", 256, 17)]
TIME_BOX = (16, 150, 240, 240)          # case du temps dans le panneau 1 (px du carré)
TIME_Y = 168
TIME_FILET = False                      # v45b : filet blanc de la case du temps enlevé
# v45 (Ryan : « top 10 A, mais à droite je veux le meilleur temps seul, rien d'autre ») : proposition A (apercu_top10.prop_a) :
# panneaux 2 + 3 = 10 lignes en bandeau (place en case blanche, numéro en pastille rose, nom, écart au leader à droite ; leader en
# rose, pastille blanche) ; panneau 4 = la carte du meilleur tour, seule (plus de nom, plus de logo).
A_N, A_H, A_Y0 = 10, 25, 3              # lignes, hauteur, haut de la 1re ligne (px du carré)
A_DY = -2                               # cellule de police (26 px) centrée sur la bande (22 px)
A_X0 = 6                                # début de la bande (panneau 2)
A_PLACE = (9, 43)                       # case blanche de la place (panneau 2)
A_PILL = (55, 109)                      # pastille du numéro (panneau 2)
A_NOM_X, A_NOM_X1 = 117, 252            # nom (panneau 2 seulement : lettres en trop enlevées)
A_BANDE_X1, A_PENTE = 250, 10           # fin de la bande en biais (panneau 3)
A_ECART_X1 = 232                        # bord droit de l'écart (panneau 3)
VIOLET3 = (74, 24, 110)
MT_CARTE = (10, 58, 246, 198)           # carte du meilleur tour (panneau 4)
# v45c : DA E (proposition retenue) : cadre de A sans ses 2 filets, police Bahnschrift gras condensé, classement de C
DA_E = True
DA_CHRONO = True                        # v45d (photo d'un écran de chrono SX2) : tableau de chronométrage (tableau_chrono.py), remplace la DA E
FONT_E, FONT_E_STYLE = r"C:/Windows/Fonts/bahnschrift.ttf", "Bold Condensed"
E_FOND, E_LIGNE, E_ROSE, E_GRIS, E_GRIS2 = (16, 16, 20), (26, 26, 32), (236, 48, 140), (140, 140, 150), (160, 160, 170)
E_H, E_Y0 = 25, 3                       # lignes du classement (px du carré)
E_PLACE_X1, E_NUM_X, E_NOM_X, E_NOM_X1, E_ECART_X1 = 28, 44, 92, 252, 240   # place (bord droit, rose), numéro, nom (panneau 2) ; écart (bord droit, panneau 3)
E_MT_X, E_MT_Y, E_MT_NOM_Y = 20, 96, 159   # panneau 4 : temps (haut de la cellule de 56 px) et pilote, alignés à gauche
E_TIME_Y = 168                          # panneau 1 : haut de la cellule du temps
E_EV_Y = (147, 177, 205)                # panneau 1, fin de course : titre (rose), numéro + nom (blanc), valeur (gris)
MT_TITRE = "FASTEST LAP"
MT_Y = 98                               # haut de la cellule (56 px) du temps
MT_NOM_Y = 156                          # v45b (« laisse 202 - OPPLIGER ») : numéro - nom du meilleur tour, en rose, sous le temps
# v44 (« holeshot avec le nom du pilote sur le grand écran ; à l'arrivée le vainqueur ; les récompenses en fin de manche ; son de la
# grille ; le public sur les chutes et les bagarres ; refais notre propre code ») : module d'événements (code USLAND, écrit ici)
EV_Y = (147, 177, 205)                  # v45c (DA E) : titre, numéro + nom, valeur sous « LIVE » ; v44 : (164, 189, 213) dans la case du temps
EV_HS_INDEX = 2                         # holeshot : 1er à passer 2 portes (porte 28, entrée du 1er virage ; la 27 est au milieu de la ligne droite)
EV_VOL = dict(grille=1.5, public=1.0, ooh=1.0, foule=1.0, foule_fin=0.25, annonce=1.0, hp=0.5, mus=1.0, mus_hp=0.4)
# v45h (« le bruit du public et ses réactions, c'est à 4 : mets à 2,5 ; la musique, laisse ») : foule, clameur et « ooh » x 2,5 / 4
PUBLIC_K = 2.5 / 4.0
for k_ in ("public", "ooh", "foule", "foule_fin"):
    EV_VOL[k_] = round(EV_VOL[k_] * PUBLIC_K, 3)
EV_COPIES = dict(public=3, mus=2)   # v45i : volume plafonné à 1 dans le jeu -> plus fort = plusieurs copies au même point (pas d'écho)   # sons RF (pack sx2026) : clameur rms ~1100 (RF la joue à 25), grille rms ~2400 ; v45e (Ryan : « la foule j'entends rien ; chaque micro en décalé, trop ») : foule normalisée (x9) à 4, son principal à la caméra, hauts-parleurs bas (léger écho) ; v45g (« pas assez fort », chutes pas entendues) : chanson x2, clameur normalisée (x3,8) à 8 ; v45h : grille inchangée (1.5), foule 4 -> 1 après l'arrivée
MUSIQUE_FIN, MUSIQUE_FONDU = 79.4, 7.0   # v45i (« coupe la chanson avant le 2e couplet, après les 3 "thunder strike" vers 1:10 ; un
# fondu de 7 s pour la fin ») : paroles transcrites (Whisper, sur le PC) : « Thunder strike! » à 62,0 / 67,2 / 71,5 s (le 3e fini à 72,3 s),
# 2e couplet à 79,5 s (« And we're in Paris... ») -> fondu de 7 s de 72,4 à 79,4 s, coupée là
MUSIQUE = os.path.join(HERE, "sons", "musique_paris.raw")       # v45d : chanson FIVE - SX Paris 2022 (locale seulement, voir _bloc_musique)
SONS_RF = os.path.join(os.path.dirname(os.path.dirname(HERE)), "commun", "assets", "sons_rf")
EV_JS = r"""
/*
USLAND Paris - evenements de course (code USLAND, v44) : son de la grille, holeshot (ecran + public), vainqueur et recompenses
de fin de manche sur l'ecran geant (vainqueur, holeshot, hard charger, meilleur tour), public sur les chutes du top 3 et les
bagarres (depassements dans le top 3). Texte ASCII expres.
*/
var EV_Y = [EVY0, EVY1, EVY2];
var EV_HS_INDEX = EVHS;
var EV_HS_DUREE = 10.0, EV_ROT = 5.0, EV_APRES_DEPART = 20.0, EV_PAUSE_PUBLIC = 10.0;
var EV_FIN_TOURS = mx.get_finish_laps(), EV_FIN_TEMPS = mx.get_finish_time();
function ev_son(f, vol, freq) {
    var i = mx.add_sound(f);
    if (i >= 0) { mx.set_sound_freq(i, freq); mx.set_sound_vol(i, vol); mx.set_sound_loop(i, 0); }
    return i;
}
var EV_S_GRILLE = ev_son("@FOLDER/js/sounds/grille.raw", EVVG, 44100);
function ev_sons(f, vol, freq, n) { var k, a = []; for (k = 0; k < n; k++) a.push(ev_son(f, vol, freq)); return a; }
var EV_S_PUBLIC = ev_sons("@FOLDER/js/sounds/public.raw", EVVP, 44100, EVNP);   /* v45i : copies a la camera (volume plafonne a 1) */
var EV_S_OOH = ev_sons("@FOLDER/js/sounds/public.raw", EVVO, 33075, EVNP);
var EV_S_ANNONCE = ev_son("@FOLDER/js/sounds/annonce.raw", EVVA, 44100);   /* v44c : annonce "le plus beau supercross du monde, c est Paris" */
var EV_HP = [[0, 0, 0]];                                              /* v44d : hauts-parleurs au-dessus de la piste (remplace par le build) */
var EV_S_HP = [], ev_k;
for (ev_k = 0; ev_k < EV_HP.length; ev_k++) {
    EV_S_HP.push(ev_son("@FOLDER/js/sounds/annonce.raw", EVVH, 44100));
    if (EV_S_HP[ev_k] >= 0) mx.set_sound_pos(EV_S_HP[ev_k], EV_HP[ev_k][0], EV_HP[ev_k][1], EV_HP[ev_k][2]);
}
function ev_hauts_parleurs() {                                         /* l'annonce part de chaque haut-parleur + un peu a la camera */
    var k;
    if (EV_S_MUS.length) { ev_mus_t = mx.seconds; return; }            /* v45f : la chanson complete seule (plus l'extrait de 20 s avant) */
    for (k = 0; k < EV_S_HP.length; k++) if (EV_S_HP[k] >= 0) mx.start_sound(EV_S_HP[k]);
    ev_joue(EV_S_ANNONCE);
}
/*EV_MUSIQUE*/
var EV_ANNONCE_MAX = 120.0;                                           /* si un pilote ne finit jamais (abandon) : annonce 120 s apres le vainqueur */
var EV_S_FOULE = ev_son("@FOLDER/js/sounds/foule.raw", EVVF, 44100);  /* v44b : bruit du public en continu, suit la camera */
var EV_FOULE_DUREE = EVFD, ev_foule_t = -1000, ev_foule_v = EVVF;
var EV_FOULE_FIN = EVFF;                                              /* v45h : foule plus basse apres l'arrivee (la chanson par-dessus) */                        /* v45c : relance a chaque fin (pas de boucle du jeu, pas au chargement) */
function ev_foule() {
    if (EV_S_FOULE < 0) return;
    mx.set_sound_pos(EV_S_FOULE, ev_p[0], ev_p[1], ev_p[2]);
    if ((ev_fin_t >= 0 ? EV_FOULE_FIN : EVVF) != ev_foule_v) {        /* volume change : on relance a ce volume */
        ev_foule_v = ev_fin_t >= 0 ? EV_FOULE_FIN : EVVF;
        mx.stop_sound(EV_S_FOULE); mx.set_sound_vol(EV_S_FOULE, ev_foule_v); ev_foule_t = -1000;
    }
    if (mx.seconds < ev_foule_t || mx.seconds - ev_foule_t >= EV_FOULE_DUREE) { ev_foule_t = mx.seconds; mx.start_sound(EV_S_FOULE); }
}
var ev_p = [0, 0, 0], ev_r = [1, 0, 0, 0, 1, 0, 0, 0, 1];
var ev_d = -2, ev_grille = -1, ev_hs = -1, ev_hs_t = -1, ev_fin_t = -1, ev_tour_temps = -1, ev_public_t = -100;
var ev_fin_tv = -1, ev_annonce = 0;
var ev_mus_t = -1, ev_mus_fin = -1;
function ev_mus_stop() { var k; if (ev_mus_fin < 0) return; for (k = 0; k < EV_S_MUS.length; k++) if (EV_S_MUS[k] >= 0) mx.stop_sound(EV_S_MUS[k]); ev_mus_fin = -1; }
function ev_musique() {                                                /* v45d : chanson sur les hauts-parleurs + une copie qui suit la camera */
    var k;
    if (ev_mus_t >= 0 && mx.seconds >= ev_mus_t) {
        ev_mus_t = -1; ev_mus_fin = mx.seconds + EV_MUS_DUREE;
        for (k = 0; k < EV_S_MUS.length; k++) if (EV_S_MUS[k] >= 0) mx.start_sound(EV_S_MUS[k]);
    }
    if (ev_mus_fin >= 0 && mx.seconds > ev_mus_fin) ev_mus_fin = -1;
    if (ev_mus_fin >= 0) for (k = 0; k < EV_S_MUS_CAM.length; k++) if (EV_S_MUS_CAM[k] >= 0) mx.set_sound_pos(EV_S_MUS_CAM[k], ev_p[0], ev_p[1], ev_p[2]);
}
var ev_top = [], ev_bas = {}, ev_prec_s = -1, ev_rec = null, ev_rec_t = -1;

function ev_joue(i) {
    var k;
    if (typeof i == "object") { for (k = 0; k < i.length; k++) ev_joue(i[k]); return; }
    if (i >= 0) { mx.set_sound_pos(i, ev_p[0], ev_p[1], ev_p[2]); mx.start_sound(i); }
}
function ev_public(i) { if (mx.seconds - ev_public_t >= EV_PAUSE_PUBLIC) { ev_public_t = mx.seconds; ev_joue(i); } }
function ev_nom(slot) { return td_nom(mx.get_rider_name(slot)); }
function ev_num(slot) { return mx.get_rider_number(slot).toString() + " -"; }
function ev_reset() { ev_hs = -1; ev_hs_t = -1; ev_fin_t = -1; ev_tour_temps = -1; ev_top = []; ev_bas = {}; ev_rec = null; ev_rec_t = -1; ev_fin_tv = -1; ev_annonce = 0; ev_mus_t = -1; ev_mus_stop(); }
function ev_tours_course() {
    if (EV_FIN_TEMPS > 0) return ev_tour_temps >= 0 ? ev_tour_temps + 1 + EV_FIN_TOURS : 1000000;
    return EV_FIN_TOURS > 0 ? EV_FIN_TOURS : 1000000;
}
function ev_temps(t) { var m = Math.floor(t / 60), s = t - 60 * m; return m + ":" + (s < 10 ? "0" : "") + s.toFixed(1); }
function ev_recompenses(o) {
    var i, j, k, n, t, t1, t2, r = {}, l1 = mx.lap_to_index(1), dep = [], best = 1e9;
    r.vainqueur = o[0].slot; r.holeshot = ev_hs;
    /* hard charger : places gagnees entre la fin du 1er tour (ordre de passage sur la ligne) et maintenant */
    for (i = 0; i < o.length; i++) { t = mx.get_timing(o[i].slot, l1); if (t >= 0) dep.push([t, o[i].slot]); }
    dep.sort(function (a, b) { return a[0] - b[0]; });
    r.charger = -1; r.gain = 0;
    for (j = 0; j < dep.length; j++)
        for (i = 0; i < o.length; i++) if (o[i].slot == dep[j][1] && j - i > r.gain) { r.gain = j - i; r.charger = o[i].slot; }
    /* meilleur tour : tours complets a partir du 2e (le 1er part de la grille) */
    r.mt = -1;
    for (i = 0; i < o.length; i++) {
        n = mx.index_to_lap(o[i].position);
        for (k = 1; k < n; k++) {
            t1 = mx.get_timing(o[i].slot, mx.lap_to_index(k)); t2 = mx.get_timing(o[i].slot, mx.lap_to_index(k + 1));
            if (t1 >= 0 && t2 > t1 && t2 - t1 < best) { best = t2 - t1; r.mt = o[i].slot; }
        }
    }
    r.mt_t = best;
    return r;
}
function ev_tous_finis(o) {                                          /* chacun a repasse la ligne apres le vainqueur */
    var i, t;
    for (i = 0; i < o.length; i++) {
        t = mx.get_timing(o[i].slot, mx.lap_to_index(mx.index_to_lap(o[i].position)));
        if (!(t >= ev_fin_tv - 0.001)) return false;
    }
    return true;
}
function ev_maj() {
    var d = mx.get_gate_drop_time(), o, i, tour, top;
    mx.get_camera_location(ev_p, ev_r);
    ev_foule();
    ev_musique();
    if (mx.seconds < ev_prec_s) { ev_reset(); ev_grille = -1; }          /* retour en arriere (replay) */
    ev_prec_s = mx.seconds;
    if (d != ev_d) { ev_d = d; ev_reset(); }                          /* nouvelle course */
    if (d < 0 || mx.seconds < d) return;
    if (ev_grille != d && mx.seconds < d + 1.0) { ev_grille = d; ev_joue(EV_S_GRILLE); }
    o = mx.get_running_order();
    if (!o.length) return;
    if (ev_hs < 0 && o[0].position >= EV_HS_INDEX) { ev_hs = o[0].slot; ev_hs_t = mx.seconds; ev_public(EV_S_PUBLIC); }
    tour = mx.index_to_lap(o[0].position);
    if (EV_FIN_TEMPS > 0 && ev_tour_temps < 0 && mx.seconds - d >= EV_FIN_TEMPS) ev_tour_temps = tour;
    if (ev_fin_t < 0 && o[0].position >= 1 && tour >= ev_tours_course()) { ev_fin_t = mx.seconds; ev_fin_tv = mx.get_timing(o[0].slot, mx.lap_to_index(tour)); ev_public_t = -100; ev_public(EV_S_PUBLIC); }
    if (ev_fin_t >= 0) {
        if (ev_rec_t < 0 || mx.seconds - ev_rec_t >= 1.0) { ev_rec = ev_recompenses(o); ev_rec_t = mx.seconds; }
        if (!ev_annonce && (ev_tous_finis(o) || mx.seconds - ev_fin_t >= EV_ANNONCE_MAX)) { ev_annonce = 1; ev_hauts_parleurs(); }
        return;
    }
    if (mx.seconds - d < EV_APRES_DEPART) return;
    top = [];
    for (i = 0; i < 3 && i < o.length; i++) {
        top.push(o[i].slot);
        if (mx.get_rider_down(o[i].slot)) {                           /* chute dans le top 3 */
            if (!ev_bas[o[i].slot]) { ev_bas[o[i].slot] = 1; ev_public(EV_S_OOH); }
        } else ev_bas[o[i].slot] = 0;
    }
    if (ev_top.length == top.length)                                  /* bagarre : depassement dans le top 3 */
        for (i = 0; i < top.length; i++) if (top[i] != ev_top[i]) { ev_public(EV_S_PUBLIC); break; }
    ev_top = top;
}
function ev_ecran() {                                                 /* [titre, numero, nom, valeur] ou null (temps de course) */
    var k, r = ev_rec, l = [];
    if (ev_fin_t >= 0 && r) {
        l.push(["WINNER", ev_num(r.vainqueur), ev_nom(r.vainqueur), ""]);
        if (r.holeshot >= 0) l.push(["HOLESHOT", ev_num(r.holeshot), ev_nom(r.holeshot), ""]);
        if (r.charger >= 0) l.push(["HARD CHARGER", ev_num(r.charger), ev_nom(r.charger), "+" + r.gain + " PLACES"]);
        if (r.mt >= 0) l.push(["MEILLEUR TOUR", ev_num(r.mt), ev_nom(r.mt), ev_temps(r.mt_t)]);
        k = Math.floor((mx.seconds - ev_fin_t) / EV_ROT) % l.length;
        return l[k];
    }
    if (ev_hs >= 0 && mx.seconds - ev_hs_t < EV_HS_DUREE) return ["HOLESHOT", ev_num(ev_hs), ev_nom(ev_hs), ""];
    return null;
}
""".replace("EVY0", str(EV_Y[0])).replace("EVY1", str(EV_Y[1])).replace("EVY2", str(EV_Y[2])).replace("EVHS", str(EV_HS_INDEX)) \
   .replace("EVVG", "%.2f" % EV_VOL["grille"]).replace("EVVP", "%.2f" % EV_VOL["public"]).replace("EVNP", str(EV_COPIES["public"])).replace("EVVO", "%.2f" % EV_VOL["ooh"]).replace("EVFF", "%.2f" % EV_VOL["foule_fin"]).replace("EVVF", "%.2f" % EV_VOL["foule"]).replace("EVVA", "%.2f" % EV_VOL["annonce"]).replace("EVVH", "%.2f" % EV_VOL["hp"]).replace("EVFD", "%.2f" % (os.path.getsize(os.path.join(SONS_RF, "crowdconstant.raw")) / 2.0 / 44100))


def musique_coupee():
    """v45i : la chanson jusqu'à MUSIQUE_FIN s, fondu de sortie de MUSIQUE_FONDU s."""
    a = np.fromfile(MUSIQUE, "<i2").astype(float); n = int(MUSIQUE_FIN * 44100); a = a[:n].copy()
    f = int(MUSIQUE_FONDU * 44100); a[-f:] *= np.linspace(1.0, 0.0, f)
    return a


def _fort(a, k):
    """v45i : limiteur doux (tanh) : monte le niveau moyen sans dépasser le pic de 29000 (le volume du jeu est plafonné à 1)."""
    a = a / np.abs(a).max()
    return (np.tanh(k * a) / np.tanh(k) * 29000.0).astype("<i2")


def _bloc_musique():
    """v45d (Ryan : la chanson FIVE - SX Paris 2022 « quand tout le monde a passé l'arrivée ») : jouée juste après l'annonce, sur les
    hauts-parleurs + des copies qui suivent la caméra. v45j : sur GitHub à la demande de Ryan (pour que tout le monde l'ait),
    avec l'accord de l'artiste FIVE donné à Ryan ;
    sans le fichier, pas de chanson (EV_S_MUS vide)."""
    an = os.path.getsize(os.path.join(HERE, "sons", "annonce_paris.raw")) / 2.0 / 44100
    L = ["var EV_ANNONCE_DUREE = %.2f, EV_S_MUS = [], EV_S_MUS_CAM = [], EV_MUS_DUREE = 0;" % (an + 0.5)]
    if os.path.exists(MUSIQUE):
        L += ["EV_MUS_DUREE = %.2f;" % min(os.path.getsize(MUSIQUE) / 2.0 / 44100, MUSIQUE_FIN),   # v45i : durée coupée
              "for (ev_k = 0; ev_k < EV_HP.length; ev_k++) {",
              '    EV_S_MUS.push(ev_son("@FOLDER/js/sounds/musique.raw", %.1f, 44100));' % EV_VOL["mus_hp"],
              "    if (EV_S_MUS[ev_k] >= 0) mx.set_sound_pos(EV_S_MUS[ev_k], EV_HP[ev_k][0], EV_HP[ev_k][1], EV_HP[ev_k][2]);",
              "}",
              'EV_S_MUS_CAM = ev_sons("@FOLDER/js/sounds/musique.raw", %.1f, 44100, %d);   /* copies a la camera */' % (EV_VOL["mus"], EV_COPIES["mus"]),
              "EV_S_MUS = EV_S_MUS.concat(EV_S_MUS_CAM);"]
    return chr(10).join(L) + chr(10)


EV_JS = EV_JS.replace("/*EV_MUSIQUE*/" + chr(10), _bloc_musique())


def _font(path, px):
    f = ImageFont.truetype(path, px)
    if path == FONT_E:   # v45c : Bahnschrift (police variable) en gras condensé
        f.set_variation_by_name(FONT_E_STYLE)
    return f


def _police(im, chars, path, px, gh, col, y0):
    """lettres rangées à partir de y0 (largeur de la page) ; renvoie {lettre: [x, y, largeur]} (px de la page) et le bas."""
    f = _font(path, px); d = ImageDraw.Draw(im); x, y = 1, y0; cells = {}
    _, rt, _, rb = d.textbbox((0, 0), "H0", font=f)                 # v45 : même ligne de base pour tous (le « . » en bas, plus au milieu)
    for ch in chars:
        l, t, r, b = d.textbbox((0, 0), ch, font=f); w = r - l + 2
        if x + w > PW - 1:
            x, y = 1, y + gh
        oy = (gh - (rb - rt)) // 2 - rt
        d.text((x + 1 - l, y + oy), ch, font=f, fill=col + (255,))
        cells[ch] = [x, y, w]; x += w + 1
    return cells, y + gh


def _lettres():
    """page 1 (les 2 textures) : polices (nom blanc, numéro rose, place sombre, temps blanc) + filets de couleur."""
    im = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
    # v45c (DA E) : Bahnschrift gras condensé ; N noms blancs, P rose (places, titres, meilleur tour), D gris (écarts), T temps
    N, y = _police(im, NOM, FONT_E, 21, 26, (255, 255, 255), 0)
    P, y = _police(im, NUM, FONT_E, 21, 26, E_ROSE, y)
    D, y = _police(im, TEMPS, FONT_E, 20, 26, E_GRIS2, y)
    T, y = _police(im, TEMPS, FONT_E, 56, 56, (255, 255, 255), y)
    by = y; d = ImageDraw.Draw(im)
    for i, col in enumerate(BANDES.values()):
        d.rectangle([i * 10, by, i * 10 + 7, by + ROW_H - 1], fill=col + (255,))
    assert by + ROW_H <= PH, "page 1 pleine"
    return im, N, P, D, T, by


def _rangees(d, y0, n):
    for k in range(n):
        y = y0 + k * ROW_H
        d.rounded_rectangle([POS_X1 + 2, y + 2, PW - 4, y + ROW_H - 3], 4, fill=(48, 14, 72, 255))
        d.rounded_rectangle([POS_X0, y + 2, POS_X1, y + ROW_H - 3], 4, fill=(250, 250, 252, 255))


def _fonds(PD):
    """pages 0 des 2 textures."""
    import sys
    sys.path.insert(0, os.path.join(HERE, "stade_paris", "src"))
    from arena import branding as BR_
    u_ = BR_.logo_rgba(); us = Image.fromarray(np.dstack([np.clip(u_[..., :3], 0, 255), np.clip(u_[..., 3] * 255, 0, 255)]).astype(np.uint8), "RGBA")
    us = us.crop(us.getbbox())
    if DA_E:
        return _fonds_e(PD)
    A = Image.new("RGBA", (PW, PH), VIOLET + (255,)); B = Image.new("RGBA", (PW, PH), VIOLET + (255,))
    # panneau 1 : coucher de soleil, logo, « CLASSEMENT LIVE », case du temps
    A.paste(PD._sunset(PW, 256), (0, 0)); dA = ImageDraw.Draw(A)
    PD.fitc(A, PD.lg("sxparis"), (12, 6, PW - 12, 104), 0.02)
    f = ImageFont.truetype(FONT_B, 15)
    dA.rectangle([0, 112, PW, 138], fill=VIOLET + (255,))
    dA.text((10, 114), "CLASSEMENT", font=f, fill=(255, 255, 255))
    dA.ellipse([PW - 66, 120, PW - 56, 130], fill=(255, 40, 60)); dA.text((PW - 52, 114), "LIVE", font=f, fill=(255, 255, 255))
    dA.rounded_rectangle(TIME_BOX, 8, fill=(28, 28, 34, 255))
    if TIME_FILET:   # v45b (« enlève le trait blanc au-dessus de 1L, ça fait IA slop ») : plus de filet
        dA.rectangle([TIME_BOX[0] + 22, TIME_BOX[1] + 9, TIME_BOX[2] - 22, TIME_BOX[1] + 12], fill=(235, 235, 240, 255))
    dB = ImageDraw.Draw(B)
    _top10_fond(dA, dB)
    _mt_fond(dB)
    return A, B


def _fonds_e(PD):
    """v45c (DA E, choisie par l'utilisateur sur les propositions A / B / C : « le cadre et la DA de A, sans ses 2 traits ; le classement
    de C ») : fond noir uni ; panneau 1 = logo Supercross Paris, « LIVE » (point rouge) et « TEMPS DE COURSE », le temps (dessiné par le
    script) ; panneaux 2-3 = 10 lignes sans case ni pastille, une sur deux un peu plus claire ; panneau 4 = « MEILLEUR TOUR » en gris."""
    A = Image.new("RGBA", (PW, PH), E_FOND + (255,)); B = Image.new("RGBA", (PW, PH), E_FOND + (255,)); dA, dB = ImageDraw.Draw(A), ImageDraw.Draw(B)
    PD.fitc(A, PD.lg("sxparis"), (24, 14, PW - 24, 96), 0.0)
    dA.ellipse([22, 124, 30, 132], fill=(230, 40, 50)); dA.text((36, 128), "LIVE", font=_font(FONT_E, 15), fill=(230, 230, 235), anchor="lm")
    dA.text((PW - 20, 128), "TEMPS DE COURSE", font=_font(FONT_E, 13), fill=E_GRIS, anchor="rm")
    for k in range(1, A_N, 2):                                   # lignes paires (2, 4...) un peu plus claires, panneaux 2 et 3
        y = E_Y0 + k * E_H
        dA.rectangle([0, 256 + y, PW, 256 + y + E_H - 1], fill=E_LIGNE + (255,)); dB.rectangle([0, y, PW, y + E_H - 1], fill=E_LIGNE + (255,))
    dB.text((E_MT_X, 256 + 70), "MEILLEUR TOUR", font=_font(FONT_E, 16), fill=E_GRIS, anchor="lm")
    return A, B


def _top10_fond(dA, dB):
    """v45 : bandes du top 10 (A) : panneau 2 = bas de la page A, panneau 3 = haut de la page B."""
    f = ImageFont.truetype(FONT_B, 12)
    for k in range(A_N):
        y = A_Y0 + k * A_H; col = ROSE if k == 0 else (VIOLET3 if k % 2 == 0 else VIOLET2)
        ya = 256 + y
        dA.rectangle([A_X0, ya, PW, ya + A_H - 3], fill=col + (255,))
        dA.rounded_rectangle([A_PLACE[0], ya + 2, A_PLACE[1], ya + A_H - 5], 3, fill=(255, 255, 255, 255))
        dA.rounded_rectangle([A_PILL[0], ya + 3, A_PILL[1], ya + A_H - 6], 4, fill=(VIOLET if k == 0 else ROSE) + (255,))   # v45c : leader violet foncé, numéro blanc
        dB.polygon([(0, y), (A_BANDE_X1, y), (A_BANDE_X1 - A_PENTE, y + A_H - 3), (0, y + A_H - 3)], fill=col + (255,))
        if k == 0:
            dB.text((A_ECART_X1, y + (A_H - 3) / 2), "LEADER", font=f, fill=(255, 255, 255), anchor="rm")


def _mt_fond(dB):
    """v45 : panneau 4 (bas de la page B) : carte du meilleur tour seule."""
    x0, y0, x1, y1 = MT_CARTE
    dB.rounded_rectangle([x0, 256 + y0, x1, 256 + y1], 10, fill=VIOLET2 + (255,))
    dB.polygon([(x0, 256 + y0), (x0 + 190, 256 + y0), (x0 + 176, 256 + y0 + 30), (x0, 256 + y0 + 30)], fill=ROSE + (255,))
    dB.text((x0 + 12, 256 + y0 + 15), MT_TITRE, font=ImageFont.truetype(FONT_B, 15), fill=(255, 255, 255), anchor="lm")


def _js(N, P, D, T, by, tex_a, tex_b, folder=""):
    bandes = {k: i for i, k in enumerate(BANDES)}
    return r"""/*
USLAND Paris by Ryan v39b - classement en direct sur tout l'ecran geant (DA de la retransmission Supercross Paris).
Fait comme la tour de classement de ZION 2025 Supercross Paris (pages 256 x 512, dessin a chaque image). Texte ASCII expres.
*/
var TD_A = mx.read_texture("%(ta)s");
var TD_B = mx.read_texture("%(tb)s");
var TD_W = %(pw)d, TD_H = %(ph)d;
var TD_N = { h: 26, c: %(N)s };
var TD_P = { h: 26, c: %(P)s };
var TD_D = { h: 26, c: %(D)s };
var TD_T = { h: 56, c: %(T)s };
var TD_BANDES = %(bandes)s, TD_BY = %(by)d;
var TD_MARQUES = [%(marques)s];
var TD_FIN_TOURS = mx.get_finish_laps(), TD_FIN_TEMPS = mx.get_finish_time();
var td_ordre = [];
var td_tex = TD_A;

function td_cp(f, sx, sy, dx, dy, w, h) {
    mx.paste_custom_frame(td_tex, f, sx / TD_W, sy / TD_H, dx / TD_W, dy / TD_H, w / TD_W, h / TD_H);
}
function td_larg(f, s) {
    var i, c, w = 0;
    for (i = 0; i < s.length; i++) {
        if (s[i] == " ") { w += 8; continue; }
        c = f.c[s[i]]; if (c) w += c[2] - 1;
    }
    return w;
}
function td_txt(f, x, y, s) {
    var i, c;
    for (i = 0; i < s.length; i++) {
        if (s[i] == " ") { x += 8; continue; }
        c = f.c[s[i]]; if (!c) continue;
        td_cp(1, c[0], c[1], x, y, c[2], f.h);
        x += c[2] - 1;
    }
}
function td_marque(m) {
    var i;
    for (i = 0; i < TD_MARQUES.length; i++) if (m.match(TD_MARQUES[i][0])) return TD_MARQUES[i][1];
    return "none";
}
function td_2(n) { n = Math.floor(n).toString(); return n.length < 2 ? "0" + n : n; }
function td_temps_restant() {
    var d = mx.get_gate_drop_time(), s = mx.seconds - d;
    if (d < 0 || s < 0) return TD_FIN_TEMPS;
    return Math.max(0.0, TD_FIN_TEMPS - s);
}
function td_passe_avant(index, secs) {
    var i, t;
    for (i = 0; i < td_ordre.length; i++) { t = mx.get_timing(td_ordre[i].slot, index); if (t >= 0 && t < secs) return true; }
    return false;
}
function td_tours_avant(secs) {
    var i, last, t;
    if (secs == 0) return 0;
    secs += mx.get_gate_drop_time();
    last = mx.index_to_lap(td_ordre[0].position);
    for (i = last; i > 0; i--) { t = mx.get_timing(td_ordre[0].slot, mx.lap_to_index(i)); if (t < secs) break; }
    for (; i <= last; i++) if (!td_passe_avant(mx.lap_to_index(i), secs)) break;
    return i - 1;
}
function td_haut() {
    var t, l, lead = td_ordre.length > 0 && td_ordre[0].position >= 1;
    if (TD_FIN_TEMPS == 0) {                                 /* v45b ("mets juste le temps qui defile") : course aux tours = temps de course */
        t = mx.get_gate_drop_time(); t = (t < 0 || mx.seconds < t) ? 0 : mx.seconds - t;
        return td_2(t / 60) + ":" + td_2(t %% 60);
    }
    t = td_temps_restant();
    if (t > 0 || !lead) return td_2(t / 60) + ":" + td_2(t %% 60) + (TD_FIN_TOURS > 0 ? " + " + TD_FIN_TOURS.toFixed(0) + "L" : "");
    l = td_tours_avant(TD_FIN_TEMPS) + 1 + TD_FIN_TOURS - mx.index_to_lap(td_ordre[0].position);
    return "00:00" + (l > 0 ? " + " + l.toFixed(0) + "L" : "");
}
function td_nom(s) {
    var m = s.replace(/\|.*/, "").replace(/^\s+|\s+$/g, "").split(" ");
    return m[m.length - 1].toUpperCase().substring(0, %(nmax)d);
}
function td_lignes_a() {                                     /* v45c (DA E) : panneau 2 (bas de la page A) : place (rose), numero, nom */
    var k, r, yy, p, n, nm;
    for (k = 0; k < %(an)d && k < td_ordre.length; k++) {
        r = td_ordre[k];
        if (r.position < 1) break;
        yy = 256 + %(ey0)d + k * %(eh)d + %(edy)d;
        p = (k + 1).toString();
        td_txt(TD_P, %(epx1)d - td_larg(TD_P, p), yy, p);
        n = mx.get_rider_number(r.slot).toString();
        td_txt(TD_N, %(enx)d, yy, n);
        nm = td_nom(mx.get_rider_name(r.slot));
        while (nm.length > 1 && %(enomx)d + td_larg(TD_N, nm) > %(enomx1)d) nm = nm.substring(0, nm.length - 1);
        td_txt(TD_N, %(enomx)d, yy, nm);
    }
}
function td_ecart(r, l) {                                      /* ecart au leader au meme point de chrono, ou tours de retard */
    var L = mx.lap_to_index(2) - mx.lap_to_index(1), n, t0, t1;
    if (L > 0) { n = Math.floor((l.position - r.position) / L); if (n >= 1) return "+" + n + "L"; }
    t0 = mx.get_timing(l.slot, r.position); t1 = mx.get_timing(r.slot, r.position);
    if (t0 < 0 || t1 < 0) return "";
    t1 = Math.max(0, t1 - t0);
    return "+" + (t1 < 60 ? t1.toFixed(1) : ev_temps(t1));
}
function td_lignes_b() {                                     /* panneau 3 (haut de la page B) : ecarts */
    var k, r, e;
    for (k = 1; k < %(an)d && k < td_ordre.length; k++) {
        r = td_ordre[k];
        if (r.position < 1) break;
        e = td_ecart(r, td_ordre[0]);
        if (e) td_txt(TD_D, %(eex1)d - td_larg(TD_D, e), %(ey0)d + k * %(eh)d + %(edy)d, e);   /* v45c : ecarts en gris */
    }
}
var td_mt_t = -1, td_mt_s = -100, td_mt_slot = -1;
function td_mt_maj() {                                       /* meilleur tour de la course (tours complets a partir du 2e), 1 fois par seconde */
    var i, k, n, t1, t2, best = -1, slot = -1;
    if (mx.seconds >= td_mt_s && mx.seconds - td_mt_s < 1.0) return;
    td_mt_s = mx.seconds;
    for (i = 0; i < td_ordre.length; i++) {
        n = mx.index_to_lap(td_ordre[i].position);
        for (k = 1; k < n; k++) {
            t1 = mx.get_timing(td_ordre[i].slot, mx.lap_to_index(k)); t2 = mx.get_timing(td_ordre[i].slot, mx.lap_to_index(k + 1));
            if (t1 >= 0 && t2 > t1 && (best < 0 || t2 - t1 < best)) { best = t2 - t1; slot = td_ordre[i].slot; }
        }
    }
    td_mt_t = best; td_mt_slot = slot;
}
function td_chrono(t) { var m = Math.floor(t / 60), s = t - 60 * m; return m + ":" + (s < 10 ? "0" : "") + s.toFixed(3); }
function td_mt() {                                           /* panneau 4 (bas de la page B) : le meilleur temps seul */
    var s;
    td_mt_maj();
    s = td_mt_t > 0 ? td_chrono(td_mt_t) : "-:--.---";
    td_txt(TD_T, %(emtx)d, 256 + %(emty)d, s);                   /* v45c : aligne a gauche, pilote en rose dessous */
    if (td_mt_slot >= 0) {
        s = mx.get_rider_number(td_mt_slot).toString() + "  " + td_nom(mx.get_rider_name(td_mt_slot));
        td_txt(TD_P, %(emtx)d, 256 + %(emtny)d, s);
    }
}
function td_dessine(secs) {
    var s;
    td_ordre = mx.get_running_order();
    td_tex = TD_A;
    mx.begin_custom_frame(TD_A);
    td_cp(0, 0, 0, 0, 0, TD_W, TD_H);
    s = ev_ecran();                                           /* v44 : holeshot / vainqueur / recompenses a la place du temps */
    if (s) {
        td_txt(TD_P, TD_W / 2 - td_larg(TD_P, s[0]) / 2, EV_Y[0], s[0]);              /* v45c : titre en rose */
        td_txt(TD_N, TD_W / 2 - td_larg(TD_N, s[1] + "  " + s[2]) / 2, EV_Y[1], s[1] + "  " + s[2]);
        td_txt(TD_N, TD_W / 2 - td_larg(TD_N, s[3]) / 2, EV_Y[2], s[3]);
    } else {
        s = td_haut();
        td_txt(TD_T, TD_W / 2 - td_larg(TD_T, s) / 2, %(ety)d, s);
    }
    td_lignes_a();
    mx.end_custom_frame(TD_A);
    td_tex = TD_B;
    mx.begin_custom_frame(TD_B);
    td_cp(0, 0, 0, 0, 0, TD_W, TD_H);
    td_lignes_b();
    td_mt();
    mx.end_custom_frame(TD_B);
}
function td_image(secs) {
    try { ev_maj(); } catch (e) { mx.message("evenements : " + e.toString()); }
    try { td_dessine(secs); } catch (e) { mx.message("classement : " + e.toString()); }
    td_prev(secs);
}
var td_prev = mx.frame_handler;
if (!td_prev) td_prev = function (s) {};
mx.frame_handler = td_image;
""" % dict(ta=tex_a, tb=tex_b, pw=PW, ph=PH, N=json.dumps(N), P=json.dumps(P), D=json.dumps(D), T=json.dumps(T), bandes=json.dumps(bandes),
           by=by, marques=", ".join('[/%s/, "%s"]' % (r, k) for r, k in MARQUES), nmax=NAME_MAX, rh=ROW_H, px0=POS_X0, px1=POS_X1,
           bx0=BAR_X0, bw=BAR_X1 - BAR_X0, nx=NUM_X, nmx=NAME_X, ty=TIME_Y, npan=NPAN, an=A_N, ah=A_H, ay0=A_Y0, ady=A_DY, pl0=A_PLACE[0], pl1=A_PLACE[1], pi0=A_PILL[0], pi1=A_PILL[1],
           nx0=A_NOM_X, nx1=A_NOM_X1, ex1=A_ECART_X1, mtcx=(MT_CARTE[0] + MT_CARTE[2]) // 2, mty=MT_Y, mtny=MT_NOM_Y,
           ey0=E_Y0, eh=E_H, edy=(E_H - 26) // 2, epx1=E_PLACE_X1, enx=E_NUM_X, enomx=E_NOM_X, enomx1=E_NOM_X1, eex1=E_ECART_X1,
           emtx=E_MT_X, emty=E_MT_Y, emtny=E_MT_NOM_Y, ety=E_TIME_Y) + EV_JS.replace("@FOLDER", "@" + folder)


def apercu(OUT, path_png, ordre=None, temps="04:32 + 1L", mt="1:52.341", mt_nom="202  OPPLIGER", evt=None):
    """aperçu de l'écran entier (mêmes calculs que frills.js, rejoués en Python) : 4 panneaux côte à côte (v45 : top 10 A)."""
    D_ = os.path.join(OUT, *SUB.split("/"))
    fA = Image.open(os.path.join(D_, "fond_a.png")).convert("RGBA"); fB = Image.open(os.path.join(D_, "fond_b.png")).convert("RGBA")
    f1 = Image.open(os.path.join(D_, "lettres.png")).convert("RGBA"); meta = json.load(open(os.path.join(D_, "polices.json")))
    frames = {"a": fA.copy(), "b": fB.copy()}

    def larg(f, s):
        return sum(8 if ch == " " else (f["c"][ch][2] - 1 if ch in f["c"] else 0) for ch in s)

    def txt(fr, f, x, y, s):
        for ch in s:
            if ch == " ":
                x += 8; continue
            if ch not in f["c"]:
                continue
            c = f["c"][ch]; fr.alpha_composite(f1.crop((c[0], c[1], c[0] + c[2], c[1] + f["h"])), (int(round(x)), int(round(y)))); x += c[2] - 1
    ordre = ordre or [(202, "OPPLIGER", ""), (21, "THOMAS", "+1.4"), (9, "HARRIS", "+2.9"), (47, "CLARK", "+3.3"), (151, "PIETERS", "+5.8"),
                      (16, "MILLER", "+7.0"), (348, "COEN", "+9.6"), (33, "HICKS", "+12.1"), (77, "MANZI", "+1L"), (5, "LAMARQUE", "+2L")]
    N, P, Dg, T = meta["N"], meta["P"], meta["D"], meta["T"]
    if evt:                                     # comme td_dessine (v45c) : titre rose, « numéro  nom » blanc, valeur
        txt(frames["a"], P, PW / 2 - larg(P, evt[0]) / 2, EV_Y[0], evt[0])
        l2 = evt[1] + "  " + evt[2]; txt(frames["a"], N, PW / 2 - larg(N, l2) / 2, EV_Y[1], l2)
        txt(frames["a"], N, PW / 2 - larg(N, evt[3]) / 2, EV_Y[2], evt[3])
    else:
        txt(frames["a"], T, PW / 2 - larg(T, temps) / 2, E_TIME_Y, temps)
    dy = (E_H - 26) // 2
    for k, (num, nom, ec) in enumerate(ordre[:A_N]):
        yy = E_Y0 + k * E_H + dy; p = str(k + 1)
        txt(frames["a"], P, E_PLACE_X1 - larg(P, p), 256 + yy, p)
        txt(frames["a"], N, E_NUM_X, 256 + yy, str(num))
        nm = nom.upper()[:NAME_MAX]
        while len(nm) > 1 and E_NOM_X + larg(N, nm) > E_NOM_X1:
            nm = nm[:-1]
        txt(frames["a"], N, E_NOM_X, 256 + yy, nm)
        if k and ec:
            txt(frames["b"], Dg, E_ECART_X1 - larg(Dg, ec), yy, ec)
    txt(frames["b"], T, E_MT_X, 256 + E_MT_Y, mt)
    txt(frames["b"], P, E_MT_X, 256 + E_MT_NOM_Y, mt_nom)
    full = Image.new("RGBA", (4 * PW, 256))
    for i, (tex, y0, _) in enumerate(PANNEAUX):
        full.paste(frames[tex].crop((0, y0, PW, y0 + 256)), (i * PW, 0))
    full = full.resize((4 * PW * 2, int(256 * 2 * 55.8 / 52.5)), Image.LANCZOS)     # au rapport réel de l'écran
    full.save(path_png)
    return path_png


def make(OUT, FOLDER, x, z, yaw, apercu_png=None):
    """écrit fond_a/b.png, lettres.png, direct_a/b.seq, dalles.jm (statue/paris/direct) et frills.js ; renvoie la ligne de statue
    (une seule statue : le jm a 2 matières, une par texture)."""
    import paddock26 as PD
    import hab_kit as K
    D = os.path.join(OUT, *SUB.split("/")); os.makedirs(D, exist_ok=True)
    for old in os.listdir(D):                                           # v37 / v38c / v39 : anciens fichiers
        os.remove(os.path.join(D, old))
    if DA_CHRONO:   # v45d : tableau de chronométrage (tableau_chrono.py) à la place du classement TV
        import tableau_chrono as TC
        A, B = TC.fonds(); let, pol_ = TC.lettres()
    else:
        A, B = _fonds(PD); let, N, P, Dg, T, by = _lettres()
    A.save(os.path.join(D, "fond_a.png")); B.save(os.path.join(D, "fond_b.png"))
    let.save(os.path.join(D, "lettres.png"))
    if DA_CHRONO:
        json.dump(pol_, open(os.path.join(D, "polices.json"), "w"))
    else:
        json.dump(dict(N=dict(h=26, c=N), P=dict(h=26, c=P), D=dict(h=26, c=Dg), T=dict(h=56, c=T), by=by,
                       bandes={k: i for i, k in enumerate(BANDES)}), open(os.path.join(D, "polices.json"), "w"))
    for t_ in ("a", "b"):
        seq = ["ANIM1 1 2 512 0", "0", "PNG @%s/%s/fond_%s.png" % (FOLDER, SUB, t_), "PNG @%s/%s/lettres.png" % (FOLDER, SUB), ""]
        open(os.path.join(D, "direct_%s.seq" % t_), "w", newline="\n").write("\n".join(seq))
    # 4 rectangles devant l'écran (paddock26.screen : plus d'image fixe, fond noir à 1 ft derrière), un statue par texture
    hs = PD.SCR_Y1 - PD.SCR_Y0; wp = PD.SCR_W / 4.0; lines = []
    for t_ in ("a", "b"):
        m = PD.M()
        for i, (tx, y0, _) in enumerate(PANNEAUX):
            if tx == t_:
                m.panel((-PD.SCR_W / 2 + wp * (i + 0.5), 1.05), (0, 1), wp, hs, PD.SCR_Y0, K.R((0, y0, PW, y0 + 256), PW, PH))
        PD.write_jm(os.path.join(D, "ecran_%s.jm" % t_), [(PD.UNLIT, m)])
        lines.append("[%.6f 0.000000 %.6f] %.6f @%s/%s/ecran_%s.jm @%s/%s/direct_%s.seq null" % (x, z, yaw, FOLDER, SUB, t_, FOLDER, SUB, t_))
    ta, tb = ("@%s/%s/direct_%s.seq" % (FOLDER, SUB, t_) for t_ in ("a", "b"))
    # v44 : sons des événements (pack sx2026 de RF : grille qui tombe, clameur du public)
    import shutil
    sd_ = os.path.join(OUT, "js", "sounds"); os.makedirs(sd_, exist_ok=True)
    shutil.copy(os.path.join(SONS_RF, "gatedrop.raw"), os.path.join(sd_, "grille.raw"))
    cr_ = np.fromfile(os.path.join(SONS_RF, "crowdroar.raw"), "<i2").astype(float)            # v45g : clameur au-dessus de la foule
    _fort(cr_, 2.5).tofile(os.path.join(sd_, "public.raw"))                                   # v45i : limiteur doux (plus fort à pic égal)
    fo_ = np.fromfile(os.path.join(SONS_RF, "crowdconstant.raw"), "<i2").astype(float)       # v45e : rms 692 -> pic 29000 (inaudible avant)
    (fo_ * (29000.0 / np.abs(fo_).max())).astype("<i2").tofile(os.path.join(sd_, "foule.raw"))
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sons", "annonce_paris.raw"), os.path.join(sd_, "annonce.raw"))   # v44c     # v44b : « et le son des spectateurs »
    if os.path.exists(MUSIQUE):                                                                          # v45d : chanson (locale)
        _fort(musique_coupee(), 2.0).tofile(os.path.join(sd_, "musique.raw"))   # v45i
    if DA_CHRONO:
        open(os.path.join(OUT, "frills.js"), "w", newline="\n", encoding="ascii").write(TC.js(pol_, ta, tb) + EV_JS.replace("@FOLDER", "@" + FOLDER))
        ap = TC.apercu(A, B, let, pol_, apercu_png or os.path.join(D, "..", "apercu_direct.png"))
        return lines, dict(da="chrono", apercu=ap)
    open(os.path.join(OUT, "frills.js"), "w", newline="\n", encoding="ascii").write(_js(N, P, Dg, T, by, ta, tb, FOLDER))
    ap = apercu(OUT, apercu_png or os.path.join(D, "..", "apercu_direct.png"))
    return lines, dict(lettres=[len(N), len(P), len(Dg), len(T)], panneaux=len(PANNEAUX), panneau_ft=[round(wp, 1), round(hs, 1)], apercu=ap)
