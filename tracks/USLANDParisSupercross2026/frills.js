/* USLAND Paris by Ryan v42 - meme script dans frills.js et nofrills.js ; verrou si le jeu lance les deux. Texte ASCII expres. */
var USP_CHARGE;
if (!USP_CHARGE) {
USP_CHARGE = 1;
(function () {
/*
USLAND Paris v45d - ecran geant en tableau de chronometrage (Pos, N, Nom, Marque, Nb, Tps total, Ec 1er, Meill Tr, Tps tour),
temps ecoule en vert et temps restant en rouge en haut, meilleur tour en bas. Texte ASCII expres.
*/
var TC_TEX = [mx.read_texture("@USLANDParisSupercross2026/statue/paris/direct/direct_a.seq"), mx.read_texture("@USLANDParisSupercross2026/statue/paris/direct/direct_b.seq")];
var TC_F = {"B": {"h": 22, "c": {"A": [1, 0, 14], "B": [16, 0, 13], "C": [30, 0, 13], "D": [44, 0, 14], "E": [59, 0, 12], "F": [72, 0, 12], "G": [85, 0, 14], "H": [100, 0, 14], "I": [115, 0, 9], "J": [125, 0, 10], "K": [136, 0, 13], "L": [150, 0, 11], "M": [162, 0, 16], "N": [179, 0, 14], "O": [194, 0, 15], "P": [210, 0, 12], "Q": [223, 0, 15], "R": [239, 0, 14], "S": [1, 22, 12], "T": [14, 22, 14], "U": [29, 22, 14], "V": [44, 22, 14], "W": [59, 22, 18], "X": [78, 22, 13], "Y": [92, 22, 14], "Z": [107, 22, 12], "a": [120, 22, 11], "b": [132, 22, 12], "c": [145, 22, 10], "d": [156, 22, 12], "e": [169, 22, 11], "f": [181, 22, 9], "g": [191, 22, 12], "h": [204, 22, 12], "i": [217, 22, 6], "j": [224, 22, 8], "k": [233, 22, 12], "l": [246, 22, 6], "m": [1, 44, 17], "n": [19, 44, 12], "o": [32, 44, 12], "p": [45, 44, 12], "q": [58, 44, 12], "r": [71, 44, 9], "s": [81, 44, 10], "t": [92, 44, 8], "u": [101, 44, 12], "v": [114, 44, 11], "w": [126, 44, 16], "x": [143, 44, 11], "y": [155, 44, 11], "z": [167, 44, 10], "0": [178, 44, 12], "1": [191, 44, 12], "2": [204, 44, 12], "3": [217, 44, 12], "4": [230, 44, 12], "5": [243, 44, 12], "6": [1, 66, 12], "7": [14, 66, 12], "8": [27, 66, 12], "9": [40, 66, 12], ":": [53, 66, 8], ".": [62, 66, 7], "-": [70, 66, 9], "+": [80, 66, 15], "(": [96, 66, 9], ")": [106, 66, 9], "'": [116, 66, 6], "\u00e9": [123, 66, 11], "\u00e8": [135, 66, 11], "\u00b0": [147, 66, 10]}}, "N": {"h": 22, "c": {"0": [1, 88, 13], "1": [15, 88, 13], "2": [29, 88, 13], "3": [43, 88, 13], "4": [57, 88, 14], "5": [72, 88, 13], "6": [86, 88, 13], "7": [100, 88, 13], "8": [114, 88, 13], "9": [128, 88, 13]}}, "V": {"h": 22, "c": {"0": [1, 110, 12], "1": [14, 110, 12], "2": [27, 110, 12], "3": [40, 110, 12], "4": [53, 110, 12], "5": [66, 110, 12], "6": [79, 110, 12], "7": [92, 110, 12], "8": [105, 110, 12], "9": [118, 110, 12], ":": [131, 110, 8], ".": [140, 110, 7], "-": [148, 110, 9]}}, "R": {"h": 22, "c": {"0": [1, 132, 12], "1": [14, 132, 12], "2": [27, 132, 12], "3": [40, 132, 12], "4": [53, 132, 12], "5": [66, 132, 12], "6": [79, 132, 12], "7": [92, 132, 12], "8": [105, 132, 12], "9": [118, 132, 12], ":": [131, 132, 8], ".": [140, 132, 7], "-": [148, 132, 9], "+": [158, 132, 15], " ": [174, 132, 8], "L": [183, 132, 11], "T": [195, 132, 14], "O": [210, 132, 15], "U": [226, 132, 14], "R": [241, 132, 14], "S": [1, 154, 12]}}};
var TC_COLS = {"pos": [6, 38, "c"], "num": [46, 98, "c"], "nom": [108, 252, "g"], "marque": [268, 390, "c"], "tours": [410, 490, "c"], "total": [530, 640, "d"], "ecart": [660, 756, "d"], "meill": [790, 884, "d"], "tour": [918, 1014, "d"]};
var TC_NL = 9, TC_NM = 1, TC_MO = 1024, TC_Y0 = 19, TC_H = 23, TC_DY = 0, TC_YBAS = 229, TC_XMT = 72, TC_YHAUT = 229;
var TC_XV = [780, 884], TC_XR = [900, 1012], TC_MT = [104, 172, 268];
var TC_MARQUES = [[/^crf?[0-9]+/, "Honda"], [/^[0-9]+sx/, "KTM"], [/^kx[0-9]+/, "Kawasaki"], [/^yz[0-9]+/, "Yamaha"], [/^rmz?[0-9]+/, "Suzuki"], [/^fc[0-9]+/, "Husqvarna"], [/^mc[0-9]+/, "GasGas"], [/^tf[0-9]+/, "Triumph"]];
var TC_FIN_TOURS = mx.get_finish_laps(), TC_FIN_TEMPS = mx.get_finish_time();
var tc_ordre = [], tc_cur = -1, tc_stats = {}, tc_s = -100, tc_mt = [-1, -1];

function tc_larg(f, s) {
    var i, c, w = 0;
    for (i = 0; i < s.length; i++) {
        if (s[i] == " ") { w += 4; continue; }
        c = f.c[s[i]]; if (c) w += c[2] - 2;
    }
    return w;
}
function tc_txt(f, x, y, s) {                         /* x, y de l'ecran entier (1024 x 256) ; reste dans le panneau de x */
    var i, c, k = Math.floor(x / 256), t = (k < 2) ? 0 : 1, xp = x - 256 * k, yp = y + ((k % 2) ? 256 : 0);
    if (t != tc_cur) return;
    for (i = 0; i < s.length; i++) {
        if (s[i] == " ") { xp += 4; continue; }
        c = f.c[s[i]]; if (!c) continue;
        mx.paste_custom_frame(TC_TEX[t], 1, c[0] / 256, c[1] / 512, xp / 256, yp / 512, c[2] / 256, f.h / 512);
        xp += c[2] - 2;
    }
}
function tc_col(f, k, y, s, o) {                      /* texte dans la colonne k de la moitie qui commence en o, coupe a sa largeur */
    var c = TC_COLS[k], w = c[1] - c[0];
    while (s.length > 1 && tc_larg(f, s) > w) s = s.substring(0, s.length - 1);
    if (c[2] == "g") tc_txt(f, o + c[0], y, s);
    else if (c[2] == "d") tc_txt(f, o + c[1] - tc_larg(f, s), y, s);
    else tc_txt(f, o + (c[0] + c[1]) / 2 - tc_larg(f, s) / 2, y, s);
}
function td_nom(s) {                                 /* pour le module d'evenements (ev_nom) : dernier mot du nom, 9 lettres */
    var m = s.replace(/\|.*/, "").replace(/^\s+|\s+$/g, "").split(" ");
    return m[m.length - 1].toUpperCase().substring(0, 9);
}
function tc_2(n) { n = Math.floor(n).toString(); return n.length < 2 ? "0" + n : n; }
function tc_chrono(t) {                               /* 45.025 / 1:05.123 / 5:55.185 */
    var m = Math.floor(t / 60), s = t - 60 * m;
    if (m < 1) return s.toFixed(3);
    return m + ":" + (s < 10 ? "0" : "") + s.toFixed(3);
}
function tc_marque(m) {
    var i;
    for (i = 0; i < TC_MARQUES.length; i++) if (m.match(TC_MARQUES[i][0])) return TC_MARQUES[i][1];
    return "";
}
function tc_nom(s) {                                  /* "Sacha Coenen" -> "COENEN Sacha" */
    var m = s.replace(/\|.*/, "").replace(/^\s+|\s+$/g, "").split(/\s+/), n;
    if (m.length < 2) return m[0].toUpperCase();
    n = m.pop().toUpperCase();
    return n + " " + m.join(" ");
}
function tc_maj() {                                   /* tours, temps total, meilleur tour, dernier tour : 1 fois par seconde */
    var i, k, r, n, t1, t2, st, d = mx.get_gate_drop_time();
    if (mx.seconds >= tc_s && mx.seconds - tc_s < 1.0) return;
    tc_s = mx.seconds; tc_stats = {}; tc_mt = [-1, -1];
    for (i = 0; i < tc_ordre.length; i++) {
        r = tc_ordre[i]; n = mx.index_to_lap(r.position); st = { tours: n, total: -1, meill: -1, der: -1 };
        if (n >= 1 && d >= 0) { t2 = mx.get_timing(r.slot, mx.lap_to_index(n)); if (t2 >= 0) st.total = t2 - d; }
        for (k = 1; k < n; k++) {
            t1 = mx.get_timing(r.slot, mx.lap_to_index(k)); t2 = mx.get_timing(r.slot, mx.lap_to_index(k + 1));
            if (t1 >= 0 && t2 > t1) {
                st.der = t2 - t1;
                if (st.meill < 0 || t2 - t1 < st.meill) st.meill = t2 - t1;
            }
        }
        if (st.meill > 0 && (tc_mt[0] < 0 || st.meill < tc_mt[0])) tc_mt = [st.meill, r.slot];
        tc_stats[r.slot] = st;
    }
}
function tc_ecart(r, l) {                             /* ecart au premier au meme point de chrono, ou tours de retard */
    var L = mx.lap_to_index(2) - mx.lap_to_index(1), n, t0, t1;
    if (L > 0) { n = Math.floor((l.position - r.position) / L); if (n >= 1) return "+" + n + " L"; }
    t0 = mx.get_timing(l.slot, r.position); t1 = mx.get_timing(r.slot, r.position);
    if (t0 < 0 || t1 < 0) return "";
    return tc_chrono(Math.max(0, t1 - t0));
}
function tc_haut() {                                  /* [ecoule (vert), restant (rouge)] */
    var d = mx.get_gate_drop_time(), e = (d < 0 || mx.seconds < d) ? 0 : mx.seconds - d, r, l;
    var ec = tc_2(e / 3600) + ":" + tc_2((e % 3600) / 60) + ":" + tc_2(e % 60);
    if (TC_FIN_TEMPS > 0) {
        r = Math.max(0, TC_FIN_TEMPS - e);
        return [ec, tc_2(r / 60) + ":" + tc_2(r % 60) + (TC_FIN_TOURS > 0 ? " +" + TC_FIN_TOURS.toFixed(0) + " L" : "")];
    }
    l = TC_FIN_TOURS - (tc_ordre.length > 0 && tc_ordre[0].position >= 1 ? mx.index_to_lap(tc_ordre[0].position) : 0);
    return [ec, Math.max(0, l).toFixed(0) + " TOURS"];
}
function tc_page(t) {
    var i, r, st, y, s, h, f, mq, o;
    tc_cur = t;
    mx.begin_custom_frame(TC_TEX[t]);
    mx.paste_custom_frame(TC_TEX[t], 0, 0, 0, 0, 0, 1, 1);
    h = tc_haut();
    tc_txt(TC_F.V, TC_XV[1] - tc_larg(TC_F.V, h[0]), TC_YHAUT, h[0]);
    tc_txt(TC_F.R, TC_XR[1] - tc_larg(TC_F.R, h[1]), TC_YHAUT, h[1]);
    for (i = 0; i < TC_NL * TC_NM && i < tc_ordre.length; i++) {      /* v45e : places 1-11 a gauche, 12-22 a droite */
        r = tc_ordre[i];
        if (r.position < 1) break;
        st = tc_stats[r.slot] || { tours: 0, total: -1, meill: -1, der: -1 };
        y = TC_Y0 + (i % TC_NL) * TC_H + TC_DY; o = Math.floor(i / TC_NL) * TC_MO;
        tc_col(TC_F.B, "pos", y, (i + 1).toString(), o);
        tc_col(TC_F.N, "num", y, mx.get_rider_number(r.slot).toString(), o);
        s = tc_nom(mx.get_rider_name(r.slot));                               /* v45h : trop long -> initiale du prenom */
        if (tc_larg(TC_F.B, s) > TC_COLS.nom[1] - TC_COLS.nom[0] && s.indexOf(" ") > 0) s = s.substring(0, s.indexOf(" ") + 2) + ".";
        tc_col(TC_F.B, "nom", y, s, o);
        mq = tc_marque(mx.get_bike_model(r.slot)); if (mq) tc_col(TC_F.B, "marque", y, mq, o);
        tc_col(TC_F.B, "tours", y, st.tours.toString(), o);
        if (st.total > 0) tc_col(TC_F.B, "total", y, tc_chrono(st.total), o);
        tc_col(TC_F.B, "ecart", y, i == 0 ? "-" : tc_ecart(r, tc_ordre[0]), o);
        f = (st.der > 0 && st.der == st.meill) ? TC_F.V : TC_F.B;           /* record perso au dernier tour : en vert */
        if (st.meill > 0) tc_col(f, "meill", y, tc_chrono(st.meill), o);
        if (st.der > 0) tc_col(f, "tour", y, tc_chrono(st.der), o);
    }
    if (tc_mt[0] > 0) {
        tc_txt(TC_F.B, TC_MT[0], TC_YBAS, tc_chrono(tc_mt[0]));                                   /* v45f : 3 parties espacees */
        tc_txt(TC_F.B, TC_MT[1], TC_YBAS, "(N\u00b0 " + mx.get_rider_number(tc_mt[1]) + ")");
        s = tc_nom(mx.get_rider_name(tc_mt[1]));
        while (s.length > 1 && TC_MT[2] - 256 + tc_larg(TC_F.B, s) > 250) s = s.substring(0, s.length - 1);
        tc_txt(TC_F.B, TC_MT[2], TC_YBAS, s);
    }
    mx.end_custom_frame(TC_TEX[t]);
}
function tc_image(secs) {
    try { ev_maj(); } catch (e) { mx.message("evenements : " + e.toString()); }
    try { tc_ordre = mx.get_running_order(); tc_maj(); tc_page(0); tc_page(1); } catch (e) { mx.message("classement : " + e.toString()); }
    tc_prev(secs);
}
var tc_prev = mx.frame_handler;
if (!tc_prev) tc_prev = function (s) {};
mx.frame_handler = tc_image;

/*
USLAND Paris - evenements de course (code USLAND, v44) : son de la grille, holeshot (ecran + public), vainqueur et recompenses
de fin de manche sur l'ecran geant (vainqueur, holeshot, hard charger, meilleur tour), public sur les chutes du top 3 et les
bagarres (depassements dans le top 3). Texte ASCII expres.
*/
var EV_Y = [147, 177, 205];
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
var EV_S_PUBLIC = ev_sons("@USLANDParisSupercross2026/js/sounds/public.raw", 0.62, 44100, 3);   /* v45i : copies a la camera (volume plafonne a 1) */
var EV_S_OOH = ev_sons("@USLANDParisSupercross2026/js/sounds/public.raw", 0.62, 33075, 3);
var EV_S_ANNONCE = ev_son("@USLANDParisSupercross2026/js/sounds/annonce.raw", 1.00, 44100);   /* v44c : annonce "le plus beau supercross du monde, c est Paris" */
var EV_HP = [[201.4, 50.0, 261.1], [201.4, 50.0, 419.7], [402.6, 50.0, 261.1], [402.6, 50.0, 419.7]];                                              /* v44d : hauts-parleurs au-dessus de la piste (remplace par le build) */
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
EV_MUS_DUREE = 79.40;
for (ev_k = 0; ev_k < EV_HP.length; ev_k++) {
    EV_S_MUS.push(ev_son("@USLANDParisSupercross2026/js/sounds/musique.raw", 0.4, 44100));
    if (EV_S_MUS[ev_k] >= 0) mx.set_sound_pos(EV_S_MUS[ev_k], EV_HP[ev_k][0], EV_HP[ev_k][1], EV_HP[ev_k][2]);
}
EV_S_MUS_CAM = ev_sons("@USLANDParisSupercross2026/js/sounds/musique.raw", 1.0, 44100, 2);   /* copies a la camera */
EV_S_MUS = EV_S_MUS.concat(EV_S_MUS_CAM);
var EV_ANNONCE_MAX = 120.0;                                           /* si un pilote ne finit jamais (abandon) : annonce 120 s apres le vainqueur */
var EV_S_FOULE = ev_son("@USLANDParisSupercross2026/js/sounds/foule.raw", 0.62, 44100);  /* v44b : bruit du public en continu, suit la camera */
var EV_FOULE_DUREE = 21.22, ev_foule_t = -1000, ev_foule_v = 0.62;
var EV_FOULE_FIN = 0.16;                                              /* v45h : foule plus basse apres l'arrivee (la chanson par-dessus) */                        /* v45c : relance a chaque fin (pas de boucle du jeu, pas au chargement) */
function ev_foule() {
    if (EV_S_FOULE < 0) return;
    mx.set_sound_pos(EV_S_FOULE, ev_p[0], ev_p[1], ev_p[2]);
    if ((ev_fin_t >= 0 ? EV_FOULE_FIN : 0.62) != ev_foule_v) {        /* volume change : on relance a ce volume */
        ev_foule_v = ev_fin_t >= 0 ? EV_FOULE_FIN : 0.62;
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
