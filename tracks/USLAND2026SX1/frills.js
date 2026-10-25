/*
USLAND 2026 SX - finish line flames (taken from the MX Simulator SX 2026 Anaheim 1 frills.js, positions adapted).
billboards 0-1: flames on the two FINISH arch torches, hidden until the winner crosses the finish line.
Plain ASCII on purpose (v13b: accented comments made the game crash while loading the track script).
*/

// sound
var finishFlameSound = mx.add_sound("@USLAND2026SX1/js/sounds/finishlineflame.raw");
mx.set_sound_freq(finishFlameSound, 44100);
mx.set_sound_vol(finishFlameSound, 1.0);
mx.set_sound_pos(finishFlameSound, 182.5, 40.4, 118.0);

// animations
var finishFlames = mx.read_texture('@USLAND2026SX1/js/pyro/finishflames.seq');
var finishFlames2 = mx.read_texture('@USLAND2026SX1/js/pyro/finishflames2.seq');
var currentFrame = 0;
var totalFrames = 41;
var secondsSinceUpdate = 0;
var flamesOn = false;

// hide the flame billboards until called upon
mx.color_billboard(0, 1, 1, 1, 0);
mx.color_billboard(1, 1, 1, 1, 0);

// winner: same last lap logic as the Anaheim finish flagger; once the checkered flag is out,
// the next lap change of the leader is the winner crossing the line
var g_win_drop = -1;
var g_win_last_lap = 1000000;
var g_win_finish_laps = mx.get_finish_laps();
var g_win_finish_time = mx.get_finish_time();
var g_win_checkered = false;
var g_win_checkered_lap = -1;

function checkWinner() {
    var p, l;
    if (g_win_drop < 0)
        g_win_drop = mx.get_gate_drop_time();
    if (g_win_drop < 0 || mx.seconds < g_win_drop)
        return false;
    p = mx.get_running_order_position(0);
    if (g_win_last_lap == 1000000) {
        if (g_win_finish_time == 0)
            g_win_last_lap = g_win_finish_laps;
        else if (mx.seconds >= g_win_drop + g_win_finish_time)
            g_win_last_lap = mx.index_to_lap(p) + 1 + g_win_finish_laps;
    }
    l = mx.index_to_lap(p + 1);
    if (!g_win_checkered && l >= g_win_last_lap) {
        g_win_checkered = true;
        g_win_checkered_lap = mx.index_to_lap(p);
    }
    return g_win_checkered && mx.index_to_lap(p) > g_win_checkered_lap;
}

function finishPyro(seconds) {
    if (!flamesOn && checkWinner()) {
        flamesOn = true;
        mx.start_sound(finishFlameSound);
    }
    if (flamesOn && currentFrame <= totalFrames && seconds - secondsSinceUpdate >= 1 / 32.0) {
        secondsSinceUpdate = seconds;
        if (currentFrame < totalFrames) {
            mx.begin_custom_frame(finishFlames);
            mx.begin_custom_frame(finishFlames2);
            mx.paste_custom_frame(finishFlames, currentFrame, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0);
            mx.paste_custom_frame(finishFlames2, currentFrame, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0);
            mx.end_custom_frame(finishFlames);
            mx.end_custom_frame(finishFlames2);
            if (currentFrame === 0) {
                mx.color_billboard(0, 1, 1, 1, 1);
                mx.color_billboard(1, 1, 1, 1, 1);
            }
        } else {
            mx.color_billboard(0, 1, 1, 1, 0);
            mx.color_billboard(1, 1, 1, 1, 0);
        }
        currentFrame++;
    }
    finishPyroPrev(seconds);
}

var finishPyroPrev = mx.frame_handler;
mx.frame_handler = finishPyro;
