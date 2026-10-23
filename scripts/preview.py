"""Render one layout alone (SX) and run geometric checks: closure, clearance, obstacle/berm overlap, length."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, numpy as np; sys.path.insert(0,ROOT + '/scripts')
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from engine import *; import layouts
name=sys.argv[1]; p=getattr(layouts,name)()
G=Grid(11,0.4)
blocks=np.zeros_like(G.H); berms=np.zeros_like(G.H); log=[]
for g in p.segs:
    if g['kind']=='S':
        for sec in g['sections']:
            prof=section_profile(sec[0],sec[2] if len(sec)>2 else None)
            render_lane_block(G,blocks,g,prof,sec[1],LIB['sx_lateral']['top_width'])
            end=sec[1]+len(prof)*0.1
            log.append((g['tag'],sec[0],sec[1],end,g['L'],'OK' if end<=g['L']+0.01 else 'OVERRUN'))
    elif g.get('berm'): render_berm_stamp(G,berms,g['berm'],g['cx'],g['cz'],turn_mid_angle(g))
H=np.maximum(blocks,berms)
S=p.samples(1.0)
x,z,_=p.closure(); x0,z0=S['x'][0],S['z'][0]
print(f'{name}: lap length {p.s:.0f} ft, closure error {np.hypot(x-x0,z-z0):.2f} ft, heading end {np.degrees(p.t)%360:.1f}')
for r in log: print('   %-24s %-15s u0=%6.1f end=%6.1f / straight %6.1f %s'%r)
ov=((blocks>0.3)&(berms>0.3)).sum()*G.s**2; print(f'   block/berm overlap area: {ov:.1f} ft2')
# clearance between non-neighbouring path parts
from scipy.spatial import cKDTree
P=np.c_[S['x'],S['z']]; tr=cKDTree(P); pairs=tr.query_pairs(38.0,output_type='ndarray')
far=np.abs(S['s'][pairs[:,0]]-S['s'][pairs[:,1]]); far=np.minimum(far,p.s-far)
bad=pairs[far>140]
print(f'   path pairs closer than 38 ft but >140 ft apart along lap: {len(bad)}')
xs,zs=S['x'],S['z']; pad=60
bx0,bx1,bz0,bz1=xs.min()-pad,xs.max()+pad,zs.min()-pad,zs.max()+pad
print(f'   bbox x[{bx0:.0f},{bx1:.0f}] z[{bz0:.0f},{bz1:.0f}]  max height {H.max():.2f}')
j0,j1,i0,i1=[int(v/G.s) for v in (bx0,bx1,bz0,bz1)]
fig,ax=plt.subplots(figsize=(16,16*(bz1-bz0)/(bx1-bx0)))
ls=LightSource(300,40); ax.imshow(ls.hillshade(H[i0:i1,j0:j1],vert_exag=3/G.s),cmap='gray',extent=[bx0,bx1,bz1,bz0])
ax.imshow(np.ma.masked_less(H[i0:i1,j0:j1],0.2),cmap='terrain',alpha=.4,extent=[bx0,bx1,bz1,bz0],vmin=0,vmax=12)
ax.plot(xs,zs,'r-',lw=.8)
for k in range(0,len(xs),60): ax.annotate('',xy=(xs[k+1],zs[k+1]),xytext=(xs[k],zs[k]),arrowprops=dict(arrowstyle='->',color='r'))
for g in p.segs:
    if g['tag']: 
        q=p.samples(1.0); 
    if g['kind']=='S' and g['tag']: ax.text(g['x0']+g['L']/2*np.cos(g['t']),g['z0']+g['L']/2*np.sin(g['t'])-8,g['tag'],color='blue',fontsize=8,ha='center')
if len(bad): ax.plot(xs[bad.ravel()],zs[bad.ravel()],'mx',ms=3)
plt.savefig(f'{ROOT}/analysis/preview_{name}.png',dpi=55,bbox_inches='tight')
np.save(f'{ROOT}/analysis/H_{name}.npy',H[i0:i1,j0:j1].astype(np.float32))
