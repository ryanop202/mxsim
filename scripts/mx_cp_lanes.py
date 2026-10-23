"""Sample as-built profiles along the lane direction through every checkpoint (lane = checkpoint normal)."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np; sys.path.insert(0,ROOT + '/scripts'); from mxs import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
f,name=sys.argv[1],sys.argv[2]; half=float(sys.argv[3]) if len(sys.argv)>3 else 110
T=Track(f,'xz'); G=parse_gates(f+'/timing_gates'); lap=G['normal']
C=np.array([[c[1],c[3],c[4],c[6]] for c in G['cps']])
out=[]
n=len(lap); cols=3; rows=int(np.ceil(n/cols))
fig,axs=plt.subplots(rows,cols,figsize=(30,2.3*rows))
for ax,(k,i) in zip(axs.flat,enumerate(lap)):
    x,z,dx,dz=C[i]; L=np.hypot(dx,dz); ux,uz=-dz/L,dx/L
    # orient lane direction along lap progression (towards next checkpoint)
    nx,nz=C[lap[(k+1)%n]][:2]
    if (nx-x)*ux+(nz-z)*uz<0: ux,uz=-ux,-uz
    d,h=T.line(x-ux*half,z-uz*half,x+ux*half,z+uz*half,step=0.25); d=d-half
    # cross section at the checkpoint (to measure lane width)
    t,hx=T.line(x-dx*1.5,z-dz*1.5,x+dx*1.5,z+dz*1.5,step=0.25); t=t-1.5*L
    out.append(dict(cp=int(i),k=k,x=float(x),z=float(z),ux=float(ux),uz=float(uz),gate_half=float(L),d0=float(d[0]),h=np.round(h,3).tolist(),xs_t0=float(t[0]),xs=np.round(hx,3).tolist()))
    ax.plot(d,h,'k',lw=.8); ax.set_aspect('equal'); ax.axvline(0,color='r',lw=.4)
    ax.set_title(f'{name} lap#{k} cp{i} ({x:.0f},{z:.0f}) dir({ux:.2f},{uz:.2f})',fontsize=8); ax.set_xticks(np.arange(-half,half+1,20)); ax.grid(alpha=.3); ax.tick_params(labelsize=6)
plt.tight_layout(); plt.savefig(f'{ROOT}/analysis/cplanes_{name}.png',dpi=40)
json.dump(out,open(f'{ROOT}/analysis/cplanes_{name}.json','w'))
