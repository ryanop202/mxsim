/* USLAND Paris by Ryan v42 - meme script dans frills.js et nofrills.js ; verrou si le jeu lance les deux. Texte ASCII expres. */
var USP_CHARGE;
if (!USP_CHARGE) {
USP_CHARGE = 1;
(function () {
/*
USLAND Paris by Ryan v39b - classement en direct sur tout l'ecran geant (DA de la retransmission Supercross Paris).
Fait comme la tour de classement de ZION 2025 Supercross Paris (pages 256 x 512, dessin a chaque image). Texte ASCII expres.
*/
var TD_A = mx.read_texture("@USLANDParisbyRyan/statue/paris/direct/direct_a.seq");
var TD_B = mx.read_texture("@USLANDParisbyRyan/statue/paris/direct/direct_b.seq");
var TD_W = 256, TD_H = 512;
var TD_N = { h: 26, c: {"A": [1, 0, 16], "B": [18, 0, 15], "C": [34, 0, 15], "D": [50, 0, 15], "E": [66, 0, 14], "F": [81, 0, 13], "G": [95, 0, 16], "H": [112, 0, 16], "I": [129, 0, 9], "J": [139, 0, 13], "K": [153, 0, 17], "L": [171, 0, 13], "M": [185, 0, 18], "N": [204, 0, 16], "O": [221, 0, 16], "P": [238, 0, 14], "Q": [1, 26, 16], "R": [18, 26, 16], "S": [35, 26, 14], "T": [50, 26, 14], "U": [65, 26, 16], "V": [82, 26, 16], "W": [99, 26, 21], "X": [121, 26, 16], "Y": [138, 26, 16], "Z": [155, 26, 14], "0": [170, 26, 13], "1": [184, 26, 13], "2": [198, 26, 13], "3": [212, 26, 13], "4": [226, 26, 13], "5": [240, 26, 13], "6": [1, 52, 13], "7": [15, 52, 13], "8": [29, 52, 13], "9": [43, 52, 13], "-": [57, 52, 8], "'": [66, 52, 7], ".": [74, 52, 8]} };
var TD_P = { h: 26, c: {"0": [1, 78, 13], "1": [15, 78, 13], "2": [29, 78, 13], "3": [43, 78, 13], "4": [57, 78, 13], "5": [71, 78, 13], "6": [85, 78, 13], "7": [99, 78, 13], "8": [113, 78, 13], "9": [127, 78, 13], ".": [141, 78, 8]} };
var TD_D = { h: 26, c: {"0": [1, 104, 13], "1": [15, 104, 13], "2": [29, 104, 13], "3": [43, 104, 13], "4": [57, 104, 13], "5": [71, 104, 13], "6": [85, 104, 13], "7": [99, 104, 13], "8": [113, 104, 13], "9": [127, 104, 13]} };
var TD_T = { h: 56, c: {"0": [1, 130, 25], "1": [27, 130, 25], "2": [53, 130, 25], "3": [79, 130, 25], "4": [105, 130, 25], "5": [131, 130, 25], "6": [157, 130, 25], "7": [183, 130, 25], "8": [209, 130, 25], "9": [1, 186, 25], ":": [27, 186, 14], "+": [42, 186, 25], "L": [68, 186, 25]} };
var TD_BANDES = {"honda": 0, "ktm": 1, "kawasaki": 2, "yamaha": 3, "suzuki": 4, "husqvarna": 5, "gasgas": 6, "triumph": 7, "none": 8}, TD_BY = 242;
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
function td_rangees(y0, k0, n) {                              /* places k0+1 .. k0+n dans le carre qui commence a y0 */
    var k, r, yy, p;
    for (k = k0; k < k0 + n && k < td_ordre.length; k++) {
        r = td_ordre[k];
        if (r.position < 1) break;
        yy = y0 + (k - k0) * 32 + 3;
        p = td_2(k + 1);                                        /* v42 : la place (r.position = portes de chrono passees : 44) */
        td_txt(TD_D, (4 + 40) / 2 - td_larg(TD_D, p) / 2, yy, p);
        td_cp(1, TD_BANDES[td_marque(mx.get_bike_model(r.slot))] * 10, TD_BY, 44, yy - 1, 6, 32 - 4);
        td_txt(TD_P, 55, yy, mx.get_rider_number(r.slot).toString() + ".");
        td_txt(TD_N, 116, yy, td_nom(mx.get_rider_name(r.slot)));
    }
}
function td_dessine(secs) {
    var s;
    td_ordre = mx.get_running_order();
    td_tex = TD_A;
    mx.begin_custom_frame(TD_A);
    td_cp(0, 0, 0, 0, 0, TD_W, TD_H);
    s = td_haut();
    td_txt(TD_T, TD_W / 2 - td_larg(TD_T, s) / 2, 168, s);
    td_rangees(256, 0, 8);
    mx.end_custom_frame(TD_A);
    td_tex = TD_B;
    mx.begin_custom_frame(TD_B);
    td_cp(0, 0, 0, 0, 0, TD_W, TD_H);
    td_rangees(0, 8, 8);
    td_rangees(256, 2 * 8, 6);
    mx.end_custom_frame(TD_B);
}
function td_image(secs) {
    try { td_dessine(secs); } catch (e) { mx.message("classement : " + e.toString()); }
    td_prev(secs);
}
var td_prev = mx.frame_handler;
if (!td_prev) td_prev = function (s) {};
mx.frame_handler = td_image;

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
var FL_TEX = [mx.read_texture("@USLANDParisbyRyan/js/pyro/flamme_start_0.seq"), mx.read_texture("@USLANDParisbyRyan/js/pyro/flamme_start_1.seq"),
              mx.read_texture("@USLANDParisbyRyan/js/pyro/flamme_finish_0.seq"), mx.read_texture("@USLANDParisbyRyan/js/pyro/flamme_finish_1.seq")];
var FL_SND = [];
var FL_N = 41, FL_FPS = 32.0;
var FL_FIN_TOURS = mx.get_finish_laps(), FL_FIN_TEMPS = mx.get_finish_time();
var fl_k;
for (fl_k = 0; fl_k < 4; fl_k++) {
    FL_SND[fl_k] = mx.add_sound("@USLANDParisbyRyan/js/sounds/flamme.raw");
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

/* USLAND Paris by Ryan v39b - chant sur la grille de depart (une fois, avant la chute de la grille). Texte ASCII expres. */
var CG_SON = mx.add_sound("@USLANDParisbyRyan/sounds/chant_grille.raw");
mx.set_sound_freq(CG_SON, 44100);
mx.set_sound_vol(CG_SON, 0.70);
var cg_fait = false, cg_p = [], cg_r = [], cg_t0 = -1, CG_AVANT = 8.0;
function cg_image(secs) {
    try {
        var d = mx.get_gate_drop_time();
        mx.get_camera_location(cg_p, cg_r);
        mx.set_sound_pos(CG_SON, cg_p[0], cg_p[1], cg_p[2]);
        if (cg_t0 < 0) cg_t0 = mx.seconds;
        if (!cg_fait && ((d > 0 && mx.seconds >= d - CG_AVANT && mx.seconds < d) || (d < 0 && mx.seconds - cg_t0 >= 2.0))) {
            mx.start_sound(CG_SON); cg_fait = true;
        }
    } catch (e) { mx.message("chant : " + e.toString()); }
    cg_prev(secs);
}
var cg_prev = mx.frame_handler;
if (!cg_prev) cg_prev = function (s) {};
mx.frame_handler = cg_image;

})();
}
