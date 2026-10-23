import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, numpy as np; sys.path.insert(0,ROOT + '/scripts'); from mxs import *
R=REF + '/'
for name,f in [('DesertSand',R+'JGMXDesertSand/JGMXDesertSand'),('DrDew',R+'JGMXDrDew/JGMXDrDew'),('SXCustom',R+'JGSX2026TestTracks/JGSX2026Custom'),('SXDetroit',R+'JGSX2026TestTracks/JGSX2026Detroit'),('SXArlington',R+'JGSX2026TestTracks/JGSX2026Arlington'),('SXGlendale',R+'JGSX2026TestTracks/JGSX2026Glendale'),('SXCleveland',R+'JGSX2026TestTracks/JGSX2026Custom1')]:
    G=parse_gates(f+'/timing_gates'); cp=G['cps']; order=G['normal'] or G['first']
    lap=[i for i in order]
    # normal lap list ends at last checkpoint; loop closes
    pts=np.array([[cp[i][1],cp[i][3]] for i in lap])
    seg=np.hypot(*np.diff(np.vstack([pts,pts[:1]]),axis=0).T)
    print(f'{name}: {len(cp)} cps, lap idx {len(lap)}, straight-line lap length {seg.sum():.0f} ft = {seg.sum()*0.3048:.0f} m (chords, underestimate)')
