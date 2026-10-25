/*
USLAND 2026 SX - flammes de l'arrivée (repris du frills.js de MX Simulator SX 2026 Anaheim 1, positions adaptées).
billboards 0-1 : flammes sur les 2 poteaux de l'arche FINISH, cachées au repos.
Elles jouent une seule fois : quand le vainqueur passe la ligne d'arrivée à la fin de la course.
*/
function _chain(prev, s) { if (typeof prev === "function") prev(s); }

var finishFlameSound = mx.add_sound("@USLAND2026SX1/js/sounds/finishlineflame.raw");
mx.set_sound_freq(finishFlameSound, 44100);
mx.set_sound_vol(finishFlameSound, 1.0);
mx.set_sound_pos(finishFlameSound, 677.0, 40.3, 250.0);

var finishFlames = mx.read_texture('@USLAND2026SX1/js/pyro/finishflames.seq');
var finishFlames2 = mx.read_texture('@USLAND2026SX1/js/pyro/finishflames2.seq');
var totalFrames = 41;
var currentFrame = totalFrames + 1;       // > totalFrames = not playing
var secondsSinceUpdate = 0;

mx.color_billboard(0, 1, 1, 1, 0);
mx.color_billboard(1, 1, 1, 1, 0);

function fireFinishFlames() {
    currentFrame = 0;
    mx.start_sound(finishFlameSound);
}

// winner: same last-lap logic as the Anaheim finish flagger; once the checkered flag is out,
// the leader's next lap change is the winner crossing the line
var g_drop = -1, g_last_lap = 1000000, g_finish_laps = mx.get_finish_laps(), g_finish_time = mx.get_finish_time();
var checkered = false, checkeredLap = -1, winnerFired = false;
function updateWinner() {
    var p, l, done;
    if (g_drop < 0) g_drop = mx.get_gate_drop_time();
    if (g_drop < 0 || mx.seconds < g_drop) return;
    p = mx.get_running_order_position(0);
    if (g_last_lap == 1000000) {
        if (g_finish_time == 0) g_last_lap = g_finish_laps;
        else if (mx.seconds >= g_drop + g_finish_time) g_last_lap = mx.index_to_lap(p) + 1 + g_finish_laps;
    }
    l = mx.index_to_lap(p + 1);
    if (!checkered && l >= g_last_lap) { checkered = true; checkeredLap = mx.index_to_lap(p); }
    done = checkered && mx.index_to_lap(p) > checkeredLap;
    if (done && !winnerFired) { winnerFired = true; fireFinishFlames(); }
}

function finishPyro(seconds) {
    updateWinner();
    if (currentFrame <= totalFrames && seconds - secondsSinceUpdate >= 1 / 32.0) {
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
    _chain(finishPyroPrev, seconds);
}
var finishPyroPrev = mx.frame_handler;
mx.frame_handler = finishPyro;
