/*
USLAND Paris - boudins de la ligne de depart : place 0 de 0 a 20 s apres la chute de la grille, puis place 1
(boudins tardifs : enterres puis sortis ; ligne Minerva : deplacee). Texte ASCII expres.
*/

var g_lt = [[0, 637.106, -200.000, 510.075, -2.988203, 637.106, 0.000, 510.075, -2.988203], [1, 620.512, -200.000, 512.640, -2.988203, 620.512, 0.000, 512.640, -2.988203], [2, 603.919, -200.000, 515.206, -2.988203, 603.919, 0.000, 515.206, -2.988203], [3, 587.326, -200.000, 517.771, -2.988203, 587.326, 0.000, 517.771, -2.988203], [4, 570.733, -200.000, 520.337, -2.988203, 570.733, 0.000, 520.337, -2.988203], [5, 554.140, -200.000, 522.902, -2.988203, 554.140, 0.000, 522.902, -2.988203], [6, 537.547, -200.000, 525.467, -2.988203, 537.547, 0.000, 525.467, -2.988203], [7, 520.953, -200.000, 528.033, -2.988203, 520.953, 0.000, 528.033, -2.988203], [8, 504.360, -200.000, 530.598, -2.988203, 504.360, 0.000, 530.598, -2.988203], [9, 487.767, -200.000, 533.163, -2.988203, 487.767, 0.000, 533.163, -2.988203], [10, 471.174, -200.000, 535.729, -2.988203, 471.174, 0.000, 535.729, -2.988203], [11, 454.581, -200.000, 538.294, -2.988203, 454.581, 0.000, 538.294, -2.988203], [12, 437.988, -200.000, 540.860, -2.988203, 437.988, 0.000, 540.860, -2.988203], [13, 421.394, -200.000, 543.425, -2.988203, 421.394, 0.000, 543.425, -2.988203], [14, 562.091, -200.000, 604.000, 0.000000, 562.091, 0.000, 604.000, 0.000000], [15, 544.636, -200.000, 604.000, 0.000000, 544.636, 0.000, 604.000, 0.000000], [16, 527.182, -200.000, 604.000, 0.000000, 527.182, 0.000, 604.000, 0.000000], [17, 509.727, -200.000, 604.000, 0.000000, 509.727, 0.000, 604.000, 0.000000], [18, 474.818, -200.000, 604.000, 0.000000, 474.818, 0.000, 604.000, 0.000000], [19, 457.364, -200.000, 604.000, 0.000000, 457.364, 0.000, 604.000, 0.000000], [20, 382.948, 0.000, 589.654, -2.709088, 427.970, 0.000, 595.071, 2.562029], [21, 369.198, 0.000, 596.002, -2.709088, 415.530, 0.000, 586.929, 2.562029], [22, 355.447, 0.000, 602.350, -2.709088, 355.447, -200.000, 602.350, -2.709088], [23, 341.696, 0.000, 608.698, -2.709088, 341.696, -200.000, 608.698, -2.709088]];
var LATE_AFTER = 20.0;
var g_lt_shown = -1;
var g_lt_t = -1.0;

function ltSet(show) {
    var i, s;
    for (i = 0; i < g_lt.length; i++) {
        s = g_lt[i];
        if (show) mx.move_statue(s[0], s[5], s[6], s[7], s[8]);
        else mx.move_statue(s[0], s[1], s[2], s[3], s[4]);
    }
    g_lt_shown = show;
}

function lateTuff(seconds) {
    var d = mx.get_gate_drop_time();
    var show = (d < 0 || mx.seconds >= d + LATE_AFTER);
    if (show != g_lt_shown || mx.seconds < g_lt_t || mx.seconds - g_lt_t > 1.0) {
        ltSet(show);
        g_lt_t = mx.seconds;
    }
    if (lateTuffPrev)
        lateTuffPrev(seconds);
}

var lateTuffPrev = mx.frame_handler;
mx.frame_handler = lateTuff;

/* USLAND Paris by Ryan v39b - chant sur la grille de depart (une fois, avant la chute de la grille). Texte ASCII expres. */
var CG_SON = mx.add_sound("@USLANDParisbyRyan/sounds/chant_grille.wav");
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

/*
USLAND Paris v41e - flammes : panneau START (billboards 0, 1) a chaque chute de grille ; panneau FINISH (billboards 2, 3) quand le
premier finit le 1er tour et quand il finit la course. Texte ASCII expres.
*/
var FL_POS = [[684.58, 19.71, 582.64], [684.58, 19.71, 528.54], [536.75, 33.71, 503.82], [536.75, 33.71, 469.73]];
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
