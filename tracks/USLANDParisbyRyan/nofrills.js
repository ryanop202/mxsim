/*
USLAND Paris v28 - boudins sponsors de la ligne de depart et boudin Automoto du virage apres le saut AMV :
invisibles de 0 a 20 s, ils sortent du sol 20 s apres la chute de la grille. Texte ASCII expres.
*/

var g_lt = [[0, 637.013, 509.184, -3.087798], [1, 620.145, 510.191, -3.080132], [2, 603.288, 511.367, -3.069805], [3, 587.074, 515.128, -2.721517], [4, 571.758, 522.265, -2.695174], [5, 555.336, 525.366, -3.039173], [6, 538.535, 527.173, -3.034314], [7, 521.740, 529.038, -3.026716], [8, 504.963, 531.058, -3.019132], [9, 488.196, 533.150, -3.004006], [10, 471.463, 535.509, -2.996466], [11, 454.743, 537.953, -2.996466], [12, 438.037, 540.494, -2.988943], [13, 421.376, 543.309, -2.975147], [14, 562.091, 600.000, 0.000000], [15, 544.636, 600.000, 0.000000], [16, 527.182, 600.000, 0.000000], [17, 509.727, 600.000, 0.000000], [18, 474.818, 600.000, 0.000000], [19, 457.364, 600.000, 0.000000], [20, 382.948, 589.654, -2.709088], [21, 369.198, 596.002, -2.709088], [22, 355.447, 602.350, -2.709088], [23, 341.696, 608.698, -2.709088]];
var LATE_AFTER = 20.0;
var g_lt_shown = -1;
var g_lt_t = -1.0;

function ltSet(show) {
    var i, s;
    for (i = 0; i < g_lt.length; i++) {
        s = g_lt[i];
        mx.move_statue(s[0], s[1], show ? 0.0 : -200.0, s[2], s[3]);
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
