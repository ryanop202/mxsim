import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, numpy as np; sys.path.insert(0, ROOT + '/scripts')
from mxs import Track
R=REF + '/'
tracks={'DesertSand':R+'JGMXDesertSand/JGMXDesertSand','DrDew':R+'JGMXDrDew/JGMXDrDew',
 'SXCustom':R+'JGSX2026TestTracks/JGSX2026Custom','SXDetroit':R+'JGSX2026TestTracks/JGSX2026Detroit',
 'SXArlington':R+'JGSX2026TestTracks/JGSX2026Arlington','SXGlendale':R+'JGSX2026TestTracks/JGSX2026Glendale','SXCleveland':R+'JGSX2026TestTracks/JGSX2026Custom1'}
for name,f in tracks.items():
    T=Track(f)
    print(f'{name}: n={T.n} s={T.s} H=[{T.hmin:.2f},{T.hmax:.2f}] png={T.N} size={T.size:.1f}m tilemap={T.tiles.shape} tile_m={T.size/T.tiles.shape[0]:.3f} grads={len(T.gradients)}')
    for mode in ['xz','xz_fz','zx','xz_fx']:
        errs=[]
        for g in T.gradients:
            P=g['pts']
            if len(P)<3 or g['len']<5: continue
            d,h=T.line(*g['a'],*g['b'],mode=mode)
            ref=np.interp(d,P[:,1],P[:,2])
            # compare shape after removing offset (gradients may be relative / later edited)
            e=np.median(np.abs((h-h.mean())-(ref-ref.mean())))
            errs.append(e)
        errs=np.array(errs)
        print(f'   {mode:6s} median|err|={np.median(errs):.3f}  frac<0.15m={np.mean(errs<0.15):.2f}')
