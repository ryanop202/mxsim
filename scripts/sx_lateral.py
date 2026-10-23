"""Measure SX block lateral (cross-lane) profiles and test two reconstruction models against the as-built stamps."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np; sys.path.insert(0,ROOT + '/scripts')
from sx_classify_lib import rot_patch
L=json.load(open(ROOT + '/lib/sx_components.json'))
singles=[c for c in L if c['npeaks']==1 and c['solidity']>1.3 and c['hmax']>1.5 and 25<c['width_lane']<45]
print('single blocks:',len(singles))
rows=[]; walls=[]
for c in singles:
    P=np.load(f'{ROOT}/lib/sx/{c["id"]}.npy')
    u,Q=rot_patch(P,c['s'],c['lane_ang'])
    prof=Q.max(0); ci=np.argmax(prof); top=prof[ci]
    xs=Q[:,ci]; occ=np.nonzero(xs>0.05)[0]; v=np.arange(len(xs))*0.1
    # wall: height vs distance inward from the foot edge (both sides averaged)
    left=xs[occ.min():occ.min()+80]; right=xs[occ.max():occ.max()-80:-1]
    n=min(len(left),len(right)); wall=(left[:n]+right[:n])/2
    top_w=(np.sum(xs>top-0.25))*0.1
    # 10%-90% run
    i10=np.argmax(wall>0.1*top); i90=np.argmax(wall>0.9*top)
    rows.append((c['id'],top,top_w,(i90-i10)*0.1,np.degrees(np.arctan(0.8*top/max((i90-i10)*0.1,0.1)))))
    walls.append((top,wall))
for r in sorted(rows,key=lambda r:r[1]): print('%-16s H=%.2f topW=%.1f run10-90=%.2f ft  mean side=%.0f deg'%r)
