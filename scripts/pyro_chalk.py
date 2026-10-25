"""v13b - flammes à l'arrivée + craie (lignes du couloir de départ, ligne de holeshot), à partir des fichiers bruts de
MX Simulator SX 2026 Anaheim 1 rangés dans assets/sx2026 (voir son README). Remplace la v13 annulée : plus de jets de feu
sur le portique de départ ni de boule de feu, seulement les flammes de l'arche d'arrivée.
  - flammes : 2 billboards (finishflames / finishflames2) sur les 2 poteaux de l'arche, cachés au repos ; ils jouent une
    fois (41 images à 32 im/s, son finishlineflame) à la chute de la grille (comme Anaheim) et quand le vainqueur passe
    l'arrivée (1er passage du leader sur la ligne après le drapeau à damier, même logique que le commissaire d'Anaheim).
    Taille 45 (Anaheim), base du billboard sur le haut des poteaux (37,5 ft) : la hauteur d'Anaheim (+11,8 ft au-dessus
    de l'arche) laissait les flammes flotter en l'air sur notre arche. À vérifier en jeu (y = base ou centre du billboard).
  - craie : un decal par piste (blanc 242, ~1,6 ft, image colonne -> x, ligne -> z, angle 0, comme la craie d'Anaheim) :
      * deux traits le long des bords du couloir de départ, de la rangée de grilles à la jonction avec le tour ;
      * la ligne de holeshot en travers de la 1re bosse après le départ, sur sa crête, sur toute la largeur de la bosse.
Ne touche ni au terrain ni aux objets. Lancé après place_props.py. Non testé en jeu."""
import os, sys, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
import numpy as np
from PIL import Image, ImageDraw
from names import FOLDERS as F
import layouts_sx as LS
from starts import StartRoute
import props_place as PP
import props_usland as PU

SRC = f'{ROOT}/assets/sx2026/flammes'
OUT = f'{ROOT}/tracks'; A = f'{OUT}/{F["SX1"]}'; P = '@' + F['SX1']
PYRO = ['finishflames', 'finishflames2']
SOUNDS = ['finishlineflame']
FLAME_SIZE = 45.0                                    # Anaheim size; billboard base on the pillar tops
CHALK_W, CHALK_RGB = 1.6, 242
LAPS = {'SX1': LS.sx1, 'SX2': LS.sx2, 'SX3': LS.sx3}

def arch_top():
    """top of the arch pillars (= top of the FINISH beam) in finish_arch.jm: pillar x = 0 (model origin) and 2 x ARCH_X."""
    V = [tuple(map(float, l.split()[:2])) for l in open(f'{ROOT}/assets/props/finish_arch.jm').read().split('\n')[3:] if len(l.split()) == 8]
    return max(y for x, y in V if abs(x) < 2.8)

def copy_assets():
    d = f'{A}/js'
    for nm in PYRO:
        os.makedirs(f'{d}/pyro/{nm}', exist_ok=True)
        for f in os.listdir(f'{SRC}/pyro/{nm}'):
            if f.endswith('.png'): shutil.copy(f'{SRC}/pyro/{nm}/{f}', f'{d}/pyro/{nm}/{f}')
        open(f'{d}/pyro/{nm}.seq', 'w', newline='\n').write(open(f'{SRC}/pyro/{nm}.seq').read().replace('@sx2026/js/', f'{P}/js/'))
    os.makedirs(f'{d}/sounds', exist_ok=True)
    for nm in SOUNDS: shutil.copy(f'{SRC}/sounds/{nm}.raw', f'{d}/sounds/{nm}.raw')

def frames(seq):
    return int(open(f'{SRC}/pyro/{seq}.seq').readline().split()[1])

JS = '''/*
USLAND 2026 SX - flammes de l'arrivée (repris du frills.js de MX Simulator SX 2026 Anaheim 1, positions adaptées).
billboards 0-1 : flammes sur les 2 poteaux de l'arche FINISH, cachées au repos.
Elles jouent une fois à la chute de la grille, puis une fois quand le vainqueur passe la ligne d'arrivée.
*/
function _chain(prev, s) { if (typeof prev === "function") prev(s); }

var finishFlameSound = mx.add_sound("%(P)s/js/sounds/finishlineflame.raw");
mx.set_sound_freq(finishFlameSound, 44100);
mx.set_sound_vol(finishFlameSound, 1.0);
mx.set_sound_pos(finishFlameSound, %(fx).1f, %(fy).1f, %(fz).1f);

var finishFlames = mx.read_texture('%(P)s/js/pyro/finishflames.seq');
var finishFlames2 = mx.read_texture('%(P)s/js/pyro/finishflames2.seq');
var totalFrames = %(nf)d;
var currentFrame = totalFrames + 1;       // > totalFrames = not playing
var secondsSinceUpdate = 0;
var dropFired = false;

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
    var drop = mx.get_gate_drop_time();
    if (!dropFired && drop >= 0 && mx.seconds >= drop) { dropFired = true; fireFinishFlames(); }
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
'''

def flames(key, T, top):
    Ap = PP.arch_pose(key, T); y = Ap['y'] + top
    L = [f'[{p[0]:.6f} {y:.6f} {p[1]:.6f}] {FLAME_SIZE:.6f} 1.000000 {P}/js/pyro/{seq}.seq'
         for p, seq in zip(Ap['pillars'], ('finishflames2', 'finishflames'))]
    return L, dict(fx=Ap['cx'], fy=Ap['y'] + top, fz=Ap['cz'])

def start_edges(key):
    """the two edges of the start corridor, gate row -> merge (an inner edge stops where a tight turn makes it run backwards)."""
    R = StartRoute(LS.STARTS[key], LS.N_GATES, LS.GATE_PITCH); s = R.samples(1.0)
    nx, nz = -np.sin(s['th']), np.cos(s['th'])
    edges = []
    for sg in (-1, 1):
        e = np.c_[s['x'] + sg * nx * s['w'] / 2, s['z'] + sg * nz * s['w'] / 2]; keep = [0]
        st = np.r_[np.linalg.norm(np.diff(e, axis=0), axis=1), 1.0]          # edge travel per ft of corridor centre
        tight = np.convolve(st < 0.35, np.ones(4), 'same') >= 4             # inside of a tight turn (radius < 0.35 x centre)
        if tight.any(): e = e[:int(np.argmax(tight))]
        for i in range(1, len(e)):
            if (e[i] - e[keep[-1]]) @ np.array([np.cos(s['th'][i]), np.sin(s['th'][i])]) > 0.05: keep.append(i)
            elif i - keep[-1] > 8: break                             # inside of a tight turn: the line stops there (no hook)
        edges.append(e[keep])
    return edges, R

def holeshot(key, T, R):
    """chalk line across the first bump after the start: on its crest, perpendicular to the lap, over the bump's width."""
    lap = LAPS[key]().samples(1.0); X, Z, TH = lap['x'], lap['z'], lap['th']
    i0 = int(np.argmin(np.hypot(X - R.merge[0], Z - R.merge[1]))); n = len(X)
    idx = (i0 + np.arange(600)) % n; h = PP.h_at(T, X[idx], Z[idx]); base = float(np.median(h[:5]))
    j = int(np.argmax(h - base > 1.0))
    if h[j] - base <= 1.0: raise ValueError(f'{key}: no bump after the start')
    while j + 1 < len(h) and h[j + 1] >= h[j]: j += 1               # crest
    k = idx[j]; c = np.array([X[k], Z[k]]); t = TH[k]; nrm = np.array([-np.sin(t), np.cos(t)])
    crest = float(h[j]); ext = []
    for sg in (-1, 1):                                              # bump width: where it stays above half its height
        u = 0.0
        while u < 40 and PP.h_at(T, *(c + nrm * sg * (u + 0.5))) - base > 0.5 * (crest - base): u += 0.5
        ext.append(u)
    a, b = c - nrm * (ext[0] + 0.5), c + nrm * (ext[1] + 0.5)
    return [a, b], dict(crest_xz=c.round(1).tolist(), crest_h=round(crest - base, 2), width=round(ext[0] + ext[1] + 1, 1),
                        after_merge_ft=int(j))

def chalk_decal(key, lines):
    pts = np.vstack(lines); lo, hi = pts.min(0) - 10, pts.max(0) + 10
    size = float(max(hi - lo)); cx, cz = (lo + hi) / 2; N = 2048; k = 2
    img = Image.new('L', (N * k, N * k), 0); dr = ImageDraw.Draw(img)
    px = lambda e: [((x - (cx - size / 2)) / size * N * k, (z - (cz - size / 2)) / size * N * k) for x, z in e]
    wpx = max(2, int(round(CHALK_W / size * N * k)))
    for e in lines: dr.line(px(e), fill=255, width=wpx, joint='curve')
    a = np.array(img.resize((N, N), Image.LANCZOS)).astype(float)
    rng = np.random.default_rng(7); a *= np.clip(0.75 + 0.25 * rng.random(a.shape), 0, 1)       # slightly broken chalk
    rgba = np.dstack([np.full((N, N), CHALK_RGB, np.uint8)] * 3 + [a.clip(0, 255).astype(np.uint8)])
    Image.fromarray(rgba, 'RGBA').save(f'{A}/decal/chalk_{key}.png')
    return f'[{cx:.6f} {cz:.6f}] 0.000000 {size:.6f} 1.000000 {P}/decal/chalk_{key}.png', size

def main():
    copy_assets(); T = PP.load_terrain(); top = arch_top(); rep = {}
    nf = min(frames(s) for s in PYRO)
    for key, folder in F.items():
        d = f'{OUT}/{folder}'
        L, fi = flames(key, T, top)
        old = [l for l in open(f'{d}/billboards').read().split('\n') if l.strip() and '/js/pyro/' not in l]
        open(f'{d}/billboards', 'w', newline='\n').write('\n'.join(L + old) + '\n')      # flames = billboards 0-1 (frills.js)
        open(f'{d}/frills.js', 'w', newline='\n').write(JS % dict(P=P, nf=nf, **fi))
        edges, R = start_edges(key); hs, info = holeshot(key, T, R)
        dec, size = chalk_decal(key, edges + [np.array(hs)])
        D = [l for l in open(f'{d}/decals').read().split('\n') if l.strip() and '/decal/chalk_' not in l]
        open(f'{d}/decals', 'w', newline='\n').write('\n'.join(D + [dec]) + '\n')       # chalk last = drawn on top
        rep[key] = dict(flammes=len(L), craie_ft=round(size, 1), holeshot=info)
    print('flammes + craie :', rep)
    return rep

if __name__ == '__main__':
    main()
