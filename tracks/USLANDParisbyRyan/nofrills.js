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
