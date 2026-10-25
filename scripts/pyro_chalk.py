"""v13 (Ryan: « prends-les dedans ») - pyro and chalk taken from the official MX Simulator SX 2026 Anaheim 1 track.
Sources (not versioned as archives; extracted from sx2026.medium.saf + sx2026r01anaheim1_medium.saf into refs/sx2026/):
  - pyro: sx2026/js/pyro (finishflames, finishflames2, gatefireburst, fireball2 + .seq) and js/sounds (gateflameburst,
    largeflameburst, finishlineflame, gatedrop); copied into USLAND2026SX1/js, .seq paths rewritten to @USLAND2026SX1/js/...
  - behaviour: the 'Start Pyro' part of Anaheim frills.js, unchanged except positions:
      billboards 0-2 hidden until the gate drops, then fireball + the two finish-line flames play once (69 frames at 32 fps)
      billboards 3-8 = gate fire bursts on top of the start structure, looping until the gate drops, then hidden
      sounds: gate flame bursts (loop) until the drop, large burst + finish flame at the drop, gate drop sound.
  - placement measured on Anaheim, transposed to our props:
      gate bursts: 6 billboards size 10, y 9.75 (Anaheim structure top 8.94 / our gantry truss top 8.9), at +-9.5 / 21.5 / 35 ft
        along the gate row from its centre (Anaheim: -36, -22.7, -10.3, +8.6, +20.8, +34 from the structure centre);
      finish flames: 2 billboards size 45 on the two arch pillars, 11.8 ft above the arch top (Anaheim: y 37, arch top 25.2);
      fireball: size 100 / 0.5, y 36, 60 ft behind the gate row centre.
  - chalk: Anaheim chalk.png is ONE decal (2048 px, angle 0) whose white lines (~1.6 ft, rgb 242) outline the start
    corridor up to the first turn. Ours: one chalk decal per track, drawn from the start corridor edges (StartRoute),
    image column -> x, row -> z (checked on Anaheim: its lines meet its gate row).
Run after place_props.py. Not tested in game."""
import os, sys, re, shutil, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
import numpy as np
from PIL import Image, ImageDraw
from names import FOLDERS as F
import layouts_sx as LS
from starts import StartRoute
import props_place as PP
import props_usland as PU

SRC = os.environ.get('MXSIM_SX2026') or f'{ROOT}/refs/sx2026'
OUT = f'{ROOT}/tracks'; A = f'{OUT}/{F["SX1"]}'; P = '@' + F['SX1']
PYRO = ['finishflames', 'finishflames2', 'gatefireburst', 'fireball2']
SEQS = ['finishflames.seq', 'finishflames2.seq', 'gatefireburst.seq', 'gatefireburst2.seq', 'fireball2.seq']
SOUNDS = ['gateflameburst', 'largeflameburst', 'finishlineflame', 'gatedrop']
ARCH_TOP = 49.4                 # finish_arch.jm max y

def copy_assets():
    s = f'{SRC}/sx2026/js'; d = f'{A}/js'
    if not os.path.isdir(s):
        print('pyro : sources absentes', s, '-> dossiers js/ du dépôt gardés tels quels'); return
    for nm in PYRO:
        os.makedirs(f'{d}/pyro/{nm}', exist_ok=True)
        for f in os.listdir(f'{s}/pyro/{nm}'):
            if f.endswith('.png'): shutil.copy(f'{s}/pyro/{nm}/{f}', f'{d}/pyro/{nm}/{f}')
    for f in SEQS:
        open(f'{d}/pyro/{f}', 'w', newline='\n').write(open(f'{s}/pyro/{f}').read().replace('@sx2026/js/', f'{P}/js/'))
    os.makedirs(f'{d}/sounds', exist_ok=True)
    for nm in SOUNDS: shutil.copy(f'{s}/sounds/{nm}.raw', f'{d}/sounds/{nm}.raw')

def bb(x, y, z, size, aspect, tex): return f'[{x:.6f} {y:.6f} {z:.6f}] {size:.6f} {aspect:.6f} {P}/js/pyro/{tex}'

def pyro_billboards(key, T):
    g = PP.gantry_pose(key, T); a = g['a']
    along = np.array([np.cos(a), -np.sin(a)])                  # gate row direction (local x of a statue at angle a)
    fwd = np.array([-np.sin(a), -np.cos(a)])                   # riders' direction at the gate
    c0 = np.array([g['x'], g['z']])
    Ap = PP.arch_pose(key, T); f = np.array(Ap['f']); n = np.array([-f[1], f[0]]); c = np.array([Ap['x'], Ap['z']])
    fb = c0 - fwd * 60.0
    L = [bb(fb[0], g['y'] + 36.0, fb[1], 100.0, 0.5, 'fireball2.seq')]
    for sg, seq in ((-1, 'finishflames2.seq'), (1, 'finishflames.seq')):
        p = c + n * sg * PU.ARCH_X; L.append(bb(p[0], Ap['y'] + ARCH_TOP + 11.8, p[1], 45.0, 1.0, seq))
    for u, seq in ((-35.0, 'gatefireburst.seq'), (35.0, 'gatefireburst.seq'), (-21.5, 'gatefireburst2.seq'),
                   (21.5, 'gatefireburst2.seq'), (-9.5, 'gatefireburst.seq'), (9.5, 'gatefireburst.seq')):
        p = c0 + along * u; L.append(bb(p[0], g['y'] + 9.75, p[1], 10.0, 1.0, seq))
    return L, dict(gate=c0, finish=c, fireball=fb, y=g['y'])

JS = '''/*
USLAND 2026 SX - start pyro (taken from the MX Simulator SX 2026 Anaheim 1 frills.js 'Start Pyro', positions adapted).
billboards 0-2: fireball + finish-line flames, shown when the gate drops. billboards 3-8: gate fire bursts until the drop.
*/
function _chain(prev, s) { if (typeof prev === "function") prev(s); }

var gateSoundPositions = [[%(gx).1f, 2, %(gz).1f]];
var gateSounds = [];
var gateSoundPlayed = false;
for (var i = 0; i < gateSoundPositions.length; i++) {
    gateSounds.push(mx.add_sound("%(P)s/js/sounds/gatedrop.raw"));
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
var gateFlameBurst = mx.add_sound("%(P)s/js/sounds/gateflameburst.raw");
mx.set_sound_freq(gateFlameBurst, 44100);
mx.set_sound_vol(gateFlameBurst, 0.2);
mx.set_sound_pos(gateFlameBurst, %(b1x).1f, 10, %(b1z).1f);
mx.set_sound_loop(gateFlameBurst, 1);
mx.start_sound(gateFlameBurst);
var gateFlameBurst2 = mx.add_sound("%(P)s/js/sounds/gateflameburst.raw");
mx.set_sound_freq(gateFlameBurst2, 44100);
mx.set_sound_vol(gateFlameBurst2, 0.2);
mx.set_sound_pos(gateFlameBurst2, %(gx).1f, 10, %(gz).1f);
mx.set_sound_loop(gateFlameBurst2, 1);
mx.start_sound(gateFlameBurst2);
var gateFlameBurst3 = mx.add_sound("%(P)s/js/sounds/gateflameburst.raw");
mx.set_sound_freq(gateFlameBurst3, 44100);
mx.set_sound_vol(gateFlameBurst3, 0.2);
mx.set_sound_pos(gateFlameBurst3, %(b2x).1f, 10, %(b2z).1f);
mx.set_sound_loop(gateFlameBurst3, 1);
mx.start_sound(gateFlameBurst3);
var largeFlameBurst = mx.add_sound("%(P)s/js/sounds/largeflameburst.raw");
mx.set_sound_freq(largeFlameBurst, 44100);
mx.set_sound_vol(largeFlameBurst, 1.0);
mx.set_sound_pos(largeFlameBurst, %(fbx).1f, %(fby).1f, %(fbz).1f);
var finishFlameSound = mx.add_sound("%(P)s/js/sounds/finishlineflame.raw");
mx.set_sound_freq(finishFlameSound, 44100);
mx.set_sound_vol(finishFlameSound, 1.0);
mx.set_sound_pos(finishFlameSound, %(fx).1f, %(fy).1f, %(fz).1f);

// animations
var finishFlames = mx.read_texture('%(P)s/js/pyro/finishflames.seq');
var finishFlames2 = mx.read_texture('%(P)s/js/pyro/finishflames2.seq');
var fireballTexture = mx.read_texture('%(P)s/js/pyro/fireball2.seq');
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
'''

def chalk(key):
    """one decal per track: two white chalk lines along the start corridor edges, grid -> merge (Anaheim style)."""
    R = StartRoute(LS.STARTS[key], LS.N_GATES, LS.GATE_PITCH); s = R.samples(1.0)
    nx, nz = -np.sin(s['th']), np.cos(s['th'])
    edges = []
    for sg in (-1, 1):                                          # drop the bits that run backwards (inside of tight corners)
        e = np.c_[s['x'] + sg * nx * s['w'] / 2, s['z'] + sg * nz * s['w'] / 2]; keep = [0]
        for i in range(1, len(e)):
            d = e[i] - e[keep[-1]]
            if d @ np.array([np.cos(s['th'][i]), np.sin(s['th'][i])]) > 0.05: keep.append(i)
        edges.append(e[keep])
    pts = np.vstack(edges); lo, hi = pts.min(0) - 10, pts.max(0) + 10
    size = float(max(hi - lo)); cx, cz = (lo + hi) / 2; N = 2048; k = 2
    img = Image.new('L', (N * k, N * k), 0); dr = ImageDraw.Draw(img)
    px = lambda e: [((x - (cx - size / 2)) / size * N * k, (z - (cz - size / 2)) / size * N * k) for x, z in e]
    wpx = max(2, int(round(1.6 / size * N * k)))
    for e in edges: dr.line(px(e), fill=255, width=wpx, joint='curve')
    a = np.array(img.resize((N, N), Image.LANCZOS)).astype(float)
    rng = np.random.default_rng(7); a *= np.clip(0.75 + 0.25 * rng.random(a.shape), 0, 1)   # slightly broken chalk
    rgba = np.dstack([np.full((N, N), 242, np.uint8)] * 3 + [a.clip(0, 255).astype(np.uint8)])
    Image.fromarray(rgba, 'RGBA').save(f'{A}/decal/chalk_{key}.png')
    return f'[{cx:.6f} {cz:.6f}] 0.000000 {size:.6f} 1.000000 {P}/decal/chalk_{key}.png', size

def main():
    copy_assets(); T = PP.load_terrain(); rep = {}
    for key, folder in F.items():
        d = f'{OUT}/{folder}'
        L, info = pyro_billboards(key, T)
        old = [l for l in open(f'{d}/billboards').read().split('\n') if l.strip() and '/js/pyro/' not in l]
        open(f'{d}/billboards', 'w', newline='\n').write('\n'.join(L + old) + '\n')      # pyro = billboards 0-8 (frills.js)
        g, fz, fb, y = info['gate'], info['finish'], info['fireball'], info['y']
        G = PP.gantry_pose(key, T); along = np.array([np.cos(G['a']), -np.sin(G['a'])])
        b1, b2 = g - along * 35, g + along * 35
        js = JS % dict(P=P, gx=g[0], gz=g[1], b1x=b1[0], b1z=b1[1], b2x=b2[0], b2z=b2[1], fbx=fb[0], fby=y + 36, fbz=fb[1],
                       fx=fz[0], fy=y + ARCH_TOP, fz=fz[1])
        open(f'{d}/frills.js', 'w', newline='\n').write(js)
        dec, size = chalk(key)
        D = [l for l in open(f'{d}/decals').read().split('\n') if l.strip() and '/decal/chalk_' not in l]
        open(f'{d}/decals', 'w', newline='\n').write('\n'.join(D + [dec]) + '\n')       # chalk last = drawn on top
        rep[key] = dict(billboards=len(L), chalk_size=round(size, 1))
    print('pyro + craie :', rep)

if __name__ == '__main__':
    main()
