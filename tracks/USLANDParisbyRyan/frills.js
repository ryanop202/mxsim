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
        p = td_2(r.position);
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

var g_lt2 = [[0, 637.106, -200.000, 510.075, -2.988203, 637.106, 0.000, 510.075, -2.988203], [1, 620.512, -200.000, 512.640, -2.988203, 620.512, 0.000, 512.640, -2.988203], [2, 603.919, -200.000, 515.206, -2.988203, 603.919, 0.000, 515.206, -2.988203], [3, 587.326, -200.000, 517.771, -2.988203, 587.326, 0.000, 517.771, -2.988203], [4, 570.733, -200.000, 520.337, -2.988203, 570.733, 0.000, 520.337, -2.988203], [5, 554.140, -200.000, 522.902, -2.988203, 554.140, 0.000, 522.902, -2.988203], [6, 537.547, -200.000, 525.467, -2.988203, 537.547, 0.000, 525.467, -2.988203], [7, 520.953, -200.000, 528.033, -2.988203, 520.953, 0.000, 528.033, -2.988203], [8, 504.360, -200.000, 530.598, -2.988203, 504.360, 0.000, 530.598, -2.988203], [9, 487.767, -200.000, 533.163, -2.988203, 487.767, 0.000, 533.163, -2.988203], [10, 471.174, -200.000, 535.729, -2.988203, 471.174, 0.000, 535.729, -2.988203], [11, 454.581, -200.000, 538.294, -2.988203, 454.581, 0.000, 538.294, -2.988203], [12, 437.988, -200.000, 540.860, -2.988203, 437.988, 0.000, 540.860, -2.988203], [13, 421.394, -200.000, 543.425, -2.988203, 421.394, 0.000, 543.425, -2.988203], [14, 562.091, -200.000, 600.000, 0.000000, 562.091, 0.000, 600.000, 0.000000], [15, 544.636, -200.000, 600.000, 0.000000, 544.636, 0.000, 600.000, 0.000000], [16, 527.182, -200.000, 600.000, 0.000000, 527.182, 0.000, 600.000, 0.000000], [17, 509.727, -200.000, 600.000, 0.000000, 509.727, 0.000, 600.000, 0.000000], [18, 474.818, -200.000, 600.000, 0.000000, 474.818, 0.000, 600.000, 0.000000], [19, 457.364, -200.000, 600.000, 0.000000, 457.364, 0.000, 600.000, 0.000000], [20, 382.948, 0.000, 589.654, -2.709088, 427.970, 0.000, 595.071, 2.562029], [21, 369.198, 0.000, 596.002, -2.709088, 415.530, 0.000, 586.929, 2.562029], [22, 355.447, 0.000, 602.350, -2.709088, 355.447, -200.000, 602.350, -2.709088], [23, 341.696, 0.000, 608.698, -2.709088, 341.696, -200.000, 608.698, -2.709088]];
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
