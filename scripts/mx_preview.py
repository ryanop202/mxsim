import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, numpy as np; sys.path.insert(0,ROOT + '/scripts')
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from engine import *; import layouts
from scipy.spatial import cKDTree
p=layouts.mx()
S=p.samples(1.0); x,z=S['x'],S['z']
print(f'MX lap {p.s:.0f} ft ({p.s*0.3048:.0f} m), closure {np.hypot(p.x-x[0],p.z-z[0]):.2f}')
tr=cKDTree(np.c_[x,z]); pairs=tr.query_pairs(70.0,output_type='ndarray')
far=np.abs(S['s'][pairs[:,0]]-S['s'][pairs[:,1]]); far=np.minimum(far,p.s-far); bad=pairs[far>200]
print('close pairs (<70ft, >200ft apart along lap):',len(bad))
for g in p.segs:
    if g['kind']=='T': 
        if g['r']<12: print('  tiny radius',g)
fig,ax=plt.subplots(figsize=(16,16))
ax.plot(x,z,'k-'); ax.set_xlim(0,1638); ax.set_ylim(1638,0); ax.set_aspect('equal'); ax.grid(alpha=.3)
for k in range(0,len(x),150): ax.annotate('',xy=(x[k+3],z[k+3]),xytext=(x[k],z[k]),arrowprops=dict(arrowstyle='->',color='r'))
for g in p.segs:
    if g['kind']=='S': ax.text(g['x0']+g['L']/2*np.cos(g['t']),g['z0']+g['L']/2*np.sin(g['t']),f"{g['tag']}\n{g['L']:.0f}",fontsize=7,color='b')
if len(bad): ax.plot(x[bad.ravel()],z[bad.ravel()],'mx',ms=3)
for (a,b,c,d) in [(20,600,1175,1638),(629,1220,1140,1638)]: ax.add_patch(plt.Rectangle((a,c),b-a,d-c,fill=False,ec='orange'))
plt.savefig(ROOT + '/analysis/mx_plan.png',dpi=50,bbox_inches='tight')
