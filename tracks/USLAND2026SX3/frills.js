/*
USLAND 2026 SX - start pyro (taken from the MX Simulator SX 2026 Anaheim 1 frills.js 'Start Pyro', positions adapted).
billboards 0-2: fireball + finish-line flames, shown when the gate drops. billboards 3-8: gate fire bursts until the drop.
*/
function _chain(prev, s) { if (typeof prev === "function") prev(s); }

var gateSoundPositions = [[788.0, 2, 965.0]];
var gateSounds = [];
var gateSoundPlayed = false;
for (var i = 0; i < gateSoundPositions.length; i++) {
    gateSounds.push(mx.add_sound("@USLAND2026SX1/js/sounds/gatedrop.raw"));
    mx.set_sound_freq(gateSounds[i], 44100);
    mx.set_sound_vol(gateSounds[i], 1.0);
    mx.set_sound_pos(gateSounds[i], gateSoundPositions[i][0], gateSoundPositions[i][1], gateSoundPositions[i][2]);
}
function gateSound(seconds) {
    var drop = mx.get_gate_drop_time();
    if (!gateSoundPlayed && drop >= 0 && mx.seconds >= drop) {
        gateSoundPlayed = true;
        for (var i = 0; i < gateSounds.length; i++) mx.start_sound(gateSounds[i]);
    }
    _chain(gateSoundPrev, seconds);
}
var gateSoundPrev = mx.frame_handler;
mx.frame_handler = gateSound;

// sounds
var gateFlameBurst = mx.add_sound("@USLAND2026SX1/js/sounds/gateflameburst.raw");
mx.set_sound_freq(gateFlameBurst, 44100);
mx.set_sound_vol(gateFlameBurst, 0.2);
mx.set_sound_pos(gateFlameBurst, 788.0, 10, 1000.0);
mx.set_sound_loop(gateFlameBurst, 1);
mx.start_sound(gateFlameBurst);
var gateFlameBurst2 = mx.add_sound("@USLAND2026SX1/js/sounds/gateflameburst.raw");
mx.set_sound_freq(gateFlameBurst2, 44100);
mx.set_sound_vol(gateFlameBurst2, 0.2);
mx.set_sound_pos(gateFlameBurst2, 788.0, 10, 965.0);
mx.set_sound_loop(gateFlameBurst2, 1);
mx.start_sound(gateFlameBurst2);
var gateFlameBurst3 = mx.add_sound("@USLAND2026SX1/js/sounds/gateflameburst.raw");
mx.set_sound_freq(gateFlameBurst3, 44100);
mx.set_sound_vol(gateFlameBurst3, 0.2);
mx.set_sound_pos(gateFlameBurst3, 788.0, 10, 930.0);
mx.set_sound_loop(gateFlameBurst3, 1);
mx.start_sound(gateFlameBurst3);
var largeFlameBurst = mx.add_sound("@USLAND2026SX1/js/sounds/largeflameburst.raw");
mx.set_sound_freq(largeFlameBurst, 44100);
mx.set_sound_vol(largeFlameBurst, 1.0);
mx.set_sound_pos(largeFlameBurst, 848.0, 36.0, 965.0);
var finishFlameSound = mx.add_sound("@USLAND2026SX1/js/sounds/finishlineflame.raw");
mx.set_sound_freq(finishFlameSound, 44100);
mx.set_sound_vol(finishFlameSound, 1.0);
mx.set_sound_pos(finishFlameSound, 674.1, 49.4, 890.0);

// animations
var finishFlames = mx.read_texture('@USLAND2026SX1/js/pyro/finishflames.seq');
var finishFlames2 = mx.read_texture('@USLAND2026SX1/js/pyro/finishflames2.seq');
var fireballTexture = mx.read_texture('@USLAND2026SX1/js/pyro/fireball2.seq');
var currentFrame = 0;
var totalFrames = 69;
var secondsSinceUpdate = 0;

// hide billboards 0-2 until called upon, show the gate bursts (3-8)
mx.color_billboard(0, 1, 1, 1, 0);
mx.color_billboard(1, 1, 1, 1, 0);
mx.color_billboard(2, 1, 1, 1, 0);
for (var b = 3; b <= 8; b++) mx.color_billboard(b, 1, 1, 1, 1);

function startPyro(seconds) {
    var gateDropCheck = mx.get_gate_drop_time() >= 0 && mx.seconds >= mx.get_gate_drop_time();
    if (gateDropCheck && seconds - secondsSinceUpdate >= 1 / 32.0) {
        secondsSinceUpdate = seconds;
        if (currentFrame <= totalFrames) {
            mx.begin_custom_frame(fireballTexture);
            mx.begin_custom_frame(finishFlames);
            mx.begin_custom_frame(finishFlames2);
            mx.paste_custom_frame(fireballTexture, currentFrame, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0);
            mx.paste_custom_frame(finishFlames, currentFrame, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0);
            mx.paste_custom_frame(finishFlames2, currentFrame, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0);
            mx.end_custom_frame(fireballTexture);
            mx.end_custom_frame(finishFlames);
            mx.end_custom_frame(finishFlames2);
            if (currentFrame === 0) {
                mx.color_billboard(0, 1, 1, 1, 1);
                mx.color_billboard(1, 1, 1, 1, 1);
                mx.color_billboard(2, 1, 1, 1, 1);
                for (var b = 3; b <= 8; b++) mx.color_billboard(b, 1, 1, 1, 0);
                mx.start_sound(largeFlameBurst);
                mx.start_sound(finishFlameSound);
                mx.stop_sound(gateFlameBurst);
                mx.stop_sound(gateFlameBurst2);
                mx.stop_sound(gateFlameBurst3);
            }
            currentFrame++;
        }
    }
    _chain(startPyroPrev, seconds);
}
var startPyroPrev = mx.frame_handler;
mx.frame_handler = startPyro;
