/* USLAND Paris by Ryan v42 - meme script dans frills.js et nofrills.js ; verrou si le jeu lance les deux. Texte ASCII expres. */
var USP_CHARGE;
if (!USP_CHARGE) {
USP_CHARGE = 1;
(function () {
/*
USLAND Paris by Ryan v39b - classement en direct sur tout l'ecran geant (DA de la retransmission Supercross Paris).
Fait (pages 256 x 512, dessin a chaque image). Texte ASCII expres.
*/
var TD_A = mx.read_texture("@USLANDParisSupercross2026/statue/paris/direct/direct_a.seq");
var TD_B = mx.read_texture("@USLANDParisSupercross2026/statue/paris/direct/direct_b.seq");
var TD_W = 256, TD_H = 512;
var TD_N = { h: 26, c: {"A": [1, 0, 16], "B": [18, 0, 15], "C": [34, 0, 15], "D": [50, 0, 15], "E": [66, 0, 14], "F": [81, 0, 13], "G": [95, 0, 16], "H": [112, 0, 16], "I": [129, 0, 9], "J": [139, 0, 13], "K": [153, 0, 17], "L": [171, 0, 13], "M": [185, 0, 18], "N": [204, 0, 16], "O": [221, 0, 16], "P": [238, 0, 14], "Q": [1, 26, 16], "R": [18, 26, 16], "S": [35, 26, 14], "T": [50, 26, 14], "U": [65, 26, 16], "V": [82, 26, 16], "W": [99, 26, 21], "X": [121, 26, 16], "Y": [138, 26, 16], "Z": [155, 26, 14], "0": [170, 26, 13], "1": [184, 26, 13], "2": [198, 26, 13], "3": [212, 26, 13], "4": [226, 26, 13], "5": [240, 26, 13], "6": [1, 52, 13], "7": [15, 52, 13], "8": [29, 52, 13], "9": [43, 52, 13], "-": [57, 52, 8], "'": [66, 52, 7], ".": [74, 52, 8], ":": [83, 52, 8], "+": [92, 52, 13]} };
var TD_P = { h: 26, c: {"0": [1, 78, 13], "1": [15, 78, 13], "2": [29, 78, 13], "3": [43, 78, 13], "4": [57, 78, 13], "5": [71, 78, 13], "6": [85, 78, 13], "7": [99, 78, 13], "8": [113, 78, 13], "9": [127, 78, 13], ".": [141, 78, 8], "-": [150, 78, 8], "A": [159, 78, 16], "B": [176, 78, 15], "C": [192, 78, 15], "D": [208, 78, 15], "E": [224, 78, 14], "F": [239, 78, 13], "G": [1, 104, 16], "H": [18, 104, 16], "I": [35, 104, 9], "J": [45, 104, 13], "K": [59, 104, 17], "L": [77, 104, 13], "M": [91, 104, 18], "N": [110, 104, 16], "O": [127, 104, 16], "P": [144, 104, 14], "Q": [159, 104, 16], "R": [176, 104, 16], "S": [193, 104, 14], "T": [208, 104, 14], "U": [223, 104, 16], "V": [1, 130, 16], "W": [18, 130, 21], "X": [40, 130, 16], "Y": [57, 130, 16], "Z": [74, 130, 14], "'": [89, 130, 7]} };
var TD_D = { h: 26, c: {"0": [1, 156, 13], "1": [15, 156, 13], "2": [29, 156, 13], "3": [43, 156, 13], "4": [57, 156, 13], "5": [71, 156, 13], "6": [85, 156, 13], "7": [99, 156, 13], "8": [113, 156, 13], "9": [127, 156, 13]} };
var TD_T = { h: 56, c: {"0": [1, 182, 25], "1": [27, 182, 25], "2": [53, 182, 25], "3": [79, 182, 25], "4": [105, 182, 25], "5": [131, 182, 25], "6": [157, 182, 25], "7": [183, 182, 25], "8": [209, 182, 25], "9": [1, 238, 25], ":": [27, 238, 14], "+": [42, 238, 25], "L": [68, 238, 25], ".": [94, 238, 14], "-": [109, 238, 14]} };
var TD_BANDES = {"honda": 0, "ktm": 1, "kawasaki": 2, "yamaha": 3, "suzuki": 4, "husqvarna": 5, "gasgas": 6, "triumph": 7, "none": 8}, TD_BY = 294;
var TD_MARQUES = [[/^crf?[0-9]+/, "honda"], [/^[0-9]+sx/, "ktm"], [/^kx[0-9]+/, "kawasaki"], [/^yz[0-9]+/, "yamaha"], [/^rmz?[0-9]+/, "suzuki"], [/^fc[0-9]+/, "husqvarna"], [/^mc[0-9]+/, "gasgas"], [/^tf[0-9]+/, "triumph"]];
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
    if (TD_FIN_TEMPS == 0) {
        l = TD_FIN_TOURS - (lead ? mx.index_to_lap(td_ordre[0].position) : 0);
        return Math.max(0, l).toFixed(0) + "L";
    }
    t = td_temps_restant();
    if (t > 0 || !lead) return td_2(t / 60) + ":" + td_2(t % 60) + (TD_FIN_TOURS > 0 ? " + " + TD_FIN_TOURS.toFixed(0) + "L" : "");
    l = td_tours_avant(TD_FIN_TEMPS) + 1 + TD_FIN_TOURS - mx.index_to_lap(td_ordre[0].position);
    return "00:00" + (l > 0 ? " + " + l.toFixed(0) + "L" : "");
}
function td_nom(s) {
    var m = s.replace(/\|.*/, "").replace(/^\s+|\s+$/g, "").split(" ");
    return m[m.length - 1].toUpperCase().substring(0, 9);
}
function td_lignes_a() {                                     /* v45 : top 10 A, panneau 2 (bas de la page A) : place, numero, nom */
    var k, r, yy, p, n, f, nm;
    for (k = 0; k < 10 && k < td_ordre.length; k++) {
        r = td_ordre[k];
        if (r.position < 1) break;
        yy = 256 + 3 + k * 25 + -2;
        p = (k + 1).toString();
        td_txt(TD_D, (9 + 43) / 2 - td_larg(TD_D, p) / 2, yy, p);
        n = mx.get_rider_number(r.slot).toString(); f = TD_N;
        td_txt(f, (55 + 109) / 2 - td_larg(f, n) / 2, yy, n);
        nm = td_nom(mx.get_rider_name(r.slot));
        while (nm.length > 1 && 117 + td_larg(TD_N, nm) > 252) nm = nm.substring(0, nm.length - 1);
        td_txt(TD_N, 117, yy, nm);
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
    for (k = 1; k < 10 && k < td_ordre.length; k++) {
        r = td_ordre[k];
        if (r.position < 1) break;
        e = td_ecart(r, td_ordre[0]);
        if (e) td_txt(TD_N, 232 - td_larg(TD_N, e), 3 + k * 25 + -2, e);
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
    td_txt(TD_T, 128 - td_larg(TD_T, s) / 2, 256 + 98, s);
    if (td_mt_slot >= 0) {
        s = mx.get_rider_number(td_mt_slot).toString() + " - " + td_nom(mx.get_rider_name(td_mt_slot));
        td_txt(TD_P, 128 - td_larg(TD_P, s) / 2, 256 + 156, s);
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
        td_txt(TD_N, TD_W / 2 - td_larg(TD_N, s[0]) / 2, EV_Y[0], s[0]);
        td_txt(TD_P, TD_W / 2 - (td_larg(TD_P, s[1]) + 8 + td_larg(TD_N, s[2])) / 2, EV_Y[1], s[1]);
        td_txt(TD_N, TD_W / 2 - (td_larg(TD_P, s[1]) + 8 + td_larg(TD_N, s[2])) / 2 + td_larg(TD_P, s[1]) + 8, EV_Y[1], s[2]);
        td_txt(TD_N, TD_W / 2 - td_larg(TD_N, s[3]) / 2, EV_Y[2], s[3]);
    } else {
        s = td_haut();
        td_txt(TD_T, TD_W / 2 - td_larg(TD_T, s) / 2, 168, s);
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

/*
USLAND Paris - evenements de course (code USLAND, v44) : son de la grille, holeshot (ecran + public), vainqueur et recompenses
de fin de manche sur l'ecran geant (vainqueur, holeshot, hard charger, meilleur tour), public sur les chutes du top 3 et les
bagarres (depassements dans le top 3). Texte ASCII expres.
*/
var EV_Y = [164, 189, 213];
var EV_HS_INDEX = 2;
var EV_HS_DUREE = 10.0, EV_ROT = 5.0, EV_APRES_DEPART = 20.0, EV_PAUSE_PUBLIC = 10.0;
var EV_FIN_TOURS = mx.get_finish_laps(), EV_FIN_TEMPS = mx.get_finish_time();
function ev_son(f, vol, freq) {
    var i = mx.add_sound(f);
    if (i >= 0) { mx.set_sound_freq(i, freq); mx.set_sound_vol(i, vol); mx.set_sound_loop(i, 0); }
    return i;
}
var EV_S_GRILLE = ev_son("@USLANDParisSupercross2026/js/sounds/grille.raw", 1.50, 44100);
function ev_sons(f, vol, freq, n) { var k, a = []; for (k = 0; k < n; k++) a.push(ev_son(f, vol, freq)); return a; }
var EV_S_PUBLIC = ev_sons("@USLANDParisSupercross2026/js/sounds/public.raw", 1.00, 44100, 3);   /* v45i : copies a la camera (volume plafonne a 1) */
var EV_S_OOH = ev_sons("@USLANDParisSupercross2026/js/sounds/public.raw", 1.00, 33075, 3);
var EV_S_ANNONCE = ev_son("@USLANDParisSupercross2026/js/sounds/annonce.raw", 1.00, 44100);   /* v44c : annonce "le plus beau supercross du monde, c est Paris" */
var EV_HP = [[200.7, 50.0, 261.0], [200.7, 50.0, 419.4], [401.1, 50.0, 261.0], [401.1, 50.0, 419.4]];                                              /* v44d : hauts-parleurs au-dessus de la piste (remplace par le build) */
var EV_S_HP = [], ev_k;
for (ev_k = 0; ev_k < EV_HP.length; ev_k++) {
    EV_S_HP.push(ev_son("@USLANDParisSupercross2026/js/sounds/annonce.raw", 0.50, 44100));
    if (EV_S_HP[ev_k] >= 0) mx.set_sound_pos(EV_S_HP[ev_k], EV_HP[ev_k][0], EV_HP[ev_k][1], EV_HP[ev_k][2]);
}
function ev_hauts_parleurs() {                                         /* l'annonce part de chaque haut-parleur + un peu a la camera */
    var k;
    if (EV_S_MUS.length) { ev_mus_t = mx.seconds; return; }            /* v45f : la chanson complete seule (plus l'extrait de 20 s avant) */
    for (k = 0; k < EV_S_HP.length; k++) if (EV_S_HP[k] >= 0) mx.start_sound(EV_S_HP[k]);
    ev_joue(EV_S_ANNONCE);
}
var EV_ANNONCE_DUREE = 20.49, EV_S_MUS = [], EV_S_MUS_CAM = [], EV_MUS_DUREE = 0;
EV_MUS_DUREE = 147.36;
for (ev_k = 0; ev_k < EV_HP.length; ev_k++) {
    EV_S_MUS.push(ev_son("@USLANDParisSupercross2026/js/sounds/musique.raw", 0.4, 44100));
    if (EV_S_MUS[ev_k] >= 0) mx.set_sound_pos(EV_S_MUS[ev_k], EV_HP[ev_k][0], EV_HP[ev_k][1], EV_HP[ev_k][2]);
}
EV_S_MUS_CAM = ev_sons("@USLANDParisSupercross2026/js/sounds/musique.raw", 1.0, 44100, 2);   /* copies a la camera */
EV_S_MUS = EV_S_MUS.concat(EV_S_MUS_CAM);
var EV_ANNONCE_MAX = 120.0;                                           /* si un pilote ne finit jamais (abandon) : annonce 120 s apres le vainqueur */
var EV_S_FOULE = ev_son("@USLANDParisSupercross2026/js/sounds/foule.raw", 1.00, 44100);  /* v44b : bruit du public en continu, suit la camera */
var EV_FOULE_DUREE = 21.22, ev_foule_t = -1000, ev_foule_v = 1.00;
var EV_FOULE_FIN = 0.25;                                              /* v45h : foule plus basse apres l'arrivee (la chanson par-dessus) */                        /* v45c : relance a chaque fin (pas de boucle du jeu, pas au chargement) */
function ev_foule() {
    if (EV_S_FOULE < 0) return;
    mx.set_sound_pos(EV_S_FOULE, ev_p[0], ev_p[1], ev_p[2]);
    if ((ev_fin_t >= 0 ? EV_FOULE_FIN : 1.00) != ev_foule_v) {        /* volume change : on relance a ce volume */
        ev_foule_v = ev_fin_t >= 0 ? EV_FOULE_FIN : 1.00;
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
        if (r.mt >= 0) l.push(["FASTEST LAP", ev_num(r.mt), ev_nom(r.mt), ev_temps(r.mt_t)]);
        k = Math.floor((mx.seconds - ev_fin_t) / EV_ROT) % l.length;
        return l[k];
    }
    if (ev_hs >= 0 && mx.seconds - ev_hs_t < EV_HS_DUREE) return ["HOLESHOT", ev_num(ev_hs), ev_nom(ev_hs), ""];
    return null;
}

/*
USLAND Paris - boudins de la ligne de depart : place 0 de 0 a 20 s apres la chute de la grille, puis place 1
(boudins tardifs : enterres puis sortis ; ligne Minerva : deplacee). Texte ASCII expres.
*/

var g_lt2 = [[0, 437.106, -200.0, 254.075, -2.988203, 437.106, 0.0, 254.075, -2.988203], [1, 420.512, -200.0, 256.64, -2.988203, 420.512, 0.0, 256.64, -2.988203], [2, 403.919, -200.0, 259.206, -2.988203, 403.919, 0.0, 259.206, -2.988203], [3, 387.326, -200.0, 261.771, -2.988203, 387.326, 0.0, 261.771, -2.988203], [4, 370.733, -200.0, 264.337, -2.988203, 370.733, 0.0, 264.337, -2.988203], [5, 354.14, -200.0, 266.902, -2.988203, 354.14, 0.0, 266.902, -2.988203], [6, 337.547, -200.0, 269.467, -2.988203, 337.547, 0.0, 269.467, -2.988203], [7, 320.953, -200.0, 272.033, -2.988203, 320.953, 0.0, 272.033, -2.988203], [8, 304.36, -200.0, 274.598, -2.988203, 304.36, 0.0, 274.598, -2.988203], [9, 287.767, -200.0, 277.163, -2.988203, 287.767, 0.0, 277.163, -2.988203], [10, 271.174, -200.0, 279.729, -2.988203, 271.174, 0.0, 279.729, -2.988203], [11, 254.581, -200.0, 282.294, -2.988203, 254.581, 0.0, 282.294, -2.988203], [12, 237.988, -200.0, 284.86, -2.988203, 237.988, 0.0, 284.86, -2.988203], [13, 221.394, -200.0, 287.425, -2.988203, 221.394, 0.0, 287.425, -2.988203], [14, 362.091, -200.0, 348.0, 0.0, 362.091, 0.0, 348.0, 0.0], [15, 344.636, -200.0, 348.0, 0.0, 344.636, 0.0, 348.0, 0.0], [16, 327.182, -200.0, 348.0, 0.0, 327.182, 0.0, 348.0, 0.0], [17, 309.727, -200.0, 348.0, 0.0, 309.727, 0.0, 348.0, 0.0], [18, 274.818, -200.0, 348.0, 0.0, 274.818, 0.0, 348.0, 0.0], [19, 257.364, -200.0, 348.0, 0.0, 257.364, 0.0, 348.0, 0.0], [20, 182.948, 0.0, 333.654, -2.709088, 227.97, 0.0, 339.071, 2.562029], [21, 169.198, 0.0, 340.002, -2.709088, 215.53, 0.0, 330.929, 2.562029], [22, 155.447, 0.0, 346.35, -2.709088, 155.447, -200.0, 346.35, -2.709088], [23, 141.696, 0.0, 352.698, -2.709088, 141.696, -200.0, 352.698, -2.709088]];
var LATE_AFTER2 = 20.0;
var g_lt2_shown = -1;
var g_lt2_t = -1.0;

function ltSet2(show) {
    var i, s;
    for (i = 0; i < g_lt2.length; i++) {
        s = g_lt2[i];
        if (show) mx.move_statue(s[0], s[5], s[6], s[7], s[8]);
        else mx.move_statue(s[0], s[1], s[2], s[3], s[4]);
    }
    g_lt2_shown = show;
}

function lateTuff2(seconds) {
    var d = mx.get_gate_drop_time();
    var show = (d < 0 || mx.seconds >= d + LATE_AFTER2);
    if (show != g_lt2_shown || mx.seconds < g_lt2_t || mx.seconds - g_lt2_t > 1.0) {
        ltSet2(show);
        g_lt2_t = mx.seconds;
    }
    if (lateTuff2Prev)
        lateTuff2Prev(seconds);
}

var lateTuff2Prev = mx.frame_handler;
mx.frame_handler = lateTuff2;

/*
USLAND Paris v41e - flammes : panneau START (billboards 0, 1) a chaque chute de grille ; panneau FINISH (billboards 2, 3) quand le
premier finit le 1er tour et quand il finit la course. Texte ASCII expres.
*/
var FL_POS = [[484.58, 19.71, 326.64], [484.58, 19.71, 272.54], [336.75, 33.71, 247.82], [336.75, 33.71, 213.73]];
var FL_TEX = [mx.read_texture("@USLANDParisSupercross2026/js/pyro/flamme_start_0.seq"), mx.read_texture("@USLANDParisSupercross2026/js/pyro/flamme_start_1.seq"),
              mx.read_texture("@USLANDParisSupercross2026/js/pyro/flamme_finish_0.seq"), mx.read_texture("@USLANDParisSupercross2026/js/pyro/flamme_finish_1.seq")];
var FL_SND = [];
var FL_N = 41, FL_FPS = 32.0;
var FL_FIN_TOURS = mx.get_finish_laps(), FL_FIN_TEMPS = mx.get_finish_time();
var fl_k;
for (fl_k = 0; fl_k < 4; fl_k++) {
    FL_SND[fl_k] = mx.add_sound("@USLANDParisSupercross2026/js/sounds/flamme.raw");
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

})();
}
