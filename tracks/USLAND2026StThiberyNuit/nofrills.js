/*
USLAND 2026 Saint-Thibery (night): start-only boudins.
Statues using the startb_*.png textures (no collision) stay until 15.0 s after the gate drop,
then they are moved under the ground. Before a gate drop (practice) they stay. Plain ASCII on purpose.
*/

var g_sb = [[54, 603.442, 412.605, -1.962165], [55, 601.128, 418.215, -1.962165], [56, 598.812, 423.825, -1.962165], [57, 596.497, 429.435, -1.962165], [58, 594.183, 435.045, -1.962165], [59, 591.867, 440.655, -1.962165], [60, 589.553, 446.265, -1.962165], [61, 587.237, 451.875, -1.962165], [62, 584.923, 457.485, -1.962165], [63, 582.607, 463.095, -1.962165], [64, 580.293, 468.705, -1.962165], [65, 577.977, 474.315, -1.962165], [66, 575.663, 479.925, -1.962165], [67, 573.347, 485.535, -1.962165], [68, 571.033, 491.145, -1.962165], [69, 568.717, 496.755, -1.962165], [70, 566.403, 502.365, -1.962165], [71, 564.087, 507.975, -1.962165], [72, 561.773, 513.585, -1.962165], [73, 559.457, 519.195, -1.962165], [74, 252.474, 427.673, -0.594759], [75, 257.421, 431.020, -0.594759], [76, 262.369, 434.367, -0.594759], [77, 267.316, 437.714, -0.594759], [78, 272.264, 441.061, -0.594759], [79, 277.211, 444.408, -0.594759], [80, 282.159, 447.755, -0.594759], [81, 287.746, 449.178, -0.047583], [82, 293.713, 449.463, -0.047583], [83, 299.679, 449.747, -0.047583], [84, 305.646, 450.031, -0.047583], [85, 311.612, 450.315, -0.047583], [86, 317.579, 450.599, -0.047583], [87, 323.545, 450.883, -0.047583], [88, 329.512, 451.167, -0.047583], [89, 335.478, 451.451, -0.047583], [90, 341.445, 451.735, -0.047583], [91, 347.411, 452.020, -0.047583], [92, 353.378, 452.304, -0.047583], [93, 359.344, 452.588, -0.047583], [94, 365.311, 452.872, -0.047583], [95, 371.281, 453.000, -0.000000], [96, 377.254, 453.000, -0.000000], [97, 383.227, 453.000, -0.000000], [98, 389.201, 453.000, -0.000000], [99, 395.174, 453.000, -0.000000], [100, 401.147, 453.000, -0.000000], [101, 407.120, 453.000, -0.000000], [102, 413.094, 453.000, -0.000000], [103, 419.067, 453.000, -0.000000], [104, 425.040, 453.000, -0.000000], [105, 431.013, 453.000, -0.000000], [106, 205.000, 528.000, -0.000000], [107, 211.000, 528.000, -0.000000], [108, 217.000, 528.000, -0.000000], [109, 223.000, 528.000, -0.000000], [110, 229.000, 528.000, -0.000000], [111, 235.000, 528.000, -0.000000]];
var g_sb_after = 15.0;
var g_sb_hidden = -1;
var g_sb_t = -1.0;

function sbSet(hide) {
    var i, s;
    for (i = 0; i < g_sb.length; i++) {
        s = g_sb[i];
        mx.move_statue(s[0], s[1], hide ? -200.0 : 0.0, s[2], s[3]);
    }
    g_sb_hidden = hide;
}

function startBoudins(seconds) {
    var d = mx.get_gate_drop_time();
    var hide = (d >= 0 && mx.seconds >= d + g_sb_after);
    if (hide != g_sb_hidden || mx.seconds < g_sb_t || mx.seconds - g_sb_t > 1.0) {
        sbSet(hide);
        g_sb_t = mx.seconds;
    }
    if (startBoudinsPrev)
        startBoudinsPrev(seconds);
}

var startBoudinsPrev = mx.frame_handler;
mx.frame_handler = startBoudins;


/* v60: START sign flames (billboards 0 and 1) + flame sound, fired at the gate drop (again after each New Race). */
var g_py_snd = [];
var g_py_pos = [[149.25, 23.38, 438.00], [149.25, 23.38, 518.00]];
var g_py_i;
for (g_py_i = 0; g_py_i < 2; g_py_i++) {
    g_py_snd[g_py_i] = mx.add_sound("@USLAND2026StThiberyNuit/js/sounds/startflame.raw");
    mx.set_sound_freq(g_py_snd[g_py_i], 44100);
    mx.set_sound_vol(g_py_snd[g_py_i], 1.0);
    mx.set_sound_pos(g_py_snd[g_py_i], g_py_pos[g_py_i][0], g_py_pos[g_py_i][1], g_py_pos[g_py_i][2]);
}
var g_py_tex = [mx.read_texture('@USLAND2026StThiberyNuit/js/pyro/finishflames2.seq'), mx.read_texture('@USLAND2026StThiberyNuit/js/pyro/finishflames.seq')];
var g_py_frames = 41;
var g_py_frame = -1;
var g_py_fired = -1;
var g_py_t = -1.0;
mx.color_billboard(0, 1, 1, 1, 0);
mx.color_billboard(1, 1, 1, 1, 0);

function pyroShow(a) {
    mx.color_billboard(0, 1, 1, 1, a);
    mx.color_billboard(1, 1, 1, 1, a);
}

function startPyro(seconds) {
    var d = mx.get_gate_drop_time();
    var k;
    if (d < 0 || mx.seconds < d || mx.seconds < g_py_t) {
        if (g_py_frame >= 0) pyroShow(0);
        g_py_frame = -1;
        if (d < 0 || mx.seconds < d) g_py_fired = -1;
        g_py_t = mx.seconds;
    }
    else if (g_py_fired != d && mx.seconds < d + 3.0) {
        g_py_fired = d;
        g_py_frame = 0;
        g_py_t = -1.0;
        for (k = 0; k < 2; k++) mx.start_sound(g_py_snd[k]);
    }
    if (g_py_frame >= 0 && mx.seconds - g_py_t >= 0.03125) {
        g_py_t = mx.seconds;
        if (g_py_frame < g_py_frames) {
            for (k = 0; k < 2; k++) {
                mx.begin_custom_frame(g_py_tex[k]);
                mx.paste_custom_frame(g_py_tex[k], g_py_frame, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0);
                mx.end_custom_frame(g_py_tex[k]);
            }
            if (g_py_frame == 0) pyroShow(1);
            g_py_frame++;
        } else {
            pyroShow(0);
            g_py_frame = -1;
        }
    }
    if (startPyroPrev)
        startPyroPrev(seconds);
}

var startPyroPrev = mx.frame_handler;
mx.frame_handler = startPyro;
