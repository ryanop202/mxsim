/*
USLAND: Supercross Paris 2026 - long tuff block le long de la ligne de depart reprise par le tour.
Enterre au depart (il generait le depart), il sort du sol LATE_AFTER s apres la chute de la grille.
Sans chute de grille (entrainement libre) il est la (v9). Texte ASCII expres.
*/

var g_lt = [];
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
